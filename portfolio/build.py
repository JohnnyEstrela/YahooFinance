#!/usr/bin/env python3
"""Consultor financeiro diario: le watchlist.json, vai buscar dados ao Yahoo
Finance (yfinance), classifica P/E e PEG e gera data.json + index.html."""
import json, sys, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent


def classify_pe(v):
    if v is None: return ("n/d", "nd")
    if v <= 0: return ("Prejuízo", "bad")
    if v < 15: return ("Barato", "cheap")
    if v <= 30: return ("Valor justo", "fair")   # 20 = justo
    if v <= 50: return ("Pricey", "pricey")      # 40 = pricey
    return ("Expensive", "exp")


def classify_peg(v):
    if v is None: return ("n/d", "nd")
    if v <= 0: return ("n/a", "nd")
    if v < 1: return ("Desconto", "cheap")
    if v <= 2: return ("Justo", "fair")
    return ("Premium", "exp")


def num(x):
    return float(x) if isinstance(x, (int, float)) and x == x else None


def news_items(t, n=4):
    out = []
    try:
        for it in (t.news or [])[:n]:
            c = it.get("content", it)
            url = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or it.get("link")
            out.append({"title": c.get("title") or it.get("title"),
                        "publisher": (c.get("provider") or {}).get("displayName") or it.get("publisher"),
                        "date": (c.get("pubDate") or "")[:10], "url": url})
    except Exception:
        pass
    return [o for o in out if o["title"]]


OVERRIDES = json.loads((HERE / "overrides.json").read_text()) if (HERE / "overrides.json").exists() else {}


def fetch(entry, yf):
    tk = entry["ticker"].strip().upper().replace(".B", "-B")
    row = {**entry, "ticker": tk, "error": None}
    try:
        t = yf.Ticker(tk)
        i = t.info
        price = num(i.get("currentPrice") or i.get("regularMarketPrice"))
        pe, fpe = num(i.get("trailingPE")), num(i.get("forwardPE"))
        peg = num(i.get("trailingPegRatio") or i.get("pegRatio"))
        if peg is None and fpe and num(i.get("earningsGrowth")):
            g = i["earningsGrowth"] * 100
            peg = round(fpe / g, 2) if g > 0 else None
        prev = num(i.get("previousClose"))
        row.update(
            name=i.get("shortName") or tk, currency=i.get("currency"), sector=i.get("sector"),
            price=price, change_pct=round((price / prev - 1) * 100, 2) if price and prev else None,
            pe=pe, fpe=fpe, peg=peg, div_yield=num(i.get("dividendYield")),
            mcap=num(i.get("marketCap")), low52=num(i.get("fiftyTwoWeekLow")),
            high52=num(i.get("fiftyTwoWeekHigh")), target=num(i.get("targetMeanPrice")),
            rec=i.get("recommendationKey"), news=news_items(t))
        if price and num(entry.get("avg_cost")) and num(entry.get("shares")):
            row["pl_pct"] = round((price / entry["avg_cost"] - 1) * 100, 2)
            row["value"] = round(price * entry["shares"], 2)
    except Exception as e:
        row["error"] = str(e)[:120]
    ov = OVERRIDES.get(tk, {})
    for k, v in ov.items():
        if row.get(k) is None:
            row[k] = v
    if row.get("price") is not None:
        row["error"] = None
    elif not row["error"]:
        row["error"] = "sem dados de cotação"
    for k, f in (("pe", classify_pe), ("fpe", classify_pe), ("peg", classify_peg)):
        row[k + "_label"], row[k + "_cls"] = f(row.get(k))
    return row


def main():
    import yfinance as yf
    wl = json.loads((HERE / "watchlist.json").read_text())
    rows = [fetch(e, yf) for e in wl["companies"]]
    market = []
    for sym, nm in (("^GSPC", "S&P 500"), ("^IXIC", "Nasdaq"), ("^STOXX50E", "Euro Stoxx 50")):
        try:
            t = yf.Ticker(sym); fi = t.fast_info
            market.append({"name": nm, "price": num(fi["lastPrice"]),
                           "change_pct": round((fi["lastPrice"] / fi["previousClose"] - 1) * 100, 2)})
        except Exception:
            pass
    mnews = []
    try: mnews = news_items(yf.Ticker("^GSPC"), 6)
    except Exception: pass
    data = {"updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "companies": rows, "market": market, "market_news": mnews}
    (HERE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    tpl = (HERE / "template.html").read_text()
    (HERE / "index.html").write_text(tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False)))
    bad = [r["ticker"] for r in rows if r["error"] or r.get("price") is None]
    print(f"{len(rows)} empresas, {len(bad)} com falhas: {bad}")
    return 0 if len(bad) < len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
