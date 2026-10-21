#!/usr/bin/env python3
"""Atualiza o portefólio: vai buscar dados ao Yahoo Finance e gera index.html + data.json.

Uso: python3 portfolio/update.py   (requer: pip install yfinance)
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent


def num(v):
    return v if isinstance(v, (int, float)) and v == v else None


def classify_pe(v, th):
    if v is None or v <= 0:
        return "n/d"
    if v < th["barato"]:
        return "Barato"
    if v < th["justo"]:
        return "Justo"
    if v < th["caro"]:
        return "Caro"
    return "Muito caro"


def classify_peg(v, th):
    if v is None or v <= 0:
        return "n/d"
    if v < th["desconto"]:
        return "Desconto"
    if v <= th["justo"]:
        return "Justo"
    return "Prémio"


def news_for(ticker, n=4):
    try:
        items = yf.Search(ticker, news_count=n).news
    except Exception:
        return []
    out = []
    for it in items[:n]:
        out.append({
            "title": it.get("title"),
            "publisher": it.get("publisher"),
            "link": it.get("link"),
            "time": it.get("providerPublishTime"),
        })
    return out


def fetch(entry, kind, cfg):
    tk = entry["ticker"].strip().upper()
    if tk.endswith((".A", ".B")):  # classes de ações US: BRK.B -> BRK-B
        tk = tk[:-2] + "-" + tk[-1]
    row = {"ticker": tk, "kind": kind, "note": entry.get("note", "")}
    try:
        info = yf.Ticker(tk).info
    except Exception as e:
        row["error"] = str(e)[:120]
        return row
    price = num(info.get("currentPrice")) or num(info.get("regularMarketPrice"))
    pe, fpe = num(info.get("trailingPE")), num(info.get("forwardPE"))
    peg = num(info.get("trailingPegRatio")) or num(info.get("pegRatio"))
    growth = num(info.get("earningsGrowth"))
    if peg is None and pe and growth and growth > 0:
        peg = pe / (growth * 100)
    dy = num(info.get("dividendYield"))  # Yahoo já devolve em %
    row.update({
        "name": info.get("longName") or info.get("shortName") or tk,
        "currency": info.get("currency"),
        "sector": info.get("sector"),
        "price": price,
        "change_pct": num(info.get("regularMarketChangePercent")),
        "market_cap": num(info.get("marketCap")),
        "pe": pe, "pe_class": classify_pe(pe, cfg["pe"]),
        "fpe": fpe, "fpe_class": classify_pe(fpe, cfg["pe"]),
        "peg": peg, "peg_class": classify_peg(peg, cfg["peg"]),
        "div_yield": dy,
        "target": num(info.get("targetMeanPrice")),
        "recommendation": info.get("recommendationKey"),
        "week52_low": num(info.get("fiftyTwoWeekLow")),
        "week52_high": num(info.get("fiftyTwoWeekHigh")),
    })
    sh, cost = num(entry.get("shares")), num(entry.get("avg_cost"))
    if kind == "holding" and sh and cost and price:
        row.update({"shares": sh, "avg_cost": cost, "value": sh * price,
                    "pl_pct": (price / cost - 1) * 100})
    row["news"] = news_for(tk)
    return row


def main():
    cfg = json.loads((HERE / "portfolio.json").read_text())
    rows = []
    for kind, key in (("holding", "holdings"), ("watch", "watchlist")):
        for e in cfg.get(key, []):
            rows.append(fetch(e, kind, cfg["thresholds"]))
            time.sleep(0.3)
    data = {"updated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
            "thresholds": cfg["thresholds"], "rows": rows}
    (HERE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    html = (HERE / "template.html").read_text().replace(
        "/*DATA*/null", json.dumps(data, ensure_ascii=False))
    (HERE / "index.html").write_text(html)
    ok = sum(1 for r in rows if "error" not in r)
    print(f"{ok}/{len(rows)} empresas atualizadas -> portfolio/index.html")


if __name__ == "__main__":
    main()
