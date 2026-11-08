# 2026-11-09 팔란티어 롱폼 — 대표 확정 원고 v2(yt_plans P261110-palantir-what data.script) 그대로
# 사용: python3 scripts/youtube/long/drafts/_build_L261109-palantir.py → specs/L261109-palantir-what.json
import json, os, copy, re, math
HERE = os.path.dirname(os.path.abspath(__file__)); SPECS = os.path.join(HERE, "..", "specs")
LIB = os.path.join(HERE, "..", "..", "..", "blog", "media", "lib")
SCRIPT = json.load(open(os.path.join(HERE, "_script_L261109-palantir.json"), encoding="utf-8"))
base = json.load(open(os.path.join(SPECS, "L261108-lev-91.json"), encoding="utf-8"))
soxl = json.load(open(os.path.join(SPECS, "L261107-soxl-38.json"), encoding="utf-8"))
OUT_DIR = os.environ.get("OUT_DIR", SPECS)
BANNED = {"commons_samsungfab_1.jpg", "commons_pyeongtaek_1.jpg", "commons_pyeongtaek_2.jpg"}
PREV = set()
for sid in ("L261107-soxl-38", "L261108-lev-91", "L261107-midterm-ai", "L261108-pepero-day"):
    for sc in json.load(open(os.path.join(SPECS, sid + ".json"), encoding="utf-8"))["scenes"]:
        v = sc["v"]
        for c in v.get("cuts", []): PREV.add(c["lib"] if isinstance(c, dict) else c)
        for k in ("lib", "closing_photo", "backdrop"):
            if v.get(k): PREV.add(v[k])
FINE = "매수·매도 권유 아님"
USED = {}; WARN = []; used_vid = {}

def resolve(tok):
    name = "il_L261109p_" + tok[2:] if tok.startswith("I:") else ("il_" + tok if re.match(r"[LY]26", tok) else tok)
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

Q3 = "팔란티어 2026년 3분기 실적(SEC 8-K, 11월 2일)"
# ---------- 훅 ----------
M((0,0), ["I:dots_city", "I:file_network"], [LOW("음모론 영상 속 주장", "확인된 사실 아님 · 회사 부인", at=0.15)], src="음모론 주장 · 확인된 사실 아님 (회사 부인)", cold=True, first=True)
M((0,1), ["I:analyst_wall", "vsurveillance_23016"], [LOW("Palantir (PLTR)", "미국 데이터 분석 소프트웨어 기업", at=0.3)], cold=True)
M((0,2), ["I:leak_screen", "vhacker_46639", "vsecret_50745", "vdata_21053", "vhacker_34838"], [P("2011 · HBGary 유출 문건")], src="iTnews 2011 · 위키백과 HBGary", cold=True)
M((0,3), ["vsoldier_5932", "commons_pentagon_3", "commons_ussupremeish_2"], [TB(["출발", "2016 소송"], [["CIA 투자 조직", "미 육군 상대"]], ["gold", "red"], at=0.25)], src="Global Venturing 2014 · Defense News 2019", cold=True)
M((0,4), ["I:gov_vs_corp", "I:sell_board_blue", "vstockmarket_47213"], [CH([209.05, 160.38], ["2026.10.9", "2026.11.6"], ["209달러", "160달러"], at=0.45)], src="StatMuse · StockAnalysis (종가 기준)", cold=True)
M((0,5), ["vanalytics_5462", "vdata_5404"], [PU("+96%", "3분기 전체 매출 · 전년 동기 대비", color="green", at=0.1, soft=False, hold=2.0)], src=Q3, cold=True)
M((0,6), ["vprogramming_41654", "vcontract_28362", "I:contract_cash"], BARS("미국 기업 신규 계약 증가율", [b("2분기", 153, "+153%", "gray"), b("3분기", 11, "+11%", "red")], at=0.55), src=Q3, cold=True)
M((0,7), ["I:money_loop", "vhandshake_30016", "vhandshake_24047"], [TB(["투자 금액", "수취 계약"], [["800만 달러", "800만 달러"]], ["gold", "gold"], at=0.55)], src="Fortune 2021-11-24 · 블랙스카이 사례", cold=True)
M((0,8), ["I:calc_notebook", "vtyping_41183"], [LOW("평단", "평균 매수 단가", at=0.25)], cold=True)
ident = copy.deepcopy(soxl["scenes"][9]); ident.pop("dur", None); ident["lines"] = [L(1,0)]; ident["en"] = [""]; S.append(ident)

