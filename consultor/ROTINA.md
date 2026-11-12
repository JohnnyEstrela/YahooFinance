# Consultor Financeiro: rotina diária

Pasta com a carteira, os dados diários e o dashboard **Carteira & Radar** (`consultor/dashboard.html`).

## Adicionar ou remover empresas

Edita `consultor/portfolio.json`, ou pede no chat (ex.: «adiciona a ASML à carteira, 10 ações a 700$»).

```json
{ "ticker": "ASML", "nome": "ASML", "estado": "carteira", "acoes": 10, "preco_medio": 700 }
```

- `estado`: `carteira` (já tens) ou `seguir` (watchlist).
- `acoes` e `preco_medio` são opcionais; se preenchidos, o dashboard mostra o valor e o ganho.
- As 5 empresas iniciais (AAPL, MSFT, NVDA, GOOGL, AMZN) são **exemplos** (`"exemplo": true`). Substitui-as pelas tuas.
- As faixas de P/E e PEG estão em `limites` e podem ser ajustadas.

## Faixas usadas

| Rácio | Barato / Desconto | Justo | Pricey | Expensive / Premium |
|---|---|---|---|---|
| P/E últ. 12m e próx. 12m | < 15 | 15–30 (~20) | 30–50 (~40) | > 50 |
| PEG / PEGY | < 1 | 1–2 | | > 2 |

- **P/E próx. 12m** = preço ÷ EPS dos próximos 12 meses (média ponderada das estimativas para o ano fiscal corrente e o seguinte).
- **PEGY** = P/E futuro ÷ (crescimento anual do EPS % + dividend yield %). O crescimento é a taxa anual composta do EPS estimado do próximo ano fiscal até dois anos depois.

## O que a rotina faz em cada execução (instruções para o agente)

1. Ler `consultor/portfolio.json`.
2. Para cada ticker, via FMP MCP (`mcp__FMP__*`):
   - `quote` / `quote` → preço, variação, 52 semanas, médias 50/200d, market cap;
   - `statements` / `metrics-ratios-ttm` → `netIncomePerShareTTM` (EPS TTM) e `dividendYieldTTM`;
   - `analyst` / `financial-estimates` (period `annual`, limit 10) → `epsAvg` por ano fiscal (guardar o ano corrente e os 3–4 seguintes).
   O Yahoo Finance (yfinance) e o Alpha Vantage estão bloqueados/limitados no ambiente cloud, por isso a fonte é o FMP. O plano FMP atual não cobre alguns tickers (ex.: ASML); nesse caso, registar "sem dados" e avisar.
3. Notícias: pesquisa web por cada empresa e um resumo do mercado; 2–3 links recentes por empresa.
4. Escrever `consultor/data/AAAA-MM-DD.json` (mesmo formato do anterior) com uma `leitura` de consultor por empresa.
5. `python3 consultor/build.py` → `consultor/dashboard.html`.
6. Commit e push; notificar com os destaques (mudanças de zona, quedas/subidas fortes, resultados próximos).
