"""Classificação de valuation (P/E e PEG) com limiares configuráveis."""

from __future__ import annotations

DEFAULT_THRESHOLDS = {
    "pe": {"cheap": 15, "fair": 30, "pricey": 50},
    "peg": {"discount": 1, "fair": 2},
}

PE_LABELS = {
    "cheap": "Barato",
    "fair": "Justo",
    "pricey": "Caro",
    "expensive": "Muito caro",
    "none": "Sem lucros",
}
PEG_LABELS = {"discount": "Desconto", "fair": "Justo", "premium": "Prémio", "none": "n/d"}


def classify_pe(value: float | None, th: dict | None = None) -> str:
    """P/E < cheap: barato; < fair: justo; < pricey: caro; >= pricey: muito caro."""
    th = th or DEFAULT_THRESHOLDS["pe"]
    if value is None or value <= 0:
        return "none"
    if value < th["cheap"]:
        return "cheap"
    if value < th["fair"]:
        return "fair"
    if value < th["pricey"]:
        return "pricey"
    return "expensive"


def classify_peg(value: float | None, th: dict | None = None) -> str:
    """PEG < discount: desconto; <= fair: justo; > fair: prémio."""
    th = th or DEFAULT_THRESHOLDS["peg"]
    if value is None or value <= 0:
        return "none"
    if value < th["discount"]:
        return "discount"
    if value <= th["fair"]:
        return "fair"
    return "premium"
