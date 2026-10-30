#!/usr/bin/env python3
"""Gera dashboard.html a partir de portfolio.json (dados Yahoo Finance via yfinance).

Uso:
  python build_dashboard.py                       # atualiza dados e gera dashboard.html
  python build_dashboard.py add TSLA --lista watchlist
  python build_dashboard.py remove TSLA
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
CONFIG = HERE / "portfolio.json"
OUT = HERE / "dashboard.html"
TEMPLATE = HERE / "template.html"
CACHE = HERE / "last_data.json"


def normalize(ticker: str) -> str:
    """BRK.B -> BRK-B (classes US); sufixos de bolsa como .LS ficam intactos."""
    t = ticker.strip().upper()
    base, _, suffix = t.partition(".")
    return f"{base}-{suffix}" if len(suffix) == 1 else t


def classify_pe(v, th):
    if v is None:
        return "nd"
    if v <= 0:
        return "prejuizo"
    if v < th["barato"]:
        return "barato"
    if v <= th["justo"]:
        return "justo"
    if v <= th["caro"]:
        return "pricey"
    return "expensive"


def classify_peg(v, th):
    if v is None:
        return "nd"
    if v <= 0:
        return "nd"
    if v < th["desconto"]:
        return "desconto"
    if v <= th["justo"]:
        return "justo"
    return "premium"


def num(x):
    return x if isinstance(x, (int, float)) and x == x else None


def news_items(t, limit=5):
    items = []
    try:
        for n in (t.news or [])[:limit]:
            c = n.get("content", n)
            url = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or c.get("link")
            items.append({
                "title": c.get("title"),
                "publisher": (c.get("provider") or {}).get("displayName") or c.get("publisher"),
                "date": c.get("pubDate") or c.get("providerPublishTime"),
                "url": url,
            })
    except Exception as e:  # noqa: BLE001
        print(f"  aviso: notícias indisponíveis ({e})", file=sys.stderr)
    return [i for i in items if i["title"]]


def fetch(entry, kind, cfg):
    import yfinance as yf

    sym = entry["ticker"]
    t = yf.Ticker(sym)
    info = {}
    for attempt in range(3):
        try:
            info = t.info or {}
            if info:
                break
        except Exception as e:  # noqa: BLE001
            print(f"  {sym}: tentativa {attempt + 1} falhou ({e})", file=sys.stderr)
        time.sleep(2 * (attempt + 1))
    price = num(info.get("currentPrice") or info.get("regularMarketPrice"))
    pe_t, pe_f = num(info.get("trailingPE")), num(info.get("forwardPE"))
    peg = num(info.get("pegRatio")) or num(info.get("trailingPegRatio"))
    growth = num(info.get("earningsGrowth"))
    if peg is None and pe_f and growth and growth > 0:
        peg = round(pe_f / (growth * 100), 2)
    dy = num(info.get("dividendYield"))
    row = {
        "ticker": sym,
        "lista": kind,
        "name": info.get("shortName") or info.get("longName") or sym,
        "sector": info.get("sector"),
        "currency": info.get("currency"),
        "price": price,
        "change_pct": num(info.get("regularMarketChangePercent")),
        "pe_ttm": pe_t,
        "pe_fwd": pe_f,
        "peg": peg,
        "div_yield": dy,
        "market_cap": num(info.get("marketCap")),
        "target": num(info.get("targetMeanPrice")),
        "pe_ttm_class": classify_pe(pe_t, cfg["pe"]),
        "pe_fwd_class": classify_pe(pe_f, cfg["pe"]),
        "peg_class": classify_peg(peg, cfg["peg"]),
        "shares": entry.get("shares"),
        "avg_cost": entry.get("avg_cost"),
        "notes": entry.get("notes"),
        "news": news_items(t),
        "ok": price is not None or pe_t is not None,
    }
    if price and entry.get("shares") and entry.get("avg_cost"):
        row["pl_pct"] = round((price / entry["avg_cost"] - 1) * 100, 2)
    return row


def load():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def save(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build():
    cfg = load()
    old = {}
    if CACHE.exists():
        old = {r["ticker"]: r for r in json.loads(CACHE.read_text(encoding="utf-8"))["rows"]}
    rows = []
    for kind in ("holdings", "watchlist"):
        for e in cfg.get(kind, []):
            e["ticker"] = normalize(e["ticker"])
            print(f"a obter {e['ticker']}...")
            r = fetch(e, "portfolio" if kind == "holdings" else "watchlist", cfg["thresholds"])
            if not r["ok"] and e["ticker"] in old:  # mantém último valor bom em vez de apagar
                r = {**old[e["ticker"]], "stale": True, "lista": r["lista"]}
            rows.append(r)
    data = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "thresholds": cfg["thresholds"],
        "rows": rows,
    }
    CACHE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    html = TEMPLATE.read_text(encoding="utf-8").replace(
        "/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    )
    OUT.write_text(html, encoding="utf-8")
    bad = [r["ticker"] for r in rows if not r["ok"]]
    print(f"dashboard.html gerado ({len(rows)} empresas)" + (f"; sem dados: {', '.join(bad)}" if bad else ""))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    a = sub.add_parser("add")
    a.add_argument("ticker")
    a.add_argument("--lista", choices=["holdings", "watchlist"], default="watchlist")
    r = sub.add_parser("remove")
    r.add_argument("ticker")
    args = p.parse_args()
    if args.cmd == "add":
        cfg = load()
        t = normalize(args.ticker)
        if any(e["ticker"] == t for k in ("holdings", "watchlist") for e in cfg[k]):
            sys.exit(f"{t} já existe")
        cfg[args.lista].append({"ticker": t})
        save(cfg)
        print(f"{t} adicionado a {args.lista}")
    elif args.cmd == "remove":
        cfg = load()
        t = normalize(args.ticker)
        for k in ("holdings", "watchlist"):
            cfg[k] = [e for e in cfg[k] if e["ticker"] != t]
        save(cfg)
        print(f"{t} removido")
    else:
        build()


if __name__ == "__main__":
    main()
