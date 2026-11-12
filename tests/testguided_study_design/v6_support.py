"""Deterministic I/O ports for the proposed v6 controller contract.

This module implements no permissions, state machine, evidence qualification,
budget or completion rules. Those belong to the production TeamController.
The proposed Python seam is documented in V6_CASES.md.
"""

import copy
import hashlib
from collections import deque

import pytest

from qb_cubie import EBT, WorldState

ISSUE = "REQ-1: double(2) returns 4."
NODE = "tests/test_calc.py::test_double"
REGRESSION_NODE = "tests/test_old.py::test_old"
POLICY = {
    "wall_seconds": 900, "model_calls": 48, "tool_calls": 96,
    "reserve_seconds": 180, "reserve_model_calls": 6,
    "revision_rounds": 3, "information_requests": 6,
    "repeat_limit": 3, "repair_calls": 1, "context_bytes": 80000,
}
GUIDES = {"pytest": "Use pytest assertions.", "cubie": "Run EBT and assert result.evaluation is True."}
MANIFEST = {
    "src": "production", "tests": "tests", "conftest.py": "fixture",
    "pytest.ini": "test_configuration", "environment.json": "environment",
    "artifacts": "artifacts",
}
CASE = {
    "case_id": "C-1", "requirement_id": "REQ-1", "reason_ref": "issue:REQ-1",
    "target": "calc.double", "setup": {}, "args": [2], "kwargs": {},
    "expected": {"returns": 4}, "reason": "The issue explicitly requires double(2) == 4.",
    "cleanup": None, "pytest_node": NODE,
}


def contract(target, expected):
    result = EBT(target=target, post=WorldState(returns=expected), reporter=None).run()
    assert result.evaluation is True


class Clock:
    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now


def outcome(observation="pass", *, failed=(), skipped=0, executed=1, ebt="checked"):
    """A test-service response, never a model-supplied observation."""
    green = observation == "pass"
    case_green = green or (bool(failed) and all(node != NODE for node, _, _ in failed))
    usage = {
        "ebt_executed": int(ebt in {"executed", "evaluated", "checked"}),
        "ebt_evaluated": int(ebt in {"evaluated", "checked"}),
        "ebt_passed": int(case_green and ebt in {"evaluated", "checked"}),
        "ebt_evaluation_checked": int(ebt == "checked"),
    }
    return {
        "status": "completed", "observation": observation,
        "exit_code": 0 if green else 1, "collection_only": False,
        "diagnostics": {"executed": executed, "counts": {
            "passed": executed if green else 0, "failed": len(failed), "skipped": skipped,
        }, "errors": [{"node": node, "type": kind, "message": message}
                       for node, kind, message in failed]},
        "case_results": {"C-1": {"executed": bool(executed), "outcome": "pass" if case_green else observation, **usage}},
        "framework_usage": usage,
    }


class IO:
    """Deliberately permissive filesystem/test port: the controller must guard it."""
    def __init__(self, root):
        self.root = root
        self.calls = []
        self.results = deque()
        self.runs = []

    def __call__(self, action):
        self.calls.append(copy.deepcopy(action))
        op = action["action"]
        if op in {"run_tests", "check_baseline"}:
            if not self.results:
                raise AssertionError("Unexpected test execution: no scripted test-service result")
            tree = self.root if op == "run_tests" else self.root.parent / action["workspace"]
            self.runs.append({
                "workspace": tree.resolve(),
                "source": (tree / "src/calc.py").read_bytes(),
                "tests": (tree / "tests/test_calc.py").read_bytes(),
                "fixture": (tree / "conftest.py").read_bytes(),
                "config": (tree / "pytest.ini").read_bytes(),
            })
            return copy.deepcopy(self.results.popleft())
        if op == "collect_tests":
            return {"status": "completed", "collection_only": True,
                    "observation": "collected", "test_ids": [NODE], "collected": 1}
        path = self.root / action["path"]
        if op == "read_file":
            data = path.read_bytes()
            lines = data.decode().splitlines(keepends=True)
            start, end = action.get("start", 1), action.get("end", len(lines))
            return {"status": "completed", "path": action["path"],
                    "text": "".join(lines[start - 1:end]), "start": start, "end": end, "total_lines": len(lines),
                    "sha256": hashlib.sha256(data).hexdigest()}
        if op in {"create_source_file", "create_test_file"}:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(action["content"], encoding="utf-8")
        elif op in {"delete_source_file", "delete_test_file"}:
            path.unlink()
        elif op == "replace_region":
            # The controller resolves the opaque handle to these concrete I/O fields.
            lines = path.read_text().splitlines(keepends=True)
            lines[action["start"] - 1:action["end"]] = [action["new_text"]]
            path.write_text("".join(lines), encoding="utf-8")
        else:
            raise AssertionError(f"Unexpected I/O operation: {op}")
        return {"status": "completed", "path": action["path"]}


