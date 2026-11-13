<center>

# EBT-Nutzungsmuster

![Cubie](.assets/cubie-logo-written.png)

Die Beispiele zeigen die vorhandene API. Die [zentrale Semantikreferenz](GUIDE_Contract-Semantics.md) definiert alle Felder, Vergleichsregeln und bekannten Fehler. Verwende explizite, nichtleere Verträge. Eine EBT-Instanz kann nacheinander mehrfach ausgeführt werden; jeder Lauf erzeugt eine eigene Ergebnis-Momentaufnahme. Die folgenden Python-Blöcke sind vollständige pytest-Beispiele.

---

</center>

## Konkrete Ein-/Ausgabepaare

Zusammengehörige Wertepaare werden durch getrennte Verträge geprüft. `pytest.mark.parametrize` erzeugt dafür einen eigenen Testfall pro Paar:

```python
import pytest
from qb_cubie import EBT, WorldState


def double(value):
    return value * 2


@pytest.mark.parametrize("value, expected", [(1, 2), (2, 4), (-1, -2)])
def test_double(value, expected):
    EBT(
        target=double,
        pre=WorldState(args=(value,)),
        post=WorldState(returns=expected),
    ).run()


if __name__ == "__main__":
    for val, exp in [(1, 2), (2, 4), (-1, -2)]:
        test_double(val, exp)
    print("OK")
```

<details>
<summary>Ergebnis</summary>

```text
OK
```
</details>

`args=[1, 2]` bedeutet zwei Positionsargumente. Eine Liste als einzelnes Argument wird mit `args=([1, 2],)` übergeben. `kwargs={"value": 1}` übergibt ein Schlüsselwortargument. `target=double` übergibt die Funktion; `target=double(...)` würde sie bereits vor dem Testlauf ausführen.

## Mehrere Eingänge, ein gemeinsames Muster

Mehrere Eingänge in `pre` prüfen gemeinsam dasselbe erwartete Muster in `post`:

```python
from qb_cubie import EBT, WorldState


def normalize(text):
    return text.strip().lower()


def test_normalize():
    EBT(
        target=normalize,
        pre=[
            WorldState(args=" TEXT "),
            WorldState(args="text"),
            WorldState(args="TeXt"),
        ],
        post=WorldState(returns="text"),
    ).run()


if __name__ == "__main__":
    test_normalize()
    print("OK")
```

<details>
<summary>Ergebnis</summary>

```text
OK
```
</details>

Jeder dieser drei Eingänge wird einmal ausgeführt. Ohne Arena laufen die Aufrufe im aufrufenden Prozess und teilen dessen Zustand. Diese Liste begründet keine Aussage über alle anderen Strings.

## Parallelität begrenzen

Mit `multiprocessing=True` und `max_workers` wird die Anzahl paralleler Worker begrenzt:

```python
from qb_cubie import EBT, WorldState


def normalize_parallel(text):
    return text.strip().lower()


def test_normalize_parallel():
    EBT(
        target=normalize_parallel,
        pre=[WorldState(args=(text,)) for text in [" TEXT ", "text", "TeXt"]],
        post=WorldState(returns=lambda value: value == "text"),
        multiprocessing=True,
        max_workers=2,
    ).run()


if __name__ == "__main__":
    test_normalize_parallel()
    print("OK")
```

<details>
<summary>Ergebnis</summary>

```text
OK
```
</details>

Pickle und Loky verwenden hier höchstens zwei Worker, zusätzlich begrenzt durch die gemeldeten CPUs und die Anzahl der Eingänge. Ohne `max_workers` oder mit `None` gelten nur CPU- und Aufgabengrenze. `max_workers` muss eine positive Ganzzahl sein; `True` und `False` sind nicht zulässig. Bei unbekannter CPU-Zahl wird ein Worker verwendet. Ein Worker führt die Aufgaben weiterhin im Kindprozess aus. Die Grenze gilt je EBT-Instanz; bei pytest-xdist können mehrere solcher Pools gleichzeitig laufen. Bei `multiprocessing=False` wird kein Pool angelegt.

