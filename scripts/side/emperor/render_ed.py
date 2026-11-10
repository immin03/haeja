"""황제의 일기 — 세로 쇼츠 렌더러 (1080x1920, 30fps)
spec(json) = {
  "id", "music": {"file","start","vol"},
  "cuts": [{"v": mp4 경로, "dur": 초, "speed": 1.0, "texts": [{"t0","t1","lines":[...],"style":"hook|sub|quote|src|big|small"}]}],
  "end": {"dur", "kicker", "lines":[...], "brand", "slogan"}
}
사용: python3 render_ed.py spec.json out.mp4 [--frames dir]
"""
import json, subprocess, sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
F = "/root/fonts/"
IVORY = (242, 235, 221); GOLD = (214, 196, 160); DIM = (170, 158, 138); BG = (14, 13, 12)
FONTS = {
    "hook": (F + "Hahmlet[wght].ttf", 104),
    "big": (F + "Hahmlet[wght].ttf", 92),
    "endbig": (F + "Hahmlet[wght].ttf", 66),
    "quote": (F + "Hahmlet[wght].ttf", 64),
    "sub": (F + "Pretendard-SemiBold.otf", 46),
    "kicker": (F + "Pretendard-SemiBold.otf", 62),  # 첫 화면 "로마 황제가 일기에 쓴 한 줄" (썸네일에서도 잘 보이게)
    "src": (F + "Pretendard-SemiBold.otf", 34),
    "slogan": (F + "Hahmlet[wght].ttf", 98),
    "cta": (F + "Pretendard-SemiBold.otf", 36),
    "cap": (F + "Pretendard-SemiBold.otf", 50),
    "small": (F + "Pretendard-SemiBold.otf", 40),
}
# 2026-11-11 영어 채널(The Emperor's Diary, @EmperorsDiary-en): ED_LANG=en 이면 영어 글꼴·문구 (한국어 편은 그대로)
LANG = os.environ.get("ED_LANG", "ko")
TXT = {"slogan1": "매일 밤,", "slogan2": "황제처럼 생각하라", "brand": "황제의 일기", "lead": "오늘의 한 줄이 마음에 남았다면",
       "like": "좋아요", "sub": "구독", "follow": "팔로우", "share": "친구에게 공유",
       "thanks1": "좋아요와 {s}는 영상 제작에", "thanks2": "큰 힘이 됩니다. 감사합니다.", "tonight": "오늘의 할 일"}
if LANG == "en":
    EF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "en", "fonts") + "/"
    # 2026-11-11 02:09 대표(02:08 지시 대체): 미국 스토아 쇼츠 문법 — 짧은 펀치 문장은 굵은 산세리프, 황제 인용은 우아한 세리프(Playfair). en/SHORTS_EN.md
    FONTS.update({"hook": (EF + "Inter-Bold.ttf", 96), "big": (EF + "Inter-Bold.ttf", 80), "cap": (EF + "Inter-Bold.ttf", 52),
                  "quote": (EF + "PlayfairDisplay-SemiBoldItalic.ttf", 70), "endbig": (EF + "Inter-Bold.ttf", 60),
                  "slogan": (EF + "PlayfairDisplay-Bold.ttf", 80), "sub": (EF + "Inter-SemiBold.ttf", 38), "kicker": (EF + "Inter-Bold.ttf", 44),
                  "src": (EF + "Inter-SemiBold.ttf", 32), "cta": (EF + "Inter-SemiBold.ttf", 32), "small": (EF + "Inter-SemiBold.ttf", 36)})
    TXT.update({"slogan1": "Every night,", "slogan2": "think like an emperor", "brand": "The Emperor's Diary", "lead": "If this line stayed with you",
                "like": "Like", "sub": "Subscribe", "follow": "Follow", "share": "Share",
                "thanks1": "A like and a {s}", "thanks2": "keep these coming. Thank you.", "tonight": "TONIGHT'S TASK"})
    F = EF
COLOR = {"cap": IVORY, "slogan": IVORY, "cta": IVORY, "hook": IVORY, "big": IVORY, "endbig": IVORY, "quote": IVORY, "sub": GOLD, "kicker": GOLD, "src": DIM, "small": DIM}
LH = {"cap": 1.42, "slogan": 1.3, "cta": 1.4, "hook": 1.28, "big": 1.3, "endbig": 1.4, "quote": 1.45, "sub": 1.4, "kicker": 1.3, "src": 1.4, "small": 1.45}
_fc = {}
WGT = {}

