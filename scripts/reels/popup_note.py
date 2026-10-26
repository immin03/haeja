"""팝업 노트 (Pop-up Note) 시안 — 밸류노트 고유 영상 포맷 (2026-10-26)

운영자: "노트가 전환되는데 노트 위에 3D로 영상이 보이기도 하고… 밸류노트만의 고유한 영상 기획"
영상 전체가 한 권의 투자 노트다.
  1) 책상 위 닫힌 노트 → 펜이 표지 라벨에 회사 이름을 쓰고 표지가 열린다
  2) 펼친 페이지에서 그 회사의 장면이 팝업북처럼 3D로 솟아오른다 (사진은 카드 안에서 천천히 움직인다)
  3) 금색 펜이 핵심 숫자를 손글씨로 쓴다
  4) 페이지가 넘어가며 다음 장
  5) 마지막 한 줄 노트 → 노트가 닫히고 펜이 표지 로고 아래를 긋고 동그라미 친 뒤 빠진다

진짜 원근(3D 카메라)으로 그린다: 책상은 y=0 평면, 노트 한 쪽 = 가로 1 × 세로 1.4, 책등 x=0.
실행:  python3 scripts/reels/popup_note.py --out OUT_DIR [--stills 1.0,5.5,...]
"""
import argparse, math, os, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FONT = os.path.join(HERE, "fonts")
LIB = os.path.join(ROOT, "scripts", "blog", "media", "lib")
THEME = os.path.join(ROOT, "scripts", "youtube", "long", "assets", "theme.mp3")

W, H, FPS = 1080, 1920, 30
TW, TH = 1000, 1400                    # 노트 한 쪽 텍스처 크기 (px)
PW, PD = 1.0, 1.4                      # 노트 한 쪽 크기 (월드)
TK = 0.035                             # 노트 한쪽 두께

NAVY = (16, 30, 58); IVORY = (243, 236, 221); INK = (22, 36, 70)
GOLD = (232, 196, 120); GOLD_D = (176, 134, 62); RED = (255, 77, 109); GREEN = (61, 245, 160)


def F(name, size):
    return ImageFont.truetype(os.path.join(FONT, name), size)


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eio(t): t = clamp(t); return t * t * (3 - 2 * t)
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def lerp(a, b, p): return a + (b - a) * p
def seg(T, t0, t1): return clamp((T - t0) / (t1 - t0)) if t1 > t0 else float(T >= t1)


# ═══════════════ 카메라 ═══════════════
class Cam:
    def __init__(self, pos, tgt, fov=38.0, roll=0.0):
        self.p = np.array(pos, float); t = np.array(tgt, float)
        fw = t - self.p; fw /= np.linalg.norm(fw)
        up = np.array([0.0, 1.0, 0.0])
        rt = np.cross(up, fw); rt /= np.linalg.norm(rt)
        cu = np.cross(fw, rt)
        if roll:
            a = math.radians(roll); rt, cu = rt * math.cos(a) + cu * math.sin(a), -rt * math.sin(a) + cu * math.cos(a)
        self.R = np.stack([rt, cu, fw]); self.f = (H / 2) / math.tan(math.radians(fov) / 2)

    def proj(self, P):
        P = np.atleast_2d(np.asarray(P, float)); d = (P - self.p) @ self.R.T
        z = np.maximum(d[:, 2], 1e-3)
        return np.stack([W / 2 + self.f * d[:, 0] / z, H / 2 - self.f * d[:, 1] / z], 1), d[:, 2]

    def depth(self, P):
        return float(((np.asarray(P, float) - self.p) @ self.R[2]))


# 카메라 키프레임: (시각, 바라보는 점, 좌우 각도, 내려다보는 각도, 거리, 화각, 기울기)
KEYS = [
    (0.0, (0.50, 0.0, 0.05), -16, 48, 3.75, 38, -3),
    (0.8, (0.50, 0.0, -0.10), -7, 58, 3.05, 38, -2),     # 펜이 라벨에 이름을 쓴다
    (2.5, (0.50, 0.0, -0.10), -3, 60, 2.95, 38, -1),
    (4.0, (0.05, 0.05, 0.00), -10, 50, 4.30, 40, 0),     # 표지 열리며 물러남
    (5.5, (0.50, 0.24, 0.12), 20, 23, 3.35, 40, 2),      # 팝업 쪽으로 낮게
    (7.1, (0.50, 0.24, 0.12), -16, 28, 3.35, 40, -2),    # 팝업 둘레를 돈다
    (8.0, (-0.50, 0.0, -0.02), 0, 60, 3.10, 38, 0),      # 왼쪽 페이지
    (9.9, (-0.50, 0.0, -0.02), 3, 61, 3.05, 38, 1),
    (10.6, (0.00, 0.0, 0.05), 0, 58, 4.70, 40, 0),       # 펼친 노트 전체 (접고 넘김)
    (12.0, (0.02, 0.0, 0.05), 0, 59, 4.55, 40, 0),
    (12.8, (0.50, 0.0, 0.02), 4, 60, 3.05, 38, 1),       # 오른쪽 페이지 (-10%)
    (16.9, (0.50, 0.0, -0.02), 0, 61, 3.05, 38, 0),
    (17.6, (0.50, 0.0, -0.16), -3, 62, 3.35, 38, -1),    # 한 줄 노트
    (19.6, (0.50, 0.0, -0.16), -1, 62, 3.35, 38, 0),
    (20.9, (0.50, 0.0, 0.00), -6, 56, 3.30, 38, -2),     # 닫힌 표지
    (23.6, (0.50, 0.0, 0.02), -2, 60, 3.00, 37, -1),
]


