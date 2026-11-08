# 2026-11-08 SK하이닉스·삼성전자 단일종목 레버리지 ETF 롱폼 (대표 11/8 10:17 "soxl 내용과 안 겹치게, 초반 후킹 세 개, 물타기·현 상황 점검·희망")
# 사용: python3 scripts/youtube/long/drafts/_build_L261108-lev-91.py  →  specs/L261108-lev-91.json
import json, os, copy
HERE = os.path.dirname(os.path.abspath(__file__)); SPECS = os.path.join(HERE, "..", "specs")
base = json.load(open(os.path.join(SPECS, "L261107-soxl-38.json"), encoding="utf-8"))

FINE = "매수·매도 권유 아님"

def P(text, line=0, at=0.05, **k):
    return dict(kind="print", text=text, line=line, at=at, **k)

def M(cuts, lines, sketch=None, src="", cold=False, wash="left", **k):
    v = {"type": "media", "full": True, "wash": "none" if cold else wash, "cuts": [{"lib": c} for c in cuts]}
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
# ---------- 콜드 오픈: 후킹 세 개 (91만 원 / 주가가 돌아와도 600만 원 / 회사는 83조) ----------
S.append(M(["il_L261107s_phone_red.jpeg", "il_L261104g_screens_red.jpeg"],
    ["SK하이닉스 레버리지 ETF 고점에 넣은 1,000만 원, 11월 6일 기준으로 91만 원이 남았습니다. 더 넣어야 할까요?"],
    [{"kind": "stamp", "text": "SEOUL · 2026.11.06 15:30", "line": 0, "at": 0.02},
     {"kind": "acct", "label": "고점에 넣은 1,000만 원", "sub": "KODEX SK하이닉스단일종목레버리지 · 11월 6일 종가", "line": 0, "at": 0.25, "unit": "만 원", "from": 1000, "to": 91, "delay": 0.8, "count": 1.6, "color": "red"}],
    cold=True, first=True, src="국민일보 2026-11-06 (KODEX 44,000원 → 4,000원)"))
S.append(M(["il_L261107m_kospi_board_red.jpeg", "vstockmarket_47792.mp4", "il_L261107s_subway_phones.jpeg"],
    ["이 ETF는 5월 27일 처음 상장해 첫날에만 18% 올랐던 상품입니다."],
    [{"kind": "stamp", "text": "SEOUL · 2026.05.27 09:00", "line": 0, "at": 0.02}, P("삼전닉스 2배 ETF 첫 상장 · 첫날 +18%")],
    cold=True, src="머니투데이 2026-05-23 · SBS Biz 2026-05-27 · MTN 2026-05-26"))
S.append(M(["il_L261107s_red_cliff.jpeg", "il_L261107s_deep_valley.jpeg"],
    ["같은 기간 SK하이닉스 주가는 61% 빠졌습니다. 그런데 이 주가가 고점까지 다시 올라가도, 이 계좌는 600만 원 근처까지밖에 돌아오지 못합니다."],
    [P("주가가 고점으로 돌아가도 → 약 600만 원", color="red")], cold=True, src="계산: 주가가 고점까지 흔들림 없이 오른다고 가정"))
S.append(M(["commons_skhynix_1.jpg", "chip_47258.mp4"],
    ["더 이상한 건 따로 있어요. 이 회사는 지난 세 달 동안 영업이익 83조 원을 벌었습니다. 역대 최대예요."],
    [P("3분기 영업이익 83조 3천억 원")], cold=True, src="SK하이닉스 2026년 3분기 실적 (10월 28일)"))
S.append(M(["il_L261107s_hands_cross.jpeg", "vmoney_45703.mp4"],
    ["그런데도 개인은 10월부터 이 ETF에 1,298억 원을 더 넣었습니다."],
    [P("10월 1일 ~ 11월 6일 개인 순매수 1,298억 원")], cold=True, src="뉴스웨이 2026-11-06"))
S.append(M(["il_L261107s_fork_road.jpeg", "il_L261107s_dawn_phone.jpeg"],
    ["지금 더 넣어야 할까요, 아니면 갈아타야 할까요. 오늘은 지금 계좌가 어디쯤 있는지 점검하고, 내 상황에 맞는 물타기 방법과 시점을 1년 뒤 계좌로 계산해 드리겠습니다. 이 계산은 내 평균 산 가격만 넣으면 되도록 계산기로 만들어 고정 댓글에 열어 뒀어요."],
    [P("현재 위치 점검 · 상황별 물타기 계산 · 회복의 조건")], cold=True))
ident = copy.deepcopy(base["scenes"][9]); S.append(ident)