# 2026-11-03 대표: 숏폼 템플릿 A/B/C 를 돌아가며 쓴다 (spec["theme"])
#  A 밤·상아(기존): 어두운 명암 그림 + 상단 그늘 + 왼쪽 정렬 상아색 글씨
#  B 대리석·낮: 밝은 금빛 그림 + 상단 크림색 판 + 가운데 정렬 먹색 글씨, 테라코타 포인트
#  C 시네마: 차가운 청회색 그림 + 위아래 검은 띠(레터박스) + 가운데 정렬, 은빛 포인트
THEME = {"name": "A", "align": "left", "top": 250}
def set_theme(name):
    global IVORY, GOLD, DIM
    name = (name or "A").upper()
    THEME.clear()
    if name == "B":
        ink, acc, dim = (43, 33, 24), (150, 72, 40), (110, 96, 80)
        THEME.update(name="B", align="center", top=210, ink=ink, shadow=0, wm=(60, 48, 36))
        for k in COLOR: COLOR[k] = ink
        COLOR.update(sub=acc, kicker=acc, src=dim, small=dim)
    elif name == "C":
        iv, acc, dim = (236, 238, 240), (196, 204, 212), (150, 158, 166)
        THEME.update(name="C", align="center", top=96, bar_t=580, bar_b=360, wm=(255, 255, 255))
        for k in COLOR: COLOR[k] = iv
        COLOR.update(sub=acc, kicker=acc, src=dim, small=dim)
    else:
        THEME.update(name="A", align="left", top=250, wm=(255, 255, 255))
        for k in COLOR: COLOR[k] = IVORY
        COLOR.update(sub=GOLD, kicker=GOLD, src=DIM, small=DIM)


def font(style):
    p, s = FONTS[style]
    if (p, s) not in _fc:
        f = ImageFont.truetype(p, s)
        if "Hahmlet" in p:
            try: f.set_variation_by_axes([WGT.get(style, 600)])
            except Exception: pass
        _fc[(p, s)] = f
    return _fc[(p, s)]


def ease(x): return 0 if x <= 0 else 1 if x >= 1 else 1 - (1 - x) ** 3


def draw_block(img, blocks, t, top=250, x0=96):
    """blocks: 같은 컷 안의 글 묶음들. 위에서부터 차례로 쌓는다. 각 묶음은 t0에 0.35초 동안 떠오른다."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = top
    for b in blocks:
        st = b.get("style", "hook"); f = font(st); lh = int(f.size * LH[st])
        a = ease((t - b["t0"]) / 0.35) * (1 - ease((t - b["t1"] + 0.3) / 0.3)) if "t1" in b else ease((t - b["t0"]) / 0.35)
        if b.get("gap"): y += b["gap"]
        if a <= 0:
            y += lh * len(b["lines"]) + b.get("after", 18); continue
        dy = int((1 - a) * 18)
        for ln in b["lines"]:
            col = COLOR[st] + (int(255 * a),)
            cx = x0 if THEME.get("align") != "center" else (W - d.textlength(ln, font=f)) / 2
            if st == "quote" and THEME.get("align") != "center":  # 원문 앞 금색 세로선
                d.rectangle([x0 - 34, y + 10 + dy, x0 - 28, y + lh - 6 + dy], fill=COLOR["sub"] + (int(255 * a),))
            # 글자 그림자(가독성) — B(밝은 판)는 그림자 없음
            if THEME.get("shadow", 1): d.text((cx + 2, y + dy + 3), ln, font=f, fill=(0, 0, 0, int(150 * a)))
            d.text((cx, y + dy), ln, font=f, fill=col)
            y += lh
        y += b.get("after", 18)
    img.alpha_composite(layer)


def draw_caps(img, caps, t, y0=1150):
    """성우가 말만 하는 구간의 자막: 화면 가운데쯤, 가운데 정렬, 최대 2줄"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer); f = font("cap"); lh = int(f.size * LH["cap"])
    for c in caps:
        a = ease((t - c["t0"]) / 0.18) * (1 - ease((t - c["t1"]) / 0.18))
        if a <= 0: continue
        n = len(c["lines"])
        if THEME.get("name") == "C": y0 = H - THEME["bar_b"] / 2 - 20
        y = y0 - (n * lh) / 2
        if THEME.get("name") == "B":  # 크림색 둥근 판 위 먹색 글씨
            wmax = max(d.textlength(ln, font=f) for ln in c["lines"])
            d.rounded_rectangle([(W - wmax) / 2 - 34, y - 18, (W + wmax) / 2 + 34, y + n * lh + 6], 26, fill=(246, 239, 226, int(225 * a)))
        for ln in c["lines"]:
            w = d.textlength(ln, font=f); x = (W - w) / 2
            if THEME.get("name") == "B":
                d.text((x, y), ln, font=f, fill=THEME["ink"] + (int(255 * a),)); y += lh; continue
            for dx, dy in ((0, 3), (2, 2), (-2, 2)): d.text((x + dx, y + dy), ln, font=f, fill=(0, 0, 0, int(170 * a)))
            d.text((x, y), ln, font=f, fill=COLOR["cap"] + (int(255 * a),)); y += lh
    img.alpha_composite(layer)


