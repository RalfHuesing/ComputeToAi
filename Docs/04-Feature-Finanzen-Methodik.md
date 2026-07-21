# Feature „Finanzen" – Simulationsmethodik

## Grundprinzip: Monte Carlo

Statt mit einer einzigen angenommenen Rendite zu rechnen, wird der Zeitstrahl eines Plans viele tausend Mal durchgerechnet (z. B. 1.000–10.000 Läufe). In jedem Lauf werden die unsicheren Effekte – vor allem die Jahresrendite je Anlageklasse, optional auch Inflation – zufällig aus einer Verteilung gezogen. Über alle Läufe hinweg entsteht so eine Verteilung möglicher Ergebnisse statt einer einzelnen Prognose.

## Ablauf eines einzelnen Simulationslaufs

Ein Lauf rechnet Jahr für Jahr vom aktuellen Alter bis zum angenommenen Lebensende – die konkrete, finanzspezifische Ausprägung der generischen Zeitstrahl-/Effekt-Auswertung aus 01-Kern-Domaenenmodell.md:

1. **Aktive Lebensphase bestimmen**: Für das laufende Jahr wird nachgeschlagen, welche Lebensphase gerade aktiv ist. Daraus ergeben sich alle phasenspezifischen Parameterwerte des Jahres, aktuell insbesondere die Notfallpuffer-Monate für den Cash-Bucket (siehe Schritt 8).
2. **Renditen ziehen**: Für jede Anlageklasse wird eine zufällige Jahresrendite gezogen, wobei die Renditen aller Anlageklassen gemeinsam (korreliert) über den Baustein „Korrelierte Anlageklassen-Renditen" gezogen werden (siehe unten).
3. **Inflation ziehen**: Optional wird auch die Inflation für das Jahr stochastisch statt fix angenommen.
4. **Einkommen berechnen**: Alle aktiven Einkommensströme werden um die jeweilige Wachstumsrate fortgeschrieben. Nach Renteneintritt einer Person ersetzt die gesetzliche Rente das Erwerbseinkommen.
5. **Laufende Ausgaben berechnen**: Individuelle und gemeinsame Ausgaben werden um Inflation fortgeschrieben; im Ruhestand wird zusätzlich der altersabhängige Ausgabenfaktor angewendet.
6. **Verbindlichkeiten fortschreiben**: Für jede aktive Verbindlichkeit wird die fällige periodische Rate ermittelt, bei Zinssatz > 0 % in Zins- und Tilgungsanteil aufgeteilt und die Restschuld um den Tilgungsanteil reduziert. Die volle Rate mindert wie eine laufende Ausgabe den verfügbaren Cashflow des Jahres. Ist die Endbedingung erreicht, entfällt die Verbindlichkeit ab dem Folgejahr vollständig. Optional wird geprüft, ob eine Sondertilgung sinnvoll ist (siehe unten).
7. **Anschaffungen prüfen**: Für jede Anschaffung, die im aktuellen Jahr fällig werden könnte, wird die Trigger-Regel ausgewertet (siehe unten). Wird sie ausgelöst, wird der Betrag als Einmalausgabe berücksichtigt und ggf. Kapital aus dem Portfolio dafür entnommen.
8. **Sparquote / Entnahme ermitteln**: Einnahmen minus laufende Ausgaben minus fällige Verbindlichkeiten-Raten minus fällige Anschaffungen ergibt in der Erwerbsphase die Sparquote oder im Ruhestand die nötige Entnahme zur Deckung der Rentenlücke.
9. **Cash-Bucket auffüllen**: Die Ziel-Bucket-Größe für das laufende Jahr wird neu berechnet (siehe unten). Die Sparquote füllt vorrangig den Bucket bis zur Zielgröße auf; erst der überschüssige Betrag fließt ins Portfolio. Reicht die Sparquote nicht aus, wird ersatzweise aus dem Portfolio verkauft. Bei einer Entnahme (Ruhestand) gilt die spiegelbildliche Reihenfolge: Zuerst wird bis zur Zielgröße aus dem Cash-Bucket entnommen, erst danach zusätzlich aus dem Portfolio.
10. **Portfolio fortschreiben**: Das Portfolio wird um die gezogene Rendite verändert (jede Position einer Anlageklasse erhält dieselbe Rendite, siehe „Korrelation zwischen Anlageklassen" unten), der nach Bucket-Auffüllung verbleibende Sparbetrag wird gemäß Ziel-Allokation zwischen den Anlageklassen investiert und dabei je Anlageklasse vollständig der aktiven Position zugewiesen, Entnahmen zur Rentenlücke werden gemäß Rebalancing-Regel zwischen den Anlageklassen entnommen und dabei je Anlageklasse zuerst aus Positionen/Lots ohne Bestandsschutz-Vorteil entnommen (siehe „Positions-Rebalancing innerhalb einer Anlageklasse" unten).
11. **Steuern berechnen**: Auf thesaurierende Fondsanteile wird die Vorabpauschale angewendet, auf realisierte Gewinne bei Verkäufen die Abgeltungsteuer nach Teilfreistellung, verbleibendem Sparerpauschbetrag und ggf. Bestandsschutz des jeweiligen Lots. Details siehe Abschnitt „Besteuerung" unten.
12. **Ruin-Prüfung**: Reichen Cash-Bucket und Portfolio zusammen nicht aus, um eine fällige Entnahme, Anschaffung, Verbindlichkeiten-Rate oder Steuerzahlung zu decken, gilt der Lauf ab diesem Jahr als „Ruin" (die finanzspezifische Zielbedingung, siehe 01) – der Lauf wird trotzdem bis zum Lebensende fortgesetzt (Speicher auf 0 gedeckelt), damit Zeitpunkt und Ausmaß erkennbar bleiben statt nur das binäre Ereignis.
13. Wiederholen bis zum angenommenen Lebensende. Am Ende steht das (nach Steuern) verbleibende, nominale Endvermögen dieses Laufs.

