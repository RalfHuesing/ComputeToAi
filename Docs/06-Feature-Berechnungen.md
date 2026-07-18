# Feature „Berechnungen"

## Zweck

LLMs sind nicht zuverlässig im Ausführen von Arithmetik. Das Berechnungen-Feature stellt deshalb deterministische, einfache Rechenwerkzeuge bereit, auf die ein Agent zurückgreifen kann – sowohl für eigenständige Alltagsfragen außerhalb einer vollen Monte-Carlo-Simulation (z. B. Datums-/Alters-Arithmetik: „ich bin 43, gehe mit 67 in Rente – wie viele Jahre sind das noch?", Zinseszins-Rechnung, Leasing- vs. Cash-Kauf-Vergleich, Kreditvergleich) als auch als Bausteine, mit denen der Agent selbst ein Simulationsergebnis grob plausibilisieren kann (siehe 02-Architektur-und-MCP.md, Abschnitt „Verifikation & Plausibilität").

## Charakter dieses Features

Anders als das Finanzen-Feature enthält dieses Feature keine Simulation über einen Zeitstrahl mit Zufallsziehungen, sondern einzelne, in sich geschlossene deterministische Berechnungen – klassische Formeln, keine Monte-Carlo-Läufe. Es ist bewusst als eigene Kategorie vom Simulations-Kern getrennt (siehe 01-Kern-Domaenenmodell.md), auch wenn beide Feature-Kategorien vom selben MCP-Server angeboten werden.

## Rolle bei der Plausibilitätsprüfung

Wie in 02-Architektur-und-MCP.md festgehalten, gibt es kein eigenes „Verifikations-Feature". Stattdessen liefert dieses Feature die Bausteine, mit denen ein Agent von sich aus ein Simulationsergebnis überschlägt – z. B. indem er aus Sparquote, Zinseszins-Berechnung und Anlagehorizont eine grobe Hausnummer für das Endvermögen bildet und diese dem detaillierten Monte-Carlo-Ergebnis gegenüberstellt, in einer für den Nutzer nachvollziehbaren Form (z. B. Tabelle). Diese Fähigkeit hängt direkt davon ab, dass die Berechnungen-Tools granular und einzeln komponierbar sind, nicht an ein bestimmtes Finanz-Szenario gebunden.

## Umfang

Acht deterministische Rechenbausteine, als MCP-Tools mit dem Präfix `calculations_` angeboten (siehe 02-Architektur-und-MCP.md), gegliedert in drei Gruppen:

**Datums-/Altersarithmetik**:
- Jahre (fraktional) zwischen zwei Datumswerten
- Alter (in ganzen Jahren) zu einem Stichtag

**Zinseszins & Diskontierung**:
- Endwert einer Einmalanlage bei fester jährlicher Rendite
- Barwert eines künftigen Einmalbetrags (Umkehrung der Einmalanlage)
- Endwert einer Serie gleichbleibender periodischer Sparraten – z. B. „100 €/Monat über 40 Jahre bei 5 % Rendite"
- Rentenbarwert (Present Value einer Annuität) einer gleichbleibenden Auszahlungsreihe – z. B. „wie viel Kapital brauche ich für 2.000 €/Monat über 25 Jahre Ruhestand"

**Kreditvergleich**:
- Monatliche Annuitätsrate eines Kredits fester Laufzeit
- Gesamtzinsaufwand über die Kreditlaufzeit

Keiner dieser Bausteine kennt Steuern, Inflation oder Korrelation – das bleibt dem Feature Finanzen vorbehalten (siehe 03–05).

**Bewusst kein eigener Baustein „Leasing vs. Kauf"**: Ein solcher Vergleich ist keine eigenständige Formel, sondern eine Komposition der obigen Bausteine (Kreditrate, Endwert des alternativ investierten Eigenkapitals, Barwert eines Restwerts). Ein dediziertes Tool würde Annahmen (Restwert, Anlagerendite des Eigenkapitals) fest verdrahten und wäre damit weniger granular und komponierbar, als es „Rolle bei der Plausibilitätsprüfung" oben verlangt – ein solcher Vergleich entsteht stattdessen, indem der Agent die granularen Bausteine selbst kombiniert.
