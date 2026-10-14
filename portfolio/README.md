# Portefólio

1. Edita `watchlist.json`: `status` = `owned` (com `shares`/`avg_cost`) ou `watching`. Os limites de P/E e PEG estão em `thresholds`.
2. `pip install yfinance && python portfolio/update.py` gera `data.json` + `index.html` (abre no browser; responsivo, claro/escuro).
3. O workflow `.github/workflows/portfolio.yml` corre em dias úteis às 07:00 UTC.

Escalões P/E: <15 Barato · 15–30 Justo · 30–50 Caro · ≥50 Muito caro. PEG: <1 Desconto · 1–2 Justo · >2 Premium. PEGY = P/E futuro ÷ (crescimento % + yield %).
`--demo` gera dados fictícios (o index.html atual é só demo).
