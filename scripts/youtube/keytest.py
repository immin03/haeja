"""유튜브 준비: 네이버 API HUB·타입캐스트 키 점검 + 성우 샘플 6개 만들기.
결과는 scripts/youtube/samples/ 에 저장한다 (키 값은 절대 기록하지 않는다).
"""
import json, os, datetime, urllib.request, urllib.parse, urllib.error

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
os.makedirs(OUT, exist_ok=True)
report = {"run_at": datetime.datetime.utcnow().isoformat() + "Z"}

SAMPLE = (
    "SK하이닉스는 메모리 반도체를 만드는 세계 2위 회사입니다. "
    "SK하이닉스의 올해 매출은 크게 늘었습니다. "
    "그런데 이 매출은 반도체를 더 많이 팔아서 늘어난 것이 아닙니다. "
    "반도체 가격이 올라서 늘어난 것입니다. "
    "가격은 언젠가 다시 내려옵니다. "
    "그래서 워렌 버핏의 기준으로 계산하면, SK하이닉스의 적정 주가는 지금 주가보다 낮게 나옵니다. "
    "오늘은 그 이유를 숫자로 하나씩 살펴보겠습니다."
)


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

    # 뉴스·다큐·해설에 맞는 청년·중년 목소리 6개 (남 3, 여 3)
    WANT = ["Sean", "Rex", "Tyson", "Mia", "Rachel", "Margot"]
    by = {(v.get("voice_name") or {}).get("eng"): v for v in voices}
    picks = [by[n] for n in WANT if n in by]
    report["picks"] = []
    for i, v in enumerate(picks, 1):
        vid = v.get("voice_id") or v.get("id")
        body = {"text": SAMPLE, "model": "ssfm-v30", "voice_id": vid, "language": "kor",
                "output": {"audio_format": "mp3"}}
        st, audio = call("https://api.typecast.ai/v1/text-to-speech", "POST", th, body, raw=True)
        if st != 200:
            body.pop("language")
            st, audio = call("https://api.typecast.ai/v1/text-to-speech", "POST", th, body, raw=True)
        fn = None
        if st == 200 and isinstance(audio, (bytes, bytearray)):
            fn = f"voice-{i}-{gender(v)}-{(v.get('voice_name') or {}).get('eng', 'x').lower()}.mp3"
            open(os.path.join(OUT, fn), "wb").write(audio)
        report["picks"].append({"no": i, "voice_id": vid, "name": v.get("voice_name") or v.get("name"),
                                "gender": gender(v), "age": v.get("age"), "use_cases": v.get("use_cases"),
                                "status": st, "file": fn, "error": None if st == 200 else audio})
else:
    report["typecast_error"] = voices

json.dump(report, open(os.path.join(OUT, "report.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(report, ensure_ascii=False, indent=1)[:4000])
