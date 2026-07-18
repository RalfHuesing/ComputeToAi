# ComputeToAi – Projektregeln

## Worum es hier geht

Dieses Repository enthält das fachliche Konzept (und später die Umsetzung) für eine generische Simulations-Engine: Ein Bestand (Speicher) verändert sich über einen Zeitstrahl durch Effekte, die ihn erhöhen oder senken; Ziel ist, mit ausreichender Wahrscheinlichkeit nie unter eine kritische Schwelle zu fallen (siehe `Docs/01-Kern-Domaenenmodell.md`). Der Kern ist bewusst domänenneutral. Das erste und bislang am weitesten ausgearbeitete Feature-Modul ist „Finanzen": eine Monte-Carlo-Simulation der finanziellen Lebensplanung von Ralf, der in einer Lebensgemeinschaft lebt. Kernfrage dort: Wie viel muss gespart werden, damit der Ruhestand mit ausreichender Wahrscheinlichkeit finanziert ist – ohne zu viel oder zu wenig zu sparen? Berücksichtigt werden u. a. gemeinsame Einkommensströme, individuelle Ausgaben, geplante Anschaffungen, Verbindlichkeiten, ein Cash-Bucket/Liquiditätspuffer, deutsches Steuerrecht, korrelierte Kapitalmarktrenditen und die gesetzliche Rente. Die vollständige Konzeptdokumentation liegt in `Docs/`, beginnend mit `Docs/README.md`.

Langfristige Vision: Das fertige Programm soll agentisch/KI-gestützt nutzbar sein, ohne eigenes Frontend – ein Assistent (Claude Code, Claude Cowork o. Ä.), der proaktiv mitdenkt (z. B. „deine Küche ist 30 Jahre alt, das hält üblicherweise X Jahre, plane das ein"), auf Basis von Alltagswissen realistische Annahmen vorschlägt, daraus eine konkrete Simulationskonfiguration erzeugt, die deterministische Simulation über einen MCP-Server ausführen lässt und die Ergebnisse verständlich erklärt und visualisiert. Details siehe `Docs/00-Vision.md`.

## Arbeitsregeln für dieses Repo

**Keine automatischen Commits**: Es werden keine Git-Commits von selbst ausgeführt. Commits erfolgen ausschließlich auf ausdrückliche Aufforderung.

**Sprache**: Konzeptdokumente werden auf Deutsch verfasst, fachliche Fremdbegriffe (z. B. aus der Portfoliotheorie) dürfen auf Englisch stehen bleiben, wenn das der übliche Fachbegriff ist.

**Quellentreue**: Aussagen zu deutschem Steuer- und Rentenrecht sollen nachvollziehbar und möglichst aktuell sein; bei unsicheren oder sich ändernden Werten (z. B. Freibeträge, Basiszins) wird der Stand (Jahr) explizit vermerkt statt stillschweigend als Konstante angenommen. Recherchierte externe Fakten mit Quelle/URL/Abrufdatum werden zusätzlich in `Docs/09-Quellen.md` festgehalten, nicht nur im jeweiligen Fachdokument verlinkt.

**Konzept vor Code**: Solange primär an `Docs/` gearbeitet wird, werden Implementierungsdetails nicht vorweggenommen. Eine kleine Zahl expliziter Grundsatzentscheidungen ist davon ausgenommen und bereits getroffen (Sprache Python, MCP-only ohne eigenes Frontend, lokale Datenhaltung – siehe `Docs/02-Architektur-und-MCP.md`); alle weiteren Architektur-/Technologiefragen bleiben offen und stehen in `Docs/08-Offene-Fragen.md`.

**Offene Fragen bleiben offen**: `Docs/08-Offene-Fragen.md` enthält ausschließlich Punkte, die tatsächlich noch ungeklärt sind. Sobald eine Frage inhaltlich entschieden wird, wird sie aus dieser Datei entfernt (nicht nur als „beantwortet" markiert und stehen gelassen) und die Entscheidung direkt im fachlich passenden Dokument (Kern-Domänenmodell, Architektur, Feature-Dokumente oder Anforderungen) festgehalten.
