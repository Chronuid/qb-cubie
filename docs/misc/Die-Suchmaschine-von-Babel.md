> PRÄAMBEL: Der Irrtum der Personifizierung Der größte theoretische Fehler in der Analyse von Systemarchitekturen ist die naive Personifizierung. Es gibt hier keinen "faulen Code", keinen "faulen Agenten" und keine Maschine, die aus Bequemlichkeit den "Weg des geringsten Widerstands" wählt. Wer in diesen psychologischen Kategorien denkt, hat die mathematische Realität der Unterspezifikation nicht verstanden.
> 
> Dieses Dokument verbietet jegliche Personifizierung und betrachtet die Problematik ausschließlich durch die Linse der Mengenlehre im unendlichen Raum. Die Bibliothek von Babel hat keine Intention. Eine Suchanfrage liefert nicht eine falsche Antwort, sondern eine gigantische Menge an Treffern. Unterspezifikation ist keine Faulheit, sondern ein rein mathematisches Filter-Problem: Die zurückgegebene Schnittmenge ist schlichtweg zu groß.

## Die Suchmaschine von Babel: Programmverifikation im Raum $\Sigma^*$

In der strukturellen Qualitätssicherung existiert das Konzept der Code-Erstellung nicht. Wir betrachten den Code als etwas, das bereits physisch vorliegt. Der unendliche Suchraum aller denkbaren Zeichenketten und Algorithmen ($\Sigma^*$) entspricht exakt Jorge Luis Borges' Bibliothek von Babel. Jedes mögliche Programm, jede perfekte Logik-Kette, aber auch jedes absolute Rauschen ist in dieser Bibliothek bereits vorhanden.

Das Framework Cubie schreibt keine Algorithmen. Es fungiert als die deterministische Suchmaschine für diese unendliche Bibliothek.

### Die Testsuite als Suchanfrage

Um das exakt richtige Programmsegment ($S$) in der Bibliothek zu finden, nutzen wir das Example-Based-Testing (EBT). Eine EBT-Instanz definiert über ihre spezifischen Attribute pre und post die absolut harten Koordinaten der Suche. Sie formen das klassische Lehrbuch-Format des Hoare-Tripels: $\{P\} S \{Q\}$.

Diese strukturelle Vorgabe ist unsere Suchanfrage. Die Suchmaschine durchkämmt die Bibliothek und liefert uns eine Treffermenge. Diese Lösungsmenge definieren wir als:

$$\mathcal{S}_{\text{summ}} = \{ S \in \Sigma^* \mid S: P \to Q \}$$

### Das Problem der Unterspezifikation (Zu viele Treffer)

Das fundamentale Problem der Unterspezifikation resultiert direkt aus der Natur einer Suchmaschine. Wenn wir eine Suchanfrage mit nur einer einzigen, simplen EBT-Instanz formulieren (z. B. Input 2 $\to$ Output 4), ist unsere Abfrage zu schwach.

Die Bibliothek liefert uns daraufhin Milliarden von Treffern zurück. Innerhalb dieser massiven Treffermenge befinden sich unzählige triviale und unsinnige Bücher (wie return 4), die rein technisch auf diese schwache Suchanfrage passen. Ein einzelnes EBT-Paar beweist also nicht die universelle Korrektheit, es liefert lediglich eine viel zu große Menge an theoretisch möglichen Antworten.

### Orthogonalität: Das Schärfen der Suchanfrage

Um das Rauschen herauszufiltern und das gesuchte Buch zu finden, müssen wir die Suchanfrage spezifizieren. Anstatt die Ergebnisse manuell zu überprüfen, fügen wir der Abfrage weitere EBT-Instanzen hinzu.

Jeder neue, orthogonal aufgespannte Datenpunkt (jeder Randfall, den wir definieren) agiert als zusätzlicher harter Filter in unserer Abfrage. Falsche Hypothesen und triviale Programme aus der Bibliothek kollabieren unter diesen neuen Kriterien und fliegen aus der Treffermenge heraus.

Erweitern wir die Suche zudem um dedizierte semantische Bedingungen und Regeln ($C$), reduziert sich die Treffermenge weiter:

$$\mathcal{S}_{\text{summ}} \cap C = \{ S \in \Sigma^* \mid S: P \to Q \} \cap C$$

Je präziser wir die Realität in unseren EBT-Instanzen durch pre und post abstecken, desto drastischer schrumpft die Liste der Treffer. Die wahre Stärke der Qualitätssicherung liegt darin, die Suchanfrage strategisch so eng zu schnüren, bis aus der Unendlichkeit der Bibliothek exakt die Menge an Büchern als logische Treffer übrig bleiben, die wir gesucht haben.