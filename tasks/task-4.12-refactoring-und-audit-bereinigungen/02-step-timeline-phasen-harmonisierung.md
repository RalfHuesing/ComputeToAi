# Step 2: Timeline- & Phasen-Harmonisierung

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.12-refactoring-und-audit-bereinigungen/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Harmonisierung von Timeline-Ende und Rentenphasen-Ende, sodass die letzte Phase (`pension_phase`) immer bis `step_count - 1` der Timeline reicht. Dies verhindert das Absinken des Cash-Bucket Notgroschens auf 0 € am Ende des Simulationshorizonts.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/features/finance/life_phases.py`
- [ ] [MODIFY] `src/compute_to_ai/features/finance/portfolio.py`
- [ ] [NEW] `tests/test_features/test_finance/test_life_phases_harmonies.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# life_phases.py
# Set final_phase.end_step = timeline.step_count - 1
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_life_phases_harmonies.py -v
```

### Abzudeckende Testfälle:
- Cash-Bucket behält sein Entnahmeziel bis zum allerletzten Zeitschritt der Timeline.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/04-Feature-Finanzen-Methodik.md` aktualisieren.
