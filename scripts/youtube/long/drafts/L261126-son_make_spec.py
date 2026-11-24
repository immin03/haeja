import json, os, re
# 손정의와 AI 버블 (2026-11-24 대표 22:52~23:36) — 기획안: 프로젝트 문서 claude/youtube/drafts/P261126-ai-bubble-plan.md v5
# 개연성 사슬(한 줄): 2000년 '하나만 맞히면 산다'는 교훈 → 그 하나(오픈AI)를 위해 엔비디아까지 판다 → 그래도 모자라 빌리고 보증받는다
#   → 돈이 가장 많이 몰린 6월 1일 "조정은 최고의 기회" → 그날이 꼭대기 → 빚 이자·손실 → 그래도 메모리(SK하이닉스)까지 노린다
#   → 그 사슬 끝에 내 반도체 주식 → 살아남을지는 '하나'(오픈AI)가 빚보다 먼저 결과를 내느냐 → 그래서 볼 숫자(손정의 체온계)
# 원칙: 원음 자막만(더빙 없음), 밸류노트 연결 장 없음, 진행자 컷 2회, 대표 생성 사진은 '○○ 무렵 · 재연 이미지' 표기(_v.png)
HJ = os.environ.get('HJ', '/home/claude/haeja')
LIB = HJ + '/scripts/blog/media/lib/'
OUT = HJ + '/scripts/youtube/long/specs/L261126-son.json'
STT = HJ + '/media/stt/'
PENDING = set()

def G(stem):
    for ext in ('.png', '.jpg', '.jpeg', '.webp', '.mp4'):
        if os.path.exists(LIB + stem + ext): return stem + ext
    PENDING.add(stem + '.png'); return stem + '.png'

def cut(*names):
    r = []
    for n in names:
        n = n if '.' in n else G(n)
        if n not in PENDING: assert os.path.exists(LIB + n), ('missing', n)
        r.append({"lib": n})
    return r

def S(cuts, lines, sketch=None, src="", note="", **kw):
    v = {"type": "media", "full": True, "wash": "none", "cuts": cut(*cuts), "wash_amt": 0.85, "cine": True, "doc_cine": True}
    v.update(kw.pop('v', {}))
    d = {"v": v, "sketch_add": [], "asof": False, "src": src, "sketch": sketch or [], "lines": lines, "note": note}
    d.update(kw)
    return d

def CH(scene, chapter):
    scene["chapter"] = chapter; return scene

def SOT(clip, start, dur, lines, name, sub, src, note, at=None):
    s = {"v": {"type": "media", "full": True, "wash": "none", "cuts": [{"lib": clip, "start": start}], "wash_amt": 0.85, "cine": True, "doc_cine": True, "news_scale": 0.66},
         "sketch_add": [], "asof": False, "src": src,
         "sketch": [{"kind": "lower", "text": name, "sub": sub, "line": 0, "at": 0.3}],
         "lines": lines, "note": note, "news": True,
         "sot": {"clip": clip, "start": start, "dur": dur, "rms": 0.085}}
    if at: s["sot"]["at"] = at
    return s

def PRES(clip, line, note):   # 진행자 컷(턱 아래, 5초) — 내레이션 한 줄
    return {"v": {"type": "media", "full": True, "wash": "none", "cuts": [{"lib": clip}], "wash_amt": 0.85, "cine": False},
            "sketch_add": [], "asof": False, "src": "", "sketch": [], "lines": [line], "note": note}

def P(t, line=0, at=0.4, color="red"): return {"kind": "punch", "text": t, "sub": "", "line": line, "at": at, "color": color, "hold": 2.2}
def steps(title, rows, line=0, at=0.3): return {"kind": "steps", "title": title, "rows": rows, "on": None, "line": line, "at": at}
def tl(events, on=None, line=0, at=0.3): return {"kind": "timeline", "events": events, "on": on, "line": line, "at": at}
def quote(rows, by, line=0, at=0.2): return {"kind": "quote", "rows": rows, "by": by, "line": line, "at": at}
def lower(t, sub, line=0, at=0.15): return {"kind": "lower", "text": t, "sub": sub, "line": line, "at": at}

# 원음 구간(STT로 확정) — 확정 전엔 아래 기본값
SOTS = json.load(open(os.path.join(os.path.dirname(__file__), 'L261126-son_sots.json'))) if os.path.exists(os.path.join(os.path.dirname(__file__), 'L261126-son_sots.json')) else {}
def sot_cfg(key, start, dur, at=None):
    c = SOTS.get(key, {}); return c.get('start', start), c.get('dur', dur), c.get('at', at), c.get('lines')

