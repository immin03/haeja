"""ValueNote 릴스 엔진: 대본 JSON 하나 → 1080x1920 세로 영상(음성·자막·음악·모션)

대본(spec) 형식
{
  "id": "R01", "title": "...", "scheduled_at": "2026-10-17T21:00:00+09:00",
  "mood": "tense" | "calm",
  "caption": "인스타·쓰레드 본문 (고지문은 게시할 때 자동으로 붙음)",
  "hashtags": [...], "threads_tag": "...",
  "scenes": [ { "type": ..., "lines": [{"cap": ["자막 1줄", "자막 2줄"], "say": "생략하면 자막을 읽음"}], ...옵션 } ]
}
"cap"만 있으면 "lines": [{"cap": cap}] 로 본다. 숫자는 자동으로 한글 발음으로 읽는다.

장면 종류
  hook      큰 숫자 카운트 + 충격  : top, num{from,to,fmt(pct|won|int),dec,suffix}, tone(loss|gold), label
  line      선 차트(1~2개 계열)    : series[{name,v[]}], x[], chips[구간별 문구], end(마지막 문구), fmt
  run       오르내림 반복 + 돈 계산 : alt[+,-], days, mult[1,3], names[], money(만 원), note
            (2번째 줄 음성에서 손실 도장이 찍힌다)
  compare   좌우 카드              : title, l{label,v,sub,tone}, r{...}
  bars      가로 막대 비교          : title, items[{label,v,text,tone}]
  list      항목이 차례로 등장       : title, items[]
  statement 큰 결론 문장            : l1, l2, fx(melt|none), sub[왼쪽, 오른쪽] 또는 note
  cta       마지막 장 (고정 문구)
"""
import math, os, sys, json, subprocess
import numpy as np
from scipy import signal
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from korean import to_speech  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 44100
NAVY = (11, 27, 51); NAVY2 = (22, 44, 78); GOLD = (214, 172, 82); GOLD_D = (150, 118, 52)
IVORY = (246, 241, 232); GRAY = (140, 152, 172); DIM = (78, 94, 122); LOSS = (232, 104, 80)
GAIN = (96, 196, 150); GRID = (38, 58, 92)
TONE = {"loss": LOSS, "gold": GOLD, "good": GAIN, "gray": GRAY, "ivory": IVORY}
DISC_VIDEO = "*본 콘텐츠는 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아닙니다"
CTA_SAY = "밸류 노트. 더 현명한 투자를 시작하세요."

_fc = {}
def F(w, s):
    if (w, s) not in _fc: _fc[(w, s)] = ImageFont.truetype(os.path.join(HERE, "fonts", f"SUIT-{w}.ttf"), s)
    return _fc[(w, s)]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_io(t): t = clamp(t); return 3 * t * t - 2 * t * t * t
def back(t, s=1.9): t = clamp(t) - 1; return 1 + (s + 1) * t ** 3 + s * t ** 2
def prog(t, a, b, f=ease): return f((t - a) / (b - a)) if b > a else 1.0
def lerp(a, b, p): return a + (b - a) * p
def mix(c1, c2, p): return tuple(int(lerp(a, b, clamp(p))) for a, b in zip(c1, c2))

def fmt_won(v):  # v: 만 원 단위
    v = round(v)
    if abs(v) >= 10000:
        e, m = divmod(abs(v), 10000)
        s = f"{e}억" + (f" {m:,}만" if m else "") + " 원"
        return ("-" if v < 0 else "") + s
    return f"{v:,}만 원"

def fmt_num(v, f):
    fmt = f.get("fmt", "int"); dec = f.get("dec", 0); suf = f.get("suffix", "")
    if fmt == "won": return fmt_won(v)
    s = f"{v:,.{dec}f}"
    if fmt == "pct": return (("+" if v > 0 and f.get("plus", True) else "") + s + "%")
    return ("+" if f.get("sign") and v > 0 else "") + s + suf

# ── 배경 ──────────────────────────────────────────────────────
BGW, BGH = W + 200, H + 200
_yy, _xx = np.mgrid[0:BGH, 0:BGW]
_base = np.zeros((BGH, BGW, 3), np.float32)
_g = (_yy / BGH)[..., None]
_base[:] = np.array(NAVY2) * (1 - _g) + np.array(NAVY) * _g
_dots = (_xx % 60 < 3) & (_yy % 60 < 3)
_base[_dots] = _base[_dots] * 0.55 + np.array(GRID, np.float32) * 0.45 + 6
BG = Image.fromarray(np.clip(_base, 0, 255).astype(np.uint8))
del _yy, _xx, _base, _g, _dots
GR = 520
_rng = np.random.default_rng(7)
DUST = [(float(_rng.uniform(0, W)), float(_rng.uniform(0, H)), float(_rng.uniform(18, 46)), float(_rng.uniform(2, 5)), float(_rng.uniform(0, 6.28))) for _ in range(26)]
_gy, _gx = np.mgrid[-GR:GR, -GR:GR]
GLOW = Image.fromarray((np.clip(1 - np.sqrt(_gx ** 2 + _gy ** 2) / GR, 0, 1) ** 2.2 * 70).astype(np.uint8), "L")

def background(t, warm=0.0):
    ox = int(100 + 60 * math.sin(t * 0.4)); oy = int(100 - t * 9) % 60 + 40
    img = BG.crop((ox, oy, ox + W, oy + H))
    layer = Image.new("RGB", (W, H), mix(GOLD_D, LOSS, warm))
    mask = Image.new("L", (W, H), 0)
    mask.paste(GLOW, (int(W * .5 + 260 * math.sin(t * .5)) - GR, int(H * .38 + 140 * math.cos(t * .35)) - GR))
    out = Image.composite(layer, img, mask)
    d = ImageDraw.Draw(out)
    for (x0, y0, sp, r, ph) in DUST:  # 천천히 떠오르는 먼지 입자: 화면이 멈춰 보이지 않게
        y = (y0 - t * sp) % (H + 80) - 40; x = x0 + 18 * math.sin(t * .6 + ph)
        a_ = .35 + .35 * math.sin(t * 1.3 + ph)
        d.ellipse([x - r, y - r, x + r, y + r], fill=mix(NAVY, GOLD, a_ * .55))
    return out

