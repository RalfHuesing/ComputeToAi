# Konzept: Task 4.20 – Tool-Ergonomie & MCP-Vollständigkeits-Lücken

**Status**: IN_PROGRESS
**Epic / Meilenstein**: Meilenstein 4 – Epic 4.20
**Erstellt am**: 2026-07-21

---

## 1. Intention & Fachlicher Kontext

Restliche Audit-Befunde, die weder die Store-Validierung (Task 4.18) noch die Schrittgranularität (Task 4.19) betreffen, aber aus derselben Leitfrage folgen: **Was kann das LLM dem Server geben, was bekommt es zurück, um seine eigene Arbeit zu prüfen, ohne umständliche Umwege gehen zu müssen?**

**Befund 1 – Rückgabewerte uneinheitlich**: Die meisten `add_*`/`finance_set_*`-Tools geben nur einen Bestätigungs-String zurück (`f"added income stream {name!r} to plan {plan_name!r}"`), nicht die tatsächlich gespeicherten, ggf. umgerechneten Werte (z. B. das nach Frequenz-Umrechnung tatsächliche `amount_per_step`, siehe `fix(engine): resolve cashflow frequency relative to plan step granularity` – genau ein falsch umgerechneter Wert wäre mit strukturiertem Echo sofort sichtbar gewesen). Andere Tools machen es vorbildlich: `finance_set_asset_shares` gibt Kurs, Stückzahl und berechneten Marktwert zurück; `finance_update_plan_prices` liefert ein strukturiertes `PriceUpdateResult`. Diese Vorbilder sollen zum Standard werden.

**Befund 2 – `finance_add_fixed_acquisition` exponiert nicht alle Fähigkeiten der zugrunde liegenden Funktion**: `add_fixed_acquisition` (`features/finance/cashflow.py`) unterstützt `glidepath_years`/`risky_store_name` (Kapitalsicherungs-Glidepath vor einer Anschaffung, Epic 4.13, Status DONE), das MCP-Tool `finance_add_fixed_acquisition` (`mcp/tools/finance/_cashflow.py`) nimmt diese Parameter aber gar nicht entgegen. Der Glidepath für **diesen** Baustein ist über MCP schlicht nicht nutzbar, obwohl der Kern das seit Epic 4.13 kann.

**Befund 3 – Breites `except Exception` verschluckt echte Bugs**: `finance_compare_plans` und `finance_compare_plan_actuals` fangen beim Laden eines optionalen Vorergebnisses (`finance_run_monte_carlo`/`core_run_path_audit` noch nicht gelaufen) pauschal `except Exception`. Ein echter Bug beim Deserialisieren (z. B. ein beschädigtes JSON, ein Schema-Mismatch nach einem Server-Update) sieht für den Agenten dann identisch aus wie "kein Ergebnis vorhanden" – kein Fehler, einfach ein leeres/eingeschränktes Ergebnis. Das sollte auf die tatsächlich erwartbare Ausnahme eingegrenzt werden (die `ValueError`, die `load_result`/`load_audited_path` bei fehlender Datei bewusst wirft, siehe `plan_storage.py`).

**Befund 4 – `steps_per_year` nachträglich nicht änderbar**: `Timeline.steps_per_year` (neu, siehe Task-Kontext) lässt sich nur bei `core_create_plan` setzen. Ein bereits angelegter Plan mit falschem/fehlendem Wert (wie zuvor `ralf`, händisch im JSON korrigiert) hat aktuell keinen MCP-Weg zur Korrektur – der Agent müsste die Datei direkt anfassen, was die Architektur explizit ausschließt ("Der Agent greift ausschließlich über die Tools darauf zu, nie direkt", `Docs/02-Architektur-und-MCP.md`).

---

## 2. Architektur & Betroffene Komponenten

- **`src/compute_to_ai/mcp/tools/finance/_cashflow.py`** [MODIFY]: `finance_add_income_stream`/`_expense`/`finance_add_fixed_acquisition` geben ein strukturiertes Objekt zurück (siehe Abschnitt 3), `finance_add_fixed_acquisition` bekommt `glidepath_years`/`risky_store_name`.
- **`src/compute_to_ai/mcp/tools/finance/_liability.py`, `_tax_pension.py`, `_portfolio.py`** [MODIFY]: analoge strukturierte Rückgabe für `finance_add_liability`, `finance_add_statutory_pension`, `finance_add_asset_class`, `finance_add_cash_bucket`, `finance_add_tax_manager` (mindestens: Name/Store(s), tatsächlich gespeicherter `amount_per_step`/Zinssatz/erste aktive Schritte – kein Voll-Dump des Effekts nötig, aber die Werte, die am ehesten aus einer Umrechnung/Berechnung stammen und daher am ehesten überraschen können).
- **`src/compute_to_ai/mcp/tools/core_tools.py`** [MODIFY]: `core_add_effect`/`core_add_transfer` ebenfalls auf strukturierte Rückgabe umstellen (Konsistenz über Kern- und Feature-Tools hinweg).
- **`src/compute_to_ai/mcp/tools/finance/_path_audit.py`, `_reports.py`** [MODIFY]: `except Exception` → `except ValueError` (die von `load_result`/`load_audited_path` dokumentiert geworfene Ausnahme bei fehlendem Ergebnis).
- **`src/compute_to_ai/mcp/tools/core_tools.py`** [MODIFY]: neues Tool `core_set_timeline_parameters(plan_name, steps_per_year)` (oder Erweiterung eines bestehenden Tools – Entscheidung dem Ausführungs-Agenten mit Begründung überlassen, siehe Abschnitt 3) zur nachträglichen Korrektur.
- **Betroffene Tests**: alle E2E-Tests, die den bisherigen reinen String-Rückgabewert der oben genannten Tools prüfen (`tests/test_mcp/test_finance_tools_e2e.py`, `test_server_e2e.py`, `test_path_audit_e2e.py`) – Assertions auf das neue strukturierte Format umstellen, nicht nur oberflächlich anpassen.

