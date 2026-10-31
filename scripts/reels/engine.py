"""ValueNote 릴스 엔진: 대본 JSON 하나 → 1080x1920 세로 영상(음성·자막·음악·모션)

대본(spec) 형식
{
  "id": "R01", "title": "...", "scheduled_at": "2026-10-17T21:00:00+09:00",
  "mood": "tense" | "calm",
  "caption": "인스타·쓰레드 본문 (고지문은 게시할 때 자동으로 붙음)",
  "hashtags": [...], "threads_tag": "...",
  "scenes": [ { "type": ..., "lines": [{"cap": ["자막 1줄", "자막 2줄"], "say": "생략하면 자막을 읽음"}]  ← 화면에는 한 번에 최대 2줄(넘치면 2줄씩 넘김, 2026-10-31), ...옵션 } ]
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
  race      여러 계열(2~4개)이 시간을 따라 함께 달리는 선 차트 + 위쪽 계열별 현황 카드 (은퇴 배당 비교, 2026-10-20)
            : x["2021.10", ...] 월 라벨, money(만 원, 처음 넣은 돈), series[{name, inc[], val[], cum[]}] (만 원 단위:
              inc = 그때 배당 수준으로 매달 받는 돈, val = 그때 평가 금액, cum = 그때까지 받은 배당 합계),
              events[{i, text}] 차트가 i번째 달을 지날 때 잠깐 뜨는 말풍선, ylab "매달 받는 배당"
  cta       마지막 장 (고정 문구)

썸네일(cover.jpg)
  영상 프레임을 그대로 잡지 않고 따로 그린다. 틀(남색·금색·로고)은 같지만 시리즈마다 그림이 다르다.
    F(기능)       → 앱 화면(screen) 장면      G(가이드) → 목록(list)·막대(bars) 장면
    A(기업)       → 막대(bars)·비교(compare)  M(금리)   → 선 차트(line)       R(교육) → 큰 숫자(hook)
  맞는 장면이 없으면 큰 숫자(hook)로 간다. "cover": "bars" 처럼 장면 종류나 장면 번호(0부터)로 직접 고를 수 있고,
  "tag": "오늘의 기업" 처럼 시리즈 표시를 바꿀 수 있다(기본은 제목의 " · " 앞부분).
"""
import sys as _bsys, os as _bos
_bsys.path.insert(0, _bos.path.join(_bos.path.dirname(_bos.path.abspath(__file__)), ".."))
from brand import paste_logo, logo_image  # noqa: E402  (2026-10-23 확정 로고)
import re
import math, os, sys, json, subprocess
import numpy as np
from scipy import signal
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from korean import to_speech  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 44100
NAVY = (11, 27, 51); NAVY2 = (22, 44, 78); GOLD = (224, 200, 150); GOLD_D = (150, 129, 88)
IVORY = (246, 241, 232); GRAY = (140, 152, 172); DIM = (78, 94, 122); LOSS = (255, 77, 109)
GAIN = (96, 196, 150); GRID = (38, 58, 92)
TONE = {"loss": LOSS, "gold": GOLD, "good": GAIN, "gray": GRAY, "ivory": IVORY}
DISC_VIDEO = "*본 콘텐츠는 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아닙니다"
CTA_SAY = "밸류 노트. 더 현명한 투자를 시작하세요."

# ── 댓글 키워드 → DM 정리본 (2026-10-21 운영자 요청) ──
# 대본에 "dm": {"keyword": "이자", ...} 가 있으면 마지막 장면에 "댓글에 '이자' 남기면 정리본 DM" 버튼과 안내 음성을 붙인다.
_BAT = {"0": 1, "1": 1, "2": 0, "3": 1, "4": 0, "5": 0, "6": 1, "7": 1, "8": 1, "9": 0}
def josa(w, a, b):
    """받침이 있으면 a(을), 없으면 b(를)"""
    c = str(w).strip()[-1:]
    if "가" <= c <= "힣": return a if (ord(c) - 0xAC00) % 28 else b
    if c in _BAT: return a if _BAT[c] else b
    return b
def dm_kw(spec):
    d = spec.get("dm") or {}
    return str(d.get("keyword") or "").strip()
YT_WORDS = ("유튜브", "풀버전", "풀영상", "전체 영상")
# 2026-10-30 운영 기준 정리: 릴스 끝은 "인스타·유튜브 팔로우" (10-27 운영자 '이런 유용한 정보를 더 얻고 싶으면 밸류노트 인스타그램과 유튜브를 팔로우', README 릴스=쇼츠 10-29) — 예전 "유튜브에서 검색"(10-25) 대체
OUTRO_SHORT = {"cap": ["이런 정보, 더 받고 싶다면", "밸류노트 인스타·유튜브 팔로우"], "say": "이런 유용한 정보를 더 얻고 싶으시면, 밸류노트 인스타그램과 유튜브를 팔로우하세요."}
# 쇼츠 끝 음성은 "좋아요와 구독"만, 풀버전 안내는 아래 자막으로만 (10-27 운영자: "마무리 음성은 더 많은 정보를 원하시면 좋아요와 구독만, 풀영상 안내는 하단 자막으로만")
SHORT_END_SAY = "더 많은 정보를 원하시면 좋아요와 구독 부탁드립니다."


def _points_yt(ln):
    t = " ".join(ln.get("cap") or []) + " " + (ln.get("say") or "")
    return any(w in t for w in YT_WORDS)


def cta_lines(spec, sc, lines):
    kw = dm_kw(spec)
    if sc["type"] != "cta": return lines
    if not kw:  # 정리본이 없는 릴스는 팔로우로 마무리 (2026-10-22 운영자: 모든 릴스에 정리본을 붙이지 않는다)
        yt = spec.get("platform") == "youtube"   # 유튜브 쇼츠는 '팔로우' 대신 '구독'
        sc["_follow"] = "yt" if yt else True
        if not yt and spec.get("end") == "follow":   # 마무리 문장을 대본에 직접 쓴 릴스 (2026-10-27 운영자: 인스타·유튜브 팔로우로 마무리) — 덧붙이지 않는다
            return lines
        # 끝맺음은 한 번만 (2026-10-26 운영자: "유튜브 밸류노트에서 확인하세요를 불필요하게 여러 번 반복한다, 마지막은 간단하게 하고 끝내자")
        lines = list(lines); ptr = [l for l in lines if _points_yt(l)]
        if yt and spec.get("end") == "subscribe":   # 롱폼 없는 단일 쇼츠는 구독·좋아요로 마무리 (2026-10-26 운영자) — 장면 문장 그대로, 링크 안내 없음
            sc["_follow"] = "sub"; return lines
        if yt:
            if ptr: return lines   # 장면이 이미 유튜브 풀영상을 가리키면 안내 문장을 더 붙이지 않는다 (화면의 '풀버전 보기' 버튼은 그대로)
            return lines + [{"cap": spec.get("full_cap", ["풀버전 ▶ 화면 아래 관련 영상"]), "say": SHORT_END_SAY}]   # 쇼츠 → 롱폼으로 (2026-10-22 운영자) · 음성은 좋아요·구독, 풀버전은 자막만 (10-27)
        if spec.get("outro"):   # 2026-10-25 운영자: 유튜브 쇼츠를 인스타에 다시 올릴 때 "유튜브에서 밸류노트 검색" 으로 마무리 — 한 문장만
            keep = [l for l in lines if not (_points_yt(l) and len(lines) > 1 and l is not lines[0])] or lines[:1]
            return keep + [OUTRO_SHORT]
        return list(lines) + [{"cap": ["밸류노트를 팔로우하고,", "매일 조금 더 현명한 투자 습관을 길러 보세요"], "say": "밸류노트를 팔로우하고, 매일 조금 더 현명한 투자 습관을 길러 보세요."}]
    sc["_dm"] = kw
    return list(lines) + [{"cap": None, "say": f"댓글에 {kw}{josa(kw, '을', '를')} 남기시면, 정리본을 보내 드립니다."}]

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
    s = f"{v:.{dec}f}" if f.get("year") else f"{v:,.{dec}f}"  # 연도는 쉼표 없이 (1,988년 → 1988년)
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

STILL = True   # 2026-10-23 운영자: "릴스에서 자꾸 화면이 움직여 글자나 그림이" → 글자·그림은 나타난 뒤 제자리에 멈춘다 (카메라 이동·확대·흔들림 끔. 배경 입자만 천천히 움직인다)

def shake(img, t, t0, dur=0.3, k=16):
    if YT or STILL: return img
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
    # 2026-10-19: 첫 화면은 질문이 주인공이다. top을 큰 흰 글씨(최대 두 줄)로 맨 먼저 띄우고, 숫자는 그 답으로 아래에 둔다
    if sc.get("top"):
        rows = sc["top"].split("\n")[:2]
        for k, row in enumerate(rows):
            y = (560 if len(rows) == 1 else 470 + k * 108)
            appear(img, u, .05 + k * .12, row, fit_font(row, "Heavy", 92, 960), IVORY, (W / 2, y), dur=.3, rise=30)
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
    n_ = max(1, len(items))
    gap = 190 if n_ <= 3 else 165 if n_ <= 4 else min(150, 760 / n_)
    big = n_ <= 4
    lf, vf, bh = (48, 64, 54) if big else (42, 56, 46)
    y0 = 900 - (n_ - 1) * gap / 2  # 막대 묶음을 화면 가운데에
    if sc.get("title"): appear(img, u, .05, sc["title"], fit_font(sc["title"], "Heavy", 76, 960), IVORY, (W / 2, max(400, y0 - 200)), dur=.35)
    step = min(.45, max(.2, L[0][1] * .7 / n_))
    for k, it in enumerate(items):
        t0 = .25 + k * step; p = prog(u, t0, t0 + .55)
        y = y0 + k * gap; col = TONE.get(it.get("tone", "gold"), GOLD)
        d = ImageDraw.Draw(img)
        d.text((120, y - bh / 2 - 34), it["label"], font=fit_font(it["label"], "SemiBold", lf, 840), fill=mix(NAVY, IVORY, prog(u, t0 - .1, t0 + .2)), anchor="lm")
        wmax = 620; w = wmax * abs(it["v"]) / mx * p
        d.rounded_rectangle([120, y - bh / 2, 120 + max(18, w), y + bh / 2], int(bh / 2), fill=mix(NAVY, col, min(1, p * 2)))
        if p > .05:
            d.text((120 + max(18, w) + 24, y), it.get("text", f"{it['v']:g}"), font=F("Heavy", vf), fill=col, anchor="lm")
    return img

def s_list(img, u, sc, L, T):
    """목록: 큰 카드, 화면 가운데에 모아 둔다 (위에 몰리고 아래가 비지 않게)"""
    items = sc["items"]; n_ = max(1, len(items))
    big = n_ <= 5
    gap, hh, fs = (192, 84, 102) if big else (161, 71, 86)
    y0 = 880 - (n_ - 1) * gap / 2
    if sc.get("title"): appear(img, u, .05, sc["title"], fit_font(sc["title"], "Heavy", 76, 960), IVORY, (W / 2, max(400, y0 - 170)), dur=.35)
    span = L[0][1] * .9
    for k, it in enumerate(items):
        t0 = (L[k][0] + .05) if len(L) == n_ and n_ > 1 else .15 + span * k / n_   # 줄마다 하나씩 말할 때는 그 줄에 맞춰 나타난다
        p = prog(u, t0, t0 + .35)
        if p <= 0: continue
        y = y0 + k * gap; x = 110 + (1 - p) * -60
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([x, y - hh, x + 860, y + hh], 28, fill=mix(NAVY, (24, 46, 82), p), outline=mix(NAVY, GOLD_D, p), width=2)
        # 동그라미 배지는 순위·번호(1위, 2, ①)일 때만. 문장 첫 낱말(예: '파는')이 배지로 들어가지 않게 한다
        if " " in it and re.fullmatch(r"\d{1,2}(위|\.)?|[①-⑩]", it.split(" ", 1)[0]):
            k_, rest = it.split(" ", 1); r_ = hh - 12
            d.ellipse([x + 26, y - r_, x + 26 + 2 * r_, y + r_], fill=mix(NAVY, GOLD, p))
            d.text((x + 26 + r_, y), k_, font=F("Heavy", 44 if len(k_) <= 2 else 32), fill=NAVY, anchor="mm")
            d.text((x + 52 + 2 * r_, y), rest, font=fit_font(rest, "Bold", fs, 860 - 80 - 2 * r_), fill=mix(NAVY, IVORY, p), anchor="lm")
        else:
            d.text((x + 40, y), it, font=fit_font(it, "Bold", fs, 790), fill=mix(NAVY, IVORY, p), anchor="lm")
    return img

