"""Verifikation der expliziten Quantoren-Deklaration ('all' / 'exists') in EBT.

Die gewünschten Verträge stehen im Sinne von Cubie-TGD bewusst ohne xfail-Marker.
"""

from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from typing import Any

import pytest

from qb_cubie import EBT, WorldState
from qb_cubie.protocols import ExceptionExpectation
from qb_cubie.reporter import JsonReporter

# ========== DUMMY TARGETS =========================================================================


def target_normalize(raw: str) -> str:
    """Deterministische Beispiel-Funktion für String-Normalisierung."""
    return raw.strip().lower()


def target_flaky_route(route: str) -> str:
    """Simuliert deterministisch erfolgreiche und fehlschlagende Routen."""
    return "ok" if route == "/health" else "error"


def target_identity(value: Any) -> Any:
    """Gibt den übergebenen Wert unverändert zurück."""
    return value


def target_raise_value_error(message: str) -> None:
    """Wirft deterministisch einen ValueError mit gegebener Meldung."""
    raise ValueError(message)


def record_call(marker: Path, value: Any = 42) -> Any:
    """Protokolliert einen Target-Aufruf auf der Platte für Guard-Prüfungen."""
    with marker.open("a", encoding="utf-8") as stream:
        stream.write("executed")
    return value


