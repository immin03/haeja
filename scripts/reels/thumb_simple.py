"""밸류노트 표준 썸네일 (2026-10-28 운영자: 조회수가 터진 삼성전자 쇼츠 썸네일처럼 "심플하고 직관적인" 것으로 통일)

요소는 딱 네 가지만 쓴다. 사진·손글씨·노트 배경·설명 문구는 넣지 않는다.
  1) 위 2줄 제목 (윗줄 아이보리 + 아랫줄 골드 강조)
  2) 가운데 회사 로고 — 누구나 알아보는 로고 PNG가 있을 때만 (영문 글자만 쓰는 건 눈에 안 띄어 빼고 한글 제목을 키운다)
  3) 그림 하나: 주가선(line)·막대 2개(bars) 또는 관련 사진(photo, 인물·장소·물건) — 편마다 섞어서 단조롭지 않게
  4) 아래 큰 숫자 하나 (하락 = 형광 핑크레드, 상승 = 형광 그린)

세로(쇼츠·릴스 1080x1920)와 가로(롱폼 1280x720) 둘 다 만든다.
세로는 인스타 프로필 격자(가운데 3:4)로 잘려도 다 보이게 위아래 여백을 둔다.

사용:
  python3 scripts/reels/thumb_simple.py <thumb.json> <out.jpg>

thumb.json 예:
{
 "format": "short",                       # short | long
 "l1": "삼성전자 주가 전망", "l2": "이 3가지만 보면 된다",
 "name": "SAMSUNG",                        # 또는 "logo": "scripts/reels/assets/logo/samsung.png"
 "chart": {"kind": "line", "pts": [["3월", 186200], ["6월", 374000], ["10월", 216000]], "mark": 1, "mark_label": "6월 최고 37만 4천 원"},
   # 또는 {"kind": "bars", "items": [["넣은 돈", 154, "154억$"], ["평가액", 354, "354억$"]]}
 "big": "-42%", "tone": "down",            # down | up
 "sub": "6월 최고가 대비"
}
숫자는 반드시 실제 자료에서 가져온다. 선은 실제 데이터 점(일별 시세 또는 확인된 날짜의 값)만 잇는다.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FD = os.path.join(HERE, "fonts")

IVORY = (246, 241, 232); GOLD = (240, 208, 140); GREY = (176, 186, 206)
RED = (255, 77, 109); GREEN = (61, 245, 160)
_fc = {}


def F(w, s):
    p = os.path.join(FD, "Montserrat-ExtraBold.ttf") if w == "Mont" else os.path.join(FD, f"SUIT-{w}.ttf")
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]


def fit(s, w, size, maxw, track=0):
    while size > 24 and F(w, size).getlength(s) + track * size * (len(s) - 1) > maxw: size -= 2
    return F(w, size)


def background(W, H, cy):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.zeros((H, W, 3), np.float32) + np.array([13, 27, 52], np.float32)
    r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * cy) / H) ** 2)
    g += (np.clip(.6 - r, 0, 1) * 70)[..., None] * np.array([.5, .7, 1.0])
    im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")   # 아주 옅은 격자 (삼성 썸네일처럼 차트 뒤만)
    step = 64 if W < H else 48
    for y in range(int(H * .3), H, step): d.line([(0, y), (W, y)], fill=(48, 72, 112, 70), width=2)
    for x in range(0, W, step): d.line([(x, int(H * .3)), (x, H)], fill=(48, 72, 112, 40), width=1)
    return im


def text_shadow(im, xy, s, font, fill, anchor="mm", off=5, blur=10, alpha=190, track=0):
    W, H = im.size
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    draw_text(ds, (xy[0] + off, xy[1] + off), s, font, (0, 0, 0, alpha), anchor, track)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    draw_text(ImageDraw.Draw(im), xy, s, font, fill, anchor, track)


def draw_text(d, xy, s, font, fill, anchor, track):
    if not track:
        d.text(xy, s, font=font, fill=fill, anchor=anchor); return
    gap = track * font.size; w = font.getlength(s) + gap * (len(s) - 1)
    x = xy[0] - w / 2 if anchor[0] == "m" else xy[0]
    for ch in s:
        d.text((x, xy[1]), ch, font=font, fill=fill, anchor="l" + anchor[1]); x += font.getlength(ch) + gap


def name_block(im, spec, cx, cy, maxw, maxh):
    if spec.get("logo"):
        lg = Image.open(os.path.join(ROOT, spec["logo"])).convert("RGBA")
        sc = min(maxw / lg.width, maxh / lg.height); lg = lg.resize((int(lg.width * sc), int(lg.height * sc)), Image.LANCZOS)
        im.alpha_composite(lg, (int(cx - lg.width / 2), int(cy - lg.height / 2))); return
    s = spec["name"]; latin = all(ord(c) < 128 for c in s)
    f = fit(s, "Mont" if latin else "Heavy", int(maxh * 1.25), maxw, track=.08 if latin else 0)
    text_shadow(im, (cx, cy), s, f, IVORY, off=4, blur=8, alpha=150, track=.08 if latin else 0)


def chart(im, c, box, tone):
    X0, Y0, X1, Y1 = box; d = ImageDraw.Draw(im, "RGBA")
    tone = c.get("tone", tone); col = RED if tone == "down" else GREEN   # 그림 색은 따로 정할 수 있다 (예: 월급은 하락, 큰 숫자는 상승)
    if c["kind"] == "bars":
        items = c["items"]; n = len(items); hi = max(v for _, v, _ in items)
        bw = (X1 - X0) / (n * 1.9); gap = ((X1 - X0) - bw * n) / (n + 1)
        lf = F("Bold", max(28, int((Y1 - Y0) * .08))); vf = F("Heavy", int((Y1 - Y0) * .13))
        for i, (lab, v, txt) in enumerate(items):
            x = X0 + gap + i * (bw + gap); top = Y1 - (Y1 - Y0 - vf.size * 1.6) * v / hi
            last = i == n - 1; fill = col if last else (92, 108, 138)
            if last:   # 마지막 막대만 은은하게 빛나게
                gl = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle([x, top, x + bw, Y1], 14, fill=col + (150,))
                im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(22))); d = ImageDraw.Draw(im, "RGBA")
            d.rounded_rectangle([x, top, x + bw, Y1], 14, fill=fill)
            text_shadow(im, (x + bw / 2, top - vf.size * .7), txt, vf, col if last else IVORY, off=3, blur=6, alpha=140)
            text_shadow(im, (x + bw / 2, Y1 + lf.size * .95), lab, lf, GREY, off=2, blur=4, alpha=120)
        if n == 2:   # 두 막대 사이 화살표
            d = ImageDraw.Draw(im, "RGBA"); ax0 = X0 + gap + bw + gap * .2; ax1 = X0 + gap + bw + gap * .8; ay = Y0 + (Y1 - Y0) * .42
            d.line([(ax0, ay), (ax1 - 18, ay)], fill=GOLD, width=10)
            d.polygon([(ax1, ay), (ax1 - 34, ay - 22), (ax1 - 34, ay + 22)], fill=GOLD)
        return
    vals = [v for _, v in c["pts"]]; n = len(vals); lo, hi = min(vals), max(vals); pad = (hi - lo) * .08 or 1
    pts = [(X0 + (X1 - X0) * i / (n - 1), Y1 - (v - lo + pad) / (hi - lo + 2 * pad) * (Y1 - Y0)) for i, v in enumerate(vals)]
    k = c.get("mark", int(np.argmax(vals) if tone == "down" else np.argmin(vals)))
    lw = max(8, int((Y1 - Y0) * .022))
    area = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(area).polygon(pts + [(X1, Y1), (X0, Y1)], fill=col + (38,))
    im.alpha_composite(area)
    gl = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).line(pts[k:], fill=col + (200,), width=lw * 2, joint="curve")
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(lw)))
    d = ImageDraw.Draw(im, "RGBA")
    if k > 0: d.line(pts[:k + 1], fill=GREY + (255,), width=int(lw * .75), joint="curve")
    d.line(pts[k:], fill=col, width=lw, joint="curve")
    (ax, ay), (bx, by) = pts[-2], pts[-1]; ang = math.atan2(by - ay, bx - ax); L = lw * 4
    tip = (bx + lw * 1.5 * math.cos(ang), by + lw * 1.5 * math.sin(ang))
    d.polygon([tip, (tip[0] - L * math.cos(ang - .5), tip[1] - L * math.sin(ang - .5)), (tip[0] - L * math.cos(ang + .5), tip[1] - L * math.sin(ang + .5))], fill=col)
    hx, hy = pts[k]; r = lw * 1.1
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=IVORY)
    if c.get("mark_label"):
        f = F("Bold", max(30, int((Y1 - Y0) * .065))); tw = f.getlength(c["mark_label"])
        tx = min(max(hx, X0 + tw / 2), X1 - tw / 2)
        ty = hy - r - f.size * .9 if tone == "down" else hy + r + f.size * .9
        text_shadow(im, (tx, ty), c["mark_label"], f, IVORY, off=2, blur=4, alpha=160)


def photo_panel(im, name, box, fade="tb", focus=(.5, .5)):
    """관련 사진 한 장 (2026-10-28 운영자: 숫자·그래프만 반복하지 말고 로고·사진·사람 배경도 적절히)
    사진은 scripts/blog/media/lib 의 출처 확인된 사진만 쓴다. 가장자리는 남색 바탕으로 부드럽게 녹인다."""
    X0, Y0, X1, Y1 = box; bw, bh = X1 - X0, Y1 - Y0
    ph = Image.open(os.path.join(ROOT, "scripts", "blog", "media", "lib", name)).convert("RGB")
    sc = max(bw / ph.width, bh / ph.height); ph = ph.resize((int(ph.width * sc) + 1, int(ph.height * sc) + 1), Image.LANCZOS)
    cx = int((ph.width - bw) * focus[0]); cy = int((ph.height - bh) * focus[1]); ph = ph.crop((cx, cy, cx + bw, cy + bh)).convert("RGBA")
    a = np.ones((bh, bw), np.float32)
    if "t" in fade: a *= (np.clip(np.linspace(0, 1, bh) / .35, 0, 1) ** 1.5)[:, None]
    if "b" in fade: a *= np.clip(np.linspace(1, 0, bh) / .3, 0, 1)[:, None]
    if "l" in fade: a *= np.clip(np.linspace(0, 1, bw) / .45, 0, 1)[None, :]
    dim = Image.new("RGBA", (bw, bh), (8, 18, 38, 70)); ph = Image.alpha_composite(ph, dim)   # 살짝 어둡게: 위 글자·숫자가 또렷하게
    ph.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    im.alpha_composite(ph, (X0, Y0))


def render(spec, out):
    # 2026-10-28 운영자: "BERKSHIRE·JAPAN 같은 영문 글자는 눈에 안 띈다, 위 한글 제목을 더 크게"
    # → 가운데 이름은 알아보기 쉬운 회사 로고 PNG가 있을 때만 쓰고, 없으면 그 자리를 한글 제목에 준다.
    tone = spec.get("tone", "down"); col = RED if tone == "down" else GREEN
    has_logo = bool(spec.get("logo"))
    if spec.get("format", "short") == "short":
        W, H = 1080, 1920; im = background(W, H, .55)
        s1, s2 = (86, 104) if has_logo else (108, 128)
        f1 = fit(spec["l1"], "Heavy", s1, 980); f2 = fit(spec["l2"], "Heavy", s2, 1000)
        y1 = 350 if has_logo else 380                                       # 인스타 격자(3:4)는 y 240~1680만 보인다
        text_shadow(im, (W / 2, y1), spec["l1"], f1, IVORY)
        text_shadow(im, (W / 2, y1 + f1.size * .5 + f2.size * .72), spec["l2"], f2, GOLD)
        if has_logo: name_block(im, spec, W / 2, 640, 780, 110)
        if spec.get("photo"): photo_panel(im, spec["photo"], (0, 620, W, 1400), "tb", tuple(spec.get("focus", (.5, .5))))
        if spec.get("chart"): chart(im, spec["chart"], (110, 760 if has_logo else 700, 970, 1250), tone)
        big = fit(spec["big"], "Heavy", 250, 900)
        text_shadow(im, (W / 2, 1490), spec["big"], big, col, off=8, blur=14, alpha=170)
        if spec.get("sub"): text_shadow(im, (W / 2, 1650), spec["sub"], F("SemiBold", 44), GREY, off=2, blur=4, alpha=140)
    else:
        W, H = 1280, 720; im = background(W, H, .62)
        if spec.get("photo"):   # 사진은 오른쪽, 큰 숫자는 왼쪽
            photo_panel(im, spec["photo"], (520, 0, W, H), "l", tuple(spec.get("focus", (.5, .5))))
            top_ = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gt = ImageDraw.Draw(top_)
            for y in range(240): gt.line([(0, y), (W, y)], fill=(8, 18, 38, int(200 * (1 - y / 240) ** 1.2)))
            im.alpha_composite(top_)
        s1, s2 = (64, 84) if has_logo else (80, 104)
        f1 = fit(spec["l1"], "Heavy", s1, 1180); f2 = fit(spec["l2"], "Heavy", s2, 1200)
        y1 = 70 if has_logo else 78
        text_shadow(im, (W / 2, y1), spec["l1"], f1, IVORY)
        text_shadow(im, (W / 2, y1 + f1.size * .55 + f2.size * .7), spec["l2"], f2, GOLD)
        top = 300 if has_logo else 320
        if spec.get("chart"): chart(im, spec["chart"], (70, top, 690, 650), tone)
        if has_logo: name_block(im, spec, 990, 300, 480, 74)
        big = fit(spec["big"], "Heavy", 210 if has_logo else 230, 540)
        by = 470 if has_logo else 480; bx = 330 if (spec.get("photo") and not spec.get("chart")) else 990
        text_shadow(im, (bx, by), spec["big"], big, col, off=7, blur=12, alpha=170)
        if spec.get("sub"): text_shadow(im, (bx, by + 130), spec["sub"], F("SemiBold", 34), IVORY if spec.get("photo") else GREY, off=2, blur=4, alpha=160)
    # 2026-10-28 운영자: 썸네일 제목은 짧게 — 글자를 최대 크기로 넣을 수 있는 길이만 (쇼츠 한 줄 9자 안팎, 롱폼 11자 안팎), 최대한 궁금하게
    for txt, f, mx in ((spec["l1"], f1, s1), (spec["l2"], f2, s2)):
        if f.size < mx * .92: print(f"  ⚠ 썸네일 제목이 길어 글자가 작아짐 ({f.size}/{mx}px): {txt} — 더 짧게 줄이세요")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    im.convert("RGB").save(out, quality=93)
    return out


if __name__ == "__main__":
    render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
    print("썸네일 →", sys.argv[2])
