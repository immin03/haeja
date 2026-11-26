"""손정의 × AI 버블 썸네일 A·B·C v2 (2026-11-26 01:50 대표: "신비롭게, AI 버블의 주범 손정의 느낌으로 세게.
AI 버블의 모든 것, 그 뒤에는 손정의가 있다")
벤치마킹: 「인류 역사상 가장 많은 돈을 잃은 사람, 손정의」(딥다이브), 「"이대로면 99%가 다 죽는다" 엔비디아 울며 팔고 4조 태운 손정의」,
「1년 만에 재산 99%가 사라진 남자」, Just In Time 인물 편(어두운 배경 + 얼굴 한쪽 조명 + 큰 질문)
- 어둡고 차가운 흑백 톤, 얼굴만 빛을 받게(나머지는 그림자), 핑크 림라이트, 글씨는 얼굴 반대편에 크게
사용: python3 scripts/youtube/long/drafts/L261126-son_thumbs.py <out_dir>
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, ".."))
import vn2
LIB = os.path.join(HERE, "..", "..", "..", "blog", "media", "lib")
TW, TH = 1280, 720; PINK = vn2.PINK; WHITE = (255, 255, 255, 255); GREY = (200, 200, 205, 255)

SETS = [
    dict(file="thumb_a.jpg", photo="son_portrait_clean.png", face=(.50, .30), zoom=1.15, fx=.5, side="right",
         top="AI 버블의 모든 것", l1=[("그 뒤엔", "w")], l2=[("손정의", "pink"), ("가 있다", "w")]),
    dict(file="thumb_b.jpg", photo="son_whitehouse_clean.png", face=(.47, .30), zoom=1.35, fx=.42, side="right",
         top="99% 잃은 남자의 마지막 베팅", l1=[("AI 버블의 주범?", "w")], l2=[("손정의", "pink")]),   # 12:03 대표: 이름을 적어줘
    dict(file="thumb_c.jpg", photo="son_2000_press_clean.png", face=(.52, .28), zoom=1.2, fx=.62, side="right",
         top="역사상 가장 많은 돈을 잃은 남자", l1=[("AI 버블을", "w")], l2=[("설계한 ", "w"), ("남자", "pink")]),
    dict(file="thumb_d.jpg", photo="son_whitehouse_clean.png", face=(.45, .30), zoom=1.2, fx=.5, fpos=.80, side="right", kind="chips",   # 2026-11-26 01:52 대표: 알리바바·쿠팡·위워크·오픈AI 나열형 1안
         top="손정의가 베팅한 회사들", chips=[("알리바바", "2,500배", "up"), ("위워크", "파산", "down"), ("쿠팡", "10배", "up"), ("????", "?", "q")],   # 12:01 대표: 오픈AI 가리기
         l1=[("다음은 ", "w"), ("OOOO", "pink")], l2=[]),
    dict(file="thumb_e.jpg", photo="son_whitehouse_clean.png", face=(.45, .30), zoom=1.2, fx=.5, fpos=.80, side="right", kind="chips",   # 2026-11-26 01:52 대표: 알리바바·쿠팡·위워크·오픈AI 나열형 1안
         top="손정의의 베팅 성적표", chips=[("알리바바", "2,500배", "up"), ("위워크", "파산", "down"), ("오픈AI", "?", "q")],   # 12:01 대표: 오픈AI 가리기
         l1=[("대박? ", "w"), ("파산?", "pink")], l2=[]),   # 14:03 대표 "D는 궁금하지 않다" → 결과를 묻는 안
    # 14:04 대표 "D·E 둘 다 안 궁금하다" → 인물 한마디(큰따옴표) · 내 계좌 · 이야기 반전 3안
    dict(file="thumb_f.jpg", photo="son_whitehouse_clean.png", face=(.47, .30), zoom=1.35, fx=.42, side="right",
         top="AI 버블을 묻자 손정의가 한 말", l1=[("“멍청한", "w")], l2=[("질문입니다”", "pink")]),
    dict(file="thumb_g.jpg", photo="son_whitehouse_clean.png", face=(.47, .30), zoom=1.35, fx=.42, side="right",
         top="손정의가 무너지면", l1=[("내 삼성전자·", "w")], l2=[("SK하이닉스는?", "pink")]),
    dict(file="thumb_h.jpg", photo="son_2000_press_clean.png", face=(.52, .28), zoom=1.2, fx=.62, side="right",
         top="엔비디아를 울면서 팔았다", l1=[("빚까지 내서", "w")], l2=[("전부 걸었다", "pink")]),
    # 14:06 대표: 2·3안(A·B) 유지, 1안만 — "손정의가 AI 미래를 좌지우지한다" 강하게
    dict(file="thumb_i.jpg", photo="son_whitehouse_clean.png", face=(.45, .30), zoom=1.2, fx=.5, fpos=.80, side="right",
         top="오픈AI·Arm·스타게이트의 주인", l1=[("AI의 미래는", "w")], l2=[("이 남자", "pink"), ("가 정한다", "w")]),
    dict(file="thumb_j.jpg", photo="son_whitehouse_clean.png", face=(.45, .30), zoom=1.2, fx=.5, fpos=.80, side="right",
         top="AI 판을 쥔 단 한 사람", l1=[("AI의 운명,", "w")], l2=[("손정의", "pink"), (" 손에", "w")]),


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
