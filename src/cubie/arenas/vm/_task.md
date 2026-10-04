 ## `VmArena` (OS-Szenarien & Routing)

Diese Arena dient der Bereitstellung von Betriebssystem-Umgebungen zur Validierung von Routing- und Berechtigungs-Logiken.

**Anforderungen:**
* **Zweck:** Simulation diverser Betriebssysteme (Linux-Derivate, Windows etc.) zum Testen spezifischer Pfad-Auflösungen (z.B. absolute vs. relative Pfade, Backslash vs. Forward-Slash, User-Home-Verzeichnisse).
* **Verhalten:** Die Testsuite muss das gewünschte Ziel-Betriebssystem deklarativ anfordern können. Die Arena kümmert sich um die Provisionierung.
* **Ausführung:** Code und Tests (insbesondere Example-Based Testing) müssen nahtlos in diese Gast-Umgebung injiziert, dort ausgeführt und die Resultate (inklusive FS-Zustand) in die Host-Instanz von `cubie` zurückgemeldet werden.


---


## 1. Das Arena-Protokoll und die PyVenv-Fähigkeiten

Die VmArena muss nahtlos in die Cubie-Architektur integriert werden und das strikte protocols.Arena-Interface abbilden. Sie erbt dabei die fundamentalen Fähigkeiten der PyVenv-Arena auf einer neuen physikalischen Schicht.


```python

@runtime_checkable
class Arena(Protocol):
    """
    Contract for isolated execution environments.
    """
    def workspace_path(self) -> Optional[Path]:
        """Returns the absolute path to the isolated working directory after setup."""
        ...
    
    def setup(self, state: WorldState) -> None:
        """Creates the temporary workspace and hydrates it based on the provided WorldState."""
        ...
    
    def execute(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Executes the target within the isolated workspace and returns the raw functional result."""
        ...
    
    def get_state(self) -> WorldState:
        """Packages and returns the mutated environment reality as a complete WorldState."""
        ...
    
    def teardown(self) -> None:
        """Destroys the workspace and cleans up all temporary environment states."""
        ...

```

* State-Guard Pattern: Sofortiger, harter Abbruch der Pipeline, wenn deklarierte Ressourcen (wie das Basis-Image) auf dem Host physisch fehlen.
* Topologische FS-Hydration und Abfrage: Projizierung der in WorldState.fs deklarierten Host-Dateien in den virtuellen Workspace und lässt sich abfragen.
* Topologische Venv-Hydration: Projizierung der im VmArena-Interface deklarierten env_path environments aus dem Host-Verzeichnis in den virtuellen Workspace und lässt sich abfragen.
* Zustandslose IPC: Serialisierung von target, args und kwargs in die isolierte Umgebung und Abfangen der funktionalen Resultate.


## 2. Validierungsmechanismen der Test-Suite

Die ausgearbeiteten EBT-Szenarien erzwingen eine kompromisslose Kapselung und Systemintegrität auf mehreren Ebenen:

* Self-Healing UX: Fehlt der Hypervisor auf dem Host, fängt die Arena den Fehler im setup() ab und startet einen interaktiven CLI-Wizard zur Fehlerbehebung oder Installation.
* Gast-Authentizität: Die Arena erzwingt standartmäßig die Ausführung im User-Space (nicht als root), um OS-spezifische Pfad-Trennungen und POSIX-Berechtigungskonzepte (wie Read-Only-Flags) unbestechlich zu validieren.
* Hardware- & Ressourcen-Kontrolle: Deklarative RAM- und CPU-Limits (DeviceResources) werden physisch durchgesetzt.
* Air-Gapping: Ohne explizite Aktivierung (network=False) blockiert die Arena den gesamten Egress-Traffic auf Hypervisor-Ebene.
* Ephemeralität: Copy-on-Write (CoW) Isolation garantiert, dass Modifikationen des Dateisystems restlos zerstört werden und weder sequentielle noch parallele Testläufe kontaminieren. Das Basis-Image bleibt zwingend immun (Read-Only).
* Nebenläufigkeit & Queueing: Die Engine drosselt die asynchrone Allokation hunderter VMs über eine Warteschlange, um OOM-Crashes auf dem Host zu verhindern. Die Kommunikation erfolgt über kollisionsfreie Ephemeral Ports oder Unix-Sockets.
* Ausbruchs-Prävention: Path-Traversal-Versuche und bösartige Symlinks auf Host-Systemdateien werden an der logischen Grenze strikt blockiert.
* Verlustfreie Fehler-Rekonstruktion: Crasht das Target, wird der Python-Traceback (inklusive Call-Stack) über die Hypervisor-Grenze hinweg für das Host-Debugging rekonstruiert.


## 3. Die Libvirt (QEMU/KVM)-Entscheidung

Die Wahl von Libvirt und QEMU/KVM ist eine fundamentale Architekturentscheidung für Automatisierung, Performance und Stabilität:

* Kernel-Performance: KVM verlagert die Virtualisierung direkt in den Linux-Kernel. Die VMs laufen als native Prozesse auf der CPU.
* Programmatische Orchestrierung: Libvirt bietet robuste, C-basierte Python-Bindings, die explizit für asynchrone Cloud- und CI-Workloads konzipiert wurden, anstatt fehleranfällige CLI-Wrapper aufzurufen.
* Ephemere CoW-Snapshots: Durch qemu-img und QCOW2-Backing-Files lassen sich in Millisekunden flüchtige Overlays über das Original-Image legen. Jeder EBT-Run operiert in einem exklusiven, winzigen Delta-State, der nach dem Teardown sofort verworfen wird.
* Netzwerklose IPC (VirtIO-Serial): QEMU ermöglicht dedizierte, serielle Hardware-Kanäle zwischen Host und Gast.
* Direkte Cgroup-Integration: Libvirt kontrolliert die Linux-Cgroups der emulierten Domains direkt, wodurch die in EBT geforderten Hard-Limits für RAM und CPU deterministisch und ohne Container-Lügen greifen. 