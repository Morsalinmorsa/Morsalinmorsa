"""Join the 8 Tum Bin scenes: mixed transitions on the beat, light film finish, end credit, song audio. 1080x1080.
usage: python3 assemble_mc.py MC_DIR OUT [--preview t1,t2]"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
a = sys.argv[1:]; MD, OUT = a[0], a[1]
PREVIEW = [float(v) for v in a[a.index("--preview") + 1].split(",")] if "--preview" in a else None
O, FPS = 1080, 30
B = [0.0, 3.75, 7.45, 11.85, 15.9, 19.85, 24.0, 28.2, 31.55]; DUR = B[-1]
EXIT = {1: "whip_h", 2: "fade", 3: "cut", 4: "zoom", 5: "whip_v", 6: "zoom", 7: "fade"}
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
f1, f2 = ImageFont.truetype(MONO, 40), ImageFont.truetype(MONO, 30)
RD = os.environ.get("RD", "renders")
# ---------- 2D lyrics on top (always fully visible, never hidden by the 3D scene) ----------
import json
from PIL import ImageFilter
LY = json.load(open(os.path.join(MD, "assets", "lyrics.json")))
BN = ImageFont.truetype(os.path.join(MD, "assets", "fonts", "HindSiliguri-Bold.ttf"), 76)
#        anim       align  y(row1)  glow colour
STYLE = {1: ("rise", "L", 760, (255, 200, 120)), 2: ("pop", "C", 800, (255, 150, 200)), 3: ("flicker", "C", 790, (255, 150, 60)),
         4: ("drop", "L", 150, (255, 170, 90)), 5: ("type", "C", 800, (120, 170, 255)), 6: ("slide", "R", 790, (255, 140, 90)),
         7: ("pop", "C", 810, (255, 170, 110)), 8: ("rise", "C", 800, (255, 130, 170))}
WIMG = {}
def word_img(w, glow):
    if (w, glow) in WIMG: return WIMG[(w, glow)]
    l, t, r, b = BN.getbbox(w); pad = 26
    W, H = r - l + 2 * pad, b - t + 2 * pad
    base = Image.new("L", (W, H), 0); ImageDraw.Draw(base).text((pad - l, pad - t), w, font=BN, fill=255)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = base.filter(ImageFilter.GaussianBlur(6)); out.paste((0, 0, 0, 255), (3, 5), sh.point(lambda v: int(v * 0.75)))
    gl = base.filter(ImageFilter.GaussianBlur(14)); out.paste(glow + (255,), (0, 0), gl.point(lambda v: int(v * 0.55)))
    ol = base.filter(ImageFilter.MaxFilter(5)); out.paste((20, 12, 8, 255), (0, 0), ol.point(lambda v: int(v * 0.6)))
    out.paste((255, 255, 255, 255), (0, 0), base)
    WIMG[(w, glow)] = (out, pad); return WIMG[(w, glow)]
def draw_lyrics(pil, t):
    for li, L in enumerate(LY):
        k = li + 1
        if not (L["s"] - 0.2 <= t <= L["e"] + 0.45): continue
        anim, align, y0, glow = STYLE[k]
        out_a = 1 - smooth((t - L["e"] - 0.1) / 0.35)
        ws = L["words"]; n = len(ws)
        rows = [list(range(n))] if n <= 4 else [list(range((n + 1) // 2)), list(range((n + 1) // 2, n))]
        for ri, idxs in enumerate(rows):
            ims = [word_img(ws[i], glow) for i in idxs]
            gap = 22; widths = [im.width - 2 * p for im, p in ims]; tot = sum(widths) + gap * (len(ims) - 1)
            sc_ = min(1.0, 940 / tot); tot *= sc_
            x = {"L": 70, "C": (O - tot) / 2, "R": O - 70 - tot}[align]; y = y0 + ri * 96
            for (im, p), wd, i in zip(ims, widths, idxs):
                u = (t - L["ws"][i]) / 0.28   # 0..1 entrance
                if u < 0: x += (wd + gap) * sc_; continue
                e = smooth(u); a = e * out_a; dx = dy = 0; s = sc_
                if anim == "rise": dy = 40 * (1 - e)
                elif anim == "drop": dy = -70 * (1 - e) ** 2
                elif anim == "slide": dx = 90 * (1 - e)
                elif anim == "pop": s = sc_ * (0.55 + 0.45 * e + 0.12 * math.sin(math.pi * min(u, 1)))
                elif anim == "flicker": a *= (0.35 + 0.65 * (math.sin(u * 37) > -0.2)) if u < 1.2 else 1.0
                elif anim == "type": a = out_a * (1.0 if u > 0.08 else 0.0)
                w2 = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
                if a < 1: w2.putalpha(w2.getchannel("A").point(lambda v: int(v * max(0, a))))
                cx = x + wd * sc_ / 2 + dx; cy = y + dy
                pil.alpha_composite(w2, (int(cx - w2.width / 2), int(cy - w2.height / 2)))
                x += (wd + gap) * sc_
def smooth(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
cache = {}
def scene(k, t):
    d = os.path.join(MD, RD, f"out_{k}"); n = len(os.listdir(d))
    f = min(max(int(round((t - B[k - 1]) * FPS)) + 1, 1), n)
    if (k, f) not in cache:
        if len(cache) > 12: cache.pop(next(iter(cache)))
        cache[(k, f)] = np.asarray(Image.open(os.path.join(d, f"f_{f:04d}.png")).convert("RGB").resize((O, O), Image.LANCZOS), np.float32)
    return cache[(k, f)]
def zoom(arr, z):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); cw = O / z; x0 = (O - cw) / 2
    return np.asarray(im.transform((O, O), Image.EXTENT, (x0, x0, x0 + cw, x0 + cw), Image.BILINEAR), np.float32)
yy, xx = np.mgrid[0:O, 0:O].astype(np.float32)
VIG = np.clip(1.1 - 0.4 * (((xx - O / 2) / O) ** 2 + ((yy - O / 2) / O) ** 2) * 2.2, 0.6, 1)[..., None]
GR = [np.random.default_rng(i).normal(0, 4, (O // 2, O // 2)).astype(np.float32) for i in range(5)]
def frame(t):
    k = max(i for i in range(1, 9) if B[i - 1] <= t); to_end = B[k] - t; since = t - B[k - 1]
    ex, en = EXIT.get(k), EXIT.get(k - 1); img = scene(k, t)
    if ex == "zoom" and to_end < 0.2: q = 1 - to_end / 0.2; img = np.mean([zoom(img, 1 + 4 * (q + j * 0.07) ** 2) for j in range(3)], 0)
    if en == "zoom" and since < 0.18: img = zoom(img, 1 + 0.25 * (1 - since / 0.18)) + 80 * (1 - since / 0.18)
    if ex == "whip_h" and to_end < 0.15: q = 1 - to_end / 0.15; img = np.mean([np.roll(img, int(700 * (q + j * 0.08) ** 2), 1) for j in range(5)], 0)
    if en == "whip_h" and since < 0.15: q = 1 - since / 0.15; img = np.mean([np.roll(img, -int(600 * (q - j * 0.08) ** 2), 1) for j in range(5)], 0)
    if ex == "whip_v" and to_end < 0.15: q = 1 - to_end / 0.15; img = np.mean([np.roll(img, int(700 * (q + j * 0.08) ** 2), 0) for j in range(5)], 0)
    if en == "whip_v" and since < 0.15: q = 1 - since / 0.15; img = np.mean([np.roll(img, -int(600 * (q - j * 0.08) ** 2), 0) for j in range(5)], 0)
    if ex == "fade" and to_end < 0.45: q = smooth(1 - to_end / 0.45); img = img * (1 - q) + scene(k + 1, min(t + 0.0, B[k] + 0.01)) * q
    if en == "cut" and since < 2 / FPS: img = img * 1.12 + 12
    img = img * VIG + np.repeat(np.repeat(GR[int(t * FPS) % 5], 2, 0), 2, 1)[..., None]
    # opening title + ending credit
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(pil)
    draw_lyrics(pil, t)
    if t < 2.6:
        al = smooth(t / 0.4) * (1 - smooth((t - 2.1) / 0.5))
        d.text((40, 40), "Tum Bin", font=f1, fill=(255, 255, 255, int(235 * al))); d.text((40, 92), "Tanveer Evan", font=f2, fill=(255, 255, 255, int(200 * al)))
    if t > 29.6:
        al = smooth((t - 29.6) / 0.5)
        d.text((O / 2, 120), "Edit by Morsalin", font=f1, fill=(255, 255, 255, int(240 * al)), anchor="mm")
        d.text((O / 2, 170), "Tum Bin · Tanveer Evan", font=f2, fill=(255, 255, 255, int(200 * al)), anchor="mm")
    img = np.asarray(pil.convert("RGB"), np.float32)
    if t > DUR - 0.5: img = img * max(0, (DUR - t) / 0.5)
    return np.clip(img, 0, 255).astype(np.uint8)
if PREVIEW:
    ims = [Image.fromarray(frame(tp)).resize((360, 360)) for tp in PREVIEW]
    st = Image.new("RGB", (360 * len(ims), 360))
    for j, im in enumerate(ims): st.paste(im, (360 * j, 0))
    st.save(OUT); sys.exit()
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{O}x{O}", "-r", str(FPS), "-i", "-",
    "-i", os.path.join(MD, "song.wav"), "-map", "0:v", "-map", "1:a", "-af", f"afade=t=out:st={DUR - 0.8}:d=0.8",
    "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(DUR), OUT],
    stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)): ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print("done", ff.returncode)
