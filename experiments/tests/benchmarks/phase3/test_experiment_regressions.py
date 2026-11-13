"""Acceptance cases derived from EXPERIMENT_Benchmark-10-3, without a model."""

from pathlib import Path

import pytest

from ..contracts import accepted
from .conftest import cli, configure_agent, read_json, write_suite

EBT_TESTS = '''import pytest
from qb_cubie import EBT, WorldState
from shipping import fee


def test_boundary():
    result = EBT(target=fee, pre=WorldState(args=(5000,)),
                 post=WorldState(returns=0), reporter=None).run()
    assert result.evaluation is True
'''
EXCEPTION_TESTS = '''import pytest
from shipping import fee


def test_negative():
    with pytest.raises(ValueError):
        fee(-1)
'''
SOLUTION = '''def fee(subtotal):
    if subtotal < 0:
        raise ValueError("negative subtotal")
    return 0 if subtotal >= 5000 else 499
'''


def experiment_run(external, public_api, tests, mode="reference"):
    """Submit actual frozen tests through the existing external JSONL peer."""
    peer = external / "agents/jsonl_agent.py"
    source = peer.read_text(encoding="utf-8")
    start = source.index("TESTS = ")
    end = source.index("\n\ndef emit", start)
    peer.write_text(source[:start] + f"TESTS = {tests!r}\nSOLUTION = {SOLUTION!r}\n"
                    + source[end:], encoding="utf-8")
    scenario = external / "scenarios/fee-initial"
    (scenario / "task.md").write_text(
        "Implement shipping.fee(subtotal): integer cents, free from 5000, otherwise 499. "
        "Negative subtotals must raise ValueError. Submit tests before implementation.\n",
        encoding="utf-8")
    (scenario / "evaluator/solution.py.txt").write_text(SOLUTION, encoding="utf-8")
    acceptance = scenario / "evaluator/acceptance.py.txt"
    acceptance.write_text('import pytest\nfrom shipping import fee\n\n'
                          '@pytest.mark.parametrize("subtotal,expected", '
                          '[(-1, None), (0, 499), (4999, 499), (5000, 0), (9000, 0)])\n'
                          'def test_fee(subtotal, expected):\n'
                          '    if subtotal < 0:\n'
                          '        with pytest.raises(ValueError):\n'
                          '            fee(subtotal)\n'
                          '    else:\n'
                          '        assert fee(subtotal) == expected\n', encoding="utf-8")
    configure_agent(external, mode)
    result = accepted(public_api("run_suite"), write_suite(external, 'ids = ["shop/fee-initial"]'),
                      expected=lambda r: len(r["runs"]) == 1)
    return result, result["runs"][0]


def observation(result, run, phase):
    entry = next(p for p in run["phases"] if p["phase"] == phase)
    return read_json(Path(result["output"]) / entry["evidence"][0])


@pytest.mark.parametrize("tests", [EXCEPTION_TESTS, EBT_TESTS + EXCEPTION_TESTS],
                         ids=["missing-exception-only", "ebt-and-missing-exception"])
def test_missing_expected_exception_is_business_red(external, public_api, tests):
    result, run = experiment_run(external, public_api, tests)
    red = observation(result, run, "red")
    assert any("DID NOT RAISE" in f["message"] for c in red["cases"] for f in c["failures"])
    assert run["status"] == "completed" and run["quality_passed"] is True
    assert [p["test_outcome"] for p in run["phases"]][2:] == ["passed", "passed"]
    assert len({p["test_tree_sha256"] for p in run["phases"]}) == 1
    assert red["test_outcome"] == "assertion_failure"
    assert run["process_passed"] is True and run["process_reason"] is None


@pytest.mark.parametrize("extra,outcome", [
    ('\ndef test_runtime():\n    if fee(0) == -1:\n        raise RuntimeError("AssertionError: DID NOT RAISE")\n', "test_error"),
    ('\n@pytest.fixture\ndef broken():\n    if fee(0) == -1:\n        raise RuntimeError("setup failed")\n\ndef test_setup(broken):\n    pass\n', "test_error"),
    ('\nimport experiment_missing_dependency\n', "import_error"),
    ('\ndef invalid syntax\n', "import_error"),
], ids=["runtime-with-misleading-text", "fixture-setup", "import", "syntax"])
def test_real_test_errors_override_business_failures(external, public_api, extra, outcome):
    result, run = experiment_run(external, public_api, EBT_TESTS + EXCEPTION_TESTS + extra)
    assert run["status"] == "completed" and run["quality_passed"] is True
    assert observation(result, run, "red")["test_outcome"] == outcome
    assert run["process_passed"] is False and run["process_reason"]


def test_wrong_agent_oracle_stays_a_process_failure_despite_correct_product(external, public_api):
    tests = EBT_TESTS + '\n\ndef test_wrong_oracle():\n    assert fee(0) == -1\n'
    _, run = experiment_run(external, public_api, tests)
    assert run["status"] == "completed" and run["quality_passed"] is True
    assert run["process_passed"] is False and run["process_reason"]
    assert [p["test_outcome"] for p in run["phases"]][1:] == [
        "assertion_failure", "assertion_failure", "assertion_failure"]


def test_report_names_quality_and_process_separately(external, public_api):
    result, run = experiment_run(external, public_api, EBT_TESTS, "early_implementation")
    assert run["quality_passed"] is True and run["process_passed"] is False
    report = (Path(result["output"]) / "report.md").read_text(encoding="utf-8").lower()
    assert "quality_passed: true" in report
    assert "process_passed: false" in report


def test_text_comparison_exposes_status_quality_and_process(external, public_api):
    before, _ = experiment_run(external, public_api, EBT_TESTS)
    after, _ = experiment_run(external, public_api, EBT_TESTS, "early_implementation")
    comparison = accepted(public_api("compare_runs"), before["output"], after["output"],
                          expected=lambda r: r["scope"] == "full" and len(r["pairs"]) == 1)
    pair = comparison["pairs"][0]
    assert pair["before"]["process_passed"] is True
    assert pair["after"]["process_passed"] is False
    output = cli("compare", before["output"], after["output"], cwd=external.parent)
    assert output.returncode == 0
    for field in ("completed", "quality_passed", "process_passed", "true", "false"):
        assert field in output.stdout.lower()


def test_cli_exit_zero_does_not_hide_process_failure(external, public_api):
    experiment_run(external, public_api, EBT_TESTS, "early_implementation")
    output = cli("run", "--suite", external / "sets/team.toml", cwd=external.parent)
    assert output.returncode == 0
    assert "quality_passed=True" in output.stdout
    assert "process_passed=False" in output.stdout
