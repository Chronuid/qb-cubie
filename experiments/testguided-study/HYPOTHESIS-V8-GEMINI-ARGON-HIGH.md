# **Ursachenanalyse und Hypothesensystem zu Agentendesign v8 (Grundlage für Generation v9)**


**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Gemini-App (Konversation)
- **Modell:** Gemini-4-Argon
- **Reasoning-Effort:** High
- **Analysedatum:** 12. November 2026 (~03:25 Uhr)
- **Untersuchter Pilotlauf:** [`runs/20261112-015457`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/runs/20261112-015457) (`fastapi_9425`, Seed 42, Modus `cubie`, Run-ID `0001` bei Call 74)

---

Die Auswertung der beiden Live-Monitor-Protokolle aus dem laufenden `v8`-Piloten (`job-12` und `job-20`) zeigt, dass die Verkürzung der Rollenprompts und die direkte Übergabe (`finish`) den initialen Orientierungs-Lock-in aus `v6`/`v7` durchbrochen haben, das System nun aber an zwei neuen strukturellen Barrieren scheitert: **epistemischer Amnesie beim Rollenwechsel** und **fehlertoleranzfreier Schema-Validierung**.

---

**1. Empirischer Befund aus dem v8-Lauf (`job-12` bis `job-20`)**

* **Teil-Erfolg (Funktionierender Rollenwechsel & Ziel-Lokalisierung):** Der Analyse-Agent schloss die initiale Orientierung erfolgreich ab und übergab an QA. Auf die gezielte Rückfrage von QA (`job-12`) lokalisierte der Analyse-Agent in `fastapi/dependencies/utils.py` (Zeilen 253–280) mit `get_typed_return_annotation` und `get_typed_annotation` (`file-15`, `file-17`) exakt die für `fastapi_9425` relevante Produktionslogik.


* **Fehlerbild A – Epistemische Amnesie zwischen Aufträgen (`materials: []`):** Obwohl der Analyse-Agent in `job-12` den exakten Zielcode (`file-15`, `file-17`) gelesen hatte, gingen diese Fundstellen beim Abschluss des Informationsauftrags verloren. Als QA 300 Sekunden später in `job-20` erneut nach derselben Logik fragte, enthielt der Arbeitskontext weiterhin `"materials": []` und unter `"knowledge"` lediglich den statischen `"visible_baseline"`-Block. Da das 12B-Modell vor dem Auftragsende nicht separat `update_context` aufrief, wurde das gelesene Wissen beim Leeren der Dialoghistorie verworfen.


* **Fehlerbild B – Deterministische Schleife durch die `"cursor": "0"`-Falle:** Im gekürzten `v8`-Systemprompt entfiel die Erklärung des Parameters `cursor`. Das Modell interpretierte das Schema-Feld `cursor` bei `search_content` in `job-12` zunächst als Dateipfad (`"cursor": "fastapi/routing.py"`) und in `job-20` dreimal in Folge als Start-Offset der ersten Seite (`"cursor": "0"`). Weil das Backend jeden dieser Aufrufe strikt mit `status: "cursor_error"` und `hits: []` ablehnte, ohne die erste Trefferseite auszuliefern oder das Weglassen des Parameters zu erklären, verfiel der Agent in eine unproduktive Fehlerschleife.


* **Fehlerbild C – Fehlende Lese-Autonomie zwingt QA in teure Rückfragen:** Da `search_content` und `find_paths` in `v8` wieder exklusiv auf den Analyse-Agenten beschränkt wurden, ist der QA-Agent bei jeder fehlenden Dateireferenz handlungsunfähig und muss über `ask_analysis` komplette Informations-Jobs (`job-12`, `job-20`) auslösen, statt die betreffende Funktion in zwei Schritten selbst nachzuschlagen.


* **Fehlerbild D – Persistenter JSON-Ballast statt Wissenskarte:** Entgegen der `v8`-Spezifikation einer viergeteilten Markdown-Wissenskarte ohne Hashes und Rohtelemetrie besteht `"knowledge"` im tatsächlichen User-Prompt weiterhin aus einem verschachtelten JSON-Dump von `visible_baseline` samt 64-stelligen SHA-256-Hashes und rohen Pytest-Sammlungsfehlern.



**2. Konsolidiertes Hypothesensystem für Agentendesign v9**

* **V9-H1 (Automatische Evidenz-Persistenz statt manueller Kontextpflege):** Ein 12B-Modell kann nicht gleichzeitig Code analysieren und wie ein Buchhalter über separate `update_context`-Aufrufe eine formale Wissensdatenbank pflegen. Wenn der Controller jede per `read_file` gelesene Code-Region und jede erfolgreiche Suche automatisch in ein persistentes, rollenübergreifendes Arbeitsgedächtnis (`materials` / Wissenskarte) übernimmt, verschwindet der Gedächtnisverlust zwischen `orient`, QA, Dev und `information`-Jobs vollständig.


