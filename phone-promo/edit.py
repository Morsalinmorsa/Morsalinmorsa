"""Promo edit for the Honor X9E Pro video (1080x1920): Bangla word captions, callouts, zooms, SFX.
usage: python3 edit.py WORKDIR SRC OUT [--preview t1,t2,...]
"""
import sys, os, math, subprocess, wave, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H, FPS = 1080, 1920, 30
args = sys.argv[1:]
wd, src, out = args[0], args[1], args[2]
preview = [float(v) for v in args[args.index("--preview") + 1].split(",")] if "--preview" in args else None

SW, SH = 960, 1920
FONTS = "/tmp/claude-0/-home-user-Morsalinmorsa/256700c8-01bb-53a3-ac0b-4bdd57d2caa1/scratchpad/lyric/fonts"
GF = "/tmp/claude-0/-home-user-Morsalinmorsa/256700c8-01bb-53a3-ac0b-4bdd57d2caa1/scratchpad/ff/fonts"
RAQM = ImageFont.Layout.RAQM
f_cap = ImageFont.truetype(f"{FONTS}/HindSiliguri-Bold.ttf", 74, layout_engine=RAQM)
f_call = ImageFont.truetype(f"{FONTS}/HindSiliguri-Bold.ttf", 52, layout_engine=RAQM)
f_big = ImageFont.truetype(f"{GF}/Anton.ttf", 150)
f_price = ImageFont.truetype(f"{GF}/Anton.ttf", 170)
f_lbl = ImageFont.truetype(f"{GF}/Bebas.ttf", 62)
f_emo = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)

def ease(t):
    t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3
def back(t):
    t = min(max(t, 0.0), 1.0); c = 1.7; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

# ---------------- transcript -> timed words ----------------
SENT = [
    "থাকেন।",
    "বিশেষ করে যারা ওমানে আপনারা থাকেন।",
    "ওমানের যেকোনো জায়গাতে আপনারা Official Original Phone আপনাদের বাসায় চলে যাবে।",
    "শুধু Mobile Number এবং Location দিলেই হবে, আর কিছু করতে হবে না।",
    "আপনাদের কাছে যাওয়ার পর, দেখার পর সবকিছু ঠিক থাকার পরে কিন্তু আপনারা মোবাইলের টাকা দিবেন।",
    "তো এইটার সম্বন্ধে বলার পরে আমি আরেকটা Vivo-র একটা মোবাইল আসছে, এটা আমি দেখাইতেছি।",
    "Honor X9E Pro।",
    "আসলে যারা মোবাইল কিনবেন চিন্তা করতেছেন, আপনারা এই মোবাইলটা নিশ্চিন্তে কিনতে পারেন।",
    "এটা ওমানি রিয়াল।",
    "যারা আমার কাছ থেকে অনলাইনে নিতে চান, তাদের জন্য বাসা পর্যন্ত একদম বাসার মধ্যে ১৫৫ রিয়াল।",
    "এইটার সাথে পাবেন একটা দামি Bluetooth, এটাও Honor Company-র",
]
HOT = {"Official", "Original", "Phone", "Mobile", "Number", "Location", "টাকা", "Honor", "X9E", "Pro", "১৫৫", "রিয়াল",
       "Bluetooth", "ওমানে", "ওমানের", "বাসায়", "নিশ্চিন্তে", "দামি"}
speech = [tuple(v) for v in np.load(os.path.join(wd, "speech.npy"))]
# map a position on the "speech-only" clock to real time
cum = np.cumsum([0] + [b - a for a, b in speech]); TOT = cum[-1]
def sp2real(p):
    p = min(max(p, 0), TOT - 1e-6)
    k = int(np.searchsorted(cum, p, side="right") - 1)
    return speech[k][0] + (p - cum[k])
def wweight(w_):
    w_ = re.sub(r"[।,]", "", w_)
    if re.search(r"[A-Za-z0-9]", w_): return max(2.0, len(w_) * 0.55)   # latin: ~syllables
    return max(1.5, len(re.sub(r"[া-্ৗ]", "", w_)) * 0.9)  # bangla: count letters, not vowel signs
