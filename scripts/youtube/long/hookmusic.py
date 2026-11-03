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
BASS = os.path.join(HERE, "assets", "bass")
TAIKO = os.path.join(HERE, "assets", "taiko_drum"); TIMP = os.path.join(HERE, "assets", "timpani"); PIZZ = os.path.join(HERE, "assets", "pizzicato_strings")
# 2026-11-04 대표님: "피아노여서 그 느낌이 덜하네… 베이스 쿵쿵이나… 박자에 맞춰" → style="drive": 타이코 북(박마다 쿵)·팀파니·현 피치카토 8분음표를 더한다
PZ = [("A2", "C3", "E3", "A3"), ("F2", "A2", "C3", "F3"), ("C3", "E3", "G3", "C4"), ("G2", "B2", "D3", "G3")]   # 핑거 베이스 샘플 (FluidR3_GM electric_bass_finger)
# 마디마다 베이스 라인: (박, 음) — 1박 뿌리음, 2박 뒤 8분 뿌리음, 3박 한 옥타브(또는 5도) 위, 4박 뿌리음
BASSLINE = [("A1", "A2"), ("F1", "F2"), ("C2", "G2"), ("G1", "G2")]
# 마디마다 (베이스, 분산화음 4음)
CHORDS = [("A2", ("A3", "C4", "E4", "C4")),   # Am
          ("F2", ("F3", "A3", "C4", "A3")),   # F
          ("C3", ("G3", "C4", "E4", "C4")),   # C
          ("G2", ("G3", "B3", "D4", "B3"))]   # G
TOPS = ["E5", "C5", "G4", "D5"]   # 마디 첫 박 위에 아주 작게 얹는 윗음 (선율처럼 들리게)
_CACHE = {}


def note(name, sr, d=None):
    d = d or PIANO; k = (name, sr, d)
    if k not in _CACHE:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(d, name + ".mp3"), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.float32).copy()
        i0 = int(np.argmax(np.abs(x) > .02 * np.abs(x).max())); x = x[i0:]   # 앞 무음 제거
        b, a = sg.butter(2, {PIANO: 2600, PIZZ: 3200, TAIKO: 5000, TIMP: 4000}.get(d, 1800) / (sr / 2)); x = sg.lfilter(b, a, x)   # 고음을 살짝 깎아 부드럽게
        _CACHE[k] = (x / (np.abs(x).max() + 1e-9)).astype(np.float32)
    return _CACHE[k]


def make_bed(n, sr, beat, strong, h0, h1, seed=7, style="drive"):
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
        add(k * e8, note(ch[1][k % 4], sr), (.16 if style == "drive" else .30) * grow * vel, cut=4 * beat - (b % 4) * beat + .1)
        if style == "drive":   # 현 피치카토 8분음표 — 예고편처럼 쉬지 않고 달리는 리듬
            pz = PZ[((b - hb) // 4) % 4]; add(k * e8, note(pz[(k * 3) % 4 if k % 2 else (k // 2) % 2], sr, PIZZ), .30 * grow * vel, cut=e8 * 1.6)
    for b in range(0, hb, 4):   # 2) 마디 첫 박: 베이스 + 윗음
        ch = CHORDS[((b - hb) // 4) % 4]; tp = TOPS[((b - hb) // 4) % 4]
        add(b * beat, note(ch[0], sr), .34, cut=4 * beat + .1); add(b * beat, note(tp, sr), .13, cut=4 * beat + .1)
    for b in range(hb):   # 3) 컷이 바뀌는 박: 낮은 옥타브를 살짝 더해 박자를 짚는다
        if b in strong and b % 4:
            ch = CHORDS[((b - hb) // 4) % 4]; add(b * beat, note(ch[0], sr), .24, cut=(4 - b % 4) * beat + .1)
    # 4) 베이스 (2026-11-03 대표님: "피아노뿐 아니라 베이스도") — 휴대폰 스피커에서도 들리게 배음이 있는 핑거 베이스, 박자를 받쳐 준다
    for b in range(0, hb, 4):
        lo, hi = BASSLINE[((b - hb) // 4) % 4]; g = .75 + .25 * min(1, b / max(1, hb - 4))
        for off, nm, lv, ln in ((0, lo, .55, 1.4), (1.5, lo, .38, .45), (2, hi, .42, .9), (3, lo, .45, .9)):
            add((b + off) * beat, note(nm, sr, BASS), lv * g, cut=ln * beat)
    if style == "drive":   # 6) 타이코 북: 박마다 쿵, 마디 첫 박·컷이 바뀌는 박은 크게(+팀파니), 로고 직전 2박은 팀파니 16분음표 롤
        for b in range(hb - 2):
            big = b % 4 == 0 or b in strong; g = .7 + .3 * min(1, b / max(1, hb - 4))
            add(b * beat, note("C2" if big else "G2", sr, TAIKO), (.62 if big else .30) * g)
            if big: add(b * beat, note(BASSLINE[((b - hb) // 4) % 4][0].replace("1", "2"), sr, TIMP), .30 * g, cut=beat * 1.5)
        for j in range(8):
            add((hb - 2) * beat + j * beat / 4, note("A1", sr, TIMP), .12 + .05 * j, cut=beat / 4 + .05)
        add(h0, note("C2", sr, TAIKO), .75); add(h0, note("C2", sr, TIMP), .5, cut=2.4)
    # 5) 로고: C장조 화음이 아래에서 위로 천천히 펼쳐진다 (0.07초 간격), 맨 위 C6 은 아주 작게
    roll = [("C3", .40), ("G3", .30), ("C4", .30), ("E4", .27), ("G4", .24), ("C5", .20), ("E5", .14), ("C6", .07)]
    add(h0 + .03, note("C2", sr, BASS), .55, cut=2.2)   # 로고 화음 밑을 베이스가 길게 받친다
    for j, (nm, lv) in enumerate(roll): add(h0 + .03 + .07 * j, note(nm, sr), lv * 1.6)   # 로고 화음은 반주보다 약 4dB 크게 (말이 없는 구간)
    # 시작은 0.3초에 걸쳐 들어오고, 인트로가 끝나면 1.2초에 걸쳐 빠진다
    tt = np.arange(n) / sr
    out *= np.clip(tt / .3, 0, 1) * np.clip((h1 + 1.2 - tt) / 1.2, 0, 1)
    return out.astype(np.float32)
