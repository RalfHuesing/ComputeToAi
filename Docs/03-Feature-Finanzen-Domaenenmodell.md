# Feature „Finanzen" – Domänenmodell

Dieses Dokument beschreibt, wie das Finanzen-Feature die generischen Kern-Begriffe aus 01-Kern-Domaenenmodell.md konkret instanziiert. Alle hier beschriebenen Begriffe sind fachliche Namen für Speicher, Effekte bzw. Bausteine des Kerns, kein eigenständiges Kern-Konzept.

## Zuordnung Kern → Finanz-Feature

| Kern-Begriff | Finanz-Instanz(en) |
|---|---|
| Speicher | Portfolio (Depot), Cash-Bucket, Restschuld einer Verbindlichkeit |
| Effekt (roh) | einfache Ausgabe, einfache fixe Anschaffung |
| Effekt (Baustein) | Einkommensstrom inkl. Wachstum, Abgeltungsteuer-Baustein, Baustein „Nachgelagerte Rentenbesteuerung", Baustein „Korrelierte Anlageklassen-Renditen", Verbindlichkeits-Tilgungsplan, Inflation |
| Phase | Lebensphase (Ausbildung, Erwerbsphase, Frühruhestandslücke, Rentenphase) |
| Zielbedingung | Ruin (Portfolio + Cash-Bucket reichen nicht mehr für eine fällige Zahlung) |
| Plan | Simulationsszenario einer Primärperson |

## Haushalt und Primärperson-Prinzip

Der Haushalt ist die oberste Planungseinheit, aber die Simulation wird grundsätzlich aus der Perspektive einer einzelnen Primärperson (im konkreten Fall: Ralf) geführt. Nur die Primärperson hat eine eigene Zielbedingung; nur ihr Lebensende bestimmt den Zeitstrahl. Weitere Personen im Haushalt (z. B. die Partnerin einer Lebensgemeinschaft) werden nicht als vollständig eigenständige Personen mit eigener Zielbedingung modelliert, sondern vereinfacht als **Partnerbeitrag**: ein Netto-Cashflow-Effekt (deren Einkommen abzüglich ihrer individuellen Ausgaben), der in den gemeinsamen Haushaltscashflow einfließt.

Das hat eine wichtige Konsequenz: Ändert sich etwas beim Partner – z. B. eine niedrigere gesetzliche Rente der Partnerin – wird das nicht als eigenes Partner-Ruin-Risiko modelliert, sondern schlägt sich unmittelbar als höhere Nettoausgabenlast bzw. geringerer Netto-Beitrag beim Haushaltscashflow der Primärperson nieder (siehe Rentenlücke unten).

## Person

Die **Primärperson** hat: ein aktuelles Alter, ein Erwerbsende (Zeitpunkt, ab dem kein Erwerbseinkommen mehr fließt – kann vom gesetzlichen Rentenbeginn abweichen, siehe unten), einen gesetzlichen Rentenbeginn mit zugehörigem Rentenanspruch, ein angenommenes Lebensende (Lebenserwartung, bestimmt das Ende des Zeitstrahls), individuelle Einkommensströme und individuelle Ausgaben.

Weitere Personen im Haushalt (**Partnerbeitrag**) werden reduziert auf: einen Netto-Cashflow (Einkommen minus individuelle Ausgaben, inkl. eigener gesetzlicher Rente ab deren Rentenbeginn), ohne eigene Zielbedingung und ohne eigenen Zeitstrahl. Details und Grenzen dieser Vereinfachung (z. B. Tod oder Wegfall des Partnerbeitrags) stehen in 08-Offene-Fragen.md.

## Lebensphase (Phase)

Über der gesamten Parametrisierung steht das generische Phasen-Konzept aus 01: Der Zeitstrahl der Primärperson wird in eine geordnete, lückenlose Folge von Lebensphasen unterteilt (z. B. Ausbildungsphase, Erwerbsphase, Frühruhestandslücke, Rentenphase – die konkrete Liste ist Teil der Plan-Konfiguration, nicht des Konzepts). Jede Lebensphase hat einen Start- und Endzeitpunkt sowie einen eigenen Satz phasenspezifischer Parameterwerte.

