"""Atualiza dados do portefólio e gera portfolio/report/index.html (+ latest.json).

Uso: python portfolio/update.py [--config portfolio/portfolio.json]
"""
import argparse
import html
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests
import yfinance as yf

HERE = Path(__file__).parent
RSS = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={}&region=US&lang=en-US"


def classify_pe(v, t):
    if v is None or v <= 0:
        return ("n/d", "na")
    if v < t["barato"]:
        return ("Barato", "cheap")
    if v < t["justo"]:
        return ("Justo", "fair")
    if v < t["caro"]:
        return ("Caro", "pricey")
    return ("Muito caro", "expensive")


def classify_peg(v, t):
    if v is None or v <= 0:
        return ("n/d", "na")
    if v < t["desconto"]:
        return ("Desconto", "cheap")
    if v <= t["justo"]:
        return ("Justo", "fair")
    return ("Premium", "expensive")


def rss_news(symbol, limit=5):
    try:
        r = requests.get(RSS.format(symbol), timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        out = []
        for it in ET.fromstring(r.content).iter("item"):
            out.append({
                "title": (it.findtext("title") or "").strip(),
                "link": (it.findtext("link") or "").strip(),
                "publisher": "Yahoo Finance",
                "date": (it.findtext("pubDate") or "")[:22],
            })
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []


def get_news(tk, symbol, limit=5):
    out = []
    try:
        for n in tk.news or []:
            c = n.get("content", n)
            link = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or c.get("link")
            if c.get("title") and link:
                out.append({
                    "title": c["title"],
                    "link": link,
                    "publisher": (c.get("provider") or {}).get("displayName") or c.get("publisher", ""),
                    "date": (c.get("pubDate") or "")[:10],
                })
    except Exception:
        pass
    return (out or rss_news(symbol, limit))[:limit]


def num(x):
    return x if isinstance(x, (int, float)) and x == x else None


def fetch(c, th):
    sym = c["ticker"]
    tk = yf.Ticker(sym)
    row = {**c, "error": None}
    try:
        i = tk.info
        price = num(i.get("currentPrice")) or num(i.get("regularMarketPrice"))
        peg = num(i.get("trailingPegRatio")) or num(i.get("pegRatio"))
        row.update(
            name=i.get("longName") or i.get("shortName") or sym,
            currency=i.get("currency", ""),
            sector=i.get("sector", ""),
            price=price,
            prev_close=num(i.get("regularMarketPreviousClose")),
            pe_ttm=num(i.get("trailingPE")),
            pe_fwd=num(i.get("forwardPE")),
            peg=peg,
            eps_ttm=num(i.get("trailingEps")),
            eps_fwd=num(i.get("forwardEps")),
            div_yield=num(i.get("dividendYield")),
            market_cap=num(i.get("marketCap")),
            low52=num(i.get("fiftyTwoWeekLow")),
            high52=num(i.get("fiftyTwoWeekHigh")),
            target=num(i.get("targetMeanPrice")),
            recommendation=i.get("recommendationKey", ""),
        )
        if price and row["prev_close"]:
            row["day_change_pct"] = (price / row["prev_close"] - 1) * 100
        sh, ac = c.get("shares") or 0, c.get("avg_cost") or 0
        if price and sh and ac:
            row["position_value"] = price * sh
            row["pl_pct"] = (price / ac - 1) * 100
    except Exception as e:
        row["error"] = str(e)[:120]
    row["news"] = get_news(tk, sym)
    row["pe_ttm_label"], row["pe_ttm_cls"] = classify_pe(row.get("pe_ttm"), th["pe"])
    row["pe_fwd_label"], row["pe_fwd_cls"] = classify_pe(row.get("pe_fwd"), th["pe"])
    row["peg_label"], row["peg_cls"] = classify_peg(row.get("peg"), th["peg"])
    return row


def f(v, d=2, suf=""):
    return "—" if v is None else f"{v:,.{d}f}{suf}"


def card(r):
    e = html.escape
    if r.get("error") and not r.get("price"):
        body = f'<p class="err">Sem dados: {e(r["error"])}</p>'
    else:
        chg = r.get("day_change_pct")
        chg_html = "" if chg is None else f'<span class="chg {"up" if chg >= 0 else "down"}">{chg:+.2f}%</span>'
        pl = r.get("pl_pct")
        pos = "" if pl is None else (
            f'<div class="pos">Posição: {f(r.get("position_value"), 0)} {e(r["currency"])} · '
            f'<span class="{"up" if pl >= 0 else "down"}">{pl:+.1f}%</span></div>')
        rng = ""
        if r.get("low52") and r.get("high52") and r.get("price"):
            p = max(0, min(100, (r["price"] - r["low52"]) / (r["high52"] - r["low52"]) * 100))
            rng = (f'<div class="rng"><span>{f(r["low52"])}</span><div class="bar"><i style="left:{p:.0f}%"></i></div>'
                   f'<span>{f(r["high52"])}</span></div>')
        metrics = [
            ("P/E (últimos 12m)", f(r.get("pe_ttm"), 1), r["pe_ttm_label"], r["pe_ttm_cls"]),
            ("P/E (próx. 12m)", f(r.get("pe_fwd"), 1), r["pe_fwd_label"], r["pe_fwd_cls"]),
            ("PEG", f(r.get("peg"), 2), r["peg_label"], r["peg_cls"]),
        ]
        m = "".join(
            f'<div class="m {c}"><small>{e(n)}</small><b>{v}</b><em>{e(l)}</em></div>'
            for n, v, l, c in metrics)
        extra = (f'<div class="kv"><span>Dividend yield</span><b>{f(r.get("div_yield"), 2, "%")}</b></div>'
                 f'<div class="kv"><span>Preço-alvo analistas</span><b>{f(r.get("target"))}</b></div>'
                 f'<div class="kv"><span>Recomendação</span><b>{e(r.get("recommendation") or "—")}</b></div>')
        body = f'<div class="metrics">{m}</div>{rng}{pos}<div class="extra">{extra}</div>'
    news = "".join(
        f'<li><a href="{e(n["link"])}" target="_blank" rel="noopener">{e(n["title"])}</a>'
        f'<small>{e(n["publisher"])} {e(n["date"])}</small></li>' for n in r["news"]) or "<li>Sem notícias.</li>"
    notes = f'<p class="notes">📝 {e(r["notes"])}</p>' if r.get("notes") else ""
    return (f'<article class="card" data-status="{e(r["status"])}">'
            f'<header><div><h3>{e(r["ticker"])}</h3><small>{e(r.get("name", ""))}</small></div>'
            f'<div class="px">{f(r.get("price"))} <small>{e(r.get("currency", ""))}</small> {"" if r.get("error") and not r.get("price") else chg_html}</div></header>'
            f'{body}{notes}<details><summary>Notícias ({len(r["news"])})</summary><ul>{news}</ul></details></article>')


CSS = """
:root{--bg:#f5f6f8;--fg:#14171f;--card:#fff;--mut:#667085;--bd:#e3e6ec;--cheap:#12805c;--fair:#2563eb;--pricey:#b7791f;--expensive:#c0392b;--na:#98a2b3}
@media(prefers-color-scheme:dark){:root{--bg:#0e1116;--fg:#e8eaee;--card:#171b23;--mut:#9aa3b2;--bd:#262c38;--cheap:#3ecf9b;--fair:#6ea0ff;--pricey:#e5b252;--expensive:#ff7b6b;--na:#6b7686}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif}
.wrap{max-width:1200px;margin:auto;padding:16px}h1{margin:.2em 0}.sub{color:var(--mut)}
.bar-top{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}
.bar-top button{border:1px solid var(--bd);background:var(--card);color:var(--fg);padding:6px 14px;border-radius:99px;cursor:pointer;font:inherit}
.bar-top button.on{background:var(--fg);color:var(--bg)}
.legend{font-size:13px;color:var(--mut);background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:10px 14px;margin-bottom:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:14px}
.card header{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.card h3{margin:0;font-size:20px}.card small{color:var(--mut)}.px{font-weight:600;text-align:right}
.chg{font-size:13px;margin-left:4px}.up{color:var(--cheap)}.down{color:var(--expensive)}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}
.m{border-radius:10px;padding:8px;text-align:center;border:1px solid var(--bd);border-top:3px solid var(--c)}
.m small{display:block;font-size:11px}.m b{font-size:20px}.m em{display:block;font-style:normal;font-size:12px;color:var(--c);font-weight:600}
.cheap{--c:var(--cheap)}.fair{--c:var(--fair)}.pricey{--c:var(--pricey)}.expensive{--c:var(--expensive)}.na{--c:var(--na)}
.rng{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--mut)}.rng .bar{flex:1;height:4px;background:var(--bd);border-radius:2px;position:relative}
.rng i{position:absolute;top:-3px;width:10px;height:10px;border-radius:50%;background:var(--fair);margin-left:-5px}
.extra{margin-top:8px}.kv{display:flex;justify-content:space-between;font-size:13px;padding:2px 0}.kv span{color:var(--mut)}
.pos{font-size:13px;margin-top:6px}.notes,.err{font-size:13px;color:var(--mut)}.err{color:var(--expensive)}
details{margin-top:8px;font-size:13px}summary{cursor:pointer;color:var(--mut)}ul{padding-left:18px;margin:6px 0}li{margin-bottom:6px}li small{display:block}a{color:var(--fair)}
h2{margin:24px 0 8px}.mkt{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:6px 14px}
"""
JS = """const b=document.querySelectorAll('.bar-top button');b.forEach(x=>x.onclick=()=>{b.forEach(y=>y.classList.remove('on'));x.classList.add('on');
document.querySelectorAll('.card').forEach(c=>c.hidden=x.dataset.f!=='all'&&c.dataset.status!==x.dataset.f)});"""


def render(rows, market, cfg, stamp):
    th = cfg["thresholds"]
    e = html.escape
    leg = (f"<b>P/E:</b> &lt;{th['pe']['barato']} Barato · &lt;{th['pe']['justo']} Justo · "
           f"&lt;{th['pe']['caro']} Caro · ≥{th['pe']['caro']} Muito caro &nbsp;|&nbsp; "
           f"<b>PEG:</b> &lt;{th['peg']['desconto']} Desconto · {th['peg']['desconto']}–{th['peg']['justo']} Justo · "
           f"&gt;{th['peg']['justo']} Premium")
    mk = "".join(
        f'<li><a href="{e(n["link"])}" target="_blank" rel="noopener">{e(n["title"])}</a><small>{e(n["publisher"])} {e(n["date"])}</small></li>'
        for n in market) or "<li>Sem notícias.</li>"
    return (f'<!doctype html><html lang="pt"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>Portefólio</title><style>{CSS}</style></head><body><div class="wrap">'
            f'<h1>📊 Portefólio &amp; Watchlist</h1><div class="sub">Atualizado {stamp}</div>'
            f'<div class="bar-top"><button class="on" data-f="all">Todas</button><button data-f="portfolio">Portefólio</button><button data-f="watchlist">A seguir</button></div>'
            f'<div class="legend">{leg}</div><div class="grid">{"".join(card(r) for r in rows)}</div>'
            f'<h2>Notícias de mercado</h2><div class="mkt"><ul>{mk}</ul></div>'
            f'<p class="sub">Dados Yahoo Finance, podem ter atraso. Informação, não aconselhamento financeiro.</p>'
            f'</div><script>{JS}</script></body></html>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(HERE / "portfolio.json"))
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    rows = [fetch(c, cfg["thresholds"]) for c in cfg["companies"]]
    market, seen = [], set()
    for s in cfg.get("market_news_symbols", []):
        for n in rss_news(s, 4):
            if n["title"] not in seen:
                seen.add(n["title"])
                market.append(n)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = HERE / "report"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(render(rows, market, cfg, stamp))
    (out / "latest.json").write_text(json.dumps({"updated": stamp, "companies": rows, "market_news": market}, indent=1))
    bad = [r["ticker"] for r in rows if r.get("error") and not r.get("price")]
    print(f"{len(rows)} empresas, {len(market)} notícias de mercado; falhas: {bad or 'nenhuma'}")
    return 1 if len(bad) == len(rows) else 0


if __name__ == "__main__":
    sys.exit(main())
