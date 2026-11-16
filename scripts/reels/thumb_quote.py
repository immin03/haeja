"""큰따옴표 인용형 썸네일 (2026-11-16 대표님: "요즘 이런 게 잘된다" — 월가 스케치 '왜 지금 젠슨황을 죽이는가' 참고).
왼쪽: 초록 큰따옴표 + 아주 큰 두세 줄 (강조 단어는 초록, 나머지 흰색) / 오른쪽: 인물·장면 사진이 어둡게 번져 들어온다.
  python3 scripts/reels/thumb_quote.py <설정.json> <출력.jpg>
설정: {"format": "long"|"short", "lines": ["왜 지금", "{젠슨 황}을", "다시 부르나"], "photo": "lib 파일명 또는 경로", "photo2": 선택, "focus_x": 0.5}
  {...} 안은 초록, 밖은 흰색. 첫 줄은 통째로 초록으로 하고 싶으면 "{왜 지금}".
"""
import json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LIB = os.path.join(ROOT, "scripts", "blog", "media", "lib")
GREEN = (40, 230, 150); WHITE = (255, 255, 255); BG = (6, 10, 18)


def F(s): return ImageFont.truetype(os.path.join(HERE, "fonts", "SUIT-Heavy.ttf"), s)


def load(p):
    q = p if os.path.isabs(p) or os.path.exists(p) else os.path.join(LIB, p)
    return Image.open(q).convert("RGB")


def cover(im, w, h, fx=.5):
    s = max(w / im.width, h / im.height); im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    l = int((im.width - w) * fx); t = (im.height - h) // 2; return im.crop((l, t, l + w, t + h))


def tint(p, cfg):
    """versus: 사진을 왼쪽 파랑 | 오른쪽 빨강으로 물들이고 위쪽에 '민주당 VS 공화당'"""
    if not cfg.get("versus"): return p
    a = np.asarray(p, np.float32); w, h = p.size; xx = np.arange(w)[None, :, None]
    k = np.clip((xx - w * .5) / (w * .08) + .5, 0, 1)   # 가운데에서 부드럽게 바뀐다
    col = np.array([30, 80, 220], np.float32) * (1 - k) + np.array([220, 40, 45], np.float32) * k
    a = a * .5 + col * .5; p = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(p)
    L_, R_ = cfg["versus"]; fs = max(40, int(w * .085)); y = int(h * (.84 if h < w * 1.2 else .14))
    d.text((w * (.36 if h < w else .27), y), L_, font=F(fs), fill=(255, 255, 255), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    d.text((w * .76, y), R_, font=F(fs), fill=(255, 255, 255), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    d.text((w * (.56 if h < w else .515), y), "VS", font=F(int(fs * 1.15)), fill=(255, 214, 90), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
    return p


def segs(line):
    out = []
    for part in re.split(r"(\{[^}]*\})", line):
        if not part: continue
        out.append((part[1:-1], GREEN) if part.startswith("{") else (part, WHITE))
    return out


def make(cfg, out):
    long_ = cfg.get("format", "long") == "long"
    W, H = (1280, 720) if long_ else (1080, 1920)
    im = Image.new("RGB", (W, H), BG)
    # 사진: 가로형은 오른쪽 60%, 세로형은 위쪽 62%
    if long_:
        pw = int(W * .62); ph = load(cfg["photo"]); p = tint(cover(ph, pw, H, cfg.get("focus_x", .5)), cfg); im.paste(p, (W - pw, 0))
        if cfg.get("photo2"):
            p2 = cover(load(cfg["photo2"]), int(pw * .45), H, cfg.get("focus2_x", .5)); im.paste(p2, (W - p2.width, 0))
        a = np.asarray(im, np.float32); xx = np.arange(W)[None, :, None]
        k = np.clip((xx - (W - pw)) / (pw * .45), 0, 1) ** 1.1; a = a * k + np.array(BG, np.float32) * (1 - k)
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        x0, y0, size, gap = 52, 120, 118, 8; qsize = 120
    else:
        ph_h = int(H * .62); p = tint(cover(load(cfg["photo"]), W, ph_h, cfg.get("focus_x", .5)), cfg); im.paste(p, (0, 0))
        a = np.asarray(im, np.float32); yy = np.arange(H)[:, None, None]
        k = np.clip((ph_h - yy) / (ph_h * .35), 0, 1); a = a * k + np.array(BG, np.float32) * (1 - k)
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        x0, y0, size, gap = 70, int(H * .50), 168, 12; qsize = 170
    d = ImageDraw.Draw(im)
    s = qsize * .55; qy = y0 - s * 1.25   # 큰따옴표를 직접 그린다 (글꼴의 따옴표는 너무 작다)
    for i in range(2):
        cx = x0 + i * s * .62 + s * .24; cy = qy + s * .66; r = s * .22
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
        d.polygon([(cx - r * .95, cy - r * .1), (cx + r * .05, qy), (cx + r * .55, qy + s * .08), (cx + r * .2, cy - r * .6)], fill=GREEN)
    y = y0 + size * .35
    maxw = (W * .52 if long_ else W - 2 * x0)
    for line in cfg["lines"]:
        s_ = size
        while True:
            f = F(s_); tw = sum(d.textlength(t, font=f) for t, _ in segs(line))
            if tw <= maxw or s_ < 60: break
            s_ -= 4
        x = x0
        for t, col in segs(line):
            # 글자 가장자리 어둡게 (사진 위에서도 읽히게)
            d.text((x, y + s_), t, font=f, fill=col, anchor="ls", stroke_width=max(2, s_ // 30), stroke_fill=(0, 0, 0))
            x += d.textlength(t, font=f)
        y += s_ + gap
    if cfg.get("sub"):   # 작은 한 줄 (예: 그 뒤 베일에 싸인 잔혹한 전쟁)
        fs = int(size * .42); f = F(fs)
        while d.textlength(cfg["sub"], font=f) > maxw and fs > 24: fs -= 2; f = F(fs)
        d.rectangle([x0, y + 14, x0 + d.textlength(cfg["sub"], font=f) + 24, y + 14 + fs + 22], fill=(200, 40, 48))
        d.text((x0 + 12, y + 14 + fs + 6), cfg["sub"], font=f, fill=WHITE, anchor="ls")
    im.save(out, quality=92); print("→", out)


if __name__ == "__main__":
    make(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
