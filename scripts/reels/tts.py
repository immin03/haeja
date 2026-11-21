"""한국어 음성 합성.
기본: 운영자 목소리 클론 (2026-10-25 운영자 결정, 이전 성우 '성호' 대체, 롱폼·쇼츠·릴스 공통), 속도 1.1배.
타입캐스트 API 로 클로닝한 목소리이며 TYPECAST_API_KEY 가 있으면 사용한다. 후처리(가속·톤 올림)는 하지 않는다.
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
CLONE_VOICE = "uc_6addc9b84bd9f624e177b63b"   # 운영자 목소리 클론 (ValueNote_Minwoo, 2026-10-25)
SEONGHO = "tc_5fe06471a9f79e8f959be96f"       # 이전 성우 '성호' (되돌릴 때만)
TC_VOICE = os.environ.get("TYPECAST_VOICE_ID", CLONE_VOICE)
TC_MODEL = "ssfm-v30"
TC_BASE_SPEED = 1.1  # 대본의 speed 1.1 = 기준 속도
VOICE_TEMPO = 1.1    # 2026-10-25 운영자 확정: 클론 목소리는 타입캐스트 audio_tempo 1.1배로 받는다 (대본 speed 1.1 일 때)
TC_CACHE = os.path.join(CACHE, "typecast")


# 2026-11-21 재렌더 효율 (대표: "같은 걸 반복 렌더할 때 최대 효율"):
#  1) 다시 받기(재녹음)는 캐시를 지우지 않고 '테이크 번호'로 따로 보관한다. 예전엔 품질 검사에서 걸리면 원본을 지우고 새로 사서
#     같은 자리에 덮어썼기 때문에, 다음 렌더에서 또 걸리면 또 샀다(렌더할 때마다 같은 줄을 1~2번씩 재구매).
#     이제 테이크 0·1·2 가 각각 남아 두 번째 렌더부터는 같은 줄에 0원.
#  2) 영구 음성 보관함(tts_store, Supabase Storage)을 로컬 캐시 뒤에 둔다 — actions/cache 가 날아가도 다시 사지 않는다.
#  3) 문장 앞뒤·중간 공백 차이로 키가 달라지지 않게 공백을 정리한 문장으로 키를 만든다(예전 키도 함께 찾는다).
#  4) 속도만 바꿨을 때(1.1 → 1.07 등, 11/17 22:56 에 이 이유로 롱폼 한 편 4,781자를 다시 삼): 가까운 속도(±8%)로 산 녹음이
#     있으면 ffmpeg atempo 로 속도만 맞춰 쓴다(음높이 유지). TTS_EXACT_TEMPO=1 이면 이 재사용을 끄고 정확한 속도로 산다.
NEAR_TEMPOS = (1.1, 1.07, 1.05, 1.03, 1.0, 1.12, 1.15, 1.2, 1.21)


def _norm(text):
    import re
    return re.sub(r"\s+", " ", text or "").strip()


def _tc_key(text, tempo, take=0):
    import hashlib
    k = hashlib.sha1(f"{TC_VOICE}|{TC_MODEL}|{tempo}|{text}".encode()).hexdigest()[:20]
    return k if not take else f"{k}_t{int(take)}"


def _decode(mp3, ratio=1.0):
    import subprocess
    af = ["-af", f"atempo={ratio:.4f}"] if abs(ratio - 1) > .004 else []
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, *af, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).copy()
    idx = np.where(np.abs(x) > 0.012)[0]
    if len(idx): x = x[max(0, idx[0] - int(.06 * SR)): idx[-1] + int(.12 * SR)]
    return x


def _find(text, raw_text, tempo, take):
    """이미 산 녹음 찾기 → (mp3 경로, 속도 보정 비율) 또는 (None, None).
    로컬에 있으면 네트워크 없이 바로. 없을 때만 보관함에 '한 번' 묻는다(정확한 키·예전 키·가까운 속도를 한 요청으로),
    있으면 그 파일 하나만 내려받는다 → 처음 사는 문장도 추가 요청은 1번뿐 (2026-11-21 효율 점검)"""
    import tts_store
    cand = [(_tc_key(text, tempo, take), 1.0)]
    if raw_text != text: cand.append((_tc_key(raw_text, tempo, take), 1.0))   # 공백 정리 전 예전 키
    if not take and not os.environ.get("TTS_EXACT_TEMPO"):
        for t in NEAR_TEMPOS:
            t = round(t, 2)
            if t == tempo or not (.92 <= tempo / t <= 1.09): continue
            for tx in dict.fromkeys([text, raw_text]): cand.append((_tc_key(tx, t, 0), tempo / t))
    for k, ratio in cand:   # 1) 로컬
        mp3 = os.path.join(TC_CACHE, k + ".mp3")
        if os.path.exists(mp3) and os.path.getsize(mp3) > 500: return mp3, ratio
    have = tts_store.has([f"ko/{k}.mp3" for k, _ in cand])   # 2) 보관함 (한 번)
    for k, ratio in cand:
        if f"ko/{k}.mp3" in have:
            mp3 = os.path.join(TC_CACHE, k + ".mp3")
            if tts_store.fetch(f"ko/{k}.mp3", mp3): return mp3, ratio
    return None, None


def _typecast(text, speed, fresh=False, take=0):
    """타입캐스트로 읽어 44.1kHz mono float 배열을 돌려준다. 같은 문장(같은 테이크)은 다시 사지 않는다 (크레딧 절약)"""
    import json, urllib.request, urllib.error
    import tts_log, tts_store
    tempo = round(min(1.3, max(.85, speed / TC_BASE_SPEED * VOICE_TEMPO)), 2)
    raw_text = text; text = _norm(text)
    os.makedirs(TC_CACHE, exist_ok=True)
    key = _tc_key(text, tempo, take)
    mp3 = os.path.join(TC_CACHE, key + ".mp3")
    if fresh and not take and os.path.exists(mp3): os.remove(mp3)   # 직접 '새로 받기'를 요청한 경우만 (렌더 재시도는 take 를 쓴다)
    if not fresh:
        hit, ratio = _find(text, raw_text, tempo, take)
        if hit:
            tts_log.add(cached=len(text))
            if ratio != 1.0: print(f"  [속도만 다른 녹음 재사용] x{ratio:.3f} · {text[:24]}", flush=True)
            return _decode(hit, ratio)
    # 요청 형식이 거절되면 단순한 형식으로 한 번 더 (키 점검 때 통과한 형식이 마지막)
    bodies = [
        {"text": text, "model": TC_MODEL, "voice_id": TC_VOICE, "language": "kor",
         "prompt": {"emotion_preset": "normal", "emotion_intensity": 1},
         "output": {"audio_format": "mp3", "audio_tempo": tempo}},
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
    _log_usage(len(text)); tts_log.add(chars=len(text))
    tts_store.put(f"ko/{key}.mp3", mp3)   # 영구 보관함에도 (다음 렌더·다른 작업이 다시 사지 않게)
    return _decode(mp3)


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


def speak(text, speed=1.15, steps=8, chunk=True, fresh=False, take=None):
    """text(한글 발음) → 44.1kHz mono float 배열.
    타입캐스트: 문장 단위로 한 번에 읽는다. 로컬 예비: 절 단위로 나눠 읽고 짧은 쉼을 넣어 잇는다
    take: 품질 검사 다시 받기 번호(0=처음). 테이크마다 따로 보관해 다음 렌더에서 다시 사지 않는다.
    fresh: take 없이 True 면 그 녹음을 버리고 새로 산다(사람이 직접 '새로 받기'를 고를 때만)"""
    if os.environ.get("TYPECAST_API_KEY"):
        # 목소리가 섞이면 안 되므로 로컬 음성으로 몰래 바꾸지 않는다: 두 번 실패하면 이 릴스는 실패 처리
        import time
        for i in range(3):
            try:
                return _typecast(text, speed, fresh=bool(fresh and take is None), take=int(take or 0))
            except Exception as e:
                err = e; print(f"타입캐스트 호출 실패({i + 1}/3):", str(e)[:200]); time.sleep(3 * (i + 1))
        raise RuntimeError(f"타입캐스트 음성 생성 실패: {err}")
    if not chunk: return _gen(text, speed, steps)
    segs = []
    for c in clauses(text):
        segs.append(_gen(c, speed, steps))
        segs.append(np.zeros(int((.12 if c.endswith(",") else .2) * SR), dtype=np.float32))
    return np.concatenate(segs[:-1]) if segs else np.zeros(1, dtype=np.float32)
