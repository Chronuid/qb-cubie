<center>

# `Linter`

![Cubie](../.assets/cubie-logo-written.png)

Diese Entwicklerreferenz beschreibt Aufbau und Schnittstellen der Linter-Integration.

---

</center>

Das Linter-Modul orchestriert die statische Code-Analyse innerhalb des Cubie-Ökosystems. Es abstrahiert die Komplexität externer CLI-Tools (AST) und nativer Python-Syntaxbäume (CST) hinter einer einheitlichen, protokollbasierten Schnittstelle, um Diagnosen verschiedener Werkzeuge einheitlich auszuwerten. Die Analyse bietet keine OS-Sicherheitsgrenze und keinen allgemeinen Korrektheitsnachweis. Bekannte Einschränkungen beschreibt die [Vertragssemantik](../GUIDE_Contract-Semantics.md).

---

## 1. Kern-Datenstrukturen und Verträge

Um die unterschiedlichen Ausgaben und Architekturen diverser Analyse-Tools (von JSON-CLI-Outputs bis hin zu in-memory Syntaxbaum-Besuchen) zu vereinheitlichen, nutzt das Modul standardisierte Verträge und Datentransferobjekte (DTOs).

### 1.1 `LinterDiagnostic` (Das DTO)
Diese `dataclass` ist das universelle Trägerobjekt für alle Linter-Meldungen im System. Unabhängig davon, ob ein Fehler durch einen Regex-Match in Pylint oder durch einen falschen Knoten im CST-Baum ausgelöst wurde – das Resultat wird immer in diese Struktur übersetzt.
* **Geografische Ortung:** `file_path`, `line`, `column` ermöglichen die exakte Lokalisierung im Dateisystem der Arena.
* **Fehler-Metadaten:** `linter_name`, `rule_id`, `message` und `severity` standardisieren die Ausgabe.
* **Topologische Kartographie (AST/CST):** Die Felder `node_type` (z. B. `FunctionDef`) und `node_name` (z. B. `Calculate_Things`) erlauben eine semantische Einordnung des Fehlers, was besonders für automatisierte Refactorings und Agenten wertvoll ist.

### 1.2 `Linter` (Das Protocol)
Das `typing.Protocol` definiert den strikten Ausführungsvertrag (Dependency Inversion) für alle Linter-Backends. Es ersetzt statische Profile durch dynamische, zustandsbehaftete Worker-Klassen. 
* **`name` (Property):** Der Anzeigename des Linters.
* **`register_excludes(excludes: List[str])`:** Eine dynamische Registry-Methode, die es dem Orchestrator erlaubt, dem Linter nachträglich ignorierte Verzeichnisse (z. B. `.venv`) aufzuzwingen, bevor die Analyse startet.
* **`check(target: Union[str, Path]) -> List[LinterDiagnostic]`:** Die ausführende Kernfunktion, die Code-Strings oder Dateipfade analysiert und die normierten Diagnosen zurückgibt.

---

## 2. Die AST-Ebene (Prozessbasierte Analyse)

Die AST-Ebene befasst sich mit klassischen Linter-Tools, die als eigenständige Subprozesse (`subprocess`) auf dem Betriebssystem ausgeführt werden.

### 2.1 `AstLinter` (Der Orchestrator)
Die `AstLinter`-Klasse agiert nicht als eigentlicher Linter, sondern als "Stateful Orchestrator". Sie nimmt über ihren Konstruktor (`*linters`) beliebig viele `Linter`-konforme Backends (als Klassen oder Instanzen) entgegen und steuert deren Lebenszyklus.
* **Auto-Discovery:** Wird der `check()`-Methode kein spezifisches Target übergeben, fällt der AstLinter automatisch auf das aktuelle Arbeitsverzeichnis (`Path.cwd()`) zurück.
* **Konfigurationsprüfung und Grenze:** Der Orchestrator behandelt bereits eine beliebige `pyproject.toml` als native Konfiguration. Deshalb können `DEFAULT_EXCLUDES` auch ohne passende Backend-Einstellungen entfallen. Beim CST-Backend ist das Ausschlussset anfangs leer. Das ist ein offener Implementierungsbefund; Ausschlussmuster sind keine Sicherheitsgrenze.
* **Aggregation:** Iteriert über alle Backends, sammelt deren Ergebnisse und führt sie zu einer einzigen, flachen Liste von `LinterDiagnostic`-Objekten zusammen.

