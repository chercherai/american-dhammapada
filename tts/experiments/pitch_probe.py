"""How do instruction words move Qwen3-TTS pitch?

Three experiments on the CustomVoice 1.7B model, one fixed sentence:

  fuzz   render the sentence under many style instructions ("Speak in a deep voice.", ...)
         x seeds x speakers and measure median F0 with Praat.
  probe  build a "pitch direction" in the instruction-embedding space (the model embeds the
         instruction tokens, projects them, and prepends them to the prompt) and project
         every fuzz instruction onto it.
  steer  add alpha * direction to the instruction embeddings of a neutral instruction and
         measure whether F0 follows alpha (a causal test of the direction).

Results append to tts/out/pitch/*.csv (resumable); audio goes to tts/out/pitch/wav/.

  tts/.venv/bin/python tts/experiments/pitch_probe.py fuzz probe steer
  PITCH_SEEDS=44,55,66 tts/.venv/bin/python tts/experiments/pitch_probe.py steer   # add seeds
"""
from __future__ import annotations

import csv
import math
import sys
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
import parselmouth
import soundfile as sf
from mlx_audio.tts.utils import load_model

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out" / "pitch"
WAV = OUT / "wav"
WAV.mkdir(parents=True, exist_ok=True)

MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
SENTENCE = "She put the bucket down and scooped up two handfuls and held them out to him."
SPEAKERS = ["ryan", "vivian"]
SEEDS = [int(s) for s in __import__("os").environ.get("PITCH_SEEDS", "11,22,33").split(",")]
NEUTRAL = "Read this sentence aloud."

# (group, instruction). None = no instruction at all (the baseline).
CONDITIONS: list[tuple[str, str | None]] = [("baseline", None), ("control", NEUTRAL)]
CONDITIONS += [("control", f"Speak in a {w} voice.") for w in ("normal", "clear", "blue", "wooden")]
CONDITIONS += [("control", "Zxqv plorb.")]
CONDITIONS += [("pitch", f"Speak in a {w} voice.") for w in (
    "high-pitched", "low-pitched", "deep", "squeaky", "shrill", "booming",
    "baritone", "bass", "tenor", "soprano", "falsetto", "gravelly", "breathy", "nasal")]
CONDITIONS += [("age/body", f"Speak in a {w} voice.") for w in (
    "child's", "young", "old", "elderly", "giant's", "tiny")]
CONDITIONS += [("emotion", f"Speak in a {w} voice.") for w in (
    "excited", "angry", "sad", "calm", "frightened", "sleepy", "cheerful", "solemn")]
CONDITIONS += [("delivery", f"Speak in a {w} voice.") for w in (
    "whispering", "shouting", "monotone", "sing-song")]
CONDITIONS += [("dose", s) for s in (
    "Speak with a slightly higher pitch.", "Speak with a higher pitch.",
    "Speak with a much higher pitch.", "Speak with an extremely high pitch.",
    "Speak with a slightly lower pitch.", "Speak with a lower pitch.",
    "Speak with a much lower pitch.", "Speak with an extremely low pitch.")]

HIGH_WORDS = ["high-pitched", "squeaky", "shrill", "soprano", "falsetto", "high pitch"]
LOW_WORDS = ["low-pitched", "deep", "booming", "baritone", "bass", "low pitch"]
ALPHAS = [-3, -2, -1, -0.5, 0, 0.5, 1, 2, 3]


# ---------------------------------------------------------------- measurement

def measure(audio: np.ndarray, sr: int, speaker: str) -> dict:
    snd = parselmouth.Sound(audio.astype(np.float64), sampling_frequency=sr)
    lo, hi = (60, 400) if speaker == "ryan" else (100, 600)
    f0 = snd.to_pitch_ac(time_step=0.01, pitch_floor=lo, pitch_ceiling=hi).selected_array["frequency"]
    v = f0[f0 > 0]
    dur = len(audio) / sr
    if len(v) < 10:
        return dict(f0_med=float("nan"), f0_p10=float("nan"), f0_p90=float("nan"),
                    range_st=float("nan"), voiced=0.0, dur=dur, wpm=float("nan"), rms_db=float("nan"))
    p10, p50, p90 = np.percentile(v, [10, 50, 90])
    rms = float(np.sqrt(np.mean(audio ** 2)))
    return dict(f0_med=float(p50), f0_p10=float(p10), f0_p90=float(p90),
                range_st=float(12 * math.log2(p90 / p10)), voiced=len(v) / len(f0), dur=dur,
                wpm=len(SENTENCE.split()) / (dur / 60), rms_db=20 * math.log10(rms + 1e-9))


def render(model, speaker, instruct, seed):
    mx.random.seed(seed)
    np.random.seed(seed)
    res = list(model.generate_custom_voice(text=SENTENCE, speaker=speaker, language="english",
                                           instruct=instruct))
    return np.concatenate([np.array(r.audio, dtype=np.float32).reshape(-1) for r in res])


def done_keys(path: Path, cols) -> set:
    if not path.exists():
        return set()
    with path.open() as f:
        return {tuple(r[c] for c in cols) for r in csv.DictReader(f)}


