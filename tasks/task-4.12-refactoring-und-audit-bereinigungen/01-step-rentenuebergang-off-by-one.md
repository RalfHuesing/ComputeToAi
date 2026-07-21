# Step 1: Bereinigung Off-By-One beim Rentenübergang

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.12-refactoring-und-audit-bereinigungen/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Exakte Abgrenzung der Phasengrenze zwischen Erwerbsphase und Rentenphase. Das Erwerbseinkommen endet in Step `N - 1`, die Rentenzahlung beginnt in Step `N`.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/features/finance/life_phases.py`
- [ ] [MODIFY] `examples/anna/plan.json`
- [ ] [MODIFY] `tests/test_features/test_finance/test_path_audit.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# life_phases.py
# Adjust active_phases and end_step so that:
# employment_phase.end_step = retirement_step - 1
# pension_phase.start_step = retirement_step
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_path_audit.py -k test_audit_plan -v
```

### Abzudeckende Testfälle:
- `finance_audit_plan` liefert keine Warnung bezüglich überschneidender Einnahmen-Kategorien im Übergangsschritt.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/04-Feature-Finanzen-Methodik.md` (Abschnitt Phasenübergänge) aktualisieren.
