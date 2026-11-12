"""Ports and call sequences for the proposed v8 acceptance seam.

No role, recovery, version, budget or completion policy lives in this adapter.
Controller resolution happens inside the EBT target so collection stays usable.
See V8_CASES.md before implementing or adapting the seam.
"""

import copy
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from v6_support import IO as V6IO
from v6_support import Clock, contract, outcome

ISSUE = "REQ-1: double(1) returns 2 and double(2) returns 4. Preserve both cases."
NODE = "tests/test_calc.py::test_double"
REGRESSION = "tests/test_old.py::test_old"
BROKEN = "def double(value):\n    return value * 2 - 1\n"
FIXED = "def double(value):\n    return value * 2\n"
GUIDES = {
    "cubie": "CUBIE_GUIDE_SENTINEL: EBT(...).run(); assert result.evaluation is True.",
    "pytest": "PYTEST_GUIDE_SENTINEL: assert actual == expected.",
}
MANIFEST = {
    "src": "production", "tests": "tests", "conftest.py": "fixture",
    "pytest.ini": "test_configuration", "environment.json": "environment",
}
CASE = {
    "case_id": "C-1", "requirement_id": "REQ-1", "input": {"args": [2]},
    "expected": {"returns": 4}, "reason": "REQ-1 explicitly requires double(2) == 4.",
    "reason_ref": "issue:REQ-1", "pytest_node": NODE,
}
ALLOWED = {
    "analysis": {"repo_overview", "find_paths", "search_content", "read_file",
                 "read_environment", "read_evidence", "update_context", "finish"},
    "qa": {"read_file", "edit_tests", "collect_tests", "read_evidence", "ask_analysis", "finish"},
    "dev": {"read_file", "edit_source", "run_tests", "read_evidence", "ask_analysis",
            "request_test_change", "finish"},
}


def test_source(mode, *, expected=4):
    if mode == "cubie":
        return (
            "from qb_cubie import EBT, WorldState\nfrom src.calc import double\n\n"
            "def test_double():\n"
            "    result = EBT(target=double, pre=WorldState(args=(2,)), "
            f"post=WorldState(returns={expected}), reporter=None).run()\n"
            "    assert result.evaluation is True\n"
        )
    return f"from src.calc import double\n\ndef test_double():\n    assert double(2) == {expected}\n"


def tool_names(request):
    """Read the proposed JSON action schema; never supply missing tools."""
    return {item["properties"]["action"]["const"] for item in request["schema"]["oneOf"]}


def messages(request):
    return json.dumps(request["messages"], ensure_ascii=False)


class IO(V6IO):
    """Permissive boundary; controller must reject forbidden calls before I/O.

    Test-service responses are scripted except in the real-subprocess replay.
    The controller resolves edit handles and baseline workspaces before calling.
    """

    def __init__(self, root, clock, *, real_tests=False):
        super().__init__(root)
        self.clock = clock
        self.real_tests = real_tests
        self.run_seconds = 0

    def __call__(self, action):
        action = copy.deepcopy(action)
        if action["action"] == "read_file":
            action["start"] = action.pop("line_start", 1)
            action["end"] = action.pop("line_end", 10000)
        if action["action"] == "run_tests":
            self.clock.now += self.run_seconds
            if self.real_tests:
                self.results.append(self.execute_pytest(action))
            if action.get("baseline"):
                action["action"] = "check_baseline"
        return super().__call__(action)

    def execute_pytest(self, action):
        root = Path(action["workspace"]) if action.get("baseline") else self.root
        if not root.is_absolute():
            root = self.root.parent / root
        report = root / "result.xml"
        repo = Path(__file__).resolve().parents[2]
        env = os.environ | {
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "",
            "PYTHONPATH": os.pathsep.join([str(root), str(repo / "src")]),
        }
        process = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--noconftest", "-o", "addopts=",
             f"--junitxml={report}", *action["targets"]],
            cwd=root, env=env, text=True, capture_output=True, check=False, timeout=30,
        )
        assert process.returncode in {0, 1}, process.stdout + process.stderr
        cases = ET.parse(report).findall(".//testcase")
        assert not any(c.find("error") is not None or c.find("skipped") is not None for c in cases)
        failed = []
        for case in cases:
            failure = case.find("failure")
            if failure is not None:
                node = case.attrib["classname"].replace(".", "/") + ".py::" + case.attrib["name"]
                failed.append((node, "AssertionError", failure.attrib.get("message", "")))
        # These counters are a boundary fixture, not runtime EBT instrumentation.
        # The paired template tests separately calibrate real EBT execution.
        return outcome("assertion_failure" if failed else "pass", failed=failed, executed=len(cases))


