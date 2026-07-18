# Feature „Berechnungen"

## Zweck

LLMs sind nicht zuverlässig im Ausführen von Arithmetik. Das Berechnungen-Feature stellt deshalb deterministische, einfache Rechenwerkzeuge bereit, auf die ein Agent zurückgreifen kann – sowohl für eigenständige Alltagsfragen außerhalb einer vollen Monte-Carlo-Simulation (z. B. Datums-/Alters-Arithmetik: „ich bin 43, gehe mit 67 in Rente – wie viele Jahre sind das noch?", Zinseszins-Rechnung, Leasing- vs. Cash-Kauf-Vergleich, Kreditvergleich) als auch als Bausteine, mit denen der Agent selbst ein Simulationsergebnis grob plausibilisieren kann (siehe 02-Architektur-und-MCP.md, Abschnitt „Verifikation & Plausibilität").

## Charakter dieses Features

Anders als das Finanzen-Feature enthält dieses Feature keine Simulation über einen Zeitstrahl mit Zufallsziehungen, sondern einzelne, in sich geschlossene deterministische Berechnungen – klassische Formeln, keine Monte-Carlo-Läufe. Es ist bewusst als eigene Kategorie vom Simulations-Kern getrennt (siehe 01-Kern-Domaenenmodell.md), auch wenn beide Feature-Kategorien vom selben MCP-Server angeboten werden.

## Rolle bei der Plausibilitätsprüfung

Wie in 02-Architektur-und-MCP.md festgehalten, gibt es kein eigenes „Verifikations-Feature". Stattdessen liefert dieses Feature die Bausteine, mit denen ein Agent von sich aus ein Simulationsergebnis überschlägt – z. B. indem er aus Sparquote, Zinseszins-Berechnung und Anlagehorizont eine grobe Hausnummer für das Endvermögen bildet und diese dem detaillierten Monte-Carlo-Ergebnis gegenüberstellt, in einer für den Nutzer nachvollziehbaren Form (z. B. Tabelle). Diese Fähigkeit hängt direkt davon ab, dass die Berechnungen-Tools granular und einzeln komponierbar sind, nicht an ein bestimmtes Finanz-Szenario gebunden.

## Umfang (bewusst noch nicht im Detail spezifiziert)

Eine konkrete Liste einzelner Rechenbausteine (Zinseszins, Alters-/Datumsarithmetik, Leasing vs. Kauf, Kreditvergleich, Rentenbarwert o. Ä.) ist zum jetzigen Zeitpunkt bewusst nicht ausgearbeitet. Diese Detaillierung erfolgt, sobald der Kern und das Finanzen-Feature stehen (siehe 10-Roadmap.md); bis dahin steht der Bedarf als Kategorie in 07-Anforderungen.md und 08-Offene-Fragen.md.
