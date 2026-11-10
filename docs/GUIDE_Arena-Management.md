<center>

# Arena-Management

![Cubie](.assets/cubie-logo-written.png)

Arenen trennen die EBT-Orchestrierung von Aufbau und Ausführung einer Testumgebung. `TempFS` und `PyVenv` verwenden temporäre Arbeitsverzeichnisse und Kindprozesse. **Beide besitzen die Rechte des aufrufenden Benutzers und bilden keine OS-Sicherheitsgrenze.** Sie sind für vertrauenswürdigen Code vorgesehen. Die [Semantikreferenz](GUIDE_Contract-Semantics.md) definiert den Vertrag und seine Grenzen.

---

</center>

## TempFS: temporärer Datei-Workspace

`TempFS()` kopiert die in `pre.fs` gemappten Quellen in einen temporären Ordner und startet das Callable mit dem Host-Interpreter. Dessen installierte Pakete stehen weiterhin zur Verfügung. Der Arbeitsordner des Elternprozesses bleibt unverändert. Eine virtuelle Umgebung wird nicht kopiert.

Targets, Argumente, Rückgaben und übertragene Exceptions müssen mit Cloudpickle serialisierbar sein. Änderungen an übergebenen Python-Objekten und globalen Variablen werden nicht zurückgespiegelt. Die Ergebnisse sind deserialisierte Objekte mit eigener Identität. Für direkte Ausführung im aufrufenden Prozess kann EBT ohne Arena genutzt werden.

EBT prüft den Workspace vor dem Aufräumen. IPC-Dateien liegen außerhalb dieses Workspace. Ein vollständiges Dateibeispiel steht im [EBT-Nutzungshandbuch](GUIDE_EBT-Usage-Pattern.md). Jede gleichzeitig aktive Arena benötigt eine eigene Instanz.

Target-Exceptions werden mit einem Hinweis auf den Kindprozess-Traceback weitergegeben. Beendet sich der Kindprozess ohne vollständiges Ergebnis, meldet TempFS einen `RuntimeError`. EBT versucht auch bei Ausnahmen aufzuräumen. Das beseitigt den temporären Workspace, aber keine Seiteneffekte außerhalb dieses Verzeichnisses.

## PyVenv: kopierte virtuelle Umgebung

`PyVenv(env_path)` kopiert eine vorhandene virtuelle Umgebung in den Workspace und startet deren Interpreter. Ein String in `pre.arena` überschreibt bei aktiver `PyVenv` den Basispfad. Er erzeugt selbst keine ausführbare Arena.

Die Basis muss zur Maschine und zum Interpreter passen. Basisumgebungen werden nicht versioniert; auch der Standardpfad `src/qb_cubie/arenas/arena_envs/empty_test_env` muss vor der Verwendung von `PyVenv()` lokal provisioniert werden. `setup()` prüft die Codec-Anforderungen ausschließlich lesend. Bei fehlenden oder unpassenden Paketen bricht es vor dem Kopieren mit einem Hinweis auf den `ArenaBuilder` ab. Es startet keinen Installer und verändert die Basis nicht.

Der `ArenaBuilder` wird über `from qb_cubie.arenas.pyvenv import ArenaBuilder` importiert. `ArenaBuilder(path).with_packages([...]).build(codec=codec)` erzeugt beziehungsweise ergänzt eine Basis und liefert ein `PyVenv`-Objekt mit diesem Codec. Ohne Codec gilt `MSGspecCodec`. Der Builder installiert auch dessen Anforderungen. Er benötigt `uv` im `PATH` und verwendet den aufrufenden Python-Interpreter für neue Umgebungen. Provisionierung ist ein ausdrücklicher Vorbereitungsschritt und kann schreiben sowie Netzwerkzugriff benötigen.

```python
from qb_cubie import CloudpickleCodec
from qb_cubie.arenas.pyvenv import ArenaBuilder

# Einmaliger Installationsschritt vor den Tests:
arena = ArenaBuilder(".arenas/my_env").with_packages([
    "cloudpickle==3.1.2",
]).build(codec=CloudpickleCodec())
```

