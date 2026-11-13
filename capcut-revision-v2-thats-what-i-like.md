# Revision v2 — "That's What I Like" music edit (9:16, 11.00 s)

## 0. What was actually uploaded
- `video_20261113_052202.mp4` is **not an edited video**. I measured it: it's 11.87 s, 1280×720 landscape, 60 fps, silent, with no text, no transitions and no cuts. It's a **second raw take** (same room and outfit, different gestures). I call it **Take 2** below.
- `video_20261113_050028.mp4` is byte-identical to the lyric/typography video from last time (11.00 s, contains the song section).
- Your list of problems matches **my previous edit** (`final_edit.mp4`) exactly, so the mistake report below is about that edit. I measured every problem to confirm it.

Sources used:
- **Take 1** = `2026-11-13_04-55-40.mp4` (15.93 s, 1280×720, 60 fps, silent)
- **Take 2** = `video_20261113_052202.mp4` (11.87 s, 1280×720, 60 fps, silent)
- **Song + typography reference** = `video_20261113_050028.mp4`

---

## 1. Mistake report — previous edit (measured, not guessed)

| # | Problem | Evidence | Cause |
|---|---|---|---|
| 1 | Black opening | Frames 0–9 luma ramps 16 → 92 (0.30 s fade from black) | `fade in from black` on frame 0 — wasted the hook |
| 2 | White flash ~2 s | Frame 59 (1.967 s) luma **204** vs 91 on the frame before; repeated at 4.40 s (185), 6.13 s, 8.00 s | 0.13 s white "flash" on every echo line — far too strong and too frequent |
| 3 | Poor text readability | Lyric video overlaid at native 576p → words only ~300 px wide, soft edges, grey "ghost" words, no shadow, sat on light shirt | Screen-blending a low-res lyric video instead of real typography |
| 4 | Split-screen look 3.6–6.1 s (and 7.0–8.0 s) | 16:9 frame in a middle band over its own blurred copy; face ≈ 1/6 of frame height | "WIDE" shots chosen to keep hand gestures |
| 5 | Face not primary | Same shots as #4 | Same cause |
| 6 | Lyric position jumps | Text on blur in wide shots, on shirt in close shots; lyric video is top-anchored so block height changes per phrase | No fixed text anchor |
| 7 | Pink highlights weak | Hot magenta `#E0189C` screen-blended over dark areas → dull; echo lines were inverted + hue-rotated, so their pink shifted | Blend-mode hack, no dedicated accent colour |
| 8 | Dark final frame | Frames 318–329 luma 93 → **22** (fade to black 10.6–11.0 s) | Fade-out to black on a song that is still singing "baby" |
| 9 | Rough transitions | White flashes + jumps between blurred-wide and 267 % close-ups; mirror flip at 1.30 s reads as a glitch | Mixed framings, no motion blur |
| 10 | Lyric sync | Word timing itself was correct (taken from the lyric video), **but** the echo lines looked different (inverted colours) and cuts weren't consistently on beats | Cuts were placed on lyric-video background flips, not measured beats |

---

## 2. Audio analysis (done before placing any cut)
- Tempo **136 BPM** (beat ≈ 0.441 s). Measured beats: 0.42, 0.86, 1.30, 1.74, 2.21, 2.65, 3.09, **3.55**, 3.99, **4.44**, 4.88, **5.32**, 5.78, **6.22**, 6.66, 7.13, 7.57, **8.03**, 8.48, **8.92**, 9.38, 9.82, 10.26 s
- Vocal onsets used for cuts: **1.95 s** ("now"), **7.04 s** ("say")
- Word times (read frame by frame from the lyric video at 15 fps; phrase starts agree with the measured vocal onsets within one frame):

