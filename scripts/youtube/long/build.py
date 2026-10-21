"""유튜브 롱폼 일괄 렌더 + 검수 대기열(social/youtube/queue.json) 갱신
사용: python3 scripts/youtube/long/build.py [id ...]
 - id 를 주지 않으면: 게시 예정이 지금부터 30시간 안인데 아직 안 만들었거나, 관리자 화면에서 '다시 만들기'가 걸린 롱폼만 렌더한다
 - 숫자는 렌더 직전 최신 데이터로 채운다 (data.mjs). 앱 화면도 렌더 직전에 다시 찍는다 (capture_co.js)
 - 영상 파일은 GitHub 릴리스(yt-<id>)에 올리고, 썸네일·메타는 저장소에 둔다
"""
import datetime as dt, glob, json, os, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "social", "youtube")
REPO = os.environ.get("GITHUB_REPOSITORY", "immin03/haeja")


def sh(cmd, **kw):
    print("$", " ".join(cmd)[:160], flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    print(r.stdout[-3000:], r.stderr[-3000:], flush=True)
    if r.returncode: raise RuntimeError(f"명령 실패({r.returncode}): {' '.join(cmd)[:120]}\n{r.stderr[-1500:]}")
    return r


def rerender_ids():
    """관리자 화면에서 숫자가 오래됐다고 표시된 롱폼 (공개 함수, 아이디만 돌려준다)"""
    try:
        cfg = open(os.path.join(ROOT, "config.js")).read()
        import re
        u = re.search(r"SUPABASE_URL:\s*'([^']+)'", cfg)[1]; k = re.search(r"SUPABASE_ANON_KEY:\s*'([^']+)'", cfg)[1]
        req = urllib.request.Request(u + "/rest/v1/rpc/yt_rerender_ids", data=b"{}", method="POST",
                                     headers={"apikey": k, "Authorization": "Bearer " + k, "Content-Type": "application/json"})
        return set(json.loads(urllib.request.urlopen(req, timeout=30).read() or b"[]") or [])
    except Exception as e:
        print("다시 만들기 목록 조회 실패:", e); return set()


def main(only):
    now = dt.datetime.now(dt.timezone.utc)
    again = set() if only else rerender_ids()
    done = []
    for f in sorted(glob.glob(os.path.join(HERE, "specs", "*.json"))):
        if f.endswith(".data.json"): continue
        spec = json.load(open(f, encoding="utf-8")); sid = spec["id"]
        when = dt.datetime.fromisoformat(spec["scheduled_at"])
        meta_p = os.path.join(OUT, sid, "meta.json")
        need = (sid in only) if only else (sid in again or (not os.path.exists(meta_p) and now - dt.timedelta(hours=6) <= when <= now + dt.timedelta(hours=30)))
        if not need: continue
        print("렌더:", sid, spec["title"], flush=True)
        try:
            sh(["node", os.path.join(HERE, "data.mjs"), f])
            data = json.load(open(f.replace(".json", ".data.json"), encoding="utf-8"))
            os.makedirs(os.path.join(OUT, sid), exist_ok=True)
            for sc in spec["scenes"]:
                img = sc["v"].get("img", "")
                if img.startswith("capture:"):
                    try: sh(["node", os.path.join(HERE, "capture_co.js"), data["raw"]["name"], os.path.join(OUT, sid, "shot_" + img.replace(":", "_") + ".png"), data["raw"]["code"]])
                    except Exception as e: print("앱 화면 캡처 실패(빈 화면으로 진행):", e)
            sh([sys.executable, os.path.join(HERE, "render.py"), f])
            meta = json.load(open(meta_p, encoding="utf-8"))
            stamp = now.strftime("%y%m%d%H%M"); tag = "yt-" + sid; name = f"{sid}-{stamp}.mp4"
            vid = os.path.join(OUT, sid, "video.mp4"); up = os.path.join(OUT, sid, name); os.replace(vid, up)
            if subprocess.run(["gh", "release", "view", tag, "-R", REPO], capture_output=True).returncode != 0:
                sh(["gh", "release", "create", tag, "-R", REPO, "--title", f"유튜브 롱폼 {sid}", "--notes", "관리자 검수용 영상 (자동 생성)", "--latest=false"])
            sh(["gh", "release", "upload", tag, up, "--clobber", "-R", REPO])
            os.remove(up)
            for w in ("voice.wav",):
                p = os.path.join(OUT, sid, w)
                if os.path.exists(p): os.remove(p)
            meta["video_url"] = f"https://github.com/{REPO}/releases/download/{tag}/{name}"
            meta["thumb"] = f"/social/youtube/{sid}/thumb.jpg?v={stamp}"
            json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            done.append(sid)
        except Exception as e:
            import traceback
            print("  ✗ 실패:", sid, e, flush=True)
            os.makedirs(os.path.join(OUT, sid), exist_ok=True)
            open(os.path.join(OUT, sid, "build_error.txt"), "w", encoding="utf-8").write(now.isoformat() + "\n" + traceback.format_exc()[-3000:])
    # 검수 대기열: 메타가 있는 롱폼 전부 (최근 30일)
    queue = []
    for m in sorted(glob.glob(os.path.join(OUT, "*", "meta.json"))):
        meta = json.load(open(m, encoding="utf-8"))
        if "video_url" not in meta: continue
        if dt.datetime.fromisoformat(meta["scheduled_at"]) < now - dt.timedelta(days=30): continue
        queue.append({k: meta.get(k) for k in ("id", "kind", "title", "description", "tags", "scheduled_at", "duration", "video_url", "thumb", "data", "data_asof", "events", "rendered_at", "company", "pinned_comment")})
    queue.sort(key=lambda x: x["scheduled_at"])
    os.makedirs(OUT, exist_ok=True)
    json.dump(queue, open(os.path.join(OUT, "queue.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("렌더 완료:", done, "· 대기열", len(queue), "편")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
