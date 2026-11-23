#!/usr/bin/env python3
"""내용 중복 관문 — 2026-11-24 대표 "자꾸 한국 쇼츠가 동일한 게 뜬다, 내용도 반복된다 … 중복으로 보이는 일 해소하는 조치 모두"

11/24 점검에서 나온 것 (authentic_check.py 는 장면 클립만 봐서 못 막았다):
  - 같은 구절 반복: 9권 42절·11권 18절·4권 7절이 각 3번, ep37·ep43 은 6일 간격에 같은 구절·같은 조언
  - 둘째 문장 "2천 년 전 로마 황제가 명상록에 쓴 답입니다." 32편 고정, "황제는 이렇게 적었습니다" 11편+
  - 제목 틀 고정: 12:20 은 12편 연속 "~진짜 이유", 20:30 은 "4가지"
  - 표지: 14편 중 10편이 같은 황제 얼굴 클로즈업 → 피드에서 같은 영상처럼 보임

쓰는 법 (scripts/side/emperor 에서):
  python3 content_check.py long_<id>.json     # 한 편 출고 전 (실패 1, 통과 0) — fx 를 다 쓴 뒤, 녹음 전에 돌린다
  python3 content_check.py --all              # 채널별 최근 편 점검표
규칙 원본: TEMPLATE.md '★ 내용 중복 방지 (11/24)'.
"""
import difflib, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

VERSE_EPS = 60        # 같은 구절(권·절)은 같은 채널 앞 60편(하루 2편 ≈ 30일) 안에서 다시 쓰지 않는다
LINE_EPS = 10         # 내레이션 문장이 앞 10편 어느 편과 글자 그대로 같으면 실패 (연결 문장 고정 금지)
LINE_MIN_LEN = 8      #   공백 뺀 8글자 미만 짧은 말("첫째,")은 빼고 본다
ADVICE_EPS = 20       # 항목·조언 문장이 앞 20편과 75% 이상 비슷하면 실패 (같은 조언 재탕)
ADVICE_SIM = 0.75
TITLE_RUN = 1         # 제목 틀이 바로 앞 편과 같으면 실패
TITLE_WIN, TITLE_MAX = 6, 2   # 최근 6편(이번 편 포함) 안에서 같은 틀은 2편까지
FACE_RUN = 2          # 첫 장면(=표지 배경)이 황제 인물 중심인 편은 연속 2편까지
FACE_WIN, FACE_MAX = 6, 3     # 최근 6편(이번 편 포함) 안에서 황제 인물 중심 표지는 3편까지

TITLE_KINDS = [  # 위에서부터 먼저 맞는 것
    ("황제가 한 일", r"황제(가|는) .*(한 일|했|썼)|황제의 선택|황제가 한"),
    ("숫자 목록", r"(\d+|[한두세네다섯]+) ?가지|THREE|\b\d\b"),
    ("한 가지", r"한 가지|ONE THING"),
    ("진짜 이유", r"(진짜 |숨은 )?이유|WHY "),
    ("방법", r"방법|하는 법|이기는 법|HOW TO"),
    ("질문형", r"\?$"),
    ("상황형(When)", r"^WHEN |^IF "),
    ("사람형(People who)", r"PEOPLE WHO|THOSE WHO|^THEY "),
    ("명령형", r"^(STOP|DON'T|NEVER|LET|DO |BE )"),
]


def title_kind(t):
    t = (t or "").split("|")[0].strip()
    for k, rx in TITLE_KINDS:
        if re.search(rx, t, re.I):
            return k
    return "기타"


try:
    _CAT = {c["id"]: c for c in json.load(open(os.path.join(HERE, "LIBRARY.json"), encoding="utf-8"))["items"]}
except Exception:
    _CAT = {}
