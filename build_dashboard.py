#!/usr/bin/env python3
"""Gera docs/dashboard.html a partir de portfolio.json + data/snapshot.json."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).parent
cfg = json.loads((ROOT / "portfolio.json").read_text())
snap = json.loads((ROOT / "data/snapshot.json").read_text())
T = cfg["thresholds"]


def pe_class(v):
    if v is None or v <= 0:
        return ("n/d", "na")
    if v < T["pe"]["cheap"]:
        return ("Barato", "good")
    if v < T["pe"]["fair"]:
        return ("Fair Value", "fair")
    if v < T["pe"]["pricey"]:
        return ("Caro", "warn")
    return ("Muito caro", "bad")


def peg_class(v):
    if v is None or v <= 0:
        return ("n/d", "na")
    if v < T["peg"]["discount"]:
        return ("Desconto", "good")
    if v <= T["peg"]["fair"]:
        return ("Fair", "fair")
    return ("Premium", "bad")


def fmt(v, d=2, suffix=""):
    return "—" if v is None else f"{v:,.{d}f}{suffix}"


def metric(label, v, cls_fn, hint):
    txt, c = cls_fn(v)
    return (f'<div class="m"><span class="l">{label}</span><b>{fmt(v)}</b>'
            f'<span class="tag {c}">{txt}</span><small>{hint}</small></div>')


def card(c):
    d = snap["companies"].get(c["ticker"], {})
    chg = d.get("change_pct")
    pos = ""
    if c.get("shares") and d.get("price"):
        val = c["shares"] * d["price"]
        pl = (d["price"] / c["avg_cost"] - 1) * 100 if c.get("avg_cost") else None
        pos = f'<div class="pos">{c["shares"]:g} ações · {fmt(val, 0)} {d.get("currency", "")}' + (
            f' · P/L {fmt(pl, 1, "%")}' if pl is not None else "") + "</div>"
    news = "".join(
        f'<li><a href="{html.escape(n["url"])}" target="_blank" rel="noopener">{html.escape(n["title"])}</a>'
        f' <small>{html.escape(n.get("source", ""))} {html.escape(n.get("date", ""))}</small></li>'
        for n in d.get("news", []))
    yl, yh, p = d.get("year_low"), d.get("year_high"), d.get("price")
    rng = ""
    if yl and yh and p:
        pct = max(0, min(100, (p - yl) / (yh - yl) * 100))
        rng = (f'<div class="rng"><i style="left:{pct:.0f}%"></i></div>'
               f'<small>52 sem: {fmt(yl)} – {fmt(yh)}</small>')
    return f'''<article class="card" data-status="{c["status"]}">
<header><h3>{c["ticker"]}</h3><span>{html.escape(d.get("name", ""))}</span>
<em class="{ "up" if (chg or 0) >= 0 else "down"}">{fmt(p)} {d.get("currency", "")} ({fmt(chg, 2, "%")})</em></header>
{pos}{rng}
<div class="metrics">
{metric("P/E (últimos 12m)", d.get("pe_ttm"), pe_class, "&lt;15 barato · ~20 fair · ~40 caro · &gt;50 muito caro")}
{metric("P/E (próx. 12m)", d.get("pe_fwd"), pe_class, "mesma escala")}
{metric("PEG", d.get("peg"), peg_class, "&lt;1 desconto · 1-2 fair · &gt;2 premium")}
<div class="m"><span class="l">Dividend yield</span><b>{fmt(d.get("div_yield_pct"), 2, "%")}</b></div>
</div>
<ul class="news">{news or "<li><small>Sem notícias registadas hoje.</small></li>"}</ul>
{f'<p class="note">{html.escape(c["note"])}</p>' if c.get("note") else ""}
</article>'''


mnews = "".join(
    f'<li><a href="{html.escape(n["url"])}" target="_blank" rel="noopener">{html.escape(n["title"])}</a>'
    f' <small>{html.escape(n.get("source", ""))}</small></li>' for n in snap.get("market_news", []))
cards = "\n".join(card(c) for c in cfg["companies"])
out = f'''<!doctype html><html lang="pt"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Portefólio</title>
<style>
:root{{--bg:#f6f7f9;--card:#fff;--fg:#14181f;--mut:#667085;--bd:#e4e7ec;--good:#12805c;--fair:#b7791f;--warn:#c05621;--bad:#c53030;--na:#98a2b3}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0e1116;--card:#171b22;--fg:#e8eaed;--mut:#98a2b3;--bd:#2a303a;--good:#3ecf9a;--fair:#e5b84b;--warn:#f0944d;--bad:#f27070}}}}
*{{box-sizing:border-box}}body{{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif}}
main{{max-width:1100px;margin:auto}}h1{{margin:0 0 4px}}.sub{{color:var(--mut)}}
.bar{{display:flex;gap:8px;margin:14px 0;flex-wrap:wrap}}
button{{border:1px solid var(--bd);background:var(--card);color:var(--fg);padding:6px 14px;border-radius:99px;cursor:pointer}}
button.on{{background:var(--fg);color:var(--bg)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px}}
.card header{{display:flex;flex-wrap:wrap;gap:4px 8px;align-items:baseline}}.card h3{{margin:0}}
.card header span{{color:var(--mut);flex:1}}em{{font-style:normal;font-weight:600}}.up{{color:var(--good)}}.down{{color:var(--bad)}}
.metrics{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0}}
.m{{display:flex;flex-direction:column;gap:2px;border:1px solid var(--bd);border-radius:8px;padding:8px}}
.m .l{{color:var(--mut);font-size:12px}}.m b{{font-size:20px}}.m small{{color:var(--mut);font-size:10px}}
.tag{{font-size:12px;font-weight:600;width:max-content}}.good{{color:var(--good)}}.fair{{color:var(--fair)}}.warn{{color:var(--warn)}}.bad{{color:var(--bad)}}.na{{color:var(--na)}}
.rng{{height:4px;background:var(--bd);border-radius:2px;position:relative;margin:10px 0 2px}}.rng i{{position:absolute;top:-3px;width:10px;height:10px;border-radius:50%;background:var(--fg);margin-left:-5px}}
ul{{padding-left:18px;margin:8px 0}}small{{color:var(--mut)}}a{{color:inherit}}.note,.pos{{color:var(--mut);font-size:13px;margin:6px 0}}
section.news{{margin-top:22px}}
</style></head><body><main>
<h1>O meu portefólio</h1><div class="sub">Atualizado em {snap["updated"]}</div>
<div class="bar"><button class="on" data-f="all">Todas</button><button data-f="portfolio">Portefólio</button><button data-f="watchlist">A seguir</button></div>
<div class="grid">{cards}</div>
<section class="news card"><h3>Notícias de mercado</h3><ul>{mnews or "<li><small>Sem notícias.</small></li>"}</ul></section>
<p class="sub">Informação para apoio à decisão, não constitui aconselhamento financeiro.</p>
</main><script>
document.querySelectorAll('button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));
document.querySelectorAll('.card[data-status]').forEach(c=>c.hidden=b.dataset.f!=='all'&&c.dataset.status!==b.dataset.f)}});
</script></body></html>'''
(ROOT / "docs/dashboard.html").write_text(out)
print("docs/dashboard.html gerado")
