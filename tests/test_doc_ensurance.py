"""Enforce living documentation code example conventions via DocEnsurance."""

from qb_cubie.core.services import CUBIE_DOC_RULES, CUBIE_DOC_STYLE, DocEnsurance

DOC_EXCLUDES = (
    ".pytest_cache",
    "tests",
    "experiments",  # Reason: I need to clean up the artifacts of the sprint in the core first.
    "docs/feature-drafts",  # Reason: Feature Drafts
    "GUTACHTEN.md",  # Reason: No Cubie-Rules apply to Inspectors.
    "docs/misc/lake",
    "CHANGELOG.md",
    "CI-Data.md",
)


def test_docs_code_examples() -> None:
    """Verifies that all documentation code examples follow Cubie conventions."""
    DocEnsurance(
        pattern=CUBIE_DOC_STYLE,
        rules=CUBIE_DOC_RULES,
        excludes=DOC_EXCLUDES,
    ).run()
