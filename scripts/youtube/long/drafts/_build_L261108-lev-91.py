# 2026-11-08 SK하이닉스·삼성전자 단일종목 레버리지 ETF 롱폼 — v2 (대표 11/8 11:23 검수 피드백 반영)
# - 인트로 고정 멘트 "밸류노트, 지금 시작합니다." · 반도체 업황·AI 큰 그림 장 추가 · 주담대·신용대출 위험 명확히
# - 정치인 사진(commons_samsungfab_1·commons_pyeongtaek_*) 절대 사용 금지 · SOXL 편과 다른 그림·영상, 같은 그림 반복 금지
# - 날짜 도장(stamp) 제거(자막과 정렬 충돌) · 오른쪽 위 계좌 카드 넘침 장면 단순화 · '갈림길' 등 추상 표현 금지 · 앱 지운다는 말 삭제
# - 더 쉬운 말 · 마지막은 밸류노트 점수 대신 레버리지 계산기 화면 한 장면만 가볍게
# 사용: python3 scripts/youtube/long/drafts/_build_L261108-lev-91.py  →  specs/L261108-lev-91.json
import json, os, copy, re
HERE = os.path.dirname(os.path.abspath(__file__)); SPECS = os.path.join(HERE, "..", "specs")
LIB = os.path.join(HERE, "..", "..", "..", "blog", "media", "lib")
base = json.load(open(os.path.join(SPECS, "L261107-soxl-38.json"), encoding="utf-8"))

FINE = "매수·매도 권유 아님"
BANNED = {"commons_samsungfab_1.jpg", "commons_pyeongtaek_1.jpg", "commons_pyeongtaek_2.jpg"}
SOXL_USED = set()
for sc in base["scenes"]:
    v = sc["v"]
    for c in v.get("cuts", []): SOXL_USED.add(c["lib"] if isinstance(c, dict) else c)
    for k in ("lib", "closing_photo", "backdrop"):
        if v.get(k): SOXL_USED.add(v[k])
USED = {}

def P(text, line=0, at=0.05, **k):
    return dict(kind="print", text=text, line=line, at=at, **k)

def M(cuts, lines, sketch=None, src="", cold=False, **k):
    for c in cuts:
        assert c not in BANNED, c
        assert os.path.exists(os.path.join(LIB, c)), c
        USED[c] = USED.get(c, 0) + 1
    v = {"type": "media", "full": True, "wash": "none" if cold else "left", "cuts": [{"lib": c} for c in cuts]}
    if cold: v.update(cine=True, doc_cine=True)
    else: v["wash_amt"] = 0.85
    s = {"v": v, "lines": lines, "sketch_add": [], "en": [""] * len(lines), "asof": False, "src": src, "sketch": sketch or []}
    if cold: s.update(lead=0.0 if k.pop("first", False) else 0.08, hold=0.12)
    s.update(k); return s

def T(title, sub):
    return {"chapter": title, "v": {"type": "title", "text": title, "sub": sub}, "lines": [], "sketch_add": [], "en": [], "asof": False, "src": "", "dur": 2.2}

def BARS(title, items, at=0.45):
    return [P(title), {"kind": "bars", "items": items, "line": 0, "at": at}]

def b(label, v, text, color): return {"label": label, "v": v, "text": text, "color": color}

S = []
# ---------- 콜드 오픈: 후킹 세 개 ----------
S.append(M(["il_L261110a_midnight_phones.jpeg", "il_L261110a_red_screens.jpeg"],
    ["SK하이닉스 레버리지 ETF 고점에 넣은 1,000만 원, 지금 91만 원이 남았습니다. 더 넣어야 할까요?"],
    [P("2026.11.6 · KODEX SK하이닉스 레버리지"),
     {"kind": "acct", "label": "고점에 넣은 1,000만 원", "sub": "11월 6일 종가 기준", "line": 0, "at": 0.25, "unit": "만 원", "from": 1000, "to": 91, "delay": 0.8, "count": 1.6, "color": "red"}],
    cold=True, first=True, src="국민일보 2026-11-06 (KODEX 44,000원 → 4,000원)"))
S.append(M(["il_Y261105_b_yeouido.jpeg", "vseoul_20089.mp4"],
    ["이 ETF는 5월 27일 처음 상장해 첫날에만 18% 올랐던 상품입니다."],
    [P("2026.5.27 첫 상장 · 첫날 +18%")], cold=True, src="머니투데이 2026-05-23 · SBS Biz 2026-05-27"))
S.append(M(["il_L261107m_low_tide.jpeg", "il_L261107m_dry_reservoir.jpeg"],
    ["SK하이닉스 주가는 61% 빠졌습니다. 그런데 주가가 고점까지 다시 올라가도, 이 계좌는 600만 원 근처까지밖에 못 돌아옵니다."],
    [P("주가가 고점으로 돌아가도 → 약 600만 원", color="red")], cold=True, src="계산: 주가가 흔들림 없이 오른다고 가정"))