def _cam(tgt, yaw, pitch, dist, fov, roll):
    y, p = math.radians(yaw), math.radians(pitch)
    pos = (tgt[0] + dist * math.cos(p) * math.sin(y), tgt[1] + dist * math.sin(p), tgt[2] - dist * math.cos(p) * math.cos(y))
    return Cam(pos, tgt, fov, roll)


def camera(T):
    for i in range(len(KEYS) - 1):
        a, b = KEYS[i], KEYS[i + 1]
        if a[0] <= T < b[0]:
            q = eio((T - a[0]) / (b[0] - a[0]))
            tgt = [lerp(a[1][j], b[1][j], q) for j in range(3)]
            return _cam(tgt, *[lerp(a[k], b[k], q) for k in range(2, 7)])
    k = KEYS[-1]
    return _cam(k[1], *k[2:])


# ═══════════════ 그리기 기본 ═══════════════
def draw_quad(fr, tex, dst, shade=1.0, alpha=1.0):
    """tex(RGB 또는 RGBA, uint8) 전체를 화면 사각형 dst(4x2: 위왼·위오·아래오·아래왼)에 원근으로 붙인다"""
    th, tw = tex.shape[:2]
    x0 = int(max(0, math.floor(dst[:, 0].min()) - 2)); x1 = int(min(W, math.ceil(dst[:, 0].max()) + 2))
    y0 = int(max(0, math.floor(dst[:, 1].min()) - 2)); y1 = int(min(H, math.ceil(dst[:, 1].max()) + 2))
    if x1 <= x0 or y1 <= y0: return
    src = np.float32([[0, 0], [tw, 0], [tw, th], [0, th]])
    d = np.float32(dst - [x0, y0])
    M = cv2.getPerspectiveTransform(src, d)
    wp = cv2.warpPerspective(tex, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillConvexPoly(m, np.int32(np.round(d * 16)), 255, lineType=cv2.LINE_AA, shift=4)
    m = m.astype(np.float32) / 255 * alpha
    if wp.shape[2] == 4:
        m *= wp[..., 3].astype(np.float32) / 255; wp = wp[..., :3]
    m = m[..., None]; reg = fr[y0:y1, x0:x1]
    reg[:] = reg * (1 - m) + wp.astype(np.float32) * shade * m


def fill_poly(fr, pts, color, alpha=1.0, blur=0):
    x0 = int(max(0, pts[:, 0].min() - 3 - blur * 3)); x1 = int(min(W, pts[:, 0].max() + 3 + blur * 3))
    y0 = int(max(0, pts[:, 1].min() - 3 - blur * 3)); y1 = int(min(H, pts[:, 1].max() + 3 + blur * 3))
    if x1 <= x0 or y1 <= y0: return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillPoly(m, [np.int32(np.round((pts - [x0, y0]) * 16))], 255, lineType=cv2.LINE_AA, shift=4)
    m = m.astype(np.float32) / 255
    if blur: m = cv2.GaussianBlur(m, (0, 0), blur)
    m = (m * alpha)[..., None]; reg = fr[y0:y1, x0:x1]
    reg[:] = reg * (1 - m) + np.array(color, np.float32) * m


# ═══════════════ 텍스처 ═══════════════
_C = {}


def desk_tex():
    if "desk" in _C: return _C["desk"]
    S = 2048; rng = np.random.default_rng(5)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    # 책상 텍스처는 z 11(위) ~ -3.5(아래), x -7 ~ 8 을 덮는다
    g = np.zeros((S, S, 3), np.float32) + np.array([12, 24, 46], np.float32)
    grain = (np.sin(yy / 9.0 + np.sin(xx / 210.0) * 3.2) * .5 + .5) * 6 + rng.normal(0, 2.0, (S, S))
    g += grain[..., None] * np.array([.55, .7, 1.0])
    cx, cy = S * 7.3 / 15, S * 10.6 / 14.5      # 노트가 놓인 자리 (월드 0.3, 0.4)
    r = np.sqrt(((xx - cx) / S) ** 2 + ((yy - cy) / S) ** 2)
    g += (np.clip(.28 - r, 0, 1) * 120)[..., None] * np.array([.55, .72, 1.0])
    g *= np.clip(.35 + yy / S * .9, .35, 1.0)[..., None]      # 멀어질수록 어둡게
    im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")   # 커피 컵 자국 (스타벅스 편 소품)
    for k in range(3):
        d.ellipse([1180 - k, 1640 - k, 1290 + k, 1750 + k], outline=(90, 70, 52, 60 - k * 15), width=5)
    _C["desk"] = np.asarray(im)
    return _C["desk"]


def paper_base(seed=0, stain=False):
    rng = np.random.default_rng(seed)
    a = np.zeros((TH, TW, 3), np.float32) + np.array(IVORY, np.float32)
    a += rng.normal(0, 2.2, (TH, TW, 1))
    yy, xx = np.mgrid[0:TH, 0:TW]
    a -= (np.clip(((xx - TW / 2) / TW) ** 2 + ((yy - TH / 2) / TH) ** 2 - .12, 0, 1) * 40)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, "RGBA")
    for y in range(110, TH - 60, 44):              # 점 모눈 (스타벅스 편 look: dots)
        for x in range(60, TW - 40, 44):
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(150, 160, 178, 120))
    if stain:
        for k in range(4):
            d.ellipse([700 - k * 2, 1080 - k * 2, 940 + k * 2, 1320 + k * 2], outline=(150, 110, 70, 70 - k * 14), width=9)
    return im


