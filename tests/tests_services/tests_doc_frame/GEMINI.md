
## 1. Leitprinzipien aus `GUIDE_Quality-Assurance.md` (Vorrang vor alten Test-Mustern)

* **Strikte Paar-Zuordnung statt Quantoren-Falle:** In einigen älteren Tests aus `tests_doc_ensurance` wurden mehrere unterschiedliche Eingaben in `pre` und verschiedene erwartete Ergebnisse in `post` innerhalb eines einzigen `EBT`-Aufrufs kombiniert. Da `GUIDE_Quality-Assurance.md` dies ausdrücklich als gefährliches Anti-Pattern (Unterspezifikation durch „Jeder gegen Jeden“-Prüfung) einstuft, wird dieses Muster im neuen Modul komplett vermieden.


* **Ein Vertrag pro Wertepaar:** Führen verschiedene Eingaben zu unterschiedlichen Ausgaben, bekommt jedes Paar entweder eine eigene kleine Test-Funktion oder wird über `@pytest.mark.parametrize` als Einzelvertrag ausgeführt.


* **Gezielter Einsatz von `pre`-Listen:** Mehrere `WorldState`-Einträge in `pre` werden nur dann in einem `EBT`-Aufruf gebündelt, wenn für alle Eingaben exakt dasselbe Zielmuster in `post` gilt (etwa wenn fünf verschiedene Fehleingaben alle denselben `STATE-GUARD` werfen oder mehrere Dokumente alle fehlerfrei mit `passed=True` durchlaufen).


* **Klare Trennung von Soll-Gesetz ($Q_{\text{Soll}}$) und Ist-Beobachtung ($Q_{\text{Ist}}$):** Da `DocFrame` neu entwickelt wird, formulieren alle Tests in der Red-Phase direkt das gewünschte Zielverhalten (`expect=True`) und werden nach dem Einrichten nicht mehr nachträglich weichgespült.


* **Orthogonale Prüf-Schichten und Styleguide-Treue:** Alle Datei-Operationen laufen isoliert in `TempFS`, während die Test-Funktionen selbst die Cubie-Styleguide-Grenzen einhalten (maximal 12 Zeilen pro Funktion, einzeilige englische Docstrings, Top-Down-Lesbarkeit).



---

## 2. Modul-Aufbau und zustandsfreie Test-Adapter (`Stateless Adapters`)

* **Synthetischer Projekt-Baum als Basis-Fixture:** Angelehnt an `_seed_project_tree` aus `test_doc_ensurance_configs.py` erzeugt eine kompakte Hilfsfunktion im temporären Workspace (`TempFS`) eine realistische Mini-Struktur mit `../../../pyproject.toml`, `README.md`, `docs/.assets/`, `docs/GUIDE_*.md`, `docs/services/`, `docs/dev/` und `docs/misc/`.


* **Adapter 1 – Katalog-Inspektor (Pass 1):** Ein kurzer, zustandsfreier Adapter (5 bis 12 Zeilen) startet den Katalog-Scan über das Test-Verzeichnis und gibt ein flaches Dictionary mit den erkannten `DocMeta`-Werten (`title`, `label`, `summary`, `order`, `routable`) zurück, damit die `WorldState`-Vergleiche frei von internem Objekt-Ballast bleiben.


* **Adapter 2 – `DocFrame.update()`-Runner (Pass 2):** Ein zweiter Adapter führt `DocFrame.update()` im `TempFS` aus und gibt die aktualisierten Rahmen-Abschnitte (`head`, `router`, `foot`) sowie den Rumpf-Text der Zieldateien als einfaches Dictionary zurück.


* **Adapter 3 – `DocEnsurance`-Diagnose-Prüfer:** Analog zu `_run_rules_scenario` aus `test_doc_ensurance_rules.py` ruft ein dritter Adapter `DocEnsurance` mit `CUBIE_DOCFRAME_RULES` und `reporter=None` auf und projiziert den `DocReport` auf `{"passed": report.passed, "diagnostics": [(d.rule_id, d.severity, d.file_path) ...]}`.