def wrap_words(s, font, maxw):
    """단어 단위로 줄을 나눈다 (한국어 keep-all: 낱말 중간에서 끊지 않는다)"""
    out, cur = [], ""
    for w_ in s.split():
        nx = (cur + " " + w_).strip()
        if cur and font.getlength(nx) > maxw: out.append(cur); cur = w_
        else: cur = nx
    if cur: out.append(cur)
    return out

def s_who(img, u, sc, L, T):
    """회사 소개: 업종 꼬리표 → 회사 이름 → 한 문장 설명(카드 하나) → 핵심 사실 칩"""
    Y = 130  # 화면 가운데 쪽으로
    if sc.get("tag"): appear(img, u, .0, sc["tag"], F("Bold", 44), GOLD, (W / 2, 430 + Y), dur=.3)
    appear(img, u, .08, sc["name"], fit_font(sc["name"], "Heavy", 112, 960), IVORY, (W / 2, 540 + Y), dur=.35)
    d = ImageDraw.Draw(img)
    wl = prog(u, .3, .7) * 220
    d.line([(W / 2 - wl / 2, 624 + Y), (W / 2 + wl / 2, 624 + Y)], fill=GOLD, width=5)
    # 줄바꿈(\n)을 넣으면 그 자리에서 끊는다 (의미 단위). 없으면 낱말 단위로 자동
    def rows_for(f_, mw): return [r for part in sc["text"].split("\n") for r in wrap_words(part, f_, mw)]
    f = F("Bold", 54); rows = rows_for(f, 800)
    if len(rows) > 3: f = F("Bold", 46); rows = rows_for(f, 820)
    lh = int(f.size * 1.5); top = 690 + Y; h = lh * len(rows) + 70
    p = prog(u, .45, .85)
    if p > 0:
        d.rounded_rectangle([110, top, W - 110, top + h], 32, fill=mix(NAVY, (24, 46, 82), p), outline=mix(NAVY, GOLD_D, p), width=2)
        for i, r in enumerate(rows):
            pop(img, r, f, mix(NAVY, IVORY, p), (W / 2, top + 35 + lh * i + lh / 2), alpha=p)
    facts = sc.get("facts", [])
    if facts:
        y = top + h + 80; fs = F("Bold", 38)
        ws = [fs.getlength(x) + 56 for x in facts]; gap = 20; x0 = W / 2 - (sum(ws) + gap * (len(ws) - 1)) / 2
        for i, (x, w_) in enumerate(zip(facts, ws)):
            q = prog(u, .9 + i * .18, 1.25 + i * .18)
            if q <= 0: x0 += w_ + gap; continue
            d.rounded_rectangle([x0, y - 34, x0 + w_, y + 34], 34, outline=mix(NAVY, GOLD, q), width=2)
            pop(img, x, fs, mix(NAVY, GOLD, q), (x0 + w_ / 2, y), alpha=q)
            x0 += w_ + gap
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
        d.line([(W / 2 - wl / 2, 990), (W / 2 + wl / 2, 990)], fill=GOLD if tone == LOSS else tone, width=6)   # 2026-10-23: 핑크레드 강조 아래 밑줄은 아이보리
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
    # 2026-10-23 확정 로고 (scripts/brand.py): 커지며 나타나고, 빛이 한 번 스쳐 지나간다
    lg, pad, _ = logo_image(112, "dark")
    if pw > 0:
        k = .85 + .15 * back((u - .1) / .5); big = lg.resize((max(1, int(lg.width * k)), max(1, int(lg.height * k))), Image.LANCZOS)
        if pw < 1: big.putalpha(big.getchannel("A").point(lambda q: int(q * pw)))
        x0, y0 = int(W / 2 - big.width / 2), int(600 - big.height / 2); img.paste(big, (x0, y0), big)
        if pw > .5:
            sx = lerp(-200, W + 200, prog(u, .6, 1.4, ease_io))
            sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).polygon([(sx - 40, y0), (sx + 30, y0), (sx - 10, y0 + big.height), (sx - 80, y0 + big.height)], fill=150)
            m = Image.new("L", (W, H), 0); m.paste(big.getchannel("A").point(lambda q: 255 if q > 200 else 0), (x0, y0))
            img.paste(Image.new("RGB", (W, H), (255, 244, 210)), (0, 0), Image.fromarray(np.minimum(np.asarray(sh), np.asarray(m))))
    d = ImageDraw.Draw(img)
    l1, l2 = sc.get("l1", "더 현명한 투자를"), sc.get("l2", "시작하세요")
    appear(img, u, V * .42, l1, fit_font(l1, "Heavy", 92, 980), IVORY, (W / 2, 850), dur=.45, rise=50)
    appear(img, u, V * .62, l2, fit_font(l2, "Heavy", 92, 980), IVORY, (W / 2, 975), dur=.45, rise=50)
    if sc.get("_follow"):  # 팔로우 버튼: 안내 음성이 시작될 때 나타난다
        tb = L[-1][0] if len(L) > 1 else V * .85; pb = prog(u, tb, tb + .4)
        if pb > 0:
            pulse = .5 + .5 * math.sin((u - tb) * 7); bw, bh = 760, 132; cx, cy = W / 2, 1170 + (1 - pb) * 40
            if pb >= 1:
                g = int(10 + pulse * 14)
                d.rounded_rectangle([cx - bw / 2 - g, cy - bh / 2 - g, cx + bw / 2 + g, cy + bh / 2 + g], 76, outline=mix(NAVY, GOLD_D, .6 - pulse * .4), width=3)
            d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], 66, fill=mix(NAVY, GOLD, pb))
            yt = sc.get("_follow") == "yt"
            t1 = "▶  풀버전 보기" if yt else ("구독 · 좋아요" if sc.get("_follow") == "sub" else "+ 밸류노트 팔로우")
            if yt:
                t1 = "풀버전 보기"; tx0 = cx + 24 - d.textlength(t1, font=fit_font(t1, "ExtraBold", 58, bw - 160)) / 2 - 62
                d.polygon([(tx0, cy - 22), (tx0, cy + 22), (tx0 + 36, cy)], fill=mix(GOLD, NAVY, pb))
            d.text((cx + (24 if yt else 0), cy), t1, font=fit_font(t1, "ExtraBold", 58, bw - 160), fill=mix(GOLD, NAVY, pb), anchor="mm")
            if yt and pb > .6:   # 화면 아래 '관련 동영상' 링크 쪽으로 내려가는 화살표
                for k in range(3):
                    ph_ = ((u - tb) * 1.6 + k / 3) % 1; ay = (1440 + ph_ * 120) if YT else (1310 + ph_ * 220); aa = math.sin(ph_ * math.pi)
                    ImageDraw.Draw(img).line([(W / 2 - 46, ay), (W / 2, ay + 40), (W / 2 + 46, ay)], fill=mix(NAVY, GOLD, aa), width=10, joint="curve")
            if pb > .6 and not yt and not YT and sc.get("_follow") != "sub":
                t2 = "매일 조금 더 현명한 투자 습관"
                appear(img, u, tb + .25, t2, fit_font(t2, "SemiBold", 38, 960), (196, 204, 220), (W / 2, 1300), dur=.4, rise=20)
        return img
    kw = sc.get("_dm")
    if kw:   # 댓글 키워드 버튼: 안내 음성이 시작될 때 나타난다
        tb = L[1][0] if len(L) > 1 else V * .85; pb = prog(u, tb, tb + .4)
        if pb > 0:
            pulse = .5 + .5 * math.sin((u - tb) * 7); bw, bh = 920, 132; cx, cy = W / 2, 1170 + (1 - pb) * 40
            if pb >= 1:
                g = int(10 + pulse * 14)
                d.rounded_rectangle([cx - bw / 2 - g, cy - bh / 2 - g, cx + bw / 2 + g, cy + bh / 2 + g], 76, outline=mix(NAVY, GOLD_D, .6 - pulse * .4), width=3)
            d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], 66, fill=mix(NAVY, GOLD, pb))
            t1 = f"댓글에 '{kw}' 남기면 정리본 DM"
            d.text((cx, cy), t1, font=fit_font(t1, "ExtraBold", 50, bw - 90), fill=mix(GOLD, NAVY, pb), anchor="mm")
            if pb > .6:
                t2 = "핵심 숫자와 내 종목 점검법을 보내 드립니다"
                appear(img, u, tb + .25, t2, fit_font(t2, "SemiBold", 38, 960), (196, 204, 220), (W / 2, 1300), dur=.4, rise=20)
        return img
    tb = V * .85; pb = prog(u, tb, tb + .4)
    if pb > 0:
        pulse = .5 + .5 * math.sin((u - tb) * 7); bw, bh = 640, 120; cx, cy = W / 2, 1160 + (1 - pb) * 40
        if pb >= 1:
            g = int(10 + pulse * 14)
            d.rounded_rectangle([cx - bw / 2 - g, cy - bh / 2 - g, cx + bw / 2 + g, cy + bh / 2 + g], 70, outline=mix(NAVY, GOLD_D, .6 - pulse * .4), width=3)
        d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], 60, fill=mix(NAVY, GOLD, pb))
        d.text((cx - 30, cy), "프로필 링크에서 시작", font=F("ExtraBold", 48), fill=mix(GOLD, NAVY, pb), anchor="mm")
        arrow(d, cx + 245 + 8 * math.sin(u * 8), cy, mix(GOLD, NAVY, pb), 1.1)
        if pb > .3: d.text((cx, cy + 128), "자세한 내용은 캡션을 확인하세요", font=F("SemiBold", 40), fill=mix(NAVY, (200, 208, 222), min(1, (pb - .3) / .5)), anchor="mm")
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

# 은퇴 배당 비교: 여러 회사가 같은 시간을 함께 달리는 차트 (위: 원금·받은 돈 카드, 가운데: 매달 받는 배당 선)
RACE_COLS = [GOLD, (96, 196, 150), (112, 164, 240), (186, 146, 238)]
RX0, RX1, RY0, RY1 = 150, 790, 720, 1250

def won_short(v):
    """만 원 단위 → 카드용 짧은 금액: 1.53억 → '1.5억', 6,903만 → '6,903만'"""
    if abs(v) >= 10000:
        x = v / 10000
        return (f"{x:.1f}" if x < 100 else f"{x:.0f}") + "억"
    return f"{round(v):,}만"

