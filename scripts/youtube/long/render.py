"""유튜브 롱폼 렌더러 (1920x1080, 24fps)
사용: python3 scripts/youtube/long/render.py <spec.json> [--fake-voice]
 - 숫자는 같은 폴더의 <id>.data.json (data.mjs 가 렌더 직전에 만든 최신값)으로 채운다
 - 음성: scripts/reels/tts.py (타입캐스트 성우 '성호'). --fake-voice 는 무음(로컬 미리보기용)
 - 결과: social/youtube/<id>/ video.mp4 · thumb.jpg · meta.json
화면 원칙: 정지 화면 없이 계속 조금씩 움직인다(느린 확대, 숫자 카운트, 차례로 나타나기). 효과음은 쓰지 않고 장면 전환은 부드러운 페이드.
"""
import json, math, os, re, subprocess, sys, urllib.request, datetime as dt
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "reels"))
from korean import to_speech  # noqa: E402

W, H, FPS, SR = 1920, 1080, 24, 44100
NAVY = (11, 27, 51); NAVY2 = (22, 44, 78); GOLD = (214, 172, 82); GOLD_L = (228, 199, 141)
IVORY = (246, 241, 232); GRAY = (150, 162, 182); DIM = (88, 104, 132); LOSS = (232, 104, 80); GAIN = (98, 196, 140)
_fc = {}


def F(w, s):
    if (w, s) not in _fc: _fc[(w, s)] = ImageFont.truetype(os.path.join(ROOT, "scripts", "reels", "fonts", f"SUIT-{w}.ttf"), s)
    return _fc[(w, s)]


class AD:
    """ImageDraw 대신 쓴다: RGB 화면 위에서도 글자 투명도(페이드)가 먹게 한다 (ImageDraw는 글자 알파를 무시함)"""
    def __init__(self, img): self.img = img; self.d = ImageDraw.Draw(img, "RGBA")
    def __getattr__(self, k): return getattr(self.d, k)
    def text(self, xy, s, font=None, fill=None, **kw):
        if fill is not None and len(fill) == 4:
            a = fill[3]
            if a <= 3: return
            if a < 250:
                l, t, r, b = [int(math.floor(v)) if i < 2 else int(math.ceil(v)) + 1 for i, v in enumerate(self.d.textbbox(xy, s, font=font, **kw))]
                if r <= l or b <= t: return
                m = Image.new("L", (r - l, b - t), 0); ImageDraw.Draw(m).text((xy[0] - l, xy[1] - t), s, font=font, fill=255, **kw)
                m = m.point(lambda v: v * a // 255)
                self.img.paste(Image.new("RGB", m.size, fill[:3]), (l, t), m); return
            fill = fill[:3]
        self.d.text(xy, s, font=font, fill=fill, **kw)


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): t = clamp(t); return 1 - (1 - t) ** 3
def prog(u, a, b): return ease((u - a) / max(1e-6, b - a))


def fill(s, V):
    def rep(m):
        if m[1] not in V: raise KeyError("원고 자리 값 없음: " + m[1])
        return V[m[1]]
    return re.sub(r"\{(\w+)\}", rep, s)


def wrap(d, text, font, maxw):
    out = []
    for para in str(text).split("\n"):
        cur = ""
        for w in para.split(" "):
            t = (cur + " " + w).strip()
            if d.textlength(t, font=font) <= maxw or not cur: cur = t
            else: out.append(cur); cur = w
        out.append(cur)
    return out


def bg_gradient():
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(0, 1, W)[None, :]
    r = np.sqrt((x - .5) ** 2 * 1.2 + (y - .32) ** 2)
    a = np.clip(1 - r * 1.4, 0, 1)[..., None]
    c = np.array(NAVY, float) * (1 - a) + np.array(NAVY2, float) * a
    return Image.fromarray(c.astype(np.uint8))


BG = None
LOGO = None
LOGO_S = None
GLOW = GLOW_RGB = None


