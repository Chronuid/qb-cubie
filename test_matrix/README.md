# EBT-MATRIX

Die EBT-Matrix ist ein dediziertes Benchmarking- und Stresstest-Modul **innerhalb der Cubie-Testsuite**. Ihr primärer Zweck ist es, die internen Mechanismen des Cubie-Frameworks unter extremen Lastbedingungen und komplexen $\{P\}S\{Q\}$-Konfigurationen automatisiert zu validieren.

---

## 1. Architektonischer Zweck

Die EBT-Matrix fungiert als zentrales Interface und Meta-Testing-Werkzeug für das Cubie-Framework, um dessen Kernkomponenten automatisiert zu validieren. Die primären Ziele umfassen:

* **Zentralisierte Nutzungs-Variationen:** Das automatisierte Durchspielen aller denkbaren Kombinationen aus Quantoren (All- und Existenzquantoren), Ausführungs-Vektoren und Topologien, ohne diese endlosen Permutationen jedes Mal händisch als isolierte Testfälle definieren zu müssen.
* **Gezielte Stress-Tests:** Die kontrollierte Auslastung der Engine und Sandbox-Protokolle durch Extremfälle (z. B. gigantische Listen-Zustände oder massive I/O-Belastung durch Rauschen), um die absoluten Belastbarkeitsgrenzen und Edge-Cases der Architektur abzusichern.
* **Performance-Benchmarking:** Die Generierung verlässlicher, reproduzierbarer Metriken zur Messung der Effizienz interner Implementierungen. Dies dient als essenzielle Entscheidungsgrundlage bei der iterativen Weiterentwicklung von Evaluierungs-Methoden (z. B. Byte-Diffing), neuen Arena-Konzepten oder der Multiprocessing-Orchestrierung.
* **Automatisierte Szenarien-Generierung:** Die bedarfsgesteuerte Erzeugung maßgeschneiderter, persistierbarer Datensätze zur isolierten Untersuchung spezifischer Aspekte (wie etwa dem Dateisystem-Mapping oder der Umgebungs-Isolierung) und deren Extrem-Varianten.

---

## 2. EBT-Matrix-Design

### Pattern

#### Allgemeine Muster

Ein zentrales Design-Muster ist die **Souveränität der Asset-Generierung**: Die komplexe Orchestrierung von Datei-Rauschen und asymmetrischen Daten-Vektoren (1:N, N:1) wird nicht zentral von der Matrix gesteuert, sondern algorithmisch an die dedizierten Targets (`MatrixTarget`) delegiert. Die Targets agieren dabei nach dem Prinzip der Idempotenz und Caching-Effizienz, indem sie atomare Bausteine (Memory, Filesystem, Environment) inkrementell generieren.

#### Komponenten

Die Matrix strukturiert ihre internen Verantwortlichkeiten analog zur Kern-Engine in ein klares Paradigma:

* **Datenmodelle:** Die strikte Typisierung der Test-Vektoren über reine Datenklassen (`Scenarios`, `Aspects`, `Overhead`), welche die Komplexitäts-Metriken deklarativ zusammenfassen.
* **MatrixTargets:** Isolierte Target-Klassen (z. B. `1:1` oder `N:1`), die sowohl die Logik der Datengenerierung (`build`) als auch die eigentliche Transformation (`target`) als unteilbare Einheit kapseln.
* **Pipes (Orchestrator):** Die zentralen Phasen-Orchestratoren der Matrix (`_arrange`, `_execute`, `_report`), welche den sequenziellen Datenfluss durch die Makro-Architektur steuern und die Delegation an das native Cubie-Framework übernehmen.



---

### Lebenszyklus

#### Matrix-Runs (Die Meta-Makro-Ebene)

