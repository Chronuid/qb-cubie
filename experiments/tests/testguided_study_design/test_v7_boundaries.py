"""Additional v7 checks for deadlines, recovery and archived study identity."""

import copy
import json
from types import SimpleNamespace

import pytest
from ollama_agents.errors import AdapterError
from testguided_study import team_agent
from testguided_study.artifacts import freeze, load_config, read, verify
from testguided_study.design import default_design
from testguided_study.iteration import freeze_design, identity, load_design
from testguided_study.launch import save_config
from testguided_study.report import workflow
from testguided_study.smoke import generate
from v6_support import GUIDES, ISSUE, NODE, outcome
from v7_support import Harness


def names(request):
    return {e['properties']['action']['const'] for e in request['schema']['oneOf']}


def test_start_card_is_bounded_public_and_budgeted(tmp_path):
    h = Harness(tmp_path, start_card_chars=500)
    context = read(tmp_path / 'archive/context.json')
    assert context['issue_ref'] == 'issue:REQ-1'
    assert 'src' in context['start_card']['layouts']
    assert len(json.dumps(context['start_card'])) <= 500
    assert 'SECRET_SENTINEL' not in json.dumps(context)
    assert h.snapshot()['metrics']['tool_calls'] == 1
    assert read(tmp_path / 'archive/actions/0001.json')['actor'] == 'controller'


@pytest.mark.parametrize('changed', [False, True])
def test_find_paths_cursor_is_bound_to_inventory(tmp_path, changed):
    h = Harness(tmp_path, search_page_size=2)
    (h.root / 'src/extra.py').write_text('value = 1\n')
    first = h.ok('analysis', 'find_paths', pattern='src/*')
    if changed:
        (h.root / 'src/new.py').write_text('value = 0\n')
    result = h.send('analysis', 'find_paths', pattern='src/*', cursor=first['next_cursor'])
    if changed:
        assert result['status'] == 'cursor_error'
    else:
        assert result['status'] == 'completed'
        assert sorted(first['files'] + result['files']) == sorted(h.team.store.inventory().keys() & {
            'src/calc.py', 'src/extra.py', 'src/requests/utils.py'})


def test_recovery_archive_keeps_model_action_and_controller_diagnosis(tmp_path):
    h = Harness(tmp_path)
    for query in ('absent-A', 'absent-B'):
        h.send('analysis', 'search_content', scope='src', query=query)
    actions = [read(p) for p in sorted((tmp_path / 'archive/actions').glob('*.json'))]
    assert [a['actor'] for a in actions] == ['controller', 'model', 'model', 'controller']
    assert actions[2]['action']['query'] == 'absent-B'
    assert actions[3]['action']['action'] == 'find_paths'


def test_resolved_recovery_does_not_block_a_different_later_episode(tmp_path):
    h = Harness(tmp_path)
    for query in ('missing-A', 'missing-B'):
        h.send('analysis', 'search_content', scope='src', query=query)
    h.ok('analysis', 'read_file', path='src/calc.py', line_start=1, line_end=2)
    assert h.snapshot()['recovery_episodes'][0]['status'] == 'resolved'
    assert 'search_content' in names(h.team.request())
    # A separate work blockage is eligible for its own diagnostic.
    h.send('analysis', 'finish_orientation', requirements=[], source_refs=[], test_entry_refs=[], hypotheses=[], unknowns=[])
    h.send('analysis', 'finish_orientation', requirements=[], source_refs=[], test_entry_refs=[], hypotheses=[], unknowns=[])
    assert h.snapshot()['metrics']['recoveries'] == 2
    assert h.snapshot()['status'] == 'running'


def test_qa_information_request_uses_the_same_task_deadline(tmp_path):
    h = Harness(tmp_path)
    h.orient()
    job = copy.deepcopy(h.snapshot()['active_job'])
    h.clock.now = 150
    question = h.ok('qa', 'ask_analysis', question='Which contract applies?', refs=['issue:REQ-1'])
    h.clock.now = 179
    assert h.team.request()['timeout_seconds'] == 1621
    h.clock.now = 225
    h.tick()
    assert h.snapshot()['role'] == 'analysis'
    assert h.snapshot()['status'] == 'running'
    h.ok('analysis', 'answer_question', reply_to=question['message_id'], answer=ISSUE,
         refs=['issue:REQ-1'], unknown=False)
    assert h.snapshot()['active_job'] == job
    assert h.snapshot()['jobs'][job['id']]['deadline'] == 1800




def test_qa_calls_have_no_phase_limit(tmp_path):
    h = Harness(tmp_path)
    h.orient()
    for _ in range(110):
        assert h.team.request()['role'] == 'qa'
    h.tick()
    job = h.snapshot()['jobs'][h.snapshot()['active_job']['id']]
    assert job['calls'] == 110 and job['limit'] is None
    assert h.snapshot()['status'] == 'running'




