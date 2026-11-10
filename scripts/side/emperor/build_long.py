"""황제의 일기 '해설형' 50~60초 편 스펙 만들기 (2026-11-03 첫 실험: ep06x)
템플릿(30초)과 다른 점
- 고정 제목: 첫 컷의 훅 문구를 모든 컷 맨 위에 금색 한 줄로 계속 띄운다(참고: 명언 쇼츠의 상단 고정 제목)
- 원문 인용 뒤에 '풀이' 문장 2~3개를 더한다(장소를 바꿔도… / 그래서 황제는… / 쉼은…) → 이 원고가 그대로 책의 한 꼭지가 된다
사용: python3 build_long.py long_ep06x.json  → /home/claude/ed/spec_<id>.json
long_*.json = {id, kicker, hook[2], title_line, music, voice(mp3), gap, hold, cuts[...], sents[[start,end,group,cut,style,lines]...], tonight[2], source}
"""
import json, subprocess, sys, os

XF = 0.4


def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout)


def build(path):
    E = json.load(open(path)); key = E["id"]
    src = E["voice"]; work = os.path.dirname(src)
    sents = E["sents"]
    groups = sorted({s[2] for s in sents})
    voices, t, abs_t = [], 0.8, {}
    for g in groups:
        ss = [s for s in sents if s[2] == g]
        a, b = max(0, ss[0][0] - 0.12), ss[-1][1] + 0.18   # 2026-11-04: 첫소리·말끝이 잘리지 않게 여유를 더 둠
        piece = f"{work}/{key}_g{g}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", src, "-af", f"asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={max(0, b - a - 0.04):.3f}:d=0.04", piece], check=True)
        voices.append({"file": piece, "at": round(t, 3), "vol": E.get("vol", 1.3)})
        for i, s in enumerate(sents):
            if s[2] == g: abs_t[i] = (t + s[0] - a, t + s[1] - a)
        t += (b - a) + E.get("gap", 1.0)
    voice_end = max(v[1] for v in abs_t.values())
    ncut = len(E["cuts"]); starts = []
    for k in range(ncut):
        idx = [i for i, s in enumerate(sents) if s[3] == k]
        starts.append(0.0 if k == 0 else round(abs_t[idx[0]][0] - 0.55, 3))
    cuts = []
    for k, c in enumerate(E["cuts"]):
        end = starts[k + 1] + XF if k + 1 < ncut else voice_end + E.get("hold", 1.6)
        d = round(end - starts[k], 3)
        cut = {"dur": d, "texts": [], "caps": []}
        if c.endswith(".mp4"):
            cut["v"] = c; L = dur(c); cut["speed"] = round(min(1.0, L / d * 0.98), 3)
            if "tablet" in c or "edv02_ep" in c: cut.update({"shade": 245, "shade_h": 1100})
        else:
            cut["img"] = c; cut["move"] = "in" if k % 2 == 0 else "out"; cut["amt"] = 0.08
        if k == 0:
            cut["texts"] += [{"t0": -1, "style": "kicker", "lines": [E["kicker"]], "after": 10}, {"t0": -1, "style": "hook", "lines": E["hook"]}]
        else:  # 고정 제목 (모든 컷 맨 위)
            cut["texts"].append({"t0": -1, "style": "sub", "lines": [E["title_line"]], "after": 34})
        for i, s in enumerate(sents):
            if s[3] != k: continue
            a, b = abs_t[i]; la, lb = round(a - starts[k] - 0.05, 2), round(b - starts[k] + 0.15, 2)
            if s[4] == "cap":
                cut["caps"].append({"t0": max(0.05, la), "t1": lb, "lines": s[5]})
            else:
                cut["texts"].append({"t0": max(0.05, la), "lines": s[5], "style": s[4]})
        if not cut["caps"]: del cut["caps"]
        cuts.append(cut)
    end_start = starts[-1] + cuts[-1]["dur"] - 0.25
    # 2026-11-03 대표: 마지막 화면 이름을 '오늘의 할 일'로(아침·점심 편에도 맞게), 그 화면에도 내레이션을 넣어 공백을 없앤다
    end_dur = E.get("end_dur", 5.0)
    if E.get("end_voice"):
        ev = E["end_voice"]; evd = dur(ev)
        voices.append({"file": ev, "at": round(end_start + 0.55, 3), "vol": E.get("vol", 1.3)})
        end_dur = max(end_dur, round(0.55 + evd + 1.1, 2))
    end = {"dur": end_dur, "kicker": E.get("end_kicker", "TONIGHT'S TASK" if os.environ.get("ED_LANG") == "en" else "오늘의 할 일"), "lines": E["tonight"], "source": E["source"], "slogan": None}
    voices.append({"file": E.get("outro_voice", "/home/claude/vo/outro_default.mp3"), "at": round(end_start + end["dur"] - 0.1, 3), "vol": 1.0})
    spec = {"id": key, "music": E["music"], "voice": voices, "cuts": cuts, "end": end, "outro": {"dur": 7.9, "p1": 4.7}}
    total = end_start + end["dur"] + 7.9
    # 2026-11-09 ep18(63초) 사고: 유튜브는 1분 넘는 쇼츠에 소유권 주장이 걸리면 전 세계 차단한다. secret-garden 은 RouteNote 주장('You Called Me')이 걸리는 곡 (TEMPLATE 고정값)
    if total >= 57 and "secret-garden" in E["music"]["file"]:
        sys.exit(f"{key}: {total:.1f}초 편에 secret-garden 사용 금지(1분 초과 쇼츠는 소유권 주장 시 전 세계 차단) — music 을 classical-7(start 91, bed 0.22) 또는 miss-you(start 19.5, bed 0.22)로 바꿀 것")
    out = f"/home/claude/ed/spec_{key}.json"
    json.dump(spec, open(out, "w"), ensure_ascii=False, indent=1)
    print(key, "voice_end", round(voice_end, 2), "end_start", round(end_start, 2), "total", round(total, 1), [c["dur"] for c in cuts])


if __name__ == "__main__":
    for p in sys.argv[1:]: build(p)
