"""**Tries to** specify Cycle 1 ServiceReport, Diagnostic.context, JsonReporter, PytestReporter, and DocFrame reporting."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
import warnings

import pytest

from qb_cubie import EBT, ExceptionExpectation, PytestReporter, WorldState
from qb_cubie.core.protocols import Diagnostic, ServiceReportProtocol
from qb_cubie.core.reporter import JsonReporter
from qb_cubie.core.services import DocDiagnostic, DocFrame, DocFrameReport, DocReport

pytestmark = pytest.mark.services


def _reporting_module() -> Any:
    """Lazily imports qb_cubie.core.service_core.reporting so Phase-Red collection stays clean."""
    return importlib.import_module("qb_cubie.core.service_core.reporting")


def _seed_docframe_project(root: Path, *, stale: bool = True) -> Path:
    """Seeds a minimal project layout for DocFrame reporter integration tests."""
    (root / "docs" / ".assets").mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='reporting-test'\n", encoding="utf-8")
    for asset in ("cubie-logo-written.png", "cubie-small.png"):
        (root / "docs" / ".assets" / asset).write_bytes(b"PNG")
    readme = root / "README.md"
    readme.write_text(
        '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# Demo\n<!-- /qb:frame -->\n\n'
        'Body.\n\n<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n',
        encoding="utf-8",
    )
    if not stale:
        DocFrame.update(target=root)
    return root


# ======================================================================================================================
# 1. Diagnostic.context (Abwärtskompatible Erweiterung in core/protocols.py)
# ======================================================================================================================


def test_ebt_diagnostic_supports_optional_context_field() -> None:
    """Diagnostic defaults context to None, preserves string contexts, and rejects non-str contexts."""

    def build_default() -> dict[str, Any]:
        diag = Diagnostic(file_path="docs/a.md", rule_id="CORE-1", line=3, message="ok")
        return {"severity": diag.severity, "context": diag.context}

    def build_with_context() -> dict[str, Any]:
        diag = Diagnostic(
            file_path="docs/a.md",
            rule_id="CORE-2",
            line=5,
            message="warn",
            severity="warning",
            context="zone:head",
        )
        return {"severity": diag.severity, "context": diag.context}

    def build_invalid_context(bad_ctx: Any) -> Diagnostic:
        return Diagnostic(file_path="docs/a.md", rule_id="CORE-3", line=1, message="x", context=bad_ctx)

    EBT(
        target=build_default,
        post=WorldState(returns={"severity": "error", "context": None}),
        custom_id="service_core_reporting_diagnostic_default_context",
    ).run()
    EBT(
        target=build_with_context,
        post=WorldState(returns={"severity": "warning", "context": "zone:head"}),
        custom_id="service_core_reporting_diagnostic_explicit_context",
    ).run()
    EBT(
        target=build_invalid_context,
        pre=[WorldState(args=(123,)), WorldState(args=(True,))],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:.*context")),
        custom_id="service_core_reporting_diagnostic_invalid_context",
    ).run()


# ======================================================================================================================
# 2. ServiceReport Dataclass & STATE-GUARDs
# ======================================================================================================================


def test_ebt_service_report_satisfies_protocol_and_is_hashable() -> None:
    """ServiceReport is frozen, hashable, implements ServiceReportProtocol, and keeps metadata."""

    def inspect_report() -> dict[str, Any]:
        rep = _reporting_module()
        diag = Diagnostic("docs/a.md", "R-1", 2, "warn", severity="warning", context="zone:foot")
        report = rep.ServiceReport(
            service="doc_frame",
            target="docs",
            passed=True,
            diagnostics=(diag,),
            changed_files=("docs/a.md",),
            files_checked=4,
            metadata=(("mode", "check"),),
        )
        return {
            "is_protocol": isinstance(report, ServiceReportProtocol),
            "hashable": isinstance(hash(report), int),
            "service": report.service,
            "files_checked": report.files_checked,
            "changed_files": report.changed_files,
            "metadata": report.metadata,
        }

    EBT(
        target=inspect_report,
        post=WorldState(
            returns={
                "is_protocol": True,
                "hashable": True,
                "service": "doc_frame",
                "files_checked": 4,
                "changed_files": ("docs/a.md",),
                "metadata": (("mode", "check"),),
            }
        ),
        custom_id="service_core_reporting_service_report_contract",
    ).run()


def test_ebt_service_report_validates_fields_with_state_guards() -> None:
    """ServiceReport rejects blank service names, non-bool passed flags, and negative/bool files_checked."""

    def make_report(service: Any, passed: Any, files_checked: Any) -> Any:
        rep = _reporting_module()
        return rep.ServiceReport(service=service, target="docs", passed=passed, files_checked=files_checked)

    EBT(
        target=make_report,
        pre=[
            WorldState(args=("", True, 0)),
            WorldState(args=("   ", True, 0)),
            WorldState(args=("doc_frame", True, -1)),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_reporting_service_report_value_guards",
    ).run()
    EBT(
        target=make_report,
        pre=[
            WorldState(args=(123, True, 0)),
            WorldState(args=("doc_frame", 1, 0)),
            WorldState(args=("doc_frame", None, 0)),
            WorldState(args=("doc_frame", True, True)),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:")),
        custom_id="service_core_reporting_service_report_type_guards",
    ).run()


# ======================================================================================================================
# 3. report_to_dict & format_service_report_text (Einheitlich über ServiceReport, DocReport, DocFrameReport)
# ======================================================================================================================


def test_ebt_report_to_dict_serializes_all_service_report_types() -> None:
    """report_to_dict produces schema_version=1 dicts for ServiceReport, DocReport, and DocFrameReport."""

    def serialize_all() -> dict[str, Any]:
        rep = _reporting_module()
        generic = rep.ServiceReport(
            service="coverage",
            target="src",
            passed=False,
            diagnostics=(Diagnostic("src/a.py", "COV-1", 10, "low coverage", context="fn:foo"),),
            changed_files=(),
            files_checked=3,
            metadata=(("profile", "strict"),),
        )
        doc_rep = DocReport(
            target="docs/a.md",
            passed=False,
            sessions=(),
            diagnostics=(DocDiagnostic("docs/a.md", "DOC-OUT", 7, "mismatch", session_id="s1"),),
        )
        frame_rep = DocFrameReport(
            target="docs",
            passed=True,
            updated_files=("README.md",),
            catalog=None,
            diagnostics=(),
        )
        g_dict = rep.report_to_dict(generic)
        d_dict = rep.report_to_dict(doc_rep)
        f_dict = rep.report_to_dict(frame_rep)
        json.dumps([g_dict, d_dict, f_dict])
        return {
            "versions": [g_dict["schema_version"], d_dict["schema_version"], f_dict["schema_version"]],
            "generic_context": g_dict["diagnostics"][0]["context"],
            "generic_files_checked": g_dict["files_checked"],
            "doc_context": d_dict["diagnostics"][0]["context"],
            "frame_changed_files": f_dict["changed_files"],
            "frame_passed": f_dict["passed"],
        }

    EBT(
        target=serialize_all,
        post=WorldState(
            returns={
                "versions": [1, 1, 1],
                "generic_context": "fn:foo",
                "generic_files_checked": 3,
                "doc_context": "s1",
                "frame_changed_files": ["README.md"],
                "frame_passed": True,
            }
        ),
        custom_id="service_core_reporting_report_to_dict_uniform",
    ).run()


def test_ebt_format_service_report_text_includes_diagnostic_and_context() -> None:
    """format_service_report_text formats rule_id, file, line, message, and optional context."""

    def render_text() -> str:
        rep = _reporting_module()
        report = rep.ServiceReport(
            service="doc_frame",
            target="docs",
            passed=False,
            diagnostics=(Diagnostic("docs/a.md", "DOCFRAME-OUTDATED", 4, "stale footer", context="zone:foot"),),
            files_checked=1,
        )
        return rep.format_service_report_text(report)

    EBT(
        target=render_text,
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=re.compile(r"\[DOCFRAME-OUTDATED\] docs/a\.md:4: stale footer")),
                WorldState(returns=lambda text: "zone:foot" in text),
            ],
        },
        custom_id="service_core_reporting_format_text",
    ).run()


# ======================================================================================================================
# 4. JsonReporter unterstützt ServiceReportProtocol (H3 Falsifikationskriterium)
# ======================================================================================================================


@pytest.mark.parametrize("kind", ["service_report", "doc_report", "doc_frame_report"])
def test_ebt_json_reporter_persists_service_reports_atomically(tmp_path: Path, kind: str) -> None:
    """JsonReporter writes schema_version=1 UTF-8 JSON for all ServiceReportProtocol implementations."""
    out_path = tmp_path / f"{kind}.json"

    def run_json_report() -> dict[str, Any]:
        if kind == "service_report":
            rep = _reporting_module()
            report: ServiceReportProtocol = rep.ServiceReport(
                service="styleguide",
                target="src",
                passed=False,
                diagnostics=(Diagnostic("src/a.py", "SG-1", 12, "too long", context="fn:bar"),),
                files_checked=2,
            )
        elif kind == "doc_report":
            report = DocReport(
                target="docs/guide.md",
                passed=False,
                diagnostics=(DocDiagnostic("docs/guide.md", "DOC-OUT", 8, "wrong", session_id="alpha"),),
            )
        else:
            report = DocFrameReport(
                target="docs",
                passed=True,
                updated_files=("README.md",),
                diagnostics=(),
            )
        JsonReporter(out_path).report(report)
        proc = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                "import json, pathlib, sys; d = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')); "
                "assert d['schema_version'] == 1; print(d['passed'], len(d['diagnostics']))",
                str(out_path),
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        parsed = json.loads(out_path.read_text(encoding="utf-8"))
        return {
            "schema_version": parsed["schema_version"],
            "passed": parsed["passed"],
            "diag_count": len(parsed["diagnostics"]),
            "files": sorted(p.name for p in tmp_path.iterdir() if p.name.startswith(kind)),
        }

    expected = {
        "service_report": {"schema_version": 1, "passed": False, "diag_count": 1, "files": ["service_report.json"]},
        "doc_report": {"schema_version": 1, "passed": False, "diag_count": 1, "files": ["doc_report.json"]},
        "doc_frame_report": {"schema_version": 1, "passed": True, "diag_count": 0, "files": ["doc_frame_report.json"]},
    }[kind]
    EBT(
        target=run_json_report,
        post=WorldState(returns=expected),
        custom_id=f"service_core_reporting_json_reporter_{kind}",
    ).run()


def test_ebt_json_reporter_still_rejects_unknown_objects(tmp_path: Path) -> None:
    """JsonReporter rejects arbitrary objects that are neither RunTrace nor ServiceReportProtocol."""
    reporter = JsonReporter(tmp_path / "invalid.json")
    EBT(
        target=reporter.report,
        pre=[WorldState(args=(123,)), WorldState(args=(object(),))],
        post=WorldState(raises=ExceptionExpectation(TypeError)),
        custom_id="service_core_reporting_json_reporter_rejects_invalid",
    ).run()


# ======================================================================================================================
# 5. PytestReporter Context-Ausgabe & DocFrame Reporter-Injection
# ======================================================================================================================


def test_ebt_pytest_reporter_surfaces_diagnostic_context_and_preserves_prefix() -> None:
    """PytestReporter preserves the standard prefix while surfacing context/session_id in service reports."""

    def run_pytest_report() -> dict[str, Any]:
        rep = _reporting_module()
        report = rep.ServiceReport(
            service="doc_ensurance",
            target="docs/a.md",
            passed=False,
            diagnostics=(
                Diagnostic("docs/a.md", "DOC-WARN", 3, "soft notice", severity="warning", context="session:w1"),
                Diagnostic("docs/a.md", "DOC-ERR", 9, "hard failure", severity="error", context="session:e1"),
            ),
            files_checked=1,
        )
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", UserWarning)
            err_msg = ""
            try:
                PytestReporter().report(report)
            except AssertionError as exc:
                err_msg = str(exc)
        return {
            "warning_msgs": [str(w.message) for w in caught if issubclass(w.category, UserWarning)],
            "error_msg": err_msg,
        }

    EBT(
        target=run_pytest_report,
        post={
            "quantor": "all",
            "states": [
                WorldState(
                    returns=lambda res: (
                        len(res["warning_msgs"]) == 1
                        and res["warning_msgs"][0].startswith("[DOC-WARN] docs/a.md:3: soft notice")
                        and "[DOC-ERR] docs/a.md:9: hard failure" in res["error_msg"]
                        and "session:e1" in res["error_msg"]
                    )
                ),
                WorldState(returns=lambda res: not res["error_msg"], expect=False),
            ],
        },
        custom_id="service_core_reporting_pytest_reporter_context",
    ).run()


def test_ebt_docframe_update_and_check_support_injectable_reporters(tmp_path: Path) -> None:
    """DocFrame.update() and DocFrame.check() support injectable JsonReporter and PytestReporter."""
    update_proj = _seed_docframe_project(tmp_path / "upd", stale=True)
    update_json = tmp_path / "update_report.json"

    def run_update_with_json() -> dict[str, Any]:
        report = DocFrame.update(target=update_proj, reporter=JsonReporter(update_json))
        payload = json.loads(update_json.read_text(encoding="utf-8"))
        return {
            "report_passed": report.passed,
            "json_schema": payload["schema_version"],
            "json_changed": payload["changed_files"],
        }

    EBT(
        target=run_update_with_json,
        post=WorldState(returns={"report_passed": True, "json_schema": 1, "json_changed": ["README.md"]}),
        custom_id="service_core_reporting_docframe_update_json_reporter",
    ).run()

    stale_proj = _seed_docframe_project(tmp_path / "chk", stale=True)
    check_json = tmp_path / "check_report.json"

    def run_check_with_json() -> dict[str, Any]:
        report = DocFrame.check(target=stale_proj, reporter=JsonReporter(check_json))
        payload = json.loads(check_json.read_text(encoding="utf-8"))
        return {
            "report_passed": report.passed,
            "json_passed": payload["passed"],
            "json_rules": [d["rule_id"] for d in payload["diagnostics"]],
        }

    EBT(
        target=run_check_with_json,
        post=WorldState(
            returns={"report_passed": False, "json_passed": False, "json_rules": ["DOCFRAME-OUTDATED"]}
        ),
        custom_id="service_core_reporting_docframe_check_json_reporter",
    ).run()

    EBT(
        target=lambda: DocFrame.check(target=stale_proj, reporter=PytestReporter()),
        post=WorldState(raises=ExceptionExpectation(AssertionError, match=r"\[DOCFRAME-OUTDATED\]")),
        custom_id="service_core_reporting_docframe_check_pytest_reporter",
    ).run()
