#!/usr/bin/env python3
"""Rotina diária de portefólio / watchlist com dados do Yahoo Finance.

Uso:
    python portfolio/report.py add NVDA --status portfolio --shares 10 --cost 120.5
    python portfolio/report.py add ASML --status watchlist --notes "esperar < 30x"
    python portfolio/report.py remove NVDA
    python portfolio/report.py run          # gera portfolio/dashboard.html
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
CONFIG = HERE / "watchlist.json"
HISTORY = HERE / "history"
OUT_HTML = HERE / "dashboard.html"
TEMPLATE = HERE / "template.html"


# ---------- classificação ----------
def classify(value, bands):
    """Devolve (key, label) da primeira banda cujo `max` é maior que o valor."""
    if value is None:
        return "na", "n/d"
    if value <= 0:
        return "na", "Sem lucros"
    for band in bands:
        if band["max"] is None or value < band["max"]:
            return band["key"], band["label"]
    return "na", "n/d"


def _num(v):
    return float(v) if isinstance(v, (int, float)) and v == v else None


def compute_peg(info):
    """PEG do Yahoo; se faltar, forward P/E a dividir pelo crescimento esperado dos lucros."""
    peg = _num(info.get("trailingPegRatio")) or _num(info.get("pegRatio"))
    growth = _num(info.get("earningsGrowth"))
    growth_pct = growth * 100 if growth is not None else None
    fpe = _num(info.get("forwardPE"))
    if peg is None and fpe and growth_pct and growth_pct > 0:
        peg = fpe / growth_pct
    # PEGY = P/E / (crescimento + dividend yield); o Yahoo devolve a yield já em %
    dy = _num(info.get("dividendYield")) or 0.0
    pegy = None
    pe = fpe or _num(info.get("trailingPE"))
    if pe and growth_pct is not None and growth_pct + dy > 0:
        pegy = pe / (growth_pct + dy)
    return peg, pegy, growth_pct, dy


def advisor_note(row):
    """Leitura rápida baseada apenas nas regras definidas - não é aconselhamento financeiro."""
    keys = [row["pe_ttm_key"], row["pe_fwd_key"], row["peg_key"]]
    known = [k for k in keys if k != "na"]
    if not known:
        return "Dados de valorização insuficientes."
    cheap = sum(k == "cheap" for k in known)
    exp = sum(k in ("pricey", "very_pricey", "expensive") for k in known)
    if cheap == len(known):
        txt = "Os 3 indicadores apontam para desconto - candidata a reforço/entrada."
    elif cheap >= 2:
        txt = "Maioria dos indicadores em zona barata."
    elif exp == len(known):
        txt = "Os indicadores apontam para valorização exigente - cautela com novas entradas."
    elif exp >= 2:
        txt = "Valorização tendencialmente cara."
    else:
        txt = "Valorização mista / próxima do justo."
    pe_t, pe_f = row["pe_ttm"], row["pe_fwd"]
    if pe_t and pe_f and pe_f < pe_t * 0.85:
        txt += " O P/E forward é bem inferior ao trailing: lucros esperados a subir."
    elif pe_t and pe_f and pe_f > pe_t * 1.1:
        txt += " P/E forward acima do trailing: lucros esperados a cair."
    return txt


# ---------- obtenção de dados ----------
def normalize(ticker):
    """Classes de ações US (BRK.B -> BRK-B); sufixos de bolsa (ASML.AS) ficam como estão."""
    t = ticker.upper()
    head, _, tail = t.partition(".")
    return f"{head}-{tail}" if len(tail) == 1 else t


def fetch_ticker(entry, cfg):
    import yfinance as yf

    sym = normalize(entry["ticker"])
    row = {"ticker": entry["ticker"].upper(), "status": entry.get("status", "watchlist"),
           "notes": entry.get("notes", ""), "error": None, "news": []}
    try:
        t = yf.Ticker(sym)
        info = t.info or {}
        price = _num(info.get("currentPrice")) or _num(info.get("regularMarketPrice"))
        peg, pegy, growth, dy = compute_peg(info)
        th = cfg["thresholds"]
        row.update(
            name=info.get("shortName") or info.get("longName") or sym,
            currency=info.get("currency", ""), price=price,
            change_pct=_num(info.get("regularMarketChangePercent")),
            sector=info.get("sector", ""),
            pe_ttm=_num(info.get("trailingPE")), pe_fwd=_num(info.get("forwardPE")),
            peg=peg, pegy=pegy, growth_pct=growth, dividend_yield=dy,
            target=_num(info.get("targetMeanPrice")),
            recommendation=info.get("recommendationKey", ""),
            week52_low=_num(info.get("fiftyTwoWeekLow")), week52_high=_num(info.get("fiftyTwoWeekHigh")),
        )
        row["pe_ttm_key"], row["pe_ttm_label"] = classify(row["pe_ttm"], th["pe"])
        row["pe_fwd_key"], row["pe_fwd_label"] = classify(row["pe_fwd"], th["pe"])
        row["peg_key"], row["peg_label"] = classify(row["peg"], th["peg"])
        shares, cost = entry.get("shares"), entry.get("cost")
        if shares and price:
            row["position_value"] = shares * price
            if cost:
                row["pnl_pct"] = (price / cost - 1) * 100
                row["pnl_abs"] = shares * (price - cost)
        row["advice"] = advisor_note(row)
        try:
            for n in (yf.Search(sym, news_count=cfg["settings"]["news_per_ticker"]).news or []):
                row["news"].append(_news_item(n))
        except Exception:
            pass
    except Exception as exc:  # um ticker mau não deve estragar o relatório
        row["error"] = f"{type(exc).__name__}: {exc}"
        row.setdefault("name", sym)
        for k in ("pe_ttm", "pe_fwd", "peg"):
            row[k + "_key"], row[k + "_label"] = "na", "n/d"
    return row


def _news_item(n):
    ts = n.get("providerPublishTime")
    return {"title": n.get("title", ""), "publisher": n.get("publisher", ""), "link": n.get("link", ""),
            "time": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M") if ts else ""}


def fetch_market_news(cfg):
    import yfinance as yf

    seen, out = set(), []
    for q in cfg["settings"]["market_news_queries"]:
        try:
            for n in yf.Search(q, news_count=5).news or []:
                if n.get("link") not in seen:
                    seen.add(n.get("link"))
                    out.append(_news_item(n))
        except Exception:
            continue
    out.sort(key=lambda x: x["time"], reverse=True)
    return out[: cfg["settings"]["market_news"]]


# ---------- comandos ----------
def load():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def save(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_add(a):
    cfg = load()
    sym = a.ticker.upper()
    cfg["tickers"] = [t for t in cfg["tickers"] if t["ticker"].upper() != sym]
    entry = {"ticker": sym, "status": a.status}
    if a.shares is not None:
        entry["shares"] = a.shares
    if a.cost is not None:
        entry["cost"] = a.cost
    if a.notes:
        entry["notes"] = a.notes
    cfg["tickers"].append(entry)
    save(cfg)
    print(f"{sym} guardado como {a.status}.")


def cmd_remove(a):
    cfg = load()
    cfg["tickers"] = [t for t in cfg["tickers"] if t["ticker"].upper() != a.ticker.upper()]
    save(cfg)
    print(f"{a.ticker.upper()} removido.")


def changes_since_last(rows):
    """Mudanças de classificação face ao último snapshot (alimenta os alertas)."""
    snaps = sorted(HISTORY.glob("*.json")) if HISTORY.exists() else []
    if not snaps:
        return []
    prev = {r["ticker"]: r for r in json.loads(snaps[-1].read_text(encoding="utf-8"))["rows"]}
    out = []
    for r in rows:
        p = prev.get(r["ticker"])
        if not p:
            continue
        for k, nome in (("pe_ttm", "P/E (12m passados)"), ("pe_fwd", "P/E (próx. 12m)"), ("peg", "PEG")):
            if p.get(k + "_key") != r.get(k + "_key"):
                out.append({"ticker": r["ticker"], "text": f"{nome}: {p.get(k + '_label')} → {r.get(k + '_label')}"})
    return out


def cmd_run(a):
    cfg = load()
    with ThreadPoolExecutor(max_workers=6) as ex:
        rows = list(ex.map(lambda e: fetch_ticker(e, cfg), cfg["tickers"]))
    data = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "thresholds": cfg["thresholds"], "rows": rows,
            "market_news": fetch_market_news(cfg), "changes": changes_since_last(rows)}
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    OUT_HTML.write_text(html, encoding="utf-8")
    HISTORY.mkdir(exist_ok=True)
    (HISTORY / f"{datetime.now(timezone.utc):%Y-%m-%d}.json").write_text(
        json.dumps({"rows": rows}, ensure_ascii=False), encoding="utf-8")
    errs = [r["ticker"] for r in rows if r["error"]]
    print(f"{len(rows)} tickers, {len(data['changes'])} mudanças, erros: {errs or 'nenhum'} -> {OUT_HTML}")
    for c in data["changes"]:
        print("MUDANÇA", c["ticker"], c["text"])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    ad = sub.add_parser("add")
    ad.add_argument("ticker")
    ad.add_argument("--status", choices=["portfolio", "watchlist"], default="watchlist")
    ad.add_argument("--shares", type=float)
    ad.add_argument("--cost", type=float, help="preço médio de compra")
    ad.add_argument("--notes")
    ad.set_defaults(fn=cmd_add)
    rm = sub.add_parser("remove")
    rm.add_argument("ticker")
    rm.set_defaults(fn=cmd_remove)
    sub.add_parser("run").set_defaults(fn=cmd_run)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
