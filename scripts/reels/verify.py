"""성우 음성 검수: 합성한 음성을 한국어 음성 인식(sherpa-onnx zipformer)으로 다시 받아 적어
대본과 글자 단위로 맞춰 본다. 음절이 빠지거나 뭉개진 줄은 설정을 바꿔 다시 합성하고,
끝까지 기준에 못 미치면 렌더를 멈춘다(엉터리 음성이 게시되지 않도록).
모델은 처음 실행할 때 GitHub 릴리스에서 받아 .cache 에 둔다 (약 330MB).
"""
import os, re, difflib, tarfile, urllib.request
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("TTS_CACHE", os.path.join(HERE, ".cache"))
NAME = "sherpa-onnx-zipformer-korean-2024-06-24"
URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{NAME}.tar.bz2"
PASS = 0.90      # 이 이상이면 통과
FLOOR = 0.85     # 모든 재시도 뒤에도 이보다 낮으면 렌더 중단
_rec = None


def _recognizer():
    global _rec
    if _rec is None:
        import sherpa_onnx as so
        d = os.path.join(CACHE, NAME)
        if not os.path.exists(os.path.join(d, "tokens.txt")):
            os.makedirs(CACHE, exist_ok=True)
            tgz = os.path.join(CACHE, NAME + ".tar.bz2")
            print("음성 인식 모델 내려받는 중…")
            urllib.request.urlretrieve(URL, tgz)
            with tarfile.open(tgz) as t: t.extractall(CACHE)
            os.remove(tgz)
        f = lambda k: os.path.join(d, f"{k}-epoch-99-avg-1.int8.onnx")
        _rec = so.OfflineRecognizer.from_transducer(encoder=f("encoder"), decoder=f("decoder"), joiner=f("joiner"),
                                                    tokens=os.path.join(d, "tokens.txt"), num_threads=4)
    return _rec


def hear(x, sr):
    from scipy.signal import resample_poly
    y = resample_poly(x, 16000, sr).astype(np.float32)
    y = np.concatenate([np.zeros(3200, np.float32), y, np.zeros(4800, np.float32)])
    s = _recognizer().create_stream(); s.accept_waveform(16000, y); _recognizer().decode_stream(s)
    return s.result.text


def _norm(t):
    from korean import to_speech
    t = re.sub(r"[^가-힣]", "", to_speech(t))
    for x in ("배류", "밸류"): t = t.replace(x, "밸유")  # 브랜드명은 받아 적는 방식만 다르다
    return t


def score(expected, heard):
    a, b = _norm(expected), _norm(heard)
    return difflib.SequenceMatcher(None, a, b).ratio() if a else 1.0


# 재시도 순서: (속도 배율, 확산 단계, 절 단위로 나누기)
TRIES = [(1.0, 8, True), (1.0, 16, True), (.94, 16, True), (.9, 32, True), (1.0, 16, False), (.88, 32, False)]


def speak_checked(text, speed, speak, sr, log):
    best = None
    for k, (m, steps, chunk) in enumerate(TRIES):
        a = speak(text, speed * m, steps=steps, chunk=chunk)
        h = hear(a, sr); r = score(text, h)
        if best is None or r > best[0]: best = (r, a, h)
        if r >= PASS: break
    r, a, h = best
    log.append({"text": text, "heard": h, "score": round(r, 3), "tries": k + 1})
    return a
