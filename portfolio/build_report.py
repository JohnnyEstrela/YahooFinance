"""Gera report/index.html (responsivo) a partir de watchlist.json + data/snapshot.json."""
import json
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from valuation import DEFAULT_THRESHOLDS, classify_pe, classify_peg  # noqa: E402

HERE = Path(__file__).parent

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--fg:#1c2330;--mut:#667085;--line:#e4e7ec;--acc:#2563eb;
--good:#12805c;--goodbg:#dcf5ea;--ok:#2563eb;--okbg:#e3ecff;--warn:#a15c07;--warnbg:#fdecc8;
--bad:#b42318;--badbg:#fde4e1;--na:#667085;--nabg:#eef0f3}
@media(prefers-color-scheme:dark){:root{--bg:#0f141b;--card:#171e28;--fg:#e8ecf2;--mut:#95a1b3;
--line:#2a3442;--acc:#6ea0ff;--good:#4cd6a0;--goodbg:#12362a;--ok:#8ab4ff;--okbg:#1b2c52;
--warn:#f5c26b;--warnbg:#3d2f10;--bad:#ff8f84;--badbg:#431b17;--na:#95a1b3;--nabg:#222b37}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1200px;margin:0 auto;padding:16px}
h1{font-size:1.4rem;margin:0}.sub{color:var(--mut);font-size:.85rem}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.bar button,.bar input{font:inherit;border:1px solid var(--line);background:var(--card);
color:var(--fg);border-radius:999px;padding:6px 14px}
.bar button.on{background:var(--acc);color:#fff;border-color:var(--acc)}
.bar input{flex:1;min-width:140px;border-radius:8px}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.head{display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.tk{font-weight:700;font-size:1.1rem}.nm{color:var(--mut);font-size:.85rem}
.tag{font-size:.7rem;border:1px solid var(--line);border-radius:6px;padding:1px 6px;color:var(--mut)}
.price{font-size:1.25rem;font-weight:600}.up{color:var(--good)}.dn{color:var(--bad)}
.met{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}
.m{background:var(--nabg);border-radius:8px;padding:8px;text-align:center}
.m small{display:block;color:var(--mut);font-size:.68rem}.m b{font-size:1.05rem}
.b{display:inline-block;margin-top:4px;font-size:.72rem;font-weight:600;border-radius:999px;padding:1px 8px}
.good{color:var(--good);background:var(--goodbg)}.ok{color:var(--ok);background:var(--okbg)}
.warn{color:var(--warn);background:var(--warnbg)}.bad{color:var(--bad);background:var(--badbg)}
.na{color:var(--na);background:var(--nabg)}
ul{margin:6px 0 0;padding-left:18px}li{margin:3px 0;font-size:.85rem}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.notes{font-size:.82rem;color:var(--mut);font-style:italic;margin-top:8px}
h2{font-size:1.05rem;margin:24px 0 8px}.legend{font-size:.78rem;color:var(--mut)}
.hide{display:none}
@media(max-width:480px){.met{grid-template-columns:1fr 1fr 1fr;gap:4px}.m b{font-size:.95rem}}
"""

JS = """
let f='all';const q=document.getElementById('q');
function ap(){const s=q.value.toLowerCase();document.querySelectorAll('.card').forEach(c=>{
const ok=(f==='all'||c.dataset.status===f)&&c.dataset.search.includes(s);
c.classList.toggle('hide',!ok)})}
document.querySelectorAll('.bar button').forEach(b=>b.onclick=()=>{f=b.dataset.f;
document.querySelectorAll('.bar button').forEach(x=>x.classList.toggle('on',x===b));ap()});
q.oninput=ap;
"""


def fmt(v, nd=1):
    return "n/d" if v is None else f"{v:,.{nd}f}"


def metric(label, value, cls):
    text, kind = cls
    return (
        f'<div class="m"><small>{label}</small><b>{fmt(value)}</b>'
        f'<br><span class="b {kind}">{text}</span></div>'
    )


def news_list(items):
    if not items:
        return "<ul><li class='sub'>Sem notícias.</li></ul>"
    rows = []
    for n in items:
        t = escape(n["title"])
        link = f'<a href="{escape(n["url"])}" target="_blank" rel="noopener">{t}</a>' if n.get("url") else t
        pub = f' <span class="sub">— {escape(n["publisher"])}</span>' if n.get("publisher") else ""
        rows.append(f"<li>{link}{pub}</li>")
    return "<ul>" + "".join(rows) + "</ul>"


def card(cfg, d, th):
    tk = cfg["ticker"]
    if d is None:
        body = '<p class="sub">Sem dados neste snapshot.</p>'
        name = tk
    else:
        name = d["name"]
        ch = d.get("change_pct")
        chtxt = ""
        if ch is not None:
            chtxt = f' <span class="{"up" if ch >= 0 else "dn"}" style="font-size:.85rem">{ch:+.2f}%</span>'
        extra = ""
        if cfg.get("shares") and cfg.get("avg_cost") and d.get("price"):
            pl = (d["price"] / cfg["avg_cost"] - 1) * 100
            extra = f'<div class="sub">Posição: {cfg["shares"]} un. · custo médio {cfg["avg_cost"]:.2f} · <b class="{"up" if pl >= 0 else "dn"}">{pl:+.1f}%</b></div>'
        body = (
            f'<div class="price">{fmt(d.get("price"), 2)} {escape(d.get("currency", ""))}{chtxt}</div>{extra}'
            '<div class="met">'
            + metric("P/E (12m passados)", d.get("trailing_pe"), classify_pe(d.get("trailing_pe"), th))
            + metric("P/E (próx. 12m)", d.get("forward_pe"), classify_pe(d.get("forward_pe"), th))
            + metric("PEG", d.get("peg"), classify_peg(d.get("peg"), th))
            + "</div>"
            + news_list(d.get("news", []))
        )
    status = cfg.get("status", "watching")
    tag = "Portefólio" if status == "portfolio" else "A seguir"
    notes = f'<div class="notes">{escape(cfg["notes"])}</div>' if cfg.get("notes") else ""
    search = f"{tk} {name} {cfg.get('notes', '')}".lower()
    return (
        f'<div class="card" data-status="{escape(status)}" data-search="{escape(search)}">'
        f'<div class="head"><div><span class="tk">{escape(tk)}</span> '
        f'<span class="tag">{tag}</span><div class="nm">{escape(name)}</div></div></div>'
        f"{body}{notes}</div>"
    )


def build(watch, snap):
    th = {**DEFAULT_THRESHOLDS, **watch.get("thresholds", {})}
    by = {c["ticker"]: c for c in snap.get("companies", [])}
    cards = "".join(card(c, by.get(c["ticker"]), th) for c in watch["companies"])
    p, g = th["pe"], th["peg"]
    legend = (
        f'P/E: &lt;{p["cheap"]} Barato · &lt;{p["fair"]} Justo · &lt;{p["pricey"]} Caro · '
        f'≥{p["pricey"]} Muito caro &nbsp;|&nbsp; PEG: &lt;{g["discount"]} Desconto · '
        f'{g["discount"]}–{g["fair"]} Justo · &gt;{g["fair"]} Prémio'
    )
    errs = snap.get("errors") or {}
    err = (
        f'<p class="sub">Falhas: {escape(", ".join(errs))}</p>' if errs else ""
    )
    return f"""<!doctype html><html lang="pt"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portefólio</title><style>{CSS}</style></head><body><div class="wrap">
<h1>Portefólio &amp; Watchlist</h1>
<div class="sub">Atualizado: {escape(snap.get("generated_at", "n/d"))} · Informação, não aconselhamento financeiro</div>
<div class="legend">{legend}</div>{err}
<div class="bar"><button class="on" data-f="all">Todas</button>
<button data-f="portfolio">Portefólio</button><button data-f="watching">A seguir</button>
<input id="q" placeholder="Pesquisar…"></div>
<div class="grid">{cards}</div>
<h2>Notícias de mercado</h2><div class="card">{news_list(snap.get("market_news", []))}</div>
</div><script>{JS}</script></body></html>"""


def main():
    watch = json.loads((HERE / "watchlist.json").read_text(encoding="utf-8"))
    snap = json.loads((HERE / "data" / "snapshot.json").read_text(encoding="utf-8"))
    out = HERE / "report" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(build(watch, snap), encoding="utf-8")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
