"""v8 role, handoff and context examples. Intentionally red until v8 exists."""

import copy
import json

import pytest
from v8_support import (
    ALLOWED,
    CASE,
    GUIDES,
    ISSUE,
    NODE,
    Harness,
    contract,
    messages,
    tool_names,
)


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
@pytest.mark.parametrize("role", ["analysis", "qa", "dev"])
def test_v8_01_role_request_has_only_its_tools_and_qa_guide(tmp_path, mode, role):
    def observe():
        h = Harness(tmp_path, mode=mode)
        if role == "qa":
            h.orient()
        elif role == "dev":
            h.suite()
        request = h.team.request()
        text = messages(request)
        return (tool_names(request) == ALLOWED[role], ISSUE in text,
                GUIDES[mode] in text, GUIDES["cubie" if mode == "pytest" else "pytest"] in text,
                all(key not in text for key in ("PRIVATE_SENTINEL", "controller_tool_calls", "policyflags")),
                "src" in text and "python" in text.lower())
    contract(observe, (True, True, role == "qa", False, True, True))


@pytest.mark.parametrize("variant", ["valid", "missing", "unknown-ref", "stale-ref"])
def test_v8_02_finish_context_is_atomic_and_preserves_uncertainty(tmp_path, variant):
    def observe():
        h = Harness(tmp_path)
        package = h.context(unknowns=[{"question": "Are negative values specified?", "blocking": False}])
        if variant == "missing":
            package.pop("requirements")
        elif variant == "unknown-ref":
            package["source_refs"] = ["invented"]
        elif variant == "stale-ref":
            (h.root / "src/calc.py").write_text("# changed\n")
        before = h.snapshot()
        result = h.send("analysis", "finish", delivery=package)
        after = h.snapshot()
        if variant != "valid":
            return (result["status"] == "rejected", after["active_job"] == before["active_job"],
                    after["context_revision"] == before["context_revision"], after["role"] == "analysis")
        return (result["status"] == "completed", after["role"] == "qa",
                after["context_revision"] == before["context_revision"] + 1,
                "Are negative values specified?" in messages(h.team.request()))
    contract(observe, (True, True, True, True))


