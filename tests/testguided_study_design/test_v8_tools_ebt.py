"""v8 literal search, edit conflicts and recovery acceptance examples."""

import json

import pytest
from v8_support import Harness, contract, messages, tool_names


@pytest.mark.parametrize("scope,status", [("src/missing.py", "scope_not_found"), ("src", "completed")])
def test_v8_15_missing_scope_differs_from_valid_empty_search(tmp_path, scope, status):
    def observe():
        h = Harness(tmp_path)
        r = h.send("analysis", "search_content", scope=scope, query="NO_MATCH")
        return (r["status"], r["scope_exists"], r["hits"],
                "src/calc.py" in r.get("candidates", []) if status == "scope_not_found" else True,
                "PRIVATE_SENTINEL" not in json.dumps(r.get("candidates", [])))
    contract(observe, (status, status == "completed", [], True, True))


def test_v8_16_search_literals_and_inclusive_line_bounds_survive_json(tmp_path):
    def observe():
        h = Harness(tmp_path)
        (h.root / "src/literal.py").write_text('123x\n\\d+[x]\n"None"\n')
        r = h.ok("analysis", "search_content", **json.loads(json.dumps({"scope": "src/literal.py", "query": r"\d+[x]"})))
        read = h.ok("analysis", "read_file", path="src/literal.py", line_start=2, line_end=3)
        return [hit["line"] for hit in r["hits"]], read["text"]
    contract(observe, ([2], '\\d+[x]\n"None"\n'))


def test_v8_17_path_search_never_becomes_content_search(tmp_path):
    def observe():
        h = Harness(tmp_path)
        wrong = h.ok("analysis", "find_paths", pattern="def double")
        right = h.ok("analysis", "search_content", scope="src", query="def double")
        return wrong["paths"], "search_content" in wrong["hint"], right["hits"][0]["path"]
    contract(observe, ([], True, "src/calc.py"))


@pytest.mark.parametrize("mutation", ["none", "source", "query", "tool"])
def test_v8_18_cursors_are_runner_owned_and_bound_to_query_and_source(tmp_path, mutation):
    def observe():
        h = Harness(tmp_path, search_page_size=2)
        path = h.root / "src/pages.py"
        path.write_text("".join(f"needle_{i}\n" for i in range(5)))
        first = h.ok("analysis", "search_content", scope="src/pages.py", query="needle")
        cursor = first["next_cursor"]
        assert cursor
        if mutation == "source":
            path.write_text("changed\n")
        if mutation == "tool":
            r = h.send("analysis", "find_paths", pattern="src/*", cursor=cursor)
        else:
            r = h.send("analysis", "search_content", scope="src/pages.py",
                       query="other" if mutation == "query" else "needle", cursor=cursor)
        if mutation != "none":
            return r["status"] == "cursor_error", not r.get("hits")
        hits = first["hits"] + r["hits"]
        while r.get("next_cursor"):
            r = h.ok("analysis", "search_content", scope="src/pages.py", query="needle", cursor=r["next_cursor"])
            hits += r["hits"]
        return [hit["line"] for hit in hits] == [1, 2, 3, 4, 5], True
    contract(observe, (True, True))


@pytest.mark.parametrize("bad", [{"cursor": 860}, {"cursor": "invented"}, {"start": 860}])
def test_v8_19_offsets_and_invented_cursors_are_explicit_errors(tmp_path, bad):
    def observe():
        h = Harness(tmp_path)
        r = h.send("analysis", "search_content", scope="src", query="double", **bad)
        return r["status"] in {"cursor_error", "rejected"}, not r.get("hits")
    contract(observe, (True, True))


def test_v8_20_stale_edit_returns_current_text_and_fresh_read_allows_patch(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.red()
        read = h.ok("dev", "read_file", path="src/calc.py", line_start=2, line_end=2)
        (h.root / "src/calc.py").write_text("def double(value):\n    return value + value - 1\n")
        calls = len(h.io.calls)
        r = h.send("dev", "edit_source", handle=read["handle"], new_text="    return value * 2\n", reason="REQ-1")
        no_write = not any(c["action"] == "replace_region" for c in h.io.calls[calls:])
        h.edit()
        return (r["status"], r["code"], "value + value - 1" in r["current_text"], no_write,
                (h.root / "src/calc.py").read_text())
    contract(observe, ("rejected", "edit_conflict", True, True, "def double(value):\n    return value * 2\n"))


def test_v8_21_second_identical_action_rebuilds_job_without_removing_tools(tmp_path):
    def observe():
        h = Harness(tmp_path)
        first = h.ok("analysis", "read_file", path="src/calc.py", line_start=1, line_end=2)
        calls = len(h.io.calls)
        second = h.ok("analysis", "read_file", path="src/calc.py", line_start=1, line_end=2)
        cached = len(h.io.calls) == calls
        request = h.team.request()
        return (second["cached"], cached, second["evidence_id"] == first["evidence_id"],
                "search_content" in tool_names(request), request["job"]["decision_required"],
                len(request["history"]) == 1, h.snapshot()["status"])
    contract(observe, (True, True, True, True, True, True, "running"))


def test_v8_22_repeated_search_keeps_full_archive_and_short_history(tmp_path):
    def observe():
        h = Harness(tmp_path)
        for note in ("first wording", "different wording"):
            h.ok("analysis", "search_content", scope="src", query="NO_MATCH", note=note)
        r = h.team.request()
        archived = list((tmp_path / "archive/actions").glob("*.json"))
        attempts = [json.loads(p.read_text()) for p in archived]
        searches = [a for a in attempts if a["action"]["action"] == "search_content"]
        return len(searches), len(r["history"]), "search_content" in tool_names(r), r["job"]["decision_required"]
    contract(observe, (2, 1, True, True))


def test_v8_23_loop_recovery_hands_existing_uncertain_context_to_qa(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.ok("analysis", "update_context", context=h.context(unknowns=[{
            "question": "Negative inputs unspecified", "blocking": False,
        }]))
        for _ in range(3):
            h.send("analysis", "search_content", scope="src", query="NO_MATCH")
            h.team.request()
        s = h.snapshot()
        text = messages(h.team.request())
        return s["role"], s["status"], s["completion"]["allowed"], "Negative inputs unspecified" in text
    contract(observe, ("qa", "running", False, True))


def test_v8_24_changed_source_invalidates_cached_read(tmp_path):
    def observe():
        h = Harness(tmp_path)
        first = h.ok("analysis", "read_file", path="src/calc.py", line_start=1, line_end=2)
        (h.root / "src/calc.py").write_text("def double(value):\n    return value * 2\n")
        second = h.ok("analysis", "read_file", path="src/calc.py", line_start=1, line_end=2)
        return first["evidence_id"] != second["evidence_id"], second.get("cached", False), second["text"]
    contract(observe, (True, False, "def double(value):\n    return value * 2\n"))
