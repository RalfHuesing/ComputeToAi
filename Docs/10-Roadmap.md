# Roadmap

Eine konkrete, abhakbare Abfolge von Meilensteinen. Jeder Meilenstein gliedert sich in Epics; Meilenstein 1 ist bereits bis auf Task-Ebene heruntergebrochen, weitere Meilensteine werden erst kurz vor ihrem Start in derselben Tiefe konkretisiert (kein Sinn, Details für Meilenstein 4 schon jetzt festzuzurren). Technologie-Details siehe 02-Architektur-und-MCP.md und 11-Code-Standards-und-Projektstruktur.md.

## Meilenstein 1 – Kern-Prototyp lauffähig

**Ziel**: Der generische Kern (siehe 01-Kern-Domaenenmodell.md) steht in Python, ist über einen MCP-Server von einem Agenten ansprechbar, und kann den denkbar einfachsten Fall simulieren: 100 €/Monat sparen, 0 % Rendite, über 40 Jahre (480 Monate) → Endsaldo 48.000 €. Bewusst noch **nicht** Teil dieses Meilensteins: Zufallsziehungen, Korrelation, Steuern, Bausteine, Lot-Semantik, Phasen – das kommt erst mit Meilenstein 3 (Feature Finanzen).

- [x] **Epic 1.1 – Projekt-Setup**
  - [x] Python-Projektstruktur angelegt (src-Layout, siehe 11-Code-Standards-und-Projektstruktur.md)
  - [x] Dependency-/Tooling-Setup (uv, ruff, pytest) lauffähig
  - [x] Ein minimaler MCP-Server ist von einem Agenten (Claude Code/Cowork) ansprechbar (die 5 Kern-Tools aus Epic 1.4 erfüllen das, kein separates Test-Tool nötig)
- [x] **Epic 1.2 – Kern-Datenmodell**
  - [x] `Store` (Speicher): Saldo (Lot-Semantik kommt mit Meilenstein 3, Feature Finanzen)
  - [x] `Effect` (Effekt): für M1 eine einzige, fixe (nicht-stochastische) Effekt-Art (`FixedEffect`); gemeinsame Basisabstraktion und Component/Baustein-Katalog kommen mit Meilenstein 3, sobald eine zweite Effekt-Art existiert
  - [x] `Timeline` (Zeitstrahl): Schrittanzahl (`step_count`); Startzeitpunkt kommt mit den Phasen in Meilenstein 3
  - [x] `Plan`: Container aus Store(s), Effect(s), Timeline, mit Schema-Version
- [x] **Epic 1.3 – Einfache Simulationsschleife**
  - [x] Zeitschritt-Iteration über die Timeline
  - [x] Der fixe Effekt wirkt je Zeitschritt auf seinen Store
  - [x] Saldo-Fortschreibung über alle Zeitschritte, Endsaldo und Zeitreihe abrufbar
- [x] **Epic 1.4 – MCP-Anbindung des Kerns**
  - [x] Tool: Plan anlegen (`create_plan`)
  - [x] Tool: Store zu einem Plan hinzufügen (`add_store`)
  - [x] Tool: Effect zu einem Store hinzufügen (`add_effect`)
  - [x] Tool: Simulation starten (`run_plan_simulation`)
  - [x] Tool: Ergebnis (Endsaldo, optional Zeitreihe) abfragen (`get_result`)
- [x] **Epic 1.5 – Tests & Verifikation**
  - [x] Unit-Tests für `Plan` (Store-Lookup) und die Simulationsschleife
  - [x] Golden-Test: 100 €/Monat, 0 % Rendite, 40 Jahre → Endsaldo exakt 48.000 €
  - [x] Derselbe Fall zusätzlich als End-to-End-Test über den MCP-Tool-Aufruf per echtem stdio-Subprozess (nicht nur auf reiner Python-Ebene)

**Abschlusskriterium**: Ralf kann über einen Agenten per MCP einen Plan mit einem Store und einem fixen monatlichen Zufluss-Effekt anlegen, 40 Jahre simulieren lassen und bekommt 48.000 € zurück – reproduzierbar und durch Tests abgesichert.

