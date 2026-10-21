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
def chrome(img, chapter, src, asof, u, frac=None):
    d = AD(img)
    if frac is not None: d.rectangle([0, 0, W, 5], fill=(20, 36, 62)); d.rectangle([0, 0, int(W * frac), 5], fill=GOLD)
    img.paste(LOGO_S, (56, 40), LOGO_S)
    if chapter:
        f = F("SemiBold", 26); tw = d.textlength(chapter, font=f)
        d.rounded_rectangle([W - 72 - tw - 36, 46, W - 72, 96], 25, outline=(*GOLD, ), width=2)
        d.text((W - 72 - tw - 18, 55), chapter, font=f, fill=GOLD_L)
    foot = " · ".join(x for x in [src, f"데이터 {asof} 기준" if asof else ""] if x)
    if foot: d.text((72, H - 52), foot, font=F("Medium", 22), fill=GRAY)
    d.text((W - 72 - d.textlength("*투자 권유가 아닌 교육용 정보입니다", font=F("Medium", 20)), H - 50), "*투자 권유가 아닌 교육용 정보입니다", font=F("Medium", 20), fill=DIM)


def subtitle(img, text, u_in, dur=None):
    """아래 자막. 두 줄을 넘는 긴 문장은 말하는 속도에 맞춰 두 줄씩 넘긴다 (잘리지 않게)"""
    if not text: return
    d = AD(img); f = F("Bold", 44)
    allL = wrap(d, text, f, 1500)
    pages = [allL[i:i + 2] for i in range(0, len(allL), 2)]
    if len(pages) > 1 and dur:
        tot = sum(len("".join(pg)) for pg in pages); acc = 0; pi = 0
        for pi, pg in enumerate(pages):
            acc += len("".join(pg))
            if u_in < dur * acc / tot: break
        lines = pages[pi]; start = dur * (acc - len("".join(pages[pi]))) / tot
        a = clamp((u_in - start) / .18) if pi else clamp(u_in / .18)
    else:
        lines = allL[:2]; a = clamp(u_in / .18)
    y0 = H - 128 - (len(lines) - 1) * 58
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=f); x = (W - tw) / 2; y = y0 + i * 58
        pad = 16
        d.rounded_rectangle([x - pad, y - 6, x + tw + pad, y + 54], 12, fill=(6, 14, 28, int(190 * a)))
        d.text((x, y), l, font=f, fill=(*IVORY, int(255 * a)))
        for m in re.finditer(r"[+\-−]?\d[\d,.]*(?:\s?억(?:\s?\d[\d,]*\s?천?만?)?|\s?만|\s?천)?\s?(?:원|%p|%|배|점|년|분기|곳|개)?", l):  # 숫자는 금색으로
            tx = x + d.textlength(l[:m.start()], font=f); d.text((tx, y), m.group().rstrip(), font=f, fill=(*GOLD_L, int(255 * a)))


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
            def scr(key, f):  # 앱 화면 key 를 f(0~1) 위치까지 스크롤한 휴대폰 화면
                sh_ = SHOTS.get(key) or shot; s_ = SHOTS_S.get(key)
                if s_ is None: s_ = SHOTS_S[key] = sh_.resize((pw, int(sh_.height * pw / sh_.width)), Image.LANCZOS)
                off = int(max(0, s_.height - ph) * clamp(f)); c = s_.crop((0, off, pw, off + ph))
                if c.height < ph: c2 = Image.new("RGB", (pw, ph), (246, 244, 239)); c2.paste(c, (0, 0)); c = c2
                return c
            if PHONE:  # 비트마다 다른 화면/위치. 비트 안에서는 계속 스크롤, 화면이 바뀔 때는 위로 밀려 올라온다
                (k0, a0, b0), (k1, a1, b1), q, tr = PHONE
                cur_ = scr(k1, a1 + (b1 - a1) * q)
                if tr < 1:
                    prev_ = scr(k0, b0); e = ease(tr); dy = int(ph * e)
                    crop = Image.new("RGB", (pw, ph)); crop.paste(prev_, (0, -dy)); crop.paste(cur_, (0, ph - dy))
                else: crop = cur_
            else: crop = scr(v["img"], clamp((u - 1.5) / max(1, dur - 3)) * .55)
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