---

## 3. Konkrete Code-Anhaltspunkte & Signaturen

Strukturierte Rückgabe nach dem Vorbild von `PriceUpdateResult`/`finance_set_asset_shares`, aber ohne für jedes Tool ein eigenes Pydantic-Modell zu erzwingen – ein generisches, leichtgewichtiges Muster reicht:

```python
# mcp/tools/finance/_cashflow.py, finance_add_income_stream
) -> dict[str, Any]:
    """..."""
    plan = load_plan(working_directory, plan_name)
    add_income_stream(plan, name, store_name, amount, ...)
    save_plan(working_directory, plan)
    effect = plan.effects[-1]  # just appended
    logger.info(...)
    return {
        "name": effect.name,
        "store_name": effect.store_name,
        "amount_per_step": effect.amount_per_step,
        "interval_steps": effect.interval_steps,
        "start_step": effect.start_step,
        "end_step": effect.end_step,
    }
```

`finance_add_fixed_acquisition` (MCP-Ebene):
```python
def finance_add_fixed_acquisition(
    plan_name: str,
    name: str,
    store_name: str,
    amount: float,
    step: int,
    inflation_rate: float = 0.0,
    description: str | None = None,
    glidepath_years: float = 0.0,
    risky_store_name: str | None = None,
) -> dict[str, Any]:
    ...
    add_fixed_acquisition(plan, name, store_name, amount, step, inflation_rate, description, glidepath_years, risky_store_name)
    ...
```

`except Exception` → `except ValueError`:
```python
try:
    result_a = load_result(working_directory, plan_name_a, _MONTE_CARLO_RESULT_FILENAME, MonteCarloResult)
except ValueError:
    result_a = None
```

Für `steps_per_year` nachträglich: einfachster, konsistentester Weg ist ein eigenes Kern-Tool (Timeline ist Kern-Konzept, kein Finance-Spezifikum):
```python
# core_tools.py
@mcp.tool()
def core_set_steps_per_year(plan_name: str, steps_per_year: int) -> str:
    """Change how many steps make up one calendar year on an existing Plan.

    Does not rescale existing effects - amounts/intervals already stored
    via finance_add_income_stream etc. keep their stored values, which may
    now mean something different (e.g. a `"yearly"`-frequency effect added
    under steps_per_year=12 keeps firing every 12 steps even after this is
    changed to 1). Intended for correcting a wrong value early, not for
    reinterpreting an already-built plan.
    """
    plan = load_plan(working_directory, plan_name)
    plan.timeline.steps_per_year = steps_per_year
    save_plan(working_directory, plan)
    ...
```
Die Warnung im Docstring ist wichtig und muss im Tool selbst (nicht nur hier im Konzept) stehen, da das MCP-Schema die einzige "Doku", die der Agent zur Aufrufzeit sieht, direkt ist (`Docs/02-Architektur-und-MCP.md`, "Selbstbeschreibung").

---

## 4. Test-Strategie & Edge Cases

- **Happy Path**: Jedes umgestellte Tool liefert ein Dict mit den dokumentierten Schlüsseln und plausiblen Werten (Regressionstest: Werte stimmen mit dem intern gespeicherten Effekt überein).
- **Edge Cases**:
  - `finance_add_fixed_acquisition` mit `glidepath_years > 0` und `risky_store_name` erzeugt tatsächlich einen `flexible_acquisition`-Effekt (nicht mehr nur `growing_fixed`) – Regressionstest gegen `add_fixed_acquisition`s bestehende Python-API-Tests (`test_liability.py`/`test_glidepath.py`, je nachdem wo `test_acquisition_glidepath` liegt).
  - `finance_compare_plans`/`finance_compare_plan_actuals`: ein absichtlich kaputtes/leeres Ergebnis-JSON (nicht bloß fehlend) muss jetzt einen Fehler propagieren statt still `None` zu werden.
  - `core_set_steps_per_year` auf einem Plan mit bereits vorhandenen Effekten ändert nur `timeline.steps_per_year`, keine bestehenden `amount_per_step`/`interval_steps`-Werte (expliziter Test, der genau das prüft, da das leicht missverstanden werden könnte).
- **Kommando**: `pytest tests/test_mcp/ tests/test_features/test_finance/ -v`

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [ ] Alle Steps in diesem Task-Ordner sind grün ausgeführt.
- [ ] Alle in Abschnitt 2 gelisteten Tools liefern strukturierte Rückgabewerte; betroffene E2E-Tests sind auf das neue Format umgestellt.
- [ ] `finance_add_fixed_acquisition` unterstützt `glidepath_years`/`risky_store_name` über MCP.
- [ ] `except Exception` in `_path_audit.py`/`_reports.py` auf `except ValueError` eingegrenzt.
- [ ] `core_set_steps_per_year` existiert, mit Warnhinweis im Docstring zu nicht rückwirkend umgerechneten Effekten.
- [ ] `ruff check` und `pyright` ohne neue Warnungen.
- [ ] Doku aktualisiert: `Docs/02-Architektur-und-MCP.md` (Baustein-Katalog-Abschnitt: Rückgabewert-Konvention "strukturiertes Echo statt reinem Bestätigungs-String" als Prinzip festhalten).
- [ ] `review.md` erstellt und gegengezeichnet.
- [ ] `Docs/10-Roadmap.md` Epic 4.20 abgehakt `[x]`.
