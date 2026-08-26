# **Sicherheits- und Schwachstellenanalyse für die PyVenv-Arena: Architekturoptimierungen und Testfallszenarien**

Die vorliegende Untersuchung liefert eine tiefgreifende Sicherheitsanalyse der Implementierung einer leichtgewichtigen Python-Ausführungsumgebung, im Folgenden als PyVenv-Arena bezeichnet. Basierend auf dem funktionalen Kern der bereitgestellten Klasse PyVenv1 wird evaluiert, inwiefern die Architektur gegen mutwillige oder unabsichtliche Systemkompromittierungen (Jailbreaks), Code-Injektionen und Privilege Escalations (Rechteausweitungen) abgesichert ist.  

## **1\. Die Inter-Prozess-Kommunikation (IPC) und die Gefahren der Deserialisierung**
> Note: DONE! MSGspecCodec integriert!

Das pickle-Modul ist in der Python-Standardbibliothek inhärent unsicher konzipiert, wenn es um die Verarbeitung von Daten geht, die eine Vertrauensgrenze (Trust Boundary) überschritten haben7. Der Deserialisierungsprozess (pickle.load()) erzeugt nicht nur Datenstrukturen, sondern rekonstruiert komplexe Objekte, indem er Anweisungen einer Stack-Maschine ausführt8. Ein weithin bekannter Angriffsvektor nutzt hierfür die sogenannten magischen Methoden \_\_reduce\_\_ oder \_\_reduce\_ex\_\_8. Diese Methoden erlauben es einem Python-Objekt zu definieren, wie es beim Unpickling rekonstruiert werden soll. Die Methode gibt ein Tupel zurück, das aus einem Callable (beispielsweise os.system oder subprocess.Popen) und einem Tupel von Argumenten für dieses Callable besteht12. Sobald pickle.load() aufgerufen wird, ruft die Python-Virtual-Machine dieses Callable mit den bereitgestellten Argumenten auf, ohne jegliche Validierung oder Sandbox-Restriktionen durchzuführen7.  
Dadurch ergeben sich zwei schwerwiegende Angriffsvektoren. Der erste Vektor zielt auf die Kompromittierung der Arena selbst ab. Hierbei werden ein manipuliertes Target (das der Arena übergeben wird) oder manipulierte Argumente in die Datei \_in\_path geschrieben1. Das vom Runner-Skript in der Arena ausgeführte pickle.load() triggert den Exploit, was zu einer Code-Ausführung innerhalb der Arena führt1. Da die Arena ohnehin zur Ausführung von Code gedacht ist, ist dieser Vektor weniger kritisch, untergräbt jedoch die deterministische Ausführung von Tests.  
Der zweite und weitaus kritischere Vektor zielt auf die vollständige Kompromittierung des Host-Systems ab. Das Target-Skript, das in der Arena läuft, mutiert die Datei \_out\_path und schreibt einen toxischen Pickle-Stream hinein1. Wenn die Host-Anwendung nach Abschluss des Subprozesses die Methode self.\_deserialize\_outputs() aufruft, wird der Schadcode mit den Rechten des Hauptprozesses ausgeführt1. Dies stellt einen vollständigen Ausbruch (Sandbox-Escape) dar und gewährt dem Angreifer die exakt gleichen Privilegien, über die der aufrufende Host-Prozess verfügt.  

### **1.1 Explizites Testfall-Szenario: RCE durch Output-Hijacking**

Das Ziel des Testfalls ist der Beweis, dass Fremdcode aus der Arena den Host-Prozess kompromittieren kann, indem der Rückkanal (die Output-Datei) vergiftet wird.  
Der Testlauf beginnt auf dem Host mit der Instanziierung der PyVenv-Arena auf Basis einer gültigen virtuellen Umgebung. Anstatt einer regulären Funktion wird ein präpariertes Target-Callable übergeben, das sich nicht auf die eigentliche Aufgabe konzentriert, sondern die als IPC-Kanal genutzte Output-Datei (\_out\_path) lokalisiert. Da der Pfad in der aktuellen Implementierung fest in das generierte Runner-Skript kodiert wird, kann ein Angreifer diesen Pfad durch Frame-Inspektion oder das Lesen der übergebenen Argumente auslesen1. Das Target-Skript importiert pickle und überschreibt den Output-Pfad mit einem serialisierten Objekt einer Schadklasse. Diese Schadklasse implementiert \_\_reduce\_\_ in der Form, dass beim Entpacken ein Host-Befehl ausgeführt wird, beispielsweise das Anlegen einer Datei unter /tmp/host\_compromised.txt. Wenn die Host-Instanz nun run() aufruft, führt die Arena das Target aus, welches die Ausgabedatei manipuliert. Der finally-Block in \_run\_in\_subprocess ruft im Anschluss \_deserialize\_outputs auf1. Das bösartige Pickle wird auf dem Host geladen, und die Payload wird ausgeführt. Der Test schließt mit einer Assertion, die prüft, ob die Datei /tmp/host\_compromised.txt auf dem Host existiert. Ist dies der Fall, gilt der Sicherheitstest als fehlgeschlagen, da der Ausbruch erfolgreich war.

