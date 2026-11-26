"""금값 3편 썸네일 v2 (2026-11-26 대표: 시청 시간은 괜찮은데 유입이 안 됨 → 썸네일·제목 교체)
- '3편'·'5가지'·'1개 켜졌다'를 뺀다(새 시청자가 막히는 말)
- 숫자 충격(101만 → 66만, 약 -35%) + 질문, C안의 '금이 AI 주식처럼 팔렸다' 각도 살림
- 손정의 편 v3 형식: 큰 두 줄 124px, 왼쪽 어둡게
- 10:32 대표: 2·3안도 금이 확실히 보이게(금고 선반·금괴 사진), 계기판 더 크게, 계기판 틀을 조금 위로
- 10:17 대표: 계기판(바닥 신호 5개 중 1개)을 명확히 보여 주고, 색은 촌스럽지 않게 통일 → 글씨는 흰색 + 핑크 하나만, 금색 글씨 없앰
사용: python3 scripts/youtube/long/drafts/L261124-gold-3_thumbs_v2.py <out_dir>
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, ".."))
import vn2
LIB = os.path.join(HERE, "..", "..", "..", "blog", "media", "lib")
TW, TH = 1280, 720; PINK = vn2.PINK; WHITE = (255, 255, 255, 255); GOLD = (244, 196, 80, 255)

SETS = [
    dict(file="thumb_v2_1.jpg", photo="il_L261124g_thumb_goldbars.jpeg", shift=.18,
         top="금값 바닥 신호", l1=[("금값 35% ", "w"), ("폭락", "pink")], l2=[("바닥은 ", "w"), ("어디?", "pink")]),
    dict(file="thumb_v2_2.jpg", photo="il_L261124g_goldvault_wide.jpeg", shift=.10,
         top="금값 바닥 신호", l1=[("101만 → 66만", "w")], l2=[("지금 ", "w"), ("사도 될까?", "pink")]),
    dict(file="thumb_v2_3.jpg", photo="il_L261113g2_gold_2015.jpeg", shift=.20,
         top="금값 바닥 신호", l1=[("안전자산의", "w")], l2=[("배신", "pink")]),
]


def F(w, s):
    return vn2.SUIT(w if os.path.exists(os.path.join(vn2.FD, f"SUIT-{w}.ttf")) else "ExtraBold", s)


def base(t):
    im = Image.open(os.path.join(LIB, t["photo"])).convert("RGB")
    s = max(TW / im.width, TH / im.height) * 1.08
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    # 피사체를 오른쪽으로: 왼쪽을 어둡게 늘려 붙인다
    sh = int(TW * t["shift"]); pad = Image.new("RGB", (im.width + sh, im.height), (8, 8, 10)); pad.paste(im, (sh, 0)); im = pad
    x0 = (im.width - TW) // 2 + sh // 2; y0 = (im.height - TH) // 2
    im = im.crop((x0, y0, x0 + TW, y0 + TH))
    im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(.9)).enhance(1.15)
    out = im.convert("RGBA")
    L = Image.new("RGBA", (TW, TH)); d = ImageDraw.Draw(L)
    for x in range(TW): d.line([x, 0, x, TH], fill=(0, 0, 0, int(240 * max(0, 1 - x / (TW * .66)) ** 1.2)))
    out.alpha_composite(L)
    B = Image.new("RGBA", (TW, TH)); d = ImageDraw.Draw(B)
    for y in range(TH // 2, TH): d.line([0, y, TW, y], fill=(0, 0, 0, int(150 * ((y - TH / 2) / (TH / 2)) ** 1.6)))
    out.alpha_composite(B)
    return out


def shadow_text(th, xy, s, f, fill, blur=14):
    lay = Image.new("RGBA", th.size, (0, 0, 0, 0)); ImageDraw.Draw(lay).text(xy, s, font=f, fill=fill)
    sh = lay.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * .9))
    o = Image.new("RGBA", th.size, (0, 0, 0, 0)); o.paste((0, 0, 0, 255), (4, 6), sh); o.alpha_composite(lay); th.alpha_composite(o)


def render(t, out):
    th = base(t)
    L = vn2.logo_layer(30); th.alpha_composite(L, (TW - 40 - L.width + 12, 34))
    D = ImageDraw.Draw(th); LX = 64; MAXW = int(TW * .64)
    COL = {"w": WHITE, "pink": (*PINK, 255), "gold": GOLD}
    z = 124
    while max(D.textlength("".join(p for p, _ in t["l1"]), font=F("Heavy", z)), D.textlength("".join(p for p, _ in t["l2"]), font=F("Heavy", z))) > MAXW: z -= 4
    fb = F("Heavy", z); ft = F("ExtraBold", 74)
    y2 = TH - 56 - fb.size; y1 = y2 - 6 - fb.size; yt = y1 - 150
    # 계기판: 램프 5개 중 1개 켜짐 + "5개 중 1개"
    yg = yt - 78; fl = F("ExtraBold", 68)
    r = 40; gy = yg + fl.size + 20; gx = LX
    P = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); ImageDraw.Draw(P).rounded_rectangle([LX - 26, yg - 20, LX + 5 * (2 * r + 20) + 470, gy + 2 * r + 26], 22, fill=(10, 10, 14, 170), outline=(255, 255, 255, 60), width=2); th.alpha_composite(P)
    shadow_text(th, (LX, yg), t["top"], fl, (235, 235, 240, 255), 8)
    g = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([gx - 16, gy - 16, gx + 2 * r + 16, gy + 2 * r + 16], fill=(*PINK, 150)); g = g.filter(ImageFilter.GaussianBlur(14)); th.alpha_composite(g)
    D = ImageDraw.Draw(th)
    for i in range(5):
        cx = gx + i * (2 * r + 20)
        if i == 0: D.ellipse([cx, gy, cx + 2 * r, gy + 2 * r], fill=(*PINK, 255))
        else: D.ellipse([cx, gy, cx + 2 * r, gy + 2 * r], fill=(20, 20, 24, 230), outline=(150, 150, 158, 255), width=4)
    tx = gx + 5 * (2 * r + 20) + 10; fz = F("Heavy", 74)
    shadow_text(th, (tx, gy + r - fz.size // 2 - 6), "5개 중 ", fz, WHITE, 8)
    shadow_text(th, (tx + ImageDraw.Draw(th).textlength("5개 중 ", font=fz), gy + r - fz.size // 2 - 6), "1개 켜짐", fz, (*PINK, 255), 8)
    for parts, y in ((t["l1"], y1), (t["l2"], y2)):
        x = LX
        for txt, c in parts:
            shadow_text(th, (x, y), txt, fb, COL[c]); x += ImageDraw.Draw(th).textlength(txt, font=fb)
    th.convert("RGB").save(out, quality=93); print(t["file"], z)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."; os.makedirs(out, exist_ok=True)
    for t in SETS: render(t, os.path.join(out, t["file"]))
