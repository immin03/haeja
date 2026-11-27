# 계기판 공유 카드 (2026-11-28 대표: 공유받은 사람도 바로 들어와 가입하고 싶게)
# 켜진 신호 조합(0~31)마다 카톡 미리보기용 페이지(/share/semi-<n>, /share/gold-<n>)와 그림(/brand/share/*.jpg)을 미리 만들어 둔다.
# 신호 이름이 바뀌면 SIG 를 고치고 다시 돌린다:  python3 scripts/share/build.py
import os, html
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = "https://www.valuenote.co.kr"
SIG = {"semi": ("반도체", ["실적", "가격", "기간", "공포", "금리"], "/semi"), "gold": ("금", ["실질금리", "연준", "달러", "금 ETF", "공포"], "/gold")}
CARD = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:'SUIT Variable';src:url({site}/fonts/SUIT-Variable.woff2) format('woff2');font-weight:100 900}}
*{{box-sizing:border-box}}body{{margin:0;width:1200px;height:630px;background:linear-gradient(160deg,#262626 0%,#141414 55%,#000 100%);color:#fff;font-family:'SUIT Variable',sans-serif;word-break:keep-all;padding:54px 70px;display:flex;flex-direction:column}}
.wm{{font-family:Helvetica,Arial,sans-serif;font-size:30px;letter-spacing:.06em}}.wm b{{font-weight:800}}.wm span{{font-weight:300}}
.t{{font-size:44px;font-weight:700;color:#BDBDBD;margin-top:34px}}
.n{{font-size:104px;font-weight:900;letter-spacing:-.03em;line-height:1.15;margin-top:2px}}.n em{{font-style:normal;color:#FF4D6D}}
.l{{display:flex;gap:18px;margin-top:auto}}
.l div{{flex:1;border:3px solid #3A3A3A;background:#1A1A1A;border-radius:22px;padding:22px 0 20px;text-align:center;font-size:32px;font-weight:800;color:#8A8A8A;white-space:nowrap}}
.l i{{display:block;width:26px;height:26px;border-radius:13px;background:#4A4A4A;margin:0 auto 14px}}
.l .on{{border-color:#FF4D6D;background:#2A1418;color:#fff}}.l .on i{{background:#FF4D6D;box-shadow:0 0 0 8px rgba(255,77,109,.2)}}
</style></head><body><div class="wm"><b>VALUE</b><span>NOTE</span></div>
<div class="t">{name} 바닥 계기판</div><div class="n">{head}</div><div class="l">{lamps}</div></body></html>"""
PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><meta name="robots" content="noindex">
<meta property="og:type" content="website"><meta property="og:site_name" content="밸류노트">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:image" content="{site}/brand/share/{k}-{m}.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<script>(function(){{var q=new URLSearchParams(location.search),by=(q.get('by')||'').replace(/[^a-z0-9]/gi,'').slice(0,12);location.replace('{to}?ref=share'+(by?'-'+by:''));}})();</script>
</head><body><a href="{to}?ref=share">{name} 바닥 계기판 보기</a></body></html>"""
def head(n): return "아직 <em>0개</em>입니다" if n == 0 else f"5개 중 <em>{n}개</em> 켜졌습니다"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    for k, (name, sigs, to) in SIG.items():
        for m in range(32):
            on = [bool(m >> i & 1) for i in range(5)]; n = sum(on)
            lamps = "".join(f'<div class="{"on" if o else ""}"><i></i>{html.escape(s)}</div>' for s, o in zip(sigs, on))
            pg.set_content(CARD.format(site=SITE, name=name, head=head(n), lamps=lamps)); pg.wait_for_timeout(350 if m else 2500)
            pg.screenshot(path=f"{ROOT}/brand/share/{k}-{m}.jpg", type="jpeg", quality=82)
            lit = " · ".join(s for s, o in zip(sigs, on) if o)
            title = f"{name} 바닥 계기판, " + ("아직 0개입니다" if n == 0 else f"5개 중 {n}개 켜졌습니다")
            desc = (f"켜진 신호: {lit}. " if lit else "") + "신호가 바뀌는 날 카카오톡으로 알려 드립니다."
            open(f"{ROOT}/share/{k}-{m}.html", "w", encoding="utf-8").write(PAGE.format(site=SITE, k=k, m=m, title=title, desc=desc, to=to, name=name))
    b.close()
