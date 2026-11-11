"""The Emperor's Diary (EN) longform renderer — runs the Korean template engine (../longform.py) with English fonts and English UI strings.
No Korean text is drawn. longform.py stays the single source of the template; this file only swaps fonts and default strings.

Fonts: ED_FONTS (default /root/fonts/) must hold CormorantGaramond-Bold/SemiBold/MediumItalic, CormorantSC-SemiBold, Inter-SemiBold/Bold, PinyonScript-Regular.
Use: ED_FPS=24 python3 longform_en.py <spec.json> [--from s] [--to s] [--preview] [--chunk name]   (same flags as longform.py)
"""
import os, re, sys, types

HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, "..", "longform.py")
STR = [  # (Korean default, English) — default UI strings in longform.py
    ('"FOR TONIGHT  ·  오늘 밤 해 볼 일"', '"FOR TONIGHT"'),
    ('"이전 이야기  ·  EPISODE 1"', '"PREVIOUS STORY"'),
    ('"다음 이야기"', '"NEXT STORY"'),
    ('"좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다."', '"If this helped, like and subscribe. Thank you."'),
    ('"매일 밤, 황제처럼 생각하라"', '"Think like an emperor, every night."'),
    ('"오늘의 일곱 문장"', '"Seven Lines"'),
    ('"구독중"', '"Subscribed"'),
    ('"구독"', '"Subscribe"'),
    ('"좋아요"', '"Like"'),
    ('"황제의 일기"', '"Marcus Aurelius  ·  Meditations"'),
]
FONTMAP = {"ko": "CormorantGaramond-Bold.ttf", "ko6": "CormorantGaramond-SemiBold.ttf", "en": "CormorantSC-SemiBold.ttf", "en5": "CormorantSC-SemiBold.ttf",
           "ui": "Inter-SemiBold.ttf", "uim": "Inter-SemiBold.ttf", "it": "CormorantGaramond-MediumItalic.ttf", "script": "PinyonScript-Regular.ttf",
           "suit": "Inter-Bold.ttf", "suitb": "Inter-Bold.ttf", "suits": "Inter-SemiBold.ttf"}
SCALE = {"ko": 1.12, "ko6": 1.12}
if os.environ.get("ED_EN_TYPE") == "a":   # owner 2026-11-11: type system (a) Cinzel + EB Garamond approved
    FONTMAP = {"ko": "Cinzel-SemiBold.ttf", "ko6": "fs_eb-garamond/eb-garamond-latin-500-italic.woff", "en": "Cinzel-SemiBold.ttf", "en5": "Cinzel-SemiBold.ttf",
               "ui": "fs_eb-garamond/eb-garamond-latin-500-normal.woff", "uim": "fs_eb-garamond/eb-garamond-latin-500-normal.woff", "it": "fs_eb-garamond/eb-garamond-latin-500-italic.woff",
               "script": "PinyonScript-Regular.ttf", "suit": "Inter-Bold.ttf", "suitb": "Inter-Bold.ttf", "suits": "Inter-SemiBold.ttf"}
    SCALE = {"ko": 0.86, "ko6": 1.08, "ui": 1.0}   # Cormorant has a small x-height: draw a little larger than the Hangul face it replaces


def load():
    src = open(SRC, encoding="utf-8").read()
    for a, b in STR:
        src = src.replace(a, b)
    src = src.replace('FONTS = "/root/fonts/"', 'FONTS = os.environ.get("ED_FONTS", "/root/fonts/").rstrip("/") + "/"')
    src = src.replace('if __name__ == "__main__":', 'if __name__ == "__main_disabled__":')
    m = types.ModuleType("longform"); m.__file__ = SRC; sys.modules["longform"] = m
    exec(compile(src, SRC, "exec"), m.__dict__)
    from PIL import ImageFont
    def font(kind, size):
        return ImageFont.truetype(m.FONTS + FONTMAP[kind], int(round(size * SCALE.get(kind, 1.0))))
    m.font = font
    # owner 2026-11-11: end card v2 (endcard_v2.py) — compact brand + ending text A at the top, empty slots for YouTube end-screen elements
    fin0 = m.finale_frame
    def finale_v2(s, t, dur, cache, logo):
        if s.get("endcard") != "v2": return fin0(s, t, dur, cache, logo)
        if "v2" not in cache:
            import numpy as np, cv2
            sys.path.insert(0, HERE); import endcard_v2
            card = np.asarray(endcard_v2.card(False).convert("RGB"))[:, :, ::-1]
            if card.shape[:2] != (m.H, m.W): card = cv2.resize(card, (m.W, m.H))
            cache["v2"] = card.astype(np.float32)
        a = m.ease(t / 1.2) * (1 - m.ease((t - dur + 0.8) / 0.8))
        m._skip_bars = True   # full frame: the slots line up with YouTube's end-screen grid, so no cinema bars over the card
        return (cache["v2"] * a).astype("uint8")
    m.finale_frame = finale_v2
    if os.environ.get("ED_EN_PACE"): pace(m)
    bars0 = m._bars
    def bars(img):
        if getattr(m, "_skip_bars", False): m._skip_bars = False; return img
        return bars0(img)
    m._bars = bars
    left = [l for l in src.splitlines() if re.search(r'"[^"#]*[가-힣][^"#]*"', l.split("#")[0]) and "print(" not in l and '"""' not in l]
    if left: print("note: Korean literals left in renderer (check they are not drawn):", len(left), flush=True)
    return m



