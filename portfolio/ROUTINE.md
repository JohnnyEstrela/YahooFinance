# Rotina diária do portefólio

1. Ler `portfolio.json` (lista de empresas: `portfolio` ou `watchlist`; limiares de P/E e PEG editáveis).
2. Para cada ticker, atualizar `snapshot.json` (FMP MCP):
   - `quote` → price, change_pct, market_cap, year_low/high
   - `statements/metrics-ratios-ttm` → `pe_ttm` (priceToEarningsRatioTTM), `peg` (priceToEarningsGrowthRatioTTM), `div_yield`
   - `analyst/financial-estimates` (annual, limit 7) → `eps_estimates` [[data_fim_ano_fiscal, epsAvg]]
   - 2–3 notícias relevantes por empresa + 3–5 notícias de mercado (WebSearch)
3. `python3 portfolio/build_report.py` → `portfolio/docs/index.html`.
4. Commit + push. Notificar apenas se: alguma empresa mudou de classificação (ex. Pricey→Fair), variação diária > ±5 %, ou notícia material.

P/E próximos 12 meses = preço ÷ EPS NTM (média ponderada dos dois anos fiscais de estimativas que cobrem os próximos 12 meses).
Para adicionar uma empresa: acrescentar entrada em `portfolio.json` e correr a rotina.
