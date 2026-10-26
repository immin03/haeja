"""잉크 노트 (2026-10-26 운영자: "성우가 얘기할 때 항상 영상에서 뭔가를 보여주고 바뀌면서 끊임없이 볼거리를 제공")

대본에 "world": "ink" 인 쇼츠·릴스. 처음 스타벅스 시안(팝업 노트 시안)의 결을 그대로 쓴다:
아이보리 모눈 종이 · 손글씨(나눔펜) · 금색 펜 · 테이프로 붙인 실사 사진·영상 · 빨간 펜 숫자 · 페이지 넘김.

규칙: 성우 한 문장마다 화면 변화가 최소 1개 (audit 가 2.6초 넘게 멈춘 구간을 찾아 실패로 표시한다).

장면 쓰는 법 — 장면에 "page" 를 넣는다 (없으면 장면 종류에서 자동으로 만든다):
  "page": {"head": "삼성전자 · 005930", "beats": [ {...}, ... ]}
  비트(beat) 공통: "line": 몇 번째 문장에서 나오나(0부터), "at": 그 문장 안 위치(0~1, 기본 .05), "dur": 그려지는 시간(초)
  좌표는 페이지 픽셀 (가로 1080 × 세로 1436). 화면에서 위 제목·아래 자막에 가리지 않는 안전 영역은 대략 y 70~1300.
  - write   손글씨: text 또는 rows[], x, y, size(기본 96), color(ink/red/gold/blue/green/gray)
  - print   인쇄 글씨(SUIT): text, x, y, size(기본 40), w(Bold/ExtraBold/Medium), color, anchor(la/ma/ra)
  - under   밑줄: x0, x1, y, color, width   · circle 동그라미: cx, cy, rx, ry · cross X: x0, y0, x1, y1
  - arrow   화살표: pts [[x,y],...] · hl 형광펜: x0, y0, x1, y1, color(yellow/red/green)
  - photo   테이프로 붙인 사진/영상: src(jpg/png/mp4), x, y, w, h, rot, cap(아래 손글씨 설명), fx/fy(자를 위치)
  - pop     페이지에서 3D로 솟는 영상·사진 카드: src, (그 문장 동안 섰다가 접힌다)
  - sticker 로고 스티커: src(png), x, y, w, rot
  - chart   손으로 그리는 선 그래프: series[숫자...], x, y, w, h, color, labels {인덱스: "글씨"}
  - bars    막대: items [{"label","v","text","color"}], x, y, w, h
  - icons   그림 기호 줄: icon(chip/person/cup/dollar/box/server), n, hl [강조 번호], x, y, size, gap, color, hlcolor
  - check   체크 줄: text, x, y, size
"""
import math, os, subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import popworld as P

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TW, TH = 1080, 1436
PW, PD = 1.0, TH / TW
TK = P.TK
IVORY = (243, 236, 221); INKC = (22, 36, 70)
COL = {"ink": INKC, "red": (214, 48, 72), "gold": (176, 128, 46), "blue": (36, 92, 190), "green": (22, 140, 90),
       "gray": (110, 118, 134), "navy": (16, 30, 58)}
HLC = {"yellow": (255, 222, 90), "red": (255, 150, 160), "green": (150, 230, 180), "gold": (240, 205, 130)}
FLIP = .85
GAP_MAX = 2.6
_C = {}


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eio(t): t = clamp(t); return t * t * (3 - 2 * t)
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def lerp(a, b, p): return a + (b - a) * p
def seg(T, t0, t1): return clamp((T - t0) / (t1 - t0)) if t1 > t0 else float(T >= t1)


def font(kind, size):
    k = (kind, size)
    if k not in _C:
        name = {"pen": "NanumPenScript-Regular.ttf", "mont": "Montserrat-ExtraBold.ttf"}.get(kind, f"SUIT-{kind}.ttf")
        _C[k] = ImageFont.truetype(os.path.join(HERE, "fonts", name), size)
    return _C[k]


def col(c): return COL.get(c, c) if isinstance(c, str) else tuple(c)


def path(p): return p if os.path.isabs(p) else os.path.join(ROOT, p)


# ── 종이 ──
def paper(seed=0, head=None, num=None):
    rng = np.random.default_rng(seed)
    a = np.zeros((TH, TW, 3), np.float32) + np.array(IVORY, np.float32)
    a += rng.normal(0, 2.0, (TH, TW, 1))
    yy, xx = np.mgrid[0:TH, 0:TW]
    a -= (np.clip(((xx - TW / 2) / TW) ** 2 + ((yy - TH / 2) / TH) ** 2 - .12, 0, 1) * 38)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, "RGBA")
    for y in range(150, TH - 50, 44):
        for x in range(54, TW - 30, 44):
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(150, 160, 178, 110))
    if head:
        d.text((64, 56), head, font=font("mont", 30) if head.isascii() else font("ExtraBold", 34), fill=(*INKC, 190))
        d.line([(64, 112), (TW - 64, 112)], fill=(*INKC, 60), width=2)
    if num is not None:
        d.text((TW - 64, TH - 64), str(num), font=font("Medium", 30), fill=(*INKC, 110), anchor="ra")
    return np.asarray(im).copy()


def crop_to(im, w, h, fx=.5, fy=.5, zoom=1.0):
    r = w / h; iw, ih = im.size
    cw, ch = (ih * r, ih) if iw / ih > r else (iw, iw / r)
    cw /= zoom; ch /= zoom
    return im.crop((int((iw - cw) * fx), int((ih - ch) * fy), int((iw - cw) * fx + cw), int((ih - ch) * fy + ch))).resize((w, h), Image.LANCZOS)


def video_frames(src, w, h, sec=10):
    k = ("vid", src, w, h)
    if k not in _C:
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path(src), "-t", str(sec), "-vf",
                              f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={FPS}",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        n = len(raw) // (w * h * 3)
        _C[k] = np.frombuffer(raw[:n * w * h * 3], np.uint8).reshape(n, h, w, 3) if n else None
    return _C[k]


