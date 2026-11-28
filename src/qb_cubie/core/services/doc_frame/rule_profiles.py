"""Preset-scoped rule binding profiles and rule sets for DocFrame."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from ...protocols import DiagnosticProtocol, validate_severity
from ...service_core.rules import FileContextCache, WorkspaceCheckRuleProtocol
from ...service_core.workspace import FileSource
from .adapters import prepare_docframe_workspace
from .doc_frame_rules import (
    DocFrameBrokenRoute,
    DocFrameFootLinks,
    DocFrameMissing,
    DocFrameOutdated,
    DocFrameProvenanceIncomplete,
    _DocFrameContext,
    _parse_and_validate_spans,
)
from .presets import CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOC_FRAME_3, FramePattern


def _coerce_pattern_id(pattern: Any) -> str:
    """Validate a FramePattern or non-empty pattern ID string and return its ID."""
    if isinstance(pattern, FramePattern):
        return pattern.id
    if isinstance(pattern, bool) or not isinstance(pattern, str):
        raise TypeError("STATE-GUARD: FrameRuleProfile pattern must be a FramePattern or string ID.")
    cleaned = pattern.strip()
    if not cleaned:
        raise ValueError("STATE-GUARD: FrameRuleProfile pattern ID must not be empty.")
    return cleaned


def _coerce_profile_rules(rules: Any) -> tuple[WorkspaceCheckRuleProtocol, ...]:
    """Validate and freeze a non-empty sequence of WorkspaceCheckRuleProtocol rules."""
    if isinstance(rules, (str, bytes)) or not isinstance(rules, Sequence) or not rules:
        raise ValueError("STATE-GUARD: FrameRuleProfile rules must be a non-empty sequence.")
    for item in rules:
        if isinstance(item, bool) or not isinstance(item, WorkspaceCheckRuleProtocol):
            raise TypeError("STATE-GUARD: FrameRuleProfile rules must implement WorkspaceCheckRuleProtocol.")
    return tuple(rules)


def _get_cached_spans(
    source: FileSource,
    patterns: dict[str, FramePattern],
    file_cache: FileContextCache,
) -> list[Any]:
    """Parse and cache frame spans once per file."""
    spans, _ = file_cache.get_or_compute(
        "doc_frame:parsed_spans",
        lambda: _parse_and_validate_spans(source.path, source.content, patterns),
    )
    return spans


def _run_scoped_rules(
    rules: Sequence[WorkspaceCheckRuleProtocol],
    source: FileSource,
    workspace_ctx: _DocFrameContext,
    file_cache: FileContextCache,
) -> list[DiagnosticProtocol]:
    """Execute rules sequentially for a matching profile while honoring depends_on error guards."""
    failed: set[str] = set()
    diags: list[DiagnosticProtocol] = []
    for rule in rules:
        if any(dep in failed for dep in rule.depends_on):
            continue
        emitted = list(rule.check_file(source, workspace_ctx, file_cache))
        diags.extend(emitted)
        if any(d.severity == "error" for d in emitted):
            failed.add(rule.rule_id)
    return diags


@dataclass(frozen=True)
class FrameRuleProfile:
    """Binds a single FramePattern preset to its dedicated sequence of atomic DocFrame rules."""

    pattern: FramePattern | str
    rules: Sequence[WorkspaceCheckRuleProtocol]

    def __post_init__(self) -> None:
        _coerce_pattern_id(self.pattern)
        object.__setattr__(self, "rules", _coerce_profile_rules(self.rules))

    @property
    def pattern_id(self) -> str:
        """Return the FramePattern identifier bound to this profile."""
        return _coerce_pattern_id(self.pattern)

    @property
    def rule_id(self) -> str:
        """Return a collision-free rule_id scoped to the bound FramePattern."""
        return f"DOCFRAME-PROFILE:{self.pattern_id}"

    @property
    def severity(self) -> str:
        """Return default severity for RuleProtocol compatibility."""
        return "error"

    @property
    def context_key(self) -> str:
        """Share the doc_frame workspace context across all profiles."""
        return "doc_frame"

    @property
    def depends_on(self) -> tuple[str, ...]:
        """Return empty top-level dependencies (handled per-rule inside the profile)."""
        return ()

    def prepare_workspace(self, sources: Sequence[FileSource], options: Mapping[str, Any]) -> _DocFrameContext:
        """Build or reuse the shared DocumentCatalog and FramePattern map via adapters."""
        return prepare_docframe_workspace(sources, options)

    def check_file(
        self,
        source: FileSource,
        workspace_ctx: _DocFrameContext,
        file_cache: FileContextCache,
    ) -> list[DiagnosticProtocol]:
        """Evaluate bound rules only when source contains spans for this profile's pattern_id."""
        spans = _get_cached_spans(source, workspace_ctx[1], file_cache)
        if not any(s.frame_id == self.pattern_id for s in spans):
            return []
        return _run_scoped_rules(self.rules, source, workspace_ctx, file_cache)