def append(path: Path, row: dict):
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)


# ---------------------------------------------------------------- embeddings

def instruct_embeds(model, instruct: str) -> mx.array:
    """Exactly what the model prepends for an instruction: [1, n_tokens, d]."""
    ids = mx.array(model.tokenizer.encode(f"<|im_start|>user\n{instruct}<|im_end|>\n"))[None, :]
    return model.talker.text_projection(model.talker.get_text_embeddings()(ids))


def word_embed(model, phrase: str) -> np.ndarray:
    """Mean projected embedding of a phrase's own tokens (leading space, no chat wrapper)."""
    ids = mx.array(model.tokenizer.encode(" " + phrase))[None, :]
    e = model.talker.text_projection(model.talker.get_text_embeddings()(ids))
    return np.array(e[0].astype(mx.float32)).mean(axis=0)


def pitch_direction(model) -> np.ndarray:
    hi = np.mean([word_embed(model, w) for w in HIGH_WORDS], axis=0)
    lo = np.mean([word_embed(model, w) for w in LOW_WORDS], axis=0)
    return hi - lo


# ---------------------------------------------------------------- experiments

def run_fuzz(model):
    path = OUT / "fuzz.csv"
    seen = done_keys(path, ["speaker", "instruct", "seed"])
    jobs = [(s, g, ins, seed) for s in SPEAKERS for g, ins in CONDITIONS for seed in SEEDS
            if (s, ins or "", str(seed)) not in seen]
    print(f"fuzz: {len(jobs)} renders to do")
    t0 = time.time()
    for i, (spk, group, ins, seed) in enumerate(jobs, 1):
        a = render(model, spk, ins, seed)
        name = f"{spk}-{abs(hash(ins)) % 10**8:08d}-{seed}.wav"
        sf.write(WAV / name, a, model.sample_rate)
        append(path, dict(speaker=spk, group=group, instruct=ins or "", seed=seed, file=name,
                          **measure(a, model.sample_rate, spk)))
        if i % 10 == 0:
            print(f"  {i}/{len(jobs)}  {time.time() - t0:.0f}s", flush=True)


def run_probe(model):
    d = pitch_direction(model)
    dn = d / np.linalg.norm(d)
    rows = []
    for group, ins in CONDITIONS:
        if ins is None:
            continue
        e = np.array(instruct_embeds(model, ins)[0].astype(mx.float32)).mean(axis=0)
        n = np.array(instruct_embeds(model, NEUTRAL)[0].astype(mx.float32)).mean(axis=0)
        rows.append(dict(group=group, instruct=ins, proj=float((e - n) @ dn)))
    with (OUT / "probe.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    # how big is the direction relative to a token embedding?
    typical = float(np.linalg.norm(np.array(instruct_embeds(model, NEUTRAL)[0].astype(mx.float32)), axis=1).mean())
    print(f"probe: |direction| = {np.linalg.norm(d):.3f}, typical token |e| = {typical:.3f}")
    np.save(OUT / "pitch_direction.npy", d)


def run_steer(model):
    """Add alpha * direction to every instruction position of the NEUTRAL instruction."""
    d = mx.array(pitch_direction(model)).astype(mx.bfloat16)
    n_ins = len(model.tokenizer.encode(f"<|im_start|>user\n{NEUTRAL}<|im_end|>\n"))
    orig = model._prepare_generation_inputs
    state = {"alpha": 0.0}

    def patched(*args, **kwargs):
        out = orig(*args, **kwargs)
        embeds, *rest = out
        if kwargs.get("instruct") == NEUTRAL and state["alpha"]:
            add = mx.zeros_like(embeds)
            add[:, :n_ins, :] = state["alpha"] * d
            embeds = embeds + add
        return (embeds, *rest)

    model._prepare_generation_inputs = patched
    path = OUT / "steer.csv"
    seen = done_keys(path, ["speaker", "alpha", "seed"])
    jobs = [(s, a, seed) for s in SPEAKERS for a in ALPHAS for seed in SEEDS
            if (s, str(float(a)), str(seed)) not in seen]
    print(f"steer: {len(jobs)} renders to do")
    for spk, a, seed in jobs:
        state["alpha"] = float(a)
        audio = render(model, spk, NEUTRAL, seed)
        name = f"steer-{spk}-{a:+.1f}-{seed}.wav"
        sf.write(WAV / name, audio, model.sample_rate)
        append(path, dict(speaker=spk, alpha=float(a), seed=seed, file=name,
                          **measure(audio, model.sample_rate, spk)))
    model._prepare_generation_inputs = orig


if __name__ == "__main__":
    which = sys.argv[1:] or ["fuzz", "probe", "steer"]
    m = load_model(MODEL)
    # sanity: the patch point must receive instruct as a keyword
    import inspect
    assert "instruct" in inspect.signature(m._prepare_generation_inputs).parameters
    for w in which:
        {"fuzz": run_fuzz, "probe": run_probe, "steer": run_steer}[w](m)
    print("done")
