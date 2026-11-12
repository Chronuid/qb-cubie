"""Deterministic provider replay through the real runner and pytest subprocesses."""

import subprocess
from types import SimpleNamespace

import pytest
from test_v6_runtime import HostContainer, Replay, a
from v6_support import GUIDES, ISSUE, contract


class V7Replay(Replay):
    def __init__(self, directory):
        super().__init__(directory)
        actions = list(self.actions)
        # Retain the established real red/edit/green/review sequence, replacing
        # only the v6 two-action handoff and the explicitly changed read API.
        actions[:3] = [
            a("read_file", path="src/calc.py", line_start=1, line_end=2),
            lambda result: a("finish_orientation", requirements=[{
                "id": "REQ-1", "text": ISSUE, "refs": ["issue:REQ-1"], "status": "confirmed",
            }], source_refs=[result["evidence_id"]], test_entry_refs=[], hypotheses=[], unknowns=[]),
        ]
        for action in actions:
            if isinstance(action, dict) and action["action"] == "read_file" and "start" in action:
                action["line_start"] = action.pop("start")
                action["line_end"] = action.pop("end", action["line_start"])
        self.actions = iter(actions)


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
def test_a14_real_runner_reproduces_repairs_and_verifies_in_both_arms(tmp_path, mode):
    def observe():
        from testguided_study import agent
        from testguided_study.artifacts import read
        from testguided_study.design import default_design

        design = default_design(mode, GUIDES, version=7)
        root = tmp_path / "workspace"
        (root / "src").mkdir(parents=True)
        (root / "tests").mkdir()
        (root / "src/calc.py").write_text("def double(value):\n    return value * 2 - 1\n")
        for args in (["init", "-q"], ["add", "."],
                     ["-c", "user.name=Tests", "-c", "user.email=tests@example.invalid", "commit", "-qm", "baseline"],
                     ["tag", "_swegemma_baseline"]):
            subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, timeout=30)
        directory = tmp_path / "archive"
        directory.mkdir()
        client = V7Replay(directory)
        config = {
            "budgets": {"wall_seconds": 900, "model_calls": 48, "tool_calls": 96,
                        "context_bytes": 80000, "command_seconds": 30, "output_chars": 12000},
            "ollama": {"think": False, "temperature": 0.2, "num_ctx": 32768, "num_predict": 8192},
        }
        result = agent.develop(
            HostContainer(root), None, SimpleNamespace(problem_statement=ISSUE),
            {"mode": mode, "seed": 42, "run_id": "0001"}, config, GUIDES,
            directory, client=client, design=design,
        )
        observations = result["test_observations"]
        archived = read(directory / "team.json")
        return (result["status"], result["completion"]["allowed"],
                observations[0]["observation"], [r["observation"] for r in observations[1:]],
                (root / "src/calc.py").read_text(), archived["private_evaluation_required"],
                result["team"]["qualifications"],
                ("result.evaluation is True" in (root / "tests/test_calc.py").read_text()) == (mode == "cubie"))

    contract(observe, ("submitted", True, "assertion_failure", ["pass", "pass"],
                       "def double(value):\n    return value * 2\n", True,
                       {"reproduced": True, "verified": True}, True))
