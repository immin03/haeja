"""The Emperor's Diary (EN) longform thumbnails — US packaging (PACKAGING_EN.md). 1280x720 PNG < 2MB.
Layout: one face on the right ~1/3 of the frame, 2-line heavy sans text on the left (shadow + dark backing), gold/orange accent bar,
lower-right corner kept clear for the duration stamp, everything inside a 6% safe margin.
python3 make_thumb_en.py <out_dir>    (fonts: ED_THUMB_FONTS dir with Anton.woff)
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
GEN = os.path.join(ROOT, "social/side/gen")
FD = os.environ.get("ED_THUMB_FONTS", "/root/fonts")
W, H = 1280, 720
GOLD = (236, 190, 92); ORANGE = (255, 140, 40); WHITE = (250, 246, 236)

# variant: (image, face box in source as fractions [x0,y0,x1,y1], text lines, highlighted line index)
V = {
    "A": ("c1_emp_talk.jpeg", (0.36, 0.08, 0.64, 0.62), ["THE PERFECT", "REVENGE"], 1),     # emperor face + text
    "B": ("cep1i_casp.jpeg", (0.40, 0.02, 0.60, 0.50), ["THE PERFECT", "REVENGE"], 1),      # betrayer's face, same text
    "C": ("c1_emp_talk.jpeg", (0.36, 0.08, 0.64, 0.62), ["HE BURNED", "THEIR NAMES"], 1),  # same image, different wording
}


def place(src, face):
    im = Image.open(os.path.join(GEN, src)).convert("RGB"); sw, sh = im.size
    fx0, fy0, fx1, fy1 = face[0] * sw, face[1] * sh, face[2] * sw, face[3] * sh
    fh = fy1 - fy0
    s = (H * 0.50) / fh                     # face height ~56% of frame height -> face area ~1/4-1/3 of frame
    cx, cy = (fx0 + fx1) / 2 * s, (fy0 + fy1) / 2 * s
    tx, ty = W * 0.75, H * 0.47             # face centre on the right, upper-middle (lower-right stays dark)
    s = max(s, (tx + 10) / ((fx0 + fx1) / 2), (W - tx + 10) / (sw - (fx0 + fx1) / 2), (ty + 10) / ((fy0 + fy1) / 2), (H - ty + 10) / (sh - (fy0 + fy1) / 2))   # always cover the frame
    cx, cy = (fx0 + fx1) / 2 * s, (fy0 + fy1) / 2 * s
    im = im.resize((int(sw * s), int(sh * s)), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), (8, 8, 10)); canvas.paste(im, (int(tx - cx), int(ty - cy)))
    return canvas


def grade(img):
    img = ImageEnhance.Contrast(img).enhance(1.18); img = ImageEnhance.Color(img).enhance(1.08)
    a = np.asarray(img).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    left = np.clip(1.0 - (xx / W - 0.30) / 0.30, 0, 1) * 0.85                       # dark backing behind the text (left)
    br = np.clip((xx / W - 0.72) / 0.28, 0, 1) * np.clip((yy / H - 0.70) / 0.30, 0, 1) * 0.75   # lower-right clear and dark
    vig = np.clip(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2 - 0.55, 0, 1) * 0.5
    k = 1 - np.clip(left + br + vig, 0, 0.9)
    a = a * k[..., None]
    a[..., 0] *= 0.96; a[..., 2] *= 0.92                                                # slight teal-shadow / warm-light split stays natural
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def text(img, lines, hi):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(os.path.join(FD, "Anton.woff"), 150)
    x0, y = int(W * 0.06), int(H * 0.17)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    pos = []
    for i, s in enumerate(lines):
        size = 150
        while ld.textlength(s, font=ImageFont.truetype(os.path.join(FD, "Anton.woff"), size)) > W * 0.47: size -= 4
        fn = ImageFont.truetype(os.path.join(FD, "Anton.woff"), size)
        pos.append((s, fn, y, i == hi)); y += int(size * 1.08)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for s, fn, yy, _ in pos: sd.text((x0 + 6, yy + 8), s, font=fn, fill=(0, 0, 0, 230))
    sh = sh.filter(ImageFilter.GaussianBlur(9)); img = Image.alpha_composite(img.convert("RGBA"), sh)
    d = ImageDraw.Draw(img)
    for s, fn, yy, h in pos:
        d.text((x0, yy), s, font=fn, fill=(GOLD if h else WHITE) + (255,), stroke_width=3, stroke_fill=(20, 14, 8, 255))
    bb = d.textbbox((x0, pos[-1][2]), pos[-1][0], font=pos[-1][1]); bar_y = bb[3] + 22
    d.rectangle([x0, bar_y, x0 + 220, bar_y + 12], fill=ORANGE + (255,))                 # one accent cue
    return img.convert("RGB")


def main(out):
    os.makedirs(out, exist_ok=True)
    for k, (src, face, lines, hi) in V.items():
        img = text(grade(place(src, face)), lines, hi)
        p = os.path.join(out, f"cine_ep01_en_thumb_{k}.png"); img.save(p, optimize=True)
        img.resize((360, 202), Image.LANCZOS).save(os.path.join(out, f"_phone_{k}.png"))
        print(k, p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "_thumbs")
