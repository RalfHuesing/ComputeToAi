# Kern-Domänenmodell (generische Engine)

Dieses Dokument definiert die domänenneutralen Grundbegriffe der Simulations-Engine – unabhängig davon, ob damit Finanzen, sportliche Ausdauerleistung oder ein anderer „Bestand verändert sich über Zeit"-Prozess simuliert wird. Fachliche Instanzen (aktuell: das Finanzen-Feature) stehen in 03-Feature-Finanzen-Domaenenmodell.md und folgenden.

## Speicher (Store)

Ein Speicher ist ein benannter Bestand mit einem Saldo, der sich über die Zeit durch Effekte verändert. Ein Speicher hat immer eine Einheit (z. B. Euro, Kalorien, Kilometer) – der Kern selbst kennt keine bestimmte Einheit und trifft keine Annahme darüber, was ein Speicher „bedeutet".

Ein Speicher kann optional **Lot-/FIFO-Semantik** haben: Statt eines einzelnen Saldos hält er eine geordnete Folge datierter „Lots" (Menge, Entstehungszeitpunkt, ggf. weitere Metadaten wie „zu diesem Zeitpunkt gültige Regelwerk-Version"). Bei einem Abfluss werden zuerst die ältesten Lots verbraucht (First In, First Out). Das ist notwendig, wenn es auf das Entstehungsdatum eines Teilbetrags ankommt – z. B. bei einem Wertpapier-Depot, in dem einzelne Anteile unterschiedlich besteuert werden (siehe Bestandsschutz-Beispiel in 03), oder allgemein überall dort, wo „was zuerst da war, wird zuerst verbraucht" gilt.

## Effekt (Flow)

Ein Effekt ist eine Funktion, die für einen Zeitschritt aus dem aktuellen Zustand (Salden aller Speicher, aktueller Zeitpunkt, aktive Phase, ggf. eine Zufallsziehung) einen Zufluss oder Abfluss zu bzw. von einem oder mehreren Speichern berechnet. Effekte können:

- **zeitabhängig** sein (z. B. nur in einer bestimmten Phase wirken, siehe Phase unten),
- **stochastisch** sein (Ziehung aus einer Verteilung statt eines festen Werts) und dabei mit anderen stochastischen Effekten **korreliert** sein (siehe unten),
- von **anderen Speichern oder Effekten abhängen** (z. B. ein Effekt, der von der Höhe eines Speichersaldos abhängt).

Ein Effekt ist entweder **roh** – eine einfache, im jeweiligen Feature oder direkt per Prompt frei definierte Formel, geeignet für unkritische oder einmalige Fälle – oder ein **Baustein**: eine kuratierte, vorimplementierte und getestete Effekt-Vorlage für mathematisch anspruchsvolle oder fehleranfällige Fälle (z. B. korrelierte Renditen mehrerer Anlageklassen, eine mehrstufige Steuerformel mit Deckelung). Bausteine werden aktiviert und parametrisiert, nicht neu geschrieben – vergleichbar mit den eingebauten Funktionen einer Tabellenkalkulation gegenüber einer frei geschriebenen Zellformel: Wo bereits eine geprüfte Lösung existiert, wird sie genutzt statt ad hoc neu erfunden. Der Baustein-Katalog ist erweiterbar, ohne dass der Kern selbst geändert werden muss (siehe 02-Architektur-und-MCP.md).

## Korrelation

Effekte mit einer stochastischen Komponente können paarweise korreliert sein (technisch z. B. über eine gemeinsame multivariate Ziehung, etwa via Cholesky-Zerlegung). Korrelation ist damit keine Eigenschaft eines bestimmten Fachkonzepts wie „Anlageklassen", sondern eine generische Beziehung zwischen beliebigen stochastischen Effekten – im Finanz-Feature konkret zwischen Anlageklassen-Renditen, denkbar aber ebenso zwischen ganz anderen Effekten in einem anderen Feature.

## Zeitstrahl

Der Zeitstrahl definiert Startzeitpunkt, Dauer und Schrittweite eines Simulationslaufs. Beides ist frei wählbar – eine Finanzsimulation läuft typischerweise über 40–80 Jahre in Jahresschritten, ein anderer Anwendungsfall könnte über Stunden in Minutenschritten laufen. Der Kern selbst trifft keine Annahme über sinnvolle Schrittweiten oder Einheiten; das ist Sache des jeweiligen Feature-Moduls bzw. Plans.

## Phase

Über dem Zeitstrahl liegt optional eine geordnete, lückenlose Folge von Phasen (im Finanz-Feature z. B. Ausbildung, Erwerbsphase, Frühruhestandslücke, Rentenphase). Jede Phase hat einen Start- und Endzeitpunkt und kann Effekte an- oder abschalten bzw. deren Parameter verändern. Das verallgemeinert, was im Finanzkonzept „Lebensphase" heißt.

## Zielbedingung

Eine Zielbedingung definiert, wann ein Simulationslauf als Erfolg bzw. als „Ruin" gilt – meist: der Saldo eines oder mehrerer Speicher darf zu keinem Zeitpunkt eine kritische Schwelle (üblicherweise 0) unterschreiten. Das ist strukturell identisch mit der Ruinwahrscheinlichkeit der Versicherungsmathematik und wird bei einem Monte-Carlo-Lauf über viele Wiederholungen zu einer Erfolgswahrscheinlichkeit aggregiert.

## Plan

Ein Plan ist eine vollständige, benannte Konfiguration aus Speichern, Effekten (inkl. aktivierter Bausteine und deren Parametrisierung), Zeitstrahl, Phasen und Zielbedingung – die Instanz, die tatsächlich simuliert wird. Ein Plan ist jederzeit kopierbar; eine Kopie kann verändert und mit dem Original verglichen werden (Was-wäre-wenn). Für einen fairen Vergleich zweier Pläne sollten dieselben Zufallsziehungen verwendet werden (Common-Random-Numbers-Technik), damit ein Unterschied im Ergebnis tatsächlich die geänderte Konfiguration widerspiegelt und nicht nur zufälliges Rauschen zwischen unabhängigen Läufen. Ein Plan ersetzt den früheren, finanzspezifischen Begriff „Simulationsszenario".

## Simulationslauf & Simulationsergebnis

Ein Simulationslauf ist ein einzelner, vollständig durchgerechneter Pfad eines Plans über den Zeitstrahl, mit jeweils zufällig gezogenen Effektwerten. Ein Plan wird über viele Läufe ausgewertet (Monte-Carlo-Prinzip); das Simulationsergebnis ist die Auswertung über alle Läufe – z. B. Verteilung des Endsaldos (Perzentile), Wahrscheinlichkeit eines Ruins.

## Beziehung zu Feature-Modulen

Ein Feature-Modul (z. B. „Finanzen") definiert keine neuen Kern-Konzepte, sondern ausschließlich: benannte Speicher-Typen (z. B. „Portfolio", „Cash-Bucket"), einen Satz vorimplementierter Effekt-Bausteine (z. B. „Korrelierte Anlageklassen-Renditen", „Nachgelagerte Rentenbesteuerung") und sinnvolle Standard-Phasenmodelle. Der Kern selbst bleibt davon unberührt – ein neues Feature-Modul erweitert das System, ohne 01 zu ändern.
