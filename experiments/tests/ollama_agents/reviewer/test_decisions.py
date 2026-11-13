"""Complete review_v1 output, evidence-based rejection and genuine abstention."""

import pytest

from .checks import completed, interrupted
from .support import paraphrased_report, report, response, setup_session, submit


@pytest.mark.parametrize("variant,decision", [("conform", "pass"), ("faulty", "fail")])
def test_new_complete_contexts_produce_source_bound_review(api, reviewer_api, review_workspace, tmp_path, variant, decision):
    root = review_workspace(variant)
    payload = report(decision)
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(payload))])
    event = completed(adapter, root, payload)
    assert event["usage"] == {"input_tokens": 13, "output_tokens": 7, "cost": None}
    assert len(transport.requests) == 1


def test_abstention_is_a_completed_distinct_criterion_decision(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    task = root / "task.md"
    task.write_text("markup_escaping: Entity-Policy wird extern festgelegt und ist nicht verfügbar.\n"
                    "unicode_preserved: Unicode muss erhalten bleiben.\n", encoding="utf-8")
    payload = report("abstain")
    adapter, _, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(payload))])
    completed(adapter, root, payload)


@pytest.mark.parametrize("change", ["missing", "extra", "unknown", "empty-findings", "pass-finding"],
                         ids=["criterion-missing", "foreign-criterion", "unknown-decision", "fail-without-evidence", "contradiction"])
def test_invalid_criterion_coverage_or_unsupported_failure_is_rejected(api, reviewer_api, review_workspace, tmp_path, change):
    root = review_workspace("faulty")
    payload = invalid_decisions(change)
    replies = [response(submit(payload)), response(submit(payload))]
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, replies)
    interrupted(adapter, root, "invalid_output")
    assert len(transport.requests) == 2


def invalid_decisions(change):
    payload = report("fail")
    if change == "missing":
        del payload["criterion_results"]["unicode_preserved"]
    if change == "extra":
        payload["criterion_results"]["style_preference"] = "fail"
    if change == "unknown":
        payload["criterion_results"]["markup_escaping"] = "maybe"
    if change == "empty-findings":
        payload["findings"] = []
    if change == "pass-finding":
        payload["criterion_results"]["markup_escaping"] = "pass"
    return payload


@pytest.mark.parametrize("field,value", [("path", "missing.py"), ("symbol", "invented_function"),
                                        ("criterion_id", "unrequested"), ("mechanism", ""), ("impact", " ")])
def test_findings_must_name_existing_sources_symbols_and_meaningful_fields(api, reviewer_api, review_workspace, tmp_path, field, value):
    root = review_workspace("faulty")
    payload = report("fail")
    payload["findings"][0][field] = value
    adapter, _, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(payload))] * 2)
    interrupted(adapter, root, "invalid_output")


def test_equivalent_free_wording_is_preserved_without_reference_rewriting(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace("faulty")
    payload = paraphrased_report()
    adapter, _, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(payload))])
    completed(adapter, root, payload)


@pytest.mark.parametrize('field,value', [('impact', 'High'), ('impact', 'Severity: critical'),
                                        ('impact', 'Hoch'), ('mechanism', 'N/A')])
def test_severity_and_placeholder_labels_are_not_finding_explanations(api, reviewer_api, review_workspace, tmp_path, field, value):
    root = review_workspace('faulty')
    payload = report('fail')
    payload['findings'][0][field] = value
    adapter, _, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(payload))] * 2)
    interrupted(adapter, root, 'invalid_output')


def test_vague_impact_is_corrected_with_explicit_explanation_request(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace('faulty')
    vague = report('fail')
    vague['findings'][0]['impact'] = 'High'
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path,
                                         [response(submit(vague)), response(submit(report('fail')))])
    completed(adapter, root, report('fail'))
    assert len(transport.requests) == 2
    assert b'impact' in transport.requests[1][0].data and b'expected' in transport.requests[1][0].data
