"""Shudhu Tomake in Morsalin's reference style: themed block-world scenes, 3D-looking words on the syllable,
moving camera, fly-through transitions, bloom; square 1080x1080.
usage: python3 make.py LYRICDIR SRC OUT [--preview t1,t2,...]
"""
import sys, os, math, subprocess, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

args = sys.argv[1:]
LD, SRC, OUT = args[0], args[1], args[2]
PREVIEW = [float(v) for v in args[args.index("--preview") + 1].split(",")] if "--preview" in args else None
O, FPS, WS = 1080, 30, 1400
START, DUR = 78.0, 36.5
BEAT0, BEAT = 79.90 - START, 0.4616
FD = os.path.join(LD, "fonts")
R = ImageFont.Layout.RAQM
def FB(n, s): return ImageFont.truetype(os.path.join(FD, n), s, layout_engine=R)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
rng = np.random.default_rng(3)

def ease(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3
def back(t):
    t = min(max(t, 0.0), 1.0); c = 1.8; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

# ---------- lyrics / word timing ----------
LINES = []
for ln in open(os.path.join(LD, "lyrics.txt"), encoding="utf-8"):
    a, b, txt = ln.strip().split(" ", 2); a, b = float(a), float(b)
    ws = txt.split(); lens = np.array([len(w) + 1.5 for w in ws])
    st = a + 0.12 + np.concatenate([[0], np.cumsum(lens)[:-1]]) / lens.sum() * (b - a) * 0.66
    LINES.append(dict(s=a, e=b, words=ws, ws=list(st)))

# ---------- drawing helpers ----------
def blocks(w, h, bs, palette, jitter=0.12, bevel=True):
    gw, gh = math.ceil(w / bs), math.ceil(h / bs)
    pal = np.array(palette, np.float32)
    idx = rng.integers(0, len(pal), (gh, gw))
    col = pal[idx] * (1 + rng.uniform(-jitter, jitter, (gh, gw, 1)))
    img = np.repeat(np.repeat(col, bs, 0), bs, 1)[:h, :w]
    if bevel:
        yy, xx = np.mgrid[0:h, 0:w] % bs
        e = max(2, bs // 10)
        img = img * np.where((yy < e) | (xx < e), 1.18, 1.0)[..., None] * np.where((yy >= bs - e) | (xx >= bs - e), 0.72, 1.0)[..., None]
    return np.clip(img, 0, 255)
def vgrad(w, h, c1, c2, p=1.0):
    k = (np.linspace(0, 1, h) ** p)[:, None, None]
    return np.array(c1, np.float32) * (1 - k) + np.array(c2, np.float32) * k * np.ones((1, w, 1))
def glow_spot(arr, cx, cy, r, col, amt=1.0):
    h, w = arr.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))[..., None]
    return arr + g * np.array(col, np.float32) * amt
def chequer(w, h, horizon, c1=(240, 240, 240), c2=(25, 25, 30), n=14):
    """perspective chequer floor below `horizon` (numpy RGB)"""
    out = np.zeros((h, w, 3), np.float32); ys = np.arange(horizon, h)
    d = (ys - horizon + 8) / (h - horizon)
    z = 1 / d; xx = (np.arange(w)[None, :] - w / 2) / (w / 2) * z[:, None]
    cell = (np.floor(xx * n / 3) + np.floor(z[:, None] * 3)) % 2
    fog = np.clip(d * 1.6, 0, 1)[:, None, None]
    floor = np.where(cell[..., None] == 0, np.array(c1, np.float32), np.array(c2, np.float32)) * (0.35 + 0.65 * fog)
    out[horizon:] = floor; return out