# ---------- 결론 먼저 ----------
CH_PENDING.append("결론 먼저")
M((2,0), ["vofficebuilding_40701", "vcomputer_308", "vanalytics_41277"], BARS("3분기 매출", [b("2025년", 11.81, "11.8억 달러", "gray"), b("2026년", 23.13, "23.1억 달러", "gold")], at=0.45), src=Q3)
M((2,1), ["vnetwork_26778", "I:ai_rivals", "vcontract_23222"], [], src="")
M((2,2), ["I:weigh_balance", "vtyping_242"], [IC("dollar", "신규 계약 금액", at=0.3), IC("warning", "계좌 내 비중", at=0.6)], src=FINE)

# ---------- 음모론 ----------
T("음모론은 어디까지 사실인가", "확인된 사실과 미확인 주장")
M((3,0), ["I:border_night", "vwashington_22788", "vcapitol_40700", "vsecuritycamera_48922", "vsurveillance_23673"], [P("2025.4 · 미국 이민세관단속국(ICE)"), P("약 3천만 달러 · 수의 계약", at=0.45)], src="The Register 2025-04-21")
M((3,1), ["commons_nytbuilding_2", "vnewspaper_34190", "vnews_41204"], [], src="뉴욕타임스 2025 보도 (AOL 인용)")
M((3,2), ["vdata_50749", "I:locked_drive", "vnetwork_31536", "vdata_14724"], [TB(["보도 내용", "회사 입장"], [["시민 정보 통합", "통합 DB 미구축"], ["개인정보 활용", "수집·판매 없음"]], ["gray", "gold"], at=0.15)], src="회사 공식 입장 (2025)")
M((3,3), ["vsurveillance_22997"], [LOW("국민 전체 감시 주장", "확인된 사실 아님 · 회사 부인", at=0.1)])
M((3,4), ["vcapitol_49851", "vwashington_22787", "vwashington_22784", "vunitedstates_19414", "vcapitol_40677"], BARS("3분기 매출 구성", [b("미국 정부", 41, "41%", "gold"), b("그 외", 59, "59%", "gray")], at=0.55), src=Q3)
M((3,5), ["vofficebuilding_31663", "vnewyork_30544"], [])

# ---------- 코카콜라 ----------
T("코카콜라가 거절한 회사", "2015~2016 · 비싼 소프트웨어")
M((4,0), ["vofficebuilding_40652", "vcontract_23112", "I:boardroom_empty"], [], src="BuzzFeed News 2016")
M((4,1), ["L261105h_contract", "commons_goldcert_2", "L261105k_cin_ledger"], BARS("2015년 · BuzzFeed 입수 자료", [b("계약 실적", 17, "17억 달러", "gray"), b("유입 현금", 4.2, "4.2억 달러", "red")], at=0.45), src="BuzzFeed News 2016 (내부 자료 보도)")
M((4,2), ["commons_cokehq_1", "commons_cokehq_3", "commons_sodabottles_1", "commons_amextower_2", "vnewyork_4442", "commons_nasdaqsite_2"], [TB(["기업", "결과"], [["코카콜라", "계약 거절"], ["아메리칸익스프레스", "18개월 후 종료"], ["나스닥", "협상 중단"]], ["gray", "red"], at=0.1)], src="BuzzFeed News 2016 보도")
M((4,3), ["I:box_exit", "vconference_23116", "vmeeting_4809"], [], src="BuzzFeed News 2016")
M((4,4), ["vmeeting_15716", "vhandshake_46755"], [], src="SiliconANGLE 2016-05-09")
M((4,5), ["L261105h_archive", "vnewspaper_41199"], [])

