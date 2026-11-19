"""경제 레이더 화면 5초 (2026-11-19 대표: 긴급 롱폼 '투자자의 태도' 끝에 "이럴 때는 이런 걸 봐라" 맥락으로 5초)
appscreen.py 와 같은 틀(검은 바탕 + 오른쪽 휴대전화 스크롤, 주소 없음, 자막은 본편 렌더러가 그림).
화면은 체험 계정으로 미리 찍은 전체 페이지 캡처(PNG, 390 css px × 3배율)를 쓴다.
사용: python3 radarscreen.py <capture.png> <out.mp4> <끝 스크롤 css px>
"""
import os, sys, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vn2
from vn2 import W, H, SUIT, NS, PINK, eout, eio, clamp, _paste, _shadowed

FPS, DUR = 30, 5.6
N = int(FPS * DUR)
SHOT, MP4 = sys.argv[1], sys.argv[2]; END_Y = float(sys.argv[3]) if len(sys.argv) > 3 else 1560
NAME = "경제 레이더"; SUBL = [""]; OUT = tempfile.mkdtemp(); SCORE_Y = 0
full = Image.open(SHOT).convert("RGB")          # 390 css px 폭, 3배 해상도
SCR_H = 740; SCR_W = round(SCR_H * 390 / 844)               # 화면 크기 (영상 px)
K = SCR_W / 390                                             # css px → 영상 px
page = full.resize((SCR_W, round(full.height * SCR_W / full.width)), Image.LANCZOS)
BZ = 14; PX = 1180; PY = 70               # 폰 위치
R = 52

# 폰 테두리
body = Image.new("RGBA", (SCR_W + BZ * 2, SCR_H + BZ * 2), (0, 0, 0, 0))
ImageDraw.Draw(body).rounded_rectangle([0, 0, body.width - 1, body.height - 1], R + BZ, fill=(28, 28, 30, 255), outline=(70, 70, 74, 255), width=2)
_pad = Image.new("RGBA", (body.width + 160, body.height + 160), (0, 0, 0, 0)); _pad.alpha_composite(body, (80, 80))
body_sh = _shadowed(_pad, 30, .7, (0, 18))
mask = Image.new("L", (SCR_W, SCR_H), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, SCR_W - 1, SCR_H - 1], R, fill=255)

# 배경: 거의 검정 + 아주 옅은 비네트
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
v = np.clip(1 - (((xx - W * .62) / W) ** 2 + ((yy - H * .5) / H) ** 2) * 1.6, 0, 1)
bg = np.stack([10 + 16 * v, 10 + 16 * v, 12 + 17 * v], -1).astype(np.uint8)
BG = Image.fromarray(bg).convert("RGBA")

SC0 = 0; SC1 = END_Y   # 2026-11-17 대표님: 적정 주가 카드는 화면에 넣지 않는다 → 점수 줄 근처에서 시작해 조금만 스크롤
SUBS = []


def left_text(im, t):
    a = eout((t - .2) / .6)
    if a <= 0: return
    lay = Image.new("RGBA", (900, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fl = NS("Medium", 30); x = 0
    for ch in "밸류노트 앱 · 매일 아침 갱신": d.text((x, 0), ch, font=fl, fill=(235, 235, 235, 255)); x += d.textlength(ch, font=fl) + 5
    ln = 560 * eout((t - .4) / .7)
    d.rectangle([0, 52, ln, 54], fill=(255, 255, 255, 220)); d.rounded_rectangle([0, 49, min(64, ln), 57], 4, fill=(*PINK, 255))
    # 2026-11-17 대표님: 주소(/c/tsla)까지 보이면 지저분 → 이름과 한 줄 설명만
    d.text((0, 96), NAME, font=SUIT("Bold", 72), fill=(255, 255, 255, 255))
    d.text((0, 200), "위기 신호 10개를 신호등으로", font=NS("Regular", 30), fill=(205, 205, 205, 255))
    _paste(im, _shadowed(lay, 8, .5), (150 - 20 * (1 - a), 250), a)


for k in range(N):
    t = k / FPS
    im = BG.copy()
    left_text(im, t)
    # 폰: 아래에서 살짝 올라오며 나타남
    pa = eout(t / .7); dy = int(40 * (1 - pa))
    sc = SC0 + (SC1 - SC0) * eio((t - 1.6) / 2.6)
    oy = int(sc * K)
    scr = page.crop((0, oy, SCR_W, oy + SCR_H)).convert("RGBA")
    # 점수 줄 핑크 밑줄 (3.1초~)
    ua = 0
    if ua > 0:
        d = ImageDraw.Draw(scr); y = int((SCORE_Y - sc) * K) + 26; x0 = int(34 * K)
        d.rounded_rectangle([x0, y, x0 + int(150 * K * ua), y + 8], 4, fill=(*PINK, 255))
    phone = Image.new("RGBA", body.size, (0, 0, 0, 0)); phone.alpha_composite(body)
    phone.paste(scr, (BZ, BZ), mask)
    _paste(im, body_sh, (PX - BZ - 80, PY - BZ - 80 + dy), pa)
    _paste(im, phone, (PX - BZ, PY - BZ + dy), pa)
    # vn2.logo(im)  2026-11-18: 롱폼 렌더러가 오른쪽 위 로고를 이미 그린다 → 두 개가 겹쳐 보였음
    for s0, s1, txt in SUBS:
        if s0 <= t < s1 or (s1 == DUR and t >= s0):
            vn2.subtitle_line(im, txt, clamp((t - s0) / .12) if s0 else 1.0)
    im.convert("RGB").save(os.path.join(OUT, f"f{k:04d}.png"))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(OUT, "f%04d.png"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", MP4], check=True)
print("경제 레이더 화면", MP4)
