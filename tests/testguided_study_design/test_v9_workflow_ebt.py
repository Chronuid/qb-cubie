"""Current-suite qualification, review, arm parity and the shared deadline."""

import pytest
from v9_support import (
    BROKEN,
    FIXED,
    NODE,
    REGRESSION,
    Harness,
    contract,
    outcome,
    prompt,
)


@pytest.mark.parametrize("kind", ["ImportError", "SyntaxError", "FixtureLookupError", "EnvironmentError"])
def test_v9_26_setup_errors_never_count_as_behavioral_red(tmp_path, kind):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        h.run(outcome("setup_failure", failed=[(NODE, kind, "SETUP_DETAIL_SENTINEL")], executed=0))
        s = h.snapshot()
        text = prompt(h.team.request())
        return s["qualifications"]["reproduced"], s["completion"]["allowed"], "SETUP_DETAIL_SENTINEL" in text
    contract(observe, (False, False, True))


def test_v9_27_collection_and_unbacked_model_success_cannot_qualify(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        before = h.snapshot()
        # Even a directly dispatched forged review cannot bypass active-role checks.
        result = h.send("analysis", "finish", verdict="verified", notes="All tests passed.")
        return (before["qualifications"]["reproduced"], before["qualifications"]["verified"],
                result["status"], h.snapshot()["completion"]["allowed"])
    contract(observe, (False, False, "rejected", False))


@pytest.mark.parametrize("path", ["tests/test_calc.py", "conftest.py", "pytest.ini"])
def test_v9_28_revision_requires_final_suite_against_original_and_current_production(tmp_path, path):
    def observe():
        h = Harness(tmp_path)
        red, _, _ = h.repaired()
        h.ok("dev", "request_test_change", case=NODE, reason="Add a requirement explanation.",
             evidence=[red["evidence_id"]])
        h.edit("qa", path, "# REQ-1 rationale\n" + (h.root / path).read_text())
        stale = h.snapshot()
        h.deliver_suite()
        h.run(outcome("assertion_failure", failed=[(NODE, "AssertionError", "assert 3 == 4")]), baseline=True)
        h.run()
        original, repaired = h.io.runs[-2:]
        return (stale["qualifications"]["reproduced"], stale["qualifications"]["verified"],
                stale["completion"]["allowed"], original["workspace"] != repaired["workspace"],
                original["source"].decode() == BROKEN, repaired["source"].decode() == FIXED,
                all(original[k] == repaired[k] for k in ("tests", "fixture", "config")))
    contract(observe, (False, False, False, True, True, True, True))


@pytest.mark.parametrize("path", ["src/calc.py", "tests/test_calc.py", "environment.json"])
def test_v9_29_change_after_green_blocks_old_review(tmp_path, path):
    def observe():
        h = Harness(tmp_path)
        evidence = h.to_review()
        h.write(path, (h.root / path).read_text() + "\n")
        h.review(evidence)
        s = h.snapshot()
        return s["completion"]["allowed"], s["status"] != "submitted"
    contract(observe, (False, True))


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
@pytest.mark.parametrize("ebt", ["none", "executed", "evaluated", "checked"])
def test_v9_30_cubie_checks_real_case_usage_while_pytest_needs_no_ebt(tmp_path, mode, ebt):
    def observe():
        h = Harness(tmp_path, mode=mode)
        red = h.red()
        h.edit()
        green = h.run(outcome(ebt=ebt))
        regression = h.run(regression=True)
        result = h.ok("dev", "finish", notes="Patch ready for final review.")
        h.diff_ref = result["diff_ref"]
        h.review((red, green, regression))
        return h.snapshot()["completion"]["allowed"]
    contract(observe, mode == "pytest" or ebt == "checked")


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
def test_v9_31_complete_replay_runs_real_red_green_and_regression(tmp_path, mode):
    def observe():
        h = Harness(tmp_path, mode=mode, real_tests=True)
        evidence = h.to_review()
        result = h.review(evidence)
        s = h.snapshot()
        return (result["status"], s["status"], s["completion"]["allowed"],
                [r["observation"] for r in s["test_observations"]],
                (h.root / "src/calc.py").read_text(), h.archive()["private_evaluation_required"],
                all(run["workspace"].is_relative_to(tmp_path) for run in h.io.runs))
    contract(observe, ("completed", "submitted", True, ["assertion_failure", "pass", "pass"], FIXED, True, True))


def test_v9_32_valid_expectation_is_not_weakened_on_dev_request(tmp_path):
    def observe():
        h = Harness(tmp_path)
        red = h.red()
        original_test = (h.root / "tests/test_calc.py").read_bytes()
        h.ok("dev", "request_test_change", case=NODE, reason="Change expected 4 to 3 because the program returns 3.",
             evidence=[red["evidence_id"]])
        qa_prompt = prompt(h.team.request())
        h.ok("qa", "finish", test_targets=[NODE], regressions=[REGRESSION],
             notes="Request rejected: REQ-1 requires 4. Returning 3 is the production defect.")
        dev_prompt = prompt(h.team.request())
        return ("Change expected 4 to 3" in qa_prompt, h.snapshot()["role"],
                "Request rejected" in dev_prompt,
                (h.root / "tests/test_calc.py").read_bytes() == original_test,
                h.snapshot()["completion"]["allowed"])
    contract(observe, (True, "dev", True, True, False))


@pytest.mark.parametrize("same_identity", [True, False])
def test_v9_33_baseline_errors_are_compared_by_identity_not_count(tmp_path, same_identity):
    def observe():
        h = Harness(tmp_path)
        old = (REGRESSION, "ImportError", "No module named optional_dependency")
        h.suite()
        h.run(outcome("setup_failure", failed=[old], executed=0), baseline=True, regression=True)
        red = h.run(outcome("assertion_failure", failed=[(NODE, "AssertionError", "assert 3 == 4")]))
        h.edit()
        green = h.run()
        failure = old if same_identity else (REGRESSION, "AssertionError", "assert 1 == 2")
        regression = h.run(outcome("setup_failure" if same_identity else "assertion_failure",
                                   failed=[failure], executed=0 if same_identity else 1), regression=True)
        delivered = h.ok("dev", "finish", notes="Focus passes; compare regression identity to environment baseline.")
        h.diff_ref = delivered["diff_ref"]
        h.review((red, green, regression))
        s = h.snapshot()
        if same_identity:
            return s["completion"]["allowed"], s["verification_status"] == "verified_with_baseline_failures"
        return not s["completion"]["allowed"], s["status"] != "submitted"
    contract(observe, (True, True))


def test_v9_34_missing_regression_execution_gets_a_dev_rework_order(tmp_path):
    def observe():
        h = Harness(tmp_path)
        red = h.red()
        h.edit()
        green = h.run()
        done = h.ok("dev", "finish", notes="Only focus has been rerun.")
        h.diff_ref = done["diff_ref"]
        h.review((red, green))
        blocked = not h.snapshot()["completion"]["allowed"]
        h.ok("analysis", "finish", verdict="rework", next_role="dev", notes="Run the agreed regression target.")
        return blocked, h.snapshot()["role"], "Run the agreed regression target" in prompt(h.team.request())
    contract(observe, (True, "dev", True))


@pytest.mark.parametrize("phase", ["research", "information", "verification"])
@pytest.mark.parametrize("mode", ["pytest", "cubie"])
def test_v9_35_deadline_preserves_evidence_patch_and_open_questions(tmp_path, phase, mode):
    def observe():
        h = Harness(tmp_path, mode=mode)
        evidence = h.read()
        if phase != "research":
            h.red()
            h.edit()
        if phase == "information":
            h.ok("dev", "ask_analysis", question="UNRESOLVED_AT_DEADLINE", reason="Need final oracle scope.")
        if phase == "verification":
            h.clock.now = 1799
            h.io.run_seconds = 2
            h.io.results.append(outcome())
            h.send("dev", "run_tests", targets=[NODE], baseline=False)
        else:
            h.clock.now = 1800
            h.team.advance()
        s = h.snapshot()
        archive = h.archive()
        patch = (tmp_path / "archive/full.patch").read_text()
        transactions = "\n".join(p.read_text() for p in (tmp_path / "transactions").glob("*.json"))
        return (s["status"], s["completion"]["allowed"], s["budget"]["deadline"],
                evidence["evidence_id"] in transactions, archive["private_evaluation_required"],
                bool(archive["open_questions"]) if phase == "information" else True,
                "return value * 2" in patch if phase != "research" else patch == "",
                archive["test_observations"][-1]["observation"] == "pass" if phase == "verification" else True)
    contract(observe, ("incomplete", False, 1800, True, True, True, True, True))


@pytest.mark.parametrize("seconds", [120, 720, 1799])
def test_v9_36_call_counts_and_former_phase_limits_do_not_end_shared_task(tmp_path, seconds):
    def observe():
        h = Harness(tmp_path)
        for i in range(110):
            h.team.request()
            h.write(f"src/distinct_{i}.py", f"VALUE = {i}\n")
            h.read(path=f"src/distinct_{i}.py", end=1)
        h.clock.now = seconds
        h.team.advance()
        s = h.snapshot()
        return s["status"], s["budget"]["deadline"], s["metrics"]["model_calls"] >= 110
    contract(observe, ("running", 1800, True))


def test_v9_37_green_original_remains_unreproduced_without_an_explicit_exception(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.write("src/calc.py", FIXED)
        h.suite()
        h.run()
        s = h.snapshot()
        return s["qualifications"]["reproduced"], s["completion"]["allowed"], (h.root / "src/calc.py").read_text()
    contract(observe, (False, False, FIXED))


@pytest.mark.parametrize("targets", [["tests/test_absent.py::test_missing"], [NODE, "tests/test_absent.py::test_missing"]])
def test_v9_38_qa_cannot_deliver_uncollected_targets(tmp_path, targets):
    def observe():
        h = Harness(tmp_path)
        h.orient()
        h.ok("qa", "collect_tests", targets=[NODE])
        before = h.snapshot()["active_job"]
        result = h.send("qa", "finish", test_targets=targets, regressions=[REGRESSION], notes="REQ-1: input 2 expects 4.")
        return result["status"], h.snapshot()["role"], h.snapshot()["active_job"] == before
    contract(observe, ("rejected", "qa", True))


def test_v9_39_unresolved_oracle_blocks_otherwise_green_review(tmp_path):
    def observe():
        h = Harness(tmp_path)
        evidence = h.to_review()
        h.ok("analysis", "finish", verdict="rework", next_role="dev", notes="Clarify coverage of negative values.")
        h.ok("dev", "ask_analysis", question="BLOCKING_ORACLE: are negative values required?", reason="Final coverage ambiguity.")
        h.ok("analysis", "finish", notes="Unspecified in available sources.", unresolved=True)
        result = h.ok("dev", "finish", notes="Existing focused results still pass; question unresolved.")
        h.diff_ref = result["diff_ref"]
        h.review(evidence)
        s = h.snapshot()
        return s["completion"]["allowed"], bool(s["open_questions"]), s["status"] != "submitted"
    contract(observe, (False, True, True))
