# Benchmark-Betrieb und Nachbewertung

Stand: 11. November 2026.

## Nachbewertung

`apply_adjudication(archive_path, decisions_path, destination)` aus
`qb_cubie.benchmarks` veröffentlicht ein neues, separat prüfbares Archiv.
Das Ursprungsarchiv bleibt unverändert. Die Entscheidung muss folgende Form haben:

```json
{
  "schema_version": 1,
  "manifest_sha256": "SHA-256 des Ursprungsmanifests",
  "evaluator_id": "Name und Konfiguration des Bewertungsverfahrens",
  "version": "1",
  "runs": {
    "RUN-ID": {
      "evaluation_sha256": "SHA-256 von episodes/.../review-evaluation.json",
      "reason": "Begründete Bewertung von Mechanismus und Auswirkung",
      "matches": [0, null, 0]
    }
  }
}
```

`matches` enthält für jedes Finding der Originalantwort den nullbasierten Index
seines Referenzfehlers oder `null` für einen unbestätigten Befund. Mehrfachnennungen
desselben Referenzfehlers erhöhen Trefferzahl und Recall nicht. Kriterienkennung,
Pfad und Symbol müssen übereinstimmen. Mechanismus und Auswirkung beurteilt das
angegebene Verfahren; der Import selbst ist kein semantischer Evaluator.
Neue plausible Fehler erfordern zuerst eine versionierte Referenzkorrektur und
die Neubewertung aller davon betroffenen Antworten. Nicht importierte Läufe
behalten ihren Bewertungsstand. Unvollständige Zuordnungen werden nicht importiert.

Die Bewertung soll Modell und Bedingung nicht kennen; Zuordnungen können
automatisch oder optional menschlich erstellt werden. Die ursprünglichen
Antworten und Bewertungsbelege bleiben erhalten. `adjudication.json` bindet den
neuen Stand an die ursprünglichen Bytes; `adjudication-parent.json` erhält
ursprüngliches Manifest und Ergebnis. `results.json`, Bericht und Gates werden
neu berechnet. `evaluate_gates`, `summarize_pilot` und Archivprüfung können das
abgeleitete Archiv wie andere Ergebnisarchive lesen. In einer Auswertung darf
nur ein Bewertungsstand desselben Versuchs verwendet werden.

## Erwartetes Stub-Rot

Eine Developer-Referenz kann `expected_red_exception` mit `module` und `message`
deklarieren. `module` muss dem Produktionsmodul `submission_module` entsprechen
und im sichtbaren Material vorhanden sein. Nur in der Rotphase gilt eine
`NotImplementedError` mit exakt dieser Meldung und abschließendem Traceback im
benannten Produktionsmodul als fachlicher Fehlschlag. Setup-/Importfehler,
andere Exceptions und derselbe Stub in Grün bleiben Fehler. Die initialen
Stub-Aufgaben im Basisdatensatz enthalten diese Deklaration. Das öffentliche
Prozessergebnis nennt fachliches Rot weiterhin `assertion_failure`.

## Laufprovenienz

Freeze und Ergebnismanifest erfassen Repository-Commit und Dirty-Status getrennt,
einen Hash aus Git-Status und versioniertem Diff sowie den Hash einer gefundenen
`uv.lock`, `poetry.lock` oder `requirements.lock`. Ohne Checkout bleiben diese
Angaben unbekannt. Der Diffhash enthält keine Inhalte unversionierter Dateien;
Szenario-, Adapter- und Quellhashes binden das tatsächlich verwendete Material.
Zusätzlich wird ein Hash der installierten Distributionsnamen und Versionen
erfasst und bei eingefrorenen Läufen geprüft. Das ist kein vollständiger Hash
aller Abhängigkeitsdateien. Eine gefundene Lockdatei belegt noch keine Installation
gemäß Lock; deshalb bleibt `dependency_lock_verified=false`. Ein Image-Digest
bleibt ohne implementierten Container-Runner unbekannt.

## Konfiguration und Episodenumfang

Der aktuelle Umfang verwendet Konfigurationsdateien für Auswahl und Budgets.
Es gibt keine zusätzlichen CLI-Overrides. Vor einem Lauf wird die endgültige
Set-Datei geplant und eingefroren. Szenariowerte überschreiben Set-Budgets;
globale harte Grenzen bleiben bindend. Ein Inkrement mit eingefrorenen Tests je
Episode bleibt die implementierte Grenze. Mehrere Inkremente und fachlich
begründete Testrevisionen sind noch nicht implementiert.

