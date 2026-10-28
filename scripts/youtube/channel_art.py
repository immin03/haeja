"""밸류노트 유튜브 채널 아트 (2026-10-29)
  python3 scripts/youtube/channel_art.py [출력폴더]
  만드는 파일: yt_banner_2560x1440.jpg / yt_profile_800.png / yt_watermark_150.png
  로고는 scripts/brand.py (2026-10-23 확정 로고)만 쓴다.
  배너 핵심 내용은 모든 기기에서 보이는 안전 영역(가운데 1546x423) 안에만 둔다.
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from brand import paste_logo, v_icon, EN_FONT, FONTS  # noqa: E402

KO_B = os.path.join(FONTS, "SUIT-ExtraBold.ttf")
KO_SB = os.path.join(FONTS, "SUIT-SemiBold.ttf")
KO_M = os.path.join(FONTS, "SUIT-Medium.ttf")
IVORY = (247, 242, 232)
BEIGE = (234, 219, 185)
LINE = (216, 194, 148)
W, H = 2560, 1440
SAFE = (507, 508, 2053, 931)          # 1546 x 423


def bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # 가운데(로고 쪽)가 살짝 밝은 네이비 그라데이션
    r = np.sqrt(((xx - W * .42) / (W * .62)) ** 2 + ((yy - H * .5) / (H * .62)) ** 2)
    k = np.clip(1 - r, 0, 1)[..., None] ** 1.4
    a = np.array([8, 14, 27], np.float32); b = np.array([27, 46, 78], np.float32)
    im = (a * (1 - k) + b * k)
    return Image.fromarray(im.astype(np.uint8)).convert("RGBA")


def notebook(im):
    """노트 포맷 모티프: 아주 옅은 가로줄 + 왼쪽 여백선"""
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for y in range(SAFE[1] - 46 * 9, H, 46):
        d.line([(0, y), (W, y)], fill=(234, 219, 185, 10), width=2)
    d.line([(SAFE[0] - 40, 0), (SAFE[0] - 40, H)], fill=(255, 77, 109, 14), width=3)
    im.alpha_composite(ov)


def pen_chart(im):
    """오른쪽 바깥(PC 넓은 화면에서만 보이는 곳)에 금색 펜으로 그린 우상향 선 — 은은하게"""
    ov = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    pts = [(2080, 860), (2150, 820), (2205, 845), (2270, 760), (2330, 790), (2400, 690), (2460, 715), (2540, 600)]
    pts = [(x * 2, y * 2) for x, y in pts]
    d.line(pts, fill=(216, 194, 148, 70), width=8, joint="curve")
    for x, y in pts[1:-1]:
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(216, 194, 148, 70))
    ov = ov.resize((W, H), Image.LANCZOS)
    im.alpha_composite(ov)


def hand_underline(im, x0, x1, y, color=LINE, width=7):
    """금색 펜이 손으로 그은 듯한 밑줄 (살짝 휘고 끝이 가늘어짐)"""
    S = 4
    ov = Image.new("RGBA", (W * S // 4, H * S // 4), (0, 0, 0, 0))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    big = Image.new("RGBA", ((x1 - x0 + 80) * S, 60 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    n = 120
    for i in range(n):
        t = i / (n - 1)
        x = (40 + t * (x1 - x0)) * S
        yy = (30 + math.sin(t * math.pi) * -5 + t * 4) * S
        w = width * S * (0.55 + 0.45 * math.sin(min(1, t * 1.15) * math.pi) ** .5)
        d.ellipse([x - w / 2, yy - w / 2, x + w / 2, yy + w / 2], fill=color + (255,))
    big = big.resize((big.width // S, big.height // S), Image.LANCZOS)
    im.alpha_composite(big, (x0 - 40, y - 30))


def text(d, xy, s, font, fill, anchor="la", spacing=0):
    if not spacing:
        d.text(xy, s, font=font, fill=fill, anchor=anchor); return d.textlength(s, font=font)
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=font, fill=fill, anchor=anchor); x += d.textlength(ch, font=font) + spacing
    return x - xy[0] - spacing


def banner(out):
    im = bg(); notebook(im); pen_chart(im)
    d = ImageDraw.Draw(im)
    sx0, sy0, sx1, sy1 = SAFE
    cy = (sy0 + sy1) // 2

    LS = 92                                   # 로고 영문 글자 크기
    f1 = ImageFont.truetype(KO_B, 50)
    f_tag = ImageFont.truetype(KO_SB, 27)
    f_en = ImageFont.truetype(EN_FONT, 21)
    l1 = "워렌 버핏·찰리 멍거의 기준으로"
    l2a, l2b, l2c = "주식을 평가해 ", "현명한 투자", "를 돕습니다"
    tags = ["기업 이야기", "주가 전망", "거장의 투자"]
    tw = max(d.textlength(l1, font=f1), d.textlength(l2a + l2b + l2c, font=f1))
    lw, lh = paste_logo(Image.new("RGBA", im.size), 0, 0, size=LS, align="left", shadow=False)
    GAP = 54                                   # 로고 ↔ 구분선 ↔ 글
    total = lw + GAP * 2 + tw
    x0 = (sx0 + sx1) / 2 - total / 2           # 묶음 전체를 안전 영역 가운데로
    assert x0 >= sx0 + 60 and x0 + total <= sx1 - 60, (x0, total)

    # 왼쪽: 확정 로고
    paste_logo(im, x0 + lw / 2, cy - lh / 2 - 6, size=LS, theme="dark", align="center", shadow=False)

    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); o = ImageDraw.Draw(ov)
    dx = x0 + lw + GAP
    o.line([(dx, cy - 118), (dx, cy + 118)], fill=(216, 194, 148, 130), width=3)

    # 오른쪽: 슬로건 2줄 → 다루는 것(칩) → 영어 한 줄
    tx = dx + GAP
    block_h = 74 + 62 + 34 + 48 + 22 + 22     # 줄1·줄2·여백·칩·여백·영어
    y1 = cy - block_h / 2 - 8
    text(d, (tx, y1), l1, f1, IVORY)
    y2 = y1 + 74
    w_a = text(d, (tx, y2), l2a, f1, IVORY)
    w_b = text(d, (tx + w_a, y2), l2b, f1, BEIGE)
    text(d, (tx + w_a + w_b, y2), l2c, f1, IVORY)
    ty = y2 + 62 + 34
    x = tx
    for tg in tags:
        w_ = o.textlength(tg, font=f_tag); pw, ph = w_ + 40, 48
        o.rounded_rectangle([x, ty, x + pw, ty + ph], radius=24, fill=(234, 219, 185, 22), outline=(216, 194, 148, 170), width=2)
        o.text((x + pw / 2, ty + ph / 2 + 1), tg, font=f_tag, fill=BEIGE + (255,), anchor="mm")
        x += pw + 12
    o.text((tx, ty + ph + 22), "STOCKS, THE BUFFETT & MUNGER WAY", font=f_en, fill=(234, 219, 185, 140), anchor="lt")
    im.alpha_composite(ov)
    hand_underline(im, int(tx + w_a), int(tx + w_a + w_b), int(y2 + 70), width=6)

    im.convert("RGB").save(out, quality=93, optimize=True, progressive=True)
    return im


def profile(out, n=800):
    """확정 마크(네이비 + 흰 V + 금선)를 유튜브 원형용으로: 작은 원(36~176px)에서도 금선이 보이게 두께만 키움"""
    S = 2; N = n * S
    yy, xx = np.mgrid[0:N, 0:N]; r = np.sqrt(((xx - N * .5) / N) ** 2 + (yy / N * .9) ** 2)
    k = np.clip(1 - r * 1.25, 0, 1)[..., None]
    im = Image.fromarray((np.array([11, 20, 36], np.float32) * (1 - k) + np.array([27, 44, 72], np.float32) * k).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im); f = ImageFont.truetype(EN_FONT, int(N * .56))
    bb = d.textbbox((0, 0), "V", font=f); w = bb[2] - bb[0]; h = bb[3] - bb[1]
    lt = round(N * .03); gap = N * .07
    top = N / 2 - (h + gap + lt) / 2          # V + 금선 묶음을 원 정가운데에
    d.text((N / 2 - w / 2 - bb[0], top - bb[1]), "V", font=f, fill=(255, 255, 255, 255))
    lw = w * .92; ly = top + h + gap
    d.rounded_rectangle([N / 2 - lw / 2, ly, N / 2 + lw / 2, ly + lt], radius=lt / 2, fill=LINE + (255,))
    im = im.resize((n, n), Image.LANCZOS).convert("RGB"); im.save(out, optimize=True)
    return im


def watermark(out, n=150):
    im = Image.open(out.replace("yt_watermark_150.png", "yt_profile_800.png")).convert("RGBA").resize((n, n), Image.LANCZOS)
    m = Image.new("L", (n * 4, n * 4), 0); ImageDraw.Draw(m).ellipse([0, 0, n * 4 - 1, n * 4 - 1], fill=255)
    im.putalpha(m.resize((n, n), Image.LANCZOS)); im.save(out, optimize=True)


if __name__ == "__main__":
    od = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(od, exist_ok=True)
    banner(os.path.join(od, "yt_banner_2560x1440.jpg"))
    profile(os.path.join(od, "yt_profile_800.png"))
    watermark(os.path.join(od, "yt_watermark_150.png"))
    print("ok", od)
