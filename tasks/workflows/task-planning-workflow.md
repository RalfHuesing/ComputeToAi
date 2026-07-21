# Task-Planungs-Workflow: Von der Vision zu Ausführbaren Steps

## Zweck & Ziel
Dieser Workflow beschreibt das standardisierte Vorgehen, wie aus groben Visionen, Feature-Ideen oder Roadmap-Einträgen konkrete, agentenfreundliche **Task-Pakete** mit ausführbaren **Step-Dateien** erstellt werden. Ziel ist es, dass ausführende Sub-Agenten alle nötigen Informationen (Intention, Architektur, konkrete Code-Muster & Pfade) vorfinden und keine eigenmächtigen Annahmen treffen müssen.

---

## 1. Task-Struktur & Konventionen

Jede größere Aufgabe wird als eigenes Verzeichnis unter `tasks/` angelegt:

```text
tasks/
├── workflows/                          # Dieser und weitere Workflows
│   └── task-planning-workflow.md
├── _templates/                         # Vorlagen für Konzept, Steps & Reviews
│   ├── 00-konzept-template.md
│   ├── 0X-step-template.md
│   └── review-template.md
└── task-[EPIC_NR]-[THEMA]/              # Einzelnes Task-Paket (z.B. task-4.10-auswertungen)
    ├── 00-konzept.md                   # Intention, Architektur, DoD & Kontrollkriterien
    ├── 01-step-[SUBTHEMA].md           # Konkrete Ausführungseinheit 1
    ├── 02-step-[SUBTHEMA].md           # Konkrete Ausführungseinheit 2
    └── review.md                       # Kontroll-Ergebnis des Review-Agenten
```

---

## 1.1 Einhaltung der Agent-Rules (`.agents/rules/`)

Sowohl beim Erstellen von Konzepten und Steps als auch bei deren Umsetzung sind **zwingend** alle im Projekt definierten Agenten-Regeln unter [.agents/rules/](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/.agents/rules) zu berücksichtigen:
- [.agents/rules/code-standards.mdc](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/.agents/rules/code-standards.mdc): Vorgaben für Python 3.12+, Typisierung, Pydantic v2 & Docstrings im Konzept & Code verankern.
- [.agents/rules/language.mdc](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/.agents/rules/language.mdc): Code, Docstrings, Kommentare und Commits ausschließlich in **Englisch**.
- [.agents/rules/testing.mdc](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/.agents/rules/testing.mdc): Pflicht-Abdeckung von Happy Path & **Edge Cases** (Grenzwerte, Fehleingaben) in allen Steps verankern.
- [.agents/rules/living-documentation.mdc](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/.agents/rules/living-documentation.mdc): Doku-Aufträge für `Docs/` in allen Steps eingeplant.
- [.agents/rules/git-workflow.mdc](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/.agents/rules/git-workflow.mdc): Atomare Commits mit Conventional Commits Syntax vorsehen.
- [.agents/rules/mcp-server-architecture.mdc](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/.agents/rules/mcp-server-architecture.mdc): Schichten-Trennung (Engine / Feature / MCP Tools) im Architekturteil des Konzepts beachten.
- [.agents/rules/sources-and-concept.mdc](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/.agents/rules/sources-and-concept.mdc): Belege in `Docs/09-Quellen.md` und Konzeptionierung vor Code.
- [.agents/rules/proactive-questions.mdc](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/.agents/rules/proactive-questions.mdc): Prägnante Abstimmungen und klare Entscheidungsfragen.

---

## 2. Ablauf des Planungs-Workflows

### Schritt 1: Detaillierte Besprechung & Prägnante Abstimmung
- **Prägnante Kommunikation**: Keine ellenlangen Textwüsten im Chat. Der Agent denkt fachlich-wissenschaftlich mit (aus Sicht von Nutzer und Finanzberater), schlägt fundierte Lösungen vor und stellt nur kurze, fokussierte Entscheidungsfragen. Details gehören direkt in die Task-Dokumente!
- **Keine offenen Fragen**: Fachliche Regeln, Grenzfälle, Edge Cases und Algorithmen werden im Konzept vollständig spezifiziert.

### Schritt 2: Erstellung des Konzept-Dokuments (`00-konzept.md`)
Enthält mindestens:
- **Status**: `DRAFT` (in Besprechung), `READY` (bereit für Umsetzung), `IN_PROGRESS` (in Arbeit), `DONE` (abgeschlossen & gereviewt).
- **Intention & Fachliche Motivation**: Warum wird das gebaut? Welches Nutzer-Problem löst es?
- **Architektur & Komponenten**: Welche Dateien/Module werden berührt, welche neuen Klassen/Tools entstehen?
- **Code-Muster & Anhaltspunkte**: Konkrete Funktionssignaturen, Datenstrukturen und Code-Skizzen, damit der Ausführungs-Agent nicht raten muss.
- **Abnahmekriterien (Definition of Done)**: Exakte Testkommandos, Edge-Case-Anforderungen, Living-Documentation-Pflichten.

### Schritt 3: Erstellung der Step-Dateien (`01-step-*.md`, `02-step-*.md`)
Jede Step-Datei ist eine in sich geschlossene, atomare Arbeitseinheit für einen Sub-Agenten:
- **Intention des Steps**
- **Zu verändernde / neu zu erstellende Dateien** (als `file://`-Links)
- **Konkreter Code-Entwurf & Implementierungshinweise**
- **Test-Spezifikation (Happy Path + Edge Cases)**
- **Doku-Aktualisierungs-Auftrag** (Living Documentation gemäß `.agents/rules/living-documentation.mdc`)

### Schritt 4: Roadmap-Einkürzung & Verlinkung
- In `Docs/10-Roadmap.md` wird der lange Beschreibungstext des Epics durch schlanke Stichpunkte mit Checkboxen `[ ]` und einem Link auf `tasks/task-X.Y-.../00-konzept.md` ersetzt.

### Schritt 5: Ausführung durch Sub-Agenten
- Ein Sub-Agent übernimmt **einen Step** nach dem anderen.
- Er schreibt den Code, führt die angegebenen Tests aus (inkl. Edge Cases) und zieht betroffene Docs in `Docs/` nach.

### Schritt 6: Review & Abnahme durch Kontroll-Agenten (`review.md`)
- Ein separater Kontroll-Agent liest `00-konzept.md` und prüft den entstandenen Code sowie die Doku.
- Er führt die Testsuite aus (inkl. Edge Cases).
- Er erstellt oder aktualisiert `tasks/task-X.Y-.../review.md`.
- **Wichtig**: Bei erfolgreichem Review hakt der Kontroll-Agent den Punkt in `Docs/10-Roadmap.md` ab `[x]` und setzt den Status in `00-konzept.md` auf `DONE`.
