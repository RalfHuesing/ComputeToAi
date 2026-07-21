# Step 3: MCP-Tools für Parameter-Pflege

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.14-zentrale-parameter-registry/00-konzept.md)  
**Status**: DONE  

---

## 1. Step-Intention
Implementierung der MCP-Tools `finance_set_plan_parameter` und `finance_get_plan_parameters` zur zentralen Anzeige und Pflege von Makro-Parametern auf Plan-Ebene.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/mcp/finance_tools.py`
- [ ] [NEW] `tests/test_mcp/test_parameter_tools.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# mcp/finance_tools.py

def finance_set_plan_parameter(plan_name: str, key: str, value: float) -> str:
    """Sets a central plan parameter (e.g. inflation_general = 0.025)."""
    ...

def finance_get_plan_parameters(plan_name: str) -> dict[str, float]:
    """Returns all registered central plan parameters."""
    ...
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_mcp/test_parameter_tools.py -v
```

### Abzudeckende Testfälle:
- MCP-Tools setzen und lesen Parameter fehlerfrei.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/02-Architektur-und-MCP.md` aktualisieren.
