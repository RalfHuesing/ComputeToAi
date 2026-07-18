# Architektur & MCP-Server

Anders als eine reine, unverbindliche Frühphasen-Idee sind die folgenden Punkte bereits getroffene Grundsatzentscheidungen. Offene Detailfragen der konkreten Umsetzung stehen in 08-Offene-Fragen.md.

## Grundsatzentscheidungen

**Sprache: Python.** Begründung: hohe Trainingsbasis bei aktuellen LLMs (bessere „Vertrautheit" eines Agenten mit generiertem/gelesenem Code), ausgereiftes numerisches Ökosystem (NumPy/SciPy) für vektorisierte Monte-Carlo-Simulation, ein offizielles, first-tier MCP-Python-SDK, Pydantic für Schema-Definition und -Validierung.

**Kein eigenes Frontend.** Der MCP-Server bietet ausschließlich Werkzeuge (Tools) an; jede Interaktion läuft über einen bestehenden Agenten (Claude Code, Claude Cowork o. Ä.), jede Visualisierung entsteht auf Seiten des Agenten, nicht im Server.

**Transport: stdio.** Der MCP-Server läuft als stdio-Server (Standard-Transport des MCP-Python-SDK): Der Agent startet ihn als Kindprozess und kommuniziert über stdin/stdout, kein Netzwerkport, keine Authentifizierung nötig. Das passt zur lokalen Einzelnutzer-Ausrichtung. Ein zusätzlicher Transport (z. B. HTTP/SSE) für entfernten Zugriff ließe sich später ergänzen, ohne stdio zu verlieren; das ist aktuell nicht geplant.

**Settings-Datei.** Grundlegende, selten geänderte Einstellungen – vor allem der Pfad zum Arbeitsverzeichnis (siehe unten) und das Logging-Level – stehen in einer Settings-Datei im TOML-Format (kommentierbar, von Hand editierbar, bevor überhaupt ein Agent involviert ist). Der Server sucht sie standardmäßig an einem plattformüblichen Konfigurationspfad; der Pfad lässt sich beim Serverstart per Umgebungsvariable oder Kommandozeilenargument überschreiben, so wie MCP-Server üblicherweise über die `mcpServers`-Konfiguration des jeweiligen Agent-Tools mit Argumenten/Umgebungsvariablen gestartet werden. Eine generische Beispiel-Settings-Datei liegt unter `examples/`.

**Arbeitsverzeichnis mit mehreren Plänen.** Die Settings-Datei verweist auf ein Arbeitsverzeichnis, das die Wurzel für **mehrere** Pläne ist – ein Unterordner je Plan (z. B. `renten-plan/`, `renten-plan-fruehrente/`), passend zum „Was-wäre-wenn"-Anspruch aus 00-Vision.md (kopierbare Pläne, die sich vergleichen lassen, ohne die Settings-Datei zu ändern). Jeder Plan-Ordner enthält alle für diesen Plan entstehenden Dateien, mindestens eine lokale JSON-Konfigurationsdatei (Speicher, aktivierte Bausteine, Parameterwerte) statt einer zentralen Datenbank. Der MCP-Server liest und schreibt diese Dateien; der Agent greift ausschließlich über die Tools darauf zu, nie direkt. Die JSON-Konfigurationsdatei führt von Beginn an eine Schema-Version mit, damit sich das Domänenmodell weiterentwickeln kann, ohne dass ältere Dateien von einer neueren Serverversion falsch interpretiert werden (Migrationsfrage siehe 08-Offene-Fragen.md). Ein generisches Beispiel-Arbeitsverzeichnis liegt unter `examples/` im Repo.

**Logging.** Der Server loggt grundsätzlich alles, aber gestuft: Auf INFO-Level werden operative Abläufe protokolliert (welches Tool wann mit welchem Ergebnis-Status aufgerufen wurde) ohne konkrete Finanzwerte; auf DEBUG-Level (nicht standardmäßig aktiv) zusätzlich vollständige Tool-Parameter und -Ergebnisse inklusive Zahlen, für gezieltes Debugging bei Bedarf einschaltbar. Log-Dateien landen in `<Arbeitsverzeichnis>/logs/`, nicht im System- oder Nutzer-Root. Kann der Server das Arbeitsverzeichnis beim Start noch nicht ermitteln (z. B. bevor die Settings-Datei gelesen ist), dient ein plattformüblicher Anwendungs-Log-Pfad als Fallback. Umsetzung über die Python-Standardbibliothek `logging` mit rotierenden Dateien, kein Zusatzpaket nötig.

## Modulare, hierarchische Tool-Struktur

Damit ein Agent nicht mit einer sehr großen Zahl flacher Funktionen überfordert wird, sind die MCP-Tools in Kategorien gegliedert, angelehnt an die Struktur dieses Konzepts:

- **Kern-Tools**: Plan anlegen/kopieren/löschen, Speicher/Effekt hinzufügen oder ändern, Simulation starten, Ergebnis abfragen.
- **Feature-Tools je aktiviertem Modul**: z. B. Finanzen-Tools (Haushalt/Person anlegen, Einkommensstrom hinzufügen, Baustein „Korrelierte Anlageklassen" aktivieren), Berechnungen-Tools (siehe 06-Feature-Berechnungen.md).
- **Verwaltungs-Tools**: Profile/Beispielvorlagen laden, Regelwerk-Templates einspielen, Schema-Selbstbeschreibung abfragen.

Die genaue Aufteilung/Benennung der Tool-Kategorien ist ein Implementierungsdetail (siehe 08-Offene-Fragen.md); die Anforderung „modular und hierarchisch, nicht flach" ist dagegen bereits Konzeptbestandteil (siehe 07-Anforderungen.md).

Da das MCP-Protokoll selbst keine verschachtelten Namensräume für Tools kennt (ein Server bietet eine flache Liste benannter Tools an), wird die Hierarchie über eine Namenskonvention abgebildet: Jeder Tool-Name trägt die Kategorie als Präfix, getrennt durch `_` (z. B. `core_create_plan` für ein Kern-Tool). Feature-Tools tragen entsprechend den Namen ihres Feature-Moduls als Präfix (z. B. `finance_add_income_stream`), Berechnungen-Tools das Präfix `calculations_`.

## Baustein-Katalog

Bausteine (siehe 01-Kern-Domaenenmodell.md) sind fertige, getestete Effekt-Vorlagen, die ein Agent auf Zuruf aktiviert und parametrisiert, statt die zugrunde liegende Mathematik selbst zu formulieren. Der Katalog ist erweiterbar (neue Bausteine lassen sich nachrüsten, ohne den Kern zu ändern), aber kuratiert – im Unterschied zu einem rohen, frei vom Agenten definierten Effekt reduziert ein Baustein das Risiko, dass mathematisch anspruchsvolle Logik (Korrelationen, Steuerformeln mit Deckelungen) fehlerhaft ad hoc erfunden wird. Wer einen Baustein pflegt, wie er versioniert wird und wie neue Bausteine aufgenommen werden, ist als offene Frage vermerkt.

## Regelwerk-Templates

Bausteine, die auf sich änderndem Recht beruhen (allen voran Steuerrecht), werden nicht im Code, sondern über versionierte, austauschbare Parameter-/Regelwerk-Pakete gepflegt (Beispiel: ein „Steuer-2027"-Template). Ein Nutzer kann ein solches Template laden (z. B. aus einem externen Repository) und einem Agenten übergeben, der es über ein Verwaltungs-Tool in einen bestehenden Plan einspielt. Wichtige Anforderungen an diesen Mechanismus:

- **Bestandsschutz-Fähigkeit**: Ein neues Regelwerk darf nicht automatisch rückwirkend auf bereits bestehende Speicher-Lots angewendet werden, wenn nach geltendem Recht Bestandsschutz gilt (Beispiel: Aktien, die vor Einführung der Abgeltungsteuer am 1.1.2009 gekauft wurden, bleiben dauerhaft nach altem Recht steuerfrei, siehe 03-Feature-Finanzen-Domaenenmodell.md). Ein Lot merkt sich deshalb, welche Regelwerk-Version bei seiner Entstehung galt.
- **Nachvollziehbarkeit vor Übernahme**: Ein Template sollte offenlegen, was sich gegenüber dem aktuellen Stand ändert, und im Idealfall eigene Testfälle mit erwartetem Ergebnis mitliefern, die der Agent vor dem Einspielen prüfen kann.
- **Quellentreue**: Wie im übrigen Konzept gilt: extern recherchierte Fakten (auch innerhalb eines Templates) werden mit Quelle/Stand/Abrufdatum vermerkt (siehe 09-Quellen.md und CLAUDE.md).

## Selbstbeschreibung

Der MCP-Server muss offenlegen können, welche Speicher-Typen, Effekte/Bausteine, Parameter und Tools in einem gegebenen Kontext existieren und welche Werte/Abhängigkeiten sie haben, damit ein Agent sinnvoll navigieren und den Nutzer gezielt befragen kann, ohne das fachliche Modell schon vorher zu kennen. Technisch stützt sich das auf zwei MCP-Bausteine: Jedes Tool und jeder Parameter beschreibt sich über sein Pydantic-Schema selbst (Docstrings/Feldbeschreibungen werden direkt Teil der MCP-Tool-Definition, kein separates Beschreibungsformat). Zusätzlich stellt der Server die vollständige Konzeptdokumentation aus `Docs/` als MCP-Resources bereit, sodass der Agent bei Bedarf denselben Text lesen kann wie ein Mensch – es gibt also nur eine Dokumentation, nicht eine für Menschen und eine separat gepflegte zweite für den Agenten.

## Verifikation & Plausibilität – kein eigenes Feature

Die Prüfung, ob ein Simulationsergebnis plausibel ist (Beispiel: „3 Mio. Euro Endvermögen – kann das grob stimmen?"), ist bewusst **kein eigenständiges Server-Feature**. Der MCP-Server bietet lediglich granulare, komponierbare Tools an – insbesondere die Berechnungen-Tools (siehe 06-Feature-Berechnungen.md). Die Plausibilitätsprüfung selbst ist ein emergentes Verhalten des Agenten: Er kombiniert von sich aus mehrere einfache Berechnungen, um ein Simulationsergebnis grob gegenzuprüfen, und stellt das Ergebnis dem Nutzer nachvollziehbar dar (z. B. tabellarisch). Das folgt direkt aus der Grundaufteilung „Server rechnet deterministisch, Agent denkt und erklärt" (siehe 00-Vision.md) und ist keine zusätzliche Architekturkomponente.

## Beispielprofile

Der Server kann vorgefertigte Beispielprofile ausliefern (z. B. „25-jähriger Berufsanfänger.json"), die sinnvolle Default-Speicher, -Effekte und -Bausteine bereits aktiviert enthalten, um den Einstieg zu erleichtern und dem Agenten eine bewährte Ausgangskonfiguration zu geben, statt bei jedem neuen Plan komplett bei null zu beginnen. Ein generisches Beispiel-Arbeitsverzeichnis mit anonymisierter statt persönlicher Benennung liegt bereits als Repo-Vorlage unter `examples/`.