Target-Ausnahmen werden ohne Backendwechsel weitergegeben. Nur geeignete
Infrastrukturfehler erlauben einen Fallback auf ein weiteres geeignetes Backend.
Dabei kann die **gesamte Eingangsliste erneut laufen**, einschließlich bereits
ausgeführter Aufgaben. Die Warnung weist auf mögliche doppelte Seiteneffekte hin;
Datei-, Netzwerk- und Datenbankoperationen werden nicht zurückgerollt. Das
Workerlimit gilt auch im Ersatzbackend. Fehler beim Aufräumen oder bei der
Konfiguration lösen keine Wiederholung aus. Die genaue Fehlerklassifikation und
den Vertrag für eigene Backends beschreibt das
[Multiprocessing-Handbuch](dev/DEV-GUIDE_2-4_Multiprocessors.md#fehlerherkunft-und-wiederholungssemantik).

## Erlaubte und verbotene Ergebnisse

Über `expect=False` lassen sich einzelne Rückgabewerte explizit als unerwünscht ausschließen:

```python
from qb_cubie import EBT, WorldState


def choose_status():
    return "OK"


def test_status():
    EBT(
        target=choose_status,
        post=[
            WorldState(returns="OK"),
            WorldState(returns="WARN"),
            WorldState(returns="ERROR", expect=False),
        ],
    ).run()


if __name__ == "__main__":
    test_status()
    print("OK")
```

<details>
<summary>Ergebnis</summary>

```text
OK
```
</details>

Die beobachtete Ausgabe muss zu mindestens einem positiven und zu keinem negativen Muster passen. Ohne positive Muster werden nur die negativen Muster ausgeschlossen. Ein zusätzliches negatives Muster ist hier zur Veranschaulichung enthalten; die beiden positiven Werte schließen `"ERROR"` bereits aus.

Bei mehreren `pre`- und `post`-Einträgen gilt dieselbe gesamte Zielmenge für jeden Eingang. Ein gemeinsames `post` für die Werte `2` und `4` erlaubt auch eine Vertauschung. Es entsteht keine Zuordnung nach Listenposition.

Das gleiche Prinzip kann einen beobachteten Würfelwert auf den Bereich `1` bis `6` beschränken. Eine konstante Rückgabe innerhalb dieses Bereichs besteht ebenfalls. Alle möglichen Ergebnisse, Zufälligkeit und Verteilung sind damit nicht geprüft.

`EBT(expect=False)` negiert dagegen das Gesamtergebnis. Es prüft keine erwartete Exception; Target-Ausnahmen propagieren weiterhin.

## Rückgabemuster

Strukturierte Rückgaben lassen sich deklarativ mit regulären Ausdrücken, Typen und `None` prüfen:

```python
import re
from typing import Any
from qb_cubie import EBT, WorldState


def payload():
    return {"task_id": "REQ-1234", "duration": 0.5, "next_page": None, "metadata": {}}


def test_payload():
    EBT(
        target=payload,
        post=WorldState(returns={
            "task_id": re.compile(r"^REQ-\d{4}$"),
            "duration": float,
            "next_page": str | None,
            "metadata": Any,
        }),
    ).run()


def test_none_return():
    EBT(
        target=lambda: None,
        post=WorldState(returns=None),
    ).run()


if __name__ == "__main__":
    test_payload()
    test_none_return()
    print("OK")
```

<details>
<summary>Ergebnis</summary>

```text
OK
```
</details>

Dictionary-Schlüssel müssen exakt übereinstimmen. Reguläre Ausdrücke verwenden `match(str(actual))`, Typmuster `isinstance`. Listen und Tupel werden rekursiv nach Position verglichen und dabei als austauschbar behandelt. `returns=None` erwartet explizit `None`, wie im zweiten Beispiel. Ausgelassenes `returns` oder `returns=qb_cubie.UNSPECIFIED` deaktiviert die Rückgabeprüfung. Diese Post-Prädikate werden beim normalen Arena-Lauf im Elternprozess ausgewertet und erfordern für sich keinen Cloudpickle-Codec.

## Dateitransformation mit expliziter Arena

Für Datei-Workflows hydriert `TempFS()` deklarierte Quelldateien in einen isolierten Workspace und vergleicht das Ergebnis:

```python
from pathlib import Path
from qb_cubie import EBT, TempFS, WorldState


def uppercase_file():
    text = Path("input.txt").read_text(encoding="utf-8")
    Path("output.txt").write_text(text.upper(), encoding="utf-8")


def test_uppercase_file(tmp_path):
    source = tmp_path / "source.txt"
    expected = tmp_path / "expected.txt"
    source.write_text("hallo", encoding="utf-8")
    expected.write_text("HALLO", encoding="utf-8")

    EBT(
        target=uppercase_file,
        arena=TempFS(),
        pre=WorldState(fs={"input.txt": str(source)}),
        post=WorldState(fs={"output.txt": str(expected)}),
    ).run()


if __name__ == "__main__":
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmp_dir:
        test_uppercase_file(Path(tmp_dir))
    print("OK")
```

<details>
<summary>Ergebnis</summary>

```text
OK
```
</details>

Das Mapping lautet `{relativer_Zielpfad: Hostquelle}`. `pre.fs` kopiert Quellen, `post.fs` vergleicht die angegebenen Pfade. Andere Dateien im Workspace sind in diesem Beispiel nicht Teil der Erwartung. Für einen Vergleich aller Dateien kann `post.fs={".": "fixtures/post"}` mit einem vorhandenen Referenzverzeichnis verwendet werden. Leere Unterverzeichnisse werden rekursiv nicht mitverglichen.

Alternativ sind Sammlungen wie `fs={"fixtures/input.txt"}` erlaubt; sie kopieren hier nach `input.txt`. Ein einzelner String wie `fs="fixtures/input.txt"` wird nicht unterstützt. Gleichnamige Quellen können bei der Normalisierung kollidieren; verwende explizite Mappings. Absolute Zielpfade und `..` werden nicht abgefangen und können außerhalb des Workspace schreiben.

## Dateiinhalte mit einem Prädikat prüfen

Anstelle einer statischen Referenzdatei kann `post.fs` eine Prüffunktion übergeben werden:

```python
import json
from pathlib import Path
from qb_cubie import EBT, TempFS, WorldState


def create_report():
    Path("report.json").write_text(json.dumps({"duration": 0.5}), encoding="utf-8")


def valid_report(path: Path) -> bool:
    return path.is_file() and isinstance(
        json.loads(path.read_text(encoding="utf-8")).get("duration"), float
    )


def test_report():
    EBT(
        target=create_report,
        arena=TempFS(),
        post=WorldState(fs={"report.json": valid_report}),
    ).run()


if __name__ == "__main__":
    test_report()
    print("OK")
```

<details>
<summary>Ergebnis</summary>

```text
OK
```
</details>

Das Prädikat erhält einen `Path` im noch bestehenden Workspace. Nach dem Vergleich wird die Arena aufgeräumt. `returns` prüft den Python-Rückgabewert; Konsolenausgaben sind kein `WorldState`-Feld.

## Erwartete Ausnahmen und persistente Berichte

Mit `ExceptionExpectation` und `JsonReporter` lassen sich erwartete Fehler dokumentieren und als JSON-Bericht sichern:

```python
import json
from qb_cubie import EBT, ExceptionExpectation, JsonReporter, PytestReporter, WorldState


def reject_order():
    raise ValueError("invalid order: 17")


def test_rejected_order(tmp_path):
    report_path = tmp_path / "acceptance.json"
    result = EBT(
        target=reject_order,
        post=WorldState(
            raises=ExceptionExpectation(ValueError, match=r"^invalid order: \d+$"),
        ),
        reporter=JsonReporter(report_path),
    ).run()
    PytestReporter().report(result)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == 1
    assert report["evaluation"] is True


if __name__ == "__main__":
    from pathlib import Path
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmp_dir:
        test_rejected_order(Path(tmp_dir))
    print("OK")
```

<details>
<summary>Ergebnis</summary>

```text
OK
```
</details>

Typ und Meldung der Ausnahme müssen passen. `returns` und `raises` im selben
Post-Zustand sind ungültig; alternative normale Rückgaben und Exceptions werden
als getrennte Post-Zustände angegeben. `fs` darf mit einer Ausnahmeerwartung
kombiniert werden. Infrastrukturfehler bleiben Ausführungsabbrüche.

`JsonReporter` schreibt auch fehlgeschlagene abgeschlossene Läufe und erhebt
selbst keine Assertion. Deshalb erfolgt die pytest-Abnahme im Beispiel nach der
Persistierung. Bereits ermittelte Diffs können auch nach Arena-Teardown gespeichert
werden. Getrennte Berichtspfade bewahren unterschiedliche Läufe. Details zum
Format und zu entfernten Exceptions stehen in der
[Vertragsreferenz](GUIDE_Contract-Semantics.md).

## Virtuelle Umgebungen

Für ein vorhandenes, eigens vorbereitetes Basis-Environment kann `arena=PyVenv("tests/.arenas/qa_env")` verwendet werden. Die Umgebung muss zur Maschine passen und wird lokal provisioniert. `PyVenv` prüft die Codec-Abhängigkeiten ohne Installation; fehlende Pakete müssen vorher ausdrücklich mit dem `ArenaBuilder` installiert werden. Das [Arena-Handbuch](GUIDE_Arena-Management.md#provisionierung-der-testbasen) beschreibt den Vorbereitungsschritt für die Repository-Tests.

Eine erwartete Umgebungsänderung lässt sich über `post=WorldState(arena="tests/.arenas/expected_env")` gegen einen vorhandenen Vergleichspfad prüfen. Das ist ein gefilterter Dateivergleich, kein Beleg korrekter Paketauflösung. Näheres erläutert das [Arena-Handbuch](GUIDE_Arena-Management.md). Beide vorhandenen Arenen führen nur vertrauenswürdigen Code aus und bilden keine OS-Sicherheitsgrenze.

---

---

<center>

![Error while trying to load the image](.assets/cubie-small.png)

## Dokumentation

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](./GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](./GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](./GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](./GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](./GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](./GUIDE_Linter.md)  

[↦ | Entwicklerübersicht EBT | ↤](./dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>
/