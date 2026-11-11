#!/usr/bin/env python3
"""Insert (or refresh) a small locator map in each story's Background, before the history section."""
import json, re, html, os, glob
HERE = os.path.dirname(os.path.abspath(__file__))
maps = json.load(open("/home/claude/maptool/maps.json"))
metas = {json.load(open(p))["file"]: json.load(open(p)) for p in glob.glob(os.path.join(HERE, "meta", "*.json"))}
done = skipped = 0
for f, svg in maps.items():
    p = os.path.join(HERE, f)
    if not os.path.exists(p): continue
    h = open(p).read()
    fig = ('<figure class="locmap" style="margin:1.6rem 0 1.8rem;max-width:320px">' + svg.replace("<svg ", '<svg style="display:block;width:100%;height:auto" ', 1) +
           f'<figcaption style="font-size:.85rem;font-style:italic;opacity:.75;margin-top:.4rem">{html.escape(metas[f]["place"])}</figcaption></figure>')
    h = re.sub(r'<figure class="locmap".*?</figure>\s*', '', h, flags=re.S)
    m = re.search(r'<div class="bg-body">(.*?)</details>', h, re.S)
    if not m: skipped += 1; print("no bg-body:", f); continue
    body_start = m.start(1)
    h3s = [x.start() for x in re.finditer(r'<h3', h[body_start:m.end(1)])]
    if len(h3s) >= 2: pos = body_start + h3s[1]
    else:
        end = h.rfind("</div>", body_start, m.end(1)); pos = end if end > 0 else m.end(1)
    h2 = h[:pos] + fig + "\n    " + h[pos:]
    if h2 != open(p).read(): open(p, "w").write(h2); done += 1
print("maps inserted:", done, "skipped:", skipped)
