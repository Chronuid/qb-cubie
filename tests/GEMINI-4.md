<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Neon" effort="High" -->
# Arbeitspaket: TGD Green-Phase — Reparatur & Härtung des Cubie-Core

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini-4-Neon
- **Reasoning-Effort:** High
- **Analysedatum:** 19. November 2026, ~ 22:00 (CET)
- **Synthesebasis:** `tests/ANALYSIS.md`, `tests/HYPOTHESIS.md`, `tests/GEMINI-1.md`, `tests/GEMINI-2.md`, `tests/GEMINI-3.md`, `src/qb_cubie/protocols.py`, `src/qb_cubie/ebt.py`, `src/qb_cubie/reporter.py`, `src/qb_cubie/arenas/tempfs.py`, `src/qb_cubie/arenas/pyvenv.py`, `tests/tests_ebt/test_ebt_quantor_declaration.py`, `tests/tests_ebt/test_ebt_state_validation.py`, `tests/tests_ebt/test_ebt_run_isolation.py`, `tests/tests_ebt/test_ebt_contract_mutation.py`, `tests/test_lint.py`, `tests/test_styleguide.py`, `docs/GUIDE_Expect-Flags.md`, `docs/GUIDE_EBT-Usage-Pattern.md`, aktueller Pytest-Gesamtlauf (`32 failed, 1724 passed, 11 skipped`)
- **Stand**: qb-cubie (v0.0.8)
- **Git-Log**:

```text
commit 905e0a062d38098b99ab2f56afce2113c59edf32 (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Thu Nov 19 21:55:24 2026 +0100

    Tried to repair the test-suite.
```

---

---

<!-- /qb:frame -->

# Operationsfähiges Arbeitspaket: Reparatur & Härtung des Cubie-Core (`qb-cubie`, TGD Green-Phase)

## 1. Auftrag, Ausgangslage & TGD-Leitplanken

### 1.1 Ziel der TGD Green-Phase

In der abgeschlossenen TGD Red-Phase (`905e0a06`) wurde die Test-Suite von `qb-cubie` auf reine Quantoren-Semantik umgestellt und um 5 neue Guard- und Lebenszyklus-Verträge in `tests/tests_ebt/test_ebt_quantor_declaration.py` ergänzt. Ziel dieser **TGD Green-Phase** ist die **operationsfähige Reparatur des Quellcodes in `src/qb_cubie/`**, sodass:

1. `EBT.pre` standardmäßig als **reiner Allquantor (`"all"`)** und `EBT.post` standardmäßig als **reiner Existenzquantor (`"exists"`)** arbeitet — ohne implizite Quantor-Überschreibung durch `WorldState.expect=False`.
2. `evaluate_step_logic()` in `src/qb_cubie/protocols.py` von der historischen $Q^+/Q^-$-Partitionierung und dem *Vacuous-True*-Zweig unter `"exists"` befreit wird.
3. Alle neuen **`STATE-GUARD`s** für `WorldState.expect` und `EBT.expect` (striktes `bool`, Verbot von `expect=False` in `pre` und unter `post_quantor="exists"`) vor jeder Target-Ausführung greifen — sowohl bei Konstruktion als auch nach In-Place-Mutation vor einem Zweitlauf.
4. Der **Sticky-Quantor-Bug** bei Attribut-Neuzuweisung von `case.pre` und `case.post` behoben wird, während wiederholte `.run()`-Aufrufe ohne Neuzuweisung sowie In-Place-Listenmutationen den explizit deklarierten Quantor bewahren.
5. Alle **32 aktuell roten Test-Items** in `tests/tests_ebt/test_ebt_quantor_declaration.py` ohne Änderung am Testcode auf **`PASSED`** springen, ohne Regressionen in den übrigen 1724 Tests oder den Code-Metrik-/Lint-Gates (`test_lint.py`, `test_styleguide.py` Code-Checks) zu verursachen.

---

### 1.2 Verbindliche Regel zum Umgang mit der Test-Suite (Hinterfragen JA, Ändern NEIN!)

> [!CAUTION]
> **Strikter Dateischutz auf `tests/**/*.py` & aktives Hinterfragungs-Mandat:**
> 1. **Die Test-Suite darf während der Umsetzung NICHT geändert werden.** Es werden in dieser Phase keinerlei bestehende `.py`-Dateien unter `tests/` editiert, abgeschwächt, übersprungen (`skip`/`xfail`) oder umgangen.
> 2. **Die Test-Suite darf und SOLL unterwegs kritisch hinterfragt werden.** Die aktuelle Test-Suite sollte grundsätzlich konsistent und erfüllbar sein — es ist jedoch nicht ausgeschlossen, dass bei der Erstellung der Red-Phase (`905e0a06`) oder bei einer Vertragsannahme zuvor ein Denkfehler, eine Unschärfe oder ein Widerspruch entstanden ist.
> 3. **Eskalationspflicht über einen Bericht statt Silent-Edit:** Wenn du während der Reparatur von `src/qb_cubie/` begründet glaubst, dass in der Test-Suite etwas fachlich, typbezogen oder logisch **nicht stimmt** (z. B. sich widersprechende Tests, fehlerhafte Exception-Typen, widersprüchliche Lebenszyklus-Annahmen oder unlösbare Meta-Gate-Konflikte), **ändere die Testdatei nicht**, sondern lege stattdessen einen strukturierten Befundbericht unter **`tests/GREEN_AUDIT.md`** an (mit `CUBIE_DOC_FRAME_2`-Provenance-Head, exakter Testdatei + Zeilennummer, technischer Begründung, Reproduktionsbeleg und konkretem Klärungsvorschlag) und berichte dem Nutzer.

