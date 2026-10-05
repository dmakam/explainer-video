#!/usr/bin/env python3
"""video.json + build/timeline.json -> build/video.html (self-contained, seekable with setTime(t))."""
import base64, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__)); from common import *
v = load(sys.argv[1]); d = v["_dir"]; out = os.path.join(d, "build")
tl = json.load(open(f"{out}/timeline.json"))
assert len(tl) == len(v["scenes"]), "timeline is stale: run tts.py again after editing scenes"
warns = []
def walk(x):  # enforce price display rule on every displayed string
    if isinstance(x, dict): return {k: (walk(val) if k not in ("image","icon","logo","logos","say") else val) for k, val in x.items()}
    if isinstance(x, list): return [walk(i) for i in x]
    if isinstance(x, str): return fix_price_text(x, warns)
    return x
video = walk({k: val for k, val in v.items() if not k.startswith("_")})
logo_svg = ""
b = video.get("brand", {})
if b.get("logo", "").endswith(".svg") and b.get("logo_mono", False):
    s = open(os.path.join(d, b["logo"])).read()
    s = re.sub(r'fill="(?!none)[^"]*"', 'fill="currentColor"', s)
    s = re.sub(r'(<svg[^>]*?)\s(width|height)="[^"]*"', r"\1", s); s = re.sub(r'(<svg[^>]*?)\s(width|height)="[^"]*"', r"\1", s)
    logo_svg = s.replace("<svg", '<svg height="100%"', 1)
F = f"{CACHE}/fonts"
def ff(name, w, file):
    p = f"{F}/{file}"
    if not os.path.exists(p): return ""
    return f"@font-face{{font-family:'{name}';font-weight:{w};src:url(data:font/woff2;base64,{base64.b64encode(open(p,'rb').read()).decode()}) format('woff2')}}\n"
fonts = "".join(ff("Poppins", w, f"poppins-latin-{w}-normal.woff2") for w in (400, 500, 600)) + ff("Material Icons", 400, "material-icons.woff2")
tpl = open(os.path.join(os.path.dirname(__file__), "..", "template", "engine.html")).read()
html = (tpl.replace("<!--BASE-->", f'<base href="file://{d}/">')
           .replace("/*FONTS*/", fonts)
           .replace("/*CONFIG*/", json.dumps({"video": video, "timeline": tl, "logoSvg": logo_svg})))
open(f"{out}/video.html", "w").write(html)
for w in sorted(set(warns)): print(f"fixed price format: {w}")
print(f"wrote {out}/video.html  ({tl[-1]['start']+tl[-1]['dur']:.1f}s)")
