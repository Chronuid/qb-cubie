> **Feature-Entwurf – nicht implementiert, Entwicklung eingefroren.**
> Die folgenden Beschreibungen sind Zielvorstellungen und keine zugesicherten Funktionen von Cubie.

# Wizards-Handbuch


---

*"Du bist ein Zauberer, Harry!"*

---

## Design

**Singleton-Instanzen, Python-SDK und Command-Pattern als Schnittstelle:**  
→ CLI und GUI sind "Fassaden"-Interfaces zum Singleton-Kern-Prozess.  
→ Interfaces sind mutable (man kann das automatische Aufploppen der GUI deaktivieren und rein über die Python-SDK oder CLI arbeiten).  
→ Die "Fassaden"-Interface beziehen sich in ihrem Zustand auf den Singleton-Kern, lassen sich wie per Fernbedingung von jeder Seite aus bedienen und zeigen die entsprechend aktuellen Zustandsänderungen.

* **Kern (Singleton):** Verwaltet den globalen Zustand, hält die OS-spezifischen Installations-Kataloge und führt die Subprozesse aus. Er weiß absolut nichts von der Existenz einer GUI oder CLI.
* **Kommunikation (Command & Observer):** Die Interfaces senden Commands an den Kern. Der Kern funkt über Event-Callbacks oder Signale asynchron seinen Fortschritt zurück.
* **Headless vs. Interactive (Mutable Interfaces):** Die Fassade passt sich dem Ausführungskontext an. Läuft `cubie` in einer CI/CD-Pipeline oder wird automatisiert via Python-SDK aufgerufen, bleibt die PySide6-GUI komplett stumm ("Headless Mode"). Läuft es im interaktiven Terminal, schaltet sich die GUI oder CLI als Vermittler dazwischen.

---

## Grundlagen für Wizards

Ein Install-Wizard (Installationsassistent) führt Benutzer schrittweise durch den Prozess der Softwareinstallation oder -einrichtung. Das primäre Ziel ist es, Komplexität zu reduzieren, Fehler zu minimieren und eine schnelle Betriebsbereitschaft (Time-to-Value) zu garantieren.

### 1. Kernkonzepte & Psychologie
Ein guter Wizard basiert auf etablierten UX-Prinzipien:

* Linearer Ablauf: Komplexe Aufgaben werden in sequenzielle, leicht verdauliche Häppchen (Schritte) zerlegt. Dies reduziert die kognitive Belastung.
* Fortschrittsanzeige (Progress Indicator): Der Benutzer muss jederzeit wissen, wo er sich befindet (z. B. Schritt 2 von 5). Das gibt ein Gefühl von Kontrolle und Fortschritt.
* Sinnvolle Standardwerte (Smart Defaults): Die Mehrheit der Nutzer klickt einfach auf "Weiter". Die Standardoptionen müssen daher sicher, performant und für 80 % der Anwendungsfälle optimal sein.
* Zustandsverwaltung (State Management): Der Wizard muss sich Eingaben merken. Wenn ein Nutzer einen Schritt zurückgeht, dürfen bereits eingegebene Daten nicht verloren gehen.

### 2. Typische Phasen eines Wizards
Ein Standard-Installationsassistent lässt sich meist in vier Phasen unterteilen:

[ Willkommen & Setup ] ──> [ Konfiguration ] ──> [ Verarbeitung/Installation ] ──> [ Abschluss ]

| Phase | Typische Inhalte | Best Practice |
|---|---|---|
| 1. Vorbereitung | Willkommensbildschirm, Systemvoraussetzungen prüfen, Lizenzvereinbarung (EULA). | Prüfen Sie Systemanforderungen (Speicherplatz, OS-Version) automatisch im Hintergrund, statt den Nutzer zu fragen. |
| 2. Konfiguration | Zielverzeichnis wählen, Komponenten auswählen, Benutzerkonto/Datenbank einrichten. | Bieten Sie einen "Express"-Modus (Standard) und einen "Benutzerdefinierten" Modus für Experten an. |
| 3. Ausführung | Fortschrittsbalken während des Kopierens/Konfigurierens der Dateien. | Zeigen Sie eine verständliche Statusmeldung (z. B. "Datenbank wird initialisiert..."), nicht nur nackten Code. |
| 4. Abschluss | Erfolgsmeldung, "Erste Schritte"-Links, Start-Button. | Geben Sie dem Nutzer eine klare Call-to-Action (z. B. "Anwendung jetzt starten"). |


### 3. Best Practices für die Entwicklung

#### UI/UX-Design

* Klare Navigation: Nutzen Sie eindeutige Buttons wie Zurück, Weiter (oder Installieren) und Abbrechen. Der primäre Button (Weiter) sollte visuell hervorgehoben sein.
* Ein-/Ausgangs-Validierung: Validieren Sie Benutzereingaben (z. B. Passwörter oder Pfade) sofort auf der aktuellen Seite. Lassen Sie den Nutzer nicht auf "Weiter" klicken, um ihm dann eine Fehlermeldung zu präsentieren.
* Abbruch-Bestätigung: Wenn ein Nutzer auf Abbrechen klickt, fragen Sie nach ("Möchten Sie die Installation wirklich abbrechen?"), um Datenverlust durch versehentliche Klicks zu verhindern.

#### Technische Umsetzung & Architektur

