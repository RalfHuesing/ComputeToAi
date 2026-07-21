# Step 2: Portfolio- und Steuer-Bausteine

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.18-store-referenz-validierung/00-konzept.md)
**Status**: DONE

---

## 1. Step-Intention

Store-Referenz-Validierung (aus Step 1) auf die verbleibenden Bausteine mit Store-Referenzen anwenden: Portfolio-Rebalancing, Cash-Bucket und Steuer-Manager. Zusätzlich: verbleibende betroffene End-to-End-Tests (MCP-Ebene) prüfen/anpassen.

---

## 2. Zu bearbeitende / neu anzulegende Dateien

- [ ] [MODIFY] `src/compute_to_ai/features/finance/portfolio.py` – `add_portfolio_rebalancing` (Keys in `weights`), `add_cash_bucket` (Keys in `portfolio_weights`, `cash_store_name` von Auto-Create auf Validierung).
- [ ] [MODIFY] `src/compute_to_ai/features/finance/tax.py` – `add_tax_manager` (`cash_store_name`, Keys in `asset_classes`).
- [ ] [MODIFY] betroffene Tests: `tests/test_features/test_finance/test_portfolio.py`, `test_tax.py`, `test_life_phases_harmonies.py`, `test_path_audit.py`, `tests/test_mcp/test_finance_tools_e2e.py`, `test_path_audit_e2e.py` (jeweils prüfen, ob `cash_store_name`/Portfolio-Keys vor dem jeweiligen `add_*`-Aufruf bereits existieren; falls nicht, `core_add_store` ergänzen).

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

Siehe `00-konzept.md`, Abschnitt 3 (Code-Beispiel für `add_cash_bucket`). Für `add_tax_manager` analog:

```python
# features/finance/tax.py, add_tax_manager
def add_tax_manager(plan: Plan, cash_store_name: str = "cash", ..., asset_classes: dict[str, AssetClassTaxConfig] | None = None, ...) -> None:
    plan.validate_store_names([cash_store_name])
    if asset_classes:
        plan.validate_store_names(asset_classes.keys())
    ...
```

`asset_classes`-Keys schlugen bisher erst zur Simulationslaufzeit über `plan.store(name)` (KeyError in `_calculate_sales_taxable_gains`/`_calculate_vorabpauschale_taxable`) fehl – die neue Prüfung verschiebt das nur auf den frühestmöglichen Zeitpunkt (Konfigurationszeit), Verhalten bei falschem Namen bleibt "Fehler", nur früher und mit klarerer Meldung.

### Spezifische Hinweise:
- Beachte `.agents/rules/code-standards.mdc` und `.agents/rules/language.mdc`.
- `add_cash_bucket`s Wechsel von Auto-Create auf Validierung für `cash_store_name` ist dieselbe bewusste Verhaltensänderung wie bei `add_liability` in Step 1 – konsistent begründen/dokumentieren.

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_portfolio.py tests/test_features/test_finance/test_tax.py tests/test_features/test_finance/test_life_phases_harmonies.py tests/test_features/test_finance/test_path_audit.py tests/test_mcp/ -v
```

### Abzudeckende Testfälle:
- **Happy Path**: `add_portfolio_rebalancing`/`add_cash_bucket`/`add_tax_manager` mit ausschließlich bekannten Store-Namen unverändert funktionsfähig.
- **Edge Cases**:
  - `add_portfolio_rebalancing` mit einem unbekannten Key in `weights` → `ValueError`.
  - `add_cash_bucket` mit unbekanntem Key in `portfolio_weights` bzw. unbekanntem `cash_store_name` → `ValueError` (Regressionstest gegen das alte Auto-Create-Verhalten).
  - `add_tax_manager` mit unbekanntem `cash_store_name` bzw. unbekanntem Key in `asset_classes` → `ValueError`, jetzt bereits beim Anlegen statt erst beim Simulationslauf.
  - Volle Testsuite (`pytest -q`) weiterhin grün, insbesondere die MCP-E2E-Tests, die Cash-Bucket/Tax-Manager auf einem frisch angelegten Plan ohne vorherigen `core_add_store`-Aufruf für den Cash-Store nutzen (ggf. dort einen `core_add_store`-Aufruf ergänzen).

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/03-Feature-Finanzen-Domaenenmodell.md`: Abschnitt zu Cash-Bucket/Steuer-Manager ergänzen, dass referenzierte Stores (anders als der jeweils neu angelegte "eigene" Store, z. B. der Verbindlichkeits-Speicher) vorab existieren müssen.
- [ ] `Docs/10-Roadmap.md`: Epic 4.18 abhaken, sobald Review „PASSED".
