# Step 2: Finance-Bausteine für Frequenzen & Turnusausgaben

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.11-frequenz-und-intervall-ausgaben/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Erweiterung der Finanz-Cashflow-Bausteine (`add_expense`, `add_income_stream`) in `src/compute_to_ai/features/finance/cashflow.py` um den Parameter `frequency` (`"monthly"`, `"quarterly"`, `"yearly"`, `"every_n_years"`) und korrekte Umrechnung/Anbindung an Inflationspfade.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/features/finance/cashflow.py`
- [ ] [NEW] `tests/test_features/test_finance/test_frequency_effects.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# src/compute_to_ai/features/finance/cashflow.py

FREQUENCY_MAP = {
    "monthly": 1,
    "quarterly": 3,
    "yearly": 12,
    "annual": 12,
}

def add_expense(
    plan: Plan,
    name: str,
    amount: float,
    frequency: str = "monthly",
    interval_years: int | None = None,
    first_occurrence_year: float | None = None,
    ...
) -> GrowingFixedEffect:
    ...
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_frequency_effects.py -v
```

### Abzudeckende Testfälle:
- **Happy Path**: Jährliche KFZ-Versicherung verringert den Cash-Bucket nur alle 12 Monate.
- **Edge Cases**:
  - `frequency="every_n_years"`, `interval_years=5`: Auto-Kauf alle 5 Jahre (Schritte 0, 60, 120).
  - Korrekte Zinseszins-Wachstumsberechnung `(1 + rate)^step` für mehrjährige Intervalle.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/04-Feature-Finanzen-Methodik.md` (Abschnitt Periodische Cashflows) aktualisieren.
