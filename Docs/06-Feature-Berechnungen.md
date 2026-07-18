# Feature „Berechnungen"

## Zweck

LLMs sind nicht zuverlässig im Ausführen von Arithmetik – erst recht nicht bei iterativen/numerischen Verfahren wie einem internen Zinsfuß. Das Berechnungen-Feature stellt deshalb deterministische Rechenwerkzeuge bereit, auf die ein Agent zurückgreifen kann – sowohl für eigenständige Alltagsfragen außerhalb einer vollen Monte-Carlo-Simulation (z. B. Datums-/Alters-Arithmetik: „ich bin 43, gehe mit 67 in Rente – wie viele Jahre sind das noch?", Zinseszins-Rechnung, Kreditvergleich, oder „hier ist ein Kreditangebot als PDF – rechne den echten Effektivzins nach") als auch als Bausteine, mit denen der Agent selbst ein Simulationsergebnis grob plausibilisieren kann (siehe 02-Architektur-und-MCP.md, Abschnitt „Verifikation & Plausibilität"). Da diese Tools keine Simulation voraussetzen, kann ein Agent sie auch völlig unabhängig von einem angelegten Plan nutzen, um beliebige vom Nutzer mitgebrachte Zahlen (Angebote, Kontoauszüge) explorativ nachzurechnen.

## Charakter dieses Features

Anders als das Finanzen-Feature enthält dieses Feature keine Simulation über einen Zeitstrahl mit Zufallsziehungen, sondern einzelne, in sich geschlossene deterministische Berechnungen – klassische Formeln, keine Monte-Carlo-Läufe. Es ist bewusst als eigene Kategorie vom Simulations-Kern getrennt (siehe 01-Kern-Domaenenmodell.md), auch wenn beide Feature-Kategorien vom selben MCP-Server angeboten werden.

## Rolle bei der Plausibilitätsprüfung

Wie in 02-Architektur-und-MCP.md festgehalten, gibt es kein eigenes „Verifikations-Feature". Stattdessen liefert dieses Feature die Bausteine, mit denen ein Agent von sich aus ein Simulationsergebnis überschlägt – z. B. indem er aus Sparquote, Zinseszins-Berechnung und Anlagehorizont eine grobe Hausnummer für das Endvermögen bildet und diese dem detaillierten Monte-Carlo-Ergebnis gegenüberstellt, in einer für den Nutzer nachvollziehbaren Form (z. B. Tabelle). Diese Fähigkeit hängt direkt davon ab, dass die Berechnungen-Tools granular und einzeln komponierbar sind, nicht an ein bestimmtes Finanz-Szenario gebunden.

## Umfang

21 deterministische Rechenbausteine, als MCP-Tools mit dem Präfix `calculations_` angeboten (siehe 02-Architektur-und-MCP.md), gegliedert in sechs Gruppen. Viele Gruppen enthalten neben der direkten Formel auch deren Umkehrung(en) – gerade bei der Ruhestandsplanung ist meist die umgekehrte Frage die eigentlich interessante („wie viel muss ich sparen", nicht „was ergibt sich aus dieser Sparrate"):

**Datums-/Altersarithmetik** (`compute_to_ai.features.calculations.dates`):
- Jahre (fraktional) zwischen zwei Datumswerten
- Alter (in ganzen Jahren) zu einem Stichtag

**Einmalbeträge, Wachstumsraten & Inflation** (`compute_to_ai.features.calculations.growth`):
- Endwert einer Einmalanlage bei fester jährlicher Rendite, und deren Umkehrung: Barwert eines künftigen Einmalbetrags
- Durchschnittliche jährliche Wachstumsrate (CAGR) zwischen einem Anfangs- und Endwert (Umkehrung der Einmalanlage nach dem Zinssatz aufgelöst)
- Reale (inflationsbereinigte) Rendite aus einer nominalen Rendite (Fisher-Gleichung)
- Kaufkraft eines künftigen nominalen Betrags in heutigem Geld

**Sparpläne** (ebenfalls `growth`):
- Endwert einer Serie gleichbleibender periodischer Sparraten – z. B. „100 €/Monat über 40 Jahre bei 5 % Rendite"
- und deren zwei Umkehrungen: nötige Sparrate für ein Zielkapital, sowie nötige Anzahl an Perioden bis zum Zielkapital

**Entnahmepläne / Rentenbarwert** (ebenfalls `growth`):
- Rentenbarwert (Present Value einer Annuität) einer gleichbleibenden Auszahlungsreihe – z. B. „wie viel Kapital brauche ich für 2.000 €/Monat über 25 Jahre Ruhestand"
- und deren zwei Umkehrungen: nachhaltige Entnahmehöhe, die ein Kapital über N Perioden exakt aufbraucht, sowie Anzahl an Perioden, bis eine gegebene Entnahmehöhe ein Kapital aufbraucht
- Variante mit Inflationsausgleich: Start-Entnahme, die (bei jährlich um die Inflation steigender Entnahme) ein Kapital über N Perioden exakt aufbraucht – realistischer als eine nominal gleichbleibende Entnahme, da sie die Kaufkraft erhält

**Kreditvergleich** (`compute_to_ai.features.calculations.loans`):
- Monatliche Annuitätsrate eines Kredits fester Laufzeit, Gesamtzinsaufwand über die Laufzeit
- Restschuld nach einer bestimmten Anzahl geleisteter Raten
- Vollständiger Tilgungsplan (Zins-/Tilgungsanteil je Periode)
- Tilgungsplan mit einer oder mehreren Sondertilgungen zu festgelegten Zeitpunkten (Rate bleibt gleich, Restlaufzeit verkürzt sich) – ein reiner Was-wäre-wenn-Rechner mit vom Nutzer vorgegebenen Beträgen, keine Simulation einer dynamischen Sondertilgungs-Entscheidung innerhalb eines laufenden Plans (das bleibt Feature Finanzen vorbehalten)

**Zahlungsstrom-Analyse** (`compute_to_ai.features.calculations.cashflows`, numerisches Root-Finding statt geschlossener Formel):
- Interner Zinsfuß (XIRR) einer Reihe unregelmäßig datierter, unregelmäßig hoher Zahlungen – z. B. ein Depot mit unregelmäßigen Ein-/Auszahlungen
- Effektivzins eines Kredits unter Berücksichtigung von Bearbeitungsgebühren und/oder einem Auszahlungskurs unter 100 % (vereinfachtes Modell, siehe Docstring – keine rechtsverbindliche PAngV-Berechnung)

Keiner dieser Bausteine kennt Steuern oder Korrelation zwischen Anlageklassen – das bleibt dem Feature Finanzen vorbehalten (siehe 03–05); Inflation dagegen ist als eigenständige, von der Finanzen-Domäne unabhängige Größe bewusst Teil dieses Features.

**Bewusst kein eigener Baustein „Leasing vs. Kauf"**: Ein solcher Vergleich ist keine eigenständige Formel, sondern eine Komposition der obigen Bausteine (Kreditrate, Endwert des alternativ investierten Eigenkapitals, Barwert eines Restwerts). Ein dediziertes Tool würde Annahmen (Restwert, Anlagerendite des Eigenkapitals) fest verdrahten und wäre damit weniger granular und komponierbar, als es „Rolle bei der Plausibilitätsprüfung" oben verlangt – ein solcher Vergleich entsteht stattdessen, indem der Agent die granularen Bausteine selbst kombiniert.

**Bewusst (noch) nicht enthalten**: deutsche Steuerformeln (Abgeltungsteuer, Vorabpauschale, nachgelagerte Rentenbesteuerung) – explizit Teil des Feature Finanzen (siehe 03-Feature-Finanzen-Domaenenmodell.md bzw. 10-Roadmap.md) und zusätzlich unterliegt Steuer-/Rentenrecht der Quellentreue-Pflicht (siehe CLAUDE.md); Portfolio-Kennzahlen, die eine Korrelationsmatrix mehrerer Anlageklassen voraussetzen (z. B. erwartete Portfolio-Volatilität) – ebenfalls Feature-Finanzen-Scope (Anlageklassen-Korrelation, siehe 10-Roadmap.md); Anleihen-Kennzahlen wie Duration – für die Ruhestandsplanungs-Ausrichtung dieses Projekts eher Randnutzen (Bond-Portfolio-Risikoanalyse), kein aktueller Bedarf erkennbar.