| Phrase | Word in-times (s) |
|---|---|
| take a / look in / that **mirror** | 0.20, 0.40, 0.67, 0.93, 1.13, **1.33** |
| now tell / me who's / the **fairest** | 1.93, 2.13, 2.40, 2.60, 2.73, **3.00** |
| is it / **you** | 3.53, 3.73, **3.93** |
| is it / **you** (echo) | 4.40, 4.60, **4.67** |
| is it / **me** | 5.27, 5.47, **5.67** |
| is it / **me** (echo) | 6.13, 6.33, **6.60** |
| say it's / **us** | 7.00, 7.27, **7.33** |
| say it's / **us** (echo) | 8.00, 8.20, **8.33** |
| and I'll / agree, / **baby** | 8.73, 9.00, 9.33, **10.27** (holds to 11.00) |

---

## 3. Corrected timeline

All shots are **full-frame 9:16, face-centred** (no split screen). In CapCut PC that's the clip at **Scale 267%** in a 9:16 project, with Position X set so your face is centred (values below). **Zoom %** below is on top of that base (100% = 267% in CapCut).

| # | Timeline | Lyric | Source | Source in → out | Speed | Pos X* | Zoom keyframes | Into this shot | Cut synced to |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.000–1.950 | take a look in that **mirror** | Take 2 | 0.30 → 1.93 | **Ramp** 100% (0–0.60) → 60% (0.60–1.40) → 100% (1.40–1.95) | 0 | 0.00 = 110% → 0.30 = 100% (opening settle) → 1.95 = 104% | Opens on picture (no black) | — |
| 2 | 1.950–3.550 | now tell me who's the **fairest** | Take 1 | 10.32 → 11.92 | 100% | 0 | 1.95 = 106% → 2.25 = 100% → 3.55 = 107% (smooth) | Zoom-settle, motion blur | Vocal onset 1.95 |
| 3 | 3.550–4.440 | is it **you** | Take 2 | 3.45 → 4.34 | 100% | −35 | 100% → **4.00 = 106%** → 4.25 = 100% (punch on "you") | Hard cut | Beat 3.55 |
| 4 | 4.440–5.320 | is it **you** (echo) | Take 1 | 4.77 → 5.65 | 100% | +70 | 106% → 4.74 = 100% → 103% | Zoom-settle | Beat 4.44 |
| 5 | 5.320–6.220 | is it **me** | Take 2 | 5.85 → 6.75 | 100% | −30 | 100% → **5.67 = 106%** → 5.92 = 100% | Hard cut | Beat 5.32 |
| 6 | 6.220–7.040 | is it **me** (echo) | Take 1 | 8.75 → 9.57 | 100% | −15 | 106% → 6.52 = 100% → 103% | Zoom-settle | Beat 6.22 |
| 7 | 7.040–8.030 | say it's **us** | Take 1 | 12.81 → 13.80 | 100% | +40 | 100% → **7.33 = 106%** → 7.58 = 100% | Hard cut | Vocal onset 7.04 |
| 8 | 8.030–8.920 | say it's **us** (echo) | Take 2 | 9.45 → 10.34 | 100% | +40 | 106% → 8.33 = 100% → 103% | Zoom-settle | Beat 8.03 |
| 9 | 8.920–11.000 | and I'll agree, **baby** | Take 1 | 14.00 → 15.56 | **75%** (smooth slow-mo, 60 fps source) | −15 | 106% → 9.22 = 100% → 11.00 = 110% (ease-in-out) | Zoom-settle | Beat 8.92 |

\*Pos X is the CapCut position offset (px in the 1080-wide canvas) that puts your face in the centre. **Verify each one by eye.** The goal is your face centred, never cut by the frame edge.

