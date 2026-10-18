# Consultor Financeiro (portefólio + watchlist)

- `watchlist.json` – empresas (`ticker`, `status`: `portfolio` | `watching`, opcional `shares`, `avg_cost`).
- `update.py` – vai buscar preço, P/E (12m e próx. 12m), PEG e notícias via yfinance e grava `data.json`.
- `index.html` – dashboard (abrir com `python -m http.server` nesta pasta).

Limiares: P/E <15 Barato · 15–20 Valor justo · 20–40 Acima do justo · 40–50 Caro · >50 Muito caro.
PEG <1 Desconto · 1–2 Justo · >2 Prémio.

Rotina diária: `pip install yfinance && python portfolio/update.py`, depois commit de `data.json`.
