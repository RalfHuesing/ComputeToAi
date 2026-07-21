# Step 1: Modulare Prompt-Hierarchie

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-5.3-5.4-prompt-restrukturierung-und-lebensberater/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Restrukturierung und Aufteilung des monolithischen Prompts `finanzberater.md` in modular geladene Teilbereiche unter `Docs/prompts/finance_de/`.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [NEW] `Docs/prompts/finance_de/core_advisor.md`
- [ ] [NEW] `Docs/prompts/finance_de/simulation_audit.md`
- [ ] [MODIFY] `Docs/prompts/finance_de/README.md`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```markdown
<!-- Docs/prompts/finance_de/core_advisor.md -->
# Rolle: Unabhängiger Finanz- & Lebensberater
[Kern-Regeln, Verhaltensprinzipien, MCP-Tool-Nutzung]
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
- Manuelle Prüfung auf Vollständigkeit und Freiheit von Redundanzen über alle Prompts hinweg.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/prompts/finance_de/README.md` aktualisieren.
