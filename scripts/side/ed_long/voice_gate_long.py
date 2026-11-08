"""황제의 일기 롱폼·소개 쇼츠 음성 관문 (2026-11-09 대표 승인 — 데일리 쇼츠 voice_gate.py 와 같은 장치)
사용: python3 voice_gate_long.py <spec_epNN.json> <완성본.mp4> [더 있으면 이어서]      # 롱폼 본편
      python3 voice_gate_long.py --teaser <spec_epNNp.json> <소개쇼츠.mp4> [인스타용.mp4]  # 소개 쇼츠 (앞부분 대사만 있음)
검사 — 하나라도 어기면 불통과, 도장을 찍지 않는다.
 A. 목소리 파일마다: 끝소리 끌기 · 중간 끌기 · 소리 끌림 · 말 속도 · 받아쓰기와 대본 일치
 B. 완성본마다: 대사가 순서대로 온전히 들어 있고 원본과 일치 · 조용한 곳 클릭 없음 · 전체 받아쓰기 일치
통과하면 <mp4>.voiceqa.json 도장을 남긴다. review_up.py 는 도장 없으면 관리자 검토로 안 올리고,
ed-yt-long 함수는 voice_qa 값 없이는 유튜브 업로드를 시작하지 않는다.
기준(11/9 실측, 롱폼 367개): 끝소리 정상 최대 1.17초 · 말 속도 정상 최저 4.34자/초 · 소리 끌림은 데일리와 같은 0.62초."""
import hashlib, json, os, re, subprocess, sys, time, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE + "/../emperor")
from take_check import held_runs, HOLD_MAX, DRAG_TH, norm, speech_seconds, _load, SR as TSR
import voice_gate as G
SR = G.SR; TAIL_MAX, MID_MAX, RATE_MIN = 1.25, 1.75, 4.2
SIM_PIECE, SIM_FULL, CORR_MIN = 0.78, 0.60, 0.85
ROOT = os.path.abspath(HERE + "/../../..")
FIXED = {"e_x2": "황제의 일기"}   # 매 편 같은 녹음이라 대본 파일이 없는 줄


def piece_why(f, text):
    why = []
    x = _load(f); win = int(.02 * TSR); e = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, "same")); end = np.where(e > e.max() * 10 ** (-35 / 20))[0][-1] / TSR
    for a, b in held_runs(f, th=DRAG_TH, min_len=0.25):
        if b >= end - .35 and b - a > TAIL_MAX: why.append(f"끝소리 끌기 {a}~{b}초 ({b - a:.2f}초, 기준 {TAIL_MAX})")
        elif b - a > MID_MAX: why.append(f"중간 끌기 {a}~{b}초 ({b - a:.2f}초, 기준 {MID_MAX})")
    for a, b in held_runs(f):
        if b - a > HOLD_MAX: why.append(f"소리 끌림 {a}~{b}초 ({b - a:.2f}초)")
    n = len(norm(text))
    if n >= 8:
        r = n / max(speech_seconds(f), .01)
        if r < RATE_MIN: why.append(f"말이 비정상적으로 느림 {r:.2f}자/초 (기준 {RATE_MIN})")
    return why


def load_fx(f, fx):
    c = ["ffmpeg", "-v", "error", "-i", f] + (["-af", fx.rstrip(",")] if fx else []) + ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(c, capture_output=True, check=True).stdout, np.float32).copy()


def manifest(S):
    vd = os.path.join(ROOT, S["voice_dir"]); mono = set(S.get("monologue_voices", [])); out = []; seen = set()
    for s in S["shots"]:
        v = s.get("voice"); v = [v] if isinstance(v, str) else (v or [])
        for n in v:
            if n in seen: continue
            seen.add(n); f = os.path.normpath(os.path.join(vd, S["voice_files"][n])); t = open(f + ".txt").read() if os.path.exists(f + ".txt") else None
            if t is None:
                t = S["subs"].get(n)
                t = " ".join(t) if isinstance(t, list) else t
            t = t or FIXED.get(n)
            if not t: sys.exit(f"불통과: {n} 대본을 찾을 수 없음")
            out.append(dict(name=n, file=f, text=t, fx=S.get("monologue_fx") if n in mono else None))
    return out


def stt_long(asr, y, step=45):
    o = []
    for i in range(0, len(y), step * SR):
        s = asr.create_stream(); s.accept_waveform(SR, y[i:i + step * SR]); asr.decode_stream(s); o.append(s.result.text)
    return " ".join(o)


def main(argv):
    teaser = "--teaser" in argv; argv = [a for a in argv if a != "--teaser"]; S = json.load(open(argv[0])); mp4s = argv[1:]
    M = manifest(S); fail = []; asr = G.recognizer()
    print(f"[A] 목소리 {len(M)}개")
    for m in M:
        s = asr.create_stream(); s.accept_waveform(SR, G.load(m["file"])); asr.decode_stream(s); m["sim"] = G.sim(m["text"], s.result.text)
        why = piece_why(m["file"], m["text"]) + ([f"받아쓰기 불일치 {m['sim']:.2f}"] if m["sim"] < SIM_PIECE else [])
        m["why"] = why
        if why: print(f"  {m['name']}: {why} · {m['text'][:30]}")
    for f in mp4s:
        print("[B]", os.path.basename(f)); y = G.load(f); last = -1.0; used = []; bad = []
        for i, m in enumerate(M):
            p = load_fx(m["file"], m["fx"]); at, r, n = G.locate(y, p)
            if at < last - 0.3 or r < CORR_MIN:
                if teaser and used: break     # 소개 쇼츠는 앞부분까지만 쓴다
                bad.append(f"{m['name']} 못 찾음/일그러짐 (자리 {at:.2f}, 상관 {r:.3f})"); continue
            used.append(m); last = at + n
        print(f"  대사 {len(used)}/{len(M)}개 확인 · 끝 {last:.1f}초")
        if teaser and not used: bad.append("대사를 하나도 찾지 못함")
        d = np.abs(np.diff(y)); w = int(.005 * SR); e = np.sqrt(np.convolve(y ** 2, np.ones(w) / w, "same")); c = np.where((d > .25) & (e[1:] < .05))[0]
        if len(c): bad.append(f"클릭 {len(c)}곳 {[round(x / SR, 2) for x in c[:6]]}")
        script = " ".join(m["text"] for m in used); fs = G.sim(script, stt_long(asr, y[:int((last + 1) * SR)])); print(f"  전체 받아쓰기 일치 {fs:.2f}")
        if fs < SIM_FULL: bad.append(f"전체 받아쓰기 불일치 {fs:.2f}")
        for m in (used if teaser else M):
            fail += [f"{m['name']}: {w}" for w in m["why"] if f"{m['name']}: {w}" not in fail]
        fail += [f"{os.path.basename(f)}: {b}" for b in bad]
    if fail:
        print("불통과"); [print(" -", x) for x in fail]
        for f in mp4s:
            if os.path.exists(f + ".voiceqa.json"): os.remove(f + ".voiceqa.json")
        sys.exit(1)
    for f in mp4s:
        h = hashlib.sha256(open(f, "rb").read()).hexdigest()
        json.dump({"passed": True, "sha256": h, "id": S["id"], "at": time.strftime("%F %T"), "ed_posts_voice_qa": "pass:" + h}, open(f + ".voiceqa.json", "w"))
        print("도장", os.path.basename(f), "pass:" + h)
    print("통과")


if __name__ == "__main__": main(sys.argv[1:])
