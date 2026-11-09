# Arena-Management

Arenen trennen die EBT-Orchestrierung von Aufbau und Ausführung einer Testumgebung. `TempFS` und `PyVenv` verwenden temporäre Arbeitsverzeichnisse und Kindprozesse. **Beide besitzen die Rechte des aufrufenden Benutzers und bilden keine OS-Sicherheitsgrenze.** Sie sind für vertrauenswürdigen Code vorgesehen. Die [Semantikreferenz](GUIDE_Contract-Semantics.md) definiert den Vertrag und seine Grenzen.

## TempFS: temporärer Datei-Workspace

`TempFS()` kopiert die in `pre.fs` gemappten Quellen in einen temporären Ordner und startet das Callable mit dem Host-Interpreter. Dessen installierte Pakete stehen weiterhin zur Verfügung. Der Arbeitsordner des Elternprozesses bleibt unverändert. Eine virtuelle Umgebung wird nicht kopiert.

Targets, Argumente, Rückgaben und übertragene Exceptions müssen mit Cloudpickle serialisierbar sein. Änderungen an übergebenen Python-Objekten und globalen Variablen werden nicht zurückgespiegelt. Die Ergebnisse sind deserialisierte Objekte mit eigener Identität. Für direkte Ausführung im aufrufenden Prozess kann EBT ohne Arena genutzt werden.

EBT prüft den Workspace vor dem Aufräumen. IPC-Dateien liegen außerhalb dieses Workspace. Ein vollständiges Dateibeispiel steht im [EBT-Nutzungshandbuch](GUIDE_EBT-Usage-Pattern.md). Jede gleichzeitig aktive Arena benötigt eine eigene Instanz.

Target-Exceptions werden mit einem Hinweis auf den Kindprozess-Traceback weitergegeben. Beendet sich der Kindprozess ohne vollständiges Ergebnis, meldet TempFS einen `RuntimeError`. EBT versucht auch bei Ausnahmen aufzuräumen. Das beseitigt den temporären Workspace, aber keine Seiteneffekte außerhalb dieses Verzeichnisses.

## PyVenv: kopierte virtuelle Umgebung

`PyVenv(env_path)` kopiert eine vorhandene virtuelle Umgebung in den Workspace und startet deren Interpreter. Ein String in `pre.arena` überschreibt bei aktiver `PyVenv` den Basispfad. Er erzeugt selbst keine ausführbare Arena.

Die Basis muss zur Maschine und zum Interpreter passen. Die mitgelieferte Basisumgebung ist kein portabler Standard für frische Checkouts. Verwende eine eigens provisionierte Umgebung und dokumentiere deren Paketversionen. Fehlende Codec-Anforderungen kann `setup()` per `uv pip install` in der **Basisumgebung** nachinstallieren; das kann schreiben, Netzwerkzugriff benötigen und bei parallelen Tests konkurrieren.

Der vorhandene `ArenaBuilder` wird über `from cubie.arenas.pyvenv import ArenaBuilder` importiert. `ArenaBuilder(path).with_packages([...]).build()` erzeugt beziehungsweise ergänzt eine Basis und liefert ein `PyVenv`-Objekt. Provisionierung sollte ein ausdrücklich geplanter Vorbereitungsschritt sein; sie ist kein rein lesender Testaufbau.

Eine Umgebungsänderung kann über `post.arena` gegen einen vorhandenen Vergleichspfad geprüft werden. Der Vergleich ignoriert unter anderem Startskripte, Caches und `.dist-info`. Ein solcher Dateiabgleich beweist keine semantische Gleichheit oder korrekte Paketauflösung.

## Codecs und Prüfprädikate

`PyVenv` nutzt standardmäßig `MSGspecCodec`. Er transportiert unterstützte Daten über MessagePack und löst Target-Referenzen über Modul und qualifizierten Namen auf. Zielmodule müssen in der Ausführungsumgebung erreichbar sein. `PickleCodec` und `CloudpickleCodec` bieten andere Serialisierungsmöglichkeiten; Cloudpickle unterstützt beispielsweise viele lokale Funktionen und komplexere Objektzustände.

Die Wahl hängt von den **übertragenen** Targets, Argumenten und Rückgaben ab. Ein Lambda in `post.returns` oder `post.fs` wird beim normalen Arena-Lauf erst im Elternprozess ausgewertet und erfordert für sich keinen Cloudpickle-Codec. Bei zusätzlichem EBT-Multiprocessing muss allerdings auch der Aufgabenkontext zwischen Workern übertragen werden.

Pickle und Cloudpickle können bei der Deserialisierung Code ausführen. MessagePack vermeidet diesen konkreten Mechanismus, entzieht dem Target aber keine Hostrechte und schützt nicht vor gefälschten Ergebnissen. `CloudpickleCodec(isolation=1)` aktiviert derzeit nur einen leeren Platzhalter und schafft keine zusätzliche Dependency-Isolation.

## Grenzen von Isolation und Reproduzierbarkeit

Targets können absolute Hostpfade, geerbte Umgebungsvariablen und verfügbare Netzwerkzugänge nutzen. Hydrierungsziele werden nicht auf den Workspace begrenzt: Verwende kontrollierte relative Pfade ohne `..`. Auch eine versehentliche absolute Pfadangabe kann außerhalb schreiben.

`PyVenv` kann ausgewählte Imports durch Phantom-Objekte ersetzen. Diese Importanpassung verändert die Testbedingungen und kann Fehler verdecken; sie entzieht keine Rechte. `PATH` und `VIRTUAL_ENV` wählen eine Umgebung aus, sie erzwingen keine OS-Isolation.

Beide Arenen haben keine konfigurierbare Target-Ausführungsfrist; ein hängendes Target kann den Lauf blockieren. `PyVenv` puffert stdout und stderr vollständig. Zusätzliche Worker, pytest-xdist und Arena-Unterprozesse können die Ressourcenlast vervielfachen. Der Multiprocessing-Fallback kann Aufgaben nach Fehlern erneut ausführen und Seiteneffekte wiederholen.

`DockerArena` und `VmArena` sind nicht implementiert und nicht Teil der öffentlichen API. Die [Virtualisierungsentwürfe](feature-drafts/virtualization/README.md) beschreiben geplante Funktionen. Aussagen daraus gelten nicht für die vorhandenen Arenen.
