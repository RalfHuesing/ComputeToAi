# Quellen & externes Wissen

Dieses Dokument sammelt externe Fakten (v. a. deutsches Steuer- und Rentenrecht sowie Vorbilder für die Architektur), die ins Konzept eingeflossen sind, mit Quelle und Abrufdatum. Zweck: spätere Nachvollziehbarkeit und einfaches Prüfen, ob ein Wert noch aktuell ist (siehe CLAUDE.md, Regel „Quellentreue"). Neue Recherchen werden hier ergänzt, nicht nur im jeweiligen Fachdokument verlinkt.

## Kapitalertragsteuer

| Aussage | Stand | Quelle | Abgerufen |
|---|---|---|---|
| Sparerpauschbetrag: 1.000 € (Einzelperson) bzw. 2.000 € (Zusammenveranlagung) | 2026 | [Sparerpauschbetrag 2026 – Raisin](https://www.raisin.com/de-de/steuer/sparerpauschbetrag/) | 2026-07-18 |
| Vorabpauschale-Basiszins: 3,20 % (Formel: Fondswert × Basiszins × 0,7) | 2026, § 18 Abs. 4 InvStG | [BMF: Basiszins zur Berechnung der Vorabpauschale](https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Steuerarten/Investmentsteuer/2026-01-13-basiszins-berechnung-vorabpauschale.html) | 2026-07-18 |
| Teilfreistellung: 30 % Aktienfonds (>50 % Aktienquote), 15 % Mischfonds (≥25 %), 0 % Rentenfonds | § 20 InvStG, unbefristet | [§ 20 InvStG – gesetze-im-internet.de](https://www.gesetze-im-internet.de/invstg_2018/__20.html) | 2026-07-18 |
| Bestandsschutz: Aktien/Fondsanteile vor dem 1.1.2009 (Einführung Abgeltungsteuer) bleiben beim Verkauf dauerhaft steuerfrei, auch über Vererbung hinweg (Ausnahme: Beteiligungen ≥ 1 %) | laufend gültige Übergangsregel | [Erben aufgepasst: Wann Gewinne aus vor 2009 gekauften Aktien steuerfrei sind – t-online](https://www.t-online.de/finanzen/frag-t-online-ihr-geld/id_101099960/abgeltungssteuer-was-gilt-fuer-alt-aktien-vor-2009-.html), [Altanteile (erworben vor 2009) – Union Investment](https://www.union-investment.de/fonds_depot/fonds_verstehen/lexikon/altanteile) | 2026-07-18 |

## Kryptowährungen

| Aussage | Stand | Quelle | Abgerufen |
|---|---|---|---|
| Nach 1 Jahr Haltefrist steuerfrei (privates Veräußerungsgeschäft, § 23 EStG); Freigrenze 1.000 €/Jahr innerhalb der Frist; Abschaffung der Haltefrist wird politisch diskutiert, aber 2026 nicht beschlossen | 2026 | [Bitcoin-Steuer 2026 – CoinTracking](https://cointracking.info/de/steuer-guides/deutschland/bitcoin-steuer/), [Update zur Besteuerung von Kryptowerten – CoinTracking](https://cointracking.info/de/steuer-guides/deutschland/update-zur-besteuerung-von-kryptowerten/) | 2026-07-18 |

## Gesetzliche Rente

| Aussage | Stand | Quelle | Abgerufen |
|---|---|---|---|
| Rentenabschlag: 0,3 %/Monat vorzeitiger Bezug, max. 14,4 % (4 Jahre); Rentenzuschlag: 0,5 %/Monat Aufschub | laufend gültige Regel, Beispielrechnung 2026 | [Rentenabschlag – VZ VermögensZentrum](https://www.vermoegenszentrum.de/wissen/rentenabschlag), [Rentenlexikon Rentenabschlag – Deutsche Rentenversicherung](https://www.deutsche-rentenversicherung.de/SharedDocs/Glossareintraege/DE/R/rentenabschlag.html) | 2026-07-18 |
| Besteuerungsanteil für Rentenbeginn 2026: 84 % (16 % Rentenfreibetrag); steigt seit 2023 um 0,5 Prozentpunkte/Jahr (Wachstumschancengesetz, vorher 1 Punkt/Jahr); 100 % erst ab Rentenbeginn 2058 | 2026 | [Steueranteil für Neu-Rentner liegt 2026 bei 84 Prozent – Deutsche Rentenversicherung](https://www.deutsche-rentenversicherung.de/DRV/DE/Ueber-uns-und-Presse/Presse/Meldungen/2026/20260216-steueranteil-neurentner) | 2026-07-18 |
| KVdR (Krankenversicherung der Rentner): allgemeiner Beitragssatz 14,6 % + Ø Zusatzbeitrag 2,9 %, jeweils hälftig von der Rentenversicherung subventioniert | 2026 | [KVdR 2026 – buerger-geld.org](https://www.buerger-geld.org/news/finanzen/kvdr-2026-beitragssatz-bleibt-gleich-belastung-fuer-rentner-steigt/) | 2026-07-18 |
| Pflegeversicherung Rentner: 3,6 % (4,2 % für Kinderlose ab 23 Jahren), vollständig vom Rentner getragen, kein Zuschuss | 2026 | [Kranken- und Pflegeversicherung der Rentner – Deutsche Rentenversicherung](https://www.deutsche-rentenversicherung.de/DRV/DE/Rente/In-der-Rente/Kranken-und-Pflegeversicherung-der-Rentner/kranken-und-pflegeversicherung-der-rentner.html) | 2026-07-18 |

## Architektur-Vorbilder (generischer Kern)

| Aussage | Quelle | Abgerufen |
|---|---|---|
| System Dynamics (Stocks/Flows) als etabliertes Modellierungsparadigma; PySD als Python-Implementierung (Stocks, Flows, Parameter, Zwischenzustände speicherbar/fortsetzbar) | [PySD Documentation](https://pysd.readthedocs.io/), [GitHub – SDXorg/pysd](https://github.com/SDXorg/pysd) | 2026-07-18 |
| OpenFisca: Rules-as-Code-Engine mit Variablen/Parametern/Reforms, Python-basiert, AGPLv3-Lizenz, kein fertiges Deutschland-Paket vorhanden | [OpenFisca](https://openfisca.org/en/), [OpenFisca-Core – GitHub](https://github.com/openfisca/openfisca-core), [OpenFisca Parameters Doc](https://openfisca.org/doc/coding-the-legislation/legislation_parameters.html) | 2026-07-18 |

## Hinweis zur Pflege

Alle Prozentsätze und Freibeträge in diesem Dokument sind Stand des jeweiligen Abrufdatums. Da sich Steuer- und Sozialversicherungsrecht jährlich ändert (Basiszins, Besteuerungsanteil, Beitragssätze etc.), sollten die Werte vor einer tatsächlichen Implementierung erneut geprüft werden.
