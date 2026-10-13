#!/usr/bin/env python3
"""Gera docs/dashboard.html (página de Artifact) a partir de portfolio.json + data/snapshot.json."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
cfg = json.loads((ROOT / "portfolio.json").read_text())
snap = json.loads((ROOT / "data/snapshot.json").read_text())
payload = {"thresholds": cfg["thresholds"], "companies": cfg["companies"], "snapshot": snap}
blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
tpl = (ROOT / "dashboard_template.html").read_text()
(ROOT / "docs/dashboard.html").write_text(tpl.replace("/*__DATA__*/null", blob))
print("docs/dashboard.html gerado")
