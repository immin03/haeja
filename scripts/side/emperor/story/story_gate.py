"""이야기형 쇼츠 음성 관문 (2026-11-14) — voice_gate.py 와 같은 기준을 이야기형(plan.json)에 적용한다.
사용: python3 story_gate.py <WK>/plan.json <final.mp4>
 A 조각마다: 소리 끌기·늘어짐·받아쓰기 일치 0.80   B 올릴 파일: 조각 자리(±0.7초)·상관 0.90·클릭·크기 -17~-13 LUFS·전체 받아쓰기 0.72
통과하면 <mp4>.voiceqa.json 도장."""
import hashlib, json, os, re, subprocess, sys, time
sys.path.insert(0, "/home/claude/haeja/scripts/side/emperor")
import numpy as np, voice_gate as G
from take_check import drag_why, held_runs, HOLD_MAX
S = json.load(open(sys.argv[1])); f = sys.argv[2]; G.LANG = S["lang"]; asr = G.recognizer(); fail = []
def stt(x):
    s = asr.create_stream(); s.accept_waveform(G.SR, x); asr.decode_stream(s); return s.result.text
print("[A] 목소리 조각"); P = []
for v in S["voice"]:
    p = G.load(v["file"]); P.append(p); sm = G.sim(v["text"], stt(p)); n = os.path.basename(v["file"])
    why = drag_why(v["file"], v["text"]) + [f"소리 끌림 {a}~{b}초" for a, b in held_runs(v["file"]) if b - a > HOLD_MAX]
    if sm < G.SIM_PIECE: why.append(f"받아쓰기 불일치 {sm:.2f}")
    print(f"  {n} 일치 {sm:.2f} {'ok' if not why else why}"); fail += [f"{n}: {w}" for w in why]
print("[B]", os.path.basename(f)); y = G.load(f); last = -1
for v, p in zip(S["voice"], P):
    at, r, n = G.locate(y, p); st = "ok"
    if abs(at - v["at"]) > 0.7: st = f"자리 어긋남 {at:.2f}/{v['at']:.2f}"
    elif r < G.CORR_MIN: st = f"일그러짐 상관 {r:.3f}"
    elif at < last - 0.05: st = f"앞 조각과 겹침"
    last = at + n; print(f"  {os.path.basename(v['file'])} @{at:.2f} 상관 {r:.3f} {st}")
    if st != "ok": fail.append(f"{os.path.basename(v['file'])}: {st}")
d = np.abs(np.diff(y)); w = int(.005 * G.SR); e = np.sqrt(np.convolve(y ** 2, np.ones(w) / w, "same"))
clicks = np.where((d > .25) & (e[1:] < .05))[0]
if len(clicks): fail.append(f"클릭 {len(clicks)}곳 {[round(c / G.SR, 2) for c in clicks[:6]]}")
st = subprocess.run(["ffmpeg", "-hide_banner", "-i", f, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", st)[-1])
if not -17 <= I <= -13: fail.append(f"크기 {I} LUFS")
script = " ".join(v["text"] for v in S["voice"]) + " " + (G.OUTRO_TXT_EN if S["lang"] == "en" else G.OUTRO_TXT)
fs = G.sim(script, stt(y)); print(f"  크기 {I} LUFS · 전체 받아쓰기 일치 {fs:.2f}")
if fs < G.SIM_FULL: fail.append(f"전체 받아쓰기 불일치 {fs:.2f}")
if fail:
    print("불통과"); [print(" -", x) for x in fail]
    if os.path.exists(f + ".voiceqa.json"): os.remove(f + ".voiceqa.json")
    sys.exit(1)
h = hashlib.sha256(open(f, "rb").read()).hexdigest()
json.dump({"passed": True, "sha256": h, "id": S["id"], "at": time.strftime("%F %T"), "gate": "story_gate", "ed_posts_voice_qa": "pass:" + h}, open(f + ".voiceqa.json", "w"))
print("도장 pass:" + h); print("통과")
