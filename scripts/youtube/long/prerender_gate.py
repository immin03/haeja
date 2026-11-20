"""롱폼 렌더 전 자동 검수 관문 (2026-11-19 대표 18:07: "렌더 후 검수·시안보다, 렌더 전에 기획 단계 검수를 아주 촘촘하게 — 렌더는 웬만하면 한 번에")

사용:
  python3 scripts/youtube/long/prerender_gate.py <spec.json> [--report] [--json] [--no-db]
  --report : 결과를 DB에 남긴다 (기획 progress·prerender_gate, 실패면 alerts 'prerender-gate-<id>')  ← build.py 가 렌더 직전에 붙여 부른다
  --no-db  : 기획 확정 제목·썸네일을 DB에서 읽지 않는다 (⑦은 경고로만)
종료 코드 0 = 통과(경고는 있을 수 있음), 1 = 실패 → 렌더 시작 금지.

검사 항목 (원고·스펙 기준, 렌더 없이 몇 초 안에 끝난다):
  ① 사실·숫자·날짜 출처: 숫자가 처음 나오는 장면에 src(출처) 없음 → 실패 / 출처에 날짜 없음 → 경고
  ② 끝까지 보게 하는 구조(r119): 장면 note 표시 [훅]·[약속]·[R1..]·[가짜 결말]·[북엔드] + 문장 근거로
     첫 60초 안 훅·숫자·질문·약속(+예고), 리후킹 간격 3분 이하, 55~65% 부근 가짜 결말, 콜백 2번 이상, 북엔드 + 정체성 구독 문장
  ③ 원음 장면(r178·r179·r180): 클립 파일이 레포에 실제로 있음, 원음 뒤 한국어 더빙 문장 지정(자막만 금지), 이름표(lower) 지정·3초 이상,
     이슈 롱폼(u)은 원음 3개 이상, clip-queue 에 대기 중인(아직 도착 안 한) 클립 참조 금지
  ④ 화면 소스: 모든 장면에 화면 소스가 있고 파일이 존재(빈 배경 0), 플레이스홀더·임시 파일 0, 옛 노트 화면 0(overlay doc 편)
  ⑤ 코드 화면(r180): globe/cfg_<편>/<이름>.json 이 safe 배치(safe:false·shrink·top·zoom·cam 금지), 렌더러 기본값(코드 화면 고정·이름표 3초) 확인
  ⑥ 음악(r176·r181·r178): 인트로 곡 지정(기본 samples3/I3), 원음 구간 덕킹이 0(무음)이 아님(렌더러 -14~-22dB), 이슈 롱폼 본편에 자체 제작(own/) 곡 금지
  ⑦ 제목·썸네일: 기획 확정본(yt_plans title·thumb)과 같음, ab_sets 기본안 제목 = 스펙 제목
  ⑧ 길이·출력: 추정 길이 8:00 이상(말 속도 실측 초당 6.15음절), 최종 mp4 faststart 설정
  ⑨ 금지어(r183): 이틀·사흘·나흘·닷새·엿새·열흘·보름 같은 고유어 날짜(하루 제외), 길목·한복판·문턱·줄기·지나가는 길
  + render2.preflight (금지 인물·빈칸 글자·저작권 곡·반복 사진·애니메이션풍·원고 단어) 를 같이 돌린다
예외: 스펙 "gate_waive": {"⑥": "대표 11/20 09:10 '이번만 자체 곡' (원문)"} — 대표 원문·시각이 있는 항목만 경고로 내린다.
렌더 후 qa.py·sheet.py 는 확인용으로 그대로 둔다.
"""
import json, os, re, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LIB = os.path.join(ROOT, "scripts", "blog", "media", "lib")
RATE = 6.15          # 실측 초당 음절 (L261117e·L261118·L261119·L261119u, 11/19)
LINE_GAP = .35
INTRO_DEFAULT = "social/music/samples3/I3_full.mp3"   # r176: L261118 까지 쓰던 기존 외부 인트로 곡
OLD_TYPES = {"stat", "list", "compare", "bars", "table", "flow", "ledger", "scale", "receipt", "split"}   # 옛 노트 화면(도식) — doc 편에는 쓰지 않는다
PLACEHOLDER = re.compile(r"placeholder|dummy|todo|tmp_|_tmp|sample_img|test_|blank|빈화면", re.I)


