#!/usr/bin/env python3
"""Gera portfolio/index.html a partir de watchlist.json + data/snapshot.json."""
import json, html, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
wl = json.loads((HERE / "watchlist.json").read_text())["companies"]
snap = json.loads((HERE / "data/snapshot.json").read_text())
today = dt.date.fromisoformat(snap["as_of"])


def pe_band(v):
    if v is None or v <= 0: return ("n/d", "na")
    if v < 15: return ("Barato", "good")
    if v <= 20: return ("Valor justo", "fair")
    if v <= 40: return ("Elevado", "warn")
    if v <= 50: return ("Elevado+", "warn")
    return ("Muito caro", "bad")


def peg_band(v):
    if v is None or v <= 0: return ("n/d", "na")
    if v < 1: return ("Desconto", "good")
    if v <= 2: return ("Justo", "fair")
    return ("Prémio", "bad")


def ntm_eps(estimates):
    """EPS dos próximos 12 meses: média ponderada dos anos fiscais pelo tempo sobreposto."""
    end = today + dt.timedelta(days=365)
    total = 0.0
    for d, eps in estimates:
        fy_end = dt.date.fromisoformat(d)
        fy_start = fy_end - dt.timedelta(days=365)
        overlap = (min(end, fy_end) - max(today, fy_start)).days
        if overlap > 0:
            total += eps * overlap / 365
    return total or None


def fmt(v, d=2): return "n/d" if v is None else f"{v:,.{d}f}"
def cap(v): return f"{v/1e12:.2f} T" if v >= 1e12 else f"{v/1e9:.0f} B"
e = html.escape


def card(w):
    t = w["ticker"]; c = snap["companies"].get(t)
    if not c:
        return f'<article class="card" data-status="{e(w["status"])}"><h2>{e(t)}</h2><p class="muted">Sem dados ainda - será preenchido na próxima execução.</p></article>'
    eps = ntm_eps(c["eps_estimates"])
    fpe = c["price"] / eps if eps else None
    pe, peg = c["pe_ttm"], c["peg"]
    rng = (c["price"] - c["year_low"]) / (c["year_high"] - c["year_low"]) * 100
    metrics = "".join(
        f'<div class="m {b[1]}"><span class="l">{l}</span><span class="v">{fmt(v)}</span><span class="b">{b[0]}</span></div>'
        for l, v, b in [("P/E (12m passados)", pe, pe_band(pe)), ("P/E (próx. 12m)", fpe, pe_band(fpe)), ("PEG", peg, peg_band(peg))])
    pos = ""
    if w.get("shares") and w.get("avg_cost"):
        pl = (c["price"] / w["avg_cost"] - 1) * 100
        pos = f'<p class="pos">{w["shares"]} ações · custo médio {w["avg_cost"]} · <b class="{"up" if pl>=0 else "dn"}">{pl:+.1f}%</b></p>'
    news = "".join(f'<li><a href="{e(n["url"])}" target="_blank" rel="noopener">{e(n["title"])}</a> <span class="muted">{e(n["date"])}</span></li>' for n in c["news"])
    label = "Carteira" if w["status"] == "portfolio" else "A seguir"
    return f'''<article class="card" data-status="{e(w["status"])}">
<header><div><h2>{e(t)}</h2><span class="muted">{e(c["name"])}</span></div><span class="tag">{label}</span></header>
<div class="price">{c["price"]:,.2f} <small class="{"up" if c["change_pct"]>=0 else "dn"}">{c["change_pct"]:+.2f}%</small></div>
{pos}
<div class="metrics">{metrics}</div>
<div class="range" title="Posição no intervalo de 52 semanas"><i style="left:{rng:.0f}%"></i></div>
<div class="muted rl"><span>{c["year_low"]:,.0f}</span><span>52 sem.</span><span>{c["year_high"]:,.0f}</span></div>
<p class="muted">Cap. {cap(c["market_cap"])} · Dividendo {c["dividend_yield"]*100:.2f}%</p>
<ul class="news">{news}</ul></article>'''


