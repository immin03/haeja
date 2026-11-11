"""The Emperor's Diary (EN) ending card v2 (owner round 2, 2026-11-11): compact brand at the top, empty space for YouTube end-screen elements.
Font system (a) Cinzel + EB Garamond (approved). Ending text A. Outro length 18 s (YouTube end screen max 20 s).
Slots (1920x1080, all inside a 5% safe margin):
  video L : x 150-750,  y 560-898  (600x338, 16:9, 31% of width)
  video R : x 1170-1770, y 560-898
  subscribe circle: centre (960, 729), diameter 200
python3 endcard_v2.py <out_dir>  -> endcard_v2_clean.png, endcard_v2_guide.png
"""
import os, sys, json
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import type_samples as T

SLOTS = {"video_left": (150, 560, 750, 898), "video_right": (1170, 560, 1770, 898), "subscribe": (860, 629, 1060, 829)}
OUTRO_SEC = 18.0


def card(guide=False):
    S = T.SYSTEMS["a_epic"]; W, H = T.W, T.H
    img = T.warm()
    coin = T.M.coin_gold(T.LOGO); c = Image.fromarray(coin, "RGBA").resize((112, 112), Image.LANCZOS)
    img = img.convert("RGBA"); img.alpha_composite(c, (W // 2 - 56, 70)); img = img.convert("RGB")
    fs = T.F(S["slogan"][0], 52); fb = T.F(S["brand"][0], 30); fsm = T.F(S["small"][0], 33)
    img, _ = T.put(img, W / 2, 196, "Think like an emperor, every night.", fs, T.IVORY, shadow=0.4)
    img, _ = T.put(img, W / 2, 270, "THE EMPEROR’S DIARY", fb, T.GOLD, track=S["brand"][2], shadow=0)
    d = ImageDraw.Draw(img); txt = T.ENDING["A"]["screen"]
    lines = T.wrap(d, txt, fsm, 1300); lh = int(fsm.size * 1.38)
    for i, s in enumerate(lines): img, _ = T.put(img, W / 2, 342 + i * lh, s, fsm, T.DIM, shadow=0)
    d = ImageDraw.Draw(img); y = 342 + lh * len(lines) + 30
    d.line([(W / 2 - 50, y), (W / 2 + 50, y)], fill=T.GOLD, width=1)
    if guide:
        fl = T.F("Inter-SemiBold.ttf", 26)
        for k, (x0, y0, x1, y1) in SLOTS.items():
            col = (90, 200, 220)
            if k == "subscribe": d.ellipse([x0, y0, x1, y1], outline=col, width=3)
            else:
                for xx in range(x0, x1, 24): d.line([(xx, y0), (min(xx + 12, x1), y0)], fill=col, width=3); d.line([(xx, y1), (min(xx + 12, x1), y1)], fill=col, width=3)
                for yy in range(y0, y1, 24): d.line([(x0, yy), (x0, min(yy + 12, y1))], fill=col, width=3); d.line([(x1, yy), (x1, min(yy + 12, y1))], fill=col, width=3)
            lab = {"video_left": "VIDEO (best for viewer)", "video_right": "VIDEO (playlist / latest)", "subscribe": "SUBSCRIBE"}[k]
            d.text(((x0 + x1) / 2, (y0 + y1) / 2), lab, font=fl, fill=col, anchor="mm")
        m = int(W * 0.05); mh = int(H * 0.05)
        d.rectangle([m, mh, W - m, H - mh], outline=(200, 90, 90), width=1)
        d.text((m + 8, H - mh - 34), f"5% safe area · outro {OUTRO_SEC:.0f} s (end screen max 20 s)", font=fl, fill=(200, 90, 90))
    return img


if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    card(False).save(os.path.join(out, "endcard_v2_clean.png")); card(True).save(os.path.join(out, "endcard_v2_guide.png"))
    json.dump({"slots_px_1920x1080": SLOTS, "outro_sec": OUTRO_SEC, "text": "A"}, open(os.path.join(out, "endcard_v2_slots.json"), "w"), indent=1)
    print("ok")
