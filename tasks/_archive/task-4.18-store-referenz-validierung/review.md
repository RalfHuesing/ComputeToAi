# Review-Protokoll: Task 4.18 – Store-Referenz-Validierung an Bausteinen (Fail-Fast)

**Geprüft am**: 2026-07-21
**Review-Agent**: Claude Code (Fable 5), autonome Task-Ausführung gemäß `tasks/workflows/task-execution-workflow.md`
**Gesamt-Ergebnis**: PASSED

---

## 1. Überprüfte Komponenten & Steps
- [x] Step 1 (`01-step-plan-helper-cashflow-liability-pension.md`): PASSED – Commit `ef5cb66`
- [x] Step 2 (`02-step-portfolio-und-tax-bausteine.md`): PASSED – Commit `ab9ff9c`

---

## 2. Test-Ergebnisse (pytest)
```text
uv run pytest -q
308 passed in 74.81s (0:01:14)
```
- **Happy-Path-Coverage**: Bestätigt – alle bestehenden Tests der betroffenen Bausteine laufen unverändert grün (Regressionsschutz).
- **Edge-Case-Coverage**: Bestätigt – je betroffener Funktion mindestens ein Unbekannter-Store-Test:
  - `Plan.validate_store_names`: bekannt/leer/unbekannt/mehrere unbekannte Namen sortiert in der Meldung (`test_plan.py`).
  - `add_income_stream`/`add_expense`/`add_fixed_acquisition`/`add_flexible_acquisition`: `ValueError`, kein Effekt hinzugefügt; `risky_store_name` nur bei `glidepath_years > 0` geprüft (`test_cashflow.py`).
  - `add_liability`: unbekannter `cash_store_name` → `ValueError` ohne Teilzustand (weder Store noch Effekte); `liability_store_name` weiterhin Auto-Create (`test_liability.py`).
  - `add_statutory_pension`: unbekannter `store_name` → `ValueError` (`test_pension.py`).
  - `add_portfolio_rebalancing`: zwei unbekannte `weights`-Keys → beide in der Meldung (`test_portfolio.py`).
  - `add_cash_bucket`: unbekannter `portfolio_weights`-Key bzw. `cash_store_name` → `ValueError`, kein Phantom-Store mehr (Regressionstest gegen altes Auto-Create-Verhalten) (`test_portfolio.py`).
  - `add_tax_manager`: unbekannter `cash_store_name` bzw. `asset_classes`-Key → `ValueError` bereits beim Anlegen (`test_tax.py`).

Qualitäts-Gates: `ruff check` → „All checks passed!"; `pyright` → 114 Fehler vor wie nach der Änderung (per `git stash`-Vergleich verifiziert, alle vorbestehend, keiner in geänderten Dateien).

---

## 3. Code- & Living-Documentation-Check
- [x] Code entspricht den Standards in `.agents/rules/code-standards.mdc` (Typ-Hinweise, Google-Docstrings, Early Returns, keine Duplikate – `_validate_transfer_targets` und `add_position_rebalancing` nutzen jetzt die zentrale Methode).
- [x] Keine Projektplanungs-Verweise im Code (`living-documentation.mdc`).
- [x] Doku in `Docs/` aktualisiert: `01-Kern-Domaenenmodell.md` (Namens-Referenzen werden zur Konfigurationszeit validiert), `03-Feature-Finanzen-Domaenenmodell.md` (referenzierte Speicher müssen vorab existieren, Auto-Create nur für „eigene" Speicher).
- [x] `Docs/10-Roadmap.md` aktualisiert (Epic 4.18 abgehakt).

---

## 4. Anmerkungen & Befunde des Review-Agenten
- **DoD vollständig erfüllt**: `Plan.validate_store_names` existiert analog zu `validate_active_phases` und wird von allen in Konzept-Abschnitt 2 gelisteten Bausteinen sowie `_validate_transfer_targets` verwendet; keine duplizierte Validierungslogik mehr.
- **Bewusste Verhaltensänderungen** wie im Konzept entschieden: `add_liability` und `add_cash_bucket` legen `cash_store_name` nicht mehr stillschweigend an; `core_add_transfer` meldet unbekannte Stores jetzt als `ValueError` statt `KeyError` (MCP-E2E-Test prüft nur `isError`, unverändert grün).
- **Befund im Bestand**: Das Fixture in `tests/test_features/test_finance/test_reports.py` verwendete Effekt-Namen („Rendite etf_world") statt Store-Namen als `weights`-Keys – exakt die stille Fehlkonfiguration, die dieser Task verhindert (das Rebalancing wäre in der Simulation wirkungslos gewesen; die Reports funktionierten nur über einen Fallback). Auf Store-Namen korrigiert, alle Report-Assertions unverändert grün.
- Freigabevermerk: Alle Steps grün, Gates bestanden – Task freigegeben.
