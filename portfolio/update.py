#!/usr/bin/env python3
"""Atualiza data.json e dashboard.html a partir de watchlist.json (dados: Yahoo Finance)."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent


def classify(value, bands):
    if value is None or value <= 0:
        return {"label": "n/d", "tone": "none"}
    for b in bands:
        if b["limit"] is None or value < b["limit"]:
            return {"label": b["label"], "tone": b["tone"]}
    return {"label": "n/d", "tone": "none"}


def num(x):
    return float(x) if isinstance(x, (int, float)) and x == x else None


def news_items(query, n):
    try:
        items = yf.Search(query, news_count=n).news
    except Exception:
        return []
    out = []
    for it in items[:n]:
        ts = it.get("providerPublishTime")
        out.append({
            "title": it.get("title"),
            "publisher": it.get("publisher"),
            "link": it.get("link"),
            "date": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d") if ts else None,
        })
    return out


def fetch(entry, group, cfg):
    sym = entry["ticker"].upper()
    if sym.count(".") == 1 and len(sym.split(".")[1]) == 1:  # BRK.B -> BRK-B
        sym = sym.replace(".", "-")
    row = {"ticker": sym, "group": group, "shares": entry.get("shares"),
           "avg_cost": entry.get("avg_cost"), "error": None}
    try:
        info = yf.Ticker(sym).info
        price = num(info.get("currentPrice") or info.get("regularMarketPrice"))
        pe, fpe = num(info.get("trailingPE")), num(info.get("forwardPE"))
        peg = num(info.get("trailingPegRatio")) or num(info.get("pegRatio"))
        growth = num(info.get("earningsGrowth"))
        if peg is None and fpe and growth and growth > 0:
            peg = fpe / (growth * 100)
        dy = num(info.get("dividendYield"))  # já em %
        pegy = fpe / (growth * 100 + (dy or 0)) if fpe and growth and growth > 0 else None
        row.update(
            name=info.get("shortName") or sym, currency=info.get("currency"), price=price,
            change_pct=num(info.get("regularMarketChangePercent")), sector=info.get("sector"),
            market_cap=num(info.get("marketCap")), pe=pe, fpe=fpe, peg=peg, pegy=pegy,
            dividend_yield=dy, high52=num(info.get("fiftyTwoWeekHigh")),
            low52=num(info.get("fiftyTwoWeekLow")), target=num(info.get("targetMeanPrice")),
            recommendation=info.get("recommendationKey"),
            pe_class=classify(pe, cfg["pe"]), fpe_class=classify(fpe, cfg["pe"]),
            peg_class=classify(peg, cfg["peg"]),
            news=news_items(f"{info.get('shortName') or sym} {sym}", cfg["news_per_ticker"]),
        )
        if price and row["avg_cost"] and row["shares"]:
            row["pnl_pct"] = (price / row["avg_cost"] - 1) * 100
            row["value"] = price * row["shares"]
    except Exception as e:  # um ticker mau não deve estragar o resto
        row.update(name=sym, error=str(e)[:120], news=[])
    return row


def main():
    wl = json.loads((HERE / "watchlist.json").read_text())
    cfg = json.loads((HERE / "config.json").read_text())
    rows = [fetch(e, "holdings", cfg) for e in wl.get("holdings", [])]
    rows += [fetch(e, "watching", cfg) for e in wl.get("watching", [])]
    market = [{"query": q, "items": news_items(q, 4)} for q in wl.get("market_news_queries", [])]
    data = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "companies": rows, "market_news": market, "bands": {"pe": cfg["pe"], "peg": cfg["peg"]}}
    (HERE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    tpl = (HERE / "template.html").read_text()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    (HERE / "dashboard.html").write_text(tpl.replace("/*__DATA__*/null", payload))
    bad = [r["ticker"] for r in rows if r["error"]]
    print(f"{len(rows)} empresas atualizadas; erros: {bad or 'nenhum'}")
    return 1 if bad and len(bad) == len(rows) else 0


if __name__ == "__main__":
    sys.exit(main())
