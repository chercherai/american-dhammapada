#!/bin/sh
# Copy finished site + tooling from the working folder into the repo
cd /home/claude/series && ./done_files.sh > /tmp/done.json
cd /home/claude/american-dhammapada
python3 - <<'PY'
import json, shutil, os
src = "/home/claude/series"
for f in json.load(open("/tmp/done.json")):
    shutil.copy(f["path"], f["as"])
shutil.copy(os.path.join(src, "prefs.js"), "prefs.js")
os.makedirs("tools", exist_ok=True); os.makedirs("meta", exist_ok=True)
for t in ["HOUSE_STYLE.md", "MOTIFS.md", "SEEDS.md", "master_list.json", "claim.py", "build_index.py", "build_views.py", "na-land.json", "prefs.js"]:
    shutil.copy(os.path.join(src, t), os.path.join("tools", t))
done = {f["as"] for f in json.load(open("/tmp/done.json"))}
for m in os.listdir(os.path.join(src, "meta")):
    if json.load(open(os.path.join(src, "meta", m)))["file"] in done:
        shutil.copy(os.path.join(src, "meta", m), os.path.join("meta", m))
PY
