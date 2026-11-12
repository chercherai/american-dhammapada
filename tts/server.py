"""Qwen3-TTS testing dashboard for Walking the American Way.

Run:  tts/.venv/bin/python tts/server.py   (then open http://localhost:8765)

Reads the story pages in the repo root, splits them into narration blocks, and lets you
render any block with any Qwen3-TTS variant (CustomVoice speakers, VoiceDesign prompts,
Base voice cloning). Every render is kept as a "take" in tts/out/ with its settings,
timing, a 1-5 rating and notes, so voices can be compared and the best takes stitched
into a full-story audio file.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import threading
import time
import uuid
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import soundfile as sf
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE / "out"
TAKES_DIR = OUT / "takes"
REFS_DIR = OUT / "refs"
RENDERS_DIR = OUT / "renders"
TAKES_DB = OUT / "takes.json"
VOICES_DB = OUT / "voices.json"
for d in (TAKES_DIR, REFS_DIR, RENDERS_DIR):
    d.mkdir(parents=True, exist_ok=True)

MODELS = {
    "custom-1.7b": {"repo": "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16", "mode": "custom",
                    "label": "CustomVoice 1.7B: preset speakers + style instruction"},
    "design-1.7b": {"repo": "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16", "mode": "design",
                    "label": "VoiceDesign 1.7B: voice described in words"},
    "base-1.7b":   {"repo": "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16", "mode": "clone",
                    "label": "Base 1.7B: clone a voice from a reference clip"},
    "custom-0.6b": {"repo": "mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-bf16", "mode": "custom",
                    "label": "CustomVoice 0.6B (faster, lower quality)"},
    "base-0.6b":   {"repo": "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16", "mode": "clone",
                    "label": "Base 0.6B clone (faster, lower quality)"},
    "kokoro":      {"repo": "mlx-community/Kokoro-82M-bf16", "mode": "kokoro",
                    "label": "Kokoro 82M: small, fast preset voices"},
    "chatterbox":  {"repo": "mlx-community/chatterbox-fp16", "mode": "chatterbox",
                    "label": "Chatterbox: clone or built-in voice, expressiveness control"},
    "chatterbox-turbo": {"repo": "mlx-community/chatterbox-turbo-fp16", "mode": "turbo",
                    "label": "Chatterbox Turbo: faster clone or built-in voice"},
    "vibevoice":   {"repo": "mlx-community/VibeVoice-Realtime-0.5B-fp16", "mode": "vibevoice",
                    "label": "VibeVoice Realtime 0.5B: preset voices"},
}
QWEN_MODES = {"custom", "design", "clone"}


def snapshot_dir(repo: str) -> Path | None:
    d = Path.home() / ".cache/huggingface/hub" / ("models--" + repo.replace("/", "--")) / "snapshots"
    snaps = sorted(d.glob("*"), key=lambda p: p.stat().st_mtime) if d.exists() else []
    return snaps[-1] if snaps else None


def preset_voices(key: str) -> list[str]:
    """Voice presets shipped as files in the model repo (Kokoro, VibeVoice)."""
    snap = snapshot_dir(MODELS[key]["repo"])
    if not snap or not (snap / "voices").exists():
        return []
    return sorted({p.stem for p in (snap / "voices").iterdir() if p.suffix in (".safetensors", ".pt")})

# ---------------------------------------------------------------- story parsing

SKIP_PAGES = {"index.html", "map.html", "timeline.html"}


class StoryParser(HTMLParser):
    """Pulls narration blocks out of a story page's <main>, in reading order."""

    BLOCK_TAGS = {"h1", "h2", "h3", "p", "div", "cite"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict] = []
        self.meta = ""
        self.stack: list[tuple[str, str]] = []  # (tag, class)
        self.buf: list[str] | None = None
        self.kind = ""
        self.in_main = self.in_footer = self.in_bg = self.in_meta = self.in_script = False
        self.section = "Opening"

    def _cls(self, attrs):
        return dict(attrs).get("class", "") or ""

    def handle_starttag(self, tag, attrs):
        cls = self._cls(attrs)
        if tag in ("br", "img", "hr", "wbr", "meta", "link", "input", "source"):
            if tag == "br" and self.buf is not None:
                self.buf.append(" / " if self.kind in ("verse", "epigraph") else " ")
            return  # void elements never get an end tag
        self.stack.append((tag, cls))
        if tag == "main":
            self.in_main = True
        if tag in ("script", "style"):
            self.in_script = True
        if not self.in_main:
            return
        if tag == "footer":
            self.in_footer = True
        if tag == "details" and "bg" in cls:
            self.in_bg = True
            self.section = "Background"
        if tag == "span" and self.stack[-2:-1] and self.stack[-2][1] == "series":
            self.in_meta = True
        if self.in_footer or self.buf is not None:
            return
        kind = None
        if tag == "h1":
            kind = "title"
        elif tag == "h2":
            kind = "heading"
        elif tag == "h3":
            kind = "bg-heading"
        elif tag == "div" and "epigraph" in cls:
            kind = "epigraph"
        elif tag == "div" and "brk" in cls:
            kind = "break"
        elif tag == "p":
            parents = " ".join(c for _, c in self.stack[:-1])
            if "dateline" in cls:
                kind = "dateline"
            elif "heard" in cls:
                kind = "heard"
            elif "brk" in cls:
                kind = "break"
            elif "verse" in parents.split() or "pd" in parents.split():
                kind = "verse"
            else:
                kind = "para"
        elif tag == "div" and ("pd" in cls.split() or "verse" in cls.split()):
            kind = None  # children <p> handle it; bare-text .pd handled below
            if "pd" in cls.split():
                kind = "verse"
        if kind:
            self.kind, self.buf = kind, []
            self.depth = len(self.stack)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.in_script = False
        if self.buf is not None and len(self.stack) == self.depth and self.stack[-1][0] == tag:
            text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            if self.kind == "heading":
                self.section = text
            if text or self.kind == "break":
                self.blocks.append({"kind": self.kind, "text": text, "section": self.section,
                                    "background": self.in_bg})
            self.buf = None
        if tag == "span":
            self.in_meta = False
        if tag == "footer":
            self.in_footer = False
        if tag == "details":
            self.in_bg = False
        if tag == "main":
            self.in_main = False
        while self.stack:
            t, _ = self.stack.pop()
            if t == tag:
                break

    def handle_data(self, data):
        if self.in_script:
            return
        if self.in_meta:
            self.meta += data
        if self.buf is not None:
            # skip the <cite> line inside verse boxes
            if any(t == "cite" for t, _ in self.stack):
                return
            self.buf.append(data)


