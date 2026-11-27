"""Part 2: 'Behind The Scenes' for the 3D-style Shudhu Tomake video (1080x1080).
usage: python3 bts.py PART1_MP4 SONG_SRC OUT [--preview t1,t2]
"""
import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

args = sys.argv[1:]
P1, SONG, OUT = args[0], args[1], args[2]
PREVIEW = [float(v) for v in args[args.index("--preview") + 1].split(",")] if "--preview" in args else None
O, FPS, DUR = 1080, 30, 30.0
SONG_START = 78.0 + 36.5           # continue right after part 1
P1_DUR = 36.5
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"; MONOB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
f_card = ImageFont.truetype(MONO, 150); f_ui = ImageFont.truetype(SANS, 20); f_uis = ImageFont.truetype(SANS, 17); f_tc = ImageFont.truetype(MONOB, 20)
rng = np.random.default_rng(5)
def ease(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3

# --- part-1 frame reader (sequential or random) ---
FS = 1080 * 1080 * 3
class Reader:
    def __init__(s): s.p = None; s.i = -1; s.cur = None
    def at(s, t):
        i = int(min(max(t, 0), P1_DUR - 0.05) * 30)
        if PREVIEW:
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{i/30:.3f}", "-i", P1, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            return Image.frombytes("RGB", (1080, 1080), r[:FS])
        if s.p is None: s.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", P1, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        while s.i < i:
            b = s.p.stdout.read(FS)
            if len(b) < FS: break
            s.cur = Image.frombytes("RGB", (1080, 1080), b); s.i += 1
        return s.cur
RD = Reader()
# lyric scene starts in part 1 (from lyrics.txt) for scene names / colours
SCENES = [(0.0, "SC00_INTRO_TITLE"), (1.75, "SC01_LANTERN_NIGHT"), (5.44, "SC02_SHADOW_WALL"), (9.14, "SC03_BLOCK_HEART"),
          (12.83, "SC04_CITY_SEARCHLIGHT"), (16.52, "SC05_SUNRISE_HILLS"), (20.21, "SC06_VINYL_SPIN"),
          (23.91, "SC07_NEON_PINK"), (27.60, "SC08_TYPEWRITER"), (32.2, "SC09_CREDITS")]
COLS = [(170, 160, 220), (150, 200, 190), (200, 120, 120), (190, 175, 110), (140, 170, 210), (200, 150, 200)]

# ---------- section A: title card with gizmo lines (0 - 4.5 s) ----------
NODES = [(rng.uniform(80, 1000), rng.uniform(80, 1000)) for _ in range(46)]
def title_card(t):
    img = Image.new("RGB", (O, O), (243, 236, 238)); d = ImageDraw.Draw(img, "RGBA")
    k = ease((t - 0.8) / 2.5)
    # wireframe gizmos drawing in
    for i in range(len(NODES) - 1):
        if i / len(NODES) > k: break
        (x1, y1), (x2, y2) = NODES[i], NODES[(i * 7 + 3) % len(NODES)]
        col = (140, 60, 200, 170) if i % 3 else (230, 150, 30, 190)
        d.line([x1, y1, x2, y2], fill=col, width=3)
        d.rectangle([x1 - 7, y1 - 7, x1 + 7, y1 + 7], fill=(200, 40, 60, 220) if i % 2 else (90, 90, 230, 220))
    for j, word in enumerate(["Behind", "The", "Scenes"]):
        d.text((O / 2, 300 + j * 230), word, font=f_card, fill=(20, 20, 30), anchor="mm")
    if k > 0:   # frame border like a layer bounding box
        d.rectangle([40, 40, O - 40, O - 40], outline=(30, 30, 30, int(200 * k)), width=3)
    return img

# ---------- helpers for the editor ----------
def wire(img):
    """edge-detected wireframe look of a frame"""
    e = img.convert("L").filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
    a = np.asarray(img, np.float32) * 0.18
    m = np.asarray(e, np.float32)[..., None] / 255
    out = a * (1 - m) + m * np.array([235, 225, 255])
    return Image.fromarray(out.astype(np.uint8))
def checker(w, h, s=24):
    yy, xx = np.mgrid[0:h, 0:w]; c = ((yy // s + xx // s) % 2)[..., None]
    return Image.fromarray(np.where(c, 255, 205).repeat(3, 2).astype(np.uint8))
def persp(img, tilt):
    """fake 3D tilt of a layer: perspective quad"""
    w, h = img.size; dx = w * 0.18 * tilt; dy = h * 0.22 * abs(tilt)
    quad_out = [(dx, dy), (w - dx * 0.3, 0), (w, h - dy * 0.4), (0, h)]
    # PIL QUAD maps output rect -> input quad; we want inverse look, so compose onto transparent canvas
    coeffs = find_coeffs([(0, 0), (w, 0), (w, h), (0, h)], quad_out)
    return img.convert("RGBA").transform((w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC), quad_out
def find_coeffs(src, dst):
    A = []
    for (x, y), (X, Y) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y]); A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
    A = np.array(A, float); B = np.array(src, float).reshape(8)
    return np.linalg.solve(A, B)

def editor(t):
    """generic dark compositing-app screen"""
    lt = 1.75 + (t - 7.0) * (P1_DUR - 1.75) / (DUR - 7.0 - 0.3)     # part-1 time shown
    frame = RD.at(lt)
    sc = max(i for i, (s0, _) in enumerate(SCENES) if s0 <= lt)
    img = Image.new("RGB", (O, O), (35, 35, 38)); d = ImageDraw.Draw(img, "RGBA")
    # toolbar
    d.rectangle([0, 0, O, 52], fill=(28, 28, 30))
    for i, x in enumerate(range(18, 520, 52)): d.rounded_rectangle([x, 12, x + 30, 40], 5, outline=(150, 150, 155), width=2)
    d.text((O - 210, 26), "Default      Review", font=f_ui, fill=(170, 170, 175), anchor="lm")
    d.rectangle([0, 52, O, 92], fill=(40, 40, 44))
    d.text((16, 72), f"Composition  {SCENES[sc][1]}", font=f_ui, fill=(210, 210, 215), anchor="lm")
    # viewports
    VY0, VY1 = 100, 640
    d.rectangle([0, VY0, 538, VY1], fill=(30, 30, 32)); d.rectangle([542, VY0, O, VY1], fill=(30, 30, 32))
    d.text((12, VY0 + 16), "Active Camera", font=f_uis, fill=(200, 200, 205), anchor="lm")
    d.text((556, VY0 + 16), "Custom View 1", font=f_uis, fill=(200, 200, 205), anchor="lm")
    # left: rendered frame with layer bounding box + null points
    lv = frame.resize((420, 420), Image.BILINEAR); img.paste(lv, (58, 160))
    d.rectangle([58, 160, 478, 580], outline=(200, 60, 60), width=2)
    for (x, y) in [(58, 160), (268, 160), (478, 160), (478, 370), (478, 580), (268, 580), (58, 580), (58, 370)]:
        d.rectangle([x - 5, y - 5, x + 5, y + 5], fill=(220, 60, 60))
    for i in range(14):
        a = t * 0.6 + i * 0.45; x = 268 + 230 * math.cos(a) * (0.5 + 0.5 * math.sin(i)); y = 370 + 200 * math.sin(a * 1.1 + i)
        d.rectangle([x - 4, y - 4, x + 4, y + 4], outline=(220, 220, 230), width=2)
        if i % 3 == 0: d.line([268, 370, x, y], fill=(200, 200, 210, 90), width=1)
    # right: tilted layer (wireframe of the frame on a checker plane) + gizmo
    rv = Image.blend(checker(420, 420), wire(frame.resize((420, 420))), 0.85)
    tilt = 0.6 * math.sin(t * 0.5)
    lay, quad = persp(rv, tilt)
    img.paste(lay, (600, 165), lay)
    cx, cy = 600 + 210, 165 + 210
    for i in range(9):
        a = t * 0.8 + i; px = cx + 160 * math.sin(a); py = cy - 230 + 40 * math.cos(a * 1.3)
        d.rectangle([px - 6, py - 6, px + 6, py + 6], fill=(210, 50, 60)); d.line([px, py, cx, cy + 30], fill=(220, 200, 220, 110), width=2)
    d.line([cx, cy, cx + 110, cy - 50], fill=(230, 60, 60), width=4); d.line([cx, cy, cx + 30, cy - 120], fill=(60, 220, 90), width=4)
    d.line([cx, cy, cx - 60, cy + 70], fill=(70, 120, 240), width=4)
    # viewport footer
    d.rectangle([0, VY1, O, VY1 + 38], fill=(28, 28, 30))
    tc = f"0:00:{int(lt):02d}:{int((lt % 1) * 30):02d}"
    d.text((540, VY1 + 19), tc, font=f_tc, fill=(160, 200, 255), anchor="mm")
    d.text((80, VY1 + 19), "Third", font=f_uis, fill=(200, 200, 205), anchor="lm"); d.text((690, VY1 + 19), "Draft 3D", font=f_uis, fill=(200, 200, 205), anchor="lm")
    # timeline
    TY = VY1 + 46
    d.rectangle([0, TY, O, O], fill=(33, 33, 36))
    tabs = [s[1].split("_", 1)[1].title().replace("_", " ") + " Comp" for s in SCENES[max(0, sc - 1):sc + 3]]
    x = 10
    for j, tb in enumerate(tabs):
        w = f_uis.getlength(tb) + 30
        d.rectangle([x, TY + 6, x + w, TY + 34], fill=(48, 48, 52) if j else (60, 60, 66)); d.text((x + 15, TY + 20), tb, font=f_uis, fill=(205, 205, 210), anchor="lm"); x += w + 6
    RX0 = 470; RY = TY + 48
    d.rectangle([RX0, RY, O, RY + 26], fill=(40, 40, 44))
    span = 6.0; t0 = lt - span * 0.55
    for s in range(int(t0) - 1, int(t0 + span) + 2):
        xx = RX0 + (s - t0) / span * (O - RX0)
        if RX0 <= xx <= O: d.line([xx, RY + 16, xx, RY + 26], fill=(150, 150, 155)); d.text((xx + 4, RY + 8), f"{s:02d}:00f", font=f_uis, fill=(170, 170, 175), anchor="lm")
    for r in range(9):
        y = RY + 34 + r * 30
        d.text((14, y + 12), f"{r + 1}", font=f_uis, fill=(150, 150, 155), anchor="lm")
        d.text((60, y + 12), ["Null 17", "Null 17", "Text 3D", "Camera 1", "Light 1", "World", "Words", "Glow", "Grain"][r], font=f_uis, fill=(200, 200, 205), anchor="lm")
        d.text((260, y + 12), "S3. Null 17" if r < 5 else "None", font=f_uis, fill=(170, 170, 175), anchor="lm")
        col = COLS[r % len(COLS)]
        bs = lt - 1.5 + (r % 4) * 0.7; be = bs + 2.5 + r % 3
        xa = RX0 + (bs - t0) / span * (O - RX0); xb = RX0 + (be - t0) / span * (O - RX0)
        d.rectangle([max(RX0, xa), y + 2, min(O, xb), y + 24], fill=col + (255,))
        for kf in range(4):
            kx = RX0 + (math.floor(t0) + kf * 1.5 + r * 0.2 - t0) / span * (O - RX0)
            if RX0 < kx < O: d.polygon([(kx, y + 6), (kx + 7, y + 13), (kx, y + 20), (kx - 7, y + 13)], fill=(240, 240, 245))
    px = RX0 + 0.55 * (O - RX0)
    d.line([px, RY, px, O], fill=(80, 150, 255), width=2); d.polygon([(px - 8, RY), (px + 8, RY), (px, RY + 12)], fill=(80, 150, 255))
    return img

# ---------- section B: wireframe fly-through (4.5 - 7 s) ----------
def flythrough(t):
    u = (t - 4.5) / 2.5
    fr = RD.at(1.75 + u * 3.0)
    w = wire(fr)
    z = 1.0 + 0.6 * u; ang = -12 + 24 * u
    w = w.rotate(ang, Image.BICUBIC, fillcolor=(10, 10, 12))
    cw = O / z; w = w.crop(((O - cw) / 2, (O - cw) / 2, (O + cw) / 2, (O + cw) / 2)).resize((O, O))
    d = ImageDraw.Draw(w, "RGBA")
    for i in range(30):
        a = i * 0.7 + t; x = O / 2 + 480 * math.sin(a) * math.cos(a * 0.3); y = O / 2 + 420 * math.cos(a * 1.2)
        d.rectangle([x - 6, y - 6, x + 6, y + 6], outline=(255, 200, 60, 230), width=2)
        d.line([O / 2, O / 2, x, y], fill=(160, 80, 220, 120), width=2)
    return w

def render(t):
    if t < 4.5: img = title_card(t)
    elif t < 7.0: img = flythrough(t)
    else: img = editor(t)
    a = np.asarray(img, np.float32)
    if 4.4 < t < 4.6 or 6.9 < t < 7.1: a = a + 120
    a = a * min(ease(t / 0.3), ease((DUR - t) / 0.8))
    return np.clip(a, 0, 255).astype(np.uint8)

if PREVIEW:
    ims = [Image.fromarray(render(tp)).resize((360, 360)) for tp in PREVIEW]
    st = Image.new("RGB", (360 * len(ims), 360))
    for j, im in enumerate(ims): st.paste(im, (360 * j, 0))
    st.save(OUT); sys.exit()

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{O}x{O}", "-r", str(FPS), "-i", "-",
    "-ss", str(SONG_START), "-t", str(DUR), "-i", SONG, "-map", "0:v", "-map", "1:a",
    "-af", f"afade=t=in:d=0.4,afade=t=out:st={DUR - 2}:d=2", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "10M", "-bufsize", "20M",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)):
    ff.stdin.write(render(i / FPS).tobytes())
    if i % 150 == 0: print(i, flush=True)
ff.stdin.close(); ff.wait(); print("done", ff.returncode)
