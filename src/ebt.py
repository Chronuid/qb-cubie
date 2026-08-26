from typing import Any, Union, List, Protocol, runtime_checkable
from dataclasses import dataclass


# ========== PROTOCOLS & DATACLASSES ===================================================================================

@runtime_checkable
class Arena(Protocol):
    """
    Vertrag für isolierte Ausführungsumgebungen.
    """
    def setup(self) -> None:
        """Bereitet die Umgebung für die Ausführung vor und isoliert das ursprüngliche Environment über ein Duplikat."""
        ...
    def execute(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Führt das Target innerhalb der isolierten Umgebung aus."""
        ...
    def teardown(self) -> None:
        """Zerstört die Umgebung und bereinigt alle temporären Zustände."""
        ...


@dataclass
class WorldState:
    """
    Deklariert Ausführungsumgebungen, Dateisystem-Zustände und funktionale Parameter einer Test-Welt.
    """
    arena: Any = None
    args: Any = None
    kwargs: Any = None
    returns: Any = None
    fs: Any = None


# ========== EXAMPLE-BASED-TESTING =====================================================================================

class EBT:
    """
    Orchestriert beispielbasierte Testläufe (Example-Based-Testing) nach dem formalen Hoare-Tripel (`{P}S{Q}`).
    """
    def __init__(
            self,
            target: Any,
            arena: Any = None,
            pre: Union[WorldState, List[WorldState], None] = None,
            post: Union[WorldState, List[WorldState], None] = None,
            expect: bool = True or False
    ):
        self.target = target
        self.arena = arena
        self.pre = pre or WorldState()
        self.post = post or WorldState()
        self._actual_returns: Any = None
        self.expect = expect

    # ----- Services ---------------------------------------------------------------------------------------------------

    def run(self) -> None:
        """Führt die Test-Pipeline bestehend aus Vorbereitung, Ausführung und Auswertung aus."""
        __tracebackhide__ = True
        self._arrange()
        self._validate()
        self._report()


    # ----- Pipes ------------------------------------------------------------------------------------------------------

    def _arrange(self) -> None:
        """Validiert und normalisiert die übergebenen Zustände für die Pipeline."""
        __tracebackhide__ = True
        ...

    def _validate(self) -> None:
        """Führt das Target mit den definierten Eingabeparametern des Prä-Zustands aus."""
        __tracebackhide__ = True
        if not isinstance(self.pre, WorldState):
            raise RuntimeError("STATE-GUARD: 'pre' wurde nicht korrekt normalisiert.")
        args = self._normalize_args(self.pre.args)
        kwargs = self.pre.kwargs if self.pre.kwargs is not None else {}
        self._execute_target(args, kwargs)

    def _report(self) -> None:
        """Gleicht das tatsächliche Ergebnis mit dem erwarteten Post-Zustand ab."""
        __tracebackhide__ = True
        if not isinstance(self.post, WorldState):
            raise RuntimeError("STATE-GUARD: 'post' wurde nicht korrekt normalisiert.")
        if self.expect: assert self._actual_returns == self.post.returns
        if not self.expect: assert self._actual_returns != self.post.returns


    # ----- Utilities --------------------------------------------------------------------------------------------------

    # ↓--- _validate() ---↓

    @staticmethod
    def _normalize_args(args_raw: Any) -> tuple:
        """Normalisiert die Argumente zu einem Tuple und verhindert versehentliches String-Unpacking."""
        __tracebackhide__ = True
        if args_raw is None: return ()
        if isinstance(args_raw, (list, tuple)): return tuple(args_raw)
        return (args_raw,)

    def _execute_target(self, args: tuple, kwargs: dict) -> None:
        """Kapselt den eigentlichen Funktionsaufruf im korrekten Kontext (Arena oder In-Memory)."""
        __tracebackhide__ = True
        if isinstance(self.arena, Arena):
            self.arena.setup()
            try: self._actual_returns = self.arena.execute(self.target, args, kwargs)
            finally: self.arena.teardown()
        else: self._actual_returns = self.target(*args, **kwargs)