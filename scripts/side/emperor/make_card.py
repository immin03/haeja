"""황제의 일기 카드뉴스 (인스타 캐러셀 · 틱톡 사진) 렌더러 — 2026-11-03
사용: python3 make_card.py card_spec.json 출력폴더
→ 출력폴더/<id>_01.jpg … (1080×1350, 4:5). 인스타·틱톡 공통.

spec = {
 "id": "c261103", "bg": "social/side/gen/ed06_forum.jpeg",
 "cover": {"kicker": "마르쿠스 아우렐리우스 『명상록』", "title": ["화가 치밀 때", "로마 황제가", "일기에 쓴 5줄"], "img": "..."},
 "items": [{"head": "…", "quote": ["…"], "body": ["…"], "src": "6권 6절", "img": "..."}],
 "end": {"kicker": "오늘 밤 할 일", "lines": ["…"], "img": "..."}
}
"""
import sys, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350
F = "/root/fonts/"
IVORY = (242, 235, 221); GOLD = (214, 196, 160); DIM = (176, 164, 144)
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
X0 = 96


def hf(size, wght=600):
    f = ImageFont.truetype(F + "Hahmlet[wght].ttf", size)
    try: f.set_variation_by_axes([wght])
    except Exception: pass
    return f


def pf(size): return ImageFont.truetype(F + "Pretendard-SemiBold.otf", size)
def cf(size): return ImageFont.truetype(F + "CormorantSC-SemiBold.ttf", size)


def cover_crop(path, blur=0, dark=0.0):
    im = Image.open(path).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s + 1), int(im.height * s + 1)), Image.LANCZOS)
    l = (im.width - W) // 2; t = int((im.height - H) * 0.45)
    im = im.crop((l, t, l + W, t + H))
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(im).astype(np.float32) * (1 - dark)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def grad(img, top=0, bottom=0, top_h=760, bottom_h=520):
    m = np.zeros((H, W), np.uint8)
    if top: m[:top_h] = np.maximum(m[:top_h], np.linspace(top, 0, top_h).astype(np.uint8)[:, None])
    if bottom: m[H - bottom_h:] = np.maximum(m[H - bottom_h:], np.linspace(0, bottom, bottom_h).astype(np.uint8)[:, None])
    sh = Image.new("RGBA", (W, H), (8, 7, 6, 0)); sh.putalpha(Image.fromarray(m)); img.alpha_composite(sh)


def text(d, xy, s, f, col, shadow=150):
    x, y = xy
    if shadow: d.text((x + 2, y + 3), s, font=f, fill=(0, 0, 0, shadow))
    d.text((x, y), s, font=f, fill=col)


def centered(d, y, s, f, col, shadow=120):
    w = d.textlength(s, font=f); text(d, ((W - w) / 2, y), s, f, col, shadow)


def footer(d, page, total):
    f = cf(30); s = "THE EMPEROR'S DIARY"; w = d.textlength(s, font=f)
    d.text(((W - w) / 2, H - 92), s, font=f, fill=(255, 255, 255, 150))
    if page:
        n = f"{page} / {total}"; fn = pf(28); w2 = d.textlength(n, font=fn)
        d.text((W - X0 - w2, H - 90), n, font=fn, fill=DIM + (200,))


def slide_cover(c, total):
    img = cover_crop(c["img"], dark=0.12); grad(img, top=245, bottom=200, top_h=1000)
    d = ImageDraw.Draw(img)
    y = 150
    text(d, (X0, y), c["kicker"], pf(44), GOLD + (255,)); y += 96
    f = hf(c.get("size", 110))
    for ln in c["title"]:
        text(d, (X0, y), ln, f, IVORY + (255,)); y += int(f.size * 1.24)
    if c.get("sub"):
        y += 20; text(d, (X0, y), c["sub"], pf(40), GOLD + (255,), 220)
    s = "넘겨서 보세요  →"; fs = pf(36); w = d.textlength(s, font=fs)
    text(d, (W - X0 - w, H - 180), s, fs, IVORY + (230,))
    footer(d, 0, total)
    return img


def wrap_check(d, lines, f, maxw, where):
    for ln in lines:
        if d.textlength(ln, font=f) > maxw: raise SystemExit(f"줄이 너무 김 ({where}): {ln}")


def slide_item(it, i, total):
    img = cover_crop(it["img"], blur=6, dark=0.58); grad(img, top=90, bottom=150)
    d = ImageDraw.Draw(img); maxw = W - 2 * X0
    fh = hf(74); fq = hf(50, 500); qlh = int(50 * 1.5); fb = pf(42); blh = int(42 * 1.55)
    wrap_check(d, it["head"], fh, maxw, "head"); wrap_check(d, it["quote"], fq, maxw - 40, "quote"); wrap_check(d, it.get("body", []), fb, maxw, "body")
    hgt = 140 + len(it["head"]) * int(74 * 1.3) + 46 + len(it["quote"]) * qlh + 8 + 84 + len(it.get("body", [])) * blh
    y = max(120, int((H - 60 - hgt) / 2) - 20)
    text(d, (X0, y), ROMAN[i], cf(96), GOLD + (255,)); y += 140
    for ln in it["head"]:
        text(d, (X0, y), ln, fh, IVORY + (255,)); y += int(74 * 1.3)
    y += 46; qy = y
    for ln in it["quote"]:
        text(d, (X0 + 40, y), ln, fq, GOLD + (255,), 120); y += qlh
    d.rectangle([X0, qy + 8, X0 + 6, y - 14], fill=GOLD + (255,))
    y += 8; text(d, (X0 + 40, y), "『명상록』 " + it["src"], pf(32), DIM + (255,), 0); y += 84
    for ln in it.get("body", []):
        text(d, (X0, y), ln, fb, IVORY + (235,), 110); y += blh
    if y > H - 150: raise SystemExit(f"{i + 1}번 장 넘침 (y={y})")
    footer(d, i + 2, total)
    return img


def slide_end(e, total):
    img = cover_crop(e["img"], blur=4, dark=0.55); grad(img, top=120, bottom=180)
    d = ImageDraw.Draw(img); maxw = W - 2 * X0
    y = 300
    centered(d, y, "—  " + e.get("kicker", "오늘 밤 할 일") + "  —", pf(44), GOLD + (255,)); y += 120
    f = hf(64)
    wrap_check(d, e["lines"], f, maxw, "end")
    for ln in e["lines"]:
        centered(d, y, ln, f, IVORY + (255,)); y += int(64 * 1.45)
    y = max(y + 110, 860)
    d.line([(W / 2 - 60, y), (W / 2 + 60, y)], fill=GOLD + (200,), width=2); y += 60
    centered(d, y, "매일 밤, 황제처럼 생각하라.", hf(52), IVORY + (255,)); y += 90
    for ln in e.get("cta", ["저장해 두고 마음이 흔들릴 때 다시 보세요", "팔로우하면 황제의 한 줄이 매일 찾아갑니다"]):
        centered(d, y, ln, pf(36), DIM + (255,), 0); y += 58
    footer(d, total, total)
    return img


def main(spec_path, out_dir):
    s = json.load(open(spec_path)); os.makedirs(out_dir, exist_ok=True)
    total = len(s["items"]) + 2
    slides = [slide_cover(s["cover"], total)] + [slide_item(it, i, total) for i, it in enumerate(s["items"])] + [slide_end(s["end"], total)]
    paths = []
    for k, im in enumerate(slides, 1):
        p = os.path.join(out_dir, f"{s['id']}_{k:02d}.jpg"); im.convert("RGB").save(p, quality=90); paths.append(p)
    print("\n".join(paths))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
