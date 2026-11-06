"""릴스 → 인스타 스토리용 영상 만들기 (2026-11-07 대표: "릴스가 업로드 되면 직후 바로 그걸 스토리로 올리면 되는 거거든")

인스타 API 스토리 영상은 60초까지만 받는다. 릴스는 95~110초라 그대로 올리면 거부돼 표지 사진으로 대체됐다(10/31).
그래서 릴스 앞부분을 59초 안에서 '문장이 끝나는 지점'(같은 폴더 subs_ko.srt 자막 끝, 없으면 무음)에서 자르고,
그 마지막 화면을 3초 멈춘 채 "이어지는 내용은 / 프로필 → 릴스에서" 안내를 얹어 social/reels/<id>/story.mp4 로 만든다.
스토리 게시는 Supabase 함수 social-publish 가 릴스 게시 직후(5분 안) story.mp4 를 찾아 올린다.

사용: python3 scripts/reels/story_clip.py social/reels/<id>/reel.mp4 [social/reels/<id>/story.mp4]
"""
import os, re, shutil, subprocess, sys

MAX = 58.5          # 인스타 스토리 60초 제한에 여유
MIN_CUT = 30.0      # 이보다 앞에서는 자르지 않는다
END = 3.0           # 끝 안내 길이
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "SUIT-ExtraBold.ttf")


def duration(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", err)
    if not m:
        sys.exit(f"길이를 읽지 못함: {path}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def srt_cut(path):
    """자막 파일에서 MIN_CUT~(MAX-END) 사이에 끝나는 마지막 문장 끝. 없으면 None."""
    srt = os.path.join(os.path.dirname(path), "subs_ko.srt")
    if not os.path.exists(srt):
        return None
    ends = []
    for blk in re.split(r"\n\s*\n", open(srt, encoding="utf-8", errors="ignore").read()):
        m = re.search(r"--> (\d+):(\d+):(\d+)[,.](\d+)", blk)
        if not m:
            continue
        t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)[:3].ljust(3, "0")) / 1000
        text = blk.split("\n")[-1].strip() if "\n" in blk else ""
        ends.append((t, bool(re.search(r"(다|요|죠|까|\?|!|\.)\W*$", text))))
    ok = [t for t, full in ends if full and MIN_CUT <= t <= MAX - END] or [t for t, _ in ends if MIN_CUT <= t <= MAX - END]
    return (max(ok) - 0.2) if ok else None   # 다음 자막이 나오기 전 프레임에서 멈춘다


def silence_cut(path):
    """자막이 없을 때: 목소리 대역(300~3400Hz)만 남겨 말 사이 쉼을 찾는다(배경음악 때문에 그냥 무음은 안 잡힘).
    MIN_CUT~(MAX-END) 안에서 0.3초 이상 쉰 마지막 지점(문장 끝일 가능성이 큼), 없으면 가장 늦은 쉼. 없으면 None."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-t", str(MAX), "-i", path, "-af",
                          "highpass=f=300,lowpass=f=3400,silencedetect=noise=-28dB:d=0.18", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    gaps = [(a, b - a) for a, b in zip(st, en) if MIN_CUT <= a <= MAX - END]
    best = [a for a, d in gaps if d >= 0.3] or [a for a, _ in gaps]
    return (max(best) + 0.08) if best else None


def main(src, out):
    d = duration(src)
    if d <= MAX + 1:
        shutil.copyfile(src, out)
        print(f"스토리: {d:.1f}초 그대로 → {out}")
        return
    t = srt_cut(src) or silence_cut(src) or (MAX - END)
    font = FONT.replace(":", r"\:")
    on = f"enable='gte(t,{t:.2f})'"
    ta = t + 0.25   # 화면은 다음 자막 전에 멈추고, 소리는 마지막 음절까지 조금 더 둔다
    vf = (f"trim=0:{t:.2f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={END},"
          f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.55:t=fill:{on},"
          f"drawtext=fontfile='{font}':text='이어지는 내용은':fontcolor=white:fontsize=h/26:"
          f"x=(w-text_w)/2:y=h/2-text_h-h/80:{on},"
          f"drawtext=fontfile='{font}':text='프로필 → 릴스에서':fontcolor=0xE8C76A:fontsize=h/20:"
          f"x=(w-text_w)/2:y=h/2+h/80:{on}")
    af = f"atrim=0:{ta:.2f},asetpts=PTS-STARTPTS,afade=t=out:st={ta - 0.25:.2f}:d=0.25,apad=whole_dur={t + END:.2f}"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-t", f"{ta + 0.5:.2f}", "-i", src, "-vf", vf, "-af", af,
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", "30",
           "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-t", f"{t + END:.2f}", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print(f"스토리: {d:.1f}초 → {t:.1f}초 문장 끝에서 자름 + 안내 {END:.0f}초 → {out} {os.path.getsize(out) // 1024}KB")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    main(src, sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(src), "story.mp4"))
