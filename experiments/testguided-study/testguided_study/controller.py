"""Evidence-based session control; model notes cannot overwrite runner facts."""

import copy
import json
from collections import Counter

from .iteration import context, identity


class Controller:
    def __init__(self, repeat_limit):
        self.repeat_limit = repeat_limit
        self.attempts = Counter()
        self.seen = set()
        self.idle = 0
        self.facts = {"workflow": "orient", "files": {}, "tests": [], "baseline": []}
        self.metrics = {"rejected_retries": 0, "tool_errors": 0, "ebt_executed": 0, "ebt_evaluated": 0,
                        "ebt_passed": 0, "first_read_call": None, "first_red_call": None,
                        "first_production_change_call": None}
        self.blocked_edits = set()
        self.paths = {}
        self.test_version = None
        self.readable = set()

    def key(self, action):
        # Notes/reasons and audit labels do not create new evidence.
        value = {k: v for k, v in action.items() if k not in {"stage", "note", "reason"}}
        if action['action'] in {'run_tests', 'collect_tests', 'check_baseline'}:
            value['versions'] = self.test_version
        return identity(value)

    def guard(self, action):
        if action['action'] == 'replace_text' and action['path'] in self.blocked_edits:
            return {"status": "tool_error", "code": "read_required", "repair": "Read the current file before another edit."}
        # Successful reads may have been evicted from the model context. Replaying
        # them is safe; unchanged results still advance the idle/stall counter.
        if action['action'] == 'read_file' and self.key(action) in self.readable:
            return None
        if self.attempts[self.key(action)] >= 2:
            self.metrics['rejected_retries'] += 1
            return {"status": "tool_error", "code": "repeated_action", "repair":
                    "No new evidence: locate an existing path, read current source, or choose a different focused test."}
        return None

    def observe(self, action, result, versions, call):
        op = action['action']
        successful = result.get('status') == 'completed'
        self.attempts[self.key(action)] += 1
        self.paths[self.key(action)] = action.get("path")
        if result.get('code') == 'edit_conflict':
            self.blocked_edits.add(action['path'])
        if op == 'read_file' and successful:
            self.readable.add(self.key(action))
            self.blocked_edits.discard(action['path'])
            self.facts['files'][action['path']] = {k: result.get(k) for k in ('sha256', 'start', 'total_lines')}
            if self.metrics['first_read_call'] is None:
                self.metrics['first_read_call'] = call
        if not successful:
            self.metrics['tool_errors'] += 1
        evidence = {k: v for k, v in result.items() if k not in {'stdout', 'stderr', 'junit_xml', 'framework_usage'}}
        fingerprint = identity([op, evidence])
        new = successful and fingerprint not in self.seen
        self.seen.add(fingerprint)
        self.idle = 0 if new else self.idle + 1
        self.test_version = (versions.get("tests"), versions.get("production"))
        observation = result.get('observation')
        if observation and not result.get('collection_only'):
            record = {"targets": action['targets'], "observation": observation, **versions,
                      "baseline": result.get('baseline', False)}
            bucket = 'baseline' if record['baseline'] else 'tests'
            self.facts[bucket] = (self.facts[bucket] + [record])[-8:]
            if observation == 'assertion_failure':
                self.facts['workflow'] = 'implement'
                if self.metrics['first_red_call'] is None:
                    self.metrics['first_red_call'] = call
            elif observation == 'pass':
                self.facts['workflow'] = 'verify'
        for key in ('ebt_executed', 'ebt_evaluated', 'ebt_passed'):
            self.metrics[key] += result.get('framework_usage', {}).get(key, 0)
        if op in {'write_file', 'replace_text', 'delete_file'} and successful:
            # A successful mutation invalidates cached attempts; notes and failures never do.
            for key in list(self.attempts):
                if self.paths.get(key) == action.get('path'):
                    del self.attempts[key]
            self.facts['workflow'] = 'reproduce' if 'test' in action.get('path', '') else 'verify'
        if len(self.facts['files']) > 12:
            del self.facts['files'][next(iter(self.facts['files']))]
        return self.idle >= 2 * self.repeat_limit


