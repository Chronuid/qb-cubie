# Geprüfte Aufgaben und Aufgabentypen – Version 2

Die IDs bezeichnen konkrete Aufgaben aus dem lokalen, mit swegemma verwendeten
`tasks.jsonl` des Gemma-Developer-Agent-Pools. swegemma ist der Ausführungsrahmen;
diese Herkunft ist keine Zusage, dass die Aufgaben Teil von SWE-bench Verified sind.
Upstream enthält der Pool keine von uns übernommene Aufgabentyp-Taxonomie.
Die folgenden Labels sind unsere eigene fachliche Annotation.

**Prüfumfang:** Aufgabenbeschreibung, Referenzänderung und privater Testpatch für
alle 15 ursprünglichen und 24 weitere Aufgaben, insgesamt 39. Von 129 Aufgaben
bleiben 90 ausdrücklich semantisch ungeprüft. Zum Zeitpunkt dieses Katalogstands
waren die Aufgaben noch nicht technisch zugelassen. Die inzwischen ergänzte
Startpipeline erledigt Snapshotbereinigung und tatsächliche Testzuordnungen je
Studie; die drei Pilotaufgaben wurden damit geprüft. Der aktuelle
[Techniknachweis](VALIDIERUNG.md) dokumentiert die Umgebung und Belege.

Der [vollständige Katalog](candidate-catalog.json) enthält für alle 129 IDs
Quellhashes, Patchpfade und Änderungsumfang. Für die 39 geprüften Aufgaben enthält
er zusätzlich Typ, Änderungsart, Testaufbau, verwandte Aufgaben und Prüfbegründung.
Patchumfang ist ein beobachtetes Strukturmerkmal, keine gemessene Schwierigkeit.
Es wurden weder fachliche Modellläufe noch Lösungserfolge zur Auswahl verwendet.

## Welche Art von Aufgabe erzeugt welche Beobachtungen?

| `task_type` | Inhalt | Erwartbare Belegform |
| --- | --- | --- |
| `parsing_encoding` | Parsing, Normalisierung, Escaping, Zeichen/Bytes | korrelierte Eingabe-/Ausgabepaare, Grenzfälle, Roundtrips, Headerwerte |
| `api_schema` | API-Vertrag, Aliase, HTTP-Metadaten und JSON-Schema | Status/Body, strukturierte JSON-Diffs, Schemas und Aliasfehler |
| `python_protocols` | Deskriptoren, Duck Typing, Hashbarkeit | Proxyobjekte, Fallbacks, Hash-/Attributverhalten, Exceptionfreiheit |
| `terminal_rendering` | Styles, Layout und interaktive Prompts | Text-/ANSI-Ausgaben, Spans, Segmentreihenfolge, In-Memory-Streams |
| `exceptions_diagnostics` | Exceptions, Meldungen und Serialisierung | Typ/Meldung, Notizen, Pickle-Roundtrip, fachliche Fehlerbeobachtung |
| `filesystem_configuration` | Dateien und Umgebungsvariablen | temporäre Konfiguration, Environment-Varianten, Default-/Prioritätsfälle |
| `lifecycle_state` | Ressourcen-, Prozess- und Verbindungslebenszyklen | Zustandsfolgen, Close/Reset-Aufrufe, Exitcodes, lokale Socket-/Prozessbelege |
| `unicode_algorithms` | Grapheme, Zellbreiten und Schnittalgorithmen | Spans, Längeninvarianten, Schnittpositionen, Terminierung |

`change_kind` trennt Bugfix, Feature, Kompatibilität, Diagnostik und gemischte
Änderungen. `test_scope` trennt reine Unit-Tests, In-Process-Integration, lokale
HTTP-Fixtures, Rendering-Snapshots, Dateisystem/Environment, POSIX-Prozesse,
Async-Integration und Versionsmatrizen. So wird eine kleine Lookup-Erweiterung
nicht still als derselbe Aufgabentyp wie eine Prozess- oder Parserreparatur gelesen.
Die Labels beschreiben die Arbeit und Belege, nicht eine vermutete Cubie-Stärke.

