#!/usr/bin/env python3
"""Build timeline.html and map.html from meta/*.json (finished stories only), and add view nav to index.html."""
import wc, re, glob, html, json, os, re
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
    for k, h, t in [("num", "index.html", "Verse"), ("year", "timeline.html", "Time"), ("map", "map.html", "Place")]:
        ac = ' aria-current="page"' if k == cur else ""
        out.append(f'<a href="{h}"{ac}>{t}</a>')
    out.append('<a href="#" id="nearme" title="A story set somewhere near you">Near you</a>')
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
rows, cur_c, decs = [], None, []
for m in ms:
    y = year_of(m); c = y // 100
    if c != cur_c:
        rows.append(f'<li class="century"><span>{c}00s</span></li>'); cur_c = c
    d = y // 10 * 10
    if not decs or decs[-1][0] != d:
        decs.append([d, 0]); rows.append(f'<li class="dec" id="d{d}" aria-hidden="true"></li>')
    decs[-1][1] += 1
    model = e(m.get("model", "").replace("Claude ", "")) + " &middot; " + wc.label(wc.count(open(os.path.join(HERE, m["file"])).read()))
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
li.dec { height: 0; scroll-margin-top: 1rem; }
#rail { position: fixed; right: .1rem; top: 8vh; bottom: 8vh; width: 2.6rem; display: flex; flex-direction: column; justify-content: space-between; align-items: flex-end; z-index: 5; touch-action: none; user-select: none; -webkit-user-select: none; cursor: ns-resize; padding: 0 .3rem; }
#rail .tk { flex: 1; display: flex; align-items: center; justify-content: flex-end; width: 100%; position: relative; }
#rail .tk::after { content: ""; height: 1px; width: .5rem; background: var(--page-dim); opacity: .45; }
#rail .tk::before { content: ""; position: absolute; right: 0; top: 15%; bottom: 15%; width: calc(.2rem + var(--n) * 2.2rem); background: var(--page-dim); opacity: .32; border-radius: 1px 0 0 1px; }
#rail .tk.c::after { width: .9rem; opacity: .9; }
#rail .tk.cur::after { background: var(--page); opacity: 1; width: 1.2rem; height: 2px; }
#rail .tk.c span { position: absolute; right: 1.2rem; font-family: var(--font-display); font-size: .78rem; color: var(--page-dim); font-variant-numeric: tabular-nums; }
#bubble { position: fixed; right: 3.4rem; padding: .25rem .7rem; background: var(--ink-2); border: 1px solid var(--rule); font-family: var(--font-display); font-size: 1.4rem; color: var(--page); pointer-events: none; opacity: 0; transition: opacity .15s; z-index: 6; transform: translateY(-50%); }
#bubble.on { opacity: 1; }
@media (max-width: 40rem) { main { padding-right: 3rem; } }
"""
newc = lambda i: i == 0 or decs[i][0] // 100 != decs[i-1][0] // 100
mx = max(n for _, n in decs)
ticks = "".join(f'<div class="tk{" c" if newc(i) else ""}" style="--n:{n / mx:.3f}" data-d="{d}" title="{d}s, {n} {"story" if n == 1 else "stories"}">' + (f'<span>{d // 100}00s</span>' if newc(i) else '') + '</div>' for i, (d, n) in enumerate(decs))
RAIL = f'''<nav id="rail" aria-label="Jump to decade">{ticks}</nav><div id="bubble"></div>
<script>
(() => {{
  const rail = document.getElementById("rail"), bub = document.getElementById("bubble");
  const tks = [...rail.querySelectorAll(".tk")];
  let dragging = false;
  function pick(y) {{
    const r = rail.getBoundingClientRect();
    const i = Math.max(0, Math.min(tks.length - 1, Math.floor((y - r.top) / r.height * tks.length)));
    const d = tks[i].dataset.d;
    document.getElementById("d" + d).scrollIntoView({{block: "start"}});
    bub.textContent = d + "s"; bub.style.top = y + "px"; bub.classList.add("on");
  }}
  rail.addEventListener("pointerdown", e => {{ dragging = true; rail.setPointerCapture(e.pointerId); pick(e.clientY); }});
  rail.addEventListener("pointermove", e => {{ if (dragging) pick(e.clientY); }});
  const end = () => {{ dragging = false; bub.classList.remove("on"); }};
  rail.addEventListener("pointerup", end); rail.addEventListener("pointercancel", end);
  const marks = tks.map(t => document.getElementById("d" + t.dataset.d));
  function mark() {{
    let k = 0; marks.forEach((m, i) => {{ if (m.getBoundingClientRect().top < innerHeight * .3) k = i; }});
    tks.forEach((t, i) => t.classList.toggle("cur", i === k));
  }}
  addEventListener("scroll", mark, {{passive: true}}); mark();
}})();
</script>
'''
page = HEAD.format(title="Walking the American Way: Time", layout="one vertical timeline grouped by century", maxw="40rem", extra=extra, h1="Time", nav=NAV("year"))
page += f'  <p class="kicker">{len(ms)} stories, {year_of(ms[0])} to {year_of(ms[-1])}</p>\n  <ol>\n' + "\n".join(rows) + "\n  </ol>\n</main>\n" + RAIL + "</body>\n</html>\n"
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
.pin { cursor: pointer; stroke: #111214; stroke-width: 1.2; vector-effect: non-scaling-stroke; outline: none; -webkit-tap-highlight-color: transparent; }
.land, .grat, .route { vector-effect: non-scaling-stroke; }
#map { cursor: grab; touch-action: none; }
#map:active { cursor: grabbing; }
.zoomer { display: flex; gap: .4rem; margin-top: .6rem; }
.zoomer button { font: inherit; font-family: var(--font-display); font-size: 1.1rem; min-width: 2.4rem; padding: .2rem .6rem; background: var(--ink-2); color: var(--page); border: 1px solid var(--rule); cursor: pointer; }
.zoomer button:hover { border-color: var(--page-dim); }
.pin:hover { stroke: #e6e1d6; stroke-width: 1.5; }
.pin.on { stroke: #e6e1d6; stroke-width: 1.2; }
#card { min-height: 6.5rem; margin-top: 1.25rem; padding: 1rem 1.25rem; border: 1px solid var(--rule); background: var(--ink-2); }
#card .t { font-family: var(--font-display); font-size: 1.6rem; color: var(--page); text-decoration: none; display: flex; align-items: center; gap: .6rem; }
#card .t:hover { text-decoration: underline; }
#card p { margin: .25rem 0 0; color: var(--page-dim); font-style: italic; font-size: .95rem; }
.hint { color: var(--page-dim); font-style: italic; font-size: .95rem; }
"""
page = HEAD.format(title="Walking the American Way: Place", layout="one full-width map of the continent, no borders drawn, a detail card below", maxw="62rem", extra=extra, h1="Place", nav=NAV("map"))
page += """  <svg id="map" viewBox="0 0 975 720" role="img" aria-label="Map of North America, without borders, with a point for each story"></svg>
  <div class="zoomer"><button id="zin" aria-label="Zoom in">+</button><button id="zout" aria-label="Zoom out">&minus;</button><button id="zreset">Reset</button></div>
  <div id="card"><p class="hint">Tap or hover a point to see the story set there. Drag to pan; pinch, scroll or use the buttons to zoom (the buttons zoom toward the chosen point).</p></div>
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
const world = svg.append("g");
world.append("path").attr("class", "grat").attr("d", path(d3.geoGraticule().step([10, 10])()));
world.append("path").attr("class", "land").attr("d", path(land));
const card = document.getElementById("card");
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
// Pins live outside the zoomed group and are repositioned on zoom, so their size never scales.
const touch = matchMedia("(hover: none)").matches;
const CSSR = touch ? 7 : 5.5;                       // pin radius in screen pixels
const R = () => CSSR * 975 / (svg.node().clientWidth || 975);
let T = d3.zoomIdentity;
function size() { g.selectAll(".pin").attr("r", function () { return this.classList.contains("on") ? R() * .6 : R(); }); }
function place() { g.selectAll(".pin").attr("cx", d => T.applyX(d.x)).attr("cy", d => T.applyY(d.y)); }
function show(p, el) {
  g.selectAll(".pin").classed("on", false); d3.select(el).classed("on", true).raise(); size();
  card.innerHTML = '<a class="t" href="' + p.f + '"><span class="dot" style="background:' + p.a + '"></span>' + esc(p.t) + '</a><p>' + esc(p.p) + ' &middot; ' + p.y + ' &middot; commentary ' + esc(p.n) + '</p>';
}
const g = svg.append("g");
PTS.sort((a, b) => a.lat - b.lat).forEach(p => {
  const xy = proj([p.lon, p.lat]); if (!xy) return;
  const c = g.append("circle").datum({x: xy[0], y: xy[1]}).attr("class", "pin").attr("fill", p.a)
    .attr("tabindex", 0).attr("role", "link").attr("aria-label", p.t + ", " + p.p + ", " + p.y);
  c.append("title").text(p.t + " - " + p.p + ", " + p.y);
  const el = c.node();
  el.addEventListener("mouseenter", () => show(p, el));
  el.addEventListener("focus", () => show(p, el));
  el.addEventListener("click", () => { if (el.classList.contains("on") && !touch) location.href = p.f; else show(p, el); });
  el.addEventListener("keydown", ev => { if (ev.key === "Enter") location.href = p.f; });
});
place(); size();
addEventListener("resize", size);
const zoom = d3.zoom().scaleExtent([1, 48]).translateExtent([[0, 0], [975, 720]])
  .on("zoom", ev => { T = ev.transform; world.attr("transform", T); place(); });
svg.call(zoom).on("dblclick.zoom", null);
const ease = () => svg.transition().duration(350);
const focusPt = () => { const o = g.select(".pin.on"); return o.empty() ? null : [T.applyX(o.datum().x), T.applyY(o.datum().y)]; };
document.getElementById("zin").onclick = () => { const f = focusPt(); f ? ease().call(zoom.scaleBy, 2, f) : ease().call(zoom.scaleBy, 2); };
document.getElementById("zout").onclick = () => { const f = focusPt(); f ? ease().call(zoom.scaleBy, .5, f) : ease().call(zoom.scaleBy, .5); };
document.getElementById("zreset").onclick = () => ease().call(zoom.transform, d3.zoomIdentity);
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
s = open(ip).read()
s2 = re.sub(r'<nav class="views">.*?</nav>', NAV("num"), s, count=1, flags=re.S)
if s2 != s: open(ip, "w").write(s2)
print("views:", len(ms), "timeline,", len(pts), "map points")

# ---------- "near you" picker ----------
NEAR = [[m["file"], round(m["lat"], 3), round(m["lon"], 3)] for m in metas if "lat" in m]
nj = open(os.path.join(HERE, "near.tpl.js")).read().replace("/*PTS*/[]", json.dumps(NEAR, separators=(",", ":")))
np_ = os.path.join(HERE, "near.js")
if not os.path.exists(np_) or open(np_).read() != nj: open(np_, "w").write(nj)
for f in ["index.html", "timeline.html", "map.html"]:
    fp = os.path.join(HERE, f); h = open(fp).read()
    if '<script src="near.js"></script>' not in h:
        open(fp, "w").write(h.replace("</body>", '<script src="near.js"></script>\n</body>', 1))

# ---------- offline downloads in the footer of the three views ----------
DL = ('<p class="dl">Read offline: <a href="https://chercherai.github.io/american-dhammapada/Walking-the-American-Way.epub" download>EPUB</a> (6.7 MB, for Play Books, Kindle and other e-readers) '
      '&middot; <a href="https://chercherai.github.io/american-dhammapada/Walking-the-American-Way.pdf" download>PDF</a> (13 MB, typeset at 6&times;9 in)</p>')
for f in ["index.html", "timeline.html", "map.html"]:
    fp = os.path.join(HERE, f); h = open(fp).read(); h0 = h
    h = re.sub(r'<p class="dl">.*?</p>', '', h, flags=re.S)
    if "<footer" in h: h = re.sub(r'</footer>', DL + '</footer>', h, count=1)
    else: h = h.replace("</main>", '<footer style="margin-top:3rem;font-size:.9rem;color:var(--page-dim)">' + DL + '</footer>\n</main>', 1)
    if '.dl a' not in h: h = h.replace("</style>", "footer .dl { margin-top: .6rem; } footer .dl a { text-decoration: underline; text-underline-offset: .2em; }\n</style>", 1)
    if h != h0: open(fp, "w").write(h)

# ---------- reader preferences script on every page ----------
import glob
TAG = '<script src="prefs.js"></script>'
for f in glob.glob(os.path.join(HERE, "*.html")):
    h = open(f).read()
    if TAG not in h and "</body>" in h:
        open(f, "w").write(h.replace("</body>", TAG + "\n</body>", 1))
