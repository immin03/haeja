"""황제의 일기 한국 롱폼 썸네일 v2 시안 (2026-11-12 대표: "기존 디자인틀 어느정도 유지하면서 바꾸는거 시도해보자").
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


# A: 황제 vs 카시우스 — 지금 쓰는 장면 그대로, 얼굴 크게 + 글자 크게
a = Image.new('RGB', (W, H)); L = fit('cep1i_spk.jpeg', (700, H), .55, .15, 1.3); R = fit('cep1i_ctalk.jpeg', (840, H), .5, .1, 1.35)
a.paste(R, (440, 0)); a.paste(L, (0, 0), grad(700, H, 470, 690, 1, 0))
a = fin(a); a = coin(a, 640, 140, 380, .18); a = bottom_dark(a, 360, .62)
text(a, ['뒤통수 친 사람,', '이렇게 이겨라'], [IVO, IVO2], [150, 190]).save(O + 'thumb2_A.jpg', quality=93)

# B: 불 앞의 황제 얼굴 크게(오른쪽) + 질문형
b = Image.new('RGB', (W, H)); bg = fit('c1_burn.jpeg', (W, H), .5, .5, 1.0); e = fit('c1_emp_fire.jpeg', (720, H), .5, .12, 1.35)
b.paste(bg, (0, 0)); b.paste(e, (560, 0), grad(720, H, 0, 220, 0, 1)); b = fin(b, 1.12); b = coin(b, 300, 210, 440, .2); b = bottom_dark(b, 360, .6)
text(b, ['믿었던 사람이', '등 돌렸을 때'], [IVO, IVO2], [140, 186]).save(O + 'thumb2_B.jpg', quality=93)

# C: 불타는 상자 — 이야기 훅
c = Image.new('RGB', (W, H)); ch = fit('c1_chest.jpeg', (820, H), .45, .35, 1.1); e2 = fit('c1_emp_listen.jpeg', (620, H), .5, .08, 1.45)
c.paste(ch, (0, 0)); c.paste(e2, (660, 0), grad(620, H, 0, 220, 0, 1)); c = fin(c, 1.12); c = coin(c, 1040, 170, 420, .15); c = bottom_dark(c, 360, .6)
text(c, ['배신자 명단을', '황제는 불태웠다'], [IVO, IVO2], [140, 170]).save(O + 'thumb2_C.jpg', quality=93)

# 비교판: 위 = 지금 썸네일, 아래 = 새 시안 3장 / 휴대폰 크기(320px) 줄
cur = Image.open(O + 'cur.jpg').convert('RGB').resize((W // 2, H // 2)) if os.path.exists(O + 'cur.jpg') else None
s = Image.new('RGB', (W * 3 // 2 + 40, H + 60), (24, 24, 24)); d = ImageDraw.Draw(s); lf = S_('Bold', 26)
if cur: s.paste(cur, (10, 30)); d.text((10, 0), '지금', font=lf, fill=(220, 220, 220))
for i, n in enumerate('ABC'):
    s.paste(Image.open(O + f'thumb2_{n}.jpg').resize((W // 2, H // 2)), (10 + i * (W // 2 + 10), H // 2 + 50)); d.text((10 + i * (W // 2 + 10), H // 2 + 20), f'새 시안 {n}', font=lf, fill=(246, 234, 210))
m = Image.new('RGB', (4 * 330 + 10, 200), (24, 24, 24))
if cur: m.paste(cur.resize((320, 180)), (10, 10))
for i, n in enumerate('ABC'): m.paste(Image.open(O + f'thumb2_{n}.jpg').resize((320, 180)), (10 + (i + 1) * 330, 10))
s.save(O + 'thumb2_sheet.jpg', quality=92); m.save(O + 'thumb2_mobile.jpg', quality=92)
