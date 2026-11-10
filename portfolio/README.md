# Consultor Financeiro — dashboard diário

1. Edita `portfolio.json`: adiciona empresas em `holdings` (`status`: `portfolio` ou `watchlist`; `shares`/`avg_cost`/`notes` opcionais).
2. `pip install yfinance && python portfolio/build.py`
3. Abre `portfolio/index.html` (responsivo, tema claro/escuro, filtros e ordenação).

Limiares (editáveis em `thresholds`):
- P/E (12m e próximos 12m): <15 barato · 15–30 justo · 30–50 caro · ≥50 muito caro
- PEG: <1 desconto · 1–2 justo · >2 prémio

Notas: o PEG vem do Yahoo; se faltar, é estimado como P/E forward ÷ crescimento de lucros. Tickers fora dos EUA usam sufixo (ex.: `EDP.LS`).
