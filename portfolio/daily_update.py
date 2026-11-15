"""Daily portfolio / watchlist update.

Reads a list of companies (JSON), fetches valuation metrics and news from
Yahoo Finance via yfinance and writes a JSON snapshot that the dashboard
artifact renders.

Usage:
    uv run python portfolio/daily_update.py companies.json out.json

companies.json: [{"ticker": "MSFT", "status": "portfolio"|"watchlist", ...}]

Valuation bands (as defined by the owner):
    P/E (TTM and forward): <15 Barato · ~20 Fair Value · ~40 Pricey · >50 Expensive
        Boundaries used: 15 / 30 (midpoint of 20 and 40) / 50.
    PEGY = P/E ÷ (expected EPS growth % + dividend yield %):
        <1 Desconto · 1–2 Justo · >2 Premium
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone

import yfinance as yf

sys.path.insert(0, __file__.rsplit("/portfolio/", 1)[0])
from server import normalize_ticker  # noqa: E402


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or math.isinf(f) else f


def pe_band(pe):
    if pe is None:
        return None
    if pe <= 0:
        return "negativo"
    if pe < 15:
        return "barato"
    if pe < 30:
        return "justo"
    if pe <= 50:
        return "caro"
    return "muito caro"


def peg_band(v):
    if v is None:
        return None
    if v <= 0:
        return "n/a"
    if v < 1:
        return "desconto"
    if v <= 2:
        return "justo"
    return "premium"


def growth_pct(t: yf.Ticker, info: dict, pe):
    """Expected annual EPS growth in %, plus the source used."""
    peg = _num(info.get("trailingPegRatio"))
    if pe and pe > 0 and peg and peg > 0:
        return pe / peg, "Yahoo PEG (5 anos)"
    try:
        ge = t.growth_estimates
        for key in ("LTG", "+1y"):
            if key in ge.index:
                g = _num(ge.loc[key, "stockTrend"])
                if g is not None:
                    return g * 100, f"estimativa {key}"
    except Exception:
        pass
    g = _num(info.get("earningsGrowth"))
    if g is not None:
        return g * 100, "crescimento último trimestre"
    return None, None


def fetch_news(query: str, n: int):
    try:
        items = yf.Search(query, news_count=n).news or []
    except Exception:
        return []
    out = []
    for it in items:
        ts = it.get("providerPublishTime")
        out.append(
            {
                "title": it.get("title"),
                "publisher": it.get("publisher"),
                "link": it.get("link"),
                "time": datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else None,
            }
        )
    return out


def company_snapshot(entry: dict) -> dict:
    sym = normalize_ticker(entry["ticker"].strip().upper())
    t = yf.Ticker(sym)
    try:
        info = t.info or {}
    except Exception as e:  # noqa: BLE001
        return {"ticker": sym, "error": f"sem dados: {e}"}
    if not info.get("regularMarketPrice") and not info.get("currentPrice"):
        return {"ticker": sym, "error": "ticker não encontrado no Yahoo Finance"}

    price = _num(info.get("currentPrice") or info.get("regularMarketPrice"))
    pe_ttm = _num(info.get("trailingPE"))
    pe_fwd = _num(info.get("forwardPE"))
    dy = _num(info.get("dividendYield")) or 0.0  # yfinance already gives %
    g, g_src = growth_pct(t, info, pe_ttm or pe_fwd)
    base_pe = pe_ttm or pe_fwd
    peg = base_pe / g if base_pe and g and g > 0 else None
    pegy = base_pe / (g + dy) if base_pe and g is not None and (g + dy) > 0 else None

    try:
        hist = t.history(period="1mo")["Close"].dropna()
        spark = [round(float(x), 2) for x in hist.tolist()]
    except Exception:
        spark = []

    snap = {
        "key": entry["ticker"],
        "ticker": sym,
        "name": info.get("shortName") or info.get("longName") or sym,
        "sector": info.get("sector"),
        "currency": info.get("currency"),
        "price": price,
        "changePct": _num(info.get("regularMarketChangePercent")),
        "marketCap": _num(info.get("marketCap")),
        "low52": _num(info.get("fiftyTwoWeekLow")),
        "high52": _num(info.get("fiftyTwoWeekHigh")),
        "target": _num(info.get("targetMeanPrice")),
        "recommendation": info.get("recommendationKey"),
        "peTtm": pe_ttm,
        "peTtmBand": pe_band(pe_ttm),
        "peFwd": pe_fwd,
        "peFwdBand": pe_band(pe_fwd),
        "growthPct": g,
        "growthSource": g_src,
        "dividendYield": dy,
        "peg": peg,
        "pegy": pegy,
        "pegyBand": peg_band(pegy),
        "spark": spark,
        "news": fetch_news(sym, 4),
    }
    shares, cost = _num(entry.get("shares")), _num(entry.get("avgCost"))
    if price and shares:
        snap["positionValue"] = price * shares
        if cost:
            snap["pnlPct"] = (price / cost - 1) * 100
            snap["pnl"] = (price - cost) * shares
    return snap


INDICES = [
    ("^GSPC", "S&P 500"),
    ("^IXIC", "Nasdaq"),
    ("^STOXX50E", "Euro Stoxx 50"),
    ("PSI20.LS", "PSI"),
    ("EURUSD=X", "EUR/USD"),
]


def fetch_indices():
    out = []
    for sym, label in INDICES:
        try:
            info = yf.Ticker(sym).info or {}
            out.append(
                {
                    "symbol": sym,
                    "label": label,
                    "price": _num(info.get("regularMarketPrice")),
                    "changePct": _num(info.get("regularMarketChangePercent")),
                }
            )
        except Exception:
            continue
    return [i for i in out if i["price"] is not None]


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    companies = json.load(open(src))
    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "companies": {},
        "marketNews": fetch_news("stock market today", 8),
        "indices": fetch_indices(),
    }
    for entry in companies:
        snap = company_snapshot(entry)
        snap.setdefault("key", entry["ticker"])
        out["companies"][entry["ticker"]] = snap
        print(f"{snap['ticker']}: P/E {snap.get('peTtm')} fwd {snap.get('peFwd')} PEGY {snap.get('pegy')} {snap.get('error', '')}")
    json.dump(out, open(dst, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