# '황제 인물 중심' 표지 = 장면 설명 첫 문장에 황제(수염 난 남자)가 나오고, 넓은 풍경·군중·사물·손 위주 장면이 아닌 것.
# 11/24 표지 14장 중 10장이 이 부류라 피드에서 같은 영상처럼 보였다.
WHO_RX = re.compile(r"emperor|marcus aurelius|bearded (roman )?man", re.I)
NOT_FACE_RX = re.compile(r"^(epic |extreme )?wide|aerial|vault|crowd of|army column|landscape|man's hand|hands? (holding|of)|maid|close-up of (a|an|the) (hand|scroll|cup|coin|letter|book|diary|candle)", re.I)


def is_face(clip):
    s = (_CAT.get(clip) or {}).get("scene") or ""
    head = re.split(r"(?<=[.:])\s", s, maxsplit=1)[0]
    return bool(WHO_RX.search(head) and not NOT_FACE_RX.search(head))


def chan(pid):
    return "EN" if re.match(r"en", pid) else "KR"


def load(path):
    d = json.load(open(path, encoding="utf-8"))
    pid = d.get("id") or os.path.basename(path)[5:-5]
    m = re.search(r"(2026-\d\d-\d\d)(?:\s+(\d\d:\d\d))?", d.get("note", ""))
    at = (m.group(1) + " " + (m.group(2) or "00:00")) if m else ""
    sents = [" ".join(s[5]) if isinstance(s[5], list) else str(s[5]) for s in d.get("sents", []) if len(s) > 5]
    big = [" ".join(s[5]) for s in d.get("sents", []) if len(s) > 5 and s[4] == "big" and isinstance(s[5], list)]
    verse = re.search(r"(\d+)\s*권\s*(\d+)\s*절|Meditations\s+(\d+)\.(\d+)", d.get("source", "") + " " + d.get("kicker", ""))
    v = (verse.group(1) or verse.group(3), verse.group(2) or verse.group(4)) if verse else None
    first = None
    fx = os.path.join(HERE, f"fx_{pid}.json")
    if os.path.exists(fx):
        try:
            first = json.load(open(fx, encoding="utf-8"))["shots"][0][0][0]
        except Exception:
            pass
    if not first and d.get("cuts"):
        first = os.path.splitext(os.path.basename(d["cuts"][0]))[0]
    return dict(id=pid, at=at, title=d.get("title_line", ""), sents=sents, big=big, verse=v, first=first,
                quote=" ".join((d.get("screen_quote") or {}).get("lines", [])))


def norm(s):
    return re.sub(r"[\s,.'\"“”‘’!?·…\-]", "", s).lower()


def all_eps():
    out = []
    for p in glob.glob(os.path.join(HERE, "long_*.json")):
        b = os.path.basename(p)[5:-5]
        if not re.fullmatch(r"(ep\d+|en\d+|enc\d+)", b):   # 'a'(녹음 맞춘 판)·b·x 같은 변형은 원본과 같은 편
            continue
        try:
            out.append(load(p))
        except Exception:
            pass
    return out


def history(me, eps):
    """같은 채널에서 이 편보다 앞선 편들(공개 시각 순, 시각 없으면 번호 순)"""
    ch = chan(me["id"])
    key = lambda e: (e["at"] or "0000", int(re.sub(r"\D", "", e["id"]) or 0))
    same = sorted([e for e in eps if chan(e["id"]) == ch and e["id"] != me["id"]], key=key)
    return [e for e in same if key(e) < key(me)]