def s_race(img, u, sc, L, T):
    ser = sc["series"][:4]; n = len(sc["x"]); k_ = len(ser)
    cols = [RACE_COLS[i] for i in range(k_)]
    a0 = .2; end = max(1.5, (L[-1][0] + L[-1][1]) * sc.get("pace", .86))
    upto = prog(u, a0, end, ease_io) * (n - 1)
    i_now = min(n - 1, int(round(upto)))
    d = ImageDraw.Draw(img)
    # 맨 위: 은퇴 N년 차 + 날짜
    yr = min(int(upto // 12) + 1, max(1, math.ceil((n - 1) / 12)))
    d.text((90, 372), f"은퇴 {yr}년 차", font=F("Heavy", 66), fill=IVORY, anchor="lm")
    d.text((990, 378), sc["x"][i_now], font=F("SemiBold", 40), fill=GRAY, anchor="rm")
    # 계열별 카드: 이름 / 원금(평가 금액) / 받은 돈
    cw = 900 / k_
    for j, s_ in enumerate(ser):
        x = 90 + j * cw; a = prog(u, .05 + j * .06, .35 + j * .06)
        nf = fit_font(s_["name"], "ExtraBold", 38, cw - 16)
        d.text((x, 458), s_["name"], font=nf, fill=mix(NAVY, cols[j], a), anchor="lm")
        v = value_at(s_["val"], upto); c = value_at(s_["cum"], upto)
        d.text((x, 516), "원금 " + won_short(v), font=fit_font("원금 " + won_short(v), "Heavy", 46 if k_ <= 3 else 40, cw - 12), fill=mix(NAVY, IVORY, a), anchor="lm")
        d.text((x, 568), "받은 돈 " + won_short(c), font=fit_font("받은 돈 " + won_short(c), "Medium", 32 if k_ <= 3 else 29, cw - 12), fill=mix(NAVY, GRAY, a), anchor="lm")
    # 차트 틀: 0부터, 깔끔한 눈금
    top_ = max(max(s_["inc"]) for s_ in ser); bot_ = min(min(s_["inc"]) for s_ in ser)
    step = next(st for st in (10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000) if (top_ - bot_ * .9) / st <= 4)
    lo = max(0, math.floor(bot_ * .9 / step) * step); hi = top_ + (top_ - lo) * .1
    ymap = lambda v: RY1 - (v - lo) / (hi - lo) * (RY1 - RY0)
    ga = prog(u, 0, .3)
    g = lo + step
    while g < hi:
        y = ymap(g)
        for x in range(RX0, RX1 + 120, 26): d.line([(x, y), (x + 12, y)], fill=mix(NAVY, GRID, ga), width=2)
        d.text((RX0 - 16, y), won_short(g), font=F("Medium", 28), fill=mix(NAVY, GRAY, ga), anchor="rm")
        g += step
    d.line([(RX0, RY1), (RX1 + 120, RY1)], fill=mix(NAVY, GRID, ga), width=3)
    xs = [RX0 + i * (RX1 - RX0) / (n - 1) for i in range(n)]
    for i, lb in enumerate(sc["x"]):  # 해마다 1월 아래 연도
        if lb.endswith(".01") or (i == 0 and int(lb[5:]) <= 7):
            d.text((xs[i], RY1 + 40), lb[:4], font=F("Medium", 28), fill=mix(NAVY, GRAY, ga), anchor="mm")
    busy = any(a0 + (end - a0) * ev["i"] / (n - 1) - .2 <= u < a0 + (end - a0) * ev["i"] / (n - 1) + 1.8 for ev in sc.get("events", []))
    if sc.get("ylab") and not busy: d.text((RX0 - 16, RY0 - 56), sc["ylab"], font=F("SemiBold", 30), fill=mix(NAVY, GRAY, ga), anchor="lm")
    pts = [[(xs[i], ymap(v)) for i, v in enumerate(s_["inc"])] for s_ in ser]
    segs = [partial(p, upto) for p in pts]
    order = list(range(k_))[::-1]  # 첫 계열(금색)을 맨 위에
    glow_lines(img, [(segs[j], cols[j], 10 if j == 0 else 8) for j in order])
    d = ImageDraw.Draw(img); ring = (u * 1.6) % 1
    # 끝 숫자: 겹치지 않게 위아래로 벌린다
    tags = sorted([(segs[j][-1][1], j) for j in range(k_)])
    ys_ = []
    for y, j in tags:
        y = max(RY0 - 10, min(RY1 - 20, y))
        if ys_ and y - ys_[-1][0] < 58: y = ys_[-1][0] + 58
        ys_.append((y, j))
    for y, j in ys_:
        p = segs[j][-1]; dot(d, p, cols[j], 13 if j == 0 else 11, ring if j == 0 else 0)
        val = "월 " + won_short(value_at(ser[j]["inc"], upto))
        d.text((p[0] + 26, y), val, font=F("Heavy", 44) if j == 0 else F("ExtraBold", 40), fill=cols[j], anchor="lm")
    for ev in sc.get("events", []):  # 말풍선: 그 달을 지날 때 1.6초
        t_ev = a0 + (end - a0) * ev["i"] / (n - 1)
        if t_ev <= u < t_ev + 1.6 and upto >= ev["i"]:
            q = prog(u, t_ev, t_ev + .3); f_ = fit_font(ev["text"], "Heavy", 50, 860)
            tw = f_.getlength(ev["text"]); cy = 662
            col = cols[ev.get("j", 0)]
            sc2 = max(.01, back((u - t_ev) / .3))
            pill = Image.new("RGBA", (int(tw + 64), 92), (0, 0, 0, 0))
            ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill.width - 1, 91], 46, fill=col + (235,))
            ImageDraw.Draw(pill).text((pill.width / 2, 46), ev["text"], font=f_, fill=NAVY, anchor="mm")
            pill = pill.resize((max(1, int(pill.width * sc2)), max(1, int(92 * sc2))), Image.BICUBIC)
            img.paste(pill, (int(W / 2 - pill.width / 2), int(cy - pill.height / 2)), pill)
    return img

# ── 유튜브 쇼츠 전용 장면 (2026-10-22 운영자 검수: "깔끔하게, 모션만 적절히") ──────────────
# 원칙: 글자는 흔들리지 않는다(카메라·흔들림 없음) · 모든 요소는 화면 가운데 정렬 · 위 제목 띠(0~330) 아래부터 자막(1330) 위까지만 쓴다
#       · 요소는 그 말을 하는 순간에 채워진다(막대가 자라고, 평균선이 그어지고, 식의 칸이 하나씩 찬다)
YT = False
YT_TITLE_Y, YT_CAP_Y, YT_CAP_X = 560, 1330, W / 2   # 자막은 오른쪽 좋아요·댓글·저장 버튼을 피해 살짝 왼쪽, 폭 800 이내

def join_fracs(parts):
    """한 번에 읽은 문장 안에서 각 자막 조각이 차지하는 시간 비율 (음절 수 + 쉼표·마침표 쉼)"""
    w = [len(re.sub(r"[^가-힣]", "", to_speech(p["say"]))) + 2.5 * len(re.findall(r"[,.?!]", p["say"])) for p in parts]
    tot = sum(w) or 1; out = []; acc = 0
    for x in w: out.append((acc / tot, (acc + x) / tot)); acc += x
    return out

def y_row(img, u, t0, row, size, fill, center):
    """'2018년 → 2019년' 같은 줄: 글꼴의 > 모양 대신 진짜 화살표를 그린다"""
    if "→" not in row: return y_fade(img, u, t0, row, fit_font(row, "Heavy", size, 960), fill, center)
    a, b = [x.strip() for x in row.split("→", 1)]; f = F("Heavy", size); gap = size * 1.5
    wa, wb = f.getlength(a), f.getlength(b); x0 = center[0] - (wa + gap + wb) / 2
    p = y_fade(img, u, t0, a, f, fill, (x0 + wa / 2, center[1]))
    y_fade(img, u, t0, b, f, fill, (x0 + wa + gap + wb / 2, center[1]))
    if p > 0:
        d = ImageDraw.Draw(img); ax = x0 + wa + gap / 2; cy = center[1] + 4; s_ = size / 80
        d.line([(ax - 34 * s_, cy), (ax + 18 * s_, cy)], fill=mix(NAVY, GOLD, p), width=int(8 * s_))
        d.polygon([(ax + 36 * s_, cy), (ax + 12 * s_, cy - 20 * s_), (ax + 12 * s_, cy + 20 * s_)], fill=mix(NAVY, GOLD, p))
    return p

def y_at(L, i, frac=0.0):
    """i번째 음성 줄의 시작(+그 줄 길이의 frac) 시각. 줄이 없으면 마지막 줄 끝"""
    if not L: return .1
    if i >= len(L): return L[-1][0] + L[-1][1]
    return L[i][0] + L[i][1] * frac

def y_fade(img, u, t0, s, font, fill, center, dur=.35, rise=18):
    p = prog(u, t0, t0 + dur)
    pop(img, s, font, fill, center, alpha=p, dy=int((1 - p) * rise))
    return p

def y_title(img, u, s, t0=.05):
    if not s: return
    y_fade(img, u, t0, s, fit_font(s, "Heavy", 70, 940), IVORY, (W / 2, YT_TITLE_Y))
    w = prog(u, t0 + .2, t0 + .6) * 120
    ImageDraw.Draw(img).line([(W / 2 - w / 2, YT_TITLE_Y + 58), (W / 2 + w / 2, YT_TITLE_Y + 58)], fill=GOLD, width=5)

def y_hook(img, u, sc, L, T):
    num = sc["num"]; col_end = TONE.get(sc.get("tone", "loss"), LOSS)
    rows = (sc.get("top") or "").split("\n")[:2] if sc.get("top") else []
    for k, row in enumerate(rows):
        y_row(img, u, .05 + k * .1, row, 80, IVORY, (W / 2, 650 + k * 96 - (len(rows) - 1) * 96))
    p = prog(u, .3, 1.0, ease_io)
    v = lerp(num.get("from", 0), num["to"], p)
    s = fmt_num(round(v, num.get("dec", 0)), num)
    big = fit_font(fmt_num(num["to"], num), "Heavy", num.get("size", 230), 960)
    pop(img, s, big, mix(IVORY, col_end, p), (W / 2, 830), alpha=prog(u, .25, .45))
    if sc.get("label"):
        li = sc.get("label_line", 1)
        t1 = max(1.1, y_at(L, li) if len(L) > li else 1.1)
        y_fade(img, u, t1, sc["label"], fit_font(sc["label"], "ExtraBold", 60, 940), GOLD, (W / 2, 1040))
        w = prog(u, t1 + .2, t1 + .6) * 420
        ImageDraw.Draw(img).line([(W / 2 - w / 2, 1098), (W / 2 + w / 2, 1098)], fill=GOLD, width=4)
    return img

def y_bars(img, u, sc, L, T):
    """세로 막대(연도별 이익 등) + 선택: 점선 평균선. avg{value, label, line(그어지는 음성 줄 번호)}"""
    y_title(img, u, sc.get("title"))
    items = sc["items"]; n_ = len(items); avg = sc.get("avg")
    vals = [it["v"] for it in items] + ([avg["value"]] if avg else [])
    lo, hi = min(0, min(vals)), max(0, max(vals))
    X0, X1, TOP, BOT = 150, 930, 750 if avg else 710, 1100
    span = (hi - lo) or 1; hi_ = hi + span * .16; lo_ = lo - (span * .14 if lo < 0 else 0)
    ymap = lambda v: BOT - (v - lo_) / (hi_ - lo_) * (BOT - TOP)
    y0 = ymap(0); d = ImageDraw.Draw(img)
    cw = (X1 - X0) / n_; bw = min(150, cw * .58)
    d.line([(X0 - 20, y0), (X1 + 20, y0)], fill=GRID, width=3)
    t_end = y_at(L, 1) - .2 if (len(L) > 1 and sc.get("split", True)) else y_at(L, 0, .85)
    t_end = max(t_end, .9); step = (t_end - .35) / max(1, n_)
    lf = F("SemiBold", 38 if n_ > 3 else 42); vf = F("Heavy", 48 if n_ > 3 else 60)
    for k, it in enumerate(items):
        t0 = it.get("at") if it.get("at") is not None else .3 + k * step
        if isinstance(t0, list): t0 = y_at(L, *t0)
        p = prog(u, t0, t0 + .55, ease_io)
        cx = X0 + cw * (k + .5); col = TONE.get(it.get("tone", "gold"), GOLD)
        for j, ln in enumerate(it["label"].split("\n")):
            c_ = mix(NAVY, IVORY if j == 0 else GRAY, prog(u, .1, .45))   # 축 이름은 처음부터: 빈 화면이 없게
            d.text((cx, max(y0, BOT) + 46 + j * 44), ln, font=lf if j == 0 else F("Medium", 32), fill=c_, anchor="mm")
        if p <= 0: continue
        yv = lerp(y0, ymap(it["v"]), p)
        top, bot = (yv, y0) if it["v"] >= 0 else (y0, yv)
        if bot - top > 2: d.rounded_rectangle([cx - bw / 2, top, cx + bw / 2, bot], 12, fill=mix(NAVY, col, min(1, p * 1.6)))
        txt = it.get("text", f"{it['v']:g}")
        vy = (top - 38) if it["v"] >= 0 else (bot + 38)
        pop(img, txt, fit_font(txt, "Heavy", vf.size, cw - 6), col, (cx, vy), alpha=prog(u, t0 + .3, t0 + .6))
    if avg:
        ta = y_at(L, avg.get("line", len(L) - 1), avg.get("frac", 0.0))
        q = prog(u, ta, ta + .9, ease_io)
        if q > 0:
            ya = ymap(avg["value"]); xe = lerp(X0 - 20, X1 + 20, q)
            x = X0 - 20
            while x < xe:
                d.line([(x, ya), (min(xe, x + 22), ya)], fill=GOLD, width=6); x += 36
            lab = avg.get("label", f"평균 {avg['value']:g}")
            a_ = prog(u, ta + .3, ta + .7)   # 범례: 제목 아래 '- - 여러 해 평균 17.3조' (막대 숫자와 겹치지 않게)
            if a_ > 0:
                f_ = F("ExtraBold", 44); tw = f_.getlength(lab); lx = W / 2 - (tw + 90) / 2; ly = 664
                for x in (lx, lx + 36): d.line([(x, ly), (x + 22, ly)], fill=mix(NAVY, GOLD, a_), width=6)
                d.text((lx + 90, ly), lab, font=f_, fill=mix(NAVY, GOLD, a_), anchor="lm")
    return img