---

### 1.3 Vollständige Diagnose der aktuellen Test-Suite (Baseline auf `905e0a06`)

Ausgangsstand aus dem Gesamtlauf der Test-Suite:
**`32 failed, 1724 passed, 11 skipped, 6 warnings in 423.65s`**

Alle 32 Fehlschläge stammen exakt aus den 5 neuen Red-Phase-Testfunktionen in `tests/tests_ebt/test_ebt_quantor_declaration.py` (Zeilen 718–982):

| Cluster | Testfunktion (`test_ebt_quantor_declaration.py`) | Anzahl `FAILED` | Aktuelles Fehlerbild | Kernursache im Quellcode (`src/qb_cubie/`) | Zugeordnetes AP |
| :---: | :--- | :---: | :--- | :--- | :---: |
| **F1** | `test_guard_rejects_negative_worldstate_under_post_exists` (Z. 718–773) | **16** | `DID NOT RAISE ValueError` | `EBT._configure_states()` / `_arrange()` prüfen nicht, ob `self.post` bei `post_quantor == "exists"` einen Zustand mit `expect is False` enthält (weder bei Konstruktion noch nach In-Place-Mutation `mutable_state.expect = False`). | **AP 2.3** |
| **F2** | `test_guard_rejects_negative_worldstate_in_pre` (Z. 775–821) | **8** | `DID NOT RAISE ValueError` | `EBT._configure_states()` / `_arrange()` ignorieren `pre[i].expect = False` stillschweigend in allen 4 Strukturformen und nach Mutation. | **AP 2.3** |
| **F3** | `test_guard_rejects_non_bool_expect_on_worldstate_and_ebt` (Z. 824–876) | **5** | `DID NOT RAISE TypeError` | `WorldState.expect` (`protocols.py:73`) ist `Optional[bool] = True` ohne Laufzeitprüfung; `EBT.expect` (`ebt.py:133`) wird weder bei Konstruktion noch in `_arrange()` strikt auf `bool` (`type(val) is bool`) geprüft (`None`, `1`, `0`, `"true"`, `[]` laufen durch). | **AP 1.1, AP 1.2, AP 2.1, AP 2.3** |
| **F4** | `test_evaluate_step_logic_enforces_pure_quantor_invariants` (Z. 879–914) | **1** | `AssertionError: assert True is False` | `evaluate_step_logic()` (`protocols.py:129-140`) partitioniert nach `positives`/`negatives`, setzt `if not positives: satisfies_pos = True` (`[]` unter `"exists"` liefert `True` statt `False`) und weist `expect=False` unter `post_quantor="exists"` nicht mit `ValueError("STATE-GUARD: ...")` ab. | **AP 1.3** |
| **F5** | `test_sticky_quantor_resets_on_reassignment_and_persists_on_rerun` (Z. 916–982) | **2** | `AssertionError: assert 'all' == 'exists'` | `EBT._arrange()` (`ebt.py:170-171`) übergibt `self.pre_quantor` bzw. `self.post_quantor` pauschal als `default_quantor` an `_parse_state_config()`, auch wenn `case.post` oder `case.pre` zuvor neu zugewiesen wurde (`post_quantor` bleibt auf `"all"` kleben statt auf `"exists"` zurückzuspringen; symmetrisch für `pre`). | **AP 2.2** |
| **Summe** | **5 Testfunktionen** | **32** | — | **2 Kernmodule betroffen (`protocols.py`, `ebt.py`)** | **AP 1 & AP 2** |

---

### 1.4 Scope-Übersicht & wichtige Kopplung zu `DocEnsurance` (`docs/`)

| Bereich | Dateien | Rolle in dieser TGD Green-Phase |
| :--- | :--- | :--- |
| **Primär-Scope (Änderung)** | `src/qb_cubie/protocols.py` | Typ-Guard `validate_bool_expect`, Härtung `WorldState.expect`, reine Quantor-Auswertung in `evaluate_step_logic()`. |
| **Primär-Scope (Änderung)** | `src/qb_cubie/ebt.py` | Strikte `expect`-Prüfung für `EBT` & `WorldState`, `STATE-GUARD`s für `pre` und `post="exists"`, Sticky-Quantor-Fix über nicht-validierende Property-Setter. |
| **Prüf-Scope (Read-Only / Verifikation)** | `src/qb_cubie/reporter.py`, `src/qb_cubie/arenas/tempfs.py`, `src/qb_cubie/arenas/pyvenv.py` | Schnittstellen- und Typkompatibilität gegen `WorldState.expect: bool` und neue `evaluate_step_logic()` prüfen (keine Logikänderung erwartet; max. einzeiliger Docstring-Abgleich). |
| **Dateischutz (NICHT ändern!)** | `tests/**/*.py` | Tabu für Edits; nur ausführen und ggf. kritisch in `tests/GREEN_AUDIT.md` auditieren. |
| **Nachgelagerter Docs-Sync (Achtung: `test_docs_code_examples`!)** | `docs/GUIDE_Expect-Flags.md`, `docs/GUIDE_EBT-Usage-Pattern.md` *(sowie weitere Guides aus `ANALYSIS.md` Teil 3)* | **Wichtig:** `tests/test_styleguide.py::test_docs_code_examples` führt via `DocEnsurance` 4 Live-Python-Snippets in `docs/` gegen den Core aus, die noch das alte `post=[..., WorldState(..., expect=False)]`-Muster ohne `"quantor": "all"` verwenden (Details in **Abschnitt 5.3**). Sobald der neue `STATE-GUARD` aktiv ist, schlägt exakt dieser eine Doc-Test an diesen 4 Alt-Snippets an — das ist **kein Core-Bug**, sondern der erwartete Auslöser für den nachfolgenden Docs-Sync-Schritt! |

