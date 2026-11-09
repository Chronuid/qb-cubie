# Gutachten: Analyse und Bewertung des Projekts „Cubie: Quality-Bench“

**Dokument-Typ:** Unabhängiges Fachgutachten (Softwarearchitektur, Testmethodik, Systemsicherheit)  
**Projekt:** Cubie (`cubie`) – Version: 0.0.3  
**Zielsystem:** Python >= 3.13  
**Datum:** 9. November 2026  

---

## Inhaltsverzeichnis

1. [Executive Summary](#executive-summary)
2. [Idee & Philosophische Fundierung](#1-idee--philosophische-fundierung)
   - 2.1 [Der Lösungsraum $\Sigma^*$ und die Bibliothek von Babel](#21-der-lösungsraum-\sigma-und-die-bibliothek-von-babel)
   - 2.2 [Die zwei Säulen: EBT und RBT](#22-die-zwei-säulen-ebt-und-rbt)
   - 2.3 [Kritische Würdigung der Kernidee](#23-kritische-würdigung-der-kernidee)
3. [Nützlichkeit & Praxistauglichkeit](#3-nützlichkeit--praxistauglichkeit)
   - 3.1 [Echte Stärken und primäre Einsatzszenarien](#31-echte-stärken-und-primäre-einsatzszenarien)
   - 3.2 [Grenzen und Reibungsverluste im Entwicklungsalltag](#32-grenzen-und-reibungsverluste-im-entwicklungsalltag)
   - 3.3 [Das RBT/Tkinter-Paradoxon (CI/CD-Inkompatibilität)](#33-das-rbttkinter-paradoxon-cicd-inkompatibilität)
4. [Detaillierte Analyse der technischen Umsetzung](#4-detaillierte-analyse-der-technischen-umsetzung)
   - 4.1 [Architektur & Entwurfsmuster (Die Habenseite)](#41-architektur--entwurfsmuster-die-habenseite)
   - 4.2 [Gravierende Mängel, Anti-Patterns und Risiken](#42-gravierende-mängel-anti-patterns-und-risiken)
     - 4.2.1 [„Smuggled Tools“: Entpackte Wheels & C-Binaries im Quellcode](#421-smuggled-tools-entpackte-wheels--c-binaries-im-quellcode)
     - 4.2.2 [Fataler Pfad-Bug & fehlschlagender Test (`test_astlinter_ignores_venv_directory`)](#422-fataler-pfad-bug--fehlschlagender-test-test_astlinter_ignores_venv_directory)
     - 4.2.3 [Schein-Architektur („Vaporware“) in den Virtualisierungs-Arenen](#423-schein-architektur-vaporware-in-den-virtualisierungs-arenen)
     - 4.2.4 [Prozessweite Seiteneffekte in `TempFS` (Bruch der Thread-Sicherheit)](#424-prozessweite-seiteneffekte-in-tempfs-bruch-der-thread-sicherheit)
     - 4.2.5 [Generator- und Lifecycle-Leak in `MultiprocessRunner`](#425-generator--und-lifecycle-leak-in-multiprocessrunner)
     - 4.2.6 [Sicherheitsrisiken bei IPC-Deserialisierung (RCE-Gefahr)](#426-sicherheitsrisiken-bei-ipc-deserialisierung-rce-gefahr)
     - 4.2.7 [Packaging- und Code-Hygienemängel](#427-packaging--und-code-hygienemängel)
5. [Reifegrad-Matrix](#5-reifegrad-matrix)
6. [Priorisierter Maßnahmenkatalog](#6-priorisierter-maßnahmenkatalog)

---

## Executive Summary

> [!NOTE]
> **Gesamtfazit:**  
> **Cubie** ist ein intellektuell faszinierendes, theoretisch hochentwickeltes Projekt mit einer poetisch-mathematischen Vision: Code wird nicht als Artefakt verstanden, das geschrieben wird, sondern als Punkt im unendlichen Suchraum $\Sigma^*$ (in Anlehnung an Jorge Luis Borges’ *Bibliothek von Babel*), der über formale Hoare-Tripel $\{P\} S \{Q\}$ und orthogonale Datenfilter determiniert wird.
>
> Insbesondere im Kontext von **autonomer KI-Codegenerierung (Agentic Coding)** bietet der Ansatz, funktionale Signaturen, topologische Dateisystemzustände und isolierte Ausführungsumgebungen in deklarativen Verträgen (`WorldState`) zu bündeln, echtes Innovationspotenzial.
>
> Dem steht jedoch eine **erhebliche Diskrepanz zwischen theoretischem Anspruch und tatsächlicher Implementierungsreife** gegenüber:
> 1. Eingeschmuggelte Third-Party-Wheels und binäre `.so`-Dateien im Quelltextordner führen zum sofortigen Absturz naiver `pytest`-Aufrufe (50 Collection Errors).
> 2. Schein-Implementierungen („Vaporware“): `DockerArena` und `VmArena` sind reine 15-Zeilen-Dummies ohne Ausführungslogik; in `src/cubie/arenas/vm/` liegen 0-Byte-Dateien neben umfangreichen Markdown-Handbüchern.
> 3. Gefährliche globale Seiteneffekte (`os.chdir` in `TempFS`) zerstören jede Thread-Sicherheit.
> 4. Ein fehlschlagender Linter-Test scannt versehentlich das gesamte `/tmp`-Verzeichnis des Betriebssystems und erzeugt einen 6,8 MB großen Fehler-Dump.
>
> **Urteil:** Konzeptionell visionär (Note 1-2), in der gegenwärtigen technischen Umsetzung jedoch unausgereift, fehlerbehaftet und in Teilen unfertig (Note 4-5).

---

## 1. Idee & Philosophische Fundierung

### 2.1 Der Lösungsraum $\Sigma^*$ und die Bibliothek von Babel
Cubie verlässt die traditionelle Softwaretest-Perspektive („Hat der Entwickler die geforderte Funktion korrekt implementiert?“). Stattdessen bedient sich das Projekt der theoretischen Informatik und Borges’ Gleichnis der *Bibliothek von Babel*:
* $\Sigma^*$ stellt die unendliche Menge aller möglichen Programme und Zeichenfolgen dar. Jede korrekte Implementierung, aber auch jedes destruktive oder triviale Programm existiert dort bereits.
* Ein Testfall ist keine bloße Prüfung, sondern eine **Suchanfrage / ein Filter**.
* Das klassische Problem unzureichender Tests wird als **Unterspezifikation** begriffen: Wer für `calculate_tax(100, 19)` lediglich einen Testfall `119` definiert, erhält als Treffermenge auch triviale Scheinlösungen wie `def calculate_tax(*args): return 119`.
* Erst durch **orthogonale Randfälle** und zusätzliche Bedingungen ($C$ für Constraints wie Linting, Laufzeit, Security) schrumpft die Treffermenge $\mathcal{S}_{\text{summ}} \cap C$ auf die gesuchte korrekte Lösung zusammen.

### 2.2 Die zwei Säulen: EBT und RBT
Das Framework teilt die Qualitätssicherung in zwei orthogonale Disziplinen:

1. **Example-Based Testing (EBT):**
   - Formalisierung über das Hoare-Tripel $\{P\} S \{Q\}$.
   - Vorbedingungen ($P$) und Nachbedingungen ($Q$) werden als passive `WorldState`-Objekte deklariert.
   - **Mengenlehre & Quantoren:** 
     - Eine Liste in `pre` repräsentiert den **beschränkten Allquantor ($\forall$)**: Jede definierte Eingabe muss deterministisch die Nachbedingung erfüllen (N:1-Mapping).
     - Eine Liste in `post` repräsentiert den **beschränkten Existenzquantor ($\exists$)**: Das Resultat muss mindestens eine der erlaubten Ausprägungen matchen (1:N-Mapping).

2. **Review-Based Testing (RBT):**
   - Deckt qualitative und subjektive Aspekte ab, die sich harten mathematischen Assertions entziehen (Design, UI-Stil, ethische Leitplanken, Security-Audits).
   - Ausführung stoppt synchron und übergibt die Verifikation an einen Prüfer (Human-in-the-Loop oder LLM-Agent).

### 2.3 Kritische Würdigung der Kernidee
* **Stärken:** Die mathematische Präzisierung und die Abbildung von Quantoren direkt über Python-Listen ist elegant und konsistent durchgezogen. Es zwingt den Entwickler (oder die steuernde KI), in Ein- und Ausgangsräumen statt in sequentiellen Einzelschritten zu denken.
* **Schwächen:** Die Ausarbeitung neigt streckenweise zu akademischem Elitarismus. Viele der im Projekt zelebrierten Konzepte (wie „FP-OOP-Isomorphismus“ oder „Connascence of Execution“) sind im Wesentlichen gängige Entwurfsmuster (Value Objects, Strategy Pattern, State Verification), die hier mit einem theoretischen Vokabular aufgeladen werden, das die Einstiegshürde unnötig erhöht.

---

## 3. Nützlichkeit & Praxistauglichkeit

### 3.1 Echte Stärken und primäre Einsatzszenarien
1. **Autonome KI-Codegenerierung (Agentic Coding):**  
   Genau hier liegt die größte Stärke von Cubie. Wenn ein LLM-Agent Programmcode erzeugt, genügen herkömmliche Unit-Tests oft nicht, da LLMs häufig Mocks korrumpieren oder unerwünschte Dateisystem-Mutationen verursachen. Cubies `WorldState` mit Dateisystem-Hydrierung (`fs`) und Ausführungsisolation (`PyVenv`, `TempFS`) ermöglicht es, Code in einer kontrollierten Quarantäne auszuführen und sowohl Rückgabewerte als auch Datei-Diffs millimetergenau abzugleichen.
2. **Dateisystem- und Code-Transformationen:**  
   Für die Entwicklung von Lintern, Formatierern, Transpilern, Migrations-Skripten oder Build-Pipelines ist das deklarative `WorldState(fs={"input.py": "fixtures/input.py"})` und das anschließende Diffing von Ordnerstrukturen signifikant sauberer als handgeschriebene Pytest-`tmp_path`-Konstrukte.
3. **Agnostic Typing & Predicates:**  
   Die Fähigkeit, in `returns` direkt reguläre Ausdrücke (`re.compile`), native Typen (`int`, `str`), Unions (`Union[str, None]`) oder Prädikat-Lambdas (`lambda x: x > 0`) zu übergeben, reduziert redundante Assertions und erhöht die Ausdruckskraft der Tests erheblich.

### 3.2 Grenzen und Reibungsverluste im Entwicklungsalltag
* **Enormer Overhead für klassische Unit-Tests:**  
  Für gewöhnliche Anwendungslogik (z. B. Berechnungen, Datenmanipulation im Speicher) ist Cubie unpraktisch. Das Erzeugen von `WorldState`-Objekten, UUID-Generierung, Tracing und Reporter-Aufrufen erzeugt signifikanten Laufzeit- und Syntax-Overhead. Ein simples `assert func(a) == b` ist in diesen Fällen überlegen.
* **I/O- und Performance-Falle:**  
  Das Konzept hinter `PyVenv` basiert darauf, eine bestehende virtuelle Umgebung via `shutil.copytree` physisch in ein temporäres Verzeichnis zu kopieren. Bei hunderten Testfällen summiert sich dieser I/O-Aufwand zu massiven Verzögerungen. Die interne Testsuite (ca. 300 Tests) benötigte im Testlauf über 3 Minuten.

### 3.3 Das RBT/Tkinter-Paradoxon (CI/CD-Inkompatibilität)
In [`src/cubie/rbt.py`](file:///home/symphonie/PycharmProjects/cubie/src/cubie/rbt.py#L28) ist als Standard-Prüfer der `HumanReviewer` hinterlegt:
```python
self.reviewer = reviewer or HumanReviewer()
```
Wird dieser aufgerufen, initialisiert er ein grafisches Tkinter-Fenster und ruft `self._root.wait_window()` auf.
* **Folge:** In Headless-CI/CD-Pipelines (z. B. GitHub Actions, GitLab CI, Linux-Server ohne X11/Wayland-Display) führt das Ausführen eines RBT-Tests ohne expliziten Mock-Reviewer zum sofortigen Crash (`TclError: no display name and no $DISPLAY environment variable`) oder zum Deadlock, weil das System auf eine menschliche Schaltflächen-Betätigung wartet.
* **Bewertung:** Ein Test-Framework, das im Standardverhalten ein Desktop-GUI-Fenster öffnet, bricht mit den fundamentalen Prinzipien automatisierter Build-Pipelines.

---

## 4. Detaillierte Analyse der technischen Umsetzung

### 4.1 Architektur & Entwurfsmuster (Die Habenseite)
* **Protokoll-Entkopplung (`protocols.py`):** Die Definition von `typing.Protocol`-Schnittstellen für `Arena`, `IPCC` (IPC-Codecs), `Reporter` und `Multiprocessor` ist vorbildlich. Sie erlaubt den modularen Austausch von Ausführungsumgebungen und Berichterstattern.
* **Entkopplung von Engine und Reporting:** `EBT` erzeugt reine Wertobjekte (`RunTrace`, `EvaluationTrace`). Die Entscheidung über den Abbruch via Pytest-Assertion ist vollständig in den `PytestReporter` ausgelagert.
* **Heuristischer Multiprocessing-Dispatcher:** Der `StateInspector` scannt Pre- und Post-Zustände auf unpickelbare Callables (wie dynamische Lambdas oder Closures). Ist alles Standard-Pickle-kompatibel, wird der schnelle `PickleProcessor` gewählt; andernfalls schaltet die Engine nahtlos auf `LokyProcessor` (mit `cloudpickle`-Serialisierung) um.

---

### 4.2 Gravierende Mängel, Anti-Patterns und Risiken

#### 4.2.1 „Smuggled Tools“: Entpackte Wheels & C-Binaries im Quellcode
Im Verzeichnis [`src/cubie/linters/`](file:///home/symphonie/PycharmProjects/cubie/src/cubie/linters/) befinden sich vollständige, entpackte Drittanbieter-Pakete:
* `src/cubie/linters/libcst_tool/`
* `src/cubie/linters/pylint_tool/`

Darin enthalten sind nicht nur fremde Quelltexte, sondern vollständige `.dist-info`-Ordner sowie vorkompilierte binäre C-Erweiterungen:
`src/cubie/linters/pylint_tool/24eba0d76380778f559b__mypyc.cpython-312-x86_64-linux-gnu.so` (kompiliert für Python 3.12, während das Projekt Python 3.13 deklariert!).

In [`src/cubie/linter.py`](file:///home/symphonie/PycharmProjects/cubie/src/cubie/linter.py#L3-L5) wird dies explizit als „geschmuggelt“ deklariert:
```python
_SMUGGLED_LIBCST = Path(__file__).parent / "linters" / "libcst_tool"
if importlib.util.find_spec("libcst") is None:
    if _SMUGGLED_LIBCST.exists(): sys.path.insert(0, str(_SMUGGLED_LIBCST.resolve()))
```

* **Die Konsequenz:** Führt man im Projekt-Root schlicht `pytest` aus, versucht Pytest die Test-Dateien der entpackten Bibliotheken (`libcst/_nodes/tests/...`, `dill/tests/...`) auszuführen. Die Test-Collection bricht mit **50 Fehlern** ab. Das Einchecken entpackter Distributions-Pakete und Binärdateien in das `src/`-Verzeichnis widerspricht sämtlichen Standards des Python-Packaging.

#### 4.2.2 Fataler Pfad-Bug & fehlschlagender Test (`test_astlinter_ignores_venv_directory`)
Die Ausführung der Testsuite (`pytest tests`) bricht mit einem harten Failure ab:
```
FAILED tests/tests_linter/test_linter_ast.py::test_astlinter_ignores_venv_directory
```
* **Analyse:** In Zeile 189 von `test_linter_ast.py` wird als Ziel `kwargs={"target": Path("..")}` übergeben.
* Innerhalb der `PyVenv`-Arena operiert der Prozess in einem temporären Verzeichnis `/tmp/cubie_arena_...`. Die Angabe von `..` verweist somit auf das globale Systemverzeichnis `/tmp` des Hosts.
* **Auswirkung:** Pylint begann, das gesamte Host-Verzeichnis `/tmp` rekursiv zu analysieren (inklusive temporärer Dateien fremder Applikationen wie LibreOffice). Es erzeugte einen Fehler-Dump von **6,8 Megabyte**, blockierte die CPU für über 90 Sekunden und scheiterte schließlich, da fremde Fehler diagnosiziert wurden. Dies zeigt eine gefährliche Lücke bei der Kapselung und Validierung von Zielpfaden auf.

#### 4.2.3 Schein-Architektur („Vaporware“) in den Virtualisierungs-Arenen
Das Projekt dokumentiert und bewirbt Virtualisierungs-Arenen für Container und virtuelle Maschinen. Ein Blick in den Quellcode offenbart jedoch:
* [`DockerArena`](file:///home/symphonie/PycharmProjects/cubie/src/cubie/arenas/dockerarena.py): Besteht aus exakt 16 Zeilen und besitzt nur ein `__init__`. Die Methoden `setup()`, `execute()`, `get_state()` und `teardown()` existieren nicht. Die Klasse implementiert das deklarierte `Arena`-Protokoll in keiner Weise, wird aber in `__all__` exportiert.
* [`VmArena`](file:///home/symphonie/PycharmProjects/cubie/src/cubie/arenas/vmarena.py): Identischer 15-Zeilen-Dummy ohne Funktion.
* [`src/cubie/arenas/vm/`](file:///home/symphonie/PycharmProjects/cubie/src/cubie/arenas/vm/): Enthält 5 Python-Dateien (`__init__.py`, `libvirt_handles.py`, `wizards.py`, `wizard_cli.py`, `wizard_gui.py`), die **vollständig leer (0 Bytes)** sind. Dem gegenüber stehen über 33 KB Markdown-Handbücher („Libvirt-Handbuch.md“).
* Sämtliche 24 Tests in `tests/tests_arena/tests_vm_arena/` sind mit `@pytest.mark.skip()` markiert.

#### 4.2.4 Prozessweite Seiteneffekte in `TempFS` (Bruch der Thread-Sicherheit)
In [`src/cubie/arenas/tempfs.py`](file:///home/symphonie/PycharmProjects/cubie/src/cubie/arenas/tempfs.py#L95-L100) findet sich folgende Methode:
```python
def _switch_cwd_to_workspace(self) -> None:
    self._original_cwd = Path.cwd()
    os.chdir(self.workspace_path)
```
* **Kritik:** In Python ist `os.chdir()` eine prozessweite Operation. Es gibt kein thread-lokales Arbeitsverzeichnis. Werden Tests mit Threading oder parallelen Werkzeugen ausgeführt, mutiert ein `TempFS`-Test das Arbeitsverzeichnis für alle anderen parallel laufenden Komponenten. Das führt zu nicht-deterministischen Fehlern und Race Conditions.

#### 4.2.5 Generator- und Lifecycle-Leak in `MultiprocessRunner`
In [`src/cubie/multiprocessors.py`](file:///home/symphonie/PycharmProjects/cubie/src/cubie/multiprocessors.py#L275-L282):
```python
def execute(self) -> Iterable:
    with self._handler.create_handler(n_tasks=self._n_tasks) as mapper:
        return mapper.map(
            self._task_func,
            self._indices,
            self._pre_states
        )
```
* **Kritik:** `mapper.map()` liefert einen lazy Iterator zurück. Beim Verlassen des `with`-Blocks wird jedoch die `__exit__`-Methode des Kontextmanagers aufgerufen (was bei `LokyMapper` z. B. `executor.shutdown(wait=True)` aufruft). Der Kontextmanager wird somit geschlossen, **bevor** der Konsument die Ergebnisse tatsächlich abgefragt hat.

#### 4.2.6 Sicherheitsrisiken bei IPC-Deserialisierung (RCE-Gefahr)
Im Test [`test_security_arena_codec.py`](file:///home/symphonie/PycharmProjects/cubie/tests/tests_arena/test_security_arena_codec.py#L87-L93) demonstriert der Autor selbst, dass der `PickleCodec` anfällig für Remote Code Execution (RCE) via `__reduce__` ist. Dennoch greift der `LokyProcessor` und der empfohlene Fallback für komplexe Typen auf `CloudpickleCodec` zurück.  
* **Risiko:** Wenn Cubie als Test-Harness für nicht-vertrauenswürdigen, KI-generierten Code eingesetzt wird, bietet das Sandboxing trügerische Sicherheit: Schreibt das isolierte Script manipulierte Bytecode-Objekte in die IPC-Datei, übernimmt es bei der Deserialisierung sofort die Kontrolle über den Host-Prozess.

#### 4.2.7 Packaging- und Code-Hygienemängel
* **`pyproject.toml`:** Es wird `"dataclasses>=0.8"` als Abhängigkeit gelistet. `dataclasses` ist seit Python 3.7 Kern der Standardbibliothek. Das externe PyPI-Paket war ein Backport für Python 3.6 und hat in einem modernen Python 3.13+-Projekt nichts zu suchen.
* **Redundante Klassendefinitionen:** Die Datenklasse `ReviewData` ist identisch sowohl in [`protocols.py`](file:///home/symphonie/PycharmProjects/cubie/src/cubie/protocols.py#L8-L14) als auch in [`rbt.py`](file:///home/symphonie/PycharmProjects/cubie/src/cubie/rbt.py#L10-L15) definiert.
* **Fragwürdige Konstrukte:** Zuweisungen wie `expect: Optional[bool] = True or False` in [`protocols.py`](file:///home/symphonie/PycharmProjects/cubie/src/cubie/protocols.py#L39) (was zur Laufzeit schlicht `True` ergibt) oder exzessive Einzeiler (`if cond: do_something()`) untergraben den eigenen, ausführlich dokumentierten Styleguide.

---

## 5. Reifegrad-Matrix

| Bewertungsbereich | Schulnote | Urteil & Begründung |
| :--- | :---: | :--- |
| **Konzept & Vision** | **1- (Sehr Gut)** | Hervorragende formallogische Konzeption; exzellente theoretische Eignung für autonome KI-Agenten und Programm-Synthese. |
| **Architektur-Entwurf** | **2 (Gut)** | Durchdachte Protokolle, saubere Trennung von Tracing, Reporting und Ausführung; gelungener Multiprocessing-Dispatcher. |
| **Code-Qualität & Stil** | **3- (Befriedigend)** | Teilweise Verstoß gegen den eigenen Styleguide (Einzeiler, Redundanzen, kryptische Hilfsvariablen). |
| **Funktionalität & Stabilität** | **4- (Ausreichend)** | Native Pytest-Ausführung scheitert; 1 harter Testabbruch; fehlerhafte relative Pfadauflösung auf das Host-System. |
| **Vollständigkeit** | **5 (Mangelhaft)** | Wesentliche beworbene Komponenten (`DockerArena`, `VmArena`, VM-Wizards) sind leere Dummies oder 0-Byte-Dateien. |
| **Packaging & Repository-Hygiene** | **6 (Ungenügend)** | Entpackte Third-Party-Wheels und fremde `.so`-C-Bibliotheken im Quellbaum eingecheckt; obsolete Abhängigkeiten. |

---

## 6. Priorisierter Maßnahmenkatalog

Um Cubie von einem faszinierenden Prototyp in ein stabiles, produktionsreifes Framework zu überführen, müssen folgende Schritte umgesetzt werden:

### Priorität 1 (Sofortige Stabilität & Hygiene)
1. **Entfernung der „Smuggled Tools“:**  (DONE)  
   Die Ordner `src/cubie/linters/libcst_tool` und `src/cubie/linters/pylint_tool` restlos aus dem Repository entfernen. Benötigte Werkzeuge ausschließlich über standardisierte Abhängigkeiten (`pyproject.toml`) deklarieren.
2. **Pytest-Konfiguration absichern:** (DONE)  
   In `pyproject.toml` eine feste Konfiguration hinterlegen:
   ```toml
   [tool.pytest.ini_options]
   testpaths = ["tests"]
   ```
   Dies verhindert, dass Pytest fremde Modultests einsammelt.
3. **Behebung des Pfad-Bugs in `test_astlinter_ignores_venv_directory`:** (DONE)  
   Das Linter-Target darf niemals unvalidiert auf übergeordnete Verzeichnisse (`..`) außerhalb der Arena zugreifen. Pfade müssen strikt an den Workspace der Arena gebunden werden.

### Priorität 2 (Architektur-Härtung)
4. **Beseitigung von `os.chdir` in `TempFS`:**  (DECLINED: We know, but that is TempFS. Use PyVenv if you want it better.)  
   Arbeitsverzeichnisse dürfen nicht prozessweit umgebogen werden. Wenn Pfad-Isolation erforderlich ist, muss das Target entweder explizite Pfadparameter akzeptieren oder die Ausführung in einen Subprozess ausgelagert werden.
5. **Materialisierung von Mappings vor Kontext-Exit:**  (DONE)  
   In `MultiprocessRunner.execute()` muss der Generator konsumiert werden, bevor der `with`-Block schließt:
   ```python
   with self._handler.create_handler(n_tasks=self._n_tasks) as mapper:
       return list(mapper.map(self._task_func, self._indices, self._pre_states))
   ```
6. **Entschärfung von RBT für CI/CD:**  
   Der `HumanReviewer` darf nicht der Default sein. RBT muss im Headless-Modus entweder auf interaktive CLI-Prompts zurückfallen oder bei fehlendem `DISPLAY` kontrolliert übersprungen werden (`pytest.skip()`).

### Priorität 3 (Bereinigung & Release-Fähigkeit)
7. **Ehrlichkeit bei Virtualisierungs-Features:**  
   Die unfertigen Klassen `DockerArena` und `VmArena` sowie die 0-Byte-Dateien in `src/cubie/arenas/vm/` vorübergehend aus dem öffentlichen Interface entfernen und klar als experimentelle Entwürfe kennzeichnen.
8. **Bereinigung von `pyproject.toml`:**  (DONE)  
   Entfernen der obsoleten `"dataclasses>=0.8"`-Abhängigkeit und Harmonisierung der Versions-Pins.
9. **Deduplizierung von `ReviewData`:**  (DONE)  
   Zusammenführung der doppelten Klassendefinitionen in `protocols.py` und Import in `rbt.py`.
