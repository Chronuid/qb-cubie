"""**Tries to** specify Cycle 2 cli_spec primitives, lazy CLI dispatch, docframe check, and docensurance CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from qb_cubie import EBT, ExceptionExpectation, WorldState
from qb_cubie.cli import main as cli_main
from qb_cubie.core.protocols import Diagnostic
from qb_cubie.core.service_core import SERVICE_REPORT_SCHEMA_VERSION, ServiceReport

pytestmark = pytest.mark.services
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _cli_spec_module() -> Any:
    """Lazily imports qb_cubie.core.service_core.cli_spec so Phase-Red collection stays clean."""
    return importlib.import_module("qb_cubie.core.service_core.cli_spec")


# ---------- Synthetic Workspace Fixtures ------------------------------------------------------------------------------


def _seed_docframe_workspace(root: Path, *, synced: bool = True) -> Path:
    """Creates a minimal project tree with optional DocFrame synchronization."""
    from qb_cubie.core.services.doc_frame import DocFrame

    (root / "docs" / ".assets").mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='cli-demo'\n", encoding="utf-8")
    (root / "docs" / ".assets" / "cubie-logo-written.png").write_bytes(b"png")
    (root / "docs" / ".assets" / "cubie-small.png").write_bytes(b"png")
    (root / "README.md").write_text(
        '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# Demo\n<!-- /qb:frame -->\n\n'
        'Body text.\n\n<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n',
        encoding="utf-8",
    )
    if synced:
        DocFrame.update(target=root)
    return root


def _seed_docensurance_workspace(root: Path, *, passing: bool = True) -> Path:
    """Creates a minimal project tree with a passing or failing Python Markdown code example."""
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='de-cli-demo'\n", encoding="utf-8")
    expected_out = "42" if passing else "99"
    (root / "docs" / "GUIDE_Calc.md").write_text(
        "# Calc Guide\n\n"
        "Diese ausreichend lange Erklärung beschreibt die folgende Berechnung eindeutig.\n\n"
        "```python\n"
        "print(21 * 2)\n"
        "```\n\n"
        "<details>\n"
        "<summary>Ergebnis</summary>\n\n"
        f"```text\n{expected_out}\n```\n"
        "</details>\n",
        encoding="utf-8",
    )
    return root


def _run_subprocess_with_blocked_modules(
    cli_args: list[str],
    blocked_prefixes: tuple[str, ...],
) -> dict[str, Any]:
    """Executes qb_cubie.cli.main in a fresh subprocess while blocking specified service packages."""
    probe = (
        "import sys\n"
        f"BLOCKED = {blocked_prefixes!r}\n"
        "class _Blocker:\n"
        "    def find_spec(self, fullname, path, target=None):\n"
        "        for prefix in BLOCKED:\n"
        "            if fullname == prefix or fullname.startswith(prefix + '.'):\n"
        "                raise ModuleNotFoundError(f'Blocked module: {fullname}')\n"
        "        return None\n"
        "sys.meta_path.insert(0, _Blocker())\n"
        "from qb_cubie.cli import main\n"
        "try:\n"
        f"    code = main({cli_args!r})\n"
        "except SystemExit as exc:\n"
        "    code = int(exc.code) if isinstance(exc.code, int) else 0\n"
        "leaked = [m for m in sys.modules if any(m == b or m.startswith(b + '.') for b in BLOCKED)]\n"
        "assert not leaked, f'Leaked blocked modules: {leaked}'\n"
        "raise SystemExit(code)\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


# ======================================================================================================================
# 1. service_core.cli_spec Contracts (Exit Codes, CommandResult, CommandSpec, Flag Builders, Render)
# ======================================================================================================================


def test_ebt_cli_spec_constants_and_command_result_contract() -> None:
    """Exit code constants and immutable CommandResult follow schema and hashability contracts."""

    def _probe() -> dict[str, Any]:
        spec = _cli_spec_module()
        report = ServiceReport(service="demo", target="docs/", passed=True, files_checked=2)
        result = spec.CommandResult(
            exit_code=spec.EXIT_OK,
            report=report,
            text="All good.",
            extra_json=(("custom", 7),),
        )
        return {
            "exit_codes": (spec.EXIT_OK, spec.EXIT_CHECK_FAILED, spec.EXIT_ERROR),
            "hashable": isinstance(hash(result), int),
            "text": spec.render_command_result(result, "text"),
            "json": json.loads(spec.render_command_result(result, "json")),
        }

    expected = {
        "exit_codes": (0, 1, 2),
        "hashable": True,
        "text": "All good.",
        "json": {
            "schema_version": SERVICE_REPORT_SCHEMA_VERSION,
            "service": "demo",
            "target": "docs/",
            "passed": True,
            "files_checked": 2,
            "changed_files": [],
            "diagnostics": [],
            "metadata": {},
            "custom": 7,
        },
    }
    EBT(
        target=_probe,
        pre=WorldState(),
        post=WorldState(returns=expected),
        custom_id="service_core_cli_spec_result_and_render",
    ).run()


def test_ebt_cli_spec_command_result_and_render_state_guards() -> None:
    """Invalid exit_code types/values and unsupported render formats raise STATE-GUARD errors."""

    def _make_result(exit_code: Any) -> Any:
        return _cli_spec_module().CommandResult(exit_code=exit_code)

    def _render(fmt: Any) -> str:
        spec = _cli_spec_module()
        return spec.render_command_result(spec.CommandResult(exit_code=0, text="ok"), fmt)

    EBT(
        target=_make_result,
        pre=[
            WorldState(args=(True,)),
            WorldState(args=(False,)),
            WorldState(args=("0",)),
            WorldState(args=(None,)),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:")),
        custom_id="service_core_cli_spec_exit_code_type_guard",
    ).run()
    EBT(
        target=_make_result,
        pre=WorldState(args=(-1,)),
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_cli_spec_exit_code_negative_guard",
    ).run()
    EBT(
        target=_render,
        pre=[WorldState(args=("xml",)), WorldState(args=("",))],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_cli_spec_render_format_guard",
    ).run()


def test_ebt_cli_spec_render_falls_back_to_format_service_report_text() -> None:
    """When CommandResult.text is empty, text rendering delegates to format_service_report_text."""

    def _probe() -> str:
        spec = _cli_spec_module()
        report = ServiceReport(
            service="lint_demo",
            target="docs/",
            passed=False,
            files_checked=1,
            diagnostics=(Diagnostic("docs/a.md", "R-1", 3, "Kaputt", severity="error", context="head"),),
        )
        return spec.render_command_result(spec.CommandResult(exit_code=1, report=report), "text")

    EBT(
        target=_probe,
        pre=WorldState(),
        post=WorldState(returns="[R-1] docs/a.md:3: Kaputt (head)"),
        custom_id="service_core_cli_spec_render_text_fallback",
    ).run()


def test_ebt_cli_spec_standard_arg_builders_and_command_spec_guards() -> None:
    """Standard flag builders bind target/excludes/format and CommandSpec validates its fields."""

    def _parse_standard(argv: list[str]) -> dict[str, Any]:
        spec = _cli_spec_module()
        parser = argparse.ArgumentParser(prog="probe")
        spec.add_standard_service_args(parser)
        ns = parser.parse_args(argv)
        return {"target": ns.target, "excludes": ns.excludes, "format": ns.format}

    def _make_spec(name: Any, help_text: Any, loader: Any) -> Any:
        return _cli_spec_module().CommandSpec(name=name, help=help_text, loader=loader)

    EBT(
        target=_parse_standard,
        pre=WorldState(args=(["docs", "--exclude", "drafts", "--exclude", "tmp", "--format", "json"],)),
        post=WorldState(returns={"target": "docs", "excludes": ["drafts", "tmp"], "format": "json"}),
        custom_id="service_core_cli_spec_standard_args",
    ).run()
    EBT(
        target=_make_spec,
        pre=[
            WorldState(args=("", "help", "a.b:CMD")),
            WorldState(args=("demo", "", "a.b:CMD")),
            WorldState(args=("demo", "help", "missing_colon")),
            WorldState(args=("demo", "help", ":CMD")),
            WorldState(args=("demo", "help", "a.b:")),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_cli_spec_command_spec_guards",
    ).run()


def test_ebt_service_cli_commands_implement_service_command_protocol() -> None:
    """Both doc_frame.cli:COMMAND and doc_ensurance.cli:COMMAND implement ServiceCommandProtocol."""

    def _probe() -> dict[str, Any]:
        spec = _cli_spec_module()
        df_cmd = importlib.import_module("qb_cubie.core.services.doc_frame.cli").COMMAND
        de_cmd = importlib.import_module("qb_cubie.core.services.doc_ensurance.cli").COMMAND
        return {
            "df_proto": isinstance(df_cmd, spec.ServiceCommandProtocol),
            "df_name": df_cmd.name,
            "de_proto": isinstance(de_cmd, spec.ServiceCommandProtocol),
            "de_name": de_cmd.name,
        }

    EBT(
        target=_probe,
        pre=WorldState(),
        post=WorldState(
            returns={
                "df_proto": True,
                "df_name": "docframe",
                "de_proto": True,
                "de_name": "docensurance",
            }
        ),
        custom_id="service_core_cli_service_command_protocols",
    ).run()


# ======================================================================================================================
# 2. CLI Commands: qb-cubie docframe check & update (Exit Codes 0 / 1 / 2 & Schema v1 JSON)
# ======================================================================================================================


def test_ebt_cli_docframe_check_passes_and_fails_with_distinct_exit_codes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """docframe check returns 0 on synced docs, 1 on frame failures, and 2 on STATE-GUARD errors."""
    clean_root = _seed_docframe_workspace(tmp_path / "clean", synced=True)
    stale_root = _seed_docframe_workspace(tmp_path / "stale", synced=False)
    missing_root = tmp_path / "does_not_exist"

    def _run_all() -> dict[str, Any]:
        ok_code = cli_main(["docframe", "check", str(clean_root), "--format", "json"])
        ok_payload = json.loads(capsys.readouterr().out)

        fail_code = cli_main(["docframe", "check", str(stale_root), "--format", "json"])
        fail_payload = json.loads(capsys.readouterr().out)

        fail_text_code = cli_main(["docframe", "check", str(stale_root), "--format", "text"])
        fail_text = capsys.readouterr().out

        err_code = cli_main(["docframe", "check", str(missing_root)])
        err_stderr = capsys.readouterr().err
        return {
            "ok_code": ok_code,
            "ok_schema": ok_payload.get("schema_version"),
            "ok_service": ok_payload.get("service"),
            "ok_passed": ok_payload.get("passed"),
            "ok_files_checked": ok_payload.get("files_checked"),
            "fail_code": fail_code,
            "fail_schema": fail_payload.get("schema_version"),
            "fail_passed": fail_payload.get("passed"),
            "fail_rule_ids": [d["rule_id"] for d in fail_payload.get("diagnostics", [])],
            "fail_text_code": fail_text_code,
            "fail_text_has_rule": "[DOCFRAME-OUTDATED]" in fail_text,
            "err_code": err_code,
            "err_has_guard": "STATE-GUARD" in err_stderr,
        }

    expected = {
        "ok_code": 0,
        "ok_schema": SERVICE_REPORT_SCHEMA_VERSION,
        "ok_service": "doc_frame",
        "ok_passed": True,
        "ok_files_checked": 1,
        "fail_code": 1,
        "fail_schema": SERVICE_REPORT_SCHEMA_VERSION,
        "fail_passed": False,
        "fail_rule_ids": ["DOCFRAME-OUTDATED"],
        "fail_text_code": 1,
        "fail_text_has_rule": True,
        "err_code": 2,
        "err_has_guard": True,
    }
    EBT(
        target=_run_all,
        pre=WorldState(),
        post=WorldState(returns=expected),
        custom_id="service_core_cli_docframe_check_exit_codes",
    ).run()


def test_ebt_cli_docframe_update_json_uses_schema_v1_and_keeps_compat_keys(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """H3(c): docframe update --format json emits schema_version=1 via report_to_dict plus legacy keys."""
    root = _seed_docframe_workspace(tmp_path / "upd", synced=False)

    def _run_update() -> dict[str, Any]:
        code = cli_main(["docframe", "update", str(root), "--format", "json"])
        payload = json.loads(capsys.readouterr().out)
        return {
            "code": code,
            "schema_version": payload.get("schema_version"),
            "service": payload.get("service"),
            "passed": payload.get("passed"),
            "changed_files": payload.get("changed_files"),
            "updated_files": payload.get("updated_files"),
            "catalog_entries": payload.get("catalog_entries"),
            "diagnostics": payload.get("diagnostics"),
        }

    expected = {
        "code": 0,
        "schema_version": SERVICE_REPORT_SCHEMA_VERSION,
        "service": "doc_frame",
        "passed": True,
        "changed_files": ["README.md"],
        "updated_files": ["README.md"],
        "catalog_entries": 1,
        "diagnostics": [],
    }
    EBT(
        target=_run_update,
        pre=WorldState(),
        post=WorldState(returns=expected),
        custom_id="service_core_cli_docframe_update_schema_v1",
    ).run()


# ======================================================================================================================
# 3. CLI Commands: qb-cubie docensurance check & Module Entrypoint
# ======================================================================================================================


def test_ebt_cli_docensurance_check_exit_codes_excludes_and_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """docensurance check returns 0 on pass, 1 on DOC-OUT failure, 2 on missing path, and respects --exclude."""
    ok_root = _seed_docensurance_workspace(tmp_path / "de_ok", passing=True)
    fail_root = _seed_docensurance_workspace(tmp_path / "de_fail", passing=False)
    (ok_root / "drafts").mkdir()
    (ok_root / "drafts" / "broken.md").write_text(
        "# Draft\n\nAusreichend lange Erklärung vor defektem Snippet.\n\n"
        "```python\nprint(1)\n```\n\n<details>\n<summary>Ergebnis</summary>\n\n```text\n999\n```\n</details>\n",
        encoding="utf-8",
    )
    missing_root = tmp_path / "de_missing"

    def _run_all() -> dict[str, Any]:
        ok_code = cli_main(["docensurance", "check", str(ok_root), "--exclude", "drafts", "--format", "json"])
        ok_payload = json.loads(capsys.readouterr().out)

        fail_code = cli_main(["docensurance", "check", str(fail_root), "--format", "json"])
        fail_payload = json.loads(capsys.readouterr().out)

        fail_text_code = cli_main(["docensurance", "check", str(fail_root), "--format", "text"])
        fail_text = capsys.readouterr().out

        err_code = cli_main(["docensurance", "check", str(missing_root)])
        err_stderr = capsys.readouterr().err
        return {
            "ok_code": ok_code,
            "ok_schema": ok_payload.get("schema_version"),
            "ok_passed": ok_payload.get("passed"),
            "ok_diags": ok_payload.get("diagnostics"),
            "fail_code": fail_code,
            "fail_schema": fail_payload.get("schema_version"),
            "fail_passed": fail_payload.get("passed"),
            "fail_rule_ids": [d["rule_id"] for d in fail_payload.get("diagnostics", [])],
            "fail_text_code": fail_text_code,
            "fail_text_has_rule": "[DOC-OUT]" in fail_text,
            "err_code": err_code,
            "err_has_guard": "STATE-GUARD" in err_stderr,
        }

    expected = {
        "ok_code": 0,
        "ok_schema": SERVICE_REPORT_SCHEMA_VERSION,
        "ok_passed": True,
        "ok_diags": [],
        "fail_code": 1,
        "fail_schema": SERVICE_REPORT_SCHEMA_VERSION,
        "fail_passed": False,
        "fail_rule_ids": ["DOC-OUT"],
        "fail_text_code": 1,
        "fail_text_has_rule": True,
        "err_code": 2,
        "err_has_guard": True,
    }
    EBT(
        target=_run_all,
        pre=WorldState(),
        post=WorldState(returns=expected),
        custom_id="service_core_cli_docensurance_check_exit_codes",
    ).run()


def test_ebt_docensurance_module_entrypoint_executes_cleanly(tmp_path: Path) -> None:
    """python -m qb_cubie.core.services.doc_ensurance check runs cleanly without RuntimeWarning."""
    root = _seed_docensurance_workspace(tmp_path / "de_mod", passing=True)

    def _run_module() -> dict[str, Any]:
        proc = subprocess.run(
            [sys.executable, "-m", "qb_cubie.core.services.doc_ensurance", "check", str(root), "--format", "json"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        payload = json.loads(proc.stdout) if proc.returncode == 0 and proc.stdout.strip() else {}
        return {
            "returncode": proc.returncode,
            "no_runtime_warning": "RuntimeWarning" not in proc.stderr,
            "schema_version": payload.get("schema_version"),
            "passed": payload.get("passed"),
        }

    EBT(
        target=_run_module,
        pre=WorldState(),
        post=WorldState(
            returns={
                "returncode": 0,
                "no_runtime_warning": True,
                "schema_version": SERVICE_REPORT_SCHEMA_VERSION,
                "passed": True,
            }
        ),
        custom_id="service_core_cli_docensurance_module_entrypoint",
    ).run()


# ======================================================================================================================
# 4. Lazy CLI Subprocess Isolation Probes (H5 Falsifikationskriterium & Mutant M7)
# ======================================================================================================================


def test_ebt_cli_top_level_help_imports_zero_services() -> None:
    """H5: qb-cubie --help lists docframe and docensurance without importing any service package."""

    def _probe() -> dict[str, Any]:
        res = _run_subprocess_with_blocked_modules(
            ["--help"],
            ("qb_cubie.core.services.doc_frame", "qb_cubie.core.services.doc_ensurance"),
        )
        return {
            "returncode": res["returncode"],
            "lists_docframe": "docframe" in res["stdout"],
            "lists_docensurance": "docensurance" in res["stdout"],
        }

    EBT(
        target=_probe,
        pre=WorldState(),
        post=WorldState(returns={"returncode": 0, "lists_docframe": True, "lists_docensurance": True}),
        custom_id="service_core_cli_top_help_zero_service_imports",
    ).run()


def test_ebt_cli_docframe_does_not_import_sibling_services(tmp_path: Path) -> None:
    """Mutant M7: docframe --help and docframe check run cleanly with doc_ensurance blocked."""
    root = _seed_docframe_workspace(tmp_path / "iso_df", synced=True)

    def _probe() -> dict[str, Any]:
        help_res = _run_subprocess_with_blocked_modules(
            ["docframe", "--help"],
            ("qb_cubie.core.services.doc_ensurance",),
        )
        check_res = _run_subprocess_with_blocked_modules(
            ["docframe", "check", str(root), "--format", "json"],
            ("qb_cubie.core.services.doc_ensurance",),
        )
        return {
            "help_rc": help_res["returncode"],
            "help_has_check_and_update": "check" in help_res["stdout"] and "update" in help_res["stdout"],
            "check_rc": check_res["returncode"],
        }

    EBT(
        target=_probe,
        pre=WorldState(),
        post=WorldState(returns={"help_rc": 0, "help_has_check_and_update": True, "check_rc": 0}),
        custom_id="service_core_cli_docframe_isolation_mutant_m7",
    ).run()


def test_ebt_cli_docensurance_does_not_import_sibling_services(tmp_path: Path) -> None:
    """H5: docensurance --help and docensurance check run cleanly with doc_frame blocked."""
    root = _seed_docensurance_workspace(tmp_path / "iso_de", passing=True)

    def _probe() -> dict[str, Any]:
        help_res = _run_subprocess_with_blocked_modules(
            ["docensurance", "--help"],
            ("qb_cubie.core.services.doc_frame",),
        )
        check_res = _run_subprocess_with_blocked_modules(
            ["docensurance", "check", str(root), "--format", "json"],
            ("qb_cubie.core.services.doc_frame",),
        )
        return {
            "help_rc": help_res["returncode"],
            "help_has_check": "check" in help_res["stdout"],
            "check_rc": check_res["returncode"],
        }

    EBT(
        target=_probe,
        pre=WorldState(),
        post=WorldState(returns={"help_rc": 0, "help_has_check": True, "check_rc": 0}),
        custom_id="service_core_cli_docensurance_isolation",
    ).run()
