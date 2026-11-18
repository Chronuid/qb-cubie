# EBT-Quantor Declarations

**Dokument-Informationen & Herkunft:**

* **Plattform / Umgebung:** Gemini-App
* **Modell:** Gemini-4-Argon
* **Reasoning-Effort:** High
* **Analysedatum:** 18. November 2026, ~22:05 (CET)
* **Synthesebasis:** "User-Prompt", 'docs/GUIDE_Quality-Assurance.md'
* **Stand**: qb-cubie (v0.0.7)
* **Git-Log**: #`git log -n 1`

```text
commit bb62e7ab7184c845465f3522ccee9af1ca7eeb23 (HEAD -> main, origin/main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Wed Nov 18 19:08:49 2026 +0100

    Crafted the prototype 'tests/tests_meta/test_gate_2.py'

```

---

---

# Implementierungsauftrag: Test-Suite für explizite Quantoren-Deklaration (`tests/tests_ebt/test_ebt_quantor_declaration.py`)

## 1. Zielsetzung & Kontext

Erstelle das neue Test-Modul `tests/tests_ebt/test_ebt_quantor_declaration.py` für die Engine `qb_cubie` (`v0.0.7`). Ziel ist die vollständige, orthogonale Verifikation der expliziten Quantoren-Konfiguration in `EBT`-Verträgen über den Dictionary-Wrapper (`{"quantor": "all" | "exists", "states": ...}`) im Zusammenspiel mit den impliziten Standard-Quantoren (`pre` = $\forall$, `post` = $\exists$) sowie den bestehenden `expect`-Flags (`WorldState(..., expect=...)` und `EBT(..., expect=...)`).

Die Test-Suite folgt den Qualitätsrichtlinien aus `docs/GUIDE_Quality-Assurance.md`:

* **Deklarative Verträge & Self-Dogfooding:** Die Prüfung der `EBT`-Engine erfolgt selbst über `EBT`-Verträge und schlanke, zustandsfreie Test-Adapter (`Stateless Adapters`), die interne `EBT`-Execution-Traces auf kanonische Prüf-Dictionaries projizieren.


* **Kein *Vacuous Pass*:** Negativ-Szenarien und erzwungene Fehlschläge werden sauber über `EBT(..., expect=False)` oder kombinierte $Q^+ / Q^-$-Muster abgesichert.


* **Strikte Modul-Hygiene:** Einhaltung aller statischen Leitplanken (`MyPy`, `Pylint`, `AstLinter`/`CstLinter`, maximale Funktionsgröße $\le 30$ Zeilen).



---

## 2. Architektur-Vorgaben für das Test-Modul

### 2.1 Speicherort & Struktur

* **Pfad:** `tests/tests_ebt/test_ebt_quantor_declaration.py`
* **Aufbau:**
1. **Modul-Docstring & Imports:** Saubere Typannotationen (`from __future__ import annotations`, `pytest`, `qb_cubie.EBT`, `qb_cubie.WorldState`).
2. **Deterministische Dummy-Targets:** Kleine, reine Hilfsfunktionen (`target_normalize`, `target_divide`, `target_flaky_route`, `target_identity`) ohne Seiteneffekte.
3. **Zustandsfreier Prüf-Adapter (`_eval_contract_adapter`):** Führt einen inneren `EBT`-Vertrag aus (`reporter=None`), fängt ggf. erwartete Guard-/Contract-Exceptions ab und projiziert das Ergebnis auf ein kanonisches Dictionary:
```python
{
    "evaluation": bool,
    "trace_count": int,
    "error_type": str | None,
    "error_msg": str | None,
}

```


4. **Test-Funktionen (Äquivalenzklassen):** Jede Test-Funktion prüft genau eine klar abgegrenzte Äquivalenzklasse oder Grenzbedingung.





---

## 3. Explizite Vorschläge für Test-Cases (Spezifikation)

