# Offene Fragen & Entscheidungen

Dinge, die im weiteren Konzeptgespräch noch geklärt werden müssen.

## Fragen zum generischen Kern

**Zirkuläre Effekt-Abhängigkeiten**: Wenn Effekte beliebig voneinander abhängen dürfen (z. B. eine Entscheidung hängt von einer erwarteten Rendite ab, die selbst von einer Zufallsziehung abhängt, die wiederum von einer Korrelationsstruktur abhängt, die von Entscheidungen im selben Jahr beeinflusst wird), braucht der Kern eine explizite, nachvollziehbare Auswertungsreihenfolge (z. B. topologische Sortierung des Abhängigkeitsgraphen). Wie wird das technisch gelöst, und wie zeigt die Selbstbeschreibung einem Agenten, welche Effekte von welchen abhängen, damit er keine unlösbare Konfiguration baut?

**Sandbox/Sicherheit bei rohen Effekten**: Sobald ein Agent (oder ein Nutzer) einen „rohen" Effekt frei formuliert, nähert sich das einer kleinen Skriptsprache an. Wie wird verhindert, dass ein fehlerhafter oder böswilliger roher Effekt die Simulation unbemerkt verfälscht oder unsicheren Code ausführt?

**Generische Korrelations-Mechanik**: Wie deklariert ein beliebiger, auch domänenfremder Effekt technisch, mit welchen anderen Effekten er korreliert ist, ohne dass „Korrelation" an ein bestimmtes Fachkonzept wie „Anlageklassen" gebunden bleibt?

**Grenzen der Generizität**: Ab wann lohnt sich ein neuer, eigener Baustein bzw. ein neues Feature-Modul gegenüber einem rohen, ad hoc definierten Effekt? Gibt es Kriterien (Komplexität der Mathematik, Wiederverwendungshäufigkeit, Fehlerkosten), nach denen entschieden wird, was in den kuratierten Katalog aufgenommen wird?

**Validierung an einer zweiten Domäne**: Der Kern ist bewusst domänenneutral entworfen, aber bisher nur am Finanzfall im Detail durchdacht. Wann und mit welcher zweiten, deutlich andersartigen Domäne (z. B. Ausdauersport, Startup-Runway) soll die tatsächliche Generizität geprüft werden?

## Fragen zur Architektur/MCP

**Baustein-Katalog-Governance**: Wer pflegt und versioniert die kuratierten Bausteine, und nach welchem Prozess werden neue aufgenommen oder bestehende geändert?