def test_orientation_retains_navigation_beyond_previous_last_request(tmp_path):
    h = Harness(tmp_path)
    for _ in range(7):
        request = h.team.request()
    assert {'read_file', 'finish_orientation'} <= names(request)
    h.ok('analysis', 'read_file', path='src/calc.py', line_start=1, line_end=2)
    h.tick()
    assert h.snapshot()['role'] == 'analysis'




def test_invalid_orientation_response_retries_without_forced_handoff(tmp_path):
    h = Harness(tmp_path)
    for _ in range(6):
        h.team.request()
    h.team.reject_output(raw={'bad': True}, usage={})
    assert h.snapshot()['role'] == 'analysis'
    assert h.snapshot()['metrics']['output_repairs'] == 1
    assert h.team.output_repair is True




def test_navigation_cannot_search_controller_artifacts(tmp_path):
    h = Harness(tmp_path)
    (h.root / 'artifacts').mkdir()
    (h.root / 'artifacts/report.txt').write_text('INTERNAL_SENTINEL\n')
    result = h.send('analysis', 'search_content', scope='artifacts', query='INTERNAL_SENTINEL')
    assert result['status'] == 'scope_denied'
    assert not result.get('hits')
    assert h.ok('analysis', 'find_paths', pattern='artifacts/*')['files'] == []


@pytest.mark.parametrize('phase', ['orient', 'specify', 'reproduce', 'review'])
def test_output_repair_uses_current_phase_schema_without_attempt_limit(tmp_path, phase):
    h = Harness(tmp_path)
    if phase == 'specify':
        h.orient()
    elif phase == 'reproduce':
        h.suite()
    elif phase == 'review':
        h.verified()
    h.team.request()
    h.team.reject_output(raw={'bad': True}, usage={})
    request = h.team.request()
    assert names(request)
    assert 'submit' not in names(request)
    assert h.snapshot()['metrics']['output_repairs'] == 1
    assert h.snapshot()['metrics']['model_calls'] == 2
    h.team.reject_output(raw={'bad': True}, usage={})
    assert h.snapshot()['status'] == 'running'
    assert h.snapshot()['metrics']['output_repairs'] == 2
    assert h.team.request() is not None


def test_reserve_still_allows_current_tests_and_review(tmp_path):
    h = Harness(tmp_path)
    h.red()
    h.edit()
    h.clock.now = 720
    h.run()
    h.run(purpose='regression')
    h.ok('dev', 'publish_implementation', requirement_ids=['REQ-1'], open_points=[])
    h.ok('analysis', 'verify_completion')
    h.ok('analysis', 'submit', reason='Current evidence')
    assert h.snapshot()['status'] == 'submitted'


def test_confirmed_requirements_cannot_be_silently_weakened(tmp_path):
    h = Harness(tmp_path)
    h.orient()
    h.prepare_suite()
    before = h.snapshot()
    result = h.send('qa', 'confirm_requirements', requirements=[{
        'id': 'REQ-1', 'text': 'double(2) returns any integer.', 'refs': ['issue:REQ-1']}])
    assert result['status'] == 'rejected'
    assert h.snapshot()['context_revision'] == before['context_revision']
    assert h.snapshot()['cases'] == before['cases']


def test_information_time_is_shared_only_across_information_jobs(tmp_path):
    h = Harness(tmp_path)
    h.suite()
    first = h.ok('dev', 'ask_analysis', question='First API question?', refs=['issue:REQ-1'])
    h.clock.now = 20
    h.ok('analysis', 'answer_question', reply_to=first['message_id'], answer=ISSUE, refs=['issue:REQ-1'], unknown=False)
    # Ordinary Dev time does not consume the combined information allowance.
    h.clock.now = 200
    second = h.ok('dev', 'ask_analysis', question='Second API question?', refs=['issue:REQ-1'])
    assert h.team.request()['timeout_seconds'] == 1600
    h.clock.now = 220
    h.ok('analysis', 'answer_question', reply_to=second['message_id'], answer=ISSUE, refs=['issue:REQ-1'], unknown=False)
    assert h.team.information_seconds_used == 40


def test_cosmetic_production_change_does_not_claim_work_progress(tmp_path):
    h = Harness(tmp_path)
    h.red()
    source = h.ok('dev', 'read_file', path='src/calc.py', line_start=2, line_end=2)
    before = h.snapshot()['progress']['work']
    h.ok('dev', 'replace_region', handle=source['handle'], new_text='    return value * 2 - 1  # comment\n', reason='REQ-1')
    assert h.snapshot()['progress']['work'] == before
    assert h.snapshot()['qualifications']['verified'] is False


def test_same_current_test_run_reuses_evidence_without_backend_execution(tmp_path):
    h = Harness(tmp_path)
    red = h.red()
    runs = len(h.io.runs)
    result = h.ok('dev', 'run_tests', targets=[NODE], purpose='focused')
    assert result['duplicate_action'] is True
    assert result['evidence_id'] == red['evidence_id']
    assert len(h.io.runs) == runs


