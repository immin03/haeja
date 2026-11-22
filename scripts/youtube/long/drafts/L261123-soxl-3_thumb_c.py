"""SOXL 3편 썸네일 C안 — 인물형 (2026-11-22 대표 20:14 "유명한 인물 위주로 썸네일", 20:22 "하나정도 넣어보자")
- 젠슨 황 실사(엔비디아 공식 사진) 오른쪽 · 왼쪽에 실제 원음 문구 + 질문
- 따옴표 문장은 영상 콜드 오픈에 실제로 나오는 원음(CNBC 2026.10, "the most consequential technology in history")만 쓴다
- A·B안과 같은 틀: 왼쪽 위 핑크 'SOXL 3편' 배지, 오른쪽 위 VALUE NOTE, 흑백 톤 + 핑크 강조
사용: python3 scripts/youtube/long/drafts/L261123-soxl-3_thumb_c.py <out.jpg>
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, ".."))
import vn2
LIB = os.path.join(HERE, "..", "..", "..", "blog", "media", "lib")
TW, TH = 1280, 720; PINK = vn2.PINK


def F(w, s):
    p = os.path.join(vn2.FD, f"SUIT-{w}.ttf")
    return vn2.SUIT(w if os.path.exists(p) else "ExtraBold", s)


def shadow_text(th, xy, s, f, fill):
    lay = Image.new("RGBA", th.size, (0, 0, 0, 0)); ImageDraw.Draw(lay).text(xy, s, font=f, fill=fill)
    sh = lay.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * .8))
    o = Image.new("RGBA", th.size, (0, 0, 0, 0)); o.paste((0, 0, 0, 255), (3, 5), sh); o.alpha_composite(lay); th.alpha_composite(o)


def render(out):
    th = Image.new("RGBA", (TW, TH), (14, 14, 16, 255))
    ph = Image.open(os.path.join(LIB, "ph_huang_nvidia.jpg")).convert("RGB")   # 1920x1920 엔비디아 공식 사진(팔짱)
    s = (TH + 60) / ph.height; ph = ph.resize((int(ph.width * s), int(ph.height * s)), Image.LANCZOS)
    ph = ImageEnhance.Color(ph).enhance(.35); ph = ImageEnhance.Brightness(ph).enhance(.72); ph = ImageEnhance.Contrast(ph).enhance(1.12)
    th.paste(ph, (TW - ph.width + 150, -18))
    g = Image.new("RGBA", (TW, TH)); d = ImageDraw.Draw(g)   # 왼쪽을 어둡게(글자 자리) — 얼굴은 밝게 남긴다
    for x in range(TW): d.line([x, 0, x, TH], fill=(10, 10, 12, int(255 * min(1, max(0, (760 - x) / 330)) ** .9)))
    th.alpha_composite(g); g = Image.new("RGBA", (TW, TH)); d = ImageDraw.Draw(g)
    for y in range(TH // 2, TH): d.line([0, y, TW, y], fill=(0, 0, 0, int(120 * ((y - TH / 2) / (TH / 2)) ** 1.6)))
    th.alpha_composite(g); D = ImageDraw.Draw(th)

    LX = 64; MAXW = 700
    fb = F("ExtraBold", 40); bw = D.textlength("SOXL 3편", font=fb) + 36   # A·B와 같은 배지
    D.rounded_rectangle([30, 22, 30 + bw, 22 + 58], 10, fill=(*PINK, 255)); D.text((30 + 18, 22 + 6), "SOXL 3편", font=fb, fill=(255, 255, 255))
    L = vn2.logo_layer(34); th.alpha_composite(L, (TW - 40 - L.width + 12, 34 - 12)); D = ImageDraw.Draw(th)

    fn = F("Bold", 46); fq = F("Heavy", 92); f1 = F("ExtraBold", 92); f2 = F("Heavy", 160)
    q1, q2 = "“역사상 가장", "중대한 기술”"; l1, l2, ul = "그런데 반도체는", "왜 -42%?", "-42%"
    for ln, f in ((q1, fq), (q2, fq), (l1, f1)):
        assert D.textlength(ln, font=f) <= MAXW, ln
    while D.textlength(l2, font=f2) > MAXW: f2 = vn2.font(os.path.basename(f2.path), f2.size - 6)

    y = 112
    D.rectangle([LX, y + 8, LX + 6, y + fn.size + 2], fill=(*PINK, 255))
    shadow_text(th, (LX + 22, y), "젠슨 황 · 엔비디아 CEO", fn, (235, 235, 235, 255)); y += fn.size + 26
    shadow_text(th, (LX, y), q1, fq, (*PINK, 255)); y += fq.size + 8
    shadow_text(th, (LX, y), q2, fq, (*PINK, 255)); y += fq.size + 44
    shadow_text(th, (LX, y), l1, f1, (255, 255, 255, 255)); y += f1.size + 10
    shadow_text(th, (LX, y), l2, f2, (255, 255, 255, 255)); D = ImageDraw.Draw(th)
    i = l2.index(ul); ux0 = LX + D.textlength(l2[:i], font=f2); ux1 = ux0 + D.textlength(ul, font=f2)
    D.rounded_rectangle([ux0, y + f2.size + 12, ux1, y + f2.size + 24], 6, fill=(*PINK, 255))
    assert y + f2.size + 24 < TH - 20, "아래로 넘침"
    th.convert("RGB").save(out, quality=92)
    print("썸네일 C", out)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "/tmp/thumb_c.jpg")
