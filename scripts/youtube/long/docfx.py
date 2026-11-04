"""다큐 스타일 화면 글씨·그래프 (2026-11-04 대표님: "흰 둥근 판은 덜 세련돼 보인다… 진짜 다큐같이", 시안 보고 "너무 좋아… 모션 그래픽 좀 넣어줘")

사진·영상 위에 판 없이 바로 그린다:
  · 사진 왼쪽을 남색으로 서서히 어둡게 (글씨가 나타날 때 0.5초에 걸쳐)
  · 첫 인쇄 글씨 = 키커: 금색 짧은 선이 그어지고 작은 금색 글씨가 옆에서 미끄러져 들어온다
  · 다음 인쇄 글씨 = 흰 글씨 한 줄 (아래에서 살짝 올라오며)
  · 손글씨(write) = 큰 굵은 숫자/문장 (숫자 하나면 0에서 세어 올라간다)
  · chart = 흰 선이 빛나는 머리점을 따라 그려지고, 아래는 금색 옅은 면, 끝점은 금색 점 + 퍼지는 고리
  · bars = 막대가 아래에서 자라고 숫자가 따라 올라간다
  · pct = 등락률 막대(가운데 기준선 위·아래), 표시 한 줄(marker)을 금색 세로선으로
대본(sketch 비트)은 그대로 쓰고, 렌더러가 전체 화면 그림 장면에서 판·손글씨 대신 이 모듈로 그린다 (spec "overlay": "doc").
"""
import math
import os
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "..", "..", "reels", "fonts")
W, H = 1920, 1080
GOLD = (226, 192, 120); WHITE = (246, 243, 236); GRAY = (160, 168, 182)
RED = (236, 92, 100); GREEN = (84, 214, 150)
TONE = {"red": RED, "green": GREEN, "gold": GOLD, "gray": GRAY}
_F = {}


def F(w, s):
    k = (w, s)
    if k not in _F: _F[k] = ImageFont.truetype(os.path.join(FD, f"SUIT-{w}.ttf"), s)
    return _F[k]


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def eio(t): t = clamp(t); return t * t * (3 - 2 * t)


_GRAD = {}


def _grad(strength):
    if strength not in _GRAD:
        xs = np.linspace(0, 1, W, dtype=np.float32)
        a = np.clip((.78 - xs) / .78, 0, 1) ** 1.15 * strength   # 밝은 사진에서도 글씨가 읽히게 (11/4 마이크론·엔비디아 사진)
        _GRAD[strength] = a[None, :, None]
    return _GRAD[strength]


def _t0(b, lines):
    i = min(b.get("line", 0), len(lines) - 1); a, v = lines[i][0], lines[i][1]
    return a + b.get("at", .05) * v


def _num(text):
    """'4.6배' '-7.1%' '+259%' '27배' → (앞, 숫자, 소수자리, 뒤) / 숫자 하나가 아니면 None"""
    m = re.fullmatch(r"([+\-]?)(\d+(?:\.\d+)?)(%|배)", text.strip())
    if not m: return None
    s = m.group(2); return m.group(1), float(s), (len(s.split(".")[1]) if "." in s else 0), m.group(3)


def _glow_line(im, pts, col, w, glow=True):
    if len(pts) < 2: return
    if glow:
        ov = Image.new("RGBA", im.size); ImageDraw.Draw(ov).line(pts, fill=(*col, 140), width=w * 4, joint="curve")
        im.alpha_composite(ov.filter(ImageFilter.GaussianBlur(9)))
    ImageDraw.Draw(im).line(pts, fill=(*col, 255), width=w, joint="curve")


def _st(d, xy, text, font, fill, **kw):
    """그림자 있는 글씨 (밝은 사진 위에서도 또렷하게)"""
    a = fill[3] if len(fill) == 4 else 255
    d.text((xy[0] + 2, xy[1] + 3), text, font=font, fill=(0, 0, 0, int(a * .55)), **kw)
    d.text(xy, text, font=font, fill=fill, **kw)


def _tone(b, default=WHITE):
    return TONE.get(b.get("color"), default)