def _is_cubie_prefix(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("cu")


def _is_cubie(value: Any) -> bool:
    return value == "cubie"


def _has_len_five(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 5


def _starts_with_om(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("om")


def _gt_minus_ten(value: Any) -> bool:
    return isinstance(value, int) and value > -10


@pytest.fixture(name="execution_mode", params=[False, True], ids=["singleprocess", "multiprocess"])
def _execution_mode_fixture(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> bool:
    """Führt Verträge sowohl im Einzelprozess als auch im Worker-Pool aus."""
    monkeypatch.setattr("qb_cubie.multiprocessors.os.cpu_count", lambda: 2)
    return bool(request.param)


# ========== GRUPPE A: BASELINE-PARITÄT ============================================================


def test_quantor_explicit_matches_implicit_default(execution_mode: bool) -> None:
    """Explizite Standard-Quantoren liefern identische Ergebnisse und Traces wie implizite."""
    ws1, ws2 = WorldState(args=("  TEXT ",)), WorldState(args=("TeXt",))
    ws_out = WorldState(returns="text")
    pre_cfg: Any = {"quantor": "all", "states": [ws1, ws2]}
    post_cfg: Any = {"quantor": "exists", "states": ws_out}
    implicit = EBT(
        target=target_normalize,
        pre=[ws1, ws2],
        post=ws_out,
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    explicit = EBT(
        target=target_normalize,
        pre=pre_cfg,
        post=post_cfg,
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert implicit is not None and explicit is not None
    assert implicit.evaluation is True and explicit.evaluation is True
    assert explicit.pre_quantor == "all"
    assert explicit.post_quantor == "exists"
    assert len(explicit.traces or []) == len(implicit.traces or []) == 2
    assert [t.evaluation for t in explicit.traces or []] == [True, True]


def test_quantor_single_worldstate_in_dict_wrapper(execution_mode: bool) -> None:
    """Ein einzelner WorldState unter 'states' wird für pre und post normalisiert."""
    pre_cfg: Any = {"quantor": "all", "states": WorldState(args=("  Cubie ",))}
    post_cfg: Any = {"quantor": "exists", "states": WorldState(returns="cubie")}
    trace = EBT(
        target=target_normalize,
        pre=pre_cfg,
        post=post_cfg,
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "exists"
    assert len(trace.traces or []) == 1


# ========== GRUPPE B: PRE-QUANTOR ('all' VS. 'exists') ============================================


def test_pre_quantor_all_aborts_on_first_failure() -> None:
    """pre='all' scheitert und meldet exakt den ersten fehlgeschlagenen Schritt."""
    pre_cfg: Any = {
        "quantor": "all",
        "states": [
            WorldState(args=("/health",)),
            WorldState(args=("/broken",)),
            WorldState(args=("/health",)),
        ],
    }
    post_ws = WorldState(returns="ok")
    case = EBT(target=target_flaky_route, pre=pre_cfg, post=post_ws)
    with pytest.raises(AssertionError) as error:
        case.run()
    trace = case.run_trace
    assert trace is not None
    assert trace.evaluation is False
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "exists"
    assert len(trace.traces or []) == 3
    failed = [item.step_id for item in (trace.traces or []) if not item.evaluation]
    assert failed == [f"{trace.run_id}_1"]
    assert f"for step '{trace.run_id}_1':" in str(error.value)
    neg_trace = EBT(
        target=target_flaky_route,
        pre=pre_cfg,
        post=post_ws,
        expect=False,
        reporter=None,
    ).run()
    assert neg_trace is not None and neg_trace.evaluation is True


def test_pre_quantor_all_reports_first_of_multiple_failures() -> None:
    """Bei mehreren Fehlschlägen unter pre='all' meldet PytestReporter den ersten Schritt."""
    pre_cfg: Any = {
        "quantor": "all",
        "states": [
            WorldState(args=("/health",)),
            WorldState(args=("/broken-1",)),
            WorldState(args=("/broken-2",)),
        ],
    }
    case = EBT(
        target=target_flaky_route,
        pre=pre_cfg,
        post=WorldState(returns="ok"),
    )
    with pytest.raises(AssertionError) as error:
        case.run()
    trace = case.run_trace
    assert trace is not None
    assert [item.evaluation for item in (trace.traces or [])] == [True, False, False]
    assert f"for step '{trace.run_id}_1':" in str(error.value)
    assert f"for step '{trace.run_id}_2':" not in str(error.value)


def test_pre_quantor_exists_succeeds_if_one_input_matches(execution_mode: bool) -> None:
    """pre='exists' besteht, sobald mindestens ein Eingang die Nachbedingung erfüllt."""
    pre_cfg: Any = {
        "quantor": "exists",
        "states": [
            WorldState(args=("/down-1",)),
            WorldState(args=("/health",)),
            WorldState(args=("/down-2",)),
        ],
    }
    trace = EBT(
        target=target_flaky_route,
        pre=pre_cfg,
        post=WorldState(returns="ok"),
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert trace.pre_quantor == "exists"
    assert trace.post_quantor == "exists"
    assert [item.evaluation for item in (trace.traces or [])] == [False, True, False]


@pytest.mark.parametrize("expect, expected_eval", [(True, False), (False, True)])
def test_pre_quantor_exists_fails_when_all_inputs_fail(
    execution_mode: bool,
    expect: bool,
    expected_eval: bool,
) -> None:
    """pre='exists' scheitert, wenn kein einziger Eingang post erfüllt."""
    pre_cfg: Any = {
        "quantor": "exists",
        "states": [WorldState(args=("/down-1",)), WorldState(args=("/down-2",))],
    }
    trace = EBT(
        target=target_flaky_route,
        pre=pre_cfg,
        post=WorldState(returns="ok"),
        expect=expect,
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is expected_eval
    assert trace.pre_quantor == "exists"
    assert trace.post_quantor == "exists"
    assert [item.evaluation for item in (trace.traces or [])] == [False, False]


# ========== GRUPPE C: POST-QUANTOR ('exists' VS. 'all') ===========================================


def test_post_quantor_exists_passes_on_partial_match(execution_mode: bool) -> None:
    """post='exists' besteht bei einem Treffer und protokolliert alle Zielmuster."""
    post_cfg: Any = {
        "quantor": "exists",
        "states": [WorldState(returns=99), WorldState(returns=10), WorldState(returns=0)],
    }
    trace = EBT(
        target=target_identity,
        pre=WorldState(args=(10,)),
        post=post_cfg,
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "exists"
    assert len(trace.traces or []) == 3
    assert [item.evaluation for item in (trace.traces or [])] == [False, True, False]


def test_post_quantor_all_requires_every_post_predicate(execution_mode: bool) -> None:
    """post='all' erzwingt alle Ziel-Prädikate gleichzeitig."""
    post_cfg: Any = {
        "quantor": "all",
        "states": [
            WorldState(returns=str),
            WorldState(returns=lambda val: val == "cubie"),
            WorldState(returns=lambda val: len(val) == 5),
        ],
    }
    trace = EBT(
        target=target_normalize,
        pre=WorldState(args=("  Cubie  ",)),
        post=post_cfg,
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "all"
    assert [item.evaluation for item in (trace.traces or [])] == [True, True, True]


@pytest.mark.parametrize("fail_index", [0, 1, 2], ids=["first", "middle", "last"])
@pytest.mark.parametrize("expect, expected_eval", [(True, False), (False, True)])
def test_post_quantor_all_fails_if_single_predicate_violated(
    fail_index: int,
    expect: bool,
    expected_eval: bool,
) -> None:
    """post='all' scheitert unabhängig von der Position, sobald ein Prädikat verletzt wird."""
    states = [
        WorldState(returns=str),
        WorldState(returns=lambda val: val == "cubie"),
        WorldState(returns=lambda val: len(val) == 5),
    ]
    failing_predicates: list[Any] = [
        int,
        lambda val: val == "other",
        lambda val: len(val) == 99,
    ]
    states[fail_index] = WorldState(returns=failing_predicates[fail_index])
    post_cfg: Any = {"quantor": "all", "states": states}
    trace = EBT(
        target=target_normalize,
        pre=WorldState(args=("  Cubie  ",)),
        post=post_cfg,
        expect=expect,
        reporter=None,
    ).run()
    assert trace is not None
    assert trace.evaluation is expected_eval
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "all"
    expected_matches = [idx != fail_index for idx in range(3)]
    assert [item.evaluation for item in (trace.traces or [])] == expected_matches


# ========== GRUPPE D: KREUZ-KOMBINATIONEN, REPORTER & MULTIPROCESSING =============================


def test_inverted_quantors_pre_exists_post_all(execution_mode: bool) -> None:
    """pre='exists' x post='all' besteht, wenn ein Eingang alle Prädikate erfüllt."""
    pre_cfg: Any = {
        "quantor": "exists",
        "states": [WorldState(args=("  no ",)), WorldState(args=("  Cubie  ",))],
    }
    post_cfg: Any = {
        "quantor": "all",
        "states": [
            WorldState(returns=_is_cubie_prefix),
            WorldState(returns=_is_cubie),
            WorldState(returns=_has_len_five),
        ],
    }
    trace = EBT(
        target=target_normalize,
        pre=pre_cfg,
        post=post_cfg,
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert trace.pre_quantor == "exists"
    assert trace.post_quantor == "all"
    assert [item.evaluation for item in (trace.traces or [])] == [
        False, False, False, True, True, True,
    ]


@pytest.mark.parametrize("expect, expected_eval", [(True, False), (False, True)])
def test_inverted_quantors_pre_exists_post_all_rejects_split_satisfaction(
    execution_mode: bool,
    expect: bool,
    expected_eval: bool,
) -> None:
    """pre='exists' x post='all' scheitert bei verteilter Erfüllung ohne Volltreffer."""
    pre_cfg: Any = {
        "quantor": "exists",
        "states": [WorldState(args=("  alpha ",)), WorldState(args=("  omega_long  ",))],
    }
    post_cfg: Any = {
        "quantor": "all",
        "states": [
            WorldState(returns=_has_len_five),
            WorldState(returns=_starts_with_om),
        ],
    }
    trace = EBT(
        target=target_normalize,
        pre=pre_cfg,
        post=post_cfg,
        expect=expect,
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is expected_eval
    assert trace.pre_quantor == "exists"
    assert trace.post_quantor == "all"
    assert [item.evaluation for item in (trace.traces or [])] == [True, False, False, True]


@pytest.mark.parametrize(
    "value, expect, expected_eval",
    [
        (42, True, True),
        (-20, True, False),
        (-1, True, False),
        (-2, True, False),
        (-1, False, True),
        (-20, False, True),
    ],
    ids=[
        "valid-positive",
        "fails-second-positive-predicate",
        "violates-first-negative-filter",
        "violates-second-negative-filter",
        "negative-filter-expect-false",
        "positive-predicate-expect-false",
    ],
)
def test_post_quantor_all_with_negative_worldstate_expect_false(
    execution_mode: bool,
    value: int,
    expect: bool,
    expected_eval: bool,
) -> None:
    """post='all' erzwingt alle positiven Prädikate und scheitert an jedem expect=False-Treffer."""
    post_cfg: Any = {
        "quantor": "all",
        "states": [
            WorldState(returns=int),
            WorldState(returns=_gt_minus_ten),
            WorldState(returns=-1, expect=False),
            WorldState(returns=-2, expect=False),
        ],
    }
    trace = EBT(
        target=target_identity,
        pre=WorldState(args=(value,)),
        post=post_cfg,
        expect=expect,
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is expected_eval
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "all"


@pytest.mark.parametrize("expect, expected_eval", [(True, False), (False, True)])
def test_double_negation_guard_with_exception_contract(
    expect: bool,
    expected_eval: bool,
) -> None:
    """post='all' prüft auch mehrere Ausnahmeverträge konjunktiv und reagiert auf Index 0."""
    post_cfg: Any = {
        "quantor": "all",
        "states": [
            WorldState(raises=ExceptionExpectation(ValueError, match=r"^expected")),
            WorldState(raises=ExceptionExpectation(ValueError)),
        ],
    }
    trace = EBT(
        target=target_raise_value_error,
        pre=WorldState(args=("unexpected error",)),
        post=post_cfg,
        expect=expect,
        reporter=None,
    ).run()
    assert trace is not None
    assert trace.evaluation is expected_eval
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "all"
    assert [item.evaluation for item in (trace.traces or [])] == [False, True]


def test_pytest_reporter_reports_when_pre_exists_all_fail() -> None:
    """PytestReporter meldet einen AssertionError, wenn alle pre='exists'-Läufe scheitern."""
    pre_cfg: Any = {
        "quantor": "exists",
        "states": [WorldState(args=("/down-1",)), WorldState(args=("/down-2",))],
    }
    case = EBT(
        target=target_flaky_route,
        pre=pre_cfg,
        post=WorldState(returns="ok"),
    )
    with pytest.raises(AssertionError) as error:
        case.run()
    assert case.run_trace is not None
    assert case.run_trace.evaluation is False
    message = str(error.value)
    assert "EBT-Assert failed" in message
    assert "Target: target_flaky_route" in message
    assert "[Q-State 0] Validation: Mismatch" in message


def test_pytest_reporter_selects_step_failing_post_all() -> None:
    """PytestReporter wählt bei post='all' den Schritt mit partiellem Mismatch korrekt aus."""
    post_cfg: Any = {
        "quantor": "all",
        "states": [
            WorldState(returns=str),
            WorldState(returns=lambda val: val == "cubie"),
        ],
    }
    case = EBT(
        target=target_normalize,
        pre=[WorldState(args=("  Cubie  ",)), WorldState(args=("  other ",))],
        post=post_cfg,
    )
    with pytest.raises(AssertionError) as error:
        case.run()
    trace = case.run_trace
    assert trace is not None
    assert trace.evaluation is False
    message = str(error.value)
    assert f"for step '{trace.run_id}_1':" in message
    assert "[Q-State 0] Validation: Matched" in message
    assert "[Q-State 1] Validation: Mismatch" in message


def test_json_reporter_persists_explicit_quantors(tmp_path: Path, execution_mode: bool) -> None:
    """JsonReporter persistiert explizite pre_quantor- und post_quantor-Felder im JSON-Dokument."""
    report_path = tmp_path / "quantor_report.json"
    pre_cfg: Any = {
        "quantor": "exists",
        "states": [WorldState(args=("  no ",)), WorldState(args=("  Cubie  ",))],
    }
    post_cfg: Any = {
        "quantor": "all",
        "states": [WorldState(returns=_is_cubie_prefix), WorldState(returns=_has_len_five)],
    }
    trace = EBT(
        target=target_normalize,
        pre=pre_cfg,
        post=post_cfg,
        reporter=JsonReporter(report_path),
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    document = json.loads(report_path.read_text(encoding="utf-8"))
    assert document["run_id"] == trace.run_id
    assert document["evaluation"] is True
    assert document["pre_quantor"] == "exists"
    assert document["post_quantor"] == "all"
    assert len(document["traces"]) == 4


# ========== GRUPPE E: STATE-GUARDS, FEHLERBEHANDLUNG & REVALIDIERUNG ==============================


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize(
    "bad_quantor",
    ["any", "none", "", "ALL", " exists ", "Exists"],
    ids=["any", "none", "empty", "upper-all", "padded-exists", "title-exists"],
)
def test_guard_rejects_unknown_quantor_value(
    tmp_path: Path,
    field: str,
    bad_quantor: str,
) -> None:
    """STATE-GUARD weist unbekannte Quantor-Strings inkl. Case-/Whitespace-Varianten ab."""
    marker = tmp_path / "called"
    bad_cfg = {"quantor": bad_quantor, "states": [WorldState()]}
    pre_val: Any = bad_cfg if field == "pre" else WorldState()
    post_val: Any = bad_cfg if field == "post" else WorldState()
    with pytest.raises((ValueError, TypeError)) as error:
        EBT(target=partial(record_call, marker), pre=pre_val, post=post_val, reporter=None).run()
    assert "all" in str(error.value) and "exists" in str(error.value)
    assert not marker.exists()


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize(
    "bad_cfg, expected_tokens",
    [
        ({}, ("quantor", "states")),
        ({"quantor": "all"}, ("states",)),
        ({"quantor": "exists"}, ("states",)),
        ({"states": [WorldState()]}, ("quantor",)),
        ({"quantor": "all", "states": [WorldState()], "extra": 1}, ("extra",)),
    ],
    ids=[
        "empty-dict",
        "missing-states-all",
        "missing-states-exists",
        "missing-quantor",
        "extra-key",
    ],
)
def test_guard_rejects_malformed_wrapper_keys(
    tmp_path: Path,
    field: str,
    bad_cfg: dict[str, Any],
    expected_tokens: tuple[str, ...],
) -> None:
    """STATE-GUARD greift bei fehlenden Pflichtschlüsseln oder Zusatzschlüsseln vor Ausführung."""
    marker = tmp_path / "called"
    pre_val: Any = bad_cfg if field == "pre" else WorldState()
    post_val: Any = bad_cfg if field == "post" else WorldState()
    with pytest.raises((ValueError, TypeError)) as error:
        EBT(target=partial(record_call, marker), pre=pre_val, post=post_val, reporter=None).run()
    msg = str(error.value)
    assert any(token in msg for token in expected_tokens)
    assert not marker.exists()


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize("quantor_val", ["all", "exists"])
def test_guard_rejects_empty_states_collection(
    tmp_path: Path,
    execution_mode: bool,
    field: str,
    quantor_val: str,
) -> None:
    """STATE-GUARD verhindert Vacuous Pass bei leerer 'states'-Menge via ValueError."""
    marker = tmp_path / "called"
    bad_cfg: dict[str, Any] = {"quantor": quantor_val, "states": []}
    pre_val: Any = bad_cfg if field == "pre" else WorldState()
    post_val: Any = bad_cfg if field == "post" else WorldState()
    with pytest.raises(ValueError, match="states"):
        EBT(
            target=partial(record_call, marker),
            pre=pre_val,
            post=post_val,
            reporter=None,
            multiprocessing=execution_mode,
        ).run()
    assert not marker.exists()


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize(
    "bad_quantor", [None, True, False, 1], ids=["none", "true", "false", "int"],
)
def test_guard_rejects_non_string_quantor_type(
    tmp_path: Path,
    field: str,
    bad_quantor: Any,
) -> None:
    """STATE-GUARD weist Nicht-Strings wie None, bool oder int sauber als TypeError ab."""
    marker = tmp_path / "called"
    bad_cfg = {"quantor": bad_quantor, "states": [WorldState()]}
    pre_val: Any = bad_cfg if field == "pre" else WorldState()
    post_val: Any = bad_cfg if field == "post" else WorldState()
    with pytest.raises(TypeError, match="quantor"):
        EBT(target=partial(record_call, marker), pre=pre_val, post=post_val, reporter=None).run()
    assert not marker.exists()


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize(
    "bad_states",
    [None, 42, "state", (WorldState(),), [None], [WorldState(), "bad"]],
    ids=["none", "int", "str", "tuple", "list-of-none", "mixed-list"],
)
def test_guard_rejects_invalid_states_in_wrapper(
    tmp_path: Path,
    field: str,
    bad_states: Any,
) -> None:
    """STATE-GUARD weist ungültige Container oder Elemente unter 'states' als TypeError ab."""
    marker = tmp_path / "called"
    bad_cfg = {"quantor": "all", "states": bad_states}
    pre_val: Any = bad_cfg if field == "pre" else WorldState()
    post_val: Any = bad_cfg if field == "post" else WorldState()
    with pytest.raises(TypeError) as error:
        EBT(target=partial(record_call, marker), pre=pre_val, post=post_val, reporter=None).run()
    msg = str(error.value)
    assert "states" in msg
    assert "WorldState" in msg
    assert not marker.exists()


@pytest.mark.parametrize("field", ["pre", "post"])
def test_default_reporter_rejects_invalid_quantor_wrapper(tmp_path: Path, field: str) -> None:
    """Auch mit aktivem Standard-PytestReporter greifen STATE-GUARDs vor der Ausführung."""
    marker = tmp_path / "called"
    bad_cfg: dict[str, Any] = {"quantor": "all", "states": []}
    pre_val: Any = bad_cfg if field == "pre" else WorldState()
    post_val: Any = bad_cfg if field == "post" else WorldState()
    with pytest.raises(ValueError, match="states"):
        EBT(target=partial(record_call, marker), pre=pre_val, post=post_val).run()
    assert not marker.exists()


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize(
    "invalid_cfg, error_type",
    [
        ({"quantor": "all", "states": []}, ValueError),
        ({"quantor": "invalid", "states": [WorldState()]}, (ValueError, TypeError)),
        ({"quantor": True, "states": [WorldState()]}, TypeError),
    ],
    ids=["empty-states", "unknown-quantor", "bool-quantor"],
)
def test_changed_quantor_wrapper_is_revalidated(
    tmp_path: Path,
    execution_mode: bool,
    field: str,
    invalid_cfg: dict[str, Any],
    error_type: type[Exception] | tuple[type[Exception], ...],
) -> None:
    """Mutationen an case.pre oder case.post zwischen Läufen werden vorab revalidiert."""
    marker = tmp_path / "called"
    pre_cfg: Any = {"quantor": "all", "states": [WorldState()]}
    post_cfg: Any = {"quantor": "exists", "states": [WorldState(returns=42)]}
    case = EBT(
        target=partial(record_call, marker),
        pre=pre_cfg,
        post=post_cfg,
        reporter=None,
        multiprocessing=execution_mode,
    )
    previous = case.run()
    assert previous is not None and previous.evaluation is True
    marker.unlink()
    setattr(case, field, invalid_cfg)
    with pytest.raises(error_type):
        case.run()
    assert not marker.exists()
    assert case.run_trace is None
    assert previous.evaluation is True
