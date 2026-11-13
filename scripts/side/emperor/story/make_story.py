"""px02 이야기형 시범편 조립 (게시 안 함)
python3 make_px02.py <px02v 목소리 폴더> <px01v 폴더(인용 e8)> <out.mp4>
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

EPID = sys.argv[1]; VD = sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__)); G = HERE + "/src/"; WK = HERE + "/" + EPID; os.makedirs(WK, exist_ok=True); OUT = WK + "/body.mp4"
sys.path.insert(0, HERE); from specs import EP
D = EP[EPID]
W, H, FPS = 1080, 1920, 30
IV, CH = (255, 253, 247), (238, 196, 126)
EN = D.get("lang") == "en"; EF = "/home/claude/haeja/scripts/side/emperor/en/fonts/"
if EN:
    FN = {"ExtraBold": "Cinzel-SemiBold.ttf", "Bold": "EBGaramond-SemiBold.ttf", "SemiBold": "Cinzel-SemiBold.ttf", "Quote": "EBGaramond-MediumItalic.ttf"}
    F = lambda s, w="ExtraBold": ImageFont.truetype(EF + FN[w], s)
else:
    F = lambda s, w="ExtraBold": ImageFont.truetype(f"/root/fonts/Pretendard-{w}.otf", s)
GAP = 0.22
LABEL = "MODERN MEDITATIONS" if EN else "현대판 명상록"   # 2026-11-14 대표: 기존 쇼츠와 다른 버전임을 표시
MUSIC = HERE + "/music/" + ("we-ll-be-okay.mp3" if sum(map(ord, EPID)) % 2 == 0 else "i-believe-2.mp3")   # 장조·따뜻한 곡 (cinematic_2 는 음산)
LINES = {k: l for k, l, *_ in D["sc"]}
SC = []
for k, line, src, img, mv in D["sc"]:
    if src.startswith("@"):
        f = src[1:]; kind = "card" if k == "card" else "quote" if k == "q" else ("img" if f.endswith(".jpeg") else "vid" if f.startswith(("px2_", "pxl_", "pw_", "st", "sw")) else "vid169")
    else:
        f = src + ("_v.mp4" if mv else ".jpeg"); kind = "vid" if mv else "img"
        if not mv and not os.path.exists(G + f) and os.path.exists(G + src + ".png"): f = src + ".png"
        if k == "q": kind = "quote"
    SC.append((k, f, kind, .5, 1.0, 1.06 if kind != "quote" else 1.0))


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)


def vf(name):
    for f in sorted(os.listdir(VD)):
        if f.endswith(f"_{EPID}_{name}_A.mp3"): return os.path.join(VD, f)
    raise SystemExit("no voice " + name)


def chunks(t):
    """자막 8~14자 단위 — 쉼표·마침표에서 먼저 끊고, 길면 띄어쓰기에서"""
    parts = [p.strip() for p in re.split(r"(?<=[,.?!])\s+", t) if p.strip()]
    out = []
    for p in parts:
        p = p.rstrip(",")
        while len(p) > (26 if EN else 15):
            sp = [m.start() for m in re.finditer(" ", p)]
            cut = min(sp, key=lambda i: abs(i - len(p) / 2)) if sp else len(p)
            out.append(p[:cut]); p = p[cut + 1:]
        out.append(p)
    return out


def png(lines, path, kind="cap"):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kind == "title":
        g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g)
        for y in range(540): gd.line([(0, y), (W, y)], fill=int(215 * (1 - y / 540) ** 1.3))
        im.paste((0, 0, 0, 255), (0, 0), g); y = 150
        for l in D["bar"]:
            f = F((88 if max(len(x) for x in D["bar"]) <= 15 else 78) if EN else (94 if max(len(x) for x in D["bar"]) <= 10 else 84)); w = d.textlength(l, font=f); d.text(((W - w) / 2, y), l, font=f, fill=IV); y += 116
        fs = F(50, "ExtraBold") if EN else F(64, "Bold"); s = LABEL; w = d.textlength(s, font=fs); cy = y + 12 + int(fs.size * 0.62); d.text(((W - w) / 2, y + 12), s, font=fs, fill=CH)
        L = min(90, (W - w) / 2 - 60)
        if L > 30: d.line([(W / 2 - w / 2 - 24 - L, cy), (W / 2 - w / 2 - 24, cy)], fill=CH, width=3); d.line([(W / 2 + w / 2 + 24, cy), (W / 2 + w / 2 + 24 + L, cy)], fill=CH, width=3)
        im.save(path); return
    if kind == "quote":
        f = F(78, "Quote") if EN else F(70, "Bold"); y = 820; ls = D["quote"]; col = CH
        src = D["qsrc"]
    elif kind == "card":
        f = F(64, "Bold"); y = 860; ls = D["card"]; col = IV; src = None
    else:
        f = F(78 if EN else 74, "Bold"); y = 640; ls = lines; col = IV; src = None
    sh = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(sh)
    for i, l in enumerate(ls):
        w = d.textlength(l, font=f); sd.text(((W - w) / 2, y + i * int(f.size * 1.34)), l, font=f, fill=255)
    im.paste((0, 0, 0, 235), (0, 4), sh.filter(ImageFilter.GaussianBlur(15)))
    for i, l in enumerate(ls):
        w = d.textlength(l, font=f); d.text(((W - w) / 2, y + i * int(f.size * 1.34)), l, font=f, fill=col if kind != "card" or i == 1 else IV)
    if src:
        fs = F(32 if EN else 36, "SemiBold"); w = d.textlength(src, font=fs); d.text(((W - w) / 2, y + len(ls) * int(f.size * 1.34) + 30), src, font=fs, fill=(230, 222, 205))
    im.save(path)


# 1) 목소리 시간표
t = 0.35; plan = []
for k, f, kind, cx, z0, z1 in SC:
    p = vf(k); d = dur(p) - 0.12   # 녹음 끝 무음 조금 잘라 빠르게
    plan.append(dict(k=k, f=f, kind=kind, cx=cx, z0=z0, z1=z1, voice=p, t=t, d=d)); t += d + GAP
T = t + 1.0
for i, s in enumerate(plan):
    s["a"] = 0 if i == 0 else s["t"] - GAP / 2
    s["b"] = T if i == len(plan) - 1 else plan[i + 1]["t"] - GAP / 2
print("total", round(T, 1), "scenes", len(plan))
json.dump({"id": EPID, "lang": "en" if EN else "ko", "voice": [{"file": x["voice"], "at": x["t"], "text": LINES[x["k"]]} for x in plan]}, open(WK + "/plan.json", "w"), ensure_ascii=False, indent=1)

# 2) 장면 조각: 영상은 끝 프레임을 붙잡아 길이를 채우고, 전체에 천천히 다가가기
parts = []
for i, s in enumerate(plan):
    sd = s["b"] - s["a"]; out = f"{WK}/seg{i:02d}.mp4"; src = G + s["f"]
    zs = f"({s['z0']}+({s['z1']}-{s['z0']})*t/{sd:.3f})"
    if s["kind"] in ("img", "card"):
        inp = ["-loop", "1", "-t", f"{sd:.3f}", "-i", src]; pre = f"scale=-2:{2*H},crop={2*W}:{2*H},"
    else:
        inp = ["-i", src]
        base = "crop=ih*9/16:ih:(iw-ih*9/16)*" + str(s["cx"]) + ":0," if s["kind"] in ("vid169", "quote") else ""
        pre = f"{base}scale={2*W}:{2*H}:flags=lanczos,tpad=stop_mode=clone:stop_duration={sd:.3f},trim=0:{sd:.3f},setpts=PTS-STARTPTS,"
    dark = ",eq=brightness=-0.07" if s["kind"] in ("quote", "card") else ""
    v = (pre + f"scale=w='trunc(iw*{zs}/2)*2':h='trunc(ih*{zs}/2)*2':eval=frame,crop={2*W}:{2*H}:(iw-ow)/2:(ih-oh)/2,"
         f"scale={W}:{H}:flags=lanczos,unsharp=5:5:0.5,eq=contrast=1.04:saturation=1.05{dark},fps={FPS},format=yuv420p")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-vf", v, "-an", "-t", f"{sd:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", out], check=True)
    parts.append(out)
open(f"{WK}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/list.txt", "-c", "copy", f"{WK}/bg.mp4"], check=True)

# 3) 글자: 제목 띠 고정 + 자막 조각(글자 수 비례로 시간 배분)
png(None, f"{WK}/title.png", "title")
caps = []
for s in plan:
    if s["kind"] == "quote": caps.append((s["a"] + 0.1, s["b"], "quote", None)); continue
    if s["kind"] == "card": caps.append((s["a"] + 0.1, T, "card", None)); continue
    cs = chunks(LINES[s["k"]]); n = sum(len(c) for c in cs); x = s["t"] - 0.1
    for j, c in enumerate(cs):
        e = s["t"] + s["d"] * sum(len(cc) for cc in cs[:j + 1]) / n
        caps.append((x, e if j < len(cs) - 1 else s["b"], "cap", c)); x = e
ins = ["-i", f"{WK}/bg.mp4", "-i", f"{WK}/title.png"]; fl = "[0:v][1:v]overlay[v0]"; last = "v0"
for i, (a, b, kind, c) in enumerate(caps):
    p = f"{WK}/cap{i:02d}.png"; png([c] if c else None, p, kind); ins += ["-i", p]
    fl += f";[{last}][{i+2}:v]overlay=enable='between(t,{a:.2f},{b:.2f})'[v{i+1}]"; last = f"v{i+1}"
print("captions", len([c for c in caps if c[2] == 'cap']))

# 4) 소리
na = 2 + len(caps); aud = []
for j, s in enumerate(plan):
    ins += ["-i", s["voice"]]; ms = int(s["t"] * 1000); aud.append(f"[{na+j}:a]adelay={ms}|{ms}[a{j}]")
ins += ["-i", MUSIC]; mi = na + len(plan)
aud.append(f"[{mi}:a]atrim=0:{T:.2f},volume=0.16,afade=t=in:d=0.8,afade=t=out:st={T-1.5:.2f}:d=1.5[m]")
mix = "".join(f"[a{j}]" for j in range(len(plan))) + f"[m]amix=inputs={len(plan)+1}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=7[aout]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fl + ";" + ";".join(aud) + ";" + mix, "-map", f"[{last}]", "-map", "[aout]",
                "-t", f"{T:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT], check=True)
print(OUT, round(T, 1))

# 5) 엔딩 붙이기 + 표지
B = dur(OUT); FIN = WK + f"/{EPID}_reels.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", OUT, "-i", HERE + ("/../px2/outro_en.mp4" if EN else "/../px2/outro.mp4"), "-filter_complex",
  f"[0:v]fps=30,format=yuv420p[a];[1:v]fps=30,format=yuv420p[b];[a][b]xfade=transition=fade:duration=0.5:offset={B-0.5:.2f}[v];[0:a]aresample=44100[x];[1:a]aresample=44100[y];[x][y]acrossfade=d=0.5[au]",
  "-map", "[v]", "-map", "[au]", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", FIN], check=True)
from PIL import ImageEnhance
cs = D.get("cover_scene", 0); f0 = G + SC[cs][1]; fr = WK + "/cv.png"
subprocess.run(["ffmpeg", "-v", "error", "-y"] + (["-ss", "1.6"] if f0.endswith(".mp4") else []) + ["-i", f0, "-frames:v", "1", fr], check=True)
im = Image.open(fr).convert("RGB"); top = 640; AH = H - top + 60
k = max(W / im.width, AH / im.height); im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
x = (im.width - W) // 2; y = int((im.height - AH) * D.get("cover_cy", 0.5)); im = im.crop((x, y, x + W, y + AH))
im = ImageEnhance.Sharpness(im).enhance(1.3); im = ImageEnhance.Brightness(im).enhance(1.08)
c = Image.new("RGB", (W, H), (8, 7, 6)); c.paste(im, (0, top - 60))
g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g)
for yy in range(top - 60, top + 60): gd.line([(0, yy), (W, yy)], fill=int(255 * (1 - (yy - (top - 60)) / 120)))
c.paste((8, 7, 6), (0, 0), g); d = ImageDraw.Draw(c); sz = 128
while max(d.textlength(l, font=F(sz)) for l in D["bar"]) > W - 80: sz -= 4
yy = 150
for l in D["bar"]:
    w = d.textlength(l, font=F(sz)); d.text(((W - w) / 2, yy), l, font=F(sz), fill=IV); yy += int(sz * 1.17)
fs = F(64, "ExtraBold") if EN else F(84, "Bold"); s_ = LABEL; w = d.textlength(s_, font=fs); ly = yy + 18 + int(fs.size * 0.62); d.text(((W - w) / 2, yy + 18), s_, font=fs, fill=CH)
L = min(116, (W - w) / 2 - 70)
if L > 30: d.line([(W / 2 - w / 2 - 34 - L, ly), (W / 2 - w / 2 - 34, ly)], fill=CH, width=4); d.line([(W / 2 + w / 2 + 34, ly), (W / 2 + w / 2 + 34 + L, ly)], fill=CH, width=4)
c.save(WK + f"/cover_{EPID}.jpg", quality=93)
print(FIN, round(dur(FIN), 1))
