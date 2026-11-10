"""Compose phased submissions, local repairs, episode budgets and complete evidence."""

import copy
import time

from ..errors import AdapterError, invalid
from ..jsonio import encode
from ..reviewer.tools import bounded
from .schema import FRAMEWORK_DOCS, PHASES, PROMPT, SCHEMA, validate_request
from .sources import DeveloperSources
from .tools import run_tests

RESERVE = 4096


class DeveloperAdapter:
    """One instance owns one episode and never rewrites submitted tests later."""

    def __init__(self, *, client, budget, evidence, context_max_bytes=65536, mode='cubie'):
        if mode not in ('cubie', 'pytest'):
            raise invalid('Developer mode must be cubie or pytest')
        self.client, self.budget, self.evidence = client, budget, evidence
        self.capacity, self.mode = context_max_bytes, mode
        self.index = 0
        self.sources: DeveloperSources
        self.identity: dict = {}
        self.deadline = 0.0
        self.runner_tools = 0

    def develop(self, request):
        """Return one public completion or classified error without writing stdout."""
        incoming = copy.deepcopy(request)
        self.budget.begin_phase()
        try:
            self._start(incoming)
            hashes = self._run()
            self.index += 1
            return self._event(incoming, 'completed', hashes)
        except AdapterError as error:
            return self._event(incoming, error.status, {}, str(error))
        except OSError as error:
            return self._event(incoming, 'infrastructure_error', {}, str(error))

    def _start(self, request):
        """Bind role, phase, workspace and deadline before model or filesystem actions."""
        validate_request(request)
        if self.index >= len(PHASES) or request['phase'] != PHASES[self.index]:
            raise invalid('Developer phases must follow test_design, red, green, refactor exactly once')
        identity = {key: request[key] for key in ('run_id', 'scenario_id', 'workspace', 'task', 'criteria', 'budgets')}
        if bool(self.identity) and identity != self.identity:
            raise invalid('Developer episode identity or configuration changed')
        self._initialize(request, identity)
        self.phase = request['phase']
        self.sources.unchanged()
        self._remaining()
        self.budget.remaining()

    def _initialize(self, request, identity):
        """Initialize episode state once; later requests cannot renew its limits."""
        if not self.identity:
            self.sources = DeveloperSources(request['workspace'])
            self.identity = identity
            self.deadline = time.monotonic() + request['budgets']['wall_time_seconds']
            self.runner_tools = request['budgets'].get('tool_calls', 100)

    def _run(self):
        """Observe immutable red or enter a bounded model-driven phase."""
        if self.phase == 'red':
            return self.sources.hashes()
        content = {'phase': self.phase, 'mode': self.mode, 'framework_docs': FRAMEWORK_DOCS[self.mode],
                   'task': self.identity['task'],
                   'criteria': self.identity['criteria'], 'context': self.sources.context(self.capacity),
                   'production_files': sorted(self.sources.production), 'documentation_files': sorted(self.sources.docs)}
        self.messages = [{'role': 'system', 'content': PROMPT},
                         {'role': 'user', 'content': encode(content).decode('utf-8')}]
        self.observation, self.proposals = None, 0
        return self._loop()

    def _loop(self):
        """One correction shares all episode limits with implementation repairs."""
        corrected = False
        while True:
            self.sources.unchanged()
            try:
                if self._step():
                    return self.sources.hashes()
            except AdapterError as error:
                if error.status != 'invalid_output' or corrected:
                    raise
                corrected = True
                self.messages.append({'role': 'user', 'content': f'Validation error: {error}. Correct the JSON action.'})

    def _step(self):
        """Archive every actual response and tool result, including rejected proposals."""
        started = time.monotonic()
        record = {'request': {'messages': copy.deepcopy(self.messages), 'format': SCHEMA},
                  'raw_response': None, 'action': None, 'tool_result': None, 'artifact_hashes': {}}
        try:
            result = self._chat(record)
            record['raw_response'], record['action'] = result['raw'], result['action']
            done = self._apply(result['action'], record)
            self._feedback(record)
            self._record(record, started, 'completed')
            return done
        except AdapterError as error:
            record['tool_result'] = {**(record['tool_result'] or {}), 'validation_error': str(error)}
            self._feedback(record)
            self._record(record, started, error.status)
            raise

    def _chat(self, record):
        """Preserve provider usage and raw bytes even for invalid model responses."""
        if len(encode({'messages': self.messages, 'format': SCHEMA})) + RESERVE > self.capacity:
            raise AdapterError('budget_exceeded', 'Developer conversation exceeds context capacity')
        timeout = min(self.budget.claim_model(), self._remaining())
        try:
            result = self.client.chat(messages=self.messages, schema=SCHEMA, timeout=timeout)
        except AdapterError as error:
            record['raw_response'] = error.raw
            self._usage(error.usage)
            raise
        self._usage(result['usage'])
        return result

    def _apply(self, action, record):
        """Check the accepted snapshot again after inference and before any action."""
        self.sources.unchanged()
        self.budget.remaining()
        self._remaining()
        name = action['action']
        if name == 'submit_phase':
            return self._submit(record)
        if name == 'write_files':
            return self._write(action['files'], record)
        record['tool_result'] = self._tool(action)
        return False

    def _write(self, files, record):
        """Publish only valid proposals and run the resulting frozen test suite."""
        if self.phase != 'test_design' and self.proposals >= 3:
            raise invalid('Implementation proposal limit reached')
        self._claim_tool()
        record['artifact_hashes'] = self.sources.write(files, self.phase)
        self.proposals += 1
        self.observation = self._tests()
        record['tool_result'] = self.observation
        if self.phase == 'test_design' and self.observation['test_outcome'] != 'assertion_failure':
            raise invalid('Test design needs business red; repair test syntax/imports or add a missing test')
        if self.phase in ('green', 'refactor') and self.proposals >= 3:
            return self._submit(record)
        return False

    def _submit(self, record):
        """Keep no-op refactoring optional and test submission bound to business red."""
        if self.phase == 'test_design':
            if self.observation is None or self.observation['test_outcome'] != 'assertion_failure':
                raise invalid('Test design requires an observed business-red test proposal')
            self.sources.freeze()
        elif self.observation is None:
            self.observation = self._tests()
            record['tool_result'] = self.observation
        if self.phase in ('green', 'refactor') and not any(name in self.sources.expected for name in self.sources.docs):
            raise invalid('Submit new usage documentation before completing implementation')
        if self.phase == 'refactor' and self.observation['test_outcome'] != 'passed':
            raise invalid('Refactor must preserve passing frozen tests')
        record['artifact_hashes'] = self.sources.hashes()
        return True

    def _tool(self, action):
        """Expose only visible reads, literal search and fixed test execution."""
        name = action['action']
        if name == 'run_visible_tests':
            self.observation = self._tests()
            return self.observation
        self._claim_tool()
        policy = self.sources.policy()
        if name == 'list_files':
            return {'files': sorted(policy.readable)}
        if name == 'read_file':
            return {'content': policy.read_file(action['path']).decode('utf-8')}
        return {'matches': self._search(policy, action['query'])}

    def _search(self, policy, query):
        """Search granted text without interpreting source instructions."""
        return [{'path': name, 'line': index, 'text': line}
                for name in sorted(policy.readable)
                for index, line in enumerate(policy.read_file(name).decode('utf-8').splitlines(), 1) if query in line]

    def _tests(self):
        """Derive execution timeout from both clocks and recheck originals afterwards."""
        timeout = self._claim_tool()
        result = run_tests(self.sources, timeout)
        self.sources.unchanged()
        self.budget.remaining()
        self._remaining()
        return result

    def _claim_tool(self):
        """Preserve runner and internal tool counters across every phase."""
        if self.runner_tools <= 0:
            raise AdapterError('budget_exceeded', 'Runner tool call budget exhausted')
        self.runner_tools -= 1
        return min(self.budget.claim_tool(), self._remaining())

    def _feedback(self, record):
        """Put actual responses and bounded diagnostics into the next model request."""
        raw = record['raw_response']
        message = raw.get('message', {}) if isinstance(raw, dict) else {}
        if isinstance(message.get('content'), str):
            self.messages.append({'role': 'assistant', 'content': bounded(message['content'])})
        if record['tool_result'] is not None:
            self.messages.append({'role': 'user', 'content': bounded(encode(record['tool_result']).decode('utf-8'))})

    def _record(self, record, started, status):
        """Write step evidence outside the workspace, leaving stdout clean."""
        self.evidence.record_step(phase=self.phase, **record, duration_seconds=time.monotonic() - started,
                                  usage=self.budget.usage(), status=status)

    def _usage(self, usage):
        """Missing measurements remain unknown even when other calls were measured."""
        usage = usage or {'input_tokens': None, 'output_tokens': None}
        self.budget.record_usage(input_tokens=usage['input_tokens'], output_tokens=usage['output_tokens'])

    def _remaining(self):
        """Keep one conservative episode deadline without renewing it per phase."""
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise AdapterError('budget_exceeded', 'Developer episode time budget exhausted')
        return remaining

    def _event(self, request, status, hashes, reason=None):
        """Bind one result to actual artifact bytes and the current request."""
        event = {key: request.get(key) for key in ('run_id', 'scenario_id', 'phase')}
        event.update(schema_version=1, type='event', status=status, artifacts=list(hashes),
                     artifact_hashes=hashes, usage=self.budget.usage())
        if reason is not None:
            event['reason'] = reason
        return event
