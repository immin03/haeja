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
import render as R  # noqa: E402  (글꼴·자막·음성 속도·배경음악·사진 움직임을 함께 쓴다)
from render import F, AD, clamp, ease, fill, wrap, count_text, W, H, FPS, SR, ROOT  # noqa: E402
from korean import to_speech  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "scripts", "reels"))

# 색
NAVY = (11, 27, 51); NAVY2 = (24, 46, 82); GOLD = (214, 172, 82); GOLD_D = (168, 120, 34); GOLD_L = (228, 199, 141)
PAPER = (244, 243, 239); GRID = (228, 226, 220); INK = (24, 32, 46); MUTED = (120, 128, 140); LINE = (200, 204, 212)
IVORY = (246, 241, 232); RED = (214, 82, 62); WHITE = (255, 255, 255)
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
            k = T("kicker"); f0 = F("Bold", 36)
            if k: center_text(d, H / 2 - 150, k, f0, A(GOLD_L, a))
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
            if b > .9: chip(d, W - 520, y - 70, fill(av.get("label", "평균"), V), F("ExtraBold", 34), "gold", pop(u, at_time(av.get("at"), lines) + .6))
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
            if cur and not on: col = tuple(int(c * .45 + 235 * .55) for c in col)
            ww = 1000 * val / mx * p; d.rounded_rectangle([600, y, 600 + max(8, ww), y + 76], 10, fill=A(col, min(1, p * 3)))
            d.text((620 + ww, y + 12), f"{val:g}{v.get('suffix', '')}", font=F("ExtraBold", 46), fill=A(t["ink"], p))
        if cur and cur.get("note"):
            b = pop(u, at_time(cur.get("at"), lines)); y = 300 + cur["i"] * 130
            chip(d, 1300, y + 2, fill(cur["note"], V), F("ExtraBold", 36), "navy", b)
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
        x = 160; y = 600  # 실사 위에 핵심 숫자가 하나씩 쌓인다 (자막 띠 위, 칩 폭은 글자에 맞춘다)
        for i, c in enumerate(v.get("chips", [])):
            a = pop(u, at_time(c.get("at"), lines)); s1, s2 = fill(c["v"], V), fill(c.get("l", ""), V)
            f1 = fitF(d, s1, "Heavy", 64, 720); f2 = fitF(d, s2, "SemiBold", 32, 720)
            cw_ = max(300, d.textlength(s1, font=f1), d.textlength(s2, font=f2)) + 64
            if a > 0:
                d.rounded_rectangle([x, y + 16 * (1 - a), x + cw_, y + 180 + 16 * (1 - a)], 16, fill=(10, 18, 32, int(205 * a)), outline=(255, 255, 255, int(60 * a)), width=2)
                d.text((x + 32, y + 24 + 16 * (1 - a)), s1, font=f1, fill=A(GOLD_L, a)); d.text((x + 32, y + 118 + 16 * (1 - a)), s2, font=f2, fill=A(IVORY, a))
            x += cw_ + 28
        if v.get("caption"):
            a = pop(u, at_time(v.get("caption_at"), lines)); s = fill(v["caption"], V); f = fitF(d, s, "Heavy", 80, W - 320)
            d.text((160, 200 + 20 * (1 - a)), s, font=f, fill=A(WHITE, a))
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


# ── 안전 영역: 로고·장 제목(위)과 자막(아래)을 그래픽이 가리지 않게 ──
SAFE = (110, 152, 1810, 900)   # 왼쪽, 위, 오른쪽, 아래 (천천히 다가가는 3% 확대까지 감안한 값)


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


