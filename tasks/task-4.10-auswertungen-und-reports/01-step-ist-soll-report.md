# Step 1: Ist/Soll-Drift- und Gewinn/Bestandsschutz-Report

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.10-auswertungen-und-reports/00-konzept.md)  
**Status**: DONE  

---

## 1. Step-Intention
Implementierung der Kernfunktion `get_asset_allocation_report` und des zugehörigen MCP-Tools `finance_get_asset_allocation_report`. Der Report stellt Soll- und Ist-Gewichtung gegenüber, berechnet die prozentuale Drift und schlüsselt unrealisierte Gewinne/Verluste nach Bestandsschutz- und regulären Lots auf.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [x] [NEW] `src/compute_to_ai/features/finance/reports.py`
- [x] [MODIFY] `src/compute_to_ai/features/finance/position.py`
- [x] [MODIFY] `src/compute_to_ai/mcp/tools/finance_tools.py`
- [x] [NEW] `tests/test_features/test_finance/test_reports.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# src/compute_to_ai/features/finance/reports.py

from typing import Any
from compute_to_ai.engine.plan import Plan
from compute_to_ai.features.finance.position import PositionRegistry

def get_asset_allocation_report(
    plan: Plan,
    metadata_store: PositionRegistry
) -> dict[str, Any]:
    """Computes target vs actual asset allocation, drift, and unrealized gains breakdown."""
    total_portfolio_value = 0.0
    # 1. Total Portfolio Marktwert berechnen (Summe aller Positionsspeicher)
    # 2. Pro Anlageklasse Soll-Gewichtung ermitteln
    # 3. Ist-Gewichtung = actual_value / total_portfolio_value (0.0 if total == 0)
    # 4. Drift = actual_weight - target_weight
    # 5. Lots analysieren: rule_version == "2008_or_earlier" vs regulär
    ...
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_reports.py -k test_get_asset_allocation_report -v
```

### Abzudeckende Testfälle:
- **Happy Path**: Portfolio mit 2 Anlageklassen (z.B. 70/30 Soll) und 3 Positionen liefert exakte Werte für Marktwert, Drift und Gewinne.
- **Edge Cases**:
  - Portfolio mit Gesamtmarktwert 0 € (keine ZeroDivisionError).
  - Position ohne Lot-Historie (Fallback auf aktuellen Saldo).
  - Mischung aus Vor-2009-Bestandsschutz-Lots und aktuellen Lots.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [x] In `Docs/04-Feature-Finanzen-Methodik.md` das Unterkapitel `Ist/Soll-Drift-Report` ergänzen.

