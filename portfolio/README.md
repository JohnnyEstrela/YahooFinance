# Portefólio & Watchlist diária

1. Edita `watchlist.json` — adiciona empresas com `"tipo": "portfolio"` (tenho) ou `"seguir"` (só observo). `acoes` e `preco_medio` são opcionais (calcula P/L).
2. Corre `pip install yfinance && python portfolio/update.py`, ou deixa o workflow `portfolio-daily.yml` correr nos dias úteis.
3. Abre `portfolio/docs/index.html` (responsivo, claro/escuro, filtro, pesquisa e ordenação).

Cada empresa mostra P/E (12m), P/E (próximos 12m) e PEG com etiquetas, mais as últimas notícias do Yahoo Finance.

## Limites (editáveis em `watchlist.json` → `limites`)
| Métrica | Regra |
|---|---|
| P/E | `< 15` Barato · `15–30` Justo · `30–50` Caro · `> 50` Muito caro (P/E ≤ 0 = Prejuízo) |
| PEG | `< 1` Desconto · `1–2` Justo · `> 2` Prémio |

Os intervalos 20–40 do pedido original foram interpretados como pontos de referência (justo ≈ 20, caro ≈ 40); os cortes por defeito são 15 / 30 / 50 e podes ajustá-los.
Se o Yahoo não fornecer o PEG, é calculado como P/E ÷ crescimento de lucros (marcado como "calculado").
