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

- [x] Epic 2.1 – Liste der Rechenbausteine festgelegt: Datums-/Altersarithmetik, Zinseszins/Diskontierung (Einmalanlage, Sparraten-Endwert, Rentenbarwert), Kreditvergleich (siehe 06-Feature-Berechnungen.md)
- [x] Epic 2.2 – Rechenbausteine implementiert und per MCP angeboten (Tool-Präfix `calculations_`, siehe 02-Architektur-und-MCP.md)
- [x] Epic 2.3 – Beispiel-Workflow „Plausibilitätsprüfung eines Simulationsergebnisses" als Prompt (`Docs/prompts/finance_de/finanzberater.md`, Abschnitt „Prüfe Nutzereingaben und Ergebnisse auf Plausibilität")

## Meilenstein 3 – Feature Finanzen

**Ziel**: Das in 03–05 beschriebene Finanz-Domänenmodell ist auf dem Kern umgesetzt: Rendite/Korrelation, Steuer-Bausteine (inkl. Bestandsschutz), Verbindlichkeiten, Cash-Bucket, Lebensphasen. Für die zentralen Bausteine gibt es Referenz-/Golden-Testfälle mit von Hand nachgerechnetem Ergebnis.

**Leitprinzip**: Fast der gesamte fachliche Umfang reduziert sich auf eine kleine, feste Zahl generischer Kern-Effekt-Arten mit unterschiedlichem Vorzeichen und unterschiedlichen Parametern statt auf viele fachspezifische Sonderfälle (siehe „Effekt-Arten" in 01-Kern-Domaenenmodell.md) – Einkommen und Ausgabe sind derselbe Effekt-Typ, ebenso die Verzinsung einer Anlage und einer Verbindlichkeit. Das Finanz-Feature fügt darauf ausschließlich Namen, Parameter und ein paar wirklich eigenständige Berechnungen (Steuer, Cash-Bucket-Logik) hinzu. Epic 3.1 und 3.2 erweitern deshalb zunächst den domänenneutralen Kern (`compute_to_ai.engine`), erst ab Epic 3.3 entsteht fachlicher Finanz-Code (`compute_to_ai.features.finance`).

### Beispiel-Plan als roter Faden

Ein durchgängiges Beispiel, das möglichst viele Bausteine dieses Meilensteins gleichzeitig braucht – dient als Testfall und als Prüfung, ob die generische Modellierung wirklich trägt, nicht als Teil des Konzepts selbst (die Begriffe stehen abschließend in 03–05):

Anna, 20 Jahre, startet ins Berufsleben mit 5.000 € Cash und ohne Portfolio. Erwerbsphase 20–63, danach eine vierjährige Frühruhestandslücke bis zum gesetzlichen Rentenbeginn mit 67 (bewusst gewählt, um auch diese Phase abzudecken), Rentenphase bis Lebenserwartung 90. Gehalt 2.800 €/Monat netto mit 2 % jährlicher Steigerung; Lebenshaltung 1.600 €/Monat, wächst mit 2 % Inflation. Mit 25 ein Autokredit über 20.000 € (4 % Zins, 60 Monate Laufzeit). Mit 28 ein Hauskauf für 350.000 €: 70.000 € Eigenkapital als fixe Anschaffung aus dem Portfolio, 280.000 € als Hypothek (3,5 % Zins, 25 Jahre, mit Sondertilgungsoption). Portfolio 70 % Aktien-ETF (7 % erwartete Rendite, 15 % Volatilität) / 30 % Anleihen-ETF (3 % Rendite, 5 % Volatilität), Korrelation −0,2. Cash-Bucket mit 6 Monaten Notfallpuffer in der Erwerbsphase, 3 Jahren Entnahmehorizont in der Rentenphase. Gesetzliche Rente ab 67: 1.800 €/Monat, 1 % jährliche Anpassung, nachgelagert besteuert, KVdR/Pflegeversicherung abgezogen. Ziel: Endvermögen nie unter 0 bis Alter 90, ausgewertet über z. B. 5.000 Monte-Carlo-Läufe.

Das deckt ab: wachsende Einkommens-/Ausgabeneffekte, zwei parallele Verbindlichkeiten unterschiedlicher Laufzeit (davon eine mit Sondertilgung), eine große fixe Anschaffung, korrelierte Mehr-Anlageklassen-Rendite, alle vier Lebensphasen inkl. Frühruhestandslücke, Cash-Bucket mit phasenabhängiger Zielgröße, Kapitalertragsteuer inkl. Vorabpauschale, nachgelagerte Rentenbesteuerung inkl. Sozialabgaben, und eine Zielbedingung mit Monte-Carlo-Aggregation. Bewusst nicht abgedeckt (siehe 08-Offene-Fragen.md): Bestandsschutz-Lots vor 2009 (Anna ist dafür zu jung), Immobilienwertsteigerung, Partnerbeitrag.

- [x] **Epic 3.1 – Kern-Erweiterung: Effekt-Arten & Ausführungsmodell** (`compute_to_ai.engine`)
  - [x] `GrowingFixedEffect` löst `FixedEffect` ab: Betrag + Wachstumsrate je Schritt (Rate 0 entspricht dem bisherigen `FixedEffect`-Verhalten); deckt Einkommen, Ausgaben, Tilgungsraten, fixe Anschaffungen und Sondereinnahmen ab (siehe 01, „Effekt-Arten")
  - [x] `PercentageGrowthEffect`: Speicher-Saldo wächst je Schritt um eine feste Rate – deckt sowohl Zinsanfall einer Verbindlichkeit als auch eine deterministisch angenommene Kapitalrendite ab
  - [x] `CorrelatedReturnEffect`: wie oben, aber Rate wird je Lauf stochastisch gezogen, gemeinsam mit allen Effekten derselben benannten Korrelationsgruppe (multivariate Normalverteilung, Cholesky-Zerlegung – NumPy/SciPy werden hier erstmals als Dependency gebraucht, siehe 11-Code-Standards-und-Projektstruktur.md)
  - [x] `ComputedEffect`-Basis: kuratierte Python-Funktion statt Formel, läuft nach den drei Effekt-Arten oben im selben Schritt auf Basis der bereits aktualisierten Salden (siehe 01, Abschnitt „Reihenfolge & keine zirkulären Abhängigkeiten")
  - [x] Effekte optional auf einen Schrittbereich beschränkbar (aktiv ab/bis) – Grundlage für Phasenbindung in Epic 3.2
  - [x] Unit-Tests je Effekt-Art, inkl. Golden-Test für `PercentageGrowthEffect` gegen `calculations_future_value_lump_sum` (M2) als Referenz
- [x] **Epic 3.2 – Kern-Erweiterung: Phasen, Lot-Semantik, Monte-Carlo-Runner** (`compute_to_ai.engine`)
  - [x] `Phase` (Name, Start-/Endschritt) auf `Plan`/`Timeline`; `active_phases` auf Effekten referenziert Phasennamen statt eigener Schrittgrenzen
  - [x] `Lot` auf `Store` (Menge, Entstehungsschritt, Regelwerk-Version, Einstandspreis), FIFO-Verbrauch bei Abfluss (siehe 01, Speicher-Abschnitt)
  - [x] `run_monte_carlo(plan, num_runs)`: wiederholt den Einzellauf aus Meilenstein 1 mit je Lauf neu gezogenen stochastischen Effekten
  - [x] Aggregation über alle Läufe: Perzentile des Endsaldos, Ruin-Wahrscheinlichkeit, Verteilung des Ruin-Zeitpunkts (Ruin selbst läuft weiter statt abzubrechen, siehe 01)
  - [x] Unit-Tests für Phasen-Lookup, FIFO-Verbrauch, Monte-Carlo-Aggregation (bekannte Verteilung mit erwartbaren Perzentilen)
- [x] **Epic 3.3 – Bausteine: Einkommen, Ausgaben, Anschaffungen** (`compute_to_ai.features.finance`)
  - [x] Einkommensstrom = `GrowingFixedEffect` (positiv), phasengebunden (z. B. Gehalt nur in der Erwerbsphase)
  - [x] Ausgabe = `GrowingFixedEffect` (negativ), Wachstumsrate = Inflation; beliebig viele, frei benannt statt fester Kategorien (siehe 03)
  - [x] Fixe Anschaffung / Sondereinnahme = `GrowingFixedEffect` mit Rate 0 auf genau einen Schritt beschränkt
  - [x] Flexible Anschaffung = `ComputedEffect` mit Referenzpfad-Vergleich + Glidepath (siehe 04); konkrete Referenzpfad-Kurve bleibt offen (siehe 08-Offene-Fragen.md)
- [x] **Epic 3.4 – Bausteine: Verbindlichkeiten** (`compute_to_ai.features.finance`)
  - [x] Eigener `Store` je Verbindlichkeit (Restschuld, positiv geführt – dieselbe Vorzeichenkonvention wie `calculations_loan_remaining_balance` aus M2)
  - [x] `PercentageGrowthEffect` (Zins, positiv) + `GrowingFixedEffect` Rate 0 (Tilgung, negativ auf Verbindlichkeits-Store **und** auf Cash) je Verbindlichkeit
  - [x] Rate wird nicht neu hergeleitet, sondern über `calculations_loan_monthly_payment` (M2) berechnet und als Parameter übergeben
  - [x] Sondertilgung als optionaler `ComputedEffect`; `calculations_loan_amortization_schedule_with_extra_payments` (M2) dient als Referenz für Golden-Tests. Die konkrete Entscheidungsregel Sondertilgung vs. Investition bleibt eine offene Kalibrierungsfrage (siehe 04 und 08-Offene-Fragen.md) – für M3 reicht ein Baustein, der eine vom Nutzer vorgegebene Regel (fester Schwellenwert Kreditzins vs. erwartete Rendite) anwendet
- [x] **Epic 3.5 – Bausteine: Kapitalanlage** (`compute_to_ai.features.finance`)
  - [x] Anlageklasse = `CorrelatedReturnEffect` mit Korrelationsgruppe `"anlageklassen"`, je Anlageklasse ein Sub-Speicher oder Allokationsanteil
  - [x] Portfolio = `Store` mit Lot-Semantik; Allokation/Rebalancing als eigener `ComputedEffect`
  - [x] Cash-Bucket = eigener `Store` + `ComputedEffect` mit der Drei-Komponenten-Zielgröße aus 04 (Einkommensausfallpuffer, Nahsicht, Entnahmepuffer), phasenabhängige Notfallpuffer-Monate, Vorrang-Auffüllung vor Portfolio-Investition, spiegelbildliche Entnahme-Priorität (siehe 04)
- [x] **Epic 3.6 – Bausteine: Steuern** (`compute_to_ai.features.finance`)
  - [x] Abgeltungsteuer, Sparerpauschbetrag, Vorabpauschale, Teilfreistellung, Bestandsschutz (Lot-Regelwerk-Version) als `ComputedEffect` auf Portfolio-Lots
  - [x] Nachgelagerte Rentenbesteuerung inkl. KVdR/Pflegeversicherung (GKV/PKV als Parameter, siehe 05) als `ComputedEffect` on Renten-Einkommensstrom
  - [x] Konkrete Sätze aus 05-Feature-Finanzen-Parameter.md, mit Stand-Jahr-Vermerk und Beleg in 09-Quellen.md (Quellentreue-Pflicht, siehe CLAUDE.md)
- [x] **Epic 3.7 – Lebensphasen & Rentenübergang** (`compute_to_ai.features.finance`)
  - [x] Standard-Phasenmodell (Ausbildung optional, Erwerbsphase, ggf. Frühruhestandslücke, Rentenphase) als vorkonfigurierbare Phasenliste (`build_standard_life_phases`)
  - [x] Erwerbsende und gesetzlicher Rentenbeginn als separate Phasengrenzen, lösen den Wechsel Einkommensstrom → gesetzliche Rente aus (über `active_phases`/`start_step` der jeweiligen `GrowingFixedEffect`-Bausteine, kein eigener Mechanismus nötig)
  - [x] Rentenabschlag (0,3 %/Monat vorzeitig, max. 14,4 %) bzw. -zuschlag (0,5 %/Monat Aufschub) als einmalige Anpassung der Renten-`GrowingFixedEffect`-Basis bei Aktivierung (`add_statutory_pension`)
- [x] **Epic 3.8 – MCP-Tools, Zielbedingung, Referenz-/Golden-Tests**
  - [x] Tool-Präfix `finance_*` (siehe 02-Architektur-und-MCP.md): je Baustein ein Tool zum Hinzufügen/Konfigurieren (`finance_add_income_stream`, `finance_add_expense`, `finance_add_fixed_acquisition`, `finance_add_flexible_acquisition`, `finance_add_liability`, `finance_add_asset_class`, `finance_set_correlation_matrix`, `finance_add_portfolio_rebalancing`, `finance_add_cash_bucket`, `finance_add_tax_manager`, `finance_add_statutory_pension`, `finance_set_life_phases`); dazu der zustandslose Schnell-Check `finance_calculate_pension_adjustment` (Rentenabschlag/-zuschlag ohne Plan)
  - [x] Tool zum Start eines Monte-Carlo-Laufs (`finance_run_monte_carlo`) und zur Abfrage des aggregierten Ergebnisses (`finance_get_monte_carlo_result`)
  - [x] Zielbedingung konfigurierbar über `finance_set_target_condition` (Zielvermögen als `ruin_stores`/`ruin_threshold`, bereits vorhandener Kern-Mechanismus); Ziel-Erfolgswahrscheinlichkeit ist keine Plan-Konfiguration, sondern ergibt sich aus `1 - ruin_probability` im Monte-Carlo-Ergebnis
  - [x] Golden-Tests mit von Hand nachrechenbarem Ergebnis je Baustein (Tax, Cash-Bucket, Liability, Cashflow, Pension – siehe `tests/test_features/test_finance/`)
  - [x] End-to-End-Test über den vollständigen Beispiel-Plan (Anna) per echtem MCP-Tool-Aufruf (`tests/test_mcp/test_finance_tools_e2e.py`)
- [x] **Epic 3.9 – Pfad-Audit: instrumentiertes Ledger für repräsentative Pfade**
  - [x] Optional pro Lauf einschaltbares Ledger im Kern (`compute_to_ai.engine`): je Zeitschritt, welcher Effekt welchen Speicher um welchen Betrag verändert hat, plus die nach Laufende verbliebenen Parameter-Zustände jedes berechneten Effekts (siehe 01-Kern-Domaenenmodell.md, „Ledger")
  - [x] `core_run_path_audit`: führt eine Monte-Carlo-Simulation aus und instrumentiert anschließend nur wenige repräsentative Pfade (Perzentil-Treffer plus deterministischer Referenzlauf) statt jeden Lauf
  - [x] Finanz-Interpretation des Ledgers (`compute_to_ai.features.finance.path_audit`): Klassifikation in sechs Kategorien (Einnahmen, Ausgaben, Steuern, Rendite, Umschichtungen, Saldo) und ein Event-Log (Phasenübergang, Verbindlichkeit getilgt, Anschaffung ausgelöst) – siehe 04-Feature-Finanzen-Methodik.md, „Pfad-Audit und Plausibilitätsprüfung"
  - [x] Tools `finance_get_path_category_series` und `finance_get_path_event_log`
- [ ] **Epic 3.10 – Automatisierte Plausibilitäts-Hinweise (`finance_audit_plan`) & Pfad-Audit-Detailabfragen**

  Ergänzt Epic 3.9 um zwei Dinge: (a) automatisiert erkannte, aber nicht hart fehlerhafte Auffälligkeiten in einem Plan, und (b) zwei Drill-down-Tools, die beim manuellen Auditieren eines konkreten Plans fehlten (siehe e2e-Test-Notizen, in denen ein doppelt gezahltes Einkommen im Übergangsjahr Erwerbsphase → Rente nur durch Python-Code auf der Kommandozeile statt per MCP-Tool gefunden werden konnte).

  - [x] **Abgrenzung zu „Verifikation & Plausibilität – kein eigenes Feature"** (02-Architektur-und-MCP.md, Abschnitt gleichen Namens): jenes Prinzip gilt für Größenordnungs-/Fachwissens-Urteile über ein Simulationsergebnis („ist 3 Mio. € Endvermögen plausibel, ist 40 % erwartete Rendite realistisch?") und bleibt emergentes, im Prompt geführtes Agenten-Verhalten (siehe `Docs/prompts/finance_de/finanzberater.md`). `finance_audit_plan` prüft dagegen ausschließlich hart und eindeutig entscheidbare strukturelle/logische Konsistenz der Plan-Konfiguration und ihrer tatsächlichen Ausführung – keine Schwellenwert-Heuristiken, kein Fachwissen nötig. Docs/02 wurde um einen Satz ergänzt, der diese Abgrenzung explizit macht, statt das bestehende Prinzip zu widersprechen.
  - [x] **Datengrundlage ist der Pfad-Audit, nicht die statische Plan-Konfiguration**: `finance_audit_plan(plan_name, path="deterministic")` setzt auf dem Ledger eines zuvor mit `core_run_path_audit` erzeugten Pfads auf (wie `finance_get_path_category_series`/`finance_get_path_event_log`).
  - [x] **Rückgabeform**: eine flache Liste von Hinweis-Objekten (`step`, `message`), keine Exceptions/harten Fehler – der Nutzer kann jede Auffälligkeit bewusst gewählt haben.
  - [x] Erste konkrete Prüfregeln implementiert (`compute_to_ai.features.finance.path_audit.audit_plan`, Liste bei Bedarf erweiterbar):
    - Zwei oder mehr Einnahmen-Kategorie-Ledger-Einträge treffen im selben Schritt denselben Speicher (genau der auslösende Praxisfall: Gehalt und gesetzliche Rente überschneiden sich am Übergang Erwerbsphase → Rentenphase)
    - Eine aktive Phase, in der über ihre gesamte Dauer kein Einnahmen-Kategorie-Eintrag auf einem Zielbedingungs-Speicher (`ruin_stores`) auftritt
    - Ein Ausgaben-Effekt mit `inflation_rate=0.0`, während gleichzeitig ein aktiver Einkommens-Effekt mit `growth_rate>0` in derselben Phase existiert (oder umgekehrt) – Portierung des bislang nur als Prompt-Hinweis vorhandenen „Trend-Check" (siehe `Docs/prompts/finance_de/finanzberater.md`) in eine Code-Prüfung
    - Ein Speicher, der über den gesamten Zeitstrahl von keinem Effekt berührt wird (verwaister Speicher)
    - Eine Verbindlichkeit, deren Speicher-Saldo bis zum Ende des Zeitstrahls nicht 0 erreicht
  - [x] `core_get_path_step_ledger(plan_name, path, step)`: liefert die rohen `LedgerEntry`-Einträge (Effekt, Speicher, Delta) eines einzelnen Zeitschritts eines instrumentierten Pfads – Drill-down-Ergänzung zu `finance_get_path_category_series`, wenn eine Kategoriesumme selbst erklärungsbedürftig ist (z. B. warum „Einnahmen" in einem bestimmten Schritt ungewöhnlich hoch ausfällt). `core_*`-Präfix statt des ursprünglich skizzierten `finance_*` – das rohe Ledger selbst ist wie `computed_effect_final_states` ein domänenneutrales Kern-Konzept (siehe 01-Kern-Domaenenmodell.md, „Ledger"), die Finanz-Interpretation liefert erst `finance_get_path_category_series`.
  - [x] `core_get_path_computed_states(plan_name, path)`: liefert `computed_effect_final_states` (die nach Laufende verbliebenen Parameter-Zustände jedes berechneten Effekts, z. B. ob eine flexible Anschaffung ausgelöst wurde) eines instrumentierten Pfads – bislang nur intern von `compute_category_series`/`build_event_log` genutzt, nicht direkt per MCP abrufbar.
  - [ ] Ein Prompt-Hinweis in `Docs/prompts/finance_de/finanzberater.md`, `finance_audit_plan` nach jedem `core_run_path_audit` als festen Schritt auszuführen und die zurückgegebenen Hinweise dem Nutzer verständlich vorzulegen (nicht nur roh durchzureichen)

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

Regimeabhängige Korrelationsmodelle, Mehrgeräte-/Mehrsitzungs-Konsistenz der lokalen Speicherung, weitere Feature-Module, Vertiefung der in 08-Offene-Fragen.md verbliebenen fachlichen Detailfragen. Denkbar auch: proaktive, marktsignalgetriebene Portfolio-Verkäufe zur Cash-Bucket-Auffüllung (z. B. bei Allzeithochs oder nach überdurchschnittlichen Renditephasen) statt nur regelbasiert nach Zielgröße - **ausdrücklich mit dem Vorbehalt, dass kurzfristiges Markttiming empirisch nicht robust vorhersagbar ist** (Effizienzmarkthypothese); eine mögliche Umsetzung müsste diesen Vorbehalt im Nutzer-Prompt/Ergebnis transparent machen, statt als empfohlene Standardstrategie zu erscheinen.
