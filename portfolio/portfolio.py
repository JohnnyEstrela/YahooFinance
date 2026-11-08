#!/usr/bin/env python3
"""Rotina diária do portefólio / watchlist.

Uso:
  python portfolio/portfolio.py run                      # atualiza dados + dashboard
  python portfolio/portfolio.py add NVDA --status watch  # adiciona (watch|portfolio)
  python portfolio/portfolio.py add AAPL --status portfolio --shares 10 --avg-cost 150
  python portfolio/portfolio.py remove NVDA
  python portfolio/portfolio.py list
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
WATCHLIST = HERE / "watchlist.json"
DATA_DIR = HERE / "data"
LATEST = DATA_DIR / "latest.json"
HISTORY = DATA_DIR / "history"
DASHBOARD = HERE / "dashboard.html"
TEMPLATE = HERE / "template.html"

PE_LABELS = {"cheap": "Barato", "fair": "Justo", "pricey": "Caro", "expensive": "Muito caro",
             "neg": "Sem lucros", "nd": "N/D"}
PEG_LABELS = {"discount": "Desconto", "fair": "Justo", "premium": "Premium",
              "neg": "Sem crescimento", "nd": "N/D"}


# ----------------------------------------------------------------- config
def load_cfg() -> dict:
    return json.loads(WATCHLIST.read_text(encoding="utf-8"))


def save_cfg(cfg: dict) -> None:
    WATCHLIST.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def norm_ticker(t: str) -> str:
    t = t.strip().upper()
    # BRK.B -> BRK-B (classes US); mantém sufixos de bolsa como .LS, .L, .DE
    if "." in t and len(t.rsplit(".", 1)[1]) == 1:
        t = t.replace(".", "-")
    return t


# --------------------------------------------------------- classificação
def num(v):
    try:
        f = float(v)
        return None if f != f else f
    except (TypeError, ValueError):
        return None


def band_pe(v, th) -> str:
    if v is None:
        return "nd"
    if v <= 0:
        return "neg"
    if v < th["cheap"]:
        return "cheap"
    if v < th["fair"]:
        return "fair"
    if v <= th["pricey"]:
        return "pricey"
    return "expensive"


def band_peg(v, th) -> str:
    if v is None:
        return "nd"
    if v <= 0:
        return "neg"
    if v < th["discount"]:
        return "discount"
    if v <= th["fair"]:
        return "fair"
    return "premium"


def verdict(pe_b, fpe_b, peg_b) -> tuple[str, str]:
    """Leitura rápida baseada só nas regras de valorização (não é aconselhamento)."""
    score = {"cheap": 2, "discount": 2, "fair": 1, "pricey": -1, "premium": -1, "expensive": -2}
    vals = [score[b] for b in (pe_b, fpe_b, peg_b) if b in score]
    if len(vals) < 2:
        return "Dados insuficientes", "nd"
    s = sum(vals) / len(vals)
    if s >= 1.5:
        return "Atrativa", "cheap"
    if s >= 0.5:
        return "Preço razoável", "fair"
    if s > -1.2:
        return "Exigente", "pricey"
    return "Cara", "expensive"


# ------------------------------------------------------------- recolha
def parse_news(items, limit=5):
    out = []
    for it in items or []:
        c = it.get("content") or it
        title = c.get("title")
        if not title:
            continue
        url = ((c.get("canonicalUrl") or {}).get("url")
               or (c.get("clickThroughUrl") or {}).get("url") or c.get("link"))
        out.append({
            "title": title,
            "summary": (c.get("summary") or c.get("description") or "")[:240],
            "url": url,
            "source": (c.get("provider") or {}).get("displayName") or c.get("publisher") or "",
            "date": c.get("pubDate") or "",
        })
    out.sort(key=lambda n: n["date"], reverse=True)
    return out[:limit]


def fetch_company(entry: dict, th: dict) -> dict:
    import yfinance as yf

    tk = norm_ticker(entry["ticker"])
    res = {"ticker": tk, "status": entry.get("status", "watch"), "notes": entry.get("notes", ""),
           "shares": num(entry.get("shares")), "avg_cost": num(entry.get("avg_cost"))}
    t = yf.Ticker(tk)
    info = t.info or {}
    price = num(info.get("currentPrice") or info.get("regularMarketPrice")
                or info.get("previousClose"))
    prev = num(info.get("regularMarketPreviousClose") or info.get("previousClose"))
    pe, fpe = num(info.get("trailingPE")), num(info.get("forwardPE"))
    eps_t, eps_f = num(info.get("trailingEps")), num(info.get("forwardEps"))
    peg = num(info.get("trailingPegRatio")) or num(info.get("pegRatio"))
    growth = None
    if eps_t and eps_f and eps_t > 0:
        growth = (eps_f / eps_t - 1) * 100
    elif num(info.get("earningsGrowth")) is not None:
        growth = num(info.get("earningsGrowth")) * 100
    dy = num(info.get("dividendYield"))  # yfinance >= 0.2.5x devolve já em %
    if peg is None and fpe and growth and growth > 0:
        peg = fpe / growth
    pegy = None
    if fpe and growth is not None and growth + (dy or 0) > 0:
        pegy = fpe / (growth + (dy or 0))

    pe_b, fpe_b, peg_b = band_pe(pe, th["pe"]), band_pe(fpe, th["pe"]), band_peg(peg, th["peg"])
    v_txt, v_tone = verdict(pe_b, fpe_b, peg_b)
    lo, hi = num(info.get("fiftyTwoWeekLow")), num(info.get("fiftyTwoWeekHigh"))
    target = num(info.get("targetMeanPrice"))

    try:
        hist = t.history(period="3mo", interval="1d")["Close"].dropna()
        spark = [round(float(x), 2) for x in hist.tolist()]
    except Exception:
        spark = []

    try:
        news = parse_news(t.news)
    except Exception:
        news = []

    res.update({
        "name": info.get("shortName") or info.get("longName") or tk,
        "currency": info.get("currency") or "",
        "sector": info.get("sector") or info.get("quoteType") or "",
        "price": price,
        "change_pct": ((price / prev - 1) * 100) if price and prev else None,
        "market_cap": num(info.get("marketCap")),
        "pe": pe, "pe_band": pe_b, "pe_label": PE_LABELS[pe_b],
        "fpe": fpe, "fpe_band": fpe_b, "fpe_label": PE_LABELS[fpe_b],
        "peg": peg, "peg_band": peg_b, "peg_label": PEG_LABELS[peg_b],
        "pegy": pegy, "pegy_band": band_peg(pegy, th["peg"]),
        "growth_pct": growth, "div_yield_pct": dy,
        "low52": lo, "high52": hi,
        "pos52": ((price - lo) / (hi - lo) * 100) if price and lo is not None and hi and hi > lo else None,
        "target": target,
        "upside_pct": ((target / price - 1) * 100) if target and price else None,
        "recommendation": info.get("recommendationKey") or "",
        "verdict": v_txt, "verdict_tone": v_tone,
        "spark": spark, "news": news, "error": None,
    })
    if res["shares"] and res["avg_cost"] and price:
        res["position_value"] = res["shares"] * price
        res["pnl_pct"] = (price / res["avg_cost"] - 1) * 100
    return res


def safe_fetch(entry, th, previous):
    try:
        return fetch_company(entry, th)
    except Exception as e:  # mantém último dado bom, marcado como desatualizado
        tk = norm_ticker(entry["ticker"])
        old = dict(previous.get(tk) or {"ticker": tk, "name": tk})
        old.update({"status": entry.get("status", "watch"), "notes": entry.get("notes", ""),
                    "error": f"{type(e).__name__}: {str(e)[:120]}", "stale": True})
        return old


def fetch_market_news(symbols):
    import yfinance as yf

    seen, out = set(), []
    for s in symbols:
        try:
            for n in parse_news(yf.Ticker(s).news, 6):
                if n["title"] not in seen:
                    seen.add(n["title"])
                    n["via"] = s
                    out.append(n)
        except Exception:
            continue
    out.sort(key=lambda n: n["date"], reverse=True)
    return out[:12]


def build_alerts(items, previous):
    alerts = []
    for c in items:
        if c.get("error") and not c.get("price"):
            alerts.append({"ticker": c["ticker"], "kind": "erro", "text": f"Sem dados: {c['error']}"})
            continue
        ch = c.get("change_pct")
        if ch is not None and abs(ch) >= 5:
            alerts.append({"ticker": c["ticker"], "kind": "movimento",
                           "text": f"{ch:+.1f}% hoje"})
        old = previous.get(c["ticker"])
        if old:
            for key, lab in (("pe_band", "P/E"), ("fpe_band", "P/E forward"), ("peg_band", "PEG")):
                if old.get(key) and c.get(key) and old[key] != c[key]:
                    pl = PEG_LABELS if key == "peg_band" else PE_LABELS
                    alerts.append({"ticker": c["ticker"], "kind": "valorização",
                                   "text": f"{lab}: {pl[old[key]]} → {pl[c[key]]}"})
    return alerts


# ---------------------------------------------------------------- comandos
def cmd_run(_):
    cfg = load_cfg()
    th = cfg["thresholds"]
    previous = {}
    if LATEST.exists():
        previous = {c["ticker"]: c for c in json.loads(LATEST.read_text("utf-8")).get("companies", [])}
    with ThreadPoolExecutor(max_workers=4) as ex:
        items = list(ex.map(lambda e: safe_fetch(e, th, previous), cfg["companies"]))
    now = datetime.now(timezone.utc)
    data = {
        "generated_at": now.isoformat(timespec="seconds"),
        "thresholds": th,
        "companies": items,
        "market_news": fetch_market_news(cfg.get("market_news", [])),
        "alerts": build_alerts(items, previous),
    }
    DATA_DIR.mkdir(exist_ok=True)
    HISTORY.mkdir(exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=1)
    LATEST.write_text(payload, encoding="utf-8")
    (HISTORY / f"{now:%Y-%m-%d}.json").write_text(payload, encoding="utf-8")
    html = TEMPLATE.read_text("utf-8").replace(
        "/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    DASHBOARD.write_text(html, encoding="utf-8")
    ok = sum(1 for c in items if not c.get("error"))
    print(f"{ok}/{len(items)} empresas atualizadas, {len(data['alerts'])} alertas -> {DASHBOARD}")
    for a in data["alerts"]:
        print(f"  [{a['kind']}] {a['ticker']}: {a['text']}")


def cmd_add(a):
    cfg = load_cfg()
    tk = norm_ticker(a.ticker)
    if any(norm_ticker(c["ticker"]) == tk for c in cfg["companies"]):
        sys.exit(f"{tk} já existe na lista (usa 'remove' primeiro para alterar).")
    e = {"ticker": tk, "status": a.status}
    if a.status == "portfolio":
        e.update({"shares": a.shares or 0, "avg_cost": a.avg_cost or 0})
    e["notes"] = a.notes or ""
    cfg["companies"].append(e)
    save_cfg(cfg)
    print(f"Adicionado {tk} ({a.status}).")


def cmd_remove(a):
    cfg = load_cfg()
    tk = norm_ticker(a.ticker)
    n = len(cfg["companies"])
    cfg["companies"] = [c for c in cfg["companies"] if norm_ticker(c["ticker"]) != tk]
    if len(cfg["companies"]) == n:
        sys.exit(f"{tk} não encontrado.")
    save_cfg(cfg)
    print(f"Removido {tk}.")


def cmd_list(_):
    for c in load_cfg()["companies"]:
        print(f"{c['ticker']:10} {c.get('status'):10} {c.get('notes', '')}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run").set_defaults(f=cmd_run)
    sub.add_parser("list").set_defaults(f=cmd_list)
    a = sub.add_parser("add")
    a.add_argument("ticker")
    a.add_argument("--status", choices=["portfolio", "watch"], default="watch")
    a.add_argument("--shares", type=float)
    a.add_argument("--avg-cost", type=float)
    a.add_argument("--notes")
    a.set_defaults(f=cmd_add)
    r = sub.add_parser("remove")
    r.add_argument("ticker")
    r.set_defaults(f=cmd_remove)
    args = p.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
