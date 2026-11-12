"""Serial three-role v6 controller. Model notes never become runner facts."""

import copy
import hashlib
import json
import time
import uuid
from pathlib import Path

from . import caseforms
from .artifacts import write
from .controller import compact_observation, session_context
from .iteration import identity
from .team_design import POLICY, PROMPTS, ROLES, SCHEMAS
from .team_workspace import (
    KINDS,
    TEST_KINDS,
    LocalWorkspace,
    canonical_path,
    classify,
    versions,
)

MUTATIONS = {'replace_region', 'create_source_file', 'create_test_file', 'delete_source_file', 'delete_test_file'}
REPAIR = MUTATIONS | {'request_test_change', 'revise_case', 'create_case', 'handoff'}


class TeamController:
    """Own permissions, versions, messages, continuation, budgets and completion.

    execute is a trusted public filesystem/test-service port, never a model
    result. store optionally supplies the same boundary inside a container.
    """
    def __new__(cls, **kwargs):
        design = kwargs.get('design')
        if cls is TeamController and design and design['core']['context']['version'] == 7:
            from .team_v7 import V7TeamController
            return object.__new__(V7TeamController)
        return object.__new__(cls)

    def __init__(self, *, workspace, artifact_dir, mode, issue, guides, manifest,
                 policy=None, execute, clock=time.monotonic, store=None, design=None):
        if mode not in {'pytest', 'cubie'}:
            raise ValueError('Unknown test condition')
        for path, kind in manifest.items():
            canonical_path(path)
            if kind not in KINDS:
                raise ValueError('Unknown manifest classification')
        self.root, self.directory = Path(workspace), Path(artifact_dir)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.mode, self.issue, self.guide = mode, issue, guides[mode]
        self.policy = POLICY | (policy or {})
        for name, value in self.policy.items():
            if type(value) is not int or value < 0:
                raise ValueError(f'Invalid team policy: {name}')
        # Legacy frozen policies may contain call allowances. Only elapsed time
        # limits an attempt; these fields remain for archive compatibility.
        self.policy.update(model_calls=0, tool_calls=0)
        self.clock, self.started, self.execute = clock, clock(), execute
        self.store = store or LocalWorkspace(workspace, manifest)
        self.manifest = self.store.manifest
        self.design = copy.deepcopy(design)
        self.prompts = design['core']['context']['roles'] if design else PROMPTS
        self.schemas = design['core']['context']['schemas'] if design else SCHEMAS
        self.role, self.state, self.status, self.reason = 'analysis', 'orient', 'running', None
        self.context_revision, self.context = 0, {}
        self.active_job = {'id': 'orient-1'}
        self.messages, self.pending, self.open_questions = [], [], []
        self.stack, self.cases, self.requirements, self.handles, self.evidence = [], {}, {}, {}, {}
        self.histories = {role: [] for role in ROLES}
        self.metrics = {'model_calls': 0, 'tool_calls': 0, 'recoveries': 0, 'output_repairs': 0,
                        'information_requests': 0, 'revision_rounds': 0, 'edit_conflicts': 0,
                        'rejected_retries': 0, 'tool_errors': 0,
                        'ebt_executed': 0, 'ebt_evaluated': 0, 'ebt_passed': 0, 'ebt_evaluation_checked': 0,
                        'first_production_change_call': None, 'first_red_call': None,
                        'first_production_change_seconds': None, 'first_red_seconds': None,
                        'roles': {role: {'model_calls': 0, 'tool_calls': 0, 'seconds': 0,
                                         'model_seconds': 0, 'tool_seconds': 0,
                                         'input_tokens': 0, 'output_tokens': 0, 'empty_outputs': 0,
                                         'invalid_outputs': 0} for role in ROLES}}
        self.versions = self._workspace_versions()
        self.original_production = self.versions['production']
        self.review = None
        self.coverage, self.targets, self.suite_cases = [], [], []
        self.open_points = []
        self.qualifications = {'reproduced': False, 'verified': False}
        self.reproduction_disposition = None
        self.completion = {'allowed': False, 'status': 'incomplete'}
        self.seen, self.idle, self.recovery_active = set(), 0, False
        self.output_repair = False
        self._archive()

    def _archive(self):
        write(self.directory / 'team.json', self._snapshot())
        write(self.directory / 'context.json', {'revision': self.context_revision, **self.context})
        write(self.directory / 'messages.json', self.messages)
        write(self.directory / 'path-manifest.json', self.manifest)
        (self.directory / 'full.patch').write_text(self.store.patch(), encoding='utf-8')

    def _snapshot(self):
        return copy.deepcopy({'role': self.role, 'roles': list(ROLES), 'state': self.state,
            'status': self.status, 'reason': self.reason, 'active_job': self.active_job,
            'context_revision': self.context_revision, 'versions': self.versions,
            'cases': self.cases, 'messages': self.messages, 'pending_requests': self.pending,
            'open_questions': self.open_questions, 'qualifications': self.qualifications,
            'reproduction_disposition': self.reproduction_disposition,
            'completion': self.completion, 'policy': self.policy,
            'budget': {'reserve_active': self.reserve, 'deadline': self.started + self.policy['wall_seconds']},
            'metrics': self.metrics, 'private_evaluation_required': True})

    def snapshot(self):
        self._refresh()
        return self._snapshot()

    @property
    def reserve(self):
        return False

    def _stop(self, reason):
        self.status, self.reason = 'incomplete', reason
        self.review = None
        self.completion = {'allowed': False, 'status': 'incomplete'}
        self._archive()

    def finish(self, reason):
        if self.status == 'running':
            self._stop(reason)

    def _budget(self, kind=None):
        if self.status != 'running':
            return False
        reason = None
        if self.clock() - self.started >= self.policy['wall_seconds']:
            reason = 'wall_budget'
        if reason:
            self._stop(reason)
        return not reason

    def _refresh(self):
        current = self._workspace_versions()
        if current != self.versions:
            self.review = None
            self.qualifications['verified'] = False
            self.completion = {'allowed': False, 'status': 'incomplete'}
            self.versions = current
            self._qualify()

    def _workspace_versions(self):
        result = versions(self.store.inventory(), self.manifest)
        behavioral_cases = {cid: {k: v for k, v in case.items() if k not in {'reason', 'reason_ref'}}
                            for cid, case in self.cases.items()}
        result['tests'] = identity([result['tests'], behavioral_cases])
        return result

    def _new_id(self, prefix):
        return prefix + '-' + uuid.uuid4().hex

    def _record(self, result, **metadata):
        eid = self._new_id('evidence')
        record = copy.deepcopy(result) | {'evidence_id': eid, 'versions': dict(self.versions), **metadata}
        self.evidence[eid] = record
        write(self.directory / 'evidence' / (eid + '.json'), record)
        return record

    def _message(self, recipient, kind, payload, refs=(), reply_to=None):
        refs = list(refs)
        self._refs(refs)
        record = {'id': self._new_id('message'), 'reply_to': reply_to, 'sender': self.role,
                  'recipient': recipient, 'type': kind, 'job_id': self.active_job['id'],
                  'context_revision': self.context_revision, 'versions': dict(self.versions),
                  'payload': copy.deepcopy(payload), 'evidence_refs': refs}
        self.messages.append(record)
        return record['id']

    def _refs(self, refs):
        for ref in refs:
            if ref in self.evidence:
                continue
            if isinstance(ref, str) and ref.startswith('issue:'):
                continue
            raise ValueError('Unknown public evidence reference')

    def _path(self, name, write_role=None):
        kind = classify(name, self.manifest)
        self.store.check(name)
        if kind == 'artifacts':
            raise ValueError('Use context/evidence tools for controller artifacts')
        if write_role and not ((write_role == 'qa' and kind in TEST_KINDS)
                               or (write_role == 'dev' and kind == 'production')):
            raise ValueError('Role cannot mutate this path classification')
        if not write_role and self.role != 'analysis':
            # Production/test context is explicitly granted by analysis; tests are
            # always readable to their owner. No unrestricted navigation in QA/Dev.
            assigned = {self.evidence[e]['path'] for e in self.context.get('sources', [])
                        if e in self.evidence and 'path' in self.evidence[e]}
            assigned.update(self.context.get('assigned_paths', []))
            if self.role == 'qa' and kind == 'production' and name not in assigned:
                raise ValueError('Ask analysis to assign this production source')
        return kind

    def request(self):
        self._refresh()
        if not self._budget('model_calls'):
            return None
        schema = self._schema(self.role)
        if self.output_repair:
            schema = self._repair_schema(schema)
        system = self.prompts[self.role] + f'\nTesting framework: {self.mode}\n' + self.guide
        if self.design:
            system = self.design['core']['prompt'] + '\n' + system
            system += '\n' + '\n'.join(self.design['specialization']['examples'])
        ledger = {'context': self.context, 'team': self._snapshot(),
                  'instructions': 'Continue the active job using current public evidence.'}
        # Other roles see addressed summaries, never entire foreign dialogues.
        ledger['team']['messages'] = [m for m in self.messages if m['recipient'] == self.role][-8:]
        if self.recovery_active:
            ledger['recovery'] = 'No new evidence. Read a different relevant source or run one focused diagnostic.'
        if self.output_repair:
            ledger['output_error'] = self._output_error()
        try:
            messages = session_context(system, self.issue, self.histories[self.role], ledger,
                                       self.policy['context_bytes'])
        except ValueError:
            self._stop('context_error')
            return None
        self.metrics['model_calls'] += 1
        self.metrics['roles'][self.role]['model_calls'] += 1
        request = {'role': self.role, 'messages': messages, 'schema': schema}
        write(self.directory / f'steps/{self.metrics["model_calls"] - 1:04d}-request.json', request)
        return request

    def _schema(self, role):
        names = {e['properties']['action']['const'] for e in SCHEMAS.get(role, {}).get('oneOf', [])}
        return {'oneOf': [copy.deepcopy(e) for e in self.schemas.get(role, {}).get('oneOf', [])
                          if e['properties']['action']['const'] in names]}

    def _repair_schema(self, schema):
        return {'oneOf': [e for e in schema['oneOf'] if e['properties']['action']['const'] == 'read_file']}

    def _output_error(self):
        return 'Return one short complete read_file JSON action matching the repair schema.'

    def record_response(self, response, seconds=0):
        write(self.directory / f'steps/{self.metrics["model_calls"] - 1:04d}-response.json', response)
        usage = response.get('usage', {})
        role_metrics = self.metrics['roles'][self.role]
        role_metrics['seconds'] += seconds
        role_metrics['model_seconds'] += seconds
        for key in ('input_tokens', 'output_tokens'):
            measured = usage.get(key)
            role_metrics[key] = None if measured is None or role_metrics[key] is None else role_metrics[key] + measured
        self.output_repair = False

    def reject_output(self, *, raw, usage, seconds=0):
        self.record_response({'raw': raw, 'usage': usage, 'status': 'invalid_output'}, seconds)
        self.metrics['roles'][self.role]['invalid_outputs'] += 1
        if raw is None or (isinstance(raw, dict) and raw.get('message', {}).get('content') == ''):
            self.metrics['roles'][self.role]['empty_outputs'] += 1
        if self._budget():
            self.metrics['output_repairs'] += 1
            self.output_repair = True
        self._archive()

    def dispatch(self, role, action):
        tool_started = self.clock()
        self._refresh()
        if not self._budget('tool_calls'):
            return {'status': 'rejected', 'reason': self.reason or self.status}
        op = action.get('action') if isinstance(action, dict) else None
        schema = self._schema(role)
        if self.output_repair:
            schema = self._repair_schema(schema)
        names = {entry['properties']['action']['const'] for entry in schema['oneOf']}
        if role != self.role or op not in names:
            return {'status': 'rejected', 'reason': 'Action is not available to the active role'}
        if self.reserve and op in REPAIR:
            return {'status': 'rejected', 'reason': 'Verification reserve: no new repair round'}
        self.metrics['tool_calls'] += 1
        tool_call = self.metrics['tool_calls']
        self.metrics['roles'][role]['tool_calls'] += 1
        before_versions = dict(self.versions)
        try:
            from ollama_agents.errors import AdapterError
            from ollama_agents.schema import validate
            try:
                validate(action, schema)
            except AdapterError as error:
                raise ValueError(str(error)) from error
            result = self._dispatch(op, action)
        except (ValueError, KeyError, TypeError, OSError, SyntaxError) as error:
            self.metrics['tool_errors'] += 1
            result = {'status': 'rejected', 'reason': str(error)[:500]}
        self._refresh()
        self._track_progress(op, action, result, before_versions)
        self.histories[role].append(({'role': 'assistant', 'content': json.dumps(action)},
                                     {'role': 'user', 'content': json.dumps(compact_observation(result))}))
        elapsed = self.clock() - tool_started
        self.metrics['roles'][role]['tool_seconds'] += elapsed
        self.metrics['roles'][role]['seconds'] += elapsed
        write(self.directory / f'actions/{tool_call:04d}.json',
              {'actor': 'model', 'role': role, 'action': action, 'result': result, 'versions': self.versions})
        self._budget()
        self._archive()
        return copy.deepcopy(result)

    def _track_progress(self, op, action, result, before_versions):
        # Only file/test/information evidence counts as progress. Notes and
        # rephrasing, runner UUIDs, routing and role switches do not reset idle.
        evidence_actions = {'read_file', 'run_tests', 'check_baseline', 'collect_tests', 'find_paths',
                            'search_content', 'read_evidence', 'read_test_details', 'read_environment', 'repo_overview'}
        if self.status == 'running':
            stable = {k: v for k, v in result.items() if k not in {'evidence_id', 'handle', 'message_id'}}
            signature = identity([op, stable, self.versions])
            new = (result.get('status') == 'completed' and
                   ((op in evidence_actions and signature not in self.seen) or self.versions != before_versions))
            if op == 'answer_question':
                signature = identity(['information', sorted(action.get('refs', [])), self.versions])
                new = result.get('status') == 'completed' and signature not in self.seen
            if new:
                self.seen.add(signature)
                self.idle = 0
            else:
                self.idle += 1
            if self.idle >= self.policy['repeat_limit']:
                self.recovery_active = True
                self.metrics['recoveries'] += 1
                self.idle = 0
                result['recovery'] = 'Read a different relevant source or run a focused diagnostic.'

    def _dispatch(self, op, a):
        if op == 'read_file':
            self._path(a['path'])
            start = a.get('start', 1)
            data = self.store.read(a['path'])
            lines = data.decode().splitlines(keepends=True)
            end = a.get('end', min(len(lines), start + 159))
            if type(start) is not int or type(end) is not int or start < 1 or end < start or end > len(lines):
                raise ValueError('Invalid one-based file region')
            result = self.execute({'action': 'read_file', 'path': a['path'], 'start': start, 'end': end})
            if result.get('status') != 'completed':
                return result
            result.update(path=a['path'], start=start, end=end, text=''.join(lines[start-1:end]),
                          sha256=hashlib.sha256(data).hexdigest())
            record = self._record(result)
            handle = self._new_id('region')
            self.handles[handle] = {'path': a['path'], 'start': start, 'end': end,
                                    'sha256': result['sha256'], 'role': self.role}
            return {**record, 'handle': handle}
        if op in MUTATIONS:
            return self._mutate(op, a)
        if op in {'repo_overview', 'find_paths', 'search_content', 'read_environment'}:
            return self._navigate(op, a)
        if op == 'read_context':
            return {'status': 'completed', 'context_revision': self.context_revision, **copy.deepcopy(self.context)}
        if op == 'classify_path':
            canonical_path(a['path'])
            self.store.check(a['path'])
            self._refs(a['refs'])
            if not a['refs'] or not a['reason'] or a['kind'] not in KINDS - {'artifacts'}:
                raise ValueError('Classification needs a public reason and evidence')
            try:
                classify(a['path'], self.manifest)
            except ValueError:
                self.manifest[a['path']] = a['kind']
            else:
                raise ValueError('Existing manifest classifications cannot be changed')
            return {'status': 'completed', 'path': a['path'], 'kind': a['kind']}
        if op in {'read_evidence', 'read_test_details'}:
            evidence = copy.deepcopy(self.evidence[a['evidence_id']])
            if op == 'read_test_details':
                errors = evidence.get('diagnostics', {}).get('errors', [])
                start = a.get('start', 0)
                if type(start) is not int or start < 0:
                    raise ValueError('Use a nonnegative error offset')
                return {'status': 'completed', 'hits': errors[start:start+1],
                        'next_start': start+1 if start+1 < len(errors) else None}
            return {'status': 'completed', **compact_observation(evidence)}
        if op == 'publish_context':
            self._refs(a['sources'])
            requirements = a['requirements']
            if not requirements or any(not r.get('id') or not r.get('text') or not r.get('refs') for r in requirements):
                raise ValueError('Requirements need IDs, text and public evidence')
            for requirement in requirements:
                self._refs(requirement['refs'])
            self.requirements = {r['id']: copy.deepcopy(r) for r in requirements}
            self.context_revision += 1
            self.context = {k: copy.deepcopy(v) for k, v in a.items() if k != 'action'} | {
                k: v for k, v in self.context.items() if k == 'visible_baseline'}
            for question in a.get('open_questions', []):
                question = copy.deepcopy(question)
                question.setdefault('id', self._new_id('question'))
                if not any(q['id'] == question['id'] for q in self.open_questions):
                    self.open_questions.append(question)
            self._invalidate()
            write(self.directory / f'contexts/{self.context_revision:04d}.json', self.context)
            return {'status': 'completed', 'context_revision': self.context_revision}
        if op == 'handoff':
            if self.state not in {'orient', 'review', 'answer_information'}:
                raise ValueError('No analysis handoff is active')
            if not self.requirements or not self.context.get('sources'):
                raise ValueError('Read relevant sources and publish context before handoff')
            if a['to'] not in {'qa', 'dev'}:
                raise ValueError('Unknown recipient')
            if self.state == 'review':
                self._round()
            continuation = (self.role, self.state, copy.deepcopy(self.active_job)) if self.state == 'answer_information' else None
            self.active_job = {'id': a['job_id'], 'inputs': a['inputs'],
                               'context_revision': self.context_revision, 'versions': dict(self.versions),
                               'delivery': a['delivery'], 'acceptance': a['acceptance']}
            mid = self._message(a['to'], 'context_ready' if self.state == 'orient' else 'review_rework',
                                a, self.context['sources'])
            if continuation:
                self.stack.append((*continuation, mid))
            self.role, self.state = a['to'], 'specify' if a['to'] == 'qa' else 'verify'
            return {'status': 'completed', 'message_id': mid}
        if op in {'create_case', 'revise_case'}:
            case = a['case']
            caseforms.validate(case)
            if case['requirement_id'] not in self.requirements:
                raise ValueError('Unknown requirement')
            self._refs([case['reason_ref']])
            path = case['pytest_node'].split('::')[0]
            self._path(path, 'qa')
            if op == 'revise_case' and case['case_id'] not in self.cases:
                raise ValueError('Unknown case')
            if op == 'create_case' and case['case_id'] in self.cases:
                raise ValueError('Case already exists')
            if path not in self.store.inventory():
                result = self._mutate('create_test_file', {'action': 'create_test_file', 'path': path,
                    'content': caseforms.render(case, self.mode), 'reason': case['reason_ref']})
                if result.get('status') != 'completed':
                    return result
            self.cases[case['case_id']] = copy.deepcopy(case)
            self._invalidate()
            return {'status': 'completed', 'case_id': case['case_id']}
        if op == 'collect_tests':
            self._targets(a['targets'])
            return self._record(self.execute(a), targets=a['targets'], collection_only=True)
        if op == 'publish_suite':
            if self.state not in {'specify', 'revise_tests'}:
                raise ValueError('No QA suite job is active')
            if not a['case_ids'] or any(c not in self.cases for c in a['case_ids']):
                raise ValueError('Publish concrete registered cases')
            self._targets(a['targets'])
            collected = [e for e in self.evidence.values() if e.get('collection_only')
                         and e['versions']['tests'] == self.versions['tests'] and e.get('status') == 'completed']
            if not collected:
                raise ValueError('Collect the current suite before publishing')
            nodes = {node for e in collected for node in
                     e.get('test_ids', e.get('framework_usage', {}).get('test_ids', []))}
            if any(not any(node == self.cases[c]['pytest_node'] or node.startswith(self.cases[c]['pytest_node'] + '[')
                           for node in nodes) for c in a['case_ids']):
                raise ValueError('Every published case must appear in the current collection')
            self.suite_cases, self.targets = list(a['case_ids']), list(a['targets'])
            if any(self.cases[c]['pytest_node'] not in self.targets for c in self.suite_cases):
                raise ValueError('Every case requires an explicit target')
            reply_to = None
            if self.state == 'revise_tests' and self.stack:
                _, _, self.active_job, reply_to = self.stack.pop()
                self.pending.remove(reply_to)
            mid = self._message('dev', 'suite_ready', a, reply_to=reply_to)
            self.role, self.state = 'dev', 'reproduce'
            return {'status': 'completed', 'message_id': mid}
        if op in {'run_tests', 'check_baseline'}:
            return self._run(op, a)
        if op == 'diagnose':
            evidence = self.evidence[a['evidence_id']]
            if a['classification'] == 'issue' and not self._behavioral_red(evidence):
                raise ValueError('This evidence is not behavioral red')
            record = self._record({'status': 'completed', **a}, diagnosis=True)
            return record
        if op == 'ask_analysis':
            self._refs(a.get('refs', []))
            mid = self._message('analysis', 'information_request', a, a.get('refs', []))
            self.stack.append((self.role, self.state, copy.deepcopy(self.active_job), mid))
            self.pending.append(mid)
            self.metrics['information_requests'] += 1
            self.role, self.state = 'analysis', 'answer_information'
            return {'status': 'completed', 'message_id': mid}
        if op == 'answer_question':
            if not self.stack or a['reply_to'] != self.stack[-1][3]:
                raise ValueError('Answer the active addressed request')
            self._refs(a['refs'])
            if not a['unknown'] and not a['refs']:
                raise ValueError('Known answers require public references')
            role, state, job, mid = self.stack.pop()
            response = self._message(role, 'information_response', a, a['refs'], reply_to=mid)
            self.pending.remove(mid)
            if a['unknown']:
                self.open_questions.append({'id': mid, 'question': a['answer'], 'dependent_job': job['id']})
            self.role, self.state, self.active_job = role, state, job
            return {'status': 'completed', 'message_id': response}
        if op == 'classify_reproduction':
            self._refs(a['evidence_ids'])
            if not a['evidence_ids'] or set(a['requirement_ids']) != set(self.requirements):
                raise ValueError('Classify all requirements against original test evidence')
            originals = [self.evidence[eid] for eid in a['evidence_ids']]
            if any(e.get('purpose') != 'focused' or e['versions']['production'] != self.original_production
                   or any(e['versions'][k] != self.versions[k] for k in ('tests', 'environment')) for e in originals):
                raise ValueError('Use the current final suite on original production')
            if a['classification'] == 'existing_coverage' and not all(self._green_cases(e) for e in originals):
                raise ValueError('Existing coverage requires actually executed original green')
            if a['classification'] == 'production_syntax' and not all(
                    e.get('observation') == 'invalid_test_run' and e.get('diagnostics', {}).get('errors') for e in originals):
                raise ValueError('Production import/syntax classification requires original error diagnostics')
            self.reproduction_disposition = {**copy.deepcopy(a), 'versions': dict(self.versions)}
            self.open_questions = [q for q in self.open_questions if q['id'] != 'missing-reproduction']
            self._invalidate()
            return {'status': 'completed', 'reproduced': self.qualifications['reproduced']}
        if op == 'request_test_change':
            if not a['case_ids'] or any(c not in self.cases for c in a['case_ids']):
                raise ValueError('Unknown test cases')
            self._refs(a['evidence_ids'])
            if not a['evidence_ids'] or a['requirement_id'] not in self.requirements:
                raise ValueError('Test changes require a requirement and actual diagnostics')
            self._round()
            mid = self._message('qa', 'test_change_request', a, a['evidence_ids'])
            self.stack.append((self.role, self.state, copy.deepcopy(self.active_job), mid))
            self.pending.append(mid)
            self.role, self.state = 'qa', 'revise_tests'
            return {'status': 'completed', 'message_id': mid}
        if op == 'respond_test_change':
            if not self.stack or self.stack[-1][3] != a['reply_to'] or self.state != 'revise_tests':
                raise ValueError('Respond to the active test change request')
            role, state, job, mid = self.stack.pop()
            response = self._message('dev', 'test_change_response', a, a['refs'], reply_to=mid)
            self.role, self.state, self.active_job = role, state, job
            if a['unresolved']:
                self.open_questions.append({'id': mid, 'question': a['reason']})
                self.role, self.state = 'analysis', 'review'
            else:
                self.pending.remove(mid)
                if a['accepted']:
                    self.state = 'reproduce'
            return {'status': 'completed', 'message_id': response}
        if op == 'resolve_question':
            self._refs(a['refs'])
            if not a['refs'] or not any(q['id'] == a['question_id'] for q in self.open_questions):
                raise ValueError('Resolve an existing question with public evidence')
            self.open_questions = [q for q in self.open_questions if q['id'] != a['question_id']]
            self.pending = [p for p in self.pending if p != a['question_id']]
            return {'status': 'completed'}
        if op == 'publish_implementation':
            if set(a['requirement_ids']) != set(self.requirements):
                raise ValueError('Report every agreed requirement')
            self.coverage, self.open_points = list(a['requirement_ids']), list(a['open_points'])
            mid = self._message('analysis', 'implementation_ready', a, list(self.evidence)[-4:])
            self.role, self.state = 'analysis', 'review'
            if self.stack and self.stack[-1][0:2] == ('analysis', 'answer_information'):
                self.role, self.state, self.active_job, _ = self.stack.pop()
            return {'status': 'completed', 'message_id': mid}
        if op == 'verify_completion':
            allowed, status = self._completion()
            self.completion = {'allowed': allowed, 'status': status}
            self.qualifications['verified'] = allowed
            self.review = dict(self.versions) if allowed else None
            return {'status': 'completed' if allowed else 'rejected', 'completion': self.completion}
        if op == 'submit':
            allowed, status = self._completion()
            if not allowed or self.review != self.versions:
                raise ValueError('Current analysis review and execution evidence are required')
            self.status, self.reason = 'submitted', None
            self.completion = {'allowed': True, 'status': status}
            return {'status': 'completed'}
        if op == 'finish_incomplete':
            raise ValueError('Time remains: investigate the blocker and continue the active job')
        raise ValueError('Unknown action')

    def _round(self):
        self.metrics['revision_rounds'] += 1

    def _invalidate(self):
        self.review = None
        self.qualifications['verified'] = False
        self.completion = {'allowed': False, 'status': 'incomplete'}
        self._refresh()
        self._qualify()

    def _mutate(self, op, a):
        if self.role == 'dev' and not self.qualifications['reproduced'] and not self._disposition_current():
            raise ValueError('Run a requirement-linked behavioral reproduction before changing production')
        concrete = {key: a[key] for key in ('action', 'path', 'content', 'reason') if key in a}
        if op == 'replace_region':
            handle = self.handles.get(a['handle'])
            if handle is None or handle['role'] != self.role:
                raise ValueError('Read the current region before editing')
            path = handle['path']
            self._path(path, self.role)
            data = self.store.read(path)
            if hashlib.sha256(data).hexdigest() != handle['sha256']:
                del self.handles[a['handle']]
                self.metrics['edit_conflicts'] += 1
                raise ValueError('Stale region; reread before one new local edit')
            lines = data.decode().splitlines(keepends=True)
            lines[handle['start']-1:handle['end']] = [a['new_text']]
            candidate = ''.join(lines)
            concrete.update(path=path, start=handle['start'], end=handle['end'])
            concrete.update(new_text=a['new_text'], expected_sha256=handle['sha256'])
        else:
            path = a['path']
            self._path(path, self.role)
            exists = path in self.store.inventory()
            if op.startswith('create') and exists:
                raise ValueError('Creation cannot overwrite an existing file; read and replace a region')
            if op.startswith('delete') and (not exists or (self.role == 'qa' and not a.get('coverage_reason'))):
                raise ValueError('Test deletion requires an explicit coverage justification')
            candidate = a.get('content')
        if not a.get('reason'):
            raise ValueError('Mutation requires a reason')
        if candidate is not None:
            if len(candidate.encode()) > 128000:
                raise ValueError('Edit exceeds size limit')
            if path.endswith('.py'):
                compile(candidate, path, 'exec')
        concrete.pop('handle', None)
        result = self.execute(concrete)
        if result.get('status') == 'completed':
            self.handles = {k: v for k, v in self.handles.items() if v['path'] != path}
            if classify(path, self.manifest) == 'production' and self.metrics['first_production_change_call'] is None:
                self.metrics['first_production_change_call'] = self.metrics['model_calls']
                self.metrics['first_production_change_seconds'] = self.clock() - self.started
            self._refresh()
            self._invalidate()
        return result

    def _navigate(self, op, a):
        import fnmatch
        names = sorted(self.store.inventory())
        if op == 'repo_overview':
            result = {'roots': sorted({p.split('/')[0] for p in names}), 'files': names[:80]}
        elif op == 'read_environment':
            result = {'files': [p for p in names if classify(p, self.manifest) == 'environment'],
                      'versions': dict(self.versions)}
        elif op == 'find_paths':
            start = a.get('start', 0)
            hits = [p for p in names if fnmatch.fnmatch(p, a['pattern'])]
            result = {'files': hits[start:start+80], 'next_start': start+80 if len(hits) > start+80 else None}
        else:
            scope = a['path']
            if scope != '.':
                canonical_path(scope)
                self.store.check(scope)
            hits = []
            for name in names:
                if scope != '.' and name != scope and not name.startswith(scope + '/'):
                    continue
                try:
                    for line, text in enumerate(self.store.read(name).decode().splitlines(), 1):
                        if a['query'] in text:
                            hits.append({'path': name, 'line': line, 'text': text[:500]})
                except UnicodeError:
                    continue
            start = a.get('start', 0)
            result = {'hits': hits[start:start+80], 'next_start': start+80 if len(hits) > start+80 else None}
        return self._record({'status': 'completed', **result})

    def _targets(self, targets):
        if not isinstance(targets, list) or not 1 <= len(targets) <= 20:
            raise ValueError('Use concrete nonempty test targets')
        for target in targets:
            path = target.split('::', 1)[0]
            if path == '.':
                raise ValueError('Use explicit focused cases and a justified regression selection')
            if classify(path, self.manifest) not in TEST_KINDS:
                raise ValueError('Target must refer to the public test suite')
            self.store.check(path)

    def _run(self, op, a):
        self._targets(a['targets'])
        if a.get('purpose', 'focused') not in {'focused', 'regression'}:
            raise ValueError('Unknown test purpose')
        root = self.store.baseline() if op == 'check_baseline' else None
        try:
            concrete = {'action': op, 'targets': list(a['targets']), 'purpose': a.get('purpose', 'focused')}
            if root:
                concrete['workspace'] = root
            result = self.execute(concrete)
        finally:
            if root:
                self.store.remove_baseline(root)
        self._refresh()
        if 'case_results' in result:
            result = copy.deepcopy(result)
            for cid in self.suite_cases:
                node = self.cases[cid]['pytest_node']
                if cid not in result['case_results'] and node in result['case_results']:
                    result['case_results'][cid] = result['case_results'][node]
                elif cid not in result['case_results']:
                    matches = [v for k, v in result['case_results'].items() if k.startswith(node + '[')]
                    if matches:
                        states = [v.get('outcome') for v in matches]
                        state = ('pass' if all(s == 'pass' for s in states) else 'assertion_failure'
                                 if all(s in {'pass', 'assertion_failure'} for s in states) else 'invalid_test_run')
                        result['case_results'][cid] = {'executed': all(v.get('executed') for v in matches),
                            'outcome': state, **{key: sum(v.get(key, 0) for v in matches)
                            for key in ('ebt_executed', 'ebt_evaluated', 'ebt_passed', 'ebt_evaluation_checked')}}
        bound_versions = dict(self.versions)
        if root:
            bound_versions['production'] = self.original_production
        record = self._record(result, versions=bound_versions, baseline=bool(root),
                              targets=list(a['targets']), purpose=a.get('purpose', 'focused'))
        for key in ('ebt_executed', 'ebt_evaluated', 'ebt_passed', 'ebt_evaluation_checked'):
            self.metrics[key] += result.get('framework_usage', {}).get(key, 0)
        self._qualify()
        if self._behavioral_red(record):
            self.state = 'implement'
            if self.metrics['first_red_call'] is None:
                self.metrics['first_red_call'] = self.metrics['model_calls']
                self.metrics['first_red_seconds'] = self.clock() - self.started
        elif record.get('observation') == 'pass' and record['versions']['production'] == self.original_production:
            if not any(q['id'] == 'missing-reproduction' for q in self.open_questions):
                self.open_questions.append({'id': 'missing-reproduction',
                    'question': 'The original production is green; analysis must classify existing coverage or missing reproduction.'})
        elif record.get('observation') == 'pass':
            self.state = 'verify'
        return record

    def _executed(self, e):
        d = e.get('diagnostics', {})
        counts = d.get('counts', {})
        executed = d.get('executed', counts.get('passed', 0) + counts.get('failed', 0))
        return (e.get('status') == 'completed' and not e.get('collection_only') and not e.get('timed_out')
                and executed > 0 and not counts.get('errors', 0) and not d.get('invalid_xml'))

    def _behavioral_red(self, e):
        if (not self._executed(e) or e.get('observation') != 'assertion_failure'
                or e.get('versions', {}).get('production') != self.original_production
                or e.get('purpose') != 'focused'):
            return False
        failures = 0
        for cid in self.suite_cases:
            case = e.get('case_results', {}).get(cid, {})
            if not case.get('executed') or case.get('outcome') not in {'pass', 'assertion_failure'}:
                return False
            failures += case.get('outcome') == 'assertion_failure'
        return failures > 0

    def _qualify(self):
        self.qualifications['reproduced'] = any(self._behavioral_red(e)
            and all(e['versions'][k] == self.versions[k] for k in ('tests', 'environment'))
            for e in self.evidence.values())

    def _green_cases(self, e):
        if not self._executed(e) or e.get('observation') != 'pass' or e.get('exit_code') != 0:
            return False
        counts = e.get('diagnostics', {}).get('counts', {})
        if counts.get('failed', 0) or counts.get('skipped', 0) or e.get('xfail') or e.get('xpass'):
            return False
        for cid in self.suite_cases:
            case = e.get('case_results', {}).get(cid, {})
            if not case.get('executed') or case.get('outcome') != 'pass':
                return False
            if self.mode == 'cubie' and not all(case.get(k, 0) > 0 for k in
                    ('ebt_executed', 'ebt_evaluated', 'ebt_passed', 'ebt_evaluation_checked')):
                return False
        return bool(self.suite_cases)

    def _completion(self):
        self._qualify()
        classified = (self._disposition_current()
                      and self.reproduction_disposition['classification'] in {'existing_coverage', 'production_syntax'}
                      and self.versions['production'] != self.original_production)
        if (self.state != 'review' or self.pending or self.open_questions or self.open_points
                or set(self.coverage) != set(self.requirements) or not self.requirements
                or not (self.qualifications['reproduced'] or classified)
                or not all(any(self.cases[c]['requirement_id'] == rid for c in self.suite_cases)
                           for rid in self.requirements)):
            return False, 'incomplete'
        current = [e for e in self.evidence.values() if e.get('versions') == self.versions and not e.get('baseline')]
        focused = [e for e in current if e.get('purpose') == 'focused']
        regression = [e for e in current if e.get('purpose') == 'regression']
        if not focused or not self._green_cases(focused[-1]) or not regression:
            return False, 'incomplete'
        final = regression[-1]
        if (not self._executed(final) or final.get('diagnostics', {}).get('counts', {}).get('skipped', 0)
                or any(c.get('outcome') in {'skip', 'xfail', 'xpass', 'missing', 'invalid_test_run'}
                       for c in final.get('case_results', {}).values())):
            return False, 'incomplete'
        if final.get('observation') == 'pass' and final.get('exit_code') == 0:
            return True, 'verified_green'
        if final.get('observation') not in {'assertion_failure', 'test_failure'}:
            return False, 'incomplete'
        baselines = [e for e in self.evidence.values() if e.get('baseline') and e.get('purpose') == 'regression'
                     and e['versions']['tests'] == self.versions['tests']
                     and e['versions']['environment'] == self.versions['environment']
                     and e.get('targets') == final.get('targets') and self._executed(e)]
        if not baselines:
            return False, 'incomplete'
        def failures(e):
            return {identity({k: error.get(k) for k in ('node', 'id', 'type', 'message')})
                    for error in e.get('diagnostics', {}).get('errors', [])}
        existing, now = failures(baselines[-1]), failures(final)
        if now and now <= existing:
            return True, 'verified_with_baseline_failures'
        return False, 'incomplete'

    def _disposition_current(self):
        return bool(self.reproduction_disposition and all(
            self.reproduction_disposition['versions'][key] == self.versions[key] for key in ('tests', 'environment')))
