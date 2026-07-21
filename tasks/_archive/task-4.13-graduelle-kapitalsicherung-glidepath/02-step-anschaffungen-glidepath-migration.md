# Step 2: Anschaffungen Glidepath-Migration

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.13-graduelle-kapitalsicherung-glidepath/00-konzept.md)  
**Status**: DONE  

---

## 1. Step-Intention
Vereinheitlichung von `fixed_acquisition` und `flexible_acquisition` in `cashflow.py`, sodass auch fixe Großanschaffungen standardmäßig von der linearen Umschichtung (`glidepath_start_step`) aus Aktien in Cash profitieren.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/features/finance/cashflow.py`
- [ ] [MODIFY] `tests/test_features/test_finance/test_cashflow.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# cashflow.py
def add_fixed_acquisition(
    ...,
    glidepath_years: float = 0.0
) -> None:
    ...
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_cashflow.py -k test_acquisition_glidepath -v
```

### Abzudeckende Testfälle:
- Anschaffung in 5 Jahren schichtet 3 Jahre vor Fälligkeit kontinuierlich monatlich Kapital um.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/04-Feature-Finanzen-Methodik.md` aktualisieren.