Der Grund dafür: Viele Effekte sind über die gesamte Lebenszeit hinweg nicht sinnvoll konstant, sondern hängen von der jeweiligen Lebenssituation ab. Beispiele: Vor dem ersten eigenen Einkommen ist eine nennenswerte Sparquote unrealistisch; während der Erwerbsphase ist ein Einkommensausfallpuffer relevant (Kündigungs-/Krankheitsrisiko); in der Rentenphase entfällt dieses Risiko weitgehend, dafür entsteht ein Entnahmepuffer-Bedarf. Statt für jeden dieser Fälle einen eigenen Sonderfall im Modell zu verankern, schlägt jeder phasenabhängige Parameter (aktuell definiert: Notfallpuffer-Monate; weitere Kandidaten siehe 05-Feature-Finanzen-Parameter.md) für das jeweilige Simulationsjahr in der aktiven Lebensphase nach.

### Erwerbsende vs. gesetzlicher Rentenbeginn

Diese beiden Zeitpunkte sind bewusst getrennte Größen, nicht ein einzelner „Renteneintritt", und zugleich die beiden fachlich wichtigsten Phasengrenzen: Das **Erwerbsende** ist der frei wählbare (und damit für Was-wäre-wenn-Szenarien wie „früher Ruhestand" zentrale) Zeitpunkt, ab dem die Primärperson kein Erwerbseinkommen mehr hat – er beendet die Erwerbsphase. Der **gesetzliche Rentenbeginn** ist der Zeitpunkt, ab dem die gesetzliche Rente einsetzt; er kann vom Regelrenteneintrittsalter abweichen, wenn die Rente vorzeitig (mit Abschlag) oder später (mit Zuschlag) in Anspruch genommen wird – er beginnt die Rentenphase. Liegt das Erwerbsende vor dem gesetzlichen Rentenbeginn, entsteht dazwischen die Lebensphase **Frühruhestandslücke** (siehe Rentenlücke unten), die vollständig aus Cash-Bucket und Portfolio finanziert werden muss.

## Einkommensstrom (Income Stream)

Ein Zufluss-Effekt, zugeordnet zu einer Person oder dem Haushalt. Beispiele: Nettogehalt, Nebeneinkünfte, ab Renteneintritt die gesetzliche Rente. Ein Einkommensstrom hat einen Betrag, eine Gültigkeitsspanne (z. B. bis Renteneintritt) und eine Wachstumsannahme (z. B. jährliche Gehaltssteigerung, Rentenanpassung).

## Ausgabe (Expense)

Ein Abfluss-Effekt für laufende Kosten, unterschieden nach:

- **Individuelle Ausgabe**: gehört zu einer Person, betrifft nur diese.
- **Gemeinsame Ausgabe**: gehört zum Haushalt, wird von beiden Partnern gemeinsam getragen.

Ausgaben unterliegen der Inflation (ebenfalls ein Effekt, siehe unten) und können ein altersabhängiges Profil haben (z. B. geringere Ausgaben im hohen Alter).

## Anschaffung (Acquisition)

Ein größerer, nicht-laufender Abfluss-Effekt mit eigenem Zeitbezug. Es gibt zwei Typen:

- **Fixe Anschaffung**: fester Zeitpunkt, z. B. der jährliche Urlaub.
- **Flexible Anschaffung**: Zieljahr mit Toleranzfenster (z. B. ±2 Jahre) und einer Trigger-Regel, die bestimmt, wann innerhalb des Fensters die Anschaffung tatsächlich stattfindet (siehe 04-Feature-Finanzen-Methodik.md). Am Rand des Toleranzfensters greift eine harte Deadline.

Eine Anschaffung hat einen Betrag, einen Zeitbezug (fest oder Zieljahr + Toleranzfenster + Trigger-Regel) und eine Zuordnung (Haushalt oder Person).

## Verbindlichkeit (Liability)

Eine periodisch zu bedienende Verpflichtung mit einem tendenziell fallenden Restbetrag – strukturell ein Speicher mit negativem Zielsaldo (Restschuld) plus ein Abfluss-Effekt (die Rate), der zusätzlich zu den Ausgaben den Haushaltscashflow belastet. Beispiele: Hauskredit, Konsumentenkredit, Unterhaltsverpflichtung. Diese Fälle werden als Instanzen eines einzigen allgemeinen Konzepts modelliert, da sie sich strukturell nur in wenigen Parametern unterscheiden.

