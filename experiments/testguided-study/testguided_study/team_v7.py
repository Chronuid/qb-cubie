"""V7 orchestration with one shared wall-clock deadline."""

import ast
import copy
import difflib
import fnmatch
import json

from .artifacts import write
from .iteration import identity
from .team import MUTATIONS, REPAIR, TeamController
from .team_v7_design import POLICY, SCHEMAS
from .team_workspace import TEST_KINDS, canonical_path, classify

NAVIGATION = {'read_file', 'find_paths', 'search_content', 'repo_overview',
              'read_environment', 'read_evidence', 'read_test_details'}


class V7TeamController(TeamController):
    def __init__(self, **kwargs):
        self.jobs, self.cursors, self.cache = {}, {}, {}
        self.transitions, self.recovery_episodes = [], []
        self.progress = {'read_lines': 0, 'paths': 0, 'locations': 0, 'work': 0}
        self.read_lines, self.known_paths, self.locations, self.negative_searches = set(), set(), set(), set()
        self.question_keys, self.recovery_keys = {}, set()
        self.information_started, self.information_used = None, 0
        self.information_seconds_used = 0
        self.information_job = None
        self.transition_trigger = 'model'
        self._preparing_request = False
        self.issued = None
        self.production_work = False
        kwargs['policy'] = POLICY | (kwargs.get('policy') or {})
        super().__init__(**kwargs)
        self.metrics['controller_tool_calls'] = 0
        self.metrics['duplicate_actions'] = 0
        self.metrics['cursor_errors'] = 0
        self.metrics['scope_not_found'] = 0
        self.metrics['provisional_contexts'] = 0
        self.metrics['requirement_confirmations'] = 0
        self.metrics['milestones'] = {}
        self._job('orientation')
        card = self._controller_tool('start_card', {}, self._start_card)
        if card:
            self.context['start_card'] = card
            self.context['issue_ref'] = 'issue:REQ-1'
        self._archive()

    def _snapshot(self):
        return super()._snapshot() | copy.deepcopy({
            'progress': self.progress, 'recovery_episodes': self.recovery_episodes,
            'transitions': self.transitions, 'jobs': self.jobs,
        })

    def _budget(self, kind=None):
        if self.status != 'running':
            return False
        exhausted = self.clock() >= self.started + self.policy['wall_seconds']
        if exhausted:
            self._stop('budget_exhausted')
        return not exhausted

    def _job(self, kind):
        self.jobs.setdefault(self.active_job['id'], {
            'kind': kind, 'started': self.clock(),
            'deadline': self.started + self.policy['wall_seconds'],
            'limit': None, 'calls': 0, 'recovery': False,
        })

    def _milestone(self, name):
        self.metrics['milestones'].setdefault(name, {
            'seconds': self.clock() - self.started, 'model_calls': self.metrics['model_calls'],
            'tool_calls': self.metrics['tool_calls'],
        })

    def _transition(self, origin, trigger=None, *, force=False):
        if not force and origin == (self.role, self.state, self.active_job['id']):
            return
        self.transitions.append({
            'actor': 'controller', 'trigger': trigger or self.transition_trigger,
            'from': {'role': origin[0], 'state': origin[1], 'job_id': origin[2]},
            'to': {'role': self.role, 'state': self.state, 'job_id': self.active_job['id']},
            'context_revision': self.context_revision, 'open_questions': copy.deepcopy(self.open_questions),
            'remaining': {'seconds': max(0, self.started + self.policy['wall_seconds'] - self.clock()),
                          'model_calls': None, 'tool_calls': None},
        })
        if self.role in {'qa', 'dev'}:
            self._milestone(self.role)
        self.recovery_active = self._active_recovery() is not None

    def _active_recovery(self):
        return next((e for e in reversed(self.recovery_episodes)
                     if e['job_id'] == self.active_job['id'] and e['status'] == 'active'), None)

    def _controller_tool(self, name, parameters, operation):
        if not self._budget('tool_calls'):
            return None
        self.metrics['tool_calls'] += 1
        self.metrics['controller_tool_calls'] += 1
        started = self.clock()
        try:
            result = operation()
        except (OSError, ValueError, UnicodeError) as error:
            result = {'status': 'scope_unreadable', 'reason': str(error)[:300]}
        write(self.directory / f'actions/{self.metrics["tool_calls"]:04d}.json', {
            'actor': 'controller', 'action': {'action': name, **parameters}, 'result': result,
            'seconds': self.clock() - started, 'versions': dict(self.versions),
        })
        self._budget()
        return result

    def _start_card(self):
        names = sorted(p for p in self.store.inventory() if classify(p, self.manifest) != 'artifacts')
        card = {'roots': sorted({p.split('/')[0] for p in names})[:40],
                'layouts': [p for p in ('src', 'tests', 'test') if any(n.startswith(p + '/') for n in names)],
                'file_count': len(names), 'metadata': {}, 'omitted': 0}
        remaining = max(0, self.policy['start_card_chars'] - len(str(card)))
        for name in names:
            if classify(name, self.manifest) not in TEST_KINDS | {'environment'}:
                continue
            if name.split('/')[-1] not in {'pyproject.toml', 'setup.cfg', 'pytest.ini', 'tox.ini',
                                         'environment.json', 'setup.py', 'requirements.txt', 'Pipfile'}:
                continue
            if len(name) + 100 > remaining:
                card['omitted'] += 1
                continue
            try:
                text = self.store.read(name).decode()
            except (OSError, ValueError, UnicodeError):
                text = '[unreadable]'
            text = text[:min(1200, remaining - len(name) - 40)]
            card['metadata'][name] = text
            remaining -= len(name) + len(text) + 40
        while len(json.dumps(card, ensure_ascii=False)) > self.policy['start_card_chars']:
            if card['metadata']:
                card['metadata'].popitem()
                card['omitted'] += 1
            elif card['roots']:
                card['roots'].pop()
            else:
                return {}
        return card

    def _schema(self, role):
        builtin = {e['properties']['action']['const'] for e in SCHEMAS.get(role, {}).get('oneOf', [])}
        allowed = builtin & set(self.design['core']['tools'])
        if role == 'analysis':
            if self.state == 'orient':
                allowed &= NAVIGATION | {'finish_orientation', 'finish_incomplete', 'classify_path'}
            elif self.state == 'answer_information':
                allowed -= {'finish_orientation', 'submit', 'verify_completion', 'handoff'}
            else:
                allowed -= {'finish_orientation', 'answer_question'}
        if role == 'dev' and self.state == 'reproduce' and not self._disposition_current():
            allowed -= MUTATIONS | {'publish_implementation'}
        if self.reserve:
            allowed -= REPAIR | {'finish_orientation', 'confirm_requirements', 'publish_suite', 'ask_analysis'}
        if self._active_recovery():
            allowed -= {'search_content'}
        entries = self.schemas.get(role, {}).get('oneOf', [])
        if not self._preparing_request and self.issued and self.issued['origin'] == (role, self.state, self.active_job['id']):
            entries = self.issued['schema']['oneOf']
        return {'oneOf': [copy.deepcopy(e) for e in entries if e['properties']['action']['const'] in allowed]}

    def _repair_schema(self, schema):
        preferred = {'orient': {'read_file', 'finish_orientation'},
                     'answer_information': {'read_file', 'answer_question'},
                     'review': {'read_file', 'verify_completion'},
                     'reproduce': {'run_tests', 'ask_analysis'},
                     'specify': {'confirm_requirements', 'collect_tests', 'ask_analysis'}}
        names = preferred.get(self.state, {'run_tests', 'read_file'})
        entries = [e for e in schema['oneOf'] if e['properties']['action']['const'] in names]
        return {'oneOf': entries or schema['oneOf']}

    def _output_error(self):
        return f'Return one short complete action from the repair schema for the current {self.state} job.'

    def _job_deadline(self):
        return self.started + self.policy['wall_seconds']

    def _timeout(self):
        return max(0, self._job_deadline() - self.clock())

    def request(self):
        self.advance()
        if self.status != 'running':
            return None
        timeout = self._timeout()
        self._preparing_request = True
        try:
            request = super().request()
        finally:
            self._preparing_request = False
        if request:
            self.jobs[self.active_job['id']]['calls'] += 1
            if self.state == 'answer_information':
                self.information_used += 1
            request['timeout_seconds'] = timeout
            self.issued = {'origin': (self.role, self.state, self.active_job['id']),
                           'schema': copy.deepcopy(request['schema'])}
            write(self.directory / f'steps/{self.metrics["model_calls"] - 1:04d}-request.json', request)
        return request

    def dispatch(self, role, action):
        self.advance(after_response=True)
        if self.status != 'running':
            return {'status': 'rejected', 'reason': self.reason}
        attempts = self.metrics['tool_calls']
        try:
            result = super().dispatch(role, action)
            # An unavailable action still consumes the accepted tool attempt.
            if self.metrics['tool_calls'] == attempts and self._budget('tool_calls'):
                self.metrics['tool_calls'] += 1
                tool_call = self.metrics['tool_calls']
                if role in self.metrics['roles']:
                    self.metrics['roles'][role]['tool_calls'] += 1
                self._track_progress(action.get('action'), action, result, dict(self.versions))
                write(self.directory / f'actions/{tool_call:04d}.json', {
                    'actor': 'model', 'role': role, 'action': action, 'result': result, 'versions': self.versions})
                self._budget()
                self._archive()
            return result
        finally:
            self.issued = None

    def reject_output(self, *, raw, usage, seconds=0, status='invalid_output'):
        origin = (self.role, self.state, self.active_job['id'])
        self.record_response({'raw': raw, 'usage': usage, 'status': status}, seconds)
        self.issued = None
        self.metrics['roles'][self.role]['invalid_outputs'] += status == 'invalid_output'
        if raw is None or (isinstance(raw, dict) and raw.get('message', {}).get('content') == ''):
            self.metrics['roles'][self.role]['empty_outputs'] += status == 'invalid_output'
        self.advance()
        if self.status != 'running' or origin != (self.role, self.state, self.active_job['id']):
            return
        if self._budget() and self._timeout() > 0:
            self.metrics['output_repairs'] += 1
            self.output_repair = True
        self._archive()

    def advance(self, *, after_response=False):
        """Only the shared task deadline can exhaust the runtime budget."""
        self._refresh()
        self._budget()
        self._archive()
        return self._snapshot()

    def _current_ref(self, ref):
        e = self.evidence.get(ref)
        if not e or not e.get('path') or not e.get('sha256'):
            return False
        return self.store.inventory().get(e['path']) == e['sha256']

    def _refs(self, refs):
        for ref in refs:
            if ref == 'issue:REQ-1':
                continue
            if ref not in self.evidence:
                raise ValueError('Unknown public evidence reference')

    def _path(self, name, write_role=None):
        # Navigation grants no additional mutation rights.
        if write_role or self.role == 'analysis':
            return super()._path(name, write_role)
        kind = classify(name, self.manifest)
        self.store.check(name)
        if kind == 'artifacts':
            raise ValueError('Use context/evidence tools for controller artifacts')
        return kind

    def _requirements(self, requirements):
        result = {}
        for r in requirements:
            if not r.get('id') or not r.get('text', '').strip() or not r.get('refs') or r['id'] in result:
                raise ValueError('Requirements need unique IDs, text and public references')
            self._refs(r['refs'])
            if any(self.evidence.get(ref, {}).get('path') and not self._current_ref(ref) for ref in r['refs']):
                raise ValueError('Stale requirement evidence; reread the source')
            result[r['id']] = copy.deepcopy(r)
        return result

    def _finish_orientation(self, a, *, provisional=False, trigger='model'):
        # Validate the complete package before mutating any context, job or message.
        if self.state != 'orient':
            raise ValueError('Orientation has already ended')
        requirements = self._requirements(a['requirements'])
        for ref in a['source_refs'] + a['test_entry_refs']:
            if not self._current_ref(ref):
                raise ValueError('Orientation requires current readable file references')
        if not provisional and not requirements:
            raise ValueError('Supply requirements, or report a concrete orientation blocker')
        origin = (self.role, self.state, self.active_job['id'])
        self.requirements = requirements
        self.metrics['provisional_contexts'] += provisional
        self.context_revision += 1
        self.context = {k: v for k, v in self.context.items() if k in {'start_card', 'issue_ref', 'visible_baseline'}} | {
            'requirements': list(requirements.values()), 'sources': list(a['source_refs']),
            'test_entry_refs': list(a['test_entry_refs']), 'hypotheses': list(a['hypotheses']),
            'unknowns': list(a['unknowns']), 'provisional': provisional,
        }
        self.active_job = {'id': self._new_id('qa'), 'context_revision': self.context_revision,
                           'inputs': list(requirements), 'delivery': 'One justified executable case and current collection',
                           'acceptance': 'Confirmed public requirements and complete case oracles'}
        mid = self._message('qa', 'context_ready', copy.deepcopy(self.context), a['source_refs'] + a['test_entry_refs'])
        self.role, self.state = 'qa', 'specify'
        self._job('qa')
        self._invalidate()
        self.idle = 0
        self._transition(origin, trigger)
        write(self.directory / f'contexts/{self.context_revision:04d}.json', self.context)
        return {'status': 'completed', 'context_revision': self.context_revision, 'message_id': mid}

    def _dispatch(self, op, a):
        if op == 'finish_orientation':
            return self._finish_orientation(a)
        if op == 'confirm_requirements':
            confirmed = self._requirements(a['requirements'])
            if any(self.requirements.get(rid, {}).get('status') == 'confirmed'
                   and self.requirements[rid]['text'] != r['text'] for rid, r in confirmed.items()):
                raise ValueError('Conflicting confirmed requirement: ask_analysis with public evidence before changing its meaning')
            changed = {rid for rid, r in confirmed.items() if self.requirements.get(rid) != r | {'status': 'confirmed'}}
            if not changed:
                return {'status': 'completed', 'duplicate_action': True, 'context_revision': self.context_revision}
            for r in confirmed.values():
                r['status'] = 'confirmed'
            self.requirements.update(confirmed)
            self.metrics['requirement_confirmations'] += 1
            self.context['requirements'] = list(copy.deepcopy(self.requirements).values())
            self.context_revision += 1
            self.context['provisional'] = any(r.get('status') != 'confirmed' for r in self.requirements.values())
            self.cases = {cid: c for cid, c in self.cases.items() if c['requirement_id'] not in changed}
            self.suite_cases = [cid for cid in self.suite_cases if cid in self.cases]
            self._invalidate()
            write(self.directory / f'contexts/{self.context_revision:04d}.json', self.context)
            return {'status': 'completed', 'context_revision': self.context_revision,
                    'judgment': 'model', 'confirmed': list(confirmed)}
        if op in {'create_case', 'revise_case'}:
            r = self.requirements.get(a['case']['requirement_id'], {})
            if r.get('status') != 'confirmed':
                raise ValueError('Confirm the public requirement before specifying its oracle')
        if op == 'publish_suite' and (not a['case_ids'] or any(
                self.requirements.get(self.cases.get(c, {}).get('requirement_id'), {}).get('status')
                != 'confirmed' for c in a['case_ids'])):
            raise ValueError('A suite requires confirmed public requirements and registered oracles')
        if op == 'publish_suite':
            self._validate_suite(a)
        if op == 'read_file':
            a = {k: v for k, v in a.items() if k not in {'line_start', 'line_end'}} | {
                'start': a['line_start'], 'end': a['line_end']}
        if op in NAVIGATION - {'read_evidence', 'read_test_details'} | {'collect_tests', 'run_tests', 'check_baseline'}:
            key = identity([self.role, {k: v for k, v in a.items() if k != 'note'},
                            self.store.inventory(), self.versions, self.suite_cases])
            if key in self.cache:
                self.metrics['duplicate_actions'] += 1
                return copy.deepcopy(self.cache[key]) | {
                    'duplicate_action': True, 'next_action': 'Read a different region, inspect a candidate, or finish the active job.'}
            origin = (self.role, self.state, self.active_job['id'])
            result = super()._dispatch(op, a)
            if result.get('status') == 'completed':
                self.cache[key] = copy.deepcopy(result)
                if op in {'run_tests', 'check_baseline'}:
                    self._milestone('test_run')
                    if self.qualifications['reproduced']:
                        self._milestone('red')
                self._transition(origin)
            return result
        if op == 'ask_analysis':
            key = identity([self.role, self.active_job['id'], a['question'].strip(), sorted(a['refs']), self.versions])
            if key in self.question_keys:
                return {'status': 'completed', 'duplicate_action': True, 'message_id': self.question_keys[key]}
        origin = (self.role, self.state, self.active_job['id'])
        result = super()._dispatch(op, a)
        if result.get('status') != 'completed':
            return result
        if op == 'ask_analysis':
            self.question_keys[key] = result['message_id']
            self.information_started = self.clock()
            self.information_job = self._new_id('information')
            self.active_job = {'id': self.information_job}
            self._job('information')
        elif op == 'answer_question':
            self.information_seconds_used += self.clock() - self.information_started
            self.information_started = None
        elif op == 'publish_suite':
            for episode in self.recovery_episodes:
                if episode['job_id'] == origin[2] and episode['status'] == 'active' and episode['cause'] == 'suite_incomplete':
                    episode.update(status='resolved', resolved_by=op, resolved_at=self.clock() - self.started)
            # A test revision resumes the stored Dev job, never a fresh budget.
            if self.active_job['id'] not in self.jobs or self.jobs[self.active_job['id']]['kind'] != 'dev':
                self.active_job = {'id': self._new_id('dev'), 'targets': list(self.targets)}
                self._job('dev')
            self._milestone('suite')
        elif op == 'request_test_change':
            self.active_job = {'id': self._new_id('qa-revision')}
            self._job('qa')
        elif op == 'handoff':
            self._job(self.role)
        elif op == 'create_case':
            self._milestone('case')
        elif op == 'verify_completion' and self.completion['allowed']:
            self._milestone('verification')
        if op in MUTATIONS and self.versions['production'] != self.original_production:
            self._milestone('production_change')
        self._transition(origin)
        return result

    def _mutate(self, op, a):
        self.production_work = False
        path = self.handles.get(a.get('handle'), {}).get('path') if op == 'replace_region' else a['path']
        def semantics():
            if path not in self.store.inventory():
                return None
            content = self.store.read(path)
            if path.endswith('.py'):
                try:
                    return ast.dump(ast.parse(content), include_attributes=False)
                except SyntaxError:
                    pass
            return content
        before = semantics() if self.role == 'dev' and path else None
        result = super()._mutate(op, a)
        if result.get('status') == 'completed' and self.role == 'dev':
            self.production_work = before != semantics()
        return result

    def _validate_suite(self, a):
        """Validate the full delivery before the inherited atomic handoff."""
        self._targets(a['targets'])
        if any(self.cases[c]['pytest_node'] not in a['targets'] or not a['expected_red'].get(c) for c in a['case_ids']):
            raise ValueError('Every case needs a concrete target and an expected behavioral comparison')
        collected = [e for e in self.evidence.values() if e.get('collection_only') and e.get('status') == 'completed'
                     and e.get('observation') == 'collected'
                     and all(e['versions'][k] == self.versions[k] for k in ('tests', 'environment'))]
        nodes = {node for e in collected for node in e.get('test_ids', e.get('framework_usage', {}).get('test_ids', []))}
        if any(not any(n == self.cases[c]['pytest_node'] or n.startswith(self.cases[c]['pytest_node'] + '[')
                       for n in nodes) for c in a['case_ids']):
            raise ValueError('Every case needs successful collection at the current tests and environment versions')

    def _navigate(self, op, a):
        if op not in {'find_paths', 'search_content'}:
            return super()._navigate(op, a)
        inventory = self.store.inventory()
        params = {k: a[k] for k in ('pattern', 'scope', 'query') if k in a}
        binding = identity([op, params, inventory])
        start = 0
        if 'cursor' in a:
            cursor = self.cursors.get(a['cursor'])
            if not cursor or cursor['binding'] != binding:
                self.metrics['cursor_errors'] += 1
                return {'status': 'cursor_error', 'reason': 'Invalid or stale cursor; restart without cursor.'}
            start = cursor['offset']
        names = sorted(p for p in inventory if classify(p, self.manifest) != 'artifacts')
        skipped, searched = [], 0
        if op == 'find_paths':
            hits = [p for p in names if fnmatch.fnmatchcase(p, a['pattern'])]
        else:
            scope = a['scope']
            try:
                if scope != '.':
                    canonical_path(scope)
                    self.store.check(scope)
                    if any((scope == prefix or scope.startswith(prefix + '/')) and kind == 'artifacts'
                           for prefix, kind in self.manifest.items()):
                        raise ValueError('Use context/evidence tools for controller artifacts')
            except (ValueError, OSError):
                return {'status': 'scope_denied', 'reason': 'Scope is outside the public workspace.'}
            selected = [p for p in names if scope == '.' or p == scope or p.startswith(scope + '/')]
            if not selected:
                self.metrics['scope_not_found'] += 1
                candidates = sorted(names, key=lambda p: (
                    p.split('/')[-1] != scope.split('/')[-1], -difflib.SequenceMatcher(None, p, scope).ratio(), p))[:5]
                return {'status': 'scope_not_found', 'scope_exists': False, 'hits': [], 'candidates': candidates}
            hits = []
            for name in selected:
                try:
                    lines = self.store.read(name).decode().splitlines()
                except (OSError, UnicodeError, ValueError):
                    skipped.append(name)
                    continue
                searched += 1
                hits.extend({'path': name, 'line': line, 'text': text[:500]}
                            for line, text in enumerate(lines, 1) if a['query'] in text)
        size = self.policy['search_page_size'] or 80
        page = hits[start:start + size]
        next_cursor = None
        if start + size < len(hits):
            next_cursor = self._new_id('cursor')
            self.cursors[next_cursor] = {'binding': binding, 'offset': start + size}
        result = {'status': 'completed', 'next_cursor': next_cursor, 'truncated': next_cursor is not None}
        if op == 'find_paths':
            result['files'] = page
        else:
            result.update(hits=page, scope_exists=True, files_searched=searched, files_skipped=skipped)
            if not searched:
                result['status'] = 'scope_unreadable'
        return self._record(result)

    def _track_progress(self, op, action, result, before_versions):
        if self.status != 'running':
            return
        information, work = False, False
        if result.get('status') == 'completed' and not result.get('duplicate_action'):
            if op == 'read_file':
                lines = {(result['path'], result['sha256'], n) for n in range(result['start'], result['end'] + 1)}
                new = lines - self.read_lines
                self.read_lines.update(lines)
                self.progress['read_lines'] += len(new)
                information = bool(new)
            elif op in {'find_paths', 'repo_overview'}:
                paths = set(result.get('files', []))
                information = bool(paths - self.known_paths)
                self.known_paths.update(paths)
                self.progress['paths'] = len(self.known_paths)
            elif op == 'search_content':
                locations = {(h['path'], h['line'], h['text']) for h in result.get('hits', [])}
                information = bool(locations - self.locations)
                self.locations.update(locations)
                self.progress['locations'] = len(self.locations)
                if not locations:
                    self.negative_searches.add(identity([action, self.versions]))
                    self.progress['negative_searches'] = len(self.negative_searches)
            if op in {'finish_orientation', 'confirm_requirements', 'create_case', 'revise_case', 'collect_tests', 'publish_suite',
                      'run_tests', 'check_baseline', 'verify_completion', 'answer_question', 'resolve_question'}:
                stable = {k: v for k, v in result.items() if k not in {'evidence_id', 'message_id', 'handle'}}
                sig = identity([op, stable, self.versions])
                qualified = (op not in {'run_tests', 'check_baseline'} or self._executed(result))
                qualified &= op != 'answer_question' or not action.get('unknown')
                work = qualified and sig not in self.seen
                self.seen.add(sig)
            if op in MUTATIONS and self.production_work and self.qualifications['reproduced']:
                work = True
        if work:
            self.progress['work'] += 1
        if information or work:
            self.idle = 0
            # A recovery ends only when its particular cause is resolved.
            if episode := self._active_recovery():
                resolved = (episode['cause'] == 'scope_not_found' and op in {'read_file', 'search_content'}
                            and result.get('status') == 'completed') or (episode['cause'] == 'navigation_stagnation' and information)
                resolved |= episode['cause'] == 'suite_incomplete' and op == 'publish_suite' and result.get('status') == 'completed'
                resolved |= episode['cause'] == 'work_stagnation' and work
                if resolved:
                    episode.update(status='resolved', resolved_by=op, resolved_at=self.clock() - self.started)
                    self.recovery_active = False
            return
        self.idle += 1
        if self.idle < self.policy['repeat_limit']:
            return
        cause = 'scope_not_found' if result.get('status') == 'scope_not_found' else (
            'navigation_stagnation' if op in NAVIGATION else 'work_stagnation')
        if self._active_recovery():
            self.idle = 0
            result['recovery'] = 'Inspect another relevant source or run a focused diagnostic; continue the active job.'
            return
        pattern = '*' + action.get('scope', action.get('path', '')).split('/')[-1] + '*'
        self._recover(cause, {'action': 'find_paths', 'pattern': pattern})

    def _recover(self, cause, diagnostic):
        key = identity([self.role, self.active_job['id'], cause, self.versions])
        if key in self.recovery_keys:
            self.idle = 0
            return
        self.recovery_keys.add(key)
        diagnosis = self._controller_tool(diagnostic['action'], diagnostic,
                                          lambda: self._navigate(diagnostic['action'], diagnostic))
        self.recovery_episodes.append({'id': self._new_id('recovery'), 'role': self.role,
                                      'job_id': self.active_job['id'], 'cause': cause,
                                      'parameters': diagnostic, 'diagnosis': diagnosis,
                                      'schema_change': 'Exclude repeated content searches; inspect paths, read, execute or conclude.',
                                      'versions': dict(self.versions), 'status': 'active'})
        self.recovery_active = True
        self.metrics['recoveries'] += 1
        self.idle = 0
