"""Summarize pitch_probe.py results into tts/out/pitch/report.html.

Pitch shifts are in semitones relative to each speaker's no-instruction baseline (mean of the
baseline seeds). The noise band is ±2 standard errors of a 3-seed mean, using the pooled
within-condition seed SD, so effects inside it are indistinguishable from sampling jitter.

  tts/.venv/bin/python tts/experiments/pitch_report.py
  open http://localhost:8765/audio/pitch/report.html   (dashboard server must be running)
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out" / "pitch"
DOSE_ORDER = ["Speak with an extremely low pitch.", "Speak with a much lower pitch.",
              "Speak with a lower pitch.", "Speak with a slightly lower pitch.", "Read this sentence aloud.",
              "Speak with a slightly higher pitch.", "Speak with a higher pitch.",
              "Speak with a much higher pitch.", "Speak with an extremely high pitch."]
DOSE_LABEL = ["extremely low", "much lower", "lower", "slightly lower", "neutral",
              "slightly higher", "higher", "much higher", "extremely high"]


def st(f, base):
    return 12 * math.log2(f / base) if f and f == f and base else float("nan")


def load(name):
    p = OUT / name
    return list(csv.DictReader(p.open())) if p.exists() else []


def main():
    fuzz, steer, probe = load("fuzz.csv"), load("steer.csv"), load("probe.csv")
    speakers = sorted({r["speaker"] for r in fuzz + steer})
    base = {}
    for s in speakers:
        b = [float(r["f0_med"]) for r in fuzz if r["speaker"] == s and r["group"] == "baseline"]
        if not b:  # fall back to steering alpha=0 (neutral instruction) if fuzz baseline not run yet
            b = [float(r["f0_med"]) for r in steer if r["speaker"] == s and float(r["alpha"]) == 0]
        base[s] = float(np.mean(b)) if b else None

    # ---- fuzz aggregate
    cells = defaultdict(list)
    for r in fuzz:
        cells[(r["instruct"], r["speaker"])].append(r)
    conds = {}
    within = []
    for (ins, spk), rs in cells.items():
        d = [st(float(r["f0_med"]), base[spk]) for r in rs]
        d = [x for x in d if x == x]
        if len(d) > 1:
            within.append(np.var(d, ddof=1))
        c = conds.setdefault(ins, {"instruct": ins or "(no instruction)", "group": rs[0]["group"], "by": {}})
        mid = sorted(rs, key=lambda r: float(r["f0_med"]))[len(rs) // 2]
        c["by"][spk] = dict(
            mean=float(np.mean(d)) if d else None, lo=min(d) if d else None, hi=max(d) if d else None,
            n=len(d), hz=float(np.mean([float(r["f0_med"]) for r in rs])),
            range_st=float(np.nanmean([float(r["range_st"]) for r in rs])),
            wpm=float(np.nanmean([float(r["wpm"]) for r in rs])),
            seeds=[dict(seed=int(r["seed"]), d=st(float(r["f0_med"]), base[spk]), file=r["file"]) for r in rs],
            clip=mid["file"])
    seed_sd = float(math.sqrt(np.mean(within))) if within else 0.0
    # "Speak in a <neutral/nonsense> voice." controls: the template's own effect on pitch
    tmpl = [b["mean"] for c in conds.values() if c["group"] == "control" and c["instruct"].startswith("Speak in a")
            for b in c["by"].values() if b["mean"] is not None]
    template = float(np.mean(tmpl)) if tmpl else None
    band = 2 * seed_sd / math.sqrt(3)

    # ---- probe join
    proj = {r["instruct"]: float(r["proj"]) for r in probe}
    for ins, c in conds.items():
        c["proj"] = proj.get(ins)

    # ---- steering aggregate
    sc = defaultdict(list)
    for r in steer:
        sc[(r["speaker"], float(r["alpha"]))].append(r)
    steer_out = []
    # steering is measured against the unsteered neutral instruction (alpha = 0)
    s0 = {s: float(np.mean([float(r["f0_med"]) for r in sc.get((s, 0.0), [])] or [np.nan])) for s in speakers}
    for (spk, a), rs in sorted(sc.items()):
        d = [st(float(r["f0_med"]), s0[spk]) for r in rs]
        steer_out.append(dict(speaker=spk, alpha=a, mean=float(np.nanmean(d)),
                              seeds=[dict(seed=int(r["seed"]), d=x, file=r["file"]) for r, x in zip(rs, d)],
                              wpm=float(np.nanmean([float(r["wpm"]) for r in rs]))))

    # ---- correlation of probe projection with measured shift (speaker-averaged)
    pts = [(c["proj"], np.mean([b["mean"] for b in c["by"].values() if b["mean"] is not None]))
           for c in conds.values() if c.get("proj") is not None and c["by"]]
    r = float(np.corrcoef(*zip(*pts))[0, 1]) if len(pts) > 3 else None
    pitch_only = [(c["proj"], np.mean([b["mean"] for b in c["by"].values()]))
                  for c in conds.values() if c.get("proj") is not None and c["group"] in ("pitch", "dose")]
    r_pitch = float(np.corrcoef(*zip(*pitch_only))[0, 1]) if len(pitch_only) > 3 else None

    data = dict(speakers=speakers, base={k: v for k, v in base.items()}, band=band, seed_sd=seed_sd, template=template,
                conds=list(conds.values()), steer=steer_out, r=r, r_pitch=r_pitch,
                dose=[dict(label=l, instruct=i) for l, i in zip(DOSE_LABEL, DOSE_ORDER)])
    tpl = (HERE / "pitch_report.tpl.html").read_text()
    findings = HERE / "pitch_findings.html"
    tpl = tpl.replace("<!--FINDINGS-->", findings.read_text() if findings.exists() else "")
    (OUT / "report.html").write_text(tpl.replace("__DATA__", json.dumps(data)))
    print(f"wrote {OUT / 'report.html'}  ({len(conds)} conditions, {len(steer_out)} steer cells, "
          f"seed SD {seed_sd:.2f} st, band ±{band:.2f} st, r={r}, r_pitch={r_pitch})")


if __name__ == "__main__":
    main()
