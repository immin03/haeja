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
W, H, FPS = 1920, 1080, int(os.environ.get("ED_FPS", "30"))   # 11/9 실화극: 24 = 원본 클립과 같은 프레임 수(섞기·끊김 없음)
BAR = 0 if os.environ.get("ED_VERT") else 131   # ED_VERT=1: 세로 쇼츠용 조각(띠·자막·구절 없이 렌더, caps/verses 파일로 따로 저장)
GOLD = (201, 164, 92); IVORY = (239, 230, 212)


def font(kind, size):
    f = {"ko": "hahmlet-korean-700-normal.ttf", "ko6": "hahmlet-korean-600-normal.ttf", "en": "cormorant-sc-latin-600-normal.ttf",
         "en5": "cormorant-sc-latin-500-normal.ttf", "ui": "Pretendard-SemiBold.otf", "uim": "Pretendard-Medium.otf",
         "it": "cormorant-garamond-latin-500-italic.ttf", "script": "PinyonScript-Regular.ttf",
         "suit": "SUIT-ExtraBold.ttf", "suitb": "SUIT-Bold.ttf", "suits": "SUIT-SemiBold.ttf"}[kind]   # SUIT: scripts/reels/fonts
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
        if grade != "modern":   # 11/5 대표(영상미): 촛불·횃불 같은 밝은 곳에 영화 같은 은은한 빛 번짐(블룸)
            sm = cv2.resize(f, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
            hi = np.clip(sm - 175, 0, None) * np.array([0.55, 0.8, 1.0], np.float32)
            f = f + cv2.resize(cv2.GaussianBlur(hi, (0, 0), 9), (W, H)) * 0.55
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
def face_fit(cx, cy, s, w, h, face):
    """11/4 대표: '왕 얼굴이 잘려 보임' — face=[x0,y0,x1,y1](원본 비율). 얼굴 윗선이 위 띠 아래 26px 안쪽, 아랫선이 아래 띠 위로 오게 화면 중심을 옮긴다."""
    if face:
        fx0, fy0, fx1, fy1 = face[0] * w, face[1] * h, face[2] * w, face[3] * h
        fy0 -= (fy1 - fy0) * 0.12                                   # 머리카락까지
        top_lim = BAR + 26; bot_lim = H - BAR - 20
        cy_max = fy0 - (top_lim - H / 2) / s                        # 얼굴 윗선이 띠 아래로
        cy_min = fy1 - (bot_lim - H / 2) / s                        # 얼굴 아랫선이 아래 띠 위로
        if cy > cy_max: cy = cy_max
        if cy < cy_min and cy_min <= cy_max: cy = cy_min
        x_max = fx0 - (60 - W / 2) / s; x_min = fx1 - (W - 60 - W / 2) / s
        if cx > x_max: cx = x_max
        if cx < x_min and x_min <= x_max: cx = x_min
    hy = (H / 2 - BAR) / s; hx = (W / 2) / s                        # 위아래는 띠 아래까지만 보이면 됨
    cy = min(max(cy, hy), h - hy); cx = min(max(cx, hx), w - hx)
    return cx, cy


class Still:
    def __init__(self, path, move, scale=1.25, face=None):
        self.face = face
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
        cx, cy = face_fit(cx, cy, s, sw, sh, self.face)
        M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
        return cv2.warpAffine(self.img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


class Clip:
    def __init__(self, path, move, start=0.0, face=None):
        self.face = face
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
        fi = min(t * rate * self.src_fps, n - 1); idx = int(fi)
        if self.move.get("loop"):                         # 11/4 대표: 말하는 동안 입 움직임을 말 끝날 때까지 반복(앞뒤로 오가며 이어 붙임)
            k = int(t * self.src_fps) % max(2 * n - 2, 1); idx = k if k < n else 2 * n - 2 - k; fi = idx
        if self.move.get("pingpong") and length / dur < 0.45:   # 11/5 라이브러리: 긴 장면은 멈추지 않고 0.5배속으로 앞뒤 왕복(촛불·표정처럼 되감겨도 자연스러운 장면만)
            q = (t * 0.5 * self.src_fps) % max(2 * n - 2, 1); fi = q if q < n - 1 else 2 * n - 2 - q; idx = min(int(fi), n - 1)
        f = self.fr[idx]
        a = fi - idx                                      # 11/5 대표(영상미): 느리게 틀 때 앞뒤 프레임을 섞어 끊김 없이 부드럽게
        if a > 0.08 and idx + 1 < n: f = cv2.addWeighted(f, 1 - a, self.fr[idx + 1], a, 0)
        z0, z1 = self.move.get("zoom", [1.0, 1.05]); (x0, y0), (x1, y1) = self.move.get("pan", [[0, 0], [0, 0]])
        e = ease(p); z = z0 + (z1 - z0) * e
        s = self.k * z; h, w = f.shape[:2]
        cx, cy = w / 2 + (x0 + (x1 - x0) * e) * w, h / 2 + (y0 + (y1 - y0) * e) * h
        cx, cy = face_fit(cx, cy, s, w, h, self.face)
        M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
        return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def page_layout(pg):
    """종이 네 모서리(첫 프레임 기준)와 글 → 줄 나눔·글씨 영역(quad). 펜 끝이 마지막 줄 위에 오도록 줄 간격을 맞춘다.
    pg = {corners, paper:[가로,세로], u0, u1, v0, pen_v, last_u, text}"""
    corners = np.float32(pg["corners"]); PWd, PHd = pg.get("paper", [1000, 1150])
    Hi = cv2.getPerspectiveTransform(np.float32([[0, 0], [PWd, 0], [PWd, PHd], [0, PHd]]), corners)
    u0, u1, v0 = pg.get("u0", 70), pg.get("u1", 930), pg.get("v0", 70); sc = (u1 - u0) / 1600
    nfull = pg.get("lines", 7); gap = (pg["pen_v"] - v0) / sc / (nfull + 0.79); size = int(gap * pg.get("size_k", 0.6))
    f = ImageFont.truetype(FONTS + "PinyonScript-Regular.ttf", size); d = ImageDraw.Draw(Image.new("L", (8, 8)))
    words = pg["text"].split(); lines = []; cur = ""
    while words and len(lines) < nfull:
        t = (cur + " " + words[0]).strip()
        if d.textlength(t, font=f) > 1560 and cur: lines.append(cur); cur = ""
        else: cur = t; words.pop(0)
    if cur and len(lines) < nfull: lines.append(cur); cur = ""
    lim = (pg["last_u"] - u0) / sc; last = ""
    while words and d.textlength((last + " " + words[0]).strip(), font=f) < lim: last = (last + " " + words.pop(0)).strip()
    PH = gap * (nfull + 1); v1 = v0 + PH * sc
    quad = cv2.perspectiveTransform(np.float32([[[u0, v0], [u1, v0], [u1, v1], [u0, v1]]]), Hi)[0]
    return {"lines": lines, "line": last or " ", "quad": quad.tolist(), "gap": int(round(gap)), "size": size, "static": True}


class WriteClip(Clip):
    """펜으로 쓰는 장면: 종이 위 영어 필기체가 펜 끝을 따라 써진다 (카메라 움직임은 특징점 추적, 펜 끝은 템플릿 추적)
    write = {quad: 글씨 줄 영역 네 꼭짓점(첫 프레임 기준), tip0: 첫 프레임 펜 끝 [x,y], lines: [이미 써 있는 줄...], line: 지금 쓰는 줄,
             size: 글자 크기, ink: [r,g,b], lead: 펜 끝보다 몇 px 앞까지 보일지}"""
    def __init__(self, path, move, start, wr):
        super().__init__(path, move, start)
        if wr.get("page"): wr = {**wr, **page_layout(wr["page"])}   # 종이 한 장 가득 원근에 맞춘 글씨 (11/4)
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
        if wr.get("clean"):   # 영상 모델이 그린 잉크 자국 지우기: 종이 위에서 첫 프레임보다 어두워진 작은 덩어리만 첫 프레임 종이로 되돌림 (손·펜 같은 큰 덩어리는 그대로)
            f0 = fr[0]; pm = np.zeros((h, w), np.uint8); cv2.fillPoly(pm, [np.int32(wr.get("paper", wr["quad"]))], 255)
            for i in range(1, n):
                f0w = cv2.warpPerspective(f0, Hs[i], (w, h), borderMode=cv2.BORDER_REPLICATE)
                d = cv2.cvtColor(f0w, cv2.COLOR_BGR2GRAY).astype(np.int16) - gray[i].astype(np.int16)
                m2 = ((d > 16) & (cv2.warpPerspective(pm, Hs[i], (w, h)) > 0)).astype(np.uint8)
                m2 = cv2.dilate(m2, np.ones((3, 3), np.uint8))
                nl, lab, st, _ = cv2.connectedComponentsWithStats(m2, 8)
                keep = np.zeros(nl, np.uint8); keep[1:] = (st[1:, cv2.CC_STAT_AREA] < wr.get("blob_max", 2500)).astype(np.uint8)
                tx_, ty_ = self.tips[i]   # 펜 끝 왼쪽·아래 띠는 크기와 관계없이 지운다 (펜에 붙은 자국)
                band = np.zeros((h, w), np.uint8); cv2.rectangle(band, (0, int(ty_) - 50), (int(tx_) - 3, int(ty_) + 60), 1, -1)
                m2 = np.maximum(keep[lab], m2 * band) * 255
                m2 = cv2.dilate(m2, np.ones((5, 5), np.uint8))
                # 첫 프레임에서 손이 있던 자리는 첫 프레임으로 되돌리면 손가락이 비친다 → 그 자리만 주변 종이로 메운다 (11/4)
                hz = np.zeros((h, w), np.uint8); cv2.rectangle(hz, (int(tx) - 40, 0), (w, int(ty) + 60), 255, -1)
                hz = cv2.warpPerspective(hz, Hs[i], (w, h)); mi = ((m2 > 0) & (hz > 0)).astype(np.uint8) * 255
                if mi.any(): f0w = np.where(mi[..., None] > 0, cv2.inpaint(fr[i], mi, 5, cv2.INPAINT_TELEA), f0w)
                m2 = cv2.GaussianBlur(m2, (0, 0), 1.5)[..., None] / 255.0
                fr[i] = (fr[i] * (1 - m2) + f0w * m2).astype(np.uint8)
        # 글씨 평면
        GAP = wr.get("gap", 240); PW, PH = 1600, GAP * (len(wr.get("lines", [])) + 1)
        f = ImageFont.truetype(FONTS + "PinyonScript-Regular.ttf", wr.get("size", 150))
        im = Image.new("L", (PW, PH), 0); d = ImageDraw.Draw(im); yb = int(GAP * 0.79)
        for ln in wr.get("lines", []): d.text((10, yb), ln, font=f, fill=255, anchor="ls"); yb += GAP
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
        if self.wr.get("static"): reveal = np.ones((1, self.PW), np.float32)
        else:
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
    rgb = np.stack([a * GOLD[0] * 1.15, a * GOLD[1] * 1.15, a * GOLD[2] * 1.1], -1)   # 11/4 대표: 주화는 예전 모습이 낫다
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
        self.ko = text_layer([spec.get("ko", "황제의 일기")], "ko6", 56, (222, 196, 140), shadow=False, height=80)
        self.t_kick = text_layer([self.kicker], "ui", 40, GOLD, track=6, shadow=False, height=60)
        self.t_title = text_layer([self.title], "ko", 78, IVORY, height=130)
        self.dust = Particles("embers", 90, 11)
        self.series = text_layer([spec["series"]], "ko6", int(spec.get("series_size", 46)), IVORY, track=6, shadow=False, height=int(spec.get("series_size", 46) * 1.6)) if spec.get("series") else None; self.series_at = float(spec.get("series_at", 7.6))   # 11/9 실화극 부제
        self.dur = 12.0

    def frame(self, t):
        img = np.zeros((H, W, 3), np.uint8)
        cx, cy, r = W // 2, 420, 182
        if 0.8 <= t < 10.2:
            # 금빛 잉크 선이 원을 그림 (0.8~2.6초)
            # 11/4 대표: '노란 동그라미' 대신 황금빛이 원을 그리는 듯 — 붓 끝처럼 굵기가 변하는 금선, 머리의 흰 금빛 불꽃, 뒤로 흩날리는 금가루
            p = ease((t - 0.8) / 1.8); ang = 360 * p
            core = np.zeros((H, W, 3), np.float32); halo = np.zeros((H, W, 3), np.float32)
            n = max(int(ang / 2), 1)
            for j in range(n):
                a0 = -90 + j * ang / n; a1 = -90 + (j + 1) * ang / n; q = (j + 0.5) / n
                th = 2.0 + 3.0 * math.sin(math.pi * q) ** 0.7
                recent = math.exp(-(1 - q) * 5) if p < 1 else 0.35
                col = (110 + 80 * recent, 186 + 50 * recent, 232 + 20 * recent)
                cv2.ellipse(core, (cx, cy), (r, r), 0, a0, a1, col, int(round(th)), cv2.LINE_AA)
                cv2.ellipse(halo, (cx, cy), (r, r), 0, a0, a1, (60, 130, 200), int(th * 5), cv2.LINE_AA)
            if p < 1:
                hx = cx + r * math.cos(math.radians(ang - 90)); hy = cy + r * math.sin(math.radians(ang - 90))
                cv2.circle(core, (int(hx), int(hy)), 6, (235, 250, 255), -1, cv2.LINE_AA)
                cv2.circle(halo, (int(hx), int(hy)), 26, (120, 200, 255), -1, cv2.LINE_AA)
                rng = np.random.default_rng(int(t * 60))
                for _ in range(18):
                    back = rng.uniform(0, 40); da = math.radians(ang - 90 - back)
                    rr = r + rng.normal(0, 6 + back * 0.25)
                    px_, py_ = cx + rr * math.cos(da), cy + rr * math.sin(da)
                    br = (1 - back / 40) * rng.uniform(0.4, 1.0)
                    cv2.circle(core, (int(px_), int(py_)), int(rng.integers(1, 3)), (150 * br + 60, 215 * br + 30, 255 * br), -1, cv2.LINE_AA)
            elif t < 3.4:
                fl = math.exp(-(t - 2.6) * 4)
                halo *= 1 + 1.2 * fl; core *= 1 + 0.5 * fl   # 원이 닫히는 순간 고리 전체가 한 번 환하게
            g = cv2.GaussianBlur(halo, (0, 0), 14) * 0.55 + cv2.GaussianBlur(core, (0, 0), 3) * 0.8
            img = np.clip(img.astype(np.float32) + core + g, 0, 255).astype(np.uint8)
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
        if self.series is not None and t >= self.series_at:
            a = ease((t - self.series_at) / 0.8) * (1 - ease((t - 9.6) / 0.6))
            layer = np.zeros((H, W, 4), np.uint8); layer[825:825 + self.series.shape[0]] = self.series
            img = blend(img, layer, a)
        return img


def end_frame(s, t, dur, cache, logo):
    """엔딩: 슬로건 → 금선·주화·THE EMPEROR'S DIARY·황제의 일기. 글자는 내레이션이 시작하는 순간에 맞춰 떠오른다."""
    if "end" not in cache:
        cache["end"] = (coin_gold(logo), text_layer(["THE EMPEROR'S DIARY"], "en", 56, GOLD, track=12, shadow=False, height=96),
                        text_layer(["황제의 일기"], "ko6", 40, (222, 196, 140), shadow=False, height=64),
                        text_layer([s.get("slogan", "매일 밤, 황제처럼 생각하라")], "ko", 58, (236, 212, 160), shadow=False, height=96),
                        Particles("embers", 50, 77))
    coin, en, ko, sl, dust = cache["end"]
    vat = s.get("_vat", {}); vs = s.get("voice") or []
    t1 = vat.get(vs[0], 0.4) - 0.15 if vs else 0.2              # 슬로건: 첫 내레이션과 함께
    t2 = vat.get(vs[1], 1.8) - 0.25 if len(vs) > 1 else t1 + 1.4  # 채널명: 두 번째 내레이션과 함께
    out = 1 - ease((t - dur + 1.2) / 1.2)
    img = np.zeros((H, W, 3), np.uint8)
    a1 = ease((t - t1) / 0.9) * out
    l = np.zeros((H, W, 4), np.uint8); l[330:426] = sl; img = blend(img, l, a1, dy=10 * (1 - ease((t - t1) / 0.9)))
    a2 = ease((t - t2) / 0.8) * out
    ln = np.zeros((H, W, 3), np.uint8); hw = int(160 * ease((t - t2 + 0.2) / 1.0))
    if hw > 2: cv2.line(ln, (W // 2 - hw, 478), (W // 2 + hw, 478), (110, 170, 205), 1, cv2.LINE_AA)
    img = cv2.add(img, (ln.astype(np.float32) * a2).astype(np.uint8))
    cs = coin.shape[0]; cy = 640; sc = 0.62; c2 = cv2.resize(coin, (int(cs * sc), int(cs * sc))); s2 = c2.shape[0]
    l = np.zeros((H, W, 4), np.uint8); l[cy - s2 // 2:cy - s2 // 2 + s2, W // 2 - s2 // 2:W // 2 - s2 // 2 + s2] = c2; img = blend(img, l, a2)
    l = np.zeros((H, W, 4), np.uint8); l[740:836] = en; l[830:894] = ko; img = blend(img, l, ease((t - t2 - 0.1) / 0.8) * out)
    return dust.draw(img, t)


def episode_frame(s, t, dur, cache):
    """편 오프닝 (템플릿): EPISODE · 큰 숫자 · 빛나며 길어지는 금선 · 한글 제목 · 영어 부제 · 금빛 먼지 · 천천히 다가오는 카메라 (11/3 대표 확정: 파일럿 v2 카드 느낌, 군더더기 없이)"""
    if "ep" not in cache:
        cache["ep"] = (text_layer(["EPISODE"], "en", 38, GOLD, track=16, shadow=False, height=60),
                       text_layer([str(s.get("num", 1))], "en", 128, GOLD, shadow=False, height=170),
                       text_layer([s["title"]], "ko", 70, (236, 212, 160), height=110),
                       text_layer([s.get("en", "")], "it", 44, (205, 192, 168), shadow=False, height=70),
                       Particles("embers", 60, 21))
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        cache["glow"] = (np.exp(-(((xx - W / 2) / 700) ** 2 + ((yy - 520) / 330) ** 2))[..., None] * np.array([18, 30, 44], np.float32))
    k, num, ttl, en, dust = cache["ep"]
    out_a = 1 - ease((t - dur + 0.7) / 0.7)
    img = np.clip(cache["glow"] * out_a, 0, 255).astype(np.uint8)
    lay = np.zeros((H, W, 4), np.uint8); lay[262:322] = k; lay[318:488] = num
    img = blend(img, lay, ease(t / 0.9) * out_a)
    L = int(380 * ease((t - 0.3) / 1.4)); y = 512
    if L > 2:
        line = np.zeros((H, W, 3), np.uint8)
        cv2.line(line, (W // 2 - L, y), (W // 2 + L, y), (92, 164, 201), 2, cv2.LINE_AA)
        cv2.circle(line, (W // 2 - L, y), 3, (140, 200, 235), -1, cv2.LINE_AA); cv2.circle(line, (W // 2 + L, y), 3, (140, 200, 235), -1, cv2.LINE_AA)
        glow = cv2.GaussianBlur(line, (0, 0), 7); sweep = np.zeros((H, W, 3), np.uint8)
        if 1.2 < t < 2.6:
            sx = int(W / 2 - 420 + 840 * ease((t - 1.2) / 1.2)); cv2.circle(sweep, (sx, y), 26, (170, 220, 255), -1); sweep = cv2.GaussianBlur(sweep, (0, 0), 14)
        img = cv2.add(img, (cv2.addWeighted(cv2.addWeighted(line, 1.0, glow, 1.6, 0), 1.0, sweep, 0.9, 0).astype(np.float32) * out_a).astype(np.uint8))
    l2 = np.zeros((H, W, 4), np.uint8); l2[540:650] = ttl
    img = blend(img, l2, ease((t - 0.7) / 0.9) * out_a, dy=12 * (1 - ease((t - 0.7) / 0.9)))
    if s.get("en"):
        l3 = np.zeros((H, W, 4), np.uint8); l3[655:725] = en; img = blend(img, l3, ease((t - 1.3) / 1.0) * out_a)
    img = dust.draw(img, t)
    z = 1.0 + 0.035 * ease(t / dur); M = np.float32([[z, 0, W / 2 * (1 - z)], [0, z, H / 2 * (1 - z)]])
    return cv2.warpAffine(img, M, (W, H))


def warm_bg(cache, cy=520, k=1.0):
    """11/4 대표: 글자 화면이 너무 어두움 → 가운데에 은은한 금빛 바탕"""
    key = f"wbg{cy}"
    if key not in cache:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        cache[key] = np.exp(-(((xx - W / 2) / 820) ** 2 + ((yy - cy) / 380) ** 2))[..., None] * np.array([20, 34, 52], np.float32) + np.array([10, 12, 14], np.float32)
    return np.clip(cache[key] * k, 0, 255).astype(np.uint8)


BRIGHT_GOLD = (226, 190, 118); BRIGHT_IVORY = (250, 244, 230)


def card_frame(spec_shot, t, dur, cache):
    """편 안의 '문장' 카드 (템플릿, 11/3 대표 확정: 효과 없이 깔끔하게): 로마 숫자, 가는 금선, 한글 제목, 영어 부제. 서서히 나타났다 사라짐"""
    if "card" not in cache:
        cache["card"] = (text_layer([spec_shot["num"]], "en", 84, BRIGHT_GOLD, shadow=False, height=110),
                         text_layer([spec_shot["title"]], "ko", 60, BRIGHT_IVORY, height=100),
                         text_layer([spec_shot.get("en", "")], "it", 40, (226, 214, 190), shadow=False, height=64))
    num, ttl, en = cache["card"]
    a = ease(t / 0.8) * (1 - ease((t - dur + 0.7) / 0.7))
    img = (warm_bg(cache, 520).astype(np.float32) * a).astype(np.uint8)
    lay = np.zeros((H, W, 4), np.uint8); lay[350:460] = num; lay[512:612] = ttl
    if spec_shot.get("en"): lay[618:682] = en
    img = blend(img, lay, a)
    line = np.zeros((H, W, 3), np.uint8); cv2.line(line, (W // 2 - 140, 488), (W // 2 + 140, 488), (92, 164, 201), 1, cv2.LINE_AA)
    return cv2.add(img, (line.astype(np.float32) * a).astype(np.uint8))


def tonight_frame(s, t, dur, cache):
    if "tn" not in cache:
        cache["tn"] = (text_layer(["FOR TONIGHT  ·  오늘 밤 해 볼 일"], "ui", 34, BRIGHT_GOLD, track=3, shadow=False, height=70),
                       text_layer(s["lines"], "ko", 64, BRIGHT_IVORY, shadow=False, height=260))
    k, body = cache["tn"]
    a = ease(t / 0.8) * (1 - ease((t - dur + 0.6) / 0.6))
    img = np.maximum((warm_bg(cache, 500).astype(np.float32) * a).astype(np.uint8), 8)
    layer = np.zeros((H, W, 4), np.uint8); layer[330:400] = k; layer[420:680] = body
    return blend(img, layer, a)


def icon_layer(kind, size=64, col=(255, 255, 255), ring=True):
    """금색 가는 테두리 원 안의 흰 선 아이콘 (구독 종 / 좋아요 엄지)"""
    im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = size
    if ring: d.ellipse([4, 4, size * 2 - 4, size * 2 - 4], outline=GOLD + (255,), width=4)
    lw = 5; col = col + (255,)
    if kind == "bell":
        d.arc([c - 26, c - 34, c + 26, c + 18], 180, 360, fill=col, width=lw)
        d.line([c - 26, c - 8, c - 26, c + 14], fill=col, width=lw); d.line([c + 26, c - 8, c + 26, c + 14], fill=col, width=lw)
        d.line([c - 34, c + 16, c + 34, c + 16], fill=col, width=lw); d.ellipse([c - 7, c + 20, c + 7, c + 32], outline=col, width=lw)
        d.line([c, c - 44, c, c - 34], fill=col, width=lw)
    else:  # thumb
        d.rounded_rectangle([c - 34, c - 6, c - 18, c + 30], 3, outline=col, width=lw)
        d.line([(c - 14, c - 4), (c - 2, c - 34), (c + 6, c - 32), (c + 4, c - 8), (c + 30, c - 8), (c + 32, c + 2), (c + 24, c + 30), (c - 14, c + 30)], fill=col, width=lw, joint="curve")
    return np.array(im)


def pill_layer(kind, label, pressed=False):
    """알약 모양 버튼: 아이콘 + 글자. pressed=True 면 금색으로 채워진 상태"""
    w, h = 300, 84; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if pressed: d.rounded_rectangle([2, 2, w - 3, h - 3], h // 2, fill=(212, 178, 112, 255))
    else: d.rounded_rectangle([2, 2, w - 3, h - 3], h // 2, fill=(20, 16, 12, 150), outline=GOLD + (255,), width=2)
    ic = Image.fromarray(icon_layer(kind, 64, (30, 22, 14) if pressed else (255, 255, 255), ring=False)).resize((60, 60), Image.LANCZOS)
    f = font("ui", 32); col = (30, 22, 14, 255) if pressed else (246, 238, 222, 255)
    tw = d.textlength(label, font=f); gx = int((w - (60 + 14 + tw)) / 2)   # 11/10 대표: 아이콘+글자를 알약 가운데로
    im.alpha_composite(ic, (gx, (h - 60) // 2)); d.text((gx + 74, h / 2), label, font=f, fill=col, anchor="lm")
    return np.array(im)


def outro_frame(s, t, dur, cache, logo):
    """아웃트로 (템플릿): 주화 → THE EMPEROR'S DIARY · 황제의 일기 → 알약 버튼 [구독] [좋아요] (눌리며 금색으로) → 금선 아래 다음 이야기 예고"""
    if "out" not in cache:
        coin = coin_gold(logo); cs = coin.shape[0]; k = 0.72
        cache["out"] = dict(coin=cv2.resize(coin, (int(cs * k), int(cs * k))),
                            en=text_layer(["THE EMPEROR'S DIARY"], "en", 54, GOLD, track=12, shadow=False, height=92),
                            ko=text_layer(["황제의 일기"], "ko6", 38, (222, 196, 140), shadow=False, height=60),
                            sub0=pill_layer("bell", "구독"), sub1=pill_layer("bell", "구독중", True),
                            like0=pill_layer("thumb", "좋아요"), like1=pill_layer("thumb", "좋아요", True),
                            nxt_k=text_layer([s.get("next_kicker", "NEXT")], "en5", 28, (190, 160, 105), track=10, shadow=False, height=46),
                            nxt=text_layer([s.get("next", "")], "ko6", 46, IVORY, shadow=False, height=72),
                            dust=Particles("embers", 80, 41))
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        cache["oglow"] = (np.exp(-(((xx - W / 2) / 760) ** 2 + ((yy - 430) / 360) ** 2))[..., None] * np.array([16, 30, 46], np.float32))
    o = cache["out"]; out_a = 1 - ease((t - dur + 1.0) / 1.0)
    img = np.clip(cache["oglow"] * ease(t / 1.2) * out_a, 0, 255).astype(np.uint8)
    c = o["coin"]; cs = c.shape[0]; cy = 300
    l = np.zeros((H, W, 4), np.uint8); l[cy - cs // 2:cy - cs // 2 + cs, W // 2 - cs // 2:W // 2 - cs // 2 + cs] = c
    img = blend(img, l, ease(t / 1.0) * out_a, dy=-14 * (1 - ease(t / 1.0)))
    l = np.zeros((H, W, 4), np.uint8); l[438:530] = o["en"]; l[524:584] = o["ko"]; img = blend(img, l, ease((t - 0.6) / 0.9) * out_a)
    for i, (key, tp) in enumerate((("sub", s.get("tap_sub", 3.4)), ("like", s.get("tap_like", 4.2)))):
        a = ease((t - 2.4 - 0.2 * i) / 0.7) * out_a
        if a <= 0: continue
        k = t - tp
        sc = 1.0 - 0.08 * math.exp(-((k - 0.06) / 0.06) ** 2) + 0.05 * math.exp(-((k - 0.24) / 0.1) ** 2) if k > -0.2 else 1.0
        pr = ease(k / 0.18) if k > 0 else 0.0
        base = o[key + "0"].astype(np.float32); on = o[key + "1"].astype(np.float32)
        pl = (base * (1 - pr) + on * pr).astype(np.uint8)
        pw, ph = int(pl.shape[1] * sc), int(pl.shape[0] * sc); pl = cv2.resize(pl, (pw, ph))
        cx = W // 2 + (-170 if i == 0 else 170); cyb = 680
        lay = np.zeros((H, W, 4), np.uint8); lay[cyb - ph // 2:cyb - ph // 2 + ph, cx - pw // 2:cx - pw // 2 + pw] = pl
        if 0 < k < 0.8:   # 눌릴 때 퍼지는 고리
            ring = np.zeros((H, W, 3), np.uint8); e = ease(k / 0.8)
            cv2.ellipse(ring, (cx, cyb), (int(150 + 60 * e), int(42 + 40 * e)), 0, 0, 360, (92, 164, 201), 2, cv2.LINE_AA)
            img = cv2.add(img, (cv2.GaussianBlur(ring, (0, 0), 2).astype(np.float32) * (1 - e) * a).astype(np.uint8))
        img = blend(img, lay, a)
    if s.get("next"):
        a = ease((t - 6.0) / 0.8) * out_a
        ln = np.zeros((H, W, 3), np.uint8); hw = int(110 * ease((t - 5.8) / 1.0))
        if hw > 2: cv2.line(ln, (W // 2 - hw, 772), (W // 2 + hw, 772), (110, 170, 205), 1, cv2.LINE_AA)
        img = cv2.add(img, (ln.astype(np.float32) * a).astype(np.uint8))
        l = np.zeros((H, W, 4), np.uint8); l[790:836] = o["nxt_k"]; l[836:908] = o["nxt"]
        img = blend(img, l, a)
    img = o["dust"].draw(img, t)
    return img


def endscreen_frame(s, t, dur, cache):
    """11/4 대표: 맨 마지막은 유튜브 최종 화면(관련 영상·구독)이 올라갈 빈 화면 — 글자·그림 없이 은은한 바탕만"""
    a = ease(t / 1.2) * (1 - ease((t - dur + 1.0) / 1.0))
    return (warm_bg(cache, 540).astype(np.float32) * a).astype(np.uint8)


def finale_frame(s, t, dur, cache, logo):
    """11/4 대표: 마지막 한 화면 — "매일 밤, 황제처럼 생각하라 · 황제의 일기" 내레이션이 나올 때 구독·좋아요 버튼과 이전 편 영상 자리가 함께 보이게.
    왼쪽 금테 칸 = 유튜브 최종 화면의 '동영상' 요소 자리, 위 주화 = '구독' 요소 자리(스튜디오에서 같은 위치에 배치)"""
    if "fin" not in cache:
        coin = coin_gold(logo); c2 = cv2.resize(coin, (180, 180))
        cache["fin"] = dict(coin=c2, sl=text_layer([s.get("slogan", "매일 밤, 황제처럼 생각하라")], "ko", 54, (240, 216, 166), shadow=False, height=86),
                            en=text_layer(["THE EMPEROR'S DIARY"], "en", 40, BRIGHT_GOLD, track=10, shadow=False, height=66),
                            ko=text_layer([s.get("brand_ko", "황제의 일기")], "ko6", 32, (232, 210, 160), shadow=False, height=52),
                            pk=text_layer([s.get("prev_kicker", "이전 이야기  ·  EPISODE 1")], "ko6", 30, (226, 200, 150), shadow=False, height=50),
                            nk=text_layer([s.get("next_kicker", "다음 이야기")], "ko6", 28, (210, 190, 150), shadow=False, height=46),
                            nx=text_layer([s.get("next", "")], "ko", 40, BRIGHT_IVORY, shadow=False, height=66),
                            sub0=pill_layer("bell", "구독"), sub1=pill_layer("bell", "구독중", True),
                            like0=pill_layer("thumb", "좋아요"), like1=pill_layer("thumb", "좋아요", True), dust=Particles("embers", 50, 91),
                            # 11/5 대표: 버튼 아래 행동 유도 한 줄 (4편부터)
                            cta=text_layer([s.get("cta", "좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다.")], "ko6", 27, (226, 204, 156), shadow=False, height=44))
    o = cache["fin"]; vat = s.get("_vat", {}); vs = s.get("voice") or []
    tv = lambda i, d: vat.get(vs[i], d) if len(vs) > i else d
    t_sl, t_ch, t_o1, t_o2 = tv(0, 0.8) - 0.15, tv(1, 3.0) - 0.2, tv(2, 5.0), tv(3, 11.0)
    out = 1 - ease((t - dur + 0.8) / 0.8)
    img = warm_bg(cache, 560)
    img = (img.astype(np.float32) * ease(t / 1.0)).astype(np.uint8)
    l = np.zeros((H, W, 4), np.uint8); cy = 262; l[cy - 90:cy + 90, W // 2 - 90:W // 2 + 90] = o["coin"]; img = blend(img, l, ease(t / 1.0) * out)
    l = np.zeros((H, W, 4), np.uint8); l[366:452] = o["sl"]; img = blend(img, l, ease((t - t_sl) / 0.9) * out, dy=8 * (1 - ease((t - t_sl) / 0.9)))
    l = np.zeros((H, W, 4), np.uint8); l[446:512] = o["en"]; l[504:556] = o["ko"]; img = blend(img, l, ease((t - t_ch) / 0.8) * out)
    # 왼쪽: 이전 편 영상 자리 (유튜브 동영상 요소가 이 칸에 뜬다)
    a = ease((t - t_ch - 0.4) / 0.9) * out * (1.0 if s.get("prev_box") else 0.0)   # 11/4 대표: 다음 편부터 이전 편 칸(금테·글자)은 그리지 않고 비워 둔다 — 유튜브 동영상 요소를 그 빈자리에
    bx0, by0, bx1, by1 = 270, 598, 870, 936
    fr = np.zeros((H, W, 3), np.uint8); cv2.rectangle(fr, (bx0, by0), (bx1, by1), (6, 6, 8), -1)
    img = (img.astype(np.float32) * (1 - 0.85 * a * (fr.sum(2, keepdims=True) > 0)) ).astype(np.uint8)
    ln = np.zeros((H, W, 3), np.uint8); cv2.rectangle(ln, (bx0 - 3, by0 - 3), (bx1 + 3, by1 + 3), (92, 164, 201), 2, cv2.LINE_AA)
    img = cv2.add(img, (ln.astype(np.float32) * a).astype(np.uint8))
    l = np.zeros((H, W, 4), np.uint8); l[542:592] = o["pk"]; img = blend(img, l, a, dx=bx0 + (bx1 - bx0) // 2 - W // 2)
    # 오른쪽: 구독·좋아요 (첫 해설 '구독과 좋아요로'에 맞춰 눌림)
    for i, (key, tp) in enumerate((("sub", t_o1 + 1.6), ("like", t_o1 + 2.4))):
        a = ease((t - t_ch - 0.6 - 0.2 * i) / 0.7) * out
        if a <= 0: continue
        k = t - tp; sc = 1.0 - 0.08 * math.exp(-((k - 0.06) / 0.06) ** 2) + 0.05 * math.exp(-((k - 0.24) / 0.1) ** 2) if k > -0.2 else 1.0
        pr = ease(k / 0.18) if k > 0 else 0.0
        pl = (o[key + "0"].astype(np.float32) * (1 - pr) + o[key + "1"].astype(np.float32) * pr).astype(np.uint8)
        pw, ph = int(pl.shape[1] * sc * 1.15), int(pl.shape[0] * sc * 1.15); pl = cv2.resize(pl, (pw, ph))
        cx, cyb = 1145 + 380 * i, 690
        lay = np.zeros((H, W, 4), np.uint8); lay[cyb - ph // 2:cyb - ph // 2 + ph, cx - pw // 2:cx - pw // 2 + pw] = pl
        if 0 < k < 0.8:
            ring = np.zeros((H, W, 3), np.uint8); e = ease(k / 0.8)
            cv2.ellipse(ring, (cx, cyb), (int(170 + 60 * e), int(48 + 40 * e)), 0, 0, 360, (92, 164, 201), 2, cv2.LINE_AA)
            img = cv2.add(img, (cv2.GaussianBlur(ring, (0, 0), 2).astype(np.float32) * (1 - e) * a).astype(np.uint8))
        img = blend(img, lay, a)
    if s.get("cta", "") is not None and not s.get("no_cta"):
        a = ease((t - t_ch - 1.4) / 0.8) * out
        l = np.zeros((H, W, 4), np.uint8); l[740:784] = o["cta"]; img = blend(img, l, a, dx=1335 - W // 2)
    if s.get("next"):
        a = ease((t - t_o2) / 0.8) * out
        l = np.zeros((H, W, 4), np.uint8); l[790:836] = o["nk"]; l[836:902] = o["nx"]; img = blend(img, l, a, dx=1335 - W // 2)
    return o["dust"].draw(img, t)


def prev_frame(s, t, dur, cache, P):
    """11/4 대표: 전편을 못 본 사람에게 1편 추천 — 'PREVIOUS EPISODE' + 1편 썸네일(금테) + 제목"""
    if "pv" not in cache:
        th = cv2.imread(P(s["thumb"]))[..., ::-1]; tw = 880; thh = int(th.shape[0] * tw / th.shape[1]); th = cv2.resize(th, (tw, thh), interpolation=cv2.INTER_AREA)
        fr = np.zeros((thh + 8, tw + 8, 4), np.uint8); fr[..., :3] = GOLD; fr[..., 3] = 255; fr[4:-4, 4:-4, :3] = th
        cache["pv"] = (fr, text_layer([s.get("kicker", "PREVIOUS  ·  EPISODE 1")], "en5", 30, (214, 182, 122), track=10, shadow=False, height=50),
                       text_layer([s.get("title", "")], "ko", 56, BRIGHT_IVORY, shadow=False, height=90),
                       text_layer([s.get("sub", "")], "ko6", 36, (230, 214, 182), shadow=False, height=60))
    fr, kk, tt_, sub = cache["pv"]; out_a = 1 - ease((t - dur + 0.9) / 0.9)
    img = warm_bg(cache, 470)
    l = np.zeros((H, W, 4), np.uint8); l[150:200] = kk; img = blend(img, l, ease(t / 0.8) * out_a)
    fh, fw = fr.shape[:2]; y0 = 225
    l = np.zeros((H, W, 4), np.uint8); l[y0:y0 + fh, (W - fw) // 2:(W - fw) // 2 + fw] = fr
    img = blend(img, l, ease((t - 0.3) / 0.9) * out_a, dy=12 * (1 - ease((t - 0.3) / 0.9)))
    l = np.zeros((H, W, 4), np.uint8); l[y0 + fh + 26:y0 + fh + 116] = tt_; l[y0 + fh + 112:y0 + fh + 172] = sub
    return blend(img, l, ease((t - 0.9) / 0.8) * out_a)


def recap_frame(s, t, dur, cache, active):
    """오늘의 일곱 문장 (템플릿): 왼쪽 정렬 목록, 지금 읽는 문장만 금색으로 밝게, 읽은 문장은 은은하게 남음"""
    if "rc" not in cache:
        big = s.get("center") and len(s["items"]) <= 4   # 11/10 대표: 항목이 적으면 크게, 화면 가운데에
        f = font("ko", 58 if big else 42); fk = font("en", 56 if big else 40)
        rows = []; base_y = 66 if big else 48
        for i, it in enumerate(s["items"]):   # 11/4 대표: I II III 과 문장을 한 줄 기준선에 맞추고, 숫자는 오른쪽 끝을 한 열로
            im = Image.new("RGBA", (1500, 88 if big else 64), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            d.text((100 if big else 80, base_y), ["I", "II", "III", "IV", "V", "VI", "VII"][i], font=fk, fill=BRIGHT_GOLD + (255,), anchor="rs")
            d.text((150 if big else 120, base_y), it, font=f, fill=(255, 255, 255, 255), anchor="ls")
            rows.append(np.array(im))
        cache["rc"] = (rows, text_layer([s.get("head", "오늘의 일곱 문장")], "ko", 56 if big else 46, (240, 214, 160), shadow=False, height=84 if big else 70),
                       text_layer([s.get("head_en", "SEVEN LINES FROM ONE NIGHT")], "en5", 34 if big else 30, (214, 182, 122), track=10, shadow=False, height=56 if big else 50))
        rh = 126 if big else 76; tot = 56 + 84 + 70 + len(rows) * rh
        cache["rc_y"] = ((H - tot) // 2 if big else 160, rh, big)
        widest = max(int(np.where(r[..., 3].max(axis=0) > 0)[0].max()) for r in rows)
        cache["rc_x"] = (W - widest) // 2
    rows, hk, he = cache["rc"]; out_a = 1 - ease((t - dur + 0.8) / 0.8); x0 = cache["rc_x"]; y0, rh, big = cache["rc_y"]
    img = warm_bg(cache, 540 if big else 560)
    l = np.zeros((H, W, 4), np.uint8); l[y0:y0 + he.shape[0]] = he; l[y0 + he.shape[0] - 2:y0 + he.shape[0] - 2 + hk.shape[0]] = hk
    img = blend(img, l, ease(t / 0.8) * out_a)
    for i, r in enumerate(rows):
        if active is None or i > active: continue
        cur = (i == active)
        rr = r.copy()
        if cur: rr[..., :3] = (rr[..., :3].astype(np.float32) * np.array([1.0, 0.9, 0.7])).astype(np.uint8)
        l = np.zeros((H, W, 4), np.uint8); y = (y0 + 56 + 84 + 70 + i * rh) if big else 320 + i * 76; l[y:y + rr.shape[0], x0:x0 + 1500] = rr[:, :W - x0]
        img = blend(img, l, (1.0 if cur else 0.72) * out_a)
    return img


# ---------- 덧씌우는 글자 (자막·구절·개념) ----------
def overlay(img, ov, t, dur, cache, key):
    k = ov["kind"]
    if k == "caption":   # 작은 장소·연도 자막, 왼쪽 아래
        if key not in cache: cache[key] = text_layer([ov["text"]], "ui", ov.get("size", 34), IVORY, track=2, width=W, height=60)
        a = ease((t - ov.get("at", 0.3)) / 0.6) * (1 - ease((t - dur + 0.5) / 0.5))
        lay = np.zeros((H, W, 4), np.uint8); tl = cache[key]
        # 왼쪽 정렬처럼 보이게 가운데 정렬 레이어를 옮긴다
        if ov.get("pos") == "top": lay[BAR + 34:BAR + 94] = tl   # 대사 자막과 겹치지 않게 위쪽에
        else: lay[H - BAR - 120:H - BAR - 60] = tl
        return blend(img, lay, a, dx=-W // 2 + 380)
    if k == "verse":     # 명상록 구절 (템플릿): 가운데 정렬, 두 줄 + 빈 줄 + '- 명상록 n권 n절 -', 화면을 살짝 어둡게
        if key not in cache:
            cache[key] = (text_layer(ov["lines"], "ko", ov.get("size", 70), (240, 222, 178), height=230, line_gap=1.5),
                          text_layer([f"- {ov['src']} -"], "ko6", 38, (205, 180, 128), shadow=True, height=70))
        q, src = cache[key]
        a = ease((t - ov["at"]) / 0.7) * (1 - ease((t - ov.get("until", dur) + 0.6) / 0.6))
        ad = ease((t - ov["at"] + 0.2) / 1.5) * (1 - ease((t - ov.get("until", dur) + 1.2) / 1.2))
        if a <= 0 and ad <= 0: return img
        img = (img.astype(np.float32) * (1 - 0.45 * ad)).astype(np.uint8)
        lay = np.zeros((H, W, 4), np.uint8); top = ov.get("top", 360); lay[top:top + 230] = q
        if ov.get("line_at"):   # 두 번째 줄부터는 그 줄을 읽기 시작할 때 나타남
            out = 1 - ease((t - ov.get("until", dur) + 0.6) / 0.6); n = len(ov["lines"]); hh = 230 // n
            for li in range(n):
                al = ease((t - max(ov["line_at"][li], ov["at"])) / 0.5) * out
                if al <= 0: continue
                ll = np.zeros((H, W, 4), np.uint8); ll[top + li * hh:top + (li + 1) * hh] = q[li * hh:(li + 1) * hh]
                img = blend(img, ll, al, dy=8 * (1 - al))
            a2 = ease((t - ov["line_at"][-1] - 0.9) / 0.7) * out
            l2 = np.zeros((H, W, 4), np.uint8); l2[top + 250:top + 320] = src
            return blend(img, l2, a2)
        a2 = ease((t - ov["at"] - 0.9) / 0.7) * (1 - ease((t - ov.get("until", dur) + 0.6) / 0.6))
        l2 = np.zeros((H, W, 4), np.uint8); l2[top + 250:top + 320] = src
        return blend(blend(img, lay, a, dy=8 * (1 - a)), l2, a2)
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
        L = ov.get("len", 4.0)
        a = ease((t - ov["at"]) / 0.8) * (1 - ease((t - ov["at"] - L) / 0.8))
        ad = ease((t - ov["at"] + 0.3) / 1.6) * (1 - ease((t - ov["at"] - L + 0.2) / 1.8))   # 11/4 대표: 더 천천히 어두워지고 밝아지게
        if a <= 0 and ad <= 0: return img
        dark = (img.astype(np.float32) * (1 - 0.68 * ad)).astype(np.uint8)
        lay = np.zeros((H, W, 4), np.uint8); lay[370:426] = kk; lay[440:640] = body
        if ov.get("en"): lay[640:704] = en
        return blend(dark, lay, a)
    return img


# ---------- 자막 (템플릿: 쇼츠와 같은 방식, 강조 문장만 크게) ----------
def speech_bounds(path, n, items=None):
    """음성 파일 안 문장 경계 (11/3 개선): 글자 수 비율로 예상한 경계에서 가장 가까운 쉼(±1.2초)에 맞춘다. 쉼이 없으면 예상 위치 그대로"""
    L = dur_of(path)
    if n <= 1: return [(0.0, L)]
    out = subprocess.run(["ffmpeg", "-i", path, "-af", "silencedetect=noise=-38dB:d=0.15", "-f", "null", "-"], capture_output=True, text=True).stderr
    import re
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]; en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    sil = [(a, b) for a, b in zip(st, en) if 0.15 < a and b < L - 0.05]
    lead = en[0] if st and st[0] < 0.05 and en else 0.0
    tail = st[-1] if st and len(en) < len(st) else L
    w = [max(len(re.sub(r"[^가-힣A-Za-z0-9]", "", x or "")), 1) for x in (items or ["x"] * n)]
    tot = sum(w); c = 0; bounds = []; prev = lead
    for k in range(n - 1):
        c += w[k]; e = lead + (tail - lead) * c / tot
        best = min(sil, key=lambda g: abs((g[0] + g[1]) / 2 - e), default=None)
        if best and abs((best[0] + best[1]) / 2 - e) < 1.2 and best[0] > prev:
            bounds.append((prev, best[0])); prev = best[1]
        else:
            bounds.append((prev, e)); prev = e
    bounds.append((prev, tail))
    return bounds


def wrap_ko(text, fnt, maxw):
    """자막 줄 나눔 (11/4): 한 줄에 들어가면 한 줄. 두 줄이면 쉼표 뒤에서 끊는 쪽을 우선하고, 뒷줄에 두세 글자만 남는 끊김은 피한다."""
    d = ImageDraw.Draw(Image.new("L", (10, 10))); words = text.split(" "); lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) > maxw and cur: lines.append(cur); cur = w
        else: cur = t
    if cur: lines.append(cur)
    if len(lines) != 2: return lines
    best, bc = lines, None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:]); wa, wb = d.textlength(a, font=fnt), d.textlength(b, font=fnt)
        if wa > maxw or wb > maxw: continue
        c = abs(wa - wb) / maxw
        if a.endswith((",", ".", "?", "!")): c -= 0.5          # 쉼표·마침표 뒤에서 끊기
        if min(wa, wb) < 0.3 * max(wa, wb): c += 1.0           # 한쪽이 너무 짧은 줄
        if bc is None or c < bc: best, bc = [a, b], c
    return best


CAP_SCALE = 1.0


def caption_layer(text, kind, cache):
    key = (text, kind)
    if key in cache: return cache[key]
    if kind == "emph":
        f = font("ko", 72); lines = wrap_ko(text, f, 1400)
        lay = text_layer(lines, "ko", 72, (240, 222, 178), height=110 * len(lines) + 40, line_gap=1.4)
    else:
        kk, sz, col = ("ko6", 46, (246, 238, 222)) if kind == "mono" else ("ui", 44, (255, 255, 255))
        sz = int(round(sz * CAP_SCALE))   # 11/10 대표: 40·50대 시청층 — 자막 살짝 크게 (spec "cap_scale")
        lines = wrap_ko(text, font(kk, sz), 1500)
        lay = text_layer(lines, kk, sz, col, height=int(sz * 1.45 * len(lines)) + 30, line_gap=1.4)
    cache[key] = lay; return lay


def draw_captions(img, gt, events, cache):
    for ev in events:
        a, b, text, kind = ev[:4]; la = ev[4] if len(ev) > 4 else None
        if not (a <= gt < b): continue
        lay = caption_layer(text, kind, cache); h = lay.shape[0]
        if la:   # 아직 읽지 않은 줄은 가린다 (text_layer 줄 간격 72×1.4)
            lay = lay.copy(); n = len(la); pitch = 72 * 1.4; y0 = (h - n * pitch) / 2
            for li in range(1, n):
                r0 = int(y0 + li * pitch) - 4; r1 = int(y0 + (li + 1) * pitch) - 4 if li < n - 1 else h
                lay[r0:r1, :, 3] = (lay[r0:r1, :, 3] * ease((gt - la[li]) / 0.3)).astype(np.uint8)
        al = ease((gt - a) / 0.18) * (1 - ease((gt - b + 0.18) / 0.18))
        full = np.zeros((H, W, 4), np.uint8)
        if kind == "emph":
            y = int(H * 0.50 - h / 2); full[y:y + h] = lay
            sc = 0.94 + 0.06 * ease((gt - a) / 0.35)
            M = np.float32([[sc, 0, W / 2 * (1 - sc)], [0, sc, (y + h / 2) * (1 - sc)]])
            full = cv2.warpAffine(full, M, (W, H))
            img = (img.astype(np.float32) * (1 - 0.25 * al)).astype(np.uint8)
        else:
            y = H - BAR - 40 - h; full[y:y + h] = lay
        img = blend(img, full, al)
    return img


def caption_events(S, plan, vfile):
    global CAP_SCALE; CAP_SCALE = float(S.get("cap_scale", 1.0))
    subs = S.get("subs", {}); mono = set(S.get("monologue_voices", [])); ev = []
    for p in plan:
        if p["s"].get("nocap"): continue
        for v, at, d in p["voices"]:
            if v in p["s"].get("nocap_voices", []): continue
            items = subs.get(v)
            if not items: continue
            items = [items] if isinstance(items, str) else items
            bounds = speech_bounds(vfile(v), len(items), [x.lstrip("!~") for x in items])
            for txt, (a, b) in zip(items, bounds):
                if txt.startswith("~"): continue
                kind = "emph" if txt.startswith("!") else ("mono" if v in mono else "nar")
                la = None
                if kind == "emph" and len(items) == 1:   # 11/5 대표: 가운데 큰 문구는 낭독에 맞춰 한 줄씩 나타나기
                    ls = wrap_ko(txt.lstrip("!"), font("ko", 72), 1400)
                    if len(ls) > 1: la = [at + b0 - 0.1 for b0, _ in speech_bounds(vfile(v), len(ls), ls)]
                ev.append((at + a - 0.08, at + b + 0.15, txt.lstrip("!"), kind, la))
    return ev


# ---------- 본체 ----------
def build(spec_path, t_from=0.0, t_to=None, preview=False, audio_only=False, chunk=None):
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
        if s["type"] == "intro": d = 10.6 / float(S.get("intro_speed", 1)) + float(S.get("intro_hold", 0))   # 11/9 실화극: 인트로 빠르게
        if s.get("fixed"): d = s["dur"]
        s["_vat"] = {v: a for v, a, dd in vt}   # 장면 안에서 각 목소리가 시작하는 시각 (엔딩 글자 박자 맞추기)
        plan.append({"s": s, "t0": t, "dur": d, "voices": [(v, t + a, dd) for v, a, dd in vt]}); t += d
    total = t
    for p in plan:   # 덧씌우기 시작을 목소리 기준으로
        for ov in p["s"].get("overlays", []):
            if ov.get("at_voice"):
                for v, a, dd in p["voices"]:
                    if v == ov["at_voice"]:
                        ov["at"] = a - p["t0"] + ov.get("offset", -0.2); ov.setdefault("until", ov.get("until_end", p["dur"]))
                        if ov.get("kind") == "verse" and len(ov["lines"]) > 1:   # 11/5 대표: 가운데 문구는 낭독에 맞춰 한 줄씩
                            lb = speech_bounds(vfile(v), len(ov["lines"]), ov["lines"]); ov["line_at"] = [a - p["t0"] + b0 - 0.15 for b0, _ in lb]
    print(f"총 길이 {total:.1f}초, 장면 {len(plan)}개", flush=True)
    json.dump([{"i": i, "type": p["s"]["type"], "t0": round(p["t0"], 2), "dur": round(p["dur"], 2), "src": p["s"].get("src", "")} for i, p in enumerate(plan)],
              open(os.path.join(base, f"plan_{S['id']}.json"), "w"), ensure_ascii=False, indent=0)
    t_to = min(t_to or total, total)
    events = caption_events(S, plan, vfile); capc = {}
    json.dump(events, open(os.path.join(base, f"caps_{S['id']}.json"), "w"), ensure_ascii=False)
    json.dump([{"t0": p["t0"] + ov.get("at", 0), "t1": p["t0"] + ov.get("until", p["dur"]), "lines": ov["lines"], "src": ov.get("src", "")} for p in plan for ov in p["s"].get("overlays", []) if ov.get("kind") == "verse"],
              open(os.path.join(base, f"verses_{S['id']}.json"), "w"), ensure_ascii=False)
    out_dir = P(S.get("out_dir", "_long")); os.makedirs(out_dir, exist_ok=True)
    tag = S["id"] + ("_prev" if preview else "") + S.get("tag_suffix", "")
    vid_path = os.path.join(out_dir, f"{tag}_{chunk}_v.mp4" if chunk else f"{tag}_v.mp4")
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
        if s["type"] == "still": src = Still(os.path.join(gdir, s["src"] + ".jpeg"), s.get("move"), face=s.get("face"))
        elif s["type"] == "video" and s.get("write"): src = WriteClip(os.path.join(gdir, s["src"] + ".mp4"), s.get("move"), s.get("start", 0), s["write"])
        elif s["type"] == "video": src = Clip(os.path.join(gdir, s["src"] + ".mp4"), s.get("move"), s.get("start", 0), face=s.get("face"))
        elif s["type"] == "intro": intro = intro or Intro({**S["intro"], "logo": P(S["intro"]["logo"])})
        parts = Particles(s["particles"]) if s.get("particles") else None
        nfr = int(round(d * FPS)); first = None; lastk = last
        for k in range(nfr):
            tt = k / FPS; gt = t0 + tt
            if gt < t_from or gt >= t_to: continue
            prog = tt / d
            if s["type"] == "black": img = np.zeros((H, W, 3), np.uint8)
            elif s["type"] == "intro":   # 11/10 대표: 로고·부제가 다 보인 순간(9.0초)에 1초 머문다 (spec "intro_hold")
                hd = float(S.get("intro_hold", 0)); ti = tt if tt < 9.0 else (9.0 if tt < 9.0 + hd else tt - hd)
                img = intro.frame(ti * float(S.get("intro_speed", 1)))
            elif s["type"] == "card": img = card_frame(s, tt, d, cache)
            elif s["type"] == "episode": img = episode_frame(s, tt, d, cache)
            elif s["type"] == "outro": img = outro_frame(s, tt, d, cache, P(S["intro"]["logo"]))
            elif s["type"] == "recap" and s.get("cascade"):   # 11/5: 낭독 없이 차례로 떠오르는 목록
                c0, step = s["cascade"]; act = min(int((tt - c0) / step), len(s["items"]) - 1) if tt >= c0 else None
                img = recap_frame(s, tt, d, cache, act)
            elif s["type"] == "recap":
                act = None
                for vi, (vn, va, vd) in enumerate(p["voices"]):
                    if gt >= va - 0.2: act = vi - s.get("recap_offset", 1)
                img = recap_frame(s, tt, d, cache, act if act is not None and act >= 0 else None)
            elif s["type"] == "end": img = end_frame(s, tt, d, cache, P(S["intro"]["logo"]))
            elif s["type"] == "tonight": img = tonight_frame(s, tt, d, cache)
            elif s["type"] == "prev": img = prev_frame(s, tt, d, cache, P)
            elif s["type"] == "endscreen": img = endscreen_frame(s, tt, d, cache)
            elif s["type"] == "finale": img = finale_frame(s, tt, d, cache, P(S["intro"]["logo"]))
            elif s["type"] == "still": img = src.frame(prog)
            elif s["type"] == "video": img = src.frame(prog, tt, d)
            if s.get("flicker") and s["type"] in ("still", "video"):
                fl = 1 + 0.035 * math.sin(tt * 7.1) + 0.025 * math.sin(tt * 13.7 + 1.3)
                img = np.clip(img.astype(np.float32) * fl, 0, 255).astype(np.uint8)
            if parts: img = parts.draw(img, tt)
            if s.get("rack") and tt < s["rack"]:   # 초점이 맞아 들어오는 연출
                sig = 9 * (1 - ease(tt / s["rack"])); img = cv2.GaussianBlur(img, (0, 0), sig) if sig > 0.3 else img
            if s.get("leak"):   # 회상 장면의 따뜻한 빛 번짐
                if "leak" not in cache:
                    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); cache["leak"] = (xx, yy)
                xx, yy = cache["leak"]; cx = W * (0.15 + 0.7 * (0.5 + 0.5 * math.sin(tt * 0.35))); cy = H * 0.3
                g = np.exp(-(((xx - cx) / 520) ** 2 + ((yy - cy) / 380) ** 2))[..., None] * np.array([40, 110, 190], np.float32) * 0.55
                img = np.clip(img.astype(np.float32) + g, 0, 255).astype(np.uint8)
            for oi, ov in enumerate(s.get("overlays", [])):
                if os.environ.get("ED_VERT") and ov.get("kind") in ("verse", "caption"): continue   # 세로 쇼츠 조각: 구절·장소 자막은 세로용으로 따로 얹는다
                img = overlay(img, ov, tt, d, cache, f"ov{oi}")
            if s["type"] in ("still", "video", "black"): img = look.apply(img, s.get("grade"))
            else: img = _bars(img)
            if not os.environ.get("ED_VERT"): img = draw_captions(img, gt, events, capc)
            # 들어오고 나가기
            tin, tout = s.get("tin", "cut"), s.get("tout", "cut")
            if tin == "black": img = (img.astype(np.float32) * ease(tt / s.get("fin", 0.6))).astype(np.uint8)
            if tin == "flash" and tt < 0.7:   # 극적 전환: 금빛 섬광
                fa = math.exp(-tt / 0.16); img = np.clip(img.astype(np.float32) * (1 - 0.3 * fa) + np.array([150, 210, 255], np.float32) * fa, 0, 255).astype(np.uint8)
            if tin == "dissolve" and last is not None and tt < 0.6: a = ease(tt / 0.6); img = cv2.addWeighted(last, 1 - a, img, a, 0)
            if tout == "black": img = (img.astype(np.float32) * (1 - ease((tt - d + s.get("fout", 0.6)) / s.get("fout", 0.6)))).astype(np.uint8)
            if first is None: first = img
            frame = cv2.resize(img, (int(W * scale), int(H * scale)), interpolation=cv2.INTER_AREA) if preview else img
            enc.stdin.write(frame.tobytes()); lastk = img
        last = lastk
        print(f"  장면 {pi} {s['type']} {s.get('src','')} {d:.1f}초 완료", flush=True)
    if enc: enc.stdin.close(); enc.wait()
    if chunk: print("조각 완성", vid_path, flush=True); return vid_path
    # 3) 소리
    for m in S.get("music", []):
        if "at_shot" in m: m["at"] = plan[m["at_shot"]]["t0"] + m.get("offset", 0)
        if "until_shot" in m: m["len"] = (plan[m["until_shot"]]["t0"] if m["until_shot"] < len(plan) else total) - m["at"] + m.get("tail", 2.0)
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
            lab = add(vfile(v), at, S.get("voice_vol", 1.0) * (S.get("voice_gain", {}).get("mono", 1.1) if v in mono else (S.get("voice_gain", {}).get("cast", 1.0) if v in S.get("cast_voices", []) else S.get("voice_gain", {}).get("narr", 1.0))), fx)
            if lab: vo.append(lab)
        s = p["s"]
        if s.get("amb"):
            key, vol = s["amb"]; path = os.path.join(sfx_dir, key)
            L = dur_of(path); d = p["dur"]
            loop = f"aloop=loop={int(d // max(L, 0.1)) + 1}:size={int(48000 * L)}," if L < d else ""
            lab = add(path, p["t0"], vol, f"{loop}atrim=0:{d},afade=t=in:d=0.8,afade=t=out:st={max(d-0.9,0)}:d=0.9,")
            if lab: bg.append(lab)
        for key, at, vol in s.get("sfx", []):
            keep = max(p["dur"] - at + 0.5, 0.6)   # 11/10 대표: 긴 효과음(심장 박동 등)이 장면 뒤까지 웅웅 남지 않게 장면 끝에서 자른다 (spec "sfx_trim")
            lab = add(os.path.join(sfx_dir, key), p["t0"] + at, vol, f"atrim=0:{keep},afade=t=out:st={max(keep - 0.6, 0)}:d=0.6," if S.get("sfx_trim") else "")
            if lab: bg.append(lab)   # 효과음은 덕킹하지 않는 쪽이 낫지만 단순하게 함께 둔다
    for m in S.get("music", []):
        path = os.path.join(mus_dir, m["file"]); length = m.get("len", 60)
        src_len = dur_of(path) - m.get("start", 0)
        loop = f"aloop=loop={int(length // max(src_len, 1)) + 1}:size={int(48000 * dur_of(path))}," if length > src_len else ""
        lab = add(path, m["at"], m["vol"], f"{loop}atrim=start={m.get('start',0)},asetpts=PTS-STARTPTS,atrim=0:{length},afade=t=in:d={m.get('fin',2)},afade=t=out:st={max(length-m.get('fout',3),0)}:d={m.get('fout',3)},")
        if lab: bg.append(lab)
    L = t_to - t_from
    fc = ";".join(flt)
    fc += f";{''.join('['+x+']' for x in vo)}amix=inputs={len(vo)}:normalize=0,apad=whole_dur={L},asplit=2[vo1][vo2]"
    fc += f";{''.join('['+x+']' for x in bg)}amix=inputs={len(bg)}:normalize=0[bgm]"
    fc += ";[bgm][vo2]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600:makeup=1[duck]"
    fc += f";[vo1][duck]amix=inputs=2:normalize=0,apad=whole_dur={L},atrim=0:{L},loudnorm=I=-16:TP=-1.5:LRA=11[out]"
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-ac", "2", os.path.join(out_dir, f"{tag}_a.wav")]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    a = sys.argv[1:]; spec = a[0]
    tf = float(a[a.index("--from") + 1]) if "--from" in a else 0.0
    tt = float(a[a.index("--to") + 1]) if "--to" in a else None
    if "--plan" in a:   # 장면 시작 시각만 출력 (조각 나누기용)
        S = json.load(open(spec)); print("plan only"); build(spec, 0, 0.001, True, True); sys.exit()
    ch = a[a.index("--chunk") + 1] if "--chunk" in a else None
    build(spec, tf, tt, "--preview" in a, "--audio-only" in a, ch)
