<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Die EBT-Klasse

![Cubie](../.assets/cubie-logo-written.png)

`EBT` orchestriert endliche Beispielausführungen. Die [Vertragssemantik](../core/GUIDE_Contract-Semantics.md) definiert Felder, Match-Regeln und bekannte Fehler zentral. Die Struktur „Ausgangszustand – Operation – Zielmuster“ ist eine Analogie zu Hoare-Tripeln, keine implementierte Beweisführung.

---

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Konstruktor und Konfiguration

`EBT(target, arena=None, pre=None, post=None, expect=True, custom_id=None, reporter=PytestReporter(), multiprocessing=False, multiprocessors=None, tags=None, *, max_workers=None)` ist das öffentliche Interface.

`target` muss ohne Arena oder mit `TempFS` ein Callable sein; zusätzliche String-Referenzen werden durch den `PyVenv`-Codec aufgelöst. `pre` und `post` akzeptieren einen `WorldState`, nichtleere Listen davon, `None` oder ein Quantor-Wrapper-Dictionary `{"quantor": "all" | "exists", "states": ...}`. `_parse_state_config()` normalisiert `None` zu `[WorldState()]` unter dem jeweiligen Standard-Quantor (`pre_quantor="all"`, `post_quantor="exists"`), entpackt Dict-Wrapper über `_parse_quantor_wrapper()` und prüft über `_validate_states()` sowie `_validate_state_expects()` alle Invarianten: Leere Listen, unbekannte/fehlende Wrapper-Schlüssel, ungültige Quantor-Strings sowie `expect=False` in `pre` oder unter `post_quantor="exists"` führen zu `ValueError("STATE-GUARD: ...")`; falsche Container-/Elementtypen oder nicht-boolesche `expect`-Werte zu `TypeError("STATE-GUARD: ...")`. Eine `ConventionMap` oder Inferenz primitiver Werte in `args`, `kwargs` oder `returns` existiert nicht.

`arena` legt die ausführbare Umgebung fest. Ein `pre.arena`-Objekt mit `setup` hat Vorrang. Ein String in `pre.arena` erzeugt keine Arena, sondern überschreibt bei aktiver `PyVenv` den Basispfad. `post.arena` kann einen Vergleichspfad bereitstellen. Beide vorhandenen Arenen sind keine OS-Sicherheitsgrenzen.

`expect` wird über `validate_bool_expect()` strikt auf `type(value) is bool` geprüft und negiert bei `False` das fertige Gesamtergebnis aller Schritte. Es behandelt keine erwarteten Exceptions. `post.expect` kennzeichnet in `post={"quantor": "all", ...}` erlaubte (`True`) oder verbotene (`False`) Muster; unter `post_quantor="exists"` sowie in `pre` wird `expect=False` per `STATE-GUARD` (`ValueError`) abgewiesen. `pre` und `post` sind als Properties implementiert: Eine Attribut-Neuzuweisung (`case.pre = ...`, `case.post = ...`) markiert `_pre_reassigned` bzw. `_post_reassigned`, sodass `_arrange_states()` beim nächsten Lauf den Quantor auf `"all"` bzw. `"exists"` zurücksetzt, sofern kein neuer Dict-Wrapper übergeben wurde.

`reporter=None` unterbindet Reporter-Assertions. Fehler beim Aufbau, bei der Target-Ausführung oder im Vergleich bleiben möglich. `tags` speichert Metadaten; daraus entstehen keine pytest-Marken. `custom_id` fließt in `_run_id` ein, die für jeden `.run()`-Aufruf neu erzeugt wird.

`multiprocessing=True` delegiert Aufgaben an den `MultiprocessManager`. Übergebene `multiprocessors` werden zur Standardliste aus `PickleProcessor` und `LokyProcessor` hinzugefügt. Ein ausschließlicher eigener Backend-Satz erfordert das explizite Setzen von `engine.MULTIPROCESSORS` vor dem Lauf. Details stehen im [Multiprocessing-Handbuch](DEV-GUIDE_2-4_Multiprocessors.md).