---

## 2. Harte Qualitäts-, Styleguide- & Lint-Leitplanken für `src/qb_cubie/`

Bevor eine einzige Zeile in `src/qb_cubie/` geändert wird, müssen diese **4 automatisch getesteten Repository-Grenzen** aus `tests/test_styleguide.py` und `tests/test_lint.py` bei jedem Designschritt mitgedacht werden:

1. **Modullänge (`tests/test_styleguide.py::test_module_size`):**
   - Maximale Dateilänge pro Modul in `src/`: **`777` Zeilen** (`MODULE_LIMIT = 777`).
   - Aktueller Stand:
     - `src/qb_cubie/protocols.py`: **242 Zeilen** (535 Zeilen Spielraum).
     - `src/qb_cubie/ebt.py`: **701 Zeilen** (**nur noch 76 Zeilen Spielraum!**).
   - **Konsequenz:** Halte neue Logik in `ebt.py` strikt kompakt (Ziel: $\le 750$ Zeilen) und platziere wiederverwendbare Validierungshelfer (wie `validate_bool_expect`) in `src/qb_cubie/protocols.py`.
2. **Funktionslänge (`tests/test_styleguide.py::test_function_size`):**
   - Maximal **`12` physische Codezeilen im Funktionskörper** (`FUNCTION_LIMIT = 12`, ohne Signatur, einzeiligen Docstring, Kommentare und Leerzeilen — mehrzeilige Statements zählen aber für jede belegte Zeile!).
   - Achte insbesondere auf bereits volle Methoden:
     - `WorldState.validate_exception_contract()` (`protocols.py:80-91`): bereits **10 Body-Zeilen** $\rightarrow$ **nicht** aufblähen, stattdessen eine eigene Methode `validate_expect()` ergänzen!
     - `EBT._configure_states()` (`ebt.py:125-138`): bereits **9 Body-Zeilen** $\rightarrow$ kompakt halten!
     - `EBT._arrange()` (`ebt.py:166-176`): bereits **10 Body-Zeilen** $\rightarrow$ Validierung in kleine Hilfsmethoden (`_arrange_states()`, `_validate_state_expects()`) auslagern!
3. **Einzeilige Docstrings (`tests/test_styleguide.py::test_docstrings`):**
   - Jeder Modul-, Klassen- und Funktions-Docstring in `src/` muss **exakt einzeilig** sein (`len(doc.splitlines()) == 1`).
4. **Statische Analyse & `mypy --warn-unreachable`-Falle (`tests/test_lint.py::test_src_lint`):**
   - `tests/test_lint.py` prüft alle Dateien in `src/` mit:
     - `ruff check --isolated --no-cache --select=E4,E7,E9,F`
     - `pylint --disable=all --enable=unreachable`
     - `mypy --warn-unreachable --check-untyped-defs`
   - **Kritische Falle bei `mypy --warn-unreachable`:**
     - Wenn ein Parameter oder Attribut statisch als `bool` typisiert ist (z. B. `self.expect: bool`) und direkt `if not isinstance(self.expect, bool): raise TypeError(...)` geschrieben wird, meldet `mypy --warn-unreachable` **`Statement is unreachable [unreachable]`**!
     - Dasselbe gilt bei `post_quantor: Quantor` (`Literal["all", "exists"]`), wenn nach Abdeckung beider Literale ein `else: raise ValueError(...)` folgt.
     - **Saubere Lösung:** `validate_bool_expect(value: Any, field: str) -> bool` nimmt explizit **`value: Any`** entgegen. Damit ist der `TypeError`-Zweig für `mypy` erreichbar, schützt zur Laufzeit zuverlässig gegen `None`, `int` (`1`/`0`), `str`, `list` usw., und liefert statisch den verengten Rückgabetyp `bool`.

---

## 3. Arbeitspaket 1 (AP 1): Reparatur von `src/qb_cubie/protocols.py`

### AP 1.1: Zentrale Typ-Validierung `validate_bool_expect`

Ergänze in `src/qb_cubie/protocols.py` (oberhalb von `WorldState` oder direkt vor `evaluate_step_logic`) eine kleine, wiederverwendbare Hilfsfunktion:

```python
def validate_bool_expect(value: Any, field: str) -> bool:
    """Validate that an expect flag is strictly a bool, rejecting int, None, and other types."""
    if type(value) is not bool:
        raise TypeError(
            f"STATE-GUARD: {field} must be a bool (True or False); received {type(value).__name__}."
        )
    return value
```

**Begründung & Kantenfall-Prüfung:**
- In Python gilt `issubclass(bool, int) is True`, `bool` selbst ist aber nicht ableitbar. `type(value) is not bool` (äquivalent zu `not isinstance(value, bool)`) lässt ausschließlich `True` und `False` passieren und weist `None`, `1`, `0`, `"true"`, `[]` zuverlässig mit `TypeError("STATE-GUARD: ...")` ab.
- Nimmt `value: Any` $\rightarrow$ kein `[unreachable]` in `mypy --warn-unreachable`.
- Body-Länge: **5 physische Zeilen** ($\le 12$).