# ---------- 결론 먼저 ----------
S.append(M(["il_L261107m_silhouette_screens.jpeg", "vstockmarket_9607.mp4", "commons_skhynix_2.jpg"],
    ["결론부터 말씀드리겠습니다. 회사는 무너지지 않았습니다. 무너진 건 2배 상품을 담은 계좌예요.",
     "그래서 더 넣는다면, 레버리지로 넣느냐 주식으로 넣느냐에 따라 1년 뒤 결과가 크게 달라집니다."],
    [P("결론 먼저"), {"kind": "table", "cols": ["회사", "레버리지 계좌"], "rows": [["세 달 영업이익 83조 원", "고점 대비 -91%"]], "colors": ["gold", "red"], "line": 0, "at": 0.5}]))

# ---------- 1장: 지금 계좌 점검 ----------
S.append(T("300만닉스의 꿈", "2026년 6월 → 11월 · 지금 계좌 점검"))
S.append(M(["il_L2611ss_crowd_2021.jpeg", "vseoul_20093.mp4", "il_L261107m_wallst_cheer.jpeg"],
    ["6월, SK하이닉스는 장중 291만 9천 원까지 올랐습니다. 다들 300만닉스를 이야기했죠."],
    [P("2026년 6월 · 장중 291만 9천 원")], src="서울신문 2026-11-06"))
S.append(M(["il_L261107m_seoul_halt.jpeg", "vstockmarket_47012.mp4", "il_L261107m_kospi_board_red.jpeg"],
    ["그리고 11월 5일과 6일, 코스피는 이틀 연속 5% 넘게 빠졌습니다. 6일에는 개장 몇 분 만에 서킷브레이커가 걸렸어요."],
    [P("11월 5일 -5.28% · 11월 6일 -6.02%")], src="한국거래소 마감 시황 보도 (2026-11-05·06)"))
S.append(M(["il_L261107m_ballot.jpeg", "il_L261107m_capitol_dawn.jpeg"],
    ["미국 중간선거 뒤 AI 데이터센터 규제 우려가 커졌고, 외국인은 6일 하루에만 2조 7천억 원 넘게 팔았습니다."],
    [P("11월 6일 외국인 순매도 약 2조 7천억 원")], src="시대일보·톱스타뉴스 2026-11-06"))
S.append(M(["il_L261104g_screens_red.jpeg", "vstockmarket_47214.mp4"],
    ["SK하이닉스는 6일 113만 2천 원에 마감했습니다. 고점에서 61% 내려온 자리예요."],
    [P("113만 2천 원 · 고점 대비 -61%", color="red")], src="11월 6일 종가"))
S.append(M(["il_L2611ss_cin_fab.jpeg", "commons_samsungfab_1.jpg"],
    ["삼성전자도 6월 36만 2,500원에서 18만 8,700원이 됐습니다. 거의 절반이에요."],
    [P("삼성전자 36만 2,500원 → 18만 8,700원")], src="서울신문 2026-11-06 · 11월 6일 종가"))
S.append(M(["il_L261107m_subway_phone.jpeg", "phone_4915.mp4", "il_L261107s_subway_phones.jpeg"],
    ["떨어지는 동안 개인 투자자들은 계속 샀습니다. 11월 2일부터 4일까지 사흘 동안 SK하이닉스 6,620억 원, 삼성전자 5,620억 원어치를 순매수했어요. 그리고 다음 날 이틀 연속 폭락이 왔습니다."],
    [P("11/2~4 개인 순매수 · SK하이닉스 6,620억 원")], src="서울신문 2026-11-06"))
S.append(M(["il_L261107m_night_worker.jpeg", "vmoney_18261.mp4"],
    ["11월 6일 한 신문 기사의 제목은 이랬습니다. 다신 주식 안 할게요, 제발 본전만. 지금 많은 계좌의 마음일 거예요."],
    [P("“제발 본전만”")], src="서울신문 2026-11-06"))
S.append(M(["il_L261107s_seoul_bed_phone.jpeg", "phone_14669.mp4"],
    ["주식 앱을 열기 무서워서 아예 지운 분도 계실 거예요. 앱은 지워도 계좌는 그대로 있다는 게 문제지만요."],
    [P("앱은 지워도 계좌는 그대로")]))
S.append(M(["il_L261107s_cracked_glass.jpeg", "il_L261107s_phone_red.jpeg"],
    ["2배 상품은 훨씬 더 크게 움직였습니다. SK하이닉스 레버리지 ETF는 6일 하루에만 20% 넘게 빠지며 상장 뒤 가장 낮은 가격을 찍었어요."],
    [P("11월 6일 하루 -20% · 상장 후 최저가", color="red")], src="국민일보 2026-11-06"))
