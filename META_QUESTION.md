<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Gemini-App" model="Gemini-4-Argon" effort="High" routable="false" -->
**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Gemini-App
- **Modell:** Gemini-4-Argon
- **Reasoning-Effort:** High

---

Gibt es eigentliche bewährte Verfahren/Methoden aus der Qualitäts-Sicherung, um eine Test-Suite wie die von Cubie selbst zu prüfen und die Fälle gegen Widersprüche und Ähnliches zu untersuchen?
<!-- /qb:frame -->

Um eine Test-Suite wie die von `qb-cubie` nicht nur als Prüfinstrument zu nutzen, sondern **selbst als formales Artefakt zu verifizieren** („Meta-Testing“ bzw. *Verification of Specifications*), kombiniert die Qualitätssicherung Methoden aus der formalen Logik mit empirischen Fehlerinjektionen.

Eine Analyse deiner hochgeladenen Test-Suite zeigt, dass du mehrere dieser Verfahren bereits intuitiv eingebaut hast – deckt aber gleichzeitig **konkrete logische Abschwächungen, Widersprüche und strukturelle Anomalien** in den aktuellen Testdateien auf.

---

## 1. Bewährte Methoden zur Prüfung einer Test-Suite (Meta-QA)

| Methode | Prüffrage an die Test-Suite | Formales Äquivalent in `qb-cubie` ($\{P\} S \{Q\}$) |
| --- | --- | --- |
| **Konsistenz- & Subsumtionsanalyse** | Widersprechen sich Vor-/Nachbedingungen oder sind Negativ-Tests durch Positiv-Tests bereits logisch impliziert? | Prüfung auf $Q_1 \land Q_2 = \bot$ bei deterministischem $S$ sowie Subsumtion $Q_{\text{pos}} \implies \neg Q_{\text{neg}}$

 |
| **Relationale Kopplungsprüfung** | Prüft ein Multi-Input/Multi-Output-Test wirklich die Bijektion $P_i \mapsto Q_i$ oder nur eine schwache Disjunktion? | Unterscheidung zwischen $\bigwedge_i \{P_i\} S \{Q_i\}$ und $\forall i: \{P_i\} S \{\bigvee_j Q_j\}$

 |
| **Vacuous-Truth-Detektion** | Kann ein Test grün werden, obwohl das Zielsystem aus einem völlig anderen Grund abstürzt oder nichts tut? | Isolierte `expect=False`-Assertions ohne positiven Ankerzustand $Q_{\text{pos}}$

 |
| **Mutation Testing & Fault Injection** | Schlagen die Tests garantiert fehl, wenn im Produktionscode oder im Test-Wächter eine Bedingung invertiert wird? | Gezielte Mutanten im Code (z. B. via `mutmut` / AST-Mutatoren) oder synthetische Fehlsonden (*Probes*)

 |
| **Metamorphe & Isomorphe Prüfung** | Liefern zwei unterschiedliche Repräsentationen desselben Problems identische Prüf-Traces? | Kommutative Diagramme über Funktoren $F(S_M(x)) == S_P(G(x))$

 |
| **Collection- & Umgebungs-Hygiene** | Gehen Tests durch Filter verloren oder spalten konkurrierende Imports (`sys.modules`) die Typidentität? | Meta-Tests über `pytest --collect-only`, Marker-Prüfung und AST-Import-Linter

 |

---

## 2. Was deine Suite bereits als Gold-Standard umsetzt

Bevor wir auf die Widersprüche schauen: Deine Suite enthält bereits vier Musterbeispiele für echte Meta-Verifikation:

* **Wächter-Selbsttests (Fault-Injection Probes)**: In `test_lint.py` verlässt sich `test_src_lint` nicht blind auf `returncode == 0`, sondern `test_linter_detects_regressions` injiziert vorab synthetischen Dead-Code (`W0101`, `[unreachable]`) und undefinierte Namen (`F821`), um zu beweisen, dass die Linter-Subprozesse überhaupt scharf geschaltet sind.


* **Audit-Hook-Verifikation vor Vertragsprüfung**: In `test_offline_core.py` prüft `test_offline_guard_detects_forbidden_operations` mit sechs gezielten Negativ-Sonden (`uv`, `pip`, `dns`, `tcp`, `udp-ipv6`, `python-child`), dass der `sitecustomize.py`-Hook Verstöße tatsächlich abfängt, bevor `test_core_feature_requires_no_install_or_network` die eigentlichen Features testet.


* **Metamorphe Isomorphie-Prüfung**: `tests_services/test_doc_ensurance_isomorphism.py` überführt Markdown-Dokumente via `_md_to_literate_py` in Python-AST-Module und beweist über `PyDocstringPattern`, dass beide Domänen unter `DocEnsurance` kommutieren (`md_summary == py_summary`).


