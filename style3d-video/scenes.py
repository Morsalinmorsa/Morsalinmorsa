"""Real 3D scenes for Shudhu Tomake (Blender). Run:
blender -b --factory-startup -P scenes.py -- SCENE_INDEX OUTDIR [RES] [FRAME_LIST]
"""
import bpy, sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

argv = sys.argv[sys.argv.index("--") + 1:]
SCN = int(argv[0]); OUTD = argv[1]; RES = int(argv[2]) if len(argv) > 2 else 720
ONLY = [int(x) for x in argv[3].split(",")] if len(argv) > 3 else None
HERE = os.path.dirname(os.path.abspath(__file__))
LD = os.path.join(HERE, "..", "lyric")
FPS = 30; BEAT0, BEAT = 79.90 - 78.0, 0.4616
rnd = random.Random(7 + SCN); nrng = np.random.default_rng(7 + SCN)

# ---------------- lyric timing (beat-snapped) ----------------
LINES = []
for ln in open(os.path.join(LD, "lyrics.txt"), encoding="utf-8"):
    a, b, txt = ln.strip().split(" ", 2); a, b = float(a), float(b)
    ws = txt.split(); lens = np.array([len(w) + 1.5 for w in ws])
    st = a + 0.12 + np.concatenate([[0], np.cumsum(lens)[:-1]]) / lens.sum() * (b - a) * 0.66
    q = []
    for x in st:
        v = BEAT0 + round((x - BEAT0) / (BEAT / 2)) * (BEAT / 2); v = max(v, a + 0.05, (q[-1] + BEAT / 2) if q else 0); q.append(v)
    LINES.append(dict(s=a, e=b, words=ws, ws=q))
BOUNDS = [0.0] + [l["s"] for l in LINES] + [32.2]
T0, T1 = BOUNDS[SCN], BOUNDS[SCN + 1]
NF = int(round((T1 - T0) * FPS))
def F(t): return int(round((t - T0) * FPS)) + 1          # absolute clip time -> scene frame
L = LINES[SCN - 1] if 1 <= SCN <= 8 else None

# ---------------- setup ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x = sc.render.resolution_y = RES
sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = NF
ee = sc.eevee; ee.use_bloom = True; ee.bloom_intensity = 0.06; ee.bloom_threshold = 0.9
ee.use_gtao = True; ee.gtao_distance = 1.2; ee.use_soft_shadows = True; ee.shadow_cube_size = "1024"; ee.shadow_cascade_size = "2048"
ee.taa_render_samples = 24; ee.use_ssr = True
sc.view_settings.view_transform = "Filmic"; sc.view_settings.look = "Medium High Contrast"
sc.render.image_settings.file_format = "PNG"
world = bpy.data.worlds.new("W"); sc.world = world; world.use_nodes = True
def world_color(c, s=1.0):
    bg = world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (*c, 1); bg.inputs[1].default_value = s

# ---------------- pixel textures ----------------
def make_tex(name, palette, size=16, pattern=None):
    p = os.path.join(HERE, "tex", f"{name}.png")
    if not os.path.exists(p):
        r = np.random.default_rng(abs(hash(name)) % 1000)
        pal = np.array(palette, np.float32)
        img = pal[r.integers(0, len(pal), (size, size))] * r.uniform(0.9, 1.1, (size, size, 1))
        if pattern: img = pattern(img, r)
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(p)
    return p
def grass_side(img, r):
    img[:4] = np.array([(90, 160, 60)], np.float32) * r.uniform(0.85, 1.1, (4, img.shape[1], 1)); return img
def bricks(img, r):
    img[::4] *= 0.7; img[:, ::8] *= 0.75; return img
def windows(img, r):
    out = img.copy()
    for y in range(2, 16, 5):
        for x in range(2, 16, 5):
            if r.random() < 0.55: out[y:y + 3, x:x + 2] = (255, 214, 120) if r.random() < 0.8 else (150, 220, 255)
    return out

