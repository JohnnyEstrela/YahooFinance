#!/usr/bin/env python3
"""Atualiza o painel do portefólio: lê watchlist.json, vai buscar dados ao Yahoo Finance
(via yfinance), classifica P/E e PEG e gera data.json + index.html."""
import html
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent
CLASS_BY_INDEX = ["good", "fair", "warn", "bad"]  # cores: do mais barato ao mais caro


def num(v):
    return float(v) if isinstance(v, (int, float)) and v == v else None


def classify(value, cfg, kind):
    """Devolve (etiqueta, nível 0..n). Valores <=0 ou em falta não são classificáveis."""
    if value is None:
        return "N/D", None
    if value <= 0:
        return "Sem lucro" if kind == "pe" else "N/D", None
    for i, limit in enumerate(cfg["limits"]):
        if value < limit:
            return cfg["labels"][i], i
    return cfg["labels"][len(cfg["limits"])], len(cfg["limits"])


def with_retry(fn, tries=3):  # espera 5s, 15s, 30s entre tentativas
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # rate limits e falhas de rede são comuns
            err = e
            time.sleep((5, 15, 30)[i])
    print(f"aviso: {err}", file=sys.stderr)
    return None


def get_news(query, ticker=None):
    """Ticker.news vem muitas vezes vazio com rate limit; a pesquisa serve de alternativa."""
    items = with_retry(lambda: ticker.news) if ticker else None
    return items or with_retry(lambda: yf.Search(query, news_count=8, max_results=1).news)


def parse_news(items, limit):
    out = []
    for n in items or []:
        c = n.get("content") or n  # formato novo vs. antigo
        title = c.get("title")
        url = ((c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url")) or n.get("link")
        if not title or not url:
            continue
        provider = (c.get("provider") or {}).get("displayName") or n.get("publisher") or ""
        when = c.get("pubDate") or ""
        if not when and n.get("providerPublishTime"):
            when = datetime.fromtimestamp(n["providerPublishTime"], timezone.utc).isoformat()
        out.append({"title": title, "url": url, "source": provider, "date": when[:10]})
        if len(out) >= limit:
            break
    return out


def fetch_company(entry, th, news_n):
    sym = entry["ticker"].strip().upper()
    if sym.endswith((".A", ".B")):  # classes de ações US: BRK.B -> BRK-B
        sym = sym.replace(".", "-")
    t = yf.Ticker(sym)
    info = with_retry(lambda: t.info) or {}
    price = num(info.get("currentPrice") or info.get("regularMarketPrice"))
    pe, fpe = num(info.get("trailingPE")), num(info.get("forwardPE"))
    peg = num(info.get("trailingPegRatio")) or num(info.get("pegRatio"))
    growth = num(info.get("earningsGrowth"))
    if peg is None and fpe and growth and growth > 0:
        peg = fpe / (growth * 100)
    news = parse_news(get_news(sym, t), news_n)
    row = {
        "ticker": sym,
        "name": info.get("shortName") or info.get("longName") or sym,
        "sector": info.get("sector") or "",
        "currency": info.get("currency") or "",
        "price": price,
        "change_pct": num(info.get("regularMarketChangePercent")),
        "market_cap": num(info.get("marketCap")),
        "div_yield_pct": num(info.get("dividendYield")),
        "low52": num(info.get("fiftyTwoWeekLow")),
        "high52": num(info.get("fiftyTwoWeekHigh")),
        "pe": pe, "fwd_pe": fpe, "peg": peg,
        "news": news,
        "note": entry.get("note", ""),
        "ok": price is not None,
    }
    row["pe_label"], row["pe_lvl"] = classify(pe, th["pe"], "pe")
    row["fpe_label"], row["fpe_lvl"] = classify(fpe, th["pe"], "pe")
    row["peg_label"], row["peg_lvl"] = classify(peg, th["peg"], "peg")
    shares, cost = num(entry.get("shares")), num(entry.get("avg_cost"))
    if shares and cost and price:
        row["shares"], row["avg_cost"] = shares, cost
        row["value"] = shares * price
        row["pl_pct"] = (price / cost - 1) * 100
    return row


def fmt(v, d=2, suffix=""):
    return "N/D" if v is None else f"{v:,.{d}f}{suffix}"


def big(v):
    if v is None:
        return "N/D"
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6)):
        if v >= div:
            return f"{v / div:.1f}{unit}"
    return f"{v:,.0f}"


