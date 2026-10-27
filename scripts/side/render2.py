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
import datetime as dt, glob, hashlib, json, math, os, random, subprocess, sys, urllib.error, urllib.request
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


def draw_sub(base, chunk, t, hl, until):
    if not chunk or t < chunk[0][1] - .02 or t > until: return
    size = L["sub_size"]; d = ImageDraw.Draw(base)
    while True:
        f = FB(size); sp = size * .34
        widths = [d.textlength(w, font=f) for w, _, _ in chunk]; tot = sum(widths) + sp * (len(chunk) - 1)
        if tot <= L["sub_w"] or size <= 44: break
        size -= 4
    x = (W - tot) / 2; y = L["sub_y"]
    for (w, a, b), wd in zip(chunk, widths):
        if t >= a - .02:
            age = t - a; s = 1.0 + .12 * max(0.0, 1 - age / .12)
            col = YEL if norm(w) in hl else WHITE
            d.text((x + wd / 2, y), w, font=FB(size * s), fill=col, anchor="ms", stroke_width=max(6, int(size * .14)), stroke_fill=INK)
        x += wd + sp


# ---------------- 타임라인 ----------------
def build(spec):
    v = spec["voice"]; t = 0.5; segs, audio_parts, sfx_ev = [], [], []
    for si, sc in enumerate(spec["scenes"]):
        st = t; lines = []
        if si: sfx_ev.append((st, "whoosh"))
        for li, line in enumerate(sc["lines"]):
            a = say(line, v); d = len(a) / SR
            audio_parts.append((t, a)); words = line.split()
            lines.append({"t0": t, "t1": t + d, "chunks": chunks_of(word_times(words, t + .02, t + d - .04))})
            t += d + (.12 if li < len(sc["lines"]) - 1 else 0)
        t += .55
        segs.append({"st": st, "en": max(t, st + 2.4), "lines": lines}); t = segs[-1]["en"]
    total = t + 1.2
    # 소품 이벤트
    for sc, sg in zip(spec["scenes"], segs):
        sg["pops"] = []
        for k, p in enumerate(sc.get("pops", [])):
            li = min(int(p.get("at", 0)), len(sg["lines"]) - 1) if sg["lines"] else 0
            at = (sg["lines"][li]["t0"] if sg["lines"] else sg["st"]) + float(p.get("dt", 0.15))
            sg["pops"].append(dict(p, t=at, k=k))
            sfx_ev.append((at, {"stamp": "thud", "glyph": "chime", "count": "ding"}.get(p["kind"], "pop")))
        h = sc.get("host")
        sg["host"] = []
        if h:
            sg["host"].append((sg["st"], h["pose"]))
            for li, pose in h.get("then", []):
                if li < len(sg["lines"]): sg["host"].append((sg["lines"][li]["t0"], pose))
    prev = None
    for sg in segs:
        for tt, pose in sg["host"]:
            if pose != prev: sfx_ev.append((tt, "pop"))
            prev = pose
        if not sg["host"]: prev = None
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
LONG = {"W": 1920, "H": 1080, "sub_size": 62, "sub_w": 1000, "sub_y": 990, "host_h": 440, "feet": 30, "edge": 60,
        "slots": [(70, 60), (1850, 60), (70, 330), (1850, 330)], "count_y": 70}
VERT = {"W": 1080, "H": 1920, "sub_size": 76, "sub_w": 960, "sub_y": 1060, "host_h": 520, "feet": 230, "edge": 30,
        "slots": [(40, 230), (1040, 560), (40, 890)], "count_y": 240}
L = dict(LONG)


def set_layout(lay):
    global W, H
    L.clear(); L.update(lay); W, H = lay["W"], lay["H"]; _BG.clear(); _HOST.clear()