Die Rentenbesteuerung (Schritt 4/11) fällt bereits vor der Bucket-Auffüllung (Schritt 9) an – sonst würde der Cash-Bucket auf ein Ziel auffüllen, das die noch ausstehende Steuerlast nicht berücksichtigt, und am Jahresende systematisch unter der Zielgröße liegen. Die Kapitalertragsteuer aus Schritt 11 läuft dagegen bewusst *nach* der Portfolio-Fortschreibung (Schritt 10), da sie genau die in diesem Jahr durch Bucket-Auffüllung oder -Entnahme tatsächlich realisierten Verkäufe besteuert. Auf Effekt-Ebene wird das über eine explizite Ausführungsreihenfolge der berechneten Effekte abgebildet (Rentensteuer vor, Kapitalertragsteuer nach dem Cash-Bucket-Manager), nicht über die Reihenfolge der Tool-Aufrufe beim Planaufbau.

Alle Beträge werden während der Simulation **konsequent nominal** geführt (kein Umschalten auf reale Größen innerhalb des Laufs); die Kaufkraft eines nominalen Ergebnisses in heutigem Geld wird bei Bedarf erst bei der **Auswertung** über das bereits vorhandene Berechnungen-Werkzeug `calculations_adjust_for_inflation` (siehe 06-Feature-Berechnungen.md) hergestellt, nicht durch ein zweites, paralleles Realwert-Modell im Simulationskern.

## Korrelation zwischen Anlageklassen

Die Jahresrenditen der Anlageklassen werden nicht unabhängig voneinander gezogen, sondern gemeinsam aus einer multivariaten Normalverteilung mit einer Korrelationsmatrix gezogen (technisch: Cholesky-Zerlegung) – die finanzspezifische Ausprägung des generischen Korrelations-Konzepts aus 01. Das ist Standard in der quantitativen Portfoliotheorie seit Markowitz (1952). Parametrisch (Erwartungswert/Volatilität/Korrelation als Eingabeparameter) statt historisches Bootstrapping ist die Basisannahme – einfacher umzusetzen und ausreichend für den aktuellen Bedarf; Bootstrapping (inkl. Fat-Tails und Autokorrelation) bleibt eine mögliche spätere Ausbaustufe.