def mat_tex(name, tex, emit=0.0, rough=0.8, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(tex); t.interpolation = "Closest"
    nt.links.new(t.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit:
        nt.links.new(t.outputs[0], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    return m
def mat_col(name, col, emit=0.0, rough=0.5, metal=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit: b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

# ---------------- voxel mesh builder (exposed faces only, per-face UV, per-face material) ----------------
DIRS = [((0, 0, 1), "top"), ((0, 0, -1), "bot"), ((1, 0, 0), "side"), ((-1, 0, 0), "side"), ((0, 1, 0), "side"), ((0, -1, 0), "side")]
QUAD = {(0, 0, 1): [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], (0, 0, -1): [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)],
        (1, 0, 0): [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], (-1, 0, 0): [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)],
        (0, 1, 0): [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)], (0, -1, 0): [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]}
def voxel_obj(name, cells, size, mats, origin=(0, 0, 0)):
    """cells: dict (x,y,z)-> (top_mat, side_mat, bottom_mat) indices"""
    verts, vid, faces, fmat = [], {}, [], []
    for (x, y, z), m in cells.items():
        for d, kind in DIRS:
            if (x + d[0], y + d[1], z + d[2]) in cells: continue
            f = []
            for (a, b, c) in QUAD[d]:
                k = (x + a, y + b, z + c)
                if k not in vid: vid[k] = len(verts); verts.append(((k[0]) * size + origin[0], k[1] * size + origin[1], k[2] * size + origin[2]))
                f.append(vid[k])
            faces.append(f); fmat.append(m[0] if kind == "top" else m[2] if kind == "bot" else m[1])
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    uv = me.uv_layers.new()
    for poly in me.polygons:
        for li, (u, v) in zip(poly.loop_indices, [(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[li].uv = (u, v)
    for mat in mats: me.materials.append(mat)
    me.polygons.foreach_set("material_index", fmat)
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob

# ---------------- Bangla words -> 3D block letters ----------------
FONTS = os.path.join(LD, "fonts")
def word_obj(word, font, rows, height, depth_cells, mat, name="w"):
    f = ImageFont.truetype(os.path.join(FONTS, font), rows, layout_engine=ImageFont.Layout.RAQM)
    bb = f.getbbox(word); w, h = bb[2] - bb[0] + 4, bb[3] - bb[1] + 4
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((2 - bb[0], 2 - bb[1]), word, font=f, fill=255)
    a = np.asarray(m) > 110; H_, W_ = a.shape
    cell = height / H_
    cells = {}
    for r in range(H_):
        for c in range(W_):
            if a[r, c]:
                for d in range(depth_cells): cells[(c, d, H_ - 1 - r)] = (0, 0, 0)
    ob = voxel_obj(name, cells, cell, [mat], origin=(-W_ * cell / 2, 0, -H_ * cell / 2))
    ob["w"] = W_ * cell
    return ob

# ---------------- helpers ----------------
def key(ob, f, loc=None, rot=None, scale=None):
    if loc is not None: ob.location = loc; ob.keyframe_insert("location", frame=f)
    if rot is not None: ob.rotation_euler = rot; ob.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: ob.scale = scale; ob.keyframe_insert("scale", frame=f)
def interp(ob, kind="BEZIER"):
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = kind
def camera(loc0, loc1, target, lens=35, shake=0.02, dof=None):
    cd = bpy.data.cameras.new("C"); cd.lens = lens; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
    tg = bpy.data.objects.new("T", None); sc.collection.objects.link(tg); tg.location = target
    con = cam.constraints.new("TRACK_TO"); con.target = tg; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    key(cam, 1, loc=loc0); key(cam, NF, loc=loc1)
    for fc in cam.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = "SINE"; kp.easing = "EASE_IN_OUT"
        n = fc.modifiers.new("NOISE"); n.scale = 14 + 6 * fc.array_index; n.strength = shake; n.phase = rnd.uniform(0, 50)
    if dof:
        cd.dof.use_dof = True; cd.dof.focus_object = dof[0]; cd.dof.aperture_fstop = dof[1]
    return cam, tg
def light(kind, loc, energy, col=(1, 1, 1), rot=(0, 0, 0), size=0.5, spot=None):
    ld = bpy.data.lights.new("L", kind); ld.energy = energy; ld.color = col
    if kind in ("POINT", "SPOT", "AREA"): ld.shadow_soft_size = size
    if kind == "SPOT" and spot: ld.spot_size = spot
    ob = bpy.data.objects.new("L", ld); sc.collection.objects.link(ob); ob.location = loc; ob.rotation_euler = rot
    return ob
def look_rot(src, dst):
    import mathutils
    return (mathutils.Vector(dst) - mathutils.Vector(src)).to_track_quat("-Z", "Y").to_euler()
def terrain(nx, ny, base, amp, mats, scale=1.0, origin=(0, 0, 0), freq=0.18, seed=0):
    cells = {}
    r = np.random.default_rng(seed); ph = r.uniform(0, 6, 4)
    for x in range(nx):
        for y in range(ny):
            h = int(base + amp * (math.sin(x * freq + ph[0]) * math.cos(y * freq * 0.8 + ph[1]) + 0.5 * math.sin((x + y) * freq * 1.7 + ph[2])))
            for z in range(max(1, h)):
                cells[(x, y, z)] = (0, 1, 1) if z == max(1, h) - 1 else (1, 1, 1)
    return voxel_obj("terrain", cells, scale, mats, origin=origin)
def place_words(specs):
    """specs: list of (word, font, rows, height, depth, mat, loc, rot_z_deg)"""
    obs = []
    for i, (wd, fnt, rows, hgt, dep, mt, loc, rz) in enumerate(specs):
        o = word_obj(wd, fnt, rows, hgt, dep, mt, f"word{i}"); o.location = loc; o.rotation_euler = (0, 0, math.radians(rz)); obs.append(o)
    return obs

# ---------------- word animators (keyframes on the sung beat) ----------------
def anim_rise(ob, t, dz=1.2):
    f = F(t); loc = tuple(ob.location); rot = tuple(ob.rotation_euler)
    key(ob, max(1, f - 12), loc=(loc[0], loc[1], loc[2] - dz), rot=(rot[0] - 0.5, rot[1], rot[2] + 0.2), scale=(0.001, 0.001, 0.001))
    key(ob, f - 1, scale=(1, 1, 1)); key(ob, f + 6, loc=loc, rot=rot)
def anim_drop(ob, t, h=6):
    f = F(t); loc = tuple(ob.location)
    key(ob, max(1, f - 9), loc=(loc[0], loc[1], loc[2] + h)); key(ob, f, loc=loc, scale=(1, 1, 1))
    key(ob, f + 2, scale=(1.12, 1.12, 0.82)); key(ob, f + 5, loc=(loc[0], loc[1], loc[2] + 0.25), scale=(0.96, 0.96, 1.06)); key(ob, f + 9, loc=loc, scale=(1, 1, 1))
    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=1); ob.hide_render = False; ob.keyframe_insert("hide_render", frame=max(2, f - 9))
def anim_slide(ob, t, dx=-6):
    f = F(t); loc = tuple(ob.location)
    key(ob, max(1, f - 10), loc=(loc[0] + dx, loc[1], loc[2])); key(ob, f + 4, loc=loc)
def anim_show(ob, t):
    f = F(t); ob.hide_render = True; ob.keyframe_insert("hide_render", frame=1); ob.hide_render = False; ob.keyframe_insert("hide_render", frame=max(2, f))
def anim_flicker(mat, ob, t, strength):
    f = F(t); b = mat.node_tree.nodes["Principled BSDF"]; inp = b.inputs["Emission Strength"]
    anim_show(ob, t - 0.05)
    seq = [1, 0, 1, 1, 0, 0, 1, 0.3, 1, 1]
    for i, v in enumerate(seq):
        inp.default_value = strength * v; inp.keyframe_insert("default_value", frame=f + i - 1)
    fc = mat.node_tree.animation_data.action.fcurves
    for c in fc:
        for kp in c.keyframe_points: kp.interpolation = "CONSTANT"

# ---------------- textures / materials ----------------
TX = dict(
    grass=make_tex("grass", [(95, 160, 60), (80, 140, 50), (110, 175, 70)]),
    dirt=make_tex("dirt", [(120, 84, 52), (100, 70, 44), (134, 96, 60)]),
    dirt_side=make_tex("dirt_side", [(120, 84, 52), (100, 70, 44), (134, 96, 60)], pattern=grass_side),
    stone=make_tex("stone", [(128, 128, 128), (110, 110, 112), (140, 140, 142)], pattern=bricks),
    red=make_tex("red", [(200, 25, 40), (180, 20, 35), (225, 45, 60)]),
    gold=make_tex("gold", [(250, 205, 70), (235, 180, 40), (255, 230, 120)]),
    build=make_tex("build", [(30, 28, 44), (36, 32, 52), (26, 24, 38)], pattern=windows),
    lantern=make_tex("lantern", [(255, 190, 60), (255, 160, 40), (250, 215, 100)]),
    plank=make_tex("plank", [(110, 74, 44), (96, 64, 38), (122, 84, 50)], pattern=lambda i, r: (i.__setitem__((slice(None, None, 4)), i[::4] * 0.7) or i)),
)

# ====================================================================================
if SCN == 0:   # intro: title in block letters, a work light flickers on
    world_color((0.0, 0.0, 0.0), 0)
    m = mat_col("title", (1.0, 0.85, 0.55), rough=0.4)
    t1 = word_obj("SHUDHU TOMAKE", "Poppins-SemiBold.ttf", 30, 0.72, 3, m, "title"); t1.location = (0, 0, 0.4)
    m2 = mat_col("sub", (0.9, 0.9, 0.95), rough=0.5)
    t2 = word_obj("FRANKLIN", "Poppins-SemiBold.ttf", 22, 0.42, 2, m2, "sub"); t2.location = (0, 0, -0.55)
    fl = bpy.data.objects.new("floor", bpy.data.meshes.new("f")); sc.collection.objects.link(fl)
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -1.2)); bpy.context.object.data.materials.append(mat_col("fl", (0.05, 0.05, 0.06), rough=0.25))
    lt = light("SPOT", (0, -7, 4), 1600, (1, 0.9, 0.75), look_rot((0, -7, 4), (0, 0, 0)), 0.3, math.radians(95))
    for i, v in enumerate([0, 1, 0, 0, 1, 1, 0, 1, 1, 1]):
        lt.data.energy = 1600 * v; lt.data.keyframe_insert("energy", frame=1 + i * 3)
    for c in lt.data.animation_data.action.fcurves:
        for kp in c.keyframe_points: kp.interpolation = "CONSTANT"
    camera((0.4, -14.0, 1.0), (0, -11.5, 0.5), (0, 0, 0), lens=40, shake=0.015)

elif SCN == 1:   # lantern night
    world_color((0.008, 0.01, 0.04), 1)
    mats = [mat_tex("grass", TX["grass"]), mat_tex("dirt_side", TX["dirt_side"])]
    terrain(34, 34, 2, 1.3, mats, 1.0, origin=(-17, -6, -3), seed=1)
    lan = voxel_obj("lantern", {(0, 0, 0): (0, 0, 0)}, 0.9, [mat_tex("lan", TX["lantern"], emit=6)], origin=(-0.45, 3, -0.2))
    light("POINT", (0, 3.4, 0.5), 700, (1, 0.55, 0.2), size=0.6)
    light("SUN", (0, 0, 10), 0.25, (0.5, 0.6, 1.0), rot=(0.7, 0.2, 0.5))
    for i in range(70):
        s_ = voxel_obj(f"star{i}", {(0, 0, 0): (0, 0, 0)}, 0.08, [mat_col(f"st{i}", (1, 1, 1), emit=rnd.uniform(3, 12))],
                       origin=(rnd.uniform(-30, 30), rnd.uniform(25, 40), rnd.uniform(4, 18)))
    cream = mat_col("cream", (1.0, 0.86, 0.6), rough=0.35); glow = mat_col("glow", (1.0, 0.7, 0.3), emit=3.5)
    w = L["words"]
    ws = place_words([(w[0], "HindSiliguri-Bold.ttf", 80, 0.75, 4, cream, (-1.7, 1.5, 2.3), 8),
                      (w[1], "HindSiliguri-Bold.ttf", 80, 0.95, 5, cream, (1.4, 2.2, 2.0), -6),
                      (w[2], "HindSiliguri-Bold.ttf", 90, 1.5, 6, glow, (0.1, 1.2, 0.9), 3)])
    for o, t in zip(ws, L["ws"]): anim_rise(o, t)
    camera((-3.5, -8.5, 2.6), (-0.6, -4.2, 1.6), (0, 2, 1.2), lens=32, shake=0.03)

elif SCN == 2:   # stone wall: block words cast real shadows from a moving spotlight
    world_color((0.01, 0.01, 0.012), 1)
    cells = {(x, 0, z): (0, 0, 0) for x in range(-14, 15) for z in range(-6, 12)}
    voxel_obj("wall", cells, 0.6, [mat_tex("stone", TX["stone"])], origin=(0, 4.0, 0))
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -3.6)); bpy.context.object.data.materials.append(mat_tex("fl", TX["stone"]))
    dark = mat_col("dark", (0.85, 0.8, 0.7), rough=0.55)
    w = L["words"]
    ws = place_words([(w[0], "HindSiliguri-Bold.ttf", 80, 0.9, 4, dark, (-1.3, 1.2, 1.3), 4),
                      (w[1], "HindSiliguri-Bold.ttf", 80, 0.8, 4, dark, (1.6, 1.6, 0.5), -5),
                      (w[2], "HindSiliguri-Bold.ttf", 90, 1.35, 5, dark, (0.0, 0.9, -0.8), 2)])
    for o, t in zip(ws, L["ws"]): anim_slide(o, t, dx=-7)
    sp = light("SPOT", (-7, -4, 3.5), 5200, (1, 0.85, 0.65), size=0.2, spot=math.radians(45))
    key(sp, 1, loc=(-7, -4, 3.5), rot=look_rot((-7, -4, 3.5), (0, 3, 0.5))); key(sp, NF, loc=(-3, -6, 4.5), rot=look_rot((-3, -6, 4.5), (1, 3, 0)))
    light("AREA", (0, -6, 6), 60, (0.6, 0.7, 1.0), rot=(0.8, 0, 0), size=6)
    camera((0.8, -9.0, 0.6), (-0.5, -7.6, 0.4), (0, 2, 0.3), lens=35, shake=0.025)

