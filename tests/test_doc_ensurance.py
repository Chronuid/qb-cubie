"""Enforce living documentation code example conventions via DocEnsurance."""

from qb_cubie.core.services import (
    CUBIE_DOC_STYLE,
    DocEnsurance,
    DocRuleSet,
    HighComplexity,
    LargeOutput,
    NoOutput,
    RawTraceback,
)

DOC_EXCLUDES = (
    ".pytest_cache",
    "tests",
    "experiments",  # Reason: I need to clean up the artifacts of the sprint in the core first.
    "docs/feature-drafts",  # Reason: Feature Drafts
    "GUTACHTEN.md",  # Reason: No Cubie-Rules apply to Inspectors.
    "docs/misc/lake",
    "docs/misc/runs",  # Reason: Active TGD minimal tickets and run artifacts (E4).
    "CHANGELOG.md",
    "CI-Data.md",
)

REPO_DOC_RULES = DocRuleSet(
    rules=(
        NoOutput(severity="warning"),
        HighComplexity(max_lines=30, severity="error"),
        LargeOutput(max_lines=25, severity="warning"),
        RawTraceback(severity="warning"),
    )
)


def test_docs_code_examples() -> None:
    """Verifies that all documentation code examples follow Cubie conventions."""
    DocEnsurance(
        pattern=CUBIE_DOC_STYLE,
        rules=(REPO_DOC_RULES,),
        excludes=DOC_EXCLUDES,
    ).run()