# ── 화면이 2.5초 넘게 같은 모습으로 머물지 않게: 문장마다 '비트'를 바꾼다 (2026-10-21 운영자 요청) ──
# cam = 그래픽을 다른 구도로 클로즈업(천천히 밀고 들어감) / cut = 실사 영상 위에 지금 문장을 큰 글자로 / 그 사이 0.45초 부드러운 카메라 이동
FRAMES = {"wide": (1.0, .5, .5), "pc": (1.07, .5, .5), "pt": (1.07, .5, .47), "pb": (1.07, .5, .53)}
MAX_BEAT = 2.4
_TOK = r"\d[\d,.]*\s*(?:조|억|만|천)*"
NUM_RE = re.compile(r"(?:약\s*)?" + _TOK + r"(?:\s+" + _TOK + r")*\s*(?:원|%|배|점)?")


def key_number(txt):
    """문장에서 가장 눈에 띄는 숫자 (금액·%·배 우선, 그다음 점수). '100점 만점'·연도는 빼고, 없으면 None"""
    c = []
    for m in NUM_RE.finditer(txt):
        v = m.group(0).strip()
        if txt[m.end():m.end() + 3].strip().startswith("만점") or not re.search(r"[조억만천원%배점]$", v): continue
        c.append((2 if re.search(r"[원%배]$", v) else 1, len(v), -m.start(), v))
    return max(c)[3] if c else None


def plan_beats(typ, dur, lines, ncut=99):
    """문장마다 화면이 바뀌게: 그래픽(구도 교대) → 숫자 카드 / 실사 컷. 한 비트는 최대 2.4초"""
    if typ == "end" or not lines: return [(0, dur, "cam", "wide")]
    if typ == "phone":  # 앱 화면: 실사 컷 없이 앱의 여러 화면을 번갈아, 각 화면은 스크롤하며
        beats = []; edges = [0] + [l[0] for l in lines[1:]] + [dur]; t = 0.0; k = 0
        while t < dur - .05:
            t1 = min(dur, t + 2.0); nxt = [e for e in edges if t + 1.0 < e <= t1]
            if nxt: t1 = nxt[-1]
            if dur - t1 < .5: t1 = dur
            beats.append((t, t1, "phone", k)); k += 1; t = t1
        return beats
    if typ == "broll":  # 챕터 제목 카드: 제목은 3초만, 그 뒤로는 실사 컷과 숫자 카드가 문장마다 바뀐다
        T = min(3.2, dur); beats = [(0, T, "cam", "wide")]; c = 0
        for idx, (a, d_, txt) in enumerate(lines):
            end = lines[idx + 1][0] if idx + 1 < len(lines) else dur; a = max(a, T)
            if end - a < .3: continue
            n = max(1, math.ceil((end - a) / MAX_BEAT)); L = (end - a) / n; num = key_number(txt)
            for j in range(n):
                t0, t1 = a + j * L, a + (j + 1) * L
                if num and (j == 1 or (ncut <= 0 and j == 0)): beats.append((t0, t1, "stat", txt, num))
                elif ncut > 0: beats.append((t0, t1, "cut", txt)); ncut -= 1
                else: beats.append((t0, t1, "cam", "pc" if c % 2 else "wide"))
                c += 1
        return beats
    beats = [(0, lines[0][0], "cam", "wide")]; k = 0; spent = {"cut": 0, "stat": 0}; alt = ["pc", "wide", "pt", "wide", "pb", "wide"]
    for idx, (a, d_, txt) in enumerate(lines):
        end = lines[idx + 1][0] if idx + 1 < len(lines) else dur
        n = max(1, math.ceil((end - a) / MAX_BEAT)); L = (end - a) / n; num = key_number(txt); stat_done = False
        for j in range(n):
            t0, t1 = a + j * L, a + (j + 1) * L; kind = None
            if j >= 1:  # 문장의 첫 비트는 항상 그래픽 (차례로 나타나는 항목이 보이게)
                if num and not stat_done and spent["stat"] + L <= dur * .25 and (j % 2 == 1 or ncut <= 0): kind = ("stat", txt, num); stat_done = True
                elif ncut > 0 and spent["cut"] + L <= dur * .4: kind = ("cut", txt); ncut -= 1
            if kind: beats.append((t0, t1) + kind); spent[kind[0]] += L
            else: beats.append((t0, t1, "cam", alt[k % len(alt)])); k += 1
    return beats


