"""Clean TikTok lyric edit: real song artwork only, simple word fades, cuts on the beat. 1080x1920.
usage: python3 clean.py LYRICDIR SONG OUT [--preview t1,t2,...]
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

a = sys.argv[1:]; LD, SONG, OUT = a[0], a[1], a[2]
PREVIEW = [float(v) for v in a[a.index("--preview") + 1].split(",")] if "--preview" in a else None
W, H, FPS = 1080, 1920, 30
START, DUR = 78.0, 34.6
HERE = os.path.dirname(os.path.abspath(__file__))
f_lyr = ImageFont.truetype(os.path.join(HERE, "fonts/TiroBangla.ttf"), 86, layout_engine=ImageFont.Layout.RAQM)
f_small = ImageFont.truetype(os.path.join(LD, "fonts/Poppins-Light.ttf"), 30)
f_small_bn = ImageFont.truetype(os.path.join(HERE, "fonts/TiroBangla.ttf"), 40, layout_engine=ImageFont.Layout.RAQM)
def smooth(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)

# lyrics with simple word timing
LINES = []
for ln in open(os.path.join(LD, "lyrics.txt"), encoding="utf-8"):
    s, e, txt = ln.strip().split(" ", 2); s, e = float(s), float(e)
    ws = txt.split(); lens = np.array([len(w) + 1.5 for w in ws])
    st = s + 0.1 + np.concatenate([[0], np.cumsum(lens)[:-1]]) / lens.sum() * (e - s) * 0.62
    LINES.append(dict(s=s, e=e, words=ws, ws=list(st)))

ART = Image.open(os.path.join(LD, "art.png")).convert("RGB")     # 1280x720 painting
AW, AH = ART.size
# Title band of the painting is y 286-436: wide shots show the whole painting (band intact);
# close-ups only use the parts above or below it.
BAND0, BAND1 = 284, 438
SHOTS = [
    ("full", 1.00, 1.03),                       # intro
    ("full", 1.02, 1.08),                       # তুমি আমার আলো
    ("close", 250, 600, 270, 40, 0),            # নিভিয়ে দাও অন্ধকার  (lower-left colours, pan right)
    ("close", 640, 525, 170, 0, 0, 0.88),       # আমি শুধু তোমাকে চাই (the lips, slow pull back)
    ("close", 640, 150, 270, 0, 30),            # আজও খুঁজে বেড়াই (the hair, tilt down)
    ("full", 1.00, 1.07),                       # তুমি আমার আলো
    ("close", 1040, 590, 260, -40, 0),          # নিভিয়ে দাও অন্ধকার (lower-right colours, pan left)
    ("close", 640, 515, 150, 0, 0, 1.1),        # আমি শুধু তোমাকেই চাই (lips, closer)
    ("full", 1.10, 1.00),                       # কেন বলতে পারিনা (pull back)
]
BOUNDS = [0.0] + [l["s"] for l in LINES] + [DUR + 1]
BG = ART.resize((int(AW * H / AH), H), Image.LANCZOS)
BG = BG.crop(((BG.width - W) // 2, 0, (BG.width + W) // 2, H)).filter(ImageFilter.GaussianBlur(45))
BG = ImageEnhance.Brightness(BG).enhance(0.42)

def shot_frame(i, u):
    sh = SHOTS[i]; e = smooth(u)
    if sh[0] == "full":
        z = sh[1] + (sh[2] - sh[1]) * e
        fw = int(W * z); fh = int(fw * AH / AW)
        fg = ART.resize((fw, fh), Image.BICUBIC)
        img = BG.copy()
        shadow = Image.new("L", (W, H), 0); sy = 700 - fh // 2
        ImageDraw.Draw(shadow).rectangle([(W - fw) // 2, sy + 18, (W + fw) // 2, sy + fh + 18], fill=150)
        img.paste((0, 0, 0), (0, 0), shadow.filter(ImageFilter.GaussianBlur(24)))
        img.paste(fg, ((W - fw) // 2, sy))
        return img
    _, cx, cy, ch, dx, dy = sh[:6]; zf = sh[6] if len(sh) > 6 else 1.0
    ch = ch * (1 + (zf - 1) * e) if zf >= 1 else ch * (zf + (1 - zf) * e)
    cw = ch * W / H
    x = cx + dx * (e - 0.5) - cw / 2; y = cy + dy * (e - 0.5) - ch / 2
    top_lim, bot_lim = (0, BAND0) if cy < BAND0 else (BAND1, AH)
    y = min(max(y, top_lim), bot_lim - ch); x = min(max(x, 0), AW - cw)
    img = ART.transform((W, H), Image.EXTENT, (x, y, x + cw, y + ch), Image.BICUBIC)
    return img.filter(ImageFilter.UnsharpMask(3, 60, 2))

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1.05 - 0.45 * (((xx - W / 2) / W) ** 2 * 1.6 + ((yy - H / 2) / H) ** 2 * 1.2), 0.55, 1)[..., None]
SHADE = (0.55 + 0.45 * np.clip(1 - np.abs(yy - 1330) / 420, 0, 1))[..., None]   # darker band behind the lyrics
GRAIN = [np.random.default_rng(i).normal(0, 4, (H // 2, W // 2)).astype(np.float32) for i in range(4)]

def wrap(words, font, maxw):
    rows, cur = [], []
    for i, w in enumerate(words):
        test = " ".join([words[j] for j in cur] + [w])
        if cur and font.getlength(test) > maxw: rows.append(cur); cur = []
        cur.append(i)
    rows.append(cur); return rows

def draw_lyrics(img, t):
    d = ImageDraw.Draw(img)
    for L in LINES:
        if not (L["s"] - 0.05 <= t < L["e"] + 0.05): continue
        out = 1 - smooth((t - (L["e"] - 0.25)) / 0.25)
        rows = wrap(L["words"], f_lyr, 860); lh = 118
        y0 = 1330 - (len(rows) - 1) * lh / 2
        for r, idx in enumerate(rows):
            line = " ".join(L["words"][i] for i in idx); x = (W - f_lyr.getlength(line)) / 2
            for i in idx:
                w = L["words"][i]; a = smooth((t - L["ws"][i] + 0.05) / 0.28) * out
                if a > 0:
                    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)) if False else None
                    d.text((x + 2, y0 + r * lh + 3), w, font=f_lyr, fill=(0, 0, 0, int(110 * a)), anchor="ls")
                    d.text((x, y0 + r * lh), w, font=f_lyr, fill=(247, 241, 230, int(255 * a)), anchor="ls")
                x += f_lyr.getlength(w + " ")

def frame(t):
    k = max(i for i in range(len(SHOTS)) if BOUNDS[i] <= t)
    u = (t - BOUNDS[k]) / (BOUNDS[k + 1] - BOUNDS[k]) if k < len(SHOTS) - 1 else (t - BOUNDS[k]) / (DUR - BOUNDS[k])
    img = shot_frame(k, u)
    img = ImageEnhance.Color(img).enhance(0.92)
    arr = np.asarray(img, np.float32)
    arr = arr * np.array([1.03, 1.0, 0.95]) + np.array([6, 4, 0])            # light warm grade
    arr = arr * VIG * SHADE
    pil = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(pil)
    # intro title + end credit, small and quiet
    if t < LINES[0]["s"]:
        a_ = smooth(t / 0.6) * (1 - smooth((t - LINES[0]["s"] + 0.3) / 0.3))
        d.text((W / 2, 1300), "শুধু তোমাকে", font=f_lyr, fill=(247, 241, 230, int(255 * a_)), anchor="ms")
        d.text((W / 2, 1370), "franklin", font=f_small, fill=(247, 241, 230, int(200 * a_)), anchor="ms")
    if t > LINES[-1]["e"] + 0.2:
        a_ = smooth((t - LINES[-1]["e"] - 0.2) / 0.8)
        d.text((W / 2, 1330), "edit by morsalin", font=f_small, fill=(247, 241, 230, int(220 * a_)), anchor="ms")
    draw_lyrics(pil, t)
    arr = np.asarray(pil.convert("RGB"), np.float32)
    arr = arr + np.repeat(np.repeat(GRAIN[int(t * FPS) % 4], 2, 0), 2, 1)[..., None]
    fa = min(smooth(t / 0.4), smooth((DUR - t) / 1.2))
    return np.clip(arr * fa, 0, 255).astype(np.uint8)

if PREVIEW:
    ims = [Image.fromarray(frame(tp)).resize((270, 480)) for tp in PREVIEW]
    st = Image.new("RGB", (270 * len(ims), 480))
    for j, im in enumerate(ims): st.paste(im, (270 * j, 0))
    st.save(OUT); sys.exit()
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-ss", str(START), "-t", str(DUR), "-i", SONG, "-map", "0:v", "-map", "1:a", "-af", f"afade=t=in:d=0.3,afade=t=out:st={DUR - 1.5}:d=1.5",
    "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT],
    stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)): ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print("done", ff.returncode)
