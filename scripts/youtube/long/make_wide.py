"""세로 인물 사진 → 가로 16:9 (2026-11-18 대표님: 세로 사진을 가로 화면에 꽉 채우면 눈 위가 잘린다)
흐리고 어둡게 깐 배경 위에 사진 전체(얼굴 포함)를 오른쪽에 세워 둔다. 왼쪽은 이름표·자막 자리.
사용: python3 make_wide.py <lib 파일명> [x 위치 0~1, 기본 .68]  → <이름>_wide.jpg 를 같은 폴더에 만든다
build.py 가 렌더 직전에 원고의 세로 사진을 찾아 자동으로 바꾼다."""
import os, sys
from PIL import Image, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "..", "blog", "media", "lib")
W, H = 1920, 1080


def is_portrait(name):
    try:
        with Image.open(os.path.join(LIB, name)) as im: w, h = im.size
        return h > w * .9
    except Exception:
        return False


def make(name, xpos=.68):
    base, _ = os.path.splitext(name)
    out = base + "_wide.jpg"
    p = os.path.join(LIB, out)
    if os.path.exists(p): return out
    im = Image.open(os.path.join(LIB, name)).convert("RGB")
    s = max(W / im.width, H / im.height)
    bg = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(40))).enhance(.45)
    fh = H; fw = int(im.width * fh / im.height)
    fg = im.resize((fw, fh), Image.LANCZOS)
    x = int(W * xpos - fw / 2); x = max(0, min(W - fw, x))
    # 사진 가장자리를 부드럽게 녹인다
    m = Image.new("L", (fw, fh), 255); e = max(8, fw // 12)
    for i in range(e):
        a = int(255 * i / e)
        for box in ((i, 0, i + 1, fh), (fw - 1 - i, 0, fw - i, fh)): m.paste(a, box)
    bg.paste(fg, (x, 0), m)
    bg.save(p, quality=92)
    return out


if __name__ == "__main__":
    print(make(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else .68))
