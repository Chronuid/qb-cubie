"""Tries to verify isomorphisms between Markdown-hosted code fences and Python-hosted docstrings."""

import ast
from typing import Any, Sequence

from qb_cubie import EBT, TempFS, WorldState
from qb_cubie.services import CUBIE_DOC_STYLE, DocEnsurance, MdBlock
from qb_cubie.services.doc_ensurance import _MarkdownScanner
from qb_cubie.services.protocols import DocDiagnostic, ExtractedExample


# ========== 1. FUNKTOR: MARKDOWN (M) -> LITERATE PYTHON MODULE (P) ====================================================
def _md_to_literate_py(md_source: str) -> str:
    """Transforms a Markdown document with Python fences into an isomorphic Python module."""
    blocks = _MarkdownScanner(md_source).parse()
    chunks = [_block_to_py_chunk(block) for block in blocks]
    return "\n\n".join(chunks) + "\n"


def _block_to_py_chunk(block: MdBlock) -> str:
    """Converts a single MdBlock into either a Python docstring literal or executable code."""
    if block.kind == "code":
        return f"# @cubie_fence: {block.meta}\n{block.content}"
    if block.kind == "details":
        raw = f"<details>\n<summary>{block.meta}</summary>\n\n{block.content}\n</details>"
        return repr(raw)
    return repr(block.content)


# ========== 2. DUALES PROTOKOLL: PYTHON-AST -> DOC-BLOCKS (P -> M) ====================================================
class PyDocstringPattern:
    """Dual DocPatternProtocol that parses a Python AST with docstrings into MdBlocks."""

    def __init__(self, inner: Any = CUBIE_DOC_STYLE) -> None:
        """Initializes the dual Python AST pattern wrapping a standard block pattern."""
        self.inner = inner

    @property
    def name(self) -> str:
        """Returns the identifier of the dual Python docstring pattern."""
        return f"py-ast-{self.inner.name}"

    def scan(
        self, blocks: Sequence[MdBlock], file_path: str
    ) -> tuple[list[ExtractedExample], list[DocDiagnostic]]:
        """Reconstructs the Python source, extracts AST blocks, and delegates to inner.scan."""
        py_source = "\n\n".join(b.content for b in blocks)
        ast_blocks = _extract_blocks_from_py_ast(py_source)
        return self.inner.scan(ast_blocks, file_path)


def _extract_blocks_from_py_ast(py_source: str) -> list[MdBlock]:
    """Walks a parsed Python AST and separates docstring literals from code statement groups."""
    tree = ast.parse(py_source)
    lines = py_source.splitlines()
    blocks: list[MdBlock] = []
    code_Buf: list[ast.stmt] = []
    for stmt in tree.body:
        if _is_docstring_stmt(stmt):
            _flush_code_buffer(code_Buf, lines, blocks)
            blocks.append(_docstring_stmt_to_block(stmt))
        else:
            code_Buf.append(stmt)
    _flush_code_buffer(code_Buf, lines, blocks)
    return blocks


def _is_docstring_stmt(stmt: ast.stmt) -> bool:
    """Checks whether an AST statement is a standalone string literal expression."""
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    )


def _docstring_stmt_to_block(stmt: ast.stmt) -> MdBlock:
    """Converts a standalone AST string literal into a paragraph or details MdBlock."""
    text = str(getattr(stmt, "value").value).strip()
    if text.startswith("<details"):
        return _MarkdownScanner._build_details_block(text, stmt.lineno)
    kind = "heading" if text.startswith("#") else "paragraph"
    return MdBlock(kind=kind, content=text, line=stmt.lineno)


def _flush_code_buffer(
    buf: list[ast.stmt], lines: list[str], blocks: list[MdBlock]
) -> None:
    """Slices consecutive non-docstring AST statements into a single code MdBlock."""
    if not buf:
        return
    start_line = buf[0].lineno
    end_line = buf[-1].end_lineno or start_line
    meta = _find_fence_meta(lines, start_line)
    code = "\n".join(lines[start_line - 1 : end_line])
    blocks.append(MdBlock(kind="code", content=code, line=start_line, meta=meta))
    buf.clear()


def _find_fence_meta(lines: list[str], start_line: int) -> str:
    """Reads the preceding # @cubie_fence comment to restore session and raises tags."""
    idx = start_line - 2
    while idx >= 0 and not lines[idx].strip():
        idx -= 1
    if idx >= 0 and lines[idx].strip().startswith("# @cubie_fence:"):
        return lines[idx].strip().removeprefix("# @cubie_fence:").strip()
    return "python"


