# Rotina diária do portefólio

1. Ler `portfolio.json` (lista editável de empresas; `status`: `portfolio` ou `watchlist`).
2. Para cada ticker, via FMP (Yahoo pode estar bloqueado no ambiente):
   - `quote` → preço, variação, market cap, mín/máx 52 semanas.
   - `statements/metrics-ratios-ttm` → `priceToEarningsRatioTTM` (P/E 12m), `priceToEarningsGrowthRatioTTM` (PEG), `dividendYieldTTM` (×100).
   - `analyst/financial-estimates` (annual) → P/E próximos 12m = preço / `epsAvg` do primeiro ano fiscal que termina daqui a ≥ ~6 meses (nunca inventar; `null` se faltar).
   - Notícias: `bigdata_search` (Bigdata.com, modo smart, ex.: "<Empresa> news in the last 2 days", max_chunks 5-8). Funciona com dados do próprio dia; o WebSearch devolve resultados desatualizados e o news do FMP exige plano pago. Guardar título, url, fonte, data. Para o mercado geral, pesquisar "major market-moving news today".
3. Escrever tudo em `data/snapshot.json` (mesmo formato do ficheiro atual) + `market_news` com 3-5 notícias gerais de mercado.
4. `python3 build_dashboard.py` → `docs/dashboard.html` (desenho em `dashboard_template.html`), e republicar como Artifact: `https://claude.ai/artifact/Ccwz65bhmktPXrTmYWinyD` (publicar o mesmo ficheiro mantém o link).
5. Commit + push.
6. Notificar (PushNotification, 1ª frase = manchete) quando houver notícia importante numa empresa do portefólio/watchlist: resultados ou guidance, fusões e aquisições, regulação/processos, mudança de CEO/CFO, rebaixamento ou subida de rating de analistas, dividendos, ofertas de ações, alertas de lucros, ou eventos macro que mexam com o mercado (Fed, taxas, tarifas). Também quando: variação diária > 5%, ou a empresa passou a Barato / Desconto. Se nada disto acontecer, não notificar.

Escalas (editáveis em `portfolio.json`): P/E <15 Barato · <30 Fair · <50 Caro · ≥50 Muito caro; PEG <1 Desconto · 1–2 Fair · >2 Premium.
