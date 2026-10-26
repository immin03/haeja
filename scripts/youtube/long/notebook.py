"""밸류노트 취재 노트 — 롱폼 전용 화면 세계 (2026-10-27 운영자: "롱폼도 하나의 큰 노트로", "우리만의 포맷")

원고에 "world": "notebook" 이 있으면 render2.py 가 장면 그림(1920x1080)을 이 모듈에 넘겨, 책상 위 한 권의 취재 노트로 찍는다.
  - 노트: 위쪽이 스프링으로 묶인 가로형 취재 수첩. 장면 그림은 페이지에 그대로 쓰인다(밝은 장면은 종이에 바로, 어두운 장면·실사는 붙여 둔 사진 카드).
  - 장(chapter)이 바뀔 때만 페이지가 위로 넘어간다. 같은 장 안에서는 카메라가 노트 위를 천천히 옮겨 다닌다(장면마다 각도가 조금씩 다르다).
  - 오른쪽 가장자리 인덱스 탭: 장 번호. 지금 장은 금색으로 길게 나온다.
  - 장 제목 페이지: 새 페이지에 금색 펜이 장 제목을 손글씨로 쓰고 밑줄을 긋는다.
  - 오프닝(cold_open): 다큐처럼 화면 위아래 검은 띠 · 필름 결 · 타자기 자막. 마지막에 카메라가 뒤로 빠지며
    그 장면이 노트에 붙은 사진이었음이 드러난다(시그니처 공개 장면). Higgsfield 클립은 장면의 v.lib 에 mp4 로 넣으면 그대로 쓴다.
원고 설정 (모두 선택):
  "notebook": {"cold_open": 2,   # 앞에서 몇 장면을 다큐 오프닝으로 (기본 0)
               "stamps": {"0": ["U.S. · 2024", "미국 어느 스타벅스 매장"]},   # 장면 번호: [타자기 첫 줄(영문), 둘째 줄]
               "desk": "walnut"}
"""
import math, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FONTS = os.path.join(ROOT, "scripts", "reels", "fonts")
W, H = 1920, 1080

INK = (24, 34, 58); NAVY = (11, 27, 51); GOLD = (224, 200, 150); GOLD_D = (168, 144, 97); PEN = (196, 150, 64)
IVORY = (246, 241, 232); CARD_BORDER = (250, 247, 240)
CARD_SCALE = .9   # 붙인 사진 카드 크기 (페이지 그림 폭 대비)


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eio(t): t = clamp(t); return t * t * (3 - 2 * t)
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def lerp(a, b, p): return a + (b - a) * p


_F = {}


def font(name, size):
    k = (name, size)
    if k not in _F:
        cand = {"pen": [os.path.join(FONTS, "NanumPenScript-Regular.ttf")],
                "mont": [os.path.join(FONTS, "Montserrat-ExtraBold.ttf")],
                "type": ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
                "serif": ["/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
                          "/usr/share/fonts/noto-cjk/NotoSerifCJK-Bold.ttc", os.path.join(FONTS, "SUIT-Medium.ttf")]}.get(name, [os.path.join(FONTS, f"SUIT-{name}.ttf")])
        p = next((c for c in cand if os.path.exists(c)), os.path.join(FONTS, "SUIT-Bold.ttf"))
        try: _F[k] = ImageFont.truetype(p, size, index=1 if p.endswith(".ttc") and "Serif" in p else 0)   # .ttc 두 번째 얼굴 = KR
        except Exception: _F[k] = ImageFont.truetype(p, size)
    return _F[k]


# ── 카메라 (책상 = y 0 평면, 노트 위쪽(스프링) = +z) ──
FOV = 30.0
FOC = (H / 2) / math.tan(math.radians(FOV) / 2)


class Cam:
    def __init__(self, tx, tz, yaw, pitch, dist, roll=0.0, ty=0.0):
        y, p = math.radians(yaw), math.radians(pitch)
        tgt = np.array([tx, ty, tz], float)
        self.p = np.array([tx + dist * math.cos(p) * math.sin(y), ty + dist * math.sin(p), tz - dist * math.cos(p) * math.cos(y)])
        fw = tgt - self.p; fw /= np.linalg.norm(fw)
        up = np.array([0.0, 1.0, 0.0]) if abs(fw[1]) < .995 else np.array([0.0, 0.0, 1.0])
        rt = np.cross(up, fw); rt /= np.linalg.norm(rt); cu = np.cross(fw, rt)
        if roll:
            a = math.radians(roll); rt, cu = rt * math.cos(a) + cu * math.sin(a), -rt * math.sin(a) + cu * math.cos(a)
        self.R = np.stack([rt, cu, fw])

    def proj(self, P):
        P = np.atleast_2d(np.asarray(P, float)); d = (P - self.p) @ self.R.T; z = np.maximum(d[:, 2], 1e-3)
        return np.stack([W / 2 + FOC * d[:, 0] / z, H / 2 - FOC * d[:, 1] / z], 1)

    def facing(self, P, n):
        return float(np.dot(np.asarray(n, float), self.p - np.asarray(P, float))) > 0


