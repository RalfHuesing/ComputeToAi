# Architektur & MCP-Server

Anders als eine reine, unverbindliche Frühphasen-Idee sind die folgenden Punkte bereits getroffene Grundsatzentscheidungen. Offene Detailfragen der konkreten Umsetzung stehen in 08-Offene-Fragen.md.

## Grundsatzentscheidungen

**Sprache: Python.** Begründung: hohe Trainingsbasis bei aktuellen LLMs (bessere „Vertrautheit" eines Agenten mit generiertem/gelesenem Code), ausgereiftes numerisches Ökosystem (NumPy/SciPy) für vektorisierte Monte-Carlo-Simulation, ein offizielles, first-tier MCP-Python-SDK, Pydantic für Schema-Definition und -Validierung.

**Kein eigenes Frontend.** Der MCP-Server bietet ausschließlich Werkzeuge (Tools) an; jede Interaktion läuft über einen bestehenden Agenten (Claude Code, Claude Cowork o. Ä.), jede Visualisierung entsteht auf Seiten des Agenten, nicht im Server.

**Lokale Datenhaltung.** Die Konfiguration eines Nutzers (Pläne, Speicher, aktivierte Bausteine, Parameterwerte) liegt in einer lokalen Datei (z. B. JSON) auf dem Rechner des Nutzers, nicht in einer zentralen Datenbank. Der MCP-Server liest und schreibt diese Datei; der Agent greift ausschließlich über die Tools darauf zu, nie direkt auf die Datei. Die Datei sollte von Beginn an eine Schema-Version mitführen, damit sich das Domänenmodell weiterentwickeln kann, ohne dass ältere Dateien von einer neueren Serverversion falsch interpretiert werden (Migrationsfrage siehe 08-Offene-Fragen.md).

## Modulare, hierarchische Tool-Struktur

Damit ein Agent nicht mit einer sehr großen Zahl flacher Funktionen überfordert wird, sind die MCP-Tools in Kategorien gegliedert, angelehnt an die Struktur dieses Konzepts:

- **Kern-Tools**: Plan anlegen/kopieren/löschen, Speicher/Effekt hinzufügen oder ändern, Simulation starten, Ergebnis abfragen.
- **Feature-Tools je aktiviertem Modul**: z. B. Finanzen-Tools (Haushalt/Person anlegen, Einkommensstrom hinzufügen, Baustein „Korrelierte Anlageklassen" aktivieren), Berechnungen-Tools (siehe 06-Feature-Berechnungen.md).
- **Verwaltungs-Tools**: Profile/Beispielvorlagen laden, Regelwerk-Templates einspielen, Schema-Selbstbeschreibung abfragen.

Die genaue Aufteilung/Benennung der Tool-Kategorien ist ein Implementierungsdetail (siehe 08-Offene-Fragen.md); die Anforderung „modular und hierarchisch, nicht flach" ist dagegen bereits Konzeptbestandteil (siehe 07-Anforderungen.md).

## Baustein-Katalog

Bausteine (siehe 01-Kern-Domaenenmodell.md) sind fertige, getestete Effekt-Vorlagen, die ein Agent auf Zuruf aktiviert und parametrisiert, statt die zugrunde liegende Mathematik selbst zu formulieren. Der Katalog ist erweiterbar (neue Bausteine lassen sich nachrüsten, ohne den Kern zu ändern), aber kuratiert – im Unterschied zu einem rohen, frei vom Agenten definierten Effekt reduziert ein Baustein das Risiko, dass mathematisch anspruchsvolle Logik (Korrelationen, Steuerformeln mit Deckelungen) fehlerhaft ad hoc erfunden wird. Wer einen Baustein pflegt, wie er versioniert wird und wie neue Bausteine aufgenommen werden, ist als offene Frage vermerkt.

## Regelwerk-Templates

Bausteine, die auf sich änderndem Recht beruhen (allen voran Steuerrecht), werden nicht im Code, sondern über versionierte, austauschbare Parameter-/Regelwerk-Pakete gepflegt (Beispiel: ein „Steuer-2027"-Template). Ein Nutzer kann ein solches Template laden (z. B. aus einem externen Repository) und einem Agenten übergeben, der es über ein Verwaltungs-Tool in einen bestehenden Plan einspielt. Wichtige Anforderungen an diesen Mechanismus:

- **Bestandsschutz-Fähigkeit**: Ein neues Regelwerk darf nicht automatisch rückwirkend auf bereits bestehende Speicher-Lots angewendet werden, wenn nach geltendem Recht Bestandsschutz gilt (Beispiel: Aktien, die vor Einführung der Abgeltungsteuer am 1.1.2009 gekauft wurden, bleiben dauerhaft nach altem Recht steuerfrei, siehe 03-Feature-Finanzen-Domaenenmodell.md). Ein Lot merkt sich deshalb, welche Regelwerk-Version bei seiner Entstehung galt.
- **Nachvollziehbarkeit vor Übernahme**: Ein Template sollte offenlegen, was sich gegenüber dem aktuellen Stand ändert, und im Idealfall eigene Testfälle mit erwartetem Ergebnis mitliefern, die der Agent vor dem Einspielen prüfen kann.
- **Quellentreue**: Wie im übrigen Konzept gilt: extern recherchierte Fakten (auch innerhalb eines Templates) werden mit Quelle/Stand/Abrufdatum vermerkt (siehe 09-Quellen.md und CLAUDE.md).

## Selbstbeschreibung

Der MCP-Server muss offenlegen können, welche Speicher-Typen, Effekte/Bausteine, Parameter und Tools in einem gegebenen Kontext existieren und welche Werte/Abhängigkeiten sie haben, damit ein Agent sinnvoll navigieren und den Nutzer gezielt befragen kann, ohne das fachliche Modell schon vorher zu kennen.

## Verifikation & Plausibilität – kein eigenes Feature

Die Prüfung, ob ein Simulationsergebnis plausibel ist (Beispiel: „3 Mio. Euro Endvermögen – kann das grob stimmen?"), ist bewusst **kein eigenständiges Server-Feature**. Der MCP-Server bietet lediglich granulare, komponierbare Tools an – insbesondere die Berechnungen-Tools (siehe 06-Feature-Berechnungen.md). Die Plausibilitätsprüfung selbst ist ein emergentes Verhalten des Agenten: Er kombiniert von sich aus mehrere einfache Berechnungen, um ein Simulationsergebnis grob gegenzuprüfen, und stellt das Ergebnis dem Nutzer nachvollziehbar dar (z. B. tabellarisch). Das folgt direkt aus der Grundaufteilung „Server rechnet deterministisch, Agent denkt und erklärt" (siehe 00-Vision.md) und ist keine zusätzliche Architekturkomponente.

## Beispielprofile

Der Server kann vorgefertigte Beispielprofile ausliefern (z. B. „25-jähriger Berufsanfänger.json"), die sinnvolle Default-Speicher, -Effekte und -Bausteine bereits aktiviert enthalten, um den Einstieg zu erleichtern und dem Agenten eine bewährte Ausgangskonfiguration zu geben, statt bei jedem neuen Plan komplett bei null zu beginnen.
