"""Compose source-bound review, bounded corrections, tools and complete evidence."""

import copy
import time

from ..errors import AdapterError, invalid
from ..jsonio import encode
from .request import validate_request
from .schema import PROMPT, SCHEMA
from .sources import ReviewSources, SourceChanged
from .tools import bounded, execute

RESERVE = 2048


class ReviewerAdapter:
    """Handle one fresh reviewer episode without touching submitted source files."""

    def __init__(self, *, client, budget, evidence, context_max_bytes=65536):
        self.client, self.budget, self.evidence = client, budget, evidence
        self.capacity = context_max_bytes
        self._used = False

    def review(self, request):
        """Return one v1 event; archive internal work without writing to stdout."""
        incoming = copy.deepcopy(request)
        try:
            self._start(incoming)
            hashes = self._run(incoming)
            return self._event(incoming, 'completed', hashes)
        except AdapterError as error:
            return self._event(incoming, error.status, {}, str(error))
        except OSError as error:
            return self._event(incoming, 'infrastructure_error', {}, str(error))

    def _start(self, request):
        """Validate the role request before collecting sources or starting inference."""
        if self._used:
            raise invalid('ReviewerAdapter requires a fresh instance for every episode')
        self._used = True
        validate_request(request)
        self.deadline = time.monotonic() + request['budgets']['wall_time_seconds']
        self.runner_tools = request['budgets'].get('tool_calls', 20)
        self.budget.begin_phase()

    def _run(self, request):
        """Prepare the complete small context and enter the bounded action loop."""
        header = {'task': request['task'], 'criteria': request['criteria']}
        overhead = len(encode(header)) + len(encode(SCHEMA)) + len(PROMPT.encode()) + 512
        self.sources = ReviewSources(request['workspace'], max_bytes=self.capacity,
                                     prompt_bytes=overhead, output_reserve_bytes=RESERVE)
        content = encode({**header, 'context': self.sources.context}).decode('utf-8')
        self.messages = [{'role': 'system', 'content': PROMPT}, {'role': 'user', 'content': content}]
        return self._loop(request['criteria'])

    def _loop(self, criteria):
        """Permit at most one corrective response within the episode budgets."""
        corrected = False
        while True:
            self.sources.unchanged()
            try:
                hashes = self._step(criteria)
                if hashes is not None:
                    return hashes
            except AdapterError as error:
                if error.status != 'invalid_output' or isinstance(error, SourceChanged) or corrected:
                    raise
                corrected = True
                self.messages.append({'role': 'user', 'content': f'Validation error: {error}. Correct the JSON action.'})

    def _step(self, criteria):
        """Measure and archive every attempted model action, including invalid ones."""
        started = time.monotonic()
        record = {'request': {'messages': copy.deepcopy(self.messages), 'format': SCHEMA},
                  'raw_response': None, 'action': None, 'tool_result': None, 'artifact_hashes': {}}
        try:
            result = self._chat(record)
            record['raw_response'], record['action'] = result['raw'], result['action']
            hashes = self._apply(result['action'], criteria, record)
            self._record(record, started, 'completed')
            return hashes
        except AdapterError as error:
            self._failure(record, started, error)
            raise

    def _failure(self, record, started, error):
        """Retain the final validation reason even when no correction remains."""
        if record['tool_result'] is None:
            record['tool_result'] = {'validation_error': str(error)}
        self._rejected_response(record)
        self._record(record, started, error.status)

    def _rejected_response(self, record):
        """Show the rejected answer to the correction step alongside its validation error."""
        raw = record['raw_response']
        message = raw.get('message', {}) if isinstance(raw, dict) else {}
        content = message.get('content')
        if isinstance(content, str):
            self.messages.append({'role': 'assistant', 'content': bounded(content)})

    def _chat(self, record):
        """Preserve provider usage and raw evidence even when response validation fails."""
        self._fits()
        timeout = min(self.budget.claim_model(), self._remaining())
        try:
            result = self.client.chat(messages=self.messages, schema=SCHEMA, timeout=timeout)
        except AdapterError as error:
            record['raw_response'] = error.raw
            self._usage(error.usage)
            raise
        self._usage(result['usage'])
        return result

    def _apply(self, action, criteria, record):
        """Check immutable sources before executing tools or publishing a review."""
        self.sources.unchanged()
        self._remaining()
        self.budget.remaining()
        if action['action'] == 'submit_review':
            self.sources.validate(action['review'], criteria)
            record['artifact_hashes'] = self.sources.publish(action['review'])
            return record['artifact_hashes']
        return self._tool(action, record)

    def _tool(self, action, record):
        """Enforce both call budgets and feed bounded local evidence back to the model."""
        if self.runner_tools <= 0:
            raise AdapterError('budget_exceeded', 'Runner tool call budget exhausted')
        self.runner_tools -= 1
        timeout = min(self.budget.claim_tool(), self._remaining())
        record['tool_result'] = execute(action, self.sources, timeout)
        self.messages.append({'role': 'assistant', 'content': encode(action).decode('utf-8')})
        self.messages.append({'role': 'user', 'content': bounded(encode(record['tool_result']).decode('utf-8'))})

    def _record(self, record, started, status):
        """Persist the request, response, action, tool result and phase usage."""
        self.evidence.record_step(phase='review', **record, duration_seconds=time.monotonic() - started,
                                  usage=self.budget.usage(), status=status)

    def _usage(self, usage):
        """Keep missing measurements unknown while summing all actual model calls."""
        usage = usage or {'input_tokens': None, 'output_tokens': None}
        self.budget.record_usage(input_tokens=usage['input_tokens'], output_tokens=usage['output_tokens'])

    def _fits(self):
        """Bound growing conversation and schema with a separate output reserve."""
        if len(encode({'messages': self.messages, 'format': SCHEMA})) + RESERVE > self.capacity:
            raise AdapterError('budget_exceeded', 'Review conversation exceeds context capacity')

    def _remaining(self):
        """Respect the request deadline as well as the independently supplied ledger."""
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise AdapterError('budget_exceeded', 'Review request time budget exhausted')
        return remaining

    def _event(self, request, status, hashes, reason=None):
        """Bind one result to the originating request and actual written artifact bytes."""
        event = {key: request.get(key) for key in ('run_id', 'scenario_id', 'phase')}
        event.update(schema_version=1, type='event', status=status, artifacts=list(hashes),
                     artifact_hashes=hashes, usage=self.budget.usage())
        if reason is not None:
            event['reason'] = reason
        return event

