"""황제의 밤 편지(롱폼) 렌더러 — 템플릿 엔진 (2026-11-03 파일럿)

사용: python3 longform.py spec.json [--from 초] [--to 초] [--preview]
spec 한 개 = 한 편. 장면(shots)을 순서대로 이어 붙이고, 목소리 길이에 맞춰 장면 길이를 정한다.
매 편 같은 것(템플릿): 영화 비율 검은 띠, 색보정·필름 입자·비네트, 전용 인트로, 장 제목 카드, 구절 손글씨, 개념 카드,
오늘 밤 할 일 카드, 엔딩, 소리 섞기 규칙(목소리 나올 때 음악·공간 소리 자동으로 낮춤, 독백은 막사 울림).
편마다 바뀌는 것: spec 의 shots(그림·영상·대본·효과음 지시)와 제목들.

shot 공통: type(black|video|still|intro|card|tonight|end), dur(최소 길이), voice(이름 또는 목록), pre(목소리 전 여백), post(뒤 여백),
          amb([소리키, 크기]), sfx([[키, 시작초, 크기], ...]), tin("cut"|"dissolve"|"black"), tout("cut"|"black")
still: src, move{zoom:[a,b], pan:[[x0,y0],[x1,y1]]}, flicker, particles(dust|snow|embers), grade(night|modern|memory)
video: src, move(같음), start(원본 시작초) — 장면이 원본보다 길면 천천히 늘려 재생하고 끝 프레임에서 카메라만 계속 움직인다
overlay: {kind: caption|quote|concept, ...}
"""
import json, math, os, subprocess, sys, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

FONTS = "/root/fonts/"
W, H, FPS = 1920, 1080, 30
BAR = 131                      # 2.35:1 검은 띠 (위아래)
GOLD = (201, 164, 92); IVORY = (239, 230, 212)


def font(kind, size):
    f = {"ko": "hahmlet-korean-700-normal.ttf", "ko6": "hahmlet-korean-600-normal.ttf", "en": "cormorant-sc-latin-600-normal.ttf",
         "en5": "cormorant-sc-latin-500-normal.ttf", "ui": "Pretendard-SemiBold.otf", "uim": "Pretendard-Medium.otf"}[kind]
    return ImageFont.truetype(FONTS + f, size)


def dur_of(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)


