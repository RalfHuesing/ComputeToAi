# Konzept: [TASK_TITEL]

**Status**: DRAFT | READY | IN_PROGRESS | DONE  
**Epic / Meilenstein**: [Referenz auf Epic/Meilenstein in Docs/10-Roadmap.md]  
**Erstellt am**: [DATUM]  

---

## 1. Intention & Fachlicher Kontext
- **Warum machen wir das?**: [Kurze Erklärung des Problems / Nutzens]
- **Welches Verhalten wird angestrebt?**: [Fachliche Zielsetzung]

---

## 2. Architektur & Betroffene Komponenten
- **Module / Dateien**:
  - `src/compute_to_ai/...`
  - `tests/...`
  - `Docs/...`
- **Datenfluss & Schnittstellen**: [Beschreibung]

---

## 3. Konkrete Code-Anhaltspunkte & Signaturen
```python
# Skizze der zentralen Datenstrukturen oder Funktionen
def example_function(param: str) -> dict:
    ...
```

---

## 4. Test-Strategie & Edge Cases
- **Happy Path Tests**: [Szenario]
- **Edge Cases & Fehlerfälle**:
  - [Edge Case 1: z.B. leere Eingaben, fehlende Daten, Division durch Null]
  - [Edge Case 2: z.B. ungültige Typen, Phasengrenzen-Mismatches]

---

## 5. Definition of Done (DoD) & Kontrollkriterien für Review-Agent
- [ ] Alle Steps in diesem Task-Ordner sind grün ausgeführt.
- [ ] Tests abgedeckt (`pytest tests/...`) inklusive aller definierten Edge Cases.
- [ ] Doku in `Docs/` aktualisiert gemäß `living-documentation.mdc`.
- [ ] `review.md` erstellt und gegengezeichnet.
- [ ] `Docs/10-Roadmap.md` abgehakt `[x]`.
