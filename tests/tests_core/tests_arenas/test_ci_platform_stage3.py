"""Frozen Red-Phase contracts for CI-Matrix Stage 3 (run 44735125009 / 98bf4247).

These contracts intentionally have no xfail markers: they freeze the confirmed
cross-platform failures observed on macos-15 and windows-2022 before Green-Phase edits.
"""

import importlib
import importlib.metadata
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from qb_cubie.core.arenas._relocation import relocate_scripts

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BENCHMARKS_SRC = PROJECT_ROOT / "experiments" / "benchmarks"
BENCHMARKS_DATA = BENCHMARKS_SRC / "cubie_benchmarks" / "data"


# ========== C1: MULTI-PLATFORM MYPY CONTRACT (macos-15 & win32) ======================================================


@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
def test_src_mypy_passes_for_all_ci_platforms(platform: str) -> None:
    """Verify strict mypy with --warn-unreachable passes for Linux, macOS, and Windows."""
    result = subprocess.run(
        [
            sys.executable, "-m", "mypy",
            "--warn-unreachable", "--check-untyped-defs",
            "--platform", platform,
            str(PROJECT_ROOT / "src"),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, f"mypy --platform {platform} failed:\n{result.stdout}\n{result.stderr}"


# ========== C2: WINDOWS TEXT-SHEBANG & CRLF RELOCATION CONTRACT ======================================================


@pytest.mark.parametrize("interpreter", ["python.exe", "pythonw.exe"])
@pytest.mark.parametrize("line_ending", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_relocation_rewrites_windows_python_exe_text_shebangs(
    tmp_path: Path, interpreter: str, line_ending: bytes,
) -> None:
    """Verify Scripts/<tool> shebangs targeting python.exe/pythonw.exe (e.g. dill) relocate cleanly."""
    base = tmp_path / "base_env"
    clone = tmp_path / "clone_env"
    (base / "Scripts").mkdir(parents=True)
    (clone / "Scripts").mkdir(parents=True)

    script = clone / "Scripts" / "get_gprof"
    original_shebang = f"#!{base}\\Scripts\\{interpreter}".encode("utf-8")
    script.write_bytes(original_shebang + line_ending + b"print('ok')" + line_ending)

    relocate_scripts(base, clone)

    rewritten = script.read_bytes()
    assert str(base).encode("utf-8") not in rewritten
    assert str(clone).encode("utf-8") in rewritten


def test_relocation_rewrites_crlf_shell_trampoline(tmp_path: Path) -> None:
    """Verify CRLF shell trampolines written on Windows relocate without rejecting the header."""
    base = tmp_path / "base_env"
    clone = tmp_path / "clone_env"
    (base / "bin").mkdir(parents=True)
    (clone / "bin").mkdir(parents=True)

    script = clone / "bin" / "tool"
    script.write_bytes(
        f"#!/bin/sh\r\n'''exec' '{base}/bin/python' \"$0\" \"$@\"\r\n' '''\r\nprint('ok')\r\n".encode("utf-8")
    )

    relocate_scripts(base, clone)

    rewritten = script.read_bytes()
    assert str(base).encode("utf-8") not in rewritten
    assert str(clone).encode("utf-8") in rewritten


def test_relocation_rejects_non_executable_unsupported_shebang_script(tmp_path: Path) -> None:
    """Verify extensionless unsupported shebang scripts are rejected even without POSIX +x bits."""
    base = tmp_path / "base_env"
    clone = tmp_path / "clone_env"
    (base / "Scripts").mkdir(parents=True)
    (clone / "Scripts").mkdir(parents=True)

    script = clone / "Scripts" / "custom-shell"
    script.write_bytes(f"#!/bin/sh\nexec '{base}/Scripts/helper'\n".encode("utf-8"))
    script.chmod(0o644)

    with pytest.raises(RuntimeError, match="Unsupported console entry point"):
        relocate_scripts(base, clone)


# ========== C3: BENCHMARK LF-BYTE INVARIANCE & WINDOWS FILE URL CONTRACT =============================================


def test_smoke_benchmark_solution_matches_acceptance_under_crlf_default_write_text(
    tmp_path: Path, monkeypatch,
) -> None:
    """Verify index-initial solution passes byte-exact acceptance when default write_text emits CRLF."""
    scenario = BENCHMARKS_DATA / "smoke" / "scenarios" / "index-initial"
    solution_src = (scenario / "evaluator" / "solution.py.txt").read_text(encoding="utf-8")
    acceptance_src = (scenario / "evaluator" / "acceptance.py.txt").read_text(encoding="utf-8")

    original_write_text = Path.write_text

    def windows_default_write_text(self, data, encoding=None, errors=None, newline=None):
        return original_write_text(
            self, data, encoding=encoding, errors=errors,
            newline="\r\n" if newline is None else newline,
        )

    monkeypatch.setattr(Path, "write_text", windows_default_write_text)

    work = tmp_path / "work"
    work.mkdir()
    (work / "index_tool.py").write_bytes(solution_src.encode("utf-8"))
    (work / "acceptance.py").write_bytes(acceptance_src.encode("utf-8"))

    sol_ns: dict[str, object] = {}
    exec(compile(solution_src, str(work / "index_tool.py"), "exec"), sol_ns)
    src_dir = tmp_path / "inputs"
    out_dir = tmp_path / "outputs"
    src_dir.mkdir()
    (src_dir / "b.txt").write_bytes(b"beta\n")
    (src_dir / "a.txt").write_bytes(b"alpha\n")

    sol_ns["build_index"](src_dir, out_dir)
    assert (out_dir / "index.txt").read_bytes() == b"a.txt\nb.txt\n"


def test_benchmark_templates_use_explicit_lf_newline_when_writing_text() -> None:
    """Verify all smoke and base scenario templates pass explicit newline= to write_text."""
    offenders: list[str] = []
    call_pattern = re.compile(r"\.write_text\(([^)]*)\)")
    for suite in ("smoke", "base"):
        suite_dir = BENCHMARKS_DATA / suite / "scenarios"
        for template in sorted(suite_dir.rglob("*.py.txt")):
            content = template.read_text(encoding="utf-8")
            for match in call_pattern.finditer(content):
                if "newline=" not in match.group(1):
                    offenders.append(template.relative_to(BENCHMARKS_DATA).as_posix())
                    break
    assert offenders == [], f"Templates missing explicit newline= in write_text(): {offenders}"


def test_benchmark_wheel_hash_uses_url2pathname_for_windows_file_urls(tmp_path: Path, monkeypatch) -> None:
    """Verify cubie_benchmarks wheel_hash resolves file:// URLs through url2pathname."""
    if str(BENCHMARKS_SRC) not in sys.path:
        sys.path.insert(0, str(BENCHMARKS_SRC))
    files_mod = importlib.import_module("cubie_benchmarks.reporting._files")

    wheel = tmp_path / "qb_cubie-0.0.10-py3-none-any.whl"
    wheel.write_bytes(b"fake-wheel-archive")

    class _FakeDist:
        def read_text(self, name: str) -> str | None:
            if name == "direct_url.json":
                return json.dumps({"url": "file:///D:/a/qb-cubie/dist/qb_cubie-0.0.10-py3-none-any.whl"})
            return None

    monkeypatch.setattr(importlib.metadata, "distribution", lambda _name: _FakeDist())
    monkeypatch.setattr(files_mod, "url2pathname", lambda _path: str(wheel))

    assert files_mod.wheel_hash() == files_mod.digest(wheel)