words = [(si, w_) for si, s in enumerate(SENT) for w_ in s.split()]
sw = np.array([sum(wweight(w_) for w_ in s.split()) for s in SENT])
segd = np.array([b - a for a, b in speech]); NS, NG = len(SENT), len(speech)
rate = segd.sum() / sw.sum()
# DP: sentence k covers segments [b_k, b_{k+1}); sentences may also share a segment (split inside it)
INF = 1e18
cost = np.full((NS + 1, NG + 1), INF); arg = np.zeros((NS + 1, NG + 1), int); cost[0][0] = 0
for k in range(1, NS + 1):
    for j in range(1, NG + 1):
        for i in range(0, j):
            if cost[k - 1][i] >= INF: continue
            d = segd[i:j].sum(); e = rate * sw[k - 1]
            c = cost[k - 1][i] + (d - e) ** 2 / e
            if c < cost[k][j]: cost[k][j] = c; arg[k][j] = i
bounds = [NG]; j = NG
for k in range(NS, 0, -1):
    j = arg[k][j]; bounds.append(j)
bounds = bounds[::-1]
timed = []
for k in range(NS):
    segs = speech[bounds[k]:bounds[k + 1]]
    c2 = np.cumsum([0] + [b - a for a, b in segs]); T = c2[-1]
    def m2(p):
        p = min(max(p, 0), T - 1e-6); q = int(np.searchsorted(c2, p, side="right") - 1); return segs[q][0] + (p - c2[q])
    ws_ = SENT[k].split(); wt = np.array([wweight(w_) for w_ in ws_]); ps = np.concatenate([[0], np.cumsum(wt)]) / wt.sum() * T
    for q, w_ in enumerate(ws_): timed.append([k, w_, m2(ps[q]), m2(ps[q + 1] - 0.02)])
first = {}
for i, (si, *_r) in enumerate(timed): first.setdefault(si, i)
# caption chunks: max 3 words / ~22 chars, never across sentences, break after commas
chunks, cur = [], []
for w in timed:
    if cur and (w[0] != cur[-1][0] or len(cur) >= 3 or sum(len(x[1]) for x in cur) + len(w[1]) > 22 or cur[-1][1].endswith(",")):
        chunks.append(cur); cur = []
    cur.append(w)
chunks.append(cur)
STIME = {si: timed[i][2] for si, i in first.items()}
with open(os.path.join(wd, "timing.txt"), "w", encoding="utf-8") as fh:
    for c in chunks: fh.write(f"{c[0][2]:6.2f}-{c[-1][3]:6.2f}  {' '.join(x[1] for x in c)}\n")

# ---------------- callouts ----------------
def emoji(ch, size):
    im = Image.new("RGBA", (140, 130), (0, 0, 0, 0)); ImageDraw.Draw(im).text((0, 0), ch, font=f_emo, embedded_color=True)
    im = im.crop(im.getbbox()); return im.resize((int(im.width * size / im.height), size), Image.LANCZOS)
