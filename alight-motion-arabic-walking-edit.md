# Premium Cinematic Arabic Walking Edit — Alight Motion Blueprint

Final format: 1080 × 1920 · 30 fps · 26.03 s · soundtrack = original Arabic audio from Video 2

> **File mapping (verified by probing).**
> - Your upload `Messenger_creation_C9780F53…mp4` = **Video 1** (576×1024, 30 fps, 10.87 s).
> - `7adc3606…mp4` = **Video 2** (1280×720, 30 fps, 26.03 s).
>
> The names 66443/66445 weren't on the files; the specs match your brief exactly.

## What I could and could not verify (read first)
| Item | Status |
|---|---|
| Arabic on-screen text (spelling, order, timing) | **Verified.** Read from enlarged frames; in/out timings measured frame by frame |
| Vocal phrase boundaries | **Verified acoustically.** Every text change lands within 0.03–0.21 s of a deep break in the vocal band |
| Exact Arabic **words** sung, word by word | **Not verified.** Automatic Arabic transcription failed (your ElevenLabs key lacks the `speech_to_text` permission, and offline speech models can't be downloaded here). I can't listen to audio directly. All text below is the original video's own on-screen text, which I did not rewrite. |
| Diacritics (tashkeel) | **Deliberately not added.** E.g. «وجد» could be وَجَدَ (found) or وَجْدُ (longing), and I can't confirm the sung vowelling. Adding unverified harakat would be inventing lyrics. |

---

## A. Video 1 — walking footage
- **Content:** you walk straight toward the camera down the centre of a paved road. You wear a light mint/white printed panjabi and white trousers, with brown sandals.
  - **Left:** a trimmed yellow-green hedge with a white kerb line and black lamp posts.
  - **Behind:** a large stone building with an arched entrance and banners, plus a tall facade of many windows filling the top of the frame. No sky is visible.
- **Camera:** handheld, moving **backward** at your walking pace. You stay roughly the same size the whole time (body centre at x ≈ 47–55 % of frame width, head at y ≈ 46–48 %). Slight natural sway, no cuts (only one scene change detected, the last frame).
- **Lighting:** hard midday sun from above (short shadows under feet). It's bright: average luma ~140/255, with 10 % of pixels above ~185. White clothes and the stone facade sit close to clipping. The hedge is a saturated yellow-green.
- **Action by time (source):**

| Source time | What happens | Use |
|---|---|---|
| 0.00–0.70 | Walking, hands joined at chest | Opening reveal |
| 0.75–3.60 | Hands at chest, adjusting cuffs/fingers while walking | Hands detail, medium shots |
| 3.75–5.00 | Hands drop, relaxed natural stride | Medium / upper-body shots |
| 5.00–6.50 | Arms at sides, calm walk | Wide shots |
| ~7.00 | **Head turns to his left**, a contemplative glance | Best "emotional" beat, medium-close |
| 8.50–10.87 | Looking forward, one hand in pocket near the end | Wide and closing shots |
| **5.5–10.87** | ⚠ **A man in a blue-and-white outfit stands at the right edge** (x ≈ 88–99 %), plus another person after 10.0 s | Must be cropped out: keep the right frame edge ≤ 86 % of source width |

- **Audio in Video 1:** faint ambience only (−27 dB mean). Mute it.
- **Best for slow motion:** the whole clip. The walk is steady and centred. 70 % works. 55 % only with frame interpolation (the source is 30 fps).
- **Limits:**
  - 576×1024 upscaled to 1080×1920 is 1.875×. Push-ins to 175 % total ≈ 3.3× upscale, so they're softer. I keep zoom ≤ 1.85× of source.
  - There's no shot without you, and no sky, so the "establishing" shot is a tilt down the facade.

## B. Video 2 — audio and Arabic text
- **Picture:** black background. One short white Arabic line at the top-centre (≈ y 280–340 px of 720), with emojis under it. Each line **fades in over ≈ 2.4 s** (brightness measured) and **cuts out in one frame**.
- **Audio:** continuous vocal performance with a sustained low drone (~320 Hz band visible in the spectrogram) and rhythmic layered voices. Mean −9 dB, peaks touch 0 dB. Measured pulse **~152 BPM** (≈ 0.40 s); each text line lasts ~8 pulses (≈ 3.2 s).
- **Text and timing (measured):**

| # | Visible (s) | Original text (exact) | Emojis in original | Nearest vocal break (s) |
|---|---|---|---|---|
| 1 | 0.167 – 3.700 | قلبي في المدينه | 🫀🤍 | 3.49 |
| 2 | 3.833 – 6.833 | وجد السكينه | 😍 | 6.71 |
| 3 | 6.933 – 9.833 | قال يا نبينا | 🤗💗 | 9.93 (deepest) |
| 4 | 10.000 – 13.100 | السلام عليك | 💞🫶 | 13.37 |
| 5 | 13.267 – 16.433 | قلبي في المدينه | 🕌🤍 | 16.40 |
| 6 | 16.500 – 19.567 | وجد السكينه | 💜 | 19.60 |
| 7 | 19.733 – 22.967 | محمد نبينا | 🤍 | 22.83 |
| 8 | 23.133 – 26.000 | السلام علينك | 😻💗 | end |

- **Spelling notes (orthography only, words unchanged):**
  - The original writes the final ة as ه («المدينه», «السكينه»). I use the standard **المدينة / السكينة**.
  - Line 8 reads «**علينك**», with an extra ن. The same phrase is spelled «**عليك**» in line 4, so I treat it as a typo and use **السلام عليك**.
  - If you prefer an exact copy of the original spelling, change those three words back.

## C. Creative concept
"A calm walk toward Madinah": no flashy transitions.
- **Hard cuts only, on the vocal phrase breaks**, which are also where the text changes. Each lyric line gets **one shot** with **one slow, motivated camera move**.
- **Structure:**
  - **Opening:** tilt down the facade to reveal you.
  - **Middle:** alternate medium, wide and detail shots so the 10.87 s of footage stretches to 26 s without visible repetition. Any reused source moment comes back with a clearly different framing and is never in adjacent scenes.
  - **Emotional peak:** «محمد نبينا» gets the slowest push-in.
  - **Close:** «السلام عليك» on a pull-back, then a 0.7 s fade with the audio fade.
- **Look:** soft warm daylight, protected highlights, calmer greens, gentle glow and fine grain.
- **Text:** ivory Amiri Bold, centred in the upper third over the building's darker window rows, so it never covers your face or white clothes.

## D. Timeline 00:00 – 00:26.03

Zoom = scale relative to Video 1 filling the 9:16 frame (100 % = 1080 px wide). Position = centre of view as % of the source frame (x from left, y from top). All moves ease in-out (smoothstep), from scene start to scene end.

| Scene | Timeline | Video 1 source | Speed | Arabic text | Sync point | Camera: start → end (zoom, x, y) | Transition in |
|---|---|---|---|---|---|---|---|
| 1 | 0.000 – 3.700 | 0.00 – 2.59 | 70 % | قلبي في المدينة | text in 0.167; vocal break 3.49 | 165 %, 50, 30 → 115 %, 52, 56 (**tilt-down reveal**) | none: opens on picture |
| 2 | 3.700 – 6.833 | 2.59 – 4.78 | 70 % | وجد السكينة | 3.833 | 135 %, 52, 62 → 142 %, 52, 62 (slow push) | hard cut |
| 3 | 6.833 – 9.833 | 4.78 – 6.88 | 70 % | قال يا نبينا | 6.933 | 120 %, 43, 58 → 123 %, 43, 58 (wide; bystander cropped) | hard cut |
| 4 | 9.833 – 13.100 | 6.88 – 9.17 | 70 % | السلام عليك | 10.000; head turn lands ≈ 10.0 | 162 %, 54, 64 → 172 %, 48, 64 (push + follow) | hard cut |
| 5a | 13.100 – 14.767 | 0.30 – 1.50 | 72 % | قلبي في المدينة | 13.267 | 160 %, 53, 69 → 164 %, 52, 69 (lower body / stride) | hard cut |
| 5b | 14.767 – 16.433 | 1.50 – 2.70 | 72 % | (same line continues) | — | 175 %, 51, 58 → 180 %, 52, 58 (hands detail) | hard cut (mid-line, on pulse) |
| 6 | 16.433 – 19.567 | 8.10 – 10.30 | 70 % | وجد السكينة | 16.500; break 16.40 | 120 %, 43, 58 → 125 %, 43, 58 (wide) | hard cut |
| 7 | 19.567 – 22.967 | 3.00 – 5.38 | 70 % | محمد نبينا | 19.733; break 19.60 | 170 %, 53, 62 → 185 %, 52, 62 (**slowest, longest push**) | hard cut |
| 8 | 22.967 – 26.033 | 9.18 – 10.87 | 55 % | السلام عليك | 23.133 | 155 %, 48, 62 → 122 %, 43, 58 (**pull-back ending**) | hard cut. **Fade out to black 25.333 – 26.033** |

Reuse map:
- 0.30–2.70 appears in scenes 1 and 5 (wide reveal vs. stride/hands detail).
- 3.00–4.78 appears in scenes 2 and 7 (142 % vs. 170–185 %).
- 8.10–10.30 appears in scenes 4, 6 and 8 (close vs. wide vs. pull-back).
- No reused section is in neighbouring scenes.

Bystander check: in every scene using source ≥ 5.5 s, the right edge of the view is ≤ 86 % (e.g. scene 3: 43 % + half-width 41.7 % = 84.7 %).

## E. Arabic text synchronisation table

All lines: **Amiri Bold**, ivory **#FAF4E6**, size **96 px** (on 1080 width), centred horizontally, **centre Y = 300 px** (upper third), RTL.

| # | Text displayed | In starts | Fully visible | Out starts | Gone | Entry | Exit |
|---|---|---|---|---|---|---|---|
| 1 | قلبي في المدينة | 0.167 | 0.867 | 3.250 | 3.700 | Fade 0→100 % + rise 26 px + blur 6→0, 0.70 s, ease-out cubic | Fade 100→0 % + rise 10 px, 0.45 s |
| 2 | وجد السكينة | 3.833 | 4.533 | 6.383 | 6.833 | same | same |
| 3 | قال يا نبينا | 6.933 | 7.633 | 9.383 | 9.833 | same | same |
| 4 | السلام عليك | 10.000 | 10.700 | 12.650 | 13.100 | same | same |
| 5 | قلبي في المدينة | 13.267 | 13.967 | 15.983 | 16.433 | same | same |
| 6 | وجد السكينة | 16.500 | 17.200 | 19.117 | 19.567 | same | same |
| 7 | محمد نبينا | 19.733 | 20.433 | 22.517 | 22.967 | same | same |
| 8 | السلام عليك | 23.133 | 23.833 | — | 26.033 | same | **no separate exit**: fades with the picture 25.333–26.033 |

- In-times are exactly the original video's text in-times.
- Out-times end exactly where the original line cuts.
- The text never appears before the original does.
- Emojis are removed: Arabic is the only visible element, as you asked.

## F. Alight Motion layer structure (top → bottom)

```
1  TXT 8  السلام عليك        23.133–26.033
2  TXT 7  محمد نبينا          19.733–22.967
3  TXT 6  وجد السكينة         16.500–19.567
4  TXT 5  قلبي في المدينة     13.267–16.433
5  TXT 4  السلام عليك        10.000–13.100
6  TXT 3  قال يا نبينا         6.933–9.833
7  TXT 2  وجد السكينة          3.833–6.833
8  TXT 1  قلبي في المدينة      0.167–3.700
9  GRAD   top gradient (shape) 0–26.033
10 GRADE  adjustment group: colour + glow + grain + vignette
11 V1-S8 … V1-S1  (9 video layers, Video 1 trimmed per scene)
12 AUDIO  Video 2 audio       0–26.033  (locked)
```

## G. Alight Motion — step by step

**Project**
- **+ → New Project:** ratio 9:16, resolution 1080p (1080×1920), frame rate 30, background black.

**Audio** (do this first, everything syncs to it)
1. **+ → Media →** choose Video 2, place at 0.000.
2. Extract its audio track. Use the audio/extract option on the layer if your version has it; otherwise convert Video 2 to an audio file in another app and import it via **+ → Audio**.
3. Delete or hide Video 2's picture.
4. Lock the audio layer.
5. Add timeline **bookmarks** at 0.167, 3.700, 6.833, 9.833, 13.100, 14.767, 16.433, 19.567, 22.967, 23.133, 25.333.

**Video layers**
1. Import Video 1 nine times, one per scene. On each layer:
   - Trim to the source range in section D.
   - Set **Speed** to the % shown.
   - Place it at its timeline start, then check the layer ends on the bookmark.
2. If your version offers **Frame Blending** in the speed/timing options, turn it on. At 70 % on a 30 fps source it reduces judder. Scene 8 at 55 % needs it. Without it, use 65 % for scene 8 and trim the source in-point to 9.00 s.
3. Mute every Video 1 layer.

**Camera moves** (Move & Transform)
1. On each video layer, add a keyframe at the layer's **first** and **last** frame.
   - **Scale:** start/end zoom from section D.
   - **Position:** at 100 % the 576-wide clip is scaled to fill 1080. To centre source point (x %, y %), offset the layer by (50 − x) % of the scaled width and (50 − y) % of the scaled height.
   - Example, scene 3: x = 43 % at 120 % → move the layer **right** by 7 % × 1296 ≈ **+91 px**.
2. Easing: select both keyframes → **Ease In/Out (Cubic)**.
3. **Motion blur:** use the layer's motion-blur option (or the "Motion Blur" effect if your version has it, shutter ~180°) **only on scene 1** (fast tilt). The other moves are slow enough not to need it.

**Grade group** (one adjustment group over all video layers, so the look is identical everywhere)

| Effect | Setting |
|---|---|
| Exposure | −0.15 EV |
| Brightness / Contrast | Brightness −4, Contrast +6 |
| Highlights (Curves / Levels) | output white 92 % (pull top end down), lift black to 2.5 % |
| Saturation (Hue/Saturation, master) | −10 |
| Green channel / greens | Saturation −25, hue +8° (yellow-green → calmer green) |
| Yellows | Saturation −20 |
| Temperature / Colour balance | Midtones R +4, B −3; Highlights R +3, B −3 (soft warm daylight); Shadows B +2 |
| Sharpen | 20–25 % (low; the source is upscaled) |
| Glow | Threshold 75 %, radius ~25 px, intensity 10 % |
| Grain / Noise | 5 %, animated |
| Vignette | ~20 %, feather high |

**Top gradient** (readability)
- Rectangle 1080 × 620 at the top, linear gradient black 45 % opacity at y = 0 → 0 % at y = 620.
- Keep it on for the whole edit so brightness never jumps.

**Text**
1. Import **Amiri Bold** (`.ttf`, free on Google Fonts) via **Font → Import**. Noto Naskh Arabic SemiBold is the alternative.
2. **+ → Text:** paste the Arabic exactly as in section E. Alight Motion renders RTL automatically; check the letters join (لا ligature, محمد).
3. Size 96, colour #FAF4E6, align centre, X = 540, Y = 300.
4. **Drop shadow:** black, opacity 55 %, blur 10 px, distance 4 px, angle 90°.
5. **Keyframes (in), line 1 example**, with times relative to the layer start:

| Property | Layer start (0.000) | 0.700 s | Easing |
|---|---|---|---|
| Opacity | 0 % | 100 % | ease-out cubic |
| Position Y | 326 | 300 | ease-out cubic |
| Gaussian Blur | 6 px | 0 px | ease-out cubic |

6. **Keyframes (out)** for lines 1–7:

| Property | 0.45 s before layer end | Layer end | Easing |
|---|---|---|---|
| Opacity | 100 % | 0 % | ease-in |
| Position Y | 300 | 290 | ease-in |

   Line 8 has no out keys.
7. **Final fade:** add a black solid at 25.333 with Opacity 0 % → 100 % at 26.033 (linear) above everything. It fades picture and text together.

## H. Colour grading rationale
- **Measured problem:** bright midday light and highlights near clipping on white cloth and stone.
- **The grade:** pulls highlights down (−0.15 EV, white output 92 %), slightly lifts blacks, warms midtones a little, and tames the neon hedge.
- **Result:** the measured average luma across the final edit stays between **101 and 124** in every frame before the final fade, so there are no exposure jumps between scenes.
- **Nothing extreme:** total saturation −10 %, greens −25 %, skin tones untouched.

## I. Audio
- Use only Video 2's audio, untouched in timing. No music replacement, no added sound effects. The track already has a drone and layered voices, so extra whooshes would fight it.
- Fade in **0.15 s** (the voice starts right at 0.0, and this only removes a click).
- Fade out **1.00 s**, 25.033 → 26.033, so it finishes with the picture fade.
- Level: target **−14 LUFS**, true peak ≤ −1.5 dB. The source peaks at 0 dB, so lower its volume about 2–3 dB in Alight Motion. My render measured **−14.0 LUFS, −4.7 dBFS peak**.

## J. Export and QC
- **Export:** Video, 1080p (1080×1920), 30 fps, bitrate ≥ 16 Mbps (Alight Motion "High"), MP4/H.264.

| Check | Result in my render |
|---|---|
| Duration | 26.033 s, the full audio |
| Empty black frames | None, except the intentional final fade (25.33–26.03) |
| Accidental white frames / flashes | None (max luma 124) |
| Bystander visible | Cropped out in every scene ≥ 5.5 s source |
| Text order and timing | 8 lines, the same order and in-times as the original |
| Text readability | Ivory 96 px Amiri on gradient over facade. Never covers face or clothes |
| Only Arabic on screen | Yes. No emojis, no English |
| Exposure consistency | Luma 101–124 across all scenes |
| Audio | Original track, −14.0 LUFS, fades 0.15 s in / 1.0 s out |

**Remaining limitations:** sung words weren't checked word by word (see the top of this document), and close shots are softer because the source is 576 px wide.