## Abbruch und Wiederholung

1. Vor dem ersten Modellaufruf ein Studienjournal außerhalb der temporären
   Arbeitsverzeichnisse anlegen. Studienkennung, geplante Zellen, Versuchskennung,
   Startzeit und Zielpfade für Runner- und Adapterarchive erfassen.
2. Nach einem Abbruch Fragmente unverändert sichern und als `interrupted_unsealed`
   kennzeichnen. Ein Fragment ohne gültiges Manifest ist kein vollständig
   prüfbares Runnerarchiv und darf nicht in die Pilotfreigabe importiert werden.
3. Lokale Prozessbäume beenden. Bei HTTP-Abbruch über den Provider prüfen, ob die
   Inferenz beendet ist. Ohne Nachweis keinen überlappenden Ersatzversuch starten.
4. Eine Wiederholung erhält eine neue Versuchskennung und den Verweis
   `retry_of` auf den ursprünglichen Versuch sowie einen Grund. Sie überschreibt
   weder Fragmente noch gültige Archive. Ein Journal mit zusätzlichen gestarteten
   Versuchen erfüllt das strikte Zwei-/Fünf-Protokoll nicht automatisch; dazu ein
   neues Studiendesign mit vollständig ausgewiesenen Versuchen festlegen.
5. Vor Auswertung Journal gegen alle Runner- und Adapterarchive abgleichen.
   Fehlende Belege und nicht gestartete Zellen ausweisen. Die vorhandene
   Pilotfreigabe prüft nur übergebene Archive, nicht dieses externe Journal.

## Belegaufbewahrung

Für weiter verwendete Ergebnisse gilt als lokale Standardregel:

- Primärablage unter `artifacts/benchmarks/STUDIENKENNUNG/` außerhalb von `/tmp`;
  Runnerarchive, Adapterarchive, Messbundles, Journal und Entscheidungen gemeinsam.
- Nur ausführende Person bzw. CI-Dienst dürfen schreiben. Bewertende erhalten
  Lesezugriff; private Referenzen und zurückgehaltene Aufgaben bleiben separat
  zugriffsbeschränkt. Zugangsdaten gehören nicht in Belege.
- Nach Abschluss eine zweite, getrennte Ablage mit unveränderlichen Archivkopien
  und SHA-256-Inventar erzeugen. Studienverantwortliche dokumentieren Ziel und Datum.
- Vor Ergebnisverwendung die Kopie in ein frisches Verzeichnis wiederherstellen,
  Inventar und `read_archive` prüfen; Datum und Ergebnis im Journal festhalten.
- Belege mindestens zwölf Monate nach letzter Ergebnisverwendung behalten;
  projektspezifisch längere Vorgaben gehen vor. Löschung ist eine separate
  bewusste Entscheidung und kein automatischer Teil eines Messlaufs.

Diese Regeln sind festgelegt, aber keine Behauptung über bereits erfolgte
Sicherungen, externe Zugriffsrechte oder Wiederherstellung alter `/tmp`-Belege.

## Noch benötigte praktische Nachweise

Für reale Pilotmessungen sind ein erreichbarer Provider, eine festgelegte
Agentenkonfiguration, kontrollierte serielle Laufbedingungen und ein geeignetes
Basisdatensatz-Set nötig. Vorläufige Laufzeiten aus parallelen Tests sind keine
Vergleichsmessungen. Zahl unabhängiger Projekte anhand der Pilotstreuung planen;
Wiederholungen ersetzen keine Projekte. Wartbarkeit, offene Bewertungen,
Fehler, Enthaltungen und unbekannte Kosten getrennt ausweisen.

CI-Betrieb benötigt einen tatsächlichen Lauf in der Ziel-CI mit Providerzugriff,
Gatefehler und wiederherstellbaren Artefakten. Ein externer Nutzertest benötigt
eine tatsächlich unvorbereitete Person. Zurückgehaltene Aufgaben benötigen eine
kontrollierte private Herkunft und dürfen nicht durch Umbenennen öffentlicher
Aufgaben entstehen. Diese Nachweise sowie Containerisolation bleiben offen.
