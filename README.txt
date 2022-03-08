Copyright Benedikt Schenk, 2022

Guide-Einteilungstool v1.0 



Um das Programm zu starten: Rechtsklick auf run.py -> 'Öffnen mit Python'




BENUTZUNGSANLEITUNG



1. Koordinaten

Die Datei 'Koordinaten.xlsx' hat zwei Sheets: Für Guides und für Events. Diese müssen aktuell und vollständig gehalten werden. Es sind 
jeweils nur die ersten beiden Spalten entscheidend. Zeile 3 muss die erste Zeile mit Inhalt sein. Die Lat/Long-Koordinaten können auf 
verschiedene Weisen ermittelt werden und müssen nicht exakt sein. 

Tipp: Google Maps, Rechts-Klick auf die Karte, Links-Klick auf die angezeigten Koordinaten, Strg-V im Excel-Sheet



2. Anzahl Wunschtage

Das Sheet 'Anzahl Wunschtage' befindet sich in der Datei 'Wunschtage.xlsx'. Es muss vollständig sein. Zeile 3 muss die erste Zeile mit Inhalt sein.
Die Guide-Namen müssen übereinstimmen mit den Guide-Namen in der Datei 'Koordinaten.xlsx'. 



3. Verfügbarkeiten

Das Sheet 'Verfügbarkeiten' befindet sich ebenfalls in der Datei 'Wunschtage.xlsx'. Zeile 3 muss die erste Zeile mit Inhalt sein. Eine Zeile steht für ein Event.

3.1 Spalte 'A' definiert die ID eines Events. Sie kann beliebig gewählt werden, muss jedoch einzigartig sein.

3.2 Spalte 'B' definiert den Kursort. Dieser muss übereinstimmen mit einem Ortnamen in 'Koordinaten.xlsx'.

3.3 Spalte 'C' definiert die Anzahl Guides, die für dieses Event benötigt werden.

3.4 Spalte 'D' definiert die Events, mit denen sich dieses Event zeitlich überschneidet. Falls überschneidende Events existieren, müssen
diese mit ihrerer ID angegeben werden. Mehrere IDs müssen durch Strichkommata getrennt werden.

3.5 Spalte 'H' definiert die Guides, die sich für dieses Event als 'Verfügbar mit hoher Priorität' eingetragen haben. Die Guide-Namen müssen mit der Datei 
'Koordinaten.xlsx' und dem Sheet 'Wunschtage' übereinstimmen. Mehrere Namen werden durch ein einfache Kommata getrennt, Leerzeichen dürfen gesetzt werden.

3.6 Spalte 'I' definiert die Guides, die sich für dieses Event als 'Verfügbar mit niedriger Priorität' eingetragen haben. Siehe Punkt 3.5




4. Programmstart

Ein Doppelklick auf guide_einteilung.exe startet das Programm. Ein Konsolenfenster öffnet sich. Den Anweisungen der Konsole folgen. Je nach Problemgröße ist mit einer
Wartezeit von einer Minute bis einer Stunde zu rechnen.


Erklärung, falls nicht die Standard-Gewichtung gewählt wird:

Das Programm minimiert bei seiner Berechnung 4 Variablen:

Variable 1: Durchschnittliche Abweichung der Arbeitstage aller Guides von den Wunschtagen
Variable 2: Die maximale Abweichung der Arbeitstage eines Guides von den Wunschtagen
Variable 3: Die summierte Distanz der Guides zu ihren Kursorten
Variable 4: Die Anzahl an Guide-Einteilungen mit Priorität 2

Die Wichtigkeit der einzelnen Variablen gegenüber einander kann unterschiedlich gewichtet werden. Standardmäßig ist eine 1-1-1-1 Gewichtung gewählt. Falls jedoch
beispielsweise der Distanz eine doppelte Wichtigkeit gegenüber dem Restzugeordnet werden soll, kann eine 1-1-2-1 Gewichtung gewählt werden. Falls die Priorität
keine Rolle spielt, kann eine 1-1-1-0 Gewichtung gewählt werden. Eine 1-1-1-1 Gewichtung ist dabei gleichbedeutend zu beispielsweise einer 2-2-2-2 Gewichtung.

Die Gewichtung bestimmt welche Guide-Einteilung durch das Programm als die beste angesehen wird und für den Output gewählt wird.




5. Output

Nach fertiger Berechnung wird der Output als Excel-Sheet im Ordner 'output' gespeichert. Eingeteilte Guides mit hoher Priorität werden blau markiert. Für jede
Einteilung gibt es eine Statisik mit nützlichen Informationen zur Analyse.
