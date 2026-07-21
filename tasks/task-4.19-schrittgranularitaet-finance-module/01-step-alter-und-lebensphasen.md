# Step 1: Alter/Schritt-Umrechnung und Lebensphasen-Aufbau

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.19-schrittgranularitaet-finance-module/00-konzept.md)
**Status**: PENDING

---

## 1. Step-Intention

`step_to_age`/`age_to_step` (zustandslose Berechnungen-Tools) und `build_standard_life_phases` (Lebensphasen-Aufbau) erhalten einen expliziten `steps_per_year`-Parameter statt hartkodiertem "1 Step = 1 Jahr". `finance_set_life_phases` liest dafür `plan.timeline.steps_per_year` und reicht ihn durch.

---

## 2. Zu bearbeitende / neu anzulegende Dateien

- [ ] [MODIFY] `src/compute_to_ai/features/calculations/dates.py`
- [ ] [MODIFY] `src/compute_to_ai/features/finance/phases.py`
- [ ] [MODIFY] `src/compute_to_ai/mcp/tools/finance/_phase.py`
- [ ] [MODIFY] Tests für `dates.py` und `phases.py` (Testmodule anhand bestehender Struktur finden, z. B. `tests/test_features/test_calculations/test_dates.py`)

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

Siehe `00-konzept.md`, Abschnitt 3, für `step_to_age`/`age_to_step`/`build_standard_life_phases`. `finance_set_life_phases` (`_phase.py`) muss den Plan **vor** dem Aufruf von `build_standard_life_phases` laden (ist heute schon der Fall) und `steps_per_year=plan.timeline.steps_per_year` übergeben:

```python
plan = load_plan(working_directory, plan_name)
plan.phases = build_standard_life_phases(
    current_age=current_age,
    employment_end_age=employment_end_age,
    statutory_pension_start_age=statutory_pension_start_age,
    life_expectancy_age=life_expectancy_age,
    education_end_age=education_end_age,
    steps_per_year=plan.timeline.steps_per_year,
)
```

`life_expectancy_step`/`pension_start_step`/`education_end_step` in `build_standard_life_phases` folgen demselben Muster wie `employment_end_step` (Altersdifferenz × `steps_per_year`) – konsistent auf alle vier Schrittberechnungen anwenden, nicht nur auf eine.

### Spezifische Hinweise:
- Beachte `.agents/rules/code-standards.mdc` und `.agents/rules/language.mdc`.
- `step_to_age` gibt jetzt ggf. einen nicht-ganzzahligen Wert zurück (`float` statt `int`), wenn `step` kein Vielfaches von `steps_per_year` ist – Rückgabetyp entsprechend anpassen und im Docstring erwähnen.

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_calculations/ tests/test_features/test_finance/ tests/test_mcp/test_finance_tools_e2e.py -v
```

### Abzudeckende Testfälle:
- **Happy Path**: `steps_per_year=1` (Default) liefert identische Ergebnisse wie vor der Änderung.
- **Edge Cases**:
  - `step_to_age(step=12, current_age=30, steps_per_year=12)` → `31.0`.
  - `age_to_step(age=31, current_age=30, steps_per_year=12)` → `12`.
  - `build_standard_life_phases(..., steps_per_year=12)` erzeugt Phasengrenzen in Monatsschritten, nicht in Jahresschritten.
  - `finance_set_life_phases` auf einem Plan mit `steps_per_year=12` (über `core_create_plan(..., steps_per_year=12)` angelegt) erzeugt dieselben, jetzt korrekt skalierten Phasengrenzen über den vollen MCP-Aufruf.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/05-Feature-Finanzen-Parameter.md` (Lebensphasen-Abschnitt) um den Hinweis ergänzen, dass die Schrittgrenzen relativ zu `Timeline.steps_per_year` berechnet werden.
