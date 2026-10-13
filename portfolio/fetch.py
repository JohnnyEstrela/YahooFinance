"""Obtém dados do Yahoo Finance para a watchlist e grava data/snapshot.json.

Uso: python portfolio/fetch.py
Requer acesso a finance.yahoo.com. Se estiver bloqueado (ex.: sandbox), a rotina
pode preencher data/snapshot.json por outra fonte com o mesmo formato.
"""
import datetime as dt
import json
from pathlib import Path

HERE = Path(__file__).parent
NEWS_PER_TICKER = 5


def _news(ticker_obj, limit=NEWS_PER_TICKER):
    out = []
    for item in ticker_obj.news or []:
        c = item.get("content") or {}
        title = c.get("title")
        if not title:
            continue
        out.append(
            {
                "title": title,
                "publisher": (c.get("provider") or {}).get("displayName", ""),
                "url": (c.get("canonicalUrl") or {}).get("url", ""),
                "published": c.get("pubDate", ""),
            }
        )
        if len(out) >= limit:
            break
    return out


def _peg(info):
    peg = info.get("trailingPegRatio") or info.get("pegRatio")
    if peg is None and info.get("forwardPE") and info.get("earningsGrowth"):
        peg = info["forwardPE"] / (info["earningsGrowth"] * 100)
    return peg


def fetch_company(yf, ticker):
    t = yf.Ticker(ticker)
    info = t.info
    return {
        "ticker": ticker,
        "name": info.get("shortName") or info.get("longName") or ticker,
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "currency": info.get("currency", ""),
        "change_pct": info.get("regularMarketChangePercent"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "peg": _peg(info),
        "news": _news(t),
    }


def main():
    import yfinance as yf

    watch = json.loads((HERE / "watchlist.json").read_text(encoding="utf-8"))
    companies, errors = [], {}
    for c in watch["companies"]:
        tk = c["ticker"]
        try:
            companies.append(fetch_company(yf, tk))
        except Exception as e:  # um ticker mau não deve parar os restantes
            errors[tk] = str(e)
    try:
        market_news = _news(yf.Ticker("^GSPC"), 8)
    except Exception as e:
        market_news, errors["^GSPC"] = [], str(e)

    out = HERE / "data" / "snapshot.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
                "companies": companies,
                "market_news": market_news,
                "errors": errors,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"{len(companies)} empresas, {len(errors)} erros -> {out}")


if __name__ == "__main__":
    main()
