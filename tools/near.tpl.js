/* "Near you": open a story set somewhere near the reader.
   Location is guessed from the browser's time zone only (nothing is sent
   anywhere); an unknown zone gets any story at all.
   Picks among the closest few, weighted toward the closest, so it isn't
   the same story every time. */
(() => {
  const PTS = /*PTS*/[];
  const TZ = {
    "America/New_York": [40.7, -74.0], "America/Detroit": [42.3, -83.0], "America/Indiana/Indianapolis": [39.8, -86.2],
    "America/Kentucky/Louisville": [38.3, -85.8], "America/Chicago": [41.9, -87.6], "America/Denver": [39.7, -105.0],
    "America/Boise": [43.6, -116.2], "America/Phoenix": [33.4, -112.1], "America/Los_Angeles": [34.1, -118.2],
    "America/Anchorage": [61.2, -149.9], "America/Juneau": [58.3, -134.4], "Pacific/Honolulu": [21.3, -157.9],
    "America/Puerto_Rico": [18.4, -66.1], "America/St_Thomas": [18.3, -64.9], "Pacific/Guam": [13.5, 144.8],
    "America/Toronto": [43.7, -79.4], "America/Montreal": [45.5, -73.6], "America/Halifax": [44.6, -63.6],
    "America/St_Johns": [47.6, -52.7], "America/Winnipeg": [49.9, -97.1], "America/Regina": [50.4, -104.6],
    "America/Edmonton": [53.5, -113.5], "America/Vancouver": [49.3, -123.1], "America/Mexico_City": [19.4, -99.1],
    "America/Monterrey": [25.7, -100.3], "America/Tijuana": [32.5, -117.0], "America/Havana": [23.1, -82.4],
    "America/Nassau": [25.1, -77.3], "America/Santo_Domingo": [18.5, -69.9]
  };
  const rad = d => d * Math.PI / 180;
  function km(a, b, c, d) {
    const x = Math.sin(rad(c - a) / 2) ** 2 + Math.cos(rad(a)) * Math.cos(rad(c)) * Math.sin(rad(d - b) / 2) ** 2;
    return 12742 * Math.asin(Math.sqrt(x));
  }
  function pick(lat, lon) {
    const near = PTS.map(p => [km(lat, lon, p[1], p[2]), p[0]]).sort((a, b) => a[0] - b[0]).slice(0, 10);
    const w = near.map((_, i) => 1 / Math.sqrt(i + 1)), tot = w.reduce((a, b) => a + b, 0);
    let r = Math.random() * tot;
    for (let i = 0; i < near.length; i++) { r -= w[i]; if (r <= 0) return near[i][1]; }
    return near[0][1];
  }
  function where() {
    try { const z = Intl.DateTimeFormat().resolvedOptions().timeZone; if (TZ[z]) return TZ[z]; } catch (e) {}
    return null;
  }
  const a = document.getElementById("nearme");
  if (!a) return;
  a.addEventListener("click", ev => {
    ev.preventDefault();
    const here = where();
    const f = here ? pick(here[0], here[1]) : PTS[Math.floor(Math.random() * PTS.length)][0];
    location.href = f;
  });
})();
