#!/usr/bin/env python3
"""Build timeline.html and map.html from meta/*.json (finished stories only), and add view nav to index.html."""
import glob, html, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
ml = json.load(open(os.path.join(HERE, "master_list.json")))
metas = [json.load(open(p)) for p in glob.glob(os.path.join(HERE, "meta", "*.json"))]
metas = [m for m in metas if os.path.exists(os.path.join(HERE, m["file"])) and ml.get(m["num"], {}).get("status") == "done"]
e = html.escape

def year_of(m):
    y = re.findall(r"\d{4}", str(m["year"]))
    return int(y[0]) if y else 0

def NAV(cur):
    out = []
    for k, h, t in [("num", "index.html", "By number"), ("year", "timeline.html", "By year"), ("map", "map.html", "On the map")]:
        ac = ' aria-current="page"' if k == cur else ""
        out.append(f'<a href="{h}"{ac}>{t}</a>')
    return '<nav class="views">' + "".join(out) + "</nav>"

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Spectral:ital,wght@0,300;0,400;1,300;1,400&display=swap" rel="stylesheet">
<style>
:root {{
  /* Layout: series front matter; {layout} */
  --ink: #111214; --ink-2: #1a1c1f; --page: #e6e1d6; --page-dim: #9d978b; --rule: rgba(230,225,214,.12);
  --font-display: "IM Fell English", "Iowan Old Style", Georgia, serif;
  --font-body: "Spectral", "Iowan Old Style", Georgia, serif;
  color-scheme: dark;
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; }}
body {{ background: var(--ink); color: var(--page); font-family: var(--font-body); font-weight: 300; font-size: 1.1rem; line-height: 1.7; -webkit-font-smoothing: antialiased; }}
main {{ max-width: {maxw}; margin: 0 auto; padding: 4rem 1.25rem 6rem; }}
.kicker {{ font-family: var(--font-display); font-style: italic; color: var(--page-dim); margin: 0 0 1rem; }}
h1 {{ font-family: var(--font-display); font-weight: 400; font-size: clamp(2.4rem, 7vw, 3.6rem); line-height: 1.02; margin: 0 0 1rem; text-wrap: balance; }}
.views {{ display: flex; gap: 1.25rem; flex-wrap: wrap; font-family: var(--font-display); font-size: 1.1rem; margin: 0 0 2.5rem; }}
.views a {{ color: var(--page-dim); text-decoration: none; border-bottom: 1px solid transparent; }}
.views a[aria-current] {{ color: var(--page); border-bottom-color: var(--page); }}
.views a:hover {{ color: var(--page); }}
a:focus-visible {{ outline: 2px solid var(--page); outline-offset: 3px; }}
.dot {{ width: .55rem; height: .55rem; border-radius: 50%; flex: none; display: inline-block; }}
{extra}
</style>
</head>
<body>
<main>
  <p class="kicker">Walking the American Way</p>
  <h1>{h1}</h1>
  {nav}
