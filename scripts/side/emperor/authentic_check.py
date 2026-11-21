#!/usr/bin/env python3
"""양산형(유튜브 '진정성 없는 콘텐츠') 위험 검사 — 2026-11-15 대표 "양산형 채널로 비춰질 가능성 … 이 문제 안 되게 잘 점검해줘"

유튜브 기준: 템플릿으로 찍어내 영상마다 거의 바뀌지 않는 채널, 대량·반복 업로드는 수익 창출 불가.
우리 위험 요소(11/15 점검): AI 그림·목소리, 한 양식, 하루 여러 편(11/21부터 2편), 같은 엔딩, 영어판이 한국 편 기반.
그래서 편마다 '눈에 보이게 다른' 것을 숫자로 지킨다. 규칙 원본: TEMPLATE.md '★ 양산형 방지'.

쓰는 법 (scripts/side/emperor 에서):
  python3 authentic_check.py fx_<id>.json [--src=<한국 편 id>] [--posts=posts.json]   # 한 편 출고 전 검사 (실패 1, 경고만 0)
  python3 authentic_check.py --all [--posts=posts.json]                                # 채널 전체 점검표 (주간 점검)
posts.json = ed_posts 에서 뽑은 [{id, kind, title, at, dur, from, fmt(images.format), value_add}] (없으면 제목·길이·편수 검사는 건너뜀)
"""
import collections, difflib, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_CAT = {c["id"]: c for c in json.load(open(os.path.join(HERE, "LIBRARY.json"), encoding="utf-8"))["items"]}
LIB = set(_CAT)
ULOG = os.path.join(HERE, "library_usage.jsonl")

# 기준 (11/15)
SAME_CH_MAX = 0.40      # 같은 채널 최근 14편 중 어느 편과도 장면 겹침 40% 이하
EN_SRC_MAX = 0.50       # 영어판은 한국 원본과 장면 겹침 50% 이하 (두 채널이 같은 영상처럼 보이지 않게)
OPEN_DAYS_EPS = 9       # 첫 장면은 같은 채널 최근 9편(약 3일)의 첫 장면과 달라야 한다
TITLE_SIM_MAX = 0.80    # 같은 채널 제목과 글자 유사도 80% 미만
PER_DAY_MAX = 2         # 채널당 하루 쇼츠 2편 상한 (현대판·롱폼 소개 쇼츠 포함) — 2026-11-21 대표 "2편으로 가자 한국도 2편으로" (이전 3편)
LEN_MIN_SPREAD = 8      # 최근 6편 길이의 최대-최소가 8초 이상 (전부 같은 길이 금지)
REUSE_DAYS = 7          # 2026-11-17 대표 "같은 장면 반복이 심하다": 같은 채널 최근 7일(예약분 포함)에 쓴 장면은
REUSE_MAX = 0.30        #   한 편의 30% 이하만 다시 쓴다. Higgsfield 체험분이 라이브러리에 들어오면(로마 800개 이상) 0.10으로 낮춘다
REUSE_FREE = 2          # 2026-11-18 대표 "한두 컷은 할 수 있겠지만": 다시 쓴 장면이 2개 이하면 비율과 상관없이 통과(6~7컷짜리 영어 편)
NIGHT_MAX = 0.50        # '밤 책상·촛불·일기' + '막사' 장면이 한 편의 50% 이하 (11/10~17 한국 쇼츠 33~67% — 다 어두운 밤이라 같은 영상처럼 보임)
NIGHT_RX = re.compile(r"candle|oil lamp|lamp|desk|diary|writing|quill|wax tablet|scroll|tent|camp", re.I)
# 2026-11-21 대표 "쇼츠가 계속 비슷한 포맷 … 다양성" → 포맷 5종 순환 (TEMPLATE.md '★ 포맷 순환')
FORMATS = {"quote": "인용형", "story": "현대판 이야기형", "history": "60초 실화형", "list": "빠른 목록형", "viewer": "시청자 사연형"}
FMT_SHARE_MAX = 0.40    # 같은 채널 최근 7일(예약분 포함) 중 한 포맷이 40% 이하
FMT_MIN_N = 5           #   비율 검사는 그 창에 포맷이 적힌 편이 5편 이상일 때만
FMT_SINCE = {"KR": "2026-11-22", "EN": "2026-11-30"}   # 이 날짜(공개일) 이후 편부터 적용 — 이미 예약된 편은 그대로 둔다
VALUE_EVERY = 3         # '사람이 더한 가치' 편은 3편에 1번 이상 (대표 11/15: 테스트로 몇 편에 한 번씩)


