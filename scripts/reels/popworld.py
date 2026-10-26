"""팝업 노트 (2026-10-26 운영자 승인 방향: "노트가 전환되는데 노트 위에 3D로 영상이 보이기도 하고… 밸류노트만의 고유한 영상")

대본에 "world": "popup" 이 있는 쇼츠·릴스를 진짜 원근(3D 카메라)으로 그린다.
  - 영상 전체가 책상 위의 한 권의 투자 노트다. 장면 하나 = 오른쪽 페이지 한 장.
  - 0초: 표지가 빠르게 열리고 첫 장면(후킹)이 바로 보인다.
  - 장면 사이: 페이지가 실제로 넘어간다 (종이가 휘며 왼쪽으로).
  - 장면의 핵심(숫자·막대·결론 문장)에 금색 펜이 직접 밑줄·동그라미를 긋는다 (goldworld.target 과 같은 표시 규칙).
  - 장면에 "popup": {"clip": "scripts/higgsfield/out/<id>.mp4", "line": 0} 이 있으면, 그 줄을 읽는 동안
    페이지에서 영상 카드가 팝업북처럼 솟아오르고 카메라가 낮게 내려가 카드를 본다. 줄이 끝나면 카드가 접히며 페이지로 들어간다.
    클립은 Higgsfield(Seedance 2.5)로 만든다: scripts/higgsfield/ 참고. 파일이 없으면 팝업 없이 그린다.
  - 제목 띠·자막·진행 막대는 engine.frame 이 위에 얹는다.
"""
import math, os, subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw

W, H, FPS = 1080, 1920, 30
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY0, PY1 = 470, 1350                 # 장면 그림에서 페이지에 담는 범위 (마지막 장면 버튼 아래 글까지)
PAD_T, PAD_B = 256, 300             # 세로로 긴 노트 페이지 (2026-10-26 운영자: 노트가 작고 답답해 보인다 → 화면을 꽉 채우게)
TW, TH = W, PY1 - PY0 + PAD_T + PAD_B   # 페이지 텍스처 (px)
PW, PD = 1.0, TH / TW                # 페이지 크기 (월드)
TK = .03                             # 페이지 묶음 두께
INK = (232, 188, 96); GOLD = (224, 200, 150); IVORY = (246, 241, 232)
FLIP = .55                           # 페이지 넘김 시간 (다음 장면 시작 직전)
OPEN = .5                            # 첫 표지 열림
_C = {}


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eio(t): t = clamp(t); return t * t * (3 - 2 * t)
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def lerp(a, b, p): return a + (b - a) * p
def seg(T, t0, t1): return clamp((T - t0) / (t1 - t0)) if t1 > t0 else float(T >= t1)


# ── 카메라 ──
class Cam:
    def __init__(self, tgt, yaw, pitch, dist, fov=38.0, roll=0.0):
        y, p = math.radians(yaw), math.radians(pitch)
        self.p = np.array([tgt[0] + dist * math.cos(p) * math.sin(y), tgt[1] + dist * math.sin(p), tgt[2] - dist * math.cos(p) * math.cos(y)])
        fw = np.array(tgt, float) - self.p; fw /= np.linalg.norm(fw)
        rt = np.cross([0.0, 1.0, 0.0], fw); rt /= np.linalg.norm(rt); cu = np.cross(fw, rt)
        if roll:
            a = math.radians(roll); rt, cu = rt * math.cos(a) + cu * math.sin(a), -rt * math.sin(a) + cu * math.cos(a)
        self.R = np.stack([rt, cu, fw]); self.f = (H / 2) / math.tan(math.radians(fov) / 2)

    def proj(self, P):
        P = np.atleast_2d(np.asarray(P, float)); d = (P - self.p) @ self.R.T; z = np.maximum(d[:, 2], 1e-3)
        return np.stack([W / 2 + self.f * d[:, 0] / z, H / 2 - self.f * d[:, 1] / z], 1)

    def depth(self, P): return float((np.asarray(P, float) - self.p) @ self.R[2])


