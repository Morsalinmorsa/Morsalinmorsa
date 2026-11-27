"""Tum Bin - Minecraft-style 3D music video (Blender 4.0+). Animated block characters + 3D Bangla lyrics.
Render one scene:  blender -b -P mc.py -- SCENE(1-8) OUTDIR [RES]     env: ENGINE=CYCLES|EEVEE, FRAMES=1,40
"""
import bpy, sys, os, math, random, json, hashlib
import numpy as np
argv = sys.argv[sys.argv.index("--") + 1:]
SCN = int(argv[0]); OUTD = os.path.abspath(argv[1]); RES = int(argv[2]) if len(argv) > 2 else 720
ENGINE = os.environ.get("ENGINE", "EEVEE").upper()
ONLY = [int(x) for x in os.environ["FRAMES"].split(",")] if os.environ.get("FRAMES") else None
HERE = os.path.dirname(os.path.abspath(__file__)); AS = os.path.join(HERE, "assets")
FPS = 30; rnd = random.Random(11 + SCN)
LY = json.load(open(os.path.join(AS, "lyrics.json"), encoding="utf-8"))
BOUNDS = [0.0, 3.75, 7.45, 11.85, 15.9, 19.85, 24.0, 28.2, 31.55]
T0, T1 = BOUNDS[SCN - 1], BOUNDS[SCN]
NF = int(round((T1 - T0) * FPS))
def F(t): return int(round((t - T0) * FPS)) + 1
L = LY[SCN - 1]
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


# ======================= characters =======================
PX = 2.0 / 32
def _mats(pal):
    return [mat_col(f"c{i}", c, rough=0.85) for i, c in enumerate(pal)]
STEVE = dict(pal=[(0.20, 0.12, 0.06), (0.74, 0.53, 0.40), (0.95, 0.95, 0.95), (0.30, 0.22, 0.58), (0.45, 0.27, 0.18), (0.27, 0.17, 0.09),
                  (0.0, 0.66, 0.68), (0.0, 0.52, 0.55), (0.27, 0.23, 0.62), (0.40, 0.40, 0.42), (0.62, 0.43, 0.31)], arm=4)
ALEX = dict(pal=[(0.86, 0.45, 0.14), (0.96, 0.80, 0.67), (0.95, 0.95, 0.95), (0.16, 0.55, 0.25), (0.92, 0.55, 0.55), (0.72, 0.34, 0.09),
                 (0.45, 0.72, 0.33), (0.15, 0.34, 0.15), (0.45, 0.28, 0.14), (0.30, 0.30, 0.32), (0.86, 0.68, 0.56)], arm=3)
# palette slots: 0 hair, 1 skin, 2 eye white, 3 iris, 4 mouth/nose, 5 beard/hair dark, 6 shirt, 7 shirt dark/belt, 8 pants, 9 shoes, 10 skin shade
def head_col(kind, x, y, z):
    r = 7 - z
    if z == 7 or y == 7: return 0
    if y == 0:   # face
        if r <= 1: return 0
        if kind == "alex" and r == 2 and x >= 5: return 0
        if r == 4: return {1: 2, 2: 3, 5: 3, 6: 2}.get(x, 1)
        if kind == "steve":
            if r == 5 and x in (3, 4): return 4
            if r == 6 and 2 <= x <= 5: return 5
            if r == 7 and x in (2, 5): return 5
        else:
            if r == 6 and x in (3, 4): return 4
        return 1
    if x in (0, 7):
        if kind == "alex": return 0 if (r <= 3 or x == 0) else 1
        return 0 if r <= 2 else 1
    return 1
def body_col(kind, x, y, z):
    r = 11 - z
    if y == 0 and r == 0 and x in (3, 4): return 1
    if kind == "steve" and y == 0 and r == 1 and x in (3, 4): return 1
    if kind == "alex":
        if r == 9: return 7
        if r >= 10: return 8
    return 6 if (x + z) % 5 else 7
def arm_col(kind, x, y, z):
    r = 11 - z; return 6 if r <= (3 if kind == "steve" else 2) else (1 if (x + z) % 4 else 10)
