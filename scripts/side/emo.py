"""What Korea Says — 감성 쇼츠 렌더러 (2026-10-28)
말 없는 15~30초 세로 쇼츠: 5초 영상 컷들을 부드럽게 이어 붙이고, 컷마다 짧은 영어 자막 한 줄, 잔잔한 배경음악.
입력: scripts/side/specs_emo/<id>.json
  {"id", "title", "description", "tags", "pinned", "scheduled_at",
   "music": {"file": "music_miss-you.mp3", "start": 0, "vol": 0.9},
   "cuts": [{"v": "mbv1_pack", "in": 0.2, "dur": 4.3, "cap": "2 a.m. in Seoul."},
            {"img": "mb3_note", "dur": 3.4, "move": "in", "cap": "..."}, ...],
   - "v" = 생성한 5초 영상 (모든 컷의 기본). "img" = 그림 한 장을 천천히 움직이는 컷 — 2026-10-28 대표님 결정으로 쓰지 않는다(퀄리티 유지). 비상용으로만 남겨 둠
     move: in(다가가기, 기본) | out(물러나기) | left | right | up | down (가로·세로로 천천히 흐르기)
   "thumb": {"cut": 5, "t": 2.5}}
결과: 릴리스 side-<id> 에 영상, social/side/<id>/(meta.json, thumb.jpg, subtitles_en.srt), social/side/queue.json 에 kind=short 로 등록
사용: python3 scripts/side/emo.py <id> [--test]   (--test 는 queue.json 에 올리지 않는다)
"""
import json, os, subprocess, sys, time, urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GEN = os.path.join(ROOT, "social", "side", "gen")
FONTS = os.path.join(os.path.dirname(__file__), "fonts")
REPO = os.environ.get("GITHUB_REPOSITORY", "immin03/haeja")
W, H, FPS, XF = 1080, 1920, 30, 0.5   # 화면, 초당 프레임, 컷 사이 겹침(초)
WORK = os.path.join(ROOT, "_emo"); os.makedirs(WORK, exist_ok=True)


def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode: sys.exit(f"실패: {' '.join(a)[:300]}\n{r.stderr[-1500:]}")
    return r.stdout


def find_image(name):
    for e in (".png", ".jpg", ".jpeg", ".webp"):
        p = os.path.join(GEN, name + e)
        if os.path.exists(p): return p
    sys.exit(f"그림 없음: {name}")


def still_cut(c, out):
    """그림 한 장 → 천천히 움직이는 컷 (Ken Burns). 원본을 2배로 키운 뒤 zoompan 으로 부드럽게 움직인다"""
    d = float(c["dur"]); fr = int(round(d * FPS)); mv = c.get("move", "in")
    z = {"in": f"1.0+0.10*on/{fr}", "out": f"1.10-0.10*on/{fr}"}.get(mv, "1.12")
    x = {"left": f"(iw-iw/zoom)*(1-on/{fr})", "right": f"(iw-iw/zoom)*on/{fr}"}.get(mv, "(iw-iw/zoom)/2")
    y = {"up": f"(ih-ih/zoom)*(1-on/{fr})", "down": f"(ih-ih/zoom)*on/{fr}"}.get(mv, "(ih-ih/zoom)/2")
    sh("ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", find_image(c["img"]), "-t", str(d), "-an",
       "-vf", f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase:flags=lanczos,crop={W * 2}:{H * 2},"
              f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p",
       "-frames:v", str(fr), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out)


def find_video(name):
    for e in (".mp4", ".webm", ".mov"):
        p = os.path.join(GEN, name + e)
        if os.path.exists(p): return p
    sys.exit(f"영상 없음: {name}")


