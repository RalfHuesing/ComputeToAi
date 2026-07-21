# Step 2: Pre-Flight Konfigurations-Audit

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.15-4.16-cache-invalidierung-und-pre-flight-audit/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Implementierung von `preflight.py` zur Erkennung unvollständiger oder fehlerhafter Plan-Konfigurationen vor der Ausführung.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [NEW] `src/compute_to_ai/features/finance/preflight.py`
- [ ] [NEW] `tests/test_features/test_finance/test_preflight_audit.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# preflight.py

def run_preflight_audit(plan: Plan) -> list[PreflightIssue]:
    issues = []
    # 1. Check ruin_stores
    if not plan.ruin_stores:
        issues.append(PreflightIssue(
            severity=Severity.CRITICAL_CONFIG_MISSING,
            code="NO_RUIN_STORES",
            message="No ruin_stores configured for plan."
        ))
    # 2. Check correlation matrix for stochastic return effects
    # 3. Check cash bucket presence for withdrawal plans
    return issues
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_preflight_audit.py -v
```

### Abzudeckende Testfälle:
- Erfasst fehlende `ruin_stores`, implizite 0.0 Korrelationen und fehlende Notgroschen.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/04-Feature-Finanzen-Methodik.md` aktualisieren.
