"""Gera o dashboard do Consultor Financeiro.

Uso:  python consultor/build.py [data/AAAA-MM-DD.json]

Lê portfolio.json (as tuas empresas e limites) e o snapshot diário em data/
(o mais recente se não indicares nenhum), calcula os rácios e escreve
dashboard.html. Só usa a biblioteca padrão do Python.

Rácios calculados
- P/E (últimos 12 meses) = preço / EPS TTM
- P/E (próximos 12 meses) = preço / EPS NTM, onde o EPS NTM é a média
  ponderada pelo tempo das estimativas dos analistas para o ano fiscal
  corrente e o seguinte
- Crescimento esperado = CAGR do EPS estimado entre o próximo ano fiscal e
  dois anos depois (ignora o ano corrente, que muitas vezes tem ganhos
  pontuais)
- PEG  = P/E futuro / crescimento (%)
- PEGY = P/E futuro / (crescimento % + dividend yield %)
"""

from __future__ import annotations

import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_snapshot() -> Path:
    files = sorted((ROOT / "data").glob("*.json"))
    if not files:
        sys.exit("Sem snapshots em consultor/data/")
    return files[-1]


def ntm_eps(estimates: dict[str, float], today: date) -> tuple[float | None, list[date]]:
    """EPS dos próximos 12 meses e lista ordenada de fins de ano fiscal futuros."""
    fy = sorted((date.fromisoformat(d), v) for d, v in estimates.items())
    future = [(d, v) for d, v in fy if d > today]
    if not future:
        return None, []
    if len(future) == 1:
        return future[0][1], [d for d, _ in future]
    (d1, e1), (_, e2) = future[0], future[1]
    w = min(max((d1 - today).days / 365.0, 0.0), 1.0)
    return w * e1 + (1 - w) * e2, [d for d, _ in future]


def growth(estimates: dict[str, float], today: date) -> float | None:
    fy = sorted((date.fromisoformat(d), v) for d, v in estimates.items() if date.fromisoformat(d) > today)
    vals = [v for _, v in fy]
    # próximo ano fiscal (índice 1) -> dois anos depois (índice 3)
    for start, end in ((1, 3), (0, 2), (0, 1)):
        if len(vals) > end and vals[start] > 0 and vals[end] > 0:
            years = end - start
            return (vals[end] / vals[start]) ** (1 / years) - 1
    return None


def pe_zone(pe: float | None, lim: dict) -> tuple[str, str]:
    if pe is None:
        return "na", "Sem dados"
    if pe <= 0:
        return "neg", "Sem lucro"
    if pe < lim["barato"]:
        return "cheap", "Barato"
    if pe < lim["justo"]:
        return "fair", "Fair Value"
    if pe <= lim["caro"]:
        return "pricey", "Pricey"
    return "exp", "Expensive"


def peg_zone(peg: float | None, lim: dict) -> tuple[str, str]:
    if peg is None or peg <= 0:
        return "na", "n/d"
    if peg < lim["desconto"]:
        return "cheap", "Desconto"
    if peg <= lim["justo"]:
        return "fair", "Justo"
    return "exp", "Premium"


def compute(portfolio: dict, snap: dict) -> list[dict]:
    today = date.fromisoformat(snap["data"])
    lim = portfolio["limites"]
    rows = []
    for c in portfolio["empresas"]:
        t = c["ticker"].upper()
        d = snap["empresas"].get(t)
        row = {"ticker": t, "nome": c.get("nome") or t, "estado": c.get("estado", "seguir"),
               "exemplo": bool(c.get("exemplo")), "acoes": c.get("acoes"),
               "preco_medio": c.get("preco_medio"), "sem_dados": d is None}
        if d is None:
            rows.append(row)
            continue
        price = d["preco"]
        eps_ttm = d.get("eps_ttm")
        pe_ttm = price / eps_ttm if eps_ttm else None
        eps_ntm, _ = ntm_eps(d.get("estimativas_eps", {}), today)
        pe_fwd = price / eps_ntm if eps_ntm else None
        g = growth(d.get("estimativas_eps", {}), today)
        y = d.get("dividend_yield") or 0.0
        peg = pe_fwd / (g * 100) if (pe_fwd and pe_fwd > 0 and g and g > 0) else None
        pegy = pe_fwd / ((g + y) * 100) if (pe_fwd and pe_fwd > 0 and g is not None and g + y > 0) else None
        row.update({
            "nome": c.get("nome") or d["nome"], "nome_completo": d["nome"],
            "preco": price, "variacao_pct": d.get("variacao_pct"),
            "min_52s": d.get("min_52s"), "max_52s": d.get("max_52s"),
            "media_50d": d.get("media_50d"), "media_200d": d.get("media_200d"),
            "market_cap": d.get("market_cap"),
            "eps_ttm": eps_ttm, "eps_ntm": eps_ntm,
            "pe_ttm": pe_ttm, "pe_fwd": pe_fwd, "crescimento": g, "yield": y,
            "peg": peg, "pegy": pegy,
            "z_pe_ttm": pe_zone(pe_ttm, lim["pe"]), "z_pe_fwd": pe_zone(pe_fwd, lim["pe"]),
            "z_pegy": peg_zone(pegy, lim["peg"]), "z_peg": peg_zone(peg, lim["peg"]),
            "leitura": d.get("leitura", ""), "noticias": d.get("noticias", []),
        })
        if c.get("acoes") and c.get("preco_medio"):
            row["valor"] = c["acoes"] * price
            row["ganho_pct"] = price / c["preco_medio"] - 1
        rows.append(row)
    return rows


def render(portfolio: dict, snap: dict, rows: list[dict]) -> str:
    template = (ROOT / "template.html").read_text(encoding="utf-8")
    payload = {"data": snap["data"], "fonte": snap.get("fonte_dados", ""),
               "limites": portfolio["limites"], "mercado": snap.get("mercado", {}),
               "empresas": rows}
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return (template.replace("__DATA_JSON__", blob)
                    .replace("__DATA__", html.escape(snap["data"])))


def main() -> None:
    snap_path = Path(sys.argv[1]) if len(sys.argv) > 1 else latest_snapshot()
    if not snap_path.is_absolute():
        snap_path = (Path.cwd() / snap_path).resolve()
    portfolio = load(ROOT / "portfolio.json")
    snap = load(snap_path)
    rows = compute(portfolio, snap)
    out = ROOT / "dashboard.html"
    out.write_text(render(portfolio, snap, rows), encoding="utf-8")
    for r in rows:
        if r["sem_dados"]:
            print(f"{r['ticker']:6} sem dados neste snapshot")
            continue
        f = lambda v, p="{:.1f}": "—" if v is None else p.format(v)
        print(f"{r['ticker']:6} P/E TTM {f(r['pe_ttm']):>6} ({r['z_pe_ttm'][1]:<10}) "
              f"P/E NTM {f(r['pe_fwd']):>6} ({r['z_pe_fwd'][1]:<10}) "
              f"cresc {f(r['crescimento'] and r['crescimento']*100):>5}%  "
              f"PEG {f(r['peg'], '{:.2f}'):>5}  PEGY {f(r['pegy'], '{:.2f}'):>5} ({r['z_pegy'][1]})")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
