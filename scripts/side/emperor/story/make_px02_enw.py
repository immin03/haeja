"""px02 이야기형 시범편 조립 (게시 안 함)
python3 make_px02.py <px02v 목소리 폴더> <px01v 폴더(인용 e8)> <out.mp4>
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

VD, VD1, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__)); G = HERE + "/src/"
W, H, FPS = 1080, 1920, 30
IV, CH = (255, 253, 247), (238, 196, 126)
EF = "/home/claude/haeja/scripts/side/emperor/en/fonts/"
FN = {"title": "Cinzel-SemiBold.ttf", "cap": "EBGaramond-SemiBold.ttf", "quote": "EBGaramond-MediumItalic.ttf", "src": "Cinzel-SemiBold.ttf"}
F = lambda s, w="cap": ImageFont.truetype(EF + FN[w], s)
GAP = 0.22

LINES = dict(json.load(open(os.path.join(HERE, "lines_en.json"))))
# 장면: (목소리, 파일, 종류 vid/img/vid169, cx, 줌 시작, 줌 끝)
SC = [("s01", "pw_meet_v.mp4", "vid", .5, 1.0, 1.04), ("s02", "pw_smirk_v.mp4", "vid", .5, 1.0, 1.05),
      ("s03", "pw_bed_v.mp4", "vid", .5, 1.0, 1.05), ("s04", "pw_fist_v.mp4", "vid", .5, 1.0, 1.06),
      ("s05", "pw_elev.png", "img", .5, 1.0, 1.10), ("s06", "pw_bed_v.mp4", "vid", .5, 1.08, 1.0),
      ("s07", "pw_mirror.png", "img", .5, 1.10, 1.0), ("s08", "pw_puppet_v.mp4", "vid", .5, 1.0, 1.05),
      ("s09", "ev4_rumor.mp4", "vid169", .5, 1.0, 1.05), ("s10", "cep1_casp_b.mp4", "vid169", .5, 1.0, 1.06),
      ("s11", "cep1_diary.mp4", "vid169", .5, 1.0, 1.05), ("s12", "cep1_diary2.mp4", "quote", .5, 1.05, 1.0),
      ("s13", "pw_desk_v.mp4", "vid", .5, 1.0, 1.05), ("s14", "pw_desk_v.mp4", "vid", .5, 1.08, 1.0),
      ("s15", "lb04_scrolls.jpeg", "card", .5, 1.0, 1.04)]


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)


def vf(name):
    for f in sorted(os.listdir(VD)):
        if f.endswith(f"_px02en_{name}_A.mp3"): return os.path.join(VD, f)
    raise SystemExit("no voice " + name)


def chunks(t):
    """자막 8~14자 단위 — 쉼표·마침표에서 먼저 끊고, 길면 띄어쓰기에서"""
    parts = [p.strip() for p in re.split(r"(?<=[,.?!])\s+", t) if p.strip()]
    out = []
    for p in parts:
        p = p.rstrip(",")
        while len(p) > 26:
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
        for l in ["WHEN THEY", "DISRESPECT YOU"]:
            f = F(92, "title"); w = d.textlength(l, font=f); d.text(((W - w) / 2, y), l, font=f, fill=IV); y += 116
        fs = F(58, "title"); s = "MEDITATIONS (MODERN)"; w = d.textlength(s, font=fs); cy = y + 12 + int(fs.size * 0.62); d.text(((W - w) / 2, y + 12), s, font=fs, fill=CH)   # 2026-11-14 현대판 표시·글자 키움
        L = min(90, (W - w) / 2 - 60)
        if L > 30: d.line([(W / 2 - w / 2 - 24 - L, cy), (W / 2 - w / 2 - 24, cy)], fill=CH, width=3); d.line([(W / 2 + w / 2 + 24, cy), (W / 2 + w / 2 + 24 + L, cy)], fill=CH, width=3)
        im.save(path); return
    if kind == "quote":
        f = F(80, "quote"); y = 800; ls = ["“The best revenge", "is not to become like", "the one who wronged you.”"]; col = CH
        src = "— MARCUS AURELIUS, MEDITATIONS 6.6"
    elif kind == "card":
        f = F(70, "cap"); y = 860; ls = ["Today's line", "Meditations, Book 6.6"]; col = IV; src = None
    else:
        f = F(78, "cap"); y = 1180; ls = lines; col = IV; src = None
    sh = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(sh)
    for i, l in enumerate(ls):
        w = d.textlength(l, font=f); sd.text(((W - w) / 2, y + i * int(f.size * 1.34)), l, font=f, fill=255)
    im.paste((0, 0, 0, 235), (0, 4), sh.filter(ImageFilter.GaussianBlur(15)))
    for i, l in enumerate(ls):
        w = d.textlength(l, font=f); d.text(((W - w) / 2, y + i * int(f.size * 1.34)), l, font=f, fill=col if kind != "card" or i == 1 else IV)
    if src:
        fs = F(34, "src"); w = d.textlength(src, font=fs); d.text(((W - w) / 2, y + len(ls) * int(f.size * 1.34) + 30), src, font=fs, fill=(230, 222, 205))
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

# 2) 장면 조각: 영상은 끝 프레임을 붙잡아 길이를 채우고, 전체에 천천히 다가가기
parts = []
for i, s in enumerate(plan):
    sd = s["b"] - s["a"]; out = f"{HERE}/seg{i:02d}.mp4"; src = G + s["f"]
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
open(f"{HERE}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{HERE}/list.txt", "-c", "copy", f"{HERE}/bg.mp4"], check=True)

# 3) 글자: 제목 띠 고정 + 자막 조각(글자 수 비례로 시간 배분)
png(None, f"{HERE}/title.png", "title")
caps = []
for s in plan:
    if s["kind"] == "quote": caps.append((s["a"] + 0.1, s["b"], "quote", None)); continue
    if s["kind"] == "card": caps.append((s["a"] + 0.1, T, "card", None)); continue
    cs = chunks(LINES[s["k"]]); n = sum(len(c) for c in cs); x = s["t"] - 0.1
    for j, c in enumerate(cs):
        e = s["t"] + s["d"] * sum(len(cc) for cc in cs[:j + 1]) / n
        caps.append((x, e if j < len(cs) - 1 else s["b"], "cap", c)); x = e
ins = ["-i", f"{HERE}/bg.mp4", "-i", f"{HERE}/title.png"]; fl = "[0:v][1:v]overlay[v0]"; last = "v0"
for i, (a, b, kind, c) in enumerate(caps):
    p = f"{HERE}/cap{i:02d}.png"; png([c] if c else None, p, kind); ins += ["-i", p]
    fl += f";[{last}][{i+2}:v]overlay=enable='between(t,{a:.2f},{b:.2f})'[v{i+1}]"; last = f"v{i+1}"
print("captions", len([c for c in caps if c[2] == 'cap']))

# 4) 소리
na = 2 + len(caps); aud = []
for j, s in enumerate(plan):
    ins += ["-i", s["voice"]]; ms = int(s["t"] * 1000); aud.append(f"[{na+j}:a]adelay={ms}|{ms}[a{j}]")
ins += ["-i", "/home/claude/haeja/_long/st/music/we-ll-be-okay.mp3"]; mi = na + len(plan)
aud.append(f"[{mi}:a]atrim=0:{T:.2f},volume=0.14,afade=t=in:d=0.8,afade=t=out:st={T-1.5:.2f}:d=1.5[m]")
mix = "".join(f"[a{j}]" for j in range(len(plan))) + f"[m]amix=inputs={len(plan)+1}:normalize=0,loudnorm=I=-15.5:TP=-1.5:LRA=7[aout]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fl + ";" + ";".join(aud) + ";" + mix, "-map", f"[{last}]", "-map", "[aout]",
                "-t", f"{T:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT], check=True)
print(OUT, round(T, 1))