Why these moments (all real footage, nothing invented):
- **#1:** both hands rise into a "frame/mirror" gesture (Take 2, 0.8–1.4 s). The 60 % ramp holds it under "look in that mirror".
- **#2:** your biggest natural smile (Take 1, 11.3–11.5 s) lands on "fairest" (3.00 s).
- **#3:** finger point and smile toward camera (Take 2, 3.7–4.3 s) on "you".
- **#4:** face turned to camera, talking (Take 1, 5.0–5.5 s).
- **#5:** thumb toward yourself (Take 2, 6.1–6.8 s) on "me".
- **#6:** thumb toward yourself (Take 1, 9.0–9.5 s) on the echo "me".
- **#7:** laugh while pointing aside (Take 1, 13.0–13.2 s) on "us".
- **#8:** your biggest laugh (Take 2, 9.7–9.9 s) on the echo "us".
- **#9:** relaxed soft smile in slow motion for the ending. It ends on your face, not black.

Trade-off: a 9:16 crop of 720p footage is narrow, so some hand gestures (thumb at #5, point at #7) are partly outside the frame. I kept your face as the priority, as you asked.

---

## 4. CapCut PC — step by step

### 4.1 Project
1. New project. Import Take 1, Take 2 and the lyric video.
2. Player → **Ratio 9:16**. Settings → frame rate **30 fps**.
3. Drag the lyric video to the timeline. Right-click → **Extract audio**. Delete the lyric video's picture. You only keep its audio (the song).
4. Lock the audio track. Optional: right-click the audio → **Beats → Auto beat** to show beat markers. They should land on the beat times in section 2.

### 4.2 Shots
For each row in the table:
1. Drag the source onto the main track. Use **Split** (Ctrl+B) at the source in/out times, delete the unused parts, and butt the clips together.
2. **Video → Basic → Transform → Scale 267%**, then set Position X from the table.
3. **Speed:**
   - Shot 1: **Speed → Curve → Custom.** Set the curve flat at 1.0× until 0.60 s, dip to 0.6× from 0.60–1.40 s, back to 1.0× by 1.95 s. Turn on **Smooth slow-mo**.
   - Shot 9: **Speed → Normal 0.75×**, with **Smooth slow-mo** on.
   - Check after setting the speed that each clip still ends exactly at its timeline time.
4. **Zoom keyframes:**
   - Click the ◇ keyframe next to Scale at each time in the table.
   - Convert the % values to Scale: 100% = 267, 103% = 275, 104% = 278, 106% = 283, 107% = 286, 110% = 294.
   - Right-click each keyframe → **Ease out** for punches and settles, **Ease in-out** for the slow pushes.

### 4.3 Motion blur and transitions
- **No** white flash, **no** fade from black, **no** fade to black.
- **Zoom-settle shots (2, 4, 6, 8, 9):** add **Effects → Video effects → Basic → Motion blur** (or "Blur" if your version names it so) on the first **0.25 s** of the clip only, intensity 35–40. Combined with the 106%→100% keyframe, this gives a smooth push-in transition without white frames.
- **Punch shots (3, 5, 7):** hard cut, plus the same Motion blur effect over the 0.25 s punch window.

### 4.4 Colour grade
Put an **Adjustment layer** across 0–11.00 s so every shot gets the identical grade:

| Setting | Value |
|---|---|
| Exposure | +5 |
| Contrast | +8 |
| Saturation | −7 |
| Brightness | +4 |
| Highlights | −12 |
| Shadows | +10 |
| Temperature | +6 |
| Tint | +6 (towards magenta, for soft pink) |
| Fade | +8 (lifted blacks) |
| Sharpen | +12 |
| Vignette | +12 (keep it light so the face isn't darkened) |
| Grain | +12 |
| HSL Orange | Lum +6, Sat −5 (skin) |
| HSL Purple/Magenta | Sat +8 (monitor glow) |

**Match exposure per clip:** before grading, compare skin brightness clip to clip. In my measurements the shots ranged 77–93 average luma, so I adjusted each one to about 85. In CapCut, use **Adjust → Exposure** on the individual clip (about ±5) until skin looks the same across cuts.

### 4.5 Light and film effects
- **Glow:** Effects → Lens → **Soft glow**, intensity 15, on the adjustment layer.
- **Light leak:** Effects → Light → a soft **pink light leak**, opacity 20–25%, only on 0–1.5 s (opening), 2.6–3.4 s ("fairest") and 9.6–11.0 s (ending). Avoid strong white leaks.

### 4.6 Lyrics (typography)
Rebuild the lyrics as sharp CapCut text instead of overlaying the low-res lyric video. The look, line breaks and word timings come from that video.

- **Font:** a soft heavy serif. I used **Fraunces Black** (free, Google Fonts). In CapCut PC pick a similar heavy serif if Fraunces isn't available.
- **Size:** about 104 px on a 1080-wide canvas. Line spacing ~112 px. Centred. Lowercase, but with correct apostrophes: who's, it's, I'll.
- **Colours:** white `#FFFFFF`. Accent words **mirror, fairest, you, me, us, baby** in soft pink `#FF9ECD`, plus a pink **Glow** (colour `#FF78BE`, blur ~16, opacity ~75%).
- **Shadow** on all text: black, opacity 65%, blur 9, distance 5, angle 90°.
- **Fixed anchor:** every phrase block is centred on **Y = 1500 px** (lower third, below your chin). Never move it between phrases.
- **Readability:** add a black → transparent gradient (Stickers/Shapes, or an overlay PNG) on the bottom ~45% of the frame, max 50% opacity. Keep it on for the whole edit so the exposure never jumps.
- **Word-by-word animation:**
  - Make one text layer per word.
  - Start each layer at its in-time from section 2.
  - Animation **In → "Fade in" + "Rise"/"Slide up", duration 0.20 s.** It rises ~22 px with an ease-out.
- **Phrase exit:** Animation **Out → Fade out 0.14 s**, ending exactly at the next phrase's first word (e.g. "mirror" phrase out at 1.79–1.93). The last phrase does **not** fade; it holds to 11.00 s.

### 4.7 Audio
- Song only (both takes are silent, so mute their tracks).
- **Fade in 0.12 s** (the first sung word is at 0.20 s). **Fade out 0.40 s** (10.60 → 11.00) so the end is clean but the picture stays on your face.
- Volume about 85–90 %. Target −14 LUFS, true peak ≤ −1.5 dB. My render measured **−13.8 LUFS, −2.9 dBFS peak**.

### 4.8 Export
1080 × 1920 · 30 fps · H.264 · bitrate "Higher" (or ≥ 16 Mbps) · AAC 256 kbps · MP4.

---

## 5. Quality-control checklist (results from my render)

| Check | Result |
|---|---|
| Empty black frames | **0** (blackdetect, pix_th 0.10). Min luma 69.7 over all 330 frames. First frame = your face. |
| Accidental white frames | **0** (max frame luma 84.9; previous edit peaked at 204) |
| Unreadable text | Text ≥ 104 px, shadow + gradient behind it, sharp vector font |
| Split-screen layouts | **None.** All 9 shots are full-bleed 9:16 |
| Sudden exposure changes | Shots matched to ~85 luma in two passes. Remaining whole-frame jumps (≤ 12 at 1.95, 4.44, 7.04, 8.03 s) come from framing (more white headset/shirt in frame), not skin exposure. Skin tone checked visually across each cut. |
| Inconsistent grade | One grade over the whole edit |
| Lyric order / timing | All 9 phrases in order, word in-times from the lyric video, pink accents on the right words |
| Unfinished ending | Ends on your smile + "and I'll agree, **baby**" fully visible, audio fades over the last 0.40 s |
| Format | 1080×1920, 30 fps, 11.00 s, H.264 + AAC |

### Known limitations
- 720p landscape source cropped to 9:16 = 2.67× upscale. It's sharpened but still softer than native vertical 1080p. Filming vertically next time fixes this completely.
- Some hand gestures fall partly outside the frame because your face was prioritised.
