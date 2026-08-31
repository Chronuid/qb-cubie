# Arenen & Sandbox-Protokolle

Arenen bilden die physische Ausführungsschicht innerhalb der Cubie-Architektur. Während die `EBT`-Klasse die formallogische Ebene (die Beweisführung) orchestriert, übernehmen die Arenen die Rolle des isolierten Labors. Sie garantieren, dass Seiteneffekte, Datei-Installationen oder veränderte Umgebungsvariablen das Host-System nicht kompromittieren.

## Das `Arena`-Protokoll

Alle Arenen in Cubie implementieren ein striktes, einheitliches Interface (`protocols.Arena`). Dieses Protokoll entkoppelt die EBT-Engine von den technischen Details der Sandbox-Generierung und forciert ein lineares Pipeline-Pattern (State-Guard Pattern).

### Kern-Methoden des Lebenszyklus

*   **`setup(state: WorldState)`:**
    Der Initialzünder der Pipeline. Die Arena empfängt den vollständigen `WorldState` des aktuellen Pre-States (Konfigurations-Zustand). Hier entscheidet die Arena, wie sie den geforderten Dateisystem-Zustand (`fs`) und gegebenenfalls den Basis-Umgebungszustand (`arena`) physisch auf der Festplatte (meist in `tempfile.mkdtemp`) aufbaut.
*   **`execute(target, args, kwargs)`:**
    Führt das übergebene Callable im Kontext des vorbereiteten Workspace aus. Abhängig vom Arena-Typ passiert dies als direkter Methodenaufruf mit verbogenem `CWD` oder via Interprozesskommunikation (IPC) in einem vollständig isolierten Subprozess.
*   **`get_state() -> WorldState`:**
    Die Aggregationsphase. Die Arena sammelt die funktionalen Return-Werte und die mutierten, absoluten Pfade vom physischen Workspace ein und verpackt diese zu einem neuen `WorldState`-Objekt (Prozessierungs-Zustand). Dieses Objekt repräsentiert die "echte Realität" und wird an die EBT-Engine zur Evaluierung übergeben.
*   **`teardown()`:**
    Zerstört die isolierte Umgebung restlos und bereinigt den Arbeitsspeicher sowie die Festplatte.

---

## `class PyVenv` (Vollständige Isolation)

Die `PyVenv`-Arena ist das Schwergewicht für maximale Sicherheit und Umgebungskontrolle. Sie nutzt `uv`, um flüchtige Klone von Python Virtual Environments zu erstellen und das Target in einem dedizierten Subprozess auszuführen.

### Architektonische Eigenschaften

*   **IPC via Codec:** Da das Target in einem Subprozess läuft, können Eingaben (Args, Kwargs) und funktionale Ausgaben (Returns) nicht direkt übergeben werden. Die Arena nutzt das `IPCC`-Protokoll (z.B. `MSGspecCodec`), um Daten zustandslos und sicher zwischen dem Host-Prozess (Cubie) und der Sandbox hin- und herzureichen.
*   **Der `arena`-Override:** Befindet sich im deklarierten Pre-State ein String im Attribut `WorldState.arena`, wird dieser als Pfad zu einer Base-Arena interpretiert. `PyVenv` klont dynamisch dieses spezifische Environment anstelle des global bei der Instanziierung definierten Defaults.
*   **Flakiness-Schutz (Volatility Ignorance):** Virtual Environments sind voll von volatilen Metadaten, die beim Byte-Diffing zu False-Positives führen. EBT und `PyVenv` nutzen einen bidirektionalen Filter, der Skripte mit absoluten Pfaden (`bin/`, `pyvenv.cfg`) sowie Caches und Paket-Metadaten (`__pycache__`, `.dist-info`) systematisch ausklammert. Die Evaluierung fokussiert sich rein auf die semantischen Modifikationen (wie neu hinzugefügte Quellcodes im `site-packages`-Ordner).

### Der `ArenaBuilder` (Provisioning)

Um Test-Code nicht mit Setup-Boilerplate zu überladen, stellt das Modul den `ArenaBuilder` bereit. Über ein Fluent Interface können Base-Environments deklarativ generiert werden (inklusive der Installation von Drittanbieter-Bibliotheken via `uv pip`).

`ArenaBuilder("tests/.arenas/ollama_env").with_packages(["ollama"]).build()`

---

## `class TempFS` (Lightweight IO-Sandbox)

Die `TempFS`-Arena ist die performante, leichtgewichtige Alternative für Programmsegmente, die I/O-Operationen ausführen, aber keine isolierten Python-Abhängigkeiten benötigen.

### Architektonische Eigenschaften

* **Host-Prozess-Ausführung:** Im Gegensatz zu `PyVenv` startet `TempFS` keinen Subprozess und serialisiert keine Daten. Es manipuliert während der `execute`-Phase lediglich kurzzeitig das "Current Working Directory" (`CWD`) des Host-Prozesses, führt das Target nativ aus und springt danach sicher in den ursprünglichen Pfad zurück.

* **Beschränkung auf die Dateisystem-Topologie:** Die Arena ist ausschließlich für das Mapping und Verifizieren der Festplattenstruktur (`WorldState.fs`) konzipiert.

* **Schutz durch Warnungen:** Wenn ein Nutzer versucht, eine komplexe Umgebungssimulation über das Attribut `WorldState.arena` in eine `TempFS`-Instanz zu injizieren, wirft die Klasse eine dedizierte Laufzeitwarnung und verweist architektonisch auf die Nutzung von `PyVenv`.