elif SCN == 3:   # block heart on a checker floor; words drop on the beat
    world_color((0.03, 0.005, 0.01), 1)
    chk = make_tex("chk", [(235, 232, 228)], 2, pattern=lambda i, r: np.array([[[235, 232, 228], [25, 24, 28]], [[25, 24, 28], [235, 232, 228]]], np.float32))
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0)); fl = bpy.context.object
    fm = mat_tex("chk", chk, rough=0.15); fl.data.materials.append(fm)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.uv.unwrap(); bpy.ops.object.mode_set(mode="OBJECT")
    for d in fl.data.uv_layers[0].data: d.uv = (d.uv[0] * 30, d.uv[1] * 30)
    HEART = ["0110001100", "1111011110", "1111111111", "1111111111", "0111111110", "0011111100", "0001111000", "0000110000"]
    cells = {(c, d, 7 - r): (0, 0, 0) for r, row in enumerate(HEART) for c, ch in enumerate(row) if ch == "1" for d in range(2)}
    voxel_obj("heart", cells, 0.7, [mat_tex("red", TX["red"], emit=0.15)], origin=(-3.5, 3.0, 0.4))
    white = mat_col("white", (0.95, 0.95, 0.95), rough=0.35); yel = mat_col("yel", (1.0, 0.8, 0.3), rough=0.35)
    w = L["words"]
    ws = place_words([(w[0], "HindSiliguri-Bold.ttf", 80, 0.75, 4, white, (-1.8, 1.0, 4.0), 10),
                      (w[1], "HindSiliguri-Bold.ttf", 80, 0.8, 4, white, (1.6, 1.4, 4.4), -8),
                      (w[2], "HindSiliguri-Bold.ttf", 90, 1.1, 5, white, (-0.2, 0.6, 2.7), 0),
                      (w[3], "HindSiliguri-Bold.ttf", 80, 1.0, 5, yel, (1.9, 0.2, 1.3), -12)])
    for o, t in zip(ws, L["ws"]): anim_drop(o, t)
    light("SPOT", (-4, -5, 9), 3000, (1, 0.9, 0.85), look_rot((-4, -5, 9), (0, 2, 2)), 0.5, math.radians(60))
    light("POINT", (3, 0, 2), 200, (1, 0.2, 0.3), size=1)
    camera((-6.5, -8.0, 3.2), (4.5, -8.5, 2.4), (0, 2, 2.6), lens=30, shake=0.02)

