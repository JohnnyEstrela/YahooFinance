#!/usr/bin/env python3
"""Rotina diária: lê companies.json, vai buscar dados ao Yahoo Finance e gera data.json + index.html."""
import html, json, sys, time, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent


def classify_pe(v, t):
    if v is None or v <= 0:
        return ("n/d", "na")
    if v < t["cheap"]:
        return ("Barato", "cheap")
    if v < t["fair"]:
        return ("Justo", "fair")
    if v < t["pricey"]:
        return ("Caro", "pricey")
    return ("Muito caro", "expensive")


def classify_peg(v, t):
    if v is None or v <= 0:
        return ("n/d", "na")
    if v < t["discount"]:
        return ("Desconto", "cheap")
    if v <= t["fair"]:
        return ("Justo", "fair")
    return ("Premium", "expensive")


def num(x):
    return round(float(x), 2) if isinstance(x, (int, float)) else None


def rss_news(symbol, limit=5):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(urllib.request.urlopen(req, timeout=15).read())
        return [
            {"title": i.findtext("title"), "url": i.findtext("link"),
             "publisher": "Yahoo Finance", "date": i.findtext("pubDate")}
            for i in root.iter("item")
        ][:limit]
    except Exception:
        return []


def get_news(symbol, limit=5):
    out = []
    try:
        for n in yf.Ticker(symbol).news[:limit]:
            c = n.get("content", n)
            url = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or c.get("link")
            out.append({"title": c.get("title"), "url": url,
                        "publisher": (c.get("provider") or {}).get("displayName") or c.get("publisher"),
                        "date": c.get("pubDate") or c.get("providerPublishTime")})
    except Exception:
        pass
    return [n for n in out if n["title"] and n["url"]] or rss_news(symbol, limit)


def fetch(entry, th):
    sym = entry["ticker"].upper().replace(".", "-") if "." in entry["ticker"] and len(entry["ticker"].split(".")[-1]) == 1 else entry["ticker"].upper()
    info = {}
    for attempt in range(3):
        try:
            info = yf.Ticker(sym).info or {}
            break
        except Exception:
            time.sleep(2 ** attempt)
    price = num(info.get("currentPrice") or info.get("regularMarketPrice"))
    pe_t, pe_f = num(info.get("trailingPE")), num(info.get("forwardPE"))
    peg = num(info.get("trailingPegRatio") or info.get("pegRatio"))
    dy = info.get("dividendYield")  # yfinance recente já devolve em %
    shares, cost = entry.get("shares") or 0, entry.get("avg_cost") or 0
    pl = round((price - cost) * shares, 2) if price and shares and cost else None
    pl_pct = round((price / cost - 1) * 100, 2) if price and cost else None
    return {
        "ticker": sym, "status": entry.get("status", "watchlist"), "notes": entry.get("notes", ""),
        "name": info.get("longName") or info.get("shortName") or sym, "currency": info.get("currency", ""),
        "sector": info.get("sector", ""), "price": price,
        "change_pct": num(info.get("regularMarketChangePercent")),
        "market_cap": info.get("marketCap"), "dividend_yield": num(dy),
        "w52_low": num(info.get("fiftyTwoWeekLow")), "w52_high": num(info.get("fiftyTwoWeekHigh")),
        "target": num(info.get("targetMeanPrice")), "recommendation": info.get("recommendationKey", ""),
        "pe_ttm": pe_t, "pe_ttm_class": classify_pe(pe_t, th["pe"]),
        "pe_fwd": pe_f, "pe_fwd_class": classify_pe(pe_f, th["pe"]),
        "peg": peg, "peg_class": classify_peg(peg, th["peg"]),
        "shares": shares, "avg_cost": cost, "pl": pl, "pl_pct": pl_pct,
        "news": get_news(sym),
        "error": None if price else "Sem dados (ticker inválido ou Yahoo indisponível)",
    }


def fmt(v, suf="", d=2):
    return "—" if v is None else f"{v:,.{d}f}{suf}"


def badge(v, cls):
    return f'<span class="b {cls[1]}">{html.escape(cls[0])}</span>'