def ptxt(d, xy, s, font, fill, anchor="la"):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def tex_L1():
    im = paper_base(1); d = ImageDraw.Draw(im, "RGBA")
    ptxt(d, (70, 60), "STARBUCKS · SBUX", F("Montserrat-ExtraBold.ttf", 34), (*INK, 200))
    ptxt(d, (70, 190), "손님이 앱과 카드에 넣어 두고", F("SUIT-Bold.ttf", 52), INK)
    ptxt(d, (70, 262), "아직 쓰지 않은 돈", F("SUIT-Bold.ttf", 52), INK)
    ptxt(d, (70, 760), "약 2조 3천억 원", F("SUIT-ExtraBold.ttf", 64), (*INK, 235))
    ptxt(d, (70, 848), "2025년 9월 기준 · 스타벅스 연차보고서", F("SUIT-Medium.ttf", 34), (*INK, 150))
    ptxt(d, (TW - 70, TH - 70), "1", F("SUIT-Medium.ttf", 30), (*INK, 120), "ra")
    return im


def tex_R1():
    im = paper_base(2); d = ImageDraw.Draw(im, "RGBA")
    ptxt(d, (70, 60), "1974 · PIKE PLACE, SEATTLE", F("Montserrat-ExtraBold.ttf", 30), (*INK, 160))
    ptxt(d, (TW - 70, TH - 70), "2", F("SUIT-Medium.ttf", 30), (*INK, 120), "ra")
    return im