def test_v8_03_qa_finishes_with_cases_and_targets_in_one_action(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        s = h.snapshot()
        text = messages(h.team.request())
        return s["role"], s["cases"]["C-1"]["expected"], NODE in text, "REQ-1" in text
    contract(observe, ("dev", {"returns": 4}, True, True))


@pytest.mark.parametrize("role,path,action", [
    ("analysis", "src/calc.py", "edit_source"),
    ("analysis", "tests/test_calc.py", "edit_tests"),
    ("qa", "src/calc.py", "edit_tests"),
    ("qa", "src/calc.py", "edit_source"),
    ("dev", "tests/test_calc.py", "edit_source"),
    ("dev", "tests/fixtures/input.txt", "edit_source"),
    ("dev", "conftest.py", "edit_source"),
    ("dev", "pytest.ini", "edit_source"),
    ("dev", "tests/test_calc.py", "edit_tests"),
])
def test_v8_04_server_rejects_cross_role_writes_before_io(tmp_path, role, path, action):
    def observe():
        h = Harness(tmp_path)
        if role == "qa":
            h.orient()
        elif role == "dev":
            h.red()
        # A genuine read handle ensures rejection cannot be explained by a fake ID.
        read = h.ok(role, "read_file", path=path, line_start=1, line_end=1)
        before, calls = h.files(), len(h.io.calls)
        result = h.send(role, action, handle=read["handle"], new_text="# forbidden\n", reason="REQ-1")
        return result["status"], h.files() == before, len(h.io.calls) == calls
    contract(observe, ("rejected", True, True))


@pytest.mark.parametrize("path", ["../outside.py", "/tmp/v8-outside.py", "tests/../src/calc.py", "alias/calc.py"])
def test_v8_05_path_aliases_cannot_bypass_write_scope(tmp_path, path):
    def observe():
        h = Harness(tmp_path)
        (h.root / "alias").symlink_to(h.root / "src", target_is_directory=True)
        h.orient()
        before, calls = h.files(), len(h.io.calls)
        result = h.send("qa", "read_file", path=path, line_start=1, line_end=1)
        return result["status"], h.files() == before, len(h.io.calls) == calls
    contract(observe, ("rejected", True, True))


@pytest.mark.parametrize("role", ["analysis", "qa", "dev"])
def test_v8_06_private_sources_are_never_delivered(tmp_path, role):
    def observe():
        h = Harness(tmp_path)
        if role == "qa":
            h.orient()
        elif role == "dev":
            h.suite()
        calls = len(h.io.calls)
        r = h.send(role, "read_file", path="private/PRIVATE_SENTINEL.py", line_start=1, line_end=1)
        return r["status"], len(h.io.calls) == calls, "PRIVATE_SENTINEL = 4" not in json.dumps(r)
    contract(observe, ("rejected", True, True))


@pytest.mark.parametrize("role", ["qa", "dev"])
def test_v8_07_information_answer_resumes_exact_job_and_deadline(tmp_path, role):
    def observe():
        h = Harness(tmp_path)
        h.orient() if role == "qa" else h.suite()
        before = h.snapshot()
        question = h.ok(role, "ask_analysis", question="Where is double defined?", reason="Need source for next edit.")
        assert h.snapshot()["role"] == "analysis"
        h.clock.now = 123
        source = h.ok("analysis", "read_file", path="src/calc.py", line_start=1, line_end=2)
        h.ok("analysis", "finish", delivery={"answer": "src/calc.py, lines 1–2",
             "refs": [source["evidence_id"]], "unresolved": False})
        after = h.snapshot()
        return (after["role"], after["active_job"]["id"] == before["active_job"]["id"],
                after["budget"]["deadline"] == before["budget"]["deadline"],
                "src/calc.py, lines 1–2" in messages(h.team.request()), bool(question["request_id"]))
    contract(observe, (role, True, True, True, True))


def test_v8_08_valid_answer_is_reused_but_changed_source_reopens_question(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.orient()
        payload = {"question": "Where is double defined?", "reason": "Need public source."}
        h.ok("qa", "ask_analysis", **payload)
        source = h.ok("analysis", "read_file", path="src/calc.py", line_start=1, line_end=2)
        h.ok("analysis", "finish", delivery={"answer": "src/calc.py", "refs": [source["evidence_id"]], "unresolved": False})
        job = h.snapshot()["active_job"]["id"]
        cached = h.ok("qa", "ask_analysis", **payload)
        same = h.snapshot()["role"] == "qa" and h.snapshot()["active_job"]["id"] == job
        (h.root / "src/calc.py").write_text("# moved definition\n")
        h.ok("qa", "ask_analysis", **payload)
        return cached["cached"], same, h.snapshot()["role"]
    contract(observe, (True, True, "analysis"))


def test_v8_09_analysis_cannot_ask_itself(tmp_path):
    def observe():
        h = Harness(tmp_path)
        before = h.snapshot()["active_job"]
        result = h.send("analysis", "ask_analysis", question="Where?", reason="Need source.")
        return result["status"], h.snapshot()["active_job"] == before
    contract(observe, ("rejected", True))


def test_v8_10_dev_test_change_routes_to_qa_with_evidence(tmp_path):
    def observe():
        h = Harness(tmp_path)
        red = h.red()
        h.ok("dev", "request_test_change", case_id="C-1", observed="3 instead of 4",
             suspected_error="Check whether setup should use another input.", evidence_refs=[red["evidence_id"]])
        request = h.team.request()
        return (h.snapshot()["role"], "C-1" in messages(request), "3 instead of 4" in messages(request),
                "edit_tests" in tool_names(request), "edit_source" not in tool_names(request))
    contract(observe, ("qa", True, True, True, True))


@pytest.mark.parametrize("missing", ["case_id", "observed", "suspected_error", "evidence_refs"])
def test_v8_11_incomplete_test_change_does_not_transfer_control(tmp_path, missing):
    def observe():
        h = Harness(tmp_path)
        red = h.red()
        payload = {"case_id": "C-1", "observed": "3", "suspected_error": "Input?",
                   "evidence_refs": [red["evidence_id"]]}
        payload.pop(missing)
        before = h.snapshot()["active_job"]
        result = h.send("dev", "request_test_change", **payload)
        return result["status"], h.snapshot()["role"], h.snapshot()["active_job"] == before
    contract(observe, ("rejected", "dev", True))


def test_v8_12_context_pressure_preserves_issue_code_and_open_questions(tmp_path):
    def observe():
        h = Harness(tmp_path, context_bytes=12000)
        h.orient(unknowns=[{"question": "OPEN_QUESTION_SENTINEL", "blocking": True}])
        for line in range(1, 9):
            # Distinct dialogs, so a repeated-action recovery cannot explain eviction.
            (h.root / "tests/long.txt").write_text("".join(f"line-{i}\n" for i in range(10)))
            h.ok("qa", "read_file", path="tests/long.txt", line_start=line, line_end=line)
        request = h.team.request()
        text = messages(request)
        return ISSUE in text, "OPEN_QUESTION_SENTINEL" in text, "return value * 2 - 1" in text, len(request["history"]) <= 4
    contract(observe, (True, True, True, True))


def test_v8_13_impossible_input_budget_fails_before_inference(tmp_path):
    def observe():
        h = Harness(tmp_path, context_bytes=16)
        r = h.team.request()
        return r["status"], h.snapshot()["metrics"]["model_calls"]
    contract(observe, ("context_error", 0))


@pytest.mark.parametrize("missing", ["input", "expected", "reason", "reason_ref"])
def test_v8_14_case_delivery_requires_input_oracle_and_reason(tmp_path, missing):
    def observe():
        h = Harness(tmp_path)
        h.orient()
        h.ok("qa", "collect_tests", targets=[NODE])
        delivery = h.suite_delivery()
        delivery["cases"] = [copy.deepcopy(CASE)]
        delivery["cases"][0].pop(missing)
        r = h.send("qa", "finish", delivery=delivery)
        return r["status"], h.snapshot()["role"], h.snapshot()["cases"]
    contract(observe, ("rejected", "qa", {}))