---

## 3. Geplante Äquivalenzklassen und Kantenfälle

* **Äquivalenzklasse 1 – Pass 1: Zero-Config-Extraktion & `DocumentCatalog`:**
* *Positiv-Invarianz (Standard-Extraktion):* Prüft, dass der Scanner aus einem `zone="head"`-Block automatisch den `# H1-Titel` als Label und den ersten Textabsatz unter dem Banner als Kurzbeschreibung (`summary`) für Index-Tabellen ausliest.


* *Vorrang expliziter Attribute:* Prüft, dass optionale Angaben wie `label="..."` und `order="10"` im öffnenden `<!-- qb:frame ... -->`-Kommentar den H1-Titel und die alphabetische Sortierung überschreiben, während `../../../README.md` ohne `order` immer an erster Stelle steht.


* *Kantenfall `routable="false"` & Excludes:* Stellt sicher, dass Dokumente mit `routable="false"` zwar selbst aktualisiert werden, aber in keinem fremden Router auftauchen, und dass `excludes` (sowie `DEFAULT_EXCLUDES` wie `.venv`) analog zu `test_doc_ensurance_configs.py` sauber ignoriert werden.




* **Äquivalenzklasse 2 – Pass 2: Relatives Pfad-Routing & Dynamische Router-Bausteine:**
* *Tiefen-Auflösung:* Prüft, dass Links und Banner-Pfade je nach Verzeichnistiefe (`../../../README.md` in der Wurzel vs. `docs/GUIDE.md` vs. `docs/dev/services/DEV.md`) exakt mit `./`, `../` oder `../../` berechnet werden.


* *Dynamisches Entdecken mit `FolderRouter`:* Beweist, dass eine neu angelegte Datei (wie `docs/GUIDE_New.md`) beim Aufruf von `DocFrame.update()` ohne Änderung an Python-Listen sofort in allen Fußzeilen verlinkt wird.


* *Kontext-abhängiger `SiblingRouter`:* Prüft, dass der Footer auf oberster Ebene (`../../../docs`) nur die Bereichs-Hubs anzeigt, aber innerhalb eines Unterordners (z. B. `docs/dev/` oder `docs/misc/`) automatisch alle Nachbardokumente dieses Unterordners aufklappt.




* **Äquivalenzklasse 3 – Die drei Rahmen-Presets & Slot-Schutz bei `DocFrame.update()`:**
* *`CUBIE_DOC_FRAME_1` (Guides):* Prüft, dass `head` und `foot` (mit `<div align="center">` und `alt="Cubie"` statt des alten Fehler-Alt-Textes) aktualisiert werden, während der `# Titel`, der Erklärungstext, ein vorhandener `DisclaimerSlot` und der gesamte Text außerhalb der Rahmen-Kommentare unverändert bleiben.


* *`CUBIE_DOC_FRAME_2` (Provenance-Berichte):* Prüft, dass `env`, `model` und `effort` aus dem Kommentar-Tag synchronisiert werden, während optionale Slots (`TitleSlot`, `PromptSlot`) und manuelle Zusatzpunkte (wie `Analysedatum`) erhalten bleiben.


* *`CUBIE_DOC_FRAME_3` (`zone="router"` für Index-Dokumente):* Prüft, dass der `CatalogRouter` in `../../../README.md`-Dateien veraltete Tabellen (`mode="table"`) oder Link-Listen (`mode="links"`) inklusive Kurzbeschreibung komplett neu aufbaut, ohne manuellen Fließtext vor oder nach dem Router-Block zu löschen.


* *Idempotenz-Gesetz:* Ein zweiter Lauf von `DocFrame.update()` direkt nach einem erfolgreichen Update darf keinerlei Dateiänderungen mehr erzeugen.