---

### AP 1.2: Härtung von `WorldState` (`src/qb_cubie/protocols.py:59-92`)

1. **Feld-Typannotation (Zeile 73):**
   Ändere:
   ```python
   expect: Optional[bool] = True
   ```
   in:
   ```python
   expect: bool = True
   ```
2. **Konstruktor-Validierung (`__post_init__`, Zeilen 77–78):**
   ```python
   def __post_init__(self) -> None:
       self.validate_expect()
       self.validate_exception_contract()

   def validate_expect(self) -> None:
       """Validate that WorldState.expect is strictly a bool (also callable after mutation)."""
       validate_bool_expect(self.expect, "WorldState.expect")
   ```
   *(Hinweis: `validate_exception_contract()` bleibt mit seinen 10 Body-Zeilen unangetastet und stabil unter `FUNCTION_LIMIT = 12`, und seine bestehende Signatur/Semantik bricht für keinen Aufrufer.)*

**Wichtige Prüfungen gegen die Test-Suite:**
- `test_guard_rejects_non_bool_expect_on_worldstate_and_ebt` (Z. 836–844): `bad_ws = WorldState(returns=42, expect=bad_expect)` steht **innerhalb** von `with pytest.raises(TypeError, match="STATE-GUARD"):` $\rightarrow$ schlägt sofort im `__post_init__` sauber mit `TypeError("STATE-GUARD: ...")` an, bevor `EBT` überhaupt instanziiert oder das Target aufgerufen wird.
- Derselbe Test (Z. 867–870): `ws.expect = bad_expect` steht **außerhalb** von `with pytest.raises(...)`, erst `case.run()` steht innerhalb $\rightarrow$ `WorldState.expect` darf **keinen** sofort validierenden `@property`-Setter erhalten, sondern wird in `EBT._arrange()` über `state.validate_expect()` revalidiert!
- `test_ebt_run_isolation.py:186` (`post.expect = False` nach `.run()`) bleibt vollständig unberührt.

---

### AP 1.3: Bereinigung von `evaluate_step_logic()` (`src/qb_cubie/protocols.py:129-140`)

Ersetze die bestehende $Q^+/Q^-$-Partitionierung in `src/qb_cubie/protocols.py:129-140`:

```python
# ALT (fehlerhaft: Q+/Q--Split & Vacuous-True):
def evaluate_step_logic(traces: List["EvaluationTrace"], post_quantor: Quantor = "exists") -> bool:
    """Evaluate one step's success from positive and negative post-state traces."""
    positives = [t for t in traces if t.post.expect]
    negatives = [t for t in traces if not t.post.expect]
    violates_neg = any(t.evaluation for t in negatives)
    if not positives:
        satisfies_pos = True
    elif post_quantor == "all":
        satisfies_pos = all(t.evaluation for t in positives)
    else:
        satisfies_pos = any(t.evaluation for t in positives)
    return satisfies_pos and not violates_neg
```

durch die reine, einheitliche Quantor-Auswertung:

```python
def evaluate_step_logic(traces: List["EvaluationTrace"], post_quantor: Quantor = "exists") -> bool:
    """Evaluate one step's traces purely under the declared post_quantor."""
    results: list[bool] = []
    for trace in traces:
        expected = validate_bool_expect(trace.post.expect, "post.expect")
        if post_quantor == "exists" and not expected:
            raise ValueError(
                "STATE-GUARD: WorldState(expect=False) is forbidden under post_quantor='exists'; "
                "use post={'quantor': 'all', 'states': [...]}."
            )
        results.append(trace.evaluation if expected else not trace.evaluation)
    return all(results) if post_quantor == "all" else any(results)
```

**Verifikation aller Invarianten (Cluster F4):**
- `evaluate_step_logic([], "exists")` $\rightarrow$ `any([])` $\rightarrow$ **`False`** (beseitigt Vacuous-True!).
- `evaluate_step_logic([], "all")` $\rightarrow$ `all([])` $\rightarrow$ **`True`** (mathematisch reine Allquantifizierung über die leere Menge; leere `post`-Listen in realen `EBT`-Läufen werden bereits in `_validate_states` per `ValueError` blockiert).
- `evaluate_step_logic([pos_hit, neg_hit], "all")` $\rightarrow$ `all([True, False])` $\rightarrow$ **`False`**.
- `evaluate_step_logic([pos_hit, neg_miss], "all")` $\rightarrow$ `all([True, True])` $\rightarrow$ **`True`**.
- `evaluate_step_logic([pos_hit, neg_hit], "exists")` $\rightarrow$ **`ValueError("STATE-GUARD: ...")`**.
- Mutiertes `trace.post.expect = None` / `1` $\rightarrow$ **`TypeError("STATE-GUARD: ...")`**.
- Body-Länge: **9 physische Zeilen** ($\le 12$), 0 `mypy [unreachable]`-Warnungen!

---

## 4. Arbeitspaket 2 (AP 2): Reparatur von `src/qb_cubie/ebt.py`

### AP 2.1: Import & strikte Validierung von `EBT.expect`

1. Importiere `validate_bool_expect` aus `.protocols` in Zeile 14 von `src/qb_cubie/ebt.py`.
2. In `EBT._configure_states()` (Zeile 133):
   ```python
   self.expect = validate_bool_expect(expect, "EBT.expect")
   ```