# ---------- 뉴욕 경찰 ----------
T("데이터를 돌려받지 못한 뉴욕 경찰", "2017 · 시스템 전환 분쟁")
M((5,0), ["commons_nypdcar_2", "commons_ibmbldg_2"], [P("2017 · 뉴욕 경찰(NYPD)"), P("팔란티어 → IBM 시스템 전환", at=0.4)], src="Brennan Center 2017-07-20")
M((5,1), ["I:police_desk", "vpolice_47491"], [])
M((5,2), ["commons_onepoliceplaza_1", "vcourt_46820", "commons_uscourthouse_1"], [IC("warning", "지식재산권 분쟁", at=0.35, color="red")], src="Brennan Center 2017-07-20")
M((5,3), ["commons_nypdcar_4", "vdetective_32780"], [])
M((5,4), ["I:key_lockin", "vsecret_49379"], [])
M((5,5), ["vanalytics_41278", "vcomputer_46635"], BARS("고객 1곳당 지출", [b("지난해", 100, "100달러", "gray"), b("올해", 165, "165달러", "gold")], at=0.3), src="3분기 실적 설명회 · 순매출 유지율 165%")
M((5,6), ["vconference_13192", "vnewyork_26920"], [PU("1억 4,600만 달러", "상위 20개 고객 · 최근 12개월 평균 매출", at=0.2)], src="3분기 실적 설명회")
M((5,7), ["vwallstreet_24517"], [])

# ---------- 스팩 ----------
T("고객사에 돈을 넣어 준 회사", "2021 · 스팩 투자")
M((6,0), ["commons_nasdaqsite_1", "I:shell_door", "vwallstreet_24515", "vprogramming_1728"], [P("2020.9 상장 · 스팩 급증기"), IC("building", "비상장사 + 상장용 빈 회사", at=0.55)], src="Fortune 2020-09-30")
M((6,1), ["vconference_13222", "commons_handshake_1", "vunitedstates_4334"], [PU("4억 달러 이상", "스타트업 20여 곳 투자 약정", at=0.25)], src="Fortune 2021-11-24")
M((6,2), ["I:satellite_earth", "vsatellite_47399", "space_45037", "space_5292"], BARS("블랙스카이 사례", [b("팔란티어 투자", 800, "800만 달러", "gold"), b("수취 계약", 800, "800만 달러", "gold")], at=0.5), src="Fortune 2021-11-24")
M((6,3), ["vpresentation_24068", "vofficebuilding_41541", "vbusinessman_22961", "vnewyork_33965"], [LOW("월가 애널리스트 평가 (2021)", "RBC · 씨티그룹 — 매출 품질 의문", at=0.45)], src="Fortune 2021-11-24")
M((6,4), ["L261105h_analyst", "commons_archiveboxes_2"], BARS("2021년 3분기 민간 매출 증가율", [b("회사 발표", 37, "37%", "gray"), b("씨티 추정", 22, "22%", "red")], at=0.4), src="Fortune 2021-11-24 · 씨티그룹 추정")
M((6,5), ["I:crash_spac", "L261105h_ticker", "L261104g_lehman_boxes"], [PCT([{"label": "투자 스타트업 가치", "v": -80, "mark": "2022년 말 평균"}], at=0.2, dec=0), P("2022.12.27 주가 5.92달러", at=0.7)], src="Motley Fool 2023-06-05 · TradingView")
M((6,6), ["L261105h_certs", "vsemiconductor_1140", "vnews_14111"], [PU("0.02% 미만", "전략 계약 3분기 매출 비중", at=0.35)], src="3분기 실적 설명회")
M((6,7), ["vsemiconductor_1141"], [])
M((6,8), ["I:bootcamp", "vpresentation_9069", "vcomputer_9757"], [P("2023 · AI 플랫폼 AIP 출시")], src="2023년 4분기 실적 설명회")
M((6,9), ["I:factory_control", "factory_17675_a", "commons_msftcampus_1", "commons_sfskyline_1", "vnetwork_19653"], BARS("3분기 미국 매출", [b("미국 기업", 9.84, "9.84억 달러", "gold"), b("미국 정부", 9.53, "9.53억 달러", "gray")], at=0.5), src=Q3)
M((6,10), ["vhacker_46627"], [])