Die folgende Matrix definiert die verbindlichen Test-Cases, die im Modul `tests/tests_ebt/test_ebt_quantor_declaration.py` implementiert werden müssen:

### Gruppe A: Impliziter Standard vs. Explizite Äquivalenz (Baseline-Parität)

| Test-ID / Funktionsname | Szenario & Konfiguration | Erwartetes Verhalten ($Q_{\text{Soll}}$) |
| --- | --- | --- |
| **`test_quantor_explicit_matches_implicit_default`** | Vergleich von Standard-Aufruf (`pre=[ws1, ws2]`, `post=ws_out`) mit explizitem Wrapper (`pre={"quantor": "all", "states": [ws1, ws2]}`, `post={"quantor": "exists", "states": ws_out}`) auf `target_normalize`. | Beide Läufe liefern `evaluation == True` und exakt identische `trace_count == 2`. |
| **`test_quantor_single_worldstate_in_dict_wrapper`** | Übergabe eines einzelnen `WorldState`-Objekts (nicht als Liste) unter `"states"` sowohl für `pre` (`"all"`) als auch für `post` (`"exists"`). | Normalisierung durch `EBT` greift fehlerfrei; `evaluation == True`, `trace_count == 1`. |

### Gruppe B: Vorbedingung (`pre`) mit `quantor="all"` vs. `quantor="exists"`

| Test-ID / Funktionsname | Szenario & Konfiguration | Erwartetes Verhalten ($Q_{\text{Soll}}$) |
| --- | --- | --- |
| **`test_pre_quantor_all_aborts_on_first_failure`** | `pre={"quantor": "all", "states": [ws_valid, ws_invalid, ws_valid_2]}` gegen ein Target, bei dem `ws_invalid` die Nachbedingung verletzt. | `evaluation == False` (bzw. `EBT(..., expect=False)` ist `True`). Vorzeitiger Abbruch beim fehlgeschlagenen Schritt; die Fehlermeldung/Trace identifiziert exakt den fehlgeschlagenen Schritt (`ws_invalid`). |
| **`test_pre_quantor_exists_succeeds_if_one_input_matches`** | `pre={"quantor": "exists", "states": [ws_failing_1, ws_passing, ws_failing_2]}` und `post=WorldState(returns="ok")`. | **Semantik-Umkehr:** Obwohl zwei `pre`-Zustände scheitern, reicht der eine erfolgreiche Durchlauf (`ws_passing`) aus, damit der Gesamtvertrag mit `evaluation == True` besteht. |
| **`test_pre_quantor_exists_fails_when_all_inputs_fail`** | `pre={"quantor": "exists", "states": [ws_failing_1, ws_failing_2]}` und `post=WorldState(returns="ok")`. | Kein einziger `pre`-Zustand erfüllt `post` $\rightarrow$ `evaluation == False` (abgesichert via `EBT(..., expect=False)`). |

### Gruppe C: Nachbedingung (`post`) mit `quantor="exists"` vs. `quantor="all"`

| Test-ID / Funktionsname | Szenario & Konfiguration | Erwartetes Verhalten ($Q_{\text{Soll}}$) |
| --- | --- | --- |
| **`test_post_quantor_exists_passes_on_partial_match`** | `pre=WorldState(args=(10,))` und `post={"quantor": "exists", "states": [WorldState(returns=99), WorldState(returns=10), WorldState(returns=0)]}`. | Standardverhalten explizit notiert: Da `returns=10` matcht, gilt `evaluation == True` (`trace_count == 3` oder bis Match). |
| **`test_post_quantor_all_requires_every_post_predicate`** | `pre=WorldState(args=("  Cubie  ",))` und `post={"quantor": "all", "states": [WorldState(returns=str), WorldState(returns=lambda s: s == "cubie"), WorldState(returns=lambda s: len(s) == 5)]}`. | **Semantik-Umkehr:** Alle drei Prädikate in `post` müssen gleichzeitig auf das Ergebnis zutreffen $\rightarrow$ `evaluation == True`. |
| **`test_post_quantor_all_fails_if_single_predicate_violated`** | Wie oben, jedoch schlägt das dritte Prädikat (`len(s) == 99`) fehl, während die ersten beiden passen. | Im Gegensatz zu `quantor="exists"` reicht ein Teil-Match nicht aus $\rightarrow$ `evaluation == False` (abgesichert via `EBT(..., expect=False)`). |