def media(src, w, h, T, t0, fx=.5, fy=.5):
    """사진(천천히 확대) 또는 영상(재생) 한 장면 (h, w, 3)"""
    if src.endswith(".mp4"):
        fr = video_frames(src, w, h)
        if fr is not None:
            # 앞뒤로 오가며 재생 (끊김 없이)
            i = int(max(0, T - t0) * FPS); n = len(fr); i = i % (2 * n - 2) if n > 1 else 0
            return fr[i if i < n else 2 * n - 2 - i]
        return np.full((h, w, 3), 200, np.uint8)
    k = ("img", src)
    if k not in _C:
        if not os.path.exists(path(src)): print("  ⚠ 사진 없음:", src); return np.full((h, w, 3), 200, np.uint8)
        _C[k] = Image.open(path(src)).convert("RGB")
    z = 1.0 + .06 * clamp((T - t0) / 6)
    return np.asarray(crop_to(_C[k], w, h, fx, fy, z))


# ── 비트 ──
class Beat:
    pen = False          # 펜이 따라다니는 비트
    def __init__(self, b, t0, t1):
        self.b, self.t0, self.t1 = b, t0, t1
    def p(self, T): return seg(T, self.t0, self.t1)
    def bbox(self): return (0, 0, TW, TH)
    def apply(self, tex, T): pass
    def tip(self, T): return None


