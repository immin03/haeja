# 2026-11-11 긴급 · SOXL × 엔비디아 젠슨 황 (P261112u-soxl-nvidia · 공개 2026-11-12 11:30 KST, 대표 지정)
# 사용: python3 scripts/youtube/long/drafts/_build_L261112-soxl-nvidia.py → specs/L261112-soxl-nvidia.json
# 제1 원칙 119: [훅] 11/9 장면 → [역설] 엔비디아 -4.3% vs SOXL +22% → [약속]+[예고 2022] → R1~R4 · 가짜 결말(약 60%) · 회수 2번 · [북엔드]
# 젠슨 황 편(L261109-nvidia-huang) 영상·그림 재사용(대표 지시) — 직전 편 겹침 경고에서 제외
import json, os, copy, re
HERE = os.path.dirname(os.path.abspath(__file__)); SPECS = os.path.join(HERE, "..", "specs")
LIB = os.path.join(HERE, "..", "..", "..", "blog", "media", "lib")
SCRIPT = json.load(open(os.path.join(HERE, "_script_L261112-soxl-nvidia.json"), encoding="utf-8"))
base = json.load(open(os.path.join(SPECS, "L261108-lev-91.json"), encoding="utf-8"))
soxl = json.load(open(os.path.join(SPECS, "L261107-soxl-38.json"), encoding="utf-8"))
pep = json.load(open(os.path.join(SPECS, "L261111-hyundai-robot.json"), encoding="utf-8"))
OUT_DIR = os.environ.get("OUT_DIR", SPECS)
BANNED = {"commons_handshake_1.jpg", "commons_handshake_2.jpg", "commons_samsungfab_1.jpg", "commons_pyeongtaek_1.jpg", "commons_pyeongtaek_2.jpg"}
USED = {}; WARN = []
def find(name):
    if "." in name and os.path.exists(os.path.join(LIB, name)): return name
    for e in (".mp4", ".jpeg", ".jpg", ".png"):
        if os.path.exists(os.path.join(LIB, name + e)): return name + e
    raise SystemExit("없는 소재: " + name)
def R(n):
    p = find(n); assert p not in BANNED, p
    if p in USED: WARN.append(p)
    USED[p] = USED.get(p, 0) + 1
    return p
def syl(t): return len(re.findall(r"[가-힣0-9A-Za-z]", t))
def P(text, line=0, at=0.05, **k): return dict(kind="print", text=text, line=line, at=at, **k)
def b(label, v, text, color): return {"label": label, "v": v, "text": text, "color": color}
def BARS(title, items, at=0.4, line=0): return [P(title, line=line), {"kind": "bars", "items": items, "line": line, "at": at}]
def PCT(items, at=0.3, line=0, dec=1):
    return {"kind": "pct", "items": items, "line": line, "at": at, "scale": round(190 / max(abs(i["v"]) for i in items), 2), "gap": 400, "dec": dec}
def TB(cols, rows, colors, at=0.3, line=0): return {"kind": "table", "cols": cols, "rows": rows, "colors": colors, "line": line, "at": at}
def PU(text, sub, at=0.4, color="gold", hold=2.0, soft=True, **k):
    d = dict(kind="punch", text=text, sub=sub, line=0, at=at, color=color, hold=hold, **k)
    if soft: d["style"] = "soft"
    return d
def IC(name, text, at=0.3, color="gold"): return dict(kind="icon", name=name, text=text, line=0, at=at, color=color)
def LOW(text, sub, at=0.15): return dict(kind="lower", text=text, sub=sub, line=0, at=at)
def QU(rows, by, at=0.3): return dict(kind="quote", rows=rows, by=by, line=0, at=at)

LN = {}  # (chapter, idx) -> line
for ci, (_, lines) in enumerate(SCRIPT):
    for li, t in enumerate(lines): LN[(ci, li)] = t
S = []; CHP = []; REPORT = []
def T(title): CHP.append(title)
def M(ref, cuts, sketch=None, src="", cold=False, first=False):
    lines = [LN[ref]]
    cs = [R(c) for c in cuts]
    secs = sum(syl(t) for t in lines) / 6.5
    REPORT.append((round(secs, 1), len(cs), round(secs / len(cs), 1), lines[0][:20]))
    v = {"type": "media", "full": True, "wash": "none" if cold else "left", "cuts": [{"lib": c} for c in cs]}
    if cold:
        v.update(cine=True, doc_cine=True)
        if sketch and any(x.get("kind") in ("table", "bars", "chart", "pct") for x in sketch): v.update(wash="left", wash_amt=0.85)
    else: v["wash_amt"] = 0.85
    s = {"v": v, "lines": lines, "sketch_add": [], "en": [""], "asof": False, "src": src, "sketch": sketch or []}
    if cold: s.update(lead=0.0 if first else 0.08, hold=0.12)
    if CHP: s["chapter"] = CHP.pop()
    S.append(s)

