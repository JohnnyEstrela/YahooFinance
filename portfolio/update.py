#!/usr/bin/env python3
"""Rotina diária: lê watchlist.json, vai buscar dados ao Yahoo Finance (yfinance),
classifica P/E e PEG e gera portfolio/index.html (dashboard estático) + data.json.

Uso:  python portfolio/update.py            # dados reais
      python portfolio/update.py --offline  # re-renderiza a partir de data.json
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent


def classify_pe(v, t):
    if v is None:
        return None
    if v <= 0:
        return "loss"
    if v < t["cheap"]:
        return "cheap"
    if v <= t["fair"]:
        return "fair"
    if v <= t["pricey"]:
        return "pricey"
    return "expensive"


def classify_peg(v, t):
    if v is None or v <= 0:
        return None
    if v < t["discount"]:
        return "discount"
    if v <= t["fair"]:
        return "fair"
    return "premium"


def num(x):
    return x if isinstance(x, (int, float)) and x == x else None


def fetch(entry, cfg):
    import yfinance as yf

    sym = entry["ticker"].upper()
    if re.fullmatch(r"[A-Z]+\.[A-Z]", sym):  # BRK.B -> BRK-B
        sym = sym.replace(".", "-")
    t = yf.Ticker(sym)
    info = t.info or {}
    price = num(info.get("currentPrice") or info.get("regularMarketPrice"))
    pe, fpe = num(info.get("trailingPE")), num(info.get("forwardPE"))
    growth = num(info.get("earningsGrowth"))  # fração
    dy = num(info.get("dividendYield"))  # yfinance 1.x devolve em %
    peg = num(info.get("trailingPegRatio")) or num(info.get("pegRatio"))
    if peg is None and fpe and growth and growth > 0:
        peg = fpe / (growth * 100)
    pegy = None
    g = (growth * 100) if growth else None
    if (fpe or pe) and g is not None and g + (dy or 0) > 0:
        pegy = (fpe or pe) / (g + (dy or 0))
    news = []
    for n in (t.news or [])[: cfg["news_per_company"]]:
        c = n.get("content", n)
        url = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or c.get("link")
        news.append({"title": c.get("title"), "publisher": (c.get("provider") or {}).get("displayName") or c.get("publisher"),
                     "date": c.get("pubDate") or c.get("providerPublishTime"), "url": url})
    prev = num(info.get("regularMarketPreviousClose"))
    return {
        "name": info.get("shortName") or sym, "sector": info.get("sector"), "currency": info.get("currency"),
        "price": price, "day_change_pct": ((price / prev - 1) * 100) if price and prev else None,
        "pe": pe, "fwd_pe": fpe, "peg": peg, "pegy": pegy, "growth_pct": g, "div_yield_pct": dy,
        "target": num(info.get("targetMeanPrice")), "rec": info.get("recommendationKey"),
        "w52_low": num(info.get("fiftyTwoWeekLow")), "w52_high": num(info.get("fiftyTwoWeekHigh")),
        "news": news,
    }


def build(cfgfile):
    cfg = cfgfile["settings"]
    rows, errors = [], []
    for e in cfgfile["companies"]:
        row = {**e}
        try:
            row.update(fetch(e, cfg))
        except Exception as ex:  # noqa: BLE001
            errors.append(f"{e['ticker']}: {ex.__class__.__name__}")
            row["error"] = True
            row.setdefault("name", e["ticker"])
        row["pe_class"] = classify_pe(row.get("pe"), cfg["pe"])
        row["fwd_pe_class"] = classify_pe(row.get("fwd_pe"), cfg["pe"])
        row["peg_class"] = classify_peg(row.get("peg"), cfg["peg"])
        row["pegy_class"] = classify_peg(row.get("pegy"), cfg["peg"])
        if row.get("shares") and row.get("price"):
            row["value"] = row["shares"] * row["price"]
            if row.get("avg_cost"):
                row["pl_pct"] = (row["price"] / row["avg_cost"] - 1) * 100
        rows.append(row)
    return {"updated": datetime.now(timezone.utc).isoformat(timespec="minutes"), "settings": cfg, "rows": rows, "errors": errors}


def main():
    data_path = HERE / "data.json"
    if "--offline" in sys.argv:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    else:
        data = build(json.loads((HERE / "watchlist.json").read_text(encoding="utf-8")))
        if data["errors"] and data_path.exists():  # reaproveita último valor bom por ticker
            old = {r["ticker"]: r for r in json.loads(data_path.read_text(encoding="utf-8"))["rows"] if not r.get("error")}
            data["rows"] = [old.get(r["ticker"], r) if r.get("error") else r for r in data["rows"]]
        data_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    html = (HERE / "template.html").read_text(encoding="utf-8").replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
    (HERE / "index.html").write_text(html, encoding="utf-8")
    print(f"{len(data['rows'])} empresas, {len(data['errors'])} erros -> portfolio/index.html")


if __name__ == "__main__":
    main()
