"""Execute the shipped workspace script locally in temporary trees."""

import json
import subprocess
import sys

import pytest
from testguided_study.workspace import SCRIPT, bounded


def execute(root, action):
    script = SCRIPT.replace("pathlib.Path('/workspace')", "pathlib.Path(" + repr(str(root)) + ")")
    return subprocess.run([sys.executable, "-S", "-c", script, json.dumps(action)],
                          check=False, capture_output=True, text=True, timeout=5)


@pytest.mark.parametrize("original,old,new,expected,success", [
    ("one\ntwo\n", "two", "three", "one\nthree\n", True),
    ("same same", "same", "other", "same same", False),
    ("unchanged", "absent", "other", "unchanged", False),
    ("one\ntwo\n", "two\n", "", "one\n", True),
])
def test_anchored_edit_requires_exactly_one_match(tmp_path, original, old, new, expected, success):
    source = tmp_path / "source.py"
    source.write_text(original)
    response = execute(tmp_path, {"action": "replace_text", "path": "source.py", "old": old, "new": new})
    assert (response.returncode == 0) is success
    assert source.read_text() == expected


@pytest.mark.parametrize("path", ["../outside.py", "/tmp/outside.py", ".git/config", "link.py"])
def test_anchored_edit_preserves_workspace_boundary(tmp_path, path):
    outside = tmp_path.parent / "outside.py"
    outside.write_text("original")
    (tmp_path / "link.py").symlink_to(outside)
    response = execute(tmp_path, {"action": "replace_text", "path": path, "old": "original", "new": "changed"})
    assert response.returncode != 0
    assert outside.read_text() == "original"


def test_scoped_search_pages_without_duplicate_or_missing_hits(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/example.py").write_text("needle\n" * 90)
    (tmp_path / "noise.py").write_text("needle")
    first = execute(tmp_path, {"action": "search_files", "path": "src", "query": "needle", "start": 0})
    page = json.loads(first.stdout)
    assert len(page["hits"]) == 80
    assert page["next_start"] == 80
    second = execute(tmp_path, {"action": "search_files", "path": "src", "query": "needle", "start": page["next_start"]})
    tail = json.loads(second.stdout)
    assert tail["next_start"] is None
    assert [hit["line"] for hit in page["hits"] + tail["hits"]] == list(range(1, 91))
    assert {hit["path"] for hit in page["hits"] + tail["hits"]} == {"src/example.py"}


def test_output_limit_preserves_structured_hits_and_continuation():
    hits = [{"path": "a.py", "line": i, "text": "x" * 100} for i in range(80)]
    result = bounded({"hits": hits, "start": 10, "next_start": 90}, 1000)
    assert len(json.dumps(result)) <= 1000
    assert result["truncated"] is True
    assert result["next_start"] == 10 + len(result["hits"])
    assert 0 < len(result["hits"]) < 80


def test_oversize_lines_are_not_returned_as_broken_json():
    result = bounded({"text": "x" * 10000, "start": 1, "total_lines": 1}, 1000)
    assert result["status"] == "tool_error"