def ease(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


# ---------- 화면 질감 (템플릿) ----------
class Look:
    def __init__(self):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.vig = np.clip(1.0 - 0.38 * np.clip(d - 0.35, 0, 1) ** 1.6, 0, 1)[..., None].astype(np.float32)
        rng = np.random.default_rng(7)
        self.grain = [cv2.resize(rng.normal(0, 7.5, (H // 2, W // 2)).astype(np.float32), (W, H))[..., None] for _ in range(12)]
        self.n = 0

    def apply(self, img, grade=None):
        f = img.astype(np.float32)
        if grade == "modern":   # 지금 장면: 푸른 회색
            f = f * np.array([1.05, 0.98, 0.88], np.float32)  # BGR
            g = f.mean(axis=2, keepdims=True); f = f * 0.75 + g * 0.25
        elif grade == "memory": # 회상: 따뜻하고 부드럽게
            f = f * np.array([0.85, 1.0, 1.1], np.float32) + 8
        else:                   # 기본: 따뜻한 촛불 톤, 검정은 살짝 들어 올림
            f = f * np.array([0.92, 0.99, 1.06], np.float32)
        f = 10 + f * 0.96
        f = f * self.vig + self.grain[self.n % 12]; self.n += 1
        out = np.clip(f, 0, 255).astype(np.uint8)
        out[:BAR] = 0; out[H - BAR:] = 0
        return out


# ---------- 글자 그리기 ----------
def text_layer(lines, size_kind, size, color, spacing=0, align="center", track=0, shadow=True, width=W, height=None, line_gap=1.35):
    """lines: [str] → RGBA numpy (H×W) 한 장"""
    im = Image.new("RGBA", (width, height or H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fnt = font(size_kind, size)
    def tw(s):
        if not track: return d.textlength(s, font=fnt)
        return sum(d.textlength(c, font=fnt) for c in s) + track * (len(s) - 1)
    total = len(lines) * size * line_gap
    y = ((height or H) - total) / 2 + spacing
    for s in lines:
        w = tw(s); x = (width - w) / 2 if align == "center" else 0
        if shadow:
            sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
            _draw(sd, x, y, s, fnt, (0, 0, 0, 200), track); sh = sh.filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(10)); im.alpha_composite(sh)
        _draw(d, x, y, s, fnt, color + (255,), track)
        y += size * line_gap
    return np.array(im)


def _draw(d, x, y, s, fnt, col, track):
    if not track: d.text((x, y), s, font=fnt, fill=col); return
    for c in s:
        d.text((x, y), c, font=fnt, fill=col); x += d.textlength(c, font=fnt) + track


def blend(base, rgba, alpha=1.0, dx=0, dy=0):
    """base BGR uint8, rgba RGBA uint8 (같은 크기) → 합성"""
    if alpha <= 0: return base
    a = rgba[..., 3:4].astype(np.float32) / 255.0 * alpha
    rgb = rgba[..., :3][..., ::-1].astype(np.float32)
    if dx or dy:
        M = np.float32([[1, 0, dx], [0, 1, dy]]); a = cv2.warpAffine(a, M, (W, H))[..., None]; rgb = cv2.warpAffine(rgb, M, (W, H))
    return (base.astype(np.float32) * (1 - a) + rgb * a).astype(np.uint8)


# ---------- 화면 소스 ----------
class Still:
    def __init__(self, path, move, scale=1.25):
        img = cv2.imread(path); h, w = img.shape[:2]
        k = max(W / w, H / h) * scale
        self.img = cv2.resize(img, (int(w * k), int(h * k)), interpolation=cv2.INTER_LANCZOS4)
        self.move = move or {}

    def frame(self, p):
        z0, z1 = self.move.get("zoom", [1.0, 1.08]); (x0, y0), (x1, y1) = self.move.get("pan", [[0, 0], [0, 0]])
        e = ease(p) if self.move.get("ease", True) else p
        z = z0 + (z1 - z0) * e; px = x0 + (x1 - x0) * e; py = y0 + (y1 - y0) * e
        sh, sw = self.img.shape[:2]
        base = max(W / sw, H / sh)        # 이 배율이면 화면을 딱 채움
        s = base * z
        cx, cy = sw / 2 + px * sw, sh / 2 + py * sh
        M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
        return cv2.warpAffine(self.img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


class Clip:
    def __init__(self, path, move, start=0.0):
        cap = cv2.VideoCapture(path); self.fr = []
        fps = cap.get(cv2.CAP_PROP_FPS) or 24
        skip = int(start * fps); i = 0
        while True:
            ok, f = cap.read()
            if not ok: break
            if i >= skip: self.fr.append(f)
            i += 1
        self.src_fps = fps; self.move = move or {"zoom": [1.0, 1.05]}
        h, w = self.fr[0].shape[:2]; self.k = max(W / w, H / h)

    def frame(self, p, t, dur):
        n = len(self.fr); length = n / self.src_fps
        rate = max(min(length / dur, 1.0), 0.45)         # 장면이 길면 느리게 (최대 0.45배속)
        idx = min(int(t * rate * self.src_fps), n - 1)
        f = self.fr[idx]
        z0, z1 = self.move.get("zoom", [1.0, 1.05]); (x0, y0), (x1, y1) = self.move.get("pan", [[0, 0], [0, 0]])
        e = ease(p); z = z0 + (z1 - z0) * e
        s = self.k * z; h, w = f.shape[:2]
        cx, cy = w / 2 + (x0 + (x1 - x0) * e) * w, h / 2 + (y0 + (y1 - y0) * e) * h
        M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
        return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


class Particles:
    def __init__(self, kind, n=70, seed=3):
        r = random.Random(seed); self.kind = kind
        self.p = [(r.random() * W, r.random() * H, r.uniform(0.6, 2.6), r.uniform(0.2, 1.0), r.random() * 6.28) for _ in range(n)]

    def draw(self, img, t):
        layer = np.zeros((H, W, 3), np.float32)
        for (x, y, s, b, ph) in self.p:
            if self.kind == "snow":
                xx = (x + t * 40 * s + 20 * math.sin(t + ph)) % W; yy = (y + t * 90 * s) % H; c = (230, 230, 235)
            elif self.kind == "embers":
                xx = (x + 15 * math.sin(t * 0.7 + ph)) % W; yy = (y - t * 35 * s) % H; c = (60, 140, 255)
            else:
                xx = (x + 12 * math.sin(t * 0.3 + ph)) % W; yy = (y - t * 6 * s + 8 * math.cos(t * 0.4 + ph)) % H; c = (150, 200, 240)
            cv2.circle(layer, (int(xx), int(yy)), max(1, int(s)), [v * b * (0.6 + 0.4 * math.sin(t * 2 + ph)) for v in c], -1, cv2.LINE_AA)
        layer = cv2.GaussianBlur(layer, (0, 0), 1.6)
        return np.clip(img.astype(np.float32) + layer * 0.55, 0, 255).astype(np.uint8)


# ---------- 템플릿 카드 ----------
def coin_gold(path):
    c = Image.open(path).convert("L").resize((360, 360), Image.LANCZOS); a = np.array(c).astype(np.float32) / 255.0
    rgb = np.stack([a * GOLD[0] * 1.15, a * GOLD[1] * 1.15, a * GOLD[2] * 1.1], -1)
    alpha = np.clip((a - 0.08) * 1.6, 0, 1) * 255
    yy, xx = np.mgrid[0:360, 0:360]; m = ((xx - 180) ** 2 + (yy - 180) ** 2) <= 178 ** 2
    alpha = alpha * m
    return np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8)


class Intro:
    """전용 인트로 12초 (매 편 같음, 편 제목만 바뀜)"""
    def __init__(self, spec):
        self.coin = coin_gold(spec["logo"]); self.title = spec.get("ep_title", "")
        self.kicker = spec.get("ep_kicker", "")
        self.en = text_layer(["THE EMPEROR'S DIARY"], "en", 74, GOLD, track=14, shadow=False, height=120)
        self.ko = text_layer(["황제의 일기"], "ko6", 56, IVORY, shadow=False, height=80)
        self.t_kick = text_layer([self.kicker], "ui", 40, GOLD, track=6, shadow=False, height=60)
        self.t_title = text_layer([self.title], "ko", 78, IVORY, height=130)
        self.dust = Particles("embers", 90, 11)
        self.dur = 12.0

    def frame(self, t):
        img = np.zeros((H, W, 3), np.uint8)
        cx, cy, r = W // 2, 420, 182
        if 0.8 <= t < 10.2:
            # 금빛 잉크 선이 원을 그림 (0.8~2.6초)
            p = ease((t - 0.8) / 1.8); ang = 360 * p
            glow = np.zeros((H, W, 3), np.uint8)
            cv2.ellipse(glow, (cx, cy), (r, r), -90, 0, ang, (92, 164, 201), 3, cv2.LINE_AA)
            if p < 1:
                hx = int(cx + r * math.cos(math.radians(ang - 90))); hy = int(cy + r * math.sin(math.radians(ang - 90)))
                cv2.circle(glow, (hx, hy), 7, (200, 235, 255), -1, cv2.LINE_AA)
            g = cv2.GaussianBlur(glow, (0, 0), 6)
            img = cv2.add(img, cv2.addWeighted(glow, 1.0, g, 1.4, 0))
        if t >= 2.4:
            # 주화가 원 안에서 떠오름 + 빛 한 줄기가 훑고 지나감
            a = ease((t - 2.4) / 1.4) * (1 - ease((t - 9.6) / 0.6))
            layer = np.zeros((H, W, 4), np.uint8); cs = self.coin.shape[0]
            layer[cy - cs // 2:cy + cs // 2, cx - cs // 2:cx + cs // 2] = self.coin
            if 3.0 < t < 4.6:
                sw = int((t - 3.0) / 1.6 * (cs + 200)) - 100
                band = np.zeros((cs, cs), np.float32); cv2.line(band, (sw, 0), (sw - 120, cs), 1.0, 40); band = cv2.GaussianBlur(band, (0, 0), 18)
                sub = layer[cy - cs // 2:cy + cs // 2, cx - cs // 2:cx + cs // 2, :3].astype(np.float32)
                sub = np.clip(sub + band[..., None] * 140 * (sub > 10), 0, 255); layer[cy - cs // 2:cy + cs // 2, cx - cs // 2:cx + cs // 2, :3] = sub.astype(np.uint8)
            shake = 6 * math.exp(-(t - 4.0) * 18) * math.sin(t * 90) if t >= 4.0 else 0
            img = blend(img, layer, a, dx=shake, dy=shake * 0.6)
        if t >= 4.0:
            img = self.dust.draw(img, t - 4.0) if t < 10.0 else img
        if t >= 5.0:
            a = ease((t - 5.0) / 0.9) * (1 - ease((t - 9.6) / 0.6))
            en = self.en.copy()
            if 5.4 < t < 7.4:   # 글자 위를 빛이 훑음
                sw = int((t - 5.4) / 2.0 * (W + 400)) - 200
                band = np.zeros((en.shape[0], W), np.float32); cv2.line(band, (sw, 0), (sw - 60, en.shape[0]), 1.0, 70); band = cv2.GaussianBlur(band, (0, 0), 25)
                en[..., :3] = np.clip(en[..., :3].astype(np.float32) + band[..., None] * 120, 0, 255).astype(np.uint8)
            layer = np.zeros((H, W, 4), np.uint8); layer[620:620 + en.shape[0]] = en
            img = blend(img, layer, a)
        if t >= 7.0:
            a = ease((t - 7.0) / 0.9) * (1 - ease((t - 9.6) / 0.6))
            layer = np.zeros((H, W, 4), np.uint8); layer[735:735 + self.ko.shape[0]] = self.ko
            img = blend(img, layer, a)
        if t >= 10.0:   # 편 제목 카드
            a = ease((t - 10.0) / 0.6) * (1 - ease((t - 11.5) / 0.5))
            layer = np.zeros((H, W, 4), np.uint8)
            layer[420:420 + self.t_kick.shape[0]] = self.t_kick; layer[485:485 + self.t_title.shape[0]] = self.t_title
            img = blend(img, layer, a)
        return img


def end_frame(s, t, dur, cache, logo):
    """엔딩: 주화 + THE EMPEROR'S DIARY + 황제의 일기 + 슬로건 (매 편 같음)"""
    if "end" not in cache:
        cache["end"] = (coin_gold(logo), text_layer(["THE EMPEROR'S DIARY"], "en", 60, GOLD, track=12, shadow=False, height=100),
                        text_layer([s.get("slogan", "매일 밤, 황제처럼 생각하라")], "ko6", 52, IVORY, shadow=False, height=90))
    coin, en, sl = cache["end"]
    img = np.zeros((H, W, 3), np.uint8); a = ease(t / 1.0) * (1 - ease((t - dur + 0.8) / 0.8))
    lay = np.zeros((H, W, 4), np.uint8); cs = coin.shape[0]; cy = 400
    lay[cy - cs // 2:cy + cs // 2, W // 2 - cs // 2:W // 2 + cs // 2] = coin
    img = blend(img, lay, a)
    l2 = np.zeros((H, W, 4), np.uint8); l2[610:710] = en; img = blend(img, l2, a)
    a3 = ease((t - 0.8) / 0.9) * (1 - ease((t - dur + 0.8) / 0.8)); l3 = np.zeros((H, W, 4), np.uint8); l3[720:810] = sl
    return blend(img, l3, a3)


def card_frame(spec_shot, t, dur, cache):
    """장 제목 카드: 검은 바탕, 금색 로마 숫자, 제목"""
    if "card" not in cache:
        cache["card"] = (text_layer([spec_shot["num"]], "en", 120, GOLD, shadow=False, height=170),
                         text_layer([spec_shot["title"]], "ko", 64, IVORY, shadow=False, height=110))
    num, ttl = cache["card"]
    img = np.zeros((H, W, 3), np.uint8)
    a = ease(t / 0.8) * (1 - ease((t - dur + 0.7) / 0.7))
    layer = np.zeros((H, W, 4), np.uint8); layer[330:330 + num.shape[0]] = num; layer[520:520 + ttl.shape[0]] = ttl
    img = blend(img, layer, a)
    # 가는 금색 선
    x = int(W / 2 - 60 * ease(t / 1.0)); cv2.line(img, (x, 505), (W - x, 505), (92, 164, 201), 1, cv2.LINE_AA)
    return img


def tonight_frame(s, t, dur, cache):
    if "tn" not in cache:
        cache["tn"] = (text_layer(["오늘 밤 해 볼 일"], "ui", 34, GOLD, track=3, shadow=False, height=70),
                       text_layer(s["lines"], "ko6", 60, IVORY, shadow=False, height=260))
    k, body = cache["tn"]
    img = np.zeros((H, W, 3), np.uint8) + np.uint8(8)
    a = ease(t / 0.8) * (1 - ease((t - dur + 0.6) / 0.6))
    layer = np.zeros((H, W, 4), np.uint8); layer[330:400] = k; layer[420:680] = body
    return blend(img, layer, a)


# ---------- 덧씌우는 글자 (자막·구절·개념) ----------
def overlay(img, ov, t, dur, cache, key):
    k = ov["kind"]
    if k == "caption":   # 작은 장소·연도 자막, 왼쪽 아래
        if key not in cache: cache[key] = text_layer([ov["text"]], "ui", 34, IVORY, track=2, width=W, height=60)
        a = ease((t - ov.get("at", 0.3)) / 0.6) * (1 - ease((t - dur + 0.5) / 0.5))
        lay = np.zeros((H, W, 4), np.uint8); tl = cache[key]
        # 왼쪽 정렬처럼 보이게 가운데 정렬 레이어를 옮긴다
        lay[H - BAR - 120:H - BAR - 60] = tl
        return blend(img, lay, a, dx=-W // 2 + 380)
    if k == "quote":     # 일기 손글씨: 글자가 앞에서부터 차례로 써짐
        if key not in cache:
            ink = ov.get("ink")
            cache[key] = (text_layer(ov["lines"], "ko6", ov.get("size", 62), (52, 36, 22) if ink else (240, 226, 196), height=300, line_gap=1.45, shadow=not ink),
                          text_layer([ov["src"]], "ui", 34, (70, 46, 22) if ink else GOLD, track=2, shadow=False, height=50))
        q, src = cache[key]
        p0, p1 = ov.get("from", 0.5), ov.get("to", 0.92)
        p = (t / dur - p0) / (p1 - p0)
        if p <= 0: return img
        # 글자를 줄 순서대로 왼→오 쓸어 드러냄
        n = len(ov["lines"]); lay = np.zeros((H, W, 4), np.uint8); top = ov.get("top", 250)
        qq = q.copy(); band_h = q.shape[0] / n
        for i in range(n):
            pi = min(max(p * n - i, 0), 1)
            y0, y1 = int(i * band_h), int((i + 1) * band_h)
            xs = np.where(q[y0:y1, :, 3].max(axis=0) > 0)[0]
            if not len(xs): continue
            edge = xs[0] + (xs[-1] - xs[0] + 40) * pi
            ramp = np.clip((edge - np.arange(W)) / 40.0, 0, 1)
            qq[y0:y1, :, 3] = (q[y0:y1, :, 3] * ramp[None, :]).astype(np.uint8)
        lay[top:top + q.shape[0]] = qq
        out = blend(img, lay, 1 - ease((t - dur + 0.4) / 0.4), dx=ov.get("dx", 0))
        if p >= 1:
            a2 = ease((p - 1) * 3) * (1 - ease((t - dur + 0.4) / 0.4)); l2 = np.zeros((H, W, 4), np.uint8); l2[top + q.shape[0] + 10:top + q.shape[0] + 60] = src
            out = blend(out, l2, a2, dx=ov.get("dx", 0))
        return out
    if k == "concept":   # 개념 카드: 화면 가운데 아래, 3~4초
        if key not in cache:
            cache[key] = (text_layer([ov["kicker"]], "ui", 36, GOLD, track=3, shadow=False, height=56),
                          text_layer(ov["lines"], "ko", 64, IVORY, height=200))
        kk, body = cache[key]
        a = ease((t - ov["at"]) / 0.6) * (1 - ease((t - ov["at"] - ov.get("len", 4.0)) / 0.6))
        if a <= 0: return img
        dark = (img.astype(np.float32) * (1 - 0.72 * a)).astype(np.uint8)
        lay = np.zeros((H, W, 4), np.uint8); lay[380:436] = kk; lay[450:650] = body
        return blend(dark, lay, a)
    return img


# ---------- 본체 ----------
def build(spec_path, t_from=0.0, t_to=None, preview=False, audio_only=False):
    S = json.load(open(spec_path)); base = os.path.dirname(os.path.abspath(spec_path))
    root = os.path.abspath(os.path.join(base, S.get("root", "../../..")))
    P = lambda p: p if os.path.isabs(p) else os.path.join(root, p)
    vdir = P(S["voice_dir"]); gdir = P(S["gen_dir"])
    vfile = lambda n: os.path.join(vdir, S["voice_files"][n])
    # 1) 장면 길이 정하기 (목소리 길이 + 여백)
    t = 0.0; plan = []
    for i, s in enumerate(S["shots"]):
        vs = s.get("voice"); vs = [vs] if isinstance(vs, str) else (vs or [])
        pre = s.get("pre", 0.4); post = s.get("post", 0.6); gap = s.get("gap", 0.5)
        vt, cur = [], pre
        for v in vs:
            d = dur_of(vfile(v)); vt.append((v, cur, d)); cur += d + gap
        need = (cur - gap + post) if vs else 0
        d = max(s.get("dur", 0), need)
        if s["type"] == "intro": d = 12.0
        if s.get("fixed"): d = s["dur"]
        plan.append({"s": s, "t0": t, "dur": d, "voices": [(v, t + a, dd) for v, a, dd in vt]}); t += d
    total = t
    print(f"총 길이 {total:.1f}초, 장면 {len(plan)}개", flush=True)
    json.dump([{"i": i, "type": p["s"]["type"], "t0": round(p["t0"], 2), "dur": round(p["dur"], 2), "src": p["s"].get("src", "")} for i, p in enumerate(plan)],
              open(os.path.join(base, f"plan_{S['id']}.json"), "w"), ensure_ascii=False, indent=0)
    t_to = min(t_to or total, total)
    out_dir = P(S.get("out_dir", "_long")); os.makedirs(out_dir, exist_ok=True)
    tag = S["id"] + ("_prev" if preview else "")
    vid_path = os.path.join(out_dir, f"{tag}_v.mp4")
    # 2) 화면
    look = Look(); intro = None; last = None
    scale = 0.5 if preview else 1.0
    if audio_only and os.path.exists(vid_path): plan_v = []
    else: plan_v = plan
    enc = None if not plan_v else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{int(W*scale)}x{int(H*scale)}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18" if not preview else "26", "-pix_fmt", "yuv420p", vid_path], stdin=subprocess.PIPE)
    for pi, p in enumerate(plan_v):
        s = p["s"]; t0, d = p["t0"], p["dur"]
        if t0 + d <= t_from or t0 >= t_to: continue
        cache = {}; src = None
        if s["type"] == "still": src = Still(os.path.join(gdir, s["src"] + ".jpeg"), s.get("move"))
        elif s["type"] == "video": src = Clip(os.path.join(gdir, s["src"] + ".mp4"), s.get("move"), s.get("start", 0))
        elif s["type"] == "intro": intro = intro or Intro({**S["intro"], "logo": P(S["intro"]["logo"])})
        parts = Particles(s["particles"]) if s.get("particles") else None
        nfr = int(round(d * FPS)); first = None
        for k in range(nfr):
            tt = k / FPS; gt = t0 + tt
            if gt < t_from or gt >= t_to: continue
            prog = tt / d
            if s["type"] == "black": img = np.zeros((H, W, 3), np.uint8)
            elif s["type"] == "intro": img = intro.frame(tt)
            elif s["type"] == "card": img = card_frame(s, tt, d, cache)
            elif s["type"] == "end": img = end_frame(s, tt, d, cache, P(S["intro"]["logo"]))
            elif s["type"] == "tonight": img = tonight_frame(s, tt, d, cache)
            elif s["type"] == "still": img = src.frame(prog)
            elif s["type"] == "video": img = src.frame(prog, tt, d)
            if s.get("flicker") and s["type"] in ("still", "video"):
                fl = 1 + 0.035 * math.sin(tt * 7.1) + 0.025 * math.sin(tt * 13.7 + 1.3)
                img = np.clip(img.astype(np.float32) * fl, 0, 255).astype(np.uint8)
            if parts: img = parts.draw(img, tt)
            for oi, ov in enumerate(s.get("overlays", [])): img = overlay(img, ov, tt, d, cache, f"ov{oi}")
            if s["type"] in ("still", "video", "black"): img = look.apply(img, s.get("grade"))
            else: img = _bars(img)
            # 들어오고 나가기
            tin, tout = s.get("tin", "cut"), s.get("tout", "cut")
            if tin == "black": img = (img.astype(np.float32) * ease(tt / s.get("fin", 0.6))).astype(np.uint8)
            if tin == "dissolve" and last is not None and tt < 0.6: a = ease(tt / 0.6); img = cv2.addWeighted(last, 1 - a, img, a, 0)
            if tout == "black": img = (img.astype(np.float32) * (1 - ease((tt - d + s.get("fout", 0.6)) / s.get("fout", 0.6)))).astype(np.uint8)
            if first is None: first = img
            frame = cv2.resize(img, (int(W * scale), int(H * scale)), interpolation=cv2.INTER_AREA) if preview else img
            enc.stdin.write(frame.tobytes()); lastk = img
        last = lastk if nfr else last
        print(f"  장면 {pi} {s['type']} {s.get('src','')} {d:.1f}초 완료", flush=True)
    if enc: enc.stdin.close(); enc.wait()
    # 3) 소리
    for m in S.get("music", []):
        if "at_shot" in m: m["at"] = plan[m["at_shot"]]["t0"] + m.get("offset", 0)
    mix_audio(S, plan, total, t_from, t_to, vfile, P, out_dir, tag)
    final = os.path.join(out_dir, f"{tag}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid_path, "-i", os.path.join(out_dir, f"{tag}_a.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart", final], check=True)
    print("완성", final, flush=True)
    return final


def _bars(img):
    img = img.copy(); img[:BAR] = 0; img[H - BAR:] = 0; return img


def mix_audio(S, plan, total, t_from, t_to, vfile, P, out_dir, tag):
    """목소리·공간 소리·효과음·음악을 한 번에 섞는다. 음악·공간 소리는 목소리에 맞춰 자동으로 낮아진다."""
    sfx_dir = P(S["sfx_dir"]); mus_dir = P(S["music_dir"])
    ins, flt, vo, bg = [], [], [], []
    def add(path, at, vol, extra=""):
        at -= t_from
        if at + dur_of(path) < 0 or at > t_to - t_from: return None
        i = len(ins) // 2; trim = ""
        if at < 0: trim = f"atrim=start={-at},asetpts=PTS-STARTPTS,"; at = 0
        ins.extend(["-i", path]); lab = f"a{i}"
        flt.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,{trim}{extra}volume={vol},adelay={int(at*1000)}|{int(at*1000)}[{lab}]")
        return lab
    mono = set(S.get("monologue_voices", []))
    for p in plan:
        for v, at, d in p["voices"]:
            fx = S.get("monologue_fx", "highpass=f=60,") if v in mono else "highpass=f=60,"   # 2026-11-03 대표: 황제(명일)는 생 목소리 그대로
            lab = add(vfile(v), at, S.get("voice_vol", 1.0) * (1.1 if v in mono else 1.0), fx)
            if lab: vo.append(lab)
        s = p["s"]
        if s.get("amb"):
            key, vol = s["amb"]; path = os.path.join(sfx_dir, key)
            L = dur_of(path); d = p["dur"]
            loop = f"aloop=loop={int(d // max(L, 0.1)) + 1}:size={int(48000 * L)}," if L < d else ""
            lab = add(path, p["t0"], vol, f"{loop}atrim=0:{d},afade=t=in:d=0.8,afade=t=out:st={max(d-0.9,0)}:d=0.9,")
            if lab: bg.append(lab)
        for key, at, vol in s.get("sfx", []):
            lab = add(os.path.join(sfx_dir, key), p["t0"] + at, vol)
            if lab: bg.append(lab)   # 효과음은 덕킹하지 않는 쪽이 낫지만 단순하게 함께 둔다
    for m in S.get("music", []):
        path = os.path.join(mus_dir, m["file"]); length = m.get("len", 60)
        lab = add(path, m["at"], m["vol"], f"atrim=start={m.get('start',0)},asetpts=PTS-STARTPTS,atrim=0:{length},afade=t=in:d={m.get('fin',2)},afade=t=out:st={max(length-m.get('fout',3),0)}:d={m.get('fout',3)},")
        if lab: bg.append(lab)
    L = t_to - t_from
    fc = ";".join(flt)
    fc += f";{''.join('['+x+']' for x in vo)}amix=inputs={len(vo)}:normalize=0,asplit=2[vo1][vo2]"
    fc += f";{''.join('['+x+']' for x in bg)}amix=inputs={len(bg)}:normalize=0[bgm]"
    fc += ";[bgm][vo2]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600:makeup=1[duck]"
    fc += f";[vo1][duck]amix=inputs=2:normalize=0,apad=whole_dur={L},atrim=0:{L},loudnorm=I=-16:TP=-1.5:LRA=11[out]"
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-ac", "2", os.path.join(out_dir, f"{tag}_a.wav")]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    a = sys.argv[1:]; spec = a[0]
    tf = float(a[a.index("--from") + 1]) if "--from" in a else 0.0
    tt = float(a[a.index("--to") + 1]) if "--to" in a else None
    build(spec, tf, tt, "--preview" in a, "--audio-only" in a)
