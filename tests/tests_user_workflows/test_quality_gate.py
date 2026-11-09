"""An offline CI gate must distinguish diagnostics from tool failure."""

import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from cubie import EBT, MyPy, WorldState


@pytest.mark.parametrize("faulty", [False, True], ids=["clean-module", "type-error"])
def test_real_type_check_gate(tmp_path, check_case, faulty):
    source = tmp_path / "pricing.py"
    source.write_text(
        'def price() -> int:\n    return "free"\n' if faulty
        else 'def price() -> int:\n    return 250\n', encoding="utf-8",
    )
    config = tmp_path / "mypy.ini"
    config.write_text("[mypy]\n", encoding="utf-8")
    command = [sys.executable, "-m", "mypy", "--config-file", str(config),
               "--cache-dir", str(tmp_path / "cache"), "--no-incremental"]
    # Real CLI exit status supplies an oracle outside Cubie's parser.
    process = subprocess.run([*command, str(source)], check=False, capture_output=True, text=True, timeout=30)
    assert process.returncode == (1 if faulty else 0), process.stdout + process.stderr
    if faulty:
        assert "[return-value]" in process.stdout
    case = EBT(target=MyPy(executable=command).check,
               pre=WorldState(args=(source,)), post=WorldState(returns=[]))
    result, message = check_case(case, accepted=not faulty)
    diagnostics = result.traces[0].outcome.returns
    if faulty:
        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "return-value"
        assert Path(diagnostics[0].file_path) == source
        assert diagnostics[0].line == 2
        if message:
            assert "Expected [] | Actual" in message
    else:
        assert diagnostics == []


@pytest.mark.parametrize("exit_kind", ["exit-2", "exit-127", "sigkill"])
def test_silent_tool_crash_never_becomes_a_clean_gate(tmp_path, exit_kind):
    if exit_kind == "sigkill" and os.name != "posix":
        pytest.skip("POSIX signal termination is tested on POSIX only")
    marker = tmp_path / "tool-started"
    script = tmp_path / "broken_checker.py"
    action = ("os.kill(os.getpid(), signal.SIGKILL)" if exit_kind == "sigkill"
              else f"raise SystemExit({exit_kind.split('-')[1]})")
    script.write_text(
        "import os, signal, sys\nfrom pathlib import Path\n"
        "Path(sys.argv[1]).write_text('started', encoding='utf-8')\n" + action + "\n",
        encoding="utf-8",
    )
    command = [sys.executable, str(script), str(marker)]
    # The fake executable is a consumer-controlled fault injector; it really runs.
    process = subprocess.run(command, check=False, capture_output=True, text=True, timeout=10)
    expected_code = -signal.SIGKILL if exit_kind == "sigkill" else int(exit_kind.split('-')[1])
    assert process.returncode == expected_code
    assert process.stdout == process.stderr == ""
    marker.unlink()
    case = EBT(target=MyPy(executable=command).check,
               pre=WorldState(args=("value: int = 1",)), post=WorldState(returns=[]))
    with pytest.raises(RuntimeError, match=f"exit code {expected_code}") as error:
        case.run()
    assert marker.read_text(encoding="utf-8") == "started"
    assert str(script) in str(error.value)
    assert case.run_trace is None
