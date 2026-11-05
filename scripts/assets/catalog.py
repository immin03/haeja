"""밸류노트 그림·영상 돌려 쓰기 목록 (2026-11-05 대표: "템플릿을 계속 쌓아서 좋은 영상·사진을 반복 재활용, 적당히 돌아가면서")

쌓인 그림(scripts/blog/media/lib 의 il_* 일러스트, commons_* 실사)과 영상 대본(쇼츠·롱폼)에서 쓴 기록을 모아
"무엇이 있고, 언제 마지막으로 썼는지"를 scripts/assets/index.json 에 만든다.

사용:
  python3 scripts/assets/catalog.py build                 목록 다시 만들기
  python3 scripts/assets/catalog.py pick 데이터센터 반도체   주제어로 고르기 — 최근 7일 안에 쓴 것은 빼고 오래 안 쓴 순서
  python3 scripts/assets/catalog.py pick hbm --vertical    세로(9:16) 그림만
"""
import glob, json, os, re, sys, datetime as dt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIB = os.path.join(ROOT, "scripts", "blog", "media", "lib")
OUT = os.path.join(ROOT, "scripts", "assets", "index.json")
SPEC_DIRS = ["scripts/reels/specs/*.json", "scripts/youtube/long/specs/*.json"]
COOLDOWN_DAYS = 7

# 한국어 주제어 → 그림 설명(영문)에 나오는 말
KO = {"데이터센터": "data center", "반도체": "chip|wafer|semiconductor|fab", "서버": "server", "주식": "stock|trading|trader|chart",
      "증권": "trading|securities|dealing", "공장": "factory|fab|plant", "전력": "power|grid|electric", "미국": "washington|new york|america|us ",
      "새벽": "dawn", "밤": "night", "스마트폰": "smartphone|phone", "중국": "china|chinese", "여의도": "yeouido|seoul", "서울": "seoul",
      "돈": "money|cash|bill", "금": "gold", "커피": "coffee|cafe", "치킨": "chicken", "배달": "delivery", "공사": "construction|crane"}


def _when_from_id(sid):
    m = re.search(r"(\d{6})", sid or "")
    if not m: return None
    try: return dt.date(2000 + int(m.group(1)[:2]), int(m.group(1)[2:4]), int(m.group(1)[4:6]))
    except ValueError: return None


def build():
    items = {}
    for f in sorted(glob.glob(os.path.join(LIB, "*"))):
        name = os.path.basename(f)
        if not re.search(r"\.(jpe?g|png|mp4)$", name, re.I) or not name.startswith(("il_", "commons_")): continue
        it = {"file": name, "kind": "video" if name.endswith(".mp4") else "image", "desc": "", "vertical": None, "uses": [], "last": None}
        meta = os.path.join(LIB, re.sub(r"\.\w+$", ".json", name))
        if os.path.exists(meta):
            try:
                j = json.load(open(meta, encoding="utf-8")); b = j.get("body") or {}
                it["desc"] = (b.get("prompt") or "").split("Scene:")[-1].strip()[:240]
                it["vertical"] = b.get("aspect_ratio") == "9:16"
            except Exception: pass
        items[name] = it
    cred = os.path.join(LIB, "commons_credits.json")
    if os.path.exists(cred):
        for k, v in json.load(open(cred, encoding="utf-8")).items():
            if k in items: items[k]["desc"] = f"{v.get('q','')} · {v.get('title','')}"[:240]; items[k]["credit"] = f"{v.get('artist','')} · {v.get('license','')}"
    try:
        from PIL import Image
        for it in items.values():
            if it["kind"] == "image" and it["vertical"] is None:
                w, h = Image.open(os.path.join(LIB, it["file"])).size; it["vertical"] = h > w
    except Exception: pass
    for pat in SPEC_DIRS:
        for f in glob.glob(os.path.join(ROOT, pat)):
            txt = open(f, encoding="utf-8").read(); sid = os.path.basename(f)[:-5]
            try: when = (json.loads(txt).get("scheduled_at") or "")[:10]
            except Exception: when = ""
            day = when or (str(_when_from_id(sid)) if _when_from_id(sid) else "")
            for name in set(re.findall(r"((?:il|commons)_[\w\-]+\.(?:jpe?g|png|mp4))", txt)):
                if name in items:
                    items[name]["uses"].append(sid)
                    if day and (not items[name]["last"] or day > items[name]["last"]): items[name]["last"] = day
    json.dump({"built": dt.datetime.now().isoformat(timespec="minutes"), "cooldown_days": COOLDOWN_DAYS, "items": list(items.values())},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    n = len(items); used = sum(1 for i in items.values() if i["uses"])
    print(f"그림·영상 {n}개 (한 번이라도 쓴 것 {used}개) → {os.path.relpath(OUT, ROOT)}")


def pick(words, vertical=False, n=8):
    if not os.path.exists(OUT): build()
    data = json.load(open(OUT, encoding="utf-8")); today = dt.date.today()
    pats = [re.compile(KO.get(w, re.escape(w)), re.I) for w in words]
    blk = os.path.join(ROOT, "scripts", "assets", "blocked.json")
    blocked = json.load(open(blk, encoding="utf-8")) if os.path.exists(blk) else {}
    rows = []
    for it in data["items"]:
        hay = it["file"] + " " + it["desc"]
        score = sum(1 for p in pats if p.search(hay))
        if it["file"] in blocked: continue
        if not score or (vertical and not it["vertical"]): continue
        last = dt.date.fromisoformat(it["last"]) if it["last"] else None
        if last and (today - last).days < data.get("cooldown_days", COOLDOWN_DAYS): continue
        rows.append((-score, last or dt.date(2000, 1, 1), len(it["uses"]), it))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    for _, last, uses, it in rows[:n]:
        print(f"{it['file']:42s} {'세로' if it['vertical'] else '가로'}  마지막 {it['last'] or '안 씀'} · {uses}회  {it['desc'][:70]}")
    if not rows: print("맞는 그림이 없습니다 — 주제어를 바꾸거나, 정말 없으면 새로 1~3장만 만드세요.")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "build": build()
    elif a[0] == "pick": pick([w for w in a[1:] if not w.startswith("--")], vertical="--vertical" in a)
