# Portefólio & Watchlist

Rotina diária que atualiza métricas e notícias das empresas que tens (ou segues).

- `watchlist.json` — as tuas empresas (`status`: `portfolio` ou `seguir`; `shares`/`avg_cost` opcionais).
- `thresholds.json` — limiares das etiquetas.
- `update.py` — vai buscar dados ao Yahoo Finance (yfinance) e escreve `data.json`.
- `index.html` — dashboard adaptável (telemóvel/desktop, tema claro/escuro, cartões/lista, filtros, ordenação, limiares editáveis, gerador de linha para adicionar empresas).
- `.github/workflows/portfolio-daily.yml` — corre `update.py` nos dias úteis e faz commit do `data.json`.

## Etiquetas
| Métrica | Barato / Discount | Fair | Pricey | Expensive / Premium |
|---|---|---|---|---|
| P/E 12m e próx. 12m | < 15 | 15–30 (ref. 20) | 30–50 (ref. 40) | > 50 |
| PEG | < 1 | 1–2 | — | > 2 |

Os cortes 30 (fair→pricey) são o ponto intermédio entre as tuas referências 20 e 40; ajusta em `thresholds.json`.
P/E ou PEG negativo/em falta aparece como `n/d`.

## Usar
```
pip install yfinance && python portfolio/update.py
cd portfolio && python -m http.server   # abrir http://localhost:8000
```
