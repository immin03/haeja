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
    p = {"Mont": "Montserrat-ExtraBold.ttf", "News": "BlackHanSans-Regular.ttf"}.get(w)   # News = 뉴스 썸네일 같은 굵은 제목체 (2026-10-29)
    p = os.path.join(FD, p) if p else os.path.join(FD, f"SUIT-{w}.ttf")
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
        lf = F("Bold", max(28, int((Y1 - Y0) * .08))); vf = F("Heavy", int((Y1 - Y0) * .165))   # 2026-10-29 운영자: 354억$ 같은 숫자를 조금 더 크게
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
    if spec.get("v", 1) >= 4 and spec.get("format") == "long": return render_v4(spec, out)
    if spec.get("v", 1) >= 3: return render_v3(spec, out)
    if spec.get("v", 1) == 2: return render_v2(spec, out)
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
    # 2026-10-28 운영자: 썸네일 제목은 제목만 봐도 무슨 얘기인지 정확히 알게 — 주어·목적어·명사를 빼서 모호하게 줄이지 않는다
    # (예: "워렌 버핏은 왜 / 일본에서 돈을 빌렸을까?"). 그 안에서 최대한 짧고 궁금하게. 너무 길어 글자가 크게 작아질 때만 경고
    for txt, f, mx in ((spec["l1"], f1, s1), (spec["l2"], f2, s2)):
        if f.size < mx * .75: print(f"  ⚠ 썸네일 제목이 길어 글자가 작아짐 ({f.size}/{mx}px): {txt} — 더 짧게 줄이세요")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    im.convert("RGB").save(out, quality=93)
    return out


# ───────────────────────── v2 (2026-10-28 밤) ─────────────────────────
# 운영자: "어떻게 하면 시각적으로 가장 어필이 될까 최대한 고민해서 바꿔 봐"
# 원칙 (휴대폰 격자에서 썸네일은 손톱만 하게 보인다 → 작은 글씨는 전부 소음)
#  1. 3초 안에 읽히는 건 세 덩어리뿐: ① 큰 제목 ② 숫자 이야기 한 줄(A → B) ③ 스티커처럼 붙은 결론 숫자
#  2. 배경은 그 이야기의 실제 장면 사진(어둡게 깔고 남색 톤) — 숫자만 있는 화면보다 감정이 실린다
#  3. 작은 설명 글씨(출처·단서)는 넣지 않는다. 막대 이름도 없앤다. 대신 숫자 위에 짧은 라벨 하나만 크게
#  4. 제목 둘째 줄은 밝은 골드로 질문을 꽂는다. 글자는 크게, 그림자는 진하게
#  5. 유튜브 격자 아래쪽은 '조회수' 글자가 덮고, 인스타 격자는 가운데 3:4만 보인다 → 중요한 건 y 240~1560 안에
#  6. 롱폼(가로)은 오른쪽 아래 재생 시간 표시를 피해 결론 숫자를 왼쪽 아래에
POP = (255, 206, 92); NAVY = (13, 27, 52)


def _cover(name, W, H, focus=(.5, .5), blur=1.2):
    ph = Image.open(os.path.join(ROOT, "scripts", "blog", "media", "lib", name)).convert("RGB")
    sc = max(W / ph.width, H / ph.height); ph = ph.resize((int(ph.width * sc) + 1, int(ph.height * sc) + 1), Image.LANCZOS)
    x = int((ph.width - W) * focus[0]); y = int((ph.height - H) * focus[1]); ph = ph.crop((x, y, x + W, y + H))
    if blur: ph = ph.filter(ImageFilter.GaussianBlur(blur))
    return ph.convert("RGBA")


def _shade(im, stops, axis="y"):
    """세로(또는 가로) 위치별 남색 덮개 투명도. stops = [(위치 0~1, 투명도 0~255), ...]"""
    W, H = im.size; n = H if axis == "y" else W
    xs = np.linspace(0, 1, n); a = np.interp(xs, [p for p, _ in stops], [v for _, v in stops]).astype(np.float32)
    A = np.repeat(a[:, None], W, 1) if axis == "y" else np.repeat(a[None, :], H, 0)
    ov = np.zeros((H, W, 4), np.uint8); ov[..., 0], ov[..., 1], ov[..., 2] = 8, 18, 40; ov[..., 3] = A.astype(np.uint8)
    im.alpha_composite(Image.fromarray(ov, "RGBA"))


