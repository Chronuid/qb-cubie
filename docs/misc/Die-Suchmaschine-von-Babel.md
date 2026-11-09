<center>

# Die Suchmaschine von Babel: eine Metapher

![Cubie](../.assets/cubie-logo-written.png)

**Status: konzeptioneller Essay.** Cubie enthält weder eine Suchmaschine für Programme noch einen Codegenerator. Den implementierten Vertrag beschreibt die [Semantikreferenz](../GUIDE_Contract-Semantics.md).

---

</center>

Die Bibliothek von Babel ist ein Bild für die Vielzahl möglicher Texte. Übertragen auf Software kann man sich alle Zeichenketten `Σ*` vorstellen, darunter auch syntaktisch gültige Programme. Tests ähneln in dieser Metapher einer Anfrage: Sie formulieren Kriterien, anhand derer ein konkret vorgelegtes Programm geprüft werden kann.

Cubie enumeriert diese Zeichenketten nicht und berechnet keine Treffermenge. Es führt die angegebenen Targets für konkrete Eingänge aus oder übergibt Kriterien an einen Reviewer. Ein erfolgreicher Lauf dokumentiert nur das beobachtete Verhalten unter diesen Bedingungen.

## Eine Anfrage schärfen

Der Fall `2 → 4` passt sowohl zu einer Verdopplung als auch zur konstanten Rückgabe `4`. Ein getrennt geprüfter Fall `3 → 6` widerlegt die konstante Funktion. Auch danach können Programme beide Fälle erfüllen und bei anderen Eingaben falsch liegen. Zusätzliche Beispiele schließen bestimmte bekannte Fehler aus, erzwingen aber keine bestimmte Abstraktion.

Der frühere Ausdruck „orthogonale Datenpunkte“ war als Bild für vielfältige Beispiele gemeint. Ohne ein definiertes Merkmalsmodell und einen Nachweis unabhängiger Dimensionen liegt keine mathematische Orthogonalität vor. Randfälle und unterschiedliche Anforderungen sind die treffenderen Begriffe.

## Weitere Kriterien

Linter und Reviews können zusätzliche Anforderungen prüfen. Ihr Bestehen macht aus der beobachteten Auswahl keine Menge bewiesener Lösungen. Ein Review hängt vom verfügbaren Material und vom Reviewer ab; ein Linter von Regeln, Konfiguration und Analysegrenzen. Auch die Testdaten und der Prüfkern können Fehler enthalten.

Die Metapher motiviert sorgfältige Spezifikation. Sie verspricht keine vollständige Suche, universelle Korrektheit oder Garantie, dass fehlerhafter Code die Prüfungen nicht bestehen kann.

---

---

<center>

![Error while trying to load the image](../.assets/cubie-small.png)

## Dokumentation

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](../GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](../GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](../GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](../GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](../GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](../GUIDE_Linter.md)  

[↦ | Entwicklerübersicht EBT | ↤](../dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>
