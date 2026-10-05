#!/usr/bin/env python3
"""video.json -> build/narration.wav + build/timeline.json (per-sentence timing for exact captions).
Each scene line: {"text": "...shown as caption..."} and optionally "say": "...spoken override...".
"""
import json, os, sys, numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(__file__)); from common import *
from kokoro_onnx import Kokoro
v = load(sys.argv[1]); out = os.path.join(v["_dir"], "build"); os.makedirs(out, exist_ok=True)
vc = {"name": "bm_fable", "lang": "en-gb", "speed": 1.1, **v.get("voice", {})}
k = Kokoro(f"{CACHE}/kokoro.onnx", f"{CACHE}/voices.bin")
SR, GAP, LEAD, TAIL = 24000, 0.22, 0.35, 0.7
acr = v.get("spell_out", [])
tl, audio, t, warns = [], [], 0.0, []
for i, sc in enumerate(v["scenes"]):
    seg = [np.zeros(int(LEAD*SR), np.float32)]; lt = LEAD; caps = []
    for ln in sc.get("lines", []):
        show = fix_price_text(ln["text"], warns)
        say = ln.get("say") or spoken(show, acr)
        a, _ = k.create(say, voice=vc["name"], speed=vc["speed"], lang=vc["lang"])
        nz = np.where(np.abs(a) > 0.008)[0]; a = a[max(0, nz[0]-600):nz[-1]+1200].astype(np.float32)
        d = len(a)/SR; caps.append({"show": show, "say": say, "start": t+lt, "end": t+lt+d})
        seg += [a, np.zeros(int(GAP*SR), np.float32)]; lt += d+GAP
    if not caps: lt += sc.get("hold", 3.0)
    seg.append(np.zeros(int((TAIL + (0 if caps else sc.get("hold", 3.0)))*SR), np.float32)); lt += TAIL
    tl.append({"scene": i, "type": sc["type"], "start": t, "dur": lt, "caps": caps}); audio += seg; t += lt
    print(f"scene {i+1:2d} {sc['type']:<10} {lt:5.1f}s")
sf.write(f"{out}/narration.wav", np.concatenate(audio), SR)
json.dump(tl, open(f"{out}/timeline.json", "w"), indent=1)
for w in sorted(set(warns)): print(f"fixed price format: {w}")
print(f"total {t:.1f}s  ({t/60:.1f} min)")
