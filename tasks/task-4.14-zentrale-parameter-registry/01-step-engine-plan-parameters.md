# Step 1: Engine-Erweiterung für Plan-Parameter

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.14-zentrale-parameter-registry/00-konzept.md)  
**Status**: DONE  

---

## 1. Step-Intention
Erweiterung des `Plan`-Modells (`src/compute_to_ai/engine/plan.py`) um das Feld `parameters: dict[str, float]` und Hilfsmethoden zum Abrufen und Aktualisieren von Parametern.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/engine/plan.py`
- [ ] [NEW] `tests/test_engine/test_parameter_registry.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# engine/plan.py

class Plan:
    parameters: dict[str, float] = Field(default_factory=dict)

    def set_parameter(self, key: str, value: float) -> None:
        self.parameters[key] = float(value)

    def resolve_rate(self, rate: float | str) -> float:
        if isinstance(rate, str) and rate.startswith("ref:"):
            key = rate[4:]
            if key not in self.parameters:
                raise ValueError(f"Plan parameter '{key}' is not defined.")
            return self.parameters[key]
        return float(rate)
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_engine/test_parameter_registry.py -v
```

### Abzudeckende Testfälle:
- Parameter setzen und auflösen.
- Nicht existierende Referenz wirft `ValueError`.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/01-Kern-Domaenenmodell.md` (Abschnitt Plan-Parameter) aktualisieren.
