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
- [x] **Epic 3.10 – Automatisierte Plausibilitäts-Hinweise (`finance_audit_plan`) & Pfad-Audit-Detailabfragen**

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
  - [x] Ein Prompt-Hinweis in `Docs/prompts/finance_de/finanzberater.md`, `finance_audit_plan` nach jedem `core_run_path_audit` als festen Schritt auszuführen und die zurückgegebenen Hinweise dem Nutzer verständlich vorzulegen (nicht nur roh durchzureichen)

- [x] **Epic 3.11 – Ergonomie & Plausibilität: Beschreibungen, Kaufkraftbereinigung, Planvergleich, Perzentilkurven**

  Vier miteinander verwandte Ergonomie- und Interpretierbarkeits-Features, die als offene Fragen in 08-Offene-Fragen.md gesammelt und dann gesamthaft umgesetzt wurden.

  - [x] **Optionale Freitext-Beschreibungen (`description`):** `Plan`, `Store`, `BaseEffect` (und alle Unterklassen) und `Phase` erhalten ein optionales Feld `description: str | None = None`. Alle MCP-Add-Tools (z. B. `finance_add_income_stream`, `finance_add_store`, `finance_set_life_phases`) akzeptieren und persistieren den Parameter. Das LLM kann dadurch die fachliche Intention hinter einem Posten lesen (z. B. *„Wohnen = Miete, Strom, Gas"* für eine Pauschale) und gezielte Rückfragen des Nutzers beantworten.
  - [x] **Kaufkraftbereinigung (`granularity="annual_real"` / `"monthly_average_real"`):** `finance_get_path_category_series` akzeptiert nun zwei zusätzliche Granularitäts-Modi. Alle Cashflow-Kategorien **und** Speicher-Salden werden auf den Schritt `t` durch `(1 + inflation_rate)^t` dividiert, wobei die Inflationsrate pfadspezifisch aus dem Plan (Cash-Bucket-Manager oder Lebenshaltungs-Effekt) ermittelt wird. Dadurch erhält das LLM direkt kaufkraftbereinigte Monatswerte, die der Nutzer intuitiv einordnen kann.
  - [x] **Plan-Vergleichs-Tool (`finance_compare_plans`):** Neues MCP-Tool und Feature-Modul `compare.py`. Liefert (1) ein Konfigurations-Delta (Stores, Effekte, Phasen: hinzugefügt / entfernt / geändert mit konkreten Vorher-Nachher-Werten) und (2) ein Simulations-Delta (Differenz der Ruinwahrscheinlichkeit sowie der Endvermögens-Perzentile p10/p50/p90 der Ruin-Stores). Bei fehlenden MC-Ergebnissen oder unterschiedlichen Timeline-Längen werden strukturierte Warnungen ausgegeben statt harter Fehler.
  - [x] **Perzentil-Kurven-Tool (`finance_get_percentile_curves`):** Neues MCP-Tool. Liest das `PathAuditResult` und klassifiziert alle Plan-Stores in `liquid` (Cash-Buckets), `invested` (Anlageklassen mit `CorrelatedReturnEffect`) und `liabilities` (über `liability_manager`). Gibt pro Pfad (`p10`, `p50`, `p90`, `deterministic`) und Schritt die aggregierten Salden sowie `total_net = liquid + invested − liabilities` zurück – maximale Token-Effizienz für Chart-Daten.
  - [x] Tests: `tests/test_features/test_finance/test_compare.py` (neu, 11 Tests), `tests/test_features/test_finance/test_path_audit.py` (erweitert um 9 Tests für Inflation-Adjustment und `get_percentile_curves`)



## Meilenstein 4 – Live-Kurs-Integration & Mehrfach-Positionen je Anlageklasse

**Ziel**: Bereitstellung eines MCP-gestützten Live-Kurs-Abfragemechanismus zur automatisierten Initialisierung und Aktualisierung von Depotsalden im Plan-Datenmodell. Das System soll deutsche WKNs und internationale ISINs direkt auflösen und Kurse von deutschen Börsenplätzen beziehen, ohne dass der Nutzer diese manuell nachschlagen muss. Zusätzlich wird das Domänenmodell auf **mehrere Positionen je Anlageklasse** erweitert (siehe „Position" in 03-Feature-Finanzen-Domaenenmodell.md) – der reale Fall, dass historisch/steuerlich bedingt mehrere ETFs denselben Index abbilden, statt nur eine einzelne Stückzahl je Anlageklasse zu erlauben.

Die Live-Kurs-Abfrage und ihre Wiederverwendung fürs manuelle Depot-Update (Epics 4.1–4.5) sind bewusst **unabhängig** von der Mehrfach-Positionen-Erweiterung (Epics 4.6–4.10) umsetzbar: Beides funktioniert schon mit dem heutigen Modell (eine Anlageklasse = ein Speicher). Die dafür neu eingeführten ISIN/Stückzahl-Metadaten sind pro Speicher-Name abgelegt und werden unverändert weiterverwendet, sobald eine Anlageklasse aus mehreren Positionen (je eigenem Speicher) besteht.

### Technische Analyse (PoC-Erkenntnisse)
* **Datenquelle**: `Ariva.de` dient als stabile, kostenlose und anmeldefreie Abfragequelle. Sie löst sowohl WKNs (z. B. `ETF018`, `A0RPWH`, `A2N6CW`, `DBX1AU`, `A12GVR`, `A111X9`, `ETF019`) als auch ISINs (z. B. `LU2572257124`, `IE00B4L5Y983`, `IE00BFY0GT14`, `LU0322253906`, `IE00BTJRMP35`, `IE00BKM4GZ66`, `LU2573966905`) per 302-Redirect auf die jeweilige Instrumenten-Detailseite auf.
* **Börsenplatz-Steuerung**: Durch das Anhängen des Parameters `?boerse_id=X` an die *aufgelöste* URL können gezielt Realtime- oder Xetra-Kurse geladen werden. Die relevanten IDs sind:
  * **Xetra**: `boerse_id=45`
  * **Tradegate**: `boerse_id=131`
  * **Lang & Schwarz (L&S)**: `boerse_id=16`
  * **Gettex**: `boerse_id=207`
* **Implementierung**: Keine externen HTTP- oder Scraping-Bibliotheken nötig. Die Implementierung erfolgt robust über die Standardbibliothek (`urllib.request` mit geeignetem `User-Agent` sowie `re` zur Extraktion).

### Teilstrecke A – Live-Kurs-Abfrage und manuelles Depot-Update

- [x] **Epic 4.1 – Zustandsloses Live-Kurs-Tool (`finance_get_live_price`)**
  - [x] Implementierung der zweistufigen HTTP-Abfrage (Redirect auflösen -> URL mit `boerse_id` abfragen).
  - [x] Robustes Parsen des HTML-Header-Preises (`class="instrument-header-quote"`), der Währung (z. B. `EUR`) und des Zeitstempels (`class="instrument-header-last-time"`).
  - [x] Rückgabe eines strukturierten JSON-Objekts mit Name, ISIN, WKN, Kurs, Währung, Börse und Abfrage-Zeitstempel.
  - [x] Funktioniert unabhängig von einem Plan – direkt für beliebige Kursabfragen des Nutzers nutzbar, nicht nur für den Depot-Kontext.
- [x] **Epic 4.2 – Wertpapier-Metadaten je Speicher, persistiert neben dem Plan** (`compute_to_ai.features.finance`)
  - [x] Neues, ausschließlich Finance-seitiges Modell (z. B. `PositionMetadata`: ISIN/WKN, Stückzahl, Börsenplatz, Zeitstempel der letzten Kurs-Aktualisierung), je Speicher-Name in einer eigenen JSON-Datei neben `plan.json` gehalten – über den bereits vorhandenen generischen `save_result`/`load_result`-Mechanismus (`plan_storage.py`), ohne den domänenneutralen `Store`/`Plan` im Kern um finanzspezifische Felder zu erweitern.
  - [x] Ein Speicher ohne hinterlegte Metadaten bleibt unverändert rein manuell geführt (kein Zwang, jede Anlageklasse/Position darüber zu pflegen).
- [x] **Epic 4.3 – Depot-Initialisierung per Stückzahl (`finance_set_asset_shares`)**
  - [x] Neues MCP-Tool `finance_set_asset_shares(plan_name, store_name, shares, isin_or_wkn, exchange="Xetra")`, welches den Kurs abfragt, den Marktwert (`shares * price`) berechnet, den Startwert des Speichers setzt und den Metadaten-Eintrag aus Epic 4.2 anlegt.
- [x] **Epic 4.4 – Manueller Update-Check (`finance_update_plan_prices`)**
  - [x] Implementierung des Tools `finance_update_plan_prices(plan_name)`, das für jeden Speicher mit hinterlegten Metadaten (Epic 4.2) den aktuellen Kurs abfragt, den Saldo neu berechnet (`shares * aktueller Kurs`) und den Plan speichert (löst das Problem des „Alterns von Plänen" teil-automatisiert, siehe 08-Offene-Fragen.md).
  - [x] Ausschließlich auf expliziten Aufruf hin – **nicht** Teil von `core_run_simulation` oder `finance_run_monte_carlo`, damit ein Simulationslauf reproduzierbar bleibt und nicht heimlich mit aktualisierten Kursen rechnet.
- [x] **Epic 4.5 – Golden-Tests & Fehlerbehandlung (Teilstrecke A)**
  - [x] Offline-Tests (mit Mock-HTML-Dateien für die getesteten ETFs), um Parser-Stabilität bei HTML-Änderungen zu sichern.
  - [x] Online-Integrationstests zur kontinuierlichen Überwachung der Ariva-Schnittstelle.

### Teilstrecke B – Mehrfach-Positionen je Anlageklasse

- [x] **Epic 4.6 – Kern-Erweiterung: Mehrfach-Speicher-Ziel für Wachstums-/Renditeeffekte** (`compute_to_ai.engine`)
  - [x] `PercentageGrowthEffect` und `CorrelatedReturnEffect` akzeptieren eine Liste von Speichernamen statt nur eines einzelnen (jeder referenzierte Speicher erhält dieselbe gezogene bzw. feste Rate) – rückwärtskompatibel, da ein einzelner Name weiterhin eine Liste der Länge 1 ist.
  - [x] Unit-Tests: mehrere Speicher derselben Gruppe erhalten in jedem Lauf identische Renditewerte.
- [ ] **Epic 4.7 – Bausteine: Position als Anlageklassen-Mitglied** (`compute_to_ai.features.finance`)
  - [x] Neue Berechnungsbausteine `calculations_shares_from_transactions` und `calculations_market_value` (siehe 06-Feature-Berechnungen.md, Gruppe „Depot-Bestand & Rebalancing-Rechner"); `calculations_shares_from_transactions` ist rein optional – ein Speicher kann seine Stückzahl weiterhin direkt (`finance_set_asset_shares`, Epic 4.3) statt über eine Transaktionshistorie erhalten, nicht jeder Nutzer hat eine solche über Jahre geführt.
  - [x] `finance_add_position` erlaubt das Hinzufügen weiterer Positionen (je ISIN/WKN, Anteile fest über `finance_set_asset_shares` oder aus Transaktionshistorie über `finance_set_position_from_transactions`, aktueller Kurs über `finance_update_plan_prices`) zu einer bestehenden Anlageklasse; jede Position wird als eigener Speicher mit Lot-Semantik angelegt, alle Positionen einer Anlageklasse referenzieren denselben Rendite-Effekt (siehe Epic 4.6). Die Wertpapier-Metadaten aus Epic 4.2 werden dabei je Position (statt je Anlageklasse) geführt. `finance_list_positions`/`finance_remove_position` runden die Verwaltung ab.
  - [x] Bei Herleitung aus der Transaktionshistorie werden die initialen Lots direkt aus den einzelnen Kauftransaktionen gebildet (Kaufdatum, Stückzahl, Einstandspreis), nicht aus einem pauschalen Startbetrag.
  - [ ] Genau eine Position je Anlageklasse ist als aktiv markierbar (Kaufpriorität für neue Sparraten).
- [x] **Epic 4.8 – Baustein: Positions-Rebalancing innerhalb einer Anlageklasse** (`compute_to_ai.features.finance`)
  - [x] Neuer `ComputedEffect`, der bei Investition den Betrag vollständig der aktiven Position zuweist und bei Entnahme zuerst die Position ohne Bestandsschutz-Vorteil mit dem geringsten unrealisierten Gewinn (in Prozent) abbaut, erst danach die mit dem nächsthöheren Gewinn, zuletzt Bestandsschutz-Positionen; innerhalb einer gewählten Position bleibt die Lot-FIFO-Verbrauchsfolge unangetastet (siehe 04-Feature-Finanzen-Methodik.md, Abschnitt „Positions-Rebalancing innerhalb einer Anlageklasse").
  - [x] Konfigurierbare Verkaufsschwelle (`sell_threshold`, Prozent-Abweichung vom Startgewicht einer Position innerhalb ihrer Anlageklasse; `None` = nie aktiv verkaufen, `0` = jede Abweichung sofort zurückführen).
  - [x] Unit-Tests für beide Schwellen-Extreme sowie einen Zwischenwert, dazu ein Test, der bestätigt, dass bei mehreren nicht geschützten Positionen zuerst die mit dem geringsten Gewinn verkauft wird.
- [x] **Epic 4.9 – Baustein: Beitrags-Rechner für Sparraten-Verteilung**
  - [x] Neuer generischer Berechnungsbaustein `calculations_contribution_allocation` (`compute_to_ai.features.calculations.holdings`): nimmt je Bucket den aktuellen Wert und das Zielgewicht sowie einen neuen Gesamtbetrag entgegen und verteilt ihn so, dass die Abweichung vom Zielgewicht über alle Buckets minimiert wird – ohne Plan-Bezug, reine Arithmetik (siehe 06-Feature-Berechnungen.md).
  - [x] Finance-Wrapper-Tool, das diesen Baustein mit den tatsächlichen Anlageklassen-Zielgewichten und Positions-Marktwerten eines Plans füttert und das Ergebnis auf die aktive Position je Anlageklasse abbildet – beantwortet direkt „wie viel investiere ich diesen Monat in welchen ETF", ohne einen vollen Monte-Carlo-Lauf zu benötigen (löst den entsprechenden Punkt aus 08-Offene-Fragen.md, „Performance interaktiver Ad-hoc-Anfragen", für diesen konkreten Fall).
- [x] **Epic 4.10 – Auswertung: Ist/Soll-Drift- und Gewinn/Bestandsschutz-Report, Einzelverkaufs-Steuerschätzer, Plan-Ist-Vergleich** → Details in [tasks/task-4.10-auswertungen-und-reports/00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.10-auswertungen-und-reports/00-konzept.md)
- [x] **Epic 4.11 – Frequenz- & Intervall-Ausgaben (Periodische Dauer- & Turnusausgaben)** → Details in [tasks/task-4.11-frequenz-und-intervall-ausgaben/00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.11-frequenz-und-intervall-ausgaben/00-konzept.md)
- [x] **Epic 4.12 – Refactoring & Plan-Audit-Bereinigungen (Code-Review-Erkenntnisse)** → Details in [tasks/task-4.12-refactoring-und-audit-bereinigungen/00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.12-refactoring-und-audit-bereinigungen/00-konzept.md)
- [ ] **Epic 4.13 – Graduelle Kapitalsicherung vor bekannten Entnahmen (Cash-Bucket- & Anschaffungs-Glidepath)** → Details in [tasks/task-4.13-graduelle-kapitalsicherung-glidepath/00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.13-graduelle-kapitalsicherung-glidepath/00-konzept.md)
- [ ] **Epic 4.14 – Zentrale Parameter- & Raten-Registry (Single Source of Truth & Referenz-System)** → Details in [tasks/task-4.14-zentrale-parameter-registry/00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.14-zentrale-parameter-registry/00-konzept.md)
- [ ] **Epic 4.15 & 4.16 – Strikte Cache-Invalidierung & Pre-Flight Konfigurations-Audit** → Details in [tasks/task-4.15-4.16-cache-invalidierung-und-pre-flight-audit/00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.15-4.16-cache-invalidierung-und-pre-flight-audit/00-konzept.md)

- [ ] **Epic 4.17 – Golden-Tests für Fehlkonfigurationen & Audit-Warnungen** → Details in [tasks/task-4.17-golden-tests-fehlkonfigurationen/00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.17-golden-tests-fehlkonfigurationen/00-konzept.md)





## Meilenstein 5 – Benutzerprofil-Speicher & Prompt-Restrukturierung (Lebensberater)

**Ziel**: Einführung eines plan-spezifischen Benutzerprofil-Speichers (Fact-Store), der es dem Agenten erlaubt, ein detailliertes Profil über den Nutzer (und ggf. weitere Haushaltsmitglieder) aufzubauen. Das Profil wird automatisch bei Was-wäre-wenn-Kopien mitgenommen. Zudem wird die zunehmende Komplexität der System-Prompts durch eine modulare Neustrukturierung gelöst und der Grundstein für die Rolle des "Lebensberaters" gelegt.

- [ ] **Epic 5.1 & 5.2 – Wissensspeicher & Profile-Tools (Fact-Store, Bulk-Read Dump & Duplizierung)** → Details in [tasks/task-5.1-5.2-wissensspeicher-und-profile-tools/00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-5.1-5.2-wissensspeicher-und-profile-tools/00-konzept.md)
- [ ] **Epic 5.3 & 5.4 – Prompt-Restrukturierung & Vorbereitung Lebensberater** → Details in [tasks/task-5.3-5.4-prompt-restrukturierung-und-lebensberater/00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-5.3-5.4-prompt-restrukturierung-und-lebensberater/00-konzept.md)

## Meilenstein 6 – Baustein-Katalog & Regelwerk-Templates

**Ziel**: Der Mechanismus für versionierte Regelwerk-Templates (z. B. jährliche Steuerrechtsänderungen) ist umgesetzt, inklusive Bestandsschutz-Handling und einem Vertrauensmodell für extern geladene Templates.

- [ ] **Epic 6.1–6.3 – Regelwerk-Templates & Versionierung (Steuerrecht-Templates, Bestandsschutz-Konsistenz, Diff-Prüfung)** → Details in [tasks/task-6.1-6.3-regelwerk-templates-und-versionierung/00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-6.1-6.3-regelwerk-templates-und-versionierung/00-konzept.md)

## Meilenstein 7 – Weitere Ausbaustufen (später, unverbindlich)

Regimeabhängige Korrelationsmodelle, Mehrgeräte-/Mehrsitzungs-Konsistenz der lokalen Speicherung, weitere Feature-Module, Vertiefung der in 08-Offene-Fragen.md verbliebenen fachlichen Detailfragen. Denkbar auch: proaktive, marktsignalgetriebene Portfolio-Verkäufe zur Cash-Bucket-Auffüllung (z. B. bei Allzeithochs oder nach überdurchschnittlichen Renditephasen) statt nur regelbasiert nach Zielgröße - **ausdrücklich mit dem Vorbehalt, dass kurzfristiges Markttiming empirisch nicht robust vorhersagbar ist** (Effizienzmarkthypothese); eine mögliche Umsetzung müsste diesen Vorbehalt im Nutzer-Prompt/Ergebnis transparent machen, statt als empfohlene Standardstrategie zu erscheinen.