S.append(M(["il_L261107s_red_cliff.jpeg", "storm_47948.mp4"],
    ["KODEX 기준으로 4만 4천 원이던 가격이 4,000원이 됐습니다. 삼성전자 레버리지도 고점에서 81% 빠졌어요."],
    BARS("고점 대비 하락률", [b("SK하이닉스 2배 ETF", 91, "-91%", "red"), b("삼성전자 2배 ETF", 81, "-81%", "red")]),
    src="국민일보 2026-11-06 (KODEX 기준)"))
S.append(M(["il_L261107s_seoul_bed_phone.jpeg", "phone_4915.mp4"],
    ["4,000원이면 커피 한 잔 값이에요. 5월엔 커피 열한 잔 값이었고요."],
    [P("4만 4천 원 → 4,000원")]))

# ---------- 2장: 주식은 61%, 계좌는 91% ----------
S.append(T("주식은 61%, 계좌는 91%", "2배 상품이 덜 돌아오는 이유"))
S.append(M(["il_L261107s_two_candles.jpeg", "il_L261107s_scale_coins.jpeg"],
    ["주식이 61% 빠졌는데, 2배 상품은 왜 122%가 아니라 91%일까요. 그리고 왜 주가가 돌아와도 계좌는 덜 돌아올까요. 두 질문의 답은 같습니다."],
    [P("주식 -61% · 2배 ETF -91%")]))
S.append(M(["il_L261107s_calendar_flip.jpeg", "vdocuments_24632.mp4"],
    ["이 상품은 기간 전체가 아니라 하루를 기준으로 2배를 맞춥니다. 매일 0에서 다시 시작하는 셈이에요."],
    [P("하루 기준 2배")], src="상품 투자설명서"))
S.append(M(["il_L261107s_ice_melt.jpeg", "technology_46635.mp4"],
    ["주가가 하루 10% 빠졌다가 다음 날 10% 오르면, 주식은 100에서 99가 됩니다. 2배 상품은 80을 거쳐 96이 돼요. 흔들릴수록 이렇게 조금씩 깎입니다. 그래서 내려갈 때 2배까지는 안 빠지는 대신, 올라갈 때도 2배만큼 못 따라와요."],
    [P("주식 100 → 90 → 99"), P("2배 100 → 80 → 96", line=0, at=0.55, color="red")]))
S.append(M(["il_L261107s_deep_valley.jpeg", "il_L261107s_chip_stairs.jpeg"],
    ["본전까지의 거리를 보면 차이가 확 보입니다. SK하이닉스 주식은 158% 오르면 고점이에요. 이 ETF는 1,000% 올라야 본전입니다."],
    BARS("고점까지 필요한 상승률", [b("SK하이닉스 주식", 158, "+158%", "gray"), b("2배 ETF", 1000, "+1,000%", "red")]),
    src="11월 6일 종가 기준 계산"))
S.append(M(["il_L2611ss_cin_fab.jpeg", "commons_samsungfab_1.jpg"],
    ["삼성전자 레버리지를 들고 계신 분도 계산은 똑같습니다. 삼성전자 주식은 92% 오르면 고점인데, 2배 ETF는 430% 올라야 본전이에요."],
    BARS("삼성전자 · 고점까지 필요한 상승률", [b("삼성전자 주식", 92, "+92%", "gray"), b("2배 ETF", 430, "+430%", "red")]),
    src="11월 6일 종가 기준 계산 (KODEX 기준)"))
S.append(M(["il_L261107m_hourglass.jpeg", "il_L261107s_dawn_phone.jpeg"],
    ["주가가 흔들림 없이 고점까지 곧장 돌아간다고 해도, 1,000만 원 계좌는 약 600만 원까지만 회복합니다. 처음에 말씀드린 그 숫자예요."],
    [P("주가 고점 회복 시 1,000만 원 계좌"), {"kind": "acct", "label": "고점에 넣은 1,000만 원", "sub": "주가가 흔들림 없이 고점까지 오른다고 가정", "line": 0, "at": 0.45, "unit": "만 원", "from": 91, "to": 605, "delay": 1.2, "count": 1.6, "color": "gold"}],
    src="계산 · " + FINE))
S.append(M(["il_L261107s_three_glasses.jpeg", "commons_wafer_1.jpg"],
    ["그럼 이 계좌는 이미 끝난 걸까요. 꼭 그렇지는 않습니다. 회사가 지금 어떤 상태인지부터 보면 이야기가 달라져요."],
    [P("회사는 지금 어떤 상태일까")]))

