# Rotina diária - Consultor Financeiro

1. Ler `watchlist.json` (o utilizador adiciona/remove empresas; `status` = `portfolio` ou `watching`).
2. Para cada ticker, atualizar `data/snapshot.json`:
   - FMP `quote` → preço, variação, intervalo 52 sem., market cap.
   - FMP `statements/metrics-ratios-ttm` → `priceToEarningsRatioTTM` (P/E), `priceToEarningsGrowthRatioTTM` (PEG), `dividendYieldTTM`.
   - FMP `analyst/financial-estimates` (annual, limit 10) → `eps_estimates` [data FY, epsAvg] dos anos fiscais futuros.
   - Notícias relevantes (WebSearch) com título, URL e data; notícias gerais de mercado em `market_news`. Não inventar: se não houver, dizer.
3. `python3 portfolio/build.py` → regenera `portfolio/index.html`.
4. Commit + push; avisar o utilizador se alguma empresa mudou de faixa de valuation ou há resultados iminentes.

Faixas: P/E <15 barato, ≤20 justo, ≤40 elevado, 40–50 elevado+, >50 muito caro. PEG <1 desconto, 1–2 justo, >2 prémio.
Nota: o Yahoo Finance devolve 429 a partir do ambiente cloud; usa-se a FMP.