def make_glow():
    g = Image.new("L", (1400, 900), 0); ImageDraw.Draw(g).ellipse([150, 100, 1250, 800], fill=40)
    g = g.resize((175, 112)).filter(ImageFilter.GaussianBlur(14)).resize((1400, 900), Image.BILINEAR)
    return g, Image.new("RGB", g.size, (214, 172, 82))


# ── 무료 영상(Mixkit) ────────────────────────────────────────
def broll_frames(cat, n):
    man = json.load(open(os.path.join(ROOT, "scripts", "reels", "assets", "manifest.json")))
    ids = man["video"].get(cat) or man["video"]["market"]
    cache = os.path.join(ROOT, "scripts", "youtube", "long", ".cache"); os.makedirs(cache, exist_ok=True)
    src = None
    for vid in ids:
        p = os.path.join(cache, f"{vid}.mp4")
        if not os.path.exists(p):
            for q in ("1080", "720"):
                try:
                    req = urllib.request.Request(f"https://assets.mixkit.co/videos/{vid}/{vid}-{q}.mp4", headers={"User-Agent": "Mozilla/5.0"})
                    open(p, "wb").write(urllib.request.urlopen(req, timeout=60).read()); break
                except Exception: pass
        if os.path.exists(p) and os.path.getsize(p) > 10000: src = p; break
    if not src:  # 네트워크가 막힌 곳(로컬 미리보기): 세로 클립을 쓴다
        cands = [f for f in os.listdir(os.path.join(ROOT, "scripts", "reels", "assets", "broll")) if f.startswith(cat)] or ["market_47012.mp4"]
        src = os.path.join(ROOT, "scripts", "reels", "assets", "broll", cands[0])
    # 천천히 확대(1.0→1.08)하면서, 짧은 클립은 왕복 재생
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf",
                          f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=rgb24", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    if len(fr) == 0: fr = np.zeros((1, H, W, 3), np.uint8)
    seq = np.concatenate([fr, fr[::-1]])
    return [seq[i % len(seq)] for i in range(n)]


# ── 공통 요소 ────────────────────────────────────────────────
def chrome(img, chapter, src, asof, u):
    d = AD(img)
    img.paste(LOGO_S, (56, 40), LOGO_S)
    if chapter:
        f = F("SemiBold", 26); tw = d.textlength(chapter, font=f)
        d.rounded_rectangle([W - 72 - tw - 36, 46, W - 72, 96], 25, outline=(*GOLD, ), width=2)
        d.text((W - 72 - tw - 18, 55), chapter, font=f, fill=GOLD_L)
    foot = " · ".join(x for x in [src, f"데이터 {asof} 기준" if asof else ""] if x)
    if foot: d.text((72, H - 52), foot, font=F("Medium", 22), fill=GRAY)
    d.text((W - 72 - d.textlength("*투자 권유가 아닌 교육용 정보입니다", font=F("Medium", 20)), H - 50), "*투자 권유가 아닌 교육용 정보입니다", font=F("Medium", 20), fill=DIM)


def subtitle(img, text, u_in):
    if not text: return
    d = AD(img); f = F("Bold", 44)
    lines = wrap(d, text, f, 1500)[:2]
    a = clamp(u_in / .18)
    y0 = H - 128 - (len(lines) - 1) * 58
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=f); x = (W - tw) / 2; y = y0 + i * 58
        pad = 16
        d.rounded_rectangle([x - pad, y - 6, x + tw + pad, y + 54], 12, fill=(6, 14, 28, int(190 * a)))
        d.text((x, y), l, font=f, fill=(*IVORY, int(255 * a)))


def count_text(target, p):
    """'4.4배', '1,294,000원', '73점' 같은 값을 앞 숫자만 0→목표로 세며 보여 준다"""
    m = re.search(r"-?[\d,]+(?:\.\d+)?", target)
    if not m or p >= 1: return target
    num = float(m[0].replace(",", "")); dec = len(m[0].split(".")[1]) if "." in m[0] else 0
    v = num * ease(p)
    s = f"{v:,.{dec}f}" if "," in m[0] else f"{v:.{dec}f}"
    return target[:m.start()] + s + target[m.end():]