_story_cache: dict[str, tuple[float, dict]] = {}


def load_story(slug: str) -> dict:
    path = REPO / f"{slug}.html"
    if not path.exists() or path.name in SKIP_PAGES:
        raise HTTPException(404, f"no story {slug}")
    mtime = path.stat().st_mtime
    if slug in _story_cache and _story_cache[slug][0] == mtime:
        return _story_cache[slug][1]
    p = StoryParser()
    p.feed(path.read_text(encoding="utf-8"))
    title = next((b["text"] for b in p.blocks if b["kind"] == "title"), slug)
    for i, b in enumerate(p.blocks):
        b["id"] = i
    meta = re.sub(r"\s+", " ", p.meta).strip()
    m = re.search(r"Commentary\s+([\d.]+)", meta)
    story = {"slug": slug, "title": title, "meta": meta, "commentary": m.group(1) if m else "",
             "blocks": p.blocks}
    _story_cache[slug] = (mtime, story)
    return story


def list_stories() -> list[dict]:
    out = []
    for f in sorted(REPO.glob("*.html")):
        if f.name in SKIP_PAGES:
            continue
        head = f.read_text(encoding="utf-8")[:20000]
        if 'class="series"' not in head:
            continue
        t = re.search(r"<title>(.*?)</title>", head)
        m = re.search(r'class="series".*?<span>(.*?)</span>', head, re.S)
        meta = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))) if m else ""
        c = re.search(r"Commentary\s+([\d.]+)", meta)
        out.append({"slug": f.stem, "title": html.unescape(t.group(1)) if t else f.stem,
                    "meta": meta, "commentary": c.group(1) if c else ""})

    def key(s):
        try:
            return tuple(int(x) for x in s["commentary"].split("."))
        except ValueError:
            return (999,)
    return sorted(out, key=key)


