"""롱폼 썸네일 v5 (2026-11-06) — 잘되는 경제 채널(슈카월드·지식한입·신비한 건축사전·머니인사이드·14F 등) 히트 썸네일 57장 분석 반영
- 사진 1장(또는 좌우 비교 2장)을 화면 가득. 주인공(제품·사람·건물)은 크고 선명하게
- 글씨는 아래쪽 두 줄만: 1줄 흰색(상황) / 2줄 노란색(반전·궁금증). 줄마다 한 줄로 끝낸다(줄 안에서 줄바꿈 금지)
- 굵은 검은 테두리 + 아래 어두운 그라데이션으로 작은 화면에서도 읽히게
- 작은 설명 줄은 넣지 않는다. 답(실적 숫자)을 주지 말고 '왜/어떻게'를 남긴다
- 밸류노트 로고는 오른쪽 위 작게
사용: python3 scripts/reels/thumb_v5.py spec.json out.jpg
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from brand import paste_logo

W, H = 1280, 720
IVORY = (246, 241, 232); NAVY = (11, 27, 51); WHITE = (255, 255, 255); YELLOW = (255, 214, 10); GREEN = (61, 245, 160); RED = (255, 77, 109)
LIB = os.environ.get("THUMB_LIB") or os.path.join(ROOT, "scripts", "blog", "media", "lib")


def font(s, w="Heavy"): return ImageFont.truetype(os.path.join(HERE, "fonts", f"SUIT-{w}.ttf"), s)


def fit(txt, size, maxw, w="Heavy"):
    while size > 30 and font(size, w).getlength(txt) > maxw: size -= 2
    return font(size, w)


def cover(name, w, h, focus=(.5, .5), sat=1.0, bright=1.0):
    im = Image.open(os.path.join(LIB, name)).convert("RGB")
    s = max(w / im.width, h / im.height); im = im.resize((int(im.width * s + .5), int(im.height * s + .5)), Image.LANCZOS)
    x = int((im.width - w) * focus[0]); y = int((im.height - h) * focus[1]); im = im.crop((x, y, x + w, y + h))
    if sat != 1: im = ImageEnhance.Color(im).enhance(sat)
    if bright != 1: im = ImageEnhance.Brightness(im).enhance(bright)
    return im.convert("RGBA")


def grad(im, y0, a0, a1):
    """y0부터 아래로 검은 그라데이션 (a0→a1)"""
    g = Image.new("L", (1, H), 0)
    for y in range(H):
        t = 0 if y < y0 else (y - y0) / (H - y0); g.putpixel((0, y), int(a0 + (a1 - a0) * t) if y >= y0 else 0)
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255)); black.putalpha(g.resize((W, H)))
    im.alpha_composite(black)


OUTLINE = True   # 2026-11-06 대표님 "검정 테두리 안 입히면 안 돼?" → spec "outline": false 면 테두리 없이 부드러운 그림자만


def text(im, xy, s, f, fill, anchor="ls", stroke=None):
    if not OUTLINE:   # 테두리 없음: 넓게 퍼진 그림자 두 겹으로 사진과 분리
        for off, blur, a in ((0, 22, 210), (4, 6, 170)):
            sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((xy[0] + off, xy[1] + off + 2), s, font=f, fill=(0, 0, 0, a), anchor=anchor)
            im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
        ImageDraw.Draw(im).text(xy, s, font=f, fill=fill, anchor=anchor); return
    stroke = stroke or max(6, int(f.size * .085))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0] + 4, xy[1] + 6), s, font=f, fill=(0, 0, 0, 200), anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0, 200))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def badge(im, cx, cy, label, col, size=46, maxw=580):
    while size > 28 and font(size).getlength(label) + size * .9 > maxw: size -= 2   # 긴 라벨은 칸 안에 들어오게 줄인다
    f = font(size); d = ImageDraw.Draw(im); tw = f.getlength(label); pw, ph = tw + size * .9, size * 1.45
    d.rounded_rectangle([cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2], 12, fill=col)
    d.text((cx, cy + 2), label, font=f, fill=(11, 27, 51) if col != RED else WHITE, anchor="mm")


def mark(im, cx, cy, ok, r=46):
    d = ImageDraw.Draw(im); col = GREEN if ok else RED
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=(0, 0, 0), width=5)
    if ok: d.line([(cx - r * .45, cy + r * .02), (cx - r * .1, cy + r * .38), (cx + r * .5, cy - r * .35)], fill=WHITE, width=int(r * .26), joint="curve")
    else:
        k = r * .38; d.line([(cx - k, cy - k), (cx + k, cy + k)], fill=WHITE, width=int(r * .26)); d.line([(cx - k, cy + k), (cx + k, cy - k)], fill=WHITE, width=int(r * .26))


def inset(im, name, box, focus=(.5, .5), fade=120):
    """box=(x,y,w,h) 안에 사진을 넣고 왼쪽 가장자리를 부드럽게"""
    x, y, w, h = box; ph = cover(name, w, h, focus)
    m = Image.new("L", (w, h), 255); dm = ImageDraw.Draw(m)
    for i in range(fade): dm.line([(i, 0), (i, h)], fill=int(255 * i / fade))
    fb = fade if y + h < H - 2 else 0   # 화면 안에서 끝나는 아래 가장자리도 부드럽게 (네모 경계 안 보이게)
    for i in range(fb):
        yy = h - 1 - i; a = i / fb; row = m.crop((0, yy, w, yy + 1)).point(lambda v, a=a: int(v * a)); m.paste(row, (0, yy))
    ph.putalpha(m); im.alpha_composite(ph, (x, y))


def line_chart(im, box, pts, col, glow=True, area=True, width=9):
    """box 안에 0~1 좌표 점들로 꺾은선 (빛나는 선 + 아래 옅은 면)"""
    x0, y0, w, h = box; P = [(x0 + px * w, y0 + (1 - py) * h) for px, py in pts]
    if area:
        a = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(a).polygon(P + [(P[-1][0], y0 + h), (P[0][0], y0 + h)], fill=col + (55,))
        im.alpha_composite(a.filter(ImageFilter.GaussianBlur(2)))
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).line(P, fill=col + (200,), width=width * 4, joint="curve")
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(im).line(P, fill=col + (255,), width=width, joint="curve")
    x, y = P[-1]; r = width * 1.6; ImageDraw.Draw(im).ellipse([x - r, y - r, x + r, y + r], fill=col + (255,), outline=WHITE, width=3)


def versus(spec):
    """좌우 대비형 (2026-11-06 대표님): 같은 줄에 'Before 라벨 / After 라벨', 왼쪽은 망한 장면(흑백+빨간 하락선),
    오른쪽은 오르는 주가 그래프(네이비+초록 상승선), 제품은 오른쪽에 작게"""
    L, R = spec["versus"]; im = Image.new("RGBA", (W, H), NAVY + (255,)); hw = W // 2
    im.alpha_composite(cover(L["photo"], hw, H, tuple(L.get("focus", (.5, .5))), sat=0, bright=.62), (0, 0))
    _r = Image.new("RGBA", (hw, H), (60, 0, 10, 70)); im.alpha_composite(_r, (0, 0))   # 왼쪽은 살짝 붉게 어둡게
    if L.get("chart", "down") == "down":   # 왼쪽 하락선은 실제로 떨어진 이야기일 때만 ("none"이면 생략)
        line_chart(im, (40, 170, hw - 80, 300), [(0, .95), (.18, .8), (.3, .86), (.5, .5), (.62, .58), (.8, .2), (1, .02)], RED, area=False)
    # 오른쪽: 네이비 바탕 + 옅은 격자 + 상승 그래프
    d = ImageDraw.Draw(im)
    for i in range(1, 8): d.line([(hw, i * 90), (W, i * 90)], fill=(40, 62, 98, 255), width=1)
    for i in range(1, 6): d.line([(hw + i * 110, 0), (hw + i * 110, H)], fill=(40, 62, 98, 255), width=1)
    v = Image.new("RGBA", (hw, H), (0, 0, 0, 0)); dv = ImageDraw.Draw(v)
    for i in range(H): dv.line([(0, i), (hw, i)], fill=(61, 245, 160, int(40 * (1 - i / H))))
    im.alpha_composite(v, (hw, 0))
    cy0 = max(150, spec.get("badge_y", 92) + 70)   # 그래프 끝점이 라벨에 가리지 않게
    pts = [(0, .02), (.15, .08), (.3, .05), (.45, .2), (.58, .3), (.7, .52), (.82, .62), (.9, .85), (1, 1)]
    if R.get("chart") == "peak":   # 고점 찍고 내려온 경우 (2026-11-06 삼성전자: 6월 38만 원 → 지금 하락)
        pts = [(0, .02), (.14, .06), (.28, .2), (.42, .42), (.55, .7), (.66, 1), (.76, .78), (.86, .62), (1, .5)]
    line_chart(im, (hw + 30, cy0, hw - 70, 480 - cy0), pts, GREEN)
    if R.get("chart") == "peak":   # 고점 이후 내려온 구간은 빨간색으로, 고점에 작은 표시
        bx, bw, bh = hw + 30, hw - 70, 480 - cy0
        line_chart(im, (bx, cy0, bw, bh), [p_ for p_ in pts if p_[0] >= .66], RED, area=False)
        px = hw + 30 + .66 * (hw - 70); py = cy0; d2 = ImageDraw.Draw(im); r = 11
        d2.ellipse([px - r, py - r, px + r, py + r], fill=GREEN + (255,), outline=WHITE, width=3)
    if R.get("product"):   # 제품은 작게
        x, y, sz = R.get("product_box", (hw + 30, 250, 230)); pk = cover(R["product"], sz, sz, (.5, .45))
        m = Image.new("L", (sz, sz), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, sz - 1, sz - 1], 18, fill=255); pk.putalpha(m)
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([x + 8, y + 12, x + sz + 8, y + sz + 12], 18, fill=(0, 0, 0, 170))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12))); im.alpha_composite(pk, (x, y))
        ImageDraw.Draw(im).rounded_rectangle([x, y, x + sz - 1, y + sz - 1], 18, outline=(255, 255, 255, 220), width=3)
    ImageDraw.Draw(im).rectangle([hw - 3, 0, hw + 3, H], fill=(0, 0, 0))
    by = spec.get("badge_y", 92)   # 두 라벨은 같은 줄
    badge(im, hw // 2, by, L["label"], RED, 58); badge(im, hw + hw // 2, by, R["label"], GREEN, 58)
    return im


def render(spec, out):
    global OUTLINE; OUTLINE = spec.get("outline", True)
    if spec.get("versus"): im = versus(spec)
    elif spec.get("split"):   # 좌우 비교형 (신비한 건축사전 ✓/✗ 구조)
        L, R = spec["split"]; im = Image.new("RGBA", (W, H))
        im.alpha_composite(cover(L["photo"], W // 2, H, tuple(L.get("focus", (.5, .5))), sat=.15, bright=.8), (0, 0))
        im.alpha_composite(cover(R["photo"], W // 2, H, tuple(R.get("focus", (.5, .5))), sat=1.1), (W // 2, 0))
        ImageDraw.Draw(im).rectangle([W // 2 - 4, 0, W // 2 + 4, H], fill=(0, 0, 0))
        badge(im, W // 4, 120, L["label"], RED, 54); badge(im, W * 3 // 4, 64, R["label"], GREEN, 54)
    else:
        im = cover(spec["photo"], W, H, tuple(spec.get("focus", (.5, .5))), sat=spec.get("sat", 1.1))
        if spec.get("inset"): inset(im, spec["inset"]["photo"], tuple(spec["inset"]["box"]), tuple(spec["inset"].get("focus", (.5, .5))))
    grad(im, int(H * spec.get("grad_from", .38)), 0, 235 if OUTLINE else 250)
    if spec.get("band"):   # 2026-11-10 r135 ①: 아래 42~45% 네이비→검정 띠(불투명 85%+) — 사진 밝기와 상관없이 읽히게
        by = int(H * (1 - spec.get("band_h", .44))); fe = 36; bd = Image.new("RGBA", (W, H - by + fe), (0, 0, 0, 0)); dd = ImageDraw.Draw(bd)
        for y in range(H - by + fe):
            t = max(0, y - fe) / max(1, H - by); a = int((217 + 25 * t) * min(1, y / fe)); c = tuple(int(NAVY[i] * (1 - t) + 4 * t) for i in range(3))
            dd.line([(0, y), (W, y)], fill=c + (a,))
        im.alpha_composite(bd, (0, by - fe))
    tp = Image.new("L", (1, 130)); [tp.putpixel((0, y), int(130 * (1 - y / 130) ** 1.6)) for y in range(130)]   # 위쪽 살짝 어둡게: 밝은 사진에서도 로고가 보이게
    tb = Image.new("RGBA", (W, 130), (0, 0, 0, 255)); tb.putalpha(tp.resize((W, 130))); im.alpha_composite(tb, (0, 0))
    LX = 46; maxw = spec.get("maxw", 1190)
    f1 = fit(spec["l1"], spec.get("s1", 104), maxw); f2 = fit(spec["l2"], spec.get("s2", 150), maxw)
    y2 = H - 40; y1 = y2 - f2.size * 1.02 - 4
    text(im, (LX, y1), spec["l1"], f1, tuple(spec.get("c1", IVORY)))
    text(im, (LX, y2), spec["l2"], f2, tuple(spec.get("c2", {"down": RED, "gold": (242, 212, 151)}.get(spec.get("tone"), GREEN))))   # 2026-11-06 대표님: 노란색 촌스러움 → 원래 썸네일 색(아이보리 + 형광 초록)
    if spec.get("company"):   # 2026-11-09 대표님: 쇼츠처럼 롱폼 썸네일에도 기업 로고(이름) — 두 줄 제목 바로 위
        fc = fit(spec["company"], spec.get("company_s", 104), 620, "Heavy") if not os.path.exists(os.path.join(HERE, "fonts", "Montserrat-ExtraBold.ttf")) else ImageFont.truetype(os.path.join(HERE, "fonts", "Montserrat-ExtraBold.ttf"), spec.get("company_s", 104))
        text(im, (LX + spec.get("company_dx", 2), y1 - f1.size - spec.get("company_gap", 72)), spec["company"], fc, IVORY)   # 11/9 17:21 대표님: 더 크게, 제목과 왼쪽 정렬, 살짝 위로
    if spec.get("tag") and spec.get("tag_style") == "solid":   # 2026-11-11 대표 "위 배너 배경을 둘째 줄 색으로, 글씨는 흰색 — 통일감 있게 세련되게"
        c2_ = tuple(spec.get("c2", {"down": RED, "gold": (242, 212, 151)}.get(spec.get("tone"), GREEN))); bg_ = tuple(spec.get("tag_bg", c2_))
        ft = font(spec.get("st", 62), "Heavy"); tw = ft.getlength(spec["tag"]); ph = ft.size * 1.5; pw = tw + ft.size * 1.0; x0, y0 = 44, 34
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([x0 + 3, y0 + 5, x0 + pw + 3, y0 + ph + 5], 8, fill=(0, 0, 0, 150)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(im).rounded_rectangle([x0, y0, x0 + pw, y0 + ph], 8, fill=bg_)
        ImageDraw.Draw(im).text((x0 + pw / 2, y0 + ph / 2 + 2), spec["tag"], font=ft, fill=tuple(spec.get("tag_fg", NAVY)), anchor="mm")   # 11/11 09:22 대표: 글씨는 우리 네이비
        if spec.get("ep"):   # 회차 배지: 네이비 바탕 + 띠 색 글씨
            ex = x0 + pw + 12; ew = ft.getlength(spec["ep"]) + ft.size * 1.0
            sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([ex + 3, y0 + 5, ex + ew + 3, y0 + ph + 5], 8, fill=(0, 0, 0, 150)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
            ImageDraw.Draw(im).rounded_rectangle([ex, y0, ex + ew, y0 + ph], 8, fill=NAVY)
            ImageDraw.Draw(im).text((ex + ew / 2, y0 + ph / 2 + 2), spec["ep"], font=ft, fill=bg_, anchor="mm")
    elif spec.get("tag") and spec.get("tag_style") == "slim":   # 2026-11-11 대표 "위 배너가 무식하게 커 보이지 않게" — 얇은 네이비 반투명 띠 + 금색 테두리·글씨
        ft = font(spec.get("st", 50), "Bold"); tw = ft.getlength(spec["tag"]); ph = ft.size * 1.6; pw = tw + ft.size * 1.2; x0, y0 = 44, 36
        bx = Image.new("RGBA", im.size, (0, 0, 0, 0)); bd_ = ImageDraw.Draw(bx)
        bd_.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], 8, fill=(11, 27, 51, 200), outline=(242, 212, 151, 255), width=2); im.alpha_composite(bx)
        ImageDraw.Draw(im).text((x0 + pw / 2, y0 + ph / 2 + 1), spec["tag"], font=ft, fill=(242, 212, 151), anchor="mm")
        if spec.get("ep"):
            ex = x0 + pw + 12; ew = ft.getlength(spec["ep"]) + ft.size * 1.1
            ImageDraw.Draw(im).rounded_rectangle([ex, y0, ex + ew, y0 + ph], 8, fill=(226, 45, 70))
            ImageDraw.Draw(im).text((ex + ew / 2, y0 + ph / 2 + 1), spec["ep"], font=font(spec.get("st", 50), "Heavy"), fill=WHITE, anchor="mm")
    elif spec.get("tag"):   # 맨 위 금색 띠 한 줄 (예: "반드시 봐야 할 3가지") — 두 줄 제목과 별도로 넣는 강한 후킹
        # 11/9 17:21 대표님: 왼쪽 위 띠 글씨가 작다 → 62→82
        ft = fit(spec["tag"], spec.get("st", 82), 1000); tw = ft.getlength(spec["tag"]); ph = ft.size * 1.55; pw = tw + ft.size * 1.1; x0, y0 = 40, 30   # 2026-11-06 대표님 "배너가 너무 안 보인다" → 50→62px
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([x0 + 4, y0 + 6, x0 + pw + 4, y0 + ph + 6], 10, fill=(0, 0, 0, 220))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        ImageDraw.Draw(im).rounded_rectangle([x0, y0, x0 + pw, y0 + ph], 10, fill=(242, 212, 151))
        ImageDraw.Draw(im).text((x0 + pw / 2, y0 + ph / 2 + 2), spec["tag"], font=ft, fill=NAVY, anchor="mm")
        if spec.get("ep"):   # 시리즈 회차 배지 (예: "2편") — 금색 띠 바로 오른쪽, 빨간 상자 흰 글씨
            ex = x0 + pw + 18; ew = ft.getlength(spec["ep"]) + ft.size * 1.0
            sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([ex + 4, y0 + 6, ex + ew + 4, y0 + ph + 6], 10, fill=(0, 0, 0, 220)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
            ImageDraw.Draw(im).rounded_rectangle([ex, y0, ex + ew, y0 + ph], 10, fill=(226, 45, 70))
            ImageDraw.Draw(im).text((ex + ew / 2, y0 + ph / 2 + 2), spec["ep"], font=ft, fill=WHITE, anchor="mm")
    if spec.get("logo_right") or spec.get("versus") or spec.get("tag"): paste_logo(im, W - 30, 22, 40, "dark", align="right")   # 11/9 17:37 대표님: 밸류노트 로고도 더 크게 (28→40)
    else: paste_logo(im, 34, 26, 42, "dark", align="left")   # 로고는 왼쪽 위 (오른쪽은 제품 사진 자리)
    for t, f, s in ((spec["l1"], f1, spec.get("s1", 104)), (spec["l2"], f2, spec.get("s2", 150))):
        if f.size < s * .85: print(f"  ⚠ 글자가 길어 작아짐 {f.size}/{s}: {t}")
    im.convert("RGB").save(out, quality=94); return out


if __name__ == "__main__":
    print(render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2]))
