# Cubie Core (`core.py`)

> *Das architektonische Fundament und der neutrale System-Knotenpunkt.*

Das `core.py`-Modul ist das Herzstück des Cubie-Frameworks, enthält jedoch bewusst keine eigenen Test-Paradigmen oder Ausführungs-Engines. Anstatt als unspezifische "Utils-Sammelstelle" zu fungieren, ist der Core die formelle, innerste Schicht der Architektur. Er bündelt ausschließlich die geteilten Werkzeuge, Marker und Basisklassen, auf denen alle spezifischen Test-Typen (wie EBT, RBT, PBT) aufbauen.

Der Core sorgt dafür, dass das Framework modular bleibt und die einzelnen Test-Disziplinen nicht miteinander verschmelzen.

---

## 1. Die "Gatekeeper"-Regel: Was gehört in den Core?

Da der Core leicht Gefahr läuft, zu einem unübersichtlichen Ablageort für Hilfsfunktionen zu mutieren, gilt für dieses Modul eine strikte Aufnahmeregel.
Ein Konzept, eine Klasse oder eine Funktion darf **nur dann** in `core.py` (und den zugehörigen Core-Dokumenten) leben, wenn es mindestens eine der folgenden Bedingungen erfüllt:

1. **Domänen-Übergreifend:** Die Komponente wird zwingend von *mehr als einem* Test-Typ (z. B. von `EBT` **und** `RBT`) genutzt.
2. **System-Brücke:** Die Komponente dient als formeller Knotenpunkt zwischen den internen Test-Klassen und externen Systemen (wie der Pytest-Orchestrierung oder Datenbank-Plugins).
3. **Architektonischer Vertrag:** Es handelt sich um abstrakte Schnittstellen oder Protokolle, die garantieren, dass zukünftige Erweiterungen (Open-Closed-Principle) nahtlos in das Framework passen.

Spezifische Logik – wie das Auflösen von Datei-Strukturen für EBT oder das Capturing von Terminal-Inputs für RBT – ist im Core strengstens untersagt und verbleibt in den jeweiligen Domänen-Modulen.

---

## 2. Aktuelle Kernkomponenten

Derzeit beheimatet der Core die beiden wichtigsten Säulen für die Skalierbarkeit und Integrität von Cubie:

### `class CubieBase` (Die System-Brücke)

Das architektonische Bindeglied zwischen der Pytest-Plugin-Ebene und den individuellen Test-Klassen.

* Sie fungiert als polymorphe Marker-Klasse, damit externe Systeme (wie der SQLite-Reporter) Cubie-Tests erkennen können, ohne die spezifischen Internas von EBT oder RBT kennen zu müssen.
* Alle Test-Disziplinen erben von dieser Basis, um eine einheitliche, stabile Schnittstelle nach außen zu garantieren.

### `class ConventionMap` (Das dynamische Registry-System)

Eine test-agnostische, universelle Übersetzungsschicht.

* Sie entkoppelt das Developer-Interface (Shorthands und primitive Datentypen) von den harten internen Zielstrukturen der Frameworks.
* Über ein Fluent Interface (`for_class`, `when`, `is_type`) erlaubt sie es, das implizite Mapping-Verhalten von Cubie dynamisch über Pytest-Fixtures anzupassen, ohne den Code der eigentlichen Ausführungs-Engines zu berühren.

*(Hinweis: Tiefergehende technische Spezifikationen zu diesen Kernkomponenten finden sich in den jeweiligen Sub-Dokumenten, z.B. `DEV-GUIDE_3-1_ConventionMap-Class.md`).*

---

## 3. Zukünftiges Wachstum

Der Core ist darauf ausgelegt, zu wachsen, sobald neue, systemübergreifende Abstraktionen nötig werden. Mögliche zukünftige Kandidaten für den Core sind:

* **Gemeinsame Typ-Definitionen (Types/Protocols):** Wenn z. B. EBT und FVT denselben abstrakten AST-Parser verwenden.
* **Zentrale Logging/Reporting-Formate:** Standardisierte Datenklassen für die Payload-Übergabe an das Plugin-System (z. B. strukturierte Confidence-Metriken aus dem RBT).