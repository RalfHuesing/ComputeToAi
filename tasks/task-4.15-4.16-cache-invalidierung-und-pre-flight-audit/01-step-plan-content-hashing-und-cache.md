# Step 1: Plan Content-Hashing & Strikte Cache-Invalidierung

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.15-4.16-cache-invalidierung-und-pre-flight-audit/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Implementierung von deterministischem SHA-256 Content-Hashing für `Plan`-Objekte und strikte automatische Cache-Invalidierung bei jeder Planänderung.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [MODIFY] `src/compute_to_ai/engine/plan.py`
- [ ] [MODIFY] `src/compute_to_ai/features/finance/plan_storage.py`
- [ ] [NEW] `tests/test_features/test_finance/test_cache_invalidation.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# engine/plan.py

import hashlib
import json

def compute_plan_content_hash(plan: Plan) -> str:
    """Computes a deterministic SHA-256 hash of the entire plan state."""
    raw_json = plan.model_dump_json(by_alias=True)
    return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_cache_invalidation.py -v
```

### Abzudeckende Testfälle:
- Jede Attributsänderung an Store, Effect, Phase oder Parameter verändert den Content-Hash.
- Veralteter Cache wird bei verändertem Content-Hash verworfen.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/01-Kern-Domaenenmodell.md` (Abschnitt Cache-Hashing) aktualisieren.
