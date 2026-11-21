"""Verifikation der UX-Argument-Normalisierung (args=1, args=(1), args=(1,)) mit expliziten Quantoren."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from qb_cubie import EBT, WorldState
from qb_cubie.core.arenas.tempfs import TempFS
from qb_cubie.core.protocols import ExceptionExpectation
from qb_cubie.core.reporter import JsonReporter

# ========== DUMMY TARGETS =========================================================================


def target_double(value: int) -> int:
    """Verdoppelt eine ganze Zahl deterministisch."""
    return value * 2


def target_normalize(raw: str) -> str:
    """Normalisiert Text durch Trimmen und Kleinschreibung."""
    return raw.strip().lower()


def target_inspect_call(*args: Any, **kwargs: Any) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Gibt alle empfangenen Positions- und Schlüsselwortargumente unverändert zurück."""
    return args, kwargs


def target_scale(value: int, *, factor: int = 1) -> int:
    """Multipliziert einen Positionswert mit einem optionalen Schlüsselwortfaktor."""
    return value * factor


def target_apply_fn(fn: Any) -> Any:
    """Wendet ein als Einzelargument übergebenes Callable auf den Wert 10 an."""
    return fn(10)


def target_write_and_echo(filename: str, content: str = "ok") -> str:
    """Schreibt eine Datei im aktuellen TempFS-Workspace und gibt den Dateinamen zurück."""
    Path(filename).write_text(content, encoding="utf-8")
    return filename


def target_raise_for_text(message: str) -> None:
    """Wirft deterministisch einen ValueError mit dem übergebenen Einzelargument."""
    raise ValueError(message)


def _is_even(value: Any) -> bool:
    return isinstance(value, int) and value % 2 == 0


def _is_positive(value: Any) -> bool:
    return isinstance(value, int) and value > 0


