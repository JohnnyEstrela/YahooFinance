# Rotina diária de portefólio

- `watchlist.json` — empresas (`portfolio` ou `watch`) e limiares de valorização.
- `portfolio.py` — `run` (atualiza tudo), `add`, `remove`, `list`.
- `dashboard.html` — dashboard responsivo gerado (abrir no browser).
- `data/latest.json` e `data/history/AAAA-MM-DD.json` — dados diários.

## Limiares (editáveis em `watchlist.json`)
- P/E (12m e próximos 12m): <15 Barato · 15–30 Justo · 30–50 Caro · >50 Muito caro
- PEG: <1 Desconto · 1–2 Justo · >2 Premium. PEGY = P/E forward ÷ (crescimento + dividend yield).

## Execução diária (para o agente da rotina)
1. `pip install yfinance` se necessário.
2. `python portfolio/portfolio.py run`
3. Commit de `portfolio/data` e `portfolio/dashboard.html`.
4. Notificar apenas se houver alertas (movimento ≥5%, mudança de classe de P/E/PEG, erros).

Adicionar empresa: `python portfolio/portfolio.py add NVDA --status watch`
ou `add AAPL --status portfolio --shares 10 --avg-cost 150`.
