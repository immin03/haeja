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
    if style in ("house", "hybrid"): return make_house(n, sr, beat, strong, h0, h1, seed, taiko=(style == "hybrid"))
    if style == "basstaiko": return make_basstaiko(n, sr, beat, strong, h0, h1, seed)
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


# ── 2026-11-04 대표님: "일렉트로 하우스 같은 느낌도 있으면… 인트로 좀 더 강력하게" → 시안용 스타일 house / hybrid ──
def _kick(sr, drive=2.2):
    m = int(sr * .38); t = np.arange(m) / sr; f = 55 + 120 * np.exp(-t * 28)
    x = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t / .16)
    x += np.exp(-t / .004) * .6   # 앞머리 딸깍 (휴대폰에서도 박자가 들리게)
    return np.tanh(drive * x) / np.tanh(drive)


def _noise(sr, d, rng): return rng.standard_normal(int(sr * d))


def _clap(sr, rng):
    m = int(sr * .25); out = np.zeros(m)
    for o in (0, .011, .022):
        L = m - int(o * sr); z = _bp(rng.standard_normal(L), sr, 900, 3200) * _env(L, sr, .001, .06); out[int(o * sr):] += z
    return out / (np.abs(out).max() + 1e-9)


def _hat(sr, rng, d=.07):
    z = _hp(_noise(sr, d, rng), sr, 7000) * _env(int(sr * d), sr, .001, d / 3); return z / (np.abs(z).max() + 1e-9)


def _sawv(f, d, sr, voices=5, spread=.012):
    m = int(sr * d); t = np.arange(m) / sr; y = np.zeros(m)
    for k in range(voices):
        df = f * (1 + spread * (k - (voices - 1) / 2) / ((voices - 1) / 2 or 1)); y += 2 * ((t * df + .13 * k) % 1) - 1
    return y / voices


def _env_(n, sr, a, r):
    return _env(n, sr, a, r)


def _env(n, sr, a, r):
    t = np.arange(n) / sr
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))


def _bp(x, sr, lo, hi):
    b, a = sg.butter(2, [lo / (sr / 2), min(.99, hi / (sr / 2))], "band"); return sg.lfilter(b, a, x)


def _hp(x, sr, f):
    b, a = sg.butter(2, f / (sr / 2), "high"); return sg.lfilter(b, a, x)


def _lp(x, sr, f):
    b, a = sg.butter(2, min(.99, f / (sr / 2)), "low"); return sg.lfilter(b, a, x)


HZ = {"A1": 55.0, "F1": 43.65, "C2": 65.41, "G1": 49.0, "A2": 110.0, "F2": 87.31, "C3": 130.81, "G2": 98.0, "E3": 164.81, "A3": 220.0,
      "C4": 261.63, "E4": 329.63, "F3": 174.61, "G3": 196.0, "B3": 246.94, "D4": 293.66, "G4": 392.0}
STAB = [("A3", "C4", "E4"), ("F3", "A3", "C4"), ("G3", "C4", "E4"), ("G3", "B3", "D4")]


