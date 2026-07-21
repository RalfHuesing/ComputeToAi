# Step 3: Alt-Stores- & Rebalancing-Cleanup

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.12-refactoring-und-audit-bereinigungen/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Entfernen von veralteten Rebalancing-Platzhalter-Effekten und Bereinigung unberührter Speicher.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `examples/ralf/plan.json`
- [ ] [MODIFY] `src/compute_to_ai/features/finance/portfolio.py`
- [ ] [MODIFY] `tests/test_features/test_finance/test_portfolio.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# Remove unreferenced placeholder stores and outdated rebalancing effects
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/ -v
```

### Abzudeckende Testfälle:
- Plan lässt sich fehlerfrei ausführen; `finance_audit_plan` meldet keine unberührten/verwaisten Speicher mehr.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/04-Feature-Finanzen-Methodik.md` aktualisieren.
