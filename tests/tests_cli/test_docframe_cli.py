"""Verify the qb-cubie core CLI and module entrypoints for docframe update."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

from qb_cubie import EBT, WorldState
from qb_cubie.cli import main as cli_main


def _seed_doc_project(root: Path) -> Path:
    """Creates a minimal repository layout with stale qb:frame zones."""
    (root / "docs" / ".assets").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (root / "docs" / ".assets" / "cubie-logo-written.png").write_bytes(b"png")
    (root / "docs" / ".assets" / "cubie-small.png").write_bytes(b"png")
    readme = root / "README.md"
    readme.write_text(
        '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# Demo\n<!-- /qb:frame -->\n\n'
        'Body\n\n<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n',
        encoding="utf-8",
    )
    (root / "docs" / "GUIDE_Sample.md").write_text(
        '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# Sample\n<!-- /qb:frame -->\n\n'
        'Text\n\n<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n',
        encoding="utf-8",
    )
    return root


def test_cli_docframe_update_text_and_idempotence(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Runs cli_main(['docframe', 'update', ...]) twice and verifies text output and idempotence."""
    root = _seed_doc_project(tmp_path / "proj")
    first_code = cli_main(["docframe", "update", str(root)])
    first_out = capsys.readouterr().out
    second_code = cli_main(["docframe", "update", str(root)])
    second_out = capsys.readouterr().out
    assert first_code == 0
    assert "Updated 2 file(s):" in first_out
    assert "README.md" in first_out
    assert "docs/GUIDE_Sample.md" in first_out
    assert second_code == 0
    assert "Updated 0 file(s); all frames up to date." in second_out


def test_cli_docframe_update_json_and_excludes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verifies JSON output and repeatable --exclude filtering for docframe update."""
    root = _seed_doc_project(tmp_path / "proj_json")
    (root / "drafts").mkdir()
    (root / "drafts" / "notes.md").write_text(
        '<!-- qb:frame id="UNKNOWN_FRAME" zone="head" -->\n# Bad\n<!-- /qb:frame -->\n',
        encoding="utf-8",
    )
    code = cli_main(["docframe", "update", str(root), "--exclude", "drafts", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["passed"] is True
    assert payload["updated_files"] == ["README.md", "docs/GUIDE_Sample.md"]
    assert payload["catalog_entries"] == 2


def test_cli_docframe_update_reports_state_guard_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verifies that STATE-GUARD errors exit with status 2 and a clear stderr message."""
    missing = tmp_path / "does_not_exist"

    def _run_missing() -> int:
        return cli_main(["docframe", "update", str(missing)])

    EBT(target=_run_missing, pre=WorldState(), post=WorldState(returns=2)).run()
    err = capsys.readouterr().err
    assert "STATE-GUARD" in err


@pytest.mark.parametrize(
    "module_args",
    [
        ["-m", "qb_cubie", "docframe", "update"],
        ["-m", "qb_cubie.core.services.docframe", "update"],
        ["-m", "qb_cubie.core.services.doc_frame", "update"],
    ],
)
def test_module_entrypoints_execute_cleanly(tmp_path: Path, module_args: list[str]) -> None:
    """Executes all python -m CLI entrypoints in a subprocess without warnings."""
    root = _seed_doc_project(tmp_path / "proj_mod")
    proc = subprocess.run(
        [sys.executable, *module_args, str(root), "--format", "json"],
        capture_output=True, text=True, timeout=20, check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RuntimeWarning" not in proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["updated_files"] == ["README.md", "docs/GUIDE_Sample.md"]
