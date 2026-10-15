# Consultor de Carteira

Painel diário com as empresas da tua carteira e das que estás a seguir: P/E (12m passados), P/E (próx. 12m), PEG, PEGY, dividendo, alvo de analistas e notícias (por empresa e de mercado). Dados do Yahoo Finance via `yfinance`.

## Usar
1. Edita `watchlist.json`: põe empresas em `holdings` (carteira, com `shares`/`avg_cost` opcionais) ou `watching` (a seguir). Tickers do Yahoo: `AAPL`, `BRK-B`, `EDP.LS`, `SAP.DE`.
2. `pip install yfinance && python portfolio/update.py`
3. Abre `portfolio/dashboard.html` (responsivo, tema claro/escuro, pesquisa, ordenação, separadores Carteira / A seguir).

## Limites de valorização (`config.json`)
- **P/E**: < 15 Barato · 15–30 Justo · 30–50 Caro · > 50 Muito caro
- **PEG**: < 1 Desconto · 1–2 Justo · > 2 Prémio

O teu pedido dava pontos (15 / 20 / 40 / 50) e não faixas contínuas; os intervalos entre eles foram fechados a meio (30). Muda os valores em `config.json` se preferires outros cortes.
O PEG vem do Yahoo (`trailingPegRatio`); se faltar, calcula-se P/E futuro ÷ crescimento de lucros. PEGY = P/E futuro ÷ (crescimento + dividendo %).
