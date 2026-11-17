# Consultor Financeiro — daily routine runbook

**Already set up (2026-11-17). Future runs: do NOT rebuild — follow the daily steps below.**

- Dashboard (claude.ai artifact, `db` capability): https://claude.ai/artifact/WPMgcTg7oDdvexpbi5uwXF
- Page source: `portfolio/dashboard.html` (republish with `url` above if the design changes)
- Data script: `portfolio/fetch.py` (needs `pip install yfinance`)

## Database layout (artifact db)
- `tickers/<id>` — written by the owner from the page: `{symbol, list: "portfolio"|"watch", shares?, avgCost?, note?, addedAt}`.
  `<id>` is the symbol with characters outside `[A-Za-z0-9_.-]` replaced by `_`.
- `daily/<YYYY-MM-DD>` — written by the routine, one new doc per day (no version pin needed):
  `{date, updatedAt, indices[], marketNews[], companies{SYMBOL:{...}}, note, alerts[]}`.
  The page shows the newest by `date`.

## Daily steps
1. `pip install -q yfinance`
2. `ArtifactData list` collection `tickers` on the URL above -> collect every `symbol`.
3. `python portfolio/fetch.py <symbols...> --out <scratchpad>/daily.json`
4. Write `note` (2 short paragraphs, PT-PT: market move + what matters for the owner's names) and
   `alerts` (one line per company whose band changed vs yesterday's `daily` doc, earnings that day,
   big moves >5%, relevant news). Compare with the previous `daily/<date>` doc.
5. `ArtifactData set` collection `daily`, doc_id = today, `file_path` = the JSON.
6. PushNotification only if something needs attention (band change, >5% move, earnings, fetch failure).
   A quiet day needs no notification.

## Valuation bands (owner's definition)
- P/E TTM and forward: <15 Barato · 15–30 Fair Value · 30–50 Pricey · >=50 Expensive (anchors 15/20/40/50)
- PEGY = P/E TTM / (expected EPS growth % + dividend yield %): <1 Desconto · 1–2 Fair · >2 Premium
  Growth = analyst next-FY EPS growth (Yahoo `growth_estimates` +1y), fallback current FY, LTG, fwd/ttm EPS.