# ---------------------------------------------------------------- model management

_model_lock = threading.Lock()
_loaded: dict[str, object] = {}   # key -> model (keep at most 2 resident)


def get_model(key: str):
    from mlx_audio.tts.utils import load_model
    if key not in MODELS:
        raise HTTPException(400, f"unknown model {key}")
    if key not in _loaded:
        while len(_loaded) >= 2:
            _loaded.pop(next(iter(_loaded)))
        _loaded[key] = load_model(MODELS[key]["repo"])
    return _loaded[key]


def model_cached(repo: str) -> bool:
    snap = snapshot_dir(repo)
    return bool(snap) and any(snap.glob("*.safetensors"))


def speakers_for(key: str) -> list[str]:
    if MODELS[key]["mode"] in ("kokoro", "vibevoice"):
        return preset_voices(key)
    if key in _loaded and hasattr(_loaded[key], "get_supported_speakers"):
        return _loaded[key].get_supported_speakers()
    return []


# ---------------------------------------------------------------- takes db

_db_lock = threading.Lock()


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path: Path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    tmp.replace(path)


# ---------------------------------------------------------------- text prep

def speakable(text: str, kind: str) -> str:
    t = text.replace(" / ", ", ").replace("&", " and ")
    t = re.sub(r"\s*—\s*", ", ", t) if kind in ("epigraph",) else t
    t = t.replace("·", ",")
    if kind in ("heading", "title", "dateline", "bg-heading") and not re.search(r"[.!?]$", t):
        t += "."
    return t.strip()


# ---------------------------------------------------------------- API

app = FastAPI(title="Qwen3-TTS dashboard")


class GenReq(BaseModel):
    model: str = "custom-1.7b"
    text: str
    kind: str = "para"
    slug: str | None = None
    block_id: int | None = None
    speaker: str | None = "Ryan"
    instruct: str | None = None
    ref_id: str | None = None
    language: str = "english"
    temperature: float = 0.9
    top_p: float = 1.0
    repetition_penalty: float = 1.05
    seed: int | None = None
    voice_name: str | None = None
    speed: float = 1.0            # Kokoro
    exaggeration: float = 0.5     # Chatterbox
    cfg_weight: float = 0.5       # Chatterbox
    cfg_scale: float = 1.5        # VibeVoice
    ddpm_steps: int | None = None  # VibeVoice


@app.get("/")
def index():
    return FileResponse(HERE / "dashboard.html")


@app.get("/api/stories")
def api_stories():
    return list_stories()


@app.get("/api/story/{slug}")
def api_story(slug: str):
    return load_story(slug)


@app.get("/api/models")
def api_models():
    out = {}
    for k, m in MODELS.items():
        out[k] = dict(m, cached=model_cached(m["repo"]), loaded=k in _loaded, speakers=speakers_for(k))
    return out


@app.post("/api/models/{key}/load")
def api_load(key: str):
    with _model_lock:
        t0 = time.time()
        get_model(key)
        return {"key": key, "seconds": round(time.time() - t0, 1), "speakers": speakers_for(key)}


