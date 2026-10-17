"""한국어 음성 합성 (Supertonic 3, sherpa-onnx). 인터넷 API 없이 로컬에서 돈다.
모델은 처음 실행할 때 GitHub 릴리스에서 받아 .cache 에 둔다 (약 130MB).
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


def speak(text, speed=1.15):
    """text(한글 발음) → 44.1kHz mono float 배열 (앞뒤 무음 정리)"""
    import sherpa_onnx as so
    g = so.GenerationConfig(); g.sid = VOICE_ID; g.num_steps = 8; g.speed = speed; g.extra["lang"] = "ko"
    a = _engine().generate(text, g)
    x = np.asarray(a.samples, dtype=np.float32)
    if a.sample_rate != SR:
        from scipy.signal import resample_poly
        x = resample_poly(x, SR, a.sample_rate).astype(np.float32)
    idx = np.where(np.abs(x) > 0.012)[0]
    if len(idx): x = x[max(0, idx[0] - int(.06 * SR)): idx[-1] + int(.12 * SR)]
    return x
