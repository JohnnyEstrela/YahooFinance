"""Classificação de P/E e PEG segundo os limites definidos em watchlist.json."""

DEFAULT_LIMITS = {
    "pe": {"barato": 15, "justo": 30, "caro": 50},
    "peg": {"desconto": 1, "justo": 2},
}


def classify_pe(pe, limits=None):
    """Devolve (etiqueta, nivel) com nivel em good|ok|warn|bad|na."""
    lim = (limits or DEFAULT_LIMITS)["pe"]
    if pe is None:
        return "N/D", "na"
    if pe <= 0:
        return "Prejuízo", "bad"
    if pe < lim["barato"]:
        return "Barato", "good"
    if pe < lim["justo"]:
        return "Justo", "ok"
    if pe <= lim["caro"]:
        return "Caro", "warn"
    return "Muito caro", "bad"


def classify_peg(peg, limits=None):
    lim = (limits or DEFAULT_LIMITS)["peg"]
    if peg is None or peg <= 0:
        return "N/D", "na"
    if peg < lim["desconto"]:
        return "Desconto", "good"
    if peg <= lim["justo"]:
        return "Justo", "ok"
    return "Prémio", "warn"


def derive_peg(forward_pe, trailing_pe, growth_pct):
    """PEG calculado quando o Yahoo não o fornece: P/E / crescimento (%)."""
    pe = forward_pe or trailing_pe
    if pe and growth_pct and growth_pct > 0:
        return round(pe / growth_pct, 2)
    return None
