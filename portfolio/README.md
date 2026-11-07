# Portefólio & Watchlist

1. Edita `portfolio/watchlist.json` (`status`: `portfolio` ou `watchlist`; `shares`/`avg_cost`/`notes` opcionais; usa `BRK-B`, `EDP.LS`).
2. `pip install yfinance && python portfolio/update.py`
3. Abre `portfolio/index.html` (funciona por duplo clique, responsivo).

Limiares (editáveis em `thresholds`): P/E <15 barato · 15–30 justo · 30–50 caro · >50 muito caro; PEG <1 desconto · 1–2 justo · >2 prémio.
PEG = valor Yahoo; PEGY = P/E forward ÷ (crescimento % + dividend yield %).
O workflow `.github/workflows/portfolio-daily.yml` atualiza `data.js` todos os dias úteis.
