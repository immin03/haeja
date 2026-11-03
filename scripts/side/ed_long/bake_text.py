"""그림 속 종이(편지·파피루스)에 영어 필기체를 원근에 맞춰 써 넣는다 (2026-11-03)
python3 bake_text.py in.jpeg out.jpeg '<quad json>' 'line1|line2|...' [글자크기] [잉크색 r,g,b]
quad = 종이 위 글씨 영역의 네 꼭짓점 [[좌상],[우상],[우하],[좌하]] (그림 픽셀 좌표)
"""
import json, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SCRIPT = "/root/fonts/PinyonScript-Regular.ttf"


def text_plane(lines, w=1600, h=900, size=None, ink=(40, 26, 14)):
    """평평한 종이 위의 글씨(알파) 한 장. 줄 간격과 크기를 영역에 맞춘다"""
    n = len(lines); size = size or int(h / (n * 1.55))
    f = ImageFont.truetype(SCRIPT, size)
    im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im)
    y = (h - n * size * 1.45) / 2 + size
    for s in lines:
        tw = d.textlength(s, font=f)
        if tw > w * 0.96:   # 넘치면 줄였다가 다시
            return text_plane(lines, w, h, int(size * w * 0.94 / tw), ink)
        d.text((w * 0.03, y), s, font=f, fill=255, anchor="ls"); y += size * 1.45
    return im


def bake(img, quad, lines, size=None, ink=(40, 26, 14), strength=0.88):
    w, h = 1600, 900
    a = np.array(text_plane(lines, w, h, size).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255.0
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]]); M = cv2.getPerspectiveTransform(src, np.float32(quad))
    H_, W_ = img.shape[:2]
    aw = cv2.warpPerspective(a, M, (W_, H_), flags=cv2.INTER_LINEAR)[..., None] * strength
    # 잉크가 종이 결을 살짝 따라가게: 종이 밝기에 비례해 진하게
    paper = img.astype(np.float32)
    ink_bgr = np.array(ink[::-1], np.float32)
    out = paper * (1 - aw) + (paper * 0.25 + ink_bgr * 0.75) * aw
    return np.clip(out, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    src, dst, quad, lines = sys.argv[1], sys.argv[2], json.loads(sys.argv[3]), sys.argv[4].split("|")
    size = int(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] != "-" else None
    ink = tuple(int(x) for x in sys.argv[6].split(",")) if len(sys.argv) > 6 else (40, 26, 14)
    cv2.imwrite(dst, bake(cv2.imread(src), quad, lines, size, ink), [cv2.IMWRITE_JPEG_QUALITY, 95])
