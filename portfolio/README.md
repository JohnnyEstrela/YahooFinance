# Consultor Financeiro (portefólio + watchlist)

1. Edita `portfolio.json` (secções `portfolio` e `watchlist`).
2. `python portfolio/fetch_data.py` — vai buscar P/E, P/E forward, PEG e notícias (yfinance) para `data/snapshot.json`.
3. `python portfolio/render.py` — gera `index.html` (responsivo, claro/escuro, filtro Portefólio/Watchlist).

Limiares configuráveis em `thresholds`. P/E: <15 Barato, ≤30 Justo (~20), ≤50 Caro (~40), >50 Muito caro. PEG: <1 Desconto, 1–2 Justo, >2 Prémio.