Eine Verbindlichkeit hat einen Ursprungsbetrag bzw. eine aktuelle Restschuld, eine periodische Rate, einen Zinssatz (der bei jeder Rate anteilig anfällt und die Restschuld nur um den Tilgungsanteil reduziert – der Zinssatz kann auch 0 % sein, z. B. bei Unterhalt) sowie eine Endbedingung: entweder die Restschuld erreicht null (Kredite) oder ein festes bzw. ereignisbezogenes Datum wird erreicht (z. B. Unterhalt bis zur Volljährigkeit eines Kindes). Hauskredit und Konsumentenkredit sind dieselbe Instanz mit Zinssatz > 0 % und tilgungsgetriebenem Ende; Unterhalt ist dieselbe Instanz mit Zinssatz = 0 % und datums-/ereignisgetriebenem statt tilgungsgetriebenem Ende.

Optional kann eine Verbindlichkeit mit Zinssatz > 0 % eine Sondertilgungsoption haben: die Möglichkeit, zusätzlich zur planmäßigen Rate Kapital vorzeitig zu tilgen, statt es ins Portfolio zu investieren – ein Vergleich zwischen einer sicheren, garantierten „Rendite" (dem ersparten Kreditzins) und einer unsicheren, im Erwartungswert höheren Portfoliorendite (siehe 04-Feature-Finanzen-Methodik.md).

## Anlageklasse (Asset Class)

Eine Kategorie von Finanzanlagen, z. B. Aktien-ETF, Anleihen-ETF, Tagesgeld. Jede Anlageklasse hat eine erwartete Rendite und eine Volatilität (bzw. Verteilungsannahme), aus der über den Baustein „Korrelierte Anlageklassen-Renditen" zufällige, untereinander korrelierte Jahresrenditen gezogen werden (siehe 04-Feature-Finanzen-Methodik.md). Für die steuerliche Behandlung hat jede Anlageklasse zudem einen Teilfreistellungssatz (Investmentsteuergesetz, siehe unten).

## Besteuerung (deutsches Steuerrecht)

Da es sich um einen deutschen Haushalt handelt, wird die Kapitalertragsbesteuerung vollständig nach deutschem Steuerrecht als Baustein abgebildet, nicht nur pauschal. Zentrale Bausteine: Abgeltungsteuer auf realisierte Kapitalerträge, der jährliche Sparerpauschbetrag als Freibetrag auf Kapitalerträge, die Vorabpauschale als jährliche Vorab-Besteuerung thesaurierender Fondsanteile, sowie die Teilfreistellung. Details und Formeln stehen in 04-Feature-Finanzen-Methodik.md, konkrete Sätze in 05-Feature-Finanzen-Parameter.md.

