"""황제의 일기 쇼츠 표지(썸네일) — 2026-11-13 대표 확정 배치.
대표 00:52 "가운데에다 크게 써주고 그 다음에 명상록을 크게 꽉 채워서 둘 다" · 00:54 "밑줄은 빼고 명상록만 깔끔하게, 한글·영어 다".
배경 = 그 편 첫 장면 클립(fx_<id>.json 첫 샷)의 깨끗한 프레임(글자 없음). 새 그림을 만들지 않는다.
글 = 화면 가운데에 제목 두 줄(윗줄 아이보리, 아랫줄 샴페인 금빛) + 그 아래 「명상록」(영어 MEDITATIONS). 테두리 없음, 부드러운 그림자만.
제목 = long_<id>.json 의 cover(있으면) → hook 을 두 줄로. 한 줄이 너무 길면 글자 크기를 줄인다(가로 94%).
사용: python3 cover_ed.py <id> [out.jpg]      (scripts/side/emperor 에서, ED_LANG=en 이면 영어)
결과: docs/emperor/ep/cover_<id>.jpg (영어는 docs/emperor/en/cover_<id>.jpg) — 「쇼츠 썸네일 고정」 크롬 작업이 이 파일을 스튜디오에 올린다.
"""
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
W, H = 1080, 1920
IVORY, CHAMP = (255, 253, 247), (238, 196, 126)   # 11/13 01:01 대표: 제목은 전부 흰색 한 가지, 금빛은 「명상록」과 양옆 선에만 (색이 오가면 어지럽다)
LANG = os.environ.get("ED_LANG", "ko")
FD = "/root/fonts/"; EF = os.path.join(HERE, "en", "fonts") + "/"


def font(sz):
    if LANG == "en":
        f = ImageFont.truetype(EF + "Cinzel-SemiBold.ttf" if os.path.exists(EF + "Cinzel-SemiBold.ttf") else FD + "Cinzel-SemiBold.ttf", sz)
    else:
        f = ImageFont.truetype(FD + "Pretendard-ExtraBold.otf", sz)
    return f


def frame(clip, cx, t=0.4):
    from clip_fetch import ensure
    path = ensure(os.path.join(ROOT, "social/side/gen", clip + ".mp4"))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", path, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    import io
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    k = H / im.height * 1.06; im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    x = int(min(max(cx * im.width - W / 2, 0), im.width - W)); y = (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H))
    im = ImageEnhance.Contrast(im).enhance(1.06); im = ImageEnhance.Color(im).enhance(1.05)
    return ImageEnhance.Brightness(im).enhance(0.85)


def two_lines(spec):
    if spec.get("cover"): return spec["cover"][:2]
    h = [x.strip() for x in spec["hook"] if x.strip()]
    if len(h) == 2: return h
    words = " ".join(h).split(); best = None
    for i in range(1, len(words)):   # 두 줄 길이가 가장 비슷하게
        a, b = " ".join(words[:i]), " ".join(words[i:]); d = abs(len(a) - len(b))
        if best is None or d < best[0]: best = (d, a, b)
    return [best[1], best[2]]


def split_best(text, f, d, maxw):
    """글자를 크게 두려고 2~4줄로 나눈다: 가장 적은 줄 수로 가로 92% 안에 들게, 안 되면 가장 긴 줄이 가장 짧은 쪽"""
    w = text.split(); best = None
    import itertools
    for k in (2, 3, 4):
        if k > len(w): break
        for cut in itertools.combinations(range(1, len(w)), k - 1):
            ls = [" ".join(w[a:b]) for a, b in zip((0,) + cut, cut + (len(w),))]
            m = max(d.textlength(l, font=f) for l in ls)
            if best is None or (m <= maxw and (best[0] > maxw or k < best[2] or (k == best[2] and m < best[0]))) or (best[0] > maxw and m < best[0]):
                best = (m, ls, k)
        if best[0] <= maxw: break
    return best[1]


def make(cid, out=None):
    spec = json.load(open(os.path.join(HERE, f"long_{cid}.json")))
    fx = json.load(open(os.path.join(HERE, f"fx_{cid}.json")))
    clip, cx = fx["shots"][0][0][0], fx["shots"][0][0][1]
    im = frame(clip, cx)
    text = " ".join(spec["cover"]) if spec.get("cover") else spec.get("title_line") or " ".join(spec["hook"])
    if LANG == "en": text = text.upper()
    else:
        for w in ("진짜 ", "절대 ", "정말 "): text = text.replace(w, "") if len(text.replace(" ", "")) > 14 else text
    sub = "MEDITATIONS" if LANG == "en" else "명상록"
    yc = 1000
    a = np.exp(-((np.arange(H) - yc) / 420.0) ** 2) * 0.6
    im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, Image.fromarray((np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)))
    d = ImageDraw.Draw(im)
    base = 150 if LANG != "en" else 124; maxw = W * 0.92
    lines = [x.upper() if LANG == "en" else x for x in spec["cover"]] if spec.get("cover") else split_best(text, font(base), d, maxw)   # cover = 사람이 끊은 줄(2~3줄, 뜻 단위). 없을 때만 자동
    # 11/13 00:57 대표: 줄마다 같은 크기(두 줄, 안 되면 세 줄), 골드는 꼭 필요한 곳에만({…} 표시), 밑줄 없음, 「명상록」 양옆 선은 둔다
    cap = 150 if LANG != "en" else 124
    plain = [re.sub(r"[{}]", "", l) for l in lines]
    sz = cap
    while max(d.textlength(l, font=font(sz)) for l in plain) > maxw: sz -= 3
    f = font(sz); fs = font(96 if LANG != "en" else 84); lh = int(sz * 1.2)
    total = lh * len(lines) + 46 + fs.size
    y = yc - total // 2; items = []   # (segments[(text, colour)], font, y)
    for l in lines:
        segs = [(re.sub(r"[{}]", "", l), IVORY)]
        if "{" not in l and len(lines) == 1: segs = [(l, CHAMP)]
        items.append((segs, f, y)); y += lh
    items.append(([(sub, CHAMP)], fs, y + 46)); sub_y = y + 46
    def draw(dr, colour=None):
        for segs, ff, yy in items:
            x = (W - dr.textlength("".join(t for t, _ in segs), font=ff)) / 2
            for t, c in segs: dr.text((x, yy), t, font=ff, fill=colour if colour is not None else c); x += dr.textlength(t, font=ff)
    sh = Image.new("L", (W, H), 0); draw(ImageDraw.Draw(sh), 255)
    im.paste((0, 0, 0), (0, 6), sh.filter(ImageFilter.GaussianBlur(24)).point(lambda v: min(255, int(v * 1.5))))
    d = ImageDraw.Draw(im); draw(d)
    tw = d.textlength(sub, font=fs); cy = sub_y + int(fs.size * 0.62)   # 「명상록」 양옆 가는 금빛 선
    d.line([(W / 2 - tw / 2 - 170, cy), (W / 2 - tw / 2 - 36, cy)], fill=CHAMP, width=4); d.line([(W / 2 + tw / 2 + 36, cy), (W / 2 + tw / 2 + 170, cy)], fill=CHAMP, width=4)
    out = out or os.path.join(ROOT, "docs/emperor", "en" if LANG == "en" else "ep", f"cover_{cid}.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True); im.save(out, quality=92)
    return out


if __name__ == "__main__":
    print(make(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
