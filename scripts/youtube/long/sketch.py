"""취재 노트 손그림 (2026-10-27 운영자: "말하는 동안 스케치북이 비어 있지 말고, 그걸 설명하거나 그려 줘. 빈틈없이 계속 뭔가를 보여 달라")

원고 장면에 "sketch": [비트, ...] 를 넣으면, 성우가 말하는 순간에 맞춰 노트 종이에 펜으로 그려진다.
화면 종류를 "v": {"type": "sketch"} 로 두면 빈 종이에서 시작해 비트만으로 장면을 만든다(다른 화면 종류 위에 얹어도 된다).
비트 형식은 쇼츠의 잉크 노트(scripts/reels/inkworld.py)와 같다. 좌표만 가로 화면(1920x1080) 기준.
  공통: "line": 몇 번째 문장(0부터), "at": 그 문장 안 위치(0~1), "dur": 그리는 시간(초, 선택)
  write(손글씨) · print(인쇄 글씨) · under · circle · cross · arrow · hl(형광펜) · photo(테이프 사진) · icons · check · chart
  이 파일에서 더한 것:
   - bar   세로 막대 하나: x, base(바닥 y), w, hmax, v, vmax, text(위 손글씨), label(아래), color
   - hbar  가로 막대 하나: x, y, h, wmax, v, vmax, text(오른쪽 손글씨), color
   - icons 의 그림 기호 추가: phone · jar(동전 저금통) · gift · store · bank · ledger(장부) · giftcard · drawer · coin · clock · cart
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "reels"))
import inkworld as IW  # noqa: E402

_base_icon = IW.icon_draw


def icon_draw(d, kind, x, y, s, c, w=4):
    L = lambda pts: d.line(pts, fill=c, width=w, joint="curve")
    if kind == "phone":
        d.rounded_rectangle([x + s * .27, y + s * .02, x + s * .73, y + s * .98], int(s * .07), outline=c, width=w)
        d.rectangle([x + s * .32, y + s * .12, x + s * .68, y + s * .82], outline=c, width=max(2, w - 1))
        d.ellipse([x + s * .47, y + s * .86, x + s * .53, y + s * .92], outline=c, width=max(2, w - 1))
    elif kind == "jar":   # 동전이 든 병
        d.rounded_rectangle([x + s * .15, y + s * .25, x + s * .85, y + s * .97], int(s * .12), outline=c, width=w)
        d.rectangle([x + s * .25, y + s * .08, x + s * .75, y + s * .25], outline=c, width=w)
        for k, (cx, cy) in enumerate(((.35, .8), (.55, .82), (.45, .65), (.65, .66), (.4, .5))):
            d.ellipse([x + s * (cx - .09), y + s * (cy - .06), x + s * (cx + .09), y + s * (cy + .06)], outline=c, width=max(2, w - 1))
    elif kind == "gift":
        d.rectangle([x + s * .12, y + s * .4, x + s * .88, y + s * .95], outline=c, width=w)
        d.rectangle([x + s * .06, y + s * .28, x + s * .94, y + s * .4], outline=c, width=w)
        L([(x + s * .5, y + s * .28), (x + s * .5, y + s * .95)])
        d.arc([x + s * .22, y + s * .08, x + s * .5, y + s * .32], 180, 20, fill=c, width=w); d.arc([x + s * .5, y + s * .08, x + s * .78, y + s * .32], 160, 360, fill=c, width=w)
    elif kind == "store":
        d.rectangle([x + s * .1, y + s * .42, x + s * .9, y + s * .97], outline=c, width=w)
        for k in range(5):   # 차양
            d.arc([x + s * (.1 + k * .16), y + s * .3, x + s * (.26 + k * .16), y + s * .5], 0, 180, fill=c, width=w)
        L([(x + s * .1, y + s * .4), (x + s * .18, y + s * .18), (x + s * .82, y + s * .18), (x + s * .9, y + s * .4)])
        d.rectangle([x + s * .42, y + s * .66, x + s * .58, y + s * .97], outline=c, width=w)
    elif kind == "bank":
        d.polygon([(x + s * .5, y + s * .05), (x + s * .95, y + s * .3), (x + s * .05, y + s * .3)], outline=c, width=w)
        for k in range(4): L([(x + s * (.2 + k * .2), y + s * .38), (x + s * (.2 + k * .2), y + s * .82)])
        L([(x + s * .05, y + s * .88), (x + s * .95, y + s * .88)])
    elif kind == "ledger":
        d.rectangle([x + s * .12, y + s * .08, x + s * .88, y + s * .95], outline=c, width=w)
        L([(x + s * .3, y + s * .08), (x + s * .3, y + s * .95)])
        for k in range(5): L([(x + s * .38, y + s * (.25 + k * .14)), (x + s * .8, y + s * (.25 + k * .14))])
    elif kind == "giftcard":
        d.rounded_rectangle([x + s * .05, y + s * .22, x + s * .95, y + s * .8], int(s * .08), outline=c, width=w)
        d.ellipse([x + s * .14, y + s * .32, x + s * .34, y + s * .52], outline=c, width=max(2, w - 1))
        L([(x + s * .5, y + s * .62), (x + s * .85, y + s * .62)])
    elif kind == "drawer":
        d.rectangle([x + s * .05, y + s * .15, x + s * .95, y + s * .9], outline=c, width=w)
        L([(x + s * .05, y + s * .52), (x + s * .95, y + s * .52)])
        for yy in (.33, .71): L([(x + s * .4, y + s * yy), (x + s * .6, y + s * yy)])
    elif kind == "coin":
        d.ellipse([x + s * .1, y + s * .1, x + s * .9, y + s * .9], outline=c, width=w); d.ellipse([x + s * .22, y + s * .22, x + s * .78, y + s * .78], outline=c, width=max(2, w - 2))
    elif kind == "clock":
        d.ellipse([x + s * .08, y + s * .08, x + s * .92, y + s * .92], outline=c, width=w)
        L([(x + s * .5, y + s * .5), (x + s * .5, y + s * .22)]); L([(x + s * .5, y + s * .5), (x + s * .7, y + s * .6)])
    elif kind == "cart":
        L([(x + s * .02, y + s * .15), (x + s * .18, y + s * .15), (x + s * .3, y + s * .7), (x + s * .85, y + s * .7), (x + s * .95, y + s * .3), (x + s * .22, y + s * .3)])
        d.ellipse([x + s * .3, y + s * .78, x + s * .42, y + s * .9], outline=c, width=w); d.ellipse([x + s * .7, y + s * .78, x + s * .82, y + s * .9], outline=c, width=w)
    else:
        _base_icon(d, kind, x, y, s, c, w)


IW.icon_draw = icon_draw   # Icons 비트가 새 그림 기호도 그리게


class Bar(IW.Beat):
    """손으로 칠한 세로 막대 하나 (빗금 + 위에 손글씨 숫자)"""
    def bbox(self): b = self.b; return (b["x"], b["base"] - b["hmax"] - 90, b["x"] + b["w"], b["base"] + 70)
    def apply(self, tex, T):
        p = IW.eout(self.p(T))
        if p <= 0: return
        b = self.b; c = IW.col(b.get("color", "ink")); x, base, w = b["x"], b["base"], b["w"]; h = b["hmax"] * b["v"] / b["vmax"] * p
        im = Image.fromarray(tex); d = ImageDraw.Draw(im, "RGBA")
        d.rectangle([x, base - h, x + w, base], fill=(*c, 60), outline=(*c, 255), width=5)
        for yy in range(int(base - h) + 12, int(base), 20): d.line([(x + 5, yy + 12), (x + w - 5, yy - 8)], fill=(*c, 90), width=3)
        d.line([(x - 40, base), (x + w + 40, base)], fill=(*IW.INKC, 200), width=4)
        if b.get("label"): d.text((x + w / 2, base + 16), b["label"], font=IW.font("Bold", 34), fill=(*IW.INKC, 220), anchor="ma")
        if p > .85 and b.get("text"): d.text((x + w / 2, base - h - 12), b["text"], font=IW.font("pen", b.get("tsize", 72)), fill=(*c, 255), anchor="md")
        tex[:] = np.asarray(im)


class HBar(IW.Beat):
    """손으로 칠한 가로 막대 하나 (오른쪽 끝에 손글씨 숫자)"""
    def bbox(self): b = self.b; return (b["x"], b["y"], b["x"] + b["wmax"] + 420, b["y"] + b.get("h", 70))
    def apply(self, tex, T):
        p = IW.eout(self.p(T))
        if p <= 0: return
        b = self.b; c = IW.col(b.get("color", "ink")); x, y, hh = b["x"], b["y"], b.get("h", 70); w = max(8, b["wmax"] * b["v"] / b["vmax"] * p)
        im = Image.fromarray(tex); d = ImageDraw.Draw(im, "RGBA")
        d.rectangle([x, y, x + w, y + hh], fill=(*c, 60), outline=(*c, 255), width=5)
        for xx in range(int(x) + 14, int(x + w), 22): d.line([(xx - 10, y + hh - 5), (xx + 10, y + 5)], fill=(*c, 90), width=3)
        if p > .85 and b.get("text"): d.text((x + w + 22, y + hh / 2), b["text"], font=IW.font("pen", b.get("tsize", 70)), fill=(*c, 255), anchor="lm")
        tex[:] = np.asarray(im)


IW.KIND["bar"] = Bar; IW.KIND["hbar"] = HBar
IW.DUR.update({"bar": .9, "hbar": .9})


def build(beats_spec, lines):
    """장면의 비트 목록 → 시간이 정해진 비트 객체들 (장면 안 초). lines = [(시작, 길이, 문장), ...]"""
    out = []
    for b in beats_spec or []:
        t0, t1 = IW.beat_time(b, lines, {"start": 0.0})
        bb = IW.make_beat(b, t0, t1)
        out += bb if isinstance(bb, list) else [bb]
    return out


def apply(arr, beats, u):
    """arr: 장면 그림 (H, W, 3) uint8 — 지금(u초)까지 그려진 비트를 얹는다. 펜촉 위치(없으면 None)를 돌려준다"""
    tip = None
    for b in beats:
        if b.t0 <= u: b.apply(arr, u)
        if b.pen and b.t0 - .05 <= u <= b.t1 + .1:
            try: tip = b.tip(min(u, b.t1))
            except Exception: pass
    return tip


def gaps(beats, lines, extra=()):
    """문장마다 새로 그려지는 것이 있는지, 2.6초 넘게 아무 변화가 없는 구간이 있는지 (장면 안 초)"""
    ev = sorted([b.t0 for b in beats] + list(extra))
    out = []
    for i, (a, d, txt) in enumerate(lines):
        inside = [t for t in ev if a - .2 <= t <= a + d]
        if not inside: out.append(f"문장 {i}: 새 그림 없음 · {txt[:24]}")
        pts = [a] + inside + [a + d]
        for p, q in zip(pts, pts[1:]):
            if q - p > 2.6: out.append(f"문장 {i}: {p:.1f}~{q:.1f}초 멈춤 · {txt[:24]}")
    return out