FN = "파이낸셜뉴스 2026-11-10 (11/9 뉴욕 종가)"
PR = "프레시안·이슈온 2026-11-10 (반도체지수 +6.86%, 엔비디아 장중 -8.8%)"
AP = "AP(KSAT) 2026-11-10 · 이코리아 2026-11-10(로이터 인용)"
NYT = "뉴욕타임스 보도 인용 (AP 2026-11-10 · CBS 2026-11-09)"
DX = "디렉시온 · 지수 구성 2026-03-31 (엔비디아 8.41%)"
SA = "StockAnalysis SOXL 시세 (11/5 40.87달러)"
VX = "Cboe VIX · Yahoo Finance (11/6 25.64) · 파이낸셜뉴스 (11/9 19.92)"
NV = "엔비디아 IR 2026-10-28 · 11/17 오후 1시 20분(태평양 시각) 발표"
CPI = "미국 노동부 10월 CPI (CBS·Kitco 2026-11-10)"
NV8K = "엔비디아 2027 회계연도 2분기 실적 (SEC 8-K)"
H22 = "머니투데이 2022 · 지난 SOXL 편(L261107-soxl-38) 자료"
FINE = "참고 기준 · 매수·매도 권유 아님"

# ── [훅] 11/9 장면 → [역설] → [약속] → [예고]
M((0,0), ["vstockmarket_47213", "commons_nvidiahq_2", "il_L261107s_chip_crack"], [PU("-8.8%", "엔비디아 장중 하락폭 · 2026.11.9", color="red", at=0.6, hold=1.8, soft=False)], src=PR, cold=True, first=True)
M((0,1), ["vspy_14090", "vsingapore_20174", "vsecret_49379"], [LOW("젠슨 황", "엔비디아 CEO · 의혹 보도 · 확인 전", at=0.4)], src=NYT, cold=True)
M((0,2), ["il_L261107s_seoul_bed_phone", "il_L261107s_phone_red"], [], cold=True)
M((0,3), ["vwallstreet_4842", "vstockmarket_47214"], [TB(["엔비디아", "SOXL"], [["-4.3%", "+22.3%"]], ["red", "green"], at=0.2)], src=FN, cold=True)
M((0,4), ["vstockmarket_47012", "chip_47048"], [], cold=True)
M((0,5), ["vdetective_32780", "vsilhouette_33968"], [], cold=True)
M((0,6), ["il_L261107s_dawn_phone", "il_L261104g_morning_phone"], [PU("06:20", "11월 18일 · 엔비디아 실적 발표 (한국 시각)", at=1.6, hold=1.8, clock=True)], src=NV, cold=True)
M((0,7), ["il_L261107s_deep_valley", "vstockmarket_9607"], [PU("-90%", "SOXL · 2022년", color="red", at=1.0, hold=1.6, soft=False)], src=H22, cold=True)
ident = copy.deepcopy(soxl["scenes"][9]); ident.pop("dur", None); ident["lines"] = [LN[(1,0)]]; ident["en"] = [""]; S.append(ident)
# ── 결론 먼저
M((2,0), ["commons_datacenter_1", "vdata_21053", "server_7863"], [TB(["SOXL 변수", "무게"], [["젠슨 황 개인", "작음"], ["엔비디아 실적", "큼"]], ["gray", "gold"], at=1.5)])
M((2,1), ["il_L261107s_closing_floor", "vanalytics_5462"], [LOW("지난 영상", "SOXL 주가 전망 · 2026.11.7 · 원리 설명", at=0.6)])
# ── 1장
T("확인된 것과 의혹")
M((3,0), ["commons_nvidiahq_3", "vmeeting_4809"], [TB(["확인", "의혹"], [["불륜 인정 · 이사회 조사", "중국 정보기관 연계"]], ["green", "red"], at=0.4)])
M((3,1), ["vdocuments_48385", "vnewspaper_41199", "vcourt_46820"], [LOW("엔비디아 이사회", "2026.11.8 · 독립 조사 착수", at=1.6)], src="엔비디아 이사회 성명 · CBS 2026-11-09")
M((3,2), ["vsingapore_30998", "datacenter_23282", "vdocuments_22856"], [PU("48억 달러", "메가스피드 · 엔비디아 칩 구매액 · 약 6조 5천억 원", at=2.2, hold=1.8)], src=NYT)
M((3,3), ["il_L261107m_cargo_chips", "server_23215"], [IC("warning", "미국 상무부 · 수출 규제 우회 조사 (보도)", at=0.3)], src=AP)
M((3,4), ["vnewspaper_41192", "vconference_23116", "vcontract_23112"], [])
M((3,5), ["il_L261108p_us_courtroom", "vcourt_47602"], [LOW("주주 집단소송", "2026.11.9 · 캘리포니아 산호세 연방법원", at=0.6)], src=AP)
M((3,6), ["vsurveillance_23988", "vstockmarket_47792"], [])
# ── 2장
T("엔비디아가 빠진 날")
M((4,0), ["vsemiconductor_1138", "chip_47051"], [IC("chip", "반도체 30종목 지수 × 하루 3배", at=0.3)], src="디렉시온 상품 설명")
M((4,1), ["commons_nvidiagpu_2", "commons_hbm_1", "vsemiconductor_1139"], [PU("약 8%", "지수 내 엔비디아 비중", at=0.5, hold=1.8)], src=DX)
M((4,2), ["vdata_5404", "commons_micronfab_1", "chip_47258"], [P("2026.11.9 하루 등락"), TB(["AMD", "브로드컴", "마이크론", "엔비디아"], [["+13.3%", "+8.8%", "+6.3%", "-4.3%"]], ["green", "green", "green", "red"], at=0.35)], src=FN)
M((4,3), ["vnightcity_40746", "vanalytics_41277", "vnewspaper_34190"], [])
M((4,4), ["commons_nasdaqsite_2", "vstockmarket_47016"], [TB(["반도체지수", "SOXL"], [["+6.9%", "+22.3%"]], ["green", "green"], at=0.4)], src=PR + " · " + FN)
M((4,5), ["vcomputer_308"], [PU("-0.3%", "엔비디아 하락이 지수에 준 영향", color="red", at=0.6, hold=1.6)], src="8% × -4.27% 계산")
M((4,6), ["vbusinessman_8941", "vofficebuilding_40652"], [])
M((4,7), ["vnetwork_31536", "il_L261107m_storm_tower"], [])
M((4,8), ["commons_datacenter_4", "vdata_14724"], [])
M((4,9), ["il_L261110a_server_aisle", "commons_hbm_2", "vnetwork_26778"], [TB(["빅테크 AI 투자", "→ 엔비디아", "→ 메모리·통신 칩"], [["데이터센터", "GPU 매출", "마이크론 · 브로드컴"]], ["gray", "gold", "gold"], at=1.0)])
M((4,10), ["vsatellite_47399", "il_L261107m_dc_cooling", "vsemiconductor_1141"], [TB(["변수", "범위"], [["CEO 스캔들", "한 종목"], ["실적 전망", "지수 전체"]], ["gray", "gold"], at=1.8)])
# ── 3장
T("지난 영상의 조건 3개")
M((5,0), ["il_L261109p_calc_notebook", "vtyping_41183"], [TB(["1차", "2차", "3차"], [["저점 2주", "VIX 20", "엔비디아 실적"]], ["gold", "gold", "gold"], at=1.0)], src="지난 SOXL 편 · 2026.11.7")
M((5,1), ["il_L261107s_rollercoaster", "il_L261107m_trading_red"], BARS("SOXL 종가 (달러)", [b("11월 5일", 40.87, "40.87", "red"), b("11월 9일", 56.2, "56.20", "green")], at=1.6), src=SA + " · " + FN)
M((5,2), ["il_L261107s_calendar_flip", "vcomputer_46635"], [IC("down", "① 저점 유지 · 확인일 11월 19일", at=0.3)], src=FINE)
M((5,3), ["il_L261107m_hourglass", "vanalytics_42648"], BARS("VIX 종가", [b("11월 6일", 25.64, "25.64", "red"), b("11월 9일", 19.92, "19.92", "green")], at=1.8), src=VX)
M((5,4), ["il_L261107s_clock_close"], [IC("warning", "② 20 아래 첫날 · 일주일 확인 전", at=0.3)], src=VX)
M((5,5), ["il_L261105k_cin_phone", "il_L261107m_subway_phone"], [LOW("엔비디아 3분기 실적", "11월 18일 새벽 6시 20분 · 한국 시각", at=1.6)], src=NV)
M((5,6), ["vmoney_45703", "coins_18263_a.jpg"], [TB(["6월 고점", "11월 5일", "11월 9일"], [["1,000만 원", "136만 원", "약 187만 원"]], ["gray", "red", "gold"], at=1.2)], src="SOXL 종가 기준 계산 (300 → 40.87 → 56.20달러)")
M((5,7), ["il_L261107s_red_cliff", "vmoney_47005"], [PU("5.3배", "원금 회복에 필요한 상승", color="red", at=1.4, hold=1.6)], src="300 ÷ 56.20 계산")
M((5,8), ["il_L261107s_hands_cross", "vdetective_49252"], [])
M((5,9), ["il_L261107s_ice_melt"], [])
# ── 4장
T("새 변수, 금리 인상")
M((6,0), ["vgrocery_23062" if False else "money_18296_a.jpg", "vmoney_18296"], [TB(["10월 소비자물가", "시장 예상"], [["+0.4%", "+0.3%"]], ["red", "gray"], at=1.0)], src=CPI)
M((6,1), ["commons_eccles_1", "il_L261105g_cin_fedbuilding", "commons_eccles_2"], [PU("84%", "12월 금리 인상 확률 · CPI 발표 전", color="red", at=1.6, hold=1.8)], src="Kitco 2026-11-10 (금리 선물)")
M((6,2), ["commons_ustreasury_1"], [IC("up", "미국 10년 국채 금리 4.9%대", at=0.2, color="red")], src="Kitco 2026-11-10")
M((6,3), ["il_L261104g_fed_winter", "vnewyork_33965"], [])
M((6,4), ["il_L261107s_red_wave", "il_L261104g_screens_red"], BARS("2022년 10월까지 하락", [b("반도체지수", 46, "-46%", "gray"), b("SOXL", 90, "-90%", "red")], at=1.6), src=H22)
M((6,5), ["vtyping_242"], [TB(["2022년", "2026년"], [["금리 인상", "금리 인상"], ["수요 감소", "AI 수요 유지"]], ["gray", "gold"], at=0.4)])
M((6,6), ["vdata_50749", "il_Y261105_a_server", "commons_nvidiagpu_3"], BARS("엔비디아 분기 매출 (달러)", [b("직전 분기", 96.2, "962억", "gray"), b("이번 분기 전망", 108, "1,080억", "gold")], at=2.2), src=NV8K)
M((6,7), ["il_L261107s_plate_slices", "vnewyork_30544"], [])
M((6,8), ["il_L261107s_dawn_phone" if False else "vairplane_28000", "commons_nvidiahq_1"], [])
# ── 5장
T("11월 18일 새벽 6시 20분")
M((7,0), ["vpresentation_24068"], [])
M((7,1), ["vanalytics_41278_a.jpg", "il_L261107m_earnings_call"], [IC("dollar", "① 다음 분기 매출 전망 · 시장 기대 대비", at=0.2)], src=FINE)
M((7,2), ["server_47050", "vdata_23061" if os.path.exists(os.path.join(LIB, "vdata_23061.mp4")) else "server_24033"], [IC("server", "② 데이터센터 매출 · 증가 속도", at=0.2)], src=FINE)
M((7,3), ["vwashington_22788", "vpresentation_24173", "vcapitol_49851"], [IC("globe", "③ 수출 규제 영향 · 경영 공백 답변", at=0.2)], src="미국 하원 3개 위원회 · 11/18 비공개 설명 요구")
M((7,4), ["il_L261107s_globe_line"], [], src=FINE)
M((7,5), ["vnewyork_4442", "il_L261107s_chip_stairs"], [TB(["3가지 유지", "다음 단계"], [["저점 2주 · VIX 일주일 확인", "분할 자금 집행"]], ["green", "gold"], at=1.0)], src=FINE)
M((7,6), ["il_L261107s_cracked_glass", "laptop_4713", "vcomputer_1781_a.jpg"], [TB(["3배 상품 비중", "90% 하락 시 전체 자산"], [["20%", "-18%"], ["40%", "-36%"]], ["gray", "red"], at=1.8)], src="2022년형 하락 가정 계산 · " + FINE)
M((7,7), ["vsemiconductor_1140", "commons_micronfab_2"], [IC("chip", "1배 반도체 ETF · 리밸런싱 손실 없음", at=0.3)], src=FINE)
M((7,8), ["il_L261107m_loan_desk", "vmoney_18261"], [IC("bank", "신용·주택담보대출 매수 금지", at=0.2, color="red")], src=FINE)
# ── [북엔드]
M((8,0), ["vwallstreet_24517", "vwallstreet_24515"], [])
M((8,1), ["vnetwork_19653", "vnightcity_49878"], [])
M((8,2), ["il_L261110a_midnight_phones", "il_L261107s_dawn_phone" if False else "vnightcity_40747"], [])
M((8,3), ["phone_4915", "il_L261110a_search_phone"], [])
M((8,4), ["vsatellite_46148", "sunrise_6734_a.jpg"], [])
M((8,5), ["space_18772", "phone_14669"], [])
S.append({"v": {"type": "end", "sub": "", "btn_at": ["0:좋아요", "0:구독", "0:구독"], "note": {"text": ""}, "closing_photo": "vsatellite_47401.mp4", "backdrop": "commons_datacenter_2.jpg", "bd_dim": 0.74},
          "lines": [LN[(8,6)]], "endscreen": 9, "sketch_add": [], "en": [""], "asof": False, "src": ""})