`related_group` verhindert beispielsweise, dass die gegensätzlichen historischen
Fixes `requests_6644` und `requests_7315` oder mehrere aufeinander aufbauende
Datei-Wrapper-Fixes als unabhängige Aufgaben in denselben Plan gelangen.
Pilotreservierungen gelten über alle Profilgrößen hinweg. Die alten Pilot-IDs
bleiben auch dann für Messungen gesperrt, wenn sie nun zurückgestellt sind.

## Die 15 ursprünglichen Kandidaten

Fachlicher Kandidat bedeutet ausschließlich: geeignet für die technische
Zulassungsarbeit. Bedingte, zurückgestellte, ausgeschlossene und ungeprüfte
Aufgaben werden vom Katalogplan nicht automatisch gewählt.

### Ursprüngliche Auswahl

| ID | Aufgabentyp / Änderungsart | Status | Prüfung und Grenzen |
| --- | --- | --- | --- |
| `fastapi_13207` | `api_schema` / `bugfix` | fachlicher Kandidat | Computed Fields bei separate_input_output_schemas=False; benötigt passende Pydantic-v2-Version und Prüfung beider Schalterwerte. |
| `fastapi_14479` | `exceptions_diagnostics` / `diagnostics` | fachlicher Kandidat | Unzulässige Query-Typen erhalten konkrete Fehlermeldung; Verhalten der Fehlermeldung getrennt von erfolgreicher Verarbeitung auswerten. |
| `fastapi_15280` | `api_schema` / `feature` | ausgeschlossen | Referenz implementiert bewusst einen Aprilscherz mit FastAPIError statt der angekündigten LLM-Funktion. Issue nennt den erwarteten Scherz nicht. Kein belastbarer funktionaler Sollvertrag. |
| `fastapi_9425` | `api_schema` / `compatibility` | fachlicher Kandidat | Stringannotation None für HTTP 204 ohne Body; klarer Status-/Body-Vertrag, TestClient benötigt keine externe Verbindung. |
| `httpx_3672` | `lifecycle_state` / `mixed` | zurückgestellt | Sieben Produktionsmodule, sync/async Reset, Keepalive und Stream-Schließen. Private Tests ändern hauptsächlich complete zu reset; Server-Schließverhalten unzureichend abgedeckt. Nicht im kurzen Hauptprofil. |
| `requests_6629` | `exceptions_diagnostics` / `bugfix` | bedingt / Klärung nötig | JSONDecodeError nach Pickle-Roundtrip rekonstruierbar machen; privater Test prüft repr-Gleichheit, kein tatsächlicher ProcessPool-Test. Der beschriebene Ausgangsfehler ist ein TypeError beim Pickle-Roundtrip, keine Assertion. Aktuelle Assertion-Rot-Zulassung kann diese Aufgabe so nicht aufnehmen. |
| `requests_6644` | `parsing_encoding` / `bugfix` | fachlicher Kandidat | Führende // im Requestpfad reduzieren. Historisch gegenteiliger Vertrag zu requests_7315; nicht gemeinsam als unabhängige Aufgaben wählen. |
| `requests_6757` | `parsing_encoding` / `compatibility` | zurückgestellt | Referenz unterscheidet urllib3 1.x/2.x und überspringt einen Fall versionsabhängig. Einzelnes Image und Pflicht ohne Skip bilden Versionsmatrix nicht ab. Alter Pilotplatz wird reserviert, nicht als Messaufgabe recycelt. |
| `requests_7309` | `parsing_encoding` / `bugfix` | fachlicher Kandidat | Content-Type-Parameter ohne Gleichheitszeichen ignorieren; enthält Anpassung bestehender Erwartungswerte und einen Encoding-Fallback-Fall. |
| `requests_7502` | `python_protocols` / `bugfix` | fachlicher Kandidat | NamedTemporaryFile/Attributproxy bei Multipart; privater Test benötigt lokalen httpbin-Dienst. Kein Internet nötig, aber Fixture muss im Container verfügbar sein. |
| `rich_2725` | `terminal_rendering` / `bugfix` | fachlicher Kandidat | Vertauschte Mid-/Footer-Boxzeichen; Issue beschreibt Reihenfolge, Testpatch parametrisiert Header/Footer. Keine Bildbewertung nötig. |
| `rich_3296` | `terminal_rendering` / `bugfix` | bedingt / Klärung nötig | Code und Test zeigen Padding mit Hintergrundfarbe; Issue verweist für das Sollbild nur auf Screenshots. Vor Pilot gleiche textuelle Anforderung für beide Agenten festhalten. |
| `rich_3676` | `exceptions_diagnostics` / `feature` | bedingt / Klärung nötig | Exception.__notes__ erfassen und darstellen; Python >=3.11. Privater Test prüft extrahierte Notizen, nicht die gesamte Darstellung. Der private Test greift auf das zuvor fehlende notes-Attribut zu (AttributeError). Das aktuelle Assertion-Rot-Gate reicht für diese Feature-Einführung nicht. |
| `rich_3882` | `terminal_rendering` / `bugfix` | fachlicher Kandidat | Promptfehler müssen Markup trotz global markup=False rendern; Eingabe und Konsolenausgabe im Speicher prüfbar. |
| `rich_3894` | `python_protocols` / `bugfix` | fachlicher Kandidat | Nicht-stringförmiges __qualname__ bei Deskriptoren; privater Test prüft vor allem Absturzfreiheit, nicht sämtliche Fallback-Zweige. |

