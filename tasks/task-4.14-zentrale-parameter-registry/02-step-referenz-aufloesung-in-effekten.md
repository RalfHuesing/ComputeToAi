# Step 2: Referenz-Auflösung in Effekten

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.14-zentrale-parameter-registry/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Anpassung aller Effekt-Klassen (`GrowingFixedEffect`, `PercentageGrowthEffect`, etc. in `src/compute_to_ai/engine/effect.py`), um Raten-Parameter sowohl als Float als auch als Referenz-String (`"ref:key"`) zu akzeptieren und während der Simulation dynamisch über den Plan aufzulösen.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/engine/effect.py`
- [ ] [MODIFY] `tests/test_engine/test_parameter_registry.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# engine/effect.py

class GrowingFixedEffect(BaseEffect):
    growth_rate: float | str = 0.0

    def apply(self, plan: Plan, step: int) -> None:
        effective_rate = plan.resolve_rate(self.growth_rate)
        # Simulation verwendet effective_rate
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_engine/test_parameter_registry.py -k test_effect_parameter_resolution -v
```

### Abzudeckende Testfälle:
- Dynamische Anpassung des Parameters verändert die Simulationsergebnisse aller verknüpften Effekte.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/01-Kern-Domaenenmodell.md` aktualisieren.
