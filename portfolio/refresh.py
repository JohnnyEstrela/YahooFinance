#!/usr/bin/env python3
"""Rotina diária: gere docs/data.json e docs/index.html a partir de watchlist.json.

Uso:
  python portfolio/refresh.py                      # actualiza tudo
  python portfolio/refresh.py add NVDA --portfolio --shares 5 --cost 120
  python portfolio/refresh.py add TSLA             # empresa a seguir
  python portfolio/refresh.py remove TSLA
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = ROOT / "docs"
sys.path.insert(0, str(HERE))
from valuation import DEFAULT_THRESHOLDS, classify_peg, classify_pe  # noqa: E402


def load(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def normalize(ticker: str) -> str:
    t = ticker.strip().upper()
    return t.replace(".", "-") if len(t.split(".")[-1]) == 1 else t  # BRK.B -> BRK-B


def num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def google_news(query: str, limit: int, lang: str = "pt-PT") -> list[dict]:
    country = lang.split("-")[-1]
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query + " when:2d", "hl": lang, "gl": country, "ceid": f"{country}:{lang.split('-')[0]}"}
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            root = ET.fromstring(r.read())
    except Exception as exc:  # rede/parse: não rebenta a rotina
        print(f"  aviso: notícias '{query}': {exc}", file=sys.stderr)
        return []
    items = []
    for it in root.iter("item"):
        try:
            when = parsedate_to_datetime(it.findtext("pubDate")).isoformat()
        except Exception:
            when = None
        src = it.find("source")
        items.append(
            {
                "title": html.unescape(it.findtext("title") or ""),
                "url": it.findtext("link"),
                "source": src.text if src is not None else "",
                "date": when,
            }
        )
        if len(items) >= limit:
            break
    return items


def yahoo_news(ticker: str, limit: int) -> list[dict]:
    import yfinance as yf

    out = []
    try:
        for n in yf.Search(ticker, news_count=limit).news[:limit]:
            ts = n.get("providerPublishTime")
            out.append(
                {
                    "title": n.get("title", ""),
                    "url": n.get("link"),
                    "source": n.get("publisher", "Yahoo Finance"),
                    "date": dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat() if ts else None,
                }
            )
    except Exception as exc:
        print(f"  aviso: yahoo news {ticker}: {exc}", file=sys.stderr)
    return out


def merge_news(*lists: list[dict], limit: int) -> list[dict]:
    seen, merged = set(), []
    for item in (i for lst in lists for i in lst):
        key = item["title"].lower()[:60]
        if item.get("url") and key not in seen:
            seen.add(key)
            merged.append(item)
    merged.sort(key=lambda i: i.get("date") or "", reverse=True)
    return merged[:limit]


def fetch_company(entry: dict, cfg: dict) -> dict:
    import yfinance as yf

    ticker = normalize(entry["ticker"])
    th = cfg.get("thresholds", DEFAULT_THRESHOLDS)
    rec = {
        "ticker": ticker,
        "status": entry.get("status", "watch"),
        "shares": entry.get("shares"),
        "avg_cost": entry.get("avg_cost"),
        "notes": entry.get("notes", ""),
        "error": None,
    }
    info = {}
    for attempt in range(4):  # Yahoo limita pedidos de vez em quando
        try:
            info = yf.Ticker(ticker).info or {}
        except Exception as exc:
            rec["error"] = str(exc)[:200]
        if info.get("currentPrice") or info.get("regularMarketPrice"):
            rec["error"] = None
            break
        time.sleep(2 * 2**attempt)
    price = num(info.get("currentPrice") or info.get("regularMarketPrice"))
    prev = num(info.get("previousClose") or info.get("regularMarketPreviousClose"))
    pe_ttm, pe_fwd = num(info.get("trailingPE")), num(info.get("forwardPE"))
    eps_ttm, eps_fwd = num(info.get("trailingEps")), num(info.get("forwardEps"))
    if price and pe_ttm is None and eps_ttm and eps_ttm > 0:
        pe_ttm = price / eps_ttm
    if price and pe_fwd is None and eps_fwd and eps_fwd > 0:
        pe_fwd = price / eps_fwd
    peg = num(info.get("trailingPegRatio")) or num(info.get("pegRatio"))
    div_yield = num(info.get("dividendYield"))  # yfinance recente: já em %
    rec.update(
        name=info.get("longName") or info.get("shortName") or ticker,
        sector=info.get("sector"),
        currency=info.get("currency"),
        price=price,
        change_pct=round((price / prev - 1) * 100, 2) if price and prev else None,
        pe_ttm=pe_ttm,
        pe_fwd=pe_fwd,
        peg=peg,
        pe_ttm_class=classify_pe(pe_ttm, th["pe"]),
        pe_fwd_class=classify_pe(pe_fwd, th["pe"]),
        peg_class=classify_peg(peg, th["peg"]),
        market_cap=num(info.get("marketCap")),
        eps_ttm=eps_ttm,
        eps_fwd=eps_fwd,
        earnings_growth=num(info.get("earningsGrowth")),
        revenue_growth=num(info.get("revenueGrowth")),
        profit_margin=num(info.get("profitMargins")),
        dividend_yield=div_yield,
        beta=num(info.get("beta")),
        week52_low=num(info.get("fiftyTwoWeekLow")),
        week52_high=num(info.get("fiftyTwoWeekHigh")),
        target_price=num(info.get("targetMeanPrice")),
        recommendation=info.get("recommendationKey"),
    )
    if rec["status"] == "portfolio" and price and rec["shares"]:
        rec["position_value"] = round(price * rec["shares"], 2)
        if rec["avg_cost"]:
            rec["pnl_pct"] = round((price / rec["avg_cost"] - 1) * 100, 2)
    n = cfg.get("news_per_ticker", 4)
    rec["news"] = merge_news(
        google_news(f"{rec['name']} {ticker} stock", n, "en-US"),
        yahoo_news(ticker, n),
        limit=n,
    )
    if price is None and not rec["error"]:
        rec["error"] = "Sem dados de cotação (ticker válido?)"
    return rec


def refresh() -> None:
    cfg, wl = load("config.json"), load("watchlist.json")
    companies = []
    for entry in wl["companies"]:
        print(f"A obter {entry['ticker']}…")
        companies.append(fetch_company(entry, cfg))
    market = {}
    for q in cfg.get("market_news_queries", []):
        market[q] = google_news(q, 5, "pt-PT" if any(c in q for c in "çãõ") or "mercados" in q else "en-US")
    data = {
        "title": cfg.get("title", "Portefólio"),
        "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
        "thresholds": cfg.get("thresholds", DEFAULT_THRESHOLDS),
        "companies": companies,
        "market_news": [n for lst in market.values() for n in lst][:12],
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    template = (HERE / "template.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    (OUT / "index.html").write_text(template.replace("/*__DATA__*/null", payload), encoding="utf-8")
    print(f"Feito: {len(companies)} empresas -> docs/index.html")


def edit_watchlist(args) -> None:
    path = HERE / "watchlist.json"
    wl = load("watchlist.json")
    t = normalize(args.ticker)
    wl["companies"] = [c for c in wl["companies"] if normalize(c["ticker"]) != t]
    if args.cmd == "add":
        entry = {"ticker": t, "status": "portfolio" if args.portfolio else "watch"}
        if args.shares is not None:
            entry["shares"] = args.shares
        if args.cost is not None:
            entry["avg_cost"] = args.cost
        if args.notes:
            entry["notes"] = args.notes
        wl["companies"].append(entry)
    path.write_text(json.dumps(wl, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{args.cmd}: {t}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd")
    a = sub.add_parser("add")
    a.add_argument("ticker")
    a.add_argument("--portfolio", action="store_true", help="no portefólio (senão: a seguir)")
    a.add_argument("--shares", type=float)
    a.add_argument("--cost", type=float, help="preço médio de compra")
    a.add_argument("--notes")
    r = sub.add_parser("remove")
    r.add_argument("ticker")
    args = p.parse_args()
    if args.cmd in ("add", "remove"):
        edit_watchlist(args)
    refresh()


if __name__ == "__main__":
    main()
