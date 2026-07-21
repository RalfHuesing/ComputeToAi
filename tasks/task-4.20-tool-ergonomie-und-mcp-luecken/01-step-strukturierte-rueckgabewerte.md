# Step 1: Strukturierte Rückgabewerte für add_*-Tools

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.20-tool-ergonomie-und-mcp-luecken/00-konzept.md)
**Status**: DONE

---

## 1. Step-Intention

Alle `add_*`-MCP-Tools, die aktuell nur einen Bestätigungs-String zurückgeben, auf ein strukturiertes Dict mit den tatsächlich gespeicherten (ggf. umgerechneten) Werten umstellen – nach dem Vorbild von `finance_set_asset_shares`/`finance_update_plan_prices`.

---

## 2. Zu bearbeitende / neu anzulegende Dateien

- [ ] [MODIFY] `src/compute_to_ai/mcp/tools/finance/_cashflow.py` – `finance_add_income_stream`, `finance_add_expense`, `finance_add_fixed_acquisition`, `finance_add_flexible_acquisition`.
- [ ] [MODIFY] `src/compute_to_ai/mcp/tools/finance/_liability.py` – `finance_add_liability`.
- [ ] [MODIFY] `src/compute_to_ai/mcp/tools/finance/_tax_pension.py` – `finance_add_statutory_pension` (mind. tatsächlicher `annual_amount` nach Abschlag/Zuschlag).
- [ ] [MODIFY] `src/compute_to_ai/mcp/tools/finance/_portfolio.py` – `finance_add_asset_class`, `finance_add_portfolio_rebalancing`, `finance_add_cash_bucket`.
- [ ] [MODIFY] `src/compute_to_ai/mcp/tools/core_tools.py` – `core_add_effect`, `core_add_transfer`.
- [ ] [MODIFY] betroffene E2E-Tests: `tests/test_mcp/test_finance_tools_e2e.py`, `test_server_e2e.py`, `test_path_audit_e2e.py` (Assertions auf `result.isError`/String-Vergleich → auf Dict-Keys prüfen, wo jetzt strukturiert zurückgegeben wird).

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

Siehe `00-konzept.md`, Abschnitt 3, für das generische Muster. Wichtig: **kein** volles `effect.model_dump()` zurückgeben (zu viel Rauschen, u. U. interne Felder) – nur die Werte, die am ehesten von einer Umrechnung/Berechnung betroffen sind und die der Agent gegen seine eigene Eingabe prüfen will (Betrag pro Schritt, Intervall, Start/Ende, ggf. der berechnete Zinssatz/Anpassungsfaktor). Je Tool selbst entscheiden, welche Felder das sind – orientiert an dem, was in diesem Tool tatsächlich berechnet statt nur durchgereicht wird.

`finance_add_statutory_pension` z. B.: der interessante Rückgabewert ist `annual_amount` (nach Rentenabschlag/-zuschlag), nicht `name`/`store_name` (die kennt der Aufrufer ja schon aus seiner eigenen Eingabe).

### Spezifische Hinweise:
- Beachte `.agents/rules/code-standards.mdc` und `.agents/rules/language.mdc`.
- Rückgabetyp der Tool-Funktionen ändert sich von `str` auf `dict[str, Any]` – Type Hints entsprechend anpassen.
- Logging (`logger.info`/`logger.debug`) bleibt wie bisher (INFO ohne Werte, DEBUG mit Werten, siehe `Docs/02-Architektur-und-MCP.md`, "Logging").

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_mcp/ -v
```

### Abzudeckende Testfälle:
- **Happy Path**: Jedes umgestellte Tool liefert die dokumentierten Keys mit Werten, die dem tatsächlich gespeicherten Effekt entsprechen (Cross-Check via `core_list_effects` im selben Test).
- **Edge Cases**:
  - `finance_add_income_stream` mit `frequency="monthly"` auf einem Jahresschritt-Plan (`steps_per_year=1`) – Rückgabewert zeigt den gefalteten Jahresbetrag (`amount * 12`), nicht den rohen Monatsbetrag – macht genau die Bug-Klasse aus dem ursprünglichen Report für den Aufrufer sofort sichtbar.
  - `finance_add_statutory_pension` mit `actual_retirement_step < regular_retirement_step` – Rückgabewert zeigt den reduzierten `annual_amount`.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/02-Architektur-und-MCP.md`: Rückgabewert-Konvention ("strukturiertes Echo der gespeicherten Werte statt reinem Bestätigungs-String") im Baustein-Katalog-Abschnitt festhalten.
