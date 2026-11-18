Hi Gemini! Aktuell sehen manche Beispiele in den Docs echt nicht schön aus. Das liegt daran, dass wir vergessen haben etwas für die UX umzusetzen. 

Was ich meine das hier: 

```python
from qb_cubie import EBT, WorldState

trace = EBT(
    target=lambda x: x * 2,
    pre=[WorldState(args=(1,)), WorldState(args=(2,))],
    post=[WorldState(returns=2), WorldState(returns=4)],
    tags={"meta:cross-product-reason": "Prüft bewusst die N:M-Matrix von EBT."},
).run()
print("Evaluation:", trace.evaluation, "| Traces:", len(trace.traces))
```

Das Komma sieht echt nicht schön aus und ich glaube das ist auch nicht notwendig. Bitte schreibe mal ein neues EBT-Testmodul, welches prüft, ob es auch ohne dieses merkwürdige Komma funktioniert. Also, das hier soll funktionieren: 
```python
trace = EBT(
    target=lambda x: x * 2,
    pre=[WorldState(args=(1)), WorldState(args=(2))],
    post=[WorldState(returns=2), WorldState(returns=4)],
    tags={"meta:cross-product-reason": "Prüft bewusst die N:M-Matrix von EBT."},
).run()
print("Evaluation:", trace.evaluation, "| Traces:", len(trace.traces))
```

oder auch: 
```python
trace = EBT(
    target=lambda x: x * 2,
    pre=[WorldState(args=1), WorldState(args=2)],
    post=[WorldState(returns=2), WorldState(returns=4)],
    tags={"meta:cross-product-reason": "Prüft bewusst die N:M-Matrix von EBT."},
).run()
print("Evaluation:", trace.evaluation, "| Traces:", len(trace.traces))
```

Das sähe einfach schöner aus und lässt sicherlich auch besser nutzen. Aber wir müssen aufpassen dass die Rückwärtskompatibilät funktioniert, damit wir die Testsuite nicht komplett umschreiben müssen. Also, bitte schreibe mal ein Testmodul was das alles ermöglicht. Und spiel mal mit der neuen Quantor-Deklarations-Funktion herum, also, nutze das für die Testsuite. 
Die Quantor-Deklarations-Funktion ermöglicht einfach nur zusätzlich das explizite Deklarieren des Quantor-Typs. Also:
```python
EBT(
    target=target_normalize,
    pre={
        "quantor": "all",
        "states": [
            WorldState(args=("TEXT",)),
            WorldState(args=(" text ",)),
        ]
    },
    post={"quantor": "exists", "states": WorldState(returns="text")}
)
```

Spiel mal im neuen Test-Modul damit herum und benutze immer die explizite Deklaration des Quantor-Typs. Sollte hoffentlich funktionieren. Wenn nicht haben wir vorher was falsch gemacht. 