<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Argon" effort="High" -->
# Analysis: Reperatur vom Cubie-Core

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini-4-Argon
- **Reasoning-Effort:** High
- **Analysedatum:** 19. November 2026, ~ 21:30 (CET)
- **Synthesebasis:** `tests/GEMINI-2.md`, `tests/GEMINI-1.md`, `tests/ANALYSIS.md`, `META_QUESTION.md`, `docs/GUIDE_Quality-Assurance.md`, `docs/GUIDE_Contract-Design.md`, `docs/GUIDE_Expect-Flags.md`, `docs/GUIDE_Quantifiers.md`, `docs/GUIDE_Contract-Semantics.md`, `docs/services/GUIDE_DocFrame.md`, `docs/feature-drafts/meta-qa/1/META_GATES.md`, `docs/feature-drafts/meta-qa/1/META_GATE_2.md`, `docs/feature-drafts/meta-qa/1/META_GATE_3.md`, `src/qb_cubie/ebt.py`, `src/qb_cubie/protocols.py`, `src/qb_cubie/reporter.py`, `tests/conftest.py`, `tests/test_lint.py`, `tests/test_styleguide.py`, `tests/test_offline_core.py`, `tests/tests_meta/test_gate_1.py`, `tests/tests_meta/test_gate_2.py`, `tests/tests_meta/test_gate_3.py`, `tests/tests_ebt/test_ebt_quantors.py`, `tests/tests_ebt/test_ebt_quantor_declaration.py`, `tests/tests_ebt/test_ebt_args_normalization.py`, `tests/tests_ebt/test_ebt_returns.py`, `tests/tests_ebt/test_ebt_return_reporting.py`, `tests/tests_ebt/test_ebt_exception_contracts.py`, `tests/tests_ebt/test_ebt_run_isolation.py`, `tests/tests_ebt/test_ebt_contract_mutation.py`, `tests/tests_ebt/test_ebt_persistent_reports.py`, `tests/tests_ebt/test_ebt_state_validation.py`, `tests/tests_arena/test_ebt_arena_mutation.py`
- **Stand**: qb-cubie (v0.0.8)
- **Git-Log**:

```text
commit db96ea4b404c7b462e350f9e0bc5b8335c4f4d82 (HEAD -> main, origin/main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Thu Nov 19 20:33:16 2026 +0100

    Found a critical bug. Analysed it. Gotta think about it.
```

---

---

<!-- /qb:frame -->

# Hypothesen-Dokument & Meta-QA-Audit zur Reparatur der Test-Suite (`qb-cubie`, TGD Red-Phase)

## Executive Summary & Leit-Hypothese ($H_0$)

1. **Bewertung der Grundrichtung des Arbeitspakets (`tests/GEMINI-2.md`):**
   - **Architektonisch korrekt:** Die Leitidee des Arbeitspakets setzt dein Ziel aus `GEMINI-1.md` und deiner Präzisierung in `GEMINI-2.md:256` (*„Man kann einfach sagen: `"quantor": "all"`, wenn ein expect-flag mit gezählt werden muss. Man muss also nur das automatische überschreiben durch den expect-flag rausnehmen und durch eine explizite Deklaration ersetzen.“*) konsistent um:
     - `EBT.pre` arbeitet standardmäßig als **reiner Allquantor (`"all"`)**.
     - `EBT.post` arbeitet standardmäßig als **reiner Existenzquantor (`"exists"`)**.
     - `WorldState(..., expect=False)` überschreibt niemals mehr heimlich den `post`-Quantor, sondern wird ausschließlich unter einem explizit deklarierten Allquantor (`post={"quantor": "all", "states": [...]}`) ausgewertet.
   - **Warum der zusätzliche `STATE-GUARD` gegen `WorldState(expect=False)` unter `post="exists"` zwingend erforderlich ist:**
     Würde man in `evaluate_step_logic()` (`src/qb_cubie/protocols.py:129-140`) *nur* die $Q^+/Q^-$-Partitionierung entfernen und `expect=False` ohne `STATE-GUARD` im Standard-Existenzquantor (`any`) zulassen, entstünden **unbedingte prädikatenlogische Tautologien** (z. B. $(x \in \mathbb{Z}) \lor (x \neq 99) \equiv \top$ für alle $x \in \text{Any}$), die niemals fehlschlagen können (formaler Nachweis in **Abschnitt 1.1**).

2. **Ergebnis des Meta-QA-Audits gegen das Arbeitspaket (`GEMINI-2.md`, Z. 1–225):**
   - Das Arbeitspaket identifiziert die **9 zu migrierenden Testdateien (21 Testfunktionen)** korrekt, enthält im Detail jedoch **8 kritische Widersprüche, fehlerhafte Alternativvorschläge und blinde Flecken**, die bei einer ungeprüften 1:1-Umsetzung entweder bestehende Assertions brechen, einen Selbst-Konflikt zwischen Arbeitspaket 2 und Meta-Gate 3 auslösen oder einen unreparierten `evaluate_step_logic()`-Mutanten im Core unentdeckt überleben lassen:

| # | Fundstelle im Arbeitspaket (`GEMINI-2.md`) | Meta-QA-Prüfmethode | Aufgedeckter Defekt / Widerspruch im Arbeitspaket |
| :-: | :--- | :--- | :--- |
| **1** | **AP 1.8** (`test_offline_core.py`, Z. 157) | **Konsistenz- & Assertions-Treue** | Die vorgeschlagene erste Option (`post=WorldState(returns=3)`) reduziert die Matrix von $2 \times 2$ auf $2 \times 1$ und **bricht sofort `assert len(trace.traces) == 4` (Z. 166)**. |
| **2** | **AP 1.9** (`test_ebt_arena_mutation.py`, Z. 165) | **Gegenproben- & Duplikat-Analyse** | Die Klammer-Alternative (*„ohne Doppel-Negation direkt mit positivem `WorldState(returns=True, arena=PyVenv(BASE_ARENA))`“*) ist mit `expect=True` ein 1:1-Duplikat von Z. 88 und schlägt mit `EBT(expect=False)` **rot fehl**, weil `target_generate_volatile_metadata` die Basis-Arena erfüllt. |
| **3** | **AP 1.1 & AP 1.6** (`test_ebt_quantors.py`, Z. 98; `test_ebt_contract_mutation.py`, Z. 141) | **Subsumtions- & Prüfziel-Treue** | Die Klammer-Alternativen (*„reiner `exists`-Vertrag ohne Verbote“* bzw. *„oder `EBT(..., expect=False)`“*) zerstören das jeweilige Prüfziel (Negativ-Filter an Intervallgrenzen bzw. Snapshot-Isolation von `WorldState.expect=False` gegen Laufzeit-Mutation). |
| **4** | **AP 1.2, 1.3 & 1.4** (`test_ebt_returns.py`, `test_ebt_exception_contracts.py`, `test_ebt_return_reporting.py`) | **Subsumtions- & Mutations-Analyse** ($Q_{\text{pos}} \implies \neg Q_{\text{neg}}$) | (a) In `test_negative_none_contract_rejects_none` und `test_forbidden_exception_rejects_matching_exception_message` stecken je **zwei** `EBT`-Aufrufe (`result` und `inverted`). (b) In `test_negative_none_contract_rejects_none` (`returns=int` bei `args=(None,)`) und `test_forbidden_falsy_return_reports_the_matching_value` (`returns="allowed"` bei Falsy-Inputs) scheitert bereits $Q_{\text{pos}}$ (`trace[0].evaluation == False`), sodass `all([False, ...])` selbst bei defektem `expect=False` falsch bleibt. |
| **5** | **AP 2** (`test_ebt_quantor_declaration.py`, Z. 171–186) | **Mutation Testing** (Überlebender Core-Mutant) | Unter `post="all"` ist die alte Formel $(\forall_{Q^+} m) \land \neg(\exists_{Q^-} m)$ nach De Morgan identisch zur neuen Formel $\forall_Q \text{sat}$; unter `post="exists"` blockiert der neue `STATE-GUARD` in `_arrange()` vorab. **Keiner der 4 Tests in AP 2 schlägt fehl, wenn `evaluate_step_logic()` in `protocols.py` überhaupt nicht repariert wird!** |
| **6** | **AP 2.3 & AP 2.4** (`test_ebt_quantor_declaration.py`, Z. 181–185) | **Äquivalenzklassen & Lebenszyklus-Symmetrie** | (a) AP 2.4 prüft den Sticky-Quantor-Reset nur für `case.post`, vergisst aber `case.pre` (Reset von `"exists"` auf `"all"`), Einzel-`WorldState`/`None`-Zuweisungen sowie die Gegenprobe: **zwei `.run()`-Aufrufe hintereinander OHNE Neuzuweisung** dürfen `post="all"` / `pre="exists"` nicht verlieren! (b) AP 2.2/2.3 vergessen In-Place-Mutationen (`ws.expect = False`/`None` zwischen zwei Läufen) sowie `expect=1`/`0` (`isinstance(1, int)` ist `True`, da `bool < int`!). |
| **7** | **AP 2.1/2.3 vs. AP 3.1** (`test_gate_3.py` vs. `test_ebt_quantor_declaration.py`, Z. 175, 194, 220) | **Wächter-Selbst-Sabotage** (Meta-Gate-Konflikt) | (a) Schreibst du in `test_ebt_quantor_declaration.py` literale `EBT`-Aufrufe mit `post=WorldState(..., expect=False)` oder `expect=None` (oder verbietet `test_gate_3.py` statisch jedes `expect=False` außerhalb von `"quantor": "all"`), **schlägt `test_gate_3.py` beim Repository-Scan über `tests/` auf `test_ebt_quantor_declaration.py` fehl**! (b) AP 3.1 nennt in `test_gate_3.py` nur Z. 177–178, übersieht aber **8 weitere Clean-Probes (Z. 180, 183–210)** und die `0pos/Kneg`-Invariante der 16 Fault-Probes. (c) AP 3.2 übersieht die veralteten Clean-/Fault-Probes in `test_gate_2.py` (Z. 167–168, 216) sowie neue Kalibrierungs-Probes gemäß **Meta-Gate 5**. |
| **8** | **Abschnitt 4** (Abnahmekriterien, Z. 220–223) | **Sammlungs- & Linter-Hygiene** (Meta-Gate 4 & 5) | Ein pauschales `ruff check tests/` meldet aktuell **19 Alt-Fehler** (darunter `I001` in `test_ebt_quantors.py:1` und `test_ebt_arena_mutation.py:1` sowie `F401` in `test_ebt_arena.py:16, 63`, wo `import pytest`/`import cowsay` **unentbehrliche Laufzeit-Arena-Sonden** sind!). `mypy` benötigt auf `test_ebt_returns.py:10` (`cloudpickle`) die Flag-Konfiguration aus `test_lint.py`. |

