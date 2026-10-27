"""What Korea Says (사이드 채널) 롱폼 렌더러 — 2026-10-27
사용: python3 scripts/side/render.py <원고 아이디 ...>   (아이디가 없으면 아직 안 만든 원고 전부)

원고: scripts/side/specs/<id>.json  (장면 t: open/stat/roadmap/chapter/fact/jersey/timeline/quote/final/schedule/recap/end, 장면마다 say: 영어 문장 목록)
결과: social/side/<id>/{meta.json, thumb.jpg, en.srt}  + 영상(롱폼·쇼츠)은 GitHub 릴리스 side-<id> 에 올린다
      social/side/queue.json  (Supabase sc_fetch/sc_import 가 10분마다 읽어 관리자 /side 검수 탭에 넣는다)

원칙 (벤치마크 claude/side-channel/benchmark-2026-10-27.md)
- 영어 원어민 성우(타입캐스트 Landon) 내레이션 + 처음부터 끝까지 일정한 영어 자막
- 남의 영상은 쓰지 않는다: 댓글 카드·사실 카드·숫자·일정표 그래픽 + Pexels 무료 사진(키가 있을 때)
- 같은 화면이 오래 머물지 않게 배경은 천천히 확대·이동, 카드 요소는 순서대로 등장
- 타입캐스트 키가 없으면(로컬 미리보기) 문장 길이로 시간을 잡고 무음으로 만든다
"""
import datetime as dt, glob, hashlib, json, math, os, random, subprocess, sys, urllib.parse, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "social", "side")
CACHE = os.path.join(HERE, ".cache"); os.makedirs(CACHE, exist_ok=True)
REPO = os.environ.get("GITHUB_REPOSITORY", "immin03/haeja")
W, H, FPS, SR = 1920, 1080, 30, 44100

NAVY = (15, 27, 51); NAVY2 = (27, 45, 82); CARD = (22, 38, 74); RED = (255, 75, 62); WHITE = (255, 255, 255)
GRAY = (201, 211, 230); DIM = (130, 146, 176); GOLD = (255, 199, 77)