def pill(text, emo, bg=(255, 255, 255), fg=(20, 20, 30), font=f_call):
    e = emoji(emo, 64) if emo else None
    tw = font.getlength(text); w_ = int(tw + 80 + (e.width + 20 if e else 0)); h_ = 104
    im = Image.new("RGBA", (w_ + 30, h_ + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([15, 22, w_ + 15, h_ + 22], 52, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    d.rounded_rectangle([15, 15, w_ + 15, h_ + 15], 52, fill=bg + (255,))
    x = 55
    if e: im.alpha_composite(e, (x, 15 + (h_ - e.height) // 2)); x += e.width + 20
    d.text((x, 15 + h_ / 2), text, font=font, fill=fg, anchor="lm")
    return im
def product_card():
    im = Image.new("RGBA", (1000, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((500, 120), "HONOR X9E PRO", font=f_big, fill=(255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(90, 30, 140))
    d.rounded_rectangle([290, 230, 710, 310], 40, fill=(255, 200, 40))
    d.text((500, 270), "NEW ARRIVAL", font=f_lbl, fill=(30, 20, 40), anchor="mm")
    g = im.filter(ImageFilter.GaussianBlur(16)); out_ = Image.new("RGBA", im.size); out_.alpha_composite(g); out_.alpha_composite(im)
    return out_
def price_card():
    im = Image.new("RGBA", (900, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([60, 40, 840, 360], 60, fill=(255, 214, 40), outline=(255, 255, 255), width=8)
    d.text((450, 175), "155", font=f_price, fill=(30, 20, 40), anchor="mm")
    d.text((450, 300), "OMR  •  HOME DELIVERY", font=f_lbl, fill=(140, 20, 60), anchor="mm")
    e = emoji("💰", 120); im.alpha_composite(e, (20, 0))
    return im
WT = lambda w: next(x[2] for x in timed if x[1] == w)
CALL = [  # (start, end, image, y, kind)
    (STIME[2] + 0.3, STIME[3], pill("সারা ওমানে হোম ডেলিভারি", "🚚", (255, 255, 255)), 250, "pill"),
    (STIME[3] + 0.2, STIME[4], pill("Mobile Number + Location", "📍", (40, 200, 120), (255, 255, 255)), 250, "pill"),
    (STIME[4] + 0.6, STIME[5], pill("দেখে নিয়ে তারপর টাকা", "💵", (255, 214, 40)), 250, "pill"),
    (STIME[6], STIME[7] + 2.0, product_card(), 270, "product"),
    (WT("১৫৫") - 0.15, STIME[10] + 0.3, price_card(), 290, "price"),
    (WT("Bluetooth,") - 0.2, 60.0, pill("সাথে পাচ্ছেন Honor Bluetooth", "🎁", (255, 90, 140), (255, 255, 255)), 250, "pill"),
]
# zoom punches: sentence starts (small) and key callouts (big)
PUNCH = [(STIME[s], 0.06) for s in STIME if s > 0] + [(c[0], 0.12) for c in CALL if c[4] != "pill"]

# ---------------- video ----------------
N = int(round(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout) * FPS)); DUR = N / FPS
FSZ = SW * SH * 3
class Reader:
    def __init__(self): self.p = None; self.i = -1; self.cur = None
    def get(self, i):
        if preview:   # random access
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{i / FPS:.3f}", "-i", src, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            return np.frombuffer(r[:FSZ], np.uint8).reshape(SH, SW, 3)
        if self.p is None: self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        while self.i < i:
            buf = self.p.stdout.read(FSZ)
            if len(buf) < FSZ: break
            self.cur = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3); self.i += 1
        return self.cur
reader = Reader()
bbox = np.load(os.path.join(wd, "bbox.npy"))   # per-frame content box in 96x192 units

def base_frame(i, t):
    x0, x1, y0, y1 = bbox[min(i, len(bbox) - 1)]
    sx, sy = SW / 96, SH / 192
    if x0 > 1:   # source shrank the picture: crop the real content back out
        bx0, bx1, by0, by1 = (x0 + 0.6) * sx, (x1 + 0.4) * sx, (y0 + 0.6) * sy, (y1 + 0.4) * sy
    else:
        bx0, bx1, by0, by1 = 0, SW, 0, SH
    # fit to 1080x1920 by cropping (cover)
    bw, bh = bx1 - bx0, by1 - by0
    if bw / bh > W / H: nw = bh * W / H; bx0 += (bw - nw) / 2; bw = nw
    else: nh = bw * H / W; by0 += (bh - nh) * 0.4; bh = nh
    z = 1.0 + 0.03 * math.sin(t / 6) ** 2
    for pt, amt in PUNCH:
        if 0 <= t - pt < 1.2: z += amt * math.exp(-(t - pt) / 0.25)
    cw, ch = bw / z, bh / z
    cx0 = bx0 + (bw - cw) / 2; cy0 = by0 + (bh - ch) * 0.38
    img = Image.fromarray(reader.get(i)).crop((int(cx0), int(cy0), int(cx0 + cw), int(cy0 + ch))).resize((W, H), Image.BICUBIC)
    if x0 > 1: img = img.filter(ImageFilter.UnsharpMask(2, 80, 2))
    img = ImageEnhance.Contrast(img).enhance(1.06)
    return img

def caption_layer(ov, t):
    for c in chunks:
        if not (c[0][2] - 0.04 <= t < c[-1][3] + 0.08): continue
        gi = ease((t - c[0][2] + 0.04) / 0.12)
        ws = [x[1].rstrip("।,") for x in c]
        widths = [f_cap.getlength(w_) for w_ in ws]; sp = 36
        tot = sum(widths) + sp * (len(ws) - 1)
        x = (W - tot) / 2; y = 1430 + 20 * (1 - gi)
        d = ImageDraw.Draw(ov)
        bgw = tot + 70
        d.rounded_rectangle([(W - bgw) / 2, y - 62, (W + bgw) / 2, y + 62], 30, fill=(0, 0, 0, int(120 * gi)))
        for (si, w_, a, b), ww, wd_ in zip(c, ws, widths):
            on = a <= t
            hot = any(h in ww for h in HOT)
            pop = 1 + 0.10 * math.sin(math.pi * min(max((t - a) / 0.2, 0), 1)) if on else 1
            if on and t < b + 0.05: col = (255, 220, 40)
            elif hot: col = (120, 230, 255)
            else: col = (255, 255, 255)
            f_ = f_cap if pop == 1 else ImageFont.truetype(f"{FONTS}/HindSiliguri-Bold.ttf", int(74 * pop), layout_engine=RAQM)
            d.text((x + wd_ / 2, y), ww, font=f_, fill=col + (int(255 * gi),), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0, int(255 * gi)))
            x += wd_ + sp

def frame(t):
    i = min(int(t * FPS), N - 1)
    img = base_frame(i, t).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for (a, b, im, y, kind) in CALL:
        if not (a <= t < b + 0.3): continue
        pin = (t - a) / 0.35; pout = ease((t - b) / 0.3)
        sc = (0.4 + 0.6 * back(pin)) * (1 + 0.02 * math.sin(t * 6)) if kind != "pill" else 1.0
        al = ease(pin) * (1 - pout)
        if kind == "pill":
            xo = (1 - back(pin)) * -W * 0.8 + pout * W * 0.8
            imm = im
        else:
            xo = 0; imm = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
        if al < 1:
            imm = imm.copy(); imm.putalpha(imm.getchannel("A").point(lambda v: int(v * al)))
        ov.alpha_composite(imm, (int((W - imm.width) / 2 + xo), int(y - imm.height / 2)))
    caption_layer(ov, t)
    img.alpha_composite(ov)
    arr = np.asarray(img.convert("RGB"), np.float32)
    for pt, amt in PUNCH:
        if 0 <= t - pt < 0.3 and amt > 0.1: arr = arr + 90 * math.exp(-(t - pt) / 0.07)
    fa = min(ease(t / 0.25), ease((DUR - t) / 0.4))
    return np.clip(arr * fa, 0, 255).astype(np.uint8)

# ---------------- audio: voice + pop / whoosh SFX ----------------
def build_audio(path):
    sr = 44100
    a = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-af", "highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=10:release=150,loudnorm=I=-14:TP=-1.5",
                        "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    m = np.frombuffer(a, np.float32).reshape(-1, 2).copy()
    rng = np.random.default_rng(1)
    def whoosh():
        n = int(0.35 * sr); x = rng.normal(0, 1, n)
        k = np.linspace(0, 1, n); env = np.sin(np.pi * k) ** 2
        spec = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / sr)
        x = np.fft.irfft(spec * np.exp(-((f - 1800) / 1400) ** 2), n)
        return x / np.abs(x).max() * env * 0.16
    def pop():
        n = int(0.12 * sr); k = np.arange(n) / sr
        return np.sin(2 * np.pi * (900 - 3000 * k) * k) * np.exp(-k / 0.03) * 0.22
    for (a0, b0, im, y, kind) in CALL:
        s = whoosh() if kind == "pill" else np.concatenate([whoosh()[: int(0.2 * sr)], pop()])
        o = int(max(0, a0 - 0.05) * sr); n = min(len(s), len(m) - o)
        if n > 0: m[o:o + n] += s[:n, None]
    fade = int(0.4 * sr); m[-fade:] *= np.linspace(1, 0, fade)[:, None]
    m = m / max(1.0, np.abs(m).max() / 0.98)
    with wave.open(path, "wb") as w_:
        w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(sr); w_.writeframes((m * 32767).astype(np.int16).tobytes())

if preview:
    ims = [Image.fromarray(frame(tp)).resize((360, 640)) for tp in preview]
    strip = Image.new("RGB", (360 * len(ims), 640))
    for j, im in enumerate(ims): strip.paste(im, (360 * j, 0))
    strip.save(out); sys.exit()

ap = os.path.join(wd, "mix.wav"); build_audio(ap)
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", ap, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
for j in range(N):
    ff.stdin.write(frame(j / FPS).tobytes())
    if j % 300 == 0: print(f"{j}/{N}", flush=True)
ff.stdin.close(); ff.wait(); print("done", ff.returncode)
