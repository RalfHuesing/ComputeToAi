# Konzept: Task 4.11 – Frequenz- & Intervall-Ausgaben (Periodische Dauer- & Turnusausgaben)

**Status**: DONE  
**Epic / Meilenstein**: Meilenstein 4 – Epic 4.11  
**Erstellt am**: 2026-07-21  

---

## 1. Intention & Fachlicher Kontext

In der Lebensplanung fallen Ausgaben und Einnahmen in unterschiedlichen Frequenzen an:
- **Monatlich**: Miete, Gehalt, Lebensmittel
- **Quartalsweise**: Nebenkostenabschläge, manche Versicherungen
- **Jährlich**: KFZ-Steuer, Gebäudeversicherung, Urlaub
- **Mehrjährig (Turnus)**: Auto-Neuanschaffung alle 5 Jahre, Dachsanierung alle 20 Jahre

**Fachliches Prinzip**: Statt mehrjährige Turnusausgaben auf Monatsbeträge umzurechnen (was Liquiditätsspitzen/Cash-Bucket-Bedarfe verschleiern würde), muss die Simulations-Engine Ausgaben exakt in den Zeitschritten wirksam werden lassen, in denen sie tatsächlich anfallen.

---

## 2. Architektur & Betroffene Komponenten

- **`src/compute_to_ai/engine/effect.py`** [MODIFY]:
  `BaseEffect` (und alle Unterklassen) erhält `interval_steps: int = 1` und `first_occurrence_step: int = 0`.
- **`src/compute_to_ai/features/finance/cashflow.py`** [MODIFY]:
  `add_expense` und `add_income_stream` unterstützen `frequency` (`"monthly"`, `"quarterly"`, `"yearly"`, `"every_n_years"` mit `interval_years`).
- **`src/compute_to_ai/mcp/finance_tools.py`** [MODIFY]:
  MCP-Tools unterstützen Frequenz- und Intervall-Parameter.
- **`tests/test_features/test_finance/test_frequency_effects.py`** [NEW]:
  Tests für periodische Cashflows, Inflationsberechnung und Cash-Bucket-Reaktionen.

---

## 3. Konkrete Code-Anhaltspunkte & Signaturen

```python
# engine/effect.py
class BaseEffect:
    interval_steps: int = 1
    first_occurrence_step: int = 0

    def is_active_at_step(self, step: int) -> bool:
        if step < self.first_occurrence_step:
            return False
        if self.start_step is not None and step < self.start_step:
            return False
        if self.end_step is not None and step > self.end_step:
            return False
        return (step - self.first_occurrence_step) % self.interval_steps == 0
```

---

## 4. Test-Strategie & Edge Cases (Mandatory)

### Happy Path:
- Eine jährliche Ausgabe von 1.200 € verringert den Cash-Bucket nur in den Schritten 0, 12, 24, 36... um den inflationsbereinigten Jahresbetrag.

### Edge Cases (Wissenschaftlich & fachlich fundiert):
- **Off-Phase Start (`first_occurrence_step > 0`)**: Eine Turnusausgabe startet erst in Schritt 5 und wiederholt sich alle 12 Schritte (5, 17, 29...).
- **Wachstum bei Intervall-Effekten**: Die Steigerung/Inflation berechnet sich dynamisch zum Zeitpunkt `step` (`(1 + r)^step`), nicht erst pro Anfall.
- **Phasengrenzen**: Turnusausgaben stoppen sofort, wenn das Schritt-Intervall die Phasengrenze überschreitet.

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [ ] Steps (`01-step-engine-intervall-effekte.md`, `02-step-finance-frequenz-bausteine.md`, `03-step-mcp-und-pfad-audit.md`) umgesetzt.
- [ ] Tests grün (`pytest tests/test_features/test_finance/test_frequency_effects.py`).
- [ ] Living Documentation in `Docs/01-Kern-Domaenenmodell.md` & `Docs/04-Feature-Finanzen-Methodik.md` aktualisiert.
- [ ] `review.md` gegengezeichnet.
- [ ] `Docs/10-Roadmap.md` abgehakt `[x]`.