### 24 zusätzlich geprüfte Aufgaben

| ID | Aufgabentyp / Änderungsart | Status | Prüfung und Grenzen |
| --- | --- | --- | --- |
| `fastapi_13537` | `parsing_encoding` / `bugfix` | fachlicher Kandidat | Leere Formstrings als fehlende optionale Werte behandeln; URL-encoded und Multipart, python-multipart im Image nötig. |
| `fastapi_14258` | `exceptions_diagnostics` / `diagnostics` | bedingt / Klärung nötig | Selbstinklusion eines Routers verhindern und Meldung ausgeben. Ausgangsstand kann RecursionError statt AssertionError erzeugen; aktuelle Assertion-Rot-Zulassung vorher prüfen. |
| `fastapi_14349` | `api_schema` / `bugfix` | fachlicher Kandidat | Feld mit Alias $ref darf nicht als Schema-Referenzstring behandelt werden; benötigt inline_snapshot und passende Pydantic-Konfiguration. |
| `fastapi_14360` | `api_schema` / `bugfix` | fachlicher Kandidat | Query-/Header-/Cookie-Modellaliase und Fehlereingaben; privater Test nutzt dirty_equals und Pydantic-v2-Zweige. |
| `fastapi_14361` | `api_schema` / `bugfix` | fachlicher Kandidat | Fehlenden $ref beim Remapping akzeptieren; Test mit Enum-Union, verwandt mit anderem Pydantic-Remapping-Fix. |
| `fastapi_14372` | `python_protocols` / `mixed` | fachlicher Kandidat | Hashbarkeit von Depends/Security und sichere Aktualisierung eingefrorener Dataclasses; private Tests erfassen nicht alle Mutations- oder Scope-Kombinationen. |
| `fastapi_14786` | `parsing_encoding` / `bugfix` | fachlicher Kandidat | Authorization-Scheme und Token bei zusätzlichen Leerzeichen; klare Eingabe-/Ausgabebeispiele, private Tests über lokalen TestClient. |
| `requests_6589` | `parsing_encoding` / `bugfix` | fachlicher Kandidat | Content-Length für UTF-8-Zeichen statt Zeichenanzahl; verwandt mit requests_6757. Test referenziert httpbin-Fixture, obwohl Request nur vorbereitet wird; urllib3-Version festlegen. |
| `requests_6592` | `api_schema` / `feature` | fachlicher Kandidat | Alias too_early für Status 425; kleiner Lookup-Fall mit Erhalt bisheriger Aliase. Als eigener kleiner Featuretyp ausweisen, nicht mit größeren Reparaturen gleichsetzen. |
| `requests_7205` | `filesystem_configuration` / `compatibility` | fachlicher Kandidat | Leere netrc-Defaults unter Python >=3.11 ignorieren; temporäre Datei und NETRC-Variable, kein echter HTTP-Request. |
| `requests_7315` | `parsing_encoding` / `bugfix` | fachlicher Kandidat | Erhält // für signierte URLs und entfernt Fix aus requests_6644. Gegensätzliche zeitgebundene Sollverträge: eine Aufgabe pro Gruppe. |
| `requests_7427` | `parsing_encoding` / `bugfix` | fachlicher Kandidat | no_proxy soll Domain-Grenzen respektieren; parametrische positive/negative Fälle, Umgebungs-Proxys kontrollieren. |
| `requests_7433` | `python_protocols` / `bugfix` | fachlicher Kandidat | __getattr__-Stream bei 307-Redirect korrekt erkennen und erneut senden; lokale httpbin-Fixture und Redirectverhalten nötig. |
| `requests_7505` | `python_protocols` / `mixed` | fachlicher Kandidat | Folgefix zu requests_7502 zentralisiert has_read und ergänzt Aufrufstellen. Nicht als unabhängige zusätzliche Wrapper-Aufgabe behandeln. |
| `rich_3052` | `terminal_rendering` / `feature` | bedingt / Klärung nötig | case_sensitive=False für Auswahlprompts, bestehendes Defaultverhalten erhalten und originale Auswahl zurückgeben; Feature statt Reparatur kennzeichnen. Der private Test ruft case_sensitive=False vor der Erweiterung direkt auf (TypeError). Das aktuelle Assertion-Rot-Gate akzeptiert dies nicht; vor Aufnahme unabhängige fachliche Rotklassifikation klären. |
| `rich_3063` | `parsing_encoding` / `bugfix` | fachlicher Kandidat | Markup-Escaping für abschließenden Backslash; Roundtrip und Style-Spans im privaten Test. Exaktes ergänzendes Issue aus externem Link lokal nicht vorhanden. |
| `rich_3067` | `parsing_encoding` / `bugfix` | fachlicher Kandidat | Tilde im URL-Highlighter akzeptieren; prüfbare Zeichenpositionen/Spans, weder Browser noch Netzwerk erforderlich. |
| `rich_3278` | `parsing_encoding` / `bugfix` | fachlicher Kandidat | Private ESC-Codes 0..? entfernen; Issue nennt Bereich und Auswirkung, parametrische Konsolenbelege im Speicher möglich. |
| `rich_3468` | `lifecycle_state` / `mixed` | bedingt / Klärung nötig | BrokenPipe behandeln und stdout umleiten; privater Test benötigt python/head und kann mit return ohne Prüfung enden. Fixture-Eignung und Soll-Exitcode vorher klären. |
| `rich_3472` | `python_protocols` / `bugfix` | bedingt / Klärung nötig | Referenz filtert repr-Felder ohne Attribut bei init=False. Lokales Issue enthält nur Titel/Link; Anforderung vor Zulassung textuell vervollständigen. |
| `rich_3521` | `unicode_algorithms` / `bugfix` | bedingt / Klärung nötig | Zellgrenzen in gemischtem CJK-Text; privater Test prüft jede Schnittposition. Lokale Aufgabe nennt Sollverhalten nur über externe Referenz. |
| `rich_3777` | `filesystem_configuration` / `feature` | fachlicher Kandidat | TTY_INTERACTIVE=0/1 und Priorität expliziter Optionen; Testpatch enthält eine Konstruktion ohne anschließende Assertion. Zusätzliche unabhängige Prüfabdeckung nötig. |
| `rich_3953` | `unicode_algorithms` / `bugfix` | bedingt / Klärung nötig | ZWJ-Randfälle und nicht druckbare Zeichen; lokales Issue besteht aus Titel und Links. Sollwerte und Python/Unicode-Versionen vor Zulassung festhalten. |
| `rich_4006` | `unicode_algorithms` / `bugfix` | zurückgestellt | Zero-Width-Zeichen können Endlosschleifen erzeugen; Ausgangsrot kann nur Timeout sein und ist im aktuellen Assertion-Rot-Gate nicht zulassungsfähig. |

