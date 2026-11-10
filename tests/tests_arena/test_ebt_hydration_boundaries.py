"""Executable contracts for GUTACHTEN.md, section 8, priority 3.4.

These contracts deliberately have no xfail markers. See
hydration_cases/README.md for the trust model and the original red baseline.
All escape probes stay within pytest-owned temporary directories.
"""

import importlib.metadata
import os
import shutil
import sysconfig
import tempfile
import venv
from pathlib import Path

import cloudpickle
import pytest

from qb_cubie import EBT, CloudpickleCodec, PickleCodec, PyVenv, TempFS, WorldState


@pytest.fixture(scope="module")
def hydration_base(tmp_path_factory):
    """Provision a real, minimal Cloudpickle base offline, outside the repo."""
    base = tmp_path_factory.mktemp("hydration-codec-base")
    venv.EnvBuilder(with_pip=False, symlinks=True).create(base)
    site = Path(sysconfig.get_path("purelib", vars={"base": str(base), "platbase": str(base)}))
    shutil.copytree(Path(cloudpickle.__file__).parent, site / "cloudpickle")
    distribution = importlib.metadata.distribution("cloudpickle")
    metadata = next(
        entry for entry in distribution.files
        if entry.name == "METADATA" and entry.parent.name.endswith(".dist-info")
    )
    shutil.copytree(distribution.locate_file(metadata).parent, site / metadata.parent.name)
    return str(base)


@pytest.fixture(params=["tempfs", "pyvenv"])
def arena(request, tmp_path, monkeypatch):
    # ../ escapes land here, never in a shared /tmp or the repository.
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(scratch))
    if request.param == "tempfs":
        return TempFS()
    return PyVenv(env_path=request.getfixturevalue("hydration_base"), codec=CloudpickleCodec())


def _assert_rejected(arena, state, tmp_path, destination, *, entrypoint="ebt", expect=True):
    marker = tmp_path / "target-called"
    scratch = tmp_path / "scratch"
    original_entries = set(scratch.iterdir())

    def target():
        marker.write_text("executed", encoding="utf-8")
        return True

    case = EBT(arena=arena, target=target, pre=state, post=WorldState(returns=True),
               expect=expect, reporter=None)
    try:
        with pytest.raises(ValueError) as caught:
            if entrypoint == "standalone":
                arena.run(target, (), {}, state)
            else:
                case.run()
        # Diagnose the offending mapping, not just a generic filesystem error.
        assert str(destination) in str(caught.value)
    finally:
        assert not marker.exists(), "Invalid hydration must fail before target execution"
        assert arena.workspace_path is None
        assert set(scratch.iterdir()) == original_entries, "Workspace or escaped output leaked"
        assert case.run_trace is None, "Invalid configuration must not produce a successful trace"


@pytest.mark.parametrize("entrypoint", ["ebt", "standalone"])
@pytest.mark.parametrize("source_kind", ["file", "directory"])
@pytest.mark.parametrize("destination_kind", ["absolute", "parent", "nested-parent"])
def test_hydration_rejects_destinations_outside_workspace(
    arena, tmp_path, entrypoint, source_kind, destination_kind,
):
    source = tmp_path / "source"
    if source_kind == "directory":
        source.mkdir()
        (source / "payload.txt").write_text("replacement", encoding="utf-8")
    else:
        source.write_text("replacement", encoding="utf-8")

    outside = (tmp_path if destination_kind == "absolute" else tmp_path / "scratch") / "outside"
    if source_kind == "directory":
        outside.mkdir()
        protected = outside / "payload.txt"
    else:
        protected = outside
    protected.write_text("host original", encoding="utf-8")
    destination = {
        "absolute": str(outside),
        "parent": "../outside",
        "nested-parent": "nested/../../outside",
    }[destination_kind]

    try:
        _assert_rejected(arena, WorldState(fs={destination: str(source)}), tmp_path,
                         destination, entrypoint=entrypoint)
    finally:
        assert protected.read_text(encoding="utf-8") == "host original"
        if source_kind == "directory":
            assert sorted(path.name for path in outside.iterdir()) == ["payload.txt"]


@pytest.mark.parametrize("expect", [True, False])
def test_missing_escape_destination_is_not_created_even_for_negated_ebt(arena, tmp_path, expect):
    source = tmp_path / "source.txt"
    source.write_text("payload", encoding="utf-8")
    outside = tmp_path / "scratch" / "new-directory"
    destination = "../new-directory/payload.txt"
    try:
        _assert_rejected(arena, WorldState(fs={destination: str(source)}), tmp_path,
                         destination, expect=expect)
    finally:
        assert not outside.exists(), "Hydration created host directories outside the workspace"


def _symlink(link, target, *, directory=False):
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Symlink creation unavailable: {error}")


