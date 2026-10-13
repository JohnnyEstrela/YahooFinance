# Rotina diária do portefólio

1. Ler `portfolio.json` (lista editável de empresas; `status`: `portfolio` ou `watchlist`).
2. Para cada ticker, via FMP (Yahoo pode estar bloqueado no ambiente):
   - `quote` → preço, variação, market cap, mín/máx 52 semanas.
   - `statements/metrics-ratios-ttm` → `priceToEarningsRatioTTM` (P/E 12m), `priceToEarningsGrowthRatioTTM` (PEG), `dividendYieldTTM` (×100).
   - `analyst/financial-estimates` (annual) → P/E próximos 12m = preço / `epsAvg` do primeiro ano fiscal que termina daqui a ≥ ~6 meses (nunca inventar; `null` se faltar).
   - Notícias: `bigdata_search` (Bigdata.com, modo smart, ex.: "<Empresa> news in the last 2 days", max_chunks 5-8). Funciona com dados do próprio dia; o WebSearch devolve resultados desatualizados e o news do FMP exige plano pago. Guardar título, url, fonte, data. 
3. Notícias de mercado (prioridade igual às das empresas): correr `bigdata_search` uma vez por tema, uma pergunta por chamada: (a) Fed, juros e inflação (CPI, PCE, emprego, PIB); (b) fecho de Wall Street e o que moveu índices e setores; (c) petróleo, geopolítica, tarifas e sanções; (d) dólar, yields e crédito; (e) Europa/Ásia (BCE, China) quando relevante; (f) calendário dos próximos dias (CPI, FOMC, resultados de grandes bancos e tecnológicas). Guardar 5-8 itens em `market_news` com `category`, `impact` ("alto" ou "medio"), `title`, `summary` (1-2 frases com números), `url`, `source`, `date`. Marcar "alto" o que pode mexer com o mercado todo (decisões e discursos da Fed, dados de inflação/emprego, choque no petróleo, guerra, tarifas, crise bancária).
3b. Escrever tudo em `data/snapshot.json` (mesmo formato do ficheiro atual) + `market_news` com 3-5 notícias gerais de mercado.
4. `python3 build_dashboard.py` → `docs/dashboard.html` (desenho em `dashboard_template.html`), e republicar como Artifact: `https://claude.ai/artifact/Ccwz65bhmktPXrTmYWinyD` (publicar o mesmo ficheiro mantém o link).
5. Commit + push.
6. Notificar (inclui notícias de mercado com `impact` = alto, mesmo que não toquem em nenhuma das suas empresas) (PushNotification, 1ª frase = manchete) quando houver notícia importante numa empresa do portefólio/watchlist: resultados ou guidance, fusões e aquisições, regulação/processos, mudança de CEO/CFO, rebaixamento ou subida de rating de analistas, dividendos, ofertas de ações, alertas de lucros, ou eventos macro que mexam com o mercado (Fed, taxas, tarifas). Também quando: variação diária > 5%, ou a empresa passou a Barato / Desconto. Se nada disto acontecer, não notificar.

Escalas (editáveis em `portfolio.json`): P/E <15 Barato · <30 Fair · <50 Caro · ≥50 Muito caro; PEG <1 Desconto · 1–2 Fair · >2 Premium.

Notas de cálculo (fonte: Bigdata.com/FMP, FMP gratuito só cobre alguns tickers):
- P/E 12m = `pe_ratio` TTM do tearsheet. Empresas com prejuízo ficam `null` (n/d).
- P/E próximos 12m = preço / soma do EPS estimado dos próximos 4 trimestres (`analyst_estimates`). `null` se a soma for negativa.
- PEG = P/E futuro / crescimento (%) do EPS dos próximos 12m face ao EPS TTM (= preço / P/E 12m). `null` se o crescimento for ≤ 0. O PEG do fornecedor foi ignorado por dar valores negativos e erráticos.
- Preço e variação: `bigdata_portfolio_tearsheet` (até 100 empresas por chamada).