class Harness:
    def __init__(self, root, **overrides):
        from testguided_study import controller

        cls = getattr(controller, "TeamController", None)
        if cls is None:
            pytest.fail("V6 not implemented: testguided_study.controller.TeamController is missing; "
                        "see tests/testguided_study_design/V6_CASES.md", pytrace=False)
        self.root = root / "workspace"
        self.root.mkdir(parents=True)
        extra_sources = overrides.pop("extra_sources", 0)
        for name, text in {
            "src/calc.py": "def double(value):\n    return value * 2 - 1\n",
            "tests/test_calc.py": (
                "from qb_cubie import EBT, WorldState\nfrom src.calc import double\n\n"
                "def test_double():\n"
                "    result = EBT(target=double, pre=WorldState(args=(2,)), "
                "post=WorldState(returns=4), reporter=None).run()\n"
                "    assert result.evaluation is True\n"
            ),
            "conftest.py": "# existing fixture\n", "pytest.ini": "[pytest]\n",
            "tests/test_old.py": "from src.calc import double\n\ndef test_old():\n    assert double(1) == 2\n",
            "environment.json": '{"python": "3.13", "revision": 1}\n',
        }.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        for index in range(extra_sources):
            (self.root / f"src/source_{index}.py").write_text(f"VALUE = {index}\n")
        self.clock = Clock()
        self.io = IO(self.root)
        self.team = cls(workspace=self.root, artifact_dir=root / "archive", mode=overrides.pop("mode", "cubie"),
                        issue=ISSUE, guides=GUIDES, manifest=MANIFEST, policy=POLICY | overrides,
                        execute=self.io, clock=self.clock)

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

    def orient(self):
        source = self.ok("analysis", "read_file", path="src/calc.py", start=1)
        self.ok("analysis", "publish_context", requirements=[{
            "id": "REQ-1", "text": ISSUE, "refs": ["issue:REQ-1"],
        }], sources=[source["evidence_id"]], baseline=[], open_questions=[])
        self.ok("analysis", "handoff", to="qa", job_id="J-QA", inputs=["REQ-1"],
                delivery="Case C-1 and collected suite", acceptance="Issue-linked double(2) == 4")

    def suite(self):
        self.orient()
        self.ok("qa", "create_case", case=copy.deepcopy(CASE))
        self.ok("qa", "collect_tests", targets=[NODE])
        self.ok("qa", "publish_suite", case_ids=["C-1"], targets=[NODE],
                expected_red={"C-1": "double(2) returns 3 instead of required 4"})

    def run(self, result=None, *, baseline=False, purpose="focused"):
        targets = [NODE, REGRESSION_NODE] if purpose == "regression" else [NODE]
        self.io.results.append(result or outcome(executed=len(targets)))
        return self.ok("dev", "check_baseline" if baseline else "run_tests", targets=targets, purpose=purpose)

    def red(self):
        self.suite()
        return self.run(outcome("assertion_failure", failed=[(NODE, "AssertionError", "assert 3 == 4")]))

    def edit(self, text="    return value * 2\n"):
        read = self.ok("dev", "read_file", path="src/calc.py", start=2, end=2)
        return self.ok("dev", "replace_region", handle=read["handle"], new_text=text, reason="REQ-1")

    def verified(self):
        self.red()
        self.edit()
        self.run()
        self.run(purpose="regression")
        self.ok("dev", "publish_implementation", requirement_ids=["REQ-1"], open_points=[])
        return self.ok("analysis", "verify_completion")
