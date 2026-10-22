"""한국어 음성 합성.
기본: 타입캐스트 성우 '성호' (2026-10-21 운영자 결정, 건석에서 변경, 릴스·유튜브 공통). TYPECAST_API_KEY 가 있으면 사용한다.
예비: 키가 없거나 호출이 실패하면 로컬 Supertonic 3 (sherpa-onnx) 로 만든다.
"""
import os, tarfile, urllib.request
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "sherpa-onnx-supertonic-3-tts-int8-2026-05-11"
URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{NAME}.tar.bz2"
CACHE = os.environ.get("TTS_CACHE", os.path.join(HERE, ".cache"))
VOICE_ID = 5        # 차분한 남성 (0~4 여성, 5~9 남성)
SR = 44100
_tts = None


def _model_dir():
    d = os.path.join(CACHE, NAME)
    if not os.path.exists(os.path.join(d, "tts.json")):
        os.makedirs(CACHE, exist_ok=True)
        tgz = os.path.join(CACHE, NAME + ".tar.bz2")
        print("음성 모델 내려받는 중…")
        urllib.request.urlretrieve(URL, tgz)
        with tarfile.open(tgz) as t: t.extractall(CACHE)
        os.remove(tgz)
    return d + "/"


def _engine():
    global _tts
    if _tts is None:
        import sherpa_onnx as so
        D = _model_dir()
        cfg = so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(supertonic=so.OfflineTtsSupertonicModelConfig(
            duration_predictor=D + "duration_predictor.int8.onnx", text_encoder=D + "text_encoder.int8.onnx",
            vector_estimator=D + "vector_estimator.int8.onnx", vocoder=D + "vocoder.int8.onnx",
            tts_json=D + "tts.json", unicode_indexer=D + "unicode_indexer.bin", voice_style=D + "voice.bin"),
            num_threads=4))
        _tts = so.OfflineTts(cfg)
    return _tts


def _gen(text, speed, steps):
    import sherpa_onnx as so
    g = so.GenerationConfig(); g.sid = VOICE_ID; g.num_steps = steps; g.speed = speed; g.extra["lang"] = "ko"
    a = _engine().generate(text, g)
    x = np.asarray(a.samples, dtype=np.float32)
    if a.sample_rate != SR:
        from scipy.signal import resample_poly
        x = resample_poly(x, SR, a.sample_rate).astype(np.float32)
    idx = np.where(np.abs(x) > 0.012)[0]
    if len(idx): x = x[max(0, idx[0] - int(.06 * SR)): idx[-1] + int(.12 * SR)]
    return x


def clauses(text, maxlen=22):
    """긴 문장을 마침표·물음표, 길면 쉼표에서 나눈다 (한 번에 길게 읽히면 음절을 빼먹는다)"""
    import re
    out = []
    for s in re.findall(r"[^.?!]+[.?!]?", text):
        s = s.strip()
        if not s: continue
        if len(s) <= maxlen: out.append(s); continue
        parts = re.findall(r"[^,]+,?", s); cur = ""
        for p in parts:
            p = p.strip()
            if cur and len(cur) + len(p) > maxlen: out.append(cur); cur = p
            else: cur = (cur + " " + p).strip()
        if cur: out.append(cur)
    return out or [text]


# ── 타입캐스트 ────────────────────────────────────────────────
TC_VOICE = os.environ.get("TYPECAST_VOICE_ID", "tc_5fe06471a9f79e8f959be96f")  # 성호 (중년 남성, 다큐·스토리텔링)
TC_MODEL = "ssfm-v30"
TC_BASE_SPEED = 1.1  # 대본의 speed 1.1 = 타입캐스트 기본 속도
TC_CACHE = os.path.join(CACHE, "typecast")


def _typecast(text, speed, fresh=False):
    """타입캐스트로 읽어 44.1kHz mono float 배열을 돌려준다. 같은 문장은 캐시를 쓴다 (크레딧 절약)"""
    import hashlib, json, subprocess, urllib.request, urllib.error
    tempo = round(min(1.3, max(.85, speed / TC_BASE_SPEED)), 2)
    key = hashlib.sha1(f"{TC_VOICE}|{TC_MODEL}|{tempo}|{text}".encode()).hexdigest()[:20]
    os.makedirs(TC_CACHE, exist_ok=True)
    mp3 = os.path.join(TC_CACHE, key + ".mp3")
    if fresh and os.path.exists(mp3): os.remove(mp3)   # 이상한 소리가 섞인 결과는 버리고 다시 받는다
    if not os.path.exists(mp3):
        # 요청 형식이 거절되면 단순한 형식으로 한 번 더 (키 점검 때 통과한 형식이 마지막)
        bodies = [
            {"text": text, "model": TC_MODEL, "voice_id": TC_VOICE, "language": "kor",
             "output": {"audio_format": "mp3", "audio_tempo": tempo}},
            {"text": text, "model": TC_MODEL, "voice_id": TC_VOICE, "language": "kor",
             "output": {"audio_format": "mp3"}},
        ]
        last = None
        for body in bodies:
            req = urllib.request.Request("https://api.typecast.ai/v1/text-to-speech", method="POST",
                                         data=json.dumps(body).encode(),
                                         headers={"X-API-KEY": os.environ["TYPECAST_API_KEY"],
                                                  "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    open(mp3, "wb").write(r.read())
                break
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}"
                if e.code not in (400, 422): raise RuntimeError(last)
        else:
            raise RuntimeError(last)
        _log_usage(len(text))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).copy()
    idx = np.where(np.abs(x) > 0.012)[0]
    if len(idx): x = x[max(0, idx[0] - int(.06 * SR)): idx[-1] + int(.12 * SR)]
    return x


def _log_usage(n):
    """이번 달 타입캐스트 사용 글자 수를 기록한다 (관리자 알림용: 15만 자 넘으면 경고)"""
    import json, datetime
    p = os.path.join(HERE, "..", "..", "social", "typecast_usage.json")
    try: u = json.load(open(p))
    except Exception: u = {}
    m = datetime.date.today().strftime("%Y-%m")
    u[m] = u.get(m, 0) + n
    json.dump(u, open(p, "w"), ensure_ascii=False, indent=1)
    if u[m] > 150000: print(f"⚠ 타입캐스트 이번 달 사용량 {u[m]:,}자 — 라이트 한도 20만 자에 가깝습니다")


def speak(text, speed=1.15, steps=8, chunk=True, fresh=False):
    """text(한글 발음) → 44.1kHz mono float 배열.
    타입캐스트: 문장 단위로 한 번에 읽는다. 로컬 예비: 절 단위로 나눠 읽고 짧은 쉼을 넣어 잇는다"""
    if os.environ.get("TYPECAST_API_KEY"):
        # 목소리가 섞이면 안 되므로 로컬 음성으로 몰래 바꾸지 않는다: 두 번 실패하면 이 릴스는 실패 처리
        import time
        for i in range(3):
            try:
                return _typecast(text, speed, fresh)
            except Exception as e:
                err = e; print(f"타입캐스트 호출 실패({i + 1}/3):", str(e)[:200]); time.sleep(3 * (i + 1))
        raise RuntimeError(f"타입캐스트 음성 생성 실패: {err}")
    if not chunk: return _gen(text, speed, steps)
    segs = []
    for c in clauses(text):
        segs.append(_gen(c, speed, steps))
        segs.append(np.zeros(int((.12 if c.endswith(",") else .2) * SR), dtype=np.float32))
    return np.concatenate(segs[:-1]) if segs else np.zeros(1, dtype=np.float32)
