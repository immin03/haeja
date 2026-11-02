"""황제의 일기 기본 템플릿 편 스펙 만들기 (2026-11-02, 4편부터)
내레이션 한 파일을 문장 구간으로 나눠 묶음(G1·G2·G3) 사이에 쉼을 넣고, 컷·자막 시각을 자동 계산한다.
python3 build_ep.py ep04  → spec_ep04.json + vo 조각
"""
import json, subprocess, sys, os
EPS = json.load(open(os.path.join(os.path.dirname(__file__), "eps_0406.json")))
VO = "/home/claude/vo/e5"
GEN = "/home/claude/haeja/social/side/gen"
XF = 0.4


def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout)


def build(key):
    E = EPS[key]
    src = f"{VO}/v_{key}.mp3"
    sents = E["sents"]  # [start, end, group, cut, style, lines]
    groups = sorted({s[2] for s in sents})
    voices, t = [], 0.8
    abs_t = {}
    for g in groups:
        ss = [s for s in sents if s[2] == g]
        a, b = ss[0][0] - 0.06, ss[-1][1] + 0.12
        piece = f"{VO}/{key}_g{g}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-af", "afade=t=in:d=0.03", piece], check=True)
        voices.append({"file": piece, "at": round(t, 3), "vol": E.get("vol", 1.3)})
        for i, s in enumerate(sents):
            if s[2] == g:
                abs_t[i] = (t + s[0] - a, t + s[1] - a)
        t += (b - a) + E.get("gap", 1.0)
    voice_end = max(v[1] for v in abs_t.values())
    ncut = len(E["cuts"])
    # 컷 시작: 그 컷 첫 문장 0.55초 전 (첫 컷 0)
    starts = []
    for k in range(ncut):
        idx = [i for i, s in enumerate(sents) if s[3] == k]
        starts.append(0.0 if k == 0 else round(abs_t[idx[0]][0] - 0.55, 3))
    cuts = []
    for k, c in enumerate(E["cuts"]):
        end = starts[k + 1] + XF if k + 1 < ncut else voice_end + E.get("hold", 1.4)
        d = round(end - starts[k], 3)
        cut = {"dur": d, "texts": [], "caps": []}
        if c.endswith(".mp4"):
            cut["v"] = c; L = dur(c); cut["speed"] = round(min(1.0, L / d * 0.98), 3)
            if "tablet" in c or "edv02_ep" in c: cut.update({"shade": 245, "shade_h": 1100})
        else:
            cut["img"] = c; cut["move"] = "in" if k % 2 == 0 else "out"; cut["amt"] = 0.08
        if k == 0:
            cut["texts"] += [{"t0": -1, "style": "kicker", "lines": [E["kicker"]], "after": 10}, {"t0": -1, "style": "hook", "lines": E["hook"]}]
        for i, s in enumerate(sents):
            if s[3] != k: continue
            a, b = abs_t[i]; la, lb = round(a - starts[k] - 0.05, 2), round(b - starts[k] + 0.15, 2)
            if s[4] == "cap":
                cut["caps"].append({"t0": max(0.05, la), "t1": lb, "lines": s[5]})
            elif s[4] == "silent":
                pass
            else:
                tx = {"t0": max(0.05, la), "lines": s[5], "style": s[4]}
                if s[4] == "sub": tx["after"] = 30
                cut["texts"].append(tx)
        for x in E.get("extra", {}).get(str(k), []):
            cut["texts"].append(x)
        if not cut["caps"]: del cut["caps"]
        cuts.append(cut)
    end_start = starts[-1] + cuts[-1]["dur"] - 0.25
    end = {"dur": E.get("end_dur", 5.0), "kicker": "오늘 밤 할 일", "lines": E["tonight"], "source": E["source"], "slogan": None}
    voices.append({"file": "/home/claude/vo/outro_default.mp3", "at": round(end_start + end["dur"] + 0.05, 3), "vol": 1.15})
    spec = {"id": key, "music": E["music"], "voice": voices, "cuts": cuts, "end": end, "outro": {"dur": 7.9, "p1": 4.7}}
    total = end_start + end["dur"] + 7.9
    json.dump(spec, open(f"/home/claude/ed/spec_{key}.json", "w"), ensure_ascii=False, indent=1)
    print(key, "voice_end", round(voice_end, 2), "end_start", round(end_start, 2), "total", round(total, 1), [c["dur"] for c in cuts])


for k in sys.argv[1:]:
    build(k)
