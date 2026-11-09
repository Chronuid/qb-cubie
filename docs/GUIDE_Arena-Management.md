# 📖 CUBIE-GUIDE: Arena-Management in Cubie

Das Arena-Management in Cubie ermöglicht es, Tests in kontrollierten, reproduzierbaren Umgebungen auszuführen. Durch die strikte Trennung von Test-Logik und Ausführungskontext (Arena) bleibt der Code flexibel und robust. Aktuell bietet Cubie zwei native Arena-Typen an, die je nach Anwendungsfall unterschiedliche Schwerpunkte auf Performance und Isolation legen:

* **`TempFS` (Filesystem):** Führt das Target in einem frischen Kindprozess mit demselben Python-Interpreter und dessen installierten Paketen aus. Ein flüchtiger Workspace dient als Arbeitsverzeichnis; eine virtuelle Umgebung wird nicht kopiert.
* **`PyVenv` (Isolation & Environment):** Der funktionale MVP für vollständige Prozess- und Dependency-Isolation. Kapselt den Lauf in einem echten Python-Subprozess innerhalb einer duplizierten virtuellen Umgebung. Ideal, um Paket-Installationen, Versionskonflikte oder externe Microservices zu testen.



---

## 1. Die `TempFS`-Arena (Filesystem-Fokus)

Die `TempFS`-Arena fungiert als Standard für alle Tests, die sich ausschließlich auf Input/Output-Operationen im Dateisystem konzentrieren (z.B. Datei-Generatoren, Parser oder klassisches Byte-Diffing) und keine spezifischen Python-Abhängigkeiten benötigen.

**Wie es funktioniert:**
Die Arena hydriert die deklarierten Dateien aus dem `WorldState` in einen temporären Ordner und startet das Target mit diesem Ordner als Arbeitsverzeichnis. Das CWD des aufrufenden Prozesses bleibt auch während paralleler Thread-Aufrufe unverändert. EBT validiert anschließend den Workspace und entfernt ihn nach der Auswertung. Jede gleichzeitig aktive Arena benötigt eine eigene `TempFS`-Instanz; `EBT(multiprocessing=True)` und pytest-xdist können die Ausführung zusätzlich auf Prozesse verteilen.

**Prozessgrenze und Migration:** Targets, Argumente, Rückgaben und übertragene Exceptions müssen mit Cloudpickle serialisierbar sein. Lokale Funktionen und Lambdas werden unterstützt. Änderungen an übergebenen Python-Objekten oder globalen Variablen gelangen nicht zurück zum Aufrufer; Rückgaben sind deserialisierte Objekte mit eigener Identität. Prüfe solche Änderungen über Rückgabewerte oder den Dateisystemzustand. Für explizite Ausführung im aufrufenden Prozess kann EBT ohne Arena verwendet werden.

Jeder Target-Aufruf benötigt einen Prozessstart und die Übertragung seiner Daten. Dadurch entsteht zusätzlicher Aufwand gegenüber der früheren direkten Ausführung, auch innerhalb eines EBT-Multiprocessing-Workers.

Target-Exceptions einschließlich `KeyboardInterrupt` und `SystemExit` werden mit einem Hinweis auf den Traceback des Kindprozesses weitergegeben. Stirbt der Kindprozess ohne Ergebnis, etwa durch `os._exit`, meldet `TempFS` einen `RuntimeError`. Das Host-CWD bleibt erhalten; `run()` und EBT räumen den Workspace auch bei Fehlern auf. IPC-Dateien liegen außerhalb des Workspace und erscheinen nicht in FS-Postconditions.

---

## 2. Die `PyVenv`-Arena (Dependency-Fokus)

> **DISCLAIMER:** `PyVenv` bietet als funktionaler MVP keine OS-Level Security-Sandbox gegen etwaige Jailbreaks.
> 
> 

Arenen (`PyVenv`) isolieren deine Tests in echten virtuellen Umgebungen. Damit das in der Praxis reibungslos funktioniert und dein Repository sauber bleibt, haben sich folgende Best Practices etabliert.

### 2.1 Lokale Arenen (Innerhalb des Test-Ordners)