# ---------- 3장: 회사는 무엇을 벌고 있나 (희망의 근거) ----------
S.append(T("회사는 무엇을 벌고 있나", "SK하이닉스 · 2026년 3분기"))
S.append(M(["commons_skhynix_3.jpg", "chip_47051.mp4", "commons_hbm_1.jpg"],
    ["10월 28일 나온 SK하이닉스 3분기 실적은 세 달 영업이익 83조 3천억 원이었습니다. 100원어치 팔아 80원을 남긴 거예요."],
    [P("100원 팔아 80원 남김")], src="SK하이닉스 2026년 3분기 실적 (10월 28일)"))
S.append(M(["il_Y261105_b_hbm.jpeg", "server_7863.mp4", "commons_hbm_2.jpg"],
    ["AI 서버를 짓는 회사들이 메모리를 사려고 줄을 섰기 때문입니다. SK하이닉스는 14개 큰 고객과 계약해 2027년과 2028년 생산능력의 절반 넘게 이미 팔아 뒀다고 밝혔어요."],
    [P("2027·2028년 생산능력 절반 이상 판매")], src="SK하이닉스 3분기 실적 설명회 (10월 28일)"))
S.append(M(["commons_hbm_4.jpg", "datacenter_23282.mp4"],
    ["AI 칩 바로 옆에 붙는 고성능 메모리, HBM에서는 세계 1위이고요."],
    [P("HBM 세계 1위")], src="카운터포인트리서치 2026년 2분기 HBM 점유율"))
S.append(M(["il_L2611ss_shareholders.jpeg", "vmoney_18296.mp4"],
    ["올해 주주에게 돌려주겠다고 한 돈도 약 100조 원입니다. 배당과 자기 회사 주식을 사들이는 데 쓰는 돈을 합친 금액이에요."],
    [P("올해 주주환원 약 100조 원")], src="SK하이닉스 3분기 실적 설명회 (10월 28일)"))
S.append(M(["il_L261107m_dealing_room.jpeg", "vdocuments_45923.mp4"],
    ["이익에 비하면 지금 주가는 최근 1년 순이익의 5배 수준입니다. 1년에 버는 돈 5년 치면 회사 전체를 살 수 있는 가격이라는 뜻이에요."],
    [P("PER 약 5배")], src="밸류노트 데이터 (11월 6일 종가 기준)"))
S.append(M(["il_L261110a_analyst_desk.jpeg", "laptop_4713.mp4"],
    ["그런데도 왜 이렇게 빠졌을까요. 유안타증권은 메모리 수요가 망가진 게 아니라, 2028년 이후 성장이 느려질 가능성을 시장이 먼저 가격에 넣은 것이라고 분석했습니다."],
    [P("수요 훼손보다 2028년 이후 둔화 우려")], src="서울신문 2026-11-06 (유안타증권)"))
S.append(M(["il_Y261105_c_winter.jpeg", "il_L261107m_earnings_drop.jpeg"],
    ["실제로 메모리는 값이 꺾이면 이익이 빠르게 줄어듭니다. 2018년 사상 최대 이익을 낸 다음 해, SK하이닉스 영업이익은 87% 줄었어요. 이번에도 그럴 위험은 남아 있습니다."],
    [P("2019년 영업이익 -87%", color="red")], src="SK하이닉스 2018·2019년 실적"))
S.append(M(["il_L2611ss_cin_winter.jpeg", "il_Y261105_c_empty.jpeg"],
    ["그리고 이 회사는 그보다 더 깊은 바닥도 지나왔습니다. 2023년에는 1년에 7조 7천억 원 적자를 냈어요. 공장을 돌릴수록 손해였던 시기였습니다."],
    [P("2023년 영업손실 7조 7천억 원")], src="SK하이닉스 2023년 실적"))
S.append(M(["il_L261107m_manhattan_sunrise.jpeg", "il_L261107s_dawn_phone.jpeg"],
    ["그 직전인 2022년 가을, 주가는 지금의 10분의 1도 안 됐습니다. 그 바닥 근처에서 산 사람은 이번 하락을 다 겪고도 지금 10배 넘게 들고 있어요. 다만 그건 그 뒤 적자의 1년을 버틴 사람만 받은 결과입니다."],
    [P("2022년 가을 주가 → 지금 10배 이상", color="gold")], src="한국거래소 · 11월 6일 종가"))
