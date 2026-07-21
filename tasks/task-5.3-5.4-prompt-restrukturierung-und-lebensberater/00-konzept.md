# Konzept: Task 5.3 & 5.4 – Prompt-Restrukturierung & Vorbereitung Lebensberater

**Status**: READY  
**Epic / Meilenstein**: Meilenstein 5 – Epics 5.3 & 5.4  
**Erstellt am**: 2026-07-21  

---

## 1. Intention & Fachlicher Kontext

**Wissenschaftlich-agentische Motivation**:
1. **Modulare Prompt-Hierarchie (Epic 5.3)**: Das bisherige System-Prompt (`Docs/prompts/finance_de/finanzberater.md`) droht monolithisch zu überfordern ("Brockhaus"-Problem). Es wird in übersichtliche, modular geladene Bausteine aufgeteilt: `core_advisor.md`, `profiling_guide.md`, `life_advisor.md`, `simulation_audit.md`.
2. **Profilierungs-Leitfaden**: Das LLM erhält einen klaren Leitfaden zur iterativen, natürlichen Abfrage von Nutzerdaten und Speicherung im Wissensspeicher (`profile_set_fact`), inklusive transparenter Rückmeldung an den Nutzer (*"Ich habe mir gemerkt, dass..."*).
3. **Rolle "Lebensberater" (Epic 5.4)**: Verankert die Prinzipien absolute Unabhängigkeit, wissenschaftliche Seriosität und Freiheit von Produktverkaufs-Interessenkonflikten. Der Lebensberater leitet aus Fakten des Wissensspeichers (z. B. Immobilienbesitz) proaktiv benötigte Simulations-Effekte ab (z. B. Instandhaltungs-Rücklage).

---

## 2. Architektur & Betroffene Komponenten

- **`Docs/prompts/finance_de/`** [MODIFY/NEW]:
  - `core_advisor.md`: Grundrolle & Verhaltensregeln.
  - `profiling_guide.md`: Datenerhebung & Wissensspeicher-Nutzung.
  - `life_advisor.md`: Lebensberater-Prinzipien & Herleitung von Simulationseffekten.
  - `simulation_audit.md`: Plausibilitätsprüfung & Pfad-Audit-Anleitung.
- **`tests/test_prompts/`** [NEW]:
  Prompt-Konsistenz- & Syntax-Prüfung.

---

## 3. Konkreter Code-Anhaltspunkte & Signaturen

```text
Docs/prompts/finance_de/
├── README.md
├── core_advisor.md
├── profiling_guide.md
├── life_advisor.md
└── simulation_audit.md
```

---

## 4. Test-Strategie & Edge Cases (Mandatory)

### Happy Path:
- Prompts sind vollständig modular verlinkt und frei von Widersprüchen zu den Projektregeln in `.agents/rules/`.

### Edge Cases:
- Das LLM stellt im Profiling-Modus keine inquisitorischen Fragen, sondern erhebt Daten empathisch und proaktiv im laufenden Gespräch.

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent

- [ ] Steps (`01-step-modulare-prompt-hierarchie.md`, `02-step-profiling-leitfaden-und-hintergrund-updates.md`, `03-step-lebensberater-rolle-und-prinzipien.md`) umgesetzt.
- [ ] Prompts in `Docs/prompts/finance_de/` vollständig aufgeteilt und gegenseitig verlinkt.
- [ ] `review.md` gegengezeichnet.
- [ ] `Docs/10-Roadmap.md` abgehakt `[x]`.
