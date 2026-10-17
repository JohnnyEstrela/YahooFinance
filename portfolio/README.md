# Painel de portefólio / watchlist

- `watchlist.json` – as tuas empresas (`portfolio` ou `watchlist`) e os limiares P/E e PEG (editáveis).
- `python portfolio/refresh.py` – vai ao Yahoo Finance, calcula P/E (12m), P/E (próx. 12m), PEG, notícias e gera `index.html` (abre no browser; responsivo, tema claro/escuro).
- `python portfolio/refresh.py add NVDA [--portfolio --shares 5 --cost 120]` / `remove NVDA`.

Limiares por omissão: P/E <15 Barato, 15–30 Justo, 30–50 Caro, >50 Muito caro. PEG <1 Desconto, 1–2 Justo, >2 Prémio.
