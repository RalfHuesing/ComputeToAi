# Konzept: Task 4.13 – Graduelle Kapitalsicherung vor bekannten Entnahmen (De-Risking Glidepath)

**Status**: READY  
**Epic / Meilenstein**: Meilenstein 4 – Epic 4.13  
**Erstellt am**: 2026-07-21  

---

## 1. Intention & Fachlicher Kontext

**Problem**: Sowohl beim Renteneintritt als auch bei geplanten Großanschaffungen (z. B. Autokauf in 5 Jahren) wird derzeit mendantenweit das benötigte Kapital abrupt am Stichtag aus dem Depot entnommen. Fällt dieser Zeitpunkt mit einem Börseneinbruch zusammen, müssen Aktien mit Verlusten realisiert werden (Sequence-of-Returns-Risiko).

**Wissenschaftlich-fachliche Lösung**:
- **Graduelle De-Risking-Rampe (Glidepath)**: Vor bekannten Großentnahmen oder Phasenwechseln (z. B. Erwerb → Rente) wird das Entnahmeziel über einen konfigurierbaren Vorlaufzeitraum (z. B. 36 Monate) linear aufgebaut.
- **Vorteil**: Umschichtungen aus risikobehafteten Aktien in sichere Liquidität/Cash-Bucket geschehen sukzessive im Vorfeld und glätten Marktschwankungen.

---

## 2. Architektur & Betroffene Komponenten

- **`src/compute_to_ai/features/finance/portfolio.py`** [MODIFY]:
  `CashBucketParameters` erhält den Parameter `glidepath_steps: int = 0`. `cash_bucket_manager_func` interpoliert die Zielgröße des Entnahmepuffers linear über die `glidepath_steps` vor einem Phasenwechsel.
- **`src/compute_to_ai/features/finance/cashflow.py`** [MODIFY]:
  Vereinheitlichung von `fixed_acquisition` und `flexible_acquisition` für stichtagsgenaue Anschaffungen mit De-Risking-Rampe.
- **`tests/test_features/test_finance/test_glidepath.py`** [NEW]:
  Golden-Test: Cash-Bucket-Zielgröße wächst nachweisbar linear über die Monate vor dem Renteneintritt.

---

## 3. Konkrete Code-Anhaltspunkte & Signaturen

```python
# portfolio.py
class CashBucketParameters:
    emergency_buffer_months: float
    glidepath_steps: int = 36  # 3 Jahre Vorlauf vor Phasenwechsel

# Lineare Interpolation vor Phasenwechsel:
# current_target = base_target + fraction * (future_target - base_target)
```

---

## 4. Test-Strategie & Edge Cases (Mandatory)

### Happy Path:
- 36 Schritte vor dem Renteneintritt beginnt das Cash-Bucket-Ziel linear anzusteigen und erreicht exakt zum Renteneintritt 100% der neuen Notgroschen-/Entnahme-Zielgröße.

### Edge Cases:
- Phasenwechsel kürzer als `glidepath_steps` (Rampe verkürzt sich dynamisch auf verbleibende Schritte).
- Markteinbruch während der Rampe: Verkauf erfolgt verteilt über 36 Monate statt in einer großen Einzelsumme.

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [ ] Steps (`01-step-cash-bucket-glidepath.md`, `02-step-anschaffungen-glidepath-migration.md`, `03-step-golden-tests-de-risking.md`) umgesetzt.
- [ ] Tests in `test_glidepath.py` grün.
- [ ] Doku in `Docs/04-Feature-Finanzen-Methodik.md` aktualisiert.
- [ ] `review.md` gegengezeichnet.
- [ ] `Docs/10-Roadmap.md` abgehakt `[x]`.