def top_shade(img, h=980, strength=200):
    if THEME.get("name") == "B":  # 위쪽 크림색 판(그라데이션)
        # 글이 놓이는 위쪽 720px 은 거의 불투명, 그 아래 260px 동안 흐려진다 (어두운 그림에서도 먹색 글씨가 읽히게)
        m = np.zeros((H, W), np.uint8); m[:720, :] = 238; m[720:980, :] = np.linspace(238, 0, 260).astype(np.uint8)[:, None]
        sh = Image.new("RGBA", img.size, (246, 239, 226, 0)); sh.putalpha(Image.fromarray(m)); img.alpha_composite(sh); return
    if THEME.get("name") == "C":  # 레터박스: 위아래 검은 띠 + 띠 경계 부드럽게
        bt, bb = THEME["bar_t"], THEME["bar_b"]
        m = np.zeros((H, W), np.uint8); m[:bt, :] = 255; m[H - bb:, :] = 255
        m[bt:bt + 140, :] = np.linspace(200, 0, 140).astype(np.uint8)[:, None]
        m[H - bb - 120:H - bb, :] = np.linspace(0, 180, 120).astype(np.uint8)[:, None]
        sh = Image.new("RGBA", img.size, (6, 7, 9, 0)); sh.putalpha(Image.fromarray(m)); img.alpha_composite(sh); return
    g = np.linspace(strength, 0, h).astype(np.uint8)
    mask = np.zeros((H, W), np.uint8); mask[:h, :] = g[:, None]
    shade = Image.new("RGBA", img.size, (8, 7, 6, 0)); shade.putalpha(Image.fromarray(mask))
    img.alpha_composite(shade)
    b = np.linspace(0, 120, 520).astype(np.uint8)
    m2 = np.zeros((H, W), np.uint8); m2[H - 520:, :] = b[:, None]
    s2 = Image.new("RGBA", img.size, (8, 7, 6, 0)); s2.putalpha(Image.fromarray(m2))
    img.alpha_composite(s2)


def watermark(img, a=0.55):
    """처음 화면·오늘 밤 할 일 화면 공통: 같은 글꼴·같은 위치(H-330)"""
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(F + "CormorantSC-SemiBold.ttf", 34)
    txt = "THE EMPEROR'S DIARY"
    w = d.textlength(txt, font=f)
    yy = H - 110 if THEME.get("name") == "C" else H - 330
    if LANG == "en": yy = H - 430   # 2026-11-11: 영어판은 화면 아래 20%(쇼츠 버튼 영역)를 비운다
    d.text(((W - w) / 2, yy), txt, font=f, fill=THEME.get("wm", (255, 255, 255)) + (int(255 * a),))


