"""Additional counterexamples for request validation and post-inference boundaries."""

import pytest

from ...benchmarks.contracts import accepted
from ..conftest import ReplayTransport
from .checks import interrupted, records
from .support import report, request, response, setup_session, submit


@pytest.mark.parametrize('field,value', [('workspace', '../visible'), ('criteria', []),
                                        ('criteria', ['same', 'same']), ('criteria', [' ']),
                                        ('phase', 'green'), ('schema_version', True),
                                        ('budgets', {'wall_time_seconds': 0}),
                                        ('budgets', {'wall_time_seconds': 10, 'tool_calls': 1.5})])
def test_invalid_requests_fail_before_reading_or_inference(api, reviewer_api, review_workspace, tmp_path, field, value):
    root = review_workspace()
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [])
    incoming = request(root, **{field: value})
    accepted(lambda: adapter.review(incoming), expected=lambda event: event['status'] == 'invalid_output')
    assert not transport.requests and not (root / 'review.json').exists()


def test_expired_ledger_after_model_response_prevents_publication(api, reviewer_api, review_workspace, tmp_path, monkeypatch):
    root = review_workspace()
    clock = [100.0]
    adapter, _, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(report()))], clock=lambda: clock[0])
    original = ReplayTransport.__call__

    def expire(self, outgoing, *, timeout):
        reply = original(self, outgoing, timeout=timeout)
        clock[0] = 1000.0
        return reply

    monkeypatch.setattr(ReplayTransport, '__call__', expire)
    interrupted(adapter, root, 'budget_exceeded')


def test_source_replaced_with_symlink_aborts_without_model_repair(api, reviewer_api, review_workspace, tmp_path, monkeypatch):
    root = review_workspace()
    private = root.parent / 'private.py'
    private.write_text('PRIVATE_SENTINEL', encoding='utf-8')
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(report()))])
    original = ReplayTransport.__call__

    def replace(self, outgoing, *, timeout):
        (root / 'escaping.py').unlink()
        (root / 'escaping.py').symlink_to(private)
        return original(self, outgoing, timeout=timeout)

    monkeypatch.setattr(ReplayTransport, '__call__', replace)
    interrupted(adapter, root, 'invalid_output')
    assert len(transport.requests) == 1


def test_final_invalid_response_archives_the_validation_reason(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    payload = report()
    payload['criterion_results'] = {}
    adapter, _, writer = setup_session(api, reviewer_api, root, tmp_path, [response(submit(payload))] * 2)
    interrupted(adapter, root, 'invalid_output')
    steps = records(writer, tmp_path)
    assert len(steps) == 2 and 'criteri' in steps[-1]['tool_result']['validation_error'].lower()


def test_visible_test_process_is_terminated_at_request_deadline(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    (root / 'tests/test_renderer.py').write_text('import time\ndef test_wait():\n    time.sleep(60)\n', encoding='utf-8')
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [response({'action': 'run_visible_tests'})])
    incoming = request(root, budgets={'wall_time_seconds': 0.5, 'tool_calls': 1})
    accepted(lambda: adapter.review(incoming), expected=lambda event: event['status'] == 'agent_timeout')
    assert len(transport.requests) == 1 and not (root / 'review.json').exists()