sc = []
# ───────── 콜드 오픈 (35초) — 두 번의 3일 천하 ─────────
st, du, at, ln = sot_cfg('rub', 30.0, 16.0)
sc.append(SOT(SOTS.get('rub', {}).get('clip', "son_rubenstein_3days_c.mp4"), st, du,
    ln or ["3일 동안, 저는 빌 게이츠보다 부자였습니다.", "그런데 6개월 뒤 주가는 99% 떨어졌습니다.", "거의 파산할 뻔했지만, 어떻게든 살아남았습니다."],
    "손정의", "소프트뱅크그룹 회장 · 블룸버그 루벤스타인 쇼 2017", "블룸버그 「데이비드 루벤스타인 쇼」 2017-10", "[훅] 원음① 3일 천하", at))
sc.append(S(["son_2000_press_v.png", "il_L261114t_dotcom_party", "il_L261117n_tokyo_office_90s"],
    ["손정의입니다. 그 뒤 닷컴 버블이 터지며, 그는 700억 달러를 잃었습니다.",
     "그리고 26년 뒤, 올해 6월 1일. 같은 남자가 다시 카메라 앞에 섰습니다."],
    [P("-99%", line=0, at=0.3)],
    "블룸버그 2017-10-11 · 테크크런치 2025-11-11(2000년 2월 재산 약 780억 달러)", "[훅] 99%"))
st, du, at, ln = sot_cfg('cnbc_hook', 0.0, 7.0)
sc.append(SOT("son_cnbc_paris_50x.mp4", st, du,
    ln or ["AI 혁명은 닷컴보다 10배 이상, 아마 50배는 클 겁니다."],
    "손정의", "소프트뱅크그룹 회장 · CNBC 2026.6.1 파리", "CNBC 2026-06-01 파리 인터뷰(아르준 카르팔)", "[훅] 원음④ 한 문장", at))
sc.append(S(["il_L261107m_trading_red", "il_L261110a_red_screens", "il_L261107m_earnings_drop"],
    ["다음 날 소프트뱅크 주가는 사상 최고를 찍었고, 지금은 3분의 1입니다.",
     "지난주엔 이 남자가 SK하이닉스를 통째로 사려 했다는 보도까지 나왔죠. AI 버블은 끝난 걸까요. 손정의는 이번에도 살아남을까요?"],
    [P("9,074엔 → 3,005엔", line=0, at=0.45)],
    "도쿄증권거래소 소프트뱅크그룹(9984) 2026-06-02 장중 9,074엔 · 2026-11-20 3,005엔(investing.com) · 디인포메이션 2026-11-20",
    "[훅] 반전 + [떡밥] SK하이닉스 + 질문"))
sc.append(S(["il_L261110a_summit_hall", "il_L261107m_dc_plains"],
    ["오늘은 손정의 한 사람을 따라가며, 내 삼성전자와 SK하이닉스가 이 베팅에 얼마나 묶여 있는지까지 보겠습니다."],
    [], "", "[훅] 약속"))
sc.append({"v": {"type": "media", "full": True, "wash": "none", "cuts": [{"lib": "il_L261116p_wallst_red.png"}], "wash_amt": 0.85, "cine": True, "ident": True},
           "lines": ["현명한 투자를 위한 경제 채널, 밸류노트 지금 시작합니다."], "sketch_add": [], "asof": False, "src": "", "sketch": [], "dur": 6.0, "note": "[로고 인트로] 시그니처"})
sc.append(PRES("pres4_a_front.mp4", "시작은 2000년 2월, 도쿄입니다.", "[진행자①] 이야기 시작")); sc[-1]["src"] = "블룸버그 2017-10-11"

# ───────── 3일 천하 — 2000년 ─────────
sc.append(CH(S(["il_L261117n_akihabara_night", "il_L261117n_computer_store_90s", "il_L261114t_crt_office"],
    ["2000년 2월, 손정의의 재산은 일주일에 100억 달러씩 불어났습니다. 미국 야후와 온라인 증권사 이트레이드에 일찍 투자한 덕분이었죠.",
     "본인 말로는, 3일 동안 세계에서 가장 부자였습니다."],
    [lower("손정의", "소프트뱅크그룹 창업자 · 2000년 당시 43세", line=0, at=0.1), P("일주일에 +100억 달러", line=0, at=0.75, color="gold")],
    "블룸버그 2017-10-11(본인 발언)", "[3일 천하] 재산"), "3일 천하"))
sc.append(S(["il_L261110a_hangzhou_office", "il_L261110a_dorm_1990s"],
    ["그 직전, 손정의는 중국 항저우에서 온 영어 교사 출신 창업자를 만났습니다. 몇 분 이야기를 듣더니 바로 투자하겠다고 했습니다.",
     "처음엔 5,000만 달러를 내밀었는데, 창업자가 너무 많다며 사양해 2,000만 달러로 줄였습니다. 그 창업자가 마윈, 회사가 알리바바입니다.",
     "사업 계획도 없던 회사에 왜 돈을 넣었느냐는 질문에, 손정의는 이렇게 답했습니다."],
    [], "CNBC 2014-08-27 · 로이터 2019-12-06(도쿄 포럼, 마윈과 대담)", "[3일 천하] 알리바바 — 재미"))
