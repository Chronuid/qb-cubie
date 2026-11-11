# Vorbereiteter Kandidatenplan und Datenzulassung

Der aktuelle Starter automatisiert die unten beschriebenen technischen Schritte:
`./study --mode pilot --prepare-only`. Er schreibt bereinigte Snapshots,
Quittungen, gesammelte Test-IDs, Ausgangs-/Referenzbelege und das zugelassene
Aufgabenmanifest in ein neues Archiv. Die drei Pilotaufgaben wurden mit diesem
Weg bereits tatsächlich zugelassen; Details stehen im Techniknachweis.
Die Katalogangabe `technical_admission=pending` beschreibt weiterhin den
ursprünglichen fachlichen Katalogstand und ist keine laufzeitunabhängige
Freigabe aller 129 Aufgaben. Jede neue Studie prüft ihre konkrete Umgebung erneut.

Der vorhandene lokale Pool liegt unter
`/home/symphonie/PycharmProjects/devagent-comp/gemma-4-developer-agent/`.
Am 11.11.2026 enthielt `tasks.jsonl` 129 Aufgaben mit Issue, Ausgangscommit,
Referenzpatch und privatem Testpatch:

| Repository | Aufgaben |
| --- | ---: |
| fastapi/fastapi | 67 |
| Textualize/rich | 48 |
| psf/requests | 13 |
| encode/httpx | 1 |

Der [Katalog Version 2](candidate-catalog.json) hält den SHA256 des Quelldokuments,
Typen und Einzelprüfungen fest. [Prüfumfang und Ergebnisse](KANDIDATEN.md) umfassen
die ursprünglichen 15 und 24 weitere Aufgaben. Von 39 geprüften Aufgaben sind
26 im aktuellen Studienpfad fachliche Kandidaten; alle 129 IDs einschließlich der
90 semantisch ungeprüften Aufgaben bleiben inventarisiert. Der
[erste Zufallsplan](candidate-selection.json) ist als überholt gekennzeichnet und
bleibt nachvollziehbar. Alle ursprünglichen 15 Snapshots existieren; auch bei den
weiteren Aufgaben ist die Snapshot-Verfügbarkeit im Katalog vermerkt.

Die neue Auswahl erfolgt vor Modellmessungen reproduzierbar nach Aufgabentyp und
Repository, mit höchstens einer Aufgabe pro Verwandtschaftsgruppe. Anzahl,
Auswahlseed und Typfilter stehen in `[selection]`; die Stundenplanung unter
`[planning]`. Der Pool bildet überwiegend Bibliotheks-/Webentwicklung ab;
das begrenzt die Übertragbarkeit. Lifecycle-/Terminierungsaufgaben sind mit den
aktuell geprüften Fällen noch nicht im Hauptprofil vertreten.

**Der Kandidatenplan ist noch kein pauschal zugelassener Messdatensatz.** In den 129
Rohrecords fehlen explizite FAIL_TO_PASS- und PASS_TO_PASS-Zuordnungen. Der geprüfte
Snapshot `requests_7328.tgz` enthält `.git` einschließlich Historie. Die insgesamt
etwa 21 GiB Snapshots wurden nicht vollständig entpackt oder fachlich geprüft.

Vor dem fachlichen Piloten:

1. Die ausgewählten Ausgangsbäume aus den gleichnamigen `.tgz`-Archiven
   bereitstellen. `.git` vollständig entfernen; Symlinks prüfen und bei Bedarf
   auf Quellen innerhalb des Ausgangsbaums materialisieren. Nur den sichtbaren
   Baum neu packen. Private Patches bleiben im Host-Record.
2. Aufgabenbeschreibung und Patchumfang prüfen. Reine Test-/Konfigurationsfixes,
   die swegemmas Produktionsfilter nicht abbildet, vorab ausschließen. Auch
   unklare Anforderungen, Duplikate oder fehlende lokal bereitstellbare
   Abhängigkeiten mit Begründung dokumentieren.
3. Gemeinsame Aufgabenabhängigkeiten in die Basisimages aufnehmen. Beide Agenten
   benötigen denselben Ausgangsstand und dieselben Abhängigkeiten; nur Cubie
   kommt im Behandlungsimage hinzu.
4. Private Prüftests getrennt auf Ausgangs- und Referenzcode ausführen. Aus den
   tatsächlich gesammelten, vollständigen pytest-Node-IDs die Zuordnung bilden:
   fachlich rot → grün ist FAIL_TO_PASS; grün → grün ist PASS_TO_PASS. Nicht
   einfach einen Testfunktionsnamen raten oder einen Sammelfehler als Rot verwenden.
5. Die geprüften Recorddateien und sauberen Snapshots mit einem `tasks.json`
   nach [README](README.md#echte-aufgaben-einrichten) verbinden. `freeze` und
   `preflight` verlangen anschließend beide Gruppen und prüfen die Zuordnungen
   nochmals automatisch, einschließlich der jeweils benannten Ausgangstests.

Scheitert ein Kandidat an diesen **vor der Inferenz** geltenden Kriterien, den
Grund festhalten und den nächsten fachlich geeigneten Fall desselben Typs und
möglichst desselben Repositorys prüfen. Bei geändertem Pool erneut planen und
dessen Zusammensetzung vor Inferenz freigeben. Nicht nach Modellmisserfolgen
austauschen. Zurückgestellte, bedingte und ungeprüfte Fälle werden nicht still
als Ersatz aufgenommen. HTTPX ist nach der fachlichen Prüfung zurückgestellt.

Die Pilotkandidaten sind `rich_3278`, `fastapi_9425` und `requests_6589`.
Pilot zunächst mit einem Seed ausführen. Erst danach gemeinsame Budgets und
Agentenstand festlegen, die zugelassenen Messkandidaten einfrieren und messen.
Konkrete kurze und längere Pläne stehen unter [plans](plans/three-hours.json)
und lassen sich mit `study.py plan` neu erzeugen. Es wurden noch keine Kandidaten
auf Grundlage einer Agentenleistung bevorzugt oder verworfen.
