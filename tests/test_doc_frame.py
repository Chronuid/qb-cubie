"""Enforce repository-wide Markdown document frames and epistemic notice anchors via DocFrame.check()."""

from qb_cubie.core.services import (
    CUBIE_DOC_FRAME_1,
    CUBIE_DOC_FRAME_2,
    CUBIE_DOC_FRAME_3,
    DocFrame,
    DocFrameBrokenRoute,
    DocFrameFootLinks,
    DocFrameMissing,
    DocFrameOutdated,
    DocFrameProvenanceIncomplete,
    DocFrameRuleSet,
    FrameRuleProfile,
)

from tests.test_doc_ensurance import DOC_EXCLUDES

CUBIE_DOCFRAME_PROFILE_1 = FrameRuleProfile(
    pattern=CUBIE_DOC_FRAME_1,
    rules=(
        DocFrameMissing(severity="error"),
        DocFrameOutdated(severity="error"),
        DocFrameBrokenRoute(severity="error"),
        DocFrameFootLinks(severity="error"),
    ),
)

CUBIE_DOCFRAME_PROFILE_2 = FrameRuleProfile(
    pattern=CUBIE_DOC_FRAME_2,
    rules=(
        DocFrameMissing(severity="error"),
        DocFrameOutdated(severity="error", allow_empty_foot=True),
        DocFrameBrokenRoute(severity="error"),
        DocFrameProvenanceIncomplete(severity="error"),
        DocFrameFootLinks(severity="warning"),
    ),
)

CUBIE_DOCFRAME_PROFILE_3 = FrameRuleProfile(
    pattern=CUBIE_DOC_FRAME_3,
    rules=(
        DocFrameMissing(severity="error"),
        DocFrameOutdated(severity="error", allow_empty_foot=True),
        DocFrameBrokenRoute(severity="error"),
        DocFrameFootLinks(severity="warning"),
    ),
)

REPO_DOCFRAME_RULES = DocFrameRuleSet(
    profiles=(
        CUBIE_DOCFRAME_PROFILE_1,
        CUBIE_DOCFRAME_PROFILE_2,
        CUBIE_DOCFRAME_PROFILE_3,
    )
)


def test_docs_frames() -> None:
    """Verifies that all documentation frames follow Cubie DocFrame conventions."""
    DocFrame.check(
        pattern=(
            CUBIE_DOC_FRAME_1,
            CUBIE_DOC_FRAME_2,
            CUBIE_DOC_FRAME_3,
        ),
        rules=(REPO_DOCFRAME_RULES,),
        excludes=DOC_EXCLUDES,
    )
