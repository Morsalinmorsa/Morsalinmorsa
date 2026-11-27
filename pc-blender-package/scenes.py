"""Shudhu Tomake - real 3D block-world scenes (Blender 4.0+).
Render one scene:   blender -b -P scenes.py -- SCENE OUTDIR [RES]
Environment:        ENGINE=CYCLES (GPU, best quality)  or  ENGINE=EEVEE (fast, default)
                    SAMPLES=128 (Cycles)   FRAMES=1,40,80 (render only these frames)   BTS=1 (Blender solid view)
Scenes: 0 intro, 1-8 the eight lyric lines.
"""
import bpy, sys, os, math, random, json, hashlib
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SCN = int(argv[0]); OUTD = os.path.abspath(argv[1]); RES = int(argv[2]) if len(argv) > 2 else 720
ENGINE = os.environ.get("ENGINE", "EEVEE").upper()
ONLY = [int(x) for x in os.environ["FRAMES"].split(",")] if os.environ.get("FRAMES") else None
HERE = os.path.dirname(os.path.abspath(__file__)); AS = os.path.join(HERE, "assets")
FPS = 30; BEAT0, BEAT = 79.90 - 78.0, 0.4616
rnd = random.Random(7 + SCN)

# ---------------- lyric timing (beat-snapped) ----------------
LINES = []
for ln in open(os.path.join(AS, "lyrics.txt"), encoding="utf-8"):
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
def F(t): return int(round((t - T0) * FPS)) + 1
L = LINES[SCN - 1] if 1 <= SCN <= 8 else None

# ---------------- render setup ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x = sc.render.resolution_y = RES; sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = NF
sc.render.image_settings.file_format = "PNG"
try: sc.view_settings.view_transform = "Filmic"; sc.view_settings.look = "Medium High Contrast"
except Exception:
    try: sc.view_settings.view_transform = "AgX"
    except Exception: pass
def setattr_safe(o, k, v):
    try: setattr(o, k, v)
    except Exception: pass
if ENGINE == "CYCLES":
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dev in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            prefs.compute_device_type = dev; prefs.get_devices()
            gpus = [d for d in prefs.devices if d.type == dev]
            if gpus:
                for d in prefs.devices: d.use = True
                sc.cycles.device = "GPU"; print("GPU:", dev, [d.name for d in gpus]); break
        except Exception: pass
    sc.cycles.samples = int(os.environ.get("SAMPLES", "128")); sc.cycles.use_adaptive_sampling = True
    setattr_safe(sc.cycles, "use_denoising", True); sc.render.use_motion_blur = True
    sc.cycles.max_bounces = 6
else:
    for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try: sc.render.engine = name; break
        except Exception: pass
    ee = sc.eevee
    for k, v in dict(use_bloom=True, bloom_intensity=0.06, bloom_threshold=0.9, use_gtao=True, gtao_distance=1.2, use_soft_shadows=True,
                     shadow_cube_size="1024", shadow_cascade_size="2048", taa_render_samples=24, use_ssr=True).items(): setattr_safe(ee, k, v)
world = bpy.data.worlds.new("W"); sc.world = world; world.use_nodes = True
def world_color(c, s=1.0):
    bg = world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (*c, 1); bg.inputs[1].default_value = s
def volume(density):
    vol = world.node_tree.nodes.new("ShaderNodeVolumeScatter"); vol.inputs["Density"].default_value = density
    world.node_tree.links.new(vol.outputs[0], world.node_tree.nodes["World Output"].inputs["Volume"])
    setattr_safe(sc.eevee, "use_volumetric_lights", True); setattr_safe(sc.eevee, "volumetric_tile_size", "8")

# ---------------- materials ----------------
_tex = {}
def TX(n): return os.path.join(AS, "tex", f"{n}.png")
def mat_tex(name, tex, emit=0.0, rough=0.8, metal=0.0):
    key = (name, tex, emit, rough, metal)
    if key in _tex: return _tex[key]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(TX(tex)); t.interpolation = "Closest"
    nt.links.new(t.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit: nt.links.new(t.outputs[0], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    _tex[key] = m; return m
def mat_col(name, col, emit=0.0, rough=0.5, metal=0.0, transmission=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit: b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    if transmission:
        for k in ("Transmission Weight", "Transmission"):
            if k in b.inputs: b.inputs[k].default_value = transmission
    return m

# ---------------- voxel mesh builder ----------------
DIRS = [((0, 0, 1), "top"), ((0, 0, -1), "bot"), ((1, 0, 0), "side"), ((-1, 0, 0), "side"), ((0, 1, 0), "side"), ((0, -1, 0), "side")]
QUAD = {(0, 0, 1): [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], (0, 0, -1): [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)],
        (1, 0, 0): [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], (-1, 0, 0): [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)],
        (0, 1, 0): [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)], (0, -1, 0): [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]}
