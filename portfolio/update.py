"""Atualiza portfolio/data.json com métricas e notícias das empresas em watchlist.json.

Uso: python portfolio/update.py   (requer: pip install yfinance)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent


def classify_pe(pe, t):
    """P/E: <15 Barato, 15-30 Fair Value, 30-50 Pricey, >50 Expensive."""
    if pe is None or pe <= 0:
        return None
    if pe < t["cheap"]:
        return "barato"
    if pe <= t["fair"]:
        return "fair"
    if pe <= t["pricey"]:
        return "pricey"
    return "expensive"


def classify_peg(peg, t):
    """PEG: <1 Discount, 1-2 Fair, >2 Premium."""
    if peg is None or peg <= 0:
        return None
    if peg < t["discount"]:
        return "discount"
    if peg <= t["fair"]:
        return "fair"
    return "premium"


def _num(v):
    return round(float(v), 2) if isinstance(v, (int, float)) and v == v else None


def parse_news(items, limit=5):
    out = []
    for it in (items or [])[:limit]:
        c = it.get("content", it)
        url = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or c.get("link")
        title = c.get("title")
        if title and url:
            out.append({
                "title": title,
                "url": url,
                "publisher": (c.get("provider") or {}).get("displayName") or c.get("publisher"),
                "date": c.get("pubDate") or c.get("providerPublishTime"),
            })
    return out


def build_company(entry, t, yf):
    tk = yf.Ticker(entry["ticker"])
    info = tk.info or {}
    price = _num(info.get("currentPrice") or info.get("regularMarketPrice"))
    pe_t, pe_f = _num(info.get("trailingPE")), _num(info.get("forwardPE"))
    peg = _num(info.get("trailingPegRatio") or info.get("pegRatio"))
    row = {
        **{k: entry.get(k) for k in ("ticker", "status", "shares", "avg_cost", "notes")},
        "name": info.get("shortName") or entry["ticker"],
        "currency": info.get("currency"),
        "sector": info.get("sector"),
        "price": price,
        "change_pct": _num(info.get("regularMarketChangePercent")),
        "pe_ttm": pe_t, "pe_ttm_label": classify_pe(pe_t, t["pe"]),
        "pe_fwd": pe_f, "pe_fwd_label": classify_pe(pe_f, t["pe"]),
        "peg": peg, "peg_label": classify_peg(peg, t["peg"]),
        "dividend_yield_pct": _num(info.get("dividendYield")),
        "market_cap": info.get("marketCap"),
        "week52_low": _num(info.get("fiftyTwoWeekLow")),
        "week52_high": _num(info.get("fiftyTwoWeekHigh")),
        "news": parse_news(tk.news),
    }
    if price and entry.get("shares"):
        row["value"] = _num(price * entry["shares"])
        if entry.get("avg_cost"):
            row["pnl_pct"] = _num((price / entry["avg_cost"] - 1) * 100)
    return row


def main():
    import yfinance as yf

    wl = json.loads((HERE / "watchlist.json").read_text())
    t = json.loads((HERE / "thresholds.json").read_text())
    companies, errors = [], []
    for e in wl["companies"]:
        try:
            companies.append(build_company(e, t, yf))
        except Exception as ex:  # um ticker mau não deve parar o resto
            errors.append({"ticker": e["ticker"], "error": str(ex)})
    market = []
    for s in wl.get("market_news_symbols", []):
        try:
            market += parse_news(yf.Ticker(s).news, 4)
        except Exception as ex:
            errors.append({"ticker": s, "error": str(ex)})
    seen, uniq = set(), []
    for n in market:
        if n["url"] not in seen:
            seen.add(n["url"])
            uniq.append(n)
    data = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "thresholds": t,
        "companies": companies,
        "market_news": uniq[:10],
        "errors": errors,
    }
    (HERE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"{len(companies)} empresas, {len(errors)} erros")
    return 1 if errors and not companies else 0


if __name__ == "__main__":
    sys.exit(main())
