# 2026-11-10 D-2 원고 · 테슬라 주가 전망 (P261108-tesla-41jo · 공개 2026-11-12 12:30 KST)
# 사용: python3 scripts/youtube/long/drafts/_script_L261112-tesla.py && python3 scripts/youtube/long/drafts/_build_L261112-tesla.py
#   → staging/L261112-tesla-41jo.json (D-1 11/11 08:47에 specs/로 옮겨 렌더)
# 제1 원칙 119 구조: [훅] 장면 → [역설] → [약속]+[예고] → R1~R4 · 가짜 결말(약 62%) · 회수 2번 · [북엔드]
import json, os, copy, re
HERE = os.path.dirname(os.path.abspath(__file__)); SPECS = os.path.join(HERE, "..", "specs")
LIB = os.path.join(HERE, "..", "..", "..", "blog", "media", "lib")
SCRIPT = json.load(open(os.path.join(HERE, "_script_L261112-tesla.json"), encoding="utf-8"))
base = json.load(open(os.path.join(SPECS, "L261108-lev-91.json"), encoding="utf-8"))
soxl = json.load(open(os.path.join(SPECS, "L261107-soxl-38.json"), encoding="utf-8"))
pep = json.load(open(os.path.join(SPECS, "L261110-pepero-v2.json"), encoding="utf-8"))
OUT_DIR = os.environ.get("OUT_DIR", os.path.join(HERE, "..", "staging"))
BANNED = {"commons_handshake_1.jpg", "commons_handshake_2.jpg", "commons_samsungfab_1.jpg", "commons_pyeongtaek_1.jpg", "commons_pyeongtaek_2.jpg"}
PREV = set()
for sid in ("L261107-soxl-38", "L261108-lev-91", "L261109-nvidia-huang", "L261109-palantir-what", "L261110-pepero-v2", "L261025-tesla-faucet"):
    p_ = os.path.join(SPECS, sid + ".json")
    if not os.path.exists(p_): continue
    for sc in json.load(open(p_, encoding="utf-8"))["scenes"]:
        v = sc["v"]
        for c in v.get("cuts", []): PREV.add(c["lib"] if isinstance(c, dict) else c)
        for k in ("lib", "closing_photo", "backdrop"):
            if v.get(k): PREV.add(v[k])
USED = {}; WARN = []; MISSING = []
FALLBACK = os.environ.get("FALLBACK", "")   # 일러스트 생성 전 미리보기용: 없는 il_ 소재를 이 소재로 임시 대체

# 2026-11-10 Higgsfield 크레딧 부족으로 새 일러스트 19장 실패(쇼룸 1장만 생성) — 라이브러리 소재로 대체. 크레딧 충전 뒤 D-1에 다시 생성되면 자동으로 새 그림을 쓴다.
ALT = {"handshake": ["il_L261105h_handshake", "vhandshake_24047_a.jpg", "il_L261105h_handshake"], "empty_factory": ["car_64_a.jpg", "cardriving_72_b.jpg"], "cashbox": ["il_L261105h_safeempty", "il_L261104g_calendar_dec", "il_L261105g_cin_cbvault"],
       "seoul_phone": ["il_L261107s_seoul_bed_phone", "il_L261107m_subway_phone", "il_L261107s_dawn_phone", "il_L261105k_cin_phone"], "red_screens": ["il_L261104g_screens_red", "il_L261107m_trading_red"], "thumb_line": ["commons_modely_3.jpg", "commons_fsd_1.jpg"],
       "three_glasses": ["il_L261107s_three_glasses", "il_L261107m_three_items"], "tax_envelope": ["il_L261105h_certs", "il_L261105g_cin_receipt"], "garage_2006": "il_L261105h_earlycar",
       "desert_highway": "il_L261104g_long_road", "courtroom": "il_L261105h_uscourt", "robotaxi": ["il_L261109p_dots_city", "il_L261107m_tech_campus", "vnightcity_49878_a.jpg"],
       "austin_ride": ["car_74_b.jpg"], "battery_field": "il_L261107m_powerlines_homes", "humanoid_line": ["il_L261109p_factory_control", "robot_47266_a.jpg"],
       "vault": "il_L261104g_vault_shine", "loan_keys": "il_L261107m_loan_desk", "night_highway": ["il_L261110a_closing_dawn", "il_L261107m_manhattan_sunrise"],
       "rocket_road": "rocket_45232.mp4", "showroom": "il_L261112t_showroom"}
