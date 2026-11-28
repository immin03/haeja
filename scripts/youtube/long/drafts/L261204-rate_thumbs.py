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
    dark = ImageEnhance.Brightness(g).enhance(t.get("dark", .22))
    lit = ImageEnhance.Brightness(g).enhance(t.get("lit", 1.12))
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


# 2026-11-27 18:38 대표 "이걸 보겠냐 — 벤치마킹하고 다시(금리의 모든 것 · 금리가 지배하는 세상 · 12월 9일 전 반드시)"
# 벤치마킹(금리·돈 원리 상위 40편): 밝은 사진, '금리' 두 글자가 가장 큼, "이거 하나로 끝·N분 만에·모든 것" 약속형, 2줄
SETS2 = [   # 18:57 대표 확정: 금리의 모든 것 · 금리가 지배하는 세상 · 금리 모르면 투자하지 마세요 — 글씨는 기존 크기
    dict(file="thumb_a.jpg", photo="il_L261113g_fed_dusk.jpeg", face=(.5, .45), zoom=1.0, dark=.42, lit=1.25,
         top="12월 9일 전 필수 시청", top_hi="12월 9일", chip="D-11", l1=[("11분 만에 끝내는", "w")], l2=[("금리", "pink"), ("의 모든 것", "w")]),
    dict(file="thumb_b.jpg", photo="il_R1204_trading_screens.png", face=(.5, .45), zoom=1.0, dark=.42, lit=1.25,
         top="12월 9일 전 필수 시청", top_hi="12월 9일", chip="총정리", l1=[("금리", "pink"), ("가", "w")], l2=[("지배하는 세상", "w")]),
    dict(file="thumb_c.jpg", photo="il_R1204b_fomc_room.png", face=(.5, .45), zoom=1.0, dark=.42, lit=1.25,
         top="12월 9일 전 필수 시청", top_hi="12월 9일", chip="필수", l1=[("금리", "pink"), (" 모르면", "w")], l2=[("투자하지 마세요", "w")]),
]
def render2(t, out):
    th = grade(t)
    L = vn2.logo_layer(30); th.alpha_composite(L, (TW - 40 - L.width + 12, 34))
    D = ImageDraw.Draw(th); LX = 56; MAXW = int(TW * .72); COL = {"w": WHITE, "pink": (*PINK, 255)}
    def fit(parts, z0, mw):
        z = z0
        while D.textlength("".join(p for p, _ in parts), font=F("Heavy", z)) > mw: z -= 4
        return z
    z2 = fit(t["l2"], 160, MAXW); z1 = fit(t["l1"], 150, MAXW)
    if abs(z1 - z2) < 50: z1 = z2 = min(z1, z2)
    y2 = TH - 56 - z2; y1 = y2 - 6 - z1
    # 왼쪽 위 배너 — 2026-11-28 대표 "더 세련되게": BANNER 환경변수로 모양 선택 (pill: 검은 유리 + 핑크 점 / bar: 핑크 세로선 / chip: 핑크 칩 + 유리 띠)
    import os as _os; BS = _os.environ.get("BANNER", "bar"); top = t["top"]; hi = t.get("top_hi", "")
    fz = 66 if BS == "bar" else 50   # 11/28 10:09 대표: "12월 9일 전 필수 시청", 대제목 바로 위, 글씨 조금 더 크게
    while D.textlength(top, font=F("Bold", fz)) > TW * .64: fz -= 2
    fB = F("Bold", fz); fw = D.textlength(top, font=fB); by = y1 - fz - 30   # 대제목 바로 위
    lay = Image.new("RGBA", th.size, (0, 0, 0, 0)); L = ImageDraw.Draw(lay)
    def words(x0, y0, col_hi):
        x = x0
        if hi and top.startswith(hi):
            L.text((x, y0), hi, font=fB, fill=col_hi); x += L.textlength(hi, font=fB); rest = top[len(hi):]
        else: rest = top
        L.text((x, y0), rest, font=fB, fill=(255, 255, 255, 255))
    if BS == "pill":
        h = fz + 30; w = fw + 30 + 26 + 34
        L.rounded_rectangle([LX, by, LX + w, by + h], h // 2, fill=(14, 14, 18, 190), outline=(255, 255, 255, 70), width=2)
        cy = by + h // 2; L.ellipse([LX + 26 - 9, cy - 9, LX + 26 + 9, cy + 9], fill=(*PINK, 255))
        glow = Image.new("RGBA", th.size, (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([LX + 26 - 22, cy - 22, LX + 26 + 22, cy + 22], fill=(*PINK, 120))
        th.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
        words(LX + 50, by + 11, (*PINK, 255))
    elif BS == "bar":
        L.rounded_rectangle([LX, by + 2, LX + 9, by + fz + 18], 4, fill=(*PINK, 255))
        words(LX + 26, by + 2, (*PINK, 255))
        L.rectangle([LX + 26, by + fz + 22, LX + 26 + fw, by + fz + 24], fill=(255, 255, 255, 90))
    else:   # chip
        cw = L.textlength(t.get("chip", "D-11"), font=fB) + 36; h = fz + 30
        L.rounded_rectangle([LX, by, LX + cw + fw + 40, by + h], 14, fill=(14, 14, 18, 200), outline=(255, 255, 255, 60), width=2)
        L.rounded_rectangle([LX + 6, by + 6, LX + cw, by + h - 6], 10, fill=(*PINK, 255))
        L.text((LX + 6 + (cw - 6 - L.textlength(t.get("chip", "D-11"), font=fB)) / 2, by + 11), t.get("chip", "D-11"), font=fB, fill=(255, 255, 255, 255))
        L.text((LX + cw + 20, by + 11), top, font=fB, fill=(255, 255, 255, 255))
    sh = lay.split()[3].filter(ImageFilter.GaussianBlur(12)); shl = Image.new("RGBA", th.size, (0, 0, 0, 0)); shl.putalpha(sh.point(lambda v: int(v * .55)))
    th.alpha_composite(shl); th.alpha_composite(lay)
    for parts, y, z in ((t["l1"], y1, z1), (t["l2"], y2, z2)):
        x = LX; f = F("Heavy", z)
        for txt, c in parts:
            shadow_text(th, (x, y), txt, f, COL[c], 18); x += ImageDraw.Draw(th).textlength(txt, font=f)
    th.convert("RGB").save(out, quality=93); print(t["file"], z1, z2)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "v2":
        os.makedirs(sys.argv[1], exist_ok=True)
        for t in SETS2: render2(t, os.path.join(sys.argv[1], t["file"]))
        sys.exit()
    out = sys.argv[1] if len(sys.argv) > 1 else "."; os.makedirs(out, exist_ok=True)
    for t in SETS: render(t, os.path.join(out, t["file"]))
