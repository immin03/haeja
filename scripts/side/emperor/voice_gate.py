"""황제의 일기 쇼츠 최종 음성 관문 (2026-11-08 대표: "검수를 꼭 해야 돼. 다시는 반복하지 마")
사고: ep17 '오늘의 할 일'에서 '떠올리기'가 1.8초 늘어진 녹음이 그대로 게시됐다. 기존 검사는 ① 끌림 기준이 느슨했고
② 올리는 파일이 아니라 중간 파일(base.mp4)만 봤고 ③ 통과 여부와 업로드가 연결돼 있지 않았다.

사용: python3 voice_gate.py <spec_<id>a.json> <유튜브.mp4> <인스타틱톡.mp4>
검사 — 하나라도 어기면 불통과, 도장을 찍지 않는다.
 A. 목소리 조각마다(원본 음성): 소리 끌기 · 말 속도 · 받아쓰기와 대본 일치(0.80 이상)
 B. 실제로 올릴 파일마다: 조각이 제자리(±0.7초)에 온전히 들어 있고 원본과 일치(상관 0.90 이상), 순서 맞음
    · 조용한 곳의 클릭 없음 · 크기 -17~-13 LUFS · 전체 받아쓰기와 대본 일치(0.72 이상)
통과하면 <mp4>.voiceqa.json 도장(파일 sha256)을 남긴다. yt_up.sh 는 도장 없이는 올리지 않고,
ed_posts 는 voice_qa='pass:<sha256>' 없이는 새 데일리 쇼츠 행을 받지 않는다(DB 트리거)."""
import difflib, hashlib, json, os, re, subprocess, sys, time, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from take_check import drag_why, held_runs, HOLD_MAX, norm
SR = 16000; SIM_PIECE, SIM_FULL, CORR_MIN = 0.80, 0.72, 0.90
MODEL = "sherpa-onnx-zipformer-korean-2024-06-24"
CACHE = os.environ.get("ED_STT_DIR", os.path.expanduser("~/.cache/ed_stt"))
OUTRO_TXT = "매일 밤, 황제처럼 생각하라. 황제의 일기."


def recognizer():
    try: import sherpa_onnx
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "-q", "sherpa-onnx"], check=True); import sherpa_onnx
    d = os.path.join(CACHE, MODEL)
    if not os.path.exists(d + "/tokens.txt"):
        os.makedirs(CACHE, exist_ok=True); t = d + ".tar.bz2"
        subprocess.run(["curl", "-sSL", "--retry", "3", "--max-time", "500", "-o", t, f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{MODEL}.tar.bz2"], check=True)
        subprocess.run(["tar", "xjf", t, "-C", CACHE], check=True); os.remove(t)
    return sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{d}/encoder-epoch-99-avg-1.int8.onnx", decoder=f"{d}/decoder-epoch-99-avg-1.int8.onnx",
        joiner=f"{d}/joiner-epoch-99-avg-1.int8.onnx", tokens=f"{d}/tokens.txt", num_threads=4, sample_rate=SR, feature_dim=80)


def load(f):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32).copy()


CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"; JUN = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"; JON = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
def jamo(t):
    o = []
    for c in re.sub(r"[^가-힣]", "", t):
        k = ord(c) - 0xAC00; o += [CHO[k // 588], JUN[k % 588 // 28]]
        if k % 28: o.append(JON[k % 28])
    return o
def sim(a, b): return difflib.SequenceMatcher(None, jamo(a), jamo(b), autojunk=False).ratio()


def locate(y, p):
    try: from scipy.signal import fftconvolve
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "-q", "scipy"], check=True); from scipy.signal import fftconvolve
    idx = np.where(np.abs(p) > 0.01)[0]; q = p[idx[0]:idx[-1]]
    c = fftconvolve(y, q[::-1], "valid"); k = int(np.argmax(np.abs(c)))
    seg = y[k:k + len(q)]; m = np.abs(q) > 0.02
    r = float(np.corrcoef(seg[m], q[m])[0, 1]) if len(seg) == len(q) else 0.0
    return (k - idx[0]) / SR, r, len(q) / SR


