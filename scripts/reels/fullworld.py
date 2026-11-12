"""꽉 찬 그림 장면 (2026-11-01 14:06 대표님 결정 'A안': 쇼츠·릴스도 그림이 화면을 꽉 채우게)

opt-in: 장면에 "full": {...} 이 있을 때만 쓴다(없으면 지금 화면 그대로). 장면 type(hook·photo·cta 등)은 길이·마무리 계산에만 쓰이고 그림은 그리지 않는다.
  "full": {"img": "<scripts/blog/media/lib 파일>", "label": "왼쪽 위 종이 라벨 한 줄(명사형)",
           "num": "펜 숫자(선택)", "num_line": 0, "num_frac": .3, "tone": "loss|ink|gold", "focus_x": .5, "focus_y": .5}
화면: 위 제목 띠(배너, draw_banner_soft) 그대로 · 그 아래 화면 끝까지 그림·영상이 꽉 참(사진은 켄 번즈, 2026-11-05) · 왼쪽 위 아이보리 종이 라벨 + 펜 숫자·금색 밑줄 ·
      자막은 아래쪽 어두운 그라데이션 위. 펜 동그라미로 그림을 가리지 않는다. 장면이 바뀔 때 0.35초 겹쳐 넘어간다.
"""
import os
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONTS = os.path.join(os.path.dirname(__file__), "fonts")
XF = .35
PAPER = (246, 240, 226); INK = (24, 38, 66); RED = (196, 52, 60); GOLD = (214, 172, 84)
TONES = {"loss": RED, "ink": INK, "gold": (168, 122, 36), "good": (40, 128, 86)}
_C = {}


def _img(name):
    if name not in _C:
        p = name if os.path.isabs(name) else os.path.join(ROOT, "scripts", "blog", "media", "lib", name)
        _C[name] = Image.open(p).convert("RGB")
    return _C[name]


def _grad():
    if "g" not in _C:
        g = np.zeros((H, 1), np.float32); n = 640
        g[H - n:, 0] = np.clip(np.arange(n) / n, 0, 1) ** 1.4 * 215
        _C["g"] = Image.fromarray(np.repeat(g, W, 1).astype(np.uint8), "L")
    return _C["g"]


def _pen(size):
    k = ("pen", size)
    if k not in _C: _C[k] = ImageFont.truetype(os.path.join(FONTS, "NanumPenScript-Regular.ttf"), size)
    return _C[k]


MOTIONS = ["in", "left", "out", "right", "up", "in", "down", "out"]   # 장면마다 방향을 바꿔 단조롭지 않게
KB_ZOOM = .06    # 확대·축소 폭 6% (2026-11-05 대표: 사진도 줌인·줌아웃·이동으로 생동감, 제1 원칙 97 — r57 '정지 그림' 대체)
KB_PAN = .05     # 이동 폭 = 화면의 5%
_V = {}          # 영상 프레임 캐시 (장면 2개까지만 — 전환 0.35초 겹침용)
VW, VH = 720, 1280


def _vpath(name):
    cands = [name] if os.path.isabs(name) else [os.path.join(ROOT, name), os.path.join(ROOT, "scripts", "blog", "media", "lib", name),
             os.path.join(os.path.dirname(__file__), "assets", "broll", name), os.path.join(os.path.dirname(__file__), "assets", "broll", name + ".mp4")]
    for c in cands:
        if os.path.isfile(c): return c
    raise FileNotFoundError(f"영상 소재 없음: {name}")


def _video(name, secs, start=0.0, xfrac=0.5):
    """세로 화면을 꽉 채우게 잘라 720x1280으로 풀어 둔다(출력 때 1080x1920으로 키움). 영상이 장면보다 짧으면 앞뒤로 왕복 재생."""
    import subprocess
    k = (name, round(start, 2), round(float(xfrac), 3))
    if k not in _V:
        if len(_V) >= 2: _V.pop(next(iter(_V)))
        # 2026-11-12: 코드로 만든 가로 효과 영상(globe_*)은 가운데만 자르면 지명 상자가 잘린다(현대차 쇼츠 '르 아이치').
        # 줄여서 가운데 놓으면 글씨가 너무 작다 → 꽉 채우되 자르는 위치를 대본 "video_x"(0~1, 기본 0.5)로 옮겨 지명 상자를 화면 안에 넣는다.
        vf = f"scale={VW}:{VH}:force_original_aspect_ratio=increase,crop={VW}:{VH}:(iw-ow)*{float(xfrac):.3f}:(ih-oh)/2,fps=30"
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{start:.2f}", "-i", _vpath(name), "-t", f"{secs + .6:.2f}", "-an", "-vf", vf,
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        n = len(raw) // (VW * VH * 3)
        if not n: raise RuntimeError(f"영상 프레임 없음: {name}")
        _V[k] = np.frombuffer(raw[:n * VW * VH * 3], np.uint8).reshape(n, VH, VW, 3)
    return _V[k]