@app.post("/api/generate")
def api_generate(req: GenReq):
    import mlx.core as mx
    text = speakable(req.text, req.kind)
    if not text:
        raise HTTPException(400, "empty text")
    mode = MODELS.get(req.model, {}).get("mode")
    with _model_lock:
        t_load = time.time()
        model = get_model(req.model)
        t_load = time.time() - t_load
        seed = req.seed if req.seed is not None else int(time.time() * 1000) % 2**31
        mx.random.seed(seed)
        np.random.seed(seed)
        common = dict(text=text, temperature=req.temperature, top_p=req.top_p,
                      repetition_penalty=req.repetition_penalty)
        refs = read_json(REFS_DIR / "refs.json", {})
        ref = refs.get(req.ref_id) if req.ref_id else None
        ref_path = str(REFS_DIR / ref["file"]) if ref else None
        t0 = time.time()
        if mode == "kokoro":
            voice = req.speaker or "am_michael"
            # Kokoro voice prefix picks the accent: a* = American, b* = British
            gen = model.generate(text=text, voice=voice, speed=req.speed,
                                 lang_code=voice[0] if voice[0] in "ab" else "a")
        elif mode == "chatterbox":
            gen = model.generate(text=text, ref_audio=ref_path, exaggeration=req.exaggeration,
                                 cfg_weight=req.cfg_weight, temperature=req.temperature,
                                 top_p=req.top_p, repetition_penalty=max(req.repetition_penalty, 1.0),
                                 verbose=False)
        elif mode == "turbo":
            gen = model.generate(text=text, ref_audio=ref_path, temperature=req.temperature,
                                 top_p=req.top_p, repetition_penalty=max(req.repetition_penalty, 1.0))
        elif mode == "vibevoice":
            gen = model.generate(text=text, voice=req.speaker or None, cfg_scale=req.cfg_scale,
                                 ddpm_steps=req.ddpm_steps)
        elif mode == "custom":
            gen = model.generate_custom_voice(speaker=req.speaker or "Ryan", language=req.language,
                                              instruct=req.instruct or None, **common)
        elif mode == "design":
            if not req.instruct:
                raise HTTPException(400, "VoiceDesign needs a voice description")
            gen = model.generate_voice_design(instruct=req.instruct, language=req.language, **common)
        else:
            if not ref:
                raise HTTPException(400, "voice cloning needs a reference clip")
            gen = model.generate(ref_audio=ref_path, ref_text=ref["text"],
                                 lang_code=req.language, split_pattern="", **common)
        results = list(gen)
        chunks = [np.array(r.audio, dtype=np.float32).reshape(-1) for r in results]
        gen_s = time.time() - t0
        sr = getattr(results[-1], "sample_rate", None) if results else None
        sr = int(sr or getattr(model, "sample_rate", 24000))
    audio = np.concatenate(chunks) if chunks else np.zeros(1, np.float32)
    tid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    sf.write(TAKES_DIR / f"{tid}.wav", audio, sr)
    dur = len(audio) / sr
    take = {
        "id": tid, "file": f"takes/{tid}.wav", "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "slug": req.slug, "block_id": req.block_id, "kind": req.kind, "text": text,
        "model": req.model,
        "speaker": req.speaker if mode in ("custom", "kokoro", "vibevoice") else None,
        "instruct": req.instruct if mode in ("custom", "design") else None,
        "ref_id": req.ref_id if mode in ("clone", "chatterbox", "turbo") else None,
        "voice_name": req.voice_name, "language": req.language,
        "temperature": req.temperature if mode not in ("kokoro", "vibevoice") else None,
        "top_p": req.top_p, "repetition_penalty": req.repetition_penalty, "seed": seed,
        "speed": req.speed if mode == "kokoro" else None,
        "exaggeration": req.exaggeration if mode == "chatterbox" else None,
        "cfg_weight": req.cfg_weight if mode == "chatterbox" else None,
        "cfg_scale": req.cfg_scale if mode == "vibevoice" else None,
        "ddpm_steps": req.ddpm_steps if mode == "vibevoice" else None,
        "sample_rate": sr,
        "duration": round(dur, 2), "gen_seconds": round(gen_s, 2),
        "load_seconds": round(t_load, 1), "rtf": round(gen_s / dur, 3) if dur else None,
        "wpm": round(len(text.split()) / (dur / 60)) if dur > 0.5 else None,
        "rating": 0, "note": "", "pick": False,
    }
    with _db_lock:
        db = read_json(TAKES_DB, [])
        db.append(take)
        write_json(TAKES_DB, db)
    return take


@app.get("/api/takes")
def api_takes(slug: str | None = None):
    db = read_json(TAKES_DB, [])
    return [t for t in db if slug is None or t.get("slug") == slug]


class TakePatch(BaseModel):
    rating: int | None = None
    note: str | None = None
    pick: bool | None = None


@app.patch("/api/takes/{tid}")
def api_patch_take(tid: str, p: TakePatch):
    with _db_lock:
        db = read_json(TAKES_DB, [])
        for t in db:
            if t["id"] == tid:
                if p.pick:  # only one pick per block
                    for o in db:
                        if o.get("slug") == t.get("slug") and o.get("block_id") == t.get("block_id"):
                            o["pick"] = False
                for k, v in p.model_dump(exclude_none=True).items():
                    t[k] = v
                write_json(TAKES_DB, db)
                return t
    raise HTTPException(404)