S.append(M(["il_L261107s_wafer_hands.jpeg", "commons_wafer_2.jpg"],
    ["회복은 늘 이익에서 시작했습니다. 그리고 지금 이익은 아직 역대 최대예요. 그럼 남은 질문은 하나입니다. 회복을 기다린다면, 어떤 방식이 덜 위험할까요."],
    [P("회복을 기다린다면, 어떤 방식이 덜 위험할까")]))

# ---------- 4장: 1년 뒤 계좌로 계산 (물타기 방법) ----------
S.append(T("1년 뒤 계좌로 계산하기", "레버리지로 물타기 vs 주식으로 갈아타기"))
S.append(M(["il_L261107s_phone_red.jpeg", "il_L261107s_seoul_bed_phone.jpeg"],
    ["다시 91만 원이 남은 계좌로 돌아가 볼게요. 여기에 1,000만 원을 더 넣는다고 해 보겠습니다. 원금은 모두 2,000만 원이에요."],
    [{"kind": "acct", "label": "91만 원 + 새 돈 1,000만 원", "text": "원금 2,000만 원", "rows": ["지금 평가액 1,091만 원"], "sub": "11월 6일 종가 기준", "line": 0, "at": 0.3, "color": "gold"}]))
S.append(M(["il_L261107s_two_candles.jpeg", "il_L261107s_fork_road.jpeg"],
    ["방법은 두 가지입니다. 같은 레버리지 ETF를 더 사서 평균 산 가격을 낮추는 방법, 그리고 남은 91만 원까지 SK하이닉스 주식으로 옮기고 새 돈도 주식으로 사는 방법이에요."],
    [P("A 레버리지로 물타기"), P("B 주식으로 갈아타기", line=0, at=0.55, color="gold")]))
S.append(M(["il_L261107m_storm_tower.jpeg", "storm_47948.mp4"],
    ["먼저 나쁜 경우부터 볼게요. 계산은 주가가 하루 평균 3~4%씩 오르내린다고 가정했습니다. 첫째, 여기서 30% 더 빠지는 경우입니다. 레버리지는 약 400만 원, 주식은 약 760만 원이 남아요."],
    BARS("1년간 30% 더 하락", [b("A 레버리지", 400, "400만 원", "red"), b("B 주식", 760, "760만 원", "gray")]), src="계산 · " + FINE))
S.append(M(["il_L261107s_ice_melt.jpeg", "technology_46635.mp4"],
    ["둘째, 1년 내내 지금 자리에서 오르내리기만 하는 경우입니다. 주식은 1,090만 원 그대로인데, 레버리지는 810만 원으로 줄어 있어요."],
    BARS("1년간 제자리에서 오르내림", [b("A 레버리지", 810, "810만 원", "red"), b("B 주식", 1090, "1,090만 원", "gray")]), src="계산 · " + FINE))
S.append(M(["il_L261107s_rollercoaster.jpeg", "vstockmarket_9607.mp4"],
    ["셋째, 1년 동안 크게 오르내리면서 170만 원까지만 돌아오는 경우입니다. 레버리지는 약 1,820만 원, 주식은 약 1,640만 원. 생각보다 차이가 크지 않고, 둘 다 원금 2,000만 원에는 못 미쳐요."],
    BARS("1년간 흔들리며 170만 원까지", [b("A 레버리지", 1820, "1,820만 원", "gold"), b("B 주식", 1640, "1,640만 원", "gray")]), src="계산 · " + FINE))
S.append(M(["il_L261107m_wallst_cheer.jpeg", "vstockmarket_47016.mp4"],
    ["마지막으로 가장 드문 경우, SK하이닉스가 1년 안에 고점까지 곧장 돌아가는 경우입니다. 레버리지는 약 7,250만 원, 주식은 약 2,810만 원이에요. 이 길을 맞히면 레버리지가 압도적이지만, 이렇게 곧게 오는 경우는 드뭅니다."],
    BARS("1년 안에 고점까지 곧장 회복", [b("A 레버리지", 7250, "7,250만 원", "gold"), b("B 주식", 2810, "2,810만 원", "gray")]), src="계산 · " + FINE))
S.append(M(["il_L261107s_dart_miss.jpeg", "il_L261107s_scale_coins.jpeg"],
    ["정리하면 레버리지는 1년 뒤 결과가 400만 원에서 7,250만 원까지 벌어지고, 주식은 760만 원에서 2,810만 원 사이입니다. 그래서 방법을 고르는 질문은 얼마나 오를 것 같으냐가 아니라, 틀렸을 때 버틸 수 있느냐예요."],
    [P("1년 뒤 결과의 폭"), {"kind": "table", "cols": ["", "가장 나쁠 때", "가장 좋을 때"], "rows": [["A 레버리지", "400만 원", "7,250만 원"], ["B 주식", "760만 원", "2,810만 원"]], "colors": ["gray", "red", "gold"], "line": 0, "at": 0.4}],
    src="연 변동성 55% 가정 단순 계산 · 수수료·세금 제외 · " + FINE))