def chan(pid, kind=None):
    if kind:
        return "EN" if kind.endswith("_en") else "KR"
    return "EN" if re.match(r"(en|sw|px\d+en)", pid) and not pid.startswith("ep") else "KR"


def clips(path):
    s = open(path, encoding="utf-8").read()
    return [t for t in re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", s) if t in LIB]


def all_fx():
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, "fx_*.json"))):
        k = os.path.basename(p)[3:-5]
        c = clips(p)
        if c:
            out[k] = c
    return out


def jac(a, b):
    a, b = set(a), set(b)
    return len(a & b) / max(1, len(a | b))


PAUSED = set()


def load_posts(path):
    if not path or not os.path.exists(path):
        return []
    P = json.load(open(path, encoding="utf-8"))
    PAUSED.update(p["id"] for p in P if p.get("paused"))
    return sorted(P, key=lambda p: p.get("at") or "")


def order_of(posts, fx):
    """채널별 공개 순서. posts 가 있으면 공개 시각 순, 없으면 파일 이름 순."""
    if posts:
        seq = [p["id"] for p in posts if p["id"] in fx]
        return seq + [k for k in fx if k not in seq]
    return sorted(fx)


def check_one(me, fx, posts, src=None):
    fails, warns = [], []
    mine = fx.get(me)
    if not mine:
        return [f"{me}: fx 장면 목록을 못 읽음"], []
    post = {p["id"]: p for p in posts}
    kind = (post.get(me) or {}).get("kind")
    ch = chan(me, kind)
    seq = [k for k in order_of(posts, fx) if chan(k, (post.get(k) or {}).get("kind")) == ch and k != me]
    if me in order_of(posts, fx):
        i = order_of(posts, fx).index(me)
        seq = [k for k in order_of(posts, fx)[:i] if chan(k, (post.get(k) or {}).get("kind")) == ch]
    recent = seq[-14:]
    # 1) 같은 채널 장면 겹침
    worst = max(((k, jac(mine, fx[k])) for k in recent), key=lambda x: x[1], default=(None, 0))
    if worst[1] > SAME_CH_MAX:
        fails.append(f"같은 채널 {worst[0]} 와 장면 {worst[1]:.0%} 겹침 (상한 {SAME_CH_MAX:.0%}) — 장면을 바꾼다")
    # 2) 첫 장면
    opens = {fx[k][0]: k for k in recent[-OPEN_DAYS_EPS:]}
    if mine[0] in opens:
        fails.append(f"첫 장면 {mine[0]} 이(가) 최근 {opens[mine[0]]} 첫 장면과 같음 — 첫 3초는 매번 달라야 한다")
    # 3) 영어판 ↔ 한국 원본
    src = src or (post.get(me) or {}).get("from")
    if ch == "EN" and src:
        s = re.sub(r"(r\d*|x|b)$", "", src) if src not in fx else src
        if s in fx:
            ov = len(set(mine) & set(fx[s])) / max(1, len(set(mine)))
            if ov > EN_SRC_MAX:
                fails.append(f"한국 원본 {s} 와 장면 {ov:.0%} 같음 (상한 {EN_SRC_MAX:.0%}) — 영어판은 장면 절반 이상을 바꾼다")
    # 4) 제목
    if me in post and post[me].get("title"):
        t = post[me]["title"].split("|")[0].strip().lower()
        for p in posts:
            if p["id"] == me or chan(p["id"], p.get("kind")) != ch or not p.get("title"):
                continue
            r = difflib.SequenceMatcher(None, t, p["title"].split("|")[0].strip().lower()).ratio()
            if r >= TITLE_SIM_MAX:
                fails.append(f"제목이 {p['id']} 「{p['title']}」와 {r:.0%} 비슷함 — 바꾼다")
                break
    # 5) 하루 편수
    if me in post and post[me].get("at"):
        day = ch_day(post[me]["at"], ch)
        n = sum(1 for p in posts if chan(p["id"], p.get("kind")) == ch and p.get("at") and ch_day(p["at"], ch) == day and not p.get("paused"))
        if n > PER_DAY_MAX:
            fails.append(f"{day} {ch} 쇼츠 {n}편 (상한 {PER_DAY_MAX})")
    # 5-1) 7일 안 재사용 (11/17)
    at = (post.get(me) or {}).get("at")
    used = recent_used(ch, me, at)
    if mine and used:
        same = sorted(set(mine) & used)
        r = len(same) / max(1, len(set(mine)))
        if r > REUSE_MAX and len(same) > REUSE_FREE:
            fails.append(f"같은 채널 최근 {REUSE_DAYS}일에 쓴 장면이 {r:.0%} (상한 {REUSE_MAX:.0%}): {', '.join(same[:8])} — library.py find 로 안 쓴 장면을 고른다")
    # 5-2) 밤 장면 쏠림 (11/17)
    night = [t for t in set(mine) if NIGHT_RX.search(((_CAT.get(t) or {}).get("scene") or "") + " " + ((_CAT.get(t) or {}).get("scene_ko") or ""))]
    if len(set(mine)) >= 4 and len(night) / len(set(mine)) > NIGHT_MAX:
        fails.append(f"밤 책상·촛불·막사 장면이 {len(night)}/{len(set(mine))} (상한 {NIGHT_MAX:.0%}) — 낮의 로마(거리·원로원·전장·자연·가족)로 바꾼다")
    # 5-3) 포맷 순환 (11/21)
    fails += check_format(me, ch, post, posts)
    # 6) 길이 다양성 (경고)
    lens = [post[k]["dur"] for k in recent[-5:] if k in post and post[k].get("dur")] + ([post[me]["dur"]] if me in post and post[me].get("dur") else [])
    if len(lens) >= 6 and max(lens) - min(lens) < LEN_MIN_SPREAD:
        warns.append(f"최근 6편 길이가 {min(lens):.0f}~{max(lens):.0f}초로 거의 같음 — 길이 회전을 넓힌다")
    # 7) 사람이 더한 가치 (경고)
    vals = [bool(post[k].get("value_add")) for k in recent[-(VALUE_EVERY - 1):] if k in post] + [bool((post.get(me) or {}).get("value_add"))]
    if len(vals) >= VALUE_EVERY and not any(vals):
        warns.append(f"최근 {VALUE_EVERY}편에 '사람이 더한 가치' 편이 없음 — 이 편을 가치 편으로 (TEMPLATE.md '★ 양산형 방지' 3)")
    return fails, warns


