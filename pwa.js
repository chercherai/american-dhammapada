/* Registers the service worker, and wires the "Save for offline" button on the index. */
(() => {
  if (!("serviceWorker" in navigator) || (location.protocol !== "https:" && location.hostname !== "localhost")) return;
  try { navigator.serviceWorker.register("sw.js").catch(() => {}); } catch (e) { return; }

  const btn = document.getElementById("save-offline");
  const msg = document.getElementById("save-offline-msg");
  if (!btn || !("caches" in window)) return;
  btn.hidden = false;
  const say = t => { if (msg) msg.textContent = t; };

  async function cacheName() {
    const keys = await caches.keys();
    return keys.find(k => k.startsWith("awaw-")) || null;
  }
  async function status() {
    try {
      const list = await (await fetch("offline-list.json")).json();
      const name = await cacheName(); if (!name) return;
      const c = await caches.open(name);
      let n = 0; for (const f of list) if (await c.match(f)) n++;
      if (n === list.length) { say("All " + list.length + " stories are saved on this device."); btn.textContent = "Update saved stories"; }
      else if (n > 0) say(n + " of " + list.length + " stories saved on this device.");
    } catch (e) {}
  }
  btn.addEventListener("click", async () => {
    btn.disabled = true;
    try {
      await navigator.serviceWorker.ready;
      const list = await (await fetch("offline-list.json", {cache: "no-store"})).json();
      const c = await caches.open(await cacheName());
      let done = 0;
      const queue = list.slice();
      async function worker() {
        while (queue.length) {
          const f = queue.shift();
          try { const r = await fetch(f, {cache: "no-cache"}); if (r.ok) await c.put(f, r); } catch (e) {}
          done++; if (done % 5 === 0 || done === list.length) say("Saving… " + done + " of " + list.length);
        }
      }
      await Promise.all([worker(), worker(), worker(), worker()]);
      say("All " + list.length + " stories are saved. They will open without a connection.");
      btn.textContent = "Update saved stories";
    } catch (e) { say("Couldn't save just now. Try again when you're online."); }
    btn.disabled = false;
  });
  status();
})();
