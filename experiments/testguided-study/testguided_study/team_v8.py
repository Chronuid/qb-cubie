"""Serial v8 controller: role-scoped context, atomic deliveries, current evidence.

The execute port is trusted runner I/O. No model-supplied counters or verdicts
establish execution facts. Workspace access is checked before calling that port.
"""

import copy
import difflib
import fnmatch
import json
import time
from pathlib import Path

from ollama_agents.errors import AdapterError
from ollama_agents.schema import validate

from .artifacts import write
from .iteration import identity
from .team import TeamController
from .team_v8_design import CONTEXT, POLICY, PROMPTS, ROLES, SCHEMAS
from .team_workspace import (
    KINDS,
    TEST_KINDS,
    LocalWorkspace,
    canonical_path,
    classify,
    versions,
)


class V8LocalWorkspace(LocalWorkspace):
    """Retain all public edits for audit and production alone for evaluation."""

    def __init__(self, root, manifest):
        super().__init__(root, manifest)
        self.initial_files = {p: self.read(p) for p in self.inventory()}

    def production_patch(self):
        return super().patch()

    def patch(self):
        current = {p: self.read(p) for p in self.inventory()}
        result = []
        for name in sorted(self.initial_files.keys() | current.keys()):
            old, new = self.initial_files.get(name, b''), current.get(name, b'')
            if old != new:
                result.extend(difflib.unified_diff(old.decode('utf-8', 'replace').splitlines(True),
                    new.decode('utf-8', 'replace').splitlines(True),
                    fromfile='a/' + name if name in self.initial_files else '/dev/null',
                    tofile='b/' + name if name in current else '/dev/null'))
        return ''.join(result)


