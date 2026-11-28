"""lf01 썸네일 2차 시안 (11/28 대표: "숫자도 쓰고 잘된 썸네일 제목 다 참고").
벤치마크(심리학탐정 상위 썸네일): 숫자를 가장 크게(「4가지」「7가지」「10가지」), 빨간 띠·노란 박스로 핵심어 강조,
인물 얼굴 하나를 오른쪽에 크게, 글자는 왼쪽에 화면 절반. 숫자는 영상 대본에 실제로 나오는 것만 쓴다(1,200명·6명·5명·4가지).
두 계열: G = 우리 톤(아이보리 + 샴페인 금) / Y = 벤치마크 톤(노랑 + 빨간 띠, 얇은 검은 테두리).
저장소 루트에서: OUT=/home/claude/render/ python3 scripts/side/ed_long/thumb_lf01b.py
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

G = 'social/side/gen/'; O = os.environ.get('OUT', '_long/'); os.makedirs(O, exist_ok=True)
W, H = 1280, 720
F = lambda s, w='Heavy': ImageFont.truetype(f'/root/fonts/SUIT-{w}.ttf', s)
IVO, GOLD = (252, 247, 236), (240, 200, 120)
YEL, RED, WHT = (255, 214, 10), (200, 24, 30), (255, 255, 255)


def fit(p, cx=.5, cy=.4, scale=1.0, push=0):
    """push>0: 그림을 오른쪽으로 밀어 얼굴을 오른쪽 1/3에 둔다(왼쪽 빈 곳은 가장자리 색을 흐려 채움)."""
    im = Image.open(G + p).convert('RGB'); k = max(W / im.width, H / im.height) * scale
    im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
    x = int((im.width - W) * cx) - push; y = int((im.height - H) * cy)
    if x >= 0: return im.crop((x, y, x + W, y + H))
    c = im.crop((0, y, W + x, y + H)); out = Image.new('RGB', (W, H))
    edge = c.crop((0, 0, 8, H)).resize((-x, H)).filter(ImageFilter.GaussianBlur(30)); out.paste(edge, (0, 0)); out.paste(c, (-x, 0)); return out


def look(im, bright=1.15):
    im = ImageEnhance.Brightness(im).enhance(bright); im = ImageEnhance.Contrast(im).enhance(1.12)
    return ImageEnhance.Color(im).enhance(1.15)


def left_dark(im, x0=380, x1=820, k=.78):
    """왼쪽(글자 자리)만 어둡게: 얼굴이 있는 오른쪽은 밝게 둔다."""
    xs = np.clip((np.arange(W) - x0) / (x1 - x0), 0, 1); a = (1 - k) + k * xs
    m = Image.fromarray((np.tile(a, (H, 1)) * 255).astype(np.uint8))
    return Image.composite(im, Image.new('RGB', (W, H), (0, 0, 0)), m)


def shadow(im, draws):
    m = Image.new('L', (W, H), 0); dm = ImageDraw.Draw(m)
    for (x, y, t, f) in draws: dm.text((x, y), t, font=f, fill=255)
    im.paste((0, 0, 0), (0, 0), m.filter(ImageFilter.GaussianBlur(22)).point(lambda v: min(255, int(v * 1.5))))


def mark(im):
    """오른쪽 위 작은 채널 표기 (로고 확정 전 임시)."""
    d = ImageDraw.Draw(im); f = ImageFont.truetype('/root/fonts/hahmlet-korean-700-normal.ttf', 26)
    t = '황제의 일기'; w = d.textlength(t, font=f); d.text((W - 36 - w, 28), t, font=f, fill=(236, 210, 150))


def compose(img, lines, out, tone='G', tag=None, frame=False, x=52, bot=46):
    """lines: [(글, 크기, 종류)]  종류 n=보통, h=강조색, box=색 박스 위 글자, bar=빨간 띠 위 흰 글자."""
    im = img.copy(); d = ImageDraw.Draw(im)
    hi = GOLD if tone == 'G' else YEL; base = IVO if tone == 'G' else WHT
    st = 0 if tone == 'G' else 5
    ys = []; y = H - bot
    for t, s, k in reversed(lines):
        y -= int(s * (1.22 if k in ('box', 'bar') else 1.08)); ys.insert(0, y)
    shadow(im, [(x, yy, t, F(s)) for (t, s, k), yy in zip(lines, ys) if k not in ('box', 'bar')])
    for (t, s, k), yy in zip(lines, ys):
        f = F(s); tw = d.textlength(t, font=f)
        if k == 'box':   # 강조색 박스 + 검은 글자 (벤치마크 「4가지」 방식)
            d.rectangle((x - 10, yy + int(s * .02), x + tw + 18, yy + int(s * 1.14)), fill=hi)
            d.text((x + 4, yy - int(s * .04)), t, font=f, fill=(18, 14, 10))
        elif k == 'bar':  # 빨간 띠 + 흰 글자
            d.rectangle((x - 10, yy + int(s * .02), x + tw + 18, yy + int(s * 1.14)), fill=RED)
            d.text((x + 4, yy - int(s * .04)), t, font=f, fill=WHT)
        else:
            d.text((x, yy), t, font=f, fill=hi if k == 'h' else base, stroke_width=st, stroke_fill=(0, 0, 0))
    if tag:
        tf = F(50, 'Bold'); tw = d.textlength(tag, font=tf); ty = ys[0] - 84
        d.rectangle((x - 6, ty, x + tw + 22, ty + 68), fill=(150, 20, 26)); d.text((x + 8, ty + 4), tag, font=tf, fill=(255, 244, 232))
    if frame:
        d.rectangle((0, 0, W - 1, H - 1), outline=hi, width=12)
    mark(im); im.save(O + out, quality=93); return out


outs = []
# 1. 연락처 1,200명 → 통화 6명 (대본 y04·y07 실제 숫자). 얼굴 오른쪽.
a = left_dark(look(fit('lf1_scroll_face.png', 0, .35, 1.25, 260), 1.2), 300, 760, .8)
outs.append(compose(a, [('연락처 1,200명', 74, 'bar'), ('한 달간 통화한 사람', 84, 'n'), ('단 6명', 190, 'h')], 'lf01_t1_G.jpg', 'G'))
outs.append(compose(a, [('연락처 1,200명', 74, 'bar'), ('한 달간 통화한 사람', 84, 'n'), ('단 6명', 190, 'h')], 'lf01_t1_Y.jpg', 'Y', frame=True))
# 2. 4가지 이유 (카드 I~IV) — 「나이 들수록 친구가 줄어드는 진짜 이유」 5.8만 + 「4가지」 숫자 박스.
b = left_dark(look(fit('lf1_ys_wonder.png', 0, .3, 1.3, 280), 1.18), 320, 780, .8)
outs.append(compose(b, [('나이 들수록', 96, 'n'), ('사람을 줄이는', 112, 'n'), ('4가지 이유', 132, 'box')], 'lf01_t2_G.jpg', 'G', tag='명상록'))
outs.append(compose(b, [('나이 들수록', 96, 'n'), ('사람을 줄이는', 112, 'n'), ('4가지 이유', 132, 'box')], 'lf01_t2_Y.jpg', 'Y', tag='명상록', frame=True))
# 3. 끝까지 남는 사람은 5명 (던바 r08·r09). 다섯 잔.
c = left_dark(look(fit('lf1_five_cups.png', .7, .5, 1.15), 1.2), 380, 820, .75)
outs.append(compose(c, [('끝까지 곁에 남는 사람', 80, 'n'), ('5명이면', 170, 'h'), ('충분합니다', 104, 'n')], 'lf01_t3_G.jpg', 'G'))
# 4. 질문형 + 숫자 — 「친구가 왜 사라질까?」 / 대본 y11.
e = left_dark(look(fit('lf1_ys_city.png', .15, .3, 1.25), 1.15), 320, 780, .8)
outs.append(compose(e, [('28년간 쌓은 1,200명', 76, 'n'), ('정년 후', 120, 'n'), ('몇 명 남을까?', 132, 'h')], 'lf01_t4_G.jpg', 'G'))
# 5. 황제 각도 — 「통찰력이 뛰어난 사람들이 지독하게 외로운 이유」(64만) 패턴. 황제 영상 프레임 대신 일기 장면.
f_ = left_dark(look(fit('lf1_ys_writes.png', .12, .3, 1.25), 1.15), 320, 780, .8)
outs.append(compose(f_, [('현명한 사람일수록', 92, 'n'), ('사람을 줄인다', 128, 'h'), ('황제의 4가지 이유', 76, 'bar')], 'lf01_t5_G.jpg', 'G'))

# 비교판: 크게 + 휴대폰 목록 크기(246x138)
s = Image.new('RGB', (2 * 640 + 30, 4 * 360 + 50 + 170), (22, 22, 22)); d = ImageDraw.Draw(s)
for i, n in enumerate(outs):
    t = Image.open(O + n); x = 10 + (i % 2) * 650; y = 10 + (i // 2) * 370
    s.paste(t.resize((640, 360), Image.LANCZOS), (x, y)); d.text((x + 8, y + 8), n[6:-4], font=F(28), fill=(255, 255, 0))
s.save(O + 'lf01_thumbs2_sheet.jpg', quality=90)
m = Image.new('RGB', (len(outs) * 256 + 10, 160), (15, 15, 15))
for i, n in enumerate(outs): m.paste(Image.open(O + n).resize((246, 138), Image.LANCZOS), (10 + i * 256, 11))
m.save(O + 'lf01_thumbs2_phone.jpg', quality=90)
print(outs)