3. In `EBT._arrange()` (vor `_validate()`):
   ```python
   validate_bool_expect(self.expect, "EBT.expect")
   ```

> [!WARNING]
> **Kein eager validierender `@expect.setter`!**
> In `tests/tests_ebt/test_ebt_quantor_declaration.py:873-875` steht:
> ```python
> case.expect = bad_expect
> with pytest.raises(TypeError, match="STATE-GUARD"):
>     case.run()
> ```
> Die Zuweisung `case.expect = bad_expect` erfolgt **außerhalb** von `pytest.raises(...)`! Deshalb darf `self.expect` ein normales Attribut bleiben, das bei Konstruktion (`_configure_states`) und vor jedem Lauf (`_arrange`) validiert wird.

---

### AP 2.2: Sticky-Quantor-Fix für `case.pre` und `case.post` (Cluster F5)

#### Analyse der Falle (warum zwei nahe liegende Ansätze brechen!)

1. **Warum ein sofort validierender `@pre.setter` / `@post.setter` BÖSE bricht:**
   In `tests/tests_ebt/test_ebt_state_validation.py:91-95` und `tests/tests_ebt/test_ebt_quantor_declaration.py:710-714` steht:
   ```python
   setattr(case, field, invalid_cfg)
   with pytest.raises(error_type):
       case.run()
   assert not marker.exists()
   assert case.run_trace is None
   ```
   `setattr(case, field, invalid_cfg)` steht **außerhalb** von `pytest.raises`, und `assert case.run_trace is None` verlangt, dass `case.run()` bis `_start_run()` (Reset von `self.run_trace = None`) und dann `_arrange()` gelangt! Ein eager validierender Setter würde die Tests sofort zum Absturz bringen.
2. **Warum reines `is`-Identitäts-Tracking (`self.post is self._post_ref`) eine subtile Lücke hat:**
   Wird eine Liste erst über `states = [ws1, ws2]; case = EBT(..., post={"quantor": "all", "states": states})` übergeben und danach per `case.post = states` (ohne Dict-Wrapper, aber dasselbe Listenobjekt!) neu zugewiesen, würde `self.post is self._post_ref` weiterhin `True` liefern und den Reset verfehlen.

#### Empfohlene, lückenlose Lösung: Nicht-validierende `@property`-Setter mit Reassignment-Flag

Ergänze in `EBT` zwei schlanke, **nicht-validierende** Properties für `pre` und `post`:

```python
    @property
    def pre(self) -> list[WorldState]:
        """Return the configured pre-states."""
        return self._pre

    @pre.setter
    def pre(self, value: StateInput) -> None:
        """Store reassigned pre-states so the next arrange resets non-wrapper quantors."""
        self._pre = value
        self._pre_reassigned = True

    @property
    def post(self) -> list[WorldState]:
        """Return the configured post-states."""
        return self._post

    @post.setter
    def post(self, value: StateInput) -> None:
        """Store reassigned post-states so the next arrange resets non-wrapper quantors."""
        self._post = value
        self._post_reassigned = True
```

*(Hinweis zur Typisierung: Deklariere in `_configure_states` die internen Felder explizit als `self._pre: Any` und `self._post: Any`, damit `mypy` sowohl das Speichern beliebiger `StateInput`-Rohwerte im Setter als auch die Rückgabe als `list[WorldState]` im Getter fehlerfrei prüft und bestehende Aufrufe wie `self.pre`, `enumerate(self.pre)`, `case.post.append(...)` sauber typisiert bleiben.)*

**Zusammenspiel in `_configure_states()` und `_arrange()`:**

1. In `_configure_states()`:
   ```python
   self._pre: Any = None
   self._post: Any = None
   self._pre_reassigned = False
   self._post_reassigned = False
   self._pre, self.pre_quantor = self._parse_state_config(pre, "pre", "all")
   self._post, self.post_quantor = self._parse_state_config(post, "post", "exists")
   ```
   *(Wichtig: Zuweisung direkt an `self._pre` / `self._post`, nicht über den Setter — so bleibt `_reassigned == False`!)*

2. In `_arrange()` (ausgelagert in eine schlanke Hilfsmethode `_arrange_states()`, um `FUNCTION_LIMIT = 12` einzuhalten):
   ```python
   def _arrange_states(self) -> None:
       """Parse, reset reassigned quantors, and validate pre/post state contracts."""
       pre_default: Quantor = "all" if self._pre_reassigned else self.pre_quantor
       post_default: Quantor = "exists" if self._post_reassigned else self.post_quantor
       self._pre, self.pre_quantor = self._parse_state_config(self._pre, "pre", pre_default)
       self._post, self.post_quantor = self._parse_state_config(self._post, "post", post_default)
       self._pre_reassigned = False
       self._post_reassigned = False
   ```

**Prüfung aller 6 Lebenszyklus-Szenarien:**