S.append(M(["commons_skhynix_1.jpg", "server_20822.mp4"],
    ["더 이상한 건 따로 있어요. 회사는 지난 세 달 동안 83조 원을 벌었습니다. 역대 최대예요."],
    [P("3분기 영업이익 83조 3천억 원")], cold=True, src="SK하이닉스 2026년 3분기 실적 (10월 28일)"))
S.append(M(["il_L261110a_search_phone.jpeg", "creditcard_34241_a.jpg"],
    ["그런데도 개인은 10월부터 이 ETF에 1,298억 원을 더 넣었습니다."],
    [P("10월 1일 ~ 11월 6일 개인 순매수 1,298억 원")], cold=True, src="뉴스웨이 2026-11-06"))
S.append(M(["il_L261104g_two_paths_scale.jpeg", "il_Y261105_b_dawn.jpeg"],
    ["더 넣을지, 갈아탈지. 오늘은 지금 계좌가 어디쯤인지, 반도체는 어디로 가는지, 그리고 내 상황에 맞는 방법을 1년 뒤 계좌로 쉽게 계산해 드리겠습니다."],
    [P("지금 위치 · 반도체 큰 그림 · 내 상황별 방법")], cold=True))
ident = copy.deepcopy(base["scenes"][9]); ident.pop("dur", None)
ident["lines"] = ["밸류노트, 지금 시작합니다."]; ident["en"] = [""]
S.append(ident)

# ---------- 결론 먼저 ----------
S.append(M(["il_L2611ss_review_docs.jpeg", "vdocuments_22856.mp4", "commons_skhynix_2.jpg"],
    ["결론부터 말씀드릴게요. 회사는 무너지지 않았습니다. 무너진 건 2배 상품을 담은 계좌예요.",
     "그래서 더 넣는다면, 레버리지로 넣느냐 주식으로 넣느냐에 따라 1년 뒤 결과가 크게 달라집니다. 오늘 계산은 고정 댓글에서 내 숫자로 다시 해 보실 수 있어요."],
    [P("결론 먼저"), {"kind": "table", "cols": ["회사", "레버리지 계좌"], "rows": [["세 달에 83조 원", "고점 대비 -91%"]], "colors": ["gold", "red"], "line": 0, "at": 0.5}]))

# ---------- 1장: 지금 계좌 점검 ----------
S.append(T("300만닉스의 꿈", "2026년 6월 → 11월"))
S.append(M(["il_L2611ss_crowd_2021.jpeg", "vseoul_20095.mp4"],
    ["6월, SK하이닉스는 291만 9천 원까지 올랐습니다. 다들 300만닉스를 이야기했죠."],
    [P("2026년 6월 · 장중 291만 9천 원")], src="서울신문 2026-11-06"))
S.append(M(["il_L261107m_kospi_board_red.jpeg", "il_L261110a_exchange_night.jpeg"],
    ["그런데 11월 5일과 6일, 코스피가 이틀 연속 5% 넘게 빠졌습니다. 6일에는 거래가 잠시 멈추는 서킷브레이커까지 걸렸어요."],
    [P("11월 5일 -5.28% · 11월 6일 -6.02%")], src="코스피 마감 시황 보도 (2026-11-05·06)"))
S.append(M(["il_L261107m_permit_stamp.jpeg", "il_L261107m_dc_plains.jpeg"],
    ["미국에서 AI 데이터센터 규제 우려가 커졌고, 외국인은 6일 하루에만 2조 7천억 원 넘게 팔았습니다."],
    [P("11월 6일 외국인 순매도 약 2조 7천억 원")], src="시대일보·톱스타뉴스 2026-11-06"))
S.append(M(["il_L261110a_dark_board.jpeg", "il_L261107m_empty_floor.jpeg"],
    ["SK하이닉스는 113만 2천 원에 마감했습니다. 고점에서 61% 내려왔어요."],
    [P("113만 2천 원 · 고점 대비 -61%", color="red")], src="11월 6일 종가"))
S.append(M(["il_Y261105_c_fab.jpeg", "factory_47257.mp4"],
    ["삼성전자도 36만 2,500원에서 18만 8,700원이 됐습니다. 거의 반이에요. 그런데도 삼성전자 레버리지 ETF에도 개인 돈 524억 원이 더 들어왔습니다."],
    [P("삼성전자 36만 2,500원 → 18만 8,700원")], src="서울신문 2026-11-06 · 뉴스웨이 2026-11-06 · 11월 6일 종가"))
S.append(M(["il_L2611ss_subway.jpeg", "vphonecall_39790.mp4"],
    ["개인은 11월 2일부터 사흘 동안 SK하이닉스를 6,620억 원어치 더 샀습니다. 그리고 다음 날 폭락이 왔어요."],
    [P("11/2~4 개인 순매수 · SK하이닉스 6,620억 원")], src="서울신문 2026-11-06"))
