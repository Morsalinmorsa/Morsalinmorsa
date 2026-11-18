"""TikTok (1080x1920) lyric video renderer.

usage: python3 render.py WORKDIR START DURATION LYRICS_FILE OUT.mp4 [--preview T]
LYRICS_FILE: one line per lyric: "<start_sec> <end_sec> <text>" (times relative to the clip start).
"""
import sys, os, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
wd, START, DUR = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
lyr_path, out = sys.argv[4], sys.argv[5]
preview = float(sys.argv[7]) if len(sys.argv) > 7 and sys.argv[6] == "--preview" else None
src = sys.argv[8] if len(sys.argv) > 8 else None
fd = os.path.join(wd, "fonts")
F = lambda n, s: ImageFont.truetype(os.path.join(fd, n), s, layout_engine=ImageFont.Layout.RAQM)
f_lyric = F("HindSiliguri-Bold.ttf", 76)
f_next = F("HindSiliguri-Medium.ttf", 46)
f_title = F("Poppins-SemiBold.ttf", 54)
f_artist = F("Poppins-Light.ttf", 34)
f_small = F("Poppins-Light.ttf", 26)

# ---------- lyrics ----------
lyrics = []
if os.path.exists(lyr_path):
    for ln in open(lyr_path, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        a, b, t = ln.split(" ", 2)
        lyrics.append((float(a), float(b), t))

# ---------- audio analysis for the visualiser ----------
x = np.fromfile(os.path.join(wd, "audio.raw"), dtype=np.float32)
sr = 16000
NB = 28
def bands(t):
    i = int((START + t) * sr)
    seg = x[max(0, i - 1024):i + 1024]
    if len(seg) < 2048:
        seg = np.pad(seg, (0, 2048 - len(seg)))
    s = np.abs(np.fft.rfft(seg * np.hanning(2048)))
    edges = np.geomspace(3, 600, NB + 1).astype(int)
    v = np.array([s[edges[k]:max(edges[k + 1], edges[k] + 1)].mean() for k in range(NB)])
    return np.log1p(v * 3)
ref = np.percentile([bands(t).max() for t in np.linspace(0, DUR, 120)], 95) + 1e-6

# ---------- static layers ----------
art = Image.open(os.path.join(wd, "art.png")).convert("RGB")
# background: cover-crop, blurred, darkened
bg_big = art.resize((int(art.width * 1920 / art.height * 1.25), int(1920 * 1.25)), Image.LANCZOS)
bg_big = bg_big.filter(ImageFilter.GaussianBlur(40))
bg_big = Image.blend(bg_big, Image.new("RGB", bg_big.size, (8, 6, 14)), 0.55)
# vignette + bottom gradient
vig = Image.new("L", (W, H), 0)
vd = ImageDraw.Draw(vig)
for i in range(60):
    a = int(200 * (i / 60) ** 2)
    vd.rectangle([i * 6, i * 9, W - i * 6, H - i * 9], outline=None)
grad = np.zeros((H, W), np.float32)
yy = np.linspace(0, 1, H)[:, None]
xx = np.linspace(-1, 1, W)[None, :]
grad = np.clip(0.25 + 0.5 * (yy - 0.45).clip(0) * 2 + 0.25 * xx ** 2, 0, 0.85)
shade = Image.fromarray((grad * 255).astype(np.uint8), "L")
black = Image.new("RGB", (W, H), (5, 4, 10))

# album card: square crop of the cover, rounded corners and shadow
CARD = 780
side = art.height
card = art.crop(((art.width - side) // 2, 0, (art.width + side) // 2, side)).resize((CARD, CARD), Image.LANCZOS)
mask = Image.new("L", (CARD, CARD), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, CARD - 1, CARD - 1], 44, fill=255)
shadow = Image.new("RGBA", (CARD + 160, CARD + 160), (0, 0, 0, 0))
ImageDraw.Draw(shadow).rounded_rectangle([80, 100, CARD + 80, CARD + 100], 50, fill=(0, 0, 0, 190))
shadow = shadow.filter(ImageFilter.GaussianBlur(36))
CARD_Y = 250

def ease(t):
    t = min(max(t, 0), 1)
    return 1 - (1 - t) ** 3

def text_center(d, y, txt, font, fill, maxw=900, stroke=0, sfill=None):
    # wrap on spaces if too wide
    words, lines, cur = txt.split(" "), [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if d.textlength(test, font=font) <= maxw or not cur:
            cur = test
        else:
            lines.append(cur); cur = w_
    lines.append(cur)
    lh = font.size * 1.32
    y0 = y - lh * (len(lines) - 1) / 2
    for k, l in enumerate(lines):
        d.text((W / 2, y0 + k * lh), l, font=font, fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=sfill)
    return len(lines)

def frame(t):
    # slow zoom/pan of background
    z = 1.0 + 0.06 * (t / max(DUR, 1))
    bw, bh = int(W * 1.25 / z * z), int(H * 1.25)
    ox = int((bg_big.width - W) / 2 + 60 * math.sin(t / 7))
    oy = int((bg_big.height - H) / 2 + 40 * math.cos(t / 9))
    img = bg_big.crop((ox, oy, ox + W, oy + H))
    img = Image.composite(black, img, shade)

    b = np.clip(bands(t) / ref, 0, 1.2)
    energy = float(b[:8].mean())
    # card with soft beat pulse
    s = 1.0 + 0.018 * energy
    cs = int(CARD * s)
    c = card.resize((cs, cs), Image.BILINEAR)
    m = mask.resize((cs, cs), Image.BILINEAR)
    cx = (W - cs) // 2
    cy = CARD_Y + (CARD - cs) // 2
    img.paste(shadow, (cx - 80, cy - 80), shadow)
    img.paste(c, (cx, cy), m)

    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    # title + artist
    ty = CARD_Y + CARD + 80
    d.text((W / 2, ty), "Shudhu Tomake", font=f_title, fill=(255, 255, 255, 245), anchor="mm")
    d.text((W / 2, ty + 58), "FRANKLIN", font=f_artist, fill=(255, 255, 255, 170), anchor="mm")
    # visualiser bars
    vy = ty + 130
    bw_, gap = 14, 10
    total = NB * bw_ + (NB - 1) * gap
    x0 = (W - total) / 2
    for k in range(NB):
        hgt = 6 + 70 * float(min(b[k], 1.1)) ** 1.6
        xk = x0 + k * (bw_ + gap)
        col = (255, 196, 92, 230) if k % 2 == 0 else (255, 120, 150, 230)
        d.rounded_rectangle([xk, vy - hgt / 2, xk + bw_, vy + hgt / 2], 7, fill=col)

    # lyrics
    LY = 1410
    cur = next((l for l in lyrics if l[0] <= t < l[1]), None)
    nxt = next((l for l in lyrics if l[0] > t), None)
    if cur:
        p_in = ease((t - cur[0]) / 0.45)
        p_out = ease((t - (cur[1] - 0.35)) / 0.35)
        alpha = int(255 * p_in * (1 - p_out))
        dy = 40 * (1 - p_in) - 30 * p_out
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        text_center(ImageDraw.Draw(glow), LY + dy, cur[2], f_lyric, (255, 170, 90, int(alpha * 0.9)))
        glow = glow.filter(ImageFilter.GaussianBlur(18))
        over = Image.alpha_composite(over, glow)
        d = ImageDraw.Draw(over)
        text_center(d, LY + dy, cur[2], f_lyric, (255, 255, 255, alpha), stroke=2, sfill=(0, 0, 0, alpha // 3))
    if nxt and (cur is None or nxt[0] - t < 6):
        a2 = 110 if cur else int(110 * ease((t - (max([l[1] for l in lyrics if l[1] <= t], default=0))) / 0.4))
        text_center(d, LY + 135, nxt[2], f_next, (255, 255, 255, a2))

    # fade in/out
    fa = min(ease(t / 0.8), ease((DUR - t) / 0.8))
    img = Image.alpha_composite(img.convert("RGBA"), over).convert("RGB")
    if fa < 1:
        img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, fa)
    return img

if preview is not None:
    frame(preview).save(out)
    sys.exit()

ff = subprocess.Popen([
    "ffmpeg", "-v", "error", "-y",
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-ss", str(START), "-t", str(DUR), "-i", src,
    "-map", "0:v", "-map", "1:a",
    "-af", f"afade=t=in:d=0.8,afade=t=out:st={DUR - 1.2}:d=1.2",
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out,
], stdin=subprocess.PIPE)
n = int(DUR * FPS)
for i in range(n):
    ff.stdin.write(frame(i / FPS).tobytes())
    if i % 150 == 0:
        print(f"{i}/{n}", flush=True)
ff.stdin.close()
ff.wait()
print("done", ff.returncode)
