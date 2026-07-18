# Code-Standards & Projektstruktur

Dieses Dokument legt fest, wie der Code (sobald Meilenstein 1 beginnt, siehe 10-Roadmap.md) strukturiert und geschrieben wird. Der Code wird vollständig agentisch erzeugt – diese Regeln sind deshalb bewusst so konkret formuliert, dass ein Agent sie ohne Rückfrage befolgen kann, statt vage Prinzipien zu benennen.

## Sprache im Code

Code-Bezeichner (Klassen, Funktionen, Variablen, Modulnamen) werden **Englisch** geschrieben, auch wenn die Konzeptdokumente Deutsch sind – das folgt der Python-Konvention und funktioniert zuverlässiger bei agentisch generiertem Code. Deutsche Fachbegriffe aus den Docs werden in Docstrings/Kommentaren referenziert, wo das für die Nachvollziehbarkeit hilft (z. B. `class Store:  # Speicher, siehe 01-Kern-Domaenenmodell.md`).

| Konzept-Begriff (Docs, Deutsch) | Code-Bezeichner (Englisch) |
|---|---|
| Speicher | `Store` |
| Effekt | `Effect` |
| Baustein | `Component` (ein registrierter, kuratierter `Effect`) |
| Zeitstrahl | `Timeline` |
| Phase | `Phase` |
| Zielbedingung | `TargetCondition` |
| Plan | `Plan` |
| Simulationslauf | `SimulationRun` |
| Simulationsergebnis | `SimulationResult` |

## Grundsatz: einfacher Code statt Enterprise-Architektur

Die Codebasis bleibt bewusst klein und direkt lesbar. Das bedeutet konkret:

- **Early Returns statt verschachtelter Bedingungen.** Eine Funktion prüft Fehler-/Sonderfälle zuerst und kehrt sofort zurück (`if not valid: return`), statt den Hauptpfad in verschachtelte `if/else`-Blöcke einzuwickeln.
- **Niedrige zyklomatische Komplexität.** Faustregel: Eine Funktion sollte auf einen Bildschirm passen und nicht mehr als eine Verschachtelungsebene an Bedingungen/Schleifen haben. Wird eine Funktion unübersichtlich, wird sie in benannte Hilfsfunktionen zerlegt, nicht mit Kommentaren durchsetzt.
- **Geringe kognitive Last.** Ein Modul soll ohne Sprünge durch fünf Abstraktionsschichten verstehbar sein. Kommentare/Docstrings erklären das *Warum* (z. B. „Bestandsschutz gilt ab 1.1.2009, siehe 09-Quellen.md"), nicht das *Was* (das soll der Code selbst zeigen).
- **Keine vorzeitige Abstraktion.** Kein Interface/keine abstrakte Basisklasse, solange es nur eine einzige Implementierung gibt. Keine „Manager"-, „Factory"- oder „Helper"-Klassen ohne konkreten Grund. Keine Dependency-Injection-Frameworks. Wird ein zweiter Anwendungsfall (z. B. Meilenstein 5, zweite Domäne) tatsächlich eine zweite Implementierung brauchen, wird erst dann abstrahiert (Rule of Three: lieber zweimal duplizieren als beim ersten Mal falsch abstrahieren).
- **Standardbibliotheken statt Eigenbau.** Wo eine ausgereifte Standard- oder Kernbibliothek existiert (NumPy/SciPy für Zufallsziehungen und Vektorrechnung, Pydantic für Schema/Validierung, das offizielle MCP-Python-SDK für den Server), wird sie genutzt – kein selbstgeschriebener Ersatz für Dinge, die es bereits gut gelöst gibt.

## Verpflichtende Tests

Jedes nicht-triviale Feature (jede Funktion mit einer Fallunterscheidung, einer Formel oder einem Seiteneffekt auf einen Store) bekommt mindestens einen Unit-Test. Trivial – und damit ohne eigenen Test – sind reine Datencontainer ohne Logik (z. B. ein `Plan`, der nur andere Objekte hält) und einfache Weiterleitungen ohne eigene Berechnung.

- **Framework**: `pytest`.
- **Ein Testmodul je Quellmodul** (`tests/test_engine/test_store.py` für `src/compute_to_ai/engine/store.py` usw.), damit die Struktur der Tests die Struktur des Codes widerspiegelt.
- **Golden-/Referenztests** für alles mit einem von Hand nachrechenbaren Ergebnis (z. B. „100 €/Monat über 40 Jahre ohne Rendite = 48.000 €", später jeder Steuer-Baustein) – der wichtigste Baustein für Vertrauen in ein System, das größtenteils vom Agenten selbst gebaut wird.
- **Kein hartes Coverage-Ziel in Prozent.** Die Regel ist qualitativ (jedes nicht-triviale Feature hat einen Test), nicht ein Prozentwert, der am Ende nur mit sinnlosen Tests für triviale Getter erreicht wird.

## Projektstruktur

```
ComputeToAi/
├── CLAUDE.md
├── Docs/                                  # bestehende Konzeptdokumente (unverändert)
├── examples/                              # generisches Beispiel-Arbeitsverzeichnis inkl. Settings-Datei (siehe 02-Architektur-und-MCP.md)
├── pyproject.toml                         # Projekt-Metadaten und Dependencies
├── src/
│   └── compute_to_ai/
│       ├── engine/                        # Kern – kennt keine Domäne (siehe 01-Kern-Domaenenmodell.md)
│       │   ├── store.py                   # Store, Lot
│       │   ├── effect.py                  # Effect (roh), Component (Baustein-Basis)
│       │   ├── timeline.py                # Timeline, Phase
│       │   ├── plan.py                    # Plan
│       │   ├── simulation.py              # Simulationslauf-Ausführung, Monte-Carlo-Schleife
│       │   └── result.py                  # SimulationResult, Aggregation über Läufe
│       ├── features/
│       │   ├── finance/                   # Feature Finanzen (ab Meilenstein 3)
│       │   └── calculations/              # Feature Berechnungen (siehe 06-Feature-Berechnungen.md)
│       │       ├── dates.py               # Datums-/Altersarithmetik
│       │       ├── growth.py              # Zinseszins, Barwert, Rentenbarwert, Entnahmepläne
│       │       ├── loans.py               # Kreditvergleich, Tilgungspläne inkl. Sondertilgung
│       │       └── cashflows.py           # XIRR, Effektivzins (numerisches Root-Finding)
│       └── mcp/                           # MCP-Server-Adapter
│           ├── server.py                  # Server-Bootstrap, stdio-Transport, Logging-Konfiguration
│           ├── settings.py                # Settings-Datei laden (TOML → Pydantic), siehe 02-Architektur-und-MCP.md
│           └── tools/
│               ├── core_tools.py           # Kern-Tools (Plan/Store/Effect/Simulation)
│               ├── finance_tools.py        # Finanzen-Tools (ab Meilenstein 3)
│               └── calculation_tools.py    # Berechnungen-Tools, Präfix `calculations_`
└── tests/
    ├── test_engine/
    ├── test_features/
    └── test_mcp/
```

## Trennung der Verantwortlichkeiten (Separation of Concerns)

Drei Schichten, mit einer festen Abhängigkeitsrichtung:

1. **`compute_to_ai.engine`** kennt nur die generischen Kern-Begriffe (siehe 01). Es importiert **nichts** aus `compute_to_ai.features` oder `compute_to_ai.mcp`. Ein Umbau des Finanzen-Features darf den Kern nie zum Brechen bringen, weil der Kern von ihm gar nichts weiß.
2. **`compute_to_ai.features.*`** (z. B. `finance`, `calculations`) bauen auf `compute_to_ai.engine` auf (z. B. registrieren sie eigene `Component`-Bausteine) und sind **untereinander unabhängig** – `finance` importiert nichts aus `calculations` und umgekehrt. Ein neues Feature-Modul lässt sich ergänzen, ohne bestehende Feature-Module anzufassen.
3. **`compute_to_ai.mcp`** übersetzt MCP-Tool-Aufrufe in Aufrufe an `compute_to_ai.engine`/`compute_to_ai.features`, enthält selbst aber keine fachliche Logik – nur Ein-/Ausgabe-Mapping (Pydantic-Schemas für Tool-Parameter, Aufruf der eigentlichen Logik, Rückgabe strukturierter Ergebnisse).

Diese Aufteilung ist bewusst schlank gehalten (keine zusätzlichen Zwischenschichten wie „Repositories", „Services" oder „Domain Events") – genau die drei Schichten, die zur bereits getroffenen Kern/Feature/MCP-Trennung aus 00-Vision.md und 02-Architektur-und-MCP.md passen.

## Tooling

| Zweck | Wahl | Begründung |
|---|---|---|
| Paket-/Abhängigkeitsverwaltung | [uv](https://docs.astral.sh/uv/) | Ein einziges, schnelles Tool für Environment, Dependencies und Lockfile – ersetzt die in der Python-Welt sonst übliche Kombination aus mehreren Tools |
| Linting & Formatierung | [ruff](https://docs.astral.sh/ruff/) | Ein einziges, sehr schnelles Tool für beides, inkl. Komplexitäts-Regel (`C90`, mccabe) zur Kontrolle der zyklomatischen Komplexität |
| Tests | [pytest](https://docs.pytest.org/) | De-facto-Standard im Python-Ökosystem |
| Typüberprüfung | Type Hints überall, geprüft mit [pyright](https://microsoft.github.io/pyright/) im `strict`-Modus | Schnelles Feedback, fängt einen Teil der Fehler ab, bevor sie zur Laufzeit auffallen |
| Numerik/Simulation | NumPy, SciPy | Vektorisierte Monte-Carlo-Läufe, Standardbibliotheken der wissenschaftlichen Python-Welt |
| Schema/Validierung | Pydantic | Für Konfigurationsobjekte und MCP-Tool-Parameter |
| MCP-Server | offizielles MCP-Python-SDK | siehe 02-Architektur-und-MCP.md |

## Strenge: Warnungen sind Fehler

Der Code wird größtenteils agentisch erzeugt; die Werkzeugkette ist deshalb bewusst so scharf gestellt, dass Nachlässigkeiten sofort auffallen, statt sich unbemerkt anzuhäufen – das Python-Äquivalent zu `Option Explicit` oder „Compiler-Warnungen als Fehler". Konkret, jeweils konfiguriert in `pyproject.toml`:

- **`pyright` im `strict`-Modus** statt `basic`/`standard`: keine impliziten `Any`-Typen, jede Funktion vollständig typisiert.
- **`ruff` mit einem breiten Regel-Set** über die reine Formatierung hinaus, u. a. `ANN` (Typannotationen verpflichtend), `S` (Sicherheits-/Bandit-Regeln), `B` (häufige Bug-Muster), `T20` (kein `print()` – der MCP-Server spricht über stdout mit dem Agenten, ein versehentliches `print()` würde das Protokoll beschädigen), `PTH` (Pfade über `pathlib`), `DTZ` (zeitzonenbewusste Datums-/Zeitwerte), `ERA` (kein auskommentierter Code), `PERF`, `RET`, `SIM`, `TRY`, `RUF`. Die vollständige, gepflegte Liste steht in `pyproject.toml` unter `[tool.ruff.lint]`, nicht hier dupliziert (siehe `.agents/rules/living-documentation.mdc`).
- **`pytest` mit `filterwarnings = ["error"]`**: jede nicht abgefangene `DeprecationWarning` o. Ä. lässt den betroffenen Test fehlschlagen, statt nur eine unauffällige Zeile im Testlauf zu hinterlassen.

Ein Agent behandelt jede Warnung dieser drei Werkzeuge wie einen Fehler: beheben statt unterdrücken. Eine gezielte Unterdrückung (`# noqa`, `# pyright: ignore[...]`) ist nur zulässig, wenn die Regel auf ein bekanntes, unvermeidbares Framework-Muster trifft (Beispiel: `reportUnusedFunction` für per Decorator registrierte MCP-Tool-Funktionen, die nie direkt beim Namen aufgerufen werden) – nie, um schnell einen echten Fehler wegzuklicken.

## Code-Kommentare: keine Projektplanung im Code

Kommentare/Docstrings erklären das *Warum* einer aktuellen Design-Entscheidung (siehe oben, „Geringe kognitive Last"), verweisen dabei aber **nie** auf Projektplanungs-Artefakte – kein „Milestone 1 scope only", kein „siehe Docs/10-Roadmap.md Epic 1.4", kein „siehe Docs/08-Offene-Fragen.md", kein „kommt später". Solche Verweise veralten garantiert (siehe `.agents/rules/living-documentation.mdc`, das sich ausdrücklich auch auf Code-Kommentare bezieht) und gehören, wenn überhaupt, in die Roadmap oder die Commit-Message, nicht in den Code. Ein Verweis auf ein Konzept-/Architekturdokument (01–07, 09, 11) ist dagegen erlaubt und erwünscht, wenn er die Nachvollziehbarkeit einer *aktuellen* Design-Entscheidung verbessert (siehe `.agents/rules/language.mdc`).

Alle Tools sind bewusst so gewählt, dass möglichst wenige, weit verbreitete Werkzeuge möglichst viel abdecken (z. B. ruff statt separater Linter/Formatter/Import-Sorter), statt viele Spezialwerkzeuge zu kombinieren.
