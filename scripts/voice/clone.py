"""운영자 목소리 클로닝 (2026-10-24 운영자 요청: "클로닝으로 한번 해보고 싶어")

녹음 원본은 공개 저장소에 평문으로 올리지 않는다.
voice-clone 워크플로가 만든 1회용 공개키로 암호화한 파일만 voice-xchg 가지에 오가고,
결과(샘플 mp3·voice_id)도 요청자 공개키(requester_pub.pem)로 암호화해 돌려준다.

이 스크립트는 워크플로 안에서 복호화된 clean.wav 를 받아
1) 타입캐스트 빠른 클로닝(5~150초)으로 목소리를 만들고
2) 같은 문장을 클로닝 목소리와 지금 성우 '성호'로 읽은 비교 샘플을 만든다.
"""
import json, os, sys, urllib.request, urllib.error, uuid

KEY = os.environ["TYPECAST_API_KEY"]
SEONGHO = "tc_5fe06471a9f79e8f959be96f"
MODEL = "ssfm-v30"

SAMPLES = [
    ("hook", "석 달에 107조 원. 삼성전자가 이번 3분기에 번 영업이익입니다. 하루로 치면 매일 1조 원 넘게 번 셈이에요. 주말에도, 추석 연휴에도요."),
    ("explain", "PER은 주가가 1년 이익의 몇 배인지예요. 3배면 3년 남짓 벌면 회사 값을 다 번다는 뜻이니, 거의 창고 대방출 가격이죠. 근데 여기서 함정이 하나 있어요."),
    ("close", "그래서 오늘 결론은 딱 하나예요. 숫자가 싸 보일 때일수록, 그 이익이 몇 년 갈지 한 번만 더 물어보자. 다음에 또 재밌는 이야기 들고 올게요!"),
]


def multipart(fields, file_field, path, ctype):
    b = uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    out += (f"--{b}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{os.path.basename(path)}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + open(path, "rb").read() + b"\r\n"
    out += f"--{b}--\r\n".encode()
    return out, f"multipart/form-data; boundary={b}"


def clone(wav, name):
    body, ct = multipart({"name": name, "model": MODEL}, "file", wav, "audio/wav")
    last = None
    for url in ("https://api.typecast.ai/v1/custom-voices/instant-clone", "https://api.typecast.ai/v1/voices/clone"):
        req = urllib.request.Request(url, data=body, method="POST", headers={"X-API-KEY": KEY, "Content-Type": ct})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read()), url
        except urllib.error.HTTPError as e:
            last = f"{url} HTTP {e.code}: {e.read().decode(errors='replace')[:400]}"
            print(last, flush=True)
            if e.code not in (404, 405): break
    raise SystemExit("클로닝 실패: " + str(last))


def speak(voice, text, out):
    body = {"text": text, "model": MODEL, "voice_id": voice, "language": "kor", "output": {"audio_format": "mp3"}}
    req = urllib.request.Request("https://api.typecast.ai/v1/text-to-speech", data=json.dumps(body).encode(), method="POST",
                                 headers={"X-API-KEY": KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            open(out, "wb").write(r.read())
        return None
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}"


def main(wav, outdir):
    os.makedirs(outdir, exist_ok=True)
    res, url = clone(wav, "ValueNote owner voice 1")
    vid = res.get("voice_id") or (res.get("result") or {}).get("voice_id")
    report = {"clone_endpoint": url, "clone_response": res, "voice_id": vid, "samples": [], "chars": 0}
    for key, text in SAMPLES:
        for tag, v in (("clone", vid), ("seongho", SEONGHO)):
            p = os.path.join(outdir, f"{key}_{tag}.mp3")
            err = speak(v, text, p)
            report["samples"].append({"file": os.path.basename(p), "voice": tag, "error": err})
            report["chars"] += len(text)
    json.dump(report, open(os.path.join(outdir, "report.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: report[k] for k in ("clone_endpoint", "voice_id", "chars")}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
