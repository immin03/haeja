"""시네마틱 훅 전용 음악 — 진짜 피아노 샘플로 (2026-11-03 대표님 3차)

1차 "음악이 안 들린다" → 중·고음 위주로 / 2차 "전자피아노 음이 듣기 별로, 소리가 너무 크다" → 뜯는 소리 /
3차 "여전히 전자음이 심하다, 편안한 피아노로, 더 낮게, 로고가 어색하다" → 합성음은 모두 빼고
  · 녹음된 그랜드 피아노 샘플(FluidR3_GM, assets/piano/*.mp3)만 쓴다. 고음을 살짝 깎아 부드럽게(펠트 피아노 느낌).
  · 8분음표 분산화음이 박자를 이끈다 (한 박의 첫 음을 조금 세게). 컷이 바뀌는 박엔 낮은 옥타브 베이스를 더해 박자를 짚는다.
  · 화음은 Am → F → C → G 로 돌다가, 로고 직전 마디가 늘 G(딸림화음)가 되게 맞춰 두고
    로고가 뜨는 순간 C장조 화음이 아래에서 위로 천천히 펼쳐지며 풀린다 (갑자기 끊기거나 쾅 하지 않게).
  · 타격음·박수·셰이커·잡음 상승음·사인파 패드 없음.

make_bed(n, sr, beat, strong, h0, h1) → float32 모노 (길이 n). 크기는 렌더러가 목소리에 맞춰 정한다.
"""
import os
import subprocess

import numpy as np
from scipy import signal as sg

HERE = os.path.dirname(os.path.abspath(__file__))
PIANO = os.path.join(HERE, "assets", "piano")
# 마디마다 (베이스, 분산화음 4음)
CHORDS = [("A2", ("A3", "C4", "E4", "C4")),   # Am
          ("F2", ("F3", "A3", "C4", "A3")),   # F
          ("C3", ("G3", "C4", "E4", "C4")),   # C
          ("G2", ("G3", "B3", "D4", "B3"))]   # G
TOPS = ["E5", "C5", "G4", "D5"]   # 마디 첫 박 위에 아주 작게 얹는 윗음 (선율처럼 들리게)
_CACHE = {}


def note(name, sr):
    k = (name, sr)
    if k not in _CACHE:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(PIANO, name + ".mp3"), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.float32).copy()
        i0 = int(np.argmax(np.abs(x) > .02 * np.abs(x).max())); x = x[i0:]   # 앞 무음 제거
        b, a = sg.butter(2, 2600 / (sr / 2)); x = sg.lfilter(b, a, x)   # 고음을 살짝 깎아 부드럽게
        _CACHE[k] = (x / (np.abs(x).max() + 1e-9)).astype(np.float32)
    return _CACHE[k]


def make_bed(n, sr, beat, strong, h0, h1, seed=7):
    rng = np.random.default_rng(seed)
    out = np.zeros(n, np.float32)

    def add(at, x, lv, cut=None):
        i = int(round(at * sr))
        if i >= n or lv <= 0: return
        if i < 0: x = x[-i:]; i = 0
        x = x[: n - i] * lv
        if cut:   # 다음 화음으로 넘어갈 때 앞 음은 부드럽게 줄인다 (페달을 떼듯)
            m = int(cut * sr)
            if m < len(x): x = x.copy(); r = min(len(x) - m, int(.25 * sr)); x[m:m + r] *= np.linspace(1, 0, r); x[m + r:] = 0
        out[i:i + len(x)] += x.astype(np.float32)

    hb = int(round(h0 / beat)); e8 = beat / 2
    for k in range(hb * 2):   # 1) 8분음표 분산화음
        b = k // 2; ch = CHORDS[((b - hb) // 4) % 4]
        grow = .75 + .25 * min(1, b / max(1, hb - 2))
        vel = (1.0 if k % 2 == 0 else .72) * (1 + .06 * rng.standard_normal())
        add(k * e8, note(ch[1][k % 4], sr), .30 * grow * vel, cut=4 * beat - (b % 4) * beat + .1)
    for b in range(0, hb, 4):   # 2) 마디 첫 박: 베이스 + 윗음
        ch = CHORDS[((b - hb) // 4) % 4]; tp = TOPS[((b - hb) // 4) % 4]
        add(b * beat, note(ch[0], sr), .34, cut=4 * beat + .1); add(b * beat, note(tp, sr), .13, cut=4 * beat + .1)
    for b in range(hb):   # 3) 컷이 바뀌는 박: 낮은 옥타브를 살짝 더해 박자를 짚는다
        if b in strong and b % 4:
            ch = CHORDS[((b - hb) // 4) % 4]; add(b * beat, note(ch[0], sr), .24, cut=(4 - b % 4) * beat + .1)
    # 4) 로고: C장조 화음이 아래에서 위로 천천히 펼쳐진다 (0.07초 간격), 맨 위 C6 은 아주 작게
    roll = [("C3", .40), ("G3", .30), ("C4", .30), ("E4", .27), ("G4", .24), ("C5", .20), ("E5", .14), ("C6", .07)]
    for j, (nm, lv) in enumerate(roll): add(h0 + .03 + .07 * j, note(nm, sr), lv * 1.6)   # 로고 화음은 반주보다 약 4dB 크게 (말이 없는 구간)
    # 시작은 0.3초에 걸쳐 들어오고, 인트로가 끝나면 1.2초에 걸쳐 빠진다
    tt = np.arange(n) / sr
    out *= np.clip(tt / .3, 0, 1) * np.clip((h1 + 1.2 - tt) / 1.2, 0, 1)
    return out.astype(np.float32)
