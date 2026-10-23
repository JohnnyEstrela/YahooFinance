#!/usr/bin/env python3
"""Consultor financeiro diário: lê carteira.json, vai buscar dados ao Yahoo Finance
(P/E trailing, P/E forward, PEG, notícias) e gera relatorio.html (autónomo, responsivo)."""
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

AQUI = Path(__file__).parent


def classificar_pe(v, t):
    if v is None or v <= 0:
        return ("n/d", "nd")
    if v < t["barato"]:
        return ("Barato", "ok")
    if v <= t["justo"]:
        return ("Justo", "fair")
    if v <= t["muito_caro"]:
        return ("Caro", "warn")
    return ("Muito caro", "bad")


def classificar_peg(v, t):
    if v is None or v <= 0:
        return ("n/d", "nd")
    if v < t["desconto"]:
        return ("Desconto", "ok")
    if v <= t["justo"]:
        return ("Justo", "fair")
    return ("Premium", "bad")


def noticias(ticker, n):
    try:
        res = yf.Search(ticker, news_count=n * 3).news
    except Exception:
        return []
    out = [x for x in res if ticker.upper() in [r.upper() for r in x.get("relatedTickers", [])]]
    return (out or res)[:n]


def recolher(e, cfg):
    t = e["ticker"].upper().replace(".", "-") if e["ticker"].count(".") == 1 and len(e["ticker"].split(".")[1]) == 1 else e["ticker"].upper()
    d = {"ticker": t, "tipo": e.get("tipo", "seguir"), "notas": e.get("notas", ""), "erro": None}
    try:
        i = yf.Ticker(t).info
    except Exception as ex:
        d["erro"] = str(ex)[:120]
        return d
    pe, fpe = i.get("trailingPE"), i.get("forwardPE")
    peg = i.get("trailingPegRatio") or i.get("pegRatio")
    if peg is None and fpe and i.get("earningsGrowth"):
        peg = fpe / (i["earningsGrowth"] * 100) if i["earningsGrowth"] > 0 else None
    preco = i.get("currentPrice") or i.get("regularMarketPrice")
    dy = i.get("dividendYield")
    d.update(
        nome=i.get("shortName") or t, moeda=i.get("currency", ""), setor=i.get("sector", ""),
        preco=preco, var_dia=i.get("regularMarketChangePercent"), pe=pe, fpe=fpe, peg=peg,
        dividendo=dy, alvo=i.get("targetMeanPrice"), recomendacao=i.get("recommendationKey"),
        pe_cls=classificar_pe(pe, cfg["limiares"]["pe"]),
        fpe_cls=classificar_pe(fpe, cfg["limiares"]["pe"]),
        peg_cls=classificar_peg(peg, cfg["limiares"]["peg"]),
        noticias=noticias(t, cfg.get("noticias_por_empresa", 3)),
    )
    q, pm = e.get("quantidade"), e.get("preco_medio")
    if q and pm and preco:
        d["valor"] = q * preco
        d["pl_pct"] = (preco / pm - 1) * 100
    return d


def f(v, nd=2, suf=""):
    return "—" if v is None else f"{v:,.{nd}f}{suf}"


def data_noticia(x):
    ts = x.get("providerPublishTime")
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%d/%m %H:%M") if ts else ""


def cartao(d):
    e = html.escape
    if d["erro"]:
        return f'<article class="card" data-tipo="{d["tipo"]}"><h3>{e(d["ticker"])}</h3><p>Erro: {e(d["erro"])}</p></article>'

    def met(rot, v, cls, dica):
        return (f'<div class="met" title="{dica}"><span>{rot}</span><b>{v[0]}</b>'
                f'<em class="tag {cls[1]}">{cls[0]}</em></div>')

    pl = ""
    if "pl_pct" in d:
        c = "ok" if d["pl_pct"] >= 0 else "bad"
        pl = f'<p class="pl {c}">Posição: {f(d["valor"], 0)} {e(d["moeda"])} · {f(d["pl_pct"], 1, "%")}</p>'
    nots = "".join(
        f'<li><a href="{e(x.get("link", "#"))}" target="_blank" rel="noopener">{e(x.get("title", ""))}</a>'
        f'<small>{e(x.get("publisher", ""))} · {data_noticia(x)}</small></li>' for x in d["noticias"]
    ) or "<li><small>Sem notícias recentes.</small></li>"
    vd = d.get("var_dia")
    return f'''<article class="card" data-tipo="{d["tipo"]}" data-pe="{d["pe"] or 9999}" data-peg="{d["peg"] or 9999}" data-nome="{e(d["ticker"])}">
<header><h3>{e(d["ticker"])} <small>{e(d["nome"])}</small></h3><span class="badge">{"Carteira" if d["tipo"] == "carteira" else "A seguir"}</span></header>
<p class="preco">{f(d["preco"])} {e(d["moeda"])} <span class="{"ok" if (vd or 0) >= 0 else "bad"}">{f(vd, 2, "%")}</span></p>
<div class="mets">{met("P/E (12m passados)", (f(d["pe"], 1),), d["pe_cls"], "Preço pago por cada $ de lucro do último ano")}
{met("P/E (próx. 12m)", (f(d["fpe"], 1),), d["fpe_cls"], "Preço sobre lucro esperado")}
{met("PEG", (f(d["peg"], 2),), d["peg_cls"], "P/E ajustado ao crescimento")}</div>
<p class="sub">Dividendo {f(d["dividendo"], 2, "%")} · Preço-alvo {f(d["alvo"])} · Analistas: {e(d["recomendacao"] or "—")}</p>
{pl}{f'<p class="nota">📝 {e(d["notas"])}</p>' if d["notas"] else ""}
<ul class="news">{nots}</ul></article>'''


def main():
    cfg = json.loads((AQUI / "carteira.json").read_text())
    dados = [recolher(e, cfg) for e in cfg["empresas"]]
    mercado = []
    try:
        mercado = yf.Search("stock market today", news_count=6).news
    except Exception:
        pass
    mkt = "".join(
        f'<li><a href="{html.escape(x.get("link", "#"))}" target="_blank" rel="noopener">{html.escape(x.get("title", ""))}</a>'
        f'<small>{html.escape(x.get("publisher", ""))} · {data_noticia(x)}</small></li>' for x in mercado
    ) or "<li><small>Sem notícias.</small></li>"
    t = cfg["limiares"]
    agora = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    modelo = (AQUI / "modelo.html").read_text()
    out = (modelo.replace("{{CARTOES}}", "\n".join(cartao(d) for d in dados))
           .replace("{{MERCADO}}", mkt).replace("{{DATA}}", agora)
           .replace("{{LEGENDA}}", f'P/E: &lt;{t["pe"]["barato"]} barato · ≤{t["pe"]["justo"]} justo · &gt;{t["pe"]["justo"]} caro (≈{t["pe"]["caro"]}) · &gt;{t["pe"]["muito_caro"]} muito caro &nbsp;|&nbsp; PEG: &lt;{t["peg"]["desconto"]} desconto · {t["peg"]["desconto"]}–{t["peg"]["justo"]} justo · &gt;{t["peg"]["justo"]} premium'))
    (AQUI / "relatorio.html").write_text(out)
    (AQUI / "dados.json").write_text(json.dumps(dados, indent=1, default=str, ensure_ascii=False))
    print(f"{len(dados)} empresas -> relatorio.html")


if __name__ == "__main__":
    sys.exit(main())
