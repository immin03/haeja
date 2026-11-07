"""이미 렌더한 롱폼의 로고 인트로 소리만 다시 입힌다 (2026-11-07 SOXL 검수: 로고 중간 1.5초가 비어 들림).
영상은 그대로 두고, 로고 첫 박(h0)부터 인트로 곡의 가장 센 타격 + 웅장한 울림을 길게(1.6초) 울려 로고 끝까지 이어 준다.
사용: python3 fix_logo_ring.py 입력.mp4 출력.mp4 h0초 로고길이초 인트로곡.mp3 첫박초"""
import sys, subprocess, numpy as np
from scipy import signal as sg
src, dst, h0, dur, song, off = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5], float(sys.argv[6])
SR = 44100; h1 = h0 + dur
dec = lambda p, ch: np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32)
a = dec(src, 2).reshape(-1, 2).copy(); x = dec(song, 1)[int(off * SR):]
fr = 1024; seg = x[: 40 * SR]; e = np.array([np.sum(seg[j:j + fr] ** 2) for j in range(0, len(seg) - fr, fr // 2)])
j = int(np.argmax(np.maximum(0, np.diff(e)))) * (fr // 2)
L = int((dur + 1.0) * SR); st = x[j:j + L].copy()
if len(st) < L: st = np.pad(st, (0, L - len(st)))
st *= np.exp(-np.arange(L) / SR / 1.6).astype(np.float32)
n = int(SR * 3.2); t = np.arange(n) / SR; saw = lambda f: 2 * ((t * f) % 1) - 1
low = sum(saw(f) * w for f, w in ((55, 1), (82.41, .7), (110, .5), (164.8, .25)))
low = sg.lfilter(*sg.butter(2, 900 / (SR / 2)), low) * np.minimum(1, t / .06) * np.exp(-t / 1.4)
shine = sum(np.sin(2 * np.pi * f * t) * w for f, w in ((659.3, .5), (987.8, .3), (1318.5, .18))) * np.minimum(1, t / .25) * np.exp(-t / 1.8)
br = low / (np.abs(low).max() + 1e-9) + shine * .35
add = np.zeros(L, np.float32); add += st / (np.abs(st).max() + 1e-9) * .6; m = min(L, len(br)); add[:m] += (br / np.abs(br).max() * .45)[:m]
fo = int(.8 * SR); add[-fo:] *= np.linspace(1, 0, fo)
i0 = int(h0 * SR); w0, w1 = int((h0 + .4) * SR), int((h1 - .2) * SR); base = a[w0:w1].mean(1); g = 1.0
for _ in range(30): g *= 10 ** (-17 / 20) / max(float(np.sqrt(np.mean((base + g * add[w0 - i0:w1 - i0]) ** 2))), 1e-6)
a[i0:i0 + L] += g * add[: max(0, len(a) - i0), None]; pk = np.abs(a).max()
if pk > .98: a = a / pk * .98
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", dst], input=a.astype(np.float32).tobytes(), check=True)
print("로고 울림 보강:", round(g, 3), dst)
