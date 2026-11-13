"""Symmetric public navigation, narrow legacy compatibility and strict edits."""

import json

import pytest
from v9_support import ALLOWED, Harness, contract, model_text, tool_names


@pytest.mark.parametrize("role", ["analysis", "qa", "dev"])
def test_v9_14_each_role_can_find_search_and_read_unassigned_public_code(tmp_path, role):
    def observe():
        h = Harness(tmp_path)
        h.activate(role)
        h.write("other/unassigned.py", "UNASSIGNED_PUBLIC = 7\n")
        paths = h.ok(role, "find_paths", pattern="other/*.py")
        found = h.ok(role, "search_content", scope="other", query="UNASSIGNED_PUBLIC")
        read = h.read(role, "other/unassigned.py", end=1)
        return paths["paths"], found["hits"][0]["path"], read["text"]
    contract(observe, (["other/unassigned.py"], "other/unassigned.py", "UNASSIGNED_PUBLIC = 7\n"))


@pytest.mark.parametrize("role", ["analysis", "qa", "dev"])
@pytest.mark.parametrize("operation", ["read_file", "search_content", "find_paths"])
@pytest.mark.parametrize("boundary", ["private", "outside", "symlink"])
def test_v9_15_navigation_cannot_disclose_private_or_external_content(tmp_path, role, operation, boundary):
    def observe():
        h = Harness(tmp_path)
        h.activate(role)
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "secret.py").write_text("EXTERNAL_SECRET = 1\n")
        (h.root / "alias").symlink_to(outside, target_is_directory=True)
        scope = {"private": "private", "outside": "../outside", "symlink": "alias"}[boundary]
        payload = ({"path": scope + "/secret.py", "line_start": 1, "line_end": 1}
                   if operation == "read_file" else
                   {"scope": scope, "query": "SECRET"} if operation == "search_content" else
                   {"pattern": scope + "/*.py"})
        if boundary == "private" and operation == "read_file":
            payload["path"] = "private/PRIVATE_SENTINEL.py"
        before = h.files()
        response = h.send(role, operation, **payload)
        text = json.dumps(response)
        # Globs may legitimately return an empty public path list.
        denied = response["status"] == "rejected" or (
            operation == "find_paths" and response["status"] == "completed" and response["paths"] == []
        )
        return denied, "PRIVATE_CONTENT_SENTINEL" not in text, "EXTERNAL_SECRET" not in text, h.files() == before
    contract(observe, (True,) * 4)


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
def test_v9_16_dispatcher_rejects_forbidden_writes_with_genuine_handle(tmp_path, role, path, action):
    def observe():
        h = Harness(tmp_path)
        h.activate(role)
        read = h.read(role, path, end=1)
        before, calls = h.files(), len(h.io.calls)
        result = h.send(role, action, handle=read["handle"], new_text="# forbidden\n", reason="REQ-1")
        return result["status"], h.files() == before, len(h.io.calls) == calls
    contract(observe, ("rejected", True, True))


@pytest.mark.parametrize("legacy", ["0", 0, "", "invalid-token", "private/PRIVATE_SENTINEL.py"])
@pytest.mark.parametrize("tool", ["search_content", "find_paths"])
def test_v9_17_only_legacy_cursor_is_ignored_and_scope_is_preserved(tmp_path, legacy, tool):
    def observe():
        h = Harness(tmp_path)
        payload = ({"scope": "src", "query": "double"} if tool == "search_content" else {"pattern": "src/*.py"})
        key = "hits" if tool == "search_content" else "paths"
        first = h.ok("analysis", tool, **payload)
        compat = h.ok("analysis", tool, **payload, cursor=legacy)
        request = h.team.request()
        return (first[key] == compat[key], bool(compat[key]),
                "cursor" not in json.dumps(request["schema"]),
                "cursor" not in json.dumps(compat), "cursor" not in model_text(request))
    contract(observe, (True,) * 5)


@pytest.mark.parametrize("extra", [{"offset": 0}, {"start": 0}, {"typo": "x"}])
def test_v9_18_cursor_adapter_does_not_tolerate_other_schema_errors(tmp_path, extra):
    def observe():
        h = Harness(tmp_path)
        result = h.send("analysis", "search_content", scope="src", query="double", cursor="0", **extra)
        return result["status"], not result.get("hits")
    contract(observe, ("rejected", True))


