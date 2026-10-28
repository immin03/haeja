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


def heart(d, cx, cy, r, fill):
    """글꼴에 없을 수 있는 하트 기호 대신 직접 그린다"""
    import math
    pts = [(cx + r * 16 * math.sin(t) ** 3 / 16, cy - r * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16)
           for t in [i * 2 * math.pi / 120 for i in range(120)]]
    d.polygon(pts, fill=fill)


def _png(img, name):
    p = os.path.join(WORK, name); img.save(p); return p


def end_card(spec, bg_frame, out, dur=4.2):
    """엔딩 (2026-10-28 운영자): 마지막 장면을 흐리게 깔고 → 글자 로고 → 소포 든 까치가 날아와 로고 위에 앉는다
    → 문구 'Kachi brings you love, from Korea' → 좋아요·팔로우 버튼. 쇼츠 아래쪽 UI(제목)와 오른쪽 버튼 줄(x>940)을 피한다"""
    E = spec.get("end", {})
    bg = Image.open(bg_frame).convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(26))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (255, 236, 205)), 0.35)
    # 로고 (글자만)
    lg = Image.open(os.path.join(ROOT, "docs", "side", "logo_text.png")).convert("RGBA")
    lw = 640; lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
    lx, ly = (W - lw) // 2, 820
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(plate).rounded_rectangle((90, 520, W - 90, 1500), 80, fill=(255, 248, 236, 140))
    bgp = _png(Image.alpha_composite(bg.convert("RGBA"), plate.filter(ImageFilter.GaussianBlur(40))).convert("RGB"), "end_bg.png")
    lgp = _png(lg, "end_logo.png")
    # 까치: 나는 모습 → 앉은 모습 ('From' 글자 위에 앉는다)
    def cutout(name, h):
        k = Image.open(os.path.join(ROOT, "social", "side", "gen", "cut", name + ".png")).convert("RGBA")
        return k.resize((int(k.width * h / k.height), h), Image.LANCZOS)
    fly = cutout(E.get("fly", "h_fly_love"), 400); stand = cutout(E.get("host", "h_love"), 400)
    flyp, standp = _png(fly, "end_fly.png"), _png(stand, "end_stand.png")
    sx, sy = lx + 30, ly - stand.height + 28          # 앉는 자리: 로고 왼쪽 위 'From' 위
    fx0, fy0 = W + 40, 160                            # 오른쪽 위 화면 밖에서 출발
    fx1, fy1 = sx - (fly.width - stand.width) // 2, sy - 20
    # 문구 + 버튼
    f1 = ImageFont.truetype(os.path.join(FONTS, "Poppins-SemiBold.ttf"), 54)
    f2 = ImageFont.truetype(os.path.join(FONTS, "Poppins-Bold.ttf"), 50)
    phrase = E.get("phrase", "Kachi brings you love, from Korea")
    ph = Image.new("RGBA", (W, 90), (0, 0, 0, 0)); dp = ImageDraw.Draw(ph)
    dp.text(((W - f1.getlength(phrase)) / 2, 8), phrase, font=f1, fill=(31, 42, 68, 255))
    php = _png(ph, "end_phrase.png"); py = ly + lg.height + 30
    bt = Image.new("RGBA", (W, 130), (0, 0, 0, 0)); db = ImageDraw.Draw(bt)
    like, follow = "Like", "Follow"
    w1 = f2.getlength(like) + 150; w2 = f2.getlength(follow) + 110; gap = 36; x = (W - w1 - w2 - gap) / 2
    db.rounded_rectangle((x, 10, x + w1, 116), 53, fill=(255, 255, 255, 255), outline=(215, 50, 44, 255), width=5)
    heart(db, x + 62, 62, 30, (215, 50, 44, 255)); db.text((x + 106, 30), like, font=f2, fill=(215, 50, 44, 255))
    x2 = x + w1 + gap; db.rounded_rectangle((x2, 10, x2 + w2, 116), 53, fill=(215, 50, 44, 255))
    db.text((x2 + 55, 30), follow, font=f2, fill=(255, 255, 255, 255))
    btp = _png(bt, "end_btn.png"); by = py + 120
    T0, T1 = 0.25, 1.35   # 비행 시작·착지
    P = f"min(max((t-{T0})/{T1 - T0},0),1)"
    E3 = f"(1-pow(1-{P},3))"
    sh("ffmpeg", "-v", "error", "-y",
       "-loop", "1", "-t", str(dur), "-i", bgp, "-loop", "1", "-t", str(dur), "-i", lgp,
       "-loop", "1", "-t", str(dur), "-i", flyp, "-loop", "1", "-t", str(dur), "-i", standp,
       "-loop", "1", "-t", str(dur), "-i", php, "-loop", "1", "-t", str(dur), "-i", btp, "-filter_complex",
       f"[0:v]scale={W * 2}:{H * 2},zoompan=z='1+0.0005*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}[b];"
       f"[1:v]format=rgba,fade=in:st=0:d=0.45:alpha=1[l];"
       f"[4:v]format=rgba,fade=in:st=1.6:d=0.5:alpha=1[p];[5:v]format=rgba,fade=in:st=2.1:d=0.35:alpha=1[n];"
       f"[b][l]overlay=x={lx}:y='{ly}+25*exp(-6*t)'[a];"
       f"[a][2:v]overlay=x='{fx0}+({fx1}-{fx0})*{E3}':y='{fy0}+({fy1}-{fy0})*{E3}-160*sin(PI*{P})+10*sin(2*PI*6*t)':enable='lt(t,{T1})'[a2];"
       f"[a2][3:v]overlay=x={sx}:y='{sy}-26*exp(-7*(t-{T1}))*abs(cos(11*(t-{T1})))':enable='gte(t,{T1})'[a3];"
       f"[a3][p]overlay=x=0:y='{py}+18*exp(-7*max(t-1.6,0))'[a4];"
       f"[a4][n]overlay=x=0:y='{by}+40*exp(-9*max(t-2.1,0))'",
       "-t", str(dur), "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", out)


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
