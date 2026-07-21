# Konzept: Task 4.19 – Schrittgranularität konsistent durchs Finance-Modul ziehen

**Status**: IN_PROGRESS
**Epic / Meilenstein**: Meilenstein 4 – Epic 4.19
**Erstellt am**: 2026-07-21

---

## 1. Intention & Fachlicher Kontext

**Direkte Folge von `fix(engine): resolve cashflow frequency relative to plan step granularity`**: `Timeline.steps_per_year` (Default 12, siehe `engine/timeline.py`) macht die Schrittweite eines Plans explizit und wird bislang **ausschließlich** von `features/finance/cashflow.py` (Frequenz-/Intervall-Umrechnung für Einkommen/Ausgaben) berücksichtigt. Der Audit des restlichen Finance-Moduls zeigt: praktisch jeder andere Baustein, der mit Alter, Renteneintritt oder Cash-Bucket-Größen rechnet, nimmt weiterhin **hart "1 Step = 1 Jahr" an**, unabhängig vom tatsächlichen Wert von `steps_per_year`:

- `features/calculations/dates.py`: `step_to_age`/`age_to_step` – Docstring: "one step == one year" – wörtlich hartkodiert, keine Parametrisierung.
- `features/finance/phases.py`: `build_standard_life_phases` – Docstring: "Step 0 corresponds to current_age; each step is one year" – Altersdifferenzen werden 1:1 als Schrittdifferenzen verwendet.
- `features/finance/pension.py`: `add_statutory_pension` – `months_early = ... * 12` nimmt an, eine Schrittdifferenz sei bereits in Jahren.
- `features/finance/portfolio.py`: Cash-Bucket-Entnahmepuffer (`_calculate_withdrawal_buffer`, Baustein 3 "Entnahmepuffer") multipliziert `withdrawal_years` direkt mit dem Pro-Schritt-Cashflow-Betrag eines einzelnen Schritts (`e_val`/`i_val`) – korrekt nur, wenn ein Schritt exakt einem Jahr entspricht.

**Warum das ein echtes Problem ist, nicht nur Theorie**: `Timeline.steps_per_year` hat den **Default 12** (Monatsschritte) – exakt umgekehrt zu dem, was jeder tatsächlich existierende Finance-Plan im Repository verwendet (Plan `ralf`: 50 Jahresschritte; das End-to-End-Testprofil "Anna" in `tests/test_mcp/test_finance_tools_e2e.py`: 70 Jahresschritte, Kommentar "yearly steps"). Ein Agent, der `core_create_plan` ohne explizites `steps_per_year=1` aufruft (der naheliegende, nicht dokumentierte Normalfall für Altersvorsorge-Pläne) und anschließend `finance_set_life_phases`/`finance_add_statutory_pension`/`finance_add_cash_bucket` verwendet, bekäme **falsche** Phasengrenzen, Renten-Anpassungsfaktoren und Cash-Bucket-Zielgrößen – bei gleichzeitig **korrekt** umgerechneten Cashflow-Beträgen (durch den bereits gefixten Bug). Diese Inkonsistenz zwischen Bausteinen desselben Feature-Moduls ist selbst eine neue Fehlerquelle.

**Welches Verhalten wird angestrebt?**: Jeder Baustein, der Alter/Jahre in Schritte umrechnet (oder umgekehrt), tut das relativ zu `plan.timeline.steps_per_year` statt einer impliziten Konstante. Die beiden zustandslosen `calculations_*`-Tools (`step_to_age`/`age_to_step`, ohne Plan-Zugriff) erhalten stattdessen einen expliziten `steps_per_year`-Parameter mit Default `1` (heutiges Verhalten bleibt Standard, ein Agent kann für einen abweichenden Plan den tatsächlichen Wert übergeben).

---

## 2. Architektur & Betroffene Komponenten

- **`src/compute_to_ai/features/calculations/dates.py`** [MODIFY]: `step_to_age`/`age_to_step` erhalten `steps_per_year: int = 1`.
- **`src/compute_to_ai/features/finance/phases.py`** [MODIFY]: `build_standard_life_phases` erhält `steps_per_year: int = 1` (Default bewusst **1**, nicht 12 – siehe Abschnitt 4/Edge-Cases, dies ist die einzige Stelle, an der ein von `Timeline`s Default abweichender Default fachlich richtig ist, weil Lebensphasen-Pläne in diesem Projekt durchgängig Jahresschritte verwenden, siehe `Docs/05-Feature-Finanzen-Parameter.md`).
- **`src/compute_to_ai/mcp/tools/finance/_phase.py`** [MODIFY]: `finance_set_life_phases` liest `plan.timeline.steps_per_year` und reicht es an `build_standard_life_phases` durch (Plan ist hier schon geladen, kein zusätzlicher Parameter für den Agenten nötig).
- **`src/compute_to_ai/features/finance/pension.py`** [MODIFY]: `add_statutory_pension` nutzt `plan.timeline.steps_per_year` statt der festen `* 12`-Umrechnung.
- **`src/compute_to_ai/features/finance/portfolio.py`** [MODIFY]: `_calculate_withdrawal_buffer`/`CashBucketParameters` – Entnahmepuffer-Formel um `steps_per_year` ergänzen, da `e_val`/`i_val` sonst nur für Jahresschritt-Pläne korrekt sind. `add_cash_bucket` liest `plan.timeline.steps_per_year`.
- **`src/compute_to_ai/mcp/tools/calculation_tools.py`** [MODIFY, ggf. keine Änderung nötig]: Registrierung von `step_to_age`/`age_to_step` bleibt gleich (neuer Parameter mit Default wird automatisch Teil des MCP-Schemas).
- **Betroffene Tests**: `tests/test_features/test_calculations/test_dates.py`, `tests/test_features/test_finance/test_life_phases_harmonies.py` (bzw. das tatsächliche Testmodul für `phases.py`), `tests/test_features/test_finance/test_pension.py`, `tests/test_features/test_finance/test_portfolio.py`.

