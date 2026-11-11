"""Additional offline coverage for admission, actual Git trees and patch grading."""

import hashlib
import json
import shutil
import time
from pathlib import Path

import pytest

from qb_cubie.benchmarks import (
    import_swebench,
    load_package,
    plan_suite,
    plan_swebench_import,
    validate_swebench_references,
)
from qb_cubie.benchmarks.execution._inputs import _copy_package
from qb_cubie.benchmarks.swebench.admission import check_report, copy_report
from qb_cubie.benchmarks.swebench.evaluation import evaluate_patch, protect_tests

from .conftest import GOLD, TEST_PATCH, git, rewrite_snapshot
from .test_reference_validation import executor_fixture


def suite_file(tmp_path, sources):
    path = tmp_path / 'suite.toml'
    path.write_text('schema_version = 1\nname = "repair-study"\nprofile = "agent-evaluation"\n'
                    'repetitions = 1\noutput = "results"\nagents = ["agent.toml"]\n' +
                    ''.join(f'[[sources]]\npath = {json.dumps(str(root))}\n' +
                            (f'reference_report = {json.dumps(str(report))}\n' if report else '') for root, report in sources))
    (tmp_path / 'agent.toml').write_text('schema_version = 1\nid = "repair-agent"\ncommand = ["adapter"]\n'
                                       'capabilities = ["workspace_changes", "project_patch", "wall_time", "tool_calls", "cancel"]\n')
    return path


def test_selection_matches_published_hash_ranking(config, public_api):
    config.update(instance_ids=[], seed=-17, limit=2)
    ids = [f'demo__calc-{n}' for n in (1, 2, 3)]
    expected = sorted(sorted(ids, key=lambda name: hashlib.sha256(f'-17\n{name}'.encode()).hexdigest())[:2])
    result = plan_swebench_import(config)
    assert [row['instance_id'] for row in result['selection']] == expected


@pytest.mark.parametrize('setup', ['', None])
def test_missing_setup_and_empty_regression_are_explicit(config, snapshot, setup):
    snapshot['records'][0].update(environment_setup_commit=setup, PASS_TO_PASS=[])
    rewrite_snapshot(snapshot)
    row = plan_swebench_import(config)['selection'][0]
    assert row['environment_setup_commit'] is None and row['PASS_TO_PASS'] == []


def test_safe_symlinks_and_executable_modes_survive_export(config, snapshot, tmp_path):
    repo = snapshot['repo']
    git(repo, 'checkout', '--detach', snapshot['base'])
    (repo / 'tool').write_text('#!/bin/sh\nexit 0\n')
    (repo / 'tool').chmod(0o755)
    (repo / 'alias').symlink_to('tool')
    git(repo, 'add', '.')
    git(repo, 'commit', '-m', 'Safe executable and symlink')
    for row in snapshot['records']:
        row['base_commit'] = git(repo, 'rev-parse', 'HEAD')
    rewrite_snapshot(snapshot)
    root = tmp_path / 'package'
    import_swebench(config, root)
    visible = root / 'scenarios/demo__calc-1/visible'
    assert (visible / 'alias').readlink() == Path('tool')
    assert (visible / 'tool').stat().st_mode & 0o777 == 0o755
    assert load_package(root)


def test_private_manifest_participates_in_planning_identity(config, tmp_path):
    root = tmp_path / 'package'
    import_swebench(config, root)
    package = load_package(root)
    from qb_cubie.benchmarks.planning._planning import _identity
    before = _identity(root, package)
    path = root / 'swebench-import.json'
    path.write_bytes(path.read_bytes() + b'\n')
    assert _identity(root, package) != before