# ---------- 4-2장: 내 상황별 답 ----------
S.append(T("내 상황별 답", "평균 산 가격과 새 돈 여유에 따라"))
S.append(M(["il_L261107s_three_glasses.jpeg", "il_L261107m_three_items.jpeg"],
    ["그럼 내 계좌는 어떻게 해야 할까요. 상황에 따라 답이 다릅니다. 세 가지 경우로 나눠 볼게요."],
    [P("내 상황은 어디일까")]))
S.append(M(["il_L261107s_seoul_bed_phone.jpeg", "phone_14669.mp4", "il_L261107s_phone_red.jpeg"],
    ["첫째, 고점 근처에 샀고 더 넣을 돈이 없는 분입니다. 남은 91만 원을 레버리지로 둘지, 주식으로 옮길지가 질문이에요.",
     "계산해 보면 갈림길은 SK하이닉스 약 153만 원입니다. 1년 안에 그 위로 간다고 보면 그대로 두는 쪽이, 그 아래에 머문다고 보면 주식으로 옮기는 쪽이 더 많이 남아요."],
    [P("① 고점 매수 · 새 돈 없음"), P("갈림길: 1년 안에 SK하이닉스 약 153만 원", line=1, at=0.3, color="gold")], src="계산: 연 변동성 55% 가정 · " + FINE))
S.append(M(["il_L261107s_exit_door.jpeg", "il_L261107s_dawn_phone.jpeg"],
    ["그리고 새 돈을 넣지 않는 것도 엄연한 선택지입니다. 생활비와 비상금까지 끌어와야 하는 돈이라면, 그 돈은 계좌보다 생활을 먼저 지켜야 해요."],
    [P("새 돈을 넣지 않는 것도 선택지")], src=FINE))
S.append(M(["il_L261107s_plate_slices.jpeg", "il_L2611ss_night_office.jpeg"],
    ["둘째, 크게 물렸지만 새 돈 여유가 있는 분입니다. 남은 레버리지는 그대로 두고 새 돈만 주식으로 넣는 방법이 있어요. 1년 뒤 결과는 약 730만 원에서 3,180만 원 사이로, 레버리지로만 물탈 때보다 바닥이 훨씬 높습니다."],
    [P("② 크게 물림 · 새 돈 여유 있음"), P("레버리지는 두고 새 돈은 주식 → 730만 ~ 3,180만 원", line=0, at=0.6, color="gold")], src="계산 · " + FINE))
S.append(M(["il_L261107m_subway_phone.jpeg", "vstockmarket_47016.mp4"],
    ["셋째, 10월이나 11월에 물을 타서 평균 산 가격이 낮아진 분입니다. 예를 들어 평균 6,000원이라면, SK하이닉스가 약 139만 원까지 오면 본전이에요.",
     "이런 분은 그 가격을 미리 목표로 정해 두고, 닿으면 비중을 줄이는 계획이 맞습니다. 하루 단위 상품이라 오래 들고 갈수록 불리하니까요."],
    [P("③ 10~11월 물타기 · 평균 6,000원"), P("본전: SK하이닉스 약 139만 원", line=0, at=0.6, color="gold")], src="계산: 흔들림 없이 오른다고 가정 · " + FINE))
S.append(M(["il_L261107s_calendar_flip.jpeg", "vdocuments_39496.mp4"],
    ["세 경우 모두 넣기로 했다면, 한 번에 다 넣기보다 실적 발표처럼 확인할 날짜를 정해 두고 나눠 넣는 편이 낫습니다. 삼성전자 레버리지도 같은 구조라 계산 방법은 똑같아요."],
    [P("확인할 날짜를 정하고 나눠서")], src=FINE))

# ---------- 5장: 회복의 신호 + 밸류노트 (말미 짧게) ----------
S.append(T("회복의 신호", "1월까지 확인할 것"))
S.append(M(["il_L261107m_earnings_call.jpeg", "commons_hbm_3.jpg", "chip_47048.mp4"],
    ["기다리는 동안 볼 것은 ETF 가격이 아닙니다. 1월 말 4분기 실적에서 100원 팔아 80원을 남기던 이익률이 지켜지는지, 그리고 매달 말 나오는 D램 계약 가격의 오르는 폭이 한 자릿수로 줄어드는지예요."],
    [P("① 1월 말 실적 · 이익률"), P("② 매달 말 D램 계약 가격", line=0, at=0.6)], src="트렌드포스 · SK하이닉스 3분기 실적 설명회"))
