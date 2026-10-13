# Rotina diária (consultor + portefólio)

1. Lê `portfolio.json` (posições + watchlist) e `thresholds.json`.
2. Atualiza `data/snapshot.json`: `python fetch_yahoo.py` (Yahoo) ou, se bloqueado, via MCP (FMP/Alpha Vantage/Bigdata).
   Por empresa: price, change_pct, pe_ttm, pe_fwd, peg, pegy (PEG + dividend yield), div_yield, target, sector, news[{title,url,source,date}].
   Em `market_news`: 3-6 notícias de mercado relevantes. Nunca inventes valores — deixa `null`.
3. `python build_dashboard.py` → `docs/index.html`.
4. Faz commit/push. Notifica só se: empresa muda de classificação (ex.: Justo→Caro), variação diária > ±5%, ou notícia material.

Para adicionar empresas: edita `portfolio.json` (ou usa o botão "Exportar" do dashboard e cola o JSON).
Limiares: PE <15 Barato · 15-25 Justo · 25-50 Caro · >50 Muito caro. PEG <1 Desconto · 1-2 Justo · >2 Prémio (editáveis em `thresholds.json`).
Não é aconselhamento financeiro.
