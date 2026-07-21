# Step 1: Engine-Erweiterung für Intervall-Effekte

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.11-frequenz-und-intervall-ausgaben/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Erweiterung der domänenneutralen Kern-Engine (`BaseEffect` und Unterklassen in `src/compute_to_ai/engine/effect.py`), um Intervall-Schrittweiten (`interval_steps`) und Erstauftritts-Schritte (`first_occurrence_step`) nativ zu unterstützen.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/engine/effect.py`
- [ ] [NEW] `tests/test_engine/test_interval_effects.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# src/compute_to_ai/engine/effect.py

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

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_engine/test_interval_effects.py -v
```

### Abzudeckende Testfälle:
- **Happy Path**: Effekt mit `interval_steps = 12` ist nur in Schritten 0, 12, 24, 36 aktiv.
- **Edge Cases**:
  - `first_occurrence_step = 3`, `interval_steps = 6` -> aktiv in 3, 9, 15, 21.
  - Kombiniert mit `start_step` und `end_step`.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/01-Kern-Domaenenmodell.md` (Abschnitt Effekte & Intervall-Schrittweite) aktualisieren.