Wenn Tests spezifische, isolierte Umgebungen benötigen (z. B. um Paket-Installationen zu prüfen), sollten diese nicht wild im Projekt verstreut werden.

* **Struktur:** Lege einen dedizierten, versteckten Ordner (z. B. `tests/.arenas/`) an.
* **Setup:** Mit schnellen Paketmanagern wie `uv` lassen sich diese Arenen in Millisekunden aufbauen:



```bash
# Initiale Erstellung der Arena
uv venv tests/arenas/qa_env_1

# Optional: Spezifische Abhängigkeiten vorab installieren
uv pip install requests --env tests/arenas/qa_env_1

```

* **Nutzung im Code:** Da der Pfad relativ zum Ausführungsort von Pytest ist, kannst du ihn direkt deklarieren:



```python
def test_installation():
    EBT(
        arena=PyVenv("tests/arenas/qa_env_1"),
        target=my_installer_func,
        # ...
    ).run()

```
### 2.4 IPC-Codecs und Payload-Serialisierung

Da die `PyVenv`-Arena das Target und die Parameter in einem isolierten Subprozess ausführt, müssen diese Daten über die Prozessgrenze (Inter-Process Communication, kurz IPC) transportiert werden. Cubie nutzt dafür austauschbare Codecs, die du je nach Komplexität deiner Test-Daten anpassen kannst:

*   **`MSGspecCodec` (Der Standard):** 
    Dieser Codec ist standardmäßig aktiv. Er basiert auf C und ist extrem performant, versteht aber **ausschließlich primitive Datenstrukturen** (Strings, Listen, Dictionaries etc.). Wenn du versuchst, gebundene Methoden mit komplexem Zustand (`__dict__`) oder dynamische EBT-Prädikate (Lambdas) an die Arena zu übergeben, blockt dieser Codec die Serialisierung ab und wirft eine dedizierte Warnung mit dem Hinweis, die Payloads zu simplifizieren oder den Codec zu wechseln.
    
*   **`CloudpickleCodec` (Für komplexe Objekte):**
    Wenn dein Test zwingend dynamische Callables (Lambdas in Post-Conditions) oder komplexe Mock-Instanzen benötigt, kannst du diesen Codec nutzen. Er serialisiert den kompletten Bytecode und Zustand.
    *Achtung (Isolation Leak):* Cloudpickle arbeitet sehr "gierig" und zieht potenziell Host-Abhängigkeiten mit in den Bytestream. Er durchbricht damit teilweise die strikte Isolation der Arena. Nutze ihn daher nur, wenn komplexe Objekte unvermeidbar sind.

**Konfiguration eines abweichenden Codecs:**
Du kannst den Codec direkt bei der Instanziierung der Arena überschreiben:

```python
from cubie import EBT, WorldState, PyVenv, CloudpickleCodec

def test_complex_callable():
    EBT(
        # Wir weisen der Arena explizit den fähigeren Codec zu
        arena=PyVenv("tests/arenas/qa_env", codec=CloudpickleCodec()),
        target=my_complex_func,
        pre=WorldState(args=(1, 2)),
        # Ein Lambda in der Post-Condition erfordert zwingend Cloudpickle
        post=WorldState(returns=lambda actual: actual > 0)
    ).run()
```

### 2.2 Externe Arenen (Andere Projekte referenzieren)

Oft möchte man die Funktionalität eines externen Projekts testen (z. B. einen lokalen LLM-Server oder eine andere Microservice-Umgebung).

* **Das Problem:** Absolute Pfade wie `/home/user/projects/anderes_projekt/.venv` in den EBT-Tests zu hardcoden, bricht sofort, sobald ein anderer Entwickler das Repository klont oder die CI/CD-Pipeline den Test ausführt.
* **Die Lösung (Environment-Mapping):** Nutze eine `.env`-Datei oder die `conftest.py`, um externe Pfade dynamisch aufzulösen. So bleibt der Testcode umgebungsagnostisch.



Beispiel via `conftest.py`:

```python
import os
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def external_arena():
    """Löst den Pfad zum externen Projekt dynamisch auf."""
    # Fallback auf einen relativen Nachbar-Ordner, falls keine Env-Var gesetzt ist
    base_path = os.getenv("EXTERNAL_PROJECT_PATH", "../anderes_projekt")
    return str(Path(base_path) / ".venv")

```

Nutzung im Test:

```python
def test_external_target(external_arena): # Pytest injiziert den Pfad
    EBT(
        arena=PyVenv(external_arena),
        target=external_system.run,
        # ...
    ).run()

```

### 2.3 Architektur-Prinzipien & Sicherheit

Die mitgelieferte `PyVenv`-Klasse repräsentiert den funktionalen MVP für das Arena-Protokoll. Sie konzentriert sich auf das absolute technische Minimum, um Abhängigkeiten sauber zu kapseln und Seiteneffekte im Dateisystem zu verhindern.

**Wichtig:** Diese Arena bietet keine tiefgreifende OS-Level-Isolation! Wir können nicht garantieren, dass ein stoischer, chaotischer Fuzzer durch unvorhersehbare Mutationen nicht doch einen "Jail-Break" hinlegt und aus der Sandbox ausbricht. Der Subprozess läuft weiterhin mit den Rechten des Host-Systems.

Für sicherheitskritische Anwendungen, die Ausführung von Fremdcode oder unüberwachte Fuzzing-Mutationen ist eine separat eingerichtete, geeignete Container- oder VM-Isolation erforderlich. Cubie stellt derzeit keine solche Arena bereit: `DockerArena` und `VmArena` sind nicht implementiert und nicht Teil der öffentlichen API. Die eingefrorenen [Feature-Entwürfe](feature-drafts/virtualization/README.md) beschreiben ausschließlich geplante Funktionen und keine bestehenden Sicherheitsgarantien.

### Flakiness-Protection im Byte-Diffing

Python Virtual Environments sind aufgrund flüchtiger Metadaten von Natur aus anfällig für Flakiness beim statischen Vergleichen. Die EBT-Engine umgeht dieses Problem durch einen bidirektionalen Set-Abgleich, der volatile Dateien systematisch ausklammert. Ignoriert werden:

* Umgebungs-Skripte mit harten absoluten Pfaden (`bin/`, `Scripts/`, `pyvenv.cfg`).
* Flüchtige Meta- und Cache-Dateien (`__pycache__`, `.pyc`, `.lock`, `CACHEDIR.TAG`).
* Paket-Metadaten (`.dist-info`), deren Hashes betriebssystemabhängig variieren können.
Der verbleibende Byte-Diff konzentriert sich somit ausschließlich auf die semantisch relevanten Quellcodes im `site-packages`-Ordner.

### State-Guard Pattern

Alle Arenen nutzen konsequent explizite State-Guards am Anfang kritischer Methoden (z.B. `if self.workspace_path is None: raise RuntimeError(...)`). Dieses Vorgehen befriedigt nicht nur den Linter restlos, sondern dient gleichzeitig als harter Laufzeitschutz gegen unvollständige Pipelines (Connascence of Execution), da es statisch und dynamisch garantiert, dass die Arena korrekt aufgebaut wurde, bevor sie evaluiert wird.

---

# 3. Provisioning mit dem `ArenaBuilder`

Um die Test-Dateien nicht mit manuellen Subprocess-Aufrufen für das Setup von Base-Environments zu überladen, bietet das Modul den `ArenaBuilder`. Er nutzt ein Fluent Interface, um Base-Arenen deklarativ per Code aufzubauen. Dies eignet sich hervorragend für das globale Provisioning (z.B. in der `conftest.py` oder auf Modul-Ebene).

**Usage-Pattern:**

```python
from arenas.pyvenv import ArenaBuilder, PyVenv
from ebt import *

# 1. Globale Provisionierung der Base-Arena (Idempotent)
base_arena_path = "tests/arenas/ollama_env"
ArenaBuilder(base_arena_path).with_packages(["ollama"]).build()


# 2. Nutzung im EBT-Run
def test_complex_mutation():
    EBT(
        target=target_do_something,
        pre=WorldState(arena=PyVenv(base_arena_path)),
        post=WorldState(returns=True)
    ).run()

```