# ---------- 주가 ----------
T("주가가 빠진 뒤 다시 본 숫자", "2026년 3분기 실적")
M((7,0), ["commons_timessquare_2", "vhacker_46634", "vcomputer_1781"], [PCT([{"label": "11월 5일", "v": -9.73}], at=0.1, dec=1)], src="Beinsure 2026-11-06")
M((7,1), ["L261105h_handshake", "Y261108n_dossier", "commons_stockcert_2", "commons_archiveboxes_1", "vsecuritycamera_23268"], [], src="증권사 리포트 요약 · Motley Fool 11/5·11/6")
M((7,2), ["L261105k_cin_exchange", "vsemiconductor_1138", "vsurveillance_23988", "commons_msftcampus_2"], BARS("미국 기업 신규 계약 금액", [b("2분기", 21.32, "21.3억 달러", "gray"), b("3분기", 14.63, "14.6억 달러", "red")], at=0.3), src=Q3)
M((7,3), ["commons_msftdc_1", "commons_ustreasury_1", "commons_msftdc_3"], [TB(["계약 기간", "기록 금액"], [["3년", "100"], ["1년", "약 33"]], ["gray", "gold"], at=0.4)], src="3분기 실적 설명회 · 회사 설명")
M((7,4), ["commons_padlock_1"], [])
M((7,5), ["vsatellite_46148", "space_45036", "vunitedstates_26828"], BARS("민간 매출 증가율", [b("미국 기업", 148, "+148%", "gold"), b("미국 밖", 21, "+21%", "gray")], at=0.35), src="3분기 실적 설명회")
M((7,6), ["commons_openaihq_1", "space_23203", "vsemiconductor_1139"], [IC("server", "AI 모델사 직접 거래", at=0.35)], src="3분기 실적 설명회")
M((7,7), ["commons_seoulnight_3", "L261105h_safeempty", "commons_bankvault_1"], [PU("약 520조 원", "시가총액 · 11/6 종가, 1,355원 환산", at=0.55)], src="StockAnalysis · KB Think 2026-11-06")
M((7,8), ["commons_goldcert_1", "vsilhouette_34041", "coins_47017_a", "commons_stockcert_1"], [PU("113배", "주가 ÷ 1주당 연간 이익 (PER)", at=0.15, color="red", soft=False)], src="StockAnalysis · PER 112.98 (11/6)")
M((7,9), ["chess_5339", "commons_wafer_3", "commons_chessknight_2"], [P("PER 30배 = 이익 약 3.8배"), TB(["연 성장", "소요 기간"], [["2배", "2년"], ["30%", "5년"]], ["gray", "gold"], at=0.3)], src="계산: 이익 3.8배 기준 · " + FINE)

# ---------- 창업자 ----------
T("창업자들이 한 일", "내부자 매도와 의결권")
M((8,0), ["I:insider_exit"], [])
M([(8,1),(8,2),(8,3)], ["commons_sfskyline_2", "commons_googleplex_1", "commons_msftsign_1", "commons_ustreasury_2", "L261105h_chess", "commons_msftsign_2", "commons_googleplex_2", "commons_grandsalon_1"],
  [{"kind": "bars", "items": [b("피터 틸", 290, "2.9억", "gold"), b("알렉스 카프", 86, "0.86억", "gold"), b("샴 산카르", 47, "0.47억", "gold")], "line": 0, "at": 0.3}, P("2026년 내부자 매도 (달러)")], src="Startup Fortune 2026-09")
