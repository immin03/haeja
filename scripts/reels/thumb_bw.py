"""쇼츠 표지 흑백 + 핑크 (2026-11-17 대표님: 새 디자인으로 쇼츠 썸네일). python3 thumb_bw.py <spec.json> <out.jpg>
spec: {photo, tag, l1, l2, hl(밑줄 낱말), big, big_label}"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
W, H = 1080, 1920; PINK = (255, 77, 109); WH = (255, 255, 255)
def SUIT(w, s): return ImageFont.truetype(os.path.join(HERE, "fonts", f"SUIT-{w}.ttf"), s)
def fit(txt, w, size, maxw):
    while size > 40 and SUIT(w, size).getlength(txt) > maxw: size -= 4
    return SUIT(w, size)
def shadow_text(base, xy, txt, font, fill, anchor="mm"):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text(xy, txt, font=font, fill=(0, 0, 0, 200), anchor=anchor)
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10))); ImageDraw.Draw(base).text(xy, txt, font=font, fill=fill, anchor=anchor)
def render(sp, out):
    ph = Image.open(os.path.join(ROOT, "scripts", "blog", "media", "lib", sp["photo"])).convert("RGB")
    s = max(W / ph.width, H / ph.height); ph = ph.resize((int(ph.width * s) + 1, int(ph.height * s) + 1))
    ox = int((ph.width - W) * sp.get("fx", .5)); ph = ph.crop((ox, 0, ox + W, H))
    a = np.asarray(ph, np.float32); g = a.mean(2, keepdims=True); a = (a * .6 + g * .4) * 1.15
    yy = np.linspace(0, 1, H)[:, None, None]
    m = np.maximum(.18 + .62 * np.clip((yy - .42) / .40, 0, 1), .45 * np.clip((.16 - yy) / .16, 0, 1))
    a = a * (1 - np.clip(m, 0, .9)); img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # 로고
    try:
        fb, fl = ImageFont.truetype(os.path.join(HERE, "fonts", "Montserrat-ExtraBold.ttf"), 46), ImageFont.truetype(os.path.join(HERE, "fonts", "Montserrat-Light.ttf"), 46)
    except Exception:
        fb = fl = SUIT("ExtraBold", 44)
    lw = fb.getlength("VALUE") + fl.getlength("NOTE") + 8; lx = (W - lw) / 2
    d.text((lx, 150), "VALUE", font=fb, fill=WH, anchor="lm"); d.text((lx + fb.getlength("VALUE") + 8, 150), "NOTE", font=fl, fill=WH, anchor="lm")
    # 꼬리표
    ft = SUIT("ExtraBold", 54); tw = ft.getlength(sp["tag"]); ty = 1010
    d.rectangle([(W - tw) / 2, ty + 40, (W + tw) / 2, ty + 50], fill=PINK)
    shadow_text(img, (W / 2, ty), sp["tag"], ft, WH)
    f1 = fit(sp["l1"], "ExtraBold", 104, W - 120); shadow_text(img, (W / 2, 1150), sp["l1"], f1, WH)
    f2 = fit(sp["l2"], "Heavy", 168, W - 90); y2 = 1330
    if sp.get("hl") and sp["hl"] in sp["l2"]:
        pre = sp["l2"][:sp["l2"].index(sp["hl"])]; tw2 = f2.getlength(sp["l2"]); x0 = (W - tw2) / 2 + f2.getlength(pre)
        ImageDraw.Draw(img).rounded_rectangle([x0, y2 + 70, x0 + f2.getlength(sp["hl"]), y2 + 92], 11, fill=PINK)
    shadow_text(img, (W / 2, y2), sp["l2"], f2, WH)
    if sp.get("big"):
        shadow_text(img, (W / 2, 1560), sp["big"], SUIT("Heavy", 150), PINK)
        if sp.get("big_label"): shadow_text(img, (W / 2, 1680), sp["big_label"], fit(sp["big_label"], "SemiBold", 40, W - 140), (225, 225, 228))
    img.convert("RGB").save(out, quality=92)
if __name__ == "__main__":
    render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