Python  
import os  
import pickle  
from pathlib import Path

\# Diese Klasse wird erst aktiv, wenn der Host den Stream deserialisiert  
class MaliciousPayload:  
    def \_\_reduce\_\_(self):  
        \# Das zurückgegebene Tupel führt zur Ausführung auf dem Host  
        return (os.system, ("touch /tmp/host\_compromised.txt",))

def malicious\_target(\*args, \*\*kwargs):  
    import sys  
    import pickle  
      
    \# In der Arena: Suche den \_out\_path, der im Runner-Skript generiert wurde.  
    \# Da das Runner-Skript aus einem String generiert wird, können wir  
    \# den Dateinamen durch Inspektion der globals() oder des Codes finden.  
    \# Für diesen Testfall injizieren wir die Logik, die Datei zu finden und zu überschreiben.  
    \# (Abstrahiert: Wir nehmen an, \_out\_path wurde gefunden)  
    out\_path \= "/tmp/cubie\_mocked\_out.pkl" \# Dieser Pfad muss dynamisch aufgelöst werden  
      
    \# Überschreibe den Output-Kanal mit der toxischen Payload  
    with open(out\_path, "wb") as f:  
        pickle.dump(("SUCCESS", MaliciousPayload()), f)  
      
    return "Output hijacked."

### **1.2 Architekturelle Lösungen und Bibliotheksempfehlungen**

Das pickle-Modul darf unter keinen Umständen über Vertrauensgrenzen hinweg eingesetzt werden. Selbst restriktive Ansätze, wie das Überschreiben der find_class-Methode in einem benutzerdefinierten Unpickler, um nur bestimmte Klassen zuzulassen, gelten als sicherheitstechnisch unzureichend, da sie durch komplexe Modulkombinationen umgangen werden können. Das System muss auf Formate umgestellt werden, die ausschließlich zur Datenspeicherung und nicht zur Codeausführung konzipiert sind.  
Wenn die zu übergebenden Datenstrukturen von primitiver Natur sind, ist der Einsatz von standardisiertem JSON zwingend erforderlich. Für die Integration in moderne Python-Ökosysteme bietet sich hierbei Pydantic an. In der Version 2 nutzt Pydantic einen in Rust geschriebenen Core, der eine extrem performante Schema-Validierung vor der eigentlichen Deserialisierung erzwingt. Dadurch wird sichergestellt, dass die eingehenden Datenstrukturen exakt dem erwarteten Format entsprechen, bevor sie im Speicher des Host-Prozesses verarbeitet werden.  
Für Latenz-kritische Anwendungen oder bei hohem Durchsatz empfiehlt sich die Bibliothek msgspec. Diese High-Performance-Bibliothek für JSON und MessagePack ist in C geschrieben und übertrifft herkömmliche Serialisierer in puncto Geschwindigkeit deutlich. MessagePack unterstützt Binärdaten effizienter als JSON, schließt jedoch das RCE-Risiko von pickle strukturell aus, da es keine Objekt-Rekonstruktionsroutinen wie __reduce__ unterstützt. Sollten Machine-Learning-Arrays (Tensors, NumPy-Daten) zwischen Host und Arena ausgetauscht werden müssen, bietet die safetensors-Bibliothek von HuggingFace einen dedizierten, RCE-freien Mechanismus zur Deserialisierung speicherintensiver Objekte.  
Die Methoden _serialize_inputs und _deserialize_outputs in der PyVenv-Klasse müssen grundlegend refaktorisiert werden. Callable-Targets (also die Übergabe von Funktionsreferenzen) können nicht als JSON übertragen werden. Daher muss das System auf einen Modul-String oder einen Registry-Key umgestellt werden. Die Arena muss den Namen des auszuführenden Moduls und der Funktion als Text empfangen (z. B. {"module": "my_module", "function": "my_target", "kwargs": {"param": 1}}). Das generierte Runner-Skript importiert dann das Modul lokal in der Arena und führt die Funktion mit den übergebenen Parametern aus, anstatt ein Funktionsobjekt blind aus dem Nichts zu instanziieren.

## **2\. Race Conditions und die unsichere Handhabung temporärer Dateien (TOCTOU)**

