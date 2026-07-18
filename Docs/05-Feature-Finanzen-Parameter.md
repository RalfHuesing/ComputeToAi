# Feature „Finanzen" – Parameter & Annahmen

Alle Größen, die das Finanzen-Feature konfigurierbar macht. Konkrete Zahlenwerte sind noch nicht festgelegt – das ist Aufgabe der Konfiguration je Plan, nicht des Konzepts.

## Lebensphasen

| Parameter | Beschreibung |
|---|---|
| Phasenliste | geordnete, lückenlose Folge von Lebensphasen (Name, Start, Ende) über den gesamten Zeitstrahl der Primärperson |
| Notfallpuffer-Monate je Phase | phasenspezifischer Wert statt einer einzelnen globalen Zahl; z. B. 0 in einer Ausbildungsphase ohne eigenes Einkommen, 6–12 in der Erwerbsphase, 0 in der Rentenphase |
| Erwerbsende / gesetzlicher Rentenbeginn | die beiden fachlich wichtigsten Phasengrenzen; lösen zusätzlich zum Phasenwechsel auch den Einkommensquellenwechsel und die Rentenabschlag/-zuschlag-Berechnung aus |

## Ausgangszustand

| Parameter | Beschreibung |
|---|---|
| Aktuelles Alter | Startpunkt der Simulation |
| Startbestand je Anlageklasse | bereits vorhandenes Vermögen, aufgeteilt auf die konfigurierten Anlageklassen, inkl. Lot-Historie (Kaufdatum je Teilbetrag, relevant für Bestandsschutz) |
| Startbestand Cash-Bucket | aktuell vorhandenes liquides Vermögen zum Simulationsstart |

## Personen & Haushalt

| Parameter | Beschreibung |
|---|---|
| Aktuelles Alter | Primärperson |
| Erwerbsende | Primärperson; Zeitpunkt, ab dem kein Erwerbseinkommen mehr fließt |
| Gesetzlicher Rentenbeginn | Primärperson; separat vom Erwerbsende, inkl. Rentenabschlag (0,3 %/Monat vorzeitig, max. 14,4 %) bzw. Rentenzuschlag (0,5 %/Monat Aufschub) |
| Lebenserwartungsannahme | Primärperson, bestimmt das Ende des Zeitstrahls |
| Partnerbeitrag | Netto-Cashflow weiterer Haushaltsmitglieder |

## Einkommen

| Parameter | Beschreibung |
|---|---|
| Einkommensströme | je Person, beliebig viele, mit Betrag und Gültigkeitszeitraum |
| Gehaltssteigerung | jährliche Wachstumsrate je Einkommensstrom |
| Gesetzliche Rente | Höhe je Person ab Renteneintritt, jährliche Anpassungsrate |

## Ausgaben

| Parameter | Beschreibung |
|---|---|
| Individuelle Fixausgaben | je Person |
| Gemeinsame Fixausgaben | Haushaltsebene |
| Altersabhängiger Ausgabenfaktor | Anpassung der Ausgaben im Ruhestand nach Alter |

## Anschaffungen

| Parameter | Beschreibung |
|---|---|
| Bezeichnung & Betrag | z. B. „neues Auto", 25.000 € |
| Typ | fix oder flexibel |
| Zieljahr / -alter | Referenzzeitpunkt |
| Toleranzfenster ± | nur bei flexiblem Typ |
| Referenzpfad | erwarteter Sparverlauf bis zum Zieljahr |
| Glidepath-Steilheit | Umschichtungsgeschwindigkeit risikoreich → risikoarm |
| Harte Deadline | spätester Zeitpunkt, an dem die Anschaffung erzwungen wird |

## Verbindlichkeiten

| Parameter | Beschreibung |
|---|---|
| Bezeichnung & Typ | z. B. „Hauskredit", „Konsumentenkredit", „Unterhalt" – rein beschreibend, technisch dieselbe Struktur |
| Ursprungsbetrag / aktuelle Restschuld | Startwert bzw. Stand zum Ausgangszustand |
| Zinssatz | jährlicher Zinssatz auf die Restschuld, kann 0 % sein |
| Periodische Rate | regelmäßig fällige Zahlung |
| Endbedingung | Restschuld = 0 (tilgungsgetrieben) oder festes/ereignisbezogenes Datum |
| Sondertilgungsoption | nur bei Zinssatz > 0 % relevant |
| Zuordnung | Haushalt oder Person |

