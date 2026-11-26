"""Part 2 v3: a real behind-the-scenes: the actual build log, each scene's real layers, and the real code.
usage: python3 bts_v3.py LYRICDIR SONG OUT [--preview t1,t2]
"""
import sys, os, math, subprocess, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_v3 as M

a = sys.argv[1:]; LDIR, SONG, OUT = a[0], a[1], a[2]
PREVIEW = [float(v) for v in a[a.index("--preview") + 1].split(",")] if "--preview" in a else None
O, FPS, DUR = 1080, 30, 30.0
SONG_START = 78.0 + 36.5
RN = M.Renderer(LDIR)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"; MONOB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
f_t = ImageFont.truetype(MONO, 30); f_c = ImageFont.truetype(MONO, 21); f_h = ImageFont.truetype(MONOB, 26); f_l = ImageFont.truetype(MONOB, 22)
def ease(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3

SRC = open(M.__file__, encoding="utf-8").read().split("\n")
def code_for(name):
    i = next(j for j, l in enumerate(SRC) if l.strip().startswith(f"# --- {name[:4]}"))
    k = next((j for j in range(i + 1, len(SRC)) if SRC[j].strip().startswith("# ---") or SRC[j].startswith("    return SC")), i + 20)
    return SRC[i:k]
LYR = list(range(1, 9))   # scenes with lyrics

# --- real layer thumbnails for each scene (computed once) ---
def thumbs(k):
    scn = RN.SC[k]; tm = scn.t0 + (scn.t1 - scn.t0) * 0.85; u = 0.85
    cx, cy, z, ang = scn.cam(u, tm)
    def cam(img): return RN.camera(img, cx, cy, z, ang).resize((260, 260), Image.BILINEAR)
    world = Image.fromarray(np.clip(scn.world, 0, 255).astype(np.uint8)).convert("RGBA")
    lit = Image.fromarray(np.clip(scn.dyn(scn.world, tm, u) if scn.dyn else scn.world, 0, 255).astype(np.uint8)).convert("RGBA")
    if scn.front is not None: lit.alpha_composite(scn.front)
    words = Image.new("RGBA", (M.WS, M.WS), (0, 0, 0, 0))
    if hasattr(scn, "disc"):
        layer = Image.new("RGBA", scn.disc.size, (0, 0, 0, 0)); M.words_on(scn, None, tm, target=layer); words.alpha_composite(layer, (100, 100))
    else: M.words_on(scn, words, tm)
    if scn.anim == "type":   # typewriter text is drawn in screen space
        w2 = Image.new("RGBA", (O, O), (0, 0, 0, 0)); RN.screen(w2, k, tm); wt = w2.resize((260, 260))
    else: wt = cam(words)
    chk = Image.fromarray((np.where(((np.mgrid[0:260, 0:260] // 20).sum(0) % 2)[..., None], 70, 50) * np.ones((1, 1, 3))).astype(np.uint8)).convert("RGBA")
    wl = chk.copy(); wl.alpha_composite(wt)
    final = Image.fromarray(RN.frame(tm)).resize((260, 260)).convert("RGBA")
    return [(cam(world), "1 world"), (cam(lit), "2 light + depth"), (wl, "3 words"), (final, "4 grade + film")]
THUMBS = {k: thumbs(k) for k in LYR}

def terminal(t, final=False):
    img = Image.new("RGB", (O, O), (14, 16, 18)); d = ImageDraw.Draw(img)
    lines = ["$ python3 make_v3.py lyric/ shudhu_tomake.mp4 part1.mp4"]
    n = 1095; prog = [f"{i}/{n}" for i in range(0, n, 150)] + ["done 0"]
    if final: shown = lines + prog
    else:
        typed = int(min(1, max(0, (t - 0.3) / 1.4)) * len(lines[0]))
        shown = [lines[0][:typed]] + (prog[:int(max(0, t - 1.9) * 4.5)] if typed == len(lines[0]) else [])
    for i, l in enumerate(shown):
        d.text((40, 90 + i * 44), l, font=f_t, fill=(120, 230, 140) if l.startswith("$") else (215, 215, 210))
    if int(t * 2.5) % 2 == 0:
        y = 90 + (len(shown) - 1) * 44; x = 40 + f_t.getlength(shown[-1]) + 6; d.rectangle([x, y + 4, x + 16, y + 34], fill=(215, 215, 210))
    d.text((40, 30), "behind the scenes", font=f_h, fill=(140, 140, 150))
    return img

def color_code(d, x, y, line):
    col = (205, 205, 200)
    if line.strip().startswith("#"): col = (120, 140, 120)
    d.text((x, y), line, font=f_c, fill=col)
    for m in re.finditer(r'"[^"]*"', line):
        d.text((x + f_c.getlength(line[:m.start()]), y), m.group(0), font=f_c, fill=(230, 190, 120))

def breakdown(t):
    seg = (t - 4.0) / 3.0; i = min(int(seg), 7); lt = seg - i; k = LYR[i]; scn = RN.SC[k]
    img = Image.new("RGB", (O, O), (24, 24, 27)); d = ImageDraw.Draw(img, "RGBA")
    d.text((30, 34), f"{scn.name}", font=f_h, fill=(230, 230, 235))
    d.text((O - 30, 34), f"{scn.t0:05.2f}s  ·  {scn.anim}  ·  exit: {scn.exit}", font=f_l, fill=(150, 150, 160), anchor="ra")
    spread = ease((lt - 0.1) / 0.7) * (1 - ease((lt - 2.55) / 0.4))
    th = THUMBS[k]
    for j, (im, lab) in enumerate(th):
        base_x, base_y = 410, 170
        x = base_x + (j - 1.5) * 240 * spread; y = base_y + (j - 1.5) * 60 * spread
        img.paste(im.convert("RGB"), (int(x), int(y)))
        d.rectangle([x, y, x + 260, y + 260], outline=(200, 200, 210, 160), width=2)
        if spread > 0.6: d.text((x + 6, y + 266), lab, font=f_l, fill=(220, 220, 225, int(255 * (spread - 0.6) / 0.4)))
    # code panel
    d.rectangle([0, 600, O, O], fill=(17, 18, 20)); d.line([0, 600, O, 600], fill=(60, 60, 66), width=2)
    d.text((24, 616), "make_v3.py", font=f_l, fill=(150, 170, 220))
    code = code_for(scn.name); scroll = max(0, lt - 0.6) * 3.2
    for n_, line in enumerate(code):
        y = 656 + (n_ - scroll) * 29
        if 650 <= y <= O - 30:
            d.text((24, y), f"{n_ + 1:3d}", font=f_c, fill=(90, 90, 100)); color_code(d, 76, y, line[:78])
    return img

def frame(t):
    if t < 4.0: img = terminal(t)
    elif t < 28.0: img = breakdown(t)
    else:
        img = terminal(t, final=True); d = ImageDraw.Draw(img)
        d.text((O / 2, 860), "edit by Morsalin", font=f_h, fill=(230, 220, 200), anchor="mm")
    a_ = np.asarray(img, np.float32)
    a_ = a_ * min(ease(t / 0.3), ease((DUR - t) / 0.9))
    return np.clip(a_ + np.random.default_rng(int(t * 30)).normal(0, 3, (1, 1, 1)), 0, 255).astype(np.uint8)

if PREVIEW:
    ims = [Image.fromarray(frame(tp)).resize((360, 360)) for tp in PREVIEW]
    st = Image.new("RGB", (360 * len(ims), 360))
    for j, im in enumerate(ims): st.paste(im, (360 * j, 0))
    st.save(OUT); sys.exit()
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{O}x{O}", "-r", str(FPS), "-i", "-",
    "-ss", str(SONG_START), "-t", str(DUR), "-i", SONG, "-map", "0:v", "-map", "1:a", "-af", f"afade=t=in:d=0.4,afade=t=out:st={DUR - 2}:d=2",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT],
    stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)):
    ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print("done", ff.returncode)