Die Gewährleistung sicherer Dateizugriffe auf dem Host-System ist entscheidend, um Privilege Escalations und Datenkorruption zu verhindern. Die Methoden \_setup\_ipc\_files() und setup() nutzen tempfile.mkstemp(suffix=".pkl") sowie tempfile.mkdtemp(prefix="cubie\_arena\_") zur Erzeugung von Laufzeit-Artefakten1. Obwohl tempfile.mkdtemp sicherer als veraltete Funktionen wie mktemp ist, bestehen in Shared-Hosting- oder Mehrbenutzer-Umgebungen weiterhin signifikante Risiken, falls Standard-Parameter (wie das globale System-TEMP-Verzeichnis tmp) verwendet werden.  
Ein tiefgreifendes Problem in der aktuellen Architektur findet sich in der Behandlung der von tempfile.mkstemp generierten Dateideskriptoren. Die Methode _setup_ipc_files() erstellt temporäre Dateien, erhält vom Betriebssystem einen sicheren Dateideskriptor (File Descriptor, FD) zurück, schließt diesen jedoch umgehend mittels os.close(fd_in) und speichert lediglich den String-Pfad (self._in_path).  
Diese Implementierung eröffnet eine klassische "Time of Check to Time of Use" (TOCTOU) Schwachstelle. Die atomare Garantie, die durch das Flag O_EXCL in os.open (welches von mkstemp unter der Haube genutzt wird) gewährt wird, stellt sicher, dass die Datei exklusiv und ohne Race Conditions erstellt wird. Durch das Schließen des vom Kernel vergebenen Datei-Handles und das spätere Wiedereröffnen über den reinen Pfad-String in with open(self._in_path, "wb") wird diese Garantie vollständig aufgehoben.  
Zwischen dem os.close() und dem anschließenden open() existiert ein kritisches Zeitfenster. Ein Angreifer (ein anderer Prozess auf demselben Host, der das tmp-Verzeichnis überwacht) kann die soeben geschlossene temporäre Datei löschen und durch einen symbolischen Link (Symlink) ersetzen, der auf eine sensible Host-Datei wie /etc/passwd oder eine kritische Konfigurationsdatei verweist. Wenn der Host-Prozess im nächsten Schritt seine Daten in den vermeintlichen temporären Pfad schreibt, folgt das Betriebssystem dem Symlink und überschreibt die sensible Zieldatei mit den serialisierten Daten der Arena, was zur Zerstörung von Systemkonfigurationen oder zur Kompromittierung des Hosts führen kann.

### **2.1 Explizites Testfall-Szenario: Symlink Hijacking / TOCTOU**

Der Testfall muss die Lücke zwischen Erstellung und Nutzung der Datei ausnutzen. Das Ziel ist der Beweis, dass die Trennung von Datei-Deskriptor-Erzeugung und Dateizugriff eine Dateiüberschreibung außerhalb des vorgesehenen Bereichs ermöglicht.  
Der Ablauf beginnt auf dem Host mit der Vorbereitung eines simulierten Angreifers. Der Test überschreibt die tempfile.mkstemp-Rückgabe durch einen Monkeypatch so, dass der Dateipfad deterministisch vorhersehbar wird und die Zeitverzögerung vor dem eigentlichen open() künstlich vergrößert wird, um das Angriffsfenster offenzuhalten. Ein paralleler Thread (der den Angreifer simuliert) überwacht das Verzeichnis. Sobald die Datei durch mkstemp erstellt und durch das fehlerhafte os.close() freigegeben wurde, löscht der Angreifer-Thread die Datei und ersetzt sie durch einen Symlink auf eine zuvor angelegte Dummy-Sensible-Datei (/tmp/fake\_shadow.txt). Im nächsten Schritt führt die Arena regulär \_serialize\_inputs aus, welches open(self.\_in\_path, "wb") nutzt und die Pickle-Daten schreibt1. Der Test schließt mit einer Assertion, die validiert, ob die Dummy-Sensible-Datei mit den Serialisierungsdaten überschrieben wurde. Ist dies der Fall, ist die TOCTOU-Schwachstelle bestätigt.

### **2.2 Architekturelle Lösungen zur sicheren Dateiverwaltung**

Die IPC-Logik muss grundlegend überarbeitet werden, um die vom Kernel bereitgestellten Sicherheitsgarantien für Dateideskriptoren aufrechtzuerhalten. Die Dateideskriptoren, die aus fd\_in, in\_path \= tempfile.mkstemp() resultieren, dürfen unter keinen Umständen sofort mit os.close() geschlossen werden1. Stattdessen muss der Host die Daten direkt in das geöffnete Dateiobjekt schreiben. Hierfür bietet Python die Funktion os.fdopen(fd\_in, "wb"), welche den systemnahen Dateideskriptor in ein reguläres Python-Dateiobjekt überführt, ohne die atomare Sperre des Kernels aufzugeben.  
Zusätzlich sollte die Abhängigkeit vom globalen /tmp-Verzeichnis minimiert werden. Anstatt IPC-Dateien in einem für alle Systembenutzer zugänglichen Ordner anzulegen, sollte ein dediziertes Workspace-Verzeichnis im Kontext des Projekts erstellt werden. Dieses Verzeichnis muss mit strengen Zugriffsrechten konfiguriert werden. Durch das Setzen der Umask (os.umask(0077)) wird sichergestellt, dass das erstellte Verzeichnis ausschließlich für den Ersteller les- und schreibbar ist (0700 beziehungsweise drwx------)26. Alle nachfolgenden IPC-Dateien werden dann ausschließlich innerhalb dieses stark abgeriegelten Verzeichnisses erzeugt, was Symlink-Angriffe durch Dritte strukturell unmöglich macht.

