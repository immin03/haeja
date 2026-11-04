"""pauses longer than CAP s -> CAP s. python3 tighten.py in.mp3 out.wav CAP [end_sec]"""
import sys, subprocess, re, numpy as np
src, out, cap = sys.argv[1], sys.argv[2], float(sys.argv[3]); endsec = float(sys.argv[4]) if len(sys.argv) > 4 else None
sr = 44100
a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
if endsec: a = a[:int(endsec * sr)]
o = subprocess.run(["ffmpeg", "-i", src, "-af", "silencedetect=noise=-36dB:d=0.1", "-f", "null", "-"], capture_output=True, text=True).stderr
S = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", o)]; E = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", o)]
keep, pos = [], 0.0
for s, e in zip(S, E):
    if s < 0.01 or (endsec and s > endsec): continue
    if e - s > cap:
        keep.append((pos, s + cap / 2)); pos = e - cap / 2
keep.append((pos, len(a) / sr))
y = np.concatenate([a[int(x * sr):int(z * sr)] for x, z in keep if z > x])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le", out], input=y.tobytes(), check=True)
print(out, round(len(y) / sr, 2))
