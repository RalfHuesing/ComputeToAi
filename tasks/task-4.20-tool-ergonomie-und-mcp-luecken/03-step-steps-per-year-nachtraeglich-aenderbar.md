# Step 3: `steps_per_year` nachträglich änderbar machen

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.20-tool-ergonomie-und-mcp-luecken/00-konzept.md)
**Status**: PENDING

---

## 1. Step-Intention

Neues Kern-Tool `core_set_steps_per_year`, damit ein bereits angelegter Plan mit falschem/fehlendem `Timeline.steps_per_year` über MCP korrigiert werden kann, statt (wie zuletzt bei Plan `ralf` nötig) die JSON-Datei direkt anzufassen.

---

## 2. Zu bearbeitende / neu anzulegende Dateien

- [ ] [MODIFY] `src/compute_to_ai/mcp/tools/core_tools.py` – neues Tool `core_set_steps_per_year`.
- [ ] [NEW/MODIFY] Test in `tests/test_mcp/test_server_e2e.py`.

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

Siehe `00-konzept.md`, Abschnitt 3, für die vollständige Tool-Skizze inklusive Warnhinweis im Docstring. Platzierung in `core_tools.py`: direkt neben `core_create_plan` in `_register_plan_lifecycle_tools`, da es dieselbe Timeline-Eigenschaft betrifft.

### Spezifische Hinweise:
- Beachte `.agents/rules/code-standards.mdc` und `.agents/rules/language.mdc`.
- `steps_per_year` muss weiterhin `> 0` sein (Pydantic-Validierung auf `Timeline` greift bereits beim Speichern/Laden – kein zusätzlicher manueller Check nötig, aber der Fehlerfall sollte eine verständliche `ValueError`-Meldung statt eines rohen Pydantic-`ValidationError` erzeugen, falls das UX-relevant ist).

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_mcp/test_server_e2e.py -v
```

### Abzudeckende Testfälle:
- **Happy Path**: `core_create_plan` mit Default `steps_per_year=12`, danach `core_set_steps_per_year(plan_name, steps_per_year=1)` → `core_get_result`/erneutes Laden des Plans zeigt `timeline.steps_per_year == 1`.
- **Edge Cases**:
  - Bereits vorhandene Effekte (z. B. über `finance_add_income_stream` mit `frequency="yearly"` unter dem alten `steps_per_year` angelegt) behalten ihren gespeicherten `amount_per_step`/`interval_steps` unverändert bei – `core_set_steps_per_year` rechnet nichts nachträglich um (explizit testen, da das leicht falsch angenommen werden könnte).
  - `steps_per_year=0` oder negativ → Fehler statt eines ungültig gespeicherten Plans.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] Keine Doku-Änderung über die bereits in Task 4.19 vorgenommene `Timeline.steps_per_year`-Beschreibung hinaus erwartet – im Review kurz bestätigen.
- [ ] `Docs/10-Roadmap.md`: Epic 4.20 abhaken, sobald Review „PASSED".
