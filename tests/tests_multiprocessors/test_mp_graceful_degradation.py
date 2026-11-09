from src.qb_cubie.ebt import *
import pytest
from typing import Callable, Iterable, Any
class MockTriggeredSignal(BaseException): pass

class GracefulMockProcessor:
    """Ein vollausgestatteter Mock für FSM- und Routing-Tests."""
    def __init__(self, mock_id: str, priority: int, triggers: bool = True, crash_at: str = None):
        self.mock_id = mock_id
        self.priority = priority
        self.triggers = triggers  # Steuert die check_condition
        self.crash_at = crash_at  # "SETUP", "EXECUTE" oder None

    def check_condition(self, pre_states: list, post_states: list) -> bool:
        return self.triggers

    def create_handler(self, n_tasks: int):
        if self.crash_at == "SETUP": raise ValueError(f"CRASH_SETUP_{self.mock_id}")
        class GracefulMapper:
            def __init__(self, spy_id: str, crash: str):
                self.spy_id = spy_id
                self.crash = crash
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): pass
            def map(self, fn: Callable, *iterables: Iterable, chunksize: int = 1) -> Iterable[Any]:
                if self.crash == "EXECUTE": raise RuntimeError(f"CRASH_EXECUTE_{self.spy_id}")
                raise MockTriggeredSignal(f"WINNER:{self.spy_id}")
        return GracefulMapper(self.mock_id, self.crash_at)


DEGRADATION_SCENARIOS = [
    (
        # Szenario A: Der Favorit crasht im SETUP, Fallback springt ein
        [
            GracefulMockProcessor("FALLBACK", priority=10, crash_at=None),
            GracefulMockProcessor("FAVORITE", priority=99, crash_at="SETUP")
        ],
        "WINNER:FALLBACK", # Erwartetes Ergebnis
        1                  # Erwartete Anzahl an Warnings
    ),
    (
        # Szenario B: Der Favorit crasht erst beim EXECUTE, Fallback springt ein
        [
            GracefulMockProcessor("FALLBACK", priority=10, crash_at=None),
            GracefulMockProcessor("FAVORITE", priority=99, crash_at="EXECUTE")
        ],
        "WINNER:FALLBACK",
        1
    ),
    (
        # Szenario C: Domino-Effekt. Proc1 (SETUP-Crash) -> Proc2 (EXECUTE-Crash) -> Proc3 (Win)
        [
            GracefulMockProcessor("HERO", priority=1, crash_at=None),
            GracefulMockProcessor("CLUMSY", priority=50, crash_at="EXECUTE"),
            GracefulMockProcessor("GLASS", priority=99, crash_at="SETUP")
        ],
        "WINNER:HERO",
        2 # Wir erwarten zwei Degradation-Warnings!
    ),
    (
        # Szenario D: Totalausfall (EXHAUSTED).
        [
            GracefulMockProcessor("FAIL_1", priority=10, crash_at="SETUP"),
            GracefulMockProcessor("FAIL_2", priority=99, crash_at="EXECUTE")
        ],
        "STATE-GUARD: All Processors failed",  # <-- HIER ANPASSEN
        2
    ),
    (
        # Szenario E: Das Registry-Chaos (Der ultimative FSM-Stresstest)
        # Die FSM sortiert zuerst nach Priorität.
        [
            # Prio 100: Fliegt sofort raus, weil check_condition False ist (Kein Crash, kein Warning!)
            GracefulMockProcessor("WRONG_TYPE", priority=100, triggers=False, crash_at=None),
            # Prio 90: Wird probiert, stürzt aber im EXECUTE ab -> Degradation + 1 Warning
            GracefulMockProcessor("KAMIKAZE_1", priority=90, triggers=True, crash_at="EXECUTE"),
            # Prio 80: Wird probiert, stürzt schon im SETUP ab -> Degradation + 1 Warning
            GracefulMockProcessor("KAMIKAZE_2", priority=80, triggers=True, crash_at="SETUP"),
            # Prio 70: Fliegt raus (check_condition False)
            GracefulMockProcessor("IGNORED", priority=70, triggers=False, crash_at=None),
            # Prio 10: Der Retter in der Not! Läuft sauber durch.
            GracefulMockProcessor("THE_SAVIOR", priority=10, triggers=True, crash_at=None),
            # Prio 5: Wird gar nicht erst erreicht, weil Prio 10 schon gewinnt.
            GracefulMockProcessor("TOO_LATE", priority=5, triggers=True, crash_at="EXECUTE")
        ],
        "WINNER:THE_SAVIOR",  # Erwartetes Ergebnis
        2  # Erwartete Warnings (nur Kamikaze 1 und 2)
    )
]


@pytest.mark.parametrize("processor_setup, expected_outcome, expected_warnings", DEGRADATION_SCENARIOS)
def test_fsm_graceful_degradation(processor_setup, expected_outcome, expected_warnings, recwarn):
    """
    Validiert die Finite-State-Machine und EAFP-Strategie des MultiprocessManagers.
    Beweist, dass abstürzende Prozessoren isoliert, degradiert (Prio=0) und per Fallback
    ersetzt werden, bis entweder ein Sieg errungen oder die Registry erschöpft ist.
    """

    # 1. Init (Wir nutzen target_state_mutator als Dummy)
    engine = EBT(
        target=lambda x: x,
        arena=None,
        pre=[WorldState(args=("TEST",))],
        post=[WorldState(returns=Any)],
        multiprocessing=True
    )

    # Die weiße Weste: Wir zwingen die Engine exklusiv auf unsere Kamikaze-Mocks
    engine.MULTIPROCESSORS = processor_setup

    # 2. Ausführung & Assertion
    if "WINNER" in expected_outcome:
        # Erfolgs-Szenarien: Einer der Mocks muss am Ende den Sieg herausschreien
        with pytest.raises(MockTriggeredSignal, match=expected_outcome):
            engine.run()
    else:
        # Totalausfall-Szenario: Die FSM sprengt sich kontrolliert selbst
        with pytest.raises(RuntimeError, match=expected_outcome):
            engine.run()

    # 3. Die FSM-Zustands-Assertions (Der eigentliche Beweis der Degradation)

    # A) Wurden die Warnings exakt in der richtigen Anzahl geworfen?
    assert len(recwarn) == expected_warnings

    # B) Wurde die Priorität der abgestürzten Prozessoren wirklich mutiert (auf 0 gesetzt)?
    for proc in processor_setup:
        # 1. Ignorierte oder nicht erreichte Prozessoren MÜSSEN ihre Prio behalten
        if not proc.triggers or proc.mock_id == "TOO_LATE":
            assert proc.priority > 0, f"Prozessor {proc.mock_id} durfte nicht degradiert werden!"

        # 2. Prozessoren, die physisch gecrasht sind, MÜSSEN Prio 0 haben
        elif proc.crash_at is not None:
            assert proc.priority == 0, f"Prozessor {proc.mock_id} wurde nicht korrekt degradiert!"