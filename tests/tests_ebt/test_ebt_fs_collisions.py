"""FS collision contracts from GUTACHTEN.md, section 8, priority 1.3."""

# Distinct sources with one basename are ambiguous, even with equal contents.
# Reject them with ValueError; explicit destination mappings resolve ambiguity.
# These desired contracts deliberately have no xfail markers.

from functools import partial
from pathlib import Path
from unittest.mock import Mock

import pytest

from qb_cubie import EBT, WorldState
from qb_cubie.arenas.tempfs import TempFS


def mark_execution(marker):
    marker.write_text("executed", encoding="utf-8")


def read_workspace():
    return {str(path): path.read_text(encoding="utf-8")
            for path in Path(".").rglob("*") if path.is_file()}


@pytest.fixture(params=["files", "directories", "file-and-directory"])
def colliding_sources(tmp_path, request):
    sources = [tmp_path / side / "shared" for side in ("first", "second")]
    for index, source in enumerate(sources):
        source.parent.mkdir()
        if request.param == "directories" or (request.param == "file-and-directory" and index == 1):
            source.mkdir()
            (source / "content.txt").write_text(str(index), encoding="utf-8")
        else:
            source.write_text(str(index), encoding="utf-8")
    return sources


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize("collection", [list, tuple, set], ids=["list", "tuple", "set"])
@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reverse"])
def test_collisions_fail_before_arena_setup(
    tmp_path, colliding_sources, monkeypatch, field, collection, reverse,
):
    sources = list(reversed(colliding_sources)) if reverse else colliding_sources
    # Include trailing slashes to exercise directory basename normalization.
    fs = collection(str(source) + ("/" if source.is_dir() else "") for source in sources)
    arena, marker = TempFS(), tmp_path / "called"
    setup = Mock(wraps=arena.setup)
    monkeypatch.setattr(arena, "setup", setup)
    with pytest.raises(ValueError) as error:
        EBT(target=partial(mark_execution, marker), arena=arena,
            **{field: WorldState(fs=fs)}, reporter=None).run()
    message = str(error.value)
    assert field in message and "fs" in message and "shared" in message
    assert all(str(source) in message for source in sources)
    assert not marker.exists()
    setup.assert_not_called()
    assert arena.workspace_path is None


@pytest.mark.parametrize("field", ["pre", "post"])
def test_equal_contents_do_not_resolve_ambiguous_sources(tmp_path, field):
    sources = [tmp_path / side / "same.txt" for side in ("first", "second")]
    for source in sources:
        source.parent.mkdir()
        source.write_text("identical", encoding="utf-8")
    marker = tmp_path / "called"
    with pytest.raises(ValueError, match="same.txt"):
        EBT(target=partial(mark_execution, marker),
            **{field: WorldState(fs=sources)}, reporter=None).run()
    assert not marker.exists()


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize("multiprocessing", [False, True], ids=["singleprocess", "multiprocess"])
def test_global_negation_does_not_accept_collisions(tmp_path, monkeypatch, field, multiprocessing):
    monkeypatch.setattr("qb_cubie.multiprocessors.os.cpu_count", lambda: 2)
    marker = tmp_path / "called"
    with pytest.raises(ValueError, match="shared"):
        EBT(target=partial(mark_execution, marker), expect=False, reporter=None,
            multiprocessing=multiprocessing,
            **{field: WorldState(fs=["first/shared", "second/shared"])}).run()
    assert not marker.exists()


def test_later_state_collision_blocks_all_execution(tmp_path):
    marker = tmp_path / "called"
    with pytest.raises(ValueError, match="shared"):
        EBT(target=partial(mark_execution, marker), reporter=None,
            pre=[WorldState(), WorldState(fs=["first/shared", "second/shared"])]).run()
    assert not marker.exists()


@pytest.mark.parametrize("mismatch", [False, True], ids=["match", "mismatch"])
def test_explicit_targets_disambiguate_basenames(colliding_sources, mismatch):
    first, second = colliding_sources
    fs = {"left/shared": str(first), "right/shared": str(second)}
    post_fs = {**fs, "right/shared": str(first)} if mismatch else fs
    expected = {f"{side}/shared" + ("/content.txt" if source.is_dir() else ""): str(index)
                for index, (side, source) in enumerate(zip(("left", "right"), colliding_sources))}
    result = EBT(target=read_workspace, arena=TempFS(), pre=WorldState(fs=fs),
                 post=WorldState(fs=post_fs, returns=expected), reporter=None).run()
    assert result.evaluation is (not mismatch)
    assert len(result.traces) == 1
    assert result.traces[0].outcome.returns == expected
    if mismatch:
        assert "right/shared" in result.traces[0].diffs["fs"]
    else:
        assert not result.traces[0].diffs


@pytest.mark.parametrize("collection", [list, tuple, set], ids=["list", "tuple", "set"])
def test_unique_basenames_preserve_all_sources(tmp_path, collection):
    first, second = tmp_path / "first.txt", tmp_path / "second.txt"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")
    result = EBT(target=read_workspace, arena=TempFS(),
                 pre=WorldState(fs=collection([str(first), str(second)])),
                 post=WorldState(fs=collection([str(first), str(second)])), reporter=None).run()
    assert result.evaluation is True
    assert len(result.traces) == 1
    assert result.traces[0].outcome.returns == {"first.txt": "first", "second.txt": "second"}
    assert not result.traces[0].diffs


@pytest.mark.parametrize("collection", [list, tuple, set], ids=["list", "tuple", "set"])
def test_repeated_source_is_unambiguous(tmp_path, collection):
    source = tmp_path / "source"
    source.mkdir()
    (source / "content.txt").write_text("same", encoding="utf-8")
    fs = collection([source, str(source), str(source) + "/"])
    result = EBT(target=read_workspace, arena=TempFS(), pre=WorldState(fs=fs),
                 post=WorldState(fs=fs), reporter=None).run()
    assert result.evaluation is True
    assert result.traces[0].outcome.returns == {"source/content.txt": "same"}


@pytest.mark.parametrize("field", ["pre", "post"])
def test_collision_preserves_declared_fs_for_retry(tmp_path, field):
    first = WorldState(fs=["fixtures/unique"])
    second = WorldState(fs=["first/shared", "second/shared"])
    marker = tmp_path / "called"
    case = EBT(target=partial(mark_execution, marker), reporter=None,
               **{field: [first, second]})
    with pytest.raises(ValueError, match="shared"):
        case.run()
    assert first.fs == ["fixtures/unique"]
    assert second.fs == ["first/shared", "second/shared"]
    assert case.run_trace is None
    assert not marker.exists()
