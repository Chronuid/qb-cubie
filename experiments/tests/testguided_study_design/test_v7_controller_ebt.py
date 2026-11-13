"""Red v7 acceptance examples, grounded in AGENTENDESIGN-V7 sections 3–9.

No xfail, no fallback to v6, no simulated controller. See V7_CASES.md for the
proposed observable seam and limits of scripted test-service evidence.
"""

import json

import pytest
from v6_support import ISSUE, NODE, contract, outcome
from v7_support import Harness


@pytest.mark.parametrize("boundary", ["calls", "seconds"])
def test_a01_orientation_continues_past_legacy_phase_limits(tmp_path, boundary):
    def observe():
        h = Harness(tmp_path)
        h.ok("analysis", "read_file", path="src/calc.py", line_start=1, line_end=2)
        if boundary == "seconds":
            h.clock.now = 120
        else:
            for _ in range(6):
                h.team.request()
                h.send("analysis", "find_paths", pattern="src/*.py")
        before = h.snapshot()["metrics"]["model_calls"]
        h.tick()
        s = h.snapshot()
        context = json.loads((tmp_path / "archive/context.json").read_text())
        return (s["role"], s["state"], s["metrics"]["model_calls"] == before,
                context.get("provisional", False), context.get("requirements", []),
                s["completion"]["allowed"], bool(s["active_job"]["id"]))
    contract(observe, ("analysis", "orient", True, False, [], False, True))


@pytest.mark.parametrize("variant", ["valid", "invalid-ref", "duplicate", "stale-ref"])
def test_a02_finish_is_atomic_versioned_and_idempotent(tmp_path, variant):
    def observe():
        h = Harness(tmp_path)
        package = h.package()
        if variant == "invalid-ref":
            package["source_refs"] = ["invented-evidence"]
        if variant == "stale-ref":
            (h.root / "src/calc.py").write_text("def double(value):\n    return value\n")
        before = h.snapshot()
        response = h.send("analysis", "finish_orientation", **package)
        if variant == "duplicate":
            h.send("analysis", "finish_orientation", **package)
        after = h.snapshot()
        if variant in {"invalid-ref", "stale-ref"}:
            return (response["status"], after["context_revision"] == before["context_revision"],
                    after["messages"] == before["messages"], after["active_job"] == before["active_job"])
        messages = [m for m in after["messages"] if m["type"] == "context_ready"]
        return response["status"], len(messages) == 1, after["role"] == "qa", after["context_revision"] == 1
    contract(observe, ("rejected" if variant in {"invalid-ref", "stale-ref"} else "completed", True, True, True))


def test_a03_missing_scope_suggests_real_src_path_without_redirect(tmp_path):
    def observe():
        h = Harness(tmp_path)
        missing = h.send("analysis", "search_content", scope="requests/utils.py", query="unquote")
        found = h.ok("analysis", "search_content", scope="src/requests/utils.py", query="unquote")
        return (missing["status"], missing["scope_exists"],
                "src/requests/utils.py" in missing["candidates"], len(missing["candidates"]) <= 5,
                bool(missing.get("hits")), found["hits"][0]["path"])
    contract(observe, ("scope_not_found", False, True, True, False, "src/requests/utils.py"))


@pytest.mark.parametrize("scope,status,exists", [
    ("src", "completed", True), ("src/absent.py", "scope_not_found", False),
    ("private/SECRET_SENTINEL.py", "scope_denied", None),
    ("../outside.py", "scope_denied", None),
])
def test_a04_scope_outcomes_and_private_boundary(tmp_path, scope, status, exists):
    def observe():
        h = Harness(tmp_path)
        r = h.send("analysis", "search_content", scope=scope, query="NO_SUCH_LITERAL")
        return (r["status"], r.get("scope_exists"), r.get("hits", []),
                "SECRET_SENTINEL" not in json.dumps({k: r.get(k) for k in ("candidates", "hits")}))
    contract(observe, (status, exists, [], True))


def test_a04_undecodable_file_is_explicitly_skipped(tmp_path):
    def observe():
        h = Harness(tmp_path)
        (h.root / "src/binary.py").write_bytes(b"\xff\xfe\x00")
        r = h.send("analysis", "search_content", scope="src", query="NO_SUCH_LITERAL")
        return r["status"], r["scope_exists"], r["files_searched"] > 0, bool(r["files_skipped"])
    contract(observe, ("completed", True, True, True))