## Konsequenzen für kurze und längere Läufe

26 Aufgaben sind im aktuellen Studienpfad fachliche Kandidaten: drei Pilot- und 23 Messkandidaten.
Verwandtschaftsgruppen verkleinern die Zahl unabhängig auswählbarer Aufgaben
zusätzlich. Neun Aufgaben sind bedingt, drei zurückgestellt und eine ausgeschlossen.

Der überarbeitete Pilot verwendet `fastapi_9425`, `rich_3278` und `requests_6589`.
Die beiden zuletzt genannten ersetzen den unvollständig textuell beschriebenen
Screenshot-Fall und die Versionsmatrix des ersten Plans. Das geschieht vor
Modellmessungen. Der [alte Plan](candidate-selection.json) bleibt als überholter
Auswahlstand erhalten.

Für kurze Hauptläufe werden fünf Aufgaben mit je einem Seed und beiden Agenten
geplant. Das Profil für sechs Stunden verwendet unter denselben Agentenbudgets
zehn Aufgaben; beim gleichen Pool ist der Fünferplan dessen Präfix. Erst nach
technischer Zulassung ist der Plan auf dem tatsächlich zugelassenen `tasks.json`
neu zu prüfen und einzufrieren. Falls sich der Pool ändert, darf sich auch die
Auswahl ändern; deshalb enthält jeder Plan den Hash seines Eingabepools.

