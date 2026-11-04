# Consultor Financeiro

1. Edita `portfolio.json` (`list`: `portfolio` ou `watchlist`).
2. `pip install yfinance && python3 update.py` → gera `data.js`.
3. Abre `index.html` (responsivo, modo claro/escuro, filtros e ordenação).

Escalas: P/E <15 Barato, 15–20 Justo, 20–40 Justo+/Caro, 40–50 Caro, >50 Muito caro. PEG <1 Desconto, 1–2 Justo, >2 Prémio.
Se o Yahoo limitar pedidos, P/E forward/PEG aparecem como "n/d" nesse dia.
