# Rotina diária de portefólio

1. Edita `companies.json` — adiciona `{"ticker": "XYZ", "status": "portfolio" | "watchlist", "shares": 10, "avg_cost": 100, "notes": "..."}`.
2. Corre `python3 portfolio/update.py` (precisa de `pip install yfinance`). Gera `data.json` e `index.html` (responsivo, claro/escuro).
3. Os limiares de P/E e PEG estão em `thresholds` (P/E: <15 Barato, 15–30 Justo, 30–50 Caro, ≥50 Muito caro; PEG: <1 Desconto, 1–2 Justo, >2 Premium).

Tickers de outros mercados usam sufixo Yahoo (ex.: `EDP.LS`, `BRK-B`). Informativo, não é aconselhamento financeiro.
