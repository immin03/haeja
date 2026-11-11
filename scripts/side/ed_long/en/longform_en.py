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
    bars0 = m._bars
    def bars(img):
        if getattr(m, "_skip_bars", False): m._skip_bars = False; return img
        return bars0(img)
    m._bars = bars
    left = [l for l in src.splitlines() if re.search(r'"[^"#]*[가-힣][^"#]*"', l.split("#")[0]) and "print(" not in l and '"""' not in l]
    if left: print("note: Korean literals left in renderer (check they are not drawn):", len(left), flush=True)
    return m


if __name__ == "__main__":
    L = load(); a = sys.argv[1:]; spec = a[0]
    tf = float(a[a.index("--from") + 1]) if "--from" in a else 0.0
    tt = float(a[a.index("--to") + 1]) if "--to" in a else None
    if "--plan" in a: L.build(spec, 0, 0.001, True, True); sys.exit()
    ch = a[a.index("--chunk") + 1] if "--chunk" in a else None
    L.build(spec, tf, tt, "--preview" in a, "--audio-only" in a, ch)
