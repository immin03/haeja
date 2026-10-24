"""유튜브 롱폼 렌더러 v2 — 머니스웨거식 '빈 틀을 먼저 보여 주고 말에 맞춰 채우는' 화면 (1920x1080, 24fps)
사용: python3 scripts/youtube/long/render2.py <spec.json> [--fake-voice]
원고 형식(spec "format": 2):
  scenes: [{chapter?, bg: light|dark, src?, v: {type, ...}, lines: [문장, ...]}]
  화면 요소의 "at" = 그 요소가 나타나는 때: "2" (장면의 세 번째 문장이 시작할 때) / "2:29만" (그 문장에서 '29만'을 말하는 순간)
원칙 (2026-10-22 운영자 검수 + 머니스웨거 분석):
  - 화면은 시간이 아니라 '보여 줄 것'이 바뀔 때 바뀐다. 한 화면 안에서는 말에 맞춰 요소가 하나씩 채워진다.
  - 숫자를 말하는 동안 다른 사진으로 빠지지 않는다. 실사는 원고가 지정한 장면에만.
  - 설명은 밝은 모눈 배경, 질문·반전·장 제목은 네이비 배경. 자막은 아래 한 줄, 문장당 한 번.
"""
import json, math, os, re, subprocess, sys, datetime as dt
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from brand import paste_logo  # noqa: E402  (2026-10-23 확정 로고)
import render as R  # noqa: E402  (글꼴·자막·음성 속도·배경음악·사진 움직임을 함께 쓴다)
from render import F, AD, clamp, ease, fill, wrap, count_text, W, H, FPS, SR, ROOT  # noqa: E402
from korean import to_speech  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "scripts", "reels"))

# 색
NAVY = (11, 27, 51); NAVY2 = (24, 46, 82); GOLD = (224, 200, 150); GOLD_D = (168, 144, 97); GOLD_L = (234, 219, 185)
PAPER = (244, 243, 239); GRID = (228, 226, 220); INK = (24, 32, 46); MUTED = (120, 128, 140); LINE = (200, 204, 212)
IVORY = (246, 241, 232); RED = (255, 77, 109); WHITE = (255, 255, 255)
TH = {"light": {"bg": PAPER, "ink": INK, "muted": MUTED, "acc": GOLD_D, "card": WHITE, "line": LINE},
      "dark": {"bg": NAVY, "ink": IVORY, "muted": (150, 162, 182), "acc": GOLD_L, "card": NAVY2, "line": (60, 80, 112)}}
MONO = None


def M(s):
    """숫자용 등폭 글꼴 (없으면 SUIT)"""
    global MONO
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", "/usr/share/fonts/truetype/noto/NotoSansMono-Bold.ttf"):
        if os.path.exists(p): MONO = p; break
    return F("ExtraBold", s)


_bg = {}


def background(theme):
    if theme in _bg: return _bg[theme].copy()
    t = TH[theme]; img = Image.new("RGB", (W, H), t["bg"]); d = ImageDraw.Draw(img)
    if theme == "light":
        for x in range(0, W, 48): d.line([x, 0, x, H], fill=GRID, width=1)
        for y in range(0, H, 48): d.line([0, y, W, y], fill=GRID, width=1)
    else:
        g = np.zeros((H, W, 3), np.float32) + np.array(NAVY, np.float32)
        yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .45) / H) ** 2)
        g += (np.clip(.55 - r, 0, 1) * 40)[..., None] * np.array([.6, .8, 1.0])
        img = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img, "RGBA")
        for x in range(0, W, 48): d.line([x, 0, x, H], fill=(255, 255, 255, 8), width=1)
        for y in range(0, H, 48): d.line([0, y, W, y], fill=(255, 255, 255, 8), width=1)
    _bg[theme] = img
    return img.copy()


# ── 시간: "2:29만" → 장면 안의 초 ──
CHAPS = []  # 장 제목 목록 (목차 화면·진행 표시용)
CV = {}  # 원고 빈칸 값 (at 의 단어에도 {iv_short} 같은 빈칸을 쓸 수 있게)


def at_time(at, lines):
    if at is None or at == "": return 0.0
    s = str(at); li, _, word = s.partition(":")
    try: word = fill(word, CV)
    except KeyError: word = ""
    i = min(int(li), len(lines) - 1); t0, d, text = lines[i]
    if not word: return t0
    k = text.find(word)
    if k < 0:  # 숫자 표기가 바뀐 경우 등: 문장 시작으로
        return t0
    return t0 + d * (k / max(1, len(text))) * .95


def pop(u, t, dur=.35):
    """요소가 나타나는 정도 0~1"""
    return ease((u - t) / dur) if u >= t else 0.0


def A(c, a): return (*c[:3], int(255 * clamp(a)))


def fitF(d, s, w, size, maxw, minsize=24):
    """글자가 칸(maxw) 밖으로 나가지 않게 글꼴을 줄인다"""
    f = F(w, size)
    while size > minsize and max([d.textlength(x, font=f) for x in str(s).split("\n")] or [0]) > maxw: size -= 2; f = F(w, size)
    return f


def center_text(d, y, s, font, fill_):
    d.text((W / 2 - d.textlength(s, font=font) / 2, y), s, font=font, fill=fill_)


def chip(d, x, y, s, font, kind, a, pad=(22, 12), r=10):
    """강조 칩: navy(흰 글씨) / gold(네이비 글씨) / white(테두리) / red"""
    tw = d.textlength(s, font=font); w = tw + pad[0] * 2; h = font.size + pad[1] * 2
    bg, fg, ol = {"navy": (NAVY, WHITE, None), "gold": (GOLD, NAVY, None), "white": (WHITE, INK, LINE), "red": (RED, WHITE, None),
                  "dark": (NAVY2, IVORY, (70, 92, 128))}[kind]
    d.rounded_rectangle([x, y, x + w, y + h], r, fill=A(bg, a), outline=A(ol, a) if ol else None, width=2)
    d.text((x + pad[0], y + pad[1] - 2), s, font=font, fill=A(fg, a))
    return w, h


def dashed_box(d, box, col, a, r=14):
    x0, y0, x1, y1 = box; seg = 14
    for x in range(int(x0 + r), int(x1 - r), seg * 2):
        d.line([x, y0, min(x + seg, x1 - r), y0], fill=A(col, a), width=2); d.line([x, y1, min(x + seg, x1 - r), y1], fill=A(col, a), width=2)
    for y in range(int(y0 + r), int(y1 - r), seg * 2):
        d.line([x0, y, x0, min(y + seg, y1 - r)], fill=A(col, a), width=2); d.line([x1, y, x1, min(y + seg, y1 - r)], fill=A(col, a), width=2)


def title_line(d, t, text, a, y=150, size=50):
    if not text: return
    size = fitF(d, text, "ExtraBold", size, W - 280).size
    d.text((140, y + 14 * (1 - a)), text, font=F("ExtraBold", size), fill=A(t["ink"], a))
    d.rectangle([140, y + size + 22, 140 + 90 * a, y + size + 27], fill=A(t["acc"], a))


def val_num(s, p):
    """'47조 2천억 원' 같은 값을 p(0~1)만큼 세며 보여 준다"""
    return count_text(s, p) if re.search(r"\d", s) else s