Bei späteren Läufen genügt `PyVenv(".arenas/my_env", codec=CloudpickleCodec())`. Ein Wechsel des Codecs kann erneute ausdrückliche Provisionierung erfordern. Auch ein Basispfad aus `pre.arena` muss bereits vollständig vorbereitet sein.

### Provisionierung der Testbasen

Nach `uv sync --locked --group dev` im Repository ausführen:

```bash
.venv/bin/python scripts/provision_test_arenas.py
.venv/bin/python -m pytest -q
```

Unter Windows den Projektinterpreter `.venv\Scripts\python.exe` verwenden. Das Skript erzeugt folgende ignorierten Verzeichnisse:

| Basis | Pakete zusätzlich zur Python-Standardbibliothek |
| --- | --- |
| `src/qb_cubie/arenas/arena_envs/empty_test_env` (`PyVenv()`-Standard) | `msgspec==0.22.0`, `cloudpickle==3.1.2` |
| `tests/.arenas/empty_venv` | dieselben Codec-Pakete |
| `tests/.arenas/cowsay_env` | Codec-Pakete und `cowsay==6.1` |
| `tests/.arenas/linter_env` | Codec-Pakete und `pylint==4.1.3` samt Abhängigkeiten |

Die Codec- und Pylint-Versionen entsprechen `uv.lock`; transitive Arena-Abhängigkeiten löst `uv` während der Provisionierung auf. Das Skript darf wiederholt werden und installiert nur bei nicht erfüllten Anforderungen. Es entfernt keine zusätzlichen Pakete aus bestehenden Basen. Für einen sauberen Neuaufbau die betreffenden generierten Verzeichnisse entfernen und das Skript erneut aufrufen, insbesondere nach einem Python- oder Maschinenwechsel. Provisionierung vor parallelen Testläufen abschließen; nicht gleichzeitig auf dieselben Basen provisionieren.

Pytest ruft die Provisionierung nicht automatisch auf. Die Tests für Paketmutationen installieren beziehungsweise deinstallieren absichtlich `cowsay` **im temporären Klon** und benötigen weiterhin `uv` sowie einen passenden Paketcache oder Netzwerkzugriff. Die Offline-Regressionen in `tests/test_offline_core.py` verwenden eigene Fixtures ohne Download.

Eine Umgebungsänderung kann über `post.arena` gegen einen vorhandenen Vergleichspfad geprüft werden. Der Vergleich ignoriert unter anderem Startskripte, Caches und `.dist-info`. Ein solcher Dateiabgleich beweist keine semantische Gleichheit oder korrekte Paketauflösung.

## Codecs und Prüfprädikate

`PyVenv` nutzt standardmäßig `MSGspecCodec`. Er transportiert unterstützte Daten über MessagePack und löst Target-Referenzen über Modul und qualifizierten Namen auf. Zielmodule müssen in der Ausführungsumgebung erreichbar sein. `PickleCodec` und `CloudpickleCodec` bieten andere Serialisierungsmöglichkeiten; Cloudpickle unterstützt beispielsweise viele lokale Funktionen und komplexere Objektzustände.

Die Wahl hängt von den **übertragenen** Targets, Argumenten und Rückgaben ab. Ein Lambda in `post.returns` oder `post.fs` wird beim normalen Arena-Lauf erst im Elternprozess ausgewertet und erfordert für sich keinen Cloudpickle-Codec. Bei zusätzlichem EBT-Multiprocessing muss allerdings auch der Aufgabenkontext zwischen Workern übertragen werden.

Pickle und Cloudpickle können bei der Deserialisierung Code ausführen. MessagePack vermeidet diesen konkreten Mechanismus, entzieht dem Target aber keine Hostrechte und schützt nicht vor gefälschten Ergebnissen. `CloudpickleCodec(isolation=1)` aktiviert derzeit nur einen leeren Platzhalter und schafft keine zusätzliche Dependency-Isolation.

## Laufzeit und Ausgabe begrenzen

Beide Arenen akzeptieren die optionalen Schlüsselwortargumente `timeout`
(positive, endliche Sekunden) und `max_output_bytes` (nichtnegative ganze Zahl).
`None` deaktiviert das jeweilige Limit; standardmäßig sind beide deaktiviert.
Beispielsweise führt diese Arena jeden Target-Aufruf mit höchstens fünf Sekunden
Laufzeit und zusammen 64 KiB stdout/stderr aus:

```python
from qb_cubie import EBT, TempFS, WorldState

EBT(
    target=lambda: "fertig",
    arena=TempFS(timeout=5, max_output_bytes=65536),
    post=WorldState(returns="fertig"),
).run()
```

Für eine vorbereitete Umgebung gilt entsprechend
`PyVenv(".arenas/my_env", timeout=5, max_output_bytes=65536)`.
Die Limits gelten auch bei direktem `arena.run(...)`. Die Frist beginnt vor dem
Start des Runner-Prozesses und umfasst dessen Ausführung und das Schreiben der
IPC-Rückgabe; Aufbau, Hydrierung, Klonen und Deserialisierung im Elternprozess
sind nicht eingeschlossen. Jeder Eingang erhält eine eigene Frist.

Das Ausgabelimit zählt rohe Bytes beider Streams gemeinsam, einschließlich
nativer Ausgabe und Ausgabe von Nachkommen mit geerbten Kanälen. Genau das
Budget ist erlaubt; `0` erlaubt nur stille Targets. Die Kanäle werden gleichzeitig
gelesen, und mit aktivem Ausgabelimit bleibt die Puffergröße proportional zum
Budget. TempFS gibt erfasste Ausgabe erst nach Prozessende weiter; PyVenv hält
sie für seine Fehlerdiagnose vor. Bei Überschreitung wird die Ausgabe verworfen
und eine kurze Fehlermeldung zurückgegeben.

Ein Timeout löst `TimeoutError` aus, eine Ausgabeüberschreitung `RuntimeError`.
Auch `EBT(expect=False)` wandelt solche Abbrüche nicht in einen Erfolg um.
Die Überwachung beendet bei Abbruch die eigene Prozessgruppe mit `SIGTERM`
und nach bis zu 0,2 Sekunden mit `SIGKILL`. Das gilt auch bei unterbrochener
Überwachung und wenn der Runner bereits beendet ist, aber Nachkommen die Pipes
offen halten. Die Arena räumt anschließend Workspace und IPC-Dateien auf.
Die Beendigung und das Aufräumen können zusätzlich zur Frist Zeit benötigen.

Die neuen Limits erfordern POSIX-Prozessgruppen (Linux/macOS); auf Windows
werden gesetzte Limits vor der Ausführung mit `NotImplementedError` abgelehnt.
Aufrufe ohne Limits behalten ihr bisheriges Verhalten auf allen Plattformen.
Gezielt aus der Prozessgruppe ausgebrochene Prozesse werden nicht erfasst.
Dateiausgabe, IPC-Dateigröße und Speicher des Targets werden nicht begrenzt.

## Grenzen von Isolation und Reproduzierbarkeit

Targets können absolute Hostpfade, geerbte Umgebungsvariablen und verfügbare Netzwerkzugänge nutzen. Hydrierungsziele werden nicht auf den Workspace begrenzt: Verwende kontrollierte relative Pfade ohne `..`. Auch eine versehentliche absolute Pfadangabe kann außerhalb schreiben.

`PyVenv` kann ausgewählte Imports durch Phantom-Objekte ersetzen. Diese Importanpassung verändert die Testbedingungen und kann Fehler verdecken; sie entzieht keine Rechte. `PATH` und `VIRTUAL_ENV` wählen eine Umgebung aus, sie erzwingen keine OS-Isolation.

Ohne explizite Limits kann ein hängendes Target den Lauf blockieren; `PyVenv`
puffert dann stdout und stderr vollständig. Zusätzliche Worker, pytest-xdist und
Arena-Unterprozesse können die Ressourcenlast vervielfachen. Der
Multiprocessing-Fallback kann Aufgaben nach Fehlern erneut ausführen und
Seiteneffekte wiederholen.

`DockerArena` und `VmArena` sind nicht implementiert und nicht Teil der öffentlichen API. Die [Virtualisierungsentwürfe](feature-drafts/virtualization/README.md) beschreiben geplante Funktionen. Aussagen daraus gelten nicht für die vorhandenen Arenen.

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
