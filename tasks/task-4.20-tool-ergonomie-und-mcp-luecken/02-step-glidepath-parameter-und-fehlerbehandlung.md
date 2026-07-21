# Step 2: Glidepath-Parameter für Anschaffungen & präzisere Fehlerbehandlung

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.20-tool-ergonomie-und-mcp-luecken/00-konzept.md)
**Status**: DONE

---

## 1. Step-Intention

`finance_add_fixed_acquisition` bekommt die vom Kern bereits unterstützten `glidepath_years`/`risky_store_name`-Parameter (Epic 4.13, Status DONE, aber nie bis zum MCP-Tool durchgereicht). Zusätzlich: `except Exception` in `finance_compare_plans`/`finance_compare_plan_actuals` auf die tatsächlich erwartbare Ausnahme eingrenzen.

---

## 2. Zu bearbeitende / neu anzulegende Dateien

- [ ] [MODIFY] `src/compute_to_ai/mcp/tools/finance/_cashflow.py` – `finance_add_fixed_acquisition`.
- [ ] [MODIFY] `src/compute_to_ai/mcp/tools/finance/_path_audit.py` – `finance_compare_plans`.
- [ ] [MODIFY] `src/compute_to_ai/mcp/tools/finance/_reports.py` – `finance_compare_plan_actuals`.
- [ ] [NEW/MODIFY] Test für `finance_add_fixed_acquisition` mit Glidepath über die volle MCP-Schicht (bisher nur auf Python-API-Ebene getestet, z. B. `test_acquisition_glidepath` in `tests/test_features/test_finance/test_cashflow.py` bzw. dem tatsächlichen Testmodul).

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

Siehe `00-konzept.md`, Abschnitt 3, für beide Code-Skizzen. Bei `finance_add_fixed_acquisition`: `risky_store_name` bleibt optional (`str | None = None`), `glidepath_years` bleibt `0.0` per Default – reines Additiv, kein Breaking Change für bestehende Aufrufer ohne diese Parameter.

Für die `except`-Eingrenzung: **vorher verifizieren**, dass `load_result`/`load_audited_path` (`plan_storage.py`) tatsächlich ausschließlich `ValueError` werfen (aktueller Code-Stand: ja, siehe `plan_storage.py`) – falls sich das durch andere gleichzeitige Änderungen geändert haben sollte, die dann tatsächlich passende(n) Exception-Typ(en) verwenden statt weiter pauschal zu fangen.

### Spezifische Hinweise:
- Beachte `.agents/rules/code-standards.mdc` und `.agents/rules/language.mdc`.
- Kein `# noqa`/Ausnahmeregel für den breiten `except` einführen – die Eingrenzung ist die eigentliche Aufgabe, nicht ihre Dokumentation.

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_mcp/test_finance_tools_e2e.py tests/test_mcp/test_path_audit_e2e.py -v
```

### Abzudeckende Testfälle:
- **Happy Path**: `finance_add_fixed_acquisition` ohne Glidepath-Parameter verhält sich unverändert (Regressionstest).
- **Edge Cases**:
  - `finance_add_fixed_acquisition` mit `glidepath_years > 0` und `risky_store_name` über die volle MCP-Schicht erzeugt einen `flexible_acquisition`-Computed-Effect (prüfbar über `core_list_effects`), nicht nur einen einmaligen `growing_fixed`-Effekt.
  - `finance_compare_plans`/`finance_compare_plan_actuals` mit fehlendem Vorergebnis: unverändert `None`/leeres Ergebnis (Regressionstest für den Normalfall "noch nicht simuliert").
  - `finance_compare_plans`/`finance_compare_plan_actuals` mit einer absichtlich beschädigten Ergebnis-Datei (z. B. ungültiges JSON oder fehlendes Pflichtfeld) muss jetzt einen Fehler propagieren, nicht mehr still `None` zurückgeben.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] Keine Doku-Änderung erwartet (reine Tool-Vervollständigung/Robustheit, Fachverhalten unverändert) – im Review kurz bestätigen, dass das stimmt.
