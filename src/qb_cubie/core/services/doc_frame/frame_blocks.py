"""Stateless Lego building blocks, routers, and protected content slots for DocFrame."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Final

from ...service_core.guards import parse_bool_attr
from ...service_core.workspace import WorkspaceView
from .protocols import (
    DocMeta,
    DocumentCatalog,
    FrameBlockProtocol,
    FrameRenderContext,
    validate_catalog_mode,
    validate_wrap_tag,
)

_HTML_WRAP_RE = re.compile(r"^</?(?:div|center)\b[^>]*>$", re.IGNORECASE)
_IMG_BANNER_RE = re.compile(r"^!\[[^\]]*\]\(([^)]+)\)$")
_PROV_BULLET_RE = re.compile(r"^-\s*\*\*([^*]+?):\*\*\s*(.*)$")
_EPISTEMIC_MARKER: Final[str] = "erkenntnistheoretischen Grenzen"
_ATTR_TO_PROV_KEY: Final[dict[str, str]] = {
    "env": "Plattform / Umgebung",
    "model": "Modell",
    "effort": "Reasoning-Effort",
}


def compute_rel_link(from_file: Path, target_rel: str, root: Path) -> str:
    """Computes a relative Markdown link prefixed with ./ or ../ from a source file to a repo path."""
    target_abs = (root.resolve() / target_rel.lstrip("/")).resolve()
    from_dir = from_file.resolve().parent
    rel = os.path.relpath(target_abs, start=from_dir).replace("\\", "/")
    return rel if rel.startswith(".") else f"./{rel}"


def resolve_banner_rel_path(
    banner: str, root: Path, workspace: WorkspaceView | None = None
) -> str:
    """Resolves a short banner filename or relative path against the repository asset directory."""
    _ = root
    clean = banner.strip().lstrip("./")
    if "/" in clean:
        return clean
    if (
        workspace is not None
        and workspace.has_path(f".assets/{clean}")
        and not workspace.has_path(f"docs/.assets/{clean}")
    ):
        return f".assets/{clean}"
    return f"docs/.assets/{clean}"


def _format_route_lines(routes: Sequence[tuple[str, str]], ctx: FrameRenderContext) -> str:
    """Formats a sequence of (label, repo_rel_path) pairs as bracketed footer route lines."""
    lines = [
        f"[↦ | {label} | ↤]({compute_rel_link(ctx.file_path, rel_target, ctx.catalog.root)})  "
        for label, rel_target in routes
    ]
    return "\n".join(lines)


def _strip_outer_html_wrappers(lines: list[str]) -> list[str]:
    """Removes leading and trailing <div align='center'> or <center> wrapper lines."""
    trimmed = [line for line in lines]
    while trimmed and (not trimmed[0].strip() or _HTML_WRAP_RE.match(trimmed[0].strip())):
        trimmed.pop(0)
    while trimmed and (not trimmed[-1].strip() or _HTML_WRAP_RE.match(trimmed[-1].strip())):
        trimmed.pop()
    return trimmed


def _split_by_dividers(lines: list[str]) -> list[list[str]]:
    """Splits a list of Markdown lines into segments separated by '---' horizontal rules."""
    segments: list[list[str]] = [[]]
    for line in lines:
        if line.strip() == "---":
            segments.append([])
        else:
            segments[-1].append(line)
    return segments


def _dedupe_dividers(items: Sequence[str]) -> list[str]:
    """Removes consecutive duplicate '---' divider blocks from a rendered block list."""
    result: list[str] = []
    for item in items:
        if item == "---" and result and result[-1] == "---":
            continue
        result.append(item)
    return result


# ========== 1. STRUCTURAL & STATIC NAVIGATION BLOCKS ==================================================================
@dataclass(frozen=True)
class Divider:
    """Renders a standard Markdown horizontal rule ('---')."""

    def render(self, ctx: FrameRenderContext) -> str:
        """Returns the horizontal rule string."""
        _ = ctx
        return "---"


@dataclass(frozen=True)
class StaticBlock:
    """Renders an immutable static Markdown block such as the mandatory epistemic notice anchor."""

    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("STATE-GUARD: StaticBlock text must be a non-empty string.")

    def render(self, ctx: FrameRenderContext) -> str:
        """Returns the trimmed static Markdown text."""
        _ = ctx
        return self.text.strip()


@dataclass(frozen=True)
class AssetImage:
    """Renders a depth-resolved Markdown image link for a repository asset."""

    path: str = "docs/.assets/cubie-small.png"
    alt: str = "Cubie"

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValueError("STATE-GUARD: AssetImage path must be a non-empty string.")
        if not isinstance(self.alt, str) or not self.alt.strip():
            raise ValueError("STATE-GUARD: AssetImage alt must be a non-empty string.")

    def render(self, ctx: FrameRenderContext) -> str:
        """Renders the Markdown image tag with a depth-adjusted relative path."""
        rel = compute_rel_link(ctx.file_path, self.path, ctx.catalog.root)
        return f"![{self.alt}]({rel})"


@dataclass(frozen=True)
class CenterWrap:
    """Wraps a sequence of child frame blocks inside a centered HTML container."""

    tag: str = "div"
    blocks: Sequence[FrameBlockProtocol] = ()

    def __post_init__(self) -> None:
        validate_wrap_tag(self.tag)

    def render(self, ctx: FrameRenderContext) -> str:
        """Renders non-empty child blocks joined by blank lines inside the HTML wrapper."""
        open_html = '<div align="center">' if self.tag == "div" else "<center>"
        close_html = f"</{self.tag}>"
        rendered = _dedupe_dividers([out for block in self.blocks if (out := block.render(ctx))])
        body = "\n\n".join(rendered)
        return f"{open_html}\n\n{body}\n\n{close_html}" if body else f"{open_html}\n{close_html}"


@dataclass(frozen=True)
class CompactNav:
    """Renders a single-line bullet-separated navigation bar with relative links."""

    routes: Sequence[tuple[str, str]] = ()
    separator: str = " • "

    def render(self, ctx: FrameRenderContext) -> str:
        """Renders all configured quick-nav routes relative to the current document."""
        items = [
            f"[{label}]({compute_rel_link(ctx.file_path, target, ctx.catalog.root)})"
            for label, target in self.routes
        ]
        return f"{self.separator.join(items)}  " if items else ""


@dataclass(frozen=True)
class RouteGroup:
    """Renders a static group of bracketed footer routes."""

    routes: Sequence[tuple[str, str]] = ()

    def render(self, ctx: FrameRenderContext) -> str:
        """Formats all static routes relative to the current file."""
        return _format_route_lines(self.routes, ctx)


# ========== 2. DYNAMIC CATALOG ROUTER BLOCKS ==========================================================================
@dataclass(frozen=True)
class FolderRouter:
    """Dynamically discovers and links routable Markdown documents in a target directory."""

    dir: str = "docs"
    glob: str = "*.md"
    exclude: Sequence[str] = ()

    def render(self, ctx: FrameRenderContext) -> str:
        """Queries the DocumentCatalog for the configured directory and formats route lines."""
        entries = ctx.catalog.select(self.dir, glob=self.glob, exclude=self.exclude)
        routes = [(e.label, e.path) for e in entries]
        return _format_route_lines(routes, ctx)


@dataclass(frozen=True)
class SiblingRouter:
    """Renders top-level area hubs and automatically expands sibling documents inside subfolders."""

    hubs: Sequence[tuple[str, str]] = ()
    include_hubs: bool = True
    exclude: Sequence[str] = ("README.md",)

    def render(self, ctx: FrameRenderContext) -> str:
        """Combines active area hubs with context-dependent sibling routes for subfolder files."""
        hub_routes: list[tuple[str, str]] = []
        sibling_routes: list[tuple[str, str]] = []
        seen: set[str] = set()
        parent_dir = Path(ctx.rel_path).parent.as_posix()
        expand_sub = parent_dir not in (".", "docs", "docs/services")
        if self.include_hubs:
            self._append_hubs(ctx.catalog, hub_routes, seen, skip_dir=parent_dir if expand_sub else None)
        if expand_sub:
            for entry in ctx.catalog.select(parent_dir, glob="*.md", exclude=self.exclude):
                if entry.path not in seen:
                    sibling_routes.append((entry.label, entry.path))
                    seen.add(entry.path)
        sections = [s for s in (_format_route_lines(hub_routes, ctx), _format_route_lines(sibling_routes, ctx)) if s]
        return "\n\n".join(sections)

    def _append_hubs(
        self, catalog: DocumentCatalog, routes: list[tuple[str, str]], seen: set[str], skip_dir: str | None = None
    ) -> None:
        """Resolves configured hub targets that exist in the catalog or their fallback folder entry."""
        for label, target in self.hubs:
            resolved = self._resolve_hub_target(catalog, target)
            if resolved is not None and Path(resolved).parent.as_posix() != skip_dir and resolved not in seen:
                routes.append((label, resolved))
                seen.add(resolved)

    @staticmethod
    def _resolve_hub_target(catalog: DocumentCatalog, target: str) -> str | None:
        """Returns the hub path if present in the catalog or the first routable file in its folder."""
        norm = Path(target).as_posix().strip("/")
        if catalog.get(norm) is not None or (catalog.workspace is not None and catalog.workspace.has_path(norm)):
            return norm
        folder_entries = catalog.select(Path(norm).parent.as_posix(), glob="*.md")
        return folder_entries[0].path if folder_entries else None


@dataclass(frozen=True)
class CatalogRouter:
    """Generates Markdown index tables or link lists from the DocumentCatalog for zone='router'."""

    default_mode: str = "table"
    exclude: Sequence[str] = ("README.md",)
    extract_summary: bool = True
    dir: str = "."
    recursive: bool = False

    def __post_init__(self) -> None:
        validate_catalog_mode(self.default_mode)

    def render(self, ctx: FrameRenderContext) -> str:
        """Renders either a two-column Markdown table or a route list for the target directory."""
        mode = validate_catalog_mode(ctx.span.attrs.get("mode", self.default_mode))
        target_dir = self._resolve_dir(ctx)
        recursive = self._resolve_recursive(ctx.span.attrs.get("recursive"))
        glob = ctx.span.attrs.get("glob", "*.md")
        entries = [
            e for e in ctx.catalog.select(target_dir, glob=glob, exclude=self.exclude, recursive=recursive)
            if e.path != ctx.rel_path
        ]
        if mode == "links":
            return _format_route_lines([(e.label, e.path) for e in entries], ctx)
        return self._render_table(entries, ctx)

    def _resolve_dir(self, ctx: FrameRenderContext) -> str:
        """Resolves the target directory attribute relative to the current file or catalog root."""
        raw = ctx.span.attrs.get("dir", self.dir).strip()
        if raw in ("", "."):
            return Path(ctx.rel_path).parent.as_posix()
        if ctx.catalog.workspace is not None and ctx.catalog.workspace.has_path(raw):
            return Path(raw).as_posix().strip("/")
        return (Path(ctx.rel_path).parent / raw).as_posix().strip("/")

    def _resolve_recursive(self, raw: str | None) -> bool:
        """Parses an optional boolean recursive attribute from the router frame tag."""
        return parse_bool_attr(raw, "recursive", default=self.recursive)

    def _render_table(self, entries: list[DocMeta], ctx: FrameRenderContext) -> str:
        """Formats catalog entries as a two-column Markdown index table."""
        rows = ["| Dokument | Inhalt und Geltung |", "| :--- | :--- |"]
        for entry in entries:
            rel = compute_rel_link(ctx.file_path, entry.path, ctx.catalog.root)
            summary = entry.summary if self.extract_summary else ""
            rows.append(f"| [{entry.label}]({rel}) | {summary} |")
        return "\n".join(rows)


CatalogTable = CatalogRouter


# ========== 3. PROTECTED CONTENT SLOTS ================================================================================
@dataclass(frozen=True)
class HeaderContentSlot:
    """Preserves H1 title and intro paragraphs while updating the relative banner image path."""

    default_banner: str = "cubie-logo-written.png"
    alt: str = "Cubie"

    def render(self, ctx: FrameRenderContext) -> str:
        """Reconstructs the header content slot with preserved title/intro and updated banner."""
        inner_lines = _strip_outer_html_wrappers(ctx.span.inner_content.splitlines())
        first_seg = _split_by_dividers(inner_lines)[0]
        title, existing_banner, body_lines = self._parse_header_parts(first_seg, ctx)
        banner_name = ctx.span.attrs.get("banner", "").strip() or existing_banner or self.default_banner
        banner_rel = compute_rel_link(
            ctx.file_path,
            resolve_banner_rel_path(banner_name, ctx.catalog.root, ctx.catalog.workspace),
            ctx.catalog.root,
        )
        parts = [f"# {title}", f"![{self.alt}]({banner_rel})"]
        intro = "\n".join(body_lines).strip()
        if intro:
            parts.append(intro)
        return "\n\n".join(parts)

    @staticmethod
    def _parse_header_parts(
        lines: list[str], ctx: FrameRenderContext
    ) -> tuple[str, str | None, list[str]]:
        """Separates the H1 heading, existing banner filename, and remaining intro lines."""
        title, banner, body = _scan_header_lines(lines)
        fallback = ctx.catalog.get(ctx.rel_path)
        resolved_title = title or (fallback.title if fallback else Path(ctx.rel_path).stem)
        return resolved_title, banner, body


def _scan_header_lines(lines: list[str]) -> tuple[str | None, str | None, list[str]]:
    """Iterates over header lines to isolate the first H1 title, banner image, and body lines."""
    title: str | None = None
    banner: str | None = None
    body: list[str] = []
    for line in lines:
        if title is None and line.strip().startswith("# "):
            title = line.strip()[2:].strip()
        elif banner is None and (m := _IMG_BANNER_RE.match(line.strip())):
            banner = Path(m.group(1)).name
        else:
            body.append(line)
    return title, banner, body


@dataclass(frozen=True)
class DisclaimerSlot:
    """Preserves an optional document-specific disclaimer block between header dividers."""

    optional: bool = True

    def render(self, ctx: FrameRenderContext) -> str:
        """Extracts document-specific disclaimer segments while filtering out the fixed epistemic anchor."""
        inner_lines = _strip_outer_html_wrappers(ctx.span.inner_content.splitlines())
        segments = _split_by_dividers(inner_lines)
        if len(segments) < 3:
            return ""
        middle = [
            text
            for seg in segments[1:-1]
            if (text := "\n".join(seg).strip()) and _EPISTEMIC_MARKER not in text
        ]
        return "\n\n---\n\n".join(middle)


@dataclass(frozen=True)
class TitleSlot:
    """Preserves an optional leading H1 title in CUBIE_DOC_FRAME_2 provenance headers."""

    optional: bool = True

    def render(self, ctx: FrameRenderContext) -> str:
        """Returns the existing H1 heading line or an optional title marker attribute."""
        for line in _split_by_dividers(ctx.span.inner_content.splitlines())[0]:
            if line.strip().startswith("# "):
                return line.strip()
        if "title" in ctx.span.attrs and ctx.span.attrs["title"].strip():
            return f"# {ctx.span.attrs['title'].strip()}"
        return ""


@dataclass(frozen=True)
class ProvenanceBlock:
    """Synchronizes required provenance metadata keys with marker attributes and preserves custom keys."""

    required_keys: Sequence[str] = ("Plattform / Umgebung", "Modell", "Reasoning-Effort")

    def __post_init__(self) -> None:
        if not self.required_keys or not all(isinstance(k, str) and k.strip() for k in self.required_keys):
            raise ValueError("STATE-GUARD: ProvenanceBlock required_keys must be non-empty strings.")

    def render(self, ctx: FrameRenderContext) -> str:
        """Renders the provenance header list with updated required fields and preserved extra items."""
        existing = self._parse_existing_bullets(ctx.span.inner_content)
        overrides = self._extract_attr_overrides(ctx.span.attrs)
        merged: dict[str, str] = {}
        for req_key in self.required_keys:
            merged[req_key] = overrides.get(req_key, existing.get(req_key, ""))
        for key, val in existing.items():
            if key not in merged:
                merged[key] = val
        bullets = [f"- **{k}:** {v}".rstrip() if v else f"- **{k}:** " for k, v in merged.items()]
        return "\n".join(["**Dokument-Informationen & Herkunft:**", *bullets])

    @staticmethod
    def _parse_existing_bullets(inner_content: str) -> dict[str, str]:
        """Parses existing '- **Key:** Value' lines before the first divider."""
        bullets: dict[str, str] = {}
        for line in _split_by_dividers(inner_content.splitlines())[0]:
            if match := _PROV_BULLET_RE.match(line.strip()):
                bullets[match.group(1).strip()] = match.group(2).strip()
        return bullets

    def _extract_attr_overrides(self, attrs: dict[str, str]) -> dict[str, str]:
        """Maps shorthand marker attributes (env, model, effort) to provenance field names."""
        overrides: dict[str, str] = {}
        for attr_key, target_key in _ATTR_TO_PROV_KEY.items():
            if attr_key in attrs and attrs[attr_key].strip():
                overrides[target_key] = attrs[attr_key].strip()
        for req_key in self.required_keys:
            if req_key in attrs and attrs[req_key].strip():
                overrides[req_key] = attrs[req_key].strip()
        return overrides


@dataclass(frozen=True)
class PromptSlot:
    """Preserves an optional prompt or question text below the divider in CUBIE_DOC_FRAME_2."""

    optional: bool = True

    def render(self, ctx: FrameRenderContext) -> str:
        """Extracts and returns any text following the first horizontal rule inside the head frame."""
        segments = _split_by_dividers(ctx.span.inner_content.splitlines())
        if len(segments) < 2:
            return ""
        rest = "\n---\n".join("\n".join(seg) for seg in segments[1:])
        return rest.strip()