def _validate_profiles(profiles: Any) -> tuple[FrameRuleProfile, ...]:
    """Validate a non-empty sequence of FrameRuleProfile objects with unique pattern IDs."""
    if isinstance(profiles, (str, bytes)) or not isinstance(profiles, Sequence) or not profiles:
        raise ValueError("STATE-GUARD: DocFrameRuleSet profiles must be a non-empty sequence.")
    seen: set[str] = set()
    for prof in profiles:
        if isinstance(prof, bool) or not isinstance(prof, FrameRuleProfile):
            raise TypeError("STATE-GUARD: DocFrameRuleSet items must be FrameRuleProfile instances.")
        if prof.pattern_id in seen:
            raise ValueError(f"STATE-GUARD: Duplicate FrameRuleProfile for {prof.pattern_id!r}.")
        seen.add(prof.pattern_id)
    return tuple(profiles)


@dataclass(frozen=True)
class DocFrameRuleSet:
    """Aggregates preset-specific FrameRuleProfile bindings into a single WorkspaceCheckRuleProtocol."""

    profiles: Sequence[FrameRuleProfile]
    rule_id: str = "DOCFRAME-RULESET"
    severity: str = "error"

    def __post_init__(self) -> None:
        validate_severity(self.severity)
        object.__setattr__(self, "profiles", _validate_profiles(self.profiles))

    @property
    def context_key(self) -> str:
        """Share the doc_frame workspace context across all DocFrame rules."""
        return "doc_frame"

    @property
    def depends_on(self) -> tuple[str, ...]:
        """Return empty top-level dependencies."""
        return ()

    def prepare_workspace(self, sources: Sequence[FileSource], options: Mapping[str, Any]) -> _DocFrameContext:
        """Build or reuse the shared DocumentCatalog and FramePattern map via adapters."""
        return prepare_docframe_workspace(sources, options)

    def check_file(
        self,
        source: FileSource,
        workspace_ctx: _DocFrameContext,
        file_cache: FileContextCache,
    ) -> list[DiagnosticProtocol]:
        """Dispatch file checks to matching FrameRuleProfiles or fallback to the first profile on unframed files."""
        spans = _get_cached_spans(source, workspace_ctx[1], file_cache)
        if not spans:
            return _run_scoped_rules(self.profiles[0].rules, source, workspace_ctx, file_cache)
        span_ids = {s.frame_id for s in spans}
        matching = (p for p in self.profiles if p.pattern_id in span_ids)
        return [d for p in matching for d in _run_scoped_rules(p.rules, source, workspace_ctx, file_cache)]


CUBIE_DOCFRAME_RULE_SET: Final[DocFrameRuleSet] = DocFrameRuleSet(
    profiles=(
        FrameRuleProfile(
            pattern=CUBIE_DOC_FRAME_1,
            rules=(
                DocFrameMissing(severity="error"),
                DocFrameOutdated(severity="error"),
                DocFrameBrokenRoute(severity="error"),
                DocFrameFootLinks(severity="error"),
            ),
        ),
        FrameRuleProfile(
            pattern=CUBIE_DOC_FRAME_2,
            rules=(
                DocFrameMissing(severity="error"),
                DocFrameOutdated(severity="error", allow_empty_foot=True),
                DocFrameBrokenRoute(severity="error"),
                DocFrameProvenanceIncomplete(severity="error"),
                DocFrameFootLinks(severity="warning"),
            ),
        ),
        FrameRuleProfile(
            pattern=CUBIE_DOC_FRAME_3,
            rules=(
                DocFrameMissing(severity="error"),
                DocFrameOutdated(severity="error", allow_empty_foot=True),
                DocFrameBrokenRoute(severity="error"),
                DocFrameFootLinks(severity="warning"),
            ),
        ),
    )
)