st, du, at, ln = sot_cfg('ali', 90.0, 30.0)
_ali = SOT("son_rubenstein_3days_a.mp4", st, du, ln or ["눈빛이 아주 강했습니다."],
    "손정의", "소프트뱅크그룹 회장 · 블룸버그 루벤스타인 쇼 2017", "블룸버그 「데이비드 루벤스타인 쇼」 2017-10 · 마윈을 처음 만난 날", "[3일 천하] 원음 알리바바 — 왜 투자했나", at)
sc.append(_ali)
sc.append(S(["il_L261116p_margin_call", "il_L261118a_storm_city"],
    ["그리고 3월, 닷컴 버블이 터졌습니다. 손정의는 그때를 이렇게 기억합니다."],
    [], "나스닥 2000-03-10 고점", "[3일 천하] 붕괴"))
st, du, at, ln = sot_cfg('rub99', 0.0, 22.9)
sc.append(SOT("son_rubenstein_99.mp4", st, du, ln or ["주가는 99% 떨어졌습니다."],
    "손정의", "소프트뱅크그룹 회장 · 블룸버그 루벤스타인 쇼 2017", "블룸버그 「데이비드 루벤스타인 쇼」 2017-10", "[3일 천하] 원음 99%", at))
sc.append(S(["il_L261117n_empty_office_ceo", "il_L261110a_bund_night"],
    ["그를 살린 건 알리바바 하나였습니다. 2,000만 달러는 14년 뒤 알리바바가 상장할 때 500억 달러가 넘었습니다."],
    [P("2,000만 → 500억 달러", line=0, at=0.55, color="gold")],
    "블룸버그 2017 · 포춘 2024-09-17(알리바바 상장 당시 500억 달러 이상)", "[3일 천하] 생존"))
sc.append(S(["il_L261117n_single_chair", "il_L261118a_lighthouse_storm"],
    ["손정의가 여기서 배운 건 하나였습니다. 버블에서 99개가 망해도, 하나만 제대로 맞히면 산다.",
     "이 교훈이 26년 뒤 그를 가장 위험한 자리로 데려갑니다. 그 전에, 그가 두고두고 후회하는 결정부터 보겠습니다."],
    [P("하나만 맞히면 산다", line=0, at=0.5, color="gold")],
    "", "[3일 천하] 열쇠 + [R1]"))

# ───────── 울면서 판 주식 — 엔비디아 ─────────
sc.append(CH(S(["il_L261117n_quiet_hq_dusk", "il_L261117n_gpu_two_cards"],
    ["2017년 손정의는 엔비디아 지분을 약 40억 달러에 샀습니다. 그리고 2019년, 전부 팔았습니다.",
     "그대로 들고 있었다면 2024년엔 1,500억 달러가 넘었을 겁니다."],
    [tl([["2017", "약 40억 달러 매수"], ["2019", "전량 매도"], ["2020", "다시 매수"], ["2025.10", "또 전량 매도"]], line=0, at=0.2)],
    "포춘 2025-11-11 · 야후 파이낸스 2025-11(2019년 매도분, 2024년 가치 1,500억 달러 이상)", "[엔비디아] 2019 매도"), "울면서 판 주식"))
sc.append(S(["il_L261117n_contract_hand", "il_L261121i_signing_desk"],
    ["2020년 다시 사들였다가, 지난해 10월 또 전부 팔았습니다. 58억 3,000만 달러 규모였습니다.",
     "한 달 뒤, 손정의는 이렇게 털어놓았습니다."],
    [P("58억 3,000만 달러", line=0, at=0.5)],
    "블룸버그·포춘 2025-11-11(3,210만 주, 58억 3,000만 달러)", "[엔비디아] 2025 매도"))
st, du, at, ln = sot_cfg('fii', 0.0, 14.0)
sc.append(SOT(SOTS.get('fii', {}).get('clip', "son_fii2025_audio_1.mp3"), st, du,
    ln or ["한 주도 팔고 싶지 않았습니다.", "오픈AI에 투자할 돈이 더 필요했을 뿐입니다.", "엔비디아를 팔면서 울었습니다."],
    "손정의", "소프트뱅크그룹 회장 · FII 프라이어리티 아시아 2025.12.1 도쿄", "FII 연구소 「Building the Asia of Tomorrow: Masayoshi Son」 2025-12-01", "[엔비디아] 원음② 울었다", at))
sc[-1]["v"]["cuts"] = cut("son_portrait_v.png")
sc.append(S(["il_L261118a_hook_chips_cash", "il_L261109p_contract_cash"],
    ["엔비디아를 팔아 마련한 돈은 전부 오픈AI로 갔습니다. 하나만 제대로 맞히면 산다는 2000년의 교훈 그대로입니다.",
     "그런데 그 돈으로도 모자랐습니다. 여기서부터 손정의가 돈을 구하는 방식이 바뀝니다."],
    [], "", "[엔비디아] 교훈 연결 + [R2]"))