def y_compare(img, u, sc, L, T):
    """좌우 카드: 왼쪽은 첫 줄, 오른쪽은 둘째 줄 음성이 시작될 때 나타난다"""
    y_title(img, u, sc.get("title"))
    sides = [sc["l"], sc["r"]]; d = ImageDraw.Draw(img)
    for i, sd in enumerate(sides):
        key = "l_line" if i == 0 else "r_line"
        if sc.get(key) is not None: t0 = y_at(L, sc[key], .05)
        else: t0 = .25 if i == 0 else max(.9, y_at(L, 1) if len(L) > 1 else y_at(L, 0, .55))
        p = prog(u, t0, t0 + .45, ease_io)
        if p <= 0: continue
        col = TONE.get(sd.get("tone", "gray" if i == 0 else "loss"), GRAY)
        cx = 290 + i * 500; off = int((1 - p) * 24) + 80
        d.rounded_rectangle([cx - 215, 590 + off, cx + 215, 1090 + off], 36, outline=mix(NAVY, col, p), width=4, fill=mix(NAVY, NAVY2, p))
        lines = sd.get("label", "").split("\n")
        for j, ln in enumerate(lines):
            d.text((cx, 680 + off + (j - (len(lines) - 1) / 2) * 50), ln, font=fit_font(ln, "Bold", 44, 390), fill=mix(NAVY, IVORY, p), anchor="mm")
        pop(img, sd["v"], fit_font(sd["v"], "Heavy", 150, 400), col, (cx, 880 + off), alpha=p)
        if sd.get("sub"): d.text((cx, 1060 + off), sd["sub"], font=fit_font(sd["sub"], "SemiBold", 36, 390), fill=mix(NAVY, GRAY, p), anchor="mm")
    return img

def y_statement(img, u, sc, L, T):
    V = L[0][1] if L else 2.0
    l1, l2 = sc["l1"], sc["l2"]
    y_fade(img, u, .05, l1, fit_font(l1, "ExtraBold", 72, 960), IVORY, (W / 2, 740))
    t2 = sc.get("t2") or min(.9, V * .35); tone = TONE.get(sc.get("tone", "gold"), GOLD)
    p = prog(u, t2, t2 + .45, ease_io)
    pop(img, l2, fit_font(l2, "Heavy", 112, 980), tone, (W / 2, 900), scale=.94 + .06 * p, alpha=p)
    wl = prog(u, t2 + .35, t2 + .8) * 420
    ImageDraw.Draw(img).line([(W / 2 - wl / 2, 990), (W / 2 + wl / 2, 990)], fill=tone, width=6)
    if sc.get("note"):
        for j, ln in enumerate(sc["note"].split("\n")):
            y_fade(img, u, t2 + .8 + j * .15, ln, fit_font(ln, "SemiBold", 44, 960), GRAY, (W / 2, 1090 + j * 62))
    return img

def y_box(img, u, t0, y, label, value, col, filled=False, h=200):
    p = prog(u, t0, t0 + .45, ease_io)
    if p <= 0: return
    d = ImageDraw.Draw(img); off = int((1 - p) * 20)
    fill = mix(NAVY, (52, 45, 32) if filled else NAVY2, p)
    d.rounded_rectangle([150, y - h / 2 + off, W - 150, y + h / 2 + off], 32, fill=fill, outline=mix(NAVY, col, p), width=4)
    d.text((W / 2, y - 50 + off), label, font=fit_font(label, "Bold", 40, 720), fill=mix(NAVY, GRAY if not filled else GOLD, p), anchor="mm")
    pop(img, value, fit_font(value, "Heavy", 96, 720), mix(NAVY, col, p), (W / 2, y + 30 + off), alpha=p)

def y_equation(img, u, sc, L, T):
    """식: [a] × 10 = [b]. a = 첫 줄, 곱하기 = 둘째 줄, b = 둘째 줄 후반(또는 셋째 줄) 음성에 맞춰 찬다"""
    y_title(img, u, sc.get("title"))
    a, b = sc["a"], sc["b"]
    ta = y_at(L, 0, .15); top = y_at(L, 1) if len(L) > 1 else y_at(L, 0, .5)
    tb = y_at(L, 2) if len(L) > 2 else top + .9
    y_box(img, u, ta, 740, a["label"], a["v"], IVORY)
    op = sc.get("op", "× 10")
    y_fade(img, u, top, op, F("Heavy", 84), GOLD, (W / 2, 896), rise=10)
    y_box(img, u, tb, 1050, b["label"], b["v"], GOLD, filled=True)
    if sc.get("note"):
        y_fade(img, u, tb + .6, sc["note"], fit_font(sc["note"], "SemiBold", 40, 900), GRAY, (W / 2, 1196))
    return img