def leg_col(kind, x, y, z):
    r = 11 - z; return (8 if r <= 9 else 9) if kind == "steve" else (8 if r <= 7 else 9)
def part(name, nx, ny, nz, fn, kind, mats, origin, parent, loc):
    cells = {}
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                c = fn(kind, x, y, z); cells[(x, y, z)] = (c, c, c)
    o = voxel_obj(name, cells, PX, mats, origin=origin); o.parent = parent; o.location = loc; return o
def character(name, spec, kind, loc=(0, 0, 0), yaw=0.0):
    mats = _mats(spec["pal"]); aw = spec["arm"]
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root); root.location = loc; root.rotation_euler = (0, 0, yaw)
    ch = dict(root=root)
    ch["body"] = part(name + "_body", 8, 4, 12, body_col, kind, mats, (-4 * PX, -2 * PX, 0), root, (0, 0, 12 * PX))
    ch["head"] = part(name + "_head", 8, 8, 8, head_col, kind, mats, (-4 * PX, -4 * PX, 0), root, (0, 0, 24 * PX))
    for side, sx in (("L", -1), ("R", 1)):
        ch["arm" + side] = part(name + "_arm" + side, aw, 4, 12, arm_col, kind, mats, (-aw / 2 * PX, -2 * PX, -10 * PX), root, (sx * (4 + aw / 2) * PX, 0, 22 * PX))
        ch["leg" + side] = part(name + "_leg" + side, 4, 4, 12, leg_col, kind, mats, (-2 * PX, -2 * PX, -12 * PX), root, (sx * 2 * PX, 0, 12 * PX))
    return ch
def swing(ch, f0, f1, amp=0.6, period=16, arms=True):
    for f in range(f0, f1 + 1, 2):
        a = amp * math.sin(2 * math.pi * (f - f0) / period)
        for p, s in (("legL", 1), ("legR", -1)): ch[p].rotation_euler = (a * s, 0, 0); ch[p].keyframe_insert("rotation_euler", frame=f)
        if arms:
            for p, s in (("armL", -1), ("armR", 1)): ch[p].rotation_euler = (a * s * 0.9, 0, 0); ch[p].keyframe_insert("rotation_euler", frame=f)
    for p in ("legL", "legR") + (("armL", "armR") if arms else ()):
        ch[p].rotation_euler = (0, 0, 0); ch[p].keyframe_insert("rotation_euler", frame=f1 + 4)
def move(ch, f0, f1, p0, p1, bob=True):
    r = ch["root"]; r.location = p0; r.keyframe_insert("location", frame=f0); r.location = p1; r.keyframe_insert("location", frame=f1)
def face(ch, f, yaw):
    ch["root"].rotation_euler = (0, 0, yaw); ch["root"].keyframe_insert("rotation_euler", frame=f)
def look(ch, f, yaw=0.0, pitch=0.0):
    ch["head"].rotation_euler = (pitch, 0, yaw); ch["head"].keyframe_insert("rotation_euler", frame=f)
def sit(ch):
    for p in ("legL", "legR"): ch[p].rotation_euler = (math.radians(-90), 0, 0)
    ch["root"].location = (ch["root"].location[0], ch["root"].location[1], ch["root"].location[2] - 12 * PX)
def wave(ch, f0, f1, arm="armR"):
    for f in range(f0, f1 + 1, 3):
        ch[arm].rotation_euler = (math.radians(170), 0, math.radians(25) * math.sin((f - f0) / 3)); ch[arm].keyframe_insert("rotation_euler", frame=f)
    ch[arm].rotation_euler = (0, 0, 0); ch[arm].keyframe_insert("rotation_euler", frame=f1 + 5)

# ======================= props =======================
HEART = ["0110001100", "1111011110", "1111111111", "1111111111", "0111111110", "0011111100", "0001111000", "0000110000"]
def heart_obj(name, size, emit=4):
    c = {(x, 0, 7 - r): (0, 0, 0) for r, row in enumerate(HEART) for x, ch in enumerate(row) if ch == "1"}
    return voxel_obj(name, c, size, [mat_col(name + "m", (1.0, 0.22, 0.4), emit=emit)], origin=(-5 * size, 0, 0))