class Write(Beat):
    pen = True
    def __init__(self, b, t0, t1):
        super().__init__(b, t0, t1)
        f = font("pen", b.get("size", 96)); rows = b.get("rows") or [b["text"]]
        lh = int(b.get("size", 96) * 1.0); wmax = int(max(f.getlength(r) for r in rows)) + 30
        lay = Image.new("RGBA", (wmax, lh * len(rows) + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        c = col(b.get("color", "ink"))
        for i, r in enumerate(rows):
            x = 10 if b.get("anchor", "l") == "l" else (wmax - 20 - f.getlength(r)) / 2 + 10
            d.text((x, 4 + i * lh), r, font=f, fill=(*c, 255))
        self.lay = np.asarray(lay).astype(np.float32); self.lh = lh; self.ws = [f.getlength(r) for r in rows]
        self.x = int(b["x"] - (wmax / 2 if b.get("anchor") == "m" else 0)); self.y = int(b["y"])
        self.offs = [10 if b.get("anchor", "l") == "l" else (wmax - 20 - w_) / 2 + 10 for w_ in self.ws]
        ys, xs_ = np.nonzero(self.lay[..., 3] > 30)
        self.tb = (self.x + int(xs_.min()), self.y + int(ys.min()), self.x + int(xs_.max()), self.y + int(ys.max())) if len(ys) else (self.x, self.y, self.x + 10, self.y + 10)
    def bbox(self): return self.tb
    def apply(self, tex, T):
        p = self.p(T)
        if p <= 0: return
        h, w = self.lay.shape[:2]; tot = sum(self.ws); done = p * tot; m = np.zeros((h, w), np.float32); xs = np.arange(w, dtype=np.float32)
        for i, rw in enumerate(self.ws):
            take = clamp(done / rw) if rw else 1; done -= rw
            if take <= 0: break
            xe = self.offs[i] + take * rw
            m[max(0, i * self.lh - 4):(i + 1) * self.lh + 14] = 1 if take >= 1 else np.clip((xe - xs) / 12 + 1, 0, 1)[None, :]
        blit(tex, self.lay, self.x, self.y, m)
    def tip(self, T):
        p = self.p(T); tot = sum(self.ws); done = p * tot
        for i, rw in enumerate(self.ws):
            if done <= rw or i == len(self.ws) - 1:
                return (self.x + self.offs[i] + min(done, rw), self.y + i * self.lh + self.lh * .78 + 6 * math.sin(T * 40))
            done -= rw


class Print(Beat):
    def __init__(self, b, t0, t1):
        super().__init__(b, max(t0, t0), t0 + .3)
        f = font(b.get("w", "Bold"), b.get("size", 40)); c = col(b.get("color", "ink"))
        rows = b.get("rows") or [b["text"]]; lh = int(b.get("size", 40) * 1.32)
        wmax = int(max(f.getlength(r) for r in rows)) + 8
        lay = Image.new("RGBA", (wmax, lh * len(rows) + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for i, r in enumerate(rows): d.text((0, i * lh), r, font=f, fill=(*c, int(255 * b.get("alpha", 1))))
        self.lay = np.asarray(lay).astype(np.float32)
        an = b.get("anchor", "la"); self.x = int(b["x"] - (wmax if an == "ra" else wmax / 2 if an == "ma" else 0)); self.y = int(b["y"])
        ys, xs_ = np.nonzero(self.lay[..., 3] > 30)
        self.tb = (self.x + int(xs_.min()), self.y + int(ys.min()), self.x + int(xs_.max()), self.y + int(ys.max())) if len(ys) else (self.x, self.y, self.x + 10, self.y + 10)
    def bbox(self): return self.tb
    def apply(self, tex, T):
        p = self.p(T)
        if p > 0: blit(tex, self.lay, self.x, self.y + int(10 * (1 - eout(p))), np.full(self.lay.shape[:2], eout(p), np.float32))


class Stroke(Beat):
    pen = True
    def __init__(self, b, t0, t1, pts, width=None, head=False):
        super().__init__(b, t0, t1)
        self.pts = np.array(pts, np.float32); self.c = col(b.get("color", "gold" if b["kind"] in ("under", "circle") else "red"))
        self.w = width or b.get("width", 9); self.head = head
        dl = np.r_[0, np.cumsum(np.hypot(*np.diff(self.pts, axis=0).T))]; self.cum = dl / max(dl[-1], 1e-6)
    def bbox(self):
        x0, y0 = self.pts.min(0); x1, y1 = self.pts.max(0); return (x0 - 20, y0 - 20, x1 + 20, y1 + 20)
    def upto(self, p):
        k = int(np.searchsorted(self.cum, p))
        if k <= 0: return self.pts[:1]
        k = min(k, len(self.pts) - 1); a, b = self.pts[k - 1], self.pts[k]
        f = (p - self.cum[k - 1]) / max(self.cum[k] - self.cum[k - 1], 1e-6)
        return np.vstack([self.pts[:k], a + (b - a) * f])
    def apply(self, tex, T):
        p = self.p(T)
        if p <= 0: return
        q = self.upto(eio(p))
        if len(q) >= 2: cv2.polylines(tex, [np.int32(np.round(q * 8))], False, self.c, self.w, cv2.LINE_AA, shift=3)
        if self.head and p >= .98:
            a, b = self.pts[-2], self.pts[-1]; ang = math.atan2(b[1] - a[1], b[0] - a[0]); L = 34
            for s in (2.6, -2.6):
                e = (b[0] + L * math.cos(ang + s), b[1] + L * math.sin(ang + s))
                cv2.line(tex, (int(b[0] * 8), int(b[1] * 8)), (int(e[0] * 8), int(e[1] * 8)), self.c, self.w, cv2.LINE_AA, shift=3)
    def tip(self, T): return tuple(self.upto(eio(self.p(T)))[-1])


def ellipse_pts(cx, cy, rx, ry, start=200, sweep=390, n=80):
    return [(cx + rx * (1 + .035 * math.sin(3 * th + .4)) * math.cos(th), cy + ry * (1 + .035 * math.sin(3 * th + .4)) * math.sin(th))
            for th in [math.radians(start + sweep * i / n) for i in range(n + 1)]]


def under_pts(x0, x1, y, n=30):
    return [(x0 + (x1 - x0) * i / n, y + 5 * math.sin(i / n * math.pi) - 4 * i / n) for i in range(n + 1)]


class Highlight(Beat):
    def __init__(self, b, t0, t1):
        super().__init__(b, t0, t1); self.c = HLC.get(b.get("color", "yellow"), (255, 222, 90))
    def bbox(self): return (self.b["x0"], self.b["y0"], self.b["x1"], self.b["y1"])
    def apply(self, tex, T):
        p = eio(self.p(T))
        if p <= 0: return
        x0, y0, x1, y1 = [int(v) for v in self.bbox()]; xe = int(x0 + (x1 - x0) * p)
        reg = tex[y0:y1, x0:xe].astype(np.float32)
        tex[y0:y1, x0:xe] = np.clip(reg * np.array(self.c, np.float32) / 255, 0, 255).astype(np.uint8)   # 곱하기 = 형광펜


class Photo(Beat):
    """테이프로 붙인 사진·영상 (종이에 철썩 붙는다)"""
    def __init__(self, b, t0, t1):
        super().__init__(b, t0, t0 + .38)
        self.w, self.h = int(b["w"]), int(b["h"]); self.rot = b.get("rot", -2.0); self.bd = 16
        self.cap = b.get("cap")
    def bbox(self): return (self.b["x"], self.b["y"], self.b["x"] + self.w, self.b["y"] + self.h + (70 if self.cap else 0))
    def card(self, T):
        bd = self.bd; ph = media(self.b["src"], self.w - 2 * bd, self.h - 2 * bd - (54 if self.cap else 0), T, self.t0, self.b.get("fx", .5), self.b.get("fy", .5))
        c = np.full((self.h, self.w, 4), 255, np.uint8); c[..., :3] = (250, 248, 242)
        c[bd:bd + ph.shape[0], bd:bd + ph.shape[1], :3] = ph
        if self.cap:
            im = Image.fromarray(c); ImageDraw.Draw(im).text((self.w / 2, self.h - 40), self.cap, font=font("pen", 46), fill=(*INKC, 255), anchor="mm"); c = np.asarray(im).copy()
        if self.b["src"].endswith(".mp4"):   # 재생 표시
            cv2.circle(c, (self.w - 46, 46), 18, (214, 48, 72, 255), -1, cv2.LINE_AA)
        return c
    def apply(self, tex, T):
        p = self.p(T)
        if p <= 0: return
        c = self.card(T); s = 1.14 - .14 * eout(p); al = eout(min(1, p * 1.6))
        ang = self.rot + 4 * (1 - eout(p))
        M = cv2.getRotationMatrix2D((self.w / 2, self.h / 2), ang, s)
        ex = int(self.w * .2); M[:, 2] += ex
        big = cv2.warpAffine(c, M, (self.w + 2 * ex, self.h + 2 * ex), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)).astype(np.float32)
        sh = cv2.GaussianBlur(big[..., 3], (0, 0), 12) * .35 * al
        x, y = self.b["x"] - ex, self.b["y"] - ex
        shl = np.zeros(big.shape, np.float32); shl[..., 3] = sh; shl[..., :3] = (40, 30, 20)
        blit(tex, shl, x + 12, y + 18, None)
        blit(tex, big, x, y, np.full(big.shape[:2], al, np.float32))
        if p >= .6:   # 마스킹 테이프 두 장
            for (tx, ty, r) in ((self.b["x"] + self.w * .22, self.b["y"] - 6, -9), (self.b["x"] + self.w * .78, self.b["y"] - 2, 8)):
                tp = Image.new("RGBA", (150, 46), (236, 222, 186, 210)).rotate(r, expand=True)
                blit(tex, np.asarray(tp).astype(np.float32), int(tx - tp.width / 2), int(ty - tp.height / 2), None)


class Sticker(Beat):
    def __init__(self, b, t0, t1):
        super().__init__(b, t0, t0 + .35)
        im = Image.open(path(b["src"])).convert("RGBA"); w = int(b["w"]); im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
        pad = 26; bg = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (255, 255, 255, 0))
        d = ImageDraw.Draw(bg); d.rounded_rectangle([0, 0, bg.width - 1, bg.height - 1], 22, fill=tuple(b.get("bg", (255, 255, 255))) + (255,))
        bg.paste(im, (pad, pad), im); self.img = bg.rotate(b.get("rot", -4), expand=True, resample=Image.BICUBIC)
    def bbox(self): return (self.b["x"], self.b["y"], self.b["x"] + self.img.width, self.b["y"] + self.img.height)
    def apply(self, tex, T):
        p = self.p(T)
        if p <= 0: return
        s = 1.25 - .25 * eout(p); im = self.img.resize((max(1, int(self.img.width * s)), max(1, int(self.img.height * s))))
        a = np.asarray(im).astype(np.float32); sh = a.copy(); sh[..., :3] = (40, 30, 20); sh[..., 3] = cv2.GaussianBlur(a[..., 3], (0, 0), 8) * .3
        cx, cy = self.b["x"] + self.img.width / 2, self.b["y"] + self.img.height / 2
        blit(tex, sh, int(cx - im.width / 2 + 8), int(cy - im.height / 2 + 12), None)
        blit(tex, a, int(cx - im.width / 2), int(cy - im.height / 2), np.full(a.shape[:2], eout(min(1, p * 1.5)), np.float32))


class Chart(Beat):
    """선 그래프. series 전체로 눈금을 잡고 from~to 구간만 그린다 (한 그래프를 문장 여러 개에 나눠 그릴 때)"""
    pen = True
    def __init__(self, b, t0, t1):
        super().__init__(b, t0, t1)
        s = np.array(b["series"], np.float32); lo, hi = b.get("lo", float(s.min())), b.get("hi", float(s.max())); n = len(s)
        x, y, w, h = b["x"], b["y"], b["w"], b["h"]
        xs = np.array(b.get("xs") or list(range(n)), np.float32); xs = (xs - xs[0]) / max(xs[-1] - xs[0], 1e-6)
        self.pts = np.stack([x + w * xs, y + h - (s - lo) / max(hi - lo, 1e-6) * h], 1)
        self.c = col(b.get("color", "red")); self.lab = {int(k): v for k, v in (b.get("labels") or {}).items()}
        self.i0 = b.get("from", 0); self.i1 = b.get("to", n - 1)
    def bbox(self):
        P_ = self.pts[self.i0:self.i1 + 1]; x0, y0 = P_.min(0); x1, y1 = P_.max(0); return (x0 - 30, y0 - 90, x1 + 30, y1 + 30)
    def cut(self, T):
        p = eio(self.p(T)); f = self.i0 + p * (self.i1 - self.i0); k = int(f); r = f - k; k1 = min(k + 1, self.i1)
        return f, np.vstack([self.pts[self.i0:k + 1], (self.pts[k] + (self.pts[k1] - self.pts[k]) * r)[None]])
    def apply(self, tex, T):
        if self.p(T) <= 0: return
        f, q = self.cut(T); x, y, w, h = self.b["x"], self.b["y"], self.b["w"], self.b["h"]
        if self.b.get("axis", self.i0 == 0):
            cv2.line(tex, (x * 8, (y + h + 18) * 8), ((x + w) * 8, (y + h + 18) * 8), INKC, 3, cv2.LINE_AA, shift=3)
        if self.b.get("fill") and len(q) > 1:
            poly = np.vstack([q, [[q[-1][0], y + h + 18], [q[0][0], y + h + 18]]])
            ov = tex.copy(); cv2.fillPoly(ov, [np.int32(poly * 8)], self.c, cv2.LINE_AA, shift=3); tex[:] = (tex * .86 + ov * .14).astype(np.uint8)
        cv2.polylines(tex, [np.int32(np.round(q * 8))], False, self.c, self.b.get("width", 10), cv2.LINE_AA, shift=3)
        im = None
        for i, t in self.lab.items():
            if self.i0 <= i <= f + 1e-6:
                if im is None: im = Image.fromarray(tex); d = ImageDraw.Draw(im)
                px, py = self.pts[i]; d.ellipse([px - 12, py - 12, px + 12, py + 12], fill=col(self.b.get("dot", "ink")))
                right = px < x + w * .6; dy = self.b.get("labdy", -64)
                d.text((px + (16 if right else -16), py + dy), t, font=font("pen", self.b.get("labsize", 58)), fill=col(self.b.get("labcolor", "ink")), anchor="la" if right else "ra")
        if im is not None: tex[:] = np.asarray(im)
    def tip(self, T): return tuple(self.cut(T)[1][-1])


class Bars(Beat):
    def bbox(self): return (self.b["x"], self.b["y"] - 90, self.b["x"] + self.b["w"], self.b["y"] + self.b["h"] + 70)
    def apply(self, tex, T):
        it = self.b["items"]; n = len(it); x, y, w, h = self.b["x"], self.b["y"], self.b["w"], self.b["h"]
        vmax = max(i["v"] for i in it); bw = w / (n * 1.6); im = Image.fromarray(tex); d = ImageDraw.Draw(im, "RGBA")
        d.line([(x, y + h), (x + w, y + h)], fill=(*INKC, 220), width=4)
        for k, i in enumerate(it):
            p = eout(seg(T, self.t0 + k * .35, self.t0 + k * .35 + .6))
            if p <= 0: continue
            bx = x + w * (k + .5) / n - bw / 2; bh = h * i["v"] / vmax * p; c = col(i.get("color", "ink"))
            d.rectangle([bx, y + h - bh, bx + bw, y + h], fill=(*c, 70), outline=(*c, 255), width=5)
            for yy in range(int(y + h - bh) + 10, int(y + h), 18): d.line([(bx + 4, yy + 10), (bx + bw - 4, yy - 6)], fill=(*c, 90), width=3)
            d.text((bx + bw / 2, y + h + 18), i["label"], font=font("Bold", 34), fill=(*INKC, 230), anchor="ma")
            if p > .8: d.text((bx + bw / 2, y + h - bh - 14), i.get("text", str(i["v"])), font=font("pen", 66), fill=(*c, 255), anchor="md")
        tex[:] = np.asarray(im)


ICON = {}
def icon_draw(d, kind, x, y, s, c, w=4):
    if kind == "chip":
        d.rectangle([x + s * .2, y + s * .2, x + s * .8, y + s * .8], outline=c, width=w)
        for k in range(3):
            o = s * (.32 + k * .18)
            for a, b_ in (((x + o, y + s * .05), (x + o, y + s * .2)), ((x + o, y + s * .8), (x + o, y + s * .95)), ((x + s * .05, y + o), (x + s * .2, y + o)), ((x + s * .8, y + o), (x + s * .95, y + o))):
                d.line([a, b_], fill=c, width=w)
    elif kind == "person":
        d.ellipse([x + s * .33, y + s * .05, x + s * .67, y + s * .39], outline=c, width=w)
        d.arc([x + s * .12, y + s * .45, x + s * .88, y + s * 1.25], 180, 360, fill=c, width=w)
    elif kind == "cup":
        d.polygon([(x + s * .15, y + s * .2), (x + s * .85, y + s * .2), (x + s * .75, y + s * .95), (x + s * .25, y + s * .95)], outline=c, width=w)
        d.rectangle([x + s * .1, y + s * .05, x + s * .9, y + s * .2], outline=c, width=w)
    elif kind == "dollar":
        d.ellipse([x + s * .08, y + s * .08, x + s * .92, y + s * .92], outline=c, width=w)
        d.text((x + s / 2, y + s / 2), "$", font=font("pen", int(s * .8)), fill=c, anchor="mm")
    elif kind == "server":
        for k in range(3):
            d.rectangle([x + s * .1, y + s * (.05 + k * .31), x + s * .9, y + s * (.31 + k * .31)], outline=c, width=w)
            d.ellipse([x + s * .72, y + s * (.15 + k * .31), x + s * .8, y + s * (.21 + k * .31)], fill=c)
    else:
        d.rectangle([x + s * .1, y + s * .1, x + s * .9, y + s * .9], outline=c, width=w)


class Icons(Beat):
    def bbox(self):
        b = self.b; s = b.get("size", 80); g = b.get("gap", 20); return (b["x"], b["y"], b["x"] + b["n"] * (s + g), b["y"] + s * 1.3)
    def apply(self, tex, T):
        b = self.b; n = b["n"]; s = b.get("size", 80); g = b.get("gap", 20); hl = set(b.get("hl", []))
        span = max(.3, self.t1 - self.t0); im = Image.fromarray(tex); d = ImageDraw.Draw(im, "RGBA")
        for k in range(n):
            p = seg(T, self.t0 + span * k / n, self.t0 + span * k / n + .12)
            if p <= 0: continue
            c = col(b.get("hlcolor", "red")) if k in hl else col(b.get("color", "ink"))
            icon_draw(d, b.get("icon", "box"), b["x"] + k * (s + g), b["y"], s, (*c, int(255 * p)), 5 if k in hl else 4)
        tex[:] = np.asarray(im)


class Pop(Beat):
    """페이지에서 3D로 솟는 카드 — 페이지 그림에는 아무것도 안 그리고, render 에서 따로 그린다"""
    def bbox(self): return (90, 300, 990, 900)


KIND = {"write": Write, "print": Print, "hl": Highlight, "photo": Photo, "sticker": Sticker, "chart": Chart, "bars": Bars, "icons": Icons, "pop": Pop}


def make_beat(b, t0, t1):
    k = b["kind"]
    if k == "under": return Stroke(b, t0, t1, under_pts(b["x0"], b["x1"], b["y"]), b.get("width", 10))
    if k == "circle": return Stroke(b, t0, t1, ellipse_pts(b["cx"], b["cy"], b["rx"], b["ry"]), b.get("width", 9))
    if k == "cross":
        x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
        return Stroke(b, t0, t1, [(x0, y0), (x1, y1), (x1 + 2, y1 - 2), (x1, y0), (x0, y1)], b.get("width", 11))
    if k == "arrow":
        pts = b["pts"]
        if len(pts) == 2:   # 살짝 휜 화살표
            (ax, ay), (bx, by) = pts; mx, my = (ax + bx) / 2 - (by - ay) * .15, (ay + by) / 2 + (bx - ax) * .15
            pts = [((1 - t) ** 2 * ax + 2 * (1 - t) * t * mx + t * t * bx, (1 - t) ** 2 * ay + 2 * (1 - t) * t * my + t * t * by) for t in np.linspace(0, 1, 24)]
        return Stroke(b, t0, t1, pts, b.get("width", 8), head=True)
    if k == "check":
        x, y, s = b["x"], b["y"], b.get("size", 64)
        return [Stroke(dict(b, kind="box", color=b.get("boxcolor", "ink")), t0, t0 + .25, [(x, y), (x + s, y), (x + s, y + s), (x, y + s), (x, y)], 5),
                Write(dict(b, kind="write", x=x + s + 24, y=y - s * .32, size=b.get("tsize", int(s * 1.25)), color=b.get("color", "ink")), t0 + .25, t1),
                Stroke(dict(b, kind="tick", color="red"), t1, t1 + .25, [(x + s * .15, y + s * .5), (x + s * .42, y + s * .82), (x + s * 1.05, y - s * .15)], 9)]
    return KIND[k](b, t0, t1)


DUR = {"write": None, "print": .3, "under": .45, "circle": .7, "cross": .5, "arrow": .55, "hl": .5, "photo": .4, "sticker": .35,
       "chart": 1.6, "bars": 1.2, "icons": 1.0, "pop": None, "check": None}


def beat_time(b, L, s):
    i = min(b.get("line", 0), len(L) - 1); a, v = L[i][0], L[i][1]
    t0 = s["start"] + a + b.get("at", .05) * v
    d = b.get("dur") or DUR.get(b["kind"])
    if d is None:
        if b["kind"] == "pop": d = clamp(a + v - (t0 - s["start"]) - .2, 1.2, 2.6)   # 카드는 길어야 2초 (그 뒤엔 페이지 글씨가 이어진다)
        else:
            n = len("".join(b.get("rows") or [b.get("text", "")]).replace(" ", ""))
            d = clamp(.15 * n + .3, .55, 1.9)
    return t0, t0 + d


# ── 장면 → 페이지 (자동) ──
def auto_page(sc, L):
    """page 가 없는 장면: 장면 종류에서 손글씨 페이지를 만든다 (문장마다 한 가지 이상)"""
    t = sc["type"]; B = []; n = len(L)
    def num_text(): return sc.get("num_text") or (f"{sc['num']['to']:,}{sc['num'].get('suffix', '')}" if sc.get("num") else "")
    if t == "hook":
        if sc.get("top"): B.append(dict(kind="print", text=sc["top"].replace("\n", " "), x=72, y=170, size=44, w="ExtraBold"))
        if sc.get("num"): B += [dict(kind="write", text=num_text(), x=72, y=300, size=230, color="red", line=0, at=.1), dict(kind="under", x0=80, x1=900, y=560, line=0, at=.75)]
        if sc.get("label"): B.append(dict(kind="write", text=sc["label"], x=80, y=620, size=90, line=min(1, n - 1)))
    elif t == "statement":
        B += [dict(kind="write", text=sc.get("l1", ""), x=72, y=220, size=96, line=0),
              dict(kind="write", text=sc.get("l2", ""), x=72, y=360, size=124, color={"loss": "red", "good": "green"}.get(sc.get("tone"), "gold"), line=min(1, n - 1), at=.05),
              dict(kind="under", x0=80, x1=980, y=520, line=min(1, n - 1), at=.7)]
        if sc.get("note"): B.append(dict(kind="print", text=sc["note"], x=72, y=600, size=32, w="Medium", color="gray", line=n - 1, at=.3))
    elif t == "compare":
        l, r = sc["l"], sc["r"]
        B += [dict(kind="print", text=sc.get("title", ""), x=72, y=160, size=40, w="ExtraBold"),
              dict(kind="print", text=l["label"], x=80, y=280, size=36, color="gray", line=0),
              dict(kind="write", text=l["v"], x=80, y=330, size=110, line=0, at=.1),
              dict(kind="arrow", pts=[[300, 520], [620, 640]], line=min(1, n - 1), at=0),
              dict(kind="print", text=r["label"], x=560, y=700, size=36, color="gray", line=min(1, n - 1)),
              dict(kind="write", text=r["v"], x=560, y=750, size=120, color={"loss": "red", "good": "green"}.get(r.get("tone"), "gold"), line=min(1, n - 1), at=.15),
              dict(kind="circle", cx=760, cy=830, rx=280, ry=110, line=n - 1, at=.6)]
    elif t == "list":
        B.append(dict(kind="print", text=sc.get("title", ""), x=72, y=160, size=44, w="ExtraBold"))
        for k, it in enumerate(sc["items"]):
            B.append(dict(kind="check", text=it.lstrip("0123456789 ").strip(), x=90, y=290 + k * 170, size=64, line=min(k, n - 1)))
    elif t == "cta":
        B += [dict(kind="write", text=sc.get("l1", ""), x=540, y=420, size=92, anchor="m", line=0),
              dict(kind="write", text=sc.get("l2", ""), x=540, y=540, size=110, color="red", anchor="m", line=n - 1, at=.1),
              dict(kind="circle", cx=540, cy=610, rx=400, ry=110, line=n - 1, at=.6)]
    return {"beats": B}


# ── 준비 ──
def prep(E, scenes):
    for k, s in enumerate(scenes):
        sc = s["sc"]; L = s["L"]; pg = sc.get("page") or auto_page(sc, L)
        beats = []
        for b in pg.get("beats", []):
            t0, t1 = beat_time(b, L, s)
            bb = make_beat(b, t0, t1)
            beats += bb if isinstance(bb, list) else [bb]
        if pg.get("autofill", True): beats += autofill(s, beats)
        s["_ink"] = {"base": paper(k + 3, pg.get("head"), k + 1), "beats": beats}
    scenes[0]["_ink_ok"] = True


def _hit(r, boxes, pad=6):
    x0, y0, x1, y1 = r
    return any(not (x1 + pad < a or x0 - pad > c or y1 + pad < b_ or y0 - pad > d_) for a, b_, c, d_ in boxes)


def autofill(s, beats):
    """문장 안에서 2.4초 넘게 새 비트가 없으면, 방금 쓴 손글씨에 펜이 강조 표시를 더한다.
    다른 글씨·그림과 겹치면 안 된다 (2026-10-27 운영자: 선을 긋다 보니 글자가 겹친다) → 밑줄 자리가 비었으면 밑줄, 아니면 글자 안쪽 형광펜, 둘레가 비었으면 동그라미"""
    add = []; t_end = s["start"] + s["dur"] - FLIP; skip = set()
    solid = [b for b in beats if isinstance(b, (Write, Print, Photo, Sticker, Chart, Bars, Icons))]
    for _ in range(12):
        pops = [b for b in beats if isinstance(b, Pop)]
        ev = sorted([s["start"]] + [b.t0 for b in beats + add] + [b.t1 + .7 for b in pops] + [float(t_) for b in pops for t_ in np.arange(b.t0 + 2.0, b.t1 + .7, 2.0)] + [t_end])
        gap = next(((a, b) for a, b in zip(ev, ev[1:]) if b - a > 2.4 and (round(a, 2), round(b, 2)) not in skip), None)
        if not gap: break
        t = gap[0] + min(1.3, (gap[1] - gap[0]) / 2)
        cands = sorted([b for b in beats if isinstance(b, Write) and b.t0 < t], key=lambda z: -z.t0)
        nb = None
        for tg in cands:
            x0, y0, x1, y1 = [float(v) for v in tg.bbox()]
            others = [o.bbox() for o in solid if o is not tg] + [z.bbox() for z in add if z.b.get("_on") is not tg]
            done = {z.b["kind"] for z in add if z.b.get("_on") is tg} | {z.b["kind"] for z in beats if isinstance(z, (Stroke, Highlight)) and _hit(z.bbox(), [tg.bbox()], 0)}
            if "under" not in done and not _hit((x0, y1 + 2, x1, y1 + 22), others):
                nb = Stroke({"kind": "under", "color": "gold", "_auto": 1, "_on": tg}, t, t + .5, under_pts(x0 + 6, x1, y1 + 12), 9)
            elif "hl" not in done:
                nb = Highlight({"kind": "hl", "x0": x0 - 4, "y0": y0 + (y1 - y0) * .45, "x1": x1 + 4, "y1": y1 + 4, "color": "yellow", "_auto": 1, "_on": tg}, t, t + .5)
            elif "circle" not in done and not _hit((x0 - 34, y0 - 26, x1 + 34, y1 + 26), others):
                nb = Stroke({"kind": "circle", "color": "red", "_auto": 1, "_on": tg}, t, t + .7, ellipse_pts((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 + 28, (y1 - y0) / 2 + 22), 8)
            if nb: break
        if nb is None:
            print(f"  ⚠ {gap[0]:.1f}~{gap[1]:.1f}초: 겹치지 않게 강조할 곳이 없습니다 — 비트를 직접 넣으세요"); skip.add((round(gap[0], 2), round(gap[1], 2))); continue
        add.append(nb)
    return add


def overlaps(s):
    """손으로 짠 비트끼리 겹치는지 (글씨·사진·그림)"""
    bs = [b for b in s["_ink"]["beats"] if isinstance(b, (Write, Print, Photo, Sticker, Bars, Icons)) and not b.b.get("_auto") and not b.b.get("over")]
    out = []
    for i, a in enumerate(bs):
        for b in bs[i + 1:]:
            A, B = a.bbox(), b.bbox()
            if not (A[2] < B[0] or B[2] < A[0] or A[3] < B[1] or B[3] < A[1]):
                out.append((a.b.get("text") or a.b.get("kind"), b.b.get("text") or b.b.get("kind")))
    return out


def page_now(s, T):
    ink = s["_ink"]; tt = min(T, s["start"] + s["dur"] - 1 / FPS)
    a = ink["base"].copy()
    for b in ink["beats"]:
        if b.t0 <= tt and not isinstance(b, Pop): b.apply(a, tt)
    return a


def blit(tex, lay, x, y, m=None):
    """lay (h,w,4 float) 를 tex(uint8) 의 (x,y) 에 알파로 얹는다. m: 추가 가림 (h,w)"""
    h, w = lay.shape[:2]; x0, y0 = max(0, x), max(0, y); x1, y1 = min(tex.shape[1], x + w), min(tex.shape[0], y + h)
    if x1 <= x0 or y1 <= y0: return
    L = lay[y0 - y:y1 - y, x0 - x:x1 - x]; a = L[..., 3:4] / 255
    if m is not None: a = a * m[y0 - y:y1 - y, x0 - x:x1 - x, None]
    reg = tex[y0:y1, x0:x1].astype(np.float32); tex[y0:y1, x0:x1] = (reg * (1 - a) + L[..., :3] * a).astype(np.uint8)


# ── 점검: 멈춘 구간 ──
def events(scenes):
    ev = []
    for j, s in enumerate(scenes):
        if j: ev.append((s["start"] - FLIP, "넘김"))
        for b in s["_ink"]["beats"]:
            ev.append((b.t0, b.b.get("kind")))
            if isinstance(b, Pop):   # 카드가 서 있는 동안은 화면이 살아 있다
                for tt in np.arange(b.t0 + 2.0, b.t1 + .7, 2.0): ev.append((float(tt), "pop"))
                ev.append((b.t1 + .7, "pop접힘"))
    return sorted(ev)


def audit(scenes, total):
    ev = [t for t, _ in events(scenes)] + [total]; gaps = []; prev = 0.0
    for t in ev:
        if t - prev > GAP_MAX: gaps.append((round(prev, 2), round(t, 2)))
        prev = max(prev, t)
    return gaps


# ── 카메라: 방금 그려진 곳을 따라간다 ──
def focus(s, T):
    bs = [b for b in s["_ink"]["beats"] if b.t0 <= T and not isinstance(b, Pop)]
    if not bs: return None
    b = max(bs, key=lambda z: z.t0); x0, y0, x1, y1 = b.bbox()
    prev = [z for z in bs if z is not b]
    if prev:
        c = max(prev, key=lambda z: z.t0); X0, Y0, X1, Y1 = c.bbox()
        q = eio(seg(T, b.t0 - .05, b.t0 + .55))
        return lerp((X0 + X1) / 2, (x0 + x1) / 2, q), lerp((Y0 + Y1) / 2, (y0 + y1) / 2, q)
    return (x0 + x1) / 2, (y0 + y1) / 2


def pop_state(s, T):
    for b in s["_ink"]["beats"]:
        if isinstance(b, Pop) and b.t0 - .05 <= T <= b.t1 + .75:
            ang = 84 * eout(seg(T, b.t0, b.t0 + .8)) * (1 - eio(seg(T, b.t1, b.t1 + .7)))
            return b, ang, 1 - clamp((seg(T, b.t1, b.t1 + .7) - .5) / .5)
    return None


def framing(s):
    """장면 하나에 고정된 카메라 자리: 그 장면에 쓰일 내용 전체가 들어오게 (2026-10-27 운영자: 노트는 흔들리지 않고 펜만 움직이게)"""
    if "frame" not in s["_ink"]:
        bb = [b.bbox() for b in s["_ink"]["beats"] if not isinstance(b, Pop)] or [(0, 150, TW, 1150)]
        y0 = max(100, min(v[1] for v in bb)); y1 = min(TH - 60, max(v[3] for v in bb))
        h = (y1 - y0) / TH; cy = (y0 + y1) / 2
        s["_ink"]["frame"] = (clamp(PD / 2 - cy / TH * PD, -.25, .3), clamp(2.3 + (h - .5) * 1.3, 2.45, 2.8))
    return s["_ink"]["frame"]


def cam_at(scenes, T):
    k = max(i for i, s in enumerate(scenes) if s["start"] <= T + 1e-6 or i == 0); s = scenes[k]
    z, dist = framing(s); u = T - s["start"]
    dist *= 1 - .025 * clamp(u / max(s["dur"], 1))          # 아주 천천히 다가간다 (흔들림 없이)
    tgt = [.5, 0, z]; pitch = 64
    if T < 1.2:
        q = eio(T / 1.2); dist = lerp(3.4, dist, q); pitch = lerp(56, pitch, q); tgt[2] = lerp(-.02, z, q)
    if k + 1 < len(scenes):   # 넘김: 다음 장면 자리로 부드럽게 옮겨 가며 살짝 물러난다
        nz, nd = framing(scenes[k + 1]); b = scenes[k + 1]["start"]
        q = eio(seg(T, b - FLIP - .25, b + .25))
        if q > 0:
            tgt[2] = lerp(z, nz, q); dist = lerp(dist, nd, q) + .35 * math.sin(math.pi * q); pitch = lerp(pitch, 60, math.sin(math.pi * q))
    st = pop_state(s, T)
    if st:
        b, ang, al = st; q = eio(seg(T, b.t0, b.t0 + .8)) * (1 - eio(seg(T, b.t1, b.t1 + .7)))
        tgt = [.5, lerp(0, .24, q), lerp(tgt[2], -.02, q)]; pitch = lerp(pitch, 34, q); dist = lerp(dist, 3.0, q)
    return P.Cam(tgt, 0.0, pitch, dist, 38, 0.0)


# ── 펜 ──
def pen_at(s, T):
    pb = sorted([b for b in s["_ink"]["beats"] if b.pen], key=lambda z: z.t0)
    for b in pb:
        if b.t0 <= T <= b.t1: return b.tip(T), 0.0, 1.0
    prev = [b for b in pb if b.t1 < T]; nxt = [b for b in pb if b.t0 > T]
    if prev and nxt:
        a, b = prev[-1], nxt[0]; pa, pb_ = a.tip(a.t1), b.tip(b.t0); gap = b.t0 - a.t1
        if gap < 1.6:
            q = eio(seg(T, a.t1, b.t0)); return (lerp(pa[0], pb_[0], q), lerp(pa[1], pb_[1], q)), math.sin(math.pi * q) * .8, 1.0
        rest = (min(TW - 80, pa[0] + 160), pa[1] + 120)
        if T < a.t1 + .5: q = eio(seg(T, a.t1, a.t1 + .5)); return (lerp(pa[0], rest[0], q), lerp(pa[1], rest[1], q)), .9 * q, 1.0
        if T > b.t0 - .5: q = eio(seg(T, b.t0 - .5, b.t0)); return (lerp(rest[0], pb_[0], q), lerp(rest[1], pb_[1], q)), .9 * (1 - q), 1.0
        return rest, .9, 1.0
    if prev:
        a = prev[-1]; pa = a.tip(a.t1); q = eio(seg(T, a.t1, a.t1 + .6)); return (pa[0] + 140 * q, pa[1] + 100 * q), .9 * q, 1.0
    if nxt:
        b = nxt[0]; pb_ = b.tip(b.t0); q = eio(seg(T, b.t0 - .6, b.t0)); return (pb_[0] + 140 * (1 - q), pb_[1] + 100 * (1 - q)), .9 * (1 - q), 1.0
    return None


def to_world(u, v, y=None): return (u / TW * PW, TK + .006 if y is None else y, PD / 2 - v / TH * PD)


# ── 한 프레임 ──
def render(E, T, scenes, total):
    if not scenes[0].get("_ink_ok"): prep(E, scenes)
    cam = cam_at(scenes, T)
    fr = np.zeros((H, W, 3), np.float32)
    S = 7.0
    P.draw_quad(fr, P.desk_tex(), cam.proj(np.array([[-S, 0, S], [S, 0, S], [S, 0, -S * .6], [-S, 0, -S * .6]])))
    for x0 in (0.0, -PW):
        poly = np.array([[x0 - .03, 0, PD / 2 + .02], [x0 + PW + .05, 0, PD / 2 + .02], [x0 + PW + .08, 0, -PD / 2 - .06], [x0 - .01, 0, -PD / 2 - .06]])
        P.fill_poly(fr, cam.proj(poly) + [10, 18], (0, 0, 0), .45, blur=18)
    _block(fr, cam, "R"); _block(fr, cam, "L")
    k = max(i for i, s in enumerate(scenes) if s["start"] <= T + 1e-6 or i == 0); s = scenes[k]
    nxt = scenes[k + 1] if k + 1 < len(scenes) else None
    flipping = nxt is not None and T >= nxt["start"] - FLIP
    Pq = np.array([[-PW, TK + .002, PD / 2], [0, TK + .002, PD / 2], [0, TK + .002, -PD / 2], [-PW, TK + .002, -PD / 2]])
    P.draw_quad(fr, _back() if k == 0 else _left(scenes, k), cam.proj(Pq), .9)
    under = nxt if flipping else s
    Pq = np.array([[0, TK + .002, PD / 2], [PW, TK + .002, PD / 2], [PW, TK + .002, -PD / 2], [0, TK + .002, -PD / 2]])
    P.draw_quad(fr, page_now(under, T if under is s else under["start"]), cam.proj(Pq))
    if flipping:
        th = math.pi * eio(seg(T, nxt["start"] - FLIP, nxt["start"]))
        _sheet(fr, cam, th, page_now(s, T), _mirror(page_now(s, T)))
    st = pop_state(s, T) if not flipping else None
    if st:
        b, ang, al = st
        if ang > 1:
            a = math.radians(ang); yb = TK + .004; x0, x1, zh, hh = .08, .92, .02, .63
            ty, tz = yb + hh * math.sin(a), zh + hh * math.cos(a)
            Q = np.array([[x0, ty, tz], [x1, ty, tz], [x1, yb, zh], [x0, yb, zh]])
            sh = np.array([[x0 + .05, yb, zh + hh * (math.sin(a) * .5 + math.cos(a))], [x1 + .05, yb, zh + hh * (math.sin(a) * .5 + math.cos(a))], [x1, yb, zh], [x0, yb, zh]])
            P.fill_poly(fr, cam.proj(sh), (0, 0, 0), .35 * math.sin(a) * al, blur=10)
            c = np.full((640, 840, 3), 248, np.uint8); c[20:620, 20:820] = media(b.b["src"], 800, 600, T, b.t0, b.b.get("fx", .5), b.b.get("fy", .5))
            if b.b.get("cap"):
                im = Image.fromarray(c); d = ImageDraw.Draw(im, "RGBA"); d.rectangle([20, 540, 820, 620], fill=(10, 18, 34, 170))
                d.text((420, 580), b.b["cap"], font=font("ExtraBold", 40), fill=(255, 255, 255), anchor="mm"); c = np.asarray(im)
            P.draw_quad(fr, c, cam.proj(Q), .92 + .08 * math.sin(a), al)
    if T < .8:
        _sheet(fr, cam, math.pi * eio(T / .8), P.cover_tex(E, ""), _back(), curl=.2, y0=TK + .008)
    if not flipping:
        pn = pen_at(s, T)
        if pn and not st:
            (u, v), lift, al = pn; P.draw_pen(fr, cam, to_world(u, v), lift, al)
    return Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8))


def _back():
    if "back" not in _C: _C["back"] = paper(99)
    return _C["back"]


def _left(scenes, k):
    """왼쪽 페이지: 앞 장면 페이지를 다 쓴 모습 (넘어간 장의 뒷면 대신 앞 장을 그대로 보여 노트가 쌓여 보이게)"""
    key = ("left", id(scenes), k)
    if key not in _C: _C[key] = _mirror(page_now(scenes[k - 1], scenes[k - 1]["start"] + scenes[k - 1]["dur"]), dim=True)
    return _C[key]


def _mirror(a, dim=False):
    """넘어간 장의 뒷면: 앞면 글씨가 희미하게 비친다"""
    b = a[:, ::-1].astype(np.float32); base = np.array(IVORY, np.float32)
    out = base + (b - base) * .12
    return np.clip(out, 0, 255).astype(np.uint8)


def _sheet(fr, cam, theta, texA, texB, curl=.6, y0=None):
    _p = (P.TW, P.TH, P.PW, P.PD)
    P.TW, P.TH, P.PW, P.PD = TW, TH, PW, PD
    try: P.sheet(fr, cam, theta, texA, texB, curl=curl, y0=TK + .006 if y0 is None else y0)
    finally: P.TW, P.TH, P.PW, P.PD = _p


def _block(fr, cam, side):
    x0, x1 = (0.0, PW) if side == "R" else (-PW, 0.0); xo = x1 if side == "R" else x0; h = TK
    for poly, c in ((np.array([[xo, 0, -PD / 2], [xo, 0, PD / 2], [xo, h, PD / 2], [xo, h, -PD / 2]]), (190, 180, 160)),
                    (np.array([[x0, 0, -PD / 2], [x1, 0, -PD / 2], [x1, h, -PD / 2], [x0, h, -PD / 2]]), (214, 204, 184))):
        P.fill_poly(fr, cam.proj(poly), c)