Die Korrelationsmatrix erstreckt sich über **alle** Anlageklassen paarweise – auch innerhalb des risikobehafteten Anteils selbst (z. B. zwischen mehreren Aktien-ETFs auf unterschiedliche Regionen oder gegenüber alternativen Anlagen wie Kryptowährungen). Die Korrelation zwischen Aktien und Anleihen ist zudem nicht konstant, sondern regimeabhängig (niedrig/negativ in Niedriginflationsphasen, positiv in Hochinflationsphasen); Korrelationen zwischen risikobehafteten Anlageklassen steigen in Krisen tendenziell an.

Kalibrierung: Die Korrelationswerte folgen – ebenso wie erwartete Renditen und Volatilitäten – allgemein anerkannten wissenschaftlichen Standardannahmen aus der Kapitalmarktforschung, nicht einer projektspezifischen Schätzung. Eine statische, historisch kalibrierte Korrelationsmatrix ist die Basisannahme; ein regimeabhängiges Modell mit zwei Regimen bleibt eine mögliche spätere Ausbaustufe.

Realisiert sich eine Anlageklasse über mehrere Positionen (siehe 03-Feature-Finanzen-Domaenenmodell.md), erhalten alle ihre Positionen **dieselbe** gezogene Jahresrendite – sie bilden ja denselben Index ab, tragen also kein eigenständiges Renditerisiko gegeneinander. Das wird direkt über den generischen Mehrfach-Speicher-Effekt aus 01-Kern-Domaenenmodell.md abgebildet, nicht über mehrere Effekte mit künstlicher Korrelation 1,0 zwischen den Positionen (numerisch instabil bei der Cholesky-Zerlegung, da die Korrelationsmatrix dann nicht mehr positiv definit ist).

## Positions-Rebalancing innerhalb einer Anlageklasse

Während das Rebalancing **zwischen** Anlageklassen ein Zielgewicht aktiv über Käufe und Verkäufe durchsetzt (z. B. die BIP-Gewichtung, siehe 03-Feature-Finanzen-Domaenenmodell.md), gilt **innerhalb** einer Anlageklasse mit mehreren Positionen eine eigene, bewusst zurückhaltendere Regel: Ein Verkauf zur reinen Gewichtskorrektur zwischen gleichwertigen Positionen würde ggf. Bestandsschutz-Lots antasten und wäre damit steuerlich fast immer nachteilig gegenüber einer vorübergehenden Schiefverteilung.

