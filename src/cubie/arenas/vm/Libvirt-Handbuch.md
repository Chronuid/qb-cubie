# **Libvirt, QEMU/KVM und Python**

# Handbuch zur Architektur und Implementierung der VmArena

Dieses Handbuch spezifiziert: 

- **die Implementierungs-Muster,**   
- **API-Referenzen**   
- **und architektonischen Richtlinien** 

*zur Nutzung der Libvirt-Python-Bindings, um die Anforderungen an Gast-Authentizität, Ephemeralität, netzwerklose Interprozesskommunikation (Air-Gapping) sowie die verlustfreie Fehler-Rekonstruktion zu erfüllen.*

| API / Funktion | Modul / Klasse | Kurzbeschreibung |
| :---- | :---- | :---- |
| **libvirt.open(uri)** | **libvirt** | Öffnet die Verbindung zum Hypervisor (z.B. qemu:///system) als zentralen Einstiegspunkt für die Orchestrierung.  |
| **createXML(xml, flags)** | **virConnect / virStoragePool** | Erzeugt und startet eine neue (transiente) Domain oder ein ephemeres Storage-Volume basierend auf einer XML-Deklaration.  |
| **destroy()** | **virDomain** | Erzwingt das sofortige Herunterfahren einer aktiven virtuellen Maschine für den sauberen Teardown-Prozess.  |
| **storagePoolLookupByName(name)** | **virConnect** | Sucht einen Storage-Pool anhand seines Namens, was für die programmatische Erzeugung der QCOW2-Overlays benötigt wird.  |
| **get_error_code()** | **libvirt.libvirtError** | Liefert den spezifischen libvirt-Fehlercode (wie VIR_ERR_NO_DOMAIN), um Fehler in der Testsuite gezielt abzufangen und CLI-Wizards zu triggern.  |
| **virEventRegisterAsyncIOImpl()** | **libvirtaio** | Registriert die Libvirt-C-Events im laufenden Python asyncio Event-Loop für eine ressourcenschonende, nicht-blockierende Nebenläufigkeit.  |
| **to_dict() / from_dict()** | **tblib.Traceback** | Serialisiert und deserialisiert den Frame-Stack einer Exception sicher in ein JSON- oder MessagePack-kompatibles Format, ohne fehleranfälliges pickle.  |
| **as_traceback()** | **tblib.Traceback** | Wandelt das rekonstruierte Traceback-Dictionary auf der Host-Seite zurück um, damit die Exception mit originalem Call-Stack geworfen werden kann.  |
| **pack('>I', length)** | **struct** | Generiert das 4-Byte lange Unsigned-Integer-Prefix (Big-Endian) für das zustandslose Message-Framing beim Senden über den VirtIO-Socket.  |
| **unpack('>I', bytes)** | **struct** | Entschlüsselt das Length-Prefix beim Empfänger, um die exakte Bytegröße des nachfolgenden Payloads blockierungsfrei zu ermitteln.  |

## **1. Architektonisches Fundament: Die Libvirt Python-Bindings**

Libvirt abstrahiert die Komplexität verschiedener Hypervisoren durch eine native, in C geschriebene API, die über die offiziellen Python-Bindings (libvirt-python) zugänglich gemacht wird1. Diese Bindings reflektieren die zugrunde liegende C-Struktur, weshalb ein tiefes Verständnis der fundamentalen Objekte für die Implementierung der VmArena unerlässlich ist.  
Das System stützt sich auf eine Hierarchie von Objekten, die den Lebenszyklus der Virtualisierung verwalten. Der Einstiegspunkt ist stets das virConnectPtr-Objekt (in Python libvirt.virConnect), welches die aktive Verbindung zum Hypervisor repräsentiert3. Über dieses Verbindungsobjekt werden die sekundären Entitäten orchestriert: virDomainPtr repräsentiert eine einzelne virtuelle Maschine (aktiv oder inaktiv) und steuert Zustandsübergänge, während virStoragePoolPtr und virStorageVolPtr die Speichermedien verwalten, die für die ephemeren Dateisysteme der Arena zwingend notwendig sind.

### **Verbindungsstrategien und Berechtigungskonzepte**

Die Initialisierung der Arena in der Methode setup() beginnt mit dem Aufbau der Hypervisor-Verbindung. Libvirt unterscheidet dabei architektonisch stark zwischen System- und Session-Kontexten, welche über den Connection-URI definiert werden.

| Verbindungs-URI | Ausführungskontext | Implikationen für die VmArena |
| :---- | :---- | :---- |
| qemu:///system | Root-Daemon (System-Level) | Ermöglicht die strikte Durchsetzung von RAM/CPU-Limits via Cgroups v2 und bietet vollständige Kontrolle über Kernel-Ressourcen4. |
| qemu:///session | User-Space (Unprivileged) | Vollständig unprivilegierte Ausführung, ideal zur Validierung von POSIX-Berechtigungskonzepten, limitiert jedoch tiefe Host-Eingriffe. |

Für die Architektur der VmArena wird primär der qemu:///system-Kontext referenziert, da die Testsuite kompromisslose Hardware- und Ressourcen-Kontrollen (DeviceResources) erfordert, welche physisch durchgesetzt werden müssen. Die geforderte Gast-Authentizität (Ausführung im User-Space) wird nicht durch einen unprivilegierten Hypervisor-Daemon erreicht, sondern durch die explizite Deklaration der Privilegien-Reduktion im Domain-XML für den Gast und den zugehörigen Dateisystem-Daemon (virtiofsd).


### **Das State-Guard Pattern und Self-Healing UX**

Fehler in der Libvirt-Bibliothek werden als libvirt.libvirtError-Exceptions geworfen und intern über die Enumeration virErrorNumber klassifiziert.   
Wenn beispielsweise der Hypervisor-Daemon auf dem Host nicht läuft oder der aktuelle Benutzer nicht den erforderlichen Gruppen (z. B. libvirtd oder kvm) angehört, schlägt der Aufruf von libvirt.open() fehl.  
Die Arena extrahiert in diesem Fall den spezifischen Fehlercode via get_error_code(). Handelt es sich um VIR_ERR_NO_CONNECT oder VIR_ERR_SYSTEM_ERROR, kann die Testsuite den Fehler schlucken und stattdessen einen interaktiven CLI-Wizard starten, der den Entwickler durch die Installation der Abhängigkeiten (apt-get install qemu-kvm libvirt-daemon-system) oder das Hinzufügen des Benutzers zur KVM-Gruppe führt. Fehlt hingegen das in der Arena deklarierte Basis-Image, resultiert dies in einem Fehler während der Storage-Orchestrierung (oft VIR_ERR_NO_DOMAIN oder VIR_ERR_NO_STORAGE_VOL), woraufhin die Engine den Download des referenzierten Betriebssystems initiieren kann.


## **2. Ephemerität: Storage-Orchestrierung und Copy-on-Write**

Ein fundamentaler Aspekt des Example-Based Testing (EBT) ist die kompromisslose Isolation von Nebenwirkungen. Tests, die das Dateisystem des Betriebssystems mutieren, dürfen unter keinen Umständen sequentielle oder parallele Testläufe kontaminieren. Die Lösung für diese Anforderung liegt in der Nutzung des QCOW2-Formats (QEMU Copy On Write) mit sogenannten Backing Files (Overlays).

### **Die Mechanik von QCOW2-Overlays**

Anstatt für jeden Testlauf ein vollständiges Betriebssystem-Image zu kopieren – was aufgrund der I/O-Latenzen bei hunderten parallelen VMs unweigerlich zu massiven Bottlenecks führen würde – generiert die VmArena flüchtige Delta-Images. Das deklarierte Basis-Image wird strikt im Read-Only-Modus behandelt. Jegliche Schreiboperationen, die das Gast-Betriebssystem während der execute()-Phase durchführt, werden vom KVM-Hypervisor auf Block-Ebene abgefangen und exklusiv in das winzige, ephemere Overlay geschrieben.  
Dieser Ansatz transformiert die Ressourcen-Allokation: Der I/O-Overhead und der Speicherbedarf pro virtueller Maschine skalieren nicht länger mit der Größe des Basis-Betriebssystems, sondern ausschließlich mit den vom Testfall aktiv induzierten Modifikationen am Dateisystem.

### **Programmatische Storage-Verwaltung via Libvirt API**

Obwohl die Erzeugung solcher Overlays auf der Kommandozeile durch `qemu-img create -f qcow2 -b base.qcow2 overlay.qcow2` möglich wäre, untersagt die Architekturvorgabe fehleranfällige CLI-Wrapper. Stattdessen wird die C-basierte Libvirt-API über Storage Pools und Volumes genutzt18.  
Die Arena definiert in der setup()-Routine einen Directory-Storage-Pool, welcher den physischen Ort der ephemeren Workspaces auf dem Host-System abbildet18. Innerhalb dieses Pools wird programmatisch ein neues Storage-Volume als XML definiert, das über das Element `<backingStore>` auf das unveränderliche Basis-Image verweist.  

```Python  
import libvirt

def create_ephemeral_workspace(conn: libvirt.virConnect, pool_name: str, base_image_path: str, run_id: str) -> str:
    pool = conn.storagePoolLookupByName(pool_name)
    
    vol_xml = f"""
    <volume type='file'>
      <name>workspace_{run_id}.qcow2</name>
      <capacity unit='G'>20</capacity>
      <target>
        <format type='qcow2'/>
      </target>
      <backingStore>
        <path>{base_image_path}</path>
        <format type='qcow2'/>
      </backingStore>
    </volume>
    """
    # Die Methode volCreateXML erzeugt das Copy-on-Write-Image in Millisekunden
    vol = pool.storageVolCreateXML(vol_xml, 0)
    return vol.path()
```  
Diese Implementierung garantiert Ephemeralität auf Infrastruktur-Ebene. In der teardown()-Methode der Arena wird das Volume über die API-Funktion delete() restlos zerstört, wodurch alle während des Tests vorgenommenen FS-Mutationen unwiderruflich verworfen werden.

## **3. FS-Hydration und Path-Traversal-Prävention**

Die VmArena fordert die Projektion von Host-Dateien in den virtuellen Workspace (die in WorldState.fs deklarierte Topologie). Während das QCOW2-Overlay das Basis-Betriebssystem bereitstellt, müssen test-spezifische Skripte, der Test-Runner selbst oder zu validierende Konfigurationsdateien nahtlos in den Gast injiziert werden.

### **VirtioFS für Performance und Semantik**

Um die Topologie in den Gast zu übertragen, wird virtiofs eingesetzt. Im Gegensatz zu klassischen Netzwerk-Dateisystemen oder 9pfs wurde VirtioFS speziell für die Virtualisierung entwickelt. Es bietet lokale Dateisystemsemantiken (inklusive POSIX-Berechtigungen) und teilt Speicherbereiche direkt zwischen Host und Gast über das Memory-Backing (memfd oder /dev/shm), was die Performance maximiert.  
Die Konfiguration im Libvirt-XML der Domain integriert den Host-Pfad des bereitgestellten Workspaces und definiert einen Tag, unter dem das Dateisystem im Gast gemountet werden kann:

```XML  
<memoryBacking>
  <source type='memfd'/>
  <access mode='shared'/>
</memoryBacking>

<devices>
  <filesystem type='mount' accessmode='passthrough'>
    <driver type='virtiofs'/>
    <source dir='/var/lib/cubie/workspaces/run_839/hydrated_fs'/>
    <target dir='arena_workspace'/>
  </filesystem>
</devices>
```

Im Gast-Betriebssystem wird die Topologie anschließend über einen simplen Mount-Befehl (`mount -t virtiofs arena_workspace /mnt/workspace`) materialisiert.


### **Unprivileged Mode und Ausbruchs-Prävention**

Da die Testsuite spezifische Pfad-Auflösungen, absolute versus relative Pfade und Backslash-Formate validiert, besteht eine inhärente Gefahr von Path-Traversal-Angriffen oder bösartigen Symlinks, die versuchen könnten, auf kritische Host-Dateien (z. B. /etc/shadow des Hosts) zuzugreifen.  
Die VmArena blockiert diese Ausbruchsversuche an der logischen Grenze durch die strikte Nutzung von unprivilegierten Daemons. Der Prozess, der die Dateien an den Gast durchreicht (virtiofsd), muss in der Architektur zwingend von Libvirt verwaltet werden. Durch die Parameterisierung des Daemons, insbesondere durch den Einsatz von Sandboxing (sandbox=namespace), wird virtiofsd in isolierte Mount-, PID- und Netzwerk-Namespaces eingekapsel.  
Zusätzlich ermöglicht VirtioFS UID/GID-Mappings (User ID Mappings). Dies bedeutet, dass eine Modifikation, die vom Gast scheinbar als Root-Benutzer ausgeführt wird, auf dem Host auf eine unprivilegierte Host-UID abgebildet wird (Rootless Virtualization). Ein Path-Traversal-Versuch, der die Virtualisierungsgrenze durchbricht, scheitert somit unweigerlich an den nativen Kernel-Zugriffskontrollen des Host-Systems, da der zugreifende Thread keinerlei Rechte außerhalb des zugewiesenen Workspace-Verzeichnisses besitzt7. Diese Architektur erfüllt die Anforderung an kompromisslose Systemintegrität.


## **4. Hardware-Kontrolle und Air-Gapping**

Eine robuste Test-Engine für Betriebssystem-Szenarien muss sicherstellen, dass Tests das Host-System nicht durch unkontrollierten Ressourcenkonsum destabilisieren. Die Deklarationen von RAM- und CPU-Limits (DeviceResources) müssen physisch durchgesetzt werden.


### **Durchsetzung via Linux Cgroups**

Libvirt übersetzt die im Domain-XML definierten Hardware-Limits direkt in Cgroup-Restriktionen (Control Groups v2) des Linux-Kernels. Dies bietet den Vorteil, dass die Limits deterministisch greifen, ohne dass fehleranfällige Container-Abstraktionen benötigt werden.

| Limitierungs-Typ | Libvirt XML-Element | Cgroup v2 Mapping (Host-Ebene) |
| :---- | :---- | :---- |
| RAM-Obergrenze | \<memory unit='MiB'\>512\</memory\> | memory.max |
| RAM-Soft-Limit | \<currentMemory unit='MiB'\>256\</currentMemory\> | memory.high |
| CPU-Zeit (Quota) | \<cputune\>\<quota\>50000\</quota\>\</cputune\> | cpu.max (Mikrosekunden pro Periode) |
| CPU-Kerne | \<vcpu placement='static'\>2\</vcpu\> | cpuset.cpus |

Durch die Definition von \<cputune\> und \<quota\> wird beispielsweise verhindert, dass eine Endlosschleife im injizierten Test-Code (target) die Host-CPU blockiert. Der Kernel drosselt die Ausführung der virtuellen Maschine exakt auf das vorgegebene Limit.


### **Air-Gapping auf Hypervisor-Ebene**

Die Anforderungen fordern eine vollständige Blockade des Egress-Traffics, sofern das Netzwerk nicht explizit aktiviert wurde (network=False). In herkömmlichen Umgebungen erfordert dies komplexe Firewall-Regeln (iptables/nftables). In der VmArena-Architektur wird Air-Gapping durch das Prinzip des "Secure by Default" realisiert: Wird im `<devices>`-Block des Libvirt-XMLs kein `<interface>`-Tag deklariert, existiert schlichtweg keine virtuelle Netzwerkkarte (NIC) im Gast.  
Ohne physikalisch emulierte Netzwerkschnittstelle gibt es keine Routing-Tabelle zum Host und somit absolut keine Möglichkeit für den Gast, TCP/IP-Pakete zu versenden. Dies ist die effizienteste und sicherste Methode, um Air-Gapping zu garantieren.


## **5. Zustandslose IPC via VirtIO-Serial und Framing**

Da die VmArena aufgrund des Air-Gappings isoliert ist, entfällt die Möglichkeit, den Test-Code über gewöhnliche SSH- oder REST-Schnittstellen in den Gast zu injizieren und die Resultate abzufragen. Die Lösung für diese netzwerklose Interprozesskommunikation (IPC) bildet VirtIO-Serial.  
VirtIO-Serial stellt dedizierte, serielle Hardware-Kanäle zwischen dem Host und dem Gast bereit, die über den gemeinsam genutzten Speicher des Hypervisors operieren. Im Gast manifestiert sich dieser Kanal als Character-Device (z.B. /dev/virtio-ports/cubie.agent), während Libvirt auf der Host-Seite angewiesen wird, diesen Kanal an einen lokalen UNIX-Domain-Socket zu binden31.

```XML  
<devices>
  <controller type='virtio-serial' index='0'/>
  <channel type='unix'>
    <source mode='bind' path='/var/run/cubie/vmarena/worker_42.sock'/>
    <target type='virtio' name='cubie.agent.channel'/>
  </channel>
</devices>
```

### **Das Length-Prefix Message Framing**

Ein kritisches Lösungsmuster bei der Nutzung von UNIX-Sockets und seriellen Kanälen ist das Message-Framing. Da Sockets auf kontinuierlichen Byte-Streams ohne inhärente Nachrichtengrenzen basieren, können gesendete Datenpakete vom Kernel fragmentiert werden. Ein recv()-Aufruf auf dem Socket könnte nur ein halbes JSON-Dokument oder MessagePack-Payload zurückliefern, was die Deserialisierung zum Absturz bringt.  
Um dies zu verhindern, implementiert die VmArena ein Length-Prefix-Framing-Protokoll, analog zur Funktionsweise des QEMU Guest Agents:

> 1. **Host sendet (Code-Injektion):** Die execute()-Methode der Arena serialisiert das Target sowie args und kwargs in ein Byte-Array (z.B. via MessagePack). Anschließend wird die exakte Länge dieses Arrays berechnet und als 4-Byte großer Unsigned Integer (Big-Endian) vorangestellt.  
> 2. **Gast empfängt:** Der im Gast laufende Agent öffnet /dev/virtio-ports/cubie.agent. Er liest in einer blockierenden Schleife exakt die ersten 4 Bytes aus, entpackt diese (struct.unpack('\>I', prefix)) und weiß nun präzise, wie viele Bytes er lesen muss, um den vollständigen Payload zu erhalten.  
> 3. **Ausführung & Antwort:** Der Gast deserialisiert die Instruktionen, führt den Test aus und sendet das funktionale Resultat sowie den akkumulierten WorldState über den gleichen Kanal und mit dem gleichen Framing-Mechanismus zurück an den Host.

Dieses zustandslose Kommunikationsmuster ist robust, resistent gegen Netzwerk-Timeouts und eliminiert das Risiko fragmentierter Datenströme vollständig38.

## **6. Verlustfreie Fehler-Rekonstruktion mit tblib**

Die Isolationsarchitektur bringt eine signifikante Herausforderung für das Test-Framework mit sich: Wenn der in den Gast injizierte Test-Code eine Exception wirft, muss der Cubie-Runner auf dem Host in der Lage sein, den Fehler exakt nachzuvollziehen. Ein simpler String-Dump der Fehlermeldung reicht nicht aus, da Entwickler den vollständigen Call-Stack (Traceback) benötigen, um die fehlerhafte Zeile im Test-Code zu identifizieren.  
Das Problem besteht darin, dass native Python-Traceback-Objekte fest an die Ausführungs-Frames und den Speicher des Laufzeit-Interpreters gebunden sind. Sie lassen sich weder über das pickle-Modul noch über JSON oder MessagePack nativ serialisieren, um sie über den VirtIO-Kanal zu senden.

### **Traceback-Serialisierung im Gast**

Dieses architektonische Hindernis wird durch die Bibliothek python-tblib gelöst. tblib abstrahiert den Frame-Stack und bietet Werkzeuge, um Tracebacks in serialisierbare, einfache Dictionaries umzuwandeln (Pickle-free Serialization).  
Der Gast-Agent fängt Ausführungsfehler auf oberster Ebene ab, extrahiert die Exception-Informationen via `sys.exc_info()` und transformiert sie:

```Python  
import sys, tblib, msgpack

try:
    # Ausführung des über VirtIO injizierten EBT-Szenarios
    result = execute_injected_code(payload)
except Exception as e: exc_type, exc_value, exc_traceback = sys.exc_info()
    # Transformation des Frames in ein serialisierbares Format ohne Pickle
    tb_wrapper = tblib.Traceback(exc_traceback)
    error_payload = {
        "status": "error",
        "exc_type": exc_type.__name__,
        "exc_value": str(exc_value),
        "traceback_dict": tb_wrapper.to_dict()
    }
    # Senden des error_payload über VirtIO (inklusive Length-Prefix-Framing)
    send_framed_message(channel_fd, msgpack.packb(error_payload))
```

### **Rekonstruktion auf dem Host**

Sobald die execute()-Methode der Arena den Payload über den UNIX-Socket empfängt und den status: "error" erkennt, wird der Fehler auf dem Host wiederbelebt. Die Arena rekonstruiert das Traceback-Objekt aus dem Dictionary (`tblib.Traceback.from_dict()`) und instanziiert die ursprüngliche Exception.  
Anschließend wird die Exception mit dem wiederhergestellten Call-Stack über `raise exception.with_traceback(tb)` dynamisch neu geworfen. Dies garantiert, dass der Test-Runner auf dem Host einen präzisen, nativ anmutenden Python-Traceback ausgibt, obwohl der Fehler in einer air-gapped Virtual Machine aufgetreten ist. Der Vorgang ist für den Endnutzer von cubie völlig transparent.

## **7. Nebenläufigkeit, Queueing und Asyncio-Integration**

### **Drosselung über asyncio.Queue**

Um die Stabilität zu garantieren, implementiert die Engine eine asynchrone Warteschlange (asyncio.Queue), die als Semaphore fungiert. Die Größe der Queue wird beim Start anhand des verfügbaren Host-RAMs und der deklarierten RAM-Limits pro Arena dynamisch berechnet. VMs werden nur dann aus der Queue geholt und provisioniert, wenn physische Kapazitäten freigegeben wurden.

### **Nicht-blockierende Orchestrierung mit libvirtaio**

Durch den Aufruf von `libvirtaio.virEventRegisterAsyncIOImpl()` wird der Libvirt-interne Event-Listener an den laufenden asyncio-Loop des Host-Prozesses gebunden. Dadurch kann die Arena auf Lifecycle-Events (wie den erfolgreichen Boot oder einen unerwarteten Crash der Domain) über asynchrone Callbacks reagieren, anstatt in blockierenden while-Schleifen Ressourcen zu verschwenden.

## **8. Performance: MicroVMs und Direct Kernel Boot**

Der microvm-Typ, der maßgeblich von AWS Firecracker inspiriert wurde, entfernt jeglichen PCI-Bus, USB-Controller und ACPI-Support aus der Architektur. Jegliche Gerätekommunikation (Festplatten, VirtIO-Serial, VirtioFS) wird auf hardwarenahe virtio-mmio (Memory Mapped I/O) Zugriffe umgeleitet, was den Overhead drastisch minimiert.  
Zusätzlich verzichtet die Arena auf ein BIOS-Image. Stattdessen liest Libvirt den Linux-Kernel des Gastes direkt auf dem Host und projiziert ihn direkt in den RAM der virtuellen Maschine, ohne Bootloader.

```XML  
<os>
  <!-- Nutzung des schlanken MicroVM-Maschinentyps -->
  <type arch='x86_64' machine='microvm'>hvm</type>
  <!-- Direct Kernel Boot zur Umgehung des BIOS/UEFI -->
  <kernel>/var/lib/cubie/vmarena/kernels/vmlinuz-guest</kernel>
  <!-- Direkter Start des Cubie-Agents anstelle von systemd -->
  <cmdline>console=ttyS0 root=/dev/vda rw init=/cubie/agent/daemon</cmdline>
</os>
```

Durch das Überspringen von systemd und dem direkten Starten des Kommunikations-Daemons als Init-Prozess (init=/cubie/agent/daemon) reduziert sich die End-to-End Boot-Zeit einer VM auf unter 100 Millisekunden.

## **9. Mapping des Arena-Protokolls: Die Implementierung**

Alle vorangegangenen Konzepte konvergieren in der Implementierung des in der Anforderung definierten Arena-Protokolls. Das folgende konzeptionelle Lösungsmuster demonstriert eine schemenhafte Skizze zur Integration der Architektur in die Python-Klasse:

```Python  
import libvirt, asyncio, struct, msgpack, tblib
from typing import Any
from pathlib import Path

class LibvirtVmArena:
    def __init__(self, run_id: str, base_image: Path):
        self.run_id = run_id
        self.base_image = base_image
        self.conn = libvirt.open('qemu:///system')
        if not self.conn: raise RuntimeError("Trigger CLI Wizard - Hypervisor not accessible.")
        self.domain = None
        self.sock_path = Path(f"/var/run/cubie/vmarena_{run_id}.sock")

    def workspace_path(self) -> Path:  return Path(f"/var/lib/cubie/workspaces/{self.run_id}")

    def setup(self, state: 'WorldState') -> None:
        self._provision_cow_storage()   # 1. Erzeuge QCOW2 Overlay via Storage Pool (CoW)
        self._hydrate_workspace(state)   # 2. FS-Hydration: Bereite VirtioFS Mounts vor
        xml_desc = self._generate_domain_xml()   # 3. Domain Definition: Cgroups (CPU/RAM),
       #  Air-Gapping (kein <interface>), VirtIO-Serial an self.sock_path, und Direct Kernel Boot.
        self.domain = self.conn.createXML(xml_desc, 0)   # 4. Erzeuge transiente VM        
        self._connect_ipc_socket()   # 5. Verbinde an den erstellten UNIX Socket für VirtIO IPC

    def execute(self, target: Any, args: tuple, kwargs: dict) -> Any:
        # Zustandslose IPC mit Length-Prefix-Framing
        payload = msgpack.packb({"target": target.__name__, "args": args, "kwargs": kwargs})
        length_prefix = struct.pack('>I', len(payload))
        self.socket.sendall(length_prefix + payload)   # Sende an /dev/virtio-ports/cubie.agent im Gast
        # Blockierendes (oder via asyncio asynchrones) Lesen der Antwort
        resp_len_data = self._recv_exact(4)
        resp_len = struct.unpack('>I', resp_len_data)[0]
        resp_payload = msgpack.unpackb(self._recv_exact(resp_len))
        if resp_payload.get("status") == "error": # Verlustfreie Fehler-Rekonstruktion
            tb_dict = resp_payload["traceback_dict"]
            tb = tblib.Traceback.from_dict(tb_dict).as_traceback()
            # Rekonstruktion und Re-Raise auf dem Host
            exc_class = getattr(builtins, resp_payload["exc_type"], Exception)
            raise exc_class(resp_payload["exc_value"]).with_traceback(tb)
        return resp_payload.get("result")

    def get_state(self) -> 'WorldState':
        # Rufe Mutation-Deltas über den IPC-Kanal ab oder 
        # analysiere das durch VirtioFS gemountete Host-Verzeichnis.
        return self._package_mutated_state()

    def teardown(self) -> None:
        if self.domain and self.domain.isActive(): self.domain.destroy() # Harter SIGTERM an die VM
        self._destroy_cow_storage()
        self.conn.close()

```