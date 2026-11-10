"""The Emperor's Diary (EN) — type-system samples for the owner (2026-11-11). Renders the same 4 frames (1920x1080) per font system:
 1 subtitle (2 lines)  2 Meditations quote card  3 summary title screen  4 ending card (with the sincere subscribe line)
and one contact sheet per system. Backgrounds = real scene stills of the episode + the same grade/letterbox as the render.
python3 type_samples.py <out_dir>    env ED_SAMPLE_FONTS = folder with fs_* (fontsource woff) + Cinzel-*.ttf
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import longform_en as LE
M = LE.load()
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
GEN = os.path.join(ROOT, "social/side/gen"); LOGO = os.path.join(ROOT, "docs/emperor/profile_final.png")
FD = os.environ.get("ED_SAMPLE_FONTS", "/root/fonts")
W, H, BAR = 1920, 1080, 131
GOLD = (214, 178, 108); IVORY = (244, 236, 220); DIM = (224, 212, 190)
E = json.load(open(os.path.join(HERE, "cine_ep01_en.json")))
ENDING = json.load(open(os.path.join(HERE, "ending_text_options.json")))


def F(path, size):
    return ImageFont.truetype(os.path.join(FD, path), size)


# ---- three font systems (all SIL OFL) ----
SYSTEMS = {
 "a_epic": dict(name="(a) Epic trailer — Cinzel + EB Garamond",
     title=("Cinzel-SemiBold.ttf", 54, 0.10), kicker=("Cinzel-SemiBold.ttf", 26, 0.42),
     sub=("fs_eb-garamond/eb-garamond-latin-500-normal.woff", 50), quote=("fs_eb-garamond/eb-garamond-latin-500-italic.woff", 66),
     cite=("Cinzel-SemiBold.ttf", 24, 0.36), item=("fs_eb-garamond/eb-garamond-latin-500-normal.woff", 52), num=("Cinzel-SemiBold.ttf", 40, 0.05),
     slogan=("fs_eb-garamond/eb-garamond-latin-500-italic.woff", 56), brand=("Cinzel-SemiBold.ttf", 34, 0.34), small=("fs_eb-garamond/eb-garamond-latin-400-italic.woff", 36)),
 "b_prestige": dict(name="(b) Prestige documentary — Cormorant Garamond",
     title=("fs_cormorant/cormorant-garamond-latin-500-normal.woff", 64, 0.02), kicker=("CormorantSC-SemiBold.ttf", 28, 0.40),
     sub=("fs_cormorant/cormorant-garamond-latin-600-normal.woff", 56), quote=("fs_cormorant/cormorant-garamond-latin-500-italic.woff", 76),
     cite=("CormorantSC-SemiBold.ttf", 28, 0.30), item=("fs_cormorant/cormorant-garamond-latin-500-normal.woff", 58), num=("CormorantSC-SemiBold.ttf", 46, 0.04),
     slogan=("fs_cormorant/cormorant-garamond-latin-500-italic.woff", 64), brand=("CormorantSC-SemiBold.ttf", 38, 0.30), small=("fs_cormorant/cormorant-garamond-latin-500-italic.woff", 40)),
 "c_caslon": dict(name="(c) American classic — Libre Caslon",
     title=("fs_libre-caslon-display/libre-caslon-display-latin-400-normal.woff", 62, 0.01), kicker=("fs_libre-caslon-text/libre-caslon-text-latin-700-normal.woff", 22, 0.42),
     sub=("fs_libre-caslon-text/libre-caslon-text-latin-400-normal.woff", 44), quote=("fs_libre-caslon-text/libre-caslon-text-latin-400-italic.woff", 56),
     cite=("fs_libre-caslon-text/libre-caslon-text-latin-700-normal.woff", 21, 0.38), item=("fs_libre-caslon-text/libre-caslon-text-latin-400-normal.woff", 46), num=("fs_libre-caslon-display/libre-caslon-display-latin-400-normal.woff", 46, 0.04),
     slogan=("fs_libre-caslon-text/libre-caslon-text-latin-400-italic.woff", 50), brand=("fs_libre-caslon-text/libre-caslon-text-latin-700-normal.woff", 28, 0.36), small=("fs_libre-caslon-text/libre-caslon-text-latin-400-italic.woff", 32)),
}


def scene(src, dark=0.0):
    im = cv2.imread(os.path.join(GEN, src)); im = cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)
    out = M.Look().apply(im)
    if dark: out = (out.astype(np.float32) * (1 - dark)).astype(np.uint8)
    return Image.fromarray(out[..., ::-1])


def warm():
    return Image.fromarray(M.warm_bg({}, 540)[..., ::-1])


def tw(d, s, f, track=0.0):
    if not track: return d.textlength(s, font=f)
    return sum(d.textlength(c, font=f) for c in s) + track * f.size * (len(s) - 1)


def put(img, x_center, y, s, f, col, track=0.0, shadow=0.75, blur=8, anchor="center"):
    """draw one line, horizontally centred, with a soft shadow (no boxes)"""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w = tw(d, s, f, track); x = x_center - w / 2 if anchor == "center" else x_center
    def draw(dd, xx, yy, fill):
        if not track: dd.text((xx, yy), s, font=f, fill=fill); return
        for c in s: dd.text((xx, yy), c, font=f, fill=fill); xx += dd.textlength(c, font=f) + track * f.size
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); draw(ImageDraw.Draw(sh), x, y + 3, (0, 0, 0, int(255 * shadow)))
        lay = Image.alpha_composite(lay, sh.filter(ImageFilter.GaussianBlur(blur)))
        d = ImageDraw.Draw(lay)
    draw(d, x, y, col + (255,))
    return Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB"), w


def wrap(d, text, f, maxw):
    words = text.split(); lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f) > maxw and cur: lines.append(cur); cur = w_
        else: cur = t
    lines.append(cur)
    if len(lines) == 2:   # balance two lines, prefer a break after punctuation
        best, bc = lines, 9e9
        for i in range(1, len(words)):
            a, b = " ".join(words[:i]), " ".join(words[i:]); wa, wb = d.textlength(a, font=f), d.textlength(b, font=f)
            if max(wa, wb) > maxw: continue
            c = abs(wa - wb) - (200 if a.endswith((",", ".", "?", ";")) else 0)
            if c < bc: best, bc = [a, b], c
        lines = best
    return lines


def bottom_vignette(img, strength=0.45):
    a = np.asarray(img).astype(np.float32); yy = np.linspace(0, 1, H)[:, None, None]
    k = 1 - strength * np.clip((yy - 0.62) / 0.26, 0, 1) ** 1.5
    return Image.fromarray(np.clip(a * k, 0, 255).astype(np.uint8))


def f_subtitle(S):
    img = bottom_vignette(scene("cep1i_ride.jpeg"))
    f = F(*S["sub"][:2]); d = ImageDraw.Draw(img)
    lines = wrap(d, "Ten years earlier, one general's name was spreading along Rome's eastern frontier.", f, 1380)
    lh = int(f.size * 1.32); y = H - BAR - 44 - lh * len(lines)
    for i, s in enumerate(lines): img, _ = put(img, W / 2, y + i * lh, s, f, IVORY, shadow=0.9, blur=7)
    return img


def f_quote(S):
    img = scene("cep1i_diary.jpeg", dark=0.45)
    a = np.asarray(img).astype(np.float32); yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.35 * np.exp(-(((xx - W / 2) / 700) ** 2 + ((yy - H / 2) / 260) ** 2)); img = Image.fromarray(np.clip(a * v[..., None], 0, 255).astype(np.uint8))
    fq = F(*S["quote"][:2]); fc = F(*S["cite"][:2]); d = ImageDraw.Draw(img)
    lines = ["“The best way to avenge yourself", "is not to become like the wrongdoer.”"]
    lh = int(fq.size * 1.28); y = H / 2 - lh * len(lines) / 2 - 40
    for i, s in enumerate(lines): img, _ = put(img, W / 2, y + i * lh, s, fq, IVORY, shadow=0.85, blur=10)
    yc = y + lh * len(lines) + 34
    d = ImageDraw.Draw(img); d.line([(W / 2 - 40, yc - 10), (W / 2 + 40, yc - 10)], fill=GOLD, width=1)
    img, _ = put(img, W / 2, yc + 6, "MARCUS AURELIUS  ·  MEDITATIONS VI.6", fc, GOLD, track=S["cite"][2], shadow=0.6)
    return img


def f_summary(S):
    img = warm(); fk = F(*S["kicker"][:2]); ft = F(*S["title"][:2]); fi = F(*S["item"][:2]); fn = F(*S["num"][:2])
    title = E["screens"]["recap"]["head"]
    caps = S["title"][0].startswith("Cinzel"); t = title.upper() if caps else title
    d = ImageDraw.Draw(img)
    tl = [t] if tw(d, t, ft, S["title"][2]) <= 1440 else wrap(d, t, ft, tw(d, t, ft, S["title"][2]) * 0.6)   # title-safe width (75%)
    lh_t = int(ft.size * 1.22); items = E["screens"]["recap"]["items"]; lh_i = int(fi.size * 1.75)
    block = 40 + len(tl) * lh_t + 70 + len(items) * lh_i; y0 = (H - block) / 2
    img, _ = put(img, W / 2, y0, "THE EMPEROR\u2019S ANSWER", fk, GOLD, track=S["kicker"][2], shadow=0)
    for i, x in enumerate(tl): img, _ = put(img, W / 2, y0 + 44 + i * lh_t, x, ft, IVORY, track=S["title"][2], shadow=0.5)
    yr = y0 + 44 + len(tl) * lh_t + 22
    d = ImageDraw.Draw(img); d.line([(W / 2 - 60, yr), (W / 2 + 60, yr)], fill=GOLD, width=1)
    ws = [d.textlength(x, font=fi) for x in items]; colx = (W - (max(ws) + 110)) / 2
    for i, x in enumerate(items):
        y = yr + 48 + i * lh_i; d = ImageDraw.Draw(img)
        d.text((colx + 70, y + fi.size * 0.12), ["I", "II", "III"][i], font=fn, fill=GOLD, anchor="ra")
        img, _ = put(img, colx + 110, y, x, fi, IVORY, shadow=0.4, anchor="left")
    return img


def f_ending(S, end_key="A"):
    img = warm(); coin = M.coin_gold(LOGO); c = Image.fromarray(coin, "RGBA").resize((170, 170), Image.LANCZOS)
    img = img.convert("RGBA"); img.alpha_composite(c, (W // 2 - 85, 168)); img = img.convert("RGB")
    fs = F(*S["slogan"][:2]); fb = F(*S["brand"][:2]); fsm = F(*S["small"][:2])
    img, _ = put(img, W / 2, 370, "Think like an emperor, every night.", fs, IVORY, shadow=0.4)
    img, _ = put(img, W / 2, 370 + int(fs.size * 1.45), "THE EMPEROR’S DIARY", fb, GOLD, track=S["brand"][2], shadow=0)
    # sincere line, centred, max 2 lines, generous leading
    d = ImageDraw.Draw(img); txt = ENDING[end_key]["screen"]
    lines = wrap(d, txt, fsm, 1240); lh = int(fsm.size * 1.4); y = 560
    for i, s in enumerate(lines): img, _ = put(img, W / 2, y + i * lh, s, fsm, DIM, shadow=0)
    # buttons (right of centre) — the left lower area stays empty for the YouTube end-screen video element
    yb = y + lh * len(lines) + 46; fbt = F(*S["cite"][:2])
    d = ImageDraw.Draw(img)
    for j, lab in enumerate(["SUBSCRIBE", "LIKE"]):
        bw = tw(d, lab, fbt, S["cite"][2]) + 84; cx = W / 2 + (j - 0.5) * 330
        d.rounded_rectangle([cx - bw / 2, yb, cx + bw / 2, yb + 62], radius=31, outline=GOLD, width=2, fill=(30, 24, 16) if j else (214, 178, 108))
        img, _ = put(img, cx, yb + 31 - fbt.size * 0.62, lab, fbt, (24, 18, 10) if j == 0 else GOLD, track=S["cite"][2], shadow=0)
        d = ImageDraw.Draw(img)
    return img


def sheet(frames, title, out):
    tw_, th_ = 960, 540; s = Image.new("RGB", (tw_ * 2 + 30, th_ * 2 + 110), (14, 14, 16)); d = ImageDraw.Draw(s)
    d.text((16, 22), title, font=ImageFont.truetype(os.path.join(FD, "Inter-SemiBold.ttf"), 34), fill=(230, 220, 200))
    for i, fr in enumerate(frames): s.paste(fr.resize((tw_, th_), Image.LANCZOS), (10 + (i % 2) * (tw_ + 10), 90 + (i // 2) * (th_ + 10)))
    s.save(out, quality=92)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "_samples"; os.makedirs(out, exist_ok=True)
    for k, S in SYSTEMS.items():
        fr = [f_subtitle(S), f_quote(S), f_summary(S), f_ending(S, "A")]
        for i, x in enumerate(fr, 1): x.save(os.path.join(out, f"type_{k}_{i}.png"))
        sheet(fr, S["name"], os.path.join(out, f"type_{k}_sheet.jpg")); print(k)
    S = SYSTEMS["b_prestige"]; f_ending(S, "B").save(os.path.join(out, "ending_B_in_b_prestige.png"))