def _has_len_four(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 4


def _starts_with_cu(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("cu")


@pytest.fixture(name="execution_mode", params=[False, True], ids=["singleprocess", "multiprocess"])
def _execution_mode_fixture(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> bool:
    """Führt Verträge sowohl im Einzelprozess als auch im Worker-Pool aus."""
    monkeypatch.setattr("qb_cubie.core.multiprocessors.os.cpu_count", lambda: 2)
    return bool(request.param)


# ========== GRUPPE A: KOMMAFREIE ARGS-UX & RÜCKWÄRTSKOMPATIBILITÄT ===============================


@pytest.mark.parametrize(
    "pre_states",
    [
        [WorldState(args=1), WorldState(args=2)],
        [WorldState(args=(1,)), WorldState(args=(2,))],
        [WorldState(args=[1]), WorldState(args=[2])],
    ],
    ids=["bare-scalar", "legacy-1-tuple", "single-element-list"],
)
def test_single_arg_variants_in_cross_product_matrix(
    execution_mode: bool,
    pre_states: list[WorldState],
) -> None:
    """args=1, args=(1,) und args=[1] verhalten sich in der N:M-Matrix identisch."""
    trace = EBT(
        target=target_double,
        pre={"quantor": "all", "states": pre_states},
        post={"quantor": "exists", "states": [WorldState(returns=2), WorldState(returns=4)]},
        tags={"meta:cross-product-reason": "Prüft bewusst die N:M-Matrix von EBT."},
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "exists"
    assert len(trace.traces or []) == 4


def test_parenthesized_single_arg_without_comma_matches_scalar(execution_mode: bool) -> None:
    """args=(1) und args=(2) ohne Komma funktionieren identisch zu args=1 / args=2."""
    trace = EBT(
        target=target_double,
        pre={"quantor": "all", "states": [WorldState(args=(1)), WorldState(args=(2))]},
        post={"quantor": "exists", "states": [WorldState(returns=2), WorldState(returns=4)]},
        tags={"meta:cross-product-reason": "Prüft bewusst die N:M-Matrix von EBT."},
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "exists"
    assert len(trace.traces or []) == 4


def test_lambda_target_without_trailing_comma_and_bare_scalar() -> None:
    """Die kompakten Doku-Beispiele mit Lambda, args=(1) und args=1 funktionieren direkt."""
    for pre_states in (
        [WorldState(args=(1)), WorldState(args=(2))],
        [WorldState(args=1), WorldState(args=2)],
        [WorldState(args=(1,)), WorldState(args=(2,))],
    ):
        trace = EBT(
            target=lambda x: x * 2,
            pre={"quantor": "all", "states": pre_states},
            post={"quantor": "exists", "states": [WorldState(returns=2), WorldState(returns=4)]},
            tags={"meta:cross-product-reason": "Prüft bewusst die N:M-Matrix von EBT."},
            reporter=None,
        ).run()
        assert trace is not None
        assert trace.evaluation is True
        assert trace.pre_quantor == "all"
        assert trace.post_quantor == "exists"
        assert len(trace.traces or []) == 4


def test_normalize_example_with_string_args_and_explicit_quantors(execution_mode: bool) -> None:
    """Strings als args='TEXT' und args=('TEXT') werden nicht zeichenweise entpackt."""
    trace = EBT(
        target=target_normalize,
        pre={
            "quantor": "all",
            "states": [
                WorldState(args="TEXT"),
                WorldState(args=(" text ")),
                WorldState(args=("TeXt",)),
            ],
        },
        post={"quantor": "exists", "states": WorldState(returns="text")},
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "exists"
    assert len(trace.traces or []) == 3


# ========== GRUPPE B: EDGE CASES DER ARGS-NORMALISIERUNG =========================================


@pytest.mark.parametrize(
    "raw_args, expected_tuple",
    [
        (0, (0,)),
        (False, (False,)),
        ("", ("",)),
        ({}, ({},)),
        ("abc", ("abc",)),
        (b"raw", (b"raw",)),
        ({"k": 1}, ({"k": 1},)),
        ({1, 2}, ({1, 2},)),
        (None, ()),
        ((), ()),
        ([], ()),
        ((None,), (None,)),
        ([None], (None,)),
        ((1, 2), (1, 2)),
        ([1, 2], (1, 2)),
        (([1, 2],), ([1, 2],)),
        ([[1, 2]], ([1, 2],)),
        (((1, 2),), ((1, 2),)),
        ([(1, 2)], ((1, 2),)),
    ],
    ids=[
        "falsy-zero",
        "falsy-false",
        "falsy-empty-str",
        "falsy-empty-dict",
        "str-no-unpack",
        "bytes-no-unpack",
        "dict-no-unpack",
        "set-no-unpack",
        "none-zero-args",
        "empty-tuple-zero-args",
        "empty-list-zero-args",
        "explicit-none-arg-tuple",
        "explicit-none-arg-list",
        "multi-arg-tuple",
        "multi-arg-list",
        "nested-list-in-tuple",
        "nested-list-in-list",
        "nested-tuple-in-tuple",
        "nested-tuple-in-list",
    ],
)
def test_args_normalization_preserves_semantics_across_types(
    execution_mode: bool,
    raw_args: Any,
    expected_tuple: tuple[Any, ...],
) -> None:
    """Einzelwerte, Falsy-Werte, Sequenz-Container und None werden exakt normalisiert."""
    trace = EBT(
        target=target_inspect_call,
        pre={"quantor": "all", "states": WorldState(args=raw_args)},
        post={"quantor": "exists", "states": WorldState(returns=(expected_tuple, {}))},
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert trace.traces is not None and len(trace.traces) == 1
    assert trace.traces[0].outcome.returns == (expected_tuple, {})


def test_single_arg_combined_with_kwargs(execution_mode: bool) -> None:
    """Ein kommafreies Einzelargument lässt sich nahtlos mit kwargs kombinieren."""
    trace = EBT(
        target=target_scale,
        pre={
            "quantor": "all",
            "states": [
                WorldState(args=4, kwargs={"factor": 3}),
                WorldState(args=(6), kwargs={"factor": 2}),
                WorldState(args=(12,), kwargs={"factor": 1}),
            ],
        },
        post={"quantor": "exists", "states": WorldState(returns=12)},
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert len(trace.traces or []) == 3


def test_callable_passed_as_single_unwrapped_arg(execution_mode: bool) -> None:
    """Auch ein Lambda/Callable als direktes args=... bleibt ein einzelnes Positionsargument."""
    trace = EBT(
        target=target_apply_fn,
        pre={"quantor": "all", "states": WorldState(args=lambda x: x + 5)},
        post={"quantor": "exists", "states": WorldState(returns=15)},
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True


# ========== GRUPPE C: EXPLIZITE QUANTOR-KOMBINATIONEN & FILTER ==================================


def test_explicit_pre_exists_post_all_succeeds_for_one_complete_hit(execution_mode: bool) -> None:
    """pre='exists' x post='all' besteht, sobald ein kommafreies Eingangsziel alle Prädikate erfüllt."""
    trace = EBT(
        target=target_double,
        pre={"quantor": "exists", "states": [WorldState(args=-3), WorldState(args=(5))]},
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=int),
                WorldState(returns=_is_even),
                WorldState(returns=_is_positive),
                WorldState(returns=10),
            ],
        },
        tags={"meta:cross-product-reason": "Prüft exists x all mit Einzelwert-args."},
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert trace.pre_quantor == "exists"
    assert trace.post_quantor == "all"
    assert [item.evaluation for item in (trace.traces or [])] == [
        True, True, False, False,
        True, True, True, True,
    ]


@pytest.mark.parametrize("expect, expected_eval", [(True, False), (False, True)])
def test_explicit_pre_exists_post_all_rejects_split_satisfaction(
    execution_mode: bool,
    expect: bool,
    expected_eval: bool,
) -> None:
    """pre='exists' x post='all' lehnt verteilte Teilerfüllung über zwei Läufe hinweg ab."""
    trace = EBT(
        target=target_normalize,
        pre={
            "quantor": "exists",
            "states": [WorldState(args="  AbCd "), WorldState(args="  cubie  ")],
        },
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=_has_len_four),
                WorldState(returns=_starts_with_cu),
            ],
        },
        expect=expect,
        tags={"meta:cross-product-reason": "Prüft Ablehnung verteilter Erfüllung unter exists x all."},
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is expected_eval
    assert trace.pre_quantor == "exists"
    assert trace.post_quantor == "all"
    assert [item.evaluation for item in (trace.traces or [])] == [True, False, False, True]


@pytest.mark.parametrize(
    "raw_input, expect, expected_eval",
    [
        (4, True, True),
        (3, True, False),
        (3, False, True),
        (-2, True, False),
        (-2, False, True),
    ],
    ids=[
        "positive-and-allowed",
        "hits-forbidden-value",
        "forbidden-value-expect-false",
        "fails-positive-predicate",
        "negative-value-expect-false",
    ],
)
def test_explicit_post_all_with_negative_filter_worldstate(
    execution_mode: bool,
    raw_input: int,
    expect: bool,
    expected_eval: bool,
) -> None:
    """post='all' erzwingt alle positiven Prädikate und blockiert jedes expect=False-Muster."""
    trace = EBT(
        target=target_double,
        pre={"quantor": "all", "states": WorldState(args=raw_input)},
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=_is_even),
                WorldState(returns=_is_positive),
                WorldState(returns=6, expect=False),
            ],
        },
        expect=expect,
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is expected_eval
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "all"


def test_explicit_quantors_with_exception_expectation(execution_mode: bool) -> None:
    """Ausnahmeverträge funktionieren mit args='...' und expliziten Quantoren."""
    trace = EBT(
        target=target_raise_for_text,
        pre={
            "quantor": "all",
            "states": [WorldState(args="boom: alpha"), WorldState(args=("boom: beta"))],
        },
        post={
            "quantor": "all",
            "states": [
                WorldState(raises=ExceptionExpectation(ValueError)),
                WorldState(raises=ExceptionExpectation(ValueError, match=r"^boom:")),
            ],
        },
        tags={"meta:cross-product-reason": "Prüft Ausnahmebehandlung mit expliziten Quantoren."},
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "all"
    assert [item.evaluation for item in (trace.traces or [])] == [True, True, True, True]


# ========== GRUPPE D: ARENA, REPORTER & ZUSTANDSMUTATION ==========================================


def test_explicit_quantors_with_tempfs_and_single_string_arg(
    tmp_path: Path,
    execution_mode: bool,
) -> None:
    """TempFS-Läufe funktionieren mit args='report.txt' und expliziten Quantoren."""
    expected_file = tmp_path / "expected.txt"
    expected_file.write_text("ok", encoding="utf-8")
    trace = EBT(
        arena=TempFS(),
        target=target_write_and_echo,
        pre={"quantor": "all", "states": WorldState(args="report.txt")},
        post={
            "quantor": "all",
            "states": [
                WorldState(returns="report.txt"),
                WorldState(fs={"report.txt": str(expected_file)}),
            ],
        },
        reporter=None,
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    assert trace.evaluation is True
    assert trace.pre_quantor == "all"
    assert trace.post_quantor == "all"
    assert trace.traces is not None and len(trace.traces) == 2


def test_pytest_reporter_on_explicit_quantors_failure() -> None:
    """PytestReporter meldet einen verständlichen AssertionError bei verletzten expliziten Quantoren."""
    case = EBT(
        target=target_double,
        pre={"quantor": "exists", "states": [WorldState(args=1), WorldState(args=(2))]},
        post={"quantor": "all", "states": [WorldState(returns=int), WorldState(returns=99)]},
        tags={"meta:cross-product-reason": "Prüft Fehlerbericht bei expliziten Quantoren."},
    )
    with pytest.raises(AssertionError) as error:
        case.run()
    trace = case.run_trace
    assert trace is not None
    assert trace.evaluation is False
    message = str(error.value)
    assert "EBT-Assert failed" in message
    assert "[Q-State 0] Validation: Matched" in message
    assert "[Q-State 1] Validation: Mismatch" in message


def test_json_reporter_persists_unwrapped_args_and_explicit_quantors(
    tmp_path: Path,
    execution_mode: bool,
) -> None:
    """JsonReporter speichert skalare args und explizite Quantor-Felder sauber als UTF-8 JSON."""
    report_path = tmp_path / "args_quantor_report.json"
    trace = EBT(
        target=target_double,
        pre={"quantor": "exists", "states": [WorldState(args=2), WorldState(args=(3))]},
        post={
            "quantor": "all",
            "states": [WorldState(returns=_is_even), WorldState(returns=_is_positive)],
        },
        tags={"meta:cross-product-reason": "Prüft JSON-Persistenz für explizite Quantoren."},
        reporter=JsonReporter(report_path),
        multiprocessing=execution_mode,
    ).run()
    assert trace is not None
    document = json.loads(report_path.read_text(encoding="utf-8"))
    assert document["evaluation"] is True
    assert document["pre_quantor"] == "exists"
    assert document["post_quantor"] == "all"
    assert len(document["traces"]) == 4
    assert document["traces"][0]["pre"]["args"] == {
        "kind": "value",
        "type": "builtins.int",
        "value": 2,
    }


def test_re_running_with_mutated_explicit_quantor_configs() -> None:
    """Wiederholtes Ausführen nach Wechsel von explizitem pre/post-Quantor aktualisiert den Lauf."""
    case: Any = EBT(
        target=target_double,
        pre={"quantor": "all", "states": [WorldState(args=1), WorldState(args=(2))]},
        post={"quantor": "exists", "states": [WorldState(returns=2), WorldState(returns=4)]},
        tags={"meta:cross-product-reason": "Prüft Revalidierung bei expliziter Quantor-Mutation."},
        reporter=None,
    )
    first = case.run()
    assert first is not None and first.evaluation is True
    assert first.pre_quantor == "all" and first.post_quantor == "exists"

    case.pre = {"quantor": "exists", "states": [WorldState(args=5), WorldState(args=3)]}
    case.post = {"quantor": "all", "states": [WorldState(returns=_is_even), WorldState(returns=6)]}
    second = case.run()
    assert second is not None and second.evaluation is True
    assert second.pre_quantor == "exists" and second.post_quantor == "all"
    assert len(second.traces or []) == 4
