#!/usr/bin/env python3
"""Typeset all stories of Walking the American Way as one book-style HTML for WeasyPrint."""
import glob, html, json, os, re, sys

SRC = "/home/claude/series"
OUT = "/home/claude/book"
CH = ["The Twin-Verses", "On Earnestness", "Thought", "Flowers", "The Fool", "The Wise Man", "The Venerable",
      "The Thousands", "Evil", "Punishment", "Old Age", "Self", "The World", "The Buddha", "Happiness",
      "Pleasure", "Anger", "Impurity", "The Just", "The Way", "Miscellaneous", "The Downward Course",
      "The Elephant", "Thirst", "The Bhikshu", "The Brahmana"]

metas = [json.load(open(p)) for p in glob.glob(f"{SRC}/meta/*.json")]
metas.sort(key=lambda m: [int(x) for x in m["num"].split(".")])
only = sys.argv[1] if len(sys.argv) > 1 else None          # e.g. "1" to build chapter 1 only
if only: metas = [m for m in metas if m["num"].split(".")[0] == only]
e = html.escape

def clean(main, m):
    s = re.sub(r"<script.*?</script>|<canvas.*?</canvas>|<style.*?</style>", "", main, flags=re.S)
    s = re.sub(r'<nav class="series">.*?</nav>', "", s, flags=re.S)
    s = re.sub(r'<div class="pager">.*?</div>', "", s, flags=re.S)
    s = re.sub(r'\sstyle="[^"]*"', "", s)                           # drop inline styles from the web pages
    s = re.sub(r'\sid="[^"]*"', "", s)
    # Background: <details> becomes an always-open block
    s = re.sub(r'<details class="bg">\s*<summary>.*?</summary>', '<div class="bg"><h3 class="bgh">Background</h3>', s, flags=re.S)
    s = s.replace("</details>", "</div>")
    # headings inside a story drop a level so the book's h1/h2 stay for chapters/stories
    s = s.replace("<h1>", '<h2 class="st">').replace("</h1>", "</h2>")
    s = re.sub(r"<h2>(.*?)</h2>", r'<h3 class="sec">\1</h3>', s, flags=re.S)
    s = re.sub(r"<header>", '<header class="sthead">', s, count=1)
    # the map: make sure the svg has an explicit width for print
    s = s.replace('<svg viewBox="0 0 320 200" width="320" height="320"', '<svg viewBox="0 0 320 200"')
    return s

parts, toc, cur = [], [], None
for m in metas:
    c = int(m["num"].split(".")[0])
    if c != cur:
        cur = c
        parts.append(f'<section class="chapter" id="ch{c}"><p class="chn">Chapter {c}</p><h1>{e(CH[c-1])}</h1></section>')
        toc.append(f'<li class="tch"><a href="#ch{c}"><span>{c}. {e(CH[c-1])}</span></a></li>')
    h = open(f"{SRC}/{m['file']}").read()
    main = re.search(r"<main[^>]*>(.*)</main>", h, re.S).group(1)
    sid = "s" + m["num"].replace(".", "-")
    title = re.search(r"<h1>(.*?)</h1>", main, re.S).group(1)
    parts.append(f'<article class="story" id="{sid}" data-title="{e(html.unescape(re.sub("<.*?>", "", title)))}">'
                 f'<p class="snum">{e(m["num"])}</p>{clean(main, m)}</article>')
    toc.append(f'<li><a href="#{sid}"><span class="n">{e(m["num"])}</span><span class="t">{title}</span></a></li>')

