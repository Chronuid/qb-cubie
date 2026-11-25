"""**Tries to** specify Cycle 1 RuleRegistry, FileContextCache, FileCheckRunner, and DocFrame.check() decoupling."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import importlib
from pathlib import Path
import subprocess
import sys
from typing import Any
import warnings

import pytest

from qb_cubie import EBT, ExceptionExpectation, PytestReporter, WorldState
from qb_cubie.core.protocols import Diagnostic, ServiceReportProtocol
from qb_cubie.core.reporter import JsonReporter
from qb_cubie.core.services import (
    CUBIE_DOC_RULES,
    CUBIE_DOC_STYLE,
    CUBIE_DOCFRAME_RULES,
    DocEnsurance,
    DocFrame,
    DocFrameBrokenRoute,
    DocFrameMissing,
    DocFrameOutdated,
    DocFrameProvenanceIncomplete,
    FramePattern,
)

pytestmark = pytest.mark.services
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _rules_module() -> Any:
    """Lazily imports qb_cubie.core.service_core.rules so Phase-Red collection stays clean."""
    return importlib.import_module("qb_cubie.core.service_core.rules")


# ---------- Minimal Domain-Neutral Probe Rules for FileCheckRunner & RuleRegistry -------------------------------------


@dataclass(frozen=True)
class _ScalarProbeRule:
    """Minimal RuleProtocol-compatible test rule."""

    rule_id: str = "PROBE-A"
    severity: str = "warning"
    label: str = "default"


class _CountingWorkspaceRule:
    """WorkspaceCheckRuleProtocol probe that counts workspace prep, cache hits, and file checks."""

    def __init__(
        self,
        rule_id: str,
        *,
        severity: str = "error",
        context_key: str = "shared",
        depends_on: tuple[str, ...] = (),
        counters: dict[str, int],
        fail_on_token: str | None = None,
    ) -> None:
        self.rule_id = rule_id
        self.severity = severity
        self.context_key = context_key
        self.depends_on = depends_on
        self._counters = counters
        self._fail_on_token = fail_on_token

    def prepare_workspace(self, sources: Sequence[Any], options: Mapping[str, Any]) -> dict[str, Any]:
        """Records workspace preparation count and returns a simple token map."""
        self._counters["prepare"] = self._counters.get("prepare", 0) + 1
        return {"source_count": len(sources), "options": dict(options)}

    def check_file(self, source: Any, workspace_ctx: Any, file_cache: Any) -> list[Diagnostic]:
        """Shares a single parsed representation per file via file_cache and checks fail_on_token."""
        _ = workspace_ctx
        self._counters[f"run:{self.rule_id}"] = self._counters.get(f"run:{self.rule_id}", 0) + 1

        def _parse() -> list[str]:
            self._counters["parse"] = self._counters.get("parse", 0) + 1
            return source.content.splitlines()

        lines = file_cache.get_or_compute("lines", _parse)
        if self._fail_on_token and any(self._fail_on_token in line for line in lines):
            return [Diagnostic(source.path, self.rule_id, 1, f"Found {self._fail_on_token}", severity=self.severity)]
        return []


class _LegacyFileCheckProbe:
    """Legacy FileCheckProtocol probe verifying backward compatibility in FileCheckRunner."""

    rule_id = "LEGACY-FILE-RULE"
    severity = "error"
    context_key = "legacy"

    def prepare_context(self, target: str | Path, excludes: Sequence[str], patterns: Sequence[Any]) -> str:
        """Returns a marker string proving legacy prepare_context was invoked."""
        _ = (target, excludes, patterns)
        return "legacy_ctx"

    def check_file(self, file_path: str, content: str, context: Any) -> list[Diagnostic]:
        """Emits a diagnostic when 'LEGACY_FAIL' appears in content."""
        if context == "legacy_ctx" and "LEGACY_FAIL" in content:
            return [Diagnostic(file_path, self.rule_id, 1, "Legacy check triggered")]
        return []


def _framed_doc(title: str, banner: str = "cubie-logo-written.png", body: str = "Body.") -> str:
    """Builds a minimal CUBIE_DOC_FRAME_1 document for DocFrame.check() scenarios."""
    return (
        f'<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="{banner}" -->\n'
        f'<div align="center">\n\n# {title}\n\n![Cubie](.assets/{banner})\n\n'
        "Kurze Zusammenfassung.\n\n---\n\n---\n\n</div>\n<!-- /qb:frame -->\n\n"
        f"{body}\n\n"
        '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n'
    )


def _seed_synced_docframe_workspace(root: Path) -> Path:
    """Seeds a 3-file synchronized DocFrame project tree under root."""
    for folder in ("docs/.assets", "docs/services", "experiments"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='docframe-core'\n", encoding="utf-8")
    for asset in ("cubie-banner.png", "cubie-logo-written.png", "cubie-small.png"):
        (root / "docs" / ".assets" / asset).write_bytes(b"PNG")
    (root / "README.md").write_text(_framed_doc("Root", "cubie-banner.png"), encoding="utf-8")
    (root / "docs" / "GUIDE_Quality-Assurance.md").write_text(_framed_doc("QA"), encoding="utf-8")
    (root / "docs" / "services" / "GUIDE_DocEnsurance.md").write_text(_framed_doc("Service"), encoding="utf-8")
    (root / "experiments" / "unframed.md").write_text("# Excluded\n", encoding="utf-8")
    DocFrame.update(target=root, excludes=("experiments",))
    return root


# ======================================================================================================================
# 1. FileContextCache (Cache-Treffer inkl. Falsy-Werte & STATE-GUARDs)
# ======================================================================================================================


def test_ebt_file_context_cache_computes_once_including_falsy_values() -> None:
    """FileContextCache calls each factory at most once even when the cached value is None, [], 0, or False."""

    def run_cache_probe() -> dict[str, Any]:
        mod = _rules_module()
        cache = mod.FileContextCache()
        calls: dict[str, int] = {}
        values: dict[str, Any] = {}
        for key, payload in (("none_val", None), ("empty_list", []), ("zero", 0), ("false_val", False)):
            def _make(k: str = key, v: Any = payload) -> Any:
                calls[k] = calls.get(k, 0) + 1
                return v

            first = cache.get_or_compute(key, _make)
            second = cache.get_or_compute(key, _make)
            values[key] = (first, second)
        return {"calls": calls, "values": values}

    EBT(
        target=run_cache_probe,
        post=WorldState(
            returns={
                "calls": {"none_val": 1, "empty_list": 1, "zero": 1, "false_val": 1},
                "values": {
                    "none_val": (None, None),
                    "empty_list": ([], []),
                    "zero": (0, 0),
                    "false_val": (False, False),
                },
            }
        ),
        custom_id="service_core_rules_file_context_cache_falsy",
    ).run()


def test_ebt_file_context_cache_rejects_invalid_keys() -> None:
    """Blank keys raise ValueError STATE-GUARD; non-string keys raise TypeError STATE-GUARD."""

    def call_with_key(bad_key: Any) -> Any:
        cache = _rules_module().FileContextCache()
        return cache.get_or_compute(bad_key, lambda: 1)

    EBT(
        target=call_with_key,
        pre=[WorldState(args=("",)), WorldState(args=("   ",))],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_rules_cache_blank_key_guard",
    ).run()
    EBT(
        target=call_with_key,
        pre=[WorldState(args=(None,)), WorldState(args=(123,))],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:")),
        custom_id="service_core_rules_cache_type_key_guard",
    ).run()


# ======================================================================================================================
# 2. RuleRegistry (Flattening, Auto-Instantiierung, Override & Kollisions-Slots — Anti-Subsumtion!)
# ======================================================================================================================


def test_ebt_rule_registry_flattens_instantiates_and_overrides_by_rule_id() -> None:
    """RuleRegistry flattens nested sequences, auto-instantiates classes, and overrides duplicate rule_ids."""

    def run_registry_override() -> dict[str, Any]:
        mod = _rules_module()
        registry = mod.RuleRegistry(
            rules=(
                (_ScalarProbeRule, [_ScalarProbeRule(rule_id="PROBE-B", severity="warning", label="v1")]),
                _ScalarProbeRule(rule_id="PROBE-A", severity="error", label="upgraded"),
            )
        )
        rules = registry.rules
        return {
            "rule_ids": [r.rule_id for r in rules],
            "severities": [r.severity for r in rules],
            "labels": [r.label for r in rules],
            "distinct_instances": len({id(r) for r in rules}),
        }

    EBT(
        target=run_registry_override,
        post=WorldState(
            returns={
                "rule_ids": ["PROBE-A", "PROBE-B"],
                "severities": ["error", "warning"],
                "labels": ["upgraded", "v1"],
                "distinct_instances": 2,
            }
        ),
        custom_id="service_core_rules_registry_override_no_subsumption",
    ).run()


def test_ebt_rule_registry_merge_hook_supports_merging_and_collision_slots() -> None:
    """Custom merge hook either combines matching rule_ids or preserves both via collision-free slots."""

    def run_registry_collision() -> dict[str, Any]:
        mod = _rules_module()

        def merge_if_same_severity(existing: _ScalarProbeRule, incoming: _ScalarProbeRule) -> _ScalarProbeRule | None:
            if existing.severity == incoming.severity:
                return _ScalarProbeRule(
                    rule_id=existing.rule_id,
                    severity=existing.severity,
                    label=f"{existing.label}+{incoming.label}",
                )
            return None

        registry = mod.RuleRegistry(
            rules=[
                _ScalarProbeRule(rule_id="LINT", severity="error", label="r1"),
                _ScalarProbeRule(rule_id="LINT", severity="error", label="r2"),
                _ScalarProbeRule(rule_id="LINT", severity="warning", label="r3"),
            ],
            merge=merge_if_same_severity,
        )
        rules = registry.rules
        return {
            "rule_ids": [r.rule_id for r in rules],
            "severities": [r.severity for r in rules],
            "labels": [r.label for r in rules],
            "distinct_instances": len({id(r) for r in rules}),
        }

    EBT(
        target=run_registry_collision,
        post=WorldState(
            returns={
                "rule_ids": ["LINT", "LINT"],
                "severities": ["error", "warning"],
                "labels": ["r1+r2", "r3"],
                "distinct_instances": 2,
            }
        ),
        custom_id="service_core_rules_registry_collision_slots",
    ).run()


def test_ebt_rule_registry_rejects_invalid_rule_objects() -> None:
    """Objects lacking rule_id/severity raise TypeError STATE-GUARD."""

    def register_invalid(bad_rule: Any) -> Any:
        return _rules_module().RuleRegistry(rules=[bad_rule])

    EBT(
        target=register_invalid,
        pre=[WorldState(args=("not_a_rule",)), WorldState(args=(123,)), WorldState(args=(object(),))],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:")),
        custom_id="service_core_rules_registry_invalid_object_guard",
    ).run()


# ======================================================================================================================
# 3. FileCheckRunner (Cache pro Datei [M3], depends_on-Kaskaden, Legacy-Bridge & Anti-Vacuous-Pass)
# ======================================================================================================================


def test_file_check_runner_computes_cached_parse_once_per_file(tmp_path: Path) -> None:
    """Mutant M3: 4 rules sharing FileContextCache over 3 files call workspace prep 1x and parse exactly 3x."""
    for name in ("a.md", "b.md", "c.md"):
        (tmp_path / name).write_text(f"# {name}\nok\n", encoding="utf-8")

    def run_cached_runner() -> dict[str, Any]:
        mod = _rules_module()
        counters: dict[str, int] = {}
        rules = [
            _CountingWorkspaceRule(f"R-{idx}", context_key="shared", counters=counters)
            for idx in range(1, 5)
        ]
        report = mod.FileCheckRunner(
            rules=rules,
            target=tmp_path,
            service="probe_svc",
            reporter=None,
        ).run()
        return {
            "is_protocol": isinstance(report, ServiceReportProtocol),
            "passed": report.passed,
            "files_checked": report.files_checked,
            "prepare_calls": counters.get("prepare", 0),
            "parse_calls": counters.get("parse", 0),
            "rule_runs": [counters.get(f"run:R-{idx}", 0) for idx in range(1, 5)],
        }

    EBT(
        target=run_cached_runner,
        post=WorldState(
            returns={
                "is_protocol": True,
                "passed": True,
                "files_checked": 3,
                "prepare_calls": 1,
                "parse_calls": 3,
                "rule_runs": [3, 3, 3, 3],
            }
        ),
        custom_id="service_core_rules_runner_m3_single_parse_per_file",
    ).run()


def test_ebt_file_check_runner_depends_on_skips_only_failed_file_and_not_warnings(tmp_path: Path) -> None:
    """depends_on skips dependent rules only on files where a dependency emitted an error (not warning)."""
    (tmp_path / "err_file.md").write_text("ERR_DEP\nDEP_TARGET\n", encoding="utf-8")
    (tmp_path / "warn_file.md").write_text("WARN_DEP\nDEP_TARGET\n", encoding="utf-8")
    (tmp_path / "clean_dep_file.md").write_text("OK\nDEP_TARGET\n", encoding="utf-8")

    def run_dependency_scenario() -> dict[str, Any]:
        mod = _rules_module()
        counters: dict[str, int] = {}
        r_err_dep = _CountingWorkspaceRule(
            "DEP-ERR", severity="error", counters=counters, fail_on_token="ERR_DEP"
        )
        r_warn_dep = _CountingWorkspaceRule(
            "DEP-WARN", severity="warning", counters=counters, fail_on_token="WARN_DEP"
        )
        r_child = _CountingWorkspaceRule(
            "CHILD",
            severity="error",
            depends_on=("DEP-ERR", "DEP-WARN"),
            counters=counters,
            fail_on_token="DEP_TARGET",
        )
        report = mod.FileCheckRunner(
            rules=(r_err_dep, r_warn_dep, r_child),
            target=tmp_path,
            service="dep_svc",
            reporter=None,
        ).run()
        return {
            "passed": report.passed,
            "files_checked": report.files_checked,
            "child_runs": counters.get("run:CHILD", 0),
            "diagnostics": [(Path(d.file_path).name, d.rule_id, d.severity) for d in report.diagnostics],
        }

    EBT(
        target=run_dependency_scenario,
        post=WorldState(
            returns={
                "passed": False,
                "files_checked": 3,
                "child_runs": 2,
                "diagnostics": [
                    ("clean_dep_file.md", "CHILD", "error"),
                    ("err_file.md", "DEP-ERR", "error"),
                    ("warn_file.md", "DEP-WARN", "warning"),
                    ("warn_file.md", "CHILD", "error"),
                ],
            }
        ),
        custom_id="service_core_rules_runner_depends_on_semantics",
    ).run()


def test_ebt_file_check_runner_supports_legacy_file_check_protocol_and_reporters(tmp_path: Path) -> None:
    """FileCheckRunner executes legacy FileCheckProtocol rules and supports PytestReporter and JsonReporter."""
    (tmp_path / "bad.md").write_text("LEGACY_FAIL\n", encoding="utf-8")
    json_out = tmp_path / "runner.json"

    def run_legacy_json() -> dict[str, Any]:
        mod = _rules_module()
        report = mod.FileCheckRunner(
            rules=[_LegacyFileCheckProbe()],
            target=tmp_path,
            service="legacy_svc",
            reporter=JsonReporter(json_out),
        ).run()
        return {
            "passed": report.passed,
            "files_checked": report.files_checked,
            "rules": [d.rule_id for d in report.diagnostics],
            "json_exists": json_out.is_file(),
        }

    EBT(
        target=run_legacy_json,
        post=WorldState(
            returns={"passed": False, "files_checked": 1, "rules": ["LEGACY-FILE-RULE"], "json_exists": True}
        ),
        custom_id="service_core_rules_runner_legacy_and_json",
    ).run()

    EBT(
        target=lambda: _rules_module().FileCheckRunner(
            rules=[_LegacyFileCheckProbe()], target=tmp_path, reporter=PytestReporter()
        ).run(),
        post=WorldState(raises=ExceptionExpectation(AssertionError, match=r"\[LEGACY-FILE-RULE\]")),
        custom_id="service_core_rules_runner_pytest_reporter_asserts",
    ).run()


def test_ebt_file_check_runner_rejects_empty_rules_empty_dir_and_bare_excludes(tmp_path: Path) -> None:
    """Guards prevent vacuous passes on 0 files, empty rule lists, and bare string excludes."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    (tmp_path / "ok.md").write_text("# ok\n", encoding="utf-8")

    def run_empty_rules() -> Any:
        return _rules_module().FileCheckRunner(rules=(), target=tmp_path, reporter=None).run()

    def run_zero_files() -> Any:
        counters: dict[str, int] = {}
        rule = _CountingWorkspaceRule("R1", counters=counters)
        return _rules_module().FileCheckRunner(rules=[rule], target=empty_dir, reporter=None).run()

    def run_bare_excludes() -> Any:
        counters: dict[str, int] = {}
        rule = _CountingWorkspaceRule("R1", counters=counters)
        return _rules_module().FileCheckRunner(rules=[rule], target=tmp_path, excludes="empty", reporter=None).run()

    EBT(
        target=run_empty_rules,
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_rules_runner_empty_rules_guard",
    ).run()
    EBT(
        target=run_zero_files,
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_rules_runner_zero_files_vacuous_guard",
    ).run()
    EBT(
        target=run_bare_excludes,
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:.*excludes")),
        custom_id="service_core_rules_runner_bare_excludes_guard",
    ).run()


