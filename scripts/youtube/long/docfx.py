"""다큐 스타일 화면 글씨·그래프 (2026-11-04 대표님: "흰 둥근 판은 덜 세련돼 보인다… 진짜 다큐같이", 시안 보고 "너무 좋아… 모션 그래픽 좀 넣어줘")

사진·영상 위에 판 없이 바로 그린다:
  · 사진 왼쪽을 남색으로 서서히 어둡게 (글씨가 나타날 때 0.5초에 걸쳐)
  · 첫 인쇄 글씨 = 키커: 금색 짧은 선이 그어지고 작은 금색 글씨가 옆에서 미끄러져 들어온다
  · 다음 인쇄 글씨 = 흰 글씨 한 줄 (아래에서 살짝 올라오며)
  · 손글씨(write) = 큰 굵은 숫자/문장 (숫자 하나면 0에서 세어 올라간다)
  · chart = 흰 선이 빛나는 머리점을 따라 그려지고, 아래는 금색 옅은 면, 끝점은 금색 점 + 퍼지는 고리
  · bars = 막대가 아래에서 자라고 숫자가 따라 올라간다
  · pct = 등락률 막대(가운데 기준선 위·아래), 표시 한 줄(marker)을 금색 세로선으로
  · punch = 핵심 숫자를 화면 가운데 크게 (쾅: 커졌다 줄며 박히고, 번쩍·흔들림, 숫자 세어 올라감 + 저음 타격음) — hold 초 뒤 사라진다
  · table = 2~3열 비교표 (머리줄 금색 선이 그어지고 줄마다 차례로 나타남 + 똑딱)
  · icon = 금색 선 아이콘 + 한 줄 글씨 (chip·bolt·dollar·building·server·warning·up·down·bank·globe)
  (2026-11-06 대표님: "글자만 쓰지 말고 아이콘/표/그림… 강조할 숫자는 화면 중간에 크게 효과음과… 시네마틱 이펙트를 많이")
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
    bs = [b for b in beats if b.get("kind") in ("print", "write", "chart", "bars", "pct", "table", "icon")]
    pu = [b for b in beats if b.get("kind") == "punch"]
    ov_ = [b for b in beats if b.get("kind") in ("stamp", "lower", "quote")]   # 2026-11-06 방송국 다큐 연출: 장소·날짜 도장, 하단 자막띠, 인용 카드
    if not bs and not pu and not ov_: return img
    if not bs:
        im = img.convert("RGBA")
        if ov_: im = _broadcast(im, ov_, u, lines)
        if pu: im = _punches(im, pu, u, lines)
        return im.convert("RGB")
    ts = [_t0(b, lines) for b in bs]
    g = eio((u - (min(ts) - .25)) / .5)
    if g <= 0:
        if not ov_ and not pu: return img
        im = img.convert("RGBA")
        if ov_: im = _broadcast(im, ov_, u, lines)
        if pu: im = _punches(im, pu, u, lines)
        return im.convert("RGB")
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
        elif k == "table":
            _table(im, b, p, y); y += _height(b, False)
        elif k == "icon":
            _icon_row(im, b, p, y); y += _height(b, False)
    if ov_: im = _broadcast(im, ov_, u, lines)
    if pu: im = _punches(im, pu, u, lines)
    return im.convert("RGB")


def _height(b, first):
    k = b["kind"]
    if k == "print": return 64 if first else 66
    if k == "write":
        txt = b.get("text") or "".join(b.get("rows") or []); return 160 if len(txt) <= 7 else (130 if len(txt) <= 11 else 110)
    if k == "bars": return b.get("h", 380) + 200
    if k == "pct": return 470
    if k == "table": return 96 + 84 * len(b.get("rows", [])) + 40
    if k == "icon": return 100
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
        lab = f"{v * q:+.{b.get('dec', 1)}f}%"
        d.text((bx + 120, (y1 + 8) if v < 0 else (y0 - 8), ), lab, font=F("Heavy", 56), fill=(*col, 255), anchor="la" if v < 0 else "ld")
        d.text((bx + 60, mid + (-40 if v < 0 else 18)), i["label"], font=F("Medium", 28), fill=(*GRAY, 255), anchor="md" if v < 0 else "ma")


# ───────── 2026-11-06 시네마틱: 숫자 펀치 · 비교표 · 아이콘 ─────────
PUNCH_HOLD = 2.4


def _broadcast(im, beats, u, lines):
    for b in beats:
        p = u - _t0(b, lines)
        if p < 0: continue
        k = b["kind"]
        if k == "stamp":   # 왼쪽 위 장소·날짜: 타자기처럼 한 글자씩 + 깜빡이는 커서, 5초 뒤 사라짐
            hold = b.get("hold", 5.0); fade = 1 - eio((p - hold) / .5)
            if fade <= 0: continue
            t = b["text"]; n = min(len(t), int(p / .045)); d = ImageDraw.Draw(im, "RGBA"); f = F("Bold", 30)
            sy = H - 290; d.rectangle([150, sy, 156, sy + 36], fill=(*RED, int(255 * fade)))
            _st(d, (172, sy), t[:n], font=f, fill=(*WHITE, int(235 * fade)))
            if n < len(t) or int(p * 2.2) % 2 == 0:
                cx = 172 + d.textlength(t[:n], font=f) + 4; d.rectangle([cx, sy + 4, cx + 14, sy + 34], fill=(*WHITE, int(200 * fade)))
        elif k == "lower":   # 하단 자막띠: 금색 세로선이 서고 이름·설명이 옆에서 밀려 들어온다
            hold = b.get("hold", 5.0); fade = 1 - eio((p - hold) / .5)
            if fade <= 0: continue
            y = H - 330; q = eout(p / .35); r = eout((p - .15) / .45); d = ImageDraw.Draw(im, "RGBA")
            bg = Image.new("RGBA", im.size); ImageDraw.Draw(bg).rectangle([120, y - 10, 120 + 900 * r, y + 120], fill=(8, 14, 26, int(170 * fade))); im.alpha_composite(bg)
            d = ImageDraw.Draw(im, "RGBA"); d.rectangle([120, y - 10 + 130 * (1 - q), 128, y + 120], fill=(*GOLD, int(255 * fade)))
            _st(d, (150 - 30 * (1 - r), y + 4), b["text"], font=F("Heavy", 50), fill=(*WHITE, int(255 * r * fade)))
            if b.get("sub"): _st(d, (150 - 30 * (1 - r), y + 68), b["sub"], font=F("SemiBold", 32), fill=(*GOLD, int(255 * r * fade)))
        elif k == "quote":   # 인용 카드: 화면을 어둡게, 큰 금색 따옴표, 한 줄씩 떠오르는 문장, 말한 사람
            a = np.asarray(im).astype(np.float32); g = eout(p / .5); a[..., :3] *= (1 - .62 * g); im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
            d = ImageDraw.Draw(im, "RGBA"); rows = b["rows"]; f = F("Bold", 66); y0 = H // 2 - 70 * len(rows) // 2 - 40
            d.text((W // 2, y0 - 70), "“", font=F("Heavy", 180), fill=(*GOLD, int(220 * g)), anchor="mm")
            for i, t in enumerate(rows):
                r = eout((p - .4 - i * .7) / .6)
                if r > 0: _st(d, (W // 2, y0 + 60 + i * 88 + 12 * (1 - r)), t, font=f, fill=(*WHITE, int(255 * r)), anchor="mm")
            r = eout((p - .5 - len(rows) * .7) / .5)
            if r > 0: _st(d, (W // 2, y0 + 80 + len(rows) * 88), "— " + b.get("by", ""), font=F("SemiBold", 38), fill=(*GOLD, int(255 * r)), anchor="mm")
    return im


def punch_times(beats, lines):
    """오디오용: (펀치 시각들, 표 줄 시각들, 아이콘 시각들) — 장면 안 시각(초)"""
    pt, tt, it = [], [], []
    for b in beats or []:
        k = b.get("kind")
        if k not in ("punch", "table", "icon"): continue
        t0 = _t0(b, lines)
        if k == "punch": pt.append(t0)
        elif k == "table": tt += [t0 + .35 + .45 * r for r in range(len(b.get("rows", [])))]
        else: it.append(t0)
    return pt, tt, it


def _numparts(text):
    """'3,000조' '-5.5%' '600조 원' → (앞, 값, 소수, 콤마, 뒤) / 없으면 None"""
    m = re.match(r"([+\-]?)(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(.*)$", text.strip())
    if not m: return None
    raw = m.group(2); dec = len(raw.split(".")[1]) if "." in raw else 0
    return m.group(1), float(raw.replace(",", "")), dec, "," in raw or float(raw.replace(",", "")) >= 1000, m.group(3)


def _punches(im, pu, u, lines):
    for b in pu:
        t0 = _t0(b, lines); p = u - t0; hold = b.get("hold", PUNCH_HOLD)
        if p < -0.05 or p > hold + .45: continue
        fade = 1 - eio((p - hold) / .45)
        col = _tone(b, WHITE); soft = b.get("style") == "soft"   # soft: 번쩍·흔들림·쾅 없이 조용히 떠오르는 약한 박자 (강약 조절, 2026-11-06)
        if soft: fade *= eout((p + .05) / .45)
        # 뒤 화면을 눌러 어둡게 (가운데 숫자에 집중)
        dk = eout((p + .05) / .2) * fade * (.7 if soft else 1)
        a = np.asarray(im).astype(np.float32)
        a[..., :3] *= (1 - .55 * dk)
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        txt = b["text"]; n = None if b.get("clock") else _numparts(txt)
        if b.get("clock") and p > -0.05:   # 2026-11-06 대표님: "00:00 → 24:00 빠르게 시간 올라가는 효과" — 시계처럼 세어 올라간다
            a_, b_ = (int(x) for x in txt.split(":")); tot = a_ * 60 + b_; v = int(round(tot * eout(max(0, p) / b.get("count", 1.0))))
            txt = f"{v // 60:02d}:{v % 60:02d}"
        if n and p > 0:
            c = eout(p / .7); v = n[1] * c
            body = f"{v:,.{n[2]}f}" if n[3] else f"{v:.{n[2]}f}"
            txt = f"{n[0]}{body}{n[4]}"
        sc = (1.0 + .55 * (1 - eout(p / .28)) if p < .28 else 1.0) if not soft else (0.82 + .04 * eout(p / 2.5))
        fs = int((230 if len(b["text"]) <= 7 else 180 if len(b["text"]) <= 11 else 140) * sc)
        fnt = F("Heavy", fs)
        cx, cy = W // 2, H // 2 - (30 if b.get("sub") else 0)
        al = int(255 * eout((p + .05) / .12) * fade)
        # 빛 번짐
        gl = Image.new("RGBA", im.size); ImageDraw.Draw(gl).text((cx, cy), txt, font=fnt, fill=(*col, int(al * .55)), anchor="mm")
        im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(22)))
        d = ImageDraw.Draw(im, "RGBA")
        d.text((cx + 4, cy + 6), txt, font=fnt, fill=(0, 0, 0, int(al * .6)), anchor="mm")
        d.text((cx, cy), txt, font=fnt, fill=(*col, al), anchor="mm")
        if b.get("sub"):
            r = eout((p - .35) / .4) * fade
            if r > 0:
                bb = d.textbbox((cx, cy), b["text"], font=F("Heavy", fs), anchor="mm")
                yy = bb[3] + 40; lw = 70 * r
                d.line([(cx - 40 - lw - 220, yy + 30), (cx - 220 - 40, yy + 30)], fill=(*GOLD, int(255 * r)), width=3)
                d.line([(cx + 260, yy + 30), (cx + 260 + lw, yy + 30)], fill=(*GOLD, int(255 * r)), width=3)
                _st(d, (cx, yy + 30 + 10 * (1 - r)), b["sub"], font=F("Bold", 50), fill=(*GOLD, int(255 * r)), anchor="mm")
        # 박히는 순간 번쩍 + 흔들림
        if soft: continue
        if 0 <= p < .16:
            fl = Image.new("RGBA", im.size, (255, 255, 255, int(110 * (1 - p / .16)))); im.alpha_composite(fl)
        if 0 <= p < .35:
            amp = 14 * (1 - p / .35); dx = int(amp * math.sin(p * 90)); dy = int(amp * .7 * math.cos(p * 77))
            im = im.transform(im.size, Image.AFFINE, (1, 0, dx, 0, 1, dy), resample=Image.BILINEAR)
    return im


def _table(im, b, p, y):
    cols = b["cols"]; rows = b.get("rows", []); x = b.get("x", 150); cw = b.get("cw", 430); n = len(cols)
    tc = [TONE.get(c, WHITE) for c in (b.get("colors") or [None] * n)]
    d = ImageDraw.Draw(im, "RGBA"); ga = eout(p / .35)
    for j, c in enumerate(cols):
        _st(d, (x + j * cw, y + 8), c, font=F("Bold", 40), fill=(*tc[j], int(255 * ga)))
    d.line([(x, y + 74), (x + (cw * n - 40) * eout(p / .5), y + 74)], fill=(*GOLD, 255), width=3)
    for r, row in enumerate(rows):
        q = eout((p - .35 - .45 * r) / .4)
        if q <= 0: continue
        yy = y + 96 + 84 * r
        for j, cell in enumerate(row):
            _st(d, (x + j * cw + 18 * (1 - q), yy), cell, font=F("SemiBold", 38), fill=(*(tc[j] if b.get("tint_cells") else WHITE), int(255 * q)))
        d.line([(x, yy + 70), (x + cw * n - 40, yy + 70)], fill=(255, 255, 255, int(40 * q)), width=1)
    if n > 1:   # 가운데 세로선
        for j in range(1, n):
            xx = x + j * cw - 30; d.line([(xx, y + 90), (xx, y + 90 + (84 * len(rows)) * ga)], fill=(255, 255, 255, 60), width=1)


def _icon(d, name, cx, cy, s, col, w=5):
    """간단한 선 아이콘 (s=반지름)"""
    c = (*col, 255) if len(col) == 3 else col
    if name == "chip":
        d.rounded_rectangle([cx - s * .6, cy - s * .6, cx + s * .6, cy + s * .6], radius=s * .12, outline=c, width=w)
        d.rectangle([cx - s * .25, cy - s * .25, cx + s * .25, cy + s * .25], outline=c, width=w - 1)
        for k in (-.3, 0, .3):
            for a, bb in ((cx + k * s, cy - s * .6), (cx + k * s, cy + s * .6)):
                d.line([(a, bb), (a, bb + (-s * .3 if bb < cy else s * .3))], fill=c, width=w - 1)
            for a, bb in ((cx - s * .6, cy + k * s), (cx + s * .6, cy + k * s)):
                d.line([(a, bb), (a + (-s * .3 if a < cx else s * .3), bb)], fill=c, width=w - 1)
    elif name == "bolt":
        d.polygon([(cx + s * .15, cy - s), (cx - s * .5, cy + s * .1), (cx - s * .02, cy + s * .1), (cx - s * .2, cy + s), (cx + s * .5, cy - s * .15), (cx + s * .02, cy - s * .15)], outline=c, width=w)
    elif name == "dollar":
        d.ellipse([cx - s * .9, cy - s * .9, cx + s * .9, cy + s * .9], outline=c, width=w)
        d.text((cx, cy + 2), "$", font=F("Heavy", int(s * 1.25)), fill=c, anchor="mm")
    elif name == "won":
        d.ellipse([cx - s * .9, cy - s * .9, cx + s * .9, cy + s * .9], outline=c, width=w)
        d.text((cx, cy + 2), "₩", font=F("Heavy", int(s * 1.1)), fill=c, anchor="mm")
    elif name == "building":
        d.rectangle([cx - s * .55, cy - s * .9, cx + s * .2, cy + s * .9], outline=c, width=w)
        d.rectangle([cx + s * .2, cy - s * .3, cx + s * .7, cy + s * .9], outline=c, width=w)
        for yy in (-.55, -.15, .25):
            d.line([(cx - s * .35, cy + yy * s), (cx, cy + yy * s)], fill=c, width=w - 1)
    elif name == "server":
        for k in (-.6, 0, .6):
            d.rounded_rectangle([cx - s * .8, cy + k * s - s * .25, cx + s * .8, cy + k * s + s * .25], radius=6, outline=c, width=w)
            d.ellipse([cx + s * .45, cy + k * s - 5, cx + s * .45 + 10, cy + k * s + 5], fill=c)
    elif name == "warning":
        d.polygon([(cx, cy - s * .9), (cx + s, cy + s * .8), (cx - s, cy + s * .8)], outline=c, width=w)
        d.line([(cx, cy - s * .3), (cx, cy + s * .25)], fill=c, width=w + 1); d.ellipse([cx - 5, cy + s * .45, cx + 5, cy + s * .45 + 10], fill=c)
    elif name in ("up", "down"):
        sg = -1 if name == "up" else 1
        pts = [(cx - s * .9, cy - sg * s * .6), (cx - s * .25, cy + sg * s * .05), (cx + s * .1, cy - sg * s * .25), (cx + s * .85, cy + sg * s * .6)]
        d.line(pts, fill=c, width=w + 1, joint="curve")
        ex, ey = pts[-1]; d.polygon([(ex, ey), (ex - s * .45, ey - sg * s * .02), (ex - s * .05, ey - sg * s * .42)], fill=c)
    elif name == "bank":
        d.polygon([(cx, cy - s * .95), (cx + s, cy - s * .45), (cx - s, cy - s * .45)], outline=c, width=w)
        for k in (-.6, -.2, .2, .6): d.line([(cx + k * s, cy - s * .3), (cx + k * s, cy + s * .6)], fill=c, width=w)
        d.line([(cx - s, cy + s * .8), (cx + s, cy + s * .8)], fill=c, width=w)
    elif name == "globe":
        d.ellipse([cx - s * .9, cy - s * .9, cx + s * .9, cy + s * .9], outline=c, width=w)
        d.ellipse([cx - s * .4, cy - s * .9, cx + s * .4, cy + s * .9], outline=c, width=w - 1)
        d.line([(cx - s * .9, cy), (cx + s * .9, cy)], fill=c, width=w - 1)
    else:
        d.ellipse([cx - s * .5, cy - s * .5, cx + s * .5, cy + s * .5], outline=c, width=w)


def _icon_row(im, b, p, y):
    x = b.get("x", 150); q = eout(p / .35); s = 34 * (.6 + .4 * q) if q < 1 else 34
    col = _tone(b, GOLD)
    ov = Image.new("RGBA", im.size); od = ImageDraw.Draw(ov, "RGBA")
    od.ellipse([x, y + 8, x + 84, y + 92], fill=(*col, int(40 * q)), outline=(*col, int(200 * q)), width=2)
    _icon(od, b.get("name", ""), x + 42, y + 50, s * .72, (*col, int(255 * q)), w=4)
    im.alpha_composite(ov)
    r = eout((p - .12) / .4)
    if r > 0 and b.get("text"):
        _st(ImageDraw.Draw(im, "RGBA"), (x + 110 - 20 * (1 - r), y + 22), b["text"], font=F("Bold", 44), fill=(*_tone({"color": b.get("text_color")}, WHITE), int(255 * r)))