def draw_quad(fr, tex, dst, shade=1.0, alpha=1.0):
    th, tw = tex.shape[:2]
    x0 = int(max(0, math.floor(dst[:, 0].min()) - 2)); x1 = int(min(W, math.ceil(dst[:, 0].max()) + 2))
    y0 = int(max(0, math.floor(dst[:, 1].min()) - 2)); y1 = int(min(H, math.ceil(dst[:, 1].max()) + 2))
    if x1 <= x0 or y1 <= y0: return
    d = np.float32(dst - [x0, y0])
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [tw, 0], [tw, th], [0, th]]), d)
    wp = cv2.warpPerspective(tex, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillConvexPoly(m, np.int32(np.round(d * 16)), 255, lineType=cv2.LINE_AA, shift=4)
    m = m.astype(np.float32) / 255 * alpha
    if wp.shape[2] == 4: m *= wp[..., 3].astype(np.float32) / 255; wp = wp[..., :3]
    m = m[..., None]; reg = fr[y0:y1, x0:x1]; reg[:] = reg * (1 - m) + wp.astype(np.float32) * shade * m


def fill_poly(fr, pts, color, alpha=1.0, blur=0):
    b = int(blur * 3) + 3
    x0 = int(max(0, pts[:, 0].min() - b)); x1 = int(min(W, pts[:, 0].max() + b))
    y0 = int(max(0, pts[:, 1].min() - b)); y1 = int(min(H, pts[:, 1].max() + b))
    if x1 <= x0 or y1 <= y0: return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillPoly(m, [np.int32(np.round((pts - [x0, y0]) * 16))], 255, lineType=cv2.LINE_AA, shift=4)
    m = m.astype(np.float32) / 255
    if blur: m = cv2.GaussianBlur(m, (0, 0), blur)
    m = (m * alpha)[..., None]; reg = fr[y0:y1, x0:x1]; reg[:] = reg * (1 - m) + np.array(color, np.float32) * m


# ── 재질 ──
def desk_tex():
    if "desk" in _C: return _C["desk"]
    S = 1536; rng = np.random.default_rng(5); yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    g = np.zeros((S, S, 3), np.float32) + np.array([10, 21, 41], np.float32)
    g += ((np.sin(yy / 8.0 + np.sin(xx / 170.0) * 3.0) * .5 + .5) * 6 + rng.normal(0, 2.0, (S, S)))[..., None] * np.array([.55, .7, 1.0])
    r = np.sqrt(((xx - S * .47) / S) ** 2 + ((yy - S * .73) / S) ** 2)
    g += (np.clip(.3 - r, 0, 1) * 110)[..., None] * np.array([.55, .72, 1.0])
    g *= np.clip(.35 + yy / S * .9, .35, 1.0)[..., None]
    _C["desk"] = np.clip(g, 0, 255).astype(np.uint8); return _C["desk"]


def blank_page(n=0):
    """넘어간 장의 뒷면 (가로줄 남색 종이 + 쪽 번호)"""
    k = ("blank", n)
    if k not in _C:
        im = Image.new("RGB", (TW, TH), (18, 34, 62)); d = ImageDraw.Draw(im)
        for y in range(60, TH, 64): d.line([(40, y), (TW - 40, y)], fill=(30, 50, 84), width=2)
        d.line([(TW - 96, 0), (TW - 96, TH)], fill=(64, 52, 60), width=2)
        _C[k] = np.asarray(im)
    return _C[k]


def cover_tex(E, spec_title):
    if "cover" in _C: return _C["cover"]
    rng = np.random.default_rng(9)
    a = np.zeros((TH, TW, 3), np.float32) + np.array([19, 34, 66], np.float32)
    a += (cv2.GaussianBlur(rng.normal(0, 1, (TH, TW)).astype(np.float32), (0, 0), 1.2) * 7)[..., None] * np.array([.6, .75, 1.0])
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([34, 34, TW - 34, TH - 34], 22, outline=(*GOLD, 120), width=3)
    try:
        lg, _, _ = E.logo_image(120, "dark"); im.paste(lg, (int(TW / 2 - lg.width / 2), int(TH * .36 - lg.height / 2)), lg)
    except Exception:
        d.text((TW / 2, TH * .36), "ValueNote", font=E.F("Heavy", 110), fill=IVORY, anchor="mm")
    d.text((TW / 2, 96), "INVESTMENT NOTE", font=E.F("SemiBold", 30), fill=(*GOLD, 200), anchor="mm")
    _C["cover"] = np.asarray(im); return _C["cover"]


# ── 페이지 내용 ──
def page_tex(E, s, T, scenes, ink=True):
    """장면 그림(engine 의 YDRAW)을 남색 노트 종이에 그리고, 펜 표시를 얹는다"""
    import goldworld
    tt = min(max(T, s["start"]), s["start"] + s["dur"] - 1 / FPS)
    if "paper" not in _C:
        im = Image.new("RGB", (TW, TH), (18, 34, 62)); d = ImageDraw.Draw(im)
        for y in range(PAD_T + 60 - 64 * 4, TH - 30, 64):
            if y > 30: d.line([(40, y), (TW - 40, y)], fill=(30, 50, 84), width=2)
        d.line([(96, 0), (96, TH)], fill=(64, 52, 60), width=2)
        _C["paper"] = np.asarray(im)
    a = _C["paper"].copy()
    _p = goldworld.PY1; goldworld.PY1 = PY1
    try: a[PAD_T:PAD_T + (PY1 - PY0)] = np.asarray(goldworld.page_image(E, s, tt, scenes))
    finally: goldworld.PY1 = _p
    if ink and s.get("_mark"):
        pts, t0, t1 = s["_mark"]; p = seg(tt, t0, t1)
        if p > 0:
            n = max(2, int(len(pts) * eio(p)))
            cv2.polylines(a, [np.int32(np.round(np.array(pts[:n]) * 8))], False, INK, 9, cv2.LINE_AA, shift=3)
    return a


def mark_setup(E, scenes):
    """장면마다 펜이 긋는 표시와 시각. 팝업 줄과 겹치면 팝업이 접힌 뒤로 미룬다"""
    import goldworld
    for s in scenes:
        try:
            pts, tm = goldworld.target(E, s["sc"], s["L"]); pts = [(x, y + PAD_T) for x, y in pts]
        except Exception: s["_mark"] = None; continue
        lo = .5
        pu = popup_window(s)
        if pu: lo = max(lo, pu[3] - s["start"] + .1)
        tm = clamp(tm, lo, max(lo, s["dur"] - FLIP - .75))
        s["_mark"] = (pts, s["start"] + tm, s["start"] + tm + .6)


# ── 팝업 영상 카드 ──
def clip_frames(path):
    k = ("clip", path)
    if k not in _C:
        full = path if os.path.isabs(path) else os.path.join(ROOT, path)
        if not os.path.exists(full): _C[k] = None; return None
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", full, "-t", "8", "-vf", "scale=800:600:force_original_aspect_ratio=increase,crop=800:600,fps=30",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        n = len(raw) // (800 * 600 * 3)
        _C[k] = np.frombuffer(raw[:n * 800 * 600 * 3], np.uint8).reshape(n, 600, 800, 3) if n else None
    return _C[k]


def popup_window(s):
    """(클립 경로, 솟기 시작, 다 섬, 접기 시작, 사라짐)"""
    pu = s["sc"].get("popup")
    if not pu or clip_frames(pu["clip"]) is None: return None
    L = s["L"]; i = min(pu.get("line", 0), len(L) - 1)
    a = s["start"] + max(0.0, L[i][0] - .35); b = s["start"] + L[i][0] + L[i][1]
    return pu["clip"], a, a + .6, b, b + .55


CARD = dict(x0=.08, x1=.92, zh=.02, h=.63)


def card_quad(ang):
    a = math.radians(ang); yb = TK + .004
    ty, tz = yb + CARD["h"] * math.sin(a), CARD["zh"] + CARD["h"] * math.cos(a)
    return np.array([[CARD["x0"], ty, tz], [CARD["x1"], ty, tz], [CARD["x1"], yb, CARD["zh"]], [CARD["x0"], yb, CARD["zh"]]])


def card_tex(frames, T, t0):
    i = int((T - t0) * FPS) % len(frames)
    c = np.full((640, 840, 3), 248, np.uint8); c[20:620, 20:820] = frames[i]
    return c


def card_state(s, T):
    """(각도 0~86, 투명도) 또는 None"""
    w = popup_window(s)
    if not w: return None
    _, a, b, c, d = w
    if T < a or T > d: return None
    ang = 86 * eout(seg(T, a, b)) * (1 - eio(seg(T, c, d)))
    alpha = 1 - clamp((seg(T, c, d) - .55) / .45)
    return ang, alpha, w


# ── 넘어가는 종이 ──
def sheet(fr, cam, theta, texA, texB, curl=.55, y0=None, n=20):
    y0 = TK + .004 if y0 is None else y0
    if theta <= 1e-4 or theta >= math.pi - 1e-4:
        side_x = 0.0 if theta <= 1e-4 else -PW; tex = texA if theta <= 1e-4 else texB
        P = np.array([[side_x, y0, PD / 2], [side_x + PW, y0, PD / 2], [side_x + PW, y0, -PD / 2], [side_x, y0, -PD / 2]])
        draw_quad(fr, tex, cam.proj(P)); return
    k = curl * math.sin(theta); pts = [(0.0, y0)]; x, y = 0.0, y0; ds = PW / n
    for i in range(n):
        sv = (i + .5) * ds; a = clamp(theta - k * (sv / PW) ** 1.3, 0, math.pi)
        x += math.cos(a) * ds; y += math.sin(a) * ds; pts.append((x, max(y, y0)))
    items = []
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        if i < n - 1: xb, yb = xb + (xb - xa) * .18, yb + (yb - ya) * .18
        P = np.array([[xa, ya, PD / 2], [xb, yb, PD / 2], [xb, yb, -PD / 2], [xa, ya, -PD / 2]])
        nrm = np.array([-(yb - ya), (xb - xa), 0.0]); nrm /= np.linalg.norm(nrm) + 1e-9
        ua, ub = int(i / n * TW), min(TW, int((i + (1.18 if i < n - 1 else 1)) / n * TW))
        if float(nrm @ (cam.p - P.mean(0))) > 0: tex, dst = texA[:, ua:ub], P
        else: tex, dst = texB[:, TW - ub:TW - ua], P[[1, 0, 3, 2]]
        shade = .72 + .3 * abs(float(nrm @ np.array([-.35, .9, -.25])))
        items.append((cam.depth(P.mean(0)), np.ascontiguousarray(tex), dst, shade))
    for _, tex, dst, shade in sorted(items, key=lambda z: -z[0]): draw_quad(fr, tex, cam.proj(dst), shade)


def block(fr, cam, side, h):
    if h <= 1e-4: return
    x0, x1 = (0.0, PW) if side == "R" else (-PW, 0.0); xo = x1 if side == "R" else x0
    for poly, c in ((np.array([[xo, 0, -PD / 2], [xo, 0, PD / 2], [xo, h, PD / 2], [xo, h, -PD / 2]]), (150, 140, 120)),
                    (np.array([[x0, 0, -PD / 2], [x1, 0, -PD / 2], [x1, h, -PD / 2], [x0, h, -PD / 2]]), (196, 186, 164))):
        fill_poly(fr, cam.proj(poly), c)


# ── 카메라 경로 ──
REST = dict(tgt=(.5, 0, .02), yaw=0, pitch=63, dist=2.78, roll=0)


def cam_at(scenes, T):
    total = scenes[-1]["start"] + scenes[-1]["dur"]
    k = max(i for i, s in enumerate(scenes) if s["start"] <= T + 1e-6 or i == 0); s = scenes[k]; u = T - s["start"]
    base = dict(REST); base["yaw"] = 2.5 * math.sin(T * .35 + k); base["roll"] = .8 * math.sin(T * .27 + k * 1.3)
    base["dist"] = REST["dist"] - .06 * clamp(u / max(s["dur"], 1))
    # 표지 열림: 조금 물러서 있다가 들어간다
    if T < OPEN + .4:
        q = eio(T / (OPEN + .4)); base["dist"] = lerp(3.6, base["dist"], q); base["pitch"] = lerp(55, 62, q); base["yaw"] = lerp(-8, base["yaw"], q)
    # 페이지 넘김: 살짝 물러나며 펼친 노트가 보인다
    for j in range(1, len(scenes)):
        b = scenes[j]["start"]
        if b - FLIP - .15 <= T < b + .35:
            q = math.sin(math.pi * seg(T, b - FLIP - .15, b + .35))
            base["dist"] += .55 * q; base["tgt"] = (lerp(.5, .1, q), 0, -.08); base["pitch"] = lerp(base["pitch"], 56, q)
    # 팝업: 낮게 내려가 카드를 본다
    st = card_state(s, T)
    if st:
        _, a, b, c, d = st[2]
        q = eio(seg(T, a, b)) * (1 - eio(seg(T, c, d)))
        base["tgt"] = (lerp(base["tgt"][0], .5, q), lerp(0, .27, q), lerp(base["tgt"][2], -.02, q))
        base["pitch"] = lerp(base["pitch"], 21, q); base["dist"] = lerp(base["dist"], 3.0, q)
        base["yaw"] = lerp(base["yaw"], 6 * math.sin((T - a) * .8), q)
    return Cam(base["tgt"], base["yaw"], base["pitch"], base["dist"], 38, base["roll"])


# ── 펜 ──
def pen_state(scenes, T):
    for s in scenes:
        m = s.get("_mark")
        if not m: continue
        pts, t0, t1 = m
        if t0 - .45 <= T <= t1 + .5:
            if T < t0: p = pts[0]; lift = seg(t0, T, t0 + .45) if False else (t0 - T) / .45; al = 1 - lift
            elif T > t1: p = pts[-1]; lift = (T - t1) / .5; al = 1 - lift
            else:
                q = eio(seg(T, t0, t1)); n = len(pts) - 1; f = q * n; i = min(int(f), n - 1); r = f - i
                p = (lerp(pts[i][0], pts[i + 1][0], r), lerp(pts[i][1], pts[i + 1][1], r)); lift = 0.0; al = 1.0
            return s, p, clamp(lift), clamp(al)
    return None


def draw_pen(fr, cam, P, lift, al):
    if al <= .02: return
    P = np.array(P) + np.array([0, .06 * lift, 0])
    tip = cam.proj(P)[0]; sc = cam.f * .55 / max(cam.depth(P), .3) / 600
    L = 430 * sc; ang = math.radians(-56); dv = np.array([math.cos(ang), math.sin(ang)]); nv = np.array([-dv[1], dv[0]])
    def parts(off):
        t = tip + off; b0 = t + dv * L * .12; b1 = t + dv * L
        nib = np.array([t, t + dv * L * .13 + nv * L * .028, t + dv * L * .13 - nv * L * .028])
        body = np.array([b0 + nv * L * .036, b1 + nv * L * .042, b1 - nv * L * .042, b0 - nv * L * .036])
        return nib, body, b0, b1
    nib, body, _, _ = parts(np.array([38, 50]) * (1 + 2.2 * lift) * sc)
    fill_poly(fr, np.vstack([nib, body]), (0, 0, 0), .3 * al, blur=6 + 10 * lift)
    nib, body, b0, b1 = parts(np.zeros(2))
    fill_poly(fr, nib, (205, 165, 90), al); fill_poly(fr, body, INK, al)
    fill_poly(fr, np.array([b0 + nv * L * .03, b1 + nv * L * .036, b1 + nv * L * .012, b0 + nv * L * .01]), (252, 228, 172), .7 * al)
    for f in (.55, .62):
        c = b0 + (b1 - b0) * f; w_ = L * .02
        fill_poly(fr, np.array([c + nv * L * .045, c + nv * L * .045 + dv * w_, c - nv * L * .045 + dv * w_, c - nv * L * .045]), (11, 27, 51), al)


# ── 한 프레임 ──
def render(E, T, scenes, total):
    if scenes[0].get("_pw") is None:
        mark_setup(E, scenes); scenes[0]["_pw"] = True
    cam = cam_at(scenes, T)
    fr = np.zeros((H, W, 3), np.float32)
    S = 7.0
    draw_quad(fr, desk_tex(), cam.proj(np.array([[-S, 0, S], [S, 0, S], [S, 0, -S * .6], [-S, 0, -S * .6]])))
    opened = seg(T, 0, OPEN)
    lh = TK * eio(opened)
    for x0, on in ((0.0, 1.0), (-PW, lh / TK)):
        if on <= 0: continue
        poly = np.array([[x0 - .03, 0, PD / 2 + .02], [x0 + PW + .05, 0, PD / 2 + .02], [x0 + PW + .08, 0, -PD / 2 - .06], [x0 - .01, 0, -PD / 2 - .06]])
        fill_poly(fr, cam.proj(poly) + [10, 18], (0, 0, 0), .45 * on, blur=18)
    block(fr, cam, "R", TK); block(fr, cam, "L", lh)
    k = max(i for i, s in enumerate(scenes) if s["start"] <= T + 1e-6 or i == 0); s = scenes[k]
    nxt = scenes[k + 1] if k + 1 < len(scenes) else None
    flipping = nxt is not None and T >= nxt["start"] - FLIP
    # 왼쪽 페이지 (앞 장의 뒷면)
    if opened > 0:
        P = np.array([[-PW, TK + .002, PD / 2], [0, TK + .002, PD / 2], [0, TK + .002, -PD / 2], [-PW, TK + .002, -PD / 2]])
        draw_quad(fr, blank_page() if k > 0 or opened >= 1 else blank_page(), cam.proj(P), .92)
    # 오른쪽: 넘기는 중이면 아래에 다음 장, 위에 넘어가는 지금 장
    under = nxt if flipping else s
    P = np.array([[0, TK + .002, PD / 2], [PW, TK + .002, PD / 2], [PW, TK + .002, -PD / 2], [0, TK + .002, -PD / 2]])
    draw_quad(fr, page_tex(E, under, T, scenes), cam.proj(P))
    if flipping:
        th = math.pi * eio(seg(T, nxt["start"] - FLIP, nxt["start"]))
        sheet(fr, cam, th, page_tex(E, s, T, scenes), blank_page(), curl=.6, y0=TK + .006)
    # 팝업 카드
    st = card_state(s, T) if not flipping else None
    if st:
        ang, alpha, w = st; frames = clip_frames(w[0])
        if ang > 1:
            a = math.radians(ang); Q = card_quad(ang); yb = TK + .004
            sh = np.array([[CARD["x0"] + .05, yb, CARD["zh"] + CARD["h"] * (math.sin(a) * .5 + math.cos(a))], [CARD["x1"] + .05, yb, CARD["zh"] + CARD["h"] * (math.sin(a) * .5 + math.cos(a))],
                           [CARD["x1"], yb, CARD["zh"]], [CARD["x0"], yb, CARD["zh"]]])
            fill_poly(fr, cam.proj(sh), (0, 0, 0), .35 * math.sin(a) * alpha, blur=10)
            draw_quad(fr, card_tex(frames, T, w[1]), cam.proj(Q), .92 + .08 * math.sin(a), alpha)
    # 첫 표지: 0.5초 동안 열리며 넘어간다
    if opened < 1:
        sheet(fr, cam, math.pi * eio(opened), cover_tex(E, ""), blank_page(), curl=.2, y0=TK + .008)
    ps = pen_state(scenes, T)
    if ps and not flipping:
        ss, p, lift, al = ps
        if ss is s: draw_pen(fr, cam, (p[0] / TW * PW, TK + .006, PD / 2 - p[1] / TH * PD), lift, al)
    return Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8))