def rising_heart(name, loc, f0, f1, size=0.06):
    h = heart_obj(name, size); h.rotation_euler = (0, 0, 0)
    key(h, 1, loc=loc, scale=(0.001, 0.001, 0.001)); key(h, f0, loc=loc, scale=(0.001, 0.001, 0.001))
    key(h, f0 + 8, scale=(1.2, 1.2, 1.2)); key(h, f0 + 14, scale=(1, 1, 1)); key(h, f1, loc=(loc[0], loc[1], loc[2] + 1.8), scale=(0.8, 0.8, 0.8))
    return h
def falling(name, n, area, z0, z1, size, mat, dur, drift=0.0, stretch=1.0):
    for i in range(n):
        x, y = rnd.uniform(*area[0]), rnd.uniform(*area[1])
        o = voxel_obj(f"{name}{i}", {(0, 0, 0): (0, 0, 0)}, size, [mat]); o.scale = (1, 1, stretch)
        off = rnd.randint(0, dur)
        o.location = (x, y, z0); o.keyframe_insert("location", frame=1 - off)
        o.location = (x + drift, y, z1); o.keyframe_insert("location", frame=1 - off + dur)
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
            fc.modifiers.new("CYCLES")
def ground(nx, ny, ox, oy, mats, flowers=0, gi=0, di=1):
    cells = {}
    for x in range(nx):
        for y in range(ny): cells[(ox + x, oy + y, 0)] = (gi, di, di)
    o = voxel_obj("ground", cells, 1.0, mats, origin=(0, 0, -1))
    if flowers:
        fm = [mat_col("fr", (0.95, 0.1, 0.1), rough=0.6), mat_col("fy", (1.0, 0.85, 0.05), rough=0.6), mat_col("fw", (1.0, 1.0, 1.0), rough=0.6), mat_col("fp", (0.75, 0.25, 0.95), rough=0.6)]
        fc = {}
        for _ in range(flowers):
            x, y = int(rnd.uniform(ox, ox + nx) / 0.12), int(rnd.uniform(oy, oy + ny) / 0.12)
            k = rnd.randint(0, 3); fc[(x, y, 0)] = (4, 4, 4); fc[(x, y, 1)] = (k, k, k)
        voxel_obj("flowers", fc, 0.12, fm + [mat_col("stem", (0.2, 0.55, 0.15), rough=0.7)], origin=(0, 0, 0))
    return o
