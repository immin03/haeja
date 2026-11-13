"""목소리 조각 '틱' 소리 고치기 (2026-11-14) — story_gate 클릭 검사(믹스 뒤 음량을 가정해 1~1.5배)로 찾은 곳만 8ms 보간.
사용: python3 declick.py <입력 폴더> <출력 폴더> [파일 이름 조각] [배율 목록, 기본 1,1.5 — 믹스에서 크게 들어가는 끝부분 조각은 1,1.5,2]  → 출력 폴더에 같은 이름으로 저장(고칠 게 없으면 그대로 복사)"""
import os, shutil, subprocess, sys, numpy as np
sys.path.insert(0, "/home/claude/haeja/scripts/side/emperor"); import voice_gate as G
def rd(f):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "1", "-ar", "44100", "-"], capture_output=True).stdout; return np.frombuffer(r, np.float32).copy()
def wr(f, y): subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", "44100", "-ac", "1", "-i", "-", "-c:a", "libmp3lame", "-q:a", "2", f], input=y.astype(np.float32).tobytes(), check=True)
def clicks(y):
    d = np.abs(np.diff(y)); w = int(.005 * G.SR); e = np.sqrt(np.convolve(y ** 2, np.ones(w) / w, "same"))
    return [c / G.SR for c in np.where((d > .25) & (e[1:] < .05))[0]]
src, dst = sys.argv[1], sys.argv[2]; key = sys.argv[3] if len(sys.argv) > 3 else ""; GS = tuple(float(x) for x in (sys.argv[4] if len(sys.argv) > 4 else "1,1.5").split(",")); os.makedirs(dst, exist_ok=True)
for n in sorted(os.listdir(src)):
    if not n.endswith(".mp3") or key not in n: continue
    o = os.path.join(dst, n); shutil.copy(os.path.join(src, n), o); fixed = []
    for it in range(5):
        z = G.load(o); c = sorted(set(round(t, 3) for g in GS for t in clicks(z * g)))
        if not c: break
        y = rd(o)
        for t in c:
            k = int(t * 44100); h = int(.008 * 44100); l, r = max(0, k - h), min(len(y) - 1, k + h); x = np.linspace(0, 1, r - l); y[l:r] = y[l] * (1 - x) + y[r] * x
        wr(o, y); fixed += c
    if fixed: print(n, "고침", fixed, "남음" if c else "")
