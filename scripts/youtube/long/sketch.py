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
import math, os, sys  # noqa: E401
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
    """장면의 비트 목록 → 시간이 정해진 비트 객체들 (장면 안 초). lines = [(시작, 길이, 문장), ...]
    비트에 "t"(장면 안 초)가 있으면 line/at 대신 그 시각에 그린다 (자동 변환이 쓴다)"""
    out = []
    for b in beats_spec or []:
        if b.get("kind") in ("write", "check"):   # 손글씨 글꼴에 없는 기호 바꾸기
            fx = lambda x: str(x).replace("·", "/").replace("≈", "약 ").replace("→", "->")
            b = dict(b)
            if "text" in b: b["text"] = fx(b["text"])
            if "rows" in b: b["rows"] = [fx(r) for r in b["rows"]]
        if "t" in b:
            t0 = float(b["t"]); d = b.get("dur") or IW.DUR.get(b["kind"])
            if d is None:
                n = len("".join(b.get("rows") or [b.get("text", "")]).replace(" ", "")); d = IW.clamp(.13 * n + .25, .45, 1.6)
            t1 = t0 + d
        else:
            t0, t1 = IW.beat_time(b, lines, {"start": 0.0})
        bb = IW.make_beat(b, t0, t1)
        out += bb if isinstance(bb, list) else [bb]
    return out


NUM = __import__("re").compile(r"[+\-−]?\d[\d,.]*\s?(?:조|억|만|천)?(?:\s?\d[\d,]*\s?(?:억|만|천))?\s?(?:원|달러|%p|%|배|명|곳|분기|분|년|개월|시간|점|개|번)")


def _free_spot(boxes, w, h):
    """빈자리 찾기: 위에서 아래로, 왼쪽에서 오른쪽으로 훑어 다른 그림과 겹치지 않는 첫 자리"""
    for y in range(150, 880 - h, 30):
        for x in range(130, 1860 - w, 40):
            if all(x + w < b[0] - 24 or x > b[2] + 24 or y + h < b[1] - 14 or y > b[3] + 14 for b in boxes): return x, y
    return None


def notes(beats, lines, dur, gap=2.4, authored=(), at_time=None):
    """빈자리에 손글씨 메모를 적는다.
    1) 원고의 "notes": [[문장 번호, "그 문장 속 단어", "적을 말", 색(선택)], ...] — 기획 단계에서 정한 짧은 메모. 자리는 자동으로 찾는다.
       적을 말이 "@cup" 처럼 @로 시작하면 그 그림 기호를 그린다.
    2) 그래도 펜이 멈추는 문장: 그 문장의 숫자(예: 25달러)를 적는다 — 이미 쓴 숫자는 다시 쓰지 않는다"""
    add = []
    def place(txt, t, color):
        if txt.startswith("@"):
            sz = 110; spot = _free_spot([z.bbox() for z in beats + add], sz + 20, sz + 20)
            if spot: add.append(IW.make_beat(dict(kind="icons", icon=txt[1:], x=spot[0], y=spot[1], size=sz, n=1, color=color or "ink"), t, t + .5))
            return
        size = 80; w = int(sum(.62 if ord(c) > 0x3000 else .42 for c in txt) * size) + 30
        spot = _free_spot([z.bbox() for z in beats + add], w, size + 10)
        if not spot: return
        txt = txt.replace("·", "/").replace("→", "->")
        add.append(IW.make_beat(dict(kind="write", text=txt, x=spot[0], y=spot[1], size=size, color=color or "ink"), t, t + IW.clamp(.13 * len(txt.replace(" ", "")) + .25, .45, 1.4)))
    for n in sorted(authored, key=lambda n: (n[0], 0)):
        i = min(int(n[0]), len(lines) - 1); a, d, txt = lines[i]
        t = at_time(f"{i}:{n[1]}", lines) if (n[1] and at_time) else a + .05
        place(str(n[2]), t, n[3] if len(n) > 3 else None)
    written = "".join("".join(b.b.get("rows") or [b.b.get("text", "")]) for b in beats + add if isinstance(b, (IW.Write, IW.Print))).replace(" ", "")
    for i, (a, d, txt) in enumerate(lines):
        if not any(q - p > gap for p, q in idle(beats + add, a, a + d)): continue
        for m in NUM.finditer(txt):
            ph = m.group().strip()
            if ph.replace(" ", "") in written or __import__("re").fullmatch(r"\d{4}\s?년", ph): continue
            t = a + d * (m.start() / max(1, len(txt))) * .95
            if not any(p - .2 <= t <= q for p, q in idle(beats + add, a, a + d)): continue
            place(ph, t, "red" if ph.startswith(("-", "−")) else "gold"); written += ph.replace(" ", "")
    return beats + add