* Idempotenz & Rollback: Schlägt die Installation in Schritt 4 fehl, muss der Wizard das System sauber hinterlassen. Entweder wird die Installation repariert (Idempotenz) oder alle bisherigen Änderungen werden rückgängig gemacht (Rollback).
* Asynchrone Verarbeitung: Blockieren Sie niemals die Benutzeroberfläche (UI Thread). Das Kopieren von Dateien oder Herunterladen von Paketen muss im Hintergrund (Background Worker) laufen, damit der Wizard nicht als "Keine Rückmeldung" einfriert.
* Ausführliches Logging: Schreiben Sie jeden Schritt und jeden Fehler in eine Log-Datei. Das ist für den Support und das Debugging überlebenswichtig.

#### Sicherheit & Barrierefreiheit

* Least Privilege Prinzip: Fordern Sie Administrator- oder Root-Rechte nur dann an, wenn sie absolut notwendig sind (und idealerweise erst im Moment der eigentlichen Installation, nicht schon beim Willkommensbildschirm).
* Tastaturbedienung & Screenreader: Der gesamte Wizard muss per Tab, Leerzeichen und Enter bedienbar sein (wichtig für Barrierefreiheit/Accessibility).

## 4. Häufige Anti-Patterns (Was Sie vermeiden sollten)

* ❌ Der "Wall of Text": Den Nutzer mit ellenlangen Texten oder unübersichtlichen EULAs zu erschlagen, die er ohnehin ungelesen wegklickt.
* ❌ Zu viele Schritte: Ein Wizard mit mehr als 5–7 Schritten ermüdet. Fassen Sie logisch zusammengehörige Einstellungen auf einer Seite zusammen.
* ❌ "Bloatware" unterjubeln: Das ungefragte oder versteckte Installieren von Drittanbieter-Software (Toolbars, Browsern) zerstört das Vertrauen der Nutzer nachhaltig.

---


## Wizards (Die Zustandsautomaten)

Die Wizards bilden eine hierarchische State-Machine. Sie agieren als modulare Zustandsautomaten, die kontextabhängig (headless via SDK oder interaktiv via PySide6/CLI) agieren können.

### SystemWizard (Discovery & Bindings)
* **Zustand:** `SystemDiscovery`
* **Aktion:** Prüft die physikalischen Host-Daten und Voraussetzungen.
* **Verantwortlichkeit:** Fungiert nicht nur als Inspektor, sondern auch als Übersetzer. Er ermittelt die Host-Distribution (z.B. Linux Mint vs. Arch) und instanziiert eine einheitliche Abstraktion der OS-spezifischen Bindings. Diese Bindings werden per Dependency Injection (DI) für alle nachfolgenden Prozesse bereitgestellt.

### TechWizard (Der System-Check)
* **Zustand:** `TechResolution`
* **Aktion:** Nutzt die vom `SystemWizard` injizierten Bindings, um fehlende Bibliotheken auf der vom User gewählten Ebene im System zu installieren.
* **Verantwortlichkeit:** Klärt den Nutzer über die fehlenden Virtualisierungs-Technologien auf und triggert die Host-spezifischen Installations-Befehle.

### AssetWizard (Scanner & Lazy-Registry)
* **Zustand:** `AssetDiscovery` & `AssetRegistry`
* **Aktion:** Fungiert zweigeteilt als konfigurierbarer Verzeichnis-Scanner und "Just-In-Time"-Gatekeeper.
* **Verantwortlichkeit:**
  1. **Scanner:** Durchkämmt beim Bootstrapping die **Host-Verzeichnisse** nach existierenden QCOW2-Images und indiziert deren Pfade. Der Nutzer kann hierbei das Verhalten exakt steuern: Er kann gezielt direkte Pfade übergeben, vollständige System-Laufwerke scannen oder die Suche auf spezifische Teil-Verzeichnisse beschränken.
  2. **Registry:** Nimmt Anfragen der Test-Suite (z.B. `VmArena(os=WIN_IMAGE)`) entgegen. **Lazy Evaluation:** Erst im Moment der konkreten Abfrage prüft der Wizard den Zustand des angeforderten Images. Besitzt das jeweilige OS-Image spezifische Lebenszyklus-Einschränkungen (wie etwa den 90-Tage-Evaluierungs-Timer bei Windows), greift hier die Validierung.

### ImageWizard (Die modulare QCOW2-Fabrik)
* **Zustand:** `ImageProvisioning`
* **Aktion:** Organisiert den OS-spezifischen Beschaffungs- und Build-Prozess über eine modulare Skript-Architektur.
* **Verantwortlichkeit:** Agiert als Orchestrator für eine Vielzahl an unabhängigen Provisionierungs-Modulen. Über ein Strategy-Pattern analysiert der Wizard das angeforderte Betriebssystem und delegiert die Aufgabe an das passende Modul (z. B. ein Linux-Cloud-Image-Downloader, ein `virt-builder`-Skript für BSD-Templates oder ein komplexer HashiCorp Packer-Runner für Windows). Der Wizard übernimmt dabei die modulspezifischen Vorbedingungen – wie etwa das Einholen von EULA-Opt-ins für proprietäre Systeme – und führt den Command-Pattern-Runner aus, bis das fertige QCOW2-Image ausgespuckt wird.

### ArenaReady (Der Guard)
* **Zustand:** `ArenaProvisioning`
* **Aktion:** Der Checkpoint ist passiert. Der Guard übergibt die Kontrolle an den eigentlichen Test-Runner.
* **Verantwortlichkeit:** Die `VmArena` übernimmt das deklarierte und vom `AssetWizard` validierte QCOW2-Image, generiert über Libvirt das flüchtige Copy-on-Write-Overlay und injiziert den EBT-Payload via VirtIO-Serial in den Gast.