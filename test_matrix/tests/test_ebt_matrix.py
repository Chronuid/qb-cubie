import pytest
from itertools import product
from typing import Iterator, Tuple, List, Union, cast
from test_matrix.protocols import MatrixConfig, Scenarios, Aspects, Overhead, MatrixReport
from arenas.pyvenv import PyVenv
from arenas.tempfs import TempFS

SCALES = [0, 1, 3]
MULTIPROCESSING = [False, True]
ARENAS = [None, TempFS(), PyVenv()]


# =================================================================================================
# 1. KERN-GENERATOREN (Reine Daten, typsicher, unabhängig von Pytest)
# =================================================================================================

def _gen_scenarios() -> Iterator[Tuple[MatrixConfig, str]]:
    for o2o, n2o, o2n, n2n in product(SCALES, SCALES, SCALES, SCALES):
        config = MatrixConfig(
            scenarios=Scenarios(one_to_one=o2o, n_to_one=n2o, one_to_n=o2n, n_to_n=n2n),
            aspects=Aspects(memory=1, filesystem=0, environment=0),
            overhead=Overhead(fs=0, arena=0),
            arena=None,
            multiprocessing=False
        )
        test_id = f"Scenarios_1:1({o2o})_N:1({n2o})_1:N({o2n})_N:N({n2n})"
        yield config, test_id


def _gen_aspects() -> Iterator[Tuple[MatrixConfig, str]]:
    for mem, fs, env in product(SCALES, SCALES, SCALES):
        valid_arenas = []
        for arena in ARENAS:
            if env > 0:
                if isinstance(arena, PyVenv): valid_arenas.append(arena)
            elif fs > 0:
                if arena is not None: valid_arenas.append(arena)
            else: valid_arenas.append(arena)

        for arena in valid_arenas:
            for mp in MULTIPROCESSING:
                config = MatrixConfig(
                    scenarios=Scenarios(one_to_one=1, n_to_one=0, one_to_n=0, n_to_n=0),
                    aspects=Aspects(memory=mem, filesystem=fs, environment=env),
                    overhead=Overhead(fs=0, arena=0),
                    arena=arena,
                    multiprocessing=mp
                )
                arena_name = type(arena).__name__ if arena else "None"
                test_id = f"Aspects_Mem({mem})_FS({fs})_Env({env})_Arena({arena_name})_MP({mp})"
                yield config, test_id


def _gen_overheads() -> Iterator[Tuple[MatrixConfig, str]]:
    for fs_noise, arena_noise in product(SCALES, SCALES):
        config = MatrixConfig(
            scenarios=Scenarios(one_to_one=1, n_to_one=0, one_to_n=0, n_to_n=0),
            aspects=Aspects(memory=1, filesystem=1, environment=0),
            overhead=Overhead(fs=fs_noise, arena=arena_noise),
            arena=TempFS(),
            multiprocessing=False
        )
        test_id = f"Overhead_FS({fs_noise})_Arena({arena_noise})"
        yield config, test_id


# =================================================================================================
# 2. PYTEST WRAPPER (Verpacken die Tuple für parametrize)
# =================================================================================================

def generate_scenario_matrix():
    for config, test_id in _gen_scenarios(): yield pytest.param(config, id=test_id)

def generate_aspect_matrix():
    for config, test_id in _gen_aspects(): yield pytest.param(config, id=test_id)

def generate_overhead_matrix():
    for config, test_id in _gen_overheads(): yield pytest.param(config, id=test_id)


# =================================================================================================
# 3. FULL MATRIX GENERATOR (Konsumiert die typsicheren Kern-Generatoren)
# =================================================================================================