def tex_L2():
    im = paper_base(3); d = ImageDraw.Draw(im, "RGBA")
    ptxt(d, (70, 60), "왜 줄었나", F("SUIT-ExtraBold.ttf", 40), (*INK, 210))
    ph = Image.open(os.path.join(LIB, "commons_mobileorder_2.jpg")).convert("RGB")
    ph = crop_to(ph, 760, 860); fr = Image.new("RGB", (800, 960), (250, 248, 242)); fr.paste(ph, (20, 20))
    dd = ImageDraw.Draw(fr); ptxt(dd, (400, 912), "모바일 주문 픽업대", F("SUIT-Bold.ttf", 34), INK, "mm")
    fr = fr.rotate(-3.2, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0))
    m = Image.new("L", (800, 960), 255).rotate(-3.2, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.rectangle([110, 230, 110 + fr.width - 20, 230 + fr.height - 20], fill=(40, 30, 20, 90))
    im.paste(Image.alpha_composite(im.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(14))).convert("RGB"))
    im.paste(fr, (90, 200), m)
    d = ImageDraw.Draw(im, "RGBA")
    for (x, y, r) in ((300, 205, -8), (720, 215, 10)):     # 마스킹 테이프
        tp = Image.new("RGBA", (190, 60), (236, 222, 190, 200)).rotate(r, expand=True)
        im.paste(tp, (x - tp.width // 2, y - tp.height // 2), tp)
    ptxt(d, (TW - 70, TH - 70), "3", F("SUIT-Medium.ttf", 30), (*INK, 120), "ra")
    return im


CUPS = [(110 + i * 82, 860) for i in range(10)]


def tex_R2():
    im = paper_base(4, stain=True); d = ImageDraw.Draw(im, "RGBA")
    ptxt(d, (70, 60), "미국 매장 결제 횟수", F("SUIT-ExtraBold.ttf", 46), INK)
    ptxt(d, (70, 128), "2024년 7~9월 · 1년 전과 비교", F("SUIT-Medium.ttf", 34), (*INK, 160))
    for (x, y) in CUPS:                                  # 컵 10개 = 손님 10명
        d.polygon([(x, y), (x + 54, y), (x + 46, y + 92), (x + 8, y + 92)], outline=(*INK, 210), width=4)
        d.rectangle([x - 4, y - 14, x + 58, y], outline=(*INK, 210), width=4)
        d.line([(x + 5, y + 34), (x + 49, y + 34)], fill=(*INK, 150), width=3)
    ptxt(d, (70, 990), "10명이 오던 매장에", F("SUIT-Bold.ttf", 36), (*INK, 190))
    ptxt(d, (TW - 70, TH - 70), "4", F("SUIT-Medium.ttf", 30), (*INK, 120), "ra")
    return im


def tex_cover():
    S = (TW, TH); rng = np.random.default_rng(9)
    a = np.zeros((TH, TW, 3), np.float32) + np.array([19, 34, 66], np.float32)
    n = cv2.GaussianBlur(rng.normal(0, 1, (TH, TW)).astype(np.float32), (0, 0), 1.2) * 7
    a += n[..., None] * np.array([.6, .75, 1.0])
    yy, xx = np.mgrid[0:TH, 0:TW]
    a += (np.clip(.45 - np.sqrt(((xx - TW * .4) / TW) ** 2 + ((yy - TH * .35) / TH) ** 2), 0, 1) * 30)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([46, 46, TW - 46, TH - 46], 24, outline=(*GOLD, 120), width=3)
    # 로고: Value(흰) + Note(아이보리) / 금선 / 밸류노트
    f = F("Montserrat-ExtraBold.ttf", 132); wv = f.getlength("Value"); wn = f.getlength("Note"); x = TW / 2 - (wv + wn) / 2
    ptxt(d, (x, 470), "Value", f, (255, 255, 255)); ptxt(d, (x + wv, 470), "Note", f, IVORY)
    d.line([(TW / 2 - 300, 640), (TW / 2 + 300, 640)], fill=(*GOLD, 255), width=4)
    ptxt(d, (TW / 2, 702), "밸류노트", F("SUIT-ExtraBold.ttf", 66), IVORY, "mm")
    ptxt(d, (TW / 2, 150), "INVESTMENT NOTE  No.01", F("Montserrat-ExtraBold.ttf", 30), (*GOLD, 200), "mm")
    # 라벨 (펜이 회사 이름을 쓴다)
    d.rounded_rectangle([200, 960, TW - 200, 1170], 14, fill=(*IVORY, 255))
    d.line([(240, 1130), (TW - 240, 1130)], fill=(*INK, 70), width=2)
    return im


def crop_to(im, w, h, fx=.5, fy=.5, zoom=1.0):
    r = w / h; iw, ih = im.size
    cw, ch = (ih * r, ih) if iw / ih > r else (iw, iw / r)
    cw /= zoom; ch /= zoom
    x0 = (iw - cw) * fx; y0 = (ih - ch) * fy
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.LANCZOS)


# ═══════════════ 손글씨 · 펜 표시 ═══════════════
class Write:
    """페이지 텍스처 위 손글씨. 왼쪽에서 오른쪽으로 써 나간다"""
    def __init__(self, page, t0, t1, text, xy, size, color, lines=None):
        self.page, self.t0, self.t1 = page, t0, t1
        f = F("NanumPenScript-Regular.ttf", size)
        rows = lines or [text]
        lh = int(size * 1.02); wmax = int(max(f.getlength(r) for r in rows)) + 40
        lay = Image.new("RGBA", (wmax, lh * len(rows) + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for i, r in enumerate(rows): d.text((10, 6 + i * lh), r, font=f, fill=(*color, 255))
        self.lay = np.asarray(lay); self.xy = xy; self.lh = lh; self.rows = rows
        self.ws = [f.getlength(r) for r in rows]

    def reveal(self, T):
        return seg(T, self.t0, self.t1)

    def apply(self, tex, T):
        p = self.reveal(T)
        if p <= 0: return
        h, w = self.lay.shape[:2]; tot = sum(self.ws); done = p * tot
        m = np.zeros((h, w), np.float32)
        for i, rw in enumerate(self.ws):
            take = clamp(done / rw) if rw else 1; done -= rw
            if take <= 0: break
            xe = 10 + take * rw
            xs = np.arange(w, dtype=np.float32)
            m[6 + i * self.lh - 6:6 + (i + 1) * self.lh + 6] = np.clip((xe - xs) / 10 + 1, 0, 1)[None, :] if take < 1 else 1
        a = self.lay[..., 3].astype(np.float32) / 255 * m
        x, y = self.xy; reg = tex[y:y + h, x:x + w]
        aa = a[:reg.shape[0], :reg.shape[1], None]
        reg[:] = reg * (1 - aa) + self.lay[:reg.shape[0], :reg.shape[1], :3] * aa

    def tip(self, T):
        p = self.reveal(T); tot = sum(self.ws); done = p * tot
        for i, rw in enumerate(self.ws):
            if done <= rw or i == len(self.ws) - 1:
                x = self.xy[0] + 10 + min(done, rw); y = self.xy[1] + 6 + i * self.lh + self.lh * .72
                return (x, y + 7 * math.sin(T * 38))
            done -= rw


class Stroke:
    """페이지 위 펜 선 (밑줄·동그라미·X)"""
    def __init__(self, page, t0, t1, pts, color, width=9):
        self.page, self.t0, self.t1, self.color, self.width = page, t0, t1, color, width
        self.pts = np.array(pts, np.float32)
        dl = np.r_[0, np.cumsum(np.hypot(*np.diff(self.pts, axis=0).T))]; self.cum = dl / dl[-1]

    def reveal(self, T): return seg(T, self.t0, self.t1)

    def upto(self, p):
        k = int(np.searchsorted(self.cum, p))
        if k <= 0: return self.pts[:1]
        k = min(k, len(self.pts) - 1); a, b = self.pts[k - 1], self.pts[k]
        f = (p - self.cum[k - 1]) / max(self.cum[k] - self.cum[k - 1], 1e-6)
        return np.vstack([self.pts[:k], a + (b - a) * f])

    def apply(self, tex, T):
        p = self.reveal(T)
        if p <= 0: return
        q = self.upto(eio(p))
        if len(q) >= 2:
            cv2.polylines(tex, [np.int32(np.round(q * 8))], False, self.color, self.width, cv2.LINE_AA, shift=3)

    def tip(self, T): return tuple(self.upto(eio(self.reveal(T)))[-1])


def ellipse_pts(cx, cy, rx, ry, start=200, sweep=390, n=80):
    out = []
    for i in range(n + 1):
        th = math.radians(start + sweep * i / n); w = 1 + .035 * math.sin(3 * th + .4)
        out.append((cx + rx * w * math.cos(th), cy + ry * w * math.sin(th)))
    return out


def under_pts(x0, x1, y, n=30):
    return [(x0 + (x1 - x0) * i / n, y + 5 * math.sin(i / n * math.pi) - 4 * i / n) for i in range(n + 1)]


# ═══════════════ 장면 설계 (스타벅스) ═══════════════
T_END = 23.6
COVER_OPEN = (2.6, 4.0)       # 표지 열림
FOLD = (10.0, 10.6)           # 팝업 접힘
FLIP = (10.6, 11.9)           # 페이지 넘김
CLOSE = (19.7, 21.0)          # 노트 닫힘

INKS = [
    Write("cover", 0.7, 2.3, "Starbucks", (250, 990), 150, INK),
    Write("L1", 7.7, 9.5, "17억 5천만 달러", (60, 420), 160, INK),
    Stroke("L1", 9.5, 9.95, under_pts(80, 900, 640), GOLD_D, 10),
    Write("R2", 12.9, 14.3, "-10%", (330, 230), 330, RED),
    Stroke("R2", 15.5, 15.75, [(838, 852), (900, 958)], RED, 11),
    Stroke("R2", 15.75, 16.0, [(900, 852), (838, 958)], RED, 11),
    Write("R2", 16.1, 16.9, "9명만 왔다", (430, 975), 92, RED),
    Write("R2", 17.6, 19.4, "", (70, 1105), 96, INK, lines=["앱이 빨라질수록,", "매장은 느려졌다"]),
    Stroke("cover", 21.2, 21.75, under_pts(TW / 2 - 330, TW / 2 + 330, 668), GOLD, 10),
    Stroke("cover", 21.75, 22.55, ellipse_pts(TW / 2, 600, 400, 175, start=25), GOLD, 9),
]
PEN_EXIT = 22.6

SUBS = [
    (0.3, 2.6, "스타벅스에는 손님이 맡겨 둔 돈이 있습니다."),
    (2.6, 7.4, "앱과 카드에 충전해 두고 아직 안 쓴 돈입니다."),
    (7.4, 10.1, "무려 17억 5천만 달러입니다."),
    (10.1, 12.6, "그런데 이 앱이 손님을 줄게 만들었습니다."),
    (12.6, 15.3, "2024년 여름, 미국 매장 결제 횟수 -10%."),
    (15.3, 17.4, "열 명 오던 매장에 아홉 명만 온 겁니다."),
    (17.4, 19.7, "앱 주문이 몰리자 매장이 느려졌기 때문입니다."),
    (19.7, T_END, "다시 손님을 늘린 방법은 풀버전에서."),
]


# ═══════════════ 페이지 위치 ═══════════════
def page_world(side, u, v, y=None):
    """정적인 페이지의 텍스처 좌표(u,v px) → 월드. side: 'R'(오른쪽) 'L'(왼쪽)"""
    x0 = 0.0 if side == "R" else -PW
    return np.array([x0 + u / TW * PW, TK + 0.002 if y is None else y, PD / 2 - v / TH * PD])


def page_corners(side, y):
    x0 = 0.0 if side == "R" else -PW
    return np.array([[x0, y, PD / 2], [x0 + PW, y, PD / 2], [x0 + PW, y, -PD / 2], [x0, y, -PD / 2]])


def sheet_strips(theta, curl, y0, n=22):
    """책등(x=0, y=y0)에서 각도 theta(0=오른쪽에 누움, π=왼쪽에 누움)로 넘어가는 종이를 n개 띠로.
    반환: 띠별 (s0, s1, 안쪽 점, 바깥쪽 점) — s 는 책등에서의 거리(0~PW)"""
    k = curl * math.sin(theta)                    # 넘기는 중일수록 끝이 늦게 따라온다
    pts = [(0.0, y0)]; x, y = 0.0, y0; ds = PW / n
    for i in range(n):
        s = (i + .5) * ds; a = theta - k * (s / PW) ** 1.3 * (1 if theta < math.pi / 2 else 1)
        a = clamp(a, 0, math.pi)
        x += math.cos(a) * ds; y += math.sin(a) * ds
        pts.append((x, max(y, y0)))
    return pts


def draw_sheet(fr, cam, theta, texA, texB, curl=.55, y0=None, n=22):
    """texA: 오른쪽에 누워 있을 때 위로 보이는 면, texB: 왼쪽에 누웠을 때 위로 보이는 면"""
    y0 = TK + 0.004 if y0 is None else y0
    if theta <= 1e-4 or theta >= math.pi - 1e-4:   # 다 누웠으면 띠 없이 한 장으로 (이음선 없음)
        side, tex = ("R", texA) if theta <= 1e-4 else ("L", texB)
        sp, _ = cam.proj(page_corners(side, y0)); draw_quad(fr, np.asarray(tex), sp); return
    pts = sheet_strips(theta, curl, y0, n)
    tA = np.asarray(texA); tB = np.asarray(texB); items = []
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        if i < n - 1:   # 띠를 조금씩 겹쳐 이음선이 보이지 않게
            xb, yb = xb + (xb - xa) * .18, yb + (yb - ya) * .18
        P = np.array([[xa, ya, PD / 2], [xb, yb, PD / 2], [xb, yb, -PD / 2], [xa, ya, -PD / 2]])
        nrm = np.array([-(yb - ya), (xb - xa), 0.0]); nrm /= np.linalg.norm(nrm) + 1e-9   # A 면 법선
        view = cam.p - P.mean(0); facingA = float(nrm @ view) > 0
        ua, ub = int(i / n * TW), min(TW, int((i + 1.18 if i < n - 1 else i + 1) / n * TW))
        if facingA:
            tex = tA[:, ua:ub]; dst = P
        else:
            tex = tB[:, TW - ub:TW - ua]; dst = P[[1, 0, 3, 2]]
        light = abs(float(nrm @ np.array([-.35, .9, -.25]))); shade = .72 + .3 * light
        items.append((cam.depth(P.mean(0)), tex, dst, shade))
    for dep, tex, dst, shade in sorted(items, key=lambda z: -z[0]):
        sp, _ = cam.proj(dst)
        draw_quad(fr, np.ascontiguousarray(tex), sp, shade)


def block(fr, cam, side, h):
    """페이지 묶음의 두께(앞면·바깥 옆면)"""
    if h <= 1e-4: return
    x0, x1 = (0.0, PW) if side == "R" else (-PW, 0.0)
    near = np.array([[x0, 0, -PD / 2], [x1, 0, -PD / 2], [x1, h, -PD / 2], [x0, h, -PD / 2]])
    xo = x1 if side == "R" else x0
    outer = np.array([[xo, 0, -PD / 2], [xo, 0, PD / 2], [xo, h, PD / 2], [xo, h, -PD / 2]])
    for poly, c in ((outer, (214, 204, 182)), (near, (226, 216, 194))):
        sp, z = cam.proj(poly)
        if (z > 0).all(): fill_poly(fr, sp, c)
    sp, _ = cam.proj(near)
    for k in range(1, 5):   # 종이 결 줄
        a = sp[3] + (sp[0] - sp[3]) * k / 5; b = sp[2] + (sp[1] - sp[2]) * k / 5
        cv2.line(fr, tuple(np.int32(a)), tuple(np.int32(b)), (190, 180, 160), 1, cv2.LINE_AA)


# ═══════════════ 팝업 카드 ═══════════════
_PH = {}


def card_store(T):
    if "pike" not in _PH: _PH["pike"] = Image.open(os.path.join(LIB, "commons_sbuxpike_1.jpg")).convert("RGB")
    z = 1.04 + .07 * seg(T, 4.0, 10.0)
    ph = crop_to(_PH["pike"], 860, 600, .45 + .06 * seg(T, 4, 10), .42, z)
    c = Image.new("RGBA", (900, 640), (250, 247, 240, 255)); c.paste(ph, (20, 20))
    return np.asarray(c)


def card_phone(T):
    """앱 주문이 쌓이는 휴대폰 카드 (실제 앱 화면을 흉내 내지 않은 밸류노트 그림)"""
    im = Image.new("RGBA", (420, 800), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 419, 799], 56, fill=(14, 22, 40, 255), outline=(*GOLD, 255), width=5)
    d.rounded_rectangle([22, 60, 397, 770], 30, fill=(24, 40, 74, 255))
    d.rounded_rectangle([160, 22, 260, 38], 8, fill=(40, 52, 80, 255))
    ptxt(d, (210, 112), "모바일 주문", F("SUIT-ExtraBold.ttf", 40), IVORY, "mm")
    n = 3 + int(7 * seg(T, 4.6, 9.5))
    for i in range(min(n, 7)):
        y = 170 + i * 82
        d.rounded_rectangle([44, y, 376, y + 66], 14, fill=(36, 58, 100, 255))
        ptxt(d, (64, y + 33), f"#{118 + i}", F("Montserrat-ExtraBold.ttf", 28), GOLD, "lm")
        ptxt(d, (356, y + 33), "픽업 대기", F("SUIT-Bold.ttf", 26), (*IVORY, 230), "rm")
    return np.asarray(im)


def popups(T):
    """(텍스처, 경첩 x0, x1, 경첩 z, 높이, 각도φ). φ: 0=페이지에 누움, 90=수직"""
    up = 1 - seg(T, *FOLD)
    a1 = 84 * eout(seg(T, 4.15, 5.35)) * up
    a2 = 80 * eout(seg(T, 4.75, 5.85)) * up
    out = []
    if a1 > 0: out.append((card_store(T), .07, .93, .30, .60, a1))
    if a2 > 0: out.append((card_phone(T), .58, .86, -.22, .53, a2))
    return out


# ═══════════════ 펜 ═══════════════
def ink_world(it, T):
    u, v = it.tip(T)
    if it.page == "cover": return page_world("R", u, v, TK + 0.008)
    side = it.page[0]
    return page_world(side, u, v)


def pen_state(T):
    """(월드 위치, 들림 정도 0~1, 보이는지 alpha)"""
    acts = sorted(INKS, key=lambda i: i.t0)
    for it in acts:
        if it.t0 <= T <= it.t1: return ink_world(it, T), 0.0, 1.0
    prev = [i for i in acts if i.t1 < T]; nxt = [i for i in acts if i.t0 > T]
    if T >= PEN_EXIT:
        p = ink_world(acts[-1], acts[-1].t1); q = seg(T, PEN_EXIT, PEN_EXIT + .5)
        return p + np.array([.55, .45, .25]) * eio(q), eio(q), 1 - q
    if not prev:
        p = ink_world(nxt[0], nxt[0].t0); q = seg(T, 0.05, nxt[0].t0)
        return p + np.array([.6, .5, -.2]) * (1 - eio(q)), 1 - eio(q), eio(q / .4)
    a = prev[-1]; pa = ink_world(a, a.t1)
    if not nxt: return pa, 0.25, 1.0
    b = nxt[0]; gap = b.t0 - a.t1
    if gap > 2.0:   # 쉬는 동안 펜은 화면 밖으로 빠졌다가 다음 글자 자리로 들어온다
        off = np.array([.95, .75, -.35]); pb = ink_world(b, b.t0)
        qo = eio(seg(T, a.t1, a.t1 + .6)); qi = eio(seg(T, b.t0 - .8, b.t0))
        if T < b.t0 - .8: return pa + off * qo, qo, 1 - qo
        return pb + off * (1 - qi), 1 - qi, qi
    # 넘김·닫힘 중에는 펜이 노트 위에서 비켜난다
    away = any(s0 - .1 < T < s1 + .1 for s0, s1 in (FOLD, FLIP, CLOSE, COVER_OPEN))
    q = eio(seg(T, a.t1 + max(0, gap - 1.1), b.t0)); pb = ink_world(b, b.t0)
    p = pa + (pb - pa) * q; lift = math.sin(math.pi * q) * .9
    if away or gap > 2.0:
        p = p + np.array([.0, .35, -.1]); lift = max(lift, .9)
    return p, clamp(lift), 1.0


def draw_pen(fr, cam, T):
    P, lift, al = pen_state(T)
    if al <= .01: return
    P = P + np.array([0, .05 * lift, 0])
    tip = cam.proj(P)[0][0]; dep = cam.depth(P)
    sc = cam.f * .55 / max(dep, .3) / 600 * 1.0
    L = 470 * sc; ang = math.radians(-58); dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    def poly(off=(0, 0)):
        t = np.array(tip) + off
        nib = [t, t + np.array([dx, dy]) * L * .13 + np.array([nx, ny]) * L * .028, t + np.array([dx, dy]) * L * .13 - np.array([nx, ny]) * L * .028]
        b0 = t + np.array([dx, dy]) * L * .12; b1 = t + np.array([dx, dy]) * L
        r0, r1 = L * .036, L * .042
        body = [b0 + np.array([nx, ny]) * r0, b1 + np.array([nx, ny]) * r1, b1 - np.array([nx, ny]) * r1, b0 - np.array([nx, ny]) * r0]
        return np.array(nib), np.array(body), b0, b1, r0, r1
    so = np.array([40, 52]) * (1 + 2.2 * lift) * sc
    nib, body, *_ = poly(so)
    fill_poly(fr, np.vstack([nib, body]), (0, 0, 0), .32 * al * (1 - .4 * lift), blur=6 + 10 * lift)
    nib, body, b0, b1, r0, r1 = poly()
    fill_poly(fr, nib, (205, 165, 90), al)
    fill_poly(fr, body, (24, 30, 46), al)
    hl = np.array([b0 + np.array([nx, ny]) * r0 * .45, b1 + np.array([nx, ny]) * r1 * .45, b1 + np.array([nx, ny]) * r1 * .15, b0 + np.array([nx, ny]) * r0 * .15])
    fill_poly(fr, hl, (90, 104, 140), .55 * al)
    for f in (.16, .70, .74):   # 금색 띠
        c = b0 + (b1 - b0) * f; w_ = L * .016
        band = np.array([c + np.array([nx, ny]) * r1 * 1.05, c + np.array([nx, ny]) * r1 * 1.05 + np.array([dx, dy]) * w_,
                         c - np.array([nx, ny]) * r1 * 1.05 + np.array([dx, dy]) * w_, c - np.array([nx, ny]) * r1 * 1.05])
        fill_poly(fr, band, GOLD, al)
    cl = np.array([b0 + (b1 - b0) * .74 + np.array([nx, ny]) * r1 * 1.15, b0 + (b1 - b0) * .97 + np.array([nx, ny]) * r1 * 1.15,
                   b0 + (b1 - b0) * .97 + np.array([nx, ny]) * r1 * .7, b0 + (b1 - b0) * .74 + np.array([nx, ny]) * r1 * .7])
    fill_poly(fr, cl, GOLD, al)


# ═══════════════ 화면 고정 요소 ═══════════════
def overlay(fr, T):
    im = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    g = np.zeros((H, 1), np.float32); g[:520, 0] = np.clip(1 - np.arange(520) / 520, 0, 1) ** 1.3 * 215
    g[1380:, 0] = np.clip((np.arange(H - 1380)) / 380, 0, 1) ** 1.4 * 200
    grad = Image.fromarray(np.repeat(g, W, 1).astype(np.uint8), "L")
    ov.paste(Image.new("RGBA", (W, H), (8, 16, 32, 255)), (0, 0), grad)
    ft = F("SUIT-Heavy.ttf", 74)
    for i, (s, c) in enumerate((("스타벅스 손님을 줄인 원인", (255, 255, 255)), ("앱이었다?", GOLD))):
        d.text((W / 2 + 3, 196 + i * 100 + 4), s, font=ft, fill=(0, 0, 0, 150), anchor="mm")
        d.text((W / 2, 196 + i * 100), s, font=ft, fill=(*c, 255), anchor="mm")
    sub = next((s for a, b, s in SUBS if a <= T < b), None)
    if sub:
        fs = F("SUIT-ExtraBold.ttf", 52)
        for dx, dy in ((0, 4),): d.text((W / 2 + dx, 1640 + dy), sub, font=fs, fill=(0, 0, 0, 170), anchor="mm")
        d.text((W / 2, 1640), sub, font=fs, fill=(255, 255, 255, 255), anchor="mm")
    p = T / T_END; d.rectangle([0, H - 8, W * p, H], fill=(*GOLD, 220))
    return np.asarray(Image.alpha_composite(im, ov).convert("RGB"))


# ═══════════════ 한 프레임 ═══════════════
_BASE = {}


def bases():
    if not _BASE:
        _BASE.update(cover=tex_cover(), L1=tex_L1(), R1=tex_R1(), L2=tex_L2(), R2=tex_R2())
        _BASE["blank"] = paper_base(7)
    return _BASE


def tex_now(name, T):
    B = bases(); a = np.asarray(B[name]).copy()
    for it in INKS:
        if it.page == name: it.apply(a, T)
    return a


def bake_popups_flat(texR1, T):
    """접힌 팝업 카드를 오른쪽 페이지 그림에 눌러 붙인다 (넘길 때 같이 넘어가게)"""
    im = Image.fromarray(texR1)
    for tex, x0, x1, zh, hgt, ang in [(card_store(T), .07, .93, .30, .60, 0), (card_phone(T), .58, .86, -.22, .53, 0)]:
        c = Image.fromarray(tex); w = int((x1 - x0) * TW); h = int(hgt / PD * TH)
        c = c.resize((w, h), Image.LANCZOS)
        v_h = int((PD / 2 - zh) / PD * TH)          # 경첩 줄 (카드는 경첩에서 먼 쪽으로 눕는다)
        im.paste(c, (int(x0 * TW), v_h - h), c if c.mode == "RGBA" else None)
    return np.asarray(im)


def frame(T):
    cam = camera(T)
    fr = np.zeros((H, W, 3), np.float32)
    # 책상
    dp = np.array([[-7.0, 0, 11.0], [8.0, 0, 11.0], [8.0, 0, -3.5], [-7.0, 0, -3.5]])
    sp, z = cam.proj(dp); draw_quad(fr, desk_tex(), sp)
    opened = seg(T, *COVER_OPEN); closed_end = seg(T, *CLOSE)
    left_h = TK * eio(opened) * (1 - eio(closed_end))
    # 노트 그림자
    for side, on in (("R", 1.0), ("L", left_h / TK)):
        if on <= 0: continue
        x0 = 0.0 if side == "R" else -PW
        poly = np.array([[x0 - .03, 0, PD / 2 + .02], [x0 + PW + .05, 0, PD / 2 + .02], [x0 + PW + .08, 0, -PD / 2 - .06], [x0 - .01, 0, -PD / 2 - .06]])
        s_, _ = cam.proj(poly); fill_poly(fr, s_ + [10, 18], (0, 0, 0), .45 * on, blur=18)
    block(fr, cam, "R", TK); block(fr, cam, "L", left_h)

    B = bases()
    if T < COVER_OPEN[1]:
        # 닫힌 노트 → 표지가 넘어간다 (표지 앞면 / 뒷면은 첫 왼쪽 페이지)
        sp, _ = cam.proj(page_corners("R", TK + .002)); draw_quad(fr, np.asarray(tex_now("R1", T)), sp)
        th = math.pi * eio(opened)
        if opened > 0:
            sp, _ = cam.proj(page_corners("L", left_h + .002)); draw_quad(fr, tex_now("L1", T), sp, .8 + .2 * eio(opened))
        draw_sheet(fr, cam, th, tex_now("cover", T), tex_now("L1", T), curl=.18, y0=TK + .006)
    elif T < FLIP[0]:
        sp, _ = cam.proj(page_corners("L", TK + .002)); draw_quad(fr, tex_now("L1", T), sp)
        r1 = tex_now("R1", T)
        if T >= FOLD[1] - 1e-3: r1 = bake_popups_flat(r1, T)
        sp, _ = cam.proj(page_corners("R", TK + .002)); draw_quad(fr, r1, sp)
        cards = popups(T)
        for tex, x0, x1, zh, hgt, ang in sorted(cards, key=lambda c: -cam.depth([c[1], 0, c[3]])):
            a = math.radians(ang); yb = TK + .004
            top_y = yb + hgt * math.sin(a); top_z = zh + hgt * math.cos(a)
            P = np.array([[x0, top_y, top_z], [x1, top_y, top_z], [x1, yb, zh], [x0, yb, zh]])
            # 바닥 그림자 (빛이 왼쪽 위 앞에서)
            sh = np.array([[x0 + .05, yb, zh + hgt * math.sin(a) * .55 + hgt * math.cos(a)], [x1 + .05, yb, zh + hgt * math.sin(a) * .55 + hgt * math.cos(a)], [x1, yb, zh], [x0, yb, zh]])
            s_, _ = cam.proj(sh); fill_poly(fr, s_, (60, 40, 20), .28 * math.sin(a), blur=10)
            s_, _ = cam.proj(P); draw_quad(fr, tex, s_, .9 + .1 * math.sin(a))
    elif T < CLOSE[0]:
        # 넘김: 아래는 L1/R2, 넘어가는 장은 앞=R1(팝업 눌린 것) 뒤=L2
        q = seg(T, *FLIP); th = math.pi * eio(q)
        sp, _ = cam.proj(page_corners("L", TK + .002)); draw_quad(fr, tex_now("L1", T), sp)
        sp, _ = cam.proj(page_corners("R", TK + .002)); draw_quad(fr, tex_now("R2", T), sp)
        if q < 1:
            draw_sheet(fr, cam, th, bake_popups_flat(tex_now("R1", T), T), tex_now("L2", T), curl=.6, y0=TK + .006)
        else:
            sp, _ = cam.proj(page_corners("L", TK + .006)); draw_quad(fr, tex_now("L2", T), sp)
    else:
        # 닫힘: 왼쪽 묶음이 오른쪽으로 (위로 보이던 L2 → 표지)
        q = closed_end; th = math.pi * (1 - eio(q))
        sp, _ = cam.proj(page_corners("R", TK + .002)); draw_quad(fr, tex_now("R2", T), sp)
        if q < 1:
            draw_sheet(fr, cam, th, tex_now("cover", T), tex_now("L2", T), curl=.25, y0=TK + .008)
        else:
            sp, _ = cam.proj(page_corners("R", TK + .008)); draw_quad(fr, tex_now("cover", T), sp)
    draw_pen(fr, cam, T)
    # 마지막: 로고에서 금빛 한 번
    g = seg(T, 22.4, 23.3)
    if 0 < g < 1:
        c = cam.proj(page_world("R", TW / 2, 600, TK + .01))[0][0]
        m = np.zeros((H, W), np.float32); cv2.ellipse(m, (int(c[0]), int(c[1])), (int(160 + 420 * eio(g)), int(90 + 230 * eio(g))), 0, 0, 360, 1.0, -1)
        m = cv2.GaussianBlur(m, (0, 0), 60) * .55 * math.sin(math.pi * g)
        fr += m[..., None] * (np.array([255, 232, 180], np.float32) - fr) * .9
    return overlay(fr, T)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--stills", default="")
    ap.add_argument("--sheet", action="store_true")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    if a.stills:
        ts = [float(x) for x in a.stills.split(",")]; ims = []
        for t in ts:
            im = Image.fromarray(frame(t)); im.save(os.path.join(a.out, f"still_{t:05.2f}.jpg"), quality=88); ims.append(im)
        if a.sheet:
            cols = min(5, len(ims)); rows = math.ceil(len(ims) / cols); sw, sh = 324, 576
            sheet = Image.new("RGB", (cols * sw, rows * sh), "black")
            for i, im in enumerate(ims): sheet.paste(im.resize((sw, sh)), ((i % cols) * sw, (i // cols) * sh))
            sheet.save(os.path.join(a.out, "sheet.jpg"), quality=85)
        return
    silent = os.path.join(a.out, "_silent.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    n = int(T_END * FPS)
    for i in range(n):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 60 == 0: print(f"{i}/{n}", flush=True)
    p.stdin.close(); p.wait()
    out = os.path.join(a.out, "popup_note_starbucks.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-stream_loop", "-1", "-i", THEME,
                    "-filter_complex", f"[1:a]volume=0.55,afade=t=in:d=0.6,afade=t=out:st={T_END - 1.4}:d=1.4[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    os.remove(silent); print(out)


if __name__ == "__main__":
    main()