_PH = {}
def y_photo(img, u, sc, L, T):
    """실제 사진 장면 (2026-10-25 운영자: 사업·제품이 나오면 실물 사진으로). 쇼츠 전용.
    photo: scripts/blog/media/lib 파일 이름(위키미디어 공용 등 재사용 허락된 것만), title: 위 제목(선택),
    chip{v,l,line}: 사진 아래 숫자 칩(선택, line번째 음성 줄에 뜬다), credit: 사진 출처 한 줄(작게)"""
    y_title(img, u, sc.get("title"))
    name = sc["photo"]
    if name not in _PH:
        p = os.path.join(HERE, "..", "blog", "media", "lib", name)
        _PH[name] = Image.open(p).convert("RGB")
    src = _PH[name]
    BW, BH, CY = 1000, 610, 962 if sc.get("title") else 900
    dur = (L[-1][0] + L[-1][1] + .6) if L else 4.0
    z = 1.0 + .08 * clamp(u / max(dur, 1))                                  # 천천히 다가가는 움직임 (멈춘 화면 방지)
    r = max(BW / src.width, BH / src.height) * z
    im = src.resize((int(src.width * r) + 1, int(src.height * r) + 1), Image.BILINEAR)
    fx = sc.get("focus_x", .5); fy = sc.get("focus_y", .5)
    x0 = int((im.width - BW) * fx); y0 = int((im.height - BH) * fy)
    im = im.crop((x0, y0, x0 + BW, y0 + BH))
    a = prog(u, 0, .35)
    mask = Image.new("L", (BW, BH), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, BW - 1, BH - 1], 34, fill=int(255 * a))
    oy = int((1 - a) * 24)
    img.paste(im, (int(W / 2 - BW / 2), int(CY - BH / 2) + oy), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([W / 2 - BW / 2, CY - BH / 2 + oy, W / 2 + BW / 2, CY + BH / 2 + oy], 34, outline=mix(NAVY, GOLD_D, a), width=3)
    ch = sc.get("chip")
    if ch:
        t0 = y_at(L, ch.get("line", 0), ch.get("frac", .3)); p = prog(u, t0, t0 + .4, ease_io)
        if p > 0:
            s = f'{ch["v"]}  {ch.get("l", "")}'.strip(); f = fit_font(s, "Heavy", 58, 900); w_ = f.getlength(s) + 70
            by = CY + BH / 2 - 70
            d.rounded_rectangle([W / 2 - w_ / 2, by - 44 + (1 - p) * 16, W / 2 + w_ / 2, by + 44 + (1 - p) * 16], 26, fill=mix(NAVY, (20, 24, 34), p), outline=mix(NAVY, GOLD, p), width=3)
            d.text((W / 2, by + (1 - p) * 16), s, font=f, fill=mix(NAVY, GOLD, p), anchor="mm")
    if sc.get("credit"):   # 출처: 사진 안 오른쪽 아래에 작게 (자막과 겹치지 않게)
        cf = F("Medium", 22); cx, cy = W / 2 + BW / 2 - 18, CY - BH / 2 + 30 + oy
        tw = d.textlength(sc["credit"], font=cf)
        bar = Image.new("RGBA", (int(tw + 24), 34), (0, 0, 0, int(140 * a))); img.paste(bar, (int(cx - tw - 12), int(cy - 17)), bar)
        d = ImageDraw.Draw(img); d.text((cx, cy), sc["credit"], font=cf, fill=mix(NAVY, (220, 226, 236), a), anchor="rm")
    return img

YDRAW = {"hook": y_hook, "bars": y_bars, "compare": y_compare, "statement": y_statement, "equation": y_equation, "photo": y_photo}

def y_wrap(d, font, cap, limit=800):
    """폭 800을 넘는 자막 줄은 글자를 줄이지 않고, 가운데에 가장 가까운 띄어쓰기에서 두 줄로 나눈다"""
    out = []
    for l in cap:
        if d.textlength(l, font=font) <= limit or " " not in l: out.append(l); continue
        sp = [i for i, ch in enumerate(l) if ch == " "]
        fits = [i for i in sp if max(d.textlength(l[:i], font=font), d.textlength(l[i + 1:], font=font)) <= limit] or sp
        i = min(fits, key=lambda i: abs(d.textlength(l[:i], font=font) - d.textlength(l[i + 1:], font=font)))
        out += y_wrap(d, font, [l[:i], l[i + 1:]], limit)
    return out

CAP_MAX_LINES = 2   # 2026-10-31 운영자: 자막이 3~4줄이 되면 아래가 안 보인다 → 쇼츠·릴스 자막은 최대 2줄, 넘치면 2줄 단위로 넘긴다

def cap_pages(lines, n=CAP_MAX_LINES):
    """줄 목록을 n줄씩 끊는다 (3줄 → 2·1, 4줄 → 2·2, 5줄 → 2·2·1)"""
    return [lines[i:i + n] for i in range(0, len(lines), n)] or [lines]

def cap_page_at(pages, u, a, v):
    """한 자막 줄을 읽는 동안(a ~ a+v) 글자 수 비율대로 장을 넘긴다. 읽기가 끝난 뒤에는 마지막 장을 유지"""
    if len(pages) == 1: return pages[0]
    w = [sum(len(l) for l in p) for p in pages]; tot = sum(w) or 1
    f = (u - a) / max(v, .1); acc = 0
    for p, x in zip(pages, w):
        acc += x / tot
        if f < acc: return p
    return pages[-1]

def y_caption(img, u, L):
    """쇼츠·릴스 자막: 장면 처음부터 끝까지 끊기지 않고 늘 떠 있다. 다음 문장이 시작되는 순간 바로 바뀐다(깜빡임 없음). 숫자는 금색.
    한 번에 보이는 자막은 최대 2줄 — 길면 2줄씩 나눠 말하는 속도에 맞춰 넘긴다 (2026-10-31)"""
    caps = [(a, v, cap) for (a, v, cap) in L if cap]
    if not caps: return
    a, v, cap = caps[0]
    for a_, v_, c in caps:
        if u >= a_ - .05: a, v, cap = a_, v_, c
    d = ImageDraw.Draw(img); font = F("Bold", 52)   # 2026-10-24 운영자: 자막 글자 크기는 처음부터 끝까지 똑같이 (줄이 길면 줄이지 말고 줄을 나눈다)
    cap = cap_page_at(cap_pages(y_wrap(d, font, cap)), u, a, v)
    maxw = max(d.textlength(l, font=font) for l in cap)
    lh = 72; y0 = YT_CAP_Y - (len(cap) - 1) * lh / 2
    bar = Image.new("RGBA", (int(maxw + 64), len(cap) * lh + 28), (6, 12, 26, 170))
    img.paste(bar, (int(YT_CAP_X - bar.width / 2), int(y0 - lh / 2 - 14)), bar)
    d = ImageDraw.Draw(img)
    for li, line in enumerate(cap):
        y = y0 + li * lh; x0 = YT_CAP_X - d.textlength(line, font=font) / 2
        d.text((x0, y), line, font=font, fill=IVORY, anchor="lm")
        for m in key_numbers(line):
            tx = x0 + d.textlength(line[:m.start()], font=font)
            d.text((tx, y), m.group().rstrip(), font=font, fill=GOLD, anchor="lm")

# 자막에서 금색으로 칠하는 숫자 (2026-10-27 운영자: "HBM4는 숫자로 보면 안 되지 — 규칙을 정립")
# 규칙: 양(量)을 나타내는 숫자만 칠한다 = 숫자 뒤에 단위(원·달러·%·%p·배·점·포인트·명·개·곳, 조·억·만·천 포함)가 붙은 것.
#  - 영문 이름 속 숫자는 칠하지 않는다: HBM4 · H100 · DDR5 · Q3
#  - 날짜·순서는 칠하지 않는다: 2024년 · 2월 · 29일 · 1분기 · 첫째
#  - "4만 9,900원", "37만 4천 원", "7,350억 달러" 처럼 단위가 이어지는 금액은 한 덩어리로 칠한다
KEYNUM = re.compile(r"(?<![A-Za-z0-9])[+\-−]?\d[\d,.]*(?:(?:\s?(?:조|억|만|천)(?:\s?\d[\d,.]*)?)+(?:\s?(?:원|달러|%p|%|배|점|포인트|명|개|곳))?|\s?(?:원|달러|%p|%|배|점|포인트|명|개|곳))(?![A-Za-z])")
def key_numbers(line):
    return list(KEYNUM.finditer(line))

def y_voice(txt, speak):
    """롱폼과 같은 목소리: 운영자 클론을 타입캐스트 1.1배로 받아 그대로 쓴다 (2026-10-25, 후처리 가속·톤 올림 없음).
    말이 늘어지거나(초당 5.5음절 미만) 뭉개지면(받아쓰기 일치 0.72 미만) 캐시를 버리고 다시 받는다. 속도는 바꾸지 않는다."""
    say = to_speech(txt); syl = len(re.sub(r"[^가-힣]", "", say)); best = None
    for k in range(3):
        raw = speak(say, 1.1, fresh=k > 0)
        a = np.asarray(raw, np.float32).copy(); rate = syl / max(.1, len(a) / SR)
        try:
            import verify; heard = verify.hear(a, SR); sc = verify.score(txt, heard)
        except Exception: heard, sc = "", 1.0
        need = .72 if re.search("버핏|그레이엄|PER|HBM|SK", txt) else .82   # 쇼츠는 더 엄격하게: 뭉개진 발음은 다시 받는다
        bad = (syl >= 10 and not (5.5 <= rate <= 8.3)) or sc < need
        cost = abs(rate - 6.7) / 6.7 + max(0, .85 - sc)
        if best is None or cost < best[0]: best = (cost, a, rate, sc, heard, k + 1, need)
        if not bad: break
        print(f"  음성 다시 받기({k + 1}/3): 속도 {rate:.1f}음절/초, 인식 {sc:.2f} · {txt[:30]}", flush=True)
    _, a, rate, sc, heard, tries, need = best
    VLOG.append({"text": txt, "score": round(sc, 3), "pass": need, "floor": .5, "tries": tries, "heard": heard, "rate": round(rate, 2)})
    return a

DRAW = {"hook": s_hook, "line": s_line, "run": s_run, "compare": s_compare, "bars": s_bars,
        "list": s_list, "race": s_race, "who": s_who, "statement": s_statement, "cta": s_cta, "screen": s_screen}
NO_CAPTION = {"statement", "cta", "list"}
DRAW["equation"] = y_equation

# ── 타임라인 ─────────────────────────────────────────────────
def plan(spec, speak):
    """각 장면의 음성을 만들고 시작·끝 시간을 정한다"""
    t = 0.0; scenes = []
    speed = spec.get("speed", 1.1)
    # 잉크 노트는 문장 사이·장면 끝에 숨 고를 틈을 둔다 (2026-10-27 운영자: "너무 빨리 넘어가 눈이 못 따라간다, 몇 초 늘어나도 부드럽게")
    GAP = spec.get("line_gap", .45 if spec.get("world") == "ink" else .12); TAIL = spec.get("scene_tail", .9 if spec.get("world") == "ink" else 0)
    for sc in spec["scenes"]:
        lines = sc.get("lines") or [{"cap": sc.get("cap"), "say": sc.get("say")}]
        if sc["type"] == "cta" and not lines[0].get("say") and not lines[0].get("cap"):
            lines = [{"cap": None, "say": CTA_SAY}]
        lines = cta_lines(spec, sc, lines)
        L = []; u = .1; vo = []
        for ln in lines:
            if ln.get("join"):   # 한 문장을 한 번에 읽고(끊김 없이) 자막만 문장 조각별로 넘긴다
                txt = " ".join(p["say"] for p in ln["join"])
                a = y_voice(txt, speak) if YT else speak(to_speech(txt), ln.get("speed", speed) * REEL_TEMPO)
                d_ = len(a) / SR
                for (f0, f1), p in zip(join_fracs(ln["join"]), ln["join"]): L.append([u + d_ * f0, d_ * (f1 - f0), p.get("cap")])
                vo.append((u, a)); u += d_ + GAP + ln.get("pause", 0); continue
            txt = ln.get("say") or " ".join(ln.get("cap") or [])
            if sc["type"] == "statement" and not txt: txt = f"{sc['l1']}, {sc['l2']}."
            if YT:
                a = y_voice(txt, speak)
            elif VERIFY:
                import verify
                if ln.get("cap") and verify.score(" ".join(ln["cap"]), txt) < .8:
                    LINT.append(f"자막과 음성이 다름: {ln['cap']} ↔ {txt}")
                a = verify.speak_checked(to_speech(txt), ln.get("speed", speed) * REEL_TEMPO, speak, SR, VLOG, orig=txt)
            else:
                a = speak(to_speech(txt), ln.get("speed", speed) * REEL_TEMPO)
            L.append([u, len(a) / SR, ln.get("cap")]); vo.append((u, a))
            u += len(a) / SR + GAP + ln.get("pause", 0)
        dur = u + {"hook": .1, "cta": .8}.get(sc["type"], .2) + (TAIL if sc is not spec["scenes"][-1] else 0)
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
        pages = cap_pages(list(cap))   # 2026-10-31: 한 번에 최대 2줄, 넘치면 2줄씩 넘긴다
        if len(pages) > 1:
            cap = cap_page_at(pages, u, a, v)
            w = [sum(len(l) for l in p) for p in pages]; k = pages.index(cap); tot = sum(w) or 1
            a = a + v * sum(w[:k]) / tot; v = v * w[k] / tot; e = a + v
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
            # 숫자(금액·%·배·점)는 드러나는 순간 금색으로 바뀌고 밑줄이 그어진다: 핵심 숫자에 눈이 가게
            for m in key_numbers(line):
                if k < m.end(): continue
                tx = x0 + d.textlength(line[:m.start()], font=font); tw = d.textlength(m.group().rstrip(), font=font)
                d.text((tx, y), m.group().rstrip(), font=font, fill=GOLD, anchor="lm")
                gw = tw * clamp((rev - m.end() + 1) / 4)
                d.rectangle([tx, y + 34, tx + gw, y + 38], fill=GOLD)
            rev -= len(line)
        return

def logo(d, y):
    """상단 로고 (2026-10-23 확정: scripts/brand.py) — y는 예전처럼 영문 글자의 가운데 높이"""
    paste_logo(d._image, W / 2, y - 17, 44, "dark", align="center")

def camera(img, u, s):
    """(STILL = False 일 때만) 장면 내내 천천히 다가가는 카메라 + 새 문장마다 살짝 튀는 박자. 2026-10-23부터 끔: 글자가 흔들려 읽기 어렵다"""
    if YT or STILL: return img
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

# ── 실제 영상 배경(B-roll): 첫 장면(후킹) 뒤에 주제에 맞는 무료 영상을 어둡게 깐다 ──
# 소스: assets/broll/<주제>_<번호>.mp4 (Mixkit 무료 라이선스, assets/fetch.py 로 받음)
BROLL_DIR = os.path.join(HERE, "assets", "broll")
BROLL_RULES = [  # (주제, 대본 제목·해시태그·캡션 앞부분에서 찾는 말) — 위에서부터 먼저 맞는 것
    ("traffic", r"보험|자동차|사고"), ("crypto", r"비트코인|코인|암호화폐"),
    ("chip", r"반도체|하이닉스|HBM|KLA|엔비디아|TSMC|칩"), ("datacenter", r"AI|데이터센터|인공지능"),
    ("storm", r"폭락|위기|공포|침체|버블|파산|무너|급락|역전"), ("gold", r"(^|[^가-힣])금(값|$|[^가-힣리융요액])"),
    ("city", r"금리|국채|환율|연준|FOMC|물가|CPI|경제 레이더|기준금리"), ("news", r"뉴스|브리핑|칼럼"),
    ("phone", r"알림|앱|화면|계좌|설정|등급|사용법"), ("time", r"복리|장기|10년|오래|기다"),
    ("money", r"1억|1,000만|돈|배당|수익"), ("market", r".")]
_BR = {"key": None, "frames": None}

def broll_key(spec):
    k = spec.get("broll")
    if k == "none": return None
    if not os.path.isdir(BROLL_DIR): return None
    have = sorted(f[:-4] for f in os.listdir(BROLL_DIR) if f.endswith(".mp4"))
    if k: cands = [h for h in have if h.split("_")[0] == k] or ([k] if k in have else [])
    else:
        txt = " ".join([spec.get("title", ""), " ".join(spec.get("hashtags", [])), spec.get("caption", "")[:160]])
        cands = []
        for key, pat in BROLL_RULES:
            if re.search(pat, txt): cands = [h for h in have if h.split("_")[0] == key]
            if cands: break
    if not cands: return None
    return cands[sum(map(ord, spec.get("id", ""))) % len(cands)]  # 같은 주제 안에서 릴스마다 다른 클립

def broll_load(name, secs):
    """클립을 540x960으로 풀어 메모리에 (배경이라 어둡게 깔리므로 이 정도면 충분)"""
    path = os.path.join(BROLL_DIR, name + ".mp4")
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-t", f"{min(6, secs + .5):.2f}", "-vf", "scale=540:960,fps=30",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    n = len(raw) // (540 * 960 * 3)
    return np.frombuffer(raw[:n * 540 * 960 * 3], np.uint8).reshape(n, 960, 540, 3) if n else None

def broll_setup(spec, scenes):
    _BR["key"] = _BR["frames"] = None
    first = scenes[0]
    if first["sc"]["type"] != "hook": return
    k = broll_key(spec)
    if not k: return
    try: _BR["frames"] = broll_load(k, first["dur"]); _BR["key"] = k
    except Exception as e: print("  영상 배경 실패", k, e)

_NAVYF = None
def broll_bg(img, T, dur):
    """후킹 장면 배경: 실제 영상(어둡게·남색 톤) 위에 기존 배경을 겹친다. 끝 0.4초 동안 기존 배경으로 넘어간다"""
    global _NAVYF
    fr = _BR["frames"]
    if fr is None: return img
    i = min(len(fr) - 1, int(T * 30))
    v = Image.fromarray(fr[i]).resize((W, H), Image.BILINEAR)
    a = np.asarray(v, np.float32)
    gray = a.mean(2, keepdims=True); a = a * .55 + gray * .45  # 색을 빼서 브랜드 색(남색·금색)이 튀게
    if _NAVYF is None:
        yy = np.linspace(0, 1, H)[:, None, None]
        # 위·아래는 더 어둡게(글자 자리), 가운데는 영상이 보이게
        _NAVYF = (.24 + .34 * np.abs(yy - .5) * 2).astype(np.float32)
    k = (1 - prog(T, dur - .45, dur)) * .70  # 영상 비중
    base = np.asarray(img, np.float32)
    tint = a * (1 - _NAVYF) + np.array(NAVY, np.float32) * _NAVYF
    out = base * (1 - k) + tint * k
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

YT_BANNER = None   # 유튜브 쇼츠: 영상 내내 위에 고정되는 제목 띠 (2026-10-22 운영자: 조회수 높은 쇼츠의 검은 띠 + 두 줄 제목)


def draw_banner(img):
    if not YT_BANNER: return
    # 2026-10-23 운영자: 유튜브 앱에서 위쪽 뒤로가기·검색 아이콘과 겹치지 않게 조금 아래로, 글자는 더 크게
    d = ImageDraw.Draw(img); d.rectangle([0, 0, W, 448], fill=(8, 10, 16))   # 아래 여백을 넉넉히 (10-23 운영자)
    l1, l2 = (list(YT_BANNER) + ["", ""])[:2]
    if l1: d.text((W / 2, 196), l1, font=fit_font(l1, "Heavy", 94, 1000), fill=IVORY, anchor="mm")
    if l2: d.text((W / 2, 318), l2, font=fit_font(l2, "Heavy", 110, 1010), fill=GOLD, anchor="mm")


def auto_banner(title):
    """제목 → 위쪽 두 줄 (쉼표·물음표 앞에서 나누고, 없으면 가운데 띄어쓰기에서)"""
    t = re.sub(r"\s*#\S+", "", title).strip()
    if " · " in t: t = t.split(" · ", 1)[1]
    for sep in (", ", "? "):
        if sep in t:
            a, b = t.split(sep, 1); return [a + ("," if sep == ", " else "?"), b] if sep == "? " else [a, b]
    w = t.split(" "); k = max(1, len(w) // 2)
    return [" ".join(w[:k]), " ".join(w[k:])]


def draw_banner_soft(img):
    """팝업 노트용 제목: 검은 띠 대신 위쪽이 어두워지는 그림자 위에 글자만 (2026-10-26 운영자: 헤더가 영상 안에 녹아 있어야 답답하지 않다)"""
    if not YT_BANNER: return
    g = np.zeros((H, 1), np.float32); n = 560
    g[:n, 0] = np.clip(1 - np.arange(n) / n, 0, 1) ** 1.25 * 225
    m = Image.fromarray(np.repeat(g, W, 1).astype(np.uint8), "L")
    img.paste(Image.new("RGB", (W, H), (6, 12, 24)), (0, 0), m)
    d = ImageDraw.Draw(img)
    l1, l2 = (list(YT_BANNER) + ["", ""])[:2]
    for s_, y, size, col in ((l1, 196, 94, IVORY), (l2, 318, 110, GOLD)):
        if not s_: continue
        f = fit_font(s_, "Heavy", size, 1010 if size > 100 else 1000)
        d.text((W / 2 + 3, y + 5), s_, font=f, fill=(0, 0, 0), anchor="mm")
        d.text((W / 2, y), s_, font=f, fill=col, anchor="mm")


# ── 골드 라인 (2026-10-26 운영자 승인: "앞으로 올라가는 릴스 및 쇼츠도 이 방향으로 전부") ──
# 펜이 그은 금선 하나가 영상 처음부터 끝까지 끊기지 않는다. 장면이 바뀔 때는 컷 대신 카메라가 펜을 따라 옆으로 이동하고
# (앞 장면이 왼쪽으로 빠지고 다음 장면이 오른쪽에서 들어옴), 선은 다음 장면에서 이어서 그어진다.
# 선 자리: 쇼츠·클린 화면은 위 제목 띠 바로 아래, 인스타 릴스는 자막과 고지문 사이. 대본에 "goldline": false 면 끈다.
GL_ON = True
WORLD = None   # "popup" = 팝업 노트 (대본 "world": "popup")
GL_INK = (232, 188, 96); GL_PAN = .5          # 펜 색 · 장면 사이 카메라 이동 시간(초)
GL_REST = .84                                  # 장면 안에서 펜이 멈추는 자리 (화면 폭 비율)


def gl_y():
    return 486 if YT else 1562


def _gl_pen(img, x, y, a, k=.8):
    """금색 만년필: 펜촉이 (x, y)에 닿고 오른쪽 위로 기울어진다 (롱폼 render2 의 펜과 같은 모양, 세로 화면은 0.8배)"""
    if a <= .02: return
    d = ImageDraw.Draw(img, "RGBA"); ang = math.radians(-38); ux, uy = math.cos(ang), math.sin(ang); px, py = -uy, ux
    def P(t, w): return (x + (ux * t + px * w) * k, y + (uy * t + py * w) * k)
    d.polygon([P(4, -10), P(170, -10), P(170, 22), P(4, 22)], fill=(0, 0, 0, int(70 * a)))
    d.polygon([P(0, 0), P(34, -11), P(34, 11)], fill=(*GOLD_D, int(255 * a)))
    d.line([P(4, 0), P(30, 0)], fill=(*NAVY, int(200 * a)), width=2)
    d.polygon([P(34, -13), P(150, -13), P(150, 13), P(34, 13)], fill=(*GL_INK, int(255 * a)))
    d.polygon([P(34, -13), P(150, -13), P(150, -5), P(34, -5)], fill=(250, 226, 170, int(200 * a)))
    d.polygon([P(92, -14), P(102, -14), P(102, 14), P(92, 14)], fill=(*NAVY, int(255 * a)))
    d.polygon([P(150, -14), P(182, -14), P(186, 0), P(182, 14), P(150, 14)], fill=(*NAVY, int(255 * a)))


def gl_tip(u, dur, first):
    """장면 안 시각 u 에서 펜촉의 x (화면 좌표). 들어오며 긋기 → 멈춤 → 장면 끝에 오른쪽 밖으로"""
    t0 = .25 if first else 0.0
    x = W * GL_REST * ease((u - t0) / .95)
    x += (W + 60 - W * GL_REST) * ease_io((u - (dur - GL_PAN / 2)) / (GL_PAN / 2))
    return x, (u - t0) / .95


def gl_rail(img, u, s, first, last):
    """장면 위에 금선을 긋는다 (장면 좌표). 펜 위치(x, y, 투명도)를 돌려준다: 긋는 동안 보이고, 멈춘 뒤 잠깐 쉬었다 사라진다"""
    tip, p_in = gl_tip(u, s["dur"] + (0 if not last else 99), first)
    if tip <= 1: return None
    y0 = gl_y(); d = ImageDraw.Draw(img, "RGBA"); n = max(2, int(tip / 18))
    pts = [(tip * k / n, y0 + 3 * math.sin((tip * k / n) / 140 + s["start"])) for k in range(n + 1)]
    d.line(pts, fill=(*GL_INK, 240), width=7, joint="curve")
    qx, qy = pts[-1]; d.ellipse([qx - 3.5, qy - 3.5, qx + 3.5, qy + 3.5], fill=(*GL_INK, 240))
    moving_out = (not last) and u > s["dur"] - GL_PAN / 2
    a = 1.0 if (p_in < 1 or moving_out) else 1 - prog(u, (.25 if first else 0) + .95 + .25, (.25 if first else 0) + .95 + .6)
    return (qx, qy, a) if tip < W + 40 else None   # 펜은 frame 이 맨 위(제목 띠·자막 위)에 그린다


def scene_layer(T, s, scenes):
    """장면 그림(배경·영상 배경·그래픽·금선). 자막·로고·띠 같은 고정 요소는 frame 이 위에 얹는다"""
    sc = s["sc"]; u = T - s["start"]
    warm = 0.0
    if sc["type"] == "hook": warm = prog(u, .85, 1.15) * (1 - prog(u, 2.0, s["dur"]))
    img = background(T, warm)
    if s is scenes[0] and sc["type"] == "hook": img = broll_bg(img, u, s["dur"])
    img = (YDRAW if YT and sc["type"] in YDRAW else DRAW)[sc["type"]](img, u, sc, s["L"], T)
    img = camera(img, u, s)
    pen = gl_rail(img, u, s, s is scenes[0], s is scenes[-1]) if GL_ON == "rail" else None
    return img, pen


_GW = {"key": None, "line": None}


def frame(T, scenes, total, pen=True):
    s = next((x for x in scenes if x["start"] <= T < x["start"] + x["dur"]), scenes[-1])
    sc = s["sc"]; u = T - s["start"]
    img = None; pens = []
    if WORLD in ("popup", "ink"):   # 팝업 노트 (popworld.py) · 잉크 노트 (inkworld.py, 2026-10-26)
        if WORLD == "ink":
            import inkworld
            img = inkworld.render(sys.modules[__name__], T, scenes, total)
        else:
            import popworld
            img = popworld.render(sys.modules[__name__], T, scenes, total)
        global YT_CAP_Y
        _cy = YT_CAP_Y; YT_CAP_Y = 1590   # 노트가 화면을 채우므로 자막은 노트 아래쪽 (그림·버튼을 가리지 않게)
        if YT: y_caption(img, u, s["L"])
        else: caption(img, u, s["L"])
        YT_CAP_Y = _cy
        if YT_BANNER: draw_banner_soft(img)
        d = ImageDraw.Draw(img); d.rectangle([0, 0, W, 8], fill=(20, 36, 62)); d.rectangle([0, 0, int(W * T / total), 8], fill=GOLD)
        return img
    if GL_ON and YT:   # 골드 라인 v2: 노트 판 위를 펜이 짚고 카메라가 따라간다 (goldworld.py)
        import goldworld
        if _GW["key"] is not scenes: _GW["key"] = scenes; _GW["line"] = goldworld.Line(sys.modules[__name__], scenes, total)
        img, (ptip, pa, pz) = goldworld.render(sys.modules[__name__], T, scenes, total, _GW["line"])
        y_caption(img, u, s["L"])
        if YT_BANNER: draw_banner(img)
        d = ImageDraw.Draw(img); d.rectangle([0, 0, W, 8], fill=(20, 36, 62)); d.rectangle([0, 0, int(W * T / total), 8], fill=GOLD)
        if pen and pa > .02: _gl_pen(img, ptip[0], ptip[1], pa, .85 * max(.7, pz))
        return img
    if GL_ON == "rail":   # 장면 경계 ±0.25초: 카메라가 펜을 따라 옆으로 (앞 장면은 왼쪽으로 빠지고 다음 장면이 오른쪽에서)
        for j in range(1, len(scenes)):
            b = scenes[j]["start"]
            if b - GL_PAN / 2 <= T < b + GL_PAN / 2:
                q = ease_io((T - (b - GL_PAN / 2)) / GL_PAN); off = int(round(W * q))
                (a_, pa), (b_, pb) = scene_layer(min(T, b - 1 / FPS), scenes[j - 1], scenes), scene_layer(max(T, b), scenes[j], scenes)
                img = Image.new("RGB", (W, H)); img.paste(a_, (-off, 0)); img.paste(b_, (W - off, 0))
                if pa: pens.append((pa[0] - off, pa[1], pa[2]))
                if pb: pens.append((pb[0] + W - off, pb[1], pb[2]))
                break
    if img is None:
        img, p_ = scene_layer(T, s, scenes)
        if p_: pens.append(p_)
    if YT: y_caption(img, u, s["L"])   # 쇼츠: 모든 장면에 자막이 계속 나온다
    elif sc["type"] not in NO_CAPTION: caption(img, u, s["L"])
    d = ImageDraw.Draw(img)
    if YT_BANNER: draw_banner(img); d = ImageDraw.Draw(img)
    elif sc["type"] not in ("cta", "screen"): logo(d, 236)
    d.rectangle([0, 0, W, 8], fill=(20, 36, 62)); d.rectangle([0, 0, int(W * T / total), 8], fill=GOLD)
    for (px_, py_, pa_) in (pens if pen else []):   # 썸네일에는 펜을 그리지 않는다
        if -40 < px_ < W + 40: _gl_pen(img, px_, py_, pa_)
    d = ImageDraw.Draw(img)
    if YT: return img   # 쇼츠: 고지문은 설명란에
    d.text((W / 2, 1650), DISC_VIDEO, font=F("Medium", 25), fill=(112, 124, 148), anchor="mm")
    if GL_ON != "rail":   # 예전의 금색 휩쓸기 전환 (인스타 기본 화면)
        for x in scenes[1:]:
            q = (T - (x["start"] - .12)) / .3
            if 0 <= q <= 1:
                px = lerp(-600, W + 600, ease_io(q)); ov = Image.new("L", (W, H), 0)
                ImageDraw.Draw(ov).polygon([(px - 260, 0), (px + 40, 0), (px - 560, H), (px - 860, H)], fill=235)
                img.paste(Image.new("RGB", (W, H), GOLD), (0, 0), ov)
    return img

# ── 썸네일(cover.jpg): 시리즈별로 다른 그림, 같은 틀 ────────────
COVER_STYLE = "box"  # "title" = 제목이 주인공인 새 썸네일 (2026-10-20 시범: 대본에 "cover_style": "title")
COVER_V = 2   # 썸네일 방식이 바뀌면 올린다 → build.py 가 아직 안 올라간 릴스의 썸네일만 다시 만든다
COVER_PREF = {"F": ["screen", "list", "bars", "compare"], "G": ["list", "bars", "compare"],
              "A": ["bars", "compare", "list"], "M": ["line", "bars"], "E": ["line", "bars"], "R": [], "D": ["race"]}
SERIES_TAG = {"F": "밸류노트 사용법", "G": "쉬운 가이드", "A": "오늘의 기업", "M": "이번 주 금리", "E": "시장 속보", "R": "투자 교육", "D": "은퇴 배당 비교"}
# 인스타 프로필 격자는 세로 4:5 로 가운데를 잘라 보여 준다(1080x1920 중 y 285~1635). 썸네일 요소는 모두 그 안에 둔다.

def series_tag(spec):
    if spec.get("tag"): return spec["tag"]
    if " · " in spec.get("title", ""): return spec["title"].split(" · ")[0]
    return SERIES_TAG.get(spec["id"][:1], "밸류노트")

def pick_cover(spec, scenes):
    c = spec.get("cover"); types = [s["sc"]["type"] for s in scenes]
    if isinstance(c, int) and 0 <= c < len(scenes): return scenes[c]
    if isinstance(c, str) and c in types: return scenes[types.index(c)]
    for ty in COVER_PREF.get(spec["id"][:1], []):
        if ty in types: return scenes[types.index(ty)]
    return scenes[0]

def settled_at(s):
    """장면 안의 요소가 모두 나타난 뒤, 전환 직전의 시각"""
    ty = s["sc"]["type"]
    if ty == "hook": return min(2.3, s["dur"] - .1)
    return max(.5, s["dur"] - .15)

def cover(spec, scenes):
    s = pick_cover(spec, scenes); sc = s["sc"]; u = settled_at(s); T = s["start"] + u
    img = background(T, 0.0)
    img = DRAW[sc["type"]](img, u, sc, s["L"], T)
    y0 = 1500
    if sc["type"] == "screen":   # 앱 화면은 제목이 격자에서 잘리지 않게 60px 내리고(점 무늬 주기와 같음), 훅 문장 대신 제목만 쓴다
        shifted = background(T, 0.0); shifted.paste(img.crop((0, 0, W, H - 60)), (0, 60)); img = shifted; y0 = 1470
    else:
        if sc["type"] != "race": logo(ImageDraw.Draw(img), 316)  # race는 맨 위에 '은퇴 N년 차' 제목이 있어 로고를 겹치지 않게 뺀다
        first = scenes[0]["sc"]; lines = first.get("lines") or [{"cap": first.get("cap")}]
        cap = lines[0].get("cap")
        if cap and sc["type"] not in NO_CAPTION: caption(img, .95, [[0, 1.0, cap]])  # 훅 문장을 다 드러난 상태로
    tag = series_tag(spec); font = F("SemiBold", 34); tw = font.getlength(tag)
    x0 = W / 2 - tw / 2 - 30
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y0, x0 + tw + 60, y0 + 66], 33, fill=(18, 36, 64), outline=GOLD_D, width=2)
    d.text((W / 2, y0 + 33), tag, font=font, fill=GOLD, anchor="mm")
    d.text((W / 2, 1650), DISC_VIDEO, font=F("Medium", 25), fill=(112, 124, 148), anchor="mm")
    return img

