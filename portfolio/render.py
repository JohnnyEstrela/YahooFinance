"""Gera index.html (dashboard responsivo) a partir de portfolio.json + data/snapshot.json."""
import html
import json
from pathlib import Path

HERE = Path(__file__).parent


def classify_pe(v, th):
    if v is None:
        return "na", "n/d"
    if v < th["cheap"]:
        return "good", "Barato"
    if v <= (th["fair"] + th["pricey"]) / 2:
        return "fair", "Justo"
    if v <= th["expensive"]:
        return "warn", "Caro"
    return "bad", "Muito caro"


def classify_peg(v, th):
    if v is None:
        return "na", "n/d"
    if v < th["discount"]:
        return "good", "Desconto"
    if v <= th["premium"]:
        return "fair", "Justo"
    return "bad", "Prémio"


def fmt(v, suffix="", nd=2):
    return "—" if v is None else f"{v:,.{nd}f}{suffix}"


def metric(label, value, cls, text):
    return (f'<div class="m"><span class="l">{label}</span><b>{fmt(value, nd=1)}</b>'
            f'<span class="tag {cls}">{text}</span></div>')


def card(kind, entry, s, th):
    if not s:
        return (f'<article class="card" data-kind="{kind}"><h3>{html.escape(entry["ticker"])}</h3>'
                '<p class="muted">Sem dados (ticker inválido ou fonte indisponível).</p></article>')
    pe = classify_pe(s["pe"], th["pe"])
    fpe = classify_pe(s["forward_pe"], th["pe"])
    peg = classify_peg(s["peg"], th["peg"])
    chg = s.get("change_pct")
    chg_html = "" if chg is None else f'<span class="{"up" if chg >= 0 else "down"}">{chg:+.2f}%</span>'
    pos = ""
    if entry.get("shares") and s["price"]:
        val = entry["shares"] * s["price"]
        pos = f'<p class="muted">Posição: {fmt(val)} {s.get("currency") or ""}'
        if entry.get("avg_cost"):
            pos += f' · P/L {(s["price"] / entry["avg_cost"] - 1) * 100:+.1f}%'
        pos += "</p>"
    news = "".join(
        f'<li><a href="{html.escape(n["url"] or "#")}" target="_blank" rel="noopener">'
        f'{html.escape(n["title"])}</a><small> {html.escape(str(n.get("publisher") or ""))}</small></li>'
        for n in s["news"])
    return f'''<article class="card" data-kind="{kind}">
<header><div><h3>{html.escape(s["ticker"])}</h3><span class="muted">{html.escape(s["name"])}</span></div>
<div class="px"><b>{fmt(s["price"])}</b> {chg_html}</div></header>
{pos}
<div class="metrics">{metric("P/E (12m)", s["pe"], *pe)}{metric("P/E (próx. 12m)", s["forward_pe"], *fpe)}{metric("PEG", s["peg"], *peg)}</div>
<ul class="news">{news or '<li class="muted">Sem notícias.</li>'}</ul></article>'''


CSS = """
:root{--bg:#f6f7f9;--fg:#171a21;--card:#fff;--mut:#6b7280;--bd:#e5e7eb;--good:#0f9d58;--fair:#2563eb;--warn:#d97706;--bad:#dc2626}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0e1116;--fg:#e6e8ec;--card:#171b22;--mut:#9aa3b2;--bd:#262c36}}
:root[data-theme=dark]{--bg:#0e1116;--fg:#e6e8ec;--card:#171b22;--mut:#9aa3b2;--bd:#262c36}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
main{max-width:1200px;margin:0 auto;padding:16px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between}
.bar button{border:1px solid var(--bd);background:var(--card);color:var(--fg);padding:6px 14px;border-radius:99px;cursor:pointer}
.bar button.on{background:var(--fg);color:var(--bg)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin-top:14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px}
.card header{display:flex;justify-content:space-between;gap:8px}h3{margin:0}.px{text-align:right;font-size:18px}
.muted,small{color:var(--mut)}.up{color:var(--good)}.down{color:var(--bad)}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0}
.m{display:flex;flex-direction:column;border:1px solid var(--bd);border-radius:8px;padding:6px}.m .l{font-size:11px;color:var(--mut)}.m b{font-size:18px}
.tag{font-size:11px;font-weight:600}.good{color:var(--good)}.fair{color:var(--fair)}.warn{color:var(--warn)}.bad{color:var(--bad)}.na{color:var(--mut)}
.news{padding-left:18px;margin:0;font-size:13px}.news a{color:inherit}
.legend{font-size:12px;color:var(--mut);margin-top:14px}
"""


def main():
    cfg = json.loads((HERE / "portfolio.json").read_text())
    snap_path = HERE / "data" / "snapshot.json"
    snap = json.loads(snap_path.read_text()) if snap_path.exists() else {"stocks": {}, "generated_at": "n/d"}
    th = cfg["thresholds"]
    cards = [card(k, e, snap["stocks"].get(e["ticker"]), th)
             for k in ("portfolio", "watchlist") for e in cfg.get(k, [])]
    p, w = th["pe"], th["peg"]
    legend = (f'P/E: &lt;{p["cheap"]} Barato · ~{p["fair"]} Justo · ~{p["pricey"]} Caro · &gt;{p["expensive"]} Muito caro. '
              f'PEG: &lt;{w["discount"]} Desconto · {w["discount"]}–{w["premium"]} Justo · &gt;{w["premium"]} Prémio.')
    page = f'''<!doctype html><html lang="pt"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Consultor Financeiro</title>
<style>{CSS}</style></head><body><main>
<div class="bar"><h1>Consultor Financeiro</h1><div>
<button class="on" data-f="all">Tudo</button><button data-f="portfolio">Portefólio</button><button data-f="watchlist">Watchlist</button></div></div>
<p class="muted">Atualizado: {html.escape(str(snap.get("generated_at")))}</p>
<section class="grid">{"".join(cards)}</section>
<p class="legend">{legend} Informativo, não é aconselhamento financeiro.</p>
<script>document.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{{document.querySelectorAll('[data-f]').forEach(x=>x.classList.toggle('on',x===b));
document.querySelectorAll('.card').forEach(c=>c.hidden=b.dataset.f!=='all'&&c.dataset.kind!==b.dataset.f)}})</script>
</main></body></html>'''
    (HERE / "index.html").write_text(page)


if __name__ == "__main__":
    main()