def autofill(beats, lines, dur, gap=2.4):
    """말하는 동안 2.4초 넘게 새 그림이 없으면, 이미 쓴 핵심(숫자 손글씨 먼저)에 펜이 밑줄을 한 번 긋는다.
    2026-10-27 운영자: "펜을 너무 많이 긋는다, 핵심만" · "선이 다른 글자와 겹쳐 보인다" →
    형광펜·동그라미는 자동으로 더하지 않고, 대상마다 밑줄 한 번만, 다른 글자와 겹치는 자리면 긋지 않는다"""
    add = []; start = lines[0][0] if lines else 0.0; end = min(dur - .3, (lines[-1][0] + lines[-1][1]) if lines else dur)
    import re as _re
    def text(z): return "".join(z.b.get("rows") or [z.b.get("text", "")])
    def tight(z):   # 손글씨 비트의 실제 글자 상자 (아래 여백 30px 제외)
        x0, y0, x1, y1 = [float(v) for v in z.bbox()]
        return (x0, y0, x1, y1)   # 잉크 노트 Write.bbox 는 이미 글자에 딱 맞는 상자
    def key(z): return isinstance(z, IW.Write) and len(text(z).strip()) > 1 and (_re.search(r"\d", text(z)) or z.b.get("color") in ("red", "gold"))
    def clear(z, band):
        for o in beats + add:
            if o is z or getattr(o, "b", {}).get("_on") is z: continue
            if isinstance(o, IW.Stroke) and not o.b.get("_auto"): continue
            ox0, oy0, ox1, oy1 = tight(o) if not isinstance(o, IW.Stroke) else [float(v) for v in o.bbox()]
            if not (band[2] < ox0 or band[0] > ox1 or band[3] < oy0 or band[1] > oy1): return False
        return True
    done = set()
    for _ in range(12):
        g = next(((p, q) for p, q in idle(beats + add, start, end) if q - p > gap), None)
        if not g: break
        t = g[0] + min(1.0, (g[1] - g[0]) / 2); pick = None
        for z in sorted([z for z in beats if key(z) and id(z) not in done and z.t1 <= t + .05], key=lambda z: -z.t0):
            x0, y0, x1, y1 = tight(z); band = (x0 + 6, y1, min(x1, 1860), y1 + 18)
            if band[3] < 890 and clear(z, band): pick = (z, band); break
            done.add(id(z))
        if not pick: break
        z, band = pick; done.add(id(z))
        nb = IW.Stroke({"kind": "under", "color": "gold", "_auto": 1}, t, t + .45, IW.under_pts(band[0], band[2], band[1] + 6), 8)
        nb.b["_on"] = z; add.append(nb)
    return beats + add


# ── 자동 변환: 기존 원고의 화면 종류 → 손글씨 페이지 (2026-10-27 운영자 승인: 자동 변환 + 빈틈 메우기 + 핵심 그림만 손으로) ──
AUTO_TYPES = {"media", "stat", "checklist", "question", "bars", "hbars", "card", "quote", "timeline", "kinetic", "twocol", "scale", "table"}
LIB = "scripts/blog/media/lib/"


def rows(t, n=11):
    """손글씨 줄 나누기: 띄어쓰기 기준으로 한 줄 n글자 안팎"""
    out, cur = [], ""
    for w in str(t).replace("\n", " ").split():
        if cur and len(cur) + 1 + len(w) > n: out.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    if cur: out.append(cur)
    return out or [""]


def tone(s):
    s = str(s).strip()
    return "red" if s.startswith(("-", "−")) else ("green" if s.startswith("+") else "red")


