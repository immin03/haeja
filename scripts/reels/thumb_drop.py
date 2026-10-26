"""쇼츠 썸네일: 위 제목 두 줄 + 가운데 회사 로고 + 주가가 꺾여 내려오는 선 (2026-10-26 운영자: "썸네일 중간에 삼성 로고랑 주가 내려가는 모습")

python3 scripts/reels/thumb_drop.py <spec.json> <out.jpg> <logo.png> <prices.json>
prices.json = {"series": [["2026-03-30", 186200], ...], "hi_label": "6월 최고", "now_label": "10월 23일", "drop": "-42%"}
"""
import json, math, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine as E

W, H = 1080, 1920
NAVY = (11, 27, 51); IVORY = (246, 241, 232); GOLD = (224, 200, 150); RED = (255, 77, 109)


def main(spec_p, out_p, logo_p, px_p):
    spec = json.load(open(spec_p, encoding="utf-8")); px = json.load(open(px_p, encoding="utf-8"))
    # 바탕: 남색 + 노트 줄 + 가운데 밝은 빛
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.zeros((H, W, 3), np.float32) + np.array([14, 28, 54], np.float32)
    r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .52) / H) ** 2)
    g += (np.clip(.55 - r, 0, 1) * 60)[..., None] * np.array([.55, .72, 1.0])
    im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, "RGBA")
    for y in range(520, H, 64): d.line([(40, y), (W - 40, y)], fill=(40, 62, 100, 90), width=2)
    # 제목 (영상 위쪽 제목과 같은 문구, 그림자만)
    l1, l2 = spec["banner"]
    for s, y, size, col in ((l1, 230, 96, IVORY), (l2, 360, 112, GOLD)):
        f = E.fit_font(s, "Heavy", size, 1000)
        d.text((W / 2 + 4, y + 6), s, font=f, fill=(0, 0, 0, 200), anchor="mm"); d.text((W / 2, y), s, font=f, fill=col, anchor="mm")
    # 로고
    lg = Image.open(logo_p).convert("RGBA"); lw = 760; lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
    im.paste(lg, (int(W / 2 - lw / 2), 560), lg)
    # 주가 선: 최고점에서 지금까지 꺾여 내려온다
    s = [v for _, v in px["series"]]; n = len(s); lo, hi = min(s), max(s)
    X0, X1, Y0, Y1 = 90, 990, 820, 1500
    pts = [(X0 + (X1 - X0) * i / (n - 1), Y1 - (v - lo) / (hi - lo) * (Y1 - Y0)) for i, v in enumerate(s)]
    k = int(np.argmax(s))
    area = pts + [(X1, 1560), (X0, 1560)]
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).polygon(area, fill=(255, 77, 109, 40)); im.paste(sh, (0, 0), sh)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).line(pts[k:], fill=(255, 77, 109, 200), width=34, joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(18)); im.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(im, "RGBA")
    d.line(pts[:k + 1], fill=(170, 180, 200, 255), width=12, joint="curve")
    d.line(pts[k:], fill=RED, width=16, joint="curve")
    # 끝 화살표
    (ax, ay), (bx, by) = pts[-2], pts[-1]; ang = math.atan2(by - ay, bx - ax)
    tip = (bx + 30 * math.cos(ang), by + 30 * math.sin(ang))
    for a in (2.5, -2.5):
        pass
    L = 64; d.polygon([tip, (tip[0] - L * math.cos(ang - .5), tip[1] - L * math.sin(ang - .5)), (tip[0] - L * math.cos(ang + .5), tip[1] - L * math.sin(ang + .5))], fill=RED)
    # 최고점 점·라벨
    hx, hy = pts[k]; d.ellipse([hx - 16, hy - 16, hx + 16, hy + 16], fill=IVORY)
    f = E.F("Bold", 40); d.text((hx, hy - 52), px["hi_label"], font=f, fill=IVORY, anchor="mm")
    # 큰 하락 숫자
    big = E.fit_font(px["drop"], "Heavy", 250, 700)
    d.text((W / 2 + 6, 1700 + 8), px["drop"], font=big, fill=(0, 0, 0, 170), anchor="mm")
    d.text((W / 2, 1700), px["drop"], font=big, fill=RED, anchor="mm")
    sub = E.F("SemiBold", 40); d.text((W / 2, 1850), px["now_label"], font=sub, fill=(200, 208, 222), anchor="mm")
    im.convert("RGB").save(out_p, quality=92)


if __name__ == "__main__":
    main(*sys.argv[1:5])
