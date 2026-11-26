"""Run inside Blender:  blender -b -P render_all_pc.py
Renders all 9 scenes with Cycles on your graphics card, then builds the final MP4 with the music.
Options (environment variables): RES=1080  SAMPLES=128  ENGINE=CYCLES
"""
import bpy, os, sys, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get("RES", "1080")
env = dict(os.environ); env.setdefault("ENGINE", "CYCLES"); env.setdefault("SAMPLES", "128")
blender = bpy.app.binary_path
for k in range(9):
    out = os.path.join(HERE, "renders", f"out_{k}")
    if os.path.isdir(out) and os.path.exists(os.path.join(out, "DONE")):
        print(f"scene {k} already rendered, skipping"); continue
    t = time.time(); print(f"\n=== rendering scene {k} of 8 ===", flush=True)
    r = subprocess.run([blender, "-b", "--factory-startup", "-P", os.path.join(HERE, "scenes.py"), "--", str(k), out, RES], env=env)
    if r.returncode != 0: sys.exit(f"scene {k} failed")
    open(os.path.join(out, "DONE"), "w").write(str(time.time() - t))
    print(f"scene {k} done in {int(time.time() - t)} s", flush=True)
print("\n=== building the video ===", flush=True)
subprocess.run([blender, "-b", "--factory-startup", "-P", os.path.join(HERE, "make_video.py")], env=env, check=True)
if os.environ.get("BTS_PART", "1") != "0":
    print("\n=== behind the scenes: Blender views ===", flush=True)
    benv = dict(env); benv["BTS"] = "1"
    for k in range(1, 9):
        out = os.path.join(HERE, "renders", f"view_{k}")
        if os.path.exists(os.path.join(out, "DONE")): continue
        subprocess.run([blender, "-b", "--factory-startup", "-P", os.path.join(HERE, "scenes.py"), "--", str(k), out, RES], env=benv, check=True)
        open(os.path.join(out, "DONE"), "w").write("1")
    subprocess.run([blender, "-b", "--factory-startup", "-P", os.path.join(HERE, "make_bts.py")], env=env, check=True)
    print("\nFINISHED: Shudhu_Tomake_3D_PC.mp4 and Shudhu_Tomake_3D_PC_BehindTheScenes.mp4", flush=True)
else:
    print("\nFINISHED: Shudhu_Tomake_3D_PC.mp4", flush=True)
