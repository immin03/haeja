"""황제의 일기 데일리 쇼츠 — 시네마틱 고정 포맷 (2026-11-05 대표 확정)
render_ed.py 로 만든 완성본(소리 포함)을 받아 화면만 다시 짜고, 소리는 그대로 쓴다.
  python3 fx_short.py <spec_<id>a.json> <render_ed 완성본.mp4> <out.mp4> --fx <fx_<id>.json> [--platform shorts|reels]
fx_<id>.json = {"shots": [[컷0의 샷들], [컷1의 샷들], ...]}  샷 = [클립 이름, 가로 중심 0~1, 컷 안 시작 초, 속도, 하이라이트 0/1]
규칙은 FX.md. 클립 목록은 CLIPS.json.
"""
import sys, os, json, math, subprocess, tempfile, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_ed as R
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W, H, FPS = 1080, 1920, 30
G = os.path.abspath(os.path.join(HERE, "../../../social/side/gen")) + "/"
A = sys.argv
spec = json.load(open(A[1])); ORIG = A[2]; OUT = A[3]
FX = json.load(open(A[A.index("--fx") + 1]))
PLAT = A[A.index("--platform") + 1] if "--platform" in A else "shorts"
TMP = tempfile.mkdtemp(dir=os.environ.get("ED_TMP", os.path.dirname(os.path.abspath(OUT))))
LOGO = os.path.join(HERE, "assets/logo_final.png")
R.set_theme("A")
for c in spec["cuts"]:
    cs = c.get("caps") or []
    for i in range(len(cs) - 1):
        cs[i]["t1"] = min(cs[i]["t1"], cs[i + 1]["t0"] - 0.22)
xf = 0.4; starts = []; s = 0
for c in spec["cuts"]: starts.append(s); s += c["dur"] - xf
END = starts[-1] + spec["cuts"][-1]["dur"] - 0.25
PLAN = FX["shots"]
assert len(PLAN) == len(spec["cuts"]), "fx shots 개수가 컷 수와 다름"
shots = []
for k, pl in enumerate(PLAN):
    for j, (clip, cx, t0, sp, hl) in enumerate(pl):
        a = starts[k] + t0 if (k == 0 or j > 0) else starts[k] + xf / 2
        shots.append([clip, cx, a, bool(hl), sp])
for i in range(len(shots)):
    shots[i].insert(3, shots[i + 1][2] if i + 1 < len(shots) else END)   # [clip, cx, a, b, hl, speed]
