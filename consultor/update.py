"""Gera consultor/dashboard.html e consultor/data.json a partir de consultor/portfolio.json."""
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent


def num(x):
    return x if isinstance(x, (int, float)) and x == x else None


def classify_pe(v, lim):
    if v is None:
        return ("n/d", "nd")
    if v <= 0:
        return ("Sem lucros", "bad")
    if v < lim["barato"]:
        return ("Barato", "cheap")
    if v <= lim["fair"]:
        return ("Fair Value", "fair")
    if v <= lim["caro"]:
        return ("Pricey", "pricey")
    return ("Expensive", "exp")


def classify_peg(v, lim):
    if v is None:
        return ("n/d", "nd")
    if v < 0:
        return ("Sem crescimento", "bad")
    if v < lim["desconto"]:
        return ("Discount", "cheap")
    if v <= lim["fair"]:
        return ("Fair", "fair")
    return ("Premium", "exp")


def get_news(t, limit=4):
    out = []
    try:
        for n in (t.news or [])[:limit]:
            c = n.get("content", n)
            url = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or n.get("link")
            if c.get("title") and url:
                out.append({"title": c["title"], "url": url,
                            "src": (c.get("provider") or {}).get("displayName") or n.get("publisher", ""),
                            "date": (c.get("pubDate") or "")[:10]})
    except Exception:
        pass
    if not out:  # fallback: RSS do Yahoo Finance
        try:
            import requests
            import xml.etree.ElementTree as ET
            r = requests.get(f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={t.ticker}&region=US&lang=en-US",
                             timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            for it in ET.fromstring(r.text).iter("item"):
                out.append({"title": it.findtext("title"), "url": it.findtext("link"), "src": "Yahoo Finance",
                            "date": (it.findtext("pubDate") or "")[5:16]})
                if len(out) >= limit:
                    break
        except Exception:
            pass
    return out


def fetch(entry, cfg):
    tk = entry["ticker"].upper().replace(".", "-") if entry["ticker"].count(".") == 1 and len(entry["ticker"].split(".")[1]) == 1 else entry["ticker"].upper()
    t = yf.Ticker(tk)
    i = t.info or {}
    price = num(i.get("currentPrice") or i.get("regularMarketPrice"))
    pe, fpe = num(i.get("trailingPE")), num(i.get("forwardPE"))
    peg = num(i.get("trailingPegRatio")) or num(i.get("pegRatio"))
    g = num(i.get("earningsGrowth"))
    if peg is None and fpe and g and g > 0:
        peg = fpe / (g * 100)
    prev = num(i.get("previousClose"))
    d = {
        "ticker": tk, "status": entry.get("status", "watchlist"),
        "name": i.get("longName") or tk, "sector": i.get("sector", ""),
        "currency": i.get("currency", ""), "price": price,
        "change_pct": ((price / prev - 1) * 100) if price and prev else None,
        "pe": pe, "fpe": fpe, "peg": peg, "div_yield": num(i.get("dividendYield")),
        "target": num(i.get("targetMeanPrice")), "rec": i.get("recommendationKey", ""),
        "pe_class": classify_pe(pe, cfg["pe"]), "fpe_class": classify_pe(fpe, cfg["pe"]),
        "peg_class": classify_peg(peg, cfg["peg"]), "news": get_news(t),
    }
    if entry.get("shares") and price:
        d["value"] = entry["shares"] * price
        if entry.get("avg_cost"):
            d["pnl_pct"] = (price / entry["avg_cost"] - 1) * 100
    return d


def f(v, nd=2, suf=""):
    return "n/d" if v is None else f"{v:,.{nd}f}{suf}"


def card(d):
    e = html.escape
    metrics = "".join(
        f'<div class="m"><span class="l">{lbl}</span><b>{f(val)}</b><i class="b {c[1]}">{c[0]}</i></div>'
        for lbl, val, c in [("P/E (12m)", d["pe"], d["pe_class"]), ("P/E (next 12m)", d["fpe"], d["fpe_class"]),
                            ("PEG", d["peg"], d["peg_class"])])
    ch = d["change_pct"]
    extra = []
    if d["target"]: extra.append(f'Alvo analistas: {f(d["target"])} ({e(d["rec"])})')
    if d["div_yield"]: extra.append(f'Dividendo: {f(d["div_yield"], 2, "%")}')
    if "value" in d: extra.append(f'Posição: {f(d["value"], 0)} {d["currency"]}' + (f' ({f(d["pnl_pct"], 1, "%")})' if "pnl_pct" in d else ""))
    news = "".join(f'<li><a href="{e(n["url"])}" target="_blank" rel="noopener">{e(n["title"])}</a> <small>{e(n["src"])} {e(n["date"])}</small></li>' for n in d["news"]) or "<li><small>Sem notícias disponíveis.</small></li>"
    return f'''<article class="card" data-s="{d["status"]}"><header><div><h2>{e(d["ticker"])}</h2><small>{e(d["name"])} · {e(d["sector"])}</small></div>
<div class="p"><b>{f(d["price"])} {e(d["currency"])}</b><span class="{"up" if (ch or 0) >= 0 else "dn"}">{f(ch, 2, "%")}</span></div></header>
<div class="ms">{metrics}</div><p class="x">{" · ".join(extra)}</p><ul>{news}</ul></article>'''


PAGE = """<!doctype html><html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Consultor Financeiro</title><style>
:root{--bg:#f6f7f9;--fg:#15181d;--card:#fff;--mut:#6b7280;--bd:#e5e7eb;--cheap:#15803d;--fair:#2563eb;--pricey:#b45309;--exp:#b91c1c;--bad:#6b7280;--nd:#9ca3af}
@media(prefers-color-scheme:dark){:root{--bg:#0e1116;--fg:#e6e8eb;--card:#171b22;--mut:#9aa3af;--bd:#2a303a;--cheap:#4ade80;--fair:#60a5fa;--pricey:#fbbf24;--exp:#f87171}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;padding:16px;max-width:1200px;margin:auto}
h1{margin:.2em 0}.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:12px 0}.bar button{border:1px solid var(--bd);background:var(--card);color:var(--fg);padding:6px 14px;border-radius:99px;cursor:pointer}.bar button.on{background:var(--fg);color:var(--bg)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:14px}.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px}
.card header{display:flex;justify-content:space-between;gap:8px}.card h2{margin:0}small{color:var(--mut)}.p{text-align:right}.p span{display:block}.up{color:var(--cheap)}.dn{color:var(--exp)}
.ms{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}.m{border:1px solid var(--bd);border-radius:8px;padding:6px;text-align:center}.m .l{display:block;font-size:11px;color:var(--mut)}.m b{font-size:18px}
.b{display:block;font-style:normal;font-size:11px;font-weight:600}.cheap{color:var(--cheap)}.fair{color:var(--fair)}.pricey{color:var(--pricey)}.exp{color:var(--exp)}.bad{color:var(--bad)}.nd{color:var(--nd)}
.x{font-size:13px;color:var(--mut);margin:.4em 0}ul{padding-left:18px;margin:.4em 0;font-size:13px}a{color:var(--fair)}footer{margin:20px 0;color:var(--mut);font-size:12px}
</style></head><body><h1>📈 Consultor Financeiro</h1><small>Atualizado: __TS__</small>
<div class="bar"><button class="on" data-f="all">Todas</button><button data-f="portfolio">Portefólio</button><button data-f="watchlist">Watchlist</button></div>
<div class="grid">__CARDS__</div>
<footer>P/E: &lt;__B__ Barato · ≤__F__ Fair Value · ≤__C__ Pricey · acima Expensive. PEG: &lt;__D__ Discount · ≤__PF__ Fair · acima Premium. Dados Yahoo Finance; informação, não aconselhamento financeiro.</footer>
<script>document.querySelectorAll('.bar button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.bar button').forEach(x=>x.classList.toggle('on',x===b));
document.querySelectorAll('.card').forEach(c=>c.style.display=(b.dataset.f==='all'||c.dataset.s===b.dataset.f)?'':'none')})</script></body></html>"""


def main():
    cfg = json.loads((HERE / "portfolio.json").read_text())
    lim = cfg["limites"]
    data, errors = [], []
    for e in cfg["empresas"]:
        try:
            data.append(fetch(e, lim))
        except Exception as ex:
            errors.append(f'{e["ticker"]}: {ex}')
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    page = (PAGE.replace("__TS__", ts).replace("__CARDS__", "".join(card(d) for d in data))
            .replace("__B__", str(lim["pe"]["barato"])).replace("__F__", str(lim["pe"]["fair"]))
            .replace("__C__", str(lim["pe"]["caro"])).replace("__D__", str(lim["peg"]["desconto"]))
            .replace("__PF__", str(lim["peg"]["fair"])))
    (HERE / "dashboard.html").write_text(page)
    (HERE / "data.json").write_text(json.dumps({"updated": ts, "empresas": data, "erros": errors}, indent=1, ensure_ascii=False))
    print(f"{len(data)} empresas, {len(errors)} erros", *errors, sep="\n")
    return 1 if errors and not data else 0


if __name__ == "__main__":
    sys.exit(main())
