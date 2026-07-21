# Step 3: MCP-Integration & Pre-Flight Warnungssystem

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.15-4.16-cache-invalidierung-und-pre-flight-audit/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Integration der Pre-Flight-Prüfungen in `finance_run_monte_carlo` und `core_run_simulation`. Rückgabe von `ruin_probability: null` bei fehlenden Ruin-Speichern.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/mcp/finance_tools.py`
- [ ] [MODIFY] `tests/test_mcp/test_finance_tools.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# mcp/finance_tools.py

# Insert preflight check into finance_run_monte_carlo:
# If ruin_stores is empty -> ruin_probability: null, add warning in response.
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_mcp/test_finance_tools.py -k test_preflight_mcp -v
```

### Abzudeckende Testfälle:
- MCP-Tool gibt strukturierte Warnungen und `ruin_probability: null` zurück, wenn `ruin_stores` fehlt.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/02-Architektur-und-MCP.md` aktualisieren.
