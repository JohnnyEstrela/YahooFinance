"""Vai buscar P/E, P/E forward, PEG, preço e notícias (yfinance) -> data/snapshot.json."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent


def num(v):
    return float(v) if isinstance(v, (int, float)) and v == v else None


def news_items(t, limit=5):
    out = []
    for n in (t.news or [])[:limit]:
        c = n.get("content", n)
        url = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or c.get("link")
        out.append(
            {
                "title": c.get("title"),
                "publisher": (c.get("provider") or {}).get("displayName") or c.get("publisher"),
                "date": c.get("pubDate") or c.get("providerPublishTime"),
                "url": url,
            }
        )
    return [n for n in out if n["title"]]


def fetch(ticker):
    t = yf.Ticker(ticker.replace(".", "-") if ticker.count(".") == 1 and len(ticker.split(".")[1]) == 1 else ticker)
    i = t.info or {}
    pe, fpe = num(i.get("trailingPE")), num(i.get("forwardPE"))
    peg = num(i.get("trailingPegRatio")) or num(i.get("pegRatio"))
    return {
        "ticker": ticker,
        "name": i.get("shortName") or ticker,
        "sector": i.get("sector"),
        "currency": i.get("currency"),
        "price": num(i.get("currentPrice") or i.get("regularMarketPrice")),
        "change_pct": num(i.get("regularMarketChangePercent")),
        "pe": pe,
        "forward_pe": fpe,
        "peg": peg,
        "dividend_yield": num(i.get("dividendYield")),
        "market_cap": num(i.get("marketCap")),
        "news": news_items(t),
    }


def main():
    cfg = json.loads((HERE / "portfolio.json").read_text())
    tickers = {e["ticker"] for k in ("portfolio", "watchlist") for e in cfg.get(k, [])}
    stocks, errors = {}, {}
    for tk in sorted(tickers):
        try:
            stocks[tk] = fetch(tk)
        except Exception as e:  # um ticker mau não deve parar o resto
            errors[tk] = str(e)
    out = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="minutes"),
           "stocks": stocks, "errors": errors}
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data" / "snapshot.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"{len(stocks)} ok, {len(errors)} erros", file=sys.stderr)


if __name__ == "__main__":
    main()