def fmt_of(p):
    f = (p or {}).get("fmt")
    if f in FORMATS:
        return f
    if re.match(r"(st|sw|px)", (p or {}).get("id", "")):
        return "story"                   # 현대판 id 는 포맷을 안 적어도 story
    return f


def check_format(me, ch, post, posts):
    """2026-11-21: 같은 채널 바로 앞 편과 같은 포맷 금지, 최근 7일 한 포맷 40% 이하. FMT_SINCE 이전 편은 검사하지 않는다."""
    import datetime
    p = post.get(me) or {}
    at = p.get("at")
    if not at or ch_day(at, ch) < FMT_SINCE[ch]:
        return []
    f = fmt_of(p)
    if f not in FORMATS:
        return [f"포맷이 안 적혀 있음 — ed_posts.images.format 에 {'/'.join(FORMATS)} 중 하나 (TEMPLATE.md '★ 포맷 순환')"]
    out = []
    same = [q for q in posts if q["id"] != me and chan(q["id"], q.get("kind")) == ch and q.get("at") and not q.get("paused")]
    t = datetime.datetime.fromisoformat(str(at).replace("Z", "+00:00"))
    ts = lambda q: datetime.datetime.fromisoformat(str(q["at"]).replace("Z", "+00:00"))
    before = [q for q in same if ts(q) < t]
    after = [q for q in same if ts(q) > t]
    if before:
        prev = max(before, key=ts)
        if fmt_of(prev) == f:
            out.append(f"바로 앞 편 {prev['id']} 와 같은 포맷({FORMATS[f]}) — 이어서 같은 포맷 금지")
    if after:
        nxt = min(after, key=ts)
        if fmt_of(nxt) == f:
            out.append(f"바로 뒤 편 {nxt['id']} 와 같은 포맷({FORMATS[f]}) — 이어서 같은 포맷 금지")
    win = [q for q in same if abs((ts(q) - t).total_seconds()) <= REUSE_DAYS * 86400 and fmt_of(q) in FORMATS] + [p]
    if len(win) >= FMT_MIN_N:
        r = sum(1 for q in win if fmt_of(q) == f) / len(win)
        if r > FMT_SHARE_MAX:
            out.append(f"앞뒤 {REUSE_DAYS}일 {len(win)}편 중 {FORMATS[f]}이 {r:.0%} (상한 {FMT_SHARE_MAX:.0%}) — 다른 포맷으로")
    return out


