#!/usr/bin/env python3
"""Atualiza data.json e index.html a partir de watchlist.json (via yfinance).

Uso: python portfolio/update.py [--demo]
"""
import json, sys, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
LABELS = ["Barato", "Justo", "Caro", "Muito caro"]


def pe_label(v, t):
    if v is None or v <= 0:
        return "n/d"
    if v < t["cheap"]:
        return LABELS[0]
    if v < t["fair"]:
        return LABELS[1]
    if v < t["pricey"]:
        return LABELS[2]
    return LABELS[3]


def peg_label(v, t):
    if v is None or v <= 0:
        return "n/d"
    return "Desconto" if v < t["discount"] else "Justo" if v <= t["fair"] else "Premium"


def num(x):
    return float(x) if isinstance(x, (int, float)) and x == x else None


def fetch(c):
    import yfinance as yf
    t = yf.Ticker(c["ticker"])
    i = t.info
    price = num(i.get("currentPrice") or i.get("regularMarketPrice"))
    pe, fpe = num(i.get("trailingPE")), num(i.get("forwardPE"))
    growth = num(i.get("earningsGrowth"))
    yld = num(i.get("dividendYield"))  # yfinance recente: já em %
    peg = num(i.get("trailingPegRatio") or i.get("pegRatio"))
    if peg is None and fpe and growth and growth > 0:
        peg = fpe / (growth * 100)
    pegy = fpe / (growth * 100 + (yld or 0)) if fpe and growth and growth > 0 else None
    news = []
    for n in (t.news or [])[:5]:
        n = n.get("content", n)
        url = (n.get("canonicalUrl") or n.get("clickThroughUrl") or {}).get("url") or n.get("link")
        news.append({"title": n.get("title"), "url": url,
                     "publisher": (n.get("provider") or {}).get("displayName") or n.get("publisher"),
                     "date": n.get("pubDate") or n.get("providerPublishTime")})
    return {"name": i.get("longName") or c["ticker"], "price": price, "currency": i.get("currency"),
            "pe": pe, "fpe": fpe, "peg": peg, "pegy": pegy, "yield": yld,
            "sector": i.get("sector"), "news": news}


def demo(c):
    return {"name": c["ticker"] + " (demo)", "price": 200.0, "currency": "USD", "pe": 32.1, "fpe": 27.4,
            "peg": 2.3, "pegy": 2.1, "yield": 0.5, "sector": "Demo",
            "news": [{"title": "Notícia de exemplo", "url": "#", "publisher": "Demo", "date": None}]}


def main():
    cfg = json.loads((HERE / "watchlist.json").read_text())
    th, rows = cfg["thresholds"], []
    for c in cfg["companies"]:
        try:
            d = demo(c) if "--demo" in sys.argv else fetch(c)
        except Exception as e:  # uma falha não pára as restantes
            d = {"name": c["ticker"], "error": str(e), "news": []}
        d.update(ticker=c["ticker"], status=c.get("status", "watching"), notes=c.get("notes", ""))
        if c.get("shares") and d.get("price"):
            d["shares"], d["avg_cost"] = c["shares"], c.get("avg_cost")
            d["value"] = c["shares"] * d["price"]
            if c.get("avg_cost"):
                d["pnl_pct"] = (d["price"] / c["avg_cost"] - 1) * 100
        d["pe_label"], d["fpe_label"] = pe_label(d.get("pe"), th["pe"]), pe_label(d.get("fpe"), th["pe"])
        d["peg_label"] = peg_label(d.get("peg"), th["peg"])
        rows.append(d)
    data = {"updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "thresholds": th, "companies": rows}
    (HERE / "data.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    html = (HERE / "template.html").read_text().replace("/*DATA*/null", json.dumps(data, ensure_ascii=False))
    (HERE / "index.html").write_text(html)
    print(f"{len(rows)} empresas atualizadas")


if __name__ == "__main__":
    main()
