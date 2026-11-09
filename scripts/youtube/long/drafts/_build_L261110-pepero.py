# 2026-11-10 빼빼로데이 롱폼 재제작 — 훅→힌트→리훅 · 대표 11/9·11/10 지시 · 사운드 최신 기준(H6→H1 @30, 120Hz 아래 차단)
# 사용: python3 scripts/youtube/long/drafts/_build_L261110-pepero.py → specs/L261110-pepero-day.json
import json, os, copy, re, math
HERE = os.path.dirname(os.path.abspath(__file__)); SPECS = os.path.join(HERE, "..", "specs")
LIB = os.path.join(HERE, "..", "..", "..", "blog", "media", "lib")
SCRIPT = json.load(open(os.path.join(HERE, "_script_L261110-pepero.json"), encoding="utf-8"))
base = json.load(open(os.path.join(SPECS, "L261108-lev-91.json"), encoding="utf-8"))
soxl = json.load(open(os.path.join(SPECS, "L261107-soxl-38.json"), encoding="utf-8"))
OUT_DIR = os.environ.get("OUT_DIR", SPECS)
BANNED = {"commons_handshake_1.jpg", "commons_handshake_2.jpg", "commons_samsungfab_1.jpg", "commons_pyeongtaek_1.jpg", "commons_pyeongtaek_2.jpg"}
PREV = set()
for sid in ("L261107-soxl-38", "L261108-lev-91", "L261107-midterm-ai", "L261109-nvidia-huang", "L261109-palantir-what"):
    for sc in json.load(open(os.path.join(SPECS, sid + ".json"), encoding="utf-8"))["scenes"]:
        v = sc["v"]
        for c in v.get("cuts", []): PREV.add(c["lib"] if isinstance(c, dict) else c)
        for k in ("lib", "closing_photo", "backdrop"):
            if v.get(k): PREV.add(v[k])
FINE = "매수·매도 권유 아님"
USED = {}; WARN = []; used_vid = {}

def resolve(tok):
    name = "il_L261108p_" + tok[2:] if tok.startswith("I:") else ("il_" + tok if re.match(r"[LY]26", tok) else tok)
    if "." in name: path = name
    else:
        path = next((name + e for e in (".mp4", ".jpeg", ".jpg", ".png") if os.path.exists(os.path.join(LIB, name + e))), None)
    assert path and os.path.exists(os.path.join(LIB, path)), "없는 소재: " + tok
    assert path not in BANNED, path
    m = re.search(r"_(\d{3,6})(?:_[ab])?\.", path)
    key = m.group(1) if m and path.endswith((".mp4", ".jpg")) and not path.startswith("commons_") else path
    if key in used_vid and used_vid[key] != path or path in USED: WARN.append(("반복", path))
    used_vid[key] = path; USED[path] = USED.get(path, 0) + 1
    if path in PREV: WARN.append(("직전 편 겹침", path))
    return path

def syl(t): return len(re.findall(r"[가-힣0-9A-Za-z]", t))
def L(c, i): return SCRIPT[c][1][i]
def P(text, line=0, at=0.05, **k): return dict(kind="print", text=text, line=line, at=at, **k)
def b(label, v, text, color): return {"label": label, "v": v, "text": text, "color": color}
def BARS(title, items, at=0.4, line=0): return [P(title, line=line), {"kind": "bars", "items": items, "line": line, "at": at}]
def PCT(items, at=0.3, line=0, dec=1):
    return {"kind": "pct", "items": items, "line": line, "at": at, "scale": round(190 / max(abs(i["v"]) for i in items), 2), "gap": 400, "dec": dec}
def TB(cols, rows, colors, at=0.3, line=0): return {"kind": "table", "cols": cols, "rows": rows, "colors": colors, "line": line, "at": at}
def PU(text, sub, at=0.4, color="gold", hold=2.2, line=0, soft=True):
    d = dict(kind="punch", text=text, sub=sub, line=line, at=at, color=color, hold=hold)
    if soft: d["style"] = "soft"
    return d
