"""Word count and reading time for a story page (story text only: no Background, footer or nav)."""
import re, html, math
WPM = 230
def count(page):
    m = re.search(r"<main[^>]*>(.*)</main>", page, re.S)
    s = m.group(1) if m else page
    s = re.sub(r"<script.*?</script>|<style.*?</style>|<nav.*?</nav>|<details.*?</details>|<footer.*?</footer>|<figure.*?</figure>", " ", s, flags=re.S)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return len(re.findall(r"[\w’'’-]+", s))
def minutes(n): return max(1, math.ceil(n / WPM))
def label(n): return f"{n:,} words &middot; {minutes(n)} min"
