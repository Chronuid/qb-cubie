<center>

# RBT-Nutzungsmuster

![Cubie](.assets/cubie-logo-written.png)

RBT delegiert eine sprachlich formulierte Prüfregel an einen Reviewer und übergibt dessen `ReviewData` an einen Reporter. Eine Entscheidung bleibt eine Beurteilung unter den jeweiligen Bedingungen. Die [Semantikreferenz](GUIDE_Contract-Semantics.md) grenzt sie von Ausführung und Beweis ab.

---

</center>

## Interaktives Review

Das Standardbeispiel delegiert eine manuelle Prüfregel interaktiv an das Terminal:

```python
from qb_cubie.rbt import RBT


def test_logging_review():
    RBT(
        target="auth_module.py",
        check="Öffne die Datei und prüfe, ob Passwörter im Klartext geloggt werden.",
    ).run()
```

<details>
<summary>Ergebnis</summary>

```text

```
</details>

Dieser Test benötigt die benannte Datei als Prüfmaterial und eine Person, die sie selbst öffnet. Starte ihn mit `pytest -s`, damit der Standardreviewer `HeadlessReviewer()` Terminaleingaben lesen kann. Ohne vorgegebene Antwort fragt dieser synchron nach `y/n` und einem optionalen Bericht. Für eine GUI kann `HumanReviewer` aus `qb_cubie.rbt` ausdrücklich injiziert werden.

`HumanReviewer` beginnt jeden Aufruf ohne Entscheidung und mit leerem Bericht.
Schließen des Fensters ohne Pass-/Fail-Klick ergibt
`ReviewData(passed=False, report={})`. Auch bei Wiederverwendung werden eine
vorherige Freigabe und ein alter Bericht nicht übernommen.

Kernimport, EBT und `HeadlessReviewer` benötigen kein Tk. `HumanReviewer` lädt `tkinter` erst beim Start der GUI. Fehlt `tkinter` oder dessen native Tk-Erweiterung, meldet dieser Aufruf einen `RuntimeError` mit Installationshinweis, beispielsweise auf `python3-tk` unter Linux. Eine verfügbare grafische Umgebung wird zusätzlich benötigt.

Ein String-Target wird unverändert weitergereicht; andere Objekte werden über `__name__` beziehungsweise `str()` bezeichnet. RBT ruft das Target nicht auf, importiert keine Zielmodule und lädt keinen Quelltext. Ohne Target erhält der Reviewer `None`; eine automatische Untersuchung des gesamten Projekts findet nicht statt.

## Eigene automatisierte Reviewer

Dieses vollständige Beispiel prüft eine bewusst eng begrenzte Dateiregel. Es zeigt die Schnittstelle, kein allgemeines Qualitätsurteil:

```python
from pathlib import Path
from qb_cubie.protocols import ReviewData
from qb_cubie.rbt import RBT


class NonEmptyFileReviewer:
    def review(self, target: str | None, check: str) -> ReviewData:
        path = Path(target) if target is not None else None
        passed = path is not None and path.is_file() and path.stat().st_size > 0
        return ReviewData(passed=passed, report={"criterion": check, "target": target})


def test_nonempty_document(tmp_path):
    document = tmp_path / "document.md"
    document.write_text("Ein Beispiel", encoding="utf-8")
    RBT(
        target=str(document),
        check="Die benannte Datei existiert und ist nicht leer.",
        reviewer=NonEmptyFileReviewer(),
    ).run()


if __name__ == "__main__":
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmp_dir:
        test_nonempty_document(Path(tmp_dir))
    print("OK")
```

<details>
<summary>Ergebnis</summary>

```text
OK
```
</details>

Ein LLM-Reviewer wäre ebenfalls eine eigene Implementierung dieses Protokolls. Quellenübergabe, Modellaufruf, Modellversion, Wiederholungen und Bewertungsnachweise muss dieser Adapter selbst regeln. Eine Klasse `AgentReviewer` wird nicht mitgeliefert.

`HeadlessReviewer(answer=True)` beziehungsweise `answer=False` liefert eine vorgegebene Entscheidung für technische Integrationen. Dabei wird keine fachliche Prüfung durchgeführt. CI benötigt einen ausdrücklich ausgewählten Reviewer ohne interaktive Eingabe.

## Reporting und Metadaten

`ReviewData` enthält `passed: bool` und ein offenes `report`-Dictionary. Der Standardreporter formatiert den Bericht und löst bei `passed=False` eine Assertion aus. Ein anderer Reporter kann injiziert werden; `reporter=None` unterdrückt die Ausgabe und Assertion, aber nicht den Review-Aufruf oder dessen Exceptions.

`RBT.run()` liefert derzeit `None`, nicht das `ReviewData`-Objekt. Ein eigener Reporter kann das Paket zur Weiterverarbeitung entgegennehmen. `tags` speichert Metadaten und erzeugt keine pytest-Marken. Das Report-Dictionary ist kein automatisch persistierter, revisionssicherer Bewertungsnachweis.

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