Beide Profile decken keine Lifecycle- oder Terminierungsaufgaben ab: Die geprüften
Kandidaten dieser Typen erfüllen die aktuellen Zulassungsregeln noch nicht.
Insbesondere ein Timeout als Ausgangsfehler genügt nicht dem bestehenden
Assertion-Rot-Gate. Diese Lücke offen berichten, statt ein beliebiges anderes
Tasklabel zu vergeben. HTTPX benötigt vor einer Aufnahme bessere unabhängige
Prüfabdeckung für die angekündigten Serveränderungen.

Der Bericht erzeugt `by_task_type`, `by_change_kind` und die Zusammensetzung
unter `task_distribution`. Je Gruppe bleiben geplante und auswertbare Läufe,
Erfolge, gepaarte Differenzen, Agentenzeit, gemessene Eingabe-/Ausgabetokens,
Modell-/Werkzeugaufrufe und sichtbare Testbeobachtungen zugänglich. Anzahl der
Aufgaben und Anzahl der Seeds getrennt lesen. Eine einzelne Aufgabe pro Typ
liefert eine Fallbeobachtung, keine statistisch belastbare Typ-Rangliste.

Die Annotationen und private Prüfbegründungen bleiben auf dem Host. Sie werden
nicht als zusätzliche Lösungshinweise in den Modellkontext aufgenommen.

Die konkreten Pläne sind unter [Pilot](plans/pilot.json),
[drei Stunden](plans/three-hours.json) und [sechs Stunden](plans/six-hours.json)
gespeichert. Der Fünferplan enthält fünf Typen; Parsing/Encoding kommt im längeren
Plan hinzu. Wer alle sechs derzeit verfügbaren Typen in einer kurzen Studie
benötigt, wählt mindestens sechs Aufgaben und prüft die zusätzliche Zeit im Plan.
Nach der statischen Prüfung wurden außerdem drei fachlich sinnvolle Fälle
(`rich_3052`, `rich_3676`, `requests_6629`) wegen ihres nicht als Assertion
auftretenden Ausgangsfehlers bedingt eingestuft. Der aktuelle Plan zieht sie nicht.
