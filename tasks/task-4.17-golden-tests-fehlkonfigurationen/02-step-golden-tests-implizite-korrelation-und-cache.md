# Step 2: Golden-Tests für implizite Korrelationen & Cache-Invalidierung

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.17-golden-tests-fehlkonfigurationen/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Erstellung von Golden-Tests für implizite Korrelationsannahmen (0.0 Warnung) sowie den Nachweis der strikten Cache-Invalidierung bei Plan-Mutationen.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `tests/test_features/test_finance/test_misconfiguration_golden.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# test_misconfiguration_golden.py

def test_implicit_correlation_warning_generated():
    ...

def test_cache_invalidated_on_mutation():
    ...
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_misconfiguration_golden.py -v
```

### Abzudeckende Testfälle:
- Korrelations-Warnung und Cache-Clearing verifiziert.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/04-Feature-Finanzen-Methodik.md` aktualisieren.
