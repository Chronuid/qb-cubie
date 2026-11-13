"""Proposed v9 acceptance seam; no controller policy is implemented here.

Only filesystem/test-service I/O and a fault-injectable persistence port are
shared or supplied. See V9_CASES.md for the deliberately red contract.
"""

import copy
import importlib
import json

import pytest
from v6_support import Clock, contract
from v6_support import outcome as service_outcome
from v8_support import BROKEN, FIXED, GUIDES, ISSUE, MANIFEST, NODE, REGRESSION
from v8_support import IO as FileIO
from v8_support import test_source as source_for_arm

COMMON = {"find_paths", "search_content", "read_file", "read_evidence"}
ALLOWED = {
    "analysis": COMMON | {"repo_overview", "read_environment", "finish"},
    "qa": COMMON | {"edit_tests", "collect_tests", "ask_analysis", "finish"},
    "dev": COMMON | {"edit_source", "run_tests", "ask_analysis", "request_test_change", "finish"},
}
HEADINGS = ["# Issue", "# Current Role & Task", "# Discovered Code & Evidence", "# Latest Test Results"]
QA_NOTES = "Input: double(2). Expected: 4. Reason: REQ-1 explicitly requires double(2) == 4."


def outcome(*args, **kwargs):
    """Runner evidence is keyed by collected node, never a model-generated ID."""
    result = service_outcome(*args, **kwargs)
    result["case_results"] = {NODE: result["case_results"].pop("C-1")}
    return result


def prompt(request):
    return next(m["content"] for m in request["messages"] if m["role"] == "user")


def model_text(request):
    return json.dumps({key: request[key] for key in ("messages", "history")}, ensure_ascii=False)


def tool_names(request):
    return {item["properties"]["action"]["const"] for item in request["schema"]["oneOf"]}


class Store:
    """Save raw transaction envelopes, or fail before the transaction is saved.

    The controller owns evidence selection, transaction content and committing
    its in-memory state. This port knows nothing about roles or handoffs.
    """

    def __init__(self, directory):
        self.directory = directory
        self.transactions = []
        self.fail = False

    def __call__(self, transaction):
        if self.fail:
            raise OSError("PERSISTENCE_UNAVAILABLE")
        self.directory.mkdir(parents=True, exist_ok=True)
        data = copy.deepcopy(transaction)
        (self.directory / f"{len(self.transactions):04d}.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8",
        )
        self.transactions.append(data)


class IO(FileIO):
    def execute_pytest(self, action):
        result = super().execute_pytest(action)
        result["case_results"] = {NODE: result["case_results"].pop("C-1")}
        return result


class Harness:
    def __init__(self, directory, *, mode="cubie", real_tests=False, baseline=None, **policy):
        # Resolve inside the EBT target: all tests collect without a v9 module.
        try:
            module = importlib.import_module("testguided_study.team_v9")
        except ModuleNotFoundError as error:
            if error.name != "testguided_study.team_v9":
                raise
            pytest.fail("V9 not implemented: testguided_study.team_v9.V9TeamController; see V9_CASES.md",
                        pytrace=False)
        self.directory = directory
        self.root = directory / "workspace"
        self.root.mkdir(parents=True)
        self.mode = mode
        for name, text in {
            "src/calc.py": BROKEN,
            "tests/test_calc.py": "# " + QA_NOTES + "\n" + source_for_arm(mode),
            "tests/test_old.py": "from src.calc import double\n\ndef test_old():\n    assert double(1) == 2\n",
            "tests/fixtures/input.txt": "2\n", "conftest.py": "# fixture\n",
            "pytest.ini": "[pytest]\n", "environment.json": '{"python": "3.13"}\n',
            "private/PRIVATE_SENTINEL.py": "PRIVATE_CONTENT_SENTINEL = 4\n",
            "src/literal.py": 'header\n\\d+[x]\n"None"\n',
        }.items():
            self.write(name, text)
        self.clock = Clock()
        self.io = IO(self.root, self.clock, real_tests=real_tests)
        self.store = Store(directory / "transactions")
        self.team = module.V9TeamController(
            workspace=self.root, artifact_dir=directory / "archive", mode=mode,
            issue=ISSUE, guides=GUIDES, manifest=MANIFEST,
            policy={"wall_seconds": 1800, "context_bytes": 80000, "history_dialogs": 4,
                    "search_limit": 50, **policy},
            execute=self.io, persist=self.store, clock=self.clock,
            **({"baseline": baseline} if baseline is not None else {}),
        )

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def send(self, role, action, **payload):
        return self.team.dispatch(role, {"action": action, **payload})

    def ok(self, role, action, **payload):
        result = self.send(role, action, **payload)
        assert result["status"] == "completed", result
        return result

    def read(self, role="analysis", path="src/calc.py", start=1, end=2):
        return self.ok(role, "read_file", path=path, line_start=start, line_end=end)

    def snapshot(self):
        return copy.deepcopy(self.team.snapshot())

    def files(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file() and not p.is_symlink()}

    def orient(self, notes="double is in src/calc.py; use REQ-1 as the oracle.", **extra):
        self.read()
        return self.ok("analysis", "finish", notes=notes, **extra)

    def activate(self, role):
        if role == "qa":
            self.orient()
        elif role == "dev":
            self.suite()

    def deliver_suite(self, notes=QA_NOTES):
        self.ok("qa", "collect_tests", targets=[NODE])
        return self.ok("qa", "finish", test_targets=[NODE], regressions=[REGRESSION], notes=notes)

    def suite(self):
        self.orient()
        return self.deliver_suite()

    def run(self, result=None, *, baseline=False, regression=False, **extra):
        if not self.io.real_tests:
            self.io.results.append(result if result is not None else outcome())
        return self.ok("dev", "run_tests", targets=[REGRESSION if regression else NODE],
                       baseline=baseline, **extra)

    def red(self):
        self.suite()
        return self.run(outcome("assertion_failure", failed=[(NODE, "AssertionError", "assert 3 == 4")]))

    def edit(self, role="dev", path="src/calc.py", text=FIXED):
        old = (self.root / path).read_text()
        read = self.read(role, path, end=max(1, len(old.splitlines())))
        return self.ok(role, "edit_source" if role == "dev" else "edit_tests",
                       handle=read["handle"], new_text=text, reason="REQ-1")

    def repaired(self):
        red = self.red()
        self.edit()
        return red, self.run(), self.run(regression=True)

    def to_review(self):
        evidence = self.repaired()
        result = self.ok("dev", "finish", notes="Correct multiplication for REQ-1; focus and regression pass.")
        self.diff_ref = result["diff_ref"]
        return evidence

    def review(self, evidence):
        for item in evidence:
            self.ok("analysis", "read_evidence", ref=item["evidence_id"])
        self.ok("analysis", "read_evidence", ref=self.diff_ref)
        self.read()
        return self.send("analysis", "finish", verdict="verified",
                         notes="REQ-1 covered with justified oracle; final diff and current runs inspected.")

    def archive(self):
        return json.loads((self.directory / "archive/team.json").read_text())


__all__ = ["Harness", "contract"]
