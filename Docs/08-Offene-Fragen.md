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

## Historische Kurs-Zeitreihe für den Ist-Depotverlauf

Ein Plan-Ist-Vergleich gegen die simulierten Perzentilkurven (siehe 10-Roadmap.md, Meilenstein 4) ist mit den aktuell geplanten Bausteinen nur als einzelner Stichtagsvergleich möglich, nicht als durchgängiger historischer Verlauf – dafür müsste bei jeder Kurs-Abfrage der jeweilige Marktwert zeitlich mitgeschrieben und dauerhaft gespeichert werden. Lohnt sich eine solche fortlaufende Kurs-/Wert-Historie, oder reicht der Stichtagsvergleich?

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

