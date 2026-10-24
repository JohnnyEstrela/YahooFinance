import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "portfolio"))
import report  # noqa: E402

CFG = report.load()["thresholds"]


def test_pe_bands():
    keys = [report.classify(v, CFG["pe"])[0] for v in (10, 15, 19.9, 30, 45, 60)]
    assert keys == ["cheap", "fair", "fair", "pricey", "very_pricey", "expensive"]


def test_peg_bands():
    keys = [report.classify(v, CFG["peg"])[0] for v in (0.5, 1, 1.9, 2, 3)]
    assert keys == ["cheap", "fair", "fair", "expensive", "expensive"]


def test_missing_and_negative_pe():
    assert report.classify(None, CFG["pe"])[0] == "na"
    assert report.classify(-3, CFG["pe"]) == ("na", "Sem lucros")


def test_peg_fallback_and_pegy():
    peg, pegy, growth, dy = report.compute_peg({"forwardPE": 20, "earningsGrowth": 0.2, "dividendYield": 2})
    assert round(peg, 2) == 1.0 and round(pegy, 2) == round(20 / 22, 2) and growth == 20 and dy == 2


def test_normalize():
    assert report.normalize("brk.b") == "BRK-B" and report.normalize("ASML.AS") == "ASML.AS"
