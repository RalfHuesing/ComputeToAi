# Konzept: Task 4.17 – Golden-Tests für Fehlkonfigurationen & Audit-Warnungen

**Status**: READY  
**Epic / Meilenstein**: Meilenstein 4 – Epic 4.17  
**Erstellt am**: 2026-07-21  

---

## 1. Intention & Fachlicher Kontext

**Wissenschaftlich-fachliche Motivation**:
Die bisherige Testsuite prüfte primär valide, vollständig konfigurierte Pläne ("Happy Path"). Systematischer Schutz vor stillen Fehlern in der Finanzberatung erfordert jedoch automatisierte **Golden-Tests für Fehlkonfigurationen**. Diese provizieren unvollständige Annahmen und weisen nach, dass das System verlässlich mit strukturierten Warnungen/Fehlern reagiert, anstatt stumm plausible, aber falsche Zahlen zu liefern.

---

## 2. Architektur & Betroffene Komponenten

- **`tests/test_features/test_finance/test_misconfiguration_golden.py`** [NEW]:
  Dedizierte Testsuite für Fehlkonfigurationen, fehlende Ruin-Speicher, implizite Korrelationen und Cache-Grenzfälle.

---

## 3. Konkreter Code-Anhaltspunkte & Signaturen

```python
# test_misconfiguration_golden.py

def test_missing_ruin_stores_warning():
    ...

def test_implicit_correlation_warning():
    ...

def test_cache_invalidation_on_plan_mutation():
    ...
```

---

## 4. Test-Strategie & Edge Cases (Mandatory)

### Happy Path:
- Alle Fehlkonfigurations-Szenarien werden von den Pre-Flight- und Audit-Systemen gefangen und mit korrekten Schweregraden (`CRITICAL_CONFIG_MISSING`, `WARNING`) ausgewiesen.

### Edge Cases:
- Plan ohne `ruin_stores` darf NIEMALS `ruin_probability: 0.0` zurückgeben.
- Verändertes Plan-Attribut muss beim nächsten `get_monte_carlo_result`-Aufruf ein frisches Ergebnis erzwingen.

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [ ] Steps (`01-step-golden-tests-fehlende-ruin-stores.md`, `02-step-golden-tests-implizite-korrelation-und-cache.md`) umgesetzt.
- [ ] Golden-Testsuite ist zu 100 % grün (`pytest`).
- [ ] `review.md` gegengezeichnet.
- [ ] `Docs/10-Roadmap.md` abgehakt `[x]` (Meilenstein 4 ist damit vollständig auf Task-Ebene abgesichert!).
