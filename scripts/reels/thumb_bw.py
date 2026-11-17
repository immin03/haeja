"""쇼츠 표지 흑백 + 핑크 v2 (2026-11-17 22:28 대표님: 글씨가 작다 → 잘된 쇼츠 표지(제목 2줄 크게 → 회사 이름 → 큰 숫자 → 기준 문구 → 얇은 그래프 → 로고) 틀을 흑백+핑크로).
python3 thumb_bw.py <spec.json> <out.jpg>
spec: {photo, l1, l2, name, big, big_label, from_label?, tone: loss|gain, fx?}"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
W, H = 1080, 1920; PINK = (255, 77, 109); WH = (255, 255, 255)
def SUIT(w, s): return ImageFont.truetype(os.path.join(HERE, "fonts", f"SUIT-{w}.ttf"), s)
def MON(w, s): return ImageFont.truetype(os.path.join(HERE, "fonts", f"Montserrat-{w}.ttf"), s)
def fit(fn, w, txt, size, maxw):
    while size > 40 and fn(w, size).getlength(txt) > maxw: size -= 4
    return fn(w, size)
def st(base, xy, txt, font, fill, anchor="mm", blur=14, a=210):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text(xy, txt, font=font, fill=(0, 0, 0, a), anchor=anchor)
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur))); ImageDraw.Draw(base).text(xy, txt, font=font, fill=fill, anchor=anchor)
def render(sp, out):
    ph = Image.open(os.path.join(ROOT, "scripts", "blog", "media", "lib", sp["photo"])).convert("RGB")
    s = max(W / ph.width, H / ph.height); ph = ph.resize((int(ph.width * s) + 1, int(ph.height * s) + 1))
    ox = int((ph.width - W) * sp.get("fx", .5)); ph = ph.crop((ox, 0, ox + W, H))
    a = np.asarray(ph, np.float32); g = a.mean(2, keepdims=True); a = (a * .6 + g * .4) * 1.1
    yy = np.linspace(0, 1, H)[:, None, None]
    m = .30 + .35 * np.clip((.55 - yy) / .45, 0, 1) + .35 * np.clip((yy - .78) / .22, 0, 1)
    img = Image.fromarray(np.clip(a * (1 - m), 0, 255).astype(np.uint8)).convert("RGBA")
    col = PINK if sp.get("tone", "loss") == "loss" else WH
    # 제목 2줄 (흰색 · 둘째 줄 핑크)
    f1 = fit(SUIT, "Heavy", sp["l1"], 150, W - 70); st(img, (W / 2, 250), sp["l1"], f1, WH)   # 22:29 대표님: 제목은 짧게, 글씨는 크게(150 기준)
    f2 = fit(SUIT, "Heavy", sp["l2"], 150, W - 70); st(img, (W / 2, 420), sp["l2"], f2, PINK)
    if min(f1.size, f2.size) < 130: print("  ⚠ 표지 제목이 길어 글씨가 130 아래로 작아졌습니다 — 제목을 더 짧게:", sp["l1"], "/", sp["l2"])
    # 회사 이름 (영문 크게)
    fn = fit(MON, "ExtraBold", sp["name"], 230, W - 90); st(img, (W / 2, 660), sp["name"], fn, WH, blur=18)
    # 큰 숫자
    fb = fit(SUIT, "Heavy", sp["big"], 300, W - 80); st(img, (W / 2, 905), sp["big"], fb, col, blur=20, a=230)
    fl = fit(SUIT, "Bold", sp["big_label"], 50, W - 120); st(img, (W / 2, 1065), sp["big_label"], fl, (235, 235, 238))
    # 얇은 그래프 (높은 곳 → 낮은 곳)
    d = ImageDraw.Draw(img); x0, x1, y0, y1 = 120, 960, 1215, 1350
    pts = [(x0, y0), (x0 + 260, y0 + 30), (x0 + 430, y1 - 40), (x0 + 600, y1), (x1, y1 + 4)]
    fill = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(fill).polygon(pts + [(x1, y1 + 90), (x0, y1 + 90)], fill=(*PINK, 46)); img.alpha_composite(fill)
    d = ImageDraw.Draw(img); d.line(pts, fill=PINK, width=9, joint="curve"); d.ellipse([x0 - 13, y0 - 13, x0 + 13, y0 + 13], fill=WH)
    d.polygon([(x1 + 30, y1 + 4), (x1 - 4, y1 - 16), (x1 - 4, y1 + 24)], fill=PINK)
    if sp.get("from_label"): st(img, (x0 + 10, y0 - 50), sp["from_label"], SUIT("ExtraBold", 50), WH, anchor="lm")
    # 로고 + 핑크 밑줄
    fb2, fl2 = MON("ExtraBold", 64), MON("Light", 64); lw = fb2.getlength("VALUE") + fl2.getlength("NOTE") + 10; lx = (W - lw) / 2; ly = 1560
    st(img, (lx, ly), "VALUE", fb2, WH, anchor="lm"); st(img, (lx + fb2.getlength("VALUE") + 10, ly), "NOTE", fl2, WH, anchor="lm")
    ImageDraw.Draw(img).rounded_rectangle([lx, ly + 46, lx + lw, ly + 56], 5, fill=PINK)
    img.convert("RGB").save(out, quality=92)
if __name__ == "__main__":
    render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
