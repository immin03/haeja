"""The Emperor's Diary (EN) longform thumbnails v3 (round 2: grounded in samples/round2/thumb_research.md — viewer-situation hook, white + yellow-gold, 4-7 words in two sizes)
Based on v2 — US-market standard (PACKAGING_EN.md, owner feedback 2026-11-11).
Emotional close-up face filling ~1/3 of the frame on the right, 3-4 heavy words on the left (Anton), dark cinematic grade,
ONE accent colour per thumbnail, coin emblem as a small brand mark (top-left), lower-right corner kept clear.
python3 make_thumb_en2.py <out_dir>   env ED_THUMB_FONTS (Anton.woff)
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
GEN = os.path.join(ROOT, "social/side/gen"); LOGO = os.path.join(ROOT, "docs/emperor/profile_final.png")
FD = os.environ.get("ED_THUMB_FONTS", "/root/fonts")
W, H = 1280, 720
WHITE = (250, 247, 240)
GOLD = (245, 196, 82); TEAL = (86, 214, 214); ORANGE = (255, 138, 36)

# name: (image, face box [x0,y0,x1,y1] in source fractions (forehead..chin), lines, accent line index, accent colour, face height share)
YEL = (255, 206, 46)
# name: (image, face box, [(text, size_weight, colour)], marble?)
V = {
    "1": ("cep1i_bury.jpeg", (0.30, 0.08, 0.52, 0.58), [("BETRAYED?", 1.0, YEL), ("DO THIS", 1.0, WHITE)], False),
    "2": ("c1_emp_talk2.jpeg", (0.42, 0.04, 0.62, 0.52), [("WHEN SOMEONE", 0.62, WHITE), ("BETRAYS YOU", 1.0, YEL)], False),
    "3": ("cep1i_spk.jpeg", (0.42, 0.10, 0.60, 0.60), [("DON'T TAKE", 0.75, WHITE), ("REVENGE", 1.0, YEL), ("DO THIS INSTEAD", 0.52, WHITE)], True),
}


def coin(size):
    c = Image.open(LOGO).convert("L").resize((size, size), Image.LANCZOS); a = np.asarray(c).astype(np.float32) / 255
    rgb = np.stack([a * 236, a * 192, a * 112], -1)
    yy, xx = np.mgrid[0:size, 0:size]; m = ((xx - size / 2) ** 2 + (yy - size / 2) ** 2) <= (size / 2 - 1) ** 2
    alpha = np.clip((a - 0.08) * 1.6, 0, 1) * 255 * m
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8), "RGBA")


def base(src, face, share):
    im = Image.open(os.path.join(GEN, src)).convert("RGB"); sw, sh = im.size
    fx0, fy0, fx1, fy1 = face[0] * sw, face[1] * sh, face[2] * sw, face[3] * sh
    s = (H * share) / (fy1 - fy0)
    im = im.resize((int(sw * s), int(sh * s)), Image.LANCZOS)
    cx, cy = (fx0 + fx1) / 2 * s, (fy0 + fy1) / 2 * s
    tx, ty = W * 0.735, H * 0.47
    bg = ImageEnhance.Brightness(Image.open(os.path.join(GEN, src)).convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(30))).enhance(0.35)
    m = Image.new("L", im.size, 255); md = ImageDraw.Draw(m)
    for i in range(70): md.rectangle([i, i, im.size[0] - 1 - i, im.size[1] - 1 - i], outline=int(255 * i / 70))
    bg.paste(im, (int(tx - cx), int(ty - cy)), m)
    return bg


def grade(img, accent):
    img = ImageEnhance.Contrast(img).enhance(1.22); img = ImageEnhance.Color(img).enhance(1.05)
    a = np.asarray(img).astype(np.float32); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    left = np.clip(1.0 - (xx / W - 0.30) / 0.28, 0, 1) * 0.82                                   # dark side for the words
    br = np.clip((xx / W - 0.80) / 0.20, 0, 1) * np.clip((yy / H - 0.80) / 0.20, 0, 1) * 0.85     # lower-right clear
    vig = np.clip(((xx - W * 0.6) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2 - 0.5, 0, 1) * 0.55
    a = a * (1 - np.clip(left + br + vig, 0, 0.92))[..., None]
    rim = np.exp(-(((xx - W * 0.86) / (W * 0.16)) ** 2 + ((yy - H * 0.30) / (H * 0.35)) ** 2))[..., None] * np.array(accent, np.float32) * 0.16   # faint accent rim light
    return Image.fromarray(np.clip(a + rim, 0, 255).astype(np.uint8))


def words(img, lines):
    fpath = os.path.join(FD, "Anton.woff"); x0 = int(W * 0.055)
    d0 = ImageDraw.Draw(img); pos = []; base_size = 168
    # common scale so the widest weighted line fits 50% of the width
    k = min(1.0, min(W * 0.50 / d0.textlength(t, font=ImageFont.truetype(fpath, int(base_size * wgt))) for t, wgt, _ in lines))
    hs = [int(base_size * wgt * k) for _, wgt, _ in lines]; total = sum(int(h * 1.04) for h in hs)
    y = int(H * 0.53 - total / 2)
    for (t, wgt, col), sz in zip(lines, hs):
        f = ImageFont.truetype(fpath, sz); pos.append((t, f, y, col)); y += int(sz * 1.04)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for t, f, yy, _ in pos: sd.text((x0 + 5, yy + 8), t, font=f, fill=(0, 0, 0, 240))
    img = Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    for t, f, yy, col in pos: d.text((x0, yy), t, font=f, fill=col + (255,), stroke_width=4, stroke_fill=(12, 10, 8, 255))
    t, f, yy, _ = pos[-1]; return img, d.textbbox((x0, yy), t, font=f)[3]


def marble(img):
    """classical-bust look (8 of 12 top thumbnails use a marble bust): desaturate + cool stone tone, keep contrast"""
    g = ImageEnhance.Color(img).enhance(0.0); a = np.asarray(g).astype(np.float32) * np.array([1.02, 1.0, 0.97])
    return Image.fromarray(np.clip(a * 1.05, 0, 255).astype(np.uint8))


def main(out):
    os.makedirs(out, exist_ok=True)
    for k, (src, face, lines, mb) in V.items():
        b = base(src, face, 0.66)
        if mb: b = marble(b)
        img = grade(b, (255, 206, 46))
        img, y_end = words(img, lines)
        c = coin(112); gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([int(W * 0.055) - 14, int(H * 0.05) - 14, int(W * 0.055) + 126, int(H * 0.05) + 126], fill=(236, 192, 112, 70)); img = Image.alpha_composite(img, gl.filter(ImageFilter.GaussianBlur(14))); img.alpha_composite(c, (int(W * 0.055), int(H * 0.05)))
        img = img.convert("RGB"); p = os.path.join(out, f"thumb_v3_{k}.png"); img.save(p, optimize=True)
        img.resize((320, 180), Image.LANCZOS).save(os.path.join(out, f"thumb_v3_{k}_mobile320.png"))
        print(k, p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "_thumbs2")