# ───────── 전부를 걸다 — 스타게이트 ─────────
sc.append(CH(S(["son_whitehouse_v.png", "il_L261119u_wh_dusk"],
    ["2025년 1월 21일, 트럼프 대통령 취임 다음 날 백악관. 손정의는 오픈AI, 오라클과 함께 5,000억 달러짜리 AI 데이터센터 계획, 스타게이트를 발표했습니다."],
    [P("5,000억 달러", line=0, at=0.75, color="gold")],
    "백악관 2025-01-21 스타게이트 발표", "[스타게이트] 발표"), "전부를 걸다"))
st, du, at, ln = sot_cfg('stargate', 20.0, 14.0)
sc.append(SOT("son_stargate_masa.mp4", st, du,
    ln or ["대통령께서 이러시더군요. 마사, 더 가 봅시다.", "그래서 저는 이렇게 답했습니다. 물론이죠."],
    "손정의", "소프트뱅크그룹 회장 · 백악관 2025.1.21", "백악관 스타게이트 발표 2025-01-21", "[스타게이트] 원음③ 트럼프 흉내 — 재미", at))
sc.append(S(["il_L261119u_sns_feed", "il_L261119u_phones_crowd"],
    ["그런데 몇 시간 뒤, 일론 머스크가 X에 글을 올렸습니다.",
     "샘 올트먼은 틀렸다고 받아쳤죠. 이 말, 22개월 뒤 다시 돌아옵니다."],
    [quote(["그들은 그만한 돈이 없다", "소프트뱅크가 확보한 돈은 100억 달러도 안 된다"], "일론 머스크 · X 2025.1.22", line=0, at=0.5)],
    "테크크런치·포춘·NBC 2025-01-22(머스크 X 게시물, 올트먼 'Wrong' 답글)", "[스타게이트] [떡밥] 머스크 '돈이 없다'"))
sc.append(S(["il_L261114s_loan_papers", "il_L261107m_loan_desk", "il_L261118a_chain_links"],
    ["실제로 손정의는 돈을 어디서 구했을까요. 처음엔 알리바바로 번 돈, 다음엔 엔비디아를 판 돈이었습니다.",
     "그다음은 빌린 돈입니다. 반도체 설계 회사 Arm 주식을 담보로 대출을 받고, 채권을 찍었습니다. 지난 분기 금융비용만 4,619억 엔, 1년 전의 2배가 넘습니다."],
    [steps("손정의가 돈을 구한 순서", [["번 돈", "알리바바"], ["판 돈", "엔비디아 전량 매도"], ["빌린 돈", "Arm 담보 대출 · 채권"], ["남의 보증", "?"]], line=0, at=0.15)],
    "소프트뱅크그룹 2026년 7~9월 실적(금융비용 4,619억 엔) · 빅고 파이낸스 2026-11-10", "[스타게이트] 돈을 구한 순서(계단)"))
sc.append(S(["il_L261116p_capex_cranes", "il_L261114t_dc_build", "il_L261116p_gas_plant_us"],
    ["마지막은 남의 보증입니다. 오픈AI가 20년 동안 빌려 쓸 오하이오 데이터센터에 대해, 엔비디아가 최대 1,050억 달러까지 보증을 섰습니다. 그 데이터센터의 건물주가 소프트뱅크 자회사 SB에너지입니다.",
     "울면서 판 엔비디아 주식, 그 엔비디아의 보증은 받은 셈입니다."],
    [P("보증 한도 1,050억 달러", line=0, at=0.55, color="gold")],
    "엔비디아 3분기(2027 회계연도) CFO 코멘터리 SEC 8-K · PORTS-Pike 4.25GW, 보증 한도 1,050억 달러", "[스타게이트] 아이러니"))
sc.append(S(["il_L261114t_fed", "il_L261113a_dc_aisle"],
    ["이건 손정의만의 방식이 아닙니다. 미국 연준은 이달 보고서에서, AI 데이터센터를 짓기 위한 빚이 올해 10월까지 6,800억 달러를 넘었다고 밝혔습니다. 2023년 한 해엔 1,300억 달러였습니다.",
     "그리고 올해 6월 1일, 손정의는 카메라 앞에서 이렇게 말했습니다."],
    [P("AI 설비 빚 6,800억 달러", line=0, at=0.55)],
    "연준 금융안정보고서 2026-11-13(Box 2.2) · 액시오스 2026-11-16", "[스타게이트] 거시 + [R3]"))

# ───────── 그날이 꼭대기였다 — 2026년 ─────────
st, du, at, ln = sot_cfg('cnbc', 0.0, 20.0)
sc.append(CH(SOT(SOTS.get('cnbc', {}).get('clip', "son_cnbc_paris_50x.mp4"), st, du,
    ln or ["이건 닷컴보다 10배 이상, 아마 50배는 큰 변화입니다.", "조정은 늘 옵니다.", "그때가 오히려 최고의 투자 기회가 될 겁니다."],
    "손정의", "소프트뱅크그룹 회장 · CNBC 2026.6.1 파리", "CNBC 2026-06-01 파리 인터뷰(아르준 카르팔)", "[꼭대기] 원음④ 전체", at), "그날이 꼭대기였다"))
