"""What Korea Says — 작업 진행률을 관리자 페이지(/side '작업 현황' 탭)로 보낸다 (2026-10-27)
Supabase sc_job_report() 함수에 토큰과 함께 기록. 표가 아직 없거나 실패해도 작업은 멈추지 않는다.
"""
import json, os, time, urllib.request

URL = "https://msjbrwyzkiueqnzjeicm.supabase.co/rest/v1/rpc/sc_job_report"
ANON = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1zamJyd3l6a2l1ZXFuemplaWNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE4NTk0NTcsImV4cCI6MjEwNzQzNTQ1N30."
        "RIq2MRW8bwHQUO_dPeIarujjWcYD_dXn06icr1Mpmuw")
# 진행률 기록 전용 토큰 (sc_jobs 한 표에만 쓸 수 있다). 비공개 저장소라 여기 둔다
TOKEN = os.environ.get("SIDE_PROGRESS_TOKEN") or "27c7b3f57250c6142046400d2e14e6e337325abdef2302fb"
_last = {}


def run_url():
    if os.environ.get("GITHUB_RUN_ID"):
        return f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{os.environ.get('GITHUB_REPOSITORY', 'immin03/haeja')}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    return None


def report(jid, label=None, status="running", pct=None, detail=None, cost=None, kind="render", every=0):
    """every 초보다 자주 부르면 건너뜀 (끝·실패는 항상 보냄)"""
    now = time.time()
    if every and status == "running" and now - _last.get(jid, 0) < every: return
    _last[jid] = now
    body = {"p_token": TOKEN, "p_id": jid, "p_kind": kind, "p_label": label, "p_status": status,
            "p_pct": None if pct is None else round(float(pct), 1), "p_detail": detail, "p_cost": cost, "p_run_url": run_url()}
    try:
        req = urllib.request.Request(URL, method="POST", data=json.dumps(body).encode(),
                                     headers={"apikey": ANON, "Authorization": "Bearer " + ANON, "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:
        if not _last.get("_warned"): print("진행률 기록 안 됨(무시):", str(e)[:120], flush=True); _last["_warned"] = 1