def voxel_obj(name, cells, size, mats, origin=(0, 0, 0), solid=None):
    """cells: (x,y,z) -> (top, side, bottom) material indices. solid: extra occupied cells (hidden faces) e.g. other objects."""
    verts, vid, faces, fmat = [], {}, [], []
    for (x, y, z), m in cells.items():
        for d, kind in DIRS:
            nb = (x + d[0], y + d[1], z + d[2])
            if nb in cells: continue
            f = []
            for (a, b, c) in QUAD[d]:
                k = (x + a, y + b, z + c)
                if k not in vid: vid[k] = len(verts); verts.append((k[0] * size + origin[0], k[1] * size + origin[1], k[2] * size + origin[2]))
                f.append(vid[k])
            faces.append(f); fmat.append(m[0] if kind == "top" else m[2] if kind == "bot" else m[1])
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    uv = me.uv_layers.new()
    for poly in me.polygons:
        for li, (u, v) in zip(poly.loop_indices, [(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[li].uv = (u, v)
    for mat in mats: me.materials.append(mat)
    if fmat: me.polygons.foreach_set("material_index", fmat)
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob
def box(cells, x0, y0, z0, nx, ny, nz, m):
    for x in range(nx):
        for y in range(ny):
            for z in range(nz): cells[(x0 + x, y0 + y, z0 + z)] = m

# ---------------- Bangla words -> 3D block letters (masks shipped as PNG; made with PIL when missing) ----------------
def text_mask(word, font, rows):
    key = hashlib.md5(f"{word}|{font}|{rows}".encode()).hexdigest()[:16]; p = os.path.join(AS, "words", key + ".png")
    if not os.path.exists(p):
        from PIL import Image, ImageDraw, ImageFont
        f = ImageFont.truetype(os.path.join(AS, "fonts", font), rows, layout_engine=ImageFont.Layout.RAQM)
        bb = f.getbbox(word); m = Image.new("L", (bb[2] - bb[0] + 4, bb[3] - bb[1] + 4), 0)
        ImageDraw.Draw(m).text((2 - bb[0], 2 - bb[1]), word, font=f, fill=255); m.save(p)
    img = bpy.data.images.load(p); w, h = img.size
    a = np.array(img.pixels[:], np.float32).reshape(h, w, 4)[::-1, :, 0]
    bpy.data.images.remove(img)
    return a > 0.43
def word_obj(word, font, rows, height, depth_cells, mat, name="w"):
    a = text_mask(word, font, rows); H_, W_ = a.shape; cell = height / H_
    cells = {(c, d, H_ - 1 - r): (0, 0, 0) for r, c in zip(*np.nonzero(a)) for d in range(depth_cells)}
    ob = voxel_obj(name, cells, cell, [mat], origin=(-W_ * cell / 2, 0, -H_ * cell / 2)); return ob

# ---------------- helpers ----------------
def key(ob, f, loc=None, rot=None, scale=None):
    if loc is not None: ob.location = loc; ob.keyframe_insert("location", frame=f)
    if rot is not None: ob.rotation_euler = rot; ob.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: ob.scale = scale; ob.keyframe_insert("scale", frame=f)
def interp(ob, kind="BEZIER"):
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = kind
def noise_anim(ob, path, strength, scale=20):
    ob.keyframe_insert(path, frame=1)
    for fc in ob.animation_data.action.fcurves:
        if fc.data_path == path:
            n = fc.modifiers.new("NOISE"); n.strength = strength; n.scale = scale; n.phase = rnd.uniform(0, 100)
def camera(loc0, loc1, target, lens=35, shake=0.02, dof=None):
    cd = bpy.data.cameras.new("C"); cd.lens = lens; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
    tg = bpy.data.objects.new("T", None); sc.collection.objects.link(tg); tg.location = target
    con = cam.constraints.new("TRACK_TO"); con.target = tg; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    key(cam, 1, loc=loc0); key(cam, NF, loc=loc1)
    for fc in cam.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = "SINE"; kp.easing = "EASE_IN_OUT"
        n = fc.modifiers.new("NOISE"); n.scale = 14 + 6 * fc.array_index; n.strength = shake; n.phase = rnd.uniform(0, 50)
    if dof: cd.dof.use_dof = True; cd.dof.focus_object = dof[0]; cd.dof.aperture_fstop = dof[1]
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
def plane(size, loc, mat, uvrep=None):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc); o = bpy.context.object; o.data.materials.append(mat)
    if uvrep:
        for d in o.data.uv_layers[0].data: d.uv = (d.uv[0] * uvrep, d.uv[1] * uvrep)
    return o
def place_words(specs):
    obs = []
    for i, (wd, fnt, rows, hgt, dep, mt, loc, rz) in enumerate(specs):
        o = word_obj(wd, fnt, rows, hgt, dep, mt, f"word{i}"); o.location = loc; o.rotation_euler = (0, 0, math.radians(rz)); obs.append(o)
    return obs

# world-building pieces (cells into a shared dict; material index map given by caller)
def terrain_cells(cells, nx, ny, base, amp, ox, oy, freq=0.18, seed=0, gi=0, di=1):
    r = np.random.default_rng(seed); ph = r.uniform(0, 6, 4); hmap = {}
    for x in range(nx):
        for y in range(ny):
            h = max(1, int(base + amp * (math.sin(x * freq + ph[0]) * math.cos(y * freq * 0.8 + ph[1]) + 0.5 * math.sin((x + y) * freq * 1.7 + ph[2]))))
            for z in range(h): cells[(ox + x, oy + y, z)] = (gi, di, di) if z == h - 1 else (di, di, di)
            hmap[(ox + x, oy + y)] = h
    return hmap
def tree_cells(cells, x, y, z, li=2, wi=3, h=None):
    h = h or rnd.randint(3, 5)
    for k in range(h): cells[(x, y, z + k)] = (wi, wi, wi)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            for dz in range(h - 1, h + 2):
                if abs(dx) + abs(dy) + max(0, dz - h) * 2 <= 3 and (dx, dy) != (0, 0) or dz >= h:
                    if abs(dx) + abs(dy) <= (3 if dz < h + 1 else 1): cells.setdefault((x + dx, y + dy, z + dz), (li, li, li))
def cloud(name, x, y, z, mat, drift):
    cells = {}
    for _ in range(rnd.randint(4, 7)):
        cx, cy = rnd.randint(-3, 3), rnd.randint(-1, 1); box(cells, cx, cy, 0, rnd.randint(2, 4), rnd.randint(1, 3), 1, (0, 0, 0))
    o = voxel_obj(name, cells, 1.0, [mat], origin=(0, 0, 0)); key(o, 1, loc=(x, y, z)); key(o, NF, loc=(x + drift, y, z)); interp(o, "LINEAR"); return o
def car(name, color_tex, path0, path1, z, yaw):
    cells = {}
    box(cells, 0, 0, 1, 8, 4, 2, (0, 0, 0)); box(cells, 2, 0, 3, 4, 4, 2, (1, 1, 1))
    for wx in (1, 6):
        for wy in (-1, 4): cells[(wx, wy, 0)] = (2, 2, 2); cells[(wx, wy, 1)] = (2, 2, 2)
    o = voxel_obj(name, cells, 0.3, [mat_tex("car_" + color_tex, color_tex, rough=0.3, metal=0.4), mat_tex("glass", "glass", rough=0.05), mat_col("tyre", (0.03, 0.03, 0.03), rough=0.7)],
                  origin=(-1.2, -0.6, 0))
    hl = voxel_obj(name + "_hl", {(0, 0, 0): (0, 0, 0), (0, 3, 0): (0, 0, 0)}, 0.3, [mat_col("hl", (1, 0.95, 0.8), emit=25)], origin=(1.2, -0.6, 0.35)); hl.parent = o
    tl = voxel_obj(name + "_tl", {(0, 0, 0): (0, 0, 0), (0, 3, 0): (0, 0, 0)}, 0.3, [mat_col("tl", (1, 0.05, 0.05), emit=12)], origin=(-1.5, -0.6, 0.35)); tl.parent = o
    o.rotation_euler = (0, 0, yaw); key(o, 1, loc=(*path0, z)); key(o, NF, loc=(*path1, z)); interp(o, "LINEAR"); return o
def lamp_post(cells, x, y, z, h=6, pi=0):
    for k in range(h): cells[(x, y, z + k)] = (pi, pi, pi)

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
    f = F(t); loc = tuple(ob.location); key(ob, max(1, f - 10), loc=(loc[0] + dx, loc[1], loc[2])); key(ob, f + 4, loc=loc)
def anim_show(ob, t):
    f = F(t); ob.hide_render = True; ob.keyframe_insert("hide_render", frame=1); ob.hide_render = False; ob.keyframe_insert("hide_render", frame=max(2, f))
def anim_flicker(mat, ob, t, strength):
    f = F(t); inp = mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]; anim_show(ob, t - 0.05)
    for i, v in enumerate([1, 0, 1, 1, 0, 0, 1, 0.3, 1, 1]): inp.default_value = strength * v; inp.keyframe_insert("default_value", frame=f + i - 1)
    for c in mat.node_tree.animation_data.action.fcurves:
        for kp in c.keyframe_points: kp.interpolation = "CONSTANT"

# ====================================================================================
if SCN == 0:   # intro: title in block letters, a work light flickers on
    world_color((0, 0, 0), 0)
    t1 = word_obj("SHUDHU TOMAKE", "Poppins-SemiBold.ttf", 30, 0.72, 3, mat_col("title", (1.0, 0.85, 0.55), rough=0.4), "title"); t1.location = (0, 0, 0.4)
    t2 = word_obj("FRANKLIN", "Poppins-SemiBold.ttf", 22, 0.42, 2, mat_col("sub", (0.9, 0.9, 0.95), rough=0.5), "sub"); t2.location = (0, 0, -0.55)
    plane(40, (0, 0, -1.2), mat_col("fl", (0.05, 0.05, 0.06), rough=0.25))
    lt = light("SPOT", (0, -7, 4), 1600, (1, 0.9, 0.75), look_rot((0, -7, 4), (0, 0, 0)), 0.3, math.radians(95))
    for i, v in enumerate([0, 1, 0, 0, 1, 1, 0, 1, 1, 1]): lt.data.energy = 1600 * v; lt.data.keyframe_insert("energy", frame=1 + i * 3)
    for c in lt.data.animation_data.action.fcurves:
        for kp in c.keyframe_points: kp.interpolation = "CONSTANT"
    camera((0.4, -14.0, 1.0), (0, -11.5, 0.5), (0, 0, 0), lens=40, shake=0.015)

elif SCN == 1:   # lantern night: hills, trees, pond, fence, fireflies, moon
    world_color((0.008, 0.01, 0.04), 1)
    mats = [mat_tex("grass", "grass"), mat_tex("dirt_side", "dirt_side"), mat_tex("leaves", "leaves"), mat_tex("log", "log"), mat_tex("plank", "plank")]
    cells = {}; hm = terrain_cells(cells, 40, 36, 2, 1.3, -20, -6, seed=1)
    for _ in range(14):
        x, y = rnd.randint(-19, 19), rnd.randint(6, 28)
        if abs(x) > 3 or y > 10: tree_cells(cells, x, y, hm[(x, y)])
    for x in range(-12, -4): cells[(x, -2, hm[(x, -2)])] = (4, 4, 4)          # fence
    voxel_obj("world", cells, 1.0, mats, origin=(0, 0, -3))
    plane(8, (6, 0, -1.05), mat_col("water", (0.05, 0.12, 0.25), rough=0.02, metal=0.2))
    voxel_obj("lantern", {(0, 0, 0): (0, 0, 0)}, 0.9, [mat_tex("lan", "lantern", emit=6)], origin=(-0.45, 3, -0.2))
    light("POINT", (0, 3.4, 0.5), 700, (1, 0.55, 0.2), size=0.6)
    light("SUN", (0, 0, 10), 0.25, (0.5, 0.6, 1.0), rot=(0.7, 0.2, 0.5))
    voxel_obj("moon", {(x, 0, z): (0, 0, 0) for x in range(3) for z in range(3)}, 1.2, [mat_col("moon", (0.9, 0.92, 1.0), emit=8)], origin=(9, 45, 16))
    for i in range(70):
        voxel_obj(f"star{i}", {(0, 0, 0): (0, 0, 0)}, 0.08, [mat_col(f"st{i}", (1, 1, 1), emit=rnd.uniform(3, 12))],
                  origin=(rnd.uniform(-30, 30), rnd.uniform(25, 40), rnd.uniform(4, 18)))
    fm = mat_col("firefly", (1.0, 0.9, 0.3), emit=30)
    for i in range(24):
        ff = voxel_obj(f"ff{i}", {(0, 0, 0): (0, 0, 0)}, 0.06, [fm]); ff.location = (rnd.uniform(-6, 6), rnd.uniform(-2, 8), rnd.uniform(-0.5, 2.5))
        noise_anim(ff, "location", 0.6, scale=30)
    cream = mat_col("cream", (1.0, 0.86, 0.6), rough=0.35); glow = mat_col("glow", (1.0, 0.7, 0.3), emit=3.5)
    w = L["words"]
    ws = place_words([(w[0], "HindSiliguri-Bold.ttf", 80, 0.75, 4, cream, (-1.7, 1.5, 2.3), 8),
                      (w[1], "HindSiliguri-Bold.ttf", 80, 0.95, 5, cream, (1.4, 2.2, 2.0), -6),
                      (w[2], "HindSiliguri-Bold.ttf", 90, 1.5, 6, glow, (0.1, 1.2, 0.9), 3)])
    for o, t in zip(ws, L["ws"]): anim_rise(o, t)
    camera((-3.5, -8.5, 2.6), (-0.6, -4.2, 1.6), (0, 2, 1.2), lens=32, shake=0.03)

elif SCN == 2:   # stone hall: torches, vines, cobble floor; words cast real shadows
    world_color((0.01, 0.01, 0.012), 1)
    cells = {}
    box(cells, -14, 0, -6, 29, 1, 18, (0, 0, 0))
    for x in range(-14, 15, 2):
        if rnd.random() < 0.6:
            for z in range(11, 11 - rnd.randint(2, 7), -1): cells[(x, -1, z)] = (1, 1, 1)
    voxel_obj("wall", cells, 0.6, [mat_tex("stone", "stone"), mat_tex("leaves", "leaves")], origin=(0, 4.6, 0))
    plane(40, (0, 0, -3.6), mat_tex("cobble", "cobble"), 20)
    for tx in (-4.5, 4.5):
        voxel_obj("torch", {(0, 0, 0): (0, 0, 0), (0, 0, 1): (0, 0, 0)}, 0.25, [mat_tex("log", "log")], origin=(tx, 4.1, 1.2))
        voxel_obj("flame", {(0, 0, 0): (0, 0, 0)}, 0.25, [mat_col("flame", (1.0, 0.55, 0.15), emit=20)], origin=(tx, 4.1, 1.7))
        tl = light("POINT", (tx + 0.12, 3.6, 1.9), 180, (1.0, 0.5, 0.15), size=0.2); noise_anim(tl.data, "energy", 60, scale=3)
    stonew = mat_col("dark", (0.85, 0.8, 0.7), rough=0.55)
    w = L["words"]
    ws = place_words([(w[0], "HindSiliguri-Bold.ttf", 80, 0.9, 4, stonew, (-1.3, 1.2, 1.3), 4),
                      (w[1], "HindSiliguri-Bold.ttf", 80, 0.8, 4, stonew, (1.6, 1.6, 0.5), -5),
                      (w[2], "HindSiliguri-Bold.ttf", 90, 1.35, 5, stonew, (0.0, 0.9, -0.8), 2)])
    for o, t in zip(ws, L["ws"]): anim_slide(o, t, dx=-7)
    sp = light("SPOT", (-7, -4, 3.5), 5200, (1, 0.85, 0.65), size=0.2, spot=math.radians(45))
    key(sp, 1, loc=(-7, -4, 3.5), rot=look_rot((-7, -4, 3.5), (0, 3, 0.5))); key(sp, NF, loc=(-3, -6, 4.5), rot=look_rot((-3, -6, 4.5), (1, 3, 0)))
    light("AREA", (0, -6, 6), 60, (0.6, 0.7, 1.0), rot=(0.8, 0, 0), size=6)
    camera((0.8, -9.0, 0.6), (-0.5, -7.6, 0.4), (0, 2, 0.3), lens=35, shake=0.025)

elif SCN == 3:   # heart hall: block heart, quartz pillars, floating hearts, checker floor
    world_color((0.03, 0.005, 0.01), 1)
    plane(60, (0, 0, 0), mat_tex("chk", "chk", rough=0.15), 30)
    HEART = ["0110001100", "1111011110", "1111111111", "1111111111", "0111111110", "0011111100", "0001111000", "0000110000"]
    hc = {(c, d, 7 - r): (0, 0, 0) for r, row in enumerate(HEART) for c, ch in enumerate(row) if ch == "1" for d in range(2)}
    voxel_obj("heart", hc, 0.7, [mat_tex("red", "red", emit=0.15)], origin=(-3.5, 3.0, 0.4))
    pc = {}
    for px in (-7, -4, 4, 7):
        box(pc, px, 4, 0, 1, 1, 9, (0, 0, 0)); box(pc, px - 1, 3, 9, 3, 3, 1, (0, 0, 0)); box(pc, px - 1, 3, 0, 3, 3, 1, (0, 0, 0))
    voxel_obj("pillars", pc, 0.7, [mat_tex("quartz", "quartz", rough=0.3)], origin=(0, 0, 0))
    small = {(c, 0, 7 - r): (0, 0, 0) for r, row in enumerate(HEART) for c, ch in enumerate(row) if ch == "1"}
    for i in range(7):
        h = voxel_obj(f"mini{i}", small, 0.08, [mat_col(f"mh{i}", (1, 0.25, 0.4), emit=3)]); h.location = (rnd.uniform(-6, 6), rnd.uniform(1, 6), rnd.uniform(1.5, 6))
        noise_anim(h, "location", 0.4, scale=40)
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

elif SCN == 4:   # night city: street, sidewalks, lamps, moving cars, trees, varied buildings, searchlights
    world_color((0.03, 0.01, 0.06), 1); volume(0.01)
    plane(120, (0, 20, -2.0), mat_tex("asphalt", "asphalt", rough=0.25), 60)
    side = {}; box(side, -40, -3, 0, 80, 2, 1, (0, 0, 0)); box(side, -40, 6, 0, 80, 2, 1, (0, 0, 0))
    voxel_obj("sidewalks", side, 1.0, [mat_tex("sidewalk", "sidewalk")], origin=(0, 0, -2))
    stripes = {(x, 2, 0): (0, 0, 0) for x in range(-40, 40, 3)}
    voxel_obj("stripes", stripes, 1.0, [mat_col("stripe", (0.9, 0.85, 0.6), emit=0.4)], origin=(0, 0.3, -2.95)).scale = (1, 0.15, 0.05)
    bm = mat_tex("build", "build", emit=2.2); bc = {}
    for row_y, flip in ((8, 1), (15, 1)):
        x = -38
        while x < 38:
            w_ = rnd.randint(3, 6); d_ = rnd.randint(3, 6); hgt = rnd.randint(5, 22)
            box(bc, x, row_y, 0, w_, d_, hgt + (8 if row_y > 10 else 0), (0, 0, 0)); x += w_ + rnd.randint(0, 1)
    voxel_obj("city", bc, 1.0, [bm], origin=(0, 0, -2))
    pc = {}
    for lx in range(-24, 25, 8):
        lamp_post(pc, lx, 7, 1, 5)
        lp = light("POINT", (lx + 0.5, 7.0, 4.2), 300, (1.0, 0.8, 0.5), size=0.3)
    voxel_obj("posts", pc, 1.0, [mat_col("post", (0.15, 0.15, 0.17), rough=0.4)], origin=(0, 0, -2))
    for lx in range(-24, 25, 8): voxel_obj("bulb", {(0, 0, 0): (0, 0, 0)}, 0.5, [mat_col("bulb", (1, 0.85, 0.6), emit=20)], origin=(lx + 0.25, 7.2, 3.6))
    tc = {}
    for tx in range(-30, 31, 10): tree_cells(tc, tx, 6, 1, li=0, wi=1, h=3)
    voxel_obj("trees", tc, 1.0, [mat_tex("leaves", "leaves"), mat_tex("log", "log")], origin=(0, 0, -2))
    for i, (ct, y, dirn) in enumerate([("car_red", 0.2, 1), ("car_blue", 0.2, 1), ("car_yellow", 3.6, -1), ("car_white", 3.6, -1), ("car_red", 0.2, 1)]):
        x0 = -30 + i * 14 if dirn > 0 else 30 - i * 12
        car(f"car{i}", ct, (x0, y), (x0 + dirn * 22, y), -2.0, 0 if dirn > 0 else math.pi)
    for i, (x, col) in enumerate([(-8, (0.7, 0.8, 1.0)), (9, (0.9, 0.7, 1.0))]):
        sp = light("SPOT", (x, 10, -1), 30000, col, size=0.1, spot=math.radians(6))
        key(sp, 1, rot=look_rot((x, 10, -1), (x + 10 * (1 if i else -1), 24, 30))); key(sp, NF, rot=look_rot((x, 10, -1), (x - 8 * (1 if i else -1), 24, 30)))
    w = L["words"]; specs = []
    for i, (col, loc, rz) in enumerate([((0.4, 0.9, 1.0), (-2.4, 3.0, 4.2), 6), ((1.0, 0.4, 0.85), (1.8, 3.6, 3.2), -8), ((1.0, 0.85, 0.4), (-0.4, 2.5, 1.9), 3)]):
        specs.append((w[i], "HindSiliguri-Bold.ttf", 34, 1.5 + 0.3 * i, 2, mat_col(f"neon{i}", col, rough=0.4), loc, rz))
    ws = place_words(specs)
    for o, t, sp_ in zip(ws, L["ws"], specs): anim_flicker(sp_[5], o, t, 9)
    light("AREA", (0, -6, 6), 40, (0.6, 0.5, 1.0), rot=(0.8, 0, 0), size=8)
    camera((-6.0, -9.5, 1.2), (3.0, -9.0, 2.4), (0, 3, 2.4), lens=28, shake=0.03)

elif SCN == 5:   # sunrise valley: hills, trees, river, drifting clouds
    world_color((1.0, 0.42, 0.18), 0.85)
    mats = [mat_tex("grass", "grass"), mat_tex("dirt_side", "dirt_side"), mat_tex("leaves", "leaves"), mat_tex("log", "log"), mat_tex("sand", "sand")]
    cells = {}
    hm = terrain_cells(cells, 44, 16, 2, 1.6, -22, 4, freq=0.22, seed=5)
    for _ in range(10):
        x, y = rnd.randint(-21, 21), rnd.randint(9, 19); tree_cells(cells, x, y, hm[(x, y)])
    hm2 = terrain_cells(cells, 44, 6, 1, 1.2, -22, -2, freq=0.3, seed=9)
    for x in range(-22, 22): cells[(x, 3, 0)] = (4, 4, 4)
    voxel_obj("valley", cells, 1.0, mats, origin=(0, 0, -3))
    plane(1, (0, 3.5, -2.55), mat_col("river", (0.15, 0.35, 0.55), rough=0.03, metal=0.3)).scale = (44, 1.0, 1)
    voxel_obj("sun", {(x, 0, z): (0, 0, 0) for x in range(4) for z in range(4)}, 1.6, [mat_col("sun", (1.0, 0.85, 0.45), emit=14)], origin=(-3.2, 40, 9))
    cm = mat_col("cloud", (1, 0.92, 0.85), rough=0.9)
    for i in range(7): cloud(f"cloud{i}", rnd.uniform(-22, 18), rnd.uniform(18, 34), rnd.uniform(7, 12), cm, 3)
    light("SUN", (0, 0, 10), 4.5, (1.0, 0.75, 0.5), rot=(1.35, 0, 3.14))
    gold = mat_tex("gold", "gold", rough=0.3, metal=0.6)
    w = L["words"]
    ws = place_words([(w[0], "HindSiliguri-Bold.ttf", 34, 1.3, 3, gold, (-2.0, 6.0, 2.6), 0),
                      (w[1], "HindSiliguri-Bold.ttf", 34, 1.4, 3, gold, (2.1, 6.4, 2.9), 0),
                      (w[2], "HindSiliguri-Bold.ttf", 34, 2.3, 3, gold, (-0.1, 5.4, 0.9), 0)])
    for o, t in zip(ws, L["ws"]): anim_rise(o, t, dz=3.5)
    camera((0.5, -5.0, -0.2), (-0.4, -2.8, 1.6), (0, 6, 1.8), lens=30, shake=0.025)

elif SCN == 6:   # record player in a room: wood box, tonearm, shelf, lamp; real cover as label
    import mathutils
    world_color((0.02, 0.012, 0.008), 1)
    plane(40, (0, 0, -0.62), mat_tex("plank", "plank", rough=0.6), 16)
    pb = {}; box(pb, -9, -9, 0, 19, 19, 2, (0, 0, 0))
    voxel_obj("player", pb, 0.35, [mat_tex("log", "log", rough=0.5)], origin=(0, 0, -0.62 - 0.0))
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=3.0, depth=0.08, location=(0, 0, 0.1)); rec = bpy.context.object
    rec.data.materials.append(mat_col("vinyl", (0.015, 0.015, 0.018), rough=0.18))
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.15, depth=0.1, location=(0, 0, 0.1)); lab = bpy.context.object
    lm = bpy.data.materials.new("label"); lm.use_nodes = True; nt = lm.node_tree
    ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(os.path.join(AS, "art.png"))
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.24, 0.43, 1); mp.inputs["Location"].default_value = (0.5, 0.5, 0)
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], ti.inputs[0]); nt.links.new(ti.outputs[0], nt.nodes["Principled BSDF"].inputs["Base Color"])
    lab.data.materials.append(lm); lab.parent = rec
    gm = mat_col("groove", (0.05, 0.05, 0.06), rough=0.1)
    for r in np.linspace(1.3, 2.9, 28):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.006, location=(0, 0, 0.14)); g = bpy.context.object; g.data.materials.append(gm); g.parent = rec
    arm = {(i, 0, 0): (0, 0, 0) for i in range(12)}; arm[(0, 0, 1)] = (0, 0, 0)
    ta = voxel_obj("tonearm", arm, 0.22, [mat_col("arm", (0.75, 0.75, 0.78), rough=0.25, metal=0.9)], origin=(0, 0, 0)); ta.location = (2.9, 2.9, 0.25)
    ta.rotation_euler = (0, 0, math.radians(200))
    white = mat_col("wht", (0.92, 0.92, 0.9), rough=0.4); gold = mat_col("gld", (1.0, 0.8, 0.35), rough=0.3, metal=0.5)
    w = L["words"]
    for i, (wd, m, ang) in enumerate([(w[0], white, 90), (w[1], white, -30), (w[2], gold, 210)]):
        o = word_obj(wd, "HindSiliguri-Bold.ttf", 80, 0.42, 2, m, f"vw{i}")
        o.data.transform(mathutils.Matrix.Rotation(math.radians(-90), 4, "X"))
        a = math.radians(ang); o.location = (2.1 * math.cos(a), 2.1 * math.sin(a), 0.145); o.rotation_euler = (0, 0, a - math.radians(90))
        o.parent = rec; anim_show(o, L["ws"][i])
    key(rec, 1, rot=(0, 0, 0)); key(rec, NF, rot=(0, 0, -math.radians(33.3 * 360 / 60 * NF / FPS))); interp(rec, "LINEAR")
    sh = {}; box(sh, -12, 12, 6, 24, 2, 1, (0, 0, 0)); voxel_obj("shelf", sh, 0.5, [mat_tex("plank", "plank")], origin=(0, 0, 0))
    for i in range(8):
        voxel_obj(f"book{i}", {(0, 0, z): (0, 0, 0) for z in range(rnd.randint(2, 4))}, 0.5, [mat_col(f"bk{i}", (rnd.random(), rnd.random() * 0.6, rnd.random() * 0.5), rough=0.6)],
                  origin=(-5 + i * 1.1, 6.0, 3.5))
    light("SPOT", (-3, -4, 6), 2500, (1, 0.9, 0.8), look_rot((-3, -4, 6), (0, 0, 0)), 0.8, math.radians(70))
    light("POINT", (4, 5, 3), 250, (1, 0.6, 0.3), size=1)
    camera((0.0, -5.5, 5.5), (0.6, -3.6, 4.2), (0, 0.3, 0), lens=30, shake=0.02)

