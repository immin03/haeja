"""타입캐스트 사용량을 Supabase tts_usage 에 남긴다 (2026-11-12 대표: 비용 추적 놓치지 말 것).
모든 렌더(롱폼·쇼츠·빠른 렌더·사이드)가 이 모듈로 기록한다. 실행이 끝날 때 한 번에 보낸다.
 - chars: 타입캐스트에 새로 요청한 글자 수(= 크레딧) / cached_chars: 저장된 음성을 다시 써서 아낀 글자 수
 - 기록 실패는 렌더를 멈추지 않는다
"""
import atexit, json, os, urllib.request

URL = "https://msjbrwyzkiueqnzjeicm.supabase.co/functions/v1/vn-tts-log"
ITEM = {"id": os.environ.get("TTS_ITEM", "")}
_rows = {}


def set_item(item):
    ITEM["id"] = str(item or "")


def add(chars=0, cached=0, lang="ko"):
    k = (ITEM["id"], lang)
    r = _rows.setdefault(k, {"item": k[0], "lang": lang, "chars": 0, "cached_chars": 0})
    r["chars"] += int(chars); r["cached_chars"] += int(cached)


@atexit.register
def flush():
    rows = [r for r in _rows.values() if r["chars"] or r["cached_chars"]]
    run = os.environ.get("GITHUB_RUN_ID")
    if not rows:
        return
    tot = sum(r["chars"] for r in rows); sav = sum(r["cached_chars"] for r in rows)
    print(f"[타입캐스트] 이번 실행 새로 산 글자 {tot:,}자 · 저장된 음성 재사용 {sav:,}자")
    if not run:
        return
    try:
        body = json.dumps({"run_id": run, "workflow": os.environ.get("GITHUB_WORKFLOW", ""), "rows": rows}).encode()
        urllib.request.urlopen(urllib.request.Request(URL, data=body, method="POST",
                               headers={"Content-Type": "application/json"}), timeout=20).read()
        _rows.clear()
    except Exception as e:
        print("  사용량 기록 실패(렌더는 그대로):", e)