def caption_png(text, path):
    """가운데 정렬 흰 글씨 + 부드러운 그림자. 화면 위쪽 1/5 지점(쇼츠 아래쪽 UI를 피한다)"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f = ImageFont.truetype(os.path.join(FONTS, "Poppins-SemiBold.ttf"), 74)
    lines = []
    for para in text.split("\n"):   # 너비 900 안으로 줄바꿈
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if f.getlength(t) > 900 and cur: lines.append(cur); cur = w
            else: cur = t
        lines.append(cur)
    lh = 98; y0 = int(H * 0.19) - lh * len(lines) // 2
    # 밝은 장면에서도 읽히게 글자 뒤에 아주 흐린 어두운 판
    tw = max(f.getlength(ln) for ln in lines)
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dp = ImageDraw.Draw(plate)
    dp.rounded_rectangle(((W - tw) / 2 - 60, y0 - 40, (W + tw) / 2 + 60, y0 + lh * len(lines) + 30), 60, fill=(10, 12, 24, 120))
    img = Image.alpha_composite(img, plate.filter(ImageFilter.GaussianBlur(38)))
    sh_ = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh_)
    for i, ln in enumerate(lines):
        x = (W - f.getlength(ln)) / 2
        ds.text((x, y0 + i * lh + 3), ln, font=f, fill=(0, 0, 0, 200))
    sh_ = sh_.filter(ImageFilter.GaussianBlur(9))
    img = Image.alpha_composite(img, sh_); d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        x = (W - f.getlength(ln)) / 2
        d.text((x, y0 + i * lh), ln, font=f, fill=(255, 251, 242, 255))
    img.save(path)


def heart(d, cx, cy, r, fill):
    """글꼴에 없을 수 있는 하트 기호 대신 직접 그린다"""
    import math
    pts = [(cx + r * 16 * math.sin(t) ** 3 / 16, cy - r * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16)
           for t in [i * 2 * math.pi / 120 for i in range(120)]]
    d.polygon(pts, fill=fill)


def _png(img, name):
    p = os.path.join(WORK, name); img.save(p); return p


def _fade(img, a):
    """RGBA 그림의 투명도를 a(0~1)배로"""
    if a >= 0.999: return img
    im = img.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0.0, a)))); return im


def _clamp(v, lo=0.0, hi=1.0): return max(lo, min(hi, v))


def _fit(text, path, size, maxw):
    """글자가 maxw 안에 들어갈 때까지 크기를 줄인다"""
    while size > 24:
        f = ImageFont.truetype(path, size)
        if f.getlength(text) <= maxw: return f
        size -= 2
    return ImageFont.truetype(path, size)


def end_card(spec, bg_frame, out, dur=4.2):
    """엔딩 (2026-10-30 대표님: "좋아요 두 번 탭, 팔로우 유도를 더 자연스럽게")
    0.0  마지막 장면을 흐리게 깔고 글자 로고가 살짝 튀어 오른다
    0.25 소포 든 까치가 오른쪽 위에서 날아와 로고 'From' 위에 앉는다
    1.45 문구 'Kachi brings you love, from Korea'
    1.9  까치 옆 빈자리를 손끝(흰 터치 점)이 톡톡 두 번 → 물결 두 번 → 빨간 하트가 터지고 작은 하트들이 날아오른다, 까치가 기뻐서 폴짝
         그 아래 'Double-tap ♥ / if this warmed your heart'
    2.85 'Follow for a new story every day' (빨간 알약 모양, 버튼보다 부드럽게)
    쇼츠 아래쪽 제목 영역(y>1470)과 오른쪽 버튼 줄(x>940)을 비운다. 프레임마다 PIL 로 그려 ffmpeg 로 묶는다"""
    import math
    E = spec.get("end", {})
    RED, NAVY, PINK = (215, 50, 44), (31, 42, 68), (240, 120, 130)
    bg = Image.open(bg_frame).convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(26))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (255, 236, 205)), 0.35).convert("RGBA")
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(plate).rounded_rectangle((90, 440, W - 90, 1460), 80, fill=(255, 248, 236, 150))
    bg = Image.alpha_composite(bg, plate.filter(ImageFilter.GaussianBlur(40)))
    # 로고 (글자만)
    lg = Image.open(os.path.join(ROOT, "docs", "side", "logo_text.png")).convert("RGBA")
    lw = 640; lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
    lx, ly = (W - lw) // 2, 740
    # 까치: 나는 모습 → 앉은 모습 ('From' 글자 위에 앉는다)
    def cutout(name, h):
        k = Image.open(os.path.join(ROOT, "social", "side", "gen", "cut", name + ".png")).convert("RGBA")
        return k.resize((int(k.width * h / k.height), h), Image.LANCZOS)
    fly = cutout(E.get("fly", "h_fly_love"), 400); stand = cutout(E.get("host", "h_love"), 400)
    sx, sy = lx + 30, ly - stand.height + 28
    fx0, fy0 = W + 40, 120
    fx1, fy1 = sx - (fly.width - stand.width) // 2, sy - 20
    T0, T1 = 0.25, 1.35
    # 문구
    f1 = _fit(E.get("phrase", "Kachi brings you love, from Korea"), os.path.join(FONTS, "Poppins-SemiBold.ttf"), 54, 740)
    phrase = E.get("phrase", "Kachi brings you love, from Korea")
    ph = Image.new("RGBA", (W, 90), (0, 0, 0, 0))
    ImageDraw.Draw(ph).text(((W - f1.getlength(phrase)) / 2, 8), phrase, font=f1, fill=NAVY + (255,))
    py = ly + lg.height + 24
    # 더블탭 안내 (두 줄): 'Double-tap ♥' + 'if this warmed your heart'
    fa = ImageFont.truetype(os.path.join(FONTS, "Poppins-Bold.ttf"), 60)
    fb = _fit(E.get("tap_line", "if this warmed your heart"), os.path.join(FONTS, "Poppins-SemiBold.ttf"), 44, 760)
    l1, l2 = "Double-tap", E.get("tap_line", "if this warmed your heart")
    cap = Image.new("RGBA", (W, 150), (0, 0, 0, 0)); dc = ImageDraw.Draw(cap)
    w1 = fa.getlength(l1) + 22 + 52; x1 = (W - w1) / 2
    dc.text((x1, 0), l1, font=fa, fill=RED + (255,)); heart(dc, x1 + fa.getlength(l1) + 22 + 26, 44, 25, RED + (255,))
    dc.text(((W - fb.getlength(l2)) / 2, 82), l2, font=fb, fill=NAVY + (255,))
    cy0 = py + 96
    # 팔로우 (빨간 알약, 오른쪽 버튼 줄을 넘지 않게 너비 760 이하)
    fl = E.get("follow_line", "Follow for a new story every day")
    ff = _fit(fl, os.path.join(FONTS, "Poppins-Bold.ttf"), 42, 660)
    pw = int(ff.getlength(fl) + 110); pill = Image.new("RGBA", (pw + 40, 120), (0, 0, 0, 0)); dl = ImageDraw.Draw(pill)
    dl.rounded_rectangle((20, 20, 20 + pw, 100), 40, fill=RED + (255,))
    dl.text((20 + 55, 60 - (ff.getbbox(fl)[1] + ff.getbbox(fl)[3]) / 2), fl, font=ff, fill=(255, 255, 255, 255))
    shadow = Image.new("RGBA", pill.size, (0, 0, 0, 0)); ImageDraw.Draw(shadow).rounded_rectangle((20, 28, 20 + pw, 108), 40, fill=(90, 20, 10, 70))
    pill = Image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(8)), pill)
    pxp, pyp = (W - pill.width) // 2, cy0 + 150
    # 탭·하트 위치: 까치 오른쪽 빈자리
    hx, hy = min(sx + stand.width + 140, 740), sy + 190
    TA, TB = 2.12, 2.40                       # 첫째·둘째 탭 (둘째 탭에 하트가 터진다)
    def heart_img(r, col, ring=0):
        s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        if ring: heart(d, s / 2, s / 2 + r * 0.05, r + ring, (255, 255, 255, 235))
        heart(d, s / 2, s / 2 + r * 0.05, r, col + (255,)); return im
    big = heart_img(92, RED, ring=8)
    def blit(fr, im, cx, cy, a=1.0, sc=1.0):
        if a <= 0.01 or sc <= 0.02: return
        if abs(sc - 1) > 0.01: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
        im = _fade(im, a); x, y = int(cx - im.width / 2), int(cy - im.height / 2)
        if x >= W or y >= H or x + im.width <= 0 or y + im.height <= 0: return
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); L.paste(im, (x, y)); fr.alpha_composite(L)
    # 작은 하트들 (각도, 거리, 크기, 색)
    random_pts = [(-125, 150, 26, PINK), (-100, 210, 20, RED), (-80, 175, 28, PINK), (-62, 225, 18, RED), (-140, 110, 18, RED), (-90, 120, 22, PINK)]
    minis = [(heart_img(r, c), a, d) for a, d, r, c in random_pts]
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for k in range(int(round(dur * FPS))):
        t = k / FPS; fr = bg.copy()
        # 로고
        blit(fr, lg, lx + lw / 2, ly + lg.height / 2 + 25 * math.exp(-6 * t), _clamp(t / 0.45))
        # 까치
        if t < T1:
            P = _clamp((t - T0) / (T1 - T0)); e3 = 1 - (1 - P) ** 3
            x = fx0 + (fx1 - fx0) * e3; y = fy0 + (fy1 - fy0) * e3 - 160 * math.sin(math.pi * P) + 10 * math.sin(2 * math.pi * 6 * t)
            blit(fr, fly, x + fly.width / 2, y + fly.height / 2)
        else:
            y = sy - 26 * math.exp(-7 * (t - T1)) * abs(math.cos(11 * (t - T1)))
            if t >= TB: y -= 46 * math.exp(-5 * (t - TB)) * abs(math.sin(9 * (t - TB)))   # 하트가 터지면 폴짝
            blit(fr, stand, sx + stand.width / 2, y + stand.height / 2)
        # 문구
        if t >= 1.45: blit(fr, ph, W / 2, py + 45 + 18 * math.exp(-7 * (t - 1.45)), _clamp((t - 1.45) / 0.45))
        # 물결 두 번
        for ts in (TA, TB):
            u = (t - ts) / 0.5
            if 0 <= u <= 1:
                rr = 36 + 118 * (1 - (1 - u) ** 2); ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(ring).ellipse((hx - rr, hy - rr, hx + rr, hy + rr), outline=RED + (int(200 * (1 - u)),), width=7)
                fr.alpha_composite(ring)
        # 큰 하트 (둘째 탭에 튀어나와 작게 두근거린다)
        if t >= TB:
            u = t - TB; s = 1 - math.exp(-7 * u) * math.cos(13 * u)
            s *= 1 + 0.035 * math.sin(2 * math.pi * 1.4 * max(0, u - 0.6)) * (u > 0.6)
            blit(fr, big, hx, hy, 1.0, max(0.02, s))
            for im, ang, dist in minis:
                v = _clamp(u / 0.95); r = math.radians(ang)
                blit(fr, im, hx + math.cos(r) * dist * v + 14 * math.sin(6 * u), hy + math.sin(r) * dist * v - 60 * v, (1 - v) ** 1.3)
        # 터치 점 (손끝): 나타나서 톡톡 두 번 누르고 사라진다
        if 1.9 <= t <= 2.75:
            a = _clamp((t - 1.9) / 0.18) * _clamp((2.75 - t) / 0.2)
            press = 1.0
            for ts in (TA, TB):
                if ts - 0.02 <= t <= ts + 0.1: press = 0.74
            r = 46 * press; dot = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(dot)
            dd.ellipse((hx + 6 - r, hy + 10 - r, hx + 6 + r, hy + 10 + r), fill=(60, 30, 20, int(60 * a)))
            fr.alpha_composite(dot.filter(ImageFilter.GaussianBlur(10)))
            dot = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(dot)
            dd.ellipse((hx - r, hy - r, hx + r, hy + r), fill=(255, 255, 255, int(225 * a)), outline=(200, 200, 200, int(255 * a)), width=3)
            fr.alpha_composite(dot)
        # 안내 문구
        if t >= 1.9: blit(fr, cap, W / 2, cy0 + 75 + 16 * math.exp(-7 * (t - 1.9)), _clamp((t - 1.9) / 0.4))
        # 팔로우
        if t >= 2.85:
            u = t - 2.85; s = 1 + 0.12 * math.exp(-6 * u) * math.sin(14 * u)
            blit(fr, pill, W / 2, pyp + pill.height / 2 + 30 * math.exp(-8 * u), _clamp(u / 0.3), s)
        proc.stdin.write(fr.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait(): sys.exit("엔딩 렌더 실패")


def srt_time(t):
    ms = int(round(t * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def music_file(m):
    p = os.path.join(WORK, m["file"])
    if not os.path.exists(p) or not os.path.getsize(p):
        urllib.request.urlretrieve(f"https://github.com/{REPO}/releases/download/side-assets/{m['file']}", p)
    return p


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; test = "--test" in sys.argv
    sid = args[0]; spec = json.load(open(os.path.join(ROOT, "scripts", "side", "specs_emo", sid + ".json"), encoding="utf-8"))
    cuts = spec["cuts"]; n = len(cuts)
    # 1) 컷마다 잘라서 1080x1920·30fps 로 맞춘다 (원본 비율이 달라도 꽉 채우고 가운데 자르기)
    parts = []
    for i, c in enumerate(cuts):
        out = os.path.join(WORK, f"c{i}.mp4")
        if c.get("img") and not c.get("v"):
            # 2026-10-28 대표님: "사진으로 대체하는 것도 안 했으면 좋겠어. 영상 계속 움직여야 돼." → 모든 컷은 실제 영상
            if os.environ.get("SIDE_ALLOW_STILL") != "1": sys.exit(f"컷 {i + 1}: 그림 컷(img)은 쓰지 않습니다. 이 컷도 영상으로 생성하세요 (대표님 결정 2026-10-28)")
            still_cut(c, out)
        else: sh("ffmpeg", "-v", "error", "-y", "-ss", str(c.get("in", 0)), "-t", str(c["dur"]), "-i", find_video(c["v"]), "-an",
           "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},setsar=1,format=yuv420p",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out)
        real = float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out))
        parts.append((out, real))
    # 1-2) 마무리 카드: 마지막 컷의 끝 장면 위에 채널 로고·팔로우 유도 (2026-10-28 운영자 요청)
    if spec.get("end", {}).get("on", True):
        lastf = os.path.join(WORK, "last.png")
        sh("ffmpeg", "-v", "error", "-y", "-sseof", "-0.1", "-i", parts[-1][0], "-frames:v", "1", "-update", "1", lastf)
        ep = os.path.join(WORK, "end.mp4"); end_card(spec, lastf, ep, spec.get("end", {}).get("dur", 4.2))
        parts.append((ep, float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", ep))))
    n = len(parts)
    # 2) 컷 시작 시각 계산 (겹침 XF 초)
    starts, t = [], 0.0
    for i, (_, d) in enumerate(parts):
        starts.append(t); t += d - (XF if i < n - 1 else 0)
    total = round(t, 3)
    # 3) 자막 그림
    caps = []
    for i, c in enumerate(cuts):
        if not c.get("cap"): continue
        a = starts[i] + 0.5 if i else 0.0; b = (starts[i + 1] + XF * 0.5) if i < n - 1 else total
        p = os.path.join(WORK, f"cap{i}.png"); caption_png(c["cap"], p); caps.append((p, round(a, 2), round(b, 2), c["cap"]))
    # 4) 이어 붙이기 + 자막 + 음악
    m = spec["music"]; mp = music_file(m)
    inp = []
    for p, _ in parts: inp += ["-i", p]
    for p, *_ in caps: inp += ["-loop", "1", "-t", str(total), "-i", p]
    inp += ["-ss", str(m.get("start", 0)), "-i", mp]
    fc, last, off = [], "[0:v]", 0.0
    for i in range(1, n):
        off += parts[i - 1][1] - XF
        fc.append(f"{last}[{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{i}]"); last = f"[x{i}]"
    fade_out = max(0, total - 0.6)
    fc.append(f"{last}null[base0]"); last = "[base0]"
    for k, (p, a, b, _) in enumerate(caps):
        ii = n + k
        fin = f"fade=in:st={a}:d=0.5:alpha=1," if a > 0 else ""   # 첫 자막은 첫 프레임부터 보인다(훅)
        fc.append(f"[{ii}:v]format=rgba,{fin}fade=out:st={max(a, b - 0.5):.2f}:d=0.5:alpha=1[cp{k}]")
        fc.append(f"{last}[cp{k}]overlay=0:0:enable='between(t,{a},{b})'[o{k}]"); last = f"[o{k}]"
    ai = n + len(caps)
    fc.append(f"[{ai}:a]atrim=0:{total},asetpts=PTS-STARTPTS,volume={m.get('vol', 0.9)},afade=t=in:st=0:d=1.2,afade=t=out:st={total - 2.2:.2f}:d=2.2,"
              f"loudnorm=I=-15:TP=-1.5:LRA=11[aout]")
    out = os.path.join(WORK, f"{sid}.mp4")
    sh("ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(fc), "-map", last, "-map", "[aout]",
       "-t", str(total), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out)
    dur = float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out))
    # 5) 썸네일·자막 파일·점검용 프레임
    od = os.path.join(ROOT, "social", "side", sid); os.makedirs(od, exist_ok=True)
    th = spec.get("thumb", {"cut": n - 2, "t": 2.0}); tt = starts[th["cut"]] + th["t"]
    sh("ffmpeg", "-v", "error", "-y", "-ss", f"{tt:.2f}", "-i", out, "-frames:v", "1", "-q:v", "2", os.path.join(od, "thumb.jpg"))
    with open(os.path.join(od, "subtitles_en.srt"), "w", encoding="utf-8") as f:
        for k, (_, a, b, txt) in enumerate(caps): f.write(f"{k + 1}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n\n")
    qa = os.path.join(od, "qa"); os.makedirs(qa, exist_ok=True)
    for i in range(n):
        sh("ffmpeg", "-v", "error", "-y", "-ss", f"{starts[i] + parts[i][1] * 0.55:.2f}", "-i", out, "-frames:v", "1", "-vf", "scale=360:-1", os.path.join(qa, f"f{i}.jpg"))
    if "--local" in sys.argv: print("로컬 점검용:", out, round(dur, 1)); return
    # 6) 릴리스에 올리고 기록
    stamp = time.strftime("%y%m%d%H%M"); tag = f"side-{sid}"; fn = f"{sid}{'-test' if test else ''}-{stamp}.mp4"
    os.rename(out, os.path.join(WORK, fn)); out = os.path.join(WORK, fn)
    if subprocess.run(["gh", "release", "view", tag, "-R", REPO], capture_output=True).returncode:
        sh("gh", "release", "create", tag, "-R", REPO, "--title", sid, "--notes", spec["title"], "--latest=false")
    sh("gh", "release", "upload", tag, out, "--clobber", "-R", REPO)
    url = f"https://github.com/{REPO}/releases/download/{tag}/{fn}"
    meta = {k: spec.get(k) for k in ("id", "title", "description", "tags", "pinned", "scheduled_at")}
    meta.update(kind="short", duration=round(dur, 1), video_url=url, thumb=f"/social/side/{sid}/thumb.jpg?v={stamp}",
                subtitle=(f"/social/side/{sid}/subtitles_en.srt" if spec.get("srt") else None), rendered_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"), test=test)
    json.dump(meta, open(os.path.join(od, "meta.json"), "w"), ensure_ascii=False, indent=1)
    if not test:
        qp = os.path.join(ROOT, "social", "side", "queue.json"); q = json.load(open(qp)) if os.path.exists(qp) else []
        q = [x for x in q if x.get("id") != sid] + [meta]; json.dump(q, open(qp, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"url": url, "duration": round(dur, 1), "captions": [(a, b, t) for _, a, b, t in caps]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
