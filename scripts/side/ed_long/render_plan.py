"""황제의 일기 롱폼 구간 병렬 렌더 도우미 (2026-11-11 대표: "그렇게 하자" — 롱폼을 GitHub 러너 여러 대에 나눠 그려 1시간 → 15~20분).
워크플로 .github/workflows/ed-long-render.yml 가 쓴다.

python3 render_plan.py paths  <spec.json>          → 렌더에 필요한 저장소 경로(스파스 체크아웃용), 한 줄에 하나
python3 render_plan.py audio  <spec.json>          → 소리 합치기에만 필요한 경로(목소리·음악·효과음)
python3 render_plan.py chunks <spec.json> <n>      → plan_<id>.json(렌더러 --plan 이 씀)을 읽어 n 조각 [{"name","from","to"}] JSON
조각 경계는 장면 시작 시각에만 둔다. 이어 붙일 때 앞 장면이 필요한 장면(디졸브로 들어오는 장면)은 경계로 쓰지 않는다.
렌더러는 프레임마다 전체 시각(gt)으로 from ≤ gt < to 를 고르므로 조각끼리 프레임이 겹치거나 빠지지 않는다.
"""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def load(spec):
    S = json.load(open(spec)); base = os.path.dirname(os.path.abspath(spec))
    root = os.path.abspath(os.path.join(base, S.get("root", "../../..")))
    rel = lambda p: os.path.relpath(p if os.path.isabs(p) else os.path.join(root, p), ROOT)
    return S, base, rel


def voice_paths(S, rel):
    vd = rel(S["voice_dir"]); out = set()
    for f in S["voice_files"].values():
        out.add(os.path.normpath(os.path.join(vd, f)))
    return sorted(out)


def audio_paths(S, rel):
    return voice_paths(S, rel) + [rel(S["music_dir"]), rel(S["sfx_dir"])]


def paths(S, rel):
    gd = rel(S["gen_dir"]); out = set(audio_paths(S, rel))
    for sh in S["shots"]:
        if sh.get("src"):
            out.add(f"{gd}/{sh['src']}.mp4" if sh["type"] == "video" else f"{gd}/{sh['src']}.jpeg")
        for ov in sh.get("overlays", []):
            if ov.get("src") and isinstance(ov["src"], str) and not ov["src"].startswith(("Meditations", "-")) and "/" not in ov["src"] and " " not in ov["src"]:
                out.add(f"{gd}/{ov['src']}.*")
    if S.get("intro", {}).get("logo"): out.add(rel(S["intro"]["logo"]))
    out.add("docs/emperor/profile_final.png")
    return sorted(out)


def chunks(S, base, n):
    plan = json.load(open(os.path.join(base, f"plan_{S['id']}.json")))
    total = plan[-1]["t0"] + plan[-1]["dur"]
    ok = [p["t0"] for i, p in enumerate(plan) if i > 0 and S["shots"][i].get("tin", "cut") != "dissolve"]
    cuts = []
    for k in range(1, n):
        want = total * k / n
        best = min((t for t in ok if not cuts or t > cuts[-1] + 5), key=lambda t: abs(t - want), default=None)
        if best is not None and 5 < best < total - 5: cuts.append(best)
    edges = [0.0] + sorted(set(cuts)) + [total + 1.0]
    return [{"name": f"c{i:02d}", "from": round(a, 4), "to": round(b, 4)} for i, (a, b) in enumerate(zip(edges, edges[1:]))]


if __name__ == "__main__":
    cmd, spec = sys.argv[1], sys.argv[2]; S, base, rel = load(spec)
    if cmd == "paths": print("\n".join(paths(S, rel)))
    elif cmd == "audio": print("\n".join(audio_paths(S, rel)))
    elif cmd == "chunks": print(json.dumps(chunks(S, base, int(sys.argv[3]))))