def badge(label, lvl, value, d=1):
    cls = "na" if lvl is None else CLASS_BY_INDEX[min(lvl, 3)]
    return (f'<div class="metric"><span class="v">{fmt(value, d)}</span>'
            f'<span class="b {cls}">{html.escape(label)}</span></div>')


def card(r, kind):
    if not r["ok"]:
        return (f'<article class="card" data-kind="{kind}"><h3>{html.escape(r["ticker"])}</h3>'
                '<p class="muted">Sem dados (ticker inválido ou limite do Yahoo). '
                'Verifica o símbolo em watchlist.json.</p></article>')
    chg = r["change_pct"]
    chg_html = "" if chg is None else (
        f'<span class="chg {"up" if chg >= 0 else "down"}">{chg:+.2f}%</span>')
    pos = ""
    if "value" in r:
        pos = (f'<p class="pos">{r["shares"]:g} ações · custo {fmt(r["avg_cost"])} · valor '
               f'{fmt(r["value"])} {r["currency"]} · '
               f'<b class="{"up" if r["pl_pct"] >= 0 else "down"}">{r["pl_pct"]:+.1f}%</b></p>')
    rng = ""
    if r["low52"] and r["high52"] and r["high52"] > r["low52"]:
        p = max(0, min(100, (r["price"] - r["low52"]) / (r["high52"] - r["low52"]) * 100))
        rng = (f'<div class="range" title="Intervalo 52 semanas"><i style="left:{p:.0f}%"></i></div>'
               f'<div class="rl"><span>{fmt(r["low52"])}</span><span>52 sem.</span>'
               f'<span>{fmt(r["high52"])}</span></div>')
    news = "".join(
        f'<li><a href="{html.escape(n["url"])}" target="_blank" rel="noopener">'
        f'{html.escape(n["title"])}</a><small>{html.escape(n["source"])} · {n["date"]}</small></li>'
        for n in r["news"]) or '<li class="muted">Sem notícias recentes.</li>'
    sector = f' · {html.escape(r["sector"])}' if r["sector"] else ""
    note = f'<p class="note">{html.escape(r["note"])}</p>' if r["note"] else ""
    dy = fmt(r["div_yield_pct"], 2, "%")
    return f"""<article class="card" data-kind="{kind}" data-name="{html.escape(r['ticker'])}"
  data-pe="{r['pe'] or 9999}" data-peg="{r['peg'] or 9999}" data-chg="{chg or 0}">
  <header><div><h3>{html.escape(r['ticker'])}</h3>
  <p class="muted">{html.escape(r['name'])}{sector}</p></div>
  <div class="px"><b>{fmt(r['price'])}</b> <small>{r['currency']}</small> {chg_html}</div></header>
  {pos}{note}
  <div class="metrics">
    <div><small>P/E (12 m passados)</small>{badge(r['pe_label'], r['pe_lvl'], r['pe'])}</div>
    <div><small>P/E (próx. 12 m)</small>{badge(r['fpe_label'], r['fpe_lvl'], r['fwd_pe'])}</div>
    <div><small>PEG</small>{badge(r['peg_label'], r['peg_lvl'], r['peg'])}</div>
  </div>
  <p class="meta">Cap. {big(r['market_cap'])} · Dividendo {dy}</p>{rng}
  <ul class="news">{news}</ul>
</article>"""


