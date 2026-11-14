"""황제의 일기 공용 이미지·영상 라이브러리 (2026-11-13 대표: "공용 이미지·영상 라이브러리 방식 — 화질·톤은 그대로, 유료 생성은 꼭 필요한 장면에만")
밸류노트 scripts/media/library.py(build/find)를 참고해 황제의 일기 전용으로 만든 것. 밸류노트 파일과는 무관하다.

하는 일
  build   지금까지 황제의 일기용으로 생성한 그림·영상(social/side/gen, 작업 목록 scripts/side/gen/ED*.json)을 전부 모아
          scripts/side/emperor/LIBRARY.json 하나로 만든다. 항목: 파일, 장면 설명(생성 프롬프트에서 뽑음 + CLIPS.json 한국어 설명),
          가로/세로, 그림/영상, 시대(로마/현대 한국/현대 서양), 쓴 편과 횟수, 다시 써도 되는지(ok).
          side-gen 워크플로가 ED 작업을 생성할 때마다 자동으로 다시 돈다.
  find    장면 설명(한국어 주제어 또는 영어 단어)으로 다시 쓸 만한 것을 찾는다. 최근 5편에 쓴 것은 뒤로 미룬다.
  check   한 편의 설정 파일(fx_<id>.json, spec_*.json …)을 보고 ① 한 편 안 중복 ② 최근 5편 사용을 알려 준다. 중복이 있으면 실패(종료 코드 1).
  gaps    기본 세트 주제별로 라이브러리에 몇 장 있는지 센다(부족한 주제 확인용).
  costs   생성 비용 기록(social/side/gen_costs.jsonl + 예전 생성 기록)을 달별로 합친다.

사용 (저장소 루트에서)
  python3 scripts/side/emperor/library.py build
  python3 scripts/side/emperor/library.py find 퇴근길 직장인 --vert --video
  python3 scripts/side/emperor/library.py find "candle desk night" --roman
  python3 scripts/side/emperor/library.py check scripts/side/emperor/fx_ep25.json
  python3 scripts/side/emperor/library.py gaps
  python3 scripts/side/emperor/library.py costs

규칙(TEMPLATE.md·LIBRARY.md 와 같이 지킴): 장면마다 find 먼저 → 맞는 게 없을 때만 생성. 한국어판·영어판은 같은 장면이면 같은 파일을 같이 쓴다.
"""
import collections, glob, json, math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GEN = "social/side/gen"
CAT = os.path.join(HERE, "LIBRARY.json")
LEDGER = os.path.join(ROOT, "social/side/gen_costs.jsonl")
ULOG = os.path.join(HERE, "library_usage.jsonl")   # 편마다 한 줄 {"at": 공개 날짜, "ep": 편, "ids": [...]} — check --record 가 쓴다. 최근 5편 판단 기준
JOBS = sorted(glob.glob(os.path.join(ROOT, "scripts/side/gen/ED*.json")))
USAGE = ["scripts/side/emperor/fx_*.json", "scripts/side/emperor/long_*.json", "scripts/side/ed_long/spec_*.json",
         "scripts/side/ed_long/en/spec_*.json", "scripts/side/ed_long/shorts/*.json"]
MEDIA = re.compile(r"\.(jpe?g|png|webp|mp4)$")

# 한국어 주제어 → 영어 검색어
KO = {"서재": "study desk villa scroll", "책상": "desk", "일기": "diary writing papyrus wax tablet", "촛불": "candle lamp flame night",
      "밤": "night moon dark", "새벽": "dawn sunrise early", "막사": "tent camp", "전쟁": "battle legion soldiers war", "전쟁터": "battlefield legion camp",
      "군대": "legion soldiers march", "로마": "rome roman forum", "거리": "street", "시장": "market crowd", "원로원": "senate senators curia",
      "황제": "emperor", "편지": "letter", "불": "fire", "비": "rain", "눈": "snow", "바다": "sea waves", "강": "river", "숲": "forest",
      "직장인": "office worker suit", "퇴근": "commute evening street subway", "퇴근길": "commute evening street subway walking", "출근": "commute morning",
      "사무실": "office desk", "회의": "meeting room", "상사": "boss", "동료": "colleagues", "지하철": "subway train", "버스": "bus",
      "혼자": "alone", "방": "room bedroom apartment", "집": "home apartment house", "가족": "family", "식탁": "dinner table kitchen family",
      "부엌": "kitchen", "엄마": "mother", "아버지": "father", "아빠": "father", "부모": "parents", "친구": "friends", "연인": "couple",
      "아이": "child", "노인": "elderly old", "병원": "hospital", "장례": "funeral", "휴대폰": "phone", "카페": "cafe", "공원": "park bench",
      "비웃음": "smirk whisper", "험담": "whisper gossip", "분노": "angry anger", "슬픔": "grief sad tears", "고독": "alone solitary",
      "창가": "window", "달": "moon", "별": "stars", "모래시계": "hourglass", "책": "book scroll"}
