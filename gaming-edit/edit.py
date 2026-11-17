"""Beat-synced Free Fire edit, 1080x1920 for TikTok.
usage: python3 edit.py WORKDIR MUSIC_SRC OUT [--preview t1,t2,...]
"""
import sys, os, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H, FPS = 1080, 1920, 30
wd, music_src, out = sys.argv[1], sys.argv[2], sys.argv[3]
preview = [float(v) for v in sys.argv[5].split(",")] if len(sys.argv) > 5 and sys.argv[4] == "--preview" else None
FR = sorted(os.listdir(os.path.join(wd, "frames")))
NSRC = len(FR); SRC_FPS = 30.0
SRC_END = (NSRC - 1) / SRC_FPS

BEAT, B0 = 0.4812, 0.35
beat = lambda k: B0 + k * BEAT
# (output time, source time) anchors: big shots land on beats
ANCH = [(0.0, 0.0), (beat(0), 0.75), (beat(6), 3.52), (beat(8), 4.34), (beat(10), 5.21), (beat(16), 7.85),
        (beat(20), 10.01), (beat(25), 12.50), (beat(29), 14.48), (beat(32), 15.78), (beat(36), 16.75),
        (beat(40), 17.49), (beat(44), 19.38), (beat(48), 20.64)]
SHOTS_OUT = [a for a, _ in ANCH[1:]]
FREEZE_AT = beat(48)
END = 24.85
SLOW = (beat(32), beat(44))   # breakdown: slow-mo look
DROP = beat(48)

def src_time(t):
    if t >= FREEZE_AT:
        return min(20.64 + (t - FREEZE_AT) * 0.06, SRC_END)
    for (a0, s0), (a1, s1) in zip(ANCH, ANCH[1:]):
        if a0 <= t <= a1:
            u = (t - a0) / (a1 - a0)
            avg = (s1 - s0) / (a1 - a0)
            k = 0.55 if avg >= 0.8 else 0.25        # velocity ramp: slow at the shot, fast between
            g = u - k * math.sin(2 * math.pi * u) / (2 * math.pi)
            return s0 + (s1 - s0) * g
    return SRC_END

_cache = {}
def load(i):
    i = max(0, min(NSRC - 1, i))
    if i not in _cache:
        if len(_cache) > 40: _cache.pop(next(iter(_cache)))
        _cache[i] = np.asarray(Image.open(os.path.join(wd, "frames", FR[i])).convert("RGB"), np.float32)
    return _cache[i]
def src_frame(s):
    f = s * SRC_FPS; i = int(f); a = f - i
    if a < 0.15 or i + 1 >= NSRC: return load(i)
    if a > 0.85: return load(i + 1)
    return load(i) * (1 - a) + load(i + 1) * a

fd = os.path.join(wd, "fonts")
F = lambda n, s: ImageFont.truetype(os.path.join(fd, n), s)
f_big = F("Anton.ttf", 170); f_mid = F("Bebas.ttf", 74); f_tag = F("Rajdhani.ttf", 44); f_gg = F("Anton.ttf", 330)

def ease(t):
    t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3

