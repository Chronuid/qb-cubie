import pytest
from typing import Any
from src.cubie.ebt import EBT
from src.cubie.protocols import WorldState
from src.cubie.arenas.tempfs import TempFS
from src.cubie.arenas.pyvenv import PyVenv


# ======================================================================================================================
# FIXTURES & TARGETS (Host-Side)
# ======================================================================================================================

# We parameterize the three execution environments to run each callable through all sandboxes.
# None (host memory), TempFS (host CWD shift), PyVenv (IPC subprocess)
@pytest.fixture(
    params=[
        None,
        TempFS(),
        PyVenv()
    ],
    ids=["No_Arena", "TempFS", "PyVenv"]
)
def arena(request) -> Any: return request.param


# --- Targets ---

def target_toplevel(val: str) -> str:
    """Baseline: A regular function at the module level."""
    return f"toplevel_{val}"


class TargetClass:
    """Encapsulates bound methods for iterative __qualname__ resolution."""
    @staticmethod
    def target_static(val: str) -> str: return f"static_{val}"
    @classmethod
    def target_class(cls, val: str) -> str: return f"class_{cls.__name__}_{val}"


class OuterClass:
    class InnerClass:
        @staticmethod
        def target_nested(val: str) -> str: return f"nested_{val}"


class RehydrationTarget:
    """A stateful object for testing instance rehydration via IPC."""
    def __init__(self, state_val: int): self.state_val = state_val
    def target_instance(self, multiplier: int) -> int: return self.state_val * multiplier


# ======================================================================================================================
# GROUP A.1: ENCAPSULATION MATRIX (Standard & OOP)
# Tests callables that already exist on the host system.
# ======================================================================================================================

def test_import_toplevel(arena):
    """Verifies the baseline: Regular functions are cleanly serialized or executed directly."""
    EBT(
        arena=arena,
        target=target_toplevel,
        pre=WorldState(args=("test",)),
        post=WorldState(returns="toplevel_test")
    ).run()


def test_import_staticmethod(arena):
    """Verifies the resolution of a static method (ticket origin)."""
    EBT(
        arena=arena,
        target=TargetClass.target_static,
        pre=WorldState(args=("test",)),
        post=WorldState(returns="static_test")
    ).run()


def test_import_classmethod(arena):
    """Verified that class methods retain their class reference (cls)."""
    EBT(
        arena=arena,
        target=TargetClass.target_class,
        pre=WorldState(args=("test",)),
        post=WorldState(returns="class_TargetClass_test")
    ).run()


def test_import_nested_class(arena):
    """Stress test for the iterative `split('.')` on the qualified name: resolves nesting of arbitrary depth."""
    EBT(
        arena=arena,
        target=OuterClass.InnerClass.target_nested,
        pre=WorldState(args=("test",)),
        post=WorldState(returns="nested_test")
    ).run()


def test_import_rehydration_instance(arena):
    """Tests bypass instantiation and rehydration for stateful objects."""
    inst = RehydrationTarget(state_val=10)
    if isinstance(arena, PyVenv): # The .* pattern also reliably captures multiline warnings.
        with pytest.warns(UserWarning, match=".*stateless static methods or classmethods.*"):
            EBT(
                arena=arena,
                target=inst.target_instance,
                pre=WorldState(kwargs={"multiplier": 5}),
                post=WorldState(returns=50)
            ).run()
    else: # Host execution: Native object reference, no IPC serialization, no warning.
        EBT(
            arena=arena,
            target=inst.target_instance,
            pre=WorldState(kwargs={"multiplier": 5}),
            post=WorldState(returns=50)
        ).run()


# ======================================================================================================================
# GROUP A.2: THE DECONTAMINATION MATRIX (Encapsulation & Phantom Imports)
# Verifies the targeted isolation of the target from toxic (missing) import branches via `decontams`.
# ======================================================================================================================

@pytest.mark.parametrize("toxic_arena", [PyVenv("tests/.arenas/empty_venv", decontams=["heavy_data_lib"])])
def test_encapsulation_toxic_module(toxic_arena, tmp_path):
    """
    Scenario 1: Toxic module level.
    The arena does not possess `heavy_data_lib`. The import at the module level is mocked
    by `decontams` as a phantom object, thereby encapsulating and saving the functionally independent target.
    """
    host_file = tmp_path / "toxic_module.py"
    host_file.write_text("import heavy_data_lib\n\ndef run(): return 'safe'")
    EBT(
        arena=toxic_arena,
        target="toxic_module.run",
        pre=WorldState(fs={"toxic_module.py": str(host_file)}),
        post=WorldState(returns="safe")
    ).run()