# ── 텍스트·도형 헬퍼 ───────────────────────────────────────────
_tc = {}
def text_img(s, font, fill):
    k = (s, font.path, font.size, fill)
    if k not in _tc:
        bb = font.getbbox(s, anchor="ls")
        im = Image.new("RGBA", (bb[2] - bb[0] + 20, bb[3] - bb[1] + 20), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10 - bb[0], 10 - bb[1]), s, font=font, fill=fill, anchor="ls")
        _tc[k] = im
    return _tc[k]

def fit_font(s, w, size, maxw):
    while size > 30 and F(w, size).getlength(s) > maxw: size -= 4
    return F(w, size)

def pop(img, s, font, fill, center, scale=1.0, alpha=1.0, dy=0):
    if alpha <= 0.01 or scale <= 0.01 or not s: return
    im = text_img(s, font, fill)
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    img.paste(im, (int(center[0] - im.width / 2), int(center[1] - im.height / 2 + dy)), im)

def appear(img, t, t0, s, font, fill, center, dur=0.4, rise=40, popin=False):
    p = prog(t, t0, t0 + dur)
    pop(img, s, font, fill, center, scale=max(0, back((t - t0) / dur)) if popin else 1.0, alpha=p, dy=int((1 - p) * rise))

def glow_lines(img, lines):
    small = Image.new("RGB", (W // 3, H // 3)); ds = ImageDraw.Draw(small)
    for pts, col, w in lines:
        if len(pts) > 1: ds.line([(x / 3, y / 3) for x, y in pts], fill=col, width=max(2, w // 2), joint="curve")
    blur = small.filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BILINEAR)
    img.paste(Image.fromarray(np.clip(np.asarray(img, np.int16) + (np.asarray(blur, np.int16) * .9).astype(np.int16), 0, 255).astype(np.uint8)))
    d = ImageDraw.Draw(img)
    for pts, col, w in lines:
        if len(pts) > 1: d.line(pts, fill=col, width=w, joint="curve")

def partial(pts, upto):
    if upto <= 0: return [pts[0]]
    n = int(upto); seg = pts[: min(n, len(pts) - 1) + 1]
    if n < len(pts) - 1:
        f = upto - n; p0, p1 = pts[n], pts[n + 1]
        seg = seg + [(lerp(p0[0], p1[0], f), lerp(p0[1], p1[1], f))]
    return seg

def value_at(v, upto):
    if upto >= len(v) - 1: return v[-1]
    n = int(upto); return lerp(v[n], v[n + 1], upto - n)

def dot(d, p, c, r=13, ring=0.0):
    if ring > 0:
        rr = r + ring * 30
        d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], outline=mix(NAVY, c, 1 - ring), width=4)
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=c)
    d.ellipse([p[0] - r * .45, p[1] - r * .45, p[0] + r * .45, p[1] + r * .45], fill=IVORY)

def arrow(d, x, y, col, s=1.0):
    d.line([(x - 22 * s, y), (x + 18 * s, y)], fill=col, width=int(6 * s))
    d.polygon([(x + 28 * s, y), (x + 8 * s, y - 16 * s), (x + 8 * s, y + 16 * s)], fill=col)

def shake(img, t, t0, dur=0.3, k=16):
    if t0 <= t < t0 + dur:
        a = (1 - (t - t0) / dur) * k
        return img.transform(img.size, Image.AFFINE, (1, 0, a * math.sin(t * 90), 0, 1, a * math.cos(t * 70)), fillcolor=NAVY)
    return img

CX0, CX1, CY0, CY1 = 170, 910, 600, 1130
def chart_frame(img, lo, hi, base=None, xlabels=None, xs=None, t=0, t0=0):
    d = ImageDraw.Draw(img)
    ymap = lambda v: CY1 - (v - lo) / (hi - lo) * (CY1 - CY0)
    if base is not None:
        y = ymap(base)
        for x in range(CX0, CX1, 26): d.line([(x, y), (x + 13, y)], fill=GRID, width=3)
        d.text((CX0 - 22, y), f"{base:g}", font=F("Medium", 32), fill=GRAY, anchor="rm")
    if xlabels:
        for i, lbl in enumerate(xlabels):
            d.text((xs[i], CY1 + 56), lbl, font=F("Medium", 32), fill=mix(NAVY, GRAY, prog(t, t0 + .1 + i * .08, t0 + .4 + i * .08)), anchor="mm")
    return ymap

def legend(img, names, cols, a):
    d = ImageDraw.Draw(img)
    x = W / 2 - sum(F("SemiBold", 36).getlength(n) + 110 for n in names) / 2
    for n, c in zip(names, cols):
        d.line([(x, 520), (x + 50, 520)], fill=mix(NAVY, c, a), width=8)
        d.text((x + 66, 520), n, font=F("SemiBold", 36), fill=mix(NAVY, c, a), anchor="lm")
        x += F("SemiBold", 36).getlength(n) + 110

# ── 장면 그리기 (u = 장면 안 시간, L = 줄별 [시작, 길이]) ──────────
def s_hook(img, u, sc, L, T):
    num = sc["num"]; impact = 0.85
    col_end = TONE.get(sc.get("tone", "loss"), LOSS)
    if sc.get("top"): appear(img, u, .1, sc["top"], fit_font(sc["top"], "Bold", 66, 900), GRAY, (W / 2, 610))
    p = prog(u, .25, impact, ease_io)
    v = lerp(num.get("from", 0), num["to"], p)
    s = fmt_num(round(v, num.get("dec", 0)), num)
    sc_ = 1.0 + 0.18 * math.exp(-max(0, u - impact) * 7) * (u >= impact)
    big = fit_font(s, "Heavy", num.get("size", 300), 980)
    pop(img, s, big, mix(IVORY, col_end, p), (W / 2, 900), scale=sc_ * (.6 + .4 * prog(u, .2, .5)), alpha=prog(u, .2, .4))
    d = ImageDraw.Draw(img)
    if u >= impact:
        q = prog(u, impact, impact + .6); r = 120 + q * 520
        d.ellipse([W / 2 - r, 900 - r, W / 2 + r, 900 + r], outline=mix(NAVY, col_end, 1 - q), width=int(6 * (1 - q)) + 1)
    if sc.get("label"):
        appear(img, u, 1.15, sc["label"], fit_font(sc["label"], "ExtraBold", 62, 940), GOLD, (W / 2, 1140))
        w = prog(u, 1.35, 1.85) * 560
        ImageDraw.Draw(img).line([(W / 2 - w / 2, 1210), (W / 2 + w / 2, 1210)], fill=GOLD, width=5)
    return shake(img, u, impact, .35, 18)