def compact_observation(result, limit=6000):
    """Keep diagnostics and current code, avoid retransmitting long raw tracebacks."""
    visible = copy.deepcopy({k: v for k, v in result.items() if k != 'junit_xml'})
    if 'diagnostics' in visible:
        visible['stdout'] = visible.get('stdout', '')[-600:]
        visible['stderr'] = visible.get('stderr', '')[-300:]
        diagnostics = visible['diagnostics']
        errors = diagnostics.get('errors', [])
        groups = {}
        for error in errors:
            key = (error.get('type'), error.get('message'))
            if key in groups:
                groups[key]['occurrences'] += error.get('occurrences', 1)
            else:
                groups[key] = {**error, 'occurrences': error.get('occurrences', 1)}
        diagnostics['errors'] = list(groups.values())[:3]
        diagnostics['omitted_errors'] = diagnostics.get('omitted_errors', 0) + len(errors) - len(diagnostics['errors'])
        for error in diagnostics['errors']:
            error['message'] = error.get('message', '')[:240]
            error['traceback_tail'] = error.get('traceback_tail', '')[-300:]
        usage = dict(visible.get('framework_usage', {}))
        ids = usage.get('test_ids', [])
        usage['test_ids'] = ids[:8]
        usage['omitted_test_ids'] = usage.get('omitted_test_ids', 0) + max(0, len(ids)-8)
        visible['framework_usage'] = usage
        # Preserve summary facts when long parameterized IDs or messages consume
        # the allowance. Full errors remain in the run's paged detail artifact.
        while len(json.dumps(visible).encode()) > limit:
            if visible.get('stdout') or visible.get('stderr'):
                visible['stdout'] = visible['stderr'] = ''
            elif usage['test_ids']:
                usage['test_ids'].pop()
                usage['omitted_test_ids'] += 1
            elif diagnostics['errors']:
                diagnostics['errors'].pop()
                diagnostics['omitted_errors'] += 1
            elif diagnostics.get('targets'):
                diagnostics['targets'].pop()
                diagnostics['omitted_targets'] = diagnostics.get('omitted_targets', 0) + 1
            else:
                break
        visible['output_truncated'] = (visible.get('output_truncated', False)
                                       or visible != {k: v for k, v in result.items() if k != 'junit_xml'})
    return visible


def session_context(system, issue, history, ledger, capacity):
    """Fit optional session evidence without ever truncating the task or guide."""
    try:
        return context(system, issue, history, ledger, capacity)
    except ValueError:
        pass
    # Ledger entries and the latest output can grow independently. Try bounded
    # views of both; previous complete exchanges are still selected by context().
    minimal = {key: copy.deepcopy(ledger[key]) for key in
               ('action_error', 'next', 'last_file', 'last_test') if key in ledger}
    minimal['context_notice'] = 'Older ledger details omitted; reread files or use read_test_details.'
    if 'visible_baseline' in ledger:
        baseline = ledger['visible_baseline']
        minimal['visible_baseline'] = {'observation': baseline.get('observation'),
                                       'counts': baseline.get('diagnostics', {}).get('counts', {}),
                                       'scope': baseline.get('scope')}
    for allowance in (4000, 2000, 800):
        exchanges = copy.deepcopy(history)
        if exchanges:
            action = json.loads(exchanges[-1][0]['content'])
            for field in ('content', 'old', 'new'):
                if len(action.get(field, '')) > allowance:
                    original = action.pop(field)
                    action.setdefault('archived_fields', {})[field] = {'sha256': identity(original), 'characters': len(original)}
            exchanges[-1][0]['content'] = json.dumps(action)
            result = json.loads(exchanges[-1][1]['content'])
            if 'diagnostics' in result:
                result = compact_observation(result, allowance)
            elif 'text' in result:
                lines = result['text'].splitlines()
                while lines and len(json.dumps(result).encode()) > allowance:
                    lines.pop()
                    result.update(text='\n'.join(lines), next_start=result.get('start', 1) + len(lines), truncated=True)
            else:
                for key in ('hits', 'files'):
                    while result.get(key) and len(json.dumps(result).encode()) > allowance:
                        result[key].pop()
                        result.update(next_start=result.get('start', 0) + len(result[key]), truncated=True)
            exchanges[-1][1]['content'] = json.dumps(result)
        try:
            return context(system, issue, exchanges, minimal, capacity)
        except ValueError:
            continue
    # Retain an explicit failure if even the mandatory input cannot fit.
    return context(system, issue, exchanges, {}, capacity)


def context_capacity(limits, model, schema):
    """Conservative byte estimate, explicitly not a tokenizer measurement."""
    schema_bytes = len(json.dumps(schema).encode())
    available = model['num_ctx'] - model['num_predict'] - 512
    # Two UTF-8 bytes/token is a conservative calibration for the archived code contexts.
    return max(0, min(limits['context_bytes'], available * 2 - schema_bytes))