@pytest.mark.parametrize("link_kind", ["file", "directory", "dangling"])
@pytest.mark.parametrize("link_form", ["absolute", "relative"])
def test_copied_tree_cannot_expose_external_symlinks(arena, tmp_path, link_kind, link_form):
    # Match the workspace tree's depth so ../../../outside resolves to the
    # same pytest-owned host path in both source and hydrated copies.
    source = tmp_path / "sources" / "nested" / "source-tree"
    source.mkdir(parents=True)
    outside = tmp_path / "outside"
    if link_kind == "directory":
        outside.mkdir()
        (outside / "secret.txt").write_text("host secret", encoding="utf-8")
    elif link_kind == "file":
        outside.write_text("host secret", encoding="utf-8")
    # Both the source tree and the hydrated tree must resolve this link outside
    # themselves. The destination of a dangling link also needs validation.
    link_target = outside if link_form == "absolute" else "../../../outside"
    _symlink(source / "external", link_target, directory=link_kind == "directory")
    _assert_rejected(arena, WorldState(fs={"bundle": str(source)}), tmp_path, "bundle")


@pytest.mark.parametrize("link_kind", ["file", "directory"])
def test_later_mapping_cannot_write_through_copied_symlink(arena, tmp_path, link_kind):
    source = tmp_path / "source-tree"
    source.mkdir()
    outside = tmp_path / "outside"
    if link_kind == "directory":
        outside.mkdir()
        protected = outside / "victim.txt"
        destination = "bundle/external/victim.txt"
    else:
        protected = outside
        destination = "bundle/external"
    protected.write_text("host original", encoding="utf-8")
    _symlink(source / "external", outside, directory=link_kind == "directory")
    replacement = tmp_path / "replacement.txt"
    replacement.write_text("overwritten", encoding="utf-8")
    try:
        _assert_rejected(arena, WorldState(fs={
            "bundle": str(source), destination: str(replacement),
        }), tmp_path, "bundle")
    finally:
        assert protected.read_text(encoding="utf-8") == "host original"


def test_later_mapping_cannot_turn_earlier_internal_link_into_escape(arena, tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    # Initially entry resolves to the workspace root. Adding pivot later changes
    # entry's meaning: workspace/bundle/pivot/../.. now leaves the workspace.
    _symlink(first / "entry", "pivot/../..")
    _symlink(second / "pivot", "..", directory=True)
    _assert_rejected(arena, WorldState(fs={
        "bundle": str(first), "bundle/.": str(second),
    }), tmp_path, "bundle")


def test_parent_traversal_after_internal_link_cannot_escape(arena, tmp_path):
    source = tmp_path / "source-tree"
    source.mkdir()
    _symlink(source / "alias", "..", directory=True)
    outside = tmp_path / "outside"
    outside.write_text("host original", encoding="utf-8")
    replacement = tmp_path / "replacement.txt"
    replacement.write_text("overwritten", encoding="utf-8")
    # Lexical normalization would leave workspace/outside. Following alias first
    # actually moves the write two levels above the workspace instead.
    destination = "bundle/alias/../../outside"
    try:
        _assert_rejected(arena, WorldState(fs={
            "bundle": str(source), destination: str(replacement),
        }), tmp_path, destination)
    finally:
        assert outside.read_text(encoding="utf-8") == "host original"


def test_cyclic_links_are_rejected_before_execution(arena, tmp_path):
    source = tmp_path / "source-tree"
    source.mkdir()
    _symlink(source / "a", "b")
    _symlink(source / "b", "a")
    _assert_rejected(arena, WorldState(fs={"bundle": str(source)}), tmp_path, "bundle")


@pytest.mark.parametrize("mapping_kind", ["file", "tree", "directory-basename"])
def test_pyvenv_hydration_cannot_write_through_base_symlinks(tmp_path, monkeypatch, mapping_kind):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(scratch))
    # A minimal base suffices: rejection must precede interpreter lookup. This
    # models venv links without ever risking the actual host interpreter.
    base = tmp_path / "base"
    base.mkdir()
    protected = tmp_path / "host-file.txt"
    protected.write_text("host original", encoding="utf-8")
    _symlink(base / "payload.txt", protected)
    source = tmp_path / "payload.txt"
    source.write_text("replacement", encoding="utf-8")
    if mapping_kind == "tree":
        tree = tmp_path / "tree"
        tree.mkdir()
        shutil.copyfile(source, tree / source.name)
        destination, host_source = ".venv", tree
    elif mapping_kind == "directory-basename":
        destination, host_source = ".venv", source
    else:
        destination, host_source = ".venv/payload.txt", source
    arena = PyVenv(env_path=str(base), codec=PickleCodec())
    try:
        _assert_rejected(arena, WorldState(fs={destination: str(host_source)}), tmp_path, destination)
    finally:
        assert protected.read_text(encoding="utf-8") == "host original"


