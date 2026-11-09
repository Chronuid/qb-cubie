"""Distribution tests copied into an empty directory by scripts/check_wheel.py.

The filename deliberately avoids normal repository pytest discovery: these
checks must run against an installed wheel, without tests/conftest.py.
"""

import importlib
import importlib.metadata
import json
import os
import pkgutil
import sys
import venv
from pathlib import Path

import pytest

import cubie
from cubie import EBT, TempFS, WorldState
from cubie.protocols import ReviewData
from cubie.rbt import RBT


def test_imports_and_distribution():
    assert sys.prefix != sys.base_prefix
    package = Path(cubie.__file__).resolve()
    assert package.is_relative_to(Path(sys.prefix).resolve())
    distribution = importlib.metadata.distribution("cubie")
    assert package == Path(distribution.locate_file("cubie/__init__.py")).resolve()
    direct_url = json.loads(distribution.read_text("direct_url.json"))
    assert direct_url["url"].endswith(".whl")
    assert not direct_url.get("dir_info", {}).get("editable", False)
    assert all(hasattr(cubie, name) for name in cubie.__all__)
    for module in pkgutil.walk_packages(cubie.__path__, "cubie."):
        importlib.import_module(module.name)
    assert not list((package.parent / "arenas/arena_envs").glob("*/pyvenv.cfg"))


def test_ebt_accepts_matching_result():
    trace = EBT(target=sum, pre=WorldState(args=([1, 2, 3],)),
                post=WorldState(returns=6)).run()
    assert trace.evaluation is True


def test_ebt_rejects_wrong_result():
    with pytest.raises(AssertionError, match="EBT-Assert failed"):
        EBT(target=sum, pre=WorldState(args=([1, 2, 3],)),
            post=WorldState(returns=7)).run()


@pytest.mark.parametrize("accepted", [True, False])
def test_rbt_with_explicit_reviewer(accepted):
    class Reviewer:
        def review(self, target, check):
            return ReviewData(passed=accepted, report={"text": "wheel review"})

    review = RBT(target="example.py", check="Review", reviewer=Reviewer())
    if accepted:
        review.run()
    else:
        with pytest.raises(AssertionError, match="wheel review"):
            review.run()


def test_tempfs_runner_and_files(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("wheel", encoding="utf-8")

    def transform():
        text = Path("input.txt").read_text(encoding="utf-8").upper()
        Path("output.txt").write_text(text, encoding="utf-8")
        return text

    arena = TempFS()
    trace = EBT(
        target=transform, arena=arena,
        pre=WorldState(fs={"input.txt": str(source)}),
        post=WorldState(returns="WHEEL", fs={
            "output.txt": lambda path: path.read_text(encoding="utf-8") == "WHEEL",
        }),
    ).run()
    assert trace.evaluation is True
    assert arena.workspace_path is None
    assert source.read_text(encoding="utf-8") == "wheel"


def test_pyvenv_runner_and_packaged_phantom_hook(tmp_path):
    base = tmp_path / "base"
    venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(base)
    arena = cubie.PyVenv(env_path=str(base), codec=cubie.PickleCodec())
    trace = EBT(target="builtins:sum", arena=arena,
                pre=WorldState(args=([1, 2, 3],)),
                post=WorldState(returns=6)).run()
    assert trace.evaluation is True
    assert arena.workspace_path is None


def test_linter_runtime_dependencies():
    diagnostics = cubie.AstLinter(cubie.MyPy()).check("value: int = 'wrong'\n")
    assert any(diagnostic.rule_id == "assignment" for diagnostic in diagnostics)
