# Notes for Claude in this repo

This repo holds Morsalin's video edits and editing guides.

## Morsalin's preferences (remember these)
- When Morsalin says "same editing as that video", "my style" or "like the reference", follow
  `editing-styles/minecraft-3d-lyric-style.md`: words as 3D objects in themed scenes, a font per scene,
  words on the beat and syllable, a constantly moving camera, fly-through transitions, saturated glow look,
  and a credits card at the end.
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
- `turbodl/`: Android download manager app
