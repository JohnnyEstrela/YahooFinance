# Consultor Financeiro

1. Edita `portfolio.json` (adiciona `{"ticker": "XYZ", "status": "portfolio"|"watchlist"}`; `shares`/`avg_cost` opcionais; limites ajustáveis).
2. `pip install yfinance && python consultor/update.py`
3. Abre `dashboard.html` (responsivo, modo claro/escuro, filtro Portefólio/Watchlist).

Classificações: P/E (12m e próx. 12m) <15 Barato · ≤30 Fair Value · ≤50 Pricey · >50 Expensive; PEG <1 Discount · 1–2 Fair · >2 Premium.