* **Äquivalenzklasse 4 – Prüfregeln in `DocEnsurance` (`CUBIE_DOCFRAME_RULES`):**
* *`DOCFRAME-MISSING` (`error`):* Schlägt an, wenn einer nicht-exkludierten Markdown-Datei der `head`- oder `foot`-Block fehlt oder einer `CUBIE_DOC_FRAME_3`-Datei der `zone="router"`-Block fehlt.


* *`DOCFRAME-OUTDATED` (`error`):* Schlägt an, sobald eine neue Markdown-Datei im Ordner liegt oder ein Link/Alt-Text im Rahmen veraltet ist, `DocFrame.update()` aber noch nicht ausgeführt wurde.


* *`DOCFRAME-BROKEN-ROUTE` (`error`):* Schlägt an, wenn ein im Rahmen verlinktes Dokument oder ein `banner="..."`-Bild in `.assets/` physisch fehlt.


* *`DOCFRAME-PROVENANCE-INCOMPLETE` (`error`):* Schlägt an, wenn in einem `CUBIE_DOC_FRAME_2`-Dokument eines der Pflichtfelder (`Plattform / Umgebung`, `Modell`, `Reasoning-Effort`) leer bleibt oder fehlt.


* *Orthogonalität der Schichten:* Prüft analog zu `test_doc_linter_feedback.py`, dass ein gemeinsamer Lauf von `DocEnsurance` mit `CUBIE_DOC_STYLE`, `CUBIE_DOC_RULES` und `CUBIE_DOCFRAME_RULES` sowohl Rahmenfehler als auch kaputte Python-Beispiele gleichzeitig meldet, ohne dass eine Schicht die andere stummschaltet.