@pytest.mark.parametrize("bad", [{"start": 860}, {"cursor": 860}, {"cursor": "invented"}])
def test_a05_search_rejects_legacy_offsets_and_invented_cursors(tmp_path, bad):
    def observe():
        h = Harness(tmp_path)
        r = h.send("analysis", "search_content", scope="src", query="return", **bad)
        return r["status"] in {"rejected", "cursor_error"}, bool(r.get("hits"))
    contract(observe, (True, False))


@pytest.mark.parametrize("mutation", ["none", "content", "query", "tool"])
def test_a05_cursor_is_bound_and_pages_have_no_loss_or_duplicates(tmp_path, mutation):
    def observe():
        h = Harness(tmp_path, search_page_size=2)
        (h.root / "src/pages.py").write_text("".join(f"needle_{i}\n" for i in range(5)))
        first = h.ok("analysis", "search_content", scope="src/pages.py", query="needle")
        assert first["truncated"] is True and first["next_cursor"]
        cursor = first["next_cursor"]
        if mutation == "content":
            (h.root / "src/pages.py").write_text("changed\n")
        if mutation == "tool":
            r = h.send("analysis", "find_paths", pattern="src/*", cursor=cursor)
        else:
            r = h.send("analysis", "search_content", scope="src/pages.py",
                       query="other" if mutation == "query" else "needle", cursor=cursor)
        if mutation != "none":
            return r["status"] == "cursor_error", bool(r.get("hits"))
        hits = first["hits"] + r["hits"]
        while r.get("next_cursor"):
            r = h.ok("analysis", "search_content", scope="src/pages.py", query="needle", cursor=r["next_cursor"])
            hits += r["hits"]
        return [hit["line"] for hit in hits] == [1, 2, 3, 4, 5], False
    contract(observe, (True, False))


def test_a05_literal_escapes_survive_json_and_inclusive_line_reads(tmp_path):
    def observe():
        h = Harness(tmp_path)
        query = r"\d+[x]"
        (h.root / "src/literal.py").write_text("123x\n" + query + "\nend\n")
        r = h.ok("analysis", "search_content", **json.loads(json.dumps({"scope": "src/literal.py", "query": query})))
        read = h.ok("analysis", "read_file", path="src/literal.py", line_start=2, line_end=2)
        return [hit["line"] for hit in r["hits"]], read["text"]
    contract(observe, ([2], "\\d+[x]\n"))


