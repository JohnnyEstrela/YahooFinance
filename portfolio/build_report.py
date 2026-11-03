#!/usr/bin/env python3
"""Gera docs/index.html a partir de portfolio.json + snapshot.json (apenas stdlib)."""
import html, json, sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent


def ntm_eps(estimates, asof):
    """EPS dos próximos 12 meses: mistura ponderada dos dois anos fiscais que o cobrem."""
    fy = sorted((date.fromisoformat(d), e) for d, e in estimates)
    fut = [x for x in fy if x[0] > asof]
    if not fut:
        return None
    if len(fut) == 1:
        return fut[0][1]
    w = min(1.0, max(0.0, (fut[0][0] - asof).days / 365))
    return w * fut[0][1] + (1 - w) * fut[1][1]


def pe_label(v, t):
    if v is None or v <= 0:
        return ("n/d", "na")
    if v < t["cheap"]:
        return ("Barato", "good")
    if v <= t["fair"]:
        return ("Fair Value", "fair")
    if v <= t["pricey"]:
        return ("Pricey", "warn")
    if v <= t["expensive"]:
        return ("Caro", "bad")
    return ("Expensive", "worst")


def peg_label(v, t):
    if v is None or v <= 0:
        return ("n/d", "na")
    if v < t["discount"]:
        return ("Desconto", "good")
    if v <= t["fair"]:
        return ("Fair", "fair")
    return ("Premium", "bad")


def fmt(v, d=2, suf=""):
    return "–" if v is None else f"{v:,.{d}f}{suf}"


def cap(v):
    return "–" if not v else (f"{v/1e12:.2f} T" if v >= 1e12 else f"{v/1e9:.1f} B")


def badge(lbl):
    return f'<span class="b {lbl[1]}">{html.escape(lbl[0])}</span>'


def main():
    pf = json.loads((HERE / "portfolio.json").read_text())
    sn = json.loads((HERE / "snapshot.json").read_text())
    th = pf["thresholds"]
    asof = date.fromisoformat(sn["as_of"])
    rows = []
    for c in pf["companies"]:
        d = sn["tickers"].get(c["ticker"])
        if not d:
            rows.append({"c": c, "missing": True})
            continue
        eps = ntm_eps(d["eps_estimates"], asof) if d.get("eps_estimates") else None
        fpe = d["price"] / eps if eps else None
        pos = None
        if c.get("shares") and c.get("avg_cost"):
            pos = (d["price"] / c["avg_cost"] - 1) * 100
        rows.append({"c": c, "d": d, "fpe": fpe, "pos": pos,
                     "l1": pe_label(d.get("pe_ttm"), th["pe"]),
                     "l2": pe_label(fpe, th["pe"]),
                     "l3": peg_label(d.get("peg"), th["peg"])})

    def card(r):
        c = r["c"]
        if r.get("missing"):
            return (f'<article class="card" data-s="{c["status"]}"><h3>{html.escape(c["ticker"])}</h3>'
                    '<p class="mut">Sem dados no snapshot - corre a rotina.</p></article>')
        d = r["d"]
        rng = (d["price"] - d["year_low"]) / (d["year_high"] - d["year_low"]) * 100
        chg = d["change_pct"]
        pos = ""
        if r["pos"] is not None:
            pos = f'<div class="kv"><span>Posição</span><b class="{"up" if r["pos"]>=0 else "dn"}">{r["pos"]:+.1f}% vs custo</b></div>'
        news = "".join(f'<li><a href="{html.escape(n["url"])}" target="_blank" rel="noopener">{html.escape(n["title"])}</a> <small>{html.escape(n.get("source",""))}</small></li>' for n in d.get("news", []))
        return f'''<article class="card" data-s="{c["status"]}">
<header><div><h3>{html.escape(c["ticker"])}</h3><small class="mut">{html.escape(d["name"])}</small></div>
<div class="px"><b>${d["price"]:,.2f}</b><span class="{"up" if chg>=0 else "dn"}">{chg:+.2f}%</span></div></header>
<div class="tag">{"Portefólio" if c["status"]=="portfolio" else "A seguir"}</div>
<div class="metrics">
<div class="m"><span>P/E (últimos 12m)</span><b>{fmt(d.get("pe_ttm"),1)}</b>{badge(r["l1"])}</div>
<div class="m"><span>P/E (próximos 12m)</span><b>{fmt(r["fpe"],1)}</b>{badge(r["l2"])}</div>
<div class="m"><span>PEG</span><b>{fmt(d.get("peg"),2)}</b>{badge(r["l3"])}</div></div>
<div class="kv"><span>Market cap</span><b>${cap(d["market_cap"])}</b></div>
<div class="kv"><span>Dividend yield</span><b>{fmt((d.get("div_yield") or 0)*100,2,"%")}</b></div>
{pos}
<div class="rng" title="Posição no intervalo de 52 semanas"><i style="left:{rng:.0f}%"></i></div>
<div class="rl"><small>${d["year_low"]:,.0f}</small><small>52 sem.</small><small>${d["year_high"]:,.0f}</small></div>
<ul class="news">{news}</ul></article>'''

    mnews = "".join(f'<li><a href="{html.escape(n["url"])}" target="_blank" rel="noopener">{html.escape(n["title"])}</a> <small>{html.escape(n.get("source",""))} · {n.get("date","")}</small></li>' for n in sn.get("market_news", []))
    cards = "\n".join(card(r) for r in rows)
    legend = (f'P/E: &lt;{th["pe"]["cheap"]} barato · ≤{th["pe"]["fair"]} fair value · ≤{th["pe"]["pricey"]} pricey · '
              f'≤{th["pe"]["expensive"]} caro · &gt;{th["pe"]["expensive"]} expensive &nbsp;|&nbsp; '
              f'PEG: &lt;{th["peg"]["discount"]} desconto · {th["peg"]["discount"]}–{th["peg"]["fair"]} fair · &gt;{th["peg"]["fair"]} premium')
    out = TEMPLATE.replace("{{CARDS}}", cards).replace("{{MNEWS}}", mnews).replace("{{LEGEND}}", legend).replace("{{ASOF}}", sn["as_of"])
    (HERE / "docs" / "index.html").write_text(out)
    print("OK ->", HERE / "docs" / "index.html")


