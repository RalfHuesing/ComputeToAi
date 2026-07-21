# Step 1: Golden-Tests für fehlende Ruin-Speicher & unvollständige Pläne

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.17-golden-tests-fehlkonfigurationen/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Erstellung von Golden-Tests, die nachweisen, dass unkonfigurierte Ruin-Speicher oder fehlende Zielbedingungen NIEMALS zu einer irreführenden `0.0 %` Ruinwahrscheinlichkeit führen, sondern zu `ruin_probability: null` und `CRITICAL_CONFIG_MISSING`.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [NEW] `tests/test_features/test_finance/test_misconfiguration_golden.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# test_misconfiguration_golden.py

def test_unconfigured_ruin_stores_returns_null_probability():
    ...
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_misconfiguration_golden.py -v
```

### Abzudeckende Testfälle:
- Nachweis der korrekten Signalisierung bei fehlenden Ruin-Speichern.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/04-Feature-Finanzen-Methodik.md` aktualisieren.