def _sticker(im, txt, cx, cy, size, tone, angle=-5, maxw=None):
    col = RED if tone == "down" else GREEN; tc = (255, 255, 255) if tone == "down" else NAVY
    maxw = maxw or im.size[0] * .84
    while size > 60 and F("Heavy", size).getlength(txt) + size * .55 > maxw: size -= 6
    f = F("Heavy", size); tw = f.getlength(txt); pw, ph = int(tw + size * .55), int(size * 1.18)
    st = Image.new("RGBA", (pw + 80, ph + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(st)
    d.rounded_rectangle([40, 40, 40 + pw, 40 + ph], int(size * .28), fill=col)
    d.text((40 + pw / 2, 40 + ph / 2 + size * .04), txt, font=f, fill=tc, anchor="mm")
    st = st.rotate(angle, resample=Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", st.size, (0, 0, 0, 0)); sh.putalpha(st.getchannel("A").point(lambda v: int(v * .6)))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    x, y = int(cx - st.width / 2), int(cy - st.height / 2)
    im.alpha_composite(sh, (x + 10, y + 16)); im.alpha_composite(st, (x, y))


def _flow(im, fl, box, tone):
    """숫자 이야기 한 줄: [라벨] A  →  [라벨] B  (반투명 남색 카드 위)"""
    X0, Y0, X1, Y1 = box; col = RED if tone == "down" else GREEN
    a, b, la, lb = fl
    card = Image.new("RGBA", im.size, (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([X0, Y0, X1, Y1], 40, fill=(8, 18, 40, 190), outline=(255, 206, 92, 90), width=3)
    im.alpha_composite(card)
    inner = X1 - X0 - 80; arrow = 110; sa, sb = 120, 170
    while sa > 50 and F("Heavy", sa).getlength(a) + F("Heavy", sb).getlength(b) + arrow + 60 > inner: sa -= 4; sb -= 5
    fa, fb = F("Heavy", sa), F("Heavy", sb); wa, wb = fa.getlength(a), fb.getlength(b)
    tot = wa + arrow + 60 + wb; x = (X0 + X1) / 2 - tot / 2; cy = (Y0 + Y1) / 2 + 34
    fl_ = F("Bold", 46)
    text_shadow(im, (x + wa / 2, cy - sb * .62 - 18), la, fl_, (210, 218, 232), off=2, blur=4, alpha=150)
    text_shadow(im, (x + wa / 2, cy), a, fa, (205, 212, 226), off=4, blur=8, alpha=170)
    ax = x + wa + 30; d = ImageDraw.Draw(im)
    d.line([(ax, cy), (ax + arrow - 30, cy)], fill=POP, width=14)
    d.polygon([(ax + arrow, cy), (ax + arrow - 44, cy - 30), (ax + arrow - 44, cy + 30)], fill=POP)
    bx = ax + arrow + 30
    text_shadow(im, (bx + wb / 2, cy - sb * .62 - 18), lb, fl_, (235, 240, 248), off=2, blur=4, alpha=150)
    gl = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).text((bx + wb / 2, cy), b, font=fb, fill=col + (170,), anchor="mm")
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(16)))
    text_shadow(im, (bx + wb / 2, cy), b, fb, col, off=5, blur=10, alpha=190)


def _titles(im, l1, l2, x, y, maxw, s1, s2, anchor="mm"):
    f1 = fit(l1, "Heavy", s1, maxw); f2 = fit(l2, "Heavy", s2, maxw)
    for ss, ff, yy, cc in ((l1, f1, y, IVORY), (l2, f2, y + f1.size * .55 + f2.size * .72, POP)):
        text_shadow(im, (x, yy), ss, ff, cc, anchor=anchor, off=6, blur=14, alpha=230)
        text_shadow(im, (x, yy), ss, ff, cc, anchor=anchor, off=2, blur=3, alpha=200)
    return f1, f2


def render_v2(spec, out):
    tone = spec.get("tone", "down"); foc = tuple(spec.get("focus", (.5, .5)))
    if spec.get("format", "short") == "short":
        W, H = 1080, 1920
        if spec.get("photo"):
            im = _cover(spec["photo"], W, H, foc)
            _shade(im, [(0, 245), (.12, 225), (.3, 110), (.55, 60), (.75, 110), (.9, 200), (1, 240)])
        else: im = background(W, H, .5)
        f1, f2 = _titles(im, spec["l1"], spec["l2"], W / 2, 360, 1000, 112, 134)
        s1, s2 = 112, 134
        if spec.get("logo"): name_block(im, spec, W / 2, 640, 640, 120)
        if spec.get("flow"): _flow(im, spec["flow"], (50, 900, 1030, 1230), spec.get("flow_tone", tone))
        elif spec.get("chart"): chart(im, spec["chart"], (110, 820, 970, 1250), tone)
        _sticker(im, spec["big"], W / 2, 1480, 220, tone)
    else:
        W, H = 1280, 720
        if spec.get("photo"):
            im = _cover(spec["photo"], W, H, foc, blur=.8)
            _shade(im, [(0, 235), (.45, 190), (.7, 70), (1, 30)], axis="x")
            _shade(im, [(0, 120), (.35, 30), (.75, 0), (1, 90)])
        else: im = background(W, H, .62)
        f1, f2 = _titles(im, spec["l1"], spec["l2"], 60, 92, 1160, 80, 104, anchor="lm")
        s1, s2 = 80, 104
        if spec.get("chart") and not spec.get("photo"): chart(im, spec["chart"], (640, 330, 1210, 640), tone)
        _sticker(im, spec["big"], 330, 520, 150, tone, angle=-4, maxw=560)
    for txt, f, mx in ((spec["l1"], f1, s1), (spec["l2"], f2, s2)):
        if f.size < mx * .75: print(f"  ⚠ 썸네일 제목이 길어 글자가 작아짐 ({f.size}/{mx}px): {txt}")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    im.convert("RGB").save(out, quality=93)
    return out


# ───────────────────────── v3 (2026-10-29) — 밸류노트 톤앤매너 ─────────────────────────
# 운영자: "사진이 적나라하게 보여서 촌스럽다, 로고도 안 보인다. 가시성은 좋은데 기본 톤앤매너는 맞추자.
#          원래 쓰던 색, 네이비 배경 일부 + 사진 일부 혼합, 배당 600%·수익률처럼 큰 숫자"
#  - 바탕은 늘 밸류노트 네이비. 사진은 가운데(롱폼은 오른쪽)에만, 네이비 톤으로 물들여 반쯤 비치게 섞는다
#  - 제목: 아이보리 + 원래 골드(240,208,140). 숫자 카드 한 줄 + 아래 큰 결론 숫자(라벨 + 숫자, 기울이지 않음)
#  - 밸류노트 로고를 항상 넣는다 (쇼츠는 아래 가운데, 롱폼은 오른쪽 위)
import sys as _sys
_sys.path.insert(0, os.path.join(ROOT, "scripts"))


def _duotone(name, W, H, focus=(.5, .5), lo=(13, 27, 52), hi=(170, 186, 214)):
    ph = _cover(name, W, H, focus, blur=.6).convert("L")
    a = np.asarray(ph).astype(np.float32) / 255.
    a = np.clip((a - .08) / .9, 0, 1) ** 1.1
    lo_, hi_ = np.array(lo, np.float32), np.array(hi, np.float32)
    rgb = lo_ + (hi_ - lo_) * a[..., None]
    return Image.fromarray(rgb.astype(np.uint8)).convert("RGBA")


def _blend_photo(im, name, box, focus, opacity, fade):
    X0, Y0, X1, Y1 = box; bw, bh = X1 - X0, Y1 - Y0
    ph = _duotone(name, bw, bh, focus)
    a = np.full((bh, bw), opacity, np.float32)
    if "t" in fade: a *= (np.clip(np.linspace(0, 1, bh) / .3, 0, 1) ** 1.6)[:, None]
    if "b" in fade: a *= (np.clip(np.linspace(1, 0, bh) / .35, 0, 1) ** 1.6)[:, None]
    if "l" in fade: a *= (np.clip(np.linspace(0, 1, bw) / .6, 0, 1) ** 1.6)[None, :]
    if "s" in fade:   # 양옆도 살짝
        e = np.minimum(np.linspace(0, 1, bw), np.linspace(1, 0, bw)); a *= (np.clip(e / .12, 0, 1))[None, :]
    ph.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    im.alpha_composite(ph, (X0, Y0))


def _big(im, label, txt, cx, ly, ny, size, tone, maxw, anchor="m"):
    col = RED if tone == "down" else GREEN
    f = fit(txt, "Heavy", size, maxw); lf = F("Bold", max(34, int(size * .24)))
    a = "mm" if anchor == "m" else "lm"
    if label: text_shadow(im, (cx, ly), label, lf, IVORY, anchor=a, off=2, blur=5, alpha=170)
    gl = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).text((cx, ny), txt, font=f, fill=col + (150,), anchor=a)
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(size * .09)))
    text_shadow(im, (cx, ny), txt, f, col, anchor=a, off=6, blur=12, alpha=190)


