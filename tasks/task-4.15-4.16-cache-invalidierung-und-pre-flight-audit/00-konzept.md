# Konzept: Task 4.15 & 4.16 – Strikte Cache-Invalidierung & Pre-Flight Konfigurations-Audit

**Status**: READY  
**Epic / Meilenstein**: Meilenstein 4 – Epics 4.15 & 4.16  
**Erstellt am**: 2026-07-21  

---

## 1. Intention & Fachlicher Kontext

**Wissenschaftliche & fachliche Notwendigkeit**:
1. **Strikte Cache-Invalidierung (Epic 4.15)**: Stellt sicher, dass Monte-Carlo- und Pfad-Audit-Ergebnisse deterministisch an den genauen Content-Hash des `Plan`-Objekts gebunden sind. Jede Planmutation (`add_*`, `set_*`, `remove_*`) invalidiert den Cache automatisch. Veraltete Simulationszahlen werden unmöglich gemacht.
2. **Pre-Flight Konfigurations-Audit (Epic 4.16)**: Verhindert, dass das System auf unvollständigen Plänen stumm plausible, aber sachlich falsche Zahlen liefert:
   - Fehlt `ruin_stores`, gibt das System `ruin_probability: null` und Status `"UNCONFIGURED"` zurück, statt irreführend `0.0 %` vorzugaukeln.
   - Implizite Korrelation 0.0 bei stochastischen Effekten ohne Matrix wird als deutliche Warnung ausgewiesen.
   - Fehlender Cash-Bucket oder unberührte Speicher werden vor Ausführung gewarnt (`CRITICAL_CONFIG_MISSING`, `WARNING`, `INFO`).

---

## 2. Architektur & Betroffene Komponenten

- **`src/compute_to_ai/engine/plan.py`** [MODIFY]:
  Implementierung von `compute_content_hash(plan: Plan) -> str` (SHA-256 über alle serialisierten Komponenten).
- **`src/compute_to_ai/features/finance/cache.py`** [MODIFY]:
  Anbindung des Caches an den Content-Hash.
- **`src/compute_to_ai/features/finance/preflight.py`** [NEW]:
  Pre-Flight Prüfer `run_preflight_audit(plan: Plan) -> PreflightAuditResult`.
- **`src/compute_to_ai/mcp/finance_tools.py`** [MODIFY]:
  Integration der Pre-Flight Prüfungen vor `finance_run_monte_carlo` und `core_run_simulation`.
- **`tests/test_features/test_finance/test_preflight_and_cache.py`** [NEW]:
  Umfassende Tests für Content-Hashing, Cache-Clearing und Pre-Flight Warnungen.

---

## 3. Konkrete Code-Anhaltspunkte & Signaturen

```python
# preflight.py
class Severity(Enum):
    CRITICAL_CONFIG_MISSING = "CRITICAL_CONFIG_MISSING"
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass
class PreflightIssue:
    severity: Severity
    code: str
    message: str

def run_preflight_audit(plan: Plan) -> list[PreflightIssue]:
    ...
```

---

## 4. Test-Strategie & Edge Cases (Mandatory)

### Happy Path:
- Nach Planänderung gibt `finance_get_monte_carlo_result` nachweislich neu berechnete Ergebnisse zurück.
- Vollständig konfigurierter Plan durchläuft Pre-Flight Audit ohne Warnungen.

### Edge Cases:
- Plan ohne `ruin_stores` liefert `ruin_probability: null` + `CRITICAL_CONFIG_MISSING`.
- Plan mit stochastischen Effekten ohne Korrelationsmatrix gibt `WARNING` ("Implicit 0.0 correlation").

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [ ] Steps (`01-step-plan-content-hashing-und-cache.md`, `02-step-pre-flight-konfigurations-audit.md`, `03-step-mcp-integration-und-warnungssystem.md`) ausgeführt.
- [ ] Pytest-Suite grün.
- [ ] Doku in `Docs/01-Kern-Domaenenmodell.md` & `Docs/04-Feature-Finanzen-Methodik.md` aktualisiert.
- [ ] `review.md` gegengezeichnet.
- [ ] `Docs/10-Roadmap.md` abgehakt `[x]`.
