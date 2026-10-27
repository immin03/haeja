"""What Korea Says — 미니어처 세계 + 진행자 까치(Kachi) 롱폼 렌더러 v2 (2026-10-27)

원고: scripts/side/specs2/<id>.json
  {"id", "title", "scheduled_at", "tags", "description", "sources", "loc",
   "voice": {"id": "tc_...", "emotion": "toneup", "pitch": 2, "tempo": 1.12},
   "music": "music_comical.mp3",            # 릴리스 side-assets 의 파일 (없으면 음악 없이)
   "thumb": {"bg": "cp_thumb", "big": "BANNED?!", "small": "IN NORTH KOREA", "pose": "c1_surprised"},
   "scenes": [{
      "bg": "cp01_dmz",                     # social/side/gen/<bg>.(jpeg|png)
      "vid": "cpv01_dmz",                   # (선택) social/side/gen/<vid>.mp4 — 있으면 영상 배경(정방향→역방향 반복)
      "move": "in|out|left|right|up|down",  # 정지 배경 카메라 이동
      "chip": "1973 · Georgia, USA",        # (선택) 왼쪽 위 장소·시간 표지
      "chapter": "A hotel in Georgia",      # (선택) 설명란 챕터
      "host": {"pose": "h_talk", "side": "right", "then": [[2, "h_laugh"]]},   # null 이면 진행자 없음
      "lines": ["...", "..."],              # 내레이션 한 줄씩
      "hl": ["banned", "snack"],            # 자막에서 노란색으로 칠할 단어
      "pops": [{"at": 1, "kind": "comment", "text": "...", "orig": "...", "src": "YouTube · Russia", "likes": "304"},
               {"at": 0, "kind": "stamp", "text": "BANNED"}, {"at": 0, "kind": "glyph", "text": "情"},
               {"at": 1, "kind": "tag", "text": "$9.50"}, {"at": 0, "kind": "count", "to": 600000000, "label": "packs a year"}],
      "short": true}]}
화면 원칙(운영자 2026-10-27): PART 번호 없음, 단어 단위로 튀어나오는 작은 자막(핵심어만 노랑), 댓글이 따다닥 터짐, 진행자 까치가 장면을 끌고 감
"""
import datetime as dt, glob, hashlib, json, math, os, random, re, subprocess, sys, urllib.error, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "social", "side")
GEN = os.path.join(OUT, "gen"); CUT = os.path.join(GEN, "cut")
CACHE = os.path.join(HERE, ".cache2"); os.makedirs(CACHE, exist_ok=True)
REPO = os.environ.get("GITHUB_REPOSITORY", "immin03/haeja")
W, H, FPS, SR = 1920, 1080, 30, 44100

INK = (24, 20, 34); WHITE = (255, 255, 255); YEL = (255, 210, 26); RED = (226, 48, 40); CREAM = (255, 248, 236)
MUTE = (120, 110, 104)

# ---------------- 글꼴 ----------------
_FC = {}
def _font(path, size, var=None, index=0):
    k = (path, size, var, index)
    if k not in _FC:
        f = ImageFont.truetype(path, size, index=index)
        if var:
            try: f.set_variation_by_name(var)
            except Exception: pass
        _FC[k] = f
    return _FC[k]
def FB(size, var="ExtraBold"): return _font(os.path.join(HERE, "fonts", "Baloo2.ttf"), int(size), var)
def FP(size, w="Bold"): return _font(os.path.join(HERE, "fonts", f"Poppins-{w}.ttf"), int(size))
def FF(size, var="Bold"): return _font(os.path.join(HERE, "fonts", "Fredoka.ttf"), int(size), var)
def FKR(size):
    for p in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"):
        if os.path.exists(p): return _font(p, int(size), None, 1)
    return FB(size)
def FCJK(size):
    for p in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"):
        if os.path.exists(p): return _font(p, int(size), None, 1)
    return FB(size)


def ease_out(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def ease_back(x):
    x = max(0.0, min(1.0, x)); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


# ---------------- 음성 ----------------
_TTS_MODE = {"m": None}
def _tts_call(body):
    req = urllib.request.Request("https://api.typecast.ai/v1/text-to-speech", method="POST", data=json.dumps(body).encode(),
                                 headers={"X-API-KEY": os.environ["TYPECAST_API_KEY"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r: return r.read()


def say(text, v):
    """영어 한 줄 → float32 mono 44.1kHz (앞뒤 무음 제거). 음높이·속도는 타입캐스트 옵션 → 안 되면 ffmpeg"""
    voice, emo, semis, tempo = v["id"], v.get("emotion", "normal"), float(v.get("pitch", 0)), float(v.get("tempo", 1.12))
    key = hashlib.sha1(f"{voice}|{emo}|{semis}|{tempo}|{text}".encode()).hexdigest()[:20]
    wav = os.path.join(CACHE, key + ".wav")
    if not os.path.exists(wav):
        if not os.environ.get("TYPECAST_API_KEY"):
            n = int(SR * max(1.2, len(text.split()) * 0.27)); return np.zeros(n, np.float32)
        base = {"text": text, "model": "ssfm-v30", "voice_id": voice, "language": "eng"}
        if emo != "normal": base["prompt"] = {"emotion_type": "preset", "emotion_preset": emo, "emotion_intensity": 1.0}
        mp3 = os.path.join(CACHE, key + ".mp3"); done = None
        # 2026-10-27 시험: 타입캐스트 audio_pitch·audio_tempo 는 받아 주지만 실제로 바뀌지 않음 → 감정만 API, 음높이·속도는 ffmpeg
        modes = [_TTS_MODE["m"]] if _TTS_MODE["m"] else ["ffmpeg", "plain"]
        for m in modes:
            body = dict(base)
            if m == "api": body["output"] = {"audio_format": "mp3", "audio_pitch": int(round(semis)), "audio_tempo": tempo}
            else: body["output"] = {"audio_format": "mp3"}
            if m == "plain": body.pop("prompt", None)
            try: open(mp3, "wb").write(_tts_call(body)); done = m; _TTS_MODE["m"] = m; break
            except urllib.error.HTTPError as e: print("음성 방식", m, "거절", e.code, e.read()[:160], flush=True)
        if not done: raise RuntimeError("음성 실패: " + text[:40])
        if done == "api": af = "anull"
        else:
            r = 2 ** (semis / 12); af = f"asetrate={SR}*{r:.5f},aresample={SR},atempo={tempo / r:.5f}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-af", af, "-ac", "1", "-ar", str(SR), wav], check=True)
        try:
            sys.path.insert(0, os.path.join(ROOT, "scripts", "youtube", "long")); import tts; tts._log_usage(len(text))
        except Exception: pass
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).copy()
    idx = np.where(np.abs(x) > 0.012)[0]
    if len(idx): x = x[max(0, idx[0] - int(.03 * SR)): idx[-1] + int(.06 * SR)]
    return x


# ---------------- 효과음 (합성) ----------------
def sfx(kind):
    t = np.arange(int(SR * {"pop": .09, "whoosh": .35, "thud": .5, "chime": .9, "tick": .03, "ding": .5}[kind])) / SR
    rng = np.random.default_rng(len(kind))
    if kind == "pop":
        f = 520 + 900 * t / t[-1]; y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 40) * .55
    elif kind == "whoosh":
        n = rng.standard_normal(len(t)); k = np.hanning(len(t)); y = np.convolve(n, np.ones(30) / 30, "same") * k * .5
    elif kind == "thud":
        y = (np.sin(2 * np.pi * 70 * t) * np.exp(-t * 9) + rng.standard_normal(len(t)) * np.exp(-t * 40) * .35) * .9
    elif kind == "chime":
        y = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in ((1318, 4), (1976, 5), (2637, 7))) * .18
    elif kind == "tick":
        y = np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 200) * .3
    else:  # ding
        y = (np.sin(2 * np.pi * 1568 * t) + .5 * np.sin(2 * np.pi * 2349 * t)) * np.exp(-t * 6) * .3
    return y.astype(np.float32)


