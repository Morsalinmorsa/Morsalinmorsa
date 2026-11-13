# CapCut Edit Guide — "That's What I Like" (Take a look in that mirror → And I'll agree, baby)

Format: 9:16 · 1080×1920 · 11.00 s · 136 BPM (one beat ≈ 0.44 s)

## What I found in your footage (frame-by-frame analysis)

**Video 1** (`2026-11-13_04-55-40.mp4`) — 15.93 s, 1280×720 landscape, 60 fps, **no audio** (silent track).
You in white headset, mint-striped shirt, dark room lit by blue/purple monitor glow, keyboard lights bottom-right. One continuous take, no cuts.

| Source time | What happens |
|---|---|
| 0.00–3.00 | Calm, looking off to the right at the screen, minimal movement — moody intro material |
| 3.40–4.20 | Both hands come up, index fingers pointing, leaning in |
| 4.90–5.10 | **Points toward camera** (left hand, frame-left) |
| 5.50 | Finger raised, face turned to camera |
| 6.80–7.10 | **Points toward camera again**, half-smile |
| 7.50 | Squint / smirk |
| 9.00–9.50 | **Thumb pointing at himself** |
| 11.00–11.50 | **Biggest natural smile**, looking right |
| 12.00–12.80 | Leans in, talking animatedly |
| 13.00–13.20 | **Points to the side + smiles/laughs** |
| 13.50–15.93 | Leans back, relaxed soft smile — perfect ending |

**Video 2** (`video_20261113_050028.mp4`) — 11.00 s, 1024×576, 30 fps, **contains the exact song section** you asked for (−11.6 dB mean, peaks hit 0 dB).
It's a kinetic-typography lyric video: words pop in one at a time, background flips black ↔ white on each phrase, key words in hot pink, small pink ★ at the bottom.

Phrase/background flips I measured (these become your cut points):

| Song time | Background | Lyric on screen |
|---|---|---|
| 0.00 | black | "take a look in that mirror" (words at 0.33 / 0.67 / 1.00 / 1.33) |
| 1.967 | white | "now tell me who's the fairest" ("fairest" pink at 3.00) |
| 3.567 | black | "is it you" ("you" at 4.00) |
| 4.400 | white | "is it you" (echo) |
| 5.267 | black | "is it me" ("me" at 5.67) |
| 6.133 | white | "is it me" (echo) |
| 7.000 | black | "say it's us" ("us" at 7.33) |
| 8.000 | white | "say it's us" (echo) |
| 8.767 | black | "and I'll agree" → "baby" (pink, at 10.33) — energy rises from 9.75 |

> Song time = Video 2 time. Use Video 2's audio as your music track — it's already trimmed to exactly your section.

---

## 1. Project setup
1. New project → import **Video 2 first**, then Video 1.
2. Tap **Ratio → 9:16**.
3. **Canvas → Blur** (level 3) — used behind the WIDE shots.
4. Select Video 2 on the main track → **Extract audio**. Then keep Video 2's *video* as an overlay (step 4), and remove it from the main track.

## 2. Two framings you'll use
- **CLOSE** = Video 1 scaled to **267%**, position X ≈ **+40** (face centred; your face sits slightly left of the source centre). Fills the 9:16 frame — intimate, cinematic.
- **WIDE** = Video 1 at **100%** (full landscape frame) on the blurred canvas — keeps your hand gestures in shot.

## 3. Complete timeline (cut list)

Split Video 1 into these pieces and place them back-to-back on the main track. **Out** = position in final edit; **Source** = where to trim from in Video 1.

| # | Out (start–end) | Lyric | Source (Video 1) | Framing | Keyframes / effect |
|---|---|---|---|---|---|
| 1a | 0.000–1.300 | take a look in that… | 0.000–1.300 | CLOSE | Scale KF 267% → 278% (slow push). Fade in from black 0.3 s |
| 1b | 1.300–1.967 | …**mirror** | 1.300–1.967 | CLOSE | **Edit → Mirror** (horizontal flip) — the frame literally mirrors on "mirror". Continue push 278% → 283% |
| 2 | 1.967–3.567 | now tell me who's the **fairest** | 10.333–11.933 | CLOSE | White **Flash** in (0.13 s). Push 267% → 283%. Your big smile (src 11.37) lands exactly on "fairest" (3.00) — add Effect **Lens → Glow / "Soft glow"** 2.9–3.6 s, intensity 30 |
| 3 | 3.567–4.400 | is it **you** | 4.550–5.383 | WIDE | **Zoom punch** on "you": KF at 4.00 = 100%, 4.03 = 106%, 4.30 = 100% (ease out) |
| 4 | 4.400–5.267 | is it you (echo) | 6.550–7.417 | WIDE | White Flash in. Your second point at camera (src 6.9–7.0) lands on the echo "you". Punch at 4.67 (same values) |
| 5 | 5.267–6.133 | is it **me** | 8.600–9.467 | WIDE | Thumb-to-self (src 9.0) lands on "me" (5.67). Punch at 5.67 |
| 6 | 6.133–7.000 | is it me (echo) | 9.467–10.333 | CLOSE | White Flash in. **Cut-in** from wide → close on the same moment (match cut). Push 267% → 280% |
| 7 | 7.000–8.000 | say it's **us** | 12.700–13.700 | WIDE | Side-point + smile (src 13.0–13.2) lands on "us" (7.33). Punch at 7.33 |
| 8 | 8.000–8.767 | say it's us (echo) | 11.933–12.700 | CLOSE | White Flash in. Push 267% → 280% |
| 9 | 8.767–11.000 | and I'll agree, **baby** | 13.700–15.933 | CLOSE | Long slow push 267% → 300% (ease in-out). Glow 30 from 10.2 s ("baby"). **Fade to black** 10.60–11.00 |

