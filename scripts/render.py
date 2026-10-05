#!/usr/bin/env python3
"""Render every frame (1920x1080, JPEG) with parallel headless browsers. Resumable: existing frames are skipped.
usage: render.py video.json [--workers N] [--fps 30] [--clean]"""
import asyncio, json, multiprocessing as mp, os, sys, time
from playwright.async_api import async_playwright
d = os.path.dirname(os.path.abspath(sys.argv[1])); b = f"{d}/build"
def opt(name, default): return type(default)(sys.argv[sys.argv.index(name)+1]) if name in sys.argv else default
FPS = opt("--fps", 30); WK = opt("--workers", max(1, mp.cpu_count()))
CLEAN = "--clean" in sys.argv; fr = f"{b}/frames_clean" if CLEAN else f"{b}/frames"; os.makedirs(fr, exist_ok=True)
tl = json.load(open(f"{b}/timeline.json")); nf = int((tl[-1]["start"] + tl[-1]["dur"]) * FPS)
def worker(w):
    async def run():
        async with async_playwright() as p:
            br = await p.chromium.launch(); pg = await br.new_page(viewport={"width": 1920, "height": 1080})
            await pg.goto(f"file://{b}/video.html{'?clean' if CLEAN else ''}"); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(800)
            await pg.evaluate("setTime(1)"); await pg.evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")  # warm-up paint
            for f in range(w, nf, WK):
                path = f"{fr}/{f:05d}.jpg"
                if os.path.exists(path) and os.path.getsize(path) > 20000: continue
                await pg.evaluate(f"setTime({f/FPS})"); await pg.screenshot(path=path, type="jpeg", quality=93)
            await br.close()
    asyncio.run(run())
if __name__ == "__main__":
    t0 = time.time(); ps = [mp.Process(target=worker, args=(w,)) for w in range(WK)]
    [p.start() for p in ps]; [p.join() for p in ps]
    print(f"{nf} frames in {fr}  ({time.time()-t0:.0f}s, {WK} workers)")
