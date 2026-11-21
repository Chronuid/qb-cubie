"""GUTACHTEN 9.2: content comparisons must survive unchanged stat signatures."""

import filecmp
import os

import pytest

from qb_cubie import EBT, WorldState


class ReusedWorkspace:
    """Keep comparison paths stable across runs; pytest owns their cleanup."""

    def __init__(self, root):
        self.root = root
        self.cleanups = 0

    def setup(self, state):
        pass

    def execute(self, target, args, kwargs):
        return target(*args, **kwargs)

    def get_state(self):
        return WorldState(returns=None, fs=str(self.root), arena=str(self.root))

    def teardown(self):
        self.cleanups += 1


@pytest.fixture(autouse=True)
def isolated_filecmp_cache():
    filecmp.clear_cache()
    yield
    filecmp.clear_cache()


@pytest.mark.parametrize("scope", ["file", "directory", "arena"])
@pytest.mark.parametrize("changed_side", ["actual", "reference"])
@pytest.mark.parametrize("content", [b"evil", b"good"], ids=["changed", "unchanged"])
def test_repeated_ebt_reads_current_bytes_at_the_same_paths(
    tmp_path, scope, changed_side, content,
):
    actual, reference = tmp_path / "actual", tmp_path / "reference"
    for root in (actual, reference):
        (root / "nested").mkdir(parents=True)
        (root / "nested/report.bin").write_bytes(b"good")
    if scope == "file":
        post = WorldState(fs={"nested/report.bin": str(reference / "nested/report.bin")})
    elif scope == "directory":
        post = WorldState(fs={"nested": str(reference / "nested")})
    else:
        post = WorldState(arena=str(reference))
    arena = ReusedWorkspace(actual)
    case = EBT(target=lambda: None, arena=arena, post=post, reporter=None)
    first = case.run()
    assert first.evaluation is True and first.traces[0].diffs is None
    changed = (actual if changed_side == "actual" else reference) / "nested/report.bin"
    before = changed.stat()
    changed.write_bytes(content)
    os.utime(changed, ns=(before.st_atime_ns, before.st_mtime_ns))
    after = changed.stat()
    assert (after.st_size, after.st_mtime_ns) == (before.st_size, before.st_mtime_ns)
    equal = (actual / "nested/report.bin").read_bytes() == (reference / "nested/report.bin").read_bytes()
    second = case.run()
    assert arena.cleanups == 2
    assert first.evaluation is True and first.traces[0].diffs is None
    assert second.evaluation is equal
    assert second.traces[0].evaluation is equal
    if equal:
        assert second.traces[0].diffs is None
    else:
        key = "arena" if scope == "arena" else "fs"
        diff = second.traces[0].diffs[key]
        if scope != "arena":
            diff = diff["nested/report.bin" if scope == "file" else "nested"]
        modified = {"file": ".", "directory": "report.bin", "arena": "nested/report.bin"}[scope]
        assert diff == {"modified": [modified]}