elif SCN == 4:   # night city with searchlights; neon pixel words flicker on
    world_color((0.03, 0.01, 0.06), 1)
    bm = mat_tex("build", TX["build"], emit=2.2)
    cells = {}
    for bx in range(-18, 19, 3):
        for by in range(4, 22, 3):
            hgt = rnd.randint(4, 16)
            for x in range(2):
                for y in range(2):
                    for z in range(hgt): cells[(bx + x, by + y, z)] = (0, 0, 0)
    voxel_obj("city", cells, 1.0, [bm], origin=(0, 0, -2))
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, -2)); bpy.context.object.data.materials.append(mat_col("road", (0.02, 0.02, 0.03), rough=0.2))
    for i, (x, col) in enumerate([(-8, (0.7, 0.8, 1.0)), (9, (0.9, 0.7, 1.0))]):
        sp = light("SPOT", (x, 6, -1), 30000, col, size=0.1, spot=math.radians(6))
        key(sp, 1, rot=look_rot((x, 6, -1), (x + 10 * (1 if i else -1), 20, 30))); key(sp, NF, rot=look_rot((x, 6, -1), (x - 8 * (1 if i else -1), 20, 30)))
    ee.use_volumetric_lights = True
    vol = world.node_tree.nodes.new("ShaderNodeVolumeScatter"); vol.inputs["Density"].default_value = 0.012
    world.node_tree.links.new(vol.outputs[0], world.node_tree.nodes["World Output"].inputs["Volume"])
    ee.volumetric_tile_size = "8"; ee.volumetric_samples = 32
    w = L["words"]; specs = []
    for i, (col, loc, rz) in enumerate([((0.4, 0.9, 1.0), (-2.4, 2.0, 3.2), 6), ((1.0, 0.4, 0.85), (1.6, 2.6, 2.2), -8), ((1.0, 0.85, 0.4), (-0.4, 1.5, 0.9), 3)]):
        m = mat_col(f"neon{i}", col, emit=0.0, rough=0.4); specs.append((w[i], "HindSiliguri-Bold.ttf", 34, 1.5 + 0.3 * i, 2, m, loc, rz))
    ws = place_words(specs)
    for o, t, sp_ in zip(ws, L["ws"], specs): anim_flicker(sp_[5], o, t, 9)
    light("AREA", (0, -6, 6), 40, (0.6, 0.5, 1.0), rot=(0.8, 0, 0), size=8)
    camera((-4.5, -11.0, 1.8), (3.0, -10.5, 2.6), (0, 2, 2.0), lens=30, shake=0.03)

