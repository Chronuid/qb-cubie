"""Import declarations and explicit replacement dependencies have distinct roles."""

import venv

import pytest

from qb_cubie import EBT, PickleCodec, PyVenv, WorldState


@pytest.fixture(scope="module")
def bare_environment(tmp_path_factory):
    base = tmp_path_factory.mktemp("declaration-base") / "venv"
    venv.EnvBuilder(with_pip=False).create(base)
    return base


@pytest.fixture
def declarations(tmp_path):
    source = tmp_path / "declared_checks.py"
    source.write_text(
        "import pytest\n"
        "@pytest.fixture\n"
        "def unused_fixture(): return 1\n"
        "@pytest.mark.parametrize('value', [pytest.param(1, id='one')])\n"
        "def unused_test(value): pass\n"
        "def independent(): return 7\n"
        "def reject(): pytest.fail('must fail')\n"
        "def runtime_decoration(): pytest.fixture(lambda: None)\n"
        "def lazy_import():\n"
        "    try: import pytest\n"
        "    except ImportError: return False\n"
        "    return True\n",
        encoding="utf-8",
    )
    return WorldState(fs={source.name: str(source)})


@pytest.mark.parametrize("target, expected", [("independent", 7), ("lazy_import", False)])
def test_missing_pytest_supports_declarations_without_leaking_into_runtime(
    bare_environment, declarations, target, expected,
):
    result = EBT(target=f"declared_checks:{target}",
                 arena=PyVenv(str(bare_environment), codec=PickleCodec()),
                 pre=declarations, post=WorldState(returns=expected)).run()
    assert result.evaluation is True
    assert result.traces[0].outcome.returns == expected


@pytest.mark.parametrize("target", ["reject", "runtime_decoration"])
def test_missing_pytest_helpers_reject_runtime_calls(bare_environment, declarations, target):
    case = EBT(target=f"declared_checks:{target}",
               arena=PyVenv(str(bare_environment), codec=PickleCodec()),
               pre=declarations, reporter=None)
    with pytest.raises(RuntimeError, match="PhantomObject.*pytest"):
        case.run()
    assert case.run_trace is None


@pytest.mark.parametrize("replace", [False, True], ids=["real-dependency", "explicit-phantom"])
def test_only_explicitly_selected_dependencies_are_replaced(bare_environment, tmp_path, replace):
    dependency = tmp_path / "workflow_guard.py"
    dependency.write_text("def check(): return 'real check'\n", encoding="utf-8")
    target = tmp_path / "guarded_target.py"
    target.write_text(
        "import workflow_guard\ndef run(): return workflow_guard.check()\n", encoding="utf-8",
    )
    arena = PyVenv(str(bare_environment), codec=PickleCodec(),
                   decontams=["workflow_guard"] if replace else None)
    case = EBT(target="guarded_target:run", arena=arena,
               pre=WorldState(fs={dependency.name: str(dependency), target.name: str(target)}),
               post=WorldState(returns="real check"), reporter=None)
    if replace:
        with pytest.raises(RuntimeError, match="PhantomObject.*workflow_guard.check"):
            case.run()
        assert case.run_trace is None
    else:
        assert case.run().evaluation is True
