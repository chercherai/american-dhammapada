// Render a small locator map (SVG string) for each story: land from Natural Earth 50m
// (via world-atlas), lakes cut out, a dot at the story's place. Output: maps.json {file: svg}.
import fs from "fs";
import * as d3 from "d3-geo";
import * as topo from "topojson-client";

const W = 320, H = 200, RADIUS_DEG = 9;     // about 1,000 km either side
const landT = JSON.parse(fs.readFileSync("node_modules/world-atlas/land-50m.json"));
const land = topo.feature(landT, landT.objects.land);
const lakes = JSON.parse(fs.readFileSync("lakes50.geojson"));
lakes.features = lakes.features.filter(f => (f.properties.scalerank ?? 9) <= 2);
const rivers = JSON.parse(fs.readFileSync("rivers50.geojson"));
rivers.features = rivers.features.filter(f => (f.properties.scalerank ?? 9) <= 5 && f.properties.featurecla !== "Lake Centerline");

const metaDir = process.argv[2];
const out = {};
for (const f of fs.readdirSync(metaDir)) {
  const m = JSON.parse(fs.readFileSync(`${metaDir}/${f}`));
  if (!isFinite(m.lat) || !isFinite(m.lon)) continue;
  const proj = d3.geoAzimuthalEqualArea().rotate([-m.lon, -m.lat]).clipAngle(RADIUS_DEG * 1.6)
    .scale(1).translate([0, 0]);
  // scale so RADIUS_DEG spans the half-width
  const edge = proj([m.lon + RADIUS_DEG / Math.cos(m.lat * Math.PI / 180), m.lat]);
  proj.scale((W / 2) / Math.abs(edge[0])).translate([W / 2, H / 2])
    .clipExtent([[0, 0], [W, H]]);
  const path = d3.geoPath(proj).digits(1);
  const L = path(land) || "", K = path(lakes) || "", R = path(rivers) || "";
  const xy = proj([m.lon, m.lat]);
  const acc = m.accent || "currentColor";
  out[m.file] = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Map showing where the story is set: ${m.place.replace(/"/g, "&quot;")}">` +
    `<rect width="${W}" height="${H}" fill="currentColor" fill-opacity=".04"/>` +
    `<path d="${L}${K}" fill="currentColor" fill-opacity=".13" fill-rule="evenodd" stroke="currentColor" stroke-opacity=".38" stroke-width=".6"/>` +
    (R ? `<path d="${R}" fill="none" stroke="currentColor" stroke-opacity=".32" stroke-width=".8" stroke-linejoin="round"/>` : "") +
    `<circle cx="${xy[0].toFixed(1)}" cy="${xy[1].toFixed(1)}" r="11" fill="${acc}" fill-opacity=".22"/>` +
    `<circle cx="${xy[0].toFixed(1)}" cy="${xy[1].toFixed(1)}" r="4.5" fill="${acc}" stroke="currentColor" stroke-opacity=".7" stroke-width="1"/>` +
    `</svg>`;
}
fs.writeFileSync("maps.json", JSON.stringify(out));
const sizes = Object.values(out).map(s => s.length).sort((a, b) => a - b);
console.log(Object.keys(out).length, "maps; median", sizes[sizes.length >> 1], "max", sizes[sizes.length - 1]);