# ── 화면 종류 ──
def draw(sc, V, u, lines, theme, media):
    v = sc["v"]; typ = v["type"]; t = TH[theme]
    img = media(u) if typ == "media" else background(theme)
    d = AD(img); T = lambda k, dflt="": fill(v.get(k, dflt), V)
    tA = pop(u, 0)
    if typ in ("title", "question"):
        a = pop(u, .1, .5)
        if typ == "question":
            cx, cy = W / 2, H / 2 - 90; rr = 230; ang = (u * 45) % 360
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(255, 255, 255, int(28 * a)), width=2)
            d.arc([cx - rr, cy - rr, cx + rr, cy + rr], start=ang, end=ang + 80, fill=A(GOLD, a), width=6)  # 천천히 도는 호
            f = F("Heavy", 300); center_text(d, H / 2 - 230 + 30 * (1 - a), "?", f, A(GOLD, a))
            s = T("text"); f2 = F("ExtraBold", 58)
            for i, l in enumerate(wrap(d, s, f2, 1500)[:2]): center_text(d, H / 2 + 170 + i * 76, l, f2, A(IVORY, pop(u, .4)))
        else:
            k = T("kicker"); f0 = F("Bold", 36); ci = CHAPS.index(T("text")) if T("text") in CHAPS else -1
            if ci >= 0: k = f"{ci + 1} / {len(CHAPS)}"
            if k: center_text(d, H / 2 - 150, k, f0, A(GOLD_L, a))
            if ci >= 0:  # 진행 표시: 지나온 장 · 지금 장 · 남은 장
                n_ = len(CHAPS); sx = W / 2 - (n_ - 1) * 34
                for j in range(n_):
                    cx_ = sx + j * 68; cy_ = H / 2 + 190; r_ = 13 if j == ci else 9
                    if j < ci: d.ellipse([cx_ - r_, cy_ - r_, cx_ + r_, cy_ + r_], fill=A((150, 162, 182), a))
                    elif j == ci: d.ellipse([cx_ - r_, cy_ - r_, cx_ + r_, cy_ + r_], fill=A(GOLD, a))
                    else: d.ellipse([cx_ - r_, cy_ - r_, cx_ + r_, cy_ + r_], outline=A((150, 162, 182), a), width=2)
                    if j < n_ - 1: d.line([cx_ + r_ + 6, cy_, cx_ + 68 - 15, cy_], fill=A((90, 104, 130), a), width=2)
            f = F("Heavy", 96); s = T("text")
            while d.textlength(s, font=f) > 1600: f = F("Heavy", f.size - 6)
            center_text(d, H / 2 - 80 + 30 * (1 - a), s, f, A(IVORY, a))
            d.rectangle([W / 2 - 70 * a, H / 2 + 50, W / 2 + 70 * a, H / 2 + 56], fill=A(GOLD, a))
            sub = T("sub")
            if sub: center_text(d, H / 2 + 90, sub, F("SemiBold", 40), A((180, 190, 206), pop(u, .4)))
    elif typ == "stat":
        a = pop(u, at_time(v.get("at"), lines))
        if v.get("kicker"): center_text(d, 250, T("kicker"), F("Bold", 40), A(t["muted"], pop(u, .1)))  # 설명 줄은 처음부터 (빈 화면 방지)
        s = T("value"); f = F("Heavy", 210)
        while d.textlength(s, font=f) > 1700: f = F("Heavy", f.size - 10)
        sv = val_num(s, clamp((u - at_time(v.get("at"), lines)) / .9)) if v.get("count", True) else s
        x = W / 2 - d.textlength(s, font=f) / 2
        d.text((x, 330 + 30 * (1 - a)), sv, font=f, fill=A(t["acc"] if theme == "light" else GOLD_L, a))
        if v.get("label"): center_text(d, 330 + f.size + 50, T("label"), F("Bold", 46), A(t["ink"], pop(u, at_time(v.get("at"), lines) + .3)))
        for c in v.get("tags", []):  # 옆에 붙는 작은 칩 (예: '영화 한 편 값')
            b = pop(u, at_time(c.get("at"), lines)); s2 = fill(c["text"], V); f3 = F("ExtraBold", 40)
            chip(d, W / 2 - d.textlength(s2, font=f3) / 2 - 22, 330 + f.size + 130, s2, f3, c.get("kind", "gold"), b)
    elif typ == "bars":
        title_line(d, t, T("title"), tA)
        if v.get("unit"): d.text((W - 300, 128), f"단위: {v['unit']}", font=F("SemiBold", 30), fill=A(t["muted"], tA))
        items = v["items"]; n = len(items); vals = [float(x[1]) for x in items]
        mx, mn = max(vals + [0]), min(vals + [0]); base_y = 820 if mn >= 0 else 700; scale_ = (base_y - 300) / max(1e-9, mx) if mx > 0 else 1
        neg_scale = scale_
        gap = 1500 / n; bw = min(200, gap * .55); x0 = 210 + (gap - bw) / 2
        d.line([180, base_y, W - 180, base_y], fill=A(t["line"], tA), width=3)
        hl = [h for h in v.get("hl", []) if u >= at_time(h.get("at"), lines)]
        cur_hl = hl[-1] if hl else None
        for i, it in enumerate(items):
            lab, val = fill(str(it[0]), V), float(it[1]); ta = at_time(it[2], lines) if len(it) > 2 and it[2] is not None else .35 + .25 * i
            p = pop(u, ta, .6); x = x0 + i * gap
            hh = (val * scale_ if val >= 0 else val * neg_scale) * p
            on = cur_hl and cur_hl.get("i") == i
            dim = cur_hl and v.get("dim", True) and not on
            col = RED if val < 0 else (GOLD if (on or (it[3] if len(it) > 3 else False)) else (NAVY if theme == "light" else (120, 146, 190)))
            if dim: col = tuple(int(c * .45 + 235 * .55) for c in col) if theme == "light" else tuple(int(c * .5) for c in col)
            if val >= 0: d.rectangle([x, base_y - hh, x + bw, base_y], fill=A(col, min(1, p * 3)))
            else: d.rectangle([x, base_y, x + bw, base_y - hh], fill=A(col, min(1, p * 3)))
            if p > .05:
                vt = (f"{val:g}") if not it[4:] else fill(it[4], V)
                fv = F("ExtraBold", 40); vy = base_y - hh - 56 if val >= 0 else base_y - hh + 8
                d.text((x + bw / 2 - d.textlength(vt, font=fv) / 2, vy), vt, font=fv, fill=A(RED if val < 0 else t["ink"], p))
                fl = F("SemiBold", 30); ly0 = base_y + 18 if val >= 0 else base_y - hh + 60
                for j, ll in enumerate(lab.split("\n")):
                    d.text((x + bw / 2 - d.textlength(ll, font=fl) / 2, ly0 + j * 36), ll, font=fl, fill=A(t["muted"], p))
        if cur_hl and cur_hl.get("note"):
            i = cur_hl["i"]; val = float(items[i][1]); x = x0 + i * gap + bw / 2; b = pop(u, at_time(cur_hl.get("at"), lines))
            top = base_y - (val * scale_ if val >= 0 else 0) - 140
            s = fill(cur_hl["note"], V); f = F("ExtraBold", 36); tw = d.textlength(s, font=f)
            bx = min(max(x - tw / 2 - 24, 160), W - 200 - tw); by = max(200, top - 20 * (1 - b))
            chip(d, bx, by, s, f, cur_hl.get("kind", "navy" if theme == "light" else "gold"), b)
        if v.get("avg") and u >= at_time(v["avg"].get("at"), lines):  # 평균선이 그어진다
            av = v["avg"]; b = pop(u, at_time(av.get("at"), lines), .8); y = base_y - float(av["value"]) * scale_
            xe = 180 + (W - 360) * b
            for xx in range(180, int(xe), 24): d.line([xx, y, min(xx + 14, xe), y], fill=A(GOLD_D, 1), width=4)
            if b > .9: chip(d, av.get("x", W - 520), av.get("y", y - 70), fill(av.get("label", "평균"), V), F("ExtraBold", 34), "gold", pop(u, at_time(av.get("at"), lines) + .6))  # x·y를 주면 막대 숫자와 겹치지 않는 자리에 고정
        for nt in v.get("notes", []):
            b = pop(u, at_time(nt.get("at"), lines))
            if b > 0: chip(d, nt.get("x", 1180), nt.get("y", 220), fill(nt["text"], V), F("ExtraBold", 36), nt.get("kind", "white"), b)
    elif typ == "hbars":
        title_line(d, t, T("title"), tA)
        items = v["items"]; mx = max(float(x[1]) for x in items)
        hl = [h for h in v.get("hl", []) if u >= at_time(h.get("at"), lines)]; cur = hl[-1] if hl else None
        for i, it in enumerate(items):
            lab, val = fill(it[0], V), float(it[1]); p = pop(u, at_time(it[2], lines) if len(it) > 2 and it[2] is not None else .35 + .25 * i, .8)  # 시점이 없으면 위에서부터 차례로 자란다
            y = 300 + i * 130; on = cur and cur.get("i") == i
            d.text((160, y + 14), lab, font=fitF(d, lab, "Bold", 42, 420), fill=A(t["ink"], p))
            col = GOLD if on else (NAVY if theme == "light" else (120, 146, 190))
            if v.get("neg"): col = RED if (len(it) > 4 and it[4]) else ((170, 61, 79) if theme == "dark" else (254, 151, 168))
            if cur and not on: col = tuple(int(c * .45 + 235 * .55) for c in col)
            room = W - 600 - 140 - max(d.textlength(fill(x[3], V) if len(x) > 3 else f"{float(x[1]):g}{v.get('suffix', '')}", font=F("ExtraBold", 46)) for x in items)  # 값 글자가 화면 밖으로 나가지 않게
            ww = min(1000, room) * val / mx * p; d.rounded_rectangle([600, y, 600 + max(8, ww), y + 76], 10, fill=A(col, min(1, p * 3)))
            d.text((620 + ww, y + 12), (fill(it[3], V) if len(it) > 3 else f"{val:g}{v.get('suffix', '')}"), font=F("ExtraBold", 46), fill=A(RED if v.get("neg") else t["ink"], p))
        if cur and cur.get("note"):
            b = pop(u, at_time(cur.get("at"), lines)); y = 300 + cur["i"] * 130
            chip(d, 600, 300 + len(items) * 130 + 10, fill(cur["note"], V), F("ExtraBold", 36), "navy", b)  # 막대 아래에 (막대·값과 겹치지 않게)
    elif typ == "scale":  # 저울
        title_line(d, t, T("title"), tA)
        tilt = 0.0; cx, cy = W / 2, 360
        lt, rt = v["left"], v["right"]; la, ra = pop(u, at_time(lt.get("at"), lines)), pop(u, at_time(rt.get("at"), lines))
        if v.get("tilt") and u >= at_time(v.get("tilt_at"), lines): tilt = (1 if v["tilt"] == "right" else -1) * 7 * pop(u, at_time(v.get("tilt_at"), lines), .8)
        ang = math.radians(tilt); L = 560
        lx, ly = cx - L * math.cos(ang), cy - L * math.sin(ang); rx, ry = cx + L * math.cos(ang), cy + L * math.sin(ang)
        d.polygon([(cx - 70, 880), (cx + 70, 880), (cx + 12, cy), (cx - 12, cy)], fill=A(t["line"], tA))
        d.line([lx, ly, rx, ry], fill=A(NAVY if theme == "light" else IVORY, tA), width=6); d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=A(GOLD, tA))
        for (px, py, side, a) in ((lx, ly, lt, la), (rx, ry, rt, ra)):
            bw, bh = 520, 260; bx0, by0 = px - bw / 2, py + 110
            d.line([px, py, bx0 + 30, by0], fill=A(t["line"], tA), width=3); d.line([px, py, bx0 + bw - 30, by0], fill=A(t["line"], tA), width=3)
            d.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh], 18, fill=A(t["card"], tA), outline=A(t["line"], tA), width=2)
            f1 = F("Bold", 36); s1 = fill(side.get("label", ""), V)
            for j, l in enumerate(s1.split("\n")): d.text((px - d.textlength(l, font=f1) / 2, by0 + 30 + j * 44), l, font=f1, fill=A(t["muted"], tA))
            s2 = fill(side.get("value", ""), V); f2 = F("Heavy", 84)
            while d.textlength(s2, font=f2) > bw - 40: f2 = F("Heavy", f2.size - 6)
            col = side.get("color"); col = GOLD_D if col == "gold" else (RED if col == "red" else t["ink"])
            d.text((px - d.textlength(s2, font=f2) / 2, by0 + 130 + 20 * (1 - a)), val_num(s2, clamp((u - at_time(side.get("at"), lines)) / .8)), font=f2, fill=A(col, a))
        if v.get("center"):
            c = v["center"]; b = pop(u, at_time(c.get("at"), lines)); s = fill(c["text"], V); f = F("ExtraBold", 44)
            chip(d, cx - d.textlength(s, font=f) / 2 - 22, cy - 130, s, f, c.get("kind", "gold"), b)
    elif typ == "equation":
        title_line(d, t, T("title"), tA)
        boxes = v["boxes"]; ops = v.get("ops", []); n = len(boxes)
        widths = [b_.get("w", 420) for b_ in boxes]; opw = 110; total = sum(widths) + opw * (n - 1); x = W / 2 - total / 2; y = v.get("y", 420); hgt = 170
        for i, b_ in enumerate(boxes):
            w_ = widths[i]; a = pop(u, at_time(b_.get("at"), lines))
            dashed_box(d, (x, y, x + w_, y + hgt), t["muted"], tA * (1 - a))
            if a > 0:
                kind = b_.get("kind", "navy"); col = {"navy": NAVY, "gold": GOLD, "white": WHITE}[kind]
                d.rounded_rectangle([x, y + 10 * (1 - a), x + w_, y + hgt + 10 * (1 - a)], 18, fill=A(col, a), outline=A(LINE, a) if kind == "white" else None, width=2)
                s = fill(b_["text"], V); f = F("Heavy", 72)
                while d.textlength(s, font=f) > w_ - 40: f = F("Heavy", f.size - 4)
                fg = WHITE if kind == "navy" else NAVY
                d.text((x + w_ / 2 - d.textlength(s, font=f) / 2, y + hgt / 2 - f.size / 2 - 8 + 10 * (1 - a)), val_num(s, clamp((u - at_time(b_.get("at"), lines)) / .7)), font=f, fill=A(fg, a))
            if b_.get("label"): d.text((x + w_ / 2 - d.textlength(fill(b_["label"], V), font=F("SemiBold", 30)) / 2, y + hgt + 22), fill(b_["label"], V), font=F("SemiBold", 30), fill=A(t["muted"], tA))
            for j, it in enumerate(b_.get("items", [])):  # 상자 아래로 구성 요소가 말에 맞춰 하나씩 쌓인다
                st_, at_ = (it if isinstance(it, list) else [it, None])[:2]; pa = pop(u, at_time(at_, lines) if at_ else .4 + .3 * j, .4)
                if pa <= 0: continue
                st_ = fill(st_, V); fi_ = fitF(d, st_, "Bold", 40, w_ - 60); iw = d.textlength(st_, font=fi_) + 60; iy = y + hgt + 80 + j * 76 + 14 * (1 - pa)
                d.rounded_rectangle([x + w_ / 2 - iw / 2, iy, x + w_ / 2 + iw / 2, iy + 60], 30, fill=A(t["card"], pa), outline=A(GOLD_D if j == len(b_["items"]) - 1 and b_.get("last_gold") else t["line"], pa), width=2)
                d.ellipse([x + w_ / 2 - iw / 2 + 18, iy + 25, x + w_ / 2 - iw / 2 + 28, iy + 35], fill=A(GOLD, pa))
                d.text((x + w_ / 2 - iw / 2 + 40, iy + 6), st_, font=fi_, fill=A(t["ink"], pa))
            x += w_
            if i < n - 1:
                o = ops[i] if i < len(ops) else "="; fo = F("Heavy", 80); d.text((x + opw / 2 - d.textlength(o, font=fo) / 2, y + hgt / 2 - 52), o, font=fo, fill=A(t["ink"], tA)); x += opw
        for nt in v.get("notes", []):
            b = pop(u, at_time(nt.get("at"), lines)); s = fill(nt["text"], V); f = F("ExtraBold", 40)
            if b > 0: chip(d, W / 2 - d.textlength(s, font=f) / 2 - 22, nt.get("y", 720), s, f, nt.get("kind", "gold"), b)
    elif typ == "timeline":
        title_line(d, t, T("title"), tA)
        pts = v["points"]; n = len(pts); y = v.get("y", 560); xL, xR = 220, W - 220
        last = max([at_time(p_.get("at"), lines) for p_ in pts if u >= at_time(p_.get("at"), lines)] or [0])
        shown = [p_ for p_ in pts if u >= at_time(p_.get("at"), lines)]
        reach = (len(shown) - 1) / max(1, n - 1) if shown else 0
        prevr = (len(shown) - 2) / max(1, n - 1) if len(shown) > 1 else 0
        rr = prevr + (reach - prevr) * pop(u, last, .6)
        d.line([xL, y, xR, y], fill=A(t["line"], tA), width=4)
        d.line([xL, y, xL + (xR - xL) * rr, y], fill=A(GOLD, tA), width=6)
        for i, p_ in enumerate(pts):
            a = pop(u, at_time(p_.get("at"), lines)); x = xL + (xR - xL) * i / max(1, n - 1)
            col = RED if p_.get("color") == "red" else (GOLD if p_.get("color") == "gold" else (NAVY if theme == "light" else IVORY))
            d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=A(col, max(.25 * tA, a)))
            fy = F("ExtraBold", 46); s = fill(p_["x"], V); up = i % 2 == 0
            d.text((x - d.textlength(s, font=fy) / 2, y - 100 if up else y + 40), s, font=fy, fill=A(t["ink"], max(.3 * tA, a)))
            ft = F("Bold", 32)
            for j, l in enumerate(wrap(d, fill(p_.get("text", ""), V), ft, 330)[:3]):
                yy = (y - 150 - (len(wrap(d, fill(p_.get("text", ""), V), ft, 330)[:3]) - 1 - j) * 42) if up else (y + 110 + j * 42)
                d.text((x - d.textlength(l, font=ft) / 2, yy + 12 * (1 - a)), l, font=ft, fill=A(RED if p_.get("color") == "red" else t["muted"], a))
        if v.get("bracket") and u >= at_time(v["bracket"].get("at"), lines):
            bk = v["bracket"]; b = pop(u, at_time(bk.get("at"), lines)); i0, i1 = bk["from"], bk["to"]
            x0_ = xL + (xR - xL) * i0 / max(1, n - 1); x1_ = xL + (xR - xL) * i1 / max(1, n - 1); yb = y + 250
            d.line([x0_, yb, x1_, yb], fill=A(GOLD_D, b), width=4); d.line([x0_, yb - 20, x0_, yb], fill=A(GOLD_D, b), width=4); d.line([x1_, yb - 20, x1_, yb], fill=A(GOLD_D, b), width=4)
            s = fill(bk["text"], V); f = F("ExtraBold", 38); chip(d, (x0_ + x1_) / 2 - d.textlength(s, font=f) / 2 - 22, yb + 20, s, f, "gold", b)
    elif typ == "headline":
        for i, it in enumerate(v["items"]):
            a = pop(u, at_time(it.get("at"), lines)); y = 360 + i * 280
            if a <= 0: continue
            x0_ = 260; x1_ = W - 260
            d.rounded_rectangle([x0_, y + 20 * (1 - a), x1_, y + 210 + 20 * (1 - a)], 12, fill=A(WHITE, a), outline=A(LINE, a), width=2)
            d.rectangle([x0_, y + 20 * (1 - a), x0_ + 10, y + 210 + 20 * (1 - a)], fill=A(RED if it.get("red") else NAVY, a))
            d.text((x0_ + 50, y + 34 + 20 * (1 - a)), fill(it.get("src", ""), V) + "  ·  " + fill(it.get("date", ""), V), font=F("SemiBold", 30), fill=A(MUTED, a))
            f = F("Heavy", 58); s = fill(it["title"], V)
            while d.textlength(s, font=f) > x1_ - x0_ - 100: f = F("Heavy", f.size - 4)
            d.text((x0_ + 50, y + 92 + 20 * (1 - a)), s, font=f, fill=A(INK, a))
        if v.get("note"):
            b = pop(u, at_time(v.get("note_at"), lines)); s = fill(v["note"], V); f = F("SemiBold", 30)
            center_text(d, 900, s, f, A(t["muted"], b))
    elif typ == "agenda":  # 오늘 볼 내용 (장 제목이 하나씩)
        a = pop(u, .1); center_text(d, 150, T("title", "오늘 볼 내용"), F("Heavy", 64), A(IVORY, a))
        items = CHAPS or v.get("items", []); y0 = 290; fi = F("ExtraBold", 44)
        two = len(items) > 7   # 장이 많으면 두 줄로 (2026-10-23: 10장이 화면 아래로 넘쳤다)
        for j, it in enumerate(items):
            p = pop(u, .5 + .32 * j, .4)
            if p <= 0: continue
            if two: half = (len(items) + 1) // 2; col, row = divmod(j, half); y = y0 + row * 100 + 14 * (1 - p); x = 200 + col * 820; fi = F("ExtraBold", 40)
            else: y = y0 + j * 84 + 14 * (1 - p); x = 560
            d.ellipse([x, y + 4, x + 56, y + 60], fill=A(GOLD, p)); nn = str(j + 1); fn = F("Heavy", 34)
            d.text((x + 28 - d.textlength(nn, font=fn) / 2, y + 10), nn, font=fn, fill=A(NAVY, p))
            d.text((x + 86, y + 4), it, font=fi, fill=A(IVORY, p))
    elif typ == "icongrid" and v.get("groups"):  # 전체 기업을 점 하나씩, 시장별 색으로
        title_line(d, t, T("title"), tA)
        groups = v["groups"]; n = sum(g[1] for g in groups); cols = v.get("cols", 45); cell = 1400 / cols; gx = W / 2 - cols * cell / 2; gy = v.get("y", 270)
        rows = math.ceil(n / cols); fillp = clamp((u - at_time(v.get("at"), lines)) / v.get("fill_sec", 2.4)); colors = []
        for g in groups: colors += [tuple(g[2])] * g[1]
        rr = cell * .36
        for k in range(int(n * fillp)):
            r_, c_ = divmod(k, cols); x = gx + c_ * cell + cell / 2; y = gy + r_ * cell + cell / 2
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=A(colors[k], 1))
        fl = F("Bold", 34); x = 0; items_ = [(fill(g[0], V) + f" {g[1]}", tuple(g[2])) for g in groups]
        tw = sum(d.textlength(s_, font=fl) + 70 for s_, _ in items_); x = W / 2 - tw / 2; ly = gy + rows * cell + 34
        for j, (s_, c) in enumerate(items_):
            p = pop(u, at_time(v.get("at"), lines) + v.get("fill_sec", 2.4) * sum(g[1] for g in groups[:j + 1]) / n, .3)
            d.ellipse([x, ly + 10, x + 24, ly + 34], fill=A(c, p)); d.text((x + 34, ly), s_, font=fl, fill=A(t["ink"], p)); x += d.textlength(s_, font=fl) + 70
        if v.get("label"):
            b = pop(u, at_time(v.get("label_at", v.get("at")), lines)); s_ = fill(v["label"], V); f = F("ExtraBold", 40)
            chip(d, W / 2 - d.textlength(s_, font=f) / 2 - 22, ly + 66, s_, f, "navy", b)
    elif typ == "icongrid":
        title_line(d, t, T("title"), tA)
        n, cols = v.get("n", 60), v.get("cols", 15); rows = math.ceil(n / cols); cell = min(130 if n <= 20 else 90, 1400 / cols); gx = W / 2 - cols * cell / 2; gy = v.get("y", 300)
        hl = v.get("hl"); hlon = hl and u >= at_time(hl.get("at"), lines)
        fillp = clamp((u - at_time(v.get("at"), lines)) / v.get("fill_sec", 1.6))
        for k in range(n):
            if k / n > fillp: break
            r_, c_ = divmod(k, cols); x = gx + c_ * cell + cell / 2; y = gy + r_ * cell + cell / 2
            on = hlon and k == hl.get("i", 0)
            col = GOLD if on else (NAVY if theme == "light" else (150, 170, 210))
            if hlon and not on: col = tuple(int(c * .4 + 235 * .6) for c in col) if theme == "light" else tuple(int(c * .45) for c in col)
            s_ = cell * .32
            if v.get("icon", "person") == "person":
                d.ellipse([x - s_ * .45, y - s_ * 1.15, x + s_ * .45, y - s_ * .25], fill=A(col, 1)); d.rounded_rectangle([x - s_ * .8, y - s_ * .15, x + s_ * .8, y + s_ * 1.1], int(s_ * .5), fill=A(col, 1))
            else:
                d.rounded_rectangle([x - s_, y - s_, x + s_, y + s_], int(s_ * .3), fill=A(col, 1))
        if v.get("label"):
            b = pop(u, at_time(v.get("label_at", v.get("at")), lines)); s = fill(v["label"], V); f = F("ExtraBold", 44)
            chip(d, W / 2 - d.textlength(s, font=f) / 2 - 22, gy + rows * cell + 40, s, f, "navy" if theme == "light" else "gold", b)
        if hlon and hl.get("note"):
            b = pop(u, at_time(hl.get("at"), lines)); s = fill(hl["note"], V); f = F("ExtraBold", 40)
            chip(d, W / 2 - d.textlength(s, font=f) / 2 - 22, gy - 100, s, f, "gold", b)
    elif typ == "circles":
        big, small = v["big"], v["small"]; cx, cy = W / 2, 520; R_ = 330
        ab = pop(u, at_time(big.get("at"), lines)); as_ = pop(u, at_time(small.get("at"), lines), .9)
        d.ellipse([cx - R_ * ab, cy - R_ * ab, cx + R_ * ab, cy + R_ * ab], outline=A(IVORY if theme == "dark" else NAVY, ab), width=4)
        r2 = R_ * math.sqrt(float(small.get("ratio", .13))) * as_ + 10 * as_
        d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=A(GOLD, as_))
        f = F("Bold", 38); s = fill(big.get("label", ""), V); d.text((cx - d.textlength(s, font=f) / 2, cy - R_ - 70), s, font=f, fill=A(t["muted"], ab))
        s2 = fill(small.get("label", ""), V); f2 = F("Heavy", 60)
        if as_ > 0: d.text((cx + r2 + 30, cy - 36), s2, font=f2, fill=A(GOLD_L if theme == "dark" else GOLD_D, as_))
    elif typ == "table":
        title_line(d, t, T("title"), tA)
        cols = v["cols"]; rows = v["rows"]; cw = v.get("cw", [560, 420, 420]); x0_ = W / 2 - sum(cw) / 2; y0 = 260
        focus = v.get("focus"); fon = focus and u >= at_time(focus.get("at"), lines); fb = pop(u, at_time(focus.get("at"), lines)) if fon else 0
        for j, c in enumerate(cols): d.text((x0_ + sum(cw[:j]) + 24, y0), fill(c, V), font=F("SemiBold", 32), fill=A(t["muted"], tA))
        for i, r in enumerate(rows):
            a = pop(u, at_time(r[-1] if isinstance(r[-1], (int,)) or (isinstance(r[-1], str) and re.fullmatch(r"\d+(:.+)?", r[-1])) else None, lines))
            cells = r[:len(cols)]; yy = y0 + 70 + i * 128
            hl = v.get("hl") == i and a > 0
            dim = fon and focus.get("row") != i
            al = a * (1 - .7 * fb if dim else 1)
            d.rounded_rectangle([x0_, yy, x0_ + sum(cw), yy + 104], 14, fill=A(GOLD if hl else t["card"], al * (.25 if hl else 1)), outline=A(GOLD_D if hl else t["line"], al), width=3 if hl else 1)
            for tg in v.get("tags", []):  # 행 옆 표시 (예: 지금 SK하이닉스 47점)
                if tg["row"] == i:
                    pb = pop(u, at_time(tg.get("at"), lines))
                    if pb > 0:
                        st_ = fill(tg["text"], V); ft = fitF(d, st_, "ExtraBold", 34, 1840 - (x0_ + sum(cw) + 40) - 60)
                        tx = x0_ + sum(cw) + 30 + 20 * (1 - pb); d.polygon([(tx, yy + 52), (tx + 18, yy + 36), (tx + 18, yy + 68)], fill=A(GOLD if tg.get("kind") == "gold" else NAVY, pb))
                        chip(d, tx + 18, yy + 26, st_, ft, tg.get("kind", "navy"), pb, pad=(18, 10))
            for j, c in enumerate(cells):
                s = fill(c, V); f = fitF(d, s, "ExtraBold" if j else "Bold", 42, cw[j] - 40)
                d.text((x0_ + sum(cw[:j]) + 24, yy + 28), s, font=f, fill=A(GOLD_D if hl and theme == "light" else (GOLD_L if hl else t["ink"]), al))
    elif typ == "checklist":
        title_line(d, t, T("title"), tA)
        for i, it in enumerate(v["items"]):
            s, at = (it if isinstance(it, list) else [it, None])[:2]; a = pop(u, at_time(at, lines)); y = 270 + i * 120
            d.rounded_rectangle([200, y + 12 * (1 - a), W - 200, y + 96 + 12 * (1 - a)], 16, fill=A(t["card"], a), outline=A(t["line"], a), width=2)
            num = f"{i + 1}"; fn = F("Heavy", 44); d.ellipse([230, y + 20, 286, y + 76], fill=A(GOLD if i == v.get("star", 0) else NAVY, a))
            d.text((258 - d.textlength(num, font=fn) / 2, y + 22), num, font=fn, fill=A(NAVY if i == v.get("star", 0) else WHITE, a))
            d.text((320, y + 24 + 12 * (1 - a)), fill(s, V), font=fitF(d, fill(s, V), "Bold", 42, W - 200 - 320 - 30), fill=A(t["ink"], a))
    elif typ == "card":  # 인물·회사 카드
        a0 = pop(u, at_time(v.get("at"), lines)); x0_, y0, x1_ = 380, 200, W - 380
        rows = v.get("rows", []); kk = fill(v.get("kicker", ""), V); ky = 64 if kk else 0  # 개념 이름(예: 경기순환주)을 크게
        y1 = y0 + 250 + ky + 90 * len(rows)
        d.rounded_rectangle([x0_, y0 + 20 * (1 - a0), x1_, y1 + 20 * (1 - a0)], 22, fill=A(t["card"], a0), outline=A(t["line"], a0), width=2)
        d.rectangle([x0_, y0 + 20 * (1 - a0), x1_, y0 + 14 + 20 * (1 - a0)], fill=A(GOLD, a0))
        if kk: chip(d, x0_ + 56, y0 + 48 + 20 * (1 - a0), kk, fitF(d, kk, "Heavy", 56, x1_ - x0_ - 160), "navy", a0, pad=(26, 12), r=12)
        d.text((x0_ + 60, y0 + 100 + ky + 20 * (1 - a0)), fill(v["title"], V), font=fitF(d, fill(v["title"], V), "Heavy", 64, x1_ - x0_ - 120), fill=A(t["ink"], a0))
        for i, r in enumerate(rows):
            s, at = (r if isinstance(r, list) else [r, None])[:2]; a = pop(u, at_time(at, lines)); y = y0 + 230 + ky + i * 90
            d.ellipse([x0_ + 64, y + 22, x0_ + 80, y + 38], fill=A(GOLD, a)); d.text((x0_ + 110, y + 6 + 10 * (1 - a)), fill(s, V), font=fitF(d, fill(s, V), "Bold", 42, x1_ - x0_ - 160), fill=A(t["ink"], a))
    elif typ == "twocol":
        title_line(d, t, T("title"), tA)
        for k, side in enumerate((v["left"], v["right"])):
            a0 = pop(u, at_time(side.get("at"), lines)); x0_ = 200 + k * 790; x1_ = x0_ + 730
            d.rounded_rectangle([x0_, 260 + 20 * (1 - a0), x1_, 860 + 20 * (1 - a0)], 20, fill=A(t["card"], a0), outline=A(t["line"], a0), width=2)
            hc = GOLD if side.get("gold") else NAVY
            d.rounded_rectangle([x0_, 260 + 20 * (1 - a0), x1_, 360 + 20 * (1 - a0)], 20, fill=A(hc, a0)); d.rectangle([x0_, 330 + 20 * (1 - a0), x1_, 360 + 20 * (1 - a0)], fill=A(hc, a0))
            d.text((x0_ + 40, 282 + 20 * (1 - a0)), fill(side["title"], V), font=fitF(d, fill(side["title"], V), "Heavy", 48, 650), fill=A(NAVY if side.get("gold") else WHITE, a0))
            for i, it in enumerate(side.get("items", [])):
                s, at = (it if isinstance(it, list) else [it, side.get("at")])[:2]; a = pop(u, at_time(at, lines)); y = 400 + i * 96
                d.text((x0_ + 50, y + 10 * (1 - a)), fill(s, V), font=fitF(d, fill(s, V), "Bold", 44, 630), fill=A(t["ink"], a))
                if i < len(side["items"]) - 1: d.line([x0_ + 40, y + 76, x1_ - 40, y + 76], fill=A(t["line"], a), width=1)
    elif typ == "phone":
        draw_phone(img, d, v, u, lines, V, theme)
    elif typ == "media":
        chips = v.get("chips", [])   # 2026-10-23 운영자: 숫자 카드는 화면 가운데에 같은 크기로 나란히
        if chips:
            ss = [(fill(c["v"], V), fill(c.get("l", ""), V)) for c in chips]
            f1 = F("Heavy", 92); f2 = F("SemiBold", 36)
            cw_ = max(380, max(max(d.textlength(a_, font=f1), d.textlength(b_, font=f2)) for a_, b_ in ss) + 96); cw_ = min(cw_, (W - 240 - 32 * (len(ss) - 1)) / len(ss))
            ch_ = 230; gap = 32; x = (W - (cw_ * len(ss) + gap * (len(ss) - 1))) / 2; y = 400
            for c, (s1, s2) in zip(chips, ss):
                a = pop(u, at_time(c.get("at"), lines)); g1 = fitF(d, s1, "Heavy", 92, cw_ - 64); g2 = fitF(d, s2, "SemiBold", 36, cw_ - 48)
                if a > 0:
                    yy = y + 18 * (1 - a)
                    d.rounded_rectangle([x + 6, yy + 10, x + cw_ + 6, yy + ch_ + 10], 22, fill=(0, 0, 0, int(90 * a)))
                    d.rounded_rectangle([x, yy, x + cw_, yy + ch_], 22, fill=(10, 18, 32, int(215 * a)), outline=A(GOLD, a * .55), width=2)
                    d.text((x + cw_ / 2 - d.textlength(s1, font=g1) / 2, yy + 34), s1, font=g1, fill=A(GOLD_L, a))
                    d.text((x + cw_ / 2 - d.textlength(s2, font=g2) / 2, yy + 34 + g1.size + 30), s2, font=g2, fill=A(IVORY, a))
                x += cw_ + gap
        if v.get("caption"):
            a = pop(u, at_time(v.get("caption_at"), lines)); s = fill(v["caption"], V); f = fitF(d, s, "Heavy", 80, W - 320)
            d.text((160, 200 + 20 * (1 - a)), s, font=f, fill=A(WHITE, a))
    elif typ == "end" and v.get("next"):
        draw_end2(img, d, v, u, lines, V)
    elif typ == "end":
        p = pop(u, .2, 1.0); ic = R.ICON_S; img.paste(ic.convert("RGB"), (W // 2 - 110, 180 + int(20 * (1 - p))), ic)
        center_text(d, 450, T("title"), fitF(d, T("title"), "Heavy", 72, 1500), A(IVORY, p)); center_text(d, 550, T("sub"), fitF(d, T("sub"), "SemiBold", 44, 1500), A(GOLD_L, p))
        # 구독 · 좋아요 · 알림 설정: 세 개가 함께 (0.12초 간격으로) 나타난다
        btns = [("구독", (220, 30, 30), WHITE, "play"), ("좋아요", WHITE, NAVY, "heart"), ("알림 설정", GOLD, NAVY, "bell")]
        fb = F("Heavy", 40); bw_, bh_, gap = 330, 100, 34; x = W / 2 - (3 * bw_ + 2 * gap) / 2; t0 = at_time(v.get("btn_at", [None])[0], lines) if v.get("btn_at") else .8
        for i, (lab, bg, fg, ic) in enumerate(btns):
            q = pop(u, t0 + i * .12, .45)
            if q > 0:
                y = 680 + 24 * (1 - q)
                d.rounded_rectangle([x + 4, y + 8, x + bw_ + 4, y + bh_ + 8], 50, fill=(0, 0, 0, int(70 * q)))   # 그림자
                d.rounded_rectangle([x, y, x + bw_, y + bh_], 50, fill=A(bg, q))
                tw = d.textlength(lab, font=fb); cx = x + bw_ / 2 - (tw + 54) / 2; cy = y + bh_ / 2
                if ic == "play": d.polygon([(cx + 6, cy - 15), (cx + 6, cy + 15), (cx + 32, cy)], fill=A(fg, q))
                elif ic == "heart":
                    d.ellipse([cx, cy - 14, cx + 20, cy + 4], fill=A(RED, q)); d.ellipse([cx + 16, cy - 14, cx + 36, cy + 4], fill=A(RED, q)); d.polygon([(cx + 1, cy - 1), (cx + 35, cy - 1), (cx + 18, cy + 18)], fill=A(RED, q))
                else:
                    d.pieslice([cx + 2, cy - 18, cx + 34, cy + 14], 180, 360, fill=A(fg, q)); d.rectangle([cx + 2, cy - 2, cx + 34, cy + 10], fill=A(fg, q))
                    d.rectangle([cx - 2, cy + 8, cx + 38, cy + 13], fill=A(fg, q)); d.ellipse([cx + 13, cy + 12, cx + 23, cy + 21], fill=A(fg, q))
                d.text((cx + 54, cy - fb.size / 2 - 6), lab, font=fb, fill=A(fg, q))
            x += bw_ + gap
    return img



NEXT_IMG = {}


def _cursor(d, x, y, a, press=0.0):
    """마우스 화살표 (누를 때 살짝 작아진다)"""
    k = 1 - .12 * press
    pts = [(0, 0), (0, 46), (12, 35), (21, 56), (30, 52), (21, 32), (37, 32)]
    sh = [(x + 4 + px * k, y + 5 + py * k) for px, py in pts]; d.polygon(sh, fill=(0, 0, 0, int(110 * a)))
    P = [(x + px * k, y + py * k) for px, py in pts]; d.polygon(P, fill=A(WHITE, a), outline=A(NAVY, a)); d.line(P + [P[0]], fill=A(NAVY, a), width=3)


def draw_end2(img, d, v, u, lines, V):
    """끝 화면 v2 (2026-10-23 운영자: 마지막이 단조롭다) — 왼쪽: 구독·좋아요·알림을 커서가 차례로 누르는 모션, 오른쪽: 다음 영상 카드"""
    p = pop(u, .15, .9); ic = R.ICON_S.resize((150, 150), Image.LANCZOS)
    LX = 520   # 왼쪽 칸 가운데
    img.paste(ic.convert("RGB"), (LX - 75, 170 + int(16 * (1 - p))), ic)
    ft = fitF(d, fill(v["title"], V), "Heavy", 66, 820); s_ = fill(v["title"], V); d.text((LX - d.textlength(s_, font=ft) / 2, 350), s_, font=ft, fill=A(IVORY, p))
    fs = fitF(d, fill(v.get("sub", ""), V), "SemiBold", 40, 820); s_ = fill(v.get("sub", ""), V); d.text((LX - d.textlength(s_, font=fs) / 2, 440), s_, font=fs, fill=A(GOLD_L, p))
    ba = v.get("btn_at", []); ts = [at_time(ba[k_], lines) if k_ < len(ba) else 1.0 + k_ for k_ in range(3)]
    bw_, bh_, gap = 250, 92, 24; x0 = LX - (3 * bw_ + 2 * gap) / 2; y0 = 560
    fb = F("Heavy", 36); centers = []
    for i_ in range(3):
        bx = x0 + i_ * (bw_ + gap); centers.append((bx + bw_ / 2, y0 + bh_ / 2))
        q = pop(u, ts[0] - .9 + i_ * .12, .45)
        if q <= 0: continue
        click = ts[i_] + .55; done = u >= click; pr = clamp(1 - abs(u - click) / .18)   # 누르는 순간 살짝 눌림
        sc_ = 1 - .06 * pr + (.08 * math.sin(min(1, (u - click) / .35) * math.pi) if done and u - click < .35 else 0)
        w2, h2 = bw_ * sc_, bh_ * sc_; cx, cy = bx + bw_ / 2, y0 + bh_ / 2 + 20 * (1 - q)
        if i_ == 0: bg, fg, lab = ((90, 90, 96), WHITE, "구독중") if done else ((220, 30, 30), WHITE, "구독")
        elif i_ == 1: bg, fg, lab = (WHITE, NAVY, "좋아요")
        else: bg, fg, lab = ((GOLD, NAVY, "알림 설정") if not done else (GOLD_L, NAVY, "알림 켜짐"))
        d.rounded_rectangle([cx - w2 / 2 + 4, cy - h2 / 2 + 8, cx + w2 / 2 + 4, cy + h2 / 2 + 8], 46, fill=(0, 0, 0, int(70 * q)))
        d.rounded_rectangle([cx - w2 / 2, cy - h2 / 2, cx + w2 / 2, cy + h2 / 2], 46, fill=A(bg, q))
        tw = d.textlength(lab, font=fb); ix = cx - (tw + 48) / 2; iy = cy
        if i_ == 0:
            if done: d.line([(ix + 4, iy), (ix + 14, iy + 11), (ix + 34, iy - 12)], fill=A(fg, q), width=6)
            else: d.polygon([(ix + 6, iy - 14), (ix + 6, iy + 14), (ix + 30, iy)], fill=A(fg, q))
        elif i_ == 1:
            hk = 1 + (.45 * math.sin(min(1, (u - click) / .5) * math.pi) if done and u - click < .5 else 0); hc = RED if done else (200, 200, 205)
            hx, hy, r_ = ix + 17, iy - 2, 9 * hk
            d.ellipse([hx - 2 * r_, hy - r_ * 1.3, hx, hy + r_ * .7], fill=A(hc, q)); d.ellipse([hx, hy - r_ * 1.3, hx + 2 * r_, hy + r_ * .7], fill=A(hc, q))
            d.polygon([(hx - 2 * r_ + 1, hy - r_ * .1), (hx + 2 * r_ - 1, hy - r_ * .1), (hx, hy + 2 * r_)], fill=A(hc, q))
            if done and u - click < .6:   # 하트 주변으로 퍼지는 점
                e = (u - click) / .6
                for k_ in range(8):
                    ang = k_ * math.pi / 4; rr = 22 + 40 * e; d.ellipse([hx + rr * math.cos(ang) - 4, hy + rr * math.sin(ang) - 4, hx + rr * math.cos(ang) + 4, hy + rr * math.sin(ang) + 4], fill=A(RED, q * (1 - e)))
        else:
            wig = 10 * math.sin((u - click) * 26) * max(0, 1 - (u - click) / .8) if done else 0   # 알림: 종이 흔들린다
            bxc = ix + 18 + wig * .6
            d.pieslice([bxc - 16, iy - 18, bxc + 16, iy + 14], 180, 360, fill=A(fg, q)); d.rectangle([bxc - 16, iy - 2, bxc + 16, iy + 10], fill=A(fg, q))
            d.rectangle([bxc - 20, iy + 8, bxc + 20, iy + 13], fill=A(fg, q)); d.ellipse([bxc - 5, iy + 12, bxc + 5, iy + 21], fill=A(fg, q))
            if done and u - click < .9:
                e = (u - click) / .9
                for sgn in (-1, 1): d.arc([bxc - 30 - 8 * e, iy - 28 - 8 * e, bxc + 30 + 8 * e, iy + 22 + 8 * e], 200 if sgn < 0 else 300, 240 if sgn < 0 else 340, fill=A(NAVY, q * (1 - e)), width=4)
        d.text((ix + 48, cy - fb.size / 2 - 6), lab, font=fb, fill=A(fg, q))
        if done and u - click < .45:   # 눌린 자리에서 퍼지는 원
            e = (u - click) / .45; R_ = 30 + 90 * e
            d.ellipse([cx - R_, cy - R_, cx + R_, cy + R_], outline=(255, 255, 255, int(150 * (1 - e))), width=4)
    # 커서: 오른쪽 아래에서 들어와 버튼을 차례로 누르고, 마지막엔 다음 영상 쪽으로
    if u >= ts[0] - .5:
        path = [(1000, 1000, ts[0] - .5)] + [(centers[k_][0] + 30, centers[k_][1] + 10, ts[k_] + .45) for k_ in range(3)] + [(1440, 560, ts[2] + 1.6)]
        cx_, cy_ = path[0][0], path[0][1]
        for (ax, ay, at_), (bx2, by2, bt) in zip(path, path[1:]):
            if u >= bt: cx_, cy_ = bx2, by2
            elif u >= at_: e = ease(clamp((u - at_) / max(.2, bt - at_ - .1))); cx_, cy_ = ax + (bx2 - ax) * e, ay + (by2 - ay) * e; break
            else: break
        press = max([clamp(1 - abs(u - (ts[k_] + .55)) / .15) for k_ in range(3)] + [0])
        _cursor(d, cx_, cy_, clamp((u - ts[0] + .5) / .3), press)
    # 다음 영상 카드
    nx = v["next"]; q2 = pop(u, at_time(nx.get("at"), lines), .7)
    if q2 > 0:
        key = nx["thumb"]
        if key not in NEXT_IMG:
            pth = os.path.join(ROOT, key.lstrip("/"))
            NEXT_IMG[key] = Image.open(pth).convert("RGB").resize((736, 414), Image.LANCZOS) if os.path.exists(pth) else Image.new("RGB", (736, 414), NAVY2)
        X0, Y0 = 1060, 250 + int(30 * (1 - q2))
        chip(d, X0, Y0 - 70, fill(nx.get("label", "다음 영상"), V), F("ExtraBold", 32), "gold", q2)
        d.rounded_rectangle([X0 - 10, Y0 - 10, X0 + 746, Y0 + 424], 22, fill=A(GOLD, q2 * .9))
        th = NEXT_IMG[key].copy()
        if q2 < 1: th = Image.blend(Image.new("RGB", th.size, NAVY), th, q2)
        img.paste(th, (X0, Y0))
        ft2 = F("Bold", 34)
        for li, ln in enumerate(wrap(d, fill(nx.get("title", ""), V), ft2, 740)[:2]): d.text((X0, Y0 + 446 + li * 46), ln, font=ft2, fill=A(IVORY, q2))


def on_backdrop(img, bd, theme):
    """그래픽(배경과 다른 부분)만 실사 배경 위로 옮긴다 (2026-10-23 운영자: 흰 판 + 그래프만 반복돼 단조롭다)"""
    key = "bga_" + theme
    if key not in _bg: _bg[key] = np.asarray(background(theme)).astype(np.int16)
    diff = np.abs(np.asarray(img).astype(np.int16) - _bg[key]).max(-1)
    mask = Image.fromarray(np.clip((diff - 4) * 14, 0, 255).astype(np.uint8))   # 글자 가장자리는 부드럽게
    out = bd.copy(); out.paste(img, (0, 0), mask); return out


def backdrop_source(v, n_frames, seed):
    if not v.get("backdrop"): return None
    return media_source({"lib": v["backdrop"], "dim": v.get("bd_dim", .64)}, n_frames, seed + 500)

# ── 안전 영역: 로고·장 제목(위)과 자막(아래)을 그래픽이 가리지 않게 ──
SAFE = (110, 152, 1810, 870)   # 왼쪽, 위, 오른쪽, 아래 (천천히 다가가는 3% 확대까지 감안한 값)


def safe_fit(sc, s, V, theme):
    """장면 전체에서 그래픽이 차지하는 영역을 재고, 안전 영역을 벗어나면 줄이고 옮길 방법을 돌려준다 (없으면 None)"""
    typ = sc["v"]["type"]
    if typ in ("media", "end"): return None
    bg = np.asarray(background(theme)).astype(np.int16); box = None
    for u in list(np.arange(0, s["dur"], .5)) + [s["dur"]]:
        im = np.asarray(draw(sc, V, u, s["lines"], theme, None)).astype(np.int16)
        m = np.abs(im - bg).max(-1) > 12; ys, xs = np.where(m.any(1))[0], np.where(m.any(0))[0]
        if not len(ys): continue
        b = (xs[0], ys[0], xs[-1] + 1, ys[-1] + 1)
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    if box is None: return None
    x0, y0, x1, y1 = box; L, T_, Rr, B = SAFE
    if x0 >= L and y0 >= T_ and x1 <= Rr and y1 <= B: return None
    x0, y0, x1, y1 = max(0, x0 - 8), max(0, y0 - 8), min(W, x1 + 8), min(H, y1 + 24)  # 나타날 때 살짝 내려오는 움직임 몫
    k = min(1.0, (Rr - L) / (x1 - x0), (B - T_) / (y1 - y0))
    nw, nh = (x1 - x0) * k, (y1 - y0) * k
    nx = min(max((x0 + x1) / 2 - nw / 2, L), Rr - nw); ny = min(max((y0 + y1) / 2 - nh / 2, T_), B - nh)
    return {"box": (int(x0), int(y0), int(x1), int(y1)), "size": (max(1, int(nw)), max(1, int(nh))), "at": (int(nx), int(ny)), "k": round(k, 3)}


def apply_fit(img, fit, theme):
    if not fit: return img
    bgi = background(theme); bga = np.asarray(bgi).astype(np.int16)
    m = Image.fromarray(((np.abs(np.asarray(img).astype(np.int16) - bga).max(-1) > 6) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
    c = img.crop(fit["box"]).resize(fit["size"], Image.LANCZOS); mc = m.crop(fit["box"]).resize(fit["size"], Image.BILINEAR)
    bgi.paste(c, fit["at"], mc)
    return bgi


SHOTS = {}
_ss = {}


def draw_phone(img, d, v, u, lines, V, theme):
    """앱 화면: 문장마다 지정한 화면·위치로. 화면이 바뀌면 아래에서 밀려 올라오고, 머무는 동안 천천히 스크롤"""
    t = TH[theme]
    if v.get("layout") == "trio":  # 첫 소개·마무리: 앱 화면 세 개가 나란히, 각자 천천히 스크롤
        a = pop(u, .1); f = fitF(d, fill(v.get("title", ""), V), "Heavy", 64, 1500); center_text(d, 150, fill(v.get("title", ""), V), f, A(t["ink"], a))
        if v.get("sub"): center_text(d, 232, fill(v["sub"], V), F("Bold", 36), A(t["acc"], pop(u, .3)))
        pw, ph, gap = 300, 540, 90; x = W / 2 - (3 * pw + 2 * gap) / 2; end_ = lines[-1][0] + lines[-1][1] + .4
        for i, it in enumerate(v["trio"][:3]):
            ta = at_time(it.get("at"), lines); p = pop(u, ta, .5)
            if p > 0:
                py = 310 + int(40 * (1 - p)); sh = SHOTS.get(it["key"]) or SHOTS.get(v["img"])
                d.rounded_rectangle([x - 14, py - 14, x + pw + 14, py + ph + 14], 50, fill=(16, 20, 28, int(255 * p)), outline=(70, 82, 104, int(255 * p)), width=3)
                if sh is not None:
                    key = (it["key"], pw); s_ = _ss.get(key)
                    if s_ is None: s_ = _ss[key] = sh.resize((pw, int(sh.height * pw / sh.width)), Image.LANCZOS)
                    q = clamp((u - ta) / max(1.0, end_ - ta)); off = int(max(0, s_.height - ph) * .55 * ease(q))
                    c = s_.crop((0, off, pw, off + ph))
                    if c.height < ph: c2 = Image.new("RGB", (pw, ph), (246, 244, 239)); c2.paste(c, (0, 0)); c = c2
                    m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw, ph], 38, fill=int(255 * p)); img.paste(c, (int(x), py), m)
                lb = fill(it.get("label", ""), V); fl = F("ExtraBold", 30); lw = d.textlength(lb, font=fl) + 44
                chip(d, x + pw / 2 - lw / 2, py + ph - 30, lb, fl, "gold" if i == 0 else "navy", p)
            x += pw + gap
        return
    px0, py0, pw, ph = 250, 120, 400, 800
    views = v["views"]; tv = [at_time(x.get("at"), lines) for x in views]
    k = max([i for i, tt in enumerate(tv) if u >= tt] or [0]); nxt = tv[k + 1] if k + 1 < len(tv) else (lines[-1][0] + lines[-1][1] + .4)
    d.rounded_rectangle([px0 - 16, py0 - 16, px0 + pw + 16, py0 + ph + 16], 60, fill=(16, 20, 28), outline=(70, 82, 104), width=3)

    def scr(vw, f):
        key = vw.get("key", v["img"]); sh = SHOTS.get(key) or SHOTS.get(v["img"])
        if sh is None: return Image.new("RGB", (pw, ph), (246, 244, 239))
        zm = vw.get("zoom", 1.0)
        ww = int(pw * zm); s_ = _ss.get((key, ww))
        if s_ is None: s_ = _ss[(key, ww)] = sh.resize((ww, int(sh.height * ww / sh.width)), Image.LANCZOS)
        off = int(max(0, s_.height - ph) * clamp(f)); xo = int((ww - pw) * vw.get("x", .5))
        c = s_.crop((xo, off, xo + pw, off + ph))
        if c.height < ph: c2 = Image.new("RGB", (pw, ph), (246, 244, 239)); c2.paste(c, (0, 0)); c = c2
        return c
    vw = views[k]; q = clamp((u - tv[k]) / max(.5, nxt - tv[k]))
    cur = scr(vw, vw.get("from", 0) + (vw.get("to", vw.get("from", 0)) - vw.get("from", 0)) * ease(q))
    tr = clamp((u - tv[k]) / .45) if k > 0 else 1.0
    if tr < 1:
        pv = views[k - 1]; prev = scr(pv, pv.get("to", pv.get("from", 0))); e = ease(tr); dy = int(ph * e)
        crop = Image.new("RGB", (pw, ph)); crop.paste(prev, (0, -dy)); crop.paste(cur, (0, ph - dy))
    else: crop = cur
    mask = Image.new("L", (pw, ph), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw, ph], 46, fill=255)
    img.paste(crop, (px0, py0), mask)
    a = pop(u, .1)
    d.text((800, 170), fill(v.get("title", ""), V), font=fitF(d, fill(v.get("title", ""), V), "Heavy", 62, 1760 - 800), fill=A(t["ink"], a))
    lab = fill(vw.get("label", ""), V)
    if lab: d.text((804, 262), lab, font=F("Bold", 40), fill=A(t["acc"], clamp((u - tv[k]) / .5)))
    for i, b in enumerate(v.get("bullets", [])):
        s, at = (b if isinstance(b, list) else [b, None])[:2]; p = pop(u, at_time(at, lines)); y = 380 + i * 130
        if p <= 0: continue
        d.rounded_rectangle([800 + 30 * (1 - p), y, 1720, y + 104], 18, fill=A(t["card"], p), outline=A(GOLD_D, p), width=2)
        d.text((838 + 30 * (1 - p), y + 26), fill(s, V), font=fitF(d, fill(s, V), "ExtraBold", 46, 1720 - 838 - 36), fill=A(t["ink"], p))


class LazyPhoto:
    """R.photo_frames와 같은 켄 번즈 움직임을, 필요한 프레임만 그때 만든다 (긴 장면에서 메모리가 넘치지 않게)"""
    def __init__(self, pth, n, seed):
        im = Image.open(pth).convert("RGB"); r = max(W / im.width, H / im.height) * 1.18
        self.im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS); self.n = n
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]; self.dx, self.dy = dirs[seed % len(dirs)]; self.zin = seed % 2 == 0
        self.kk = min(self.im.width / W, self.im.height / H)

    def __len__(self): return self.n

    def __getitem__(self, i):
        im = self.im; t = i / max(1, self.n - 1); z = (1.0 + .08 * t) if self.zin else (1.08 - .08 * t)
        w, h = W * self.kk / z, H * self.kk / z
        cx = im.width / 2 + self.dx * (im.width - w) / 2 * (t - .5) * 1.6; cy = im.height / 2 + self.dy * (im.height - h) / 2 * (t - .5) * 1.6
        l = min(max(cx - w / 2, 0), im.width - w); tp = min(max(cy - h / 2, 0), im.height - h)
        return np.asarray(im.resize((W, H), Image.BILINEAR, box=(l, tp, l + w, tp + h)))


