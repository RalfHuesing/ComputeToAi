# Review-Protokoll: Task 4.20 – Tool-Ergonomie & MCP-Vollständigkeits-Lücken

**Geprüft am**: 2026-07-21
**Review-Agent**: Claude Code (Fable 5)
**Gesamt-Ergebnis**: PASSED

---

## 1. Überprüfte Komponenten & Steps
- [x] Step 1 (`01-step-strukturierte-rueckgabewerte.md`): PASSED
- [x] Step 2 (`02-step-glidepath-parameter-und-fehlerbehandlung.md`): PASSED
- [x] Step 3 (`03-step-steps-per-year-nachtraeglich-aenderbar.md`): PASSED

---

## 2. Test-Ergebnisse (pytest)
```text
pytest tests/ -q
329 passed in 102.57s
```
- **Happy-Path-Coverage**: Bestätigt – strukturierte Echos aller umgestellten Tools werden per E2E gegen `core_list_effects` cross-gecheckt (`test_add_tools_echo_stored_values`, `test_core_add_effect_and_transfer_echo_stored_values`); `finance_add_fixed_acquisition` ohne Glidepath verhält sich unverändert; `finance_compare_plans`/`finance_compare_plan_actuals` mit fehlendem Vorergebnis liefern weiterhin ein Ergebnis statt eines Fehlers (Regressionstests).
- **Edge-Case-Coverage**: Bestätigt – `frequency="monthly"` auf einem Jahresschritt-Plan zeigt im Echo den gefalteten Jahresbetrag (12.000 statt 1.000); `finance_add_statutory_pension` mit vorgezogenem Rentenbeginn zeigt den reduzierten `annual_amount` samt `adjustment_factor`; Glidepath über die volle MCP-Schicht erzeugt einen `flexible_acquisition`-Computed-Effect (`test_finance_add_fixed_acquisition_supports_glidepath`); absichtlich beschädigte Ergebnis-Dateien propagieren jetzt als Tool-Fehler statt still `None` zu werden; `core_set_steps_per_year` lässt bestehende `amount_per_step`/`interval_steps` unangetastet und weist `steps_per_year=0` ab.

---

## 3. Code- & Living-Documentation-Check
- [x] Code entspricht den Standards in `.agents/rules/code-standards.mdc` (`ruff check`: All checks passed; `pyright`: 114 Fehler, identisch zur Baseline vor der Task – keine neuen Warnungen).
- [x] Keine Projektplanungs-Verweise im Code (`living-documentation.mdc`).
- [x] Doku in `Docs/` aktualisiert: `Docs/02-Architektur-und-MCP.md` (Baustein-Katalog: Rückgabewert-Konvention „strukturiertes Echo statt reinem Bestätigungs-String" als Prinzip festgehalten). Für Step 2 und Step 3 wie im jeweiligen Step vorgesehen keine weitere Doku-Änderung nötig – bestätigt: Glidepath und `Timeline.steps_per_year` sind fachlich bereits in `Docs/04`/`Docs/01` beschrieben, die Tools ändern kein Fachverhalten.
- [x] `Docs/10-Roadmap.md` aktualisiert (Epic 4.20 abgehakt).

---

## 4. Anmerkungen & Befunde des Review-Agenten
- **Abweichung mit Begründung (Befund 3)**: Das Konzept schlug `except ValueError` vor. Pydantics `ValidationError` ist jedoch selbst eine `ValueError`-Subklasse – ein bloßes `except ValueError` hätte beschädigte/schema-inkompatible Ergebnis-Dateien weiterhin verschluckt und damit genau den Edge Case verfehlt, den die Task fordert. Stattdessen wirft `load_result` (`plan_storage.py`) jetzt eine dedizierte `ResultNotFoundError(ValueError)` bei fehlender Datei, und nur diese wird in `finance_compare_plans`/`finance_compare_plan_actuals` gefangen. Das entspricht der im Step ausdrücklich vorgesehenen Klausel, „die dann tatsächlich passende(n) Exception-Typ(en)" zu verwenden; bestehende Aufrufer, die `ValueError` erwarten, bleiben kompatibel.
- **Entscheidung Befund 4**: Eigenes Kern-Tool `core_set_steps_per_year` (statt Erweiterung eines bestehenden Tools), platziert direkt neben `core_create_plan` in `_register_plan_lifecycle_tools` – Timeline ist Kern-Konzept, kein Finance-Spezifikum. Der Warnhinweis (keine rückwirkende Umrechnung bestehender Effekte) steht im Tool-Docstring selbst und damit im MCP-Schema.
- Die strukturierten Echos geben bewusst kein volles `model_dump()` zurück, sondern je Tool die tatsächlich berechneten/umgerechneten Werte (gefalteter `amount_per_step`, Rentenbetrag nach Abschlag inkl. `adjustment_factor`, normalisierter Transferbetrag, Cash-Bucket-Parameter inkl. gefüllter Defaults, Effekt-Namen bei Mehr-Effekt-Bausteinen wie Verbindlichkeit/Steuer-Manager).
- Die `pyright`-Fehlerzahl (114) besteht vollständig aus vorbestehenden Befunden (Baseline-Vergleich, siehe Task 4.19); die Task hat keine neuen hinzugefügt.
- Freigabevermerk: DoD vollständig erfüllt, Gesamt-Ergebnis PASSED.
