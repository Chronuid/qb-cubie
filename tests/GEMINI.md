## Ziele

Analyse der Test-Suite Strukturen und Identifikation potentieller Möglichkeiten zum Bau eines Analyse-Werkzeugs zur Erfassung der realen EBT-Case-Coverage für Quellcode-Objekte

---

## Hintergrund

Ich will später ein Meta-Gate für Quellcode bauen, welches die Regel umsetzt, dass Tests existieren, bezeiehungsweise die Menge der Tests für Objekte und die Art der Tests. Dazu müssen wir aber erstmal herausfinden können, welche Tests sich auf welche Objekte im Quellcode beziehen.

## Relevante Dokumente & Einstiegspunkte

@docs/GUIDE_Quality-Assurance.md
@docs/dev/README.md
@docs/dev/DEV-GUIDE_Agent-Reports.md

---

## Auftrag

Analysiere welche Möglichkeiten wir haben, um ein Analysewerkzeug zu bauen, mit dem wir herausfinden können, wie viele Tests und welche Arten von Tests auf welchen Objekten im Quellcode liegen.

Schreibe deinen Bericht in @tests/ANALYSIS_COVERAGE_OPTIONS.md .