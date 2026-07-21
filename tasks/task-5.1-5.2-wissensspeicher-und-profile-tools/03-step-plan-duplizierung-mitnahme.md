# Step 3: Automatisches Mitkopieren bei Plan-Duplizierung

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-5.1-5.2-wissensspeicher-und-profile-tools/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Erweiterung der Plan-Kopierlogik (`core_duplicate_plan` in `src/compute_to_ai/mcp/core_tools.py`), sodass beim Erstellen einer Was-wäre-wenn-Kopie die Datei `knowledge.json` (falls vorhanden) automatisch mit in den neuen Plan-Ordner kopiert wird.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/mcp/core_tools.py`
- [ ] [MODIFY] `tests/test_mcp/test_core_tools.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# core_tools.py

# In core_duplicate_plan:
# Check if source_plan_dir / "knowledge.json" exists
# If yes -> shutil.copy2(source_plan_dir / "knowledge.json", target_plan_dir / "knowledge.json")
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_mcp/test_core_tools.py -k test_duplicate_plan_with_knowledge -v
```

### Abzudeckende Testfälle:
- Nach duplizieren eines Plans steht derselbe Wissensspeicher unter dem neuen Plan-Namen zur Verfügung.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/02-Architektur-und-MCP.md` aktualisieren.
