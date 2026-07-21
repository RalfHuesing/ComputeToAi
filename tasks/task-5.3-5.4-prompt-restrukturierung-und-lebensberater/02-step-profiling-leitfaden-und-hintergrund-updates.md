# Step 2: Profilierungs-Leitfaden & Hintergrund-Updates

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-5.3-5.4-prompt-restrukturierung-und-lebensberater/00-konzept.md)  
**Status**: PENDING  

---

## 1. Step-Intention
Erstellung des Prompts `profiling_guide.md`, der das LLM anleitet, Wissensspeicher-Fakten proaktiv abzufragen, per Bulk-Read zu lesen (`profile_get_all_facts`) und per `profile_set_fact` im Hintergrund zu pflegen.

---

## 2. Zu bearbeitende / neu anzulegende Dateien
- [ ] [NEW] `Docs/prompts/finance_de/profiling_guide.md`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

```markdown
<!-- profiling_guide.md -->
# Profilierungs-Leitfaden
1. Lade zu Beginn der Session alle Fakten über `profile_get_all_facts`.
2. Erkenne Wissenslücken (z.B. Wohnsituation, Risikoeinstellung, Frühruhestandswunsch).
3. Erfasse Fakten empathisch im Dialog.
4. Speichere neue Daten sofort über `profile_set_fact` und erwähne dies transparent: "Ich habe mir gemerkt, dass..."
```

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
- Überprüfung des Prompts im Zusammenspiel mit den MCP-Tools.

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/prompts/finance_de/README.md` aktualisieren.
