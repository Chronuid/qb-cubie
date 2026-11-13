"""Test ports for v7 acceptance; no controller policy is implemented here.

The proposed extensions to the production seam are listed in V7_CASES.md.
Version selection is deliberately inside the EBT target, never at collection.
"""

import copy

from v6_support import CASE, GUIDES, ISSUE, MANIFEST, NODE, POLICY, Clock
from v6_support import IO as V6IO
from v6_support import Harness as V6Harness


class IO(V6IO):
    def __call__(self, action):
        action = copy.deepcopy(action)
        if action["action"] == "read_file":
            if "line_start" in action:
                action["start"] = action.pop("line_start")
            if "line_end" in action:
                action["end"] = action.pop("line_end")
        return super().__call__(action)


class Harness(V6Harness):
    def __init__(self, root, *, mode="cubie", **policy):
        from testguided_study.controller import TeamController
        from testguided_study.design import default_design

        design = default_design(mode, GUIDES, version=7)
        self.root = root / "workspace"
        self.root.mkdir(parents=True)
        files = {
            "src/calc.py": "def double(value):\n    return value * 2 - 1\n",
            "src/requests/utils.py": "def unquote(value):\n    return value\n",
            "tests/test_calc.py": (
                "from qb_cubie import EBT, WorldState\nfrom src.calc import double\n\n"
                "def test_double():\n"
                "    result = EBT(target=double, pre=WorldState(args=(2,)), "
                "post=WorldState(returns=4), reporter=None).run()\n"
                "    assert result.evaluation is True\n"
            ) if mode == "cubie" else (
                "from src.calc import double\n\ndef test_double():\n    assert double(2) == 4\n"
            ),
            "tests/test_old.py": "def test_old():\n    assert True\n",
            "conftest.py": "# fixture\n", "pytest.ini": "[pytest]\n",
            "environment.json": '{"python": "3.13"}\n',
        }
        for name, text in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        # Must never appear in the public card, candidates or model requests.
        (self.root / "private").mkdir()
        (self.root / "private/SECRET_SENTINEL.py").write_text("SECRET_SENTINEL = 4\n")
        self.clock = Clock()
        self.io = IO(self.root)
        self.team = TeamController(
            workspace=self.root, artifact_dir=root / "archive", mode=mode,
            issue=ISSUE, guides=GUIDES, manifest=MANIFEST,
            policy=POLICY | design["core"]["policy"] | policy,
            execute=self.io, clock=self.clock, design=design,
        )

    def package(self):
        source = self.ok("analysis", "read_file", path="src/calc.py", line_start=1, line_end=2)
        return {
            "requirements": [{"id": "REQ-1", "text": ISSUE,
                              "refs": ["issue:REQ-1"], "status": "confirmed"}],
            "source_refs": [source["evidence_id"]], "test_entry_refs": [],
            "hypotheses": [], "unknowns": [],
        }

    def orient(self):
        return self.ok("analysis", "finish_orientation", **self.package())

    def prepare_suite(self):
        self.ok("qa", "create_case", case=copy.deepcopy(CASE))
        return self.ok("qa", "collect_tests", targets=[NODE])

    def suite(self):
        self.orient()
        self.prepare_suite()
        self.ok("qa", "publish_suite", case_ids=["C-1"], targets=[NODE],
                expected_red={"C-1": "3 instead of required 4"})

    def edit(self, text="    return value * 2\n"):
        read = self.ok("dev", "read_file", path="src/calc.py", line_start=2, line_end=2)
        return self.ok("dev", "replace_region", handle=read["handle"], new_text=text, reason="REQ-1")

    def tick(self):
        """Runner boundary: enforce elapsed deadlines without another inference."""
        return self.team.advance()