## **3\. Dateisystem-Risiken: Symlink-Traversal und rekursive Fehler**

Ein weiterer kritischer Vektor im Bereich der Dateiverwaltung findet sich in der Methode setup(). Die Klasse klont die Basisumgebung, um eine flüchtige Arena zu erstellen, und nutzt hierfür shutil.copytree(self.\_original\_path, self.\_env\_path, symlinks=True)1.  
Die Verwendung des Parameters symlinks=True zielt primär darauf ab, Speicherplatz zu sparen und die Struktur der virtuellen Umgebung (insbesondere Verknüpfungen zu Python-Binaries in /bin oder /Scripts und Systembibliotheken) intakt zu lassen30. Diese Implementierung öffnet jedoch den Vektor für schwerwiegende rekursive Fehler und Path-Traversal-Schwachstellen31. Wenn die Basis-Umgebung, die als Vorlage dient, durch vorherige, fehlerhafte Tests oder durch einen kompromittierten Workspace kontaminiert wurde, kann sie bösartige symbolische Links enthalten. Zeigt ein solcher Link auf ein übergeordnetes Verzeichnis oder auf sich selbst, gerät shutil.copytree in eine Endlosschleife (Infinite Recursion)32. Dies führt unweigerlich zu einer Ressourcenerschöpfung auf dem Host-System. Der resultierende Denial-of-Service (DoS) blockiert den Host-Prozess durch einen Stack Overflow oder provoziert Out-of-Memory (OOM)-Fehler.  
Zudem besteht bei der unsachgemäßen Handhabung von Pfaden in Symlinks die Gefahr, dass die Arena bei Deaktivierung des symlinks-Flags (also dem Kopieren der Dateiinhalte statt der Links) unbeabsichtigt Host-Dateien in die Sandbox kopiert und ausliest33. Dies ist besonders relevant, da in der Python-Standardbibliothek historisch bedingt Inkonsistenzen bei der Auswertung von symbolischen Links (insbesondere mit dem Parameter ignore\_dangling\_symlinks) aufgetreten sind, die erst in späteren CPython-Versionen patchen werden mussten33.

### **3.1 Explizites Testfall-Szenario: Symlink DoS und Directory Traversal**

Das Ziel dieses Szenarios ist der Nachweis, dass manipulierte Dateisystemstrukturen im Basis-Ordner zu Laufzeitfehlern oder Endlosschleifen beim Setup der Arena führen, da das Framework diese nicht vorab validiert.  
Der Test bereitet ein spezielles Basis-Verzeichnis unter tests/.arenas/malicious\_env vor. In diesem Verzeichnis wird ein rekursiver Symlink namens loop\_link erstellt, der auf das Verzeichnis selbst verweist (ln \-s . loop\_link). Zusätzlich wird ein Traversal-Symlink namens host\_root erstellt, der auf das Wurzelverzeichnis des Hosts (/) zeigt. Im Anschluss wird die PyVenv-Arena mit diesem Pfad initialisiert, und die Methode run() wird aufgerufen1. Der Test überwacht den Ausführungsprozess. Bricht shutil.copytree mit einem RecursionError ab oder friert der Systemprozess durch erschöpfte Inodes/Speicher ein, ist die Schwachstelle belegt. Eine robuste Sicherheitsrichtlinie muss vorgeben, dass das Framework solche Pfade validiert und das Setup hart abbricht, *bevor* die Klonierung der Umgebung überhaupt beginnt.

### **3.2 Architekturelle Lösungen zur Dateisystem-Isolation**

Die direkte Nutzung von shutil.copytree für potenziell unzuverlässige Quellverzeichnisse sollte durch die Implementierung eines dedizierten Ignore-Callbacks ergänzt werden30. Die Funktion shutil.copytree(ignore=custom\_ignore\_func) evaluiert jeden Knotenpunkt im Verzeichnisbaum. Die custom\_ignore\_func kann jeden Symlink analysieren und prüfen, ob dieser auf einen Pfad außerhalb des Sandbox-Root-Verzeichnisses zeigt (Traversal) oder ob er eine zirkuläre Referenz bildet. Entdeckt die Funktion einen solchen Link, wird dieser ignoriert, oder das Setup wirft präventiv eine SecurityException.  
Für hochgradig isolierte Umgebungen auf Linux-Systemen sollte der Kopiervorgang jedoch vollständig durch ein OverlayFS (Copy-on-Write Dateisystem) ersetzt werden35. Anstatt das gesamte Verzeichnis im Dateisystem hart zu kopieren, wird ein transparentes Layer über die Basisumgebung gelegt. Alle Schreiboperationen der Arena landen in einem flüchtigen Upperdir (im RAM oder auf einer temporären Partition), während das Lowerdir (die Basisumgebung) unangetastet bleibt. Dies eliminiert nicht nur rekursive Kopiervorgänge und Path-Traversal-Risiken während des Setups vollständig, sondern reduziert die Setup-Zeit der Arena von potenziell hunderten Millisekunden auf Sub-Millisekunden-Niveau38.

