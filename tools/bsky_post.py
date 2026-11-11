#!/usr/bin/env python3
"""Post today's story from Walking the American Way to Bluesky.

Order: all 305 stories in a shuffled order, one a day from START, reshuffled each
time the cycle completes, so the sequence needs no saved state. Safe to re-run:
if today's story is already among the account's recent posts it does nothing.

Usage: BSKY_HANDLE=usdhp.bsky.social BSKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx python3 bsky_post.py [--dry-run] [--date YYYY-MM-DD]
"""
import datetime, json, os, random, sys, urllib.request, urllib.error
from zoneinfo import ZoneInfo

SITE = "https://chercherai.github.io/american-dhammapada/"
PDS = "https://bsky.social/xrpc/"
START = datetime.date(2026, 11, 11)
TZ = ZoneInfo("America/Winnipeg")

def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} from {url}: {e.read().decode(errors='replace')[:400]}")

def xrpc(method, body=None, token=None, raw=None, ctype="application/json"):
    h = {"Content-Type": ctype}
    if token: h["Authorization"] = "Bearer " + token
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    return json.loads(http(PDS + method, data, h, "POST" if data is not None else "GET"))

import re

def fit(text, budget):
    """As many whole sentences as fit; if that's too little, fill and cut at a word."""
    if len(text) <= budget: return text
    body = ""
    for x in re.split(r'(?<=[.!?\u201d\u2019])\s+', text):
        if len(body) + len(x) + 1 > budget - 2: break
        body = (body + " " + x).strip()
    if len(body) < budget * 0.6:
        body = text[:budget - 1].rsplit(" ", 1)[0].rstrip(",;:") + "\u2026"
    else:
        body += " \u2026"
    return body

def compose(head, text, label, uri):
    budget = 296 - len(head) - len("\n\n") - len("\n\n" + label)
    t = f"{head}\n\n{fit(text, budget)}\n\n{label}"
    start = len(t.encode()) - len(label.encode())
    return t, [{"index": {"byteStart": start, "byteEnd": len(t.encode())},
                "features": [{"$type": "app.bsky.richtext.facet#link", "uri": uri}]}]

def section_post(sec, url):
    head = sec["heading"] + ("\n" + sec["dateline"] if sec.get("dateline") else "")
    return compose(head, sec["text"], "Read this part \u2192", url + sec["anchor"])

def background_posts(bg, url):
    """Two closing replies: the verse with the commentary story, then the history."""
    out = []
    if bg.get("verse"):
        verse = "\u201c" + fit(bg["verse"], 170) + "\u201d"
        head = f"The verse \u00b7 {bg.get('cite', 'Dhammapada')}\n{verse}"
        out.append(compose(head, bg.get("commentary", ""), "The verse and the old story \u2192", url + "#background"))
    if bg.get("history"):
        out.append(compose(bg.get("hist_title", "Background"), bg["history"], "Historical background \u2192", url + "#history"))
    return out

def story_for(day, posts):
    n = (day - START).days
    if n < 0: sys.exit(f"Posting starts {START}")
    cycle, i = divmod(n, len(posts))
    order = sorted(posts, key=lambda p: [int(x) for x in p["num"].split(".")])
    random.Random(f"walking-the-american-way-{cycle}").shuffle(order)
    return order[i], cycle, i

def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    day = datetime.datetime.now(TZ).date()
    if "--date" in args: day = datetime.date.fromisoformat(args[args.index("--date") + 1])
    posts = json.loads(http(SITE + "posts.json"))
    p, cycle, i = story_for(day, posts)
    text = f"{p['title']}\n{p['place']}, {p['year']}\n\n{p['logline']}"
    if len(text) > 290: text = text[:287].rsplit(" ", 1)[0] + "…"
    print(f"{day}: cycle {cycle + 1}, #{i + 1} of {len(posts)} -> {p['num']} {p['title']}")
    if dry:
        print(text); print(p["url"])
        for t, f in [section_post(sec, p["url"]) for sec in p.get("sections", [])] + background_posts(p.get("bg", {}), p["url"]):
            print("--- reply (%d chars)\n%s\n[%s]" % (len(t), t, f[0]["features"][0]["uri"]))
        return

    handle, pw = os.environ["BSKY_HANDLE"], os.environ["BSKY_APP_PASSWORD"]
    s = xrpc("com.atproto.server.createSession", {"identifier": handle, "password": pw})
    tok, did = s["accessJwt"], s["did"]

    auth = {"Authorization": "Bearer " + tok}
    def create(record):
        r = xrpc("com.atproto.repo.createRecord", {"repo": did, "collection": "app.bsky.feed.post", "record": record}, token=tok)
        return {"uri": r["uri"], "cid": r["cid"]}

    # already started today's story? find its root post among the latest posts
    root = None
    feed = json.loads(http(f"{PDS}app.bsky.feed.getAuthorFeed?actor={did}&limit=40&filter=posts_no_replies", headers=auth))
    for item in feed.get("feed", []):
        emb = item["post"].get("record", {}).get("embed", {})
        if emb.get("external", {}).get("uri") == p["url"]:
            root = {"uri": item["post"]["uri"], "cid": item["post"]["cid"]}; break
    if root is None:
        img = http(p["image"])
        blob = xrpc("com.atproto.repo.uploadBlob", token=tok, raw=img, ctype="image/png")["blob"]
        root = create({
            "$type": "app.bsky.feed.post", "text": text, "langs": ["en"],
            "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "embed": {"$type": "app.bsky.embed.external", "external": {
                "uri": p["url"], "title": f"{p['title']} · Walking the American Way",
                "description": p["logline"], "thumb": blob}},
        })
        done, parent = 0, root
    else:
        # count the replies already in the thread (our own chain), to resume after a failure
        th = json.loads(http(f"{PDS}app.bsky.feed.getPostThread?uri={root['uri']}&depth=20&parentHeight=0", headers=auth))["thread"]
        done, parent, node = 0, root, th
        while True:
            mine = [r for r in node.get("replies", []) if r.get("post", {}).get("author", {}).get("did") == did]
            if not mine: break
            node = min(mine, key=lambda r: r["post"]["record"]["createdAt"]); done += 1
            parent = {"uri": node["post"]["uri"], "cid": node["post"]["cid"]}

    replies = [section_post(sec, p["url"]) for sec in p.get("sections", [])] + background_posts(p.get("bg", {}), p["url"])
    secs = replies
    for text, facets in replies[done:]:
        rec = {"$type": "app.bsky.feed.post", "text": text, "langs": ["en"],
               "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
               "reply": {"root": root, "parent": parent}}
        if facets: rec["facets"] = facets
        parent = create(rec)
    rkey = root["uri"].rsplit("/", 1)[1]
    word = "Posted" if done == 0 else "Completed"
    if done == len(secs) and done: word = "Already posted"
    print(f"{word}: https://bsky.app/profile/{handle}/post/{rkey} ({len(secs)} replies)")

if __name__ == "__main__":
    main()