def hook_video(E, scenes):
    """첫 화면은 가능하면 무조건 영상 (2026-11-05 15:21 대표: "제일 첫 화면은 일단 무조건 가능하면 영상으로… 생성하는건 아껴쓰고").
    대본 첫 장면에 "video" 가 없으면 이미 있는 영상(라이브러리 il_*.mp4 → 무료 스톡 영상)에서 제목·해시태그 주제로 골라 끼운다. 새로 만들지 않는다.
    끄려면 첫 장면 full 에 "video": "none"."""
    if not scenes or scenes[0].get("_hv"): return
    scenes[0]["_hv"] = True
    f = scenes[0]["sc"].get("full")
    if not f or f.get("end"): return
    if f.get("video") == "none": f.pop("video", None); return
    if f.get("video"): return
    spec = getattr(E, "SPEC", None) or {}
    try: k = E.broll_key(spec)
    except Exception: k = None
    if k:
        f["video"] = k; print("  첫 화면 영상 자동 선택:", k)


def _ease(E, x):
    return E.ease_io(max(0.0, min(1.0, x)))


def motion_of(f, idx):
    m = f.get("motion")
    if m in ("none", "still") or f.get("zoom") == 0: return "none"
    return m if m in ("in", "out", "left", "right", "up", "down") else MOTIONS[idx % len(MOTIONS)]


def picture(E, s, u):
    """장면 바탕. 소재 우선순위(제1 원칙 97): 라이브러리 영상 → 무료 스톡 영상 → 라이브러리 사진 → 무료 사진.
    영상은 "video": "<lib mp4 | assets/broll 이름 | 경로>" (선택 "video_start": 초). 사진은 "img" 이고 정지 화면 없이 켄 번즈(느린 줌인·줌아웃·이동, 한 장면 한 방향)."""
    f = s["sc"]["full"]; p = _ease(E, u / max(s["dur"], 1.0))
    if f.get("video"):
        fr = _video(f["video"], s["dur"], float(f.get("video_start", 0) or 0), f.get("video_x", 0.5))
        n = len(fr); i = int(u * 30); i = i % (2 * n - 2) if n > 1 else 0
        if i >= n: i = 2 * n - 2 - i
        im = Image.fromarray(fr[i]).resize((W, H), Image.BICUBIC)
        z = 1.0 + .025 * p   # 영상은 이미 움직이므로 아주 느린 확대만
        if z > 1.001:
            big = im.resize((int(W * z), int(H * z)), Image.BILINEAR); x0 = (big.width - W) // 2; y0 = (big.height - H) // 2
            im = big.crop((x0, y0, x0 + W, y0 + H))
        return im
    src = _img(f["img"]); m = motion_of(f, s.get("_mi", 0))
    amp = float(f.get("motion_amp", 1.0) or 1.0)
    if m == "in": z = 1.0 + KB_ZOOM * amp * p
    elif m == "out": z = 1.0 + KB_ZOOM * amp * (1 - p)
    elif m == "none": z = 1.0
    else: z = 1.0 + KB_PAN * amp * 2 + .01   # 이동할 여유만큼 살짝 크게
    r = max(W / src.width, H / src.height) * z
    im = src.resize((int(src.width * r) + 1, int(src.height * r) + 1), Image.BICUBIC)
    fx = f.get("focus_x", .5); fy = f.get("focus_y", .5); sw = KB_PAN * amp * W; sh = KB_PAN * amp * H
    cx = (im.width - W) * fx; cy = (im.height - H) * fy
    if m == "left": cx += sw * (.5 - p)
    elif m == "right": cx += sw * (p - .5)
    elif m == "up": cy += sh * (.5 - p)
    elif m == "down": cy += sh * (p - .5)
    x0 = int(max(0, min(im.width - W, cx))); y0 = int(max(0, min(im.height - H, cy)))
    return im.crop((x0, y0, x0 + W, y0 + H))


