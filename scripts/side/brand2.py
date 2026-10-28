"""From Korea, With Love — 채널 브랜드 이미지 (2026-10-28 채널명 변경)
입력: social/side/gen/brand_banner2.jpeg, brand_profile2.jpeg, cut/h_love.png (Higgsfield 생성 + 배경 제거)
결과: docs/side/logo_main.png (영상 구석·쇼츠 마무리 카드), banner_2560x1440.jpg, profile_800.png, watermark_150.png
사용: python3 scripts/side/brand2.py
"""
import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GEN = os.path.join(ROOT, "social", "side", "gen"); OUT = os.path.join(ROOT, "docs", "side")
FONTS = os.path.join(os.path.dirname(__file__), "fonts")
NAVY, RED, CREAM, WHITE = (31, 42, 68, 255), (215, 50, 44, 255), (255, 248, 236, 255), (255, 255, 255, 255)


def font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if weight: f.set_variation_by_name(weight)
    return f


def heart(d, cx, cy, r, fill):
    pts = [(cx + r * math.sin(t) ** 3, cy - r * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16)
           for t in [i * 2 * math.pi / 160 for i in range(160)]]
    d.polygon(pts, fill=fill)


def sticker(img, width=14):
    """스티커처럼 흰 테두리 + 옅은 그림자"""
    a = img.split()[3]
    edge = a.filter(ImageFilter.MaxFilter(width * 2 + 1))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (20, 24, 40, 0)); sh.putalpha(edge.point(lambda v: int(v * 0.35)))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (0, 8))
    wh = Image.new("RGBA", img.size, WHITE); wh.putalpha(edge); out.alpha_composite(wh)
    out.alpha_composite(img); return out


def logo(with_bird=True):
    """왼쪽 까치 + 'From' 작게, 'Korea' 크게, 빨간 말풍선 'with love ♥' (with_bird=False 는 글자만 — 쇼츠 마무리 카드용)"""
    W, H, P = 1500, 640, 40
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    x0 = P
    if with_bird:
        k = Image.open(os.path.join(GEN, "cut", "h_love.png")).convert("RGBA")
        kh = 470; k = k.resize((int(k.width * kh / k.height), kh), Image.LANCZOS); c.alpha_composite(k, (P, H - kh - 70))
        x0 = P + k.width + 26
    f_from = font("Baloo2.ttf", 150, "ExtraBold"); f_kor = font("Baloo2.ttf", 300, "ExtraBold"); f_love = font("Baloo2.ttf", 112, "ExtraBold")
    d.text((x0 + 8, 40), "From", font=f_from, fill=NAVY)
    d.text((x0, 150), "Korea", font=f_kor, fill=NAVY)
    # 말풍선: 'From' 오른쪽 위
    t = "with love"; tw = f_love.getlength(t); bx = x0 + f_from.getlength("From") + 60; by = 22
    bw, bh = tw + 150, 150
    d.rounded_rectangle((bx, by, bx + bw, by + bh), 75, fill=RED)
    d.polygon([(bx + 60, by + bh - 6), (bx + 30, by + bh + 46), (bx + 120, by + bh - 6)], fill=RED)
    d.text((bx + 42, by + 4), t, font=f_love, fill=WHITE)
    heart(d, bx + bw - 62, by + bh / 2 - 2, 34, WHITE)
    c = c.crop(c.getbbox()); pad = 30
    big = Image.new("RGBA", (c.width + pad * 2, c.height + pad * 2), (0, 0, 0, 0)); big.alpha_composite(c, (pad, pad))
    return sticker(big, 16)


def main():
    lg = logo(); lg.save(os.path.join(OUT, "logo_main.png")); print("로고", lg.size)
    logo(False).save(os.path.join(OUT, "logo_text.png"))
    # 배너 2560x1440 — 모바일 안전 영역(가운데 1546x423) 안에 로고·한 줄 소개
    src = Image.open(os.path.join(GEN, "brand_banner2.jpeg")).convert("RGB").resize((2560, 1440), Image.LANCZOS)
    # 휴대폰·PC는 가운데 띠(높이 423)만 보인다 → 날아가는 까치 얼굴이 띠 안에 오게 그림을 아래로 내리고 위는 하늘을 늘려 채운다
    DY = 250; b = Image.new("RGB", (2560, 1440)); b.paste(src, (0, DY))
    b.paste(src.crop((0, 0, 2560, 40)).resize((2560, DY + 10)).filter(ImageFilter.GaussianBlur(6)), (0, 0))
    b = b.convert("RGBA")
    sx0, sy0, sx1, sy1 = (2560 - 1546) // 2, (1440 - 423) // 2, (2560 + 1546) // 2, (1440 + 423) // 2
    # 오른쪽은 날아가는 까치 자리 → 로고와 소개는 안전 영역 왼쪽(약 880px)에 위아래로
    lw = 640; l2 = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
    ft = font("Baloo2.ttf", 50, "ExtraBold"); lines = ["Tiny stories from Korea", "that warm your heart"]
    blockh = l2.height + 18 + 2 * 60
    lx, ly = sx0 + 40, sy0 + (423 - blockh) // 2
    b.alpha_composite(l2, (lx, ly))
    tag = Image.new("RGBA", b.size, (0, 0, 0, 0)); dt = ImageDraw.Draw(tag)
    ty = ly + l2.height + 14
    for i, ln in enumerate(lines):
        tx = lx + 30 + (0 if i == 0 else 0)
        dt.text((tx, ty + i * 60), ln, font=ft, fill=NAVY if i == 0 else RED, stroke_width=9, stroke_fill=WHITE)
    heart(dt, lx + 30 + ft.getlength(lines[1]) + 40, ty + 60 + 36, 22, WHITE)
    heart(dt, lx + 30 + ft.getlength(lines[1]) + 40, ty + 60 + 36, 15, RED)
    b.alpha_composite(tag); b.convert("RGB").save(os.path.join(OUT, "banner_2560x1440.jpg"), quality=92)
    # 프로필 800 — 얼굴이 원 안 가운데
    p = Image.open(os.path.join(GEN, "brand_profile2.jpeg")).convert("RGB").resize((800, 800), Image.LANCZOS)
    p.save(os.path.join(OUT, "profile_800.png"))
    # 워터마크 150 — 동그란 프로필
    m = Image.new("L", (600, 600), 0); ImageDraw.Draw(m).ellipse((0, 0, 599, 599), fill=255)
    w = p.resize((600, 600), Image.LANCZOS).convert("RGBA"); w.putalpha(m)
    ring = Image.new("RGBA", (640, 640), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse((0, 0, 639, 639), fill=WHITE); ring.alpha_composite(w, (20, 20))
    ring.resize((150, 150), Image.LANCZOS).save(os.path.join(OUT, "watermark_150.png"))
    # 영상 구석 로고(롱폼 렌더러가 쓰는 파일)도 같이
    lg.save(os.path.join(GEN, "brand_logo_main.png"))


if __name__ == "__main__":
    main()
