from __future__ import annotations

import contextlib
import dataclasses
import io
import re
from pathlib import Path
from typing import Any, Final, Sequence

from ..arenas.tempfs import TempFS
from ..linter import DEFAULT_EXCLUDES
from ..protocols import Arena, Reporter, WorldState
from ..reporter import PytestReporter
from .protocols import (
    DocBlockProtocol,
    DocDiagnostic,
    DocPatternProtocol,
    DocReport,
    DocScopeProtocol,
    ExampleSession,
    ExtractedExample,
    MdBlock,
    SessionTrace,
)

_SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.DOTALL)
_INNER_FENCE_RE = re.compile(r"^```[^\n]*\n(.*?)\n```$", re.DOTALL)
_TAG_RE = re.compile(r"(?P<key>session|raises)=(?P<val>[^\s]+)")


# ========== 1. ATOMIC BLOCK PROTOCOLS (LEVEL 1) =======================================================================
@dataclasses.dataclass(frozen=True)
class Explanation:
    """Matches a narrative Markdown paragraph with a required minimum character count."""
    min_chars: int = 20
    role: str = "explanation"

    def matches(self, block: MdBlock) -> bool:
        return block.kind == "paragraph" and len(block.content.strip()) >= self.min_chars

    def extract(self, block: MdBlock) -> str:
        return block.content.strip()


@dataclasses.dataclass(frozen=True)
class CodeSnippet:
    """Matches a fenced code block for a target language and extracts fence metadata."""
    lang: str = "python"
    role: str = "target"

    def matches(self, block: MdBlock) -> bool:
        tokens = block.meta.strip().split()
        return block.kind == "code" and bool(tokens) and tokens[0] == self.lang

    def extract(self, block: MdBlock) -> str:
        return block.content

    @staticmethod
    def parse_tags(meta: str) -> dict[str, str]:
        return {m.group("key"): m.group("val") for m in _TAG_RE.finditer(meta)}


@dataclasses.dataclass(frozen=True)
class CollapsibleResult:
    """Matches a collapsible HTML <details> block and strips optional inner code fences."""
    summary: str | None = None
    role: str = "result"

    def matches(self, block: MdBlock) -> bool:
        if block.kind != "details":
            return False
        return self.summary is None or self.summary in block.meta

    def extract(self, block: MdBlock) -> str:
        raw = block.content.strip()
        match = _INNER_FENCE_RE.match(raw)
        return match.group(1).strip() if match else raw


# ========== 2. PATTERN & SCOPE PROTOCOLS (LEVEL 2) ====================================================================
@dataclasses.dataclass(frozen=True)
class ExamplePattern:
    """Validates pre- and post-blocks around every anchor block in a Markdown stream."""
    anchor: DocBlockProtocol = CodeSnippet(lang="python")
    pre: Sequence[DocBlockProtocol] = ()
    post: Sequence[DocBlockProtocol] = ()
    name: str = "example-pattern"

    def scan(
        self, blocks: Sequence[MdBlock], file_path: str
    ) -> tuple[list[ExtractedExample], list[DocDiagnostic]]:
        examples: list[ExtractedExample] = []
        diagnostics: list[DocDiagnostic] = []
        for idx, block in enumerate(blocks):
            if self.anchor.matches(block):
                self._inspect_anchor(blocks, idx, file_path, examples, diagnostics)
        return examples, diagnostics

    def _inspect_anchor(
        self,
        blocks: Sequence[MdBlock],
        idx: int,
        file_path: str,
        examples: list[ExtractedExample],
        diagnostics: list[DocDiagnostic],
    ) -> None:
        anchor_block = blocks[idx]
        pre_ok, explanation = self._check_pre(blocks, idx, file_path, anchor_block.line, diagnostics)
        post_ok, expected_out = self._check_post(blocks, idx, file_path, anchor_block.line, diagnostics)
        if pre_ok and post_ok:
            examples.append(self._build_example(anchor_block, file_path, explanation, expected_out))

    def _check_pre(
        self, blocks: Sequence[MdBlock], idx: int, file_path: str, line: int, diags: list[DocDiagnostic]
    ) -> tuple[bool, str | None]:
        explanation: str | None = None
        for offset, rule in enumerate(reversed(self.pre), start=1):
            target_idx = idx - offset
            if target_idx < 0 or not rule.matches(blocks[target_idx]):
                diags.append(DocDiagnostic(file_path, "DOC-PRE", line, f"Missing or invalid pre-block '{rule.role}'."))
                return False, None
            explanation = rule.extract(blocks[target_idx])
        return True, explanation

    def _check_post(
        self, blocks: Sequence[MdBlock], idx: int, file_path: str, line: int, diags: list[DocDiagnostic]
    ) -> tuple[bool, str | None]:
        expected_out: str | None = None
        for offset, rule in enumerate(self.post, start=1):
            target_idx = idx + offset
            if target_idx >= len(blocks) or not rule.matches(blocks[target_idx]):
                diags.append(DocDiagnostic(file_path, "DOC-POST", line, f"Missing or invalid post-block '{rule.role}'."))
                return False, None
            expected_out = rule.extract(blocks[target_idx])
        return True, expected_out

    def _build_example(
        self, block: MdBlock, file_path: str, explanation: str | None, expected_out: str | None
    ) -> ExtractedExample:
        tags = CodeSnippet.parse_tags(block.meta)
        return ExtractedExample(
            file_path=file_path,
            line=block.line,
            code=self.anchor.extract(block),
            expected_output=expected_out,
            explanation=explanation,
            session_id=tags.get("session"),
            expected_raises=tags.get("raises"),
        )