elif SCN == 5:   # sunrise over block hills; gold block words rise from behind the hill
    world_color((1.0, 0.42, 0.18), 0.85)
    mats = [mat_tex("grass", TX["grass"]), mat_tex("dirt_side", TX["dirt_side"])]
    terrain(40, 14, 2, 1.6, mats, 1.0, origin=(-20, 4, -3), seed=5, freq=0.22)
    terrain(40, 6, 1, 1.2, mats, 1.0, origin=(-20, -2, -3), seed=9, freq=0.3)
    voxel_obj("sun", {(x, 0, z): (0, 0, 0) for x in range(4) for z in range(4)}, 1.6, [mat_col("sun", (1.0, 0.85, 0.45), emit=14)], origin=(-3.2, 40, 9))
    light("SUN", (0, 0, 10), 4.5, (1.0, 0.75, 0.5), rot=(1.35, 0, 3.14))
    gold = mat_tex("gold", TX["gold"], rough=0.3, metal=0.6)
    w = L["words"]
    ws = place_words([(w[0], "HindSiliguri-Bold.ttf", 34, 1.3, 3, gold, (-2.0, 6.0, 2.6), 0),
                      (w[1], "HindSiliguri-Bold.ttf", 34, 1.4, 3, gold, (2.1, 6.4, 2.9), 0),
                      (w[2], "HindSiliguri-Bold.ttf", 34, 2.3, 3, gold, (-0.1, 5.4, 0.9), 0)])
    for o, t in zip(ws, L["ws"]): anim_rise(o, t, dz=3.5)
    camera((0.5, -5.0, -0.2), (-0.4, -2.8, 1.6), (0, 6, 1.8), lens=30, shake=0.025)