def check(me, eps):
    fails = []
    prev = history(me, eps)
    # 1) 구절
    if me["verse"]:
        for e in prev[-VERSE_EPS:]:
            if e["verse"] == me["verse"]:
                fails.append(f"구절 {me['verse'][0]}권 {me['verse'][1]}절을 {e['id']}에서 이미 씀 (앞 {VERSE_EPS}편 안 재사용 금지) — 다른 구절로")
                break
    # 2) 문장 그대로 반복
    seen = {}
    for e in prev[-LINE_EPS:]:
        for s in e["sents"]:
            if len(norm(s)) >= LINE_MIN_LEN:
                seen.setdefault(norm(s), e["id"])
    for s in me["sents"]:
        if len(norm(s)) >= LINE_MIN_LEN and norm(s) in seen:
            fails.append(f"문장 「{s}」이(가) {seen[norm(s)]}와 그대로 같음 — 매 편 새 문장으로 (연결 문장 고정 금지)")
    # 3) 같은 조언 재탕
    pool = [(e["id"], x) for e in prev[-ADVICE_EPS:] for x in e["big"] + ([e["quote"]] if e["quote"] else [])]
    for x in me["big"] + ([me["quote"]] if me["quote"] else []):
        nx = norm(re.sub(r"^(첫째|둘째|셋째|넷째|다섯째|One|Two|Three|Four|Five)[,.]?", "", x))
        for pid, y in pool:
            ny = norm(re.sub(r"^(첫째|둘째|셋째|넷째|다섯째|One|Two|Three|Four|Five)[,.]?", "", y))
            th = ADVICE_SIM if re.search(r"[가-힣]", x) else 0.85   # 영어는 짧은 Never ~ 문장끼리 글자가 비슷해 기준을 높인다
            if len(nx) >= 8 and difflib.SequenceMatcher(None, nx, ny).ratio() >= th:
                fails.append(f"「{x}」이(가) {pid}의 「{y}」와 거의 같음 — 다른 조언·다른 각도로")
                break
    # 4) 제목 틀
    k = title_kind(me["title"])
    if prev and title_kind(prev[-1]["title"]) == k:
        fails.append(f"제목 틀 '{k}'이 바로 앞 편 {prev[-1]['id']}와 같음 — 이유/방법/한 가지/목록/황제가 한 일/질문형을 돌아가며")
    win = [title_kind(e["title"]) for e in prev[-(TITLE_WIN - 1):]] + [k]
    if win.count(k) > TITLE_MAX:
        fails.append(f"최근 {TITLE_WIN}편 중 제목 틀 '{k}'이 {win.count(k)}편 (상한 {TITLE_MAX})")
    # 5) 표지(첫 장면) 얼굴 클로즈업 쏠림
    if me["first"] and is_face(me["first"]):
        run = 0
        for e in reversed(prev):
            if e["first"] and is_face(e["first"]):
                run += 1
            else:
                break
        if run >= FACE_RUN:
            fails.append(f"첫 장면 {me['first']}이 황제 인물 중심 — 앞 {run}편 표지도 황제라 피드에서 같은 영상처럼 보임. 손·뒷모습·현장·사물·현대 장면으로")
        n = sum(1 for e in prev[-(FACE_WIN - 1):] if e["first"] and is_face(e["first"])) + 1
        if n > FACE_MAX:
            fails.append(f"최근 {FACE_WIN}편 중 황제 인물 중심 표지 {n}편 (상한 {FACE_MAX})")
    return fails


def main():
    eps = all_eps()
    byid = {e["id"]: e for e in eps}
    if "--all" in sys.argv:
        bad = 0
        for ch in ("KR", "EN"):
            seq = [e for e in eps if chan(e["id"]) == ch]
            seq.sort(key=lambda e: (e["at"] or "0000", int(re.sub(r"\D", "", e["id"]) or 0)))
            print(f"== {ch} 최근 {min(20, len(seq))}편")
            for e in seq[-20:]:
                f = check(e, eps)
                print(f"  {e['id']} [{title_kind(e['title'])}{' · 황제표지' if e['first'] and is_face(e['first']) else ''}] " + ("통과" if not f else f"✗ {len(f)}건: " + f[0]))
                bad += 1 if f else 0
        return 0
    rc = 0
    for a in [x for x in sys.argv[1:] if not x.startswith("--")]:
        e = load(a if os.path.exists(a) else os.path.join(HERE, a))
        if e["id"] in byid:
            eps = [x for x in eps if x["id"] != e["id"]]
        f = check(e, eps + [e])
        print(f"{e['id']}: " + ("내용 중복 관문 통과" if not f else "내용 중복 관문 실패"))
        for x in f:
            print("  ✗", x)
        rc |= 1 if f else 0
    return rc


if __name__ == "__main__":
    sys.exit(main())
