"""롱폼 썸네일 v6 (2026-11-10 빼빼로 편에서 쓴 톤을 스크립트로 정리, 2026-11-11 빼빼로데이 3안)
- 네이비 바탕 왼쪽에 큰 글씨, 오른쪽에 사진(왼쪽 가장자리는 바탕에 녹임)
- 맨 위 띠: 배경은 강조 줄과 같은 색, 글씨는 네이비 (11/11 대표: 통일감)
- 핵심 주제(종목·제품명·핵심 숫자)가 가장 크게, 보조 말은 작게
- 글자 테두리 없음, 그림자만 / SUIT 글꼴만 / 밸류노트 로고 오른쪽 위
사용: python3 scripts/reels/thumb_v6.py spec.json out.jpg
spec 예:
{"photo": "il_L261108p_thumb_sticks.jpeg", "focus": [0.6, 0.5], "photo_x": 0.38,
 "tag": "11.11 빼빼로데이",
 "lines": [["위기의 롯데", 84, "ivory"], ["빼빼로에 건", 150, "gold"], ["1조 원", 170, "gold"]]}
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from brand import paste_logo

W, H = 1280, 720
NAVY = (11, 27, 51); BG = (14, 22, 40)
COL = {"ivory": (246, 241, 232), "gold": (240, 208, 140), "green": (61, 245, 160), "red": (255, 77, 109)}
LIB = os.environ.get("THUMB_LIB") or os.path.join(ROOT, "scripts", "blog", "media", "lib")


def font(s, w="Heavy"): return ImageFont.truetype(os.path.join(HERE, "fonts", f"SUIT-{w}.ttf"), s)


def fit(t, s, maxw, w="Heavy"):
    while s > 30 and font(s, w).getlength(t) > maxw: s -= 2
    return font(s, w)


def photo(spec):
    im = Image.new("RGBA", (W, H), BG + (255,))
    x0 = int(W * spec.get("photo_x", .38)); pw = W - x0
    ph = Image.open(os.path.join(LIB, spec["photo"])).convert("RGB")
    sc = max(pw / ph.width, H / ph.height) * spec.get("zoom", 1.0)
    ph = ph.resize((int(ph.width * sc) + 1, int(ph.height * sc) + 1), Image.LANCZOS)
    fx, fy = spec.get("focus", (.5, .5)); cx = int((ph.width - pw) * fx); cy = int((ph.height - H) * fy)
    ph = ph.crop((cx, cy, cx + pw, cy + H))
    ph = ImageEnhance.Brightness(ph).enhance(spec.get("bright", .9)).convert("RGBA")
    a = np.clip(np.linspace(0, 1, pw) / spec.get("fade", .55), 0, 1) ** 1.6   # 왼쪽 가장자리를 바탕에 녹인다
    ph.putalpha(Image.fromarray((np.tile(a, (H, 1)) * 255).astype(np.uint8)))
    im.alpha_composite(ph, (x0, 0))
    # 왼쪽 글자 자리 살짝 더 어둡게 + 위쪽 로고 자리 어둡게
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    sh = np.clip(1 - xx / (W * .62), 0, 1) ** 1.3 * 150 + np.clip(1 - yy / 120, 0, 1) ** 1.6 * 110
    dk = Image.new("RGBA", (W, H), BG + (0,)); dk.putalpha(Image.fromarray(np.clip(sh, 0, 235).astype(np.uint8)))
    im.alpha_composite(dk)
    return im


def shadow_text(im, xy, s, f, fill):
    for off, blur, al in ((0, 20, 200), (4, 6, 160)):
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((xy[0] + off, xy[1] + off + 2), s, font=f, fill=(0, 0, 0, al), anchor="ls")
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(im).text(xy, s, font=f, fill=fill, anchor="ls")


def render(spec, out):
    im = photo(spec); LX = 48; maxw = spec.get("maxw", 760)
    lines = [(t, fit(t, s, maxw), COL.get(c, c)) for t, s, c in spec["lines"]]
    accent = COL[spec.get("accent", "gold")]
    top = 40
    if spec.get("tag"):   # 위 띠: 강조색 바탕 + 네이비 글씨
        ft = font(spec.get("st", 50)); tw = ft.getlength(spec["tag"]); ph = ft.size * 1.5; pw = tw + ft.size * 1.0
        s_ = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(s_).rounded_rectangle([LX + 3, top + 5, LX + pw + 3, top + ph + 5], 8, fill=(0, 0, 0, 150))
        im.alpha_composite(s_.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(im).rounded_rectangle([LX, top, LX + pw, top + ph], 8, fill=accent)
        ImageDraw.Draw(im).text((LX + pw / 2, top + ph / 2 + 2), spec["tag"], font=ft, fill=NAVY, anchor="mm")
        top += ph
    # 남은 세로 공간 가운데에 줄을 쌓는다 (줄 간격은 글자 크기의 1.06배)
    asc = [f.getmetrics()[0] for _, f, _ in lines]
    hs = [f.size * 1.06 for _, f, _ in lines]; total = sum(hs)
    y = top + (H - 30 - top - total) / 2 + spec.get("dy", 0)
    for (t, f, c), h, a in zip(lines, hs, asc):
        y += h; shadow_text(im, (LX - 2, y - f.size * .12), t, f, c)
    paste_logo(im, W - 30, 22, 40, "dark", align="right")
    for (t, f, _), (_, s, _) in zip(lines, spec["lines"]):
        if f.size < s * .85: print(f"  ⚠ 글자가 길어 작아짐 {f.size}/{s}: {t}")
    im.convert("RGB").save(out, quality=94); return out


if __name__ == "__main__":
    print(render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2]))