def IC(name, text, at=0.3, line=0, color="gold"): return dict(kind="icon", name=name, text=text, line=line, at=at, color=color)
def LOW(text, sub, at=0.15, line=0): return dict(kind="lower", text=text, sub=sub, line=line, at=at)
def CH(series, ticks, labels, color="red", at=0.3, line=0, hi=None, lo=0):
    n = len(series); xs = [i / (n - 1) for i in range(n)]
    return dict(kind="chart", series=series, xs=xs, lo=lo, hi=hi or max(series) * 1.15, x=150, y=250, w=820, h=300, color=color, width=9,
                labels={str(i): t for i, t in enumerate(labels)}, labsize=44, line=line, at=at, dur=2.0, **{"from": 0, "to": 1}, ticks=[[xs[i], t] for i, t in enumerate(ticks)])

S = []; REPORT = []
def M(ref, cuts, sketch=None, src="", cold=False, first=False):
    """ref = (장, 줄 번호) 또는 [(장, 줄)…]"""
    refs = ref if isinstance(ref, list) else [ref]
    lines = [L(*r) for r in refs]
    cs = [resolve(c) for c in cuts]
    secs = sum(syl(t) for t in lines) / 6.1
    per = secs / len(cs)
    REPORT.append((round(secs, 1), len(cs), round(per, 1), lines[0][:18]))
    v = {"type": "media", "full": True, "wash": "none" if cold else "left", "cuts": [{"lib": c} for c in cs]}
    if cold:
        v.update(cine=True, doc_cine=True)
        if sketch and any(b.get("kind") in ("table", "bars", "chart") for b in sketch): v.update(wash="left", wash_amt=0.85)
    else: v["wash_amt"] = 0.85
    s = {"v": v, "lines": lines, "sketch_add": [], "en": [""] * len(lines), "asof": False, "src": src, "sketch": sketch or []}
    if cold: s.update(lead=0.0 if first else 0.08, hold=0.12)
    if CH_PENDING: s["chapter"] = CH_PENDING.pop()
    S.append(s)
CH_PENDING = []
def T(title, sub):
    """렌더러는 문장 없는 장 제목 카드를 건너뛴다 — 장 구분(챕터)은 그 장 첫 장면에 붙인다"""
    CH_PENDING.append(title)



