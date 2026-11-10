"""External files and real CLI calls, without a substitute planner or runner."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "phase3"
CAPABILITIES = ["review_output", "workspace_changes", "phased_submission", "cancel", "wall_time", "tool_calls"]


def configure_agent(root, mode="reference", identifier="own-agent", capabilities=None):
    agent = root / "agents" / "current.toml"
    command = [sys.executable, "-I", "jsonl_agent.py", mode, identifier]
    agent.write_text('schema_version = 1\ntransport = "jsonl-v1"\ncwd = "."\n'
                     f'id = {json.dumps(identifier)}\ncommand = {json.dumps(command)}\n'
                     f'capabilities = {json.dumps(CAPABILITIES if capabilities is None else capabilities)}\n', encoding="utf-8")
    return agent


def write_suite(root, selection='', sources=None, seconds=10, repetitions=1):
    suite = root / "sets" / "team.toml"
    suite.parent.mkdir(exist_ok=True)
    suite.write_text('schema_version = 1\nname = "team-smoke"\nprofile = "agent-evaluation"\n'
                     f'repetitions = {repetitions}\nagents = ["../agents/current.toml"]\noutput = "../results"\n'
                     + ''.join(f'\n[[sources]]\npath = {json.dumps(p)}\n' for p in (sources or [".."]))
                     + f'\n[budgets]\nwall_time_seconds = {seconds}\ntool_calls = 20\n'
                     + '\n[limits]\nmax_runs = 20\nmax_total_wall_time_seconds = 200\n'
                     + ('\n[select]\n' + selection + '\n' if selection else ''), encoding="utf-8")
    return suite


@pytest.fixture
def external(tmp_path):
    root = tmp_path / "external project with spaces"
    shutil.copytree(FIXTURES, root)
    source = root / "agents" / "jsonl_agent.py.txt"
    source.rename(source.with_suffix(""))
    configure_agent(root)
    write_suite(root)
    return root


def cli(*args, cwd):
    source = str(ROOT / "src")
    code = ('import sys; sys.path.insert(0, sys.argv.pop(1)); '
            'from qb_cubie.benchmarks.cli import main; raise SystemExit(main())')
    return subprocess.run([sys.executable, "-I", "-c", code, source, *map(str, args)],
                          cwd=cwd, capture_output=True, text=True, timeout=25, check=False)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def traffic(root):
    path = root / "agents" / "traffic.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
