"""Verifikation der expliziten Quantoren-Deklaration ('all' / 'exists') in EBT."""

from __future__ import annotations

from typing import Any

import pytest

from qb_cubie import EBT, WorldState
from qb_cubie.reporter import PytestReporter


# ========== DUMMY TARGETS =============================================================================================


def target_normalize(raw: str) -> str:
    """Deterministische Beispiel-Funktion für String-Normalisierung."""
    return raw.strip().lower()


def target_divide(numerator: int, denominator: int) -> float:
    """Deterministische Divisions-Funktion ohne Seiteneffekte."""
    return numerator / denominator


def target_flaky_route(route: str) -> str:
    """Simuliert deterministisch erfolgreiche und fehlschlagende Routen."""
    return "ok" if route == "/health" else "error"


def target_identity(value: Any) -> Any:
    """Gibt den übergebenen Wert unverändert zurück."""
    return value


def _unreached_target(*_args: Any, **_kwargs: Any) -> Any:
    """Schlägt fehl, falls ein STATE-GUARD den Target-Aufruf nicht verhindert."""
    raise AssertionError("Target darf bei aktivem STATE-GUARD nicht ausgeführt werden.")


# ========== STATELESS ADAPTERS ========================================================================================


def _eval_contract_adapter(
    target: Any, pre: Any, post: Any, *, expect: bool = True, tags: Any = None,
) -> dict[str, Any]:
    """Zustandsfreier Adapter: projiziert EBT-Läufe, Traces und Guards auf ein Prüf-Dict."""
    try:
        trace = EBT(target=target, pre=pre, post=post, expect=expect, tags=tags, reporter=None).run()
        assert trace is not None
        return {
            "evaluation": trace.evaluation, "trace_count": len(trace.traces or []),
            "pre_quantor": trace.pre_quantor, "post_quantor": trace.post_quantor,
            "error_type": None, "error_msg": None,
        }
    except (ValueError, TypeError) as exc:
        return {
            "evaluation": False, "trace_count": 0,
            "pre_quantor": None, "post_quantor": None,
            "error_type": type(exc).__name__, "error_msg": str(exc),
        }


def _eval_failure_step_adapter(target: Any, pre: Any, post: Any) -> dict[str, Any]:
    """Zustandsfreier Adapter: erfasst den fehlgeschlagenen Schritt im Trace und Reporter."""
    try:
        trace = EBT(target=target, pre=pre, post=post, reporter=None).run()
        assert trace is not None
        failed = [item for item in (trace.traces or []) if not item.evaluation]
        report_msg = _capture_pytest_report(trace)
        return {
            "evaluation": trace.evaluation,
            "pre_quantor": trace.pre_quantor,
            "post_quantor": trace.post_quantor,
            "failed_step_ids": [item.step_id for item in failed],
            "expected_step_id": f"{trace.run_id}_1",
            "report_mentions_step_1": f"for step '{trace.run_id}_1':" in report_msg,
            "error_type": None,
        }
    except (ValueError, TypeError) as exc:
        return {
            "evaluation": False,
            "pre_quantor": None,
            "post_quantor": None,
            "failed_step_ids": [],
            "expected_step_id": "",
            "report_mentions_step_1": False,
            "error_type": type(exc).__name__,
        }


def _capture_pytest_report(trace: Any) -> str:
    """Ermittelt die PytestReporter-Fehlermeldung eines fehlgeschlagenen RunTrace."""
    try:
        PytestReporter().report(trace)
    except AssertionError as exc:
        return str(exc)
    return ""


# ========== GRUPPE A: BASELINE-PARITÄT ================================================================================


def test_quantor_explicit_matches_implicit_default() -> None:
    """Explizite Standard-Quantoren liefern identische Ergebnisse und Traces wie implizite."""
    ws1, ws2 = WorldState(args=("  TEXT ",)), WorldState(args=("TeXt",))
    ws_out = WorldState(returns="text")
    expected = {
        "evaluation": True,
        "trace_count": 2,
        "pre_quantor": "all",
        "post_quantor": "exists",
        "error_type": None,
        "error_msg": None,
    }
    implicit = _eval_contract_adapter(target_normalize, [ws1, ws2], ws_out)
    explicit_pre = {"quantor": "all", "states": [ws1, ws2]}
    explicit_post = {"quantor": "exists", "states": ws_out}
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(args=(target_normalize, explicit_pre, explicit_post)),
        post=WorldState(returns=expected),
        reporter=None,
    ).run()
    assert implicit == expected
    assert outer is not None and outer.evaluation is True


