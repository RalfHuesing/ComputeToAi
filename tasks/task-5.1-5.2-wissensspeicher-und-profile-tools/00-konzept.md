# Konzept: Task 5.1 & 5.2 – Wissensspeicher & Profile-Tools (Fact-Store, Bulk-Read Dump & Duplizierung)

**Status**: READY  
**Epic / Meilenstein**: Meilenstein 5 – Epics 5.1 & 5.2  
**Erstellt am**: 2026-07-21  

---

## 1. Intention & Fachlicher Kontext

**Wissenschaftlich-agentische Motivation**:
Statt eines starren, unflexiblen "User-Profils" implementiert dieser Task einen generischen **Wissensspeicher (Fact-Store / Knowledge-Store)** je Plan:
1. **Generische Fakt-Struktur**: Jeder Fakt besteht aus `category` (z. B. `demografie`, `wohnsituation`, `praeferenzen`, `ziele`), `key`, `value` (beliebiger JSON-Typ), `description`, `source` (`user_explicit` vs. `agent_inferred`) und Timestamp.
2. **Bulk-Read Context Dump (`profile_get_all_facts`)**: Das LLM kann mit einem einzigen Tool-Aufruf zu Session-Beginn das komplette gesammelte Wissen zu einem Plan als strukturierten JSON/Markdown-Dump im Kontext verankern – ohne langwierige, tokenfressende Einzelabfragen.
3. **Automatisches Mitkopieren bei Szenarien**: Bei `core_duplicate_plan` wird der Wissensspeicher (`knowledge.json`) im Plan-Ordner automatisch mitkopiert.

---

## 2. Architektur & Betroffene Komponenten

- **`src/compute_to_ai/features/finance/knowledge_store.py`** [NEW]:
  Pydantic-Modelle `FactItem` und `KnowledgeStore`, Speicherung als `knowledge.json` im Plan-Ordner.
- **`src/compute_to_ai/mcp/finance_tools.py`** & `core_tools.py` [MODIFY]:
  MCP-Tools `profile_get_all_facts`, `profile_set_fact`, `profile_remove_fact`. Erweiterung von `core_duplicate_plan` zum Kopieren von `knowledge.json`.
- **`tests/test_features/test_finance/test_knowledge_store.py`** [NEW]:
  Tests für CRUD, Bulk-Read Dump, Kategorisierung und Plan-Duplizierung.

---

## 3. Konkrete Code-Anhaltspunkte & Signaturen

```python
# knowledge_store.py

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

## 4. Test-Strategie & Edge Cases (Mandatory)

### Happy Path:
- `profile_get_all_facts` liefert einen sauberen, vollständigen Dump aller Fakten.
- `core_duplicate_plan` dupliziert den Wissensspeicher exakt unter dem neuen Plan-Namen.

### Edge Cases:
- Abruf von Fakten eines Plans ohne existierenden Wissensspeicher liefert ein leeres, strukturiertes Objekt (kein Dateifehler).
- Überschreiben eines `user_explicit` Fakts aktualisiert den Timestamp und den Wert verlässlich.

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [ ] Steps (`01-step-wissensspeicher-datenmodell-und-datei.md`, `02-step-mcp-tools-bulk-read-und-crud.md`, `03-step-plan-duplizierung-mitnahme.md`) ausgeführt.
- [ ] Pytest-Suite grün.
- [ ] Doku in `Docs/02-Architektur-und-MCP.md` aktualisiert.
- [ ] `review.md` gegengezeichnet.
- [ ] `Docs/10-Roadmap.md` abgehakt `[x]`.