| Szenario | Was passiert mit `_reassigned`? | Ergebnis (`pre_quantor` / `post_quantor`) |
| :--- | :--- | :--- |
| **1. Lauf 1 nach `__init__`** mit `post={"quantor": "all", ...}` | `_post_reassigned == False` | `post_quantor == "all"` |
| **2. Lauf 2 ohne Neuzuweisung** (`case.run()` erneut, ggf. nur `case.pre = ...` geändert) | `_post_reassigned == False` (`_pre_reassigned == True`) | `post_quantor` bleibt **`"all"`**; `pre_quantor` springt auf **`"all"`** |
| **3. In-Place-Listenmutation** (`case.post.append(...)`) | Ruft nur `@post`-Getter auf, **nicht** den Setter $\rightarrow$ `_post_reassigned == False` | `post_quantor` bleibt **`"all"`**; neue Elemente werden in `_validate_states` revalidiert |
| **4. Attribut-Neuzuweisung ohne Wrapper** (`case.post = [...]`, `case.post = WorldState(...)`, `case.post = None`, oder `case.pre = [...]`) | Setter setzt `_post_reassigned = True` bzw. `_pre_reassigned = True` | `post_quantor` springt auf **`"exists"`**; `pre_quantor` springt auf **`"all"`** |
| **5. Attribut-Neuzuweisung mit neuem Wrapper** (`case.post = {"quantor": "all", "states": [...]}`) | Setter setzt `_post_reassigned = True`; `_parse_state_config` liest Dict-Quantor direkt | `post_quantor == "all"`, danach `_post_reassigned = False` |
| **6. Ungültige Neuzuweisung** (`case.post = []`, `case.post = {"quantor": "invalid", ...}`) | Setter wirft **nicht**; erst `case.run()` setzt `run_trace = None` und `_parse_state_config` wirft `ValueError`/`TypeError` (Flags bleiben `True` für Folgeläufe) | Exakt kompatibel mit `test_changed_lists_are_revalidated` & `test_changed_quantor_wrapper_is_revalidated`! |

---

### AP 2.3: `STATE-GUARD`s für `WorldState.expect` in `pre` und unter `post="exists"` (Cluster F1, F2, F3)

Ergänze in `EBT` eine kompakte statische Validierungsmethode `_validate_state_expects()` und rufe sie **am Ende von `_parse_state_config()`** (damit Konstruktion **und** `_arrange()` denselben Guard teilen!):

```python
    @staticmethod
    def _validate_state_expects(states: list[WorldState], field: str, quantor: Quantor) -> None:
        """Enforce bool expect flags and reject expect=False in pre or under post='exists'."""
        __tracebackhide__ = True
        for index, state in enumerate(states):
            state.validate_expect()
            if not state.expect and (field == "pre" or quantor == "exists"):
                context = "in pre" if field == "pre" else "under post_quantor='exists'"
                raise ValueError(
                    f"STATE-GUARD: {field}[{index}].expect=False is forbidden {context}; "
                    "use WorldState(expect=True) or post={'quantor': 'all', 'states': [...]}."
                )
```

**Integration in `_parse_state_config()` (`src/qb_cubie/ebt.py:523-535`):**

```python
    @staticmethod
    def _parse_state_config(
        raw_value: Any, field: str, default_quantor: Quantor,
    ) -> tuple[list[WorldState], Quantor]:
        """Normalize and validate a WorldState, list, None, or quantor wrapper dict."""
        __tracebackhide__ = True
        if raw_value is None:
            states, quantor = [WorldState()], default_quantor
        elif isinstance(raw_value, WorldState):
            states, quantor = [raw_value], default_quantor
        elif isinstance(raw_value, dict):
            states, quantor = EBT._parse_quantor_wrapper(raw_value, field)
        else:
            EBT._validate_states(raw_value, field)
            states, quantor = raw_value, default_quantor
        EBT._validate_state_expects(states, field, quantor)
        return states, quantor
```

**Zwei kritische Invarianten prüfen:**

1. **Reihenfolge `TypeError` vor `ValueError` (entscheidend!):**
   `state.validate_expect()` läuft **zuerst**. Dadurch wird ein mutiertes `ws.expect = None` oder `ws.expect = 0` in `pre` oder `post="exists"` immer sauber als **`TypeError("STATE-GUARD: ...")`** gemeldet — und niemals fälschlich über `if not state.expect:` als `ValueError`!
2. **Kein Target-Aufruf & saubere Zeilenbilanz:**
   - Weil `_parse_state_config()` sowohl in `_configure_states()` als auch in `_arrange()` (über `_arrange_states()`) läuft, schlagen sowohl Konstruktionsfehler als auch In-Place-Mutationen (`mutable_state.expect = False`, `mutable_pre.expect = False`, `ws.expect = bad_expect`) **vor** `_validate()` fehl (`assert not marker.exists()`).
   - **Body-Längen-Check (`FUNCTION_LIMIT = 12`):**
     - `_parse_state_config`: **11 Body-Zeilen** ($\le 12$)! *(Falls zu knapp: die 4 Zweige in `_extract_state_config` auslagern, dann je 6–8 Zeilen.)*
     - `_validate_state_expects`: **7 Body-Zeilen** ($\le 12$)!
     - `_arrange`: **8 Body-Zeilen** ($\le 12$):
       ```python
       def _arrange(self) -> None:
           """Validate all declared states before normalizing their filesystems."""
           __tracebackhide__ = True
           _validate_max_workers(self.max_workers)
           validate_bool_expect(self.expect, "EBT.expect")
           self._arrange_states()
           for state in (*self.pre, *self.post):
               state.validate_exception_contract()
           for state, fs in self._normalized_states():
               state.fs = fs
       ```
   - **Gesamt-Modullänge `src/qb_cubie/ebt.py` (`MODULE_LIMIT = 777`):**
     701 Zeilen Bestand + ~40 Zeilen netto $\approx$ **741 Zeilen** ($\le 777$, über 30 Zeilen Reserve!).

---

### AP 2.4: Schnittstellen-Gegenprüfung angrenzender Core-Module (Read-Only-Check)