TITLE = "SOXL 주가 전망, 엔비디아 -4% 날 SOXL은 +22% | 젠슨 황 리스크보다 11월 18일 실적이 중요한 이유"
spec = {k: base[k] for k in ["fx", "format", "world", "notebook", "hook", "overlay"]}
spec["look"] = {"paper": "grain", "dark": "navy", "accent": "red"}
spec["music"] = copy.deepcopy(pep["music"])
spec.update({"id": "L261112-soxl-nvidia", "company": "SOXL", "no_data": True, "series": "SOXL 물타기 해도 될까?", "plan": "P261112u-soxl-nvidia",
 "scheduled_at": "2026-11-12T11:30:00+09:00",
 "events": [{"at": "2026-11-11T02:30:00+09:00", "by": "claude-long", "what": "긴급 제작 (대표 채팅 11/11 01:20) — 원고·렌더 동시"}],
 "opening": "장면형(11/9 엔비디아 장중 -8.8%) + 역설(엔비디아 -4.3% vs SOXL +22%) + 보유자 약속 + 2022년 예고",
 "hook_type": "H11 비교(모순) + 보유자 대응 힌트",
 "endscreen_target": "L261109-nvidia-huang",
 "endscreen_also": "L261107-soxl-38",
 "title": TITLE, "doc_title": "엔비디아가 흔들린 날 SOXL이 오른 이유, 그리고 11월 18일 새벽에 볼 숫자 3개",
 "title_en": "SOXL outlook: NVIDIA fell 4% but SOXL rose 22% — why Nov 17 earnings matter more than the Jensen Huang scandal",
 "tags": ["soxl 전망", "soxl", "soxl 주가", "SOXL 주가 전망", "엔비디아 주가 전망", "엔비디아 주가 하락 이유", "젠슨 황", "엔비디아 실적 발표", "soxl 물타기", "soxl 장기투자", "반도체 3배 ETF", "메가스피드"],
 "search_keywords": ["soxl 전망", "soxl 주가", "엔비디아 주가 전망", "엔비디아 실적 발표", "soxl 물타기"],
 "sources": [FN + " (SOXL 56.20달러 +22.25%, 엔비디아 178.67달러 -4.27%, AMD +13.26%, 브로드컴 +8.78%, 마이크론 +6.25%, VIX 19.92)", PR, AP + " (집단소송·상무부 조사 보도·메가스피드 48억 달러)", NYT, DX, SA, VX, NV, CPI + " (+0.4%, 예상 0.3% · 12/8~9 FOMC · 인상 확률 84%(발표 전) · 10년물 4.94%)", NV8K, H22,
   "그림: AI 생성 스틸(실존 인물 아님) · 사진: Wikimedia Commons · 영상: Mixkit·Pexels · 음악: Pixabay"],
 "pinned_comment": "11월 18일 새벽 엔비디아 실적에서 여러분은 어떤 숫자를 가장 먼저 보실 건가요? (다음 분기 매출 전망 / 데이터센터 매출 / 설명회 답변)\n\n▶ 젠슨 황 사건 총정리: 엔비디아 젠슨 황 편\n▶ SOXL 원리와 물타기 기준: 지난 SOXL 주가 전망 편\n\n※ 영상 속 분할·비중 기준은 참고 기준이며 매수·매도 권유가 아닙니다. 중국 정보기관 연계는 보도된 의혹이며 확인된 사실이 아닙니다.\n좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다.",
 "description_head": "SOXL 주가 전망, 엔비디아 주가가 젠슨 황 리스크로 4.3% 빠진 11월 9일 SOXL은 22% 올랐습니다.\nSOXL 보유자가 볼 것은 젠슨 황 기사보다 11월 18일 새벽(한국 시각) 엔비디아 실적 발표입니다.\n\n엔비디아 비중이 약 8%인 반도체지수 구조, 지난 SOXL 영상의 추가 매수 조건 3개 중간 점검(11/5 저점·VIX·실적), 10월 CPI와 12월 금리 인상이라는 새 변수, 2022년 SOXL -90%와 닮은 점·다른 점, 실적에서 확인할 3가지와 결과별 대응 기준을 정리했습니다.\n\n※ 참고 기준이며 매수·매도 권유가 아닙니다. 중국 정보기관 연계는 보도된 의혹입니다.",
 "description_en": "On Nov 9, NVIDIA fell 4.3% on the Jensen Huang reports, yet SOXL rose 22%. We explain why, check the three conditions from our last SOXL video, add the new rate-hike risk, and list three things to check in NVIDIA's Nov 17 earnings.",
 "hook_promises": ["11월 18일 실적에서 확인할 3가지", "결과별 대응 기준", "2022년과 닮은 점 하나"],
 "viewer_question": "젠슨 황 리스크에 SOXL 보유자는 무엇을 봐야 하나",
 "format_note": "긴급 7분 내외(대표 지시 6~7분, 118 예외). 원리 재설명 없이 지난 SOXL 편으로 넘김. 젠슨 황 편 소재 재사용. 실존 인물 사진 없음. 다음 영상 이름 엔딩 언급 없음. 투자 경력 언급 없음.",
 "thumb": {"photo": "commons_nvidiahq_2.jpg", "focus_x": 0.6, "l1": "엔비디아 -4%인 날", "l2": "SOXL은 왜 +22%?", "pos": "left"},
 "ab_sets": [{"key": "a", "default": True, "title": TITLE, "file": "thumb_a.jpg", "type": "A 보유자·사건 · 모순(H11)"},
             {"key": "b", "title": "SOXL 주가 전망, 젠슨 황 리스크에 흔들릴 때 보유자가 확인할 3가지 | 엔비디아 실적 11월 18일", "file": "thumb_b.jpg", "type": "B 젠슨 황 리스크형(실사 인물 없음)"},
             {"key": "c", "title": "엔비디아 실적 발표 11월 18일 새벽, SOXL·반도체 갖고 계신 분이 확인할 3가지", "file": "thumb_c.jpg", "type": "C 범용 · 실적 D-7"}],
 "scenes": S})
for s_ in spec["scenes"]:
    if s_.get("lines") and s_.get("sketch"):
        ls = max(1.0, syl(s_["lines"][0]) / 6.5)
        for e_ in s_["sketch"]:
            if e_.get("at", 0) > 0.75: e_["at"] = round(min(0.6, e_["at"] / ls), 2)
    if s_["v"].get("cine"):
        for e_ in s_.get("sketch") or []:
            if e_.get("kind") == "lower": e_["y"] = 540
os.makedirs(OUT_DIR, exist_ok=True)
out = os.path.join(OUT_DIR, "L261112-soxl-nvidia.json")
json.dump(spec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
spoken = [x for sc in S for x in sc.get("lines", [])]; expected = [x for c, l in SCRIPT for x in l]
assert spoken == expected, "불일치"
tot = sum(syl(t) for t in spoken); nums = sum(1 for t in spoken if re.search(r"[0-9]", t))
print("scenes", len(S), "syl", tot, "est", round(tot / 6.5), "s · 숫자 문장 비율", round(nums / len(spoken), 2))
print("긴 컷:", [r for r in REPORT if r[2] > 4.6])
print("반복:", sorted(set(WARN)))
