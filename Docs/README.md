# Docs – ComputeToAi Konzept

Konzeptdokumentation für eine generische Simulations-Engine (Speicher/Effekt/Zeitstrahl, siehe 01), deren erstes und bislang am weitesten ausgearbeitetes Feature-Modul die finanzielle Lebensplanung / Ruhestandssimulation (Monte Carlo) ist. Arbeitsregeln für Agenten (u. a. Commit-Verhalten, Code-Standards) stehen in [`.agents/rules/`](../.agents/rules/README.md) im Repo-Root, verlinkt über die dortige `CLAUDE.md`. Die Vision steht in 00-Vision.md.

1. [00-Vision.md](00-Vision.md) – Grundidee, Architekturprinzip Kern+Feature, Abgrenzung
2. [01-Kern-Domaenenmodell.md](01-Kern-Domaenenmodell.md) – Generische Begriffe: Speicher, Effekt, Korrelation, Zeitstrahl, Phase, Zielbedingung, Plan
3. [02-Architektur-und-MCP.md](02-Architektur-und-MCP.md) – Technische Grundsatzentscheidungen: Python, MCP-only über stdio, Settings-Datei, Arbeitsverzeichnis mit mehreren Plänen, Logging, Baustein-Katalog, Regelwerk-Templates
4. [03-Feature-Finanzen-Domaenenmodell.md](03-Feature-Finanzen-Domaenenmodell.md) – Finanz-Begriffe als Instanzen des Kerns
5. [04-Feature-Finanzen-Methodik.md](04-Feature-Finanzen-Methodik.md) – Wie die Finanz-Simulation abläuft
6. [05-Feature-Finanzen-Parameter.md](05-Feature-Finanzen-Parameter.md) – Konfigurierbare Parameter des Finanz-Features
7. [06-Feature-Berechnungen.md](06-Feature-Berechnungen.md) – Deterministische Einzel-Rechenwerkzeuge
8. [07-Anforderungen.md](07-Anforderungen.md) – Was das Programm fachlich und technisch können muss
9. [08-Offene-Fragen.md](08-Offene-Fragen.md) – Noch zu klärende Entscheidungen
10. [09-Quellen.md](09-Quellen.md) – Externe Fakten (u. a. Steuer-/Rentenrecht, Architektur-Vorbilder) mit Quelle und Abrufdatum
11. [10-Roadmap.md](10-Roadmap.md) – Abhakbare Meilensteine und Epics
12. [11-Code-Standards-und-Projektstruktur.md](11-Code-Standards-und-Projektstruktur.md) – Wie der Code strukturiert und geschrieben wird

Stand: laufende Konzeptarbeit, wird fortlaufend erweitert.
