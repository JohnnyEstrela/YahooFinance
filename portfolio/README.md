# Portefólio diário

1. Edita `watchlist.json` (campo `status`: `portfolio` ou `watching`; limiares P/E e PEG em `settings`).
2. `pip install yfinance && python portfolio/update.py` → atualiza `data.json` e `index.html` (abre no browser).
3. Classificação: P/E <15 barato, ≤30 justo (ref. 20), ≤50 caro (ref. 40), >50 muito caro; PEG <1 desconto, 1–2 justo, >2 prémio. PEGY = P/E ÷ (crescimento % + dividendo %).

Requer acesso a Yahoo Finance; se falhar, mantém os dados anteriores e mostra aviso.
