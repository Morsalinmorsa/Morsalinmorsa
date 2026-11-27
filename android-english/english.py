# Replace the Chinese on-screen text with English (intro word cloud + 3 phone widgets)
import cv2, numpy as np, json, sys, os
from PIL import Image, ImageDraw, ImageFont
FR, TRACK, OUT, FONT = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)
N = len([f for f in os.listdir(FR) if f.endswith('.png')])
def font(sz): return ImageFont.truetype(FONT, max(6, int(round(sz))))

def text_img(txt, size, col, maxw=None, stroke=0):
    f = font(size)
    while maxw and f.getbbox(txt)[2] > maxw and size > 8:
        size *= 0.95; f = font(size)
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    im = Image.new('RGBA', (r - l + 4, b - t + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - l, 2 - t), txt, font=f, fill=tuple(int(c) for c in col) + (255,),
                            stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    return np.array(im).astype(np.float32), size

def paste(frame, timg, x, y, alpha=1.0):
    """frame BGR uint8; timg RGBA float; x,y top-left"""
    h, w = timg.shape[:2]; H, W = frame.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    t = timg[y0 - y:y1 - y, x0 - x:x1 - x]
    a = t[..., 3:4] / 255.0 * alpha
    reg = frame[y0:y1, x0:x1].astype(np.float32)
    frame[y0:y1, x0:x1] = (reg * (1 - a) + t[..., 2::-1] * a).clip(0, 255).astype(np.uint8)

# ---------------- intro (frames 1..130) ----------------
WORDS = [  # name, english, y0,y1, x0,x1, anchor
    ('kafei',   'Super laggy, bro', 222, 308,   0, 420, 'R'),
    ('ruanjian','Bad app support',  335, 415,   0, 420, 'R'),
    ('meiyou',  'No innovation',    425, 505,   0, 420, 'R'),
    ('donghua', 'Laggy animations', 238, 318, 530, 960, 'L'),
    ('youhua',  'Bad optimization', 350, 422, 540, 960, 'L'),
    ('tiaojiao','Trash tuning',     425, 530, 540, 960, 'L'),
]
TITLE = 'How people see Android'
K = 151
def analyse(img):
    m = img.max(2).astype(np.uint8)
    b = (m > 45).astype(np.uint8)
    lines = cv2.morphologyEx(b, cv2.MORPH_OPEN, np.ones((1, K), np.uint8)) | \
            cv2.morphologyEx(b, cv2.MORPH_OPEN, np.ones((K, 1), np.uint8))
    lines = cv2.dilate(lines, np.ones((3, 3), np.uint8))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    green = ((hsv[..., 0] > 55) & (hsv[..., 0] < 85) & (hsv[..., 1] > 120) & (hsv[..., 2] > 50)).astype(np.uint8)
    g2 = cv2.dilate(green, np.ones((3, 3), np.uint8))
    n_, lab, st, _ = cv2.connectedComponentsWithStats(g2)
    cxs = st[:, cv2.CC_STAT_LEFT] + st[:, cv2.CC_STAT_WIDTH] / 2
    keep = (st[:, cv2.CC_STAT_AREA] > 800) & (cxs > 280) & (cxs < 680); keep[0] = False
    body = keep[lab].astype(np.uint8)
    inv = (1 - body).copy(); h_, w_ = inv.shape
    ff = np.zeros((h_ + 2, w_ + 2), np.uint8)
    for sx in range(0, w_, 40):
        for sy in (0, h_ - 1):
            if inv[sy, sx]: cv2.floodFill(inv, ff, (sx, sy), 2)
    robot = ((body == 1) | (inv == 1)).astype(np.uint8)   # holes (eyes, mouth) inside the robot count as robot
    text = (b == 1) & (lines == 0) & (robot == 0)
    return text, lines, robot, hsv

def bbox(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) < 60: return None
    # trim outliers
    x0, x1 = np.percentile(xs, [0.5, 99.5]); y0, y1 = np.percentile(ys, [1, 99])
    return x0, y0, x1, y1, len(xs)

def rebuild_bg(img, fill_mask, robot):
    """black + straight grid lines through the masked area"""
    valid = (fill_mask == 0) & (robot == 0)
    f = img.astype(np.float32).copy()
    big = np.where(valid[..., None], f, np.nan)
    with np.errstate(all='ignore'):
        rowp = np.nan_to_num(np.nanmedian(big, axis=1))   # H x 3
        colp = np.nan_to_num(np.nanmedian(big, axis=0))   # W x 3
    bg = np.maximum(rowp[:, None, :], colp[None, :, :])
    out = img.copy()
    out[fill_mask > 0] = bg[fill_mask > 0].clip(0, 255).astype(np.uint8)
    return out

# reference pass: final layout / colours (frame 100)
REF = {}
for name, en, y0, y1, x0, x1, anc in WORDS:
    ref = cv2.imread(FR + '/0119.png'); rt, _, rrob, _ = analyse(ref)
    m = np.zeros_like(rt); m[y0:y1, x0:x1] = rt[y0:y1, x0:x1]
    bb = bbox(m); px = ref[m]
    col = np.median(px[px.max(1) > np.percentile(px.max(1), 60)], 0)[::-1]
    REF[name] = (bb, col)
m = np.zeros_like(rt); m[95:185, 250:700] = rt[95:185, 250:700]
tb = bbox(m); px = ref[m]
REF['title'] = (tb, np.median(px[px.max(1) > np.percentile(px.max(1), 60)], 0)[::-1])
robot_ref = cv2.imread(FR + '/0110.png')[260:420, 400:560].astype(np.float32).mean()
print('ref', {k: (tuple(int(v) for v in b[0][:4]), tuple(int(c) for c in b[1])) for k, b in REF.items()}, flush=True)

def intro(n, img):
    text, lines, robot, hsv = analyse(img)
    fade = min(1.0, img[260:420, 400:560].astype(np.float32).mean() / robot_ref) if n > 110 else 1.0
    fill = np.zeros(text.shape, np.uint8); draws = []
    # title
    if n <= 12:
        lowsat = hsv[..., 1] < 60
        tm = text & lowsat; tm[:60] = False; tm[560:] = False
    else:
        tm = np.zeros_like(text); tm[95:185, 250:700] = text[95:185, 250:700]
    bb = bbox(tm)
    if bb:
        fill |= tm.astype(np.uint8)
        x0, y0, x1, y1, _ = bb
        rb = REF['title'][0]
        sc = (480 - x0) / (480 - rb[0]) if n <= 12 else (y1 - y0) / (rb[3] - rb[1])
        sc = float(np.clip(sc, 0.7, 2.0)) if n <= 12 else 1.0
        cy = (y0 + y1) / 2
        draws.append((TITLE, 40 * sc, REF['title'][1], 'C', 480, cy, 700 * sc, 0))
    if n > 12:
        for name, en, y0, y1, x0, x1, anc in WORDS:
            m = np.zeros_like(text); m[y0:y1, x0:x1] = text[y0:y1, x0:x1]
            bb = bbox(m)
            if not bb: continue
            fill |= m.astype(np.uint8)
            rb = REF[name][0]; h = rb[3] - rb[1]
            cy = (bb[1] + bb[3]) / 2
            if anc == 'R':
                draws.append((en, h * 0.80, REF[name][1], 'R', bb[2], cy, 345, 0))
            else:
                draws.append((en, h * 0.80, REF[name][1], 'L', bb[0], cy, 330, rb[0]))
    if not draws: return img
    fill = cv2.dilate(fill, np.ones((9, 9), np.uint8))
    fill[robot > 0] = 0
    out = rebuild_bg(img, fill, robot)
    for en, size, col, anc, ax, cy, maxw, fx in draws:
        t, _ = text_img(en, size, np.array(col) * fade, maxw, stroke=max(2, int(size / 14)))
        h, w = t.shape[:2]
        x = ax - w / 2 if anc == 'C' else (ax - w if anc == 'R' else ax - max(0, fx + w - 950))
        paste(out, t, x, cy - h / 2)
    # robot stays in front of the title
    out[robot > 0] = img[robot > 0]
    return out

# ---------------- widgets ----------------
TR = json.load(open(TRACK))
WIDGETS = {
  'ios':   (170, (245, 65), [
      ('Smooth  ·  Easy  ·  Innovative', (378, 120, 604, 149), 'L', 1.55, False),
      ('No lag for 3 years',             (378, 151, 498, 180), 'L', 1.9, False)]),
  'color': (285, (250, 45), [
      ('Your Dove is ready', (356, 51, 551, 86), 'L', 1.0, False),
      ('View details',       (376, 88, 444, 108), 'L', 1.8, False),
      ('OK',                 (600, 58, 660, 82), 'C', 1.0, True),
      ('Silky smooth',       (353, 135, 522, 181), 'L', 1.5, False)]),
  'mi':    (445, (200, 500), [
      ('System not responding', (386, 525, 546, 563), 'C', 2.2, False),
      ('Wait',                  (300, 643, 366, 679), 'C', 1.2, True),
      ('OK',                    (560, 643, 632, 679), 'C', 1.2, True)]),
}
WCOL = {'ios': [(175, 175, 175), (175, 175, 175)],
        'color': [(242, 242, 242), (150, 150, 150), (45, 45, 45), (248, 248, 248)],
        'mi': [(25, 25, 25), (70, 70, 70), (255, 255, 255)]}
for k, (refn, _, items) in []:
    im = cv2.imread(FR + '/%04d.png' % refn)
    cols = []
    for txt, (x0, y0, x1, y1), *_ in items:
        reg = im[y0:y1, x0:x1].reshape(-1, 3).astype(np.float32)
        bgc = np.median(reg, 0); d = np.abs(reg - bgc).sum(1)
        cols.append(np.median(reg[d > np.percentile(d, 85)], 0)[::-1])
    WCOL[k] = cols
SEG = {}
for k, res in TR.items():
    prev = None
    for n in sorted(res, key=int):
        sc, x, y, s = res[n]
        if sc < 0.55: continue
        if k == 'mi' and not 443 <= int(n) <= 450: continue
        if k == 'ios' and not 145 <= int(n) <= 191: continue
        if k == 'color' and not 259 <= int(n) <= 292: continue
        if prev and abs(x - prev[0]) + abs(y - prev[1]) > 200: continue
        prev = (x, y); SEG[int(n)] = (k, x, y, s)

# Xiaomi dialog sliding up from the bottom: track just its title line
_g = lambda n: cv2.cvtColor(cv2.imread(FR + '/%04d.png' % n), cv2.COLOR_BGR2GRAY)
_T = _g(445)[515:575, 330:600]
_s = SEG[444][3] if 444 in SEG else 1.0
for n in range(432, 444):
    if n in SEG: continue
    im = _g(n); t = cv2.resize(_T, None, fx=_s, fy=_s)
    r = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED); _, mv, _, ml = cv2.minMaxLoc(r)
    print('mi-title', n, round(mv, 2), ml, flush=True)
    if mv > 0.6:
        SEG[n] = ('mi', ml[0] - (330 - 200) * _s, ml[1] - (515 - 500) * _s, _s, 30)