`max_workers` akzeptiert `None` oder eine positive Ganzzahl; boolesche Werte und andere Typen führen zu `TypeError`, Zahlen kleiner als eins zu `ValueError`. Die Prüfung erfolgt beim Anlegen und vor jedem Lauf, auch bei sequenzieller Ausführung. Pickle und Loky verwenden höchstens `min(os.cpu_count() or 1, len(pre), max_workers)` Worker; bei `None` entfällt die Benutzergrenze. Die Berechnung erfolgt je Lauf. `post`-Zustände erhöhen die Aufgabenzahl nicht. Ein Limit von eins nutzt weiterhin einen Kindprozess; bei `multiprocessing=False` wird kein Pool angelegt. Das Limit gilt je EBT-Instanz, auch bei pytest-xdist.

## Pipeline

1. `_arrange()` validiert `max_workers` und `EBT.expect`, aktualisiert und prüft über `_arrange_states()` die Zustandslisten samt Quantor-Reset und `expect`-Guards, prüft `validate_exception_contract()` und normalisiert anschließend `fs`. Unterschiedliche Quellen mit gleichem Basename in FS-Kurzformen führen zu `ValueError`; explizite Zielpfad-Mappings lösen die Mehrdeutigkeit auf. Erst nach erfolgreicher Normalisierung aller Zustände werden ihre `fs`-Felder verändert. Fehler verhindern Arena-Aufbau und Target-Ausführung.
2. `_validate()` führt die Aufgaben sequenziell oder über das Multiprocessing-Modul aus. `_build_context()` kopiert die normalisierten Zielmuster und Ignore-Sets vor der Ausführung in einen `EBTContext`. Alle Eingänge verwenden diesen Vertragsstand; Target und Arena bleiben die ausführbaren Instanzen. Funktionen, Closures und externe Ressourcen werden durch `deepcopy` nicht eingefroren.
3. `_process_single_task()` wählt die aktive Arena und ruft `_execute_step()` auf. Ohne Arena wird das Target direkt aufgerufen. Mit Arena folgen `setup`, `execute` und `get_state`. Bei mindestens einem `post.raises`-Vertrag kapselt `CaptureTarget` ausschließlich den Target-Aufruf; Arena- und Transportfehler werden nicht erfasst. Die PyVenv-Codecs übertragen diese Erfassung als explizite Ergebnisstatus und beschreibende Exception-Daten.
4. `_observe_task()` kopiert Vorzustand und Zielmuster vor dem Target-Aufruf. `_evaluate_step()` vergleicht das originale Ergebnis gegen diese kopierten Muster und übernimmt dieselben Muster in den `EvaluationTrace`. Erst danach werden Ergebnis und Traces für die Historie kopiert. Der rohe Match berücksichtigt noch nicht, ob das Zielmuster verboten ist.
5. Die Arena wird nach dem Vergleich aufgeräumt, auch bei Fehlern. Ein zusätzlicher Aufräumfehler wird der ursprünglichen Exception als Notiz hinzugefügt. Pfade in Traces sind danach keine persistenten Artefakte.
6. `_report()` ruft `_evaluate_run()` auf und übergibt den `RunTrace` an den Reporter. Bei regulärem Abschluss liefert `run()` diesen Trace zurück.

## Aggregation

Die Traces werden nach Eingangsschritt gruppiert. Pro Schritt wertet `evaluate_step_logic(traces, self.post_quantor)` die Einzelerfüllungen `sat(t) = t.evaluation if t.post.expect else not t.evaluation` strikt nach `self.post_quantor` aus (`all(results)` bei `"all"`, `any(results)` bei `"exists"` – ohne historische $Q^+$/$Q^-$-Partitionierung und ohne Vacuous-True bei leerer Trace-Liste unter `"exists"`). Danach werden die Schritt-Ergebnisse gemäß `self.pre_quantor` (`all(successes)` bei `"all"`, `any(successes)` bei `"exists"`) verknüpft. `EBT.expect=False` negiert dieses Endergebnis. Alle Eingänge teilen dieselbe Zielmenge; eine Zuordnung von `pre[i]` zu `post[i]` entsteht nicht.

