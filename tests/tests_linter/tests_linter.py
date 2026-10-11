from pathlib import Path
from cubie import EBT, WorldState, TempFS, PyVenv
from cubie.linter import AstLinter, Pylint, LinterDiagnostic
from cubie import CloudpickleCodec


def test_linter_aggregation():
    linter = AstLinter(Pylint())
    EBT(
        arena=TempFS(),
        target=linter.check,
        pre=WorldState(fs={"bad_code.py": "tests/fixtures/bad_code.py"}),
        post=WorldState(
            returns=lambda actual: len(actual) > 0 and isinstance(actual[0], LinterDiagnostic)
        )
    ).run()


def test_linter_discovery_and_ignores():
    """Verifies: The .venv directory was successfully excluded."""
    linter = AstLinter(Pylint())
    EBT(
        arena=PyVenv("tests/.arenas/linter_env", codec=CloudpickleCodec()),
        target=linter.check,
        pre=WorldState(),
        post=WorldState(returns=[]),
    ).run()


def test_linter_custom_excludes():
    """Verifies: The linter checks only the defined folders, taking 'excludes' configurations into account."""
    linter = AstLinter(Pylint(excludes=["custom_dir"]))
    EBT(
        arena=PyVenv(codec=CloudpickleCodec()),
        target=linter.check,
        pre=WorldState(
            args=(Path("src")),
            fs={
                ".": "tests/fixtures/bad_code.py",
                "src/custom_dir/bad_code.py": "tests/fixtures/bad_code.py",
            },
        ),
        post=WorldState(returns=[])
    ).run()


def test_linter_checks_in_memory():
    """Verifies: The AstLinter can accept code directly."""
    linter = AstLinter(Pylint())
    bad_code_string = "import sys\ndef foo():\n    pass\n"
    EBT(
        target=linter.check,
        pre=WorldState(args=(bad_code_string,)),
        post=WorldState(returns=lambda diag: len(diag) > 0 and isinstance(diag[0], LinterDiagnostic))
    ).run()