def _titles3(im, l1, l2, x, y, maxw, s1, s2, anchor="mm"):
    f1 = fit(l1, "Heavy", s1, maxw); f2 = fit(l2, "Heavy", s2, maxw)
    for ss, ff, yy, cc in ((l1, f1, y, IVORY), (l2, f2, y + f1.size * .55 + f2.size * .72, GOLD)):
        text_shadow(im, (x, yy), ss, ff, cc, anchor=anchor, off=5, blur=12, alpha=210)
    return f1, f2


def _bg_photo(im, name, focus=(.5, .5), opacity=.3):
    """배경 사진을 은은하게 (2026-10-29 운영자: 머니스웨거처럼 사진이 은은하게 깔린 게 세련됐다, 적나라하면 촌스럽다)
    네이비 톤으로 물들이고 30% 안팎으로만 비치게, 가장자리는 어둡게."""
    W, H = im.size
    ph = _duotone(name, W, H, focus, lo=(10, 22, 46), hi=(150, 168, 200))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - np.clip(np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H * .5) / (H * .62)) ** 2), 0, 1) ** 1.6
    ph.putalpha(Image.fromarray((np.clip(v, 0, 1) * opacity * 255).astype(np.uint8)))
    im.alpha_composite(ph)


def emblem(im, kind, cx, cy, size, text=None):
    """한눈에 주제를 알려 주는 포인트 하나 (2026-10-29 운영자: 삼성은 삼성 로고가 있어 직관적이었다 — 그런 포인트가 꼭 하나)
    jp_flag · coin(text=기호) · envelope(text=글자) · stamp(text=글자) · goldbar"""
    W, H = im.size; L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    if kind == "jp_flag":
        w, h = size * 1.5, size; x0, y0 = cx - w / 2, cy - h / 2
        d.rounded_rectangle([x0, y0, x0 + w, y0 + h], int(size * .06), fill=(246, 241, 232))
        r = size * .3; d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(214, 40, 66))
    elif kind == "coin":
        r = size / 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(196, 160, 92)); d.ellipse([cx - r * .86, cy - r * .86, cx + r * .86, cy + r * .86], fill=(232, 198, 128))
        d.ellipse([cx - r * .86, cy - r * .86, cx + r * .86, cy + r * .86], outline=(176, 140, 76), width=max(3, int(size * .02)))
        d.text((cx, cy + size * .02), text or "¥", font=F("Heavy", int(size * .6)), fill=(120, 88, 36), anchor="mm")
    elif kind == "envelope":
        w, h = size * 1.45, size * .95; x0, y0 = cx - w / 2, cy - h / 2
        d.rounded_rectangle([x0, y0, x0 + w, y0 + h], int(size * .05), fill=(240, 232, 214))
        d.polygon([(x0, y0), (x0 + w, y0), (cx, y0 + h * .48)], fill=(222, 210, 186))
        d.line([(x0, y0), (cx, y0 + h * .48), (x0 + w, y0)], fill=(196, 182, 156), width=max(3, int(size * .02)))
        if text: d.text((cx, y0 + h * .74), text, font=F("Heavy", int(size * .28)), fill=(170, 40, 60), anchor="mm")
    elif kind == "goldbar":
        w, h = size * 1.6, size * .62; x0, y0 = cx - w / 2, cy - h / 2; t = h * .32
        d.polygon([(x0 + w * .12, y0), (x0 + w * .88, y0), (x0 + w, y0 + t), (x0, y0 + t)], fill=(250, 222, 140))
        d.polygon([(x0, y0 + t), (x0 + w, y0 + t), (x0 + w * .94, y0 + h), (x0 + w * .06, y0 + h)], fill=(214, 168, 70))
        d.polygon([(x0 + w * .2, y0 + t * .2), (x0 + w * .5, y0 + t * .2), (x0 + w * .45, y0 + t * .8), (x0 + w * .12, y0 + t * .8)], fill=(255, 240, 196))
        d.text((cx, y0 + t + (h - t) / 2), text or "GOLD", font=F("Mont", int(size * .2)), fill=(150, 108, 30), anchor="mm")
    elif kind == "stamp":
        f = F("Heavy", int(size * .42)); tw = f.getlength(text); w, h = tw + size * .5, size * .78
        st = Image.new("RGBA", (int(w + 40), int(h + 40)), (0, 0, 0, 0)); ds = ImageDraw.Draw(st); c = (255, 77, 109)
        ds.rounded_rectangle([20, 20, 20 + w, 20 + h], int(size * .08), outline=c, width=max(6, int(size * .06)))
        ds.text((20 + w / 2, 20 + h / 2 + size * .02), text, font=f, fill=c, anchor="mm")
        st = st.rotate(-8, resample=Image.BICUBIC, expand=True); L.alpha_composite(st, (int(cx - st.width / 2), int(cy - st.height / 2)))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.putalpha(L.getchannel("A").point(lambda v: int(v * .55)))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(max(8, size * .08))), (int(size * .04), int(size * .07)))
    im.alpha_composite(L)


