"""성우 녹음 테이크 검사 (2026-11-04 대표: "앞으로 문제 재발하지 않도록")
8편 사고 두 가지를 막는다.
 1) 녹음 자체 결함: 타입캐스트가 한 소리를 비정상적으로 길게 끌어 '갈라지는' 테이크 ('떠올리고'가 0.7초 늘어짐)
    → 0.62초 넘게 스펙트럼이 거의 안 변하는 유성음 구간이 있으면 불통과 (정상 테이크는 최대 0.55초 안팎)
 2) 엉뚱한 문장: 다른 편의 '오늘의 할 일' 녹음을 잘못 가져다 씀
    → 녹음 옆의 <파일>.txt (voices.py 가 녹음 때 남기는 원문) 가 대본 문장과 같아야 통과. txt 가 없으면 불통과
사용: python3 take_check.py <mp3> ["기대 문장"]   (문장을 주면 원문 대조까지)
다른 스크립트: from take_check import check  → (ok, 이유 목록)"""
import os, re, subprocess, sys, numpy as np
SR = 24000
HOLD_MAX = 0.62


def _load(f):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                        capture_output=True, check=True).stdout, np.float32)


def held_runs(f, th=0.9, min_len=0.5):
    x = _load(f); n, h = 1024, 240
    fr = np.array([np.abs(np.fft.rfft(x[i:i + n] * np.hanning(n)))[:340] for i in range(0, len(x) - n, h)])
    if not len(fr): return []
    e = 20 * np.log10(fr.sum(1) + 1e-9); loud = e > e.max() - 30
    lf = np.log(fr + 1e-6)
    with np.errstate(all="ignore"):
        d = np.nan_to_num(np.r_[1, [np.corrcoef(lf[i], lf[i - 1])[0, 1] for i in range(1, len(lf))]])
    st = (d > th) & loud; runs, s = [], None
    for i, v in enumerate(list(st) + [False]):
        if v and s is None: s = i
        if not v and s is not None:
            if (i - s) * h / SR > min_len: runs.append((round(s * h / SR, 2), round(i * h / SR, 2)))
            s = None
    return runs


def norm(t):
    return re.sub(r"[\s'\"‘’“”.,?!·…\-—]", "", t or "")


def check(f, expect=None):
    why = []
    for a, b in held_runs(f):
        if b - a > HOLD_MAX: why.append(f"소리 끌림 {a}~{b}초 ({b - a:.2f}초)")
    if expect is not None:
        side = f + ".txt"
        if not os.path.exists(side): why.append("원문 기록(.txt) 없음 — 이 편 대본으로 새로 녹음한 테이크만 쓴다")
        elif norm(open(side).read()) != norm(expect):
            why.append(f"원문 불일치: 녹음='{open(side).read().strip()}' / 대본='{expect}'")
    return (not why), why


if __name__ == "__main__":
    ok, why = check(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(os.path.basename(sys.argv[1]), "통과" if ok else "불통과", *why)
    sys.exit(0 if ok else 1)
