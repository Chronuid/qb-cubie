# test_ebt_ipc_contract.py
import pytest
from pathlib import Path
from typing import Any

import cubie
# Cubie Imports (Pfade ggf. anpassen)
from cubie import EBT
from cubie.protocols import WorldState
from cubie import PyVenv


# ===== DUMMY TARGETS ==================================================================================================

def pure_function(a: int, b: int) -> int:
    return a + b


def is_native_path(value) -> bool:
    # Import inside the arena so a copied module cannot mask a type mismatch.
    from pathlib import Path
    return isinstance(value, Path) and type(value) is type(Path("project"))


class LinterProfile:
    def __init__(self):
        self.rules = [lambda node: node is not None]


class AstLinter:
    def __init__(self, use_complex_state: bool = False):
        self.runs = 0
        self.name = "default_linter"
        if use_complex_state:
            self.profile = LinterProfile()

    def check(self, code: str) -> bool:
        self.runs += 1
        return True

    @classmethod
    def factory(cls) -> 'AstLinter':
        return cls()

    @staticmethod
    def is_valid(code: str) -> bool:
        return len(code) > 0


# ===== IPC CODEC CONTRACT SUITE =======================================================================================

class TestIPCCodecContract:
    """
    Definiert die Anforderungen an die IPC-Serialisierung der PyVenv-Arena.
    Ein vollständig implementierter Codec muss alle folgenden EBT-Aufrufe erfolgreich
    über die Prozessgrenze transportieren und ausführen können.
    """

    @pytest.fixture
    def arena(self) -> PyVenv:
        return PyVenv(codec=cubie.CloudpickleCodec())

    def test_pure_function_serialization(self, arena: PyVenv):
        """Ein Codec muss reine Funktionen übertragen können."""
        EBT(
            arena=arena,
            target=pure_function,
            pre=WorldState(args=(1, 2)),
            post=WorldState(returns=3)
        ).run()

    @pytest.mark.parametrize("argument_kind", ["args", "kwargs"])
    def test_path_keeps_native_type(self, arena: PyVenv, argument_kind: str):
        """Path arguments must retain the arena's native pathlib class identity."""
        path = Path("project")
        pre = WorldState(args=(path,)) if argument_kind == "args" else WorldState(kwargs={"value": path})
        EBT(
            arena=arena,
            target=is_native_path,
            pre=pre,
            post=WorldState(returns=True)
        ).run()

    def test_static_and_class_method_serialization(self, arena: PyVenv):
        """Ein Codec muss ungebundene Klassenmethoden übertragen können."""
        EBT(
            arena=arena,
            target=AstLinter.is_valid,
            pre=WorldState(args=("code",)),
            post=WorldState(returns=True)
        ).run()

    def test_bound_method_with_simple_state(self, arena: PyVenv):
        """Ein Codec muss gebundene Methoden einer Instanz (mit primitiven Zuständen) rehydrieren können."""
        linter = AstLinter(use_complex_state=False)

        EBT(
            arena=arena,
            target=linter.check,
            pre=WorldState(args=("x = 1",)),
            post=WorldState(returns=True)
        ).run()

    def test_bound_method_with_complex_object_state(self, arena: PyVenv):
        """Ein Codec muss gebundene Methoden rehydrieren können, deren Instanzen komplexe Sub-Objekte enthalten."""
        linter = AstLinter(use_complex_state=True)

        EBT(
            arena=arena,
            target=linter.check,
            pre=WorldState(args=("x = 1",)),
            post=WorldState(returns=True)
        ).run()

    def test_bound_method_with_functional_state(self, arena: PyVenv):
        """Ein Codec muss gebundene Methoden rehydrieren können, die rohe Callables (Lambdas) im __dict__ halten."""
        linter = AstLinter(use_complex_state=False)
        linter.dynamic_rule = lambda node: node is not None

        EBT(
            arena=arena,
            target=linter.check,
            pre=WorldState(args=("x = 1",)),
            post=WorldState(returns=True)
        ).run()

    def test_dynamic_predicates_in_kwargs(self, arena: PyVenv):
        """
        Ein Codec muss Callables innerhalb des Test-Payloads (z. B. in Args/Kwargs) serialisieren können,
        da EBT dynamische Prädikate zur Laufzeit unterstützt.
        """
        predicate = lambda actual: actual == 3

        EBT(
            arena=arena,
            target=pure_function,
            pre=WorldState(args=(1, 2)),
            post=WorldState(returns=predicate)
        ).run()