# ── 실사 (원고가 지정한 파일만) ──
def media_source(v, n_frames, seed):
    lib = os.path.join(ROOT, "scripts", "blog", "media", "lib"); f = v.get("lib")
    pth = os.path.join(lib, f) if f else None
    if not pth or not os.path.exists(pth): return lambda u: background("dark")
    if f.endswith(".jpg") or f.endswith(".png"):
        frames = R.photo_frames(pth, n_frames, seed)
    else:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pth], capture_output=True, text=True).stdout.strip() or 0)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-stream_loop", "-1", "-ss", "0", "-i", pth, "-frames:v", str(n_frames), "-vf",
                              f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=rgb24", "-f", "rawvideo", "-"], capture_output=True).stdout
        fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3) if raw else np.zeros((1, H, W, 3), np.uint8)
        frames = [fr[min(i, len(fr) - 1)] for i in range(n_frames)]
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
    lg = logo_dark if theme == "light" else logo_light
    img.paste(lg, (60, 42), lg)
    kf = F("Bold", 24); ks = "밸류노트"; kx = 60 + lg.width / 2 - (d.textlength(ks, font=kf) + 3 * 6) / 2
    for ch in ks: d.text((kx, 42 + lg.height + 6), ch, font=kf, fill=A(t["ink"] if theme == "light" else IVORY, .8)); kx += d.textlength(ch, font=kf) + 6
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
    tw = d.textlength(l, font=f); x = (W - tw) / 2; y = H - 128
    d.rounded_rectangle([x - 20, y - 8, x + tw + 20, y + 56], 12, fill=(8, 14, 26, int(205 * a)))
    d.text((x, y), l, font=f, fill=(255, 255, 255, int(255 * a)))
    for m in re.finditer(r"[+\-−]?\d[\d,.]*(?:\s?(?:조|억|만|천))*(?:\s?\d[\d,]*\s?(?:억|만|천))*\s?(?:원|%p|%|배|점|년|분기|곳|개)?", l):
        tx = x + d.textlength(l[:m.start()], font=f); d.text((tx, y), m.group().rstrip(), font=f, fill=(*GOLD_L, int(255 * a)))