ALT_N = {}
def _ex(n): return any(os.path.exists(os.path.join(LIB, n + e)) for e in (".mp4", ".jpeg", ".jpg", ".png")) or os.path.exists(os.path.join(LIB, n))
def resolve(tok):
    name = "il_L261112t_" + tok[2:] if tok.startswith("I:") else tok
    if tok.startswith("I:") and not _ex(name):
        a = ALT[tok[2:]]; n = ALT_N.get(tok, 0); ALT_N[tok] = n + 1
        name = a[n % len(a)] if isinstance(a, list) else a
    if "." in name: path = name
    else:
        path = next((name + e for e in (".mp4", ".jpeg", ".jpg", ".png") if os.path.exists(os.path.join(LIB, name + e))), None)
    if not path or not os.path.exists(os.path.join(LIB, path)):
        MISSING.append(tok)
        assert FALLBACK, "없는 소재: " + tok
        return FALLBACK
    assert path not in BANNED, path
    if path in USED: WARN.append(("반복", path))
    USED[path] = USED.get(path, 0) + 1
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
def QU(rows, by, at=0.3, line=0): return dict(kind="quote", rows=rows, by=by, line=line, at=at)
def CH(series, ticks, labels, color="red", at=0.3, line=0, hi=None, lo=0):
    n = len(series); xs = [i / (n - 1) for i in range(n)]
    return dict(kind="chart", series=series, xs=xs, lo=lo, hi=hi or max(series) * 1.15, x=150, y=250, w=820, h=300, color=color, width=9,
                labels={str(i): t for i, t in enumerate(labels)}, labsize=44, line=line, at=at, dur=2.0, **{"from": 0, "to": 1}, ticks=[[xs[i], t] for i, t in enumerate(ticks)])

POOLS = {
 "story": ["vtyping_1781.mp4", "vdocuments_22856_a.jpg", "vcontract_23112_a.jpg", "vnewspaper_34190_a.jpg", "commons_musk_1.jpg", "cardriving_72_a.jpg", "vunitedstates_4251.mp4", "vmeeting_15716_a.jpg", "vphonecall_23073_a.jpg", "vbusinessman_22961_a.jpg", "office_4809_a.jpg", "factory_14631_a.jpg", "vnewspaper_41199_a.jpg", "vcourt_46820_a.jpg", "commons_musk_4.jpg", "vphonecall_39790_a.jpg", "vdocuments_45923_a.jpg"],
 "biz": ["factory_47257_a.jpg", "robot_47257_a.jpg", "solarpanels_23491_a.jpg", "server_23215_a.jpg", "commons_optimus_1.jpg", "chip_47048_a.jpg", "vanalytics_41277_a.jpg", "commons_cybercab_4.jpg", "robot_49042_a.jpg", "solarpanels_46623_a.jpg", "commons_nasdaqsite_3.jpg", "vprogramming_9757.mp4", "newyork_4442_a.jpg", "commons_optimus_5.jpg", "server_47050_a.jpg", "money_47012_a.jpg", "vsemiconductor_1138_a.jpg", "commons_fsd_5.jpg", "vanalytics_41278_a.jpg", "map_21607_a.jpg", "commons_musk_7.jpg", "vsemiconductor_1139_a.jpg", "il_L261107m_dc_cooling", "il_L261107m_earnings_call", "il_L261107m_dealing_room", "server_7863_a.jpg", "chip_47051_a.jpg", "vunitedstates_26828_a.jpg", "newyork_26920_a.jpg", "commons_musk_6.jpg", "vdocuments_24632_a.jpg", "vcontract_28362_a.jpg"],
 "kr": ["vseoul_20089_a.jpg", "phone_4919_a.jpg", "smartphone_41638_a.jpg", "money_18296_a.jpg", "vprogramming_46635.mp4", "coins_18263_a.jpg", "laptop_1781_a.jpg", "vcapitol_40677_a.jpg", "money_18297_a.jpg", "vcomputer_9757_a.jpg", "coins_47008_a.jpg", "umbrella_4331_a.jpg", "storm_25081_a.jpg", "vtyping_41183_a.jpg", "vdocuments_39496_a.jpg", "il_L261107s_subway_phones", "il_L261109p_calc_notebook", "il_L261107s_scale_coins", "il_L261109p_analyst_wall", "il_L261105h_contract", "il_L261105g_cin_signing", "il_L261107m_permit_stamp", "il_L261109p_contract_cash", "money_45703_a.jpg", "money_47005_a.jpg", "vmoney_18296_a.jpg", "coins_38406_a.jpg", "vofficebuilding_41541_a.jpg", "il_L261105h_padlock", "vseoul_20093_a.jpg", "vseoul_20095_a.jpg", "phone_4915_a.jpg", "vsilhouette_1214_a.jpg", "vofficebuilding_40652_a.jpg", "vofficebuilding_40701_a.jpg", "vcapitol_40700_a.jpg", "vcontract_28362_a.jpg", "vnewspaper_41192_a.jpg", "technology_46635_a.jpg", "vstockmarket_47213_a.jpg", "vstockmarket_9607_a.jpg"],
 "end": ["sunrise_6734_a.jpg", "vnightcity_49878_a.jpg", "newyork_33965_a.jpg", "electriccar_23126_a.jpg", "sunrise_26532_a.jpg", "commons_modely_2.jpg", "cardriving_52427_b.jpg", "vanalytics_42648_a.jpg", "commons_megapack_2.jpg", "electriccar_22982_b.jpg"],
}
def pool_for(c): return "story" if c <= 4 else "biz" if c <= 9 else "kr" if c <= 13 else "end"
PER = 4.0
S = []; REPORT = []; CH_PENDING = []
def M(ref, cuts, sketch=None, src="", cold=False, first=False):
    refs = ref if isinstance(ref, list) else [ref]
    lines = [L(*r) for r in refs]
    cs = [resolve(c) for c in cuts]
    secs = sum(syl(t) for t in lines) / 6.1
    pl = POOLS[pool_for(refs[0][0])]
    while secs / len(cs) > PER and not cold:
        nxt = next((x for x in pl if x not in USED and not any(k.startswith(x + ".") for k in USED) and _ex(x)), None)
        if not nxt: WARN.append(("풀 소진", pool_for(refs[0][0]))); break
        cs.append(resolve(nxt))
    REPORT.append((round(secs, 1), len(cs), round(secs / len(cs), 1), lines[0][:18]))
    v = {"type": "media", "full": True, "wash": "none" if cold else "left", "cuts": [{"lib": c} for c in cs]}
    if cold:
        v.update(cine=True, doc_cine=True)
        if sketch and any(x.get("kind") in ("table", "bars", "chart", "pct") for x in sketch): v.update(wash="left", wash_amt=0.85)
    else: v["wash_amt"] = 0.85
    s = {"v": v, "lines": lines, "sketch_add": [], "en": [""] * len(lines), "asof": False, "src": src, "sketch": sketch or []}
    if cold: s.update(lead=0.0 if first else 0.08, hold=0.12)
    if CH_PENDING: s["chapter"] = CH_PENDING.pop()
    S.append(s)
