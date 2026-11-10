"""Keep real benchmark episodes opt-in while leaving deterministic tests offline."""

from pathlib import Path

import pytest

from qb_cubie.benchmarks.execution import _inputs
from qb_cubie.benchmarks.planning.planner import plan_suite


def pytest_addoption(parser):
    """Register explicit activation and suite configuration options."""
    group = parser.getgroup("cubie benchmarks")
    group.addoption("--run-agent-benchmarks", action="store_true", help="Enable explicitly marked agent episodes")
    group.addoption("--suite", help="Benchmark suite TOML for explicitly enabled agent episodes")


def pytest_configure(config):
    """Register benchmark markers without importing any model-provider integration."""
    for name in ("agent_benchmark", "review_agent", "developer_agent"):
        config.addinivalue_line("markers", f"{name}: explicitly controlled Cubie benchmark episode")


def pytest_collection_modifyitems(config, items):
    """Skip agent episodes unless enabled, even when a marker selector names them."""
    if not config.getoption("run_agent_benchmarks"):
        skip = pytest.mark.skip(reason="Agent benchmarks require --run-agent-benchmarks and --suite")
        for item in items:
            if item.get_closest_marker("agent_benchmark"):
                item.add_marker(skip)


def pytest_collection_finish(session):
    """Validate live configuration after deselection and only for actual enabled execution."""
    config = session.config
    selected = any(item.get_closest_marker("agent_benchmark") for item in session.items)
    if not selected or config.option.collectonly or not config.getoption("run_agent_benchmarks"):
        return
    suite = config.getoption("suite")
    if not suite:
        raise pytest.UsageError("Agent benchmarks require --suite")
    try:
        path = Path(suite).resolve()
        _inputs.prepare(path, plan_suite(path))
    except (ValueError, OSError) as error:
        raise pytest.UsageError(f"Agent benchmark suite: {error}") from error


@pytest.fixture(scope="session")
def agent_benchmark_result(pytestconfig):
    """Execute a selected suite once for enabled review and developer acceptance tests."""
    if not pytestconfig.getoption("run_agent_benchmarks"):
        pytest.skip("Agent benchmarks require --run-agent-benchmarks and --suite")
    from qb_cubie.benchmarks.runner import run_suite
    return run_suite(pytestconfig.getoption("suite"))