def plan_estimate(spec):
    """음성을 만들지 않고 글자 수로 길이를 어림한 타임라인 (썸네일만 다시 만들 때)"""
    t = 0.0; scenes = []; speed = spec.get("speed", 1.1)
    GAP = spec.get("line_gap", .45 if spec.get("world") == "ink" else .12); TAIL = spec.get("scene_tail", .9 if spec.get("world") == "ink" else 0)
    for sc in spec["scenes"]:
        lines = sc.get("lines") or [{"cap": sc.get("cap"), "say": sc.get("say")}]
        if sc["type"] == "cta" and not lines[0].get("say") and not lines[0].get("cap"): lines = [{"cap": None, "say": CTA_SAY}]
        lines = cta_lines(spec, sc, lines)
        L = []; u = .1
        for ln in lines:
            if ln.get("join"):
                v = max(.8, len(" ".join(p["say"] for p in ln["join"]).replace(" ", "")) * .17 / ln.get("speed", speed))
                for (f0, f1), p in zip(join_fracs(ln["join"]), ln["join"]): L.append([u + v * f0, v * (f1 - f0), p.get("cap")])
                u += v + GAP; continue
            txt = ln.get("say") or " ".join(ln.get("cap") or [])
            if sc["type"] == "statement" and not txt: txt = f"{sc['l1']}, {sc['l2']}."
            v = max(.8, len(txt.replace(" ", "")) * .15 / ln.get("speed", speed))
            L.append([u, v, ln.get("cap")]); u += v + GAP + ln.get("pause", 0)
        dur = u + {"hook": .1, "cta": .8}.get(sc["type"], .2) + (TAIL if sc is not spec["scenes"][-1] else 0)
        if sc["type"] == "hook": dur = max(dur, 2.6)
        if sc["type"] == "statement": dur = max(dur, 2.5)
        scenes.append({"sc": sc, "start": t, "dur": dur, "L": L, "vo": []}); t += dur
    return scenes, t