elif SCN == 6:   # spinning vinyl with the real cover as label; words printed on the record
    world_color((0.02, 0.012, 0.008), 1)
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.06)); bpy.context.object.data.materials.append(mat_tex("plank", TX["plank"], rough=0.6))
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=3.0, depth=0.08, location=(0, 0, 0)); rec = bpy.context.object
    rec.data.materials.append(mat_col("vinyl", (0.015, 0.015, 0.018), rough=0.18))
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.15, depth=0.1, location=(0, 0, 0)); lab = bpy.context.object
    lm = bpy.data.materials.new("label"); lm.use_nodes = True; nt = lm.node_tree
    ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(os.path.join(LD, "art.png"))
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.24, 0.43, 1); mp.inputs["Location"].default_value = (0.5, 0.5, 0)
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], ti.inputs[0]); nt.links.new(ti.outputs[0], nt.nodes["Principled BSDF"].inputs["Base Color"])
    lab.data.materials.append(lm); lab.parent = rec
    for r in np.linspace(1.3, 2.9, 28):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.006, location=(0, 0, 0.04)); g = bpy.context.object
        g.data.materials.append(mat_col("groove", (0.05, 0.05, 0.06), rough=0.1)); g.parent = rec
    white = mat_col("wht", (0.92, 0.92, 0.9), rough=0.4); gold = mat_col("gld", (1.0, 0.8, 0.35), rough=0.3, metal=0.5)
    w = L["words"]
    for i, (wd, m, ang) in enumerate([(w[0], white, 90), (w[1], white, -30), (w[2], gold, 210)]):
        o = word_obj(wd, "HindSiliguri-Bold.ttf", 80, 0.42, 2, m, f"vw{i}")
        a = math.radians(ang); o.location = (2.1 * math.cos(a), 2.1 * math.sin(a), 0.045)
        o.rotation_euler = (math.radians(90), 0, a - math.radians(90)); o.rotation_euler = (0, 0, a - math.radians(90))
        o.rotation_mode = "XYZ"; o.rotation_euler = (0, 0, a - math.radians(90))
        o.data.transform(__import__("mathutils").Matrix.Rotation(math.radians(-90), 4, "X"))
        o.parent = rec; anim_show(o, L["ws"][i])
    key(rec, 1, rot=(0, 0, 0)); key(rec, NF, rot=(0, 0, -math.radians(33.3 * 360 / 60 * NF / FPS)))
    interp(rec, "LINEAR")
    light("SPOT", (-3, -4, 6), 2500, (1, 0.9, 0.8), look_rot((-3, -4, 6), (0, 0, 0)), 0.8, math.radians(70))
    light("POINT", (3, 3, 2), 150, (0.5, 0.6, 1.0), size=1)
    camera((0.0, -5.5, 5.5), (0.6, -3.6, 4.2), (0, 0.3, 0), lens=30, shake=0.02)

