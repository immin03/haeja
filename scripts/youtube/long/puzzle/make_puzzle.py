"""퍼즐 조각 화면 (2026-11-16 대표님: "지구본 말고 퍼즐 조각을 맞추는 형태로도 — 매번 같은 방식은 지루하다").

설정 JSON 하나로 영상 클립 여러 개를 만든다 → scripts/blog/media/lib/<prefix>_<name>.mp4
  python3 scripts/youtube/long/puzzle/make_puzzle.py scripts/youtube/long/puzzle/<cfg>.json

설정 예:
{ "prefix": "puzzle_L261117r", "title": "젠슨 황 복귀 퍼즐", "sub": "네 조각이 맞아야 돌아온다",
  "pieces": [ {"name": "실리콘밸리", "img": "il_….jpeg", "verdict": "복귀를 원한다", "tone": "gold"}, … 4개 (왼위·오위·왼아래·오아래) ],
  "clips": [ {"name": "open", "dur": 6, "show": [], "add": null, "left": ["젠슨 황, 돌아올까?", "네 조각이 맞아야 한다"]},
             {"name": "p1", "dur": 6, "show": [], "add": 0, "left": ["조각 1 · 실리콘밸리", "복귀를 원한다"]}, …,
             {"name": "end", "dur": 7, "show": [0,1,2,3], "add": null, "key": 3, "left": ["마지막 열쇠는 워싱턴", "…"]} ] }
tone: gold(복귀에 유리) · red(불리) · gray(아직 모름)
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
LIB = os.path.join(ROOT, "scripts", "blog", "media", "lib"); FONT = os.path.join(ROOT, "scripts", "reels", "fonts")
W, H, FPS = 1920, 1080, 30
NAVY = (8, 16, 32); INK = (236, 230, 214); GOLD = (214, 178, 96); RED = (214, 82, 72); GRAY = (150, 158, 172)
TONE = {"gold": GOLD, "red": RED, "gray": GRAY}
SS = 3   # 조각 테두리 계단 현상 줄이기 (3배로 그려 줄인다)


def F(w, s): return ImageFont.truetype(os.path.join(FONT, f"SUIT-{w}.ttf"), s)


# ── 퍼즐 조각 모양 ─────────────────────────────────────────
def edge(p0, p1, kind):
    """p0→p1 한 변. kind: 0 평평, +1 혹이 바깥(변의 왼쪽 법선 반대)으로, -1 안쪽으로"""
    (x0, y0), (x1, y1) = p0, p1; L = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / L, (y1 - y0) / L; nx, ny = uy, -ux
    if kind == 0: return [p0, p1]
    pts = []
    for i in range(121):
        s = i / 120
        # 혹: 가운데 30% 구간에 목이 좁고 머리가 둥근 모양
        if .34 < s < .66:
            a = (s - .34) / .32 * math.pi
            r = .17 * L; cx = .5; off = (math.sin(a) ** .9) * r * 1.05
            sx = s + (-.06 * math.sin(2 * a))   # 목을 살짝 좁힌다
        else:
            sx = s; off = 0
        x = x0 + ux * sx * L + nx * off * kind; y = y0 + uy * sx * L + ny * off * kind
        pts.append((x, y))
    return pts


def piece_poly(x, y, s, kinds):
    """정사각형 (x,y,크기 s) + 네 변의 혹 (위, 오른쪽, 아래, 왼쪽) — 시계 방향"""
    t, r, b, l = kinds
    P = [(x, y), (x + s, y), (x + s, y + s), (x, y + s)]
    pts = edge(P[0], P[1], t) + edge(P[1], P[2], r)[1:] + edge(P[2], P[3], b)[1:] + edge(P[3], P[0], l)[1:]
    return pts


# 2×2 퍼즐: 0 왼위, 1 오위, 2 왼아래, 3 오아래.  혹 방향(시계 방향 변 기준, +1 = 바깥으로 튀어나옴)
KINDS = [(0, 1, -1, 0), (0, 0, 1, -1), (1, -1, 0, 0), (-1, 0, 0, 1)]
S = 400; GX, GY = 1000, 100   # 퍼즐판 왼위 모서리 · 조각 크기 (판 800×800)
POS = [(GX, GY), (GX + S, GY), (GX, GY + S), (GX + S, GY + S)]


def sprite(i, piece):
    """조각 하나를 미리 그려 둔다 (RGBA, 혹 여유 포함)"""
    pad = int(S * .25); size = S + 2 * pad
    poly = [((px - POS[i][0] + pad) * SS, (py - POS[i][1] + pad) * SS) for px, py in piece_poly(POS[i][0], POS[i][1], S, KINDS[i])]
    mask = Image.new("L", (size * SS, size * SS), 0); ImageDraw.Draw(mask).polygon(poly, fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    im = Image.open(os.path.join(LIB, piece["img"])).convert("RGB")
    # 퍼즐판 전체(680) 크기로 잘라 조각 위치만큼 떼어 온다 → 네 조각이 각자 다른 사진
    sc = max(size / im.width, size / im.height); im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
    l = (im.width - size) // 2; tp = (im.height - size) // 2; im = im.crop((l, tp, l + size, tp + size))
    im = Image.blend(im, Image.new("RGB", im.size, NAVY), .45)
    tone = TONE.get(piece.get("tone", "gray"), GRAY)
    d = ImageDraw.Draw(im)
    # 이름과 판정
    cx = pad + S // 2; cy = pad + S // 2
    nm = piece["name"].split("\n"); fs = 44 if len(nm) == 1 else 40
    for j, ln in enumerate(nm): d.text((cx, cy - 30 - (len(nm) - 1 - j) * (fs + 6)), ln, font=F("Heavy", fs), fill=INK, anchor="mm")
    if piece.get("verdict"):
        f = F("Bold", 28); w_ = d.textlength(piece["verdict"], font=f)
        d.rounded_rectangle([cx - w_ / 2 - 16, cy + 18, cx + w_ / 2 + 16, cy + 62], 22, fill=(*tone, ), outline=None)
        d.text((cx, cy + 40), piece["verdict"], font=f, fill=NAVY, anchor="mm")
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); out.paste(im, (0, 0), mask)
    # 테두리 (판정 색)
    edge_m = mask.filter(ImageFilter.MaxFilter(7)); ring = Image.new("RGBA", (size, size), (*tone, 255))
    ring_a = Image.fromarray(np.clip(np.asarray(edge_m, np.int16) - np.asarray(mask, np.int16), 0, 255).astype(np.uint8))
    out.paste(ring, (0, 0), ring_a)
    return out, pad


def slot(i):
    pad = int(S * .25); size = S + 2 * pad
    poly = [((px - POS[i][0] + pad) * SS, (py - POS[i][1] + pad) * SS) for px, py in piece_poly(POS[i][0], POS[i][1], S, KINDS[i])]
    m = Image.new("L", (size * SS, size * SS), 0); d = ImageDraw.Draw(m)
    d.line(poly + [poly[0]], fill=255, width=3 * SS)
    m = m.resize((size, size), Image.LANCZOS)
    # 점선처럼 보이게 군데군데 끊는다
    a = np.asarray(m).copy(); yy, xx = np.mgrid[0:size, 0:size]; a[((xx + yy) // 14) % 2 == 1] = 0
    out = Image.new("RGBA", (size, size), (*INK, 0)); out.putalpha(Image.fromarray((a * .45).astype(np.uint8)))
    fill = Image.new("L", (size * SS, size * SS), 0); ImageDraw.Draw(fill).polygon(poly, fill=26); fill = fill.resize((size, size), Image.LANCZOS)
    bg = Image.new("RGBA", (size, size), (*INK, 0)); bg.putalpha(fill)
    return Image.alpha_composite(bg, out), pad


def background():
    im = Image.new("RGB", (W, H), NAVY); a = np.asarray(im, np.float32)
    yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot((xx - 1360) / W, (yy - 520) / H)
    a = a + (1 - np.clip(r * 1.6, 0, 1))[..., None] * np.array([14, 22, 38], np.float32)
    rng = np.random.default_rng(3); a += rng.normal(0, 3.2, (H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def ease(t): t = min(1, max(0, t)); return 1 - (1 - t) ** 3


def left_text(img, lines, k, tone=None):
    d = ImageDraw.Draw(img, "RGBA")
    if not lines: return
    a = int(255 * ease(k))
    d.text((150, 420), lines[0], font=F("Heavy", 76), fill=(*INK, a), anchor="ls")
    if len(lines) > 1:
        col = TONE.get(tone, GOLD) if tone else GOLD
        d.text((152, 500), lines[1], font=F("Bold", 40), fill=(*col, a), anchor="ls")
    for j, ln in enumerate(lines[2:]):
        d.text((152, 570 + j * 52), ln, font=F("Medium", 32), fill=(*INK, int(a * .8)), anchor="ls")
    d.rectangle([150, 330, 150 + int(90 * ease(k)), 336], fill=(*GOLD, a))


def render(cfg, clip, sprites, slots, bg):
    n = int(clip["dur"] * FPS); out = os.path.join(LIB, f"{cfg['prefix']}_{clip['name']}.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    show = set(clip.get("show", [])); add = clip.get("add"); key = clip.get("key")
    for f in range(n):
        t = f / FPS; im = bg.copy().convert("RGBA")
        k_slot = ease(t / .8) if clip["name"] == "open" else 1
        for i in range(4):
            if i in show or (add == i and t > .9): continue
            sp, pad = slots[i]; s2 = sp.copy(); s2.putalpha(Image.fromarray((np.asarray(sp.getchannel("A"), np.float32) * k_slot).astype(np.uint8)))
            im.alpha_composite(s2, (POS[i][0] - pad, POS[i][1] - pad))
        for i in sorted(show):
            sp, pad = sprites[i]; x, y = POS[i][0] - pad, POS[i][1] - pad
            if key == i:   # 마지막 열쇠 조각: 천천히 빛난다
                g = .5 + .5 * math.sin(t * 2.4)
                glow = sp.getchannel("A").filter(ImageFilter.GaussianBlur(18)); gl = Image.new("RGBA", sp.size, (*GOLD, 0)); gl.putalpha(Image.fromarray((np.asarray(glow, np.float32) * (.35 + .5 * g)).astype(np.uint8)))
                im.alpha_composite(gl, (x, y))
            im.alpha_composite(sp, (x, y))
        if add is not None:
            sp, pad = sprites[add]; T0, T1 = .25, 1.25; k = ease((t - T0) / (T1 - T0))
            sx = {0: -700, 1: 900, 2: -700, 3: 900}[add]; sy = {0: -500, 1: -500, 2: 600, 3: 600}[add]
            x = POS[add][0] - pad + sx * (1 - k); y = POS[add][1] - pad + sy * (1 - k)
            rot = (1 - k) * (14 if add % 2 else -14); z = 1 + .12 * (1 - k)
            s2 = sp.rotate(rot, resample=Image.BICUBIC, expand=False)
            if z > 1.001: s2 = s2.resize((int(s2.width * z), int(s2.height * z)), Image.BICUBIC); x -= (s2.width - sp.width) / 2; y -= (s2.height - sp.height) / 2
            if t > T0: im.alpha_composite(s2, (int(x), int(y)))
            if T1 < t < T1 + .35:   # 딸깍 — 맞물리는 순간 테두리가 번쩍
                fl = (1 - (t - T1) / .35); glow = sp.getchannel("A").filter(ImageFilter.GaussianBlur(10))
                gl = Image.new("RGBA", sp.size, (255, 244, 214, 0)); gl.putalpha(Image.fromarray((np.asarray(glow, np.float32) * .55 * fl).astype(np.uint8)))
                im.alpha_composite(gl, (POS[add][0] - pad, POS[add][1] - pad))
        tone = cfg["pieces"][add]["tone"] if add is not None else (cfg["pieces"][key]["tone"] if key is not None else None)
        left_text(im, clip.get("left", []), (t - (1.1 if add is not None else .3)) / .6, tone)
        p.stdin.write(np.asarray(im.convert("RGB")).tobytes())
    p.stdin.close(); p.wait(); print("→", os.path.relpath(out, ROOT), clip["dur"], "초")


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    sprites = [sprite(i, pc) for i, pc in enumerate(cfg["pieces"])]; slots = [slot(i) for i in range(4)]; bg = background()
    only = sys.argv[2:] or None
    for c in cfg["clips"]:
        if only and c["name"] not in only: continue
        render(cfg, c, sprites, slots, bg)
