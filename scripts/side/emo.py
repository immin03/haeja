"""What Korea Says — 감성 쇼츠 렌더러 (2026-10-28)
말 없는 15~30초 세로 쇼츠: 5초 영상 컷들을 부드럽게 이어 붙이고, 컷마다 짧은 영어 자막 한 줄, 잔잔한 배경음악.
입력: scripts/side/specs_emo/<id>.json
  {"id", "title", "description", "tags", "pinned", "scheduled_at",
   "music": {"file": "music_miss-you.mp3", "start": 0, "vol": 0.9},
   "cuts": [{"v": "mbv1_pack", "in": 0.2, "dur": 4.3, "cap": "2 a.m. in Seoul."}, ...],
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
        sh("ffmpeg", "-v", "error", "-y", "-ss", str(c.get("in", 0)), "-t", str(c["dur"]), "-i", find_video(c["v"]), "-an",
           "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},setsar=1,format=yuv420p",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out)
        real = float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out))
        parts.append((out, real))
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
                subtitle=f"/social/side/{sid}/subtitles_en.srt", rendered_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"), test=test)
    json.dump(meta, open(os.path.join(od, "meta.json"), "w"), ensure_ascii=False, indent=1)
    if not test:
        qp = os.path.join(ROOT, "social", "side", "queue.json"); q = json.load(open(qp)) if os.path.exists(qp) else []
        q = [x for x in q if x.get("id") != sid] + [meta]; json.dump(q, open(qp, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"url": url, "duration": round(dur, 1), "captions": [(a, b, t) for _, a, b, t in caps]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
