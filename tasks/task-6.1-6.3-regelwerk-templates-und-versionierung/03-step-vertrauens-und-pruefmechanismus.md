# Step 3: Vertrauens- & Prüfmechanismus (Diff-Vorschau & Checksum)

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-6.1-6.3-regelwerk-templates-und-versionierung/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Implementierung der Checksummen-Validierung und eines MCP-Tools `finance_diff_tax_templates(template_id_a, template_id_b)`, das alle Parameteränderungen gegeneinander vergleicht.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/features/finance/tax_templates.py`
- [ ] [MODIFY] `src/compute_to_ai/mcp/finance_tools.py`
- [ ] [MODIFY] `tests/test_features/test_finance/test_tax_templates.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# tax_templates.py

def diff_tax_templates(t1: TaxRulesTemplate, t2: TaxRulesTemplate) -> dict[str, Any]:
    """Returns a structured comparison of parameter changes between two tax templates."""
    ...
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_tax_templates.py -k test_diff_templates -v
```

### Abzudeckende Testfälle:
- Diff-Tool weist Parameterabweichungen (z. B. 801 € vs. 1.000 € Sparerpauschbetrag) korrekt aus.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/02-Architektur-und-MCP.md` aktualisieren.