def draw(img, beats, u, lines):
    """img: 전체 화면 그림(RGB) · beats: 장면의 sketch 비트 · u: 장면 안 시각(초) · lines: [(시작, 길이, …)]"""
    bs = [b for b in beats if b.get("kind") in ("print", "write", "chart", "bars", "pct")]
    if not bs: return img
    ts = [_t0(b, lines) for b in bs]
    g = eio((u - (min(ts) - .25)) / .5)
    if g <= 0: return img
    a = np.asarray(img).astype(np.float32)
    m = _grad(.86) * g; navy = np.array([8, 14, 26], np.float32)
    a = a * (1 - .18 * g)   # 화면 전체를 살짝 어둡게 (다큐 색)
    a = a * (1 - m) + navy * m
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    X = 150; y = 150; first = True
    for b, t0 in zip(bs, ts):
        p = (u - t0)
        if p < 0:
            # 아직 안 나온 것도 자리는 차지해야 다음 줄 위치가 흔들리지 않는다
            y += _height(b, first); first = first and b["kind"] != "print"; continue
        k = b["kind"]
        if k == "print" and first:
            q = eout(p / .35); d = ImageDraw.Draw(im, "RGBA")
            d.line([(X, y + 17), (X + 50 * q, y + 17)], fill=(*GOLD, 255), width=3)
            r = eout((p - .15) / .4)
            if r > 0: _st(d, (X + 66 - 24 * (1 - r), y), b["text"], font=F("SemiBold", 32), fill=(*GOLD, int(255 * r)))
            y += _height(b, True); first = False
        elif k == "print":
            r = eout(p / .45); d = ImageDraw.Draw(im, "RGBA")
            col = _tone(b, WHITE); sz = 44 if len(b.get("text", "")) <= 22 else 38
            _st(d, (X, y + 14 * (1 - r)), b["text"], font=F("Bold", sz), fill=(*col, int(255 * r)))
            y += _height(b, False)
        elif k == "write":
            r = eout(p / .5); d = ImageDraw.Draw(im, "RGBA")
            col = _tone(b, WHITE); txt = b.get("text") or "".join(b.get("rows") or [])
            n = _num(txt)
            if n:   # 숫자 하나: 0에서 세어 올라간다
                c = eout(p / 1.0); v = n[1] * c; txt = f"{n[0]}{v:,.{n[2]}f}{n[3]}"
            sz = 132 if len(txt) <= 7 else (104 if len(txt) <= 11 else 84)
            _st(d, (X, y + 20 * (1 - r)), txt, font=F("Heavy", sz), fill=(*col, int(255 * r)))
            y += _height(b, False)
        elif k == "chart":
            _chart(im, b, p); y = max(y, b["y"] + b["h"] + 90)
        elif k == "bars":
            _bars(im, b, p, y); y += _height(b, False)
        elif k == "pct":
            _pct(im, b, p, y); y += _height(b, False)
    return im.convert("RGB")


def _height(b, first):
    k = b["kind"]
    if k == "print": return 64 if first else 66
    if k == "write":
        txt = b.get("text") or "".join(b.get("rows") or []); return 160 if len(txt) <= 7 else (130 if len(txt) <= 11 else 110)
    if k == "bars": return b.get("h", 380) + 200
    if k == "pct": return 470
    return 0


def _chart(im, b, p):
    s = np.array(b["series"], np.float32); lo, hi = b.get("lo", float(s.min())), b.get("hi", float(s.max())); n = len(s)
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    xs = np.array(b.get("xs") or list(range(n)), np.float32); xs = (xs - xs[0]) / max(xs[-1] - xs[0], 1e-6)
    P = [(x + w * xx, y + h - (v - lo) / max(hi - lo, 1e-6) * h) for xx, v in zip(xs, s)]
    i0, i1 = b.get("from", 0), b.get("to", n - 1); dur = b.get("dur", 2.0)
    d = ImageDraw.Draw(im, "RGBA"); ga = eout(p / .4)
    for k in range(1, 5):   # 옅은 눈금선
        yy = y + h - k * h / 5; d.line([(x, yy), (x + w * ga, yy)], fill=(255, 255, 255, 26), width=1)
    d.line([(x, y + h), (x + w * ga, y + h)], fill=(255, 255, 255, 100), width=2)
    q = eio(p / dur); f = i0 + q * (i1 - i0); kk = int(f); r = f - kk; k1 = min(kk + 1, i1)
    pts = P[i0:kk + 1] + [(P[kk][0] + (P[k1][0] - P[kk][0]) * r, P[kk][1] + (P[k1][1] - P[kk][1]) * r)]
    if len(pts) > 1:   # 아래 금색 옅은 면
        ov = Image.new("RGBA", im.size); ImageDraw.Draw(ov).polygon(pts + [(pts[-1][0], y + h), (pts[0][0], y + h)], fill=(*GOLD, 36)); im.alpha_composite(ov)
    _glow_line(im, pts, WHITE, 5)
    d = ImageDraw.Draw(im, "RGBA")
    hx, hy = pts[-1]
    if q < 1:   # 그려지는 머리점
        ov = Image.new("RGBA", im.size); ImageDraw.Draw(ov).ellipse([hx - 18, hy - 18, hx + 18, hy + 18], fill=(*WHITE, 200)); im.alpha_composite(ov.filter(ImageFilter.GaussianBlur(8)))
        d = ImageDraw.Draw(im, "RGBA"); d.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=WHITE)
    lab = {int(k): v for k, v in (b.get("labels") or {}).items()}
    for i in range(i0, i1 + 1):
        if i > f + 1e-6: break
        px, py = P[i]; last = i == i1
        if last and q >= 1:
            pr = (p - dur) % 1.6 / 1.6   # 끝점: 금색 점 + 퍼지는 고리
            rr = 14 + 30 * pr; d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=(*GOLD, int(180 * (1 - pr))), width=3)
            d.ellipse([px - 12, py - 12, px + 12, py + 12], fill=GOLD)
        else: d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=WHITE)
        if i in lab:
            la = eout((p - dur * (i - i0) / max(1, i1 - i0)) / .4)
            right = px > x + w * .6
            col = GOLD if last else WHITE
            if right: d.text((px - 18, py - 26), lab[i], font=F("Bold", 32), fill=(*col, int(255 * la)), anchor="rd")
            else: d.text((px, py + 24), lab[i], font=F("SemiBold", 30), fill=(*col, int(255 * la)), anchor="ma")
    for tx, tl in (b.get("ticks") or []):   # 아래 날짜
        d.text((x + w * tx, y + h + 18), tl, font=F("Medium", 28), fill=(*GRAY, int(255 * ga)), anchor="ma")