sc.append(S(["son_ohio_v.png", "il_L261105h_parisnight", "il_L261119u_red_board"],
    ["여기까지만 보면, 손정의는 이번에도 맞힌 것처럼 보였습니다. 같은 날 소프트뱅크 시가총액은 22년 만에 도요타를 넘어 일본 1위가 됐고, 다음 날 주가는 9,074엔, 사상 최고였습니다.",
     "그리고 11월 20일, 3,005엔. 6개월 만에 3분의 1이 됐습니다. 2000년의 3일 천하가 26년 만에 다시 나온 겁니다."],
    [tl([["2000.2", "3일간 세계 최고 부자"], ["2000.3~", "-99%"], ["2026.6.2", "9,074엔 최고"], ["2026.11.20", "3,005엔"]], line=1, at=0.1)],
    "CNBC 2026-06-01(도요타 추월) · 국내 보도 2026-11-06(6/2 장중 9,074엔) · investing.com 2026-11-20(3,005엔)", "[가짜 결말] 이번에도 맞힌 듯 → [콜백] 두 번의 3일 천하"))
sc.append(S(["il_L261116p_turbine_loading", "il_L261116p_turbine_blades", "il_L261114t_gas_plant"],
    ["11월 10일 실적 발표에서 소프트뱅크는 3개월 동안 1조 1,200억 엔 순손실을 냈습니다. 시장은 흑자를 예상했었죠.",
     "가장 큰 구멍은 미국 데이터센터에 쓸 가스 터빈을 미리 주문했다가 본 5,972억 엔 손실이었습니다."],
    [P("3개월 순손실 1조 1,200억 엔", line=0, at=0.4)],
    "CNBC 2026-11-10 · 빅고 파이낸스 2026-11-10(전력 설비 5,972억 5,000만 엔)", "[꼭대기] 청구서"))
sc.append(S(["il_L261114t_vote_phone", "il_L261118a_tightrope"],
    ["이달 초 머스크는 다시 X에 글을 올렸습니다. 소프트뱅크가 터빈 주문 대금을 못 갚고 있다는 겁니다. 근거는 내놓지 않았고, 소프트뱅크는 사실이 아니라고 했습니다.",
     "22개월 전, 돈이 없다고 했던 바로 그 사람입니다."],
    [quote(["소프트뱅크가", "터빈 주문을 못 갚고 있다"], "일론 머스크 · X 2026.11.7 (소프트뱅크는 부인)", line=0, at=0.3)],
    "제로헤지 2026-11-07(머스크 X 게시물) · 요미우리 2026-11-11(고토 요시미쓰 CFO 부인)", "[꼭대기] [떡밥 회수] 머스크"))
st, du, at, ln = sot_cfg('chanos', 0.0, 12.0)
sc.append(SOT("chanos_ai_bigger_dotcom.mp4", st, du,
    ln or ["AI 버블은 닷컴 버블보다 훨씬 큽니다."],
    "짐 채노스", "채노스앤드컴퍼니 창업자 · 엔론 붕괴를 먼저 본 공매도 투자자", "짐 채노스 인터뷰 · 2026-06 공개 영상", "[꼭대기] 원음⑤ 반대편", at))
sc.append(S(["il_L261118a_shadow_investor", "il_L261119u_two_paths"],
    ["영화 빅쇼트의 실제 주인공 마이클 버리도 11월 19일 짧은 글을 올렸습니다.",
     "700억 달러를 잃어 본 남자, 그리고 엔론과 2008년을 먼저 본 사람들. 누가 맞을까요. 그 답에 한국 투자자가 빠질 수 없는 이유가, 지난주 보도에 있습니다."],
    [quote(["코어위브, 네비우스, 엔비디아, 반도체", "경고했잖아"], "마이클 버리 · X 2026.11.19", line=0, at=0.3)],
    "모틀리풀 2026-11-19(마이클 버리 X 게시물)", "[꼭대기] 버리 + [R4]"))

# ───────── SK하이닉스, 1조 달러 ─────────
sc.append(CH(S(["il_L261114s_korea_cleanroom", "il_L261121j_fab_night"],
    ["미국 매체 디인포메이션은 11월 20일, 손정의가 SK하이닉스를 약 1조 달러, 우리 돈 1,300조 원이 넘는 금액에 사들이는 방안을 검토하며 월가에 자금 조달을 문의했다고 보도했습니다.",
     "소프트뱅크는 더 이상 적극적으로 검토하지 않는다고 했습니다."],
    [P("SK하이닉스 1조 달러", line=0, at=0.4, color="gold")],
    "디인포메이션 2026-11-20(뉴스1·연합인포맥스 인용, 소프트뱅크 '더 이상 적극 검토 대상 아님')", "[콜백] [떡밥 회수] SK하이닉스 보도"), "SK하이닉스, 1조 달러"))
