"""밸류노트 공용 이미지 라이브러리 (2026-11-13 대표: "주식·경제에 공통으로 쓰이는 사진은 라이브러리에 저장해 두고 한 달에 효율적으로 쓰게 구조를 짜자")

하는 일
 1. build  : 지금까지 생성한 실사 이미지(il_*)를 생성 프롬프트와 함께 목록으로 만든다 → scripts/media/catalog.json
            · 그림체(수채·스케치·애니) 이미지는 r151 에 따라 '쓰지 않음'으로 표시
            · 가로(16:9)·세로(9:16) 구분, 처음 쓴 편, 최근 사용 편
 2. find   : 장면 설명(영어 단어 또는 한국어 주제어)으로 다시 쓸 만한 이미지를 찾는다
            · 최근 5편에 쓴 이미지는 뒤로 미룬다(반복 방지), 같은 편 안 중복은 render 점검이 막는다
 3. 새로 생성하기 전에 반드시 find 를 먼저 돌린다 (r164: 꼭 필요한 데만 생성)

사용
  python3 scripts/media/library.py build
  python3 scripts/media/library.py find "trading floor red screens" --vert
  python3 scripts/media/library.py find 연준 금리
"""
import glob, json, os, re, sys, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIB = os.path.join(ROOT, "scripts/blog/media/lib")
CAT = os.path.join(ROOT, "scripts/media/catalog.json")
ANIM = re.compile(r"watercolor|sketch|ink wash|illustration|hand-drawn|painting|pen and ink|cartoon|anime|miniature|diorama", re.I)
# 한국어 주제어 → 영어 검색어 (자주 쓰는 경제·투자 장면)
KO = {"연준": "federal reserve washington government building", "금리": "interest rate bond", "국채": "bond treasury",
      "주식": "trading floor stock monitors", "폭락": "red plunging crash", "급등": "green rising", "반도체": "chip semiconductor wafer",
      "데이터센터": "data center server", "AI": "ai data center server", "유가": "oil tanker", "중동": "oil tanker gulf desert",
      "금": "gold bar bullion", "금괴": "gold bar bullion vault", "중앙은행": "central bank vault", "환율": "banknotes currency won dollar",
      "원화": "korean won banknotes", "달러": "dollar banknotes", "엔화": "yen japanese", "중국": "shanghai china chinese", "일본": "tokyo japan japanese",
      "미국": "new york wall street washington", "월가": "wall street new york", "한국": "seoul korean", "서울": "seoul", "울산": "factory korean",
      "자동차": "car showroom factory", "공장": "factory assembly line", "스마트폰": "smartphone phone", "애플": "smartphone store",
      "실적": "report earnings analyst desk", "배당": "coins dividend", "자사주": "shares documents", "회의": "boardroom meeting room",
      "선거": "capitol election", "관세": "port containers trade", "무역": "port containers ship", "항구": "port containers cranes",
      "은행": "bank", "부동산": "apartment buildings city", "투자자": "investor desk monitors", "개미": "investor phone home desk"}
STOP = set("a an the of with and in on at to from for by into over under its their no not any is are as seen behind front".split())


def _prompts():
    out = {}
    for p in glob.glob(os.path.join(ROOT, "scripts/youtube/long/illust/*.json")):
        try: jobs = json.load(open(p, encoding="utf-8"))
        except Exception: continue
        for j in jobs if isinstance(jobs, list) else []:
            pr = (j.get("body") or {}).get("prompt", ""); ar = (j.get("body") or {}).get("aspect_ratio", "16:9")
            out[j.get("id")] = {"prompt": pr, "scene": pr.split("Scene:", 1)[-1].strip(), "ar": ar, "job": os.path.basename(p)}
    return out


def _usage():
    """편별 사용 기록: specs 안의 이미지 이름 → [편 id …] (날짜순)"""
    use = collections.defaultdict(list)
    files = glob.glob(os.path.join(ROOT, "scripts/youtube/long/specs/*.json")) + glob.glob(os.path.join(ROOT, "scripts/reels/specs/*.json"))
    for p in files:
        sid = os.path.basename(p)[:-5]
        try: s = open(p, encoding="utf-8").read()
        except Exception: continue
        for n in set(re.findall(r'"(il_[A-Za-z0-9_]+\.(?:jpe?g|png))"', s)): use[n].append(sid)
    for n in use: use[n].sort(key=lambda x: re.sub(r"\D", "", x)[:6])
    return use


def build():
    P = _prompts(); U = _usage(); cat = []
    for f in sorted(os.listdir(LIB)):
        if not f.startswith("il_") or not re.search(r"\.(jpe?g|png)$", f): continue
        meta = P.get(f.rsplit(".", 1)[0], {})
        pr = meta.get("prompt", "")
        cat.append({"file": f, "scene": meta.get("scene", "")[:400], "ar": meta.get("ar", "?"),
                    "ok": bool(pr) and not ANIM.search(pr), "used": U.get(f, [])})
    json.dump(cat, open(CAT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    ok = sum(1 for c in cat if c["ok"])
    print(f"라이브러리 {len(cat)}장 · 다시 쓸 수 있는 실사 {ok}장 · 그림체/설명 없음 {len(cat) - ok}장 → {CAT}")


def _words(t):
    return [w for w in re.findall(r"[a-z]+", t.lower()) if w not in STOP and len(w) > 2]


def find(q, vert=False, n=8, recent=None):
    cat = json.load(open(CAT, encoding="utf-8"))
    terms = []
    for w in q.split(): terms += _words(KO.get(w, w))
    terms = set(terms)
    # 최근 5편(롱폼 날짜 기준)
    eps = sorted({u for c in cat for u in c["used"]}, key=lambda x: re.sub(r"\D", "", x)[:6])
    recent = set(recent or eps[-5:])
    import math
    df = collections.Counter(w for c in cat for w in set(_words(c["scene"])))
    N = len(cat); idf = lambda w: math.log((N + 1) / (df.get(w, 0) + 1))
    res = []
    for c in cat:
        if not c["ok"]: continue
        if vert != (c["ar"] == "9:16"): continue
        sw = set(_words(c["scene"])); m = terms & sw
        if not m: continue
        hit = sum(idf(w) for w in m)
        pen = 3 if recent & set(c["used"]) else 0
        res.append((hit - pen - .1 * len(c["used"]), c))
    res.sort(key=lambda x: -x[0])
    for s, c in res[:n]:
        print(f"{s:5.1f}  {c['file']:45s} 사용 {len(c['used'])}회 {('(최근 사용)' if recent & set(c['used']) else ''):9s} {c['scene'][:90]}")
    if not res: print("맞는 이미지 없음 → 새로 생성")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "build": build()
    elif a[0] == "find": find(" ".join(x for x in a[1:] if not x.startswith("--")), vert="--vert" in a)