### Gruppe D: Kreuz-Kombinationen & Zusammenspiel mit `expect=False`

| Test-ID / Funktionsname | Szenario & Konfiguration | Erwartetes Verhalten ($Q_{\text{Soll}}$) |
| --- | --- | --- |
| **`test_inverted_quantors_pre_exists_post_all`** | Vollständige Inversion beider Quantoren: `pre={"quantor": "exists", "states": [bad_in, good_in]}` kombiniert mit `post={"quantor": "all", "states": [pred_1, pred_2]}`. | Es existiert mindestens eine Eingabe (`good_in`), für die *alle* Nachbedingungen (`pred_1` und `pred_2`) erfüllt sind $\rightarrow$ `evaluation == True`. |
| **`test_post_quantor_all_with_negative_worldstate_expect_false`** | `post={"quantor": "all", "states": [WorldState(returns=int), WorldState(returns=-1, expect=False)]}` bei Rückgabe `42` vs. Rückgabe `-1`. | Bei `42` sind alle Bedingungen erfüllt (`True`). Bei `-1` ist zwar `int` erfüllt, aber das Verbot `expect=False` verletzt $\rightarrow$ `evaluation == False`.

 |
| **`test_double_negation_guard_with_explicit_quantor`** | Kombination von `post={"quantor": "all", "states": [...]}` mit äußerem `EBT(..., expect=False)` als Red-Phase-Nachweis gegen ein fehlerhaftes Target.

 | Der äußere Vertrag erkennt das Scheitern des `all`-Quantors zuverlässig und meldet `evaluation == True`.

 |

### Gruppe E: `STATE-GUARD`s & Fehlerbehandlung bei ungültiger Konfiguration

| Test-ID / Funktionsname | Szenario & Konfiguration | Erwartetes Verhalten ($Q_{\text{Soll}}$) |
| --- | --- | --- |
| **`test_guard_rejects_unknown_quantor_value`** | Übergabe eines ungültigen Strings, z. B. `pre={"quantor": "any", "states": [...]}` oder `post={"quantor": "none", "states": [...]}`. | Sofortiger Abbruch durch `STATE-GUARD` (`ValueError` / `TypeError`) mit klarer Benennung der erlaubten Werte (`"all"`, `"exists"`).

 |
| **`test_guard_rejects_missing_states_key_in_wrapper`** | Übergabe eines Dictionaries ohne `"states"`-Schlüssel, z. B. `pre={"quantor": "all"}`. | `STATE-GUARD` greift vor der Ausführung und meldet das fehlende Pflichtfeld `"states"`.

 |
| **`test_guard_rejects_empty_states_collection`** | Übergabe einer leeren Liste: `pre={"quantor": "exists", "states": []}` sowie `post={"quantor": "all", "states": []}`. | Verhindert *Vacuous Pass* bzw. undefinierte Quantifizierung über leere Mengen ($\emptyset$) durch expliziten `STATE-GUARD`.

 |
| **`test_guard_rejects_non_bool_or_invalid_quantor_type`** | Übergabe von Nicht-Strings wie `quantor=None`, `quantor=True` oder `quantor=1`. | Typprüfung weist den falschen Datentyp sauber ab.

 |

---

## 4. Konkrete Code-Vorlage für den Einstieg (Referenz-Implementierung)

Die folgende Struktur dient als verbindliche Vorlage für Stil, Typisierung und kompakte Funktionsgrößen in `tests/tests_ebt/test_ebt_quantor_declaration.py`:

```python
"""Verifikation der expliziten Quantoren-Deklaration ('all' / 'exists') in EBT."""

from __future__ import annotations

from typing import Any

import pytest

from qb_cubie import EBT, WorldState


def _target_normalize(raw: str) -> str:
    """Deterministische Beispiel-Funktion für String-Normalisierung."""
    return raw.strip().lower()


def _run_ebt_projection(
    target: Any,
    pre: Any,
    post: Any,
    *,
    expect: bool = True,
) -> dict[str, Any]:
    """Zustandsfreier Adapter: projiziert EBT-Läufe und Guards auf ein Prüf-Dict."""
    try:
        trace = EBT(
            target=target,
            pre=pre,
            post=post,
            expect=expect,
            reporter=None,
        ).run()
        return {
            "evaluation": trace.evaluation,
            "trace_count": len(trace.traces),
            "error_type": None,
        }
    except (ValueError, TypeError) as exc:
        return {
            "evaluation": False,
            "trace_count": 0,
            "error_type": type(exc).__name__,
        }


def test_post_quantor_all_requires_every_post_predicate() -> None:
    """Prüft, dass post mit quantor='all' alle Ziel-Prädikate gleichzeitig erzwingt."""
    contract_result = EBT(
        target=_run_ebt_projection,
        pre=WorldState(
            args=(
                _target_normalize,
                WorldState(args=("  Cubie  ",)),
                {
                    "quantor": "all",
                    "states": [
                        WorldState(returns=str),
                        WorldState(returns=lambda val: val == "cubie"),
                        WorldState(returns=lambda val: len(val) == 5),
                    ],
                },
            )
        ),
        post=WorldState(
            returns={
                "evaluation": True,
                "trace_count": 3,
                "error_type": None,
            }
        ),
        reporter=None,
    ).run()
    assert contract_result.evaluation is True


@pytest.mark.parametrize(
    "bad_config",
    [
        {"quantor": "any", "states": [WorldState(args=("a",))]},
        {"quantor": "all"},
        {"quantor": "exists", "states": []},
        {"quantor": 123, "states": [WorldState(args=("a",))]},
    ],
)
def test_guard_rejects_invalid_quantor_declarations(bad_config: dict[str, Any]) -> None:
    """Prüft STATE-GUARDs gegen ungültige Quantor-Werte, fehlende Keys und leere Mengen."""
    guard_check = EBT(
        target=_run_ebt_projection,
        pre=WorldState(
            args=(
                _target_normalize,
                bad_config,
                WorldState(returns="a"),
            )
        ),
        post=WorldState(
            returns=lambda res: res["evaluation"] is False
            and res["error_type"] in {"ValueError", "TypeError"}
        ),
        reporter=None,
    ).run()
    assert guard_check.evaluation is True

```

---

## 5. Abnahmekriterien (Definition of Done)

Der Auftrag gilt als vollständig abgeschlossen, wenn:

1. **Datei erstellt:** `tests/tests_ebt/test_ebt_quantor_declaration.py` deckt alle 14 spezifizierten Test-Cases aus den Gruppen **A bis E** ab.
2. **Dynamische Verifikation (`pytest`):** `pytest tests/tests_ebt/test_ebt_quantor_declaration.py` läuft ohne Fehler, Warnungen oder geskippte Tests grün durch.
3. **Statische & Stil-Verifikation:** Alle Cubie-Linter (`MyPy`, `Pylint`, `AstLinter`/`CstLinter`) laufen ohne Beanstandungen über das neue Modul.


4. **Doku-Kohärenz (`DocEnsurance`):** Falls parallel Beispiele in `docs/GUIDE_EBT-Usage-Pattern.md` oder `docs/GUIDE_Contract-Semantics.md` ergänzt werden, bestehen diese den `DocEnsurance`-Lauf.