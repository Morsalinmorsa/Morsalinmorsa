"""TikTok lyric video v2: kinetic word-by-word lyrics, beat-synced effects.

usage: python3 render_v2.py WORKDIR START DUR LYRICS OUT [--preview t1,t2,...] --src SRC
Lyrics lines: "<start> <end> <text>" (seconds from clip start).
Beat grid: BEAT0 (absolute song seconds of a downbeat) and BEAT (seconds per beat).
"""
import sys, os, math, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

W, H, FPS = 1080, 1920, 30
BEAT0, BEAT = 79.90, 0.4616
args = sys.argv[1:]
wd, START, DUR, lyr_path, out = args[0], float(args[1]), float(args[2]), args[3], args[4]
preview = None
src = None
if "--preview" in args: preview = [float(v) for v in args[args.index("--preview") + 1].split(",")]
if "--src" in args: src = args[args.index("--src") + 1]

fd = os.path.join(wd, "fonts")
F = lambda n, s: ImageFont.truetype(os.path.join(fd, n), s, layout_engine=ImageFont.Layout.RAQM)
f_word = F("HindSiliguri-Bold.ttf", 88)
f_next = F("HindSiliguri-Medium.ttf", 44)
f_bn_title = F("Galada.ttf", 92)
f_artist = F("Poppins-SemiBold.ttf", 30)
f_small = F("Poppins-Light.ttf", 26)

def ease(t):
    t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3
def ease_back(t):
    t = min(max(t, 0.0), 1.0); c = 1.9; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

# ---------------- lyrics + word timing ----------------
lyrics = []
for ln in open(lyr_path, encoding="utf-8"):
    ln = ln.strip()
    if ln and not ln.startswith("#"):
        a, b, t = ln.split(" ", 2)
        words = t.split()
        lens = np.array([len(w_) + 1.5 for w_ in words], float)
        sing = (float(b) - float(a)) * 0.68
        starts = float(a) + 0.12 + np.concatenate([[0], np.cumsum(lens)[:-1]]) / lens.sum() * sing
        lyrics.append(dict(s=float(a), e=float(b), text=t, words=words, ws=list(starts)))

# ---------------- audio features ----------------
x = np.fromfile(os.path.join(wd, "audio.raw"), dtype=np.float32); sr = 16000
NB = 64
def spectrum(t):
    i = int((START + t) * sr)
    seg = x[max(0, i - 1024):i + 1024]
    if len(seg) < 2048: seg = np.pad(seg, (0, 2048 - len(seg)))
    s = np.abs(np.fft.rfft(seg * np.hanning(2048)))
    edges = np.geomspace(3, 700, NB + 1).astype(int)
    return np.log1p(np.array([s[edges[k]:max(edges[k + 1], edges[k] + 1)].mean() for k in range(NB)]) * 3)
REF = np.percentile([spectrum(t).max() for t in np.linspace(0, DUR, 150)], 95) + 1e-6
smooth = {"v": np.zeros(NB)}

def beat_info(t):
    a = START + t - BEAT0
    k = math.floor(a / BEAT)
    since = a - k * BEAT
    pulse = math.exp(-since / 0.11)
    down = (k % 4 == 0)
    return pulse, down, since, k

# ---------------- static layers ----------------
art = Image.open(os.path.join(wd, "art.png")).convert("RGB")
side = art.height
sq = art.crop(((art.width - side) // 2, 0, (art.width + side) // 2, side))
bg_src = art.resize((int(art.width * 2300 / art.height), 2300), Image.LANCZOS)
bg_src = ImageEnhance.Color(bg_src).enhance(1.5).filter(ImageFilter.GaussianBlur(30))
bg_src = ImageEnhance.Brightness(bg_src).enhance(0.42)

D = 620  # disc diameter
disc = sq.resize((D, D), Image.LANCZOS)
disc_mask = Image.new("L", (D, D), 0); ImageDraw.Draw(disc_mask).ellipse([0, 0, D - 1, D - 1], fill=255)
CX, CY = W // 2, 600

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vign = np.clip(1.0 - 0.75 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.62)) ** 2), 0.15, 1)[..., None]
def blob(cx, cy, r, col):
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))[..., None]
    return g * np.array(col, np.float32)[None, None, :]