"""

# ---------- timeline ----------
ms = sorted(metas, key=lambda m: (year_of(m), m["num"]))
rows, cur_c = [], None
for m in ms:
    y = year_of(m); c = y // 100
    if c != cur_c:
        rows.append(f'<li class="century"><span>{c}00s</span></li>'); cur_c = c
    model = e(m.get("model", "").replace("Claude ", ""))
    rows.append(f'''<li><a href="{e(m['file'])}">
  <span class="yr">{y}</span>
  <span class="t"><span class="dot" style="background:{e(m['accent'])};box-shadow:0 0 8px {e(m['glow'])}"></span>{e(m['title'])}</span>
  <span class="m">{e(m['place'])} &middot; commentary {e(m['num'])}, after {e(m['source'])} &middot; {model}</span>
</a></li>''')
extra = """
ol { list-style: none; margin: 0; padding: 0; position: relative; }
ol::before { content: ""; position: absolute; left: 3.6rem; top: 0; bottom: 0; width: 1px; background: var(--rule); }
li.century span { display: block; font-family: var(--font-display); font-style: italic; color: var(--page-dim); font-size: 1.3rem; padding: 2rem 0 .5rem 4.6rem; }
li a { display: grid; grid-template-columns: 3.2rem 1fr; gap: 0 1.4rem; padding: .7rem 0; color: inherit; text-decoration: none; }
.yr { font-family: var(--font-display); color: var(--page-dim); font-variant-numeric: tabular-nums; text-align: right; padding-top: .15rem; }
.t { font-family: var(--font-display); font-size: 1.45rem; line-height: 1.2; display: flex; align-items: center; gap: .6rem; }
.m { grid-column: 2; font-size: .95rem; color: var(--page-dim); font-style: italic; }
li a:hover .t { text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: .2em; }
"""
page = HEAD.format(title="Walking the American Way by Year", layout="one vertical timeline grouped by century", maxw="40rem", extra=extra, h1="By year", nav=NAV("year"))
page += f'  <p class="kicker">{len(ms)} stories, {year_of(ms[0])} to {year_of(ms[-1])}</p>\n  <ol>\n' + "\n".join(rows) + "\n  </ol>\n</main>\n</body>\n</html>\n"
open(os.path.join(HERE, "timeline.html"), "w").write(page)

# ---------- map ----------
land = json.load(open(os.path.join(HERE, "na-land.json")))
pts = [dict(t=m["title"], f=m["file"], p=m["place"], y=year_of(m), n=m["num"], a=m["accent"], lat=m["lat"], lon=m["lon"],
            r=m.get("route", []))
       for m in metas if "lat" in m]
extra = """
svg { width: 100%; height: auto; display: block; }
.land { fill: #1d2024; stroke: #3a3e44; stroke-width: .5; }
.sea { fill: #141619; }
.grat { fill: none; stroke: rgba(230,225,214,.05); stroke-width: .5; }
.route { fill: none; stroke-width: 1.2; stroke-dasharray: 3 4; opacity: .7; }
.pin { cursor: pointer; stroke: #111214; stroke-width: 1.2; }
.pin:hover, .pin.on { stroke: #e6e1d6; stroke-width: 2; }
#card { min-height: 6.5rem; margin-top: 1.25rem; padding: 1rem 1.25rem; border: 1px solid var(--rule); background: var(--ink-2); }
#card .t { font-family: var(--font-display); font-size: 1.6rem; color: var(--page); text-decoration: none; display: flex; align-items: center; gap: .6rem; }
#card .t:hover { text-decoration: underline; }
#card p { margin: .25rem 0 0; color: var(--page-dim); font-style: italic; font-size: .95rem; }
.hint { color: var(--page-dim); font-style: italic; font-size: .95rem; }
"""
page = HEAD.format(title="Walking the American Way on the Map", layout="one full-width map of the continent, no borders drawn, a detail card below", maxw="62rem", extra=extra, h1="On the map", nav=NAV("map"))
page += """  <svg id="map" viewBox="0 0 975 720" role="img" aria-label="Map of North America, without borders, with a point for each story"></svg>
  <div id="card"><p class="hint">Tap or hover a point to see the story set there. Dashed lines follow journeys.</p></div>
</main>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js"></script>
<script>
const LAND = """ + json.dumps(land, separators=(",", ":")) + """;
const PTS = """ + json.dumps(pts, ensure_ascii=False) + """;
const svg = d3.select("#map");
const land = topojson.feature(LAND, LAND.objects.land);
const frame = {type: "MultiPoint", coordinates: [[-160, 18], [-62, 16], [-150, 62], [-58, 52], [-100, 14], [-140, 68]]};
const proj = d3.geoConicConformal().parallels([20, 60]).rotate([105, 0]).fitExtent([[10, 10], [965, 710]], frame);
const path = d3.geoPath(proj);
svg.append("rect").attr("class", "sea").attr("width", 975).attr("height", 720);
svg.append("path").attr("class", "grat").attr("d", path(d3.geoGraticule().step([10, 10])()));
svg.append("path").attr("class", "land").attr("d", path(land));
const card = document.getElementById("card");
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
function show(p, el) {
  d3.selectAll(".pin").classed("on", false); d3.select(el).classed("on", true);
  card.innerHTML = '<a class="t" href="' + p.f + '"><span class="dot" style="background:' + p.a + '"></span>' + esc(p.t) + '</a><p>' + esc(p.p) + ' &middot; ' + p.y + ' &middot; commentary ' + esc(p.n) + '</p>';
}
const routes = svg.append("g"), g = svg.append("g");
PTS.forEach(p => {
  if (p.r && p.r.length) {
    const line = {type: "LineString", coordinates: [[p.lon, p.lat]].concat(p.r.map(q => [q[1], q[0]]))};
    routes.append("path").attr("class", "route").attr("stroke", p.a).attr("d", path(line));
    p.r.forEach(q => { const xy = proj([q[1], q[0]]); routes.append("circle").attr("cx", xy[0]).attr("cy", xy[1]).attr("r", 2.5).attr("fill", p.a).attr("opacity", .7); });
  }
});
PTS.sort((a, b) => a.lat - b.lat).forEach(p => {
  const xy = proj([p.lon, p.lat]); if (!xy) return;
  const c = g.append("circle").attr("class", "pin").attr("cx", xy[0]).attr("cy", xy[1]).attr("r", 6).attr("fill", p.a)
    .attr("tabindex", 0).attr("role", "link").attr("aria-label", p.t + ", " + p.p + ", " + p.y);
  c.append("title").text(p.t + " - " + p.p + ", " + p.y);
  const el = c.node();
  el.addEventListener("mouseenter", () => show(p, el));
  el.addEventListener("focus", () => show(p, el));
  el.addEventListener("click", () => { if (el.classList.contains("on") && matchMedia("(hover: hover)").matches) location.href = p.f; else show(p, el); });
  el.addEventListener("keydown", ev => { if (ev.key === "Enter") location.href = p.f; });
});
</script>
</body>
</html>
"""
open(os.path.join(HERE, "map.html"), "w").write(page)

# ---------- nav on index ----------
ip = os.path.join(HERE, "index.html"); s = open(ip).read()
if 'class="views"' not in s:
    css = """.views { display: flex; gap: 1.25rem; flex-wrap: wrap; font-family: var(--font-display); font-size: 1.1rem; margin: 0 0 2.5rem; }
.views a { color: var(--page-dim); text-decoration: none; border-bottom: 1px solid transparent; }
.views a[aria-current] { color: var(--page); border-bottom-color: var(--page); }
.views a:hover { color: var(--page); }
footer {"""
    s = s.replace("footer {", css, 1)
    s = s.replace('<p class="count">', NAV("num") + '\n  <p class="count">', 1)
    open(ip, "w").write(s)
print("views:", len(ms), "timeline,", len(pts), "map points")