def read_clip(name, cx, n, speed=0.82):
    from clip_fetch import ensure; path = ensure(G + name + ".mp4")   # 2026-11-06: 저장소에 없으면 받아 온다
    w, h = map(int, subprocess.run(["ffprobe","-v","error","-select_streams","v","-show_entries","stream=width,height","-of","csv=p=0",path],capture_output=True,text=True).stdout.strip().split(","))
    sc = H * 1.0 / h * 1.06; sw = int(w * sc) // 2 * 2; sh = int(h * sc) // 2 * 2
    cw, ch = int(W * 1.06) // 2 * 2, int(H * 1.06) // 2 * 2
    x = int(min(max(cx * sw - cw / 2, 0), sw - cw)); y = (sh - ch) // 2
    vf = f"setpts=PTS/{speed},fps={FPS},scale={sw}:{sh}:flags=lanczos,crop={cw}:{ch}:{x}:{y},eq=contrast=1.06:saturation=1.05"
    pr = subprocess.Popen(["ffmpeg","-v","error","-i",path,"-vf",vf,"-frames:v",str(n),"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
    fp = tempfile.NamedTemporaryFile(dir=TMP, delete=False).name
    arr = np.memmap(fp, np.uint8, "w+", shape=(n, ch, cw, 3)); os.unlink(fp)
    fs = cw * ch * 3; last = None
    for i in range(n):
        b = pr.stdout.read(fs)
        if len(b) < fs: arr[i] = last if last is not None else 0; continue
        last = np.frombuffer(b, np.uint8).reshape(ch, cw, 3); arr[i] = last
    pr.stdout.close(); pr.wait()
    return arr
CACHE = {}
def frames(q):
    if q not in CACHE:
        for old in list(CACHE):
            if old < q - 1: del CACHE[old]
        sh = shots[q]; n = int(math.ceil((sh[3] - sh[2] + 1.2) * FPS)) + 2
        CACHE[q] = read_clip(sh[0], sh[1], n, sh[5])
    return CACHE[q]
# 인용·강조가 뜨는 순간 (펀치)
PUNCH = []   # 하이라이트 컷의 첫 강조 글이 뜨는 순간만
for k, c in enumerate(spec["cuts"]):
    if not PLAN[k][0][4]: continue
    for b in c["texts"]:
        if b.get("style") in ("quote", "big") and b["t0"] >= 0: PUNCH.append(starts[k] + b["t0"]); break
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.45 * np.clip((np.sqrt(((xx - W/2)/(W/2))**2 + ((yy - H*0.5)/(H/2))**2) - 0.5) / 0.8, 0, 1) ** 1.5)[..., None]
GRADE = np.array([1.04, 1.0, 0.92], np.float32)
rng = np.random.default_rng(3); P = rng.random((70, 5))
def leak(a, side):
    cx = W * (0.15 if side else 0.85); cy = H * 0.3
    g = np.exp(-(((xx - cx) / 700) ** 2 + ((yy - cy) / 900) ** 2))[..., None]
    return g * np.array([255, 190, 110], np.float32) * a
def ease(x): return 0 if x <= 0 else 1 if x >= 1 else 1 - (1 - x) ** 3
def frame_at(q, t):
    clip, cx, a, b, hl, sp = shots[q]; fr = frames(q)
    u = t - a; i = min(max(int(u * FPS), 0), len(fr) - 1)
    p = min(max(u / max(b - a, 0.5), 0), 1.2)
    za = 0.05 if sp <= 0.6 else 0.08; z = 1.0 + za * (p * (2 - p) if p < 1 else 1)      # 밀고 들어가는 카메라 (슬로우 장면은 더 약하게)
    src = fr[i]; ch, cw = src.shape[:2]
    vw, vh = W * 1.16 / z / 1.0, H * 1.16 / z
    vw, vh = cw / z, ch / z
    dx = (cw - vw) / 2 + (0 if sp <= 0.6 else (cw - vw) * 0.12 * math.sin(u * 0.4 + a))   # 슬로우 장면은 좌우 흔들림 없음
    box = (dx, (ch - vh) / 2, dx + vw, (ch - vh) / 2 + vh)
    return np.asarray(Image.fromarray(src).resize((W, H), Image.BICUBIC, box=box), np.float32)
HEAD = os.path.join(TMP, "head.mp4")
enc = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-preset","veryfast","-crf","17","-pix_fmt","yuv420p",HEAD], stdin=subprocess.PIPE)
N = int(round(END * FPS))
for fi in range(N):
    t = fi / FPS
    j = max(q for q in range(len(shots)) if shots[q][2] <= t or q == 0)
    base = frame_at(j, t)
    lk = 0; hl = shots[j][4]
    TR = 0.7 if hl else (0.45 if shots[j][5] <= 0.5 else 0.12)   # 슬로우 장면은 부드럽게 섞기만                   # 평소: 짧고 깔끔한 전환 / 하이라이트: 느린 금빛 전환
    if j > 0 and t < shots[j][2] + TR:
        w = (t - shots[j][2]) / TR
        base = base * w + frame_at(j - 1, t) * (1 - w)
        if hl: lk = math.sin(w * math.pi)
    if j + 1 < len(shots) and shots[j + 1][4] and t > shots[j + 1][2] - 0.25:
        lk = max(lk, ease((t - (shots[j + 1][2] - 0.25)) / 0.25))
    pz = 0
    for pt in PUNCH:
        if 0 <= t - pt < 0.5: pz = max(pz, 1 - (t - pt) / 0.5)
    if pz > 0:   # 인용 펀치: 살짝 확대 + 흔들림 + 번쩍임
        z = 1 + 0.035 * pz; sx = 6 * pz * math.sin(t * 90); im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
        bw, bh = W / z, H / z; im = im.resize((W, H), Image.BILINEAR, box=((W - bw) / 2 + sx, (H - bh) / 2, (W + bw) / 2 + sx, (H + bh) / 2))
        base = np.asarray(im, np.float32) + 70 * pz ** 2
    base = base * GRADE * VIG
    if lk > 0: base = base + leak(0.85 * lk, j % 2)
    base = base + rng.normal(0, 7, (H // 3, W // 3, 1)).astype(np.float32).repeat(3, 0).repeat(3, 1)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    # 불티
    pl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(pl)
    for q in range(len(P)):
        sp = 40 + P[q, 2] * 110; px = (P[q, 0] * W + 40 * math.sin(t * (0.6 + P[q, 3]) + q)) % W; py = (P[q, 1] * H * 1.2 - t * sp) % (H * 1.2) - H * 0.1
        r = 1.2 + P[q, 4] * 3.2; al = int((90 + 140 * P[q, 3]) * (0.55 + 0.45 * math.sin(t * 4 + q)))
        d.ellipse([px - r, py - r, px + r, py + r], fill=(255, 170 + int(60 * P[q, 4]), 90, max(0, al)))
    img.alpha_composite(pl.filter(ImageFilter.GaussianBlur(1.3)))
    k = max(q for q in range(len(starts)) if starts[q] <= t); c = spec["cuts"][k]
    R.top_shade(img, strength=c.get("shade", 200), h=c.get("shade_h", 980))
    R.draw_block(img, [dict(b, t1=b.get("t1", 999)) for b in c["texts"]], t - starts[k], top=c.get("top", 250))
    if c.get("caps"): R.draw_caps(img, c["caps"], t - starts[k], c.get("cap_y", 1150))
    R.watermark(img)
    LAST = np.clip(base, 0, 255).astype(np.uint8)
    enc.stdin.write(img.convert("RGB").tobytes())
# ---------- 오늘의 할 일: 내레이션에 맞춰 글이 써진다 ----------
from PIL import ImageFont
E = spec["end"]; O = spec["outro"]; DELAY = 0.35   # 오늘의 할 일 내레이션 뒤 여유 (소리도 같은 만큼 늘림)
OS = END + E["dur"] + DELAY; TOT = OS + O["dur"]
OS0 = END + E["dur"]   # render_ed 완성본에서 마지막 화면이 시작되는 시각
def voiced(a, b, src=None):
    if src:   # 2026-11-08: 음악 없는 목소리 원본에서 잰다 — 음악이 섞인 완성본으로 재면 말끝을 놓쳐 ep17 재렌더가 멈췄다
        r = subprocess.run(["ffmpeg", "-v", "info", "-i", src, "-vn", "-af", "silencedetect=noise=-32dB:d=0.15", "-f", "null", "-"], capture_output=True, text=True).stderr
    else:
        r = subprocess.run(["ffmpeg", "-v", "info", "-ss", str(a), "-t", str(b - a), "-i", ORIG, "-vn", "-af", "highpass=f=250,lowpass=f=3500,silencedetect=noise=-19dB:d=0.15", "-f", "null", "-"], capture_output=True, text=True).stderr
    ev = [(l.split("silence_")[1].split(":")[0], float(l.split(": ")[1].split()[0])) for l in r.splitlines() if "silence_start" in l or "silence_end" in l]
    segs = []; cur = 0.0
    for k2, v in ev:
        if k2 == "start":
            if v > cur + 0.12: segs.append([a + cur, a + v])
        else: cur = v
    if cur < b - a - 0.12 and (not ev or ev[-1][0] == "end"): segs.append([a + cur, b])
    return segs
EV = spec["voice"][-2]   # [..., 오늘의 할 일, 슬로건]
_evd = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", EV["file"]], capture_output=True, text=True).stdout)
seg = voiced(EV["at"], EV["at"] + _evd, src=EV["file"])
T_K = seg[0] if seg else [END + .8, END + 1.5]
rest = seg[1:]; nL = len(E["lines"])
while len(rest) > nL:   # 가장 가까운 두 조각부터 합친다
    gi = min(range(len(rest) - 1), key=lambda i: rest[i + 1][0] - rest[i][1]); rest[gi] = [rest[gi][0], rest[gi + 1][1]]; del rest[gi + 1]
if rest and len(rest) < nL:   # 2026-11-08: 쉼 없이 이어 읽은 테이크 — 글자 수 비율로 나눈다 (예전엔 고정 시각으로 대체돼 소리 처리까지 어긋났다)
    a0, a1 = rest[0][0], rest[-1][1]; Ln = [max(len(x.replace(" ", "")), 1) for x in E["lines"]]; x0 = a0; rest = []
    for n in Ln:
        x1 = x0 + (a1 - a0) * n / sum(Ln); rest.append([x0, x1]); x0 = x1
T_L = rest if len(rest) == nL else [[END + 2.3, END + 4.1], [END + 4.5, END + 5.9]][:nL]
NAR_END = T_L[-1][1]
oseg = voiced(OS0 - 0.2, OS0 + spec["outro"]["dur"])
VO = {"outro": [max(0, x[0] - OS0 - 0.05) for x in oseg[:3]] + ([oseg[min(2, len(oseg) - 1)][1] - OS0 + 0.1] if oseg else [])} if len(oseg) >= 3 else {}
bgE = Image.fromarray(LAST).convert("RGBA").filter(ImageFilter.GaussianBlur(18))
def write_line(d, layer, y, txt, st, p, col):
    # 왼쪽부터 붓으로 쓰듯 드러나고, 써지는 끝에 금빛 펜촉 빛
    f = R.font(st); w = d.textlength(txt, font=f); x0 = (W - w) / 2
    if p <= 0: return
    L = Image.new("L", (W, H), 0); ImageDraw.Draw(L).text((x0, y), txt, font=f, fill=255)
    m = Image.new("L", (W, H), 0); xe = x0 + (w + 30) * p
    ImageDraw.Draw(m).rectangle([0, 0, xe, H], fill=255); m = m.filter(ImageFilter.GaussianBlur(10))
    al = Image.fromarray(np.minimum(np.array(L), np.array(m)))
    c = Image.new("RGBA", (W, H), col + (0,)); c.putalpha(al)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.putalpha(al.point(lambda v: int(v * .55))); layer.alpha_composite(sh, (2, 3)); layer.alpha_composite(c)
    if p < 1:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([xe - 26, y + 10, xe + 26, y + f.size + 6], fill=(255, 220, 150, 170))
        layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(12)))
def ease2(x): return 0 if x <= 0 else 1 if x >= 1 else x * x * (3 - 2 * x)
LG, LG_HI = (201, 164, 92), (236, 212, 160)
OUT_T = VO.get("outro", [0.0, 1.18, 2.46, 3.5])   # 매일 밤 / 황제처럼 생각하라 / 황제의 일기 / 버튼 (마지막 화면 시작 기준 초)
COIN = R._coin_gold(LOGO, 270)
def outro2(u):
    img = R._outro_bg().copy(); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    def ct(y, txt, f, col, a):
        w = d.textlength(txt, font=f); d.text(((W - w) / 2, y + int((1 - a) * 10)), txt, font=f, fill=col + (int(255 * a),))
    cx, cy, Rr = W // 2, 440, 150
    a0 = ease2(u / 0.9); ang = 360 * a0
    c2 = COIN.copy(); c2.putalpha(c2.split()[3].point(lambda v: int(v * ease(u / 1.0)))); lay.alpha_composite(c2, (cx - c2.width // 2, cy - c2.height // 2))
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
    rd.arc([cx - Rr, cy - Rr, cx + Rr, cy + Rr], -90, -90 + ang, fill=(244, 200, 120, 235), width=4)
    if u < 0.95:
        hx = cx + Rr * math.cos(math.radians(-90 + ang)); hy = cy + Rr * math.sin(math.radians(-90 + ang)); rd.ellipse([hx - 14, hy - 14, hx + 14, hy + 14], fill=(255, 236, 190, 220))
    lay.alpha_composite(ring.filter(ImageFilter.GaussianBlur(8))); lay.alpha_composite(ring)
    ct(700, R.TXT["slogan1"], R.font("sub"), LG, ease((u - OUT_T[0]) / 0.5))
    ct(776, R.TXT["slogan2"], R.font("slogan"), LG_HI, ease((u - OUT_T[1]) / 0.6))
    a3 = ease((u - OUT_T[2]) / 0.5)
    if a3 > 0:
        R._glint_line(d, lay, W / 2, 960, 120, a3, u)
        kf = ImageFont.truetype(R.F + "Hahmlet[wght].ttf", 46) if R.LANG != "en" else ImageFont.truetype(R.EF + "Cinzel-SemiBold.ttf", 44)
        try: kf.set_variation_by_axes([600])
        except Exception: pass
        ct(992, R.TXT["brand"], kf, (222, 196, 140), a3)
    ab = ease((u - OUT_T[3]) / 0.5)
    if ab > 0:
        # 11/5 대표: 실제 행동을 이끄는 한 줄 — "좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다."
        # 11/9 대표: 안내 글과 아이콘 사이가 좁음 → 글을 20px 올리고 아이콘을 55px 내림 (간격 약 32 → 약 107px)
        ct(1110, R.TXT["thanks1"].format(s=(R.TXT["follow"] if PLAT == "reels" else R.TXT["sub"]).lower() if R.LANG == "en" else (R.TXT["follow"] if PLAT == "reels" else R.TXT["sub"])), R.font("small"), (222, 196, 140), ab)
        ct(1168, R.TXT["thanks2"], R.font("small"), (222, 196, 140), ab)
        items = [("like", R.TXT["like"]), ("follow", R.TXT["follow"]) if PLAT == "reels" else ("bell", R.TXT["sub"]), ("share", R.TXT["share"])]
        for k2, (kind, lab) in enumerate(items):
            ak = ease((u - OUT_T[3] - 0.1 - k2 * 0.15) / 0.4); bx = W / 2 - 290 + k2 * 290; by = 1385 + int((1 - ak) * 14)
            sp = R.cta_sprite(kind); sp2 = sp.copy(); sp2.putalpha(sp.split()[3].point(lambda v: int(v * ak)))
            lay.alpha_composite(sp2, (int(bx - sp.width / 2), int(by - sp.height / 2)))
            f = R.font("cta"); w = d.textlength(lab, font=f); d.text((bx - w / 2, by + 112), lab, font=f, fill=LG_HI + (int(240 * ak),))
    img.alpha_composite(lay); return img
t = END
while t < TOT:
    fi += 1; t = fi / FPS
    if t >= TOT: break
    if t < OS:
        u = t - END
        img = bgE.copy()
        if u < 0.8:   # 마지막 장면이 계속 움직이다가 부드럽게 흐려진다 (갑자기 바뀌지 않게)
            live = Image.fromarray(np.clip(frame_at(len(shots) - 1, t) * GRADE * VIG, 0, 255).astype(np.uint8)).convert("RGBA")
            lc = spec["cuts"][-1]; R.top_shade(live, strength=lc.get("shade", 200), h=lc.get("shade_h", 980))
            tl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); R.draw_block(tl, [dict(b, t1=b.get("t1", 999)) for b in lc["texts"]], t - starts[-1], top=lc.get("top", 250))
            ta = np.array(tl); ta[..., 3] = (ta[..., 3] * (1 - ease2(u / 0.5))).astype(np.uint8); live.alpha_composite(Image.fromarray(ta))
            img = Image.blend(live, img, ease2(u / 0.8))
        img.alpha_composite(Image.new("RGBA", (W, H), R.BG + (int(220 * ease2(u / 0.9)),)))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        write_line(d, lay, 640, E["kicker"], "sub", ease2((t - T_K[0] + .1) / (T_K[1] - T_K[0])), R.GOLD)
        y = 730; lh = int(R.font("endbig").size * R.LH["endbig"])
        for ln, (a0, a1) in zip(E["lines"], T_L):
            write_line(d, lay, y, ln, "endbig", ease2((t - a0 + .1) / (a1 - a0)), R.IVORY); y += lh
        sa = ease((t - T_L[-1][1] - .2) / .5)
        if sa > 0:
            f = R.font("small"); w = d.textlength(E["source"], font=f); d.text(((W - w) / 2, y + 110), E["source"], font=f, fill=R.DIM + (int(255 * sa),))
        q = ease2((t - (OS - 1.15)) / 1.15)
        if q > 0:
            a = np.array(lay); a[..., 3] = (a[..., 3] * (1 - q)).astype(np.uint8); lay = Image.fromarray(a)
        img.alpha_composite(lay); R.watermark(img, .55 * (1 - q))
        if q > 0:
            nxt = outro2(0.0); img = Image.blend(img, nxt, q * 0.85)
    else:
        u = t - OS
        img = outro2(u)
        z = 1 + 0.03 * ease(u / O["dur"]); bw, bh = W / z, H / z
        img = img.resize((W, H), Image.BILINEAR, box=((W - bw) / 2, (H - bh) / 2, (W + bw) / 2, (H + bh) / 2))
    # 금빛 먼지(끝 화면에도 계속)
    pl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(pl)
    for q2 in range(0, len(P), 2):
        px = (P[q2, 0] * W + 30 * math.sin(t * .5 + q2)) % W; py = (P[q2, 1] * H * 1.2 - t * (20 + P[q2, 2] * 40)) % (H * 1.2) - H * .1; r = 1 + P[q2, 4] * 2
        d.ellipse([px - r, py - r, px + r, py + r], fill=(255, 210, 140, int(60 + 80 * P[q2, 3])))
    img.alpha_composite(pl.filter(ImageFilter.GaussianBlur(1.2)))
    enc.stdin.write(img.convert("RGB").tobytes())
enc.stdin.close(); enc.wait()
# ---------- 소리: 완성본 소리 + 내레이션 뒤 여유(DELAY만큼 음악 늘림) + 하이라이트 효과음 ----------
SW = os.path.join(TMP, "swell.wav"); BM = os.path.join(TMP, "boom.wav")
subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i","anoisesrc=d=1.2:c=pink:a=0.8","-af","highpass=f=200,lowpass=f=2500,afade=t=in:d=0.8:curve=exp,afade=t=out:st=0.8:d=0.4,volume=0.45","-ar","48000","-ac","2",SW],check=True)
subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i","sine=f=48:d=1.6","-f","lavfi","-i","anoisesrc=d=1.6:c=brown:a=0.6","-filter_complex","[0][1]amix=2,lowpass=f=160,afade=t=out:st=0.05:d=1.5,volume=1.6","-ar","48000","-ac","2",BM],check=True)
sa, sb = NAR_END + 0.13, OS0 - 0.15; tempo = (sb - sa) / (sb - sa + DELAY)
assert sb - sa > 0.4 and 0.5 <= tempo <= 1.0, f"오늘의 할 일 뒤 여유 계산 오류 sa={sa} sb={sb} tempo={tempo} — 목소리 시각 확인"
fc = ["[1:a]asplit=3[x1][x2][x3]", f"[x1]atrim=0:{sa},asetpts=PTS-STARTPTS[a1]", f"[x2]atrim={sa}:{sb},asetpts=PTS-STARTPTS,atempo={tempo:.4f}[a2]", f"[x3]atrim={sb},asetpts=PTS-STARTPTS[a3]", "[a1][a2][a3]concat=n=3:v=0:a=1[base]"]
ins = ["-i", HEAD, "-i", ORIG]; mix = ["[base]"]; k = 2
for t in [x[2] for x in shots[1:] if x[4]]:
    ins += ["-i", SW]; ms = int(max(0, t - 0.9) * 1000); fc.append(f"[{k}:a]adelay={ms}|{ms},volume=0.3[s{k}]"); mix.append(f"[s{k}]"); k += 1
for t in PUNCH:
    ins += ["-i", BM]; ms = int(t * 1000); fc.append(f"[{k}:a]adelay={ms}|{ms},volume=0.5[s{k}]"); mix.append(f"[s{k}]"); k += 1
fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first,alimiter=limit=0.9{':latency=1' if R.LANG == 'en' else ''},aresample=48000[a]")   # 2026-11-13 영어: render_ed 와 같은 이유(ffmpeg 6.1 alimiter 지연 보정 없으면 목소리 파형 틀어짐)
base = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]", "-pix_fmt", "yuv420p", "-shortest"]
if PLAT == "shorts":   # 유튜브
    subprocess.run(base + ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-tune", "grain", "-maxrate", "9M", "-bufsize", "18M", "-c:a", "aac", "-b:a", "192k", "-ac", "2", OUT], check=True)
else:                  # 인스타·틱톡: 10MB 아래 (틱톡 업로드 한도)
    PL = os.path.join(TMP, "p2")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", HEAD, "-an", "-c:v", "libx264", "-preset", "medium", "-b:v", "1450k", "-maxrate", "3M", "-bufsize", "6M", "-pass", "1", "-passlogfile", PL, "-pix_fmt", "yuv420p", "-f", "mp4", "/dev/null"], check=True)
    subprocess.run(base + ["-c:v", "libx264", "-preset", "medium", "-b:v", "1450k", "-maxrate", "3M", "-bufsize", "6M", "-pass", "2", "-passlogfile", PL, "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-ar", "48000", "-movflags", "+faststart", OUT], check=True)
import shutil; shutil.rmtree(TMP, ignore_errors=True)
print(f"{OUT} · 샷 {len(shots)} · 금빛 {sum(1 for x in shots if x[4])} · 오늘의 할 일 {T_K[0]:.2f}/{[round(x[0],2) for x in T_L]} · 엔딩 {VO.get('outro')}")
