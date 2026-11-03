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
         "en5": "cormorant-sc-latin-500-normal.ttf", "ui": "Pretendard-SemiBold.otf", "uim": "Pretendard-Medium.otf",
         "it": "cormorant-garamond-latin-500-italic.ttf", "script": "PinyonScript-Regular.ttf"}[kind]
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


class WriteClip(Clip):
    """펜으로 쓰는 장면: 종이 위 영어 필기체가 펜 끝을 따라 써진다 (카메라 움직임은 특징점 추적, 펜 끝은 템플릿 추적)
    write = {quad: 글씨 줄 영역 네 꼭짓점(첫 프레임 기준), tip0: 첫 프레임 펜 끝 [x,y], lines: [이미 써 있는 줄...], line: 지금 쓰는 줄,
             size: 글자 크기, ink: [r,g,b], lead: 펜 끝보다 몇 px 앞까지 보일지}"""
    def __init__(self, path, move, start, wr):
        super().__init__(path, move, start)
        self.wr = wr; fr = self.fr; n = len(fr); h, w = fr[0].shape[:2]
        gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in fr]
        quad = np.float32(wr["quad"]); tx, ty = wr["tip0"]
        # 카메라 추적 (손·펜 쪽은 빼고 종이 위 특징점)
        m = np.zeros((h, w), np.uint8); cv2.fillPoly(m, [np.int32(wr.get("paper", wr["quad"]))], 255)
        cv2.rectangle(m, (int(tx) - 40, 0), (w, int(ty) + 60), 0, -1)
        acc = np.eye(3); Hs = [acc.copy()]; prev = gray[0]; pts = cv2.goodFeaturesToTrack(prev, 400, 0.01, 8, mask=m)
        for i in range(1, n):
            ok = pts is not None and len(pts) >= 8
            if ok:
                nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, gray[i], pts, None, winSize=(21, 21), maxLevel=3)
                g0, g1 = pts[st == 1], nxt[st == 1]
                Hm = cv2.findHomography(g0, g1, cv2.RANSAC, 3.0)[0] if len(g0) >= 8 else None
                if Hm is not None: acc = Hm @ acc
                pts = g1.reshape(-1, 1, 2) if len(g1) >= 120 else cv2.goodFeaturesToTrack(gray[i], 400, 0.01, 8, mask=cv2.warpPerspective(m, acc, (w, h)))
            Hs.append(acc.copy()); prev = gray[i]
        self.Hs = Hs
        # 펜 끝 추적
        r = wr.get("tpl", [12, 60, 60, 8])  # 왼, 위, 오른, 아래 여유
        tpl = gray[0][int(ty) - r[1]:int(ty) + r[3], int(tx) - r[0]:int(tx) + r[2]]; tips = [(tx, ty)]
        for i in range(1, n):
            px, py = tips[-1]; x0, y0 = int(px) - 90, int(py) - 90
            roi = gray[i][max(y0, 0):y0 + 200 + r[1], max(x0, 0):x0 + 200 + r[2]]
            res = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED); _, _, _, loc = cv2.minMaxLoc(res)
            tips.append((max(x0, 0) + loc[0] + r[0], max(y0, 0) + loc[1] + r[1]))
        tips = np.array(tips, float); k = 5
        self.tips = np.array([tips[max(0, i - k):i + k + 1].mean(0) for i in range(n)])
        if wr.get("clean"):   # 영상 모델이 그린 엉뚱한 잉크 자국 지우기: 펜 끝 아래·왼쪽에서 첫 프레임보다 어두워진 곳을 첫 프레임 종이로 되돌림
            f0 = fr[0]
            for i in range(1, n):
                f0w = cv2.warpPerspective(f0, Hs[i], (w, h), borderMode=cv2.BORDER_REPLICATE)
                d = cv2.cvtColor(f0w, cv2.COLOR_BGR2GRAY).astype(np.int16) - gray[i].astype(np.int16)
                tx_, ty_ = self.tips[i]
                reg = np.zeros((h, w), np.uint8); cv2.rectangle(reg, (0, int(ty_) - 48), (int(tx_) - 6, h), 255, -1)
                cv2.rectangle(reg, (int(tx_) - 6, int(ty_) - 4), (int(tx_) + 8, h), 255, -1)
                m2 = ((d > 18) & (reg > 0)).astype(np.uint8) * 255
                m2 = cv2.dilate(m2, np.ones((5, 5), np.uint8)); m2 = cv2.GaussianBlur(m2, (0, 0), 1.5)[..., None] / 255.0
                fr[i] = (fr[i] * (1 - m2) + f0w * m2).astype(np.uint8)
        # 글씨 평면
        PW, PH = 1600, 240 * (len(wr.get("lines", [])) + 1)
        f = ImageFont.truetype(FONTS + "PinyonScript-Regular.ttf", wr.get("size", 150))
        im = Image.new("L", (PW, PH), 0); d = ImageDraw.Draw(im); yb = 190
        for ln in wr.get("lines", []): d.text((10, yb), ln, font=f, fill=255, anchor="ls"); yb += 240
        self.static = np.array(im).astype(np.float32) / 255.0
        im2 = Image.new("L", (PW, PH), 0); ImageDraw.Draw(im2).text((10, yb), wr["line"], font=f, fill=255, anchor="ls")
        self.wline = np.array(im2).astype(np.float32) / 255.0
        self.line_w = d.textlength(wr["line"], font=f) + 10
        self.Hq = cv2.getPerspectiveTransform(np.float32([[0, 0], [PW, 0], [PW, PH], [0, PH]]), quad)
        self.PW, self.PH, self.wh = PW, PH, (w, h)
        self.ink = np.array(wr.get("ink", [36, 24, 14])[::-1], np.float32)
        # 펜 끝 → 글씨 평면 x 좌표 (앞으로만 나아가게)
        us = []
        for i in range(n):
            p = np.array([self.tips[i][0], self.tips[i][1], 1.0]); q = np.linalg.inv(Hs[i] @ self.Hq) @ p; us.append(q[0] / q[2])
        us = np.maximum.accumulate(np.array(us)); u0 = us[0]
        self.us = us - u0 + wr.get("lead", 30)

    def frame(self, p, t, dur):
        n = len(self.fr); length = n / self.src_fps
        rate = max(min(length / dur, 1.0), 0.45)
        idx = min(int(t * rate * self.src_fps), n - 1)
        f = self.fr[idx].astype(np.float32); w, h = self.wh
        u = self.us[idx]; reveal = (np.arange(self.PW)[None, :] < u).astype(np.float32)
        reveal = cv2.GaussianBlur(reveal, (0, 0), 6) if u < self.line_w else np.ones_like(reveal)
        a = np.clip(self.static + self.wline * reveal, 0, 1)
        a = cv2.GaussianBlur(a, (0, 0), 0.9)
        aw = cv2.warpPerspective(a, self.Hs[idx] @ self.Hq, (w, h))
        # 손·펜에 가려지는 곳은 글씨를 빼기 (종이는 밝고 손·펜은 어둡다)
        g = cv2.GaussianBlur(cv2.cvtColor(self.fr[idx], cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 2.5)
        lo, hi = self.wr.get("paper_lv", [105, 135])
        vis = np.clip((g - lo) / (hi - lo), 0, 1)
        vis = cv2.erode(vis, np.ones((7, 7), np.uint8))
        aw = (aw * vis)[..., None] * self.wr.get("strength", 0.9)
        f = f * (1 - aw) + (f * 0.25 + self.ink * 0.75) * aw
        self_fr, self.fr[idx] = self.fr[idx], f.astype(np.uint8)
        out = Clip.frame(self, p, t, dur); self.fr[idx] = self_fr
        return out


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
    """장 제목 카드 (템플릿): CHAPTER + 로마 숫자, 빛나며 길어지는 금색 선, 한글 제목, 영어 부제, 금빛 먼지, 천천히 다가오는 카메라"""
    if "card" not in cache:
        cache["card"] = (text_layer(["CHAPTER"], "en", 38, GOLD, track=16, shadow=False, height=60),
                         text_layer([spec_shot["num"]], "en", 128, GOLD, shadow=False, height=170),
                         text_layer([spec_shot["title"]], "ko", 66, IVORY, height=110),
                         text_layer([spec_shot.get("en", "")], "it", 44, (205, 192, 168), shadow=False, height=70),
                         Particles("embers", 60, 21))
    k, num, ttl, en, dust = cache["card"]
    out_a = 1 - ease((t - dur + 0.7) / 0.7)
    img = np.zeros((H, W, 3), np.uint8)
    # 아주 옅은 따뜻한 빛 웅덩이
    if "glow" not in cache:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); g = np.exp(-(((xx - W / 2) / 700) ** 2 + ((yy - 520) / 330) ** 2))
        cache["glow"] = (g[..., None] * np.array([18, 30, 44], np.float32)).astype(np.float32)
    img = np.clip(img + cache["glow"] * out_a, 0, 255).astype(np.uint8)
    lay = np.zeros((H, W, 4), np.uint8)
    lay[262:322] = k; lay[318:488] = num
    img = blend(img, lay, ease(t / 0.9) * out_a)
    # 금색 선: 가운데서 양옆으로 길어지고, 빛이 한 번 훑고 지나감
    L = int(380 * ease((t - 0.3) / 1.4)); y = 512
    if L > 2:
        line = np.zeros((H, W, 3), np.uint8)
        cv2.line(line, (W // 2 - L, y), (W // 2 + L, y), (92, 164, 201), 2, cv2.LINE_AA)
        cv2.circle(line, (W // 2 - L, y), 3, (140, 200, 235), -1, cv2.LINE_AA); cv2.circle(line, (W // 2 + L, y), 3, (140, 200, 235), -1, cv2.LINE_AA)
        glow = cv2.GaussianBlur(line, (0, 0), 7)
        sweep = np.zeros((H, W, 3), np.uint8)
        sx = int(W / 2 - 420 + 840 * ease((t - 1.2) / 1.2))
        if 1.2 < t < 2.6: cv2.circle(sweep, (sx, y), 26, (170, 220, 255), -1); sweep = cv2.GaussianBlur(sweep, (0, 0), 14)
        img = cv2.add(img, (cv2.addWeighted(cv2.addWeighted(line, 1.0, glow, 1.6, 0), 1.0, sweep, 0.9, 0).astype(np.float32) * out_a).astype(np.uint8))
    l2 = np.zeros((H, W, 4), np.uint8); l2[540:650] = ttl
    img = blend(img, l2, ease((t - 0.7) / 0.9) * out_a, dy=12 * (1 - ease((t - 0.7) / 0.9)))
    if spec_shot.get("en"):
        l3 = np.zeros((H, W, 4), np.uint8); l3[655:725] = en
        img = blend(img, l3, ease((t - 1.3) / 1.0) * out_a)
    img = dust.draw(img, t)
    # 천천히 다가오는 카메라
    z = 1.0 + 0.035 * ease(t / dur); M = np.float32([[z, 0, W / 2 * (1 - z)], [0, z, H / 2 * (1 - z)]])
    return cv2.warpAffine(img, M, (W, H))


def tonight_frame(s, t, dur, cache):
    if "tn" not in cache:
        cache["tn"] = (text_layer(["FOR TONIGHT  ·  오늘 밤 해 볼 일"], "ui", 32, GOLD, track=3, shadow=False, height=70),
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
                          text_layer(ov["lines"], "ko", 64, IVORY, height=200),
                          text_layer([ov.get("en", "")], "it", 42, (205, 192, 168), shadow=False, height=64))
        kk, body, en = cache[key]
        a = ease((t - ov["at"]) / 0.6) * (1 - ease((t - ov["at"] - ov.get("len", 4.0)) / 0.6))
        if a <= 0: return img
        dark = (img.astype(np.float32) * (1 - 0.72 * a)).astype(np.uint8)
        lay = np.zeros((H, W, 4), np.uint8); lay[370:426] = kk; lay[440:640] = body
        if ov.get("en"): lay[640:704] = en
        return blend(dark, lay, a)
    return img


# ---------- 자막 (템플릿: 쇼츠와 같은 방식, 강조 문장만 크게) ----------
def speech_bounds(path, n):
    """음성 파일 안 문장 경계: 긴 쉼 n-1개를 골라 [(시작, 끝)] n개를 돌려준다"""
    L = dur_of(path)
    if n <= 1: return [(0.0, L)]
    out = subprocess.run(["ffmpeg", "-i", path, "-af", "silencedetect=noise=-38dB:d=0.18", "-f", "null", "-"], capture_output=True, text=True).stderr
    import re
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]; en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    gaps = [(b - a, a, b) for a, b in zip(st, en) if 0.15 < a and b < L - 0.1]
    gaps = sorted(sorted(gaps, reverse=True)[:n - 1], key=lambda g: g[1])
    if len(gaps) < n - 1:   # 쉼을 못 찾으면 글자 수 비율로
        return None
    pts = [0.0] + [g[1] for g in gaps]; ends = [g[1] for g in gaps] + [L]
    starts = [0.0] + [g[2] for g in gaps]
    return list(zip(starts, ends))


def wrap_ko(text, fnt, maxw):
    d = ImageDraw.Draw(Image.new("L", (10, 10))); words = text.split(" "); lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) > maxw and cur: lines.append(cur); cur = w
        else: cur = t
    if cur: lines.append(cur)
    return lines


def caption_layer(text, kind, cache):
    key = (text, kind)
    if key in cache: return cache[key]
    if kind == "emph":
        f = font("ko", 72); lines = wrap_ko(text, f, 1400)
        lay = text_layer(lines, "ko", 72, (240, 222, 178), height=110 * len(lines) + 40, line_gap=1.4)
    else:
        kk, sz, col = ("ko6", 46, (246, 238, 222)) if kind == "mono" else ("ui", 44, (255, 255, 255))
        lines = wrap_ko(text, font(kk, sz), 1500)
        lay = text_layer(lines, kk, sz, col, height=int(sz * 1.45 * len(lines)) + 30, line_gap=1.4)
    cache[key] = lay; return lay


def draw_captions(img, gt, events, cache):
    for (a, b, text, kind) in events:
        if not (a <= gt < b): continue
        lay = caption_layer(text, kind, cache); h = lay.shape[0]
        al = ease((gt - a) / 0.18) * (1 - ease((gt - b + 0.18) / 0.18))
        full = np.zeros((H, W, 4), np.uint8)
        if kind == "emph":
            y = int(H * 0.60 - h / 2); full[y:y + h] = lay
            sc = 0.94 + 0.06 * ease((gt - a) / 0.35)
            M = np.float32([[sc, 0, W / 2 * (1 - sc)], [0, sc, (y + h / 2) * (1 - sc)]])
            full = cv2.warpAffine(full, M, (W, H))
            img = (img.astype(np.float32) * (1 - 0.25 * al)).astype(np.uint8)
        else:
            y = H - BAR - 40 - h; full[y:y + h] = lay
        img = blend(img, full, al)
    return img


def caption_events(S, plan, vfile):
    subs = S.get("subs", {}); mono = set(S.get("monologue_voices", [])); ev = []
    for p in plan:
        if p["s"].get("nocap"): continue
        for v, at, d in p["voices"]:
            items = subs.get(v)
            if not items: continue
            items = [items] if isinstance(items, str) else items
            bounds = speech_bounds(vfile(v), len(items))
            if bounds is None:
                n = [max(len(x), 1) for x in items]; tot = sum(n); c = 0; bounds = []
                for k in n: bounds.append((d * c / tot, d * (c + k) / tot)); c += k
            for txt, (a, b) in zip(items, bounds):
                if txt.startswith("~"): continue
                kind = "emph" if txt.startswith("!") else ("mono" if v in mono else "nar")
                ev.append((at + a - 0.05, at + b + 0.25, txt.lstrip("!"), kind))
    return ev


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
    events = caption_events(S, plan, vfile); capc = {}
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
        elif s["type"] == "video" and s.get("write"): src = WriteClip(os.path.join(gdir, s["src"] + ".mp4"), s.get("move"), s.get("start", 0), s["write"])
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
            img = draw_captions(img, gt, events, capc)
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