M((8,4), ["I:founders_key", "commons_chessknight_1"], [], src=FINE)
M((8,5), ["I:ballot_small", "commons_auctiongavel_1"], [PU("49.999999%", "공동 창업자 3명 · 의결권 상한", at=0.4)], src="SEC 10-Q 2026-06-30")
M((8,6), ["commons_ladefense_1", "vdetective_49252"], [])
M((8,7), ["vnetwork_4916"], [])

# ---------- 볼 것 3가지 ----------
T("볼 것 3가지와 평단별 점검", "보유자 참고 기준")
M((9,0), ["L261105h_window"], [])
M((9,1), ["commons_krxboard_2", "commons_handshake_2", "vsoldier_47862"], [IC("up", "① 미국 기업 신규 계약 증가율", at=0.1)], src="다음 분기 3분기 대비")
M((9,2), ["commons_ustreasury_3", "vwashington_22786"], [IC("bank", "② 미국 정부 매출 · 전체의 41%", at=0.1)], src=Q3)
M((9,3), ["commons_krxboard_3", "commons_msftdc_2", "vspy_14090"], [IC("dollar", "③ 4분기 매출 전망 약 26.5억 달러", at=0.1)], src="회사 가이던스 · 다음 실적 2027년 2월 초 예상")
M((9,4), ["commons_iphonehand_2", "commons_iphonehand_3"], [], src=FINE)
M((9,5), ["commons_seoulnight_2", "L261105h_phone2010", "commons_iphonehand_1"], [PCT([{"label": "200달러 매수", "v": -20, "mark": "현재 손실"}, {"label": "본전 회복", "v": 25, "mark": "필요 상승률"}], at=0.3, dec=0)], src="11/6 종가 160달러 기준 · " + FINE)
M((9,6), ["commons_pricetag_1", "L2611ss_expo", "commons_bankvault_2"], [PCT([{"label": "비중 20%", "v": -4.6}, {"label": "비중 50%", "v": -11.5}], at=0.45, dec=1), P("주가 -23% 시 계좌 영향")], src="단순 계산 · " + FINE)
M((9,7), ["commons_lotteworldtower_1", "L261104g_banker_silhouette", "L261105g_cin_receipt", "L261105k_cin_seoulstreet"], [LOW("신용융자 반대매매", "주가 하락 시 증권사의 강제 매도", at=0.55)], src=FINE)
M((9,8), ["L261105g_cin_signing", "commons_msftsign_3"], [P("2027년 2월 초 · 4분기 실적 (예상)")], src=FINE)
M((9,9), ["commons_sfskyline_3", "commons_seouldept_1"], [CH([106, 209.05, 160.38], ["2026.6.25", "2026.10.9", "2026.11.6"], ["106달러", "209달러", "160달러"], color="gold", at=0.55)], src="종가 기준 · TradingView · StatMuse")
M((9,10), ["vsilhouette_33968", "commons_lottedept_1"], [P("평단 50달러 미만 · 비중 점검")], src=FINE)
M((9,11), ["commons_ladefense_2", "commons_msftcampus_3"], [CH([5.92, 209.05, 160.38], ["2022.12", "2026.10", "2026.11"], ["5.92달러", "209달러", "160달러"], color="gold", at=0.3)], src="TradingView · StatMuse · " + FINE)

# ---------- 마무리 ----------
M((10,0), ["I:thumb_tower", "space_18772"], [])
S.append({"v": {"type": "media", "full": True, "wash": "none", "lib": resolve("space_45033")}, "lines": [L(10,1)], "sketch_add": [], "en": [""], "asof": False, "src": ""})
END_LINES = [L(10,2).split(" 좋아요")[0], "좋아요" + L(10,2).split(" 좋아요", 1)[1]]
S.append({"v": {"type": "end", "sub": "", "btn_at": ["1:좋아요", "1:구독", "1:구독"], "note": {"text": ""},
    "closing_photo": resolve("space_47401"), "backdrop": resolve("commons_lotteworldtower_2"), "bd_dim": 0.74},
    "lines": END_LINES, "endscreen": 8, "sketch_add": [], "en": ["", ""], "asof": False, "src": ""})

