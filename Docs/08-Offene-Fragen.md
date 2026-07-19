# Offene Fragen & Entscheidungen

Dinge, die im weiteren Konzeptgespräch noch geklärt werden müssen.

## Fragen zum generischen Kern

**Sandbox/Sicherheit bei rohen Effekten**: Sobald ein Agent (oder ein Nutzer) einen „rohen" Effekt frei formuliert, nähert sich das einer kleinen Skriptsprache an. Wie wird verhindert, dass ein fehlerhafter oder böswilliger roher Effekt die Simulation unbemerkt verfälscht oder unsicheren Code ausführt? Für Meilenstein 3 (siehe 10-Roadmap.md) stellt sich die Frage nicht akut, da dort ausschließlich kuratierte Bausteine (keine rohen, frei formulierten Effekte) verwendet werden – sobald rohe Effekte tatsächlich gebraucht werden, muss das geklärt sein.

**Grenzen der Generizität**: Ab wann lohnt sich ein neuer, eigener Baustein bzw. ein neues Feature-Modul gegenüber einem rohen, ad hoc definierten Effekt? Gibt es Kriterien (Komplexität der Mathematik, Wiederverwendungshäufigkeit, Fehlerkosten), nach denen entschieden wird, was in den kuratierten Katalog aufgenommen wird?

**Validierung an einer zweiten Domäne**: Der Kern ist bewusst domänenneutral entworfen, aber bisher nur am Finanzfall im Detail durchdacht. Wann und mit welcher zweiten, deutlich andersartigen Domäne (z. B. Ausdauersport, Startup-Runway) soll die tatsächliche Generizität geprüft werden?

## Fragen zur Architektur/MCP

**Baustein-Katalog-Governance**: Wer pflegt und versioniert die kuratierten Bausteine, und nach welchem Prozess werden neue aufgenommen oder bestehende geändert?

