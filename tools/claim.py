#!/usr/bin/env python3
"""Master list for Walking the American Way. Safe for concurrent agents (file lock).

  python3 claim.py --list                      # show the whole list
  python3 claim.py NUM --setting "..." --year 1918 --community "..." \
      --teacher "..." --scripture "..." --status writing|done [--title "..."] [--agent NAME]

NUM is the commentary story number, e.g. 8.13. Rows are keyed by NUM.
"""
import argparse, fcntl, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "master_list.json")
FIELDS = ["title", "setting", "year", "community", "teacher", "scripture", "status", "agent"]

def load(f):
    f.seek(0); txt = f.read()
    return json.loads(txt) if txt.strip() else {}

def key(n):
    return [int(x) for x in n.split(".")]

def show(db):
    rows = sorted(db.items(), key=lambda kv: key(kv[0]))
    print(f"{'num':6} {'status':9} {'year':6} {'setting':38} {'community':30} {'teacher':30} {'scripture':24} title")
    for n, r in rows:
        print(f"{n:6} {r.get('status',''):9} {str(r.get('year','')):6} {r.get('setting','')[:38]:38} {r.get('community','')[:30]:30} {r.get('teacher','')[:30]:30} {r.get('scripture','')[:24]:24} {r.get('title','')}")

ap = argparse.ArgumentParser()
ap.add_argument("num", nargs="?")
ap.add_argument("--list", action="store_true")
for fld in FIELDS: ap.add_argument("--" + fld)
a = ap.parse_args()
with open(DB, "a+") as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    db = load(f)
    if a.list or not a.num:
        show(db); sys.exit(0)
    row = db.setdefault(a.num, {})
    for fld in FIELDS:
        v = getattr(a, fld)
        if v is not None: row[fld] = v
    f.seek(0); f.truncate(); json.dump(db, f, indent=1, ensure_ascii=False)
    print("saved", a.num, row)
