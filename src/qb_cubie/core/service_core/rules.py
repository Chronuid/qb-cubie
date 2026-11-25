"""Generic rule registry, per-file parse cache, and FileCheckRunner for qb-cubie services."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence, Set as AbstractSet
from pathlib import Path
from typing import Any, Final, Protocol, TypeVar, runtime_checkable

from ..protocols import (
    DiagnosticProtocol,
    FileCheckProtocol,
    Reporter,
    validate_severity,
)
from .guards import validate_non_empty_str
from .reporting import ServiceReport
from .workspace import FileSource, find_project_root, load_sources, normalize_excludes

T = TypeVar("T")
_UNSET_REPORTER: Final[object] = object()


@runtime_checkable
class RuleProtocol(Protocol):
    """Minimal contract shared by all pluggable rules managed by RuleRegistry."""

    @property
    def rule_id(self) -> str: ...

    @property
    def severity(self) -> str | None: ...


class FileContextCache:
    """Per-file memoization cache ensuring expensive parses run once across all rules."""

    def __init__(self) -> None:
        """Initialize an empty per-file cache."""
        self._entries: dict[str, Any] = {}

    def get_or_compute(self, key: str, factory: Callable[[], T]) -> T:
        """Return cached value for key or compute, cache, and return factory()."""
        validate_non_empty_str(key, "cache key")
        if key not in self._entries:
            self._entries[key] = factory()
        return self._entries[key]


@runtime_checkable
class WorkspaceCheckRuleProtocol(Protocol):
    """Domain-neutral contract for multi-file check rules with per-file caching and depends_on."""

    @property
    def rule_id(self) -> str: ...

    @property
    def severity(self) -> str | None: ...

    @property
    def context_key(self) -> str: ...

    @property
    def depends_on(self) -> tuple[str, ...]: ...

    def prepare_workspace(self, sources: Sequence[FileSource], options: Mapping[str, Any]) -> Any: ...

    def check_file(
        self,
        source: FileSource,
        workspace_ctx: Any,
        file_cache: FileContextCache,
    ) -> Sequence[DiagnosticProtocol]: ...


class RuleRegistry:
    """Ordered registry flattening rule sequences, overriding by rule_id, and supporting merge slots."""

    def __init__(
        self,
        rules: Sequence[Any] = (),
        *,
        coerce: Callable[[Any], Any] | None = None,
        merge: Callable[[Any, Any], Any | None] | None = None,
    ) -> None:
        """Initialize the registry by flattening, coercing, and inserting all supplied rules."""
        self._coerce = coerce or self._default_coerce
        self._merge = merge
        self._entries: dict[str, Any] = {}
        self.register(*rules)

    @property
    def rules(self) -> tuple[Any, ...]:
        """Return the ordered immutable tuple of registered rule instances."""
        return tuple(self._entries.values())

    def register(self, *rules: Any) -> RuleRegistry:
        """Flatten, coerce, and register one or more rules or nested rule sequences."""
        for raw in _flatten_rules(rules):
            self._insert(self._coerce(raw))
        return self

    def remove(self, rule_id: str) -> None:
        """Remove all registered entries matching rule_id."""
        for key in [k for k, rule in self._entries.items() if getattr(rule, "rule_id", None) == rule_id]:
            del self._entries[key]

    def _insert(self, rule: Any) -> None:
        """Insert rule by rule_id, delegating collisions to the optional merge hook."""
        if self._merge is None:
            self._entries[rule.rule_id] = rule
            return
        for key, existing in list(self._entries.items()):
            if existing.rule_id == rule.rule_id:
                merged = self._merge(existing, rule)
                if merged is not None:
                    self._entries[key] = merged
                    return
        slot = rule.rule_id if rule.rule_id not in self._entries else self._unique_slot(rule.rule_id)
        self._entries[slot] = rule

    def _unique_slot(self, rule_id: str) -> str:
        """Allocate a collision-free slot key for coexisting rules sharing rule_id."""
        idx = len(self._entries)
        while f"{rule_id}#{idx}" in self._entries:
            idx += 1
        return f"{rule_id}#{idx}"

    @staticmethod
    def _default_coerce(raw: Any) -> Any:
        """Instantiate rule classes and validate RuleProtocol attributes."""
        inst = raw() if isinstance(raw, type) else raw
        if not isinstance(inst, RuleProtocol):
            raise TypeError(f"STATE-GUARD: Rule must implement RuleProtocol; received {type(inst).__name__}.")
        validate_non_empty_str(inst.rule_id, "rule_id")
        if inst.severity is not None:
            validate_severity(inst.severity)
        return inst


def _flatten_rules(items: Sequence[Any]) -> list[Any]:
    """Recursively flatten nested tuple/list rule collections."""
    flat: list[Any] = []
    for item in items:
        if isinstance(item, (list, tuple)):
            flat.extend(_flatten_rules(item))
        else:
            flat.append(item)
    return flat


def execute_file_checks(
    rules: Sequence[WorkspaceCheckRuleProtocol | FileCheckProtocol],
    sources: Sequence[FileSource],
    *,
    target: str | Path,
    excludes: AbstractSet[str],
    options: Mapping[str, Any] | None = None,
) -> list[DiagnosticProtocol]:
    """Execute WorkspaceCheckRuleProtocol and legacy FileCheckProtocol rules with per-file caching."""
    opts = dict(options or {})
    contexts = _prepare_contexts(rules, sources, target, excludes, opts)
    diagnostics: list[DiagnosticProtocol] = []
    for source in sources:
        diagnostics.extend(_check_single_source(rules, source, contexts))
    return diagnostics


def _prepare_contexts(
    rules: Sequence[WorkspaceCheckRuleProtocol | FileCheckProtocol],
    sources: Sequence[FileSource],
    target: str | Path,
    excludes: AbstractSet[str],
    options: Mapping[str, Any],
) -> dict[str, Any]:
    """Build each unique rule workspace context exactly once per run."""
    contexts: dict[str, Any] = {}
    excl_tuple = tuple(sorted(excludes))
    for rule in rules:
        if rule.context_key in contexts:
            continue
        if isinstance(rule, WorkspaceCheckRuleProtocol):
            contexts[rule.context_key] = rule.prepare_workspace(sources, options)
        else:
            contexts[rule.context_key] = rule.prepare_context(target, excl_tuple, options.get("patterns", ()))
    return contexts


def _check_single_source(
    rules: Sequence[WorkspaceCheckRuleProtocol | FileCheckProtocol],
    source: FileSource,
    contexts: Mapping[str, Any],
) -> list[DiagnosticProtocol]:
    """Run all applicable rules against one FileSource with shared FileContextCache and depends_on."""
    cache = FileContextCache()
    failed_errors: set[str] = set()
    file_diags: list[DiagnosticProtocol] = []
    for rule in rules:
        deps = getattr(rule, "depends_on", ())
        if any(dep in failed_errors for dep in deps):
            continue
        diags = _invoke_file_rule(rule, source, contexts[rule.context_key], cache)
        file_diags.extend(diags)
        if any(getattr(d, "severity", "error") == "error" for d in diags):
            failed_errors.add(rule.rule_id)
    return file_diags


def _invoke_file_rule(
    rule: WorkspaceCheckRuleProtocol | FileCheckProtocol,
    source: FileSource,
    workspace_ctx: Any,
    cache: FileContextCache,
) -> Sequence[DiagnosticProtocol]:
    """Dispatch a single check rule according to WorkspaceCheckRuleProtocol or legacy FileCheckProtocol."""
    if isinstance(rule, WorkspaceCheckRuleProtocol):
        return rule.check_file(source, workspace_ctx, cache)
    return rule.check_file(source.path, source.content, workspace_ctx)


class FileCheckRunner:
    """Domain-neutral multi-file verification host with caching, depends_on, and pluggable reporters."""

    def __init__(
        self,
        rules: Sequence[Any],
        *,
        target: str | Path | None = None,
        glob: str = "*.md",
        excludes: Sequence[str] | None = None,
        options: Mapping[str, Any] | None = None,
        service: str = "file_check",
        reporter: Reporter[ServiceReport] | None | object = _UNSET_REPORTER,
    ) -> None:
        """Validate configuration and build the ordered rule registry for multi-file verification."""
        self.service = validate_non_empty_str(service, "service")
        self.glob = validate_non_empty_str(glob, "glob")
        self.excludes = normalize_excludes(excludes)
        self.target: str | Path = target if target is not None else find_project_root()
        self.options = dict(options or {})
        self.reporter: Reporter[ServiceReport] | None = self._resolve_reporter(reporter)
        self.rules = self._coerce_runner_rules(rules)

    @staticmethod
    def _resolve_reporter(reporter: Reporter[ServiceReport] | None | object) -> Reporter[ServiceReport] | None:
        """Return the configured reporter or lazily instantiate the default PytestReporter."""
        if reporter is _UNSET_REPORTER:
            from ..reporter import PytestReporter

            return PytestReporter()
        return reporter  # type: ignore[return-value]

    @staticmethod
    def _coerce_runner_rules(rules: Sequence[Any]) -> tuple[WorkspaceCheckRuleProtocol | FileCheckProtocol, ...]:
        """Validate non-empty rule list and ensure every rule supports file checking."""
        registry = RuleRegistry(rules)
        if not registry.rules:
            raise ValueError("STATE-GUARD: FileCheckRunner requires at least one rule.")
        for rule in registry.rules:
            if not isinstance(rule, (WorkspaceCheckRuleProtocol, FileCheckProtocol)):
                raise TypeError(
                    "STATE-GUARD: FileCheckRunner rules must implement WorkspaceCheckRuleProtocol "
                    f"or FileCheckProtocol; received {type(rule).__name__}."
                )
        return registry.rules

    def run(self) -> ServiceReport:
        """Discover files, run all checks with per-file caching, notify reporter, and return ServiceReport."""
        __tracebackhide__ = True
        sources = load_sources(self.target, pattern=self.glob, excludes=self.excludes, allow_in_memory=False)
        diagnostics = execute_file_checks(
            self.rules, sources, target=self.target, excludes=self.excludes, options=self.options
        )
        passed = not any(getattr(d, "severity", "error") == "error" for d in diagnostics)
        report = ServiceReport(
            service=self.service,
            target=str(self.target),
            passed=passed,
            diagnostics=tuple(diagnostics),
            files_checked=len(sources),
        )
        if self.reporter is not None:
            self.reporter.report(report)
        return report
