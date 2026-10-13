import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from update import classify_pe, classify_peg, parse_news  # noqa: E402

PE = {"cheap": 15, "fair": 30, "pricey": 50}
PEG = {"discount": 1, "fair": 2}


def test_pe():
    assert classify_pe(10, PE) == "barato"
    assert classify_pe(20, PE) == "fair"
    assert classify_pe(40, PE) == "pricey"
    assert classify_pe(60, PE) == "expensive"
    assert classify_pe(-5, PE) is None and classify_pe(None, PE) is None


def test_peg():
    assert classify_peg(0.8, PEG) == "discount"
    assert classify_peg(1.5, PEG) == "fair"
    assert classify_peg(2.5, PEG) == "premium"
    assert classify_peg(None, PEG) is None


def test_news():
    n = parse_news([{"content": {"title": "x", "canonicalUrl": {"url": "http://a"}}}, {"content": {}}])
    assert n == [{"title": "x", "url": "http://a", "publisher": None, "date": None}]