leak_small = None  # computed at low res per frame for speed
ly, lx = np.mgrid[0:H // 8, 0:W // 8].astype(np.float32)

rng = random.Random(7)
parts = [dict(x=rng.uniform(0, W), y=rng.uniform(0, H), r=rng.uniform(2, 9), sp=rng.uniform(25, 90),
              ph=rng.uniform(0, 6.28), dr=rng.uniform(-15, 15), hue=rng.choice([(255, 210, 140), (255, 140, 180), (180, 220, 255), (255, 255, 255)]))
         for _ in range(90)]
grain_bank = [np.random.default_rng(i).normal(0, 7, (H // 2, W // 2)).astype(np.float32) for i in range(6)]

# word sprite cache
def grad_text(word, font, c1, c2):
    bbox = font.getbbox(word, anchor="ls")
    w_, h_ = bbox[2] - bbox[0] + 20, bbox[3] - bbox[1] + 20
    m = Image.new("L", (w_, h_), 0)
    ImageDraw.Draw(m).text((10 - bbox[0], 10 - bbox[1]), word, font=font, fill=255, anchor="ls")
    g = np.linspace(0, 1, h_)[:, None, None]
    col = (np.array(c1)[None, None] * (1 - g) + np.array(c2)[None, None] * g) * np.ones((1, w_, 1))
    img = Image.fromarray(col.astype(np.uint8), "RGB").convert("RGBA"); img.putalpha(m)
    return img, -bbox[1] + 10
cache = {}
def sprite(word, kind):
    key = (word, kind)
    if key not in cache:
        if kind == "hot": cache[key] = grad_text(word, f_word, (255, 236, 160), (255, 92, 150))
        elif kind == "dim": cache[key] = grad_text(word, f_word, (255, 255, 255), (230, 230, 240))
        else: cache[key] = grad_text(word, f_next, (255, 255, 255), (255, 255, 255))
    return cache[key]

title_bn = grad_text("শুধু তোমাকে", f_bn_title, (255, 230, 150), (255, 110, 160))

def paste_alpha(base, img, x0, y0, alpha=1.0, scale=1.0):
    if alpha <= 0.01: return
    if scale != 1.0:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BILINEAR)
    if alpha < 1:
        a = img.getchannel("A").point(lambda v: int(v * alpha)); img = img.copy(); img.putalpha(a)
    base.alpha_composite(img, (int(x0), int(y0)))

def layout_line(L, font=f_word, maxw=900):
    space = font.getlength(" ")
    widths = [font.getlength(w_) for w_ in L["words"]]
    rows, cur, cw = [], [], 0
    for i, wv in enumerate(widths):
        if cur and cw + space + wv > maxw:
            rows.append((cur, cw)); cur, cw = [], 0
        cw = cw + (space if cur else 0) + wv; cur.append(i)
    rows.append((cur, cw))
    pos = {}
    lh = 118
    for r, (idxs, rw) in enumerate(rows):
        xx0 = (W - rw) / 2
        for i in idxs:
            pos[i] = (xx0, r * lh - (len(rows) - 1) * lh / 2); xx0 += widths[i] + space
    return pos

def frame(t):
    pulse, down, since, k = beat_info(t)
    in_chorus = START + t >= BEAT0 - 0.02
    dp = pulse * (1.0 if down else 0.45) * (1 if in_chorus else 0.25)
    spec = np.clip(spectrum(t) / REF, 0, 1.3)
    smooth["v"] = np.maximum(spec, smooth["v"] * 0.82)
    sv = smooth["v"]
    energy = float(spec[:10].mean())

    # --- background: rotating/zooming blurred art ---
    z = 1.06 + 0.04 * math.sin(t / 5) + 0.035 * dp
    ang = 4 * math.sin(t / 6)
    M = 1.16
    cw_, ch_ = int(W * M / z), int(H * M / z)
    ox = (bg_src.width - cw_) // 2 + int(50 * math.sin(t / 4.3))
    oy = (bg_src.height - ch_) // 2 + int(40 * math.cos(t / 5.1))
    big = bg_src.crop((ox, oy, ox + cw_, oy + ch_)).resize((int(W * M), int(H * M)), Image.BILINEAR).rotate(ang, Image.BILINEAR)
    mx, my = (big.width - W) // 2, (big.height - H) // 2
    bg = big.crop((mx, my, mx + W, my + H))
    f = np.asarray(bg, np.float32)

    # light leaks (computed small, upscaled)
    c1 = (W / 8 * (0.5 + 0.45 * math.sin(t / 3.1)), H / 8 * (0.3 + 0.2 * math.cos(t / 2.7)))
    c2 = (W / 8 * (0.5 + 0.45 * math.cos(t / 3.7 + 1)), H / 8 * (0.75 + 0.15 * math.sin(t / 2.3)))
    leak = (np.exp(-(((lx - c1[0]) ** 2 + (ly - c1[1]) ** 2) / (2 * 38 ** 2)))[..., None] * np.array([255, 120, 40], np.float32)
            + np.exp(-(((lx - c2[0]) ** 2 + (ly - c2[1]) ** 2) / (2 * 44 ** 2)))[..., None] * np.array([230, 40, 140], np.float32))
    leak = np.asarray(Image.fromarray(np.clip(leak, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32)
    f = f + leak * (0.32 + 0.25 * energy)
    f = f * vign
    img = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).convert("RGBA")

    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # --- particles ---
    for p in parts:
        py = (p["y"] - t * p["sp"] * (1 + energy)) % (H + 40) - 20
        px = p["x"] + p["dr"] * math.sin(t * 0.7 + p["ph"]) * 3
        a = int(150 * (0.5 + 0.5 * math.sin(t * 2.2 + p["ph"])) * (0.6 + 0.6 * energy))
        r = p["r"] * (1 + 0.4 * dp)
        d.ellipse([px - r, py - r, px + r, py + r], fill=p["hue"] + (min(a, 255),))

    # --- radial spectrum ring ---
    R0 = D / 2 * (1 + 0.035 * dp) + 22
    rot = t * 0.35
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
    N = 96
    for i in range(N):
        bi = i % (N // 2); bi = bi if bi < NB else NB - 1
        v = float(sv[min(int(bi * NB / (N // 2)), NB - 1)])
        L_ = 8 + 120 * v ** 1.5
        th = rot + 2 * math.pi * i / N
        x1, y1 = CX + R0 * math.cos(th), CY + R0 * math.sin(th)
        x2, y2 = CX + (R0 + L_) * math.cos(th), CY + (R0 + L_) * math.sin(th)
        mix = i / N
        col = (255, int(210 - 120 * mix), int(110 + 60 * mix), 235)
        rd.line([x1, y1, x2, y2], fill=col, width=9)
    glow = ring.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
    ov.alpha_composite(glow); ov.alpha_composite(glow); ov.alpha_composite(ring)

    # --- disc (album art) ---
    s = 1 + 0.035 * dp + 0.01 * math.sin(t * 1.3)
    dd = int(D * s)
    dsc = disc.resize((dd, dd), Image.BILINEAR); m = disc_mask.resize((dd, dd), Image.BILINEAR)
    halo = Image.new("RGBA", (dd + 200, dd + 200), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([90, 90, dd + 110, dd + 110], fill=(255, 150, 120, int(120 + 100 * dp)))
    halo = halo.filter(ImageFilter.GaussianBlur(40))
    ov.alpha_composite(halo, (CX - dd // 2 - 100, CY - dd // 2 - 100))
    dimg = Image.new("RGBA", (dd, dd), (0, 0, 0, 0)); dimg.paste(dsc, (0, 0), m)
    ov.alpha_composite(dimg, (CX - dd // 2, CY - dd // 2))
    ImageDraw.Draw(ov).ellipse([CX - dd / 2, CY - dd / 2, CX + dd / 2, CY + dd / 2], outline=(255, 255, 255, 200), width=4)

    # --- title block ---
    intro = ease((t - 0.1) / 0.9)
    ty = 1145 + 40 * (1 - intro)
    paste_alpha(ov, title_bn[0], (W - title_bn[0].width) / 2, ty - title_bn[1] + 30, alpha=intro)
    sp = 14 + 10 * (1 - intro)
    txt = "FRANKLIN"
    tw = sum(f_artist.getlength(c) for c in txt) + sp * (len(txt) - 1)
    xa = (W - tw) / 2
    d2 = ImageDraw.Draw(ov)
    for c in txt:
        d2.text((xa, ty + 70), c, font=f_artist, fill=(255, 255, 255, int(200 * intro)))
        xa += f_artist.getlength(c) + sp

    # --- lyrics (kinetic, word by word) ---
    LY = 1420
    for L in lyrics:
        if t < L["s"] - 0.05 or t > L["e"] + 0.5: continue
        pos = layout_line(L)
        out_p = ease((t - L["e"]) / 0.45)
        for i, w_ in enumerate(L["words"]):
            ws = L["ws"][i]
            pin = (t - (ws - 0.22)) / 0.3
            lin = ease((t - L["s"] + 0.05) / 0.35)
            pop = (t - ws) / 0.28
            sc = 1.0 + 0.22 * math.sin(math.pi * min(max(pop, 0), 1)) if 0 <= pop < 1 else 1.0
            al = lin * (1 - out_p)
            hot = t >= ws
            spr, base = sprite(w_, "hot" if hot else "dim")
            if not hot: al *= 0.42
            x0, yo = pos[i]
            yv = LY + yo - 70 * out_p + 30 * (1 - lin) - 10 * (sc - 1) * 4
            cx_ = x0 + spr.width / 2 - 10
            if hot and t - ws < 0.6:
                gl = spr.resize((spr.width // 3, spr.height // 3)).filter(ImageFilter.GaussianBlur(5)).resize(spr.size)
                paste_alpha(ov, gl, cx_ - spr.width * sc / 2, yv - base * sc, alpha=al * (1 - (t - ws) / 0.6), scale=sc)
            paste_alpha(ov, spr, cx_ - spr.width * sc / 2, yv - base * sc, alpha=al, scale=sc)
    # next line preview
    cur = [L for L in lyrics if L["s"] <= t < L["e"]]
    nxt = [L for L in lyrics if L["s"] > t]
    if nxt and (cur or nxt[0]["s"] - t < 2.5) and nxt[0]["s"] - t < 4.2:
        n = nxt[0]
        a = 0.4 * ease((t - (n["s"] - 3.6)) / 0.5)
        tw = f_next.getlength(n["text"])
        d2.text((W / 2, LY + 140), n["text"], font=f_next, fill=(255, 255, 255, int(255 * a)), anchor="ms")

    img.alpha_composite(ov)
    arr = np.asarray(img.convert("RGB"), np.float32)

    # --- beat effects: flash, chromatic split, shake, grain ---
    hit = math.exp(-max(0, START + t - BEAT0) / 0.16) if START + t >= BEAT0 - 0.02 else 0
    arr = arr + 255 * (0.30 * hit + 0.05 * dp)
    shift = int(round(10 * dp + 18 * hit))
    if shift:
        r = np.roll(arr[..., 0], shift, axis=1); b = np.roll(arr[..., 2], -shift, axis=1)
        arr = np.stack([r, arr[..., 1], b], -1)
    g = grain_bank[int(t * FPS) % len(grain_bank)]
    arr = arr + np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    sx = int(round(6 * dp * math.sin(t * 90))); sy = int(round(6 * dp * math.cos(t * 77)))
    if sx or sy: arr = np.roll(arr, (sy, sx), axis=(0, 1))
    fa = min(ease(t / 0.5), ease((DUR - t) / 1.0))
    arr = arr * fa
    return np.clip(arr, 0, 255).astype(np.uint8)

if preview:
    ims = [Image.fromarray(frame(tp)).resize((360, 640)) for tp in preview]
    strip = Image.new("RGB", (360 * len(ims), 640))
    for i, im in enumerate(ims): strip.paste(im, (360 * i, 0))
    strip.save(out); sys.exit()

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-ss", str(START), "-t", str(DUR), "-i", src, "-map", "0:v", "-map", "1:a",
    "-af", f"afade=t=in:d=0.5,afade=t=out:st={DUR - 1.2}:d=1.2",
    "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
n = int(DUR * FPS)
for i in range(n):
    ff.stdin.write(frame(i / FPS).tobytes())
    if i % 150 == 0: print(f"{i}/{n}", flush=True)
ff.stdin.close(); ff.wait(); print("done", ff.returncode)