Ein Matrix-Run repräsentiert den gesamten Lebenszyklus eines Benchmarking- oder Stresstest-Szenarios. Er aggregiert die übergebene `MatrixConfig` und orchestriert die Bereitstellung der Test-Landschaft. Der Run garantiert, dass das Caching der atomaren Bausteine validiert wird, triggert die Assemblierung der Zielzustände durch das injizierte Target und reicht diese anschließend in die isolierte Ausführungsschicht weiter. Den Abschluss des Lebenszyklus bildet immer die Auswertung des Framework-Verhaltens und die Formatierung der generierten Metriken.

#### Target-Generierung und Assemblierung

Während in regulären Tests der Entwickler die Zustände händisch deklariert, existiert in der Matrix ein vorgeschalteter Mikro-Lebenszyklus innerhalb des `MatrixTarget`-Objekts.
Bevor die Cubie-Engine gestartet wird, generiert das Target inkrementell die benötigten Entropie-Bausteine (wie Rausch-Dateien oder isolierte Umgebungen). Diese atomaren Fragmente werden anschließend deterministisch zu vollumfänglichen `WorldState`-Objekten für die Vorbedingung (`pre`) komponiert, um daraus den "Golden Master" für die Nachbedingung (`post`) abzuleiten.

---

### Phasen-Verantwortlichkeiten

#### Arrange (Generierung & Bereitstellung)

Diese Makro-Phase der Matrix agiert als intelligenter Cache-Manager und System-Vorbereiter.
* Sie konsumiert die abstrakten Skalierungs-Forderungen (Aspects, Overhead) der Konfiguration.
* Sie evaluiert das Dateisystem (`.matrix_cache/`), prüft den Bestand der geforderten Testdaten (Filesystem-Topologien und Environments) und verhindert redundante I/O-Lasten.
* Sie delegiert die finale Erzeugung und Assemblierung an die `build()`-Methode des Targets.
* **Ergebnis:** Zwei sauber strukturierte Listen aus `WorldState`-Objekten (`pre` und `post`), welche die exakte formallogische Index-Topologie für den anstehenden Testlauf definieren.

#### Execute (Testlauf via EBT-Delegation)

Die Execute-Phase führt keine eigene Test-Auswertung durch, sondern fungiert als reiner Proxy. Da die Matrix das Cubie-Framework validiert, baut sie in dieser Phase eine native `EBT`-Instanz auf.
* Sie injiziert das `MatrixTarget` funktional in das `EBT.target`-Attribut.
* Sie übergibt die generierten Zustands-Listen direkt an `EBT.pre` und `EBT.post`.
* Sie übersetzt Matrix-Konfigurationen (wie Sandbox-Deklarationen oder Multiprocessing) in native `EBT`-Parameter.
* Den Abschluss dieser Phase bildet der Aufruf der nativen `ebt.run()`-Methode, welche das eigentliche $\{P\}S\{Q\}$-Paradigma abarbeitet.

#### Report (Benchmarking & Konsolidierung)

Anstatt rohe String-Fehlermeldungen zu generieren, konsumiert diese abschließende Phase das durch die `EBT`-Klasse retournierte, unveränderliche `RunTrace`-Objekt.
* Da die `EBT`-Engine die formallogische Auswertung völlig wertungsfrei als Fakt in dieser Datenstruktur speichert, nutzt die Matrix den Trace als Datenquelle.
* Die Phase aggregiert Metriken aus den unzähligen durchlaufenen `EvaluationTrace`-Mikro-Steps (Performance, Diff-Zeiten, Arena-Overhead).
* Sie nutzt den MatrixReporter und lässt ihn die gewonnenen Daten in einen standardisierten Benchmark-Report formatieren.

---

## 3. Das Matrix-Interface und Datenmodelle

Um die Test-Szenarien typsicher und logisch konsistent zu konfigurieren, nutzt die Matrix folgende Kern-Definitionen:

```python
@dataclass
class Scenarios:
    one_to_one: int = 1
    n_to_one: int = 1
    one_to_n: int = 1
    n_to_n: int = 1

@dataclass
class Aspects:
    memory: int = 0       # 0 = inaktiv, > 0 = step_complexity für args/kwargs
    filesystem: int = 0   # 0 = inaktiv, > 0 = step_complexity für fs
    environment: int = 0  # 0 = inaktiv, > 0 = step_complexity für arena

@dataclass
class Overhead:
    fs: Optional[int] = 0
    arena: Optional[int] = 0

@dataclass
class MatrixConfig:
    scenarios: Scenarios
    aspects: Aspects
    overhead: Optional[Overhead]
    arena: Optional[Arena] = None
    multiprocessing: bool = False
```

---

## 4. Das `MatrixTarget`-Protokoll

Da die Targets (das $S$ im $\{P\}S\{Q\}$-Tripel) spezifisch für die verschiedenen Lösungsräume gebaut sein müssen, übernehmen sie selbst die Verantwortung für die Generierung ihrer Testdaten und das intelligente Verwalten ihrer Assets.

```python
class MatrixTarget(Protocol):
    matrix_type: str  # "1:1" | "N:1" | "1:N" | "N:N"
    cache_dir: str  # The name of the dedicated directory within .matrix_cache

    def target(self, *args, **kwargs) -> Any:
        """
        The actual implementation that performs the transformation.
        It must be equipped to handle the iterative processing of batch inputs (step_complexity)
        and navigate through noisy data.
        """
        ...
    def _execute_memory(self, *args, **kwargs) -> Any: ...
    def _execute_fs(self, *args, **kwargs) -> Any: ...
    def _execute_env(self, *args, **kwargs) -> Any: ...


    def build(self, config: MatrixConfig, cache_root: Path) -> Tuple[List[WorldState], List[WorldState]]:
        """
        Orchestrates the incremental assembly of assets
        and composes the fully declared pre- and post-states for the engine from them.
        """
        ...
    def _build_pre(self): ...
    def _build_post(self): ...
```

---

## 5. Matrix-Interface & Usage-Patterns

Basierend auf den übergebenen Skalaren der `MatrixConfig` deduziert die Matrix automatisch das benötigte Target (z. B. 1:1, 1:N, N:1) und generiert die entsprechende Entropie. Um dieses Paradigma sauber umzusetzen und gleichzeitig den direkten Vergleich verschiedener Testläufe zu ermöglichen, akzeptiert die `EBTMatrix` sowohl einzelne Konfigurationen als auch ganze Listen.

### Das Matrix-Interface und die Rolle des `MatrixReporter`

Das gesamte Handling der Ergebnisse – sei es die visuelle Formatierung, die vergleichende Darstellung oder das Werfen von test-spezifischen Assertions – wird vollständig an den `MatrixReporter` delegiert.
* **Formatierung & Gegenüberstellung:** Der Reporter konsumiert die rohen `MatrixReport`-DTOs und übersetzt diese in strukturierte Konsolen-Ausgaben, Benchmark-Tabellen oder Delta-Vergleiche.
* **Automatisierte Assertions:** Für die Integration in Test-Runner (wie Pytest) übernimmt der Reporter die Verantwortung, Schwellenwerte oder fehlgeschlagene Läufe zu erkennen und entsprechende Exceptions (z. B. `assert False`) zu werfen.
* **Headless-Rückfall:** Der Nutzer hat durch den Rückgabewert der `run()`-Methode zwar weiterhin den direkten Zugriff auf die DTOs, muss diese im regulären Arbeitsfluss aber nicht mehr händisch assertieren.

```python
class MatrixReporter(Protocol):
    """
    Protocol for EBT Matrix Benchmark result reporters.
    """
    # Konsumiert die fertigen DTOs und übernimmt jegliche visuelle Darstellung, 
    # Gegenüberstellung sowie das Werfen von Test-Runner-Assertions.
    def report(self, reports: Union[List[MatrixReport], MatrixReport]) -> None: 
        ...

    
class EBTMatrix:
    def __init__(
        self,
        configs: Union[List[MatrixConfig], MatrixConfig],
        reporter: Optional[MatrixReporter] = EBTMatrixReporter()
    ):
        self.CONFIGS: List[MatrixConfig] = configs if isinstance(configs, list) else [configs] # Normalisierung zu einer iterierbaren Liste
        self.reporter: MatrixReporter = reporter # Injektion des Reporters (Standard: EBTMatrixReporter)

    def run(self) -> Union[List[MatrixReport], MatrixReport]:
        # Orchestriert die Testläufe, delegiert die DTOs an self.reporter.report()
        # und gibt die reinen DTOs zur optionalen programmatischen Weiterverwendung zurück
        ...
```