F = f"file://{OUT}/fonts"
css = f"""
@font-face {{ font-family: Fell; src: url({F}/IMFeENrm28P.ttf); }}
@font-face {{ font-family: Fell; font-style: italic; src: url({F}/IMFeENit28P.ttf); }}
@font-face {{ font-family: Spectral; font-weight: 300; src: url({F}/Spectral-Light.ttf); }}
@font-face {{ font-family: Spectral; font-weight: 300; font-style: italic; src: url({F}/Spectral-LightItalic.ttf); }}
@font-face {{ font-family: Spectral; font-weight: 400; src: url({F}/Spectral-Regular.ttf); }}
@font-face {{ font-family: Spectral; font-weight: 400; font-style: italic; src: url({F}/Spectral-Italic.ttf); }}
@font-face {{ font-family: Spectral; font-weight: 600; src: url({F}/Spectral-SemiBold.ttf); }}

@page {{ size: 6in 9in; margin: .8in .65in .85in .75in;
  @bottom-center {{ content: counter(page); font: 300 8.5pt Spectral; color: #555; }} }}
@page :left {{ margin-left: .65in; margin-right: .75in;
  @top-left {{ content: "Walking the American Way"; font: italic 8.5pt Fell; color: #666; }} }}
@page :right {{ @top-right {{ content: string(story); font: italic 8.5pt Fell; color: #666; }} }}
@page front {{ @top-left {{ content: none; }} @top-right {{ content: none; }} @bottom-center {{ content: none; }} }}
@page chap {{ @top-left {{ content: none; }} @top-right {{ content: none; }} @bottom-center {{ content: none; }} }}
@page :blank {{ @top-left {{ content: none; }} @top-right {{ content: none; }} @bottom-center {{ content: none; }} }}

html {{ font: 300 10.4pt/1.47 Spectral; color: #1b1a17; hyphens: auto; }}
body {{ margin: 0; }}
a {{ color: inherit; text-decoration: none; }}
em, i {{ font-style: italic; }}
p {{ margin: 0; text-align: justify; text-indent: 1.15em; orphans: 2; widows: 2; }}

.front {{ page: front; }}
.titlepage {{ page: front; height: 7.2in; display: flex; flex-direction: column; justify-content: center; text-align: center; break-after: page; }}
.titlepage h1 {{ font: 400 34pt/1.05 Fell; margin: 0 0 .25in; }}
.titlepage .sub {{ font: italic 12.5pt/1.4 Fell; color: #444; text-indent: 0; text-align: center; }}
.titlepage .by {{ margin-top: 1.2in; font: 300 9.5pt/1.5 Spectral; color: #555; text-indent: 0; text-align: center; }}
.note {{ page: front; break-after: page; }}
.note h2 {{ font: 400 17pt Fell; margin: .6in 0 .25in; }}
.note p {{ margin-bottom: .6em; text-indent: 0; }}
.contents {{ page: front; break-after: right; }}
.contents h2 {{ font: 400 17pt Fell; margin: .3in 0 .2in; }}
.contents ol {{ list-style: none; margin: 0; padding: 0; font-size: 9pt; line-height: 1.38; }}
.contents li.tch {{ font: italic 10.5pt Fell; margin: .65em 0 .2em; break-after: avoid; }}
.contents li a {{ display: table; width: 100%; }}
.contents li .n {{ display: table-cell; width: 2.6em; color: #777; font-variant-numeric: tabular-nums; }}
.contents li .t {{ display: table-cell; }}
.contents li a::after {{ content: target-counter(attr(href), page); display: table-cell; width: 3em; text-align: right; color: #555; font-variant-numeric: tabular-nums; }}

.chapter {{ page: chap; break-before: right; break-after: page; height: 7.2in; display: flex; flex-direction: column; justify-content: center; text-align: center; }}
.chapter .chn {{ font: italic 12pt Fell; color: #666; text-indent: 0; text-align: center; margin-bottom: .1in; }}
.chapter h1 {{ font: 400 30pt/1.1 Fell; margin: 0; bookmark-level: 1; }}
h2.st {{ bookmark-level: 2; }}
h3, .note h2, .contents h2, .titlepage h1 {{ bookmark-level: none; }}

.story {{ break-before: right; }}
.story .snum {{ font: italic 9.5pt Fell; color: #777; text-indent: 0; margin-top: .55in; }}
h2.st {{ string-set: story content(text); font: 400 25pt/1.08 Fell; margin: .05in 0 .2in; text-align: left; }}
.epigraph {{ font: italic 9.6pt/1.45 Spectral; color: #444; margin: 0 0 .28in 1.1in; text-align: left; }}
.heard {{ font: italic 11pt Fell; text-indent: 0; margin: .1in 0 .3in; text-align: left; }}
.heard-lead {{ font-style: italic; }}
section {{ margin: 0; }}
h3.sec {{ font: 400 14pt/1.2 Fell; margin: .32in 0 .04in; break-after: avoid; text-align: left; }}
.dateline {{ font: italic 9pt Fell; color: #666; text-indent: 0; margin-bottom: .14in; break-after: avoid; text-align: left; }}
section > .dateline + p {{ text-indent: 0; }}
section > .dateline + p::first-line {{ font-variant: small-caps; letter-spacing: .035em; }}
h3.sec + p, .brk + p, .verse + p, blockquote + p, div[class] + p {{ text-indent: 0; }}
p[class] {{ text-indent: 0; }}
.brk {{ text-align: center; margin: .14in 0; color: #777; text-indent: 0; letter-spacing: .3em; }}
.verse, blockquote {{ margin: .16in .25in .16in .25in; font-style: italic; line-height: 1.45; break-inside: avoid; }}
.verse p, blockquote p {{ text-indent: 0; margin-bottom: .35em; text-align: left; }}
cite {{ display: block; font: normal 8.3pt Spectral; color: #666; margin-top: .3em; font-style: normal; }}
div.doc, div.log, div.slate, div.note, div.entry, div.song, div.leaf, div.tally, div.dep, div.day, div.form {{
  margin: .14in 0 .14in .1in; padding: .02in 0 .02in .14in; border-left: .6pt solid #999; }}
div.slate {{ text-align: center; border: .6pt solid #999; padding: .12in; margin: .16in .6in; font: 400 13pt Fell; letter-spacing: .08em; }}
div.slate p {{ text-align: center; }}
span.dt, span.t, span.who, span.entry {{ font-variant: small-caps; letter-spacing: .03em; margin-right: .45em; }}
span.hd {{ display: block; font-variant: small-caps; letter-spacing: .04em; margin-bottom: .1em; }}
span.sm, span.mid, span.big {{ display: block; text-align: center; }}
span.big {{ font: 400 13pt Fell; letter-spacing: .05em; }}
span.sm {{ font-size: 8.6pt; font-style: italic; }}
span.cite {{ display: block; font-size: 8.4pt; color: #666; font-style: normal; margin-top: .2em; }}
span.q {{ display: block; font-style: italic; }}
span.fee {{ margin-left: .5em; font-variant-numeric: tabular-nums; }}
.log, .entry, .day, .form {{ text-indent: 0; }}
p + p.log, p + p.entry {{ margin-top: .45em; }}
footer {{ margin-top: .3in; font-size: 8.2pt; color: #555; text-indent: 0; }}
footer p {{ text-indent: 0; }}

.bg {{ margin-top: .32in; padding-top: .12in; border-top: .5pt solid #aaa; font-size: 9pt; line-height: 1.42; }}
.bg h3 {{ font: 400 11pt Fell; margin: .14in 0 .06in; break-after: avoid; }}
.bg h3.bgh {{ font: italic 12.5pt Fell; margin-top: 0; }}
.bg p {{ text-indent: 0; margin-bottom: .45em; }}
.bg blockquote {{ margin: .08in .2in; font-size: 9pt; }}
figure.locmap {{ margin: .12in 0 .14in; width: 2.6in; break-inside: avoid; color: #1b1a17; }}
figure.locmap svg {{ width: 2.6in; height: auto; display: block; }}
figure.locmap figcaption {{ font: italic 7.8pt Spectral; color: #666; margin-top: .04in; }}
"""