CT = "미국 연방 제3순회항소법원 2021-01 (Ezaki Glico v. Lotte)"
SH = "머니투데이·뉴데일리 2020-01-19"
LQ = "뉴시스 2024-11-29"
LB = "한경비즈니스 2026-10-29"
FIN = "다올투자증권 2026-10-12 · 매수·매도 권유 아님"
# 훅
M((0,0), ["L261108p_us_courtroom", "L261105h_uscourt"], [LOW("“A tale of more than just desserts.”", "Ezaki Glico v. Lotte · 2021년 1월", at=0.9)], src=CT, cold=True, first=True)
M((0,1), ["L261108p_stick_handle", "commons_pepero_1"], [PU("POCKY vs PEPERO", "미국 연방 항소법원", at=0.6, hold=1.8, soft=False)], src=CT, cold=True)
M((0,2), ["vdocuments_22856", "vnewspaper_41199"], [], src=CT, cold=True)
M((0,3), ["tokyo_28687", "commons_busanstairs_1"], [TB(["막대 과자", "11월 11일"], [["일본이 먼저", "한국이 먼저"]], ["gray", "gold"], at=1.0)], cold=True)
M((0,4), ["L261108p_girls_handover"], [], cold=True)
M((0,5), ["L261108p_empty_class"], [PU("215곳 중 101곳", "2011년 11월 11일 · 대구 초등학교 휴업", color="red", at=0.3, hold=1.8, soft=False)], src="매일신문 2011-11-09", cold=True)
M((0,6), ["commons_lotteworldtower_1", "vcontract_23112"], [LOW("롯데월드타워", "2024년 11월 · 은행 담보", at=1.4)], src=LQ, cold=True)
M((0,7), ["commons_pepero_5"], [], cold=True)
M((0,8), ["vdocuments_45923"], [], cold=True)
ident = copy.deepcopy(soxl["scenes"][9]); ident.pop("dur", None); ident["lines"] = [L(1,0)]; ident["en"] = [""]; S.append(ident)
T("회사보다 먼저 움직인 주문", "")
M((2,0), ["L261108p_sales_office", "vtyping_242"], [P("1994년 · 경상남도")], src="아이뉴스24 2025-11-07")
M((2,1), ["L261108p_corner_shop", "commons_oldgrocery_2"], [])
M((2,2), ["phone_4919"], [])
M((2,3), ["L261108p_hands_exchange", "L261108p_sticks_eleven", "commons_busanstairs_2"], [])
M((2,4), ["L261108p_busan_alley"], [TB(["시작 시점", "주체"], [["1993년 또는 1994년", "중학생 또는 고등학생"]], ["gray", "gray"], at=0.3)], src="헤럴드경제 2025-06-07")
M((2,5), ["L261108p_thumb_girls"], [])
M((2,6), ["L261108p_press_1996"], [P("1996년 11월 13일 · 첫 보도")], src="연합통신 1996-11-13")
M((2,7), ["commons_lottedept_1"], [])
T("83엔을 들고 떠난 청년", "")
M((3,0), ["L261108p_busan_port", "commons_yenbills_1"], [PU("83엔", "1941년 일본행 밑천", at=1.5, hold=1.8)], src=SH)
M((3,1), ["L261108p_tokyo_1948", "L2611sy_newspaper"], [], src=SH)
M((3,2), ["factory_14051_a", "commons_yenbills_2"], [LOW("윤활유 공장", "1944년 · 5만 엔 차입", at=0.3)], src=SH)
M((3,3), ["storm_47948"], [], src=SH)
M((3,4), ["vcraftsman_7039"], [], src=SH)
M((3,5), ["L261108p_novel_gum", "L261108p_gum_workshop"], [LOW("LOTTE", "1948년 · 샤롯데에서 따온 이름", at=0.3)], src=SH)
M((3,6), ["commons_bankvault_1", "vmoney_18261"], [], src="서울신문 1998-09-04")
M((3,7), ["L261104g_bank_queue_1998"], [PU("부채비율 216%", "1998년 · 30대 그룹 중 재무구조 1위", at=0.6, hold=2.0)], src="서울신문 1998-09-04")
M((3,8), ["commons_lottedept_2"], [])
M((3,9), ["L261108p_factory_1960s", "L261108p_choco_line"], [P("1967년 롯데제과 · 1983년 빼빼로")])
M((3,10), ["chocolate_41117_a", "commons_uscourthouse_1"], [])
T("6년 소송의 마지막 한 줄", "")
M((4,0), ["tokyo_4231", "commons_lawson_2"], [LOW("POCKY", "1966년 · 일본 글리코", at=0.5)], src=CT)
M((4,1), ["vnewspaper_34190"], [])
M((4,2), ["vcourt_46117", "vcontract_23222"], [P("2015년 · 미국 소송 제기")], src=CT)
M((4,3), ["vdocuments_48385"], [], src=CT)
M((4,4), ["commons_uscourthouse_2", "newspaper_41191_a"], [LOW("“the no mess handle”", "글리코 광고 문구 · 판결문 인용", at=2.0)], src=CT)
M((4,5), ["vcourt_46820"], [TB(["포키의 특징", "판결"], [["잡기·먹기·나누기·포장", "실용적 기능"]], ["gray", "gold"], at=0.5)], src=CT)
M((4,6), ["vcourt_47602"], [], src=CT)
M((4,7), ["vdocuments_24632"], [])
M((4,8), ["commons_ussupremeish_1"], [LOW("“That's the way the cookie crumbles.”", "판결문 마지막 문장", at=1.6)], src=CT)
M((4,9), ["candy_10381_a"], [])
M((4,10), ["commons_koreaconv_1"], [])
T("천년에 단 하루", "")
M((5,0), ["tokyo_30137", "commons_lawson_1"], [LOW("포키의 날", "1999년 · 일본 글리코 지정", at=0.3)], src="글리코 · 헤럴드경제 2025-06-07")
M((5,1), ["L261108p_office_gifts", "gift_14839_a"], [])
M((5,2), ["vshopping_15914"], [LOW("2011년 11월 11일", "1이 여섯 개", at=0.5)], src="뉴데일리 2011-11-03")
M((5,3), ["commons_chocolatesale_1"], [LOW("“천년에 단 하루”", "2011년 롯데제과 홍보 문구", at=0.5)], src="뉴데일리 2011-11-03")
M((5,4), ["phone_4915", "laptop_4713"], [TB(["2111년 11월 11일", "2211년 11월 11일"], [["1이 여섯 개", "1이 여섯 개"]], ["gray", "gray"], at=0.6)], src="뉴데일리 2011-11-03")
M((5,5), ["L261110a_rural_school"], [], src="매일신문 2011-11-09")
M((5,6), ["city_1606_a"], BARS("11월 11일 휴업 학교 수 · 대구 초등", [b("2009년", 2, "2곳", "gray"), b("2010년", 0.3, "0곳", "gray"), b("2011년", 101, "101곳", "red")]), src="매일신문 2011-11-09")
M((5,7), ["vpresentation_9069"], [])
M((5,8), ["commons_pricetag_1", "money_23524_a"], [], src="뉴데일리 2011-11-03")
M((5,9), ["commons_jewelryshop_1", "commons_handbagshop_1"], BARS("받고 싶은 선물 · 20~30대 여성", [b("액세서리", 27, "27%", "gray"), b("명품 가방", 20, "20%", "gray"), b("화장품", 18, "18%", "gray"), b("빼빼로", 17, "17%", "gold")]), src="엘르엣진 설문 2011")
M((5,10), ["commons_silkscarf_1"], [])
M((5,11), ["vofficebuilding_31663", "commons_familymart_2"], [LOW("2026년 11월 11일", "수요일", at=0.3)], src="파이낸셜뉴스 2026-10-16")
M((5,12), ["office_914_a", "L261108p_store_night"], [])
M((5,13), ["commons_koreaconv_2"], [PU("+120%", "세븐일레븐 지난해 11월 1~11일 관련 매출", color="green", at=0.4, hold=1.8)], src="새턴경제 2026-11-04")
M((5,14), ["L261108p_warehouse"], [])
M((5,15), ["wheat_17120", "commons_doljanchi_2"], [])
M((5,16), ["commons_jongno_1"], [])
T("담보로 잡힌 123층", "")
M((6,0), ["vnewspaper_41192", "vseoul_20093"], [P("2015년 7월")], src="서울신문 2015-07-31")
M((6,1), ["vdocuments_39496"], [LOW("신동주 측 공개", "해임 지시서 · 신동주 측 주장", at=0.5)], src="서울신문 2015-07-31")
M((6,2), ["vcontract_28362"], [LOW("롯데그룹 측 반박", "적법 절차 없어 무효", at=0.3)], src="서울신문 2015-07-31")
M((6,3), ["vconference_13192", "vmeeting_22961"], [P("2015년 8월 17일 · 일본 롯데홀딩스 주주총회")], src="이투데이")
M((6,4), ["commons_lotteworldtower_2", "vseoul_20095"], [PU("123층", "1987년 부지 매입 · 2017년 완공", at=0.8, hold=1.8)], src=SH)
M((6,5), ["L261104g_banker_silhouette"], [])
M((6,6), ["phone_14669", "vnews_41204"], [P("2024년 11월 18일 · 공시 '사실무근'")], src=LQ)
M((6,7), ["commons_refinery_1", "commons_refinery_2"], BARS("롯데케미칼 차입금", [b("2019년", 3.6, "약 3.6조", "gray"), b("2024년 9월", 10.9, "약 10.9조", "red")], at=0.5), src=LQ)
M((6,8), ["L261105k_cin_ledger"], [TB(["회사채 약정", "2024년 3분기 말"], [["5배 이상", "4.3배"]], ["gray", "red"], at=0.8)], src=LQ)
M((6,9), ["L261107m_storm_tower", "L261105g_cin_vaultclose"], [PU("6조 원+", "롯데월드타워 가치 · 은행 담보 제공", color="red", at=1.2, hold=1.8)], src=LQ)
M((6,10), ["L261105h_towerman"], [])
M((6,11), ["vhandshake_30016", "vcontract_23222".replace("23222","23222") if False else "vmoney_47005"], [PU("1조 3,105억 원", "롯데렌탈 매각 · TPG · 2026년 10월 30일", at=1.2, hold=1.8)], src="글로벌이코노믹 2026-10-30")
M((6,12), ["vmoney_45703"], [], src=LB)
M((6,13), ["L261108p_thumb_sticks"], [])
T("매출의 열에 하나도 안 되는 과자", "")
M((7,0), ["commons_pepero_2"], [])
M((7,1), ["L261108p_analyst_desk"], BARS("지난해 매출", [b("빼빼로", 2430, "2,430억", "gold"), b("롯데웰푸드 전체", 42160, "4조 2,160억", "gray")]), src="아주경제 2026-10-20 · 스마트투데이 2026-02-06")
M((7,2), ["L261108p_cocoa_farm", "commons_cocoapod_1", "L261108p_cocoa_screens"], [PU("-30%", "지난해 롯데웰푸드 영업이익", color="red", at=1.0, hold=1.8)], src="비즈워치 2026-02-11")
M((7,3), ["map_39787"], [])
M((7,4), ["L261108p_hanoi_popup", "containership_30467"], BARS("올해 상반기 빼빼로 매출", [b("해외", 530, "530억", "gold"), b("국내", 385, "385억", "gray")]), src="아주경제 2026-10-20")
M((7,5), ["vshopping_49137"], [])
M((7,6), ["vairplane_7374", "vconference_13222"], [LOW("2024년 9월 · 폴란드 바르샤바", "원롯데 식품사 전략회의", at=0.3)], src="새턴경제 2024-09-09")
M((7,7), ["vsingapore_30966", "vhandshake_24047"], [LOW("2026년 7월 · 싱가포르", "한일 롯데 합작법인", at=0.3)], src="아주경제 2026-06-30")
M((7,8), ["vmeeting_4809"], [], src="더구루 2026-09-05")
M((7,9), ["L261108p_india_factory", "commons_haryana_1", "L261108p_sun_chocolate"], [P("인도 하리아나 · 2025년 7월 생산 시작")], src="아이뉴스24 2025-11-07")
M((7,10), ["L261108p_times_square", "commons_timessquare_1"], [], src="머니투데이 2026-10-23")
M((7,11), ["L261108p_world_pins"], [])
M((7,12), ["vnewyork_30544", "cargo_4011"], [PU("1조 원", "2035년 빼빼로 매출 목표", at=0.3, hold=1.8)], src="아주경제 2026-10-20")
T("롯데웰푸드 주가 전망", "")
M((8,0), ["vstockmarket_9607"], [])
M((8,1), ["L261108p_freezer_aisle", "vanalytics_5462"], [], src=FIN)
M((8,2), ["laptop_1781", "vtyping_41183", "vstockmarket_47214"], [PU("883억 원", "3분기 영업이익 전망 · 전년 대비 +27.5%", at=0.9, hold=2.0), TB(["해외 법인 매출", "국내 매출"], [["+15.3%", "-0.7%"]], ["green", "red"], at=0.5, line=0) if False else P("증권사 전망치 · 2026년 10월 12일", at=0.05)], src=FIN)
M((8,3), ["L261108p_three_items"], [])
M((8,4), ["L261108p_delhi_market"], [IC("globe", "① 인도 실적", at=0.08)], src=FIN)
M((8,5), ["commons_cocoapod_3", "vmoney_18296"], [IC("dollar", "② 원가 · 유제품·포장재", at=0.08)], src=FIN)
M((8,6), ["cargo_30125"], [IC("up", "③ 빼빼로 해외 매출 1,000억 원", at=0.08)], src="머니투데이 2026-10-23")
M((8,7), ["commons_oldgrocery_3", "vstockmarket_47792"], [], src=FIN)
M((8,8), ["vstockmarket_47016"], [], src=FIN)
M((9,0), ["L261108p_closing_store"], [])
M((9,1), ["L2611sy_snackbar"], [])
S.append({"v": {"type": "end", "sub": "", "btn_at": ["0:좋아요", "0:구독", "0:구독"], "note": {"text": ""}, "closing_photo": resolve("commons_seoulnight_2"), "backdrop": resolve("L261108p_sticks_eleven"), "bd_dim": 0.74},
    "lines": [L(9,2), L(9,3)], "endscreen": 8, "sketch_add": [], "en": ["", ""], "asof": False, "src": ""})
