"""Vertical (1080x1920) edit of a talking clip: grade, push-ins, cut punches, optional word captions.
usage: python3 edit.py WORKDIR SRC OUT [--preview t1,t2] [--captions captions.txt]
captions.txt lines: "<start> <end> <word>" ; a line '---' starts a new caption group.
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H, FPS = 1080, 1920, 30
args = sys.argv[1:]
wd, src, out = args[0], args[1], args[2]
preview = [float(v) for v in args[args.index("--preview") + 1].split(",")] if "--preview" in args else None
cap_path = args[args.index("--captions") + 1] if "--captions" in args else None

SW, SH = 576, 730
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, SH, SW, 3)
N = len(frames); DUR = N / FPS
CUTS = [0.0, 1.37, 3.13, 5.2, 6.43, 8.7, 10.23, 13.1, 16.93, 22.33, 24.57, 27.4, DUR]

def ease(t):
    t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3

# --- captions (optional) ---
groups = []
if cap_path:
    cur = []
    for ln in open(cap_path, encoding="utf-8"):
        ln = ln.strip()
        if not ln: continue
        if ln == "---":
            if cur: groups.append(cur); cur = []
            continue
        a, b, w_ = ln.split(" ", 2); cur.append((float(a), float(b), w_))
    if cur: groups.append(cur)
FONT = "/tmp/claude-0/-home-user-Morsalinmorsa/256700c8-01bb-53a3-ac0b-4bdd57d2caa1/scratchpad/ff/fonts/Anton.ttf"
f_cap = ImageFont.truetype(FONT, 96)

# static grade helpers
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vign = np.clip(1.08 - 0.55 * (((xx - W / 2) / W) ** 2 * 1.4 + ((yy - H / 2) / H) ** 2 * 1.6), 0.55, 1.0)[..., None]
grain = [np.random.default_rng(i).normal(0, 5, (H // 2, W // 2)).astype(np.float32) for i in range(4)]
lut_x = np.arange(256) / 255.0
s_curve = np.clip(lut_x + 0.12 * np.sin(2 * math.pi * (lut_x - 0.5)) * -1 * 0 + 0.0, 0, 1)
# filmic S-curve
s_curve = np.clip(0.5 + (lut_x - 0.5) * 1.12 + 0.06 * np.sin(math.pi * (lut_x - 0.5) * 2) * 0, 0, 1)

def grade(img):
    img = ImageEnhance.Color(img).enhance(1.18)
    a = np.asarray(img, np.float32) / 255
    a = np.clip(0.5 + (a - 0.5) * 1.1, 0, 1)
    # teal shadows / warm highlights
    lum = a.mean(-1, keepdims=True)
    a = a + (1 - lum) * np.array([-0.025, 0.01, 0.035]) + lum * np.array([0.03, 0.012, -0.03])
    return np.clip(a, 0, 1) * 255

CH = int(SH * W / SW)        # 1369: content height at full width
CY = (H - CH) // 2 - 40      # content top

def frame(t):
    i = min(int(t * FPS), N - 1)
    k = max(j for j in range(len(CUTS) - 1) if CUTS[j] <= t + 1e-6)
    c0, c1 = CUTS[k], CUTS[k + 1]
    u = (t - c0) / max(c1 - c0, 1e-3)
    punch = math.exp(-(t - c0) / 0.18) if k > 0 else 0
    z = 1.0 + 0.07 * u + 0.08 * punch          # slow push-in + punch on each cut
    src_img = Image.fromarray(frames[i])
    cw, ch = SW / z, SH / z
    x0 = (SW - cw) / 2; y0 = (SH - ch) * 0.35
    content = src_img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, CH), Image.BICUBIC)
    bg = src_img.resize((54, 96)).filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR)
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    canvas = bg.copy()
    # soft feathered edges of the content into the blur
    m = Image.new("L", (W, CH), 255)
    md = ImageDraw.Draw(m)
    for e in range(60):
        a = int(255 * e / 60)
        md.rectangle([0, e, W, e], fill=a); md.rectangle([0, CH - 1 - e, W, CH - 1 - e], fill=a)
    canvas.paste(content, (0, CY), m)
    arr = grade(canvas) * vign

    # captions
    if groups:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        for g in groups:
            if not (g[0][0] - 0.05 <= t < g[-1][1] + 0.15): continue
            words = [w_ for _, _, w_ in g]
            widths = [f_cap.getlength(w_.upper()) for w_ in words]; sp = 26
            tot = sum(widths) + sp * (len(words) - 1)
            x = (W - tot) / 2; y = CY + CH - 300
            gi = ease((t - g[0][0] + 0.05) / 0.15)
            for (a, b, w_), wd_ in zip(g, widths):
                on = a <= t
                pop = 1 + 0.18 * math.sin(math.pi * min(max((t - a) / 0.2, 0), 1)) if on else 1
                col = (255, 226, 40, 255) if on and t < b + 0.1 else (255, 255, 255, int(255 * gi))
                f_ = f_cap if pop == 1 else ImageFont.truetype(FONT, int(96 * pop))
                d.text((x + wd_ / 2, y), w_.upper(), font=f_, fill=col, anchor="mm", stroke_width=9, stroke_fill=(0, 0, 0, 255))
                x += wd_ + sp
        o = np.asarray(ov, np.float32); al = o[..., 3:4] / 255
        arr = arr * (1 - al) + o[..., :3] * al

    arr = arr + 160 * punch * 0.15                  # small flash on cuts
    arr = arr + np.repeat(np.repeat(grain[i % 4], 2, 0), 2, 1)[..., None]
    fa = min(ease(t / 0.3), ease((DUR - t) / 0.4))
    return np.clip(arr * fa, 0, 255).astype(np.uint8)

if preview:
    ims = [Image.fromarray(frame(tp)).resize((360, 640)) for tp in preview]
    strip = Image.new("RGB", (360 * len(ims), 640))
    for j, im in enumerate(ims): strip.paste(im, (360 * j, 0))
    strip.save(out); sys.exit()

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", src, "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st=%.2f:d=0.4" % (DUR - 0.4),
    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-maxrate", "14M", "-bufsize", "28M", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
for j in range(N):
    ff.stdin.write(frame(j / FPS).tobytes())
    if j % 150 == 0: print(f"{j}/{N}", flush=True)
ff.stdin.close(); ff.wait(); print("done", ff.returncode)