elif SCN == 7:   # neon words switch on, glossy floor reflections
    world_color((0.03, 0.005, 0.04), 1)
    chk = os.path.join(HERE, "tex", "chk.png")
    if not os.path.exists(chk): Image.fromarray(np.array([[[235, 232, 228], [25, 24, 28]], [[25, 24, 28], [235, 232, 228]]], np.uint8)).save(chk)
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0)); fl = bpy.context.object
    fl.data.materials.append(mat_tex("chk2", chk, rough=0.08))
    for d in fl.data.uv_layers[0].data: d.uv = (d.uv[0] * 30, d.uv[1] * 30)
    w = L["words"]; specs = []
    for i, (col, loc, rz) in enumerate([((1.0, 0.25, 0.7), (-1.9, 2.2, 3.1), 8), ((0.3, 0.75, 1.0), (1.8, 2.8, 2.7), -10),
                                        ((1.0, 0.25, 0.7), (-0.3, 1.6, 1.6), 3), ((1.0, 0.8, 0.3), (2.0, 1.2, 0.6), -14)]):
        m = mat_col(f"neon{i}", col, emit=0.0, rough=0.4); specs.append((w[i], "Galada.ttf", 80, 1.0 + 0.15 * (i == 2), 2, m, loc, rz))
    ws = place_words(specs)
    for o, t, sp_ in zip(ws, L["ws"], specs): anim_flicker(sp_[5], o, t, 12)
    for i in range(40):
        voxel_obj(f"bk{i}", {(0, 0, 0): (0, 0, 0)}, rnd.uniform(0.05, 0.12), [mat_col(f"bk{i}", (1, 0.7, 1), emit=rnd.uniform(4, 10))],
                  origin=(rnd.uniform(-10, 10), rnd.uniform(4, 14), rnd.uniform(0.5, 7)))
    camera((-1.5, -7.5, 1.4), (0.8, -5.2, 2.0), (0, 2, 1.8), lens=32, shake=0.025, dof=None)