def recent_used(ch, me, at):
    """같은 채널이 이 편 공개 시각 전 REUSE_DAYS 일 동안(그리고 아직 공개 전인 예약분) 쓴 장면 id"""
    import datetime
    if not os.path.exists(ULOG):
        return set()
    base = (datetime.datetime.fromisoformat(str(at).replace("Z", "+00:00")).astimezone(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
            if at else datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M"))
    lo = (datetime.datetime.strptime(base, "%Y-%m-%d %H:%M") - datetime.timedelta(days=REUSE_DAYS)).strftime("%Y-%m-%d %H:%M")
    hi = (datetime.datetime.strptime(base, "%Y-%m-%d %H:%M") + datetime.timedelta(days=REUSE_DAYS)).strftime("%Y-%m-%d %H:%M")
    out = set()
    for l in open(ULOG, encoding="utf-8"):
        try: r = json.loads(l)
        except Exception: continue
        if r.get("ep") == me or chan(r.get("ep", "")) != ch or not (lo <= r.get("at", "") <= hi):
            continue
        if r.get("ep") in PAUSED:      # 2026-11-18: 비공개(paused)로 돌린 편은 나가지 않으므로 세지 않는다
            continue
        out |= set(r.get("ids", []))
    return out


def ch_day(at, ch):
    """하루 편수 셈의 '하루' — 한국 채널은 한국 날짜, 영어 채널은 미국 동부 날짜(21:47·01:47·05:47·08:47 KST 가 같은 날).
    11/17: 영어를 한국 날짜로 세서 11/17(동부) 4편이 통과한 일 → 고침"""
    if ch != "EN":
        return kst_day(at)
    import datetime
    from zoneinfo import ZoneInfo
    d = datetime.datetime.fromisoformat(str(at).replace("Z", "+00:00"))
    return d.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")


def kst_day(at):
    import datetime
    d = datetime.datetime.fromisoformat(str(at).replace("Z", "+00:00"))
    return (d + datetime.timedelta(hours=9)).strftime("%Y-%m-%d")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    kv = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    posts = load_posts(kv.get("posts"))
    fx = all_fx()
    if "--all" in sys.argv:
        bad = 0
        for ch in ("KR", "EN"):
            ids = [k for k in order_of(posts, fx) if chan(k, ({p["id"]: p for p in posts}.get(k) or {}).get("kind")) == ch]
            print(f"== {ch} {len(ids)}편")
            for k in ids:
                f, w = check_one(k, fx, posts)
                if f or w:
                    print(f"  {k}: " + " / ".join(["✗ " + x for x in f] + ["! " + x for x in w]))
                bad += len(f)
        print(f"실패 {bad}건" if bad else "전체 통과")
        return 1 if bad else 0
    if "--gate" in sys.argv:
        # 2026-11-18 대표 "앞으로만 잘 올라가게": 업로드 직전 관문(yt_up.sh · en/qa_en.py 가 부른다). 재사용·밤 장면 두 가지만 본다.
        # 실패 1, 통과 0, 장면 목록이 없는 편(현대판 등) 0. --at=<공개 시각 ISO> 가 없으면 지금 시각 기준.
        rc = 0
        for a in args:
            me = os.path.basename(a)[3:-5] if os.path.basename(a).startswith("fx_") else a
            if me not in fx:
                print(f"{me}: 장면 목록 없음 — 관문 건너뜀"); continue
            p = [x for x in posts if x["id"] != me] + [{"id": me, "kind": "reel_en" if chan(me) == "EN" else "reel", "at": kv.get("at")}]
            f, _ = check_one(me, {me: fx[me]}, p)
            f = [x for x in f if "최근 7일" in x or "밤 책상" in x or f"최근 {REUSE_DAYS}일" in x]
            print(f"{me}: " + ("재사용 관문 통과" if not f else "재사용 관문 실패"))
            for x in f: print("  ✗", x)
            rc |= 1 if f else 0
        return rc
    rc = 0
    for a in args:
        me = os.path.basename(a)[3:-5] if os.path.basename(a).startswith("fx_") else a
        f, w = check_one(me, fx, posts, kv.get("src"))
        print(f"{me}: " + ("통과" if not f else "실패"))
        for x in f: print("  ✗", x)
        for x in w: print("  !", x)
        rc |= 1 if f else 0
    return rc


if __name__ == "__main__":
    sys.exit(main())
