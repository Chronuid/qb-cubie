# 📖 CUBIE-GUIDE: RBT Usage-Patterns

> **Hinweise:**
> * Die folgenden Usage-Patterns definieren die architektonischen Verträge und die Developer-Experience (DX) für das Review-Based-Testing.
> * Auch wenn die interne Engine diese Flexibilität durch injizierbare Abhängigkeiten und das `ReviewData`-Datenpaket abbildet, bleibt das Interface nach außen für den Entwickler radikal simpel.

---

## 1. Das Fundament: Human-in-the-Loop

In seiner reinsten Form ist RBT für das manuelle Bootstrapping und interaktive Testing konzipiert. Der Entwickler vor dem Terminal agiert als primärer Reviewer.

### 1.1. Explizites Target & binäre Entscheidung

Das klassische RBT-Muster benötigt eine Prüfregel (`check`) und optional ein Ziel (`target`). 

```python
def test_01():
    RBT(
        target="rbt.py:RBT", 
        #reviewer=HumanReviewer() #impliziter Fallback zum HumanReviewer, wenn nichts angegeben ist.
        check="""
            Das Terminal mit dem Testlauf pausiert, wartet geduldig auf deine Eingabe 
            und du bekommst das deklarierte Test-Ziel 'rbt.py:RBT' mitsamt diesem Test angezeigt.
                
            Du kannst diesen Test als 'Bestanden (y)' oder 'Fehlgeschlagen (n)' deklarieren.
            """
    ).run()
```
* **Target-Darstellung:** Wenn `target` als String (`"rbt.py:RBT"`) übergeben wird, zeigt das Terminal diesen exakt so an. Werden stattdessen direkte Python-Objekte (Klassen, Funktionen) übergeben, evaluiert die Engine diese unter der Haube und präsentiert dem Reviewer automatisch deren String-Repräsentation (Namen).
* **Ausführungs-Lebenszyklus:** Das Framework pfuscht nicht im Capturing von Pytest herum. Wenn ein RBT-Knoten erreicht wird, ruft der Test den HumanReviewer auf und blockiert einfach (wartet synchron).

### 1.2. Implizites Target & Optionale Reports

Targets sind nicht zwingend erforderlich. Wenn kein Target definiert wird, bezieht sich die Prüfregel implizit auf das gesamte Projekt, den aktuellen Zustand oder den logischen Kontext.

```python
def test_02():
    RBT(check="Du hast die Möglichkeit einen schriftlichen Bericht mitzugeben.").run()
```
* **Die Report-Struktur (`ReviewData`):** Nach der binären Entscheidung (Passed/Failed) öffnet sich die Möglichkeit für einen schriftlichen Bericht. Dieser Text landet in dem offenen `report`-Dictionary der zugrundeliegenden `ReviewData`-Klasse.

### 1.3. Nahtlose Pytest-Integration

Das RBT bricht nicht aus dem etablierten Ökosystem aus. Alles, was der Reviewer entscheidet, wird formell an Pytest übergeben.

```python
def test_03():
    RBT(target="rbt.py:RBT", 
        check="Nachdem du 'test_01' ausgeführt hast, wurden deine Eingaben wie erwartet im Pytest-Report wiedergegeben."
    ).run()

def test_04():
    RBT(target="rbt.py:RBT", 
        check="Nachdem 'test_02' lief, wurde dein Bericht wie erwartet im Pytest-Report wiedergegeben."
    ).run()
```
* **Der Vertrag:** Die `RBT`-Engine leitet das `ReviewData`-Paket (bestehend aus `passed: bool` und dem `report: dict`) nahtlos als PyTest-Report weiter.

---

## 2. Dependency Injection: Erweiterbarkeit & Automatisierung

Die `RBT`-Engine weiß nicht, *wer* die Prüfung durchführt – sie erwartet am Ende lediglich ein gültiges `ReviewData`-Objekt.

### 2.1. Automatisierte Reviewer (Agents)

Die menschliche Interaktion kann jederzeit durch maschinelle Reviewer ersetzt werden, indem diese als Attribut injiziert werden.

```python
def test_05():
    RBT(
        target="rbt.py:RBT",
        reviewer=AgentReviewer("gemma3-12b"),
        check="Hinterlasse im Report ein kleines Gedicht und deklariere diesen Test als Bestanden (y)."
    ).run()
```
* **Schnittstelle:** Die Klasse `AgentReviewer` kapselt den gesamten LLM-API-Aufruf, wertet den `check` aus und generiert selbstständig das `ReviewData`-Objekt. Der Test läuft vollautomatisiert durch.

### 2.2. Custom Workflows & Payload-Kontrolle

Da das `report`-Attribut des `ReviewData`-Objekts ein offenes Dictionary ist, können injizierte Reviewer völlig eigene Workflows ausführen und beliebige Metadaten an den Testlauf heften.

```python
def test_06():
    RBT(
        target="rbt.py:RBT",
        reviewer=CustomReport(), 
        check="Übergebe ein zusätzliches Signaturen-Feld mit deinem Namen im Payload vom Report."
    ).run()
```
* **Payload-Erweiterung:** Eine `CustomReport`-Klasse kann den `report`-Payload beliebig anreichern (z. B. `{"text": "Alles top", "signature": "Chronuid", "tokens_used": 150}`). Das Framework leitet diese unstrukturierten Daten einfach als Pytest-Report durch, ohne sich an der Struktur zu stören.

---

## 3. Exploratives Testen & Metadaten

Das RBT ist prädestiniert für qualitative und subjektive Anforderungen, die sich der deterministischen Logik (EBT/PBT) entziehen.

### 3.1. Subjektive Checks & Tagging

Durch das 'tags'-Attribut können weiterführende Mechanismen sauber angedockt werden, während die internen Tags elegant von den Pytest-Marken differenzierbar bleiben, was für zukünftig geplante Plugins und Utilities entscheidend ist.

```python
def test_07():
    RBT(
        target="rbt.py:RBT",
        check="Ist die UX sauber? Falls nein, bitte erkläre im Bericht, was man anpassen könnte, um die UX zu verbessern.",
        tags=["exploration"]
    ).run()
```
