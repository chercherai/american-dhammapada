#!/usr/bin/env python3
"""Build an EPUB 3 (with NCX for older readers) of Walking the American Way."""
import glob, html, io, json, os, re, uuid, zipfile, datetime
import cairosvg
from lxml import etree, html as lhtml
from PIL import Image, ImageDraw, ImageFont

SRC, OUT = "/home/claude/series", "/home/claude/book"
CH = ["The Twin-Verses", "On Earnestness", "Thought", "Flowers", "The Fool", "The Wise Man", "The Venerable",
      "The Thousands", "Evil", "Punishment", "Old Age", "Self", "The World", "The Buddha", "Happiness",
      "Pleasure", "Anger", "Impurity", "The Just", "The Way", "Miscellaneous", "The Downward Course",
      "The Elephant", "Thirst", "The Bhikshu", "The Brahmana"]
metas = [json.load(open(p)) for p in glob.glob(f"{SRC}/meta/*.json")]
metas.sort(key=lambda m: [int(x) for x in m["num"].split(".")])
e = html.escape
BOOKID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "https://chercherai.github.io/american-dhammapada/"))

def xhtml(fragment):
    """Parse an HTML fragment and return well-formed XHTML (entities resolved)."""
    root = lhtml.fragment_fromstring(fragment, create_parent="div")
    for el in root.iter():
        if not isinstance(el.tag, str): continue
        for a in [a for a in el.attrib if a.startswith("aria-") and a != "aria-label" or a in ("style", "id", "tabindex", "role", "onclick")]:
            del el.attrib[a]
    s = etree.tostring(root, method="xml", encoding="unicode")
    return s[len("<div>"):-len("</div>")] if s.startswith("<div>") else s

F2S = {m["file"]: "s" + m["num"].replace(".", "-") + ".xhtml" for m in metas}
def clean(main):
    main = re.sub(r'href="([a-z0-9-]+\.html)(#[^"]*)?"', lambda x: f'href="{F2S[x.group(1)]}{x.group(2) or ""}"' if x.group(1) in F2S else 'href="https://chercherai.github.io/american-dhammapada/' + x.group(1) + (x.group(2) or "") + '"', main)
    s = re.sub(r"<script.*?</script>|<canvas.*?</canvas>|<style.*?</style>", "", main, flags=re.S)
    s = re.sub(r'<nav class="series">.*?</nav>', "", s, flags=re.S)
    s = re.sub(r'<div class="pager">.*?</div>', "", s, flags=re.S)
    s = re.sub(r'<details class="bg">\s*<summary>.*?</summary>', '<div class="bg"><h3 class="bgh">Background</h3>', s, flags=re.S)
    s = s.replace("</details>", "</div>")
    s = s.replace("<h1>", '<h1 class="st">')
    s = re.sub(r"<h2>(.*?)</h2>", r'<h2 class="sec">\1</h2>', s, flags=re.S)
    return s

files, manifest, spine, nav, ncx = {}, [], [], [], []

def page(title, body, cls=""):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head><meta charset="utf-8"/><title>{e(title)}</title><link rel="stylesheet" type="text/css" href="../css/book.css"/></head>
<body{f' class="{cls}"' if cls else ''}>
{body}
</body></html>'''

# ---- maps: svg -> png
def map_png(svg, name):
    svg = svg.replace("currentColor", "#3a3833")
    svg = re.sub(r'<svg [^>]*viewBox="0 0 320 200"[^>]*>', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 200" width="320" height="200">', svg, count=1)
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=640, output_height=400, background_color="#ffffff")
    im = Image.open(io.BytesIO(png)).convert("RGB").quantize(colors=32)
    b = io.BytesIO(); im.save(b, "PNG", optimize=True)
    files[f"OEBPS/images/{name}.png"] = b.getvalue()
    manifest.append(f'<item id="img-{name}" href="images/{name}.png" media-type="image/png"/>')

# ---- front matter
count = len(metas)
files["OEBPS/text/title.xhtml"] = page("Walking the American Way", f'''<div class="titlepage">
<h1 class="booktitle">Walking the American Way</h1>
<p class="sub">The stories behind the Dhammapada, set down again across five hundred years of American life</p>
<p class="by">{count} stories &#183; written by Claude Opus 5.5 and Claude Fable 5.2</p></div>'''.replace("&#183;", "·"), "front")
files["OEBPS/text/note.xhtml"] = page("A note on these stories", '''<h1 class="fronth">A note on these stories</h1>
<p>The Dhammapada is a collection of 423 short verses attributed to the Buddha. A commentary compiled in Sri Lanka in the fifth century tells, for each verse or group of verses, the story of the occasion on which it was spoken: 305 stories in all, of monks and lay people, merchants and kings, grieving mothers and foolish sons.</p>
<p>Each story in this book retells one of those commentary stories somewhere in American history, broadly drawn, from 1492 to the present and from Guam to Newfoundland. Each opens, as the old suttas do, with a version of “Thus have I heard” in the speech of its community. In place of the Buddha’s verse, a teacher speaks words from that community’s own tradition, quoted exactly from public-domain sources. Each story is followed by a Background with Max Müller’s 1881 translation of the verses, a short account of the original commentary story, a map, and notes on the history.</p>
<p>The stories are fiction, written by two AI models, Claude Opus 5.5 and Claude Fable 5.2, working from a shared house style. The history was checked against sources, and each Background says what is documented and what is invented; real public figures appear only at a distance. Errors surely remain.</p>
<p>The online edition, with a timeline and a map: chercherai.github.io/american-dhammapada</p>''', "front")
for f, t in [("title", "Title page"), ("note", "A note on these stories")]:
    manifest.append(f'<item id="{f}" href="text/{f}.xhtml" media-type="application/xhtml+xml"/>')
    spine.append(f'<itemref idref="{f}"/>')