* **Collection-Vertragsschutz**: `test_default_collection_contract.py` sichert per Subprozess (`--collect-only -o addopts=`) ab, dass historische Testfälle nicht stillschweigend durch Dateiumbenennungen aus der Standard-Collection fallen.



---

## 3. Konkrete Befunde & Widersprüche in deiner aktuellen Test-Suite

Wendet man die oben genannten formalen Prüfmethoden systematisch auf dein hochgeladenes `tests/`-Archiv an, treten **sieben konkrete Schwachstellen bzw. Widersprüche** zutage:

### Befund 1: Die Kreuzprodukt-Falle (Disjunktive Abschwächung bei `pre=[...]` und `post=[...]`)

* **Betroffene Dateien**: Nahezu alle Module in `tests_services/`, u. a. `test_doc_rules.py`, `test_doc_ensurance_configs.py`, `test_doc_ensurance_edge_cases.py`, `test_doc_rule_edge_cases.py` und `test_doc_ensurance_isomorphism.py`.


* **Mechanismus**: Wenn du mehrere Vorzustände $P_1, \dots, P_n$ aus **verschiedenen Äquivalenzklassen** in `pre=[...]` und deren jeweils erwartete (paarweise disjunkte) Ergebnisse $Q_1, \dots, Q_n$ in `post=[...]` desselben `EBT`-Aufrufs packst, bildet `EBT` das kartesische Produkt $n \times m$ (in `test_offline_core.py` explizit über `len(trace.traces) == 4` bei $2 \times 2$ bestätigt).


* **Logischer Defekt**: Da eine deterministische Funktion für $P_1$ niemals gleichzeitig zwei disjunkte Ergebnis-Dictionaries $Q_1 \neq Q_2$ liefern kann, muss `EBT` positive `post`-Zustände pro `pre`-Zustand **existenziell (als Disjunktion $\bigvee_j Q_j$)** auswerten, damit der Lauf grün wird. Statt der scharfen Bijektion $\bigwedge_{i=1}^n \{P_i\} S \{Q_i\}$ prüft der Test nur noch die massiv schwächere Aussage $\forall i: \{P_i\} S \{Q_1 \lor \dots \lor Q_n\}$.


* **Konkretes Beispiel für einen blinden Fleck**: In `test_doc_rules.py` (`test_ebt_cubie_doc_rules_preset_clean_and_multi_warning_execution`) stehen `clean_doc` und `noisy_doc` gemeinsam in `pre`, während `post` sowohl `{"warning_count": 0, "rule_ids": []}` als auch `{"warning_count": 2, "rule_ids": ["DOC-NO-OUTPUT", "DOC-LARGE-OUTPUT"]}` enthält. Wenn `CUBIE_DOC_RULES` durch einen Bug komplett ausfällt und für `noisy_doc` ebenfalls `warning_count: 0` liefert, matcht `noisy_doc` einfach `post[0]` (`clean_doc`) – und der Test wird trotz kaputter Regel-Engine **grün**!


* **Sichtbare Arity-Asymmetrie**: In `test_doc_ensurance_configs.py` (`test_ebt_exclude_prefix_collision_and_root_name_excludes`, Zeile 214–236) hat `pre` **3** Elemente (`("docs",)`, `("/",)`, `("",)`), `post` aber **2** Elemente (`session_count: 3` und `session_count: 4`). Zudem erzwingt ein $4 \times 4$-Aufruf wie in `test_doc_ensurance_isomorphism.py` 16 schwere Arena-Läufe, von denen 12 ($N(N-1)$) konstruktionsbedingt fehlschlagen müssen.


* **Lösung**: `pre=[P1, P2, ...]` nur dann bündeln, wenn alle $P_i$ in **dieselbe Äquivalenzklasse** fallen (also exakt denselben `post=WorldState(...)` teilen), oder in `EBT` einen expliziten paarweisen Modus (z. B. Bijektions-/Zip-Semantik für Tupel `(P_i, Q_i)`) einführen.



### Befund 2: Isolierte `expect=False`-Tests ohne positiven Anker (*Vacuous Pass*)

* **Betroffene Stelle**: `tests_services/test_doc_rule_edge_cases.py` in `test_ebt_lazy_list_continuation_alert_and_html_comment_traps` (Zeile 356–374).


* **Mechanismus**: Drei Dokumente (`_LAZY_LIST_CONTINUATION_DOC`, `_GITHUB_ALERT_PRE_DOC`, `_HTML_COMMENT_DISPLACES_PRE_DOC`) werden ausschließlich gegen `expect=False` auf zwei hochspezifische Fehler-Tupel geprüft (`diagnostics: [("DOC-PRE", "error", 4)]` und `[("DOC-PRE", "error", 5)]`).


