"""V9 serial team with automatic evidence memory and transactional handoffs.

Runner execution facts and safe versioned edits reuse the V8 implementation.
V9 owns navigation, deliveries, persistence and the explicit Markdown renderer.
The persist port accepts one complete transaction before state is committed.
"""

import copy
import difflib
import fnmatch
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from ollama_agents.client import OllamaClient
from ollama_agents.errors import AdapterError
from ollama_agents.schema import validate

from .artifacts import write
from .iteration import identity
from .team_v8 import V8LocalWorkspace, V8TeamController
from .team_v9_design import POLICY, PROMPTS, SCHEMAS
from .team_workspace import (
    IGNORED,
    PRIVATE,
    TEST_KINDS,
    RemoteWorkspace,
    canonical_path,
    classify,
    inferred_manifest,
    versions,
)


class PersistenceError(OSError):
    """The transaction port did not acknowledge a durable commit."""


class V9OllamaClient(OllamaClient):
    """Normalize legacy search cursors before the strict V9 action validation."""

    def _action(self, raw, schema):
        compatible = copy.deepcopy(schema)
        for entry in compatible.get('oneOf', []):
            if entry.get('properties', {}).get('action', {}).get('const') in {'find_paths', 'search_content'}:
                entry['properties']['cursor'] = True
        action = super()._action(raw, compatible)
        if action.get('action') in {'find_paths', 'search_content'}:
            action.pop('cursor', None)
        validate(action, schema)
        return action


def public_entry(name, manifest):
    """Inventory ports may include private names as files, e.g. a worktree .git."""
    try:
        canonical_path(name)
    except ValueError:
        return False
    try:
        return classify(name, manifest) != 'artifacts'
    except ValueError:
        return True  # Public reading does not confer a write classification.


class V9LocalWorkspace(V8LocalWorkspace):
    """Public reads include files without a write classification."""

    def inventory(self):
        result = {}
        for folder, dirs, names in os.walk(self.root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in PRIVATE | IGNORED
                             and not (Path(folder) / d).is_symlink())
            for name in sorted(names):
                path = Path(folder) / name
                relative = path.relative_to(self.root).as_posix()
                if path.is_file() and not path.is_symlink() and public_entry(relative, self.manifest):
                    result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        return result

    def __init__(self, root, manifest):
        # Unclassified public files are readable, but never implicitly writable.
        self.root, self.manifest = Path(root).resolve(), dict(manifest)
        self.initial_files = {p: self.read(p) for p in self.inventory()}
        self.original = {p: data for p, data in self.initial_files.items()
                         if self.kind(p) == 'production'}

    def kind(self, name):
        try:
            return classify(name, self.manifest)
        except ValueError:
            return 'environment'


    def baseline(self):
        root = Path(tempfile.mkdtemp(prefix='v9-baseline-', dir=self.root.parent))
        try:
            for name in self.inventory():
                if self.kind(name) in TEST_KINDS | {'environment'}:
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(self.read(name))
            for name, data in self.original.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        except BaseException:
            shutil.rmtree(root)
            raise
        return str(root)

    def production_patch(self):
        current = {p: self.read(p) for p in self.inventory() if self.kind(p) == 'production'}
        result = []
        for name in sorted(self.original.keys() | current.keys()):
            old, new = self.original.get(name, b''), current.get(name, b'')
            if old != new:
                result.extend(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True),
                    fromfile='a/' + name if name in self.original else '/dev/null',
                    tofile='b/' + name if name in current else '/dev/null'))
        return ''.join(result)


class V9RemoteWorkspace(RemoteWorkspace):
    """Include unclassified public paths in navigation, preserving write policy."""

    def __init__(self, manager, sandbox, timeout=10):
        self.manager, self.sandbox, self.timeout = manager, sandbox, timeout
        original = {p: digest for p, digest in self._call(op='inventory').items() if public_entry(p, {})}
        self.original_names = set(original)
        self.manifest = inferred_manifest(self.original_names)
        self.original_production = versions(original, self.manifest)['production']

    def inventory(self):
        return {p: digest for p, digest in self._call(op='inventory').items() if public_entry(p, self.manifest)}