**Regelwerk-Template-Vertrauensmodell**: Wie wird ein heruntergeladenes Regelwerk-Template (z. B. „Steuer-2027") vor der Anwendung geprüft – Signierung, mitgelieferte Testfälle mit erwartetem Ergebnis, manuelle Bestätigung durch den Nutzer?

**Technische Umsetzung des Bestandsschutzes**: Wie genau merkt sich ein Speicher-Lot, unter welcher Regelwerk-Version es entstanden ist, und wie wird das bei einer späteren Regelwerk-Aktualisierung konsistent gehalten?

**JSON-Schema-Versionierung und Migration**: Wie wird sichergestellt, dass eine ältere lokale Profildatei von einer neueren Serverversion entweder korrekt migriert oder klar als veraltet erkannt wird?

**Mehrgeräte-/Mehrsitzungs-Konsistenz**: Die lokale JSON-Datei als einzige Quelle der Wahrheit funktioniert für Einzelnutzung auf einem Gerät gut. Was passiert bei parallelen Schreibzugriffen (mehrere Agenten-Sitzungen, mehrere Geräte über Cloud-Sync)? Reicht ein einfacher Zeitstempel-/Versionscheck, oder braucht es mehr?

**Performance interaktiver Ad-hoc-Anfragen**: Eine Chat-eingebettete Frage wie „kann ich mir das jetzt leisten?" sollte spürbar schneller beantwortbar sein als eine volle Batch-Simulation mit tausenden Läufen. Reicht eine reduzierte Laufzahl für solche Anfragen, eine Wiederverwendung des letzten Batch-Ergebnisses mit einem schnellen Differenz-Check, oder braucht es einen eigenen, leichteren Rechenweg?

**Ablageort von Prompt-/Workflow-Dateien**: 00-Vision.md sieht vor, dass ein Agent über Prompts/Workflow-Dateien (Markdown) weiß, welche Rolle er gerade einnimmt (z. B. „du bist mein Finanzberater"). Wo im Repo liegen solche Dateien, in welchem Format/welcher Konvention, und wie unterscheiden sie sich von den `.agents/rules/*.mdc`-Dateien (die Entwicklungsregeln für Coding-Agenten sind, keine fachlichen Nutzer-Workflows)?

## Detailfragen zur Besteuerung (Feature Finanzen)

Wie wird der gemeinsame Sparerpauschbetrag (2.000 €) auf mehrere Depots/Anlageklassen aufgeteilt, wenn nicht alle Erträge in einem Depot anfallen? Sollen Verlustverrechnungstöpfe (allgemeiner Verlusttopf vs. Aktien-Verlusttopf) und Verlustvorträge über mehrere Jahre abgebildet werden?

## Alternative Anlagen (z. B. Kryptowährungen) und Besteuerung

Soll das Modell auch Anlageklassen außerhalb von Fonds/ETFs unterstützen, z. B. Kryptowährungen? Diese unterliegen in Deutschland (Stand 2026) einer grundlegend anderen Besteuerung (privates Veräußerungsgeschäft nach § 23 EStG, Freigrenze 1.000 €/Jahr innerhalb der Haltefrist, danach steuerfrei) – das bräuchte einen eigenen Steuer-Baustein.

## Detailfragen zum Referenzpfad/Glidepath

Wie wird der Referenzpfad konkret definiert – linear interpoliert oder nach einer anderen Kurve? Wie steil soll der Glidepath standardmäßig sein, pro Anschaffung oder global konfigurierbar?

## Portfolio-Struktur

Ein gemeinsames Portfolio für den Haushalt, oder getrennte Depots je Person mit ggf. unterschiedlicher Allokation und steuerlicher Behandlung?

## Detailgrad der Ausgabenmodellierung

Reicht ein pauschaler Ausgabenbetrag je Person/Haushalt mit altersabhängigem Faktor, oder sollen Ausgaben nach Kategorien (Wohnen, Konsum, Gesundheit, Freizeit) getrennt modelliert werden?

## Cash-Bucket-Details

Wie wird priorisiert, wenn die Sparquote weder Bucket-Auffüllung noch reguläre Sparrate vollständig decken kann? Wie läuft der Übergang des Einkommensausfallpuffers nach dem Erwerbsende ab – schlagartig oder schrittweise? Welche konkreten Werte sind für Notfallpuffer-Monate und Entnahmehorizont sinnvoll, und sollte der Entnahmehorizont selbst mit dem Alter variieren?

## Detailfragen zu Verbindlichkeiten (Kredite, Unterhalt)

Nach welcher konkreten Regel wird zwischen Sondertilgung und Investition entschieden? Sind Kreditzinsen steuerlich absetzbar (z. B. Werbungskosten bei vermieteter Immobilie)? Ist Unterhalt steuerlich relevant (Realsplitting, Kindesunterhalt)? Soll ein variabler Hauskreditzins (Anschlussfinanzierung) als unsichere Größe abgebildet werden? Wie verknüpft sich ein Hauskredit mit einem etwaigen Immobilien-Vermögenswert?

## Lebensphasen-Details

Sollen unfreiwillige, zufällige Phasenübergänge abgebildet werden (z. B. unerwarteter Jobverlust)? Welche weiteren Parameter außer den Notfallpuffer-Monaten sollten phasenspezifisch sein?

## Krankenversicherungsstatus (GKV vs. PKV)

Ist die Primärperson gesetzlich oder privat krankenversichert? Das betrifft KVdR-Beitrag vs. PKV-Prämie in der Rentenphase sowie die Nettogehalt-Annahme in der Erwerbsphase.

## Immobilie/Wohneigentum

Wird selbstgenutztes oder vermietetes Wohneigentum abgebildet – als Vermögenswert, als Mietkostenersparnis, als Anschaffung, als spätere Liquiditätsquelle?

## Weitere Altersvorsorge-Formen

Existieren bAV, Riester, Rürup oder private Rentenversicherungen mit eigener Besteuerungs-/Auszahlungslogik?

## Erbschaftssteuer für den Partner

Falls ein Vererbungsziel für die Partnerin gilt: Soll die Erbschaftssteuerlast (abhängig von Ehe vs. nichteheliche Lebensgemeinschaft) im Zielvermögen berücksichtigt werden?

## Besteuerung der Cash-Bucket-Zinsen

Zinserträge aus dem Cash-Bucket unterliegen ebenfalls der Abgeltungsteuer unter Nutzung des Sparerpauschbetrags – sollte im Jahresablauf explizit als eigener Fall ergänzt werden.

## Entnahme-Priorisierung zwischen Cash-Bucket und Portfolio

Wird zuerst der Cash-Bucket bis auf seine Zielgröße abgeschmolzen, oder proportional aus beiden entnommen?

## Ruin-Verhalten

Läuft eine Simulation nach Eintritt des Ruins mit Nullvermögen weiter, oder bricht der Lauf ab?

## Sondereinnahmen und -ausgaben

Sollen unregelmäßige Ereignisse wie Erbschaften, Boni oder unerwartete größere Ausgaben abgebildet werden?

## Wegfall des Partnerbeitrags (Trennung oder Tod)

Was passiert, wenn der Partnerbeitrag wegfällt? Einfachste Annahme: ab einem Jahr auf null. Realistischer: Hinterbliebenenrente bei Ehe/Lebenspartnerschaft.

## Ehe/Lebenspartnerschaft vs. nichteheliche Lebensgemeinschaft

Mehrere Annahmen (gemeinsamer Sparerpauschbetrag, Hinterbliebenenrente, gesetzliches Erbrecht) hängen am rechtlichen Status der Partnerschaft, der noch zu klären ist.

## Pflegekosten und Langlebigkeitsrisiko

Soll ein Tail-Risiko-Szenario für Pflegebedürftigkeit/altersgerechten Umbau abgebildet werden, oder reicht der altersabhängige Ausgabenfaktor als Näherung?

## Reale vs. nominale Größen

Sind alle Beträge konsequent nominal oder real zu verstehen? Muss projektweit einheitlich festgelegt werden.

## Quelle der Höhe der gesetzlichen Rente

Extern vorgegebener Wert (Renteninformation der Deutschen Rentenversicherung) oder eigene Nachbildung der Rentenformel (Entgeltpunkte × aktueller Rentenwert)?

## Wissensbasis für KI-gestützte Vorschläge

Woher stammen Referenzwerte zu typischen Nutzungsdauern/Kostenrahmen (Küche, Auto, Dach) für proaktive Vorschläge – LLM-Wissen, gepflegte Tabelle, oder Kombination?

## Renditeannahmen: parametrisch vs. Bootstrapping

Parametrische Verteilung je Anlageklasse oder historisches Bootstrapping (inkl. Fat-Tails und Autokorrelation)?
