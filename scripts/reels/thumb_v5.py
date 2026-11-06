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


def badge(im, cx, cy, label, col, size=46):
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
    line_chart(im, (hw + 30, 150, hw - 70, 330), [(0, .02), (.15, .08), (.3, .05), (.45, .2), (.58, .3), (.7, .52), (.82, .62), (.9, .85), (1, 1)], GREEN)
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
    tp = Image.new("L", (1, 130)); [tp.putpixel((0, y), int(130 * (1 - y / 130) ** 1.6)) for y in range(130)]   # 위쪽 살짝 어둡게: 밝은 사진에서도 로고가 보이게
    tb = Image.new("RGBA", (W, 130), (0, 0, 0, 255)); tb.putalpha(tp.resize((W, 130))); im.alpha_composite(tb, (0, 0))
    LX = 46; maxw = spec.get("maxw", 1190)
    f1 = fit(spec["l1"], spec.get("s1", 104), maxw); f2 = fit(spec["l2"], spec.get("s2", 150), maxw)
    y2 = H - 40; y1 = y2 - f2.size * 1.02 - 4
    text(im, (LX, y1), spec["l1"], f1, tuple(spec.get("c1", IVORY)))
    text(im, (LX, y2), spec["l2"], f2, tuple(spec.get("c2", {"down": RED, "gold": (242, 212, 151)}.get(spec.get("tone"), GREEN))))   # 2026-11-06 대표님: 노란색 촌스러움 → 원래 썸네일 색(아이보리 + 형광 초록)
    if spec.get("tag"):   # 맨 위 금색 띠 한 줄 (예: "반드시 봐야 할 3가지") — 두 줄 제목과 별도로 넣는 강한 후킹
        ft = font(spec.get("st", 50)); tw = ft.getlength(spec["tag"]); ph = ft.size * 1.5; pw = tw + ft.size * 1.0; x0, y0 = 46, 34
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([x0 + 4, y0 + 6, x0 + pw + 4, y0 + ph + 6], 10, fill=(0, 0, 0, 150))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(im).rounded_rectangle([x0, y0, x0 + pw, y0 + ph], 10, fill=(242, 212, 151))
        ImageDraw.Draw(im).text((x0 + pw / 2, y0 + ph / 2 + 2), spec["tag"], font=ft, fill=NAVY, anchor="mm")
    if spec.get("logo_right") or spec.get("versus") or spec.get("tag"): paste_logo(im, W - 30, 22, 28, "dark", align="right")
    else: paste_logo(im, 34, 26, 30, "dark", align="left")   # 로고는 왼쪽 위 (오른쪽은 제품 사진 자리)
    for t, f, s in ((spec["l1"], f1, spec.get("s1", 104)), (spec["l2"], f2, spec.get("s2", 150))):
        if f.size < s * .85: print(f"  ⚠ 글자가 길어 작아짐 {f.size}/{s}: {t}")
    im.convert("RGB").save(out, quality=94); return out


if __name__ == "__main__":
    print(render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2]))