# ---------- 메타 ----------
TITLE = "팔란티어 주가 전망, 음모론 단골 회사가 왜 한 달 만에 -23%가 됐나"
spec = {k: base[k] for k in ["fx", "format", "world", "notebook", "hook", "overlay"]}
spec["look"] = {"paper": "blueprint", "dark": "ink", "accent": "sky"}
spec["music"] = copy.deepcopy(base["music"])
spec["music"]["note"] = "본편 H6 House - July → H1 Deep House Sunset, 모두 Pixabay·Content ID 없음 · 인트로 I2 · 훅 사진 전환 간격 줄이려 중간 베이스 시각 추가"
spec["music"]["hits"] = sorted(set(spec["music"].get("hits", []) + [9.76, 15.6, 39.5, 50.47, 71.9, 85.09]))
spec.update({
    "id": "L261109-palantir-what", "company": "PLTR", "series": "내 계좌 점검", "plan": "P261110-palantir-what",
    "events": [{"at": "2026-11-09T01:22:00+09:00", "by": "owner", "what": "채팅 지시 — 스토리가 모호한 건 하지 말고 이해하기 쉽게, 그 방향으로 렌더링 시작 (원고 v2 확정)"}],
    "scheduled_at": "2026-11-09T19:30:00+09:00",
    "opening": "결론 먼저형 (음모론 주장 → 위키리크스 계획서 → CIA·육군 → 209→160달러 → 매출 +96% → 신규 계약 153%→11% → 800만 달러 → 평단별 점검)",
    "hook_type": "H13 숨은 이유 + 보유자 대응 힌트",
    "endscreen_target": "L261107-soxl-38",
    "title": TITLE,
    "doc_title": "팔란티어, 미국 정부를 등에 업은 음모론의 회사는 왜 한 달 만에 -23%가 됐나",
    "title_en": "Palantir stock outlook: why did the company at the center of conspiracy theories fall 23% in a month?",
    "tags": ["팔란티어 주가 전망", "팔란티어 주가", "팔란티어", "팔란티어 전망", "팔란티어 실적", "PLTR", "Palantir", "미국 주식", "서학개미", "AI 소프트웨어", "AIP", "알렉스 카프", "피터 틸", "미국주식 전망", "AI 주식"],
    "search_keywords": ["팔란티어 주가 전망", "팔란티어 주가", "팔란티어", "팔란티어 실적", "PLTR", "팔란티어 전망"],
    "sources": ["팔란티어 2026년 3분기 실적 보도자료 (SEC 8-K, 2026-11-02) · 2분기 실적 보도자료 (2026-08-03) · 3분기 실적 설명회",
                "StatMuse·StockAnalysis·TradingView (최고 종가 209.05달러, 11/6 종가 160.38달러, PER 112.98, 시가총액 3,864억 달러, 2022-12-27 저점 5.92달러)",
                "Beinsure 2026-11-06 (11/5 -9.73%, 소프트웨어 동반 급락) · KB Think 2026-11-06 (환율 1,355원)",
                "BuzzFeed News 2016 (2015 계약 17억·현금 4.2억 달러, 코카콜라·아멕스·나스닥) · SiliconANGLE 2016-05-09 (공동 창업자 반박)",
                "Brennan Center 2017-07-20 (뉴욕 경찰 분쟁) · Fortune 2021-11-24 (스팩 투자·블랙스카이·씨티 추정) · Motley Fool 2023-06-05",
                "iTnews 2011 · 위키백과 HBGary · The Register 2025-04-21 (ICE 약 3천만 달러) · 뉴욕타임스 2025 보도(AOL 인용)·회사 반박",
                "Startup Fortune 2026-09 (내부자 매도) · SEC 10-Q 2026-06-30 (창업자 의결권 49.999999%)",
                "그림: AI 생성 시네마틱 스틸(실존 인물 아님) · 사진: Wikimedia Commons · 영상: Mixkit·Pexels · 음악: Pixabay (BerryDeep, Easy_Eva, sunset-house-grooves)"],
    "pinned_comment": "팔란티어를 들고 계신다면, 지금 계좌에서 비중이 몇 %인가요? 다음 실적 때 어떤 숫자를 먼저 보실지 댓글로 나눠 주세요.\n※ 2026년 11월 6일 종가 기준 숫자이며 매수·매도 권유가 아닙니다.\n좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다.",
    "description_head": "팔란티어 주가 전망이 궁금하신 분들을 위해 정리했습니다. 팔란티어 주가, 3분기 실적, 신규 계약 숫자를 쉽게 풀었습니다.\n\n음모론 영상마다 나오는 회사 팔란티어의 주가가 10월 9일 209달러에서 11월 6일 160달러로 한 달 만에 23% 내렸습니다. 문제는 음모론이 아니었습니다. 3분기 매출은 96% 늘었지만, 미국 기업 신규 계약 증가율이 153%에서 11%로 내려왔습니다.\n\n확인된 사실과 확인되지 않은 주장을 구분하고, 코카콜라가 거절한 계약, 뉴욕 경찰과의 데이터 분쟁, 스팩 투자 논란을 지금의 숫자와 연결했습니다. 평단별로 점검할 내용까지 정리했습니다.\n\n국민 전체를 감시한다는 주장은 확인된 사실이 아니며, 회사는 이를 부인합니다. 2026년 11월 6일 종가 기준, 매수·매도 권유가 아닙니다.",
    "description_en": "Palantir fell 23% in a month, from $209 on Oct 9 to $160 on Nov 6, even as Q3 revenue grew 96%. We separate confirmed facts from unverified claims, retell three lesser-known episodes (the Coca-Cola rejection, the NYPD data dispute, the SPAC investments), and show the number many missed: US commercial new deal growth slowing from 153% to 11%. Not investment advice; claims of mass surveillance are unverified and denied by the company.",
    "hook_promises": ["음모론의 사실 여부 구분", "주주도 잘 모르는 사건 세 개", "평단별 점검 내용"],
    "viewer_question": "매출이 96% 늘었는데 왜 주가는 23% 빠졌나",
    "format_note": "대표 확정 원고 v2 그대로. 실존 인물 사진·닮은 그림 없음, 직전 SOXL·레버리지 편과 겹치는 소재 없음, 한 장면 3~4초, 숫자는 그래프.",
    "thumb": {"photo": "il_L261109p_thumb_tower.jpeg", "focus_x": 0.5, "l1": "미국 정부가 키운 음모론의 회사", "l2": "주가 왜 한 달 만에 -23%?", "pos": "left", "s1": 60, "s2": 110},
    "ab_sets": [
        {"key": "a", "default": True, "title": TITLE, "file": "thumb_a.jpg", "type": "A 음모론의 회사 (콜드 오픈과 같은 질문)"},
        {"key": "b", "title": TITLE, "file": "thumb_b.jpg", "type": "B 검색어형 (팔란티어 주가 전망)"},
        {"key": "c", "title": TITLE, "file": "thumb_c.jpg", "type": "C 좌우 대비 (매출 +96% vs 주가 -23%)"}],
    "scenes": S,
})
out = os.path.join(OUT_DIR, "L261109-palantir-what.json")
json.dump(spec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 원고 일치 검사
spoken = [x for sc in S for x in sc.get("lines", [])]
expected = [x for c, l in SCRIPT for x in l]
assert " ".join(spoken) == " ".join(expected), "원고 순서·문장 불일치"
tot = sum(syl(t) for t in spoken)
print("scenes", len(S), "syl", tot, "est", round(tot / 6.1), "cuts", sum(r[1] for r in REPORT))
print("긴 컷(>4.2s):"); [print(" ", r) for r in REPORT if r[2] > 4.2]
print("반복:", sorted({w[1] for w in WARN if w[0]=="반복"}))
prev = sorted({w[1] for w in WARN if w[0]!="반복"}); print("겹침:", len(prev), prev)
import collections
print("종류:", collections.Counter("영상" if p.endswith(".mp4") else "사진·그림" for p in USED))
