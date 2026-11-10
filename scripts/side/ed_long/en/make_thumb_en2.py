"""The Emperor's Diary (EN) longform thumbnails v2 — US-market standard (PACKAGING_EN.md, owner feedback 2026-11-11).
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
V = {
    "1": ("cep1i_spk.jpeg", (0.42, 0.10, 0.60, 0.60), ["WHEN THEY", "BETRAY YOU"], 1, TEAL, 0.64),
    "2": ("c1_emp_talk2.jpeg", (0.42, 0.04, 0.62, 0.52), ["THE PERFECT", "REVENGE"], 1, GOLD, 0.66),
    "3": ("cep1i_bury.jpeg", (0.30, 0.08, 0.52, 0.58), ["BURN", "THEIR NAMES"], 0, ORANGE, 0.66),
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


def words(img, lines, hi, accent):
    fpath = os.path.join(FD, "Anton.woff"); x0 = int(W * 0.055); y = int(H * 0.25)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pos = []
    d = ImageDraw.Draw(lay)
    for i, s in enumerate(lines):
        size = 170
        while d.textlength(s, font=ImageFont.truetype(fpath, size)) > W * 0.50: size -= 4
        f = ImageFont.truetype(fpath, size); pos.append((s, f, y, i == hi)); y += int(size * 1.02)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for s, f, yy, _ in pos: sd.text((x0 + 5, yy + 8), s, font=f, fill=(0, 0, 0, 240))
    img = Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    for s, f, yy, h in pos: d.text((x0, yy), s, font=f, fill=(accent if h else WHITE) + (255,), stroke_width=4, stroke_fill=(12, 10, 8, 255))
    s, f, yy, _ = pos[-1]; return img, d.textbbox((x0, yy), s, font=f)[3]


def main(out):
    os.makedirs(out, exist_ok=True)
    for k, (src, face, lines, hi, acc, share) in V.items():
        img = grade(base(src, face, share), acc)
        img, y_end = words(img, lines, hi, acc)
        c = coin(112); gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([int(W * 0.055) - 14, int(H * 0.05) - 14, int(W * 0.055) + 126, int(H * 0.05) + 126], fill=(236, 192, 112, 70)); img = Image.alpha_composite(img, gl.filter(ImageFilter.GaussianBlur(14))); img.alpha_composite(c, (int(W * 0.055), int(H * 0.05)))                 # brand mark, top-left
        d = ImageDraw.Draw(img); d.rectangle([int(W * 0.055), y_end + 18, int(W * 0.055) + 150, y_end + 28], fill=acc + (255,))   # single accent cue
        img = img.convert("RGB"); p = os.path.join(out, f"thumb_v2_{k}.png"); img.save(p, optimize=True)
        img.resize((320, 180), Image.LANCZOS).save(os.path.join(out, f"thumb_v2_{k}_mobile320.png"))
        print(k, p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "_thumbs2")
