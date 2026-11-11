/* Service worker for Walking the American Way: offline reading.
   - The three views and small scripts are cached on install.
   - Stories are cached as you read them, or all at once from "Save for offline".
   - Pages: network first, so corrections arrive; the cached copy when offline.
   - Fonts and map libraries: cache first. */
const VERSION = "8fa510b622";
const CACHE = "awaw-" + VERSION;
const SHELL = ["./", "index.html", "timeline.html", "map.html", "prefs.js", "rail.js", "near.js",
               "manifest.webmanifest", "icon-192.png", "icon-512.png", "offline-list.json"];

const EXTRA = ["https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js",
               "https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js",
               "https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Spectral:ital,wght@0,300;0,400;1,300;1,400&display=swap"];

self.addEventListener("install", ev => {
  ev.waitUntil((async () => {
    const c = await caches.open(CACHE);
    await c.addAll(SHELL);
    // best effort: map libraries and font stylesheet, so the Place view works offline
    await Promise.all(EXTRA.map(async u => { try { const r = await fetch(u, {mode: "cors"}); if (r.ok) await c.put(u, r); } catch (e) {} }));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", ev => {
  ev.waitUntil((async () => {
    const keys = await caches.keys();
    const old = keys.filter(k => k.startsWith("awaw-") && k !== CACHE);
    // carry saved stories forward into the new cache, then drop the old ones
    const cur = await caches.open(CACHE);
    for (const k of old) {
      const c = await caches.open(k);
      for (const req of await c.keys()) {
        if (!(await cur.match(req))) { const r = await c.match(req); if (r) await cur.put(req, r); }
      }
      await caches.delete(k);
    }
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", ev => {
  const req = ev.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  const sameOrigin = url.origin === self.location.origin;
  const thirdParty = /fonts\.(googleapis|gstatic)\.com$|cdnjs\.cloudflare\.com$/.test(url.hostname);
  if (sameOrigin && /\.(pdf|epub)$/.test(url.pathname)) return;     // big downloads go straight to the network
  if (thirdParty) {
    ev.respondWith(caches.open(CACHE).then(async c => {
      const hit = await c.match(req);
      if (hit) return hit;
      const res = await fetch(req); if (res.ok || res.type === "opaque") c.put(req, res.clone()); return res;
    }));
    return;
  }
  if (!sameOrigin) return;
  ev.respondWith((async () => {
    const c = await caches.open(CACHE);
    try {
      const res = await fetch(req);
      if (res.ok) c.put(req, res.clone());
      return res;
    } catch (e) {
      const hit = await c.match(req, {ignoreSearch: true});
      if (hit) return hit;
      if (req.mode === "navigate") return (await c.match("index.html")) || Response.error();
      return Response.error();
    }
  })());
});