S.append(M(["il_L261110a_empty_chair.jpeg", "vnightcity_49878.mp4"],
    ["그날 한 신문 기사 제목은 이랬습니다. 다신 주식 안 할게요, 제발 본전만."],
    [P("“제발 본전만”")], src="서울신문 2026-11-06"))
S.append(M(["il_L261104g_phone_margin.jpeg", "calculator_34126_a.jpg"],
    ["2배 상품은 훨씬 크게 움직였습니다. SK하이닉스 레버리지 ETF는 6일 하루에만 20% 넘게 빠졌어요. 4만 4천 원이던 가격이 4,000원이 됐습니다."],
    [P("4만 4천 원 → 4,000원", color="red")], src="국민일보 2026-11-06 (KODEX 기준)"))
S.append(M(["il_L261110a_phone_pay.jpeg", "coins_38406.mp4"],
    ["4,000원이면 커피 한 잔 값이에요. 5월엔 커피 열한 잔 값이었고요. 삼성전자 레버리지도 고점에서 81% 빠졌습니다."],
    BARS("고점 대비 하락률", [b("SK하이닉스 2배", 91, "-91%", "red"), b("삼성전자 2배", 81, "-81%", "red")]), src="국민일보 2026-11-06 (KODEX 기준)"))

# ---------- 2장: 주식은 61%, 계좌는 91% ----------
S.append(T("주식은 61%, 계좌는 91%", "2배 상품이 덜 돌아오는 이유"))
S.append(M(["il_L261104g_scale_tilt.jpeg", "il_L2611ss_qualtest.jpeg"],
    ["이 상품은 하루 단위로 2배를 맞춥니다. 매일 0에서 다시 시작하는 셈이에요."],
    [P("하루 단위로 2배")], src="상품 투자설명서"))
S.append(M(["il_L261107m_crane_stopped.jpeg", "il_Y261105_b_floor.jpeg"],
    ["예를 들어 볼게요. 주가가 하루 10% 빠졌다가 다음 날 10% 오르면, 주식은 100에서 99가 됩니다. 2배 상품은 80을 거쳐 96이 돼요.",
     "이렇게 오르내릴수록 조금씩 깎입니다. 그래서 내려갈 때 2배까지는 안 빠지는 대신, 올라갈 때도 2배만큼 못 따라와요."],
    [P("주식 100 → 90 → 99"), P("2배 100 → 80 → 96", line=0, at=0.55, color="red")]))
S.append(M(["il_L2611ss_empty_fab.jpeg", "factory_14631.mp4"],
    ["본전까지의 거리를 보면 차이가 확 보입니다. SK하이닉스 주식은 158% 오르면 고점이에요. 이 ETF는 1,000% 올라야 본전입니다."],
    BARS("고점까지 필요한 상승률", [b("SK하이닉스 주식", 158, "+158%", "gray"), b("2배 ETF", 1000, "+1,000%", "red")]),
    src="11월 6일 종가 기준 계산"))
S.append(M(["il_L261110a_closing_dawn.jpeg", "vnightcity_40746.mp4"],
    ["그래서 주가가 고점까지 곧장 돌아가도, 1,000만 원 계좌는 약 600만 원까지만 회복합니다. 삼성전자 레버리지도 똑같아요. 주식은 92%면 고점인데, 2배 ETF는 430%가 올라야 본전입니다."],
    [P("주가 고점 회복 시 → 약 600만 원"), P("삼성전자: 주식 +92% · 2배 ETF +430%", line=0, at=0.55, color="red")],
    src="계산 · 흔들림 없이 오른다고 가정 · " + FINE))

# ---------- 3장: 반도체와 AI, 큰 그림 ----------
S.append(T("반도체와 AI, 큰 그림", "메모리 경기는 지금 어디쯤일까"))
S.append(M(["il_Y261105_a_server.jpeg", "server_23215.mp4"],
    ["그럼 반도체 경기는 지금 어디쯤일까요. 메모리는 값이 오르면 이익이 크게 늘고, 값이 내리면 이익이 빠르게 줄어드는 산업입니다."],
    [P("메모리 = 값이 이익을 정한다")]))
S.append(M(["il_L2611ss_cin_winter.jpeg", "vphonecall_23073.mp4" if False else "il_L261110a_bund_night.jpeg"],
    ["그리고 메모리 경기는 보통 3~4년마다 크게 오르내렸습니다. 2018년 호황 뒤 2019년 불황, 2021년 호황 뒤 2023년 불황처럼요. 그래서 지금 시장이 묻는 건, 이번 호황이 언제까지 가느냐입니다."],
    [P("2018 호황 → 2019 불황 · 2021 호황 → 2023 불황")], src="SK하이닉스 연도별 실적"))