def metric(label, v, cls, hint):
    return (f'<div class="m"><span class="l">{label}</span><span class="v">{fmt(v)}</span>'
            f'{badge(v, cls)}<span class="h">{hint}</span></div>')


def card(c):
    news = "".join(
        f'<li><a href="{html.escape(n["url"])}" target="_blank" rel="noopener">{html.escape(n["title"])}</a>'
        f'<small>{html.escape(str(n["publisher"] or ""))}</small></li>' for n in c["news"]) or "<li><small>Sem notícias.</small></li>"
    rng = ""
    if c["price"] and c["w52_low"] and c["w52_high"] and c["w52_high"] > c["w52_low"]:
        p = max(0, min(100, (c["price"] - c["w52_low"]) / (c["w52_high"] - c["w52_low"]) * 100))
        rng = f'<div class="rng" title="Intervalo 52 semanas"><i style="left:{p:.0f}%"></i></div><div class="rl"><span>{c["w52_low"]}</span><span>52s</span><span>{c["w52_high"]}</span></div>'
    chg = c["change_pct"]
    pl = f'<div class="pl {"up" if (c["pl"] or 0) >= 0 else "down"}">P/L: {fmt(c["pl"])} {c["currency"]} ({fmt(c["pl_pct"], "%")})</div>' if c["pl"] is not None else ""
    err = f'<p class="err">{c["error"]}</p>' if c["error"] else ""
    return f'''<article class="card" data-status="{c["status"]}" data-name="{html.escape((c["ticker"]+" "+c["name"]).lower())}">
<header><div><h3>{c["ticker"]}</h3><p>{html.escape(c["name"])}</p></div>
<div class="px"><b>{fmt(c["price"])} {c["currency"]}</b><span class="{"up" if (chg or 0) >= 0 else "down"}">{fmt(chg, "%")}</span></div></header>
{err}<div class="metrics">
{metric("P/E (12m passados)", c["pe_ttm"], c["pe_ttm_class"], "o que pagas por cada $1 de lucro do último ano")}
{metric("P/E (próx. 12m)", c["pe_fwd"], c["pe_fwd_class"], "baseado nas estimativas de lucro")}
{metric("PEG", c["peg"], c["peg_class"], "P/E ajustado ao crescimento")}
</div>{rng}{pl}
<div class="facts"><span>Dividendo: {fmt(c["dividend_yield"], "%")}</span><span>Preço-alvo: {fmt(c["target"])}</span><span>Analistas: {html.escape(c["recommendation"] or "—")}</span></div>
{f'<p class="note">📝 {html.escape(c["notes"])}</p>' if c["notes"] else ""}
<details><summary>Notícias ({len(c["news"])})</summary><ul>{news}</ul></details></article>'''


CSS = """
:root{--bg:#f6f7f9;--fg:#1a1d23;--card:#fff;--mut:#6b7280;--bd:#e5e7eb;--cheap:#16a34a;--fair:#2563eb;--pricey:#d97706;--expensive:#dc2626;--na:#9ca3af}
@media(prefers-color-scheme:dark){:root{--bg:#0f1115;--fg:#e8eaed;--card:#181b22;--mut:#9aa0aa;--bd:#2a2f3a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;padding:16px;max-width:1300px;margin:auto}
h1{margin:0 0 4px;font-size:1.5rem}.sub{color:var(--mut);margin:0 0 16px}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}.bar input,.bar button{padding:8px 12px;border:1px solid var(--bd);border-radius:8px;background:var(--card);color:var(--fg);font:inherit}
.bar input{flex:1 1 200px}.bar button.on{background:var(--fg);color:var(--bg)}
.legend{font-size:.85rem;color:var(--mut);margin-bottom:16px;display:flex;flex-wrap:wrap;gap:6px 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:14px}
.card header{display:flex;justify-content:space-between;gap:8px}.card h3{margin:0}.card header p{margin:0;color:var(--mut);font-size:.85rem}
.px{text-align:right}.px b{display:block}.up{color:var(--cheap)}.down{color:var(--expensive)}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}
.m{display:flex;flex-direction:column;gap:2px;background:var(--bg);border-radius:10px;padding:8px}.m .l{font-size:.7rem;color:var(--mut)}.m .v{font-size:1.15rem;font-weight:600}.m .h{display:none;font-size:.7rem;color:var(--mut)}
@media(min-width:700px){.m .h{display:block}}
.b{align-self:flex-start;font-size:.7rem;font-weight:600;padding:1px 8px;border-radius:99px;color:#fff}
.b.cheap{background:var(--cheap)}.b.fair{background:var(--fair)}.b.pricey{background:var(--pricey)}.b.expensive{background:var(--expensive)}.b.na{background:var(--na)}
.rng{height:6px;background:var(--bd);border-radius:3px;position:relative;margin-top:6px}.rng i{position:absolute;top:-3px;width:12px;height:12px;border-radius:50%;background:var(--fair);transform:translateX(-50%)}
.rl{display:flex;justify-content:space-between;font-size:.7rem;color:var(--mut)}
.facts{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:.8rem;color:var(--mut);margin-top:8px}.note,.err{font-size:.85rem}.err{color:var(--expensive)}
details{margin-top:8px}summary{cursor:pointer;font-size:.9rem}li{margin:6px 0}li a{color:var(--fg)}li small{display:block;color:var(--mut)}
.mkt{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:14px;margin-bottom:16px}.mkt h2{margin:0 0 6px;font-size:1.1rem}
footer{color:var(--mut);font-size:.75rem;margin-top:24px}
"""

