<center>

# EBT-Nutzungsmuster

![Cubie](.assets/cubie-logo-written.png)

Die Beispiele zeigen die vorhandene API. Die [zentrale Semantikreferenz](GUIDE_Contract-Semantics.md) definiert alle Felder, Vergleichsregeln und bekannten Fehler. Verwende für jeden Lauf eine neue EBT-Instanz und explizite, nichtleere Verträge. Die folgenden Python-Blöcke sind vollständige pytest-Beispiele.

---

</center>

## Konkrete Ein-/Ausgabepaare

Zusammengehörige Wertepaare werden durch getrennte Verträge geprüft. `pytest.mark.parametrize` erzeugt dafür einen eigenen Testfall pro Paar:

```python
import pytest
from cubie import EBT, WorldState


def double(value):
    return value * 2


@pytest.mark.parametrize("value, expected", [(1, 2), (2, 4), (-1, -2)])
def test_double(value, expected):
    EBT(
        target=double,
        pre=WorldState(args=(value,)),
        post=WorldState(returns=expected),
    ).run()
```

`args=[1, 2]` bedeutet zwei Positionsargumente. Eine Liste als einzelnes Argument wird mit `args=([1, 2],)` übergeben. `kwargs={"value": 1}` übergibt ein Schlüsselwortargument. `target=double` übergibt die Funktion; `target=double(...)` würde sie bereits vor dem Testlauf ausführen.

## Mehrere Eingänge, ein gemeinsames Muster

```python
from cubie import EBT, WorldState


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
```

Jeder dieser drei Eingänge wird einmal ausgeführt. Ohne Arena laufen die Aufrufe im aufrufenden Prozess und teilen dessen Zustand. Diese Liste begründet keine Aussage über alle anderen Strings.

## Erlaubte und verbotene Ergebnisse

```python
from cubie import EBT, WorldState


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
```

Die beobachtete Ausgabe muss zu mindestens einem positiven und zu keinem negativen Muster passen. Ohne positive Muster werden nur die negativen Muster ausgeschlossen. Ein zusätzliches negatives Muster ist hier zur Veranschaulichung enthalten; die beiden positiven Werte schließen `"ERROR"` bereits aus.

Bei mehreren `pre`- und `post`-Einträgen gilt dieselbe gesamte Zielmenge für jeden Eingang. Ein gemeinsames `post` für die Werte `2` und `4` erlaubt auch eine Vertauschung. Es entsteht keine Zuordnung nach Listenposition.

Das gleiche Prinzip kann einen beobachteten Würfelwert auf den Bereich `1` bis `6` beschränken. Eine konstante Rückgabe innerhalb dieses Bereichs besteht ebenfalls. Alle möglichen Ergebnisse, Zufälligkeit und Verteilung sind damit nicht geprüft.

`EBT(expect=False)` negiert dagegen das Gesamtergebnis. Es prüft keine erwartete Exception; Target-Ausnahmen propagieren weiterhin.

## Rückgabemuster

```python
import re
from typing import Any
from cubie import EBT, WorldState


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
```

Dictionary-Schlüssel müssen exakt übereinstimmen. Reguläre Ausdrücke verwenden `match(str(actual))`, Typmuster `isinstance`. Listen und Tupel werden rekursiv nach Position verglichen und dabei als austauschbar behandelt. `returns=None` erwartet explizit `None`, wie im zweiten Beispiel. Ausgelassenes `returns` oder `returns=cubie.UNSPECIFIED` deaktiviert die Rückgabeprüfung. Diese Post-Prädikate werden beim normalen Arena-Lauf im Elternprozess ausgewertet und erfordern für sich keinen Cloudpickle-Codec.

## Dateitransformation mit expliziter Arena

```python
from pathlib import Path
from cubie import EBT, TempFS, WorldState


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
```

Das Mapping lautet `{relativer_Zielpfad: Hostquelle}`. `pre.fs` kopiert Quellen, `post.fs` vergleicht die angegebenen Pfade. Andere Dateien im Workspace sind in diesem Beispiel nicht Teil der Erwartung. Für einen Vergleich aller Dateien kann `post.fs={".": "fixtures/post"}` mit einem vorhandenen Referenzverzeichnis verwendet werden. Leere Unterverzeichnisse werden rekursiv nicht mitverglichen.

Alternativ sind Sammlungen wie `fs={"fixtures/input.txt"}` erlaubt; sie kopieren hier nach `input.txt`. Ein einzelner String wie `fs="fixtures/input.txt"` wird nicht unterstützt. Gleichnamige Quellen können bei der Normalisierung kollidieren; verwende explizite Mappings. Absolute Zielpfade und `..` werden nicht abgefangen und können außerhalb des Workspace schreiben.

## Dateiinhalte mit einem Prädikat prüfen

```python
import json
from pathlib import Path
from cubie import EBT, TempFS, WorldState


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
```

Das Prädikat erhält einen `Path` im noch bestehenden Workspace. Nach dem Vergleich wird die Arena aufgeräumt. `returns` prüft den Python-Rückgabewert; Konsolenausgaben sind kein `WorldState`-Feld.

## Virtuelle Umgebungen

Für ein vorhandenes, eigens vorbereitetes Basis-Environment kann `arena=PyVenv("tests/.arenas/qa_env")` verwendet werden. Die Umgebung muss zur Maschine passen; die eingecheckte Basis ist kein portabler Installationsvertrag. `PyVenv` kann fehlende Codec-Abhängigkeiten in der Basis nachinstallieren.

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