def overlay(E, img, s, u):
    """왼쪽 위 종이 라벨 + 펜 숫자 + 금색 밑줄"""
    f = s["sc"]["full"]; L = s["L"]
    lab = f.get("label"); num = f.get("num")
    if not lab and not num: return img
    a = E.prog(u, .15, .55)
    if a <= 0: return img
    p = 0.0
    if num:   # 숫자 자리는 숫자가 나타날 때 늘어난다 (2026-11-01 15:11 대표님: 펜 숫자 쓰기 전 라벨 칸이 비어 보인다)
        t0 = E.y_at(L, f.get("num_line", 0), f.get("num_frac", .3)); p = E.prog(u, t0, t0 + .45)
    lf = E.fit_font(lab or "", "ExtraBold", 46, 820) if lab else None
    pf = _pen(f.get("num_size", 150))
    d0 = ImageDraw.Draw(img)
    lw = d0.textlength(lab, font=lf) if lab else 0
    nw = d0.textlength(num, font=pf) if num else 0
    X, Y = X0, f.get("y", (getattr(E, "BAND_H", 0) or 390) + 30)
    bw = max(lw, nw * (1 if p > 0 else 0)) + 72; bh = 96 + 150 * p
    card = Image.new("RGBA", (int(bw) + 30, int(bh) + 30), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([12, 16, bw + 12, bh + 16], 10, fill=(0, 0, 0, int(90 * a)))
    card = card.filter(ImageFilter.GaussianBlur(7)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, bw, bh], 10, fill=(*PAPER, int(250 * a)))
    oy = int((1 - a) * 16)
    img.paste(card, (X, Y + oy), card)
    d = ImageDraw.Draw(img)
    if lab: d.text((X + 36, Y + oy + 50), lab, font=lf, fill=E.mix(PAPER, INK, a), anchor="lm")
    if num:
        if p > 0:
            col = TONES.get(f.get("tone", "loss"), RED)
            ny = Y + oy + 96 + 70
            d.text((X + 36, ny + (1 - p) * 10), num, font=pf, fill=E.mix(PAPER, col, p), anchor="lm")
            q = E.prog(u, t0 + .35, t0 + .9)
            if q > 0:
                x1 = X + 36 + nw * q; yy = ny + 62
                d.line([(X + 32, yy), (x1, yy - 4)], fill=GOLD, width=9)
    return img


def scene_img(E, s, u):
    if s["sc"]["full"].get("end"): return ending_card(E, s, u, s["sc"]["full"]["end"])
    img = picture(E, s, u)
    img.paste(Image.new("RGB", (W, H), (6, 12, 24)), (0, 0), _grad())
    if getattr(E, "DOC", False): return doc_overlay(E, img, s, u)   # 다큐 스타일 (11/6 편부터 기본)
    return overlay(E, img, s, u)


def render(E, T, s, scenes):
    """현재 장면이 꽉 찬 그림 장면일 때 한 프레임 (자막·제목 띠는 engine.frame 이 얹는다)"""
    i = scenes.index(s)
    for k, x in enumerate(scenes): x.setdefault("_mi", k)   # 장면 순번 → 켄 번즈 방향
    hook_video(E, scenes)
    u = T - s["start"]; img = scene_img(E, s, u)
    if i > 0 and u < XF and scenes[i - 1]["sc"].get("full"):
        p = scenes[i - 1]; prev = scene_img(E, p, p["dur"] - 1 / 30)
        img = Image.blend(prev, img, E.ease_io(u / XF))
    return img


YEL = (255, 216, 77)
NAVYB = (11, 27, 51)


def band_fonts(E, lines, maxw=960):
    """제목 띠 글꼴: 1줄 흰 SemiBold, 2·3줄 노랑 Heavy — 화면 폭(좌우 60px 안)에 맞춰 최대로"""
    out = []
    for i, s_ in enumerate(lines):
        out.append(E.fit_font(s_, "SemiBold" if i == 0 else "Heavy", 74 if i == 0 else 150, maxw))
    return out


