# Tickets

## Linter-Pipeline: Auto-Discovery, Pfad-Auflösung und Ignore-Mechanismen

### **Problembeschreibung:**
Wenn der Linter auf Projektverzeichnisse angesetzt wird, durchsucht er aktuell unselektiv alle Unterordner. Dies führt dazu, dass Fremdcode in `.venv`- oder Cache-Ordnern gescannt wird, was falsche Fehler in der EBT-Auswertung generiert. Zudem erfordert die API derzeit zwingend die Angabe eines Targets.

### **Aufgaben:**

* **Auto-Discovery implementieren:** Wenn `.check()` ohne explizites Target aufgerufen wird, soll automatisch das Root-Verzeichnis des Repositories (bzw. der Arena), in welchem der Linter ausgeführt wird, als Ziel gesetzt werden. Zusätzlich soll man explizite Pfade deklarieren können, um die Linter auf einen Bereich anzusetzen.
* **Integrierte Scope-Schärfung:** Interface-Erweiterung und Umsetzung von Scope-Mechanismen, um zu ignorierende Verzeichnisse (z. B. `.venv`, `__pycache__`, `.git`, `.ruff_cache`) aus dem Scope zu rauszuziehen.
* **Kontext-Weiche für Konfigurationsdateien:** Vor dem Subprozess-Aufruf prüft das Framework, ob eine `pyproject.toml` im Zielverzeichnis existiert.
  * *Falls ja:* Der Linter nutzt die native Konfiguration des Projekts.
  * *Falls nein:* Das Framework injiziert die Standard-Ausschlüsse.

---

## Linter-Pipeline: Type-Detector und Pre-Processing für In-Memory-Strings

### **Problembeschreibung:**
Die Linter stürzen bei In-Memory-Strings mit Fehler-Diagnosen ab, wenn diese unstrukturierten Text oder Markdown-Artefakte (z. B. von LLM-Agenten) enthalten. Die Linter interpretieren Backticks (`````) als Syntaxfehler (E999). Es fehlt eine Vorverarbeitungsstufe, welche alle Datei-Typen interpretieren, den eigentlichen Python-Code identifizieren und korrekt validieren kann.

### **Aufgaben:**

* **Block-Inspektor:** Implementierung einer Filterlogik im Pre-Processor, Dateityp-Blöcke (`python ... `) erkennen, dessen Inhalte extrahieren und konkatenieren kann.

---

## Linter-Interfaces: dynamisches Rule-Management und Regel-Konfiguration

### **Problembeschreibung:**
Oft ist es erforderlich, bestimmte Regeln (wie die Docstring-Pflicht `C0114` bei Pylint) kontextbezogen zu deaktivieren. Aktuell sind die Regel-Sets hart in den Linter-Profilen verdrahtet. Es benötigt ein erweitertes Rule-Management für die Linter.

### **Aufgaben:**

* **UX-zentriertes API-Design:** Entwurf einer intuitiven und entwicklerfreundlichen Schnittstelle, um spezifische Regel-IDs (wie `C0114` oder `CST001`) bei der Initialisierung der Linter gezielt zu deaktivieren oder zu konfigurieren. Der Fokus liegt auf einer klaren, selbsterklärenden Bedienung (Ergonomie) für den Endnutzer.