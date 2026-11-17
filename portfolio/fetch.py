"""Daily snapshot for the "Consultor Financeiro" dashboard.

Usage:
    python portfolio/fetch.py AAPL MSFT ASML --out snapshot.json

Pulls price, valuation multiples and news from Yahoo Finance (yfinance)
and writes one JSON document shaped for the dashboard's `daily/<date>` row.

Valuation bands (as defined by the portfolio owner):
  P/E (TTM and forward):  <15 Barato | 15-30 Fair Value | 30-50 Pricey | >=50 Expensive
  PEGY = P/E(TTM) / (EPS growth % + dividend yield %):
                          <1 Desconto | 1-2 Fair | >2 Premium
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone

import yfinance as yf

INDICES = [
    ("^GSPC", "S&P 500"),
    ("^IXIC", "Nasdaq"),
    ("^STOXX50E", "Euro Stoxx 50"),
    ("PSI20.LS", "PSI"),
    ("^VIX", "VIX"),
    ("EURUSD=X", "EUR/USD"),
]
NEWS_PER_TICKER = 4
MARKET_NEWS = 8


def norm_symbol(sym: str) -> str:
    sym = sym.strip().upper()
    # US class shares: BRK.B -> BRK-B (Yahoo uses a dash); keep exchange suffixes like ASML.AS
    if re.fullmatch(r"[A-Z]{1,5}\.[A-Z]", sym):
        sym = sym.replace(".", "-")
    return sym


def num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or math.isinf(f) else f


def pe_band(pe):
    if pe is None:
        return None
    if pe <= 0:
        return "n/a"
    if pe < 15:
        return "Barato"
    if pe < 30:
        return "Fair Value"
    if pe < 50:
        return "Pricey"
    return "Expensive"


def peg_band(peg):
    if peg is None or peg <= 0:
        return None
    if peg < 1:
        return "Desconto"
    if peg <= 2:
        return "Fair"
    return "Premium"


def news_items(raw, limit):
    out = []
    for n in raw or []:
        c = n.get("content") or n
        title = c.get("title")
        if not title:
            continue
        url = ((c.get("canonicalUrl") or {}).get("url")
               or (c.get("clickThroughUrl") or {}).get("url") or c.get("link"))
        out.append({
            "title": title,
            "summary": (c.get("summary") or "")[:280],
            "source": (c.get("provider") or {}).get("displayName") or c.get("publisher"),
            "url": url,
            "date": c.get("pubDate") or c.get("displayTime"),
            "tickers": [t.get("symbol") for t in ((c.get("finance") or {}).get("stockTickers") or [])][:6],
        })
        if len(out) >= limit:
            break
    return out


def growth_pct(t: yf.Ticker, info: dict):
    """Expected EPS growth in %: analyst next-FY, else current-FY, else long-term, else fwd/ttm EPS."""
    try:
        ge = t.growth_estimates
        for period in ("+1y", "0y", "LTG"):
            if ge is not None and period in ge.index:
                v = num(ge.loc[period, "stockTrend"])
                if v is not None:
                    return v * 100, period
    except Exception:
        pass
    fe, te = num(info.get("forwardEps")), num(info.get("trailingEps"))
    if fe and te and te > 0:
        return (fe / te - 1) * 100, "fwdEPS/ttmEPS"
    return None, None


def company(sym: str) -> dict:
    t = yf.Ticker(sym)
    try:
        info = t.info or {}
    except Exception as e:  # noqa: BLE001
        return {"symbol": sym, "error": f"sem dados: {e}"[:200]}
    price = num(info.get("currentPrice")) or num(info.get("regularMarketPrice"))
    if price is None:
        return {"symbol": sym, "error": "ticker não encontrado no Yahoo Finance"}
    pe_ttm = num(info.get("trailingPE"))
    pe_fwd = num(info.get("forwardPE"))
    dy = num(info.get("dividendYield")) or 0.0  # already in % in yfinance >= 0.2.5x
    g, g_src = growth_pct(t, info)
    pegy = None
    if pe_ttm and pe_ttm > 0 and g is not None and (g + dy) > 0:
        pegy = pe_ttm / (g + dy)
    try:
        news = news_items(t.news, NEWS_PER_TICKER)
    except Exception:
        news = []
    return {
        "symbol": sym,
        "name": info.get("longName") or info.get("shortName") or sym,
        "currency": info.get("currency"),
        "exchange": info.get("fullExchangeName") or info.get("exchange"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "price": price,
        "changePct": num(info.get("regularMarketChangePercent")),
        "marketCap": num(info.get("marketCap")),
        "low52": num(info.get("fiftyTwoWeekLow")),
        "high52": num(info.get("fiftyTwoWeekHigh")),
        "peTTM": pe_ttm,
        "peTTMBand": pe_band(pe_ttm) if pe_ttm is not None or info.get("trailingEps") is not None else None,
        "peFwd": pe_fwd,
        "peFwdBand": pe_band(pe_fwd),
        "epsGrowthPct": g,
        "epsGrowthSource": g_src,
        "divYieldPct": dy,
        "pegy": pegy,
        "pegyBand": peg_band(pegy),
        "pegYahoo": num(info.get("trailingPegRatio")),
        "target": num(info.get("targetMeanPrice")),
        "recommendation": info.get("recommendationKey"),
        "analysts": info.get("numberOfAnalystOpinions"),
        "news": news,
    }


def indices():
    out = []
    for sym, label in INDICES:
        try:
            f = yf.Ticker(sym).fast_info
            last, prev = num(f.last_price), num(f.previous_close)
            out.append({"symbol": sym, "label": label, "last": last,
                        "changePct": (last / prev - 1) * 100 if last and prev else None})
        except Exception:
            out.append({"symbol": sym, "label": label, "last": None, "changePct": None})
    return out


def market_news():
    seen, out = set(), []
    for sym in ("^GSPC", "^STOXX50E", "^IXIC"):
        try:
            for n in news_items(yf.Ticker(sym).news, MARKET_NEWS):
                if n["title"] not in seen:
                    seen.add(n["title"])
                    out.append(n)
        except Exception:
            continue
    out.sort(key=lambda n: n.get("date") or "", reverse=True)
    return out[:MARKET_NEWS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="*")
    ap.add_argument("--out", default="snapshot.json")
    a = ap.parse_args()
    syms = list(dict.fromkeys(norm_symbol(s) for s in a.symbols if s.strip()))
    now = datetime.now(timezone.utc)
    doc = {
        "date": now.strftime("%Y-%m-%d"),
        "updatedAt": now.isoformat(timespec="seconds"),
        "indices": indices(),
        "marketNews": market_news(),
        "companies": {s: company(s) for s in syms},
        "note": "",
        "alerts": [],
    }
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    print(f"wrote {a.out}: {len(syms)} companies")


if __name__ == "__main__":
    main()
