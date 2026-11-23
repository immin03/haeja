"""SOXL 3편 썸네일 A·B·C — 핵심만 크게 · 20:53 대표 각도 '반도체 급락, 끝나는 신호 5가지' (2026-11-22 20:50 대표: "텍스트가 너무 많아, 핵심만 강력하게" · 20:51 "버핏은 빼고 기존 3개")
- 17:08 확정 문구에서 머리글 줄을 빼고 큰 두 줄만 남긴다. 사진 3장은 그대로(A/B 테스트 규칙: 서로 다른 사진)
- 왼쪽 위 핑크 'SOXL 3편' 배지, 오른쪽 위 VALUE NOTE, 두 번째 줄 핵심어만 핑크
사용: python3 scripts/youtube/long/drafts/L261123-soxl-3_thumbs.py <out_dir>
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, ".."))
import vn2
LIB = os.path.join(HERE, "..", "..", "..", "blog", "media", "lib")
TW, TH = 1280, 720; PINK = vn2.PINK; WHITE = (255, 255, 255, 255)

SETS = [   # 20:53 대표: 제목 각도 '반도체 급락, 끝나는 신호 5가지'로 — 아랫줄은 세 안 공통, 윗줄만 바꿔 A/B 테스트
    dict(file="thumb_a.jpg", photo="il_L261105g_cin_panic.jpeg", fx=.62, l1="반도체 바닥 신호 0/5", l2=("물타기 전 꼭 보세요", "")),   # 22:30 대표 "세게" · 11/23 19:46 "전에 → 전"
    dict(file="thumb_b.jpg", photo="il_L261107s_red_cliff.jpeg", fx=.6, chip="고점 대비 -90% 폭락", l1=("SOXL 300 → ", "30달러"), l2=("지금 물타도 될까?", ""), ep2=True),   # 23:29 대표: 2편 썸네일(300 → 46달러)을 기억하는 시청자용 — 같은 틀, 지금 디자인
    dict(file="thumb_c.jpg", photo="il_L261113a_phone_vs_chart.jpeg", fx=.55, l1="반도체 바닥 신호 0/5", l2=("바닥은 아직일까?", "")),
]


def F(w, s):
    return vn2.SUIT(w if os.path.exists(os.path.join(vn2.FD, f"SUIT-{w}.ttf")) else "ExtraBold", s)


def photo(name, fx):
    im = Image.open(os.path.join(LIB, name)).convert("RGB")
    a = im.convert("L").point(lambda v: 255 if v > 12 else 0).getbbox()   # 위아래 검은 띠(레터박스) 잘라 내기
    if a: im = im.crop(a)
    s = max(TW / im.width, TH / im.height); im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x0 = int((im.width - TW) * fx); y0 = (im.height - TH) // 2
    im = im.crop((x0, y0, x0 + TW, y0 + TH))
    im = ImageEnhance.Color(im).enhance(.8); im = im.point([min(255, int(255 * ((v / 255) ** .62) * 1.12)) for v in range(256)] * 3)   # 22:42·13:18 대표: 사진 더 밝게
    return im.convert("RGBA")


def shadow_text(th, xy, s, f, fill):
    lay = Image.new("RGBA", th.size, (0, 0, 0, 0)); ImageDraw.Draw(lay).text(xy, s, font=f, fill=fill)
    sh = lay.getchannel("A").filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * .85))
    o = Image.new("RGBA", th.size, (0, 0, 0, 0)); o.paste((0, 0, 0, 255), (4, 6), sh); o.alpha_composite(lay); th.alpha_composite(o)


def render(t, out):
    th = photo(t["photo"], t["fx"])
    g = Image.new("RGBA", (TW, TH)); d = ImageDraw.Draw(g)
    for x in range(TW): d.line([x, 0, x, TH], fill=(0, 0, 0, int(85 * max(0, 1 - x / (TW * .85)) ** 1.2)))
    th.alpha_composite(g); g = Image.new("RGBA", (TW, TH)); d = ImageDraw.Draw(g)
    for y in range(TH // 3, TH): d.line([0, y, TW, y], fill=(0, 0, 0, int(150 * ((y - TH / 3) / (TH * 2 / 3)) ** 1.6)))
    th.alpha_composite(g); D = ImageDraw.Draw(th)
    fb = F("ExtraBold", 54)
    if t.get("chip"):   # 2편 틀: 빨간 띠(고점 대비 하락) + 어두운 '3편'
        bw = D.textlength(t["chip"], font=fb) + 48; D.rounded_rectangle([40, 32, 40 + bw, 32 + 80], 14, fill=(*PINK, 255)); D.text((64, 39), t["chip"], font=fb, fill=(255, 255, 255))
        x2 = 40 + bw + 16; bw2 = D.textlength("3편", font=fb) + 48; D.rounded_rectangle([x2, 32, x2 + bw2, 32 + 80], 14, fill=(20, 20, 24, 235)); D.text((x2 + 24, 39), "3편", font=fb, fill=(255, 255, 255))
    else:
        bw = D.textlength("SOXL 3편", font=fb) + 48   # 21:01 대표: 배지 조금 더 크게 (44 → 54)
        D.rounded_rectangle([40, 32, 40 + bw, 32 + 80], 14, fill=(*PINK, 255)); D.text((64, 39), "SOXL 3편", font=fb, fill=(255, 255, 255))
    L = vn2.logo_layer(34); th.alpha_composite(L, (TW - 40 - L.width + 12, 34)); D = ImageDraw.Draw(th)
    # 20:58 대표 "너무 과하게 큼 → 조금 더 세련되게": 잘된 썸네일(저스트인타임·삼성 3가지 편) 비율 — 화면 높이의 약 16~17%, 두 줄 사이 숨, 여백 넉넉히
    LX = 72; f1 = F("ExtraBold", 121); f2 = F("Heavy", 132)   # 11/23 19:58 대표: 글씨 +8%
    y2 = TH - 84 - f2.size; y1 = y2 - 18 - f1.size
    if t.get("ep2"):
        l1s = "".join(t["l1"]); z = 132
        while ImageDraw.Draw(th).textlength(l1s, font=F("Heavy", z)) > TW - 2 * LX - 10: z -= 4
        f1 = F("Heavy", z); y1 = y2 - 20 - f1.size
    if isinstance(t["l1"], tuple):
        p1, q1 = t["l1"]; shadow_text(th, (LX, y1), p1, f1, WHITE); D = ImageDraw.Draw(th); shadow_text(th, (LX + D.textlength(p1, font=f1), y1), q1, f1, (*PINK, 255)); t = dict(t, l1=p1 + q1)
    else: shadow_text(th, (LX, y1), t["l1"], f1, WHITE)
    if t.get("ep2"): t = dict(t, l2=("", t["l2"][0]))   # 둘째 줄은 흰색
    a, b = t["l2"]; D = ImageDraw.Draw(th)
    shadow_text(th, (LX, y2), a, f2, (*PINK, 255)); D = ImageDraw.Draw(th)
    shadow_text(th, (LX + D.textlength(a, font=f2), y2), b, f2, WHITE)
    assert D.textlength(t["l1"], font=f1) < TW - 2 * LX and D.textlength(a + b, font=f2) < TW - 2 * LX
    th.convert("RGB").save(out, quality=92); print(t["file"])


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."; os.makedirs(out, exist_ok=True)
    for t in SETS: render(t, os.path.join(out, t["file"]))