---

## Teil 1: Die Fragen der Meta-QA — Kritische Hinterfragung des Arbeitspakets

Gemäß der in [`META_QUESTION.md`](../META_QUESTION.md) und [`docs/feature-drafts/meta-qa/1/META_GATES.md`](../docs/feature-drafts/meta-qa/1/META_GATES.md) etablierten Methodik stellen wir sechs formale Meta-QA-Fragen an das Arbeitspaket aus [`tests/GEMINI-2.md`](./GEMINI-2.md).

---

### 1.1 Meta-QA-Frage 1 (Prädikatenlogische Konsistenz & Tautologie-Gefahr)

> **Prüffrage:** *„Reicht es aus, in `evaluate_step_logic()` das automatische Überschreiben des Quantors durch `expect=False` zu entfernen und die bestehenden Tests auf `post={"quantor": "all", ...}` umzustellen — oder warum darf `WorldState(expect=False)` unter `post="exists"` überhaupt nicht erst ausgeführt werden?“*

#### Formale Beweisführung

Sei $m(q, y) \in \{\top, \bot\}$ das rohe Vergleichsergebnis (`trace.evaluation`) eines `WorldState` $q$ gegen das beobachtete Ergebnis $y$, und sei die Einzelerfüllung eines Zustands definiert als:

$$\text{sat}(q, y) := \begin{cases} m(q, y) & \text{falls } q.\text{expect} = \top \\ \neg m(q, y) & \text{falls } q.\text{expect} = \bot \end{cases}$$

Wenn `evaluate_step_logic()` den deklarierten Quantor strikt rein ohne $Q^+/Q^-$-Sonderbehandlung auswertet, gilt:

$$\text{step\_ok}_{\text{all}}(y) = \forall q \in Q : \text{sat}(q, y), \qquad \text{step\_ok}_{\text{exists}}(y) = \exists q \in Q : \text{sat}(q, y)$$

Betrachten wir nun, was unter dem Standard-Existenzquantor ($\text{step\_ok}_{\text{exists}}$, logisches `OR`) passiert, sobald mindestens ein Zustand $q^- \in Q$ mit `expect=False` ($\text{sat}(q^-, y) = \neg m(q^-, y)$) enthalten ist:

1. **Fall A — Verbot liegt innerhalb des positiven Zielbereichs ($\{y \mid m(q^-, y)\} \subseteq \{y \mid m(q^+, y)\}$):**
   Dies ist das Standardmuster fast aller bisherigen Tests (z. B. `post=[WorldState(returns=int), WorldState(returns=99, expect=False)]`). Unter reinem `post="exists"` (`OR`) lautet die Bedingung:
   $$(y \in \mathbb{Z}) \;\lor\; (y \neq 99)$$
   - Für $y = 99$ (den explizit verbotenen Wert!) ist der linke Zweig $(99 \in \mathbb{Z})$ **wahr ($\top$)**.
   - Für jeden beliebigen anderen Wert $y \neq 99$ (selbst `None`, `"crash"` oder `object()`) ist der rechte Zweig $(y \neq 99)$ **wahr ($\top$)**.
   - Damit gilt für **jedes denkbare Python-Objekt $y$**:
     $$\forall y \in \text{Any}: \quad (y \in \mathbb{Z}) \lor (y \neq 99) \;\equiv\; \top \quad (\textbf{Unbedingte Tautologie!})$$
   Ein solcher Vertrag unter `post="exists"` kann mathematisch **niemals fehlschlagen**.

2. **Fall B — Zwei disjunkte Verbote ($q_1^-, q_2^-$ mit $\{y \mid m(q_1^-, y)\} \cap \{y \mid m(q_2^-, y)\} = \emptyset$):**
   Bei `post=[WorldState(returns=404, expect=False), WorldState(returns=500, expect=False)]` lautet die reine Existenzformel:
   $$(y \neq 404) \;\lor\; (y \neq 500)$$
   Da kein Rückgabewert gleichzeitig $404$ und $500$ sein kann, ist auch diese Disjunktion für **jedes $y$ (inklusive $404$ und $500$!) immer wahr ($\top$)**.

3. **Fall C — Verbot liegt außerhalb eines konkreten Sollwerts ($\{y \mid m(q^+, y)\} \cap \{y \mid m(q^-, y)\} = \emptyset$):**
   Bei `post=[WorldState(returns=3), WorldState(returns=99, expect=False)]` (wie in `tests/test_offline_core.py:164`) gilt wegen $y = 3 \implies y \neq 99$:
   $$(y = 3) \;\lor\; (y \neq 99) \;\equiv\; (y \neq 99)$$
   Das positive Soll-Ziel `returns=3` wird durch das `OR` mit `y != 99` **vollständig verschluckt (subsumiert)** — jeder falsche Rückgabewert wie `999` oder `None` besteht den Test grün!

4. **Fall D — Einzelelement-Liste ($|Q| = 1$, z. B. `post=WorldState(returns=7, expect=False)`):**
   Für eine einelementige Menge $\{q_0\}$ fallen All- und Existenzquantor zwar logisch zusammen ($\exists q \in \{q_0\} : \neg m(q, y) \iff \neg m(q_0, y) \iff \forall q \in \{q_0\} : \neg m(q, y)$). Dennoch ist ein einzelnes `expect=False` ohne positiven Anker erstens ein **Vacuous-Pass-Risiko (`META-EBT-LONELY-NEGATION`)** und zweitens bricht jede spätere Erweiterung der Liste um einen zweiten Zustand sofort in Fall A, B oder C auf, wenn der Vertrag nicht von vornherein explizit unter `post={"quantor": "all", ...}` steht.

> [!IMPORTANT]
> **Meta-QA-Urteil zu Frage 1:**
> Deine Feststellung in `GEMINI-2.md:256` (*„Man kann einfach sagen: `"quantor": "all"`, wenn ein expect-flag mit gezählt werden muss“*) und der `STATE-GUARD` aus Arbeitspaket 2.1 bedingen einander: Weil `WorldState(..., expect=False)` prädikatenlogisch eine einschränkende Bedingung (Konjunktion) ausdrückt, ist es unter `post="exists"` (`OR`) immer entweder eine **Tautologie** oder eine **Auslöschung des Positiv-Ziels**. Der `STATE-GUARD` bei `post_quantor == "exists"` verhindert, dass Nutzer versehentlich tautologische Tests schreiben, wenn sie `"quantor": "all"` vergessen.

---

### 1.2 Meta-QA-Frage 2 (Konsistenz-, Subsumtions- & Prüfziel-Analyse zu Arbeitspaket 1)

> **Prüffrage:** *„Erhalten die Transformationsvorschläge in Arbeitspaket 1 (Migration der 9 Dateien / 21 Testfunktionen) alle bestehenden Assertions und Prüfziele, und wo leiden die Verträge unter logischer Subsumtion ($Q_{\text{pos}} \implies \neg Q_{\text{neg}}$)?“*

Eine Einzelprüfung aller 9 Dateien aus Arbeitspaket 1 deckt **sechs konkrete Korrekturpunkte** am Arbeitspaket auf:

#### Befund 2.1: `tests/test_offline_core.py` (Z. 160–166) — Erste Option im Arbeitspaket bricht Zeile 166!
In [`tests/test_offline_core.py:160-166`](./test_offline_core.py#L160-L166) steht:
```python
    elif feature == "ebt":
        trace = EBT(
            target=sum,
            pre=[WorldState(args=([1, 2],)), WorldState(args=([3],))],
            post=[WorldState(returns=3), WorldState(returns=99, expect=False)],
        ).run()
        assert trace.evaluation is True and len(trace.traces) == 4
```
- **Fehler im Arbeitspaket (`GEMINI-2.md`, Z. 157):** Das Arbeitspaket schlägt vor: *„entweder auf ein reines `post=WorldState(returns=3)` oder explizites `post={"quantor": "all", "states": [WorldState(returns=3), WorldState(returns=99, expect=False)]}` umstellen.“*
- **Warum Option 1 fehlschlägt:** Bei `post=WorldState(returns=3)` hat `pre` 2 Zustände und `post` nur noch 1 Zustand ($2 \times 1 = 2$ Traces). Dadurch schlägt Zeile 166 (`assert ... len(trace.traces) == 4`) sofort mit `AssertionError` fehl!
- **Korrekte Migration:** Zwingend die zweite Option `post={"quantor": "all", "states": [WorldState(returns=3), WorldState(returns=99, expect=False)]}` verwenden, damit die $2 \times 2$-Matrix (`len(trace.traces) == 4`) unangetastet bleibt.

#### Befund 2.2: `tests/tests_arena/test_ebt_arena_mutation.py` (Z. 99–112) — Klammer-Alternative im Arbeitspaket ist defekt!
In [`tests/tests_arena/test_ebt_arena_mutation.py:88-112`](./tests_arena/test_ebt_arena_mutation.py#L88-L112) stehen direkt untereinander:
1. `test_volatile_metadata_ignorance_green` (Z. 88–97): prüft `post=WorldState(returns=True, arena=PyVenv(BASE_ARENA))` mit `expect=True`.
2. `test_volatile_metadata_with_strict_expectation_red` (Z. 99–112): prüft `post=[WorldState(returns=True), WorldState(arena=PyVenv(BASE_ARENA), expect=False)]` mit `expect=False`.
- **Fehler im Arbeitspaket (`GEMINI-2.md`, Z. 165):** Die Klammer-Alternative lautet: *„(oder alternativ ohne Doppel-Negation direkt mit positivem `WorldState(returns=True, arena=PyVenv(BASE_ARENA))` prüfen)“*.
- **Warum die Klammer-Alternative fehlschlägt:**
  - Mit `EBT(..., expect=True)` entsteht eine 100 % redundante Kopie von `test_volatile_metadata_ignorance_green` (Z. 88).
  - Mit `EBT(..., expect=False)` schlägt der Test **rot fehl (`AssertionError`)**, weil `target_generate_volatile_metadata` nur ignorierte `.pyc`/`.dist-info`-Dateien erzeugt, der Arena-Vergleich gegen `BASE_ARENA` also **erfolgreich (`True`)** ist und `EBT(..., expect=False)` dieses `True` zu `False` invertiert!
- **Korrekte Migration:** Zwingend `post={"quantor": "all", "states": [WorldState(returns=True), WorldState(arena=PyVenv(BASE_ARENA), expect=False)]}` bei `expect=False` beibehalten.

#### Befund 2.3: `tests/tests_ebt/test_ebt_quantors.py` (Z. 113–158) — Historische Subsumtion & falsche Klammer-Alternative
In [`tests/tests_ebt/test_ebt_quantors.py:113-158`](./tests_ebt/test_ebt_quantors.py#L113-L158) (`test_mixed_expect_exists_green`, `test_mixed_expect_exists_red_lower_bound`, `test_mixed_expect_exists_red_upper_bound`) lautete `post` bisher:
```python
post=[
    WorldState(returns=0, expect=False),
    WorldState(returns=1), ..., WorldState(returns=5),
    WorldState(returns=6, expect=False),
]
```
- **Meta-QA-Subsumtionsbefund:** Da $Q^+ = \{1, 2, 3, 4, 5\}$ weder `0` noch `6` enthält ($y \in \{1..5\} \implies y \neq 0 \land y \neq 6$), waren die beiden `expect=False`-Zustände für `0` und `6` bisher **logisch komplett tot**! Selbst ohne `expect=False` scheiterten `args=(0,)` und `args=(6,)` bereits daran, dass `satisfies_pos` `False` war — im direkten Widerspruch zum Docstring in Z. 130 (*„Although it matches a declaration, it violates the strict negative filter“*).
- **Warum die Klammer-Alternative in `GEMINI-2.md` (Z. 98: *„oder einen reinen `exists`-Vertrag ohne redundante Verbote“*) falsch ist:** Sie würde den Abschnitt `MIXED QUANTOR INVERTIONS` seines Prüfziels berauben und `test_exists_green` / `test_exists_red` (Z. 48–72) duplizieren.
- **Korrekte Migration:** Zwingend auf `post={"quantor": "all", "states": [WorldState(returns=lambda v: 0 <= v <= 6), WorldState(returns=0, expect=False), WorldState(returns=6, expect=False)]}` umstellen. Erst dadurch erfüllen `0` und `6` die positive Bereichsbedingung `0 <= v <= 6` und scheitern **ausschließlich** am jeweiligen Negativ-Filter (`expect=False`), exakt wie der Docstring es verlangt!

#### Befund 2.4: `tests/tests_ebt/test_ebt_quantors.py` (Z. 208–232) — Vertrags-Asymmetrie zwischen Green und Red
In [`tests/tests_ebt/test_ebt_quantors.py:208-232`](./tests_ebt/test_ebt_quantors.py#L208-L232) nutzt `test_negative_filters_green` (Z. 214) das positive Prädikat `200 <= status < 300` (wodurch `404` und `500` logisch subsumiert sind), während `test_negative_filters_red` (Z. 227) `200 <= status < 600` nutzt.
- **Meta-QA-Empfehlung:** Neben dem Wrapping beider `post`-Listen in `{"quantor": "all", "states": [...]}` sollte auch in `test_negative_filters_green` der Bereich `200 <= status < 600` genutzt werden, damit Positiv-Test (`args=(200,)`) und Negativ-Gegenprobe (`args=(404,)`, `expect=False`) exakt **denselben Vertrag** prüfen.

#### Befund 2.5: `tests/tests_ebt/test_ebt_returns.py` (Z. 87–123), `test_ebt_exception_contracts.py` (Z. 76–111) & `test_ebt_return_reporting.py` (Z. 76–126)
1. **Doppelte `EBT`-Aufrufe nicht übersehen:** Sowohl `test_negative_none_contract_rejects_none` ([`test_ebt_returns.py:101-123`](./tests_ebt/test_ebt_returns.py#L101-L123), Z. 103 `result` und Z. 115 `inverted`) als auch `test_forbidden_exception_rejects_matching_exception_message` ([`test_ebt_exception_contracts.py:89-111`](./tests_ebt/test_ebt_exception_contracts.py#L89-L111), Z. 90 `result` und Z. 101 `inverted`) enthalten **jeweils zwei `EBT`-Instanziierungen**. Wer nur den ersten Aufruf migriert, lässt den `inverted`-Aufruf beim Einschalten des `STATE-GUARD`s crashen.
2. **Meta-QA-Hinweis zur bestehenden Subsumtion in `test_negative_none_contract_rejects_none` und `test_forbidden_falsy_return_reports_the_matching_value`:**
   - In `test_negative_none_contract_rejects_none` wird `args=(None,)` gegen `[WorldState(returns=int), WorldState(returns=None, expect=False)]` geprüft und `assert [trace.evaluation for trace in result.traces] == [False, True]` verlangt. Weil `isinstance(None, int)` bereits `False` ist (`trace[0].evaluation == False`), ist die Konjunktion `all([False, ...])` selbst dann `False`, wenn `expect=False` in `Q-State 1` gar nicht ausgewertet würde.
   - Da die Leitplanke aus `GEMINI-2.md` (Z. 213) vorschreibt, bestehende Assertions (`[False, True]`) nicht umzuschreiben, behalten wir `[WorldState(returns=int), WorldState(returns=None, expect=False)]` unter `quantor="all"` bei — während die scharfe Mutation-Probe, bei der $Q_{\text{pos}}$ (`True`) erfüllt ist und **allein** $Q_{\text{neg}}$ (`expect=False`) den Ausschlag gibt (`[True, True] -> False`), in `test_forbidden_exception_rejects_matching_exception_message` (`test_ebt_exception_contracts.py:98`), `test_local_expect_false_red` (`test_ebt_quantors.py:195`), `test_json_retains_every_input_and_post_match_including_negative_states` (`test_ebt_persistent_reports.py:147`) und `test_post_quantor_all_with_negative_worldstate_expect_false` (`test_ebt_quantor_declaration.py:406`) verankert ist.

#### Befund 2.6: `tests/tests_ebt/test_ebt_contract_mutation.py` (Z. 14–45) — Nur Dict-Wrapper erhält das Prüfziel
In [`tests/tests_ebt/test_ebt_contract_mutation.py:14-45`](./tests_ebt/test_ebt_contract_mutation.py#L14-L45) prüft `test_replacing_return_contract_cannot_rewrite_the_verdict` für `forbidden in [False, True]`, dass `post = WorldState(returns=7, expect=not forbidden)` vor dem Target-Aufruf (`post.returns = 42; return 42`) tief kopiert wird.
- **Warum die Klammer-Alternative in `GEMINI-2.md` (Z. 141: *„oder `EBT(..., expect=False)`“*) unzulässig ist:** Sie würde `WorldState.expect=False` gar nicht mehr testen und das JSON-Feld `document["traces"][0]["post"]["expect"]` verändern.
- **Korrekte Migration:** `case = EBT(target=mutate, post={"quantor": "all", "states": post}, reporter=reporters[reporting])` (für einen einzelnen `WorldState` ist `"quantor": "all"` im Fall `forbidden=False` äquivalent zu `"exists"` und im Fall `forbidden=True` `STATE-GUARD`-konform!).

---

### 1.3 Meta-QA-Frage 3 (Mutation Testing zu Arbeitspaket 2 — Die blinde Stelle bei `evaluate_step_logic`)

> **Prüffrage (Methodik 4 aus `META_QUESTION.md` — Mutation Testing):** *„Angenommen, ein Entwickler implementiert im nächsten Schritt alle vier `STATE-GUARD`s und den Sticky-Quantor-Reset in `src/qb_cubie/ebt.py` und `WorldState`, vergisst aber komplett, `evaluate_step_logic()` in `src/qb_cubie/protocols.py:129-140` umzubauen. Schlägt dann mindestens ein Test aus Arbeitspaket 1 oder Arbeitspaket 2 rot an?“*

#### Mathematischer & Empirischer Befund: **NEIN — der Mutant überlebt!**

Schauen wir uns [`src/qb_cubie/protocols.py:129-140`](../src/qb_cubie/protocols.py#L129-L140) an:
```python
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

Warum überlebt dieser ungefixte Code **alle** Tests aus Arbeitspaket 1 und Arbeitspaket 2, sobald in `EBT._arrange()` der `STATE-GUARD` für `post_quantor == "exists"` eingebaut ist?
1. **Wenn `post_quantor == "exists"`:** Der neue `STATE-GUARD` in `EBT._arrange()` wirft bereits vor der Target-Ausführung einen `ValueError`, sobald `any(not s.expect for s in self.post)` wahr ist. Über `EBT.run()` erreicht `evaluate_step_logic(..., "exists")` also nur noch nichtleere Trace-Listen mit $Q^- = \emptyset$ (`negatives == []`, `violates_neg == False`). Für $Q^- = \emptyset$ und $Q^+ \neq \emptyset$ berechnet die alte Funktion `any(t.evaluation for t in positives) and True`, was 100 % identisch zur neuen Funktion `any(results)` ist!
2. **Wenn `post_quantor == "all"`:** Nach den Gesetzen von De Morgan gilt für jede (auch rein negative!) nichtleere Liste $Q = Q^+ \cup Q^-$ wegen `all([]) == True`:
   $$\Big(\forall t \in Q^+ : t.\text{evaluation}\Big) \;\wedge\; \neg\Big(\exists t \in Q^- : t.\text{evaluation}\Big) \;\;\equiv\;\; \forall t \in Q : \big(t.\text{evaluation} \text{ if } t.\text{post.expect} \text{ else } \neg t.\text{evaluation}\big)$$
   Für `post_quantor == "all"` liefern alte und neue `evaluate_step_logic()` für **jede nichtleere Trace-Liste** exakt denselben Wahrheitswert!

Damit bleibt der eigentliche Bug in `evaluate_step_logic()` (`protocols.py:129-140`) — nämlich die $Q^+/Q^-$-Partitionierung und der *Vacuous-Pass*-Zweig `if not positives: satisfies_pos = True` — durch die 4 Tests aus Arbeitspaket 2 **komplett ungetestet**, obwohl `evaluate_step_logic` eine öffentliche Funktion in `qb_cubie.protocols` ist und von `PytestReporter._select_report_step()` (`src/qb_cubie/reporter.py:101`) direkt aufgerufen wird!

#### Wie wir diese Mutations-Lücke in Arbeitspaket 2 schließen

`evaluate_step_logic(traces, post_quantor)` muss **selbst** die Quantor-Invariante durchsetzen und in Arbeitspaket 2 direkt getestet werden:
1. **Kein `expect=False` unter `post_quantor="exists"` in `evaluate_step_logic()`:** Enthält `traces` bei `post_quantor == "exists"` einen Trace mit `t.post.expect is not True` (oder nicht-booleschem `expect`), wirft auch `evaluate_step_logic()` direkt `ValueError("STATE-GUARD: ...")` bzw. `TypeError("STATE-GUARD: ...")`.
2. **Kein Vacuous-True bei leerer Trace-Liste unter `"exists"`:** Für `traces = []` liefert `evaluate_step_logic([], "exists")` gemäß der Standard-Semantik von `any([])` den Wert **`False`** ($\exists x \in \emptyset \equiv \bot$), während der alte Code wegen `if not positives: satisfies_pos = True` fälschlich **`True`** liefert!
3. **Ein zusätzlicher Red-Phase-Unit-Test (`test_evaluate_step_logic_enforces_pure_quantor_invariants`)** in `test_ebt_quantor_declaration.py` prüft `evaluate_step_logic` direkt auf diese beiden Punkte — er schlägt gegen den ungehärteten Core sofort rot fehl und stirbt nur dann grün, wenn `evaluate_step_logic()` in `protocols.py` tatsächlich bereinigt wurde.

---

### 1.4 Meta-QA-Frage 4 (Äquivalenzklassen & Lebenszyklus-Lücken in Arbeitspaket 2)

> **Prüffrage (Schritt 3 aus `GUIDE_Quality-Assurance.md` — Äquivalenzklassen & Kantenfälle):** *„Decken die 4 vorgeschlagenen Guard-Tests in Arbeitspaket 2 alle Mutations- und Konfigurationspfade von `EBT` und `WorldState` ab?“*

Das Audit zeigt **vier unterabgedeckte Kantenfälle** in Arbeitspaket 2 (`GEMINI-2.md`, Z. 171–186):

1. **Lücke 4.1 — Sticky-Quantor-Bug ist symmetrisch (`case.pre` UND `case.post`) und hat eine gefährliche Gegen-Invariante:**
   - In `src/qb_cubie/ebt.py:170-171` steht:
     ```python
     self.pre, self.pre_quantor = self._parse_state_config(self.pre, "pre", self.pre_quantor)
     self.post, self.post_quantor = self._parse_state_config(self.post, "post", self.post_quantor)
     ```
   - **Fehlende Symmetrie:** Arbeitspaket 2.4 prüft nur `case.post = [WorldState(returns=1), WorldState(returns=2)]` nach `post={"quantor": "all", ...}` (Reset auf `"exists"`). Genau derselbe Bug existiert aber für **`case.pre`**: Wird ein `EBT`-Fall erst mit `pre={"quantor": "exists", "states": [...]}` ausgeführt und danach per `case.pre = [WorldState(args=1), WorldState(args=2)]` (oder `case.pre = WorldState(args=1)` oder `case.pre = None`) neu zugewiesen, bleibt `case.pre_quantor` aktuell fehlerhaft auf `"exists"` kleben, statt auf `"all"` zurückzuspringen!
   - **Gefährliche Gegen-Invariante (Wiederholtes `.run()` OHNE Neuzuweisung):**
     Würde ein Entwickler in `_arrange()` naiv `self._parse_state_config(self.post, "post", "exists")` schreiben und das Entpacken des Dict-Wrappers von `__init__` nach `_arrange()` verschieben, dann würde `self.post` beim **ersten** `case.run()` zu einer `list` entpackt — und beim **zweiten** `case.run()` **ohne Neuzuweisung** würde `case.post_quantor` plötzlich stillschweigend von `"all"` auf `"exists"` zurückfallen! Aktuell ruft **kein einziger Test** in `test_ebt_quantor_declaration.py` oder `test_ebt_args_normalization.py` zweimal hintereinander `case.run()` auf derselben Instanz mit `post="all"` oder `pre="exists"` ohne Neuzuweisung auf!
   - **Konsequenz für den Test:** Der Sticky-Quantor-Test muss einen vierstufigen Lebenszyklus für `pre` **und** `post` prüfen:
     1. Lauf 1 mit `pre={"quantor": "exists", ...}` und `post={"quantor": "all", ...}` $\rightarrow$ `pre_quantor == "exists"`, `post_quantor == "all"`.
     2. Lauf 2 **ohne Neuzuweisung** (`case.run()` erneut) $\rightarrow$ `pre_quantor == "exists"` und `post_quantor == "all"` bleiben erhalten!
     3. Lauf 3 nach **In-Place-Listenmutation** (`case.post.append(...)`) $\rightarrow$ `post_quantor == "all"` bleibt erhalten!
     4. Lauf 4 nach **Attribut-Neuzuweisung** (`case.pre = [...]`, `case.post = [...]` sowie Einzel-`WorldState` und `None`) $\rightarrow$ `pre_quantor` wird sauber auf `"all"` und `post_quantor` auf `"exists"` zurückgesetzt!

2. **Lücke 4.2 — In-Place-Mutation von `expect` zwischen zwei Läufen:**
   Da `WorldState` und `EBT` veränderliche Objekte sind ([`GUIDE_Contract-Semantics.md:102, 205`](../docs/GUIDE_Contract-Semantics.md#L205)), muss der Test auch sicherstellen, dass eine nachträgliche Mutation nach einem gültigen ersten Lauf — nämlich `case.post[0].expect = False` (unter `post="exists"`), `case.pre[0].expect = False`, `case.post[0].expect = None` oder `case.expect = None` — beim nächsten `case.run()` in `_arrange()` vor jeder Target-Ausführung abgefangen wird.

3. **Lücke 4.3 — Python-Subtyping `bool < int` bei der Typprüfung auf `expect`:**
   In Python gilt `issubclass(bool, int) is True`, also `isinstance(True, int) is True`! Ein nachlässiger Typ-Check dürfte niemals `int` durchlassen. Arbeitspaket 2.3 muss daher neben `expect=None` und `expect="true"` explizit auch **`expect=1` und `expect=0`** sowohl auf `WorldState(..., expect=...)` als auch auf `EBT(..., expect=...)` prüfen (`TypeError("STATE-GUARD: ...")`).

4. **Lücke 4.4 — `pre.expect=False` unter allen vier `pre`-Strukturformen:**
   Arbeitspaket 2.2 nennt nur `pre=WorldState(args=1, expect=False)`. Der Guard-Test muss alle 4 Äquivalenzklassen abdecken:
   - einzelnes `pre=WorldState(args=1, expect=False)`,
   - Liste `pre=[WorldState(args=1), WorldState(args=2, expect=False)]`,
   - expliziter Wrapper `pre={"quantor": "all", "states": [WorldState(args=1, expect=False)]}`,
   - expliziter Wrapper `pre={"quantor": "exists", "states": [WorldState(args=1, expect=False)]}`.

---

### 1.5 Meta-QA-Frage 5 (Selbst-Sabotage zwischen Arbeitspaket 2 und Arbeitspaket 3)

> **Prüffrage:** *„Harmonieren die neuen Negativ-Tests in `tests/tests_ebt/test_ebt_quantor_declaration.py` (Arbeitspaket 2) mit den statischen CST-Wächtern in `tests/tests_meta/test_gate_2.py` und `tests/tests_meta/test_gate_3.py` (Arbeitspaket 3) — oder bringt Arbeitspaket 3 das Repository-Gate zum Absturz?“*

#### Empirischer Nachweis eines direkten Widerspruchs im Arbeitspaket (`GEMINI-2.md`)

In `GEMINI-2.md` fordern drei Stellen gleichzeitig:
1. **Arbeitspaket 2.1 & 2.3 (Z. 175, 181):** In `tests/tests_ebt/test_ebt_quantor_declaration.py` sollen `EBT`-Aufrufe mit `post=[WorldState(returns=int), WorldState(returns=99, expect=False)]`, `post={"quantor": "exists", "states": [...]}` und `WorldState(..., expect=None)` ergänzt werden.
2. **Arbeitspaket 3.1 (Z. 194):** In `tests/tests_meta/test_gate_3.py` soll sichergestellt werden, *„dass `WorldState(..., expect=False)` statisch nur innerhalb eines expliziten `"quantor": "all"`-Wrappers akzeptiert wird.“*
3. **Abnahmekriterium (Z. 220):** *„Alle migrierten Tests in `tests/tests_ebt/`, `tests/tests_arena/`, `tests/test_offline_core.py` sowie `tests/tests_meta/` laufen mit `pytest` sauber durch (lediglich die 4 neuen Guard-Tests aus Arbeitspaket 2 schlagen erwartungsgemäß rot fehl...).“*

**Was passiert tatsächlich, wenn man das genau so umsetzt?**
`test_gate_3.py::test_repository_has_no_lonely_ebt_negations` scannt **alle** Python-Dateien unter `tests/` (einschließlich `test_ebt_quantor_declaration.py`!).
- Bereits gegen das **heutige, unveränderte** `test_gate_3.py` erzeugt ein literaler Testaufruf `EBT(target=f, post=WorldState(returns=1, expect=None))` oder `EBT(target=f, post=WorldState(returns=99, expect=False))` in `test_ebt_quantor_declaration.py` sofort einen fatalen Fehler in `tests/tests_meta/test_gate_3.py`:
  ```text
  [META-EBT-LONELY-NEGATION] 0pos/1neg - Einsame Negation (1x expect=False in post ohne positives Ziel)
  ```
- Und falls `test_gate_3.py` zusätzlich jedes `WorldState(expect=False)` außerhalb von `post={"quantor": "all", ...}` statisch als Fehler meldet, schlägt `test_gate_3.py` **auch** bei `EBT(target=..., post=[WorldState(returns=int), WorldState(returns=99, expect=False)])` in `test_ebt_quantor_declaration.py` fehl!

#### Drei weitere blinde Flecken in Arbeitspaket 3 (`test_gate_3.py` & `test_gate_2.py`)

1. **In `test_gate_3.py` sind nicht nur Z. 177–178 betroffen, sondern 10 Clean-Probes (Z. 177–178, 180, 183–210):**
   Arbeitspaket 3.1 (`GEMINI-2.md`, Z. 193) nennt nur die beiden Clean-Probes in Z. 177–178 (`mixed-list-pos-and-neg`, `mixed-tuple-neg-and-pos`). Tatsächlich enthalten in [`tests/tests_meta/test_gate_3.py:177-210`](./tests_meta/test_gate_3.py#L177-L210) aber **8 weitere Clean-Probes** (Z. 180 `mixed-opaque-post-list` sowie alle 7 `exempt-*`-Probes in Z. 183–210) ein statisches `WorldState(..., expect=False)` außerhalb eines `"quantor": "all"`-Wrappers!
2. **In `test_gate_3.py` prüfen alle 16 Fault-Probes (Z. 250–306) exakt die `0pos/Kneg`-Invariante:**
   `test_lonely_negation_rule_detects_fault_probes` (Z. 336–344) verlangt für jede rote Sonde exakt `len(diagnostics) == 1`, `diag.node_name == "0pos/1neg"` (bzw. `"0pos/2neg"`, `"0pos/3neg"`) und `EXEMPT_TAG in diag.message`.
   - Die Aufgabe von `META-EBT-LONELY-NEGATION` (`EbtLonelyNegationRule`) ist und bleibt die Erkennung **einsamer Negationen (`0pos/Kneg`)** — also `post`-Spezifikationen ohne jeden positiven Ankerzustand!
   - Weil in der reparierten Test-Suite alle `expect=False`-Zustände in `post={"quantor": "all", "states": ...}` verpackt werden, `test_gate_3.py` bisher bei `cst.Dict` in `_extract_post_worldstates()` (Z. 77–94) aber pauschal `None` zurückgibt, wäre `test_gate_3.py` ohne Dict-Support nach der Migration **komplett blind** gegenüber einsamen Negationen wie `post={"quantor": "all", "states": [WorldState(returns=99, expect=False)]}`!
   - Das Verbot von `WorldState(expect=False)` unter `post="exists"` (auch bei gemischten `1pos/1neg`-Listen!) wird hingegen zur Laufzeit ausnahmslos durch den neuen **`STATE-GUARD`** im Core erzwungen.
3. **In `test_gate_2.py` fehlen die Bereinigung der Alt-Probes (Z. 167–168, 216) sowie die neuen Kalibrierungs-Sonden (Meta-Gate 5):**
   - In [`tests/tests_meta/test_gate_2.py:167-168`](./tests_meta/test_gate_2.py#L167-L168) stehen zwei Clean-Probes (`many-pre-one-positive-one-negative` und `many-pre-only-negative-posts`) sowie in Z. 216 eine Fault-Probe (`two-positive-one-negative`), die `WorldState(..., expect=False)` in einer ungewrappten Standard-`post`-Liste (`"exists"`) als normales `EBT`-Muster verwenden.
   - Nach der Reparatur von `_count_pre_states()` und `_count_positive_post_states()` für den Dict-Wrapper `{"quantor": ..., "states": ...}` müssen gemäß **Meta-Gate 5 (Wächter-Kalibrierungs-Triade)** in `test_gate_2.py` zwingend sowohl **neue Clean-Probes** (z. B. `pre=[p1, p2]` mit `post={"quantor": "all", "states": [q1, q2]}` $\rightarrow$ Konjunktion, kein Kreuzprodukt!) als auch **neue Fault-Probes** (`pre={"quantor": "all", "states": [p1, p2]}` mit `post={"quantor": "exists", "states": [q1, q2]}` ohne Begründungs-Tag $\rightarrow$ `2x2`-Kreuzprodukt!) ergänzt werden.

#### Wie wir Arbeitspaket 2 und Arbeitspaket 3 konfliktfrei verzahnen

1. **Parametrisierte Variablen-Übergabe in `test_ebt_quantor_declaration.py` (Arbeitspaket 2):**
   Genau wie alle bestehenden Guard-Tests in Gruppe E von [`tests/tests_ebt/test_ebt_quantor_declaration.py:539-711`](./tests_ebt/test_ebt_quantor_declaration.py#L539-L711) übergeben auch die neuen Guard-Tests ihre ungültigen `pre`-/ `post`-Konfigurationen über `@pytest.mark.parametrize`-Parameter (`EBT(target=..., pre=pre_val, post=post_val, expect=expect_val)`). Dadurch sieht der statische CST-Scanner an der `EBT(...)`-Aufrufstelle die Variablen `pre_val`/`post_val` und schlägt niemals fälschlich auf den Negativ-Tests des `STATE-GUARD`s an.
2. **Klare Aufgabentrennung in `test_gate_3.py` (Arbeitspaket 3.1):**
   - `_extract_post_worldstates(module, post_expr)` entpackt neben `WorldState(...)` und `cst.List`/`cst.Tuple` nun auch `cst.Dict` (`{"quantor": ..., "states": ...}` — sowohl wenn `"states"` ein einzelner `WorldState(...)`-Aufruf ist als auch bei einer Liste/einem Tupel von `WorldState(...)`-Aufrufen).
   - Alle Clean-Probes in `test_gate_3.py` mit statischem `expect=False` (Z. 177–178, 180, 183–210) werden auf `post={"quantor": "all", "states": ...}` umgestellt, sodass `test_gate_3.py` nur noch `STATE-GUARD`-konforme Clean-Probes lehrt.
   - Die Fault-Probes in `test_gate_3.py` werden um einsame Negationen **innerhalb** des Dict-Wrappers (`post={"quantor": "all", "states": WorldState(returns=99, expect=False)}` und `post={"quantor": "all", "states": [WorldState(returns=404, expect=False), WorldState(returns=500, expect=False)]}`) erweitert.

---

### 1.6 Meta-QA-Frage 6 (Sammlungs- & Linter-Hygiene bei den Abnahmekriterien)

> **Prüffrage (Methodik 6 aus `META_QUESTION.md` — Collection- & Umgebungs-Hygiene):** *„Was passiert, wenn wir das Abnahmekriterium aus Abschnitt 4 (`Statische Prüfungen ruff, mypy, pylint auf tests/ melden 0 Fehler`) im aktuellen Workspace ausführen?“*

Ein empirischer Testlauf im Workspace deckt zwei Umgebungs-Fakten auf, die im Arbeitspaket unpräzise formuliert sind:

1. **Befund 6.1 — Altlasten vs. echte Laufzeit-Sonden in `tests/` bei `ruff` und `mypy`:**
   - Ein ungefiltertes `.venv/bin/ruff check tests/` über alle Testdateien meldet aktuell **19 Fehler** in bestehenden Dateien:
     - In [`tests/tests_arena/test_ebt_arena.py:16, 63`](./tests_arena/test_ebt_arena.py#L16) stehen `import pytest` und `import cowsay` ohne weitere Nutzung im Funktionskörper (`F401`). Diese Imports sind **keine Versehen**, sondern **echte Laufzeit-Sonden**, die innerhalb einer `PyVenv`-Arena prüfen, ob ein Paket importierbar ist (`try: import cowsay; return True except ImportError: return False`). Würde man sie wegen `F401` löschen, wäre der Isolationstest zerstört!
     - In **2 der 9 zu migrierenden Dateien** — [`tests/tests_ebt/test_ebt_quantors.py:1`](./tests_ebt/test_ebt_quantors.py#L1) und [`tests/tests_arena/test_ebt_arena_mutation.py:1`](./tests_arena/test_ebt_arena_mutation.py#L1) — liegen aktuell unsortierte Importblöcke (`I001`, z. B. `import subprocess, sys` in einer Zeile) vor.
   - Ein ungefiltertes `mypy` auf [`tests/tests_ebt/test_ebt_returns.py:10`](./tests_ebt/test_ebt_returns.py#L10) meldet `error: Skipping analyzing "cloudpickle": module is installed, but missing library stubs or py.typed marker [import-untyped]`, sofern nicht `--ignore-missing-imports` (oder die isolierte Konfiguration aus `tests/test_lint.py`) übergeben wird.
   - **Präzisiertes Abnahmekriterium:**
     - Auf allen **12 im Auftrag bearbeiteten Testdateien** müssen `.venv/bin/ruff check` (inklusive `I001`-Bereinigung in `test_ebt_quantors.py` und `test_ebt_arena_mutation.py`), `MYPYPATH=src .venv/bin/mypy --ignore-missing-imports --warn-unreachable --check-untyped-defs` sowie `PYTHONPATH=src .venv/bin/pylint --disable=all --enable=unreachable` (und die Linter-Suite `pytest tests/test_lint.py`) mit **0 Fehlern** durchlaufen.
2. **Befund 6.2 — Kopplung von `test_styleguide.py::test_docs_code_examples` an das `fast`- und `meta`-Profil:**
   - Weil `test_styleguide.py` in [`tests/conftest.py:27`](./conftest.py#L27) nur die Marker `("meta", "lint")` trägt, weist `pytest_collection_modifyitems` (`conftest.py:82-83`) `test_docs_code_examples` automatisch den Marker `fast` zu.
   - **In der aktuellen TGD Red-Phase (nur `tests/` bearbeitet):** `test_styleguide.py` läuft weiterhin grün, da `src/qb_cubie/` und `docs/` noch unverändert sind.
   - **Wichtige Warnung für den nachfolgenden Green-Phase-Schritt:** Sobald `src/qb_cubie/` den neuen `STATE-GUARD` aktiviert, wird `test_styleguide.py::test_docs_code_examples` bei jedem Standard-`pytest`-Lauf (`make test` / `make test-meta`) rot anschlagen, bis die Live-Beispiele in `docs/GUIDE_Expect-Flags.md` (Z. 39–57, 80–101, 154–177) und `docs/GUIDE_EBT-Usage-Pattern.md` (Z. 147–169) synchron auf `post={"quantor": "all", ...}` umgestellt sind.

---

## Teil 2: Überprüfbare Teil-Hypothesen zur Reparatur der Test-Suite ($H_1$ bis $H_5$)

Jede Teil-Hypothese ist so geschnitten, dass sie **deterministisch überprüfbar** ist — sowohl im aktuellen Schritt (**TGD Red-Phase**: nur `tests/` angepasst, Core in `src/qb_cubie/` noch auf `v0.0.8`) als auch nach der anschließenden Core-Reparatur (**TGD Green-Phase**).

---

### Hypothesen-Gruppe $H_1$: Migration der 9 bestehenden Testdateien (21 Testfunktionen, 23 `EBT`-Aufrufe)

> **Übergeordnete Hypothese $H_1$:**
> *Wenn alle 23 `EBT`-Aufrufe in den 9 betroffenen Testdateien, die bisher `WorldState(..., expect=False)` unter dem impliziten Standard-`post` (`"exists"`) genutzt haben, auf die explizite Konjunktion `post={"quantor": "all", "states": [...]}` umgestellt werden, dann bleiben sämtliche 21 Testfunktionen sowohl gegen den aktuellen Core (`v0.0.8`) als auch gegen den reparierten Core (`evaluate_step_logic` ohne $Q^+/Q^-$-Split + `STATE-GUARD`) zu 100 % grün, ohne dass eine einzige fachliche Assertion abgeschwächt wird.*

| Teil-Hypothese | Zieldatei & Zeilen | Betroffene Testfunktionen (`EBT`-Aufrufe) | Exakte Transformations-Spezifikation ($Q_{\text{Soll}}$) | Überprüfbares Kriterium (Red- & Green-Phase) |
| :--- | :--- | :--- | :--- | :--- |
| **$H_{1.1a}$** | [`tests/tests_ebt/test_ebt_quantors.py:113-158`](./tests_ebt/test_ebt_quantors.py#L113-L158) | `test_mixed_expect_exists_green`, `test_mixed_expect_exists_red_lower_bound`, `test_mixed_expect_exists_red_upper_bound` (3 Aufrufe) | Ersetze die redundante Liste `[WS(0, False), WS(1)..WS(5), WS(6, False)]` durch `post={"quantor": "all", "states": [WorldState(returns=lambda v: 0 <= v <= 6), WorldState(returns=0, expect=False), WorldState(returns=6, expect=False)]}`. *(Beseitigt die logische Subsumtion: `0` und `6` erfüllen nun das positive Bereichsprädikat und scheitern exklusiv am `expect=False`-Filter!)* | `args=(3,)` $\to$ `evaluation is True`; `args=(0,)` mit `EBT(expect=False)` $\to$ `evaluation is True` (rohe Traces `[True, True, False]`); `args=(6,)` mit `EBT(expect=False)` $\to$ `evaluation is True` (rohe Traces `[True, False, True]`). |
| **$H_{1.1b}$** | [`tests/tests_ebt/test_ebt_quantors.py:181-232`](./tests_ebt/test_ebt_quantors.py#L181-L232) | `test_local_expect_false_green`, `test_local_expect_false_red`, `test_negative_filters_green`, `test_negative_filters_red` (4 Aufrufe) | Verpacke `post=[...]` jeweils in `post={"quantor": "all", "states": [...]}` (und angleiche in `test_negative_filters_green` das Bereichsprädikat auf `200 <= status < 600`, damit Green und Red denselben Vertrag prüfen). Bereinige `I001` in Z. 1–3. | Alle 4 Tests bestehen (`PASSED`); `trace.post_quantor == "all"`. |
| **$H_{1.2}$** | [`tests/tests_ebt/test_ebt_returns.py:87-123`](./tests_ebt/test_ebt_returns.py#L87-L123) | `test_negative_none_contract_accepts_non_none_values` (1 Aufruf), `test_negative_none_contract_rejects_none` (**2 Aufrufe**: `result` Z. 103 & `inverted` Z. 115) | Stelle in beiden Funktionen (und beiden `EBT`-Aufrufen in `test_negative_none_contract_rejects_none`) `post` auf `{"quantor": "all", "states": [WorldState(returns=int), WorldState(returns=None, expect=False)]}` um. | Für `[42, 0, False]`: `traces == [True, False]`, `evaluation is True`. Für `None`: `traces == [False, True]`, `result.evaluation is False`, `inverted.evaluation is True`. |
| **$H_{1.3}$** | [`tests/tests_ebt/test_ebt_exception_contracts.py:76-111`](./tests_ebt/test_ebt_exception_contracts.py#L76-L111) | `test_forbidden_exception_accepts_allowed_exception_message` (1 Aufruf), `test_forbidden_exception_rejects_matching_exception_message` (**2 Aufrufe**: `result` Z. 90 & `inverted` Z. 101) | Stelle alle 3 `EBT`-Aufrufe (`direct` und `tempfs`) auf `post={"quantor": "all", "states": [WorldState(raises=expectation(ValueError)), WorldState(raises=expectation(match="^invalid order:"), expect=False)]}` um. | Für `"wrong-message"`: `traces == [True, False]`, `evaluation is True`. Für `"value-error"`: `traces == [True, True]`, `result.evaluation is False`, `inverted.evaluation is True`. |
| **$H_{1.4}$** | [`tests/tests_ebt/test_ebt_return_reporting.py:76-126`](./tests_ebt/test_ebt_return_reporting.py#L76-L126) | `test_allowed_falsy_return_passes_with_negative_filter`, `test_forbidden_falsy_return_reports_the_matching_value`, `test_omitted_return_expectation_accepts_non_matching_negative_filter`, `test_omitted_return_expectation_does_not_invent_a_return_comparison` (4 Aufrufe) | Verpacke in allen 4 Funktionen die `post`-Liste in `post={"quantor": "all", "states": [...]}`. | Alle 20 parametrisierten Läufe bestehen; `[Q-State 1] Validation: Matched` wird bei verbotenem Falsy-Return gemeldet; bei `WorldState(expect=False)` ohne `returns` wird kein `"Returns:"`/`"UNSPECIFIED"` erfunden. |
| **$H_{1.5}$** | [`tests/tests_ebt/test_ebt_run_isolation.py:41-57`](./tests_ebt/test_ebt_run_isolation.py#L41-L57) | `test_previous_negative_match_does_not_poison_next_run`, `test_previous_positive_match_does_not_mask_next_negative_match` (2 Aufrufe) | Verpacke `post` in beiden Funktionen in `post={"quantor": "all", "states": [WorldState(returns=int), WorldState(returns=0, expect=False)]}`. *(Hinweis: Z. 172 mutiert `post.expect = False` erst nach `.run()` ohne Zweitlauf und bleibt unverändert gültig.)* | Beide Isolations-Tests bestehen im `singleprocess`- und `multiprocess`-Modus (`False -> True` bzw. `True -> False`). |
| **$H_{1.6}$** | [`tests/tests_ebt/test_ebt_contract_mutation.py:14-45`](./tests_ebt/test_ebt_contract_mutation.py#L14-L45) | `test_replacing_return_contract_cannot_rewrite_the_verdict` (1 parametrisierter Aufruf, 6 Kombinationen) | Übergib `post={"quantor": "all", "states": post}` an `EBT(...)` (wobei `post = WorldState(returns=7, expect=not forbidden)` als Referenz für die Laufzeit-Mutation `post.returns = 42` im Target erhalten bleibt). | Alle 6 Läufe (`silent`/`pytest`/`json` $\times$ `required`/`forbidden`) bestehen; `trace.post.returns == 7`, `result.evaluation is forbidden`. |
| **$H_{1.7}$** | [`tests/tests_ebt/test_ebt_persistent_reports.py:136-150`](./tests_ebt/test_ebt_persistent_reports.py#L136-L150) | `test_json_retains_every_input_and_post_match_including_negative_states` (1 Aufruf) | Verpacke `post` in `post={"quantor": "all", "states": [WorldState(returns=int), WorldState(returns=2, expect=False)]}`. | `document["evaluation"] is False`, `document["post_quantor"] == "all"`, `len(document["traces"]) == 4`, `evaluations == [True, False, True, True]`. |
| **$H_{1.8}$** | [`tests/test_offline_core.py:160-166`](./test_offline_core.py#L160-L166) | `exercise("ebt", base)` in `test_core_feature_requires_no_install_or_network` (1 Aufruf) | Verpacke `post` in `post={"quantor": "all", "states": [WorldState(returns=3), WorldState(returns=99, expect=False)]}` *(nicht auf Einzel-`WorldState` kürzen, damit `len(trace.traces) == 4` erhalten bleibt!)*. | `pytest tests/test_offline_core.py -k "ebt"` besteht (`trace.evaluation is True and len(trace.traces) == 4`, `0` Offline-Verstöße). |
| **$H_{1.9}$** | [`tests/tests_arena/test_ebt_arena_mutation.py:99-112`](./tests_arena/test_ebt_arena_mutation.py#L99-L112) | `test_volatile_metadata_with_strict_expectation_red` (1 Aufruf) | Verpacke `post` in `post={"quantor": "all", "states": [WorldState(returns=True), WorldState(arena=PyVenv(BASE_ARENA), expect=False)]}` bei `expect=False`. Bereinige `I001` in Z. 1–5. | `pytest tests/tests_arena/test_ebt_arena_mutation.py` besteht komplett grün. |

---

### Hypothesen-Gruppe $H_2$: Neue Red-Phase-Guard-Tests für `STATE-GUARD`s & Quantor-Reinheit

> **Übergeordnete Hypothese $H_2$:**
> *Wenn wir in `tests/tests_ebt/test_ebt_quantor_declaration.py` (Gruppe E) gezielte Guard-Tests für (1) das Verbot von `WorldState(expect=False)` unter `post="exists"`, (2) das Verbot von `WorldState(expect=False)` in `pre`, (3) die strikte `bool`-Typprüfung auf `WorldState.expect` und `EBT.expect` sowie (4) die direkte Invarianten-Prüfung auf `evaluate_step_logic()` ergänzen und die ungültigen Konfigurationen über `@pytest.mark.parametrize`-Variablen injizieren, dann:*
> 1. *schlagen diese Tests gegen den ungehärteten Core (`v0.0.8`) als echter **TGD Red-Phase-Nachweis** deterministisch fehl,*
> 2. *lösen sie in den statischen CST-Gates (`test_gate_2.py`, `test_gate_3.py`) **keine** Fehlalarme aus, und*
> 3. *erzwingen sie in der anschließenden Green-Phase zwingend sowohl die `STATE-GUARD`s in `ebt.py`/`WorldState` als auch den Umbau von `evaluate_step_logic()` in `protocols.py`.*

| Teil-Hypothese | Neuer Test in `test_ebt_quantor_declaration.py` | Geprüfte Äquivalenzklassen & Kantenfälle | Erwartetes Verhalten in TGD Red-Phase (aktueller Core `v0.0.8`) | Erwartetes Verhalten in TGD Green-Phase (reparierter Core) |
| :--- | :--- | :--- | :--- | :--- |
| **$H_{2.1}$** | `test_guard_rejects_negative_worldstate_under_post_exists` | Alle 4 Strukturformen mit `expect=False` unter `post="exists"`: (a) implizit einzeln `post=WorldState(returns=99, expect=False)`, (b) implizit gemischt `post=[WorldState(returns=int), WorldState(returns=99, expect=False)]`, (c) explizit einzeln `post={"quantor": "exists", "states": WorldState(returns=99, expect=False)}`, (d) explizit gemischt `post={"quantor": "exists", "states": [WorldState(returns=int), WorldState(returns=99, expect=False)]}` — sowie In-Place-Mutation `case.post[0].expect = False` vor Lauf 2 und mit `EBT(..., expect=False)`. | **FAIL (Red):** Aktueller Core wirft keinen `ValueError`, sondern führt das Target aus (`marker.exists() is True`) und wertet `expect=False` heimlich als `AND`-Veto aus. | **PASS (Green):** Wirft vor jeder Target-Ausführung `ValueError` mit `"STATE-GUARD"` (`not marker.exists()`); auch `EBT(..., expect=False)` unterdrückt den Konfigurationsfehler nicht. |
| **$H_{2.2}$** | `test_guard_rejects_negative_worldstate_in_pre` | Alle 4 Strukturformen mit `expect=False` in `pre`: (a) implizit einzeln `pre=WorldState(args=1, expect=False)`, (b) implizit Liste `pre=[WorldState(args=1), WorldState(args=2, expect=False)]`, (c) explizit `"all"` `pre={"quantor": "all", "states": [WorldState(args=1, expect=False)]}`, (d) explizit `"exists"` `pre={"quantor": "exists", "states": [WorldState(args=1, expect=False)]}` — sowie In-Place-Mutation `case.pre[0].expect = False` vor Lauf 2. | **FAIL (Red):** Aktueller Core ignoriert `pre.expect=False` stillschweigend und führt das Target aus (`marker.exists() is True`). | **PASS (Green):** Wirft vor jeder Target-Ausführung `ValueError` mit `"STATE-GUARD"` (`not marker.exists()`). |
| **$H_{2.3}$** | `test_guard_rejects_non_bool_expect_on_worldstate_and_ebt` | Nicht-`bool`-Werte `bad_expect in [None, 1, 0, "true", []]` (inkl. `int`-Subtyping-Falle `1` und `0`!): (a) bei `WorldState(expect=bad_expect)`, (b) bei `EBT(..., expect=bad_expect)`, (c) bei nachträglicher Mutation `ws.expect = bad_expect` bzw. `case.expect = bad_expect` vor `case.run()`. | **FAIL (Red):** Aktueller Core akzeptiert `None`, `0`, `1`, `"true"`, `[]` ohne `TypeError` und wertet sie per Truthiness (`bool(...)`) aus. | **PASS (Green):** Wirft sofort `TypeError` mit `"STATE-GUARD"` (`not marker.exists()`). |
| **$H_{2.4}$** | `test_evaluate_step_logic_enforces_pure_quantor_invariants` | Direkter Unit-Test auf `evaluate_step_logic(traces, post_quantor)` aus `qb_cubie.protocols`: (a) `evaluate_step_logic([], "exists") is False` vs. `evaluate_step_logic([], "all") is True`, (b) `evaluate_step_logic` mit einem `post=WorldState(expect=False)`-Trace unter `post_quantor="exists"` wirft `ValueError("STATE-GUARD: ...")`, (c) unter `post_quantor="all"` gilt rein `all(t.evaluation if t.post.expect else not t.evaluation)`. | **FAIL (Red):** Aktueller Core liefert für `evaluate_step_logic([], "exists")` fälschlich `True` (`if not positives: satisfies_pos = True`) und wirft bei `expect=False` unter `"exists"` keinen `ValueError`. | **PASS (Green):** Beweist, dass `evaluate_step_logic()` in `protocols.py` tatsächlich von der $Q^+/Q^-$-Partitionierung befreit wurde (kein überlebender Mutant!). |

---

### Hypothesen-Gruppe $H_3$: Lebenszyklus- & Sticky-Quantor-Hypothesen (`case.pre` & `case.post`)

> **Übergeordnete Hypothese $H_3$:**
> *Ein wiederverwendetes `EBT`-Objekt muss seinen explizit deklarierten Quantor (`pre_quantor="exists"` bzw. `post_quantor="all"`) über wiederholte `.run()`-Aufrufe ohne Neuzuweisung sowie bei In-Place-Listenmutationen bewahren, ihn jedoch bei jeder Attribut-Neuzuweisung ohne Dict-Wrapper (`case.pre = ...` bzw. `case.post = ...` mit Liste, Einzel-`WorldState` oder `None`) deterministisch auf den jeweiligen Standard-Quantor (`pre_quantor="all"`, `post_quantor="exists"`) zurücksetzen.*

| Teil-Hypothese | Szenario in `test_ebt_quantor_declaration.py` | Geprüfte Lebenszyklus-Übergänge | Erwartetes Verhalten in TGD Red-Phase (`v0.0.8`) | Erwartetes Verhalten in TGD Green-Phase (reparierter Core) |
| :--- | :--- | :--- | :--- | :--- |
| **$H_{3.1}$** | `test_sticky_quantor_resets_on_reassignment_and_persists_on_rerun` (Teil `post`) | 1. Init mit `post={"quantor": "all", "states": [WorldState(returns=int), WorldState(returns=1)]}` (`args=(1,)` $\to$ `True`, `post_quantor == "all"`).<br>2. Zweiter `.run()` **ohne Neuzuweisung** mit `case.pre = WorldState(args=(2,))` $\to$ muss unter `post="all"` scheitern (`evaluation is False`, `post_quantor == "all"`).<br>3. Neuzuweisung `case.post = [WorldState(returns=1), WorldState(returns=2)]` (einfache Liste ohne Wrapper!) bei `args=(2,)` $\to$ muss auf `post_quantor == "exists"` zurückspringen und mit `[False, True]` **bestehen (`evaluation is True`)**!<br>4. Analoge Prüfung für `case.post = WorldState(returns=2)` und `case.post = None`. | **FAIL (Red) in Schritt 3:** `case.post_quantor` bleibt in `ebt.py:171` auf `"all"` kleben, sodass `[WorldState(returns=1), WorldState(returns=2)]` bei `args=(2,)` fälschlich als Konjunktion (`False and True == False`) ausgewertet wird! | **PASS (Green):** Schritt 1 & 2 behalten `post_quantor == "all"`; Schritt 3 & 4 setzen `post_quantor` sauber auf `"exists"` zurück (`evaluation is True`). |
| **$H_{3.2}$** | `test_sticky_quantor_resets_on_reassignment_and_persists_on_rerun` (Teil `pre`) | 1. Init mit `pre={"quantor": "exists", "states": [WorldState(args=1), WorldState(args=2)]}`, `post=WorldState(returns=1)` $\to$ `evaluation is True`, `pre_quantor == "exists"`.<br>2. Zweiter `.run()` **ohne Neuzuweisung** $\to$ `pre_quantor == "exists"`, `evaluation is True`.<br>3. Neuzuweisung `case.pre = [WorldState(args=1), WorldState(args=2)]` (einfache Liste ohne Wrapper!) $\to$ muss auf `pre_quantor == "all"` zurückspringen und wegen `args=2 != 1` **scheitern (`evaluation is False`)**! | **FAIL (Red) in Schritt 3:** `case.pre_quantor` bleibt in `ebt.py:170` auf `"exists"` kleben, sodass `case.pre = [WorldState(args=1), WorldState(args=2)]` fälschlich als Disjunktion (`True or False == True`) besteht! | **PASS (Green):** Schritt 1 & 2 behalten `pre_quantor == "exists"`; Schritt 3 setzt `pre_quantor` sauber auf `"all"` zurück (`evaluation is False`). |

---

### Hypothesen-Gruppe $H_4$: Härtung & Kalibrierung der Meta-Gates (`test_gate_2.py` & `test_gate_3.py`)

> **Übergeordnete Hypothese $H_4$:**
> *Wenn `test_gate_2.py` (`META-EBT-CROSS-PRODUCT`) und `test_gate_3.py` (`META-EBT-LONELY-NEGATION`) um das statische Entpacken des Quantor-Dictionary-Wrappers `{"quantor": ..., "states": ...}` erweitert und ihre Clean- sowie Fault-Probes nach der Wächter-Kalibrierungs-Triade (Meta-Gate 5) auf die neue Quantor-Semantik aktualisiert werden, erkennen beide Gates Verstöße auch innerhalb von Dict-Wrappern zuverlässig und laufen über alle Python-Dateien unter `tests/` mit `0` Diagnosen grün durch.*

| Teil-Hypothese | Zieldatei | Konkrete Anpassung an Regel & Sonden (Clean Probes / Fault Probes / Repo-Gate) | Überprüfbares Kriterium |
| :--- | :--- | :--- | :--- |
| **$H_{4.1}$** | [`tests/tests_meta/test_gate_2.py`](./tests_meta/test_gate_2.py) (`META-EBT-CROSS-PRODUCT`) | 1. **Dict-Entpackung in `_count_pre_states(module, pre_expr)`:** Wenn `pre_expr` ein `cst.Dict` ist, extrahiere den Wert unter `"states"` und zähle dessen Listen-/Tupel-Elemente.<br>2. **Quantor-Differenzierung in `_count_positive_post_states(module, post_expr)`:** Wenn `post_expr` ein `cst.Dict` ist: Bei `"quantor": "all"` gib `1` zurück (Konjunktion $\forall q \in Q$, keine disjunktive Kreuzprodukt-Abschwächung!); bei `"quantor": "exists"` (oder unbekanntem Quantor) entpacke `"states"` und zähle die positiven `WorldState`s.<br>3. **Sonden-Update:** Stelle die Clean-Probes Z. 167–168 auf `post={"quantor": "all", "states": [...]}` um; ergänze neue Clean-Probes für `pre=[p1, p2]` + `post={"quantor": "all", "states": [WorldState(returns=int), WorldState(returns=3)]}` sowie neue Fault-Probes für unbegründete `2x2`-Aufrufe mit `pre={"quantor": "all", "states": [p1, p2]}` und `post={"quantor": "exists", "states": [WorldState(returns=1), WorldState(returns=2)]}` (beidseitig und einseitig gewrappt). | Alle Clean-Probes liefern `[]`; alle Fault-Probes liefern `META-EBT-CROSS-PRODUCT` (`2x2`/`3x4`); `test_repository_has_no_unjustified_ebt_cross_products` besteht über ganz `tests/` (`0` Diagnosen). |
| **$H_{4.2}$** | [`tests/tests_meta/test_gate_3.py`](./tests_meta/test_gate_3.py) (`META-EBT-LONELY-NEGATION`) | 1. **Dict-Entpackung in `_extract_post_worldstates(module, post_expr)`:** Wenn `post_expr` ein `cst.Dict` ist, suche den Schlüssel `"states"` und extrahiere rekursiv dessen `WorldState(...)`-Aufruf(e) (Einzel-`WorldState` oder `cst.List`/`cst.Tuple`).<br>2. **Clean-Probes bereinigen:** Stelle alle 10 Clean-Probes mit statischem `expect=False` (Z. 177–178, 180 sowie Z. 183–210) auf `post={"quantor": "all", "states": ...}` um.<br>3. **Fault-Probes erweitern:** Ergänze Fault-Probes für einsame Negationen innerhalb des Dict-Wrappers (`post={"quantor": "all", "states": WorldState(returns=99, expect=False)}` $\to$ `0pos/1neg` und `post={"quantor": "all", "states": [WorldState(returns=404, expect=False), WorldState(returns=500, expect=False)]}` $\to$ `0pos/2neg`). | Alle Clean-Probes liefern `[]`; alle Fault-Probes (inkl. Dict-Wrapper) liefern `META-EBT-LONELY-NEGATION` (`0pos/Kneg`); `test_repository_has_no_lonely_ebt_negations` besteht über ganz `tests/` (`0` Diagnosen). |

---

### Hypothesen-Gruppe $H_5$: TGD-Phasen-Invarianz & Schicht-Isolation

> **Übergeordnete Hypothese $H_5$:**
> *Die Trennung zwischen der jetzigen **TGD Red-Phase** (nur `tests/` geändert) und der nachfolgenden **TGD Green-Phase** (`src/qb_cubie/` + `docs/` geändert) erzeugt ein exaktes, reproduzierbares Differenzsignal:*

1. **Teil-Hypothese $H_{5.1}$ (Soll-Zustand am Ende der TGD Red-Phase — ausschließlich `tests/` bearbeitet):**
   - Alle **9 migrierten Testdateien** aus Arbeitspaket 1 (`test_ebt_quantors.py`, `test_ebt_returns.py`, `test_ebt_exception_contracts.py`, `test_ebt_return_reporting.py`, `test_ebt_run_isolation.py`, `test_ebt_contract_mutation.py`, `test_ebt_persistent_reports.py`, `test_offline_core.py`, `test_ebt_arena_mutation.py`) laufen mit `pytest` **100 % grün (`PASSED`)**.
   - Alle **3 Meta-Gate-Testdateien** (`test_gate_1.py`, `test_gate_2.py`, `test_gate_3.py`) inklusive ihrer Repository-Scans über ganz `tests/` laufen **100 % grün (`PASSED`)**.
   - Alle bestehenden Tests in `test_ebt_quantor_declaration.py` (Gruppen A–E) laufen **100 % grün (`PASSED`)**.
   - **Exakt und ausschließlich die neuen Red-Phase-Tests aus $H_2$ und $H_3$** in `test_ebt_quantor_declaration.py` schlagen gegen den noch ungehärteten Core (`v0.0.8`) **rot fehl (`FAILED`)**.
   - Alle 12 bearbeiteten Testdateien bestehen `ruff check`, `mypy --ignore-missing-imports --warn-unreachable --check-untyped-defs` und `pylint --disable=all --enable=unreachable` mit **0 Fehlern**.
2. **Teil-Hypothese $H_{5.2}$ (Soll-Zustand am Ende der TGD Green-Phase — nach Core- & Doku-Reparatur):**
   - Sobald `src/qb_cubie/protocols.py` (`WorldState.expect`-Typguard + reine `evaluate_step_logic`) und `src/qb_cubie/ebt.py` (`STATE-GUARD`s für `expect=False` bei `post="exists"` und in `pre`, `EBT.expect`-Typguard sowie Property-Setter/Referenz-Reset für `pre` und `post`) gehärtet sind, springen alle roten Tests aus $H_2$ und $H_3$ ohne jede weitere Änderung an den Testfunktionen auf **grün (`PASSED`)**.
   - Sobald die Live-Code-Snippets in `docs/GUIDE_Expect-Flags.md` und `docs/GUIDE_EBT-Usage-Pattern.md` nachgezogen sind, läuft auch `tests/test_styleguide.py::test_docs_code_examples` (`DocEnsurance`) komplett **grün (`PASSED`)**.

---

## Teil 3: Korrigierter & gehärteter Umsetzungsfahrplan für die Test-Suite (TGD Red-Phase)

Um die 8 identifizierten Schwachstellen des ursprünglichen Arbeitspakets aus `GEMINI-2.md` auszuschließen, sollte die Umsetzung in `tests/` exakt nach diesen vier bereinigten Schritten erfolgen:

1. **Schritt 1 — Migration der 9 bestehenden Testdateien gemäß $H_{1.1}$ bis $H_{1.9}$:**
   - In `test_ebt_quantors.py` (Z. 113–158) die konjunktive Bereichsformel `post={"quantor": "all", "states": [WorldState(returns=lambda v: 0 <= v <= 6), WorldState(returns=0, expect=False), WorldState(returns=6, expect=False)]}` einsetzen (nicht die sinnentstellende Klammer-Alternative), in Z. 214 das Bereichsprädikat auf `200 <= status < 600` harmonisieren und `I001` in Z. 1–3 bereinigen.
   - In `test_ebt_returns.py` (Z. 87–123) und `test_ebt_exception_contracts.py` (Z. 76–111) jeweils **alle drei** `EBT`-Aufrufe (inklusive `inverted = EBT(...)`) auf `post={"quantor": "all", "states": [...]}` umstellen.
   - In `test_ebt_return_reporting.py` (Z. 76–126), `test_ebt_run_isolation.py` (Z. 41–57) und `test_ebt_persistent_reports.py` (Z. 136–150) die `post`-Listen in `{"quantor": "all", "states": [...]}` verpacken.
   - In `test_ebt_contract_mutation.py` (Z. 25) `post={"quantor": "all", "states": post}` übergeben.
   - In `test_offline_core.py` (Z. 164) `post={"quantor": "all", "states": [WorldState(returns=3), WorldState(returns=99, expect=False)]}` nutzen, damit `len(trace.traces) == 4` (Z. 166) gewahrt bleibt.
   - In `test_ebt_arena_mutation.py` (Z. 107–110) `post={"quantor": "all", "states": [WorldState(returns=True), WorldState(arena=PyVenv(BASE_ARENA), expect=False)]}` bei `expect=False` nutzen und `I001` in Z. 1–5 bereinigen.
2. **Schritt 2 — Erweiterung der Meta-Gates (`test_gate_2.py` & `test_gate_3.py`) gemäß $H_{4.1}$ und $H_{4.2}$:**
   - In `test_gate_2.py` Dict-Entpackung für `pre` und `post` nachrüsten (`post` mit `"quantor": "all"` zählt als `1` konjunktives Ziel, `"quantor": "exists"` zählt die positiven `WorldState`s), Alt-Probes in Z. 167–168 aktualisieren und neue Clean-/Fault-Probes für Dict-Wrapper ergänzen.
   - In `test_gate_3.py` `_extract_post_worldstates()` um `cst.Dict`-Entpackung erweitern, alle 10 Clean-Probes mit statischem `expect=False` (Z. 177–178, 180, 183–210) auf `post={"quantor": "all", "states": ...}` umstellen und neue Fault-Probes für einsame Negationen im Dict-Wrapper ergänzen.
3. **Schritt 3 — Ergänzung der Red-Phase-Tests in `test_ebt_quantor_declaration.py` gemäß $H_{2.1}$–$H_{2.4}$ und $H_{3.1}$–$H_{3.2}$:**
   - Alle 5 neuen Testfunktionen (`test_guard_rejects_negative_worldstate_under_post_exists`, `test_guard_rejects_negative_worldstate_in_pre`, `test_guard_rejects_non_bool_expect_on_worldstate_and_ebt`, `test_evaluate_step_logic_enforces_pure_quantor_invariants`, `test_sticky_quantor_resets_on_reassignment_and_persists_on_rerun`) mit `@pytest.mark.parametrize`-Variablen-Injektion am Ende von Gruppe E in `test_ebt_quantor_declaration.py` einfügen.
4. **Schritt 4 — Verifikation der TGD Red-Phase & Statik-Abnahme gemäß $H_{5.1}$:**
   - `pytest` über alle migrierten Dateien und `tests/tests_meta/` ausführen (100 % grün),
   - `pytest` auf den neuen Guard-/Lifecycle-Tests in `test_ebt_quantor_declaration.py` ausführen (kontrollierter Red-Phase-Nachweis gegen `v0.0.8`),
   - `ruff`, `mypy` und `pylint` auf allen 12 bearbeiteten Testdateien mit `0` Fehlern verifizieren.

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