def pace(m):
    """2026-11-11 대표: 딥 호라이즌처럼 '지루할 틈 없게' — 추가 생성 비용 0인 편집 리듬 시안 (ED_EN_PACE=1).
    ① 한 클립을 2.6초 안팎으로 쪼개 넓게 → 가깝게 → 더 가깝게 다른 구도로 이어 붙인다(같은 순간을 여러 카메라로 찍은 것처럼 시간은 이어진다).
    ② 장면 사이를 '밀고 들어가기'로 잇는다: 끝 0.2초는 빠르게 확대+흐림, 다음 장면 첫 0.25초는 확대된 상태에서 제자리로 — 배경이 끊기지 않고 이어지는 느낌.
    ③ move.inserts = [[src, 시작(초), 길이(초)], ...] 이면 그 시간에 다른 클립(손·봉인·불 등)을 끼워 넣는다."""
    import math, cv2, numpy as np
    base = m.Clip; SEG = float(os.environ.get("ED_EN_SEG", "2.6"))
    FRAMES = [((1.0, 1.05), ((0, 0), (0, 0))), ((1.30, 1.36), ((-0.05, -0.03), (-0.04, -0.03))), ((1.52, 1.58), ((0.06, 0.04), (0.05, 0.04)))]

    def blur_zoom(img, z, amt):
        if z != 1.0:
            h, w = img.shape[:2]; M = cv2.getRotationMatrix2D((w / 2, h / 2), 0, z); img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)
        if amt > 0.05:
            k = int(3 + amt * 40) | 1; ker = np.zeros((k, k), np.float32); ker[k // 2, :] = 1.0 / k
            img = cv2.addWeighted(img, 1 - min(amt, 0.85), cv2.filter2D(img, -1, ker), min(amt, 0.85), 0)
        return img

    class PaceClip(base):
        def __init__(self, path, move, start=0.0, face=None):
            super().__init__(path, move, start, face)
            self.m0 = dict(self.move); self.ins = []
            for src, at, ln in (move or {}).get("inserts", []):
                self.ins.append((base(os.path.join(os.path.dirname(path), src + ".mp4"), {"zoom": [1.05, 1.12]}, 0, None), at, ln))
            self.seed = sum(map(ord, os.path.basename(path)))

        def frame(self, p, t, dur):
            for c, at, ln in self.ins:
                if at <= t < at + ln: img = c.frame((t - at) / ln, t - at, ln); return self._edges(img, t, dur)
            n = max(1, int(round(dur / SEG))) if dur > SEG * 1.3 else 1
            seg = dur / n; k = min(int(t / seg), n - 1); lp = (t - k * seg) / seg
            if n > 1:
                (z0, z1), pan = FRAMES[(k + self.seed) % len(FRAMES)] if k else FRAMES[0]
                self.move = {**self.m0, "zoom": [z0, z1], "pan": [list(pan[0]), list(pan[1])]}
            img = super().frame(lp if n > 1 else p, t, dur)
            self.move = self.m0
            if n > 1 and k > 0 and t - k * seg < 0.12: img = blur_zoom(img, 1.0 + 0.06 * (1 - (t - k * seg) / 0.12), 0.35)   # 구도 바뀔 때 살짝 튕기듯
            return self._edges(img, t, dur)

        def _edges(self, img, t, dur):
            if t < 0.25: e = 1 - t / 0.25; img = blur_zoom(img, 1.0 + 0.22 * e * e, 0.8 * e)           # 밀고 들어온 뒤 제자리로
            elif dur - t < 0.2: e = 1 - (dur - t) / 0.2; img = blur_zoom(img, 1.0 + 0.25 * e * e, 0.8 * e)   # 다음 장면으로 밀고 들어감
            return img
    m.Clip = PaceClip


if __name__ == "__main__":
    L = load(); a = sys.argv[1:]; spec = a[0]
    tf = float(a[a.index("--from") + 1]) if "--from" in a else 0.0
    tt = float(a[a.index("--to") + 1]) if "--to" in a else None
    if "--plan" in a: L.build(spec, 0, 0.001, True, True); sys.exit()
    ch = a[a.index("--chunk") + 1] if "--chunk" in a else None
    L.build(spec, tf, tt, "--preview" in a, "--audio-only" in a, ch)

