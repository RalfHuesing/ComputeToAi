# Konzept: Task 4.18 – Store-Referenz-Validierung an Bausteinen (Fail-Fast)

**Status**: READY
**Epic / Meilenstein**: Meilenstein 4 – Epic 4.18
**Erstellt am**: 2026-07-21

---

## 1. Intention & Fachlicher Kontext

**Ausgangsbefund (Audit)**: Ein Agent-Bug-Report zu Plan `ralf` deckte zwei reale Bugs auf (mittlerweile gefixt: `fix(engine): resolve cashflow frequency relative to plan step granularity`, `fix(mcp): require a name on core_add_effect`). Ein anschließender Audit des gesamten MCP-Tool-Bestands (aus Sicht Nutzer → LLM → Server) fand eine dritte, verwandte und potenziell schwerwiegendere Fehlerklasse: **die meisten `add_*`-Bausteine validieren referenzierte Store-Namen nicht.**

**Warum das gefährlich ist**: Die Engine überspringt einen Effekt, dessen `store_name` nicht in der aktuellen Step-Berechnung bekannt ist, vollkommen stillschweigend – kein Fehler, keine Warnung:

```python
# src/compute_to_ai/engine/_simulation_phase1.py, _apply_growing_fixed_effect
store_name = effect.store_name
if store_name in fixed_additions:   # fixed_additions ist nur mit echten Store-Namen befüllt
    ...
# store_name nicht bekannt -> Effekt tut buchstäblich nichts, kein Log, kein Raise
```