# ======================================================================================================================
# 4. DocFrame.check(), Entkopplung (M3, M4), Dummy-Entfernung, Span-Kaskaden & E2-Kompatibilitätsbrücke
# ======================================================================================================================


def test_ebt_docframe_check_runs_natively_and_parses_each_file_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mutant M3 + H1: DocFrame.check() verifies synced workspaces cleanly and parses each file at most once."""
    root = _seed_synced_docframe_workspace(tmp_path / "synced")

    def run_counted_check() -> dict[str, Any]:
        from qb_cubie.core.services.doc_frame import doc_frame_rules

        original_parse = doc_frame_rules.parse_frame_spans
        rule_parse_calls = 0

        def counting_parse(content: str) -> Any:
            nonlocal rule_parse_calls
            rule_parse_calls += 1
            return original_parse(content)

        monkeypatch.setattr(doc_frame_rules, "parse_frame_spans", counting_parse)
        report = DocFrame.check(target=root, excludes=("experiments",), reporter=None)
        return {
            "is_protocol": isinstance(report, ServiceReportProtocol),
            "passed": report.passed,
            "files_checked": report.files_checked,
            "diag_count": len(report.diagnostics),
            "rule_parse_calls_per_file_ok": rule_parse_calls <= report.files_checked,
            "not_4x_redundant": rule_parse_calls < report.files_checked * 4,
        }

    EBT(
        target=run_counted_check,
        post=WorldState(
            returns={
                "is_protocol": True,
                "passed": True,
                "files_checked": 3,
                "diag_count": 0,
                "rule_parse_calls_per_file_ok": True,
                "not_4x_redundant": True,
            }
        ),
        custom_id="service_core_docframe_check_single_parse_per_file",
    ).run()


def test_doc_frame_check_runs_with_doc_ensurance_blocked(tmp_path: Path) -> None:
    """Mutant M4: DocFrame.check() must execute cleanly when doc_ensurance is blocked via sys.meta_path."""
    root = _seed_synced_docframe_workspace(tmp_path / "isolated")
    broken_root = _seed_synced_docframe_workspace(tmp_path / "isolated_fault")
    (broken_root / "docs" / "UNFRAMED.md").write_text("# Missing Frame\n", encoding="utf-8")

    probe_script = (
        "import importlib, sys\n"
        "from pathlib import Path\n"
        "BLOCKED = 'qb_cubie.core.services.doc_ensurance'\n"
        "class _Blocker:\n"
        "    def find_spec(self, fullname, path, target=None):\n"
        "        if fullname == BLOCKED or fullname.startswith(BLOCKED + '.'):\n"
        "            raise ModuleNotFoundError(f'Blocked: {fullname}')\n"
        "        return None\n"
        "sys.meta_path.insert(0, _Blocker())\n"
        "from qb_cubie.core.services.doc_frame import DocFrame\n"
        "clean = DocFrame.check(target=Path(sys.argv[1]), excludes=('experiments',), reporter=None)\n"
        "assert clean.passed is True and clean.files_checked == 3 and not clean.diagnostics, clean\n"
        "fault = DocFrame.check(target=Path(sys.argv[2]), excludes=('experiments',), reporter=None)\n"
        "assert fault.passed is False and [d.rule_id for d in fault.diagnostics] == ['DOCFRAME-MISSING'], fault\n"
        "leaked = [m for m in sys.modules if m == BLOCKED or m.startswith(BLOCKED + '.')]\n"
        "assert not leaked, f'Leaked doc_ensurance modules: {leaked}'\n"
    )

    def run_blocked_subprocess() -> int:
        proc = subprocess.run(
            [sys.executable, "-c", probe_script, str(root), str(broken_root)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(f"DocFrame.check() failed with doc_ensurance blocked:\n{proc.stdout}\n{proc.stderr}")
        return proc.returncode

    EBT(
        target=run_blocked_subprocess,
        post=WorldState(returns=0),
        custom_id="service_core_docframe_check_m4_isolated_from_doc_ensurance",
    ).run()


def test_ebt_docframe_dummy_methods_are_removed() -> None:
    """H1 #2: FramePattern has no dummy scan() method and DocFrame rules have no dummy check() method."""

    def inspect_dummy_methods() -> dict[str, bool]:
        rule_classes = (
            DocFrameMissing,
            DocFrameOutdated,
            DocFrameBrokenRoute,
            DocFrameProvenanceIncomplete,
        )
        return {
            "frame_pattern_has_no_scan": not hasattr(FramePattern, "scan"),
            "rules_have_no_dummy_check": all(not hasattr(cls, "check") for cls in rule_classes),
        }

    EBT(
        target=inspect_dummy_methods,
        post=WorldState(returns={"frame_pattern_has_no_scan": True, "rules_have_no_dummy_check": True}),
        custom_id="service_core_docframe_no_dummy_methods",
    ).run()