sc.append(S(["il_L261119u_chess_dark", "son_altman_v.png"],
    ["왜 하필 SK하이닉스였을까요. 손정의는 AI 시대를 바둑판처럼 봅니다. 네 귀퉁이를 차지하면 판을 쥔다는 겁니다. AI 모델은 오픈AI, 반도체 설계는 Arm, 데이터센터는 스타게이트, 그리고 로봇.",
     "그런데 반도체 중에서도 손정의가 갖지 못한 조각이 있습니다. AI 메모리, HBM입니다. 그 HBM을 가장 잘 만드는 회사가 SK하이닉스죠."],
    [], "아주경제 2026-11-11(네 귀퉁이 전략: AI 모델·데이터센터·반도체·피지컬 AI) · 빅고 파이낸스 2026-11", "[SK하이닉스] 왜 하이닉스"))
sc.append(S(["il_L261107m_memory_wafer", "il_L261118a_gpu_racks_gold", "il_L261121j_kr_investor_night"],
    ["이게 내 계좌와 무슨 상관일까요. SK하이닉스와 삼성전자가 만드는 HBM의 가장 큰 손님이 엔비디아이고, 엔비디아 칩의 큰 손님이 오픈AI와 스타게이트입니다.",
     "그래서 손정의의 돈줄이 마르면 메모리 주문이 먼저 흔들리고, 돈줄이 돌면 가장 먼저 웃습니다. 젠슨 황이 돌아온 다음 날 SK하이닉스가 6.7% 오른 것도 같은 이유입니다."],
    [steps("돈이 도는 순서", [["소프트뱅크", "오픈AI · 스타게이트에 투자"], ["오픈AI · 스타게이트", "엔비디아 칩 주문"], ["엔비디아", "SK하이닉스 · 삼성전자 HBM 주문"]], line=0, at=0.15)],
    "코리아중앙데일리·애드혹뉴스 2026-11-24(SK하이닉스 +6.73%)", "[SK하이닉스] 내 계좌"))
sc.append(PRES("pres4_d_hands.mp4", "여기서부터는 밸류노트가 판단하는 대목입니다.", "[진행자②] 판단 시작"))

# ───────── 누가 맞나 ─────────
sc.append(CH(S(["il_L261107m_fiber_glow", "il_L261110a_exchange_night"],
    ["2000년과 지금은 닮았습니다. 설비를 먼저 깔고 돈은 나중에 버는 구조, 장비를 파는 회사가 사는 회사에 돈까지 대 주는 구조도 같습니다.",
     "2000년 통신 장비 회사 루슨트는 고객사에 81억 달러를 외상으로 깔아 줬다가, 고객사들이 쓰러지면서 함께 무너졌습니다."],
    [P("루슨트 외상 81억 달러", line=1, at=0.4)],
    "토마스 퉁구즈 2025-10(루슨트 81억 달러) · 모틀리풀 2026-08-11", "[누가 맞나] 닮은 점"), "누가 맞나"))
sc.append(S(["il_L261119u_investor_desk", "il_L261118a_office_tower_lights"],
    ["다른 점도 있습니다. 미국 주식 전체의 몸값은 닷컴 때보다 낮습니다. S&P 500은 내년 이익의 17.1배, 닷컴 꼭대기에선 25.2배였습니다.",
     "대신 빚이 훨씬 많습니다. 그래서 이번 버블은 주가보다 빚에서 먼저 신호가 옵니다."],
    [P("17.1배 vs 25.2배", line=0, at=0.6, color="gold")],
    "포춘 2026-11-23(JP모건 데이비드 켈리 · S&P 500 선행 PER 17.1배, 닷컴 고점 25.2배)", "[누가 맞나] 다른 점"))
sc.append(S(["il_L261119u_dawn_capital", "il_L261119u_gov_building_rain"],
    ["2000년 버블을 터뜨린 방아쇠는 금리였습니다. 연준이 1999년부터 금리를 계속 올리자, 나스닥은 2년 반 동안 78% 빠졌습니다.",
     "지금 시장은 12월 9일 연준의 금리 인상을 94% 확률로 봅니다. 빚이 가장 많은 손정의에게 금리는 곧 이자입니다."],
    [P("12월 9일 인상 확률 94%", line=1, at=0.35)],
    "포춘 2025-09(연준 1999년 초 4.75% → 2000년 5월 6.5%) · 나스닥 2000-03-10 5,048 → 2002-10-09 1,114 · rateprobability.com 2026-11-23(94%)", "[누가 맞나] 방아쇠"))
