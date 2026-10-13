# Rotina diária do portefólio

1. Ler `portfolio.json` (lista editável de empresas; `status`: `portfolio` ou `watchlist`).
2. Para cada ticker, via FMP (Yahoo pode estar bloqueado no ambiente):
   - `quote` → preço, variação, market cap, mín/máx 52 semanas.
   - `statements/metrics-ratios-ttm` → `priceToEarningsRatioTTM` (P/E 12m), `priceToEarningsGrowthRatioTTM` (PEG), `dividendYieldTTM` (×100).
   - `analyst/financial-estimates` (annual) → P/E próximos 12m = preço / `epsAvg` do primeiro ano fiscal que termina daqui a ≥ ~6 meses (nunca inventar; `null` se faltar).
   - Notícias: WebSearch por ticker (o endpoint de news do FMP exige plano pago). Guardar título, url, fonte, data.
3. Escrever tudo em `data/snapshot.json` (mesmo formato do ficheiro atual) + `market_news` com 3-5 notícias gerais de mercado.
4. `python3 build_dashboard.py` → `docs/dashboard.html`.
5. Commit + push. Notificar apenas se houver algo relevante (empresa passou a Barato/Desconto, variação > 5%, notícia material).

Escalas (editáveis em `portfolio.json`): P/E <15 Barato · <30 Fair · <50 Caro · ≥50 Muito caro; PEG <1 Desconto · 1–2 Fair · >2 Premium.