def s_line(img, u, sc, L, T):
    ser = sc["series"]; n = len(ser[0]["v"])
    cols = [GRAY, GOLD] if len(ser) == 2 else [GOLD]
    allv = [x for s in ser for x in s["v"]]
    lo, hi = min(allv), max(allv); pad = (hi - lo) * .15 or 1; lo -= pad; hi += pad
    xs = [CX0 + 30 + i * (CX1 - CX0 - 60) / (n - 1) for i in range(n)]
    ymap = chart_frame(img, lo, hi, sc.get("base"), sc.get("x"), xs, u, 0)
    if len(ser) > 1: legend(img, [s["name"] for s in ser], cols, prog(u, 0, .4))
    a0, dur = .15, max(1.0, L[0][1] * .85)
    upto = prog(u, a0, a0 + dur, lambda x: clamp(x)) * (n - 1)
    pts = [[(xs[i], ymap(v)) for i, v in enumerate(s["v"])] for s in ser]
    segs = [partial(p, upto) for p in pts]
    glow_lines(img, [(sg, c, 12 if c == GOLD else 9) for sg, c in zip(segs, cols)])
    d = ImageDraw.Draw(img); ring = (u * 1.6) % 1
    f = sc.get("fmt", {"fmt": "int"})
    for k, (sg, c) in enumerate(zip(segs, cols)):
        dot(d, sg[-1], c, 15 if c == GOLD else 13, ring)
        val = fmt_num(value_at(ser[k]["v"], upto), f)
        right = sg[-1][0] > 760
        off = (-40 if c == GOLD else 44) * (1 if not right else -1) if len(ser) > 1 else -44
        d.text((sg[-1][0] + (-30 if right else 28), sg[-1][1] + off), val,
               font=F("Heavy", 56) if c == GOLD else F("ExtraBold", 44), fill=c, anchor="rm" if right else "lm")
    chips = sc.get("chips", [])
    done = upto >= n - 1
    if done and sc.get("end"):
        t_end = a0 + dur
        appear(img, u, t_end, sc["end"], fit_font(sc["end"], "Heavy", 72, 960), TONE.get(sc.get("end_tone", "loss"), LOSS), (W / 2, 410), dur=.3, popin=True)
    elif chips:
        seg = min(int(upto), len(chips) - 1); t_seg = a0 + dur * seg / (n - 1)
        txt = chips[seg]
        tone = LOSS if txt.strip().startswith("-") else IVORY
        appear(img, u, t_seg, txt, fit_font(txt, "Heavy", 72, 960), tone, (W / 2, 410), dur=.3, popin=True)
    return img