def render_v3(spec, out):
    """2026-10-29 운영자: 삼성전자 썸네일 톤 + 은은한 배경 사진(머니스웨거 느낌) + 한눈에 주제를 알려 주는 포인트 하나.
    네이비 빛·옅은 격자, 위 제목(아이보리 + 골드), 포인트(로고 PNG 또는 emblem), 빛나는 그래프, 아래 라벨 + 큰 숫자, 작은 밸류노트 로고."""
    from brand import paste_logo
    tone = spec.get("tone", "down"); ig = spec.get("safe") == "ig"; foc = tuple(spec.get("focus", (.5, .5)))
    em = spec.get("emblem")
    if spec.get("format", "short") == "short":
        W, H = 1080, 1920; im = background(W, H, .52); o = 60 if ig else 0
        if spec.get("photo"): _bg_photo(im, spec["photo"], foc, spec.get("photo_opacity", .32))
        f1 = fit(spec["l1"], "Heavy", 100, 980); f2 = fit(spec["l2"], "Heavy", 120, 1000); s1, s2 = 100, 120
        text_shadow(im, (W / 2, 250 + o), spec["l1"], f1, IVORY)
        text_shadow(im, (W / 2, 250 + o + f1.size * .5 + f2.size * .75), spec["l2"], f2, GOLD)
        top = 520 + o
        if spec.get("logo"): name_block(im, spec, W / 2, top + 90, 780, 130); top += 220
        elif em: emblem(im, em["kind"], W / 2, top + 130, em.get("size", 230), em.get("text")); top += 290
        bot = 1300 if ig else 1340
        if spec.get("chart"): chart(im, spec["chart"], (130, top + 50, 950, bot), tone)
        ly, ny = (bot + 150, bot + 290) if not ig else (bot + 140, bot + 270)
        _big(im, spec.get("big_label"), spec["big"], W / 2, ly, ny, 220 if not ig else 200, tone, 960)
        paste_logo(im, W / 2, 90, 34, "dark", align="center")
    else:
        # 롱폼 (2026-10-29 운영자: JTBC 뉴스 썸네일처럼 — 배경 사진이 잘 드러나게, 아래 두 톤 큰 제목(굵은 제목체),
        #       오른쪽 위 로고 크게, 큰 숫자는 글자처럼 얹지 말고 배경에 녹여서 크게)
        W, H = 1280, 720; im = background(W, H, .6)
        if spec.get("photo"):
            ph = _cover(spec["photo"], W, H, foc, blur=0)
            g = np.asarray(ph.convert("RGB")).astype(np.float32); gray = g.mean(-1, keepdims=True)
            g = gray + (g - gray) * .88
            g = g * .84 + np.array([13, 27, 52], np.float32) * .16             # 네이비는 아주 살짝만
            im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGBA")
        _shade(im, [(0, 70), (.18, 0), (.5, 0), (.62, 110), (.8, 205), (1, 235)])   # 위 로고 자리와 아래 제목 자리만
        col = RED if tone == "down" else GREEN
        if spec.get("big"):   # 배경에 녹인 큰 숫자: 반투명 + 은은한 빛, 사진 위에 스며들게
            bf = F("News", 300); bx, by = 40, 44
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).text((bx, by), spec["big"], font=bf, fill=col + (150,))
            im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(26)))
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).text((bx, by), spec["big"], font=bf, fill=col + (200,))
            im.alpha_composite(lay)
            if spec.get("big_label"):
                tw = bf.getlength(spec["big"]); bb = bf.getbbox(spec["big"])
                text_shadow(im, (bx + tw + 22, by + bb[3] - 22), spec["big_label"], F("Bold", 34), IVORY, anchor="ls", off=2, blur=5, alpha=200)
        f1 = fit(spec["l1"], "News", 92, 1180); f2 = fit(spec["l2"], "News", 106, 1200); s1, s2 = 92, 106
        y2 = H - 22 - f2.size * .58; y1 = y2 - f2.size * .55 - f1.size * .6 - 4
        text_shadow(im, (W / 2, y1), spec["l1"], f1, GOLD, off=4, blur=10, alpha=230)
        text_shadow(im, (W / 2, y2), spec["l2"], f2, IVORY, off=4, blur=10, alpha=230)
        if not spec.get("photo") and spec.get("chart"): chart(im, spec["chart"], (660, 140, 1210, 420), tone)
        paste_logo(im, W - 34, 28, 44, "dark", align="right")
    for txt, f, mx in ((spec["l1"], f1, s1), (spec["l2"], f2, s2)):
        if f.size < mx * .75: print(f"  ⚠ 썸네일 제목이 길어 글자가 작아짐 ({f.size}/{mx}px): {txt}")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    im.convert("RGB").save(out, quality=93)
    return out