def stat_card(text, num, u, L):
    """숫자 카드: 큰 금색 숫자가 올라가며 나타나고, 아래에 지금 문장"""
    img = BG.copy(); d = AD(img)
    for gx in range(0, W, 96): d.line([gx, 0, gx, H], fill=(255, 255, 255, 10))
    for gy in range(0, H, 96): d.line([0, gy, W, gy], fill=(255, 255, 255, 10))
    a = ease(u / .5); f = F("Heavy", 200)
    while d.textlength(num, font=f) > 1640 and f.size > 90: f = F("Heavy", f.size - 10)
    sv = count_text(num, clamp(u / .9)) if re.search(r"\d", num) else num
    tw = d.textlength(num, font=f); x = W / 2 - tw / 2; y = H / 2 - 170 + 40 * (1 - a)
    d.text((x, y), sv, font=f, fill=(*GOLD_L, int(255 * a)))
    d.rectangle([W / 2 - 160 * a, y + f.size + 62, W / 2 + 160 * a, y + f.size + 68], fill=(*GOLD, int(255 * a)))
    return img


def cam(img, f0, f1, p, drift):
    """f0 → f1 구도로 p(0~1) 만큼 이동한 화면. drift: 비트 안에서 천천히 더 다가간다"""
    z0, x0, y0 = FRAMES[f0]; z1, x1, y1 = FRAMES[f1]; e = ease(p)
    z = (z0 + (z1 - z0) * e) * (1 + .02 * drift); cx = x0 + (x1 - x0) * e; cy = y0 + (y1 - y0) * e
    if z < 1.003: return img
    w, h = W / z, H / z; l = min(max(cx * W - w / 2, 0), W - w); t = min(max(cy * H - h / 2, 0), H - h)
    return img.resize((W, H), Image.BILINEAR, box=(l, t, l + w, t + h))


CUTS = []          # (경로, 길이초)
PHONE = None       # 앱 화면 장면의 현재 상태 ((이전 화면), (지금 화면), 스크롤 진행, 전환 진행)


def phone_views(img):
    """같은 화면이 반복되지 않게: 회사 상세를 위→아래로 나눠 보여 주고, 사이사이 다른 탭 화면"""
    seq = [(img, 0, .18), (img + ":list", 0, .5), (img, .2, .42), (img + ":value", 0, .5), (img, .44, .66),
           (img + ":brief", 0, .5), (img, .68, .9), (img + ":port", 0, .5), (img, .9, 1.0)]
    seq = [x for x in seq if x[0] in SHOTS and SHOTS[x[0]] is not None]
    return seq or [(img, 0, 1)]
_cut_i = [0]


def load_cuts(queries):
    cache = os.path.join(ROOT, "scripts", "youtube", "long", ".cache"); os.makedirs(cache, exist_ok=True)
    key = os.environ.get("PEXELS_API_KEY", ""); got = []
    if key:
        import urllib.parse
        for q in queries:
            try:
                req = urllib.request.Request(f"https://api.pexels.com/videos/search?query={urllib.parse.quote(q)}&per_page=3&orientation=landscape&size=medium",
                                             headers={"Authorization": key, "User-Agent": "Mozilla/5.0"})
                for v in json.loads(urllib.request.urlopen(req, timeout=30).read()).get("videos", [])[:2]:
                    fs_ = sorted([f for f in v["video_files"] if f.get("file_type") == "video/mp4" and 1280 <= (f.get("width") or 0) <= 1920], key=lambda f: -f["width"])
                    if not fs_: continue
                    pth = os.path.join(cache, f"pex_{v['id']}.mp4")
                    if not os.path.exists(pth) or os.path.getsize(pth) < 10000:
                        open(pth, "wb").write(urllib.request.urlopen(urllib.request.Request(fs_[0]["link"], headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read())
                    got.append(pth)
            except Exception as e: print("  Pexels 실패:", q, str(e)[:80])
    if len(got) < 4:  # 예비: Mixkit (릴스와 같은 무료 소스)
        man = json.load(open(os.path.join(ROOT, "scripts", "reels", "assets", "manifest.json")))
        for cat in ("chip", "datacenter", "market", "money", "city", "time", "news"):
            for vid in man["video"].get(cat, [])[:2]:
                pth = os.path.join(cache, f"{vid}.mp4")
                if not os.path.exists(pth) or os.path.getsize(pth) < 10000:
                    try:
                        req = urllib.request.Request(f"https://assets.mixkit.co/videos/{vid}/{vid}-1080.mp4", headers={"User-Agent": "Mozilla/5.0"})
                        open(pth, "wb").write(urllib.request.urlopen(req, timeout=60).read())
                    except Exception: continue
                if os.path.exists(pth) and os.path.getsize(pth) > 10000: got.append(pth)
    if len(got) < 4:  # 마지막 예비: 저장소에 있는 릴스용 세로 영상 (가운데를 잘라 쓴다)
        bd = os.path.join(ROOT, "scripts", "reels", "assets", "broll")
        got += [os.path.join(bd, f) for f in sorted(os.listdir(bd)) if f.split("_")[0] in ("chip", "datacenter", "market", "money", "city")] if os.path.isdir(bd) else []
    for pth in got:
        try:
            d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pth], capture_output=True, text=True).stdout.strip())
            if d > 3: CUTS.append((pth, d))
        except Exception: pass
    print(f"  실사 컷 소스 {len(CUTS)}개")


