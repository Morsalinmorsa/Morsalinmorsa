"""Joins the rendered scenes + credits + music into Shudhu_Tomake_3D_PC.mp4 using Blender's own video editor.
Run: blender -b -P make_video.py"""
import bpy, os, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); AS = os.path.join(HERE, "assets"); FPS = 30; DUR = 36.5
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
starts = [0.0] + [float(l.split(" ", 2)[0]) for l in open(os.path.join(AS, "lyrics.txt"), encoding="utf-8")] + [32.2]
first = sorted(glob.glob(os.path.join(HERE, "renders", "out_0", "f_*.png")))[0]
img = bpy.data.images.load(first); res = img.size[0]
sc.render.resolution_x = sc.render.resolution_y = res; sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = int(DUR * FPS)
se = sc.sequence_editor_create()
for k in range(9):
    files = sorted(glob.glob(os.path.join(HERE, "renders", f"out_{k}", "f_*.png")))
    st = se.sequences.new_image(f"scene{k}", files[0], channel=1, frame_start=int(round(starts[k] * FPS)) + 1)
    for f in files[1:]: st.elements.append(os.path.basename(f))
cr = se.sequences.new_image("credits", os.path.join(AS, "credits.png"), channel=2, frame_start=int(round(starts[9] * FPS)) + 1 - 18)
cr.frame_final_duration = int(sc.frame_end - cr.frame_start + 1)
cr.blend_alpha = 0.0; cr.keyframe_insert("blend_alpha", frame=cr.frame_start); cr.blend_alpha = 1.0; cr.keyframe_insert("blend_alpha", frame=cr.frame_start + 18)
se.sequences.new_sound("song", os.path.join(HERE, "audio", "song_part.wav"), channel=3, frame_start=1)
r = sc.render; r.use_sequencer = True; r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format = "MPEG4"; r.ffmpeg.codec = "H264"; r.ffmpeg.constant_rate_factor = "HIGH"; r.ffmpeg.ffmpeg_preset = "GOOD"
r.ffmpeg.audio_codec = "AAC"; r.ffmpeg.audio_bitrate = 192
r.filepath = os.path.join(HERE, "Shudhu_Tomake_3D_PC.mp4")
bpy.ops.render.render(animation=True)
