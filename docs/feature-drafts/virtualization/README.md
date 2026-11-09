<center>

# Virtualisierung: eingefrorene Feature-Entwürfe

![Cubie](../../.assets/cubie-logo-written.png)

**Status: nicht implementiert; noch auszuarbeiten.** `DockerArena` und `VmArena`
gehören derzeit nicht zur öffentlichen API von Cubie. Es gibt keine ausführbare
Docker- oder VM-Arena und keine zugesicherte Container-, Netzwerk-, Ressourcen-
oder Betriebssystem-Isolation durch diese Entwürfe.

---

</center>

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

---

---

<center>

![Error while trying to load the image](../../.assets/cubie-small.png)

## Dokumentation

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](../../GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](../../GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](../../GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](../../GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](../../GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](../../GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](../../GUIDE_Linter.md)  

[↦ | Entwicklerübersicht EBT | ↤](../../dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>