def test_quantor_single_worldstate_in_dict_wrapper() -> None:
    """Ein einzelnes WorldState unter 'states' wird für pre ('all') und post ('exists') normalisiert."""
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(
            args=(
                target_normalize,
                {"quantor": "all", "states": WorldState(args=("  Cubie ",))},
                {"quantor": "exists", "states": WorldState(returns="cubie")},
            )
        ),
        post=WorldState(
            returns={
                "evaluation": True,
                "trace_count": 1,
                "pre_quantor": "all",
                "post_quantor": "exists",
                "error_type": None,
                "error_msg": None,
            }
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True


# ========== GRUPPE B: PRE-QUANTOR ('all' VS. 'exists') ================================================================


def test_pre_quantor_all_aborts_on_first_failure() -> None:
    """pre mit quantor='all' bricht beim ersten Fehlschlag ab und meldet exakt diesen Schritt."""
    pre_cfg = {
        "quantor": "all",
        "states": [WorldState(args=("/health",)), WorldState(args=("/broken",)), WorldState(args=("/health",))],
    }
    post_ws = WorldState(returns="ok")
    failure_check = EBT(
        target=_eval_failure_step_adapter,
        pre=WorldState(args=(target_flaky_route, pre_cfg, post_ws)),
        post=WorldState(
            returns=lambda res: res["evaluation"] is False
            and res["error_type"] is None
            and res["pre_quantor"] == "all"
            and res["post_quantor"] == "exists"
            and res["report_mentions_step_1"] is True
            and res["expected_step_id"] in res["failed_step_ids"]
        ),
        reporter=None,
    ).run()
    neg_check = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(args=(target_flaky_route, pre_cfg, post_ws), kwargs={"expect": False}),
        post=WorldState(returns=lambda res: res["evaluation"] is True and res["pre_quantor"] == "all"),
        reporter=None,
    ).run()
    assert failure_check is not None and failure_check.evaluation is True
    assert neg_check is not None and neg_check.evaluation is True