def read_frames(path, n, speed=1.0):
    """영상을 1080x1920으로 꽉 채워(가운데 자르기) n 프레임 읽는다. speed<1 이면 느리게."""
    from clip_fetch import ensure; path = ensure(path)   # 2026-11-06: 저장소에 없는 생성 클립은 받아 온다(없으면 검은 화면 대신 멈춤)
    vf = f"setpts=PTS/{speed},fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    # 2026-11-03: 긴 편(55초+)에서 메모리 부족(7GB) → 디스크 memmap 에 담는다
    import tempfile
    _fp = tempfile.NamedTemporaryFile(prefix="edfr_", dir=os.environ.get("ED_TMP", "/tmp"), delete=False).name
    mm = np.memmap(_fp, np.uint8, "w+", shape=(n, H, W, 3)); os.unlink(_fp)   # 2026-11-04: 렌더가 끝나면 저절로 사라지게 (남은 파일 28GB로 디스크가 찼음)
    last = None; got = 0
    for i in range(n):
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            mm[i] = last if last is not None else 0; continue
        last = np.frombuffer(buf, np.uint8).reshape(H, W, 3); mm[i] = last
    p.stdout.close(); p.wait()
    return mm


def kb_frames(path, n, move="in", amt=0.10):
    """정지 그림 → 천천히 줌인/줌아웃/위아래 패닝 (켄 번스). 비용 0."""
    src = Image.open(path).convert("RGB")
    sw, sh = src.size; sc = max(W / sw, H / sh) * (1 + amt + 0.02)
    big = src.resize((int(sw * sc), int(sh * sc)), Image.LANCZOS); BW, BH = big.size
    class _KB:  # 2026-11-03: 프레임을 미리 다 만들지 않고 필요할 때 만든다(메모리 절약)
        def __len__(self): return n
        def __getitem__(self, i): return _kb(i)
    def _kb(i):
        p = i / max(1, n - 1); p = p * p * (3 - 2 * p)  # 부드럽게
        if move == "in": z = 1 + amt * p
        elif move == "out": z = 1 + amt * (1 - p)
        else: z = 1 + amt * 0.6
        cw, ch = W * (BW / W) / ((1 + amt + 0.02)) / z * (1 + amt + 0.02) / (BW / W) * (BW / W), 0
        cw = BW / ((1 + amt + 0.02) * 1.0) / z * (1 + amt + 0.02) / (1 + amt + 0.02)
        cw = (W / (max(W / sw, H / sh) * (1 + amt + 0.02))) * sc / z; ch = cw * H / W
        cx, cy = BW / 2, BH / 2
        if move == "up": cy = BH / 2 + (BH - ch) / 2 * (0.8 - 1.6 * p)
        elif move == "down": cy = BH / 2 - (BH - ch) / 2 * (0.8 - 1.6 * p)
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        return np.asarray(big.resize((W, H), Image.BILINEAR, box=box))
    return _KB()


def end_card(spec_end, base, t):
    img = Image.fromarray(base).convert("RGBA").filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(Image.new("RGBA", img.size, BG + (int(220 * ease(t / 0.5)),)))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    def ct(y, txt, st, al, col=None, track=0):
        f = font(st)
        if track:
            ws = [d.textlength(c, font=f) for c in txt]; g = f.size * track; tot = sum(ws) + g * (len(txt) - 1); x = (W - tot) / 2
            for c, w in zip(txt, ws): d.text((x, y), c, font=f, fill=(col or COLOR[st]) + (int(255 * al),)); x += w + g
        else:
            w = d.textlength(txt, font=f); d.text(((W - w) / 2, y + int((1 - al) * 12)), txt, font=f, fill=(col or COLOR[st]) + (int(255 * al),))
    a1 = ease((t - 0.2) / 0.4); a2 = ease((t - 0.5) / 0.4); a3 = ease((t - 1.0) / 0.4)
    ct(640, spec_end["kicker"], "sub", a1, col=GOLD)
    f = font("endbig"); lh = int(f.size * LH["endbig"]); y = 730
    for ln in spec_end["lines"]: ct(y, ln, "endbig", a2); y += lh
    y += 110
    for ln in [x for x in [spec_end.get("source"), spec_end.get("slogan")] if x]: ct(y, ln, "small", a3, col=DIM); y += 62
    img.alpha_composite(layer)
    watermark(img, 0.55)  # 첫 화면과 동일한 위치·글꼴
    return img


