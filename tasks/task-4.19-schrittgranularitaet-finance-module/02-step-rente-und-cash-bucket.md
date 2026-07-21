# Step 2: Gesetzliche Rente und Cash-Bucket-Entnahmepuffer

**Task-Referenz**: [00-konzept.md](file:///c:/Daten/Entwicklung/Ralf/ComputeToAi/tasks/task-4.19-schrittgranularitaet-finance-module/00-konzept.md)
**Status**: DONE

---

## 1. Step-Intention

`add_statutory_pension`s Rentenabschlag/-zuschlag-Berechnung und der Cash-Bucket-Entnahmepuffer (Baustein 3, "Entnahmepuffer") auf `plan.timeline.steps_per_year` umstellen, statt implizit von Jahresschritten auszugehen.

---

## 2. Zu bearbeitende / neu anzulegende Dateien

- [ ] [MODIFY] `src/compute_to_ai/features/finance/pension.py`
- [ ] [MODIFY] `src/compute_to_ai/features/finance/portfolio.py` (`CashBucketParameters`, `_calculate_withdrawal_buffer`, `add_cash_bucket`)
- [ ] [MODIFY] betroffene Tests, u. a. `tests/test_features/test_finance/test_pension.py`, `test_portfolio.py`

---

## 3. Konkreter Code-Entwurf & Implementierungs-Vorgaben

Siehe `00-konzept.md`, Abschnitt 3. Wichtig für den Cash-Bucket: `_calculate_withdrawal_buffer` kennt den Plan bereits (`plan: Plan` ist Parameter), `steps_per_year` muss also nicht extra durchgereicht werden, sondern kann direkt über `plan.timeline.steps_per_year` gelesen werden. Der bestehende Golden-Test für Jahresschritt-Pläne (`steps_per_year=1`, heutiger einziger produktiv genutzter Fall) darf sich **nicht** ändern – vor der Änderung den bestehenden erwarteten Wert notieren und als Regressionstest sichern, bevor die Formel angepasst wird.

`add_statutory_pension` braucht keinen neuen Parameter (liest `plan.timeline.steps_per_year` intern), die MCP-Tool-Signatur in `finance/_tax_pension.py` bleibt unverändert.

### Spezifische Hinweise:
- Beachte `.agents/rules/code-standards.mdc` und `.agents/rules/language.mdc`.
- `regular_retirement_step`/`actual_retirement_step` bleiben Schritt-Werte (nicht Jahre) – nur die interne Umrechnung in Monate für die Abschlag/Zuschlag-Formel ändert sich.

---

## 4. Test-Spezifikation (Happy Path & Edge Cases)

### Auszuführende Tests:
```bash
pytest tests/test_features/test_finance/test_pension.py tests/test_features/test_finance/test_portfolio.py -v
```

### Abzudeckende Testfälle:
- **Happy Path / Regression**: `steps_per_year=1` liefert identische Rentenabschlag-/Cash-Bucket-Werte wie vor der Änderung (bestehende Golden-Tests bleiben grün, unverändert).
- **Edge Cases**:
  - `add_statutory_pension` auf einem Plan mit `steps_per_year=12`: `actual_retirement_step` liegt z. B. 6 Monatsschritte vor `regular_retirement_step` → `months_early == 6`, nicht `72`.
  - Cash-Bucket-Entnahmepuffer auf einem Plan mit `steps_per_year=12`: derselbe fachliche Sachverhalt (identische Jahres-Ausgaben, identische `withdrawal_years`) liefert denselben Entnahmepuffer-Betrag wie das äquivalente Jahresschritt-Szenario mit `steps_per_year=1` (Betrag ist unabhängig von der gewählten Schrittweite, nur die Schrittzahlen unterscheiden sich).

---

## 5. Doku-Aktualisierungs-Auftrag (Living Documentation)
- [ ] `Docs/04-Feature-Finanzen-Methodik.md` (Abschnitt "Cash-Bucket-Management") und `Docs/05-Feature-Finanzen-Parameter.md` (Rentenabschlag/-zuschlag) um den Hinweis auf `steps_per_year`-Abhängigkeit ergänzen.
- [ ] `Docs/10-Roadmap.md`: Epic 4.19 abhaken, sobald Review „PASSED".
