import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from valuation import classify_pe, classify_peg, derive_peg  # noqa: E402


def test_pe_bands():
    assert classify_pe(10) == ("Barato", "good")
    assert classify_pe(20) == ("Justo", "ok")
    assert classify_pe(40) == ("Caro", "warn")
    assert classify_pe(60) == ("Muito caro", "bad")
    assert classify_pe(-3)[0] == "Prejuízo"
    assert classify_pe(None)[0] == "N/D"


def test_peg_bands():
    assert classify_peg(0.8) == ("Desconto", "good")
    assert classify_peg(1.5) == ("Justo", "ok")
    assert classify_peg(2.5) == ("Prémio", "warn")
    assert classify_peg(None)[0] == "N/D"


def test_derive_peg():
    assert derive_peg(20, None, 10) == 2.0
    assert derive_peg(None, None, 10) is None
    assert derive_peg(20, None, -5) is None
