# Notes for Claude in this repo

This repo holds Morsalin's video edits and editing guides.

## Morsalin's preferences (remember these)
- When Morsalin says "same editing as that video", "my style" or "like the reference", follow
  `editing-styles/minecraft-3d-lyric-style.md`: words as 3D objects in themed scenes, a font per scene,
  words on the beat and syllable, a constantly moving camera, fly-through transitions, saturated glow look,
  and a credits card at the end.
- **It must not feel like AI.** Make every edit feel hand-made: a different text animation per scene (drop,
  rise, flicker, typewriter with uneven speed...), words placed at different spots, sizes and angles (never
  the same centred stack), keyframes snapped to the beat, handheld camera shake, a different colour grade per
  scene, light leaks / dust / grain / gate weave, and mixed transitions (hard cuts on the beat, whip pans,
  glitch, zoom-through, fade). No fake software screens: a behind-the-scenes must show real material (the real
  code, real layers, real build log). See `style3d-video/make_v3.py` and `bts_v3.py`.
- Credit line: **"Edit by Morsalin"**. Credit the song's artist too; never claim the song itself.
- Usual output: TikTok-ready MP4. The reference style is **1:1 square**, other edits are 9:16 (1080×1920).
- Captions/lyrics in Bangla (Hind Siliguri font renders correctly) or English. Use the exact words Morsalin
  provides; Claude cannot transcribe audio here, so ask for the words.
- Morsalin writes short messages in simple English or Bangla. Reply in simple English, and add a short Bangla
  summary when it helps.

## Existing work
- `lyric-video/`: Shudhu Tomake TikTok lyric videos (`render_v2.py` is the kinetic word-by-word renderer)
- `gaming-edit/`: Free Fire beat-synced edit (`edit.py`)
- `phone-promo/`: Honor X9E Pro promo with timed Bangla captions (`edit.py`)
- `talk-edit/`: vertical speech edit (`edit.py`)
- `style3d-video/`: Shudhu Tomake in the reference style (v3 = hand-edited feel, part 2 = real behind-the-scenes)
- `turbodl/`: Android download manager app