CSS = """
:root{--bg:#f6f7f9;--fg:#15181d;--card:#fff;--mut:#6b7280;--line:#e5e7eb;--good:#15803d;--fair:#a16207;
--warn:#c2410c;--bad:#b91c1c;--acc:#2563eb}
@media(prefers-color-scheme:dark){:root{--bg:#0e1116;--fg:#e8eaed;--card:#171b22;--mut:#9aa3af;
--line:#262c36;--good:#4ade80;--fair:#facc15;--warn:#fb923c;--bad:#f87171;--acc:#60a5fa}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
.wrap{max-width:1200px;margin:0 auto;padding:16px}
h1{font-size:1.4rem;margin:0}h2{font-size:1.05rem;margin:28px 0 10px}
.muted,small,.meta{color:var(--mut)}.top{display:flex;flex-wrap:wrap;gap:8px;
justify-content:space-between;align-items:center}
.tools{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0}
button,select{background:var(--card);color:var(--fg);border:1px solid var(--line);
border-radius:8px;padding:6px 12px;font:inherit;cursor:pointer}
button.on{background:var(--acc);border-color:var(--acc);color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(310px,100%),1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.card header{display:flex;justify-content:space-between;gap:8px}.card h3{margin:0}
.card p{margin:4px 0}.px{text-align:right;white-space:nowrap}.px b{font-size:1.2rem}
.up{color:var(--good)}.down{color:var(--bad)}.note{font-style:italic;color:var(--mut)}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0}
.metrics small{display:block;font-size:.7rem;min-height:2em}
.metric{display:flex;flex-direction:column;gap:3px}.v{font-size:1.15rem;font-weight:600}
.b{font-size:.72rem;font-weight:600;border-radius:99px;padding:1px 8px;width:fit-content;
border:1px solid currentColor}
.b.good{color:var(--good)}.b.fair{color:var(--fair)}.b.warn{color:var(--warn)}
.b.bad{color:var(--bad)}.b.na{color:var(--mut)}
.range{position:relative;height:6px;background:var(--line);border-radius:3px;margin-top:8px}
.range i{position:absolute;top:-3px;width:3px;height:12px;background:var(--acc);border-radius:2px}
.rl{display:flex;justify-content:space-between;font-size:.7rem;color:var(--mut)}
.news{list-style:none;padding:0;margin:12px 0 0;border-top:1px solid var(--line)}
.news li{padding:7px 0;border-bottom:1px solid var(--line)}.news li:last-child{border:0}
.news a{color:var(--fg);text-decoration:none}.news a:hover{color:var(--acc)}
.news small{display:block}.legend{font-size:.8rem;color:var(--mut)}
.mkt li{list-style:none;padding:6px 0;border-bottom:1px solid var(--line)}
.mkt{padding:0;margin:0;background:var(--card);border-radius:12px;padding:6px 14px;
border:1px solid var(--line)}.mkt a{color:var(--fg);text-decoration:none}
.mkt small{display:block}.hide{display:none!important}
@media(max-width:480px){.wrap{padding:12px}.metrics{gap:4px}}
"""

JS = """
const cards=[...document.querySelectorAll('.card')];let kind='all';
function apply(){const q=document.getElementById('q').value.toLowerCase();
cards.forEach(c=>c.classList.toggle('hide',!((kind==='all'||c.dataset.kind===kind)&&
(c.dataset.name||'').toLowerCase().includes(q))));
document.querySelectorAll('section.g').forEach(s=>s.classList.toggle('hide',
!s.querySelector('.card:not(.hide)')))}
document.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{kind=b.dataset.f;
document.querySelectorAll('[data-f]').forEach(x=>x.classList.toggle('on',x===b));apply()});
document.getElementById('q').oninput=apply;
document.getElementById('s').onchange=e=>{const k=e.target.value;
document.querySelectorAll('.grid').forEach(g=>{[...g.children].sort((a,b)=>k==='name'?
a.dataset.name.localeCompare(b.dataset.name):k==='chg'?b.dataset.chg-a.dataset.chg:
a.dataset[k]-b.dataset[k]).forEach(c=>g.appendChild(c))})};
"""


