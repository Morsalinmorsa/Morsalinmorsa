# Shudhu Tomake – real 3D video (make it on your PC)

## What you need
- A Windows PC with **Blender 4.0 or newer** (free: blender.org). A graphics card (NVIDIA / AMD / Intel Arc) makes it much faster.
- Nothing else. No Python, no ffmpeg.

## How to make the video
1. Download this whole folder (`pc-blender-package`) to your PC.
2. Double-click **`RUN_ON_PC.bat`**.
3. Wait. Blender renders the 9 scenes, then joins them with the song.
4. Your video appears in this folder: **`Shudhu_Tomake_3D_PC.mp4`** (1080×1080).

If it stops in the middle, just run `RUN_ON_PC.bat` again: finished scenes are skipped.

## Settings (optional)
Open a terminal in this folder and run, for example:

```
set RES=720
set SAMPLES=64
"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" -b -P render_all_pc.py
```

- `RES` = video size (1080 default). Lower = faster.
- `SAMPLES` = quality (128 default). Lower = faster but more grain.
- `ENGINE=EEVEE` = much faster, slightly less realistic.

## Look at or change a scene in Blender
```
blender -P scenes.py -- 4 renders/test 1080
```
opens scene 4 (night city) in Blender so you can move things, add buildings and press F12 to render.
Scenes: 0 intro, 1 lantern night, 2 stone hall, 3 heart hall, 4 night city, 5 sunrise valley, 6 record player,
7 neon club, 8 typewriter.

## Files
- `scenes.py` – builds every 3D scene (blocks, trees, cars, lights, camera, word animations)
- `render_all_pc.py` – renders all scenes with your graphics card, then calls `make_video.py`
- `make_video.py` – joins scenes + credits + music into the MP4 (uses Blender's video editor)
- `assets/` – textures, Bangla word shapes, lyrics timing, cover art, credits card
- `audio/song_part.wav` – the song part (Shudhu Tomake – Franklin)

Credit: Edit by Morsalin · Music: Shudhu Tomake – Franklin

---

## বাংলায়
১. পিসিতে Blender (৪.০ বা নতুন) ইনস্টল করুন, blender.org থেকে ফ্রি।
২. পুরো ফোল্ডারটা পিসিতে ডাউনলোড করুন।
৩. **RUN_ON_PC.bat** ফাইলে ডাবল-ক্লিক করুন।
৪. অপেক্ষা করুন। শেষ হলে এই ফোল্ডারেই **Shudhu_Tomake_3D_PC.mp4** ভিডিও পাবেন।
মাঝপথে থেমে গেলে আবার RUN_ON_PC.bat চালান, যেসব দৃশ্য আগেই শেষ হয়েছে সেগুলো আবার রেন্ডার হবে না।
