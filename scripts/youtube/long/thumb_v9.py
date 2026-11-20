"""롱폼 썸네일 v8 (2026-11-17 대표: 큰 2줄 제목 · 핑크 밑줄 · VALUE NOTE 로고 — 클릭률 5% 미만 15편 교체본과 같은 틀)
- 어두운 실사 한 장(1280x720) · 왼쪽 정렬: 작은 머리글(흰색, 앞 4글자 아래 핑크 짧은 밑줄) → 흰 제목 1줄 → 아주 큰 흰 제목 2줄
- 2줄에서 ul 낱말 아래 핑크 굵은 밑줄 · 오른쪽 위 VALUE NOTE · 시리즈 후속편은 badge("2편") 핑크 칩
사용: python3 thumb_v8.py <spec.json> <out_dir>   (spec "thumb_v8": [{key, file, photo, kicker, l1, l2, ul, badge?, photo_side?}])
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vn2
LIB = os.path.join(HERE, "..", "..", "blog", "media", "lib")
TW, TH = 1280, 720; PINK = vn2.PINK


def _photo(name, side):
    p = os.path.join(LIB, name)
    if not os.path.exists(p):
        c = [f for f in os.listdir(LIB) if f.startswith(name + ".") and not f.endswith(".json")]
        p = os.path.join(LIB, c[0]) if c else None
    if not p: return Image.new("RGB", (TW, TH), (12, 12, 14))
    im = Image.open(p).convert("RGB"); s = max(TW / im.width, TH / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x0 = {"right": im.width - TW, "left": 0}.get(side, (im.width - TW) // 2)
    im = im.crop((x0, (im.height - TH) // 2, x0 + TW, (im.height - TH) // 2 + TH))
    im = ImageEnhance.Color(im).enhance(.55); im = ImageEnhance.Brightness(im).enhance(.78)   # 흑백 톤 쪽으로, 글자가 읽히게
    return im


def _txt(th, xy, s, f, fill=(255, 255, 255, 255)):
    lay = Image.new("RGBA", th.size, (0, 0, 0, 0)); ImageDraw.Draw(lay).text(xy, s, font=f, fill=fill)
    sh = lay.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * .75))
    o = Image.new("RGBA", th.size, (0, 0, 0, 0)); o.paste((0, 0, 0, 255), (3, 5), sh); o.alpha_composite(lay); th.alpha_composite(o)


def render(t, out):
    th = _photo(t["photo"], t.get("photo_side")).convert("RGBA")
    g = Image.new("RGBA", (TW, TH)); d = ImageDraw.Draw(g)   # 왼쪽·아래를 어둡게
    for x in range(TW): d.line([x, 0, x, TH], fill=(0, 0, 0, int(150 * max(0, 1 - x / (TW * .85)) ** 1.2)))
    th.alpha_composite(g); g = Image.new("RGBA", (TW, TH)); d = ImageDraw.Draw(g)
    for y in range(TH // 3, TH): d.line([0, y, TW, y], fill=(0, 0, 0, int(140 * ((y - TH / 3) / (TH * 2 / 3)) ** 1.4)))
    th.alpha_composite(g); D = ImageDraw.Draw(th)
    LX = 64; fk, f1 = vn2.SUIT("Heavy", 86) if os.path.exists(os.path.join(vn2.FD, "SUIT-Heavy.ttf")) else vn2.SUIT("ExtraBold", 86), vn2.SUIT("ExtraBold", 84)   # 2026-11-20 대표: 가운데 부제가 작아 안 보임(60대 시청자) — 58 Bold → 84 ExtraBold
    f2 = vn2.SUIT("Heavy", 150) if os.path.exists(os.path.join(vn2.FD, "SUIT-Heavy.ttf")) else vn2.SUIT("ExtraBold", 150)
    while D.textlength(t["l2"], font=f2) > TW - LX - 40: f2 = vn2.font(os.path.basename(f2.path), f2.size - 6)
    while D.textlength(t["kicker"], font=fk) > TW - LX - 40: fk = vn2.font(os.path.basename(fk.path), fk.size - 4)
    while D.textlength(t["l1"], font=f1) > TW - LX - 40: f1 = vn2.font(os.path.basename(f1.path), f1.size - 4)
    y2 = TH - 70 - f2.size; y1 = y2 - 30 - f1.size; yk = y1 - 18 - fk.size
    x = LX
    if t.get("badge"):
        fb = vn2.SUIT("ExtraBold", 40); bw = D.textlength(t["badge"], font=fb) + 40
        D.rounded_rectangle([x, yk - 4, x + bw, yk + fk.size + 14], 10, fill=(*PINK, 255)); D.text((x + 20, yk), t["badge"], font=fb, fill=(255, 255, 255)); x += bw + 22
    _txt(th, (x, yk), t["kicker"], fk, (*PINK, 255)); D = ImageDraw.Draw(th)
    pass
    _txt(th, (LX, y1), t["l1"], f1); _txt(th, (LX, y2), t["l2"], f2); D = ImageDraw.Draw(th)
    if t.get("ul") and t["ul"] in t["l2"]:
        i = t["l2"].index(t["ul"]); ux0 = LX + D.textlength(t["l2"][:i], font=f2); ux1 = ux0 + D.textlength(t["ul"], font=f2)
        D.rounded_rectangle([ux0, y2 + f2.size + 14, ux1, y2 + f2.size + 26], 6, fill=(*PINK, 255))
    L = vn2.logo_layer(34); th.alpha_composite(L, (TW - 40 - L.width + 12, 34 - 12))
    th.convert("RGB").save(out, quality=92)


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    dflt = next((a["file"] for a in spec.get("ab_sets", []) if a.get("default")), None)
    for t in spec.get("thumb_v8", []):
        render(t, os.path.join(out, t["file"]))
        if t["file"] == dflt: render(t, os.path.join(out, "thumb.jpg"))
        print("썸네일 v8", t["file"])