def s_run(img, u, sc, L, T):
    up, dn = sc.get("alt", [5, -5]); days = sc.get("days", 20); mult = sc.get("mult", [1, 3])
    names = sc.get("names", ["지수", "3배 레버리지"]); money = sc.get("money", 1000)
    ser = []
    for m in mult:
        v = [100.0]
        for i in range(days): v.append(v[-1] * (1 + m * (up if i % 2 == 0 else dn) / 100))
        ser.append(v)
    cols = [GRAY, GOLD] if len(ser) == 2 else [GOLD]
    allv = [x for s in ser for x in s]; lo, hi = min(allv) - 4, max(allv) + 4
    xs = [CX0 + 10 + i * (CX1 - CX0 - 20) / days for i in range(days + 1)]
    res = L[1][0] + L[1][1] * .55 if len(L) > 1 else L[0][0] + L[0][1]
    img = background(T, warm=prog(u, res - 1.2, res) * .8)
    ymap = chart_frame(img, lo, hi, 100)
    d = ImageDraw.Draw(img)
    draw_end = L[1][0] - .1 if len(L) > 1 else L[0][1]
    upto = prog(u, .15, draw_end, lambda x: clamp(x)) * days
    pts = [[(xs[i], ymap(v)) for i, v in enumerate(s)] for s in ser]
    segs = [partial(p, upto) for p in pts]
    last = LOSS if u >= res else GOLD
    glow_lines(img, [(sg, GRAY if c == GRAY else last, 10 if c == GOLD else 7) for sg, c in zip(segs, cols)])
    d = ImageDraw.Draw(img)
    for sg, c in zip(segs, cols): dot(d, sg[-1], GRAY if c == GRAY else last, 13 if c == GOLD else 11)
    day = min(days, int(upto) + 1)
    d.text((W / 2, CY1 + 56), f"{sc.get('note', '매일 +5%, -5% 반복')} · {day}거래일", font=F("Medium", 34), fill=GRAY, anchor="mm")
    xc = [W / 2 - 230, W / 2 + 200] if len(ser) == 2 else [W / 2]
    for k, (s, c) in enumerate(zip(ser, cols)):
        cur = money * value_at(s, upto) / 100
        appear(img, u, .1 + k * .05, names[k], F("Bold", 38), c, (xc[k], 310), dur=.3)
        pop(img, fmt_won(cur), F("Heavy", 80) if c == GOLD else F("ExtraBold", 66), LOSS if (c == GOLD and u >= res) else c, (xc[k], 395), alpha=prog(u, .1, .4))
        if len(ser) == 2 and k == 0 and u >= res - .9:
            loss = round(money * s[-1] / 100) - money
            appear(img, u, res - .9, fmt_won(loss) if loss < 0 else "+" + fmt_won(loss), F("ExtraBold", 50), GRAY, (xc[k], 470), dur=.3, popin=True)
    if u >= res:
        loss = round(money * ser[-1][-1] / 100) - money
        stamp_txt = sc.get("stamp") or fmt_won(loss)
        q = (u - res) / .35; scl = 1.6 - .6 * ease(q)
        st = text_img(stamp_txt, F("Heavy", 150), LOSS); pad = 34
        box = Image.new("RGBA", (st.width + pad * 2, st.height + pad * 2), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle([4, 4, box.width - 5, box.height - 5], 30, fill=(20, 16, 30, 225), outline=LOSS, width=8)
        box.paste(st, (pad, pad), st)
        box = box.rotate(-6, resample=Image.BICUBIC, expand=True)
        box = box.resize((int(box.width * scl), int(box.height * scl)), Image.BICUBIC)
        al = prog(u, res, res + .15)
        if al < 1: box.putalpha(box.getchannel("A").point(lambda v: int(v * al)))
        img.paste(box, (int(W / 2 - box.width / 2), int(820 - box.height / 2)), box)
        img = shake(img, u, res, .3, 16)
    return img

def s_compare(img, u, sc, L, T):
    sides = [sc["l"], sc["r"]]
    for i, sd in enumerate(sides):
        p = prog(u, .1 + i * .45, .7 + i * .45)
        col = TONE.get(sd.get("tone", "gray" if i == 0 else "loss"), GRAY)
        cx = 290 + i * 500; off = int((1 - p) * 60)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([cx - 220, 560 + off, cx + 220, 1160 + off], 36, outline=mix(NAVY, col, p), width=4, fill=NAVY)
        lab = sd.get("label", "")
        lines = lab.split("\n")
        for j, ln in enumerate(lines):
            d.text((cx, 660 + off + (j - (len(lines) - 1) / 2) * 52), ln, font=fit_font(ln, "Bold", 44, 400), fill=mix(NAVY, IVORY if col == GRAY else col, p), anchor="mm")
        v = sd["v"]; fv = fit_font(v, "Heavy", 150, 410)
        sc_ = back((u - .1 - i * .45) / .5) if u > .1 + i * .45 else 0
        pop(img, v, fv, col, (cx, 890 + off), scale=max(0, sc_), alpha=p)
        if sd.get("sub"):
            ImageDraw.Draw(img).text((cx, 1080 + off), sd["sub"], font=fit_font(sd["sub"], "SemiBold", 38, 410), fill=mix(NAVY, GRAY, p), anchor="mm")
    if sc.get("title"):
        appear(img, u, 1.0, sc["title"], fit_font(sc["title"], "Heavy", 80, 960), TONE.get(sc.get("title_tone", "gold"), GOLD), (W / 2, 410), dur=.4, popin=True)
    return img

def s_bars(img, u, sc, L, T):
    items = sc["items"]; mx = max(abs(i["v"]) for i in items) or 1
    if sc.get("title"): appear(img, u, .05, sc["title"], fit_font(sc["title"], "Heavy", 68, 960), IVORY, (W / 2, 410), dur=.35)
    gap = min(170, 560 / max(1, len(items))); y0 = 640 + (560 - gap * len(items)) / 2
    step = min(.45, max(.2, L[0][1] * .7 / len(items)))
    for k, it in enumerate(items):
        t0 = .25 + k * step; p = prog(u, t0, t0 + .55)
        y = y0 + k * gap; col = TONE.get(it.get("tone", "gold"), GOLD)
        d = ImageDraw.Draw(img)
        d.text((140, y - 34), it["label"], font=fit_font(it["label"], "SemiBold", 38, 800), fill=mix(NAVY, IVORY, prog(u, t0 - .1, t0 + .2)), anchor="lm")
        wmax = 640; w = wmax * abs(it["v"]) / mx * p
        d.rounded_rectangle([140, y, 140 + max(16, w), y + 44], 22, fill=mix(NAVY, col, min(1, p * 2)))
        if p > .05:
            d.text((140 + max(16, w) + 22, y + 22), it.get("text", f"{it['v']:g}"), font=F("Heavy", 54), fill=col, anchor="lm")
    return img

def s_list(img, u, sc, L, T):
    items = sc["items"]
    if sc.get("title"): appear(img, u, .05, sc["title"], fit_font(sc["title"], "Heavy", 68, 960), IVORY, (W / 2, 410), dur=.35)
    span = L[0][1] * .9; gap = 118; y0 = 600
    for k, it in enumerate(items):
        t0 = .15 + span * k / max(1, len(items))
        p = prog(u, t0, t0 + .35)
        if p <= 0: continue
        y = y0 + k * gap; x = 140 + (1 - p) * -60
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([x, y - 46, x + 800, y + 46], 24, fill=mix(NAVY, (24, 46, 82), p), outline=mix(NAVY, GOLD_D, p), width=2)
        if " " in it and len(it.split(" ", 1)[0]) <= 3:
            k_, rest = it.split(" ", 1)
            d.ellipse([x + 22, y - 32, x + 86, y + 32], fill=mix(NAVY, GOLD, p))
            d.text((x + 54, y), k_, font=F("Heavy", 40 if len(k_) <= 2 else 30), fill=NAVY, anchor="mm")
            d.text((x + 112, y), rest, font=fit_font(rest, "Bold", 46, 660), fill=mix(NAVY, IVORY, p), anchor="lm")
        else:
            d.text((x + 36, y), it, font=fit_font(it, "Bold", 46, 740), fill=mix(NAVY, IVORY, p), anchor="lm")
    return img

DRIPS = [(-300, 0.0, 26), (-190, 0.25, 20), (-60, 0.1, 30), (40, 0.4, 22), (150, 0.15, 28), (260, 0.3, 20)]
def s_statement(img, u, sc, L, T):
    fx = sc.get("fx", "none")
    img = background(T, warm=.9 if fx == "melt" else 0)
    V = L[0][1]
    appear(img, u, .05, sc["l1"], fit_font(sc["l1"], "ExtraBold", 80, 960), IVORY, (W / 2, 720))
    t2 = min(.55, V * .35)
    tone = TONE.get(sc.get("tone", "loss" if fx == "melt" else "gold"), GOLD)
    sc_ = back((u - t2) / .4) if u > t2 else 0
    pop(img, sc["l2"], fit_font(sc["l2"], "Heavy", 128, 980), tone, (W / 2, 890), scale=max(0, sc_), alpha=prog(u, t2, t2 + .4))
    d = ImageDraw.Draw(img)
    if fx == "melt":
        for x, delay, w in DRIPS:
            q = prog(u, t2 + .35 + delay, t2 + 1.5 + delay, ease_io)
            if q > 0:
                Lh = 40 + q * 240; cx = W / 2 + x; y0 = 950
                d.rounded_rectangle([cx - w / 2, y0, cx + w / 2, y0 + Lh], int(w / 2), fill=LOSS)
                d.ellipse([cx - w * .8, y0 + Lh - w * .9, cx + w * .8, y0 + Lh + w * .7], fill=LOSS)
    else:
        wl = prog(u, t2 + .3, t2 + .8) * 420
        d.line([(W / 2 - wl / 2, 990), (W / 2 + wl / 2, 990)], fill=tone, width=6)
    ys = 1300 if fx == "melt" else 1120
    if sc.get("sub"):
        a, b = sc["sub"]
        appear(img, u, t2 + .6, a, F("Bold", 52), IVORY, (W / 2 - 200, ys))
        appear(img, u, t2 + .8, b, fit_font(b, "Heavy", 60, 380), tone, (W / 2 + 210, ys), popin=True)
        if u > t2 + .7: arrow(ImageDraw.Draw(img), W / 2, ys, IVORY, 1.0)
    if sc.get("note"):
        for j, ln in enumerate(sc["note"].split("\n")):
            appear(img, u, t2 + .7 + j * .15, ln, fit_font(ln, "SemiBold", 44, 960), GRAY, (W / 2, ys + j * 64))
    return img

def s_cta(img, u, sc, L, T):
    V = L[0][1]
    pw = prog(u, .1, .55)
    pop(img, "ValueNote", F("Heavy", 120), GOLD, (W / 2, 560), scale=.85 + .15 * back((u - .1) / .5), alpha=pw)
    if pw > .5:
        sx = lerp(-200, W + 200, prog(u, .6, 1.4, ease_io))
        sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).polygon([(sx - 40, 470), (sx + 30, 470), (sx - 10, 650), (sx - 80, 650)], fill=150)
        wm = text_img("ValueNote", F("Heavy", 120), GOLD).getchannel("A")
        m = Image.new("L", (W, H), 0); m.paste(wm, (int(W / 2 - wm.width / 2), int(560 - wm.height / 2)))
        img.paste(Image.new("RGB", (W, H), (255, 244, 210)), (0, 0), Image.fromarray(np.minimum(np.asarray(sh), np.asarray(m))))
    d = ImageDraw.Draw(img); ul = prog(u, .45, .95) * 300
    d.line([(W / 2 - ul / 2, 650), (W / 2 + ul / 2, 650)], fill=GOLD, width=6)
    if pw > .3: d.text((W / 2, 708), "밸 류 노 트", font=F("SemiBold", 40), fill=mix(NAVY, (170, 180, 200), prog(u, .35, .8)), anchor="mm")
    l1, l2 = sc.get("l1", "더 현명한 투자를"), sc.get("l2", "시작하세요")
    appear(img, u, V * .42, l1, fit_font(l1, "Heavy", 92, 980), IVORY, (W / 2, 850), dur=.45, rise=50)
    appear(img, u, V * .62, l2, fit_font(l2, "Heavy", 92, 980), IVORY, (W / 2, 975), dur=.45, rise=50)
    tb = V * .85; pb = prog(u, tb, tb + .4)
    if pb > 0:
        pulse = .5 + .5 * math.sin((u - tb) * 7); bw, bh = 640, 120; cx, cy = W / 2, 1160 + (1 - pb) * 40
        if pb >= 1:
            g = int(10 + pulse * 14)
            d.rounded_rectangle([cx - bw / 2 - g, cy - bh / 2 - g, cx + bw / 2 + g, cy + bh / 2 + g], 70, outline=mix(NAVY, GOLD_D, .6 - pulse * .4), width=3)
        d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], 60, fill=mix(NAVY, GOLD, pb))
        d.text((cx - 30, cy), "프로필 링크에서 시작", font=F("ExtraBold", 48), fill=mix(GOLD, NAVY, pb), anchor="mm")
        arrow(d, cx + 245 + 8 * math.sin(u * 8), cy, mix(GOLD, NAVY, pb), 1.1)
    return img

