# Rotina diária de portefólio

## Como adicionar empresas
Edita `portfolio/watchlist.json` e acrescenta em `companies`:

```json
{ "ticker": "MSFT", "status": "portfolio", "shares": 5, "avg_cost": 300, "notes": "opcional" }
```
- `status`: `portfolio` (tenho) ou `watching` (quero seguir).
- Tickers fora dos EUA levam sufixo do Yahoo: `GALP.LS`, `EDP.LS`, `SAP.DE`.
- Os limiares (`thresholds`) são editáveis.

## Limiares (interpretação contígua do pedido)
| Métrica | Barato/Desconto | Justo | Caro | Muito caro/Prémio |
|---|---|---|---|---|
| P/E (passado e próx. 12m) | < 15 | 15–30 | 30–50 | ≥ 50 |
| PEG | < 1 | 1–2 | — | > 2 (Prémio) |

P/E ≤ 0 aparece como "Sem lucros"; dados em falta como "n/d".

## Rotina diária
1. `python portfolio/fetch.py` — P/E (trailing), P/E (forward), PEG, preço e notícias (Yahoo Finance via `yfinance`) → `portfolio/data/snapshot.json`.
2. `python portfolio/build_report.py` — gera `portfolio/report/index.html` (responsivo, modo claro/escuro, filtros e pesquisa).
3. Se o Yahoo estiver inacessível, preencher `snapshot.json` com o mesmo formato por outra fonte (ex.: FMP) e correr o passo 2.
4. Resumir ao utilizador: mudanças de classificação (ex.: passou de Justo a Caro), grandes variações e notícias relevantes.

Nota: `data/snapshot.json` incluído no repositório é apenas um exemplo com valores fictícios.
Isto é informação, não aconselhamento financeiro.
