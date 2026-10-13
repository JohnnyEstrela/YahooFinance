"""Gera data/snapshot.json a partir do Yahoo Finance (yfinance). Uso: python fetch_yahoo.py"""
import json, pathlib, datetime as dt
import yfinance as yf

here = pathlib.Path(__file__).parent
pf = json.loads((here / "portfolio.json").read_text())
items = [dict(h, group="holding") for h in pf["holdings"]] + [dict(w, group="watchlist") for w in pf["watchlist"]]
out = []
for it in items:
    t = yf.Ticker(it["ticker"].replace(".", "-") if it["ticker"].count(".") == 1 and len(it["ticker"].split(".")[1]) == 1 else it["ticker"])
    try:
        i = t.info
        news = [{"title": n.get("content", {}).get("title"), "url": (n.get("content", {}).get("canonicalUrl") or {}).get("url"),
                 "source": (n.get("content", {}).get("provider") or {}).get("displayName"), "date": n.get("content", {}).get("pubDate")}
                for n in (t.news or [])[:4]]
    except Exception as e:  # noqa
        out.append(dict(it, error=str(e))); continue
    g = i.get("earningsGrowth") or i.get("earningsQuarterlyGrowth")
    pe, fpe = i.get("trailingPE"), i.get("forwardPE")
    y = (i.get("dividendYield") or 0)  # yfinance >=0.2.5x devolve em %
    peg = i.get("trailingPegRatio") or i.get("pegRatio")
    pegy = round(fpe / (g * 100 + y), 2) if fpe and g and g > 0 else None
    out.append(dict(it, price=i.get("currentPrice"), currency=i.get("currency"), change_pct=i.get("regularMarketChangePercent"),
                    pe_ttm=pe, pe_fwd=fpe, peg=peg, pegy=pegy, div_yield=y, market_cap=i.get("marketCap"),
                    sector=i.get("sector"), target=i.get("targetMeanPrice"), news=news))
(here / "data" / "snapshot.json").write_text(json.dumps({"updated": dt.datetime.utcnow().isoformat() + "Z", "source": "yahoo", "items": out, "market_news": []}, indent=1))
