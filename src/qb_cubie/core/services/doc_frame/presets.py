"""Central preset definitions and mandatory epistemic notice anchor for Cubie Markdown document frames."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Final

from ...protocols import Diagnostic
from .frame_blocks import (
    AssetImage,
    CatalogRouter,
    CenterWrap,
    CompactNav,
    DisclaimerSlot,
    Divider,
    FolderRouter,
    HeaderContentSlot,
    PromptSlot,
    ProvenanceBlock,
    SiblingRouter,
    StaticBlock,
    TitleSlot,
)
from .protocols import (
    FrameBlockProtocol,
    FrameRenderContext,
    validate_zone,
)


@dataclass(frozen=True)
class FramePattern:
    """Defines the structural block composition for head, router, and foot zones."""

    id: str
    head: Sequence[FrameBlockProtocol] = ()
    foot: Sequence[FrameBlockProtocol] = ()
    router: Sequence[FrameBlockProtocol] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("STATE-GUARD: FramePattern id must be a non-empty string.")
        for zone_name, seq in (("head", self.head), ("foot", self.foot), ("router", self.router)):
            _validate_block_sequence(zone_name, seq)

    @property
    def name(self) -> str:
        """Returns the pattern identifier for compatibility with DocPatternProtocol."""
        return self.id

    def scan(
        self, blocks: Sequence[Any], file_path: str
    ) -> tuple[list[Any], list[Diagnostic]]:
        """Satisfies DocPatternProtocol when FramePattern is passed in DocEnsurance(pattern=...)."""
        _ = (blocks, file_path)
        return [], []

    def render_zone(self, zone: str, ctx: FrameRenderContext) -> str:
        """Renders all configured blocks for the requested zone ('head', 'router', or 'foot')."""
        validate_zone(zone)
        blocks = {"head": self.head, "router": self.router, "foot": self.foot}[zone]
        rendered = [out for block in blocks if (out := block.render(ctx))]
        return "\n\n".join(rendered)


def _validate_block_sequence(zone_name: str, seq: Any) -> None:
    """Validates that a zone block collection is a sequence of FrameBlockProtocol objects."""
    if isinstance(seq, (str, bytes)) or not isinstance(seq, Sequence):
        raise TypeError(f"STATE-GUARD: FramePattern.{zone_name} must be a sequence of frame blocks.")
    for item in seq:
        if not isinstance(item, FrameBlockProtocol):
            raise TypeError(
                f"STATE-GUARD: Block in {zone_name} must implement FrameBlockProtocol; got {type(item).__name__}."
            )


# ========== MANDATORY EPISTEMIC BOUNDARY NOTICE ANCHOR ================================================================
EPISTEMIC_NOTICE_TEXT: Final[str] = (
    "> [!NOTE]  \n"
    "> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers "
    "kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte "
    "Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  \n"
    ">\n"
    "> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  \n"
    "> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  \n"
    "> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  \n"
    "> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**"
)

EPISTEMIC_NOTICE: Final[StaticBlock] = StaticBlock(text=EPISTEMIC_NOTICE_TEXT)


# ========== STANDARD CUBIE DOC-FRAME PRESETS ==========================================================================
HEADER_QUICK_NAV: Final[CompactNav] = CompactNav(
    routes=(
        ("README", "README.md"),
        ("QA-Handbuch", "docs/GUIDE_Quality-Assurance.md"),
        ("DocEnsurance", "docs/services/GUIDE_DocEnsurance.md"),
    )
)

GUIDE_ROUTER: Final[FolderRouter] = FolderRouter(dir="docs", glob="GUIDE_*.md")
SERVICE_ROUTER: Final[FolderRouter] = FolderRouter(dir="docs/services", glob="GUIDE_*.md")
CONTEXT_ROUTER: Final[SiblingRouter] = SiblingRouter(
    hubs=(
        ("Dokumentations-Übersicht", "docs/README.md"),
        ("Core-Dokumentation", "docs/core/README.md"),
        ("Entwicklerdokumentation", "docs/dev/README.md"),
        ("Core-Internals", "docs/dev/core/README.md"),
        ("Hintergrund & Essays", "docs/misc/README.md"),
        ("Feature-Drafts: Virtualisierung", "docs/feature-drafts/virtualization/README.md"),
    )
)

STD_FOOTER_BLOCKS: Final[tuple[FrameBlockProtocol, ...]] = (
    Divider(),
    Divider(),
    CenterWrap(
        tag="div",
        blocks=(
            AssetImage(path="docs/.assets/cubie-small.png", alt="Cubie"),
            GUIDE_ROUTER,
            SERVICE_ROUTER,
            CONTEXT_ROUTER,
        ),
    ),
)

AUTO_INDEX_ROUTER: Final[CatalogRouter] = CatalogRouter(
    default_mode="table",
    exclude=("README.md",),
    extract_summary=True,
)

STD_HEAD_BLOCKS: Final[tuple[FrameBlockProtocol, ...]] = (
    CenterWrap(
        tag="div",
        blocks=(
            HeaderContentSlot(),
            Divider(),
            DisclaimerSlot(),
            Divider(),
            EPISTEMIC_NOTICE,
            Divider(),
            HEADER_QUICK_NAV,
        ),
    ),
)

CUBIE_DOC_FRAME_1: Final[FramePattern] = FramePattern(
    id="CUBIE_DOC_FRAME_1",
    head=STD_HEAD_BLOCKS,
    foot=STD_FOOTER_BLOCKS,
)

CUBIE_DOC_FRAME_2: Final[FramePattern] = FramePattern(
    id="CUBIE_DOC_FRAME_2",
    head=(
        TitleSlot(optional=True),
        ProvenanceBlock(required_keys=("Plattform / Umgebung", "Modell", "Reasoning-Effort")),
        Divider(),
        PromptSlot(optional=True),
    ),
    foot=STD_FOOTER_BLOCKS,
)

CUBIE_DOC_FRAME_3: Final[FramePattern] = FramePattern(
    id="CUBIE_DOC_FRAME_3",
    head=STD_HEAD_BLOCKS,
    router=(AUTO_INDEX_ROUTER,),
    foot=STD_FOOTER_BLOCKS,
)

DEFAULT_FRAME_PATTERNS: Final[tuple[FramePattern, ...]] = (
    CUBIE_DOC_FRAME_1,
    CUBIE_DOC_FRAME_2,
    CUBIE_DOC_FRAME_3,
)
