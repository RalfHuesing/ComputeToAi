# Step 2: MCP-Tools für Bulk-Read Dump & CRUD-Operationen

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-5.1-5.2-wissensspeicher-und-profile-tools/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Implementierung der MCP-Tools `profile_get_all_facts`, `profile_set_fact`, `profile_remove_fact` in `src/compute_to_ai/mcp/finance_tools.py`.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/mcp/finance_tools.py`
- [ ] [NEW] `tests/test_mcp/test_profile_tools.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# mcp/finance_tools.py

def profile_get_all_facts(plan_name: str, category: str | None = None) -> dict[str, Any]:
    """Returns a full bulk-read dump of all facts in the plan's knowledge store."""
    ...

def profile_set_fact(
    plan_name: str,
    key: str,
    value: Any,
    category: str = "general",
    description: str | None = None,
    source: str = "user_explicit"
) -> str:
    """Creates or updates a fact in the knowledge store."""
    ...

def profile_remove_fact(plan_name: str, key: str) -> str:
    """Removes a fact by key."""
    ...
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_mcp/test_profile_tools.py -v
```

### Abzudeckende Testfälle:
- Bulk-Read Dump liefert sauberes Kontext-Objekt.
- CRUD-Operationen verarbeiten Daten fehlerfrei.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/02-Architektur-und-MCP.md` aktualisieren.