def syl(s):
    return len(re.sub(r"[^가-힣0-9A-Za-z]", "", s))


def sb():
    cfg = open(os.path.join(ROOT, "config.js"), encoding="utf-8").read()
    return re.search(r"SUPABASE_URL:\s*'([^']+)'", cfg)[1], re.search(r"SUPABASE_ANON_KEY:\s*'([^']+)'", cfg)[1]


def rpc(name, body):
    u, k = sb()
    req = urllib.request.Request(u + "/rest/v1/rpc/" + name, data=json.dumps(body).encode(), method="POST",
                                 headers={"apikey": k, "Authorization": "Bearer " + k, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read() or b"null")


def lib_exists(n):
    if not n: return False
    if os.path.exists(os.path.join(LIB, n)): return True
    if n.startswith("social/") and os.path.exists(os.path.join(ROOT, n)): return True
    return False


def timeline(spec):
    """장면별 (시작, 길이) 추정 — 렌더러와 같은 규칙(문장 + 0.35초, 원음 orig, 말 없는 인트로 2.6초)"""
    t = 0.0; out = []
    for sc in spec["scenes"]:
        lines = [l[1:] if l.startswith("?") else l for l in sc.get("lines", [])]
        d = sum(syl(l) / RATE + LINE_GAP for l in lines)
        if sc.get("sot"): d = max(d, float(sc["sot"].get("dur", 0)) + .3)
        if sc.get("dub"): d += float(sc["dub"].get("orig", 2.5)) + .15
        if not lines and (sc.get("v") or {}).get("ident"): d = float(sc.get("dur", 2.6))
        out.append((t, d)); t += d
    return out, t


def check(spec, spec_path, use_db=True):
    F, Wn = [], []   # 실패, 경고
    def fail(k, m): F.append(f"{k} {m}")
    def warn(k, m): Wn.append(f"{k} {m}")
    sid = spec.get("id", os.path.basename(spec_path).replace(".json", ""))
    scenes = spec.get("scenes", [])
    tl, total = timeline(spec)
    end_sec = next((float(sc.get("endscreen", 0)) for sc in scenes if (sc.get("v") or {}).get("type") == "end"), 0)
    issue = bool(re.match(r"L\d{6}u", sid)) or "이슈" in json.dumps(spec.get("plan_type", ""), ensure_ascii=False)
    doc = spec.get("overlay") == "doc" or spec.get("design") == "v2"

    # ① 출처
    seen = set()
    for i, sc in enumerate(scenes):
        if (sc.get("v") or {}).get("type") == "end" or (sc.get("v") or {}).get("ident"): continue
        txt = " ".join(re.sub(r"\{[^}]*\}", "", l) for l in sc.get("lines", []))
        nums = {n for n in re.findall(r"\d[\d,.]*", txt) if len(n.replace(",", "").replace(".", "")) >= 1}
        src = str(sc.get("src", "") or (sc.get("v") or {}).get("src", "")).strip()
        if src:
            seen |= nums
            if nums and not re.search(r"(19|20)\d\d|\d{1,2}월|\d{1,2}[./-]\d{1,2}", src): warn("①", f"장면 {i}: 출처에 날짜 없음 — {src[:40]}")
            continue
        new = sorted(n for n in nums if n not in seen and len(re.sub(r"\D", "", n)) >= 2)   # 한 자리 수(1주·3명·첫째)는 제외
        if new: fail("①", f"장면 {i}: 숫자 {', '.join(new[:4])} 출처(src) 없음 — {txt[:40]}")

    # ② 구조 (r119)
    notes = [str(sc.get("note", "")) for sc in scenes]
    alltxt = [" ".join(sc.get("lines", [])) for sc in scenes]
    def at(i): return tl[i][0]
    first60 = [i for i in range(len(scenes)) if at(i) < 60]
    t60 = " ".join(alltxt[i] for i in first60)
    if not any("[훅" in notes[i] for i in first60): warn("②", "첫 60초 장면에 [훅] 표시 없음")
    if not re.search(r"\d", t60): fail("②", "첫 60초에 숫자 없음")
    if "?" not in t60: fail("②", "첫 60초에 질문 없음")
    prom = [i for i in range(len(scenes)) if "[약속" in notes[i]]
    early = any(re.search(r"약속|예고", notes[i]) for i in first60) or re.search(r"이 영상|끝날 때|마지막(엔|에는|에)|끝까지|알게 됩니다|보여 드리|짚어 보", t60)
    if not early:
        if prom and at(prom[0]) <= 120: warn("②", f"[약속]이 {at(prom[0]):.0f}초 — r119 는 35~60초")
        else: fail("②", "첫 60초에 약속(이 영상이 끝날 때쯤…)·예고 없음")
    rr = sorted(at(i) for i in range(len(scenes)) if re.search(r"\[R\d|\[리훅|\[리후킹", notes[i]))
    qs = sorted(at(i) for i in range(len(scenes)) if re.search(r"\?|까요|일까", alltxt[i]))
    marks = sorted(set(rr + [x for x in qs]))
    body_end = total - end_sec - 30
    pts = [60.0] + [x for x in marks if 60 <= x <= body_end] + [body_end]
    gaps = [(b - a, a) for a, b in zip(pts, pts[1:])]
    big = [g for g in gaps if g[0] > 180]
    for g, a in big: fail("②", f"{a / 60:.1f}분부터 {g / 60:.1f}분 동안 리후킹·질문 없음 (2~3분마다)")
    if len(rr) < 2: warn("②", f"[R] 리후킹 표시 {len(rr)}개 — 대본에 [R1]~ 표시")
    fe = [i for i in range(len(scenes)) if "가짜 결말" in notes[i] or re.search(r"이걸로 끝일까|정답일까요|아직 아닙니다|아직 남았습니다|끝이 아닙니다|여기서 끝이 아닙", alltxt[i])]
    if not fe: fail("②", "가짜 결말 없음 (전체의 55~65%)")
    elif not any(.45 <= at(i) / max(1, total) <= .75 for i in fe): warn("②", f"가짜 결말 위치 {at(fe[0]) / total:.0%} — 55~65% 권장")
    cb = sum(1 for i in range(len(scenes)) if "콜백" in notes[i] or re.search(r"아까|앞에서 (본|말씀|보신)|기억하시죠|기억나시|처음에 (본|말씀)|맨 처음", alltxt[i]))
    if cb < 2: fail("②", f"콜백 {cb}번 — 최소 2번")
    tail = [i for i in range(len(scenes)) if at(i) >= total * .85]
    if not any("[북엔드" in notes[i] for i in tail) and not any(re.search(r"처음|첫 장면|다시 그", alltxt[i]) for i in tail): fail("②", "북엔드(첫 장면으로 돌아가 닫기) 없음")
    endtxt = " ".join(alltxt[i] for i in tail)
    if "구독" not in endtxt and not any((sc.get("v") or {}).get("type") == "end" for sc in scenes): fail("②", "엔딩 구독 문장·끝 화면 없음")

    # ③ 원음
    queue_wait = set()
    try:
        q = json.load(open(os.path.join(ROOT, "media", "clip-queue.json"), encoding="utf-8"))
        queue_wait = {c["name"] for c in q.get("clips", []) if not any(f.startswith(c["name"] + ".") for f in os.listdir(LIB))}
    except Exception: pass
    n_orig = 0
    for i, sc in enumerate(scenes):
        sot, dub = sc.get("sot"), sc.get("dub")
        for c in ((sc.get("v") or {}).get("cuts") or []):
            n = c.get("lib") if isinstance(c, dict) else c
            if n and n.rsplit(".", 1)[0] in queue_wait: fail("③", f"장면 {i}: 아직 도착하지 않은 원음 클립 {n} (media/clip-queue.json 대기)")
        if not (sot or (dub and dub.get("clip"))): continue
        n_orig += 1; clip = (sot or dub).get("clip")
        if not lib_exists(clip): fail("③", f"장면 {i}: 원음 클립 파일 없음 {clip} — 원음 확보 후 렌더 (CLIPS.md)")
        # 2026-11-21 대표: 더빙 없이 원음+자막 테스트(r205) — spec.orig_mode=="sot_test"면 sot만 허용, 원음은 넉넉하게
        if sot and not dub and spec.get("orig_mode") != "sot_test": fail("③", f"장면 {i}: 원음 뒤 한국어 더빙 지정 없음(sot만 — r179 자막만 금지)")
        if sot and not sc.get("lines"): fail("③", f"장면 {i}: 원음 자막(번역 문장) 없음")
        if sot and not (4.0 <= float(sot.get("dur", 0)) <= 45.0): fail("③", f"장면 {i}: 원음 길이 {sot.get('dur')}초 — 4~45초")
        if dub and not (dub.get("voice") and sc.get("lines")): fail("③", f"장면 {i}: 더빙 목소리·문장 지정 없음")
        if not any(b.get("kind") == "lower" and b.get("text") for b in (sc.get("sketch") or [])): fail("③", f"장면 {i}: 원음 이름표(lower) 없음")
        if tl[i][1] < 3.0: fail("③", f"장면 {i}: 원음 장면 {tl[i][1]:.1f}초 — 이름표 3초 이상 보이게")
        if not str(sc.get("src", "")).strip(): fail("③", f"장면 {i}: 원음 출처(방송사·날짜) 없음")
    if issue and n_orig < 3: fail("③", f"이슈 롱폼 원음 {n_orig}개 — 3개 이상 (r178)")

    # ④ 화면 소스
    for i, sc in enumerate(scenes):
        v = sc.get("v") or {}; typ = v.get("type")
        if typ == "end": continue
        if doc and typ in OLD_TYPES and not v.get("backdrop"): fail("④", f"장면 {i}: 옛 노트 화면({typ}) — doc 편은 사진·영상 + 다큐 그래픽")
        srcs = [c.get("lib") if isinstance(c, dict) else c for c in (v.get("cuts") or [])] + ([v["lib"]] if v.get("lib") else []) + ([v["backdrop"]] if isinstance(v.get("backdrop"), str) else [])
        if typ == "media" and not srcs: fail("④", f"장면 {i}: 화면 소스 없음(빈 배경)")
        for n in srcs:
            if not n: fail("④", f"장면 {i}: 빈 컷")
            elif PLACEHOLDER.search(n): fail("④", f"장면 {i}: 플레이스홀더·임시 파일 {n}")
            elif not lib_exists(n) and not n.startswith("capture:") and not n.endswith("_wide.jpg"):
                fail("④", f"장면 {i}: 화면 파일 없음 {n}")

    # ⑤ 코드 화면 (r180)
    gdir = os.path.join(HERE, "globe"); pre = sid.split("-")[0]
    cfgdirs = sorted([os.path.join(gdir, d) for d in os.listdir(gdir) if d.startswith("cfg_")], key=lambda d: (not os.path.basename(d)[4:].startswith(pre[:7]), d))
    for i, sc in enumerate(scenes):
        for c in ((sc.get("v") or {}).get("cuts") or []):
            n = c.get("lib") if isinstance(c, dict) else c
            if isinstance(c, dict) and any(k in c for k in ("zoom", "kenburns", "cam")) and re.search(r"(^|/)(globe_|app_|puzzle_)|_fx_", n or ""):
                fail("⑤", f"장면 {i}: 코드 화면 {n}에 확대·카메라 효과 지정")
            m = re.match(r"globe_[^_]+_fx_(.+)\.mp4$", n or "")
            if not m: continue
            nm = m.group(1); cfgid = n.split("_")[1]
            cands = [os.path.join(d, x + ".json") for d in sorted(cfgdirs, key=lambda d: not os.path.basename(d)[4:] == cfgid) for x in (nm, nm.replace("goldscale", "gold_scale"))]
            cp = next((p for p in cands if os.path.exists(p)), None)
            if not cp: warn("⑤", f"장면 {i}: 코드 화면 설정 파일 못 찾음 ({nm}) — 레이아웃 확인 불가"); continue
            try: cfg = (json.load(open(cp, encoding="utf-8")) or {}).get("cfg", {})
            except Exception as e: fail("⑤", f"{os.path.basename(cp)} 읽기 실패 {e}"); continue
            if cfg.get("safe") is False: fail("⑤", f"{nm}: safe:false (r180 이전 배치)")
            for k in ("shrink", "top", "zoom", "cam"):
                if k in cfg: fail("⑤", f"{nm}: '{k}' 지정 — r180 안전 배치(safeDraw)와 충돌")
    r2 = open(os.path.join(HERE, "render2.py"), encoding="utf-8").read()
    m = re.search(r"R180_TAG_MIN\s*=\s*([\d.]+)", r2)
    if not m or float(m.group(1)) < 3: fail("⑤", "렌더러 이름표 최소 시간(R180_TAG_MIN) 3초 미만")
    if "fixed = is_code_screen(pth)" not in r2: fail("⑤", "렌더러 코드 화면 고정(is_code_screen) 빠짐")

    # ⑥ 음악
    mus = spec.get("music") or {}
    if not mus.get("intro"): fail("⑥", "인트로 곡 미지정 (r176 기본 " + INTRO_DEFAULT + ")")
    elif mus["intro"] != INTRO_DEFAULT and not mus.get("intro_by_owner"): fail("⑥", f"인트로 곡 {mus['intro']} — r176 기존 곡({INTRO_DEFAULT}). 대표 지정이면 music.intro_by_owner 에 원문")
    if not lib_exists(mus.get("intro", INTRO_DEFAULT)): fail("⑥", f"인트로 곡 파일 없음 {mus.get('intro')}")
    beds = mus.get("bed") or []; beds = [beds] if isinstance(beds, str) else beds
    for b in beds:
        p = b.split("@")[0]
        if not lib_exists(p): fail("⑥", f"본편 곡 파일 없음 {p}")
        if "/own/" in p: (fail if issue else warn)("⑥", f"본편 곡이 자체 제작 {p} (r178: 예전에 써서 문제 없던 다큐·미스터리 곡)")
    for k in ("sot_duck_db", "duck_db"):
        if k in mus and float(mus[k]) <= -40: fail("⑥", f"music.{k}={mus[k]} — 원음 구간 음악이 사실상 0 (r181)")
    if mus.get("mute_on_sot") or mus.get("sot_mute"): fail("⑥", "원음 구간 음악 끄기 지정 (r181 금지)")
    m = re.search(r"tgt = float\(10 \*\* \((-?\d+) / 20\)\)", r2)
    if not m or not (-22 <= int(m.group(1)) <= -14): fail("⑥", "렌더러 원음 구간 덕킹 목표가 -14~-22dB 가 아님 (r181)")

    # ⑦ 제목·썸네일
    title = (spec.get("title") or "").strip()
    ab = spec.get("ab_sets") or []
    dflt = next((a for a in ab if a.get("default")), ab[0] if ab else None)
    if dflt and (dflt.get("title") or "").strip() and dflt["title"].strip() != title: fail("⑦", f"썸네일 기본안 제목과 스펙 제목이 다름")
    plan = None
    if use_db and spec.get("plan"):
        try: plan = rpc("prerender_plan", {"p_id": spec["plan"]})
        except Exception as e: warn("⑦", f"기획 확정본을 읽지 못함 ({str(e)[:60]})")
    if plan:
        norm = lambda s: re.sub(r"\s+", " ", str(s or "")).strip()
        if plan.get("title") and norm(plan["title"]) != norm(title): fail("⑦", f"제목이 기획 확정본과 다름 — 기획: {norm(plan['title'])[:50]} / 스펙: {title[:50]}")
        pt, st = plan.get("thumb") or {}, spec.get("thumb") or {}
        for k in ("l1", "l2"):
            if pt.get(k) and st.get(k) and norm(pt[k]) != norm(st[k]): fail("⑦", f"썸네일 {k} 가 기획 확정본과 다름 — 기획: {pt[k]} / 스펙: {st[k]}")
    elif spec.get("plan") and use_db: warn("⑦", "기획을 찾지 못해 제목·썸네일 대조 못 함")
    elif not spec.get("plan"): warn("⑦", "스펙에 plan(기획 id) 없음 — 제목·썸네일 대조 못 함")

    # ⑨ 금지어 (r183 대표 11/19 19:10 "다음 롱폼부터 무조건"): 고유어 날짜 수사(하루 제외)·AI 상투어 — 하나라도 있으면 렌더 금지
    ban = re.compile(r"이틀|사흘|나흘|닷새|엿새|여드레|아흐레|열흘|보름|길목|한복판|문턱|줄기|지나가는 길")
    texts = [("제목", spec.get("title", "")), ("설명", spec.get("description_head", "")), ("고정 댓글", spec.get("pinned_comment", ""))]
    texts += [(f"썸네일 {k}", str((spec.get("thumb") or {}).get(k, ""))) for k in ("l1", "l2", "l3")]
    texts += [(f"썸네일 {a_.get('key')}안", " ".join(str(a_.get(k, "")) for k in ("title", "l1", "l2", "l3"))) for a_ in ab]
    for i, sc in enumerate(scenes):
        texts += [(f"장면 {i}", l) for l in sc.get("lines", [])] + [(f"장면 {i} 출처", str(sc.get("src", "")))]
        texts += [(f"장면 {i} 화면", str(b.get(k, ""))) for b in (sc.get("sketch") or []) for k in ("text", "sub", "title")]
    # 2026-11-20 12:22 대표 "중대한, 그 무게는 엉뚱한 데 떨어졌습니다 — 이런 표현 진짜 하지 말자. 추상적이고 뭔 소리인지 모르겠다"
    ban2 = re.compile(r"무게는|무게가 실|엉뚱한 (곳|데)|신호탄|축포")
    for where, tx in texts:
        for m_ in ban.finditer(tx or ""): fail("⑨", f"{where}: 금지어 '{m_.group(0)}' — {tx[max(0, m_.start() - 12):m_.end() + 12]}")
        for m_ in ban2.finditer(tx or ""): fail("⑨", f"{where}: 추상 비유 금지(r185) '{m_.group(0)}' — {tx[max(0, m_.start() - 12):m_.end() + 12]}")
        for m_ in re.finditer(r"(다섯|여섯|일곱|여덟|아홉|스무|서른|마흔|쉰|예순|일흔|여든|아흔) ?(곳|번|차례|명|개|해|살|년|달)", tx or ""):
            warn("⑨", f"{where}: 고유어 수 '{m_.group(0)}' — 아라비아 숫자 권장(r84·r183)")

    # ⑧ 길이·출력
    body = total
    if body < 480: fail("⑧", f"추정 길이 {int(body // 60)}:{int(body % 60):02d} — 8:00 이상 (이야기 장면 추가)")
    if "+faststart" not in r2.split("def finish", 1)[-1][:1500]: fail("⑧", "최종 mp4 faststart 설정 없음")

    # render2.preflight
    try:
        sys.path.insert(0, HERE); import render2
        render2.preflight(json.loads(json.dumps(spec)))
    except SystemExit as e: fail("⓪", str(e)[:400])
    except Exception as e: warn("⓪", f"preflight 실행 못 함 ({type(e).__name__}: {str(e)[:80]})")

    # 대표 예외
    waive = spec.get("gate_waive") or {}
    if waive:
        keep = []
        for f in F:
            k = f.split(" ", 1)[0]
            if k in waive and re.search(r"\d{1,2}[:/]\d{2}", str(waive[k])): Wn.append("(대표 예외) " + f)
            else: keep.append(f)
        F = keep
    return {"id": sid, "plan": spec.get("plan"), "ok": not F, "fail": F, "warn": Wn,
            "est_sec": round(total, 1), "orig_clips": n_orig}


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a: print(__doc__); sys.exit(2)
    p = a[0]
    try: spec = json.load(open(p, encoding="utf-8"))
    except Exception as e: print("✗ 스펙을 읽지 못함:", e); sys.exit(1)
    if not isinstance(spec, dict) or not spec.get("scenes"): print("✗ scenes 없는 스펙"); sys.exit(1)
    r = check(spec, p, use_db="--no-db" not in sys.argv)
    if "--json" in sys.argv: print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"렌더 전 관문 {r['id']} · 추정 {int(r['est_sec'] // 60)}:{int(r['est_sec'] % 60):02d} · 원음 {r['orig_clips']}개 → {'통과' if r['ok'] else '실패 — 렌더 금지'}")
        for f in r["fail"]: print("  ✗", f)
        for w in r["warn"]: print("  △", w)
    if "--report" in sys.argv:
        summ = ("통과" if r["ok"] else "실패 " + str(len(r["fail"])) + "건: " + " / ".join(r["fail"][:6])) + (f" · 경고 {len(r['warn'])}" if r["warn"] else "")
        try: rpc("prerender_gate_report", {"p_spec": r["id"], "p_plan": r.get("plan") or "", "p_ok": r["ok"], "p_summary": summ})
        except Exception as e: print("  (DB 기록 실패:", e, ")")
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
