"""롱폼 우측 상단 로고 2차 시안 8종 (11/28 대표: 1차 A·B·C 반려 → "다시 여러 시안").
1차는 회색 주화 + 작은 글자라 존재감이 약했다. 2차는 금색·붉은 낙관·월계관 등 방향을 넓혔다.
각 시안은 투명 PNG(logo_X.png)로 만들어 longform.py 가 그대로 얹을 수 있게 한다. 영상 위 검은 띠(약 90px) 안에 들어가는 크기.
저장소 루트에서: OUT=/home/claude/render/ python3 scripts/side/ed_long/logo_lf01.py
"""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

O = os.environ.get('OUT', '_long/'); os.makedirs(O, exist_ok=True)
FD = '/root/fonts/'
fnt = lambda n, s: ImageFont.truetype(FD + n, s)
GOLD, GOLD2, IVO, RED = (226, 190, 120), (176, 136, 70), (240, 232, 216), (168, 28, 30)
COIN = 'docs/emperor/profile_final.png'


def coin(d, gold=True):
    c = Image.open(COIN).convert('RGBA').resize((d, d), Image.LANCZOS)
    if gold:
        g = ImageOps.colorize(ImageOps.autocontrast(c.convert('L')), (38, 24, 6), (252, 224, 160), mid=(170, 128, 60)).convert('RGBA')
        c = g
    m = Image.new('L', (d, d), 0); ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=255); c.putalpha(m); return c


def spaced(d, xy, t, f, fill, sp):
    x, y = xy
    for ch in t: d.text((x, y), ch, font=f, fill=fill); x += d.textlength(ch, font=f) + sp
    return x


def tw(t, f, sp):
    d = ImageDraw.Draw(Image.new('L', (1, 1))); return sum(d.textlength(c, font=f) for c in t) + sp * (len(t) - 1)


def canvas(w, h): return Image.new('RGBA', (w, h), (0, 0, 0, 0))


def L_D():  # 붉은 낙관(도장) 2x2 「황제/일기」
    s = 76; im = canvas(s, s); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, s - 1, s - 1), 6, fill=RED + (235,)); d.rounded_rectangle((4, 4, s - 5, s - 5), 4, outline=(250, 236, 220, 255), width=2)
    f = fnt('hahmlet-korean-700-normal.ttf', 27)
    for (ch, x, y) in [('황', 10, 8), ('제', 40, 8), ('일', 10, 38), ('기', 40, 38)]: d.text((x, y), ch, font=f, fill=(252, 240, 226))
    return im


def L_E():  # 금색 세리프 워드마크 + 양옆 가는 선
    f = fnt('Cinzel-SemiBold.ttf', 26); t = "THE EMPEROR'S DIARY"; w = int(tw(t, f, 3)); im = canvas(w + 120, 44); d = ImageDraw.Draw(im)
    d.line((0, 22, 44, 22), fill=GOLD2 + (255,), width=1); d.line((w + 76, 22, w + 120, 22), fill=GOLD2 + (255,), width=1)
    d.polygon([(50, 22), (54, 18), (58, 22), (54, 26)], fill=GOLD); d.polygon([(w + 62, 22), (w + 66, 18), (w + 70, 22), (w + 66, 26)], fill=GOLD)
    spaced(d, (60 + 2, 6), t, f, GOLD, 3); return im


def L_F():  # 금빛 주화 크게 + 이중 링
    d0 = 78; im = canvas(d0, d0); dr = ImageDraw.Draw(im)
    dr.ellipse((0, 0, d0 - 1, d0 - 1), outline=GOLD + (255,), width=2); dr.ellipse((5, 5, d0 - 6, d0 - 6), outline=GOLD2 + (200,), width=1)
    im.alpha_composite(coin(d0 - 16), (8, 8)); return im


def L_G():  # 한글 세리프 「황제의 일기」 금색 + 작은 영문
    f = fnt('hahmlet-korean-700-normal.ttf', 34); f2 = fnt('CormorantSC-SemiBold.ttf', 16)
    t = '황제의 일기'; w = int(tw(t, f, 4)); e = 'MEDITATIONS · MARCUS AURELIUS'; w2 = int(tw(e, f2, 2))
    W_ = max(w, w2) + 4; im = canvas(W_, 70); d = ImageDraw.Draw(im)
    spaced(d, (W_ - w, 0), t, f, GOLD, 4); d.line((W_ - w2, 50, W_, 50), fill=GOLD2 + (180,), width=1); spaced(d, (W_ - w2, 53), e, f2, (200, 180, 140), 2); return im