### Usage-Patterns

Die folgenden Szenarien skizzieren die primären Anwendungsfälle der Matrix. Da der Reporter die gesamte Auswertung und Fehlerbehandlung übernimmt, reduziert sich der Test-Code auf die reine, deklarative Definition der Vektoren.

#### Pattern 1: Der einfache Stresstest (Single Config)

Der klassische Anwendungsfall, um die Engine unter einer spezifischen, isolierten Last zu testen. Hier wird gezielt ein massiver N:1-Lösungsraum (Allquantor) mit hohem Dateisystem-Rauschen generiert.

```python
def test_single_heavy_load():
    config = MatrixConfig(
        scenarios=Scenarios(one_to_one=250),  # 250 E2E Durchläufe
        aspects=Aspects(filesystem=50),      # Jeder Step vergleicht 50 Dateien
        overhead=Overhead(fs=100),           # jeweils 100 Dateien unbeteiligtes Noise im Hintergrund
        multiprocessing=True
    )
    # Ausführung: Die Matrix baut die Zustände und feuert die EBT-Engine.
    EBTMatrix(configs=config).run()

```

#### Pattern 2: A/B-Benchmarking (Listen-Vergleich)

Der größte architektonische Vorteil der `EBTMatrix` ist die Gegenüberstellung von Konfigurationen. Durch die Übergabe einer Liste von `MatrixConfig`-Objekten lassen sich spezifische Feature-Flags der Engine direkt miteinander vergleichen.

```python
def test_multiprocessing_efficiency(): # Wir testen identische I/O-Lasten, variieren aber die Skalierungs-Strategie
    base_scenarios = Scenarios(n_to_one=500)
    base_aspects = Aspects(filesystem=100)
    
    config_single = MatrixConfig(
        scenarios=base_scenarios, 
        aspects=base_aspects, 
        multiprocessing=False
    )
    config_multi = MatrixConfig(
        scenarios=base_scenarios, 
        aspects=base_aspects, 
        multiprocessing=True
    )
    # Der Reporter erkennt die Liste und wechselt automatisch in den Vergleichsmodus.
    # Er stellt die Laufzeiten und Diffing-Zeiten tabellarisch gegenüber und 
    # assertiert bei Bedarf (z. B. wenn Multi- nicht schneller als Singleprocessing ist).
    reports = EBTMatrix(configs=[config_single, config_multi]).run()

```

#### Pattern 3: Arena-Overhead Profiling

Hierbei wird nicht die Skalierung der Eingabedaten ($P$), sondern die physische Ausführungsumgebung ($S$) durchleuchtet. Das Pattern vergleicht den formallogischen Overhead unterschiedlicher Sandbox-Implementierungen.

```python
def test_arena_provisioning_overhead(): # Identische funktionale Last, unterschiedliche Arenen
    config_tempfs = MatrixConfig(
        scenarios=Scenarios(n_to_one=100),
        arena=TempFS() # Leichtgewichtiges In-Memory-Filesystem
    )
    config_pyvenv = MatrixConfig(
        scenarios=Scenarios(n_to_one=100),
        arena=PyVenv() # Vollständige Subprozess-Isolation
    )
    # Der Reporter visualisiert nun exakt die Delta-Zeiten für das Provisioning 
    # zwischen einem simplen Temp-Ordner und einer echten Virtual Environment.
    reports = EBTMatrix(configs=[config_tempfs, config_pyvenv]).run()
```