def music_track(name, total):
    """릴리스 side-assets 의 음악을 받아 total 초로 이어 붙인다"""
    if not name: return None
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        try:
            if os.environ.get("GH_TOKEN"):
                subprocess.run(["gh", "release", "download", "side-assets", "-p", name, "-D", CACHE, "--clobber", "-R", REPO], check=True)
            else: return None
        except Exception as e: print("음악 못 받음", e); return None
    raw = subprocess.run(["ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", path, "-t", f"{total:.2f}", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


# ---------------- 그림 재료 ----------------
def asset(stem, exts=(".jpeg", ".jpg", ".png", ".webp")):
    for e in exts:
        p = os.path.join(GEN, stem + e)
        if os.path.exists(p): return p
    return None


_BG = {}
def bg_source(stem):
    """정지 배경: 출력보다 10% 크게 미리 키워 둔다 (카메라 이동용)"""
    if stem not in _BG:
        p = asset(stem)
        im = Image.open(p).convert("RGB") if p else Image.new("RGB", (W, H), (40, 34, 50))
        r = W / H; iw, ih = im.size
        if iw / ih > r: cw = int(ih * r); im = im.crop(((iw - cw) // 2, 0, (iw - cw) // 2 + cw, ih))
        else: ch = int(iw / r); im = im.crop((0, (ih - ch) // 2, iw, (ih - ch) // 2 + ch))
        im = im.resize((int(W * 1.1), int(H * 1.1)), Image.LANCZOS)
        _BG.clear(); _BG[stem] = im
    return _BG[stem]


def ken_burns(src, move, p):
    """p: 0→1 장면 진행. 1.0~1.1배 사이에서 밀고 당기기"""
    p = p * p * (3 - 2 * p)  # 부드럽게
    z0, z1, dx, dy = {"in": (1.0, 1.1, 0, 0), "out": (1.1, 1.0, 0, 0), "left": (1.08, 1.08, 1, 0), "right": (1.08, 1.08, -1, 0),
                      "up": (1.08, 1.08, 0, 1), "down": (1.08, 1.08, 0, -1)}.get(move or "in", (1.0, 1.1, 0, 0))
    z = z0 + (z1 - z0) * p
    sw, sh = src.size; cw, ch = W * 1.1 / z, H * 1.1 / z
    fx = .5 + dx * (p - .5) * .9; fy = .5 + dy * (p - .5) * .9
    x0 = (sw - cw) * fx; y0 = (sh - ch) * fy
    return src.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


class Footage:
    """AI 영상 배경: 정방향+역방향을 이어 끊김 없이 반복"""
    def __init__(self, stem, dur):
        src = os.path.join(GEN, stem + ".mp4"); pp = os.path.join(CACHE, f"{stem}_{W}x{H}_pp.mp4")
        if not os.path.exists(pp):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex",
                            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1[v]",
                            "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", pp], check=True)
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", pp, "-t", f"{dur + 1:.2f}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL); self.last = None
    def frame(self):
        b = self.p.stdout.read(W * H * 3)
        if len(b) == W * H * 3: self.last = Image.frombytes("RGB", (W, H), b)
        return self.last.copy() if self.last else Image.new("RGB", (W, H))
    def close(self):
        try: self.p.stdout.close(); self.p.kill()
        except Exception: pass


_HOST = {}
def host_img(pose, height=None):
    height = height or L["host_h"]
    k = (pose, height)
    if k not in _HOST:
        p = os.path.join(CUT, pose + ".png")
        if not os.path.exists(p): p = os.path.join(CUT, "c1_magpie.png")
        im = Image.open(p).convert("RGBA"); r = height / im.height
        _HOST[k] = im.resize((max(1, int(im.width * r)), height), Image.LANCZOS)
    return _HOST[k]


def shadow_blob(w):
    im = Image.new("RGBA", (w, 50), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 10, w, 46), fill=(0, 0, 0, 90)); return im.filter(ImageFilter.GaussianBlur(8))


# ---------------- 소품 카드 ----------------
def wrap(text, font, maxw):
    words, lines, cur = text.split(), [], ""
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w_
    if cur: lines.append(cur)
    return lines


def card_comment(pop, seed):
    """휴대폰 알림 같은 댓글 카드 (번역문 굵게, 원문은 작게)"""
    cw, pad = 640, 30
    f1, f2, f3 = FB(40), FKR(25), FB(26, "Bold")   # 원문(한글·러시아어)은 Noto 로
    lines = wrap(pop["text"], f1, cw - pad * 2)
    orig = wrap(pop["orig"], f2, cw - pad * 2)[:2] if pop.get("orig") else []
    h = pad + 46 + len(lines) * 48 + (len(orig) * 34 + 8 if orig else 0) + 54 + pad - 10
    im = Image.new("RGBA", (cw + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((20, 26, cw + 20, h + 26), 30, fill=(0, 0, 0, 110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im); d.rounded_rectangle((20, 20, cw + 20, h + 20), 30, fill=WHITE)
    rnd = random.Random(seed); col = rnd.choice([(255, 99, 72), (52, 152, 219), (46, 204, 113), (155, 89, 182), (241, 196, 15)])
    d.ellipse((20 + pad, 20 + pad - 4, 20 + pad + 40, 20 + pad + 36), fill=col)
    d.text((20 + pad + 20, 20 + pad + 16), (pop.get("who") or "?")[0].upper(), font=FB(26), fill=WHITE, anchor="mm")
    d.text((20 + pad + 54, 20 + pad + 16), pop.get("src", "YouTube comment"), font=f3, fill=MUTE, anchor="lm")
    y = 20 + pad + 46
    for ln in lines: d.text((20 + pad, y), ln, font=f1, fill=INK); y += 48
    if orig:
        y += 4
        for ln in orig: d.text((20 + pad, y), ln, font=f2, fill=(150, 140, 134)); y += 34
    y += 12
    d.text((20 + pad, y), "♥", font=FCJK(30), fill=(235, 64, 82)); d.text((20 + pad + 38, y + 2), str(pop.get("likes", "")), font=f3, fill=MUTE)
    return im.rotate(rnd.uniform(-3.5, 3.5), resample=Image.BICUBIC, expand=True)


def card_stamp(text):
    f = FB(150); d0 = ImageDraw.Draw(Image.new("RGB", (8, 8))); tw = int(d0.textlength(text, font=f))
    im = Image.new("RGBA", (tw + 120, 250), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, tw + 110, 240), 26, outline=RED + (235,), width=16)
    d.text(((tw + 120) // 2, 132), text, font=f, fill=RED + (235,), anchor="mm")
    return im.rotate(-12, resample=Image.BICUBIC, expand=True)


def card_glyph(text):
    cjk = any(ord(c) > 0x2E80 for c in text)
    f = FCJK(300) if cjk else FB(230)
    d0 = ImageDraw.Draw(Image.new("RGB", (8, 8))); tw = int(d0.textlength(text, font=f))
    im = Image.new("RGBA", (tw + 200, 460), (0, 0, 0, 0))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(glow).text((im.width // 2, 230), text, font=f, fill=(255, 190, 60, 200), anchor="mm")
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(26)))
    ImageDraw.Draw(im).text((im.width // 2, 230), text, font=f, fill=(255, 236, 170), anchor="mm", stroke_width=6, stroke_fill=(120, 60, 10))
    return im


def card_tag(text):
    f = FB(92); d0 = ImageDraw.Draw(Image.new("RGB", (8, 8))); tw = int(d0.textlength(text, font=f))
    im = Image.new("RGBA", (tw + 170, 190), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(10, 95), (60, 20), (tw + 160, 20), (tw + 160, 170), (60, 170)], fill=(255, 214, 64), outline=(120, 80, 10))
    d.ellipse((44, 82, 70, 108), fill=(0, 0, 0, 0), outline=(120, 80, 10), width=4)
    d.text((85 + tw // 2, 100), text, font=f, fill=INK, anchor="mm")
    return im


def card_chip(text):
    f = FF(38); d0 = ImageDraw.Draw(Image.new("RGB", (8, 8))); tw = int(d0.textlength(text, font=f))
    im = Image.new("RGBA", (tw + 60, 74), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw + 60, 74), 37, fill=(20, 18, 30, 200)); d.text((30, 37), text, font=f, fill=WHITE, anchor="lm")
    return im


def card_count(val, label):
    f, f2 = FB(110), FB(40, "Bold")
    s = f"{int(val):,}"
    d0 = ImageDraw.Draw(Image.new("RGB", (8, 8))); tw = max(int(d0.textlength(s, font=f)), int(d0.textlength(label, font=f2))) + 80
    im = Image.new("RGBA", (tw, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw, 200), 30, fill=(255, 255, 255, 235))
    d.text((tw // 2, 82), s, font=f, fill=RED, anchor="mm"); d.text((tw // 2, 160), label, font=f2, fill=INK, anchor="mm")
    return im


# ---------------- 자막 ----------------
def word_times(words, t0, t1):
    wts = [len(w) + 2 + (3 if w[-1] in ",.?!;:" else 0) for w in words]; s = sum(wts); out, t = [], t0
    for w, k in zip(words, wts):
        d = (t1 - t0) * k / s; out.append((w, t, t + d)); t += d
    return out


def chunks_of(wt):
    out, cur = [], []
    for item in wt:
        cur.append(item)
        if len(cur) >= 5 or sum(len(x[0]) + 1 for x in cur) > 28 or item[0][-1] in ".?!": out.append(cur); cur = []
    if cur: out.append(cur)
    return out


def norm(w): return "".join(c for c in w.lower() if c.isalnum() or c in "'$")


SUB_STYLE = {"s": "pill"}


def draw_sub(base, chunk, t, hl, until, style=None):
    """자막 3가지: pill(반투명 둥근 바탕 + 형광펜 핵심어, 기본) / clean(바탕 없이 그림자) / card(흰 카드 + 빨강 핵심어)
    아직 안 읽은 단어는 흐리게 미리 보이고, 읽는 순간 밝아지며 살짝 튄다"""
    if not chunk or t < chunk[0][1] - .02 or t > until: return
    style = style or SUB_STYLE["s"]
    size = L["sub_size"] - 6; d0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    while True:
        f = FP(size, "Bold"); sp = size * .42
        widths = [d0.textlength(w, font=f) for w, _, _ in chunk]; tot = sum(widths) + sp * (len(chunk) - 1)
        if tot <= L["sub_w"] or size <= 40: break
        size -= 3
    padx, pady = int(size * .55), int(size * .32); bh = int(size * 1.3) + pady * 2
    im = Image.new("RGBA", (int(tot) + padx * 2 + 20, bh + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if style == "pill": d.rounded_rectangle((10, 10, 10 + tot + padx * 2, 10 + bh), bh // 2, fill=(18, 16, 28, 175))
    elif style == "card": d.rounded_rectangle((10, 10, 10 + tot + padx * 2, 10 + bh), 22, fill=(255, 255, 255, 240))
    x = 10 + padx; yb = 10 + pady + int(size * 1.02)
    for (w, a, b), wd in zip(chunk, widths):
        said = t >= a - .02; key = norm(w) in hl
        if said and key and style != "clean":
            col_bg = YEL if style == "pill" else (255, 226, 222)
            d.rounded_rectangle((x - 8, 10 + pady + int(size * .12), x + wd + 8, 10 + pady + int(size * 1.28)), 12, fill=col_bg + (255,))
        if style == "card": col = (RED if key else INK) + ((255,) if said else (90,))
        elif style == "pill": col = (INK + (255,)) if (said and key) else (WHITE + ((255,) if said else (110,)))
        else: col = (YEL if key else WHITE) + ((255,) if said else (120,))
        fs = f
        if said and t - a < .1: fs = FP(size * (1 + .08 * (1 - (t - a) / .1)), "Bold")
        if style == "clean": d.text((x + wd / 2 + 3, yb + 4), w, font=fs, fill=(0, 0, 0, 150 if said else 60), anchor="ms")
        d.text((x + wd / 2, yb), w, font=fs, fill=col, anchor="ms")
        x += wd + sp
    if style == "clean": im = im.filter(ImageFilter.SMOOTH)
    base.paste(im, (int((W - im.width) / 2), int(L["sub_y"] - bh * .8)), im)


# ---------------- 타임라인 ----------------
def tts_text(text, spec):
    """화면 자막은 그대로, 성우에게만 읽는 법을 바꿔 준다 (예: Orion → Oh-ree-on)"""
    for k, v in (spec.get("say_map") or {}).items():
        text = re.sub(r"(?<![\w-])" + re.escape(k) + r"(?![\w-])", v, text)
    return text


def align(audio, lines, t0):
    """장면을 한 번에 녹음 → 문장 경계는 소리가 끊기는 곳에 맞추고, 문장 안 단어는 글자 수 비례로 나눈다"""
    sents = []
    for li, ln in enumerate(lines):
        cur = []
        for w in ln.split():
            cur.append(w)
            if w[-1] in ".?!": sents.append((li, cur)); cur = []
        if cur: sents.append((li, cur))
    n = len(sents); d = len(audio) / SR; hop = int(.01 * SR)
    e = np.array([np.sqrt(np.mean(audio[i:i + hop] ** 2)) for i in range(0, max(1, len(audio) - hop), hop)]) if len(audio) > hop else np.zeros(1)
    thr = max(.006, float(np.percentile(e, 25)) * .7) if len(e) > 10 else .006
    quiet = e < thr; gaps = []; i = 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if (j - i) * .01 >= .08 and i > 0 and j < len(quiet): gaps.append((i * .01, j * .01))
            i = j
        else: i += 1
    chars = [sum(len(w) + 1 for w in s_[1]) for s_ in sents]; tot = max(1, sum(chars))
    bounds, used, c = [], -1, 0
    for k in range(n - 1):
        c += chars[k]; x = d * c / tot; best = None
        for gi in range(used + 1, len(gaps)):
            m = (gaps[gi][0] + gaps[gi][1]) / 2
            if best is None or abs(m - x) < abs((gaps[best][0] + gaps[best][1]) / 2 - x): best = gi
        if best is not None and abs((gaps[best][0] + gaps[best][1]) / 2 - x) < 1.6: used = best; bounds.append(gaps[best])
        else: bounds.append((x, x))
    out = [[] for _ in lines]; st = 0.0
    for k, (li, ws) in enumerate(sents):
        en = bounds[k][0] if k < n - 1 else d
        out[li] += word_times(ws, t0 + st + .02, t0 + max(st + .2, en) - .03)
        st = bounds[k][1] if k < n - 1 else d
    return [{"t0": wt[0][1], "t1": wt[-1][2], "chunks": chunks_of(wt)} for wt in out if wt]


def build(spec):
    v = spec["voice"]; t = 0.5; segs, audio_parts, sfx_ev = [], [], []
    for si, sc in enumerate(spec["scenes"]):
        st = t
        if si: sfx_ev.append((st, "whoosh"))
        a = say(tts_text(" ".join(sc["lines"]), spec), v)
        audio_parts.append((t, a)); lines = align(a, sc["lines"], t)
        t += len(a) / SR + .55
        segs.append({"st": st, "en": max(t, st + 2.4), "lines": lines}); t = segs[-1]["en"]
    total = t + 1.2
    side = "right"
    for sc, sg in zip(spec["scenes"], segs):
        sg["pops"] = []
        for k, p in enumerate(sc.get("pops", [])):
            li = min(int(p.get("at", 0)), len(sg["lines"]) - 1) if sg["lines"] else 0
            at = (sg["lines"][li]["t0"] if sg["lines"] else sg["st"]) + float(p.get("dt", 0.15))
            sg["pops"].append(dict(p, t=at, k=k))
            sfx_ev.append((at, {"stamp": "thud", "glyph": "chime", "count": "ding"}.get(p["kind"], "pop")))
        h = sc.get("host") or {"pose": "h_talk", "side": side}   # 운영자: 까치는 처음부터 끝까지 나온다
        side = h.get("side", side); sg["side"] = side
        sg["host"] = [(sg["st"], h["pose"])]
        for li, pose in h.get("then", []):
            if li < len(sg["lines"]): sg["host"].append((sg["lines"][li]["t0"], pose))
    prev = None
    for sg in segs:
        for tt, pose in sg["host"]:
            if pose != prev: sfx_ev.append((tt, "pop"))
            prev = pose
    return segs, audio_parts, sfx_ev, total


def mix(audio_parts, sfx_ev, total, music):
    n = int(total * SR) + SR; voice = np.zeros(n, np.float32)
    for t, a in audio_parts:
        i = int(t * SR); voice[i:i + len(a)] += a[:max(0, n - i)]
    fx = np.zeros(n, np.float32)
    for t, k in sfx_ev:
        s = sfx(k); i = int(t * SR); fx[i:i + len(s)] += s[:max(0, n - i)] * .5
    env = np.abs(voice); win = int(.25 * SR)
    env = np.convolve(env, np.ones(win) / win, "same"); speaking = (env > .01).astype(np.float32)
    duck = np.convolve(speaking, np.ones(int(.3 * SR)) / int(.3 * SR), "same")
    out = voice * 1.0 + fx
    if music is not None and len(music):
        m = np.zeros(n, np.float32); m[:min(n, len(music))] = music[:n]
        fade = np.ones(n, np.float32); fl = int(2 * SR); fade[:fl] = np.linspace(0, 1, fl); end = int(total * SR); fade[end - fl:end] = np.linspace(1, 0, fl); fade[end:] = 0
        out += m * (.20 - .12 * duck) * fade
    peak = np.max(np.abs(out)) or 1; out = out / peak * .89
    # 진행자 들썩임용 프레임별 음량
    fr = int(total * FPS) + 2; hop = SR // FPS
    vf = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) if i * hop < n else 0 for i in range(fr)])
    vf = vf / (np.percentile(vf[vf > 0], 95) if np.any(vf > 0) else 1)
    return out, np.clip(vf, 0, 1.2)


# ---------------- 렌더 ----------------
LONG = {"W": 1920, "H": 1080, "sub_size": 62, "sub_w": 1000, "sub_y": 1000, "host_h": 440, "feet": 30, "edge": 60,
        "slots": [(70, 300), (1850, 60), (1850, 330)], "count_y": 70, "logo": (24, 18), "chip_y": 230}
VERT = {"W": 1080, "H": 1920, "sub_size": 76, "sub_w": 960, "sub_y": 1080, "host_h": 520, "feet": 230, "edge": 30,
        "slots": [(40, 420), (1040, 700)], "count_y": 300, "logo": (32, 120), "chip_y": 280}
FLY_FACES = "left"   # h_fly 그림이 바라보는 쪽 (날아가는 방향이 반대면 좌우 뒤집음)
L = dict(LONG)


def logo_badge(brand=None):
    """왼쪽 위 고정 로고 (2026-10-27 확정: 까치가 가리키는 큰 Korea + What + 'says!' 말풍선) + 오늘의 브랜드 줄"""
    lp = os.path.join(GEN, "brand_logo_main.png")
    lg = Image.open(lp).convert("RGBA")
    tw = 380 if W > H else 400
    lg = lg.resize((tw, int(lg.height * tw / lg.width)), Image.LANCZOS)
    if not brand: return lg
    fb = FP(24, "Bold"); d0 = ImageDraw.Draw(Image.new("RGB", (8, 8))); bw = int(d0.textlength(brand, font=fb))
    im = Image.new("RGBA", (max(lg.width, bw + 90), lg.height + 52), (0, 0, 0, 0)); im.alpha_composite(lg, (0, 0))
    d = ImageDraw.Draw(im); y = lg.height + 4
    d.rounded_rectangle((14, y, 14 + bw + 58, y + 42), 21, fill=(255, 255, 255, 235))
    d.ellipse((28, y + 13, 44, y + 29), fill=RED); d.text((54, y + 21), brand, font=fb, fill=INK, anchor="lm")
    return im


def zoomc(img, z):
    if z <= 1.001: return img
    cw, ch = W / z, H / z; x0, y0 = (W - cw) / 2, (H - ch) / 2
    return img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


def has_pose(p): return os.path.exists(os.path.join(CUT, p + ".png"))


def set_layout(lay):
    global W, H
    L.clear(); L.update(lay); W, H = lay["W"], lay["H"]; _BG.clear(); _HOST.clear()


def write_srt(segs, path):
    """유튜브 자막 파일(SRT): 화면 자막과 같은 묶음·같은 타이밍"""
    ts = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round((x % 1) * 1000)) % 1000:03d}"
    items = [(ch[0][1], ch[-1][2], " ".join(w for w, _, _ in ch)) for sg in segs for ln in sg["lines"] for ch in ln["chunks"]]
    out = []
    for i, (a, b, txt) in enumerate(items):
        nxt = items[i + 1][0] if i + 1 < len(items) else b + .5
        out.append(f"{i + 1}\n{ts(max(0, a - .05))} --> {ts(min(b + .25, nxt - .01))}\n{txt}\n")
    open(path, "w", encoding="utf-8").write("\n".join(out))


def render(sid):
    sys.path.insert(0, HERE); from progress import report
    spec = json.load(open(os.path.join(HERE, "specs2", sid + ".json"), encoding="utf-8"))
    JID = "render-" + sid; LBL = "롱폼 렌더 · " + spec["title"]
    report(JID, LBL, pct=1, detail="내레이션 녹음 중")
    od = os.path.join(OUT, sid); os.makedirs(od, exist_ok=True)
    set_layout(LONG)
    segs, parts, sfx_ev, total = build(spec)
    write_srt(segs, os.path.join(od, "subtitles_en.srt"))
    report(JID, LBL, pct=12, detail=f"녹음 끝 · 길이 {int(total // 60)}분 {int(total % 60)}초 · 화면 그리는 중")
    vid = os.path.join(od, "_long.mp4")
    draw_video(spec, sid, segs, parts, sfx_ev, total, vid, lambda f, msg: report(JID, LBL, pct=12 + 74 * f, detail=msg, every=20))
    # 챕터
    chapters, last = [], -99
    for sc, sg in zip(spec["scenes"], segs):
        if sc.get("chapter") and sg["st"] - last > 10:
            s = 0 if not chapters else int(sg["st"]); chapters.append(f"{s // 60}:{s % 60:02d} {sc['chapter']}"); last = sg["st"]
    if spec.get("test"): return {"video": vid, "short": None, "total": total, "chapters": "\n".join(chapters)}
    report(JID, LBL, pct=87, detail="썸네일 만드는 중")
    thumb(spec, os.path.join(od, "thumb.jpg"))
    report(JID, LBL, pct=88, detail="세로 쇼츠 그리는 중")
    try: short = render_short(spec, sid, od, lambda f, msg: report(JID, LBL, pct=88 + 7 * f, detail="쇼츠 " + msg, every=20))
    except Exception as e: print("쇼츠 실패", e); short = None
    set_layout(LONG)
    return {"video": vid, "short": short, "total": total, "chapters": "\n".join(chapters)}


def render_short(spec, sid, od, prog):
    """세로 쇼츠 (57초 이하): short:true 장면만 골라 세로 화면으로 다시 그린다 — 같은 녹음(캐시) 사용"""
    pick, tot = [], 0.0
    cand = [sc for sc in spec["scenes"] if sc.get("short")]
    set_layout(VERT)
    for sc in cand:
        d = build(dict(spec, scenes=[sc]))[3] - 1.7
        if tot + d > 55: continue
        pick.append(sc); tot += d
    if not pick: return None
    sp = dict(spec, scenes=[dict(sc) for sc in pick])
    sp["scenes"][-1] = dict(sp["scenes"][-1], chip="Full story on our channel!")
    segs, parts, sfx_ev, total = build(sp)
    out = os.path.join(od, "short.mp4")
    draw_video(sp, sid + "-short", segs, parts, sfx_ev, total, out, prog)
    return out


def draw_video(spec, sid, segs, parts, sfx_ev, total, vid, prog):
    od = os.path.dirname(vid)
    audio, venv = mix(parts, sfx_ev, total, music_track(spec.get("music"), total))
    wav = os.path.join(od, "_audio.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le", wav], input=audio.astype(np.float32).tobytes(), check=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", vid],
                           stdin=subprocess.PIPE)
    nfr = int(total * FPS); prev_last = None; host_state = {"pose": None, "since": -9, "side": None, "x": None}
    LOGO = logo_badge(spec.get("brand_tag"))
    srt = []
    for sc, sg in zip(spec["scenes"], segs):
        for ln in sg["lines"]:
            for ch in ln["chunks"]: srt.append((ch[0][1], ch[-1][2] + .15, " ".join(w for w, _, _ in ch)))
    hl_all = [{norm(w) for w in sc.get("hl", [])} for sc in spec["scenes"]]
    all_lines = [(si_, ln) for si_, sg_ in enumerate(segs) for ln in sg_["lines"]]   # 자막 겹침 방지: 한 번에 한 줄만
    si = 0; foot = None; cards = {}
    for fi in range(nfr):
        t = fi / FPS
        while si < len(segs) - 1 and t >= segs[si + 1]["st"]:
            si += 1
            if foot: foot.close(); foot = None
            cards = {}
        sc, sg = spec["scenes"][si], segs[si]
        if sc.get("vid") and os.path.exists(os.path.join(GEN, sc["vid"] + ".mp4")):
            if foot is None: foot = Footage(sc["vid"], sg["en"] - sg["st"] + 2)
            base = zoomc(foot.frame(), 1 + .06 * min(1, max(0, (t - sg["st"]) / max(.1, sg["en"] - sg["st"]))))   # 영상도 천천히 당긴다
        else:
            p = (t - sg["st"]) / max(.1, (sg["en"] - sg["st"]))
            base = ken_burns(bg_source(sc["bg"]), sc.get("move"), min(1, max(0, p)))
        # 장면 전환: 앞 장면 속으로 빨려 들어가듯 확대되며 다음 장면이 당겨져 나온다 (0.45초)
        age = t - sg["st"]
        if si and age < .45 and prev_last is not None:
            e_ = age / .45; e_ = e_ * e_ * (3 - 2 * e_)
            base = Image.blend(zoomc(prev_last, 1 + .35 * e_), zoomc(base, 1.18 - .18 * e_), e_)
        # 흔들림 (도장)
        shake = 0
        for pp in sg["pops"]:
            if pp["kind"] == "stamp" and 0 <= t - pp["t"] < .35: shake = int(16 * (1 - (t - pp["t"]) / .35))
        if shake:
            base = base.transform(base.size, Image.AFFINE, (1, 0, random.randint(-shake, shake), 0, 1, random.randint(-shake, shake)), resample=Image.BILINEAR)
        # 장소 표지 (없으면 로고만)
        if not (sc.get("chip") and age < 5.5): base.paste(LOGO, L["logo"], LOGO)
        if sc.get("chip") and age < 5.5:
            if "chip" not in cards: cards["chip"] = card_chip(sc["chip"])
            c = cards["chip"]; k = ease_out(age / .4) if age < 5.1 else 1 - ease_out((age - 5.1) / .4)
            base.paste(c, (int(-c.width + (L["edge"] + 10 + c.width) * k), L["chip_y"]), c)
        base.paste(LOGO, L["logo"], LOGO)
        # 소품
        slot = 0
        for pp in sg["pops"]:
            a = t - pp["t"]
            key = ("p", pp["k"])
            if pp["kind"] == "comment":
                pos = L["slots"][slot % len(L["slots"])]; slot += 1
                if sc.get("chip") and pos == L["slots"][0]: pos = (pos[0], pos[1] + 60)
            if a < 0 or t > sg["en"] - .05: continue
            if key not in cards:
                kd = pp["kind"]
                cards[key] = (card_comment(pp, sid + str(si) + str(pp["k"])) if kd == "comment" else card_stamp(pp["text"]) if kd == "stamp"
                              else card_glyph(pp["text"]) if kd == "glyph" else card_tag(pp["text"]) if kd == "tag" else None)
            c = cards[key]; out_k = 1 - ease_out((t - (sg["en"] - .3)) / .25) if t > sg["en"] - .3 else 1
            if pp["kind"] == "count":
                val = pp["to"] * ease_out(a / 1.6); c = card_count(val, pp.get("label", ""))
                s = ease_back(a / .3) * out_k
            elif pp["kind"] == "stamp": s = (2.3 - 1.3 * ease_out(a / .16)) * out_k
            else: s = ease_back(a / .3) * out_k
            if s <= .02: continue
            cw, ch = max(1, int(c.width * s)), max(1, int(c.height * s)); ci = c.resize((cw, ch), Image.BILINEAR)
            if pp["kind"] == "comment":
                x = pos[0] if pos[0] < W / 2 else pos[0] - cw; y = pos[1]
            elif pp["kind"] == "count": x, y = (W - cw) // 2, L["count_y"]
            else:
                fx_, fy_ = pp.get("x", .5), pp.get("y", .42)
                bob = math.sin(a * 2.2) * 8 if pp["kind"] in ("glyph", "tag") else 0
                x, y = int(W * fx_ - cw / 2), int(H * fy_ - ch / 2 + bob)
            if pp["kind"] == "stamp" and a < .16:
                ci.putalpha(ci.getchannel("A").point(lambda v_: int(v_ * min(1, a / .1))))
            base.paste(ci, (int(x), int(y)), ci)
        # 진행자 까치: 처음엔 오른쪽 밖에서 날아 들어오고, 장면마다 정한 쪽(side)으로 날아가 앉는다
        hs = [p for p in sg["host"] if p[0] <= t] or sg["host"][:1]
        pose = hs[-1][1]; side = sg.get("side", "right")
        hi0 = host_img(pose)
        tx = W - L["edge"] - hi0.width // 2 if side == "right" else L["edge"] + hi0.width // 2
        if host_state["x"] is None: host_state.update(x=W + 320, fx0=W + 320, ftx=tx, fstart=.15, side=side)
        if side != host_state["side"]: host_state.update(side=side, fx0=host_state["x"], ftx=tx, fstart=t)
        fp = (t - host_state["fstart"]) / .9
        e = float(venv[min(fi, len(venv) - 1)])
        if fp < 1:
            q = fp * fp * (3 - 2 * fp); x = host_state["fx0"] + (host_state["ftx"] - host_state["fx0"]) * q
            yoff = -150 * math.sin(math.pi * fp); flying = True
        else:
            x = tx + 14 * math.sin(t * 2 * math.pi / 6.5); yoff = 0; flying = False
        host_state["x"] = x
        if flying and has_pose("h_fly"):
            nm = "h_fly2" if (fi // 4) % 2 and has_pose("h_fly2") else "h_fly"; hi = host_img(nm)
            going_left = host_state["ftx"] < host_state["fx0"]
            if (FLY_FACES == "right") == going_left: hi = hi.transpose(Image.FLIP_LEFT_RIGHT)
            sx = sy = 1.0
        else:
            if pose != host_state["pose"]: host_state.update(pose=pose, since=hs[-1][0] if hs[-1][0] > host_state["fstart"] + .9 else t)
            nm = pose
            if has_pose(pose + "_b") and ((t + (hash(pose) % 7) * .5) % 3.7) < .13: nm = pose + "_b"        # 눈 깜빡임
            elif has_pose(pose + "_c") and not (e > .22 and (fi // 3) % 2 == 0): nm = pose + "_c"           # 말할 때 부리 열고 닫기
            hi = host_img(nm); ha = t - host_state["since"]
            sc_in = ease_back(ha / .3) if ha < .3 else 1.0
            sy = (1 + .035 * e) * sc_in; sx = (1 - .015 * e) * sc_in
        if sy > .03:
            hw, hh = int(hi.width * sx), int(hi.height * sy); im = hi.resize((max(1, hw), max(1, hh)), Image.BILINEAR)
            ang = (8 if flying else 1.8) * math.sin(t * 2 * math.pi / (0.9 if flying else 2.6))
            im = im.rotate(ang, resample=Image.BICUBIC, expand=True)
            bob = int(6 * math.sin(t * 2 * math.pi / 1.5)) + int(yoff)
            feet = H - L["feet"]
            if not flying:
                shb = shadow_blob(int(hi0.width * .7 * sx) or 1); base.paste(shb, (int(x) - shb.width // 2, feet - 30), shb)
            base.paste(im, (int(x - im.width / 2), int(feet - hh + bob - (im.height - hh) / 2)), im)
        # 자막: 지금 시각 직전에 시작한 줄 하나만 (다음 줄이 시작되면 앞 줄은 바로 사라진다)
        cur = None
        for k_, (si_, ln) in enumerate(all_lines):
            if ln["t0"] - .05 <= t: cur = k_
            else: break
        if cur is not None:
            si_, ln = all_lines[cur]
            end_ln = ln["t1"] + .3
            if cur + 1 < len(all_lines): end_ln = min(end_ln, all_lines[cur + 1][1]["t0"] - .06)
            if t <= end_ln:
                for ci_, ch in enumerate(ln["chunks"]):
                    nxt = ln["chunks"][ci_ + 1][0][1] if ci_ + 1 < len(ln["chunks"]) else end_ln
                    if ch[0][1] - .02 <= t < nxt: draw_sub(base, ch, t, hl_all[si_], nxt, spec["scenes"][si_].get("sub_style") or spec.get("sub_style"))
        enc.stdin.write(base.tobytes())
        if t >= sg["en"] - 1 / FPS - 1e-6: prev_last = base
        if fi % (FPS * 30) == 0: print(f"  {sid} {t / 60:.1f}분 / {total / 60:.1f}분", flush=True)
        if fi % (FPS * 5) == 0: prog(fi / max(1, nfr), f"화면 {int(t // 60)}:{int(t % 60):02d} / {int(total // 60)}:{int(total % 60):02d}")
    if foot: foot.close()
    enc.stdin.close(); enc.wait()
    os.remove(wav)


def thumb(spec, path):
    set_layout(LONG)
    th = spec.get("thumb", {})
    im = ken_burns(bg_source(th.get("bg", spec["scenes"][0]["bg"])), "in", .6).convert("RGBA")
    # 왼쪽 어둡게 (글자 자리)
    g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g)
    for x in range(W): gd.line([(x, 0), (x, H)], fill=int(170 * max(0, 1 - x / (W * .55))))
    im.paste(Image.new("RGBA", (W, H), (10, 8, 20, 255)), (0, 0), g)
    if th.get("stamp"):
        c = card_stamp(th["stamp"]).resize((int(card_stamp(th["stamp"]).width * 1.2), int(card_stamp(th["stamp"]).height * 1.2)))
        im.paste(c, (int(W * th.get("stamp_x", .66) - c.width / 2), int(H * th.get("stamp_y", .5) - c.height / 2)), c)
    hp = os.path.join(CUT, th.get("pose", "c1_surprised") + ".png")
    if os.path.exists(hp):
        h = Image.open(hp).convert("RGBA"); r = 760 / h.height; h = h.resize((int(h.width * r), 760), Image.LANCZOS)
        im.paste(h, (int(W * th.get("host_x", .02)), H - 760 + 40), h)
    d = ImageDraw.Draw(im)
    big = th.get("big", ""); f = FB(250)
    while d.textlength(big, font=f) > W * .62 and f.size > 120: f = FB(f.size - 10)
    bx = int(W * th.get("text_x", .40))
    d.text((bx, 120), th.get("small", ""), font=FB(96), fill=WHITE, stroke_width=10, stroke_fill=INK)
    d.text((bx, 220), big, font=f, fill=YEL, stroke_width=16, stroke_fill=INK)
    im.convert("RGB").resize((1280, 720), Image.LANCZOS).save(path, quality=92)


def build_description(spec, chapters):
    desc = spec["description"]
    if "{chapters}" in desc: desc = desc.replace("{chapters}", chapters)
    else: desc += "\n\nChapters\n" + chapters
    desc += "\n\nVisuals are AI-generated miniature illustrations, not real footage. Viewer comments are real, translated where needed."
    if spec.get("sources"): desc += "\n\nSources\n" + "\n".join(spec["sources"])
    return desc


def main(ids):
    sys.path.insert(0, HERE); import render as r1
    r1.build_description = build_description
    if not ids: ids = [os.path.basename(f)[:-5] for f in sorted(glob.glob(os.path.join(HERE, "specs2", "*.json")))
                       if not os.path.exists(os.path.join(OUT, os.path.basename(f)[:-5], "meta.json")) or "--all" in sys.argv]
    if "--srt" in sys.argv:   # 녹음 캐시로 타이밍만 다시 계산해 자막 파일만 만든다 (영상은 그대로)
        for sid in ids:
            spec = json.load(open(os.path.join(HERE, "specs2", sid + ".json"), encoding="utf-8"))
            set_layout(LONG); segs = build(spec)[0]; od = os.path.join(OUT, sid)
            write_srt(segs, os.path.join(od, "subtitles_en.srt"))
            mp = os.path.join(od, "meta.json"); m = json.load(open(mp)); m["subtitle"] = f"/social/side/{sid}/subtitles_en.srt"
            json.dump(m, open(mp, "w"), ensure_ascii=False, indent=1); print("자막", sid)
        r1.write_queue(); return
    for sid in ids:
        spec = json.load(open(os.path.join(HERE, "specs2", sid + ".json"), encoding="utf-8"))
        from progress import report
        try:
            res = render(sid)
            if spec.get("test"):   # 시험본: 검수 대기열에 올리지 않고 자료 릴리스에만 올린다
                stamp = dt.datetime.utcnow().strftime("%y%m%d%H%M"); name = f"test_{sid}_{stamp}.mp4"; dst = os.path.join(os.path.dirname(res["video"]), name)
                os.replace(res["video"], dst); url = None
                if os.environ.get("GH_TOKEN"):
                    subprocess.run(["gh", "release", "upload", "side-assets", dst, "--clobber", "-R", REPO], check=True)
                    url = f"https://github.com/{REPO}/releases/download/side-assets/{name}"; os.remove(dst)
                tf = os.path.join(OUT, "tests.json"); tl = json.load(open(tf)) if os.path.exists(tf) else []
                tl.insert(0, {"id": sid, "file": name, "url": url, "sec": round(res["total"], 1), "at": dt.datetime.now(dt.timezone.utc).isoformat()})
                json.dump(tl[:30], open(tf, "w"), ensure_ascii=False, indent=1)
                report("render-" + sid, status="done", pct=100, detail=f"시험본 완료 · {name}")
                continue
            report("render-" + sid, pct=96, detail="검수 대기열에 올리는 중")
            mp = os.path.join(OUT, sid, "meta.json"); keep = (json.load(open(mp)).get("thumbs") if os.path.exists(mp) else None)
            r1.publish(sid, res, spec)
            open(os.path.join(OUT, sid, "transcript_en.txt"), "w").write("\n\n".join(" ".join(x["lines"]) for x in spec["scenes"]) + "\n")
            m = json.load(open(mp)); m["transcript"] = f"/social/side/{sid}/transcript_en.txt"; m["subtitle"] = f"/social/side/{sid}/subtitles_en.srt"; json.dump(m, open(mp, "w"), ensure_ascii=False, indent=1)
            if keep:   # 따로 만든 썸네일 후보는 다시 렌더해도 유지
                m = json.load(open(mp)); m["thumbs"] = keep; json.dump(m, open(mp, "w"), ensure_ascii=False, indent=1)
            report("render-" + sid, status="done", pct=100, detail=f"완료 · {int(res['total'] // 60)}분 {int(res['total'] % 60)}초 · 검수 탭에서 확인 (몇 분 뒤 반영)")
        except Exception as e:
            report("render-" + sid, status="failed", detail="실패: " + str(e)[:200]); raise
    r1.write_queue()


if __name__ == "__main__":
    main([a for a in sys.argv[1:] if not a.startswith("--")])
