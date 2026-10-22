"""Gera o dashboard HTML (ficheiro único, responsivo, claro/escuro)."""
import json
from html import escape

TEMPLATE = r"""<!doctype html>
<html lang="pt"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portefólio</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--fg:#1a1d23;--mut:#6b7280;--bd:#e3e6eb;--good:#0f9d58;--ok:#2b6cb0;--warn:#d97706;--bad:#d93025;--na:#8a909b}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0f1115;--card:#181b21;--fg:#e8eaed;--mut:#9aa0aa;--bd:#2a2e36}}
:root[data-theme=dark]{--bg:#0f1115;--card:#181b21;--fg:#e8eaed;--mut:#9aa0aa;--bd:#2a2e36}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;padding:16px}
header{display:flex;min-width:0;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:12px}
h1{font-size:20px;margin:0 auto 0 0}.mut{color:var(--mut);font-size:13px}
button,input,select{font:inherit;color:var(--fg);background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:6px 10px}
button.on{background:var(--ok);color:#fff;border-color:var(--ok)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(300px,100%),1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px}
.top{display:flex;justify-content:space-between;gap:8px}.tk{font-weight:700;font-size:17px}
.px{text-align:right;font-weight:600}.up{color:var(--good)}.dn{color:var(--bad)}
.m{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:8px;margin:12px 0}
.m div{min-width:0;border:1px solid var(--bd);border-radius:8px;padding:6px 8px}.m small{display:block;color:var(--mut);font-size:11px}
.m b{font-size:16px}.tag{font-size:11px;font-weight:600;border-radius:99px;padding:1px 8px;color:#fff}
.good{background:var(--good)}.ok{background:var(--ok)}.warn{background:var(--warn)}.bad{background:var(--bad)}.na{background:var(--na)}
ul{padding-left:18px;margin:8px 0 0}li{margin:4px 0}a{color:var(--ok)}
.err{color:var(--bad);font-size:13px}.pill{font-size:11px;border:1px solid var(--bd);border-radius:6px;padding:0 6px;color:var(--mut)}
</style></head><body>
<header><h1>📈 Portefólio &amp; Watchlist</h1><span class="mut" id="upd"></span>
<input id="q" placeholder="Pesquisar…" size="10">
<span id="tipos"></span>
<select id="ord"><option value="ticker">Ordenar: nome</option><option value="pe_forward">P/E forward</option><option value="peg">PEG</option><option value="pe_trailing">P/E 12m</option></select>
<button id="th">🌓</button></header>
<p class="mut" id="leg"></p>
<div class="grid" id="g"></div>
<script>
const D=__DATA__;let tipo="todos";
const $=s=>document.querySelector(s),f=(v,d=2)=>v==null?"—":Number(v).toFixed(d);
$("#upd").textContent="Atualizado "+D.atualizado.replace("T"," ").slice(0,16)+" UTC";
const L=D.limites;$("#leg").textContent=`P/E: <${L.pe.barato} barato · <${L.pe.justo} justo · ≤${L.pe.caro} caro · >${L.pe.caro} muito caro  |  PEG: <${L.peg.desconto} desconto · ≤${L.peg.justo} justo · >${L.peg.justo} prémio`;
$("#tipos").innerHTML=["todos","portfolio","seguir"].map(t=>`<button data-t="${t}">${t}</button>`).join(" ");
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function m(l,v,c){return `<div><small>${l}</small><b>${v}</b> <span class="tag ${c.nivel}">${c.etiqueta}</span></div>`}
function draw(){
 document.querySelectorAll("#tipos button").forEach(b=>b.classList.toggle("on",b.dataset.t===tipo));
 const q=$("#q").value.toLowerCase(),o=$("#ord").value;
 let r=D.empresas.filter(e=>(tipo==="todos"||e.tipo===tipo)&&(e.ticker+(e.nome||"")).toLowerCase().includes(q));
 r.sort((a,b)=>o==="ticker"?a.ticker.localeCompare(b.ticker):(a[o]??1e9)-(b[o]??1e9));
 $("#g").innerHTML=r.map(e=>{
  const ch=e.variacao_dia_pct,n=(e.noticias||[]).map(x=>`<li>${x.url?`<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.titulo)}</a>`:esc(x.titulo)} <span class="mut">${esc(x.fonte||"")}</span></li>`).join("");
  return `<div class="card"><div class="top"><div><span class="tk">${esc(e.ticker)}</span> <span class="pill">${esc(e.tipo)}</span><div class="mut">${esc(e.nome||"")}${e.setor?" · "+esc(e.setor):""}</div></div>
  <div class="px">${f(e.preco)} ${esc(e.moeda||"")}<div class="${ch>=0?"up":"dn"}">${ch==null?"":(ch>=0?"+":"")+f(ch)+"%"}</div></div></div>
  <div class="m">${m("P/E 12m",f(e.pe_trailing,1),e.pe_ttm)}${m("P/E próx. 12m",f(e.pe_forward,1),e.pe_fwd)}${m("PEG",f(e.peg),e.peg_cls)}</div>
  ${e.peg_origem==="calculado"?'<div class="mut">PEG calculado (P/E ÷ crescimento)</div>':""}
  ${e.pl_pct!=null?`<div class="mut">Posição: ${f(e.valor_posicao)} · P/L ${f(e.pl_pct)}%</div>`:""}
  ${e.nota?`<div class="mut">📝 ${esc(e.nota)}</div>`:""}
  ${e.erro?`<div class="err">⚠ ${esc(e.erro)}</div>`:""}
  ${n?`<ul>${n}</ul>`:""}</div>`}).join("")||'<p class="mut">Sem resultados.</p>'}
document.addEventListener("click",ev=>{if(ev.target.dataset.t){tipo=ev.target.dataset.t;draw()}});
$("#q").oninput=draw;$("#ord").onchange=draw;
$("#th").onclick=()=>{const r=document.documentElement;r.dataset.theme=(r.dataset.theme||(matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light"))==="dark"?"light":"dark"};
draw();
</script></body></html>"""


def render_html(data):
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.replace("__DATA__", payload)