S.append(M(["il_L261107m_three_items.jpeg", "commons_skhynix_2.jpg"],
    ["끝까지 봐 주신 분들께 하나만 더 말씀드릴게요. 워렌 버핏·벤저민 그레이엄의 기준으로 계산한 SK하이닉스의 밸류노트 점수는 지금 {score}점이고, 바닥이던 2022년 10월에는 73점이었습니다. 이 점수는 지금 이익이 평소보다 얼마나 높은 자리인지도 함께 보기 때문에, 이익이 최고일 때는 오히려 낮게 나와요."],
    [P("SK하이닉스 밸류노트 점수 {score}점", color="gold"), P("2022년 10월 73점", line=0, at=0.6, color="ink")], src="밸류노트 · 점수는 계산 결과이며 늘 맞지는 않음"))

# ---------- 마무리 ----------
S.append({"v": {"type": "media", "full": True, "wash": "none", "lib": "il_L261107s_dawn_phone.jpeg"},
    "lines": ["주가는 이익을 따라 돌아올 수 있습니다. 다만 2배 상품은 그 길이 곧게 날 때만 같이 돌아옵니다."], "sketch_add": [], "en": [""], "asof": False, "src": ""})
S.append({"v": {"type": "media", "full": True, "wash": "none", "lib": "il_L261107s_wafer_hands.jpeg"},
    "lines": ["오늘 쓴 계산은 고정 댓글의 계산기에 그대로 있습니다. 내 평균 산 가격을 넣으면 1년 뒤 계좌와 물을 탈 시점이 바로 나오고, SOXL 같은 3배 상품도 똑같이 계산돼요."], "sketch_add": [], "en": [""], "asof": False, "src": ""})
S.append({"v": {"type": "end", "sub": "", "btn_at": ["0:좋아요", "0:구독", "0:구독"], "note": {"text": "고정 댓글 · 내 계좌 1년 뒤 계산하기"},
    "closing_photo": "il_L261107s_wafer_hands.jpeg", "backdrop": "il_L261107s_dawn_phone.jpeg", "bd_dim": 0.74},
    "lines": ["판단은 결국 ETF 가격이 아니라, 이 회사가 세 달에 얼마를 버는지 위에서 하시는 겁니다. 좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다."],
    "endscreen": 8, "sketch_add": [], "en": [""], "asof": False, "src": ""})

