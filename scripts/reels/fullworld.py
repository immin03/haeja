"""꽉 찬 그림 장면 (2026-11-01 14:06 대표님 결정 'A안': 쇼츠·릴스도 그림이 화면을 꽉 채우게)

opt-in: 장면에 "full": {...} 이 있을 때만 쓴다(없으면 지금 화면 그대로). 장면 type(hook·photo·cta 등)은 길이·마무리 계산에만 쓰이고 그림은 그리지 않는다.
  "full": {"img": "<scripts/blog/media/lib 파일>", "label": "왼쪽 위 종이 라벨 한 줄(명사형)",
           "num": "펜 숫자(선택)", "num_line": 0, "num_frac": .3, "tone": "loss|ink|gold", "focus_x": .5, "focus_y": .5}
화면: 위 제목 띠(배너, draw_banner_soft) 그대로 · 그 아래 화면 끝까지 그림이 꽉 참(천천히 켄 번즈) · 왼쪽 위 아이보리 종이 라벨 + 펜 숫자·금색 밑줄 ·
      자막은 아래쪽 어두운 그라데이션 위. 펜 동그라미로 그림을 가리지 않는다. 장면이 바뀔 때 0.35초 겹쳐 넘어간다.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONTS = os.path.join(os.path.dirname(__file__), "fonts")
XF = .35
PAPER = (246, 240, 226); INK = (24, 38, 66); RED = (196, 52, 60); GOLD = (214, 172, 84)
TONES = {"loss": RED, "ink": INK, "gold": (168, 122, 36), "good": (40, 128, 86)}
_C = {}


def _img(name):
    if name not in _C:
        p = name if os.path.isabs(name) else os.path.join(ROOT, "scripts", "blog", "media", "lib", name)
        _C[name] = Image.open(p).convert("RGB")
    return _C[name]


def _grad():
    if "g" not in _C:
        g = np.zeros((H, 1), np.float32); n = 640
        g[H - n:, 0] = np.clip(np.arange(n) / n, 0, 1) ** 1.4 * 215
        _C["g"] = Image.fromarray(np.repeat(g, W, 1).astype(np.uint8), "L")
    return _C["g"]


def _pen(size):
    k = ("pen", size)
    if k not in _C: _C[k] = ImageFont.truetype(os.path.join(FONTS, "NanumPenScript-Regular.ttf"), size)
    return _C[k]


def picture(E, s, u):
    f = s["sc"]["full"]; src = _img(f["img"])
    z = 1.0 + .07 * E.clamp(u / max(s["dur"], 1.0))
    r = max(W / src.width, H / src.height) * z
    im = src.resize((int(src.width * r) + 1, int(src.height * r) + 1), Image.BILINEAR)
    x0 = int((im.width - W) * f.get("focus_x", .5)); y0 = int((im.height - H) * f.get("focus_y", .5))
    return im.crop((x0, y0, x0 + W, y0 + H))


def overlay(E, img, s, u):
    """왼쪽 위 종이 라벨 + 펜 숫자 + 금색 밑줄"""
    f = s["sc"]["full"]; L = s["L"]
    lab = f.get("label"); num = f.get("num")
    if not lab and not num: return img
    a = E.prog(u, .15, .55)
    if a <= 0: return img
    lf = E.fit_font(lab or "", "ExtraBold", 46, 820) if lab else None
    pf = _pen(f.get("num_size", 150))
    d0 = ImageDraw.Draw(img)
    lw = d0.textlength(lab, font=lf) if lab else 0
    nw = d0.textlength(num, font=pf) if num else 0
    X, Y = 56, f.get("y", 420)
    bw = max(lw, nw) + 72; bh = 96 + (150 if num else 0)
    card = Image.new("RGBA", (int(bw) + 30, int(bh) + 30), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([12, 16, bw + 12, bh + 16], 10, fill=(0, 0, 0, int(90 * a)))
    card = card.filter(ImageFilter.GaussianBlur(7)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, bw, bh], 10, fill=(*PAPER, int(250 * a)))
    oy = int((1 - a) * 16)
    img.paste(card, (X, Y + oy), card)
    d = ImageDraw.Draw(img)
    if lab: d.text((X + 36, Y + oy + 50), lab, font=lf, fill=E.mix(PAPER, INK, a), anchor="lm")
    if num:
        t0 = E.y_at(L, f.get("num_line", 0), f.get("num_frac", .3)); p = E.prog(u, t0, t0 + .45)
        if p > 0:
            col = TONES.get(f.get("tone", "loss"), RED)
            ny = Y + oy + 96 + 70
            d.text((X + 36, ny + (1 - p) * 10), num, font=pf, fill=E.mix(PAPER, col, p), anchor="lm")
            q = E.prog(u, t0 + .35, t0 + .9)
            if q > 0:
                x1 = X + 36 + nw * q; yy = ny + 62
                d.line([(X + 32, yy), (x1, yy - 4)], fill=GOLD, width=9)
    return img


def scene_img(E, s, u):
    img = picture(E, s, u)
    img.paste(Image.new("RGB", (W, H), (6, 12, 24)), (0, 0), _grad())
    return overlay(E, img, s, u)


def render(E, T, s, scenes):
    """현재 장면이 꽉 찬 그림 장면일 때 한 프레임 (자막·제목 띠는 engine.frame 이 얹는다)"""
    u = T - s["start"]; img = scene_img(E, s, u)
    i = scenes.index(s)
    if i > 0 and u < XF and scenes[i - 1]["sc"].get("full"):
        p = scenes[i - 1]; prev = scene_img(E, p, p["dur"] - 1 / 30)
        img = Image.blend(prev, img, E.ease_io(u / XF))
    return img