# ── 실사 (원고가 지정한 파일만) ──
def media_source(v, n_frames, seed):
    lib = os.path.join(ROOT, "scripts", "blog", "media", "lib"); f = v.get("lib")
    pth = os.path.join(lib, f) if f else None
    if not pth or not os.path.exists(pth): return lambda u: background("dark")
    if f.endswith(".jpg") or f.endswith(".png"):
        frames = LazyPhoto(pth, n_frames, seed)   # 2026-10-23: 긴 장면에서 모든 프레임을 미리 만들면 메모리가 넘친다 → 그때그때 만든다
    else:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pth], capture_output=True, text=True).stdout.strip() or 0)
        cap = min(n_frames, 240)   # 영상은 최대 8초만 풀어 두고, 더 길면 앞뒤로 왕복 재생
        raw = subprocess.run(["ffmpeg", "-v", "error", "-stream_loop", "-1", "-ss", "0", "-i", pth, "-frames:v", str(cap), "-vf",
                              f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=rgb24", "-f", "rawvideo", "-"], capture_output=True).stdout
        fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3) if raw else np.zeros((1, H, W, 3), np.uint8)
        L_ = len(fr); frames = [fr[(i % (2 * L_ - 1)) if (i % (2 * L_ - 1)) < L_ else (2 * L_ - 2 - i % (2 * L_ - 1))] for i in range(n_frames)] if L_ > 1 else [fr[0]] * n_frames
    dark = v.get("dim", .35)

    def get(u):
        im = Image.fromarray(np.asarray(frames[min(int(u * FPS), len(frames) - 1)])).convert("RGB")
        ov = Image.new("RGB", (W, H), (6, 12, 24)); im = Image.blend(im, ov, dark)
        g = ImageDraw.Draw(im, "RGBA")
        for k in range(14): g.rectangle([0, H - 360 + k * 26, W, H], fill=(6, 12, 24, 12))
        return im
    return get


def chrome2(img, theme, chapter, src, asof, frac, logo_dark, logo_light):
    d = AD(img); t = TH[theme]
    paste_logo(img, 60, 40, 36, "light" if theme == "light" else "dark")   # 2026-10-23 확정 로고 (scripts/brand.py)
    d = AD(img)
    d.rectangle([0, 0, W, 6], fill=(220, 220, 214) if theme == "light" else (20, 36, 62)); d.rectangle([0, 0, int(W * frac), 6], fill=GOLD)
    if chapter:
        f = F("SemiBold", 28); tw = d.textlength(chapter, font=f)
        d.rounded_rectangle([W - 72 - tw - 36, 46, W - 72, 94], 24, outline=A(t["acc"], 1), width=2)
        d.text((W - 72 - tw - 18, 54), chapter, font=f, fill=A(t["ink"], .85))
    foot = " · ".join([x for x in [src, (f"데이터 {asof} 기준" if asof else "")] if x])
    if foot: d.text((60, H - 46), foot, font=F("Medium", 22), fill=A(t["muted"], 1))


def sub_pages(d, text, f, maxw=1480):
    """자막을 한 줄짜리 묶음으로: 쉼표·마침표에서 먼저 끊고, 그래도 길면 단어 단위로 (2026-10-22 운영자: 한 줄씩)"""
    parts = [p.strip() for p in re.split(r"(?<=[,.?!])\s+", text) if p.strip()]
    out = []
    for p in parts:
        for l in wrap(d, p, f, maxw):
            if out and len(l) < 9 and d.textlength(out[-1] + " " + l, font=f) <= maxw: out[-1] += " " + l
            else: out.append(l)
    i = 0
    while i < len(out) - 1:  # 너무 짧은 줄은 다음 줄과 합친다 (한 줄에 들어가면)
        if len(out[i]) < 9 and d.textlength(out[i] + " " + out[i + 1], font=f) <= maxw: out[i] += " " + out.pop(i + 1)
        else: i += 1
    return out


def subtitle2(img, text, u_in, dur):
    """아래 자막: 어두운 띠 위 흰 글씨, 한 번에 한 줄. 말하는 길이에 맞춰 다음 줄로 넘어간다"""
    if not text: return
    d = AD(img); f = F("Bold", 44); pages = sub_pages(d, text, f)
    tot = sum(len(p) for p in pages); acc = 0; pi = 0; start = 0.0
    for pi, pg in enumerate(pages):
        if u_in < dur * (acc + len(pg)) / tot or pi == len(pages) - 1: start = dur * acc / tot; break
        acc += len(pg)
    l = pages[pi]; a = clamp((u_in - start) / .12) if pi else clamp(u_in / .15 + .3)
    tw = d.textlength(l, font=f); x = (W - tw) / 2; y = H - 160   # 2026-10-23 운영자: 자막을 살짝 위로
    d.rounded_rectangle([x - 20, y - 8, x + tw + 20, y + 56], 12, fill=(8, 14, 26, int(205 * a)))
    d.text((x, y), l, font=f, fill=(255, 255, 255, int(255 * a)))
    for m in re.finditer(r"[+\-−]?\d[\d,.]*(?:\s?(?:조|억|만|천))*(?:\s?\d[\d,]*\s?(?:억|만|천))*\s?(?:원|%p|%|배|점|년|분기|곳|개)?", l):
        tx = x + d.textlength(l[:m.start()], font=f); d.text((tx, y), m.group().rstrip(), font=f, fill=(*GOLD_L, int(255 * a)))


def make_theme(n, seed=11):
    """밸류노트 시그니처 배경음악 v3 (직접 합성, 저작권 걱정 없음) — 122BPM 묵직한 베이스 하우스 (2026-10-22 운영자: 피아노 빼고, 무게감 있는 베이스, 따다단 리듬).
    주인공은 끊어 치는 베이스 리프(16분음표 '따-다단-단따-단단-따'): 2마디 패턴이 계속 돌아서 귀에 남는다. 그 아래 서브 베이스, 굵은 킥, 클랩, 하이햇."""
    from scipy import signal
    rng = np.random.default_rng(seed); L = np.zeros(n, np.float32); Rr = np.zeros(n, np.float32); K = np.zeros(n, np.float32)
    bpm = 122; b = 60 / bpm; bar = 4 * b; s16 = b / 4; nt = lambda k: 440 * 2 ** ((k - 69) / 12)
    def add(at, x, gl=1.0, gr=1.0, kick=False):
        i = int(at * SR)
        if i >= n or i < 0: return
        m = min(len(x), n - i)
        if kick: K[i:i + m] += x[:m]
        else: L[i:i + m] += x[:m] * gl; Rr[i:i + m] += x[:m] * gr
    tt = lambda d: np.arange(int(SR * d)) / SR
    t = tt(.4); kick = (np.sin(2 * np.pi * (40 * t + 90 / 20 * (1 - np.exp(-20 * t)))) * np.exp(-t * 6.5) + .25 * np.exp(-t * 250) * rng.standard_normal(len(t))).astype(np.float32)
    kick = np.tanh(kick * 1.6).astype(np.float32) * .95
    nz = lambda d: rng.standard_normal(int(SR * d)).astype(np.float32)
    bp = signal.butter(2, [900 / (SR / 2), 3000 / (SR / 2)], "band"); hp = signal.butter(2, 7000 / (SR / 2), "high")
    clap = np.zeros(int(SR * .25), np.float32)
    for k in range(3): seg = signal.lfilter(*bp, nz(.25)) * np.exp(-tt(.25) * (60 if k < 2 else 16)); clap[int(k * .011 * SR):] += seg[: len(clap) - int(k * .011 * SR)]
    clap = (clap / np.abs(clap).max() * .3).astype(np.float32)
    ohat = (signal.lfilter(*hp, nz(.13)) * np.exp(-tt(.13) * 24) * .12).astype(np.float32)
    chat = (signal.lfilter(*hp, nz(.035)) * np.exp(-tt(.035) * 100) * .06).astype(np.float32)
    def riff(f, d):   # 끊어 치는 묵직한 베이스: 톱니+사각파를 낮게 거르고, 필터가 열렸다 닫힌다
        t = tt(d); x = .6 * signal.sawtooth(2 * np.pi * f * t) + .5 * signal.square(2 * np.pi * f * t, .5) + .8 * np.sin(2 * np.pi * f * t)
        y = np.zeros_like(x); zi = None
        cut = 200 + 1300 * np.exp(-t * 18)
        for a in range(0, len(x), 256):
            bb, aa = signal.butter(2, min(.99, cut[a] / (SR / 2))); seg, zi = signal.lfilter(bb, aa, x[a:a + 256], zi=zi if zi is not None else signal.lfilter_zi(bb, aa) * 0); y[a:a + 256] = seg
        return (np.tanh(1.8 * y) * np.minimum(1, t / .003) * np.minimum(1, (d - t) / .01) * .55).astype(np.float32)
    def sub(f, d):
        t = tt(d); return (np.sin(2 * np.pi * f * t) * np.minimum(1, t / .01) * np.minimum(1, (d - t) / .02) * .5).astype(np.float32)
    def stab(fs, d=.16):
        t = tt(d); x = sum(signal.sawtooth(2 * np.pi * f * t) for f in fs); x = signal.lfilter(*signal.butter(2, 1500 / (SR / 2)), x)
        return (x / len(fs) * np.exp(-t * 14) * .1).astype(np.float32)
    # 2마디 리프 (16분음표 위치, 반음 차이): 1마디 '따 · 다단 · 단따 · 단단 · 따', 2마디는 끝을 올려 대답
    patA = [(0, 0), (3, 0), (4, 0), (6, 12), (7, 0), (10, 0), (11, 3), (14, 5)]
    patB = [(0, 0), (3, 0), (4, 0), (6, 12), (7, 0), (10, 7), (12, 5), (14, 3)]
    roots = [33, 33, 29, 31]   # A1 A1 F1 G1 (4마디 진행)
    t0, bi = 0.0, 0; total = n / SR
    while t0 < total:
        root = roots[bi % 4]; sec = (bi // 8) % 4
        for k in range(4):
            add(t0 + k * b, kick, kick=True)
            if k in (1, 3) and bi >= 1: add(t0 + k * b, clap, .9, 1)
            add(t0 + k * b + b / 2, ohat, .8, 1)
            for q in (1, 3): add(t0 + k * b + q * s16, chat, 1, .8)
        for pos, iv in (patA if bi % 2 == 0 else patB):
            add(t0 + pos * s16, riff(nt(root + 12 + iv), s16 * 1.6))
        add(t0, sub(nt(root), b * 1.8)); add(t0 + 2 * b, sub(nt(root), b * 1.8))
        if sec in (1, 3):   # 8마디마다 코드 끊어 치기가 들어왔다 빠진다 (반복이 지루하지 않게)
            for k in (1, 3): add(t0 + k * b + b * .75, stab([nt(root + 36 + x) for x in (0, 3, 7, 10)]), 1, .85)
        t0 += bar; bi += 1
    env = np.ones(n, np.float32); per = int(b * SR); dip = (1 - .55 * np.exp(-np.arange(per) / SR * 9)).astype(np.float32)
    for i in range(0, n, per): env[i:i + per] = dip[: min(per, n - i)]
    L = L * env + K; Rr = Rr * env + K
    m = np.stack([L, Rr], 1); m = signal.lfilter(*signal.butter(2, 10000 / (SR / 2), "low"), m, axis=0)
    fi = int(SR * .8); m[:fi] *= np.linspace(0, 1, fi)[:, None]; fo = int(SR * 3); m[-fo:] *= np.linspace(1, 0, fo)[:, None]
    m = np.tanh(m / (np.abs(m).max() + 1e-9) * 1.5) / np.tanh(1.5)
    return m.astype(np.float32)


def load_theme(n):
    """운영자가 직접 만든 밸류노트 테마곡(assets/theme.mp3, 저작권 없음)을 영상 길이만큼 이어 붙인다.
    곡 앞뒤 무음은 잘라 내고, 반복할 때는 3초 동안 겹쳐서 자연스럽게 넘어간다. 파일이 없으면 합성 테마를 쓴다."""
    p = os.path.join(HERE, "assets", "theme.mp3")
    if not os.path.exists(p): return make_theme(n)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy(); lv = np.abs(x).max(1)
    idx = np.where(lv > .01)[0]; x = x[idx[0]: idx[-1] + 1] if len(idx) else x
    xf = int(SR * 3); out = x.copy(); fade = np.linspace(0, 1, xf, dtype=np.float32)[:, None]
    while len(out) < n:
        out[-xf:] = out[-xf:] * (1 - fade) + x[:xf] * fade; out = np.concatenate([out, x[xf:]])
    out = out[:n]; fi = int(SR * .8); out[:fi] *= np.linspace(0, 1, fi, dtype=np.float32)[:, None]; fo = int(SR * 3); out[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)[:, None]
    return (out / (np.abs(out).max() + 1e-9)).astype(np.float32)


VOICE_LOG = []


def clean_voice(l, speak):
    """성우 음성에 가끔 섞이는 이상한 소리(늘어진 소리·괴물 소리·덜 녹음된 소리)를 걸러 낸다 (2026-10-22 운영자 검수).
    1) 말 속도가 평소(초당 약 6.7음절)보다 크게 느리거나 빠르면  2) 음성 인식으로 다시 받아 적었을 때 원고와 많이 다르면
    캐시를 버리고 다시 받는다. 세 번까지 받아 가장 정상인 것을 쓴다."""
    say = to_speech(l); syl = len(re.sub(r"[^가-힣]", "", say)); best = None
    for k in range(3):
        a = R.pace(speak(say, 1.1, fresh=k > 0)); rate = syl / max(.1, len(a) / SR)
        bad_rate = syl >= 10 and not (5.5 <= rate <= 8.3)
        try:
            import verify; sc = verify.score(l, verify.hear(a, SR))
        except Exception: sc = 1.0
        bad = bad_rate or sc < (.62 if re.search("버핏|그레이엄|멍거|버크셔|CXMT|HBM|PER", l) else .72); cost = abs(rate - 6.7) / 6.7 + max(0, .85 - sc)
        if best is None or cost < best[0]: best = (cost, a, rate, sc)
        if not bad: break
        print(f"  음성 다시 받기({k + 1}/3): 속도 {rate:.1f}음절/초, 인식 {sc:.2f} · {l[:30]}", flush=True)
    VOICE_LOG.append([l[:40], round(best[2], 2), round(best[3], 2)])
    return best[1]


def make_thumb(spec, V, out):
    """썸네일 (2026-10-22 운영자: 머니스웨거처럼 단순·직관·자극적으로) — 관련 사진 한 장 + 굵은 두 줄(흰색 + 노란색 질문)"""
    tv = spec["thumb"]; TW, TH_ = 1280, 720; YEL = (255, 219, 148)
    ph = tv.get("photo") and os.path.join(ROOT, "scripts", "blog", "media", "lib", tv["photo"])
    if ph and os.path.exists(ph):
        im = Image.open(ph).convert("RGB"); sc_ = max(TW / im.width, TH_ / im.height)
        im = im.resize((int(im.width * sc_) + 1, int(im.height * sc_) + 1), Image.LANCZOS)
        fx = tv.get("focus_x", .5); x0 = int((im.width - TW) * fx); im = im.crop((x0, (im.height - TH_) // 2, x0 + TW, (im.height - TH_) // 2 + TH_))
    else:
        im = background("dark").resize((TW, TH_))
    th = im.convert("RGBA")
    sh = Image.new("RGBA", (TW, TH_)); g = ImageDraw.Draw(sh)   # 글자 쪽(왼쪽 아래)만 어둡게: 사진은 살리고 글자는 또렷하게
    for k in range(TW):
        a = int((40 if tv.get("pos", "top") in ("top", "center") else 170) * max(0, 1 - k / (TW * .75)) ** 1.3); g.line([k, 0, k, TH_], fill=(0, 0, 0, a))
    th = Image.alpha_composite(th, sh); sh2 = Image.new("RGBA", (TW, TH_)); g2 = ImageDraw.Draw(sh2)
    for y in range(TH_ // 2, TH_): g2.line([0, y, TW, y], fill=(0, 0, 0, int((20 if tv.get("pos", "top") in ("top", "center") else 120) * (y - TH_ / 2) / (TH_ / 2))))
    th = Image.alpha_composite(th, sh2); d = ImageDraw.Draw(th)
    l1, l2 = fill(tv["l1"], V), fill(tv["l2"], V); maxw = TW - 120
    f1 = F("Heavy", 112)
    while d.textlength(l1, font=f1) > maxw: f1 = F("Heavy", f1.size - 4)
    f2 = F("Heavy", 190)
    while d.textlength(l2, font=f2) > maxw: f2 = F("Heavy", f2.size - 6)
    pos = tv.get("pos", "top")   # 2026-10-22 운영자: 테두리 없이 그림자만 (예시: '얼마 벌고 얼마 쓸까'). center = 회사 로고 + 두 줄을 가운데에
    if pos in ("center", "left"):
        LX = 72; YEL = tuple(tv.get("accent", (242, 212, 151)))   # 2026-10-22: 노랑 대신 은은한 골드, 왼쪽 정렬
        f1 = F("Heavy", tv.get("s1", 78)); f2 = F("Heavy", tv.get("s2", 138))
        co = tv.get("co_logo") and os.path.join(HERE, "assets", tv["co_logo"]); card = None
        if co and os.path.exists(co):
            lh = tv.get("logo_h", 100); cl = Image.open(co).convert("RGBA"); sc2 = lh / cl.height; cl = cl.resize((int(cl.width * sc2), lh), Image.LANCZOS)
            card = cl   # 투명 배경 로고는 카드 없이 사진 위에 바로 (2026-10-22 운영자)
        bdg = tv.get("badge"); fbg = F("ExtraBold", tv.get("badge_s", 38))   # 2026-10-23 운영자: '주가 전망 심층분석' 같은 작은 배지
        hh = (card.height + 34 if card else 0) + (fbg.size + 58 if bdg else 0) + f1.size + 18 + f2.size; y0 = (TH_ - hh) // 2 - 6
        vg = Image.new("RGBA", (TW, TH_)); gv = ImageDraw.Draw(vg)   # 가운데를 살짝 어둡게
        for r_ in range(0, 520, 4): gv.ellipse([TW / 2 - 700 + r_, TH_ / 2 - 380 + r_ * .55, TW / 2 + 700 - r_, TH_ / 2 + 380 - r_ * .55], fill=(0, 0, 0, 3))
        th = Image.alpha_composite(th, vg.filter(ImageFilter.GaussianBlur(30)))
        if card:
            shd = Image.new("RGBA", (TW, TH_)); sx0 = (TW - card.width) // 2 if pos == "center" else LX; sh_a = card.getchannel("A").point(lambda v: int(v * .55)); shd.paste((0, 0, 0, 255), (sx0 + 3, y0 + 4), sh_a)   # 로고 모양 그대로 은은한 그림자
            cx0 = (TW - card.width) // 2 if pos == "center" else LX
            th = Image.alpha_composite(th, shd.filter(ImageFilter.GaussianBlur(6))); th.alpha_composite(card, (cx0, y0)); y0 += card.height + 30
        if bdg:
            dd = ImageDraw.Draw(th); bw = dd.textlength(bdg, font=fbg) + 52; bx = (TW - bw) / 2 if pos == "center" else LX; bh = fbg.size + 30
            sdb = Image.new("RGBA", (TW, TH_)); ImageDraw.Draw(sdb).rounded_rectangle([bx + 3, y0 + 5, bx + bw + 3, y0 + bh + 5], 12, fill=(0, 0, 0, 150)); th = Image.alpha_composite(th, sdb.filter(ImageFilter.GaussianBlur(6)))
            dd = ImageDraw.Draw(th); dd.rounded_rectangle([bx, y0, bx + bw, y0 + bh], 12, fill=(224, 200, 150)); dd.text((bx + 26, y0 + 10), bdg, font=fbg, fill=(11, 27, 51)); y0 += bh + 28
        for (txt, f, col) in ((l1, f1, WHITE), (l2, f2, YEL)):
            tw_ = ImageDraw.Draw(th).textlength(txt, font=f); x_ = (TW - tw_) / 2 if pos == "center" else LX
            for blur, off, alpha in ((14, 6, 160), (4, 3, 170)):
                sd_ = Image.new("RGBA", (TW, TH_)); ImageDraw.Draw(sd_).text((x_ + off, y0 + off), txt, font=f, fill=(0, 0, 0, alpha))
                th = Image.alpha_composite(th, sd_.filter(ImageFilter.GaussianBlur(blur)))
            ImageDraw.Draw(th).text((x_, y0), txt, font=f, fill=col); y0 += f.size + 18
        paste_logo(th, TW - 40, 34, 34, "dark", align="right", ko=False)   # 썸네일은 ValueNote 단독   # 2026-10-23 확정 로고 (오른쪽 위)
        th.convert("RGB").save(os.path.join(out, "thumb.jpg"), quality=92); return
    if pos == "top": y1 = 46; y2 = y1 + f1.size + 14
    else: y2 = TH_ - 70 - f2.size; y1 = y2 - f1.size - 18
    if pos == "top":   # 위쪽을 살짝 어둡게 (사진은 살리고 글자는 또렷하게)
        sh3 = Image.new("RGBA", (TW, TH_)); g3 = ImageDraw.Draw(sh3)
        for yy in range(int(TH_ * .62)): g3.line([0, yy, TW, yy], fill=(0, 0, 0, int(120 * (1 - yy / (TH_ * .62)) ** 1.4)))
        th = Image.alpha_composite(th, sh3); d = ImageDraw.Draw(th)
    for (txt, f, y, col) in ((l1, f1, y1, WHITE), (l2, f2, y2, YEL)):
        for blur, off, alpha in ((14, 6, 150), (4, 3, 170)):   # 넓고 부드러운 그림자 + 가까운 그림자 (테두리는 쓰지 않는다)
            sd_ = Image.new("RGBA", (TW, TH_)); ImageDraw.Draw(sd_).text((60 + off, y + off), txt, font=f, fill=(0, 0, 0, alpha))
            th = Image.alpha_composite(th, sd_.filter(ImageFilter.GaussianBlur(blur)))
        d = ImageDraw.Draw(th); d.text((60, y), txt, font=f, fill=col)
    co = tv.get("co_logo") and os.path.join(HERE, "assets", tv["co_logo"])
    if co and os.path.exists(co):   # 회사 로고 (흰 바탕 카드 위, 오른쪽 아래)
        cl = Image.open(co).convert("RGBA"); sc2 = min(300 / cl.width, 110 / cl.height); cl = cl.resize((int(cl.width * sc2), int(cl.height * sc2)), Image.LANCZOS)
        card = Image.new("RGBA", (cl.width + 56, cl.height + 40), (0, 0, 0, 0)); ImageDraw.Draw(card).rounded_rectangle([0, 0, card.width - 1, card.height - 1], 18, fill=(255, 255, 255, 235))
        card.alpha_composite(cl, (28, 20)); th.alpha_composite(card, (TW - card.width - 40, TH_ - card.height - 40))
    paste_logo(th, TW - 40, 34, 34, "dark", align="right", ko=False)   # 썸네일은 ValueNote 단독
    th.convert("RGB").save(os.path.join(out, "thumb.jpg"), quality=92)


def main():
    spec_path = sys.argv[1]; fake = "--fake-voice" in sys.argv
    spec = json.load(open(spec_path, encoding="utf-8")); data = json.load(open(spec_path.replace(".json", ".data.json"), encoding="utf-8")); V = data["vars"]; CV.update(V)
    out = os.path.join(ROOT, "social", "youtube", spec["id"]); os.makedirs(out, exist_ok=True)
    R.BG = R.bg_gradient(); R.LOGO = Image.open(os.path.join(HERE, "assets", "logo.png")).convert("RGBA")
    R.ICON = Image.open(os.path.join(HERE, "assets", "icon.png")).convert("RGBA"); R.ICON_S = R.ICON.resize((220, 220), Image.LANCZOS)
    wm = R.LOGO.crop((0, 0, R.LOGO.width, 120))  # 로고 이미지의 작은 한글은 잘라 내고, 아래에 '밸류노트'를 크게 직접 쓴다
    logo_light = wm.resize((int(wm.width * .42), int(wm.height * .42)), Image.LANCZOS)
    # 밝은 배경용 로고: 밝은 글자를 네이비로
    arr = np.asarray(logo_light).copy(); lum = arr[..., :3].mean(-1); m = (lum > 200) & (arr[..., 3] > 0); arr[m, :3] = NAVY; logo_dark = Image.fromarray(arr)
    CHAPS[:] = [sc["chapter"] for sc in spec["scenes"] if sc.get("chapter")][1:]  # 첫 장(도입)은 목차에서 뺀다
    for sc in spec["scenes"]:
        img = sc["v"].get("img")
        if img:
            p = os.path.join(out, "shot_" + img.replace(":", "_") + ".png")
            if os.path.exists(p): SHOTS[img] = Image.open(p).convert("RGB")
            for k in ("list", "value", "brief", "port"):
                q = p.replace(".png", "_" + k + ".png")
                if os.path.exists(q): SHOTS[img + ":" + k] = Image.open(q).convert("RGB")
    # 1) 음성
    if not fake: from tts import speak
    timeline = []; t = 0.0; audio = []
    for sc in spec["scenes"]:
        lines = []
        for l in sc["lines"]:
            if l.startswith("?"):
                try: lines.append(fill(l[1:], V))
                except KeyError: print("  선택 문장 생략:", l[:40])
            else: lines.append(fill(l, V))
        if not lines: print("  문장이 없어 장면 생략:", sc["v"]["type"]); continue
        lt = []; u = .25
        for l in lines:
            a = np.zeros(int(len(l) / 9.2 * SR), np.float32) if fake else clean_voice(l, speak)
            lt.append((u, len(a) / SR, l)); audio.append((t + u, a)); u += len(a) / SR + R.GAP
        dur = u + sc.get("hold", .35)
        timeline.append({"sc": sc, "start": t, "dur": dur, "lines": lt}); t += dur
    total = t
    mix = np.zeros(int((total + 1) * SR), np.float32)
    for st, a in audio:
        i = int(st * SR); mix[i:i + len(a)] += a[: len(mix) - i]
    if np.abs(mix).max() > 0: mix = mix / np.abs(mix).max() * .9
    from scipy import signal as _sg
    env = np.convolve(np.abs(mix), np.ones(int(SR * .25)) / (SR * .25), "same"); env = np.clip(env / (env.max() + 1e-9) * 4, 0, 1)
    env = _sg.lfilter([.0005], [1, -.9995], env); env = np.clip(env / (env.max() + 1e-9), 0, 1)
    MUS_LEVEL, MUS_DUCK = .19, .62   # 2026-10-22 운영자: 음악이 안 들린다 → 말 없는 곳은 또렷하게, 말할 때는 62% 낮춘다
    boost = np.ones(len(mix), np.float32)   # 시작(첫 말 전)과 끝 화면에서는 음악을 더 크게, 사이는 부드럽게 이어 준다
    first = int(timeline[0]["start"] * SR + timeline[0]["lines"][0][0] * SR); last = int(timeline[-1]["start"] * SR)
    boost[:first] = 1.5; boost[last:] = 1.5
    boost = np.convolve(boost, np.ones(int(SR * 1.2)) / (SR * 1.2), "same").astype(np.float32)
    mus = load_theme(len(mix)) * (MUS_LEVEL * boost * (1 - MUS_DUCK * env))[:, None]
    st_ = np.stack([mix, mix], 1) + mus; st_ = (st_ / max(1.0, np.abs(st_).max() / .95)).astype(np.float32)
    wav = os.path.join(out, "voice.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", wav], input=st_.tobytes(), check=True)
    if "--stills" in sys.argv:  # 검수용: 장면마다 마지막 문장을 말하는 순간 한 장씩
        sd = os.path.join(out, "stills"); os.makedirs(sd, exist_ok=True); chapter = ""
        for k, s in enumerate(timeline):
            sc = s["sc"]; typ = sc["v"]["type"]; theme = "dark" if sc["v"].get("backdrop") else (sc.get("bg") or ("dark" if typ in ("title", "question", "end", "media", "agenda") else "light"))
            if sc.get("chapter"): chapter = sc["chapter"]
            fit = safe_fit(sc, s, V, theme); media = media_source(sc["v"], int(s["dur"] * FPS) + 2, k) if typ == "media" else None
            bdf = backdrop_source(sc["v"], int(s["dur"] * FPS) + 2, k)
            lt = s["lines"][-1]; u = min(s["dur"] - .05, lt[0] + lt[1] * .9)
            img = apply_fit(draw(sc, V, u, s["lines"], "dark" if typ == "media" else theme, media), fit, theme)
            if bdf: img = on_backdrop(img, bdf(u), theme)
            if typ not in ("media", "end"):
                z = 1.03; cw, ch = W / z, H / z; img = img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
            chrome2(img, "dark" if typ == "media" else theme, chapter if typ != "end" else "", fill(sc.get("src", sc["v"].get("src", "")), V), V.get("asof"), .5, logo_dark, logo_light)
            if typ != "end": subtitle2(img, lt[2], lt[1] * .9, lt[1])
            img.save(os.path.join(sd, f"{k:02d}_{typ}.jpg"), quality=80)
            if typ not in ("media", "end"):  # 빈 화면 점검: 문장마다 시작 0.4초 뒤에 그래픽이 있는지
                bga = np.asarray(background(theme)).astype(np.int16)
                for li, (t_, d_, txt) in enumerate(s["lines"]):
                    im_ = np.asarray(draw(sc, V, t_ + .4, s["lines"], theme, None)).astype(np.int16)
                    if (np.abs(im_ - bga).max(-1) > 12).mean() < .004: print(f"  ⚠ 빈 화면: 장면 {k} 문장 {li} · {txt[:30]}")
            print(k, typ, fit and fit["k"])
        make_thumb(spec, V, sd)
        return
    # 2) 영상
    tmp = os.path.join(out, "video_noaudio.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    prev_last = None; chapter = ""
    for k, s in enumerate(timeline):
        sc = s["sc"]; n = int(round(s["dur"] * FPS)); typ = sc["v"]["type"]
        theme = "dark" if sc["v"].get("backdrop") else (sc.get("bg") or ("dark" if typ in ("title", "question", "end", "media", "agenda") else "light"))
        if sc.get("chapter"): chapter = sc["chapter"]
        media = media_source(sc["v"], n + 2, k) if typ == "media" else None
        bdf = backdrop_source(sc["v"], n + 2, k)
        fit = safe_fit(sc, s, V, theme)
        if fit: print(f"  안전 영역 맞춤: 장면 {k + 1} {typ} ×{fit['k']}", flush=True)
        src = fill(sc.get("src", sc["v"].get("src", "")), V); asof = V.get("asof") if sc.get("asof", typ not in ("title", "question", "end", "media")) else ""
        for i in range(n):
            u = i / FPS
            img = apply_fit(draw(sc, V, u, s["lines"], "dark" if typ == "media" else theme, media), fit, theme)
            if bdf: img = on_backdrop(img, bdf(u), theme)
            if typ not in ("media", "end"):  # 그래픽 화면은 장면 내내 아주 천천히 다가간다 (멈춘 화면처럼 보이지 않게)
                z = 1 + .03 * (u / max(1.0, s["dur"])); cw, ch = W / z, H / z
                img = img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
            chrome2(img, "dark" if typ == "media" else theme, chapter if typ != "end" else "", src, asof, (s["start"] + u) / total, logo_dark, logo_light)
            cur = next((l for l in reversed(s["lines"]) if u >= l[0] - .05), None)
            if cur and u <= cur[0] + cur[1] + .25 and typ != "end": subtitle2(img, cur[2], u - cur[0], cur[1])
            fr = np.asarray(img)
            if prev_last is not None and i < 6:  # 장면 사이 짧은 디졸브 (0.25초)
                a = (i + 1) / 7; fr = (prev_last * (1 - a) + fr * a).astype(np.uint8)
            enc.stdin.write(fr.tobytes())
            if i == n - 1: prev_last = fr.astype(np.float32)
        print(f"  장면 {k + 1}/{len(timeline)} {typ} {s['dur']:.1f}초", flush=True)
    enc.stdin.close(); enc.wait()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", os.path.join(out, "video.mp4")], check=True)
    os.remove(tmp)
    make_thumb(spec, V, out)
    # 4) 설명·메타
    chapters = []
    for s in timeline:
        if s["sc"].get("chapter"):
            m_, sec = divmod(int(s["start"]), 60); chapters.append(f"{m_}:{sec:02d} {s['sc']['chapter']}")
    if not chapters or not chapters[0].startswith("0:00"): chapters.insert(0, "0:00 시작")
    desc = "\n".join([fill(spec["description_head"], V), "", f"※ 영상의 주가·적정 주가·점수는 {V['asof']} 기준입니다.", "", *chapters, "",
                      "참고 자료", *[fill(x, V) for x in spec.get("sources", [])], "",
                      "내 종목의 적정 주가와 점수 확인: https://valuenote.co.kr/yt", "",
                      "*본 영상은 투자 교육용 정보이며, 특정 종목의 매수·매도 권유가 아닙니다. 적정 주가는 워렌 버핏·그레이엄·찰리 멍거의 방식으로 계산한 결과이며, 이 방식이 늘 맞지는 않습니다."])
    meta = {"id": spec["id"], "kind": "long", "title": fill(spec["title"], V)[:100], "description": desc, "tags": spec.get("tags", []),
            "scheduled_at": spec["scheduled_at"], "duration": round(total, 1), "data": data["raw"], "data_asof": data["raw"]["asof_iso"],
            "events": spec.get("events", []), "pinned_comment": fill(spec.get("pinned_comment", ""), V), "rendered_at": dt.datetime.now(dt.timezone.utc).isoformat(), "company": spec.get("company"),
            "qa": {"media": [[k, "lib", s["sc"]["v"].get("lib")] for k, s in enumerate(timeline) if s["sc"]["v"]["type"] == "media"] + [[k, "lib", s["sc"]["v"]["backdrop"]] for k, s in enumerate(timeline) if s["sc"]["v"].get("backdrop")],
                   "lines": [[round(x["start"] + a, 2), round(d_, 2), l, to_speech(l)] for x in timeline for (a, d_, l) in x["lines"]],
                   "scenes": [[round(x["start"], 2), round(x["dur"], 2), x["sc"]["v"]["type"]] for x in timeline], "voice": VOICE_LOG}}
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), ensure_ascii=False, indent=1)
    print(f"완료: {total / 60:.1f}분 → {out}")


if __name__ == "__main__":
    main()