* **Logischer Defekt**: Es fehlt jede positive Nachbedingung (`passed: True`, `outputs: [["123"]]` bzw. `[["1"]]`). Wenn der Scanner für diese Dokumente weiterhin fehlschlägt – aber z. B. mit Zeilennummer `3` statt `4` oder mit `DOC-EXEC` –, ist die Bedingung „Ergebnis ist nicht `('DOC-PRE', 'error', 4)`“ trivial erfüllt (*Vacuous Pass*).


* **Ursache (aus den `.pyc`-Artefakten rekonstruierbar)**: In der älteren `test_doc_rule_edge_cases.cpython-313.pyc` war dieser Test noch ein positiver Bug-Reproduktionstest (TGD Red-Phase); beim Übergang in die Green-Phase wurde lediglich `expect=False` ergänzt, ohne das eigentliche Soll-Gesetz (`passed: True`) zu verankern. (In `test_doc_ensurance_configs.py` Zeile 206 vs. 240 blieb das Red-Phase-Relikt mit `expect=False` sogar unter exakt derselben `custom_id="doc_config_exclude_subpath_no_basename_collision"` neben dem neuen Positiv-Test stehen.)



### Befund 3: Logische Subsumtion bei redundanten `expect=False`-Klauseln

* **Betroffene Stellen**: `tests_services/test_doc_linter_feedback.py` (Tests 1, 2, 3, 4, 5) sowie `tests_services/test_doc_rules.py` (`test_ebt_high_complexity_fails_on_oversized_qa_guide_example`).


* **Logischer Defekt**: In `test_ebt_ast_and_cst_linter_preserve_concrete_messages_and_lines` prüft `post[0]` für eine deterministische Funktion exakt `diagnostics: [("ARCH-NO-EVAL", "error", 5, "eval() verletzt die Sicherheitsarchitektur.")]`. Gleichzeitig prüfen `post[1]` und `post[2]` mit `expect=False`, dass die Meldung am selben Punkt nicht `""` und nicht `"ARCH-NO-EVAL"` lautet.


* **Auswirkung**: Da $Q_{\text{pos}}(y) \implies \neg Q_{\text{neg}}(y)$ für jede deterministische Abbildung gilt, fügen `post[1]` und `post[2]` **null logische Schärfe** hinzu, verdreifachen aber die Anzahl der `TempFS`-/Linter-Durchläufe. `expect=False` ist nur dort informationshaltig, wo $Q_{\text{pos}}$ bewusst partiell/abstrakt bleibt oder $S$ nicht-deterministisch ist.



### Befund 4: Vertragsbruch zwischen `README.md`, `conftest.py` und `test_styleguide.py`

* **Betroffene Stellen**: `README.md` (Abschnitt „Schnellstart“ & „Verfügbare Marker“), `conftest.py` (`FILE_MARKERS`) und `test_styleguide.py` (Zeile 82).


* **Widerspruch**: Laut `README.md` führt `pytest` bzw. `make test` standardmäßig nur schnelle Tests (`not slow`) aus, während schwere Doku-Ausführungstests über Profile oder CI zugeschaltet werden. In `test_styleguide.py` ist der Marker `#@pytest.mark.slow` über `test_docs_code_examples()` jedoch **auskommentiert**.


* **Auswirkung**: Da `test_styleguide.py` in `conftest.py` nur mit `("meta", "lint")` eingetragen ist, greift in `pytest_collection_modifyitems` der Fallback `if "slow" not in existing and "fast" not in existing: item.add_marker(pytest.mark.fast)`. Damit wird der komplette Repository-weite `DocEnsurance`-Lauf über alle Markdown-Dateien heimlich als **`fast`** eingestuft und bei jedem schnellen Dev-Lauf ausgeführt.



### Befund 5: Gespaltener Modul-Namespace (`src.qb_cubie` vs. `qb_cubie`) & Bitrot in `@pytest.mark.skip`

* **Betroffene Stellen**: `test_headless_reviewer.py`, `test_rbt_reporter.py` und `test_rbt_demo.py` vs. alle übrigen Testdateien.


* **Widerspruch**: `conftest.py` hängt `PROJECT_ROOT / "src"` in `sys.path` ein, sodass das Paket als `qb_cubie` importiert wird. Drei Dateien importieren jedoch über `from src.qb_cubie...` – und `test_rbt_demo.py` mischt sogar beide Pfade direkt untereinander (`import qb_cubie.rbt` in Zeile 1, `from src.qb_cubie.rbt import RBT` in Zeile 2).


* **Auswirkung**: Python legt in `sys.modules` zwei getrennte Modulbäume (`qb_cubie.*` und `src.qb_cubie.*`) mit doppelten Klassenobjekten an, wodurch `isinstance`- und `is`-Prüfungen über Modulgrenzen hinweg scheitern (`src.qb_cubie.protocols.ReviewData is not qb_cubie.protocols.ReviewData`). Zudem übergibt `test_rbt_demo.py` die uninstanziierte Klasse `reviewer=qb_cubie.rbt.HumanReviewer` statt einer Instanz `HumanReviewer()`, was nur deshalb unbemerkt bleibt, weil der Test dauerhaft auf `@pytest.mark.skip` steht.



