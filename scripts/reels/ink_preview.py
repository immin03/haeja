"""잉크 노트 미리보기 (음성 없이 글자 수로 길이를 어림해 스틸·짧은 영상)
python3 scripts/reels/ink_preview.py <spec.json> <out_dir> [--every 1.0] [--video]
"""
import argparse, json, os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import engine as E
import inkworld
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("out"); ap.add_argument("--every", type=float, default=1.0)
ap.add_argument("--video", action="store_true"); ap.add_argument("--t", default="")
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
spec = json.load(open(a.spec, encoding="utf-8")); spec["world"] = "ink"
E.WORLD = "ink"; E.YT = True; E.GL_ON = False; E.YT_BANNER = spec.get("banner")
scenes, total = E.plan_estimate(spec)
inkworld.prep(E, scenes)
print("길이(어림)", round(total, 1), "초 · 멈춘 구간", inkworld.audit(scenes, total))
for s in scenes:
    print(f"  {s['start']:6.1f} {s['sc']['type']:9s} 문장 {len(s['L'])} · 비트 {len(s['_ink']['beats'])}")
    for a_, b_ in inkworld.overlaps(s): print(f"      ⚠ 겹침: {a_} ↔ {b_}")
if a.video:
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
                          "-vf", "scale=540:960", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", os.path.join(a.out, "preview.mp4")], stdin=subprocess.PIPE)
    for i in range(int(total * 30)): p.stdin.write(E.frame(i / 30, scenes, total).convert("RGB").tobytes())
    p.stdin.close(); p.wait(); sys.exit()
ts = [float(x) for x in a.t.split(",")] if a.t else [round(x * a.every + .3, 2) for x in range(int(total / a.every))]
ims = []
for t in ts:
    im = E.frame(t, scenes, total).convert("RGB"); ims.append((t, im))
cols = 6; sw, sh = 270, 480; rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * sw, rows * sh), "black")
from PIL import ImageDraw
for i, (t, im) in enumerate(ims):
    sm = im.resize((sw, sh)); ImageDraw.Draw(sm).text((6, 4), f"{t:.1f}", fill=(255, 80, 80))
    sheet.paste(sm, ((i % cols) * sw, (i // cols) * sh))
sheet.save(os.path.join(a.out, "sheet.jpg"), quality=80)
if len(ims) <= 3:
    for t, im in ims: im.save(os.path.join(a.out, f"f_{t:.1f}.jpg"), quality=85)
print(os.path.join(a.out, "sheet.jpg"))