def render(rows_h, rows_w, mkt, th, stamp):
    def section(title, rows, kind):
        if not rows:
            return ""
        return (f'<section class="g"><h2>{title}</h2><div class="grid">'
                + "".join(card(r, kind) for r in rows) + "</div></section>")

    pe, peg = th["pe"], th["peg"]
    legend = ("P/E: " + " · ".join(
        f'{l} {"&lt;" + str(pe["limits"][i]) if i < len(pe["limits"]) else "≥" + str(pe["limits"][-1])}'
        for i, l in enumerate(pe["labels"]))
        + " &nbsp;|&nbsp; PEG: " + " · ".join(
        f'{l} {"&lt;" + str(peg["limits"][i]) if i < len(peg["limits"]) else "≥" + str(peg["limits"][-1])}'
        for i, l in enumerate(peg["labels"])))
    mk = "".join(
        f'<li><a href="{html.escape(n["url"])}" target="_blank" rel="noopener">'
        f'{html.escape(n["title"])}</a><small>{html.escape(n["source"])} · {n["date"]}</small></li>'
        for n in mkt) or '<li class="muted">Sem notícias de mercado.</li>'
    total = sum(r["value"] for r in rows_h if "value" in r)
    tot = f' · valor total (posições preenchidas): {total:,.0f}' if total else ""
    return f"""<!doctype html><html lang="pt"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Portefólio</title>
<style>{CSS}</style></head><body><div class="wrap">
<div class="top"><h1>Portefólio &amp; Watchlist</h1><small>Atualizado {stamp}{tot}</small></div>
<p class="legend">{legend}</p>
<div class="tools"><button data-f="all" class="on">Todas</button>
<button data-f="holding">Portefólio</button><button data-f="watch">A seguir</button>
<input id="q" placeholder="Procurar ticker" style="background:var(--card);color:var(--fg);
border:1px solid var(--line);border-radius:8px;padding:6px 10px">
<select id="s"><option value="name">Ordenar: nome</option><option value="pe">P/E ↑</option>
<option value="peg">PEG ↑</option><option value="chg">Variação ↓</option></select></div>
{section("O meu portefólio", rows_h, "holding")}{section("A seguir", rows_w, "watch")}
<section><h2>Notícias de mercado</h2><ul class="mkt">{mk}</ul></section>
<p class="legend">Dados do Yahoo Finance, podem ter atraso. Informação indicativa, não é
aconselhamento financeiro. P/E e PEG baixos não significam por si só boa compra.</p>
</div><script>{JS}</script></body></html>"""


def main():
    cfg = json.loads((HERE / "watchlist.json").read_text())
    th, n = cfg["thresholds"], cfg.get("news_per_company", 4)
    seen = set()

    def fetch_all(entries):
        out = []
        for e in entries:
            if e["ticker"].upper() in seen:
                continue
            seen.add(e["ticker"].upper())
            out.append(fetch_company(e, th, n))
            time.sleep(0.5)
        return out

    holdings = fetch_all(cfg.get("holdings", []))
    watching = fetch_all(cfg.get("watching", []))
    # se o Yahoo falhar para uma empresa, mantém os últimos dados bons (marcados como antigos)
    try:
        old = json.loads((HERE / "data.json").read_text())
        prev = {r["ticker"]: r for r in old["holdings"] + old["watching"] if r["ok"]}
    except (OSError, ValueError, KeyError):
        prev = {}
    for rows in (holdings, watching):
        for i, r in enumerate(rows):
            if not r["ok"] and r["ticker"] in prev:
                rows[i] = {**prev[r["ticker"]], "note": (prev[r["ticker"]]["note"] + " (dados antigos)").strip()}
    mkt, urls = [], set()
    for q in cfg.get("market_news_queries", []):
        for item in parse_news(get_news(q), 6):
            if item["url"] not in urls:
                urls.add(item["url"])
                mkt.append(item)
    mkt = sorted(mkt, key=lambda x: x["date"], reverse=True)[: cfg.get("market_news_total", 8)]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (HERE / "data.json").write_text(json.dumps(
        {"updated": stamp, "holdings": holdings, "watching": watching, "market_news": mkt},
        ensure_ascii=False, indent=1))
    (HERE / "index.html").write_text(render(holdings, watching, mkt, th, stamp))
    bad = [r["ticker"] for r in holdings + watching if not r["ok"]]
    print(f"{len(holdings)} no portefólio, {len(watching)} a seguir, {len(mkt)} notícias"
          + (f"; sem dados: {', '.join(bad)}" if bad else ""))


if __name__ == "__main__":
    main()