## Kapitalmarkt

| Parameter | Beschreibung |
|---|---|
| Anlageklassen | beliebig viele, z. B. Aktien-ETF je Region, Anleihen-ETF, Tagesgeld, ggf. Kryptowährungen |
| Erwartete Rendite p.a. | je Anlageklasse |
| Volatilität / Verteilung | je Anlageklasse |
| Korrelationsmatrix | paarweise Korrelationen zwischen allen Anlageklassen, Basisannahme aus wissenschaftlichen Standardwerten, optional regimeabhängig als Ausbaustufe |
| Inflation | Erwartungswert und ggf. Volatilität |

## Portfolio

| Parameter | Beschreibung |
|---|---|
| Allokation | Aufteilung über Anlageklassen |
| Rebalancing-Regel | Frequenz und Methode |
| Zuordnung | gemeinsames Portfolio oder getrennt je Person |

## Steuern (deutsches Steuerrecht)

| Parameter | Beschreibung |
|---|---|
| Abgeltungsteuersatz | 25 % auf realisierte Kapitalerträge |
| Solidaritätszuschlag | 5,5 % der Abgeltungsteuer |
| Kirchensteuersatz | 8 % oder 9 %, sonst 0 % |
| Sparerpauschbetrag | 1.000 € pro Person bzw. 2.000 € bei Zusammenveranlagung (Stand 2026) |
| Vorabpauschale-Basiszins | jährlich vom BMF festgelegt (Beispiel 2026: 3,20 %) |
| Teilfreistellungssatz je Anlageklasse | 30 % Aktienfonds, 15 % Mischfonds, 0 % Rentenfonds |
| Bestandsschutz-Stichtag | 1.1.2009 (Einführung Abgeltungsteuer) – Lots davor dauerhaft steuerfrei veräußerbar |
| Besteuerungsanteil gesetzliche Rente | abhängig vom Rentenbeginn-Jahr (2026: 84 %), steigt 0,5 Punkte/Jahr, 100 % ab 2058 |
| Grundfreibetrag | mindert die einkommensteuerpflichtige Bemessungsgrundlage der Rente |
| KVdR-Beitragssatz | 14,6 % + Ø Zusatzbeitrag 2,9 % (2026), hälftig subventioniert, nur bei GKV |
| Pflegeversicherungsbeitrag Rentner | 3,6 % bzw. 4,2 % Kinderlose (2026), vollständig vom Rentner getragen, nur bei GKV |
| Krankenversicherungsstatus | GKV oder PKV, Eingabeparameter je Person – bestimmt, ob KVdR/Pflegeversicherung (GKV) oder eine fest konfigurierte PKV-Prämie (Rentenphase) bzw. eine Nettogehalt-Annahme ohne KVdR-Abzug (Erwerbsphase) angewendet wird |

## Cash-Bucket (Liquiditätspuffer)

| Parameter | Beschreibung |
|---|---|
| Notfallpuffer-Monate | phasenspezifischer Wert, deckt Einkommensausfallrisiko |
| Nah-Horizont | kurzer rollierender Zeitraum in Jahren (z. B. 1–2) |
| Entnahmehorizont | Jahre, mit denen die Entnahmeabhängigkeit multipliziert wird (z. B. 3–5) |
| Entnahmeabhängigkeit | berechnete Größe, kein Eingabeparameter |
| Verzinsung Cash-Bucket | niedrige, risikoarme Rendite |
| Vorfinanzierungslogik flexible Anschaffungen | Glidepath-Ansparung vor Fälligkeit |

## Ziel & Risiko

| Parameter | Beschreibung |
|---|---|
| Zielvermögen am Lebensende | 0, Sicherheitspuffer X, oder Erbe X |
| Ziel-Erfolgswahrscheinlichkeit | z. B. 90 % der Läufe sollen das Ziel erreichen |

## Simulation

| Parameter | Beschreibung |
|---|---|
| Anzahl Simulationsläufe | z. B. 1.000–10.000 |
| Zeitschritt | jährlich |