def test_pre_quantor_exists_succeeds_if_one_input_matches() -> None:
    """pre mit quantor='exists' besteht, sobald mindestens ein Eingang die Nachbedingung erfüllt."""
    pre_cfg = {
        "quantor": "exists",
        "states": [
            WorldState(args=("/down-1",)),
            WorldState(args=("/health",)),
            WorldState(args=("/down-2",)),
        ],
    }
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(args=(target_flaky_route, pre_cfg, WorldState(returns="ok"))),
        post=WorldState(
            returns=lambda res: res["evaluation"] is True
            and res["pre_quantor"] == "exists"
            and res["post_quantor"] == "exists"
            and res["error_type"] is None
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True


@pytest.mark.parametrize("inner_expect, expected_eval", [(True, False), (False, True)])
def test_pre_quantor_exists_fails_when_all_inputs_fail(inner_expect: bool, expected_eval: bool) -> None:
    """pre mit quantor='exists' scheitert, wenn kein einziger Eingang post erfüllt."""
    pre_cfg = {
        "quantor": "exists",
        "states": [WorldState(args=("/down-1",)), WorldState(args=("/down-2",))],
    }
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(
            args=(target_flaky_route, pre_cfg, WorldState(returns="ok")),
            kwargs={"expect": inner_expect},
        ),
        post=WorldState(
            returns=lambda res: res["evaluation"] is expected_eval
            and res["pre_quantor"] == "exists"
            and res["post_quantor"] == "exists"
            and res["error_type"] is None
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True


# ========== GRUPPE C: POST-QUANTOR ('exists' VS. 'all') ===============================================================


def test_post_quantor_exists_passes_on_partial_match() -> None:
    """post mit quantor='exists' besteht bereits bei einem Treffer in den Zielmustern."""
    post_cfg = {
        "quantor": "exists",
        "states": [WorldState(returns=99), WorldState(returns=10), WorldState(returns=0)],
    }
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(args=(target_identity, WorldState(args=(10,)), post_cfg)),
        post=WorldState(
            returns=lambda res: res["evaluation"] is True
            and 1 <= res["trace_count"] <= 3
            and res["pre_quantor"] == "all"
            and res["post_quantor"] == "exists"
            and res["error_type"] is None
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True


def test_post_quantor_all_requires_every_post_predicate() -> None:
    """post mit quantor='all' erzwingt alle Ziel-Prädikate gleichzeitig."""
    post_cfg = {
        "quantor": "all",
        "states": [
            WorldState(returns=str),
            WorldState(returns=lambda val: val == "cubie"),
            WorldState(returns=lambda val: len(val) == 5),
        ],
    }
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(args=(target_normalize, WorldState(args=("  Cubie  ",)), post_cfg)),
        post=WorldState(
            returns={
                "evaluation": True,
                "trace_count": 3,
                "pre_quantor": "all",
                "post_quantor": "all",
                "error_type": None,
                "error_msg": None,
            }
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True


@pytest.mark.parametrize("inner_expect, expected_eval", [(True, False), (False, True)])
def test_post_quantor_all_fails_if_single_predicate_violated(
    inner_expect: bool,
    expected_eval: bool,
) -> None:
    """post mit quantor='all' scheitert, wenn auch nur ein einziges Ziel-Prädikat verletzt wird."""
    post_cfg = {
        "quantor": "all",
        "states": [
            WorldState(returns=str),
            WorldState(returns=lambda val: val == "cubie"),
            WorldState(returns=lambda val: len(val) == 99),
        ],
    }
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(
            args=(target_normalize, WorldState(args=("  Cubie  ",)), post_cfg),
            kwargs={"expect": inner_expect},
        ),
        post=WorldState(
            returns=lambda res: res["evaluation"] is expected_eval
            and res["pre_quantor"] == "all"
            and res["post_quantor"] == "all"
            and res["error_type"] is None
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True


# ========== GRUPPE D: KREUZ-KOMBINATIONEN & EXPECT-INTERAKTION ========================================================


def test_inverted_quantors_pre_exists_post_all() -> None:
    """pre='exists' mit post='all' besteht, wenn ein Eingang alle Nachbedingungen erfüllt."""
    pre_cfg = {
        "quantor": "exists",
        "states": [WorldState(args=("  other ",)), WorldState(args=("  Cubie  ",))],
    }
    post_cfg = {
        "quantor": "all",
        "states": [
            WorldState(returns=str),
            WorldState(returns=lambda val: val == "cubie"),
            WorldState(returns=lambda val: len(val) == 5),
        ],
    }
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(
            args=(target_normalize, pre_cfg, post_cfg),
            kwargs={"tags": {"meta:cross-product-reason": "Tests inverted pre='exists' x post='all'."}},
        ),
        post=WorldState(
            returns=lambda res: res["evaluation"] is True
            and res["pre_quantor"] == "exists"
            and res["post_quantor"] == "all"
            and res["error_type"] is None
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True


@pytest.mark.parametrize(
    "value, inner_expect, expected_eval",
    [(42, True, True), (-1, True, False), (-1, False, True)],
)
def test_post_quantor_all_with_negative_worldstate_expect_false(
    value: int,
    inner_expect: bool,
    expected_eval: bool,
) -> None:
    """post='all' respektiert negative Verbote (expect=False) neben positiven Pflicht-Zuständen."""
    post_cfg = {
        "quantor": "all",
        "states": [WorldState(returns=int), WorldState(returns=-1, expect=False)],
    }
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(
            args=(target_identity, WorldState(args=(value,)), post_cfg),
            kwargs={"expect": inner_expect},
        ),
        post=WorldState(
            returns=lambda res: res["evaluation"] is expected_eval
            and res["pre_quantor"] == "all"
            and res["post_quantor"] == "all"
            and res["error_type"] is None
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True


def test_double_negation_guard_with_explicit_quantor() -> None:
    """EBT(..., expect=False) erkennt zuverlässig das Scheitern eines post='all'-Vertrags."""
    post_cfg = {
        "quantor": "all",
        "states": [WorldState(returns=float), WorldState(returns=lambda val: val > 0)],
    }
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(
            args=(target_divide, WorldState(args=(-10, 2)), post_cfg),
            kwargs={"expect": False},
        ),
        post=WorldState(
            returns=lambda res: res["evaluation"] is True
            and res["pre_quantor"] == "all"
            and res["post_quantor"] == "all"
            and res["error_type"] is None
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True


# ========== GRUPPE E: STATE-GUARDS & FEHLERBEHANDLUNG =================================================================


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize("bad_quantor", ["any", "none", ""])
def test_guard_rejects_unknown_quantor_value(field: str, bad_quantor: str) -> None:
    """STATE-GUARD weist unbekannte Quantor-Strings ab und nennt 'all' und 'exists'."""
    bad_cfg = {"quantor": bad_quantor, "states": [WorldState()]}
    pre_val = bad_cfg if field == "pre" else WorldState()
    post_val = bad_cfg if field == "post" else WorldState()
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(args=(_unreached_target, pre_val, post_val)),
        post=WorldState(
            returns=lambda res: res["evaluation"] is False
            and res["error_type"] in {"ValueError", "TypeError"}
            and res["error_msg"] is not None
            and "all" in res["error_msg"]
            and "exists" in res["error_msg"]
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize("quantor_val", ["all", "exists"])
def test_guard_rejects_missing_states_key_in_wrapper(field: str, quantor_val: str) -> None:
    """STATE-GUARD greift vor Ausführung und meldet das fehlende Pflichtfeld 'states'."""
    bad_cfg = {"quantor": quantor_val}
    pre_val = bad_cfg if field == "pre" else WorldState()
    post_val = bad_cfg if field == "post" else WorldState()
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(args=(_unreached_target, pre_val, post_val)),
        post=WorldState(
            returns=lambda res: res["evaluation"] is False
            and res["error_type"] in {"ValueError", "TypeError"}
            and res["error_msg"] is not None
            and "states" in res["error_msg"]
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True


@pytest.mark.parametrize("field, quantor_val", [("pre", "exists"), ("post", "all")])
def test_guard_rejects_empty_states_collection(field: str, quantor_val: str) -> None:
    """STATE-GUARD verhindert Vacuous Pass bei leerer 'states'-Menge via ValueError."""
    bad_cfg: dict[str, Any] = {"quantor": quantor_val, "states": []}
    pre_val = bad_cfg if field == "pre" else WorldState()
    post_val = bad_cfg if field == "post" else WorldState()
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(args=(_unreached_target, pre_val, post_val)),
        post=WorldState(
            returns=lambda res: res["evaluation"] is False
            and res["error_type"] == "ValueError"
            and res["error_msg"] is not None
            and "states" in res["error_msg"]
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True


@pytest.mark.parametrize("field", ["pre", "post"])
@pytest.mark.parametrize("bad_quantor", [None, True, 1])
def test_guard_rejects_non_bool_or_invalid_quantor_type(field: str, bad_quantor: Any) -> None:
    """STATE-GUARD weist Nicht-Strings wie None, bool oder int sauber als TypeError ab."""
    bad_cfg = {"quantor": bad_quantor, "states": [WorldState()]}
    pre_val = bad_cfg if field == "pre" else WorldState()
    post_val = bad_cfg if field == "post" else WorldState()
    outer = EBT(
        target=_eval_contract_adapter,
        pre=WorldState(args=(_unreached_target, pre_val, post_val)),
        post=WorldState(
            returns=lambda res: res["evaluation"] is False
            and res["error_type"] == "TypeError"
            and res["error_msg"] is not None
            and "quantor" in res["error_msg"]
        ),
        reporter=None,
    ).run()
    assert outer is not None and outer.evaluation is True