Ein Tippfehler im Store-Namen bei `finance_add_income_stream`/`_expense` (z. B. "ING Verrechungskonto" statt "ING Verrechnungskonto") erzeugt also einen Effekt, der beim Anlegen **erfolgreich** zurückgemeldet wird, aber in der Simulation **nie** wirksam wird – ohne dass der Agent (oder `finance_audit_plan`) das momentan bemerken kann. Das ist strukturell dasselbe Problem, das für Phasennamen bereits bewusst über `Plan.validate_active_phases` verhindert wurde (siehe `plan.py`, Docstring: „Ohne dies wird ein getippter Phasenname stillschweigend akzeptiert und der referenzierende Effekt aktiviert sich einfach nie, statt zur Konfigurationszeit zu scheitern"). Dieselbe Begründung gilt eins zu eins für Store-Namen, wurde aber nicht konsequent auf alle Bausteine übertragen. `core_add_transfer` (`_validate_transfer_targets` in `core_tools.py`) und `add_position_rebalancing` (`positions_rebalancing.py`) machen es bereits richtig und dienen als Referenzimplementierung.

**Zwei Arten von Store-Parametern, zwei Regeln** (Entscheidung dieses Konzepts, siehe Audit-Diskussion):
- **Neu angelegte, dem Baustein "gehörende" Stores** (z. B. der Verbindlichkeits-Speicher in `add_liability`, der Anlageklassen-Speicher in `add_asset_class`): Auto-Create bei Nichtvorhandensein bleibt wie bisher – hier ist der Store unzweideutig neuer Bestandteil dieses einen Aufrufs, ein Tippfehler kann hier nichts fälschlich referenzieren, weil noch nichts existiert, das gemeint sein könnte.
- **Referenzierte, bereits existierende Stores** (z. B. `cash_store_name` in `add_liability`/`add_cash_bucket`/`add_tax_manager`, `store_name` in `add_income_stream`/`_expense`/`add_statutory_pension`, `risky_store_name`/`safe_store_name` in (flexible) Anschaffungen, die Keys in `portfolio_weights`/`weights`): Diese müssen **vorher existieren** und werden ab sofort validiert statt (teils) stillschweigend auto-erzeugt. Ein bislang implizites Auto-Create von `cash_store_name` in `add_liability`/`add_cash_bucket` ist eine bewusste Verhaltensänderung – ein Tippfehler dort erzeugte bisher einen leeren Phantom-Store statt eines Fehlers, was ebenso irreführend ist wie der stille No-Op.

**Welches Verhalten wird angestrebt?**: Jeder Aufruf, der einen "referenzierten" Store-Namen entgegennimmt, der nicht in `plan.stores` existiert, schlägt sofort mit einer klaren, umsetzbaren Fehlermeldung fehl (welcher Store fehlt, welches Tool ihn ggf. zuerst anlegen würde) – analog zu `finance_set_asset_shares`s bereits vorbildlicher Meldung "add it first with finance_add_asset_class".

---

## 2. Architektur & Betroffene Komponenten

- **`src/compute_to_ai/engine/plan.py`** [MODIFY]: Neue Methode `Plan.validate_store_names(names: Iterable[str]) -> None`, analog zu `validate_active_phases` (raist `ValueError` mit sortierter Liste aller unbekannten Namen). Zentrale, einmalige Implementierung statt der bisherigen Duplikate (`_validate_transfer_targets` in `core_tools.py`, Inline-Schleife in `add_position_rebalancing`).
- **`src/compute_to_ai/mcp/tools/core_tools.py`** [MODIFY]: `_validate_transfer_targets` auf `plan.validate_store_names(...)` umstellen (Verhalten unverändert, nur Duplikat entfernt).
- **`src/compute_to_ai/features/finance/cashflow.py`** [MODIFY]: `add_income_stream` (`store_name`), `add_expense` (`store_name`), `add_fixed_acquisition` (`store_name`; `risky_store_name` nur wenn `glidepath_years > 0`), `add_flexible_acquisition` (`risky_store_name`, `safe_store_name`) validieren vor jeder Mutation.
- **`src/compute_to_ai/features/finance/liability.py`** [MODIFY]: `add_liability` validiert `cash_store_name` (neu, bisher unvalidiert); `liability_store_name` bleibt Auto-Create.
- **`src/compute_to_ai/features/finance/pension.py`** [MODIFY]: `add_statutory_pension` validiert `store_name`.
- **`src/compute_to_ai/features/finance/portfolio.py`** [MODIFY]: `add_portfolio_rebalancing` validiert alle Keys in `weights`; `add_cash_bucket` validiert alle Keys in `portfolio_weights` und ändert `cash_store_name` von Auto-Create auf Validierung (Verhaltensänderung, siehe oben).
- **`src/compute_to_ai/features/finance/tax.py`** [MODIFY]: `add_tax_manager` validiert `cash_store_name` (Verhaltensänderung: bisher nicht validiert und ohne Auto-Create – ein Tippfehler landete stillschweigend in `balances[cash_store]`, ohne dass der Wert je nach `plan.stores` zurückgeschrieben wird, siehe `_reconcile_balances` in `simulation.py`) sowie alle Keys in `asset_classes` (bisher erst zur Laufzeit über `plan.store(name)` mit `KeyError`, jetzt zusätzlich sofort beim Anlegen).
- **`src/compute_to_ai/features/finance/positions_rebalancing.py`** [KEEP]: bereits korrekt, keine Änderung – dient als Referenz.
- **Betroffene Tests** (auf implizites Auto-Create von `cash_store_name` prüfen und ggf. anpassen, `plan.store(cash_store_name)` vorher explizit anlegen): `tests/test_features/test_finance/test_liability.py`, `test_portfolio.py`, `test_tax.py`, `test_glidepath.py`, `test_life_phases_harmonies.py`, `test_path_audit.py`, `tests/test_mcp/test_finance_tools_e2e.py`, `test_path_audit_e2e.py`.

---

## 3. Konkrete Code-Anhaltspunkte & Signaturen

```python
# engine/plan.py, neu auf Plan
from collections.abc import Iterable

def validate_store_names(self, names: Iterable[str]) -> None:
    """Raise ValueError if any name is not a registered Store.

    Without this, a typo'd store name is accepted silently and the
    effect referencing it simply never applies (Phase 1 skips any
    store_name not in fixed_additions, see _simulation_phase1.py),
    instead of failing at configuration time - the same rationale as
    validate_active_phases, generalized to store references.
    """
    known = {store.name for store in self.stores}
    unknown = sorted({name for name in names if name not in known})
    if unknown:
        msg = f"unknown store name(s) {unknown!r} in plan {self.name!r}"
        raise ValueError(msg)
```

```python
# features/finance/cashflow.py, add_income_stream (analog: add_expense)
def add_income_stream(plan: Plan, name: str, store_name: str, ...) -> None:
    plan.validate_active_phases(active_phases)
    plan.validate_store_names([store_name])
    ...
```

```python
# features/finance/liability.py, add_liability
def add_liability(plan: Plan, name: str, liability_store_name: str, cash_store_name: str, ...) -> None:
    plan.validate_store_names([cash_store_name])  # NEW - existing store, no auto-create
    # liability_store_name: auto-create bleibt unverändert (eigener, neuer Store)
    ...
```

```python
# features/finance/portfolio.py, add_cash_bucket
def add_cash_bucket(plan: Plan, portfolio_weights: dict[str, float], ..., cash_store_name: str = "cash", ...) -> None:
    plan.validate_store_names(portfolio_weights.keys())
    plan.validate_store_names([cash_store_name])  # CHANGED: war Auto-Create, jetzt Validierung
    ...
```

Fehlermeldungen sollen wo sinnvoll auf das passende Anlage-Tool verweisen (Vorbild `finance_set_asset_shares`):
```python
msg = f"no store named {cash_store_name!r} in plan {plan.name!r}; add it first with core_add_store"
```

---

## 4. Test-Strategie & Edge Cases

- **Happy Path**: Jeder betroffene `add_*`-Aufruf mit existierenden Stores funktioniert unverändert (Regressionsschutz über bestehende Tests).
- **Edge Cases & Fehlerfälle** (je betroffener Funktion mindestens ein Test):
  - Unbekannter `store_name`/`cash_store_name`/Key in `weights`/`portfolio_weights`/`asset_classes` → `ValueError` mit dem/den fehlenden Namen in der Meldung, **bevor** irgendein Effekt/Store der Plan-Konfiguration hinzugefügt wird (kein Teilzustand – bei einem Fehler bleibt der Plan unverändert, wichtig für `add_liability`/`add_tax_manager`, die mehrere Effekte auf einmal anlegen).
  - `add_liability`/`add_cash_bucket` mit fehlendem `cash_store_name`: schlägt jetzt fehl statt (wie bisher) einen leeren Store anzulegen – expliziter Test, der das alte Auto-Create-Verhalten als **nicht mehr gültig** dokumentiert.
  - `add_fixed_acquisition` mit `glidepath_years > 0` und unbekanntem `risky_store_name`.
  - Mehrere unbekannte Namen gleichzeitig (z. B. zwei Keys in `portfolio_weights`) → beide in der Fehlermeldung, nicht nur der erste.
- **Kommando**: `pytest tests/test_engine/test_plan.py tests/test_features/test_finance/ tests/test_mcp/ -v`

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [ ] Alle Steps in diesem Task-Ordner sind grün ausgeführt.
- [ ] `Plan.validate_store_names` existiert und wird von `_validate_transfer_targets` sowie allen in Abschnitt 2 gelisteten Bausteinen verwendet (keine duplizierte Validierungslogik mehr).
- [ ] Alle betroffenen bestehenden Tests (Abschnitt 2) sind angepasst und grün, inklusive der neuen Edge-Case-Tests aus Abschnitt 4.
- [ ] `ruff check` und `pyright` ohne neue Warnungen.
- [ ] Doku aktualisiert: `Docs/01-Kern-Domaenenmodell.md` (Store-Referenzen werden wie Phasen-Referenzen zur Konfigurationszeit validiert) und `Docs/03-Feature-Finanzen-Domaenenmodell.md` (Auto-Create nur für neu angelegte, "eigene" Stores, nicht für referenzierte).
- [ ] `review.md` erstellt und gegengezeichnet.
- [ ] `Docs/10-Roadmap.md` Epic 4.18 abgehakt `[x]`.
