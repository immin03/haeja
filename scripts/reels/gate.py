"""렌더 전 자동 차단 (2026-11-12 대표: "왜 이런 현상이 계속 무한 반복돼")

규칙을 기억에 맡기지 않고, 어기면 렌더 자체가 시작되지 않게 한다.
11/12 이후 대본(id 날짜 261112~)부터 적용 — 이미 나간 옛 대본은 건드리지 않는다.

막는 것
 1. 자막이 내레이션과 다름 (요약 자막 금지 — 말 그대로 한 줄씩)
 2. 같은 사진·영상을 두 장면 이상에 씀
 3. 제목 띠·제목이 알아듣기 어려움: 숫자 없음 / 질문·대비 없음 / 분석 용어(몫 등)
 4. 윤석열 사진 (대표 지시 — 다른 실존 인물은 써도 된다)
"""
import json, os, re

BAN_WORDS = ["몫", "밸류에이션 갭", "디레이팅", "리레이팅", "멀티플", "펀더멘털", "모멘텀"]   # 시청자가 모르는 분석 용어
YOON = re.compile(r"yoon|suk[- ]?yeol|윤석열", re.I)
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "blog", "media", "lib")


def _norm(s):
    return re.sub(r"[\s,.!?…·'\"“”‘’()\-]", "", s or "")


def _date(spec):
    m = re.search(r"(\d{6})", spec.get("id", ""))
    return int(m.group(1)) if m else 0


def check(spec):
    if _date(spec) < 261112 or spec.get("gate") is False:
        return []
    errs = []
    # 1. 자막 = 내레이션
    for i, sc in enumerate(spec.get("scenes", [])):
        if sc.get("type") == "cta":
            continue
        for ln in sc.get("lines", []) or []:
            say, cap = ln.get("say"), ln.get("cap")
            if say and cap and _norm(" ".join(cap)) != _norm(say):
                errs.append(f"장면 {i}: 자막이 내레이션과 다릅니다 — 요약하지 말고 말 그대로 ({' '.join(cap)[:30]} ↔ {say[:30]})")
    # 2. 사진·영상 중복
    seen = {}
    for i, sc in enumerate(spec.get("scenes", [])):
        if sc.get("type") == "cta":
            continue
        img = (sc.get("full") or {}).get("img") or sc.get("photo")
        if img:
            seen.setdefault(img, []).append(i)
    for img, idx in seen.items():
        if len(idx) > 1 and not img.startswith("owner_"):
            errs.append(f"같은 사진·영상을 {len(idx)}번 씁니다: {img} (장면 {idx})")
    # 2-1. 사진 칸(img·photo)에 영상 파일 → 렌더가 중간에 깨진다 (11/12 엔비디아 쇼츠). 영상은 full.video
    for i, sc in enumerate(spec.get("scenes", [])):
        for n in ((sc.get("full") or {}).get("img"), sc.get("photo")):
            if n and str(n).endswith(".mp4"):
                errs.append(f"장면 {i}: 사진 칸에 영상 {n} — full.video 로 넣고 img 는 사진으로")
    # 3. 제목 띠·제목
    banner = " ".join(spec.get("banner") or [])
    title = spec.get("title", "")
    for name, t in (("제목 띠", banner), ("제목", title)):
        if not t:
            continue
        if not re.search(r"\d", t):
            errs.append(f"{name}에 숫자가 없습니다: {t}")
        if name == "제목" and not re.search(r"[?!]|vs|→|되면|할까|일까|왜", t):   # 띠는 '사건 뒤 + 숫자'도 허용(r137②)
            errs.append(f"{name}에 궁금증(질문·대비)이 없습니다: {t}")
        for w in BAN_WORDS:
            if w in t:
                errs.append(f"{name}에 시청자가 모르는 분석 용어 '{w}': {t}")
    # 4. 윤석열 사진
    for i, sc in enumerate(spec.get("scenes", [])):
        for key in ("photo",):
            n = sc.get(key) or ""
            if n and YOON.search(n):
                errs.append(f"장면 {i}: 윤석열 사진 {n}")
        n = (sc.get("full") or {}).get("img") or ""
        if n and YOON.search(n):
            errs.append(f"장면 {i}: 윤석열 사진 {n}")
    return errs


def enforce(spec):
    errs = check(spec)
    if errs:
        raise SystemExit("렌더 전 점검 실패 (scripts/reels/gate.py) — " + " / ".join(errs))


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        e = check(json.load(open(p, encoding="utf-8")))
        print(p, "통과" if not e else "\n  ✗ " + "\n  ✗ ".join(e))