cards = "\n".join(card(w) for w in wl)
mnews = "".join(f'<li><a href="{e(n["url"])}" target="_blank" rel="noopener">{e(n["title"])}</a> <span class="muted">{e(n["date"])}</span></li>' for n in snap["market_news"])
page = f'''<!doctype html><html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Consultor Financeiro</title><style>
:root{{--bg:#f6f7f9;--card:#fff;--tx:#1b1f24;--mu:#6b7280;--bd:#e5e7eb;--good:#15803d;--fair:#0369a1;--warn:#b45309;--bad:#b91c1c;--na:#6b7280}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#0f1318;--card:#171c23;--tx:#e6e9ee;--mu:#9aa3af;--bd:#2a313b;--good:#4ade80;--fair:#38bdf8;--warn:#fbbf24;--bad:#f87171;--na:#9aa3af}}}}
:root[data-theme=dark]{{--bg:#0f1318;--card:#171c23;--tx:#e6e9ee;--mu:#9aa3af;--bd:#2a313b;--good:#4ade80;--fair:#38bdf8;--warn:#fbbf24;--bad:#f87171;--na:#9aa3af}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--tx);font:15px/1.45 system-ui,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:20px 16px}}h1{{margin:0 0 4px;font-size:1.5rem}}
.muted{{color:var(--mu);font-size:.85em}}.bar{{display:flex;gap:8px;margin:14px 0;flex-wrap:wrap}}
button{{background:var(--card);color:var(--tx);border:1px solid var(--bd);border-radius:999px;padding:6px 14px;cursor:pointer}}button.on{{border-color:var(--fair);color:var(--fair)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px}}.card header{{display:flex;justify-content:space-between;align-items:start}}
h2{{margin:0;font-size:1.2rem}}.tag{{font-size:.75em;border:1px solid var(--bd);border-radius:999px;padding:2px 10px;color:var(--mu)}}
.price{{font-size:1.7rem;font-weight:600;margin:8px 0}}.price small{{font-size:.5em}}.up{{color:var(--good)}}.dn{{color:var(--bad)}}
.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0}}.m{{border:1px solid var(--bd);border-radius:8px;padding:8px;display:flex;flex-direction:column}}
.m .l{{font-size:.7em;color:var(--mu)}}.m .v{{font-size:1.15rem;font-weight:600}}.m .b{{font-size:.75em;font-weight:600}}
.m.good .b{{color:var(--good)}}.m.fair .b{{color:var(--fair)}}.m.warn .b{{color:var(--warn)}}.m.bad .b{{color:var(--bad)}}.m.na .b{{color:var(--na)}}
.range{{position:relative;height:6px;background:var(--bd);border-radius:3px;margin-top:12px}}.range i{{position:absolute;top:-3px;width:12px;height:12px;border-radius:50%;background:var(--fair);margin-left:-6px}}
.rl{{display:flex;justify-content:space-between;margin-top:4px}}.news{{padding-left:18px;margin:8px 0 0}}.news li{{margin:6px 0}}a{{color:var(--fair)}}
section.mk{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:12px 16px;margin-bottom:14px}}.legend{{margin-top:18px}}
</style></head><body><main>
<h1>⚡ Consultor Financeiro</h1><div class="muted">Dados de {e(snap["as_of"])} · {e(snap["source"])}</div>
<div class="bar"><button class="on" data-f="all">Todas</button><button data-f="portfolio">Carteira</button><button data-f="watching">A seguir</button><button id="th">Tema</button></div>
<section class="mk"><b>Mercado</b><ul class="news">{mnews}</ul></section>
<div class="grid">{cards}</div>
<p class="muted legend"><b>Legenda.</b> P/E: &lt;15 barato · ≤20 valor justo · ≤40 elevado · 40–50 elevado+ · &gt;50 muito caro. PEG: &lt;1 desconto · 1–2 justo · &gt;2 prémio. P/E próx. 12m = preço ÷ EPS estimado dos próximos 12 meses (média ponderada dos anos fiscais de consenso). Informação de apoio, não aconselhamento financeiro.</p>
</main><script>
document.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{{document.querySelectorAll('[data-f]').forEach(x=>x.classList.toggle('on',x===b));
document.querySelectorAll('.card').forEach(c=>c.style.display=(b.dataset.f==='all'||c.dataset.status===b.dataset.f)?'':'none')}});
document.getElementById('th').onclick=()=>{{const r=document.documentElement;r.dataset.theme=(r.dataset.theme==='dark'||(!r.dataset.theme&&matchMedia('(prefers-color-scheme:dark)').matches))?'light':'dark'}};
</script></body></html>'''
(HERE / "index.html").write_text(page)
print("ok", len(wl), "empresas")
for w in wl:
    c = snap["companies"].get(w["ticker"])
    if c: print(w["ticker"], round(c["pe_ttm"],1), round(c["price"]/ntm_eps(c["eps_estimates"]),1), c["peg"])
