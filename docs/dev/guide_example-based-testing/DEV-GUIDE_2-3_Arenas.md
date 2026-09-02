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

## Der Identifikations- und ID-Mechanismus

Um isolierte Umgebungen präzise nachverfolgen zu können (z.B. beim Debugging in temporären Verzeichnissen), implementieren alle nativen Cubie-Arenen (`PyVenv` und `TempFS`) ein standardisiertes ID-Muster.

* **`custom_id`:** Ein optionaler String, der der Arena bei der Instanziierung mitgegeben werden kann. Wird kein Wert übergeben, fällt dieser auf den kleingeschriebenen Klassennamen zurück (z.B. `"pyvenv"` oder `"tempfs"`). Dies erlaubt es, spezifischen Testläufen einen semantischen Kontext zu geben.
* **`arena_id`:** Ein intern generierter String, der die absolute Eindeutigkeit der Instanz garantiert. Er setzt sich aus dem Präfix `cubie_arena_`, der `custom_id` und einem 8-stelligen Hexadezimal-Code (via `uuid.uuid4()`) zusammen. Diese ID wird genutzt, um die temporären Verzeichnisse via `tempfile.mkdtemp(prefix=...)` kollisionsfrei und eindeutig zu benennen.

---

## `class PyVenv` (Vollständige Isolation)

Die `PyVenv`-Arena ist das Schwergewicht für maximale Sicherheit und Umgebungskontrolle. Sie nutzt `uv`, um flüchtige Klone von Python Virtual Environments zu erstellen und das Target in einem dedizierten Subprozess auszuführen.

### Architektonische Eigenschaften

*   **IPC via Codec:** Da das Target in einem Subprozess läuft, können Eingaben (Args, Kwargs) und funktionale Ausgaben (Returns) nicht direkt übergeben werden. Die Arena nutzt das `IPCC`-Protokoll (Standartmäßig `MSGspecCodec`), um Daten zustandslos und sicher zwischen dem Host-Prozess (Cubie) und der Sandbox hin- und herzureichen.
*   **Der `arena`-Override:** Befindet sich im deklarierten Pre-State ein String im Attribut `WorldState.arena`, wird dieser als Pfad zu einer Base-Arena interpretiert. `PyVenv` klont dynamisch dieses spezifische Environment anstelle des global bei der Instanziierung definierten Defaults.
*   **Flakiness-Schutz (Volatility Ignorance):** Virtual Environments sind voll von volatilen Metadaten, die beim Byte-Diffing zu False-Positives führen. EBT und `PyVenv` nutzen einen bidirektionalen Filter, der Skripte mit absoluten Pfaden (`bin/`, `pyvenv.cfg`) sowie Caches und Paket-Metadaten (`__pycache__`, `.dist-info`) systematisch ausklammert. Die Evaluierung fokussiert sich rein auf die semantischen Modifikationen (wie neu hinzugefügte Quellcodes im `site-packages`-Ordner).

### `PyVenv`-Attribute

#### Konfigurations-Attribute
* **`PyVenv.env_path`:** Speichert den Pfad zur Basis-Arena, die als Vorlage für den flüchtigen Klon dient, als `Path`-Objekt.
* **`PyVenv.codec`:** Eine Instanz des `IPCC`-Protokolls (standardmäßig `MSGspecCodec`), verantwortlich für die Serialisierung und Deserialisierung der I/O-Daten zwischen dem Host und der isolierten Umgebung.
* **`PyVenv.custom_id`** & **`PyVenv.arena_id`:** Die Identifikations-Attribute für die semantische Benennung und das garantierte Tracing vom temporären Workspace.

#### Pfad- und Zustands-Attribute
* **`PyVenv.workspace_path`:** Hält den absoluten Pfad (`Path`) zum temporär generierten Verzeichnis für den aktuellen Testlauf. 
* **`PyVenv.virtual_path`:** Zeigt direkt auf das isolierte `.venv`-Verzeichnis innerhalb vom Workspace, welches den dynamischen Klon darstellt.

#### Prozessierungs-Attribute
* **`PyVenv._config_state`:** Referenziert das bei der `setup()`-Methode übergebene `WorldState`-Objekt (den deklarierten Pre-State).
* **`PyVenv._actual_returns`:** Zwischenspeicher für die funktionalen Rückgabewerte des Targets nach dem erfolgreichen Abschluss des Subprozesses.
* **Interne Subprozess-Kontrolle:** Variablen wie `_python_exe`, `_env_vars`, `_in_path` (Input-Datei für IPC), `_out_path` (Output-Datei für IPC) und `_process` kapseln den genauen Zustand und die Interaktion mit dem Systemprozess.

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

### `TempFS`-Attribute

#### Konfigurations-Attribute
* **`TempFS.custom_id`** & **`TempFS.arena_id`:** Steuern – exakt wie bei `PyVenv` – die eindeutige Namensgebung des flüchtigen `tempfile`-Verzeichnisses für das Dateisystem.

#### Pfad- und Zustands-Attribute
* **`TempFS.workspace_path`:** Der absolute Pfad (`Path`) zum temporären Ordner, in den die in `WorldState.fs` deklarierten Dateien der Topologie projiziert werden.
* **`TempFS._original_cwd`:** Ein hochkritisches Sicherheits-Attribut. Es speichert den Pfad des ursprünglichen Host-Arbeitsverzeichnisses, um nach der Ausführung des Targets (oder im Fehlerfall) eine sichere Wiederherstellung via `os.chdir()` ins Host-System zu gewährleisten.

#### Prozessierungs-Attribute
* **`TempFS._config_state`:** Referenziert den durch die EBT-Engine übergebenen initialen Pre-State.
* **`TempFS._actual_returns`:** Fängt den direkten, unmodifizierten Rückgabewert des nativ im Host-Prozess ausgeführten Targets ab.