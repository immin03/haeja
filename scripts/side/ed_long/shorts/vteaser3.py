"""황제의 일기 롱폼 소개 쇼츠 v3 (1080x1920) — 2026-11-06 대표 지시 반영
1) 말하는 사람 중심: 장면마다 고정 cx 대신 시간별 카메라 위치(키프레임)를 따라 세로 화면이 움직인다.
   말하는 인물의 얼굴·손이 잘리지 않게 잡고, 화자가 바뀌거나 화면 밖으로 나가면 부드럽게 따라간다.
2) 웅장한 로고 인트로를 항상 넣는다: 오프닝 장면 → 인트로(통째로, 위아래 검정) → 끝 카드.

사용: python3 vteaser3.py <track.json>
track.json = {
  "key": "teaser_ep03", "sid": "edl_ep03p",            # _long/<sid>_v.mp4, _long/<sid>_a.wav, caps_<sid>.json
  "t1": "<맨 위 흰 줄>", "t2": "<맨 위 금색 줄>",
  "end1": "<끝 카드 큰 글>|<둘째 줄>", "end2": "<끝 카드 금색>|<둘째 줄>",
  "hook": [0, 30.77],                                   # 세로로 자를 구간 (원본 초)
  "intro": [30.77, 41.37],                              # 통째로 보여 줄 인트로 구간
  "track": [[t, x], ...]                                # 원본 1920 폭 기준 화면 중심 x, 시각 오름차순
                                                        # 같은 시각 두 점 = 컷(바로 점프), 그 사이는 부드럽게(ease) 이동
}"""
import sys, os, json, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

cfg = json.load(open(sys.argv[1]))
ROOT = "/home/claude/haeja/"; L = ROOT + "_long/"; SID = cfg["sid"]
SRC = L + SID + "_v.mp4"; AUD = L + SID + "_a.wav"; CAP = ROOT + f"scripts/side/ed_long/caps_{SID}.json"
F = "/root/fonts/"; OUT = "/home/claude/shorts2/"; os.makedirs(OUT, exist_ok=True)
W, H, FPS, END, CW = 1080, 1920, 30, 2.6, 608
key = cfg["key"]; h0, h1 = cfg["hook"]; i0, i1 = cfg["intro"]
FB = lambda s: ImageFont.truetype(F + "Pretendard-ExtraBold.otf", s); FS = lambda s: ImageFont.truetype(F + "Pretendard-SemiBold.otf", s)
FM = lambda s: ImageFont.truetype(F + "hahmlet-korean-600-normal.ttf", s)
WHITE = (255, 255, 255); GOLD = (240, 196, 110); CREAM = (246, 234, 206)


def shadow_text(img, lines, y, font, fill, gap=1.32):
    d = ImageDraw.Draw(img); sh = Image.new("L", img.size, 0); sd = ImageDraw.Draw(sh); pos = []
    for i, t in enumerate(lines):
        w = d.textlength(t, font=font); x = (img.width - w) / 2; yy = y + i * font.size * gap; pos.append((x, yy, t))
        sd.text((x + 2, yy + 4), t, font=font, fill=255)
    sh = sh.filter(ImageFilter.GaussianBlur(7)); img.paste((0, 0, 0, 230), (0, 0), sh)
    for x, yy, t in pos: d.text((x, yy), t, font=font, fill=fill)


def wrap(t, font, maxw=930):
    d = ImageDraw.Draw(Image.new("L", (1, 1))); out = [""]
    for w in t.split(" "):
        c = (out[-1] + " " + w).strip()
        if d.textlength(c, font=font) <= maxw: out[-1] = c
        else: out.append(w)
    return out


# ---- 카메라 위치 식 (ffmpeg crop x, t = 구간 안 시간) ----
def xexpr(track, off):
    clamp = lambda v: max(0, min(1920 - CW, v - CW / 2))
    pts = [(t - off, clamp(x)) for t, x in track]
    e = f"{pts[-1][1]:.1f}"
    for (ta, xa), (tb, xb) in reversed(list(zip(pts, pts[1:]))):
        if tb - ta < 1e-3: continue   # 컷: 점프
        u = f"((t-{ta:.3f})/{tb - ta:.3f})"; s = f"({u}*{u}*(3-2*{u}))"
        seg = f"{xa:.1f}+({xb - xa:.1f})*{s}" if abs(xb - xa) > 0.5 else f"{xa:.1f}"
        e = f"if(lt(t,{tb:.3f}),{seg},{e})"
    return f"if(lt(t,{pts[0][0]:.3f}),{pts[0][1]:.1f},{e})"