* **Äquivalenzklasse 5 – Explizite `STATE-GUARD`s (Schutz vor Fehlkonfiguration):**
* *Ziel- und Pfad-Guards:* Nicht existierende Pfade lösen vor jedem Datei-Zugriff einen `FileNotFoundError("STATE-GUARD: ...")` aus, falsche Ziel-Typen einen `TypeError("STATE-GUARD: ...")` und komplett leere/ausgeschlossene Ordner einen `ValueError("STATE-GUARD## 1. Leitlinien für den Modul-Aufbau (Vorrang für `GUIDE_Quality-Assurance.md`)


* **Strikte Vermeidung des Quantoren-Anti-Patterns:** In einigen bestehenden Tests aus `doc_ensurance` werden mehrere unterschiedliche Eingaben in `pre` und mehrere unterschiedliche Ergebnisse in `post` innerhalb eines einzigen `EBT`-Aufrufs kombiniert. Laut `GUIDE_Quality-Assurance.md` führt dies zu gefährlicher Unterspezifikation, da `pre` als Allquantor und `post` als Existenzquantor wirkt („Jeder gegen Jeden“).


* **Ein Vertrag pro Wertepaar:** Zusammengehörige Ein-/Ausgabepaare mit unterschiedlichen erwarteten Ergebnissen erhalten im neuen Test-Modul jeweils einen eigenen `EBT`-Aufruf oder werden über `@pytest.mark.parametrize` getrennt geprüft.


* **Bündelung in `pre` nur bei identischem Zielmuster:** Mehrere `WorldState`-Einträge in `pre` werden nur dann in einem gemeinsamen `EBT`-Aufruf zusammengefasst, wenn für alle Eingaben exakt dasselbe Ergebnis in `post` erwartet wird (z. B. wenn mehrere gültige Dokumente alle fehlerfrei mit `passed=True` durchlaufen müssen).


* **Schlanke, zustandsfreie Test-Adapter (`Stateless Adapters`):** Statt komplexe `DocReport`-Objekte oder ganze Dateibäume direkt im Test zu vergleichen, nutzt das Modul kurze Adapter-Funktionen (5 bis 12 Zeilen), die das Ergebnis auf ein einfaches Prüf-Dictionary reduzieren (z. B. `{"passed": ..., "rules": ...}`).


* **Konsequente Umgebungs-Isolation mit `TempFS`:** Da `DocFrame.update()` Dateien verändert und relative Pfade über Ordnerstrukturen hinweg berechnet, laufen alle dateibasierten Tests isoliert in einer `TempFS()`-Arena.


* **Fokus auf Soll-Gesetze ($Q_{\text{Soll}}$) und Red-Phase:** Jeder Testfall definiert vor der Implementierung das gewünschte Zielverhalten (`expect=True`) und schließt bekannte Fehlersymptome (wie veraltete Alt-Texte oder verschluckte Inhalte) bei Bedarf explizit über `expect=False` aus.


* **Einhaltung des Styleguides:** Funktionen im Test-Modul sind maximal 7 bis 12 Codezeilen lang, besitzen einen einzeiligen englischen Docstring (nur das *Was*) und das gesamte Modul überschreitet nicht die Grenze von 300 bis 500 Zeilen.



---

## 2. Aufbau des initialen Test-Moduls (`test_docframe.py`)

* **Kopfbereich mit kompakten Text-Vorlagen (Fixtures):** Am Anfang der Datei werden kurze Markdown-Vorlagen als Konstanten angelegt (z. B. ein Standard-Guide mit `CUBIE_DOC_FRAME_1`, ein Bericht mit `CUBIE_DOC_FRAME_2`, eine Index-Datei mit `CUBIE_DOC_FRAME_3` sowie defekte Dokumente).


* **Hilfsfunktion für den künstlichen Projektbaum (`_seed_docframe_tree`):** Eine kleine Hilfsfunktion legt im temporären Arbeitsverzeichnis (`TempFS`) eine realistische, mehrstufige Ordnerstruktur an (`../../../README.md`, `docs/.assets/`, `docs/GUIDE_*.md`, `docs/services/GUIDE_*.md`, `docs/dev/DEV-GUIDE_*.md`, `docs/misc/README.md` und einen ausgeschlossenen Ordner wie `experiments/`).


* **Adapter 1 – Synchronisations-Prüfer (`_run_docframe_update`):** Führt `DocFrame.update(...)` auf dem Test-Verzeichnis aus und gibt die aktualisierten Textinhalte oder extrahierten Rahmen-Abschnitte als einfaches Dictionary für den `EBT`-Vergleich zurück.


* **Adapter 2 – Diagnose-Prüfer (`_run_docframe_check`):** Führt `DocEnsurance` mit den `CUBIE_DOCFRAME_RULES` und `reporter=None` aus und gibt ein kompaktes Dictionary mit `passed` sowie einer Liste aus `(rule_id, severity, file_path)` zurück.



---

## 3. Geplante Äquivalenzklassen und Prüffälle

### Äquivalenzklasse 1: Zero-Config-Metadaten (`zone="head"`) & Katalog-Aufbau (Pass 1)

* **Automatische Extraktion aus dem Standard-Header:** Prüft, dass `DocFrame` ohne manuelle Python-Listen den `# H1-Titel` als Router-Label und den ersten Textabsatz unter dem Banner als Kurzbeschreibung (`summary`) in den `DocumentCatalog` übernimmt.


* **Überschreiben durch Marker-Attribute:** Prüft durch einen eigenen `EBT`-Vertrag, dass optionale Angaben wie `label="Kurzname"` und `order="10"` im öffnenden `<!-- qb:frame ... -->`-Kommentar den Standard-Titel und die alphabetische Sortierung überschreiben.


* **Sortierungs-Gesetz ohne `order`-Attribut:** Stellt sicher, dass Dateien ohne explizite `order`-Angabe alphabetisch nach Dateinamen sortiert werden, wobei `../../../README.md` immer auf Platz 1 steht.


* **Steuerung über `routable="false"`:** Prüft, dass ein Dokument mit `routable="false"` zwar seinen eigenen Kopf- und Fußrahmen behält, aber nicht automatisch in die Router anderer Dokumente eingespielt wird.



