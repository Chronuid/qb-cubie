<center>

# Die EBT-Klasse

![Cubie](../.assets/cubie-logo-written.png)

`EBT` orchestriert endliche Beispielausführungen. Die [Vertragssemantik](../GUIDE_Contract-Semantics.md) definiert Felder, Match-Regeln und bekannte Fehler zentral. Die Struktur „Ausgangszustand – Operation – Zielmuster“ ist eine Analogie zu Hoare-Tripeln, keine implementierte Beweisführung.

---

</center>

## Konstruktor und Konfiguration

`EBT(target, arena=None, pre=None, post=None, expect=True, custom_id=None, reporter=PytestReporter(), multiprocessing=False, multiprocessors=None, tags=None)` ist das öffentliche Interface.

`target` muss ohne Arena oder mit `TempFS` ein Callable sein; zusätzliche String-Referenzen werden durch den `PyVenv`-Codec aufgelöst. `pre` und `post` akzeptieren `WorldState`, Listen davon oder `None`. `_ensure_list(None)` erzeugt `[WorldState()]`; andere Einzelwerte werden lediglich in eine Liste verpackt. Eine `ConventionMap` oder Inferenz primitiver Werte in `args`, `kwargs` oder `returns` existiert nicht.

`arena` legt die ausführbare Umgebung fest. Ein `pre.arena`-Objekt mit `setup` hat Vorrang. Ein String in `pre.arena` erzeugt keine Arena, sondern überschreibt bei aktiver `PyVenv` den Basispfad. `post.arena` kann einen Vergleichspfad bereitstellen. Beide vorhandenen Arenen sind keine OS-Sicherheitsgrenzen.

`expect` negiert bei `False` das Gesamtergebnis aller Schritte. Es behandelt keine erwarteten Exceptions. `post.expect` kennzeichnet unabhängig davon erlaubte oder verbotene Muster; `pre.expect` steuert diese Auswertung nicht.

`reporter=None` unterbindet Reporter-Assertions. Fehler beim Aufbau, bei der Target-Ausführung oder im Vergleich bleiben möglich. `tags` speichert Metadaten; daraus entstehen keine pytest-Marken. `custom_id` fließt in `_run_id` ein, die beim Konstruktoraufruf und nicht bei jedem `.run()` erzeugt wird.

`multiprocessing=True` delegiert Aufgaben an den `MultiprocessManager`. Übergebene `multiprocessors` werden zur Standardliste aus `PickleProcessor` und `LokyProcessor` hinzugefügt. Ein ausschließlicher eigener Backend-Satz erfordert das explizite Setzen von `engine.MULTIPROCESSORS` vor dem Lauf. Details stehen im [Multiprocessing-Handbuch](DEV-GUIDE_2-4_Multiprocessors.md).

## Pipeline

1. `_arrange()` normalisiert `fs` in den übergebenen Zustandsobjekten. Diese Objekte werden dabei verändert. Es erfolgt keine umfassende Validierung aller Deklarationen.
2. `_validate()` führt die Aufgaben sequenziell oder über das Multiprocessing-Modul aus. `_build_context()` bündelt Konfiguration in einem `EBTContext`. Obwohl dieser `frozen=True` ist, bleiben enthaltene Listen, Sets und Objekte veränderlich; es gibt keine tiefe Zustandsisolation.
3. `_process_single_task()` wählt die aktive Arena und ruft `_execute_step()` auf. Ohne Arena wird das Target direkt aufgerufen. Mit Arena folgen `setup`, `execute` und `get_state`.
4. `_evaluate_step()` vergleicht das eine Ergebnis gegen jeden `post`-Zustand und erzeugt je Vergleich einen `EvaluationTrace`. Der rohe Match berücksichtigt noch nicht, ob das Zielmuster verboten ist.
5. Die Arena wird nach dem Vergleich aufgeräumt, auch bei Fehlern. Ein zusätzlicher Aufräumfehler wird der ursprünglichen Exception als Notiz hinzugefügt. Pfade in Traces sind danach keine persistenten Artefakte.
6. `_report()` ruft `_evaluate_run()` auf und übergibt den `RunTrace` an den Reporter. Bei regulärem Abschluss liefert `run()` diesen Trace zurück.

## Aggregation

Die Traces werden nach Eingangsschritt gruppiert. Pro Schritt muss mindestens ein positives Muster passen, sofern positive Muster existieren, und kein negatives darf passen. Danach werden die Schritte mit UND verknüpft. `EBT.expect=False` negiert dieses Endergebnis. Alle Eingänge teilen dieselbe Zielmenge; eine Zuordnung von `pre[i]` zu `post[i]` entsteht nicht.

Leere Zustandslisten können derzeit ohne Vergleiche erfolgreich erscheinen. Wiederholte Läufe derselben Instanz sammeln alte `_outcome`- und `_traces`-Einträge weiter und können neue Fehler verdecken. Verwende eine frische EBT-Instanz je Ausführung. Die Listen in bereits zurückgegebenen `RunTrace`-Objekten sind keine stabilen historischen Momentaufnahmen.

## Vergleiche und Diagnosen

`_calculate_diffs()` aktiviert Rückgabevergleiche derzeit nur für `post.returns is not None`. Für einen echten `None`-Sollwert ist ein Prädikat nötig. `arena` und `fs` werden nur bei wahrheitswertig gesetzten Feldern verglichen. Ein leerer Zustand prüft damit keine Ergebnismerkmale.

`_compare()` unterstützt `Any`, Unions, Typen, Regex, Callables und verschachtelte Container. Die exakten Regeln stehen in der Semantikreferenz. `EvaluationTrace.diffs` enthält Abweichungen für Rückgaben, Dateien und Arena-Vorlagen. Der Standardreporter kann Details falscher Rückgaben mit falschem Wahrheitswert auslassen, obwohl diese verglichen wurden.

`FS_IGNORES` startet mit `{""}` und filtert Pfadsegmente im rekursiven Dateiscan. `ARENA_IGNORES` enthält unter anderem `bin`, `Scripts`, `pyvenv.cfg` und `__pycache__`; der Arena-Scan ignoriert zusätzlich `.pyc` und `.dist-info`. Diese Ausschlüsse verändern den Prüfbereich und garantieren weder Reproduzierbarkeit noch semantische Gleichheit. Leere Unterverzeichnisse werden im rekursiven Scan nicht erfasst.

---

---

<center>

![Error while trying to load the image](../.assets/cubie-small.png)

## Dokumentation

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](../GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](../GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](../GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](../GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](../GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](../GUIDE_Linter.md)  

[↦ | Entwicklerübersicht EBT | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>
