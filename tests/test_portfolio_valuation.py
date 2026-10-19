import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "portfolio"))

from valuation import classify_peg, classify_pe  # noqa: E402


def test_pe_bands():
    assert classify_pe(10) == "cheap"
    assert classify_pe(15) == "fair"
    assert classify_pe(20) == "fair"
    assert classify_pe(40) == "pricey"
    assert classify_pe(50) == "expensive"
    assert classify_pe(None) == "none"
    assert classify_pe(-5) == "none"


def test_peg_bands():
    assert classify_peg(0.8) == "discount"
    assert classify_peg(1) == "fair"
    assert classify_peg(2) == "fair"
    assert classify_peg(2.1) == "premium"
    assert classify_peg(None) == "none"