@pytest.mark.parametrize("deep_arena", [PyVenv("tests/.arenas/empty_venv", decontams=["massive_framework"])])
def test_encapsulation_deep_tree(deep_arena, tmp_path):
    """
    Scenario 2: Deep-Tree Decontamination (Sub-modules).
    Verifies whether PhantomFinder correctly prunes nested branch imports (`from A.B import C`)
    when only the root module is declared in `decontams`.
    """
    host_file = tmp_path / "deep_module.py"
    host_file.write_text("from massive_framework.core.utils import complex_helper\n\ndef run(): return 'deep_safe'")
    EBT(
        arena=deep_arena,
        target="deep_module.run",
        pre=WorldState(fs={"deep_module.py": str(host_file)}),
        post=WorldState(returns="deep_safe")
    ).run()


@pytest.mark.parametrize("alias_arena", [PyVenv("tests/.arenas/empty_venv", decontams=["missing_library"])])
def test_encapsulation_import_aliasing(alias_arena, tmp_path):
    """
    Scenario 3: Import aliasing.
    Demonstrates that the hook in `sys.meta_path` resolves the architectural truth (the actual module name)
    and is not misled by syntactic sugar (`import ... as ...`).
    """
    host_file = tmp_path / "alias_module.py"
    host_file.write_text("import missing_library as ml\n\ndef run(): return 'alias_safe'")
    EBT(
        arena=alias_arena,
        target="alias_module.run",
        pre=WorldState(fs={"alias_module.py": str(host_file)}),
        post=WorldState(returns="alias_safe")
    ).run()


def test_encapsulation_boomerang_collision(tmp_path):
    """
    Scenario 4: The Boomerang Collision (State-Guard negative test).
    Demonstrates that phantom objects save only the import. If the target actively
    accesses the mocked logic at runtime, the EBT run fails—as is formally correct.
    """
    host_file = tmp_path / "boomerang_module.py"
    host_file.write_text("import blocked_lib\n\ndef run(): return blocked_lib.calculate() + 10")
    with pytest.raises(RuntimeError, match="Arena Error.*TypeError.*PhantomObject"):
        EBT(
            arena=PyVenv("tests/.arenas/empty_venv", decontams=["blocked_lib"]),
            target="boomerang_module.run",
            pre=WorldState(fs={"boomerang_module.py": str(host_file)}),
            post=WorldState(returns="irrelevant") # expect=False ist hier obsolet!
        ).run()

# ======================================================================================================================
# GROUP B: THE TOPOLOGY MATRIX (Special Callables / Late Binding)
# ======================================================================================================================

@pytest.mark.parametrize("dynamic_arena", [PyVenv("tests/.arenas/empty_venv")])
def test_import_dynamic_fs(dynamic_arena, tmp_path):
    """The target is projected into the arena only through the fs declaration."""
    host_file = tmp_path / "dynamic_module.py"
    host_file.write_text("def run(val): return f'dynamic_{val}'")
    EBT(
        arena=dynamic_arena,
        target="dynamic_module.run",
        pre=WorldState(
            kwargs={"val": "injection"},
            fs={"dynamic_module.py": str(host_file)}
        ),
        post=WorldState(returns="dynamic_injection")
    ).run()


def test_import_arena_package():
    """The target originates from a third-party library in the isolated environment."""
    EBT(
        arena=PyVenv("tests/.arenas/cowsay_env"),
        target="cowsay.get_output_string",
        pre=WorldState(args=("cow", "moo")),  # Cowsay expects positional arguments!
        post=WorldState(
            returns=lambda ret: isinstance(ret, str) and "moo" in ret
        )
    ).run()


# ======================================================================================================================
# GROUP C: THE PATH AND TOPOLOGY MATRIX (Relative & Absolute Imports)
# ======================================================================================================================

@pytest.mark.parametrize("path_arena", [PyVenv("tests/.arenas/empty_venv")])
def test_import_absolute_shadowing(path_arena, tmp_path):
    """Verifies that dynamic modules in the workspace shadow identically named host modules."""
    host_file = tmp_path / "utils.py"
    host_file.write_text("def run(): return 'arena_shadow'")
    EBT(
        arena=path_arena,
        target="utils.run",
        pre=WorldState(fs={"utils.py": str(host_file)}),
        post=WorldState(returns="arena_shadow")
    ).run()


@pytest.mark.parametrize("pkg_arena", [PyVenv("tests/.arenas/empty_venv")])
def test_import_relative_package(pkg_arena, tmp_path):
    """Builds a package graph within the workspace and tests intra-package dependencies."""
    pkg_dir = tmp_path / "my_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").touch()
    (pkg_dir / "helper.py").write_text("SECRET_KEY = 'cubie_rocks'")
    (pkg_dir / "main.py").write_text("from .helper import SECRET_KEY\n\ndef run(): return SECRET_KEY")
    EBT(
        arena=pkg_arena,
        target="my_pkg.main.run",
        pre=WorldState(fs={"my_pkg": str(pkg_dir)}),
        post=WorldState(returns="cubie_rocks")
    ).run()