def T(title): CH_PENDING.append(title)   # 장 제목 카드는 그 장 첫 장면의 chapter (제1 원칙 109: 무음 카드, 내레이션으로 읽지 않음)

EL = "Electrek 2026-10-21 · 테슬라 2026년 3분기 실적"
BNN = "BNN Bloomberg 2026-10-22"
TR = "Trefis·서울신문 2026-11-06"
SB = "한국예탁결제원 세이브로 · SBS Biz 2026-11-06"
VA = "애슐리 밴스 『일론 머스크』(2015) · CNN 2015-04-20"
MP = "tesla.com · 2006-08-02 'The Secret Tesla Motors Master Plan'"
NT = "notateslaapp 2026-10-22 · 테슬라 3분기 실적 발표"
MT22 = "머니투데이 2022-12-26 (한국예탁결제원)"
MT25 = "머니투데이 2025-12-22 (한국예탁결제원)"
TS = "247wallst 2026-07-31 · 최근 1년 수익률"
PAY = "테슬라 2025 위임장 · 2025-11-06 주주총회 승인"
LAW = "미국 캘리포니아 북부 연방지법 2024-09 (Lamontagne v. Tesla)"
TAX = "SBS Biz 2026-11-04 · 이코노미스트 2026-11-05 · MTN 2026-11-05"
VIX = "Cboe VIX · 2026-11-09 종가 19.92"
FINE = "참고 기준 · 매수·매도 권유 아님"

