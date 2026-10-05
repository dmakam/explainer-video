---
name: explainer-video
description: Turn a product page, doc or brief into a narrated, captioned explainer video (MP4) with a free local AI voice and animated scenes. Use when someone asks for a product video, explainer, walkthrough or narrated overview.
license: MIT
---

# Explainer video

This skill makes a 30-second to 3-minute 1080p explainer video with narration, burned-in captions and animated scenes. The voice is free and runs locally, so the only cost is the tokens used to write the script.

**How it works:** you write one `video.json` file containing the script and the scenes. The scripts turn it into an MP4. You never hand-write animation code: the engine in `template/engine.html` handles layout, motion, captions and timing. This keeps token use low, because most of the work is a small JSON file.

```
video.json ──tts.py──▶ narration.wav + timeline.json (exact per-sentence timing)
           ──build.py─▶ video.html (seekable: setTime(t))
           ──shots.py─▶ QA contact sheet  ──render.py─▶ frames ──encode.sh─▶ MP4
                                                              └──web.sh──▶ 720p MP4/WebM + poster + embed
```

## Workflow

1. **Brief (one message).** Ask only what changes the build:
   - Who the audience is: customers, sales or support enablement, or leadership.
   - Target length. The default is 60 to 150 seconds.
   - Whether any numbers must be left out.
   - Whether real product screenshots exist.

   Then send a one-line-per-scene storyboard and build. Don't loop for approval on wording; people react better to a rendered video.
2. **Gather material.** Get the facts from the source page or doc only, and never invent features. Collect screenshots (PNG) and a logo, plus a white or one-colour logo version for dark backgrounds. Flag it to the user if the source contradicts itself.
3. **One-time setup:** `bash scripts/setup.sh`. This installs kokoro-onnx, Playwright, the voice model, and the Poppins and Material Icons fonts into `~/.cache/explainer-video`. `ffmpeg` is also required.
4. **Write `video.json`.** See the schema below and `examples/demo.json`.
5. **Run the narration:** `python3 scripts/tts.py video.json`. It prints each scene's length, so adjust the script until the total fits.
6. **Build and check:** run `python3 scripts/build.py video.json`, then `python3 scripts/shots.py video.json` (one frame per scene, or `--every 12`). Look at `build/qa/sheet.jpg` and fix anything wrong before rendering.
7. **Render:** `python3 scripts/render.py video.json --workers N`. It is resumable, and roughly 1 minute of video takes about 3 minutes on 2 CPUs. Then run `bash scripts/encode.sh video.json`.
8. **Web copies, if the video goes on a page:** `bash scripts/web.sh video.json [poster-seconds]`. This makes the 720p MP4 and WebM, a poster image, and a `preload="none"` embed snippet.
9. **Deliver one MP4 by default.** Check it with `ffprobe` and a few frames pulled from the MP4 itself.

## video.json schema

```jsonc
{
  "title": "Product name",                 // shown top-right with "tag"
  "tag": "Product overview",
  "output": "Product-Overview",            // output file name
  "currency": "USD", "locale": "en-US",
  "brand": {
    "name": "Acme", "logo": "assets/logo.svg",
    "logo_mono": true,                     // recolour an SVG logo to white for the dark background
    "font": "Poppins",
    "colors": { "bg1": "#0B1026", "bg2": "#1B1F4B", "primary": "#5B6CFF", "accent": "#22D3EE" }
  },
  "voice": { "name": "bm_fable", "lang": "en-gb", "speed": 1.1 },
  "spell_out": ["AI", "SEO"],              // acronyms the voice should spell out
  "scenes": [ { "type": "...", "lines": [ { "text": "Caption and narration.", "say": "optional spoken override" } ] } ]
}
```

Each **line** is one sentence. It appears as a caption and is spoken, and scene elements appear when their line starts. Use `*word*` in headlines for the gradient accent and `\n` for a line break.

| type | fields | how lines drive it |
| --- | --- | --- |
| `title` | eyebrow, headline, sub, logos[], price, chip | headline first; chip on the last line |
| `cards` | eyebrow, headline, items[{icon, title, text, at?}] (≤4) | each card lights up on its line |
| `screenshot` | eyebrow, headline, image, aspect, focus{x,y,w,h,at,zoom?}, items[] (≤3) | ring or zoom on `focus` at line `at`; side cards follow the lines |
| `grid` | eyebrow, headline, items[] (3–4) | each column lights up on its line |
| `compare` | eyebrow, headline, columns[{name, image}], pick, pickLabel | answers fill on line 2; the pick badge comes after |
| `pricing` | headline, plans[{name, desc, price, features[], badge, cta}] (≤3) | plans rise in at the scene start |
| `end` | headline, url | logo, headline and URL |

- `icon` is a [Material Icons](https://fonts.google.com/icons) name (`"lock"`) or an image path (shown on a white tile).
- `focus` coordinates are fractions (0–1) of the screenshot.
- `at` overrides which line (0-based) an item appears on. By default, items map to lines in order.

## Rules that matter

- **Prices:** whole amounts never show decimals (**$20/mo**, never $20.00 or $20.0). Amounts with cents show exactly two digits ($14.50). `price` objects (`{"amount": 20, "period": "mo"}`) are formatted automatically, and any `$20.00` typed in text is corrected at build time with a warning. Narration says "20 dollars a month".
- **Logos:** use each brand's real logo file in its original colours; never redraw or recolour other companies' logos. Only your own logo is recoloured, and only with `logo_mono`. Check the owner's brand guidelines before using third-party marks.
- **Facts:** use only what the source says. Keep internal or confidential numbers out unless the requester explicitly wants them.
- **Layout:** keep content above y ≈ 900, because two-line captions take the bottom band. Prefer 3–4 items per scene, 1–4 lines per scene, and under 20 words per line.
- **Length:** at speed 1.1, about 150 spoken words is about 1 minute.
- **Disclosure:** when sharing, say the narration is an AI voice (Kokoro, Apache-2.0).

## Extending the engine

Each scene type is one function in `template/engine.html` (`B.<type>`) that returns `{html, animate(el, sceneStart, lineStarts)}`. Animations use the Web Animations API with absolute delays, so the page can be seeked to any frame. Three rules keep it seekable:

- Entrances use `fill:'both'` and exits use `fill:'forwards'`.
- Floats use the separate `translate`/`scale` properties, so they don't fight `transform`.
- Never centre an element with `transform` if that element's transform is also animated.

## Troubleshooting

- **Headline missing in a QA frame:** the first screenshot after page load can be stale. The scripts already wait two animation frames before shooting.
- **A long render was killed by a tool timeout:** run it detached (`setsid nohup … &`) and poll. `render.py` skips frames it has already made.
- **Words pronounced wrongly:** add `"say"` to that line, or add the term to `spell_out`.
- **File too big to share:** use `web.sh`, or raise the CRF in `encode.sh`.