TITLE = "빼빼로데이 유래, 미국 법원까지 간 6년 소송… 그 날을 만든 건 롯데가 아니었다"
spec = {k: base[k] for k in ["fx", "format", "world", "notebook", "hook", "overlay"]}
spec["look"] = {"paper": "blueprint", "dark": "ink", "accent": "sky"}
spec["music"] = copy.deepcopy(base["music"]); spec["music"].pop("bed_eq", None)
spec["music"].update(bed=["social/music/samples3/H6_full.mp3@30", "social/music/samples3/H1_full.mp3@30"], bed_gain_db=3, bed_hp=120, note="본편 H6 House - July → H1 Deep House Sunset · 120Hz 아래 차단 (대표 11/9 최신 기준)")
spec.update({"id": "L261110-pepero-day", "company": None, "no_data": True, "series": "빼빼로데이", "scheduled_at": "2026-11-10T19:30:00+09:00",
 "events": [{"at": "2026-11-10T00:24:00+09:00", "by": "owner", "what": "채팅 지시 — 빼빼로 내일 예약본 작업, 훅·리훅 살리고 사운드 최신 버전"}],
 "opening": "미스터리형 — 판결문 첫 줄 → 손잡이 소송 → 광고 문구(답 미공개) → 11월 11일의 수수께끼 → 휴업 → 타워 담보 → 판결문 마지막 줄 예고", "hook_type": "미스터리 훅 + 힌트 + 리훅",
 "endscreen_target": "L261105-hermes", "title": TITLE, "doc_title": "빼빼로데이는 누가 만들었나", "title_en": "Pepero Day: the six-year US lawsuit and the day Lotte did not invent",
 "tags": ["빼빼로데이 유래", "빼빼로데이", "빼빼로", "포키", "롯데웰푸드", "롯데웰푸드 주가", "롯데웰푸드 주가 전망", "신격호", "롯데월드타워", "롯데 유동성", "11월 11일", "가래떡데이", "빼빼로 수출", "인도 빼빼로", "K푸드"],
 "search_keywords": ["빼빼로데이 유래", "빼빼로데이", "롯데웰푸드 주가 전망", "빼빼로"],
 "sources": ["미국 연방 제3순회항소법원 2021-01-26 판결 (Ezaki Glico v. Lotte International America, 판결문 인용)", "아이뉴스24 2025-11-07 · 헤럴드경제 2025-06-07 · 연합통신 1996-11-13 (유래)", "머니투데이·뉴데일리 2020-01-19 (신격호 생애) · 서울신문 1998-09-04 (재무구조)", "뉴데일리 2011-11-03 · 매일신문 2011-11-09 · 엘르엣진 설문 2011 (밀레니엄 빼빼로데이·대구 휴업·선물 설문)", "파이낸셜뉴스 2026-10-16 · 새턴경제 2026-11-04 (올해 편의점 준비)", "서울신문 2015-07-31 · 이투데이 (경영권 분쟁, 양측 주장)", "뉴시스 2024-11-29 (유동성 위기설·롯데월드타워 담보)", "글로벌이코노믹 2026-10-30 · 한경비즈니스 2026-10-29 (롯데렌탈·자금 확보)", "아주경제 2026-10-20·2026-06-30 · 머니투데이 2026-10-23 · 더구루 2026-09-05 · 새턴경제 2024-09-09 (빼빼로 매출·원롯데)", "스마트투데이 2026-02-06 · 비즈워치 2026-02-11 (2025년 실적)", "다올투자증권 2026-10-12 (3분기 전망, S저널 인용)", "그림: AI 생성 스틸(실존 인물 아님) · 사진: Wikimedia Commons · 영상: Mixkit·Pexels"],
 "pinned_comment": "이번 빼빼로데이, 여러분은 누구에게 주실 건가요? 직장 동료 몫까지 챙기시나요? 댓글로 나눠 주세요.\n※ 2015년 경영권 분쟁은 양측 주장을 함께 소개했습니다. 주가 전망은 2026년 10월 12일 증권사 자료 기준이며 매수·매도 권유가 아닙니다.\n좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다.",
 "description_head": "빼빼로데이 유래가 궁금하신 분들을 위해 정리했습니다.\n\n11월 11일을 만든 건 롯데가 아니었습니다. 포키와 빼빼로의 6년 미국 소송, 2011년 대구 초등학교 휴업, 창업자의 타워가 담보가 된 사연, 롯데웰푸드 주가 전망까지 다룹니다.\n\n※ 주가 전망은 2026년 10월 12일 증권사 자료 기준이며 매수·매도 권유가 아닙니다.",
 "description_en": "Pepero Day was not invented by Lotte. We trace the six-year US lawsuit with Pocky, the 2011 school closures, the Lotte World Tower pledge and what to watch at Lotte Wellfood.",
 "hook_promises": ["판결문의 마지막 한 줄", "승패를 결정한 광고 문구", "볼 것 3가지"], "viewer_question": "빼빼로데이는 누가 만들었고 롯데는 지금 어떤 상황인가",
 "format_note": "11/10 재제작. 실존 인물 사진 없음. 경영권 분쟁은 양측 주장 구분. 시그니엘 매각 언급 없음.",
 "thumb": {"photo": "il_L261108p_thumb_girls.jpeg", "focus_x": 0.6, "l1": "이 날을 만든 건", "l2": "롯데가 아니었다", "pos": "left", "s1": 70, "s2": 130},
 "ab_sets": [{"key": "a", "default": True, "title": TITLE, "file": "thumb_a.jpg", "type": "A 유래"}, {"key": "b", "title": TITLE, "file": "thumb_b.jpg", "type": "B 소송"}, {"key": "c", "title": TITLE, "file": "thumb_c.jpg", "type": "C 타워·주가 전망"}],
 "scenes": S})