- **Kaufpriorität**: Der einer Anlageklasse zugewiesene Investitionsbetrag fließt vollständig in ihre als aktiv markierte Position; alle übrigen Positionen der Anlageklasse erhalten keine neuen Zuflüsse.
- **Verkaufspriorität**: Eine Entnahme aus einer Anlageklasse (Rentenlücke, Anschaffung, Cash-Bucket-Auffüllung) wird zuerst aus den Positionen ohne Bestandsschutz-Vorteil gedeckt, und dort aus der Position mit dem geringsten unrealisierten Gewinn in Prozent (nicht chronologisch) – erschöpft ihr Bestand nicht den nötigen Betrag, folgt die Position mit dem nächsthöheren Gewinn. **Innerhalb** einer so gewählten Position gilt zwingend FIFO über ihre eigenen Lots (siehe 03-Feature-Finanzen-Domaenenmodell.md, „Besteuerung"), da die Verbrauchsfolge einzelner Lots derselben ISIN im selben Depot keine freie Wahl ist, anders als die Wahl zwischen verschiedenen Positionen. Bestandsschutz-Lots werden unabhängig vom aktuellen Gewinn zuletzt angetastet.
- **Verkaufsschwelle** (`sell_threshold`): ein optionaler, je Anlageklasse konfigurierbarer Prozentwert der relativen Gewichtsabweichung einer Position von ihrem Anteil an der Anlageklasse zum Startzeitpunkt. Ist er `None`/unbegrenzt (Standardannahme), wird zwischen den Positionen **nie** aktiv verkauft – die Gewichtung driftet mit der Zeit rein durch die Kaufpriorität auseinander. Ist er gesetzt (einschließlich 0), wird bei Überschreiten aktiv so viel aus der/den übergewichteten Position(en) verkauft (unter Beachtung der Verkaufspriorität) und in die aktive Position investiert, bis die Abweichung wieder innerhalb der Schwelle liegt; 0 bedeutet, jede Abweichung sofort zurückzuführen.

## Trigger-Logik für flexible Anschaffungen

Kurzfristiges Markttiming ist empirisch nicht robust vorhersagbar (Effizienzmarkthypothese, Fama 1970). Die Trigger-Logik orientiert sich deshalb an zwei etablierten Prinzipien der Ruhestandsforschung:

**1. Referenzpfad-Vergleich (angelehnt an Guyton-Klinger-Guardrails, 2006):** Der tatsächliche Wert des für die Anschaffung vorgesehenen Kapitals wird mit einem erwarteten Referenzpfad verglichen – dem Wert, den die geplante, gleichmäßige Vorfinanzierung bis zum Zieljahr eigentlich erreichen sollte. Liegt der tatsächliche Wert über dem Referenzpfad, wird die Anschaffung ausgelöst, sonst verschoben.

**2. Rising-/Falling-Glidepath (angelehnt an Kitces & Pfau, 2014):** Das Kapital für eine flexible Anschaffung wird mit Annäherung an das Zieljahr graduell von risikoreichen in risikoarme Anlagen umgeschichtet, um Sequence-of-Returns-Risiko zu reduzieren.

Konkret für eine Anschaffung mit Zieljahr T und Toleranzfenster [T − x, T + x]: Ab T − x wird jährlich geprüft, ob der tatsächliche Kapitalwert den Referenzpfad erreicht; ist das der Fall, wird ausgelöst; sonst wird die Prüfung im Folgejahr wiederholt. Spätestens bei T + x wird die Anschaffung zwingend ausgelöst (harte Deadline).

## Verbindlichkeiten und Sondertilgung

Für Verbindlichkeiten mit Zinssatz > 0 % kann eine Sondertilgung konfiguriert sein: Statt überschüssige Liquidität ins Portfolio zu investieren, wird sie vorzeitig auf die Restschuld verrechnet. Die Entscheidung Sondertilgung vs. Investition ist strukturell dieselbe Abwägung wie bei flexiblen Anschaffungen: einer sicheren, garantierten Rendite (dem ersparten Kreditzins) steht eine unsichere, im Erwartungswert höhere Portfoliorendite gegenüber. Grundregel: Sondertilgung ist tendenziell vorteilhaft, wenn der Kreditzins über der erwarteten risikoarmen Anlagerendite liegt. Die genaue Entscheidungsregel ist eine offene Kalibrierungsfrage (siehe 08-Offene-Fragen.md). Eine durch Sondertilgung vorzeitig getilgte Restschuld verkürzt die Restlaufzeit entsprechend.

## Cash-Bucket-Management (Liquiditätsschicht)

Die Ziel-Größe des Cash-Bucket-Speichers wird jedes Simulationsjahr neu berechnet und setzt sich aus drei Komponenten zusammen:

**1. Einkommensausfallpuffer** = Notfallpuffer-Monate(aktive Lebensphase) × monatliche Ausgaben.

**2. Nahsicht-Komponente** = Summe der geplanten Fixausgaben und Urlaube innerhalb eines kurzen rollierenden Nah-Horizonts plus Vorfinanzierungsanteil für flexible Anschaffungen, deren frühester möglicher Zeitpunkt bereits in diesen Horizont fällt.

**3. Entnahmepuffer** = Entnahmehorizont (Jahre) × Entnahmeabhängigkeit(t) × erwartete Jahresausgaben(t).

**De-Risking Glidepath vor Phasenübergängen**: Über den Parameter `glidepath_steps` (z. B. 36 Schritte / 3 Jahre Vorlauf vor dem Renteneintritt) wird die Zielgröße des Cash-Buckets vor einem Phasenwechsel von der bisherigen auf die neue Zielgröße linear über die Vorlaufschritte aufgebaut. Dadurch wird schlagartiger Verkauf von Aktien am Stichtag vermieden und das Sequence-of-Returns-Risiko geglättet. Reichen die verbleibenden Schritte bis zum Phasenwechsel nicht für die volle Schrittanzahl aus, passt sich der lineare Aufbau dynamisch an die verbleibenden Schritte an.

**Vorrang bei der Sparquote**: In jedem Jahr wird die Sparquote zunächst genutzt, um den Bucket auf seine Zielgröße zu bringen bzw. zu halten; erst der darüber hinausgehende Betrag fließt ins Portfolio.

**Glidepath für Anschaffungen**: Sobald eine Anschaffung in den Horizont eintritt, steigt die Ziel-Bucket-Größe bzw. das Cash-Guthaben schrittweise an, statt im Auslösejahr abrupt aus dem Portfolio zu entnehmen.

**Rückfall-Mechanismus**: Fällt der Bucket unter seine Zielgröße, wird er in den Folgejahren vorrangig wieder aufgefüllt; reicht die Sparquote dafür nicht, kann ergänzend aus dem Portfolio verkauft werden.

 Der Cash-Bucket wird mit einem eigenen, niedrigen und risikoarmen Zinssatz verzinst (siehe 05-Feature-Finanzen-Parameter.md).

## Periodische Cashflows & Turnusausgaben

In der Lebensplanung fallen Einnahmen und Ausgaben in unterschiedlichen Rhythmen an:
- **Monatlich (`monthly`)**: Schrittweite 1 Monat.
- **Quartalsweise (`quarterly`)**: Schrittweite 3 Monate.
- **Jährlich (`yearly` / `annual`)**: Schrittweite 12 Monate.
- **Mehrjähriger Turnus (`every_n_years`)**: Schrittweite `interval_years * 12` Monate (z. B. Autokauf alle 5 Jahre oder Dachsanierung alle 20 Jahre).

**Fachliches Prinzip**:
Statt mehrjährige Turnusausgaben auf künstliche Monats- oder Jahresdurchschnitte umzurechnen (was Liquiditätsspitzen verschleiern würde), lässt die Engine Ausgaben exakt in den Zeitschritten wirksam werden, in denen sie tatsächlich anfallen (`interval_steps`). 

Über den Parameter `first_occurrence_step` bzw. `first_occurrence_year` lässt sich der zeitliche Versatz des Erstauftritts festlegen. Die Steigerung durch Inflation oder Wertsicherungsklauseln wird dynamisch für jeden Zeitschritt $t$ als $(1 + r)^t$ berechnet und kommt genau in den aktiven Intervallschritten zum Tragen.

## Besteuerung (deutsches Steuerrecht)

**Abgeltungsteuer**: Realisierte Kapitalerträge werden mit 25 % zzgl. Solidaritätszuschlag (effektiv ca. 26,375 %) besteuert, zzgl. Kirchensteuer, falls zutreffend.

**Sparerpauschbetrag**: Ein jährlicher Freibetrag auf Kapitalerträge von 1.000 € pro Person bzw. 2.000 € für gemeinsam veranlagte Paare (Stand 2026).

**Vorabpauschale**: Bei thesaurierenden Fondsanteilen wird jährlich eine pauschale Mindestbesteuerung fällig. Formel: Fondswert zum 1.1. × Basiszins × 0,7, abzüglich tatsächlicher Ausschüttungen, gedeckelt auf die tatsächliche Wertsteigerung des Jahres. Der Basiszins wird jährlich vom BMF festgelegt (Beispiel 2026: 3,20 %, § 18 Abs. 4 InvStG). Bereits gezahlte Vorabpauschalen mindern bei einem späteren Verkauf den steuerpflichtigen Gewinn.

**Teilfreistellung**: 30 % bei Aktienfonds (>50 % Aktienanteil), 15 % bei Mischfonds (≥25 % Aktienanteil), 0 % bei reinen Renten-/Anleihefonds.

**FIFO-Prinzip und Bestandsschutz**: Bei Teilverkäufen gelten die zuerst gekauften Anteile als zuerst verkauft. Das ist im Kern die generische Lot-Semantik eines Speichers (siehe 01): Jedes Lot trägt sein Kaufdatum, seinen Einstandspreis und – wichtig für Altfälle – das zu diesem Zeitpunkt gültige Steuerregime. Vor dem 1.1.2009 gekaufte Aktien/Fondsanteile bleiben dauerhaft nach altem Recht steuerfrei verkäuflich (Bestandsschutz), unabhängig vom tatsächlichen Verkaufsdatum.

**Besteuerung der gesetzlichen Rente (nachgelagerte Besteuerung)**: Nur ein bestimmter Besteuerungsanteil der Rente ist steuerpflichtig; dieser hängt vom Jahr des Rentenbeginns ab (Beispiel 2026: 84 %) und steigt seit 2023 um 0,5 Prozentpunkte pro Jahr bis 100 % ab Rentenbeginn 2058. Der zu versteuernde Betrag wird zusätzlich durch den jährlichen Grundfreibetrag gemindert.

**Sozialversicherungsbeiträge auf die gesetzliche Rente (KVdR/Pflegeversicherung)**: Zusätzlich mindern Beiträge zur Krankenversicherung der Rentner (KVdR) und zur Pflegeversicherung die Rente direkt an der Quelle. KVdR-Beitrag wird hälftig von der Rentenversicherung übernommen, der Pflegeversicherungsbeitrag vollständig vom Rentner selbst getragen. Gilt nur bei gesetzlicher Krankenversicherung (siehe 08-Offene-Fragen.md zu GKV/PKV).

Konkrete Steuersätze stehen in 05-Feature-Finanzen-Parameter.md, Belege in 09-Quellen.md.

## Ruhestandsübergang

**Stufe 1 – Erwerbsende**: Ab diesem Jahr entfällt das Erwerbseinkommen der Primärperson vollständig. Liegt das Erwerbsende vor dem gesetzlichen Rentenbeginn, folgt eine Frühruhestandslücke: mehrere Jahre ganz ohne Erwerbseinkommen und ohne gesetzliche Rente, in denen sämtliche Ausgaben aus Cash-Bucket und Portfolio finanziert werden müssen.

**Stufe 2 – gesetzlicher Rentenbeginn**: Wird die Rente vor dem Regelrenteneintrittsalter in Anspruch genommen, gilt ein Rentenabschlag von 0,3 % pro Monat vorzeitiger Inanspruchnahme (max. 14,4 %); bei späterer Inanspruchnahme ein Rentenzuschlag von 0,5 % pro Monat Aufschub. Beide Effekte wirken dauerhaft auf die gesamte weitere Rentenhöhe.

**Phasengrenzen & Timeline-Harmonisierung**: Lebensphasen sind halboffene Intervalle \([start\_step, end\_step)\). Die Erwerbsphase endet bei Zeitschritt \(N - 1\) (bezogen auf das Erwerbsende-Alter \(N\)), sodass Erwerbseinkommen letztmalig in Step \(N - 1\) anfällt und die Rentenphase ab Step \(N\) beginnt. Die letzte Phase (Rentenphase) erstreckt sich stets bis zum Ende des Simulationshorizonts (`timeline.step_count`), damit der Notgroschen-Puffer des Cash-Buckets bis zum letzten Zeitschritt aktiv bleibt.

## Aggregation über alle Läufe

Nach Abschluss aller Läufe eines Plans werden berechnet: Perzentile des Endvermögens, Anteil der Läufe mit Ruin (Ruin-Wahrscheinlichkeit) und ggf. Alter bei Ruin, sowie – falls eine Zielvorgabe definiert ist – der Anteil der Läufe, die dieses Ziel erreichen.

## Ableitung der nötigen Sparquote

Die minimal nötige Sparquote kann ermittelt werden, indem die Sparquote als variabler Parameter behandelt und die Simulation wiederholt wird, bis die gewünschte Ziel-Erfolgswahrscheinlichkeit gerade erreicht wird (z. B. Bisektion über die Sparquote). Das methodische Detail wird erst bei der Programmentwicklung festgelegt.

## Pfad-Audit und Plausibilitätsprüfung

Für einen instrumentierten Lauf (siehe 01-Kern-Domaenenmodell.md, „Ledger") ordnet das Finanz-Feature jede Ledger-Zeile einer von sechs Kategorien zu:

- **Einnahmen**: ein positiver additiver Effekt (Einkommensstrom, Sondereinnahme, …) auf einen Nicht-Verbindlichkeits-Speicher.
- **Ausgaben**: ein negativer additiver Effekt (laufende Ausgabe, fixe Anschaffung, die volle fällige Verbindlichkeiten-Rate, …) auf einen Nicht-Verbindlichkeits-Speicher.
- **Steuern**: jede Ledger-Zeile der Bausteine „Rentenbesteuerung" bzw. „Abgeltungsteuer/Vorabpauschale".
- **Rendite**: der prozentuale Wachstumseffekt bzw. die korrelierte Anlageklassen-Rendite auf einen Nicht-Verbindlichkeits-Speicher.
- **Umschichtungen**: alles Übrige – Transfer-Effekte, alle sonstigen berechneten Effekte (Cash-Bucket-Management, Portfolio-Rebalancing, flexible Anschaffung, Verbindlichkeiten-Manager) sowie jede Zins-/Tilgungsbuchung direkt auf dem Verbindlichkeits-Speicher selbst. Der volle fällige Rate-Abfluss vom Cash-Konto zählt bereits als Ausgabe (siehe oben); die parallele Zins-/Tilgungsbuchung auf dem Verbindlichkeits-Speicher restatiert nur dessen Restschuld und wäre sonst eine Doppelzählung derselben Zahlung.
- **Saldo**: der Speicherstand je Speicher zum jeweiligen Zeitschritt, unverändert aus dem Zeitverlauf übernommen – keine Kategorie im eigentlichen Sinn, sondern der Momentaufnahme-Bezugswert dazu.

Welche Speicher als „Verbindlichkeits-Speicher" gelten, wird nicht erraten, sondern aus den im Plan konfigurierten Verbindlichkeiten-Bausteinen abgeleitet. Eine bekannte Vereinfachung: Der tatsächliche Auslösezeitpunkt einer flexiblen Anschaffung ist real ein Vermögensabfluss (kein reiner Umschichtungsvorgang wie die vorangehenden Glidepath-Schritte), wird aus Einfachheitsgründen aber ebenfalls als Umschichtung geführt – erkennbar bleibt der Vorgang trotzdem über das Event-Log (siehe unten) und den sichtbaren Sprung im Speichersaldo.

Diese Kategoriesummen lassen sich wahlweise als Jahressumme oder als Monatsdurchschnitt (Jahreswert / 12) ausgeben; der Saldo je Speicher bleibt davon unberührt, da er eine Momentaufnahme und kein Fluss ist.

Ein Event-Log fasst drei Ereignistypen chronologisch zusammen:

- **Phasenübergang**: die aktive Phase ändert sich zwischen zwei aufeinanderfolgenden Zeitschritten.
- **Verbindlichkeit getilgt**: der Saldo eines Verbindlichkeits-Speichers erreicht erstmals 0.
- **Anschaffung ausgelöst**: eine fixe Anschaffung (bestätigt durch ihre Ledger-Zeile im Auslöseschritt) oder eine flexible Anschaffung (deren Baustein nach Laufende einen Auslöse-Zeitpunkt im Ledger-Zustand hinterlassen hat, siehe 01-Kern-Domaenenmodell.md, „Ledger").

Kategorie-Aggregation und Event-Log setzen einen zuvor durchgeführten Pfad-Audit voraus (siehe 01, „Ledger") und liefern damit die Grundlage, um einzelne Effekte eines Plans (ein zeitlich versetzter Autokauf, eine Steueränderung, eine Ausgabenerhöhung) im Nachhinein nachvollziehbar zu prüfen, statt sich auf aggregierte Endwerte verlassen zu müssen.

## Auswertungen und Reports

### Ist/Soll-Drift- & Gewinn/Bestandsschutz-Report

Der Ist/Soll-Drift-Report (`get_asset_allocation_report` / `finance_get_asset_allocation_report`) vergleicht die aktuelle Ist-Verteilung der Vermögenswerte über alle Anlageklassen hinweg mit den im Plan definierten Zielgewichtungen (Soll-Gewichtungen).

- **Drift-Berechnung**: Pro Anlageklasse wird der Ist-Marktwert berechnet und ins Verhältnis zum Gesamtportfoliowert gesetzt (`actual_weight`). Die Differenz zur Zielgewichtung ergibt die Drift (`drift = actual_weight - target_weight`). Bei einem Gesamtportfoliowert von 0 € wird eine Division durch Null vermieden und die Drift als `-target_weight` ausgewiesen.
- **Gewinn- & Bestandsschutz-Aufschlüsselung**: Für jede Position werden alle hinterlegten Lots analysiert. Das Modul schlüsselt Anschaffungskosten, unrealisierte Gewinne in € und % sowie die Aufteilung in steuerlich befreite Alt-Lots (Bestandsschutz für Käufe vor 2009, `pre_2009`) versus reguläre Lots auf.

### Einzelverkaufs-Steuerschätzer

Der Einzelverkaufs-Steuerschätzer (`estimate_sale_tax` / `finance_estimate_sale_tax`) berechnet exakt die Steuerlast und den Nettoerlös bei einem beabsichtigten Teil- oder Vollverkauf einer spezifischen Depotposition.

- **FIFO-Verbrauchsfolge**: Die Simulation baut die Lots der Position in strikter FIFO-Reihenfolge ab, um den genauen steuerpflichtigen Gewinn der verkauften Anteile zu ermitteln.
- **Teilfreistellung**: Je nach Anlageklasse (`asset_type`) greift die gesetzliche Teilfreistellung nach InvStG: 30 % für Aktienfonds (`equity_fund`), 15 % für Mischfonds (`mixed_fund`), 60 % für Immobilienfonds (`real_estate_fund`) und 0 % für Anleihen/Einzeltitel (`bond_fund`, `stock`).
- **Bestandsschutz**: Gewinne aus Vor-2009-Lots fließen als steuerfreie Gewinne ein.
- **Freibeträge & Steuersatz**: Auf den verbleibenden steuerpflichtigen Gewinn wird der verbleibende Sparerpauschbetrag angewendet. Die Steuerlast berechnet sich aus 25 % Abgeltungsteuer zzgl. 5,5 % Solidaritätszuschlag (effektiv 26,375 %) und optionaler Kirchensteuer.

### Plan-Ist-Stichtagsvergleich

Der Plan-Ist-Stichtagsvergleich (`compare_plan_actuals` / `finance_compare_plan_actuals`) führt einen Stichtagsvergleich durch zwischen dem aktuellen Ist-Gesamtvermögen (Summe aller liquiden Mittel und Anlageklassen abzüglich Verbindlichkeiten) und den simulierten Erwartungs-Perzentilen der Monte-Carlo-Simulation (p10, p50, p90) zu einem gewählten Zeitschritt.

- **Klassifizierung**: Das Ist-Vermögen wird in eine von vier Zonen eingeordnet (`BELOW_P10`, `BETWEEN_P10_AND_P50`, `BETWEEN_P50_AND_P90`, `ABOVE_P90`).
- **Abweichungsanalyse**: Das Tool weist die exakte Abweichung (Euro und %) gegenüber dem Median-Pfad (p50) aus, was dem Berater und Anleger als Frühwarn- und Diagnoseindikator dient.

