"""롱폼 검토본을 관리자 페이지(valuenote.co.kr/side · 롱폼 칸)에 올린다 (2026-11-05 대표: 롱폼은 업로드 하루 전까지 렌더 완료, 관리자 페이지에서 확인).

python3 review_up.py <편 번호> <완성 mp4> [썸네일 jpg ...]
 · 540p로 줄여(50MB 이하) Storage 'ed-review/epNN.mp4' 에 올리고, 썸네일은 ed-review/epNN_A.jpg ... 로 올린다
 · 올린 뒤 app_config ed_ops.longform.eps 의 그 편 render_done·review 를 고치는 SQL 한 줄을 출력한다 (Supabase에서 실행)
 · 업로드 키는 scratchpad yt.sh 와 같은 ed-yt-long 함수(action review_sign) — 키 값은 이 파일에 두지 않는다 (환경변수 ED_YT_KEY)
"""
import os, sys, json, subprocess, urllib.request, datetime

FN = "https://msjbrwyzkiueqnzjeicm.supabase.co/functions/v1/ed-yt-long"
ST = "https://msjbrwyzkiueqnzjeicm.supabase.co/storage/v1"
ANON = os.environ.get("ED_ANON", ""); KEY = os.environ.get("ED_YT_KEY", "")


def call(b):
    b = dict(b, key=KEY)
    req = urllib.request.Request(FN, data=json.dumps(b).encode(), headers={"Authorization": "Bearer " + ANON, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def put(path, file, ct):
    u = call({"action": "review_sign", "path": path})["url"]; u = u if u.startswith("http") else ST + u
    req = urllib.request.Request(u, data=open(file, "rb").read(), method="PUT", headers={"Content-Type": ct, "x-upsert": "true"})
    return urllib.request.urlopen(req, timeout=600).status


def small(src, dst):
    """50MB 아래로: 540p, 길이에 맞춰 비트레이트를 정한다"""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout)
    kbps = int(46 * 8 * 1024 / dur) - 96
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", "scale=-2:540", "-c:v", "libx264", "-preset", "veryfast", "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps*1.3)}k",
                    "-bufsize", f"{kbps*2}k", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", dst], check=True)
    return dur


if __name__ == "__main__":
    n = int(sys.argv[1]); src = sys.argv[2]; thumbs = sys.argv[3:]
    # 2026-11-09 음성 관문: voice_gate_long.py 도장 없는 완성본은 관리자 검토로 올리지 않는다
    import hashlib
    stamp = src + ".voiceqa.json"
    if not os.path.exists(stamp): sys.exit(f"음성 관문 도장 없음 — 먼저: python3 voice_gate_long.py <spec.json> {src}")
    if json.load(open(stamp)).get("sha256") != hashlib.sha256(open(src, "rb").read()).hexdigest(): sys.exit("음성 관문 도장이 이 파일과 다름 — 다시 검사할 것")
    tmp = f"/tmp/ed_review_ep{n:02d}.mp4"; dur = small(src, tmp)
    print("video", put(f"ep{n:02d}.mp4", tmp, "video/mp4"), round(os.path.getsize(tmp) / 1e6, 1), "MB")
    th = []
    for i, t in enumerate(thumbs):
        k = "abc"[i]; p = f"ep{n:02d}_{k}.jpg"; print("thumb", k, put(p, t, "image/jpeg")); th.append(p)
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
    patch = {"render_done": now, "review": f"ep{n:02d}.mp4", "len": f"{int(dur // 60)}분 {int(dur % 60)}초"}
    if th: patch["review_thumbs"] = th
    print(json.dumps(patch, ensure_ascii=False))
