"""lf01 썸네일 3차 (11/28 15:28 대표: "너무 촌스러워, 애매한 주화 빼고" / 15:32 "로고 32로 썸네일").
2차의 색 박스·빨간 띠·노란 테두리·주화를 모두 뺐다. 다큐 포스터처럼 사진 + 큰 글자 + 금빛 숫자 하나 + 가는 금선.
숫자(1,200·6·5·4)는 대본에 있는 것만. 오른쪽 위는 영상과 같은 한 줄 로고(8번, 32px 비율).
저장소 루트에서: OUT=/home/claude/render/ python3 scripts/side/ed_long/thumb_lf01c.py
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
G = 'social/side/gen/'; O = os.environ.get('OUT', '_long/'); W, H = 1280, 720
SU = lambda s, w='Heavy': ImageFont.truetype(f'/root/fonts/SUIT-{w}.ttf', s)
HM = lambda s: ImageFont.truetype('/root/fonts/hahmlet-korean-700-normal.ttf', s)
IVO, GOLD, GOLD2, DIM = (246, 240, 228), (232, 196, 128), (176, 136, 70), (214, 204, 186)
LOGO = Image.open('docs/emperor/long/corner_logo.png'); LOGO = LOGO.resize((LOGO.width * 2 // 3, LOGO.height * 2 // 3), Image.LANCZOS)


def fit(p, cx=.5, cy=.4, scale=1.0, push=0):
    im = Image.open(G + p).convert('RGB'); k = max(W / im.width, H / im.height) * scale
    im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
    x = int((im.width - W) * cx) - push; y = int((im.height - H) * cy)
    if x >= 0: return im.crop((x, y, x + W, y + H))
    c = im.crop((0, y, W + x, y + H)); out = Image.new('RGB', (W, H)); out.paste(c.crop((0, 0, 8, H)).resize((-x, H)).filter(ImageFilter.GaussianBlur(30)), (0, 0)); out.paste(c, (-x, 0)); return out


def grade(im, bright=1.12, x0=300, x1=800, k=.82):
    im = ImageEnhance.Brightness(im).enhance(bright); im = ImageEnhance.Contrast(im).enhance(1.1); im = ImageEnhance.Color(im).enhance(1.05)
    xs = np.clip((np.arange(W) - x0) / (x1 - x0), 0, 1); a = (1 - k) + k * xs
    yy = np.linspace(0, 1, H)[:, None]; a = a[None, :] * (1 - .35 * np.clip((yy - .7) / .3, 0, 1))   # 아래 살짝 어둡게
    return Image.fromarray(np.clip(np.array(im).astype(np.float32) * a[..., None], 0, 255).astype(np.uint8))


def compose(img, lines, out, x=64, bot=64, kicker='명상록 · 에세이'):
    """lines: [(글, 폰트, 색)] 아래 정렬. 첫 줄 위에 작은 머리글 + 가는 금선."""
    im = img.copy(); d = ImageDraw.Draw(im); ys = []; y = H - bot
    for t, f, c in reversed(lines):
        b = d.textbbox((0, 0), t, font=f); y -= (b[3] - b[1]) + int(f.size * .22); ys.insert(0, y - b[1])
    m = Image.new('L', (W, H), 0); dm = ImageDraw.Draw(m)
    for (t, f, c), yy in zip(lines, ys): dm.text((x, yy), t, font=f, fill=255)
    im.paste((0, 0, 0), (0, 0), m.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * .9)))
    for (t, f, c), yy in zip(lines, ys): d.text((x, yy), t, font=f, fill=c)
    top = ys[0] + d.textbbox((0, 0), lines[0][0], font=lines[0][1])[1]
    kf = SU(30, 'Bold'); d.text((x + 2, top - 62), kicker, font=kf, fill=GOLD); d.line((x + 2, top - 18, x + 92, top - 18), fill=GOLD2, width=3)
    im.paste(LOGO, (W - 40 - LOGO.width, 34), LOGO); im.save(O + out, quality=94); return out


outs = []
a = grade(fit('lf1_scroll_face.png', 0, .35, 1.25, 260))
outs.append(compose(a, [('연락처 1,200명', SU(70, 'Bold'), DIM), ('한 달간 통화한 사람', SU(92), IVO), ('6명', SU(250), GOLD)], 'lf01_c1.jpg'))
b = grade(fit('lf1_ys_wonder.png', 0, .3, 1.3, 280))
outs.append(compose(b, [('나이 들수록', SU(100), IVO), ('사람을 줄이는', SU(118), IVO), ('4가지 이유', SU(150), GOLD)], 'lf01_c2.jpg'))
outs.append(compose(b, [('나이 들수록', HM(100), IVO), ('사람을 줄이는', HM(116), IVO), ('4가지 이유', HM(150), GOLD)], 'lf01_c2s.jpg'))
c = grade(fit('lf1_five_cups.png', .7, .5, 1.15), 1.15, 380, 840, .78)
outs.append(compose(c, [('끝까지 곁에 남는 사람', SU(84), IVO), ('5명이면', SU(190), GOLD), ('충분합니다', SU(110), IVO)], 'lf01_c3.jpg'))
e = grade(fit('lf1_ys_city.png', .15, .3, 1.25), 1.1)
outs.append(compose(e, [('28년간 쌓은 1,200명', SU(72, 'Bold'), DIM), ('정년 후', SU(124), IVO), ('몇 명 남을까', SU(140), GOLD)], 'lf01_c4.jpg'))
f_ = grade(fit('lf1_ys_writes.png', .12, .3, 1.25), 1.12)
outs.append(compose(f_, [('현명한 사람일수록', HM(92), IVO), ('사람을 줄인다', HM(130), GOLD)], 'lf01_c5.jpg', kicker='명상록 · 4가지 이유'))

s = Image.new('RGB', (2 * 640 + 30, 3 * 370 + 10), (22, 22, 22)); d = ImageDraw.Draw(s)
for i, n in enumerate(outs):
    x = 10 + (i % 2) * 650; y = 10 + (i // 2) * 370; s.paste(Image.open(O + n).resize((640, 360), Image.LANCZOS), (x, y)); d.text((x + 8, y + 8), n[5:-4], font=SU(26), fill=(255, 255, 0))
s.save(O + 'lf01_thumbs3_sheet.jpg', quality=90)
m = Image.new('RGB', (len(outs) * 256 + 10, 160), (15, 15, 15))
for i, n in enumerate(outs): m.paste(Image.open(O + n).resize((246, 138), Image.LANCZOS), (10 + i * 256, 11))
m.save(O + 'lf01_thumbs3_phone.jpg', quality=90); print(outs)

# 11/28 15:36 대표: 흰 줄 두 개 글자 크기 통일, 앞말은 최대한 짧게(「~할수록」)
V = [('나이 들수록', 'lf1_ys_wonder.png', (0, .3, 1.3, 280)), ('현명할수록', 'lf1_ys_writes.png', (.12, .3, 1.25, 0)),
     ('품격 있을수록', 'lf1_ys_side.png', (0, .3, 1.2, 240)), ('지혜로울수록', 'lf1_ys_city.png', (.15, .3, 1.25, 0)),
     ('단단할수록', 'lf1_ys_pen.png', (0, .3, 1.2, 260)), ('행복할수록', 'lf1_ys_morning.png', (0, .3, 1.2, 260))]
WF = SU(120)
outs2 = []
for i, (pre, img, fa) in enumerate(V, 1):
    b = grade(fit(img, *fa), 1.14)
    outs2.append(compose(b, [(pre, WF, IVO), ('사람을 줄이는', WF, IVO), ('4가지 이유', SU(160), GOLD)], f'lf01_d{i}.jpg'))
s = Image.new('RGB', (2 * 640 + 30, 3 * 370 + 10), (22, 22, 22)); d = ImageDraw.Draw(s)
for i, n in enumerate(outs2):
    x = 10 + (i % 2) * 650; y = 10 + (i // 2) * 370; s.paste(Image.open(O + n).resize((640, 360), Image.LANCZOS), (x, y)); d.text((x + 8, y + 8), n[5:-4], font=SU(26), fill=(255, 255, 0))
s.save(O + 'lf01_thumbs4_sheet.jpg', quality=90)
m = Image.new('RGB', (len(outs2) * 256 + 10, 160), (15, 15, 15))
for i, n in enumerate(outs2): m.paste(Image.open(O + n).resize((246, 138), Image.LANCZOS), (10 + i * 256, 11))
m.save(O + 'lf01_thumbs4_phone.jpg', quality=90); print(outs2)