MEDIA_LOG = []     # 검수용: 실제로 쓴 실사 소스 [장면, 종류, 파일]
POOLS = {}         # 장면 번호 → 그 장면 내용에 맞는 실사 소스 [(종류, 경로, 길이)]
USED = set()


def _pex(path_q, key):
    req = urllib.request.Request("https://api.pexels.com/" + path_q, headers={"Authorization": key, "User-Agent": "Mozilla/5.0"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def load_pools(spec):
    """장면마다 원고의 q 검색어로 Pexels 사진·영상을 받아 둔다 (무료, 출처 표기 불필요). 같은 소스는 영상 전체에서 한 번만 쓴다"""
    key = os.environ.get("PEXELS_API_KEY", "")
    import urllib.parse
    cache = os.path.join(ROOT, "scripts", "youtube", "long", ".cache"); os.makedirs(cache, exist_ok=True)
    seen = set()
    for k, sc in enumerate(spec["scenes"]):
        pool = []
        lib = os.path.join(ROOT, "scripts", "blog", "media", "lib")
        for f in sc.get("lib", []):  # 원고에 장면별로 골라 둔 무료 소재 (저장소 소재 창고: Mixkit 라이선스)
            pth = os.path.join(lib, f)
            if not os.path.exists(pth): continue
            if f.endswith(".mp4"):
                try: d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pth], capture_output=True, text=True).stdout.strip())
                except Exception: continue
                pool.append(("video", pth, d))
            else: pool.append(("photo", pth, 0))
        for qi, q in enumerate(sc.get("q", [])):
            qq = urllib.parse.quote(q)
            if not key: break
            try:  # 사진 2장 (천천히 확대·이동하며 보여 준다)
                for ph in _pex(f"v1/search?query={qq}&per_page=4&orientation=landscape", key).get("photos", [])[:2]:
                    if ph["id"] in seen: continue
                    pth = os.path.join(cache, f"pexp_{ph['id']}.jpg")
                    if not os.path.exists(pth) or os.path.getsize(pth) < 5000:
                        open(pth, "wb").write(urllib.request.urlopen(urllib.request.Request(ph["src"]["large2x"], headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read())
                    seen.add(ph["id"]); pool.append(("photo", pth, 0))
            except Exception as e: print("  Pexels 사진 실패:", q, str(e)[:80])
            if qi > 1: continue
            try:  # 영상 1개 (검색어 앞의 두 개만)
                for v in _pex(f"videos/search?query={qq}&per_page=3&orientation=landscape&size=medium", key).get("videos", [])[:2]:
                    if v["id"] in seen: continue
                    fs_ = sorted([f for f in v["video_files"] if f.get("file_type") == "video/mp4" and 1280 <= (f.get("width") or 0) <= 1920], key=lambda f: f["width"])
                    if not fs_ or v.get("duration", 0) < 4: continue
                    pth = os.path.join(cache, f"pex_{v['id']}.mp4")
                    if not os.path.exists(pth) or os.path.getsize(pth) < 10000:
                        open(pth, "wb").write(urllib.request.urlopen(urllib.request.Request(fs_[0]["link"], headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read())
                    seen.add(v["id"]); pool.append(("video", pth, float(v["duration"]))); break
            except Exception as e: print("  Pexels 영상 실패:", q, str(e)[:80])
        if len(pool) < 3: pool += mixkit_pool(sc.get("q", []), seen, 3 - len(pool))
        # 골라 둔 순서를 지키되, Pexels 사진·영상이 있으면 번갈아 섞는다
        picked = [x for x in pool if os.path.dirname(x[1]) == lib]; pool = [x for x in pool if os.path.dirname(x[1]) != lib]
        ph_ = [x for x in pool if x[0] == "photo"]; vd_ = [x for x in pool if x[0] == "video"]; mix_ = list(picked)
        while ph_ or vd_:
            if vd_: mix_.append(vd_.pop(0))
            if ph_: mix_.append(ph_.pop(0))
            if ph_: mix_.append(ph_.pop(0))
        POOLS[k] = mix_
    print("  장면별 실사 소스:", {k: len(v) for k, v in POOLS.items()})


def mixkit_pool(queries, seen, need):
    """Pexels 키가 없거나 결과가 모자랄 때: Mixkit 태그 페이지에서 그 장면 검색어에 맞는 영상 (무료, 출처 표기 불필요)"""
    cache = os.path.join(ROOT, "scripts", "youtube", "long", ".cache")
    man = json.load(open(os.path.join(ROOT, "scripts", "reels", "assets", "manifest.json")))
    generic = {str(v) for vs in man["video"].values() for v in vs}  # 릴스 공용 영상(이미 여러 번 쓴 것)은 빼고
    out = []
    for q in queries:
        words = [w for w in re.split(r"\s+", q.lower()) if len(w) > 2]
        for slug in ["-".join(words)] + words[::-1]:
            try:
                page = urllib.request.urlopen(urllib.request.Request(f"https://mixkit.co/free-stock-video/{slug}/", headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("utf-8", "ignore")
            except Exception: continue
            ids = []
            for vid in re.findall(r"/free-stock-video/[a-z0-9-]+-(\d+)/", page):
                if vid not in ids and vid not in generic and ("mk" + vid) not in seen: ids.append(vid)
            got = 0
            for vid in ids[:4]:
                pth = os.path.join(cache, f"mk_{vid}.mp4")
                if not os.path.exists(pth) or os.path.getsize(pth) < 10000:
                    for qual in ("1080", "720"):
                        try:
                            open(pth, "wb").write(urllib.request.urlopen(urllib.request.Request(f"https://assets.mixkit.co/videos/{vid}/{vid}-{qual}.mp4", headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read()); break
                        except Exception: pass
                if os.path.exists(pth) and os.path.getsize(pth) > 10000:
                    try: d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pth], capture_output=True, text=True).stdout.strip())
                    except Exception: continue
                    seen.add("mk" + vid); out.append(("video", pth, d)); got += 1
                    if got >= 1: break
            if got: break
        if len(out) >= need: break
    return out


def photo_frames(pth, n, seed):
    """사진을 천천히 확대하며 한쪽으로 흐르게 (켄 번즈)"""
    im = Image.open(pth).convert("RGB"); r = max(W / im.width, H / im.height) * 1.18
    im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]; dx, dy = dirs[seed % len(dirs)]; zin = seed % 2 == 0
    out = []; kk = min(im.width / W, im.height / H)
    for i in range(n):
        t = i / max(1, n - 1); z = (1.0 + .08 * t) if zin else (1.08 - .08 * t)
        w, h = W * kk / z, H * kk / z
        cx = im.width / 2 + dx * (im.width - w) / 2 * (t - .5) * 1.6; cy = im.height / 2 + dy * (im.height - h) / 2 * (t - .5) * 1.6
        l = min(max(cx - w / 2, 0), im.width - w); tp = min(max(cy - h / 2, 0), im.height - h)
        out.append(np.asarray(im.resize((W, H), Image.BILINEAR, box=(l, tp, l + w, tp + h))))
    return out


def cut_frames(n, scene=None):
    """이 장면 내용에 맞는 소스 중 아직 안 쓴 것 → 다른 장면의 안 쓴 것 → 예비 영상 순서로"""
    cand = [x for x in POOLS.get(scene, []) if x[1] not in USED]  # 이 장면 것만 (다른 장면 소재를 끌어오면 내용과 안 맞는다)
    _cut_i[0] += 1
    if cand:
        kind, pth, d = cand[0]; USED.add(pth); MEDIA_LOG.append([scene, kind, os.path.basename(pth)])
        if kind == "photo": return photo_frames(pth, n, _cut_i[0])
    else:
        return None  # 이 장면에 맞는 새 소스가 없으면 실사 컷을 쓰지 않는다 (같은 영상 반복 금지)
    st = (d - n / FPS - .2) * ((_cut_i[0] * 0.37) % 1) if d > n / FPS + .5 else 0
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, st):.2f}", "-i", pth, "-frames:v", str(n), "-vf",
                          f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=rgb24", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3) if raw else np.zeros((1, H, W, 3), np.uint8)
    return [fr[min(i, len(fr) - 1)] for i in range(n)]


def shade(img):
    """실사 컷: 자막이 잘 보이게 아래쪽을 어둡게 (문장은 화면에 다시 쓰지 않는다: 아래 자막 하나만)"""
    d = AD(img); d.rectangle([0, 0, W, H], fill=(6, 14, 28, 70))
    for k in range(12): d.rectangle([0, H - 330 + k * 28, W, H], fill=(6, 14, 28, 14))


def kinetic(img, text, u, L):
    """실사 컷 위 큰 글자: 단어가 차례로 떠오르고 숫자는 금색"""
    d = AD(img); d.rectangle([0, 0, W, H], fill=(6, 14, 28, 120))
    f = F("Heavy", 92); lines = wrap(d, text, f, 1560)
    while len(lines) > 3 and f.size > 50: f = F("Heavy", f.size - 6); lines = wrap(d, text, f, 1560)
    words = sum(len(l.split(" ")) for l in lines); shown = words * clamp(u / max(.6, L * .55)); k = 0
    lh = f.size + 22; y0 = H / 2 - len(lines) * lh / 2 - 20
    for li, l in enumerate(lines):
        x = W / 2 - d.textlength(l, font=f) / 2; y = y0 + li * lh
        for w_ in l.split(" "):
            a = clamp(shown - k); k += 1
            if a > 0:
                col = GOLD_L if re.search(r"\d", w_) else IVORY
                d.text((x, y + 18 * (1 - ease(a))), w_, font=f, fill=(*col, int(255 * a)))
            x += d.textlength(w_ + " ", font=f)

SHOTS = {}
SHOTS_S = {}
ICON = ICON_S = None


VOICE_SPEED = 1.15   # 원음 대비 말 빠르기 (2026-10-21 운영자: "느려서 지루하다")
VOICE_PITCH = 1.04   # 톤 살짝 위로 (약 0.7반음)
GAP = .22            # 문장 사이 쉼(초)


def pace(a):
    """속도와 톤을 함께 조정: asetrate로 톤을 올리고(그만큼 빨라짐) 나머지 속도는 atempo로"""
    out = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                          f"asetrate={int(SR * VOICE_PITCH)},aresample={SR},atempo={VOICE_SPEED / VOICE_PITCH:.4f}", "-f", "f32le", "-"],
                         input=np.asarray(a, np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(out, np.float32).copy()


def make_music(n, seed=7):
    """잔잔한 배경음악을 직접 만든다 (저작권 걱정 없음): 일렉트릭 피아노 화음 + 부드러운 베이스 + 아주 작은 하이햇, 84BPM.
    16마디마다 진행을 바꿔 10분 내내 같은 반복으로 들리지 않게 한다."""
    from scipy import signal
    rng = np.random.default_rng(seed); L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    bpm = 84; beat = 60 / bpm; bar = 4 * beat
    note = lambda k: 440 * 2 ** ((k - 69) / 12)
    def add(at, x, gl=1.0, gr=1.0):
        i = int(at * SR)
        if i >= n or i < 0: return
        m = min(len(x), n - i); L[i:i + m] += x[:m] * gl; R[i:i + m] += x[:m] * gr
    def ep(f, dur, amp):  # 일렉트릭 피아노 비슷한 소리
        t = np.arange(int(SR * dur)) / SR
        x = np.sin(2 * np.pi * f * t + .8 * np.exp(-t * 3) * np.sin(2 * np.pi * f * 2 * t)) + .25 * np.sin(2 * np.pi * f * 3 * t) * np.exp(-t * 4)
        return (amp * x * np.minimum(1, t / .008) * np.exp(-t * 1.1)).astype(np.float32)
    def bass(f, dur):
        t = np.arange(int(SR * dur)) / SR
        return (.22 * np.sin(2 * np.pi * f * t) * np.minimum(1, t / .02) * np.exp(-t * 1.3)).astype(np.float32)
    hatsrc = signal.lfilter(*signal.butter(2, 8000 / (SR / 2), "high"), rng.standard_normal(int(SR * .05))).astype(np.float32)
    hat = lambda a: a * hatsrc * np.exp(-np.arange(len(hatsrc)) / SR * 70).astype(np.float32)
    progs = [[[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 64]],     # Am7 Fmaj7 Cmaj7 G6
             [[50, 53, 57, 60], [55, 59, 62, 65], [48, 52, 55, 59], [57, 60, 64, 67]],     # Dm7 G7 Cmaj7 Am7
             [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [55, 59, 62, 64]]]     # Fmaj7 Em7 Dm7 G6
    t0, bi = 0.0, 0; total = n / SR
    while t0 < total:
        ch = progs[(bi // 16) % 3][bi % 4]
        for j, k in enumerate(ch): add(t0 + j * .018, ep(note(k), 3.2, .07), 1 - .2 * (j % 2), .8 + .2 * (j % 2))
        for j, k in enumerate(ch[1:3]): add(t0 + 2.5 * beat + j * .02, ep(note(k + 12), 1.6, .035), .8, 1)  # 가벼운 장식음
        add(t0, bass(note(ch[0] - 24), 2.0)); add(t0 + 2 * beat, bass(note(ch[0] - 24), 1.4))
        if (bi // 8) % 2 == 1 or bi >= 16:
            for b_ in range(8): add(t0 + b_ * beat / 2, hat(.05 if b_ % 2 else .08), .7, 1)
        t0 += bar; bi += 1
    fi = int(SR * 2); L[:fi] *= np.linspace(0, 1, fi); R[:fi] *= np.linspace(0, 1, fi)
    fo = int(SR * 3); L[-fo:] *= np.linspace(1, 0, fo); R[-fo:] *= np.linspace(1, 0, fo)
    m = np.stack([L, R], 1); m = signal.lfilter(*signal.butter(2, 5000 / (SR / 2), "low"), m, axis=0)
    return (m / (np.abs(m).max() + 1e-9)).astype(np.float32)


MUSIC_LEVEL = .085   # 목소리 대비 음악 크기 (말할 때는 더 줄인다)


def main():
    global BG, LOGO, ICON, PHONE
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
            for k in ("list", "value", "brief", "port"):  # 밸류노트 소개 장면에서 번갈아 보여 줄 앱 화면
                q = p.replace(".png", "_" + k + ".png")
                if os.path.exists(q): SHOTS[img + ":" + k] = Image.open(q).convert("RGB")

    # 1) 음성 (문장마다) → 장면 길이
    if not fake: from tts import speak
    timeline = []; t = 0.0; audio = []
    for sc in spec["scenes"]:
        lines = []
        for l in sc["lines"]:  # "?"로 시작하는 문장은 값이 없으면 뺀다
            if l.startswith("?"):
                try: lines.append(fill(l[1:], V))
                except KeyError: print("  선택 문장 생략:", l[:40])
            else: lines.append(fill(l, V))
        lt = []; u = .35
        for l in lines:
            a = np.zeros(int(len(l) / 9.2 * SR), np.float32) if fake else pace(speak(to_speech(l), 1.1))
            lt.append((u, len(a) / SR, l)); audio.append((t + u, a)); u += len(a) / SR + GAP
        dur = u + .4
        timeline.append({"sc": sc, "start": t, "dur": dur, "lines": lt}); t += dur
    total = t
    # 2) 음성 합치기
    mix = np.zeros(int((total + 1) * SR), np.float32)
    for st, a in audio:
        i = int(st * SR); mix[i:i + len(a)] += a[: len(mix) - i]
    if np.abs(mix).max() > 0: mix = mix / np.abs(mix).max() * .9
    # 배경음악: 말하는 동안 자동으로 낮춘다(덕킹)
    from scipy import signal as _sg
    env = np.convolve(np.abs(mix), np.ones(int(SR * .25)) / (SR * .25), "same"); env = np.clip(env / (env.max() + 1e-9) * 4, 0, 1)
    env = _sg.lfilter([.0005], [1, -.9995], env)  # 천천히 오르내리게
    env = np.clip(env / (env.max() + 1e-9), 0, 1)
    mus = make_music(len(mix)) * (MUSIC_LEVEL * (1 - .45 * env))[:, None]
    st_ = np.stack([mix, mix], 1) + mus
    st_ = (st_ / max(1.0, np.abs(st_).max() / .95)).astype(np.float32)
    wav = os.path.join(out, "voice.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", wav], input=st_.tobytes(), check=True)
    # 3) 영상
    tmp = os.path.join(out, "video_noaudio.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    load_cuts(spec.get("broll_q", ["stock market screen", "computer chip", "data center", "city night"]))
    load_pools(spec)
    prev_last = None
    for k, s in enumerate(timeline):
        sc = s["sc"]; n = int(round(s["dur"] * FPS))
        frames_bg = broll_frames(sc["v"].get("clip", "market"), n) if sc["v"]["type"] == "broll" else None
        chapter = next((x["sc"].get("chapter") for x in reversed(timeline[:k + 1]) if x["sc"].get("chapter")), "")
        src = fill(sc["v"].get("src", ""), V); asof = V.get("asof") if sc["v"]["type"] not in ("broll", "end") else ""
        beats = plan_beats(sc["v"]["type"], s["dur"], s["lines"], len(POOLS.get(k, []))); bi = -1; cutbuf = None; prevf = "wide"; curf = "wide"; shown = None; from_img = None
        for i in range(n):
            u = i / FPS
            while bi + 1 < len(beats) and u >= beats[bi + 1][0]:
                bi += 1; b = beats[bi]; from_img = shown if b[2] not in ("cam", "phone") or beats[bi - 1][2] not in ("cam", "phone") else None
                if b[2] == "cut":
                    cutbuf = cut_frames(int(math.ceil((b[1] - b[0]) * FPS)) + 2, k)
                    if cutbuf is None:  # 새 소스가 없으면 그래픽 구도 이동으로 대신
                        alt_ = ["pc", "pt", "pb"][bi % 3] if curf == "wide" else "wide"
                        b = beats[bi] = (b[0], b[1], "cam", alt_); prevf, curf = curf, alt_; from_img = None
                elif b[2] == "cam": prevf, curf = curf, b[3]
                elif b[2] == "phone": prevf = curf = "wide"
            b = beats[bi]; bu = u - b[0]; bl = b[1] - b[0]
            if b[2] in ("cut", "stat"):
                if b[2] == "cut": img = Image.fromarray(cutbuf[min(int(bu * FPS), len(cutbuf) - 1)]); shade(img)
                else: img = stat_card(b[3], b[4], bu, bl)
            else:
                if b[2] == "phone":
                    vs_ = phone_views(sc["v"]["img"]); cv = vs_[b[3] % len(vs_)]; pv = vs_[(b[3] - 1) % len(vs_)]
                    PHONE = (pv, cv, clamp(bu / max(bl, .1)), 1.0 if b[3] == 0 else clamp(bu / .5))
                else: PHONE = None
                img = draw_scene(sc, V, u, s["dur"], s["lines"], frames_bg[i] if frames_bg is not None else None)
                if b[2] == "cam": img = cam(img, prevf, curf, bu / .45, clamp(bu / max(bl, .1)))
            if from_img is not None and bu < .2: img = Image.blend(from_img, img, bu / .2)
            shown = img.copy()
            chrome(img, chapter if sc["v"]["type"] != "end" else "", src, asof, u, (s["start"] + u) / total)
            cur = next((l for l in reversed(s["lines"]) if u >= l[0] - .05), None)
            if cur and u <= cur[0] + cur[1] + .3 : subtitle(img, cur[2], u - cur[0], cur[1])
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
            "events": spec.get("events", []), "pinned_comment": fill(spec.get("pinned_comment", ""), V), "rendered_at": dt.datetime.now(dt.timezone.utc).isoformat(), "company": spec.get("company"),
            "qa": {"media": MEDIA_LOG, "lines": [[round(x["start"] + a, 2), round(d_, 2), l, to_speech(l)] for x in timeline for (a, d_, l) in x["lines"]]}}
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), ensure_ascii=False, indent=1)
    print(f"완료: {total / 60:.1f}분 → {out}")


if __name__ == "__main__":
    main()