def test_a06_duplicate_read_avoids_backend_and_only_new_lines_count(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.ok("analysis", "read_file", path="src/calc.py", line_start=1, line_end=1)
        before, calls = h.snapshot(), len(h.io.calls)
        r = h.send("analysis", "read_file", path="src/calc.py", line_start=1, line_end=1)
        cached = len(h.io.calls) == calls
        h.ok("analysis", "read_file", path="src/calc.py", line_start=1, line_end=2)
        after = h.snapshot()
        return (r["duplicate_action"], cached,
                after["progress"]["read_lines"] - before["progress"]["read_lines"],
                after["metrics"]["tool_calls"] - before["metrics"]["tool_calls"])
    contract(observe, (True, True, 1, 2))


def test_a07_two_empty_searches_trigger_diagnosis_and_schema_change(tmp_path):
    def observe():
        h = Harness(tmp_path)
        schema = h.team.request()["schema"]
        for query in ("absent-A", "absent-B"):
            h.send("analysis", "search_content", scope="src", query=query)
        s = h.snapshot()
        return (s["metrics"]["recoveries"], bool(s["recovery_episodes"][-1]["diagnosis"]),
                schema != h.team.request()["schema"], s["metrics"]["controller_tool_calls"] > 0)
    contract(observe, (1, True, True, True))


def test_a08_provisional_context_needs_public_requirement_confirmation(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.orient()
        h.ok("qa", "find_paths", pattern="src/*.py")
        rejected = h.send("qa", "publish_suite", case_ids=[], targets=[NODE], expected_red={})
        h.ok("qa", "confirm_requirements", requirements=[{
            "id": "REQ-1", "text": ISSUE, "refs": ["issue:REQ-1"],
        }])
        h.prepare_suite()
        accepted = h.send("qa", "publish_suite", case_ids=["C-1"], targets=[NODE],
                          expected_red={"C-1": "3 instead of 4"})
        return rejected["status"], accepted["status"], h.snapshot()["qualifications"]["reproduced"]
    contract(observe, ("rejected", "completed", False))


@pytest.mark.parametrize("valid", [True, False])
def test_a09_qa_keeps_control_past_legacy_phase_deadline(tmp_path, valid):
    def observe():
        h = Harness(tmp_path)
        h.orient()
        if valid:
            h.prepare_suite()
        h.clock.now = 180
        h.tick()
        s = h.snapshot()
        if valid:
            return s["role"], s["state"], s["qualifications"]["reproduced"]
        h.clock.now = 225
        h.tick()
        s = h.snapshot()
        return s["status"], s["reason"], s["completion"]["allowed"]
    contract(observe, ("qa", "specify", False) if valid else ("running", None, False))


@pytest.mark.parametrize("observation", ["collection_error", "pass", "assertion_failure"])
def test_a10_only_matching_behavioral_red_unlocks_production(tmp_path, observation):
    def observe():
        h = Harness(tmp_path)
        h.suite()
        failed = [(NODE, "AssertionError", "assert 3 == 4")] if observation == "assertion_failure" else []
        h.run(outcome(observation, failed=failed, executed=0 if observation == "collection_error" else 1))
        read = h.ok("dev", "read_file", path="src/calc.py", line_start=2, line_end=2)
        before = (h.root / "src/calc.py").read_bytes()
        r = h.send("dev", "replace_region", handle=read["handle"], new_text="    return value * 2\n", reason="REQ-1")
        return r["status"], h.snapshot()["qualifications"]["reproduced"], (h.root / "src/calc.py").read_bytes() != before
    contract(observe, ("completed", True, True) if observation == "assertion_failure" else ("rejected", False, False))


@pytest.mark.parametrize("role", ["qa", "dev"])
def test_a11_information_roundtrip_preserves_job_budget_and_deduplicates(tmp_path, role):
    def observe():
        h = Harness(tmp_path)
        h.orient() if role == "qa" else h.suite()
        before = h.snapshot()
        question = {"question": "Which public compatibility rule applies?", "refs": ["issue:REQ-1"]}
        r = h.ok(role, "ask_analysis", **question)
        h.clock.now = 30
        h.ok("analysis", "answer_question", reply_to=r["message_id"], answer="Unknown",
             refs=[], unknown=True)
        after = h.snapshot()
        messages = len(after["messages"])
        h.send(role, "ask_analysis", **question)
        final = h.snapshot()
        return (after["role"], after["active_job"] == before["active_job"],
                after["budget"]["deadline"] == before["budget"]["deadline"],
                len(final["messages"]) == messages, bool(final["open_questions"]), final["completion"]["allowed"])
    contract(observe, (role, True, True, True, True, False))


@pytest.mark.parametrize("elapsed,timeout", [(0, 1800), (100, 1700)])
def test_a12_request_timeout_uses_shared_task_deadline(tmp_path, elapsed, timeout):
    def observe():
        h = Harness(tmp_path)
        h.clock.now = elapsed
        request = h.team.request()
        return request["timeout_seconds"], h.snapshot()["budget"]["deadline"]
    contract(observe, (timeout, 1800))


def test_a12_global_exhaustion_precedes_automatic_handoff(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.clock.now = 1800
        h.tick()
        s = h.snapshot()
        return s["status"], s["reason"], bool(s["messages"]), (tmp_path / "archive/full.patch").exists(), s["private_evaluation_required"]
    contract(observe, ("incomplete", "budget_exhausted", False, True, True))


@pytest.mark.parametrize("phase", ["orient", "specify", "implement", "review"])
def test_a13_reserve_blocks_new_repair_and_preserves_artifacts(tmp_path, phase):
    def observe():
        h = Harness(tmp_path)
        if phase == "specify":
            h.orient()
        elif phase == "implement":
            h.red()
            h.edit()
        elif phase == "review":
            h.verified()
        h.clock.now = 720
        s = h.snapshot()
        r = h.send(s["role"], "request_test_change", case_ids=["C-1"], requirement_id="REQ-1",
                   evidence_ids=[], reason="Another repair round")
        final = h.snapshot()
        return (r["status"], final["budget"]["reserve_active"], final["metrics"]["revision_rounds"],
                (tmp_path / "archive/full.patch").exists(), final["private_evaluation_required"])
    contract(observe, ("rejected", False, 0, True, True))


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
def test_a14_complete_scripted_contract_keeps_public_boundary(tmp_path, mode):
    def observe():
        h = Harness(tmp_path, mode=mode)
        h.verified()
        h.ok("analysis", "submit", reason="Current REQ-1 evidence reviewed")
        s = h.snapshot()
        archive = json.loads((tmp_path / "archive/team.json").read_text())
        return (s["status"], s["qualifications"], s["completion"]["allowed"],
                "SECRET_SENTINEL" not in json.dumps(archive), s["private_evaluation_required"])
    contract(observe, ("submitted", {"reproduced": True, "verified": True}, True, True, True))
