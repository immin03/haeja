"""밸류노트 로고 (2026-10-23 운영자 확정) — 모든 영상·이미지가 이 함수 하나로 로고를 그린다.

모양: 'Value'(흰색) + 'Note'(아이보리 베이지) — Montserrat ExtraBold
      그 아래 얇은 금색 줄, 그 아래 가운데 '밸류노트'(SUIT Bold, 영문의 약 0.5배, 자간 넓게)
밝은 배경에서는 Value = 네이비, Note·줄·한글 = 금빛을 조금 뺀 아이보리(#AE9260).
사용: from brand import logo_image, paste_logo
      paste_logo(img, x, y, size=46, theme="dark", align="left")   # size = 영문 글자 크기(px)
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "reels", "fonts")
EN_FONT = os.path.join(FONTS, "Montserrat-ExtraBold.ttf")
KO_FONT = os.path.join(FONTS, "SUIT-Bold.ttf")

COLORS = {
    "dark": {"value": (255, 255, 255), "note": (234, 219, 185), "line": (216, 194, 148), "ko": (234, 219, 185)},
    "light": {"value": (11, 27, 51), "note": (174, 146, 96), "line": (192, 168, 124), "ko": (158, 132, 86)},   # 2026-10-23: 금빛에서 조금 빠진 아이보리
}
_cache = {}


def logo_image(size=46, theme="dark", shadow=None, ko=True, line=None):
    """투명 배경 로고 이미지와 (왼쪽 위 여백 pad)를 돌려준다. shadow 기본값: 어두운 테마에서만 은은한 그림자"""
    if shadow is None: shadow = theme == "dark"
    if line is None: line = ko   # 한글이 없는 단독 로고(solo)는 줄도 뺀다
    key = (size, theme, shadow, ko, line)
    if key in _cache: return _cache[key]
    c = COLORS[theme]; fe = ImageFont.truetype(EN_FONT, size); fk = ImageFont.truetype(KO_FONT, max(12, round(size * .5)))
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    wv = tmp.textlength("Value", font=fe); wt = wv + tmp.textlength("Note", font=fe)
    bb = tmp.textbbox((0, 0), "ValueNote", font=fe); top, bot = bb[1], bb[3]
    sp = size * .2; kch = list("밸류노트"); kws = [tmp.textlength(ch, font=fk) for ch in kch]; kw = sum(kws) + sp * (len(kch) - 1)
    lw = max(1, round(size / 40)); ly = bot + round(size * .2); ky = ly + lw + round(size * .16)
    kb = tmp.textbbox((0, 0), "밸류노트", font=fk)
    W_ = int(max(wt, kw) if ko else wt) + 2; H_ = int((ky + kb[3]) if ko else ((ly + lw) if line else bot)) + 2
    pad = int(size * .45) if shadow else 2
    im = Image.new("RGBA", (W_ + 2 * pad, H_ - top + 2 * pad), (0, 0, 0, 0))
    ox, oy = (pad + (W_ - wt) / 2 if (ko and kw > wt) else pad), pad - top

    def draw(d, mono=None):
        d.text((ox, oy), "Value", font=fe, fill=mono or c["value"]); d.text((ox + wv, oy), "Note", font=fe, fill=mono or c["note"])
        if line: d.rectangle([ox, oy + ly, ox + wt, oy + ly + lw - 1], fill=mono or c["line"])
        if ko:
            x = ox + wt / 2 - kw / 2
            for ch, w in zip(kch, kws): d.text((x, oy + ky), ch, font=fk, fill=mono or c["ko"]); x += w + sp
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); draw(ImageDraw.Draw(sh), (0, 0, 0, 255))
        a = sh.getchannel("A").filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(size / 7)).point(lambda q: int(q * .6))
        im.paste((0, 0, 0, 255), (0, 0), a)
    draw(ImageDraw.Draw(im))
    _cache[key] = (im, pad, ox - pad)
    return _cache[key]


def paste_logo(img, x, y, size=46, theme="dark", align="left", shadow=None, ko=True, line=None):
    """img 위 (x, y)에 로고를 붙인다. align='left'면 x가 'V'의 왼쪽, 'center'면 로고 가운데, 'right'면 오른쪽 끝. (너비, 높이)를 돌려준다"""
    im, pad, off = logo_image(size, theme, shadow, ko, line)
    w = im.width - 2 * pad
    if align == "center": x0 = x - w / 2
    elif align == "right": x0 = x - w
    else: x0 = x - off
    pos = (int(round(x0 - pad)), int(round(y - pad)))
    if img.mode == "RGBA": img.alpha_composite(im, (max(0, pos[0]), max(0, pos[1])))
    else: img.paste(im, pos, im)
    return w, im.height - 2 * pad


if __name__ == "__main__":   # 확인용: python3 scripts/brand.py out.png
    import sys
    out = Image.new("RGB", (1200, 420), (11, 27, 51)); paste_logo(out, 60, 50, 46); paste_logo(out, 600, 50, 80, align="center")
    lt = Image.new("RGB", (1200, 200), (246, 244, 238)); paste_logo(lt, 60, 50, 46, "light")
    full = Image.new("RGB", (1200, 620)); full.paste(out, (0, 0)); full.paste(lt, (0, 420)); full.save(sys.argv[1] if len(sys.argv) > 1 else "brand_test.png")


def v_icon(n=1080, mono=False):
    """작은 원·앱 아이콘용 마크 (2026-10-23 확정): 네이비 바탕에 흰 V(Montserrat ExtraBold) + 그 아래 금선.
    mono=True면 투명 바탕에 흰색만 (안드로이드 알림 배지)"""
    import numpy as np
    if mono: im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    else:
        yy, xx = np.mgrid[0:n, 0:n]; r = np.sqrt(((xx - n * .5) / n) ** 2 + (yy / n * .9) ** 2)
        k = np.clip(1 - r * 1.25, 0, 1)[..., None]
        im = Image.fromarray((np.array([11, 20, 36], np.float32) * (1 - k) + np.array([27, 44, 72], np.float32) * k).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im); f = ImageFont.truetype(EN_FONT, int(n * .58))
    bb = d.textbbox((0, 0), "V", font=f); w = bb[2] - bb[0]; h = bb[3] - bb[1]
    d.text((n / 2 - w / 2 - bb[0], n * .45 - h / 2 - bb[1]), "V", font=f, fill=(255, 255, 255, 255))
    lw = w * .92; ly = n * .45 + h / 2 + n * .075; lh = max(2, round(n * .016))
    d.rectangle([n / 2 - lw / 2, ly, n / 2 + lw / 2, ly + lh], fill=(255, 255, 255, 255) if mono else (216, 194, 148, 255))
    return im
