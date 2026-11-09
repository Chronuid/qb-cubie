<center>

# Linter

![Cubie](.assets/cubie-logo-written.png)

Das Linter-Modul orchestriert die statische Code-Analyse innerhalb des Cubie-Ökosystems. Es abstrahiert die Komplexität externer CLI-Tools (wie Pylint) und nativer Python-Syntaxbäume (CST) hinter einer einheitlichen, protokollbasierten Schnittstelle, um Diagnosen verschiedener Werkzeuge einheitlich auszuwerten. Die Analyse bietet keine OS-Sicherheitsgrenze und keinen allgemeinen Korrektheitsnachweis. Bekannte Einschränkungen beschreibt die [Vertragssemantik](GUIDE_Contract-Semantics.md).

Die Analysewerkzeuge sind optional: `python -m pip install 'qb-cubie[linters]'` installiert LibCST, MyPy und Pylint. Der Paketimport funktioniert auch ohne dieses Extra; beim Aufruf eines fehlenden Werkzeugs erscheint ein Installationshinweis. Eigene ausführbare Dateien lassen sich über `QB_CUBIE_MYPY_PATH` und `QB_CUBIE_PYLINT_PATH` angeben. Für die Repository-Entwicklung installiert `uv sync --locked --group dev` die Werkzeuge aus der Lockdatei.

---

</center>

Dieses Dokument erklärt die typischen Usage-Pattern, zeigt auf, wie das Framework mit Dateisystemen und LLM-Outputs interagiert, und bietet einen Deep-Dive in die Entwicklung eigener Code-Style-Regeln.

---

## 1. Klassische AST-Analyse mit Pylint

Die klassische Code-Analyse basiert auf Subprozessen. In Cubie fungiert der `AstLinter` hierbei als intelligenter "Stateful Orchestrator", der die Lebenszyklen der angehängten Linter-Backends (wie `Pylint`) steuert.

### 1.1 Basis-Nutzung und Auto-Discovery

Das API-Interface agiert agnostisch und akzeptiert nahtlos Objekte vom Typ `Union[str, Path]`. Wird der `.check()`-Methode kein explizites Ziel übergeben (Zero-Config Execution), fällt der Orchestrator automatisch auf das aktuelle Arbeitsverzeichnis (`Path.cwd()`) zurück.

```python
from pathlib import Path
from qb_cubie import AstLinter, Pylint

# 1. Analyse eines gesamten Repositories (Auto-Discovery)
linter = AstLinter(Pylint())
diagnostics = linter.check()

# 2. Gezielte Analyse einer einzelnen Datei
diagnostics_file = linter.check(Path("src/main.py"))

```

### 1.2. Analyseumfang und Ausschlüsse

Ausschlussmuster begrenzen den Analyseumfang, aber keine Zugriffsrechte. `AstLinter` behandelt derzeit bereits die Existenz einer beliebigen `pyproject.toml` als native Konfiguration. Dadurch können `DEFAULT_EXCLUDES` auch ohne passende Backend-Konfiguration entfallen; das Ausschlussset des CST-Backends ist anfangs leer. Prüfe den tatsächlich analysierten Umfang und konfiguriere benötigte Ausschlüsse ausdrücklich. Pylints `--ignore-paths` ist ein Dateifilter und keine OS-Sicherheitsgrenze.

Eine leere Diagnoseliste bedeutet nur, dass der Adapter keine Diagnosen zurückgegeben hat. Der MyPy-Adapter akzeptiert Exitcode 0 (erfolgreiche Analyse) und 1 (Diagnosen). Alle anderen Exitcodes, einschließlich negativer Signal-Codes und Exitcode 2 ohne Ausgabe, lösen einen `RuntimeError` mit Exitcode, Befehl sowie vollständigem stdout und stderr aus. Der Fehler propagiert auch durch `AstLinter` und EBT; er wird nicht als leere Diagnoseliste ausgewertet.

### 1.3 Analyse von In-Memory Strings (LLM-Outputs)

Unstrukturierte Agenten-Ausgaben oder generierter Code aus dem Arbeitsspeicher können direkt als String übergeben werden. In-Memory-Strings werden dynamisch über `stdin` an die CLI-Tools geroutet.

```python
llm_code = "def foo():\n    pass\n"

# Analyse rein im RAM, ohne Festplatten-I/O
diagnostics = AstLinter(Pylint()).check(llm_code)

```

### 1.4 Rule-Management: Regeln deaktivieren

Oft ist es nötig, kontextbezogen Regeln abzuschalten (z. B. die Docstring-Pflicht in simplen Test-Skripten). Der `Pylint`-Worker nimmt hierfür eine `disable`-Liste im Konstruktor entgegen, was sich nahtlos in die entsprechenden CLI-Flags übersetzt.

