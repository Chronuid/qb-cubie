<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Arenen und IPC-Codecs

![Cubie](../.assets/cubie-logo-written.png)

Arenen implementieren die Ausführungsschicht für konkrete EBT-Fälle. Die beiden vorhandenen Arenen sind Prozess- und Workspace-Abstraktionen ohne OS-Sicherheitsgrenze. Die [Vertragssemantik](../core/GUIDE_Contract-Semantics.md) und das [Arena-Nutzungshandbuch](../core/GUIDE_Arena-Management.md) beschreiben die verbindlichen Grenzen.

---

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Arena-Protokoll und Lebenszyklus

`qb_cubie.protocols.Arena` verlangt:

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

`PyVenv(env_path=None, codec=None, decontams=None, custom_id=None)` verwendet standardmäßig `MSGspecCodec`. Ohne `env_path` löst `default_arena_path()` den Basispfad extern über `QB_CUBIE_DEFAULT_ARENA` oder den Plattform-Benutzer-Cache (`qb-cubie/arenas/py<major>.<minor>-empty`) auf, sodass keine Arena-Basen im Core-Paket liegen. `setup()` wählt den Basispfad aus `pre.arena`, wenn dort ein String steht, sonst aus `env_path`. Es prüft Codec-Abhängigkeiten ausschließlich lesend und meldet fehlende Anforderungen vor dem Kopieren. Installation und Änderungen an der Basis gehören zum ausdrücklichen Provisionierungsschritt.

`PyVenv.setup()` legt einen gemeinsamen temporären Laufzeit-Root (`_root_path`) mit getrenntem `workspace_path` (`workspace/`, fachlicher Arbeitsordner für `CWD`, `pre.fs` und `post.fs`) und `virtual_path` (`.venv/`, geklonte virtuelle Umgebung) an. Pro `execute()`-Lauf verwaltet `_run_in_subprocess()` zusätzlich ein temporäres IPC-/Phantom-Verzeichnis (`ipc_*` mit `ipc_in<suffix>`, `ipc_out<suffix>` und `_cubie_phantom.py`) unterhalb von `_root_path`, das im Anschluss atomar abgeräumt wird. Das Target läuft mit dem Interpreter von `virtual_path`. `get_state()` liefert den sauberen Workspace als `fs` und die virtuelle Umgebung als `arena` zurück. Der Vergleich einer erwarteten Umgebung ist ein gefilterter Dateiabgleich, kein Nachweis identischer Laufzeitbedingungen.

