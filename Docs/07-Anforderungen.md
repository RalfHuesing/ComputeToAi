# Anforderungen an das Programm

Dieses Dokument beschreibt, was das spätere Programm fachlich und technisch leisten muss – gegliedert nach Kern, Architektur und Feature-Modulen.

## Kern (generische Engine)

Das Programm muss Speicher (mit optionaler Lot-/FIFO-Semantik), Effekte (roh oder als aktivierbarer Baustein), einen frei konfigurierbaren Zeitstrahl (Dauer und Schrittweite), Phasen und eine Zielbedingung als domänenneutrale Grundbausteine bereitstellen, ohne dabei Annahmen über eine bestimmte Domäne (z. B. Finanzen) zu treffen. Effekte mit stochastischer Komponente müssen paarweise korreliert gezogen werden können. Ein Plan (Konfiguration aus Speichern, Effekten, Zeitstrahl, Phasen, Zielbedingung) muss vollständig kopierbar sein; beim Vergleich zweier Pläne müssen dieselben Zufallsziehungen wiederverwendet werden können (Common Random Numbers), damit Unterschiede im Ergebnis auf die geänderte Konfiguration zurückzuführen sind.

Das Programm muss auf Basis eines Plans eine Monte-Carlo-Simulation mit konfigurierbarer Anzahl an Läufen durchführen und über alle Läufe aggregierte Kennzahlen liefern (mindestens Perzentile des Endsaldos, Wahrscheinlichkeit der Zielverfehlung/Ruin).

## Architektur

Das Programm wird in Python umgesetzt und ausschließlich über einen MCP-Server angesprochen; es gibt kein eigenes Frontend. Die MCP-Tools müssen modular und hierarchisch gegliedert sein (Kern-Tools, Feature-Tools je aktiviertem Modul, Verwaltungs-Tools), damit ein Agent nicht mit einer unübersichtlich großen Zahl flacher Funktionen konfrontiert wird. Die Konfiguration eines Nutzers muss lokal (z. B. als JSON-Datei) gespeichert werden, versehen mit einer Schema-Version zur späteren Migrierbarkeit. Der MCP-Server muss sich selbst beschreiben können (welche Speicher-Typen, Effekte/Bausteine, Parameter, Tools existieren), damit ein Agent ohne Vorwissen über das fachliche Modell navigieren kann. Bausteine müssen als Katalog erweiterbar sein, ohne den Kern zu ändern; Regelwerke mit Zeitbezug (v. a. Steuerrecht) müssen als versionierte, austauschbare Templates einspielbar sein, einschließlich der Fähigkeit, Bestandsschutz-Fälle korrekt zu behandeln (ein Lot bleibt unter dem bei seiner Entstehung gültigen Regelwerk). Sämtliche Visualisierung von Ergebnissen erfolgt außerhalb des MCP-Servers durch den Agenten; der Server liefert dafür ausreichend granulare, strukturierte Zeitreihen (nicht nur Endkennzahlen).

## Feature „Finanzen"

Das Programm muss einen Haushalt mit einer Primärperson und optional weiteren Personen (vereinfacht als Partnerbeitrag) anlegen können. Für die Primärperson müssen Alter, Erwerbsende, gesetzlicher Rentenbeginn (getrennt konfigurierbar, inkl. Rentenabschlag/-zuschlag) und eine Lebenserwartungsannahme hinterlegt werden können, dazu beliebig viele Einkommensströme, individuelle und gemeinsame Ausgaben, fixe und flexible Anschaffungen (inkl. Trigger-Regel und harter Deadline) sowie Verbindlichkeiten (Restschuld, Zinssatz, Rate, Endbedingung, optionale Sondertilgung).

Für die Kapitalanlage müssen beliebig viele Anlageklassen mit erwarteter Rendite, Volatilität, paarweisen Korrelationen und Teilfreistellungssatz definiert werden können, dazu eine Allokation und Rebalancing-Regel. Ein Cash-Bucket muss konfigurierbar sein, dessen Zielgröße sich aus Notfallpuffer-Monaten (phasenabhängig), einem Nah-Horizont und einem Entnahmehorizont (multipliziert mit der berechneten Entnahmeabhängigkeit) zusammensetzt. Ein Ausgangszustand (aktuelles Alter, Startbestand je Anlageklasse inkl. Lot-Historie, Startbestand Cash-Bucket) muss erfassbar sein.

Das Programm muss die deutsche Kapitalertragsbesteuerung als Bausteine abbilden: Abgeltungsteuer inkl. Teilfreistellung und Sparerpauschbetrag, Vorabpauschale, FIFO-Zuordnung inkl. Bestandsschutz für Lots vor dem 1.1.2009, nachgelagerte Rentenbesteuerung inkl. KVdR/Pflegeversicherung. Für flexible Anschaffungen muss die Auslösung über einen Referenzpfad-Vergleich statt reinem Markttiming erfolgen. Das Programm muss erkennen und festhalten, wenn ein Lauf die Zielbedingung verletzt (Ruin), inkl. Zeitpunkt.

Das Programm sollte mehrere Pläne nebeneinander abbilden und vergleichen können (z. B. unterschiedliche Sparquoten, Allokationen, Erwerbsende/Rentenbeginn), explizit inklusive des Falls „früherer Ruhestand" mit Frühruhestandslücke. Es sollte die minimal nötige Sparquote für eine gewünschte Ziel-Erfolgswahrscheinlichkeit ableiten können.

## Feature „Berechnungen"

Das Programm muss einzelne, deterministische Rechenwerkzeuge außerhalb der Monte-Carlo-Simulation bereitstellen (z. B. Datums-/Alters-Arithmetik, Zinseszins, Vergleichsrechnungen wie Leasing vs. Kauf), die sowohl eigenständig als auch zur Plausibilitätsprüfung eines Simulationsergebnisses durch den Agenten genutzt werden können. Eine konkrete Liste ist nicht Teil dieser Anforderungen (siehe 06-Feature-Berechnungen.md und 08-Offene-Fragen.md).

## Nicht-funktionale Erwartungen

Parameter sollen ohne Programmieraufwand änderbar sein. Die Anzahl der Simulationsläufe soll so hoch gewählt werden können, dass Ergebnisse statistisch stabil sind, bei vertretbarer Rechenzeit. Zwischenergebnisse und Annahmen sollen nachvollziehbar bleiben (keine Black Box). Interaktive Ad-hoc-Anfragen im Chat-Kontext (z. B. „kann ich mir das jetzt leisten?") sollen deutlich schneller beantwortbar sein als eine vollständige Batch-Simulation mit tausenden Läufen – die genaue Umsetzung (z. B. reduzierte Laufzahl, Wiederverwendung vorheriger Ergebnisse) ist offen (siehe 08-Offene-Fragen.md).

## Nicht Teil dieser Anforderungen (vorerst)

Mehrfach-Depot-Strukturen mit unterschiedlicher steuerlicher Behandlung, Abbildung von Trennung oder Tod eines Partners, eine konkrete Liste der Berechnungen-Bausteine, sowie jede über die in 02-Architektur-und-MCP.md getroffenen Grundsatzentscheidungen hinausgehende Aussage zu Technologie oder Architektur. Die Kapitalertragsbesteuerung selbst ist dagegen vollständig Teil des Konzepts. Offene Detailfragen stehen in 08-Offene-Fragen.md.
