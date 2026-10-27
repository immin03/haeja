"""What Korea Says — Higgsfield 이미지·영상 생성기 (2026-10-27)
작업 목록: scripts/side/gen/*.json  (리스트)
  {"id": "c_magpie_q", "kind": "image", "endpoint": "alibaba/qwen-image-3/text-to-image",
   "body": {"prompt": "...", "aspect_ratio": "1:1"}, "ref": "social/side/gen/x.png" (선택: 참고 이미지, 저장소 경로)}
  {"id": "v_store", "kind": "video", "endpoint": "alibaba/wan-3.0/image-to-video",
   "image": "social/side/gen/k_store.png", "body": {"prompt": "...", "duration": 5}}
결과: social/side/gen/<id>.(png|jpg|mp4) + social/side/gen/<id>.json (요청·상태·비용 추정·에러)
- 이미 결과 파일이 있으면 건너뛴다 (같은 장면을 두 번 돈 내고 만들지 않는다)
- 제출이 거절되면(필드 이름이 다르거나 하면) 응답을 그대로 기록해서 다음 수정에 쓴다 — 거절은 과금되지 않는다
- 한 번 실행에 쓸 수 있는 돈 상한: 환경변수 SIDE_GEN_MAX_USD (기본 3달러)
"""
import glob, json, os, sys, time, uuid, urllib.request, urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "higgsfield"))
import hf  # noqa: E402  (http, auth_headers 재사용)

OUT = os.path.join(ROOT, "social", "side", "gen")
REPO = os.environ.get("GITHUB_REPOSITORY", "immin03/haeja")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
PRICE = {  # 대략 단가 (open.higgsfield.ai 2026-10-27 표시가, 할인 반영) — 상한 계산용
    "image": 0.05, "video_per_s": {"wan-3.0/": 0.02, "wan-3.0-prime": 0.027, "kling": 0.11, "seedance": 0.15, "grok": 0.08}}


def est(job):
    if job["kind"] == "image": return PRICE["image"] * int(job.get("body", {}).get("num_images", 1))
    d = float(job.get("body", {}).get("duration", 5))
    for k, v in PRICE["video_per_s"].items():
        if k in job["endpoint"]: return v * d
    return 0.15 * d


def find_url(obj, exts):
    s = json.dumps(obj)
    import re
    for m in re.findall(r'https://[^"\s]+', s):
        if any(m.split("?")[0].lower().endswith(e) for e in exts): return m
    return None


def raw_url(path): return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}"


def run(job, H, spent):
    jid = job["id"]; os.makedirs(OUT, exist_ok=True)
    exts = (".mp4", ".webm", ".mov") if job["kind"] == "video" else (".png", ".jpg", ".jpeg", ".webp")
    for e in exts:
        if os.path.exists(os.path.join(OUT, jid + e)): print(f"[{jid}] 이미 있음"); return 0.0
    cost = est(job); cap = float(os.environ.get("SIDE_GEN_MAX_USD", "3"))
    if spent + cost > cap: print(f"[{jid}] 상한 {cap}달러 초과 예상 — 건너뜀"); return 0.0
    body = dict(job.get("body", {}))
    if job.get("image"): body[job.get("image_field", "image_url")] = raw_url(job["image"])
    if job.get("ref"): body[job.get("ref_field", "image_urls")] = [raw_url(r) for r in (job["ref"] if isinstance(job["ref"], list) else [job["ref"]])]
    key = str(uuid.uuid5(uuid.NAMESPACE_URL, jid + json.dumps(body, sort_keys=True)))
    t0 = time.time(); st, js = hf.http("POST", f"{hf.BASE}/{job['endpoint']}", {**H, "Idempotency-Key": key}, body)
    rec = {"id": jid, "endpoint": job["endpoint"], "body": body, "submit_http": st, "submit": js, "est_usd": round(cost, 3)}
    print(f"[{jid}] 제출 {st}: {json.dumps(js, ensure_ascii=False)[:300]}", flush=True)
    if st >= 300 or "request_id" not in js:
        rec["status"] = "submit_failed"; json.dump(rec, open(os.path.join(OUT, jid + ".json"), "w"), ensure_ascii=False, indent=1); return 0.0
    url = js.get("status_url") or f"{hf.BASE}/requests/{js['request_id']}/status"; status, s = None, {}
    while time.time() - t0 < 15 * 60:
        time.sleep(6); _, s = hf.http("GET", url, H); status = s.get("status")
        if status in ("completed", "failed", "nsfw", "canceled"): break
    rec.update(status=status, result=s, seconds=round(time.time() - t0))
    out_url = find_url(s, exts)
    if status == "completed" and out_url:
        ext = os.path.splitext(out_url.split("?")[0])[1].lower() or exts[0]
        dst = os.path.join(OUT, jid + ext); urllib.request.urlretrieve(out_url, dst)
        rec["file"] = os.path.relpath(dst, ROOT); print(f"[{jid}] 저장 {rec['file']} {os.path.getsize(dst) // 1024}KB {rec['seconds']}s", flush=True)
    json.dump(rec, open(os.path.join(OUT, jid + ".json"), "w"), ensure_ascii=False, indent=1)
    return cost if status == "completed" else 0.0


def main(only=None):
    H = hf.auth_headers(); spent = 0.0
    files = sorted(glob.glob(os.path.join(ROOT, "scripts", "side", "gen", "*.json")))
    for f in files:
        if only and os.path.basename(f)[:-5] not in only: continue
        for job in json.load(open(f, encoding="utf-8")):
            if job.get("disabled"): continue
            # 앞 작업 결과(같은 실행에서 만든 이미지)를 영상 입력으로 쓰는 경우: 커밋 전이라 raw 주소가 없다 → 업로드 경로로 대체
            if job.get("image") and not os.path.exists(os.path.join(ROOT, job["image"])):
                stem = os.path.splitext(job["image"])[0]
                alt = next((stem + e for e in (".png", ".jpg", ".jpeg", ".webp") if os.path.exists(os.path.join(ROOT, stem + e))), None)
                if not alt: print(f"[{job['id']}] 입력 이미지 없음 — 다음 실행에서"); continue
                job["image"] = alt
            spent += run(job, H, spent)
    print(f"이번 실행 예상 비용 합계: {spent:.2f}달러")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