EXTRA = {"광복 뒤": ["commons_yenbills_3"], "쓸모 때문에": ["L261105h_contract"], "2024년 9월": ["vofficebuilding_40652"], "지난해 빼빼로 매출": ["commons_krxboard_1"], "시작이 1993년": ["commons_busanstairs_3"], "외환위기 직후": ["vseoul_20089"], "판사의 논리": ["commons_ussupremeish_2"], "그리고 판사는": ["L2611sy_court"], "이렇게 막대 모양": ["commons_familymart_1"], "절정은 2011": ["commons_chocolatesale_2"], "그런데 인터넷에서": ["vcomputer_308"], "학교는 더": ["city_49845_a"], "학교들은 행사": ["candy_10374_a", "vpresentation_24068"], "직장에서는": ["commons_cafeint_1"], "세븐일레븐은": ["commons_koreaconv_3"], "여기까지가": ["commons_seoulnight_3"], "장남 신동주": ["commons_archiveboxes_1"], "롯데 측은": ["vmeeting_15716"], "앞에서 기억": ["commons_bankvault_2"], "일부 회사채": ["commons_stockcert_1", "L261105g_cin_receipt"], "다만 국내": ["commons_oldgrocery_1"], "경영권 분쟁의": ["commons_tokyocommute_1"], "첫째는 인도": ["commons_haryana_2", "vshopping_42123"], "셋째는 빼빼로": ["commons_busanport_1"], "그래서 이 회사": ["vanalytics_42648"], "부산 여학생들이": ["commons_busanport_2"], "판사의 말처럼": ["gift_14839_b"]}
for s_ in spec["scenes"]:
    for k_, ex_ in EXTRA.items():
        if s_.get("lines") and s_["lines"][0].startswith(k_) and "cuts" in s_["v"]:
            s_["v"]["cuts"] += [{"lib": resolve(c_)} for c_ in ex_]
for s_ in spec["scenes"]:
    if s_["v"].get("cine"):
        for e_ in s_.get("sketch") or []:
            if e_.get("kind") == "lower": e_["y"] = 540
out = os.path.join(OUT_DIR, "L261110-pepero-day.json")
json.dump(spec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
spoken = [x for sc in S for x in sc.get("lines", [])]; expected = [x for c, l in SCRIPT for x in l]
assert " ".join(spoken) == " ".join(expected), "불일치"
tot = sum(syl(t) for t in spoken); nums = sum(len(re.findall(r"[0-9][0-9,.]*", t)) for t in spoken)
print("scenes", len(S), "syl", tot, "est", round(tot/6.1), "숫자", nums, "cuts", sum(r[1] for r in REPORT))
print("긴 컷:", [r for r in REPORT if r[2] > 4.6])
print("반복:", sorted({w[1] for w in WARN if w[0]=="반복"}))
print("직전 겹침:", sorted({w[1] for w in WARN if w[0]!="반복"}))
