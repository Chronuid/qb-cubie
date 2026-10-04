Ein Install-Wizard (Installationsassistent) führt Benutzer schrittweise durch den Prozess der Softwareinstallation oder -einrichtung. Das primäre Ziel ist es, Komplexität zu reduzieren, Fehler zu minimieren und eine schnelle Betriebsbereitschaft (Time-to-Value) zu garantieren.
Hier ist eine strukturierte Übersicht über die Grundlagen, Konzepte und Best Practices für moderne Install-Wizards.


## 1. Kernkonzepte & Psychologie
Ein guter Wizard basiert auf etablierten UX-Prinzipien:

* Linearer Ablauf: Komplexe Aufgaben werden in sequenzielle, leicht verdauliche Häppchen (Schritte) zerlegt. Dies reduziert die kognitive Belastung.
* Fortschrittsanzeige (Progress Indicator): Der Benutzer muss jederzeit wissen, wo er sich befindet (z. B. Schritt 2 von 5). Das gibt ein Gefühl von Kontrolle und Fortschritt.
* Sinnvolle Standardwerte (Smart Defaults): Die Mehrheit der Nutzer klickt einfach auf "Weiter". Die Standardoptionen müssen daher sicher, performant und für 80 % der Anwendungsfälle optimal sein.
* Zustandsverwaltung (State Management): Der Wizard muss sich Eingaben merken. Wenn ein Nutzer einen Schritt zurückgeht, dürfen bereits eingegebene Daten nicht verloren gehen.

## 2. Typische Phasen eines Wizards
Ein Standard-Installationsassistent lässt sich meist in vier Phasen unterteilen:

[ Willkommen & Setup ] ──> [ Konfiguration ] ──> [ Verarbeitung/Installation ] ──> [ Abschluss ]

| Phase | Typische Inhalte | Best Practice |
|---|---|---|
| 1. Vorbereitung | Willkommensbildschirm, Systemvoraussetzungen prüfen, Lizenzvereinbarung (EULA). | Prüfen Sie Systemanforderungen (Speicherplatz, OS-Version) automatisch im Hintergrund, statt den Nutzer zu fragen. |
| 2. Konfiguration | Zielverzeichnis wählen, Komponenten auswählen, Benutzerkonto/Datenbank einrichten. | Bieten Sie einen "Express"-Modus (Standard) und einen "Benutzerdefinierten" Modus für Experten an. |
| 3. Ausführung | Fortschrittsbalken während des Kopierens/Konfigurierens der Dateien. | Zeigen Sie eine verständliche Statusmeldung (z. B. "Datenbank wird initialisiert..."), nicht nur nackten Code. |
| 4. Abschluss | Erfolgsmeldung, "Erste Schritte"-Links, Start-Button. | Geben Sie dem Nutzer eine klare Call-to-Action (z. B. "Anwendung jetzt starten"). |


## 3. Best Practices für die Entwicklung

### 🎨 UI/UX-Design

* Klare Navigation: Nutzen Sie eindeutige Buttons wie Zurück, Weiter (oder Installieren) und Abbrechen. Der primäre Button (Weiter) sollte visuell hervorgehoben sein.
* Ein-/Ausgangs-Validierung: Validieren Sie Benutzereingaben (z. B. Passwörter oder Pfade) sofort auf der aktuellen Seite. Lassen Sie den Nutzer nicht auf "Weiter" klicken, um ihm dann eine Fehlermeldung zu präsentieren.
* Abbruch-Bestätigung: Wenn ein Nutzer auf Abbrechen klickt, fragen Sie nach ("Möchten Sie die Installation wirklich abbrechen?"), um Datenverlust durch versehentliche Klicks zu verhindern.

### 🛠️ Technische Umsetzung & Architektur

* Idempotenz & Rollback: Schlägt die Installation in Schritt 4 fehl, muss der Wizard das System sauber hinterlassen. Entweder wird die Installation repariert (Idempotenz) oder alle bisherigen Änderungen werden rückgängig gemacht (Rollback).
* Asynchrone Verarbeitung: Blockieren Sie niemals die Benutzeroberfläche (UI Thread). Das Kopieren von Dateien oder Herunterladen von Paketen muss im Hintergrund (Background Worker) laufen, damit der Wizard nicht als "Keine Rückmeldung" einfriert.
* Ausführliches Logging: Schreiben Sie jeden Schritt und jeden Fehler in eine Log-Datei. Das ist für den Support und das Debugging überlebenswichtig.

### 🔒 Sicherheit & Barrierefreiheit

* Least Privilege Prinzip: Fordern Sie Administrator- oder Root-Rechte nur dann an, wenn sie absolut notwendig sind (und idealerweise erst im Moment der eigentlichen Installation, nicht schon beim Willkommensbildschirm).
* Tastaturbedienung & Screenreader: Der gesamte Wizard muss per Tab, Leerzeichen und Enter bedienbar sein (wichtig für Barrierefreiheit/Accessibility).---

## 4. Häufige Anti-Patterns (Was Sie vermeiden sollten)

* ❌ Der "Wall of Text": Den Nutzer mit ellenlangen Texten oder unübersichtlichen EULAs zu erschlagen, die er ohnehin ungelesen wegklickt.
* ❌ Zu viele Schritte: Ein Wizard mit mehr als 5–7 Schritten ermüdet. Fassen Sie logisch zusammengehörige Einstellungen auf einer Seite zusammen.
* ❌ "Bloatware" unterjubeln: Das ungefragte oder versteckte Installieren von Drittanbieter-Software (Toolbars, Browsern) zerstört das Vertrauen der Nutzer nachhaltig.

---


Für den produktiven Ablauf bietet sich folgende hierarchische State-Machine (HSM) an, die sich vor den eigentlichen `setup()`-Aufruf der Libvirt-Architektur schaltet:

1. **State: SystemDiscovery**
* *Aktion:* Prüft non-destruktiv, ob `/var/run/libvirt/libvirt-sock` existiert, `/dev/kvm` ansprechbar ist und der aktuelle User in den Gruppen `kvm` und `libvirt` liegt.


* *Transition:* Wenn alles erfüllt ist $\rightarrow$ `AssetDiscovery`. Wenn nicht $\rightarrow$ `TechWizard`.


2. **State: TechWizard (Der System-Check)**
* *Aktion:* Spawnt die PySide6-GUI. Klärt den Nutzer auf, generiert die passenden Host-spezifischen Installations-Befehle (z.B. für Linux Mint) und führt sie über einen PolicyKit/sudo-Prompt aus.
* *Transition:* Nach erfolgreicher Installation $\rightarrow$ `SystemDiscovery` (Re-Evaluierung).


3. **State: AssetDiscovery**
* *Aktion:* Prüft die lokale Registry (dein `masterhub`) auf die Existenz und Gültigkeit der deklarierten QCOW2-Images.


* *Transition:* Wenn das Image fehlt oder der 90-Tage-Timer für Windows abgelaufen ist $\rightarrow$ `ImageWizard`. Wenn bereit $\rightarrow$ `ArenaReady`.


4. **State: ImageWizard (Die QCOW2-Fabrik)**
* *Aktion:* Spawnt die GUI, holt das EULA-Opt-in ein und triggert den Command-Pattern-Runner für den Download (Cloud-Images) oder den Packer-Build (Windows).
* *Transition:* Nach erfolgreicher Registrierung des Images $\rightarrow$ `AssetDiscovery`.


5. **State: ArenaReady**
* *Aktion:* Der Guard gibt den Test-Runner frei. Die `VmArena` übernimmt, generiert das Copy-on-Write-Overlay und injiziert den EBT-Payload via VirtIO-Serial.