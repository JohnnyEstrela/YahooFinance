# Rotina diária de portefólio

- **Adicionar empresa**: `python portfolio/report.py add NVDA --status portfolio --shares 10 --cost 120.5`
  ou `--status watchlist` para empresas só a seguir. (Ou edita `portfolio/watchlist.json` à mão.)
- **Remover**: `python portfolio/report.py remove NVDA`
- **Gerar relatório**: `python portfolio/report.py run` → abre `portfolio/dashboard.html`
  (responsivo, modo claro/escuro, filtros, pesquisa e ordenação).
- **Limiares** (P/E e PEG) editáveis em `watchlist.json` → `thresholds`.
  P/E: <15 Barato · 15–20 Fair value · 20–40 Caro · 40–50 Pricey · >50 Expensive.
  PEG: <1 Desconto · 1–2 Justo · >2 Prémio. O PEG+yield (PEGY = P/E ÷ (crescimento + yield)) aparece como informação adicional.
- Cada execução guarda um snapshot em `portfolio/history/` e destaca mudanças de classificação.
- `.github/workflows/daily-portfolio.yml` corre isto nos dias úteis e faz commit do dashboard.
