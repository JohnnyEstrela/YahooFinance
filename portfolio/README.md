# Portefólio & Watchlist

Painel diário com as tuas empresas (no portefólio ou só a seguir), P/E, PEG e notícias.

## Como usar
1. Edita `watchlist.json`:
   - `holdings` → empresas que tens (`shares` e `avg_cost` opcionais, mostram o ganho/perda).
   - `watching` → empresas que só segues.
   - Tickers no formato Yahoo (`AAPL`, `BRK-B`, `EDP.LS`, `SAP.DE`).
   - As entradas atuais marcadas como "EXEMPLO" são só placeholders.
2. Corre `pip install yfinance && python portfolio/update.py` (gera `index.html` e `data.json`).
3. Abre `portfolio/index.html` (adapta-se a telemóvel e modo escuro; filtros, pesquisa e ordenação).

## Faixas (configuráveis em `thresholds`)
| Métrica | Faixas |
|---|---|
| P/E (12 m passados) e P/E (próx. 12 m) | < 15 Barato · 15–30 Valor justo · 30–50 Caro · ≥ 50 Muito caro |
| PEG | < 1 Desconto · 1–2 Justo · ≥ 2 Prémio |

Os limites 15/20/40/50 que definiste foram convertidos em faixas contínuas, com o corte
"Justo/Caro" a 30 (ponto médio entre 20 e 40). Muda `limits` e `labels` se preferires outro corte.
P/E negativo aparece como "Sem lucro". Se o Yahoo falhar numa empresa, ficam os últimos dados
bons, marcados "(dados antigos)".

Dados do Yahoo Finance (podem ter atraso). Informação indicativa, não é aconselhamento financeiro.
