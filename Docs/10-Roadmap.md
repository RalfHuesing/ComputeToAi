# Roadmap

Eine konkrete, abhakbare Abfolge von Meilensteinen. Jeder Meilenstein gliedert sich in Epics; Meilenstein 1 ist bereits bis auf Task-Ebene heruntergebrochen, weitere Meilensteine werden erst kurz vor ihrem Start in derselben Tiefe konkretisiert (kein Sinn, Details für Meilenstein 4 schon jetzt festzuzurren). Technologie-Details siehe 02-Architektur-und-MCP.md und 11-Code-Standards-und-Projektstruktur.md.

## Meilenstein 1 – Kern-Prototyp lauffähig

**Ziel**: Der generische Kern (siehe 01-Kern-Domaenenmodell.md) steht in Python, ist über einen MCP-Server von einem Agenten ansprechbar, und kann den denkbar einfachsten Fall simulieren: 100 €/Monat sparen, 0 % Rendite, über 40 Jahre (480 Monate) → Endsaldo 48.000 €. Bewusst noch **nicht** Teil dieses Meilensteins: Zufallsziehungen, Korrelation, Steuern, Bausteine, Lot-Semantik, Phasen – das kommt erst mit Meilenstein 2.

- [ ] **Epic 1.1 – Projekt-Setup**
  - [ ] Python-Projektstruktur angelegt (src-Layout, siehe 11-Code-Standards-und-Projektstruktur.md)
  - [ ] Dependency-/Tooling-Setup (uv, ruff, pytest) lauffähig
  - [ ] Ein minimaler MCP-Server ist von einem Agenten (Claude Code/Cowork) ansprechbar (ein einziges Test-Tool reicht)
- [ ] **Epic 1.2 – Kern-Datenmodell**
  - [ ] `Store` (Speicher): Saldo, optional Liste datierter Lots
  - [ ] `Effect` (Effekt): Basisabstraktion für einen Zu-/Abfluss auf einen Store; für M1 genügt eine einzige, fixe (nicht-stochastische) Effekt-Art
  - [ ] `Timeline` (Zeitstrahl): Dauer, Schrittweite
  - [ ] `Plan`: Container aus Store(s), Effect(s), Timeline
- [ ] **Epic 1.3 – Einfache Simulationsschleife**
  - [ ] Zeitschritt-Iteration über die Timeline
  - [ ] Der fixe Zufluss-Effekt wirkt je Zeitschritt auf einen Store
  - [ ] Saldo-Fortschreibung über alle Zeitschritte, Endsaldo abrufbar
- [ ] **Epic 1.4 – MCP-Anbindung des Kerns**
  - [ ] Tool: Plan anlegen
  - [ ] Tool: Store zu einem Plan hinzufügen
  - [ ] Tool: Effect zu einem Store hinzufügen
  - [ ] Tool: Simulation starten
  - [ ] Tool: Ergebnis (Endsaldo, optional Zeitreihe) abfragen
- [ ] **Epic 1.5 – Tests & Verifikation**
  - [ ] Unit-Tests für `Store`, `Effect`, `Timeline`, `Plan`
  - [ ] Golden-Test: 100 €/Monat, 0 % Rendite, 40 Jahre → Endsaldo exakt 48.000 €
  - [ ] Derselbe Fall zusätzlich als End-to-End-Test über den MCP-Tool-Aufruf (nicht nur auf reiner Python-Ebene)

**Abschlusskriterium**: Ralf kann über einen Agenten per MCP einen Plan mit einem Store und einem fixen monatlichen Zufluss-Effekt anlegen, 40 Jahre simulieren lassen und bekommt 48.000 € zurück – reproduzierbar und durch Tests abgesichert.

## Meilenstein 2 – Feature Finanzen

**Ziel**: Das in 03–05 beschriebene Finanz-Domänenmodell ist auf dem Kern umgesetzt: Rendite/Korrelation, Steuer-Bausteine (inkl. Bestandsschutz), Verbindlichkeiten, Cash-Bucket, Lebensphasen. Für die zentralen Bausteine gibt es Referenz-/Golden-Testfälle mit von Hand nachgerechnetem Ergebnis. Epics werden bei Start dieses Meilensteins auf Task-Ebene heruntergebrochen.

- [ ] Epic 2.1 – Stochastische Effekte & Korrelation (Anlageklassen-Renditen)
- [ ] Epic 2.2 – Steuer-Bausteine (Abgeltungsteuer, Vorabpauschale, Teilfreistellung, Bestandsschutz)
- [ ] Epic 2.3 – Verbindlichkeiten (Tilgungsplan, Sondertilgung)
- [ ] Epic 2.4 – Cash-Bucket (drei Komponenten, Auffüll-Logik)
- [ ] Epic 2.5 – Lebensphasen & Rentenübergang (Erwerbsende/Rentenbeginn, Abschlag/Zuschlag, KVdR/Pflegeversicherung)
- [ ] Epic 2.6 – Referenz-/Golden-Tests für alle obigen Bausteine

## Meilenstein 3 – Feature Berechnungen

**Ziel**: Eine erste konkrete Liste an Rechenbausteinen ist festgelegt und implementiert; ein Prompt-/Workflow-Muster existiert, mit dem ein Agent diese Bausteine selbstständig zur Plausibilitätsprüfung eines Simulationsergebnisses kombiniert.

- [ ] Epic 3.1 – Liste der Rechenbausteine festlegen (siehe 08-Offene-Fragen.md)
- [ ] Epic 3.2 – Rechenbausteine implementieren und per MCP anbieten
- [ ] Epic 3.3 – Beispiel-Workflow „Plausibilitätsprüfung eines Simulationsergebnisses" als Prompt/Skill

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