TITLE = "SK하이닉스 레버리지 -91%, 물타기 해도 될까? 주가가 돌아와도 본전 못 오는 이유"
spec = {k: base[k] for k in ["fx", "format", "world", "notebook", "hook", "overlay", "look", "music"]}
spec.update({
    "id": "L261108-lev-91", "company": "000660", "series": "내 계좌 점검", "plan": "P261108-lev-91",
    "events": [{"at": "2026-11-08T10:17:00+09:00", "by": "owner", "what": "채팅 지시 — 오늘 19:30 빼빼로 대신 좁은 타깃 롱폼(SK하이닉스·삼성전자 단일종목 레버리지 ETF), 초반 후킹 세 개, 물타기 방법·현 상황 점검·희망, SOXL 편과 겹치지 않게. 빼빼로는 11/9 19:30으로 이동"}],
    "scheduled_at": "2026-11-08T19:30:00+09:00",
    "opening": "장면형 (5/27 상장 → 첫날 +18% → 1,000만 원이 91만 원 → 주가가 돌아와도 600만 원 → 회사는 83조 → 개인 1,298억 물타기 → 3가지 약속)",
    "hook_type": "장면형 · 보유자 손익 + 결정 질문 (후킹 3개)",
    "endscreen_target": "L261107-soxl-38",
    "title": TITLE,
    "title_en": "SK hynix 2x ETF down 91%: should you average down? Why the account won't recover even if the stock does",
    "tags": ["SK하이닉스", "SK하이닉스 주가", "SK하이닉스 주가 전망", "SK하이닉스 레버리지", "KODEX SK하이닉스단일종목레버리지", "TIGER SK하이닉스단일종목레버리지", "SOL SK하이닉스단일종목레버리지", "삼성전자 레버리지", "삼전닉스 레버리지", "단일종목 레버리지 ETF", "레버리지 ETF 물타기", "물타기", "하이닉스 물타기", "2배 ETF", "코스피 서킷브레이커"],
    "search_keywords": ["SK하이닉스 레버리지", "SK하이닉스 주가 전망", "하이닉스 물타기", "삼성전자 레버리지", "단일종목 레버리지 ETF"],
    "sources": ["국민일보 2026-11-06 (단일종목 레버리지 ETF 고점·종가: KODEX SK하이닉스 44,000원 → 4,000원, KODEX 삼성전자 31,325원 → 5,905원)",
                "뉴스웨이 2026-11-06 (10/1~11/6 개인 순매수: KODEX SK하이닉스단일종목레버리지 1,298억 원)",
                "서울신문 2026-11-06 (SK하이닉스 고점 291만 9천 원, 삼성전자 고점 36만 2,500원, 서킷브레이커, 유안타증권 분석)",
                "머니투데이 2026-05-23 · SBS Biz 2026-05-27 · MTN 2026-05-26 (5월 27일 상장, 첫날 +18%, 사전교육 접속 지연)",
                "SK하이닉스 2026년 3분기 실적·설명회 (10월 28일: 영업이익 83조 3천억 원, 장기 계약, 주주환원) · 2018·2019·2023년 실적",
                "코스피 마감 시황 보도 (11/5 -5.28%, 11/6 -6.02%, 외국인 순매도) · 밸류노트 SK하이닉스 데이터",
                "계산: 1년·연 변동성 55% 가정 단순 계산, 수수료·세금 제외",
                "그림: AI 생성 시네마틱 스틸(실존 인물 아님) · 사진: Wikimedia Commons · 영상: Mixkit·Pexels"],
    "pinned_comment": "영상에 쓴 계산기입니다. 내 평균 산 가격만 넣으면 본전까지의 거리, 1년 뒤 계좌(4가지 경우), 물을 탈 시점이 바로 나옵니다. SOXL·TQQQ 같은 3배 상품도 됩니다 → valuenote.co.kr/lev\n\n여러분은 지금 레버리지로 더 넣고 계신가요, 주식으로 옮기고 계신가요? 기준을 댓글로 나눠 주세요.\n※ 2026년 11월 6일 종가 기준 숫자이며 매수·매도 권유가 아닙니다.\n좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다.",
    "description_head": "SK하이닉스 레버리지 ETF 물타기가 고민이신 분들을 위해 정리했습니다. SK하이닉스 주가 전망과 함께, 단일종목 레버리지 ETF가 왜 주가보다 덜 돌아오는지 계산했습니다.\n\n5월 27일 상장한 SK하이닉스 레버리지 ETF는 고점 4만 4천 원에서 11월 6일 4,000원이 됐습니다(KODEX 기준). 같은 기간 SK하이닉스 주가는 61% 빠졌고, 회사는 세 달 동안 영업이익 83조 원을 벌었습니다.\n\n지금 계좌 점검, 주가가 고점으로 돌아가도 2배 ETF가 본전에 못 닿는 이유, 레버리지로 물타기 vs 주식으로 갈아타기 1년 뒤 계좌 계산(4가지 경우), 그리고 SK하이닉스가 2022~2023년 바닥에서 보여 준 회복의 조건을 정리합니다.\n\n※ 숫자 기준: 2026년 11월 6일 종가. 매수·매도 권유가 아닙니다.\n\n#SK하이닉스 #SK하이닉스주가전망 #레버리지ETF #삼성전자레버리지 #물타기",
    "description_en": "Korea's first single-stock 2x ETFs on Samsung Electronics and SK hynix listed on May 27. By Nov 6 the SK hynix 2x ETF was down 91% while the stock was down 61% — and the company had just earned a record 83 trillion won in one quarter. Where the account stands, why a 2x ETF won't fully recover even if the stock does, and a one-year account calculation: averaging down with leverage vs switching to the stock.",
    "hook_promises": ["지금 계좌 점검 (주식 -61% vs 계좌 -91%, 본전까지 거리)", "물타기 방법 1년 뒤 계좌 계산 (레버리지 vs 주식 · 4가지 경우)", "회복의 조건 (2022~2023 바닥과 지금의 이익)"],
    "viewer_question": "SK하이닉스 레버리지 -91%, 물타면 본전 올까?",
    "format_note": "대표님 11/8 10:17 채팅 지시로 당일 19:30 편성(빼빼로 → 11/9). SOXL 편과 겹침 피함: 리밸런싱·SOXS·1배 ETF·비중 역산은 다루지 않고, 단일종목 2배·한국 상장·주가 고점 회복 시 계좌·1년 뒤 계좌 4경우·회사 이익 회복 근거 중심. 그림은 기존 라이브러리 재사용.",
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
import re
syl = len(re.findall(r"[가-힣0-9A-Za-z]", txt))
print("scenes", len(S), "syllables", syl, "est sec @6.1/s", round(syl / 6.1))