def auto(v, lines, V, fill, at_time):
    """v: 원고 화면, lines: [(시작, 길이, 문장)], fill: 빈칸 채우기, at_time: "1:단어" → 장면 안 초"""
    F = lambda x: fill(str(x), V) if x is not None else ""
    T = lambda at, d=0.0: at_time(at, lines) if at not in (None, "") else (lines[0][0] + d if lines else d)
    def LS(at):   # 그 단어가 있는 문장이 시작하는 때 (틀·이름표는 문장 시작에 먼저 그린다)
        try: i = min(int(str(at).partition(":")[0] or 0), len(lines) - 1)
        except ValueError: i = 0
        return lines[i][0] + .05 if lines else 0.0
    S0 = (lines[0][0] + .05) if lines else 0.0
    t = v["type"]; B = []
    def photo(src, x, y, w, h, rot, tt, cap=None):
        if not src or not os.path.exists(os.path.join(IW.ROOT, LIB + src)): return
        d = dict(kind="photo", src=LIB + src, x=x, y=y, w=w, h=h, rot=rot, t=tt)
        if cap: d["cap"] = cap
        B.append(d)
    def title(txt, tt=None):
        tt = S0 if tt is None else tt
        if txt: B.append(dict(kind="print", text=F(txt), x=120, y=90, size=46, w="ExtraBold", t=tt))
    if t == "media":
        photo(v.get("lib"), 90, 100, 1000, 690, -2, S0)
        y = 130
        if v.get("caption"):
            r = rows(F(v["caption"]), 8); B.append(dict(kind="write", rows=r, x=1170, y=y, size=96, t=T(v.get("caption_at", "0")) + .1)); y += 100 * len(r) + 60
        for i, ch in enumerate(v.get("chips", [])):
            tt = T(ch.get("at")); B.append(dict(kind="write", rows=rows(F(ch.get("l", "")), 12), x=1175, y=y + 150, size=52, color="gray", t=LS(ch.get("at"))))
            B.append(dict(kind="write", text=F(ch["v"]), x=1170, y=y, size=130, color="red", t=tt)); y += 290
    elif t == "stat":
        if v.get("backdrop"): photo(v["backdrop"], 1180, 140, 640, 460, 3, S0)
        if v.get("kicker"): B.append(dict(kind="print", text=F(v["kicker"]), x=140, y=110, size=42, w="Bold", color="gray", t=S0))
        val = F(v["value"]); ta = T(v.get("at")); B.append(dict(kind="write", text=val, x=140, y=180, size=300, color=tone(val), t=ta))
        B.append(dict(kind="under", x0=150, x1=150 + int(len(val) * 300 * .5), y=500, color="gold", t=ta + .7))
        if v.get("label"): B.append(dict(kind="write", text=F(v["label"]), x=150, y=540, size=84, t=ta + .4))
        for j, tg in enumerate(v.get("tags", [])): B.append(dict(kind="write", text=F(tg["text"]), x=150, y=680 + j * 90, size=66, color="gold", t=T(tg.get("at"))))
    elif t == "question":
        if v.get("backdrop"): photo(v["backdrop"], 1220, 140, 600, 430, 3, S0)
        r = rows(F(v["text"]), 9); B.append(dict(kind="write", rows=r, x=140, y=180, size=120, t=S0 + .1))
        B.append(dict(kind="write", text="?", x=1000, y=150, size=320, color="red", t=S0 + .3 + .13 * len("".join(r))))
    elif t == "checklist":
        title(v.get("title"))
        if v.get("backdrop"): photo(v["backdrop"], 1320, 120, 500, 360, 3, S0)
        for i, it in enumerate(v["items"]): B.append(dict(kind="check", text=F(it[0]), x=140, y=220 + i * 170, size=64, t=T(it[1]) if len(it) > 1 else .3 + i))
    elif t == "bars":
        title(v.get("title")); its = v["items"]; vmax = max(float(i[1]) for i in its); n = len(its)
        if v.get("unit"): B.append(dict(kind="print", text="단위: " + F(v["unit"]), x=1800, y=100, size=32, w="Medium", color="gray", anchor="ra", t=S0))
        for i, it in enumerate(its):
            sp = min(700, 1400 / n)
            B.append(dict(kind="bar", x=int(960 - sp * (n - 1) / 2 + i * sp - 100), base=800, w=200, hmax=420, v=float(it[1]), vmax=vmax,
                          text=F(it[4]) if len(it) > 4 else str(it[1]), label=F(it[0]).replace("\n", " "), color="gold" if (len(it) > 3 and it[3]) else "ink", t=T(it[2]) if len(it) > 2 else .3 + i))
    elif t == "hbars":
        title(v.get("title")); its = v["items"]; vmax = max(float(i[1]) for i in its); hl = {h["i"]: h for h in v.get("hl", [])}
        for i, it in enumerate(its):
            tt = T(it[2]) if len(it) > 2 else .3 + i; y = 200 + i * 240
            B.append(dict(kind="write", text=F(it[0]), x=140, y=y, size=66, t=LS(it[2]) if len(it) > 2 else S0))
            B.append(dict(kind="hbar", x=150, y=y + 90, h=66, wmax=1150, v=float(it[1]), vmax=vmax, text=F(it[3]) if len(it) > 3 else "", color="gold" if i in hl else "ink", t=tt))
            if i in hl: B.append(dict(kind="circle", cx=150 + 1150 * float(it[1]) / vmax + 200, cy=y + 123, rx=230, ry=62, color="red", t=T(hl[i].get("at"))))
    elif t == "card":
        if v.get("kicker"): B.append(dict(kind="print", text=F(v["kicker"]), x=140, y=100, size=42, w="Bold", color="red", t=S0))
        B.append(dict(kind="write", text=F(v.get("title", "")), x=140, y=170, size=110, t=T(v.get("at")) + .1))
        for i, r in enumerate(v.get("rows", [])): B.append(dict(kind="check", text=F(r[0]), x=160, y=380 + i * 160, size=62, t=T(r[1]) if len(r) > 1 else .5 + i))
    elif t == "quote":
        if v.get("backdrop"): photo(v["backdrop"], 1220, 140, 600, 430, 3, S0)
        r = rows("“" + F(v["text"]) + "”", 10); ta = T(v.get("at")); B.append(dict(kind="write", rows=r, x=140, y=180, size=110, t=ta))
        B.append(dict(kind="print", text="— " + F(v.get("who", "")), x=150, y=200 + 112 * len(r) + 30, size=40, w="Bold", color="gray", t=T(v.get("who_at")) if v.get("who_at") else ta + 1))
    elif t == "timeline":
        title(v.get("title")); pts = v["points"]; n = len(pts)
        B.append(dict(kind="under", x0=160, x1=1760, y=580, color="ink", t=S0 + .2, dur=.6))
        for i, pnt in enumerate(pts):
            x = int(300 + i * (1300 / max(1, n - 1))) if n > 1 else 960; tt = T(pnt.get("at")); c = pnt.get("color", "ink")
            c = {"gold": "gold", "red": "red", "green": "green"}.get(c, "ink")
            B.append(dict(kind="circle", cx=x, cy=578, rx=16, ry=16, color=c, t=tt, dur=.3))
            B.append(dict(kind="write", rows=rows(F(pnt["text"]), 7), x=x, y=330, size=92, color=c, anchor="m", t=tt + .1))
            B.append(dict(kind="print", text=F(pnt["x"]), x=x, y=620, size=36, w="Bold", color="gray", anchor="ma", t=tt))
    elif t == "kinetic":
        if v.get("backdrop"): photo(v["backdrop"], 1220, 140, 600, 430, 3, S0)
        y = 160
        for wd in v["words"]:
            sz = min(150, int(wd.get("size", 90) * 1.05)); c = {"acc": "red", "muted": "gray"}.get(wd.get("c"), "ink"); tt = T(wd.get("at"))
            B.append(dict(kind="write", text=F(wd["t"]), x=140, y=y, size=sz, color=c, t=tt))
            if wd.get("under"): B.append(dict(kind="under", x0=150, x1=150 + int(len(F(wd["t"])) * sz * .5), y=y + sz + 6, color="gold", t=tt + .6))
            y += int(sz * 1.25)
    elif t == "twocol":
        title(v.get("title"))
        for side, x, c in (("left", 140, "ink"), ("right", 1000, "gold")):
            col = v.get(side) or {}; tt = T(col.get("at"))
            B.append(dict(kind="write", text=F(col.get("title", "")), x=x, y=200, size=64, color="gray", t=tt))
            for j, it in enumerate(col.get("items", [])):
                B.append(dict(kind="write", text=F(it[0]), x=x, y=330 + j * 140, size=96, color="gold" if col.get("gold") else c, t=T(it[1]) + .1 * j if len(it) > 1 else tt + .5 + j))
    elif t == "scale":
        title(v.get("title"))
        for side, x in (("left", 200), ("right", 1060)):
            c = v.get(side) or {}; tt = T(c.get("at"))
            B.append(dict(kind="print", text=F(c.get("label", "")).replace("\n", " "), x=x, y=240, size=44, w="Bold", color="gray", t=tt))
            B.append(dict(kind="write", text=F(c.get("value", "")), x=x, y=310, size=170, color={"gold": "gold", "red": "red"}.get(c.get("color"), "ink"), t=tt + .1))
        ce = v.get("center")
        if ce:
            tt = T(ce.get("at")); B.append(dict(kind="write", text=F(ce["text"]), x=760, y=600, size=130, color="red", t=tt))
            B.append(dict(kind="circle", cx=960, cy=690, rx=300, ry=95, color="red", t=tt + .8))
    elif t == "table":
        title(v.get("title")); cw = v.get("cw", [700, 600]); x2 = 140 + cw[0] + 60
        for j, c in enumerate(v.get("cols", [])): B.append(dict(kind="print", text=F(c), x=140 if j == 0 else x2, y=190, size=36, w="Bold", color="gray", t=S0))
        for i, r in enumerate(v["rows"]):
            tt = T(r[2]) if len(r) > 2 else .3 + i; y = 260 + i * 170
            B.append(dict(kind="write", text=F(r[0]), x=140, y=y, size=74, t=tt)); B.append(dict(kind="write", text=F(r[1]), x=x2, y=y, size=74, color="red", t=tt + .5))
            if v.get("hl") == i: B.append(dict(kind="hl", x0=130, y0=y + 20, x1=x2 + 600, y1=y + 95, color="yellow", t=tt + 1.0))
    return B