class V8TeamController(TeamController):
    def __init__(self, *, workspace, artifact_dir, mode, issue, guides, manifest,
                 policy=None, execute, clock=time.monotonic, store=None, design=None):
        if mode not in {'cubie', 'pytest'}:
            raise ValueError('Unknown study arm')
        for name, kind in manifest.items():
            canonical_path(name)
            if kind not in KINDS:
                raise ValueError('Unknown path classification')
        self.root, self.directory = Path(workspace), Path(artifact_dir)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.store = store or V8LocalWorkspace(workspace, manifest)
        self.manifest = self.store.manifest
        self.environment = self.store.environment() if hasattr(self.store, 'environment') else {'python': 'Inspect public environment files'}
        self.policy = POLICY | (policy or {})
        if any(type(v) is not int or v < 0 for v in self.policy.values()):
            raise ValueError('Policies require nonnegative integers')
        self.clock, self.started, self.execute = clock, clock(), execute
        self.mode, self.issue, self.guide = mode, issue, guides[mode]
        self.prompts = copy.deepcopy(design['core']['context']['roles'] if design else PROMPTS)
        self.schemas = copy.deepcopy(design['core']['context']['schemas'] if design else SCHEMAS)
        self.role, self.state, self.status, self.reason = 'analysis', 'orient', 'running', None
        self.serial, self.context_revision, self.context = 0, 0, {}
        self.active_job = self._job('orient', 'Locate sources and a first justified test case.')
        self.pending, self.answers, self.open_questions = [], {}, []
        self.unresolved_answers = {}
        self.cases, self.targets, self.regressions, self.requirements = {}, [], [], {}
        self.evidence, self.handles, self.cursors, self.cache = {}, {}, {}, {}
        self.histories = {role: [] for role in ROLES}
        self.inspected = set()
        self.messages = []
        self.metrics = {'model_calls': 0, 'tool_calls': 0, 'output_repairs': 0,
            'recoveries': 0, 'information_requests': 0, 'revision_rounds': 0,
            'edit_conflicts': 0, 'tool_errors': 0,
            'ebt_executed': 0, 'ebt_evaluated': 0, 'ebt_passed': 0, 'ebt_evaluation_checked': 0,
            'first_qa_delivery_seconds': None, 'first_red_call': None, 'first_red_seconds': None,
            'first_production_change_call': None, 'first_production_change_seconds': None,
            'verified_seconds': None,
            'milestones': {}, 'duplicate_actions': 0, 'cursor_errors': 0, 'scope_not_found': 0,
            'context_requests': [],
            'roles': {r: {'model_calls': 0, 'tool_calls': 0, 'model_seconds': 0,
                         'tool_seconds': 0, 'input_tokens': 0, 'output_tokens': 0} for r in ROLES}}
        self.versions = versions(self.store.inventory(), self.manifest)
        self.original_production = self.versions['production']
        self.qualifications = {'reproduced': False, 'verified': False}
        self.completion = {'allowed': False, 'status': 'incomplete'}
        self.diff_ref, self.review_versions = None, None
        self.last_error = None
        self._archive()

    def _new_id(self, prefix):
        self.serial += 1
        return f'{prefix}-{self.serial}'

    def _job(self, kind, task, **inputs):
        return {'id': self._new_id('job'), 'kind': kind, 'task': task,
                'decision_required': False, **copy.deepcopy(inputs)}

    def _activate(self, role, kind, task, **inputs):
        self.role, self.state = role, kind
        self.active_job = self._job(kind, task, **inputs)
        # A role's old job exchanges are not examples for its new assignment.
        self.histories[role] = []
        self.last_error = None
        if role in {'qa', 'dev'}:
            self._milestone(role)

    def _milestone(self, name):
        self.metrics['milestones'].setdefault(name, {'seconds': self.clock() - self.started,
            'model_calls': self.metrics['model_calls'], 'tool_calls': self.metrics['tool_calls']})

    def _refresh(self):
        current = versions(self.store.inventory(), self.manifest)
        if current != self.versions:
            self.versions = current
            self.qualifications['verified'] = False
            self.completion = {'allowed': False, 'status': 'incomplete'}
        self._qualify()

    def _snapshot(self):
        return copy.deepcopy({'role': self.role, 'roles': list(ROLES), 'state': self.state,
            'status': self.status, 'reason': self.reason, 'active_job': self.active_job,
            'context_revision': self.context_revision, 'versions': self.versions,
            'cases': self.cases, 'open_questions': self.open_questions,
            'pending_requests': self.pending, 'qualifications': self.qualifications,
            'completion': self.completion, 'metrics': self.metrics,
            'budget': {'deadline': self.started + self.policy['wall_seconds'], 'reserve_active': False},
            'test_observations': [e for e in self.evidence.values() if e.get('kind') == 'test'],
            'private_evaluation_required': True})

    def snapshot(self):
        self._refresh()
        return self._snapshot()

    def _archive(self):
        write(self.directory / 'team.json', self._snapshot())
        write(self.directory / 'context.json', {'revision': self.context_revision, **self.context})
        write(self.directory / 'path-manifest.json', self.manifest)
        (self.directory / 'full.patch').write_text(self.store.patch(), encoding='utf-8')

    def advance(self):
        self._refresh()
        if self.status == 'running' and self.clock() >= self.started + self.policy['wall_seconds']:
            self.finish('budget_exhausted')
        return self._snapshot()

    def finish(self, reason):
        if self.status == 'running':
            self.status, self.reason = 'incomplete', reason
            self.completion = {'allowed': False, 'status': 'incomplete'}
            self._archive()

    def _path(self, name, *, writing=False):
        canonical_path(name)
        self.store.check(name)
        kind = classify(name, self.manifest)
        if kind == 'artifacts':
            raise ValueError('Controller artifacts are available only through read_evidence')
        if writing:
            if not ((self.role == 'qa' and kind in TEST_KINDS)
                    or (self.role == 'dev' and kind == 'production')):
                raise ValueError('Role cannot write this path')
        elif self.role != 'analysis' and kind not in TEST_KINDS:
            assigned = self._assigned_sources()
            if name not in assigned:
                raise ValueError('Source is not assigned; ask_analysis for this information')
        return name

    def _assigned_sources(self):
        refs = self.context.get('source_refs', []) + self.active_job.get('refs', [])
        for answer in self.answers.values():
            refs += answer.get('refs', [])
        return {self.evidence[r]['path'] for r in refs if r in self.evidence and 'path' in self.evidence[r]}

    def _record(self, result, **metadata):
        record = copy.deepcopy(result) | {'evidence_id': self._new_id('ev'),
                                         'versions': dict(self.versions), **metadata}
        self.evidence[record['evidence_id']] = record
        write(self.directory / 'evidence' / (record['evidence_id'] + '.json'), record)
        return copy.deepcopy(record)

    def _refs_current(self, refs, *, issue=True, issue_ids=()):
        if not isinstance(refs, list):
            return False
        for ref in refs:
            if not isinstance(ref, str):
                return False
            if issue and ref.startswith('issue:') and (ref[6:] in self.issue
                    or ref[6:] in self.requirements or ref[6:] in issue_ids or ref == 'issue:original'):
                continue
            record = self.evidence.get(ref)
            if not record:
                return False
            if record.get('kind') == 'file':
                if self.store.inventory().get(record['path']) != record['sha256']:
                    return False
            elif record.get('versions') != self.versions:
                return False
        return True

    def _validate_context(self, context, manifest):
        if not isinstance(context, dict) or any(k not in context for k in CONTEXT['required']):
            raise ValueError('Context needs requirements, facts, sources, tests, baseline, hypotheses and open questions')
        reqs = context['requirements']
        if not isinstance(reqs, list) or not reqs:
            raise ValueError('At least one issue-linked requirement is needed')
        ids = set()
        for req in reqs:
            if not isinstance(req, dict) or not all(req.get(k) for k in ('id', 'text', 'refs')):
                raise ValueError('Incomplete requirement')
            if req['id'] in ids or not self._refs_current(req['refs'], issue_ids=[req['id']]):
                raise ValueError('Invalid requirement references')
            ids.add(req['id'])
        if not self._refs_current(context['source_refs']):
            raise ValueError('Unknown or stale source reference; read the current source')
        for fact in context['facts']:
            if not fact.get('text') or not fact.get('refs') or not self._refs_current(fact['refs']):
                raise ValueError('Facts need current public references')
        for path in context['test_paths']:
            if classify(path, manifest) not in TEST_KINDS:
                raise ValueError('Test paths must identify test areas')
            self.store.check(path)
        if not context['test_command'] or not isinstance(context['open_questions'], list):
            raise ValueError('Missing test command or open questions')

    def _set_context(self, context, *, merge=False):
        context = (copy.deepcopy(self.context) | context) if merge else copy.deepcopy(context)
        manifest = dict(self.manifest)
        for assignment in context.get('path_assignments', []):
            path, kind = assignment['path'], assignment['kind']
            canonical_path(path)
            self.store.check(path)
            if not assignment['reason'] or not assignment['refs'] or not self._refs_current(assignment['refs']):
                raise ValueError('Path classification needs a reason and public evidence')
            for prefix, existing in manifest.items():
                if (path == prefix or path.startswith(prefix + '/') or prefix.startswith(path + '/')) and kind != existing:
                    raise ValueError('Classification cannot override existing production/test boundaries')
            manifest[path] = kind
        self._validate_context(context, manifest)
        self.manifest.clear()
        self.manifest.update(manifest)
        self.context = copy.deepcopy(context)
        self.context_revision += 1
        self.requirements = {r['id']: copy.deepcopy(r) for r in context['requirements']}
        self.open_questions = copy.deepcopy(context['open_questions'])
        self.open_questions += [{'id': p['request_id'], 'question': p['question'], 'blocking': True}
                                for p in self.pending if p.get('kind') == 'information']
        self.open_questions += list(copy.deepcopy(self.unresolved_answers).values())

    def _read(self, a):
        name = self._path(a['path'])
        start, end = a['line_start'], a['line_end']
        if type(start) is not int or type(end) is not int or not 1 <= start <= end:
            raise ValueError('Use inclusive one-based line bounds')
        inventory = self.store.inventory()
        if name not in inventory:
            self._path(name, writing=True)
            if start != 1 or end != 1:
                raise ValueError('Read a new file with line_start=1, line_end=1')
            result = {'status': 'completed', 'text': '', 'sha256': None, 'new_file': True}
        else:
            result = self.execute({'action': 'read_file', 'path': name,
                                   'line_start': start, 'line_end': end})
        if result.get('status') != 'completed':
            return result
        digest = inventory.get(name)
        if self.store.inventory().get(name) != digest:
            raise ValueError('File changed during read; read again')
        if result.get('truncated'):
            # A handle must never authorize replacement of unread trailing lines.
            end = min(end, start + len(result['text'].splitlines()) - 1)
            if end < start:
                raise ValueError('Read returned no complete lines; use a smaller region')
            result['text'] = ''.join(self.store.read(name).decode().splitlines(keepends=True)[start - 1:end])
        handle = self._new_id('file')
        self.handles[handle] = {'path': name, 'sha256': digest, 'start': start, 'end': end}
        return self._record(result | {'handle': handle, 'path': name, 'sha256': digest}, kind='file')

    def _edit(self, a):
        handle = self.handles.get(a['handle'])
        if not handle:
            raise ValueError('Unknown read handle')
        name = self._path(handle['path'], writing=True)
        if self.role == 'dev' and not any(
                e.get('kind') == 'test' and not e.get('baseline')
                and all(e.get('versions', {}).get(k) == self.versions[k] for k in ('tests', 'environment'))
                and set(self.targets) <= set(e.get('targets', [])) for e in self.evidence.values()):
            raise ValueError('Run the current focused tests before editing production')
        digest = self.store.inventory().get(name)
        if digest != handle['sha256']:
            self.metrics['edit_conflicts'] += 1
            data = self.store.read(name).decode() if digest is not None else ''
            lines = data.splitlines(keepends=True)
            return {'status': 'rejected', 'code': 'edit_conflict',
                    'current_text': ''.join(lines[handle['start'] - 1:handle['end']]),
                    'hint': 'Read the current region and use its new handle.'}
        if not a.get('reason') or not isinstance(a.get('new_text'), str):
            raise ValueError('Edit needs new_text and an issue-grounded reason')
        if len(a['new_text'].encode()) > 12000:
            raise ValueError('Use a smaller edit')
        original = self.store.read(name).decode() if digest is not None else ''
        lines = original.splitlines(keepends=True)
        if digest is not None and handle['start'] > len(lines) + 1:
            raise ValueError('Edit starts beyond end of file')
        lines[handle['start'] - 1:handle['end']] = [a['new_text']]
        candidate = ''.join(lines)
        if name.endswith('.py'):
            compile(candidate, name, 'exec')
        concrete = {'action': 'replace_region', 'path': name, 'start': handle['start'],
                    'end': handle['end'], 'new_text': a['new_text'], 'expected_sha256': digest}
        if digest is None:
            concrete = {'action': 'create_test_file' if self.role == 'qa' else 'create_source_file',
                        'path': name, 'content': candidate, 'reason': a['reason']}
        result = self.execute(concrete)
        self._refresh()
        if result.get('status') == 'completed' and self.role == 'dev' and self.metrics['first_production_change_call'] is None:
            self.metrics['first_production_change_call'] = self.metrics['model_calls']
            self.metrics['first_production_change_seconds'] = self.clock() - self.started
            self._milestone('production_change')
        return result

    def _navigate(self, a):
        op = a['action']
        inventory = self.store.inventory()
        names = sorted(inventory)
        if op == 'repo_overview':
            return {'status': 'completed', 'roots': sorted({n.split('/')[0] for n in names}), 'files': names[:80]}
        if op == 'read_environment':
            return {'status': 'completed', 'files': [n for n in names if classify(n, self.manifest) == 'environment'],
                    'test_command': 'python -m pytest', **self.environment}
        if 'start' in a:
            return {'status': 'rejected', 'code': 'invalid_parameter', 'error': 'Use the returned opaque cursor, not offsets'}
        params = {k: a[k] for k in ('action', 'pattern', 'scope', 'query') if k in a}
        signature = identity([params, inventory])
        offset = 0
        if a.get('cursor') is not None:
            item = self.cursors.get(a['cursor']) if isinstance(a['cursor'], str) else None
            if not item or item['signature'] != signature:
                return {'status': 'cursor_error', 'hits': [], 'error': 'Cursor does not match this tool, query and source version'}
            offset = item['offset']
        if op == 'find_paths':
            items = [n for n in names if fnmatch.fnmatchcase(n, a['pattern'])]
            field = 'paths'
        else:
            scope = a['scope']
            if scope != '.':
                canonical_path(scope)
                self.store.check(scope)
            selected = [n for n in names if scope == '.' or n == scope or n.startswith(scope + '/')]
            if not selected and scope not in self.manifest:
                return {'status': 'scope_not_found', 'scope_exists': False, 'hits': [],
                        'candidates': names[:80], 'hint': 'Choose an existing public scope.'}
            items, field = [], 'hits'
            for name in selected:
                try:
                    lines = self.store.read(name).decode().splitlines()
                except UnicodeError:
                    continue
                for line, text in enumerate(lines, 1):
                    if a['query'] in text:
                        items.append({'path': name, 'line': line, 'text': text})
        size = max(1, self.policy['search_page_size'])
        cursor = None
        if offset + size < len(items):
            cursor = self._new_id('page')
            self.cursors[cursor] = {'signature': signature, 'offset': offset + size}
        return {'status': 'completed', field: items[offset:offset + size], 'next_cursor': cursor,
                'scope_exists': True, 'hint': 'find_paths searches filenames; use search_content for literal text in files.'}

    def _targets(self, targets):
        if not isinstance(targets, list) or not targets or len(targets) > 20:
            raise ValueError('Supply concrete test paths or pytest node IDs')
        for node in targets:
            if not isinstance(node, str) or node.startswith('-'):
                raise ValueError('Invalid test target')
            path = node.split('::', 1)[0]
            if classify(path, self.manifest) not in TEST_KINDS:
                raise ValueError('Target is outside the test area')
            self.store.check(path)

    def _run(self, a):
        self._targets(a['targets'])
        before = dict(self.versions)
        baseline = bool(a.get('baseline'))
        root = self.store.baseline() if baseline else None
        try:
            concrete = {'action': a['action'], 'targets': list(a['targets'])}
            if a['action'] == 'run_tests':
                concrete['baseline'] = baseline
            if root:
                concrete['workspace'] = root
            if self.clock() >= self.started + self.policy['wall_seconds']:
                result = {'status': 'tool_error', 'observation': 'timeout', 'timed_out': True,
                          'error': 'Shared deadline expired during test preparation'}
            else:
                result = self.execute(concrete)
        finally:
            if root:
                self.store.remove_baseline(root)
        self._refresh()
        # Bind to the state at launch; a concurrent change invalidates the result.
        if baseline:
            before['production'] = self.original_production
        result = copy.deepcopy(result)
        cases = result.get('case_results', {})
        for cid, case in self.cases.items():
            node = case['pytest_node']
            if cid not in cases and node in cases:
                cases[cid] = copy.deepcopy(cases[node])
            elif cid not in cases:
                matches = [v for k, v in cases.items() if k.startswith(node + '[')]
                if matches:
                    states = [v.get('outcome') for v in matches]
                    state = ('pass' if all(s == 'pass' for s in states) else 'assertion_failure'
                             if all(s in {'pass', 'assertion_failure'} for s in states) else 'invalid_test_run')
                    cases[cid] = {'executed': all(v.get('executed') for v in matches), 'outcome': state,
                        **{k: sum(v.get(k, 0) for v in matches) for k in
                           ('ebt_executed', 'ebt_evaluated', 'ebt_passed', 'ebt_evaluation_checked')}}
        if cases:
            result['case_results'] = cases
        for key in ('ebt_executed', 'ebt_evaluated', 'ebt_passed', 'ebt_evaluation_checked'):
            self.metrics[key] += result.get('framework_usage', {}).get(key, 0)
        if a['action'] == 'run_tests':
            self._milestone('test_run')
        return self._record(result, versions=before, kind='collection' if a['action'] == 'collect_tests' else 'test',
                            targets=list(a['targets']), baseline=baseline, case_signature=identity(self.cases))

    def _executed(self, e):
        diagnostics = e.get('diagnostics', {})
        counts = diagnostics.get('counts', {})
        return (e.get('kind') == 'test' and e.get('status') == 'completed'
                and not e.get('collection_only') and not e.get('timed_out')
                and diagnostics.get('executed', 0) > 0 and not counts.get('errors', 0)
                and not diagnostics.get('invalid_xml') and not counts.get('skipped', 0))

    def _red(self, e):
        if not (self._executed(e) and e.get('observation') == 'assertion_failure'
                and e['versions']['production'] == self.original_production
                and all(e['versions'][k] == self.versions[k] for k in ('tests', 'environment'))
                and e.get('case_signature') == identity(self.cases)
                and set(self.targets) <= set(e.get('targets', [])) and self.cases):
            return False
        results = [e.get('case_results', {}).get(cid, {}) for cid in self.cases]
        return (all(c.get('executed') and c.get('outcome') in {'pass', 'assertion_failure'} for c in results)
                and any(c.get('outcome') == 'assertion_failure' for c in results)
                and all(err.get('type') in {'AssertionError', 'Failed'}
                        or (err.get('type') is None and 'AssertionError' in err.get('traceback_tail', ''))
                        for err in e.get('diagnostics', {}).get('errors', [])))

    def _green(self, e):
        counts = e.get('diagnostics', {}).get('counts', {})
        return (self._executed(e) and e.get('observation') == 'pass' and e.get('exit_code') == 0
                and not counts.get('failed') and not e.get('xfail') and not e.get('xpass'))

    def _green_cases(self, e):
        if (not self._green(e) or not set(self.targets) <= set(e.get('targets', []))
                or e.get('case_signature') != identity(self.cases)):
            return False
        for cid in self.cases:
            case = e.get('case_results', {}).get(cid, {})
            if not case.get('executed') or case.get('outcome') != 'pass':
                return False
            if self.mode == 'cubie' and not all(case.get(k, 0) > 0 for k in
                    ('ebt_executed', 'ebt_evaluated', 'ebt_passed', 'ebt_evaluation_checked')):
                return False
        return bool(self.cases)

    def _qualify(self):
        self.qualifications['reproduced'] = any(self._red(e) for e in self.evidence.values())
        if self.qualifications['reproduced'] and self.metrics['first_red_call'] is None:
            self.metrics['first_red_call'] = self.metrics['model_calls']
            self.metrics['first_red_seconds'] = self.clock() - self.started
            self._milestone('red')

    def _regression_ok(self, evidence):
        for target in self.regressions:
            current = [e for e in evidence if target in e.get('targets', [])]
            if not current:
                return False
            last = current[-1]
            if self._green(last):
                continue
            # Compare actual failing nodes/types/messages, not just failure counts.
            def failures(e):
                return {identity({k: err.get(k) for k in ('node', 'id', 'type', 'message')})
                        for err in e.get('diagnostics', {}).get('errors', [])}
            if not self._executed(last) or last.get('observation') != 'assertion_failure' or not failures(last):
                return False
            baseline = [e for e in self.evidence.values() if e.get('baseline')
                and e.get('targets') == last.get('targets') and self._executed(e)
                and all(e['versions'][k] == self.versions[k] for k in ('tests', 'environment'))]
            if not baseline or not failures(last) <= failures(baseline[-1]):
                return False
        return True

    def _completion_check(self, delivery):
        self._refresh()
        refs = delivery.get('evidence_refs', [])
        if (self.state != 'review' or self.pending or self.review_versions != self.versions
                or not self.diff_ref or self.diff_ref not in self.inspected
                or delivery.get('open_points') or self.active_job.get('open_points')
                or any(q.get('blocking', True) for q in self.open_questions)
                or not self.requirements or not self.cases or not delivery.get('reason')
                or set(delivery.get('requirement_ids', [])) != set(self.requirements)
                or {c['requirement_id'] for c in self.cases.values()} != set(self.requirements)
                or not refs or any(r not in self.evidence or r not in self.inspected for r in refs)):
            return False
        reproduction = any(self._red(self.evidence[r]) for r in refs)
        existing_coverage = (bool(delivery.get('existing_coverage_reason'))
            and self.versions['production'] != self.original_production
            and any(self.evidence[r].get('versions', {}).get('production') == self.original_production
                    and all(self.evidence[r]['versions'][k] == self.versions[k] for k in ('tests', 'environment'))
                    and self._green_cases(self.evidence[r]) for r in refs))
        if not (reproduction or existing_coverage):
            return False
        current = [self.evidence[r] for r in refs if self.evidence[r].get('versions') == self.versions
                   and self.evidence[r].get('case_signature') == identity(self.cases)
                   and not self.evidence[r].get('baseline') and self.evidence[r].get('kind') == 'test']
        focused = [e for e in current if set(self.targets) <= set(e.get('targets', []))]
        return bool(focused and self._green_cases(focused[-1]) and self._regression_ok(current))

    def _finish_delivery(self, d):
        if not isinstance(d, dict):
            raise TypeError('finish needs a delivery')
        if self.role == 'analysis':
            if self.state == 'information':
                if not d.get('answer') or 'unresolved' not in d or not self._refs_current(d.get('refs', [])):
                    raise ValueError('Answer needs current references and explicit uncertainty')
                saved = self.pending.pop()
                self.answers[saved['question']] = copy.deepcopy(d)
                self.role, self.state, self.active_job = saved['role'], saved['state'], saved['job']
                self.active_job['answer'] = copy.deepcopy(d)
                self.active_job['refs'] = d.get('refs', [])
                self.open_questions = [q for q in self.open_questions if q.get('id') != saved['request_id']]
                if d['unresolved']:
                    question = {'id': saved['request_id'], 'question': saved['question'], 'blocking': True}
                    self.unresolved_answers[saved['question']] = question
                    self.open_questions.append(question)
                else:
                    old = self.unresolved_answers.pop(saved['question'], None)
                    if old:
                        self.open_questions = [q for q in self.open_questions if q.get('id') != old['id']]
                return {'status': 'completed'}
            if d.get('verdict') == 'rework':
                if self.state != 'review' or d.get('next_role') not in {'qa', 'dev'} or not d.get('task'):
                    raise ValueError('Review rework needs next_role and a concrete task')
                self._activate(d['next_role'], 'tests' if d['next_role'] == 'qa' else 'implement', d['task'])
                return {'status': 'completed'}
            if d.get('verdict') == 'verified':
                if not self._completion_check(d):
                    raise ValueError('Missing current focused/baseline/regression evidence, review or resolved requirements; request concrete rework')
                self.status, self.reason = 'submitted', 'verified'
                self.qualifications['verified'] = True
                self.metrics['verified_seconds'] = self.clock() - self.started
                self._milestone('verification')
                self.completion = {'allowed': True, 'status': 'verified_green', 'judgment': 'model_review',
                                   'scope': {'focused': list(self.targets), 'regressions': list(self.regressions)}}
                if any(not self._green(self.evidence[r]) and self.evidence[r].get('kind') == 'test'
                       and self.evidence[r].get('versions') == self.versions
                       and not self.evidence[r].get('baseline')
                       and set(self.regressions) & set(self.evidence[r].get('targets', []))
                       for r in d['evidence_refs']):
                    self.completion['status'] = 'verified_with_baseline_failures'
                return {'status': 'completed'}
            if self.state != 'orient':
                raise ValueError('This analysis job needs an answer or review delivery')
            self._set_context(d)
            self._activate('qa', 'tests', 'Create the first issue-grounded case, collect it and deliver test targets.')
            return {'status': 'completed'}
        if self.role == 'qa':
            if d.get('accepted') is False:
                if self.state != 'test_change' or not d.get('reason') or 'unresolved' not in d:
                    raise ValueError('A test-change refusal needs a reason and explicit uncertainty')
                recipient = 'analysis' if d['unresolved'] else 'dev'
                self._activate(recipient, 'review' if d['unresolved'] else 'implement',
                               'Resolve the test-oracle disagreement.' if d['unresolved'] else 'Continue production repair.',
                               test_change_response=d)
                return {'status': 'completed'}
            cases = d.get('cases')
            if not isinstance(cases, list) or not cases:
                raise ValueError('Suite needs complete cases')
            registered = {}
            for case in cases:
                if (not isinstance(case, dict) or any(k not in case for k in
                        ('case_id', 'requirement_id', 'input', 'expected', 'reason', 'reason_ref', 'pytest_node'))
                        or not case['reason'] or not case['expected'] or not isinstance(case['input'], dict)
                        or case['requirement_id'] not in self.requirements
                        or not self._refs_current([case['reason_ref']]) or case['case_id'] in registered):
                    raise ValueError('Case needs requirement, concrete input, oracle, reason and public reference')
                self._targets([case['pytest_node']])
                registered[case['case_id']] = copy.deepcopy(case)
            self._targets(d.get('targets'))
            if not isinstance(d.get('regressions'), list):
                raise ValueError('Supply the agreed regression selection')
            if d['regressions']:
                self._targets(d['regressions'])
            if not all(c['pytest_node'] in d['targets'] for c in cases):
                raise ValueError('Targets must include all delivered cases')
            collections = [e for e in self.evidence.values() if e.get('kind') == 'collection'
                and all(e['versions'][k] == self.versions[k] for k in ('tests', 'environment'))
                and e.get('status') == 'completed' and e.get('observation') == 'collected'
                and set(d['targets']) <= set(e.get('targets', []))]
            if not collections:
                raise ValueError('Collect the current suite before delivery')
            self.cases, self.targets, self.regressions = registered, list(d['targets']), list(d['regressions'])
            if self.metrics['first_qa_delivery_seconds'] is None:
                self.metrics['first_qa_delivery_seconds'] = self.clock() - self.started
            self._milestone('suite')
            self._milestone('case')
            self.qualifications['verified'] = False
            self.completion = {'allowed': False, 'status': 'incomplete'}
            self._activate('dev', 'implement', 'Run the supplied cases first; repair production and verify focused tests and regressions.')
            self._qualify()
            return {'status': 'completed'}
        if not d.get('summary') or not d.get('evidence_refs') or 'open_points' not in d:
            raise ValueError('Implementation delivery needs summary, evidence_refs and open_points')
        if any(r not in self.evidence for r in d['evidence_refs']):
            raise ValueError('Unknown evidence')
        diff = self._record({'status': 'completed', 'text': self.store.patch()}, kind='diff')
        self.diff_ref, self.review_versions = diff['evidence_id'], dict(self.versions)
        self.inspected = set()
        self._activate('analysis', 'review', 'Review the issue, final case oracles, patch and execution details.',
                       summary=d['summary'], evidence_refs=d['evidence_refs'], diff_ref=self.diff_ref,
                       open_points=d['open_points'])
        return {'status': 'completed', 'diff_ref': self.diff_ref}

    def _ask(self, a):
        if not a.get('question') or not a.get('reason'):
            raise ValueError('Ask a specific question with the reason it is needed')
        answer = self.answers.get(a['question'])
        if answer and not answer['unresolved'] and answer.get('refs') and self._refs_current(answer['refs']):
            self.active_job['answer'] = copy.deepcopy(answer)
            return {'status': 'completed', 'cached': True, 'request_id': self._new_id('answer'), **answer}
        rid = self._new_id('question')
        self.pending.append({'request_id': rid, 'kind': 'information', 'role': self.role,
                             'state': self.state, 'job': copy.deepcopy(self.active_job), 'question': a['question']})
        self.open_questions.append({'id': rid, 'question': a['question'], 'blocking': True})
        self.metrics['information_requests'] += 1
        self._activate('analysis', 'information', a['question'], reason=a['reason'])
        return {'status': 'completed', 'request_id': rid}

    def _perform(self, a):
        op = a['action']
        if op == 'read_file':
            return self._read(a)
        if op in {'edit_tests', 'edit_source'}:
            return self._edit(a)
        if op in {'repo_overview', 'read_environment', 'find_paths', 'search_content'}:
            return self._navigate(a)
        if op in {'collect_tests', 'run_tests'}:
            return self._run(a)
        if op == 'read_evidence':
            if a['ref'] not in self.evidence:
                raise ValueError('Unknown public evidence reference')
            self.inspected.add(a['ref'])
            return copy.deepcopy(self.evidence[a['ref']])
        if op == 'update_context':
            self._set_context(a['context'], merge=True)
            return {'status': 'completed'}
        if op == 'finish':
            return self._finish_delivery(a['delivery'])
        if op == 'ask_analysis':
            return self._ask(a)
        if op == 'request_test_change':
            if not all(a.get(k) for k in ('case_id', 'observed', 'suspected_error', 'evidence_refs')):
                raise ValueError('Test change needs case_id, observed, suspected_error, evidence_refs')
            if a['case_id'] not in self.cases or any(r not in self.evidence for r in a['evidence_refs']):
                raise ValueError('Test change must identify a real case and runner evidence')
            self.metrics['revision_rounds'] += 1
            self._activate('qa', 'test_change', 'Assess the requested test change against the original issue.',
                           change_request={k: v for k, v in a.items() if k != 'action'})
            return {'status': 'completed'}
        raise ValueError('Unknown action')

    def _recovery(self):
        self.active_job['decision_required'] = True
        self.active_job['decision'] = 'Use the existing result. Deliver, ask a concrete question, or choose a different justified action.'
        self.metrics['recoveries'] += 1
        if self.active_job.get('repeat_count', 0) < 3:
            return
        if self.state == 'orient':
            self._activate('qa', 'tests', 'Use the existing knowledge to build a first case; ask analysis about unresolved oracle information.')
        elif self.role in {'qa', 'dev'}:
            self._ask({'question': 'Which concrete next step resolves the current stalled job?',
                       'reason': 'Repeated identical actions supplied no new evidence.'})
        elif self.state == 'information':
            self._finish_delivery({'answer': 'No additional evidence was obtained. The information gap remains open.',
                                   'refs': [], 'unresolved': True})
        elif self.state == 'review':
            self._activate('dev', 'implement', 'Supply missing current focused and regression evidence; resolve the review gap.',
                           evidence_refs=self.active_job.get('evidence_refs', []))

    def dispatch(self, role, action):
        self.advance()
        before = self.clock()
        job_id = self.active_job['id']
        cache_key = None
        try:
            if self.status != 'running' or role != self.role:
                raise ValueError('Role is not active or the shared deadline has expired')
            if not isinstance(action, dict):
                raise TypeError('Return one JSON action object')
            allowed = {e['properties']['action']['const']: e for e in self.schemas[role]['oneOf']}
            op = action.get('action')
            if op not in allowed:
                raise ValueError('Tool is unavailable to this role')
            entry = allowed[op]
            if any(k not in action for k in entry['required']):
                raise ValueError('Missing required action fields')
            if set(action) - set(entry['properties']) - {'note'}:
                raise ValueError('Unknown action parameter')
            try:
                validate({k: v for k, v in action.items() if k != 'note'}, entry)
            except AdapterError as error:
                raise ValueError(str(error)) from error
            # A free audit note never changes effective action identity.
            effective = {k: v for k, v in action.items() if k not in {'note', 'reason'}}
            if op == 'run_tests':
                effective.setdefault('baseline', False)
                effective.setdefault('fresh', False)
            cacheable = op in {'read_file', 'find_paths', 'search_content', 'repo_overview', 'read_environment', 'run_tests'}
            if action.get('fresh') and not action.get('reason'):
                raise ValueError('A fresh independent run needs a reason')
            cache_key = identity([role, job_id, effective, self.store.inventory()])
            if cacheable and not action.get('fresh') and cache_key in self.cache:
                result = copy.deepcopy(self.cache[cache_key]) | {'cached': True}
                self.metrics['duplicate_actions'] += 1
                self.active_job['repeat_count'] = self.active_job.get('repeat_count', 1) + 1
                self._recovery()
            else:
                result = self._perform(action)
                if cacheable and result.get('status') == 'completed' and not action.get('fresh'):
                    self.cache[cache_key] = copy.deepcopy(result)
                if self.active_job['id'] == job_id:
                    self.active_job['repeat_count'] = 1
                    self.active_job['decision_required'] = False
                if self.active_job['id'] == job_id:
                    history = self.histories[role]
                    history[:] = [h for h in history if h['key'] != cache_key]
                    history.append({'key': cache_key, 'action': copy.deepcopy(action), 'result': copy.deepcopy(result)})
                    del history[:-4]
        except (ValueError, KeyError, TypeError, OSError, SyntaxError) as error:
            result = {'status': 'rejected', 'code': 'invalid_action', 'error': str(error)}
            self.last_error = str(error)
        self.metrics['tool_calls'] += 1
        if result.get('status') != 'completed':
            self.metrics['tool_errors'] += 1
        if result.get('status') in {'cursor_error', 'scope_not_found'}:
            self.metrics['cursor_errors' if result['status'] == 'cursor_error' else 'scope_not_found'] += 1
        if role in self.metrics['roles']:
            self.metrics['roles'][role]['tool_calls'] += 1
            self.metrics['roles'][role]['tool_seconds'] += self.clock() - before
        write(self.directory / 'actions' / f'{self.metrics["tool_calls"]:06d}.json',
              {'role': role, 'job_id': job_id, 'action': action, 'result': result})
        self._refresh()
        self.advance()
        self._archive()
        return result

    def request(self):
        self.advance()
        if self.status != 'running':
            return None
        history = copy.deepcopy(self.histories[self.role][-4:])
        # Positive list: no controller ledger, raw metrics, hashes or private data.
        materials = []
        for ref in self.context.get('source_refs', []):
            e = self.evidence.get(ref, {})
            if e.get('kind') == 'file':
                if self._refs_current([ref]):
                    materials.append({'ref': ref, 'path': e['path'], 'text': e['text']})
                else:
                    materials.append({'ref': ref, 'path': e['path'], 'stale': True,
                                      'instruction': 'Read current source before relying on this reference.'})
        names = sorted(self.store.inventory())
        payload = {'issue': self.issue, 'job': copy.deepcopy(self.active_job),
            'issue_ref': 'issue:original',
            'knowledge': self.context, 'materials': materials,
            'start': {'layout': sorted({n.split('/')[0] for n in names}),
                      **self.environment, 'test_command': self.context.get('test_command', 'python -m pytest')},
            'remaining_seconds': max(0, self.started + self.policy['wall_seconds'] - self.clock())}
        if self.role in {'qa', 'dev'} or self.state == 'review':
            payload['suite'] = {'cases': self.cases, 'targets': self.targets, 'regressions': self.regressions}
        if self.last_error:
            payload['action_error'] = self.last_error
        system = self.prompts[self.role]
        if self.role == 'qa':
            system += '\nFramework guide:\n' + self.guide
        schema = copy.deepcopy(self.schemas[self.role])

        def build(dialogs):
            messages = [{'role': 'system', 'content': system},
                        {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}]
            for dialog in dialogs:
                messages.extend([{'role': 'assistant', 'content': json.dumps(dialog['action'], ensure_ascii=False)},
                                 {'role': 'user', 'content': json.dumps(self._brief(dialog['result']), ensure_ascii=False)}])
            return {'role': self.role, 'messages': messages, 'schema': schema, 'history': dialogs,
                    'job': copy.deepcopy(self.active_job),
                    'timeout_seconds': max(0.001, self.started + self.policy['wall_seconds'] - self.clock())}
        request = build(history)
        # Measure the full inference payload, including the schema. Output space is
        # already reserved by context_capacity in the runtime adapter.
        def size(r):
            return len(json.dumps({'messages': r['messages'], 'schema': r['schema']}, ensure_ascii=False).encode())
        while len(history) > 1 and size(request) > self.policy['context_bytes']:
            history.pop(0)
            request = build(history)
        if size(request) > self.policy['context_bytes']:
            self.last_error = 'Mandatory issue, knowledge, materials and schema exceed the input budget; request smaller source sections.'
            return {'status': 'context_error', 'error': self.last_error}
        self.metrics['model_calls'] += 1
        self.metrics['context_requests'].append({'role': self.role, 'bytes': size(request),
            'history_dialogs': len(history), 'knowledge_chars': len(json.dumps(self.context, ensure_ascii=False))})
        self.metrics['roles'][self.role]['model_calls'] += 1
        write(self.directory / 'steps' / f'{self.metrics["model_calls"] - 1:04d}-request.json', request)
        self._archive()
        return request

    @staticmethod
    def _brief(result):
        return {k: copy.deepcopy(v) for k, v in result.items()
                if k not in {'versions', 'sha256', 'framework_usage', 'kind'}}

    def record_response(self, response, seconds):
        write(self.directory / 'steps' / f'{self.metrics["model_calls"] - 1:04d}-response.json', response)
        stats = self.metrics['roles'][self.role]
        stats['model_seconds'] += seconds
        usage = response.get('usage', {})
        stats['input_tokens'] += usage.get('input_tokens', 0) or 0
        stats['output_tokens'] += usage.get('output_tokens', 0) or 0

    def reject_output(self, *, raw, usage, seconds, status='invalid_output'):
        self.record_response({'raw': raw, 'usage': usage, 'status': status}, seconds)
        self.metrics['output_repairs'] += 1
        self.last_error = f'{status}: Return one complete action matching the current role schema.'
        self.advance()
        self._archive()