def text_img(txt, font, fill=(255, 255, 255), stroke=0, sfill=(0, 0, 0), spacing=0):
    bb = font.getbbox(txt)
    w_ = int(bb[2] - bb[0] + 40 + spacing * len(txt)); h_ = bb[3] - bb[1] + 40
    im = Image.new("RGBA", (w_, h_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if spacing:
        x = 20
        for c in txt:
            d.text((x, 20 - bb[1]), c, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill); x += font.getlength(c) + spacing
    else:
        d.text((20 - bb[0], 20 - bb[1]), txt, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return im
def neon(im, col, r=14):
    a = im.getchannel("A")
    g = Image.new("RGBA", im.size, col + (0,)); g.putalpha(a)
    g = g.resize((im.width // 3, im.height // 3)).filter(ImageFilter.GaussianBlur(r / 3)).resize(im.size)
    out_ = Image.new("RGBA", im.size); out_.alpha_composite(g); out_.alpha_composite(g); out_.alpha_composite(im)
    return out_
T_STORM = neon(text_img("STORM", f_big, (255, 255, 255), 3, (255, 40, 90)), (255, 40, 120), 24)
T_SUB = neon(text_img("AWM  •  SOLO VS SQUAD", f_mid, (255, 214, 60), spacing=4), (255, 140, 0), 10)
T_SLOW = neon(text_img("1 VS 4", f_big, (255, 255, 255), 3, (0, 200, 255)), (0, 170, 255), 24)
T_GG = neon(text_img("GG", f_gg, (255, 255, 255), 5, (255, 40, 90)), (255, 30, 90), 30)
T_TAG = text_img("FREE FIRE", f_tag, (255, 255, 255), spacing=10)

def place(base, im, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.01 or scale <= 0.01: return
    if scale != 1: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

PW, PH = 1080, 810          # gameplay panel (4:3 crop)
PY = 520                     # panel top
def frame(t):
    s = src_time(t)
    raw = src_frame(s)                       # 720x1280
    # shot impact: closest anchor before t
    last = max([a for a in SHOTS_OUT if a <= t + 1e-6], default=-9)
    imp = math.exp(-(t - last) / 0.13) if t >= last else 0
    kb = math.floor((t - B0) / BEAT); since = t - B0 - kb * BEAT
    bp = math.exp(-since / 0.09) if t >= B0 else 0
    slow = SLOW[0] <= t < SLOW[1]
    if slow: bp *= 0.3
    frz = t >= FREEZE_AT

    # zoom punch on shots & beats, slow push-in during freeze
    z = 1.0 + 0.10 * imp + 0.025 * bp + (0.18 * ease((t - FREEZE_AT) / 1.2) if frz else 0)
    cw, ch = 960 / z, 720 / z
    jx = 14 * imp * math.sin(t * 97); jy = 14 * imp * math.cos(t * 83)
    x0 = (1280 - cw) / 2 + jx; y0 = (720 - ch) / 2 + jy
    x0 = min(max(x0, 0), 1280 - cw); y0 = min(max(y0, 0), 720 - ch)
    img_src = Image.fromarray(np.clip(raw, 0, 255).astype(np.uint8))
    panel = img_src.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((PW, PH), Image.BILINEAR)
    panel = ImageEnhance.Contrast(ImageEnhance.Color(panel).enhance(1.35 if not slow else 0.75)).enhance(1.12)

    # background: blurred gameplay
    bg = img_src.resize((180, 101)).filter(ImageFilter.GaussianBlur(3)).crop((45, 0, 135, 101)).resize((W, H), Image.BILINEAR)
    bg = ImageEnhance.Brightness(ImageEnhance.Color(bg).enhance(1.6)).enhance(0.38)
    canvas = bg.convert("RGBA")
    # neon frame behind panel
    hue_t = t * 0.6
    col = (int(255 * (0.5 + 0.5 * math.sin(hue_t))), int(80 + 80 * math.sin(hue_t + 2)), int(255 * (0.5 + 0.5 * math.sin(hue_t + 4))))
    if slow: col = (0, 190, 255)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rectangle([-10, PY - 10, W + 10, PY + PH + 10], fill=col + (int(170 + 85 * max(bp, imp)),))
    glow = glow.resize((W // 6, H // 6)).filter(ImageFilter.GaussianBlur(7)).resize((W, H))
    canvas.alpha_composite(glow)
    canvas.paste(panel, (0, PY))
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, PY - 3, W, PY], fill=col + (255,)); d.rectangle([0, PY + PH, W, PY + PH + 3], fill=col + (255,))

    # --- text ---
    it = ease((t - 0.05) / 0.35)
    if not frz:
        sc = 1.0 + 0.06 * bp + 0.5 * (1 - it)
        place(canvas, T_STORM, W / 2, 250, sc, it)
        place(canvas, T_SUB, W / 2, 400, 1.0, ease((t - 0.25) / 0.4))
    if slow:
        st = ease((t - SLOW[0]) / 0.3) * (1 - ease((t - SLOW[1] + 0.4) / 0.4))
        place(canvas, T_SLOW, W / 2, PY + PH + 200, 1.0 + 0.3 * (1 - ease((t - SLOW[0]) / 0.3)), st)
        place(canvas, T_TAG, W / 2, PY + PH + 330, 1.0, st * 0.8)
        # cinematic bars over the panel
        d.rectangle([0, PY, W, PY + 55], fill=(0, 0, 0, 255)); d.rectangle([0, PY + PH - 55, W, PY + PH], fill=(0, 0, 0, 255))
    if frz:
        gp = ease((t - FREEZE_AT) / 0.25)
        place(canvas, T_GG, W / 2, 300, 1.0 + 1.2 * (1 - gp) + 0.05 * bp, gp)
        place(canvas, T_SUB, W / 2, PY + PH + 160, 1.0, ease((t - FREEZE_AT - 0.3) / 0.3))

    arr = np.asarray(canvas.convert("RGB"), np.float32)
    if slow:
        arr = arr * np.array([0.85, 0.95, 1.12])
    # flash + chromatic split
    drop_flash = math.exp(-(t - DROP) / 0.14) if t >= DROP else 0
    arr = arr + 255 * (0.16 * imp + 0.45 * drop_flash)
    sh = int(round(9 * imp + 3 * bp + 16 * drop_flash))
    if sh:
        arr = np.stack([np.roll(arr[..., 0], sh, 1), arr[..., 1], np.roll(arr[..., 2], -sh, 1)], -1)
    fa = min(ease(t / 0.15), ease((END - t) / 0.35))
    return np.clip(arr * fa, 0, 255).astype(np.uint8)

# ---------------- audio: music + gunshot hits ----------------
def build_audio(path):
    sr = 44100
    m = subprocess.run(["ffmpeg", "-v", "error", "-i", music_src, "-t", str(END), "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    m = np.frombuffer(m, np.float32).reshape(-1, 2).copy()
    g = np.fromfile(os.path.join(wd, "game44.raw"), np.float32).reshape(-1, 2)
    for t_out, s in ANCH[1:]:
        a = int((s - 0.02) * sr); b = a + int(0.55 * sr)
        clip = g[a:b].copy()
        if not len(clip): continue
        env = np.minimum(1, np.linspace(1.6, 0, len(clip)))[:, None] ** 1.5
        o = int((t_out - 0.02) * sr)
        n = min(len(clip), len(m) - o)
        if n > 0: m[o:o + n] += clip[:n] * env[:n] * 0.85
    fade = int(0.35 * sr); m[-fade:] *= np.linspace(1, 0, fade)[:, None]
    m = m / max(1.0, np.abs(m).max() / 0.98)
    with wave.open(path, "wb") as w_:
        w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(sr)
        w_.writeframes((m * 32767).astype(np.int16).tobytes())

if preview:
    ims = [Image.fromarray(frame(tp)).resize((360, 640)) for tp in preview]
    strip = Image.new("RGB", (360 * len(ims), 640))
    for i, im in enumerate(ims): strip.paste(im, (360 * i, 0))
    strip.save(out); sys.exit()

apath = os.path.join(wd, "mix.wav"); build_audio(apath)
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", apath, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-maxrate", "16M", "-bufsize", "32M", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
n = int(END * FPS)
for i in range(n):
    ff.stdin.write(frame(i / FPS).tobytes())
    if i % 150 == 0: print(f"{i}/{n}", flush=True)
ff.stdin.close(); ff.wait(); print("done", ff.returncode)
