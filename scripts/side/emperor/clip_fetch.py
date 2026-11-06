"""생성 클립이 저장소에 없으면 받아 온다 (2026-11-06).

영상 클립(social/side/gen/*.mp4)은 저장소에서 빼고 Supabase Storage 로 옮긴다. 사이트 주소는 그대로라
https://www.valuenote.co.kr/social/side/gen/<파일> 로 받을 수 있다(vercel.json rewrite → Storage).
저장소에 파일이 있으면 아무것도 하지 않는다. 받지 못하면 검은 화면으로 렌더되지 않게 분명히 실패한다.

사용: from clip_fetch import ensure; path = ensure(path)
     python3 clip_fetch.py social/side/gen/edv02_tablet.mp4 [다른 경로 …]   (미리 받아 두기)
"""
import os, sys, time, urllib.request

SITE = "https://www.valuenote.co.kr/"
STORE = "https://msjbrwyzkiueqnzjeicm.supabase.co/storage/v1/object/public/media/"
KEY = "social/side/gen/"


def ensure(path):
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        return path
    norm = os.path.abspath(path).replace(os.sep, "/")
    i = norm.find(KEY)
    if i < 0:
        return path
    rel = norm[i:]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    part = path + ".part"
    for base in (SITE, STORE):
        for attempt in range(3):
            try:
                req = urllib.request.Request(base + rel, headers={"User-Agent": "valuenote-render"})
                with urllib.request.urlopen(req, timeout=90) as r, open(part, "wb") as f:
                    while True:
                        b = r.read(1 << 20)
                        if not b:
                            break
                        f.write(b)
                if os.path.getsize(part) > 10000:
                    os.replace(part, path)
                    print(f"  클립 받음: {rel} ({os.path.getsize(path) // 1024}KB)", flush=True)
                    return path
            except Exception as ex:
                print(f"  클립 받기 재시도 {attempt + 1}/3 ({base[8:30]}…): {ex}", flush=True)
                time.sleep(3)
    if os.path.exists(part):
        os.remove(part)
    sys.exit(f"클립 없음: {rel} — 저장소·사이트·Storage 모두 실패 (검은 화면 렌더 방지를 위해 멈춤)")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        ensure(p)
