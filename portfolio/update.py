"""Atualiza portfolio/data.json a partir de watchlist.json usando yfinance.

Uso: python portfolio/update.py
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent
MAX_NEWS = 5


def num(value):
    return value if isinstance(value, (int, float)) and value == value else None


def news_items(ticker):
    items = []
    for n in (ticker.news or [])[:MAX_NEWS]:
        c = n.get("content", n)
        url = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or c.get("link")
        items.append(
            {
                "title": c.get("title"),
                "publisher": (c.get("provider") or {}).get("displayName") or c.get("publisher"),
                "date": c.get("pubDate") or c.get("providerPublishTime"),
                "url": url,
            }
        )
    return [i for i in items if i["title"]]


def fetch(entry):
    symbol = entry["ticker"].upper()
    if re.fullmatch(r"[A-Z]+\.[A-Z]", symbol):  # BRK.B -> BRK-B (EDP.LS fica igual)
        symbol = symbol.replace(".", "-")
    t = yf.Ticker(symbol)
    info = t.info or {}
    pe_ttm, pe_fwd = num(info.get("trailingPE")), num(info.get("forwardPE"))
    peg = num(info.get("trailingPegRatio")) or num(info.get("pegRatio"))
    return {
        **entry,
        "ticker": symbol,
        "name": info.get("shortName") or info.get("longName") or symbol,
        "currency": info.get("currency"),
        "price": num(info.get("currentPrice") or info.get("regularMarketPrice")),
        "change_pct": num(info.get("regularMarketChangePercent")),
        "market_cap": num(info.get("marketCap")),
        "pe_ttm": pe_ttm,
        "pe_fwd": pe_fwd,
        "peg": peg,
        "dividend_yield": num(info.get("dividendYield")),
        "sector": info.get("sector"),
        "news": news_items(t),
    }


def main():
    watch = json.loads((HERE / "watchlist.json").read_text())
    out, errors = [], []
    for entry in watch.get("companies", []):
        try:
            out.append(fetch(entry))
        except Exception as exc:  # keep going; report at the end
            errors.append(f"{entry.get('ticker')}: {exc}")
            out.append({**entry, "error": str(exc), "news": []})
    data = {"updated": datetime.now(timezone.utc).isoformat(), "companies": out}
    (HERE / "data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"{len(out)} empresas, {len(errors)} erros")
    for e in errors:
        print(" -", e, file=sys.stderr)


if __name__ == "__main__":
    main()
