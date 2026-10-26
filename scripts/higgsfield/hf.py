"""Higgsfield API 호출기 (2026-10-26) — 팝업 노트의 '영상 팝업' 카드를 AI 영상으로 만든다.

키: GitHub 저장소 비밀값 HF_API_KEY (콘솔에서 복사한 키 그대로).
    예전 형식(HF_API_KEY_ID + HF_API_KEY_SECRET)도 받는다.
작업 목록: scripts/higgsfield/jobs/*.json
    {"id": "pike_walk", "endpoint": "bytedance/seedance-2.5/image-to-video",
     "image": "scripts/higgsfield/in/pike_card.jpg", "body": {"prompt": "...", "duration": 5, ...},
     "max_usd": 2.0}
    "check_only": true 이면 키만 확인하고 생성하지 않는다(돈 안 듦).
결과: scripts/higgsfield/out/<id>.mp4 + <id>.json (요청 id·상태·걸린 시간). 이미 있으면 건너뛴다.
생성 파일은 Higgsfield 서버에 7일만 남으므로 바로 내려받아 저장소에 넣는다.

실행:  python3 scripts/higgsfield/hf.py  (GitHub Actions: .github/workflows/higgsfield.yml)
"""
import glob, json, os, sys, time, uuid
import urllib.request, urllib.error

BASE = "https://api.higgsfield.ai"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "scripts", "higgsfield", "out")
REPO = os.environ.get("GITHUB_REPOSITORY", "immin03/haeja")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")


def http(method, url, headers, body=None, timeout=60):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={**headers, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(); return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try: return e.code, json.loads(raw)
        except Exception: return e.code, {"raw": raw[:500].decode("utf8", "replace")}


def auth_headers():
    """콘솔 키 형식을 몰라도 되게: 가능한 형식을 차례로 시험해 401/403 이 아닌 것을 쓴다"""
    k = os.environ.get("HF_API_KEY", "").strip()
    kid, sec = os.environ.get("HF_API_KEY_ID", "").strip(), os.environ.get("HF_API_KEY_SECRET", "").strip()
    cands = []
    if kid and sec: cands.append({"Authorization": f"Key {kid}:{sec}"})
    if k:
        cands.append({"Authorization": f"Key {k}"})
        if ":" in k:
            a, b = k.split(":", 1); cands.append({"hf-api-key": a, "hf-secret": b})
        cands.append({"Authorization": f"Bearer {k}"})
    if not cands: sys.exit("HF_API_KEY 비밀값이 없습니다 (GitHub → Settings → Secrets and variables → Actions)")
    probe = f"{BASE}/requests/{uuid.UUID(int=0)}/status"
    for h in cands:
        st, js = http("GET", probe, h)
        name = list(h)[0] + (" " + h["Authorization"].split()[0] if "Authorization" in h else "")
        print(f"키 확인 [{name}] → HTTP {st}")
        if st not in (401, 403): return h
    sys.exit("키가 거부됐습니다 (401/403). 콘솔에서 키를 다시 복사해 HF_API_KEY 를 바꿔 주세요.")


def run_job(job, H):
    jid = job["id"]; mp4 = os.path.join(OUT, jid + ".mp4"); meta = os.path.join(OUT, jid + ".json")
    if os.path.exists(mp4): print(f"[{jid}] 이미 있음 — 건너뜀"); return
    body = dict(job.get("body", {}))
    if job.get("image"):
        body["image_url"] = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{job['image']}"
    key = str(uuid.uuid5(uuid.NAMESPACE_URL, jid + json.dumps(body, sort_keys=True)))
    t0 = time.time()
    st, js = http("POST", f"{BASE}/{job['endpoint']}", {**H, "Idempotency-Key": key}, body)
    print(f"[{jid}] 제출 HTTP {st}: {json.dumps(js, ensure_ascii=False)[:400]}")
    rec = {"id": jid, "endpoint": job["endpoint"], "body": body, "submit_http": st, "submit": js, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if st >= 300 or "request_id" not in js:
        rec["status"] = "submit_failed"; json.dump(rec, open(meta, "w"), ensure_ascii=False, indent=1); return
    url = js.get("status_url") or f"{BASE}/requests/{js['request_id']}/status"
    while time.time() - t0 < 20 * 60:
        time.sleep(10)
        st, s = http("GET", url, H)
        status = s.get("status")
        print(f"[{jid}] {int(time.time() - t0)}s 상태 {status}")
        if status in ("completed", "failed", "nsfw", "canceled"): break
    rec.update(status=status, result=s, seconds=round(time.time() - t0))
    v = (s.get("video") or {}).get("url") if isinstance(s.get("video"), dict) else None
    if status == "completed" and v:
        urllib.request.urlretrieve(v, mp4); rec["file"] = os.path.relpath(mp4, ROOT)
        print(f"[{jid}] 저장 {mp4} ({os.path.getsize(mp4) // 1024} KB)")
    json.dump(rec, open(meta, "w"), ensure_ascii=False, indent=1)


def main():
    os.makedirs(OUT, exist_ok=True)
    H = auth_headers()
    jobs = []
    for f in sorted(glob.glob(os.path.join(ROOT, "scripts", "higgsfield", "jobs", "*.json"))):
        j = json.load(open(f)); jobs += j if isinstance(j, list) else [j]
    for j in jobs:
        if j.get("check_only"): print(f"[{j['id']}] 키 확인만 — 생성 안 함"); continue
        if j.get("disabled"): continue
        run_job(j, H)


if __name__ == "__main__":
    main()
