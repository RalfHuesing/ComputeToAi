# Konzept: Task 6.1–6.3 – Regelwerk-Templates & Versionierung

**Status**: READY  
**Epic / Meilenstein**: Meilenstein 6 – Epics 6.1, 6.2 & 6.3  
**Erstellt am**: 2026-07-21  

---

## 1. Intention & Fachlicher Kontext

**Wissenschaftlich-fachliche Motivation**:
1. **Versionierte Steuerrechts-Templates (Epic 6.1)**: Steuerrechtliche Parameter (z. B. Sparerpauschbetrag, Vorabpauschalen-Basiszins, Teilfreistellungssätze) dürfen nicht hart im Code stehen, sondern werden über versionierte JSON-Templates (z. B. `de_tax_2024.json`, `de_tax_2025.json`) geladen.
2. **Bestandsschutz-Konsistenz (Epic 6.2)**: Wird ein Plan auf ein neues Steuerjahr-Template aktualisiert, behalten bestehende Lots ihre geschützten Regelwerk-Versionen (`lot.rule_version`). Dies garantiert historische Rechtskonformität.
3. **Vertrauens- & Prüfmechanismus (Epic 6.3)**: Templates enthalten Prüfsummen und Schema-Validierungen. Vor der Aktivierung in einem Plan liefert ein Diff-Tool die exakten Abweichungen zum aktuellen Regelwerk.

---

## 2. Architektur & Betroffene Komponenten

- **`src/compute_to_ai/features/finance/tax_templates.py`** [NEW]:
  Modelle `TaxRulesTemplate`, Loader und Validator.
- **`src/compute_to_ai/features/finance/tax.py`** [MODIFY]:
  Steuer-Effekte nutzen dynamisch das geladene `TaxRulesTemplate`.
- **`src/compute_to_ai/mcp/finance_tools.py`** [MODIFY]:
  MCP-Tools `finance_list_tax_templates`, `finance_apply_tax_template`, `finance_diff_tax_templates`.
- **`tests/test_features/test_finance/test_tax_templates.py`** [NEW]:
  Tests für Template-Loading, Bestandsschutz-Wechsel und Diff-Vorschau.

---

## 3. Konkrete Code-Anhaltspunkte & Signaturen

```python
# tax_templates.py

class TaxRulesTemplate(BaseModel):
    template_id: str  # z.B. "de_tax_2024"
    valid_from_year: int
    savers_allowance: float  # 1000.0
    capital_gains_tax_rate: float  # 0.25
    soli_rate: float  # 0.055
    partial_exemptions: dict[str, float]  # {"equity_fund": 0.30}
    checksum: str
```

---

## 4. Test-Strategie & Edge Cases (Mandatory)

### Happy Path:
- Template-Wechsel von `de_tax_2023` auf `de_tax_2024` aktualisiert Freibeträge für neue Lots, während Vor-2009-Lots ihren vollen Bestandsschutz behalten.

### Edge Cases:
- Manipuliertes oder ungültiges Template wird bei der Schema- / Checksummen-Prüfung abgelehnt.
- Fehlendes Template im System wirft verständlichen Fehler mit verfuegbaren Versionen.

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [ ] Steps (`01-step-regelwerk-template-format-und-lader.md`, `02-step-bestandsschutz-konsistenz-bei-wechsel.md`, `03-step-vertrauens-und-pruefmechanismus.md`) umgesetzt.
- [ ] Pytest-Suite grün.
- [ ] Doku in `Docs/03-Feature-Finanzen-Domaenenmodell.md` & `Docs/05-Feature-Finanzen-Parameter.md` aktualisiert.
- [ ] `review.md` gegengezeichnet.
- [ ] `Docs/10-Roadmap.md` abgehakt `[x]`.