### Äquivalenzklasse 2: Relatives Pfad-Routing & Dynamische Router (Pass 2)

* **Tiefenabhängige Pfad-Auflösung:** Prüft, dass Links auf dieselben Ziele und Banner-Bilder je nach Verzeichnistiefe (`../../../README.md` in der Wurzel vs. `docs/GUIDE_*.md` vs. `docs/dev/services/DEV-GUIDE_*.md`) exakt mit `./`, `../` oder `../../` berechnet werden.


* **Dynamischer `FolderRouter`:** Prüft, dass eine neu angelegte Datei (z. B. `docs/GUIDE_Neu.md`) beim Aufruf von `DocFrame.update()` automatisch in den Fußzeilen aller Dokumente ergänzt wird.


* **Kontext-sensitiver `SiblingRouter`:**
* *Fall A (Hauptverzeichnis `../../../docs`):* Prüft in einem eigenen Testvertrag, dass im Footer eines Haupt-Guides nur die übergeordneten Bereichs-Hubs (`../../../docs/dev`, `docs/misc/`, `docs/feature-drafts/`) angezeigt werden.


* *Fall B (Unterordner wie `../../../docs/dev` oder `docs/misc/`):* Prüft in einem getrennten Testvertrag, dass innerhalb eines Unterordners automatisch alle Geschwister-Dokumente dieses Ordners im Footer aufgeklappt werden.




* **Index-Generierung mit `CatalogRouter` (`zone="router"`):** Prüft für `CUBIE_DOC_FRAME_3`, dass in `../../../README.md`-Dateien sowohl der Tabellen-Modus (`mode="table"` inklusive extrahierter Kurzbeschreibung) als auch der Link-Modus (`mode="links"`) automatisch aus den Dateien des Zielordners generiert werden, ohne die `README.md` selbst aufzulisten.



### Äquivalenzklasse 3: Die drei Presets (`FRAME_1`, `FRAME_2`, `FRAME_3`) & Schutz manueller Inhalte

* **Erhalt geschützter Slots in `CUBIE_DOC_FRAME_1`:** Prüft, dass `DocFrame.update()` die Navigation und den Footer (mit `<div align="center">` und Alt-Text `![Cubie]`) aktualisiert, aber den `# Titel`, den Einführungstext (`HeaderContentSlot`), das gewählte `banner="..."` und den optionalen Disclaimer (`DisclaimerSlot`) niemals überschreibt.


* **Provenance-Verarbeitung in `CUBIE_DOC_FRAME_2`:** Prüft, dass die Attribute `env`, `model` und `effort` aus dem Marker-Tag in die Pflichtfelder übernommen werden, während zusätzliche eigene Aufzählungspunkte (z. B. `Analysedatum`) und der `PromptSlot` vollständig erhalten bleiben.


* **Schutz des Dokumentkörpers (`CUBIE_DOC_FRAME_3` & allgemein):** Beweist, dass sämtlicher manueller Text und manuelle Tabellen außerhalb der `<!-- qb:frame ... -->`-Blöcke bei einem Update zu 100 % unangetastet bleiben.



### Äquivalenzklasse 4: Diagnose-Regeln (`CUBIE_DOCFRAME_RULES`) in `DocEnsurance`

* **Positiv-Test (Synchroner Zustand):** Ein Projektbaum, auf dem zuvor `DocFrame.update()` ausgeführt wurde, besteht den `DocEnsurance`-Lauf mit `CUBIE_DOCFRAME_RULES` komplett ohne Fehler (`passed=True`, `diagnostics=[]`).


* **Einzelverträge für jeden Fehler-Code (`severity="error"`):** Jeder der vier Diagnose-Fälle wird als eigener, klar getrennter `EBT`-Vertrag geprüft:


