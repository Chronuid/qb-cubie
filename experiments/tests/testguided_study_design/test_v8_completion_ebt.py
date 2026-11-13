"""v8 current evidence, replay and shared-deadline acceptance examples."""

import json

import pytest
from v8_support import BROKEN, FIXED, NODE, Harness, contract, outcome


@pytest.mark.parametrize("kind", ["ImportError", "SyntaxError", "FixtureLookupError", "EnvironmentError"])
def test_v8_25_setup_failure_is_not_behavioral_red(tmp_path, kind):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        h.run(outcome("setup_failure", failed=[(NODE, kind, "setup failed")], executed=0))
        s = h.snapshot()
        return s["qualifications"]["reproduced"], s["completion"]["allowed"], s["test_observations"][-1]["observation"]
    contract(observe, (False, False, "setup_failure"))


def test_v8_26_collection_alone_never_qualifies_completion(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        s = h.snapshot()
        return s["qualifications"], s["completion"]["allowed"]
    contract(observe, ({"reproduced": False, "verified": False}, False))


def test_v8_27_green_original_is_not_manufactured_red(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        h.run(outcome())
        s = h.snapshot()
        return s["qualifications"]["reproduced"], s["completion"]["allowed"], (h.root / "src/calc.py").read_text()
    contract(observe, (False, False, BROKEN))


@pytest.mark.parametrize("path", ["tests/test_calc.py", "conftest.py", "pytest.ini"])
def test_v8_28_test_revision_invalidates_old_red_and_green(tmp_path, path):
    def observe():
        h = Harness(tmp_path)
        red, _, _ = h.repaired()
        h.ok("dev", "request_test_change", case_id="C-1", observed="Current focused test passes.",
             suspected_error="Add explanatory test comment.", evidence_refs=[red["evidence_id"]])
        # Change bytes without weakening the existing assertion.
        h.edit("qa", path, "# REQ-1 coverage\n" + (h.root / path).read_text(), start=1,
               end=len((h.root / path).read_text().splitlines()))
        stale = h.snapshot()
        h.ok("qa", "collect_tests", targets=[NODE])
        h.ok("qa", "finish", delivery=h.suite_delivery())
        h.run(outcome("assertion_failure", failed=[(NODE, "AssertionError", "assert 3 == 4")]), baseline=True)
        h.run()
        baseline, current = h.io.runs[-2:]
        return (stale["qualifications"]["reproduced"], stale["qualifications"]["verified"],
                stale["completion"]["allowed"], baseline["workspace"] != current["workspace"],
                baseline["source"].decode() == BROKEN, current["source"].decode() == FIXED,
                all(baseline[key] == current[key] for key in ("tests", "fixture", "config")))
    contract(observe, (False, False, False, True, True, True, True))


@pytest.mark.parametrize("ebt", ["none", "executed", "evaluated", "checked"])
def test_v8_29_cubie_requires_executed_and_explicitly_checked_evaluation(tmp_path, ebt):
    def observe():
        h = Harness(tmp_path)
        red = h.red()
        h.edit()
        green = h.run(outcome(ebt=ebt))
        regression = h.run(regression=True)
        done = h.ok("dev", "finish", delivery={"summary": "Fix REQ-1.",
                    "evidence_refs": [r["evidence_id"] for r in (red, green, regression)], "open_points": []})
        h.review_diff_ref = done["diff_ref"]
        h.review((red, green, regression))
        return h.snapshot()["completion"]["allowed"]
    contract(observe, ebt == "checked")


@pytest.mark.parametrize("path", ["src/calc.py", "tests/test_calc.py", "environment.json"])
def test_v8_30_changes_after_green_block_review_completion(tmp_path, path):
    def observe():
        h = Harness(tmp_path)
        evidence = h.to_review()
        target = h.root / path
        target.write_text(target.read_text() + ("\n" if path.endswith("json") else "# changed\n"))
        h.review(evidence)
        s = h.snapshot()
        return s["completion"]["allowed"], s["status"] != "submitted"
    contract(observe, (False, True))


def test_v8_31_unsupported_success_claim_cannot_replace_runner_evidence(tmp_path):
    def observe():
        h = Harness(tmp_path)
        before = h.files()
        r = h.send("analysis", "finish", delivery={"verdict": "verified", "reason": "Everything is green.",
                   "requirement_ids": ["REQ-1"], "evidence_refs": [], "open_points": []})
        return r["status"], h.snapshot()["completion"]["allowed"], h.files() == before
    contract(observe, ("rejected", False, True))


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
def test_v8_32_full_repair_replay_uses_real_pytest_in_both_arms(tmp_path, mode):
    def observe():
        h = Harness(tmp_path, mode=mode, real_tests=True)
        evidence = h.to_review()
        assert h.review(evidence)["status"] == "completed"
        s = h.snapshot()
        archive = json.loads((tmp_path / "archive/team.json").read_text())
        observations = s["test_observations"]
        return (s["status"], s["completion"]["allowed"], s["qualifications"],
                [r["observation"] for r in observations],
                (h.root / "src/calc.py").read_text(), archive["private_evaluation_required"],
                all(r["workspace"].is_relative_to(tmp_path) for r in h.io.runs))
    contract(observe, ("submitted", True, {"reproduced": True, "verified": True},
                       ["assertion_failure", "pass", "pass"], FIXED, True, True))


@pytest.mark.parametrize("role", ["qa", "dev"])
def test_v8_33_deadline_during_information_preserves_patch_and_pending_question(tmp_path, role):
    def observe():
        h = Harness(tmp_path)
        if role == "qa":
            h.orient()
        else:
            h.red()
            h.edit()
        h.ok(role, "ask_analysis", question="Does REQ-1 require other inputs?", reason="Need final coverage.")
        deadline = h.snapshot()["budget"]["deadline"]
        h.clock.now = 1800
        h.team.advance()
        s = h.snapshot()
        archive = json.loads((tmp_path / "archive/team.json").read_text())
        patch = (tmp_path / "archive/full.patch").read_text()
        return (s["status"], s["completion"]["allowed"], s["budget"]["deadline"] == deadline,
                bool(archive["open_questions"]), archive["private_evaluation_required"],
                "return value * 2" in patch if role == "dev" else patch == "")
    contract(observe, ("incomplete", False, True, True, True, True))


def test_v8_34_test_run_consumes_the_same_deadline_and_archives_result(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.red()
        h.edit()
        h.clock.now = 1799
        h.io.run_seconds = 2
        h.io.results.append(outcome())
        h.send("dev", "run_tests", targets=[NODE], baseline=False)
        s = h.snapshot()
        saved = json.loads((tmp_path / "archive/team.json").read_text())
        return (s["status"], s["completion"]["allowed"], saved["test_observations"][-1]["observation"],
                (tmp_path / "archive/full.patch").is_file())
    contract(observe, ("incomplete", False, "pass", True))


@pytest.mark.parametrize("seconds", [120, 720, 1799])
def test_v8_35_no_phase_deadline_or_call_limit_ends_task_early(tmp_path, seconds):
    def observe():
        h = Harness(tmp_path)
        # Recovery may change the role; it must not end the shared task.
        for i in range(100):
            h.team.request()
            if h.snapshot()["role"] == "analysis":
                path = f"src/part_{i}.py"
                (h.root / path).write_text(f"VALUE = {i}\n")
                h.ok("analysis", "read_file", path=path, line_start=1, line_end=1)
        h.clock.now = seconds
        h.team.advance()
        s = h.snapshot()
        return s["status"], s["budget"]["deadline"], s["metrics"]["model_calls"] >= 100
    contract(observe, ("running", 1800, True))


def test_v8_36_cached_test_is_not_a_fresh_independent_run(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        first = h.run()
        count = len(h.io.runs)
        cached = h.ok("dev", "run_tests", targets=[NODE], baseline=False)
        no_execution = len(h.io.runs) == count
        fresh = h.run(fresh=True, reason="Investigate suspected flakiness.")
        return (cached["cached"], no_execution, cached["evidence_id"] == first["evidence_id"],
                fresh["evidence_id"] != first["evidence_id"], len(h.io.runs) == count + 1)
    contract(observe, (True, True, True, True, True))


def test_v8_38_missing_agreed_regressions_block_completion(tmp_path):
    def observe():
        h = Harness(tmp_path)
        red = h.red()
        h.edit()
        green = h.run()
        evidence = (red, green)
        done = h.ok("dev", "finish", delivery={"summary": "Fix REQ-1.",
                    "evidence_refs": [r["evidence_id"] for r in evidence], "open_points": []})
        h.review_diff_ref = done["diff_ref"]
        h.review(evidence)
        return h.snapshot()["completion"]["allowed"], h.snapshot()["status"] != "submitted"
    contract(observe, (False, True))


def test_v8_39_requirement_blocking_question_prevents_green_completion(tmp_path):
    def observe():
        h = Harness(tmp_path)
        evidence = h.to_review()
        h.ok("analysis", "update_context", context=h.context(unknowns=[{
            "question": "Does the public requirement contain an unresolved exception?", "blocking": True,
        }]))
        h.review(evidence)
        return h.snapshot()["completion"]["allowed"], h.snapshot()["status"] != "submitted"
    contract(observe, (False, True))