**Regelwerk-Template-Vertrauensmodell**: Wie wird ein heruntergeladenes Regelwerk-Template (z. B. „Steuer-2027") vor der Anwendung geprüft – Signierung, mitgelieferte Testfälle mit erwartetem Ergebnis, manuelle Bestätigung durch den Nutzer?

**Technische Umsetzung des Bestandsschutzes**: Wie genau merkt sich ein Speicher-Lot, unter welcher Regelwerk-Version es entstanden ist, und wie wird das bei einer späteren Regelwerk-Aktualisierung konsistent gehalten?

**JSON-Schema-Versionierung und Migration**: Wie wird sichergestellt, dass eine ältere lokale Profildatei von einer neueren Serverversion entweder korrekt migriert oder klar als veraltet erkannt wird?

**Mehrgeräte-/Mehrsitzungs-Konsistenz**: Die lokale JSON-Datei als einzige Quelle der Wahrheit funktioniert für Einzelnutzung auf einem Gerät gut. Was passiert bei parallelen Schreibzugriffen (mehrere Agenten-Sitzungen, mehrere Geräte über Cloud-Sync)? Reicht ein einfacher Zeitstempel-/Versionscheck, oder braucht es mehr?

**Performance interaktiver Ad-hoc-Anfragen**: Eine Chat-eingebettete Frage wie „kann ich mir das jetzt leisten?" sollte spürbar schneller beantwortbar sein als eine volle Batch-Simulation mit tausenden Läufen. Reicht eine reduzierte Laufzahl für solche Anfragen, eine Wiederverwendung des letzten Batch-Ergebnisses mit einem schnellen Differenz-Check, oder braucht es einen eigenen, leichteren Rechenweg?

## Detailfragen zur Besteuerung (Feature Finanzen)

Wie wird der gemeinsame Sparerpauschbetrag (2.000 €) auf mehrere Depots/Anlageklassen aufgeteilt, wenn nicht alle Erträge in einem Depot anfallen? Sollen Verlustverrechnungstöpfe (allgemeiner Verlusttopf vs. Aktien-Verlusttopf) und Verlustvorträge über mehrere Jahre abgebildet werden?

## Alternative Anlagen (z. B. Kryptowährungen) und Besteuerung

Soll das Modell auch Anlageklassen außerhalb von Fonds/ETFs unterstützen, z. B. Kryptowährungen? Diese unterliegen in Deutschland (Stand 2026) einer grundlegend anderen Besteuerung (privates Veräußerungsgeschäft nach § 23 EStG, Freigrenze 1.000 €/Jahr innerhalb der Haltefrist, danach steuerfrei) – das bräuchte einen eigenen Steuer-Baustein.

## Detailfragen zum Referenzpfad/Glidepath

Wie wird der Referenzpfad konkret definiert – linear interpoliert oder nach einer anderen Kurve? Wie steil soll der Glidepath standardmäßig sein, pro Anschaffung oder global konfigurierbar?

## Portfolio-Struktur

Ein gemeinsames Portfolio für den Haushalt, oder getrennte Depots je Person mit ggf. unterschiedlicher Allokation und steuerlicher Behandlung?

## Detailfragen zu Verbindlichkeiten (Kredite, Unterhalt)

Nach welcher konkreten Regel wird zwischen Sondertilgung und Investition entschieden? Sind Kreditzinsen steuerlich absetzbar (z. B. Werbungskosten bei vermieteter Immobilie)? Ist Unterhalt steuerlich relevant (Realsplitting, Kindesunterhalt)? Soll ein variabler Hauskreditzins (Anschlussfinanzierung) als unsichere Größe abgebildet werden?

## Lebensphasen-Details

Sollen unfreiwillige, zufällige Phasenübergänge abgebildet werden (z. B. unerwarteter Jobverlust)? Welche weiteren Parameter außer den Notfallpuffer-Monaten sollten phasenspezifisch sein?

## Immobilie/Wohneigentum als Vermögenswert

Die Basisausprägung bildet ein finanziertes Wohneigentum bereits als Anschaffung + Verbindlichkeit ab (siehe 03-Feature-Finanzen-Domaenenmodell.md). Offen bleibt die Erweiterung: Soll der Immobilienwert selbst als eigener, wertsteigernder Vermögens-Speicher geführt werden, und soll eine Mietkostenersparnis bei selbstgenutztem Eigentum gegengerechnet werden?

## Weitere Altersvorsorge-Formen

Existieren bAV, Riester, Rürup oder private Rentenversicherungen mit eigener Besteuerungs-/Auszahlungslogik?

## Erbschaftssteuer für den Partner

Falls ein Vererbungsziel für die Partnerin gilt: Soll die Erbschaftssteuerlast (abhängig von Ehe vs. nichteheliche Lebensgemeinschaft) im Zielvermögen berücksichtigt werden?

## Besteuerung der Cash-Bucket-Zinsen

Zinserträge aus dem Cash-Bucket unterliegen ebenfalls der Abgeltungsteuer unter Nutzung des Sparerpauschbetrags – sollte im Jahresablauf explizit als eigener Fall ergänzt werden.

## Hinterbliebenenrente bei Wegfall des Partnerbeitrags

Der einfache Fall (Partnerbeitrag endet zu einem Zeitpunkt) ist gelöst (siehe 03-Feature-Finanzen-Domaenenmodell.md). Offen bleibt die realistischere Hinterbliebenenrente bei Ehe/Lebenspartnerschaft.

## Ehe/Lebenspartnerschaft vs. nichteheliche Lebensgemeinschaft

Mehrere Annahmen (gemeinsamer Sparerpauschbetrag, Hinterbliebenenrente, gesetzliches Erbrecht) hängen am rechtlichen Status der Partnerschaft, der noch zu klären ist.

## Pflegekosten und Langlebigkeitsrisiko

Soll ein Tail-Risiko-Szenario für Pflegebedürftigkeit/altersgerechten Umbau abgebildet werden, oder reicht der altersabhängige Ausgabenfaktor als Näherung?

## Quelle der Höhe der gesetzlichen Rente

Extern vorgegebener Wert (Renteninformation der Deutschen Rentenversicherung) oder eigene Nachbildung der Rentenformel (Entgeltpunkte × aktueller Rentenwert)?

## Wissensbasis für KI-gestützte Vorschläge

Woher stammen Referenzwerte zu typischen Nutzungsdauern/Kostenrahmen (Küche, Auto, Dach) für proaktive Vorschläge – LLM-Wissen, gepflegte Tabelle, oder Kombination?

## Konkrete Werte für Cash-Bucket-Parameter

Welche konkreten Werte sind für Notfallpuffer-Monate und Entnahmehorizont sinnvoll (siehe Wertebeispiele in 05-Feature-Finanzen-Parameter.md), und sollte der Entnahmehorizont selbst mit dem Alter variieren?

## Altern von Plänen und zeitlicher Verlauf

**Intention:**
Wenn ein Simulationsplan (z. B. erstellt im Jahr 2026) nach mehreren Jahren (z. B. 2031) unverändert geladen wird, stimmen das relative Startalter der Personen und die hinterlegten Anfangssalden der Speicher nicht mehr mit der Realität überein. Es muss verhindert werden, dass veraltete Pläne stillschweigend mit veraltetem Zeitbezug simuliert werden, was zu verfälschten Ergebnissen führt.

**Vorgeschlagene Lösung:**
1. **Zentraler Zeit-Anker:** Die `timeline` erhält ein explizites `start_year`, und Personen werden über ihr Geburtsjahr statt eines statischen Alters definiert, damit das Alter in jedem Zeitschritt dynamisch berechnet werden kann.
2. **Validierung in der Engine:** Die Simulations-Engine vergleicht beim Start das `start_year` des Plans mit dem aktuellen Kalenderjahr des ausführenden Systems. Liegt das Startjahr in der Vergangenheit, bricht die Engine mit einer strukturierten Fehlermeldung ab (`PlanOutdatedError`).
3. **Interaktive Agenten-Aktualisierung:** Der LLM-Agent fängt diesen Fehler ab, analysiert den Plan auf betroffene Elemente (z. B. abgelaufene Einmaleffekte oder verschobene Phasen) und bittet den Nutzer gezielt um die Eingabe der aktuellen Kontostände und Lebensdaten. Danach aktualisiert der Agent das `start_year` und die Salden im JSON-Plan und startet die Simulation neu.

**Warum:**
Dieser Ansatz hält den Kern der Simulations-Engine schlank und verzichtet auf eine hochkomplexe Historisierung von Ist-Daten im Simulations-Code. Da sich Lebensumstände in mehreren Jahren meist grundlegend und unvorhersehbar ändern (z. B. durch Jobwechsel, Erbschaften, Markt-Crashs), ist eine automatische Fortschreibung ohnehin unrealistisch. Die menschlich-agentische Schnittstelle kann diese Anpassungen flexibler und präziser interaktiv lösen.

## Optionale Freitext-Beschreibungen für Modell-Entitäten (Absichts-Metadaten)

**Intention:**
Ein Effekt (z. B. `"Lebenshaltung"`) oder ein Store (z. B. `"cash"`) hat bisher nur einen Namen. Ohne Zusatzkontext ist unklar, welche konkreten Posten (z. B. Miete, Strom, Lebensmittel) in einer Pauschale enthalten sind. Dem LLM-Agenten fehlt dadurch die Brücke, um fachliche Fragen des Nutzers (z. B. *"Habe ich die Stromkosten bedacht?"*) direkt mit der Simulationsstruktur abzugleichen.

**Vorgeschlagene Lösung:**
Einführung eines optionalen Freitextfeldes `description: str | None = None` auf Ebene der Basisklassen (für `Plan`, `Store`, `BaseEffect`, `Phase`). Diese Beschreibungen werden bei MCP-Listenabfragen (z. B. `core_list_effects`, `core_list_stores`) in den JSON-Payloads mitgeliefert, sodass das LLM sie lesen und interpretieren kann.

**Warum & Mehrwert:**
Das LLM-Weltwissen kann dadurch die Intention des Nutzers verstehen und logisch verknüpfen. Fragt der Nutzer nach einer Detail-Ausgabe, kann der Agent die Beschreibungen scannen und bestätigen, ob der Wert in einer Pauschale enthalten ist oder separat angelegt werden muss.

## Kaufkraftbereinigung im Export (Option `real_in_today_money`)

**Intention:**
Simulationsergebnisse werden nominal ausgegeben. Zukünftige nominale Werte (z. B. im Jahr 2069) sind durch die Inflation schwer zu plausibilisieren. Der Agent muss heute jeden Zeitschritt einzeln über Hilfstools abdiskontieren, um dem Nutzer reale Kaufkraftwerte nennen zu können.

**Vorgeschlagene Lösung:**
Erweiterung von `finance_get_path_category_series` um einen Parameter `adjust_for_inflation: bool = False` (oder `real_in_today_money`). 
* **Edge Case / Entscheidung:** Um stochastische Verläufe korrekt abzubilden, muss die Engine bei der Pfadhistorisierung (Ledger) den kumulierten, pfadspezifisch simulierten Inflationsfaktor mitprotokollieren. Die Werte werden dann pfadspezifisch dividiert, anstatt pauschal mit einem statischen Zinssatz abzuzinsen.

**Warum & Mehrwert:**
Der Agent erhält direkt kaufkraftbereinigte Zeitreihen und kann dem Nutzer unmittelbar verständliche monatliche Durchschnittsbudgets präsentieren, was die Ergonomie und Interpretierbarkeit massiv erhöht.

## Plan-Vergleichs-Schnittstelle (`finance_compare_plans`)

**Intention:**
Das Herzstück der Finanzplanung sind "Was-wäre-wenn"-Vergleiche (z. B. Renteneintritt mit 63 vs. 65). Bisher muss der Agent beide Pläne getrennt simulieren, die Ergebnisse einzeln laden und die Differenzen manuell berechnen.

**Vorgeschlagene Lösung:**
Ein neues MCP-Tool `finance_compare_plans(plan_name_a: str, plan_name_b: str)` vergleicht zwei berechnete Pläne.
* **Umfang:** Das Tool liefert:
  1. Statistischen Vergleich: Differenz der Ruinwahrscheinlichkeit und der Endvermögens-Perzentile (p10, p50, p90).
  2. Konfigurations-Delta: Liste der geänderten, hinzugefügten oder gelöschten Effekte/Parameter.
* **Edge Cases:** Pläne können unterschiedliche Timeline-Längen haben (z. B. 40 vs. 50 Jahre). Das Tool muss die Vergleiche auf die jeweils gemeinsame Schnittmenge normieren (z. B. Vergleich zum Ende der kürzeren Timeline) oder klare Warnungen ausgeben, da ein direkter Endvermögens-Vergleich sonst mathematisch hinkt.

**Warum & Mehrwert:**
Das Tool liefert dem Agenten ein fokussiertes Datenpaket. Das LLM kann daraus eine fachlich hervorragende Gegenüberstellung formulieren, ohne redundante MCP-Runden drehen zu müssen.

## Optimierter Export von Perzentil-Kurven (`finance_get_percentile_curves`)

**Intention:**
Für die Erstellung von Vermögensverläufen (Charts) muss der Agent aktuell die kompletten Kategorienserien für mehrere Pfade (`p10`, `p50`, `p90`) separat abfragen, was zu sehr großen JSON-Antworten und hohem Token-Verbrauch führt.

**Vorgeschlagene Lösung:**
Ein neues MCP-Tool `finance_get_percentile_curves(plan_name: str)` gibt eine kompakte Zeitreihe zurück, die pro Schritt die aggregierten Salden für die Perzentile (10, 50, 90) liefert.
* **Aggregationsebene & Edge Cases:** Es sollten zwei Saldenwerte pro Schritt/Perzentil ausgegeben werden: `liquid_balance` (Summe aller Cash-Buckets) und `invested_balance` (Summe aller ETF-Portfolios), sowie `liabilities` (Summe aller Restschulden). 
* **Warum Liquiditätsklassen statt nur einer Summenkurve:** Eine reine Summenkurve kaschiert gefährliche Liquiditätsengpässe (z. B. hohes ETF-Vermögen, aber leeres Cash-Konto, was kurzfristig zum Ruin führen kann). Kreditschulden müssen getrennt ausgewiesen werden, damit das Netto-Vermögen korrekt berechnet wird.

**Warum & Mehrwert:**
Maximale Token-Effizienz und schnelle Datenbereitstellung für Visualisierungen bei gleichzeitiger Beibehaltung der wichtigsten Liquiditätsunterscheidungen.


