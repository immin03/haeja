#!/usr/bin/env python3
"""양산형(유튜브 '진정성 없는 콘텐츠') 위험 검사 — 2026-11-15 대표 "양산형 채널로 비춰질 가능성 … 이 문제 안 되게 잘 점검해줘"

유튜브 기준: 템플릿으로 찍어내 영상마다 거의 바뀌지 않는 채널, 대량·반복 업로드는 수익 창출 불가.
우리 위험 요소(11/15 점검): AI 그림·목소리, 한 양식, 하루 3편, 같은 엔딩, 영어판이 한국 편 기반.
그래서 편마다 '눈에 보이게 다른' 것을 숫자로 지킨다. 규칙 원본: TEMPLATE.md '★ 양산형 방지'.

쓰는 법 (scripts/side/emperor 에서):
  python3 authentic_check.py fx_<id>.json [--src=<한국 편 id>] [--posts=posts.json]   # 한 편 출고 전 검사 (실패 1, 경고만 0)
  python3 authentic_check.py --all [--posts=posts.json]                                # 채널 전체 점검표 (주간 점검)
posts.json = ed_posts 에서 뽑은 [{id, kind, title, at, dur, from, fmt, value_add}] (없으면 제목·길이·편수 검사는 건너뜀)
"""
import collections, difflib, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = {c["id"] for c in json.load(open(os.path.join(HERE, "LIBRARY.json"), encoding="utf-8"))["items"]}

# 기준 (11/15)
SAME_CH_MAX = 0.40      # 같은 채널 최근 14편 중 어느 편과도 장면 겹침 40% 이하
EN_SRC_MAX = 0.50       # 영어판은 한국 원본과 장면 겹침 50% 이하 (두 채널이 같은 영상처럼 보이지 않게)
OPEN_DAYS_EPS = 9       # 첫 장면은 같은 채널 최근 9편(약 3일)의 첫 장면과 달라야 한다
TITLE_SIM_MAX = 0.80    # 같은 채널 제목과 글자 유사도 80% 미만
PER_DAY_MAX = 3         # 채널당 하루 쇼츠 3편 상한 (대표 11/15 권장안 1)
LEN_MIN_SPREAD = 8      # 최근 6편 길이의 최대-최소가 8초 이상 (전부 같은 길이 금지)
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


def load_posts(path):
    if not path or not os.path.exists(path):
        return []
    P = json.load(open(path, encoding="utf-8"))
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
        day = kst_day(post[me]["at"])
        n = sum(1 for p in posts if chan(p["id"], p.get("kind")) == ch and p.get("at") and kst_day(p["at"]) == day and not p.get("paused"))
        if n > PER_DAY_MAX:
            fails.append(f"{day} {ch} 쇼츠 {n}편 (상한 {PER_DAY_MAX})")
    # 6) 길이 다양성 (경고)
    lens = [post[k]["dur"] for k in recent[-5:] if k in post and post[k].get("dur")] + ([post[me]["dur"]] if me in post and post[me].get("dur") else [])
    if len(lens) >= 6 and max(lens) - min(lens) < LEN_MIN_SPREAD:
        warns.append(f"최근 6편 길이가 {min(lens):.0f}~{max(lens):.0f}초로 거의 같음 — 길이 회전을 넓힌다")
    # 7) 사람이 더한 가치 (경고)
    vals = [bool(post[k].get("value_add")) for k in recent[-(VALUE_EVERY - 1):] if k in post] + [bool((post.get(me) or {}).get("value_add"))]
    if len(vals) >= VALUE_EVERY and not any(vals):
        warns.append(f"최근 {VALUE_EVERY}편에 '사람이 더한 가치' 편이 없음 — 이 편을 가치 편으로 (TEMPLATE.md '★ 양산형 방지' 3)")
    return fails, warns


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
