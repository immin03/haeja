"""밸류노트 롱폼 디자인 v2 (2026-11-16 20:16 대표님 확정)
- 로고: 한 줄 굵기 대비 'VALUE(굵게)NOTE(얇게)', 흰색, 오른쪽 위
- 인트로: 홍콩 야경이 흐려지고, VALUENOTE가 한 글자씩 또렷해지며 자간이 모이고, 아래 '밸류노트'가 떠오른다
- 자막: 띠 없이 그림자만 · 인물이 말하는 장면은 다큐 이름표 + 왼쪽 정렬 자막
- 숫자 강조: 작은 라벨 + 가는 선(핑크 머리) + 아주 얇은 큰 숫자 (넷플릭스 다큐형)
- 문구 강조: 굵은 명조 기울임 흰색 (자막과 동시에 띄우지 않는다)
"""
import os, re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "..", "..", "reels", "fonts")
W, H = 1920, 1080
PINK = (255, 77, 109); WHITE = (255, 255, 255)
_F = {}


def font(name, size):
    k = (name, size)
    if k not in _F: _F[k] = ImageFont.truetype(os.path.join(FD, name), size)
    return _F[k]


EB = lambda s: font("Montserrat-ExtraBold.ttf", s)
LT = lambda s: font("Montserrat-Light.ttf", s)
SUIT = lambda w, s: font(f"SUIT-{w}.ttf", s)
NS = lambda w, s: font(f"NotoSansKR-{w}.otf", s)
SER = lambda s: font("NotoSerifKR-Black.otf", s)


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def eio(t): t = clamp(t); return t * t * (3 - 2 * t)


def _shadowed(lay, blur=6, op=.6, off=(2, 3)):
    """RGBA 레이어 → 그림자 포함 RGBA (작은 레이어에서만 흐림 → 빠르다)"""
    sh = lay.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * op))
    out = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    out.paste((0, 0, 0, 255), off, sh)
    out.alpha_composite(lay)
    return out


def _paste(im, lay, xy, a=1.0):
    if a < 1: lay = lay.copy(); lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    if im.mode == "RGBA": im.alpha_composite(lay, (int(xy[0]), int(xy[1])))
    else: im.paste(lay, (int(xy[0]), int(xy[1])), lay)


# ── 로고 (B안) ─────────────────────────────────────────
_LOGO = {}
def logo_layer(size=34, tr=3):
    k = (size, tr)
    if k not in _LOGO:
        d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
        tw = lambda t, f: sum(d0.textlength(c, font=f) for c in t) + tr * (len(t) - 1)
        f1, f2 = EB(size), LT(size); w = int(tw("VALUE", f1) + tr + tw("NOTE", f2)) + 24; h = int(size * 1.4) + 24
        lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); x = 12
        for c in "VALUE": d.text((x, 12), c, font=f1, fill=(255, 255, 255, 242)); x += d.textlength(c, font=f1) + tr
        for c in "NOTE": d.text((x, 12), c, font=f2, fill=(255, 255, 255, 242)); x += d.textlength(c, font=f2) + tr
        _LOGO[k] = _shadowed(lay, 5, .5)
    return _LOGO[k]


def logo(im, a=1.0):
    L = logo_layer(); _paste(im, L, (W - 52 + 12 - L.width, 44 - 12), a)