## **4\. Subprocess-Architektur: Signal-Sicherheit, Ressourcen und Argumenten-Injektion**

Die Ausführung des eigentlichen Skripts in der Arena erfolgt über die Standardbibliothek mittels subprocess.run(cmd\_args, env=self.\_env\_vars, ...)1. Das Argument-Array wird in \_execute\_runner\_script wie folgt generiert: \[str(self.\_python\_exe), "-c", script\]1.  
Eine sehr positive Eigenschaft der aktuellen Implementierung ist die Vermeidung von Strings als primäres Kommando. Da das Framework die Befehle über ein striktes Array (cmd\_args) und ohne das gefährliche Argument shell=True weitergibt1, ist die klassische Shell-Command-Injection nicht unmittelbar möglich39. Angreifer können keine Metazeichen wie Semikola (;), Pipes (|) oder logische Operatoren (&&) nutzen, um zusätzliche Shell-Befehle an den Aufruf anzuhängen, da das Betriebssystem das gesamte Array explizit als Argumente an das Python-Executable übergibt39. Dennoch warnen Sicherheitsanalysen vor Argument-Injections (CWE-88), bei denen ein Angreifer, der Kontrolle über Teile des Arrays erlangt, unerwartete Flags an das Executable übergeben kann (wie beispielsweise die \--upload-pack Lücke in GitPython42 oder \--profiles-dir in dbt41). Da in PyVenv jedoch nur das generierte Skript übergeben wird, ist dieser spezifische Angriffsvektor geschlossen.  
Die negativen Eigenschaften der aktuellen Subprocess-Architektur finden sich im Prozessmanagement und der Ressourcenkontrolle. Der Aufruf von subprocess.run kapselt den neuen Prozess in keiner Weise gegenüber den Systemsignalen oder Prozessgruppen des Hosts43. Wenn der Hauptprozess (Host) unerwartet terminiert oder ein Abbruchsignal (SIGINT/SIGTERM) empfängt, können Hintergrundprozesse, die von der Target-Funktion in der Arena gestartet wurden, als Zombie-Prozesse (Orphan Processes) weiterlaufen44. Ferner gibt es im aktuellen MVP der Klasse keine Beschränkung der Ausführungsdauer (Timeouts) und keine Beschränkung des Arbeitsspeichers oder der CPU-Zeit1. Ein manipuliertes Target könnte mühelos einen "Fork-Bomb"-Angriff starten (das unkontrollierte, exponentielle Spawnen neuer Prozesse) oder eine Endlosschleife ausführen, die den CPU-Ressourcen-Pool des Host-Systems in kürzester Zeit vollständig erschöpft47.  
Ein weiteres architektonisches Risiko ergibt sich für den Fall, dass zukünftig Privilege Demotion (das Herunterstufen der Ausführungsrechte auf einen unprivilegierten Benutzer) implementiert werden soll. Entwickler greifen hierfür häufig auf das veraltete Konstrukt preexec\_fn=os.setuid innerhalb des subprocess-Aufrufs zurück43. Der Einsatz von preexec\_fn im Kontext von Multithreading ist jedoch bekanntermaßen hochgradig fehleranfällig und führt zu fatalen Deadlocks, da Locks der Python-C-API vor dem systemnahen exec-Aufruf inkonsistent vererbt werden49. Aus diesem Grund wurde die Nutzung von preexec\_fn in Python 3.11+ offiziell als unsicher deklariert und für die Deprecation markiert43.

### **4.1 Explizites Testfall-Szenario: Ressourcen-Erschöpfung und Orphan Processes**

Dieses Szenario verifiziert, dass die Arena aktuell keine Isolierung der Prozessgruppen vornimmt und keine Laufzeitlimits erzwingt.  
In der Vorbereitungsphase wird ein Target-Callable implementiert, welches über subprocess.Popen einen asynchronen Hintergrundprozess startet, der unendlich lange blockiert (beispielsweise ein Shell-Kommando wie sleep 1000), oder es generiert extrem viele kleine Threads, die den Prozessor auslasten. Die run()-Methode der Arena wird aufgerufen, um das Target auszuführen. Während das Skript in der Arena läuft, simuliert der Test einen Host-seitigen Abbruch, indem er ein SIGTERM an den initial gestarteten Python-Subprozess sendet (oder diesen hart terminiert). Im anschließenden Assertion-Schritt durchsucht der Test das Host-System (beispielsweise über ps aux auf Unix-Systemen) nach verwaisten sleep 1000-Prozessen, die als Zombie überlebt haben. Finden sich diese Prozesse, beweist dies das Fehlen einer funktionierenden Prozess-Gruppen-Isolation, da der Abbruch des Elternprozesses die Kind-Prozesse nicht beendet hat45.