Prüfe nach Abschluss von AP 1 und AP 2 die folgenden 3 Stellen auf volle Kompatibilität (keine Logikänderung erforderlich, nur Verifikation):

1. **`src/qb_cubie/reporter.py`:**
   - `PytestReporter._select_report_step()` (Z. 94–103) und `PytestReporter._evaluate_step_logic()` (Z. 115–118) delegieren direkt an `evaluate_step_logic()`.
   - `JsonReporter._state()` (Z. 304) schreibt `"expect": state.expect` (jetzt strikt `bool`).
   - Optional: Einzeilige Docstrings in `ebt.py:186`, `ebt.py:691` und `reporter.py:116` an die reine Quantor-Semantik anpassen (zwingend einzeilig belassen!).
2. **`src/qb_cubie/arenas/tempfs.py:98` & `src/qb_cubie/arenas/pyvenv.py:138`:**
   - Beide übergeben `expect=self._config_state.expect` beim Bau des Outcome-`WorldState`. Da `pre`-Zustände durch AP 2.3 garantiert `expect is True` (`bool`) haben, ist dies nun auch typseitig (`bool` statt `Optional[bool]`) 100 % sauber.

---

## 5. Arbeitspaket 3 (AP 3): Verifikations-, Audit- & Abnahmeprotokoll

Führe nach Umsetzung von AP 1 und AP 2 die folgenden **4 Verifikationsstufen** exakt in dieser Reihenfolge aus:

### Schritt 5.1: Zielgerichtete Green-Verifikation der 32 ehemals roten Tests

```bash
.venv/bin/python -m pytest -q tests/tests_ebt/test_ebt_quantor_declaration.py
```
- **Erwartetes Ergebnis:** **100 % `PASSED`** (`0 failed`) — alle **32** zuvor fehlgeschlagenen Items aus F1–F5 sind ohne Änderung an `tests/` grün!

---

### Schritt 5.2: Harte Core-Qualitäts- & Styleguide-Gates (`src/`-Metriken & Linter)

```bash
.venv/bin/python -m pytest -q tests/test_lint.py
.venv/bin/python -m pytest -q tests/test_styleguide.py -k "not test_docs_code_examples"
```
- **Erwartetes Ergebnis:** **100 % `PASSED`** (`0 failed`):
  - `test_src_lint[ruff]`, `test_src_lint[pylint]`, `test_src_lint[mypy]` (0 Fehler, insbesondere kein `[unreachable]`).
  - `test_module_size` (`ebt.py <= 777`, `protocols.py <= 777`), `test_function_size` (alle Funktionen/Methoden `<= 12` Body-Zeilen), `test_docstrings` (alle Docstrings exakt 1 Zeile).

---

### Schritt 5.3: Vollständige Regression-Suite & explizite Abgrenzung zu `test_docs_code_examples`

1. **Komplette Code- & Meta-Test-Suite (ohne den Doku-Runner `test_docs_code_examples`):**
   ```bash
   .venv/bin/python -m pytest -q -m "" -k "not test_docs_code_examples"
   ```
   *(Für schnelle Zwischenläufe vorab: `make test-ebt`, `make test-meta`, `make test-mp`, `make test-arena`.)*
   - **Erwartetes Ergebnis:** **`0 failed`** (alle EBT-, Arena-, Multiprocessing-, Linter-, Meta-Gate-1/2/3-, Service-, Reviewer-, Workflow- und Offline-Core-Tests laufen zu 100 % grün!).

2. **Isolierte Gegenprobe von `tests/test_styleguide.py::test_docs_code_examples` (`DocEnsurance`):**
   ```bash
   .venv/bin/python -m pytest -q tests/test_styleguide.py -k "test_docs_code_examples"
   ```
   - **Erwarteter Befund bei unverändertem `docs/`:**
     Dieser eine Test schlägt nach Aktivierung des neuen `STATE-GUARD`s **erwartungsgemäß rot** an, weil `DocEnsurance` genau **4 ausführbare Alt-Snippets in `docs/`** live gegen den Core ausführt, die noch `WorldState(..., expect=False)` ohne `"quantor": "all"` verwenden:
     1. `docs/GUIDE_Expect-Flags.md` (Z. 39–57): `post=[WorldState(returns=85), WorldState(returns=lambda value: value < 0, expect=False)]`
     2. `docs/GUIDE_Expect-Flags.md` (Z. 80–101): `post=[WorldState(returns=lambda value: value >= 0), WorldState(returns=-10, expect=False)]`
     3. `docs/GUIDE_Expect-Flags.md` (Z. 154–177): `post=WorldState(returns=-1, expect=False)` und `post=[WorldState(returns=int), WorldState(returns=-1, expect=False)]`
     4. `docs/GUIDE_EBT-Usage-Pattern.md` (Z. 147–169): `post=[WorldState(returns="OK"), WorldState(returns="WARN"), WorldState(returns="ERROR", expect=False)]`
   - **Wichtige Abgrenzung:**
     - **Kein Core-Defekt und kein Edit an `tests/test_styleguide.py`!** Prüfe in der Ausgabe von `test_docs_code_examples` lediglich, dass die gemeldeten Fehler ausschließlich auf diese 4 bekannten Alt-Snippets (mit dem neuen `ValueError: STATE-GUARD`) zurückzuführen sind und kein anderes Doku-Beispiel gebrochen wurde.
     - Die vollständige Synchronisation der Dokumentation (diese 4 Live-Snippets plus alle Text- und Tabellenkorrekturen aus `tests/ANALYSIS.md`, Teil 3) bildet das sauber getrennte Folge-Arbeitspaket (**Docs-Sync**), sofern der Nutzer nicht explizit eine direkte Mitbearbeitung von `docs/` anfordert.

