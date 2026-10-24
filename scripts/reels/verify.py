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
PASS = 0.93      # 이 이상이면 통과 (2026-10-24 0.90에서 올림)
FLOOR = 0.90     # 모든 재시도 뒤에도 이보다 낮으면 불합격 (2026-10-24 0.85에서 올림)
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


# 소리는 같고 받아 적는 글자만 다른 말
HOMO = [("벨류", "밸유"), ("델류", "밸유"), ("같이", "가치"), ("메수", "매수"), ("주간은", "주가는"), ("주까", "주가")]  # "주가는"을 인식기가 늘 "주간은"으로 적는다(모든 기업 릴스 비교 문장에서 확인)
# 음성 인식기가 잘 모르는 외국 인명: 이 말이 든 줄은 기준을 조금 낮춘다(소리가 맞아도 엉뚱하게 받아 적는다)
NAMES = re.compile("버핏|그레이엄|멍거|버크셔|해서웨이|워런")

LETTERS = {"A": "에이", "B": "비", "C": "씨", "D": "디", "E": "이"}


def _assim(t):
    """표준 발음대로 맞춘다: 받침 ㅂ 뒤에 ㄴ이 오면 ㅁ으로 소리 난다(바꿉니다 → [바꿈니다]). 인식기는 소리대로 적는다"""
    out = list(t)
    for i in range(len(out) - 1):
        c, n = ord(out[i]) - 0xAC00, ord(out[i + 1]) - 0xAC00
        if 0 <= c < 11172 and 0 <= n < 11172 and c % 28 == 17 and n // 588 == 2:
            out[i] = chr(0xAC00 + c - 1)
    return "".join(out)


def _norm(t):
    from korean import to_speech
    t = re.sub(r"\b([A-Ea-e])\b", lambda m: LETTERS[m[1].upper()], t)  # 인식기가 '에이'를 'A'로 적는 경우
    t = re.sub(r"[^가-힣]", "", to_speech(t))
    for x in ("배류", "밸류"): t = t.replace(x, "밸유")  # 브랜드명은 받아 적는 방식만 다르다
    for a, b in HOMO: t = t.replace(a, b)
    return _assim(t)


def score(expected, heard):
    a, b = _norm(expected), _norm(heard)
    return difflib.SequenceMatcher(None, a, b).ratio() if a else 1.0


# 재시도 순서: (속도 배율, 확산 단계, 절 단위로 나누기)
TRIES = [(1.0, 8, True), (1.0, 16, True), (.94, 16, True), (.9, 32, True), (1.0, 16, False), (.88, 32, False)]
# 타입캐스트 재시도: 속도는 그대로 두고 캐시를 버리고 새로 받는다(같은 문장도 받을 때마다 소리가 조금씩 다르다)
TC_TRIES = [(1.0, False), (1.0, True), (1.0, True), (1.0, True), (.97, True)]


def problems(orig, expected, heard):
    """전체 일치율과 별개로 '듣는 사람이 바로 이상하다고 느끼는' 오류를 찾는다 (2026-10-24 원유 ETF 릴스 사고 뒤 추가).
    그 릴스는 '원유 ETF는 22%'가 '원유프는 202%'로, '갈아탑니다'가 '갈아입합니다'로 들렸는데 일치율 0.9로 통과했다.
    1) 숫자: 대본의 숫자가 들린 말에 그대로 있어야 한다(숫자로 적히든 한글로 적히든)
    2) 빠지거나 뭉개진 덩어리: 대본 쪽 3음절 이상이 통째로 빠지거나 다른 말로 바뀌면 오류"""
    from korean import to_speech
    out = []
    h_norm = _norm(heard); h_digits = set(re.findall(r"\d+", (heard or "").replace(",", "")))
    for n in re.findall(r"\d[\d,]*(?:\.\d+)?", orig or ""):
        d = n.replace(",", "")
        if d in h_digits: continue
        if re.sub(r"[^가-힣]", "", to_speech(n)) in h_norm: continue
        out.append(f"숫자 {n}")
    a, b = _norm(expected), h_norm
    ops = [o for o in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if o[0] != "equal"]
    for tag, i1, i2, j1, j2 in ops:
        if tag in ("delete", "replace") and i2 - i1 >= 3:
            out.append(f"'{a[i1:i2]}' → '{b[j1:j2]}'")
    # 3) 한 문장 안에서 세 군데 이상 다르게 들리면 뭉개진 것으로 본다 ('원유 이티에프'→'원이틀에프', '갈아탑니다'→'갈아입합니다')
    if len(ops) >= 3 and not out:
        out.append("여러 곳 다르게 들림: " + ", ".join(f"'{a[i1:i2]}'→'{b[j1:j2]}'" for _, i1, i2, j1, j2 in ops))
    return out


def speak_checked(text, speed, speak, sr, log, orig=None):
    best = None
    pass_, floor = (PASS - .05, FLOOR - .1) if NAMES.search(text) else (PASS, FLOOR)
    # 2026-10-24: 타입캐스트라고 기준을 낮추던 예외를 없앴다. 실제로 이상한 소리가 게시됐다.
    tc = bool(os.environ.get("TYPECAST_API_KEY"))
    tries = [(m, 16, True, f) for m, f in TC_TRIES] if tc else [(m, s, c, False) for m, s, c in TRIES]
    for k, (m, steps, chunk, fresh) in enumerate(tries):
        a = speak(text, speed * m, steps=steps, chunk=chunk, fresh=fresh) if tc else speak(text, speed * m, steps=steps, chunk=chunk)
        h = hear(a, sr); r = score(text, h); bad = problems(orig or text, text, h)
        key = (not bad, r)
        if best is None or key > best[0]: best = (key, a, h, bad, r)
        if r >= pass_ and not bad: break
    _, a, h, bad, r = best
    if bad: floor = max(floor, 1.01)   # 숫자 오류·덩어리 오류가 남으면 일치율과 상관없이 불합격 → 사람이 듣고 승인
    log.append({"text": text, "heard": h, "score": round(r, 3), "tries": k + 1, "pass": pass_, "floor": floor, "problems": bad})
    return a