spine.insert(0, '<itemref idref="cover"/>')
nav.append('<li><a href="text/note.xhtml">A note on these stories</a></li>')

order = 0
def ncx_point(label, href, children=""):
    global order; order += 1
    return f'<navPoint id="np{order}" playOrder="{order}"><navLabel><text>{e(label)}</text></navLabel><content src="{href}"/>{children}</navPoint>'
ncx.append(ncx_point("A note on these stories", "text/note.xhtml"))

cur, ch_nav, ch_ncx = None, [], []
def close_chapter():
    if cur is None: return
    c = cur
    nav.append(f'<li><a href="text/ch{c:02d}.xhtml">{c}. {e(CH[c-1])}</a><ol>{"".join(ch_nav)}</ol></li>')
    ncx.append(ncx_point(f"{c}. {CH[c-1]}", f"text/ch{c:02d}.xhtml", "".join(ch_ncx)))

for m in metas:
    c = int(m["num"].split(".")[0])
    if c != cur:
        close_chapter(); cur = c; ch_nav, ch_ncx = [], []
        files[f"OEBPS/text/ch{c:02d}.xhtml"] = page(CH[c-1], f'<div class="chapter"><p class="chn">Chapter {c}</p><h1 class="cht">{e(CH[c-1])}</h1></div>', "chap")
        manifest.append(f'<item id="ch{c:02d}" href="text/ch{c:02d}.xhtml" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="ch{c:02d}"/>')
    h = open(f"{SRC}/{m['file']}").read()
    main = clean(re.search(r"<main[^>]*>(.*)</main>", h, re.S).group(1))
    sid = "s" + m["num"].replace(".", "-")
    svg = re.search(r'<svg.*?</svg>', main, re.S)
    if svg:
        map_png(svg.group(0), sid)
        main = main.replace(svg.group(0), f'<img src="../images/{sid}.png" alt="Map: {e(m["place"])}"/>')
    title = html.unescape(re.sub("<.*?>", "", re.search(r"<h1[^>]*>(.*?)</h1>", main, re.S).group(1))).strip()
    body = f'<p class="snum">{e(m["num"])}</p>' + xhtml(main)
    files[f"OEBPS/text/{sid}.xhtml"] = page(title, body, "story")
    manifest.append(f'<item id="{sid}" href="text/{sid}.xhtml" media-type="application/xhtml+xml"/>')
    spine.append(f'<itemref idref="{sid}"/>')
    ch_nav.append(f'<li><a href="text/{sid}.xhtml">{e(m["num"])} {e(title)}</a></li>')
    ch_ncx.append(ncx_point(f'{m["num"]} {title}', f"text/{sid}.xhtml"))
close_chapter()

# ---- cover
W, H = 1600, 2560
im = Image.new("RGB", (W, H), "#16181a"); d = ImageDraw.Draw(im)
fell = f"{OUT}/fonts/IMFeENrm28P.ttf"; felli = f"{OUT}/fonts/IMFeENit28P.ttf"
def center(y, text, font, fill):
    w = d.textlength(text, font=font); d.text(((W - w) / 2, y), text, font=font, fill=fill)