Vor der Hydrierung passt `_relocation.relocate_scripts()` unterstützte POSIX-Python-Einstiegsskripte an den Klon an. Nicht unterstützte Launcher werden vor der Target-Ausführung abgelehnt. Insbesondere sind zusätzliche native Windows-`.exe`-Launcher ausgeschlossen. Der genaue Umfang und die Grenzen stehen im [Arena-Handbuch](../core/GUIDE_Arena-Management.md#pyvenv-kopierte-virtuelle-umgebung).

`_prepare_env()` übernimmt Host-Umgebungsvariablen und setzt unter anderem `PATH` und `VIRTUAL_ENV`. Das beeinflusst die Programmauswahl, entzieht aber keine Rechte. Die Import-Middleware ersetzt ausgewählte Module durch Phantom-Objekte; sie ist eine Anpassung der Importbedingungen und kein Schutz gegen nicht vertrauenswürdigen Code.

Der `ArenaBuilder` aus `qb_cubie.arenas.pyvenv` provisioniert Basen über `uv` mit dem aufrufenden Python-Interpreter (ohne `env_path` am `default_arena_path()`). `.build(codec=None)` installiert die registrierten Pakete sowie die Anforderungen des gewählten Codecs und liefert eine entsprechend konfigurierte `PyVenv`-Instanz. Bereits vollständig erfüllte Anforderungen verursachen keine Installation. Lokale Testbasen sind durch die Root-`.gitignore` ausgeschlossen; die Standard-Arena liegt außerhalb des Core-Pakets im Benutzer-Cache. Ein frischer Checkout benötigt vor pytest den im [Arena-Handbuch](../core/GUIDE_Arena-Management.md#provisionierung-der-testbasen) dokumentierten Aufruf von `scripts/provision_test_arenas.py`; das erzeugt auch die externe `PyVenv()`-Standardbasis. Pytest selbst provisioniert keine gemeinsamen Basen.

## IPCC und Codec-Auswahl

Das `IPCC`-Protokoll definiert `file_suffix`, `requirements`, `dump(obj, path)`, `load(path)` und `get_runner_snippet(in_path, out_path)`.

`MSGspecCodec` nutzt MessagePack für unterstützte Payloads und eine Modul-/Namensreferenz für das Target. `PickleCodec` verwendet Python-Pickle. `CloudpickleCodec` unterstützt zusätzliche dynamische Callables und Objektzustände; dabei können auch Host-Abhängigkeiten in den Payload gelangen. Sein `isolation`-Parameter bietet derzeit keine zusätzliche Dependency-Isolation: `_apply_dependency_isolation()` ist ein leerer Platzhalter.

`PyVenv` startet den Kindprozess mit `python -P -c <script>` (ohne implizites `cwd` auf `sys.path[0]`) und stellt das temporäre IPC-Verzeichnis beim Start über `PYTHONPATH` bereit (während leere und `"."`-Einträge aus dem Host-`sys.path` herausgefiltert werden). Die drei eingebauten Codecs importieren zuerst die Transportmodule sowie `_cubie_phantom`, lösen anschließend sowohl `_cubie_phantom` aus `sys.modules` als auch das IPC-Verzeichnis aus `sys.path` und `PYTHONPATH` ab und fügen erst danach `os.getcwd()` als `sys.path[0]` ein. Eigene `IPCC`-Implementierungen sollten dieses Transport-First-Muster übernehmen, sobald ihre Runner Workspace-Module aus `cwd` importieren.

Post-Prädikate werden beim normalen Arena-Lauf auf dem Host ausgewertet und verlangen für sich keinen bestimmten Arena-Codec. Werden sie durch EBT-Multiprocessing an Worker übertragen, gilt zusätzlich die Serialisierungsanforderung dieses Backends.

Pickle/Cloudpickle-Deserialisierung kann Code ausführen. MessagePack reduziert diesen konkreten Angriffsweg, schafft aber weder eine OS-Sicherheitsgrenze noch eine vertrauenswürdige Ergebnisquelle für bösartige Targets.

## Identifikation und Betriebsgrenzen

`custom_id` fließt in `arena_id` mit einem achtstelligen UUID-Anteil ein. Temporäre Verzeichnisse erhalten zusätzlich von `tempfile.mkdtemp` erzeugte Namen. Die IDs helfen bei der Zuordnung; sie sind kein Beweis absoluter Eindeutigkeit.

Beide Arenen delegieren an `_process.run_process()`. Die optionalen POSIX-Limits
`timeout` und `max_output_bytes` begrenzen Runner-Laufzeit und gemeinsame
stdout/stderr-Ausgabe. Die Überwachung liest beide Pipes gleichzeitig und beendet
bei Abbruch die eigene Prozessgruppe mit SIGTERM/SIGKILL. Ohne Limits bleibt das
bisherige Ausführungsverhalten erhalten; PyVenv puffert dann weiterhin die gesamte
Ausgabe. Siehe [Arena-Handbuch](../core/GUIDE_Arena-Management.md#laufzeit-und-ausgabe-begrenzen).
Die `pre.fs`-Hydrierung begrenzt Kopierziele auf den fachlichen Workspace (absolute Pfade, ausbrechende `..`-Komponenten und entweichende Symlinks/Junctions werden mit `ValueError` abgelehnt). Für laufende Targets selbst werden Dateiziele nicht eingeschränkt; Rechte, Netzwerk und geerbte Variablen bleiben grundsätzlich verfügbar.

Docker-/VM-Arenen existieren nur als [Feature-Entwürfe](../feature-drafts/virtualization/README.md). Deren geplante Eigenschaften sind keine Garantien des aktuellen Arena-Protokolls oder seiner Implementierungen.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  
[↦ | Review-Based Testing | ↤](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md)  
[↦ | RBT-Klassen | ↤](./DEV-GUIDE_1-1_RBT-Classes.md)  
[↦ | EBT: Entwicklerübersicht | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Die EBT-Klasse | ↤](./DEV-GUIDE_2-1_EBT-Class.md)  
[↦ | WorldState | ↤](./DEV-GUIDE_2-2_WorldState-Class.md)  
[↦ | Arenen und IPC-Codecs | ↤](./DEV-GUIDE_2-3_Arenas.md)  
[↦ | `Multiprocessors` | ↤](./DEV-GUIDE_2-4_Multiprocessors.md)  
[↦ | `Linter` | ↤](./DEV-GUIDE_2-5_Linter.md)  
[↦ | DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes | ↤](./DEV-GUIDE_Next-Steps.md)  
[↦ | DEV-GUIDE: Release-Vorbereitung und sauberer Release | ↤](./DEV-GUIDE_Release-Preparation.md)  
[↦ | DEV-GUIDE: Bugs dokumentieren (`KNOWN_ISSUES.md`) | ↤](./DEV-GUIDE_Write-down-the-bugs.md)  
[↦ | Styleguide | ↤](./Style-Guide.md)  

</div>
<!-- /qb:frame -->
