# EBT-MATRIX

Die EBT-Matrix ist ein dediziertes Benchmarking- und Stresstest-Modul **innerhalb der Cubie-Testsuite**. Ihr primärer Zweck ist es, die internen Mechanismen des Cubie-Frameworks unter extremen Lastbedingungen und komplexen $\{P\}S\{Q\}$-Konfigurationen automatisiert zu validieren.

---

## 1. Architektonischer Zweck

Die EBT-Matrix fungiert als zentrales Interface und Meta-Testing-Werkzeug für das Cubie-Framework, um dessen Kernkomponenten automatisiert zu validieren. Die primären Ziele umfassen:

* **Zentralisierte Nutzungs-Variationen:** Das automatisierte Durchspielen aller denkbaren Kombinationen aus Quantoren (All- und Existenzquantoren), Ausführungs-Vektoren und Topologien, ohne diese endlosen Permutationen jedes Mal händisch als isolierte Testfälle definieren zu müssen.
* **Gezielte Stress-Tests:** Die kontrollierte Auslastung der Engine und Sandbox-Protokolle durch Extremfälle (z. B. gigantische Listen-Zustände oder massive I/O-Belastung durch Rauschen), um die absoluten Belastbarkeitsgrenzen und Edge-Cases der Architektur abzusichern.
* **Performance-Benchmarking:** Die Generierung verlässlicher, reproduzierbarer Metriken zur Messung der Effizienz interner Implementierungen. Dies dient als essenzielle Entscheidungsgrundlage bei der iterativen Weiterentwicklung von Evaluierungs-Methoden (z. B. Byte-Diffing), neuen Arena-Konzepten oder der Multiprocessing-Orchestrierung.
* **Automatisierte Szenarien-Generierung:** Die bedarfsgesteuerte Erzeugung maßgeschneiderter, persistierbarer Datensätze zur isolierten Untersuchung spezifischer Aspekte (wie etwa dem Dateisystem-Mapping oder der Umgebungs-Isolierung) und deren Extrem-Varianten.

Die Auslagerung der Entwicklungs-Phasen in ein dediziertes Planungs-Dokument ("DEV-GUIDE_2-4_EBT-Matrix-Plan.md") und die Spiegelung der Dokumentations-Struktur von `../../docs/dev/example-based-testing/DEV-GUIDE_2-1_EBT-Class.md` ist eine hervorragende architektonische Entscheidung. Die strikte Trennung von Modul-Planung und systemischer Dokumentation beugt kognitiver Überlastung vor und hält die `DEV-GUIDE`-Dokumente zeitlos.

Deine definierte Modul-Strategie (`..`) fügt sich nahtlos in dieses Vorhaben ein. Die klare Separation in `ebt_matrix.py` (Orchestrator), isolierte Target-Klassen (z. B. `one_to_one.py`) und dedizierte Phasen-Tests (`test_matrix_arrange.py`) bietet die perfekte Grundlage, um die Pattern und den Lebenszyklus nun sauber zu spezifizieren.

Hier ist der detaillierte Entwurf für den neuen Abschnitt "## EBT-Matrix-Design", der sich exakt an der Blaupause der `EBT`-Klasse orientiert, aber die Meta-Ebene der Matrix abbildet.

---

## 2. EBT-Matrix-Design

### Pattern

#### Allgemeine Muster

Die Architektur der `EBTMatrix` agiert als Meta-Layer für das Cubie-Framework und folgt dem Prinzip des extremen "Dogfooding". Anstatt eigene Evaluierungs-Mechanismen zu implementieren, adaptiert die Matrix das fraktale Pipeline-Muster der nativen `EBT`-Klasse.
Ein zentrales Design-Muster ist hierbei die **Souveränität der Asset-Generierung**: Die komplexe Orchestrierung von Datei-Rauschen und asymmetrischen Daten-Vektoren (1:N, N:1) wird nicht zentral von der Matrix gesteuert, sondern algorithmisch an die dedizierten Targets (`MatrixTarget`) delegiert. Die Targets agieren dabei nach dem Prinzip der Idempotenz und Caching-Effizienz, indem sie atomare Bausteine (Memory, Filesystem, Environment) inkrementell generieren.

#### Komponenten

Die Matrix strukturiert ihre internen Verantwortlichkeiten analog zur Kern-Engine in ein klares Paradigma:

* **Datenmodelle:** Die strikte Typisierung der Test-Vektoren über reine Datenklassen (`Scenarios`, `Aspects`, `Overhead`), welche die Komplexitäts-Metriken deklarativ zusammenfassen.
* **MatrixTargets:** Isolierte Target-Klassen (z. B. `1:1` oder `N:1`), die sowohl die Logik der Datengenerierung (`build`) als auch die eigentliche Transformation (`target`) als unteilbare Einheit kapseln.
* **Pipes (Orchestrator):** Die zentralen Phasen-Orchestratoren der Matrix (`_arrange`, `_execute`, `_report`), welche den sequenziellen Datenfluss durch die Makro-Architektur steuern und die Delegation an das native Cubie-Framework übernehmen.



---

### Lebenszyklus

#### Matrix-Runs (Die Meta-Makro-Ebene)