def apply(arr, beats, u):
    """arr: 장면 그림 (H, W, 3) uint8 — 지금(u초)까지 그려진 비트를 얹는다. 펜촉 위치(없으면 None)를 돌려준다"""
    tip = None
    for b in beats:
        if b.t0 <= u: b.apply(arr, u)
        if b.pen and b.t0 - .05 <= u <= b.t1 + .1:
            try: tip = b.tip(min(u, b.t1))
            except Exception: pass
    return tip


def idle(beats, a, b):
    """a~b초 사이 펜이 아무것도 그리지 않는 구간들 (그리는 중인 비트는 움직임으로 친다)"""
    iv = sorted((max(a, z.t0), min(b, z.t1 + .4)) for z in beats if z.t1 + .4 > a and z.t0 < b)
    out = []; cur = a
    for x, y in iv:
        if x > cur: out.append((cur, x))
        cur = max(cur, y)
    if cur < b: out.append((cur, b))
    return out


def gaps(beats, lines, extra=(), lim=2.6):
    """문장마다 새로 그려지는 것이 있는지, lim초 넘게 펜이 멈춘 구간이 있는지 (장면 안 초)"""
    out = []
    for i, (a, d, txt) in enumerate(lines):
        if not any(a - .2 <= z.t0 <= a + d for z in beats): out.append(f"문장 {i}: 새 그림 없음 · {txt[:24]}")
        for p, q in idle(beats, a, a + d):
            if q - p > lim: out.append(f"문장 {i}: {p:.1f}~{q:.1f}초 멈춤 · {txt[:24]}")
    return out


def scene_beats(sc, lines, V, fill, at_time, auto_ok=True):
    """장면 하나의 손그림: 원고에 sketch 가 있으면 그것(핵심 그림), 없으면 화면 종류를 자동 변환. 마지막에 빈틈 메우기"""
    spec = sc.get("sketch")
    if spec is None and auto_ok and sc["v"]["type"] in AUTO_TYPES: spec = auto(sc["v"], lines, V, fill, at_time) + list(sc.get("sketch_add", []))
    if spec is None: return None
    dur = (lines[-1][0] + lines[-1][1] + .35) if lines else 1.0
    return autofill(notes(build(spec, lines), lines, dur, authored=[n for n in sc.get("notes", [])], at_time=at_time), lines, dur)
