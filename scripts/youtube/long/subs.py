"""롱폼 자막 파일(한국어·영어 .srt) 만들기 (2026-10-25 운영자: "자막이 또 없어졌네 관리자에? 한글 영문 각각 받을 수 있게")
사용: python3 scripts/youtube/long/subs.py <롱폼 아이디>
 - 문장 타이밍은 렌더 결과 meta.json 의 qa.lines [시작, 길이, 자막 문장, 읽은 문장] 을 쓴다
 - 영어는 원고 장면의 "en" (문장마다 하나, lines 와 같은 순서). 숫자 자리표({mcap} 등)는 영어 표기로 바꿔 채운다
 - 결과: social/youtube/<id>/subs_ko.srt · subs_en.srt, meta.json 의 subs·title_en·description_en
build.py 가 렌더 뒤에 자동으로 부른다.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def en_value(v):
    """'1.5조 달러' → '$1.5 trillion', '약 0.97달러' → 'about $0.97', '38.3배' → '38.3x', '10월 23일 종가' → 'the Oct 23 close'"""
    s = str(v)
    s = re.sub(r"약\s*", "about ", s)
    s = re.sub(r"([\d.,]+)\s*조\s*달러", r"$\1 trillion", s)
    s = re.sub(r"([\d.,]+)\s*억\s*달러", lambda m: f"${float(m[1].replace(',', '')) / 10:g} billion", s)
    s = re.sub(r"([\d.,]+)\s*달러", r"$\1", s)
    s = re.sub(r"([\d.,]+)\s*조\s*원", r"\1 trillion won", s)
    s = re.sub(r"([\d.,]+)\s*배", r"\1x", s)
    s = re.sub(r"([\d.,]+)\s*점", r"\1 points", s)
    s = re.sub(r"(\d+)월\s*(\d+)일\s*종가", lambda m: f"the {MON[int(m[1]) - 1][:3]} {m[2]} close", s)
    s = re.sub(r"(\d+)월\s*(\d+)일", lambda m: f"{MON[int(m[1]) - 1][:3]} {m[2]}", s)
    return s


def fill_en(t, V):
    return re.sub(r"\{(\w+)\}", lambda m: en_value(V.get(m[1], m[0])), t)


def chunks(text, limit):
    """긴 문장을 쉼표·마침표 기준으로 화면에 맞게 나눈다"""
    parts = [p.strip() for p in re.split(r"(?<=[.?!,])\s+", text) if p.strip()]
    out, cur = [], ""
    for p in parts:
        if cur and len(cur) + 1 + len(p) > limit: out.append(cur); cur = p
        else: cur = (cur + " " + p).strip()
    if cur: out.append(cur)
    res = []
    for c in out:   # 그래도 길면 띄어쓰기에서 자른다
        while len(c) > limit * 1.4:
            k = c.rfind(" ", 0, limit) or limit; res.append(c[:k].strip()); c = c[k:].strip()
        res.append(c)
    return res


def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def srt(items):
    return "\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n" for i, (a, b, t) in enumerate(items, 1))


def build(sid):
    d = os.path.join(ROOT, "social", "youtube", sid)
    mp = os.path.join(d, "meta.json"); meta = json.load(open(mp, encoding="utf-8"))
    sp = os.path.join(HERE, "specs", sid + ".json"); spec = json.load(open(sp, encoding="utf-8"))
    V = json.load(open(sp.replace(".json", ".data.json"), encoding="utf-8"))["vars"] if os.path.exists(sp.replace(".json", ".data.json")) else {}
    lines = meta.get("qa", {}).get("lines") or []
    en = [fill_en(e, V) for sc in spec["scenes"] for e in (sc.get("en") or [None] * len(sc["lines"]))]
    ko_items, en_items = [], []
    for k, (t0, dur, text, _say) in enumerate(lines):
        for lang, txt, lim, items in (("ko", text, 26, ko_items), ("en", en[k] if k < len(en) else None, 48, en_items)):
            if not txt: continue
            cs = chunks(txt, lim); tot = sum(len(c) for c in cs) or 1; a = t0
            for c in cs:
                b = a + dur * len(c) / tot; items.append((a, b, c)); a = b
    v = (meta.get("thumb") or "").split("?v=")[-1] or "0"
    subs = dict(meta.get("subs") or {})
    if ko_items: open(os.path.join(d, "subs_ko.srt"), "w", encoding="utf-8").write(srt(ko_items)); subs["ko"] = f"/social/youtube/{sid}/subs_ko.srt?v={v}"
    if en_items: open(os.path.join(d, "subs_en.srt"), "w", encoding="utf-8").write(srt(en_items)); subs["en"] = f"/social/youtube/{sid}/subs_en.srt?v={v}"
    meta["subs"] = subs
    if spec.get("title_en"): meta["title_en"] = fill_en(spec["title_en"], V)
    if spec.get("description_en"): meta["description_en"] = fill_en(spec["description_en"], V)
    json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"자막: {sid} 한국어 {len(ko_items)}줄 · 영어 {len(en_items)}줄 (영어 문장 {len(en)} / 음성 문장 {len(lines)})")
    return meta


if __name__ == "__main__":
    for a in sys.argv[1:]: build(a)
