"""롱폼 화면 반복 점검기 (2026-10-24 운영자: "모눈종이도 항상 같고 저울도 항상 같고… 머니스웨거는 같은 형태로 하는 게 하나도 없어")
사용: python3 scripts/youtube/long/vary.py scripts/youtube/long/specs/<새 원고>.json
규칙 (어기면 ✗, 종료 코드 1):
  1. look(바탕 질감·어두운 색·강조색)이 있어야 하고, 직전 롱폼 2편과 셋 다 같으면 안 된다.
  2. 한 편 안에서 같은 화면 종류는 2번까지 (큰 숫자 stat 은 3번, 장 제목 title·질문 question·실사 media·끝 end 는 제외).
  3. 강한 비유 화면(저울 scale, 식 equation, 영수증 receipt, 대결 versus)은 한 편에 각 1번까지,
     직전 롱폼에서 쓴 비유 화면은 이번 편에 쓰지 않는다.
  4. 연달아 같은 화면 종류 금지 (title/question 사이에 끼는 것 제외).
  5. 실사(media 또는 backdrop) 장면이 전체의 30% 이상.
  6. 서로 다른 화면 종류가 8가지 이상.
"""
import json, os, sys, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = {"title", "question", "media", "end", "agenda", "sketch"}   # sketch: 2026-10-27 취재 노트 핵심 그림 5~8개 (FORMAT.md ★)
METAPHOR = {"scale", "equation", "receipt", "versus"}


def types(spec):
    return [s["v"]["type"] for s in spec["scenes"]]


def main(path):
    spec = json.load(open(path, encoding="utf-8")); me = os.path.basename(path)
    prev = sorted(p for p in glob.glob(os.path.join(HERE, "specs", "L*.json")) if not p.endswith(".data.json") and os.path.basename(p) < me and "TEST" not in p)[-2:]
    prev = [json.load(open(p, encoding="utf-8")) for p in prev]
    bad, ok = [], []
    ty = types(spec); c = collections.Counter(ty)
    look = spec.get("look")
    if not look: bad.append("look 없음: 바탕 질감(paper)·어두운 색(dark)·강조색(accent)을 정하세요")
    else:
        same = [p["id"] for p in prev if p.get("look") and all(p["look"].get(k) == look.get(k) for k in ("paper", "dark", "accent"))]
        if same: bad.append(f"look 이 직전 편({', '.join(same)})과 같습니다")
        else: ok.append(f"look {look.get('paper')}·{look.get('dark')}·{look.get('accent')}")
    for k, n in c.items():
        if k in FREE: continue
        lim = 1 if k in METAPHOR else (3 if k == "stat" else 2)
        if n > lim: bad.append(f"'{k}' 화면 {n}번 (한 편에 {lim}번까지)")
    if prev:
        last = set(types(prev[-1])) & METAPHOR
        rep = sorted(last & set(ty))
        if rep: bad.append(f"직전 편({prev[-1]['id']})에서 쓴 비유 화면을 또 씀: {', '.join(rep)}")
    seq = [x for x in ty if x not in ("title", "question")]
    for a, b in zip(seq, seq[1:]):
        if a == b and a not in ("media", "sketch"): bad.append(f"같은 화면 연속: {a} → {b}"); break
    real = sum(1 for s in spec["scenes"] if s["v"]["type"] == "media" or s["v"].get("backdrop"))
    if real / max(1, len(ty)) < .30: bad.append(f"실사 장면 {real}/{len(ty)} ({real / len(ty):.0%}) — 30% 이상으로")
    else: ok.append(f"실사 {real}/{len(ty)}")
    kinds = len([k for k in c if k not in ("title", "end")])
    if kinds < 8: bad.append(f"화면 종류 {kinds}가지 — 8가지 이상으로")
    else: ok.append(f"화면 종류 {kinds}가지")
    print("화면 구성:", dict(c))
    for x in ok: print("  ✓", x)
    for x in bad: print("  ✗", x)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1])
