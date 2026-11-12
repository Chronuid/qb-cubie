"""Additional evidence and recovery boundaries beyond the original v8 catalog."""

import copy

import pytest
from v8_support import CASE, Harness, contract, outcome


def test_unknown_information_cannot_be_erased_by_republishing_context(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.orient()
        h.ok('qa', 'ask_analysis', question='Which exception does the issue require?', reason='Oracle is unspecified')
        h.ok('analysis', 'finish', delivery={'answer': 'Public issue does not specify it.', 'refs': [], 'unresolved': True})
        h.ok('qa', 'ask_analysis', question='Refresh the sources?', reason='Need current source')
        h.ok('analysis', 'update_context', context=h.context())
        return any(q['question'] == 'Which exception does the issue require?' for q in h.snapshot()['open_questions'])
    contract(observe, True)


def test_case_metadata_revision_requires_new_reproduction_even_with_identical_file_bytes(tmp_path):
    def observe():
        h = Harness(tmp_path)
        red, _, _ = h.repaired()
        h.ok('dev', 'request_test_change', case_id='C-1', observed='Pass',
             suspected_error='Revisit the described input', evidence_refs=[red['evidence_id']])
        delivery = h.suite_delivery()
        delivery['cases'][0]['input'] = {'args': [1]}
        h.ok('qa', 'collect_tests', targets=delivery['targets'])
        h.ok('qa', 'finish', delivery=delivery)
        return h.snapshot()['qualifications']
    contract(observe, {'reproduced': False, 'verified': False})


@pytest.mark.parametrize('role', ['qa', 'dev'])
def test_repeated_role_action_requests_analysis_without_ending_task(tmp_path, role):
    def observe():
        h = Harness(tmp_path)
        h.orient() if role == 'qa' else h.suite()
        for _ in range(3):
            h.ok(role, 'read_file', path='tests/test_calc.py', line_start=1, line_end=1)
        state = h.snapshot()
        return state['role'], state['state'], state['status'], state['budget']['deadline']
    contract(observe, ('analysis', 'information', 'running', 1800))


def test_test_change_refusal_keeps_valid_suite_and_returns_to_dev(tmp_path):
    def observe():
        h = Harness(tmp_path)
        red = h.red()
        h.ok('dev', 'request_test_change', case_id='C-1', observed='3',
             suspected_error='Perhaps expect 3?', evidence_refs=[red['evidence_id']])
        h.ok('qa', 'finish', delivery={'accepted': False, 'reason': 'REQ-1 explicitly requires 4.', 'unresolved': False})
        return h.snapshot()['role'], h.snapshot()['cases']['C-1']['expected']
    contract(observe, ('dev', {'returns': 4}))


@pytest.mark.parametrize('explained', [False, True])
def test_green_original_needs_explicit_review_explanation(tmp_path, explained):
    def observe():
        h = Harness(tmp_path, mode='pytest')
        h.suite()
        green_original = h.run(outcome())
        h.edit()
        green = h.run()
        regression = h.run(regression=True)
        evidence = (green_original, green, regression)
        done = h.ok('dev', 'finish', delivery={'summary': 'Change with existing coverage.',
            'evidence_refs': [e['evidence_id'] for e in evidence], 'open_points': []})
        for e in evidence:
            h.ok('analysis', 'read_evidence', ref=e['evidence_id'])
        h.ok('analysis', 'read_evidence', ref=done['diff_ref'])
        delivery = {'verdict': 'verified', 'requirement_ids': ['REQ-1'],
            'reason': 'Inspected current patch, original coverage and final tests.',
            'evidence_refs': [e['evidence_id'] for e in evidence], 'open_points': []}
        if explained:
            delivery['existing_coverage_reason'] = 'The original focused run already covered these inputs; the inspected patch preserves the behavior.'
        h.send('analysis', 'finish', delivery=delivery)
        return h.snapshot()['completion']['allowed'], h.snapshot()['qualifications']['reproduced']
    contract(observe, (explained, False))


def test_changed_note_does_not_hide_cached_test_execution(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        first = h.run(reason='First test invocation')
        second = h.ok('dev', 'run_tests', targets=h.suite_delivery()['targets'], reason='Another wording')
        return second['cached'], second['evidence_id'] == first['evidence_id'], len(h.io.runs)
    contract(observe, (True, True, 1))


def test_invalid_nested_delivery_is_atomic(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.orient()
        h.ok('qa', 'collect_tests', targets=h.suite_delivery()['targets'])
        case = copy.deepcopy(CASE)
        case['input'] = 'not structured input'
        before = h.snapshot()['active_job']
        result = h.send('qa', 'finish', delivery=h.suite_delivery() | {'cases': [case]})
        return result['status'], h.snapshot()['active_job'] == before, h.snapshot()['cases']
    contract(observe, ('rejected', True, {}))


def test_partial_knowledge_update_preserves_requirements_and_sources(tmp_path):
    def observe():
        h = Harness(tmp_path)
        original = h.context()
        h.ok('analysis', 'update_context', context=original)
        h.ok('analysis', 'update_context', context={'hypotheses': ['Only the offset is wrong.']})
        return (h.team.context['requirements'] == original['requirements'],
                h.team.context['source_refs'] == original['source_refs'], h.snapshot()['context_revision'])
    contract(observe, (True, True, 2))


def test_analysis_can_classify_a_new_path_but_cannot_relabel_production_as_tests(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.ok('analysis', 'update_context', context=h.context())
        assignment = {'path': 'checks', 'kind': 'tests', 'reason': 'A new test directory for the issue.',
                      'refs': ['issue:REQ-1']}
        h.ok('analysis', 'update_context', context={'path_assignments': [assignment]})
        before = h.snapshot()['context_revision']
        r = h.send('analysis', 'update_context', context={'path_assignments': [assignment | {'path': 'src'}]})
        return h.team.manifest['checks'], h.team.manifest['src'], r['status'], h.snapshot()['context_revision'] == before
    contract(observe, ('tests', 'production', 'rejected', True))