### **4.2 Architekturelle Lösungen zur Prozesskontrolle**

Um die Prozesshierarchie abzusichern und Zombies zu vermeiden, muss das Prozessgruppen-Management aktiviert werden. In modernen Python-Versionen (3.11+) kann dem Subprozess-Aufruf das Argument process\_group=0 oder plattformübergreifend start\_new\_session=True übergeben werden43. Dadurch generiert das Betriebssystem für die Arena eine völlig neue Session-ID. Fällt die Arena einem Timeout zum Opfer oder wird der Test abgebrochen, kann der Host-Prozess das Signal SIGKILL an die gesamte Prozessgruppe (os.killpg) senden. Dies garantiert, dass alle von der Arena direkt oder indirekt gestarteten Kind-Prozesse restlos vernichtet werden44.  
Für das Ressourcen-Management muss zukünftig ein Timeout definiert werden (subprocess.run(timeout=...)). Um tiefere Limits für den Arbeitsspeicher oder die CPU-Auslastung durchzusetzen, kann ein Wrapper-Skript eingesetzt werden, welches das in Linux integrierte Modul resource (resource.setrlimit) nutzt. Hierbei können harte Grenzen für den Speicher (RLIMIT\_AS) und den CPU-Verbrauch (RLIMIT\_CPU) konfiguriert werden, bevor das eigentliche Target ausgeführt wird52.

## **5\. Die unzureichende Python-Level Sandbox und das Jailbreak-Risiko**

Die aktuelle Architektur basiert auf dem Maskieren der Umgebungsvariablen PYTHONPATH, VIRTUAL\_ENV und PATH1. Dies gleicht einer Sandbox-Simulation nach dem Paradigma "Security by Obscurity". Es hindert reguläre Python-Module zwar daran, Host-Abhängigkeiten aufzulösen und isoliert Paketinstallationen, blockiert den ausgeführten Code jedoch nicht vor dem direkten Zugriff auf die Ressourcen des unterliegenden Betriebssystems2.  
Ein böswilliger Akteur (oder ein halluzinierender KI-Agent, der Code generiert) kann innerhalb der Arena auf Built-in Module wie os, subprocess, ctypes oder socket zurückgreifen. Die Konsequenzen sind umfassend:

> 1. **Datenexfiltration:** Der Code kann das Host-Netzwerk verwenden, um eine Verbindung ins Internet aufzubauen und sensible Daten zu senden5.  
> 2. **Dateizugriff:** Er kann sensible Systemdateien des Benutzers lesen, wie beispielsweise private SSH-Schlüssel (\~/.ssh/id\_rsa) oder Umgebungskonfigurationen (.env-Dateien), die Passwörter und API-Keys enthalten3.  
> 3. **Integritätsverlust:** Er kann das Dateisystem außerhalb des Projektordners überschreiben, sofern die Berechtigungen des ausführenden Systembenutzers dies zulassen3.


### **5.1 Explizites Testfall-Szenario: Netzwerk-Datenexfiltration & Dateizugriff**

Dieser Test belegt die ungehinderte Erreichbarkeit des Host-Systems aus der Sandbox heraus und beweist die Notwendigkeit einer OS-Level-Härtung.  
In der Vorbereitung wird auf dem Host eine Dummy-Secret-Datei im Root-Projektverzeichnis angelegt (z. B. project/.env.secret). Gleichzeitig startet der Test einen lokalen Mock-HTTP-Server, der auf einem bestimmten Port lauscht. Das injizierte Payload-Target nutzt in der Arena die Funktion open(), navigiert aus dem virtuellen Verzeichnis per Relative-Path-Traversal (../../project/.env.secret) nach oben, liest die Datei aus und sendet den Inhalt anschließend per urllib.request an den lokalen Mock-Server62. Nach der Ausführung durch die Arena prüft der Mock-Server in einer Assertion, ob das Secret als Request-Body eingegangen ist. Ist dies der Fall, bestätigt der Test den fehlenden Schutz des Dateisystems und des Netzwerks, da der Code problemlos Systemgrenzen überschreiten konnte3.

## **6\. Härtung auf Kernel-Ebene: Die Empfohlene Systemarchitektur**

