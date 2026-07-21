# Step 2: Bestandsschutz-Konsistenz bei Regelwerk-Wechsel

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-6.1-6.3-regelwerk-templates-und-versionierung/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Absicherung, dass beim Wechsel der aktiven Steuer-Template-Version eines Plans bereits existierende Lots ihre spezifische Regelwerksversion (`rule_version`) und deren Bestandsschutzrechte behalten.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/features/finance/tax.py`
- [ ] [MODIFY] `tests/test_features/test_finance/test_tax_templates.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# tax.py
# Ensure Lot.rule_version overrides plan-level template defaults for historical lots
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_tax_templates.py -k test_grandfathering_on_template_switch -v
```

### Abzudeckende Testfälle:
- Nach Wechsel von 2023 auf 2024 Regelwerk behalten Vor-2009-Lots und 2023er-Lots ihre historischen Freibeträge.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/03-Feature-Finanzen-Domaenenmodell.md` aktualisieren.
