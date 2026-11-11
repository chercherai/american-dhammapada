#!/usr/bin/env python3
"""Rebuild index.html from meta/*.json and rewrite every story's pager (prev / all / next)."""
import glob, html, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
metas = [json.load(open(p)) for p in glob.glob(os.path.join(HERE, "meta", "*.json"))]
ml = json.load(open(os.path.join(HERE, "master_list.json")))
metas = [m for m in metas if os.path.exists(os.path.join(HERE, m["file"])) and ml.get(m["num"], {}).get("status") == "done"]
metas.sort(key=lambda m: [int(x) for x in m["num"].split(".")])
e = html.escape
CH = ["The Twin-Verses", "On Earnestness", "Thought", "Flowers", "The Fool", "The Wise Man", "The Venerable", "The Thousands", "Evil", "Punishment", "Old Age", "Self", "The World", "The Buddha", "Happiness", "Pleasure", "Anger", "Impurity", "The Just", "The Way", "Miscellaneous", "The Downward Course", "The Elephant", "Thirst", "The Bhikshu", "The Brahmana"]
from collections import Counter
chn = Counter(m["num"].split(".")[0] for m in metas)
items, seen = [], set()
for m in metas:
    c = m["num"].split(".")[0]
    if c not in seen:
        seen.add(c)
        items.append(f'    <li class="chapter" data-rail="{c}" data-rail-major data-rail-n="{chn[c]}" data-rail-tip="{c} &middot; {e(CH[int(c)-1])}"><h2><span class="cn">Chapter {c}</span>{e(CH[int(c)-1])}</h2></li>')
    items.append(f'''    <li><a href="{e(m['file'])}">
      <span class="num">{e(m['num'])}</span>
      <span class="title"><span class="dot" style="background:{e(m['accent'])};box-shadow:0 0 10px {e(m['glow'])}"></span>{e(m['title'])}</span>
      <span class="meta">{e(m['place'])} &middot; {e(str(m['year']))} &middot; after {e(m['source'])} &middot; {e(m.get('model','').replace('Claude ',''))}</span>
      <span class="line">{e(m['logline'])}</span>
    </a></li>''')
idx_path = os.path.join(HERE, "index.html")
idx = open(idx_path).read()
idx = re.sub(r"<ol>.*?</ol>", "<ol>\n" + "\n".join(items) + "\n  </ol>", idx, count=1, flags=re.S)
idx = re.sub(r'<p class="count">.*?</p>', f'<p class="count">{'All ' + str(len(metas)) + ' stories' if len(metas)==305 else str(len(metas)) + ' stories so far'}</p>', idx)
if "li.chapter" not in idx:
    idx = idx.replace("ol { list-style: none;", """li.chapter { border-bottom: none; scroll-margin-top: .5rem; }
li.chapter h2 { font-family: var(--font-display); font-weight: 400; font-size: clamp(2.2rem, 6vw, 2.8rem); line-height: 1.15; margin: 3.5rem 0 0; padding: 0 0 .9rem; border-bottom: 1px solid var(--rule); }
li.chapter:first-child h2 { margin-top: 1.5rem; }
li.chapter .cn { display: block; font-style: italic; font-size: 1rem; color: var(--page-dim); margin-bottom: .2rem; }
ol { list-style: none;""", 1)
if '<script src="rail.js"></script>' not in idx:
    idx = idx.replace("</body>", '<script src="rail.js"></script>\n</body>', 1)
if idx != open(idx_path).read(): open(idx_path, "w").write(idx)
for i, m in enumerate(metas):
    p = os.path.join(HERE, m["file"]); s = open(p).read()
    prev = f'<a href="{e(metas[i-1]["file"])}">&larr; {e(metas[i-1]["title"])}</a>' if i > 0 else '<span></span>'
    nxt = f'<a href="{e(metas[i+1]["file"])}">{e(metas[i+1]["title"])} &rarr;</a>' if i < len(metas) - 1 else '<span></span>'
    pager = f'<div class="pager">{prev}<a href="index.html">All stories</a>{nxt}</div>'
    s2, n = re.subn(r'<div class="pager">.*?</div>', pager, s, count=1, flags=re.S)
    if n == 0:
        s2 = s.replace("</footer>", "  " + pager + "\n</footer>", 1)
    if s2 != s: open(p, "w").write(s2)
print(f"index: {len(metas)} stories")