def band_height(E, lines):
    fs = band_fonts(E, lines)
    return int(44 + sum(f.size * (1.22 if i else 1.3) for i, f in enumerate(fs)) + 26)


def draw_band(E, img, lines, top=0):
    """진한 단색 네이비 제목 띠 (2026-11-01 15:11 대표님: 제목이 잘 안 보인다 → 띠를 불투명 네이비로, 숫자 줄은 밝은 노랑 + 검정 외곽선, 글자는 폭에 맞춰 최대로)"""
    fs = band_fonts(E, lines); h = band_height(E, lines)
    d = ImageDraw.Draw(img)
    d.rectangle([0, top, W, top + h], fill=NAVYB)
    d.line([(0, top + h), (W, top + h)], fill=(214, 172, 84), width=4)
    y = top + 44
    for i, (s_, f) in enumerate(zip(lines, fs)):
        lh = f.size * (1.22 if i else 1.3); cy = y + lh / 2
        if i == 0:
            d.text((W / 2, cy), s_, font=f, fill=(255, 255, 255), anchor="mm")
        else:
            d.text((W / 2 + 3, cy + 5), s_, font=f, fill=(0, 0, 0), anchor="mm")
            d.text((W / 2, cy), s_, font=f, fill=YEL, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
        y += lh
    return h


# ── 제목 띠 v4 (2026-11-01 16:11 대표님 결정: A 기준 + B의 왼쪽 정렬·골드 알약 태그, 글자 조금 더 크게, 제목 최대 2줄, 로고 영문만 크게) ──
# 대본: "banner_band": true, "banner_style": "tag", "banner_tag": "치킨 한 마리 팔면", "banner": ["사장님 손엔 3,037원", "배달앱 몫은 6,710원?"]
# 네이비 단색 띠 · 크림 글자 · 숫자만 골드 · 외곽선 없이 옅은 그림자 · 왼쪽 정렬(x 60) · 오른쪽 위 영문 ValueNote 로고. 제목 본문은 최대 2줄(넘으면 렌더 오류).
CREAM = (246, 236, 214); GOLDN = (232, 200, 132); TAGC = (214, 172, 84)
BAND_MAX_LINES = 2


def _num_runs(E, s_):
    out = []; i = 0
    for m in E.key_numbers(s_):
        if m.start() > i: out.append((s_[i:m.start()], CREAM))
        out.append((m.group(), GOLDN)); i = m.end()
    if i < len(s_): out.append((s_[i:], CREAM))
    return out


def _shadow_runs(img, x, y, runs, font):
    d = ImageDraw.Draw(img); sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh); cx = x
    for t, _ in runs: ds.text((cx + 3, y + 4), t, font=font, fill=(0, 0, 0, 150), anchor="lm"); cx += d.textlength(t, font=font)
    sh = sh.filter(ImageFilter.GaussianBlur(6)); img.paste(sh, (0, 0), sh)
    d = ImageDraw.Draw(img); cx = x
    for t, c in runs: d.text((cx, y), t, font=font, fill=c, anchor="lm"); cx += d.textlength(t, font=font)


BAND_W = int(W * .88)   # 2026-11-01 16:23 대표님: 두 줄 중 긴 줄이 화면 폭의 약 88%


def tag_fonts(E, lines):
    longest = max(lines, key=lambda t: E.F("Heavy", 100).getlength(t))
    return E.fit_font(longest, "Heavy", 160, BAND_W)


TOP_PAD = 60   # 2026-11-05 대표: 헤더가 화면 맨 위에 너무 붙어 있다 → 띠 안 내용을 60px 내린다(앱 뒤로가기·검색 아이콘과도 안 겹침)


def tag_band_height(E, tag, lines):
    f = tag_fonts(E, lines)
    return int(TOP_PAD + (150 if tag else 50) + len(lines) * f.size * 1.18 + 30)


def logo_en(img, x, y, size=38, a=1.0):
    from brand import logo_image
    lim, pad, off = logo_image(size, "dark", ko=False)
    if a < 1: lim = lim.copy(); lim.putalpha(lim.getchannel("A").point(lambda v: int(v * a)))
    img.paste(lim, (int(x - (lim.width - 2 * pad)) - pad, int(y) - pad), lim)