def _font_path(bold=True):
    for p in (["/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"] if bold else
              ["/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]):
        if os.path.exists(p): return p
    hits = glob.glob("/usr/share/fonts/**/NotoSansCJK*.tt*", recursive=True)
    return hits[0]
_FC = {}
def F(size, bold=True):
    k = (size, bold)
    if k not in _FC: _FC[k] = ImageFont.truetype(_font_path(bold), size, index=1)   # index 1 = KR
    return _FC[k]


# ---------------- 음성 ----------------
def say(text):
    """영어 문장 → float32 mono. 키가 없으면 길이만 맞춘 무음 (미리보기용)"""
    if os.environ.get("TYPECAST_API_KEY"):
        sys.path.insert(0, os.path.join(ROOT, "scripts", "youtube", "long")); sys.path.insert(0, os.path.join(ROOT, "scripts", "reels"))
        import en_audio
        return en_audio._say_en(text)
    words = len(text.split())
    return np.zeros(int(SR * (0.35 + words / 2.55)), np.float32)


def bgm(n):
    """저작권 걱정 없는 잔잔한 패드 (코드 진행 Am-F-C-G, 느린 아르페지오)"""
    t = np.arange(n) / SR; out = np.zeros(n, np.float32)
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (130.81, 196.0, 261.63), (196.0, 246.94, 293.66)]
    seg = 4.0
    for k in range(int(n / SR / seg) + 1):
        a, b = int(k * seg * SR), min(n, int((k + 1) * seg * SR) + int(SR * .6))
        if a >= n: break
        tt = t[a:b] - k * seg; env = np.minimum(1, tt / 1.2) * np.exp(-np.maximum(0, tt - seg) * 3)
        for f in chords[k % 4]:
            out[a:b] += (np.sin(2 * np.pi * f * tt) * .5 + np.sin(2 * np.pi * f * 2 * tt) * .12).astype(np.float32) * env.astype(np.float32) * .06
        for j, f in enumerate(chords[k % 4] * 2):   # 아르페지오
            s = a + int(j * .5 * SR); e2 = min(n, s + int(SR * .9))
            if s >= n: break
            ttt = t[s:e2] - t[s]; out[s:e2] += (np.sin(2 * np.pi * f * 2 * ttt) * np.exp(-ttt * 4)).astype(np.float32) * .025
    return out


# ---------------- 배경 사진 (Pexels) ----------------
def pexels_photo(q, used):
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key or not q: return None
    try:
        req = urllib.request.Request(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(q)}&per_page=6&orientation=landscape",
                                     headers={"Authorization": key, "User-Agent": "Mozilla/5.0"})
        for ph in json.loads(urllib.request.urlopen(req, timeout=30).read()).get("photos", []):
            if ph["id"] in used: continue
            p = os.path.join(CACHE, f"pexp_{ph['id']}.jpg")
            if not os.path.exists(p) or os.path.getsize(p) < 5000:
                open(p, "wb").write(urllib.request.urlopen(urllib.request.Request(ph["src"]["large2x"], headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read())
            used.add(ph["id"]); return p
    except Exception as e: print("  Pexels 실패:", q, str(e)[:80])
    return None


def gradient_bg(seed):
    rnd = random.Random(seed); im = Image.new("RGB", (W + 200, H + 120), NAVY); d = ImageDraw.Draw(im)
    cx, cy = rnd.randint(500, 1500), rnd.randint(300, 800)
    for r in range(900, 0, -12):
        a = (900 - r) / 900; c = tuple(int(NAVY[i] + (NAVY2[i] - NAVY[i]) * a) for i in range(3)); d.ellipse([cx - r * 1.6, cy - r, cx + r * 1.6, cy + r], fill=c)
    return im.filter(ImageFilter.GaussianBlur(40))


def photo_bg(path):
    im = Image.open(path).convert("RGB"); sc = max((W + 200) / im.width, (H + 120) / im.height)
    im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
    l, t = (im.width - W - 200) // 2, (im.height - H - 120) // 2; im = im.crop((l, t, l + W + 200, t + H + 120))
    im = im.filter(ImageFilter.GaussianBlur(3))
    ov = Image.new("RGB", im.size, NAVY); return Image.blend(im, ov, .72)


# ---------------- 실사 영상 (Mixkit 무료 라이선스: 상업적 이용 가능, 출처 표기 불필요) ----------------
def mixkit_clip(vid):
    p = os.path.join(CACHE, f"mix_{vid}.mp4")
    if os.path.exists(p) and os.path.getsize(p) > 20000: return p
    for q in ("1080", "720", "360"):
        try:
            data = urllib.request.urlopen(urllib.request.Request(f"https://assets.mixkit.co/videos/{vid}/{vid}-{q}.mp4", headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read()
            if len(data) > 20000: open(p, "wb").write(data); return p
        except Exception: continue
    return None


def clip_len(path):
    try: return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip())
    except Exception: return 0.0


class Footage:
    """장면 길이만큼 실사 영상을 1920x1080 프레임으로 읽는다 (짧으면 반복)"""
    def __init__(self, path, dur, start=0.0, loop=True):
        args = ["ffmpeg", "-v", "error"] + (["-stream_loop", "-1"] if loop else []) + ["-ss", f"{start:.2f}", "-i", path,
                "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}", "-t", f"{dur + 1:.2f}",
                "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        self.p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL); self.last = None
    def frame(self):
        b = self.p.stdout.read(W * H * 3)
        if len(b) == W * H * 3: self.last = Image.frombytes("RGB", (W, H), b)
        return self.last
    def close(self):
        try: self.p.stdout.close(); self.p.kill()
        except Exception: pass


# ---------------- 그리기 도우미 ----------------
def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w_
    if cur: lines.append(cur)
    return lines


def wrap_ko(d, text, font, maxw):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=font) <= maxw: cur += ch
        else: lines.append(cur); cur = ch
    if cur: lines.append(cur)
    return lines


def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def layer(size=(W, H)): return Image.new("RGBA", size, (0, 0, 0, 0))


def paste_fade(base, lay, a, dy=0):
    if a <= 0: return
    if a < 1:
        al = lay.split()[3].point(lambda v: int(v * a)); lay = lay.copy(); lay.putalpha(al)
    base.alpha_composite(lay, (0, int(dy)))


def rrect(d, box, r, fill, outline=None, width=0): d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


# ---------------- 장면 그래픽 (정적 레이어 목록: [(등장 시각, 레이어)]) ----------------
def scene_layers(sc, total_dur, ctx):
    t = sc["t"]; L = []
    def card(draw_fn, at):
        im = layer(); draw_fn(ImageDraw.Draw(im), im); L.append((at, im))
    if t == "story":
        if sc.get("chip"):
            def c(d, im):
                fk = F(38); tx = sc["chip"].upper(); tw = d.textlength(tx, font=fk); rrect(d, (60, 140, 60 + tw + 52, 206), 33, RED); d.text((86, 146), tx, font=fk, fill=WHITE)
            card(c, 0.1)
        if sc.get("big"):
            def b(d, im):
                fb = F(200); tx = sc["big"]
                while d.textlength(tx, font=fb) > 1600: fb = F(fb.size - 10)
                tw = d.textlength(tx, font=fb); x = (W - tw) / 2; y = 330
                d.text((x + 6, y + 8), tx, font=fb, fill=(0, 0, 0, 150)); d.text((x, y), tx, font=fb, fill=WHITE)
            card(b, 0.35)
    elif t == "kinetic":
        g = sc.get("glyphs", []); n = len(g); step = max(.8, (total_dur - 1) / max(1, n))
        for i, gl in enumerate(g):
            def f(d, im, i=i, gl=gl):
                fb = F(240 if len(gl) <= 2 else 170); slot = W / n; tw = d.textlength(gl, font=fb); x = slot * i + (slot - tw) / 2
                d.text((x + 6, 300 + 8), gl, font=fb, fill=(0, 0, 0, 150)); d.text((x, 300), gl, font=fb, fill=RED if i == n - 1 else WHITE)
            card(f, 0.3 + i * step)
    elif t == "clip":
        def f(d, im):
            fk = F(30); tx = "SOURCE: " + sc.get("credit", ""); tw = d.textlength(tx, font=fk); rrect(d, (60, 140, 60 + tw + 40, 196), 12, (0, 0, 0, 170)); d.text((80, 147), tx, font=fk, fill=WHITE)
        card(f, 0.0)
    elif t == "open":
        def f(d, im):
            fb = F(260); tw = d.textlength(sc["big"], font=fb); d.text(((W - tw) / 2, 250), sc["big"], font=fb, fill=RED)
        card(f, 0.2)
        def g(d, im):
            fs = F(64, False); tw = d.textlength(sc["small"], font=fs); d.text(((W - tw) / 2, 600), sc["small"], font=fs, fill=WHITE)
        card(g, 1.4)
    elif t == "stat":
        def f(d, im):
            fb = F(300); tw = d.textlength(sc["num"], font=fb); d.text(((W - tw) / 2, 190), sc["num"], font=fb, fill=WHITE)
        card(f, 0.2)
        def g(d, im):
            fs = F(54, False); ls = wrap(d, sc["label"], fs, 1300)
            for i, l in enumerate(ls): tw = d.textlength(l, font=fs); d.text(((W - tw) / 2, 590 + i * 74), l, font=fs, fill=GRAY)
        card(g, 0.9)
    elif t in ("roadmap", "recap"):
        def h(d, im):
            d.text((260, 150), "TODAY" if t == "roadmap" else "IN SHORT", font=F(44), fill=RED)
        card(h, 0.1)
        n = len(sc["items"]); step = max(.6, min(1.6, (total_dur - 1.5) / max(1, n)))
        for i, it in enumerate(sc["items"]):
            def f(d, im, i=i, it=it):
                y = 250 + i * 118; rrect(d, (260, y, 1660, y + 96), 22, CARD)
                d.ellipse((290, y + 22, 342, y + 74), fill=RED); num = str(i + 1); fn = F(34); d.text((316 - d.textlength(num, font=fn) / 2, y + 26), num, font=fn, fill=WHITE)
                d.text((376, y + 18), it, font=F(48), fill=WHITE)
            card(f, 0.5 + i * step)
    elif t == "chapter":
        def f(d, im):
            d.text((260, 330), f"PART {sc['n']}", font=F(56), fill=RED)
            ls = wrap(d, sc["title"], F(110), 1400)
            for i, l in enumerate(ls): d.text((252, 420 + i * 132), l, font=F(110), fill=WHITE)
            d.rectangle((260, 410 + len(ls) * 132 + 30, 460, 410 + len(ls) * 132 + 40), fill=RED)
        card(f, 0.1)
    elif t == "fact":
        def k(d, im):
            fk = F(40); tw = d.textlength(sc["kicker"].upper(), font=fk); rrect(d, (240, 250, 240 + tw + 56, 322), 36, RED)
            d.text((268, 258), sc["kicker"].upper(), font=fk, fill=WHITE)
        card(k, 0.15)
        def f(d, im):
            fh = F(84); ls = wrap(d, sc["head"], fh, 1440)
            for i, l in enumerate(ls[:4]): d.text((240, 370 + i * 112), l, font=fh, fill=WHITE)
        card(f, 0.6)
    elif t == "jersey":
        def f(d, im):
            cx, cy, k = 1260, 470, .78
            P = lambda x, y: (cx + x * k, cy + y * k)
            body = [P(-330, -300), P(-120, -360), P(120, -360), P(330, -300), P(470, -120), P(330, -40), P(300, 360), P(-300, 360), P(-330, -40), P(-470, -120)]
            d.polygon(body, fill=(214, 40, 52)); d.polygon([P(-120, -360), P(0, -280), P(120, -360)], fill=NAVY)
            fb = F(330); tw = d.textlength("7", font=fb); d.text((cx - tw / 2, cy - 230), "7", font=fb, fill=WHITE)
        card(f, 0.2)
        def g(d, im):
            d.text((240, 260), "59", font=F(220), fill=GOLD); d.text((250, 520), "goals for Korea", font=F(48), fill=WHITE)
            d.text((250, 590), "New national record", font=F(40, False), fill=GRAY)
        card(g, max(1.0, total_dur * .35))
    elif t == "timeline":
        n = len(sc["rows"]); step = max(.8, (total_dur - 1) / max(1, n))
        sp_ = min(170, 640 // max(1, n))
        def ax(d, im): d.rectangle((300, 170, 306, 170 + (n - 1) * sp_ + 40), fill=DIM)
        card(ax, 0.1)
        for i, (when, what) in enumerate(sc["rows"]):
            def f(d, im, i=i, when=when, what=what):
                y = 170 + i * sp_; d.ellipse((285, y + 14, 321, y + 50), fill=RED if i == n - 1 else WHITE)
                d.text((360, y), when, font=F(44), fill=RED if i == n - 1 else GOLD)
                for j, l in enumerate(wrap(d, what, F(40, False), 1300)[:2]): d.text((360, y + 58 + j * 48), l, font=F(40, False), fill=WHITE)
            card(f, 0.4 + i * step)
    elif t in ("quote", "final"):
        def f(d, im):
            x0, y0, x1 = 220, (220 if t == "final" else 170), 1700
            ko_ls = wrap_ko(d, sc["ko"], F(40, False), x1 - x0 - 120); en_ls = wrap(d, sc["en"], F(66), x1 - x0 - 120)
            h_ = 130 + len(ko_ls) * 56 + 40 + len(en_ls) * 86 + (110 if sc.get("likes") else 50)
            rrect(d, (x0, y0, x1, y0 + h_), 34, WHITE)
            d.ellipse((x0 + 50, y0 + 44, x0 + 110, y0 + 104), fill=(222, 228, 240))
            d.text((x0 + 130, y0 + 46), sc.get("who", "Korean viewer"), font=F(34), fill=NAVY); d.text((x0 + 130, y0 + 88), sc["src"], font=F(28, False), fill=(110, 120, 140))
            y = y0 + 140
            for l in ko_ls: d.text((x0 + 60, y), l, font=F(40, False), fill=(120, 128, 146)); y += 56
            y += 30
            for l in en_ls: d.text((x0 + 60, y), l, font=F(66), fill=NAVY); y += 86
            y += 20
            if sc.get("likes"): d.text((x0 + 60, y), "♥", font=F(44), fill=RED); d.text((x0 + 116, y + 4), sc["likes"] + " likes", font=F(40), fill=NAVY)
            ctx["quote_h"] = h_
        card(f, 0.15)
        if t == "final":
            def g(d, im):
                d.text((220, 150), "THE COMMENT THAT SUMS IT UP", font=F(42), fill=GOLD)
            card(g, 0.05)
    elif t == "schedule":
        def h(d, im): d.text((260, 140), "WHAT'S NEXT", font=F(44), fill=RED)
        card(h, 0.1)
        n = len(sc["rows"]); step = max(.8, (total_dur - 1.5) / max(1, n))
        for i, (when, what) in enumerate(sc["rows"]):
            def f(d, im, i=i, when=when, what=what):
                y = 230 + i * 150; rrect(d, (260, y, 1660, y + 124), 24, CARD)
                d.text((310, y + 30), when, font=F(54), fill=GOLD); d.text((660, y + 34), what, font=F(50, False), fill=WHITE)
            card(f, 0.4 + i * step)
    elif t == "end":
        def f(d, im):
            fb = F(130); s = "What Korea "; tw = d.textlength(s + "Says", font=fb); x = (W - tw) / 2
            d.text((x, 300), s, font=fb, fill=WHITE); d.text((x + d.textlength(s, font=fb), 300), "Says", font=fb, fill=RED)
            fs = F(52, False); s2 = "Real Korean reactions, translated for the world"; d.text(((W - d.textlength(s2, font=fs)) / 2, 490), s2, font=fs, fill=GRAY)
        card(f, 0.1)
        def g(d, im):
            rrect(d, (W / 2 - 260, 640, W / 2 + 260, 752), 56, RED); fs = F(58); s = "SUBSCRIBE"; d.text(((W - d.textlength(s, font=fs)) / 2, 658), s, font=fs, fill=WHITE)
        card(g, 1.2)
    return L


def chrome(d, chapter):
    d.text((60, 42), "WHAT KOREA ", font=F(30), fill=WHITE); x = 60 + d.textlength("WHAT KOREA ", font=F(30)); d.text((x, 42), "SAYS", font=F(30), fill=RED)
    if chapter: d.text((60, 84), chapter, font=F(26, False), fill=DIM)


def sub_chunks(d, text):
    """두 줄에 들어가게 문장을 나눈다 (쉼표·접속어 우선)"""
    fs = F(46); ls = wrap(d, text, fs, 1560)
    if len(ls) <= 2: return [text]
    words, out, cur = text.split(), [], []
    for w_ in words:
        cur.append(w_)
        if len(wrap(d, " ".join(cur), fs, 1560)) > 2:
            cur.pop(); out.append(" ".join(cur)); cur = [w_]
        elif w_.endswith((",", ";", ":")) and len(wrap(d, " ".join(cur), fs, 1560)) == 2:
            out.append(" ".join(cur)); cur = []
    if cur: out.append(" ".join(cur))
    return out


def sub_piece(d, cur, t):
    t0, dd, text = cur; ch = sub_chunks(d, text)
    if len(ch) == 1: return text
    tot = sum(len(c) for c in ch); acc = t0
    for c in ch:
        acc += dd * len(c) / tot
        if t < acc: return c
    return ch[-1]


def subtitle(d, text):
    fs = F(46); ls = wrap(d, text, fs, 1560)[:2]; y = H - 70 - len(ls) * 62
    for i, l in enumerate(ls):
        tw = d.textlength(l, font=fs); x = (W - tw) / 2; rrect(d, (x - 22, y + i * 62 - 6, x + tw + 22, y + i * 62 + 58), 12, (0, 0, 0, 175))
        d.text((x, y + i * 62), l, font=fs, fill=WHITE)


# ---------------- 썸네일 ----------------
def thumbnail(spec, path):
    th = spec.get("thumb", {}); im = Image.new("RGB", (1280, 720), NAVY); d = ImageDraw.Draw(im)
    for r in range(700, 0, -10):
        a = (700 - r) / 700; d.ellipse([900 - r, 360 - r * .8, 900 + r, 360 + r * .8], fill=tuple(int(NAVY[i] + (NAVY2[i] - NAVY[i]) * a) for i in range(3)))
    art = th.get("art", "jersey")
    if art == "jersey":
        cx, cy, k = 1075, 380, .82   # 등번호 7 유니폼 (글자와 겹치지 않게 오른쪽)
        P = lambda x, y: (cx + x * k, cy + y * k)
        body = [P(-210, -190), P(-75, -230), P(75, -230), P(210, -190), P(300, -75), P(210, -25), P(190, 230), P(-190, 230), P(-210, -25), P(-300, -75)]
        d.polygon(body, fill=(214, 40, 52)); d.polygon([P(-75, -230), P(0, -178), P(75, -230)], fill=NAVY)
        fb = F(230); d.text((cx - d.textlength("7", font=fb) / 2, cy - 160), "7", font=fb, fill=WHITE)
    elif art == "box":   # 로고 없는 빨간 과자 상자 + 둥근 초코 과자 + '금지' 표시
        box = Image.new("RGBA", (420, 300), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
        bd.rounded_rectangle((0, 40, 420, 300), 18, fill=(205, 30, 40)); bd.polygon([(0, 40), (60, 0), (480, 0), (420, 40)], fill=(160, 20, 30))
        for i in range(3):
            x0 = 40 + i * 120; bd.ellipse((x0, 120, x0 + 110, 230), fill=(84, 46, 26)); bd.ellipse((x0 + 12, 130, x0 + 98, 200), fill=(110, 64, 38))
        box = box.rotate(-8, expand=True, resample=Image.BICUBIC); im.paste(box, (835, 200), box)
        d.ellipse((830, 130, 1260, 560), outline=RED, width=34); d.line((880, 500, 1210, 190), fill=RED, width=34)
    d.text((60, 150), th.get("top", ""), font=F(78), fill=WHITE)
    fbig = F(190)
    while d.textlength(th.get("big", ""), font=fbig) > (700 if th.get("art") == "box" else 780): fbig = F(fbig.size - 10)
    d.text((52, 250), th.get("big", ""), font=fbig, fill=RED)
    rrect(d, (60, 520, 60 + d.textlength(th.get("sub", ""), font=F(52)) + 60, 604), 18, WHITE); d.text((90, 528), th.get("sub", ""), font=F(52), fill=NAVY)
    im.save(path, quality=92)


# ---------------- 렌더 ----------------
def build_timeline(spec):
    """문장별 음성 → [장면 시작, 장면 길이, [(문장 시작, 길이, 문장)]] 과 전체 음성"""
    segs, chunks, t = [], [], 0.8
    for sc in spec["scenes"]:
        st = t; lines = []
        if sc["t"] == "clip":
            src = os.path.join(ROOT, sc.get("file", ""))
            a0, a1 = float(sc.get("from", 0)), float(sc.get("to", 0)); dur = max(0.0, min(15.0, a1 - a0))
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a0:.2f}", "-t", f"{dur:.2f}", "-i", src, "-vn", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
            a = np.frombuffer(raw, dtype=np.float32).copy() * .9; chunks.append((t, a)); sc["_src"] = src
            if sc.get("caption"): lines.append((t, dur, sc["caption"]))
            t += dur + .3; segs.append((st, t - st, lines)); continue
        for s in sc["say"]:
            a = say(s); lines.append((t, len(a) / SR, s)); chunks.append((t, a)); t += len(a) / SR + .28
        t += .45
        segs.append((st, t - st, lines))
    total = t + 1.5
    mix = np.zeros(int(total * SR) + SR, np.float32)
    for t0, a in chunks: i = int(t0 * SR); mix[i:i + len(a)] += a
    return segs, total, mix


def render(sid):
    sp = os.path.join(HERE, "specs", sid + ".json"); spec = json.load(open(sp, encoding="utf-8"))
    od = os.path.join(OUT, sid); os.makedirs(od, exist_ok=True)
    print("렌더:", sid, flush=True)
    keep = []
    for sc in spec["scenes"]:
        if sc["t"] == "clip" and not os.path.exists(os.path.join(ROOT, sc.get("file", ""))): print("  인용 영상 없음 — 건너뜀:", sc.get("file")); continue
        keep.append(sc)
    spec["scenes"] = keep
    segs, total, voice = build_timeline(spec)
    # 소리: 목소리 + 배경 패드(말할 때 작아짐)
    env = np.convolve(np.abs(voice), np.ones(int(SR * .3)) / int(SR * .3), mode="same"); env = np.clip(env / (env.max() + 1e-9) * 5, 0, 1)
    music = bgm(len(voice)) * (1 - .55 * env)
    if np.abs(voice).max() > 0: voice = voice / np.abs(voice).max() * .9
    mix = np.clip(voice + music, -1, 1).astype(np.float32)
    wav = os.path.join(od, "audio.f32")
    mix.tofile(wav)
    # 배경
    used = set(); bgs = []; foots = []; used_mix = set()
    for k, sc in enumerate(spec["scenes"]):
        p = pexels_photo(sc.get("bg"), used) if sc.get("bg") else None
        bgs.append(photo_bg(p) if p else gradient_bg(sid + str(k)))
        fp = None
        if sc["t"] == "clip": fp = sc["_src"]
        else:
            for vid in sc.get("mix", []):
                if vid in used_mix and len(sc.get("mix", [])) > 1: continue
                fp = mixkit_clip(vid)
                if fp: used_mix.add(vid); break
        foots.append(fp)
    print("  실사 영상", sum(1 for f in foots if f), "/", len(foots), "장면", flush=True)
    # 장(챕터) 이름
    chap, chaps = "", []
    for (st, du, _), sc in zip(segs, spec["scenes"]):
        if sc["t"] == "chapter": chap = f"PART {sc['n']} · {sc['title']}"; chaps.append((st, sc["title"]))
        sc["_chap"] = chap
    ctx = {}; layers = [scene_layers(sc, du, ctx) for sc, (st, du, _) in zip(spec["scenes"], segs)]
    vid = os.path.join(od, "video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", vid], stdin=subprocess.PIPE)
    nfr = int(total * FPS); k = 0; cur_k = -1; reader = None
    DIM_ = {"story": .30, "kinetic": .55, "clip": 0.0, "stat": .62}
    for fi in range(nfr):
        t = fi / FPS
        while k + 1 < len(segs) and t >= segs[k + 1][0]: k += 1
        st, du, lines = segs[k]; lt = t - st; sc = spec["scenes"][k]
        if k != cur_k:
            if reader: reader.close()
            reader = None; cur_k = k
            if foots[k]:
                reader = Footage(foots[k], du, start=float(sc.get("from", 0)) if sc["t"] == "clip" else 0.0, loop=sc["t"] != "clip")
        fr_ = reader.frame() if reader else None
        if fr_ is not None:
            frame = fr_.convert("RGBA"); dim = DIM_.get(sc["t"], .72)
            if dim: frame = Image.blend(frame, Image.new("RGBA", (W, H), NAVY + (255,)), dim)
        else:
            bg = bgs[k]; z = 1 + .05 * (lt / max(du, 1)); ox = int(100 * (lt / max(du, 1)) * (1 if k % 2 else -1)) + 100
            cw, ch_ = int(W / z), int(H / z); left = max(0, min(bg.width - cw, ox + (W - cw) // 2)); top = max(0, min(bg.height - ch_, 60 + (H - ch_) // 2))
            frame = bg.crop((left, top, left + cw, top + ch_)).resize((W, H), Image.BILINEAR).convert("RGBA")
        for at, lay in layers[k]:
            a = ease((lt - at) / .45)
            if a > 0: paste_fade(frame, lay, a, dy=(1 - a) * 30)
        # 장면 끝 0.25초 페이드 아웃
        if du - lt < .25: frame = Image.blend(frame, Image.new("RGBA", (W, H), NAVY + (255,)), (1 - (du - lt) / .25) * .6)
        d = ImageDraw.Draw(frame)
        chrome(d, sc.get("_chap", ""))
        cur = next(((t0, dd, s) for (t0, dd, s) in lines if t0 <= t < t0 + dd + .28), None)
        if cur: subtitle(d, sub_piece(d, cur, t))
        ff.stdin.write(frame.convert("RGB").tobytes())
    if reader: reader.close()
    ff.stdin.close(); ff.wait()
    # 자막·썸네일·쇼츠
    srt = []
    for _, _, lines in segs:
        for t0, dd, s in lines:
            ch = sub_chunks(ImageDraw.Draw(Image.new("RGB", (8, 8))), s); tot = sum(len(c) for c in ch); acc = t0
            for c in ch: srt.append((acc, acc + dd * len(c) / tot, c)); acc += dd * len(c) / tot
    fmt = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(x * 1000 % 1000):03d}"
    open(os.path.join(od, "en.srt"), "w", encoding="utf-8").write("\n".join(f"{i + 1}\n{fmt(a)} --> {fmt(b)}\n{s}\n" for i, (a, b, s) in enumerate(srt)))
    thumbnail(spec, os.path.join(od, "thumb.jpg"))
    short = make_short(spec, segs, vid, od, srt)
    os.remove(wav)
    chapters = "\n".join(f"{int(s // 60)}:{int(s % 60):02d} {name}" for s, name in [(0, "Intro")] + chaps)
    return {"total": total, "chapters": chapters, "video": vid, "short": short}


def make_short(spec, segs, vid, od, srt):
    """세로 쇼츠 (최대 57초): 원고에서 short: true 인 장면(없으면 앞쪽 장면) → 위 고정 제목 띠, 가운데 화면(작은 자막은 잘라 냄), 아래 큰 자막, 끝에 풀버전 안내"""
    flag = [k for k, sc in enumerate(spec["scenes"]) if sc.get("short")]
    cand = flag or [k for k, sc in enumerate(spec["scenes"]) if sc["t"] in ("open", "story", "quote", "final", "stat")]
    pick, tot = [], 0
    for k in cand:
        if tot + segs[k][1] > 57: continue
        pick.append(k); tot += segs[k][1]
    if not pick: return None
    band = Image.new("RGB", (1080, 1920), NAVY); d = ImageDraw.Draw(band)
    th = spec.get("thumb", {})
    d.text((60, 190), th.get("top", ""), font=F(76), fill=WHITE)
    fb = F(150)
    while d.textlength(th.get("big", ""), font=fb) > 960: fb = F(fb.size - 8)
    d.text((54, 280), th.get("big", ""), font=fb, fill=RED)
    d.text((60, 1730), "Full story on our channel ▶ What Korea Says", font=F(40), fill=GRAY)
    bp = os.path.join(od, "_short_bg.png"); band.save(bp)
    parts, events, off = [], [], 0.0
    for i, k in enumerate(pick):
        st, du, _ = segs[k]; p = os.path.join(od, f"_s{i}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{st:.2f}", "-t", f"{du:.2f}", "-i", vid, "-i", bp, "-filter_complex",
                        "[0:v]crop=1240:880:340:0,scale=1080:-2[v];[1:v][v]overlay=0:470", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-r", str(FPS), p], check=True)
        parts.append(p)
        for a_, b_, txt in srt:
            if a_ >= st - .05 and b_ <= st + du + .05: events.append((a_ - st + off, b_ - st + off, txt))
        off += du
    lst = os.path.join(od, "_list.txt"); open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    joined = os.path.join(od, "_joined.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined], check=True)
    ts = lambda x: f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"
    ass = os.path.join(od, "_short.ass")
    font = "Noto Sans CJK KR"
    open(ass, "w", encoding="utf-8").write(
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Big,{font},70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,3,14,0,8,70,70,1290,1\n\n[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" +
        "".join(f"Dialogue: 0,{ts(a_)},{ts(b_)},Big,,0,0,0,,{txt}\n" for a_, b_, txt in events))
    out = os.path.join(od, "short.mp4")
    fdir = os.path.dirname(_font_path())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-vf", f"ass={ass}:fontsdir={fdir}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "copy", "-movflags", "+faststart", out], check=True)
    for p in parts + [lst, bp, joined, ass]: os.remove(p)
    return out


def publish(sid, res, spec):
    """릴리스에 올리고 meta.json 작성"""
    od = os.path.join(OUT, sid); stamp = dt.datetime.utcnow().strftime("%y%m%d%H%M"); tag = "side-" + sid
    meta = {"id": sid, "kind": "long", "title": spec["title"], "description": "",
            "tags": spec.get("tags", []), "scheduled_at": spec["scheduled_at"], "duration": round(res["total"], 1), "loc": spec.get("loc", {}),
            "plan_id": sid, "rendered_at": dt.datetime.now(dt.timezone.utc).isoformat(), "sources": spec.get("sources", [])}
    meta["description"] = build_description(spec, res["chapters"])
    meta["thumb"] = f"/social/side/{sid}/thumb.jpg?v={stamp}"
    if os.environ.get("GH_TOKEN"):
        sh = lambda a: subprocess.run(a, check=True)
        if subprocess.run(["gh", "release", "view", tag, "-R", REPO], capture_output=True).returncode != 0:
            sh(["gh", "release", "create", tag, "-R", REPO, "--title", f"What Korea Says {sid}", "--notes", "사이드 채널 검수용 영상 (자동 생성)", "--latest=false"])
        for key, src in (("video_url", res["video"]), ("short_url", res["short"])):
            if not src: continue
            name = f"{sid}-{'short-' if key == 'short_url' else ''}{stamp}.mp4"; up = os.path.join(od, name); os.replace(src, up)
            sh(["gh", "release", "upload", tag, up, "--clobber", "-R", REPO]); os.remove(up)
            meta[key] = f"https://github.com/{REPO}/releases/download/{tag}/{name}"
    else:
        meta["video_url"] = os.path.relpath(res["video"], ROOT); meta["short_url"] = res["short"] and os.path.relpath(res["short"], ROOT)
    json.dump(meta, open(os.path.join(od, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return meta


def build_description(spec, chapters):
    desc = spec["description"]
    if "Chapters\n" in desc:
        head, rest = desc.split("Chapters\n", 1); tail = rest.split("\n\n", 1)[1] if "\n\n" in rest else ""
        desc = head + "Chapters\n" + chapters + "\n\n" + tail
    if spec.get("sources"): desc += "\n\nSources\n" + "\n".join(spec["sources"])
    return desc


def write_queue():
    q = []
    for m in sorted(glob.glob(os.path.join(OUT, "*", "meta.json"))):
        meta = json.load(open(m, encoding="utf-8"))
        if not str(meta.get("video_url", "")).startswith("http"): continue
        q.append(meta)
    json.dump(q, open(os.path.join(OUT, "queue.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("대기열", len(q), "편")


def main(ids):
    if not ids: ids = [os.path.basename(f)[:-5] for f in sorted(glob.glob(os.path.join(HERE, "specs", "*.json"))) if not os.path.exists(os.path.join(OUT, os.path.basename(f)[:-5], "meta.json"))]
    for sid in ids:
        spec = json.load(open(os.path.join(HERE, "specs", sid + ".json"), encoding="utf-8"))
        res = render(sid); publish(sid, res, spec)
    write_queue()


if __name__ == "__main__":
    main(sys.argv[1:])