d.rectangle([90, 90, W - 90, H - 90], outline="#c9a24a", width=3)
center(820, "Walking the", ImageFont.truetype(fell, 170), "#ece4d0")
center(1010, "American Way", ImageFont.truetype(fell, 170), "#ece4d0")
center(1330, "The stories behind the Dhammapada,", ImageFont.truetype(felli, 64), "#b9ae97")
center(1415, "across five hundred years of American life", ImageFont.truetype(felli, 64), "#b9ae97")
d.ellipse([W/2 - 14, 1640, W/2 + 14, 1668], fill="#c9a24a")
center(2200, "Claude Opus 5.5 · Claude Fable 5.2", ImageFont.truetype(felli, 58), "#8f8672")
b = io.BytesIO(); im.save(b, "JPEG", quality=88); files["OEBPS/images/cover.jpg"] = b.getvalue()
files["OEBPS/text/cover.xhtml"] = page("Cover", '<div class="cover"><img src="../images/cover.jpg" alt="Walking the American Way"/></div>', "coverpage")
manifest[:0] = ['<item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
                '<item id="cover" href="text/cover.xhtml" media-type="application/xhtml+xml"/>']

# ---- fonts and css
fonts = ["IMFeENrm28P.ttf", "IMFeENit28P.ttf", "Spectral-Light.ttf", "Spectral-LightItalic.ttf", "Spectral-SemiBold.ttf"]
for f in fonts:
    files[f"OEBPS/fonts/{f}"] = open(f"{OUT}/fonts/{f}", "rb").read()
    manifest.append(f'<item id="font-{f.split(".")[0]}" href="fonts/{f}" media-type="font/ttf"/>')
files["OEBPS/css/book.css"] = """
@font-face { font-family: "Fell"; src: url(../fonts/IMFeENrm28P.ttf); }
@font-face { font-family: "Fell"; font-style: italic; src: url(../fonts/IMFeENit28P.ttf); }
@font-face { font-family: "Spectral"; font-weight: normal; src: url(../fonts/Spectral-Light.ttf); }
@font-face { font-family: "Spectral"; font-weight: normal; font-style: italic; src: url(../fonts/Spectral-LightItalic.ttf); }
@font-face { font-family: "Spectral"; font-weight: bold; src: url(../fonts/Spectral-SemiBold.ttf); }
body { font-family: "Spectral", Georgia, serif; line-height: 1.5; margin: 0 4%; }
p { margin: 0; text-indent: 1.2em; text-align: justify; orphans: 2; widows: 2; }
a { color: inherit; text-decoration: none; }
h1, h2, h3 { font-family: "Fell", Georgia, serif; font-weight: normal; text-align: left; page-break-after: avoid; }
.cover { text-align: center; margin: 0; padding: 0; } .cover img { max-width: 100%; max-height: 100%; }
.titlepage { text-align: center; margin-top: 30%; }
.booktitle { font-size: 2.3em; text-align: center; line-height: 1.1; }
.titlepage p { text-indent: 0; text-align: center; font-family: "Fell", Georgia, serif; font-style: italic; margin-top: 1em; }
.titlepage .by { font-family: "Spectral", Georgia, serif; font-style: normal; font-size: .8em; margin-top: 4em; opacity: .75; }
.fronth { font-size: 1.5em; margin: 1.5em 0 1em; }
.front p { text-indent: 0; margin-bottom: .7em; }
.chapter { text-align: center; margin-top: 35%; }
.chn { text-indent: 0; text-align: center; font-family: "Fell", Georgia, serif; font-style: italic; opacity: .7; }
.cht { font-size: 2.1em; text-align: center; margin-top: .2em; }
.snum { text-indent: 0; font-family: "Fell", Georgia, serif; font-style: italic; opacity: .6; margin-top: 2em; }
h1.st { font-size: 2em; line-height: 1.1; margin: .2em 0 .6em; }
.epigraph { font-style: italic; font-size: .9em; margin: 0 0 1.4em 18%; opacity: .85; }
.heard { text-indent: 0; font-family: "Fell", Georgia, serif; font-style: italic; margin: .6em 0 1.6em; }
h2.sec { font-size: 1.3em; margin: 1.8em 0 .1em; }
.dateline { text-indent: 0; font-family: "Fell", Georgia, serif; font-style: italic; font-size: .85em; opacity: .7; margin-bottom: .8em; }
.dateline + p, h2 + p, .brk + p, .verse + p, blockquote + p, div + p { text-indent: 0; }
.dateline + p:first-line { font-variant: small-caps; letter-spacing: .03em; }
p[class] { text-indent: 0; }
.brk { text-align: center; margin: .9em 0; letter-spacing: .3em; opacity: .6; text-indent: 0; }
.verse, blockquote { margin: 1em 5%; font-style: italic; }
.verse p, blockquote p { text-indent: 0; text-align: left; margin-bottom: .4em; }
cite { display: block; font-style: normal; font-size: .82em; opacity: .7; margin-top: .3em; }
div.doc, div.log, div.note, div.entry, div.song, div.leaf, div.tally, div.dep, div.day, div.form { margin: .9em 0 .9em 2%; padding-left: .8em; border-left: 1px solid #999; }
div.slate { text-align: center; border: 1px solid #999; padding: .8em; margin: 1em 15%; font-family: "Fell", Georgia, serif; letter-spacing: .08em; }
div.slate p { text-align: center; }
span.dt, span.t, span.who, span.entry { font-variant: small-caps; letter-spacing: .03em; margin-right: .45em; }
span.hd { display: block; font-variant: small-caps; letter-spacing: .04em; }
span.sm, span.mid, span.big { display: block; text-align: center; }
span.big { font-family: "Fell", Georgia, serif; font-size: 1.25em; }
span.cite { display: block; font-size: .85em; opacity: .7; }
span.q { display: block; font-style: italic; }
span.fee { margin-left: .5em; }
footer { margin-top: 2em; font-size: .8em; opacity: .75; }
.bg { margin-top: 2.2em; padding-top: .8em; border-top: 1px solid #aaa; font-size: .9em; }
.bg h3 { font-size: 1.1em; margin: 1em 0 .3em; }
.bg h3.bgh { font-style: italic; font-size: 1.25em; margin-top: 0; }
.bg p { text-indent: 0; margin-bottom: .5em; }
figure.locmap { margin: 1em 0; } figure.locmap img { width: 100%; max-width: 320px; }
figcaption { font-size: .8em; font-style: italic; opacity: .7; }
nav ol { list-style: none; padding-left: 0; } nav ol ol { padding-left: 1.2em; font-size: .92em; }
""".encode()
manifest.append('<item id="css" href="css/book.css" media-type="text/css"/>')

