"""Part 2: real behind-the-scenes of the Blender video. Final render next to Blender's own view of the same scene.
usage: python3 bts_real.py B3D_DIR SONG OUT [--preview t1,t2]
"""
import sys, os, math, re, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
a = sys.argv[1:]; BD, SONG, OUT = a[0], a[1], a[2]
PREVIEW = [float(v) for v in a[a.index("--preview") + 1].split(",")] if "--preview" in a else None
O, FPS, DUR = 1080, 30, 30.0
SONG_START = 78.0 + 36.5
NAMES = ["intro", "lantern night", "stone hall", "heart hall", "night city", "sunrise valley", "record player", "neon club", "typewriter"]
TOOK = {int(m.group(1)): int(m.group(2)) for m in re.finditer(r"scene (\d) took (\d+)s", open(os.path.join(BD, "render.log")).read())}
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"; MONOB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
f_card = ImageFont.truetype(MONO, 140); f_lab = ImageFont.truetype(MONOB, 26); f_inf = ImageFont.truetype(MONO, 22); f_end = ImageFont.truetype(MONO, 46)
def ease(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3
SEG0, SEG1 = 3.5, 28.0; SCN = list(range(1, 9)); SEGL = (SEG1 - SEG0) / len(SCN)

def load(d, f):
    n = len([x for x in os.listdir(d) if x.endswith(".png")]); f = min(max(f, 1), n)
    p = os.path.join(d, f"f_{f:04d}.png")
    return Image.open(p).convert("RGB"), n

def card(t, final=False):
    img = Image.new("RGB", (O, O), (232, 226, 246) if not final else (205, 200, 240)); d = ImageDraw.Draw(img)
    a_ = ease(t / 0.6)
    if final:
        d.text((O / 2, 470), "edit by", font=f_end, fill=(70, 66, 110), anchor="mm"); d.text((O / 2, 550), "Morsalin", font=f_card, fill=(70, 66, 110), anchor="mm")
        d.text((O / 2, 680), "music: Shudhu Tomake - Franklin", font=f_inf, fill=(90, 86, 130), anchor="mm")
    else:
        for j, w in enumerate(["Behind", "The", "Scenes"]):
            d.text((O / 2, 300 + j * 230), w, font=f_card, fill=(20, 20, 30, int(255 * a_)), anchor="mm")
    return img

def split(t):
    i = min(int((t - SEG0) / SEGL), len(SCN) - 1); k = SCN[i]; lt = (t - SEG0) - i * SEGL
    img = Image.new("RGB", (O, O), (22, 22, 24)); d = ImageDraw.Draw(img)
    fin, n = load(os.path.join(BD, f"out_{k}"), int(lt / SEGL * 1.0 * len(os.listdir(os.path.join(BD, f"out_{k}")))) + 1)
    vp, _ = load(os.path.join(BD, f"view_{k}"), int(lt / SEGL * len(os.listdir(os.path.join(BD, f"view_{k}")))) + 1)
    fi = int(lt / SEGL * n) + 1
    img.paste(fin.resize((530, 530)), (6, 230)); img.paste(vp.resize((530, 530)), (544, 230))
    d.text((12, 200), "Camera (final render)", font=f_lab, fill=(230, 230, 235)); d.text((550, 200), "Blender view (same scene)", font=f_lab, fill=(230, 230, 235))
    d.text((O / 2, 90), f"scene {k}  ·  {NAMES[k]}", font=f_end, fill=(240, 236, 228), anchor="mm")
    took = TOOK.get(k)
    info = f"frame {fi:03d}/{n}   ·   Eevee 720x720   ·   " + (f"rendered in {took // 60}m {took % 60:02d}s" if took else "")
    d.text((O / 2, 820), info, font=f_inf, fill=(170, 170, 180), anchor="mm")
    p = lt / SEGL; d.rectangle([60, 880, 60 + (O - 120) * p, 886], fill=(200, 170, 255)); d.rectangle([60, 880, O - 60, 886], outline=(80, 80, 90))
    return img

def frame(t):
    img = card(t) if t < SEG0 else split(t) if t < SEG1 else card(t - SEG1, final=True)
    arr = np.asarray(img, np.float32)
    if abs(t - SEG0) < 0.07 or abs(t - SEG1) < 0.07: arr = arr * 0.6 + 100
    return np.clip(arr * min(ease(t / 0.3), ease((DUR - t) / 0.9)), 0, 255).astype(np.uint8)

if PREVIEW:
    ims = [Image.fromarray(frame(tp)).resize((360, 360)) for tp in PREVIEW]
    st = Image.new("RGB", (360 * len(ims), 360))
    for j, im in enumerate(ims): st.paste(im, (360 * j, 0))
    st.save(OUT); sys.exit()
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{O}x{O}", "-r", str(FPS), "-i", "-",
    "-ss", str(SONG_START), "-t", str(DUR), "-i", SONG, "-map", "0:v", "-map", "1:a", "-af", f"afade=t=in:d=0.4,afade=t=out:st={DUR - 2}:d=2",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)): ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print("done", ff.returncode)
