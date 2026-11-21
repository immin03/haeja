"""이미 산 녹음을 영구 음성 보관함으로 옮겨 담기 (2026-11-21).
actions/cache 에만 있던 예전 녹음을 보관함에 올려, 캐시가 날아가도 다시 사지 않게 한다.
한 번 실행에 최대 MAX 개만(렌더 시간을 잡아먹지 않게). 올린 파일은 .seeded 목록에 적어 다음엔 건너뛴다.
사용: python3 scripts/reels/tts_seed.py   (yt-long·reels 렌더 뒤에 자동 실행)
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tts_store

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CACHE = os.environ.get("TTS_CACHE", os.path.join(HERE, ".cache"))
DIRS = [(os.path.join(CACHE, "typecast"), "ko"), (os.path.join(CACHE, "typecast_en"), "en"),
        (os.path.join(ROOT, "social", "side", "tts_cache"), "side")]
MAX = int(os.environ.get("TTS_SEED_MAX", "400"))


def main():
    if not os.environ.get("TYPECAST_API_KEY"): return
    mark = os.path.join(CACHE, ".seeded"); os.makedirs(CACHE, exist_ok=True)
    done = set(open(mark).read().split()) if os.path.exists(mark) else set()
    todo = []
    for d, ns in DIRS:
        if not os.path.isdir(d): continue
        for f in sorted(os.listdir(d), key=lambda f: -os.path.getmtime(os.path.join(d, f))):   # 최근 녹음부터
            if not f.endswith(".mp3"): continue
            p = f"{ns}/{f}"
            if p in done or not tts_store.OK_NAME(f): continue
            todo.append((p, os.path.join(d, f)))
    todo = todo[:MAX]; up = 0
    for i in range(0, len(todo), 40):
        chunk = todo[i:i + 40]
        have = tts_store.has([p for p, _ in chunk])
        if tts_store._OFF["v"]: break
        import concurrent.futures
        new = [(p, src) for p, src in chunk if p not in have]
        done.update(p for p, _ in chunk if p in have)
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            for (p, _), ok in zip(new, ex.map(lambda x: tts_store.put_now(*x), new)):
                if ok: done.add(p); up += 1
    open(mark, "w").write("\n".join(sorted(done)))
    print(f"[음성 보관함] 옮겨 담기: 새로 올림 {up} · 확인 {len(todo)} · 누적 {len(done)}", flush=True)


if __name__ == "__main__":
    main()
