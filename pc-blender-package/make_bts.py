"""Part 2 'Behind The Scenes': final render next to Blender's own view of each scene. Uses Blender's video editor.
Needs renders/out_1..8 (final) and renders/view_1..8 (made with BTS=1). Run: blender -b -P make_bts.py"""
import bpy, os, glob
HERE = os.path.dirname(os.path.abspath(__file__)); AS = os.path.join(HERE, "assets"); FPS = 30; DUR = 30.0
NAMES = ["intro", "lantern night", "stone hall", "heart hall", "night city", "sunrise valley", "record player", "neon club", "typewriter"]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
sc.render.resolution_x = sc.render.resolution_y = 1080; sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = int(DUR * FPS)
se = sc.sequence_editor_create()
T0, T1 = 3.5, 28.0; SEG = (T1 - T0) / 8
def img_strip(name, folder, ch, start, nfr):
    files = sorted(glob.glob(os.path.join(folder, "f_*.png")))
    pick = [files[min(len(files) - 1, int(i * len(files) / nfr))] for i in range(nfr)]
    st = se.sequences.new_image(name, pick[0], channel=ch, frame_start=start)
    for f in pick[1:]: st.elements.append(os.path.basename(f))
    return st
t = se.sequences.new_image("title", os.path.join(AS, "bts_title.png"), channel=1, frame_start=1); t.frame_final_duration = int(T0 * FPS)
for i, k in enumerate(range(1, 9)):
    s0 = int(round((T0 + i * SEG) * FPS)) + 1; n = int(round(SEG * FPS))
    bg = se.sequences.new_effect(f"bg{k}", "COLOR", channel=1, frame_start=s0, frame_end=s0 + n); bg.color = (0.02, 0.02, 0.025)
    a = img_strip(f"final{k}", os.path.join(HERE, "renders", f"out_{k}"), 2, s0, n)
    b = img_strip(f"view{k}", os.path.join(HERE, "renders", f"view_{k}"), 3, s0, n)
    for st, ox in ((a, -270), (b, 270)):
        st.transform.scale_x = st.transform.scale_y = 0.49; st.transform.offset_x = ox; st.blend_type = "ALPHA_OVER"
    for txt, y, size in ((f"scene {k}  ·  {NAMES[k]}", 0.9, 46), ("final render", 0.77, 26), ("Blender view (same scene)", 0.77, 26)):
        tx = se.sequences.new_effect(f"t{k}{y}{txt[:3]}", "TEXT", channel=4, frame_start=s0, frame_end=s0 + n)
        tx.text = txt; tx.font_size = size; tx.color = (0.92, 0.92, 0.95, 1); tx.align_x = "CENTER"
        tx.location = (0.5 if size == 46 else (0.25 if txt.startswith("final") else 0.75), y)
    took = os.path.join(HERE, "renders", f"out_{k}", "DONE")
    if os.path.exists(took):
        s = int(float(open(took).read())); tx = se.sequences.new_effect(f"took{k}", "TEXT", channel=5, frame_start=s0, frame_end=s0 + n)
        tx.text = f"rendered on this PC in {s // 60}m {s % 60:02d}s"; tx.font_size = 24; tx.color = (0.7, 0.7, 0.75, 1); tx.align_x = "CENTER"; tx.location = (0.5, 0.16)
e = se.sequences.new_image("end", os.path.join(AS, "bts_end.png"), channel=1, frame_start=int(T1 * FPS) + 1); e.frame_final_duration = int((DUR - T1) * FPS)
se.sequences.new_sound("song2", os.path.join(HERE, "audio", "song_part2.wav"), channel=6, frame_start=1)
r = sc.render; r.use_sequencer = True; r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format = "MPEG4"; r.ffmpeg.codec = "H264"; r.ffmpeg.constant_rate_factor = "HIGH"; r.ffmpeg.audio_codec = "AAC"; r.ffmpeg.audio_bitrate = 192
r.filepath = os.path.join(HERE, "Shudhu_Tomake_3D_PC_BehindTheScenes.mp4")
bpy.ops.render.render(animation=True)