def L_H():  # 월계관 + ED 모노그램
    s = 84; k = 3; S = s * k; im = canvas(S, S); d = ImageDraw.Draw(im); cx = cy = S / 2; R = S * .40
    for side in (-1, 1):
        for i in range(9):
            a = math.radians(110 + i * 17) if side < 0 else math.radians(70 - i * 17)
            x = cx + R * math.cos(a); y = cy + R * math.sin(a) * -1 * -1
            leaf = canvas(46, 20); ImageDraw.Draw(leaf).ellipse((0, 0, 45, 19), fill=GOLD + (255,))
            ang = math.degrees(a) + (-60 if side < 0 else 60) + 90
            lf = leaf.rotate(-ang, expand=True, resample=Image.BICUBIC); im.alpha_composite(lf, (int(x - lf.width / 2), int(y - lf.height / 2)))
    f = fnt('Cinzel-SemiBold.ttf', 30 * k); t = 'ED'; w = d.textlength(t, font=f); d.text((cx - w / 2, cy - 22 * k), t, font=f, fill=IVO)
    return im.resize((s, s), Image.LANCZOS)


def L_I():  # 세로 금선 + 2단 「황제의 / 일기」 + 영문
    f = fnt('hahmlet-korean-700-normal.ttf', 30); f2 = fnt('Cinzel-SemiBold.ttf', 15)
    im = canvas(190, 76); d = ImageDraw.Draw(im)
    d.line((84, 6, 84, 70), fill=GOLD + (255,), width=2)
    spaced(d, (96, 2), '황제의', f, IVO, 2); spaced(d, (96, 38), '일기', f, GOLD, 2)
    spaced(d, (0, 14), 'THE', f2, (200, 180, 140), 2); spaced(d, (0, 32), "EMPEROR'S", fnt('Cinzel-SemiBold.ttf', 11), (200, 180, 140), 1); spaced(d, (0, 48), 'DIARY', f2, (200, 180, 140), 2)
    return im


def L_J():  # 반투명 흰 워터마크 (주화 + 글자, 55%)
    f = fnt('SUIT-Bold.ttf', 26); t = '황제의 일기'; w = int(tw(t, f, 3)); im = canvas(w + 64, 54); d = ImageDraw.Draw(im)
    c = coin(48, gold=False).convert('LA').convert('RGBA'); im.alpha_composite(c, (0, 3)); spaced(d, (60, 10), t, f, (255, 255, 255, 255), 3)
    a = im.getchannel('A').point(lambda v: int(v * .55)); im.putalpha(a); return im


def L_K():  # 금 테두리 알약 배지 + 금빛 주화
    f = fnt('hahmlet-korean-700-normal.ttf', 26); t = '황제의 일기'; w = int(tw(t, f, 3)); W_, H_ = w + 92, 56
    im = canvas(W_, H_); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ - 1, H_ - 1), H_ // 2, fill=(14, 10, 6, 215), outline=GOLD + (255,), width=2)
    im.alpha_composite(coin(44), (7, 6)); spaced(d, (62, 10), t, f, GOLD, 3); return im


LOGOS = {'D 붉은 낙관': L_D, 'E 금색 영문 워드마크': L_E, 'F 금빛 주화 엠블럼': L_F, 'G 한글 세리프 + 영문': L_G,
         'H 월계관 ED': L_H, 'I 2단 세로선': L_I, 'J 반투명 워터마크': L_J, 'K 금테 배지': L_K}

if __name__ == '__main__':
    bgs = [Image.open(O + 'bg1.png').convert('RGBA'), Image.open(O + 'bg2.png').convert('RGBA')]
    lab = fnt('SUIT-Bold.ttf', 30); cols, cw = 2, 860
    rows = []
    for name, fn in LOGOS.items():
        lg = fn(); lg.save(O + f'logo_{name[0]}.png')
        frames = []
        for bg in bgs:
            f = bg.copy(); f.alpha_composite(lg, (1280 - 34 - lg.width, max(8, (88 - lg.height) // 2))); frames.append(f.convert('RGB'))
        row = Image.new('RGB', (480 * 2 + 400 + 40, 270 + 50), (24, 24, 24)); d = ImageDraw.Draw(row); d.text((10, 6), name, font=lab, fill=(255, 220, 120))
        row.paste(frames[0].resize((480, 270), Image.LANCZOS), (10, 46)); row.paste(frames[1].resize((480, 270), Image.LANCZOS), (500, 46))
        row.paste(frames[1].crop((1280 - 560, 0, 1280, 280)).resize((400, 200), Image.LANCZOS), (990 + 0, 46)); rows.append(row)
    sheet = Image.new('RGB', (rows[0].width * 2 + 10, (len(rows) + 1) // 2 * (rows[0].height + 6)), (24, 24, 24))
    for i, r in enumerate(rows): sheet.paste(r, ((i % 2) * (r.width + 10), (i // 2) * (r.height + 6)))
    sheet.save(O + 'logo_options2.jpg', quality=88); print('ok', sheet.size)
