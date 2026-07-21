# Konzept: Task 4.14 – Zentrale Parameter- & Raten-Registry (Single Source of Truth)

**Status**: DONE  
**Epic / Meilenstein**: Meilenstein 4 – Epic 4.14  
**Erstellt am**: 2026-07-21  

---

## 1. Intention & Fachlicher Kontext

**Problem**: Derzeit sind Inflations- und Steigerungsraten (`growth_rate`, `inflation_rate`) als fixe Zahlenliterale (z. B. `0.02`) an Dutzenden einzelnen Effekten hinterlegt. Ändert sich eine makroökonomische Grundannahme (z.B. Inflationserwartung von 2,0 % auf 2,5 % oder der Geldmarktzins), müssen Dutzende Effekte einzeln angepasst werden.

**Wissenschaftlich-fachliche Lösung**:
- **Zentrale Parameter-Registry auf Plan-Ebene**: `plan.parameters: dict[str, float]` speichert zentrale Makro-Parameter (z. B. `{"inflation_general": 0.02, "gehalt_growth": 0.02, "zins_geldmarkt": 0.025}`).
- **Referenzierung per Key**: Effekte akzeptieren bei Raten entweder ein Float-Literal (`0.02`) oder einen Referenz-Key (z. B. `"ref:inflation_general"`), der zur Laufzeit dynamisch aufgelöst wird.
- **Ein-Klick-Anpassung**: Über MCP-Tools kann ein Parameter zentral geändert werden; alle verknüpften Effekte in der Simulation reagieren sofort.

---

## 2. Architektur & Betroffene Komponenten

- **`src/compute_to_ai/engine/plan.py`** [MODIFY]:
  `Plan` erhält das Feld `parameters: dict[str, float] = Field(default_factory=dict)`.
- **`src/compute_to_ai/engine/effect.py`** [MODIFY]:
  `GrowingFixedEffect` und `PercentageGrowthEffect` auflösen Raten über `plan.get_parameter(rate)` auf, wenn ein String übergeben wird.
- **`src/compute_to_ai/mcp/finance_tools.py`** [MODIFY]:
  Neues MCP-Tool `finance_set_plan_parameter(plan_name, key, value)` und `finance_get_plan_parameters(plan_name)`.
- **`tests/test_engine/test_parameter_registry.py`** [NEW]:
  Tests für Referenz-Auflösung, Fallback-Verhalten und dynamische Parameteränderungen.

---

## 3. Konkrete Code-Anhaltspunkte & Signaturen

```python
# engine/plan.py
class Plan:
    parameters: dict[str, float] = Field(default_factory=dict)

    def get_parameter_value(self, val: float | str) -> float:
        if isinstance(val, str) and val.startswith("ref:"):
            param_key = val[4:]
            if param_key not in self.parameters:
                raise ValueError(f"Parameter '{param_key}' not found in plan parameters.")
            return self.parameters[param_key]
        return float(val)
```

---

## 4. Test-Strategie & Edge Cases (Mandatory)

### Happy Path:
- 10 Effekte referenzieren `"ref:inflation_general"`. Eine Anpassung des Parameters von `0.02` auf `0.03` aktualisiert alle 10 Effekte in der nächsten Simulation automatisch.

### Edge Cases:
- **Ungültige Referenz**: Referenz auf einen nicht existierenden Key wirft einen klaren `ValueError` mit Schlüsselnamen.
- **Rückwärtskompatibilität**: Direkte Float-Werte (`0.02`) funktionieren weiterhin uneingeschränkt.

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [ ] Steps (`01-step-engine-plan-parameters.md`, `02-step-referenz-aufloesung-in-effekten.md`, `03-step-mcp-tools-parameter-pflege.md`) ausgeführt.
- [ ] Pytest-Suite grün.
- [ ] Doku in `Docs/01-Kern-Domaenenmodell.md` & `Docs/02-Architektur-und-MCP.md` aktualisiert.
- [ ] `review.md` gegengezeichnet.
- [ ] `Docs/10-Roadmap.md` abgehakt `[x]`.
