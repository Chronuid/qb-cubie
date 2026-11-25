"""**Tries to** specify Cycle 1 workspace discovery, excludes, atomic writes, WorkspaceView, and integrations."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import libcst as cst
import pytest

from qb_cubie import CstLinter, CstRule, EBT, ExceptionExpectation, TempFS, WorldState
from qb_cubie.core.services import DocEnsurance, DocFrame

pytestmark = pytest.mark.services


def _workspace_module() -> Any:
    """Lazily imports qb_cubie.core.service_core.workspace so Phase-Red collection stays clean."""
    return importlib.import_module("qb_cubie.core.service_core.workspace")


# ---------- Stateless Adapters (TempFS-kompatible Top-Level-Helfer) ---------------------------------------------------


def _run_find_project_root_scenario(case: str) -> dict[str, Any]:
    """Seeds nested folders in TempFS and verifies find_project_root markers and stop_at_cwd."""
    ws = _workspace_module()
    root = Path.cwd().resolve()
    if case == "pyproject_upward":
        (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
        deep = root / "docs" / "services"
        deep.mkdir(parents=True)
        found = ws.find_project_root(start=deep)
        return {"matched_root": found == root}
    if case == "nested_assets_marker":
        (root / "docs" / ".assets").mkdir(parents=True)
        nested = root / "docs" / "guides"
        nested.mkdir(parents=True)
        found = ws.find_project_root(start=nested, markers=("pyproject.toml", "docs/.assets"))
        return {"matched_root": found == root}
    if case == "stop_at_cwd":
        outer = root / "outer"
        inner_cwd = outer / "inner"
        deep = inner_cwd / "sub"
        deep.mkdir(parents=True)
        (outer / "pyproject.toml").write_text("[project]\nname='outer'\n", encoding="utf-8")
        import os

        os.chdir(inner_cwd)
        found = ws.find_project_root(start=deep, stop_at_cwd=True)
        return {"stopped_below_outer": found == deep.resolve(), "did_not_escape_cwd": found != outer.resolve()}
    leaf = root / "isolated"
    leaf.mkdir()
    found = ws.find_project_root(start=leaf, markers=("never_present.marker",), stop_at_cwd=True)
    return {"fallback_to_start": found == leaf.resolve()}


def _call_normalize_excludes(excludes: Any, base: Any = None) -> frozenset[str]:
    """Invokes service_core.workspace.normalize_excludes with optional custom base."""
    ws = _workspace_module()
    if base is None:
        return ws.normalize_excludes(excludes)
    return ws.normalize_excludes(excludes, base=base)


def _call_is_excluded(rel_path: str, root_name: str, excludes: tuple[str, ...]) -> bool:
    """Invokes service_core.workspace.is_excluded."""
    ws = _workspace_module()
    return ws.is_excluded(Path(rel_path), root_name, frozenset(excludes))


def _run_crawl_scenario(pattern: str, excludes: tuple[str, ...]) -> list[str]:
    """Seeds mixed .md and .py files in TempFS and returns sorted relative paths from crawl_files."""
    ws = _workspace_module()
    root = Path.cwd().resolve()
    for folder in ("docs", "docs/drafts", "src", ".venv"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text("# Root\n", encoding="utf-8")
    (root / "docs" / "b.md").write_text("# B\n", encoding="utf-8")
    (root / "docs" / "a.md").write_text("# A\n", encoding="utf-8")
    (root / "docs" / "drafts" / "wip.md").write_text("# WIP\n", encoding="utf-8")
    (root / ".venv" / "ignored.md").write_text("# Venv\n", encoding="utf-8")
    (root / "src" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    (root / "docs" / "drafts" / "skip.py").write_text("x = 2\n", encoding="utf-8")
    files = ws.crawl_files(root, pattern=pattern, excludes=frozenset(excludes))
    return [p.relative_to(root).as_posix() for p in files]


def _call_crawl_invalid_root(kind: str) -> Any:
    """Triggers STATE-GUARD errors in crawl_files for missing path or file target."""
    ws = _workspace_module()
    root = Path.cwd().resolve()
    if kind == "missing":
        return ws.crawl_files(root / "missing_dir")
    sample = root / "file.md"
    sample.write_text("# File\n", encoding="utf-8")
    return ws.crawl_files(sample)


def _run_load_sources_scenario(target: Any, allow_in_memory: bool, excludes: tuple[str, ...] = ()) -> list[dict[str, str]]:
    """Seeds a minimal docs folder in TempFS and projects load_sources FileSource records."""
    ws = _workspace_module()
    root = Path.cwd().resolve()
    (root / "docs" / "drafts").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
    (root / "docs" / "drafts" / "wip.md").write_text("# WIP\n", encoding="utf-8")
    sources = ws.load_sources(
        target,
        pattern="*.md",
        excludes=frozenset(excludes),
        allow_in_memory=allow_in_memory,
    )
    return [{"rel_path": s.rel_path, "content": s.content, "is_mem": str(s.path == "IN_MEMORY")} for s in sources]


def _run_workspace_view_scenario(mode: str) -> dict[str, bool]:
    """Tests both InMemoryWorkspaceView and FileSystemWorkspaceView against WorkspaceView protocol."""
    ws = _workspace_module()
    root = Path.cwd().resolve()
    if mode == "memory":
        view = ws.InMemoryWorkspaceView(
            root=Path("/virtual/repo"),
            paths=("docs/guide.md", "docs/.assets/cubie-small.png"),
        )
        return {
            "matches_protocol": isinstance(view, ws.WorkspaceView),
            "finds_exact_file": view.has_path("docs/guide.md"),
            "finds_dot_prefixed_file": view.has_path("./docs/.assets/cubie-small.png"),
            "finds_parent_dir": view.has_path("docs/.assets"),
            "rejects_missing_file": not view.has_path("docs/.assets/missing.png"),
        }
    (root / "docs" / ".assets").mkdir(parents=True)
    (root / "docs" / ".assets" / "logo.png").write_bytes(b"PNG")
    view = ws.FileSystemWorkspaceView(root=root)
    return {
        "matches_protocol": isinstance(view, ws.WorkspaceView),
        "finds_exact_file": view.has_path("docs/.assets/logo.png"),
        "finds_abs_path": view.has_path(root / "docs" / ".assets" / "logo.png"),
        "finds_parent_dir": view.has_path("docs/.assets"),
        "rejects_missing_file": not view.has_path("docs/.assets/absent.png"),
    }


# ======================================================================================================================
# 1. find_project_root (Eliminiert Duplikat D1)
# ======================================================================================================================


def test_ebt_find_project_root_markers_and_cwd_boundary() -> None:
    """Verifies upward marker search, nested markers, stop_at_cwd boundary, and fallback."""
    EBT(
        target=_run_find_project_root_scenario,
        arena=TempFS(),
        pre=[
            WorldState(args=("pyproject_upward",)),
            WorldState(args=("nested_assets_marker",)),
        ],
        post=WorldState(returns={"matched_root": True}),
        custom_id="service_core_workspace_find_root_markers",
    ).run()
    EBT(
        target=_run_find_project_root_scenario,
        arena=TempFS(),
        pre=WorldState(args=("stop_at_cwd",)),
        post=WorldState(returns={"stopped_below_outer": True, "did_not_escape_cwd": True}),
        custom_id="service_core_workspace_find_root_stop_at_cwd",
    ).run()
    EBT(
        target=_run_find_project_root_scenario,
        arena=TempFS(),
        pre=WorldState(args=("fallback",)),
        post=WorldState(returns={"fallback_to_start": True}),
        custom_id="service_core_workspace_find_root_fallback",
    ).run()


# ======================================================================================================================
# 2. normalize_excludes & is_excluded (Kills Mutant M1 & eliminates Duplikat D2)
# ======================================================================================================================


def test_ebt_normalize_excludes_merges_base_and_returns_frozenset() -> None:
    """Merges default/base excludes with user sequences into an immutable frozenset."""
    EBT(
        target=_call_normalize_excludes,
        pre=WorldState(args=(("experiments", "docs/drafts"), (".venv", ".git"))),
        post=WorldState(returns=frozenset({".venv", ".git", "experiments", "docs/drafts"})),
        custom_id="service_core_workspace_normalize_excludes_merge",
    ).run()
    EBT(
        target=_call_normalize_excludes,
        pre=WorldState(args=(None, (".venv",))),
        post=WorldState(returns=frozenset({".venv"})),
        custom_id="service_core_workspace_normalize_excludes_none",
    ).run()


def test_normalize_excludes_rejects_bare_string() -> None:
    """Mutant M1: bare strings, bytes, non-sequences, and non-string items raise TypeError STATE-GUARD."""
    EBT(
        target=_call_normalize_excludes,
        pre=[
            WorldState(args=("tests",)),
            WorldState(args=(b"tests",)),
            WorldState(args=(42,)),
            WorldState(args=(["docs", 123],)),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:.*excludes")),
        custom_id="service_core_workspace_normalize_excludes_m1_guard",
    ).run()


@pytest.mark.parametrize(
    "rel_path, root_name, excludes, expected",
    [
        ("experiments/study.md", "cubie", ("experiments",), True),
        ("docs/drafts/wip.md", "cubie", ("docs/drafts",), True),
        ("docs/guide.md", "cubie", ("docs/drafts",), False),
        ("guide.md", "docs", ("docs/guide.md",), True),
        ("tutorials/guide.md", "docs", ("docs/guide.md",), False),
        ("docs/nested.md", "docs", ("docs",), True),
        ("guide.md", "docs", ("", "/"), False),
    ],
    ids=[
        "segment-match",
        "subpath-match",
        "sibling-subpath-not-matched",
        "root-prefixed-exact-match",
        "root-prefixed-does-not-swallow-nested-basename",
        "inner-subfolder-named-like-root",
        "empty-and-slash-ignored",
    ],
)
def test_ebt_is_excluded_subpath_and_root_collision_semantics(
    rel_path: str, root_name: str, excludes: tuple[str, ...], expected: bool
) -> None:
    """Verifies segment, subpath, and root-name-prefixed exclusion semantics."""
    EBT(
        target=_call_is_excluded,
        pre=WorldState(args=(rel_path, root_name, excludes)),
        post=WorldState(returns=expected),
        custom_id=f"service_core_workspace_is_excluded_{rel_path}",
    ).run()


# ======================================================================================================================
# 3. crawl_files & load_sources (inkl. allow_in_memory-Guard gegen Tippfehler)
# ======================================================================================================================


def test_ebt_crawl_files_supports_md_and_py_with_excludes() -> None:
    """crawl_files deterministically sorts matched files for any glob pattern while honoring excludes."""
    EBT(
        target=_run_crawl_scenario,
        arena=TempFS(),
        pre=WorldState(args=("*.md", (".venv", "docs/drafts"))),
        post=WorldState(returns=["README.md", "docs/a.md", "docs/b.md"]),
        custom_id="service_core_workspace_crawl_md",
    ).run()
    EBT(
        target=_run_crawl_scenario,
        arena=TempFS(),
        pre=WorldState(args=("*.py", (".venv", "docs/drafts"))),
        post=WorldState(returns=["src/mod.py"]),
        custom_id="service_core_workspace_crawl_py",
    ).run()


def test_ebt_crawl_files_rejects_missing_or_non_directory_root() -> None:
    """Missing roots raise FileNotFoundError STATE-GUARD; file targets raise ValueError STATE-GUARD."""
    EBT(
        target=_call_crawl_invalid_root,
        arena=TempFS(),
        pre=WorldState(args=("missing",)),
        post=WorldState(raises=ExceptionExpectation(FileNotFoundError, match=r"STATE-GUARD:")),
        custom_id="service_core_workspace_crawl_missing_root",
    ).run()
    EBT(
        target=_call_crawl_invalid_root,
        arena=TempFS(),
        pre=WorldState(args=("file",)),
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_workspace_crawl_file_root",
    ).run()


def test_ebt_load_sources_respects_allow_in_memory_flag() -> None:
    """When allow_in_memory=False, every string is treated as a path; when True, prose loads in memory."""
    EBT(
        target=_run_load_sources_scenario,
        arena=TempFS(),
        pre=WorldState(args=("not a real file", False)),
        post=WorldState(raises=ExceptionExpectation(FileNotFoundError, match=r"STATE-GUARD:")),
        custom_id="service_core_workspace_load_sources_strict_path",
    ).run()
    EBT(
        target=_run_load_sources_scenario,
        arena=TempFS(),
        pre=WorldState(args=("# Heading\nBody", True)),
        post=WorldState(returns=[{"rel_path": "IN_MEMORY", "content": "# Heading\nBody", "is_mem": "True"}]),
        custom_id="service_core_workspace_load_sources_in_memory",
    ).run()
    EBT(
        target=_run_load_sources_scenario,
        arena=TempFS(),
        pre=WorldState(args=("docs", False, ("drafts",))),
        post=WorldState(returns=[{"rel_path": "guide.md", "content": "# Guide\n", "is_mem": "False"}]),
        custom_id="service_core_workspace_load_sources_directory",
    ).run()
    EBT(
        target=_run_load_sources_scenario,
        arena=TempFS(),
        pre=WorldState(args=("docs", False, ("guide.md", "drafts"))),
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_workspace_load_sources_empty_dir_guard",
    ).run()


def test_ebt_load_sources_rejects_invalid_target_types_and_empty_str() -> None:
    """Non-str/Path targets raise TypeError; blank strings raise ValueError."""
    EBT(
        target=_run_load_sources_scenario,
        arena=TempFS(),
        pre=WorldState(args=(12345, False)),
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:")),
        custom_id="service_core_workspace_load_sources_bad_type",
    ).run()
    EBT(
        target=_run_load_sources_scenario,
        arena=TempFS(),
        pre=WorldState(args=("   ", True)),
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_workspace_load_sources_blank_str",
    ).run()


# ======================================================================================================================
# 4. atomic_write_text (Kills Mutant M2 — Fault-Injection statt Subsumtion!)
# ======================================================================================================================


def test_ebt_atomic_write_text_writes_lf_and_replaces_cleanly(tmp_path: Path) -> None:
    """atomic_write_text writes UTF-8 text with LF newlines and leaves zero temporary files behind."""
    target = tmp_path / "sample.md"
    target.write_text("old content\n", encoding="utf-8")

    def run_write() -> dict[str, Any]:
        ws = _workspace_module()
        ws.atomic_write_text(target, "line1\nline2\n")
        return {
            "bytes": target.read_bytes(),
            "files": sorted(p.name for p in tmp_path.iterdir()),
        }

    EBT(
        target=run_write,
        post=WorldState(returns={"bytes": b"line1\nline2\n", "files": ["sample.md"]}),
        custom_id="service_core_workspace_atomic_write_happy",
    ).run()


def test_atomic_write_preserves_original_and_cleans_tmp_on_replace_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mutant M2: failed os.replace must preserve original content and clean up all temp files."""
    target = tmp_path / "doc.md"
    original = "ORIGINAL_CONTENT\n"
    replacement = "NEW_CONTENT\n"
    target.write_text(original, encoding="utf-8")

    def fail_replace(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("disk full")

    def run_faulted_write() -> dict[str, Any]:
        ws = _workspace_module()
        monkeypatch.setattr("os.replace", fail_replace)
        raised_os_error = False
        try:
            ws.atomic_write_text(target, replacement)
        except OSError as exc:
            raised_os_error = "disk full" in str(exc)
        return {
            "raised_os_error": raised_os_error,
            "content": target.read_text(encoding="utf-8"),
            "dir_entries": sorted(p.name for p in tmp_path.iterdir()),
        }

    EBT(
        target=run_faulted_write,
        post={
            "quantor": "all",
            "states": [
                WorldState(
                    returns={
                        "raised_os_error": True,
                        "content": original,
                        "dir_entries": ["doc.md"],
                    }
                ),
                WorldState(
                    returns=lambda res: res["content"] == replacement or not res["raised_os_error"],
                    expect=False,
                ),
            ],
        },
        custom_id="service_core_workspace_atomic_write_m2_fault_injection",
    ).run()


# ======================================================================================================================
# 5. WorkspaceView Protocol (FileSystemWorkspaceView & InMemoryWorkspaceView)
# ======================================================================================================================


@pytest.mark.parametrize("mode", ["memory", "filesystem"])
def test_ebt_workspace_view_implementations(mode: str) -> None:
    """Both InMemoryWorkspaceView and FileSystemWorkspaceView satisfy WorkspaceView.has_path."""
    keys = (
        ("matches_protocol", "finds_exact_file", "finds_dot_prefixed_file", "finds_parent_dir", "rejects_missing_file")
        if mode == "memory"
        else ("matches_protocol", "finds_exact_file", "finds_abs_path", "finds_parent_dir", "rejects_missing_file")
    )
    EBT(
        target=_run_workspace_view_scenario,
        arena=TempFS(),
        pre=WorldState(args=(mode,)),
        post=WorldState(returns=dict.fromkeys(keys, True)),
        custom_id=f"service_core_workspace_view_{mode}",
    ).run()


# ======================================================================================================================
# 6. Zyklus-1-Integrationen: DocEnsurance excludes-Guard, DocFrame atomic write, CstLinter subpath excludes
# ======================================================================================================================


def test_ebt_doc_ensurance_rejects_bare_string_excludes() -> None:
    """H2 Integration: DocEnsurance(excludes='tests') must raise TypeError STATE-GUARD (not iterate chars)."""

    def init_with_bad_excludes(bad_excludes: Any) -> Any:
        return DocEnsurance(target="# Hello\n", excludes=bad_excludes, reporter=None)

    EBT(
        target=init_with_bad_excludes,
        pre=[
            WorldState(args=("tests",)),
            WorldState(args=(b"tests",)),
            WorldState(args=(["docs", 123],)),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:.*excludes")),
        custom_id="service_core_integration_doc_ensurance_excludes_guard",
    ).run()


def test_ebt_docframe_update_uses_atomic_write_on_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """H2 Integration (M2): DocFrame.update() must write atomically via os.replace and preserve original on error."""
    proj = tmp_path / "proj"
    (proj / "docs" / ".assets").mkdir(parents=True)
    (proj / "pyproject.toml").write_text("[project]\nname='atomic'\n", encoding="utf-8")
    for asset in ("cubie-logo-written.png", "cubie-small.png"):
        (proj / "docs" / ".assets" / asset).write_bytes(b"PNG")
    readme = proj / "README.md"
    original = (
        '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# Atomic\n<!-- /qb:frame -->\n\n'
        'Body\n\n<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n'
    )
    readme.write_text(original, encoding="utf-8")

    def fail_replace(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("simulated replace failure")

    def run_faulted_update() -> dict[str, Any]:
        monkeypatch.setattr("os.replace", fail_replace)
        raised = False
        try:
            DocFrame.update(target=proj)
        except OSError as exc:
            raised = "simulated replace failure" in str(exc)
        return {
            "raised": raised,
            "original_intact": readme.read_text(encoding="utf-8") == original,
            "leftover_tmp": [p.name for p in proj.iterdir() if p.name.startswith(".README")],
        }

    EBT(
        target=run_faulted_update,
        post={
            "quantor": "all",
            "states": [
                WorldState(returns={"raised": True, "original_intact": True, "leftover_tmp": []}),
                WorldState(returns=lambda res: not res["raised"], expect=False),
            ],
        },
        custom_id="service_core_integration_docframe_atomic_write",
    ).run()


class _FlagEvalRule(CstRule):
    """Minimal CST probe rule flagging eval() calls."""

    def visit_Call(self, node: cst.Call) -> None:
        """Record a diagnostic on every eval() call."""
        if isinstance(node.func, cst.Name) and node.func.value == "eval":
            self.add_diagnostic(node, "PROBE-EVAL", "eval forbidden")


def test_ebt_cstlinter_honors_subpath_excludes(tmp_path: Path) -> None:
    """H2 Integration: CstLinter excludes=['docs/drafts'] must skip docs/drafts/*.py while scanning docs/active/*.py."""
    (tmp_path / "docs" / "drafts").mkdir(parents=True)
    (tmp_path / "docs" / "active").mkdir(parents=True)
    (tmp_path / "docs" / "drafts" / "ignored.py").write_text("eval('1')\n", encoding="utf-8")
    (tmp_path / "docs" / "active" / "checked.py").write_text("eval('2')\n", encoding="utf-8")

    def run_cst_subpath_check() -> list[str]:
        linter = CstLinter(rules=[_FlagEvalRule()], excludes=["docs/drafts"])
        return [Path(d.file_path).relative_to(tmp_path).as_posix() for d in linter.check(tmp_path)]

    EBT(
        target=run_cst_subpath_check,
        post=WorldState(returns=["docs/active/checked.py"]),
        custom_id="service_core_integration_cstlinter_subpath_excludes",
    ).run()