# ── 장면 그리기 ──────────────────────────────────────────────
def draw_scene(sc, V, u, dur, lines_t, frame_bg):
    v = sc["v"]; typ = v["type"]
    img = Image.fromarray(frame_bg) if frame_bg is not None else BG.copy()
    if typ != "broll":  # 배경의 금빛 번짐이 아주 천천히 움직인다 (미리 흐리게 만든 조각을 붙인다)
        cx = int(W * .5 + 140 * math.sin(u * .15)) - GLOW.width // 2; cy = int(-GLOW.height * .35 + 30 * math.sin(u * .5))
        img.paste(GLOW_RGB, (cx, cy), GLOW)
    d = AD(img)
    T = lambda k: fill(v.get(k, ""), V)
    nth = lambda i: lines_t[min(i, len(lines_t) - 1)][0] if lines_t else 0  # i번째 문장이 시작하는 시각

    if typ == "broll":
        d.rectangle([0, 0, W, H], fill=(6, 14, 28, 150))
        y = 380
        if v.get("kicker"):
            a = prog(u, .2, .8); d.text((W / 2 - d.textlength(T("kicker"), font=F("SemiBold", 34)) / 2, y - 70 + 20 * (1 - a)), T("kicker"), font=F("SemiBold", 34), fill=(*GOLD_L, int(255 * a)))
        a = prog(u, .4, 1.1); f = F("Heavy", 96)
        for i, l in enumerate(wrap(d, T("title"), f, 1600)):
            d.text((W / 2 - d.textlength(l, font=f) / 2, y + i * 112 + 30 * (1 - a)), l, font=f, fill=(*IVORY, int(255 * a)))
        if v.get("sub"):
            a = prog(u, 1.0, 1.7); f = F("SemiBold", 40)
            for i, l in enumerate(wrap(d, T("sub"), f, 1400)):
                d.text((W / 2 - d.textlength(l, font=f) / 2, y + 160 + i * 54), l, font=f, fill=(*IVORY, int(220 * a)))
        lw = 160 * prog(u, .9, 1.6); d.rectangle([W / 2 - lw / 2, y + 140, W / 2 + lw / 2, y + 144], fill=GOLD)

    elif typ == "split":
        a = prog(u, .1, .7); f = F("Bold", 44)
        d.text((W / 2 - d.textlength(T("title"), font=f) / 2, 170 + 20 * (1 - a)), T("title"), font=f, fill=(*GOLD_L, int(255 * a)))
        for k, (side, x0) in enumerate((("left", 200), ("right", 1000))):
            t0 = .5 + k * max(.8, (nth(2) if k else 0) * .6)
            p = prog(u, t0, t0 + .7)
            d.rounded_rectangle([x0, 290 + 30 * (1 - p), x0 + 720, 690 + 30 * (1 - p)], 28, fill=(255, 255, 255, int(16 * p)), outline=(*(GOLD if k else GRAY), int(160 * p)), width=2)
            lab = fill(v[side]["label"], V); val = fill(v[side]["value"], V)
            for i, l in enumerate(lab.split("\n")):
                d.text((x0 + 360 - d.textlength(l, font=F("SemiBold", 34)) / 2, 340 + i * 46 + 30 * (1 - p)), l, font=F("SemiBold", 34), fill=(*IVORY, int(230 * p)))
            sv = count_text(val, prog(u, t0 + .2, t0 + 1.6)); fv = F("Heavy", 104)
            while d.textlength(sv, font=fv) > 660: fv = F("Heavy", fv.size - 6)
            d.text((x0 + 360 - d.textlength(sv, font=fv) / 2, 470 + 30 * (1 - p)), sv, font=fv, fill=(*(GOLD_L if k else IVORY), int(255 * p)))
        if v.get("foot"):
            p = prog(u, max(2.2, nth(2)), max(2.2, nth(2)) + .7); ft = T("foot"); f = F("Bold", 38)
            d.text((W / 2 - d.textlength(ft, font=f) / 2, 745 + 16 * (1 - p)), ft, font=f, fill=(*GOLD_L, int(255 * p)))
            uw = d.textlength(ft, font=f) * prog(u, max(2.2, nth(2)) + .4, max(2.2, nth(2)) + 1.2)
            d.rectangle([W / 2 - d.textlength(ft, font=f) / 2, 800, W / 2 - d.textlength(ft, font=f) / 2 + uw, 803], fill=GOLD)

    elif typ == "bars":
        a = prog(u, .1, .7); f = F("Bold", 46)
        d.text((150, 150 + 16 * (1 - a)), T("title"), font=f, fill=(*IVORY, int(255 * a)))
        d.text((150 + d.textlength(T("title"), font=f) + 20, 166), f"단위: {v.get('unit', '')}", font=F("Medium", 26), fill=GRAY)
        items = v["items"]; n = len(items); hl = v.get("highlight")
        vals = [float(x[1]) for x in items]; mx = max(max(vals), 0.01); mn = min(min(vals), 0)
        if v.get("horizontal"):
            for i, (lab, val) in enumerate(items):
                t0 = .6 + i * .35; p = prog(u, t0, t0 + 1.0); y = 280 + i * 140
                d.text((150, y + 22), lab, font=F("Bold", 40), fill=IVORY)
                bw = 1000 * (val / mx) * p; col = GOLD if (hl == i) else (90, 116, 156)
                d.rounded_rectangle([600, y + 10, 600 + max(bw, 4), y + 90], 14, fill=col)
                d.text((620 + bw, y + 26), count_text(f"{val:g}{v.get('unit', '')}", p), font=F("ExtraBold", 40), fill=GOLD_L if hl == i else IVORY)
        else:
            base = 760; span = 440; zero = base - span * (0 - mn) / (mx - mn) if mn < 0 else base
            colw = min(220, 1500 / n - 40); gap = (1620 - colw * n) / max(1, n - 1) if n > 1 else 0
            d.line([150, zero, 1770, zero], fill=DIM, width=2)
            for i, (lab, val) in enumerate(items):
                t0 = .6 + i * .45; p = prog(u, t0, t0 + 1.0); x = 150 + i * (colw + gap)
                h = span * (abs(val) / (mx - mn)) * p
                col = LOSS if val < 0 else (GOLD if (hl == i or i == n - 1) else (90, 116, 156))
                top, bot = (zero - h, zero) if val >= 0 else (zero, zero + h)
                d.rounded_rectangle([x, top, x + colw, max(bot, top + 2)], 10, fill=col)
                vt = count_text(f"{val:g}", p); fv = F("ExtraBold", 40)
                d.text((x + colw / 2 - d.textlength(vt, font=fv) / 2, (top - 56) if val >= 0 else (zero - 56)), vt, font=fv, fill=LOSS if val < 0 else IVORY)
                for j, l in enumerate(str(lab).split("\n")):
                    d.text((x + colw / 2 - d.textlength(l, font=F("SemiBold", 30)) / 2, base + 30 + j * 38), l, font=F("SemiBold", 30), fill=GRAY if i != n - 1 else GOLD_L)
        if v.get("foot"):
            p = prog(u, n * .45 + 1.2, n * .45 + 1.9); ft = T("foot")
            d.text((W - 150 - d.textlength(ft, font=F("Heavy", 48)), 190), ft, font=F("Heavy", 48), fill=(*LOSS, int(255 * p)))

    elif typ in ("list", "table"):
        a = prog(u, .1, .7); f = F("Bold", 50)
        d.text((150, 150 + 16 * (1 - a)), T("title"), font=f, fill=(*IVORY, int(255 * a)))
        d.rectangle([150, 222, 150 + 120 * prog(u, .4, 1.0), 226], fill=GOLD)
        if typ == "list":
            items = v["items"]; nl = len(lines_t); top = 280 + max(0, 5 - len(items)) * 59  # 항목이 적으면 화면 가운데로
            for i, it in enumerate(items):
                t0 = nth(min(nl - 1, round(i * (nl - 1) / max(1, len(items) - 1)))) if nl > 1 else .6 + i * .5
                t0 = max(.5 + i * .25, t0 - .2); p = prog(u, t0, t0 + .6); y = top + i * 118
                d.rounded_rectangle([150 + 40 * (1 - p), y, 1770, y + 96], 18, fill=(255, 255, 255, int(14 * p)))
                d.ellipse([186 + 40 * (1 - p), y + 30, 222 + 40 * (1 - p), y + 66], fill=(*GOLD, int(255 * p)))
                d.text((196 + 40 * (1 - p), y + 30), str(i + 1), font=F("Heavy", 28), fill=(*NAVY, int(255 * p)))
                d.text((250 + 40 * (1 - p), y + 24), fill(it, V), font=F("SemiBold", 40), fill=(*IVORY, int(255 * p)))
        else:
            cols = v["cols"]; rows = [[fill(c, V) for c in r] for r in v["rows"]]; hl = v.get("highlight")
            cw = [700, 480, 440]; x0 = 150; y = 270
            for j, c in enumerate(cols): d.text((x0 + sum(cw[:j]) + 20, y), c, font=F("Bold", 32), fill=GRAY)
            for i, r in enumerate(rows):
                t0 = .7 + i * .7; p = prog(u, t0, t0 + .6); yy = y + 70 + i * 120
                d.rounded_rectangle([x0, yy, x0 + sum(cw), yy + 100], 16, fill=(*(GOLD if hl == i else (255, 255, 255)), int((40 if hl == i else 12) * p)), outline=(*GOLD, int(200 * p)) if hl == i else None, width=2)
                for j, c in enumerate(r):
                    d.text((x0 + sum(cw[:j]) + 20, yy + 28), c, font=F("ExtraBold" if j else "SemiBold", 40), fill=(*(GOLD_L if hl == i else IVORY), int(255 * p)))

    elif typ == "phone":
        shot = SHOTS.get(v["img"])
        px0, py0, pw, ph = 230, 120, 420, 860
        d.rounded_rectangle([px0 - 14, py0 - 14, px0 + pw + 14, py0 + ph + 14], 56, fill=(14, 18, 26), outline=(70, 82, 104), width=3)
        if shot is not None:
            sc_w = pw; s = SHOTS_S.get(v["img"])
            if s is None: s = SHOTS_S[v["img"]] = shot.resize((sc_w, int(shot.height * sc_w / shot.width)), Image.LANCZOS)
            maxoff = max(0, s.height - ph); off = int(maxoff * clamp((u - 1.5) / max(1, dur - 3)) * .55)  # 천천히 아래로 훑는다
            crop = s.crop((0, off, sc_w, off + ph))
            mask = Image.new("L", (pw, ph), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw, ph], 44, fill=255)
            img.paste(crop, (px0, py0), mask); d = AD(img)
        a = prog(u, .2, .8)
        d.text((780, 200 + 16 * (1 - a)), T("title"), font=F("Heavy", 60), fill=(*IVORY, int(255 * a)))
        nl = len(lines_t)
        for i, b in enumerate(v.get("bullets", [])):
            t0 = nth(min(nl - 1, 4 + i)) - .2 if nl > 4 else 1 + i * .6; p = prog(u, t0, t0 + .6); y = 360 + i * 130
            bt = fill(b, V)
            d.rounded_rectangle([780 + 40 * (1 - p), y, 1700, y + 104], 20, fill=(255, 255, 255, int(16 * p)), outline=(*GOLD, int(120 * p)), width=2)
            d.text((820 + 40 * (1 - p), y + 26), bt, font=F("ExtraBold", 46), fill=(*GOLD_L, int(255 * p)))

    elif typ == "end":
        p = prog(u, .2, 1.0)
        ic = ICON_S; img.paste(ic.convert("RGB"), (W // 2 - 110, 210 + int(20 * (1 - p))), ic)
        f = F("Heavy", 72); t = T("title"); d.text((W / 2 - d.textlength(t, font=f) / 2, 480), t, font=f, fill=(*IVORY, int(255 * p)))
        f = F("SemiBold", 44); t = T("sub"); d.text((W / 2 - d.textlength(t, font=f) / 2, 580), t, font=f, fill=(*GOLD_L, int(255 * p)))
        q = prog(u, 1.2, 1.9); bw = 360; x = W / 2 - bw / 2
        sc_ = 1 + .04 * math.sin(u * 3) * q
        d.rounded_rectangle([x - 10 * sc_, 680, x + bw + 10 * sc_, 770], 45, fill=(204, 0, 0, int(255 * q)))
        d.text((W / 2 - d.textlength("구독하기", font=F("Heavy", 46)) / 2, 698), "구독하기", font=F("Heavy", 46), fill=(255, 255, 255, int(255 * q)))
    return img


SHOTS = {}
SHOTS_S = {}
ICON = ICON_S = None


def main():
    global BG, LOGO, ICON
    spec_path = sys.argv[1]; fake = "--fake-voice" in sys.argv
    spec = json.load(open(spec_path, encoding="utf-8"))
    data = json.load(open(spec_path.replace(".json", ".data.json"), encoding="utf-8"))
    V = data["vars"]
    out = os.path.join(ROOT, "social", "youtube", spec["id"]); os.makedirs(out, exist_ok=True)
    global LOGO_S, GLOW, GLOW_RGB
    BG = bg_gradient(); LOGO = Image.open(os.path.join(HERE, "assets", "logo.png")).convert("RGBA")
    LOGO_S = LOGO.resize((int(LOGO.width * .42), int(LOGO.height * .42)), Image.LANCZOS); GLOW, GLOW_RGB = make_glow()
    ICON = Image.open(os.path.join(HERE, "assets", "icon.png")).convert("RGBA")
    global ICON_S; ICON_S = ICON.resize((220, 220), Image.LANCZOS)
    for sc in spec["scenes"]:
        img = sc["v"].get("img")
        if img:
            p = os.path.join(out, "shot_" + img.replace(":", "_") + ".png")
            SHOTS[img] = Image.open(p).convert("RGB") if os.path.exists(p) else None

    # 1) 음성 (문장마다) → 장면 길이
    if not fake: from tts import speak
    timeline = []; t = 0.0; audio = []
    for sc in spec["scenes"]:
        lines = [fill(l, V) for l in sc["lines"]]; lt = []; u = .5
        for l in lines:
            a = np.zeros(int(len(l) / 8.0 * SR), np.float32) if fake else speak(to_speech(l), 1.1)
            lt.append((u, len(a) / SR, l)); audio.append((t + u, a)); u += len(a) / SR + .32
        dur = u + .5
        timeline.append({"sc": sc, "start": t, "dur": dur, "lines": lt}); t += dur
    total = t
    # 2) 음성 합치기
    mix = np.zeros(int((total + 1) * SR), np.float32)
    for st, a in audio:
        i = int(st * SR); mix[i:i + len(a)] += a[: len(mix) - i]
    if np.abs(mix).max() > 0: mix = mix / np.abs(mix).max() * .9
    wav = os.path.join(out, "voice.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", wav], input=mix.tobytes(), check=True)
    # 3) 영상
    tmp = os.path.join(out, "video_noaudio.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    prev_last = None
    for k, s in enumerate(timeline):
        sc = s["sc"]; n = int(round(s["dur"] * FPS))
        frames_bg = broll_frames(sc["v"].get("clip", "market"), n) if sc["v"]["type"] == "broll" else None
        chapter = next((x["sc"].get("chapter") for x in reversed(timeline[:k + 1]) if x["sc"].get("chapter")), "")
        src = fill(sc["v"].get("src", ""), V); asof = V.get("asof") if sc["v"]["type"] not in ("broll", "end") else ""
        for i in range(n):
            u = i / FPS
            img = draw_scene(sc, V, u, s["dur"], s["lines"], frames_bg[i] if frames_bg is not None else None)
            chrome(img, chapter if sc["v"]["type"] != "end" else "", src, asof, u)
            cur = next((l for l in reversed(s["lines"]) if u >= l[0] - .05), None)
            if cur and u <= cur[0] + cur[1] + .3: subtitle(img, cur[2], u - cur[0])
            fr = np.asarray(img)
            if prev_last is not None and i < 10:  # 장면 사이 부드러운 페이드 (0.4초)
                a = (i + 1) / 11; fr = (prev_last * (1 - a) + fr * a).astype(np.uint8)
            enc.stdin.write(fr.tobytes())
            if i == n - 1: prev_last = fr.astype(np.float32)
        print(f"  장면 {k + 1}/{len(timeline)} {s['dur']:.1f}초", flush=True)
    enc.stdin.close(); enc.wait()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    os.path.join(out, "video.mp4")], check=True)
    os.remove(tmp)
    # 4) 썸네일 (제목이 크게 보이게)
    th = BG.copy().convert("RGBA").resize((1280, 720)); d = ImageDraw.Draw(th); tv = spec["thumb"]
    d.text((80, 90), fill(tv["top"], V), font=F("ExtraBold", 54), fill=GOLD_L)
    y = 180
    for l in fill(tv["main"], V).split("\n"):
        f = F("Heavy", 112)
        while d.textlength(l, font=f) > 1120: f = F("Heavy", f.size - 4)
        d.text((80, y), l, font=f, fill=IVORY); y += f.size + 18
    d.rectangle([80, y + 10, 300, y + 18], fill=GOLD)
    d.text((80, y + 44), fill(tv["sub"], V), font=F("Bold", 46), fill=IVORY)
    lg = LOGO.resize((int(LOGO.width * .5), int(LOGO.height * .5))); th.alpha_composite(lg, (1280 - lg.width - 50, 720 - lg.height - 40))
    th.convert("RGB").save(os.path.join(out, "thumb.jpg"), quality=92)
    # 5) 제목·설명(챕터)·태그
    chapters = []
    for s in timeline:
        if s["sc"].get("chapter"):
            m, sec = divmod(int(s["start"]), 60); chapters.append(f"{m}:{sec:02d} {s['sc']['chapter']}")
    if not chapters or not chapters[0].startswith("0:00"): chapters.insert(0, "0:00 시작")
    desc = "\n".join([fill(spec["description_head"], V), "", f"※ 영상의 주가·적정 주가·점수는 {V['asof']} 기준입니다.", "", *chapters, "",
                      "참고 자료", *[fill(x, V) for x in spec.get("sources", [])], "",
                      "내 종목의 적정 주가와 점수 확인: https://valuenote.co.kr/yt", "",
                      "*본 영상은 투자 교육용 정보이며, 특정 종목의 매수·매도 권유가 아닙니다. 적정 주가는 워렌 버핏·그레이엄·찰리 멍거의 방식으로 계산한 결과이며, 이 방식이 늘 맞지는 않습니다."])
    meta = {"id": spec["id"], "kind": "long", "title": fill(spec["title"], V)[:100], "description": desc, "tags": spec.get("tags", []),
            "scheduled_at": spec["scheduled_at"], "duration": round(total, 1), "data": data["raw"], "data_asof": data["raw"]["asof_iso"],
            "events": spec.get("events", []), "rendered_at": dt.datetime.now(dt.timezone.utc).isoformat(), "company": spec.get("company")}
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), ensure_ascii=False, indent=1)
    print(f"완료: {total / 60:.1f}분 → {out}")


if __name__ == "__main__":
    main()
