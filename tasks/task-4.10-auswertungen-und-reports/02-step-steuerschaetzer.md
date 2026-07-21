# Step 2: Einzelverkaufs-Steuerschätzer

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.10-auswertungen-und-reports/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Implementierung der Funktion `estimate_sale_tax` in `reports.py` und des MCP-Tools `finance_estimate_sale_tax`. Das Tool schätzt exakt die Steuerlast für einen Teil- oder Vollverkauf unter Berücksichtigung von FIFO, Teilfreistellung, Bestandsschutz, Sparerpauschbetrag und Abgeltungsteuer + Soli.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/features/finance/reports.py`
- [ ] [MODIFY] `src/compute_to_ai/mcp/finance_tools.py`
- [ ] [MODIFY] `tests/test_features/test_finance/test_reports.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# src/compute_to_ai/features/finance/reports.py

def estimate_sale_tax(
    plan: Plan,
    metadata_store: PositionMetadataStore,
    store_name: str,
    shares_to_sell: float | None = None,
    amount_to_sell: float | None = None,
    sell_all: bool = False,
    remaining_savers_allowance: float = 1000.0,
    church_tax_rate: float = 0.0
) -> dict[str, Any]:
    """Estimates taxes for a hypothetical sale of shares or EUR amount of a position."""
    # 1. Validation: shares_to_sell vs amount_to_sell vs sell_all
    # 2. FIFO-Lot-Abbau simulieren
    # 3. Teilfreistellung anwenden: equity_fund (30%), mixed_fund (15%), bond_fund/other (0%)
    # 4. Vor-2009 Bestandsschutz prüfen (Freibetrag 100.000 € für Gewinne ab 2018)
    # 5. Sparerpauschbetrag anrechnen
    # 6. Abgeltungsteuer 25% + Soli 5.5% (26.375%) + ggf. Kirchensteuer berechnen
    ...
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_reports.py -k test_estimate_sale_tax -v
```

### Abzudeckende Testfälle:
- **Happy Path**: Verkauf von 50 Anteilen eines Aktienfonds (30% Teilfreistellung) mit 2.000 € Gewinn und 1.000 € Sparerpauschbetrag ergibt exakt `(2000 * 0.70 - 1000) * 0.26375 = 105.50 €` Steuer.
- **Edge Cases**:
  - Verkauf verlangt mehr Anteile als im Depot vorhanden (`ValueError`).
  - Verkauf mit Verlust: Steuer = 0.0 €, Verlustausgleichstopf-Hinweis.
  - Verkauf von Vor-2009-Lots: Steuer = 0.0 € (Bestandsschutz).

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] In `Docs/04-Feature-Finanzen-Methodik.md` das Unterkapitel `Einzelverkaufs-Steuerschätzer` ergänzen.
