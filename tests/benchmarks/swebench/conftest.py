"""Build synthetic SWE-bench rows and real local Git history without downloads."""

import hashlib
import json
import socket
import subprocess
from copy import deepcopy

import pytest

DATASET = "SWE-bench/SWE-bench_Lite"
REVISION = "a" * 40
HARNESS = "b" * 40
GOLD = """diff --git a/calc.py b/calc.py
--- a/calc.py
+++ b/calc.py
@@ -1,2 +1,2 @@
 def total(values):
-    return 0
+    return sum(values)  # GOLD_SOLUTION_SENTINEL
"""
TEST_PATCH = """diff --git a/test_total.py b/test_total.py
new file mode 100644
--- /dev/null
+++ b/test_total.py
@@ -0,0 +1,3 @@
+from calc import total
+def test_total():
+    assert total([2, 3]) == 5  # PRIVATE_TEST_SENTINEL
"""


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(root):
    return {str(path.relative_to(root)): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("SWE-bench acceptance cases must stay offline")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)


@pytest.fixture
def snapshot(tmp_path):
    root = tmp_path / "synthetic source with spaces"
    repo = root / "repos" / "demo"
    repo.mkdir(parents=True)
    git(repo, "init", "--initial-branch=main")
    git(repo, "config", "user.name", "Synthetic acceptance fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "commit.gpgsign", "false")
    (repo / "calc.py").write_text("def total(values):\n    return 0\n", encoding="utf-8")
    (repo / "test_existing.py").write_text("from calc import total\ndef test_empty():\n    assert total([]) == 0\n",
                                           encoding="utf-8")
    (repo / "LICENSE").write_text("MIT; synthetic acceptance material\n", encoding="utf-8")
    (repo / "setup.py").write_text("raise RuntimeError('PROJECT_CODE_MUST_NOT_RUN')\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Synthetic base")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "calc.py").write_text("def total(values):\n    return sum(values)  # GOLD_SOLUTION_SENTINEL\n",
                                  encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Future solution must not reach the agent")
    records = [{"instance_id": f"demo__calc-{number}", "repo": "demo/calc", "base_commit": base,
                "environment_setup_commit": base, "version": "1.0", "created_at": "2024-01-01T00:00:00Z",
                "problem_statement": "Calculate totals, including empty lists and Unicode: Größe.",
                "hints_text": "OPTIONAL_HINT_SENTINEL", "patch": GOLD, "test_patch": TEST_PATCH,
                "FAIL_TO_PASS": json.dumps(["test_total.py::test_total"]),
                "PASS_TO_PASS": json.dumps(["test_existing.py::test_empty"])} for number in (1, 2, 3)]
    source = {"schema_version": 1, "dataset_name": DATASET, "revision": REVISION, "split": "test",
              "dataset_license": "MIT", "repository_licenses": {"demo/calc": "MIT"},
              "repositories": {"demo/calc": "repos/demo"}}
    result = {"root": root, "repo": repo, "base": base, "records": records, "source": source}
    rewrite_snapshot(result)
    return result


def rewrite_snapshot(snapshot):
    rows = snapshot["root"] / "records.jsonl"
    rows.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in snapshot["records"]),
                    encoding="utf-8")
    snapshot["source"]["records_sha256"] = digest(rows)
    write_json(snapshot["root"] / "source.json", snapshot["source"])


@pytest.fixture
def config(snapshot, tmp_path):
    return {"schema_version": 1, "dataset_name": DATASET, "revision": REVISION, "split": "test",
            "snapshot": str(snapshot["root"]), "cache_dir": str(tmp_path / "cache"), "offline": True,
            "namespace": "swebench-fixture", "version": "1.0.0", "seed": 17,
            "instance_ids": ["demo__calc-1", "demo__calc-2"], "include_hints": False,
            "on_error": "fail", "process_profile": "issue_resolution", "harness_revision": HARNESS}


@pytest.fixture
def importer(public_api):
    # Resolution happens inside the test call, so absent implementation is an assertion failure.
    def invoke(config, destination):
        return public_api("import_swebench")(deepcopy(config), destination)
    return invoke


def exported_cases(public_api, root):
    package = public_api("load_package")(root)
    return package, [(case, (root / case["manifest"]).parent) for case in package["scenarios"]]
