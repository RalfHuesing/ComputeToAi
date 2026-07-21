# Konzept: Task 4.12 – Refactoring & Plan-Audit-Bereinigungen

**Status**: DONE  
**Epic / Meilenstein**: Meilenstein 4 – Epic 4.12  
**Erstellt am**: 2026-07-21  

---

## 1. Intention & Fachlicher Kontext

Dieser Task bereinigt logische Grenzfall-Fehler und Altlasten im Plan-Modell und Pfad-Audit, die im praktischen Testbetrieb auffällig wurden:

1. **Rentenübergang Off-By-One**: Im Schritt des Erwerbsendes (Step 20) überschneiden sich Gehalt und Rente, was zu doppelten Einnahmen im Übergangsjahr führte.
2. **Timeline vs. Phasen-Ende (Step 43 vs 49)**: Lebensphasen endeten bei Alter 90 (Step 43), während die Timeline bis Step 49 lief. Dadurch fiel nach Step 43 der Notgroschen des Cash-Buckets fälschlich auf 0 €.
3. **Altlasten-Cleanup**: Entfernung ungenutzter Rebalancing-Effekte und Bereinigung/Dokumentation verwaister Platzhalter-Speicher.

---

## 2. Architektur & Betroffene Komponenten

- **`src/compute_to_ai/features/finance/life_phases.py`** [MODIFY]:
  Korrektur der Phasenberechnung (`build_standard_life_phases`), damit Erwerbsphase bei `N-1` endet und Rentenphase bei `N` beginnt. Die letzte Phase erstreckt sich stets bis zum Ende der Timeline.
- **`examples/ralf/plan.json` & `examples/anna/plan.json`** [MODIFY]:
  Harmonisierung der Phasengrenzen in den Beispielszenarien.
- **`src/compute_to_ai/features/finance/portfolio.py`** [MODIFY]:
  Entfernung veralteter Rebalancing-Platzhalter.
- **`tests/test_features/test_finance/`** [MODIFY/NEW]:
  Anpassung bestehender Audit-Tests und neue Tests für saubere Phasenübergänge.

---

## 3. Konkrete Code-Anhaltspunkte & Signaturen

```python
# life_phases.py
def build_standard_life_phases(
    birth_year: int,
    retirement_age: int,
    end_age: int,
    timeline_steps: int
) -> list[Phase]:
    # Ensure pension phase end_step matches timeline_steps - 1
    ...
```

---

## 4. Test-Strategie & Edge Cases (Mandatory)

### Happy Path:
- `finance_audit_plan` meldet im Übergangsjahr **keine** doppelte Einnahmen-Warnung mehr.
- Der Cash-Bucket behält sein Zielguthaben bis zum allerletzten Schritt der Timeline.

### Edge Cases:
- Phasenübergänge bei variablen Zeitschrittlängen.
- Pläne mit exakt 0 Jahren Frühruhestand vs. Pläne mit Frühruhestandslücke.

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [x] Steps (`01-step-rentenuebergang-off-by-one.md`, `02-step-timeline-phasen-harmonisierung.md`, `03-step-alt-stores-und-rebalancing-cleanup.md`) ausgeführt.
- [x] Pytest-Suite grün.
- [x] Living Documentation in `Docs/04-Feature-Finanzen-Methodik.md` aktualisiert.
- [x] `review.md` gegengezeichnet.
- [x] `Docs/10-Roadmap.md` abgehakt `[x]`.
