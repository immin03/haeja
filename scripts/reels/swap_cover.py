"""표지만 갈아 끼우기 (2026-11-21 대표: "그런 정도 이슈로 실패를 하면 앞부분만 갈아 끼우면 되잖아")

영상 전체를 다시 렌더하지 않는다. 음성(타입캐스트)도 다시 사지 않는다.
  python3 scripts/reels/swap_cover.py <id>
1) scripts/reels/thumbs_bw/<id>.json 으로 표지를 다시 그린다 → social/reels/<id>/cover.jpg
2) 이미 만들어진 social/reels/<id>/reel.mp4 의 표지 구간만 새 표지로 바꾼다
   - 맨 끝 0.5초(쇼츠 표지 꼬리), 대본에 cover_head 가 있으면 맨 앞 그 길이도
   - 소리는 그대로 복사(-c:a copy), 영상만 다시 인코딩 — 30초 안팎
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
W, H, FPS, TAIL = 1080, 1920, 30, .5


def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", p],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def main(i):
    spec = json.load(open(os.path.join(HERE, "specs", f"{i}.json"), encoding="utf-8"))
    d = os.path.join(ROOT, "social", "reels", i); reel = os.path.join(d, "reel.mp4"); cover = os.path.join(d, "cover.jpg")
    if not os.path.exists(reel):   # 2026-11-22: 영상 원본이 Storage 에만 있을 수 있다(저장소에는 reel.stored 표시만) → 사이트 주소에서 받아 온다
        import urllib.request
        try:
            os.makedirs(d, exist_ok=True)
            rq = urllib.request.Request(f"https://www.valuenote.co.kr/social/reels/{i}/reel.mp4", headers={"User-Agent": "valuenote-swap-cover"})
            with urllib.request.urlopen(rq, timeout=300) as r, open(reel, "wb") as fh: fh.write(r.read())
        except Exception as e:
            if os.path.exists(reel): os.remove(reel)
            sys.exit(f"✗ {reel} 가 없고 사이트에서도 못 받았습니다 ({e}) — 처음 렌더는 reels-one 으로")
    import thumb_bw
    thumb_bw.render(json.load(open(os.path.join(HERE, "thumbs_bw", f"{i}.json"), encoding="utf-8")), cover)
    head = float(spec.get("cover_head") or 0); D = dur(reel); tmp = reel + ".swap.mp4"
    body = f"[0:v]trim=start={head}:end={D - TAIL},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p,setsar=1[b]"
    cv = f"[1:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1,split=2[c1][c2]"
    tl = f"[c1]trim=duration={TAIL},setpts=PTS-STARTPTS[t]"
    if head > 0:
        hd = f"[c2]trim=duration={head},setpts=PTS-STARTPTS[h]"
        fc = ";".join([body, cv, tl, hd, "[h][b][t]concat=n=3:v=1:a=0[v]"])
    else:
        fc = ";".join([body, cv, tl, "[c2]nullsink", "[b][t]concat=n=2:v=1:a=0[v]"])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", reel, "-loop", "1", "-t", str(max(head, TAIL) + 1), "-framerate", str(FPS), "-i", cover,
                    "-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                    "-c:a", "copy", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, reel)
    print(f"✓ {i}: 표지만 교체 (앞 {head}s / 끝 {TAIL}s) — {dur(reel):.2f}s")


if __name__ == "__main__":
    for a in sys.argv[1:]: main(a)
