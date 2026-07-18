# ComputeToAi – Projektregeln

## Worum es hier geht

Dieses Repository enthält das fachliche Konzept (und später die Umsetzung) für eine generische Simulations-Engine: Ein Bestand (Speicher) verändert sich über einen Zeitstrahl durch Effekte, die ihn erhöhen oder senken; Ziel ist, mit ausreichender Wahrscheinlichkeit nie unter eine kritische Schwelle zu fallen (siehe `Docs/01-Kern-Domaenenmodell.md`). Der Kern ist bewusst domänenneutral. Das erste und bislang am weitesten ausgearbeitete Feature-Modul ist „Finanzen": eine Monte-Carlo-Simulation der finanziellen Lebensplanung von Ralf, der in einer Lebensgemeinschaft lebt. Kernfrage dort: Wie viel muss gespart werden, damit der Ruhestand mit ausreichender Wahrscheinlichkeit finanziert ist – ohne zu viel oder zu wenig zu sparen? Berücksichtigt werden u. a. gemeinsame Einkommensströme, individuelle Ausgaben, geplante Anschaffungen, Verbindlichkeiten, ein Cash-Bucket/Liquiditätspuffer, deutsches Steuerrecht, korrelierte Kapitalmarktrenditen und die gesetzliche Rente. Die vollständige Konzeptdokumentation liegt in `Docs/`, beginnend mit `Docs/README.md`.

Langfristige Vision: Das fertige Programm soll agentisch/KI-gestützt nutzbar sein, ohne eigenes Frontend – ein Assistent (Claude Code, Claude Cowork o. Ä.), der proaktiv mitdenkt (z. B. „deine Küche ist 30 Jahre alt, das hält üblicherweise X Jahre, plane das ein"), auf Basis von Alltagswissen realistische Annahmen vorschlägt, daraus eine konkrete Simulationskonfiguration erzeugt, die deterministische Simulation über einen MCP-Server ausführen lässt und die Ergebnisse verständlich erklärt und visualisiert. Details siehe `Docs/00-Vision.md`.

## Arbeitsregeln für dieses Repo

Dieses Repo wird **vollagentisch** entwickelt – bewusst mit mehreren Agenten (Claude Code, ggf. weitere), nicht nur mit einem. Die eigentlichen Arbeitsregeln liegen deshalb tool-neutral im Verzeichnis [.agents/rules/](.agents/rules/README.md) (Format `.mdc`, aus den Konzeptdokumenten in `Docs/` abgeleitet – bei Widerspruch gilt `Docs/`) und werden hier für Claude Code eingebunden:

@.agents/rules/language.mdc
@.agents/rules/proactive-questions.mdc
@.agents/rules/sources-and-concept.mdc
@.agents/rules/living-documentation.mdc
@.agents/rules/code-standards.mdc
@.agents/rules/mcp-server-architecture.mdc
@.agents/rules/testing.mdc
@.agents/rules/git-workflow.mdc
@.agents/rules/environment.mdc

Die vollständige fachliche Konzeptdokumentation liegt in `Docs/`, beginnend mit [Docs/README.md](Docs/README.md).
