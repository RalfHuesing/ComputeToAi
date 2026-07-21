# Konzept: Task 4.10 – Auswertung: Ist/Soll-Drift- & Gewinn/Bestandsschutz-Report, Einzelverkaufs-Steuerschätzer, Plan-Ist-Vergleich

**Status**: READY  
**Epic / Meilenstein**: Meilenstein 4 – Epic 4.10  
**Erstellt am**: 2026-07-21  

---

## 1. Intention & Fachlicher Kontext

Dieses Task-Paket stellt drei essenzielle Auswertungs- und Diagnose-Werkzeuge für den Finanzberater-Agenten und den Nutzer bereit:

1. **Ist/Soll-Drift- & Gewinn/Bestandsschutz-Report (`finance_get_asset_allocation_report`)**:
   - Zeigt die Vermögensverteilung über alle Anlageklassen und Einzelpositionen.
   - Berechnet die prozentuale Drift gegenüber den Soll-Zielgewichtungen (z.B. BIP-Allokation).
   - Weist unrealisierte Gewinne/Verluste in € und % aus, getrennt nach steuerfreiem Bestandsschutz (vor 2009) vs. regulären Lots.

2. **Einzelverkaufs-Steuerschätzer (`finance_estimate_sale_tax`)**:
   - Ermittelt exakt die Steuerlast bei einem beabsichtigten Teil- oder Vollverkauf einer Position.
   - Wendet das deutsche Steuerrecht an: FIFO-Prinzip, Teilfreistellung (30% Aktienfonds, 15% Mischfonds), Bestandsschutz-Freibeträge (100k€ Freibetrag für Vor-2009-Lots seit 2018), Sparerpauschbetrag (1.000 € / 2.000 €) und Abgeltungsteuer (25% + Soli 5.5% = 26.375%).

3. **Plan-Ist-Vergleich (`finance_compare_plan_actuals`)**:
   - Führt einen Stichtagsvergleich durch: Steht das aktuelle Gesamtvermögen (Positionen + Cash-Bucket - Verbindlichkeiten) im Einklang mit den simulierten Erwartungs-Perzentilen (p10, p50, p90) der Monte-Carlo-Simulation?

---

## 2. Architektur & Betroffene Komponenten

- **`src/compute_to_ai/features/finance/reports.py`** [NEW]:
  Enthält die Kernfunktionen `get_asset_allocation_report`, `estimate_sale_tax`, `compare_plan_actuals`.
- **`src/compute_to_ai/features/finance/position_metadata.py`** [MODIFY]:
  Erweiterung von `PositionMetadata` um `asset_type` (`"equity_fund"`, `"mixed_fund"`, `"real_estate_fund"`, `"bond_fund"`, `"stock"`), um die passende Teilfreistellung automatisch abzuleiten.
- **`src/compute_to_ai/mcp/finance_tools.py`** [MODIFY]:
  Registrierung der drei MCP-Tools `finance_get_asset_allocation_report`, `finance_estimate_sale_tax`, `finance_compare_plan_actuals`.
- **`tests/test_features/test_finance/test_reports.py`** [NEW]:
  Umfassende Unit- und Integrationstests inkl. aller Edge Cases.

---

## 3. Konkrete Code-Anhaltspunkte & Signaturen

```python
# reports.py

def get_asset_allocation_report(plan: Plan, metadata_store: PositionMetadataStore) -> dict[str, Any]:
    ...

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
    ...

def compare_plan_actuals(
    plan: Plan,
    audit_result: PathAuditResult | None = None,
    current_step: int = 0
) -> dict[str, Any]:
    ...
```

---

## 4. Test-Strategie & Edge Cases (Mandatory)

### Happy Path:
- Korrekte Drift-Berechnung bei eingehaltenen und abweichenden Zielgewichtungen.
- Exakte Steuerberechnung für Teilverkäufe mit Teilfreistellung (30%) und Ausnutzung des Sparerpauschbetrags.
- Plan-Ist-Vergleich ordnet Vermögen korrekt zwischen p10/p50/p90 ein.

### Edge Cases (Wissenschaftlich & fachlich fundiert):
- **Portfolio-Gesamtwert = 0 €**: Keine `ZeroDivisionError` bei Prozent-Gewichtungen.
- **Verkauf über Maximalbestand**: Anforderung von mehr Anteilen als vorhanden wirft klaren `ValueError`.
- **Verkauf bei Verlust**: Keine negative Steuer; Verlust verringert zu versteuernden Gewinn auf 0.
- **Bestandsschutz (Vor 2009)**: Vergewissern, dass Vor-2009-Wertsteigerungen bis 31.12.2017 komplett steuerfrei sind und seit 2018 der 100.000 € Freibetrag greift.
- **Fehlendes Audit-Ergebnis**: `compare_plan_actuals` stößt Monte-Carlo/Audit automatisch an, falls noch nicht berechnet.

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [ ] Alle 3 Steps (`01-step-ist-soll-report.md`, `02-step-steuerschaetzer.md`, `03-step-plan-ist-vergleich.md`) vollständig umgesetzt.
- [ ] Tests in `tests/test_features/test_finance/test_reports.py` sind zu 100% grün (`pytest`).
- [ ] Edge Cases systematisch durch Unit-Tests abgedeckt.
- [ ] MCP-Tools registriert und E2E getestet.
- [ ] Living Documentation in `Docs/04-Feature-Finanzen-Methodik.md` nachgezogen.
- [ ] `review.md` durch den Kontroll-Agenten erstellt.
