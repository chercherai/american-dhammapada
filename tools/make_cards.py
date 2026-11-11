#!/usr/bin/env python3
"""Social cards (1200x630) for each story: title, place and year, logline, and the locator map.
Writes og/<num>.png and a posts.json the Bluesky poster reads."""
import glob, html, io, json, os, re, textwrap
import cairosvg
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/home/claude/book/fonts"
MAPS = json.load(open("/home/claude/maptool/maps.json"))
SITE = "https://chercherai.github.io/american-dhammapada/"
os.makedirs(os.path.join(HERE, "og"), exist_ok=True)
fell = lambda s: ImageFont.truetype(f"{FONTS}/IMFeENrm28P.ttf", s)
felli = lambda s: ImageFont.truetype(f"{FONTS}/IMFeENit28P.ttf", s)
spec = lambda s: ImageFont.truetype(f"{FONTS}/Spectral-Light.ttf", s)
BG, INK, DIM, GOLD = "#16181a", "#ece4d0", "#a59c88", "#c9a24a"

def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

posts = []
metas = sorted((json.load(open(p)) for p in glob.glob(os.path.join(HERE, "meta", "*.json"))),
               key=lambda m: [int(x) for x in m["num"].split(".")])
for m in metas:
    slug = m["num"].replace(".", "-")
    out = os.path.join(HERE, "og", f"{slug}.png")
    page = open(os.path.join(HERE, m["file"])).read()
    secs = []
    for i, sec in enumerate(re.findall(r'<section[^>]*>(.*?)</section>', page, re.S), 1):
        hm = re.search(r'<h2>(.*?)</h2>', sec, re.S)
        paras = [html.unescape(re.sub(r'<[^>]+>', '', x)).strip() for x in re.findall(r'<p(?: class="(?!dateline)[^"]*")?>(.*?)</p>', sec, re.S)]
        dm = re.search(r'<p class="dateline">(.*?)</p>', sec, re.S)
        secs.append({"heading": html.unescape(re.sub(r'<[^>]+>', '', hm.group(1))).strip() if hm else "",
                     "dateline": html.unescape(re.sub(r'<[^>]+>', '', dm.group(1))).strip() if dm else "",
                     "text": " ".join(x for x in paras if x)[:1200], "anchor": f"#part-{i}"})
    posts.append({"sections": secs, "num": m["num"], "title": m["title"], "place": m["place"], "year": str(m["year"]),
                  "logline": m.get("logline", ""), "url": SITE + m["file"], "image": SITE + f"og/{slug}.png"})
    im = Image.new("RGB", (1200, 630), BG); d = ImageDraw.Draw(im)
    d.rectangle([24, 24, 1176, 606], outline="#3a3a36", width=2)
    # map on the right
    svg = MAPS.get(m["file"])
    if svg:
        s = svg.replace("currentColor", INK)
        s = re.sub(r"<svg [^>]*>", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 200" width="320" height="200">', s, count=1)
        png = cairosvg.svg2png(bytestring=s.encode(), output_width=480, output_height=300)
        mp = Image.open(io.BytesIO(png)).convert("RGBA")
        im.paste(mp, (676, 165), mp)
    # text on the left
    x, w = 64, 580
    d.text((x, 62), "Walking the American Way", font=felli(30), fill=DIM)
    d.text((x + w - d.textlength(m["num"], font=felli(30)), 62), m["num"], font=felli(30), fill=DIM)
    size = 76
    while True:
        tl = wrap(d, m["title"], fell(size), w)
        if len(tl) <= 2 or size <= 50: break
        size -= 4
    y = 130
    for line in tl:
        d.text((x, y), line, font=fell(size), fill=INK); y += int(size * 1.08)
    y += 14
    d.text((x, y), f"{m['place']}, {m['year']}"[:70], font=felli(30), fill=GOLD); y += 58
    for line in wrap(d, m.get("logline", ""), spec(27), w)[:6]:
        d.text((x, y), line, font=spec(27), fill=INK); y += 38
    d.text((676 + 240 - d.textlength("chercherai.github.io/american-dhammapada", font=spec(20)) / 2, 520),
           "chercherai.github.io/american-dhammapada", font=spec(20), fill=DIM)
    im.save(out, optimize=True)

json.dump(posts, open(os.path.join(HERE, "posts.json"), "w"), ensure_ascii=False, indent=0)
print(len(posts), "cards")
