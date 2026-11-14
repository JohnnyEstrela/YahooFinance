"""Daily refresh for the portfolio dashboard.

Reads portfolio/watchlist.json, pulls valuation data from Yahoo Finance
(yfinance) and headlines from Yahoo Finance / Google News RSS, and writes:

  portfolio/out/companies.json  -> {rows, meta}  one row per company
  portfolio/out/news.json       -> {rows, meta}  headlines per company + market

Run:  uv run python portfolio/fetch.py
"""

import json
import math
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
NOW = datetime.now(timezone.utc)
UA = {"User-Agent": "Mozilla/5.0 (portfolio-dashboard)"}
NEWS_PER_TICKER = 4
NEWS_MAX_AGE_DAYS = 7


def num(x):
    """Return a finite float or None."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def rnd(x, d=2):
    return None if x is None else round(x, d)


def pe_zone(pe, t):
    if pe is None:
        return "n/d"
    if pe <= 0:
        return "Prejuízo"
    if pe < t["cheap_below"]:
        return "Barato"
    if pe < t["fair_below"]:
        return "Fair Value"
    if pe < t["pricey_below"]:
        return "Pricey"
    return "Expensive"


def pegy_zone(v, t):
    if v is None:
        return "n/d"
    if v < t["discount_below"]:
        return "Discount"
    if v < t["fair_below"]:
        return "Fair"
    return "Premium"


def growth_estimate(tk):
    """Analyst EPS growth in %: long-term (LTG) > next year (+1y). Returns (pct, label)."""
    try:
        ge = tk.growth_estimates
        st = ge["stockTrend"] if ge is not None and "stockTrend" in ge else None
    except Exception:
        st = None
    if st is not None:
        for key, label in (("LTG", "longo prazo"), ("+1y", "próximo ano")):
            v = num(st.get(key)) if key in st.index else None
            if v is not None:
                return v * 100, label
    return None, None


def fx_rate(cur, base, cache):
    """Units of base per 1 unit of cur."""
    if cur is None or cur == base:
        return 1.0
    cur_n, div = cur, 1.0
    if cur == "GBp":  # London quotes in pence
        cur_n, div = "GBP", 100.0
    if cur_n == base:
        return 1.0 / div
    key = f"{cur_n}{base}=X"
    if key not in cache:
        try:
            cache[key] = num(yf.Ticker(key).info.get("regularMarketPrice"))
        except Exception:
            cache[key] = None
    r = cache[key]
    return None if r is None else r / div


def company_row(entry, group, th, base, fxc):
    sym = entry["ticker"].strip().upper()
    tk = yf.Ticker(sym)
    info = tk.info or {}
    price = num(info.get("currentPrice")) or num(info.get("regularMarketPrice"))
    if price is None:
        raise ValueError("sem preço (ticker inválido?)")
    pe_ttm = num(info.get("trailingPE"))
    if pe_ttm is None:
        eps = num(info.get("trailingEps"))
        pe_ttm = price / eps if eps else None
    pe_fwd = num(info.get("forwardPE"))
    dy = num(info.get("dividendYield"))  # yfinance >=0.2.5x returns percent (0.4 = 0.4%)
    dy = dy or 0.0
    g, g_label = growth_estimate(tk)
    if g is None and num(info.get("earningsGrowth")) is not None:
        g, g_label = num(info.get("earningsGrowth")) * 100, "último trimestre"
    pe_for_pegy = pe_ttm if (pe_ttm and pe_ttm > 0) else pe_fwd
    pegy = None
    if pe_for_pegy and pe_for_pegy > 0 and g is not None and (g + dy) > 0:
        pegy = pe_for_pegy / (g + dy)

    cur = info.get("currency")
    target = num(info.get("targetMeanPrice"))
    lo, hi = num(info.get("fiftyTwoWeekLow")), num(info.get("fiftyTwoWeekHigh"))
    earnings = None
    try:
        cal = tk.calendar or {}
        ed = cal.get("Earnings Date")
        if ed:
            earnings = str(ed[0])
    except Exception:
        pass

    shares = num(entry.get("shares"))
    cost = num(entry.get("avg_cost"))
    fx = fx_rate(cur, base, fxc)
    value_base = shares * price * fx if (shares and fx) else None
    pl_pct = (price / cost - 1) * 100 if cost else None
    pl_base = (price - cost) * shares * fx if (cost and shares and fx) else None

    return {
        "ticker": sym,
        "name": info.get("shortName") or info.get("longName") or sym,
        "group": group,
        "example": bool(entry.get("example")),
        "note": entry.get("note") or "",
        "sector": info.get("sector") or info.get("quoteType") or "",
        "currency": cur,
        "price": rnd(price),
        "change_pct": rnd(num(info.get("regularMarketChangePercent"))),
        "market_cap_bn": rnd((num(info.get("marketCap")) or 0) / 1e9, 1) or None,
        "pe_ttm": rnd(pe_ttm, 1),
        "pe_ttm_zone": pe_zone(pe_ttm, th["pe"]),
        "pe_fwd": rnd(pe_fwd, 1),
        "pe_fwd_zone": pe_zone(pe_fwd, th["pe"]),
        "growth_pct": rnd(g, 1),
        "growth_basis": g_label or "",
        "div_yield_pct": rnd(dy, 2),
        "pegy": rnd(pegy, 2),
        "pegy_zone": pegy_zone(pegy, th["pegy"]),
        "peg_yahoo": rnd(num(info.get("trailingPegRatio")), 2),
        "low_52w": rnd(lo),
        "high_52w": rnd(hi),
        "pos_52w_pct": rnd((price - lo) / (hi - lo) * 100, 0) if lo and hi and hi > lo else None,
        "target_mean": rnd(target),
        "upside_pct": rnd((target / price - 1) * 100, 1) if target else None,
        "recommendation": (info.get("recommendationKey") or "").replace("_", " "),
        "analysts": info.get("numberOfAnalystOpinions"),
        "next_earnings": earnings,
        "shares": shares,
        "avg_cost": cost,
        "value_base": rnd(value_base),
        "pl_pct": rnd(pl_pct, 1),
        "pl_base": rnd(pl_base),
        "error": "",
    }


def rss(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        src = it.find("source")
        try:
            dt = parsedate_to_datetime(it.findtext("pubDate"))
        except Exception:
            continue
        if src is not None and src.text and title.endswith(" - " + src.text.strip()):
            title = title[: -len(src.text.strip()) - 3]
        if title and link.startswith("https://"):
            out.append((dt, title, link, src.text.strip() if src is not None and src.text else ""))
    return out


def news_for(key, label, kind, url):
    try:
        items = rss(url)
    except Exception as e:  # network/feed problems shouldn't stop the run
        print(f"  news {label}: {e}", file=sys.stderr)
        return []
    cutoff = NOW - timedelta(days=NEWS_MAX_AGE_DAYS)
    items = sorted((i for i in items if i[0] >= cutoff), reverse=True)[:NEWS_PER_TICKER]
    return [
        {
            "key": key,
            "label": label,
            "kind": kind,
            "published": dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "title": title,
            "source": src or ("Yahoo Finance" if "yahoo" in url else ""),
            "url": link,
        }
        for dt, title, link, src in items
    ]


def clean_name(name):
    import re

    n = re.sub(r"[,.]?\s*(S\.?A\.?|SGPS|N\.V\.|Inc\.?|Corporation|Holding|-NOM|plc|AG|SE)\b.*$", "", name, flags=re.I)
    return n.strip(" ,.-") or name


def yahoo_rss(sym):
    return "https://feeds.finance.yahoo.com/rss/2.0/headline?" + urllib.parse.urlencode(
        {"s": sym, "region": "US", "lang": "en-US"}
    )


def google_rss(q):
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q + " when:7d", "hl": "pt-PT", "gl": "PT", "ceid": "PT:pt-150"}
    )


def main():
    cfg = json.loads((HERE / "watchlist.json").read_text())
    th, base = cfg["thresholds"], cfg.get("base_currency", "EUR")
    fxc = {}
    rows, news = [], []
    seen = set()
    for group, key in (("Portefólio", "portfolio"), ("Radar", "radar")):
        for entry in cfg.get(key, []):
            sym = entry["ticker"].strip().upper()
            if sym in seen:
                continue
            seen.add(sym)
            print(f"{group}: {sym}")
            try:
                row = company_row(entry, group, th, base, fxc)
            except Exception as e:
                row = {"ticker": sym, "name": sym, "group": group, "error": str(e)[:200]}
            rows.append(row)
            name = row.get("name", sym)
            items = news_for(sym, name, "empresa", yahoo_rss(sym))
            if len(items) < 2:  # Yahoo has thin coverage of European small/mid caps
                q = entry.get("news_query") or f'"{clean_name(name)}" ações OR stock'
                urls = {i["url"] for i in items}
                items += [i for i in news_for(sym, name, "empresa", google_rss(q)) if i["url"] not in urls]
                items = sorted(items, key=lambda i: i["published"], reverse=True)[:NEWS_PER_TICKER]
            news += items
    for m in cfg.get("market_news", []):
        url = yahoo_rss(m["yahoo"]) if "yahoo" in m else google_rss(m["google"])
        news += news_for(m.get("yahoo") or m["label"], m["label"], "mercado", url)

    stamp = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
    code = Path(__file__).read_text()
    meta = [
        {"label": "fetch.py", "value": code, "type": "code", "lang": "python"},
        {"label": "Input", "value": "portfolio/watchlist.json"},
        {"label": "Fonte", "value": "Yahoo Finance via yfinance; notícias Yahoo Finance RSS e Google News RSS"},
        {"label": "Gerado", "value": stamp},
    ]
    fx_meta = {k: v for k, v in fxc.items()}
    OUT.mkdir(exist_ok=True)
    (OUT / "companies.json").write_text(
        json.dumps({"rows": rows, "meta": meta + [{"label": "Câmbios usados", "value": json.dumps(fx_meta)}]},
                   ensure_ascii=False, indent=1)
    )
    (OUT / "news.json").write_text(json.dumps({"rows": news, "meta": meta}, ensure_ascii=False, indent=1))
    errs = [r["ticker"] for r in rows if r.get("error")]
    print(f"OK {len(rows)} empresas, {len(news)} notícias, erros: {errs or 'nenhum'}")


if __name__ == "__main__":
    main()
