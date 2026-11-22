#!/usr/bin/env python3
"""렌더 결과 영상을 Supabase Storage 'media' 버킷(사이트가 내주는 곳)에 바로 올리고 받는다. (2026-11-22)

배경: 영상을 git 에 커밋하면 저장소가 하루 1GB 가까이 커진다(11/20 기준 기록 27GB). 영상은 Storage 가 원본이 되게 옮기는 중이다.
경로는 저장소 경로와 같다(예: social/reels/Y261122a/reel.mp4). 사이트 주소도 그대로다.

사용:
  python3 scripts/ci/media_store.py put <경로>...      # 그 파일들을 올린다
  python3 scripts/ci/media_store.py changed <폴더>...  # git 기준으로 새로 생기거나 바뀐 mp4 만 올린다
  python3 scripts/ci/media_store.py get <경로>...      # 로컬에 없으면 사이트 주소에서 받아 그 자리에 둔다

인증: X-API-KEY = TYPECAST_API_KEY (vn-tts-cache 와 같은 방식, Supabase 함수 media-put).
put·changed 는 실패해도 렌더를 멈추지 않는다(종료 코드 0). 올라간 경로는 MEDIA_STORE_OUT 파일(있으면)에 한 줄씩 적는다.
"""
import json, os, subprocess, sys, urllib.request

FN = "https://msjbrwyzkiueqnzjeicm.supabase.co/functions/v1/media-put"
SITE = "https://www.valuenote.co.kr/"
PUB = "https://msjbrwyzkiueqnzjeicm.supabase.co/storage/v1/object/public/media/"


def _fn(op, body, timeout=30):
    req = urllib.request.Request(FN + "?op=" + op, data=json.dumps(body).encode(), method="POST",
                                 headers={"X-API-KEY": os.environ.get("TYPECAST_API_KEY", ""), "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def put(path):
    """파일 하나를 올리고 크기(바이트)를 돌려준다. 실패하면 예외."""
    path = path.replace(os.sep, "/").lstrip("./")
    size = os.path.getsize(path)
    url = _fn("sign", {"path": path})["url"]
    with open(path, "rb") as f:
        req = urllib.request.Request(url, data=f, method="PUT",
                                     headers={"Content-Type": "video/mp4", "Content-Length": str(size), "x-upsert": "true"})
        urllib.request.urlopen(req, timeout=900).read()
    return size


def changed(roots):
    out = subprocess.run(["git", "status", "--porcelain", "-uall", "--"] + list(roots), capture_output=True, text=True).stdout
    res = []
    for line in out.splitlines():
        st, p = line[:2], line[3:].strip().strip('"')
        if " -> " in p: p = p.split(" -> ")[-1]
        if p.endswith(".mp4") and "D" not in st and os.path.exists(p): res.append(p)
    return res


def get(path):
    """로컬에 없으면 사이트 주소(저장소 또는 Storage)에서 받는다. 있으면 그대로 둔다."""
    path = path.replace(os.sep, "/").lstrip("./")
    if os.path.exists(path) and os.path.getsize(path) > 1000: return path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    last = None
    for base in (PUB, SITE):
        try:
            req = urllib.request.Request(base + path, headers={"User-Agent": "valuenote-media-store"})
            with urllib.request.urlopen(req, timeout=300) as r, open(path + ".part", "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b: break
                    f.write(b)
            if os.path.getsize(path + ".part") > 1000:
                os.replace(path + ".part", path)
                return path
        except Exception as e:
            last = e
    if os.path.exists(path + ".part"): os.remove(path + ".part")
    raise RuntimeError(f"받기 실패 {path}: {last}")


def main(argv):
    if len(argv) < 2 or argv[0] not in ("put", "changed", "get"):
        print(__doc__); return 2
    cmd, args = argv[0], argv[1:]
    if cmd == "get":
        for p in args: print("받음", get(p))
        return 0
    paths = changed(args) if cmd == "changed" else args
    if not paths:
        print("올릴 영상 없음"); return 0
    if not os.environ.get("TYPECAST_API_KEY"):
        print("TYPECAST_API_KEY 없음 — Storage 업로드 건너뜀"); return 0
    done = []
    for p in paths:
        try:
            n = put(p); done.append(p); print(f"  Storage 올림 {p} · {n/1e6:.1f}MB")
        except Exception as e:
            print(f"  Storage 실패 {p} · {e}")
    out = os.environ.get("MEDIA_STORE_OUT")
    if out:
        with open(out, "a") as f: f.write("".join(p + "\n" for p in done))
    print(f"Storage {len(done)}/{len(paths)}개")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
