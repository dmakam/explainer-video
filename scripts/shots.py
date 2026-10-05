#!/usr/bin/env python3
"""QA: grab frames at chosen times (or N evenly spaced) and save a contact sheet.
usage: shots.py video.json [t1,t2,... | --every N] [--clean]"""
import asyncio, json, os, sys
from PIL import Image
from playwright.async_api import async_playwright
d = os.path.dirname(os.path.abspath(sys.argv[1])); b = f"{d}/build"; qa = f"{b}/qa"; os.makedirs(qa, exist_ok=True)
tl = json.load(open(f"{b}/timeline.json")); total = tl[-1]["start"] + tl[-1]["dur"]
arg = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--clean") else "--every"
if arg == "--every":
    n = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 0
    ts = [round(s["start"] + s["dur"] * 0.6, 2) for s in tl] if not n else [round(total*(i+.5)/n, 2) for i in range(n)]
else: ts = [float(x) for x in arg.split(",")]
q = "?clean" if "--clean" in sys.argv else ""
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(); pg = await br.new_page(viewport={"width": 1920, "height": 1080})
        await pg.goto(f"file://{b}/video.html{q}"); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(500)
        files = []
        for t in ts:
            await pg.evaluate(f"setTime({t})"); await pg.evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))"); f = f"{qa}/t_{t:07.2f}.jpg"
            await pg.screenshot(path=f, type="jpeg", quality=85); files.append(f)
        await br.close(); return files
files = asyncio.run(main())
W, H = 640, 360; cols = 3; rows = (len(files)+cols-1)//cols
sheet = Image.new("RGB", (W*cols, H*rows))
for i, f in enumerate(files): sheet.paste(Image.open(f).resize((W, H)), ((i % cols)*W, (i//cols)*H))
sheet.save(f"{qa}/sheet.jpg", quality=85)
print(f"{len(files)} frames -> {qa}/sheet.jpg")
