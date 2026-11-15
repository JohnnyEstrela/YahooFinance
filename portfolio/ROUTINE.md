# Rotina diária: Carteira e Radar

O painel já existe. **Não criar um novo**: atualizar este.

- Painel (artifact): https://claude.ai/artifact/VUTaMq2YKieMrDduBF457h
- Base de dados do painel (ArtifactData, mesmo URL):
  - `companies/<TICKER>`: escrita pelo utilizador no painel (`ticker`, `status` = `portfolio`|`watchlist`, `shares`, `avgCost`, `note`, `example`).
  - `metrics/<TICKER>`: escrita pela rotina (saída de `daily_update.py`).
  - `market/latest`: índices + notícias de mercado.
  - `briefing/latest`: nota do consultor (`date`, `text`, `points[]`), em português.

## Passos de cada execução

1. `ArtifactData list companies` (com `out_dir`) e montar `companies.json` (lista dos `data`).
2. `uv run python portfolio/daily_update.py companies.json snapshot.json`
3. `python portfolio/to_db_files.py snapshot.json db/`
4. `ArtifactData batch`: `set` de cada `metrics/<KEY>` e `market/latest` (com `if_version` se já existirem),
   `delete` de `metrics/*` cujas empresas foram removidas, e `set` de `briefing/latest` com a nota do dia.
5. Nota do consultor: destacar mudanças de banda (ex.: P/E passou de justo para caro), PEGY < 1, notícias
   relevantes para empresas da carteira e o tom do mercado. Sem recomendações de compra/venda.
6. Notificar o utilizador só quando houver algo relevante (mudança de banda, movimento > 5%, notícia
   importante numa empresa da carteira, ou falha da rotina).

## Bandas

- P/E (12m passados e próximos): < 15 barato · 15–30 justo (~20) · 30–50 caro/pricey (~40) · > 50 muito caro.
- PEGY = P/E ÷ (crescimento esperado % + dividend yield %): < 1 desconto · 1–2 justo · > 2 premium.
  O crescimento vem do PEG a 5 anos do Yahoo (P/E ÷ PEG); em alternativa, estimativas LTG/+1y.
