"""Classificação de avaliação (P/E e PEG) com limiares configuráveis."""

DEFAULT_THRESHOLDS = {
    "pe": {"cheap": 15, "fair": 30, "pricey": 50},
    "peg": {"discount": 1, "fair": 2},
}


def classify_pe(value, th=None):
    """P/E: < cheap Barato | < fair Justo | < pricey Caro | senão Muito caro."""
    th = (th or DEFAULT_THRESHOLDS)["pe"]
    if value is None:
        return "n/d", "na"
    if value <= 0:
        return "Sem lucros", "bad"
    if value < th["cheap"]:
        return "Barato", "good"
    if value < th["fair"]:
        return "Justo", "ok"
    if value < th["pricey"]:
        return "Caro", "warn"
    return "Muito caro", "bad"


def classify_peg(value, th=None):
    """PEG: < discount Desconto | <= fair Justo | senão Prémio."""
    th = (th or DEFAULT_THRESHOLDS)["peg"]
    if value is None:
        return "n/d", "na"
    if value <= 0:
        return "Sem crescimento", "bad"
    if value < th["discount"]:
        return "Desconto", "good"
    if value <= th["fair"]:
        return "Justo", "ok"
    return "Prémio", "warn"
