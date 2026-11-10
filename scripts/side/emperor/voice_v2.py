"""황제의 일기 쇼츠 음성 v2 (2026-11-04 대표: "성우 목소리 안 깨지게끔 철저하게")
- 문장 묶음마다 따로 녹음한 파일을 그대로 쓴다 (한 테이크를 잘라 붙이지 않음 → 이음새 없음)
- 명상록 인용(e*)은 황제 목소리(명일, 롱폼과 같은 막사 울림 아주 약간), 나머지(n*)는 해설 건석
- 조각마다 앞뒤 무음만 안전하게 다듬고(-50 dB, 0.15초 여유) 같은 크기(-16 LUFS)로 맞춘다. 48 kHz 유지
- 조각 사이는 디지털 무음 0.6초로 이어 한 파일로 만들고, 문장 시각을 다시 잰다 → long_<id>a.json
사용: python3 voice_v2.py <ep> <take A|B per piece, 예: A,A,B,A> <voice_dir>"""
import json, re, subprocess, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from take_check import check as take_check, norm as _norm
SR = 48000; GAP = 0.6
MONO_FX = "highpass=f=70,aecho=0.9:0.35:35|70:0.09|0.04"   # 롱폼 황제 독백과 같은 값
HERE = os.path.dirname(os.path.abspath(__file__))

def load(f, af=None):
    cmd = ["ffmpeg", "-v", "error", "-i", f] + (["-af", af] if af else []) + ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).copy()

def lufs(a):
    r = subprocess.run(["ffmpeg", "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", "ebur128", "-f", "null", "-"], input=a.tobytes(), capture_output=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr.decode()); return float(m[-1])

def trim(a, thr_db=-50, pad=0.15):
    win = int(0.01 * SR); e = np.sqrt(np.convolve(a ** 2, np.ones(win) / win, "same")); thr = 10 ** (thr_db / 20)
    idx = np.where(e > thr)[0]
    if not len(idx): return a
    s, t = max(0, idx[0] - int(pad * SR)), min(len(a), idx[-1] + int(pad * SR))
    y = a[s:t].copy(); f = int(0.01 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f); return y

def speech_runs(a, thr_db=-42, min_gap=0.16):
    win = int(0.01 * SR); e = np.sqrt(np.convolve(a ** 2, np.ones(win) / win, "same")) > 10 ** (thr_db / 20)
    runs, on, st = [], False, 0
    for i in range(0, len(e), win):
        v = e[i]
        if v and not on: on, st = True, i
        if not v and on: on = False; runs.append([st / SR, i / SR])
    if on: runs.append([st / SR, len(e) / SR])
    out = []
    for r in runs:
        if out and r[0] - out[-1][1] < min_gap: out[-1][1] = r[1]
        else: out.append(r)
    return out

def split_times(a, n, texts):
    """조각 안 문장 n개의 시작·끝 (2026-11-04 고침: 말 덩어리를 문장 글자 수 비율에 가장 잘 맞게 나눔 — 쉼이 큰 곳만 고르면
    '화가 나면, 곧바로…'처럼 쉼표 쉼에서 잘려 자막이 말보다 먼저 넘어감)"""
    runs = speech_runs(a); m = len(runs)
    if m < n:
        L = [len(t) for t in texts]; T0, T1 = runs[0][0], runs[-1][1]; tot = sum(L); out, x = [], T0
        for l in L: y = x + (T1 - T0) * l / tot; out.append([x, y]); x = y
        return out
    L = [len(re.sub(r"\s", "", t)) for t in texts]; ct = sum(L)
    T = runs[-1][1] - runs[0][0]
    import functools
    @functools.lru_cache(None)
    def best(i, k):   # runs[i:] 를 문장 k.. 에 나눠 담는 최소 비용
        if k == n: return (0.0, ()) if i == m else (1e9, ())
        if m - i < n - k: return (1e9, ())
        res = (1e9, ())
        last = m if k == n - 1 else m - (n - k - 1)
        for j in range(i + 1, last + 1):
            d = runs[j - 1][1] - runs[i][0]
            c = (d / T - L[k] / ct) ** 2
            if j < m and k < n - 1: c -= 0.002 * (runs[j][0] - runs[j - 1][1])   # 쉼이 길수록 조금 선호
            sub = best(j, k + 1)
            if c + sub[0] < res[0]: res = (c + sub[0], (j,) + sub[1])
        return res
    cuts = best(0, 0)[1]; out, s0 = [], 0
    for j in cuts: out.append([runs[s0][0], runs[j - 1][1]]); s0 = j
    return out

