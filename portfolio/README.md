# Portefólio & Watchlist

1. Edita `portfolio/portfolio.json` — adiciona empresas (`status`: `portfolio` ou `watchlist`; `shares`, `avg_cost`, `notes` opcionais).
2. Corre `pip install yfinance requests && python portfolio/update.py`.
3. Abre `portfolio/report/index.html` (adaptável a telemóvel, modo claro/escuro, filtro Portefólio/A seguir).

Cada empresa mostra P/E (últimos 12m), P/E (próx. 12m) e PEG com etiqueta de valorização, intervalo 52 semanas,
dividend yield, preço-alvo, P/L da posição e notícias. Há ainda notícias gerais de mercado.

Limiares (editáveis em `thresholds`): P/E <15 Barato, <30 Justo, <50 Caro, ≥50 Muito caro; PEG <1 Desconto, 1–2 Justo, >2 Premium.
P/E ou PEG negativos/ausentes aparecem como `n/d`.
