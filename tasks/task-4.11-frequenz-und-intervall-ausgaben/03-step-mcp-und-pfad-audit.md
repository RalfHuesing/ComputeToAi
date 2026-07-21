# Step 3: MCP-Tools & Pfad-Audit für Intervall-Ausgaben

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.11-frequenz-und-intervall-ausgaben/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Erweiterung der MCP-Tools (`finance_add_expense`, `finance_add_income_stream`) in `src/compute_to_ai/mcp/finance_tools.py` um Frequenzparameter sowie Anpassung des Pfad-Audits zur korrekten Klassifikation turnusmäßiger Cashflows.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/mcp/finance_tools.py`
- [ ] [MODIFY] `src/compute_to_ai/features/finance/path_audit.py`
- [ ] [MODIFY] `tests/test_mcp/test_finance_tools.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# mcp/finance_tools.py

def finance_add_expense(
    plan_name: str,
    name: str,
    amount: float,
    frequency: str = "monthly",
    interval_years: int | None = None,
    ...
) -> str:
    ...
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_mcp/test_finance_tools.py -k test_add_expense_frequency -v
```

### Abzudeckende Testfälle:
- MCP-Tool akzeptiert `"yearly"` und `"every_n_years"`.
- Pfad-Audit verarbeitet Schritte ohne Cashflows fehlerfrei und erfasst die Turnus-Events ordnungsgemäß.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] MCP-Tool-Dokumentation in `Docs/02-Architektur-und-MCP.md` nachziehen.
