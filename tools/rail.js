/* Fast scroller for long lists. Builds a rail from elements carrying
   data-rail="short label" (and optional data-rail-tip, data-rail-n, data-rail-major). */
(() => {
  const marks = [...document.querySelectorAll("[data-rail]")];
  if (marks.length < 2) return;
  const css = document.createElement("style");
  css.textContent = `
#frail { position: fixed; right: .1rem; top: 8vh; bottom: 8vh; width: 2.8rem; display: flex; flex-direction: column; z-index: 5; touch-action: none; user-select: none; -webkit-user-select: none; cursor: ns-resize; padding: 0 .3rem; }
#frail .tk { flex: 1; display: flex; align-items: center; justify-content: flex-end; width: 100%; position: relative; }
#frail .tk::before { content: ""; position: absolute; right: 0; top: 15%; bottom: 15%; width: calc(.2rem + var(--n) * 2.2rem); background: var(--page-dim, #999); opacity: .32; border-radius: 1px 0 0 1px; }
#frail .tk::after { content: ""; height: 1px; width: .5rem; background: var(--page-dim, #999); opacity: .45; position: relative; }
#frail .tk.c::after { width: .9rem; opacity: .9; }
#frail .tk.cur::after { background: var(--page, #eee); opacity: 1; width: 1.2rem; height: 2px; }
#frail .tk span { position: absolute; right: 1.3rem; font-family: var(--font-display, serif); font-size: .72rem; color: var(--page-dim, #999); font-variant-numeric: tabular-nums; }
#fbubble { position: fixed; right: 3.6rem; max-width: 70vw; padding: .25rem .7rem; background: var(--ink-2, #222); border: 1px solid var(--rule, #444); font-family: var(--font-display, serif); font-size: 1.3rem; color: var(--page, #eee); pointer-events: none; opacity: 0; transition: opacity .15s; z-index: 6; transform: translateY(-50%); white-space: nowrap; }
#fbubble.on { opacity: 1; }
@media (max-width: 40rem) { main { padding-right: 3.2rem; } }`;
  document.head.appendChild(css);
  const mx = Math.max(...marks.map(m => +(m.dataset.railN || 1)));
  const rail = document.createElement("nav");
  rail.id = "frail"; rail.setAttribute("aria-label", "Jump to section");
  marks.forEach((m, i) => {
    const t = document.createElement("div");
    t.className = "tk" + (m.dataset.railMajor !== undefined ? " c" : "");
    t.style.setProperty("--n", (+(m.dataset.railN || 1) / mx).toFixed(3));
    t.title = m.dataset.railTip || m.dataset.rail;
    if (m.dataset.railMajor !== undefined) { const s = document.createElement("span"); s.textContent = m.dataset.rail; t.appendChild(s); }
    rail.appendChild(t);
  });
  const bub = document.createElement("div"); bub.id = "fbubble";
  document.body.append(rail, bub);
  const tks = [...rail.children];
  let dragging = false;
  function pick(y) {
    const r = rail.getBoundingClientRect();
    const i = Math.max(0, Math.min(tks.length - 1, Math.floor((y - r.top) / r.height * tks.length)));
    marks[i].scrollIntoView({block: "start"});
    bub.textContent = marks[i].dataset.railTip || marks[i].dataset.rail;
    bub.style.top = y + "px"; bub.classList.add("on");
  }
  rail.addEventListener("pointerdown", e => { dragging = true; rail.setPointerCapture(e.pointerId); pick(e.clientY); });
  rail.addEventListener("pointermove", e => { if (dragging) pick(e.clientY); });
  const end = () => { dragging = false; bub.classList.remove("on"); };
  rail.addEventListener("pointerup", end); rail.addEventListener("pointercancel", end);
  function mark() {
    let k = 0; marks.forEach((m, i) => { if (m.getBoundingClientRect().top < innerHeight * .3) k = i; });
    tks.forEach((t, i) => t.classList.toggle("cur", i === k));
  }
  addEventListener("scroll", mark, {passive: true}); mark();
})();
