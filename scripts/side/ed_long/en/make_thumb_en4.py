"""The Emperor's Diary (EN) longform thumbnails v4 — owner feedback 2026-11-11 09:30:
"v1·v2·v3 put the coin top-left as a small badge; the Korean channel never did that."
Korean method (docs/emperor/long/ep04_a.jpg, scripts/side/ed_long/thumb_cep01.py coin()): the coin is LARGE,
filling about half the left side, blended softly (screen) into the dark background, and the words sit on top of it.
Everything else stays from v3 (thumb_research.md): viewer-situation hook, white + yellow-gold, Anton, face on the right,
one small subtitle line, lower-right corner kept clear.
python3 scripts/side/ed_long/en/make_thumb_en4.py <out_dir>   (run from the repo root; fonts in ED_THUMB_FONTS: Anton.woff, Cinzel.ttf)
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

sys.path.insert(0, os.path.dirname(__file__))
import make_thumb_en3 as V3   # base(), grade(), marble() unchanged

W, H = V3.W, V3.H
FD = V3.FD
WHITE, YEL = V3.WHITE, V3.YEL
SUB = (236, 214, 170)

# name: (image, face box, lines [(text, weight, colour)], marble?, subtitle, coin (cx, cy, diameter, opacity))
V = {
    "1": ("cep1i_bury.jpeg", (0.30, 0.08, 0.52, 0.58), [("BETRAYED?", 1.0, YEL), ("DO THIS", 1.0, WHITE)], False,
          "WHAT MARCUS AURELIUS DID INSTEAD", (285, 372, 660, 0.55)),
    "2": ("c1_emp_talk2.jpeg", (0.42, 0.04, 0.62, 0.52), [("WHEN SOMEONE", 0.62, WHITE), ("BETRAYS YOU", 1.0, YEL)], False,
          "3 STOIC RULES FROM A ROMAN EMPEROR", (285, 372, 660, 0.55)),
    "3": ("cep1i_spk.jpeg", (0.42, 0.10, 0.60, 0.60), [("DON'T TAKE", 0.75, WHITE), ("REVENGE", 1.0, YEL), ("DO THIS INSTEAD", 0.52, WHITE)], True,
          "", (285, 372, 660, 0.42)),
}


def big_coin(img, cx, cy, d, op):
    """Korean thumb_cep01.coin(): soft-edged coin, screen-blended so it reads as a lit relief in the dark, not a sticker."""
    g = np.asarray(Image.open(V3.LOGO).convert("L").resize((d, d), Image.LANCZOS)).astype(np.float32) / 255
    c = Image.fromarray(np.clip(np.stack([g * 250, g * 198, g * 110], -1), 0, 255).astype(np.uint8))   # warm gold relief (Korean ep04_a tone), not grey
    m = Image.new("L", (d, d), 0); ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=255); m = m.filter(ImageFilter.GaussianBlur(d // 14))
    lay = Image.new("RGB", (W, H), (0, 0, 0)); lay.paste(c, (cx - d // 2, cy - d // 2), m)
    base = img.convert("RGB")
    return Image.blend(base, ImageChops.screen(base, lay), op)


def words(img, lines, sub, yc=0.52):
    """v3 words (Anton, two sizes, soft shadow) + one small subtitle line in Cinzel under them."""
    fpath = os.path.join(FD, "Anton.woff"); x0 = int(W * 0.055)
    d0 = ImageDraw.Draw(img); base_size = 168
    k = min(1.0, min(W * 0.50 / d0.textlength(t, font=ImageFont.truetype(fpath, int(base_size * wgt))) for t, wgt, _ in lines))
    hs = [int(base_size * wgt * k) for _, wgt, _ in lines]; total = sum(int(h * 1.04) for h in hs) + (70 if sub else 0)
    y = int(H * yc - total / 2); pos = []
    for (t, wgt, col), sz in zip(lines, hs):
        pos.append((t, ImageFont.truetype(fpath, sz), y, col)); y += int(sz * 1.04)
    ss = 30
    while sub and ss > 18:
        sf = ImageFont.truetype(os.path.join(FD, "Cinzel.ttf"), ss); sf.set_variation_by_axes([700])
        if d0.textlength(sub, font=sf) + 2 * len(sub) <= W * 0.47: break
        ss -= 1
    sf = ImageFont.truetype(os.path.join(FD, "Cinzel.ttf"), ss); sf.set_variation_by_axes([700])
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for t, f, yy, _ in pos: sd.text((x0 + 5, yy + 8), t, font=f, fill=(0, 0, 0, 240))
    if sub: sd.text((x0 + 3, y + 40), sub, font=sf, fill=(0, 0, 0, 230))
    img = Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    for t, f, yy, col in pos: d.text((x0, yy), t, font=f, fill=col + (255,), stroke_width=4, stroke_fill=(12, 10, 8, 255))
    if sub:
        x = x0
        for ch in sub: d.text((x, y + 36), ch, font=sf, fill=SUB + (255,)); x += d.textlength(ch, font=sf) + 2   # letter-spaced
    return img


def main(out):
    os.makedirs(out, exist_ok=True); tiles = []
    for k, (src, face, lines, mb, sub, (cx, cy, d, op)) in V.items():
        b = V3.base(src, face, 0.66)
        if mb: b = V3.marble(b)
        img = V3.grade(b, YEL)
        img = big_coin(img, cx, cy, d, op)
        img = words(img, lines, sub).convert("RGB")
        p = os.path.join(out, f"thumb_v4_{k}.png"); img.save(p, optimize=True)
        img.resize((320, 180), Image.LANCZOS).save(os.path.join(out, f"thumb_v4_{k}_mobile320.png"))
        tiles.append(img); print(k, p, os.path.getsize(p) // 1024, "KB")
    # one review sheet: three at half size + phone-size row
    sheet = Image.new("RGB", (W // 2 * 3 + 40, H // 2 + 20 + 190), (18, 18, 18))
    for i, t in enumerate(tiles):
        sheet.paste(t.resize((W // 2, H // 2), Image.LANCZOS), (10 + i * (W // 2 + 10), 10))
        sheet.paste(t.resize((320, 180), Image.LANCZOS), (10 + i * (W // 2 + 10), H // 2 + 20))
    sheet.save(os.path.join(out, "thumb_v4_sheet.jpg"), quality=90)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "_thumbs4")