S.append(M(["il_L261110a_server_aisle.jpeg", "il_Y261105_b_dc.jpeg"],
    ["지금 그 값을 끌어올리는 건 AI입니다. AI 서버를 짓는 회사들이 메모리를 사려고 줄을 섰는데, 공장은 하루아침에 늘릴 수 없거든요."],
    [P("AI 서버 → 메모리 수요")]))
S.append(M(["il_L261110a_ai_orb.jpeg", "server_24033.mp4" if False else "il_L261107m_powerlines_homes.jpeg"],
    ["AI 투자는 큰 회사들이 서로 뒤처지지 않으려고 데이터센터를 짓는 경쟁이에요. 이 경쟁이 이어지는 한 메모리는 계속 필요합니다. 반대로 경쟁이 멈추면 가장 먼저 흔들리는 게 메모리 값이고요."],
    [P("AI 데이터센터 경쟁 = 메모리 수요의 엔진")]))
S.append(M(["il_L2611ss_hbm_stack.jpeg", "commons_hbm_1.jpg"],
    ["특히 AI 칩 바로 옆에 붙는 고성능 메모리, HBM에서는 SK하이닉스가 세계 1위예요. 조사 회사 트렌드포스는 4분기에도 일반 D램 값이 10~15% 더 오른다고 봤습니다."],
    [P("HBM 세계 1위"), P("4분기 D램 값 +10~15% 전망", line=0, at=0.6, color="gold")], src="카운터포인트리서치 · 트렌드포스 (2026년 10월)"))
S.append(M(["il_L261107m_dc_cooling.jpeg", "il_L2611ss_dc_build.jpeg"],
    ["걱정도 두 가지 있습니다. 하나는 이번 하락을 부른 미국의 AI 데이터센터 규제 우려예요. 데이터센터를 덜 지으면 메모리도 덜 필요하니까요."],
    [P("걱정 ① AI 데이터센터 규제 우려")]))
S.append(M(["il_L2611ss_cin_cleanroom.jpeg", "il_Y261105_a_china.jpeg"],
    ["다른 하나는 공급입니다. 값이 오르자 메모리 회사들이 공장을 늘리고 있어요. SK하이닉스 용인 첫 공장도 2027년에 문을 열고, 중국 회사들도 싼 메모리로 따라오고 있습니다."],
    [P("걱정 ② 2027년부터 늘어나는 공급")], src="SK하이닉스 · 카운터포인트리서치"))
S.append(M(["il_L261110a_analyst_desk.jpeg", "il_Y261105_a_hall.jpeg"],
    ["그래서 시장은 지금은 좋지만 2028년쯤부터 느려질 수 있다는 걱정을 먼저 가격에 넣고 있습니다. 유안타증권도 수요가 망가진 게 아니라 그 걱정이 먼저 반영된 것이라고 봤어요."],
    [P("지금 주가 = 2028년 이후 걱정이 먼저 반영")], src="서울신문 2026-11-06 (유안타증권)"))

# ---------- 4장: 회사는 무엇을 벌고 있나 (희망의 근거) ----------
S.append(T("회사는 무엇을 벌고 있나", "SK하이닉스 · 2026년 3분기"))
S.append(M(["commons_skhynix_3.jpg", "commons_micronfab_2.jpg"],
    ["그래도 회사의 체력은 아직 역대 최고입니다. 세 달 영업이익이 83조 원, 100원어치 팔아 80원을 남겼어요."],
    [P("100원 팔아 80원 남김")], src="SK하이닉스 2026년 3분기 실적 (10월 28일)"))
S.append(M(["il_Y261105_c_lab.jpeg", "server_47050.mp4"],
    ["그리고 2027년과 2028년에 만들 물건의 절반 넘게를 큰 고객 14곳에 이미 팔아 뒀다고 밝혔습니다. 갑자기 안 팔릴 위험은 그만큼 줄었죠."],
    [P("2027·2028년 물량 절반 이상 판매")], src="SK하이닉스 3분기 실적 설명회 (10월 28일)"))
S.append(M(["il_L2611ss_shareholders.jpeg", "bank_14977_a.jpg"],
    ["올해 주주에게 돌려주겠다는 돈도 90조 원이 넘습니다. 현금 배당 30조 원 이상, 자기 회사 주식 사들이는 데 60조 원 이상이에요."],
    [P("올해 주주환원 90조 원 이상")], src="SK하이닉스 3분기 실적 설명회 (10월 28일)"))
S.append(M(["il_Y261105_c_winter.jpeg", "il_L261107m_earnings_drop.jpeg"],
    ["물론 메모리는 꺾일 때 빠르게 꺾입니다. 2018년 사상 최대 이익 다음 해에 SK하이닉스 이익은 87% 줄었고, 2023년에는 1년에 7조 7천억 원 적자를 냈어요."],
    [P("2019년 이익 -87% · 2023년 적자 7조 7천억 원", color="red")], src="SK하이닉스 2018·2019·2023년 실적"))