Every clip is at **100% speed** — your expressions stay natural and the gestures land on the words. (Video 1 is 60 fps, so if you ever want a slow-mo variant, clip 9 at 0.8× with **Smooth slow-mo** still looks clean.)

### Why it's built this way
- Cuts sit exactly on the lyric video's phrase flips, so picture changes when the vocal phrase changes — every 2 beats (~0.87 s) in the middle section, giving rhythm.
- **Black-background lines = WIDE / new info, white-background echoes = CLOSE + white flash** (except clip 4). The white flash mirrors the lyric video's black→white flip.
- Lyrics about *you / me / us* are matched to your real gestures (point at camera / thumb at self / point to side). Nothing staged, nothing invented.

## 4. Lyric overlay (combining Video 2)
1. Add Video 2 as **Overlay**, aligned at 0.000. Scale so it's **1080 px wide** (≈105%), position Y so the text block sits in the **lower third** (text ≈ y 1355–1650 of 1920 — below your face, over the shirt / blur).
2. Split the overlay at **1.967, 3.567, 4.400, 5.267, 6.133, 7.000, 8.000, 8.767**.
3. Black-background pieces (0–1.967, 3.567–4.4, 5.267–6.133, 7.0–8.0, 8.767–end): **Blend → Screen** → black disappears, white + pink text floats on your footage.
4. White-background pieces (1.967–3.567, 4.4–5.267, 6.133–7.0, 8.0–8.767): first add **Effects → Basic → Invert** (turns white bg black and text white) then **Blend → Screen**. If your CapCut version has no Invert effect, use **Blend → Multiply** instead (text shows dark) — or hide those pieces and keep only the black-bg phrases.
5. Optional extra: on "fairest" (3.0 s) and "baby" (10.33 s) add a tiny **Sparkle / Star** sticker near the pink word, 0.5 s, scale-in animation — echoes the pink ★ in the lyric video.

## 5. Colour grading (apply as an Adjustment layer over the whole timeline)
Your source is dark, with a blue/purple cast from the monitor on your face. Goal: lift it, warm the skin, keep the moody purple/blue room glow.

| Setting | Value |
|---|---|
| Brightness | +8 |
| Contrast | +12 |
| Saturation | −5 |
| Exposure | +6 |
| Highlights | −10 |
| Shadows | +15 |
| Temperature | +8 (warm skin) |
| Tint | +5 (slight magenta, romantic) |
| Fade | +6 (lifted blacks, filmic) |
| Sharpen | +15 (needed — CLOSE shots are upscaled) |
| Vignette | +20 |
| Grain | +10 |
| HSL → Orange | Saturation −5, Luminance +8 (skin) |
| HSL → Blue/Purple | Saturation +10 (keep the monitor glow) |

Optional filter on top: **Movies → "Hong Kong"** or **Retro → "Film"** at **25–30%**.
Add Effect **Lens → Glow** (or "Soft glow") at intensity ~20 across the whole edit for the dreamy bloom.

## 6. Transitions summary
- 0.000: Fade in from black (0.3 s)
- 1.300: no transition — Mirror flip IS the transition
- 1.967, 4.400, 6.133, 8.000: **Flash / "White flash"** 0.1–0.15 s
- 3.567, 5.267, 7.000, 8.767: **hard cuts** (cleaner, hits the downbeat)
- 10.60–11.00: Fade out to black

Don't add more transitions than this — the lyric typography already supplies motion.

## 7. Audio mixing
- Music = audio extracted from Video 2 (Video 1 is silent, so nothing to duck).
- Volume ≈ **85–90**. Video 2 peaks at 0 dB, so turn it down slightly to avoid clipping.
- **Fade in 0.05 s, fade out 0.45 s** (10.55 → 11.00).
- Mute Video 1's track and the Video 2 overlay track (so audio isn't doubled).
- Target if you check: −14 LUFS, true peak ≤ −1 dB. (My render measured **−13.8 LUFS / −2.9 dB peak**.)

## 8. Export
- Resolution **1080p**, Frame rate **30 fps**, Bitrate **Higher / Recommended+**, Codec **H.264**, Format MP4.
- Upload to TikTok/Reels with "High quality upload" turned on.

---

### Honest limitations
- Video 1 is only 720 px tall, so CLOSE shots are a 2.67× upscale — slightly soft. Sharpen +15 helps; re-filming in 4K or vertical would fix it.
- I matched cuts to the vocal phrases and beats measured from Video 2's audio. If you replace the audio with a different copy of the song, re-align it so "take" hits ≈ 0.33 s.
