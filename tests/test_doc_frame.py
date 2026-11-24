"""Enforce repository-wide Markdown document frames and epistemic notice anchors via DocFrame rules."""

from qb_cubie.core.services import (
    CUBIE_DOC_FRAME_1,
    CUBIE_DOC_FRAME_2,
    CUBIE_DOC_FRAME_3,
    CUBIE_DOCFRAME_RULES,
    DocEnsurance,
)

from tests.test_doc_ensurance import DOC_EXCLUDES


def test_docs_frames() -> None:
    """Verifies that all documentation frames follow Cubie DocFrame conventions."""
    DocEnsurance(
        pattern=(
            CUBIE_DOC_FRAME_1,
            CUBIE_DOC_FRAME_2,
            CUBIE_DOC_FRAME_3,
        ),
        rules=CUBIE_DOCFRAME_RULES,
        excludes=DOC_EXCLUDES,
    ).run()