def test_ebt_docframe_check_preserves_span_level_cascade_granularity(tmp_path: Path) -> None:
    """H1 Risk: broken route in head still reports outdated foot on the same file, while missing foot skips outdated."""
    root = _seed_synced_docframe_workspace(tmp_path / "cascade")
    qa = root / "docs" / "GUIDE_Quality-Assurance.md"
    text = qa.read_text(encoding="utf-8")
    # Inject broken banner in head AND stale alt text in foot of the same document:
    mutated = text.replace('banner="cubie-logo-written.png"', 'banner="nonexistent-banner.png"', 1).replace(
        "![Cubie](.assets/cubie-small.png)", "![StaleAlt](.assets/cubie-small.png)", 1
    )
    qa.write_text(mutated, encoding="utf-8")
    # Also add a file missing its foot zone (must emit ONLY DOCFRAME-MISSING, not DOCFRAME-OUTDATED):
    (root / "docs" / "NO_FOOT.md").write_text(
        '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# Missing Foot\n<!-- /qb:frame -->\n',
        encoding="utf-8",
    )

    def run_cascade_check() -> dict[str, list[str]]:
        report = DocFrame.check(target=root, excludes=("experiments",), reporter=None)
        by_file: dict[str, list[str]] = {}
        for diag in report.diagnostics:
            by_file.setdefault(Path(diag.file_path).name, []).append(diag.rule_id)
        return {name: sorted(ids) for name, ids in by_file.items()}

    EBT(
        target=run_cascade_check,
        post=WorldState(
            returns={
                "GUIDE_Quality-Assurance.md": ["DOCFRAME-BROKEN-ROUTE", "DOCFRAME-OUTDATED"],
                "NO_FOOT.md": ["DOCFRAME-MISSING"],
            }
        ),
        custom_id="service_core_docframe_span_level_cascade_granularity",
    ).run()