elif SCN == 8:   # typewriter: letters appear one by one on a dark desk, blinking cursor block
    world_color((0.005, 0.005, 0.006), 1)
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.02)); bpy.context.object.data.materials.append(mat_col("desk", (0.03, 0.03, 0.035), rough=0.3))
    paper = mat_col("ink", (0.92, 0.9, 0.85), rough=0.5)
    full = " ".join(L["words"])
    cl = []
    for ch in full:
        if cl and (0x0981 <= ord(ch) <= 0x0983 or 0x09BC <= ord(ch) <= 0x09D7 or cl[-1].endswith("্")): cl[-1] += ch
        else: cl.append(ch)
    fnt = ImageFont.truetype(os.path.join(FONTS, "HindSiliguri-Medium.ttf"), 80, layout_engine=ImageFont.Layout.RAQM)
    bb = fnt.getbbox(full); MW, MH = bb[2] - bb[0] + 8, bb[3] - bb[1] + 8
    mk = Image.new("L", (MW, MH), 0); ImageDraw.Draw(mk).text((4 - bb[0], 4 - bb[1]), full, font=fnt, fill=255)
    A = np.asarray(mk) > 110; LINEW = 7.0; cell = LINEW / MW
    jit = np.random.default_rng(3).uniform(0.6, 1.5, len(cl)); tt = L["ws"][0]; prefix = ""; last = None; xprev = 0
    for i, c in enumerate(cl):
        tt += 0.075 * jit[i] + (0.18 if c == " " else 0)
        prefix += c; xe = int(round(4 - bb[0] + fnt.getlength(prefix))) if i < len(cl) - 1 else MW
        cells = {(cx, d, MH - 1 - r): (0, 0, 0) for r in range(MH) for cx in range(xprev, xe) if A[r, cx] for d in range(3)}
        if cells:
            o = voxel_obj(f"c{i}", cells, cell, [paper], origin=(-LINEW / 2, 0, 0.1)); anim_show(o, tt)
        last = (tt, -LINEW / 2 + xe * cell); xprev = xe
    tt = last[0]
    cur = voxel_obj("cursor", {(0, 0, 0): (0, 0, 0)}, 0.12, [mat_col("cur", (0.95, 0.95, 0.9), emit=2)], origin=(0, -0.06, 0.15))
    cur.scale = (0.5, 1, 6)
    for f in range(1, NF + 1, 8):
        cur.hide_render = (f // 8) % 2 == 1; cur.keyframe_insert("hide_render", frame=f)
    key(cur, 1, loc=(-3.5, 0, 0)); key(cur, F(tt) + 2, loc=(last[1] + 0.1, 0, 0)); interp(cur, "LINEAR")
    light("SPOT", (-1, -3, 4), 900, (1, 0.92, 0.8), look_rot((-1, -3, 4), (0, 0, 0.5)), 0.6, math.radians(80))
    camera((-2.0, -11.5, 1.8), (0.6, -10.0, 1.3), (0, 0, 0.5), lens=40, shake=0.012)

if os.environ.get("BTS"):   # real behind-the-scenes view: Blender solid viewport look, wide orbiting "custom view" camera
    import mathutils
    sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
    sh.light = "STUDIO"; sh.color_type = "RANDOM"; sh.show_cavity = True; sh.show_object_outline = True
    sh.show_shadows = True; sh.background_type = "VIEWPORT" if hasattr(sh, "background_type") else sh.background_type
    main = sc.camera; tg = main.constraints[0].target
    cd = bpy.data.cameras.new("CV"); cd.lens = 22; cv = bpy.data.objects.new("CV", cd); sc.collection.objects.link(cv)
    con = cv.constraints.new("TRACK_TO"); con.target = tg; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    base = mathutils.Vector(main.location) - mathutils.Vector(tg.location)
    r = max(base.length * 1.25, 8)
    for f in (1, NF):
        a = math.radians(-60 + 70 * (f - 1) / max(NF - 1, 1))
        cv.location = (tg.location[0] + r * math.sin(a), tg.location[1] - r * math.cos(a), tg.location[2] + r * 0.55); cv.keyframe_insert("location", frame=f)
    # show the real render camera as a small marker + its view line
    mk = voxel_obj("cam_marker", {(0, 0, 0): (0, 0, 0)}, 0.35, [mat_col("mk", (1, 0.2, 0.2))], origin=(-0.17, -0.17, -0.17)); mk.parent = main
    sc.camera = cv
os.makedirs(OUTD, exist_ok=True)
sc.render.filepath = os.path.join(OUTD, "f_####")
if ONLY:
    for f in ONLY:
        sc.frame_set(f); sc.render.filepath = os.path.join(OUTD, f"p_{f:04d}"); bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print("SCENE_DONE", SCN, NF)