def make_house(n, sr, beat, strong, h0, h1, seed=7, taiko=False):
    """일렉트로 하우스: 4박 킥 · 2·4박 클랩 · 엇박 하이햇 · 엇박 베이스 · 사이드체인으로 출렁이는 신스 화음 · 마지막 2박 스네어 롤+상승음 · 로고에 큰 임팩트"""
    rng = np.random.default_rng(seed); out = np.zeros(n, np.float32); pad = np.zeros(n, np.float32)
    def add(buf, at, x, lv):
        i = int(round(at * sr))
        if 0 <= i < n: buf[i:i + len(x)] += (np.asarray(x)[: n - i] * lv).astype(np.float32)
    hb = int(round(h0 / beat)); e8 = beat / 2; K = _kick(sr); C = _clap(sr, rng)
    for b in range(hb - 2):
        g = .75 + .25 * min(1, b / max(1, hb - 4)); big = b in strong or b % 4 == 0
        add(out, b * beat, K, .9 * g)
        if taiko and big: add(out, b * beat, note("C2", sr, TAIKO), .55 * g)
        if b % 2 == 1: add(out, b * beat, C, .38 * g)
        add(out, b * beat + e8, _hat(sr, rng, .09), .16 * g)
        ch = STAB[((b - hb) // 4) % 4]; root = {"A3": "A1", "F3": "F1", "G3": "G1"}[ch[0]] if ch[0] in ("A3", "F3", "G3") else "C2"
        bs = _lp(_sawv(HZ[root] * 2, e8 * .9, sr, 3, .006), sr, 700) * _env(int(sr * e8 * .9), sr, .004, e8 * .5)
        add(pad, b * beat + e8, bs, .55 * g)   # 엇박 베이스
        st = sum(_sawv(HZ[nm], beat * .9, sr) for nm in ch); st = _lp(st, sr, 2600 + 1400 * g) * _env(len(st), sr, .006, beat * .45)
        add(pad, b * beat, st / 3, .34 * g)    # 화음 스탭
    # 사이드체인: 킥마다 신스·베이스가 눌렸다가 올라온다 (하우스 특유의 출렁임)
    tt = np.arange(n) / sr; ph = (tt % beat) / beat; sc = np.clip(ph / .45, 0, 1) ** .7
    out += pad * (.25 + .75 * sc)
    # 마지막 2박: 스네어 롤(점점 빨라짐) + 상승 잡음 + 올라가는 음
    t0 = (hb - 2) * beat; hits = [t0 + beat * x for x in (0, .5, 1, 1.25, 1.5, 1.625, 1.75, 1.875)]
    for j, at in enumerate(hits): add(out, at, C, .18 + .05 * j)
    m = int(2 * beat * sr); u = np.linspace(0, 1, m); z = rng.standard_normal(m)
    rs = _hp(z, sr, 1500) * u ** 2; add(out, t0, rs / (np.abs(rs).max() + 1e-9), .35)
    f = 220 * 2 ** (u * 2); sw = np.sin(2 * np.pi * np.cumsum(f) / sr) * u ** 2; add(out, t0, sw, .12)
    # 로고 임팩트: 큰 킥 + 낮게 떨어지는 서브 + 잡음 폭발 + 넓은 화음, 꼬리는 길게
    m = int(sr * 2.4); t = np.arange(m) / sr; fsub = 70 * np.exp(-t * 1.6) + 32
    sub = np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(fsub) / sr)) * np.exp(-t / .9)
    add(out, h0, _kick(sr, 3.0), 1.1); add(out, h0, sub, .7)
    z = rng.standard_normal(int(sr * 1.2)); bl = _bp(z, sr, 300, 5000) * _env(len(z), sr, .002, .25); add(out, h0, bl / (np.abs(bl).max() + 1e-9), .45)
    ch = sum(_sawv(HZ[nm], 2.4, sr, 7, .015) for nm in ("C3", "G3", "C4", "E4", "G4")); ch = _lp(ch, sr, 3200) * _env(len(ch), sr, .01, 1.0)
    add(out, h0, ch / (np.abs(ch).max() + 1e-9), .38)
    if taiko: add(out, h0, note("C2", sr, TAIKO), .8); add(out, h0, note("C2", sr, TIMP), .55)
    out *= np.clip(tt / .05, 0, 1) * np.clip((h1 + 1.2 - tt) / 1.2, 0, 1)
    return out.astype(np.float32)


# ── 2026-11-04 16:09 대표님: 베이스하우스 변형 시안 중 "B2(타이코 섞음)로 전체 다 렌더링" → style="basstaiko" ──
# 4박 킥 · 2·4박 클랩 · 엇박 하이햇 · 엇박 워블 리스 베이스 + 박마다 808 서브 · 마디 첫 박 타이코, 두 마디마다 팀파니 · 마지막 2박 롤+상승음 · 로고 임팩트
# 16:02 대표님 "음악 소리가 거의 안 들려": 휴대폰 스피커는 200Hz 아래를 못 낸다 → 저음을 포화시켜 들리는 배음을 더하고 초저음은 7dB 줄인다.
ROOTS_BT = ["A1", "F1", "C2", "G1"]