def _icon(d, kind, cx, cy, r, col, w):
    if kind == "like":
        import math as _m
        pts = []
        for i in range(120):
            t = 2 * _m.pi * i / 120
            x = 16 * _m.sin(t) ** 3; y = -(13 * _m.cos(t) - 5 * _m.cos(2 * t) - 2 * _m.cos(3 * t) - _m.cos(4 * t))
            pts.append((cx + x * r / 17, cy + y * r / 17 - r * 0.05))
        d.line(pts + [pts[0]], fill=col, width=w, joint="curve")
    elif kind == "follow":
        d.ellipse([cx - r * 0.42 - r * 0.2, cy - r * 0.95, cx + r * 0.42 - r * 0.2, cy - r * 0.11], outline=col, width=w)
        d.arc([cx - r * 0.95 - r * 0.2, cy - r * 0.05, cx + r * 0.95 - r * 0.2, cy + r * 1.75], 180, 360, fill=col, width=w)
        px, py = cx + r * 0.78, cy - r * 0.35
        d.line([(px - r * 0.3, py), (px + r * 0.3, py)], fill=col, width=w); d.line([(px, py - r * 0.3), (px, py + r * 0.3)], fill=col, width=w)
    elif kind == "share":
        p = [(cx - r, cy - r * 0.05), (cx + r, cy - r * 0.85), (cx + r * 0.25, cy + r * 0.95), (cx - r * 0.05, cy + r * 0.15)]
        d.line(p + [p[0]], fill=col, width=w, joint="curve"); d.line([(cx - r * 0.05, cy + r * 0.15), (cx + r, cy - r * 0.85)], fill=col, width=w)


_SPR = {}
# 2026-11-04 대표: 마지막 화면을 롱폼 인트로의 금색 디자인으로 ("좋아요 구독 그쪽도 같이 테두리 다 변경… 그 톤으로")
LG = (201, 164, 92); LG_HI = (236, 212, 160); LG_KO = (222, 196, 140); LG_BG = (10, 9, 8)
def cta_sprite(kind, D=176):
    """좋아요·팔로우/구독·공유 버튼: 검은 원 + 은은히 빛나는 금색 가는 테두리 + 금색 선 아이콘 (4배로 그려 매끈하게)"""
    if kind in _SPR: return _SPR[kind]
    import math as _m
    S4 = 4; N = (D + 40) * S4; im = Image.new("RGBA", (N, N), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    c = N / 2; R = D * S4 / 2 - 2 * S4
    glow = Image.new("RGBA", (N, N), (0, 0, 0, 0)); gg = ImageDraw.Draw(glow)
    gg.ellipse([c - R, c - R, c + R, c + R], outline=LG + (200,), width=int(6 * S4))
    glow = glow.filter(ImageFilter.GaussianBlur(9 * S4)); im.alpha_composite(glow)
    g.ellipse([c - R, c - R, c + R, c + R], fill=(12, 11, 9, 235), outline=LG + (255,), width=int(2.2 * S4))
    col = LG_HI + (255,); w = int(3.6 * S4); r = 29 * S4
    if kind == "like":
        pts = []
        for i in range(240):
            t = 2 * _m.pi * i / 240
            x = 16 * _m.sin(t) ** 3; y = -(13 * _m.cos(t) - 5 * _m.cos(2 * t) - 2 * _m.cos(3 * t) - _m.cos(4 * t))
            pts.append((c + x * r / 16.5, c + y * r / 16.5 - r * 0.08))
        g.line(pts + [pts[0], pts[1]], fill=col, width=w, joint="curve")
    elif kind == "follow":
        hx = c - r * 0.18
        g.ellipse([hx - r * 0.38, c - r * 0.92, hx + r * 0.38, c - r * 0.16], outline=col, width=w)
        g.arc([hx - r * 0.82, c - r * 0.02, hx + r * 0.82, c + r * 1.5], 200, 340, fill=col, width=w)
        px, py = c + r * 0.78, c - r * 0.28
        g.line([(px - r * 0.27, py), (px + r * 0.27, py)], fill=col, width=w); g.line([(px, py - r * 0.27), (px, py + r * 0.27)], fill=col, width=w)
    elif kind == "bell":
        top = c - r * 0.85
        g.arc([c - r * 0.62, top, c + r * 0.62, top + r * 1.25], 180, 360, fill=col, width=w)
        g.line([(c - r * 0.62, top + r * 0.62), (c - r * 0.66, c + r * 0.42), (c - r * 0.86, c + r * 0.62), (c + r * 0.86, c + r * 0.62), (c + r * 0.66, c + r * 0.42), (c + r * 0.62, top + r * 0.62)], fill=col, width=w, joint="curve")
        g.arc([c - r * 0.24, c + r * 0.5, c + r * 0.24, c + r * 0.98], 0, 180, fill=col, width=w)
        g.ellipse([c - r * 0.09, top - r * 0.2, c + r * 0.09, top - r * 0.02], fill=col)
    elif kind == "share":
        a = (c - r * 0.92, c - r * 0.02); b = (c + r * 0.9, c - r * 0.8); t3 = (c + r * 0.12, c + r * 0.95); m = (c - r * 0.12, c + r * 0.12)
        g.line([a, b, t3, m, a], fill=col, width=w, joint="curve"); g.line([m, b], fill=col, width=w)
    out = im.resize((D + 40, D + 40), Image.LANCZOS); _SPR[kind] = out
    return out


def _coin_gold(path, size=300):
    """롱폼 인트로와 같은 금색 주화 (longform.coin_gold 와 같은 계산)"""
    c = Image.open(path).convert("L").resize((size, size), Image.LANCZOS); a = np.array(c).astype(np.float32) / 255.0
    rgb = np.stack([a * LG[0] * 1.15, a * LG[1] * 1.15, a * LG[2] * 1.1], -1)
    alpha = np.clip((a - 0.08) * 1.6, 0, 1) * 255
    yy, xx = np.mgrid[0:size, 0:size]; m = ((xx - size / 2) ** 2 + (yy - size / 2) ** 2) <= (size / 2 - 2) ** 2
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha * m]).astype(np.uint8), "RGBA")