# ── 훅 (인트로 전) — 사진·영상 3~4초마다, 펀치는 훅에서만 강약
M((0,0), ["I:seoul_phone", "commons_modely_2"], [PU("약 30조 원", "한국 투자자 테슬라 보관액 · 2026.11.4", at=0.3, hold=1.8)], src=SB, cold=True, first=True)
M((0,1), ["vhandshake_46755_a.jpg", "commons_googleplex_1", "vhandshake_30016"], [LOW("2013년 봄", "테슬라 매각 협상 · 구글", at=0.5)], src=VA, cold=True)
M((0,2), ["I:cashbox", "I:cashbox"], [PU("2주", "2013년 테슬라 현금 · 버틸 수 있던 기간", at=0.3, hold=1.6, soft=False)], src=VA, cold=True)
M((0,3), ["I:red_screens", "vstockmarket_47213", "vseoul_20093"], [PU("-10.8%", "2026.11.5 하루 · 회사 발표 없음", color="red", at=2.0, hold=1.8, soft=False)], src=TR, cold=True)
M((0,4), ["I:thumb_line", "factory_14051_a"], [PU("약 200만 원", "3분기 회사 영업이익 ÷ 판매 대수", at=1.6, hold=1.8)], src=EL, cold=True)
M((0,5), ["commons_teslastore_1", "vwallstreet_4842_a.jpg"], [], cold=True)
M((0,6), ["I:three_glasses", "phone_4915"], [TB(["얼마나", "언제", "하지 말 것"], [["비중", "확인 조건", "대출·배수 상품"]], ["gold", "gold", "red"], at=1.0)], cold=True)
M((0,7), ["I:tax_envelope", "vcontract_23222_a.jpg"], [], cold=True)
ident = copy.deepcopy(soxl["scenes"][9]); ident.pop("dur", None); ident["lines"] = [L(1,0)]; ident["en"] = [""]; S.append(ident)
# ── 결론 먼저
M((2,0), ["electriccar_23125_a", "commons_fsd_2"], [TB(["테슬라 주가", "구성"], [["자동차", "일부"], ["약속 3개", "대부분"]], ["gray", "gold"], at=1.2)])
M((2,1), ["commons_cybercab_1", "commons_megapack_2", "commons_optimus_2"], [IC("bolt", "로보택시 · 대형 배터리 · 로봇", at=0.1)])
M((2,2), ["vanalytics_5462"], [])
M((2,3), ["I:empty_factory"], [])
# ── 1장
T("2006년의 4줄과 2013년의 악수")
M((3,0), ["I:garage_2006"], [P("2006년 · 캘리포니아")])
M((3,1), ["vcomputer_46635", "vtyping_242"], [LOW("The Secret Tesla Motors Master Plan", "2006년 8월 2일 · 회사 홈페이지", at=1.0)], src=MP)
M((3,2), ["vdocuments_22856"], [TB(["순서", "계획"], [["1", "스포츠카"], ["2", "더 싼 차"], ["3", "더 싼 차"], ["4", "친환경 전기"]], ["gray", "gold"], at=0.3)], src=MP)
M((3,3), ["vsecret_14024" if os.path.exists(os.path.join(LIB, "vsecret_14024.mp4")) else "vdocuments_45923"], [QU(["Don't tell anyone."], "2006년 계획 마지막 문장", at=0.2)], src=MP)
M((3,4), ["storm_47948"], [])
M((3,5), ["commons_modely_4", "I:showroom"], [P("2013년 초 · 모델 S")], src=VA)
M((3,6), ["vdocuments_48385"], [LOW("애슐리 밴스 『일론 머스크』", "2015년 출간 전기 · 협상 기록", at=0.1)], src=VA)
M((3,7), ["commons_googleplex_2", "vcontract_23112"], [TB(["인수 금액", "공장 증설"], [["약 60억 달러", "50억 달러"]], ["gold", "gray"], at=0.5)], src=VA)
M((3,8), ["vbusinessman_8941_a.jpg", "vphonecall_7029" if os.path.exists(os.path.join(LIB, "vphonecall_7029.mp4")) else "vphonecall_39790_a.jpg"], [])
M((3,9), ["I:empty_factory", "vmoney_18261"], BARS("2013년 1분기", [b("매출", 562, "5억 6,200만 달러", "gray"), b("순이익", 60, "1,100만 달러 · 첫 흑자", "green")]), src="테슬라 2013년 1분기 실적")
M((3,10), ["vstockmarket_9607"], [])
M((3,11), ["electriccar_22982_a"], [])
# ── 2장
T("약속은 몇 번 미뤄졌나")
M((4,0), ["commons_musk_3"], [])
M((4,1), ["I:desert_highway"], [LOW("2016년 10월", "자율주행 미국 횡단 약속 · 2017년 말까지", at=0.3)], src="테슬라 발표 2016-10-19")
M((4,2), ["commons_fsdscreen_2", "road_34563" if os.path.exists(os.path.join(LIB, "road_34563.mp4")) else "cardriving_52427_a"], [LOW("2019년 4월", "‘내년 로보택시 100만 대’ · 오토노미 데이", at=0.3)], src="테슬라 오토노미 데이 2019-04-22")
M((4,3), ["vcalendar" if False else "vdocuments_24632"], [TB(["약속", "결과"], [["2017년 횡단", "미이행"], ["2020년 100만 대", "미이행"]], ["gray", "red"], at=0.2)])
M((4,4), ["I:courtroom", "vcourt_46117"], [P("2024년 9월 · 주주 소송 기각")], src=LAW)
M((4,5), ["vcourt_47602"], [QU(["corporate puffery"], "법원 판단 · 기업의 홍보성 과장", at=0.6)], src=LAW)
M((4,6), ["vstockmarket_47214", "vwallstreet_4022" if os.path.exists(os.path.join(LIB, "vwallstreet_4022.mp4")) else "vstockmarket_47016"], [])
M((4,7), ["car_35540_b.jpg", "car_64_b.jpg"], [P("2018년 모델 3 양산 → 2020년 첫 연간 흑자")], src="테슬라 연차보고서 2020")
# ── 3장
T("차에서 버는 돈")
M((5,0), ["factory_23696_b" if os.path.exists(os.path.join(LIB, "factory_23696_b.jpg")) else "factory_14051_b"], [])
M((5,1), ["I:thumb_line"], [PU("280억 달러", "2026년 3분기 매출 · 약 38조 원", at=0.4, hold=1.8)], src=EL)
M((5,2), ["vanalytics_42648"], BARS("영업이익률 · 3분기", [b("2025년", 5.8, "5.8%", "gray"), b("2026년", 2.6, "2.6%", "red")]), src=EL)
M((5,3), ["electriccar_40692_a", "commons_modely_5"], [TB(["판매 대수", "차 한 대당 영업이익"], [["48만 6천 대", "1,476달러 · 약 200만 원"]], ["gray", "gold"], at=1.0)], src=EL + " · 환율 약 1,360원")
M((5,4), ["commons_modely_6"], BARS("자동차 총이익률 · 크레딧 제외", [b("2025년 3분기", 15.4, "15.4%", "gray"), b("2026년 3분기", 18.1, "18.1%", "green")]), src=EL)
M((5,5), ["vsemiconductor_4040" if os.path.exists(os.path.join(LIB, "vsemiconductor_4040.mp4")) else "server_20823" if os.path.exists(os.path.join(LIB, "server_20823.mp4")) else "vdata_23062" if os.path.exists(os.path.join(LIB, "vdata_23062.mp4")) else "datacenter_23283" if os.path.exists(os.path.join(LIB, "datacenter_23283.mp4")) else "chip_4010" if os.path.exists(os.path.join(LIB, "chip_4010.mp4")) else "vprogramming_4060" if os.path.exists(os.path.join(LIB, "vprogramming_4060.mp4")) else "vnetwork_40712" if os.path.exists(os.path.join(LIB, "vnetwork_40712.mp4")) else "commons_nvidiagpu_2"], [IC("chip", "영업이익 감소 · 연구개발·AI 비용", at=0.6)], src="테슬라 2026년 3분기 10-Q")
M((5,6), ["car_35540_a"], [])
# ── 4장
T("왜 자동차 회사 값이 아닌가")
M((6,0), ["vstockmarket_47792"], BARS("주가수익비율 · 2026.10.22", [b("테슬라", 188, "188배", "red"), b("포드", 6.6, "6.6배", "gray"), b("GM", 5.2, "5.2배", "gray")]), src=BNN)
M((6,1), ["car_74_a"], [])
M((6,2), ["vnewyork_30544"], [])
M((6,3), ["commons_nasdaqsite_2"], [P("2026년 11월 5일")], src=TR)
M((6,4), ["vwashington_4085" if os.path.exists(os.path.join(LIB, "vwashington_4085.mp4")) else "commons_cacapitol_1", "I:red_screens"], [PCT([{"label": "나스닥", "v": -5.5}, {"label": "테슬라", "v": -10.8}], at=1.2)], src=TR)
M((6,5), ["vstockmarket_47012"], [])
M((6,6), ["commons_cybercab_2", "commons_megapack_3", "commons_optimus_3"], [])
# ── 5장
T("약속 ① 로보택시")
M((7,0), ["commons_fsd_3"], [])
M((7,1), ["I:robotaxi", "map_39787"], [IC("globe", "로보택시 운영 도시 · 6곳", at=0.5)], src=NT)
M((7,2), ["commons_cybercab_5", "I:austin_ride"], [LOW("사이버캡", "운전대 없는 전용 차 · 오스틴 300대+", at=0.5)], src=NT)
M((7,3), ["commons_fsdscreen_3"], BARS("자율주행 기능 사용자", [b("2025년 3분기", 104, "약 104만 명", "gray"), b("2026년 3분기", 174, "174만 명", "green")]), src=EL)
M((7,4), ["electriccar_23126_b"], [])
M((7,5), ["commons_fsd_4"], [P("고객 차 운전자 없는 자율주행 · 2027년 2분기 예고")], src=NT)
M((7,6), ["commons_googleplex_1", "commons_sfskyline_2"], [LOW("웨이모", "구글 모회사 알파벳의 자율주행 회사", at=1.5)], src="웨이모 · 알파벳 공시")
M((8,0), ["I:battery_field"], [])
M((8,1), ["commons_megapack_4"], BARS("에너지 저장 설치량 · 3분기", [b("시장 기대", 15.9, "15.9GWh", "gray"), b("실제", 13.7, "13.7GWh", "red")]), src=EL)
M((8,2), ["commons_datacenter_3", "commons_megapack_1"], [IC("bolt", "메가팩 · 2027년 물량 거의 매진", at=0.4)], src=NT)
M((8,3), ["commons_constructiondc_2"], [])
M((8,4), ["I:humanoid_line", "commons_optimus_4"], [LOW("옵티머스", "프리몬트 초기 생산 · 외부 판매 2027년 말쯤", at=0.6)], src=NT)
M((8,5), ["factory_47258" if os.path.exists(os.path.join(LIB, "factory_47258.mp4")) else "commons_constructiondc_3"], [])
M((8,6), ["I:vault"], [PU("454억 달러", "테슬라 현금 · 2026년 9월 말 · 약 62조 원", at=0.3, hold=1.8)], src=EL)
M((8,7), ["I:cashbox", "commons_bankvault_2"], [TB(["2013년", "2026년"], [["현금 2주치", "454억 달러"]], ["red", "green"], at=0.8)])
# ── 7장
T("1조 달러짜리 계약서")
M((9,0), ["vdocuments_39496"], [])
M((9,1), ["commons_musk_5", "vconference_23116"], [P("2025년 11월 6일 · 주주총회 승인")], src=PAY)
M((9,2), ["vmoney_47005"], [PU("1조 달러", "목표를 모두 채울 때 머스크 보상 주식 가치", at=0.3, hold=1.8)], src=PAY)
M((9,3), ["vbusinessman_42648_a.jpg"], BARS("시가총액", [b("현재", 1.5, "약 1조 5천억 달러", "gray"), b("보상 조건", 8.5, "8조 5천억 달러", "gold")]), src=PAY + " · Fox Business 2026-11-09")
M((9,4), ["commons_cybercab_3" if "commons_cybercab_3" not in PREV else "I:robotaxi", "I:humanoid_line", "electriccar_22982_b"], [TB(["조건", "목표"], [["로보택시", "100만 대"], ["로봇", "100만 대"], ["누적 차량", "2천만 대"]], ["gray", "gold"], at=0.2)], src=PAY)
M((9,5), ["commons_fsdscreen_1" if "commons_fsdscreen_1" not in PREV else "commons_fsd_5"], [TB(["2019년", "2025년"], [["‘내년 100만 대’", "보상 조건 100만 대"]], ["gray", "gold"], at=0.4)])
M((9,6), ["vnews_41204", "commons_optimus_wide.jpg", "vwallstreet_24517_a.jpg"], [])
# ── 8장
T("한국 투자자의 기록")
M((10,0), ["vseoul_20095"], [])
M((10,1), ["I:seoul_phone"], [CH([300, 245, 215, 180, 137], ["9월", "", "", "", "12월"], {"0": "300달러", "4": "137달러"}, color="red", at=0.3), P("2022년 · 한국 투자자 순매수 11억 7천만 달러", at=2.5)], src=MT22)
M((10,2), ["vnightcity_40746"], [P("2025년 12월 · 사상 최고 종가 주간 · 순매도 2억 3천만 달러")], src=MT25)
M((10,3), ["vnightcity_40747", "il_L261107s_phone_red"], [])
M((10,4), ["phone_14669"], [LOW("TSLL", "테슬라 하루 수익률 2배 추종 ETF", at=1.4)])
M((10,5), ["vcomputer_1781_a.jpg"], [PCT([{"label": "테슬라", "v": -5.6}, {"label": "TSLL", "v": -36.8}], at=0.6)], src=TS)
M((10,6), ["vdata_23061" if os.path.exists(os.path.join(LIB, "vdata_23061.mp4")) else "commons_stockcert_2"], [TB(["100원 시작", "테슬라", "2배 상품"], [["+10% → -10%", "99원", "96원"]], ["gray", "gray", "red"], at=1.8)], src="예시 계산 · 변동성 손실")
M((10,7), ["vbusinessman_231"], [])
# ── 9장
T("들고 계신 분의 기준")
M((11,0), ["vpresentation_24173"], [], src=FINE)
M((11,1), ["I:red_screens" if False else "vwallstreet_24515_a.jpg"], [PU("-74%", "테슬라 2021.11 → 2023.1 고점 대비", color="red", at=0.9, hold=1.8)], src="나스닥 종가 · 2021-11-04 409.97달러 → 2023-01-03 108.10달러")
M((11,2), ["calculator_4" if False else "commons_pricetag_1" if False else "laptop_4713"], [TB(["테슬라 비중", "전체 자산 손실"], [["30%", "-22%"], ["50%", "-37%"]], ["gray", "red"], at=0.3)], src="같은 하락(-74%) 가정 계산 · " + FINE)
M((11,3), ["vcomputer_308"], [])
M((11,4), ["I:three_glasses"], [], src=FINE)
M((11,5), ["commons_krxboard_1"], [IC("down", "① 11/5 종가 343달러 · 2주 유지", at=0.1)], src=TR)
M((11,6), ["umbrella_4111" if os.path.exists(os.path.join(LIB, "umbrella_4111.mp4")) else "il_L261107m_hourglass"], [IC("warning", "② VIX 20 아래 · 2주", at=0.1)], src=VIX)
M((11,7), ["vpresentation_24068"], [IC("dollar", "③ 1월 인도량·실적 · 약속 일정 유지", at=0.1)], src=FINE)
M((11,8), ["I:loan_keys"], [IC("bank", "신용·주택담보대출 매수 금지", at=0.2, color="red")], src=FINE)
M((11,9), ["vmoney_45703"], [])
# ── 10장
T("팔지 않아도 세금?")
M((12,0), ["I:tax_envelope"], [])
M((12,1), ["I:rocket_road", "rocket_4201" if os.path.exists(os.path.join(LIB, "rocket_4201.mp4")) else "space_4201" if os.path.exists(os.path.join(LIB, "space_4201.mp4")) else "commons_smallsat_1"], [LOW("2026년 10월 20일", "머스크 · 두 회사 합병 검토 위원회", at=0.8)], src=TAX)
M((12,2), ["vofficebuilding_31663"], [P("바클레이즈 · 12월 주주총회 전 발표 가능성 (예상)")], src=TAX)
M((12,3), ["vcontract_23222"], [IC("building", "해외 회사 주식 교환 합병 = 양도로 간주", at=0.6)], src=TAX)
M((12,4), ["commons_stockcert_1"], [TB(["공제", "세율"], [["연 250만 원", "22%"]], ["gray", "red"], at=1.0)], src=TAX + " · 지방소득세 포함")
M((12,5), ["calculator_14" if False else "vtyping_41183"], [])
# ── 볼 것 3가지
T("앞으로 볼 것 3가지")
M((13,0), ["electriccar_40692_b.jpg"], [])
M((13,1), ["I:robotaxi" if USED.get("il_L261112t_robotaxi.jpeg", 0) < 2 else "commons_cybercab_4", "vunitedstates_4334_a.jpg"], [IC("globe", "① 로보택시 도시 · 2027년 2분기 일정", at=0.1)], src=NT)
M((13,2), ["commons_modely_1"], [IC("up", "② 자동차 총이익률 18%", at=0.1)], src=EL)
M((13,3), ["I:vault" if False else "commons_nyfedvault_2", "commons_nyfedvault_1.jpg"], [IC("dollar", "③ 설비투자 · 현금 흐름 (1월 말 실적)", at=0.1)])
# ── 마무리 (북엔드)
M((14,0), ["I:handshake"], [])
M((14,1), ["electriccar_23125_b.jpg"], [])
M((14,2), ["I:night_highway"], [])
M((14,3), ["I:seoul_phone"], [])
M((14,4), ["I:night_highway"], [])
S.append({"v": {"type": "end", "sub": "", "btn_at": ["0:좋아요", "0:좋아요", "0:좋아요"], "note": {"text": ""}, "dark_end": True},
    "lines": [L(14, 5)], "endscreen": 11, "sketch_add": [], "en": [""], "asof": False, "src": ""})

