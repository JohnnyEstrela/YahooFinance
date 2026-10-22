"""Rotina diária: lê watchlist.json, vai buscar dados ao Yahoo Finance e gera
data/latest.json + docs/index.html (dashboard).

Uso: python portfolio/update.py
"""
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

from render import render_html
from valuation import DEFAULT_LIMITS, classify_pe, classify_peg, derive_peg

ROOT = Path(__file__).resolve().parent
WATCHLIST = ROOT / "watchlist.json"
LATEST = ROOT / "data" / "latest.json"
HTML = ROOT / "docs" / "index.html"


def normalize_ticker(t):
    # Yahoo usa hífen nas ações de classe (BRK.B -> BRK-B)
    return re.sub(r"\.([AB])$", r"-\1", t.strip().upper())


def get_news(tk, limit=5):
    out = []
    try:
        for n in (tk.news or [])[:limit]:
            c = n.get("content", n)
            url = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or c.get("link")
            title = c.get("title")
            if title:
                out.append({
                    "titulo": title,
                    "url": url,
                    "fonte": (c.get("provider") or {}).get("displayName") or c.get("publisher"),
                    "data": c.get("pubDate") or c.get("providerPublishTime"),
                })
    except Exception:
        pass
    return out


def fetch_company(entry, limits):
    ticker = normalize_ticker(entry["ticker"])
    row = {**entry, "ticker": ticker, "erro": None}
    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        trailing, forward = info.get("trailingPE"), info.get("forwardPE")
        growth = info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth")
        peg = info.get("pegRatio") or info.get("trailingPegRatio")
        peg_origem = "Yahoo"
        if peg is None:
            peg = derive_peg(forward, trailing, growth * 100 if growth else None)
            peg_origem = "calculado" if peg else None
        row.update({
            "nome": info.get("longName") or info.get("shortName") or ticker,
            "setor": info.get("sector"),
            "moeda": info.get("currency"),
            "preco": price,
            "variacao_dia_pct": info.get("regularMarketChangePercent"),
            "pe_trailing": trailing,
            "pe_forward": forward,
            "peg": peg,
            "peg_origem": peg_origem,
            "dividend_yield_pct": info.get("dividendYield"),
            "alvo_analistas": info.get("targetMeanPrice"),
            "recomendacao": info.get("recommendationKey"),
            "market_cap": info.get("marketCap"),
            "noticias": get_news(tk),
        })
        if not price and not trailing and not forward:
            row["erro"] = "Sem dados devolvidos pelo Yahoo (limite de pedidos?)."
        shares, cost = entry.get("acoes") or 0, entry.get("preco_medio") or 0
        if price and shares and cost:
            row["pl_pct"] = round((price / cost - 1) * 100, 2)
            row["valor_posicao"] = round(price * shares, 2)
    except Exception as e:  # um ticker falhado não pára a rotina
        row["erro"] = f"{type(e).__name__}: {e}"
    for key, fn, src in (("pe_ttm", classify_pe, "pe_trailing"),
                         ("pe_fwd", classify_pe, "pe_forward"),
                         ("peg_cls", classify_peg, "peg")):
        row[key] = dict(zip(("etiqueta", "nivel"), fn(row.get(src), limits)))
    return row


def main():
    cfg = json.loads(WATCHLIST.read_text(encoding="utf-8"))
    limits = {**DEFAULT_LIMITS, **cfg.get("limites", {})}
    rows = []
    for entry in cfg["empresas"]:
        rows.append(fetch_company(entry, limits))
        time.sleep(1)  # evita 429
    data = {
        "atualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "limites": limits,
        "empresas": rows,
    }
    LATEST.parent.mkdir(exist_ok=True)
    HTML.parent.mkdir(exist_ok=True)
    LATEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    HTML.write_text(render_html(data), encoding="utf-8")
    falhas = [r["ticker"] for r in rows if r["erro"]]
    print(f"{len(rows)} empresas, {len(falhas)} com erro: {falhas}")


if __name__ == "__main__":
    main()
