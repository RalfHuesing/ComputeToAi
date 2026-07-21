# Step 1: Wissensspeicher Datenmodell & Dateiverwaltung (`knowledge.json`)

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-5.1-5.2-wissensspeicher-und-profile-tools/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Implementierung der Pydantic-Modelle `FactItem` und `KnowledgeStore` in `src/compute_to_ai/features/finance/knowledge_store.py` sowie der JSON-Persistence im Plan-Ordner (`knowledge.json`).

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [NEW] `src/compute_to_ai/features/finance/knowledge_store.py`
- [ ] [NEW] `tests/test_features/test_finance/test_knowledge_store.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```python
# knowledge_store.py

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class FactSource(str, Enum):
    USER_EXPLICIT = "user_explicit"
    AGENT_INFERRED = "agent_inferred"
    SYSTEM_IMPORT = "system_import"

class FactItem(BaseModel):
    key: str
    value: Any
    category: str = "general"
    description: str | None = None
    source: FactSource = FactSource.USER_EXPLICIT
    updated_at: str

class KnowledgeStore(BaseModel):
    owner: str | None = None
    facts: dict[str, FactItem] = Field(default_factory=dict)
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_knowledge_store.py -v
```

### Abzudeckende Testfälle:
- Serialisierung und Deserialisierung von `knowledge.json`.
- Handhabung belieber Datentypen im `value`-Feld.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/02-Architektur-und-MCP.md` (Abschnitt Wissensspeicher) aktualisieren.