# 앱 화면: 휴대폰 틀 안에서 스크롤 → 강조 박스 + 설명
_shots = {}
def shot(name):
    if name not in _shots: _shots[name] = Image.open(os.path.join(HERE, "screens", name + ".png")).convert("RGB")
    return _shots[name]

PX0, PY0, PW, PH = 170, 370, 740, 950   # 휴대폰 바깥 틀
_boxes = {}
def find_box(name, q, min_w=500):
    """캡처 때 저장한 블록 위치에서 q 글자를 포함하는 가장 작은 블록"""
    if name not in _boxes: _boxes[name] = json.load(open(os.path.join(HERE, "screens", name + ".json"), encoding="utf-8"))
    hits = [x["b"] for x in _boxes[name] if q in x["t"] and x["b"][2] - x["b"][0] >= min_w]
    if not hits: raise ValueError(f"화면 {name}에서 '{q}'를 찾지 못했습니다")
    return min(hits, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))

def resolve_stops(sc, view, height):
    out = []
    for st in sc.get("stops") or [{"y": 0}]:
        st = dict(st)
        if st.get("find"):
            b = find_box(sc["shot"], st["find"], st.get("min_w", 500))
            st["box"] = [b[0] + 6, b[1], b[2] - 6, b[3]]
        if st.get("box") and "y" not in st: st["y"] = st["box"][1] - view * .22
        st["y"] = clamp(st.get("y", 0), 0, max(0, height - view))
        out.append(st)
    return out

