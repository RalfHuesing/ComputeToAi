# Step 1: Plan.validate_store_names + Cashflow/Liability/Pension-Bausteine

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.18-store-referenz-validierung/00-konzept.md)
**Status**: DONE

---

## 1. Step-Intention

Zentrale Validierungsmethode `Plan.validate_store_names` schaffen, bestehende Duplikate darauf umstellen, und in den Cashflow-/Liability-/Pension-Bausteinen jeden referenzierten (nicht neu angelegten) Store-Namen vor jeder Mutation validieren.

---

## 2. Zu bearbeitende / neu anzulegende Dateien

- [ ] [MODIFY] `src/compute_to_ai/engine/plan.py` – neue Methode `validate_store_names`.
- [ ] [MODIFY] `src/compute_to_ai/mcp/tools/core_tools.py` – `_validate_transfer_targets` nutzt `plan.validate_store_names`.
- [ ] [MODIFY] `src/compute_to_ai/features/finance/positions_rebalancing.py` – Inline-Schleife in `add_position_rebalancing` durch `plan.validate_store_names` ersetzen (Verhalten identisch, nur Duplikat entfernt).
- [ ] [MODIFY] `src/compute_to_ai/features/finance/cashflow.py` – `add_income_stream`, `add_expense`, `add_fixed_acquisition`, `add_flexible_acquisition`.
- [ ] [MODIFY] `src/compute_to_ai/features/finance/liability.py` – `add_liability` (`cash_store_name` validieren, `liability_store_name` bleibt Auto-Create).
- [ ] [MODIFY] `src/compute_to_ai/features/finance/pension.py` – `add_statutory_pension`.
- [ ] [NEW/MODIFY] passende Tests je Funktion (siehe Abschnitt 4).

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

Siehe `00-konzept.md`, Abschnitt 3, für die exakte Signatur von `validate_store_names` und Anwendungsbeispiele.

Reihenfolge innerhalb jeder Funktion: **erst** alle Validierungen (Phasen, Store-Namen), **dann** erst Mutation von `plan.stores`/`plan.effects` – kein Teilzustand bei einem Fehler. Bei `add_fixed_acquisition` gilt die `risky_store_name`-Prüfung nur, wenn `glidepath_years > 0.0` (sonst wird der Parameter gar nicht verwendet).

### Spezifische Hinweise:
- Beachte `.agents/rules/code-standards.mdc` (Typ-Hinweise, Google-Docstrings, Python 3.12+).
- Beachte `.agents/rules/language.mdc` (Code & Kommentare in Englisch, Doku auf Deutsch).
- `add_liability`s bisheriges Auto-Create von `cash_store_name` entfällt bewusst (siehe Konzept, Abschnitt 1) – das ist eine Verhaltensänderung, kein Versehen.

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_engine/test_plan.py tests/test_mcp/test_server_e2e.py tests/test_features/test_finance/test_cashflow.py tests/test_features/test_finance/test_frequency_effects.py tests/test_features/test_finance/test_liability.py tests/test_features/test_finance/test_glidepath.py -v
```

### Abzudeckende Testfälle:
- **Happy Path**: Jede der fünf Funktionen mit ausschließlich bekannten Store-Namen funktioniert unverändert.
- **Edge Cases**:
  - `add_income_stream`/`add_expense` mit unbekanntem `store_name` → `ValueError`, kein Effekt wird hinzugefügt.
  - `add_fixed_acquisition` mit `glidepath_years > 0` und unbekanntem `risky_store_name` → `ValueError`.
  - `add_flexible_acquisition` mit unbekanntem `risky_store_name` oder `safe_store_name`.
  - `add_liability` mit unbekanntem `cash_store_name` → `ValueError` (vorher: stiller Auto-Create eines leeren Stores – expliziter Regressionstest, der das alte Verhalten als überholt dokumentiert); `liability_store_name` wird weiterhin auto-erzeugt, wenn er fehlt.
  - `add_statutory_pension` mit unbekanntem `store_name`.
  - Bestehende Tests, die sich bislang auf implizites Auto-Create von `cash_store_name` in `add_liability` verlassen (`test_liability.py`, ggf. `test_path_audit.py`, `test_glidepath.py`), vorher explizit `core_add_store`/`plan.stores.append(...)` ergänzen.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/01-Kern-Domaenenmodell.md`: Store-Referenzen werden analog zu Phasen-Referenzen zur Konfigurationszeit validiert (kurzer Verweis neben der bestehenden Phasen-Beschreibung).
