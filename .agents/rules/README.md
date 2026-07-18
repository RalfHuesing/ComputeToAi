# Agent-Regeln

Dieses Verzeichnis enthält die Arbeitsregeln für KI-Coding-Agents in diesem Repo, tool-neutral im `.mdc`-Format (Markdown mit YAML-Frontmatter: `description`, optional `globs`, `alwaysApply`). Das Format folgt der von mehreren Agent-Tools (u. a. Cursor) genutzten Konvention, damit sich diese Regeln bei Bedarf ohne Umformulierung an weitere Agents anbinden lassen.

**Dieses Repo wird bewusst mit mehreren Agenten entwickelt** (Claude Code, ggf. weitere) – nicht nur mit einem. Regeln hier sind deshalb agent-neutral formuliert. `CLAUDE.md` im Repo-Root bindet diese Dateien für Claude Code per `@`-Import ein; andere Agents lesen dieses Verzeichnis direkt oder über ihre eigene, tool-spezifische Einstiegsdatei, die hierher verweist.

**Quelle der Wahrheit ist `Docs/`**: Diese Regeln sind aus den Konzeptdokumenten abgeleitet (insbesondere `Docs/11-Code-Standards-und-Projektstruktur.md`), nicht umgekehrt. Bei Widerspruch gilt `Docs/`; diese Dateien dann entsprechend nachziehen.

## Dateien

| Datei | Inhalt |
|---|---|
| [language.mdc](language.mdc) | Sprachregeln: Deutsch für Kommunikation/Docs, Englisch für Code |
| [proactive-questions.mdc](proactive-questions.mdc) | Proaktiv nachfragen bei echten Entscheidungen statt eigenmächtig loszulegen |
| [sources-and-concept.mdc](sources-and-concept.mdc) | Quellentreue, Konzept-vor-Code, Umgang mit offenen Fragen |
| [living-documentation.mdc](living-documentation.mdc) | Doku beschreibt nur den Ist-Stand, wächst automatisch mit |
| [code-standards.mdc](code-standards.mdc) | Code-Stil, Architektur-Grundsätze, Projektstruktur (sobald Code entsteht) |
| [mcp-server-architecture.mdc](mcp-server-architecture.mdc) | MCP-Server: Transport, Selbstbeschreibung, Settings, Arbeitsverzeichnis, Logging |
| [testing.mdc](testing.mdc) | Testpflicht für nicht-trivialen Code |
| [git-workflow.mdc](git-workflow.mdc) | Vollagentische Entwicklung, Auto-Commits, Commit-Konventionen |
| [environment.mdc](environment.mdc) | Windows-Entwicklungsumgebung, verfügbare Tools |