S.append(M(["il_L261107m_manhattan_sunrise.jpeg", "il_Y261105_b_board.jpeg"],
    ["그런데 그 적자 직전, 2022년 가을 주가는 지금의 10분의 1도 안 됐습니다. 그때 산 사람은 이번 하락을 다 겪고도 10배 넘게 들고 있어요. 물론 그 뒤 적자의 1년을 버틴 사람만 받은 결과입니다."],
    [P("2022년 가을 → 지금 10배 이상", color="gold")], src="한국거래소 · 11월 6일 종가"))
S.append(M(["il_L2611ss_hbm4_base.jpeg", "commons_wafer_4.jpg"],
    ["회복은 늘 이익에서 시작했습니다. 그리고 지금 이익은 아직 역대 최대예요. 그럼 남은 질문은 하나입니다. 기다린다면, 어떤 방식이 덜 위험할까요."],
    [P("기다린다면, 어떤 방식이 덜 위험할까")]))

# ---------- 5장: 1년 뒤 계좌로 계산하기 ----------
S.append(T("1년 뒤 계좌로 계산하기", "레버리지로 물타기 vs 주식으로 갈아타기"))
S.append(M(["il_L261110a_giant_screen.jpeg", "il_L261104g_morning_phone.jpeg"],
    ["다시 91만 원 남은 계좌로 가 볼게요. 여기에 1,000만 원을 더 넣는다고 해 보겠습니다. 방법은 두 가지예요. 같은 레버리지 ETF를 더 사는 것, 아니면 남은 돈까지 SK하이닉스 주식으로 옮기는 것입니다."],
    [P("91만 원 + 새 돈 1,000만 원"), P("A 레버리지로 물타기 · B 주식으로 갈아타기", line=0, at=0.7, color="gold")]))
S.append(M(["il_L261104g_crisis_2008.jpeg", "il_L261104g_sell_all.jpeg"],
    ["주가가 하루 3~4%씩 오르내린다고 보고 계산했습니다. 먼저 나쁜 경우부터요. 1년 동안 30% 더 빠지면 레버리지는 약 400만 원, 주식은 약 760만 원이 남습니다."],
    BARS("1년간 30% 더 하락", [b("A 레버리지", 400, "400만 원", "red"), b("B 주식", 760, "760만 원", "gray")]), src="계산 · 연 변동성 55% 가정 · " + FINE))
S.append(M(["il_L261107m_rental_racks.jpeg", "il_L261107m_tech_campus.jpeg"],
    ["1년 내내 지금 자리에서 오르내리기만 하면, 주식은 1,090만 원 그대로인데 레버리지는 810만 원으로 줄어 있어요."],
    BARS("1년간 제자리", [b("A 레버리지", 810, "810만 원", "red"), b("B 주식", 1090, "1,090만 원", "gray")]), src="계산 · " + FINE))
S.append(M(["il_L261107m_fiber_glow.jpeg", "vbusinessman_231.mp4"],
    ["크게 흔들리며 170만 원까지 돌아오면, 레버리지는 약 1,820만 원, 주식은 약 1,640만 원입니다. 둘 다 원금 2,000만 원에는 못 미쳐요."],
    BARS("1년간 흔들리며 170만 원까지", [b("A 레버리지", 1820, "1,820만 원", "gold"), b("B 주식", 1640, "1,640만 원", "gray")]), src="계산 · " + FINE))
S.append(M(["il_L261107m_wallst_cheer.jpeg", "vbusinessman_42648.mp4"],
    ["가장 드문 경우, 1년 안에 고점까지 곧장 돌아가면 레버리지는 약 7,250만 원, 주식은 약 2,810만 원이에요. 맞히면 크지만, 이렇게 곧게 오르는 일은 드뭅니다."],
    BARS("1년 안에 고점까지 곧장", [b("A 레버리지", 7250, "7,250만 원", "gold"), b("B 주식", 2810, "2,810만 원", "gray")]), src="계산 · " + FINE))
S.append(M(["il_L261104g_level_scale.jpeg", "il_Y261105_c_office.jpeg"],
    ["정리하면 레버리지는 1년 뒤 400만 원에서 7,250만 원까지 벌어지고, 주식은 760만 원에서 2,810만 원 사이입니다. 그래서 고를 때 물어야 할 건, 틀렸을 때 버틸 수 있느냐예요."],
    [P("1년 뒤 결과의 폭"), {"kind": "table", "cols": ["", "가장 나쁠 때", "가장 좋을 때"], "rows": [["A 레버리지", "400만 원", "7,250만 원"], ["B 주식", "760만 원", "2,810만 원"]], "colors": ["gray", "red", "gold"], "line": 0, "at": 0.4}],
    src="연 변동성 55% 가정 단순 계산 · 수수료·세금 제외 · " + FINE))

