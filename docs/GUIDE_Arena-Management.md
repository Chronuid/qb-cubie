# 📖 GUIDE: Arena-Management in Cubie

Das Arena-Management in Cubie ermöglicht es, Tests in kontrollierten, reproduzierbaren Umgebungen auszuführen. Durch die strikte Trennung von Test-Logik und Ausführungskontext (Arena) bleibt der Code flexibel und robust. Aktuell bietet Cubie zwei native Arena-Typen an, die je nach Anwendungsfall unterschiedliche Schwerpunkte auf Performance und Isolation legen:

* **`TempFS` (Speed & Filesystem):** Ein extrem leichtgewichtiger Runner, der den Overhead von Subprozessen, Inter-Process-Communication (IPC) und Venv-Duplikaten eliminiert. Führt das Target direkt im Host-Prozess aus, kapselt aber alle Dateisystem-Operationen in einem flüchtigen Workspace. Ideal für reine FS-Abgleiche und bei minimalen Datensätzen gut 3-mal schneller als eine prozessbasierte Virtualisierung.
* **`PyVenv` (Isolation & Environment):** Der funktionale MVP für vollständige Prozess- und Dependency-Isolation. Kapselt den Lauf in einem echten Python-Subprozess innerhalb einer duplizierten virtuellen Umgebung. Ideal, um Paket-Installationen, Versionskonflikte oder externe Microservices zu testen.



---

## 1. Die `TempFS`-Arena (Filesystem-Fokus)

Die `TempFS`-Arena fungiert als Standard für alle Tests, die sich ausschließlich auf Input/Output-Operationen im Dateisystem konzentrieren (z.B. Datei-Generatoren, Parser oder klassisches Byte-Diffing) und keine spezifischen Python-Abhängigkeiten benötigen.

**Wie es funktioniert:**
Die Arena hydriert die deklarierten Dateien aus dem `WorldState` in einen temporären Ordner. Für den Moment der Funktionsausführung wird das Arbeitsverzeichnis des Betriebssystems für den Host-Prozess in diesen temporären Workspace verschoben. Das Target läuft als normaler Funktionsaufruf mit maximaler Performance, manipuliert aber unwissentlich den temporären Workspace, welcher danach durch EBT sauber via Byte-Diffing validiert und anschließend zerstört wird.

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

Für sicherheitskritische Anwendungen, die Ausführung von absolutem Fremdcode oder bei exzessiven, unüberwachten Fuzzing-Mutationen sollte zwingend auf stabilere Virtualisierungs-Technologien zurückgegriffen werden (z. B. durch die Implementierung einer dedizierten `DockerArena` oder MicroVMs), welche diese Sicherheit auf Kernel-Ebene garantieren können.

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