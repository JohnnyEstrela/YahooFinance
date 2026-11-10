#!/usr/bin/env python3
"""Gera o dashboard diário (portfolio/index.html + data.json) a partir de portfolio.json.

Uso:  python portfolio/build.py            (requer: pip install yfinance)
Para adicionar empresas basta editar portfolio.json e voltar a correr.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent
NEWS_PER_TICKER = 4


def classify_pe(v, t):
    if v is None or v <= 0:
        return "na"
    if v < t["cheap"]:
        return "cheap"
    if v < t["fair"]:
        return "fair"
    if v < t["pricey"]:
        return "pricey"
    return "expensive"


def classify_peg(v, t):
    if v is None or v <= 0:
        return "na"
    if v < t["discount"]:
        return "discount"
    if v <= t["fair"]:
        return "fair"
    return "premium"


def num(x):
    return x if isinstance(x, (int, float)) and x == x else None


def parse_news(item):
    c = item.get("content", item)
    url = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or c.get("link")
    return {
        "title": c.get("title"),
        "publisher": (c.get("provider") or {}).get("displayName") or c.get("publisher"),
        "date": c.get("pubDate") or c.get("providerPublishTime"),
        "url": url,
    }


def fetch(entry, cfg):
    sym = entry["ticker"].upper()
    if len(sym.split(".")[-1]) == 1:  # BRK.B -> BRK-B (mantém EDP.LS)
        sym = sym.replace(".", "-")
    out = {**entry, "ticker": sym, "error": None}
    try:
        tk = yf.Ticker(sym)
        info = tk.info or {}
        price = num(info.get("currentPrice") or info.get("regularMarketPrice"))
        pe, fpe = num(info.get("trailingPE")), num(info.get("forwardPE"))
        peg = num(info.get("trailingPegRatio") or info.get("pegRatio"))
        growth = num(info.get("earningsGrowth"))
        if peg is None and fpe and growth and growth > 0:
            peg = round(fpe / (growth * 100), 2)  # estimativa
        dy = num(info.get("dividendYield"))
        out.update(
            name=info.get("shortName") or sym,
            sector=info.get("sector"),
            currency=info.get("currency"),
            price=price,
            change_pct=num(info.get("regularMarketChangePercent")),
            market_cap=num(info.get("marketCap")),
            pe=pe, fwd_pe=fpe, peg=peg,
            div_yield=dy,  # já em %
            target=num(info.get("targetMeanPrice")),
            rating=info.get("recommendationKey"),
            hi52=num(info.get("fiftyTwoWeekHigh")), lo52=num(info.get("fiftyTwoWeekLow")),
            pe_class=classify_pe(pe, cfg["pe"]),
            fwd_pe_class=classify_pe(fpe, cfg["pe"]),
            peg_class=classify_peg(peg, cfg["peg"]),
        )
        if price and entry.get("shares"):
            out["value"] = round(price * entry["shares"], 2)
            if entry.get("avg_cost"):
                out["pl_pct"] = round((price / entry["avg_cost"] - 1) * 100, 2)
        out["news"] = [n for n in map(parse_news, (tk.news or [])[:NEWS_PER_TICKER]) if n["title"]]
    except Exception as e:  # um ticker mau não pode estragar o relatório
        out["error"] = f"{type(e).__name__}: {e}"[:200]
        out.setdefault("news", [])
    return out


def main():
    cfg = json.loads((HERE / "portfolio.json").read_text(encoding="utf-8"))
    rows = []
    for h in cfg["holdings"]:
        rows.append(fetch(h, cfg["thresholds"]))
        time.sleep(0.5)
    data = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "thresholds": cfg["thresholds"],
        "companies": rows,
    }
    (HERE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tpl = (HERE / "template.html").read_text(encoding="utf-8")
    (HERE / "index.html").write_text(
        tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False)), encoding="utf-8"
    )
    bad = [r["ticker"] for r in rows if r["error"] or r.get("price") is None]
    print(f"{len(rows)} empresas; sem dados: {bad or 'nenhuma'}")


if __name__ == "__main__":
    main()