class Harness:
    def __init__(self, directory, *, mode="cubie", real_tests=False, **policy):
        try:
            module = importlib.import_module("testguided_study.team_v8")
        except ModuleNotFoundError as error:
            if error.name != "testguided_study.team_v8":
                raise
            pytest.fail("V8 not implemented: testguided_study.team_v8.V8TeamController; see V8_CASES.md", pytrace=False)
        self.root = directory / "workspace"
        self.root.mkdir(parents=True)
        self.mode = mode
        for name, content in {
            "src/calc.py": BROKEN, "tests/test_calc.py": test_source(mode),
            "tests/test_old.py": "from src.calc import double\n\ndef test_old():\n    assert double(1) == 2\n",
            "tests/fixtures/input.txt": "2\n", "conftest.py": "# fixture\n",
            "pytest.ini": "[pytest]\n", "environment.json": '{"python": "3.13"}\n',
            "private/PRIVATE_SENTINEL.py": "PRIVATE_SENTINEL = 4\n",
        }.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.clock = Clock()
        self.io = IO(self.root, self.clock, real_tests=real_tests)
        self.team = module.V8TeamController(
            workspace=self.root, artifact_dir=directory / "archive", mode=mode,
            issue=ISSUE, guides=GUIDES, manifest=MANIFEST,
            policy={"wall_seconds": 1800, "context_bytes": 80000, **policy},
            execute=self.io, clock=self.clock,
        )

    def send(self, role, action, **payload):
        return self.team.dispatch(role, {"action": action, **payload})

    def ok(self, role, action, **payload):
        response = self.send(role, action, **payload)
        assert response["status"] == "completed", response
        return response

    def snapshot(self):
        return copy.deepcopy(self.team.snapshot())

    def files(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file() and not p.is_symlink()}

    def context(self, *, unknowns=()):
        read = self.ok("analysis", "read_file", path="src/calc.py", line_start=1, line_end=2)
        return {
            "requirements": [{"id": "REQ-1", "text": ISSUE, "refs": ["issue:REQ-1"]}],
            "facts": [{"text": "double is defined in src/calc.py", "refs": [read["evidence_id"]]}],
            "source_refs": [read["evidence_id"]], "test_paths": ["tests"],
            "test_command": "python -m pytest", "baseline": [], "hypotheses": [],
            "open_questions": list(unknowns),
        }

    def orient(self, **kwargs):
        return self.ok("analysis", "finish", delivery=self.context(**kwargs))

    def suite_delivery(self):
        return {"cases": [copy.deepcopy(CASE)], "targets": [NODE], "regressions": [REGRESSION]}

    def suite(self):
        self.orient()
        self.ok("qa", "collect_tests", targets=[NODE])
        return self.ok("qa", "finish", delivery=self.suite_delivery())

    def run(self, result=None, *, baseline=False, regression=False, **kwargs):
        if not self.io.real_tests:
            self.io.results.append(result if result is not None else outcome())
        return self.ok("dev", "run_tests", targets=[REGRESSION if regression else NODE],
                       baseline=baseline, **kwargs)

    def red(self):
        self.suite()
        return self.run(outcome("assertion_failure", failed=[(NODE, "AssertionError", "assert 3 == 4")]))

    def edit(self, role="dev", path="src/calc.py", new_text="    return value * 2\n", start=2, end=2):
        read = self.ok(role, "read_file", path=path, line_start=start, line_end=end)
        return self.ok(role, "edit_source" if role == "dev" else "edit_tests",
                       handle=read["handle"], new_text=new_text, reason="REQ-1")

    def repaired(self):
        red = self.red()
        self.edit()
        green = self.run()
        regression = self.run(regression=True)
        return red, green, regression

    def to_review(self):
        evidence = self.repaired()
        delivery = self.ok("dev", "finish", delivery={"summary": "Correct multiplication for REQ-1.",
                "evidence_refs": [r["evidence_id"] for r in evidence], "open_points": []})
        self.review_diff_ref = delivery["diff_ref"]
        return evidence

    def review(self, evidence):
        # Analyse must inspect the actual diff and details, not just counters.
        for ref in evidence:
            self.ok("analysis", "read_evidence", ref=ref["evidence_id"])
        self.ok("analysis", "read_evidence", ref=self.review_diff_ref)
        self.ok("analysis", "read_file", path="src/calc.py", line_start=1, line_end=2)
        return self.send("analysis", "finish", delivery={
            "verdict": "verified", "requirement_ids": ["REQ-1"],
            "reason": "Issue inputs are covered; focused and regression evidence match the final diff.",
            "evidence_refs": [r["evidence_id"] for r in evidence], "open_points": [],
        })


__all__ = ["Harness", "contract"]