### 2.2 `Pylint` (Das Backend)
Implementiert das `Linter`-Protokoll und startet das Pylint-CLI-Tool als Subprozess mit den Rechten des Aufrufers.
* **Regex-gestützte Excludes:** Registrierte Ausschlüsse werden in `--ignore-paths` übersetzt. Sie filtern den Analyseumfang, entziehen dem Linter-Prozess aber keine OS-Rechte.
* **Rule-Management:** Über den `disable`-Parameter im Konstruktor können spezifische Regeln (wie `C0114`) gezielt abgeschaltet werden.
* **Silent Failure Prevention:** Ein State-Guard überwacht den Subprozess. Stürzt Pylint ohne standardisierte Ausgabe ab, wirft der Worker eine sprechende `RuntimeError`-Exception, anstatt den Fehler zu schlucken.

---

## 3. Die CST-Ebene (Baumbasierte Analyse)

Im Gegensatz zur AST-Ebene analysiert die CST-Ebene (Concrete Syntax Tree) den Python-Code nicht über Subprozesse, sondern zerlegt ihn direkt im Arbeitsspeicher in verlustfreie Syntaxbäume (`libcst`). Dies ermöglicht chirurgische Prüfungen unter Beibehaltung von Kommentaren und Formatierungen.

### 3.1 `CstLinter` (Der Crawler und Parser)
Diese Klasse implementiert ebenfalls das `Linter`-Protokoll, operiert aber nativ im Python-Speicher.
* **Integrierter Directory Crawler:** Da Syntaxbäume nur auf Dateiebene funktionieren, bringt der `CstLinter` einen eigenen rekursiven Crawler (`_crawl_directory`) mit. Dieser löst Ordner-Targets in einzelne Python-Dateien auf, filtert diese rigoros gegen die `_excludes`-Registry und übergibt sie an den Parser.
* **SyntaxError-Grace-Fallback:** Enthält unstrukturierter In-Memory-String-Code (z. B. von LLM-Agenten) fatale Syntaxfehler, stürzt der Linter nicht ab. Er fängt den `cst.ParserSyntaxError` ab und konvertiert ihn on-the-fly in ein valides `LinterDiagnostic`-Objekt der Regel `E999`.

### 3.2 `CstRule` (Der zustandsbehaftete Visitor)
Die Basisklasse für alle individuellen CST-Regeln. Sie erbt von `cst.CSTVisitor` und wandert durch den generierten Syntaxbaum.
* **State-Reset (`reset()`):** Da eine Instanz einer Regel in einem großen Projekt über Hunderte von Dateien iteriert, sorgt diese Methode dafür, dass der interne `diagnostics`-Zustand zwischen den Dateien geleert und der aktuelle `file_path` injiziert wird (Verhinderung von State-Bleeding).
* **Automatisierte Metadaten-Extraktion:** Die Hilfsmethode `add_diagnostic()` nimmt den fehlerhaften `CSTNode` entgegen, extrahiert vollautomatisch über den `PositionProvider` die exakten Zeilen- und Spaltenkoordinaten und injiziert den Node-Typ (z. B. `FunctionDef`) in die finale Diagnose.

---

## 4. Design-Prinzipien

Das Linter-Modul folgt strikt den architektonischen Richtlinien des Cubie-Projekts:
1. **Dependency Inversion:** Der Orchestrator (`AstLinter`) kennt keine Subprozesse oder CLI-Flags. Er kommuniziert ausschließlich über das `Linter`-Protokoll.
2. **Pure Worker & Stateful Orchestrators:** Operative CLI-Aufrufe (Pylint) und Datei-Crawlings (CstLinter) sind in spezialisierten Klassen gekapselt. Die Zustandsmutation (das Registrieren der Excludes) obliegt alleinig der übergeordneten Kompositionsfunktion des AstLinters.
3. **Narrative Programming:** Die Hauptmethoden (`check`) fungieren als reine Inhaltsverzeichnisse (Top-Down-Lesbarkeit) und delegieren die technische Komplexität an kleine, gut benannte Hilfsmethoden (`_resolve_target`, `_propagate_excludes`).
## Aussagegrenzen

Diagnosen gelten für den konfigurierten Analyseumfang und die Fähigkeiten des jeweiligen Backends. Eine leere Liste beweist keine Fehlerfreiheit. MyPy akzeptiert nur Status 0 oder 1 und lehnt unbekannte Ausgabezeilen sowie einen Fehlerstatus ohne erkannte Fehlerdiagnose ab. Absolute Windows-Pfade bleiben in Diagnosen erhalten. Die früheren Prozessstatus- und Parserlücken sind durch [Regressionstests](../../tests/CONTRACT_CASES_9_1.md) abgesichert. Weder ein Linter-Prozess noch seine Ausschlussmuster sind eine OS-Sicherheitsgrenze.

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
