"""2026-11-16 대표: 경쟁 채널 벤치마킹 새 썸네일 레이아웃 3종 (밸류노트 색: 네이비 + 골드)
  doc     : Just In Time 결 — 어두운 실사 인물 크게(오른쪽), 왼쪽 골드 인용부호 + 작은 흰 줄 + 큰 골드 줄
  versus  : 월가 스케치·에디 결 — 인물 2~3명 + 라벨 칩, 가운데 VS/?, 아래 큰 두 줄
  chips   : 월가 스케치 결 — 왼쪽 위 숫자 칩 2개, 오른쪽 인물, 왼쪽 큰 헤드라인({}는 골드 강조)
사용: python3 thumb_v6.py <설정.json> <출력.jpg>"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__)); LIB = os.path.join(HERE, "..", "blog", "media", "lib")
W, H = 1280, 720; GOLD = (242, 212, 151); NAVY = (13, 27, 52); WHITE = (246, 241, 232); RED = (255, 77, 109); TINT_RED = (178, 64, 72); BLUE = (52, 86, 150)   # 밸류노트 톤: 네이비 + 아이보리 + 골드 (형광색은 숫자 업다운에만)
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, HERE)
def F(w, s): return ImageFont.truetype(os.path.join(HERE, "fonts", f"SUIT-{w}.ttf"), s)
def load(p): return Image.open(p if os.path.isabs(p) else os.path.join(LIB, p)).convert("RGB")
def cover(im, w, h, fx=.5, fy=.4):
    s = max(w / im.width, h / im.height); im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = int((im.width - w) * fx); y = int((im.height - h) * fy); return im.crop((x, y, x + w, y + h))
def grade(im, dark=.78, sat=.85): return ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(dark)).enhance(sat)
def segs(line):   # "{강조}" → [(글자, 강조여부)]
    return [(t, i % 2 == 1) for i, t in enumerate(re.split(r"[{}]", line)) if t]
SHADOWS = []
def text(d, xy, line, size, base=WHITE, hi=GOLD, w="Heavy", stroke=0, anchor="ls"):
    x, y = xy; f = F("Heavy", size)
    if anchor == "ms": x -= sum(d.textlength(t, font=f) for t, _ in segs(line)) / 2
    for t, h in segs(line):
        SHADOWS.append((x, y, t, f)); d.text((x, y), t, font=f, fill=hi if h else base, anchor="ls"); x += d.textlength(t, font=f)
def shadowed(im, draw_fn):
    """글자를 한 번 그려 위치를 모은 뒤, 그림자 층을 깔고 다시 그린다"""
    SHADOWS.clear(); tmp = im.copy(); draw_fn(tmp)
    sh = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(sh)
    for x, y, t, f in SHADOWS: sd.text((x + 3, y + 5), t, font=f, fill=200, anchor="ls")
    sh = sh.filter(ImageFilter.GaussianBlur(9)); im.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), sh); draw_fn(im); return im
def fit(d, line, size, maxw, w="Heavy"):
    while size > 40 and sum(d.textlength(t, font=F(w, size)) for t, _ in segs(line)) > maxw: size -= 4
    return size
def logo(d): pass
def brand_logo(im):
    from brand import paste_logo
    paste_logo(im, W - 36, 28, 30, "dark", align="right")
def grad_left(im, to=.62, a0=245):
    g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g)
    for x in range(W): gd.line([x, 0, x, H], fill=int(a0 * max(0, 1 - x / (W * to)) ** 1.1))
    im.paste(Image.new("RGB", (W, H), NAVY), (0, 0), g)
def soft_paste(im, ph, x, fade=.5, top_fade=0):
    """사진 왼쪽 가장자리를 부드럽게(코사인 곡선) 네이비로 녹인다 — 경계선이 안 보이게"""
    import math
    m = Image.new("L", ph.size, 255); md = ImageDraw.Draw(m); fw = int(ph.width * fade)
    for i in range(fw): md.line([i, 0, i, ph.height], fill=int(255 * (1 - math.cos(math.pi * i / fw)) / 2))
    im.paste(ph, (x, 0), m)
def grad_bottom(im, frm=.45, a0=250):
    g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g)
    for y in range(H): gd.line([0, y, W, y], fill=int(a0 * max(0, (y / H - frm) / (1 - frm)) ** 1.2))
    im.paste(Image.new("RGB", (W, H), NAVY), (0, 0), g)
def quote_mark(d, x, y, s=70):
    for k in (0, 1):
        cx = x + k * s * .62; d.ellipse([cx, y + s * .38, cx + s * .46, y + s * .84], fill=GOLD)
        d.polygon([(cx + s * .05, y + s * .55), (cx + s * .30, y), (cx + s * .42, y + s * .05), (cx + s * .30, y + s * .55)], fill=GOLD)
def chip(d, x, y, t, bg=GOLD, fg=NAVY, size=34):
    f = F("Heavy", size); w = d.textlength(t, font=f)
    d.rounded_rectangle([x, y, x + w + 40, y + size + 26], 12, fill=bg); d.text((x + 20, y + 10), t, font=f, fill=fg); return x + w + 36

def doc(c):
    im = Image.new("RGB", (W, H), NAVY); pw = int(W * c.get("pw", .64))
    ph = grade(cover(load(c["photo"]), pw, H, *c.get("focus", [.5, .3])), .9)
    soft_paste(im, ph, W - pw, .24); grad_bottom(im, .78, 110); d = ImageDraw.Draw(im)
    L2 = c["l2"].split("\n"); s2 = min(fit(d, "{" + l + "}", 112, 640) for l in L2); s1 = fit(d, c["l1"], 58, 620, "ExtraBold")
    y = H - 70 - (len(L2) - 1) * (s2 + 10)
    HI = RED if c.get("pink", True) else GOLD
    text(d, (64, y - s2 - 28), c["l1"], s1, hi=WHITE); quote_mark(d, 64, y - s2 - s1 - 120, 60)
    for l in L2: text(d, (64, y), "{" + l + "}", s2, hi=HI); y += s2 + 10
    if c.get("tag"): chip(d, 60, 60, c["tag"], HI, NAVY, 46)
    return im

def versus(c):
    im = Image.new("RGB", (W, H), NAVY); ps = c["photos"]; n = len(ps); cw = W // n
    for i, p in enumerate(ps):
        ph = grade(cover(load(p["photo"]), cw, H, *p.get("focus", [.5, .25])), .85)
        if p.get("tint"):
            t = Image.new("RGB", ph.size, BLUE if p["tint"] == "blue" else TINT_RED); ph = Image.blend(ph, t, .2)
        im.paste(ph, (i * cw, 0))
    d = ImageDraw.Draw(im)
    for i in range(1, n): d.line([i * cw, 0, i * cw, H], fill=NAVY, width=6)
    grad_bottom(im, .38, 252); d = ImageDraw.Draw(im)
    for i, p in enumerate(ps):
        if p.get("label"):
            f = F("Heavy", 44); w = d.textlength(p["label"], font=f); x = i * cw + (cw - w - 36) / 2
            chip(d, x, 120, p["label"], WHITE if p.get("tint") == "red" else GOLD, NAVY, 44)
    if c.get("mid"):
        f = F("Heavy", 96); d.text((W / 2, 300), c["mid"], font=f, fill=GOLD, anchor="mm", stroke_width=6, stroke_fill=NAVY)
    s1 = fit(d, c["l1"], 56, W - 120, "ExtraBold"); text(d, (W / 2, 548), c["l1"], s1, hi=GOLD, anchor="ms")
    s2 = fit(d, "{" + c["l2"] + "}", 110, W - 100); text(d, (W / 2, 670), "{" + c["l2"] + "}", s2, hi=RED, anchor="ms")
    logo(d); return im

def chips(c):
    im = Image.new("RGB", (W, H), NAVY); phs = c.get("photos") or [{"photo": c["photo"], "focus": c.get("focus", [.5, .3])}]
    pw = int(W * c.get("pw", .64)); cw = pw // len(phs); strip = Image.new("RGB", (pw, H), NAVY)
    for i, p in enumerate(phs): strip.paste(grade(cover(load(p["photo"]), cw, H, *p.get("focus", [.5, .3])), .9), (i * cw, 0))
    if len(phs) > 1:
        sd = ImageDraw.Draw(strip)
        for i in range(1, len(phs)): sd.line([i * cw, 0, i * cw, H], fill=NAVY, width=6)
    soft_paste(im, strip, W - pw, .16); grad_bottom(im, .52, 235); d = ImageDraw.Draw(im)
    y = 64
    for i, t in enumerate(c.get("chips", [])): chip(d, 56, y, t, RED if i == 0 else WHITE, NAVY, 46); y += 90
    lines = c["head"]; s = min(fit(d, l, c.get("size", 132), c.get("maxw", 880)) for l in lines); y = H - 58 - (len(lines) - 1) * (s + 12)
    for l in lines: text(d, (56, y), l, s, hi=RED if c.get("hi_red") else GOLD); y += s + 12
    return im

if __name__ == "__main__":
    c = json.load(open(sys.argv[1], encoding="utf-8")); im = {"doc": doc, "versus": versus, "chips": chips}[c["layout"]](c); brand_logo(im); im = im.convert("RGB")
    im.save(sys.argv[2], quality=92); print("→", sys.argv[2])