sc.append(S(["il_L261117n_hourglass", "il_L261114t_ipo_bell"],
    ["그래서 앞으로는 손정의를 보시면 됩니다. AI 버블에서 돈을 가장 많이 빌린 사람이라, 버블이 식으면 가장 먼저 열이 오르기 때문입니다.",
     "가장 빠른 경보는 소프트뱅크 주가와 부도 위험 보험료입니다. 손정의의 출구는 오픈AI의 다음 투자 유치와 상장 일정이고, 빌린 돈의 값은 12월 9일 금리가 정합니다."],
    [steps("손정의 체온계", [["경보", "소프트뱅크 주가 · 부도 보험료"], ["출구", "오픈AI 투자 유치 · 상장 일정"], ["이자", "12월 9일 연준 금리"]], line=1, at=0.05)],
    "빅고 파이낸스 2026-11(소프트뱅크 부도 보험료 2022년 이후 최고)", "[누가 맞나] 배울 것: 손정의 체온계"))
sc.append(S(["il_L261121j_analyst_call", "il_L261114t_silhouette", "il_L261119u_three_roads"],
    ["이번 주 반등은 젠슨 황 한 사람이 돌아온 겁니다. 손정의의 빚은 그대로입니다.",
     "2000년에도 인터넷은 진짜였습니다. 다만 기술이 이긴 날과 주주가 이긴 날은 25년 차이가 났습니다. 2000년 꼭대기에서 시스코를 산 사람은 작년 12월에야 본전을 찾았습니다.",
     "그래서 밸류노트가 판단하는 최선의 대안은, 손정의처럼 한 번에 전부를 걸지 않는 것. 나눠서 사는 분할 매수입니다."],
    [P("최선의 대안 = 분할 매수", line=2, at=0.45, color="gold")],
    "슬래시닷(FT 인용) 2025-12-11(시스코 80.25달러, 2000-03-27 고점 80.06달러 돌파)", "[누가 맞나] [콜백] 반등 + 판단"))

# ───────── 마무리 ─────────
sc.append(S(["il_L261118a_closing_bridge_dawn", "il_L261118a_seven_towers", "il_L261121i_closing"],
    ["손정의는 2000년에 99%를 잃고도 알리바바 하나로 살아남았습니다. 이번에 그 하나는 오픈AI입니다. 답은 아직 아무도 모릅니다. 다만 다음 신호는 12월 9일 금리에서 옵니다.",
     "손정의는 이번에도 살아남을까요? 여러분의 생각을 댓글로 남겨 주세요.",
     "이 영상 한 편을 위해 며칠을 붙들고 만들었습니다. 도움이 되셨다면 좋아요와 구독으로 응원해 주세요."],
    [], "", "[마무리] 여운 + 질문 + 구독"))
sc.append({"v": {"type": "end", "sub": "", "btn_at": ["0:거시적", "0:거시적", "0:거시적"], "note": {"text": ""}, "dark_end": True, "end_v2": True,
                 "slogan": ["시장의 흐름 뒤", "숨은 이야기를 읽는 채널", "거시적 관점으로 시장을 이해하면, 투자가 달라집니다"]},
           "lines": ["거시적 관점으로 시장을 이해하면, 투자가 달라집니다. 감사합니다. 밸류노트였습니다."],
           "sketch_add": [], "asof": False, "src": "", "note": "[북엔드] 끝 화면"})

ph = [c["lib"] for x in sc for c in x["v"].get("cuts", []) if c["lib"].startswith("il_")]
dups = sorted({l for l in ph if ph.count(l) > 1})

