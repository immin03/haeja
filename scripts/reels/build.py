"""대본 → 영상 일괄 생성 + 게시 대기열(queue.json) 갱신
- scripts/reels/specs/*.json  : 정기 편성 (사람이 쓴 대본)
- scripts/reels/events/*.json : 시장 급변 때 events.py 가 자동으로 만든 대본
- 결과: social/reels/<id>/reel.mp4, cover.jpg  →  social/reels/queue.json
  (Vercel 배포 뒤 Supabase가 1시간마다 queue.json을 읽어 게시 대기열에 넣는다)
사용: python3 scripts/reels/build.py            # 바뀐 대본만 렌더
      python3 scripts/reels/build.py R03       # 특정 대본만 다시 렌더
"""
import os, sys, json, glob, hashlib, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "social", "reels")
sys.path.insert(0, HERE)


def specs():
    for f in sorted(glob.glob(os.path.join(HERE, "specs", "*.json")) + glob.glob(os.path.join(HERE, "events", "*.json"))):
        yield f, json.load(open(f, encoding="utf-8"))


def digest(spec):
    keep = {k: spec[k] for k in ("scenes", "mood", "speed") if k in spec}
    src = open(os.path.join(HERE, "engine.py"), "rb").read()
    return hashlib.sha1(json.dumps(keep, ensure_ascii=False, sort_keys=True).encode() + src[:0]).hexdigest()[:12]


def main(only=None):
    import engine
    now = dt.datetime.now(dt.timezone.utc)
    queue = []
    for f, sp in specs():
        d = os.path.join(OUT, sp["id"]); h = digest(sp)
        mark = os.path.join(d, "spec.sha")
        stale = not os.path.exists(os.path.join(d, "reel.mp4")) or not os.path.exists(mark) or open(mark).read().strip() != h
        when = dt.datetime.fromisoformat(sp["scheduled_at"])
        if (only and sp["id"] in only) or (not only and stale and when > now - dt.timedelta(hours=6)):
            print("렌더:", sp["id"], sp["title"])
            sec = engine.render(sp, d)
            open(mark, "w").write(h)
            print(f"  {sec:.1f}초")
        if not os.path.exists(os.path.join(d, "reel.mp4")): continue
        if when < now - dt.timedelta(days=3): continue
        queue.append({
            "id": sp["id"], "seq": int(when.timestamp() // 60), "title": sp["title"],
            "scheduled_at": sp["scheduled_at"], "caption": sp["caption"], "hashtags": sp.get("hashtags", []),
            "threads_tag": sp.get("threads_tag"), "kind": "reel",
            "video": f"/social/reels/{sp['id']}/reel.mp4", "cover": f"/social/reels/{sp['id']}/cover.jpg",
            "to_ig": True, "to_threads": True, "approved": sp.get("approved", True)})
    queue.sort(key=lambda x: x["scheduled_at"])
    os.makedirs(OUT, exist_ok=True)
    json.dump(queue, open(os.path.join(OUT, "queue.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("대기열", len(queue), "편")


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
