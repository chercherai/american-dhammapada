/* Reader preferences for Walking the American Way: text size and light/dark.
   Each story keeps its own palette; "light" or "dark" flips a page whose
   designed palette is the other way, by inverting it (hues kept). */
(() => {
  const SIZES = [87.5, 100, 112.5, 125, 140];
  const get = k => { try { return localStorage.getItem("awaw-" + k); } catch (e) { return null; } };
  const set = (k, v) => { try { localStorage.setItem("awaw-" + k, v); } catch (e) {} };
  const root = document.documentElement;

  function lum(c) {
    const m = c.match(/\d+(\.\d+)?/g); if (!m) return 0;
    const [r, g, b] = m.slice(0, 3).map(x => +x / 255);
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }
  let nativeDark = null;
  function native() {
    if (nativeDark === null) {
      const bg = getComputedStyle(document.body).backgroundColor;
      const transparent = /rgba\(.*,\s*0\)$/.test(bg) || bg === "transparent";
      nativeDark = transparent ? lum(getComputedStyle(root).backgroundColor) < 0.5 : lum(bg) < 0.5;
      root.style.backgroundColor = transparent ? "" : bg;
    }
    return nativeDark;
  }
  function applySize() {
    const i = +(get("size") ?? 1);
    root.style.fontSize = SIZES[Math.max(0, Math.min(SIZES.length - 1, i))] + "%";
  }
  function applyTheme() {
    const want = get("theme");                  // "light", "dark" or null (as designed)
    const flip = want && ((want === "dark") !== native());
    root.style.filter = flip ? "invert(1) hue-rotate(180deg)" : "";
    const btn = document.getElementById("awaw-theme");
    if (btn) btn.setAttribute("aria-label", "Switch to " + ((want ? want === "dark" : native()) ? "light" : "dark") + " theme");
  }
  applySize();

  function ui() {
    const css = document.createElement("style");
    css.textContent = `
#awaw-prefs { position: fixed; right: .6rem; bottom: .6rem; z-index: 50; display: flex; gap: .3rem; font: 600 15px/1 system-ui, sans-serif; }
#awaw-prefs button { min-width: 2.4em; height: 2.4em; padding: 0 .55em; border-radius: 1.2em; border: 1px solid rgba(128,128,128,.45);
  background: rgba(20,20,22,.72); color: #eee; cursor: pointer; backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); }
#awaw-prefs button:hover { border-color: rgba(220,220,220,.8); }
#awaw-prefs button:focus-visible { outline: 2px solid #eee; outline-offset: 2px; }
@media print { #awaw-prefs { display: none; } }`;
    document.head.appendChild(css);
    const box = document.createElement("div");
    box.id = "awaw-prefs"; box.setAttribute("role", "group"); box.setAttribute("aria-label", "Reading preferences");
    box.innerHTML = '<button id="awaw-smaller" aria-label="Smaller text">A&minus;</button>' +
                    '<button id="awaw-bigger" aria-label="Larger text">A+</button>' +
                    '<button id="awaw-theme"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" style="display:block;margin:auto"><circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 1.5a6.5 6.5 0 0 1 0 13z" fill="currentColor"/></svg></button>';
    document.body.appendChild(box);
    const step = d => { const i = +(get("size") ?? 1); set("size", Math.max(0, Math.min(SIZES.length - 1, i + d))); applySize(); dispatchEvent(new Event("resize")); };
    document.getElementById("awaw-smaller").onclick = () => step(-1);
    document.getElementById("awaw-bigger").onclick = () => step(1);
    document.getElementById("awaw-theme").onclick = () => {
      const now = get("theme") ? get("theme") === "dark" : native();
      set("theme", now ? "light" : "dark"); applyTheme();
    };
    applyTheme();
    // Story pages: a discreet arrow at the top that takes you to the end (Background, pager).
    if (document.querySelector(".pager")) {
      const st = document.createElement("style");
      st.textContent = `
#awaw-down { position: absolute; top: .9rem; right: 1rem; z-index: 40; width: 2.2rem; height: 2.2rem; display: grid; place-items: center;
  color: inherit; opacity: .45; text-decoration: none; border-radius: 50%; animation: awaw-bob 2.4s ease-in-out 1.2s 4; }
#awaw-down:hover, #awaw-down:focus-visible { opacity: .9; }
#awaw-down:focus-visible { outline: 1px solid currentColor; outline-offset: 2px; }
@keyframes awaw-bob { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(6px); } }
@media (prefers-reduced-motion: reduce) { #awaw-down { animation: none; } }
@media print { #awaw-down { display: none; } }`;
      document.head.appendChild(st);
      const d = document.createElement("a");
      d.id = "awaw-down"; d.href = "#"; d.setAttribute("aria-label", "Skip to the end of the page");
      d.style.color = getComputedStyle(document.body).color;
      d.innerHTML = '<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><path d="M9 2v13M3.5 9.5 9 15l5.5-5.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
      d.addEventListener("click", ev => {
        ev.preventDefault();
        const smooth = !matchMedia("(prefers-reduced-motion: reduce)").matches;
        scrollTo({top: document.documentElement.scrollHeight, behavior: smooth ? "smooth" : "auto"});
      });
      document.body.appendChild(d);
    }
  }
  if (document.body) ui(); else document.addEventListener("DOMContentLoaded", ui);
})();