class V9TeamController(V8TeamController):
    def __init__(self, *, persist=None, baseline=None, store=None, policy=None, design=None, **kwargs):
        self.runner_artifacts = set()
        self.deliveries, self.baseline_ref = [], None
        self.verification_status = 'incomplete'
        self.persist = persist
        self._transaction_serial = 0
        self._in_transaction = False
        store = store or V9LocalWorkspace(kwargs['workspace'], kwargs['manifest'])
        super().__init__(store=store, policy=POLICY | (policy or {}), design=None, **kwargs)
        self.prompts = copy.deepcopy(design['core']['context']['roles'] if design else PROMPTS)
        self.schemas = copy.deepcopy(design['core']['context']['schemas'] if design else SCHEMAS)
        self._refresh()
        self.original_production = self.versions['production']
        if baseline is not None:
            self.set_baseline(baseline)
        self._archive()

    def _refresh(self):
        inventory = {p: h for p, h in self.store.inventory().items() if p not in self.runner_artifacts}
        manifest = dict(self.manifest)
        for name in inventory:
            try:
                classify(name, manifest)
            except ValueError:
                manifest[name] = 'environment'
        current = versions(inventory, manifest)
        if current != self.versions:
            self.versions = current
            self.qualifications['verified'] = False
            self.completion = {'allowed': False, 'status': 'incomplete'}
            self.verification_status = 'incomplete'
        self._qualify()

    def _snapshot(self):
        return super()._snapshot() | {'deliveries': copy.deepcopy(self.deliveries),
                                     'verification_status': self.verification_status}

    def _archive(self):
        if not self._in_transaction:
            super()._archive()

    def _record(self, result, **metadata):
        record = copy.deepcopy(result) | {'evidence_id': self._new_id('ev'),
            'versions': dict(self.versions), 'origin_role': self.role,
            'origin_job': self.active_job['id'], **metadata}
        self.evidence[record['evidence_id']] = record
        return copy.deepcopy(record)

    def set_baseline(self, result):
        serial = self.serial
        record = self._record(result, kind='baseline', baseline=True)
        try:
            self._persist_transaction({'kind': 'baseline', 'evidence': record})
        except PersistenceError:
            self.serial = serial
            self.evidence.pop(record['evidence_id'])
            raise
        self.baseline_ref = record['evidence_id']

    def _persist_transaction(self, transaction):
        transaction = {'sequence': self._transaction_serial, **transaction}
        try:
            if self.persist is not None:
                self.persist(copy.deepcopy(transaction))
            else:
                write(self.directory / 'transactions' / f'{self._transaction_serial:06d}.json', transaction)
        except Exception as error:
            raise PersistenceError(str(error)) from error
        self._transaction_serial += 1

    def _path(self, name, *, writing=False):
        canonical_path(name)
        self.store.check(name)
        if writing:
            kind = classify(name, self.manifest)
            if not ((self.role == 'qa' and kind in TEST_KINDS)
                    or (self.role == 'dev' and kind == 'production')):
                raise ValueError('Role cannot write this path')
        else:
            try:
                kind = classify(name, self.manifest)
            except ValueError:
                kind = None
            if kind == 'artifacts':
                raise ValueError('Use read_evidence for controller artifacts')
        return name

    def _read(self, a):
        result = super()._read(a)
        if result.get('status') == 'completed':
            handle = self.handles[result['handle']]
            total = len(self.store.read(result['path']).decode().splitlines()) if not result.get('new_file') else 0
            handle['end'] = min(handle['end'], total) if total else 0
            result.update(line_start=handle['start'], line_end=handle['end'], current=True)
            self.evidence[result['evidence_id']].update(result)
        return result

    def _edit(self, a):
        handle = self.handles.get(a['handle'])
        if not handle:
            raise ValueError('Unknown read handle')
        name = self._path(handle['path'], writing=True)
        if self.role == 'dev' and handle['sha256'] is not None and not any(
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

    def _run(self, a):
        before = set(self.store.inventory())
        execute = self.execute

        def tracked_execute(concrete):
            result = execute(concrete)
            if concrete['action'] == 'collect_tests' and 'test_ids' not in result:
                result = copy.deepcopy(result)
                result['test_ids'] = result.get('framework_usage', {}).get('test_ids', [])
            # New unclassified output files belong to the runner, not the project
            # environment. Existing files and classified files remain versioned.
            for name in self.store.inventory().keys() - before:
                try:
                    classify(name, self.manifest)
                except ValueError:
                    self.runner_artifacts.add(name)
            return result

        self.execute = tracked_execute
        try:
            return super()._run(a)
        finally:
            self.execute = execute

    def _navigate(self, a):
        op = a['action']
        names = sorted(self.store.inventory())
        if op == 'read_environment':
            return self._record({'status': 'completed', **self.environment}, kind='environment')
        if op == 'repo_overview':
            return self._record({'status': 'completed', 'paths': names[:50],
                                 'truncated': len(names) > 50}, kind='search')
        limit = min(50, self.policy['search_limit'])
        if op == 'find_paths':
            canonical_path(a['pattern'])
            matches = [n for n in names if fnmatch.fnmatchcase(n, a['pattern'])]
            result = {'paths': matches[:limit], 'pattern': a['pattern']}
        else:
            scope = a['scope']
            if scope not in {'', '.'}:
                self._path(scope)
                scoped = [n for n in names if n == scope or n.startswith(scope + '/')]
                if not scoped:
                    # An existing public directory can legitimately have no files.
                    exists = (self.root / scope).exists() if isinstance(self.store, V9LocalWorkspace) else False
                    if not exists:
                        candidates = difflib.get_close_matches(scope, names, n=5, cutoff=0.2)
                        return self._record({'status': 'scope_not_found', 'scope': scope,
                                             'candidates': candidates}, kind='search')
            else:
                scoped = names
            matches = []
            for name in scoped:
                for number, line in enumerate(self.store.read(name).decode('utf-8', 'replace').splitlines(), 1):
                    if a['query'] in line:
                        matches.append({'path': name, 'line': number, 'text': line})
            result = {'hits': matches[:limit], 'scope': scope, 'query': a['query']}
        truncated = len(matches) > limit
        return self._record({'status': 'completed', **result, 'truncated': truncated,
            **({'hint': 'Ergebnis begrenzt; Scope oder Suchtext eingrenzen.'} if truncated else {})}, kind='search')

    def _recovery(self):
        self.active_job['decision_required'] = True
        self.active_job['decision'] = ('Read existing findings, narrow the search, ask a specific '
                                       'knowledge question or finish the available delivery.')
        self.metrics['recoveries'] += 1

    def _perform(self, a):
        op = a['action']
        if op == 'finish':
            return self._deliver(a)
        if op == 'request_test_change':
            if a['case'] not in self.cases or any(
                    ref not in self.evidence or self.evidence[ref].get('kind') != 'test' for ref in a['evidence']):
                raise ValueError('Identify a current case and test execution evidence')
            self.metrics['revision_rounds'] += 1
            self._activate('qa', 'test_change', a['reason'], change_request=copy.deepcopy(a))
            return {'status': 'completed'}
        if op == 'read_evidence':
            ref = a['ref']
            if ref not in self.evidence:
                raise ValueError('Unknown public evidence reference')
            self.inspected.add(ref)
            e = copy.deepcopy(self.evidence[ref])
            e['current'] = self._refs_current([ref])
            return e
        return super()._perform(a)

    def _deliver(self, a):
        notes, role, job = a['notes'], self.role, copy.deepcopy(self.active_job)
        refs = list(dict.fromkeys(job.get('source_refs', []) + [
            r for r, e in self.evidence.items() if e.get('origin_job') == job['id']]))
        result = {'status': 'completed'}
        if role == 'analysis':
            if self.state == 'information':
                # V8 resumes exactly the saved job and retains unresolved questions.
                result = super()._finish_delivery({'answer': notes, 'refs': [r for r in refs
                    if self._refs_current([r])], 'unresolved': a.get('unresolved', False)})
            elif self.state == 'orient':
                if a.get('verdict'):
                    raise ValueError('Orientation cannot verify a repair')
                self._activate('qa', 'tests', 'Create a justified regression case and collect the suite.')
            elif self.state == 'review':
                if a.get('verdict') == 'rework':
                    if a.get('next_role') not in {'qa', 'dev'}:
                        raise ValueError('Rework needs a recipient')
                    self._activate(a['next_role'], 'tests' if a['next_role'] == 'qa' else 'implement', notes)
                elif a.get('verdict') == 'verified':
                    if not self._can_complete(a):
                        raise ValueError('Missing current reproduction, focus, regression, review or resolved questions')
                    self.status, self.reason = 'submitted', 'verified'
                    self.qualifications['verified'] = True
                    current = self._current_tests()
                    failures = any(not self._green(e) for e in current
                                   if set(e['targets']) & set(self.regressions))
                    self.verification_status = 'verified_with_baseline_failures' if failures else 'verified_green'
                    self.completion = {'allowed': True, 'status': self.verification_status,
                                       'judgment': 'model_review'}
                    self.metrics['verified_seconds'] = self.clock() - self.started
                else:
                    raise ValueError('Review needs verified or rework')
        elif role == 'qa':
            targets = a.get('test_targets')
            self._targets(targets)
            regressions = a.get('regressions')
            if not isinstance(regressions, list):
                raise ValueError('Supply agreed regressions')
            if regressions:
                self._targets(regressions)
            collections = [e for e in self.evidence.values() if e.get('kind') == 'collection'
                and e.get('status') == 'completed' and e.get('observation') == 'collected'
                and all(e['versions'][k] == self.versions[k] for k in ('tests', 'environment'))
                and all(any(node == target or node.startswith(target + '[')
                            or ('::' not in target and node.startswith(target + '::'))
                            for node in e.get('test_ids', [])) for target in targets)]
            if not collections:
                raise ValueError('Collect all current test targets before delivery')
            # QA supplies its explanation in ordinary notes/tests. Analysis judges
            # the oracle; keyword matching cannot establish a justified expectation.
            self.targets, self.regressions = list(targets), list(regressions)
            collected = collections[-1]['test_ids']
            nodes = list(dict.fromkeys(node.split('[', 1)[0] for node in collected if any(
                node == target or node.startswith(target + '[')
                or ('::' not in target and node.startswith(target + '::')) for target in targets)))
            self.cases = {node: {'pytest_node': node} for node in nodes}
            self.metrics['first_qa_delivery_seconds'] = self.metrics['first_qa_delivery_seconds'] or self.clock() - self.started
            self._milestone('suite')
            self._activate('dev', 'implement', 'Run focus first, repair production, then verify focus and agreed regressions.')
        else:
            diff = self._record({'status': 'completed', 'text': self.store.patch()}, kind='diff')
            self.diff_ref, self.review_versions = diff['evidence_id'], dict(self.versions)
            self.inspected = set()
            self._activate('analysis', 'review', 'Inspect the issue, case oracles, final diff and execution evidence.',
                           diff_ref=self.diff_ref)
            result['diff_ref'] = self.diff_ref
        delivery = {'id': self._new_id('delivery'), 'role': role, 'job': job['id'],
                    'notes': notes, 'refs': refs, 'unresolved': a.get('unresolved', False)}
        self.deliveries.append(delivery)
        return result | {'delivery_id': delivery['id']}

    def _current_tests(self):
        return [e for e in self.evidence.values() if e.get('kind') == 'test'
                and not e.get('baseline') and e.get('versions') == self.versions
                and e.get('case_signature') == identity(self.cases)]

    @staticmethod
    def _failures(e):
        return {identity({k: err.get(k) for k in ('node', 'id', 'type', 'message')})
                for err in e.get('diagnostics', {}).get('errors', [])}

    def _regression_ok(self, evidence):
        for target in self.regressions:
            runs = [e for e in evidence if target in e.get('targets', [])]
            if not runs:
                return False
            last = runs[-1]
            if self._green(last):
                continue
            failures = self._failures(last)
            baselines = [e for e in self.evidence.values() if e.get('kind') == 'test' and e.get('baseline')
                and e.get('targets') == last.get('targets') and e['versions']['production'] == self.original_production
                and all(e['versions'][k] == self.versions[k] for k in ('tests', 'environment'))]
            if (not failures or last.get('timed_out') or last.get('status') != 'completed'
                    or not baselines or failures != self._failures(baselines[-1])):
                return False
        return True

    def _can_complete(self, a):
        self._refresh()
        if (self.state != 'review' or self.pending or self.open_questions
                or self.review_versions != self.versions or self.diff_ref not in self.inspected):
            return False
        current = self._current_tests()
        focus = [e for e in current if set(self.targets) <= set(e.get('targets', []))]
        red = [e for e in self.evidence.values() if self._red(e)]
        existing = bool(a.get('existing_coverage_reason')) and any(
            e.get('versions', {}).get('production') == self.original_production
            and all(e.get('versions', {}).get(k) == self.versions[k] for k in ('tests', 'environment'))
            and self._green_cases(e) for e in self.evidence.values())
        required = red[-1:] + focus[-1:] + [e for e in current if set(e['targets']) & set(self.regressions)]
        return bool((red or existing) and focus and self._green_cases(focus[-1])
                    and self._regression_ok(current)
                    and all(e['evidence_id'] in self.inspected for e in required))

    def dispatch(self, role, action):
        self.advance()
        if self.status != 'running' or role != self.role:
            return {'status': 'rejected', 'code': 'invalid_action', 'error': 'Role is not active or deadline expired'}
        before = self.clock()
        # Only owned controller values are staged; ports and workspace are not copied.
        excluded = {'store', 'execute', 'clock', 'persist'}
        saved = {k: copy.deepcopy(v) for k, v in self.__dict__.items() if k not in excluded}
        raw = copy.deepcopy(action)
        job_id = self.active_job['id']
        self._in_transaction = True
        try:
            if not isinstance(action, dict):
                raise TypeError('Return one action object')
            action = copy.deepcopy(action)
            if action.get('action') in {'find_paths', 'search_content'}:
                action.pop('cursor', None)
            entries = {e['properties']['action']['const']: e for e in self.schemas[role]['oneOf']}
            entry = entries.get(action.get('action'))
            if entry is None:
                raise ValueError('Tool unavailable to this role')
            validate(action, entry)
            if action.get('fresh') and not action.get('reason'):
                raise ValueError('Fresh execution needs a reason')
            key = identity([action, self.store.inventory()])
            cacheable = action['action'] in {'read_file', 'find_paths', 'search_content', 'read_environment', 'repo_overview'}
            if cacheable and key in self.cache:
                result = copy.deepcopy(self.cache[key]) | {'cached': True}
                self.metrics['duplicate_actions'] += 1
                if any(h['key'] == key for h in self.histories[role]):
                    self._recovery()
            else:
                result = self._perform(action)
                if cacheable and result.get('status') == 'completed':
                    self.cache[key] = copy.deepcopy(result)
            self.metrics['tool_calls'] += 1
            if result.get('status') == 'scope_not_found':
                self.metrics['scope_not_found'] += 1
            self.metrics['roles'][role]['tool_calls'] += 1
            self.metrics['roles'][role]['tool_seconds'] += self.clock() - before
            if self.active_job['id'] == job_id:
                if result.get('evidence_id'):
                    refs = self.active_job.setdefault('source_refs', [])
                    if result['evidence_id'] not in refs:
                        refs.append(result['evidence_id'])
                history = self.histories[role]
                history[:] = [h for h in history if h['key'] != key]
                history.append({'key': key, 'action': action, 'result': self._brief(result)})
                del history[:-max(1, self.policy['history_dialogs'])]
            self._refresh()
            self._persist_transaction({'kind': 'action', 'role': role, 'action': raw,
                'result': result, 'state': self._snapshot(), 'evidence': {
                    r: e for r, e in self.evidence.items() if r not in saved['evidence']}})
        except (AdapterError, ValueError, KeyError, TypeError, OSError, SyntaxError) as error:
            persistence = isinstance(error, PersistenceError)
            for k, v in saved.items():
                setattr(self, k, v)
            result = {'status': 'rejected', 'code': 'persistence_error' if persistence else 'invalid_action',
                      'error': str(error)}
            self.last_error = str(error)
        finally:
            self._in_transaction = False
        self.advance()
        self._archive()
        return result

    @staticmethod
    def _brief(result):
        # Explicit model-facing fields. Full runner telemetry stays in the archive.
        keys = ('status', 'code', 'error', 'hint', 'evidence_id', 'handle', 'path',
                'line_start', 'line_end', 'current', 'new_file', 'observation',
                'delivery_id', 'diff_ref', 'scope', 'candidates', 'truncated',
                'cached', 'current_text', 'text', 'answer', 'unresolved')
        brief = {k: copy.deepcopy(result[k]) for k in keys if k in result}
        if result.get('kind') == 'file' and result.get('current', True):
            brief.pop('text', None)  # Exact source already appears in the materials.
        if result.get('kind') in {'baseline', 'test'}:
            brief.pop('text', None)
            brief['diagnosis'] = V9TeamController._diagnosis(result)
            brief['cases'] = '\n'.join(
                f"{node}: executed={case.get('executed')}, outcome={case.get('outcome')}, "
                f"EBT executed={case.get('ebt_executed', 0)}, evaluated={case.get('ebt_evaluated', 0)}, "
                f"evaluation checked={case.get('ebt_evaluation_checked', 0)}"
                for node, case in result.get('case_results', {}).items())
        if 'test_ids' in result:
            brief['collected_tests'] = '\n'.join(result['test_ids'])
        if result.get('kind') == 'environment':
            brief['environment'] = str(result.get('python', '')) + '\n' + '\n'.join(
                f'{name}: {version}' for name, version in result.get('packages', {}).items())
        return brief

    def _source_materials(self):
        groups = {}
        inventory = self.store.inventory()
        for e in self.evidence.values():
            if e.get('kind') != 'file' or inventory.get(e['path']) != e.get('sha256'):
                continue
            key = e['path']
            group = groups.setdefault(key, {'refs': [], 'lines': {}})
            group['refs'].append(e['evidence_id'])
            for i, line in enumerate(e['text'].splitlines(keepends=True), e['line_start']):
                group['lines'][i] = line
        materials = []
        for path, group in groups.items():
            regions = []
            for line in sorted(group['lines']):
                if not regions or line != regions[-1][-1] + 1:
                    regions.append([])
                regions[-1].append(line)
            for region in regions:
                label = f"{', '.join(group['refs'])} · {path}:{region[0]}–{region[-1]}"
                text = ''.join(group['lines'][i] for i in region)
                # Pick a fence that cannot be closed by repository data.
                fence = '`' * max(3, max((len(s) for s in re.findall(r'`+', text)), default=0) + 1)
                materials.append((label, f'{label}\n{fence}\n{text}{fence}\n'))
        return materials

    @staticmethod
    def _diagnosis(e):
        return '\n'.join(str(err.get('message') or err.get('traceback_tail') or err.get('type', ''))
                         for err in e.get('diagnostics', {}).get('errors', []))

    def request(self):
        self.advance()
        if self.status != 'running':
            return None
        system = self.prompts[self.role]
        if self.role == 'qa':
            system += '\nFramework guide:\n' + self.guide
        schema = copy.deepcopy(self.schemas[self.role])
        remaining = max(0, self.started + self.policy['wall_seconds'] - self.clock())
        notes = '\n'.join(f"{d['role']} · {d['id']} (model finding, unresolved={d['unresolved']}; "
                          f"sources: {', '.join(d['refs']) or 'unreferenced hypothesis'}): {d['notes']}"
                          for d in self.deliveries)
        questions = '\n'.join('Blocking: ' + q['question'] for q in self.open_questions) or 'None.'
        searches = []
        for e in self.evidence.values():
            if e.get('kind') == 'search' and e.get('versions') == self.versions:
                searches.append(f"{e['evidence_id']} · {e.get('scope', e.get('pattern', 'overview'))} · "
                    f"{e.get('query', '')}: " + '; '.join(
                        f"{h['path']}:{h['line']} {h['text']}" for h in e.get('hits', []))
                    + '; '.join(e.get('paths', [])) + (' · limited; narrow scope' if e.get('truncated') else '')
                    + (' · no matches' if not e.get('hits') and not e.get('paths') else ''))
        results = []
        if self.baseline_ref:
            baseline = self.evidence[self.baseline_ref]
            results.append(f"Baseline ({self.baseline_ref}): {baseline.get('observation', 'unknown')} · "
                           + self._diagnosis(baseline).split('\n')[0])
        latest = {}
        test_index = []
        for e in self.evidence.values():
            if e.get('kind') != 'test':
                continue
            if e.get('versions') == self.versions and not e.get('baseline'):
                latest[tuple(e['targets'])] = e
            else:
                test_index.append(f"{e['evidence_id']} · historical execution · {', '.join(e['targets'])}: "
                                  f"{e.get('observation')} · read_evidence for original details")
        for e in latest.values():
            results.append(f"{e['evidence_id']} · {', '.join(e['targets'])}: {e.get('observation')}\n"
                           + self._diagnosis(e))
        if not results:
            results = ['Focus and regressions: not yet executed.']
        materials = self._source_materials()
        selected = []
        history = [{'action': copy.deepcopy(h['action']), 'result': copy.deepcopy(h['result'])}
                   for h in self.histories[self.role][-self.policy['history_dialogs']:]] if self.policy['history_dialogs'] else []
        index = '\n'.join(label for label, _ in materials)
        task = self.active_job['task']
        if self.active_job.get('decision_required'):
            task += '\n' + self.active_job['decision']
        if self.last_error:
            task += '\nAction error: ' + self.last_error
        task += '\nTest targets: ' + ', '.join(self.targets) + '\nRegressions: ' + ', '.join(self.regressions)
        task += '\nPublic layout: ' + ', '.join(sorted({p.split('/')[0] for p in self.store.inventory()}))
        task += '\nPython: ' + str(self.environment.get('python', 'inspect environment'))
        diff = self.evidence.get(self.diff_ref, {}) if self.state == 'review' else {}

        def build():
            text = (f'# Issue\n{self.issue}\n\n# Current Role & Task\nRole: {self.role}\n'
                f'Task: {task}\nRemaining shared task seconds: {remaining}\n\n'
                f'# Discovered Code & Evidence\n## Requirements and findings\n{notes}\n'
                f'## Current sources\n' + '\n'.join(selected) + '\n'
                f'## Hypotheses and open questions\n{questions}\n'
                f'## Search findings\n' + '\n'.join(searches) + '\n'
                f'## Further available materials\n{index}\n'
                + (f"## Current diff\n{self.diff_ref} · Read the complete patch with read_evidence.\n" if diff else '')
                + '\n# Latest Test Results\n' + '\n'.join(results)
                + '\n## Historical execution evidence\n' + '\n'.join(test_index))
            messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': text}]
            for dialog in history:
                messages.append({'role': 'assistant', 'content': json.dumps(dialog['action'], ensure_ascii=False)})
                messages.append({'role': 'user', 'content': '\n'.join(
                    f'{key}: {value}' for key, value in dialog['result'].items())})
            return {'role': self.role, 'messages': messages, 'schema': schema, 'history': history,
                'job': copy.deepcopy(self.active_job), 'baseline_ref': self.baseline_ref,
                'timeout_seconds': max(0.001, remaining), 'omitted_materials': len(materials) - len(selected)}

        def size(request):
            return len(json.dumps({k: request[k] for k in ('messages', 'schema')}, ensure_ascii=False).encode())

        request = build()
        while history and size(request) > self.policy['context_bytes']:
            history.pop(0)
            request = build()
        if size(request) > self.policy['context_bytes']:
            return {'status': 'rejected', 'code': 'context_budget_exceeded',
                    'component': 'issue, active task, findings, results and schema',
                    'error': 'Mandatory context exceeds the input byte budget'}
        for _, block in reversed(materials):
            selected.append(block)
            candidate = build()
            if size(candidate) > self.policy['context_bytes']:
                selected.pop()
            else:
                request = candidate
        self.metrics['model_calls'] += 1
        self.metrics['roles'][self.role]['model_calls'] += 1
        self.metrics['context_requests'].append({'role': self.role, 'bytes': size(request),
                                               'omitted_materials': request['omitted_materials']})
        write(self.directory / 'steps' / f'{self.metrics["model_calls"] - 1:04d}-request.json', request)
        self._archive()
        return request