def draw_tag_band(E, img, tag, lines):
    if len(lines) > BAND_MAX_LINES: raise RuntimeError(f"제목 띠 본문은 최대 {BAND_MAX_LINES}줄 (2026-11-01 대표님): {lines}")
    h = tag_band_height(E, tag, lines); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, h], fill=NAVYB); d.line([(X0, h - 2), (W - X0, h - 2)], fill=TAGC, width=3)
    y = TOP_PAD + 50
    if tag:
        tf = E.F("Bold", 54); tw = d.textlength(tag, font=tf); ty = TOP_PAD + 46
        d.rounded_rectangle([X0, ty, X0 + tw + 52, ty + 78], 39, fill=TAGC)
        d.text((X0 + 26, ty + 39), tag, font=tf, fill=NAVYB, anchor="lm"); y = TOP_PAD + 150
    f = tag_fonts(E, lines)
    for i, s_ in enumerate(lines):
        _shadow_runs(img, X0, y + f.size * .59 + i * f.size * 1.18, _num_runs(E, s_), f)
    return h


X0 = (W - BAND_W) // 2


LOGO_Y = 1572   # 2026-11-05 대표: 하단 자막·로고를 조금 더 위로(1712 → 1572, 인스타 계정명·캡션과 안 겹치게)


def logo_bottom(img, y=None, size=46, a=.75):
    """화면 아래 가운데 영문 ValueNote (2026-11-01 16:23 대표님: 반투명 흰색 0.75, 자막 박스 아래 여백)"""
    y = LOGO_Y if y is None else y
    from brand import EN_FONT
    f = ImageFont.truetype(EN_FONT, size)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.text((W / 2 + 2, y + 3), "ValueNote", font=f, fill=(0, 0, 0, int(110 * a)), anchor="mm")
    lay = lay.filter(ImageFilter.GaussianBlur(3)); ImageDraw.Draw(lay).text((W / 2, y), "ValueNote", font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")
    img.paste(lay, (0, 0), lay)


def ending_card(E, s, u, kind):
    """엔딩 카드: 영문 ValueNote 로고 크게 + 슬로건 "매일 조금 더 / 현명한 투자 습관" + 유튜브 「+ 구독하기」/ 인스타 「+ 팔로우하기」"""
    from brand import paste_logo
    yy = np.linspace(0, 1, H)[:, None]; a = np.array(NAVYB) * (1 - yy) + np.array((6, 14, 30)) * yy
    im = Image.fromarray(np.repeat(a[:, None, :], W, 1).astype(np.uint8))
    f = s["sc"]["full"]
    if f.get("img"):
        src = _img(f["img"]).resize((W, int(W * _img(f["img"]).height / _img(f["img"]).width)))
        src = Image.blend(src, Image.new("RGB", src.size, NAVYB), .82); im.paste(src, (0, H - src.height))
    p = E.prog(u, .05, .45)
    paste_logo(im, W / 2, 660, 120, "dark", align="center", ko=False)
    d = ImageDraw.Draw(im); d.line([(W / 2 - 70, 860), (W / 2 + 70, 860)], fill=TAGC, width=4)
    fs = E.F("ExtraBold", 70)
    for i, l in enumerate(f.get("slogan", ["매일 조금 더", "현명한 투자 습관"])): d.text((W / 2, 960 + i * 98), l, font=fs, fill=(246, 241, 232) if i == 0 else GOLDN, anchor="mm")
    btn = "+ 구독하기" if kind == "yt" else "+ 팔로우하기"; fb = E.F("Heavy", 62); bw = d.textlength(btn, font=fb) + 130
    q = E.prog(u, .4, .8); by = 1230 + (1 - q) * 20
    if q > 0:
        d.rounded_rectangle([W / 2 - bw / 2, by, W / 2 + bw / 2, by + 124], 62, fill=(196, 52, 60) if kind == "yt" else TAGC)
        d.text((W / 2, by + 62), btn, font=fb, fill=(255, 255, 255) if kind == "yt" else NAVYB, anchor="mm")
        t = E.prog(u, .9, 1.3)   # 2026-11-05 16:04 대표: 마지막에 감사 문구 (실제 행동 유도)
        if t > 0:
            ft = E.F("SemiBold", 42); col = tuple(int(c * t + n * (1 - t)) for c, n in zip((236, 230, 218), NAVYB))
            for i, l in enumerate(["좋아요와 구독은 영상 제작에", "큰 힘이 됩니다. 감사합니다."] if kind == "yt" else ["좋아요와 팔로우는 콘텐츠 제작에", "큰 힘이 됩니다. 감사합니다."]):
                d.text((W / 2, 1440 + i * 62), l, font=ft, fill=col, anchor="mm")
    if p < 1: im = Image.blend(Image.new("RGB", (W, H), NAVYB), im, p)
    return im


# ── 다큐 스타일 표시 (2026-11-05 15:30 대표: 롱폼 다큐 스타일(11/4 확정, youtube/long/docfx.py)을 숏폼에) ──
# 판(종이 라벨) 없이 그림·영상 위에 바로: 위쪽을 남색으로 서서히 어둡게 → 금색 짧은 선이 그어지고 작은 금색 제목이 미끄러져 들어옴 →
# 굵은 숫자 하나가 0에서 세어 올라감(빛나는 그림자) → 선택: 등락률 막대("pct")·막대("bars")가 자라며 숫자가 따라 올라감.
# 대본: full 의 "label"(작은 제목) · "num"(큰 숫자) · "tone" 그대로 + 선택 "pct": [{"label","v"}] · "bars": [{"label","v","text","color"}]
DGOLD = (226, 192, 120); DWHITE = (246, 243, 236); DGRAY = (170, 178, 192); DRED = (236, 92, 100); DGREEN = (84, 214, 150)
DTONE = {"loss": DRED, "good": DGREEN, "gold": DGOLD, "ink": DWHITE}
_DG = {}


def _dgrad(top, n):
    k = (top, n)
    if k not in _DG:
        yy = np.arange(H, dtype=np.float32)
        a = np.clip(1 - (yy - top) / n, 0, 1) ** 1.1; a[yy < top] = 1
        _DG[k] = a[:, None, None]
    return _DG[k]


def _eout(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def _count(txt, q):
    m = re.fullmatch(r"(약 )?([+\-]?)(\d[\d,]*(?:\.\d+)?)(%|배|조|원|만 원)?", txt.strip())
    if not m: return txt
    raw = m.group(3).replace(",", ""); dec = len(raw.split(".")[1]) if "." in raw else 0
    v = float(raw) * q; body = f"{v:,.{dec}f}" if "," in m.group(3) or dec == 0 and v >= 1000 else f"{v:.{dec}f}"
    return f"{m.group(1) or ''}{m.group(2)}{body}{m.group(4) or ''}"


def _dtext(img, xy, text, font, fill, glow=False, anchor="la"):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    a = fill[3] if len(fill) == 4 else 255
    ld.text((xy[0] + 3, xy[1] + 5), text, font=font, fill=(0, 0, 0, int(a * .6)), anchor=anchor)
    lay = lay.filter(ImageFilter.GaussianBlur(5 if glow else 3))
    if glow:
        g = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(g).text(xy, text, font=font, fill=(*fill[:3], int(a * .45)), anchor=anchor)
        lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(lay).text(xy, text, font=font, fill=fill, anchor=anchor)
    img.paste(lay, (0, 0), lay)


def _tat(E, L, i, frac):
    """대본의 num_line 이 자막 묶음 수보다 크면(한 묶음 안의 둘째 줄을 가리킨 옛 대본) 마지막 묶음 안에서 비율로 잡는다"""
    if i < len(L): return E.y_at(L, i, frac)
    a, v = L[-1][0], L[-1][1]; return a + v * min(.95, (.5 + .5 * frac))


def doc_overlay(E, img, s, u):
    f = s["sc"]["full"]; L = s["L"]
    lab = f.get("label"); num = f.get("num"); pct = f.get("pct"); bars = f.get("bars")
    if not (lab or num or pct or bars): return img
    g = E.ease_io(max(0.0, min(1.0, (u - .05) / .5)))
    top = (getattr(E, "BAND_H", 0) or 330)
    if g > 0:   # 위쪽을 남색으로 (글씨 자리) + 전체를 살짝 어둡게 — 다큐 색
        a = np.asarray(img, np.float32); m = _dgrad(top + 120, 760) * .82 * g
        a = a * (1 - .14 * g); a = a * (1 - m) + np.array([8, 14, 26], np.float32) * m
        img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    X = X0; y = top + 70
    if lab:
        p = u - .15; d = ImageDraw.Draw(img)
        # 2026-11-13 대표: "작은 폰트 쓰지 마, 안 보여" → 줄이지 않고 46px 고정, 길면 두 줄로. 앞 장식 선도 없앰(겹침)
        lf = E.F("SemiBold", 46); maxw = BAND_W - 40
        words = lab.split(); rows = [""]
        for w_ in words:
            t_ = (rows[-1] + " " + w_).strip()
            if d.textlength(t_, font=lf) <= maxw or not rows[-1]: rows[-1] = t_
            else: rows.append(w_)
        r = _eout((p - .05) / .4)
        if r > 0:
            for k_, row in enumerate(rows[:2]):
                _dtext(img, (X + 26 * (1 - r), y + 22 + k_ * 60), row, lf, (*DGOLD, int(255 * r)), anchor="lm")
        y += 84 + 60 * (min(len(rows), 2) - 1)
    col = DTONE.get(f.get("tone", "ink"), DWHITE)
    if num:
        t0 = _tat(E, L, f.get("num_line", 0), f.get("num_frac", .3)); p = u - t0
        if p > 0:
            r = _eout(p / .5); c = _eout(p / 1.0)
            txt = _count(num, c); fnt = E.F("Heavy", 190 if len(num) <= 7 else 150)
            _dtext(img, (X, y + 22 * (1 - r)), txt, fnt, (*col, int(255 * r)), glow=True)
        y += 230
    if pct:
        t0 = _tat(E, L, f.get("num_line", 0), f.get("pct_frac", .45)); p = u - t0
        if p > 0: img = _dpct(E, img, pct, p, y)
    if bars:
        t0 = _tat(E, L, f.get("num_line", 0), f.get("bars_frac", .2)); p = u - t0
        if p > 0: img = _dbars(E, img, bars, p, y)
    return img


def _dpct(E, img, it, p, y):
    """등락률 가로 막대: 한 줄에 하나씩 — 위 작은 회색 이름, 아래 기준선에서 오른쪽으로 자라는 막대(상승 초록·하락 빨강) + 끝에 숫자"""
    vmax = max(abs(i["v"]) for i in it) or 1; maxw = BAND_W - 360
    for k, i in enumerate(it):
        q = _eout((p - .1 - k * .45) / .8)
        if q <= 0: continue
        v = i["v"]; col = DRED if v < 0 else DGREEN; ry = y + 40 + k * 190
        _dtext(img, (X0, ry), i["label"], E.F("SemiBold", 38), (*DGRAY, int(255 * min(1, q * 2))))
        bw = max(8, maxw * abs(v) / vmax * q); d = ImageDraw.Draw(img)
        d.rectangle([X0, ry + 60, X0 + bw, ry + 130], fill=col)
        _dtext(img, (X0 + bw + 24, ry + 95), f"{v * q:+.2f}%", E.F("Heavy", 76), (*col, 255), anchor="lm")
    return img


def _dbars(E, img, it, p, y):
    d = ImageDraw.Draw(img); h = 420; base = y + 80 + h; vmax = max(abs(i["v"]) for i in it); n = len(it); step = min(330, (BAND_W - 40) // n)
    d.line([(X0, base), (X0 + step * n * _eout(p / .4), base)], fill=(200, 205, 215), width=2)
    for k, i in enumerate(it):
        q = _eout((p - .15 - k * .35) / .9)
        if q <= 0: continue
        bx = X0 + k * step; bh = h * abs(i["v"]) / vmax * q; col = DTONE.get(i.get("color"), DWHITE)
        d.rectangle([bx, base - bh, bx + 130, base], fill=col if k == len(it) - 1 else tuple(int(c * .62) for c in col))   # 마지막(강조) 막대만 선명하게
        _dtext(img, (bx, base - bh - 14), _count(i.get("text", ""), q), E.F("Heavy", 58), (*col, 255), anchor="ld")
        _dtext(img, (bx, base + 18), i["label"], E.F("SemiBold", 32), (*DGRAY, 255))
        d = ImageDraw.Draw(img)
    return img