* `DOCFRAME-MISSING`: Feuert, wenn einer nicht-exkludierten `.md`-Datei der `head`- oder `foot`-Rahmen fehlt oder wenn in einem `CUBIE_DOC_FRAME_3`-Dokument der Block `zone="router"` fehlt.


* `DOCFRAME-OUTDATED`: Feuert, wenn ein neues Dokument im Ordner hinzukam, ohne dass `DocFrame.update()` lief, oder wenn im Footer noch der alte Fehler-Text `![Error while trying to load the image]` steht.


* `DOCFRAME-BROKEN-ROUTE`: Feuert, wenn eine Route oder ein `banner="..."`-Attribut auf eine Datei verweist, die im Workspace nicht existiert.


* `DOCFRAME-PROVENANCE-INCOMPLETE`: Feuert, wenn in einem `CUBIE_DOC_FRAME_2`-Dokument eines der Pflichtfelder (`Plattform / Umgebung`, `Modell`, `Reasoning-Effort`) fehlt oder leer gelassen wurde.




* **Orthogonalität zu `CUBIE_DOC_STYLE` und `CUBIE_DOC_RULES`:** Prüft analog zu `test_doc_linter_feedback.py`, dass ein Rahmen-Fehler (`DOCFRAME-*`) niemals einen gleichzeitigen Fehler in einem Python-Codebeispiel (`DOC-OUT`, `DOC-EXEC`) verschluckt oder stummschaltet.



### Äquivalenzklasse 5: Excludes, Kantenfälle & `STATE-GUARD`-Prüfungen

* **Verzeichnis- und Datei-Excludes:** Prüft analog zu `test_doc_ensurance_configs.py`, dass ausgeschlossene Pfade (wie `excludes=("experiments", "GUTACHTEN.md")` sowie Standard-Excludes wie `.venv`) weder beim Katalog-Scan in Footer aufgenommen noch wegen fehlender Rahmen bemängelt werden.


* **Kantenfälle an Grenzen:** Prüft leere `.md`-Dateien (wie eine 0-Byte-Datei), ungeschlossene `<!-- qb:frame ... -->`-Kommentare ohne schließendes `<!-- /qb:frame -->` sowie Dokumente ohne zweiten Absatz unter dem Banner.


* **Explizite `STATE-GUARD`-Tests mit `ExceptionExpectation`:** Prüft, dass nicht existierende Zielpfade (`FileNotFoundError`), falsche Parametertypen (`TypeError`), unbekannte Frame-IDs oder ungültige Zonen-Namen sofort vor der Ausführung mit einer sprechenden `STATE-GUARD:`-Fehlermeldung abgewiesen werden.


* **End-to-End-Abnahme mit `PytestReporter`:** Prüft in einem separaten Test, dass `DocEnsurance` bei einem `DOCFRAME-*`-Fehler über den Standard-`PytestReporter` einen `AssertionError` mit Dateipfad, Zeilennummer und Regel-ID auslöst.



---

## 4. Geplante Aufteilung bei wachsendem Umfang

* **Start in einer Datei:** Für den ersten Schritt der Red-Phase starten die Kern-Szenarien gebündelt in `tests/tests_services/tests_docframe/test_docframe.py`, um die Basis-Architektur schnell gegenzuprüfen.


* **Sauberer Schnitt entlang des 500-Zeilen-Limits:** Sobald das Modul wächst, wird es analog zu `tests_doc_ensurance` in drei fokussierte Module aufgeteilt:


* `test_docframe_catalog_and_routing.py` (Pass 1, Pass 2, `FolderRouter`, `SiblingRouter`, `CatalogRouter`).


* `test_docframe_presets_and_update.py` (`CUBIE_DOC_FRAME_1` bis `3`, Slot-Schutz und `DocFrame.update()`).


* `test_docframe_rules_and_guards.py` (`CUBIE_DOCFRAME_RULES`, `DocEnsurance`-Integration, Excludes und `STATE-GUARD`s).