---

### Schritt 5.4: Kritische Prüfliste zum Hinterfragen der Test-Suite (Eskalations-Protokoll)

Prüfe während und nach der Umsetzung aktiv folgende 5 Kontrollfragen gegen `tests/` — **ohne `tests/**/*.py` zu verändern**:

1. **Fehlertyp- und Meldungs-Konsistenz:** Erwarten zwei Tests für denselben ungültigen Zustand widersprüchliche Exception-Typen (`TypeError` vs. `ValueError`) oder sich ausschließende Regex-Matches (`match="STATE-GUARD"` vs. `match=field`)?
2. **Konstruktions- vs. Laufzeit-Validierung:** Erzeugt irgendein Bestands-Test ein ungültiges `EBT` oder `WorldState` außerhalb eines `pytest.raises`-Blocks in der Erwartung, dass der Fehler erst in `.run()` (oder erst nach einer Mutation) auftritt?
3. **Multiprocessing-Parität:** Verhalten sich `singleprocess` und `multiprocess` (inkl. `PickleProcessor` / `LokyProcessor`-Fallback bei Lambdas wie in `test_sticky_quantor_resets_on_reassignment_and_persists_on_rerun:940`) identisch, oder tritt ein Serialisierungs-/Transport-Effekt auf?
4. **Unentdeckte Alt-Tests mit implizitem `post="exists"` + `expect=False`:** Schlägt nach Aktivierung des Guards irgendein bislang grüner Test außerhalb von `test_docs_code_examples` (z. B. ein langsamer `slow`- oder Hypothesis-Test) unerwartet mit `ValueError: STATE-GUARD` fehl, weil er in der Red-Phase übersehen wurde?
5. **Semantische Schärfe der neuen Verträge:** Deckt ein neuer Test in `test_ebt_quantor_declaration.py` eine Forderung falsch oder widersprüchlich zu `GUIDE_Contract-Semantics.md` / dem Architekturziel (*reine Quantoren ohne `expect`-Überschreibung*) ab?

**Falls eine dieser 5 Fragen mit „JA“ beantwortet wird:**
- **STOPP vor jedem Eingriff in `tests/**/*.py`!**
- Erstelle stattdessen den Bericht **`tests/GREEN_AUDIT.md`** mit folgender Minimalstruktur:
  1. `CUBIE_DOC_FRAME_2`-Provenance-Head (inkl. aktuellem `git log -n 1` und Modell/Effort).
  2. **Betroffener Test:** Exakter Dateipfad, Funktionsname, Zeilennummer und exakter Pytest-Output.
  3. **Widerspruch / Verdacht:** Warum die Test-Annahme vermutlich fehlerhaft oder übersehen ist (inkl. Abgleich mit dem Core-Vertrag).
  4. **Handlungsoptionen:** Konkreter Korrekturvorschlag für die Test-Suite zur Freigabe durch den Nutzer.

---

## 6. Ausblick: Übergabepunkt nach Abschluss der Core-Green-Phase

Sobald alle 32 vormals roten Tests in `test_ebt_quantor_declaration.py` sowie alle Code-, Lint-, Meta- und Styleguide-Metrik-Tests grün sind (und ggf. keine offenen Eskalationen in `tests/GREEN_AUDIT.md` bestehen), schließt sich als finaler Schritt der **Docs-Sync** an:
- Aktualisierung der 4 ausführbaren Live-Snippets in `docs/GUIDE_Expect-Flags.md` und `docs/GUIDE_EBT-Usage-Pattern.md` sowie der in `tests/ANALYSIS.md` (Teil 3) identifizierten Spezifikationsabschnitte (`GUIDE_Contract-Semantics.md`, `GUIDE_Quantifiers.md`, `GUIDE_Quality-Assurance.md`, `GUIDE_Contract-Design.md`, `DEV-GUIDE_2-1_EBT-Class.md`, `DEV-GUIDE_2-2_WorldState-Class.md`, `README.md`).
- Abschluss-Signal: `make test-all` inklusive `tests/test_styleguide.py::test_docs_code_examples` läuft zu **100 % grün (`0 failed`)**.

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->

---

---

<div align="center">

![Cubie](../docs/.assets/cubie-small.png)

[↦ | Arena-Management | ↤](../docs/GUIDE_Arena-Management.md)  
[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../docs/GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../docs/GUIDE_Contract-Design.md)  
[↦ | Verbindliche Vertragssemantik | ↤](../docs/GUIDE_Contract-Semantics.md)  
[↦ | EBT-Nutzungsmuster | ↤](../docs/GUIDE_EBT-Usage-Pattern.md)  
[↦ | Example-Based Testing | ↤](../docs/GUIDE_Example-Based-Testing.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../docs/GUIDE_Expect-Flags.md)  
[↦ | Linter | ↤](../docs/GUIDE_Linter.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../docs/GUIDE_Quantifiers.md)  
[↦ | RBT-Nutzungsmuster | ↤](../docs/GUIDE_RBT-Usage-Pattern.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../docs/services/GUIDE_DocFrame.md)  

[↦ | Entwicklerübersicht & Internals | ↤](../docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Hintergrund & Essays | ↤](../docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