# ── 인트로 ────────────────────────────────────────────
def intro_source(bg_get, n_frames, fps=30):
    """bg_get(u) → 배경 영상(홍콩 야경) 프레임. 5초 기준 연출, 길이에 맞춰 늘어난다."""
    dur = max(1.0, n_frames / fps); k = dur / 5.0
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    fb, fl = EB(80), LT(80); EN = [(c, fb) for c in "VALUE"] + [(c, fl) for c in "NOTE"]
    ew = [d0.textlength(c, font=f) for c, f in EN]
    kb, kl = SUIT("Bold", 44), NS("Light", 44); KO = [(c, kb) for c in "밸류"] + [(c, kl) for c in "노트"]
    kw = [d0.textlength(c, font=f) for c, f in KO]
    BY, KY = 452, 566

    def text_layer(t):
        L = Image.new("L", (W, H), 0)
        tr = 3 + 60 * (1 - eio((t - .9 * k) / (1.6 * k))); tot = sum(ew) + tr * (len(EN) - 1); x = W / 2 - tot / 2
        for i, ((c, f), w) in enumerate(zip(EN, ew)):
            a = eout((t - .9 * k - i * .07 * k) / (.7 * k))
            if a > 0:
                g = Image.new("L", (int(w) + 80, 160), 0); ImageDraw.Draw(g).text((40, 110), c, font=f, fill=int(255 * a), anchor="ls")
                b = (1 - a) * 8
                if b > .5: g = g.filter(ImageFilter.GaussianBlur(b))
                box = (int(x) - 40, BY - 30); L.paste(Image.fromarray(np.maximum(np.asarray(L.crop((box[0], box[1], box[0] + g.width, box[1] + g.height))), np.asarray(g))), box)
            x += w + tr
        a = eout((t - 2.3 * k) / (.8 * k))
        if a > 0:
            sp = 14; tot = sum(kw) + sp * 3; x = W / 2 - tot / 2; y = KY + 14 * (1 - a); dd = ImageDraw.Draw(L)
            for (c, f), w in zip(KO, kw): dd.text((x, y + 44), c, font=f, fill=int(235 * a), anchor="ls"); x += w + sp
        return L

    def get(u):
        t = u; fr = bg_get(u)
        z = 1 + .05 * t / dur; cw, ch = int(W / z), int(H / z)
        fr = fr.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch)).resize((W, H), Image.BILINEAR)
        q = eio((t - .6 * k) / (1.2 * k)); sm = fr.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(.5 + 1.0 * q)).resize((W, H), Image.BILINEAR)
        fr = Image.blend(fr, sm, .15 + .35 * q)   # 2026-11-17 대표님: 인트로 배경을 덜 흐리게
        arr = np.asarray(fr, np.float32) * (.66 - .26 * q)
        L = text_layer(t); La = np.asarray(L, np.float32) / 255
        if La.max() > 0:
            glow = np.asarray(L.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR), np.float32) / 255 * .45
            arr = arr * (1 - glow[..., None]) + 255 * glow[..., None]
            sx = eout((t - 3.0 * k) / (.8 * k))
            if 0 < sx < 1:   # 은은한 빛 훑기
                sw = Image.new("L", (W, H), 0); x0 = int(500 + 900 * sx)
                ImageDraw.Draw(sw).polygon([(x0, 380), (x0 + 60, 380), (x0 + 10, 720), (x0 - 50, 720)], fill=120)
                swa = np.minimum(np.asarray(sw.filter(ImageFilter.GaussianBlur(18)), np.float32) / 255, La)
                arr = arr * (1 - swa[..., None]) + np.array([255, 245, 225], np.float32) * swa[..., None]
            arr = arr * (1 - La[..., None]) + 255 * La[..., None]
        fade = eout(t / .5) * (1 - eout((t - (dur - .5)) / .5))
        return Image.fromarray(np.clip(arr * fade, 0, 255).astype(np.uint8))
    return get


def intro_sfx_times(dur):
    k = dur / 5.0
    return {"whoosh": .25 * k, "boom": .95 * k, "chime": 2.35 * k}


# ── 자막 (그림자만) ─────────────────────────────────────
def subtitle_line(im, text, a, x0=None, y=None, size=52, bg=False, box=False):   # 2026-11-17 대표님: 55px는 살짝 커 보여 52px
    if not text or a <= 0: return
    f = SUIT("Bold", size); d0 = ImageDraw.Draw(Image.new("L", (1, 1))); tw = d0.textlength(text, font=f)
    if box:   # 2026-11-19 대표 v5: 뉴스 화면(80% 축소) 아래 빈 띠에 반투명 검정 바탕 자막 — 방송사 하단 띠와 겹치지 않게
        x = (W - tw) / 2 if x0 is None else x0; y = H - 150 if y is None else y
        bx = Image.new("RGBA", (int(tw) + 56, size + 34), (0, 0, 0, 0)); ImageDraw.Draw(bx).rounded_rectangle([0, 0, bx.width - 1, bx.height - 1], 12, fill=(0, 0, 0, 165))
        _paste(im, bx, (x - 28, y - 10), a)
        lay = Image.new("RGBA", (int(tw) + 4, size + 20), (0, 0, 0, 0)); ImageDraw.Draw(lay).text((0, -4), text, font=f, fill=(255, 255, 255, 255))
        _paste(im, lay, (x, y + 4), a); return
    pad = 30; lay = Image.new("RGBA", (int(tw) + pad * 2, size + pad * 2), (0, 0, 0, 0))
    if bg:   # 2026-11-19 대표(v4.1): 원음(뉴스 화면) 장면은 반투명 검정 바탕을 깔아 뉴스 띠·화면 글씨와 구분
        ImageDraw.Draw(lay).rounded_rectangle([pad - 22, 6, pad + int(tw) + 22, size + pad * 2 - 6], 14, fill=(0, 0, 0, 165))
    ImageDraw.Draw(lay).text((pad, pad - 4), text, font=f, fill=(255, 255, 255, 255))
    sh = lay.getchannel("A").filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * .78))
    out = Image.new("RGBA", lay.size, (0, 0, 0, 0)); out.paste((0, 0, 0, 255), (0, 3), sh); out.alpha_composite(lay)
    x = (W - tw) / 2 if x0 is None else x0; y = H - 150 if y is None else y
    _paste(im, out, (x - pad, y - pad + 4), a)