def make_theme(n, seed=11):
    """밸류노트 시그니처 배경음악 v2 (직접 합성, 저작권 걱정 없음) — 116BPM 차분한 딥하우스 (2026-10-22 운영자: 더 차분하게, 베이스는 더 강하게, 중독성 있게).
    굵은 서브 베이스가 엇박으로 굴러가고, 따뜻한 일렉트릭 피아노 코드, 단순한 4음 훅이 2마디마다 돌아온다. 훅은 영상마다 같다."""
    from scipy import signal
    rng = np.random.default_rng(seed); L = np.zeros(n, np.float32); Rr = np.zeros(n, np.float32); K = np.zeros(n, np.float32)
    bpm = 116; b = 60 / bpm; bar = 4 * b; nt = lambda k: 440 * 2 ** ((k - 69) / 12)
    def add(at, x, gl=1.0, gr=1.0, kick=False):
        i = int(at * SR)
        if i >= n or i < 0: return
        m = min(len(x), n - i)
        if kick: K[i:i + m] += x[:m]
        else: L[i:i + m] += x[:m] * gl; Rr[i:i + m] += x[:m] * gr
    tt = lambda d: np.arange(int(SR * d)) / SR
    t = tt(.35); kick = (np.sin(2 * np.pi * (42 * t + 70 / 16 * (1 - np.exp(-16 * t)))) * np.exp(-t * 7.5)).astype(np.float32) * .95
    nz = lambda d: rng.standard_normal(int(SR * d)).astype(np.float32)
    bp = signal.butter(2, [800 / (SR / 2), 2600 / (SR / 2)], "band"); hp = signal.butter(2, 6500 / (SR / 2), "high")
    clap = np.zeros(int(SR * .3), np.float32)
    for k in range(3): seg = signal.lfilter(*bp, nz(.3)) * np.exp(-tt(.3) * (60 if k < 2 else 14)); clap[int(k * .012 * SR):] += seg[: len(clap) - int(k * .012 * SR)]
    clap = (clap / np.abs(clap).max() * .24).astype(np.float32)
    ohat = (signal.lfilter(*hp, nz(.12)) * np.exp(-tt(.12) * 26) * .09).astype(np.float32)
    shk = (signal.lfilter(*hp, nz(.05)) * np.exp(-tt(.05) * 70) * .04).astype(np.float32)
    def bass(f, d):
        t = tt(d); env = np.minimum(1, t / .006) * np.minimum(1, (d - t) / .03) * np.exp(-t * 2.2)
        x = np.sin(2 * np.pi * f * t) * .9 + .35 * np.tanh(2.5 * np.sin(2 * np.pi * f * t))   # 굵은 서브 + 살짝 찌그러진 배음
        return (signal.lfilter(*signal.butter(2, 380 / (SR / 2)), x * env) * .72).astype(np.float32)
    def keys(fs, d, amp=.1):
        t = tt(d); x = sum(np.sin(2 * np.pi * f * t + .7 * np.exp(-t * 3) * np.sin(2 * np.pi * 2 * f * t)) for f in fs)
        return (x / len(fs) * np.minimum(1, t / .01) * np.exp(-t * 2.4) * amp).astype(np.float32)
    def pluck(f, d=.45):
        t = tt(d); x = np.sin(2 * np.pi * f * t + .9 * np.exp(-t * 6) * np.sin(2 * np.pi * f * 3 * t)) + .3 * signal.square(2 * np.pi * f * t, .25)
        x = signal.lfilter(*signal.butter(2, 1900 / (SR / 2)), x) * np.minimum(1, t / .004) * np.exp(-t * 5.5)
        return (x * .14).astype(np.float32)
    prog = [(45, [57, 60, 64, 67]), (41, [57, 60, 64, 65]), (43, [55, 59, 62, 67]), (40, [55, 59, 64, 67])]   # Am7  Fmaj7  G6  Em7
    groove = [(.5, .32), (1.5, .3), (1.75, .2), (2.5, .32), (3.5, .45)]                                     # 엇박으로 굴러가는 베이스 (박, 길이)
    hook = [(0, 76), (1, 72), (2, 74), (3, 76), (5, 69), (6, 67), (7, 69)]                                   # 8분음표 위치: E-C-D-E | A-G-A
    t0, bi = 0.0, 0; total = n / SR
    while t0 < total:
        root, ch = prog[bi % 4]; sec = (bi // 16) % 4
        for k in range(4):
            add(t0 + k * b, kick, kick=True)
            if k in (1, 3) and bi >= 2: add(t0 + k * b, clap, .9, 1)
            add(t0 + k * b + b / 2, ohat, .8, 1)
            for q in (1, 3): add(t0 + k * b + q * b / 4, shk, 1, .7)
        for pos, d in groove: add(t0 + pos * b, bass(nt(root - 12 if root < 40 else root - 12), d * b * 1.6))
        add(t0, keys([nt(x) for x in ch], bar * .9, .09), .9, 1); add(t0 + 2.5 * b, keys([nt(x) for x in ch[1:]], b * 1.2, .06), 1, .9)
        if sec != 2 and bi % 2 == 0:
            for pos, k in hook: add(t0 + pos * b / 2, pluck(nt(k)), .85, 1)
            if bi % 4 == 2:  # 메아리 (훅이 귀에 남도록)
                for pos, k in hook[:4]: add(t0 + pos * b / 2 + 3 * b / 4, pluck(nt(k)) * .35, 1, .7)
        t0 += bar; bi += 1
    env = np.ones(n, np.float32); per = int(b * SR); dip = (1 - .45 * np.exp(-np.arange(per) / SR * 8)).astype(np.float32)
    for i in range(0, n, per): env[i:i + per] = dip[: min(per, n - i)]
    L = L * env + K; Rr = Rr * env + K
    m = np.stack([L, Rr], 1); m = signal.lfilter(*signal.butter(2, 7500 / (SR / 2), "low"), m, axis=0)
    fi = int(SR * 1.0); m[:fi] *= np.linspace(0, 1, fi)[:, None]; fo = int(SR * 3); m[-fo:] *= np.linspace(1, 0, fo)[:, None]
    m = np.tanh(m / (np.abs(m).max() + 1e-9) * 1.3) / np.tanh(1.3)
    return m.astype(np.float32)


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
    tv = spec["thumb"]; TW, TH_ = 1280, 720; YEL = (255, 206, 46)
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
        a = int(170 * max(0, 1 - k / (TW * .75)) ** 1.3); g.line([k, 0, k, TH_], fill=(0, 0, 0, a))
    th = Image.alpha_composite(th, sh); sh2 = Image.new("RGBA", (TW, TH_)); g2 = ImageDraw.Draw(sh2)
    for y in range(TH_ // 2, TH_): g2.line([0, y, TW, y], fill=(0, 0, 0, int(120 * (y - TH_ / 2) / (TH_ / 2))))
    th = Image.alpha_composite(th, sh2); d = ImageDraw.Draw(th)
    l1, l2 = fill(tv["l1"], V), fill(tv["l2"], V); maxw = TW - 120
    f1 = F("Heavy", 112)
    while d.textlength(l1, font=f1) > maxw: f1 = F("Heavy", f1.size - 4)
    f2 = F("Heavy", 190)
    while d.textlength(l2, font=f2) > maxw: f2 = F("Heavy", f2.size - 6)
    y2 = TH_ - 70 - f2.size; y1 = y2 - f1.size - 18
    for (txt, f, y, col) in ((l1, f1, y1, WHITE), (l2, f2, y2, YEL)):
        sd_ = Image.new("RGBA", (TW, TH_)); ImageDraw.Draw(sd_).text((64 + 6, y + 8), txt, font=f, fill=(0, 0, 0, 200))
        th = Image.alpha_composite(th, sd_.filter(ImageFilter.GaussianBlur(6))); d = ImageDraw.Draw(th)
        d.text((64, y), txt, font=f, fill=col, stroke_width=max(4, f.size // 22), stroke_fill=(0, 0, 0))
    lg = R.LOGO.resize((int(R.LOGO.width * .36), int(R.LOGO.height * .36)), Image.LANCZOS); th.alpha_composite(lg, (TW - lg.width - 40, 36))
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
    mus = make_theme(len(mix)) * (MUS_LEVEL * boost * (1 - MUS_DUCK * env))[:, None]
    st_ = np.stack([mix, mix], 1) + mus; st_ = (st_ / max(1.0, np.abs(st_).max() / .95)).astype(np.float32)
    wav = os.path.join(out, "voice.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", wav], input=st_.tobytes(), check=True)
    if "--stills" in sys.argv:  # 검수용: 장면마다 마지막 문장을 말하는 순간 한 장씩
        sd = os.path.join(out, "stills"); os.makedirs(sd, exist_ok=True); chapter = ""
        for k, s in enumerate(timeline):
            sc = s["sc"]; typ = sc["v"]["type"]; theme = sc.get("bg") or ("dark" if typ in ("title", "question", "end", "media") else "light")
            if sc.get("chapter"): chapter = sc["chapter"]
            fit = safe_fit(sc, s, V, theme); media = media_source(sc["v"], int(s["dur"] * FPS) + 2, k) if typ == "media" else None
            lt = s["lines"][-1]; u = min(s["dur"] - .05, lt[0] + lt[1] * .9)
            img = apply_fit(draw(sc, V, u, s["lines"], "dark" if typ == "media" else theme, media), fit, theme)
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
        theme = sc.get("bg") or ("dark" if typ in ("title", "question", "end", "media") else "light")
        if sc.get("chapter"): chapter = sc["chapter"]
        media = media_source(sc["v"], n + 2, k) if typ == "media" else None
        fit = safe_fit(sc, s, V, theme)
        if fit: print(f"  안전 영역 맞춤: 장면 {k + 1} {typ} ×{fit['k']}", flush=True)
        src = fill(sc.get("src", sc["v"].get("src", "")), V); asof = V.get("asof") if sc.get("asof", typ not in ("title", "question", "end", "media")) else ""
        for i in range(n):
            u = i / FPS
            img = apply_fit(draw(sc, V, u, s["lines"], "dark" if typ == "media" else theme, media), fit, theme)
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
            "qa": {"media": [[k, "lib", s["sc"]["v"].get("lib")] for k, s in enumerate(timeline) if s["sc"]["v"]["type"] == "media"],
                   "lines": [[round(x["start"] + a, 2), round(d_, 2), l, to_speech(l)] for x in timeline for (a, d_, l) in x["lines"]],
                   "scenes": [[round(x["start"], 2), round(x["dur"], 2), x["sc"]["v"]["type"]] for x in timeline], "voice": VOICE_LOG}}
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), ensure_ascii=False, indent=1)
    print(f"완료: {total / 60:.1f}분 → {out}")


if __name__ == "__main__":
    main()