def widget(n, img):
    k, mx, my, s = SEG[n][:4]; pad = SEG[n][4] if len(SEG[n]) > 4 else 0
    refn, (ox, oy), items = WIDGETS[k]
    out = img.copy()
    rects = []
    for txt, (x0, y0, x1, y1), *_ in items:
        X0 = mx + (x0 - ox) * s; Y0 = my + (y0 - oy) * s
        X1 = mx + (x1 - ox) * s; Y1 = my + (y1 - oy) * s
        rects.append((X0, Y0 - pad, X1, Y1 + pad))
    mask = np.zeros(img.shape[:2], np.uint8)
    for X0, Y0, X1, Y1 in rects:
        cv2.rectangle(mask, (int(X0), int(Y0)), (int(np.ceil(X1)), int(np.ceil(Y1))), 255, -1)
    solid = out.copy()
    for (X0, Y0, X1, Y1), it in zip(rects, items):
        a0, b0, a1, b1 = int(X0), int(Y0), int(np.ceil(X1)), int(np.ceil(Y1))
        H, W = out.shape[:2]
        ring = np.concatenate([out[max(0, b0 - 2):max(0, b0), max(0, a0):min(W, a1)].reshape(-1, 3),
                               out[min(H, b1):min(H, b1 + 2), max(0, a0):min(W, a1)].reshape(-1, 3),
                               out[max(0, b0):min(H, b1), max(0, a0 - 2):max(0, a0)].reshape(-1, 3)])
        if len(ring) == 0: continue
        top = np.median(out[max(0, b0 - 2):max(1, b0), max(0, a0):min(W, a1)].reshape(-1, 3), 0) if b0 > 1 else np.median(ring, 0)
        bot = np.median(out[min(H - 1, b1):min(H, b1 + 2), max(0, a0):min(W, a1)].reshape(-1, 3), 0) if b1 < H - 1 else top
        for yy in range(max(0, b0), min(H, b1)):
            f = (yy - b0) / max(1, b1 - b0)
            solid[yy, max(0, a0):min(W, a1)] = top * (1 - f) + bot * f    # vertical gradient like the box
        if it[4] and pad == 0:   # buttons: flat colour from the button itself (left/right edges)
            side = np.concatenate([out[max(0, b0 + 4):min(H, b1 - 4), max(0, a0 - 3):max(0, a0)].reshape(-1, 3),
                                   out[max(0, b0 + 4):min(H, b1 - 4), min(W, a1):min(W, a1 + 3)].reshape(-1, 3)])
            if len(side): solid[max(0, b0):min(H, b1), max(0, a0):min(W, a1)] = np.median(side, 0)
    mm = cv2.GaussianBlur(mask, (0, 0), 1.2)[..., None] / 255.0
    out = (out * (1 - mm) + solid * mm).astype(np.uint8)
    for (txt, _, anc, wmul, _b), (X0, Y0, X1, Y1), col in zip(items, rects, WCOL[k]):
        h = Y1 - Y0; w = X1 - X0
        t, _ = text_img(txt, h * 0.82, col, w * wmul)
        th, tw = t.shape[:2]
        x = X0 if anc == 'L' else (X0 + X1) / 2 - tw / 2
        paste(out, t, x, (Y0 + Y1) / 2 - th / 2)
    return out

for n in range(1, N + 1):
    img = cv2.imread(FR + '/%04d.png' % n)
    if n <= 132: img = intro(n, img)
    elif n in SEG: img = widget(n, img)
    cv2.imwrite(OUT + '/%04d.png' % n, img)
    if n % 50 == 0: print('frame', n, flush=True)
print('DONE')
