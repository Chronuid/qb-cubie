# ruff: noqa: F811
"""Acceptance contracts from the active pilot 20261111-180702.

Introduced as red contracts; now required to pass without xfail. All inputs
are synthetic; no live archive, Docker container or inference server is touched.
"""

import copy
import hashlib
import json
from xml.etree import ElementTree as ET

import pytest
from test_pilot_technical_ebt import (
    SUBMIT,
    LocalSandbox,
    contract,
    pilot_session,  # noqa: F401 -- shared real-session fixture
)
from test_session_integration import action
from test_workspace_iteration import execute as local_execute
from testguided_study import workspace
from testguided_study.artifacts import read
from testguided_study.controller import session_context


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def edit(path, original, old, new):
    return action("replace_text", path=path, expected_sha256=sha256(original),
                  old=old, new=new, reason="Implement the required behavior")


@pytest.mark.parametrize("replacement", [
    "def value(:\n    return 2\n",
    "def value():\n    if True:\n        return 2\n   return 3\n",
    "def value():\n    return 'unterminated\n",
], ids=["syntax", "indentation", "unterminated-string"])
def test_a01_invalid_python_replacement_is_rejected_before_any_mutation(tmp_path, replacement):
    source = tmp_path / "module.py"
    original = b"def value():\n    return 1\n"
    source.write_bytes(original)
    before = source.stat().st_mtime_ns

    def observe():
        versions = json.loads(local_execute(tmp_path, action("snapshot")).stdout)
        response = local_execute(tmp_path, edit("module.py", original, original.decode(), replacement))
        result = json.loads(response.stdout)
        after = json.loads(local_execute(tmp_path, action("snapshot")).stdout)
        return (response.returncode != 0, result.get("status"), bool(result.get("error")),
                source.read_bytes() == original, source.stat().st_mtime_ns == before,
                versions == after)

    contract(observe, (True, "tool_error", True, True, True, True))


@pytest.mark.parametrize("path,original,new", [
    ("module.py", b"def value():\n    return 1\n", "def value():\n    return 2\n"),
    ("notes.md", b"# Original\n", "This is deliberately not Python: (\n"),
], ids=["valid-python", "non-python"])
def test_a02_valid_python_and_non_python_edits_still_work(tmp_path, path, original, new):
    source = tmp_path / path
    source.write_bytes(original)

    def observe():
        response = local_execute(tmp_path, edit(path, original, original.decode(), new))
        result = json.loads(response.stdout)
        return response.returncode, source.read_text(), result.get("sha256")

    contract(observe, (0, new, sha256(new.encode())))


def test_a03_invalid_existing_python_can_be_repaired(tmp_path):
    source = tmp_path / "module.py"
    original = b"def value(:\n    return 1\n"
    source.write_bytes(original)

    def observe():
        response = local_execute(tmp_path, edit("module.py", original, "value(:", "value():"))
        return response.returncode, source.read_text()

    contract(observe, (0, "def value():\n    return 1\n"))


@pytest.mark.parametrize("reason,old,bad_hash,original", [
    ("hash_mismatch", "return 1", True, b"def value():\n    return 1\n"),
    ("anchor_missing", "return 999", False, b"def value():\n    return 1\n"),
    ("anchor_ambiguous", "1", False, b"def value():\n    return 1 + 1\n"),
], ids=["hash-mismatch", "anchor-missing", "anchor-ambiguous"])
def test_a04_edit_conflict_identifies_the_specific_repair_without_mutating(tmp_path, reason, old, bad_hash, original):
    source = tmp_path / "module.py"
    source.write_bytes(original)
    selected = edit("module.py", original, old, "return 2")
    if bad_hash:
        selected["expected_sha256"] = "0" * 64

    def observe():
        response = local_execute(tmp_path, selected)
        result = json.loads(response.stdout)
        return (response.returncode != 0, result.get("code"), result.get("conflict_reason"),
                result.get("sha256"), result.get("match_count"), bool(result.get("repair")),
                source.read_bytes() == original)

    contract(observe, (True, "edit_conflict", reason, sha256(original), original.decode().count(old), True, True))


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
@pytest.mark.parametrize("failure", ["hash_mismatch", "anchor_missing"])
def test_a05_conflict_read_and_small_corrected_edit_can_reach_submission(pilot_session, mode, failure):
    run, tree, _ = pilot_session
    original = (tree / "module.py").read_bytes()
    wrong = edit("module.py", original, "UNIQUE_IMPLEMENTATION = 1", "UNIQUE_IMPLEMENTATION = 2")
    if failure == "hash_mismatch":
        wrong["expected_sha256"] = "0" * 64
    else:
        wrong["old"] = "UNIQUE_IMPLEMENTATION = 999"
    corrected = edit("module.py", original, "UNIQUE_IMPLEMENTATION = 1", "UNIQUE_IMPLEMENTATION = 2")

    def observe():
        result, _, directory = run([
            action("read_file", path="module.py", start=1), wrong,
            action("read_file", path="module.py", start=1), corrected, SUBMIT,
        ], mode=mode)
        conflict = read(directory / "steps/0001-tool.json")["result"]
        fixed = read(directory / "steps/0003-tool.json")["result"]
        return (result["status"], conflict.get("code"), fixed.get("status"),
                result["process_metrics"]["first_production_change_call"],
                (tree / "module.py").read_text(), bool((directory / "full.patch").read_text()))

    contract(observe, ("submitted", "edit_conflict", "completed", 4, "UNIQUE_IMPLEMENTATION = 2\n", True))