# ========== 3. KOMMUTATIVER ISOMORPHIE-PRÜFER =========================================================================
def _evaluate_isomorphism(md_doc: str) -> dict[str, Any]:
    """Evaluates both the Markdown domain (M) and the transformed Python domain (P)."""
    py_module = _md_to_literate_py(md_doc)
    ast.parse(py_module)
    md_report = DocEnsurance(target=md_doc, pattern=CUBIE_DOC_STYLE, reporter=None).run()
    py_report = DocEnsurance(
        target=py_module, pattern=PyDocstringPattern(CUBIE_DOC_STYLE), reporter=None
    ).run()
    md_summary = _summarize_report(md_report)
    py_summary = _summarize_report(py_report)
    return {
        "isomorphic": md_summary == py_summary,
        "summary": md_summary,
    }


def _summarize_report(report: Any) -> dict[str, Any]:
    """Projects a DocReport onto its canonical semantic observables (passed, outputs, rules)."""
    return {
        "passed": report.passed,
        "outputs": [list(s.actual_outputs) for s in report.sessions],
        "rules": [d.rule_id for d in report.diagnostics],
    }


# ========== 4. SPEZIFIKATIONS-KORPUS FÜR DEN ISOMORPHIE-CHECK =========================================================
_VALID_SESSION_SPEC = (
    "# Kapitel: Geteilte Zustände\n\n"
    "Schritt 1 initialisiert die Variable x in der Session alpha.\n\n"
    "```python session=alpha\nx = 21\nprint(x)\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n21\n```\n</details>\n\n"
    "Schritt 2 verdoppelt x und greift auf denselben Namensraum zu.\n\n"
    "```python session=alpha\ny = x * 2\nprint(y)\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n42\n```\n</details>"
)

_EXPECTED_RAISES_SPEC = (
    "Schritt 1 legt ein Dictionary in der Session beta an.\n\n"
    "```python session=beta\ndata = {'a': 1}\nprint(len(data))\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n1\n```\n</details>\n\n"
    "Schritt 2 provoziert einen erwarteten KeyError ohne die Session zu zerstören.\n\n"
    "```python session=beta raises=KeyError\nprint(data['missing'])\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\nKeyError: 'missing'\n```\n</details>\n\n"
    "Schritt 3 arbeitet auf dem intakten Dictionary aus Schritt 1 weiter.\n\n"
    "```python session=beta\ndata['b'] = 2\nprint(len(data))\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n2\n```\n</details>"
)

_DOC_PRE_IN_SESSION_NO_CASCADE_SPEC = (
    "Schritt 1 legt die Variable x in der Session gamma sauber an.\n\n"
    "```python session=gamma\nx = 10\nprint(x)\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n10\n```\n</details>\n\n"
    "Kurz.\n\n"
    "```python session=gamma\ny = x + 5\nprint(y)\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n15\n```\n</details>\n\n"
    "Schritt 3 nutzt y aus Schritt 2 und darf keinen künstlichen NameError werfen.\n\n"
    "```python session=gamma\nprint(y * 2)\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n30\n```\n</details>"
)

_RUNTIME_CRASH_CASCADE_SPEC = (
    "Schritt 1 initialisiert base in der Session delta.\n\n"
    "```python session=delta\nbase = 10\nprint(base)\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n10\n```\n</details>\n\n"
    "Schritt 2 bricht zur Laufzeit mit ZeroDivisionError vor der Zuweisung ab.\n\n"
    "```python session=delta\n_ = 1 / 0\nderived = base * 2\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n20\n```\n</details>\n\n"
    "Schritt 3 scheitert nun legitim mit einem echten NameError.\n\n"
    "```python session=delta\nprint(derived)\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n20\n```\n</details>"
)


def test_ebt_markdown_and_python_docstring_isomorphism() -> None:
    """Verifies that Markdown fences and Python docstring modules commute across all states."""
    EBT(
        target=_evaluate_isomorphism,
        arena=TempFS(),
        pre=[
            WorldState(args=(_VALID_SESSION_SPEC,)),
            WorldState(args=(_EXPECTED_RAISES_SPEC,)),
            WorldState(args=(_DOC_PRE_IN_SESSION_NO_CASCADE_SPEC,)),
            WorldState(args=(_RUNTIME_CRASH_CASCADE_SPEC,)),
        ],
        post=[
            WorldState(
                returns={
                    "isomorphic": True,
                    "summary": {"passed": True, "outputs": [["21", "42"]], "rules": []},
                }
            ),
            WorldState(
                returns={
                    "isomorphic": True,
                    "summary": {
                        "passed": True,
                        "outputs": [["1", "KeyError: 'missing'", "2"]],
                        "rules": [],
                    },
                }
            ),
            WorldState(
                returns={
                    "isomorphic": True,
                    "summary": {
                        "passed": False,
                        "outputs": [["10", "15", "30"]],
                        "rules": ["DOC-PRE"],
                    },
                }
            ),
            WorldState(
                returns={
                    "isomorphic": True,
                    "summary": {
                        "passed": False,
                        "outputs": [["10", "", ""]],
                        "rules": ["DOC-EXEC", "DOC-EXEC"],
                    },
                }
            ),
        ],
        custom_id="doc_ensurance_md_py_isomorphism",
    ).run()