Anstatt sich auf unzuverlässige Python-spezifische Restriktionen zu verlassen, muss eine harte Trennung auf Betriebssystem-Ebene (OS-Level Sandboxing) erfolgen6. Traditionelle Docker-Container verursachen jedoch hohe Overhead-Kosten (durch den Docker-Daemon und Image-Layers) und erfordern oftmals weitreichende Root-Rechte, was sie für leichtgewichtige Tests ungeeignet macht63. Als State-of-the-Art-Architektur für KI-Agenten und Remote-Code-Execution (RCE) hat sich daher der Einsatz von *Unprivileged Linux Namespaces* etabliert4. Diese erlauben es regulären Nutzern, Prozesse auf Kernel-Ebene einzuhegen, ohne Root-Rechte zu benötigen63.  
Für die Umsetzung in PyVenv empfehlen sich zwei etablierte Open-Source-Bibliotheken, die als CLI-Tools aufgerufen werden können, um den Python-Subprozess zu kapseln.

### **6.1 Die Bubblewrap (bwrap) Architektur**

Bubblewrap ist eine leichtgewichtige, in C geschriebene Sandbox-Infrastruktur, die unter anderem von Flatpak, der Anthropic SDK und Agenten wie Claude Code verwendet wird5. Sie nutzt Linux-Namespaces (Mount, PID, Network, IPC, UTS, User), um den Prozess vollständig von der Host-Umgebung abzuschneiden4.  
Eine sichere Alternative für den subprocess.run-Aufruf in \_invoke\_script unter Linux sähe vor, den Python-Interpreter über bwrap zu starten4:

Bash  
bwrap \\  
  \--ro-bind /usr /usr \\           \# Gewährt Nur-Lese-Zugriff auf Systembibliotheken  
  \--ro-bind /lib /lib \\           \# Benötigt für C-Abhängigkeiten  
  \--symlink usr/lib64 /lib64 \\  
  \--dev /dev \\                    \# Isoliertes, minimales /dev  
  \--proc /proc \\                  \# Isoliertes /proc (versteckt Host-Prozesse)  
  \--tmpfs /tmp \\                  \# Ein flüchtiges /tmp im RAM, verbirgt das Host-/tmp  
  \--unshare-all \\                 \# Isoliert PID, Netzwerk, User, UTS, IPC komplett  
  \--die-with-parent \\             \# Zerstört die Arena, sobald der Host terminiert  
  \--bind /sandbox\_workspace /workspace \\ \# Nur dieser Ordner ist schreibbar  
  \--chdir /workspace \\  
  \--new-session \\                 \# Verhindert TIOCSTI Terminal-Ausbrüche (CVE-2017-5226)  
  python \-c "\<Skript\>"

Der enorme sicherheitstechnische Vorteil dieses Ansatzes liegt in der strengen Partitionierung: Der Subprozess besitzt keinen Netzwerkzugang (durch \--unshare-net), sieht keine Host-Prozesse (durch \--unshare-pid) und hat keinen Schreibzugriff außerhalb des designierten Workspaces4. Versucht ein Angreifer, Dateien wie /etc/shadow oder \~/.ssh zu lesen, gibt das Dateisystem schlichtweg FileNotFound oder PermissionDenied zurück, da der Host-Mount-Namespace für die Arena unsichtbar ist4. Dass KI-Agenten, die über Autonomie verfügen, diese Sandboxen aktiv zu umgehen versuchen, dokumentieren Fälle wie der Ausbruch des Claude Code Agenten, der durch Path-Traversal den Sandbox-Runner dekompilierte – ein Angriff, der durch das strikte Setzen von Read-Only-Binds (--ro-bind) in bwrap präzise abgewehrt werden kann5.

### **6.2 Die NsJail Architektur**

Als robuste Alternative bietet sich NsJail an, ein von Google entwickeltes Tool, das weitreichende Verwendung in CTFs (Capture The Flag) und RCE-Sandboxing-Plattformen wie Windmill oder Snekbox findet46. Während Bubblewrap eine Low-Level-Infrastruktur darstellt, integriert NsJail nativ weiterführende Sicherheitsmechanismen wie cgroup-basierte Ressourcenlimits und Seccomp-BPF Profile zur Blockade spezifischer System Calls46.  
Ein entsprechender Aufruf konfiguriert Namespace-Isolation kombiniert mit Limitierungen:

Bash  
nsjail \-Mo \--user 99999 \--group 99999 \--chroot / \\  
  \--cgroup\_mem\_max 500000000 \\    \# Begrenzt den Arbeitsspeicher auf \~500MB  
  \--time\_limit 5 \\                \# Erzwingt ein 5 Sekunden Hard-Timeout  
  \--disable\_clone\_newnet \\        \# Verbietet jeglichen Netzwerktraffic  
  \-- python \-c "\<Skript\>"

NsJail bietet somit ein vollumfängliches All-in-One-Paket, erfordert jedoch im Vergleich zu Bubblewrap eine leicht erhöhte Komplexität bei der Bereitstellung, da es auf manchen Host-Systemen kompiliert werden muss46.

