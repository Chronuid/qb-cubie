"""Phase 10.2 acceptance fixtures; no runner substitute or model calls."""

import re
import tomllib

import pytest

from ..contracts import accepted


def initialize_smoke(public_api, path):
    accepted(public_api("init_smoke_suite"), path, expected=lambda value: (
        value["suite"] == str(path.resolve()) and path.is_file()))


@pytest.fixture
def smoke_suite(tmp_path):
    return tmp_path / "external project" / "sets" / "smoke.toml"


@pytest.fixture
def execute(public_api, smoke_suite):
    def run(behavior="reference", benchmark=None, mutant=None):
        runner = public_api("run_suite")
        if not smoke_suite.exists():
            initialize_smoke(public_api, smoke_suite)
        configure_fake(smoke_suite, behavior, benchmark, mutant)
        return accepted(runner, smoke_suite, expected=lambda value: (
            value["schema_version"] == 1 and bool(value["runs"])))

    return run


def configure_fake(suite, behavior, benchmark=None, mutant=None):
    data = tomllib.loads(suite.read_text(encoding="utf-8"))
    agent = (suite.parent / data["agents"][0]).resolve()
    text = agent.read_text(encoding="utf-8").split("\n[fake]")[0]
    text += f'\n[fake]\nbehavior = "{behavior}"\n'
    if mutant:
        text += f'mutant = "{mutant}"\n'
    agent.write_text(text, encoding="utf-8")
    if behavior == "hang":
        text, count = re.subn(r"(?m)^wall_time_seconds\s*=.*$", "wall_time_seconds = 0.25",
                             suite.read_text(encoding="utf-8"))
        assert count == 1, "Smoke template needs an explicit wall_time_seconds budget"
        suite.write_text(text, encoding="utf-8")
    if benchmark:
        with suite.open("a", encoding="utf-8") as stream:
            stream.write(f'\n[select]\nbenchmarks = ["{benchmark}"]\n')
