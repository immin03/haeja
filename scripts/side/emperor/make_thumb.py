"""첫 화면(훅) 썸네일: python3 make_thumb.py spec.json out.jpg [프레임초]
유튜브 맞춤 썸네일 = 릴스 표지 = 쓰레드 사진 = 틱톡 커버 (2026-11-02 확정 양식)"""
import sys, json, numpy as np
from PIL import Image
import render_ed as R
spec = json.load(open(sys.argv[1])); out = sys.argv[2]; ts = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
c = spec["cuts"][0]
n = int(ts * R.FPS) + 1
fr = R.kb_frames(c["img"], max(n, 2), c.get("move", "in"), c.get("amt", 0.10)) if c.get("img") else R.read_frames(c["v"], max(n, 2), c.get("speed", 1.0))
base = fr[n - 1].astype(np.float32)
fx = spec.get("fx")
if fx:
    yy, xx = np.mgrid[0:R.H, 0:R.W]; r = np.sqrt(((xx - R.W / 2) / (R.W / 2)) ** 2 + ((yy - R.H * 0.52) / (R.H / 2)) ** 2)
    base = base * (1 - fx.get("vignette", 0.35) * np.clip((r - 0.45) / 0.75, 0, 1) ** 1.6)[..., None]
img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
R.top_shade(img, strength=c.get("shade", 200), h=c.get("shade_h", 980))
R.draw_block(img, [dict(b, t0=-1, t1=999) for b in c["texts"]], 1.0, top=c.get("top", 250))
R.watermark(img)
img.convert("RGB").save(out, quality=92)
print(out)
