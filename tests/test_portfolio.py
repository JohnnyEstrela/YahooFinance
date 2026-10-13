import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "portfolio"))
from build_report import build  # noqa: E402
from valuation import classify_pe, classify_peg  # noqa: E402


def test_pe_bands():
    assert classify_pe(10)[0] == "Barato"
    assert classify_pe(20)[0] == "Justo"
    assert classify_pe(40)[0] == "Caro"
    assert classify_pe(55)[0] == "Muito caro"
    assert classify_pe(-3)[0] == "Sem lucros"
    assert classify_pe(None)[0] == "n/d"


def test_peg_bands():
    assert classify_peg(0.8)[0] == "Desconto"
    assert classify_peg(1.5)[0] == "Justo"
    assert classify_peg(2.5)[0] == "Prémio"


def test_build_escapes_and_handles_missing():
    watch = {"companies": [{"ticker": "X", "status": "portfolio"}, {"ticker": "Y"}]}
    snap = {"companies": [{"ticker": "X", "name": "<b>X</b>", "price": 1, "news": []}]}
    html = build(watch, snap)
    assert "&lt;b&gt;X&lt;/b&gt;" in html and "Sem dados" in html
