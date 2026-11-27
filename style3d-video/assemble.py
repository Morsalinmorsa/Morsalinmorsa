"""Join the Blender scene renders into the final square video with mixed transitions, light film finish, credits, music.
usage: python3 assemble.py B3D_DIR SONG OUT [--preview t1,t2]
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
a = sys.argv[1:]; BD, SONG, OUT = a[0], a[1], a[2]
PREVIEW = [float(v) for v in a[a.index("--preview") + 1].split(",")] if "--preview" in a else None
O, FPS, START, DUR = 1080, 30, 78.0, 36.5
BEAT0, BEAT = 79.90 - 78.0, 0.4616
LYR = [l.strip().split(" ", 2) for l in open(os.path.join(BD, "..", "lyric", "lyrics.txt"), encoding="utf-8")]
BOUNDS = [0.0] + [float(l[0]) for l in LYR] + [32.2, DUR + 1]
EXIT = {0: "cut", 1: "whip_h", 2: "cut", 3: "zoom", 4: "glitch", 5: "whip_v", 6: "zoom", 7: "cut", 8: "fade"}
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
f_m, f_s = ImageFont.truetype(MONO, 54), ImageFont.truetype(MONO, 40)
def smooth(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
def ease(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3

cache = {}
def scene_img(k, t):
    if k == 9: return credits(t)
    d = os.path.join(BD, f"out_{k}"); n = len(os.listdir(d))
    f = min(max(int(round((t - BOUNDS[k]) * FPS)) + 1, 1), n)
    key = (k, f)
    if key not in cache:
        if len(cache) > 12: cache.pop(next(iter(cache)))
        cache[key] = np.asarray(Image.open(os.path.join(d, f"f_{f:04d}.png")).convert("RGB").resize((O, O), Image.LANCZOS), np.float32)
    return cache[key]
def credits(t):
    img = Image.new("RGB", (O, O)); g = np.linspace(0, 1, O)[:, None, None]
    img = Image.fromarray((np.array([205, 200, 240]) * (1 - g) + np.array([172, 166, 222]) * g * np.ones((1, O, 1))).astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA"); a_ = ease((t - 32.2) / 0.6) * (1 - ease((t - (DUR - 1.0)) / 0.9))
    for txt, y, f in [("Shudhu Tomake", 360, f_m), ("Franklin", 440, f_s), ("Edited By", 600, f_s), ("Morsalin", 680, f_m)]:
        d.text((O / 2, y), txt, font=f, fill=(70, 66, 110, int(255 * a_)), anchor="mm")
    return np.asarray(img, np.float32)
def zoom(arr, z, dx=0, dy=0):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); cw = O / z
    x0 = (O - cw) / 2 + dx; y0 = (O - cw) / 2 + dy
    return np.asarray(im.transform((O, O), Image.EXTENT, (x0, y0, x0 + cw, y0 + cw), Image.BILINEAR), np.float32)
def shift(arr, dx, dy):
    return np.roll(arr, (int(dy), int(dx)), (0, 1))

yy, xx = np.mgrid[0:O, 0:O].astype(np.float32)
VIG = np.clip(1.1 - 0.4 * (((xx - O / 2) / O) ** 2 + ((yy - O / 2) / O) ** 2) * 2.2, 0.6, 1)[..., None]
GR = [np.random.default_rng(i).normal(0, 4.5, (O // 2, O // 2)).astype(np.float32) for i in range(5)]

def frame(t):
    k = max(i for i in range(10) if BOUNDS[i] <= t); to_end = BOUNDS[k + 1] - t; since = t - BOUNDS[k]
    ex = EXIT.get(k); en = EXIT.get(k - 1)
    img = scene_img(k, t)
    if ex == "zoom" and to_end < 0.2:
        q = 1 - to_end / 0.2; img = np.mean([zoom(img, 1 + 4 * (q + j * 0.07) ** 2) for j in range(3)], 0)
    if en == "zoom" and since < 0.18:
        img = zoom(img, 1 + 0.25 * (1 - since / 0.18)) + 90 * (1 - since / 0.18)
    if ex == "whip_h" and to_end < 0.15:
        q = 1 - to_end / 0.15; img = np.mean([shift(img, 700 * (q + j * 0.08) ** 2, 0) for j in range(5)], 0)
    if en == "whip_h" and since < 0.15:
        q = 1 - since / 0.15; img = np.mean([shift(img, -600 * (q - j * 0.08) ** 2, 0) for j in range(5)], 0)
    if ex == "whip_v" and to_end < 0.15:
        q = 1 - to_end / 0.15; img = np.mean([shift(img, 0, 700 * (q + j * 0.08) ** 2) for j in range(5)], 0)
    if en == "whip_v" and since < 0.15:
        q = 1 - since / 0.15; img = np.mean([shift(img, 0, -600 * (q - j * 0.08) ** 2) for j in range(5)], 0)
    if ex == "fade" and to_end < 0.6:
        q = smooth(1 - to_end / 0.6); img = img * (1 - q) + scene_img(k + 1, t) * q
    if en == "cut" and since < 2 / FPS: img = img * 1.15 + 15
    gl = (k, k + 1) if ex == "glitch" and to_end < 0.1 else (k - 1, k) if en == "glitch" and since < 0.1 else None
    if gl:
        other = scene_img(gl[1] if gl[0] == k else gl[0], t); r = np.random.default_rng(int(t * 1000)); img = img.copy()
        for _ in range(8):
            y0 = int(r.integers(0, O - 60)); h = int(r.integers(12, 90)); off = int(r.integers(-120, 120))
            img[y0:y0 + h] = np.roll((other if r.random() < 0.5 else img)[y0:y0 + h], off, 1)
        img = np.stack([np.roll(img[..., 0], 12, 1), img[..., 1], np.roll(img[..., 2], -12, 1)], -1)
    # small beat bump (zoom 1%) like a hand-set keyframe, only inside lyric scenes
    if 1 <= k <= 8 and t >= BEAT0:
        s_ = (t - BEAT0) % BEAT
        if s_ < 0.12: img = zoom(img, 1 + 0.012 * (1 - s_ / 0.12))
    img = img * VIG + np.repeat(np.repeat(GR[int(t * FPS) % 5], 2, 0), 2, 1)[..., None]
    if t > DUR - 0.5: img = img * max(0, (DUR - t) / 0.5)
    return np.clip(img, 0, 255).astype(np.uint8)

if PREVIEW:
    ims = [Image.fromarray(frame(tp)).resize((360, 360)) for tp in PREVIEW]
    st = Image.new("RGB", (360 * len(ims), 360))
    for j, im in enumerate(ims): st.paste(im, (360 * j, 0))
    st.save(OUT); sys.exit()
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{O}x{O}", "-r", str(FPS), "-i", "-",
    "-ss", str(START), "-t", str(DUR), "-i", SONG, "-map", "0:v", "-map", "1:a", "-af", f"afade=t=out:st={DUR - 1.8}:d=1.8",
    "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT],
    stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)): ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print("done", ff.returncode)
