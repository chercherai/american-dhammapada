#!/usr/bin/env python3
"""Post today's story from Walking the American Way to Bluesky, as a thread:

  1. opening post: title, place and year, the one-line summary, with the story's card image
  2. the verse(s), in Max Müller's translation
  3. "The old story": the commentary story behind the verse, in full
  4. the historical background, in full
  5. a closing post linking to the story, with a link card

Order: all 305 stories in a fixed shuffled order, one a day from START, reshuffled each
cycle, so no saved state is needed. Safe to re-run: if today's thread is already up, or
partly up, it only posts what is missing.

Usage: BSKY_HANDLE=... BSKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx python3 bsky_post.py [--dry-run] [--date YYYY-MM-DD]
"""
import datetime, json, os, random, re, sys, urllib.request, urllib.error
from zoneinfo import ZoneInfo

SITE = "https://chercherai.github.io/american-dhammapada/"
PDS = "https://bsky.social/xrpc/"
START = datetime.date(2026, 11, 11)
TZ = ZoneInfo("America/Winnipeg")
LIMIT = 295   # Bluesky allows 300 graphemes per post; keep a little margin


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


def chunks(text, prefix="", limit=LIMIT):
    """Split text into posts at sentence boundaries. A sentence that won't fit is split at a
    word (marked with an ellipsis) only when the current post would otherwise be left under-full.
    The first post starts with prefix; paragraph breaks are kept."""
    out, cur = [], prefix
    def flush():
        nonlocal cur
        if cur.strip(): out.append(cur.rstrip())
        cur = ""
    for pi, para in enumerate(x for x in text.split("\n\n") if x.strip()):
        sents = re.split(r'(?<=[.!?\u201d\u2019:;])\s+', para.strip())
        first_in_para = True
        for x in sents:
            sep = ("\n\n" if first_in_para and cur.strip() and not cur.endswith("\n\n") else (" " if cur.strip() and not cur.endswith("\n\n") else ""))
            first_in_para = False
            while True:
                if len(cur) + len(sep) + len(x) <= limit:
                    cur += sep + x; break
                room = limit - len(cur) - len(sep) - 2
                if len(cur) < limit * 0.6 and room > 40:          # fill this post, carry the rest over
                    cut = x[:room].rsplit(" ", 1)[0]
                    cur += sep + cut + " \u2026"; flush()
                    x, sep = "\u2026 " + x[len(cut):].lstrip(), ""
                else:
                    flush(); sep = ""
    flush()
    return out


def thread_texts(p):
    bg = p.get("bg", {})
    posts = []
    for v in bg.get("verses", []):
        posts += chunks("“" + v["text"] + "”", f"{v.get('cite') or 'Dhammapada'}\n\n")
    if bg.get("commentary"):
        posts += chunks(bg["commentary"], "The old story\n\n")
    if bg.get("history"):
        posts += chunks(bg["history"], f"{bg.get('hist_title') or 'Background'}\n\n")
    return posts


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

    head = f"{p['title']}\n{p['place']}, {p['year']}"
    text = f"{head}\n\n{p['logline']}\n\n\U0001F9F5"
    if len(text) > LIMIT: text = text[:LIMIT - 1] + "…"
    body = thread_texts(p)
    closing = f"Read the story: {p['title']} →"
    print(f"{day}: cycle {cycle + 1}, #{i + 1} of {len(posts)} -> {p['num']} {p['title']} ({len(body) + 2} posts)")
    if dry:
        for t in [text] + body + [closing + "   [link card: " + p["url"] + "]"]:
            print(f"--- ({len(t)} chars)\n{t}")
        return

    handle, pw = os.environ["BSKY_HANDLE"], os.environ["BSKY_APP_PASSWORD"]
    s = xrpc("com.atproto.server.createSession", {"identifier": handle, "password": pw})
    tok, did = s["accessJwt"], s["did"]
    auth = {"Authorization": "Bearer " + tok}
    now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

    def create(record):
        r = xrpc("com.atproto.repo.createRecord", {"repo": did, "collection": "app.bsky.feed.post", "record": record}, token=tok)
        return {"uri": r["uri"], "cid": r["cid"]}

    def upload_card():
        return xrpc("com.atproto.repo.uploadBlob", token=tok, raw=http(p["image"]), ctype="image/png")["blob"]

    # already started today's thread? find its opening post among the latest posts
    root = None
    feed = json.loads(http(f"{PDS}app.bsky.feed.getAuthorFeed?actor={did}&limit=40&filter=posts_no_replies", headers=auth))
    for item in feed.get("feed", []):
        if item["post"].get("record", {}).get("text", "").startswith(head + "\n"):
            root = {"uri": item["post"]["uri"], "cid": item["post"]["cid"]}; break

    img = None
    if root is None:
        img = upload_card()
        root = create({"$type": "app.bsky.feed.post", "text": text, "langs": ["en"], "createdAt": now(),
                       "embed": {"$type": "app.bsky.embed.images", "images": [{
                           "image": img, "alt": f"{p['title']}. {p['place']}, {p['year']}. {p['logline']}",
                           "aspectRatio": {"width": 1200, "height": 630}}]}})
        done, parent = 0, root
    else:
        # count the replies already in the thread (our own chain), to resume after a failure
        th = json.loads(http(f"{PDS}app.bsky.feed.getPostThread?uri={root['uri']}&depth=60&parentHeight=0", headers=auth))["thread"]
        done, parent, node = 0, root, th
        while True:
            mine = [r for r in node.get("replies", []) if r.get("post", {}).get("author", {}).get("did") == did]
            if not mine: break
            node = min(mine, key=lambda r: r["post"]["record"]["createdAt"]); done += 1
            parent = {"uri": node["post"]["uri"], "cid": node["post"]["cid"]}

    total = len(body) + 1
    for k in range(done, total):
        rec = {"$type": "app.bsky.feed.post", "langs": ["en"], "createdAt": now(),
               "reply": {"root": root, "parent": parent}}
        if k < len(body):
            rec["text"] = body[k]
        else:
            img = img or upload_card()
            rec["text"] = closing
            rec["facets"] = [{"index": {"byteStart": 0, "byteEnd": len(closing.encode())},
                              "features": [{"$type": "app.bsky.richtext.facet#link", "uri": p["url"]}]}]
            rec["embed"] = {"$type": "app.bsky.embed.external", "external": {
                "uri": p["url"], "title": f"{p['title']} · Walking the American Way",
                "description": p["logline"], "thumb": img}}
        parent = create(rec)

    rkey = root["uri"].rsplit("/", 1)[1]
    word = "Already posted" if done >= total else ("Posted" if done == 0 else "Completed")
    print(f"{word}: https://bsky.app/profile/{handle}/post/{rkey} ({total + 1} posts)")


if __name__ == "__main__":
    main()