_OUT = {}
def _outro_bg():
    if "bg" in _OUT: return _OUT["bg"]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - W / 2) / 620) ** 2 + ((yy - 760) / 760) ** 2))[..., None]   # 가운데 따뜻한 빛, 가장자리는 어둡게
    arr = np.clip(np.array(LG_BG, np.float32) + g * np.array([34, 24, 10], np.float32), 0, 255).astype(np.uint8)
    _OUT["bg"] = Image.fromarray(arr).convert("RGBA"); return _OUT["bg"]


def _glint_line(d, layer, cx, y, w, a, t):
    """금색 가는 선 + 선을 따라 지나가는 빛 (롱폼 EPISODE 카드와 같은 느낌)"""
    d.line([(cx - w / 2, y), (cx + w / 2, y)], fill=LG + (int(210 * a),), width=2)
    gx = cx - w / 2 + (w * ((t * 0.45) % 1.0))
    gl = Image.new("RGBA", layer.size, (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([gx - 22, y - 7, gx + 22, y + 7], fill=(255, 236, 190, int(230 * a)))
    layer.alpha_composite(gl.filter(ImageFilter.GaussianBlur(7)))


def _track(d, y, txt, f, col, a, track):
    ws = [d.textlength(c, font=f) for c in txt]; g = f.size * track; x = (W - (sum(ws) + g * (len(txt) - 1))) / 2
    for c, w in zip(txt, ws): d.text((x, y), c, font=f, fill=col + (int(255 * a),)); x += w + g


def outro(spec_o, base, t, platform="reels"):
    """마지막(롱폼 인트로 금색 디자인): (1) 슬로건 '매일 밤, 황제처럼 생각하라' + 황제의 일기  (2) 금빛 주화·THE EMPEROR'S DIARY·황제의 일기 + 좋아요·팔로우(구독)·공유"""
    img = _outro_bg().copy()
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    p1 = spec_o.get("p1", 3.4)
    def ctext(y, txt, st, a, col=None):
        f = font(st); w = d.textlength(txt, font=f); d.text(((W - w) / 2, y), txt, font=f, fill=(col or COLOR[st]) + (int(255 * a),))
    if "coin" not in _OUT: _OUT["coin"] = _coin_gold(spec_o.get("logo", "/home/claude/logo/logo_final.png"))
    if t < p1:
        a1 = ease((t - 0.35) / 0.5); a2 = ease((t - 1.6) / 0.5); fo = 1 - ease((t - (p1 - 0.35)) / 0.35)
        ctext(700, TXT["slogan1"], "sub", a1 * fo, col=LG)
        ctext(780, TXT["slogan2"], "slogan", a1 * fo, col=LG_HI)
        _glint_line(d, layer, W / 2, 962, 120, a2 * fo, t)
        ctext(996, TXT["brand"], "sub", a2 * fo, col=LG_KO)
    else:
        u = t - p1; a = ease(u / 0.5)
        cx, cy, R = W // 2, 470, 168
        # 금빛 링(빛 번짐) + 주화
        ring = Image.new("RGBA", img.size, (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
        rd.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(244, 200, 120, int(235 * a)), width=4)
        layer.alpha_composite(ring.filter(ImageFilter.GaussianBlur(9))); layer.alpha_composite(ring)
        coin = _OUT["coin"].copy(); coin.putalpha(coin.split()[3].point(lambda v: int(v * a)))
        layer.alpha_composite(coin, (cx - coin.width // 2, cy - coin.height // 2))
        ef = ImageFont.truetype(F + "CormorantSC-SemiBold.ttf", 56)
        _track(d, cy + R + 52, "THE EMPEROR'S DIARY", ef, LG, ease((u - 0.25) / 0.5), 0.22)
        kf = ImageFont.truetype(F + "Hahmlet[wght].ttf", 46) if LANG != "en" else ImageFont.truetype(F + "PlayfairDisplay-Bold.ttf", 48)
        try: kf.set_variation_by_axes([600])
        except Exception: pass
        aw = ease((u - 0.45) / 0.5)
        w = d.textlength(TXT["brand"], font=kf); d.text(((W - w) / 2, cy + R + 140), TXT["brand"], font=kf, fill=LG_KO + (int(255 * aw),))
        _glint_line(d, layer, W / 2, cy + R + 228, 150, aw, u)
        # 아래: 안내 문구 + 좋아요 / 팔로우(구독) / 공유 — 금색 테두리·아이콘·글씨
        ab = ease((u - 0.6) / 0.45)
        ctext(1030, spec_o.get("lead", TXT["lead"]), "small", ab, col=LG_KO)
        items = [("like", TXT["like"]), ("follow" if platform == "reels" else "bell", TXT["follow"] if platform == "reels" else TXT["sub"]), ("share", TXT["share"])]
        gap = 290; x0 = W / 2 - gap
        for k, (kind, lab) in enumerate(items):
            ak = ease((u - 0.7 - k * 0.15) / 0.4); bx = x0 + k * gap; by = 1220 + int((1 - ak) * 14)
            sp = cta_sprite(kind); sp2 = sp.copy(); sp2.putalpha(sp.split()[3].point(lambda v: int(v * ak)))
            layer.alpha_composite(sp2, (int(bx - sp.width / 2), int(by - sp.height / 2)))
            f = font("cta"); w = d.textlength(lab, font=f); d.text((bx - w / 2, by + 112), lab, font=f, fill=LG_HI + (int(240 * ak),))
    img.alpha_composite(layer)
    return img


def main(spec_path, out, frames_dir=None, platform="reels"):
    spec = json.load(open(spec_path))
    set_theme(spec.get("theme", "A"))
    xf = 0.4  # 컷 사이 겹침
    cuts = []
    for c in spec["cuts"]:
        n = int(round(c["dur"] * FPS))
        cuts.append((c, kb_frames(c["img"], n, c.get("move", "in"), c.get("amt", 0.10)) if c.get("img") else read_frames(c["v"], n, c.get("speed", 1.0))))
    total = sum(c["dur"] for c, _ in cuts) - xf * (len(cuts) - 1) + spec["end"]["dur"] + (spec["outro"]["dur"] if spec.get("outro") else 0)
    N = int(round(total * FPS))
    starts = []; s = 0
    for c, _ in cuts: starts.append(s); s += c["dur"] - xf
    end_start = s + xf  # 마지막 컷이 끝나는 시점
    end_start = starts[-1] + cuts[-1][0]["dur"] - 0.25
    tmp = out + ".video.mp4"
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    last_base = None
    for i in range(N):
        t = i / FPS
        if t >= end_start and THEME.get("name") != "A": set_theme("A")  # 오늘의 할 일·마지막 화면은 브랜드 공통(A)
        if spec.get("outro") and t >= end_start + spec["end"]["dur"]:
            img = outro(spec["outro"], last_base, t - end_start - spec["end"]["dur"], platform)
        elif t >= end_start:
            img = end_card(spec["end"], last_base, t - end_start)
        else:
            # 현재 컷과 겹침 처리
            k = max(j for j in range(len(cuts)) if starts[j] <= t)
            c, fr = cuts[k]; li = min(int((t - starts[k]) * FPS), len(fr) - 1)
            base = fr[li].astype(np.float32)
            if k + 1 < len(cuts) and t >= starts[k + 1]:
                pass
            if k > 0 and t < starts[k] + xf:
                pc, pfr = cuts[k - 1]; pi = min(int((t - starts[k - 1]) * FPS), len(pfr) - 1)
                a = (t - starts[k]) / xf; base = base * a + pfr[pi].astype(np.float32) * (1 - a)
            fx = spec.get("fx")
            if fx:  # 고급판: 비네트 + 필름 그레인 (영상 층에만)
                global _VIG
                if "_VIG" not in globals():
                    yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * 0.52) / (H / 2)) ** 2)
                    _VIG = (1 - fx.get("vignette", 0.35) * np.clip((r - 0.45) / 0.75, 0, 1) ** 1.6)[..., None].astype(np.float32)
                base = base * _VIG
                g = fx.get("grain", 0)
                if g: base = base + np.random.normal(0, 255 * g, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)
                base = np.clip(base, 0, 255)
            base = base.astype(np.uint8); last_base = base
            img = Image.fromarray(base).convert("RGBA")
            top_shade(img, strength=c.get('shade',200), h=c.get('shade_h',980))
            draw_block(img, [dict(b, t0=b["t0"], t1=b.get("t1", 999)) for b in c["texts"]], t - starts[k], top=c.get("top", THEME.get("top", 250)))
            if c.get("caps"):
                cs = Image.new("RGBA", img.size, (0, 0, 0, 0))
                draw_caps(img, c["caps"], t - starts[k], c.get("cap_y", 1150))
            watermark(img)
        rgb = img.convert("RGB")
        if frames_dir and i % 15 == 0:
            os.makedirs(frames_dir, exist_ok=True); rgb.save(f"{frames_dir}/f{i:04d}.jpg", quality=80)
        enc.stdin.write(np.asarray(rgb).tobytes())
    enc.stdin.close(); enc.wait()
    m = spec["music"]
    fade_out = total - 1.8
    voices = spec.get("voice", [])
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", tmp, "-ss", str(m["start"]), "-i", m["file"]]
    for v in voices: cmd += ["-i", v["file"]]
    mv = m.get("vol", 0.9) if not voices else m.get("bed", 0.22)
    fc = f"[1:a]atrim=0:{total},asetpts=PTS-STARTPTS,afade=t=in:d=1.2,afade=t=out:st={fade_out}:d=1.8,volume={mv}[m]"
    if voices:
        parts = []
        for k, v in enumerate(voices):
            ms = int(v["at"] * 1000)
            fc += f";[{k+2}:a]adelay={ms}|{ms},volume={v.get('vol',1.0)}[v{k}]"; parts.append(f"[v{k}]")
        fc += f";{''.join(parts)}[m]amix=inputs={len(voices)+1}:normalize=0:duration=first,aresample=48000,volume=2.5dB,alimiter=limit=0.85:attack=5:release=60:level=disabled[a]"   # 2026-11-04: 한 번에 거는 loudnorm(목소리 일그러짐) 대신 고정 음량 + 리미터. 목소리 조각은 미리 -16 LUFS 로 맞춰 둔다
        fc = fc.replace(f"volume={mv}[m]", f"volume={mv},apad=whole_dur={total}[m]")
        fc = fc.replace(f"{''.join(parts)}[m]amix", f"[m]{''.join(parts)}amix")
    else:
        fc = fc.replace("[m]", ",loudnorm=I=-16:TP=-1.5[a]")
    subprocess.run(cmd + ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", str(total), out], check=True)
    os.remove(tmp)
    print(f"{out} {total:.1f}s")


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], a[a.index("--frames") + 1] if "--frames" in a else None, a[a.index("--platform") + 1] if "--platform" in a else "reels")