# ---------- 6장: 내 상황별 답 ----------
S.append(T("내 상황별 답", "어떤 돈으로, 언제 샀는지에 따라"))
S.append(M(["il_L261107m_loan_desk.jpeg", "vphonecall_23073.mp4"],
    ["먼저 꼭 말씀드릴 게 있습니다. 주택담보대출이나 신용대출로 빌린 돈으로 물을 타는 건 가장 위험합니다.",
     "2배 상품은 하루에 20%도 빠져요. 계좌가 반토막 나도 빌린 돈과 매달 나가는 이자는 그대로 남고, 집을 담보로 잡힌 돈이면 생활 자체가 흔들립니다. 이런 돈이라면 더 넣지 않는 게 먼저예요."],
    [P("주담대·신용대출로 물타기 = 가장 위험", color="red"), P("계좌가 줄어도 빚과 이자는 그대로", line=1, at=0.3)], src=FINE))
S.append(M(["il_L261110a_office_exit.jpeg", "il_L261110a_korea_door.jpeg"],
    ["첫째, 고점 근처에 샀고 더 넣을 돈이 없는 분입니다. 남은 91만 원을 레버리지로 둘지, 주식으로 옮길지가 질문이에요.",
     "기준은 SK하이닉스 약 153만 원입니다. 1년 안에 그 위로 간다고 보면 그대로 두는 쪽이, 못 간다고 보면 주식으로 옮기는 쪽이 더 많이 남아요."],
    [P("① 고점 매수 · 새 돈 없음"), P("기준: 1년 안에 SK하이닉스 약 153만 원", line=1, at=0.3, color="gold")], src="계산: 연 변동성 55% 가정 · " + FINE))
S.append(M(["il_L2611ss_cin_investor.jpeg", "vbusinessman_8941.mp4"],
    ["둘째, 크게 물렸지만 여윳돈이 있는 분입니다. 남은 레버리지는 두고 새 돈만 주식으로 넣으면, 1년 뒤 결과는 약 730만 원에서 3,180만 원 사이예요. 레버리지로만 물탈 때보다 가장 나쁜 경우가 훨씬 덜 나쁩니다. 새로 넣는 돈에는 하루 단위로 깎이는 구조가 붙지 않으니까요."],
    [P("② 크게 물림 · 여윳돈 있음"), P("레버리지는 두고 새 돈은 주식 → 730만 ~ 3,180만 원", line=0, at=0.6, color="gold")], src="계산 · " + FINE))
S.append(M(["il_Y261105_a_subway.jpeg", "creditcard_35902_a.jpg"],
    ["셋째, 10월이나 11월에 물을 타서 평균 산 가격이 6,000원쯤인 분입니다. SK하이닉스가 곧게 오르면 약 139만 원, 지금처럼 흔들리며 오르면 160만 원 안팎에서 본전이에요.",
     "하루 단위 상품이라 오래 들고 갈수록 불리하거든요. 그래서 그 가격을 목표로 정해 두고, 닿으면 일부를 정리하는 계획을 세워 두는 방법도 있습니다. 본전은 목표지, 약속은 아니니까요."],
    [P("③ 10~11월 물타기 · 평균 6,000원"), P("본전: SK하이닉스 약 139만 ~ 160만 원", line=0, at=0.6, color="gold")], src="계산: 곧게 오를 때 / 연 변동성 55% 가정 · " + FINE))
S.append(M(["il_L261110a_seal_stamp.jpeg", "calculator_47415_a.jpg"],
    ["어느 경우든 넣기로 했다면, 1월 말 실적 발표처럼 확인할 날짜를 정해 두고 나눠 넣으면 다시 판단할 기회가 남습니다."],
    [P("확인할 날짜를 정하고 나눠서")], src=FINE))

# ---------- 7장: 회복의 신호 ----------
S.append(T("회복의 신호", "1월까지 볼 것 두 가지"))
S.append(M(["il_L261110a_summit_hall.jpeg", "il_Y261105_c_hbm4.jpeg"],
    ["기다리는 동안 볼 건 ETF 가격이 아닙니다. 1월 말 실적에서 100원 팔아 80원 남기던 이익이 지켜지는지, 그리고 매달 말 나오는 D램 값이 계속 오르는지예요."],
    [P("① 1월 말 실적 · 이익률"), P("② 매달 말 D램 값", line=0, at=0.6)], src="트렌드포스 · SK하이닉스"))
S.append(M(["il_L261108v_lev_calc.jpeg"],
    ["내 평균 산 가격으로 직접 계산해 보고 싶으시면, 레버리지 계산기를 참고해 보세요. 링크는 고정 댓글에 있습니다."],
    [P("레버리지 계산기"), P("valuenote.co.kr/lev", line=0, at=0.3, color="gold")]))