def main(spec_path, *mp4s):
    S = json.load(open(spec_path)); L = json.load(open(f"{HERE}/long_{S['id']}.json")); fail = []; asr = recognizer()
    def stt(x):
        s = asr.create_stream(); s.accept_waveform(SR, x); asr.decode_stream(s); return s.result.text
    groups = sorted({s[2] for s in L["sents"]})
    texts = [" ".join(" ".join(s[5]) for s in L["sents"] if s[2] == g) for g in groups]
    texts += ["오늘의 할 일. " + " ".join(L["tonight"])] if L.get("end_voice") else []
    texts += [OUTRO_TXT]
    if len(texts) != len(S["voice"]): sys.exit(f"불통과: 조각 {len(S['voice'])}개와 대본 {len(texts)}개 수가 다름")
    print("[A] 목소리 조각"); P = []
    for v, t in zip(S["voice"], texts):
        p = load(v["file"]); P.append(p); s = sim(t, stt(p)); name = os.path.basename(v["file"])
        why = drag_why(v["file"], t) + [f"소리 끌림 {a}~{b}초" for a, b in held_runs(v["file"]) if b - a > HOLD_MAX]
        if s < SIM_PIECE: why.append(f"받아쓰기 불일치 {s:.2f}")
        print(f"  {name} 일치 {s:.2f} {'ok' if not why else why}")
        fail += [f"{name}: {w}" for w in why]
    script = " ".join(texts); stamps = []
    for f in mp4s:
        print("[B]", os.path.basename(f)); y = load(f); bad = []; last = -1
        delay = float(S.get("voice_delay_tail", 0.35))
        for i, (v, p) in enumerate(zip(S["voice"], P)):
            at, r, n = locate(y, p); exp = v["at"] + (delay if i == len(P) - 1 else 0)
            st = "ok"
            if abs(at - exp) > 0.7: st = f"자리 어긋남 {at:.2f}/{exp:.2f}"
            elif r < CORR_MIN: st = f"일그러짐 상관 {r:.3f}"
            elif at < last - 0.05: st = f"앞 조각과 겹침 {at:.2f}<{last:.2f}"
            last = at + n
            print(f"  {os.path.basename(v['file'])} @{at:.2f} 상관 {r:.3f} {st}")
            if st != "ok": bad.append(f"{os.path.basename(v['file'])}: {st}")
        d = np.abs(np.diff(y)); w = int(.005 * SR); e = np.sqrt(np.convolve(y ** 2, np.ones(w) / w, "same"))
        clicks = np.where((d > .25) & (e[1:] < .05))[0]
        if len(clicks): bad.append(f"클릭 {len(clicks)}곳 {[round(c / SR, 2) for c in clicks[:6]]}")
        st = subprocess.run(["ffmpeg", "-hide_banner", "-i", f, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
        I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", st)[-1])
        if not -17 <= I <= -13: bad.append(f"크기 {I} LUFS")
        fs = sim(script, stt(y)); print(f"  크기 {I} LUFS · 전체 받아쓰기 일치 {fs:.2f}")
        if fs < SIM_FULL: bad.append(f"전체 받아쓰기 불일치 {fs:.2f}")
        fail += [f"{os.path.basename(f)}: {b}" for b in bad]; stamps.append(f)
    if fail:
        print("불통과"); [print(" -", x) for x in fail]
        for f in mp4s:
            if os.path.exists(f + ".voiceqa.json"): os.remove(f + ".voiceqa.json")
        sys.exit(1)
    for f in stamps:
        h = hashlib.sha256(open(f, "rb").read()).hexdigest()
        json.dump({"passed": True, "sha256": h, "id": S["id"], "at": time.strftime("%F %T"), "ed_posts_voice_qa": "pass:" + h}, open(f + ".voiceqa.json", "w"))
        print("도장", os.path.basename(f), "pass:" + h)
    print("통과")


if __name__ == "__main__": main(*sys.argv[1:])
