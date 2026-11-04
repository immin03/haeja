"""황제의 일기 쇼츠 음성 검사 (2026-11-04 대표: "성우 목소리 안 깨지게끔 철저하게")
python3 voice_qa.py <final.mp4> <spec.json>   → 통과하면 exit 0
1) 목소리 조각마다 완성본에서 같은 자리의 소리와 비교(상관계수) — 0.90 미만이면 일그러짐/겹침
2) 조용한 곳의 '딱' 소리(클릭) 찾기
3) 전체 크기 -17~-13 LUFS, 최고점 -1.0 dBTP 이하"""
import json, re, subprocess, sys, numpy as np
SR = 48000
def load(f, ch=1):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32)
def main(mp4, spec):
    S = json.load(open(spec)); y = load(mp4); ok = True; rows = []
    for v in S["voice"]:
        p = load(v["file"]); s = int(v["at"] * SR); seg = y[s:s + len(p)]
        if len(seg) < len(p) * 0.9: rows.append((v["file"].split("/")[-1], "잘림", 0)); ok = False; continue
        best = 0
        for sh in range(-480, 481, 48):   # ±10 ms 맞춰 보기
            a = y[max(0, s + sh):max(0, s + sh) + len(p)]; n = min(len(a), len(p))
            m = np.abs(p[:n]) > 0.02
            if m.sum() < 100: continue
            c = np.corrcoef(a[:n][m], p[:n][m])[0, 1]; best = max(best, c)
        rows.append((v["file"].split("/")[-1], "ok" if best >= 0.90 else "확인", round(float(best), 3)))
        if best < 0.90: ok = False
    d = np.abs(np.diff(y)); win = int(0.005 * SR)
    e = np.sqrt(np.convolve(y ** 2, np.ones(win) / win, "same"))
    clicks = [round(i / SR, 2) for i in np.where((d > 0.25) & (e[1:] < 0.05))[0]]
    st = subprocess.run(["ffmpeg", "-v", "info", "-i", mp4, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", st)[-1]); tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", st)[-1])
    for r in rows: print("  ", *r)
    print(f"클릭 {len(clicks)}곳 {clicks[:8]} · 크기 {I} LUFS · 최고점 {tp} dBTP")
    if clicks or not (-17 <= I <= -13) or tp > -1.0: ok = False
    print("통과" if ok else "불통과"); sys.exit(0 if ok else 1)
if __name__ == "__main__": main(*sys.argv[1:3])
