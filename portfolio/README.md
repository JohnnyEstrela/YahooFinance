# Consultor de Portefólio

Dashboard diário do teu portefólio e das empresas que segues (dados Yahoo Finance + notícias).

## Uso
```bash
pip install yfinance
python portfolio/build_dashboard.py                      # atualiza e gera portfolio/dashboard.html
python portfolio/build_dashboard.py add TSLA --lista watchlist   # ou holdings
python portfolio/build_dashboard.py remove TSLA
```
Ou edita `portfolio.json` à mão (`holdings` = no portefólio, `watchlist` = a seguir; opcional `shares`, `avg_cost`, `notes`).

## Indicadores e escalas (editáveis em `portfolio.json` → `thresholds`)
| Indicador | Escala |
|---|---|
| P/E últimos 12m | <15 Barato · 15–20 Justo · 20–50 Pricey · >50 Expensive |
| P/E próximos 12m | igual |
| PEG | <1 Desconto · 1–2 Justo · >2 Premium |

P/E negativo = "Prejuízo"; PEG ausente é calculado como P/E futuro ÷ crescimento de lucros quando possível.
Se o Yahoo falhar para um ticker, mantém-se o último valor bom (marcado como antigo).
O dashboard é um único HTML (filtros portefólio/a seguir, ordenação, pesquisa, tema claro/escuro, responsivo).
