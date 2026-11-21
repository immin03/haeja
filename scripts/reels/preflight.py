"""렌더 보내기 전 로컬 점검 (2026-11-21 대표: 효율 극대화) — 서버 렌더(체크아웃만 수 분)를 돌리기 전에 몇 초 안에 막힐 것을 다 잡는다.
  PYTHONPATH=scripts/reels python3 scripts/reels/preflight.py <id> [...]
점검: 대본 존재·자막=내레이션 등 gate 규칙·쇼츠 표지 대본(thumbs_bw) 존재·표지 사진 존재. 하나라도 걸리면 exit 1.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
LIB = os.path.join(HERE, "..", "blog", "media", "lib")
bad = 0
for i in sys.argv[1:]:
    p = os.path.join(HERE, "specs", f"{i}.json")
    if not os.path.exists(p): print(f"✗ {i}: 대본 없음"); bad += 1; continue
    spec = json.load(open(p, encoding="utf-8"))
    try:
        import gate; gate.enforce(spec)
    except (Exception, SystemExit) as e: print(f"✗ {i}: gate {e}"); bad += 1; continue
    if spec.get("platform") == "youtube" and spec.get("thumb_end", True) and spec.get("look") != "classic":
        tb = os.path.join(HERE, "thumbs_bw", f"{i}.json")
        if not os.path.exists(tb) and not spec.get("thumb_file"): print(f"✗ {i}: 표지 대본 thumbs_bw/{i}.json 없음"); bad += 1; continue
        if os.path.exists(tb):
            ph = json.load(open(tb, encoding="utf-8")).get("photo")
            if ph and not os.path.exists(os.path.join(LIB, ph)): print(f"✗ {i}: 표지 사진 {ph} 없음"); bad += 1; continue
    print(f"✓ {i}: 렌더 보내도 됨")
sys.exit(1 if bad else 0)