## Meilenstein 2 – Feature Berechnungen

**Ziel**: Eine erste konkrete Liste an Rechenbausteinen ist festgelegt und implementiert (deterministisch, zustandslos, kein eigener Simulationslauf, siehe 06-Feature-Berechnungen.md); ein Prompt-/Workflow-Muster existiert, mit dem ein Agent diese Bausteine selbstständig zur Plausibilitätsprüfung eines Simulationsergebnisses kombiniert. Vor Feature Finanzen eingeordnet, weil die Berechnungen-Tools deutlich einfacher sind (reine Funktionen ohne Steuer-/Korrelationslogik oder Zustand) und schneller nutzbares Werkzeug liefern.

- [ ] Epic 2.1 – Liste der Rechenbausteine festlegen (siehe 08-Offene-Fragen.md)
- [ ] Epic 2.2 – Rechenbausteine implementieren und per MCP anbieten (Tool-Präfix `calculations_`, siehe 02-Architektur-und-MCP.md)
- [ ] Epic 2.3 – Beispiel-Workflow „Plausibilitätsprüfung eines Simulationsergebnisses" als Prompt/Skill

## Meilenstein 3 – Feature Finanzen

**Ziel**: Das in 03–05 beschriebene Finanz-Domänenmodell ist auf dem Kern umgesetzt: Rendite/Korrelation, Steuer-Bausteine (inkl. Bestandsschutz), Verbindlichkeiten, Cash-Bucket, Lebensphasen. Für die zentralen Bausteine gibt es Referenz-/Golden-Testfälle mit von Hand nachgerechnetem Ergebnis. Epics werden bei Start dieses Meilensteins auf Task-Ebene heruntergebrochen.

- [ ] Epic 3.1 – Stochastische Effekte & Korrelation (Anlageklassen-Renditen)
- [ ] Epic 3.2 – Steuer-Bausteine (Abgeltungsteuer, Vorabpauschale, Teilfreistellung, Bestandsschutz)
- [ ] Epic 3.3 – Verbindlichkeiten (Tilgungsplan, Sondertilgung)
- [ ] Epic 3.4 – Cash-Bucket (drei Komponenten, Auffüll-Logik)
- [ ] Epic 3.5 – Lebensphasen & Rentenübergang (Erwerbsende/Rentenbeginn, Abschlag/Zuschlag, KVdR/Pflegeversicherung)
- [ ] Epic 3.6 – Referenz-/Golden-Tests für alle obigen Bausteine

## Meilenstein 4 – Baustein-Katalog & Regelwerk-Templates

**Ziel**: Der Mechanismus für versionierte Regelwerk-Templates (z. B. jährliche Steuerrechtsänderungen) ist umgesetzt, inklusive Bestandsschutz-Handling und einem Vertrauensmodell für extern geladene Templates.

- [ ] Epic 4.1 – Regelwerk-Template-Format und Ladeprozess
- [ ] Epic 4.2 – Bestandsschutz-Konsistenz bei Regelwerk-Wechsel
- [ ] Epic 4.3 – Vertrauens-/Prüfmechanismus für Templates (Testfälle, Diff-Vorschau)

## Meilenstein 5 – Generizitäts-Probe an einer zweiten Domäne

**Ziel**: Testweise Umsetzung eines zweiten, deutlich andersartigen Anwendungsfalls (z. B. Ausdauersport- oder Startup-Runway-Simulation) auf demselben Kern, um zu prüfen, ob die generische Architektur trägt.

- [ ] Epic 5.1 – Zweite Domäne auswählen und Speicher/Effekte modellieren
- [ ] Epic 5.2 – Kern-Anpassungen dokumentieren, falls die Domäne finanzspezifische Annahmen im Kern aufdeckt

## Meilenstein 6 – Weitere Ausbaustufen (später, unverbindlich)

Regimeabhängige Korrelationsmodelle, Mehrgeräte-/Mehrsitzungs-Konsistenz der lokalen Speicherung, weitere Feature-Module, Vertiefung der in 08-Offene-Fragen.md verbliebenen fachlichen Detailfragen.
