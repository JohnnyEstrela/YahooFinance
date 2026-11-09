# Consultor Financeiro (portefólio + watchlist)

1. Edita `watchlist.json` (`status`: `portfolio` ou `watch`).
2. `pip install yfinance && python portfolio/build.py` → gera `data.json` e `index.html` (dashboard responsivo, tema claro/escuro).
3. `overrides.json` é fallback de fundamentais (preenchido pela rotina diária via FMP) quando o Yahoo bloqueia.

Escalas: P/E <15 Barato · 15–30 Valor justo (~20) · 30–50 Pricey (~40) · >50 Expensive. PEG <1 Desconto · 1–2 Justo · >2 Premium.
