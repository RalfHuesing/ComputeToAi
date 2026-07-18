# ComputeToAi

Generische Simulations-Engine (Speicher/Effekt/Zeitstrahl) mit dem Finanz-Feature „Ruhestandsplanung" als erstem, am weitesten ausgearbeitetem Anwendungsfall. Kein eigenes Frontend – Zugang ausschließlich über einen MCP-Server, angesprochen von einem KI-Agenten.

- **Fachliches Konzept**: [Docs/](Docs/README.md), beginnend mit [Docs/00-Vision.md](Docs/00-Vision.md)
- **Projekt-/Arbeitsregeln für Agenten**: [CLAUDE.md](CLAUDE.md) und [.agents/rules/](.agents/rules/README.md)

Aktueller Stand: In aktiver Entwicklung (Work in Progress). Die Kernkomponenten und Features werden schrittweise implementiert (siehe [Docs/10-Roadmap.md](Docs/10-Roadmap.md)).

## Verwendung und Integration (MCP-Server)

Dieses Projekt besitzt kein eigenes Frontend. Die Interaktion und Steuerung erfolgen ausschließlich über einen **Model Context Protocol (MCP) Server**, den du in einen KI-Agenten deiner Wahl integrierst.

### Voraussetzungen
1. **KI-Agent / IDE mit MCP-Unterstützung:** z. B. *Claude Code*, *Cursor*, *Windsurf* oder die *Claude Desktop App*.
2. **Lauffähiges Python-Projekt:** Der MCP-Server wird lokal über Python gestartet (am einfachsten via `uv`).

### Integration des MCP-Servers
Füge die folgende Konfiguration in dein Tool ein (z. B. in die globale MCP-Konfigurationsdatei):

```json
{
  "mcpServers": {
    "compute-to-ai": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "compute_to_ai.mcp.server"
      ],
      "env": {
        "COMPUTE_TO_AI_SETTINGS": "examples/settings.toml"
      }
    }
  }
}
```

> [!NOTE]
> Passe den Pfad in `COMPUTE_TO_AI_SETTINGS` an, um sicherzustellen, dass er auf deine Einstellungsdatei verweist, in welcher das Arbeitsverzeichnis für die Pläne festgelegt ist.

### Anwendung im Chat / Prompt
Sobald der MCP-Server erfolgreich verbunden ist, kannst du den Agenten direkt anweisen, das Tool zu nutzen. Ein typischer Einstiegs-Prompt sieht so aus:

> *„Nutze ausschließlich den ComputeToAi MCP-Server. Du bist mein Finanzberater. Wir erstellen jetzt einen langfristigen Finanzplan für mich.“*

Der Agent kann daraufhin selbstständig Pläne anlegen, Einnahmen, Ausgaben, Kredite, Steuern und Portfolios hinzufügen sowie die Monte-Carlo-Simulation starten und auswerten.