"""금리 편 썸네일 3안 (2026-11-27, 대표 11/26 제목 "이자는 원래 “죄”였다" — 따옴표로 안 헷갈리게)
손정의 편 틀(흑백 + 핑크, 왼쪽 큰 글씨, 오른쪽 그림에 빛) 그대로 · 사진은 이번 편 시네마틱 생성 사진·볼커 실제 사진
사용: python3 scripts/youtube/long/drafts/L261204-rate_thumbs.py <out_dir>
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, ".."))
import vn2
LIB = os.path.join(HERE, "..", "..", "..", "blog", "media", "lib")
TW, TH = 1280, 720; PINK = vn2.PINK; WHITE = (255, 255, 255, 255); GREY = (200, 200, 205, 255)

SETS = [
    dict(file="thumb_a.jpg", photo="il_R1204_stone_tablet.png", face=(.50, .45), zoom=1.1, fx=.5, side="right",
         top="4,000년 금리의 역사", l1=[("이자는 원래", "w")], l2=[("“죄”", "pink"), ("였다", "w")]),
    dict(file="thumb_b.jpg", photo="il_R1204b_dante_hell.png", face=(.55, .45), zoom=1.1, fx=.5, side="right",
         top="단테가 지옥에 보낸 사람들", l1=[("이자 받으면", "w")], l2=[("지옥", "pink"), ("에 갔다", "w")]),
    dict(file="thumb_c.jpg", photo="commons_volcker_1.jpg", face=(.50, .22), zoom=1.0, fx=.5, side="right",
         top="키 2미터 연준 의장", l1=[("금리 ", "w"), ("20%", "pink")], l2=[("세상을 멈춘 남자", "w")]),
]

def F(w, s):
    return vn2.SUIT(w if os.path.exists(os.path.join(vn2.FD, f"SUIT-{w}.ttf")) else "ExtraBold", s)


def grade(t):
    im = Image.open(os.path.join(LIB, t["photo"])).convert("RGB")
    s = max(TW / im.width, TH / im.height) * t["zoom"]
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    # 얼굴이 오른쪽 2/3 지점에 오도록
    fxp, fyp = t["face"]; cx = int(im.width * fxp); cy = int(im.height * fyp)
    x0 = cx - int(TW * t.get("fpos", .68))
    if x0 < 0:   # 얼굴을 더 오른쪽에 두려면 왼쪽을 어둡게 늘린다
        pad = Image.new("RGB", (im.width - x0, im.height), (12, 12, 14)); pad.paste(im, (-x0, 0)); im = pad; x0 = 0
    x0 = min(x0, im.width - TW); y0 = min(max(0, cy - int(TH * .40)), im.height - TH)
    im = im.crop((x0, y0, x0 + TW, y0 + TH))
    g = ImageEnhance.Color(im).enhance(.12)                       # 거의 흑백
    g = ImageEnhance.Contrast(g).enhance(1.35)
    g = Image.merge("RGB", [c.point(lambda v, k=k: int(v * k)) for c, k in zip(g.split(), (.92, .96, 1.06))])   # 차가운 톤
    # 얼굴 쪽만 빛: 방사형 마스크
    m = Image.new("L", (TW, TH), 0); d = ImageDraw.Draw(m)
    fx, fy = int(TW * .68), int(TH * .40)
    for r in range(620, 0, -6):
        d.ellipse([fx - r, fy - int(r * 1.05), fx + r, fy + int(r * 1.05)], fill=int(255 * (1 - r / 620) ** .55))
    m = m.filter(ImageFilter.GaussianBlur(40))
    dark = ImageEnhance.Brightness(g).enhance(.22)
    lit = ImageEnhance.Brightness(g).enhance(1.12)
    out = Image.composite(lit, dark, m).convert("RGBA")
    # 핑크 림라이트(얼굴 오른쪽 가장자리)
    glow = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([int(TW * .80), int(TH * .02), int(TW * 1.15), int(TH * .95)], fill=(*PINK, 70))
    out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    # 왼쪽 글씨 자리 어둡게
    L = Image.new("RGBA", (TW, TH)); ld = ImageDraw.Draw(L)
    for x in range(TW): ld.line([x, 0, x, TH], fill=(0, 0, 0, int(235 * max(0, 1 - x / (TW * .62)) ** 1.3)))
    out.alpha_composite(L)
    return out


def shadow_text(th, xy, s, f, fill, blur=14):
    lay = Image.new("RGBA", th.size, (0, 0, 0, 0)); ImageDraw.Draw(lay).text(xy, s, font=f, fill=fill)
    sh = lay.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * .9))
    o = Image.new("RGBA", th.size, (0, 0, 0, 0)); o.paste((0, 0, 0, 255), (4, 6), sh); o.alpha_composite(lay); th.alpha_composite(o)


def render_chips(t, out):
    th = grade(t)
    L = vn2.logo_layer(30); th.alpha_composite(L, (TW - 40 - L.width + 12, 34))
    D = ImageDraw.Draw(th); LX = 56
    ft = F("ExtraBold", 74); D.rectangle([LX, 70 + 10, LX + 12, 70 + 80], fill=(*PINK, 255))
    shadow_text(th, (LX + 30, 70), t["top"], ft, (235, 235, 240, 255), 10)
    cw, ch, gap, y0 = 184, 196, 14, 200
    fn = F("Heavy", 46); fv = F("Heavy", 54)
    for i, (n, v, k) in enumerate(t["chips"]):
        x = LX + i * (cw + gap)
        col = {"up": (150, 150, 158), "down": (150, 150, 158), "q": (*PINK,)}[k]   # 12:02 대표 "색이 너무 많아 헷갈린다": 흑백 + 핑크(마지막 칸)만
        box = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
        bd.rounded_rectangle([x, y0, x + cw, y0 + ch], 18, fill=(14, 14, 18, 215), outline=(*col, 255), width=5)
        th.alpha_composite(box); D = ImageDraw.Draw(th)
        z = 46
        while D.textlength(n, font=F("Heavy", z)) > cw - 24: z -= 2
        D.text((x + (cw - D.textlength(n, font=F("Heavy", z))) / 2, y0 + 26), n, font=F("Heavy", z), fill=(255, 255, 255))
        zv = 54
        while D.textlength(v, font=F("Heavy", zv)) > cw - 24: zv -= 2
        D.text((x + (cw - D.textlength(v, font=F("Heavy", zv))) / 2, y0 + 104 + (54 - zv) // 2), v, font=F("Heavy", zv), fill=(*(col if k == "q" else (255, 255, 255)), 255))
        if k != "q" and i < 3: pass
    fb = F("Heavy", 136); y1 = TH - 70 - fb.size; x = LX
    for txt, c in t["l1"]:
        shadow_text(th, (x, y1), txt, fb, WHITE if c == "w" else (*PINK, 255)); x += ImageDraw.Draw(th).textlength(txt, font=fb)
    th.convert("RGB").save(out, quality=93); print(t["file"])


def render(t, out):
    if t.get("kind") == "chips": return render_chips(t, out)
    th = grade(t)
    L = vn2.logo_layer(30); th.alpha_composite(L, (TW - 40 - L.width + 12, 34))
    D = ImageDraw.Draw(th); LX = 64; MAXW = int(TW * .60)
    COL = {"w": WHITE, "pink": (*PINK, 255)}
    ft = F("ExtraBold", 74)
    z = 124
    while max(D.textlength("".join(p for p, _ in t["l1"]), font=F("Heavy", z)), D.textlength("".join(p for p, _ in t["l2"]), font=F("Heavy", z))) > MAXW: z -= 4
    fb = F("Heavy", z)
    y2 = TH - 64 - fb.size; y1 = y2 - 8 - fb.size; yt = y1 - 30 - ft.size
    # 위 작은 줄: 핑크 막대 + 회색 글씨
    D.rectangle([LX, yt + 10, LX + 12, yt + ft.size + 6], fill=(*PINK, 255))
    zt = ft.size
    while ImageDraw.Draw(th).textlength(t["top"], font=F("ExtraBold", zt)) > TW * .66: zt -= 2
    shadow_text(th, (LX + 30, yt + (ft.size - zt)), t["top"], F("ExtraBold", zt), (235, 235, 240, 255), 10)
    for parts, y in ((t["l1"], y1), (t["l2"], y2)):
        x = LX
        for txt, c in parts:
            shadow_text(th, (x, y), txt, fb, COL[c]); x += ImageDraw.Draw(th).textlength(txt, font=fb)
    th.convert("RGB").save(out, quality=93); print(t["file"], "글씨", z)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."; os.makedirs(out, exist_ok=True)
    for t in SETS: render(t, os.path.join(out, t["file"]))