def main(ep, takes, vdir):
    lines = json.load(open(os.environ.get("ED_LINES", "/home/claude/vo/v2_lines.json")))[ep]
    old = json.load(open(f"{HERE}/long_{ep}.json"))
    takes = takes.split(",")
    # 예전 문장 목록을 조각에 나눠 담기 (조각 글에 들어 있는 문장 순서대로)
    sents = old["sents"]; si = 0; pieces = []; full = []; t = 0.3
    out_sents = []
    for k, ((nm, vid, line), tk) in enumerate(zip(lines, takes)):
        f = [x for x in os.listdir(vdir) if x.endswith(f"_{ep}_{nm}_{tk}.mp3")][0]
        ok, why = take_check(os.path.join(vdir, f), line if os.path.exists(os.path.join(vdir, f) + ".txt") else None)   # 2026-11-04 녹음 결함·원문 검사
        if not ok: sys.exit(f"테이크 불통과 {f}: {why} — 다른 테이크(A/B)를 고르거나 다시 녹음")
        a = load(os.path.join(vdir, f), MONO_FX if nm.startswith("e") else None)
        a = trim(a); g = 10 ** ((-16 - lufs(a)) / 20); a = a * g
        pk = float(np.abs(a).max())
        if pk > 0.89: a = a * (0.89 / pk)
        mine = []
        flat = re.sub(r"[\s'\",.?!]", "", line)
        while si < len(sents) and re.sub(r"[\s'\",.?!]", "", " ".join(sents[si][5])) in flat: mine.append(sents[si]); si += 1
        tm = split_times(a, len(mine), [" ".join(s[5]) for s in mine])
        for q, (s, (x, y)) in enumerate(zip(mine, tm)):
            y2 = (tm[q + 1][0] - 0.05) if q + 1 < len(tm) else max(y, len(a) / SR - 0.1)
            out_sents.append([round(t + x, 3), round(t + max(y, y2), 3), k + 1, s[3], s[4], s[5]])
        full.append(np.zeros(int(0.3 * SR) if k == 0 else int(GAP * SR), np.float32)); full.append(a); t += len(a) / SR + GAP
        pieces.append((nm, tk, round(len(a) / SR, 2), len(mine)))
    assert si == len(sents), f"문장 {len(sents) - si}개가 조각에 안 들어감: {sents[si][5]}"
    y = np.concatenate(full + [np.zeros(int(0.5 * SR), np.float32)])
    wav = f"/home/claude/vo/v2/v_{ep}a.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s24le", wav], input=y.tobytes(), check=True)
    new = dict(old); new.update(id=f"{ep}a", theme="A", voice=wav, sents=out_sents, vol=1.0,
                                note=old.get("note", "") + " | 2026-11-04 v2: 묶음별 녹음, 인용은 황제(명일), 잘라 붙이지 않음, -16 LUFS, 레이아웃 A")
    # 2026-11-04 8편 사고: '오늘의 할 일' 녹음은 이 편 대본(tonight)으로 새로 녹음한 것만 쓴다 — 원문(.txt) 대조 + 소리 끌림 검사
    if old.get("end_voice"):
        ev = old["end_voice"]; src = ev if os.path.exists(ev + ".txt") else os.environ.get("ED_END_SRC", ev)
        want = " ".join(old["tonight"])
        side = open(src + ".txt").read() if os.path.exists(src + ".txt") else None
        ok, why = take_check(src)
        if side is None: why.append("'오늘의 할 일' 녹음 원문(.txt) 없음 — 이 편 문장으로 새로 녹음할 것 (다른 편 녹음 금지)")
        elif _norm(side) not in (_norm(want), _norm("오늘의 할 일" + want), _norm("오늘의 할 일은" + want), _norm("Tonight's task. " + want)):   # 2026-11-11 영어 채널
            why.append(f"'오늘의 할 일' 원문 불일치: 녹음='{side.strip()}' / 화면='{want}'")
        if why: sys.exit(f"엔딩 녹음 불통과 {os.path.basename(src)}: {why}")
    for key in ("end_voice", "outro_voice"):
        if old.get(key):
            b = trim(load(old[key])); b = b * 10 ** ((-16 - lufs(b)) / 20); p = f"/home/claude/vo/v2/{ep}_{key}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s24le", p], input=b.tobytes(), check=True); new[key] = p
    json.dump(new, open(f"{HERE}/long_{ep}a.json", "w"), ensure_ascii=False, indent=1)
    print(ep, pieces, "len", round(len(y) / SR, 2))

if __name__ == "__main__": main(*sys.argv[1:4])
