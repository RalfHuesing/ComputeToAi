# Step 1: Cash-Bucket Glidepath vor Phasenwechseln

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.13-graduelle-kapitalsicherung-glidepath/00-konzept.md)  
**Status**: DONE  

---

## 1. Step-Intention
Erweiterung von `CashBucketParameters` und `cash_bucket_manager_func` in `portfolio.py` um eine lineare De-Risking-Rampe (`glidepath_steps`) vor Phasenübergängen (z.B. Erwerbsphase → Rentenphase).

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/features/finance/portfolio.py`
- [ ] [NEW] `tests/test_features/test_finance/test_glidepath.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# portfolio.py

class CashBucketParameters:
    emergency_buffer_months: float
    withdrawal_buffer_years: float = 0.0
    glidepath_steps: int = 0  # 0 = deaktiviert / sprungsprung
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_glidepath.py -k test_cash_bucket_glidepath -v
```

### Abzudeckende Testfälle:
- Zielgröße des Cash-Buckets steigt über 36 Schritte linear an.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/04-Feature-Finanzen-Methodik.md` (Abschnitt Cash-Bucket De-Risking) aktualisieren.