elif SCN == 7:   # neon club: tube frames on walls, pillars, hanging light bars, glossy floor
    world_color((0.03, 0.005, 0.04), 1)
    plane(60, (0, 0, 0), mat_tex("chk2", "chk", rough=0.08), 30)
    wl = {}; box(wl, -20, 10, 0, 40, 1, 14, (0, 0, 0)); voxel_obj("backwall", wl, 1.0, [mat_col("bw", (0.05, 0.03, 0.07), rough=0.6)])
    for i, (x0, col) in enumerate([(-9, (1, 0.2, 0.7)), (-2, (0.3, 0.7, 1)), (5, (1, 0.8, 0.3))]):
        fr = {}
        for x in range(5): fr[(x, 0, 0)] = fr[(x, 0, 6)] = (0, 0, 0)
        for z in range(7): fr[(0, 0, z)] = fr[(4, 0, z)] = (0, 0, 0)
        voxel_obj(f"tube{i}", fr, 0.5, [mat_col(f"tb{i}", col, emit=8)], origin=(x0, 9.6, 2))
    for i in range(6):
        bar = voxel_obj(f"bar{i}", {(x, 0, 0): (0, 0, 0) for x in range(6)}, 0.18, [mat_col(f"lb{i}", (1, 0.9, 1), emit=12)]); bar.location = (-6 + i * 2.4, 4, 8)
        noise_anim(bar, "rotation_euler", 0.08, scale=50)
    w = L["words"]; specs = []
    for i, (col, loc, rz) in enumerate([((1.0, 0.25, 0.7), (-1.9, 2.2, 3.1), 8), ((0.3, 0.75, 1.0), (1.8, 2.8, 2.7), -10),
                                        ((1.0, 0.25, 0.7), (-0.3, 1.6, 1.6), 3), ((1.0, 0.8, 0.3), (2.0, 1.2, 0.6), -14)]):
        specs.append((w[i], "Galada.ttf", 80, 1.0 + 0.15 * (i == 2), 2, mat_col(f"neon{i}", col, rough=0.4), loc, rz))
    ws = place_words(specs)
    for o, t, sp_ in zip(ws, L["ws"], specs): anim_flicker(sp_[5], o, t, 12)
    for i in range(40):
        voxel_obj(f"bk{i}", {(0, 0, 0): (0, 0, 0)}, rnd.uniform(0.05, 0.12), [mat_col(f"bkc{i}", (1, 0.7, 1), emit=rnd.uniform(4, 10))],
                  origin=(rnd.uniform(-10, 10), rnd.uniform(4, 9), rnd.uniform(0.5, 7)))
    camera((-1.5, -7.5, 1.4), (0.8, -5.2, 2.0), (0, 2, 1.8), lens=32, shake=0.025)

