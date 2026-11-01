"""꽉 찬 그림 장면 (2026-11-01 14:06 대표님 결정 'A안': 쇼츠·릴스도 그림이 화면을 꽉 채우게)

opt-in: 장면에 "full": {...} 이 있을 때만 쓴다(없으면 지금 화면 그대로). 장면 type(hook·photo·cta 등)은 길이·마무리 계산에만 쓰이고 그림은 그리지 않는다.
  "full": {"img": "<scripts/blog/media/lib 파일>", "label": "왼쪽 위 종이 라벨 한 줄(명사형)",
           "num": "펜 숫자(선택)", "num_line": 0, "num_frac": .3, "tone": "loss|ink|gold", "focus_x": .5, "focus_y": .5}
화면: 위 제목 띠(배너, draw_banner_soft) 그대로 · 그 아래 화면 끝까지 그림이 꽉 참(천천히 켄 번즈) · 왼쪽 위 아이보리 종이 라벨 + 펜 숫자·금색 밑줄 ·
      자막은 아래쪽 어두운 그라데이션 위. 펜 동그라미로 그림을 가리지 않는다. 장면이 바뀔 때 0.35초 겹쳐 넘어간다.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONTS = os.path.join(os.path.dirname(__file__), "fonts")
XF = .35
PAPER = (246, 240, 226); INK = (24, 38, 66); RED = (196, 52, 60); GOLD = (214, 172, 84)
TONES = {"loss": RED, "ink": INK, "gold": (168, 122, 36), "good": (40, 128, 86)}
_C = {}


def _img(name):
    if name not in _C:
        p = name if os.path.isabs(name) else os.path.join(ROOT, "scripts", "blog", "media", "lib", name)
        _C[name] = Image.open(p).convert("RGB")
    return _C[name]


def _grad():
    if "g" not in _C:
        g = np.zeros((H, 1), np.float32); n = 640
        g[H - n:, 0] = np.clip(np.arange(n) / n, 0, 1) ** 1.4 * 215
        _C["g"] = Image.fromarray(np.repeat(g, W, 1).astype(np.uint8), "L")
    return _C["g"]


def _pen(size):
    k = ("pen", size)
    if k not in _C: _C[k] = ImageFont.truetype(os.path.join(FONTS, "NanumPenScript-Regular.ttf"), size)
    return _C[k]


def picture(E, s, u):
    f = s["sc"]["full"]; src = _img(f["img"])
    # 2026-11-01 16:14 대표님: 확대 효과가 어지럽다 → 기본은 정지 그림. 대본 "zoom": 0.02 이하일 때만 아주 느린 확대 한 방향
    z = 1.0 + min(float(f.get("zoom", 0) or 0), .02) * E.clamp(u / max(s["dur"], 1.0))
    r = max(W / src.width, H / src.height) * z
    im = src.resize((int(src.width * r) + 1, int(src.height * r) + 1), Image.BILINEAR)
    x0 = int((im.width - W) * f.get("focus_x", .5)); y0 = int((im.height - H) * f.get("focus_y", .5))
    return im.crop((x0, y0, x0 + W, y0 + H))


def overlay(E, img, s, u):
    """왼쪽 위 종이 라벨 + 펜 숫자 + 금색 밑줄"""
    f = s["sc"]["full"]; L = s["L"]
    lab = f.get("label"); num = f.get("num")
    if not lab and not num: return img
    a = E.prog(u, .15, .55)
    if a <= 0: return img
    p = 0.0
    if num:   # 숫자 자리는 숫자가 나타날 때 늘어난다 (2026-11-01 15:11 대표님: 펜 숫자 쓰기 전 라벨 칸이 비어 보인다)
        t0 = E.y_at(L, f.get("num_line", 0), f.get("num_frac", .3)); p = E.prog(u, t0, t0 + .45)
    lf = E.fit_font(lab or "", "ExtraBold", 46, 820) if lab else None
    pf = _pen(f.get("num_size", 150))
    d0 = ImageDraw.Draw(img)
    lw = d0.textlength(lab, font=lf) if lab else 0
    nw = d0.textlength(num, font=pf) if num else 0
    X, Y = X0, f.get("y", (getattr(E, "BAND_H", 0) or 390) + 30)
    bw = max(lw, nw * (1 if p > 0 else 0)) + 72; bh = 96 + 150 * p
    card = Image.new("RGBA", (int(bw) + 30, int(bh) + 30), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([12, 16, bw + 12, bh + 16], 10, fill=(0, 0, 0, int(90 * a)))
    card = card.filter(ImageFilter.GaussianBlur(7)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, bw, bh], 10, fill=(*PAPER, int(250 * a)))
    oy = int((1 - a) * 16)
    img.paste(card, (X, Y + oy), card)
    d = ImageDraw.Draw(img)
    if lab: d.text((X + 36, Y + oy + 50), lab, font=lf, fill=E.mix(PAPER, INK, a), anchor="lm")
    if num:
        if p > 0:
            col = TONES.get(f.get("tone", "loss"), RED)
            ny = Y + oy + 96 + 70
            d.text((X + 36, ny + (1 - p) * 10), num, font=pf, fill=E.mix(PAPER, col, p), anchor="lm")
            q = E.prog(u, t0 + .35, t0 + .9)
            if q > 0:
                x1 = X + 36 + nw * q; yy = ny + 62
                d.line([(X + 32, yy), (x1, yy - 4)], fill=GOLD, width=9)
    return img


def scene_img(E, s, u):
    if s["sc"]["full"].get("end"): return ending_card(E, s, u, s["sc"]["full"]["end"])
    img = picture(E, s, u)
    img.paste(Image.new("RGB", (W, H), (6, 12, 24)), (0, 0), _grad())
    return overlay(E, img, s, u)


def render(E, T, s, scenes):
    """현재 장면이 꽉 찬 그림 장면일 때 한 프레임 (자막·제목 띠는 engine.frame 이 얹는다)"""
    u = T - s["start"]; img = scene_img(E, s, u)
    i = scenes.index(s)
    if i > 0 and u < XF and scenes[i - 1]["sc"].get("full"):
        p = scenes[i - 1]; prev = scene_img(E, p, p["dur"] - 1 / 30)
        img = Image.blend(prev, img, E.ease_io(u / XF))
    return img


YEL = (255, 216, 77)
NAVYB = (11, 27, 51)


def band_fonts(E, lines, maxw=960):
    """제목 띠 글꼴: 1줄 흰 SemiBold, 2·3줄 노랑 Heavy — 화면 폭(좌우 60px 안)에 맞춰 최대로"""
    out = []
    for i, s_ in enumerate(lines):
        out.append(E.fit_font(s_, "SemiBold" if i == 0 else "Heavy", 74 if i == 0 else 150, maxw))
    return out


def band_height(E, lines):
    fs = band_fonts(E, lines)
    return int(44 + sum(f.size * (1.22 if i else 1.3) for i, f in enumerate(fs)) + 26)


def draw_band(E, img, lines, top=0):
    """진한 단색 네이비 제목 띠 (2026-11-01 15:11 대표님: 제목이 잘 안 보인다 → 띠를 불투명 네이비로, 숫자 줄은 밝은 노랑 + 검정 외곽선, 글자는 폭에 맞춰 최대로)"""
    fs = band_fonts(E, lines); h = band_height(E, lines)
    d = ImageDraw.Draw(img)
    d.rectangle([0, top, W, top + h], fill=NAVYB)
    d.line([(0, top + h), (W, top + h)], fill=(214, 172, 84), width=4)
    y = top + 44
    for i, (s_, f) in enumerate(zip(lines, fs)):
        lh = f.size * (1.22 if i else 1.3); cy = y + lh / 2
        if i == 0:
            d.text((W / 2, cy), s_, font=f, fill=(255, 255, 255), anchor="mm")
        else:
            d.text((W / 2 + 3, cy + 5), s_, font=f, fill=(0, 0, 0), anchor="mm")
            d.text((W / 2, cy), s_, font=f, fill=YEL, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
        y += lh
    return h


# ── 제목 띠 v4 (2026-11-01 16:11 대표님 결정: A 기준 + B의 왼쪽 정렬·골드 알약 태그, 글자 조금 더 크게, 제목 최대 2줄, 로고 영문만 크게) ──
# 대본: "banner_band": true, "banner_style": "tag", "banner_tag": "치킨 한 마리 팔면", "banner": ["사장님 손엔 3,037원", "배달앱 몫은 6,710원?"]
# 네이비 단색 띠 · 크림 글자 · 숫자만 골드 · 외곽선 없이 옅은 그림자 · 왼쪽 정렬(x 60) · 오른쪽 위 영문 ValueNote 로고. 제목 본문은 최대 2줄(넘으면 렌더 오류).
CREAM = (246, 236, 214); GOLDN = (232, 200, 132); TAGC = (214, 172, 84)
BAND_MAX_LINES = 2


def _num_runs(E, s_):
    out = []; i = 0
    for m in E.key_numbers(s_):
        if m.start() > i: out.append((s_[i:m.start()], CREAM))
        out.append((m.group(), GOLDN)); i = m.end()
    if i < len(s_): out.append((s_[i:], CREAM))
    return out


def _shadow_runs(img, x, y, runs, font):
    d = ImageDraw.Draw(img); sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh); cx = x
    for t, _ in runs: ds.text((cx + 3, y + 4), t, font=font, fill=(0, 0, 0, 150), anchor="lm"); cx += d.textlength(t, font=font)
    sh = sh.filter(ImageFilter.GaussianBlur(6)); img.paste(sh, (0, 0), sh)
    d = ImageDraw.Draw(img); cx = x
    for t, c in runs: d.text((cx, y), t, font=font, fill=c, anchor="lm"); cx += d.textlength(t, font=font)


BAND_W = int(W * .88)   # 2026-11-01 16:23 대표님: 두 줄 중 긴 줄이 화면 폭의 약 88%


def tag_fonts(E, lines):
    longest = max(lines, key=lambda t: E.F("Heavy", 100).getlength(t))
    return E.fit_font(longest, "Heavy", 160, BAND_W)


def tag_band_height(E, tag, lines):
    f = tag_fonts(E, lines)
    return int((150 if tag else 50) + len(lines) * f.size * 1.18 + 22)


def logo_en(img, x, y, size=38, a=1.0):
    from brand import logo_image
    lim, pad, off = logo_image(size, "dark", ko=False)
    if a < 1: lim = lim.copy(); lim.putalpha(lim.getchannel("A").point(lambda v: int(v * a)))
    img.paste(lim, (int(x - (lim.width - 2 * pad)) - pad, int(y) - pad), lim)


def draw_tag_band(E, img, tag, lines):
    if len(lines) > BAND_MAX_LINES: raise RuntimeError(f"제목 띠 본문은 최대 {BAND_MAX_LINES}줄 (2026-11-01 대표님): {lines}")
    h = tag_band_height(E, tag, lines); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, h], fill=NAVYB); d.line([(X0, h - 2), (W - X0, h - 2)], fill=TAGC, width=3)
    y = 50
    if tag:
        tf = E.F("Bold", 54); tw = d.textlength(tag, font=tf)
        d.rounded_rectangle([X0, 46, X0 + tw + 52, 46 + 78], 39, fill=TAGC)
        d.text((X0 + 26, 85), tag, font=tf, fill=NAVYB, anchor="lm"); y = 150
    f = tag_fonts(E, lines)
    for i, s_ in enumerate(lines):
        _shadow_runs(img, X0, y + f.size * .59 + i * f.size * 1.18, _num_runs(E, s_), f)
    return h


X0 = (W - BAND_W) // 2


def logo_bottom(img, y=1712, size=46, a=.75):
    """화면 아래 가운데 영문 ValueNote (2026-11-01 16:23 대표님: 반투명 흰색 0.75, 자막 박스 아래 여백)"""
    from brand import EN_FONT
    f = ImageFont.truetype(EN_FONT, size)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.text((W / 2 + 2, y + 3), "ValueNote", font=f, fill=(0, 0, 0, int(110 * a)), anchor="mm")
    lay = lay.filter(ImageFilter.GaussianBlur(3)); ImageDraw.Draw(lay).text((W / 2, y), "ValueNote", font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")
    img.paste(lay, (0, 0), lay)


def ending_card(E, s, u, kind):
    """엔딩 카드: 영문 ValueNote 로고 크게 + 슬로건 "매일 조금 더 / 현명한 투자 습관" + 유튜브 「+ 구독하기」/ 인스타 「+ 팔로우하기」"""
    from brand import paste_logo
    yy = np.linspace(0, 1, H)[:, None]; a = np.array(NAVYB) * (1 - yy) + np.array((6, 14, 30)) * yy
    im = Image.fromarray(np.repeat(a[:, None, :], W, 1).astype(np.uint8))
    f = s["sc"]["full"]
    if f.get("img"):
        src = _img(f["img"]).resize((W, int(W * _img(f["img"]).height / _img(f["img"]).width)))
        src = Image.blend(src, Image.new("RGB", src.size, NAVYB), .82); im.paste(src, (0, H - src.height))
    p = E.prog(u, .05, .45)
    paste_logo(im, W / 2, 660, 120, "dark", align="center", ko=False)
    d = ImageDraw.Draw(im); d.line([(W / 2 - 70, 860), (W / 2 + 70, 860)], fill=TAGC, width=4)
    fs = E.F("ExtraBold", 70)
    for i, l in enumerate(f.get("slogan", ["매일 조금 더", "현명한 투자 습관"])): d.text((W / 2, 960 + i * 98), l, font=fs, fill=(246, 241, 232) if i == 0 else GOLDN, anchor="mm")
    btn = "+ 구독하기" if kind == "yt" else "+ 팔로우하기"; fb = E.F("Heavy", 62); bw = d.textlength(btn, font=fb) + 130
    q = E.prog(u, .4, .8); by = 1230 + (1 - q) * 20
    if q > 0:
        d.rounded_rectangle([W / 2 - bw / 2, by, W / 2 + bw / 2, by + 124], 62, fill=(196, 52, 60) if kind == "yt" else TAGC)
        d.text((W / 2, by + 62), btn, font=fb, fill=(255, 255, 255) if kind == "yt" else NAVYB, anchor="mm")
    if p < 1: im = Image.blend(Image.new("RGB", (W, H), NAVYB), im, p)
    return im