def house(cells, x0, y0, w=5, d=5, h=4, wall=0, base=1, roof=2, glass=3, door=True):
    for x in range(w):
        for y in range(d):
            for z in range(h):
                edge = x in (0, w - 1) or y in (0, d - 1)
                if not edge: continue
                m = base if z == 0 else wall
                if z == 2 and (x == w // 2 or y == d // 2) and not (x in (0, w - 1) and y in (0, d - 1)): m = glass
                if door and y == 0 and x == w // 2 and z in (0, 1): continue
                cells[(x0 + x, y0 + y, z)] = (m, m, m)
    for k in range(w // 2 + 1):
        for x in range(k, w - k):
            for y in range(-1, d + 1): cells[(x0 + x, y0 + y, h + k)] = (roof, roof, roof)

# ======================= 3D lyrics that ride with the camera =======================
def lyrics(cam, col=(1.0, 0.95, 0.85), emit=0.6, y0=-0.95, dist=4.0):
    if not os.environ.get('LYR3D'):
        sh = light('AREA', (0, 0, 0), 30, (1, 1, 1), size=3); sh.parent = cam; sh.location = (0, -1.5, -2.5); return
    m = mat_col("lyr", col, emit=emit, rough=0.4)
    words = L["words"]; n = len(words)
    rows = [list(range(n))] if n <= 4 else [list(range((n + 1) // 2)), list(range((n + 1) // 2, n))]
    hgt = 0.33; gap = 0.11
    for ri, idxs in enumerate(rows):
        obs = [word_obj(words[i], "HindSiliguri-Bold.ttf", 80, hgt, 3, m, f"ly{i}") for i in idxs]
        bpy.context.view_layer.update()
        wids = [o.dimensions.x for o in obs]; tot = sum(wids) + gap * (len(obs) - 1); k = min(1.0, 3.9 / tot)
        x = -tot * k / 2
        for o, wd, i in zip(obs, wids, idxs):
            o.parent = cam; o.rotation_euler = (math.radians(-90), 0, 0)
            o.location = (x + wd * k / 2, y0 - ri * 0.43 * k, -dist); o.scale = (k, k, k); x += (wd + gap) * k
            f = F(L["ws"][i]); s = o.scale[0]
            key(o, 1, scale=(0, 0, 0)); key(o, max(2, f - 2), scale=(0, 0, 0)); key(o, f + 3, scale=(s * 1.18,) * 3); key(o, f + 7, scale=(s,) * 3)
    sh = light("AREA", (0, 0, 0), 30, (1, 1, 1), size=3); sh.parent = cam; sh.location = (0, -1.5, -2.5)

def cam_track(loc0, loc1, t0, t1, lens=32, shake=0.02):
    cam, tg = camera(loc0, loc1, t0, lens=lens, shake=shake); key(tg, 1, loc=t0); key(tg, NF, loc=t1)
    for fc in tg.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = "SINE"; kp.easing = "EASE_IN_OUT"
    return cam

GR = lambda: [mat_tex("grass", "grass"), mat_tex("dirt_side", "dirt_side")]
LEAF = lambda col=None: mat_col("pink", col, rough=0.8) if col else mat_tex("leaves", "leaves")

# ======================= scenes =======================
if SCN == 1:   # alone in a flower meadow at sunrise
    world_color((0.55, 0.72, 1.0), 0.9)
    ground(30, 24, -15, -10, GR(), flowers=500)
    bg = {}; hm = terrain_cells(bg, 50, 10, 2, 1.5, -25, 14, seed=3)
    for _ in range(9):
        x, y = rnd.randint(-24, 24), rnd.randint(14, 22); tree_cells(bg, x, y, hm[(x, y)])
    voxel_obj("hills", bg, 1.0, GR() + [mat_tex("leaves", "leaves"), mat_tex("log", "log")], origin=(0, 0, -1))
    for i in range(6): cloud(f"cl{i}", rnd.uniform(-20, 15), rnd.uniform(20, 30), rnd.uniform(8, 12), mat_col("cloud", (1, 1, 1), rough=0.9), 2)
    light("SUN", (0, 0, 10), 3.5, (1.0, 0.88, 0.7), rot=(math.radians(50), 0, math.radians(30)))
    st = character("steve", STEVE, "steve", (-4, 0, 0), math.radians(90))
    move(st, 1, NF, (-4, 0, 0), (1.5, 0, 0)); swing(st, 1, NF, 0.55, 18)
    for f, y in ((1, 0), (50, -0.3), (NF, 0.2)): look(st, f, y)
    cam = cam_track((-1.0, -3.6, 1.7), (4.2, -3.0, 1.6), (-3.6, 0, 1.3), (1.3, 0, 1.3), lens=32)
    lyrics(cam)

elif SCN == 2:   # he sees her under a pink cherry tree; she waves
    world_color((0.6, 0.75, 1.0), 0.9)
    ground(30, 24, -15, -10, GR(), flowers=450)
    tc = {}; tree_cells(tc, 4, 5, 0, li=0, wi=1, h=5); tree_cells(tc, 6, 6, 0, li=0, wi=1, h=4)
    voxel_obj("cherry", tc, 1.0, [mat_col("pinkleaf", (1.0, 0.62, 0.78), rough=0.8), mat_tex("log", "log")])
    falling("petal", 60, ((1, 9), (2, 9)), 5, 0, 0.07, mat_col("petal", (1.0, 0.7, 0.85), emit=0.3), 90, drift=1.0)
    light("SUN", (0, 0, 10), 3.5, (1.0, 0.88, 0.75), rot=(math.radians(55), 0, math.radians(-20)))
    st = character("steve", STEVE, "steve", (-2.5, -1.5, 0), math.radians(133))
    al = character("alex", ALEX, "alex", (1.9, 2.3, 0), math.radians(-47))
    move(st, 1, 60, (-2.5, -1.5, 0), (-0.6, 0.2, 0)); swing(st, 1, 60, 0.5, 18)
    look(st, 1, 0); look(st, 45, math.radians(-15), math.radians(-5)); look(al, 1, 0); look(al, 60, math.radians(10))
    wave(al, 55, 95)
    rising_heart("h1", (0.65, 1.25, 2.3), 70, NF)
    cam = cam_track((-1.6, -4.4, 1.8), (-0.6, -3.4, 1.7), (0.2, 0.6, 1.3), (1.0, 1.6, 1.4), lens=30)
    lyrics(cam)

elif SCN == 3:   # night, alone at a campfire
    world_color((0.01, 0.012, 0.04), 1)
    ground(30, 24, -15, -10, GR())
    bg = {}
    for _ in range(10): x, y = rnd.randint(-12, 12), rnd.randint(4, 12); tree_cells(bg, x, y, 0, li=0, wi=1)
    voxel_obj("trees", bg, 1.0, [mat_tex("leaves", "leaves"), mat_tex("log", "log")])
    logs = {(0, 0, 0): (0, 0, 0), (1, 0, 0): (0, 0, 0), (0, 1, 0): (0, 0, 0), (1, 1, 0): (0, 0, 0)}
    voxel_obj("logs", logs, 0.35, [mat_tex("log", "log")], origin=(0.6, 0.1, 0))
    fl = voxel_obj("fire", {(0, 0, 0): (0, 0, 0), (1, 0, 0): (0, 0, 0), (0, 1, 0): (0, 0, 0), (1, 1, 0): (0, 0, 0), (0, 0, 1): (0, 0, 0)}, 0.2, [mat_col("flame", (1.0, 0.5, 0.1), emit=25)], origin=(0.75, 0.25, 0.35))
    noise_anim(fl, "scale", 0.25, scale=4)
    fire = light("POINT", (0.95, 0.45, 0.9), 400, (1.0, 0.5, 0.15), size=0.3); noise_anim(fire.data, "energy", 160, scale=3)
    for i in range(80):
        voxel_obj(f"st{i}", {(0, 0, 0): (0, 0, 0)}, 0.08, [mat_col(f"stc{i}", (1, 1, 1), emit=rnd.uniform(3, 12))], origin=(rnd.uniform(-30, 30), rnd.uniform(20, 35), rnd.uniform(4, 20)))
    voxel_obj("moon", {(x, 0, z): (0, 0, 0) for x in range(3) for z in range(3)}, 1.0, [mat_col("moon", (0.9, 0.92, 1.0), emit=8)], origin=(-8, 30, 12))
    light("SUN", (0, 0, 10), 0.15, (0.5, 0.6, 1.0), rot=(0.7, 0.2, 0.5))
    st = character("steve", STEVE, "steve", (-0.6, -0.2, 0), math.radians(113)); sit(st)
    for f, (y, p) in ((1, (0, 0.2)), (60, (0, -0.35)), (NF, (math.radians(15), -0.4))): look(st, f, y, p)
    cam = cam_track((2.4, -2.6, 1.3), (1.4, -3.2, 1.6), (-0.3, 0.0, 0.8), (0.1, 0.1, 0.9), lens=32)
    light('AREA', (-2, -3, 3), 40, (0.55, 0.65, 1.0), look_rot((-2, -3, 3), (-0.6, -0.2, 0.6)), 3)
    lyrics(cam, col=(1.0, 0.85, 0.6))

elif SCN == 4:   # he builds a little house for his dream, block by block
    world_color((1.0, 0.7, 0.45), 0.8)
    ground(30, 24, -15, -10, GR(), flowers=250)
    hc = {}; house(hc, -1, 2, 6, 5, 4)
    keys = sorted(hc.keys(), key=lambda k: (k[2], k[0], k[1]))
    mats = [mat_tex("plank", "plank"), mat_tex("cobble", "cobble"), mat_tex("log", "log"), mat_tex("glass", "glass", rough=0.05)]
    for i, kk in enumerate(keys):
        o = voxel_obj(f"b{i}", {kk: hc[kk]}, 1.0, mats)
        anim_show(o, T0 + 0.25 + 3.3 * i / len(keys))
    light("SUN", (0, 0, 10), 3.0, (1.0, 0.75, 0.5), rot=(math.radians(60), 0, math.radians(40)))
    light("POINT", (2, 4.5, 2), 120, (1.0, 0.7, 0.3), size=0.5)
    st = character("steve", STEVE, "steve", (-2.5, 0.3, 0), math.radians(-40))
    for f in range(1, NF, 10):
        st["armR"].rotation_euler = (math.radians(-60), 0, 0); st["armR"].keyframe_insert("rotation_euler", frame=f)
        st["armR"].rotation_euler = (math.radians(-100), 0, 0); st["armR"].keyframe_insert("rotation_euler", frame=f + 5)
    look(st, 1, math.radians(20), -0.2); look(st, NF, math.radians(-20), -0.1)
    cam = cam_track((-5.5, -4.5, 3.0), (2.5, -6.0, 2.6), (0.0, 2.2, 1.4), (1.0, 3.0, 1.7), lens=30)
    lyrics(cam)

elif SCN == 5:   # alone in the rain under a street lamp
    world_color((0.02, 0.03, 0.06), 1)
    plane(60, (0, 0, 0), mat_tex("cobble", "cobble", rough=0.05), 30)
    pc = {}; lamp_post(pc, 0, 0, 0, 5)
    voxel_obj("post", pc, 1.0, [mat_col("post", (0.12, 0.12, 0.14), rough=0.4)], origin=(0.6, 1.2, 0)).scale = (0.3, 0.3, 1)
    voxel_obj("bulb", {(0, 0, 0): (0, 0, 0)}, 0.5, [mat_col("bulb", (1, 0.85, 0.55), emit=25)], origin=(0.45, 1.15, 4.6))
    light("SPOT", (0.7, 1.4, 4.4), 900, (1, 0.82, 0.55), look_rot((0.7, 1.4, 4.4), (0.4, 0.4, 0)), 0.3, math.radians(70))
    bc = {}
    for i, x in enumerate(range(-14, 14, 6)): house(bc, x, 8, 5, 4, 5, door=False)
    voxel_obj("houses", bc, 1.0, [mat_tex("stone", "stone"), mat_tex("cobble", "cobble"), mat_tex("log", "log"), mat_tex("build", "build", emit=1.5)])
    falling("rain", 260, ((-5, 5), (-3, 6)), 7, 0, 0.03, mat_col("drop", (0.7, 0.8, 1.0), emit=0.6, rough=0.1), 14, stretch=8)
    light("SUN", (0, 0, 10), 0.2, (0.5, 0.6, 1.0), rot=(0.6, 0.3, 0.4))
    st = character("steve", STEVE, "steve", (0.4, 0.4, 0), math.radians(-20))
    look(st, 1, 0, 0.35); look(st, NF, math.radians(-10), 0.45)
    cam = cam_track((-2.5, -5.5, 1.2), (-1.0, -4.0, 1.5), (0.4, 0.6, 1.2), (0.4, 0.6, 1.4), lens=34)
    lyrics(cam, col=(0.85, 0.92, 1.0))

elif SCN == 6:   # running through the village to find her
    world_color((0.9, 0.55, 0.45), 0.8)
    ground(36, 40, -18, -14, GR())
    path = {(x, y, 0): (0, 0, 0) for x in range(-1, 2) for y in range(-14, 26)}
    voxel_obj("path", path, 1.0, [mat_tex("dirt", "dirt")], origin=(0, 0, -0.98))
    bc = {}
    for y in range(-10, 24, 8):
        house(bc, -8, y, 5, 5, 4); house(bc, 4, y + 3, 5, 5, 4)
    voxel_obj("village", bc, 1.0, [mat_tex("plank", "plank"), mat_tex("cobble", "cobble"), mat_tex("log", "log"), mat_tex("glass", "glass", rough=0.05)])
    tc = {}
    for y in range(-12, 24, 6): tree_cells(tc, rnd.choice([-12, 11]), y, 0, li=0, wi=1)
    voxel_obj("trees", tc, 1.0, [mat_tex("leaves", "leaves"), mat_tex("log", "log")])
    light("SUN", (0, 0, 10), 3.0, (1.0, 0.7, 0.5), rot=(math.radians(65), 0, math.radians(160)))
    st = character("steve", STEVE, "steve", (0.5, 12, 0), math.radians(0))
    move(st, 1, NF, (0.5, 14, 0), (0.5, 2, 0)); swing(st, 1, NF, 0.95, 10)
    cam = cam_track((1.8, 3.5, 1.6), (1.8, -5.5, 1.8), (0.5, 14, 1.2), (0.5, 2, 1.2), lens=30, shake=0.035)
    lyrics(cam)

elif SCN == 7:   # they meet on a bridge at sunset
    world_color((1.0, 0.45, 0.25), 0.9)
    plane(80, (0, 0, -1.2), mat_col("water", (0.12, 0.28, 0.42), rough=0.04, metal=0.2))
    br = {(x, y, 0): (0, 0, 0) for x in range(-12, 13) for y in range(-1, 2)}
    for x in range(-12, 13, 3):
        if abs(x) > 2: br[(x, 1, 1)] = (1, 1, 1)
    voxel_obj("bridge", br, 1.0, [mat_tex("plank", "plank"), mat_tex("log", "log")], origin=(0, 0, -1))
    bank = {}; terrain_cells(bank, 10, 30, 2, 1, -24, -15, seed=2); terrain_cells(bank, 10, 30, 2, 1, 14, -15, seed=4)
    voxel_obj("banks", bank, 1.0, GR(), origin=(0, 0, -2))
    light("SUN", (0, 0, 10), 3.5, (1.0, 0.65, 0.4), rot=(math.radians(75), 0, math.radians(180)))
    st = character("steve", STEVE, "steve", (-5, 0, 0), math.radians(-90)); al = character("alex", ALEX, "alex", (5, 0, 0), math.radians(90))
    mid = int(NF * 0.6)
    move(st, 1, mid, (-5, 0, 0), (-0.55, 0, 0)); swing(st, 1, mid, 0.5, 18)
    move(al, 1, mid, (5, 0, 0), (0.55, 0, 0)); swing(al, 1, mid, 0.5, 18)
    look(st, mid, 0, -0.1); look(al, mid, 0, -0.1)
    rising_heart("h1", (0, 0, 2.1), mid + 5, NF, 0.07)
    cam = cam_track((-3.0, -8.0, 2.0), (-1.2, -4.6, 1.7), (-1.5, 0, 1.2), (0, 0, 1.4), lens=34)
    lyrics(cam, col=(1.0, 0.92, 0.8))

elif SCN == 8:   # together on a hill, hearts floating up, camera pulls back
    world_color((1.0, 0.4, 0.22), 0.85)
    cells = {}; terrain_cells(cells, 40, 30, 1, 1.2, -20, 4, seed=8)
    box(cells, -4, -4, 0, 9, 7, 3, (0, 1, 1))
    voxel_obj("hill", cells, 1.0, GR(), origin=(0, 0, -3))
    light("SUN", (0, 0, 10), 3.0, (1.0, 0.6, 0.4), rot=(math.radians(80), 0, math.radians(180)))
    st = character("steve", STEVE, "steve", (-0.4, 2.9, 0.75), math.radians(180)); sit(st)
    al = character("alex", ALEX, "alex", (0.4, 2.9, 0.75), math.radians(180)); sit(al)
    look(st, 1, 0); look(st, 30, math.radians(-40)); look(al, 1, 0); look(al, 40, math.radians(40))
    for i in range(6): rising_heart(f"h{i}", (rnd.uniform(-0.8, 0.8), 3.2, 2.0), 8 + i * 12, min(NF, 8 + i * 12 + 50), 0.05)
    cam = cam_track((1.7, 0.4, 1.5), (2.4, -2.8, 2.3), (0, 2.9, 1.0), (0, 4.5, 1.3), lens=32, shake=0.015)
    lyrics(cam, col=(1.0, 0.92, 0.85))


# ======================= "shaders" look: real sky, light rays, soft shadows, depth of field, motion blur =======================
SKY = {1: (14, 205), 2: (22, 150), 4: (9, 230), 6: (6, 175), 7: (2.5, 180), 8: (2.0, 180)}
HAZE = {1: 0.004, 2: 0.004, 3: 0.012, 4: 0.006, 5: 0.02, 6: 0.008, 7: 0.01, 8: 0.01}
def shaders():
    ee = sc.eevee
    for k_, v_ in dict(use_volumetric_lights=True, use_volumetric_shadows=True, volumetric_tile_size="8", volumetric_samples=16,
                       volumetric_end=120.0, shadow_cube_size="2048", shadow_cascade_size="4096", use_shadow_high_bitdepth=True,
                       gtao_distance=2.0, gtao_factor=1.4, bloom_intensity=0.09, bloom_threshold=0.8, bloom_radius=6.5,
                       use_ssr_refraction=True, use_motion_blur=True, motion_blur_shutter=0.45, taa_render_samples=10).items():
        setattr_safe(ee, k_, v_)
    nt = world.node_tree; bg = nt.nodes["Background"]
    if SCN in SKY:
        el, rot = SKY[SCN]
        sky = nt.nodes.new("ShaderNodeTexSky"); sky.sky_type = "NISHITA"; sky.sun_elevation = math.radians(el); sky.sun_rotation = math.radians(rot)
        sky.sun_intensity = 0.35; sky.altitude = 200; sky.air_density = 1.4; sky.dust_density = 2.5 if el < 8 else 1.0
        nt.links.new(sky.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.22
        for o in sc.objects:
            if o.type == "LIGHT" and o.data.type == "SUN":
                o.rotation_euler = (math.radians(90 - el), 0, math.radians(rot + 180)); o.data.angle = math.radians(1.5)
    volume(HAZE.get(SCN, 0.005))
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        nodes = m.node_tree.nodes; tex = [n for n in nodes if n.type == "TEX_IMAGE"]
        bsdf = nodes.get("Principled BSDF")
        if tex and bsdf:
            bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35; bump.inputs["Distance"].default_value = 0.03
            m.node_tree.links.new(tex[0].outputs[0], bump.inputs["Height"]); m.node_tree.links.new(bump.outputs[0], bsdf.inputs["Normal"])
    cam = sc.camera; cam.data.dof.use_dof = True; cam.data.dof.focus_object = cam.constraints[0].target; cam.data.dof.aperture_fstop = 7.0
if os.environ.get("SHADERS", "1") != "0": shaders()


if os.environ.get("BTS"):   # Blender solid view of the same scene from a wide orbiting camera (behind the scenes)
    import mathutils
    sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
    sh.light = "STUDIO"; sh.color_type = "RANDOM"; sh.show_cavity = True; sh.show_object_outline = True; sh.show_shadows = True
    main = sc.camera; tg = main.constraints[0].target
    cd = bpy.data.cameras.new("CV"); cd.lens = 22; cv = bpy.data.objects.new("CV", cd); sc.collection.objects.link(cv)
    con = cv.constraints.new("TRACK_TO"); con.target = tg; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    r = 7.5
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
    sc.render.use_overwrite = not os.environ.get("RESUME"); sc.render.filepath = os.path.join(OUTD, "f_####"); bpy.ops.render.render(animation=True)
print("SCENE_DONE", SCN, NF)
