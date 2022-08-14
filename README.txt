Copyright Benedikt Schenk, 2022

Guide-Einteilungstool v1.0 





BENUTZUNGSANLEITUNG


I) Einrichtung der Dateien

1. Koordinaten

Für die Koordinaten braucht es eine Excel Datei, welche zwei Sheets enthält: 'guides' und 'events'. Diese müssen aktuell und vollständig gehalten werden. In der ersten Spalte
(ab Zeile 3!) steht jeweils der Name vom Guide / vom Event-Ort. In der zweiten Spalte die Lat/Long-Koordinaten, durch Kommas getrennt. Diese können auf verschiedene Weisen 
ermittelt werden und müssen nicht exakt sein. Die restlichen Zeilen und Spalten können für Anmerkungen verwendet werden.

Tipp: Google Maps, Rechts-Klick auf die Karte, Links-Klick auf die angezeigten Koordinaten, Strg-V im Excel-Sheet



2. Terminwünsche

Für die Terminwünsche braucht es ebenfalls eine Excel Date, welche zwei Sheets enthält: 'Anzahl Wunschtage' und 'Übersicht Terminwünsche'

Das Sheet 'Anzahl Wunschtage' wird in der ersten Spalte (ab Zeile 3!) mit den Namen der Guides befüllt, in der zweiten Spalte mit der jeweils gewünschten Anzahl an Arbeitstagen.
Das Sheet muss vollständig sein. Die Guide-Namen müssen übereinstimmen mit den Guide-Namen in der Koordinaten-Datei. 


Das Sheet 'Verfügbarkeiten' wird ebenfalls ab Zeile 3 befüllt. Eine Zeile steht für ein Event.

3.1 Spalte 'A' definiert die ID eines Events. Sie kann beliebig gewählt werden, muss jedoch einzigartig sein (Tipp: von 1 aufwärts durchnummerieren).

3.2 Spalte 'B' definiert den Kursort. Dieser muss übereinstimmen mit einem Ortnamen in 'Koordinaten.xlsx'.

3.3 Spalte 'C' definiert die Anzahl an Tagen, die dieses Event andauert.

3.4 Spalte 'D' definiert die Anzahl Guides, die für dieses Event benötigt werden.

3.5 Spalte 'E' definiert die Events, mit denen sich dieses Event zeitlich überschneidet. Falls überschneidende Events existieren, müssen
diese mit ihrerer ID angegeben werden. Es reicht aus, lediglich die Events anzugeben, die in der Tabelle weiter unten definiert werden.
Mehrere IDs müssen durch Strichkommata (;) getrennt werden.

3.6 Spalten 'G' bis 'J' listen die für dieses Event verfügbaren Guides auf. Falls mehrere Namen in einer Zelle gelistet sind, müssen diese mit einfachen Kommata (,) getrennt werden.
Spalte 'G' steht für die Guides mit niedrigster Priorität, 'H' mit mittlerer, 'I' mit hoher und 'J' für die Guides, welche zwangsweise für dieses Event gesetzt werden müssen.
Die Guide-Namen müssen mit der Koordinaten-Datei und dem Sheet 'Anzahl Wunschtage' übereinstimmen. Mehrere Namen werden durch ein einfache Kommata getrennt.




II) Programmstart

Rechtsklick auf run.py -> 'Öffnen mit Python'
Ein kleines Fenster öffnet sich. Die zwei Dateien (aus Teil I) und den gewünschten Speicherort für den Output angeben. 
Optional: Über die Schaltfläche "Custom weights" eigene Gewichtungen wählen.
Dann auf "Compute" klicken. Die Wartezeit hängt stark von der Problemgröße ab. Im Normalfall sollte die Wartezeit wenige Sekunden, im Worst-Case exakt 10 Minuten betragen.

Erklärung, falls nicht die Standard-Gewichtung gewählt wird:

Das Programm minimiert bei seiner Berechnung folgende Variablen:

Variable 1: Die Abweichung zwischen gewünschten und zugeteilten Arbeitstagen
Variable 2: Die summierte Distanz der Guides zu ihren Kursorten

Und maximiert folgende Variable:

Variable 3: Die durchschnittliche Priorität

Die Wichtigkeit der einzelnen Variablen gegenüber einander kann unterschiedlich gewichtet werden. Standardmäßig ist eine 1-1-1 Gewichtung gewählt. Falls jedoch
beispielsweise der Distanz eine doppelte Wichtigkeit gegenüber dem Rest zugeordnet werden soll, kann eine 1-2-1 Gewichtung gewählt werden. Falls die Priorität
keine Rolle spielt, kann eine 1-1-0 Gewichtung gewählt werden. Eine 1-1-1 Gewichtung ist dabei gleichbedeutend zu beispielsweise einer 2-2-2 Gewichtung.

Die Gewichtung bestimmt welche Guide-Einteilung durch das Programm als die beste angesehen wird und für den Output gewählt wird.



III) Output

Nach fertiger Berechnung wird der Output als Excel-Sheet am angegebenen Ort gespeichert. Eingeteilte Guides werden je nach Priorität mit unterschiedlicher Farbe markiert. Für jede
Einteilung gibt es ein zweites Sheet mit einer Statisik mit nützlichen Informationen zur Analyse.

Bei Fehlermeldungen und Log-Nachrichten werden die Dateien 'errors.txt' und 'logs.txt' erstellt. Diese bitte dem Programmierer weiterleiten.
