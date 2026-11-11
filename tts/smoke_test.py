"""Smoke test: load Qwen3-TTS (MLX) and render one Dhammapada verse to out/smoke.wav."""
import time, sys
import numpy as np, soundfile as sf
from mlx_audio.tts.utils import load_model

MODEL = sys.argv[1] if len(sys.argv) > 1 else "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
t0 = time.time(); model = load_model(MODEL); print(f"loaded {MODEL} in {time.time()-t0:.1f}s")
print("speakers:", model.get_supported_speakers())
text = ("All that we are is the result of what we have thought: it is founded on our thoughts, "
        "it is made up of our thoughts.")
t0 = time.time()
kw = dict(text=text, language="english")
if "CustomVoice" in MODEL:
    r = list(model.generate_custom_voice(speaker="Ryan", instruct="Calm, unhurried storyteller.", **kw))
elif "VoiceDesign" in MODEL:
    r = list(model.generate_voice_design(instruct="A warm older American man, low and unhurried, reading aloud.", **kw))
else:
    r = list(model.generate(text=text))
audio = np.concatenate([np.array(x.audio) for x in r])
dt = time.time() - t0; dur = len(audio) / model.sample_rate
sf.write("out/smoke.wav", audio, model.sample_rate)
print(f"{dur:.1f}s audio in {dt:.1f}s (RTF {dt/dur:.2f}) -> out/smoke.wav")
