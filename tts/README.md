# Narration Bench: local TTS for *Walking the American Way*

A local dashboard for auditioning text-to-speech voices on the stories, running on Apple
Silicon through [mlx-audio](https://github.com/Blaizzy/mlx-audio). Built around
[Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS), with other local models alongside for
comparison:

| Model | Key in dashboard | Voices | Notes |
|---|---|---|---|
| Qwen3-TTS CustomVoice 1.7B | `custom-1.7b` | 9 presets (Ryan, Aiden native English) | style instruction |
| Qwen3-TTS VoiceDesign 1.7B | `design-1.7b` | described in words | voice drifts between paragraphs; freeze one with *Make clone ref* |
| Qwen3-TTS Base 1.7B | `base-1.7b` | cloned from a clip + transcript | |
| Kokoro 82M | `kokoro` | 54 presets (`a*` American, `b*` British) | ~30× real time, very stable, no cloning |
| Chatterbox | `chatterbox` | built-in or cloned | *exaggeration* (expressiveness), *CFG weight* (lower = slower pacing) |
| Chatterbox Turbo | `chatterbox-turbo` | built-in or cloned | faster; tends to read fast |
| VibeVoice Realtime 0.5B | `vibevoice` | presets (`en-Carter_man`, `en-Emma_woman`, …) | the long-form 1.5B/7B have no official MLX build |

## Setup (once)

```sh
cd tts
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python mlx-audio soundfile fastapi uvicorn python-multipart "misaki[en]"
brew install ffmpeg            # for clone references and mp3 export
```

Models download from Hugging Face the first time they are loaded (about 3.8 GB each for
Qwen 1.7B bf16, 0.3–2.4 GB for the others; the Check button pulls Parakeet, 1.2 GB). If a
download stalls, fetch it over plain HTTP instead:

```sh
HF_HUB_DISABLE_XET=1 .venv/bin/hf download mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16
```

## Run

```sh
tts/.venv/bin/python tts/server.py      # from the repo root
open http://localhost:8765
```

`tts/smoke_test.py [model-repo]` renders one verse to `tts/out/smoke.wav` as a sanity check.

## What it does

- **Stories**: every story page in the repo, sorted by commentary number. Each page is split
  into blocks (title, epigraph, "heard" line, section heading, dateline, paragraph, verse) in
  reading order; tick **Background** to include the end notes.
- **Voice**: three model families.
  - *CustomVoice*: nine preset speakers (Ryan and Aiden are the native-English ones) plus an
    optional style instruction.
  - *VoiceDesign*: describe the voice in words.
  - *Base*: clone a voice from a 5–20 s reference clip plus its exact transcript. **Make clone
    ref** on any take turns it into a reference, so a voice found with VoiceDesign can be
    locked for a whole story.
  Save settings as named voices; checked voices are used by **A/B checked voices**.
- **Takes**: every render is kept with its full settings, seed, duration, real-time factor and
  words per minute. Rate 1–5, add notes, **Pick** the keeper for each block, or **Reuse** a
  take's exact settings (seed included) to re-render.
- **Check**: transcribes a take with Parakeet ASR and compares it to the source text, giving a
  word error rate and the words that differ (`gold → bowl`). Catches skipped or misread
  words without listening to everything; an occasional hit is the transcriber's mistake.
- **Deepen…**: lowers a take's pitch and formants with Praat's *Change Gender* (PSOLA) and saves
  the result as a new take beside the original. Presets: subtle (−2 st, formants ×0.96),
  deeper (−3 st, ×0.94), heavy (−5 st, ×0.90); *range* below 1 flattens intonation. Lowering
  formants with the pitch is what makes it sound like a bigger voice rather than a slowed one.
  For a whole story, deepen one good take, **Make clone ref** from it, and render with the Base
  model: clones of a −3 st reference came out about 2 st lower than clones of the original,
  as fresh renders rather than processed audio.
- **Compare**: per-voice averages of rating, WER, speed and pace for the current story.
- **Export**: stitch the picked takes (or best-rated as fallback) into one mp3/wav with
  pauses between paragraphs and sections.

Keys: `j`/`k` move between blocks, `r` renders, space plays the top take.

All output lives in `tts/out/` (gitignored): `takes/*.wav`, `takes.json`, `voices.json`,
`refs/`, `renders/`.