STOP = set("a an the of with and in on at to from for by into over under its their his her no not any is are as seen behind front "
           "very soft softly slowly slow one two small large while only just like still each".split())
STYLE_CUT = re.compile(r"\b(Camera |Cinematic|Painterly|painterly cinematic|Vertical 9:16|Absolutely no|Keep the painterly|Smooth, slow|Oil-painting|Style:)", re.I)
MODERN_KR = re.compile(r"seoul|korean|hangang|kakao|apartment complex", re.I)
MODERN = re.compile(r"modern|office|subway|smartphone|phone|laptop|car |cars|apartment|bus |cafe|hospital|elevator|present-day|suit|sweater|jeans", re.I)


def _git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True).stdout


def _gen_files():
    """social/side/gen 의 파일 목록 (일부만 받아 둔 저장소에서도 git 목록으로 전부 안다)"""
    fs = set(os.path.basename(x) for x in _git("ls-files", GEN).split())
    if os.path.isdir(os.path.join(ROOT, GEN)): fs |= set(os.listdir(os.path.join(ROOT, GEN)))
    return fs


def _read_many(paths):
    """저장소 파일 여러 개 읽기 — 받아 둔 건 디스크에서, 아니면 git 에서"""
    out, miss = {}, []
    for p in paths:
        fp = os.path.join(ROOT, p)
        if os.path.exists(fp):
            try: out[p] = open(fp, encoding="utf-8").read()
            except Exception: pass
        else: miss.append(p)
    if miss and os.environ.get("LIB_GIT"):   # 일부만 받은 저장소(blob 지연 받기)에서는 아주 느리다 → 기본은 디스크에 있는 것만
        r = subprocess.run(["git", "-C", ROOT, "cat-file", "--batch"], input="".join(f"HEAD:{p}\n" for p in miss).encode(), capture_output=True).stdout
        i = 0
        for p in miss:
            nl = r.index(b"\n", i); head = r[i:nl].split()
            if len(head) < 3 or head[1] != b"blob": i = nl + 1; continue
            n = int(head[2]); out[p] = r[nl + 1: nl + 1 + n].decode("utf-8", "replace"); i = nl + 1 + n + 1
    return out


def _price(j):
    """기록이 없을 때 쓰는 추정 단가 (gen.py PRICE 와 같음)"""
    if not j: return None
    if j.get("kind") == "image": return 0.06 * int(j.get("body", {}).get("num_images", 1))
    d = float(j.get("body", {}).get("duration", 5)); e = j.get("endpoint", "")
    for k, v in {"wan-3.0-prime": 0.051, "wan-3.0/": 0.10, "kling": 0.11, "seedance": 0.15, "grok": 0.08}.items():
        if k in e: return round(v * d, 3)
    return round(0.15 * d, 3)


def _scene(prompt):
    m = STYLE_CUT.search(prompt or "")
    s = (prompt[:m.start()] if m else prompt or "").strip()
    return re.sub(r"\s+", " ", s)[:420]


def _jobs():
    J = {}
    for f in JOBS:
        name = os.path.basename(f)[:-5]; day = re.search(r"(\d{6})", name)
        day = ("20" + day.group(1)[:2] + "-" + day.group(1)[2:4] + "-" + day.group(1)[4:6]) if day else ""
        try: jobs = json.load(open(f, encoding="utf-8"))
        except Exception: continue
        for j in jobs if isinstance(jobs, list) else []:
            if j.get("disabled"): continue
            J[j["id"]] = {**j, "_job": name, "_day": day}
    return J


