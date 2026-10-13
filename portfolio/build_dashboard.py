"""Gera docs/index.html (dashboard responsivo, claro/escuro) a partir de data/snapshot.json + thresholds.json."""
import json, pathlib
here = pathlib.Path(__file__).parent
snap = json.loads((here / "data" / "snapshot.json").read_text())
th = json.loads((here / "thresholds.json").read_text())
pf = json.loads((here / "portfolio.json").read_text())
TEMPLATE = (here / "template.html").read_text()
html = TEMPLATE.replace("/*DATA*/", json.dumps({"snap": snap, "th": th, "pf": pf}))
out = here.parent / "docs" / "index.html"
out.write_text(html)
print("escrito", out)
