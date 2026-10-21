"""롱폼 최종 검수 (운영자 지시 목록 기준). 사용: python3 qa.py <video.mp4> <meta.json> [출력 폴더]
1) 발음: 문장마다 음성 인식으로 다시 받아 적어 원고와 맞춰 본다 (낮은 줄 = 다시 들어볼 곳)
2) 화면: 같은 화면이 3초 넘게 머무는 곳 (끝 화면 제외)
3) 실사: 같은 소스 반복 / 예비(공용) 영상 사용
4) 소리: 말 속도(초당 음절), 음악 크기(말 없는 구간 대비)
"""
import json, os, re, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "reels"))
import verify  # noqa: E402

video, meta_p = sys.argv[1], sys.argv[2]
meta = json.load(open(meta_p)); qa = meta.get("qa", {})
SR = 16000
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
A = np.frombuffer(pcm, np.float32)
rep = {"pron": [], "static": [], "media": {}, "audio": {}}

# 1) 발음
for t, d, text, say in qa.get("lines", []):
    seg = A[int(max(0, t - .05) * SR): int((t + d + .1) * SR)]
    heard = verify.hear(seg, SR); sc = verify.score(text, heard)
    if sc < .86: rep["pron"].append({"t": t, "score": round(sc, 2), "text": text, "said_as": say, "heard": heard})
# 2) 화면
Wd, Hd = 192, 108
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps=8,scale={Wd}:{Hd},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
F = np.frombuffer(raw, np.uint8).reshape(-1, Hd, Wd).astype(np.float32); st = 0; dur = len(F) / 8
for i in range(1, len(F) + 1):
    if i == len(F) or np.abs(F[i] - F[st]).mean() > 5:
        L = (i - st) / 8
        if L > 3 and st / 8 < dur - 14: rep["static"].append({"t": round(st / 8, 1), "sec": L})
        st = i
# 3) 실사
med = qa.get("media", [])
names = [m[2] for m in med]
rep["media"] = {"cuts": len(med), "repeated": sorted({n for n in names if names.count(n) > 1}),
                "fallback": sum(1 for m in med if m[1] == "fallback"),
                "kinds": {k: sum(1 for m in med if m[1] == k) for k in ("photo", "video", "fallback")}}
# 4) 소리
lines = qa.get("lines", [])
syl = sum(len(re.sub(r"[^가-힣]", "", say)) for _, _, _, say in lines); speech = sum(d for _, d, _, _ in lines)
mask = np.zeros(len(A), bool)
for t, d, _, _ in lines: mask[int(t * SR): int((t + d) * SR)] = True
rms = lambda x: float(np.sqrt(np.mean(x ** 2)) + 1e-9)
quiet = A[~mask][int(3 * SR):-int(3 * SR)] if (~mask).sum() > 8 * SR else A[~mask]
rep["audio"] = {"syll_per_sec": round(syl / max(speech, 1), 2), "speech_db": round(20 * np.log10(rms(A[mask])), 1),
                "gap_db(음악만)": round(20 * np.log10(rms(quiet)), 1), "duration": round(len(A) / SR, 1)}
print(json.dumps(rep, ensure_ascii=False, indent=1))