Ein Matrix-Run repräsentiert den gesamten Lebenszyklus eines Benchmarking- oder Stresstest-Szenarios. Er aggregiert die übergebene `EBTMatrixConfig` und orchestriert die Bereitstellung der Test-Landschaft. Der Run garantiert, dass das Caching der atomaren Bausteine validiert wird, triggert die Assemblierung der Zielzustände durch das injizierte Target und reicht diese anschließend in die isolierte Ausführungsschicht weiter. Den Abschluss des Lebenszyklus bildet immer die Auswertung des Framework-Verhaltens und die Formatierung der generierten Metriken.

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
* Sie formatiert die gewonnenen Daten in einen standardisierten Benchmark-Report und evaluiert abschließend die Effizienz und Robustheit der Kernkomponenten unter den simulierten Extrembedingungen.

---

## 3. Das Matrix-Interface und Datenmodelle

Um die Test-Szenarien typsicher und logisch konsistent zu konfigurieren, nutzt die Matrix folgende Kern-Definitionen:

```python
from dataclasses import dataclass, field
from typing import Optional
from protocols import Arena

@dataclass
class Scenarios:
    # 1:1 → entsteht implizit, wenn beide Werte 1 sind.
    n_to_one: int = 1  # N:1 → Skaliert die Liste der pre-Zustände
    one_to_n: int = 1  # 1:N → Skaliert die Liste der post-Zustände
    # N:N → entsteht implizit, wenn beide Werte > 1 sind.

@dataclass
class Aspects:
    memory: int = 0       # 0 = inaktiv, > 0 = step_complexity für args/kwargs
    filesystem: int = 0   # 0 = inaktiv, > 0 = step_complexity für fs
    environment: int = 0  # 0 = inaktiv, > 0 = step_complexity für arena

@dataclass
class Overhead:
    fs: int = 0
    arena: int = 0

@dataclass
class EBTMatrixConfig:
    scenarios: Scenarios
    aspects: Aspects
    overhead: Overhead
    arena: Optional[Arena] = None
    multiprocessing: bool = False
```

---

## 4. Das `MatrixTarget`-Protokoll

Da die Targets (das $S$ im $\{P\}S\{Q\}$-Tripel) spezifisch für die verschiedenen Lösungsräume (N:1, 1:N) gebaut sein müssen, übernehmen sie selbst die Verantwortung für die Generierung ihrer Testdaten und das intelligente Verwalten ihrer Assets.

```python
from typing import Protocol, Tuple, List, Any
from pathlib import Path
from test_matrix.protocols import EBTMatrixConfig
from protocols import WorldState

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

    def build(self, config: EBTMatrixConfig, cache_root: Path) -> Tuple[List[WorldState], List[WorldState]]:
        """
        Orchestrates the incremental assembly of assets
        and composes the fully declared pre- and post-states for the engine from them.
        """
        ...

    def _build_pre(self): ...
    def _build_pre_memory(self, aspect: int): ...
    def _build_pre_filesystem(self, aspect: int): ...
    def _build_pre_environment(self, aspect: int): ...
    def _build_post(self): ...
    ...
```

## 5. Struktur und Caching-Strategie

Um exponentielles Wachstum und I/O-Flaschenhälse bei massiven Skalierungen (z. B. durch hohe Werte im `Overhead` oder den `Aspects`) zu verhindern, verzichtet das Framework auf redundante und flüchtige Run-Ordner. Stattdessen agieren die Targets als dedizierte Asset-Manager, die atomare Datenbausteine inkrementell generieren und zur Laufzeit modular zu `WorldState`-Objekten komponieren.

Die EBTMatrix nutzt hierfür eine strikt getrennte und persistente Ordnerstruktur innerhalb von `.matrix_cache/`:

```plaintext
.matrix_cache/noise/fs/                  # Globales Dateisystem-Rauschen (Overhead)
.matrix_cache/noise/env/                 # Globales Umgebungs-Rauschen (Overhead)
.matrix_cache/{cache_folder}/pre/memory/     # In-Memory-Bausteine (Args/Kwargs)
.matrix_cache/{cache_folder}/pre/filesystem/ # Komponierbare Ziel-Dateien
.matrix_cache/{cache_folder}/pre/environment/# Komponierbare Environments (Arenen)
.matrix_cache/{cache_folder}/post/       # Die resultierenden Nachbedingungen (post: WorldState)

```

**Der Kompositions-Workflow:**

* **Globale Entropie vs. Spezifische Logik:** Das Rauschen (`noise`), welches die Arena und das Dateisystem der Host-Umgebung belasten soll, wird global verwaltet und steht allen Targets gleichermaßen zur Verfügung. Logische, vom jeweiligen Target abhängige Bausteine werden im vom `MatrixTarget` definierten `cache_folder` isoliert persistiert.
* **Inkrementelles Auffüllen (`_build_pre_*`):** Fordert die `EBTMatrixConfig` über die Aspekte eine bestimmte Skalierung (z. B. `Aspects.filesystem=50`), prüft das Target den Bestand im eigenen Cache. Existieren dort bereits 30 komponierbare Dateien aus vorherigen Durchläufen, werden lediglich die fehlenden 20 atomaren Bausteine generiert. Dies macht das Skalieren von Matrix-Runs hochgradig effizient.
* **Dynamische Assemblierung:** Anstatt Dateien für den Testlauf physisch zu kopieren oder Ordner zu duplizieren, wählt die `build`-Methode die benötigten atomaren Dateien und Environments aus dem Cache aus.
* **Ableitung der resultierenden Nachbedingung (`_build_post`):** Auf Basis der soeben komponierten `pre`-Zustände berechnet das Target deterministisch die zu erwartenden funktionalen Rückgaben und Dateisystem-Mutationen. Diese Ergebnisse werden als "Golden Master" in den `post/`-Ordner geschrieben.