```python
# Schaltet C0114 (Missing module docstring) und C0116 (Missing function docstring) ab
relaxed_pylint = Pylint(disable=["C0114", "C0116"])
diagnostics = AstLinter(relaxed_pylint).check("x = 1\n")

```

---

## 2. Eigene Linter integrieren (Das `Linter`-Protokoll)

Möchtest du weitere CLI-Tools in Cubie integrieren, musst du lediglich das `Linter`-Protokoll implementieren. Der `AstLinter` kommuniziert ausschließlich über diesen strikten Ausführungsvertrag (Dependency Inversion).

Ein Backend muss folgende Schnittstellen bereitstellen:

1. **`name`**: Ein Property, das den Anzeigenamen liefert.


2. **`register_excludes(excludes: list[str])`**: Eine Methode, um dem Linter nachträglich ignorierte Verzeichnisse aufzuzwingen.


3. **`check(target: Union[str, Path])`**: Die exekutive Kernfunktion, die Code oder Pfade in normierte `LinterDiagnostic`-Objekte übersetzt.



---

## 3. Deep-Dive: Eigene Regeln mit `CstLinter` entwickeln

Im Gegensatz zur AST-Ebene analysiert die CST-Ebene (Concrete Syntax Tree) den Python-Code nativ im Arbeitsspeicher. Syntaxbäume von `libcst` sind verlustfrei (Full-Fidelity); sie behalten jeden Kommentar und jedes Leerzeichen bei, was chirurgische Code-Style-Prüfungen ermöglicht.

Der `CstLinter` bringt einen eigenen integrierten Directory Crawler (`_crawl_directory`) mit, der Ordner rekursiv auflöst und gegen die Exclusion-Registry filtert. Bei toxischen LLM-Strings stürzt er dank Grace-Fallback nicht hart ab, sondern fängt `cst.ParserSyntaxError` ab und wandelt diese on-the-fly in standardisierte `E999`-Diagnosen um.

### 3.1 Die Anatomie der `CstRule`

Jede eigene Regel erbt von der Basisklasse `CstRule` (welche selbst ein `cst.CSTVisitor` ist).
Die Basisklasse löst zwei große Probleme für den Entwickler:

* **State-Bleeding:** Die interne Methode `reset()` leert den Diagnose-Zustand zwischen Dateien.


* **Automatisierte Metadaten-Extraktion:** Die Hilfsmethode `add_diagnostic()` nimmt fehlerhafte `CSTNode`-Objekte entgegen und extrahiert über den `PositionProvider` vollautomatisch exakte Zeilen- und Spaltenkoordinaten.



### 3.2 Eine eigene CST-Regel schreiben

Hier ist ein komplettes Beispiel für eine Regel, die Type-Hints für alle Funktions-Rückgaben (außer bei `__init__`) erzwingt. Wir nutzen dafür deklaratives Pattern Matching via `libcst.matchers`, um uns endlose `if`-Verschachtelungen zu ersparen.

```python
import libcst as cst
import libcst.matchers as m
from qb_cubie import CstRule, CstLinter

class RequireReturnTypeRule(CstRule):
    """
    Erzwingt Type-Hints für Rückgabewerte (außer bei __init__).
    """
    # Wird vom Framework aufgerufen, sobald eine Funktion im Baum gefunden wird
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        # Pattern Matching: Wir suchen exakt die Struktur m.Annotation() im returns-Feld
        has_return_type = m.matches(node, m.FunctionDef(returns=m.Annotation()))
        if not has_return_type and node.name.value != "__init__":
            self.add_diagnostic(  # Kinderleichte Fehlererfassung über die Basisklasse
                node=node,
                rule_id="CST002",
                message=f"Der Funktion '{node.name.value}' fehlt die Return-Type-Annotation.",
                severity="warning"
            )
```

### 3.3 Ausführung im System

Um die eigene Regel nun auf Code anzuwenden, wird sie instanziiert und dem `CstLinter` übergeben:

```python
bad_code = """
def helfer_funktion(x):
    pass
"""

linter = CstLinter(rules=[RequireReturnTypeRule()]) # Instanziierung des Linters mit der eigenen Regel
diagnostics = linter.check(bad_code) # Analyse ausführen

for d in diagnostics:
    print(f"[{d.rule_id}] {d.message} (Zeile: {d.line})")
    # Output: [CST002] Der Funktion 'helfer_funktion' fehlt die Return-Type-Annotation. (Zeile: 2)
```

---

---

<center>

![Error while trying to load the image](.assets/cubie-small.png)

## Dokumentation

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](./GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](./GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](./GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](./GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](./GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](./GUIDE_Linter.md)  

[↦ | Entwicklerübersicht EBT | ↤](./dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>