def _usage(ids):
    """편별 사용 기록. 편 이름: 쇼츠 ep24·en05b, 롱폼 L-ep04·L-ep04_en, 롱폼 소개 쇼츠 L-ep04p. 순서는 그 파일의 마지막 커밋 시각"""
    files = sorted({os.path.relpath(p, ROOT) for g in USAGE for p in glob.glob(os.path.join(ROOT, g))})
    files = [f for f in files if not re.search(r"(caps|verses|plan)_", f)]
    texts = _read_many(files); use = collections.defaultdict(set); when = {}
    for f, s in texts.items():
        b = os.path.basename(f)[:-5]
        if "ed_long" in f: ep = "L-" + b.replace("spec_", "")
        else: ep = re.sub(r"^(fx|long)_", "", b); ep = re.sub(r"a$", "", ep) if re.match(r"(ep|en)\d+b?a$", ep) else ep
        for t in set(re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", s)) & ids: use[t].add(ep)
    if os.path.exists(ULOG):
        for l in open(ULOG, encoding="utf-8"):
            try: r = json.loads(l)
            except Exception: continue
            when[r["ep"]] = max(when.get(r["ep"], ""), r.get("at", ""))
            for t in r.get("ids", []):
                if t in ids: use[t].add(r["ep"])
    for e in {e for v in use.values() for e in v}: when.setdefault(e, "")
    return use, when


def build(quiet=False):
    J = _jobs(); files = _gen_files()
    stem = {}
    for f in files:
        if MEDIA.search(f): stem.setdefault(f.rsplit(".", 1)[0], []).append(f)
    clips = json.load(open(os.path.join(HERE, "CLIPS.json"), encoding="utf-8"))
    banned = set(re.findall(r"(libv_[a-z_]+)\(", clips.get("_note", "")))
    ko = {c["name"]: c for c in clips["clips"]}
    ids = set(J) | set(ko)
    use, when = _usage(set(stem))
    # 작업 목록에 없더라도 황제의 일기 편에 쓰인 파일은 라이브러리에 넣는다
    ids |= {i for i in use if i in stem}
    recs = _read_many([f"{GEN}/{i}.json" for i in ids if f"{i}.json" in files])
    order = sorted(when, key=lambda e: when[e]); rank = {e: n for n, e in enumerate(order)}
    cat = []
    for i in sorted(ids):
        if i not in stem: continue                     # 생성 실패·미완성
        f = sorted(stem[i], key=lambda x: x.endswith(".mp4"))[-1] if any(x.endswith(".mp4") for x in stem[i]) else stem[i][0]
        j = J.get(i, {}); rec = {}
        try: rec = json.loads(recs.get(f"{GEN}/{i}.json", "{}"))
        except Exception: pass
        body = j.get("body") or rec.get("body") or {}
        kind = "video" if f.endswith(".mp4") else "image"
        src = (j.get("image") or "").split("/")[-1].rsplit(".", 1)[0]
        sj = J.get(src, {}).get("body", {})
        ar = body.get("aspect_ratio") or sj.get("aspect_ratio") or ("16:9" if kind == "video" else "?")
        prompt = body.get("prompt", "")
        scene = _scene(sj.get("prompt", "")) + (" | 움직임: " + _scene(prompt)[:160] if src else "") if src else _scene(prompt)
        allp = prompt + " " + sj.get("prompt", "")
        era = ("modern_west" if i.startswith(("e4en", "e5en", "en")) or re.search(r"american|new york|london|western", allp, re.I) else "modern_kr" if MODERN_KR.search(allp)
               else "modern" if MODERN.search(allp) and not re.search(r"roman|emperor|legion|ancient|toga", allp, re.I) else "roman")
        k = ko.get(i, {})
        u = sorted(use.get(i, ()), key=lambda e: rank.get(e, -1))
        cat.append({"file": f, "id": i, "kind": kind, "ar": ar, "era": era, "src": src or None,
                    "scene": scene, "scene_ko": k.get("scene", ""), "use_ko": k.get("use", ""), "cx": k.get("cx"),
                    "ok": i not in banned and bool(scene or k), "made": j.get("_day", ""), "job": j.get("_job", ""),
                    "used": u, "n_used": len(u), "usd": rec.get("est_usd") or _price(j)})
    meta = {"_about": "황제의 일기 공용 그림·영상 라이브러리. library.py build 로 다시 만든다(손으로 고치지 않는다).",
            "_recent_eps": order[-5:], "_built": subprocess.run(["date", "+%F %T %Z"], capture_output=True, text=True).stdout.strip(),
            "items": cat}
    json.dump(meta, open(CAT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    if not quiet:
        ok = [c for c in cat if c["ok"]]
        print(f"라이브러리 {len(cat)}개 (그림 {sum(c['kind']=='image' for c in cat)} · 영상 {sum(c['kind']=='video' for c in cat)}) · "
              f"다시 쓸 수 있는 것 {len(ok)}개 · 한 번도 안 쓴 것 {sum(1 for c in ok if not c['used'])}개 → {os.path.relpath(CAT, ROOT)}")
    return meta


def _load():
    if not os.path.exists(CAT): return build(quiet=True)
    return json.load(open(CAT, encoding="utf-8"))


def _words(t):
    return [w for w in re.findall(r"[a-z]+", (t or "").lower()) if w not in STOP and len(w) > 2]


def find(q, vert=None, kind=None, era=None, n=10, exclude=(), show=True):
    m = _load(); cat = [c for c in m["items"] if c["ok"]]; recent = set(m.get("_recent_eps", []))
    terms, ko_terms = set(), set()
    for w in q.split():
        if re.search(r"[가-힣]", w): ko_terms.add(w)
        terms |= set(_words(KO.get(w, w)))
    df = collections.Counter(w for c in cat for w in set(_words(c["scene"])))
    N = len(cat); idf = lambda w: math.log((N + 1) / (df.get(w, 0) + 1)) + .2
    res = []
    for c in cat:
        if c["id"] in exclude: continue
        if kind and c["kind"] != kind: continue
        if era and not c["era"].startswith(era): continue
        if vert is True and c["ar"] not in ("9:16",) and not (c["kind"] == "video" and c.get("cx") is not None) and c["ar"] != "16:9": continue
        if vert is True and c["ar"] == "1:1": continue
        sw = set(_words(c["scene"])); hit = sum(idf(w) for w in terms & sw)
        hit += sum(2.0 for w in ko_terms if w in (c["scene_ko"] + c["use_ko"]))
        if hit <= 0: continue
        if vert is True and c["ar"] == "9:16": hit += .5          # 세로 원본이 세로 화면에 제일 깨끗하다
        if vert is True and c["ar"] == "16:9" and c["kind"] == "image": hit -= .3
        rec = bool(recent & set(c["used"]))
        res.append((hit - (3 if rec else 0) - .15 * c["n_used"], rec, c))
    res.sort(key=lambda x: -x[0])
    if show:
        for s, rec, c in res[:n]:
            tag = "(최근 5편)" if rec else ""
            print(f"{s:5.1f} {c['id']:24s} {c['kind'][:3]} {c['ar']:5s} {c['era']:11s} 사용{c['n_used']:2d} {tag:9s} {(c['scene_ko'] or c['scene'])[:80]}")
        if not res: print("맞는 것 없음 → 이 장면만 새로 생성 (생성 상한: TEMPLATE.md ★ 생성 상한)")
    return [c for _, _, c in res[:n]]


def check(path, record=False, ep=None, at=None):
    """한 편 설정 파일 점검: 한 편 안에서 같은 그림·영상 두 번 금지, 최근 5편 사용 경고"""
    m = _load(); ids = {c["id"]: c for c in m["items"]}; recent = set(m.get("_recent_eps", []))
    s = open(path, encoding="utf-8").read()
    toks = [t for t in re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", s) if t in ids]
    me = re.sub(r"^(fx|long|spec)_", "", os.path.basename(path)[:-5])
    # fx 는 같은 클립을 [이름, cx, 시작초…] 로 한 번씩 적는다 → 개수 = 쓴 횟수
    cnt = collections.Counter(toks); dup = {t: n for t, n in cnt.items() if n > 1}
    rec = sorted(t for t in cnt if (set(ids[t]["used"]) - {me, "L-" + me}) & recent)
    bad = sorted(t for t in cnt if not ids[t]["ok"])
    # 2026-11-14 대표 "그냥 명상록은 로마 배경만, 현대판만 현대 장면 — 왔다 갔다 섞지 말자" (한국·영어 모두)
    story = bool(re.match(r"(st|sw|px)\d", me)) or '"format": "story"' in s
    era_bad = sorted(t for t in cnt if (ids[t]["era"] != "roman") != story)
    if era_bad: print(f"  ✗ {'현대판에 로마 장면' if story else '일반 명상록에 현대 장면'}:", ", ".join(era_bad)); bad = bad + era_bad
    print(f"{path}: 그림·영상 {len(cnt)}개")
    if dup: print("  ✗ 한 편 안 중복:", ", ".join(f"{t}×{n}" for t, n in dup.items()))
    if bad: print("  ✗ 쓰지 않는 것:", ", ".join(bad))
    if rec: print("  ! 최근 5편에 쓴 것(바꿀 수 있으면 바꾸기):", ", ".join(rec))
    if not (dup or bad or rec): print("  통과")
    if record and not (dup or bad):
        import datetime
        at = at or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
        with open(ULOG, "a", encoding="utf-8") as fo: fo.write(json.dumps({"at": at, "ep": ep or me, "ids": sorted(cnt)}, ensure_ascii=False) + "\n")
        print(f"  사용 기록 남김: {ep or me} {at}")
    return 1 if (dup or bad) else 0


# 기본 세트 주제 (대표 11/13: 자주 나오는 장면은 한 번에 만들어 두고 계속 다시 쓴다)
THEMES = [("황제의 서재", "roman", r"study|desk|wax tablet|scroll|library|villa", r"."),
          ("밤의 촛불", "roman", r"candle|oil lamp|lamp", r"night|dark|evening"),
          ("전쟁터 막사", "roman", r"tent|camp|legion|battle", r"."),
          ("로마 거리", "roman", r"street|market|alley|forum|crowd", r"."),
          ("원로원", "roman", r"senat|curia", r"."),
          ("퇴근길 직장인 뒷모습", "modern", r"commut|subway|walking home|bus|street|crosswalk|platform", r"worker|office|suit|coat|man|woman"),
          ("밤의 사무실", "modern", r"office", r"night|late|dark|evening"),
          ("혼자 있는 방", "modern", r"room|bedroom|apartment|studio|living", r"alone|lone|by himself|by herself|single"),
          ("가족 식탁", "modern", r"dinner|table|meal|kitchen", r"family|mother|father|parents|children|daughter|son")]


def _theme(c, era, a, b):
    t = (c["scene"] + " " + c["scene_ko"]).lower()
    return c["era"].startswith(era) and re.search(a, t) and re.search(b, t)


def gaps():
    m = _load(); cat = [c for c in m["items"] if c["ok"]]
    print(f"{'주제':14s} 전체  그림(세로/가로) 영상  안 쓴 것")
    rows = []
    for name, era, a, b in THEMES:
        hit = [c for c in cat if _theme(c, era, a, b)]
        v = sum(c["kind"] == "image" and c["ar"] == "9:16" for c in hit); h = sum(c["kind"] == "image" and c["ar"] != "9:16" for c in hit)
        vid = sum(c["kind"] == "video" for c in hit); fresh = sum(not c["used"] for c in hit)
        rows.append({"theme": name, "all": len(hit), "img_v": v, "img_h": h, "video": vid, "fresh": fresh})
        print(f"{name:14s} {len(hit):4d}   {v:3d}/{h:3d}     {vid:4d}   {fresh:4d}")
    return rows


def costs(alert_usd=None):
    """달별 생성 비용(추정). 새 기록 = social/side/gen_costs.jsonl(실행마다 한 줄), 그 전 = 생성 기록(est_usd)"""
    by = collections.defaultdict(float); runs = collections.defaultdict(int)
    seen = set()
    if os.path.exists(LEDGER):
        for l in open(LEDGER, encoding="utf-8"):
            try: r = json.loads(l)
            except Exception: continue
            if r.get("channel") != "emperor": continue
            by[r["at"][:7]] += r.get("usd", 0); runs[r["at"][:7]] += 1; seen |= set(r.get("ids", []))
    for c in _load()["items"]:
        if c["id"] in seen or not c.get("usd") or not c["made"]: continue
        by[c["made"][:7]] += float(c["usd"])
    for k in sorted(by): print(f"{k}  {by[k]:7.2f}달러(추정)  실행 {runs.get(k, 0)}회")
    return dict(by)


if __name__ == "__main__":
    a = sys.argv[1:]
    flags = {x for x in a if x.startswith("--")}; args = [x for x in a[1:] if not x.startswith("--")]
    cmd = a[0] if a else "build"
    if cmd == "build": build()
    elif cmd == "find":
        find(" ".join(args), vert=True if "--vert" in flags else None, kind="video" if "--video" in flags else ("image" if "--image" in flags else None),
             era="modern" if "--modern" in flags else "roman")   # 2026-11-14 대표: 일반 명상록은 로마 장면만 → 기본은 roman, 현대판(이야기형)만 --modern
    elif cmd == "check":   # --record [--ep=<편>] [--at="YYYY-MM-DD HH:MM"] : 통과하면 사용 기록을 남긴다(최근 5편 판단에 쓰임)
        kv = dict(x[2:].split("=", 1) for x in flags if "=" in x)
        sys.exit(max([check(p, "--record" in flags, kv.get("ep"), kv.get("at")) for p in args] or [0]))
    elif cmd == "gaps": gaps()
    elif cmd == "costs": costs()
    else: print(__doc__)
