"""Priority 3.5: recursive FS contracts include directories and entry kinds."""

from pathlib import Path

import pytest

from qb_cubie import EBT, TempFS, WorldState
from qb_cubie.reporter import PytestReporter


def create_tree(directories, files):
    for name in directories:
        Path(name).mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        path = Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


@pytest.mark.parametrize("expected_dirs, expected_files, actual_dirs, actual_files, changes", [
    (("out", "out/cache"), {}, ("out", "out/cache"), {}, {}),
    (("out", "out/cache"), {}, ("out",), {}, {"missing": ["cache"]}),
    (("out",), {}, ("out", "out/cache"), {}, {"unexpected": ["cache"]}),
    (("out", "out/a", "out/a/b"), {}, ("out", "out/a"), {}, {"missing": ["a/b"]}),
    (("out", "out/cache"), {}, ("out",), {"out/cache": b""}, {"modified": ["cache"]}),
    (("out",), {"out/report.csv": b""}, ("out", "out/report.csv"), {}, {"modified": ["report.csv"]}),
], ids=["equal-empty-directory", "missing-empty-directory", "extra-empty-directory",
        "missing-nested-empty-directory", "directory-became-file", "file-became-directory"])
def test_directory_entries_are_part_of_recursive_contract(
        tmp_path, monkeypatch, expected_dirs, expected_files, actual_dirs, actual_files, changes):
    reference = tmp_path / "reference"
    reference.mkdir()
    with monkeypatch.context() as context:
        context.chdir(reference)
        create_tree(expected_dirs, expected_files)
    # Independently observe the target before evaluating the same inputs in EBT.
    direct = tmp_path / "direct"
    direct.mkdir()
    with monkeypatch.context() as context:
        context.chdir(direct)
        assert create_tree(actual_dirs, actual_files) is None
    assert {p.relative_to(direct).as_posix() for p in direct.rglob("*") if p.is_dir()} == set(actual_dirs)
    assert {p.relative_to(direct).as_posix(): p.read_bytes()
            for p in direct.rglob("*") if p.is_file()} == actual_files
    arena = TempFS()
    result = EBT(target=create_tree, arena=arena,
                 pre=WorldState(args=(actual_dirs, actual_files)),
                 post=WorldState(returns=None, fs={"out": str(reference / "out")}),
                 reporter=None).run()
    assert arena.workspace_path is None
    assert result.evaluation is (not changes)
    trace = result.traces[0]
    assert trace.evaluation is result.evaluation
    assert (trace.diffs or {}).get("fs", {}).get("out", {}) == changes
    if changes:
        with pytest.raises(AssertionError, match="EBT-Assert failed") as error:
            PytestReporter().report(result)
        for names in changes.values():
            for name in names:
                assert f"out/{name}" in str(error.value)


def test_ignored_directory_excludes_its_entire_subtree(tmp_path):
    reference = tmp_path / "reference"
    reference.mkdir()
    case = EBT(target=create_tree, arena=TempFS(),
               pre=WorldState(args=(("out/cache/nested",), {"out/cache/debug.txt": b"ignored"})),
               post=WorldState(fs={"out": str(reference)}), reporter=None)
    case.FS_IGNORES = {"cache"}
    result = case.run()
    assert result.evaluation is True
    assert result.traces[0].diffs is None


def test_directory_outside_mapped_scope_is_not_checked(tmp_path):
    reference = tmp_path / "reference"
    reference.mkdir()
    result = EBT(target=create_tree, arena=TempFS(),
                 pre=WorldState(args=(("out", "unrelated/empty"), {})),
                 post=WorldState(fs={"out": str(reference)}), reporter=None).run()
    assert result.evaluation is True
    assert result.traces[0].diffs is None


def test_missing_explicitly_mapped_empty_directory_is_a_failure(tmp_path):
    reference = tmp_path / "empty"
    reference.mkdir()
    result = EBT(target=lambda: None, arena=TempFS(),
                 post=WorldState(fs={"out": str(reference)}), reporter=None).run()
    assert result.evaluation is False
    assert result.traces[0].diffs["fs"]["out"]["error"]
