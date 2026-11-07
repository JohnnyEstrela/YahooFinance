#!/usr/bin/env python3
"""Atualiza o dashboard: lê watchlist.json, vai buscar dados ao Yahoo Finance
(yfinance) e escreve data.js / data.json que o index.html lê.

Uso:  pip install yfinance && python portfolio/update.py
"""
import json, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent


def num(v):
    return v if isinstance(v, (int, float)) and v == v else None


def classify_pe(pe, th):
    if pe is None or pe <= 0:
        return "na"  # sem lucros / sem dados
    if pe < th["cheap"]:
        return "cheap"
    if pe < th["fair"]:
        return "fair"
    if pe <= th["pricey"]:
        return "pricey"
    return "expensive"


def classify_peg(peg, th):
    if peg is None or peg <= 0:
        return "na"
    if peg < th["discount"]:
        return "discount"
    if peg <= th["fair"]:
        return "fair"
    return "premium"


def retry(fn, tries=3):
    for i in range(tries):
        try:
            return fn()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def parse_news(items, limit=6):
    out = []
    for n in items or []:
        c = n.get("content") or n
        url = ((c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url")
               or c.get("link"))
        if not c.get("title") or not url:
            continue
        out.append({
            "title": c["title"],
            "summary": c.get("summary") or "",
            "url": url,
            "source": (c.get("provider") or {}).get("displayName") or c.get("publisher") or "",
            "date": c.get("pubDate") or "",
            "tickers": [t["symbol"] for t in (c.get("finance") or {}).get("stockTickers", [])],
        })
    return out[:limit]


def fetch_company(entry, th):
    sym = entry["symbol"].upper()
    row = {"symbol": sym, "status": entry.get("status", "watchlist"),
           "shares": entry.get("shares"), "avg_cost": entry.get("avg_cost"),
           "notes": entry.get("notes", ""), "error": None}
    try:
        t = yf.Ticker(sym)
        i = retry(lambda: t.info)
        price = num(i.get("currentPrice")) or num(i.get("regularMarketPrice"))
        pe, fpe = num(i.get("trailingPE")), num(i.get("forwardPE"))
        # yfinance devolve dividendYield já em % (0.32 = 0.32%)
        dy = num(i.get("dividendYield")) or 0.0
        peg = num(i.get("trailingPegRatio")) or num(i.get("pegRatio"))
        # crescimento implícito (%) = P/E ÷ PEG; fallback: crescimento trimestral de lucros
        growth = (pe / peg) if (pe and peg and peg > 0) else None
        if growth is None and num(i.get("earningsGrowth")) is not None:
            growth = i["earningsGrowth"] * 100
        pegy = None
        base_pe = fpe or pe
        if base_pe and base_pe > 0 and growth is not None and growth + dy > 0:
            pegy = base_pe / (growth + dy)
        prev = num(i.get("previousClose"))
        row.update({
            "name": i.get("shortName") or i.get("longName") or sym,
            "sector": i.get("sector") or i.get("quoteType") or "",
            "currency": i.get("currency") or "",
            "price": price,
            "change_pct": ((price / prev - 1) * 100) if price and prev else None,
            "market_cap": num(i.get("marketCap")),
            "pe": pe, "forward_pe": fpe, "peg": peg, "pegy": pegy,
            "growth": growth, "dividend_yield": dy,
            "week52_low": num(i.get("fiftyTwoWeekLow")),
            "week52_high": num(i.get("fiftyTwoWeekHigh")),
            "target": num(i.get("targetMeanPrice")),
            "recommendation": i.get("recommendationKey") or "",
            "pe_class": classify_pe(pe, th["pe"]),
            "fpe_class": classify_pe(fpe, th["pe"]),
            "peg_class": classify_peg(peg if peg is not None else pegy, th["peg"]),
            "pegy_class": classify_peg(pegy, th["peg"]),
        })
        if row["shares"] and price:
            row["position_value"] = row["shares"] * price
            if row["avg_cost"]:
                row["pnl_pct"] = (price / row["avg_cost"] - 1) * 100
        row["news"] = parse_news(retry(lambda: t.news))
    except Exception as e:  # um ticker mau não pode estragar o resto
        row["error"] = f"{type(e).__name__}: {e}"[:200]
        row.setdefault("name", sym)
    return row


def fetch_market(symbols):
    out = []
    for s in symbols:
        try:
            fi = yf.Ticker(s).fast_info
            last, prev = fi["lastPrice"], fi["previousClose"]
            out.append({"symbol": s, "price": last, "change_pct": (last / prev - 1) * 100})
        except Exception:
            out.append({"symbol": s, "price": None, "change_pct": None})
    return out


def main():
    cfg = json.loads((HERE / "watchlist.json").read_text(encoding="utf-8"))
    th = cfg["thresholds"]
    seen, entries = set(), []
    for e in cfg["companies"]:
        s = e["symbol"].upper().strip()  # classes: BRK-B (não BRK.B)
        if s not in seen:
            seen.add(s)
            entries.append({**e, "symbol": s})
    with ThreadPoolExecutor(4) as ex:
        companies = list(ex.map(lambda e: fetch_company(e, th), entries))
    market = fetch_market(cfg.get("market", []))
    try:
        mnews = parse_news(yf.Ticker("^GSPC").news, 8)
    except Exception:
        mnews = []
    data = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "thresholds": th, "market": market, "market_news": mnews, "companies": companies}
    (HERE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    # data.js permite abrir index.html por duplo clique (file://) sem servidor
    (HERE / "data.js").write_text("window.PORTFOLIO_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    bad = [c["symbol"] for c in companies if c["error"]]
    print(f"OK: {len(companies)} empresas, {len(bad)} com erro {bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