count = len(metas)
doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Walking the American Way</title>
<meta name="author" content="Claude Opus 5.5 and Claude Fable 5.2"><style>{css}</style></head><body>
<div class="titlepage"><h1>Walking the<br>American Way</h1>
<p class="sub">The stories behind the Dhammapada,<br>set down again across five hundred years of American life</p>
<p class="by">{count} stories &middot; written by Claude Opus 5.5 and Claude Fable 5.2</p></div>
<div class="note"><h2>A note on these stories</h2>
<p>The Dhammapada is a collection of 423 short verses attributed to the Buddha. A commentary compiled in Sri Lanka in the fifth century tells, for each verse or group of verses, the story of the occasion on which it was spoken: 305 stories in all, of monks and lay people, merchants and kings, grieving mothers and foolish sons.</p>
<p>Each story in this book retells one of those commentary stories somewhere in American history, broadly drawn, from 1492 to the present and from Guam to Newfoundland. Each opens, as the old suttas do, with a version of &ldquo;Thus have I heard&rdquo; in the speech of its community. In place of the Buddha&rsquo;s verse, a teacher speaks words from that community&rsquo;s own tradition, quoted exactly from public-domain sources. Each story is followed by a Background with Max M&uuml;ller&rsquo;s 1881 translation of the verses, a short account of the original commentary story, a map, and notes on the history.</p>
<p>The stories are fiction, written by two AI models, Claude Opus 5.5 and Claude Fable 5.2, working from a shared house style. The history was checked against sources, and each Background says what is documented and what is invented; real public figures appear only at a distance. Errors surely remain.</p>
<p>The online edition, with a timeline and a map: chercherai.github.io/american-dhammapada</p></div>
<div class="contents"><h2>Contents</h2><ol>{''.join(toc)}</ol></div>
{''.join(parts)}
</body></html>"""
name = f"{OUT}/book{'-ch'+only if only else ''}.html"
open(name, "w").write(doc)
print(name, count, "stories")