# ---- nav and ncx
files["OEBPS/nav.xhtml"] = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head><meta charset="utf-8"/><title>Contents</title><link rel="stylesheet" type="text/css" href="css/book.css"/></head>
<body><nav epub:type="toc" id="toc"><h1 class="fronth">Contents</h1><ol>{"".join(nav)}</ol></nav>
<nav epub:type="landmarks" hidden="hidden"><ol><li><a epub:type="cover" href="text/cover.xhtml">Cover</a></li>
<li><a epub:type="toc" href="nav.xhtml">Contents</a></li><li><a epub:type="bodymatter" href="text/ch01.xhtml">Stories</a></li></ol></nav></body></html>'''
manifest.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
spine.insert(3, '<itemref idref="nav"/>')
files["OEBPS/toc.ncx"] = f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="{BOOKID}"/></head>
<docTitle><text>Walking the American Way</text></docTitle><navMap>{"".join(ncx)}</navMap></ncx>'''
manifest.append('<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')

now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
files["OEBPS/content.opf"] = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="en">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{BOOKID}</dc:identifier><dc:title>Walking the American Way</dc:title>
<dc:creator>Claude Opus 5.5</dc:creator><dc:creator>Claude Fable 5.2</dc:creator><dc:language>en</dc:language>
<dc:description>All 305 Dhammapada commentary stories, retold across five hundred years of American life.</dc:description>
<meta property="dcterms:modified">{now}</meta><meta name="cover" content="cover-image"/></metadata>
<manifest>{"".join(manifest)}</manifest>
<spine toc="ncx">{"".join(spine)}</spine>
<guide><reference type="cover" title="Cover" href="text/cover.xhtml"/><reference type="toc" title="Contents" href="nav.xhtml"/></guide>
</package>'''
files["META-INF/container.xml"] = '''<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>
<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'''

out = f"{OUT}/Walking-the-American-Way.epub"
with zipfile.ZipFile(out, "w") as z:
    z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
    for k, v in files.items():
        z.writestr(k, v if isinstance(v, bytes) else v.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)
print(out, os.path.getsize(out) // 1024, "KB,", count, "stories")
