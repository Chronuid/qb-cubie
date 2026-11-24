<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# VmArena: Anforderungen an Betriebssystem-Szenarien und Routing

![Cubie](../../.assets/cubie-logo-written.png)

Dieser Entwurf beschreibt Anforderungen an Betriebssystem-Szenarien und Routing in einer geplanten VmArena.

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
>
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ...heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../../README.md) • [QA-Handbuch](../../GUIDE_Quality-Assurance.md) • [DocEnsurance](../../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

> **Feature-Entwurf – nicht implementiert, Entwicklung eingefroren.**
> Die folgenden Beschreibungen sind Zielvorstellungen und keine zugesicherten Funktionen von Cubie.

Diese Arena dient der Bereitstellung von Betriebssystem-Umgebungen zur Validierung von Routing- und Berechtigungs-Logiken.

**Anforderungen:**
* **Zweck:** Simulation diverser Betriebssysteme (Linux-Derivate, Windows etc.) zum Testen spezifischer Pfad-Auflösungen (z.B. absolute vs. relative Pfade, Backslash vs. Forward-Slash, User-Home-Verzeichnisse).
* **Verhalten:** Die Testsuite muss das gewünschte Ziel-Betriebssystem deklarativ anfordern können. Die Arena kümmert sich um die Provisionierung.
* **Ausführung:** Code und Tests (insbesondere Example-Based Testing) müssen nahtlos in diese Gast-Umgebung injiziert, dort ausgeführt und die Resultate (inklusive FS-Zustand) in die Host-Instanz von `cubie` zurückgemeldet werden.


---


## 1. Das Arena-Protokoll und die PyVenv-Fähigkeiten

Die VmArena muss nahtlos in die Cubie-Architektur integriert werden und das strikte protocols.Arena-Interface abbilden. Sie erbt dabei die fundamentalen Fähigkeiten der PyVenv-Arena auf einer neuen physikalischen Schicht.


```python
from pathlib import Path
from typing import Any, Optional, Protocol, runtime_checkable
from qb_cubie import WorldState

@runtime_checkable
class Arena(Protocol):
    """Contract for isolated execution environments."""
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

methods = ("workspace_path", "setup", "execute", "get_state", "teardown")
found = [m for m in methods if hasattr(Arena, m)]
print(f"Arena-Protokoll ({len(found)} Methoden): {', '.join(found)}")
```

<details>
<summary>Ergebnis</summary>

```text
Arena-Protokoll (5 Methoden): workspace_path, setup, execute, get_state, teardown
```
</details>

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
* Direkte Cgroup-Integration: Libvirt kontrolliert die Linux-Cgroups der emulierten Domains direkt, wodurch die in EBT geforderten Hard-Limits für RAM und CPU deterministisch und ohne Container-Lügen greifen

---

## Entwicklungs-Phasen

### **Phase 1: Wizard-Kernprozess (Top-Down in `wizards.py`)**
* Definition der Nutzungsmuster und Abläufe.
* Verankern der Nutzungsmuster und Abläufe als Test-Suites.
* Ausarbeitung der sequenziellen Zustandsübergänge.


### **Phase 2: Fassaden-Implementierung**
* Entwicklung der mutablen Interfaces zur kontextabhängigen Steuerung (Headless-Mode für Pipelines vs. interaktive UI).
* Python-SDK-Interface (Optimierte Schnittstellen zum Wirzard-Kernprozess)
* CLI-Interface (Weiterentwickelbar zur TUI)
* GUI-Interface (Pyside6)

### **Phase 3: Basis-Integration (`vmarena.py` Setup)**
* Implementierung der `setup()`-Methode inklusive des State-Guard-Patterns zur Validierung der Host-Ressourcen.
* Einbindung der Wizards als Self-Healing-Mechanismus, um bei fehlenden Abhängigkeiten wie dem Hypervisor direkt einzugreifen.

### **Phase 4: Libvirt-Kapselung (`libvirt_handles.py`)**
* Auslagerung der C-nahen API-Aufrufe und der verbosen XML-Deklarationen für Domains und Speichermedien.
* Bereitstellung von Funktionen zur spezifischen Auswertung der Libvirt-Fehlercodes (`get_error_code()`).

### **Phase 5: Ausführungslogik & Isolation (`vmarena.py`)**
* Definition der Nutzungsmuster und Variationen.
* Verankern der Nutzungsmuster und Variationen als Test-Suites.
* Entwicklung zur Erfüllung der Test-Suites.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../../GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../../services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../../README.md)  
[↦ | Core-Dokumentation | ↤](../../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../../dev/README.md)  
[↦ | Core-Internals | ↤](../../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../../misc/README.md)  

[↦ | **Libvirt, QEMU/KVM und Python** | ↤](./Libvirt-Handbuch.md)  
[↦ | Wizards-Handbuch | ↤](./Wizards-Handbuch.md)  
[↦ | [Feature] Implementierung von `DockerArena` und `VmArena` für erweiterte OS- und FS-Isolation (Entwicklung bis auf Weiteres Eingefroren) | ↤](./arena-requirements.md)  
[↦ | VmArena: Anforderungen an Betriebssystem-Szenarien und Routing | ↤](./vm-requirements.md)  

</div>
<!-- /qb:frame -->