def test_ebt_doc_ensurance_compatibility_bridge_runs_docframe_rules_without_frame_pattern_in_pattern(
    tmp_path: Path,
) -> None:
    """E2 Bridge: DocEnsurance still executes CUBIE_DOCFRAME_RULES orthogonally with pattern=CUBIE_DOC_STYLE."""
    root = _seed_synced_docframe_workspace(tmp_path / "bridge")
    qa = root / "docs" / "GUIDE_Quality-Assurance.md"
    qa.write_text(
        "# QA\n\n"
        "Ausreichend lange Erklärung vor einem fehlerhaften Python-Beispiel.\n\n"
        "```python\nprint(21 * 2)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n99\n```\n</details>\n",
        encoding="utf-8",
    )

    def run_bridge() -> dict[str, Any]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            report = DocEnsurance(
                target=root,
                pattern=CUBIE_DOC_STYLE,
                rules=(CUBIE_DOC_RULES, CUBIE_DOCFRAME_RULES),
                excludes=("experiments",),
                reporter=None,
            ).run()
        return {
            "passed": report.passed,
            "rules": sorted({d.rule_id for d in report.diagnostics if d.severity == "error"}),
        }

    EBT(
        target=run_bridge,
        post=WorldState(returns={"passed": False, "rules": ["DOC-OUT", "DOCFRAME-MISSING"]}),
        custom_id="service_core_e2_doc_ensurance_compatibility_bridge",
    ).run()
