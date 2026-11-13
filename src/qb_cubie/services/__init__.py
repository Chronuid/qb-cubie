"""Reusable quality assurance and verification services built on the qb-cubie core."""

from . import doc_ensurance, protocols
from .doc_ensurance import (
    CUBIE_DOC_STYLE,
    CodeSnippet,
    CollapsibleResult,
    DocEnsurance,
    ExamplePattern,
    Explanation,
    IsolatedScope,
    TaggedScope,
)
from .protocols import (
    DocBlockProtocol,
    DocDiagnostic,
    DocPatternProtocol,
    DocReport,
    DocScopeProtocol,
    ExampleSession,
    ExtractedExample,
    MdBlock,
    ServiceReportProtocol,
    SessionTrace,
)

__all__ = [
    "doc_ensurance",
    "protocols",
    "CUBIE_DOC_STYLE",
    "DocEnsurance",
    "ExamplePattern",
    "Explanation",
    "CodeSnippet",
    "CollapsibleResult",
    "IsolatedScope",
    "TaggedScope",
    "MdBlock",
    "ExtractedExample",
    "ExampleSession",
    "DocDiagnostic",
    "SessionTrace",
    "DocReport",
    "ServiceReportProtocol",
    "DocBlockProtocol",
    "DocPatternProtocol",
    "DocScopeProtocol",
]