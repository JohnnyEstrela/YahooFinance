#!/usr/bin/env python3
"""Atualiza data.json e index.html a partir de watchlist.json (Yahoo Finance).

Uso:
  python portfolio/refresh.py                 # atualiza tudo
  python portfolio/refresh.py add NVDA        # adiciona à watchlist
  python portfolio/refresh.py add NVDA --portfolio --shares 5 --cost 120.5
  python portfolio/refresh.py remove NVDA
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
WATCH = HERE / "watchlist.json"
DATA = HERE / "data.json"
TEMPLATE = HERE / "template.html"
OUT = HERE / "index.html"


def classify_pe(v, b):
    if v is None or v <= 0:
        return "n/a"
    if v < b["cheap"]:
        return "cheap"
    if v < b["fair"]:
        return "fair"
    if v < b["pricey"]:
        return "pricey"
    return "expensive"


def classify_peg(v, b):
    if v is None or v <= 0:
        return "n/a"
    if v < b["discount"]:
        return "discount"
    if v <= b["fair"]:
        return "fair"
    return "premium"


def num(x):
    return round(float(x), 2) if isinstance(x, (int, float)) and x == x else None


def news_item(n):
    c = n.get("content") or n
    link = n.get("link") or (c.get("canonicalUrl") or {}).get("url")
    ts = n.get("providerPublishTime")
    return {
        "title": n.get("title") or c.get("title"),
        "publisher": n.get("publisher") or (c.get("provider") or {}).get("displayName"),
        "link": link,
        "time": ts,
    }


def fetch_company(c, s, yf):
    t = yf.Ticker(c["ticker"])
    info = t.info or {}
    pe, fpe = num(info.get("trailingPE")), num(info.get("forwardPE"))
    peg = num(info.get("trailingPegRatio") or info.get("pegRatio"))
    price = num(info.get("currentPrice") or info.get("regularMarketPrice"))
    row = {
        **c,
        "name": info.get("longName") or info.get("shortName") or c["ticker"],
        "sector": info.get("sector"),
        "currency": info.get("currency"),
        "price": price,
        "change_pct": num(info.get("regularMarketChangePercent")),
        "market_cap": info.get("marketCap"),
        "pe": pe, "forward_pe": fpe, "peg": peg,
        "pe_class": classify_pe(pe, s["pe_bands"]),
        "forward_pe_class": classify_pe(fpe, s["pe_bands"]),
        "peg_class": classify_peg(peg, s["peg_bands"]),
        "dividend_yield_pct": num(info.get("dividendYield")),
        "target_price": num(info.get("targetMeanPrice")),
        "recommendation": info.get("recommendationKey"),
        "week52_low": num(info.get("fiftyTwoWeekLow")),
        "week52_high": num(info.get("fiftyTwoWeekHigh")),
    }
    sh, cost = c.get("shares") or 0, c.get("avg_cost") or 0
    if c.get("status") == "portfolio" and sh and cost and price:
        row["position_value"] = round(sh * price, 2)
        row["pnl_pct"] = round((price / cost - 1) * 100, 2)
    try:
        row["news"] = [news_item(n) for n in yf.Search(c["ticker"], news_count=s["news_per_ticker"]).news]
    except Exception:
        row["news"] = []
    return row


def refresh():
    import yfinance as yf

    cfg = json.loads(WATCH.read_text())
    s = cfg["settings"]
    rows = []
    for c in cfg["companies"]:
        try:
            rows.append(fetch_company(c, s, yf))
        except Exception as e:  # um ticker mau não deve parar o resto
            rows.append({**c, "name": c["ticker"], "error": str(e)[:120], "news": []})
    market = []
    for q in s["market_news_queries"]:
        try:
            market += [news_item(n) for n in yf.Search(q, news_count=4).news]
        except Exception:
            pass
    seen, uniq = set(), []
    for n in market:
        if n["link"] not in seen:
            seen.add(n["link"]); uniq.append(n)
    data = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "settings": s, "companies": rows, "market_news": uniq,
    }
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    OUT.write_text(TEMPLATE.read_text().replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    print(f"{len(rows)} empresas, {len(uniq)} notícias -> {OUT}")


def edit(args):
    cfg = json.loads(WATCH.read_text())
    tk = args.ticker.upper().replace(".", "-") if "." in args.ticker and len(args.ticker.split(".")[-1]) == 1 else args.ticker.upper()
    cfg["companies"] = [c for c in cfg["companies"] if c["ticker"] != tk]
    if args.cmd == "add":
        c = {"ticker": tk, "status": "portfolio" if args.portfolio else "watchlist"}
        if args.shares: c["shares"] = args.shares
        if args.cost: c["avg_cost"] = args.cost
        if args.notes: c["notes"] = args.notes
        cfg["companies"].append(c)
    WATCH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    a = sub.add_parser("add"); a.add_argument("ticker"); a.add_argument("--portfolio", action="store_true")
    a.add_argument("--shares", type=float); a.add_argument("--cost", type=float); a.add_argument("--notes")
    r = sub.add_parser("remove"); r.add_argument("ticker")
    args = p.parse_args()
    if args.cmd:
        edit(args)
    refresh()