# ── 다큐 이름표 ─────────────────────────────────────────
def nametag(im, name, desc, p, fade, y=None):
    """2026-11-17 대표님: 이름만 짧게 보이고 직책이 안 보였다 → 이름 크게, 소속·직책은 그 아래 한 줄로 크게, 자막 위에, 장면 내내"""
    a = eout(p / .5) * fade
    if a <= 0: return
    fn, fd = SUIT("Heavy", 64), SUIT("Bold", 38)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1))); w = int(max(d0.textlength(name, font=fn), d0.textlength(desc or "", font=fd))) + 80
    lay = Image.new("RGBA", (w, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([20, 14, 26, 128 if desc else 82], fill=(255, 77, 109, 255))
    d.text((46, 70), name, font=fn, fill=(255, 255, 255, 255), anchor="ls")
    if desc: d.text((48, 122), desc, font=fd, fill=(218, 220, 225, 255), anchor="ls")
    y = (H - 370) if y is None else y
    _paste(im, _shadowed(lay, 10, .8), (90 + 24 * (1 - eout(p / .5)), y), a)


# ── 숫자·문구 강조 ──────────────────────────────────────
NUM_RE = re.compile(r"[0-9][0-9.,]*")
def is_number(text):
    return bool(NUM_RE.search(text)) and not re.match(r"^[①②③④⑤]", text)


def _left_shade(im, a):
    if a <= 0: return im
    g = _SHADE.get("g")
    if g is None:
        xs = np.linspace(0, 1, W, dtype=np.float32); ys = np.linspace(0, 1, H, dtype=np.float32)
        m = np.clip((.7 - xs) / .7, 0, 1)[None, :] ** 1.5 * (.35 + .65 * ys[:, None] ** 1.2)
        g = _SHADE["g"] = (m * 215).astype(np.float32)
    arr = np.asarray(im).astype(np.float32); mm = (g * a / 255)[..., None]
    arr[..., :3] = arr[..., :3] * (1 - mm) + np.array([6, 10, 20], np.float32) * mm
    return Image.fromarray(arr.astype(np.uint8), im.mode)
_SHADE = {}


def _split_label(sub):
    parts = [s.strip() for s in (sub or "").split("·")]
    return (parts[0] if parts else ""), " · ".join(parts[1:])


def number(im, text, sub, p, fade, numparts=None):
    """데이터 라인: 라벨(자간) + 가는 선(핑크 머리) + 얇은 큰 숫자(세어 올라감) + 출처 한 줄"""
    a = fade
    im = _left_shade(im, eout(p / .4) * fade)
    if a <= 0: return im
    label, src = _split_label(sub)
    if numparts and p >= 0:
        c = eout(p / .9); v = numparts[1] * c
        body = f"{v:,.{numparts[2]}f}" if numparts[3] else f"{v:.{numparts[2]}f}"
        text = numparts[0] + body + numparts[4]
    x = 130; y0 = H - 580
    lay = Image.new("RGBA", (W - 200, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fl = NS("Medium", 30); xx = 0; ra = eout(p / .5)
    for ch in label: d.text((xx, 0), ch, font=fl, fill=(255, 255, 255, int(255 * ra))); xx += d.textlength(ch, font=fl) + 6
    ln = 520 * eout((p - .1) / .6)
    d.rectangle([0, 52, ln, 54], fill=(255, 255, 255, 230)); d.rectangle([0, 50, min(60, ln), 56], fill=(*PINK, 255))
    fbig, fsm = NS("Thin", 210), NS("Light", 72)
    toks = re.findall(r"[0-9.,%+\-→~/]+| +|[^0-9.,%+\-→~/ ]+", text); xx = -6; base = 290; ra2 = eout((p - .15) / .5)
    for tk in toks:
        if tk.isspace(): xx += 22 * len(tk); continue
        big = bool(re.search(r"[0-9%]", tk)) or tk.strip() in ("→",)
        f = fbig if big else fsm
        d.text((xx, base), tk, font=f, fill=(255, 255, 255, int(255 * ra2)), anchor="ls"); xx += d.textlength(tk, font=f) + (4 if big else 8)
    if src: d.text((0, 350), src, font=NS("Regular", 24), fill=(190, 190, 190, int(255 * eout((p - .4) / .5))))
    _paste(im, _shadowed(lay, 10, .5), (x, y0 + 10 * (1 - eout(p / .5))), a)
    return im


def phrase(im, text, sub, p, fade):
    """문구 강조: 작은 라벨 + 굵은 명조 기울임 흰 글씨 (왼쪽 아래)"""
    a = fade
    im = _left_shade(im, eout(p / .4) * fade)
    if a <= 0: return im
    label, src = _split_label(sub)
    size = 116 if len(text) <= 8 else (96 if len(text) <= 12 else 80)
    f = SER(size); d0 = ImageDraw.Draw(Image.new("L", (1, 1))); tw = int(d0.textlength(text, font=f)) + 120; th = int(size * 1.6)
    lay = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((30, th - 30), text, font=f, fill=(255, 255, 255, 255), anchor="ls")
    shr = .16; lay = lay.transform(lay.size, Image.AFFINE, (1, shr, -shr * th, 0, 1, 0), resample=Image.BICUBIC)
    r = eout(p / .6)
    if label:
        fl = NS("Medium", 32); lw = int(d0.textlength(label, font=fl)) + 40
        ll = Image.new("RGBA", (lw + 20, 60), (0, 0, 0, 0)); ImageDraw.Draw(ll).text((10, 8), label, font=fl, fill=(240, 240, 240, 255))
        _paste(im, _shadowed(ll, 6, .6), (130 - 10, H - 300 - th + 10), a * eout(p / .5))
    _paste(im, _shadowed(lay, 10, .75, (4, 6)), (130 - 30 + 20 * (1 - r), H - 260 - th + 30), a * r)
    if src:
        sl = Image.new("RGBA", (W - 300, 50), (0, 0, 0, 0)); ImageDraw.Draw(sl).text((10, 8), src, font=NS("Regular", 24), fill=(195, 195, 195, 255))
        _paste(im, _shadowed(sl, 5, .6), (130 - 10, H - 232), a * eout((p - .4) / .5))
    return im


# ── v2.1 (2026-11-16 21:34 대표님): 표·체크리스트·타임라인 새 양식 — 자막은 항상 아래에 떠 있고 이 판들은 그 위에 놓인다 ──
def _track(d, x, y, t, f, tr, fill):
    for c in t: d.text((x, y), c, font=f, fill=fill); x += d.textlength(c, font=f) + tr
    return x


def _head(d, x, y, title, w, a):
    _track(d, x, y, title, NS("Medium", 28), 4, (255, 255, 255, int(255 * a)))
    d.rectangle([x, y + 50, x + int(w * a), y + 51], fill=(255, 255, 255, 170)); d.rectangle([x, y + 48, x + int(56 * a), y + 53], fill=(*PINK, 255))


def panel(im, b, p):
    """b: table | steps | timeline | icon 비트 · p: 나타난 뒤 흐른 시간(초). 장면 끝까지 남는다."""
    cont = bool(b.get("cont"))   # 2026-11-23 대표: 앞 장면에서 이어지는 표 — 판·기존 줄은 처음부터 그대로, 새 줄만 추가되고 강조만 바뀐다(다시 깜빡이지 않게)
    a = 1.0 if cont else eout((p + .25) / .45)
    if a <= 0: return im
    k = b.get("kind")
    if k == "timeline": return _timeline(im, b, p, a)
    im = _left_shade(im, a)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); x = 130
    if k == "table":
        rows = b.get("rows", []); y = 200 if len(rows) <= 4 else 150; title = (b.get("cols") or [""])[0] or b.get("title", "")
        if title: _head(d, x, y, title, 900, a)
        hl = b.get("hl"); lw = max([d.textlength(str(r[0]), font=NS("Medium", 28)) for r in rows] + [120]) + 60
        size = 46 if max([len(str(r[1])) for r in rows] + [0]) <= 20 else 38
        for i, r in enumerate(rows):
            ra = eout((p - .15 - .3 * i) / .45)
            if ra <= 0: continue
            yy = y + 92 + i * 112
            d.text((x, yy + 14), str(r[0]), font=NS("Medium", 28), fill=(205, 205, 210, int(255 * ra)))
            col = PINK if hl == i else (255, 255, 255)
            d.text((x + lw, yy + (0 if size == 46 else 6)), str(r[1]), font=SUIT("Bold", size), fill=(*col, int(255 * ra)))
            if len(r) > 2 and r[2]: d.text((x + lw + d.textlength(str(r[1]), font=SUIT("Bold", size)) + 28, yy + 16), str(r[2]), font=NS("Regular", 26), fill=(200, 200, 205, int(255 * ra)))
            d.rectangle([x, yy + 88, x + 900, yy + 88], fill=(255, 255, 255, int(60 * ra)))
    elif k == "steps":
        rows = b.get("rows", []); on = b.get("on")
        # 2026-11-22 대표 SOXL 3편 검수: 5줄 목록이 아래 자막과 겹침 → 4줄 이상은 줄 간격을 좁히고 위로 올린다(자막 자리 y 880 위에서 끝나게)
        many = len(rows) >= 4; y = 150 if many else 190; gap = 128 if many else 158
        if b.get("title"): _head(d, x, y, b["title"], 640, a)
        for i, r in enumerate(rows):
            ra = (1.0 if i < (on or 0) else eout((p + .05) / .45)) if cont else eout((p - .15 - .25 * i) / .45)
            if ra <= 0: continue
            yy = y + 100 + i * gap; al = int((255 if (on is None or on == i) else 115) * ra)
            d.text((x, yy + 6), f"0{i + 1}", font=NS("Thin", 72), fill=(255, 255, 255, al))
            d.text((x + 130, yy), str(r[0]), font=NS("Medium", 26), fill=(*(PINK if on == i else (200, 200, 200)), al))
            d.text((x + 130, yy + 36), str(r[1]), font=SUIT("Bold", 46), fill=(255, 255, 255, al))
            if len(r) > 2 and not many: d.text((x + 130, yy + 98), str(r[2]), font=NS("Regular", 26), fill=(215, 215, 215, al))
    elif k == "icon":
        y = H - 330; t = b.get("text", "")
        d.rectangle([x, y, x + int(56 * a), y + 5], fill=(*PINK, 255))
        f = SUIT("Bold", 50 if len(t) <= 24 else 42)
        d.text((x, y + 26), t, font=f, fill=(255, 255, 255, int(255 * a)))
    _paste(im, _shadowed(lay, 8, .6), (0, int(10 * (1 - a))), 1.0)
    return im


def _timeline(im, b, p, a):
    arr = np.asarray(im).astype(np.float32); arr[..., :3] *= (1 - .42 * a); im = Image.fromarray(arr.astype(np.uint8), im.mode)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    ev = b.get("events", []); on = b.get("on"); y = 450; x0, x1 = 230, 1690; n = max(1, len(ev) - 1)
    d.rectangle([x0, y, x0 + int((x1 - x0) * eout(p / .8)), y + 2], fill=(255, 255, 255, 190))
    for i, e in enumerate(ev):
        ra = eout((p - .2 - .3 * i) / .45)
        if ra <= 0: continue
        cx = x0 + (x1 - x0) * i / n; hot = (on == i); r = 11 if hot else 7; al = int(255 * ra)
        d.ellipse([cx - r, y + 1 - r, cx + r, y + 1 + r], fill=(*(PINK if hot else (255, 255, 255)), al))
        d.text((cx, y - 40), str(e[0]), font=NS("Thin", 76), fill=(255, 255, 255, al), anchor="ms")
        d.text((cx, y + 70), str(e[1]), font=SUIT("Bold", 38), fill=(*(PINK if hot else (255, 255, 255)), al), anchor="ms")
        if len(e) > 2: d.text((cx, y + 112), str(e[2]), font=NS("Regular", 26), fill=(210, 210, 210, al), anchor="ms")
    _paste(im, _shadowed(lay, 8, .6), (0, 0), 1.0)
    return im
