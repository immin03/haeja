"""유튜브 준비: 네이버 API HUB·타입캐스트 키 점검 + 성우 샘플 6개 만들기.
결과는 scripts/youtube/samples/ 에 저장한다 (키 값은 절대 기록하지 않는다).
"""
import json, os, datetime, urllib.request, urllib.parse, urllib.error

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
os.makedirs(OUT, exist_ok=True)
report = {"run_at": datetime.datetime.utcnow().isoformat() + "Z"}

SAMPLE = ("미국은 이 년 넘게 단기 금리가, 장기 금리보다 높았습니다. "
          "대출 이자가 늘면, 사람들은 돈을 덜 쓰고 경기가 식습니다.")  # 2026-10-22 릴스 성우 비교 (장단기 금리 릴스 대본)
# (이름, 감정, 빠르기): 릴스용 — 톤은 낮게, 더 경쾌하고 빠르게
TRY = [("Sungho", None, 1.0), ("Sungho", None, 1.18), ("Sungho", "toneup", 1.18), ("Doyoon", "toneup", 1.15), ("Sanghyun", "toneup", 1.15),
       ("Byunghun", "toneup", 1.15), ("Wonwoo", "toneup", 1.15), ("Kangil", "toneup", 1.15), ("Jungseok", "toneup", 1.15)]


def call(url, method="GET", headers=None, body=None, raw=False):
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers = {**(headers or {}), "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            b = r.read()
            return r.status, (b if raw else json.loads(b.decode() or "null"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")[:500]
    except Exception as e:  # 네트워크 오류
        return -1, str(e)[:300]


# ── 네이버 API HUB ──
nid, nsec = os.environ.get("NAVER_CLIENT_ID", ""), os.environ.get("NAVER_CLIENT_SECRET", "")
nh = {"X-NCP-APIGW-API-KEY-ID": nid, "X-NCP-APIGW-API-KEY": nsec}
HUB = "https://naverapihub.apigw.ntruss.com"
report["naver_keys_present"] = bool(nid and nsec)
today = datetime.date.today()
st, res = call(HUB + "/search-trend/v1/search", "POST", nh, {
    "startDate": (today - datetime.timedelta(days=30)).isoformat(), "endDate": today.isoformat(),
    "timeUnit": "date", "keywordGroups": [
        {"groupName": "삼성전자", "keywords": ["삼성전자", "삼성전자 주가"]},
        {"groupName": "SK하이닉스", "keywords": ["SK하이닉스", "하이닉스 주가"]}]})
report["naver_trend"] = {"status": st, "sample": res if st != 200 else {
    g["title"]: (g["data"][-1] if g.get("data") else None) for g in res.get("results", [])}}
for name, path in [("news", "/search/v1/news"), ("cafe", "/search/v1/cafearticle"),
                   ("blog", "/search/v1/blog"), ("kin", "/search/v1/kin")]:
    q = urllib.parse.urlencode({"query": "SK하이닉스 주가", "display": 2, "format": "json"})
    st, res = call(f"{HUB}{path}?{q}", headers=nh)
    report[f"naver_{name}"] = {"status": st, "sample": [i.get("title") for i in res.get("items", [])][:2]
                               if st == 200 and isinstance(res, dict) else res}

# ── 타입캐스트 ──
tk = os.environ.get("TYPECAST_API_KEY", "")
th = {"X-API-KEY": tk}
report["typecast_key_present"] = bool(tk)
st, voices = call("https://api.typecast.ai/v3/voices?model=ssfm-v30", headers=th)
report["typecast_voices"] = {"status": st, "count": len(voices) if isinstance(voices, list) else None}
if st == 200 and isinstance(voices, list):
    json.dump(voices, open(os.path.join(OUT, "voices.json"), "w"), ensure_ascii=False, indent=1)
    good = ("news", "narrat", "documentary", "announc", "audiobook", "e-learning", "explainer", "conversational")

    def score(v):
        s = json.dumps(v, ensure_ascii=False).lower()
        return sum(k in s for k in good) + (2 if "kor" in s or "ko" in str(v.get("languages", "")).lower() else 0)

    def gender(v):
        return str(v.get("gender", "")).lower()

    # 2차 후보: 션과 결이 비슷하면서 개성 있는 남성 해설·다큐 목소리 6개
    by = {(v.get("voice_name") or {}).get("eng"): v for v in voices}
    report["picks"] = []
    for i, (nm, emo, tempo) in enumerate(TRY, 1):
        v = by.get(nm)
        if not v: report["picks"].append({"no": i, "name": nm, "error": "없음"}); continue
        vid = v.get("voice_id")
        body = {"text": SAMPLE, "model": "ssfm-v30", "voice_id": vid, "language": "kor", "output": {"audio_format": "mp3", "audio_tempo": tempo}}
        if emo: body["prompt"] = {"emotion_preset": emo, "emotion_intensity": 1.2}
        st, audio = call("https://api.typecast.ai/v1/text-to-speech", "POST", th, body, raw=True)
        note = ""
        if st != 200 and emo:  # 감정 지정이 거절되면 감정 없이
            body.pop("prompt"); note = "감정 지정 거절됨"
            st, audio = call("https://api.typecast.ai/v1/text-to-speech", "POST", th, body, raw=True)
        fn = None
        if st == 200 and isinstance(audio, (bytes, bytearray)):
            fn = f"reel-{i}-{nm.lower()}-{emo or 'normal'}-x{tempo}.mp3"
            open(os.path.join(OUT, fn), "wb").write(audio)
        report["picks"].append({"no": i, "name": (v.get("voice_name") or {}), "age": v.get("age"), "use_cases": v.get("use_cases"),
                                "emotion": emo, "tempo": tempo, "status": st, "file": fn, "note": note, "error": None if st == 200 else str(audio)[:300]})
else:
    report["typecast_error"] = voices

# ── 릴스 엔진 음성 점검 ──
import sys, traceback
sys.path.insert(0, os.path.join(os.path.dirname(OUT), "..", "reels"))
try:
    import tts
    a = tts.speak("SK하이닉스는 메모리 반도체를 만드는 세계 2위 회사입니다.", 1.1)
    report["engine_tts"] = {"ok": True, "sec": round(len(a) / tts.SR, 2), "voice": tts.TC_VOICE}
except Exception:
    report["engine_tts"] = {"ok": False, "error": traceback.format_exc()[-1500:]}

json.dump(report, open(os.path.join(OUT, "report.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(report, ensure_ascii=False, indent=1)[:4000])
