# Rotina diária: Portefólio & Radar

Dashboard: https://claude.ai/artifact/5cZ6UDNddSPgLbGouTtoFT (tipo "Data", página em `portfolio/dashboard/index.html`)

## O que o utilizador edita

`portfolio/watchlist.json`:

- `portfolio`: empresas que tem. `{"ticker": "ASML", "shares": 10, "avg_cost": 650, "note": "..."}` (`avg_cost` na moeda da ação).
- `radar`: empresas a seguir. `{"ticker": "EDP.LS", "note": "..."}`. `news_query` opcional afina o Google News.
- `thresholds`: fronteiras das zonas. P/E: <15 Barato, 15–30 Fair Value, 30–50 Pricey, ≥50 Expensive. PEGY: <1 Discount, 1–2 Fair, ≥2 Premium.
- `example: true` marca empresas de exemplo.

Se o utilizador pedir numa conversa para adicionar/remover empresas, edita este ficheiro, faz commit e push.

## Passos de cada execução

1. `uv sync` e `uv run python portfolio/fetch.py` → gera `portfolio/out/companies.json` e `portfolio/out/news.json` (`{rows, meta}`).
2. Antes de substituir, lê os ids atuais: `ArtifactData get` em `datasets/companies` e `datasets/news` (o id é o que vem depois de `/_blob/` em `source.url`). Lê o `companies.json` antigo (`Artifact read`, `path` = id) para comparar com o novo.
3. Carrega os dois ficheiros novos: `Artifact publish` com `url` do dashboard, `asset: true`, um `file_path` por chamada.
4. `ArtifactData batch` com `update` em `datasets/companies` e `datasets/news` (com `if_version`): `source.url` novo, `updated: {at, by: "Rotina diária (Claude)"}`, `edit: {via: "claude", at}`. Depois apaga os assets antigos (`Artifact delete`, `url` + `path` = id antigo).
5. Lê `data/users/me` (`check`, `runs`) e corrige o que estiver partido.
6. Notificação (PushNotification, sempre, é o briefing diário). Começa pela coisa mais importante. Inclui:
   - empresas que mudaram de zona (P/E 12m, P/E próx. 12m ou PEGY) face ao dia anterior;
   - movimentos diários acima de ±3%;
   - resultados nos próximos 7 dias;
   - 2–3 notícias que realmente importam para as empresas seguidas;
   - erros de dados (ticker sem preço).
   Escreve em português de Portugal. Informação, não recomendações de compra/venda.