def text_sprite(word, font, face, extrude=(40, 20, 20), depth=10, stroke=0, sfill=(0, 0, 0), pixel=0, grad=None, glow=None):
    """3D-looking word: extruded side, face colour/gradient, optional pixel look and glow."""
    if pixel:
        f = FB(font[0], font[1] // pixel)
        bb = f.getbbox(word); w, h = bb[2] - bb[0] + 6, bb[3] - bb[1] + 6
        m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m); d.fontmode = "1"
        d.text((3 - bb[0], 3 - bb[1]), word, font=f, fill=255)
        m = m.resize((w * pixel, h * pixel), Image.NEAREST)
    else:
        f = FB(*font); bb = f.getbbox(word); w, h = bb[2] - bb[0] + 20, bb[3] - bb[1] + 20
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).text((10 - bb[0], 10 - bb[1]), word, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
    pad = depth + 40
    W_, H_ = m.width + pad * 2, m.height + pad * 2
    out = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    if glow:
        g = Image.new("RGBA", (W_, H_), glow + (0,)); gm = Image.new("L", (W_, H_), 0); gm.paste(m, (pad, pad))
        gm = gm.filter(ImageFilter.GaussianBlur(18)); g.putalpha(gm.point(lambda v: min(255, v * 2)))
        out.alpha_composite(g); out.alpha_composite(g)
    side = Image.new("RGBA", m.size, extrude + (255,))
    for k in range(depth, 0, -1):
        sh = Image.new("RGBA", m.size, tuple(int(c * (0.6 + 0.4 * k / depth)) for c in extrude) + (255,)); sh.putalpha(m)
        out.alpha_composite(sh, (pad + k, pad + k))
    if grad:
        g = np.linspace(0, 1, m.height)[:, None, None]
        fc = (np.array(grad[0]) * (1 - g) + np.array(grad[1]) * g) * np.ones((1, m.width, 1))
        fimg = Image.fromarray(fc.astype(np.uint8), "RGB").convert("RGBA")
    else:
        fimg = Image.new("RGBA", m.size, face + (255,))
    fimg.putalpha(m); out.alpha_composite(fimg, (pad, pad))
    return out

# ---------- scenes ----------
ART = Image.open(os.path.join(LD, "art.png")).convert("RGB")
class Scene:
    def __init__(s, t0, t1, world, words=None, layout=None, cam=None, dyn=None, line=None):
        s.t0, s.t1, s.world, s.layout, s.cam, s.dyn = t0, t1, world, layout or [], cam, dyn
        s.line = words if isinstance(words, dict) else line

def stack_layout(sprites, cx, cy, gap=-10, maxw=1000):
    """stack words vertically, centred; returns list of (sprite,x,y) in world coords"""
    sc = [min(1.0, maxw / sp.width) for sp in sprites]
    hs = [sp.height * k for sp, k in zip(sprites, sc)]
    tot = sum(hs) + gap * (len(hs) - 1); y = cy - tot / 2; res = []
    for sp, k, h in zip(sprites, sc, hs):
        res.append((sp, k, cx - sp.width * k / 2, y)); y += h + gap
    return res

def build():
    L = LINES; sc = []
    # S0 intro: black with flicker title
    w0 = np.zeros((WS, WS, 3), np.float32) + 8
    sc.append(Scene(0, L[0]["s"], w0, cam=lambda u, t: (700, 700, 1.25 + 0.15 * u, 0)))
    # S1 night field + lantern
    a = vgrad(WS, WS, (10, 12, 40), (60, 30, 90), 1.3)
    a[880:] = blocks(WS, WS - 880, 56, [(78, 52, 34), (95, 64, 40), (70, 46, 30)])
    a[880:936] = blocks(WS, 56, 56, [(70, 140, 50), (82, 160, 58), (60, 120, 45)])
    for _ in range(120):
        x, y = rng.integers(0, WS), rng.integers(0, 800); a[y:y + 4, x:x + 4] = 255
    a[700:820, 640:760] = blocks(120, 120, 30, [(255, 190, 60), (255, 160, 40), (250, 210, 90)])
    a = glow_spot(a, 700, 760, 160, (255, 170, 60), 0.9); a = glow_spot(a, 700, 760, 420, (255, 120, 40), 0.35)
    sp = [text_sprite(w, ("HindSiliguri-Bold.ttf", 170), (255, 236, 190), extrude=(120, 60, 20), depth=12,
                      glow=(255, 170, 60) if "আলো" in w else None) for w in L[0]["words"]]
    sc.append(Scene(L[0]["s"], L[1]["s"], a, L[0], stack_layout(sp, 700, 470),
                    cam=lambda u, t: (700, 560, 1.02 + 0.2 * u, -3 + 5 * u)))
    # S2 stone wall + moving spotlight, words as shadows
    a = blocks(WS, WS, 70, [(120, 120, 125), (100, 100, 106), (135, 135, 140), (90, 92, 98)], 0.15)
    sp = []
    for w in L[1]["words"]:
        t = text_sprite(w, ("HindSiliguri-Bold.ttf", 230 if "অন্ধকার" in w else 170), (15, 10, 20), extrude=(15, 10, 20), depth=2)
        t = t.filter(ImageFilter.GaussianBlur(3)); al = t.getchannel("A").point(lambda v: int(v * 0.8)); t.putalpha(al)
        sp.append(t.transform(t.size, Image.AFFINE, (1, 0.35, -0.175 * t.height, 0, 1, 0), Image.BICUBIC))
    def wall_dyn(img_arr, t, u):
        cx = 350 + 700 * u; cy = 650 + 120 * math.sin(t * 2)
        yy, xx = np.mgrid[0:WS:4, 0:WS:4].astype(np.float32)
        g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * 380 ** 2))
        g = np.repeat(np.repeat(g, 4, 0), 4, 1)[..., None]
        return img_arr * (0.22 + 1.1 * g) + g * np.array([60, 45, 20])
    sc.append(Scene(L[1]["s"], L[2]["s"], a, L[1], stack_layout(sp, 720, 680, gap=-30), dyn=wall_dyn,
                    cam=lambda u, t: (700, 700, 1.2 + 0.1 * u, 4 - 6 * u)))
    # S3 red voxel heart on chequer floor
    a = np.zeros((WS, WS, 3), np.float32) + 12; a[:] = chequer(WS, WS, 760); a[:760] = vgrad(WS, 760, (8, 6, 12), (40, 20, 30))
    HEART = ["0110001100", "1111011110", "1111111111", "1111111111", "0111111110", "0011111100", "0001111000", "0000110000"]
    bs = 88; hx, hy = 700 - 5 * bs, 280
    for r, row in enumerate(HEART):
        for c, ch in enumerate(row):
            if ch == "1": a[hy + r * bs:hy + (r + 1) * bs, hx + c * bs:hx + (c + 1) * bs] = blocks(bs, bs, bs, [(210, 25, 40), (190, 20, 35), (230, 40, 55)], 0.1)
    a = glow_spot(a, 700, 600, 500, (120, 0, 20), 0.5)
    sp = [text_sprite(w, ("HindSiliguri-Bold.ttf", 150), (255, 255, 255), extrude=(110, 10, 20), depth=10) for w in L[2]["words"]]
    sc.append(Scene(L[2]["s"], L[3]["s"], a, L[2], stack_layout(sp, 700, 610, gap=-35),
                    cam=lambda u, t: (700, 620, 1.05 + 0.3 * u, -8 + 14 * u)))
    # S4 night city + searchlights, pixel words
    a = vgrad(WS, WS, (20, 8, 50), (110, 40, 120), 1.2)
    x = 0
    while x < WS:
        bw = min(int(rng.integers(90, 200)), WS - x); bh = int(rng.integers(300, 820)); top = WS - bh
        a[top:, x:x + bw] = blocks(bw, bh, 30, [(25, 22, 40), (32, 28, 50)], 0.08)
        for wy in range(top + 30, WS - 30, 60):
            for wx in range(x + 20, x + bw - 30, 50):
                if rng.random() < 0.45: a[wy:wy + 22, wx:wx + 18] = (255, 220, 120)
        x += bw + int(rng.integers(0, 20))
    def city_dyn(arr, t, u):
        out = arr.copy()
        for k, base in enumerate([-0.6, 0.5]):
            ang = base + 0.5 * math.sin(t * 1.3 + k * 2)
            ox, oy = 350 + 700 * k, WS
            yy, xx = np.mgrid[0:WS:4, 0:WS:4].astype(np.float32)
            th = np.arctan2(xx - ox, oy - yy)
            beam = np.exp(-((th - ang) / 0.07) ** 2) * np.clip((oy - yy) / WS, 0, 1)
            out = out + np.repeat(np.repeat(beam, 4, 0), 4, 1)[..., None] * np.array([180, 190, 255]) * 0.6
        return out
    sp = [text_sprite(w, ("HindSiliguri-Bold.ttf", 168), (120, 240, 255), extrude=(20, 60, 120), depth=10, pixel=6) for w in L[3]["words"]]
    sc.append(Scene(L[3]["s"], L[4]["s"], a, L[3], stack_layout(sp, 700, 520, gap=-20), dyn=city_dyn,
                    cam=lambda u, t: (600 + 200 * u, 560, 1.12, 0)))
    # S5 sunrise over block hills, gold voxel words
    a = vgrad(WS, WS, (255, 120, 80), (255, 210, 120), 0.8)
    a[300:540, 540:860] = blocks(320, 240, 80, [(255, 240, 150), (255, 225, 120)], 0.05)
    a = glow_spot(a, 700, 420, 300, (255, 200, 100), 0.6)
    for layer, (base, col) in enumerate([(820, (90, 150, 70)), (960, (70, 130, 55))]):
        for x in range(0, WS, 70):
            top = base + int(80 * math.sin(x / 160 + layer * 2) + rng.integers(-1, 2) * 70)
            top = top // 70 * 70
            a[top:, x:x + 70] = blocks(70, WS - top, 70, [(120, 84, 52), (100, 70, 44)])
            a[top:top + 70, x:x + 70] = blocks(70, 70, 70, [col])
    sp = [text_sprite(w, ("HindSiliguri-Bold.ttf", 186), (255, 215, 80), extrude=(120, 70, 10), depth=14, pixel=6,
                      grad=((255, 245, 160), (230, 150, 20))) for w in L[4]["words"]]
    sc.append(Scene(L[4]["s"], L[5]["s"], a, L[4], stack_layout(sp, 700, 560, gap=-20),
                    cam=lambda u, t: (700, 700 - 120 * u, 1.15 - 0.1 * u, 0)))
    # S6 spinning vinyl with cover label
    a = vgrad(WS, WS, (30, 18, 12), (10, 6, 4)); disc = Image.new("RGBA", (1200, 1200), (0, 0, 0, 0)); d = ImageDraw.Draw(disc)
    d.ellipse([0, 0, 1199, 1199], fill=(18, 18, 20, 255))
    for r in range(590, 250, -9): d.ellipse([600 - r, 600 - r, 600 + r, 600 + r], outline=(32, 32, 36, 255), width=2)
    lab = ART.crop(((ART.width - ART.height) // 2, 0, (ART.width + ART.height) // 2, ART.height)).resize((480, 480))
    lm = Image.new("L", (480, 480), 0); ImageDraw.Draw(lm).ellipse([0, 0, 479, 479], fill=255); disc.paste(lab, (360, 360), lm)
    d.ellipse([588, 588, 612, 612], fill=(10, 10, 10, 255))
    sp = [text_sprite(w, ("HindSiliguri-Bold.ttf", 120), (245, 245, 245), extrude=(60, 60, 60), depth=4) for w in L[5]["words"]]
    sc6 = Scene(L[5]["s"], L[6]["s"], a, L[5], stack_layout(sp, 700, 700, gap=-10),
                cam=lambda u, t: (700, 700, 1.25 + 0.15 * u, 10 - 20 * u))
    sc6.disc = disc; sc.append(sc6)
    # S7 neon pink script
    a = chequer(WS, WS, 900, (230, 220, 240), (40, 20, 50)); a[:900] = vgrad(WS, 900, (40, 10, 60), (150, 50, 130))
    for _ in range(60):
        x, y, r = rng.integers(0, WS), rng.integers(0, 880), rng.integers(4, 16); a = glow_spot(a, x, y, r, (255, 200, 255), 0.8) if r > 12 else a
    sp = [text_sprite(w, ("Galada.ttf", 160), (255, 120, 200), extrude=(120, 20, 90), depth=6, glow=(255, 60, 200)) for w in L[6]["words"]]
    sc.append(Scene(L[6]["s"], L[7]["s"], a, L[6], stack_layout(sp, 700, 580, gap=-70),
                    cam=lambda u, t: (700, 600, 1.02 + 0.2 * u, 6 * math.sin(t * 0.8))))
    # S8 typewriter (drawn in screen space)
    a = np.zeros((WS, WS, 3), np.float32) + 6
    sc.append(Scene(L[7]["s"], 32.2, a, L[7], [], cam=lambda u, t: (700, 700, 1.25 + 0.12 * u, 0)))
    # S9 credits
    a = vgrad(WS, WS, (205, 200, 240), (170, 165, 220))
    sc.append(Scene(32.2, DUR + 1, a, None, [], cam=lambda u, t: (700, 700, 1.25, 0)))
    return sc

SC = build()
F_MONO = ImageFont.truetype(MONO, 54); F_MONO_S = ImageFont.truetype(MONO, 40)
F_TYPE = FB("HindSiliguri-Medium.ttf", 104)

def clusters(s):
    out = []
    for ch in s:
        if out and (0x0981 <= ord(ch) <= 0x0983 or 0x09BC <= ord(ch) <= 0x09D7 or ch in "‌‍" or out[-1].endswith("্")):
            out[-1] += ch
        else: out.append(ch)
    return out

def world_frame(scn, t):
    u = (t - scn.t0) / max(scn.t1 - scn.t0, 1e-3)
    arr = scn.dyn(scn.world, t, u) if scn.dyn else scn.world
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    if hasattr(scn, "disc"):
        layer = scn.disc.copy()
        img.alpha_composite(layer.rotate(-t * 45, Image.BICUBIC), (100, 100))
    for k, (sp, sck, x, y) in enumerate(scn.layout):
        ws = scn.line["ws"][k]; p = (t - ws + 0.05) / 0.32
        if p <= 0: continue
        s = sck * (0.3 + 0.7 * back(p)); al = ease(p * 1.5)
        spr = sp.resize((max(1, int(sp.width * s)), max(1, int(sp.height * s))), Image.BILINEAR)
        if al < 1: spr.putalpha(spr.getchannel("A").point(lambda v: int(v * al)))
        cx = x + sp.width * sck / 2; cy = y + sp.height * sck / 2 - 40 * (1 - ease(p))
        img.alpha_composite(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)))
    return img, u

