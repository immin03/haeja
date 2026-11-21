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


def _rpc(name, body):
    import re
    cfg = open(os.path.join(ROOT, "config.js")).read()
    u = re.search(r"SUPABASE_URL:\s*'([^']+)'", cfg)[1]; k = re.search(r"SUPABASE_ANON_KEY:\s*'([^']+)'", cfg)[1]
    req = urllib.request.Request(u + "/rest/v1/rpc/" + name, data=json.dumps(body).encode(), method="POST",
                                 headers={"apikey": k, "Authorization": "Bearer " + k, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read() or b"null")


def lock(sid, holder):
    """DB 잠금 (public.render_lock, 최대 4시간). DB에 닿지 못하면 렌더는 진행한다(워크플로 concurrency 가 1차 방어)."""
    try: return _rpc("render_lock", {"p_id": sid, "p_holder": holder, "p_minutes": 240}) or {"ok": True}
    except Exception as e: print("  잠금 확인 실패(진행):", e); return {"ok": True}


def unlock(sid, holder):
    try: _rpc("render_unlock", {"p_id": sid, "p_holder": holder})
    except Exception as e: print("  잠금 풀기 실패(4시간 뒤 자동 만료):", e)


def _on_term(*_):   # 2026-11-20 대표 "왜 그런 실수를 자꾸": 실행을 취소하면 렌더 잠금이 남아 다음 렌더가 "렌더 완료: []"로 건너뛰었다 →
    raise KeyboardInterrupt("취소 신호")   # 취소(SIGTERM)도 예외로 바꿔 finally 의 unlock 이 반드시 돌게 한다


def main(only):
    import signal; signal.signal(signal.SIGTERM, _on_term)
    now = dt.datetime.now(dt.timezone.utc)
    again = set() if only else rerender_ids()
    done = []
    for f in sorted(glob.glob(os.path.join(HERE, "specs", "*.json"))):
        if f.endswith(".data.json"): continue
        # 2026-11-19: specs/ 안에 id·scheduled_at 없는 파일(메모·깨진 json)이 있어도 전체 build 가 멈추지 않게 건너뛴다
        try:
            spec = json.load(open(f, encoding="utf-8")); sid = spec["id"]
            when = dt.datetime.fromisoformat(spec["scheduled_at"])
            if not isinstance(spec.get("scenes"), list): raise KeyError("scenes")
        except Exception as e:
            print("  건너뜀(롱폼 스펙 아님):", os.path.basename(f), type(e).__name__, str(e)[:80], flush=True); continue
        meta_p = os.path.join(OUT, sid, "meta.json")
        if "--all-upcoming" in only: need = now - dt.timedelta(hours=6) <= when <= now + dt.timedelta(hours=30)
        else: need = (sid in only) if only else (sid in again or (not os.path.exists(meta_p) and now - dt.timedelta(hours=6) <= when <= now + dt.timedelta(hours=30)))
        if not need: continue
        if os.environ.get("DRY") == "1":   # 2026-11-21: 매시 점검은 렌더할 게 있는지만 먼저 본다(28GB 전체 내려받기 전에)
            print("DRY_TARGET", sid, flush=True); continue
        # 2026-11-21 대표 "썸네일 때문에 왜 재렌더": 렌더 뒤에야 필요한 칸이 비면 다 구운 영상을 버린다 → 렌더 전에 확인
        _miss = [k for k in ("title", "description_head", "scheduled_at") if not spec.get(k)]
        if _miss:
            os.makedirs(os.path.join(OUT, sid), exist_ok=True)
            open(os.path.join(OUT, sid, "build_error.txt"), "w", encoding="utf-8").write(now.isoformat() + "\n렌더 전 필수 칸 없음: " + ", ".join(_miss))
            print("  ✗ 필수 칸 없음 — 렌더 안 함:", sid, _miss, flush=True); continue
        print("렌더:", sid, spec["title"], flush=True)
        # 2026-11-19 대표 18:07: 렌더 전 관문 — 원고·스펙 검수가 실패하면 렌더를 시작하지 않는다 (사유는 기획 progress·alerts 에 기록)
        g = subprocess.run([sys.executable, os.path.join(HERE, "prerender_gate.py"), f, "--report"], capture_output=True, text=True)
        print(g.stdout[-4000:], g.stderr[-1500:], flush=True)
        if g.returncode != 0:
            os.makedirs(os.path.join(OUT, sid), exist_ok=True)
            open(os.path.join(OUT, sid, "build_error.txt"), "w", encoding="utf-8").write(now.isoformat() + "\n렌더 전 관문 실패 — 렌더 안 함\n" + g.stdout[-3000:])
            print("  ✗ 렌더 전 관문 실패 — 렌더 안 함:", sid, flush=True); continue
        # 2026-11-19: 한 영상 한 작업 — 같은 롱폼을 두 작업이 동시에 렌더하지 않게 DB 잠금 (docs locks 'render-<id>')
        holder = f"{os.environ.get('GITHUB_WORKFLOW', 'local')}#{os.environ.get('GITHUB_RUN_ID', os.getpid())}"
        lk = lock(sid, holder)
        if not lk.get("ok"):
            print("  ✗ 잠금 — 다른 작업이 렌더 중이라 건너뜀:", sid, lk, flush=True); continue
        try:
            sh(["node", os.path.join(HERE, "data.mjs"), f])
            data = json.load(open(f.replace(".json", ".data.json"), encoding="utf-8"))
            os.makedirs(os.path.join(OUT, sid), exist_ok=True)
            for sc in spec["scenes"]:
                img = sc["v"].get("img", "")
                if img.startswith("capture:"):
                    try: sh(["node", os.path.join(HERE, "capture_co.js"), data["raw"]["name"], os.path.join(OUT, sid, "shot_" + img.replace(":", "_") + ".png"), data["raw"]["code"]])
                    except Exception as e: print("앱 화면 캡처 실패(빈 화면으로 진행):", e)
            # 2026-11-17 대표님: 영상 속 앱 화면 5초는 렌더 직전에 실제 종목 페이지를 다시 찍는다 (컷 {"lib": "app_<slug>_<id>.mp4", "app": [slug, 회사명, "자막1|자막2"]})
            # 실패하면 저장소에 둔 지난 캡처 그대로 쓴다
            for sc in spec["scenes"]:
                for c in (sc["v"].get("cuts") or []):
                    if isinstance(c, dict) and c.get("app"):
                        try:
                            try: import playwright  # noqa: F401
                            except ImportError:
                                sh([sys.executable, "-m", "pip", "install", "-q", "playwright"]); sh([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"])
                            a = c["app"]; sh([sys.executable, os.path.join(HERE, "appscreen.py"), a[0], a[1], os.path.join(ROOT, "scripts", "blog", "media", "lib", c["lib"])] + ([a[2]] if len(a) > 2 else []))
                        except Exception as e: print("앱 화면 다시 찍기 실패(저장된 캡처로 진행):", e)
            # 2026-11-18 대표님: 세로 인물 사진이 가로 화면에서 눈 위로 잘림 → 렌더 직전에 *_wide(흐린 배경 + 인물 전체)로 바꿔 원고에 저장
            try:
                sys.path.insert(0, HERE); import make_wide
                _ch = False
                for sc in spec["scenes"]:
                    for c in (sc.get("v", {}).get("cuts") or []):
                        n = c.get("lib") if isinstance(c, dict) else None
                        if n and n.endswith("_wide.jpg") and not os.path.exists(os.path.join(make_wide.LIB, n)):   # 저장소에 없는 wide 는 원본에서 다시 만든다
                            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                                if os.path.exists(os.path.join(make_wide.LIB, n[:-9] + ext)): make_wide.make(n[:-9] + ext); break
                        elif n and not n.endswith("_wide.jpg") and n.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) and make_wide.is_portrait(n):
                            c["lib"] = make_wide.make(n); _ch = True; print("세로 사진 → 가로:", n, "→", c["lib"])
                if _ch: json.dump(spec, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            except Exception as e: print("세로 사진 가로 변환 실패(원본으로 진행):", e)
            renderer = "render2.py" if spec.get("format") == 2 else "render.py"  # v2: 머니스웨거식 샷 리스트 원고
            os.environ["TTS_ITEM"] = sid   # 타입캐스트 사용량을 편별로 기록 (scripts/reels/tts_log.py)
            # 2026-11-20 대표: "썸네일이 옛날 걸로 검수 페이지에 올라가고, 올릴 때도 옛날 걸로 올라간다" — 원인: 대표가 확정해 손으로 바꾼
            # 썸네일([skip ci] 커밋)을 그 뒤 다시 렌더할 때마다 렌더러/thumb_v8 이 원고 기준 옛 썸네일로 덮어썼다(L261119u 11/19 12:28·14:37).
            # 원고에 "thumb_fixed"가 있으면 렌더 전에 지금 썸네일을 떼어 두었다가 렌더 뒤 그대로 되돌린다. 썸네일을 바꾸라는 지시가 오면
            # 제작 작업이 thumb_fixed 를 지우고 thumb_v8 을 고쳐 다시 렌더한다(제1 원칙 r184).
            _keep = {}
            if spec.get("thumb_fixed"):
                for _n in ("thumb.jpg", "thumb_a.jpg", "thumb_b.jpg", "thumb_c.jpg", "thumb_en.jpg"):
                    _p = os.path.join(OUT, sid, _n)
                    if os.path.exists(_p): _keep[_n] = open(_p, "rb").read()
                print("확정 썸네일 보존:", sid, sorted(_keep) or "없음(처음 렌더)")
            sh([sys.executable, os.path.join(HERE, renderer), f])
            if spec.get("thumb_v8") and not _keep:   # 2026-11-17 썸네일 v8(큰 2줄 · 핑크 밑줄) 3안 — 렌더러가 만든 옛 썸네일을 덮는다
                # 2026-11-20 대표 "이거 최신 규칙 맞아? 왜 자꾸 이러지" — 11/18 확정 썸네일 틀은 v9(핑크 큰 머리글·밑줄 없음, thumb_v9.py)인데
                # 렌더는 계속 v8(작은 흰 머리글)로 만들고 있었다. 원고 키 이름은 thumb_v8 그대로 두고 그리는 틀만 v9로.
                _tv = "thumb_v9.py" if os.path.exists(os.path.join(HERE, "thumb_v9.py")) else "thumb_v8.py"
                try: sh([sys.executable, os.path.join(HERE, _tv), f, os.path.join(OUT, sid)])
                except Exception as e: print("썸네일 v8 실패(옛 썸네일 유지):", e)
            for _n, _b in _keep.items():   # 확정 썸네일 되돌리기
                open(os.path.join(OUT, sid, _n), "wb").write(_b)
            meta = json.load(open(meta_p, encoding="utf-8"))
            stamp = now.strftime("%y%m%d%H%M"); tag = "yt-" + sid; name = f"{sid}-{stamp}{'-draft' if os.environ.get('DRAFT') == '1' else ''}.mp4"   # 2026-11-20 시안은 이름에 -draft
            vid = os.path.join(OUT, sid, "video.mp4"); up = os.path.join(OUT, sid, name); os.replace(vid, up)
            if subprocess.run(["gh", "release", "view", tag, "-R", REPO], capture_output=True).returncode != 0:
                sh(["gh", "release", "create", tag, "-R", REPO, "--title", f"유튜브 롱폼 {sid}", "--notes", "관리자 검수용 영상 (자동 생성)", "--latest=false"])
            for _try in range(3):   # 2026-11-21: 업로드 한 번 끊겼다고 다 구운 영상을 버리지 않는다
                try: sh(["gh", "release", "upload", tag, up, "--clobber", "-R", REPO]); break
                except Exception as e:
                    if _try == 2: raise
                    print("  업로드 재시도", _try + 1, e, flush=True); import time; time.sleep(20)
            os.remove(up)
            for w in ("voice.wav",):
                p = os.path.join(OUT, sid, w)
                if os.path.exists(p): os.remove(p)
            meta["video_url"] = f"https://github.com/{REPO}/releases/download/{tag}/{name}"
            meta["thumb"] = f"/social/youtube/{sid}/thumb.jpg?v={stamp}"
            json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            try:   # 2026-10-25 운영자: 한국어·영어 자막(.srt)을 관리자에서 내려받을 수 있게
                sys.path.insert(0, HERE); import subs; subs.build(sid)
            except Exception as e: print("  자막 만들기 실패:", e)
            # 2026-11-12 대표: 영어 음성은 만들지 않는다 (유튜브에 올린 적 없이 크레딧만 썼다 → 유튜브 자동 더빙 사용).
            # 꼭 필요할 때만 EN_AUDIO=1 또는 yt-long 의 en_only=1 로 따로 만든다.
            if os.environ.get("EN_AUDIO") == "1":
              try:
                import en_audio; en_audio.build(sid, tag, REPO)
              except Exception as e: print("  영어 음성 만들기 실패(한국어판은 그대로):", e)
            done.append(sid)
        except Exception as e:
            import traceback
            print("  ✗ 실패:", sid, e, flush=True)
            # 2026-11-21: 영상은 다 구웠는데 그 뒤(썸네일·메타·자막)에서 죽으면 영상까지 버려졌다 → 영상만이라도 릴리스에 올린다
            _v = os.path.join(OUT, sid, "video.mp4")
            if os.path.exists(_v) and os.path.getsize(_v) > 1_000_000:
                try:
                    _tag = "yt-" + sid; _nm = f"{sid}-{now.strftime('%y%m%d%H%M')}{'-draft' if os.environ.get('DRAFT') == '1' else ''}-salvage.mp4"
                    _up = os.path.join(OUT, sid, _nm); os.replace(_v, _up)
                    if subprocess.run(["gh", "release", "view", _tag, "-R", REPO], capture_output=True).returncode != 0:
                        sh(["gh", "release", "create", _tag, "-R", REPO, "--title", f"유튜브 롱폼 {sid}", "--notes", "관리자 검수용 영상 (자동 생성)", "--latest=false"])
                    sh(["gh", "release", "upload", _tag, _up, "--clobber", "-R", REPO]); os.remove(_up)
                    print("  ↳ 영상은 살림:", _nm, flush=True)
                except Exception as e2: print("  ↳ 영상 살리기 실패:", e2, flush=True)
            os.makedirs(os.path.join(OUT, sid), exist_ok=True)
            open(os.path.join(OUT, sid, "build_error.txt"), "w", encoding="utf-8").write(now.isoformat() + "\n" + traceback.format_exc()[-3000:])
        finally:
            unlock(sid, holder)
    # 검수 대기열: 메타가 있는 롱폼 전부 (최근 30일)
    queue = []
    for m in sorted(glob.glob(os.path.join(OUT, "*", "meta.json"))):
        meta = json.load(open(m, encoding="utf-8"))
        if "video_url" not in meta: continue
        if meta.get("retired"): continue   # 2026-11-04 대표님: 없앤 편은 검수 대기열에 다시 넣지 않는다
        if dt.datetime.fromisoformat(meta["scheduled_at"]) < now - dt.timedelta(days=30): continue
        queue.append({k: meta.get(k) for k in ("id", "kind", "title", "description", "tags", "scheduled_at", "duration", "video_url", "thumb", "data", "data_asof", "events", "rendered_at", "company", "pinned_comment", "subs", "title_en", "description_en")})
    queue.sort(key=lambda x: x["scheduled_at"])
    os.makedirs(OUT, exist_ok=True)
    json.dump(queue, open(os.path.join(OUT, "queue.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("렌더 완료:", done, "· 대기열", len(queue), "편")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
