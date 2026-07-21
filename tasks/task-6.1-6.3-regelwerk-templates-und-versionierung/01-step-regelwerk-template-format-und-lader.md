# Step 1: Regelwerk-Template-Format & Ladeprozess

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-6.1-6.3-regelwerk-templates-und-versionierung/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Implementierung des `TaxRulesTemplate`-Modells und des Lade-Mechanismus aus JSON-Dateien unter `src/compute_to_ai/features/finance/tax_templates.py`.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [NEW] `src/compute_to_ai/features/finance/tax_templates.py`
- [ ] [NEW] `src/compute_to_ai/features/finance/templates/de_tax_2024.json`
- [ ] [NEW] `tests/test_features/test_finance/test_tax_templates.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# tax_templates.py

class TaxRulesTemplate(BaseModel):
    template_id: str
    valid_from_year: int
    savers_allowance: float
    capital_gains_tax_rate: float = 0.25
    soli_rate: float = 0.055
    partial_exemptions: dict[str, float]
    checksum: str
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_tax_templates.py -v
```

### Abzudeckende Testfälle:
- Laden von vordefinierten Steuer-Templates (`de_tax_2024.json`).

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/05-Feature-Finanzen-Parameter.md` aktualisieren.
