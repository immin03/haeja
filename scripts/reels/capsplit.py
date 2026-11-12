"""쇼츠 자막 끊기 (2026-11-12 대표: "전 문장하고 새로운 문장이 단어 단위로 끊겨 지저분하다 — 한 문장씩 깔끔하게")
규칙
 1. 문장(. ? !)을 넘어 한 줄에 섞지 않는다 — '11월 8일. 젠슨' 같은 줄 금지
 2. 쉼표에서 먼저 끊는다
 3. 그래도 길면(18자 초과) 어절 단위로, 줄 길이가 고르게 나뉘는 자리에서 끊는다 ('약', '새' 같은 한두 글자 꼬리 줄 금지)
사용: python3 scripts/reels/capsplit.py <spec.json>  → 모든 lines 의 cap 을 say 에서 다시 만든다
"""
import json, math, re, sys

MAX = 15   # 한 줄 자막 58px·폭 880px 에 들어가는 길이


def _balance(words, n):
    """어절 목록을 n 줄로, 가장 긴 줄이 가장 짧아지게 나눈다"""
    best = None
    def rec(i, k, acc):
        nonlocal best
        if k == 1:
            parts = acc + [" ".join(words[i:])]
            good = sum(1 for q in parts[:-1] if re.search(r"(고|며|는데|인데|서|면|지만|니|도|은|는)$", q))   # 말이 쉬는 자리에서 끊으면 가산
            score = (max(len(p) for p in parts) - 3 * good, -min(len(p) for p in parts))
            if best is None or score < best[0]: best = (score, parts)
            return
        for j in range(i + 1, len(words) - k + 2):
            rec(j, k - 1, acc + [" ".join(words[i:j])])
    rec(0, n, [])
    return best[1]


GLUE_NEXT = {"새", "넘게", "번째", "같은", "정도", "가량", "이상", "이하", "만에", "만", "뒤", "전", "후", "째"}
GLUE_PREV = {"약", "두", "세", "네", "한", "첫", "이", "그", "저", "몇", "단", "총", "각", "매"}


def _tokens(p):
    """끊으면 어색한 어절은 미리 붙인다: '8% 넘게' '하룻밤 새' '두 번째' '약 460조' '6시 20분' '11월 18일'"""
    w = p.split(); out = []
    for x in w:
        if out:
            prev = out[-1]; last = prev.split()[-1]
            if (x in GLUE_NEXT or last in GLUE_PREV or (len(x) == 1 and re.match(r"[가-힣]", x))
                    or (re.search(r"\d", last) and re.match(r"\d", x) and re.search(r"(시|월|년|일|분|억|조|만)$", last))):
                out[-1] = prev + " " + x; continue
        out.append(x)
    return out


def split_piece(p):
    p = p.strip()
    if len(p) <= MAX: return [p] if p else []
    w = _tokens(p)
    n = max(2, math.ceil(len(p) / 16))
    n = min(n, len(w))
    return _balance(w, n)


def split(say):
    out = []
    for sent in re.split(r"(?<=[.?!])(?!\d)\s*", say):
        sent = sent.strip()
        if not sent: continue
        if len(sent) <= MAX: out.append(sent); continue
        pieces = [x for x in re.split(r"(?<=,)\s+", sent)]
        # 쉼표 조각이 너무 짧으면(6자 미만) 다음 조각과 붙인다
        merged = []
        for x in pieces:
            if merged and len(merged[-1]) < 6: merged[-1] += " " + x   # '첫째,' 처럼 짧은 조각은 혼자 두지 않는다
            else: merged.append(x)
        for x in merged: out += split_piece(x)
    return out


def apply(spec):
    for sc in spec.get("scenes", []):
        if sc.get("type") == "cta": continue
        for ln in sc.get("lines", []) or []:
            if ln.get("say") and ln.get("cap") is not None:
                ln["cap"] = split(ln["say"])
    return spec


if __name__ == "__main__":
    for p in sys.argv[1:]:
        d = apply(json.load(open(p, encoding="utf-8")))
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        for sc in d["scenes"]:
            for ln in sc.get("lines", []) or []:
                if ln.get("cap"): print(" | ".join(ln["cap"]))