TEMPLATE = """<!doctype html><html lang="pt"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Meu Portefólio</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--tx:#14181f;--mut:#667085;--bd:#e4e7ec;--good:#12b76a;--fair:#2e90fa;--warn:#f79009;--bad:#f04438;--worst:#b42318;--na:#98a2b3}
@media(prefers-color-scheme:dark){:root{--bg:#0e1116;--card:#171b22;--tx:#e7eaf0;--mut:#8b94a5;--bd:#262c36}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.45 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:20px 16px 40px}
h1{margin:0;font-size:1.5rem}.top{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;align-items:center;margin-bottom:12px}
.mut,small{color:var(--mut)}.tabs{display:flex;gap:6px}.tabs button{border:1px solid var(--bd);background:var(--card);color:var(--tx);padding:6px 12px;border-radius:99px;cursor:pointer}
.tabs button.on{background:var(--tx);color:var(--bg)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:16px}
.card header{display:flex;justify-content:space-between;gap:8px}.card h3{margin:0;font-size:1.2rem}
.px{text-align:right;display:flex;flex-direction:column}.up{color:var(--good)}.dn{color:var(--bad)}
.tag{display:inline-block;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);margin:6px 0}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:6px 0 10px}
.m{border:1px solid var(--bd);border-radius:10px;padding:8px;display:flex;flex-direction:column;gap:4px}
.m span{font-size:.68rem;color:var(--mut)}.m b{font-size:1.15rem}
.b{font-size:.68rem;font-weight:600;color:#fff;border-radius:6px;padding:2px 6px;align-self:flex-start}
.b.good{background:var(--good)}.b.fair{background:var(--fair)}.b.warn{background:var(--warn)}.b.bad{background:var(--bad)}.b.worst{background:var(--worst)}.b.na{background:var(--na)}
.kv{display:flex;justify-content:space-between;padding:3px 0;font-size:.9rem}.kv span{color:var(--mut)}
.rng{height:6px;background:var(--bd);border-radius:9px;position:relative;margin:10px 0 2px}.rng i{position:absolute;top:-3px;width:12px;height:12px;border-radius:50%;background:var(--fair);transform:translateX(-50%)}
.rl{display:flex;justify-content:space-between}
ul{padding-left:18px;margin:8px 0 0}li{margin:4px 0}a{color:var(--fair)}
section.mk{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:4px 16px 12px;margin-bottom:16px}
.legend{font-size:.78rem;color:var(--mut);margin-top:18px}
@media(max-width:560px){.metrics{grid-template-columns:1fr}}
</style></head><body><main>
<div class="top"><div><h1>Meu Portefólio</h1><small>Dados de {{ASOF}} · não é aconselhamento financeiro</small></div>
<div class="tabs"><button class="on" data-f="all">Todas</button><button data-f="portfolio">Portefólio</button><button data-f="watchlist">A seguir</button></div></div>
<section class="mk"><h3>Notícias do mercado</h3><ul>{{MNEWS}}</ul></section>
<div class="grid">{{CARDS}}</div>
<p class="legend">{{LEGEND}}</p>
</main><script>
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x===b));
document.querySelectorAll('.card').forEach(c=>c.style.display=(b.dataset.f==='all'||c.dataset.s===b.dataset.f)?'':'none')});
</script></body></html>"""

if __name__ == "__main__":
    sys.exit(main())