def test_dev_recovery_keeps_the_job_available_for_a_focused_test(tmp_path):
    h = Harness(tmp_path)
    h.suite()
    for _ in range(8):
        h.ok('dev', 'read_context')
    assert h.snapshot()['status'] == 'running'
    assert h.snapshot()['state'] == 'reproduce'
    assert len(h.io.runs) == 0
    h.run(outcome('assertion_failure', failed=[(NODE, 'AssertionError', 'assert 3 == 4')]))
    assert h.snapshot()['qualifications']['reproduced'] is True
    assert h.snapshot()['state'] == 'implement'
    assert len(h.io.runs) == 1




def test_report_counts_missing_milestones_in_the_scheduled_denominator():
    summary = workflow([
        {'agent': {'process_metrics': {'milestones': {
            'qa': {'seconds': 12, 'model_calls': 2}, 'suite': {'seconds': 20, 'model_calls': 4}}}}},
        {'agent': {'process_metrics': {'milestones': {'qa': {'seconds': 30, 'model_calls': 6}}}}},
        {'resolved': None},
    ])
    assert summary['qa']['reached'] == 2
    assert summary['qa']['scheduled'] == 3
    assert summary['qa']['mean_seconds_when_reached'] == 21
    assert summary['red']['mean_seconds_when_reached'] is None
    assert summary['suite_per_started_qa'] == {'numerator': 1, 'denominator': 2, 'rate': 0.5}


def test_invalid_suite_does_not_change_published_targets(tmp_path):
    h = Harness(tmp_path)
    h.orient()
    h.prepare_suite()
    result = h.send('qa', 'publish_suite', case_ids=['C-1'], targets=['tests/test_old.py'], expected_red={'C-1': '4'})
    assert result['status'] == 'rejected'
    assert h.team.suite_cases == [] and h.team.targets == []


def test_environment_change_invalidates_suite_collection(tmp_path):
    h = Harness(tmp_path)
    h.orient()
    h.prepare_suite()
    (h.root / 'environment.json').write_text('{"python": "changed"}\n')
    assert h.send('qa', 'publish_suite', case_ids=['C-1'], targets=[NODE], expected_red={'C-1': '4'})['status'] == 'rejected'


def test_freeze_and_load_keep_explicit_v7_identity(tmp_path):
    design = default_design('cubie', GUIDES, version=7)
    freeze_design(design, tmp_path / 'design.json')
    assert identity(load_design(tmp_path / 'design.json')) == identity(design)
    generate(tmp_path / 'input')
    path = tmp_path / 'input/study.toml'
    config = load_config(path)
    config['agent_version'] = 7
    config['ollama']['think'] = False
    save_config(path, config)
    freeze(path, tmp_path / 'frozen')
    assert verify(tmp_path / 'frozen')['agent_version'] == 7
    assert read(tmp_path / 'frozen/designs/cubie.json')['design']['core']['context']['version'] == 7
    assert default_design('cubie', GUIDES)['core']['context']['version'] == 5


@pytest.mark.parametrize('failure', ['agent_timeout', 'invalid_output', 'late_response'])
def test_runner_passes_remaining_task_time_and_preserves_archive_on_provider_failure(tmp_path, failure):
    h = Harness(tmp_path / 'setup')
    directory = tmp_path / 'run'
    calls = []

    class Client:
        def chat(self, **request):
            calls.append(request)
            if len(calls) == 3:
                raise AdapterError('infrastructure_error', 'Controlled stop after observing QA activation')
            if len(calls) == 1:
                h.clock.now = 100
                if failure != 'late_response':
                    raise AdapterError(failure, 'Controlled provider failure', usage={'output_tokens': 10})
                return {'action': {'action': 'read_file', 'path': 'src/calc.py', 'line_start': 1, 'line_end': 2}}
            h.clock.now = 120
            return {'action': {'action': 'finish_orientation', 'requirements': [
                {'id': 'REQ-1', 'text': ISSUE, 'refs': ['issue:REQ-1'], 'status': 'confirmed'}],
                'source_refs': [], 'test_entry_refs': [], 'hypotheses': [], 'unknowns': []}}

    design = default_design('pytest', GUIDES, version=7)
    config = {'budgets': {'wall_seconds': 900, 'model_calls': 48, 'tool_calls': 96,
                          'context_bytes': 80000, 'command_seconds': 30, 'output_chars': 12000},
              'ollama': {'think': False, 'temperature': 0.2, 'num_ctx': 32768, 'num_predict': 8192}}
    result = team_agent.develop(None, None, SimpleNamespace(problem_statement=ISSUE),
        {'mode': 'pytest', 'seed': 42, 'run_id': '0001'}, config, GUIDES, directory,
        design=design, client=Client(), clock=h.clock, store=h.team.store, io=h.io)
    assert [c['timeout'] for c in calls] == [900, 800, 780]
    assert result['team']['role'] == 'qa'
    assert result['team']['context_revision'] == 1
    assert read(directory / 'context.json')['provisional'] is False
    assert result['repairs'] == (0 if failure == 'late_response' else 1)
    assert (directory / 'production.patch').exists()
    assert result['private_evaluation_required'] is True
