<center>

# Arenen und IPC-Codecs

![Cubie](../.assets/cubie-logo-written.png)

Arenen implementieren die Ausführungsschicht für konkrete EBT-Fälle. Die beiden vorhandenen Arenen sind Prozess- und Workspace-Abstraktionen ohne OS-Sicherheitsgrenze. Die [Vertragssemantik](../GUIDE_Contract-Semantics.md) und das [Arena-Nutzungshandbuch](../GUIDE_Arena-Management.md) beschreiben die verbindlichen Grenzen.

---

</center>

## Arena-Protokoll und Lebenszyklus

`cubie.protocols.Arena` verlangt:

- `workspace_path`: Pfad des vorbereiteten Workspace, vorher gegebenenfalls `None`.
- `setup(state)`: Erstellt die Umgebung und kopiert deklarierte Dateiquellen.
- `execute(target, args, kwargs)`: Führt das Target aus und liefert den Rückgabewert.
- `get_state()`: Liefert einen `WorldState` mit Rückgabe und aktuellen Workspace-/Umgebungspfaden.
- `teardown()`: Entfernt die temporäre Umgebung.

EBT erfasst den Zustand und vergleicht die Dateien vor `teardown()`. In Traces gespeicherte Pfade sind danach keine persistenten Dateiartefakte. Aufräumen entfernt keine externen Seiteneffekte und stellt nicht den gesamten Hostzustand wieder her.

## TempFS

`TempFS(custom_id=None)` startet mit `sys.executable` einen frischen Kindprozess, dessen CWD der Workspace ist. Der Elternprozess ändert sein CWD nicht. Das Callable und seine Argumente sowie Ergebnisse werden mit Cloudpickle übertragen. Mutationen an normalen Python-Objekten im Kind werden nicht zurückgespiegelt. IPC-Dateien liegen außerhalb des Workspace.

Eine gleichzeitig aktive Lebensphase benötigt eine eigene Arena-Instanz. `run()` kapselt bei eigenständiger Nutzung Aufbau, Ausführung und Aufräumen. EBT verwendet stattdessen die einzelnen Protokollmethoden, damit der Vergleich vor dem Aufräumen stattfinden kann.

## PyVenv

`PyVenv(env_path=..., codec=None, decontams=None, custom_id=None)` verwendet standardmäßig `MSGspecCodec`. `setup()` wählt den Basispfad aus `pre.arena`, wenn dort ein String steht, sonst aus `env_path`. Fehlende Codec-Abhängigkeiten können vor dem Kopieren in der Basis nachinstalliert werden. Die Basis ist somit nicht zwingend unveränderlich.

`workspace_path` bezeichnet den temporären Arbeitsordner und `virtual_path` dessen kopierte `.venv`. Das Target läuft mit dem Interpreter dieser Kopie. `get_state()` liefert den Workspace als `fs` und die virtuelle Umgebung als `arena` zurück. Der Vergleich einer erwarteten Umgebung ist ein gefilterter Dateiabgleich, kein Nachweis identischer Laufzeitbedingungen.

`_prepare_env()` übernimmt Host-Umgebungsvariablen und setzt unter anderem `PATH` und `VIRTUAL_ENV`. Das beeinflusst die Programmauswahl, entzieht aber keine Rechte. Die Import-Middleware ersetzt ausgewählte Module durch Phantom-Objekte; sie ist eine Anpassung der Importbedingungen und kein Schutz gegen nicht vertrauenswürdigen Code.

Der `ArenaBuilder` aus `cubie.arenas.pyvenv` provisioniert Basen über `uv` und kann Pakete installieren. `.build()` liefert eine `PyVenv`-Instanz. Die eingecheckte Standardbasis ist kein zugesicherter portabler Ersatz für diesen Vorbereitungsschritt.

## IPCC und Codec-Auswahl

Das `IPCC`-Protokoll definiert `file_suffix`, `requirements`, `dump(obj, path)`, `load(path)` und `get_runner_snippet(in_path, out_path)`.

`MSGspecCodec` nutzt MessagePack für unterstützte Payloads und eine Modul-/Namensreferenz für das Target. `PickleCodec` verwendet Python-Pickle. `CloudpickleCodec` unterstützt zusätzliche dynamische Callables und Objektzustände; dabei können auch Host-Abhängigkeiten in den Payload gelangen. Sein `isolation`-Parameter bietet derzeit keine zusätzliche Dependency-Isolation: `_apply_dependency_isolation()` ist ein leerer Platzhalter.

Post-Prädikate werden beim normalen Arena-Lauf auf dem Host ausgewertet und verlangen für sich keinen bestimmten Arena-Codec. Werden sie durch EBT-Multiprocessing an Worker übertragen, gilt zusätzlich die Serialisierungsanforderung dieses Backends.

Pickle/Cloudpickle-Deserialisierung kann Code ausführen. MessagePack reduziert diesen konkreten Angriffsweg, schafft aber weder eine OS-Sicherheitsgrenze noch eine vertrauenswürdige Ergebnisquelle für bösartige Targets.

## Identifikation und Betriebsgrenzen

`custom_id` fließt in `arena_id` mit einem achtstelligen UUID-Anteil ein. Temporäre Verzeichnisse erhalten zusätzlich von `tempfile.mkdtemp` erzeugte Namen. Die IDs helfen bei der Zuordnung; sie sind kein Beweis absoluter Eindeutigkeit.

Es gibt keine konfigurierbare Target-Ausführungsfrist. `PyVenv` puffert die gesamte Standardausgabe und Fehlerausgabe. Dateiziele werden nicht auf den Workspace begrenzt; absolute Pfade und `..` können außerhalb schreiben. Rechte, Netzwerk und geerbte Variablen bleiben grundsätzlich verfügbar.

Docker-/VM-Arenen existieren nur als [Feature-Entwürfe](../feature-drafts/virtualization/README.md). Deren geplante Eigenschaften sind keine Garantien des aktuellen Arena-Protokolls oder seiner Implementierungen.

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