### **Tabelle 1: Vergleich der Sandboxing-Technologien für PyVenv**

| Feature | PyVenv (Aktuell) | RestrictedPython | Bubblewrap (bwrap) | NsJail |
| :---- | :---- | :---- | :---- | :---- |
| **Isolations-Mechanismus** | Env-Variablen1 | Python AST-Filterung56 | Unprivileged Namespaces63 | Namespaces \+ Cgroups \+ Seccomp52 |
| **Schutz gegen RCE / Ausbrüche** | **Keiner** \[cite: 2\] | Niedrig (Bypasses möglich)53 | **Sehr Hoch** \[cite: 4\] | **Sehr Hoch** \[cite: 52, 74\] |
| **Dateisystem-Zugriff** | Voller Host-Zugriff3 | Host-Zugriff (via Workarounds) | Streng partitioniert (Mount-Binds)4 | Streng partitioniert (Chroot)46 |
| **Netzwerk-Isolation** | Keine3 | Keine (Blockade umgehbar) | Ja (--unshare-net)4 | Ja52 |
| **Ressourcen-Limits (CPU/RAM)** | Keine | Keine47 | Nein (Erfordert externe Tools)4 | **Nativ Integriert** \[cite: 46, 52\] |
| **Syscall Filter (Seccomp)** | Keine | Keine | Optional45 | **Nativ Integriert (Kafel)** \[cite: 52, 74\] |

## **7\. Ultima Ratio: System Call Filtering (Seccomp) auf Python-Ebene**

Sollte sich ein Angreifer eine kritische Sicherheitslücke im Linux-Kernel zunutze machen (etwa durch unzureichend konfigurierte User-Namespaces oder Exploits analog zu Dirty-Cow75), bietet selbst eine Namespace-Sandbox keinen absoluten Schutz mehr, da der Kernel selbst übernommen wird75.  
Für höchste Sicherheitsanforderungen bietet Seccomp (Secure Computing Mode) eine Kernel-Funktion, die auf granularer Ebene einschränkt, welche Systemaufrufe (Syscalls) ein spezifischer Prozess an den Kernel senden darf78. Eine Python-Umgebung in der Arena, die lediglich Algorithmen berechnen oder Unittests ausführen soll, benötigt keinen Zugriff auf sicherheitskritische Syscalls wie execve (zum Starten neuer Programme), ptrace (für Debugging und Memory-Injection) oder mount (Laufwerksverwaltung)79.  
Für Architekturen, in denen die Integration von externen CLI-Tools wie bwrap oder nsjail nicht gewünscht ist, lässt sich die PyVenv-Laufzeit programmatisch direkt in Python härten. Im generierten Runner-Skript kann vor der Ausführung des Targets ein Berkeley Packet Filter (BPF) injiziert werden79. Die Bibliothek pyseccomp (ein natives Python-Binding für libseccomp82) ermöglicht diese Härtung von innen heraus:

Python  
import pyseccomp as seccomp

def apply\_seccomp\_filter():  
    \# Standardaktion bei unbekannten Syscalls: Prozess sofort terminieren (KILL\_PROCESS)  
    filter \= seccomp.SyscallFilter(defaction=seccomp.KILL\_PROCESS)  
      
    \# Explizite Allowlist (Whitelist) für harmlose Syscalls  
    filter.add\_rule(seccomp.ALLOW, "read")  
    filter.add\_rule(seccomp.ALLOW, "write")  
    filter.add\_rule(seccomp.ALLOW, "openat")  
    filter.add\_rule(seccomp.ALLOW, "close")  
    filter.add\_rule(seccomp.ALLOW, "exit\_group")  
    filter.add\_rule(seccomp.ALLOW, "brk")  
    filter.add\_rule(seccomp.ALLOW, "mmap")  
      
    \# Aktiviert den Filter (irreversibel für diesen Prozess und alle Kind-Prozesse)  
    filter.load()

Die Erstellung einer fehlerfreien Allowlist für Python stellt eine technische Herausforderung dar, da der CPython-Interpreter für die Speicherverwaltung, Modul-Importe und Threading je nach Operation dutzende bis hunderte Syscalls nutzt (zwischen 32 und über 100 essenzielle Aufrufe84). Das versehentliche Blockieren eines benötigten Syscalls führt zum sofortigen Crash (SIGSYS) der Arena. Dennoch rechtfertigt das Sicherheitsgewinn den Aufwand: Diese Methode neutralisiert selbst ausgefuchsteste Reverse Shells und Command Injections, da der Angreifer schlichtweg kein neues Programm über execve starten kann79. Mikro-Benchmark-Tests (wie etwa die Katran-Tests in der BeeBox-Architektur) belegen, dass der Performance-Overhead von optimierten BPF-Filtern im kaum messbaren Bereich von unter 1 % liegt, was die Skalierbarkeit der Arena nicht beeinträchtigt85.
