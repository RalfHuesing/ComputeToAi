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
10. **Portfolio fortschreiben**: Das Portfolio wird um die gezogene Rendite verändert, der nach Bucket-Auffüllung verbleibende Sparbetrag wird gemäß Allokation investiert, Entnahmen zur Rentenlücke werden gemäß Rebalancing-Regel entnommen.
11. **Steuern berechnen**: Auf thesaurierende Fondsanteile wird die Vorabpauschale angewendet, auf realisierte Gewinne bei Verkäufen die Abgeltungsteuer nach Teilfreistellung, verbleibendem Sparerpauschbetrag und ggf. Bestandsschutz des jeweiligen Lots. Details siehe Abschnitt „Besteuerung" unten.
12. **Ruin-Prüfung**: Reichen Cash-Bucket und Portfolio zusammen nicht aus, um eine fällige Entnahme, Anschaffung, Verbindlichkeiten-Rate oder Steuerzahlung zu decken, gilt der Lauf ab diesem Jahr als „Ruin" (die finanzspezifische Zielbedingung, siehe 01) – der Lauf wird trotzdem bis zum Lebensende fortgesetzt (Speicher auf 0 gedeckelt), damit Zeitpunkt und Ausmaß erkennbar bleiben statt nur das binäre Ereignis.
13. Wiederholen bis zum angenommenen Lebensende. Am Ende steht das (nach Steuern) verbleibende, nominale Endvermögen dieses Laufs.

Alle Beträge werden während der Simulation **konsequent nominal** geführt (kein Umschalten auf reale Größen innerhalb des Laufs); die Kaufkraft eines nominalen Ergebnisses in heutigem Geld wird bei Bedarf erst bei der **Auswertung** über das bereits vorhandene Berechnungen-Werkzeug `calculations_adjust_for_inflation` (siehe 06-Feature-Berechnungen.md) hergestellt, nicht durch ein zweites, paralleles Realwert-Modell im Simulationskern.

## Korrelation zwischen Anlageklassen

Die Jahresrenditen der Anlageklassen werden nicht unabhängig voneinander gezogen, sondern gemeinsam aus einer multivariaten Normalverteilung mit einer Korrelationsmatrix gezogen (technisch: Cholesky-Zerlegung) – die finanzspezifische Ausprägung des generischen Korrelations-Konzepts aus 01. Das ist Standard in der quantitativen Portfoliotheorie seit Markowitz (1952). Parametrisch (Erwartungswert/Volatilität/Korrelation als Eingabeparameter) statt historisches Bootstrapping ist die Basisannahme – einfacher umzusetzen und ausreichend für den aktuellen Bedarf; Bootstrapping (inkl. Fat-Tails und Autokorrelation) bleibt eine mögliche spätere Ausbaustufe.

Die Korrelationsmatrix erstreckt sich über **alle** Anlageklassen paarweise – auch innerhalb des risikobehafteten Anteils selbst (z. B. zwischen mehreren Aktien-ETFs auf unterschiedliche Regionen oder gegenüber alternativen Anlagen wie Kryptowährungen). Die Korrelation zwischen Aktien und Anleihen ist zudem nicht konstant, sondern regimeabhängig (niedrig/negativ in Niedriginflationsphasen, positiv in Hochinflationsphasen); Korrelationen zwischen risikobehafteten Anlageklassen steigen in Krisen tendenziell an.

Kalibrierung: Die Korrelationswerte folgen – ebenso wie erwartete Renditen und Volatilitäten – allgemein anerkannten wissenschaftlichen Standardannahmen aus der Kapitalmarktforschung, nicht einer projektspezifischen Schätzung. Eine statische, historisch kalibrierte Korrelationsmatrix ist die Basisannahme; ein regimeabhängiges Modell mit zwei Regimen bleibt eine mögliche spätere Ausbaustufe.

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

Der Wechsel der phasenspezifischen Parameter (z. B. Notfallpuffer-Monate) bei einem Phasenübergang erfolgt **schlagartig** zum Stichtag, nicht schrittweise geglättet – der Glidepath-Mechanismus unten deckt den einzigen Fall ab, in dem eine allmähliche Anpassung fachlich gewünscht ist (Vorfinanzierung einer bereits bekannten, terminierten Anschaffung), ein genereller Glättungsmechanismus für alle Phasenwechsel ist nicht vorgesehen.

**Vorrang bei der Sparquote**: In jedem Jahr wird die Sparquote zunächst genutzt, um den Bucket auf seine Zielgröße zu bringen bzw. zu halten; erst der darüber hinausgehende Betrag fließt ins Portfolio.

**Glidepath für flexible Anschaffungen**: Sobald eine flexible Anschaffung in den Bucket-Horizont eintritt, steigt die Ziel-Bucket-Größe schrittweise an, statt im Auslösejahr abrupt aus dem Portfolio zu entnehmen.

**Rückfall-Mechanismus**: Fällt der Bucket unter seine Zielgröße, wird er in den Folgejahren vorrangig wieder aufgefüllt; reicht die Sparquote dafür nicht, kann ergänzend aus dem Portfolio verkauft werden.

Der Cash-Bucket wird mit einem eigenen, niedrigen und risikoarmen Zinssatz verzinst (siehe 05-Feature-Finanzen-Parameter.md).

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

## Aggregation über alle Läufe

Nach Abschluss aller Läufe eines Plans werden berechnet: Perzentile des Endvermögens, Anteil der Läufe mit Ruin (Ruin-Wahrscheinlichkeit) und ggf. Alter bei Ruin, sowie – falls eine Zielvorgabe definiert ist – der Anteil der Läufe, die dieses Ziel erreichen.

## Ableitung der nötigen Sparquote

Die minimal nötige Sparquote kann ermittelt werden, indem die Sparquote als variabler Parameter behandelt und die Simulation wiederholt wird, bis die gewünschte Ziel-Erfolgswahrscheinlichkeit gerade erreicht wird (z. B. Bisektion über die Sparquote). Das methodische Detail wird erst bei der Programmentwicklung festgelegt.