tmp = OUT + key + "_tmp/"; os.makedirs(tmp, exist_ok=True)
# 위 고정층: 그라데이션 + 훅 제목
top = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = Image.new("L", (1, H))
for y in range(H):
    a = 0
    if y < 720: a = int(215 * (1 - y / 720) ** 1.3)
    if y > 1250: a = max(a, int(200 * ((y - 1250) / 670) ** 1.2))
    g.putpixel((0, y), a)
top.paste((0, 0, 0, 255), (0, 0), g.resize((W, H)))
def fit(t, s=104):
    while ImageDraw.Draw(Image.new("L", (1, 1))).textlength(t, font=FB(s)) > 990: s -= 4
    return FB(s)
fs = min(fit(cfg["t1"]).size, fit(cfg["t2"]).size)
shadow_text(top, [cfg["t1"]], 250, FB(fs), WHITE); shadow_text(top, [cfg["t2"]], 250 + fs * 1.22, FB(fs), GOLD)
top.save(tmp + "top.png")
# 자막 (출력 시각 = 원본 시각 - h0; 인트로 구간엔 자막 없음)
ov = []
for cc in json.load(open(CAP)):
    ca, cb, txt, kind = cc[:4]
    if cb <= h0 or ca >= h1: continue
    s0, s1 = max(ca, h0) - h0, min(cb, h1) - h0
    im = Image.new("RGBA", (W, 520), (0, 0, 0, 0))
    fnt, col = (FB(74), GOLD) if kind == "emph" else (FM(66), CREAM) if kind == "mono" else (FB(66), WHITE)
    lines = wrap(txt, fnt); y0 = (520 - len(lines) * fnt.size * 1.32) / 2; shadow_text(im, lines, y0, fnt, col)
    if kind == "mono":
        d2 = ImageDraw.Draw(im); m = "— 황제 —"; mf = FS(30); d2.text(((W - d2.textlength(m, font=mf)) / 2, y0 - 50), m, font=mf, fill=(220, 200, 160))
    p = f"{tmp}c{len(ov):03d}.png"; im.save(p); ov.append((p, s0, s1))
# 끝 카드
end = Image.new("RGBA", (W, H), (0, 0, 0, 242))
shadow_text(end, cfg["end1"].split("|"), 700, FB(78), WHITE)
shadow_text(end, cfg["end2"].split("|"), 970, FB(58), GOLD)
shadow_text(end, ["매일 밤, 황제처럼 생각하라."], 1230, FS(40), CREAM)
shadow_text(end, [cfg.get("cta", "좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다.")], 1320, FS(30), (200, 190, 170))
end.save(tmp + "end.png")
# 합성
HD, ID = h1 - h0, i1 - i0; T = HD + ID
fc = (f"[0:v]trim={h0:.3f}:{h1:.3f},setpts=PTS-STARTPTS,fps={FPS},crop={CW}:1080:'{xexpr(cfg['track'], h0)}':0,scale={W}:{H}:flags=lanczos,setsar=1[v0];"
      f"[0:v]trim={i0:.3f}:{i1:.3f},setpts=PTS-STARTPTS,fps={FPS},crop=1200:1080:360:0,scale={W}:-2:flags=lanczos,pad={W}:{H}:0:(oh-ih)/2:black,setsar=1[v1];"
      f"[1:a]atrim={h0:.3f}:{i1:.3f},asetpts=PTS-STARTPTS[a0];"
      f"[v0][v1]concat=n=2:v=1:a=0[cv];")
ins = ["-i", SRC, "-i", AUD, "-i", tmp + "top.png"]; k = 3
fc += f"[cv][2:v]overlay=0:0[o0];"; last = "o0"
for j, (p, s0, s1) in enumerate(ov):
    ins += ["-i", p]; fc += f"[{last}][{k}:v]overlay=0:1150:enable='between(t,{s0:.3f},{s1:.3f})'[o{j+1}];"; last = f"o{j+1}"; k += 1
ins += ["-loop", "1", "-t", str(END), "-i", tmp + "end.png"]; e = k
fc += (f"[{last}]tpad=stop_mode=clone:stop_duration={END}[pad];[{e}:v]fps={FPS},format=rgba,fade=t=in:d=0.4:alpha=1,setpts=PTS+{T:.3f}/TB[endv];"
       f"[pad][endv]overlay=0:0:eof_action=pass,format=yuv420p[vo];[a0]apad=pad_dur={END},afade=t=out:st={T+0.2:.3f}:d={END-0.3}[ao]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{T+END:.3f}", "-movflags", "+faststart", OUT + key + ".mp4"], check=True)
subprocess.run(["rm", "-rf", tmp]); print("완성", OUT + key + ".mp4", round(T + END, 1))