@pytest.mark.parametrize("scope", ["", "."])
def test_v9_19_root_scope_searches_public_repo_in_deterministic_order(tmp_path, scope):
    def observe():
        h = Harness(tmp_path)
        for path, value in [("z.py", "ROOT_NEEDLE\n"), ("a.py", "ROOT_NEEDLE\nROOT_NEEDLE\n"),
                            ("private/hidden.py", "ROOT_NEEDLE\n")]:
            h.write(path, value)
        result = h.ok("analysis", "search_content", scope=scope, query="ROOT_NEEDLE")
        return [(hit["path"], hit["line"]) for hit in result["hits"]], result["truncated"]
    contract(observe, ([("a.py", 1), ("a.py", 2), ("z.py", 1)], False))


@pytest.mark.parametrize("scope", ["src/missing.py", "src"])
def test_v9_20_missing_scope_differs_from_valid_empty_result(tmp_path, scope):
    def observe():
        h = Harness(tmp_path)
        result = h.send("analysis", "search_content", scope=scope, query="NO_MATCH")
        if scope == "src":
            return result["status"] == "completed", result["hits"] == [], True
        candidates = result["candidates"]
        return (result["status"] == "scope_not_found", result["scope"] == scope,
                len(candidates) <= 5 and all((h.root / p).exists() and not p.startswith("private/") for p in candidates))
    contract(observe, (True, True, True))


@pytest.mark.parametrize("tool,count", [("search_content", 50), ("search_content", 51), ("find_paths", 51)])
def test_v9_21_search_limit_is_explicit_without_pagination(tmp_path, tool, count):
    def observe():
        h = Harness(tmp_path)
        for i in reversed(range(count)):
            h.write(f"many/file_{i:03d}.py", "LIMIT_NEEDLE\n")
        result = h.ok("analysis", tool, **({"scope": "many", "query": "LIMIT_NEEDLE"}
                                          if tool == "search_content" else {"pattern": "many/*.py"}))
        paths = [hit["path"] for hit in result["hits"]] if tool == "search_content" else result["paths"]
        return (len(paths), paths == sorted(paths), result["truncated"],
                bool(result.get("hint")) if count > 50 else True, "cursor" not in json.dumps(result))
    contract(observe, (50, True, count > 50, True, True))


def test_v9_22_literal_search_and_inclusive_read_preserve_exact_bytes(tmp_path):
    def observe():
        h = Harness(tmp_path)
        result = h.ok("analysis", "search_content", scope="src/literal.py", query="\\d+[x]")
        read = h.read(path="src/literal.py", start=2, end=999)
        return ([hit["line"] for hit in result["hits"]], read["text"], read["line_start"], read["line_end"])
    contract(observe, ([2], '\\d+[x]\n"None"\n', 2, 3))


def test_v9_23_stale_handle_conflicts_before_write_and_fresh_handle_repairs(tmp_path):
    def observe():
        h = Harness(tmp_path)
        h.red()
        read = h.read("dev")
        h.write("src/calc.py", "def double(value):\n    return value + value - 1\n")
        calls = len(h.io.calls)
        result = h.send("dev", "edit_source", handle=read["handle"], new_text="BAD\n", reason="REQ-1")
        no_write = not any(c["action"] == "replace_region" for c in h.io.calls[calls:])
        h.edit()
        return result["code"], "value + value - 1" in result["current_text"], no_write, "BAD" not in (h.root / "src/calc.py").read_text()
    contract(observe, ("edit_conflict", True, True, True))


def test_v9_24_repetition_keeps_search_available_and_never_invents_completion(tmp_path):
    def observe():
        h = Harness(tmp_path)
        results = []
        for _ in range(2):
            results.append(h.ok("analysis", "search_content", scope="src", query="NO_MATCH"))
        request = h.team.request()
        s = h.snapshot()
        return (results[0]["evidence_id"] == results[1]["evidence_id"], results[1]["cached"],
                "search_content" in tool_names(request), request["job"]["decision_required"],
                s["status"], s["completion"]["allowed"])
    contract(observe, (True, True, True, True, "running", False))


@pytest.mark.parametrize("role,path,action", [
    ("qa", "tests/test_added.py", "edit_tests"), ("dev", "src/added.py", "edit_source"),
])
def test_v9_25_new_files_use_empty_read_handle_and_the_existing_edit_contract(tmp_path, role, path, action):
    def observe():
        h = Harness(tmp_path)
        h.activate(role)
        read = h.read(role, path, end=1)
        text = "# New file in the role's allowed tree.\n"
        result = h.ok(role, action, handle=read["handle"], new_text=text, reason="REQ-1")
        return read["text"], result["status"], (h.root / path).read_text(), tool_names(h.team.request()) == ALLOWED[role]
    contract(observe, ("", "completed", "# New file in the role's allowed tree.\n", True))
