"""Split a daily snapshot into one JSON file per dashboard database document.

    python portfolio/to_db_files.py snapshot.json out_dir/

Writes out_dir/metrics/<TICKER>.json and out_dir/market/latest.json, which the
routine then sends to the artifact's database (collections `metrics`, `market`).
"""

import json
import os
import sys

snap = json.load(open(sys.argv[1]))
out = sys.argv[2]
os.makedirs(f"{out}/metrics", exist_ok=True)
os.makedirs(f"{out}/market", exist_ok=True)
for key, doc in snap["companies"].items():
    doc = dict(doc, key=key, generatedAt=snap["generatedAt"])
    json.dump(doc, open(f"{out}/metrics/{key}.json", "w"), ensure_ascii=False)
json.dump(
    {"generatedAt": snap["generatedAt"], "indices": snap["indices"], "marketNews": snap["marketNews"]},
    open(f"{out}/market/latest.json", "w"),
    ensure_ascii=False,
)
print("\n".join(sorted(os.listdir(f"{out}/metrics"))))
