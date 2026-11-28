"""(thumb_kr2.py 함수 복사) 황제의 일기 한국 롱폼 썸네일 v2 시안 (2026-11-12 대표: "기존 디자인틀 어느정도 유지하면서 바꾸는거 시도해보자").
벤치마킹(BENCH_LONG_1112.md): 잘 되는 한국 롱폼 썸네일 = 글자가 화면 절반 이상, 강한 색(노랑·흰색)과 검은 테두리, 얼굴 크게, 밝은 화면.
유지: 장면 사진, 빨간 「명상록」 태그, 오른쪽 위 채널 표식, 주화, SUIT 고딕, 왼쪽 아래 글 배치.
바꾼 것: 글자 140 → 180~200px(Heavy) + 검은 테두리, 강조 줄 금색 → 밝은 노랑, 화면 어둡게 깎는 정도를 절반으로, 얼굴 더 크게.
저장소 루트에서: OUT=_long/ python3 scripts/side/ed_long/thumb_kr2.py
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import numpy as np

G = 'social/side/gen/'; O = os.environ.get('OUT', '_long/'); os.makedirs(O, exist_ok=True)
W, H = 1280, 720
S_ = lambda w, s: ImageFont.truetype(f'/root/fonts/SUIT-{w}.ttf', s)
YEL, WHT = (255, 214, 10), (255, 255, 255)
IVO, IVO2 = (252, 247, 236), (238, 196, 126)   # 11/12 대표: 노랑·검은 테두리 싫음 → 윗줄 밝은 아이보리, 강조 줄 샴페인 금빛(18:14 확정), 테두리 없음


def fit(p, box, cx=.5, cy=.4, scale=1.0):
    im = Image.open(G + p).convert('RGB'); bw, bh = box; k = max(bw / im.width, bh / im.height) * scale
    im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
    x = int((im.width - bw) * cx); y = int((im.height - bh) * cy); return im.crop((x, y, x + bw, y + bh))


def grad(w, h, x0, x1, a0, a1):
    g = np.zeros((h, w), np.float32); xs = np.clip((np.arange(w) - x0) / max(x1 - x0, 1), 0, 1); g[:] = a0 + (a1 - a0) * xs
    return Image.fromarray((g * 255).astype(np.uint8))


def coin(base, cx, cy, d, op):
    c = Image.open('docs/emperor/profile_final.png').convert('RGBA').resize((d, d), Image.LANCZOS)
    m = Image.new('L', (d, d), 0); ImageDraw.Draw(m).ellipse((0, 0, d, d), fill=255); m = m.filter(ImageFilter.GaussianBlur(d // 14))
    lay = Image.new('RGB', base.size, (0, 0, 0)); lay.paste(c.convert('RGB'), (cx - d // 2, cy - d // 2), m)
    return Image.blend(base, ImageChops.screen(base, lay), op)


def fin(im, bright=1.08):
    im = ImageEnhance.Brightness(im).enhance(bright)
    im = ImageEnhance.Contrast(im).enhance(1.15); im = ImageEnhance.Color(im).enhance(1.18)
    v = np.array(im).astype(np.float32); yy, xx = np.mgrid[0:H, 0:W]; r = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    v *= np.clip(1.06 - 0.16 * r, 0, 1.1)[..., None]; return Image.fromarray(np.clip(v, 0, 255).astype(np.uint8))


def bottom_dark(im, start=380, k=.55):
    a = np.clip(1.0 - np.clip((np.mgrid[0:H, 0:W][0] - start) / (H - start), 0, 1) * k, 0, 1)
    return Image.composite(im, Image.new('RGB', (W, H), (0, 0, 0)), Image.fromarray((a * 255).astype(np.uint8)))


def brand(im):
    d = ImageDraw.Draw(im); ef = ImageFont.truetype('/root/fonts/CormorantSC-SemiBold.ttf', 30); kf = S_('SemiBold', 22)
    en = "THE EMPEROR'S DIARY"; ko = '황제의 일기'; ew = d.textlength(en, font=ef) + 3 * len(en); kw = d.textlength(ko, font=kf) + 6 * len(ko); r = W - 40; cd = 58
    x0 = r - max(ew, kw); cx = int(x0 - 14 - cd)
    sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).rectangle((cx - 10, 24, r + 10, 24 + cd + 12), fill=150); im.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(22)))
    c = Image.open('docs/emperor/profile_final.png').convert('RGBA').resize((cd, cd), Image.LANCZOS); mk = Image.new('L', (cd, cd), 0); ImageDraw.Draw(mk).ellipse((0, 0, cd - 1, cd - 1), fill=255)
    im.paste(c.convert('RGB'), (cx, 30), mk)
    x = r - ew
    for ch in en: d.text((x, 30), ch, font=ef, fill=(236, 206, 140)); x += d.textlength(ch, font=ef) + 3
    x = r - kw
    for ch in ko: d.text((x, 68), ch, font=kf, fill=(240, 234, 224)); x += d.textlength(ch, font=kf) + 6


def text(im, lines, colors, size, x=48, tag='명상록', lh=1.1, stroke=0, bot=40):
    """큰 글자 + 검은 테두리. 줄마다 크기를 따로 줄 수 있다(size 가 list)."""
    sizes = size if isinstance(size, list) else [size] * len(lines)
    d = ImageDraw.Draw(im)
    ys = []; y = H - bot
    for s in reversed(sizes): y -= int(s * lh); ys.insert(0, y)
    # 그림자
    m = Image.new('L', (W, H), 0); dm = ImageDraw.Draw(m)
    for l, s, yy in zip(lines, sizes, ys): dm.text((x, yy), l, font=S_('Heavy', s), fill=255)
    # 테두리 대신 넓고 부드러운 그림자 두 겹 (글자 둘레가 선으로 보이지 않게)
    im.paste((0, 0, 0), (0, 0), m.filter(ImageFilter.GaussianBlur(28)).point(lambda v: min(255, int(v * 1.6))))
    im.paste((0, 0, 0), (0, 4), m.filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * .55)))
    for l, s, yy, c in zip(lines, sizes, ys, colors):
        d.text((x, yy), l, font=S_('Heavy', s), fill=c, stroke_width=stroke, stroke_fill=(0, 0, 0))
    if tag:
        tf = S_('Bold', 54); tw = d.textlength(tag, font=tf) + 4 * len(tag); ty = ys[0] - 92
        d.rectangle((x + 4, ty, x + 4 + tw + 40, ty + 74), fill=(160, 22, 28))
        xx = x + 24
        for ch in tag: d.text((xx, ty + 6), ch, font=tf, fill=(255, 246, 236)); xx += d.textlength(ch, font=tf) + 4
    brand(im)
    return im



# 11/28 lf01 에세이 롱폼 1편 썸네일 3장 — 『명상록』 2장 + 스토아 철학 1장 (11/12 확정 규칙: 아이보리 글자 + 샴페인 금빛 강조 줄, 테두리 없음, 주화는 글자 뒤 은은하게)
G = 'social/side/gen/'
a = fin(fit('lf1_hall_three.png', (W, H), .5, .55, 1.05), 1.15); a = coin(a, 330, 250, 460, .16); a = bottom_dark(a, 300, .6)
text(a, ['나이 들수록', '사람을 줄이는', '진짜 이유'], [IVO, IVO, IVO2], [118, 118, 150], tag='명상록').save(O + 'lf01_thumb_A.jpg', quality=93)
b = fin(fit('lf1_ys_table.png', (W, H), .62, .25, 1.25), 1.12); b = coin(b, 300, 230, 440, .15); b = bottom_dark(b, 300, .62)
text(b, ['끝까지 곁에 남길', '다섯 사람'], [IVO, IVO2], [112, 170], tag='명상록').save(O + 'lf01_thumb_B.jpg', quality=93)
c = fin(fit('lf1_ridge.png', (W, H), .5, .5, 1.05), 1.1); c = coin(c, 980, 250, 440, .14); c = bottom_dark(c, 300, .6)
text(c, ['사람을 줄이면', '인생이 편해진다'], [IVO, IVO2], [124, 150], tag='스토아 철학').save(O + 'lf01_thumb_C.jpg', quality=93)
from PIL import Image as _I
s = _I.new('RGB', (W * 3 // 2 + 40, H // 2 + 20 + 210), (24, 24, 24)); d = ImageDraw.Draw(s)
for i, n in enumerate('ABC'):
    t = _I.open(O + f'lf01_thumb_{n}.jpg'); s.paste(t.resize((W // 2, H // 2)), (10 + i * (W // 2 + 10), 10)); s.paste(t.resize((320, 180)), (10 + i * (W // 2 + 10), H // 2 + 30))
s.save(O + 'lf01_thumb_sheet.jpg', quality=92)
