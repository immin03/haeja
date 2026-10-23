"""롱폼에서 쇼츠(1080x1920) 잘라 만들기.
사용: python3 shorts.py <video.mp4> <meta.json> <out_dir> <shorts.json>
shorts.json: [{"id": "S1", "from": 0, "to": 2, "hook": ["SK하이닉스", "적정 주가 29만 원?"], "cta": "전체 분석은 밸류노트 채널에서"}]
  from/to = 롱폼 장면 번호(meta.qa.scenes). 화면: 위 훅 두 줄 → 가운데 롱폼 화면(아래 자막 띠는 잘라 냄) → 그 아래 큰 자막 → 맨 아래 안내.
"""
import json, os, re, subprocess, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from brand import paste_logo  # noqa: E402
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FD = os.path.join(ROOT, "scripts", "reels", "fonts")
F = lambda w, s: ImageFont.truetype(os.path.join(FD, f"SUIT-{w}.ttf"), s)
W, H = 1080, 1920; NAVY = (11, 27, 51); GOLD = (228, 206, 161); IVORY = (246, 241, 232)
VID_Y, VID_H = 540, int(1080 * 900 / 1700)          # 롱폼 가운데 1700x900(양옆 여백·아래 자막·출처 줄 제외)을 1080 폭으로


def ts(t):
    h, r = divmod(max(0, t), 3600); m, s = divmod(r, 60); return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def pages(text, maxc=17):
    """쇼츠 자막: 한 줄 17자 안팎, 쉼표·마침표에서 먼저 끊는다"""
    out = []
    for part in [p.strip() for p in re.split(r"(?<=[,.?!])\s+", text) if p.strip()]:
        cur = ""
        for w in part.split(" "):
            if len(cur) + len(w) + 1 > maxc and cur: out.append(cur); cur = w
            else: cur = (cur + " " + w).strip()
        if cur: out.append(cur)
    return out


def frame_png(hook, cta, path):
    im = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(im)
    for y in range(H):  # 아주 옅은 세로 그라데이션
        k = y / H; d.line([0, y, W, y], fill=(int(11 + 10 * k), int(27 + 12 * k), int(51 + 20 * k)))
    y = 190
    for i, l in enumerate(hook[:2]):
        f = F("Heavy", 92 if i else 74)
        while d.textlength(l, font=f) > W - 100: f = F("Heavy", f.size - 4)
        d.text((W / 2, y), l, font=f, fill=GOLD if i else IVORY, anchor="ma", stroke_width=3, stroke_fill=(0, 0, 0)); y += f.size + 26
    d.rounded_rectangle([60, VID_Y - 10, W - 60, VID_Y - 4], 3, fill=GOLD)
    f = F("ExtraBold", 44); d.text((W / 2, VID_Y + VID_H + 300), cta, font=f, fill=IVORY, anchor="mm")   # 쇼츠 화면 아래쪽(제목·채널 표시)에 가리지 않게
    paste_logo(im, W / 2, VID_Y + VID_H + 340, 40, "dark", align="center")   # 2026-10-23 확정 로고
    im.save(path)


def main():
    video, meta_p, out, spec_p = sys.argv[1:5]
    meta = json.load(open(meta_p)); sc = meta["qa"]["scenes"]; lines = meta["qa"]["lines"]
    os.makedirs(out, exist_ok=True)
    for s in json.load(open(spec_p)):
        t0 = sc[s["from"]][0]; t1 = sc[s["to"]][0] + sc[s["to"]][1]
        png = os.path.join(out, s["id"] + "_bg.png"); frame_png(s["hook"], s.get("cta", "전체 분석은 밸류노트 채널에서"), png)
        ev = []
        for st, du, text, _ in lines:
            if st < t0 - .05 or st > t1: continue
            ps = pages(text); tot = sum(len(p) for p in ps); acc = 0
            for p in ps:
                a = st - t0 + du * acc / tot; acc += len(p); b = st - t0 + du * acc / tot
                ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{p}")
        ass = os.path.join(out, s["id"] + ".ass")
        open(ass, "w").write("\n".join([
            "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
            "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Cap,SUIT ExtraBold,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,5,0,8,60,60,{VID_Y + VID_H + 70},1", "",
            "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text", *ev]))
        dur = t1 - t0 + .3; dst = os.path.join(out, s["id"] + ".mp4")
        fc = (f"[1:v]crop=1700:900:110:0,scale=1080:{VID_H}[v];[0:v][v]overlay=0:{VID_Y}[c];"
              f"[c]subtitles={ass}:fontsdir={FD}[o]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", png, "-ss", f"{t0:.2f}", "-t", f"{dur:.2f}", "-i", video,
                        "-filter_complex", fc, "-map", "[o]", "-map", "1:a", "-t", f"{dur:.2f}", "-r", "30",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                        "-af", f"afade=t=in:d=0.15,afade=t=out:st={max(0, dur - .6):.2f}:d=0.6", "-movflags", "+faststart", dst], check=True)
        print(s["id"], f"{dur:.1f}초", dst)


if __name__ == "__main__":
    main()