def render_v4(spec, out):
    """롱폼 썸네일 확정 틀 (2026-10-29 운영자: 예전 삼성·하이닉스 롱폼 썸네일 "이 정도 느낌이 낫다" + 썸네일 연구 정리)
    - 주제 실사 사진 1장을 화면 가득, 왼쪽만 어둡게 (사진은 물들이지 않는다)
    - 왼쪽 정렬로 세 줄만: [로고 또는 주제어] · 흰 짧은 한 줄 · 아주 큰 색 글씨 숫자 질문 (글자는 합쳐 3~6단어)
    - 글꼴은 SUIT Heavy 하나, 밸류노트 로고는 오른쪽 위, 오른쪽 아래는 재생 시간 자리라 비운다
    - 설명은 영상 제목이 한다. 썸네일은 핵심 명사와 숫자만"""
    from brand import paste_logo
    W, H = 1280, 720; foc = tuple(spec.get("focus", (.5, .5)))
    im = _cover(spec["photo"], W, H, foc, blur=0) if spec.get("photo") else background(W, H, .6)
    _shade(im, [(0, 235), (.4, 195), (.66, 60), (.88, 0), (1, 0)], axis="x")
    _shade(im, [(0, 40), (.2, 0), (.8, 0), (1, 70)])
    tone = spec.get("tone", "down")
    acc = {"down": (255, 92, 104), "up": GREEN, "gold": (242, 212, 151), "ivory": (250, 247, 240)}.get(tone, (242, 212, 151))
    LX = 64; maxw = W - 2 * LX - 120
    rows = []
    if spec.get("logo"):
        lg = Image.open(os.path.join(ROOT, spec["logo"])).convert("RGBA"); lh = 64; lg = lg.resize((int(lg.width * lh / lg.height), lh), Image.LANCZOS); rows.append(("img", lg))
    elif spec.get("name"): rows.append(("txt", spec["name"], fit(spec["name"], "Mont", 70, maxw), IVORY))
    rows.append(("txt", spec["l1"], fit(spec["l1"], "Heavy", 84, maxw), IVORY))
    f2 = fit(spec["l2"], "Heavy", 150, maxw); rows.append(("txt", spec["l2"], f2, acc))
    hts = [r[1].height if r[0] == "img" else r[2].size for r in rows]; gap = 22
    y = (H - (sum(hts) + gap * (len(rows) - 1))) / 2 + 10
    for r, h in zip(rows, hts):
        if r[0] == "img": im.alpha_composite(r[1], (LX, int(y)))
        else:
            text_shadow(im, (LX, y + h / 2), r[1], r[2], r[3], anchor="lm", off=5, blur=14, alpha=200)
        y += h + gap
    paste_logo(im, W - 36, 30, 30, "dark", align="right")
    if f2.size < 150 * .75: print(f"  ⚠ 큰 글씨가 길어 작아짐 ({f2.size}/150px): {spec['l2']} — 3~4단어로 줄이세요")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    im.convert("RGB").save(out, quality=93)
    return out


if __name__ == "__main__":
    render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
    print("썸네일 →", sys.argv[2])
