"""What Korea Says — 진행자(까치) 동작 이미지 배경 제거 (2026-10-27)
social/side/gen/h_*.(jpeg|png) → social/side/gen/cut/h_*.png (투명 배경, 몸통 안쪽은 꽉 채움)
rembg(isnet) 결과는 크림색 배와 크림색 배경을 헷갈려 반투명이 생긴다 → 외곽선 안쪽 구멍을 메우고 색은 원본 그대로 쓴다
"""
import glob, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GEN = os.path.join(ROOT, "social", "side", "gen"); CUT = os.path.join(GEN, "cut")


def cut(src, dst, session):
    from rembg import remove
    im = Image.open(src).convert("RGB")
    a = np.array(remove(im, session=session))[..., 3].astype(float)
    a[a < 12] = 0
    m = nd.binary_closing(a > 40, iterations=3)
    fill = nd.binary_fill_holes(m)
    lab, n = nd.label(fill)
    if n:
        keep = lab == (np.argmax(nd.sum(fill, lab, range(1, n + 1))) + 1)
        a = a * keep; fill = fill & keep
    inner = nd.binary_erosion(fill, iterations=3)
    a = np.where(inner, 255, a)
    out = np.dstack([np.array(im), a.clip(0, 255).astype(np.uint8)])
    img = Image.fromarray(out, "RGBA"); img = img.crop(img.getbbox())
    img.save(dst); return img.size


def main(names=None):
    from rembg import new_session
    os.makedirs(CUT, exist_ok=True); s = new_session("isnet-general-use")
    for f in sorted(glob.glob(os.path.join(GEN, "h_*.*")) + glob.glob(os.path.join(GEN, "c1_*.*"))):
        stem, ext = os.path.splitext(os.path.basename(f))
        if ext.lower() not in (".png", ".jpg", ".jpeg", ".webp"): continue
        if names and stem not in names: continue
        dst = os.path.join(CUT, stem + ".png")
        if os.path.exists(dst): continue
        print(stem, cut(f, dst, s), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
