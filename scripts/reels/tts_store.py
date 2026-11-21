"""영구 음성 보관함 (2026-11-21 대표: "같은 걸 다시 렌더할 때 타입캐스트를 다시 사지 않게, 할 수 있는 조치 모두 철저하게").

왜: 지금까지 산 녹음은 GitHub actions/cache 에만 있었다. 그 캐시는
  - 같은 시각에 도는 작업(롱폼·릴스·릴스 한 편 묶음)이 각자 저장하면, 다음 작업은 그중 '가장 최근 하나'만 되살려
    다른 작업이 산 녹음을 잃는다.
  - 7일 동안 안 쓰이거나 저장소 전체 10GB 를 넘으면 지워진다.
  실제 사례: 11/16 엔비디아 30일 편은 3시간 뒤 재렌더에서 5,110자를 그대로 다시 샀다(재사용 52자).
           11/19 전쟁 공포 편도 1시간 반 뒤 재렌더에서 5,033자를 다시 샀다(재사용 0자).
그래서 새로 산 녹음은 Supabase Storage 'tts' 버킷(비공개)에도 올리고, 로컬 캐시에 없으면 먼저 여기서 찾는다.

순서: 로컬 캐시(actions/cache) → 영구 보관함 → (없을 때만) 타입캐스트 구매 → 로컬 + 영구 보관함에 저장
보관함 접근 실패는 렌더를 멈추지 않는다(그냥 예전처럼 동작).
"""
import json, os, urllib.error, urllib.request

URL = "https://msjbrwyzkiueqnzjeicm.supabase.co/functions/v1/vn-tts-cache"
_OFF = {"v": bool(os.environ.get("TTS_STORE_OFF"))}
STATS = {"remote_hit": 0, "remote_put": 0}


def _key():
    return os.environ.get("TYPECAST_API_KEY", "")


def _req(op, path=None, data=None, method="GET", timeout=20, ctype="application/octet-stream"):
    q = f"?op={op}" + (f"&p={path}" if path else "")
    h = {"X-API-KEY": _key()}
    if data is not None: h["Content-Type"] = ctype
    return urllib.request.urlopen(urllib.request.Request(URL + q, data=data, method=method, headers=h), timeout=timeout)


_LIST = {}   # 갈래(ko/en/side)별 보관함 전체 목록 — 렌더 한 번에 1회만 받는다 (2026-11-21 효율 점검: 문장마다 묻지 않기)


def _names(ns):
    if ns not in _LIST:
        try:
            with _req(f"list&ns={ns}", timeout=15) as r:
                _LIST[ns] = set(json.loads(r.read()).get("names") or [])
        except Exception as e:
            _fail(e); _LIST[ns] = None
    return _LIST[ns]


def has(paths):
    """여러 경로 중 보관함에 있는 것만 돌려준다. 목록을 한 번 받아 두고 그 안에서 찾는다(없으면 한 번 묻는다)"""
    if _OFF["v"] or not _key() or not paths: return set()
    ns = {p.split("/", 1)[0] for p in paths}
    if len(ns) == 1:
        L = _names(ns.pop())
        if L is not None: return {p for p in paths if p in L}
    try:
        with _req("has", data=json.dumps({"paths": list(paths)[:40]}).encode(), method="POST", ctype="application/json", timeout=8) as r:
            return set(json.loads(r.read()).get("have") or [])
    except Exception as e:
        _fail(e); return set()


def fetch(path, dest):
    """보관함에 있으면 dest 로 내려받고 True"""
    if _OFF["v"] or not _key(): return False
    L = _names(path.split("/", 1)[0])
    if L is not None and path not in L: return False   # 목록에 없으면 묻지 않는다
    try:
        with _req("get", path, timeout=15) as r:
            b = r.read()
        if len(b) < 500: return False
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        tmp = dest + ".part"; open(tmp, "wb").write(b); os.replace(tmp, dest)
        STATS["remote_hit"] += 1
        return True
    except urllib.error.HTTPError as e:
        if e.code != 404: _fail(e)
        return False
    except Exception as e:
        _fail(e); return False


def put_now(path, src):
    """새로 산 녹음을 보관함에 올린다 (이미 있으면 그대로). 끝날 때까지 기다린다"""
    if _OFF["v"] or not _key() or not os.path.exists(src): return False
    try:
        with _req("put", path, data=open(src, "rb").read(), method="PUT", timeout=20) as r:
            r.read()
        STATS["remote_put"] += 1
        L = _LIST.get(path.split("/", 1)[0])
        if L is not None: L.add(path)
        return True
    except Exception as e:
        _fail(e); return False


_POOL = {"p": None}


def put(path, src):
    """렌더를 기다리게 하지 않도록 뒤에서 올린다 (2026-11-21 효율 점검). 실행이 끝날 때 남은 업로드를 모두 마친다"""
    if _OFF["v"] or not _key() or not os.path.exists(src): return False
    if _POOL["p"] is None:
        import atexit, concurrent.futures
        _POOL["p"] = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        atexit.register(lambda: _POOL["p"] and _POOL["p"].shutdown(wait=True))
    _POOL["p"].submit(put_now, path, src)
    return True


_NFAIL = {"n": 0}


def _fail(e):
    """연속으로 실패하면 이번 실행에서는 보관함을 끈다 (렌더가 느려지지 않게)"""
    _NFAIL["n"] += 1
    if _NFAIL["n"] <= 3: print("  [음성 보관함] 접근 실패(렌더는 그대로):", str(e)[:160], flush=True)
    if _NFAIL["n"] >= 3: _OFF["v"] = True


def local_or_remote(local_path, remote_path):
    """로컬 캐시에 있으면 True, 없으면 보관함에서 내려받아 보고 결과를 돌려준다"""
    if os.path.exists(local_path) and os.path.getsize(local_path) > 500: return True
    return fetch(remote_path, local_path)


def OK_NAME(fname):
    """보관함 경로 규칙(영문 소문자·숫자·밑줄 8~64자 + .mp3/.wav)에 맞는 파일 이름인지"""
    import re
    return bool(re.fullmatch(r"[a-z0-9_]{8,64}\.(mp3|wav)", fname))