JS = """const f=document.querySelectorAll('.bar button'),q=document.getElementById('q');let s='all';
function run(){document.querySelectorAll('.card').forEach(c=>{c.style.display=(s=='all'||c.dataset.status==s)&&c.dataset.name.includes(q.value.toLowerCase())?'':'none'})}
f.forEach(b=>b.onclick=()=>{f.forEach(x=>x.classList.remove('on'));b.classList.add('on');s=b.dataset.s;run()});q.oninput=run;"""


def render(cards, market_news, ts, th):
    pe, peg = th["pe"], th["peg"]
    legend = (f'<div class="legend"><span><b>P/E:</b> &lt;{pe["cheap"]} Barato · {pe["cheap"]}–{pe["fair"]} Justo · '
              f'{pe["fair"]}–{pe["pricey"]} Caro · ≥{pe["pricey"]} Muito caro</span>'
              f'<span><b>PEG:</b> &lt;{peg["discount"]} Desconto · {peg["discount"]}–{peg["fair"]} Justo · &gt;{peg["fair"]} Premium</span></div>')
    mk = "".join(f'<li><a href="{html.escape(n["url"])}" target="_blank" rel="noopener">{html.escape(n["title"])}</a></li>' for n in market_news)
    mkt = f'<section class="mkt"><h2>📰 Mercados hoje</h2><ul>{mk}</ul></section>' if mk else ""
    return f'''<!doctype html><html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portefólio</title><style>{CSS}</style></head><body>
<h1>📈 O meu Portefólio</h1><p class="sub">Atualizado: {ts}</p>
<div class="bar"><input id="q" placeholder="Pesquisar empresa…"><button class="on" data-s="all">Todas</button><button data-s="portfolio">Portefólio</button><button data-s="watchlist">A seguir</button></div>
{legend}{mkt}<div class="grid">{"".join(cards)}</div>
<footer>Dados: Yahoo Finance. Informação apenas informativa — não constitui aconselhamento financeiro.</footer>
<script>{JS}</script></body></html>'''


def main():
    cfg = json.loads((HERE / "companies.json").read_text())
    th = cfg["thresholds"]
    seen, data = set(), []
    for e in cfg["companies"]:
        if e["ticker"].upper() in seen:
            continue
        seen.add(e["ticker"].upper())
        data.append(fetch(e, th))
    data.sort(key=lambda c: (c["status"] != "portfolio", c["ticker"]))
    market = get_news("^GSPC", 6)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (HERE / "data.json").write_text(json.dumps({"updated": ts, "companies": data, "market_news": market}, ensure_ascii=False, indent=1))
    (HERE / "index.html").write_text(render([card(c) for c in data], market, ts, th))
    bad = [c["ticker"] for c in data if c["error"]]
    print(f"{len(data)} empresas, falharam: {bad or 'nenhuma'}")


if __name__ == "__main__":
    sys.exit(main())