---

## 3. Konkrete Code-Anhaltspunkte & Signaturen

```python
# features/calculations/dates.py
def step_to_age(step: int, current_age: int, steps_per_year: int = 1) -> float:
    """Age at a given simulation step, given step 0 == current_age.

    `steps_per_year` makes the conversion explicit instead of assuming a
    fixed one-step-one-year cadence (see Timeline.steps_per_year,
    Docs/01-Kern-Domaenenmodell.md, "Zeitstrahl").
    """
    if step < 0:
        msg = f"step must be >= 0, got {step}"
        raise ValueError(msg)
    return current_age + step / steps_per_year


def age_to_step(age: float, current_age: int, steps_per_year: int = 1) -> int:
    if age < current_age:
        msg = f"age {age} is before current_age {current_age}"
        raise ValueError(msg)
    return round((age - current_age) * steps_per_year)
```

```python
# features/finance/phases.py
def build_standard_life_phases(
    current_age: int,
    employment_end_age: int,
    statutory_pension_start_age: int,
    life_expectancy_age: int,
    education_end_age: int | None = None,
    steps_per_year: int = 1,
    ...
) -> list[Phase]:
    ...
    employment_end_step = (employment_end_age - current_age) * steps_per_year
    ...
```

```python
# features/finance/pension.py, add_statutory_pension
def add_statutory_pension(plan: Plan, name: str, store_name: str, ..., regular_retirement_step: int, actual_retirement_step: int, ...) -> None:
    months_per_step = 12.0 / plan.timeline.steps_per_year
    months_early = max(0, regular_retirement_step - actual_retirement_step) * months_per_step
    months_late = max(0, actual_retirement_step - regular_retirement_step) * months_per_step
    ...
```

Für den Cash-Bucket-Entnahmepuffer: `e_val`/`i_val` sind Beträge **eines einzelnen Schritts**; `withdrawal_years` ist Jahre. Die Formel muss die Anzahl der Schritte pro Jahr einbeziehen, damit `withdrawal_years * dependency * e_val` weiterhin "N Jahre erwarteter Ausgaben" bedeutet statt "N Schritte":
```python
annual_e_val = e_val * plan.timeline.steps_per_year
return withdrawal_years * dependency * annual_e_val
```
(Exakte Herleitung/Edge-Cases dem Ausführungs-Agenten überlassen – `_calculate_withdrawal_buffer` und ihr Golden-Test in `test_portfolio.py` sind die Quelle der Wahrheit für das bisherige, für Jahresschritte korrekte Verhalten; die Änderung darf das für `steps_per_year=1` bestehende Ergebnis nicht verändern.)

---

## 4. Test-Strategie & Edge Cases

- **Happy Path / Regression**: Alle bestehenden Tests mit (implizitem) `steps_per_year=1` liefern identische Ergebnisse wie vorher (kein Verhaltensbruch für den heute einzig genutzten Fall).
- **Neuer Fall – Monatsschritt-Plan**: Ein Plan mit `steps_per_year=12` und `finance_set_life_phases(current_age=30, employment_end_age=67, ...)` erzeugt Phasengrenzen in **Monatsschritten** (`employment_end_step == (67-30)*12 == 444`), nicht in Jahresschritten.
- **`calculations_step_to_age`/`calculations_age_to_step`**: Test mit `steps_per_year=12` liefert für `step=12` ein Alter von `current_age + 1`, nicht `current_age + 12`.
- **`add_statutory_pension`**: Test mit `steps_per_year=12`, `regular_retirement_step`/`actual_retirement_step` als Monats-Schritte, korrekter `months_early`/`months_late`-Wert (keine Verzwölffachung).
- **Edge Case**: `steps_per_year=1` (unverändertes Verhalten) explizit als Regressionstest, nicht nur implizit über bestehende Tests.
- **Kommando**: `pytest tests/test_features/test_calculations/ tests/test_features/test_finance/ -v`

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [ ] Alle Steps in diesem Task-Ordner sind grün ausgeführt.
- [ ] Kein bestehender Test (insbesondere `ralf`-artige Jahresschritt-Szenarien, `test_frequency_effects.py`) ändert sein Ergebnis.
- [ ] Neue Tests für `steps_per_year != 1` bestehen für `dates.py`, `phases.py`, `pension.py`, Cash-Bucket-Entnahmepuffer.
- [ ] `ruff check` und `pyright` ohne neue Warnungen.
- [ ] Doku aktualisiert: `Docs/01-Kern-Domaenenmodell.md` (Zeitstrahl-Abschnitt, bereits um `steps_per_year` ergänzt, hier um Verweis auf Alters-/Renten-/Cash-Bucket-Bausteine erweitern), `Docs/05-Feature-Finanzen-Parameter.md` (Lebensphasen).
- [ ] `review.md` erstellt und gegengezeichnet.
- [ ] `Docs/10-Roadmap.md` Epic 4.19 abgehakt `[x]`.