@app.delete("/api/takes/{tid}")
def api_delete_take(tid: str):
    with _db_lock:
        db = read_json(TAKES_DB, [])
        keep = [t for t in db if t["id"] != tid]
        write_json(TAKES_DB, keep)
    (TAKES_DIR / f"{tid}.wav").unlink(missing_ok=True)
    return {"ok": True}


ASR_REPO = "mlx-community/parakeet-tdt-0.6b-v2"
_asr = None


def _words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", s.lower().replace("’", "'"))


@app.post("/api/takes/{tid}/check")
def api_check_take(tid: str):
    """Transcribe a take with Parakeet and score it against the source text (word error rate)."""
    global _asr
    import difflib
    db = read_json(TAKES_DB, [])
    t = next((x for x in db if x["id"] == tid), None)
    if not t:
        raise HTTPException(404)
    with _model_lock:
        if _asr is None:
            from mlx_audio.stt.utils import load_model as load_stt
            _asr = load_stt(ASR_REPO)
        heard = _asr.generate(str(OUT / t["file"])).text.strip()
    ref, hyp = _words(t["text"]), _words(heard)
    sm = difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False)
    errors = sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")
    diffs = [{"said": " ".join(ref[i1:i2]), "heard": " ".join(hyp[j1:j2])}
             for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
    wer = round(errors / max(len(ref), 1), 3)
    with _db_lock:
        db = read_json(TAKES_DB, [])
        for x in db:
            if x["id"] == tid:
                x.update(asr=heard, wer=wer, asr_diffs=diffs)
                t = x
        write_json(TAKES_DB, db)
    return t


class DeepenReq(BaseModel):
    pitch_st: float = -3.0      # shift of the median pitch, in semitones
    formant: float = 0.94       # formant shift ratio (<1 = larger vocal tract, "bigger" voice)
    pitch_range: float = 0.85   # scale of pitch excursions around the median (<1 = flatter)
    duration: float = 1.0       # >1 = slower


def _median_f0(snd) -> float:
    f = snd.to_pitch_ac(time_step=0.01, pitch_floor=60, pitch_ceiling=500).selected_array["frequency"]
    v = f[f > 0]
    return float(np.median(v)) if len(v) else 0.0


@app.post("/api/takes/{tid}/deepen")
def api_deepen_take(tid: str, p: DeepenReq):
    """Praat "Change Gender" (PSOLA): lower pitch and formants, save the result as a new take."""
    import parselmouth
    from parselmouth.praat import call
    db = read_json(TAKES_DB, [])
    t = next((x for x in db if x["id"] == tid), None)
    if not t:
        raise HTTPException(404)
    if not (0.7 <= p.formant <= 1.3 and -12 <= p.pitch_st <= 12 and 0 <= p.pitch_range <= 2
            and 0.5 <= p.duration <= 2):
        raise HTTPException(400, "settings out of range")
    snd = parselmouth.Sound(str(OUT / t["file"]))
    f0_before = _median_f0(snd)
    if not f0_before:
        raise HTTPException(400, "no voiced speech found")
    out = call(snd, "Change gender", 60, 500, p.formant, f0_before * 2 ** (p.pitch_st / 12),
               p.pitch_range, p.duration)
    audio = out.values[0].astype(np.float32)
    peak = float(np.max(np.abs(audio))) or 1.0
    if peak > 0.99:
        audio *= 0.99 / peak
    sr = int(out.sampling_frequency)
    nid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    sf.write(TAKES_DIR / f"{nid}.wav", audio, sr)
    dur = len(audio) / sr
    f0_after = _median_f0(out)
    label = f"{p.pitch_st:+g} st, formants ×{p.formant:g}, range ×{p.pitch_range:g}" + \
            (f", duration ×{p.duration:g}" if p.duration != 1 else "")
    new = dict(t, id=nid, file=f"takes/{nid}.wav", created=time.strftime("%Y-%m-%d %H:%M:%S"),
               duration=round(dur, 2), sample_rate=sr, rating=0, note="", pick=False,
               wpm=round(len(t["text"].split()) / (dur / 60)) if dur > 0.5 else None,
               parent=tid, processed={"method": "praat-change-gender", **p.model_dump(),
                                      "f0_before": round(f0_before, 1), "f0_after": round(f0_after, 1)},
               voice_name=(t.get("voice_name") or None), gen_seconds=0.0, rtf=0.0)
    for k in ("asr", "wer", "asr_diffs"):
        new.pop(k, None)
    with _db_lock:
        db = read_json(TAKES_DB, [])
        db.append(new)
        write_json(TAKES_DB, db)
    new["label"] = label
    return new


@app.get("/api/refs")
def api_refs():
    return read_json(REFS_DIR / "refs.json", {})


@app.post("/api/refs")
async def api_add_ref(text: str, name: str = "", file: UploadFile = File(...)):
    rid = uuid.uuid4().hex[:8]
    raw = REFS_DIR / f"{rid}.src{Path(file.filename or 'x.wav').suffix}"
    raw.write_bytes(await file.read())
    dst = REFS_DIR / f"{rid}.wav"
    # Qwen3 speaker encoder wants mono 24 kHz
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-ac", "1", "-ar", "24000",
                    str(dst)], check=True)
    raw.unlink()
    refs = read_json(REFS_DIR / "refs.json", {})
    refs[rid] = {"id": rid, "name": name or rid, "text": text, "file": dst.name,
                 "duration": round(sf.info(dst).duration, 1)}
    write_json(REFS_DIR / "refs.json", refs)
    return refs[rid]


