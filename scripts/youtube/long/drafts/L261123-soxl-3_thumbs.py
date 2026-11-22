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
    dict(file="thumb_a.jpg", photo="il_L261105g_cin_panic.jpeg", fx=.62, l1="반도체 급락", l2=("끝나는 신호", " 5가지")),
    dict(file="thumb_b.jpg", photo="il_L261107s_chip_stairs.jpeg", fx=.75, l1="SOXL -90%", l2=("끝나는 신호", " 5가지")),
    dict(file="thumb_c.jpg", photo="il_L261113a_phone_vs_chart.jpeg", fx=.55, l1="30년간 13번 폭락", l2=("끝나는 신호", " 5가지")),
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
    im = ImageEnhance.Color(im).enhance(.7); im = ImageEnhance.Brightness(im).enhance(1.0)
    return im.convert("RGBA")


def shadow_text(th, xy, s, f, fill):
    lay = Image.new("RGBA", th.size, (0, 0, 0, 0)); ImageDraw.Draw(lay).text(xy, s, font=f, fill=fill)
    sh = lay.getchannel("A").filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * .85))
    o = Image.new("RGBA", th.size, (0, 0, 0, 0)); o.paste((0, 0, 0, 255), (4, 6), sh); o.alpha_composite(lay); th.alpha_composite(o)


def render(t, out):
    th = photo(t["photo"], t["fx"])
    g = Image.new("RGBA", (TW, TH)); d = ImageDraw.Draw(g)
    for x in range(TW): d.line([x, 0, x, TH], fill=(0, 0, 0, int(110 * max(0, 1 - x / (TW * .85)) ** 1.2)))
    th.alpha_composite(g); g = Image.new("RGBA", (TW, TH)); d = ImageDraw.Draw(g)
    for y in range(TH // 3, TH): d.line([0, y, TW, y], fill=(0, 0, 0, int(175 * ((y - TH / 3) / (TH * 2 / 3)) ** 1.6)))
    th.alpha_composite(g); D = ImageDraw.Draw(th)
    fb = F("ExtraBold", 44); bw = D.textlength("SOXL 3편", font=fb) + 40
    D.rounded_rectangle([40, 34, 40 + bw, 34 + 66], 12, fill=(*PINK, 255)); D.text((60, 41), "SOXL 3편", font=fb, fill=(255, 255, 255))
    L = vn2.logo_layer(34); th.alpha_composite(L, (TW - 40 - L.width + 12, 34)); D = ImageDraw.Draw(th)
    LX, MAXW = 60, TW - 120
    f = F("Heavy", 168); l2 = "".join(t["l2"])
    while max(D.textlength(t["l1"], font=f), D.textlength(l2, font=f)) > MAXW: f = vn2.font(os.path.basename(f.path), f.size - 4)
    y2 = TH - 60 - f.size; y1 = y2 - 22 - f.size
    shadow_text(th, (LX, y1), t["l1"], f, WHITE)
    a, b = t["l2"]; pink_first = True   # 앞부분(핵심어)이 핑크
    shadow_text(th, (LX, y2), a, f, (*PINK, 255) if pink_first else WHITE); D = ImageDraw.Draw(th)
    shadow_text(th, (LX + D.textlength(a, font=f), y2), b, f, WHITE if pink_first else (*PINK, 255))
    th.convert("RGB").save(out, quality=92); print(t["file"], "글자", f.size)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."; os.makedirs(out, exist_ok=True)
    for t in SETS: render(t, os.path.join(out, t["file"]))