Ein wichtiges Beispiel dafür, warum Steuer-Bausteine an Speicher-Lots statt global am Regelwerk hängen müssen (siehe 02-Architektur-und-MCP.md, Abschnitt „Regelwerk-Templates"): Aktien und Fondsanteile, die **vor dem 1.1.2009** (Einführung der Abgeltungsteuer) gekauft wurden, genießen dauerhaften Bestandsschutz – ihr Veräußerungsgewinn bleibt unbegrenzt steuerfrei, unabhängig vom tatsächlichen Verkaufsdatum, sogar über eine Vererbung hinweg. Ein Portfolio-Speicher muss sich also je Lot merken, unter welchem Steuerregime es entstanden ist, nicht nur, welches Regelwerk gerade aktuell gilt.

## Portfolio (Depot)

Ein Speicher mit Lot-Semantik: eine Menge von Anlageklassen mit einer Allokation (z. B. 60 % Aktien / 40 % Anleihen) und einer Rebalancing-Regel. Ein Portfolio kann dem Haushalt gemeinsam oder einzelnen Personen zugeordnet sein (offene Frage, siehe 08-Offene-Fragen.md). In das Portfolio fließt die Sparquote; aus dem Portfolio werden im Ruhestand Entnahmen zur Deckung der Rentenlücke getätigt.

## Cash-Bucket (Liquiditätspuffer)

Ein separater, liquide gehaltener Speicher neben dem investierten Portfolio, quasi risikofrei verzinst (z. B. Tagesgeld). Die Sparquote wird vorrangig zur Auffüllung des Buckets auf seine Zielgröße verwendet; erst der überschüssige Betrag fließt in das investierte Portfolio.

Der Cash-Bucket erfüllt je nach Lebensphase zwei unterschiedliche Schutzfunktionen, die unterschiedlich bemessen werden:

- **Einkommensausfallpuffer** (relevant vor allem in der Erwerbsphase): schützt vor einem vorübergehenden Wegfall des Erwerbseinkommens (Kündigung, Krankheit), bemessen in Monaten der laufenden Ausgaben.
- **Entnahmepuffer** (relevant sobald und soweit Ausgaben aus dem Portfolio statt aus sicherem Einkommen gedeckt werden müssen): schützt vor Sequence-of-Returns-Risiko, bemessen an der **Entnahmeabhängigkeit** – dem Anteil der Ausgaben, der nicht durch sichere Einkommensquellen (gesetzliche Rente, Partnerbeitrag) gedeckt ist.

Die Entnahmeabhängigkeit ergibt sich Jahr für Jahr aus (Ausgaben − gesetzliche Rente − Partnerbeitrag) / Ausgaben, begrenzt auf [0, 1]. In der Frühruhestandslücke ist sie exakt 100 %; nach gesetzlichem Rentenbeginn sinkt sie in dem Maß, wie die Rente die Ausgaben deckt.

Zusätzlich enthält der Cash-Bucket, unabhängig von der Lebensphase, eine reine Nahsicht-Komponente: die Summe der geplanten Fixausgaben und Urlaube innerhalb eines kurzen rollierenden Horizonts sowie einen anteiligen Vorfinanzierungsbetrag für flexible Anschaffungen, deren Zieldatum in diesen Horizont fällt (siehe 04-Feature-Finanzen-Methodik.md).

## Ausgangszustand (Startvermögen)

Jeder Plan startet nicht bei null, sondern mit einem konkreten Ausgangszustand zum heutigen Tag: dem aktuellen Alter der Primärperson sowie dem bereits vorhandenen Vermögen, aufgeteilt auf den aktuellen Bestand je Anlageklasse (inkl. der Lot-Historie für Bestandsschutz-Fälle) und den aktuellen Bestand im Cash-Bucket. Erst ab diesem Ausgangspunkt schreibt die Simulation Jahr für Jahr fort. Konkrete Werte gehören in 05-Feature-Finanzen-Parameter.md.

## Rentenlücke (Pension Gap)

Die Differenz zwischen den Ausgaben im Ruhestand und den verfügbaren Renteneinkünften (gesetzliche Rente der Primärperson zzgl. Partnerbeitrag). Diese Lücke muss durch Entnahmen aus Cash-Bucket und Portfolio gedeckt werden.

Ein Sonderfall ist die **Frühruhestandslücke**: der Zeitraum zwischen dem Erwerbsende der Primärperson und ihrem gesetzlichen Rentenbeginn, in dem es kein Erwerbseinkommen und noch keine gesetzliche Rente gibt – die Rentenlücke ist in dieser Phase also potenziell so groß wie die vollen Ausgaben abzüglich eines etwaigen Partnerbeitrags.

## Zielvorgabe (Target)

Definiert, was als „Erfolg" gilt: Endvermögen auf null (Verbrauchsziel), ein definierter Sicherheitspuffer, oder ein Vererbungsbetrag. Die Zielvorgabe ist die konkrete Ausprägung der generischen Zielbedingung (siehe 01) für den Finanz-Fall und beeinflusst, wie die Erfolgswahrscheinlichkeit berechnet wird.

## Beziehungsübersicht

```
Haushalt (1)     ── hat ──> (1) Primärperson
Haushalt (1)     ── hat ──> (0..n) Partnerbeitrag (vereinfachter Netto-Cashflow-Effekt)
Haushalt (1)     ── hat ──> (0..n) Gemeinsame Ausgabe
Haushalt (1)     ── hat ──> (0..n) Anschaffung
Haushalt (1)     ── hat ──> (0..n) Verbindlichkeit (Kredit, Unterhalt)
Haushalt (1)     ── hat ──> (1..n) Portfolio (Speicher)
Haushalt (1)     ── hat ──> (1) Cash-Bucket (Speicher)
Primärperson (1) ── hat ──> (0..n) Einkommensstrom (Effekt)
Primärperson (1) ── hat ──> (0..n) Individuelle Ausgabe (Effekt)
Primärperson (1) ── hat ──> Erwerbsende (separat von gesetzlichem Rentenbeginn)
Primärperson (1) ── hat ──> (0..1) gesetzliche Rente (ab gesetzlichem Rentenbeginn)
Portfolio (1)    ── besteht aus ──> (1..n) Anlageklasse (mit Allokation)
Plan (1)         ── referenziert ──> Haushalt + alle Parameter
Plan (1)         ── erzeugt ──> (n) Simulationslauf ──> (1) Simulationsergebnis
```