def cover_title(spec, scenes):
    """2026-10-20 운영자 요청: 제목이 주인공인 썸네일. 큰 제목(최대 3줄) → 답이 되는 숫자는 작게 → 시리즈 표시.
    배경은 그 릴스의 실사 영상 한 장면을 어둡게(격자에서 게시물마다 달라 보이게). 요소는 y 285~1635(4:5 격자) 안."""
    first = scenes[0]["sc"]
    title = spec.get("cover_title") or first.get("top") or spec.get("title", "")
    rows = [r for r in title.split("\n") if r][:3]
    img = background(1.0, 0.0)
    k = broll_key(spec)
    if k:
        try:
            fr = broll_load(k, 2.0)
            if fr is not None:
                v = Image.fromarray(fr[min(len(fr) - 1, 45)]).resize((W, H), Image.BILINEAR)
                a = np.asarray(v, np.float32); g = a.mean(2, keepdims=True); a = a * .5 + g * .5
                yy = np.linspace(0, 1, H)[:, None, None]
                dark = (.50 + .32 * np.clip((.62 - yy) / .30, 0, 1) ** 1.2 + .18 * np.clip((yy - .80) / .20, 0, 1)).astype(np.float32)  # 위(제목)는 짙게, 가운데는 사진이 보이게, 끊김 없이
                out = a * (1 - dark) + np.array(NAVY, np.float32) * dark
                img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        except Exception as e: print("  썸네일 배경 실패", k, e)
    d = ImageDraw.Draw(img)
    logo(d, 330)
    size = 132 if len(rows) <= 2 else 116
    font = F("Heavy", size)
    while size > 84 and max(font.getlength(r) for r in rows) > 980: size -= 6; font = F("Heavy", size)
    lh = int(size * 1.22); y0 = 470 + lh // 2 + (0 if len(rows) == 3 else lh // 3)
    for i, r in enumerate(rows):
        y = y0 + i * lh
        d.text((W / 2 + 4, y + 5), r, font=font, fill=(4, 10, 22), anchor="mm")  # 그림자: 사진 위에서도 읽히게
        d.text((W / 2, y), r, font=font, fill=IVORY, anchor="mm")
    yb = y0 + (len(rows) - 1) * lh + int(size * .75) + 40
    d.line([(W / 2 - 70, yb), (W / 2 + 70, yb)], fill=GOLD, width=6)
    num = first.get("num") if first.get("type") == "hook" else None
    if num and not spec.get("cover_hide_num"):
        s = fmt_num(num["to"], num)
        nf = fit_font(s, "Heavy", 150, 900)
        d.text((W / 2, yb + 140), s, font=nf, fill=TONE.get(first.get("tone", "gold"), GOLD), anchor="mm")
        lab = spec.get("cover_label") or first.get("label")
        if lab: d.text((W / 2, yb + 250), lab, font=fit_font(lab, "SemiBold", 40, 900), fill=(196, 204, 220), anchor="mm")
    tag = series_tag(spec); tf = F("SemiBold", 34); tw = tf.getlength(tag); x0 = W / 2 - tw / 2 - 30; ty = 1520
    d.rounded_rectangle([x0, ty, x0 + tw + 60, ty + 66], 33, fill=(18, 36, 64), outline=GOLD_D, width=2)
    d.text((W / 2, ty + 33), tag, font=tf, fill=GOLD, anchor="mm")
    d.text((W / 2, 1650), DISC_VIDEO, font=F("Medium", 25), fill=(150, 160, 180), anchor="mm")
    return img

def render_cover(spec, outdir):
    os.makedirs(outdir, exist_ok=True)
    global YT_BANNER, YT, GL_ON, WORLD
    # 2026-10-26 운영자: "앞으로 올릴 거 전부 그 방식(팝업 노트)으로" → 기본은 팝업 노트 + 깔끔한 화면(제목 두 줄).
    # 예전 화면이 꼭 필요하면 대본에 "world": "classic".
    WORLD = spec.get("world", "popup")
    if WORLD == "classic": WORLD = None
    YT = spec.get("platform") == "youtube" or spec.get("style") == "clean" or WORLD in ("popup", "ink")
    if WORLD in ("popup", "ink") and not spec.get("banner"): spec["banner"] = auto_banner(spec.get("title", ""))
    GL_ON = spec.get("goldline", True) is not False   # 골드 라인 기본 켬 (2026-10-26 운영자: 릴스·쇼츠는 샘플처럼 금선이 이어지는 연출 유지. 롱폼만 끔)   # 인스타도 "style": "clean" 이면 쇼츠와 같은 깔끔한 화면
    YT_BANNER = spec.get("banner") if YT else None
    scenes, _ = plan_estimate(spec)
    if YT_BANNER and spec.get("platform") == "youtube":   # 유튜브 쇼츠 표지: 제목 띠 + 첫 장면의 큰 숫자가 터진 순간
        broll_setup(spec, scenes); im = frame(min(1.6, scenes[0]["dur"] - .1), scenes, sum(x["dur"] for x in scenes), pen=False).convert("RGB")
    else:
        im = cover_title(spec, scenes) if spec.get("cover_style", COVER_STYLE) == "title" else cover(spec, scenes)
    im.save(os.path.join(outdir, "cover.jpg"), quality=90)
    open(os.path.join(outdir, "cover.v"), "w").write(str(COVER_V))

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
    # 실제 효과음(assets/sfx, Mixkit 무료) 이 있으면 그것을, 없으면 직접 합성한 소리를 쓴다
    SFX = {}
    for nm in ("whoosh", "alt_whoosh", "impact", "light", "item", "cta", "coins", "ui"):
        fp = os.path.join(HERE, "assets", "sfx", nm + ".wav")
        if os.path.exists(fp):
            import soundfile as _sf
            a_, sr_ = _sf.read(fp, dtype="float32")
            if sr_ == SR: SFX[nm] = a_ if a_.ndim == 1 else a_.mean(1)
    PEAK = {"whoosh": .70, "alt_whoosh": .42, "impact": .28}
    # 2026-10-21 운영자: 장면 전환 소리가 거슬린다 → 높은 쉭 소리를 걷어 내고(저역 통과) 앞뒤를 부드럽게, 크기도 낮춘다
    def soften(a, cut=1600):
        b_, a_ = signal.butter(2, cut / (SR / 2), "low"); y = signal.lfilter(b_, a_, a)
        env = np.sin(np.linspace(0, np.pi, len(y))) ** 1.5
        return (y * env).astype(np.float32)
    for nm in ("whoosh", "alt_whoosh"):
        if nm in SFX: SFX[nm] = soften(SFX[nm])
    if "impact" in SFX: SFX["impact"] = soften(SFX["impact"], 900)
    s = np.arange(int(SR * .7)) / SR
    impact = .7 * np.sin(2 * np.pi * (70 - 40 * s) * s) * np.exp(-s * 6) + .15 * rng.standard_normal(len(s)) * np.exp(-s * 30)
    def tick(f):
        s_ = np.arange(int(SR * .05)) / SR; return .15 * np.sin(2 * np.pi * f * s_) * np.exp(-s_ * 80)
    for j, x_ in enumerate(scenes[1:]):
        if "whoosh" in SFX:
            nm = "whoosh" if j % 2 == 0 or "alt_whoosh" not in SFX else "alt_whoosh"
            addfx(x_["start"] - PEAK[nm], .2 * SFX[nm])
        else:
            m = int(SR * .4); w = signal.lfilter(*signal.butter(2, 1800 / (SR / 2), "low"), rng.standard_normal(m))
            addfx(x_["start"] - .15, .35 * w * np.sin(np.linspace(0, np.pi, m)) ** 2)
    for x_ in scenes:
        st, ty, Lx, sc = x_["start"], x_["sc"]["type"], x_["L"], x_["sc"]
        if ty == "hook":
            if "impact" in SFX: addfx(st + .85 - PEAK["impact"], .4 * SFX["impact"])
            else: addfx(st + .85, impact)
            for k in range(9): addfx(st + .3 + k * .065, .5 * tick(900 + 70 * k))
            if "coins" in SFX and sc.get("num", {}).get("fmt") == "won": addfx(st + 1.05, .3 * SFX["coins"])
        elif ty == "run":
            days = sc.get("days", 20); end = Lx[1][0] - .1 if len(Lx) > 1 else Lx[0][1]
            for k in range(days): addfx(st + .15 + (end - .15) * k / days, tick(1300 if k % 2 == 0 else 1000))
            if len(Lx) > 1: addfx(st + Lx[1][0] + Lx[1][1] * .55, impact * .9)
        elif ty == "compare":
            addfx(st + .55 - (PEAK["impact"] if "impact" in SFX else 0), (.22 * SFX["impact"]) if "impact" in SFX else impact * .3)
        elif ty == "statement":
            at = st + min(.55, Lx[0][1] * .35)
            if "impact" in SFX: addfx(at - PEAK["impact"], .22 * SFX["impact"]); addfx(at, .25 * SFX.get("light", np.zeros(1)))
            else: addfx(at, impact * .7)
        elif ty in ("bars", "list"):
            n_ = len(sc["items"]); span = Lx[0][1] * .9 if ty == "list" else None
            for k in range(n_):
                at = st + (.15 + span * k / n_ if ty == "list" else .25 + k * min(.45, max(.2, Lx[0][1] * .7 / n_)))
                addfx(at, .25 * SFX["item"] if "item" in SFX else .6 * tick(1100))
        elif ty == "who":
            if "light" in SFX: addfx(st + .08, .45 * SFX["light"]); addfx(st + .45, .3 * SFX.get("item", np.zeros(1)))
        elif ty == "screen":
            if "ui" in SFX: addfx(st + .5, .35 * SFX["ui"])
        elif ty == "cta":
            if "cta" in SFX: addfx(st + .1, .32 * SFX["cta"])
            else:
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

