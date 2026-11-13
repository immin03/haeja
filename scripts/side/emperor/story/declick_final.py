"""완성 영상 소리에서 story_gate 가 잡는 '틱'만 8ms 보간으로 지운다 (2026-11-14). 영상은 그대로 복사.
사용: python3 declick_final.py <in.mp4> <out.mp4>"""
import subprocess, sys, numpy as np
sys.path.insert(0, "/home/claude/haeja/scripts/side/emperor"); import voice_gate as G
src, dst = sys.argv[1:3]; SR = 44100
y = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True).stdout, np.float32).copy().reshape(-1, 2)
fixed = []; cur = src; import os, tempfile
def enc(path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", path], input=y.tobytes(), check=True)
tmp = os.path.join(tempfile.mkdtemp(), "t.mp4")
for it in range(8):   # 게이트와 같은 방식(인코딩된 파일을 그대로 읽어)으로 찾고, 고친 뒤 다시 인코딩해 확인
    z = G.load(cur); d = np.abs(np.diff(z)); w = int(.005 * G.SR); e = np.sqrt(np.convolve(z ** 2, np.ones(w) / w, "same"))
    c = [k / G.SR for k in np.where((d > .25) & (e[1:] < .05))[0]]
    if not c: break
    for t in c:
        k = int(t * SR); h = int(.006 * SR); l, r = k - h, k + h; x = np.linspace(0, 1, r - l)[:, None]; y[l:r] = y[l] * (1 - x) + y[r] * x
    fixed += [round(t, 2) for t in c]; enc(tmp); cur = tmp
print("고침", fixed, "· 남은 틱", len(c))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", dst], input=y.tobytes(), check=True)