@pytest.mark.parametrize("source_kind", ["file", "directory"])
def test_trusted_host_sources_are_copied_to_relative_destinations(arena, tmp_path, source_kind):
    source = tmp_path / "source"
    destination = "nested/input.txt"
    if source_kind == "directory":
        source.mkdir()
        host_file = source / "input.txt"
        mapping = {"nested": str(source)}
    else:
        host_file = source
        mapping = {destination: str(source)}
    host_file.write_text("host original", encoding="utf-8")

    def target():
        path = Path(destination)
        before = path.read_text(encoding="utf-8")
        path.write_text("workspace changed", encoding="utf-8")
        return before

    trace = EBT(
        arena=arena, target=target, pre=WorldState(fs=mapping),
        post=WorldState(returns="host original", fs={
            destination: lambda path: path.read_text(encoding="utf-8") == "workspace changed",
        }),
    ).run()
    assert trace.evaluation is True
    assert trace.traces[0].outcome.returns == "host original"
    assert host_file.read_text(encoding="utf-8") == "host original"
    assert arena.workspace_path is None
    assert list((tmp_path / "scratch").iterdir()) == []


def test_relative_host_sources_still_resolve_from_host_cwd(arena, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("source.txt").write_text("host original", encoding="utf-8")
    trace = EBT(
        arena=arena, target=lambda: Path("nested/input.txt").read_text(encoding="utf-8"),
        pre=WorldState(fs={"nested/input.txt": "source.txt"}),
        post=WorldState(returns="host original"),
    ).run()
    assert trace.evaluation is True
    assert Path.cwd() == tmp_path


def test_internal_relative_symlinks_remain_usable_without_mutating_source(arena, tmp_path):
    source = tmp_path / "source-tree"
    source.mkdir()
    original = source / "original.txt"
    original.write_text("host original", encoding="utf-8")
    _symlink(source / "alias.txt", "original.txt")

    def target():
        alias = Path("bundle/alias.txt")
        before = alias.read_text(encoding="utf-8")
        alias.write_text("workspace changed", encoding="utf-8")
        return before, alias.is_symlink(), Path("bundle/original.txt").read_text(encoding="utf-8")

    trace = EBT(
        arena=arena, target=target, pre=WorldState(fs={"bundle": str(source)}),
        post=WorldState(returns=("host original", True, "workspace changed")),
    ).run()
    assert trace.evaluation is True
    assert original.read_text(encoding="utf-8") == "host original"


def test_internal_forward_and_dangling_links_are_preserved(arena, tmp_path):
    source = tmp_path / "source-tree"
    source.mkdir()
    _symlink(source / "alias.txt", "later.txt")
    _symlink(source / "later.txt", "original.txt")
    _symlink(source / "dangling.txt", "not-created.txt")
    (source / "original.txt").write_text("host original", encoding="utf-8")

    def target():
        return (Path("bundle/alias.txt").read_text(encoding="utf-8"),
                Path("bundle/dangling.txt").is_symlink(),
                Path("bundle/dangling.txt").exists())

    trace = EBT(arena=arena, target=target, pre=WorldState(fs={"bundle": str(source)}),
                post=WorldState(returns=("host original", True, False))).run()
    assert trace.evaluation is True


def test_workspace_does_not_prevent_target_host_access(arena, tmp_path, monkeypatch):
    """A passing capability demonstration, never a sandbox security promise."""
    outside = tmp_path / "host-file.txt"
    outside.write_text("host original", encoding="utf-8")
    monkeypatch.setenv("CUBIE_HYDRATION_TEST_TOKEN", "test-only-token")

    def target():
        before = outside.read_text(encoding="utf-8")
        outside.write_text("target changed host", encoding="utf-8")
        return before, os.environ["CUBIE_HYDRATION_TEST_TOKEN"], os.getpid()

    host_pid = os.getpid()
    trace = EBT(arena=arena, target=target, post=WorldState(
        returns=lambda result: result[:2] == ("host original", "test-only-token")
        and result[2] != host_pid,
    )).run()
    assert trace.evaluation is True
    assert outside.read_text(encoding="utf-8") == "target changed host"


def test_cloudpickle_result_deserialization_can_execute_in_host(arena):
    """Use a harmless PID probe to show that results must also be trusted."""
    class PidOnLoad:
        def __reduce__(self):
            return os.getpid, ()

    def target():
        return os.getpid(), PidOnLoad()

    host_pid = os.getpid()
    trace = EBT(arena=arena, target=target, post=WorldState(
        returns=lambda result: result[0] != host_pid and result[1] == host_pid,
    )).run()
    assert trace.evaluation is True
