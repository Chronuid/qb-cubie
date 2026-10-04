# [Feature] Implementierung von `DockerArena` und `VmArena` für erweiterte OS- und FS-Isolation (Entwicklung bis auf Weiteres Eingefroren)


## Kontext & Motivation
Für die Entwicklung robuster Datei- und Pfad-Operationen (insbesondere für das komplexe Home-Routing und Eject-Muster der `devops`-Architektur) reicht die Ausführung in der Standard-Host-Umgebung nicht mehr aus. Da Pfadauflösungen, Symlinks und Berechtigungskonzepte zwischen verschiedenen Betriebssystemen stark abweichen, benötigt das Test-Framework dedizierte Arenen, die diese spezifischen Umgebungen simulieren und kapseln. 

Um die Integrität der isolierten Ausführungs-Arenen in `cubie` zu wahren und OS-übergreifendes Testen zu ermöglichen, müssen zwei neue Arena-Typen implementiert werden.

## 1. `DockerArena` (FS-Isolation)
Diese Arena adressiert den Bedarf nach strikter Dateisystem-Isolation auf Container-Ebene.

**Anforderungen:**
* **Zweck:** Bereitstellung einer isolierten Ausführungsumgebung (ein häufiger "synthetischer" Community-Wunsch für sauberes Sandboxing).
* **Verhalten:** Die Arena muss einen flüchtigen Container hochfahren, in dem File-I/O-Operationen (wie das Kopieren von `.devops`-Strukturen) ausgeführt werden können, ohne das Host-Dateisystem zu kontaminieren.
* **Konfiguration:** Es muss möglich sein, das Basis-Image und die Volume-Mounts direkt aus der Test-Deklaration heraus zu definieren.

## 2. `VmArena` (OS-Szenarien & Routing)
Diese Arena dient der Bereitstellung vollwertiger oder leichtgewichtiger Betriebssystem-Umgebungen zur Validierung von Routing- und Berechtigungs-Logiken.

**Anforderungen:**
* **Zweck:** Simulation diverser Betriebssysteme (Linux-Derivate, Windows etc.) zum Testen spezifischer Pfad-Auflösungen (z.B. absolute vs. relative Pfade, Backslash vs. Forward-Slash, User-Home-Verzeichnisse).
* **Verhalten:** Die Testsuite muss das gewünschte Ziel-Betriebssystem deklarativ anfordern können. Die Arena kümmert sich um die Provisionierung (ob im Backend tatsächliche VMs, Micro-VMs oder speziell konfigurierte System-Container genutzt werden, ist der Arena-Schnittstelle zunächst abstrahiert).
* **Ausführung:** Code und Tests (insbesondere Example-Based Testing) müssen nahtlos in diese Gast-Umgebung injiziert, dort ausgeführt und die Resultate (inklusive FS-Zustand) in die Host-Instanz von `cubie` zurückgemeldet werden.

## Akzeptanzkriterien (Acceptance Criteria)
- [ ] `DockerArena`-Klasse ist implementiert und erbt von der Basis-Arena-Schnittstelle. .
- [ ] `VmArena`-Klasse ist entworfen und bietet eine deklarative Schnittstelle zur Auswahl des Ziel-OS.
- [ ] Funktionalitäts-Nachweise für die `DockerArena` und die `VmArena`: Der Natur der Arenen entsprechend umfassende Test-Suites.
- [ ] Dokumentation der neuen Arenen und deren Konfiguration (z. B. Anforderungen an den Host, wie installierter Docker-Daemon oder VM-Hypervisor).