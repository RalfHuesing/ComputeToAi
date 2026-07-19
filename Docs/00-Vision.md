# ComputeToAi – Vision & Überblick

## Grundidee

Dieses Projekt ist im Kern kein Finanzprogramm, sondern eine generische Simulations-Engine für eine sehr allgemeine Frage: Bleibt ein Bestand über der Zeit über einer kritischen Linie, wenn verschiedene Kräfte auf ihn wirken? Ein Bestand (siehe **Speicher** in 01-Kern-Domaenenmodell.md) verändert sich über einen Zeitstrahl durch **Effekte**, die ihn erhöhen oder senken; manche Effekte hängen zufällig, korreliert oder phasenabhängig voneinander ab; Ziel ist, mit ausreichender Wahrscheinlichkeit nie unter eine kritische Schwelle (meist 0) zu fallen.

Dieses Muster ist nicht neu erfunden, sondern ein seit Jahrzehnten etabliertes wissenschaftliches Paradigma unter verschiedenen Namen: **System Dynamics** (Jay Forrester, „Stock and Flow"-Modelle), die **Ruin Theory** der Versicherungsmathematik (Cramér–Lundberg-Modell: ein Bestand, Prämien fließen zu, Schäden fließen zufällig ab, gefragt ist die Ruinwahrscheinlichkeit) oder kompartimentelle Modelle in der Ökologie (Populationsdynamik, Lotka-Volterra). Dieselbe Struktur trägt sowohl eine Ruhestands-Cashflow-Simulation als auch – als Gedankenexperiment zur Einordnung, nicht als aktueller Scope – einen Radmarathon (Energiespeicher, Gegenwind/Steigung als Effekte, Erschöpfung als „Ruin") oder ein Startup-Runway-Modell (Kontostand als Speicher, Personalkosten als Effekt, Funding als Zufluss). Die wissenschaftliche Fundiertheit dieses Kerns – und, darauf aufbauend, der Finanz-Instanz im Speziellen – ist ein durchgehendes Leitprinzip dieses Konzepts, keine Ausschmückung.

## Architekturprinzip: Kern + Feature-Module

Das System besteht aus einem domänenneutralen Kern (siehe 01-Kern-Domaenenmodell.md) und darauf aufsetzenden Feature-Modulen. „Finanzen" ist das erste und bislang am weitesten ausgearbeitete Feature-Modul (siehe 03–05), „Berechnungen" ein zweites, schlankeres Modul (siehe 06). Der Kern selbst kennt weder „Steuer" noch „Person" noch „Euro" – all das kommt erst durch das jeweils aktivierte Feature-Modul hinzu. Neue Domänen (andere Simulationsgegenstände) oder neue Bausteine innerhalb eines bestehenden Feature-Moduls sollen sich ergänzen lassen, ohne den Kern zu ändern.

## Agentische Nutzung, kein eigenes Frontend

Das System hat keine eigene Benutzeroberfläche. Einziger Zugangsweg ist ein MCP-Server, angesprochen von einem bestehenden Agenten (Claude Code, Claude Cowork o. Ä.), der über Prompts/Workflow-Dateien (Markdown) weiß, welche Rolle er gerade einnimmt – z. B. „du bist mein Finanzberater, hilf mir bei der Ruhestandsplanung". Diese Dateien liegen unter `Docs/prompts/<feature>_<sprache>/` (z. B. `Docs/prompts/finance_de/finanzberater.md`) und werden wie die übrige Konzeptdokumentation als `docs://`-Resources bereitgestellt – bewusst klientenneutrales Markdown statt eines an einen bestimmten Agenten gebundenen Formats. Die deterministische Rechenarbeit (Simulation, Berechnung) liegt vollständig im MCP-Server; Kontext verstehen, Rückfragen stellen, Ergebnisse erklären und jede Visualisierung liegen vollständig beim Agenten. Details der technischen Umsetzung stehen in 02-Architektur-und-MCP.md.

## Was-wäre-wenn-Charakter

Das System soll nicht nur einen einzigen geplanten Verlauf durchrechnen, sondern beliebige Varianten gegenüberstellen können: kopierbare **Pläne** (siehe 01), die sich in einzelnen Speichern, Effekten oder Parametern unterscheiden. Im Finanz-Feature z. B. „fünf Jahre früher in Ruhestand" oder „kann ich mir heute ein 10.000-€-Fahrrad leisten, ohne mein Verbrauchsziel zu gefährden" – strukturell aber jede Änderung an Speichern, Effekten oder Zeitstrahl in jeder Domäne.

## Abgrenzung

Dieses Konzept legt die fachliche und architektonische Grundlage fest, ist aber kein vollständiges Pflichtenheft. Einzelne technische Grundsatzentscheidungen sind bereits getroffen (siehe 02-Architektur-und-MCP.md), viele Detailfragen bleiben bewusst offen (siehe 08-Offene-Fragen.md) und werden iterativ geklärt. Eine grobe zeitliche/inhaltliche Abfolge der weiteren Ausarbeitung steht in 10-Roadmap.md.

## Struktur der Konzeptdokumente

| Dokument | Inhalt |
|---|---|
| [01-Kern-Domaenenmodell.md](01-Kern-Domaenenmodell.md) | Generische Begriffe: Speicher, Effekt, Korrelation, Zeitstrahl, Phase, Zielbedingung, Plan |
| [02-Architektur-und-MCP.md](02-Architektur-und-MCP.md) | Technische Grundsatzentscheidungen: Python, MCP-only, lokale Datenhaltung, Baustein-Katalog, Regelwerk-Templates |
| [03-Feature-Finanzen-Domaenenmodell.md](03-Feature-Finanzen-Domaenenmodell.md) | Finanz-Begriffe als Instanzen des Kerns: Haushalt, Person, Einkommen, Ausgaben, Verbindlichkeiten, Portfolio, Cash-Bucket |
| [04-Feature-Finanzen-Methodik.md](04-Feature-Finanzen-Methodik.md) | Wie die Finanz-Simulation konkret abläuft |
| [05-Feature-Finanzen-Parameter.md](05-Feature-Finanzen-Parameter.md) | Konfigurierbare Parameter des Finanz-Features |
| [06-Feature-Berechnungen.md](06-Feature-Berechnungen.md) | Deterministische Einzel-Rechenwerkzeuge (kein Simulationslauf) |
| [07-Anforderungen.md](07-Anforderungen.md) | Was das System fachlich und technisch können muss |
| [08-Offene-Fragen.md](08-Offene-Fragen.md) | Noch zu klärende Entscheidungen |
| [09-Quellen.md](09-Quellen.md) | Externe Fakten (v. a. Steuer-/Rentenrecht) mit Quelle und Abrufdatum |
| [10-Roadmap.md](10-Roadmap.md) | Abhakbare Meilensteine und Epics |
| [11-Code-Standards-und-Projektstruktur.md](11-Code-Standards-und-Projektstruktur.md) | Wie der Code strukturiert und geschrieben wird |
| [12-Disruption-und-Reality-Check.md](12-Disruption-und-Reality-Check.md) | Das Potenzial und die harten Grenzen von ComputeToAi (Disruptionsanalyse, Behavioral Finance, Thesenmatrix) |

Die Dokumente bauen aufeinander auf, können aber auch einzeln gelesen werden. Sie werden im Laufe der weiteren Arbeit erweitert und angepasst.