elif SCN == 8:   # typewriter: letters appear on a sheet of paper on a wooden desk, desk lamp, blinking cursor
    world_color((0.005, 0.005, 0.006), 1)
    plane(40, (0, 0, -0.02), mat_tex("plank", "plank", rough=0.45), 14)
    plane(1, (0, 0.3, 0.0), mat_col("paper", (0.9, 0.88, 0.82), rough=0.8)).scale = (8.5, 3.0, 1)
    ink = mat_col("ink", (0.08, 0.08, 0.1), rough=0.5)
    full = " ".join(L["words"])
    cl = []
    for ch in full:
        if cl and (0x0981 <= ord(ch) <= 0x0983 or 0x09BC <= ord(ch) <= 0x09D7 or cl[-1].endswith("্")): cl[-1] += ch
        else: cl.append(ch)
    cuts_p = os.path.join(AS, "words", "typewriter_cuts.json")
    if not os.path.exists(cuts_p):
        from PIL import ImageFont
        fnt = ImageFont.truetype(os.path.join(AS, "fonts", "HindSiliguri-Medium.ttf"), 80, layout_engine=ImageFont.Layout.RAQM)
        bb = fnt.getbbox(full); pre = ""; cuts = []
        for c in cl: pre += c; cuts.append(int(round(2 - bb[0] + fnt.getlength(pre))))
        json.dump(cuts, open(cuts_p, "w"))
    cuts = json.load(open(cuts_p)); A = text_mask(full, "HindSiliguri-Medium.ttf", 80); MH, MW = A.shape; cuts[-1] = MW
    LINEW = 7.0; cell = LINEW / MW
    jit = np.random.default_rng(3).uniform(0.6, 1.5, len(cl)); tt = L["ws"][0]; xprev = 0
    for i, c in enumerate(cl):
        tt += 0.075 * jit[i] + (0.18 if c == " " else 0); xe = cuts[i]
        rs, cs = np.nonzero(A[:, xprev:xe])
        cells = {(cx + xprev, d, MH - 1 - r): (0, 0, 0) for r, cx in zip(rs, cs) for d in range(2)}
        if cells:
            o = voxel_obj(f"c{i}", cells, cell, [ink], origin=(-LINEW / 2, 0, 0))
            o.data.transform(__import__("mathutils").Matrix.Rotation(math.radians(-90), 4, "X")); o.location = (0, -0.1, 2 * cell + 0.01); anim_show(o, tt)
        last = (tt, -LINEW / 2 + xe * cell); xprev = xe
    cur = voxel_obj("cursor", {(0, 0, 0): (0, 0, 0)}, 0.12, [mat_col("cur", (0.1, 0.1, 0.12), rough=0.4)], origin=(0, -0.06, 0.1)); cur.scale = (0.5, 6, 0.3)
    for f in range(1, NF + 1, 8): cur.hide_render = (f // 8) % 2 == 1; cur.keyframe_insert("hide_render", frame=f)
    key(cur, 1, loc=(-3.5, 0.0, -0.05)); key(cur, F(last[0]) + 2, loc=(last[1] + 0.1, 0.0, -0.05)); interp(cur, "LINEAR")
    lampc = {}; box(lampc, 0, 0, 0, 2, 2, 1, (0, 0, 0)); box(lampc, 0, 0, 1, 1, 1, 6, (0, 0, 0)); box(lampc, -2, 0, 7, 4, 2, 1, (0, 0, 0))
    voxel_obj("desklamp", lampc, 0.3, [mat_col("lampc", (0.1, 0.25, 0.2), rough=0.3, metal=0.6)], origin=(4.0, 2.0, 0))
    light("SPOT", (3.4, 2.3, 1.85), 900, (1, 0.88, 0.7), look_rot((3.4, 2.3, 1.85), (0, 0.2, 0)), 0.3, math.radians(110))
    light("AREA", (-3, -4, 5), 160, (0.6, 0.7, 1), rot=(0.7, 0, -0.5), size=5)
    camera((-1.2, -6.0, 6.2), (0.5, -5.0, 5.2), (0, 0.5, 0), lens=31, shake=0.012)

if os.environ.get("BTS"):   # Blender solid view of the same scene from a wide orbiting camera
    import mathutils
    sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
    sh.light = "STUDIO"; sh.color_type = "RANDOM"; sh.show_cavity = True; sh.show_object_outline = True; sh.show_shadows = True
    main = sc.camera; tg = main.constraints[0].target
    cd = bpy.data.cameras.new("CV"); cd.lens = 22; cv = bpy.data.objects.new("CV", cd); sc.collection.objects.link(cv)
    con = cv.constraints.new("TRACK_TO"); con.target = tg; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    r = max((mathutils.Vector(main.location) - mathutils.Vector(tg.location)).length * 1.25, 8)
    for f in (1, NF):
        a = math.radians(-60 + 70 * (f - 1) / max(NF - 1, 1))
        cv.location = (tg.location[0] + r * math.sin(a), tg.location[1] - r * math.cos(a), tg.location[2] + r * 0.55); cv.keyframe_insert("location", frame=f)
    mk = voxel_obj("cam_marker", {(0, 0, 0): (0, 0, 0)}, 0.35, [mat_col("mk", (1, 0.2, 0.2))], origin=(-0.17, -0.17, -0.17)); mk.parent = main
    sc.camera = cv

os.makedirs(OUTD, exist_ok=True)
if ONLY:
    for f in ONLY:
        sc.frame_set(f); sc.render.filepath = os.path.join(OUTD, f"p_{f:04d}"); bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = os.path.join(OUTD, "f_####"); bpy.ops.render.render(animation=True)
print("SCENE_DONE", SCN, NF)
