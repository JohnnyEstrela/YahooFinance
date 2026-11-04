#!/usr/bin/env python3
"""Atualiza data.js com preços, múltiplos (P/E TTM, P/E forward, PEG) e notícias."""
import json, sys, datetime as dt
from pathlib import Path
import yfinance as yf

HERE = Path(__file__).parent


def num(v):
    return round(float(v), 2) if isinstance(v, (int, float)) and v == v else None


def fetch(ticker):
    t = yf.Ticker(ticker.replace(".", "-") if ticker.upper().endswith((".A", ".B")) else ticker)
    out = {"ticker": ticker.upper(), "name": ticker.upper(), "price": None, "currency": None,
           "change_pct": None, "pe_ttm": None, "pe_fwd": None, "peg": None, "div_yield": None,
           "notes": [], "news": []}
    try:
        fi = t.fast_info
        out["price"], out["currency"] = num(fi["lastPrice"]), fi["currency"]
        prev = fi["regularMarketPreviousClose"]
        out["change_pct"] = num((fi["lastPrice"] / prev - 1) * 100) if prev else None
    except Exception as e:
        out["notes"].append(f"preço indisponível ({type(e).__name__})")
    try:
        info = t.info or {}
    except Exception:
        info = {}
    out["name"] = info.get("shortName") or out["name"]
    out["pe_ttm"] = num(info.get("trailingPE"))
    out["pe_fwd"] = num(info.get("forwardPE"))
    out["peg"] = num(info.get("trailingPegRatio") or info.get("pegRatio"))
    dy = info.get("dividendYield")
    out["div_yield"] = num(dy if dy and dy > 1 else (dy or 0) * 100) if dy is not None else None
    if out["pe_ttm"] is None and out["price"]:  # fallback: soma do EPS dos últimos 4 trimestres
        try:
            eps = t.quarterly_income_stmt.loc["Diluted EPS"].dropna().head(4)
            if len(eps) == 4 and eps.sum() > 0:
                out["pe_ttm"] = num(out["price"] / eps.sum())
                out["notes"].append("P/E TTM calculado (preço / EPS 4 trimestres)")
        except Exception:
            pass
    try:
        for n in (t.news or [])[:5]:
            c = n.get("content", n)
            url = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or c.get("link")
            out["news"].append({"title": c.get("title"), "date": (c.get("pubDate") or "")[:10],
                                "source": (c.get("provider") or {}).get("displayName"), "url": url})
    except Exception:
        pass
    return out


def main():
    cfg = json.loads((HERE / "portfolio.json").read_text())
    items = []
    for h in cfg["holdings"]:
        d = fetch(h["ticker"])
        d.update({k: h.get(k) for k in ("list", "shares", "avg_cost")})
        items.append(d)
        print(d["ticker"], d["price"], d["pe_ttm"], d["pe_fwd"], d["peg"], file=sys.stderr)
    data = {"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"), "items": items}
    (HERE / "data.js").write_text("window.DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")


if __name__ == "__main__":
    main()
