# Step 3: Golden-Tests für De-Risking & Sequence-of-Returns Absicherung

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.13-graduelle-kapitalsicherung-glidepath/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Erstellung von mathematisch nachgewiesenen Golden-Tests in `test_glidepath.py`, die belegen, dass die Glidepath-Umschichtung in Stressphasen (z. B. Markteinbruch exakt im Entnahmejahr) die Ruinwahrscheinlichkeit signifikant senkt.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `tests/test_features/test_finance/test_glidepath.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# Golden test comparing abrupt withdrawal vs glidepath withdrawal in a market crash scenario
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_glidepath.py -v
```

### Abzudeckende Testfälle:
- Nachweis des reduzierten Sequence-of-Returns-Risikos.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/04-Feature-Finanzen-Methodik.md` aktualisieren.