def draw_quad(fr, tex, dst, shade=1.0, alpha=1.0, src=None):
    FH, FW = fr.shape[:2]; th, tw = tex.shape[:2]
    x0 = int(max(0, math.floor(dst[:, 0].min()) - 2)); x1 = int(min(FW, math.ceil(dst[:, 0].max()) + 2))
    y0 = int(max(0, math.floor(dst[:, 1].min()) - 2)); y1 = int(min(FH, math.ceil(dst[:, 1].max()) + 2))
    if x1 <= x0 or y1 <= y0: return
    d = np.float32(dst - [x0, y0])
    s = np.float32(src if src is not None else [[0, 0], [tw, 0], [tw, th], [0, th]])
    M = cv2.getPerspectiveTransform(s, d)
    wp = cv2.warpPerspective(tex, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillConvexPoly(m, np.int32(np.round(d * 16)), 255, lineType=cv2.LINE_AA, shift=4)
    m = m.astype(np.float32) * (alpha / 255)
    if wp.ndim == 3 and wp.shape[2] == 4: m *= wp[..., 3].astype(np.float32) / 255; wp = wp[..., :3]
    reg = fr[y0:y1, x0:x1]
    if shade != 1.0: wp = wp.astype(np.float32) * shade
    m3 = m[..., None]; reg -= reg * m3; reg += wp.astype(np.float32) * m3


def fill_poly(fr, pts, color, alpha=1.0, blur=0):
    FH, FW = fr.shape[:2]; b = int(blur * 3) + 3
    x0 = int(max(0, pts[:, 0].min() - b)); x1 = int(min(FW, pts[:, 0].max() + b))
    y0 = int(max(0, pts[:, 1].min() - b)); y1 = int(min(FH, pts[:, 1].max() + b))
    if x1 <= x0 or y1 <= y0: return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillPoly(m, [np.int32(np.round((pts - [x0, y0]) * 16))], 255, lineType=cv2.LINE_AA, shift=4)
    m = m.astype(np.float32) / 255
    if blur: m = cv2.GaussianBlur(m, (0, 0), blur)
    m = (m * alpha)[..., None]; reg = fr[y0:y1, x0:x1]; reg -= reg * m; reg += np.array(color, np.float32) * m


class Notebook:
    """페이지 텍스처: 가로 TW x 세로 TH. 장면 그림(1920x1080)이 (MX, MT) 에 들어간다"""

    def __init__(self, light_bg, paper_kind, paper_rgb, chapters, logo, seed=3, desk="walnut"):
        self.kind = paper_kind; per = {"grid": 48, "dots": 40}.get(paper_kind, 40)
        self.MX, self.MT, self.MB = 2 * per, 5 * per, 2 * per
        self.TW, self.TH = W + 2 * self.MX, H + self.MT + self.MB
        self.PW = 1.0; self.PD = self.TH / self.TW; self.TK = .022
        self.chapters = chapters; self.rng = np.random.default_rng(seed)
        self.paper_rgb = paper_rgb
        self.base = self._paper(light_bg, per)           # 종이(무늬·구멍·머리말 로고 포함), uint8
        self.shade = self._shade()                       # 종이 결·가장자리 그늘 (곱하기)
        self.back = self._back()                         # 페이지 뒷면
        self.desk = self._desk(desk)
        self.light = self._light()
        self.grain = [self.rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
        self.logo = logo
        self.tabs = [self._tab(i) for i in range(len(chapters))]

    # ── 텍스처 ──
    def _paper(self, bg, per):
        TW, TH = self.TW, self.TH
        if self.kind in ("grid", "dots"):   # 무늬 주기가 맞게 바탕을 이어 붙인다 (장면 그림과 이음매가 안 보이게)
            tile = np.asarray(bg)[0:per * 6, 0:per * 6]
            reps = (TH // tile.shape[0] + 2, TW // tile.shape[1] + 2)
            big = np.tile(tile, (reps[0], reps[1], 1))
            oy = (-self.MT) % per; ox = (-self.MX) % per
            a = big[oy:oy + TH, ox:ox + TW].copy()
        else:
            a = np.asarray(bg.resize((TW, TH), Image.BILINEAR)).copy()
        im = Image.fromarray(a); d = ImageDraw.Draw(im, "RGBA")
        # 스프링 구멍 + 머리말 줄
        for x in self.rings_px():
            d.ellipse([x - 9, 30 - 9, x + 9, 30 + 9], fill=(40, 44, 52, 255))
            d.ellipse([x - 9, 30 - 9, x + 9, 30 + 9], outline=(0, 0, 0, 60), width=2)
        d.line([(self.MX, self.MT - 24), (TW - self.MX, self.MT - 24)], fill=(198, 92, 92, 120), width=2)   # 머리말 아래 붉은 줄
        return np.asarray(im).copy()

    def rings_px(self):
        n = 30; return [int(self.TW * (.06 + .88 * i / (n - 1))) for i in range(n)]

    def _shade(self):
        TW, TH = self.TW, self.TH; yy, xx = np.mgrid[0:TH, 0:TW].astype(np.float32)
        r = ((xx - TW / 2) / TW) ** 2 * 1.2 + ((yy - TH * .48) / TH) ** 2
        s = 1 - np.clip(r - .10, 0, 1) * .16
        s *= 1 - .05 * np.exp(-((TW - xx) / 18)) - .05 * np.exp(-(xx / 18)) - .06 * np.exp(-((TH - yy) / 14))   # 가장자리
        g = cv2.GaussianBlur(self.rng.normal(0, 1, (TH // 3, TW // 3)).astype(np.float32), (0, 0), 1.0)
        g = cv2.resize(g, (TW, TH)); s *= 1 + g * .012
        return s[..., None].astype(np.float32)

    def _back(self):
        b = np.zeros((self.TH, self.TW, 3), np.float32) + np.array(self.paper_rgb, np.float32) * .95
        return np.clip(b * self.shade, 0, 255).astype(np.uint8)

    def _desk(self, kind):
        h, w = 900, 1600; rng = np.random.default_rng(5)
        x = np.linspace(0, 1, w)[None, :]; y = np.linspace(0, 1, h)[:, None]
        n1 = cv2.resize(rng.normal(0, 1, (h // 30, 18)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.resize(rng.normal(0, 1, (h // 4, 60)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        grain = np.sin((y * 90 + n1 * 2.2 + x * 3) * math.pi) * .5 + n2 * .35
        base = np.array([58, 40, 30], np.float32) if kind == "walnut" else np.array([30, 34, 42], np.float32)
        d = base[None, None, :] * (1 + .16 * grain[..., None]) + rng.normal(0, 2.2, (h, w, 1))
        return np.clip(d, 0, 255).astype(np.uint8)

    def _light(self):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W * .42) / W) ** 2 * 1.1 + ((yy - H * .38) / H) ** 2)
        l = 1.08 - np.clip(r - .18, 0, 1) * .9
        warm = np.stack([l * 1.03, l * 1.0, l * .95], -1)
        return np.clip(warm, .25, 1.12).astype(np.float32)

    def _tab(self, i):
        im = Image.new("RGBA", (120, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((60, 45), f"{i + 1:02d}", font=font("mont", 34), fill=(255, 255, 255, 255), anchor="mm")
        return np.asarray(im)

    # ── 페이지 만들기 ──
    def _base_hdr(self, right):
        if not hasattr(self, "_hdr"): self._hdr = {}
        if right not in self._hdr:
            t = self.base.copy(); self._header(t, right); self._hdr[right] = t
        return self._hdr[right]

    def page_light(self, S, header_right=""):
        """밝은 장면: 장면 그림을 종이에 그대로 쓴다"""
        t = self._base_hdr(header_right).astype(np.float32); t[self.MT:self.MT + H, self.MX:self.MX + W] = np.asarray(S)[..., :3]
        t *= self.shade
        return np.clip(t, 0, 255).astype(np.uint8)

    def _card_prep(self, rot, scale, right, seed):
        if not hasattr(self, "_cards"): self._cards = {}
        key = (round(rot, 3), scale, right, seed)
        if key in self._cards: return self._cards[key]
        if len(self._cards) > 6: self._cards.clear()
        cw, ch = int(W * scale), int(H * scale); b = 16; CW, CH = cw + 2 * b, ch + 2 * b
        cx, cy = self.TW / 2, self.MT + H / 2
        M = cv2.getRotationMatrix2D((CW / 2, CH / 2), rot, 1.0); M[0, 2] += cx - CW / 2; M[1, 2] += cy - CH / 2
        a = cv2.warpAffine(np.full((CH, CW), 255, np.uint8), M, (self.TW, self.TH), flags=cv2.INTER_LINEAR).astype(np.float32) / 255
        sh = cv2.GaussianBlur(np.roll(np.roll(a, 14, 0), 8, 1), (0, 0), 12) * .42
        t = self._base_hdr(right).astype(np.float32) * (1 - sh[..., None])
        tape = np.zeros((self.TH, self.TW, 3), np.float32); ta = np.zeros((self.TH, self.TW, 1), np.float32)
        pts = (M[:, :2] @ np.array([[0, 0], [CW, 0]], np.float32).T).T + M[:, 2]
        for (px, py), ang in zip(pts, (-38 + rot, 38 + rot)): self._tape(tape, ta, px, py, ang, seed)
        a3 = a[..., None]
        P1 = (t * (1 - a3) * (1 - ta) + tape * ta) * self.shade
        A1 = a3 * (1 - ta) * self.shade
        c = {"M": M, "cw": cw, "ch": ch, "b": b, "P1": P1.astype(np.float32), "A1": A1.astype(np.float32)}
        self._cards[key] = c
        return c

    def page_card(self, S, rot=0.0, scale=None, header_right="", seed=0):
        scale = scale or CARD_SCALE
        """어두운 장면·실사: 테두리 있는 사진 카드로 붙인다 (테이프 두 장)"""
        c = self._card_prep(rot, scale, header_right, seed); b = c["b"]
        card = np.empty((c["ch"] + 2 * b, c["cw"] + 2 * b, 3), np.uint8); card[:] = CARD_BORDER
        card[b:b + c["ch"], b:b + c["cw"]] = cv2.resize(np.asarray(S)[..., :3], (c["cw"], c["ch"]), interpolation=cv2.INTER_AREA)
        img = cv2.warpAffine(card, c["M"], (self.TW, self.TH), flags=cv2.INTER_LINEAR)
        t = c["P1"] + img.astype(np.float32) * c["A1"]
        return np.clip(t, 0, 255).astype(np.uint8)

    def _tape(self, rgb, al, x, y, ang, seed):
        w, h = 170, 50
        tape = np.zeros((h, w, 4), np.float32); tape[..., :3] = (236, 226, 196); tape[..., 3] = .62
        tape[..., 3] += np.random.default_rng(int(x) + seed).normal(0, .04, (h, w))
        tape[:, :6, 3] *= .5; tape[:, -6:, 3] *= .5
        M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0); M[0, 2] += x - w / 2; M[1, 2] += y - h / 2
        wp = cv2.warpAffine(tape, M, (self.TW, self.TH), flags=cv2.INTER_LINEAR)
        a = np.clip(wp[..., 3:4], 0, 1); rgb[:] = rgb * (1 - a) + wp[..., :3] * a; al[:] = 1 - (1 - al) * (1 - a)

    def page_title(self, text, sub, num, u, write_t0=.55, write_dur=1.1):
        """장 제목 페이지: 새 종이에 금색 펜으로 장 제목을 쓰고 밑줄"""
        t = self.base.copy(); im = Image.fromarray(t); d = ImageDraw.Draw(im, "RGBA")
        cx, cy = self.TW / 2, self.MT + H * .46
        d.text((cx, cy - 190), f"PART {num:02d}", font=font("mont", 40), fill=(*GOLD_D, 255), anchor="mm")
        f = font("pen", 190)
        while f.size > 90 and d.textlength(text, font=f) > W * .8: f = font("pen", f.size - 10)
        tw = d.textlength(text, font=f)
        layer = Image.new("L", (int(tw) + 40, f.size + 60), 0); ImageDraw.Draw(layer).text((20, 10), text, font=f, fill=255)
        p = clamp((u - write_t0) / write_dur); cut = int(layer.width * p)
        if cut > 0:
            m = layer.copy(); ImageDraw.Draw(m).rectangle([cut, 0, layer.width, layer.height], fill=0)
            x0, y0 = int(cx - layer.width / 2), int(cy - layer.height / 2)
            sh = m.point(lambda v: int(v * .25)); im.paste((0, 0, 0), (x0 + 3, y0 + 4), sh)
            im.paste(INK, (x0, y0), m)
        # 밑줄 (손으로 긋는 금색)
        q = clamp((u - write_t0 - write_dur) / .45)
        if q > 0:
            x0, x1, y = cx - tw / 2 - 10, cx - tw / 2 - 10 + (tw + 30) * eio(q), cy + f.size * .52
            pts = [(x0 + (x1 - x0) * k / 40, y + 5 * math.sin(k / 40 * math.pi) - 4 * k / 40) for k in range(41)]
            d.line(pts, fill=(*PEN, 240), width=10, joint="curve")
        a = clamp((u - write_t0 - write_dur - .2) / .4)
        if sub and a > 0:   # 장 제목을 다 쓴 뒤에 부제가 떠오른다 (PIL 은 투명도 0 글자도 그리므로 따로 겹친다)
            lay = Image.new("L", im.size, 0); ImageDraw.Draw(lay).text((cx, cy + f.size * .52 + 70), sub, font=font("SemiBold", 44), fill=int(255 * a), anchor="mm")
            im.paste((110, 118, 134), (0, 0), lay)
        t = np.asarray(im).copy(); self._header(t, "")
        tip = None
        if 0 < p < 1: tip = (cx - layer.width / 2 + layer.width * p, cy + f.size * (.1 + .25 * math.sin(u * 38)))
        elif 0 < q < 1: tip = (x1, y)
        return np.clip(t * self.shade, 0, 255).astype(np.uint8), tip

    def _header(self, t, right):
        im = Image.fromarray(t); self._header_draw(im, right); t[:] = np.asarray(im)

    def _header_f(self, t, right):
        im = Image.fromarray(np.clip(t, 0, 255).astype(np.uint8)); self._header_draw(im, right); t[:] = np.asarray(im).astype(np.float32)

    def _header_draw(self, im, right):
        if self.logo is not None:
            lg = self.logo; im.paste(lg, (self.MX, self.MT - 30 - lg.height - 6), lg)
        if right:
            d = ImageDraw.Draw(im, "RGBA"); f = font("SemiBold", 32)
            d.text((self.TW - self.MX, self.MT - 30 - 12), right, font=f, fill=(*INK, 200), anchor="rs")

    # ── 3D 그리기 ──
    def W3(self, u, v, y=0.0):
        """텍스처 픽셀 → 월드 좌표 (노트 위쪽 = +z)"""
        return np.array([u / self.TW - .5, y, self.PD / 2 - v / self.TW])

    def corners(self, y=0.0, pad=0.0):
        PD = self.PD
        return np.array([[-.5 - pad, y, PD / 2 + pad], [.5 + pad, y, PD / 2 + pad], [.5 + pad, y, -PD / 2 - pad], [-.5 - pad, y, -PD / 2 - pad]])

    def frame(self, tex, cam, flip=None, tab=-1, pen_tip=None, pen_alpha=0.0):
        """tex: 지금 보이는 페이지. flip=(theta(0~pi), old_tex): 앞 페이지가 위로 넘어가는 중"""
        TK, PD = self.TK, self.PD; yb = -TK
        # 책상·그림자·소품·뒤표지는 절반 해상도로 그리고 키운다 (흐릿해도 되는 부분이라 속도를 아낀다)
        lo = np.zeros((H // 2, W // 2, 3), np.float32); P2 = lambda P: cam.proj(P) * .5
        dq = np.array([[-1.9, yb, 1.6], [1.9, yb, 1.6], [1.9, yb, -1.4], [-1.9, yb, -1.4]])
        draw_quad(lo, self.desk, P2(dq))
        fill_poly(lo, P2(self.corners(yb, .03) + [.012, 0, -.02]), (0, 0, 0), .55, blur=11)
        self._desk_pen(lo, P2, yb)
        fill_poly(lo, P2(self.corners(yb + .002, .012)), (20, 30, 50))
        fr = cv2.resize(lo, (W, H), interpolation=cv2.INTER_LINEAR)
        top, bot = self.corners(0.0), self.corners(yb + .004)
        for i, j, n in ((3, 2, (0, 0, -1)), (1, 2, (1, 0, 0)), (0, 3, (-1, 0, 0))):
            P = np.array([top[i], top[j], bot[j], bot[i]])
            if cam.facing(P.mean(0), n):
                q = cam.proj(P); fill_poly(fr, q, (214, 206, 190))
                for k in range(1, 6):   # 종이 결
                    a = k / 6; l = np.array([top[i] * (1 - a) + bot[i] * a, top[j] * (1 - a) + bot[j] * a])
                    pl = cam.proj(l); cv2.line(fr, tuple(np.int32(pl[0])), tuple(np.int32(pl[1])), (186, 176, 158), 1, cv2.LINE_AA)
        # 인덱스 탭 (오른쪽 가장자리)
        n = len(self.tabs)
        for i in range(n):
            z1 = PD / 2 - .09 - i * min(.085, (PD - .18) / max(1, n)); z0 = z1 - .062; ext = .045 if i == tab else .03
            col = (196, 166, 104) if i == tab else (44, 62, 96)
            P = np.array([[.5 - .005, -TK * .45, z1], [.5 + ext, -TK * .45, z1 - .006], [.5 + ext, -TK * .45, z0 + .006], [.5 - .005, -TK * .45, z0]])
            q = cam.proj(P); fill_poly(fr, q, col)
            draw_quad(fr, self.tabs[i], q, alpha=.95 if i == tab else .7)
        draw_quad(fr, tex, cam.proj(self.corners(0.0)))
        if flip is not None and flip[0] < math.pi * .995: self._sheet(fr, cam, flip[0], flip[1])
        self._rings(fr, cam)
        if pen_tip is not None and pen_alpha > .02: self._pen_on_page(fr, cam, pen_tip, pen_alpha)
        fr *= self.light
        return np.clip(fr, 0, 255)

    def _sheet(self, fr, cam, theta, old, n=26):
        """앞 페이지가 아래 가장자리부터 들려 위로 넘어간다 (아래쪽이 먼저 휘며 올라감)"""
        TH, TW, PD = self.TH, self.TW, self.PD
        L = PD; ds = L / n; pts = [(0.0, PD / 2)]; angs = []
        y, z = 0.0, PD / 2
        for i in range(n):
            s = (i + .5) / n
            a = clamp(theta * (1 + .55 * s * math.sin(min(math.pi, theta)) ** .7), 0, math.pi)
            a = min(math.pi, a + .002 * i)
            y += ds * math.sin(a); z -= ds * math.cos(a); pts.append((y, z)); angs.append(a)
        strips = []
        for i in range(n):
            (ya, za), (yb, zb) = pts[i], pts[i + 1]
            P = np.array([[-.5, ya + .001, za], [.5, ya + .001, za], [.5, yb + .001, zb], [-.5, yb + .001, zb]])
            nrm = np.array([0, math.cos(angs[i]), math.sin(angs[i])])
            front = cam.facing(P.mean(0), nrm)
            v0, v1 = TH * i / n, TH * (i + 1) / n
            strips.append((cam.depth(P.mean(0)) if hasattr(cam, "depth") else 0, P, front, v0, v1, angs[i]))
        for _, P, front, v0, v1, a in strips:
            src_tex = old if front else self.back
            vv0, vv1 = (v0, v1)
            q = cam.proj(P)
            sh = .78 + .22 * abs(math.cos(a)) if front else .7 + .2 * abs(math.cos(a))
            draw_quad(fr, src_tex, q, shade=sh, src=[[0, vv0], [TW, vv0], [TW, vv1], [0, vv1]])

    def _rings(self, fr, cam):
        PD = self.PD; zc = PD / 2 - 30 / self.TW; r = .02
        for xp in self.rings_px():
            x = xp / self.TW - .5
            th = np.linspace(-.25 * math.pi, 1.25 * math.pi, 22)
            P = np.stack([np.full_like(th, x), r * np.sin(th) - self.TK * .4, zc + .012 + r * np.cos(th) * 1.05], 1)
            q = cam.proj(P)
            cv2.polylines(fr, [np.int32(q * 4)], False, (40, 36, 30), 7, cv2.LINE_AA, shift=2)
            cv2.polylines(fr, [np.int32(q * 4)], False, (176, 160, 126), 4, cv2.LINE_AA, shift=2)
            cv2.polylines(fr, [np.int32(q[3:9] * 4)], False, (236, 226, 198), 2, cv2.LINE_AA, shift=2)

    def _desk_pen(self, fr, proj, yb):
        c = np.array([.72, yb + .006, -.05]); d = np.array([math.cos(1.9), 0, math.sin(1.9)]); nrm = np.array([-d[2], 0, d[0]])
        def quad(t0, t1, w, col):
            P = np.array([c + d * t0 + nrm * w, c + d * t1 + nrm * w, c + d * t1 - nrm * w, c + d * t0 - nrm * w])
            fill_poly(fr, proj(P), col)
        fill_poly(fr, proj(np.array([c + d * -.02 + nrm * .02 + [.006, -.004, -.006], c + d * .36 + nrm * .02 + [.006, -.004, -.006],
                                      c + d * .36 - nrm * .02, c + d * -.02 - nrm * .02])), (0, 0, 0), .45, blur=3)
        quad(0, .04, .006, (196, 160, 90)); quad(.04, .25, .011, (16, 26, 46)); quad(.25, .27, .0115, (210, 180, 116)); quad(.27, .34, .011, (16, 26, 46))
        quad(.05, .24, .003, (60, 76, 104))

    def _pen_on_page(self, fr, cam, tip, al):
        """페이지 위 금색 펜: 펜촉이 tip(텍스처 픽셀)에 닿고 오른쪽 아래로 누워 있다"""
        P0 = self.W3(*tip, y=.004); d = np.array([.62, .55, -.56]); d /= np.linalg.norm(d); nrm = np.array([.67, 0, .74])
        def seg(t0, t1, w, col, a=1.0):
            P = np.array([P0 + d * t0 + nrm * w, P0 + d * t1 + nrm * w, P0 + d * t1 - nrm * w, P0 + d * t0 - nrm * w])
            fill_poly(fr, cam.proj(P), col, al * a)
        g = np.array([d[0], 0, d[2]]); g /= np.linalg.norm(g); o = np.array([.012, -.004, -.018])   # 종이에 떨어지는 그림자
        S = np.array([P0 + nrm * .006, P0 + g * .24 + nrm * .012 + o, P0 + g * .24 - nrm * .012 + o, P0 - nrm * .006]); S[:, 1] = .001
        fill_poly(fr, cam.proj(S), (40, 34, 24), .32 * al, blur=7)
        seg(0, .035, .004, GOLD_D); seg(.035, .2, .009, (16, 26, 46)); seg(.2, .215, .0095, (220, 190, 120)); seg(.215, .27, .009, (16, 26, 46))
        seg(.04, .19, .0025, (90, 110, 140), .8)


# ── 화면 위에 얹는 다큐 효과 ──
def doc_grade(img, amt, k=0, nb=None):
    """필름 결 · 따뜻한 색 · 가장자리 어둡게 (amt 0~1)"""
    if amt <= 0: return img
    a = img.astype(np.float32)
    lum = a.mean(-1, keepdims=True)
    tone = np.where(lum > 128, np.array([1.04, 1.0, .93]), np.array([.92, .98, 1.06]))   # 밝은 곳 따뜻하게, 어두운 곳 청록
    a = a * (1 + (tone - 1) * amt)
    if nb is not None:
        g = cv2.resize(nb.grain[k % len(nb.grain)], (W, H), interpolation=cv2.INTER_NEAREST)
        a += g[..., None] * 9 * amt
    yy, xx = np.mgrid[0:H:8, 0:W:8].astype(np.float32)
    v = 1 - np.clip(np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) - .32, 0, 1) * 1.3
    v = cv2.resize(v, (W, H))[..., None]
    a *= 1 - (1 - v) * amt
    return np.clip(a, 0, 255)


def letterbox(img, amt):
    if amt <= 0: return img
    bh = int(round(131 * amt)); img[:bh] *= 0; img[H - bh:] *= 0
    return img


def stamp(pil, lines, u, t0=.6, cps=16):
    """타자기 자막: 첫 줄(영문, 고정폭) · 둘째 줄(명조). 한 글자씩 찍히고 커서가 깜빡인다"""
    if not lines: return []
    d = ImageDraw.Draw(pil, "RGBA"); x, y = 150, H - 131 - 230; ticks = []   # 아래 띠 위, 자막보다 위 (위쪽 장면 제목과 겹치지 않게)
    l1 = lines[0]; l2 = lines[1] if len(lines) > 1 else ""
    n1 = int(clamp((u - t0) * cps / max(1, len(l1))) * len(l1)); t2 = t0 + len(l1) / cps + .25
    n2 = int(clamp((u - t2) * cps / max(1, len(l2) or 1)) * len(l2)) if l2 else 0
    fade = clamp((u - t0) / .2)
    d.text((x, y), l1[:n1], font=font("type", 40), fill=(246, 241, 232, int(235 * fade)))
    if l2 and n2: d.text((x, y + 62), l2[:n2], font=font("serif", 36), fill=(234, 219, 185, int(220 * fade)))
    blink = (int(u * 2.2) % 2 == 0)
    if fade > 0 and blink:
        if n1 < len(l1) or not l2: cx = x + d.textlength(l1[:n1], font=font("type", 40)) + 6; cy = y
        else: cx = x + d.textlength(l2[:n2], font=font("serif", 36)) + 6; cy = y + 62
        d.rectangle([cx, cy + 4, cx + 18, cy + 44], fill=(246, 241, 232, 200))
    return ticks


def stamp_times(lines, t0=.6, cps=16):
    """타자기 소리를 넣을 때(장면 안 초)"""
    if not lines: return []
    out = [t0 + i / cps for i, ch in enumerate(lines[0]) if ch != " "]
    if len(lines) > 1:
        t2 = t0 + len(lines[0]) / cps + .25; out += [t2 + i / cps for i, ch in enumerate(lines[1]) if ch != " "]
    return out


# ── 카메라 자세 ──
def pose_for(k, typ, nb, seed=0, mode="light"):
    """정면에서 내려다본 고정 구도 (2026-10-27 운영자: 기울어 왔다 갔다 하면 잘 안 보이고 답답하다 → 한 화면에 꽉, 정면)
    light = 종이에 쓴 장면 그림이 화면을 꽉 채움 · card = 붙인 사진 카드가 화면의 97% · title = 노트 전체(스프링·탭)가 보이게"""
    tz = nb.PD / 2 - (nb.MT + H / 2) / nb.TW
    if mode == "card": frac = CARD_SCALE * W / nb.TW / .97
    elif mode == "title": frac = 1.26; tz = 0.0
    else: frac = W / nb.TW / 1.0
    return {"tx": 0.0, "tz": tz, "yaw": 0.0, "pitch": 89.6, "dist": FOC * (frac / 2) / (W / 2), "roll": 0.0}


def close_pose(nb, scale=None):
    scale = scale or CARD_SCALE
    """오프닝 공개 장면: 붙인 카드 안의 그림이 화면을 꽉 채우는 위에서 내려다본 자세"""
    tz = nb.PD / 2 - (nb.MT + H / 2) / nb.TW
    half = (W * scale / nb.TW) / 2
    return {"tx": 0.0, "tz": tz, "yaw": 0.0, "pitch": 89.6, "dist": FOC * half / (W / 2), "roll": 0.0}


def wide_pose(nb, base):
    p = dict(base); p["dist"] *= 1.34; p["pitch"] = 64; p["yaw"] = base["yaw"] - 8; p["roll"] = base["roll"] - 2.5; p["tz"] -= .03
    return p


def mix_pose(a, b, p):
    return {k: lerp(a[k], b[k], p) for k in a}


def drift(pose, u, dur, k):
    """장면 안에서 아주 천천히 다가가기만 한다 (돌거나 기울지 않는다)"""
    q = dict(pose); f = u / max(1.0, dur)
    q["dist"] = pose["dist"] * (1 - .025 * f)
    return q


def cam_of(p): return Cam(p["tx"], p["tz"], p["yaw"], p["pitch"], p["dist"], p["roll"])


# ── 소리 ──
def flip_sound(sr, seed=0, level=.09):
    """종이 넘기는 소리: 들릴 때 바스락 + 넘어가며 쉭"""
    from scipy import signal as sg
    rng = np.random.default_rng(seed); d = .75; n = int(sr * d); t = np.arange(n) / sr
    x = rng.standard_normal(n).astype(np.float32)
    b, a = sg.butter(2, [900 / (sr / 2), 7000 / (sr / 2)], "band"); x = sg.lfilter(b, a, x)
    crackle = (rng.random(n) < .012).astype(np.float32) * rng.standard_normal(n) * 3
    crackle = sg.lfilter(*sg.butter(2, 2500 / (sr / 2), "high"), crackle)
    env = np.exp(-((t - .12) / .07) ** 2) * .6 + np.exp(-((t - .42) / .14) ** 2) * 1.0
    y = (x * env + crackle * env * .5)
    return (y / (np.abs(y).max() + 1e-9) * level).astype(np.float32)


def type_tick(sr, seed=0, level=.05):
    from scipy import signal as sg
    rng = np.random.default_rng(seed); n = int(sr * .06); t = np.arange(n) / sr
    x = rng.standard_normal(n) * np.exp(-t * 160) + .6 * np.sin(2 * np.pi * (1800 + 300 * rng.random()) * t) * np.exp(-t * 90)
    x = sg.lfilter(*sg.butter(2, 900 / (sr / 2), "high"), x)
    return (x / (np.abs(x).max() + 1e-9) * level).astype(np.float32)


def whoosh(sr, dur=1.6, level=.06, seed=1):
    from scipy import signal as sg
    rng = np.random.default_rng(seed); n = int(sr * dur); t = np.arange(n) / sr
    x = rng.standard_normal(n); y = np.zeros(n)
    for a in range(0, n, 512):   # 필터가 천천히 열린다
        f = 300 + 2600 * (a / n) ** 1.5; b_, a_ = sg.butter(2, f / (sr / 2)); y[a:a + 512] = sg.lfilter(b_, a_, x[a:a + 512])
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    y = y * env
    return (y / (np.abs(y).max() + 1e-9) * level).astype(np.float32)