def _sub808(f, d, sr, drive=1.6):
    m = int(sr * d); t = np.arange(m) / sr; ff = f * (1 + 1.5 * np.exp(-t * 40))
    return np.tanh(drive * np.sin(2 * np.pi * np.cumsum(ff) / sr)) * np.exp(-t / (d * .55))


def _reese(f, d, sr, beat, rate=2, lo=500, hi=900, drive=1.5):
    m = int(sr * d); t = np.arange(m) / sr
    y = sum(2 * ((t * f * (1 + dt) + k * .3) % 1) - 1 for k, dt in enumerate((-.008, 0, .008)))
    lfo = lo + hi * (.5 + .5 * np.sin(2 * np.pi * t / beat * rate)); out = np.zeros(m); seg = int(sr * .02)
    for i in range(0, m, seg):
        b, a = sg.butter(2, min(.99, lfo[i] / (sr / 2)), "low"); out[i:i + seg] = sg.lfilter(b, a, y[i:i + seg])
    return np.tanh(drive * out) * _env(m, sr, .005, d)


def make_basstaiko(n, sr, beat, strong, h0, h1, seed=11):
    rng = np.random.default_rng(seed); out = np.zeros(n, np.float32); pad = np.zeros(n, np.float32); C = _clap(sr, rng)
    def add(buf, at, x, lv):
        i = int(round(at * sr))
        if 0 <= i < n: buf[i:i + len(x)] += (np.asarray(x)[: n - i] * lv).astype(np.float32)
    hb = int(round(h0 / beat))
    for b in range(hb - 2):
        g = .8 + .2 * min(1, b / max(1, hb - 4)); r = ROOTS_BT[(b // 4) % 4]
        add(out, b * beat, _kick(sr, 2.8), 1.0 * g)
        if b % 2: add(out, b * beat, C, .32 * g)
        add(out, b * beat + beat / 2, _hat(sr, rng, .08), .14 * g)
        add(pad, b * beat + beat / 2, _reese(HZ[r] * 2, beat * .48, sr, beat), .5 * g)
        if b % 4 == 0 or b in strong: add(out, b * beat, note("C2", sr, TAIKO), .65 * g)
        if b % 8 == 0: add(out, b * beat, note("C2", sr, TIMP), .4 * g)
        add(pad, b * beat, _sub808(HZ[r], beat * .9, sr), .55 * g)
    tt = np.arange(n) / sr; ph = (tt % beat) / beat; out += pad * (.2 + .8 * np.clip(ph / .4, 0, 1) ** .7)
    t0 = (hb - 2) * beat; m = int(2 * beat * sr); u = np.linspace(0, 1, m)
    rs = _hp(rng.standard_normal(m), sr, 1500) * u ** 2; add(out, t0, rs / np.abs(rs).max(), .3)
    for j, at in enumerate([t0 + beat * x for x in (0, .5, 1, 1.25, 1.5, 1.625, 1.75, 1.875)]): add(out, at, C, .16 + .05 * j)
    m = int(sr * 2.4); t = np.arange(m) / sr; fs_ = 70 * np.exp(-t * 1.6) + 32
    add(out, h0, _kick(sr, 3.0), 1.1); add(out, h0, np.tanh(2 * np.sin(2 * np.pi * np.cumsum(fs_) / sr)) * np.exp(-t / .9), .85)
    add(out, h0, note("C2", sr, TIMP), .5)
    out *= np.clip(tt / .05, 0, 1) * np.clip((h1 + 1.2 - tt) / 1.2, 0, 1)
    # 들리게: 저음 포화 배음 더하고, 120Hz 아래는 7dB 줄인다
    lo4 = lambda x, f: sg.sosfilt(sg.butter(4, f / (sr / 2), "low", output="sos"), x)
    hi4 = lambda x, f: sg.sosfilt(sg.butter(4, f / (sr / 2), "high", output="sos"), x)
    low = lo4(out, 180); pk = np.abs(low).max() + 1e-9
    out = out + hi4(np.tanh(low / pk * 4.0), 180) * pk * .9
    out = out - lo4(out, 120) * (1 - 10 ** (-7 / 20))
    return out.astype(np.float32)
