"""Red acceptance contracts for AGENTENDESIGN-V6.md, not a v6 implementation.

Imports of the missing v6 API are delayed until EBT executes its target.
Each pytest node maps to a catalogue entry in V6_CASES.md. No xfails or skips.
"""

import copy

import pytest
from v6_support import CASE, GUIDES, ISSUE, NODE, Harness, contract, outcome


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
def test_a01_analysis_starts_and_qa_receives_versioned_context(tmp_path, mode):
    def observe():
        h = Harness(tmp_path, mode=mode)
        initial = h.snapshot()
        h.orient()
        state = h.snapshot()
        message = state["messages"][-1]
        return (initial["role"], initial["state"], state["role"], state["state"],
                message["type"], message["context_revision"] == state["context_revision"],
                message["versions"] == state["versions"], state["active_job"]["id"])
    contract(observe, ("analysis", "orient", "qa", "specify", "context_ready", True, True, "J-QA"))


def test_a02_suite_handoff_preserves_cases_targets_and_runner_ids(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        state = h.snapshot()
        message = state["messages"][-1]
        return (state["role"], state["state"], message["type"],
                message["payload"]["targets"], state["cases"]["C-1"]["requirement_id"],
                bool(message["id"]), message["sender"], message["recipient"],
                len({m["id"] for m in state["messages"]}) == len(state["messages"]))
    contract(observe, ("dev", "reproduce", "suite_ready", [NODE], "REQ-1", True, "qa", "dev", True))


@pytest.mark.parametrize("role,path,action", [
    ("analysis", "src/new.py", "create_source_file"),
    ("analysis", "tests/new.py", "create_test_file"),
    ("qa", "src/new.py", "create_source_file"),
    ("dev", "tests/new.py", "create_test_file"),
    ("dev", "conftest.py", "create_source_file"),
    ("dev", "pytest.ini", "create_source_file"),
    ("dev", "tests/test_calc.py", "delete_source_file"),
], ids=["analysis-source", "analysis-tests", "qa-source", "dev-tests", "dev-fixture", "dev-config", "dev-delete-test"])
def test_a03_dispatch_rejects_cross_role_mutations_before_io(tmp_path, role, path, action):
    def observe():
        h = Harness(tmp_path)
        if role == "qa":
            h.orient()
        elif role == "dev":
            h.suite()
        before, calls = h.files(), len(h.io.calls)
        response = h.send(role, action, path=path, content="pass\n", reason="Try forbidden mutation")
        return response["status"], h.files() == before, len(h.io.calls) == calls
    contract(observe, ("rejected", True, True))


@pytest.mark.parametrize("path", ["../escape.py", "absolute", "tests/../src/new.py", "alias/new.py"])
def test_a03_canonical_paths_and_symlinks_cannot_bypass_manifest(tmp_path, path):
    def observe():
        h = Harness(tmp_path)
        h.orient()
        (h.root / "alias").symlink_to(h.root / "src", target_is_directory=True)
        before, calls = h.files(), len(h.io.calls)
        candidate = str(tmp_path / "outside.py") if path == "absolute" else path
        response = h.send("qa", "create_test_file", path=candidate, content="pass\n", reason="Path probe")
        return response["status"], h.files() == before, len(h.io.calls) == calls
    contract(observe, ("rejected", True, True))


@pytest.mark.parametrize("requester", ["qa", "dev"])
def test_a04_information_roundtrip_resumes_same_job_and_role(tmp_path, requester):
    def observe():
        h = Harness(tmp_path)
        h.orient() if requester == "qa" else h.suite()
        before = h.snapshot()
        response = h.ok(requester, "ask_analysis", question="Where is double defined?", refs=["issue:REQ-1"])
        suspended = h.snapshot()
        h.ok("analysis", "answer_question", reply_to=response["message_id"],
             answer="src/calc.py:1", refs=["issue:REQ-1"], unknown=False)
        after = h.snapshot()
        message = after["messages"][-1]
        return (suspended["role"], suspended["state"], after["role"],
                before["active_job"]["id"] == after["active_job"]["id"],
                before["state"] == after["state"], message["reply_to"] == response["message_id"],
                after["metrics"]["model_calls"] == before["metrics"]["model_calls"])
    contract(observe, ("analysis", "answer_information", requester, True, True, True, True))


def test_a04_unknown_answer_preserves_dependent_open_question(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        request = h.ok("dev", "ask_analysis", question="Which unspecified compatibility behavior applies?", refs=[])
        h.ok("analysis", "answer_question", reply_to=request["message_id"],
             answer="Not specified by the public task", refs=[], unknown=True)
        return bool(h.snapshot()["open_questions"]), h.snapshot()["completion"]["allowed"]
    contract(observe, (True, False))


def test_a05_test_change_request_is_addressed_to_qa_with_evidence(tmp_path):
    def observe():
        h = Harness(tmp_path)
        red = h.red()
        response = h.ok("dev", "request_test_change", case_ids=["C-1"], requirement_id="REQ-1",
                        evidence_ids=[red["evidence_id"]], reason="Check the oracle against the issue")
        state = h.snapshot()
        message = state["messages"][-1]
        return (state["role"], state["state"], message["type"], message["recipient"],
                red["evidence_id"] in message["evidence_refs"], bool(response["message_id"]))
    contract(observe, ("qa", "revise_tests", "test_change_request", "qa", True, True))


def test_a06_qa_rejects_unsupported_weakening_and_escalates_dissent(tmp_path):
    def observe():
        h = Harness(tmp_path)
        red = h.red()
        request = h.ok("dev", "request_test_change", case_ids=["C-1"], requirement_id="REQ-1",
                       evidence_ids=[red["evidence_id"]], reason="Change expected 4 to observed 3")
        before = copy.deepcopy(h.snapshot()["cases"]["C-1"])
        h.ok("qa", "respond_test_change", reply_to=request["message_id"], accepted=False,
             reason="REQ-1 requires 4; observed output cannot justify 3", refs=["issue:REQ-1"], unresolved=True)
        state = h.snapshot()
        return state["cases"]["C-1"] == before, state["role"], state["completion"]["allowed"], bool(state["pending_requests"])
    contract(observe, (True, "analysis", False, True))


@pytest.mark.parametrize("path", ["tests/test_calc.py", "conftest.py", "pytest.ini"])
def test_a07_revision_invalidates_red_and_requires_final_suite_baseline(tmp_path, path):
    def observe():
        h = Harness(tmp_path)
        red = h.red()
        original = h.snapshot()["versions"]["production"]
        original_bytes = (h.root / "src/calc.py").read_bytes()
        h.edit()
        request = h.ok("dev", "request_test_change", case_ids=["C-1"], requirement_id="REQ-1",
                       evidence_ids=[red["evidence_id"]], reason="Add a justified boundary case")
        read = h.ok("qa", "read_file", path=path, start=1)
        h.ok("qa", "replace_region", handle=read["handle"],
             new_text="# revised public test setup\n" + read["text"], reason="REQ-1")
        invalidated = not h.snapshot()["qualifications"]["reproduced"]
        h.ok("qa", "respond_test_change", reply_to=request["message_id"], accepted=True,
             reason="Boundary coverage extended", refs=["issue:REQ-1"], unresolved=False)
        baseline = h.run(outcome("assertion_failure", failed=[(NODE, "AssertionError", "assert 3 == 4")]), baseline=True)
        current = h.run()
        state = h.snapshot()
        return (invalidated, baseline["versions"]["production"] == original,
                baseline["versions"]["tests"] == current["versions"]["tests"],
                current["versions"]["production"] == state["versions"]["production"],
                baseline["versions"]["production"] != current["versions"]["production"],
                h.io.runs[-2]["workspace"] != h.io.runs[-1]["workspace"],
                h.io.runs[-2]["source"] == original_bytes,
                all(h.io.runs[-2][key] == h.io.runs[-1][key] for key in ("tests", "fixture", "config")))
    contract(observe, (True, True, True, True, True, True, True, True))


@pytest.mark.parametrize("path", ["src/calc.py", "environment.json"])
def test_a08_change_after_review_invalidates_current_completion(tmp_path, path):
    def observe():
        h = Harness(tmp_path)
        h.verified()
        before = h.snapshot()["completion"]["allowed"]
        # An external workspace/environment mutation must be noticed at dispatch.
        with (h.root / path).open("a") as stream:
            stream.write("\n")
        response = h.send("analysis", "submit", reason="Try stale review")
        state = h.snapshot()
        return before, response["status"], state["completion"]["allowed"], state["qualifications"]["verified"]
    contract(observe, (True, "rejected", False, False))


def test_a09_stale_handle_requires_reread_before_one_new_edit(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.red()
        read = h.ok("dev", "read_file", path="src/calc.py", start=2, end=2)
        path = h.root / "src/calc.py"
        path.write_text(path.read_text() + "# external change\n")
        before, calls = path.read_bytes(), len(h.io.calls)
        first = h.send("dev", "replace_region", handle=read["handle"], new_text="    return 4\n", reason="REQ-1")
        second = h.send("dev", "replace_region", handle=read["handle"], new_text="    return 4\n", reason="retry")
        unchanged = path.read_bytes() == before and len(h.io.calls) == calls
        h.edit()
        return first["status"], second["status"], unchanged, "return value * 2\n" in path.read_text()
    contract(observe, ("rejected", "rejected", True, True))


def test_a09_invalid_python_is_rejected_atomically(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.red()
        read = h.ok("dev", "read_file", path="src/calc.py", start=2, end=2)
        before, calls = h.files(), len(h.io.calls)
        response = h.send("dev", "replace_region", handle=read["handle"], new_text="    return (\n", reason="REQ-1")
        return response["status"], h.files() == before, len(h.io.calls) == calls
    contract(observe, ("rejected", True, True))


@pytest.mark.parametrize("usage,allowed", [("none", False), ("executed", False), ("evaluated", False), ("checked", True)])
def test_a10_cubie_execution_evaluation_and_explicit_check_are_distinct(tmp_path, usage, allowed):
    def observe():
        h = Harness(tmp_path)
        h.red()
        h.edit()
        h.run(outcome(ebt=usage))
        h.run(outcome(ebt=usage), purpose="regression")
        h.ok("dev", "publish_implementation", requirement_ids=["REQ-1"], open_points=[])
        h.send("analysis", "verify_completion")
        return h.snapshot()["completion"]["allowed"]
    contract(observe, allowed)


@pytest.mark.parametrize("result", [
    {"status": "completed", "observation": "collected", "collection_only": True, "collected": 1},
    outcome("invalid_test_run", executed=0),
    outcome("pass", skipped=1, executed=0),
    {**outcome("pass", executed=0), "xfail": 1},
    outcome("invalid_test_run", failed=[(NODE, "ImportError", "src/calc.py: invalid import")], executed=0),
], ids=["collection-only", "zero-tests", "skip", "xfail", "production-import"])
def test_a12_non_execution_never_qualifies_as_behavioral_red_or_green(tmp_path, result):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        h.run(result)
        state = h.snapshot()
        return state["qualifications"]["reproduced"], state["qualifications"]["verified"], state["completion"]["allowed"]
    contract(observe, (False, False, False))


@pytest.mark.parametrize("changed,allowed", [(False, True), (True, False)])
def test_a13_baseline_identity_matters_even_when_failure_counts_match(tmp_path, changed, allowed):
    def observe():
        h = Harness(tmp_path)
        h.red()
        old = ("tests/test_old.py::test_old", "TypeError", "known snapshot failure")
        new = (NODE, "AssertionError", "new regression") if changed else old
        h.run(outcome("test_failure", failed=[old]), baseline=True, purpose="regression")
        h.edit()
        h.run()
        h.run(outcome("test_failure", failed=[new]), purpose="regression")
        h.ok("dev", "publish_implementation", requirement_ids=["REQ-1"], open_points=[])
        h.send("analysis", "verify_completion")
        state = h.snapshot()
        return state["completion"]["allowed"], state["completion"]["status"]
    contract(observe, (allowed, "verified_with_baseline_failures" if allowed else "incomplete"))


@pytest.mark.parametrize("limit", ["wall", "models", "tools"])
def test_a14_only_wall_budget_limits_role_changes(tmp_path, limit):
    def observe():
        h = Harness(tmp_path, extra_sources=100)
        h.suite()
        if limit == "wall":
            h.clock.now = 900
            h.send("dev", "read_file", path="src/calc.py", start=1)
        elif limit == "models":
            # Requests count; deterministic handoffs do not consume inference.
            for _ in range(49):
                h.team.request()
        else:
            for index in range(97):
                h.send("dev", "read_file", path=f"src/source_{index}.py", start=1)
        state = h.snapshot()
        return (state["status"], state["reason"], state["completion"]["status"],
                state["metrics"]["model_calls"] > 48, state["metrics"]["tool_calls"] > 96)
    contract(observe, ("incomplete" if limit == "wall" else "running",
                       "wall_budget" if limit == "wall" else None, "incomplete",
                       limit == "models", limit == "tools"))


@pytest.mark.parametrize("boundary", ["seconds", "model-calls"])
def test_a14_no_early_reserve_shortens_work(tmp_path, boundary):
    def observe():
        h = Harness(tmp_path)
        h.red()
        if boundary == "seconds":
            h.clock.now = 720
        else:
            for _ in range(42):
                h.team.request()
        response = h.send("dev", "request_test_change", case_ids=["C-1"], requirement_id="REQ-1",
                          evidence_ids=[], reason="Start another repair round")
        verified = h.run()
        return response["status"], verified["status"], h.snapshot()["budget"]["reserve_active"], h.snapshot()["budget"]["deadline"]
    contract(observe, ("rejected", "completed", False, 900))


def test_a14_rephrased_notes_do_not_reset_stagnation(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        for index in range(9):
            h.send("dev", "read_file", path="src/calc.py", start=1, note={"hypothesis": f"Rephrased note {index}"})
        state = h.snapshot()
        return state["status"], state["metrics"]["recoveries"], state["completion"]["allowed"]
    contract(observe, ("running", 2, False))


@pytest.mark.parametrize("role", ["qa", "dev"])
def test_a15_only_analysis_can_submit_even_after_current_green(tmp_path, role):
    def observe():
        h = Harness(tmp_path)
        h.verified()
        response = h.send(role, "submit", reason="Claim success")
        return response["status"], h.snapshot()["status"] != "submitted"
    contract(observe, ("rejected", True))


def test_a15_valid_analysis_submission_records_verified_green(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.verified()
        response = h.ok("analysis", "submit", reason="REQ-1 verified with current focused and regression evidence")
        state = h.snapshot()
        return response["status"], state["status"], state["completion"]["status"]
    contract(observe, ("completed", "submitted", "verified_green"))


def test_a15_analysis_claim_without_execution_cannot_open_completion_gate(tmp_path):
    def observe():
        h = Harness(tmp_path)
        response = h.send("analysis", "submit", reason="Everything is green; trust this note")
        return response["status"], h.snapshot()["completion"]["allowed"]
    contract(observe, ("rejected", False))


def test_a16_green_original_is_visible_and_does_not_manufacture_reproduction(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        h.run()
        state = h.snapshot()
        return (state["qualifications"]["reproduced"], state["completion"]["allowed"],
                state["metrics"]["first_production_change_call"], bool(state["open_questions"]))
    contract(observe, (False, False, None, True))


def test_a17_both_arms_share_permissions_policy_and_roles(tmp_path):
    def observe():
        teams = [Harness(tmp_path / mode, mode=mode) for mode in ("pytest", "cubie")]
        snapshots = [h.snapshot() for h in teams]
        policies = [state["policy"] for state in snapshots]
        schemas = [h.team.request()["schema"] for h in teams]
        return (policies[0] == policies[1], schemas[0] == schemas[1],
                snapshots[0]["roles"] == snapshots[1]["roles"] == ["analysis", "qa", "dev"])
    contract(observe, (True, True, True))


@pytest.mark.parametrize("cause", ["deadline", "invalid-output"])
def test_a18_incomplete_exit_preserves_patch_and_raw_evidence(tmp_path, cause):
    def observe():
        h = Harness(tmp_path)
        h.red()
        h.edit()
        if cause == "deadline":
            h.clock.now = 900
            h.team.request()
        else:
            for index in range(2):
                h.team.request()
                h.team.reject_output(raw=f"invalid-json-{index}", usage={"output_tokens": 8192})
        state = h.snapshot()
        archive = tmp_path / "archive"
        raw = "\n".join(path.read_text() for path in archive.rglob("*.json"))
        return (state["status"], state["completion"]["status"],
                bool((archive / "full.patch").read_text()), (archive / "team.json").exists(),
                state["private_evaluation_required"],
                state["metrics"]["output_repairs"] == (2 if cause == "invalid-output" else 0),
                cause != "invalid-output" or all(f"invalid-json-{index}" in raw for index in range(2)))
    contract(observe, ("incomplete" if cause == "deadline" else "running", "incomplete", True, True, True, True, True))


@pytest.mark.parametrize("field", ["case_id", "requirement_id", "reason_ref", "target", "expected", "pytest_node"])
def test_c01_case_structure_is_validated_without_inventing_an_oracle(tmp_path, field):
    def observe():
        h = Harness(tmp_path)
        h.orient()
        case = copy.deepcopy(CASE)
        del case[field]
        before = h.files()
        response = h.send("qa", "create_case", case=case)
        return response["status"], h.snapshot()["cases"], h.files() == before
    contract(observe, ("rejected", {}, True))


@pytest.mark.parametrize("role", ["analysis", "qa", "dev"])
def test_c02_private_paths_are_unreadable_to_every_role(tmp_path, role):
    def observe():
        h = Harness(tmp_path)
        if role == "qa":
            h.orient()
        elif role == "dev":
            h.suite()
        private = h.root / "evaluator/gold.py"
        private.parent.mkdir()
        private.write_text("PRIVATE_REFERENCE_SENTINEL = 42\n")
        calls = len(h.io.calls)
        response = h.send(role, "read_file", path="evaluator/gold.py", start=1)
        return response["status"], len(h.io.calls) == calls, "PRIVATE_REFERENCE_SENTINEL" not in str(response)
    contract(observe, ("rejected", True, True))


@pytest.mark.parametrize("role", ["analysis", "qa", "dev"])
def test_c03_actual_role_request_preserves_mandatory_context(tmp_path, role):
    def observe():
        h = Harness(tmp_path)
        if role == "qa":
            h.orient()
        elif role == "dev":
            h.suite()
        request = h.team.request()
        text = "\n".join(message["content"] for message in request["messages"])
        tools = {entry["properties"]["action"]["const"] for entry in request["schema"]["oneOf"]}
        required = {"analysis": "publish_context", "qa": "create_case", "dev": "run_tests"}
        forbidden = {"analysis": "replace_region", "qa": "run_tests", "dev": "revise_case"}
        return ISSUE in text, GUIDES["cubie"] in text, required[role] in tools, forbidden[role] not in tools
    contract(observe, (True, True, True, True))


def test_c03_oversized_mandatory_context_fails_explicitly(tmp_path):
    def observe():
        h = Harness(tmp_path, context_bytes=16)
        h.team.request()
        state = h.snapshot()
        return state["status"], state["reason"], state["metrics"]["model_calls"]
    contract(observe, ("incomplete", "context_error", 0))


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
def test_c04_v6_is_an_explicitly_supported_design_version(mode):
    def observe():
        from testguided_study.design import default_design
        from testguided_study.iteration import compose

        design = default_design(mode, GUIDES, version=6)
        return compose(design["core"], design["specialization"]) == design
    contract(observe, True)
