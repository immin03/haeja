"""골드 라인 v2 — 노트 판 위를 금색 펜이 짚고, 카메라가 펜을 따라가는 세로 영상 (2026-10-26 운영자 시안 승인)

운영자: "밸류노트가 노트니까 노트 같은 판이 배경에 나오고 입체적으로 화면이 움직이면서, 선이 따라가며 정확하게 타깃을 긋는 것.
펜이 하나와 하나의 콘텐츠를 이어 가면서 설명하고, 그림·사진을 보여 주는 방식" (시안: Artifact '밸류노트 골드 라인').

구조
  - 장면 하나 = 노트 한 장(page). 장면마다 기존 쇼츠 그림(engine.YDRAW)을 노트 종이 위에 그린다.
  - 노트들은 넓은 책상(world) 위에 지그재그로, 조금씩 기울어진 채 놓인다.
  - 금선은 영상 처음부터 끝까지 하나: 노트에 들어와 → 그 장면의 핵심(숫자·막대·카드)에 밑줄·동그라미 → 노트 밖으로 나가
    → 다음 노트까지 이어진다. 카메라는 펜촉을 따라가며 장면 사이에서 살짝 물러났다(줌 아웃·회전) 다음 노트에 내려앉는다.
  - 제목 띠·자막·진행 막대는 화면에 고정 (engine.frame 이 얹는다).
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
PY0, PY1 = 470, 1300            # 노트 한 장에 담는 원래 화면 범위 (제목 띠 아래 ~ 자막 위)
PW, PH = W, PY1 - PY0
PC = (PW / 2, PH / 2)            # 노트 중심 (노트 좌표)
S0 = (W / 2, PY0 + PH / 2)       # 화면에서 노트 중심이 오는 자리
ZF = .9                          # 노트에 내려앉았을 때 배율 (책상과 노트 가장자리가 보이게)
INK = (232, 188, 96); INK_D = (168, 128, 60)
DESK = (9, 20, 40); CARD = (18, 34, 62); RULE = (30, 50, 84)
PAN0, PAN1 = .38, .62           # 장면 경계 앞뒤로 카메라가 움직이는 시간
_cache = {}


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): t = clamp(t); return 1 - (1 - t) ** 3
def eio(t): t = clamp(t); return 3 * t * t - 2 * t * t * t
def lerp(a, b, p): return a + (b - a) * p


# ── 책상과 노트 종이 ────────────────────────────────────────────
def _desk():
    if "desk" in _cache: return _cache["desk"]
    rng = np.random.default_rng(3)
    g = np.zeros((H, W, 3), np.float32) + np.array(DESK, np.float32)
    yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .46) / H) ** 2)
    g += (np.clip(.55 - r, 0, 1) * 34)[..., None] * np.array([.5, .7, 1.0])
    g += rng.normal(0, 2.2, (H, W, 1))
    _cache["desk"] = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8))
    return _cache["desk"]


SHEETS = [(float(x), float(y), float(w), float(h), float(r), float(z)) for x, y, w, h, r, z in
          zip(*[np.random.default_rng(11).uniform(a, b, 40) for a, b in ((-1500, 9000), (-1800, 1800), (180, 340), (260, 520), (-.5, .5), (.35, .75))])]


def _paper():
    """노트 종이: 남색 종이 + 옅은 가로줄 + 왼쪽 여백선 + 위쪽 링 구멍 (밸류노트 = 노트)"""
    if "paper" in _cache: return _cache["paper"].copy()
    im = Image.new("RGB", (W, H), CARD); d = ImageDraw.Draw(im)
    for y in range(PY0 + 60, PY1, 64): d.line([(40, y), (W - 40, y)], fill=RULE, width=2)
    d.line([(96, PY0), (96, PY1)], fill=(64, 52, 60), width=2)
    _cache["paper"] = im
    return im.copy()


def _card_mask():
    if "mask" in _cache: return _cache["mask"]
    m = Image.new("L", (PW, PH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, PW - 1, PH - 1], 38, fill=255)
    _cache["mask"] = m
    return m


# ── 노트 배치와 장면별 펜 목표 ───────────────────────────────────
def page_pose(k):
    """k번째 노트의 책상 위 위치(중심)와 기울기(도)"""
    return (k * 1240.0, (130.0 if k % 2 else -130.0) + 40 * math.sin(k * 1.7)), (2.4 if k % 2 else -2.0)


def to_world(k, p):
    (ox, oy), r = page_pose(k); a = math.radians(r); x, y = p[0] - PC[0], p[1] - PC[1]
    return (ox + x * math.cos(a) - y * math.sin(a), oy + x * math.sin(a) + y * math.cos(a))


def _ellipse(cx, cy, rx, ry, n=64):
    pts = []
    for i in range(n + 1):
        th = math.radians(180 + i * 385 / n); wob = 1 + .03 * math.sin(3 * th + .5)   # 왼쪽 끝에서 시작해 한 바퀴 조금 넘게
        pts.append((cx + rx * wob * math.cos(th), cy + ry * wob * math.sin(th)))
    return pts


def _under(x0, x1, y, n=30):
    return [(x0 + (x1 - x0) * i / n, y + 4 * math.sin(i / n * math.pi) - 3 * i / n) for i in range(n + 1)]


def target(E, sc, L):
    """장면의 핵심에 긋는 표시(노트 좌표 점들)와 그 시각. 화면 원래 좌표에서 PY0 만큼 올린다"""
    t = sc["type"]; y_at = E.y_at; Y = lambda y: y - PY0
    if t == "hook":
        num = sc["num"]; f = E.fit_font(E.fmt_num(num["to"], num), "Heavy", num.get("size", 230), 960); w = f.getlength(E.fmt_num(num["to"], num))
        return _under(W / 2 - w / 2 - 10, W / 2 + w / 2 + 10, Y(960)), 1.05
    if t == "bars":
        items = sc["items"]; n = len(items); vals = [it["v"] for it in items] + ([sc["avg"]["value"]] if sc.get("avg") else [])
        lo, hi = min(0, min(vals)), max(0, max(vals)); X0, X1, TOP, BOT = 150, 930, (750 if sc.get("avg") else 710), 1100
        span = (hi - lo) or 1; hi_ = hi + span * .16; lo_ = lo - (span * .14 if lo < 0 else 0)
        ymap = lambda v: BOT - (v - lo_) / (hi_ - lo_) * (BOT - TOP)
        k = max(range(n), key=lambda i: abs(items[i]["v"])); it = items[k]; cw = (X1 - X0) / n; cx = X0 + cw * (k + .5)
        vy = ymap(it["v"]) - 38 if it["v"] >= 0 else ymap(it["v"]) + 38
        t0 = it.get("at")
        if isinstance(t0, list): t0 = y_at(L, *t0)
        elif t0 is None: t0 = y_at(L, 0, .85)
        return _ellipse(cx, Y(vy), min(cw * .62, 150), 52), t0 + .7
    if t == "statement":
        t2 = sc.get("t2") or min(.9, (L[0][1] if L else 2.0) * .35)
        f = E.fit_font(sc["l2"], "Heavy", 112, 980); w = f.getlength(sc["l2"])
        return _ellipse(W / 2, Y(900), w / 2 + 50, 92), t2 + .55
    if t == "compare":
        tr = y_at(L, sc["r_line"], .05) if sc.get("r_line") is not None else max(.9, y_at(L, 1) if len(L) > 1 else y_at(L, 0, .55))
        return _under(590, 990, Y(1196)), tr + .55   # 오른쪽 카드 아래 밑줄 (왼쪽 카드를 가로지르지 않게)
    if t == "equation":
        tb = y_at(L, 2) if len(L) > 2 else (y_at(L, 1) if len(L) > 1 else y_at(L, 0, .5)) + .9
        return _under(190, W - 190, Y(1050 + 112)), tb + .5
    if t == "photo":
        return _ellipse(W / 2, Y(962 if sc.get("title") else 900), 520, 330, 80), .5
    if t == "cta":
        return _under(W / 2 - 250, W / 2 + 250, Y(694)), .7
    return _under(W / 2 - 200, W / 2 + 200, Y(640)), .6


# ── 금선 경로 (영상 전체에 하나) ──────────────────────────────────
class Line:
    def __init__(self, E, scenes, total):
        self.E = E; self.scenes = scenes; self.total = total; self.segs = []   # (t0, t1, [world pts])
        prev_exit = None
        for k, s in enumerate(scenes):
            b, e = s["start"], s["start"] + s["dur"]
            mk, tm = target(E, s["sc"], s["L"])
            mw = [to_world(k, p) for p in mk]
            ty = mk[0][1]   # 표시의 시작 높이로 수평하게 들어온다 (시안처럼 선이 흐르며 밑줄·동그라미가 된다)
            entry = to_world(k, (-30, ty))
            # 이전 노트 출구 → 이번 노트 입구 (장면 경계에서 카메라가 따라간다)
            if prev_exit is not None:
                self.segs.append((b - PAN0, b + .12, _bez(prev_exit, entry, k)))
            t_in0 = b + (.15 if k else .2); t_in1 = t_in0 + .45
            self.segs.append((t_in0, t_in1, [entry] + _towards(entry, mw[0])))
            tm = clamp(tm, t_in1 - b + .05, s["dur"] - PAN0 - .7) + b
            self.segs.append((tm, tm + .6, mw))
            if k < len(scenes) - 1:
                ex = to_world(k, (PW + 30, mk[-1][1]))
                self.segs.append((e - PAN0 - .25, e - PAN0, [mw[-1]] + _towards(mw[-1], ex)))
                prev_exit = ex

    def tip(self, T):
        """시각 T 의 펜촉 위치와 움직이는 중인지"""
        last = self.segs[0][2][0]; moving = False; rest_since = 0.0
        for t0, t1, pts in self.segs:
            if T < t0: break
            if T < t1:
                return _along(pts, eio((T - t0) / (t1 - t0))), True, 0.0
            last = pts[-1]; rest_since = T - t1
        return last, moving, rest_since

    def draw(self, d, T, cam, erase=0.0):
        """erase: 0~1, 영상 마지막에 선이 처음부터 지워지며(꼬리가 따라 들어가며) 로고 밑줄로 흡수된다"""
        drawn = []
        for t0, t1, pts in self.segs:
            if T < t0: break
            p = 1.0 if T >= t1 else eio((T - t0) / (t1 - t0))
            n = max(2, int(len(pts) * p)); seg = list(pts[:n])
            if p < 1: seg.append(_along(pts, p))
            drawn.append(seg)
        total_n = sum(len(x) for x in drawn); cut = int(total_n * erase)
        for seg in drawn:
            if cut >= len(seg): cut -= len(seg); continue
            seg = seg[cut:]; cut = 0
            sp = [cam(q) for q in seg]
            if len(sp) >= 2:
                wdt = max(4, int(8 * cam.z))
                d.line(sp, fill=(*INK, 235), width=wdt, joint="curve")
                for q in (sp[0], sp[-1]): d.ellipse([q[0] - wdt / 2, q[1] - wdt / 2, q[0] + wdt / 2, q[1] + wdt / 2], fill=(*INK, 235))


def _towards(a, b, n=18):
    """a 에서 b 까지 부드럽게 휘는 선 (먼저 옆으로 가다가 목표 쪽으로 꺾인다)"""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * mx + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * my + t * t * b[1]) for t in [i / n for i in range(1, n + 1)]]


def _bez(a, b, k, n=40):
    dx = b[0] - a[0]; up = -70 if k % 2 else 70
    c1 = (a[0] + dx * .35, a[1] + up); c2 = (a[0] + dx * .65, b[1] - up * .6)
    return [((1 - t) ** 3 * a[0] + 3 * (1 - t) ** 2 * t * c1[0] + 3 * (1 - t) * t * t * c2[0] + t ** 3 * b[0],
             (1 - t) ** 3 * a[1] + 3 * (1 - t) ** 2 * t * c1[1] + 3 * (1 - t) * t * t * c2[1] + t ** 3 * b[1]) for t in [i / n for i in range(n + 1)]]


def _along(pts, p):
    if len(pts) == 1: return pts[0]
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    tot = sum(seg) or 1; d_ = p * tot
    for i, s in enumerate(seg):
        if d_ <= s or i == len(seg) - 1:
            f = 0 if s == 0 else clamp(d_ / s); return (lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f))
        d_ -= s
    return pts[-1]


# ── 카메라 ────────────────────────────────────────────────────
class Cam:
    def __init__(self, cx, cy, z, rot):
        self.cx, self.cy, self.z, self.r = cx, cy, z, rot
        a = math.radians(rot); self.c, self.s = math.cos(a), math.sin(a)

    def __call__(self, p):
        x, y = p[0] - self.cx, p[1] - self.cy
        return (S0[0] + self.z * (x * self.c - y * self.s), S0[1] + self.z * (x * self.s + y * self.c))


def camera_at(T, scenes, line):
    """장면 안에서는 노트에 내려앉고(살짝 떠다님), 경계에서는 펜촉을 따라 물러났다 다음 노트로"""
    k = max(i for i, s in enumerate(scenes) if s["start"] <= T + 1e-6 or i == 0)
    def rest(i, t):
        (ox, oy), r = page_pose(i); u = t - scenes[i]["start"]
        return ox + 8 * math.sin(u * .6), oy + 6 * math.cos(u * .45), ZF + .012 * clamp(u / max(scenes[i]["dur"], 1)), -r
    cx, cy, z, r = rest(k, T)
    for j in range(1, len(scenes)):
        b = scenes[j]["start"]
        if b - PAN0 <= T < b + PAN1:
            q = eio((T - (b - PAN0)) / (PAN0 + PAN1))
            a_ = rest(j - 1, T); b_ = rest(j, T)
            tip, _, _ = line.tip(T)
            cx = lerp(a_[0], b_[0], q); cy = lerp(a_[1], b_[1], q)
            w = math.sin(math.pi * q) * .55   # 이동 중에는 펜촉 쪽으로 끌린다
            cx = lerp(cx, tip[0], w); cy = lerp(cy, tip[1], w)
            z = lerp(a_[2], b_[2], q) - .2 * math.sin(math.pi * q)
            r = lerp(a_[3], b_[3], q)
            break
    return Cam(cx, cy, z, r)


# ── 한 프레임 ─────────────────────────────────────────────────
def page_image(E, s, T, scenes):
    """노트 한 장: 종이 위에 기존 쇼츠 장면 그림. 첫 장면(후킹)은 실제 영상을 종이 안 사진처럼"""
    sc = s["sc"]; u = T - s["start"]
    img = _paper()
    if s is scenes[0] and sc["type"] == "hook" and E._BR["frames"] is not None:
        fr = E._BR["frames"]; i = min(len(fr) - 1, int(T * 30))
        v = Image.fromarray(fr[i]).resize((W, H), Image.BILINEAR)
        a = np.asarray(v, np.float32); g = a.mean(2, keepdims=True); a = a * .5 + g * .5
        a = a * .42 + np.array(CARD, np.float32) * .58
        img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    img = (E.YDRAW if sc["type"] in E.YDRAW else E.DRAW)[sc["type"]](img, u, sc, s["L"], T)
    return img.crop((0, PY0, W, PY1))


FIN = 1.7   # 마지막 몇 초 동안 마무리 연출


def render(E, T, scenes, total, line, pen=True):
    cam = camera_at(T, scenes, line)
    kL = len(scenes) - 1; f = clamp((T - (total - FIN)) / FIN)
    logo_w = to_world(kL, (PW / 2, 600 - PY0))
    if f > 0:   # 카메라가 로고로 천천히 다가간다
        q = eio(f); cam = Cam(lerp(cam.cx, logo_w[0], q * .3), lerp(cam.cy, logo_w[1], q * .3), cam.z + .08 * q, cam.r)
    out = _desk().copy()
    d = ImageDraw.Draw(out, "RGBA")
    # 책상 위 흩어진 빈 노트 종이(멀리 있는 것일수록 천천히 움직인다): 화면이 입체적으로 보이게
    for (x, y, w, h, r, z) in SHEETS:
        sx = S0[0] + (x - cam.cx) * z * cam.z * .55; sy = S0[1] + (y - cam.cy) * z * cam.z * .55
        if -400 < sx < W + 400 and -400 < sy < H + 400:
            a = math.radians(r * 57.3 * .2 + cam.r); c, s_ = math.cos(a), math.sin(a); hw, hh = w * z * .5, h * z * .5
            pts = [(sx + px * c - py * s_, sy + px * s_ + py * c) for px, py in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
            d.polygon(pts, fill=(28, 46, 80, 70))
    # 화면에 걸치는 노트들
    for k, s in enumerate(scenes):
        corners = [cam(to_world(k, p)) for p in ((0, 0), (PW, 0), (PW, PH), (0, PH))]
        if max(c[0] for c in corners) < -50 or min(c[0] for c in corners) > W + 50 or max(c[1] for c in corners) < -50 or min(c[1] for c in corners) > H + 50: continue
        tt = min(max(T, s["start"]), s["start"] + s["dur"] - 1 / 30)
        pg = page_image(E, s, tt, scenes)
        # 그림자
        sh = [(x + 18 * cam.z, y + 26 * cam.z) for x, y in corners]; d.polygon(sh, fill=(0, 0, 0, 110))
        # 화면 → 노트 좌표 역변환 (affine)
        (ox, oy), r = page_pose(k); A = math.radians(r + cam.r); z = cam.z
        # 노트 좌표 p → 화면: S0 + z*Rcam*(Rpage*(p-PC) + O - C)
        ca, sa = math.cos(A), math.sin(A)
        cr, sr = math.cos(math.radians(cam.r)), math.sin(math.radians(cam.r))
        tx = S0[0] + z * ((ox - cam.cx) * cr - (oy - cam.cy) * sr); ty = S0[1] + z * ((ox - cam.cx) * sr + (oy - cam.cy) * cr)
        # 화면 q = M (p - PC) + t,  M = z*R(A)  →  p = M^-1 (q - t) + PC
        ia, ib, ic, id_ = ca / z, sa / z, -sa / z, ca / z
        coeffs = (ia, ib, -(ia * tx + ib * ty) + PC[0], ic, id_, -(ic * tx + id_ * ty) + PC[1])
        pg_rgba = pg.convert("RGBA"); pg_rgba.putalpha(_card_mask())
        warped = pg_rgba.transform((W, H), Image.AFFINE, coeffs, resample=Image.BILINEAR)
        out.paste(warped, (0, 0), warped)
        d = ImageDraw.Draw(out, "RGBA")
        d.line(corners + [corners[0]], fill=(60, 84, 126, 160), width=2)
    line.draw(d, T, cam, erase=eio(clamp(f / .6)) if f > 0 else 0.0)
    tip, moving, rest = line.tip(T)
    pa = 1.0 if moving else max(.0, 1 - max(0, rest - .5) / .5)
    tip_s = cam(tip)
    if f > 0:   # 펜이 로고로 날아가 작아지며 흡수된다 → 로고에서 금빛이 한 번 퍼진다
        q = eio(clamp(f / .6)); ls = cam(logo_w)
        tip_s = (lerp(tip_s[0], ls[0], q), lerp(tip_s[1], ls[1] + 40, q)); pa = (1 - q) * max(pa, .9)
        g = clamp((f - .55) / .45)
        if g > 0:
            glow = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(glow); rr = 120 + 520 * eio(g)
            gd.ellipse([ls[0] - rr, ls[1] - rr * .55, ls[0] + rr, ls[1] + rr * .55], fill=int(150 * math.sin(math.pi * g)))
            glow = glow.filter(ImageFilter.GaussianBlur(60))
            out.paste(Image.new("RGB", (W, H), (255, 232, 180)), (0, 0), glow)
    return out, (tip_s, pa, cam.z)
