agent feedback:
"
...
Drei-Komponenten-Zielgröße: Die Berechnung in cash_bucket_manager in 

portfolio.py
 splittet sich in:
Einkommensausfallpuffer: Monatliche Ausgaben × phasenabhängige Puffer-Monate (z. B. 3 Monate in der Erwerbsphase).
Nahsicht-Komponente: Automatische Prüfung aller Zukunftsjahre im Nah-Horizont ($N$ Schritte) auf geplante Ausgaben/Anschaffungen aus "cash".
Entnahmepuffer: In Phasen, deren Name "rente" enthält, wird ein Entnahmepuffer ($Y$ Jahre × Entnahme-Abhängigkeit) ermittelt.
...
"

-> wird im code hart auf "cash" oder "rente" gefiltert?
das ist doch grundsätzlicher unsinn?
was wenn ich, als nutzer, das "ruhestand" nenne?
wenn wir das filtern müssen dann brauchen wir definierte eigenschaften dafür. enum's oder so.
aber nicht auf "strings matchen"!?

das scheint sich grundsätzlich durch den ganzen roadmap punkt #3 zu ziehen

klären und umsetzen

=> allgemein sehr viele "feste strings" .. macht das so sinn?! wenn dann constanten irgendwo zentral? aber ich stelle die festen strings allgemein in frage.

noch mehr:

    cash_store = str(parameters.get("cash_store_name", "cash"))
    portfolio_weights = {k: float(v) for k, v in parameters["portfolio_weights"].items()}
    emergency_buffer_months = {
        k: float(v) for k, v in parameters["emergency_buffer_months"].items()
    }
    monthly_expenses = float(parameters["monthly_expenses"])
    inflation_rate = float(parameters.get("inflation_rate", 0.0))
    near_horizon_steps = int(parameters.get("near_horizon_steps", 2))
    entnahme_years = float(parameters.get("entnahme_years", 3.0))


---

"taxed_vorabpauschale: float = 0.0"
macht das so sinn?
mental hatte ich gedacht wir implementieren sowas als "abstraktes modell"?
was dann als effect wirkt oder so?
ich könnte mir "spezial-pauschale" ausdenken. 20% auf alles - außer tiernahrung.
das müsste ich so in unser modell "konfiguieren" können (per mcp server interaktion) OHNE das ich den code nochmal anfassen muss?

---

wtf ist tax.py?
hartkodierte steuer regeln?! (siehe vorabpauschale)

