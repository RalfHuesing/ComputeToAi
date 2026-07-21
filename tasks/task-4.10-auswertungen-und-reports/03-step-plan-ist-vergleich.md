# Step 3: Plan-Ist-Vergleich

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.10-auswertungen-und-reports/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Implementierung der Funktion `compare_plan_actuals` in `reports.py` und des MCP-Tools `finance_compare_plan_actuals`. Das Tool führt einen Stichtagsvergleich zwischen dem aktuellen Ist-Gesamtvermögen und den Erwartungswerten aus den Monte-Carlo-Perzentilkurven (p10, p50, p90) durch.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/features/finance/reports.py`
- [ ] [MODIFY] `src/compute_to_ai/mcp/finance_tools.py`
- [ ] [MODIFY] `tests/test_features/test_finance/test_reports.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# src/compute_to_ai/features/finance/reports.py

def compare_plan_actuals(
    plan: Plan,
    audit_result: PathAuditResult | None = None,
    current_step: int = 0
) -> dict[str, Any]:
    """Compares current total net worth against Monte Carlo percentile curves (p10, p50, p90)."""
    # 1. Ist-Gesamtvermögen ermitteln = sum(liquid stores) + sum(invested stores) - sum(liabilities)
    # 2. Falls audit_result None ist: core_run_path_audit ausführen
    # 3. get_percentile_curves für current_step abrufen
    # 4. Klassifizierung vornehmen:
    #    - BELOW_P10
    #    - BETWEEN_P10_AND_P50
    #    - BETWEEN_P50_AND_P90
    #    - ABOVE_P90
    # 5. Delta zu p50 in Euro und % berechnen
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_reports.py -k test_compare_plan_actuals -v
```

### Abzudeckende Testfälle:
- **Happy Path**: Ist-Vermögen liegt über p50 -> Status `BETWEEN_P50_AND_P90`, positives Delta.
- **Edge Cases**:
  - `audit_result` fehlt initial -> wird automatisch ohne Fehler berechnet.
  - `current_step` außerhalb des Simulationshorizonts -> verständliche Fehlermeldung.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] In `Docs/04-Feature-Finanzen-Methodik.md` das Unterkapitel `Plan-Ist-Stichtagsvergleich` ergänzen.