def test_repair_plan_requires_bound_report_before_start(config, tmp_path):
    root = tmp_path / 'package'
    import_swebench(config, root)
    with pytest.raises(ValueError, match='reference_report'):
        plan_suite(suite_file(tmp_path, [(root, None)]))
    execute, _ = executor_fixture()
    report = validate_swebench_references(root, executor=execute)
    planned = plan_suite(suite_file(tmp_path, [(root, report['report'])]))
    assert all(run['process_profile'] == 'issue_resolution' and 'project_patch' in run['required_capabilities']
               and 'phased_submission' not in run['required_capabilities'] for run in planned['runs'])
    assert all(run['source']['repo'] == 'demo/calc' and run['import_summary']['potentially_known'] for run in planned['runs'])


def test_overlapping_instances_across_namespaces_are_rejected(config, tmp_path):
    roots, reports = [], []
    for namespace in ('full-study', 'lite-study'):
        root = tmp_path / namespace
        import_swebench({**config, 'namespace': namespace}, root)
        execute, _ = executor_fixture()
        roots.append(root)
        reports.append(validate_swebench_references(root, executor=execute)['report'])
    with pytest.raises(ValueError, match='overlapping|duplicate'):
        plan_suite(suite_file(tmp_path, list(zip(roots, reports, strict=True))))


def test_report_and_package_can_be_archived_and_moved_together(config, tmp_path):
    root = tmp_path / 'package'
    import_swebench(config, root)
    execute, _ = executor_fixture()
    report = validate_swebench_references(root, executor=execute)
    bundle = tmp_path / 'bundle'
    _copy_package(root, bundle / 'package', load_package(root))
    copy_report(report['report'], bundle / 'evidence/report.json')
    moved = tmp_path / 'moved'
    shutil.move(bundle, moved)
    assert check_report(moved / 'evidence/report.json', moved / 'package', load_package(moved / 'package'))
    (moved / 'evidence/demo__calc-1/base/tests.json').write_text('{}')
    with pytest.raises(ValueError, match='integrity'):
        check_report(moved / 'evidence/report.json', moved / 'package', load_package(moved / 'package'))


@pytest.mark.parametrize('gold_passes', [True, False])
def test_agent_patch_quality_has_no_tdd_process_credit(config, tmp_path, gold_passes):
    root = tmp_path / 'package'
    import_swebench(config, root)
    case = load_package(root)['scenarios'][0]
    base = (root / case['manifest']).parent
    reference = json.loads((base / case['evaluator']['reference']).read_text())
    artifact = tmp_path / 'submission.patch'
    artifact.write_text(GOLD)
    context = {'base': base, 'reference': reference, 'root': tmp_path, 'directory': tmp_path / 'episode',
               'deadline': time.monotonic() + 30}
    executor, _ = executor_fixture(None if gold_passes else 'regression')
    result = evaluate_patch(context, artifact, executor=executor)
    assert result['quality_passed'] is gold_passes and result['process_passed'] is None
    assert result['evaluation_status'] == 'complete' and result['status'] == 'completed'


def test_agent_patch_cannot_replace_private_tests():
    with pytest.raises(ValueError, match='test and collection'):
        protect_tests(TEST_PATCH, TEST_PATCH)


def test_freeze_keeps_repair_admission_without_runtime_or_agent_start(config, tmp_path):
    from qb_cubie.benchmarks import freeze_suite
    from qb_cubie.benchmarks.measurement._bundle import verify
    root = tmp_path / 'package'
    import_swebench(config, root)
    execute, _ = executor_fixture()
    report = validate_swebench_references(root, executor=execute)
    suite = suite_file(tmp_path, [(root, report['report'])])
    agent = tmp_path / 'agent.toml'
    agent.write_text(agent.read_text() + 'transport = "jsonl-v1"\ncontainer_image = "sha256:' + 'e' * 64 + '"\n')
    destination = tmp_path / 'frozen'
    freeze_suite(suite, destination)
    manifest = verify(destination)
    assert manifest['plan']['runs'][0]['reference_report_sha256']
    assert (destination / 'inputs/references/swebench-fixture/report.json').is_file()
    assert plan_suite(destination / 'inputs/suite.toml')['runs'] == manifest['plan']['runs']