TITLE = "테슬라 주가 전망, 차 한 대에 200만 원 남기는 회사를 한국 사람은 왜 30조 원어치나 들고 있나"
spec = {k: base[k] for k in ["fx", "format", "world", "notebook", "hook", "overlay"]}
spec["look"] = {"paper": "grain", "dark": "navy", "accent": "red"}
spec["music"] = copy.deepcopy(pep["music"])
spec.update({"id": "L261112-tesla-41jo", "company": "TSLA", "no_data": True, "series": "내 계좌 점검", "plan": "P261108-tesla-41jo",
 "scheduled_at": "2026-11-12T12:30:00+09:00",
 "events": [{"at": "2026-11-10T09:30:00+09:00", "by": "claude-long", "what": "D-2 원고 (staging) — 렌더는 11/11 08:47"}],
 "opening": "장면형(2013 구글 악수) + 역설(30조 원·-10.8%·200만 원) + 보유자 호명 약속 + 세금 예고",
 "hook_type": "H13 숨은 이유 + 보유자 대응 힌트",
 "endscreen_target": "L261109-nvidia-huang",
 "title": TITLE, "doc_title": "2주치 현금으로 구글에 팔릴 뻔한 회사, 테슬라 주주는 지금 무엇을 들고 있나",
 "title_en": "Tesla stock outlook: $1,476 profit per car, yet Korean investors hold $22 billion — what are they buying?",
 "tags": ["테슬라 주가 전망", "테슬라 주가", "테슬라주가전망", "테슬라", "TSLA", "TSLL", "테슬라 로보택시", "테슬라 주가 급락", "서학개미 테슬라", "테슬라 스페이스X 합병", "테슬라 합병 세금", "일론 머스크", "사이버캡", "옵티머스", "머스크 보상안"],
 "search_keywords": ["테슬라 주가 전망", "테슬라 주가", "TSLL", "테슬라 로보택시", "테슬라 스페이스X 합병 세금"],
 "sources": [EL, BNN, TR + " (11/5 -10.77%, 343.69달러, 나스닥 -5.52%)", SB + " (11/4 221억 달러 · 11/2 233억 달러)", VA + " · Guardian 2015-04-21", MP,
   "테슬라 2016-10-19 발표 · 오토노미 데이 2019-04-22", LAW, NT + " · driveteslacanada·teslanorth 2026-10-21", PAY, MT22, MT25, TS,
   TAX, VIX + " · Benzinga(나스닥 +2.6%)", "그림: AI 생성 스틸(실존 인물 아님) · 사진: Wikimedia Commons · 영상: Mixkit·Pexels"],
 "pinned_comment": "여러분 계좌에서 테슬라 비중은 몇 퍼센트인가요? 그 비중을 정한 기준이 있다면 댓글로 나눠 주세요.\n※ 영상 속 분할·비중 기준은 참고 기준이며 매수·매도 권유가 아닙니다. 합병·세금은 2026년 11월 5일 기사 기준이며 확정된 내용이 아닙니다.\n좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다.",
 "description_head": "테슬라 주가 전망, 갖고 계신 분이 지금 정해야 할 것은 매수가 아니라 비중입니다.\n\n2026년 11월 5일 테슬라는 회사 발표 없이 하루 10.8% 빠졌습니다. 문제는 실적이 아니었습니다. 주가에 들어 있는 것이 자동차가 아니라 약속 세 개(로보택시·대형 배터리·로봇)이기 때문입니다.\n2013년 현금 2주치로 구글에 팔릴 뻔한 이야기부터, 미뤄진 약속의 역사, 3분기 실적, 머스크 1조 달러 보상안, 한국 투자자의 매매 기록과 TSLL 변동성 손실, 비중·분할 기준, 스페이스X 합병 때 세금 문제까지 정리했습니다.\n\n※ 참고 기준이며 매수·매도 권유가 아닙니다.",
 "description_en": "Tesla nearly sold itself to Google in 2013 with two weeks of cash left. Today Korean investors hold about $22 billion of it. We look at what the share price is really paying for, how far the three promises have come, and how holders can size their position.",
 "hook_promises": ["비중을 정하는 기준 세 가지", "팔지 않아도 세금이 나올 수 있는 이야기", "앞으로 볼 것 3가지"],
 "viewer_question": "테슬라 주주는 무엇을 사고 있고, 지금 비중을 어떻게 정해야 하나",
 "format_note": "D-2 staging. 실존 인물 사진은 머스크(Commons)만, 정치인 없음. 다음 영상 이름 언급 없음. 투자 경력 언급 없음(직전 편 사용). 펀치는 훅 강약 + 본편 soft만.",
 "thumb": {"photo": "commons_modely_5.jpg", "focus_x": 0.65, "l1": "이익은 차 한 대 200만 원꼴", "l2": "한국인 30조, 뭘 믿고 있나?", "pos": "left"},
 "ab_sets": [{"key": "a", "default": True, "title": TITLE, "file": "thumb_a.jpg", "type": "A 큰 숫자 · H13"},
             {"key": "b", "title": "테슬라 주가 하루 -10.8%, 갖고 계신 분이 지금 정해야 할 비중과 기준 3가지", "file": "thumb_b.jpg", "type": "B 보유자 호명 · H22"},
             {"key": "c", "title": "테슬라 주가 전망, 2주치 현금으로 구글에 팔릴 뻔한 회사를 한국 사람은 왜 30조 원어치나 들고 있나", "file": "thumb_c.jpg", "type": "C 변화 스토리 · versus"}],
 "scenes": S})
for s_ in spec["scenes"]:
    if s_["v"].get("cine"):
        for e_ in s_.get("sketch") or []:
            if e_.get("kind") == "lower": e_["y"] = 540
os.makedirs(OUT_DIR, exist_ok=True)
out = os.path.join(OUT_DIR, "L261112-tesla-41jo.json")
json.dump(spec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
spoken = [x for sc in S for x in sc.get("lines", [])]; expected = [x for c, l in SCRIPT for x in l]
assert " ".join(spoken) == " ".join(expected), "불일치"
tot = sum(syl(t) for t in spoken); nums = sum(1 for t in spoken if re.search(r"[0-9]", t))
print("scenes", len(S), "syl", tot, "est", round(tot / 6.1), "숫자 문장 비율", round(nums / len(spoken), 2), "cuts", sum(r[1] for r in REPORT))
print("긴 컷:", [r for r in REPORT if r[2] > 4.6])
print("반복:", sorted({w[1] for w in WARN if w[0] == "반복"}))
print("직전 겹침:", sorted({w[1] for w in WARN if w[0] != "반복"}))
print("없는 소재:", sorted(set(MISSING)))