def _bars(im, b, p, y):
    it = b["items"]; x = b.get("x", 150); h = b.get("h", 380); base = y + 120 + h; vmax = max(abs(i["v"]) for i in it)
    d = ImageDraw.Draw(im, "RGBA")
    d.line([(x - 20, base), (x - 20 + 300 * len(it) * eout(p / .4), base)], fill=(255, 255, 255, 110), width=2)
    for k, i in enumerate(it):
        q = eout((p - .15 - k * .35) / .9)
        if q <= 0: continue
        bx = x + k * 300; bh = h * i["v"] / vmax * q; col = TONE.get(i.get("color"), WHITE) if i.get("color") not in (None, "ink") else WHITE
        if i.get("color") == "gray": col = GRAY
        alpha = 235 if k == 0 else 150
        d.rectangle([bx, base - bh, bx + 120, base], fill=(*col, alpha))
        n = _num_k(i.get("text", ""), q)
        d.text((bx, base - bh - 18), n, font=F("Heavy", 60), fill=(*col, 255), anchor="ld")
        d.text((bx, base + 18), i["label"], font=F("Medium", 28), fill=(*GRAY, 255))


def _num_k(text, q):
    """'23.5조' 같은 숫자를 막대와 함께 세어 올린다"""
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(.*)", text.strip())
    if not m: return text
    s = m.group(1); dec = len(s.split(".")[1]) if "." in s else 0
    return f"{float(s) * q:,.{dec}f}{m.group(2)}"


def _pct(im, b, p, y):
    """등락률 막대: items [{"label","v"(%), "mark":"실적 발표"}] — 가운데 기준선 아래로(하락 빨강)·위로(상승 초록)"""
    it = b["items"]; x = b.get("x", 150); mid = y + 210; sc = b.get("scale", 26)   # 1% = 26px
    d = ImageDraw.Draw(im, "RGBA"); ga = eout(p / .4)
    d.line([(x - 10, mid), (x - 10 + 260 * len(it) * ga, mid)], fill=(255, 255, 255, 110), width=2)
    d.text((x - 10, mid - 12), "0%", font=F("Medium", 24), fill=(*GRAY, int(200 * ga)), anchor="rd")
    for k, i in enumerate(it):
        q = eout((p - .2 - k * .45) / .8)
        bx = x + k * 260
        if i.get("mark") and q > 0:
            d.line([(bx + 60, mid - 200), (bx + 60, mid + 230)], fill=(*GOLD, int(200 * q)), width=2)
            d.text((bx + 74, mid - 200), i["mark"], font=F("Medium", 26), fill=(*GOLD, int(255 * q)))
        if q <= 0: continue
        v = i["v"]; col = RED if v < 0 else GREEN; bh = abs(v) * sc * q
        y0, y1 = (mid, mid + bh) if v < 0 else (mid - bh, mid)
        d.rectangle([bx + 10, y0, bx + 110, y1], fill=(*col, 230))
        lab = f"{v * q:+.1f}%"
        d.text((bx + 120, (y1 + 8) if v < 0 else (y0 - 8), ), lab, font=F("Heavy", 56), fill=(*col, 255), anchor="la" if v < 0 else "ld")
        d.text((bx + 60, mid + (-40 if v < 0 else 18)), i["label"], font=F("Medium", 28), fill=(*GRAY, 255), anchor="md" if v < 0 else "ma")