* **V9-H2 (Koerzierende Werkzeug-Affordanz statt strafender Schema-Fehler):** Werkzeuge müssen für kleine Modelle nach dem Robustheitsprinzip (Postel's Law) arbeiten. Wenn `cursor` aus dem Modell-Schema gestrichen wird (oder Werte wie `"0"`, `0`, `""` sowie ungültige Cursor automatisch als Seite 1 ausgeführt werden und ein Dateipfad in `cursor` automatisch als `scope` interpretiert wird), entfallen 100 % der `cursor_error`-Schleifen.
* **V9-H3 (Symmetrische Lese-Autonomie bei strikter Schreib-Gewaltenteilung):** Die Komplexitätsreduktion eines Multi-Agenten-Systems entsteht durch getrennte *Schreib- und Entscheidungszuständigkeiten*, nicht durch künstliche Lesebeschränkungen. Wenn alle drei Rollen (`analysis`, `qa`, `dev`) uneingeschränkten Lese- und Suchzugriff (`find_paths`, `search_content`, `read_file`) besitzen, während Schreibrechte strikt getrennt bleiben (Analyse: Kontext & Review; QA: Testdateien; Dev: Produktionscode), sinkt die Zahl blockierender `ask_analysis`-Schleifen drastisch.


* **V9-H4 (Reine Text-/Markdown-Kontexte ohne Metadaten-Rauschen):** Wenn der User-Prompt statt verschachtelter JSON-Metadaten (`visible_baseline`, `framework_usage`, `versions`-Hashes) ein klar gegliedertes Markdown-Dokument mit (1) Issue, (2) automatisch protokollierten Code-Ausschnitten, (3) aktuellen Testergebnissen und (4) dem konkreten Rollenauftrag übergibt, steigt die Zuverlässigkeit von `finish`-Übergaben und Code-Edits.



**3. Verbindliche Design-Vorgaben für Generation v9**

1. **Zero-Admin Memory (Controller-gestützte Wissenskarte):** Streiche `update_context` als Pflichtaufgabe des Modells. Sobald irgendein Agent `read_file` ausführt, speichert der Controller den gelesenen Dateipfad, Zeilenbereich und Code-Ausschnitt automatisch in den gemeinsamen `materials` des Teams. Bei `finish(summary, ...)` wird der Freitext-Befund des aktiven Agenten direkt an die gemeinsame Markdown-Wissenskarte angehängt und samt den gelesenen Code-Snippets an die nächste Rolle übergeben.
2. **Vereinfachte, fehlertolerante Such- und Lese-Tools für alle drei Rollen:**
* `find_paths(pattern)` und `search_content(scope, query)` stehen **Analyse, QA und Dev** gleichermaßen zur Verfügung.
* Entferne `cursor` aus den Tool-Schemas (liefere stattdessen bis zu 50 kompakte Treffer mit Dateipfad und Zeilennummer; falls das Backend intern `cursor` behält, behandle `"0"`, `""` oder ungültige Werte immer stillschweigend als Seite 1, niemals als `cursor_error`).
* Wenn `scope` in `search_content` leer oder `"."` ist, durchsuche das gesamte öffentliche Repo; wenn `scope` nicht existiert, liefere sofort die ähnlichsten vorhandenen Pfade zurück.




3. **Klare Rollen-Hoheit (Wer darf was schreiben?):**
* **Analyse-Agent:** Startet den Lauf, findet die relevante Produktionsstelle und den Testeinstieg, übergibt per `finish(notes)` an QA. Beantwortet Rückfragen von QA/Dev und führt am Ende das Review zur Abnahme (`verdict="verified"` oder `verdict="rework"`) durch.


* **QA-Agent:** Sieht die von Analyse gelesenen Code-Ausschnitte direkt im Prompt, schreibt mit Hilfe der Cubie-/Pytest-Anleitung den Testfall (`edit_tests` / `create_test_file`), prüft ihn per `collect_tests` und übergibt per `finish(test_targets, notes)` direkt an Dev.


* **Dev-Agent:** Führt `run_tests(targets)` aus, sieht das Rot-Ergebnis, ändert den Produktionscode per `edit_source`, verifiziert Grün auf den Zieltests und gibt per `finish(notes)` an Analyse zur Endabnahme (oder per `request_test_change(reason)` zurück an QA).




4. **Lesbarer Markdown-Arbeitskontext statt JSON-Ledger:** Formatiere den `user`-Prompt für jede Rolle als sauberes Markdown mit klaren Überschriften (`# Issue`, `# Current Role & Task`, `# Discovered Code & Evidence`, `# Latest Test Results`) ohne SHA-256-Hashes und ohne den rohen `visible_baseline`-JSON-Block (reduziere die Baseline-Info auf einen Einzeiler zu bekannten Collection-Fehlern wie `pydantic_settings`).