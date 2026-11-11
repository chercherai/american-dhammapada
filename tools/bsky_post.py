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

LINK = "Read this part \u2192"
def section_post(sec, url):
    """One post per section: heading, dateline, as many whole sentences as fit, and a link to the section."""
    import re
    head = sec["heading"] + ("\n" + sec["dateline"] if sec.get("dateline") else "")
    budget = 296 - len(head) - len("\n\n") - len("\n\n" + LINK)
    sents = re.split(r'(?<=[.!?\u201d\u2019])\s+', sec["text"])
    body = ""
    for x in sents:
        if len(body) + len(x) + 1 > budget: break
        body = (body + " " + x).strip()
    if len(body) < budget * 0.6 and len(body) < len(sec["text"]):
        # too little fits in whole sentences: fill to the budget and cut at a word
        body = sec["text"][:budget - 1].rsplit(" ", 1)[0].rstrip(",;:") + "\u2026"
    elif len(body) < len(sec["text"]):
        body += " \u2026"
    text = f"{head}\n\n{body}\n\n{LINK}"
    start = len(text.encode()) - len(LINK.encode())
    facets = [{"index": {"byteStart": start, "byteEnd": len(text.encode())},
               "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url + sec["anchor"]}]}]
    return text, facets

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
        for sec in p.get("sections", []):
            t, f = section_post(sec, p["url"]); print("--- reply (%d chars)\n%s\n[%s]" % (len(t), t, f[0]["features"][0]["uri"]))
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

    secs = p.get("sections", [])
    for sec in secs[done:]:
        text, facets = section_post(sec, p["url"])
        rec = {"$type": "app.bsky.feed.post", "text": text, "langs": ["en"],
               "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
               "reply": {"root": root, "parent": parent}}
        if facets: rec["facets"] = facets
        parent = create(rec)
    rkey = root["uri"].rsplit("/", 1)[1]
    word = "Posted" if done == 0 else "Completed"
    if done == len(secs) and done: word = "Already posted"
    print(f"{word}: https://bsky.app/profile/{handle}/post/{rkey} ({len(secs)} section replies)")

if __name__ == "__main__":
    main()