@app.post("/api/refs/from-take/{tid}")
def api_ref_from_take(tid: str, name: str = ""):
    """Freeze a take (e.g. a VoiceDesign voice you like) as a clone reference for the Base model."""
    db = read_json(TAKES_DB, [])
    t = next((x for x in db if x["id"] == tid), None)
    if not t:
        raise HTTPException(404)
    rid = uuid.uuid4().hex[:8]
    shutil.copy(OUT / t["file"], REFS_DIR / f"{rid}.wav")
    refs = read_json(REFS_DIR / "refs.json", {})
    refs[rid] = {"id": rid, "name": name or t.get("voice_name") or f"from {tid}", "text": t["text"],
                 "file": f"{rid}.wav", "duration": t["duration"], "from_take": tid}
    write_json(REFS_DIR / "refs.json", refs)
    return refs[rid]


@app.get("/api/voices")
def api_voices():
    return read_json(VOICES_DB, [])


@app.put("/api/voices")
def api_save_voices(voices: list[dict]):
    write_json(VOICES_DB, voices)
    return voices


class RenderReq(BaseModel):
    slug: str
    take_ids: list[str]
    gap_para: float = 0.6
    gap_section: float = 1.6
    fmt: str = "mp3"


@app.post("/api/render")
def api_render(req: RenderReq):
    """Stitch takes (in the given order) into one file, with pauses scaled by block kind."""
    db = {t["id"]: t for t in read_json(TAKES_DB, [])}
    pieces, sr = [], 24000
    for tid in req.take_ids:
        t = db.get(tid)
        if not t:
            continue
        a, a_sr = sf.read(OUT / t["file"], dtype="float32")
        if a.ndim > 1:
            a = a.mean(axis=1)
        if a_sr != sr:  # takes from different models may differ; resample to 24 kHz
            n = int(round(len(a) * sr / a_sr))
            a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)
        gap = req.gap_section if t["kind"] in ("heading", "title", "break", "epigraph") else req.gap_para
        if t["kind"] == "dateline":
            gap = req.gap_para * 1.2
        pieces += [a, np.zeros(int(gap * sr), np.float32)]
    if not pieces:
        raise HTTPException(400, "no takes")
    audio = np.concatenate(pieces)
    stem = f"{req.slug}-{time.strftime('%Y%m%d-%H%M%S')}"
    wav = RENDERS_DIR / f"{stem}.wav"
    sf.write(wav, audio, sr)
    out = wav
    if req.fmt == "mp3":
        out = wav.with_suffix(".mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-codec:a", "libmp3lame",
                        "-q:a", "3", str(out)], check=True)
        wav.unlink()
    return {"file": f"renders/{out.name}", "duration": round(len(audio) / sr, 1)}


app.mount("/audio", StaticFiles(directory=OUT), name="audio")
app.mount("/story", StaticFiles(directory=REPO), name="story")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    uvicorn.run(app, host=a.host, port=a.port)