def s_screen(img, u, sc, L, T):
    im = shot(sc["shot"]); pad = 14; iw = PW - pad * 2; ih = PH - pad * 2
    k = iw / im.width; view = ih / k
    if "_stops" not in sc: sc["_stops"] = resolve_stops(sc, view, im.height)
    stops = sc["_stops"]
    V = (L[-1][0] + L[-1][1] - L[0][0]) if L else 3
    span = max(.8, V / len(stops))
    idx = min(len(stops) - 1, int(max(0, u - .1) / span)); t0 = .1 + idx * span
    prev_y = stops[idx - 1]["y"] if idx else 0
    yv = lerp(prev_y, stops[idx]["y"], prog(u, t0, t0 + min(.7, span * .35), ease_io))
    yv = clamp(yv, 0, max(0, im.height - view))
    enter = prog(u, 0, .45)
    oy = int((1 - enter) * 120)
    d = ImageDraw.Draw(img)
    # 그림자 + 틀
    sh = Image.new("RGBA", (PW + 80, PH + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([40, 50, PW + 40, PH + 50], 64, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    img.paste(sh, (PX0 - 40, PY0 - 40 + oy), sh)
    d.rounded_rectangle([PX0, PY0 + oy, PX0 + PW, PY0 + PH + oy], 60, fill=(16, 22, 34), outline=(70, 86, 112), width=3)
    crop = im.crop((0, int(yv), im.width, int(yv + view))).resize((iw, ih), Image.LANCZOS)
    m = Image.new("L", (iw, ih), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, iw - 1, ih - 1], 48, fill=255)
    sx, sy = PX0 + pad, PY0 + pad + oy
    st = stops[idx]; hp = prog(u, t0 + min(.7, span * .35), t0 + min(.7, span * .35) + .35)
    if st.get("box") and hp > 0:
        x0, y0, x1, y1 = st["box"]
        bx = [x0 * k, max(4, (y0 - yv) * k), x1 * k, min(ih - 4, (y1 - yv) * k)]
        dim = Image.new("RGBA", (iw, ih), (6, 12, 24, int(150 * hp)))
        ImageDraw.Draw(dim).rounded_rectangle(bx, 18, fill=(0, 0, 0, 0))
        crop = crop.convert("RGBA"); crop.alpha_composite(dim); crop = crop.convert("RGB")
    img.paste(crop, (sx, sy), m)
    d = ImageDraw.Draw(img)
    if st.get("box") and hp > 0:
        x0, y0, x1, y1 = st["box"]
        bx = [sx + x0 * k - 6, sy + max(4, (y0 - yv) * k) - 6, sx + x1 * k + 6, sy + min(ih - 4, (y1 - yv) * k) + 6]
        d.rounded_rectangle(bx, 22, outline=mix(NAVY, GOLD, hp), width=6)
    d.rounded_rectangle([PX0 + PW - 190, PY0 + PH - 70 + oy, PX0 + PW - 30, PY0 + PH - 26 + oy], 22, fill=(11, 27, 51))
    d.text((PX0 + PW - 110, PY0 + PH - 48 + oy), "예시 계정 화면", font=F("SemiBold", 24), fill=GOLD, anchor="mm")
    lab = st.get("label") or sc.get("title")
    if lab:
        appear(img, u, t0 + .05, lab, fit_font(lab, "Heavy", 60, 980), IVORY, (W / 2, 320), dur=.35, popin=True)
    return img

DRAW = {"hook": s_hook, "line": s_line, "run": s_run, "compare": s_compare, "bars": s_bars,
        "list": s_list, "statement": s_statement, "cta": s_cta, "screen": s_screen}
NO_CAPTION = {"statement", "cta", "list"}

# ── 타임라인 ─────────────────────────────────────────────────
def plan(spec, speak):
    """각 장면의 음성을 만들고 시작·끝 시간을 정한다"""
    t = 0.0; scenes = []
    speed = spec.get("speed", 1.1)
    for sc in spec["scenes"]:
        lines = sc.get("lines") or [{"cap": sc.get("cap"), "say": sc.get("say")}]
        if sc["type"] == "cta" and not lines[0].get("say") and not lines[0].get("cap"):
            lines = [{"cap": None, "say": CTA_SAY}]
        L = []; u = .1; vo = []
        for ln in lines:
            txt = ln.get("say") or " ".join(ln.get("cap") or [])
            if sc["type"] == "statement" and not txt: txt = f"{sc['l1']}, {sc['l2']}."
            if VERIFY:
                import verify
                if ln.get("cap") and verify.score(" ".join(ln["cap"]), txt) < .8:
                    LINT.append(f"자막과 음성이 다름: {ln['cap']} ↔ {txt}")
                a = verify.speak_checked(to_speech(txt), ln.get("speed", speed), speak, SR, VLOG)
            else:
                a = speak(to_speech(txt), ln.get("speed", speed))
            L.append([u, len(a) / SR, ln.get("cap")]); vo.append((u, a))
            u += len(a) / SR + .12
        dur = u + {"hook": .1, "cta": .8}.get(sc["type"], .2)
        if sc["type"] == "hook": dur = max(dur, 2.6)
        if sc["type"] == "statement": dur = max(dur, 2.5)
        scenes.append({"sc": sc, "start": t, "dur": dur, "L": L, "vo": vo})
        t += dur
    return scenes, t

def caption(img, u, L):
    for i, (a, v, cap) in enumerate(L):
        if not cap: continue
        e = a + v; nxt = L[i + 1][0] if i + 1 < len(L) else 999
        if not (a - .05 <= u < nxt - .02): continue
        d = ImageDraw.Draw(img); font = F("Bold", 54)
        maxw = max(d.textlength(l, font=font) for l in cap)
        if maxw > 960: font = F("Bold", int(54 * 960 / maxw)); maxw = 960
        total = sum(len(l) for l in cap); rev = prog(u, a + .05, e - .15, lambda x: clamp(x)) * total
        fade = prog(u, a - .05, a + .15); y0 = 1395 - (len(cap) - 1) * 36
        bar = Image.new("RGBA", (int(maxw + 52), len(cap) * 74 + 24), (8, 18, 36, int(150 * fade)))
        img.paste(bar, (int(W / 2 - bar.width / 2), y0 - 48 + int((1 - fade) * 16)), bar)
        d = ImageDraw.Draw(img)
        for li, line in enumerate(cap):
            rp = prog(u, a + li * .18, a + li * .18 + .3)
            y = y0 + li * 74 + int((1 - fade) * 16) + int((1 - rp) * 22); x0 = W / 2 - d.textlength(line, font=font) / 2
            d.text((x0, y), line, font=font, fill=mix(NAVY, DIM, fade), anchor="lm")
            k = int(clamp(rev, 0, len(line)))
            if k > 0: d.text((x0, y), line[:k], font=font, fill=IVORY, anchor="lm")
            rev -= len(line)
        return

def logo(d, y):
    """상단 로고: 영문 ValueNote, 그 아래 한글 밸류노트"""
    d.text((W / 2, y), "ValueNote", font=F("ExtraBold", 46), fill=GOLD, anchor="mm")
    d.text((W / 2, y + 44), "밸 류 노 트", font=F("Medium", 26), fill=(156, 166, 188), anchor="mm")

def camera(img, u, s):
    """장면 내내 천천히 다가가는 카메라 + 새 문장이 나올 때마다 살짝 튀는 박자. 화면이 멈춰 있는 순간을 없앤다"""
    z = 1 + .045 * ease_io(clamp(u / max(s["dur"], .1)))
    for (a, v, cap) in s["L"]:
        if u >= a: z += .018 * math.exp(-(u - a) * 5)
    dx = 10 * math.sin(u * .7); dy = 8 * math.cos(u * .5)
    if z < 1.001 and abs(dx) < .5: return img
    w, h = int(W * z), int(H * z)
    big = img.resize((w, h), Image.BILINEAR)
    x0 = int((w - W) / 2 + dx); y0 = int((h - H) / 2 + dy)
    x0 = max(0, min(w - W, x0)); y0 = max(0, min(h - H, y0))
    return big.crop((x0, y0, x0 + W, y0 + H))

def frame(T, scenes, total):
    s = next((x for x in scenes if x["start"] <= T < x["start"] + x["dur"]), scenes[-1])
    sc = s["sc"]; u = T - s["start"]
    warm = 0.0
    if sc["type"] == "hook": warm = prog(u, .85, 1.15) * (1 - prog(u, 2.0, s["dur"]))
    img = background(T, warm)
    img = DRAW[sc["type"]](img, u, sc, s["L"], T)
    img = camera(img, u, s)
    if sc["type"] not in NO_CAPTION: caption(img, u, s["L"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=(20, 36, 62)); d.rectangle([0, 0, int(W * T / total), 8], fill=GOLD)
    if sc["type"] not in ("cta", "screen"): logo(d, 236)
    d.text((W / 2, 1650), DISC_VIDEO, font=F("Medium", 25), fill=(112, 124, 148), anchor="mm")
    for x in scenes[1:]:
        q = (T - (x["start"] - .12)) / .3
        if 0 <= q <= 1:
            px = lerp(-600, W + 600, ease_io(q)); ov = Image.new("L", (W, H), 0)
            ImageDraw.Draw(ov).polygon([(px - 260, 0), (px + 40, 0), (px - 560, H), (px - 860, H)], fill=235)
            img.paste(Image.new("RGB", (W, H), GOLD), (0, 0), ov)
    return img

# ── 오디오: 직접 합성한 배경음악·효과음 + 내레이션 (저작권 없음) ──
def note(n): return 440.0 * 2 ** ((n - 69) / 12)
MOODS = {"tense": [[57, 60, 64, 67, 71], [53, 57, 60, 64, 67], [48, 55, 59, 64, 67], [55, 59, 62, 64, 67]],
         "calm": [[53, 57, 60, 64, 67], [55, 59, 62, 65, 69], [52, 55, 59, 62, 67], [57, 60, 64, 67, 71]]}

def build_audio(scenes, total, mood, path):
    n = int(SR * total); L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(7)
    def add(at, sig, gl=1.0, gr=1.0):
        i = int(at * SR)
        if i >= n or i < 0: return
        m = min(len(sig), n - i); L[i:i + m] += sig[:m] * gl; R[i:i + m] += sig[:m] * gr
    beat = 60 / 96; bar = 4 * beat
    def ep(f, dur, amp):
        s = np.arange(int(SR * dur)) / SR
        return amp * (np.sin(2 * np.pi * f * s) + .32 * np.sin(4 * np.pi * f * s) * np.exp(-s * 4) + .08 * np.sin(6 * np.pi * f * s) * np.exp(-s * 8)) * np.minimum(1, s / .006) * np.exp(-s * 2.2) * (1 + .12 * np.sin(2 * np.pi * 4.5 * s))
    def kick():
        s = np.arange(int(SR * .45)) / SR
        return .9 * np.sin(2 * np.pi * (45 * s + (110 / 18) * (1 - np.exp(-s * 18)))) * np.exp(-s * 7)
    def hat(a):
        x = signal.lfilter(*signal.butter(2, 7000 / (SR / 2), "high"), rng.standard_normal(int(SR * .06)))
        return a * x * np.exp(-np.arange(len(x)) / SR * 60)
    def snare():
        s = np.arange(int(SR * .22)) / SR
        x = signal.lfilter(*signal.butter(2, [1200 / (SR / 2), 6000 / (SR / 2)], "band"), rng.standard_normal(len(s)))
        return .28 * x * np.exp(-s * 18) + .12 * np.sin(2 * np.pi * 190 * s) * np.exp(-s * 25)
    def bass(f, dur):
        s = np.arange(int(SR * dur)) / SR
        return .34 * np.tanh(1.6 * np.sin(2 * np.pi * f * s)) * np.minimum(1, s / .01) * np.exp(-s * 1.6)
    chords = MOODS.get(mood, MOODS["tense"])
    drop = .95 if scenes[0]["sc"]["type"] == "hook" else .3
    cta_at = next((s["start"] for s in scenes if s["sc"]["type"] == "cta"), total)
    s = np.arange(int(SR * drop)) / SR
    pad = sum(.05 * np.sin(2 * np.pi * note(k) * s + .3 * np.sin(2 * np.pi * .7 * s)) for k in chords[0]) * np.linspace(0, 1, len(s)) ** 1.5
    add(0, pad, 1, .9)
    x = signal.lfilter(*signal.butter(2, 2500 / (SR / 2), "low"), rng.standard_normal(len(s)) * np.linspace(0, 1, len(s)) ** 2) * .22
    add(0, x, .9, 1)
    t0, bi = drop, 0
    while t0 < total:
        ch = chords[bi % 4] if t0 < cta_at else ([53, 57, 60, 64, 67] if bi % 2 == 0 else [48, 55, 59, 62, 64, 67])
        for off, amp in ((0, .11), (2.5 * beat, .07)):
            for j, k in enumerate(ch): add(t0 + off + j * .012, ep(note(k), 2.2, amp * (.8 if j else 1)), 1 - .15 * (j % 2), .85 + .15 * (j % 2))
        add(t0, bass(note(ch[0] - 12), 1.6)); add(t0 + 2.5 * beat, bass(note(ch[0] - 12), .9))
        for b in range(4):
            tb = t0 + b * beat
            if b in (0, 2): add(tb, kick())
            if b == 3 and bi % 2: add(tb + .5 * beat, kick() * .6)
            if b in (1, 3): add(tb, snare(), .9, 1)
            for e in (0, .55): add(tb + e * beat, hat(.07 if e else .10), .7, 1)
        t0 += bar; bi += 1
    fo = int(SR * .8); L[-fo:] *= np.linspace(1, 0, fo); R[-fo:] *= np.linspace(1, 0, fo)
    music = np.stack([L, R], 1)
    fx = np.zeros(n)
    def addfx(at, sig):
        i = int(at * SR)
        if 0 <= i < n: m = min(len(sig), n - i); fx[i:i + m] += sig[:m]
    s = np.arange(int(SR * .7)) / SR
    impact = .7 * np.sin(2 * np.pi * (70 - 40 * s) * s) * np.exp(-s * 6) + .15 * rng.standard_normal(len(s)) * np.exp(-s * 30)
    def tick(f):
        s_ = np.arange(int(SR * .05)) / SR; return .15 * np.sin(2 * np.pi * f * s_) * np.exp(-s_ * 80)
    for x_ in scenes[1:]:
        m = int(SR * .4); w = signal.lfilter(*signal.butter(2, 1800 / (SR / 2), "low"), rng.standard_normal(m))
        addfx(x_["start"] - .15, .35 * w * np.sin(np.linspace(0, np.pi, m)) ** 2)
    for x_ in scenes:
        st, ty, Lx, sc = x_["start"], x_["sc"]["type"], x_["L"], x_["sc"]
        if ty == "hook":
            addfx(st + .85, impact)
            for k in range(9): addfx(st + .3 + k * .065, tick(900 + 70 * k))
        elif ty == "run":
            days = sc.get("days", 20); end = Lx[1][0] - .1 if len(Lx) > 1 else Lx[0][1]
            for k in range(days): addfx(st + .15 + (end - .15) * k / days, tick(1300 if k % 2 == 0 else 1000))
            if len(Lx) > 1: addfx(st + Lx[1][0] + Lx[1][1] * .55, impact * .9)
        elif ty == "compare": addfx(st + .55, impact * .45)
        elif ty == "statement": addfx(st + min(.55, Lx[0][1] * .35), impact * .7)
        elif ty in ("bars", "list"):
            for k in range(len(sc["items"])): addfx(st + .25 + k * .3, tick(1100))
        elif ty == "cta":
            s2 = np.arange(int(SR * 1.6)) / SR
            addfx(st + .1, sum(.07 * np.sin(2 * np.pi * note(k) * s2) * np.exp(-s2 * 3) for k in (76, 79, 84)))
    voice = np.zeros(n)
    for x_ in scenes:
        for at, a in x_["vo"]:
            i = int((x_["start"] + at) * SR); m = min(len(a), n - i); voice[i:i + m] += a[:m]
    voice = voice / (np.max(np.abs(voice)) + 1e-9) * .92
    env = signal.lfilter([1 - .9995], [1, -.9995], np.abs(voice))
    env = np.convolve(env, np.ones(2205) / 2205, "same"); env = np.clip(env / (env.max() + 1e-9) * 2.5, 0, 1)
    mm = music / (np.max(np.abs(music)) + 1e-9) * .34 * (1 - .7 * env)[:, None]
    out = np.tanh((mm + (voice + fx * .8)[:, None]) * 1.1) / np.tanh(1.1)
    import soundfile as sf
    sf.write(path, (out / np.max(np.abs(out)) * .95).astype(np.float32), SR, subtype="PCM_16")

# ── 실행 ─────────────────────────────────────────────────────
VERIFY = os.environ.get("REELS_VERIFY", "1") != "0"
VLOG, LINT = [], []
MAX_SEC = 30  # 릴스 길이 상한 (목표 20초 안팎)

def render(spec, outdir, stills=None):
    from tts import speak
    os.makedirs(outdir, exist_ok=True)
    VLOG.clear(); LINT.clear()
    scenes, total = plan(spec, speak)
    if total > MAX_SEC and not spec.get("allow_long"):
        raise RuntimeError(f"{spec['id']}: {total:.1f}초 — 최대 {MAX_SEC}초를 넘습니다. 대본을 줄여야 합니다(목표 20초 안팎)")
    if VERIFY:
        import verify
        for w in LINT: print("  ⚠", w)
        for v in VLOG:
            mark = "OK" if v["score"] >= v["pass"] else ("△" if v["score"] >= v["floor"] else "✗")
            print(f"  음성 {mark} {v['score']:.2f} (시도 {v['tries']}) {v['text']}")
            if v["score"] < v["pass"]: print(f"        들린 말: {v['heard']}")
        bad = [v for v in VLOG if v["score"] < v["floor"]]
        json.dump({"lines": VLOG, "lint": LINT}, open(os.path.join(outdir, "voice_check.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if bad: raise RuntimeError(f"{spec['id']}: 음성 검수 실패 {len(bad)}줄 — 대본을 고쳐야 합니다")
    if stills is not None:
        for ts in stills: frame(ts, scenes, total).save(os.path.join(outdir, f"still_{ts:.1f}.png"))
        return total
    wav = os.path.join(outdir, "_mix.wav"); build_audio(scenes, total, spec.get("mood", "tense"), wav)
    out = os.path.join(outdir, "reel.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium",
           "-crf", "22", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cover_t = scenes[0]["start"] + min(1.6, scenes[0]["dur"] - .1)
    for i in range(int(total * FPS)):
        im = frame(i / FPS, scenes, total)
        if abs(i / FPS - cover_t) < .5 / FPS: im.save(os.path.join(outdir, "cover.jpg"), quality=88)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait(); os.remove(wav)
    return total

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "out", spec["id"])
    if len(sys.argv) > 3 and sys.argv[3] == "stills":
        print(render(spec, out, [float(x) for x in sys.argv[4].split(",")]))
    else:
        print("길이", round(render(spec, out), 1), "초 →", out)