def generate_full_matrix():
    for scen_cfg, scen_id in _gen_scenarios():
        for asp_cfg, asp_id in _gen_aspects():
            for over_cfg, over_id in _gen_overheads():
                if over_cfg.overhead.arena > 0 and not isinstance(asp_cfg.arena, PyVenv): continue
                combined_config = MatrixConfig(
                    scenarios=scen_cfg.scenarios,
                    aspects=asp_cfg.aspects,
                    overhead=over_cfg.overhead,
                    arena=asp_cfg.arena,
                    multiprocessing=asp_cfg.multiprocessing
                )
                test_id = f"FULL_{scen_id} | {asp_id} | {over_id}"
                yield pytest.param(combined_config, id=test_id)


# ======================================================================================================================

from test_matrix.ebt_matrix import EBTMatrix, MatrixConfig
from test_matrix.one_to_one import One2One_Mock
from test_matrix.one_to_n import One2N_Mock
from test_matrix.n_to_one import N2One_Mock
from test_matrix.n_to_n import N2N_Mock


class MockMatrixReporter:
    """Ein lautloser Reporter, der DTOs für die Test-Assertions vorhält[cite: 1]."""

    def __init__(self):
        self.reports: List[MatrixReport] = []

    def report(self, reports: Union[List[MatrixReport], MatrixReport]) -> None:
        if isinstance(reports, list):
            self.reports.extend(reports)
        else:
            self.reports.append(reports)


@pytest.fixture
def matrix_deps():
    """Stellt die Abhängigkeiten via Dependency Injection bereit."""
    return {
        "reporter": MockMatrixReporter(),
        "_one_to_one": One2One_Mock(),
        "_one_to_n": One2N_Mock(),
        "_n_to_one": N2One_Mock(),
        "_n_to_n": N2N_Mock()
    }


# =========================================================================
# TEST SUITES
# =========================================================================

@pytest.mark.parametrize("config", generate_scenario_matrix())
def test_scenario_routing_and_quantors(config: MatrixConfig, matrix_deps):
    """Prüft, ob die Quantoren-Mocks ohne Absturz in Cubie ausgeführt werden."""

    matrix = EBTMatrix(configs=config, **matrix_deps)
    matrix.run()

    reporter = cast(MockMatrixReporter, matrix_deps["reporter"])

    # Assertion 1: Wenn wir 1:1, 1:N und N:1 in der Config > 0 haben,
    # müssen genau so viele MatrixReports generiert werden.
    expected_reports = sum([
        1 if config.scenarios.one_to_one > 0 else 0,
        1 if config.scenarios.one_to_n > 0 else 0,
        1 if config.scenarios.n_to_one > 0 else 0,
        1 if config.scenarios.n_to_n > 0 else 0
    ])

    # Sonderfall: Wenn alle Scenarios 0 sind (was durch unsere product-Schleife passiert),
    # feuert kein Target.
    if expected_reports == 0:
        assert len(reporter.reports) == 0
        return

    assert len(reporter.reports) == expected_reports

    # Assertion 2: Die Cubie Engine MUSS alle Mock-Durchläufe als erfolgreich validieren.
    for report in reporter.reports:
        # trace.evaluation ist True, wenn {P}S{Q} für alle Quantoren aufgegangen ist[cite: 7, 8]
        assert report.trace.evaluation is True, f"Mock-Evaluation für {report.target_type} fehlgeschlagen!"


@pytest.mark.parametrize("config", generate_aspect_matrix())
def test_aspects_and_arena_provisioning(config: MatrixConfig, matrix_deps):
    """
    Prüft, ob die Cubie Engine die Arenen und Dateisystem-Mocks sauber aufbaut,
    ohne sich an Umgebungs-Mutationen zu verschlucken.
    """
    matrix = EBTMatrix(configs=config, **matrix_deps)
    matrix.run()
    reporter = cast(MockMatrixReporter, matrix_deps["reporter"])
    report = reporter.reports[0]  # Aspects frieren Scenarios auf One2One=1 ein
    assert report.trace.evaluation is True
    # Optional: Wir können hier auch prüfen, ob Multiprocessing korrekt weitergereicht wurde
    assert report.config.multiprocessing == config.multiprocessing