def camera(img, cx, cy, z, ang):
    th = math.radians(ang); c, sn = math.cos(th), math.sin(th)
    z = max(z, (abs(c) + abs(sn)) * 1.02)
    half = WS / z / 2 * (abs(c) + abs(sn))
    cx = min(max(cx, half), WS - half); cy = min(max(cy, half), WS - half)
    s = (WS / z) / O
    a, b = s * c, -s * sn; d, e = s * sn, s * c
    cc = cx - a * O / 2 - b * O / 2; f = cy - d * O / 2 - e * O / 2
    return img.transform((O, O), Image.AFFINE, (a, b, cc, d, e, f), Image.BILINEAR, fillcolor=(0, 0, 0, 255))

def screen_text(img, scn, t):
    d = ImageDraw.Draw(img)
    if scn is SC[0]:
        on = (int(t * 12) % 3 != 0) or t > 1.0
        if on:
            for txt, y, sz in [("SHUDHU TOMAKE", 470, 10), ("FRANKLIN", 640, 6)]:
                f = ImageFont.truetype(MONO, sz * 9); bb = f.getbbox(txt)
                m = Image.new("L", (bb[2] + 4, bb[3] + 4), 0); md = ImageDraw.Draw(m); md.fontmode = "1"
                md.text((2, 2), txt, font=ImageFont.truetype(MONO, sz * 9 // 6), fill=255)
                m = m.crop(m.getbbox()).resize((m.getbbox()[2] * 6 - m.getbbox()[0] * 6, (m.getbbox()[3] - m.getbbox()[1]) * 6), Image.NEAREST)
                face = Image.new("RGBA", m.size, (255, 230, 120, 255) if sz == 10 else (255, 255, 255, 255)); face.putalpha(m)
                img.alpha_composite(face, ((O - m.width) // 2, y - m.height // 2))
    elif scn is SC[8]:
        L = scn.line; full = " ".join(L["words"]); cl = clusters(full)
        n = 0
        # reveal clusters across word timings
        starts = L["ws"] + [L["ws"][-1] + 0.8]; acc = 0
        for k, w in enumerate(L["words"]):
            wc = len(clusters(w)) + (1 if k < len(L["words"]) - 1 else 0)
            p = min(max((t - starts[k]) / max(starts[k + 1] - starts[k], 0.2), 0), 1)
            n += int(round(wc * p)) if t < starts[k + 1] else wc
        shown = "".join(cl[:n]); cur = "_" if int(t * 3) % 2 == 0 else " "
        bb = F_TYPE.getbbox(full)
        x0 = (O - (bb[2] - bb[0])) // 2
        d.text((x0, 540), shown + cur, font=F_TYPE, fill=(240, 240, 240), anchor="ls")
    elif scn is SC[9]:
        a = ease((t - scn.t0) / 0.5) * (1 - ease((t - (DUR - 1.0)) / 0.9))
        col = (70, 66, 110, int(255 * a))
        for txt, y, f in [("Shudhu Tomake", 360, F_MONO), ("Franklin", 440, F_MONO_S), ("Edited By", 600, F_MONO_S), ("Morsalin", 680, F_MONO)]:
            d.text((O / 2, y), txt, font=f, fill=col, anchor="mm")

def render(t):
    k = max(i for i, s in enumerate(SC) if s.t0 <= t + 1e-6); scn = SC[k]
    img, u = world_frame(scn, t)
    cx, cy, z, ang = scn.cam(u, t)
    since = t - BEAT0 - math.floor((t - BEAT0) / BEAT) * BEAT if t >= BEAT0 else 9
    bp = math.exp(-since / 0.1) if scn is not SC[9] else 0
    z *= 1 + 0.018 * bp
    out_t = scn.t1 - t
    if k < len(SC) - 1 and out_t < 0.22:        # fly-through into next scene
        q = 1 - out_t / 0.22
        frames = [camera(img, cx, cy, z * (1 + 6 * (q + j * 0.06) ** 2), ang).convert("RGB") for j in range(3)]
        res = np.mean([np.asarray(f, np.float32) for f in frames], 0)
    else:
        res = np.asarray(camera(img, cx, cy, z, ang).convert("RGB"), np.float32)
    pil = Image.fromarray(res.astype(np.uint8)).convert("RGBA"); screen_text(pil, scn, t)
    res = np.asarray(pil.convert("RGB"), np.float32)
    # bloom
    small = Image.fromarray(np.clip((res - 170) * 2, 0, 255).astype(np.uint8)).resize((O // 4, O // 4)).filter(ImageFilter.GaussianBlur(6)).resize((O, O))
    res = res + np.asarray(small, np.float32) * (0.45 + 0.25 * bp)
    if t - scn.t0 < 0.15 and k > 0: res = res + 200 * (1 - (t - scn.t0) / 0.15)
    if t < 0.12: res = res * 0 + 255
    yy, xx = np.mgrid[0:O, 0:O].astype(np.float32) if not hasattr(render, "v") else (None, None)
    if not hasattr(render, "v"):
        render.v = np.clip(1.1 - 0.5 * (((xx - O / 2) / O) ** 2 + ((yy - O / 2) / O) ** 2) * 2.2, 0.5, 1)[..., None]
        render.g = [np.random.default_rng(i).normal(0, 6, (O // 2, O // 2)).astype(np.float32) for i in range(4)]
    res = res * render.v + np.repeat(np.repeat(render.g[int(t * FPS) % 4], 2, 0), 2, 1)[..., None]
    if t > DUR - 0.4: res = res * max(0, (DUR - t) / 0.4)
    return np.clip(res, 0, 255).astype(np.uint8)

if PREVIEW:
    ims = [Image.fromarray(render(tp)).resize((360, 360)) for tp in PREVIEW]
    cols = 5; rows = math.ceil(len(ims) / cols); strip = Image.new("RGB", (360 * cols, 360 * rows))
    for j, im in enumerate(ims): strip.paste(im, (360 * (j % cols), 360 * (j // cols)))
    strip.save(OUT); sys.exit()

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{O}x{O}", "-r", str(FPS), "-i", "-",
    "-ss", str(START), "-t", str(DUR), "-i", SRC, "-map", "0:v", "-map", "1:a",
    "-af", f"afade=t=out:st={DUR - 1.8}:d=1.8", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
n = int(DUR * FPS)
for i in range(n):
    ff.stdin.write(render(i / FPS).tobytes())
    if i % 150 == 0: print(f"{i}/{n}", flush=True)
ff.stdin.close(); ff.wait(); print("done", ff.returncode)