def render(sid):
    sys.path.insert(0, HERE); from progress import report
    spec = json.load(open(os.path.join(HERE, "specs2", sid + ".json"), encoding="utf-8"))
    JID = "render-" + sid; LBL = "롱폼 렌더 · " + spec["title"]
    report(JID, LBL, pct=1, detail="내레이션 녹음 중")
    od = os.path.join(OUT, sid); os.makedirs(od, exist_ok=True)
    set_layout(LONG)
    segs, parts, sfx_ev, total = build(spec)
    report(JID, LBL, pct=12, detail=f"녹음 끝 · 길이 {int(total // 60)}분 {int(total % 60)}초 · 화면 그리는 중")
    vid = os.path.join(od, "_long.mp4")
    draw_video(spec, sid, segs, parts, sfx_ev, total, vid, lambda f, msg: report(JID, LBL, pct=12 + 74 * f, detail=msg, every=20))
    # 챕터
    chapters, last = [], -99
    for sc, sg in zip(spec["scenes"], segs):
        if sc.get("chapter") and sg["st"] - last > 10:
            s = 0 if not chapters else int(sg["st"]); chapters.append(f"{s // 60}:{s % 60:02d} {sc['chapter']}"); last = sg["st"]
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
    nfr = int(total * FPS); prev_last = None; host_state = {"pose": None, "since": -9, "side": None}
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
            base = foot.frame()
        else:
            p = (t - sg["st"]) / max(.1, (sg["en"] - sg["st"]))
            base = ken_burns(bg_source(sc["bg"]), sc.get("move"), min(1, max(0, p)))
        # 장면 전환: 앞 장면 마지막 화면에서 0.25초 섞기 + 살짝 당기기
        age = t - sg["st"]
        if si and age < .25 and prev_last is not None:
            base = Image.blend(prev_last, base, ease_out(age / .25))
        # 흔들림 (도장)
        shake = 0
        for pp in sg["pops"]:
            if pp["kind"] == "stamp" and 0 <= t - pp["t"] < .35: shake = int(16 * (1 - (t - pp["t"]) / .35))
        if shake:
            base = base.transform(base.size, Image.AFFINE, (1, 0, random.randint(-shake, shake), 0, 1, random.randint(-shake, shake)), resample=Image.BILINEAR)
        # 장소 표지
        if sc.get("chip") and age < 5.5:
            if "chip" not in cards: cards["chip"] = card_chip(sc["chip"])
            c = cards["chip"]; k = ease_out(age / .4) if age < 5.1 else 1 - ease_out((age - 5.1) / .4)
            base.paste(c, (int(-c.width + (L["edge"] + 10 + c.width) * k), 40 if W > H else 120), c)
        # 소품
        slot = 0
        for pp in sg["pops"]:
            a = t - pp["t"]
            key = ("p", pp["k"])
            if pp["kind"] == "comment":
                pos = L["slots"][slot % len(L["slots"])]; slot += 1
                if sc.get("chip") and pos == L["slots"][0]: pos = (pos[0], pos[1] + 80)
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
        # 진행자
        hs = [p for p in sg["host"] if p[0] <= t]
        if hs:
            pose = hs[-1][1]; side = (sc.get("host") or {}).get("side", "right")
            if pose != host_state["pose"] or side != host_state["side"]:
                host_state.update(pose=pose, since=hs[-1][0], side=side)
            hi = host_img(pose); ha = t - host_state["since"]
            e = float(venv[min(fi, len(venv) - 1)])
            sc_in = ease_back(ha / .3) if ha < .3 else 1.0
            out_k = 1 - ease_out((t - (sg["en"] - .2)) / .2) if (t > sg["en"] - .2 and si + 1 < len(segs) and not spec["scenes"][si + 1].get("host")) else 1
            sy = (1 + .045 * e) * sc_in * out_k; sx = (1 - .02 * e) * sc_in * out_k
            if sy > .03:
                hw, hh = int(hi.width * sx), int(hi.height * sy); im = hi.resize((max(1, hw), max(1, hh)), Image.BILINEAR)
                bob = int(6 * math.sin(t * 2 * math.pi / 1.5))
                cx = W - L["edge"] - hi.width // 2 if side == "right" else L["edge"] + hi.width // 2
                feet = H - L["feet"]
                shb = shadow_blob(int(hi.width * .7 * sc_in * out_k) or 1)
                base.paste(shb, (cx - shb.width // 2, feet - 30), shb)
                base.paste(im, (cx - hw // 2, feet - hh + bob), im)
        else: host_state.update(pose=None)
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
                    if ch[0][1] - .02 <= t < nxt: draw_sub(base, ch, t, hl_all[si_], nxt)
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
    for sid in ids:
        spec = json.load(open(os.path.join(HERE, "specs2", sid + ".json"), encoding="utf-8"))
        from progress import report
        try:
            res = render(sid)
            report("render-" + sid, pct=96, detail="검수 대기열에 올리는 중")
            r1.publish(sid, res, spec)
            report("render-" + sid, status="done", pct=100, detail=f"완료 · {int(res['total'] // 60)}분 {int(res['total'] % 60)}초 · 검수 탭에서 확인 (몇 분 뒤 반영)")
        except Exception as e:
            report("render-" + sid, status="failed", detail="실패: " + str(e)[:200]); raise
    r1.write_queue()


if __name__ == "__main__":
    main([a for a in sys.argv[1:] if not a.startswith("--")])