Leere Zustandslisten werden als Konfigurationsfehler abgelehnt. Jeder Lauf setzt Outcomes und Traces zurück und liefert unabhängige historische Momentaufnahmen; siehe [Vertragssemantik](../core/GUIDE_Contract-Semantics.md#Wiederholte-Läufe-und-historische-Ergebnisse).

## Vergleiche und Diagnosen

`_calculate_diffs()` aktiviert Rückgabevergleiche für `post.returns is not UNSPECIFIED`. Der Sentinel ist ein Enum-Mitglied und behält seine Identität beim Kopieren sowie bei Pickle-/Cloudpickle-Serialisierung für Multiprocessing. Explizites `None` wird als Sollwert verglichen. `post.raises` prüft Typ und optionalen Meldungsregex; `returns` und `raises` im selben Zustand sind ungültig. `arena` und `fs` werden nur bei wahrheitswertig gesetzten Feldern verglichen. Ein leerer Zustand verlangt normale Beendigung, prüft aber keine weiteren Ergebnismerkmale.

`_compare()` unterstützt `Any`, Unions, Typen, Regex, Callables und verschachtelte Container. Die exakten Regeln stehen in der Semantikreferenz. `EvaluationTrace.diffs` enthält Abweichungen für Rückgaben, Ausnahmeverträge, FS und Arena-Vorlagen. Der Standardreporter zeigt auch falsy Rückgaben und erwartete/beobachtete Exceptions. `JsonReporter(path)` persistiert abgeschlossene Läufe einschließlich typisierter Werte und Diffs mit `schema_version: 1`; er erhebt selbst keine fachliche Assertion.

`FS_IGNORES` startet mit `{""}` und filtert Pfadsegmente samt Teilbaum im rekursiven Scan. `ARENA_IGNORES` enthält unter anderem `bin`, `Scripts`, `pyvenv.cfg` und `__pycache__`; der Arena-Scan ignoriert zusätzlich `.pyc` und `.dist-info`. Diese Ausschlüsse verändern den Prüfbereich und garantieren weder Reproduzierbarkeit noch semantische Gleichheit. Der Scan erfasst Dateien und Verzeichnisse einschließlich leerer Unterverzeichnisse; verschachtelte Datei-/Verzeichniswechsel zählen als `modified`.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  
[↦ | Review-Based Testing | ↤](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md)  
[↦ | RBT-Klassen | ↤](./DEV-GUIDE_1-1_RBT-Classes.md)  
[↦ | EBT: Entwicklerübersicht | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Die EBT-Klasse | ↤](./DEV-GUIDE_2-1_EBT-Class.md)  
[↦ | WorldState | ↤](./DEV-GUIDE_2-2_WorldState-Class.md)  
[↦ | Arenen und IPC-Codecs | ↤](./DEV-GUIDE_2-3_Arenas.md)  
[↦ | `Multiprocessors` | ↤](./DEV-GUIDE_2-4_Multiprocessors.md)  
[↦ | `Linter` | ↤](./DEV-GUIDE_2-5_Linter.md)  
[↦ | DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes | ↤](./DEV-GUIDE_Next-Steps.md)  
[↦ | DEV-GUIDE: Release-Vorbereitung und sauberer Release | ↤](./DEV-GUIDE_Release-Preparation.md)  
[↦ | DEV-GUIDE: Bugs dokumentieren (`KNOWN_ISSUES.md`) | ↤](./DEV-GUIDE_Write-down-the-bugs.md)  
[↦ | Styleguide | ↤](./Style-Guide.md)  

</div>
<!-- /qb:frame -->