def test_a06_unchanged_conflict_read_cycles_still_terminate_without_mutation(pilot_session):
    run, tree, _ = pilot_session
    original = (tree / "module.py").read_bytes()
    wrong = edit("module.py", original, "missing anchor", "UNIQUE_IMPLEMENTATION = 2")
    cycle = [action("read_file", path="module.py", start=1), wrong]

    def observe():
        result, _, directory = run(cycle * 10)
        return (result["status"], result["model_calls"] < 20,
                (tree / "module.py").read_bytes() == original,
                result["process_metrics"]["first_production_change_call"],
                (directory / "full.patch").read_text())

    contract(observe, ("stalled", True, True, None, ""))


@pytest.mark.parametrize("broken", [
    "import missing_pilot_dependency\n",
    "def test_broken(:\n    pass\n",
], ids=["import", "syntax"])
def test_a07_collection_error_target_can_be_used_after_repair(tmp_path, broken):
    manager = LocalSandbox(tmp_path, False)
    source = manager.tree / "test_broken.py"
    source.write_text(broken)

    def observe():
        failed = workspace.run_tests(manager, object(), ["test_broken.py"], 20, 12000)
        diagnostic = failed["diagnostics"]["errors"][0]
        target = diagnostic.get("id")
        source.write_text("def test_repaired(): assert True\n")
        rerun = workspace.run_tests(manager, object(), [target], 20, 12000) if target else {}
        return (failed["observation"], diagnostic["phase"], target,
                rerun.get("observation"), rerun.get("diagnostics", {}).get("counts", {}).get("passed"))

    contract(observe, ("invalid_test_run", "setup_or_collection", "test_broken.py", "pass", 1))


def test_a08_unknown_collection_target_is_not_invented():
    def observe():
        suite = ET.Element("testsuite")
        case = ET.SubElement(suite, "testcase")
        ET.SubElement(case, "error", message="collection interrupted").text = "Unknown collection origin"
        diagnostic = workspace.test_diagnostics(ET.tostring(suite, encoding="unicode"))["errors"][0]
        return diagnostic.get("id"), diagnostic["message"], diagnostic["phase"]

    contract(observe, (None, "collection interrupted", "setup_or_collection"))


def test_a09_recorded_runtime_id_keeps_lowercase_classes_and_parameters():
    target = "tests/test_api.py::lowercase::test_value[a.b/é;]"

    def observe():
        suite = ET.Element("testsuite")
        case = ET.SubElement(suite, "testcase", classname="tests.test_api.lowercase", name="test_value[a.b/é;]")
        properties = ET.SubElement(case, "properties")
        ET.SubElement(properties, "property", name="study_nodeid", value=target)
        ET.SubElement(case, "failure", message="AssertionError: wrong value")
        return workspace.test_diagnostics(ET.tostring(suite, encoding="unicode"))["errors"][0]["id"]

    contract(observe, target)


@pytest.mark.parametrize("cause", [
    "ModuleNotFoundError: No module named 'pydantic_settings'",
    "OSError: [Errno 101] Network is unreachable",
    "TypeError: Column.__init__() got an unexpected keyword argument 'highlight'",
], ids=["missing-package", "network-isolation", "snapshot-defect"])
@pytest.mark.parametrize("fallback", [False, True], ids=["normal-context", "reduced-context"])
def test_a10_original_baseline_cause_survives_context_reduction(cause, fallback):
    collection_error = cause.startswith("ModuleNotFoundError")
    counts = {"passed": 1, "failed": 0 if collection_error else 1,
              "errors": 1 if collection_error else 0, "skipped": 0}
    baseline = {
        "observation": "invalid_test_run" if collection_error else "test_failure",
        "diagnostics": {"collected": 2, "counts": counts,
                        "errors": [{"id": "tests/test_existing.py::test_existing", "message": cause}]},
        "scope": "Original visible suite; existing failures are not new regressions.",
    }
    ledger = {"visible_baseline": baseline, "note": "Optional old notes " * (1000 if fallback else 1)}
    before = copy.deepcopy(ledger)

    def observe():
        messages = session_context("Mandatory framework guide", "Mandatory issue", [], ledger, 1800)
        sent = json.dumps(messages, ensure_ascii=False)
        serialized_counts = json.dumps(counts, sort_keys=True, separators=(",", ":"))
        # The ledger is embedded in the user message, so inspect that content
        # rather than its escaped outer transport representation.
        counts_retained = serialized_counts in messages[1]["content"]
        return (cause in sent, baseline["scope"] in sent,
                "Mandatory framework guide" in sent, "Mandatory issue" in sent,
                counts_retained, len(sent.encode()) <= 1800, ledger == before)

    contract(observe, (True, True, True, True, True, True, True))


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
def test_a11_rejected_syntax_edit_does_not_poison_session_or_production_metrics(pilot_session, mode):
    run, tree, _ = pilot_session
    original = (tree / "module.py").read_bytes()
    invalid = edit("module.py", original, "UNIQUE_IMPLEMENTATION = 1", "UNIQUE_IMPLEMENTATION = (")
    corrected = edit("module.py", original, "UNIQUE_IMPLEMENTATION = 1", "UNIQUE_IMPLEMENTATION = 2")

    def observe():
        result, client, directory = run([
            action("read_file", path="module.py", start=1), invalid,
            action("read_file", path="module.py", start=1), corrected, SUBMIT,
        ], mode=mode)
        rejected = read(directory / "steps/0001-tool.json")["result"]
        delivered = json.loads(client.requests[2]["messages"][-1]["content"])
        fixed = read(directory / "steps/0003-tool.json")["result"]
        return (result["status"], rejected.get("status"), delivered.get("status"), fixed.get("status"),
                result["process_metrics"]["first_production_change_call"],
                (tree / "module.py").read_text())

    contract(observe, ("submitted", "tool_error", "tool_error", "completed", 4, "UNIQUE_IMPLEMENTATION = 2\n"))
