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

Páginas de notícias do painel: cada `category` em `market_news` vira uma página (separador). Categorias atuais: Macro e Fed, Energia e geopolítica, Mercado de ações, Tecnologia e chips, Eletricidade e renováveis, Fintech e crédito, Espaço, defesa e quântica. Criar novas categorias quando surgir um tema que mexa com as empresas seguidas ou com o mercado todo (ex.: biotecnologia, criptomoedas, China/Ásia, resultados da semana). Uma pesquisa `bigdata_search` por tema, 3-5 itens cada.
Frequência: de 4 em 4 horas. Notificar só novidades de impacto alto que ainda não foram notificadas (comparar com o `data/snapshot.json` anterior).

## Notificação (sempre com empresas)
Por pedido do utilizador, nunca enviar uma notificação sem empresas. Toda a notificação (PushNotification, dentro de <routine_summary>) tem de nomear empresas concretas de portfolio.json (hoje 65: as 15 originais + 49 novas + as 8 corrigidas):
1. Primeira frase: a empresa/notícia mais importante (ex.: "J&J -5,7% após resultados"). Notícias de mercado só entram como contexto depois, nunca sozinhas.
2. Depois: empresas com variação > 3% (ticker, %, preço), empresas que mudaram de classificação (P/E ou PEG: Barato/Desconto/Caro/Premium), empresas com resultados a sair nos próximos dias (ex.: ASML) e 1-2 notícias por empresa afetada.
3. Se nenhuma empresa tiver variação > 3%, listar as 3 maiores variações do dia na mesma.
4. Link do painel https://claude.ai/artifact/Ccwz65bhmktPXrTmYWinyD.
Se a rotina não conseguir correr (acesso negado, erro), notificar com o erro e as empresas que ficaram por atualizar.

## Âmbito das empresas
A rotina tem de cobrir TODAS as empresas de portfolio.json (65). Preços/variação/P/E 12m: Wisesheets (`get_prices_live`, 25 por chamada, só EUA) e Bigdata `bigdata_portfolio_tearsheet` (europeias: BAYN, M09, YSON, EDW). P/E futuro e PEG: ver "P/E futuro via Bigdata.com". Notícias: `bigdata_search` por empresa que mexeu > 3% ou tem evento (resultados, M&A, rating), e por tema de mercado. Tudo em USD (ver Moeda).

## Prompt para a rotina agendada (colar nas definições da rotina, frequência de 4 em 4 horas)
Lê ROUTINE.md e executa-o por completo no repositório YahooFinance, branch claude/cool-dijkstra-4zh0sf: atualiza TODAS as 65 empresas de portfolio.json (preços, P/E 12m, P/E futuro, PEG, em USD), recolhe notícias por empresa que mexeu e por tema de mercado, corre build_dashboard.py, republica o painel (Artifact acima), faz commit e push, e termina com uma PushNotification que nomeia sempre empresas concretas (nunca só notícias de mercado).
