"""영상 속 앱 화면 5초 (2026-11-17 대표님 확정: 테슬라 2편부터, 영상마다 그 종목 페이지를 5초 보여 준다)
- 실제 종목 페이지(https://www.valuenote.co.kr/c/<slug>)를 휴대전화 크기로 렌더 직전에 캡처 → 숫자가 늘 최신
- 검은 바탕 + 오른쪽 휴대전화 화면이 천천히 스크롤, 점수 줄에 핑크 밑줄 / 왼쪽: 라벨 + 회사 이름 (주소는 넣지 않음) / 자막 52px
사용: python3 appscreen.py <slug> <회사명> <out.mp4> ["자막1|자막2"]
배경음은 넣지 않는다 (본편 음악·내레이션 아래에 그대로 깔린다)
"""
import os, sys, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vn2
from vn2 import W, H, SUIT, NS, PINK, eout, eio, clamp, _paste, _shadowed

FPS, DUR = 30, 5.0
N = int(FPS * DUR)
SLUG, NAME, MP4 = sys.argv[1], sys.argv[2], sys.argv[3]
SUBL = (sys.argv[4] if len(sys.argv) > 4 else f"{NAME} 점수와 적정 주가는|설명란 첫 줄 링크에서 보실 수 있습니다").split("|")
OUT = tempfile.mkdtemp(); SHOT = os.path.join(OUT, "page.png")
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); c = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True, locale="ko-KR", timezone_id="Asia/Seoul")
    pg = c.new_page(); pg.goto(f"https://www.valuenote.co.kr/c/{SLUG}", wait_until="networkidle", timeout=90000); pg.wait_for_timeout(2500)
    SCORE_Y = pg.evaluate(r"""() => { const e=[...document.querySelectorAll('*')].filter(x=>x.children.length===0 && /\/ ?100/.test(x.textContent||'')).map(x=>x.getBoundingClientRect().top + scrollY).filter(y=>y>200).sort((a,b)=>a-b)[0]; return e || 548 }""")
    pg.screenshot(path=SHOT, full_page=True); b.close()

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

SC0, SC1 = 0, 250                # 스크롤 (css px)
SUBS = [(0.0, 2.4, SUBL[0]), (2.4, 5.0, SUBL[-1])]


def left_text(im, t):
    a = eout((t - .2) / .6)
    if a <= 0: return
    lay = Image.new("RGBA", (900, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fl = NS("Medium", 30); x = 0
    for ch in f"밸류노트 · {NAME} 종목 페이지": d.text((x, 0), ch, font=fl, fill=(235, 235, 235, 255)); x += d.textlength(ch, font=fl) + 5
    ln = 560 * eout((t - .4) / .7)
    d.rectangle([0, 52, ln, 54], fill=(255, 255, 255, 220)); d.rounded_rectangle([0, 49, min(64, ln), 57], 4, fill=(*PINK, 255))
    # 2026-11-17 대표님: 주소(/c/tsla)까지 보이면 지저분 → 이름과 한 줄 설명만
    d.text((0, 96), NAME, font=SUIT("Bold", 72), fill=(255, 255, 255, 255))
    d.text((0, 200), "같은 기준으로 매일 계산하는 기업 점수", font=NS("Regular", 30), fill=(205, 205, 205, 255))
    _paste(im, _shadowed(lay, 8, .5), (150 - 20 * (1 - a), 250), a)


for k in range(N):
    t = k / FPS
    im = BG.copy()
    left_text(im, t)
    # 폰: 아래에서 살짝 올라오며 나타남
    pa = eout(t / .7); dy = int(40 * (1 - pa))
    sc = SC0 + (SC1 - SC0) * eio((t - 1.0) / 2.0)
    oy = int(sc * K)
    scr = page.crop((0, oy, SCR_W, oy + SCR_H)).convert("RGBA")
    # 점수 줄 핑크 밑줄 (3.1초~)
    ua = eout((t - 3.1) / .5)
    if ua > 0:
        d = ImageDraw.Draw(scr); y = int((SCORE_Y - sc) * K) + 26; x0 = int(34 * K)
        d.rounded_rectangle([x0, y, x0 + int(150 * K * ua), y + 8], 4, fill=(*PINK, 255))
    phone = Image.new("RGBA", body.size, (0, 0, 0, 0)); phone.alpha_composite(body)
    phone.paste(scr, (BZ, BZ), mask)
    _paste(im, body_sh, (PX - BZ - 80, PY - BZ - 80 + dy), pa)
    _paste(im, phone, (PX - BZ, PY - BZ + dy), pa)
    vn2.logo(im)
    for s0, s1, txt in SUBS:
        if s0 <= t < s1 or (s1 == DUR and t >= s0):
            vn2.subtitle_line(im, txt, clamp((t - s0) / .12) if s0 else 1.0)
    im.convert("RGB").save(os.path.join(OUT, f"f{k:04d}.png"))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(OUT, "f%04d.png"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", MP4], check=True)
print("앱 화면", SLUG, MP4)