### Befund 6: Nicht-Monotonie im Regel-Vertrag & Lokales Fixture-Shadowing

* **Nicht-Monotonie in `test_doc_rule_edge_cases.py**`: In `test_ebt_rule_defaults_reduction_and_type_coercion` ist als positiver Vertrag kodiert, dass `rules=()` die Standardregel `DOC-OUT-MISSING` deaktiviert (`rule_ids: ["DOC-OUT"]`), während die Übergabe einer einzelnen, völlig unabhängigen `CodeRule` (`rules=[custom_noop]`) plötzlich `DOC-OUT-MISSING` wieder aktiviert (`rule_ids: ["DOC-OUT-MISSING", "DOC-OUT", "C1"]`). Hier hat der Test eine Implementierungs-Asymmetrie (`if not rules:` vs. `if rules:`) als vermeintliches Naturgesetz festgeschrieben.


* **Pattern-Shadowing in `test_doc_ensurance.py**`: Die Datei importiert oben `CUBIE_DOC_STYLE` (`min_chars=20`), definiert dann aber ein lokales `CUBIE_PATTERN` mit `min_chars=15` für `run_ensurance()`, während die unteren Tests in derselben Datei `CUBIE_DOC_STYLE` (`min_chars=20`) verwenden.



### Befund 7: Verwaiste und divergierende Bytecode-Artefakte (`__pycache__`)

* Im Wurzel-`__pycache__/` liegt noch `test_readme_examples.cpython-313-pytest-9.2.0.pyc`, obwohl die zugehörige Quelldatei `test_readme_examples.py` im Repository-Root gelöscht wurde.


* In `tests_services/__pycache__/` liegen parallel zwei verschiedene Kompilate pro Modul (`*.cpython-313.pyc` und `*.cpython-313-pytest-9.2.0.pyc`), wobei die `cpython-313.pyc`-Dateien noch ältere Docstrings und Assertions enthalten (z. B. `IsolatedScope` statt `TaggedScope` in `test_doc_ensurance_rules` oder `HighComplexity` als Warning statt Error in `test_doc_rules`).



---

## 4. Wie du diese Prüfungen als automatisiertes Meta-Gate in `qb-cubie` verankerst

Da du in `qb-cubie` bereits `CstLinter`/`AstLinter` und `test_meta` (`make test-meta`) besitzt, kannst du genau diese Konsistenzprüfungen als **statische und dynamische Meta-Verträge** direkt in die Suite einbauen:

1. **CST-Regel für Import-Kanonizität (`MetaImportRule`)**: Eine kleine `CstRule` über `tests/`, die jeden Import der Form `from src.qb_cubie...` oder `import src.qb_cubie...` als Architekturverstoß meldet und ausschließlich `qb_cubie` erzwingt.


2. **EBT-in-EBT-Invariante gegen Disjunktions-Abschwächung**: Eine Prüfung im `EBT`-Runner (oder als Linter-Regel auf Testdateien), die anschlägt, sobald in einem `EBT`-Aufruf `len(pre) > 1` und `len([q for q in post if q.expect]) > 1` gleichzeitig auftreten, ohne dass ein expliziter `zip`/`pairwise`-Modus deklariert wurde.


3. **Verbot isolierter Negativ-Spezifikationen (No-Lonely-Negation-Guard)**: Eine Prüfung, dass ein `EBT`-Aufruf, dessen `post`-Liste *ausschließlich* aus `expect=False`-Zuständen besteht, mindestens einen positiven Typ-/Struktur-Vertrag enthalten muss (oder explizit als Negativ-Invariante markiert wird).


4. **Marker-Vertragstest in `test_default_collection_contract.py**`: Ergänze einen Check, der verifiziert, dass schwere Integrationsläufe wie `test_docs_code_examples` in der Default-Collection tatsächlich das Marker-Attribut `slow` tragen und nicht durch den Auto-Tagger in `conftest.py` auf `fast` zurückfallen.



Sollen wir als Nächstes die paarweise Zuordnung (`pre`/`post`-Kopplung) im `EBT`-Runner näher betrachten oder zuerst die gefundenen Widersprüche in `tests_services/` und `test_styleguide.py` glattziehen?

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->

---

---

<div align="center">

![Cubie](./docs/.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](./docs/GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./docs/GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./docs/GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./docs/GUIDE_Quantifiers.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./docs/services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](./docs/core/README.md)  
[↦ | Entwicklerübersicht & Internals | ↤](./docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Hintergrund & Essays | ↤](./docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