REEL_TEMPO = 1.0  # 2026-10-25 운영자: 릴스도 롱폼·쇼츠와 같은 클론 1.1배 (이전 성호 1.15배 가속 대체)

# ── 실행 ─────────────────────────────────────────────────────
VERIFY = os.environ.get("REELS_VERIFY", "1") != "0"
VLOG, LINT = [], []
MAX_SEC = 60  # 2026-10-20 운영자: 정말 좋은 내용이면 50~60초도 괜찮다 (이전 40초)

def write_subs(spec, scenes, total, outdir):
    """유튜브 쇼츠 자막 파일 (2026-10-23 운영자): 한국어 subs_ko.srt, 영어 subs_en.srt(대본의 subs_en, 자막 순서대로).
    관리자 유튜브 검수 카드에서 내려받아 유튜브 스튜디오 → 자막 → 언어 추가에 올린다."""
    ents = [(x["start"] + a, cap) for x in scenes for (a, v, cap) in x["L"] if cap]
    def ts(t):
        t = max(0, t); return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round((t % 1) * 1000)) % 1000:03d}"
    langs = [("ko", [" ".join(c) for _, c in ents])]
    if len(spec.get("subs_en") or []) == len(ents): langs.append(("en", spec["subs_en"]))
    elif spec.get("subs_en"): print(f"  ⚠ 영어 자막 수({len(spec['subs_en'])})가 자막 수({len(ents)})와 달라 영어 자막을 만들지 않았습니다")
    for lang, texts in langs:
        out = [f"{k + 1}\n{ts(t0)} --> {ts(ents[k + 1][0] - .02 if k + 1 < len(ents) else total)}\n{texts[k]}\n" for k, (t0, _) in enumerate(ents)]
        open(os.path.join(outdir, f"subs_{lang}.srt"), "w", encoding="utf-8").write("\n".join(out))

def render(spec, outdir, stills=None):
    global YT_BANNER, YT, GL_ON, WORLD
    # 2026-10-26 운영자: "앞으로 올릴 거 전부 그 방식(팝업 노트)으로" → 기본은 팝업 노트 + 깔끔한 화면(제목 두 줄).
    # 예전 화면이 꼭 필요하면 대본에 "world": "classic".
    WORLD = spec.get("world", "popup")
    if WORLD == "classic": WORLD = None
    YT = spec.get("platform") == "youtube" or spec.get("style") == "clean" or WORLD in ("popup", "ink")
    if WORLD in ("popup", "ink") and not spec.get("banner"): spec["banner"] = auto_banner(spec.get("title", ""))
    GL_ON = spec.get("goldline", True) is not False   # 골드 라인 기본 켬 (2026-10-26 운영자: 릴스·쇼츠는 샘플처럼 금선이 이어지는 연출 유지. 롱폼만 끔)   # 인스타도 "style": "clean" 이면 쇼츠와 같은 깔끔한 화면
    YT_BANNER = spec.get("banner") if YT else None
    if spec.get("platform") == "youtube" and spec["scenes"][-1]["type"] != "cta":
        # 2026-10-24 운영자: 롱폼에서 나온 쇼츠는 전부 '풀버전 보기'로 끝나야 한다
        raise RuntimeError(f"{spec['id']}: 유튜브 쇼츠의 마지막 장면은 풀버전 안내(cta)여야 합니다")
    from tts import speak
    os.makedirs(outdir, exist_ok=True)
    VLOG.clear(); LINT.clear()
    scenes, total = plan(spec, speak)
    broll_setup(spec, scenes)
    if _BR["key"]: print("  영상 배경:", _BR["key"])
    if WORLD == "ink":   # 멈춘 구간 점검 (2026-10-26 운영자: 성우가 말하는 동안 화면이 쉬면 안 된다)
        import inkworld
        inkworld.prep(sys.modules[__name__], scenes); gaps = inkworld.audit(scenes, total)
        json.dump({"gaps": gaps, "max_gap": inkworld.GAP_MAX}, open(os.path.join(outdir, "ink_check.json"), "w"), ensure_ascii=False)
        for a_, b_ in gaps: print(f"  ✗ 화면이 {b_ - a_:.1f}초 멈춤: {a_}~{b_}초")
        if gaps and spec.get("ink_strict", True): raise RuntimeError(f"{spec['id']}: 화면이 {inkworld.GAP_MAX}초 넘게 멈추는 구간 {len(gaps)}곳 — 비트를 더 넣으세요")
    if total > MAX_SEC and not spec.get("allow_long"):
        raise RuntimeError(f"{spec['id']}: {total:.1f}초 — 최대 {MAX_SEC}초를 넘습니다. 이야기에 꼭 필요한 문장만 남기세요")
    if VERIFY:
        import verify
        for w in LINT: print("  ⚠", w)
        for v in VLOG:
            mark = "OK" if v["score"] >= v["pass"] else ("△" if v["score"] >= v["floor"] else "✗")
            print(f"  음성 {mark} {v['score']:.2f} (시도 {v['tries']}) {v['text']}")
            if v["score"] < v["pass"] or v.get("problems"): print(f"        들린 말: {v['heard']}  {' · '.join(v.get('problems') or [])}")
        bad = [v for v in VLOG if v["score"] < v["floor"]]
        json.dump({"lines": VLOG, "lint": LINT}, open(os.path.join(outdir, "voice_check.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        mark = os.path.join(outdir, "needs_listen.txt")
        if bad and os.environ.get("TYPECAST_API_KEY"):
            # 타입캐스트는 음절을 빼먹지 않는다: 남은 차이는 대개 받아쓰기 쪽 오차라 영상은 만들고, 사람이 들어 보고 승인하게 한다
            open(mark, "w", encoding="utf-8").write("\n".join(f"{v['text']} → 들린 말: {v['heard']}" for v in bad))
            print(f"  △ 받아쓰기 차이 {len(bad)}줄 → 관리자 승인 대기로 올립니다")
        else:
            if os.path.exists(mark): os.remove(mark)
            if bad: raise RuntimeError(f"{spec['id']}: 음성 검수 실패 {len(bad)}줄 — 대본을 고쳐야 합니다")
    if stills is not None:
        for ts in stills: frame(ts, scenes, total).save(os.path.join(outdir, f"still_{ts:.1f}.png"))
        return total
    # 유튜브 쇼츠: 썸네일을 먼저 만들고 영상 맨 끝 0.5초에 붙인다 (2026-10-26 운영자: 모바일 앱에선 썸네일 이미지를 못 올리고
    # 영상 속 장면만 고를 수 있으니, 업로드할 때 마지막 장면을 표지로 고르면 되게 준비해 둔다). 대본 "thumb_end": false 면 끈다.
    tail_img = None; tail = 0.0
    if spec.get("platform") == "youtube" and spec.get("thumb_end", True):
        cover_path = os.path.join(outdir, "cover.jpg")
        tj = os.path.join(HERE, "thumbs", f"{spec['id']}.json")   # 2026-10-28 운영자: 삼성전자 쇼츠 같은 심플 썸네일로 통일 (thumb_simple.py)
        if os.path.exists(tj):
            import thumb_simple; thumb_simple.render(json.load(open(tj, encoding="utf-8")), cover_path)
        elif spec.get("thumb_file") and os.path.exists(os.path.join(HERE, "..", "..", spec["thumb_file"])):
            Image.open(os.path.join(HERE, "..", "..", spec["thumb_file"])).convert("RGB").resize((W, H)).save(cover_path, quality=92)
        else:
            print(f"  ⚠ {spec['id']}: scripts/reels/thumbs/{spec['id']}.json 이 없어 첫 장면을 썸네일로 씁니다 — 심플 썸네일을 만들어야 업로드할 수 있습니다")
            frame(min(1.6, scenes[0]["dur"] - .1), scenes, total, pen=False).convert("RGB").save(cover_path, quality=90)
        tail_img = Image.open(cover_path).convert("RGB").resize((W, H)); tail = .5
    wav = os.path.join(outdir, "_mix.wav"); build_audio(scenes, total + tail, spec.get("mood", "tense"), wav)
    out = os.path.join(outdir, "reel.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium",
           "-crf", "22", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(total * FPS)):
        p.stdin.write(frame(i / FPS, scenes, total).tobytes())
    if tail_img is not None:
        for _ in range(int(tail * FPS)): p.stdin.write(tail_img.tobytes())
    p.stdin.close(); p.wait(); os.remove(wav)
    if tail_img is not None:   # 썸네일은 위에서 이미 만들었다
        open(os.path.join(outdir, "cover.v"), "w").write(str(COVER_V))
        write_subs(spec, scenes, total, outdir)
        return total + tail
    tj = os.path.join(HERE, "thumbs", f"{spec['id']}.json")
    if not os.path.exists(tj) and spec["id"][:1] == "R":   # 2026-10-29 운영자: 릴스는 같은 내용 쇼츠(Y…)와 같은 표지로 (인스타 격자에 맞춰 안쪽으로)
        tj = os.path.join(HERE, "thumbs", "Y" + spec["id"][1:] + ".json")
    if os.path.exists(tj):
        import thumb_simple; tspec = json.load(open(tj, encoding="utf-8"))
        if spec.get("platform") != "youtube": tspec["safe"] = "ig"
        thumb_simple.render(tspec, os.path.join(outdir, "cover.jpg"))
    else: (frame(min(1.6, scenes[0]["dur"] - .1), scenes, total, pen=False).convert("RGB") if (YT_BANNER and spec.get("platform") == "youtube") else cover_title(spec, scenes) if spec.get("cover_style", COVER_STYLE) == "title" else cover(spec, scenes)).save(os.path.join(outdir, "cover.jpg"), quality=90)
    open(os.path.join(outdir, "cover.v"), "w").write(str(COVER_V))
    if spec.get("platform") == "youtube": write_subs(spec, scenes, total, outdir)
    return total

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "out", spec["id"])
    if len(sys.argv) > 3 and sys.argv[3] == "stills":
        print(render(spec, out, [float(x) for x in sys.argv[4].split(",")]))
    elif len(sys.argv) > 3 and sys.argv[3] == "cover":   # 썸네일만 (음성 없이)
        render_cover(spec, out); print("썸네일 →", os.path.join(out, "cover.jpg"))
    else:
        print("길이", round(render(spec, out), 1), "초 →", out)
