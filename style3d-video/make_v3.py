"""Shudhu Tomake, reference style v3 ("hand-edited feel").
Per-scene text animators and hand-placed layouts, beat-quantised keyframes, handheld camera, per-scene grades,
light leaks / dust / gate weave, and mixed transitions (cuts, whips, glitch, zoom, fade). Square 1080x1080.
usage: python3 make_v3.py LYRICDIR SRC OUT [--preview t1,t2,...]
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

O, FPS, WS = 1080, 30, 1400
START, DUR = 78.0, 36.5
BEAT0, BEAT = 79.90 - START, 0.4616
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
LD = None; FD = None
rng = np.random.default_rng(3)
R = ImageFont.Layout.RAQM
def FB(n, s): return ImageFont.truetype(os.path.join(FD, n), s, layout_engine=R)
def ease(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3
def smooth(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
def noise1(t, seed, f=(0.7, 1.9, 4.3)):
    r = np.random.default_rng(seed); ph = r.uniform(0, 6.28, 3)
    return sum(math.sin(t * fi * 2 * math.pi * 0.25 + p) / (i + 1) for i, (fi, p) in enumerate(zip(f, ph))) / 1.83

# ---------------- lyrics, beat-quantised ----------------
def load_lines():
    L = []
    for ln in open(os.path.join(LD, "lyrics.txt"), encoding="utf-8"):
        a, b, txt = ln.strip().split(" ", 2); a, b = float(a), float(b)
        ws = txt.split(); lens = np.array([len(w) + 1.5 for w in ws])
        st = a + 0.12 + np.concatenate([[0], np.cumsum(lens)[:-1]]) / lens.sum() * (b - a) * 0.66
        q = []
        for x in st:   # snap to the half-beat grid, keep order
            v = BEAT0 + round((x - BEAT0) / (BEAT / 2)) * (BEAT / 2)
            v = max(v, a + 0.05, (q[-1] + BEAT / 2) if q else 0); q.append(v)
        L.append(dict(s=a, e=b, words=ws, ws=q))
    return L

# ---------------- textures ----------------
def blocks(w, h, bs, palette, jitter=0.12):
    """block texture with Minecraft-like 'pixels' inside each block and soft bevel"""
    gw, gh = math.ceil(w / bs), math.ceil(h / bs)
    pal = np.array(palette, np.float32)
    col = pal[rng.integers(0, len(pal), (gh, gw))] * (1 + rng.uniform(-jitter, jitter, (gh, gw, 1)))
    img = np.repeat(np.repeat(col, bs, 0), bs, 1)[:h, :w]
    px = max(2, bs // 8)
    fine = rng.uniform(0.86, 1.12, (math.ceil(h / px), math.ceil(w / px), 1))
    img = img * np.repeat(np.repeat(fine, px, 0), px, 1)[:h, :w]
    yy, xx = np.mgrid[0:h, 0:w] % bs; e = max(2, bs // 12)
    img = img * np.where((yy < e) | (xx < e), 1.12, 1.0)[..., None] * np.where((yy >= bs - e) | (xx >= bs - e), 0.78, 1.0)[..., None]
    return np.clip(img, 0, 255)
def vgrad(w, h, c1, c2, p=1.0):
    k = (np.linspace(0, 1, h) ** p)[:, None, None]
    return np.array(c1, np.float32) * (1 - k) + np.array(c2, np.float32) * k * np.ones((1, w, 1))
def glow_spot(arr, cx, cy, r, col, amt=1.0):
    h, w = arr.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return arr + np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))[..., None] * np.array(col, np.float32) * amt
def light_dir(arr, strength=0.25):
    h, w = arr.shape[:2]; k = (np.linspace(0, 1, w)[None, :] * 0.6 + np.linspace(0, 1, h)[:, None] * 0.4)
    return arr * (1 - strength * k)[..., None]
def chequer(w, h, horizon, c1=(235, 232, 228), c2=(28, 26, 30), n=14):
    out = np.zeros((h, w, 3), np.float32); ys = np.arange(horizon, h)
    d = (ys - horizon + 8) / (h - horizon); z = 1 / d
    xx = (np.arange(w)[None, :] - w / 2) / (w / 2) * z[:, None]
    cell = (np.floor(xx * n / 3) + np.floor(z[:, None] * 3)) % 2
    fog = np.clip(d * 1.6, 0, 1)[:, None, None]
    out[horizon:] = np.where(cell[..., None] == 0, np.array(c1, np.float32), np.array(c2, np.float32)) * (0.35 + 0.65 * fog)
    out[horizon:] *= rng.uniform(0.94, 1.06, (h - horizon, 1, 1))
    return out

def text_sprite(word, font, face, extrude=(40, 20, 20), depth=10, pixel=0, grad=None, glow=None):
    if pixel:
        f = FB(font[0], font[1] // pixel); bb = f.getbbox(word); w, h = bb[2] - bb[0] + 6, bb[3] - bb[1] + 6
        m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m); d.fontmode = "1"; d.text((3 - bb[0], 3 - bb[1]), word, font=f, fill=255)
        m = m.resize((w * pixel, h * pixel), Image.NEAREST)
    else:
        f = FB(*font); bb = f.getbbox(word); w, h = bb[2] - bb[0] + 20, bb[3] - bb[1] + 20
        m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((10 - bb[0], 10 - bb[1]), word, font=f, fill=255)
    pad = depth + 40; out = Image.new("RGBA", (m.width + 2 * pad, m.height + 2 * pad), (0, 0, 0, 0))
    if glow:
        g = Image.new("RGBA", out.size, glow + (0,)); gm = Image.new("L", out.size, 0); gm.paste(m, (pad, pad))
        g.putalpha(gm.filter(ImageFilter.GaussianBlur(18)).point(lambda v: min(255, v * 2))); out.alpha_composite(g); out.alpha_composite(g)
    for k in range(depth, 0, -1):
        sh = Image.new("RGBA", m.size, tuple(int(c * (0.6 + 0.4 * k / depth)) for c in extrude) + (255,)); sh.putalpha(m)
        out.alpha_composite(sh, (pad + k, pad + k))
    if grad:
        g = np.linspace(0, 1, m.height)[:, None, None]
        fimg = Image.fromarray(((np.array(grad[0]) * (1 - g) + np.array(grad[1]) * g) * np.ones((1, m.width, 1))).astype(np.uint8), "RGB").convert("RGBA")
    else:
        fimg = Image.new("RGBA", m.size, face + (255,))
    fimg.putalpha(m); out.alpha_composite(fimg, (pad, pad))
    return out

class Scene:
    def __init__(s, name, t0, t1, world, line=None, words=None, anim="rise", cam=None, dyn=None, front=None, grade=None, exit="cut"):
        s.name, s.t0, s.t1, s.world, s.line, s.words, s.anim = name, t0, t1, world, line, words or [], anim
        s.cam, s.dyn, s.front, s.grade, s.exit = cam, dyn, front, grade or {}, exit

def build(L):
    SC = []
    ART = Image.open(os.path.join(LD, "art.png")).convert("RGB")
    # --- SC00 intro: black, flicker title (screen-space)
    SC.append(Scene("SC00_INTRO", 0, L[0]["s"], np.zeros((WS, WS, 3), np.float32) + 8, cam=lambda u, t: (700, 700, 1.25 + 0.1 * u, 0),
                    grade=dict(gain=(1, 1, 1)), exit="cut"))
    # --- SC01 lantern night: words float up, hand-placed
    a = vgrad(WS, WS, (10, 14, 44), (70, 34, 92), 1.3)
    a[880:] = blocks(WS, WS - 880, 56, [(78, 52, 34), (95, 64, 40), (70, 46, 30)])
    a[880:936] = blocks(WS, 56, 56, [(70, 140, 50), (82, 160, 58), (60, 120, 45)])
    for _ in range(140):
        x, y, s_ = rng.integers(0, WS), rng.integers(0, 820), rng.integers(2, 6); a[y:y + s_, x:x + s_] = rng.integers(180, 255)
    a[700:820, 640:760] = blocks(120, 120, 30, [(255, 190, 60), (255, 160, 40), (250, 210, 90)])
    a = glow_spot(a, 700, 760, 160, (255, 170, 60), 0.9); a = glow_spot(a, 700, 760, 420, (255, 120, 40), 0.35)
    w = L[0]["words"]
    words = [(text_sprite(w[0], ("HindSiliguri-Bold.ttf", 120), (255, 236, 190), (120, 60, 20), 8), 470, 330, -7),
             (text_sprite(w[1], ("HindSiliguri-Bold.ttf", 150), (255, 236, 190), (120, 60, 20), 10), 860, 420, 4),
             (text_sprite(w[2], ("HindSiliguri-Bold.ttf", 230), (255, 240, 200), (130, 70, 20), 14, glow=(255, 170, 60)), 690, 600, -2)]
    SC.append(Scene("SC01_LANTERN_NIGHT", L[0]["s"], L[1]["s"], light_dir(a, 0.2), L[0], words, "rise",
                    cam=lambda u, t: (680, 560, 1.08 + 0.18 * u, -2 + 4 * u), grade=dict(lift=(4, 8, 18), gain=(1.08, 1.0, 0.92)), exit="whip_h"))
    # --- SC02 shadow wall: words as cast shadows, revealed by the moving spotlight
    a = blocks(WS, WS, 70, [(120, 120, 125), (100, 100, 106), (135, 135, 140), (90, 92, 98)], 0.15)
    sh = []
    for i, (wd, sz) in enumerate(zip(L[1]["words"], (150, 140, 230))):
        t_ = text_sprite(wd, ("HindSiliguri-Bold.ttf", sz), (15, 10, 20), (15, 10, 20), 2).filter(ImageFilter.GaussianBlur(4))
        t_.putalpha(t_.getchannel("A").point(lambda v: int(v * 0.8)))
        sh.append(t_.transform(t_.size, Image.AFFINE, (1, 0.35, -0.175 * t_.height, 0, 1, 0), Image.BICUBIC))
    words = [(sh[0], 560, 470, 3), (sh[1], 840, 620, -2), (sh[2], 700, 840, 1)]
    def wall_dyn(arr, t, u):
        cx = 350 + 700 * smooth(u) + 40 * noise1(t, 11); cy = 650 + 120 * math.sin(t * 2)
        yy, xx = np.mgrid[0:WS:4, 0:WS:4].astype(np.float32)
        g = np.repeat(np.repeat(np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * 380 ** 2)), 4, 0), 4, 1)[..., None]
        return arr * (0.2 + 1.1 * g) + g * np.array([60, 45, 20])
    SC.append(Scene("SC02_SHADOW_WALL", L[1]["s"], L[2]["s"], a, L[1], words, "shadow", dyn=wall_dyn,
                    cam=lambda u, t: (700, 680, 1.2 + 0.08 * u, 3 - 5 * u), grade=dict(sat=0.55, gain=(1.05, 0.98, 0.9)), exit="cut"))
    # --- SC03 block heart: words drop and bounce on the beat
    a = chequer(WS, WS, 760); a[:760] = vgrad(WS, 760, (8, 6, 12), (40, 20, 30))
    HEART = ["0110001100", "1111011110", "1111111111", "1111111111", "0111111110", "0011111100", "0001111000", "0000110000"]
    bs = 88; hx, hy = 700 - 5 * bs, 280
    for r, row in enumerate(HEART):
        for c, ch in enumerate(row):
            if ch == "1": a[hy + r * bs:hy + (r + 1) * bs, hx + c * bs:hx + (c + 1) * bs] = blocks(bs, bs, bs, [(210, 25, 40), (190, 20, 35), (230, 40, 55)], 0.1)
    a = glow_spot(a, 700, 600, 500, (120, 0, 20), 0.5)
    w = L[2]["words"]
    words = [(text_sprite(w[0], ("HindSiliguri-Bold.ttf", 120), (255, 255, 255), (110, 10, 20), 8), 520, 390, -8),
             (text_sprite(w[1], ("HindSiliguri-Bold.ttf", 130), (255, 255, 255), (110, 10, 20), 8), 860, 450, 6),
             (text_sprite(w[2], ("HindSiliguri-Bold.ttf", 175), (255, 255, 255), (110, 10, 20), 12), 690, 620, -3),
             (text_sprite(w[3], ("HindSiliguri-Bold.ttf", 150), (255, 230, 120), (120, 60, 10), 10), 880, 800, 5)]
    SC.append(Scene("SC03_BLOCK_HEART", L[2]["s"], L[3]["s"], light_dir(a, 0.15), L[2], words, "drop",
                    cam=lambda u, t: (700, 620, 1.05 + 0.25 * u, -6 + 10 * u), grade=dict(lift=(-6, -6, -6), gain=(1.08, 0.96, 0.98)), exit="zoom"))
    # --- SC04 night city: pixel words flicker on like signs
    a = vgrad(WS, WS, (20, 8, 50), (110, 40, 120), 1.2); x = 0
    while x < WS:
        bw = min(int(rng.integers(90, 200)), WS - x); bh = int(rng.integers(300, 820)); top = WS - bh
        a[top:, x:x + bw] = blocks(bw, bh, 30, [(25, 22, 40), (32, 28, 50)], 0.08)
        for wy in range(top + 30, WS - 30, 60):
            for wx in range(x + 20, x + bw - 30, 50):
                if rng.random() < 0.45: a[wy:wy + 22, wx:wx + 18] = (255, 220, 120) if rng.random() < 0.8 else (140, 220, 255)
        x += bw + int(rng.integers(0, 20))
    def city_dyn(arr, t, u):
        out = arr.copy(); yy, xx = np.mgrid[0:WS:4, 0:WS:4].astype(np.float32)
        for k, base in enumerate([-0.6, 0.5]):
            ang = base + 0.5 * math.sin(t * 1.3 + k * 2); ox, oy = 350 + 700 * k, WS
            th = np.arctan2(xx - ox, oy - yy); beam = np.exp(-((th - ang) / 0.07) ** 2) * np.clip((oy - yy) / WS, 0, 1)
            out = out + np.repeat(np.repeat(beam, 4, 0), 4, 1)[..., None] * np.array([180, 190, 255]) * 0.6
        return out
    w = L[3]["words"]
    words = [(text_sprite(w[0], ("HindSiliguri-Bold.ttf", 150), (120, 240, 255), (20, 60, 120), 8, pixel=6), 430, 360, 0),
             (text_sprite(w[1], ("HindSiliguri-Bold.ttf", 168), (255, 140, 220), (90, 20, 80), 8, pixel=6), 900, 520, 0),
             (text_sprite(w[2], ("HindSiliguri-Bold.ttf", 190), (255, 230, 120), (110, 70, 10), 10, pixel=6), 620, 720, 0)]
    SC.append(Scene("SC04_CITY_SEARCHLIGHT", L[3]["s"], L[4]["s"], a, L[3], words, "flicker", dyn=city_dyn,
                    cam=lambda u, t: (560 + 260 * smooth(u), 580, 1.12, 0), grade=dict(gain=(0.95, 0.95, 1.1), lift=(6, 0, 14)), exit="glitch"))
    # --- SC05 sunrise: gold block words rise from behind the hills (front layer)
    a = vgrad(WS, WS, (255, 120, 80), (255, 210, 120), 0.8)
    a[300:540, 540:860] = blocks(320, 240, 80, [(255, 240, 150), (255, 225, 120)], 0.05)
    a = glow_spot(a, 700, 420, 300, (255, 200, 100), 0.6)
    front = np.zeros((WS, WS, 4), np.float32)
    for layer, (base, col) in enumerate([(820, (90, 150, 70)), (960, (70, 130, 55))]):
        for x in range(0, WS, 70):
            top = (base + int(80 * math.sin(x / 160 + layer * 2) + rng.integers(-1, 2) * 70)) // 70 * 70
            tgt = a if layer == 0 else front
            blk = blocks(70, WS - top, 70, [(120, 84, 52), (100, 70, 44)]); blk[:70] = blocks(70, 70, 70, [col])
            if layer == 0: a[top:, x:x + 70] = blk
            else: front[top:, x:x + 70, :3] = blk; front[top:, x:x + 70, 3] = 255
    w = L[4]["words"]
    gold = dict(face=(255, 215, 80), extrude=(120, 70, 10), pixel=6, grad=((255, 245, 160), (230, 150, 20)))
    words = [(text_sprite(w[0], ("HindSiliguri-Bold.ttf", 160), gold["face"], gold["extrude"], 12, gold["pixel"], gold["grad"]), 470, 560, 0),
             (text_sprite(w[1], ("HindSiliguri-Bold.ttf", 170), gold["face"], gold["extrude"], 12, gold["pixel"], gold["grad"]), 930, 610, 0),
             (text_sprite(w[2], ("HindSiliguri-Bold.ttf", 230), gold["face"], gold["extrude"], 14, gold["pixel"], gold["grad"]), 700, 790, 0)]
    SC.append(Scene("SC05_SUNRISE_HILLS", L[4]["s"], L[5]["s"], a, L[4], words, "riseclip",
                    front=Image.fromarray(front.astype(np.uint8), "RGBA"),
                    cam=lambda u, t: (700, 720 - 100 * u, 1.12 - 0.06 * u, 0), grade=dict(lift=(22, 14, 8), gain=(1.02, 0.97, 0.88), sat=0.9), exit="whip_v"))
    # --- SC06 vinyl: words printed on the record, they spin with it
    a = vgrad(WS, WS, (34, 20, 14), (10, 6, 4))
    for i in range(0, WS, 40): a[:, i:i + 3] *= 0.85            # wood planks
    disc = Image.new("RGBA", (1200, 1200), (0, 0, 0, 0)); d = ImageDraw.Draw(disc)
    d.ellipse([0, 0, 1199, 1199], fill=(18, 18, 20, 255))
    for r in range(590, 250, -9): d.ellipse([600 - r, 600 - r, 600 + r, 600 + r], outline=(30 + int(r % 27 // 9) * 3, 30, 34, 255), width=2)
    lab = ART.crop(((ART.width - ART.height) // 2, 0, (ART.width + ART.height) // 2, ART.height)).resize((480, 480))
    lm = Image.new("L", (480, 480), 0); ImageDraw.Draw(lm).ellipse([0, 0, 479, 479], fill=255); disc.paste(lab, (360, 360), lm)
    d.ellipse([588, 588, 612, 612], fill=(10, 10, 10, 255))
    w = L[5]["words"]
    words = [(text_sprite(w[0], ("HindSiliguri-Bold.ttf", 96), (245, 245, 245), (60, 60, 60), 3), 600, 180, 0),
             (text_sprite(w[1], ("HindSiliguri-Bold.ttf", 96), (245, 245, 245), (60, 60, 60), 3), 1020, 600, 90),
             (text_sprite(w[2], ("HindSiliguri-Bold.ttf", 110), (255, 220, 120), (90, 60, 10), 3), 600, 1030, 180)]
    s6 = Scene("SC06_VINYL_SPIN", L[5]["s"], L[6]["s"], a, L[5], words, "disc",
               cam=lambda u, t: (700, 700, 1.22 + 0.12 * u, 8 - 14 * u), grade=dict(sat=0.85, gain=(1.0, 1.0, 1.0)), exit="zoom")
    s6.disc = disc; SC.append(s6)
    # --- SC07 neon: words switch on like neon tubes
    a = chequer(WS, WS, 900, (230, 220, 240), (40, 20, 50)); a[:900] = vgrad(WS, 900, (40, 10, 60), (150, 50, 130))
    for _ in range(60):
        x, y, r = rng.integers(0, WS), rng.integers(0, 880), rng.integers(4, 18)
        if r > 11: a = glow_spot(a, x, y, r, (255, 200, 255), 0.8)
    w = L[6]["words"]
    words = [(text_sprite(w[0], ("Galada.ttf", 140), (255, 120, 200), (120, 20, 90), 5, glow=(255, 60, 200)), 470, 330, -6),
             (text_sprite(w[1], ("Galada.ttf", 150), (120, 220, 255), (20, 60, 120), 5, glow=(60, 160, 255)), 900, 400, 5),
             (text_sprite(w[2], ("Galada.ttf", 175), (255, 120, 200), (120, 20, 90), 6, glow=(255, 60, 200)), 650, 610, -3),
             (text_sprite(w[3], ("Galada.ttf", 160), (255, 235, 120), (120, 90, 10), 5, glow=(255, 190, 60)), 960, 790, 8)]
    SC.append(Scene("SC07_NEON_PINK", L[6]["s"], L[7]["s"], a, L[6], words, "neon",
                    cam=lambda u, t: (700, 580, 1.04 + 0.2 * u, 4 * math.sin(t * 0.8)), grade=dict(gain=(1.06, 0.94, 1.06), lift=(10, 0, 12)), exit="black"))
    # --- SC08 typewriter (screen space)
    SC.append(Scene("SC08_TYPEWRITER", L[7]["s"], 32.2, np.zeros((WS, WS, 3), np.float32) + 7, L[7], [], "type",
                    cam=lambda u, t: (700, 700, 1.25 + 0.1 * u, 0), grade=dict(sat=0.0), exit="fade"))
    # --- SC09 credits
    SC.append(Scene("SC09_CREDITS", 32.2, DUR + 1, vgrad(WS, WS, (205, 200, 240), (172, 166, 222)), cam=lambda u, t: (700, 700, 1.25, 0),
                    grade=dict(lift=(10, 8, 12)), exit=None))
    return SC

# ---------------- per-scene word animators ----------------
def place_rot(img, spr, cx, cy, ang=0, alpha=1.0, sx=1.0, sy=1.0):
    if alpha <= 0.01: return
    if sx != 1 or sy != 1: spr = spr.resize((max(1, int(spr.width * sx)), max(1, int(spr.height * sy))), Image.BILINEAR)
    if ang: spr = spr.rotate(ang, Image.BICUBIC, expand=True)
    if alpha < 1: spr = spr.copy(); spr.putalpha(spr.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)))

def words_on(scn, img, t, target=None):
    """draw scene words onto img (world coords). target is used for the vinyl disc layer."""
    for k, (spr, x, y, ang) in enumerate(scn.words):
        ws = scn.line["ws"][k]; p = t - ws
        if scn.anim == "rise":
            q = ease((p + 0.15) / 0.6)
            if q > 0: place_rot(img, spr, x, y + 90 * (1 - q), ang + 6 * (1 - q), q)
        elif scn.anim == "shadow":
            q = smooth((p + 0.1) / 0.7)
            if q > 0: place_rot(img, spr, x + 30 * (1 - q), y, ang, q * 0.95)
        elif scn.anim == "drop":
            if p < -0.3: continue
            if p < 0: place_rot(img, spr, x, y - 700 * (p / 0.3) ** 2, ang, 1.0)
            else:
                b = math.exp(-p / 0.12) * math.cos(p * 30)
                place_rot(img, spr, x, y + 18 * b, ang, 1.0, 1 + 0.12 * b, 1 - 0.16 * b)
        elif scn.anim == "flicker":
            if p < -0.05: continue
            seq = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1]
            on = seq[min(int((p + 0.05) * 30), len(seq) - 1)] if p < 0.32 else 1
            if on: place_rot(img, spr, x, y, ang, 0.95 + 0.05 * math.sin(t * 50 + k))
        elif scn.anim == "riseclip":
            q = ease((p + 0.1) / 0.55)
            if q > 0: place_rot(img, spr, x, y + 300 * (1 - q), ang, 1.0)
        elif scn.anim == "disc":
            if p > -0.05: place_rot(target, spr, x, y, ang, min(1, (p + 0.05) / 0.15))
        elif scn.anim == "neon":
            if p < -0.05: continue
            seq = [0.3, 0, 0.8, 0.2, 1, 0.4, 1, 1, 0.7, 1]
            a = seq[min(int((p + 0.05) * 30), len(seq) - 1)] if p < 0.3 else 0.92 + 0.08 * math.sin(t * 37 + k)
            place_rot(img, spr, x, y, ang, a)

# ---------------- renderer ----------------
class Renderer:
    def __init__(s, lyricdir):
        global LD, FD
        LD = lyricdir; FD = os.path.join(LD, "fonts")
        s.L = load_lines(); s.SC = build(s.L)
        s.f_type = FB("HindSiliguri-Medium.ttf", 100); s.f_m = ImageFont.truetype(MONO, 54); s.f_ms = ImageFont.truetype(MONO, 40)
        yy, xx = np.mgrid[0:O, 0:O].astype(np.float32)
        s.vig = np.clip(1.12 - 0.5 * (((xx - O / 2) / O) ** 2 + ((yy - O / 2) / O) ** 2) * 2.4, 0.45, 1)[..., None]
        s.grain = [np.random.default_rng(i).normal(0, 7, (O // 2, O // 2)).astype(np.float32) for i in range(6)]
        r = np.random.default_rng(9); s.type_jit = r.uniform(0.6, 1.5, 200)

    def scene_at(s, t): return max(i for i, sc in enumerate(s.SC) if sc.t0 <= t + 1e-6)

    def world(s, scn, t):
        u = (t - scn.t0) / max(scn.t1 - scn.t0, 1e-3)
        arr = scn.dyn(scn.world, t, u) if scn.dyn else scn.world
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        if hasattr(scn, "disc"):
            layer = scn.disc.copy(); words_on(scn, None, t, target=layer)
            img.alpha_composite(layer.rotate(-t * 40, Image.BICUBIC), (100, 100))
        elif scn.line and scn.words:
            words_on(scn, img, t)
        if scn.front is not None: img.alpha_composite(scn.front)
        return img, u

    def camera(s, img, cx, cy, z, ang):
        th = math.radians(ang); c, sn = math.cos(th), math.sin(th)
        z = max(z, (abs(c) + abs(sn)) * 1.03); half = WS / z / 2 * (abs(c) + abs(sn))
        cx = min(max(cx, half), WS - half); cy = min(max(cy, half), WS - half); sc = (WS / z) / O
        a, b, d, e = sc * c, -sc * sn, sc * sn, sc * c
        return img.transform((O, O), Image.AFFINE, (a, b, cx - a * O / 2 - b * O / 2, d, e, cy - d * O / 2 - e * O / 2), Image.BILINEAR)

    def screen(s, img, k, t):
        scn = s.SC[k]; d = ImageDraw.Draw(img)
        if k == 0:
            if (int(t * 14) % 4 != 1) or t > 1.1:
                for txt, y, sz, col in [("SHUDHU TOMAKE", 480, 15, (255, 230, 120)), ("FRANKLIN", 600, 9, (255, 255, 255))]:
                    f = ImageFont.truetype(MONO, sz); m = Image.new("L", (int(f.getlength(txt)) + 4, sz + 6), 0)
                    md = ImageDraw.Draw(m); md.fontmode = "1"; md.text((2, 1), txt, font=f, fill=255)
                    m = m.resize((m.width * 5, m.height * 5), Image.NEAREST); face = Image.new("RGBA", m.size, col + (255,)); face.putalpha(m)
                    img.alpha_composite(face, ((O - m.width) // 2 + int(3 * noise1(t, 3)), y - m.height // 2))
        elif scn.anim == "type":
            L = scn.line; full = " ".join(L["words"]); cl = clusters(full)
            t_first = L["ws"][0]; n = 0; acc = t_first
            for i in range(len(cl)):             # uneven, human typing speed
                acc += 0.075 * s.type_jit[i] + (0.18 if cl[i] == " " else 0)
                if acc <= t: n = i + 1
            cur = "|" if int(t * 2.6) % 2 == 0 else " "
            bb = s.f_type.getbbox(full); x0 = (O - (bb[2] - bb[0])) // 2
            d.text((x0 + int(2 * noise1(t, 5)), 560), "".join(cl[:n]) + cur, font=s.f_type, fill=(236, 232, 222), anchor="ls")
        elif k == len(s.SC) - 1:
            a = ease((t - scn.t0) / 0.6) * (1 - ease((t - (DUR - 1.0)) / 0.9)); col = (70, 66, 110, int(255 * a))
            for txt, y, f in [("Shudhu Tomake", 360, s.f_m), ("Franklin", 440, s.f_ms), ("Edited By", 600, s.f_ms), ("Morsalin", 680, s.f_m)]:
                d.text((O / 2, y), txt, font=f, fill=col, anchor="mm")

    def grade(s, arr, g):
        if "sat" in g:
            l = arr.mean(-1, keepdims=True); arr = l + (arr - l) * g["sat"]
        arr = arr * np.array(g.get("gain", (1, 1, 1)), np.float32) + np.array(g.get("lift", (0, 0, 0)), np.float32)
        return arr

    def base(s, k, t, extra_z=1.0, dx=0, dy=0):
        scn = s.SC[k]; img, u = s.world(scn, t)
        cx, cy, z, ang = scn.cam(u, t)
        cx += 9 * noise1(t, 21 + k) + dx; cy += 7 * noise1(t, 41 + k) + dy; ang += 0.5 * noise1(t, 61 + k)   # handheld
        since = (t - BEAT0) % BEAT if t >= BEAT0 else 9
        z *= (1 + 0.012 * math.exp(-since / 0.1)) * extra_z
        out = s.camera(img, cx, cy, z, ang).convert("RGBA"); s.screen(out, k, t)
        return s.grade(np.asarray(out.convert("RGB"), np.float32), scn.grade)

    def frame(s, t):
        k = s.scene_at(t); scn = s.SC[k]
        prev = s.SC[k - 1] if k > 0 else None
        to_end = scn.t1 - t; since = t - scn.t0
        ex = scn.exit; en = prev.exit if prev else None
        if ex == "zoom" and to_end < 0.2:
            q = 1 - to_end / 0.2
            res = np.mean([s.base(k, t, 1 + 5 * (q + j * 0.07) ** 2) for j in range(3)], 0)
        elif ex == "whip_h" and to_end < 0.16:
            q = 1 - to_end / 0.16; res = np.mean([s.base(k, t, dx=900 * (q + j * 0.08) ** 2) for j in range(4)], 0)
        elif en == "whip_h" and since < 0.16:
            q = 1 - since / 0.16; res = np.mean([s.base(k, t, dx=-700 * (q - j * 0.08) ** 2) for j in range(4)], 0)
        elif ex == "whip_v" and to_end < 0.16:
            q = 1 - to_end / 0.16; res = np.mean([s.base(k, t, dy=900 * (q + j * 0.08) ** 2) for j in range(4)], 0)
        elif en == "whip_v" and since < 0.16:
            q = 1 - since / 0.16; res = np.mean([s.base(k, t, dy=-700 * (q - j * 0.08) ** 2) for j in range(4)], 0)
        elif ex == "fade" and to_end < 0.5:
            q = smooth(1 - to_end / 0.5); res = s.base(k, t) * (1 - q) + s.base(k + 1, t) * q
        else:
            res = s.base(k, t)
            if en == "zoom" and since < 0.18: res = res + 120 * (1 - since / 0.18)
        # glitch cut (both sides of the boundary)
        gl = None
        if ex == "glitch" and to_end < 0.1: gl = (k, k + 1, 1 - to_end / 0.1)
        if en == "glitch" and since < 0.1: gl = (k - 1, k, since / 0.1)
        if gl:
            other = s.base(gl[1] if gl[0] == k else gl[0], t); r = np.random.default_rng(int(t * 1000))
            for _ in range(9):
                y0 = int(r.integers(0, O - 60)); h = int(r.integers(12, 90)); off = int(r.integers(-120, 120))
                src = other if r.random() < 0.5 else res
                res[y0:y0 + h] = np.roll(src[y0:y0 + h], off, axis=1)
            res = np.stack([np.roll(res[..., 0], 14, 1), res[..., 1], np.roll(res[..., 2], -14, 1)], -1)
        if en == "cut" and since < 2 / FPS: res = res * 1.25 + 20
        # bloom
        small = Image.fromarray(np.clip((res - 165) * 2, 0, 255).astype(np.uint8)).resize((O // 4, O // 4)).filter(ImageFilter.GaussianBlur(6)).resize((O, O))
        res = res + np.asarray(small, np.float32) * 0.42
        # light leak on warm scenes
        if scn.name in ("SC01_LANTERN_NIGHT", "SC05_SUNRISE_HILLS", "SC07_NEON_PINK"):
            lx = O * (0.15 + 0.7 * (0.5 + 0.5 * math.sin(t * 0.7 + k))); amt = 0.18 + 0.12 * noise1(t, 77)
            yy = np.linspace(0, 1, O)[:, None]; xx = np.arange(O)[None, :]
            leak = np.exp(-((xx - lx) ** 2) / (2 * 220 ** 2)) * (0.6 + 0.4 * yy)
            res = res + leak[..., None] * np.array([255, 120, 50]) * amt
        # film: gate weave, vignette, grain, dust, slight edge fringing
        fi = int(t * FPS)
        res = np.roll(res, (int(round(1.2 * noise1(t * 3, 5))), int(round(1.2 * noise1(t * 3, 6)))), (0, 1))
        res = res * s.vig + np.repeat(np.repeat(s.grain[fi % 6], 2, 0), 2, 1)[..., None]
        r = np.random.default_rng(fi)
        if r.random() < 0.35:
            for _ in range(int(r.integers(1, 5))):
                x, y = int(r.integers(0, O - 4)), int(r.integers(0, O - 4)); sz = int(r.integers(1, 4))
                res[y:y + sz, x:x + sz] = 235 if r.random() < 0.6 else 20
        if r.random() < 0.06:
            x = int(r.integers(80, O - 80)); res[:, x:x + 1] = res[:, x:x + 1] * 0.6 + 90
        res = np.stack([np.roll(res[..., 0], 1, 1), res[..., 1], np.roll(res[..., 2], -1, 1)], -1)
        if t < 0.1: res = res * 0 + 250
        if t > DUR - 0.5: res = res * max(0.0, (DUR - t) / 0.5)
        return np.clip(res, 0, 255).astype(np.uint8)

def clusters(s_):
    out = []
    for ch in s_:
        if out and (0x0981 <= ord(ch) <= 0x0983 or 0x09BC <= ord(ch) <= 0x09D7 or ch in "‌‍" or out[-1].endswith("্")): out[-1] += ch
        else: out.append(ch)
    return out

if __name__ == "__main__":
    a = sys.argv[1:]; LDIR, SRC, OUT = a[0], a[1], a[2]
    PREVIEW = [float(v) for v in a[a.index("--preview") + 1].split(",")] if "--preview" in a else None
    Rn = Renderer(LDIR)
    if PREVIEW:
        ims = [Image.fromarray(Rn.frame(tp)).resize((360, 360)) for tp in PREVIEW]
        cols = 5; rows = math.ceil(len(ims) / cols); st = Image.new("RGB", (360 * cols, 360 * rows))
        for j, im in enumerate(ims): st.paste(im, (360 * (j % cols), 360 * (j // cols)))
        st.save(OUT); sys.exit()
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{O}x{O}", "-r", str(FPS), "-i", "-",
        "-ss", str(START), "-t", str(DUR), "-i", SRC, "-map", "0:v", "-map", "1:a", "-af", f"afade=t=out:st={DUR - 1.8}:d=1.8",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        ff.stdin.write(Rn.frame(i / FPS).tobytes())
        if i % 150 == 0: print(f"{i}/{n}", flush=True)
    ff.stdin.close(); ff.wait(); print("done", ff.returncode)
