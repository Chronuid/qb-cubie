<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Virtualisierung: eingefrorene Feature-Entwürfe

![Cubie](../../.assets/cubie-logo-written.png)

**Status: nicht implementiert; noch auszuarbeiten.** `DockerArena` und `VmArena`
gehören derzeit nicht zur öffentlichen API von Cubie. Es gibt keine ausführbare
Docker- oder VM-Arena und keine zugesicherte Container-, Netzwerk-, Ressourcen-
oder Betriebssystem-Isolation durch diese Entwürfe.

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../../README.md) • [QA-Handbuch](../../GUIDE_Quality-Assurance.md) • [DocEnsurance](../../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

Die bisherigen Klassen enthielten ausschließlich Konfigurationsfelder und keine
Implementierung des Arena-Protokolls. Sie liegen hier als Textdateien außerhalb
des Python-Pakets. Die früheren leeren VM-Module (`__init__.py`,
`libvirt_handles.py`, `wizard_cli.py`, `wizard_gui.py`, `wizards.py`) wurden entfernt.

- [Arena-Anforderungen](arena-requirements.md) und [VM-Anforderungen](vm-requirements.md)
  beschreiben das geplante Verhalten.
- [Docker-Konfigurationsskizze](dockerarena.py.txt) und
  [VM-Konfigurationsskizze](vmarena.py.txt) sind historische API-Entwürfe.
- [Libvirt-Handbuch](Libvirt-Handbuch.md) und [Wizards-Handbuch](Wizards-Handbuch.md)
  sind Architekturentwürfe; Aussagen über Verhalten oder Sicherheit sind Zielvorstellungen.
- Die bisherigen, vollständig übersprungenen VM-Tests sind als
  [Arena-Szenarien](test_vm_arena.py.txt), [Hardening-Szenarien](test_vm_hardening.py.txt)
  und [UX-Szenarien](test_vm_ux.py.txt) archiviert. Sie werden nicht von pytest
  gesammelt und sind keine Funktionsnachweise.

Verfügbar bleiben `TempFS` und `PyVenv`. Beide bieten keine OS-Sicherheitsgrenze.
Vor einer erneuten Veröffentlichung müssen die Entwürfe überarbeitet, das
Arena-Protokoll implementiert und die tatsächlichen Isolationsgarantien durch
ausführbare Tests nachgewiesen werden.

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