base = json.load(open(HJ + '/scripts/youtube/long/specs/L261124-gold-3.json'))
spec = {k: base[k] for k in ['format', 'world', 'notebook', 'overlay', 'look', 'roadmap', 'hook', 'music', 'design', 'synthetic_media'] if k in base}
TITLE = "닷컴 버블에서 99%를 잃은 남자 | 손정의는 왜 AI 버블에 또 전부를 걸었나"
spec.update({
 "id": "L261126-son", "company": "SOFTBANK", "no_data": True, "series": "", "plan": "P261126-ai-bubble",
 "scheduled_at": "2026-11-26T11:30:00+09:00", "manual": True,
 "opening": "원음 3일 천하 → 99% → 6/1 '50배' → 다음 날 꼭대기 → 3분의 1 → SK하이닉스 떡밥 → 이번 주 반등, 끝났나?",
 "hook_type": "인물 원음 + 날짜 대조(두 번의 3일 천하)",
 "endscreen_target": "L261123-soxl-3", "endscreen_also": "L261124-gold-3",
 "title": TITLE,
 "doc_title": "손정의와 AI 버블",
 "title_en": "He lost 99% in the dot-com crash. Why is Masayoshi Son betting everything on AI again?",
 "description_head": "닷컴 버블 때 3일 동안 세계 최고 부자였다가 6개월 만에 700억 달러를 잃은 손정의. 26년 뒤 그는 엔비디아를 울면서 팔고, 돈을 빌리고, 엔비디아의 보증까지 받아 오픈AI와 스타게이트에 전부를 걸었습니다.\n\"조정이 오면 최고의 기회\"라고 말한 6월 1일, 그날이 소프트뱅크 주가의 꼭대기였습니다. 그리고 지난주, 그가 SK하이닉스를 통째로 사려 했다는 보도가 나왔습니다.\nAI 버블의 돈이 어떻게 굴러가는지, 내 삼성전자·SK하이닉스가 그 사슬에 어떻게 묶여 있는지, 앞으로 무엇을 보면 되는지 정리합니다.\n\n📟 반도체 바닥 신호(매일 자동 갱신) 👉 valuenote.co.kr/semi",
 "description_en": "Masayoshi Son was briefly the world's richest man in February 2000, then lost about $70 billion. Twenty-six years later he sold all of SoftBank's Nvidia shares, borrowed against Arm and leaned on an Nvidia guarantee to go all in on OpenAI and Stargate. We trace how the AI bubble's money moves, what it means for Korean memory makers, and which numbers to watch. Not investment advice. Some images are AI-generated reenactments and are labeled.",
 "pinned_comment": "손정의 돈줄이 흔들리면 반도체가 먼저 움직입니다.\n📟 반도체 바닥 신호(매일 자동 갱신) 👉 valuenote.co.kr/semi\n\n손정의는 이번에도 살아남을까요? 여러분의 생각을 남겨 주세요.\n\n※ 원음: 블룸버그 루벤스타인 쇼 2017, FII 2025, 백악관 2025, CNBC 2026, 짐 채노스. 손정의 사진 일부는 재연 이미지(AI 생성)입니다. 숫자 기준 2026년 11월 24일. 매수·매도 권유가 아닙니다.",
 "hook_promises": ["손정의가 AI에 전부를 건 과정", "내 삼성전자·SK하이닉스가 묶인 사슬", "손정의 체온계 · 앞으로 볼 숫자"],
 "viewer_question": "AI 버블은 끝났나, 손정의는 살아남을까",
 "tags": ["손정의", "소프트뱅크", "AI 버블", "AI버블", "엔비디아", "오픈AI", "SK하이닉스", "삼성전자", "스타게이트", "닷컴버블", "마이클 버리"],
 "search_keywords": ["AI 버블", "손정의", "소프트뱅크 주가", "SK하이닉스 인수", "닷컴 버블"],
 "sources": ["블룸버그 「데이비드 루벤스타인 쇼」 2017", "FII 연구소 2025-12-01", "백악관 2025-01-21", "CNBC 2026-06-01", "짐 채노스 인터뷰", "테크크런치·포춘 2025-01-22", "CNBC 2014-08-27", "로이터·CNN 2019-12-06", "포춘 2025-11-11", "CNBC 2026-11-10", "엔비디아 SEC 8-K", "연준 금융안정보고서 2026-11-13", "디인포메이션 2026-11-20", "모틀리풀 2026-11-19", "포춘 2026-11-23", "제로헤지 2026-11-07", "요미우리 2026-11-11"],
 "format_note": "v5 2026-11-24 대표 — 인물(손정의) 중심, 원음 자막만, 밸류노트 연결 장 없음, 진행자 컷 2회, 재연 이미지 표기",
 "orig_mode": "sot_test", "orig_mode_note": "원음+한국어 자막(더빙 없음). 구간은 media/stt/ 받아쓰기로 확정.",
 "voice_speed": 1.03,
 "photo_lift": 1.25,
 "thumb_fixed": "2026-11-24 — 썸네일은 drafts/L261126-son_thumbs.py에서 따로 만든다",
 "thumb": {"photo": "son_2000_press_clean.png", "focus_x": 0.6, "l1": "99% 잃은 남자", "l2": "또 전부를 걸었다", "pos": "left"},
 "scenes": sc,
})
for _s in spec['scenes']:
    _v = _s.get('v') or {}; _cs = _v.get('cuts') or []
    if len(_cs) < 2 or _v.get('cut_by_line') or any(str(c.get('lib', '')).endswith('.mp4') for c in _cs): continue
    _sec = sum(len(l.replace(' ', '')) for l in _s.get('lines', []) if isinstance(l, str)) / 6.1 + 0.6 * len(_s.get('lines', []))
    _d = round(max(2.5, _sec / len(_cs)), 2)
    for c in _cs[:-1]: c['d'] = _d
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(spec, open(OUT, 'w'), ensure_ascii=False, indent=1)
narr = sum(len(re.sub(r'[^가-힣0-9A-Za-z]', '', l)) for s in sc if not s.get('sot') for l in s['lines'])
sot = sum(s['sot']['dur'] for s in sc if s.get('sot'))
print('scenes', len(sc), 'narr_sec', round(narr / 6.1), 'sot_sec', sot, 'total_min', round((narr / 6.1 + sot) / 60, 1), 'dup_photos', dups, 'pending', sorted(PENDING))
