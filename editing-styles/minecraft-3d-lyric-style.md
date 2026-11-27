# Morsalin's reference style: "3D world kinetic lyric video"

This is the editing style Morsalin asked to be remembered and copied ("make it the same as this video").
The reference was a 60 s square video: a Minecraft-style 3D animated lyric video of
"That's What I Like" (Bruno Mars), followed by a credits card and a behind-the-scenes section.
Frame grid of the edit part: `minecraft-3d-lyric-reference-frames.jpg` (one frame every 0.5 s).

## Measured facts

| Item | Value |
|---|---|
| Canvas | **1:1 square**, 720×720, 30 fps |
| Structure | 0–26 s lyric edit → 26–30 s credits card → 30–58 s "Behind The Scenes" |
| Tempo | 133 BPM (beat ≈ 0.45 s) |
| Scene length | One scene per lyric phrase, about 1.5–4 s (2–8 beats) |
| Hard cuts | Very few (2.8, 11.2, 12.0, 13.2, 14.9, 16.4, 18.5 s). Most scene changes are **camera fly-throughs**, not cuts |
| Audio | Song only, no sound effects, loudness about -15 dB mean |
| Opening | 0–0.5 s white flash, then rapid flicker straight into the first scene (hook in under 1 s) |

## The 8 rules of the style

1. **Every lyric word is a physical object in the scene.** Words are 3D (extruded, made of blocks, cast as shadows,
   printed on a record, on a sign). They are never a flat subtitle bar.
2. **The scene illustrates the lyric literally.** "Jump in the Cadillac" → driving a Cadillac down a city street;
   record and vinyl label (album art) → "anything you want"; smiley face → "ice on it"; concert stage → "gonna";
   gold treasure chest and jewellery → "gold jewelry"; strawberry champagne glass → "strawberry champagne";
   big red heart → "that's what I like"; Minecraft hills → the ending.
3. **The font changes with every scene to match its theme:** chunky pixel/block font (JUMP, Some Miles),
   chrome script logo (Cadillac), typewriter with blinking cursor ("Just put_"), big serif as shadows
   ("deserve it, baby"), gold voxel letters (Gold Jewelry), neon pink glowing script (Champagne),
   stacked mixed-colour serif (LUCKY green, THAT'S blue, WHAT white), white serif on a red heart (LIKE).
4. **Words land exactly on the sung syllable.** One word or a short phrase at a time. The typewriter effect is used
   for spoken-feel lines. Key words are bigger or a different colour.
5. **The camera never stops moving:** push-ins, orbits, fly-overs, tilts, Dutch angles and speed ramps on the beat.
6. **Transitions are "fly-through" match moves:** the camera flies through the record hole, into a box, past a
   word or into an object, and that object becomes the next scene. A hard cut is used only on a strong beat.
7. **Look:** very saturated colour, warm gold/red against black/white chequer floors, purple-pink glow for the
   champagne part, depth-of-field blur, motion blur and soft bloom on bright parts.
8. **Ending:** a calm credits card on a soft lavender background in a monospace/pixel font:
   song title / artist / "Animated and Edited By <name>", which fades out.
   Optional extra: a "Behind The Scenes" title card, then screen recordings of the editing project.

## How to make it (what each tool can do)

- **Full look (true 3D):** Blender + Mineways/Minecraft world export or voxel models; text as extruded 3D
  text objects; camera on a path, keyframed to the beat. This is how the reference was made.
- **Phone (Alight Motion / CapCut), close version:**
  - 1:1 canvas.
  - One clip per lyric phrase, cut on the beat.
  - For each phrase, a matching background (photo, clip or Minecraft screenshot) with slow 3D camera keyframes
    (scale 100 → 115 %, plus small rotation).
  - Text layers with **3D rotate X/Y**, extrude/shadow, and a different font per phrase, keyframed in word by word.
  - "Zoom in" transition into an object for the scene changes.
  - Glow/bloom and motion-blur effects.
  - Credits card at the end.
- **Claude's Python/ffmpeg pipeline (2.5D version):** per-phrase scene images with a moving virtual camera
  (zoom, pan, rotate), per-scene themed fonts, words drawn with perspective and extrude shadow and popped in on the
  syllable, zoom-through transitions on phrase changes, bloom and grain, and a credits card.
  Reuse `lyric-video/render_v2.py` (word timing, beat grid) and `gaming-edit/edit.py` (beat-synced zooms) as a base.

## Inputs needed to make a video in this style
1. The song (audio or video file) and which part (start–end).
2. The lyrics for that part (exact words). Claude cannot transcribe speech or singing in this environment.
3. Visuals for each phrase (gameplay, photos, clips, Minecraft screenshots), or permission to design scenes from
   shapes and text only.
4. The credit name, which defaults to "Edit by Morsalin".