CUBIE_DOC_STYLE: Final[ExamplePattern] = ExamplePattern(
    name="cubie-doc-style",
    pre=(Explanation(min_chars=20),),
    anchor=CodeSnippet(lang="python"),
    post=(CollapsibleResult(),),
)


class IsolatedScope:
    """Assigns every extracted example to its own isolated arena session."""

    def group(self, examples: Sequence[ExtractedExample]) -> list[ExampleSession]:
        return [
            ExampleSession(session_id=f"{ex.file_path}::isolated:{idx}", steps=(ex,))
            for idx, ex in enumerate(examples)
        ]


class TaggedScope:
    """Groups examples with identical `session=<id>` tags per file while keeping untagged blocks isolated."""

    def group(self, examples: Sequence[ExtractedExample]) -> list[ExampleSession]:
        buckets: dict[str, list[ExtractedExample]] = {}
        for idx, ex in enumerate(examples):
            suffix = f"session:{ex.session_id}" if ex.session_id else f"isolated:{idx}"
            key = f"{ex.file_path}::{suffix}"
            buckets.setdefault(key, []).append(ex)
        return [ExampleSession(session_id=k, steps=tuple(v)) for k, v in buckets.items()]


# ========== 3. ARENA SESSION WORKER (IPC-SAFE PRIMITIVES) =============================================================
def _execute_session_payload(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Top-level worker executed inside the Arena; shares globals and CWD across steps."""
    shared_globals: dict[str, Any] = {"__name__": "__main__"}
    return [_execute_single_step(step, shared_globals) for step in steps]


def _execute_single_step(step: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    """Executes one snippet, captures stdout, and intercepts expected exceptions."""
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            exec(compile(step["code"], f"<doc_line_{step['line']}>", "exec"), env)
    except Exception as error:  # noqa: BLE001 -- target observation inside documentation snippet
        return _classify_step_exception(error, step.get("expected_raises"))
    return _finalize_normal_step(buffer.getvalue().strip(), step.get("expected_raises"))


def _classify_step_exception(error: Exception, expected_raises: str | None) -> dict[str, Any]:
    """Determines whether a caught exception satisfies a declared `raises=` tag."""
    mro_names = {cls.__name__ for cls in type(error).__mro__}
    formatted = f"{type(error).__name__}: {error}"
    if expected_raises is not None:
        if expected_raises in mro_names:
            return {"status": "OK", "output": formatted}
        msg = f"Expected exception '{expected_raises}', but '{type(error).__name__}' was raised."
        return {"status": "DOC-RAISE", "output": formatted, "error": msg}
    return {"status": "DOC-EXEC", "output": "", "error": f"Unhandled {formatted}"}


def _finalize_normal_step(output: str, expected_raises: str | None) -> dict[str, Any]:
    """Checks whether an exception was expected when the snippet completed normally."""
    if expected_raises is not None:
        msg = f"Expected exception '{expected_raises}', but snippet completed normally."
        return {"status": "DOC-RAISE", "output": output, "error": msg}
    return {"status": "OK", "output": output}


# ========== 4. MARKDOWN BLOCK SCANNER =================================================================================
class _MarkdownScanner:
    """Lightweight line-based state machine converting Markdown text into MdBlocks."""

    def __init__(self, source: str) -> None:
        self.lines = source.splitlines()
        self.blocks: list[MdBlock] = []
        self.para_lines: list[str] = []
        self.para_start: int = 1

    def parse(self) -> list[MdBlock]:
        idx = 0
        while idx < len(self.lines):
            idx = self._consume_line(idx)
        self._flush_paragraph()
        return self.blocks

    def _consume_line(self, idx: int) -> int:
        line = self.lines[idx]
        stripped = line.strip()
        if stripped.startswith("```"):
            return self._consume_code_fence(idx, stripped[3:].strip())
        if stripped.startswith("<details"):
            return self._consume_details(idx)
        return self._consume_text_line(idx, line, stripped)

    def _consume_text_line(self, idx: int, line: str, stripped: str) -> int:
        if not stripped:
            self._flush_paragraph()
        elif stripped.startswith("#"):
            self._flush_paragraph()
            self.blocks.append(MdBlock(kind="heading", content=stripped, line=idx + 1))
        elif stripped.startswith(("- ", "* ")):
            self._flush_paragraph()
            self.blocks.append(MdBlock(kind="list", content=stripped, line=idx + 1))
        else:
            self._append_paragraph(line, idx + 1)
        return idx + 1

    def _append_paragraph(self, line: str, line_no: int) -> None:
        if not self.para_lines:
            self.para_start = line_no
        self.para_lines.append(line)

    def _flush_paragraph(self) -> None:
        if self.para_lines:
            content = "\n".join(self.para_lines).strip()
            self.blocks.append(MdBlock(kind="paragraph", content=content, line=self.para_start))
            self.para_lines = []

    def _consume_code_fence(self, start_idx: int, meta: str) -> int:
        self._flush_paragraph()
        body: list[str] = []
        idx = start_idx + 1
        while idx < len(self.lines) and not self.lines[idx].strip().startswith("```"):
            body.append(self.lines[idx])
            idx += 1
        self.blocks.append(MdBlock(kind="code", content="\n".join(body), line=start_idx + 1, meta=meta))
        return idx + 1

    def _consume_details(self, start_idx: int) -> int:
        self._flush_paragraph()
        raw_lines: list[str] = []
        idx = start_idx
        while idx < len(self.lines):
            raw_lines.append(self.lines[idx])
            if "</details>" in self.lines[idx]:
                break
            idx += 1
        self.blocks.append(self._build_details_block("\n".join(raw_lines), start_idx + 1))
        return idx + 1

    @staticmethod
    def _build_details_block(raw: str, line_no: int) -> MdBlock:
        summary_match = _SUMMARY_RE.search(raw)
        meta = summary_match.group(1).strip() if summary_match else ""
        body = _SUMMARY_RE.sub("", raw)
        body = re.sub(r"</?details[^>]*>", "", body).strip()
        return MdBlock(kind="details", content=body, line=line_no, meta=meta)


# ========== 5. DOC-ENSURANCE SERVICE (LEVEL 3) ========================================================================
class DocEnsurance:
    """Verifies structural conventions and runtime outputs of documentation code examples."""

    def __init__(
        self,
        target: str | Path | None = None,
        pattern: DocPatternProtocol | None = None,
        scope: DocScopeProtocol | None = None,
        arena: Arena | None = None,
        reporter: Reporter[DocReport] | None = PytestReporter(),
        pre_state: WorldState | None = None,
        excludes: Sequence[str] | None = None,
    ) -> None:
        """Initializes the documentation verification service with default project conventions."""
        self.target: str | Path = target if target is not None else self._default_project_dir()
        self.pattern = pattern or CUBIE_DOC_STYLE
        self.scope = scope or TaggedScope()
        self.arena = arena if arena is not None else TempFS()
        self.reporter = reporter
        self.pre_state = pre_state or WorldState()
        self.excludes = set(DEFAULT_EXCLUDES) | set(excludes or ())
        self._reset_state()

    def _reset_state(self) -> None:
        """Resets internal pipeline buffers before a verification run."""
        self._sources: list[tuple[str, str]] = []
        self._sessions: list[ExampleSession] = []
        self._diagnostics: list[DocDiagnostic] = []
        self._traces: list[SessionTrace] = []
        self.report_result: DocReport | None = None

    @staticmethod
    def _default_project_dir() -> Path:
        """Resolves the project root directory relative to CWD or pyproject.toml."""
        cwd = Path.cwd().resolve()
        for directory in (cwd, *cwd.parents):
            if (directory / "pyproject.toml").exists():
                return directory
        return cwd

    # ---------- SERVICES ----------------------------------------------------------------------------------------------
    def run(self) -> DocReport:
        """Executes the documentation verification pipeline and returns the report."""
        __tracebackhide__ = True
        self._arrange()
        self._validate()
        self._report()
        if self.report_result is None:
            raise RuntimeError("STATE-GUARD: DocEnsurance run yielded no report_result.")
        return self.report_result

    # ---------- PIPES -------------------------------------------------------------------------------------------------
    def _arrange(self) -> None:
        """Validates inputs, parses Markdown blocks, and groups valid examples into sessions."""
        __tracebackhide__ = True
        self._sources = self._resolve_sources(self.target, self.excludes)
        self._sessions = []
        self._diagnostics = []
        self._traces = []
        all_examples: list[ExtractedExample] = []
        for file_path, content in self._sources:
            blocks = _MarkdownScanner(content).parse()
            examples, diags = self.pattern.scan(blocks, file_path)
            all_examples.extend(examples)
            self._diagnostics.extend(diags)
        self._sessions = self.scope.group(all_examples)

    def _validate(self) -> None:
        """Executes each grouped session inside the configured Arena and checks outputs."""
        __tracebackhide__ = True
        for session in self._sessions:
            trace, diags = self._execute_session(session)
            self._traces.append(trace)
            self._diagnostics.extend(diags)

    def _report(self) -> None:
        """Builds the final DocReport and delegates it to the configured reporter."""
        __tracebackhide__ = True
        is_memory = bool(self._sources) and self._sources[0][0] == "IN_MEMORY"
        target_label = "IN_MEMORY" if is_memory else str(self.target)
        self.report_result = DocReport(
            target=target_label,
            passed=not bool(self._diagnostics),
            sessions=tuple(self._traces),
            diagnostics=tuple(self._diagnostics),
        )
        if self.reporter is not None:
            self.reporter.report(self.report_result)

    # ---------- UTILITIES ---------------------------------------------------------------------------------------------
    @classmethod
    def _resolve_sources(cls, target: Any, excludes: set[str]) -> list[tuple[str, str]]:
        """Validates the target and loads Markdown content from file, directory, or memory."""
        if isinstance(target, Path):
            return cls._load_path_sources(target, excludes)
        if isinstance(target, str):
            if not target.strip():
                raise ValueError("STATE-GUARD: Markdown target string must not be empty.")
            if "\n" not in target and (target.endswith(".md") or Path(target).exists()):
                return cls._load_path_sources(Path(target), excludes)
            return [("IN_MEMORY", target)]
        raise TypeError(
            f"STATE-GUARD: target must be a Markdown str or Path; received {type(target).__name__}."
        )

    @classmethod
    def _load_path_sources(cls, target: Path, excludes: set[str]) -> list[tuple[str, str]]:
        """Loads either a single Markdown file or crawls a directory recursively."""
        if not target.exists():
            raise FileNotFoundError(f"STATE-GUARD: Documentation path not found: {target}")
        if target.is_file():
            return [(str(target), target.read_text(encoding="utf-8"))]
        files = cls._crawl_directory(target, excludes)
        if not files:
            raise ValueError(f"STATE-GUARD: No Markdown files found in directory: {target}")
        return [(str(path), path.read_text(encoding="utf-8")) for path in files]

    @staticmethod
    def _crawl_directory(root: Path, excludes: set[str]) -> list[Path]:
        """Recursively collects sorted Markdown files while respecting exclusions."""
        return [
            path for path in sorted(root.rglob("*.md"))
            if path.is_file() and not any(excl in path.parts for excl in excludes)
        ]

    def _execute_session(self, session: ExampleSession) -> tuple[SessionTrace, list[DocDiagnostic]]:
        """Runs a single session in the arena and evaluates all step outcomes."""
        payload = [
            {"code": s.code, "line": s.line, "expected_raises": s.expected_raises}
            for s in session.steps
        ]
        raw_outcomes = self._invoke_arena(payload)
        return self._evaluate_outcomes(session, raw_outcomes)

    def _invoke_arena(self, payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Dispatches the session payload to the Arena lifecycle."""
        self.arena.setup(self.pre_state)
        try:
            return self.arena.execute(_execute_session_payload, (payload,), {})
        finally:
            self.arena.teardown()

    @staticmethod
    def _evaluate_outcomes(
        session: ExampleSession, outcomes: list[dict[str, Any]]
    ) -> tuple[SessionTrace, list[DocDiagnostic]]:
        """Compares step outcomes against expected outputs and collects diagnostics."""
        diags: list[DocDiagnostic] = []
        outputs: list[str] = []
        for step, outcome in zip(session.steps, outcomes):
            outputs.append(outcome["output"])
            diag = DocEnsurance._check_step_outcome(step, outcome, session.session_id)
            if diag is not None:
                diags.append(diag)
        return SessionTrace(session.session_id, tuple(outputs), not bool(diags)), diags

    @staticmethod
    def _check_step_outcome(
        step: ExtractedExample, outcome: dict[str, Any], session_id: str
    ) -> DocDiagnostic | None:
        """Evaluates one step outcome for runtime errors, missing exceptions, or output diffs."""
        if outcome["status"] in ("DOC-EXEC", "DOC-RAISE"):
            return DocDiagnostic(
                step.file_path, outcome["status"], step.line, outcome["error"], session_id
            )
        if step.expected_output is not None and outcome["output"] != step.expected_output:
            msg = f"Output mismatch: expected {step.expected_output!r}, got {outcome['output']!r}."
            return DocDiagnostic(step.file_path, "DOC-OUT", step.line, msg, session_id)
        return None