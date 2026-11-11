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
        print(text); print(p["url"]); return

    handle, pw = os.environ["BSKY_HANDLE"], os.environ["BSKY_APP_PASSWORD"]
    s = xrpc("com.atproto.server.createSession", {"identifier": handle, "password": pw})
    tok, did = s["accessJwt"], s["did"]

    # already posted today's story? (look at the latest posts for the same link)
    feed = json.loads(http(f"{PDS}app.bsky.feed.getAuthorFeed?actor={did}&limit=20", headers={"Authorization": "Bearer " + tok}))
    for item in feed.get("feed", []):
        emb = item["post"].get("record", {}).get("embed", {})
        if emb.get("external", {}).get("uri") == p["url"]:
            print("Already posted:", item["post"]["uri"]); return

    img = http(p["image"])
    blob = xrpc("com.atproto.repo.uploadBlob", token=tok, raw=img, ctype="image/png")["blob"]
    record = {
        "$type": "app.bsky.feed.post", "text": text, "langs": ["en"],
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "embed": {"$type": "app.bsky.embed.external", "external": {
            "uri": p["url"], "title": f"{p['title']} · Walking the American Way",
            "description": p["logline"], "thumb": blob}},
    }
    r = xrpc("com.atproto.repo.createRecord", {"repo": did, "collection": "app.bsky.feed.post", "record": record}, token=tok)
    rkey = r["uri"].rsplit("/", 1)[1]
    print(f"Posted: https://bsky.app/profile/{handle}/post/{rkey}")

if __name__ == "__main__":
    main()