def test_git_replacements_and_caller_environment_cannot_change_base(config, snapshot, tmp_path, monkeypatch):
    git(snapshot['repo'], 'replace', snapshot['base'], 'HEAD')
    monkeypatch.setenv('GIT_WORK_TREE', str(tmp_path / 'unrelated'))
    monkeypatch.setenv('GIT_OBJECT_DIRECTORY', str(tmp_path / 'unrelated-objects'))
    root = tmp_path / 'package'
    import_swebench(config, root)
    assert (root / 'scenarios/demo__calc-1/visible/calc.py').read_text() == 'def total(values):\n    return 0\n'


def test_frozen_repair_runs_through_real_jsonl_transport_and_reporting(config, tmp_path, monkeypatch):
    """Replace only the container/executor boundaries; exercise the full runner."""
    import sys

    from qb_cubie.benchmarks import freeze_suite, run_frozen_suite, summarize_pilot
    from qb_cubie.benchmarks.swebench import agent, runtime

    root = tmp_path / 'package'
    import_swebench(config, root)
    execute, _ = executor_fixture()
    report = validate_swebench_references(root, executor=execute)
    suite = suite_file(tmp_path, [(root, report['report'])])
    agent_path = tmp_path / 'agent.toml'
    agent_path.write_text(agent_path.read_text() + 'transport = "jsonl-v1"\ncontainer_image = "sha256:' + 'e' * 64 + '"\n')
    replay = tmp_path / 'replay-agent.py'
    replay.write_text('''import hashlib, json, pathlib, sys
for line in sys.stdin:
    request = json.loads(line)
    if request['type'] == 'capabilities':
        answer = dict(schema_version=1, type='capabilities', agent_id='repair-agent', agent_version='synthetic-replay',
                      capabilities=['workspace_changes', 'project_patch', 'wall_time', 'tool_calls', 'cancel'])
    else:
        workspace = pathlib.Path(request['workspace'])
        visible = b'\\n'.join(path.read_bytes() for path in workspace.rglob('*') if path.is_file())
        assert b'GOLD_SOLUTION_SENTINEL' not in visible and b'PRIVATE_TEST_SENTINEL' not in visible
        assert 'FAIL_TO_PASS' not in request and 'reference' not in request
        assert request['phase'] == 'repair' and request['output_format'] == 'patch_v1'
        artifact = workspace / 'submission.patch'
        artifact.write_text(''' + repr(GOLD) + ''')
        answer = dict(schema_version=1, type='event', run_id=request['run_id'], scenario_id=request['scenario_id'],
                      phase='repair', status='completed', artifacts=['submission.patch'],
                      artifact_hashes={'submission.patch': hashlib.sha256(artifact.read_bytes()).hexdigest()},
                      usage={'input_tokens': 0, 'output_tokens': 0, 'cost': None})
    print(json.dumps(answer), flush=True)
''')

    class SyntheticContainer:
        def __init__(self, *args):
            pass

        def __enter__(self):
            return [sys.executable, str(replay)]

        def stop(self):
            pass

        def __exit__(self, *_):
            self.stop()

    class SyntheticExecutor:
        def __init__(self, revision):
            pass

        def prepare_request(self, request):
            return {**request, 'execution_environment': {'image_digest': 'sha256:' + 'd' * 64}}

        def __call__(self, request):
            return execute(request)

    monkeypatch.setattr(agent, 'AgentContainer', SyntheticContainer)
    monkeypatch.setattr(runtime, 'ContainerExecutor', SyntheticExecutor)
    bundle = tmp_path / 'frozen'
    freeze_suite(suite, bundle)
    result = run_frozen_suite(bundle, tmp_path / 'results')
    assert all(run['quality_passed'] and run['process_passed'] is None and run['status'] == 'completed' for run in result['runs'])
    summary = summarize_pilot([result['output']])
    group, = summary['groups']
    assert group['process_profile'] == 'issue_resolution' and group['counts']['process_passed'] is None
    assert group['independent_groups'] == 1 and group['repositories'] == ['demo/calc']
