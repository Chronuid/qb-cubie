<center>

# `class WorldState` 

![Alternativtext](docs/assets/cubie-logo-written.png "Error while trying to load the image") 

Die `WorldState`-Klasse ist ein Zustands-Deklarator, der alle Variablen einer Test-Welt kapselt. Sie dient als standardisierte Datenstruktur zur Definition von Zuständen. Seien es nun Vorbedingungen ($P$) oder Nachbedingungen ($Q$) innerhalb des EBT-Paradigmas.
Die Klasse ist konzeptionell die Antwort auf die Frage, wie man komplexe Tests sauber abbildet, ohne den Code mit Boilerplate zu überladen. 
Sie fungiert als das einheitliche Ziel-Schema, in welches die übergeordnete `EBT`-Klasse alle primitiven Eingaben (Shorthands) implizit konvertiert.
</center>

* **Die Kernidentität:** Die Klasse fungiert als strikter "Zustands-Deklarator". Sie ist das standardisierte Objekt, das eine konkrete "Welt" (sei es $P$ oder $Q$) kapselt.

* **Die Trennung der Ebenen:** Ihre wichtigste strukturelle Eigenschaft ist die klare Trennung: Sie separiert die funktionale Ausführungsebene, wie Code-Inputs (`args`) oder Outputs (`returns`), strikt von der topologischen Dateisystem-Ebene (`fs`).

* **Das Normalisierungs-Ziel:** Das `WorldState`-Objekt ist das interne Zielformat der `EBT`-Klasse. Die `EBT`-Klasse nutzt Auto-Inferenz, um einfache Datentypen (Shorthands) unter der Haube implizit in vollumfängliche `WorldState`-Objekte umzuwandeln.




---

### `WorldState.arena`

Das Attribut `arena` speichert als String-Referenz den Pfad oder Bezeichner zu einem isolierten Ausführungsraum (Sandbox/Virtual-Environment). Es dient als reiner Datenhalter, um einen lokalen Override-Mechanismus für die Testumgebung zu ermöglichen, falls das Target die explizite Aufgabe hat, die Umgebung selbst zu mutieren. Wird das Attribut im Vorbedingungs-Zustand ($P$) definiert, repräsentiert es den Ausgangsraum; wird ein abweichender String im Nachbedingungs-Zustand ($Q$) definiert, fungiert dieser reine Datenpunkt für die übergeordnete Engine als deklariertes Ziel für eine Umgebungs-Mutation.
 * **Architektonische Abgrenzung (`arena` vs. `fs`)**: Die Arena repräsentiert ausschließlich das Environment unter der Haube (z.B. installierte Python-Libraries, System-Pakete, Environment-Variablen). Wenn das Ziel ist, zu testen, ob ein Paket erfolgreich via pip installiert wurde, nutzt man `arena`. Sie dient nicht dazu, offene Datei- oder Ordner-Strukturen vom Workspace zu prüfen.

---

### `WorldState.args` und `WorldState.kwargs`

Die Attribute `args` und `kwargs` bilden die funktionale Ausführungsebene des Zustands-Deklarators. Sie repräsentieren ausschließlich die Eingabeparameter für das Target (das Programmsegment $S$) und dienen dazu, die funktionalen Inputs strikt von etwaigen topologischen Dateisystem-Zuständen zu entkoppeln. Sie kapseln als passive Daten-Container ausschließlich die Code-Inputs (positionale und schlüsselwortbasierte Argumente), welche bei der Testausführung an das Target ($S$) übergeben werden sollen.

* **Die Shorthand-Inferenz:** Sie sind die direkten Ziel-Attribute für die Auto-Inferenz der übergeordneten `EBT`-Engine bei reinen In-Memory-Funktionen. Wird in der Vorbedingung (`pre`) ein `tuple` übergeben, wird dieses konventionell und implizit als `args` ausgewertet; wird ein `dict` übergeben, landet dies automatisch im `kwargs`-Attribut des generierten `WorldState`-Objekts.

* Das Framework nutzt diese Attribute als primäre Ziele für die Shorthand-Inferenz: Übergibt der Entwickler ein primitives `tuple` oder `dict` als Vorbedingung, konvertiert die `EBT`-Engine diese implizit in die `args`- bzw. `kwargs`-Attribute eines zugrundeliegenden `WorldState`-Objekts.

---

### `WorldState.returns`
Das Attribut `returns` ist das funktionale Gegenstück zu den Eingabeparametern und kapselt als passiver Daten-Container den erwarteten Output der Nachbedingung ($Q$). Es dient der Validierung direkter funktionaler Schnittstellen des Targets, strikt isoliert von topologischen Zuständen (`fs`). 

* **Der hybride Charakter:** Anstatt die Schnittstellen künstlich aufzublähen, fungiert das Attribut als Sammelbecken für direkte Ausgaben. Es agiert als hybrider Soll-Wert und hält sowohl den klassisch erwarteten Rückgabewert (Return-Value) von Python-Funktionen als auch erwartete Konsolenausgaben (CLI-Streams) vor.
* **Die Shorthand-Inferenz:** Es ist das primäre Ziel-Attribut für einfache Post-Conditions. Übergibt der Entwickler einen primitiven Datentyp (wie `int` oder `str`) direkt an das `post`-Attribut der `EBT`-Klasse, wandelt die Shorthand-Inferenz diesen Wert implizit in das `returns`-Attribut des zugrundeliegenden `WorldState`-Objekts um.


---

### `WorldState.fs`

Das Attribut `fs` (Filesystem) bildet die topologische Ebene des Zustands-Deklarators und trennt physische Dateisystem-Zustände strikt von den funktionalen Code-Inputs. Als passiver Daten-Container speichert es exakt die Pfad-Zuordnungen, welche die Struktur der Sandbox (Arena) definieren.
 
* **Der Datentyp (Konvention vs. Konfiguration):** Das Attribut fasst die Daten entweder als `set` für die flache direkte Konvention oder als `dict` (Dictionary-Pattern). Letzteres fungiert als unkompliziertes String-Mapping, um Pfade auf dem Host-System auf relative Ziel-Pfade innerhalb der isolierten Arena zu projizieren.

* **Die kontextuelle Dualität (als passiver Daten-Container):** Das Attribut selbst speichert nur die Topologie, wird von der `EBT`-Engine jedoch völlig unterschiedlich ausgewertet. Befinden sich die Daten im `pre`-State, dienen sie der Engine als Vorlage für die Workspaces. Befinden sie sich im `post`-State, liest die Engine sie als erwartete Soll-Struktur für das anschließende Byte-für-Byte-Diffing aus.

* * **Architektonische Abgrenzung (`fs` vs. `arena`):** Während die Arena die unsichtbare Laufzeitumgebung darstellt, repräsentiert `fs` die physischen Dateien auf der Festplatte (Ordner, Skripte, Konfigurationen). Wenn das Ziel ist, zu testen, ob ein Skript eine Datei korrekt formatiert oder einen Ordner generiert hat, nutzt man ausschließlich `fs`.

### `WorldState.expect`

Das Attribut `expect` (bool: True or False) fungiert als Negation der Erwartungshaltung für einen Testlauf, um Negativ-Beispiele deklarieren zu können.

---

<center>

![Alternativtext](docs/assets/cubie-small.png "Error while trying to load the image") 

</center>

---