# ---------- 마무리 ----------
S.append({"v": {"type": "media", "full": True, "wash": "none", "lib": "il_Y261105_b_dawn.jpeg"},
    "lines": ["주가는 이익을 따라 돌아올 수 있습니다. 다만 2배 상품은 그 길이 곧게 날 때만 같이 돌아옵니다."], "sketch_add": [], "en": [""], "asof": False, "src": ""})
S.append({"v": {"type": "end", "sub": "", "btn_at": ["0:좋아요", "0:구독", "0:구독"], "note": {"text": "고정 댓글 · 레버리지 계산기"},
    "closing_photo": "il_Y261105_b_dawn.jpeg", "backdrop": "il_L261110a_closing_dawn.jpeg", "bd_dim": 0.74},
    "lines": ["판단은 ETF 가격이 아니라, 이 회사가 세 달에 얼마를 버는지 위에서 하시는 겁니다. 좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다."],
    "endscreen": 8, "sketch_add": [], "en": [""], "asof": False, "src": ""})

TITLE = "SK하이닉스 레버리지 -91%, 물타기 해도 될까? 주가가 돌아와도 본전 못 오는 이유"
spec = {k: base[k] for k in ["fx", "format", "world", "notebook", "hook", "overlay", "look"]}
spec["music"] = copy.deepcopy(base["music"])
spec["music"]["bed"] = ["social/music/samples3/H6_full.mp3@30", "social/music/samples3/H1_full.mp3@30"]
spec["music"]["note"] = "2026-11-08 대표님: 본편 House - July(Easy_Eva) → Deep House Sunset(sunset-house-grooves), 둘 다 Pixabay·Content ID 없음 · 인트로 I2 그대로"
spec.update({
    "id": "L261108-lev-91", "company": "000660", "series": "내 계좌 점검", "plan": "P261108-lev-91",
    "events": [{"at": "2026-11-08T10:17:00+09:00", "by": "owner", "what": "채팅 지시 — 오늘 19:30 빼빼로 대신 좁은 타깃 롱폼(레버리지 ETF), 초반 후킹 세 개, 물타기·현 상황 점검·희망, SOXL 편과 겹치지 않게"},
               {"at": "2026-11-08T11:23:00+09:00", "by": "owner", "what": "검수 피드백 — 인트로 고정 멘트 '밸류노트, 지금 시작합니다', 반도체 업황·AI 큰 그림, 정치인 사진 금지(1:38·3:16), 앱 지운다는 말 삭제, SOXL과 다른 그림·반복 금지, 5:23 오른쪽 위 넘침, 날짜 도장·자막 정렬, '갈림길' 금지, 주담대 위험 명확히, 더 쉽게, 마지막은 계산기만 가볍게"}],
    "scheduled_at": "2026-11-08T19:30:00+09:00",
    "opening": "장면형 (1,000만 원이 91만 원 → 첫날 +18% → 주가가 돌아와도 600만 원 → 회사는 83조 → 개인 1,298억 → 약속 3개 → 인트로 '밸류노트, 지금 시작합니다')",
    "hook_type": "장면형 · 보유자 손익 + 결정 질문 (후킹 3개)",
    "endscreen_target": "L261107-soxl-38",
    "title": TITLE,
    "title_en": "SK hynix 2x ETF down 91%: should you average down? Why the account won't recover even if the stock does",
    "tags": ["SK하이닉스", "SK하이닉스 주가", "SK하이닉스 주가 전망", "SK하이닉스 레버리지", "KODEX SK하이닉스단일종목레버리지", "TIGER SK하이닉스단일종목레버리지", "SOL SK하이닉스단일종목레버리지", "삼성전자 레버리지", "삼전닉스 레버리지", "단일종목 레버리지 ETF", "레버리지 ETF 물타기", "물타기", "하이닉스 물타기", "반도체 업황", "HBM"],
    "search_keywords": ["SK하이닉스 레버리지", "SK하이닉스 주가 전망", "하이닉스 물타기", "삼성전자 레버리지", "단일종목 레버리지 ETF"],
    "sources": ["국민일보 2026-11-06 (단일종목 레버리지 ETF: KODEX SK하이닉스 44,000원 → 4,000원, 삼성전자 레버리지 -81%)",
                "뉴스웨이 2026-11-06 (10/1~11/6 개인 순매수: KODEX SK하이닉스단일종목레버리지 1,298억 원)",
                "서울신문 2026-11-06 (SK하이닉스 고점 291만 9천 원, 삼성전자 고점 36만 2,500원, 서킷브레이커, 개인 순매수, 유안타증권 분석)",
                "머니투데이 2026-05-23 · SBS Biz 2026-05-27 (5월 27일 상장, 첫날 +18%)",
                "SK하이닉스 2026년 3분기 실적·설명회 (10월 28일) · 2018·2019·2023년 실적 · 트렌드포스 4분기 D램 전망(2026년 10월) · 카운터포인트리서치",
                "코스피 마감 시황 보도 (11/5 -5.28%, 11/6 -6.02%, 외국인 순매도)",
                "계산: 1년·연 변동성 55% 가정 단순 계산, 수수료·세금 제외",
                "그림: AI 생성 시네마틱 스틸(실존 인물 아님) · 사진: Wikimedia Commons · 영상: Mixkit·Pexels · 음악: Pixabay (BerryDeep, Easy_Eva, sunset-house-grooves)"],
    "pinned_comment": "영상에서 쓴 계산을 그대로 열어 뒀습니다. 내 평균 산 가격을 넣으면 본전까지의 거리와 1년 뒤 계좌를 4가지 경우로 볼 수 있습니다 → valuenote.co.kr/lev\n\n여러분은 지금 레버리지로 더 넣고 계신가요, 주식으로 옮기고 계신가요? 기준을 댓글로 나눠 주세요.\n※ 2026년 11월 6일 종가 기준 숫자이며 매수·매도 권유가 아닙니다.\n좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다.",
    "description_head": "SK하이닉스 레버리지 ETF 물타기가 고민이신 분들을 위해 정리했습니다. SK하이닉스 주가 전망과 반도체 업황, 단일종목 레버리지 ETF가 왜 주가보다 덜 돌아오는지 쉽게 계산했습니다.\n\n5월 27일 상장한 SK하이닉스 레버리지 ETF는 고점 4만 4천 원에서 11월 6일 4,000원이 됐습니다(KODEX 기준). 같은 기간 SK하이닉스 주가는 61% 빠졌고, 회사는 세 달 동안 영업이익 83조 원을 벌었습니다.\n\n지금 계좌 점검, 반도체와 AI 큰 그림(메모리 값·HBM·2027년 공급), 레버리지로 물타기 vs 주식으로 갈아타기 1년 뒤 계좌 계산(4가지 경우), 주택담보대출·신용대출로 물타기의 위험, 내 상황별 방법(고점 매수·여윳돈·10~11월 물타기)을 정리합니다.\n\n※ 숫자 기준: 2026년 11월 6일 종가. 매수·매도 권유가 아닙니다.\n\n#SK하이닉스 #SK하이닉스주가전망 #레버리지ETF #삼성전자레버리지 #물타기",
    "description_en": "Korea's first single-stock 2x ETFs on Samsung Electronics and SK hynix listed on May 27. By Nov 6 the SK hynix 2x ETF was down 91% while the stock was down 61% — and the company had just earned a record 83 trillion won in one quarter. Where the account stands, the memory cycle and AI outlook, why a 2x ETF won't fully recover even if the stock does, the danger of averaging down with mortgage or credit loans, and a one-year account calculation by situation.",
    "hook_promises": ["지금 계좌 점검 (주식 -61% vs 계좌 -91%)", "반도체·AI 큰 그림 (메모리 값·HBM·2027년 공급)", "내 상황별 물타기 방법 (1년 뒤 계좌 계산 · 대출 위험)"],
    "viewer_question": "SK하이닉스 레버리지 -91%, 물타면 본전 올까?",
    "format_note": "대표님 11/8 11:23 검수 피드백 반영 v2. 정치인 사진 금지, SOXL 편 그림 재사용 최소화·같은 그림 반복 없음, 날짜 도장 없음, 인트로 고정 멘트, 마지막 계산기 화면.",
    "thumb": {"photo": "il_L261107m_kospi_board_red.jpeg", "focus_x": 0.5, "l1": "하이닉스 레버리지 -91%", "l2": "물타면 본전 올까?", "pos": "left", "s1": 70, "s2": 130},
    "ab_sets": [
        {"key": "a", "default": True, "title": TITLE, "file": "thumb_a.jpg", "type": "A 큰 숫자 (-91%, 콜드 오픈과 같은 질문)"},
        {"key": "b", "title": "SK하이닉스 레버리지 1,000만 원이 91만 원, 물탈까 갈아탈까? 1년 뒤 계산", "file": "thumb_b.jpg", "type": "B 실물 (휴대전화 계좌)"},
        {"key": "c", "title": "삼성전자·SK하이닉스 레버리지 ETF 주가 전망, 회사는 세 달에 83조 버는데 왜 계좌는 -91%일까", "file": "thumb_c.jpg", "type": "C 희망 (회사 이익 · 새벽)"}],
    "scenes": S,
})
out = os.path.join(SPECS, "L261108-lev-91.json")
json.dump(spec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
txt = "".join("".join(s.get("lines", [])) for s in S)
syl = len(re.findall(r"[가-힣0-9A-Za-z]", txt))
rep = [k for k, n in USED.items() if n > 1]; overlap = [k for k in USED if k in SOXL_USED]
print("scenes", len(S), "syllables", syl, "est total sec @6.0/s", round(syl / 6.0))
print("반복 사용:", rep); print("SOXL 편과 겹침:", overlap)
for bad in ["갈림길", "앱을", "지운"]:
    assert bad not in txt, bad
