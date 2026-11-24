import json, os, re, copy
# 금값 전망 3편 — 바닥 신호 5가지 (2026-11-24 대표 07:33~07:34)
# 방향: SOXL 3편(신호 0/5) 다음 날 SOXL +40% → "바닥은 아무도 못 맞힌다" → 금도 신호 1/5
#       → 신호는 '비중을 늘리는 타이밍', 분할 매수는 '놓치지 않는 방법'. 둘을 같이 쓴다. ("가장 현명"이라 단정하지 않음)
# 틀: SOXL 3편(L261123-soxl-3) 최종 v12 — 직접 만든 사진·코드 그래픽 위주, 무료 영상 0, 원음+한국어 자막, 말 속도 1.03, 사진 밝게
HJ = os.environ.get('HJ', '/home/claude/haeja')
LIB = HJ + '/scripts/blog/media/lib/'
OUT = HJ + '/scripts/youtube/long/specs/L261124-gold-3.json'
PENDING = {"gold3_boockvar_kitco.mp4", "gold3_buf_rose_timing.mp4"}   # clip-queue 요청 중(11/24 07:5x) — 도착 전엔 관문 ③이 막는다

def G(stem):   # 2026-11-24 대표 '무료 사진 전부 직접 생성한 사진으로' — il_L261124g_* (확장자 자동)
    for ext in ('.png', '.jpg', '.jpeg', '.webp'):
        if os.path.exists(LIB + stem + ext): return stem + ext
    PENDING.add(stem + '.png'); return stem + '.png'

def cut(*names):
    r = []
    for n in names:
        if n not in PENDING:
            assert os.path.exists(LIB + n), ('missing', n)
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

def SOT(clip, start, dur, lines, name, sub, src, note):
    return {"v": {"type": "media", "full": True, "wash": "none", "cuts": [{"lib": clip, "start": start}], "wash_amt": 0.85, "cine": True, "doc_cine": True, "news_scale": 0.66},
            "sketch_add": [], "asof": False, "src": src,
            "sketch": [{"kind": "lower", "text": name, "sub": sub, "line": 0, "at": 0.3}],
            "lines": lines, "note": note, "news": True,
            "sot": {"clip": clip, "start": start, "dur": dur, "rms": 0.085}}

def punch(t, sub, line=0, at=0.4, color="red"): return {"kind": "punch", "text": t, "sub": sub, "line": line, "at": at, "color": color, "hold": 1.8}
def bars(items, line=0, at=0.4): return {"kind": "bars", "items": items, "line": line, "at": at}
def steps(title, rows, line=0, at=0.3): return {"kind": "steps", "title": title, "rows": rows, "on": None, "line": line, "at": at}
def tl(events, on=None, line=0, at=0.3): return {"kind": "timeline", "events": events, "on": on, "line": line, "at": at}
def quote(rows, by, line=0, at=0.2): return {"kind": "quote", "rows": rows, "by": by, "line": line, "at": at}

sc = []
# v4 (2026-11-24 14:58 대표): 인트로에서 신호 5개 헤드라인만 맛보기 → 본편은 신호 1개 = 1장(소개·해설·과거·지금 숫자) → 백테스트 → 밸류노트의 최선의 대안(3회 분할 매수, 빠르게)
#   겹침 방지: 계기판·그래프 화면 위엔 강조 문구 없음, 이름표가 있는 문장엔 강조 문구 없음. 작은 보조 문구는 없앰.
def GZ(*ks): return ["globe_L261124g_fx_gauge_%s.mp4" % k for k in ks]
def FX(k): return "globe_L261124g_fx_%s.mp4" % k
def P(t, line=0, at=0.4, color="red"): return {"kind": "punch", "text": t, "sub": "", "line": line, "at": at, "color": color, "hold": 2.2}
# ───────── 인트로 (50초 안팎) ─────────
sc.append(S([G("il_L261124g_goldbars_desk"), G("il_L261124g_thumb_goldbars")],
    ["금, 한 돈 101만 원이 66만 원이 됐습니다.", "지금 사도 될까요? 이것부터 보세요."],
    [P("금 -37%", line=0, at=0.45)],
    "TheStreet 2026-11-23(고점 대비 -37.1%) · 헤럴드경제 2026-11-22(한 돈 66만 원대)", "[훅0] 세게 여는 말"))
sc.append(S(GZ("all"),
    ["밸류노트가 과거 금 바닥마다 반복된 신호 5개를 찾았습니다. 실질금리, 연준, 달러, 금 ETF, 그리고 공포 지수.",
     "지금 이 중 몇 개가 켜졌을까요? 과거 바닥에선 몇 개였을까요? 영상이 끝날 때쯤, 직접 백테스트한 결과로 답하겠습니다."],
    [], "밸류노트 금 바닥 계기판 2026-11-24", "[훅] 신호 5개 헤드라인 맛보기 (세부 숫자 없이 '?')"))
BV = os.path.exists(LIB + "gold3_boockvar_aistock.mp4")
bv = SOT("gold3_boockvar_aistock.mp4" if BV else "gold3_boockvar_kitco.mp4", 4.0 if BV else 66.5, 11.1,
    ["금은 지금 AI 주식처럼 취급받고 있습니다.", "금은 AI 주식이 아닙니다. 결국 회복할 겁니다."],
    "피터 부크바", "원포인트 BFG 웰스파트너스 최고투자책임자 · Kitco 2026.10.30", "Kitco 뉴스 2026-11-02 공개(10-30 뉴올리언스 투자 콘퍼런스 녹화)",
    "[훅] 원음① 부크바 — STT 1078.1~1089.0초")
if not BV: bv["sot"].update({"clip": "gold3_boockvar_kitco_audio.mp3", "start": 1078.0})
bv["sot"]["at"] = [[0.1, 4.7], [4.8, 6.2]]
sc.append(bv)
_hj = S(["il_L261124g_huang_return.png", "il_L261113a_trader_gold.jpeg"],
    ["어제 엔비디아에 젠슨 황이 돌아오자, SOXL은 하루 40%, 금은 3.5% 뛰었습니다.",
     "하지만 하루 반등이 바닥을 확인해 주진 않습니다. 그래서 신호로 확인해 보겠습니다."],
    [{"kind": "lower", "text": "젠슨 황", "sub": "엔비디아 창업자 · 최고경영자", "line": 0, "at": 0.15}],
    "야후 파이낸스 2026-11-23(젠슨 황 복귀, SOXL 30.88 → 43.21달러) · 로이터/Kitco 2026-11-23(금 +3.5%)", "[훅] 어제의 반등 — 이름표 있는 문장엔 강조 문구 없음")
_hj["v"]["cut_by_line"] = True
sc.append(_hj)
sc.append({"v": {"type": "media", "full": True, "wash": "none", "cuts": [{"lib": "il_L261116p_wallst_red.png"}], "wash_amt": 0.85, "cine": True, "ident": True},
           "lines": ["현명한 투자를 위한 경제 채널, 밸류노트 지금 시작합니다."], "sketch_add": [], "asof": False, "src": "", "sketch": [], "dur": 6.0, "note": "[로고 인트로] 시그니처"})

# ───────── ① 실질금리 ─────────
sc.append(CH(S(["il_L261123s_bond_glow.png", "il_L261123s_fed_dawn.png"],
    ["첫 번째 신호, 실질금리.", "실질금리는 물가를 뺀 금리입니다. 금은 이자를 주지 않으니, 실질금리가 높을수록 금을 들고 있는 비용이 커집니다."],
    [], "", "[①] 소개"), "① 실질금리"))
sc.append(S(["il_L261113g2_trading_1980.jpeg", "il_L261113g2_gold_2015.jpeg"],
    ["1980년 폴 볼커가 금리를 끌어올리자 금은 2년 동안 52% 빠졌습니다. 2011년부터도 금리 인상 예상에 4년 넘게 42% 빠졌죠.",
     "금리 때문에 빠진 금은 느리고, 길었습니다."],
    [P("1980~82년 -52%", line=0, at=0.35), P("2011~15년 -42%", line=0, at=0.8)],
    "세계금협회(1980.9~1982.6 -52% · 2011.8~2015.12 -42%)", "[①] 과거: 금리형 폭락"))
sc.append(S(["il_L261113g3_cb_vault.jpeg", "il_L261105g_cin_fedbuilding.jpeg"],
    ["이번에도 2월부터 10월까지 금을 끌어내린 건 금리였습니다. 11월 19일 미국 10년 물가연동국채 입찰 금리는 2.903%, 2002년 이후 가장 높았습니다.",
     "물가를 빼고도 3% 가까운 이자를 주는 국채가 있으니, 이자가 없는 금을 들고 있을 이유가 약해진 겁니다."],
    [P("실질금리 2.903%", at=0.78, color="gold")],
    "팁스워치 2026-11-19(10년 물가연동국채 입찰 2.903%)", "[①] 지금"))
sc.append(S(GZ("1"),
    ["시장 금리는 지금 2.77%. 정점을 지나 2.66% 아래로 내려와야 켜집니다. 아직 대기입니다.",
     "그럼 금리를 정하는 연준은 지금 어디를 보고 있을까요?"],
    [], "FRED DFII10(2.77%)", "[①] 계기판 + 리후킹 [R1]"))

# ───────── ② 연준 ─────────
sc.append(CH(S([G("il_L261124g_fed_stone_dawn"), "il_L261113g3_bank_1980.jpeg"],
    ["두 번째 신호, 연준.", "흥미로운 건 2015년입니다. 연준이 금리를 처음 올린 바로 다음 날, 금값은 6년 만의 최저를 찍고 그게 바닥이 됐습니다. 인상이 실제로 나오자, 시장은 불확실성이 끝났다고 본 겁니다.",
     "이번엔 반대였습니다. 11월 10일 물가 발표 뒤 12월 인상 확률이 91%로 뛰자, 금은 하루에 3% 가까이 빠졌습니다."],
    [], "CNN 2015-12-17(첫 금리 인상 다음 날 금값 6년 최저) · 트레이딩이코노믹스 2026-11-10~11(물가 발표 뒤 금 약 -3%, 12월 인상 확률 91%)", "[②] 소개 + 2015 + 이번"), "② 연준"))
sc.append(S(GZ("2"),
    ["지금 시장은 12월 9일 회의에서 금리 인상을 90% 넘게 예상합니다. 인상을 멈춘다는 신호가 나와야 켜집니다. 대기.",
     "그런데 금리만큼 금을 누르는 게 하나 더 있습니다."],
    [], "GoldSilver 2026-11-20(12월 인상 확률 90%대)", "[②] 계기판 + 리후킹 [R2]"))

# ───────── ③ 달러 ─────────
sc.append(CH(S(["il_L261123s_tower_night.png", "il_L261113g2_coin_shop_1980.jpeg"],
    ["세 번째 신호, 달러.", "금은 달러로 값을 매깁니다. 달러가 강해지면 다른 나라 사람들에겐 금이 비싸지니, 수요가 줄어듭니다. 원화로 사는 우리에겐 환율까지 겹치고요.",
     "그래서 원화로 금을 사는 분이라면, 달러가 꺾일 때 환율까지 함께 내려 한국 금값이 더 빠질 수 있다는 점도 기억해 두셔야 합니다."],
    [], "", "[③] 소개"), "③ 달러"))
sc.append(S(GZ("3"),
    ["달러 인덱스는 이번 달 19개월 만의 최고를 찍었고, 아직 꺾이지 않았습니다. 최고점에서 3% 내려오고 50일 평균 아래로 가야 켜집니다. 대기.",
     "그럼 큰손들은 지금 금을 팔고 있을까요, 사고 있을까요?"],
    [], "베이비핍스 2026-11-17(달러 인덱스 19개월 최고) · 밸류노트 계기판(달러지수 104.33)", "[③] 계기판 + 리후킹 [R3]"))

# ───────── ④ 금 ETF ─────────
sc.append(CH(S([FX("etf_cb")],
    ["네 번째 신호, 금 ETF 자금.", "미국 대표 금 ETF에서는 한 달 동안 26억 달러가 빠져나갔습니다. 반대로 세계 중앙은행들은 3분기에 금을 321톤 샀습니다. 1년 전보다 42% 많습니다.",
     "그중 약 200톤은 어느 나라가 샀는지 공개되지도 않았습니다. 개인과 펀드는 팔고, 국가는 조용히 사고 있는 겁니다.",
     "그래서 이 신호는 ETF 자금이 다시 들어오는 순간 켜집니다. 지난 30일은 빠져나갔으니, 아직 꺼져 있습니다."],
    [], "벤징가 2026-11-21(GLD 30일 26억 달러 순유출) · 세계금협회 3분기(중앙은행 321.2톤, +42%, 미공개 매입 약 200톤 · 키트코 2026-11-03)", "[④] 소개 + 큰손 갈림(코드 그래픽)"), "④ 금 ETF"))
sc.append(S([G("il_L261124g_jewelry_window"), "il_L261113g3_coin_jar.jpeg"],
    ["골드만삭스는 최고가를 되찾는 데 2년쯤 걸린다고 봤고, 금 강세론자 피터 쉬프는 큰 하락은 사들일 기회라고 했습니다.",
     "2008년과 2020년엔 바닥 직후 ETF로 돈이 다시 들어왔습니다. 그 유입이 네 번째 신호입니다."],
    [quote(["큰 폭의 금값 하락은", "사들일 기회다"], "피터 쉬프 · 2026.11.19 X", line=0, at=0.55)],
    "헤럴드경제 2026-11-20(골드만삭스 '약 2년') · 피터 쉬프 X 2026-11-19", "[④] 월가 갈림"))
sc.append(S(GZ("4"),
    ["지금은 아직 빠져나가는 중이라 대기입니다.", "그럼 마지막 신호는 어떨까요? 이번 폭락의 진짜 원인과 바로 연결돼 있습니다."],
    [], "벤징가 2026-11-21", "[④] 계기판 + 리후킹 [R4]"))

# ───────── ⑤ 공포 지수 ─────────
sc.append(CH(S(["il_L261113a3_s25_margin.png", "il_L261123s_earnings_desk.png"],
    ["마지막 신호, 공포 지수 VIX.", "VIX는 S&P 500 옵션 가격으로 계산하는 공포 지수로, 평소엔 15에서 20 사이를 오갑니다.", "AI 주식에 빚을 내 투자한 펀드들은 엔비디아가 일주일에 23% 빠지자, 증권사에서 당장 현금을 넣으라는 요구, 마진콜을 받았습니다. 그래서 덜 빠졌고 바로 현금이 되는 금부터 팔았습니다."],
    [steps("마진콜이 금을 파는 순서", [["AI 주식 급락", "엔비디아 1주일 -23%"], ["담보 부족", "증권사가 현금 요구"], ["팔기 쉬운 금부터", "금 1주일 -9%"]], line=2, at=0.1)],
    "파인와이어 2026-11-23(마진콜 구조, 엔비디아 주간 -23%)", "[⑤] 소개 + 마진콜"), "⑤ 공포 지수"))
sc.append(S(["il_L261113a3_s29_wallstreet.jpeg", "il_L261105h_ticker.jpeg"],
    ["CNBC의 팀 시모어는 지금 금이 안전자산이 아니라, 현금을 마련하는 자산이라고 했습니다."],
    [quote(["금은 지금 안전자산이 아니라", "현금 마련용 자산이다"], "팀 시모어 · CNBC 패스트 머니 2026.11.20", line=0, at=0.25)],
    "24/7 월스트리트 2026-11-21(팀 시모어 CNBC 패스트 머니 11-20)", "[⑤] 시모어 인용"))
sc.append(S([FX("g1y")],
    ["11월 20일 금은 14개월 만의 최저까지 갔다가, 젠슨 황이 돌아온 월요일 하루 3.5% 뛰었습니다. 금 자체가 나빠진 게 아니라, 팔기 쉬워서 팔렸다는 뜻입니다."],
    [], "금 선물(GC=F) 종가 · TheStreet 2026-11-23(11.20 14개월 최저) · 로이터/Kitco 2026-11-23(+3.5%)", "[⑤] 금값 1년 그래프(코드)"))
sc.append(S(["il_L261105g_cin_crisis2008.jpeg", "il_L261105g_cin_panic.jpeg"],
    ["2008년 금융위기와 2020년 코로나 때도 금은 이렇게 억지로 팔렸습니다. 그런데 이런 폭락은 빨리 끝났습니다. 2008년 바닥에서 3년 뒤, 금은 125% 올라 있었습니다.",
     "그럼 이번에도 마진콜만 끝나면 2008년처럼 바로 오를까요? 다른 점이 하나 있습니다. 2008년엔 금리를 내렸고, 지금은 올리고 있습니다."],
    [P("3년 뒤 +125%", at=0.85, color="gold")],
    "센추리 파이낸셜(2008.10.24 682.50달러 바닥, 3년 +125.1% · 2020.3 11일 -14.6%)", "[⑤] 과거: 강제 매도형은 빨리 끝남 + [가짜 결말] 2008과 다른 점"))
sc.append(S(GZ("5", "final"),
    ["그 끝을 알려 준 게 공포 지수였습니다. VIX가 30 위로 치솟았다가 30 아래로 내려오면, 억지로 파는 물량이 끝난 경우가 많았습니다. 지난 금요일 35.89였던 VIX가 월요일 26.62로 내려왔습니다. 켜졌습니다.",
     "그래서 지금 금 바닥 신호는 5개 중 1개입니다. 1개면 너무 적은 걸까요?"],
    [], "밸류노트 계기판 시세(VIX 11.20 35.89 → 11.23 26.62)", "[⑤] 계기판 켜짐 + 1/5 + 리후킹 [R5]"))
sc[-1]["v"]["cut_by_line"] = True

# ───────── 과거 4번의 바닥 (백테스트) ─────────
sc.append(CH(S([FX("btest")],
    ["밸류노트가 지난 4번의 금 바닥에 이 신호들을 그대로 대 봤습니다.",
     "2008년, 2015년, 2020년, 2022년. 바닥이던 날 켜진 신호는 매번 0개에서 1개였습니다. 지금과 같습니다.",
     "신호가 2개, 3개로 늘어난 건 바닥에서 한두 달이 지난 뒤였습니다. 그사이 금값은 이미 올랐고, 바닥 3개월 뒤엔 17%에서 35% 높았습니다."],
    [], "밸류노트 백테스트(gold-backtest 2026-11-24): 금 선물 종가 · FRED DFII10·DFF · 달러지수 · VIX. 바닥일 2008-11-13·2015-12-17·2020-03-19·2022-11-03. 3개월 뒤 +34.6%·+20.3%·+17.1%·+18.4%. ④ 금 ETF는 과거 일별 자료가 없어 제외",
    "[백테스트] 바닥 날 0~1개"), "과거 4번의 바닥"))
sc.append(S(["il_L261123s_storm_clearing.png", "il_L261123s_dawn_chip_city.png"],
    ["신호는 바닥을 확인해 주는 지표라 늦게 켜집니다. 가격이 먼저 움직이고, 신호는 따라옵니다.",
     "반대로 하루 크게 올랐다고 바닥이 확인된 것도 아닙니다. 어제 40% 오른 반도체도 켜진 신호는 아직 VIX 하나뿐입니다. 추가 하락 가능성도 열어 둬야 합니다."],
    [P("신호는 늦게 켜진다", line=0, at=0.35, color="gold")],
    "밸류노트 반도체 계기판(2026-11-23 미국 종가, 1/5)", "[백테스트] 결론 — 늦다 + 하루 반등도 확인 아님 [콜백] 인트로 어제 반등"))

# ───────── 밸류노트의 최선의 대안, 분할 매수 ─────────
_bf = SOT("gold3_buf_rose_timing.mp4", 17.6, 8.7,
    ["경기는 돌아섭니다. 6개월 뒤일지 2년 뒤일지는 모르겠습니다.", "2년 쪽이 더 가능성 있겠죠. 한두 달은 아닐 겁니다."],
    "워렌 버핏", "버크셔 해서웨이 회장 · 찰리 로즈 인터뷰 2008.10", "찰리 로즈 2008-10-01 워렌 버핏 인터뷰",
    "[대안] 원음② 버핏 — STT 17.68~26.18초")
_bf["sot"]["at"] = [[0.1, 4.8], [6.1, 2.6]]
sc.append(CH(_bf, "최선의 대안, 분할 매수"))
sc.append(S(["il_L261113g3_coins_rise.jpeg", "il_L261109p_calc_notebook.jpeg"],
    ["워렌 버핏조차 바닥 날짜는 모른다고 했습니다. 너무 일찍 사면 더 빠질 수 있고, 신호만 기다리면 첫 반등을 놓칩니다.",
     "그래서 밸류노트가 판단하는 최선의 대안은 분할 매수입니다."],
    [P("최선의 대안 = 분할 매수", line=1, at=0.2, color="gold")],
    "", "[대안] 왜 분할 매수인가"))
sc.append(S([FX("split08")],
    ["2008년, 고점 대비 20%, 30%, 34% 하락 지점에서 3회 분할 매수했다면 평균 단가는 743달러, 3년 뒤 수익률은 107%였습니다.",
     "20% 하락에 한 번에 샀다면 86%, 바닥을 정확히 맞혔다면 125%. 3회 분할 매수가 바닥을 맞힌 결과에 꽤 가까웠습니다."],
    [], "밸류노트 가정 계산 · 2008.3.17 고점 1,031.90달러 기준 -20%(825.5)·-30%(722.3)·-34%(682.5) 균등 매수, 3년 뒤 1,535달러(센추리 파이낸셜). 그래프는 금 선물 종가. 비용·환율 미반영", "[대안] 2008 3회 분할 매수(코드 그래프)"))
sc.append(S(["il_L261105g_cin_goldload.jpeg", G("il_L261124g_vault_door_open")],
    ["금은 분할 매수에 적합한 자산입니다. 3배 레버리지 상품처럼 출렁이는 동안 값이 녹아내리지 않기 때문입니다.",
     "다만 2011년처럼 길게 빠지면, 분할 매수도 한동안은 마이너스입니다. 손실을 없애는 게 아니라, 후회를 줄이는 방법입니다."],
    [], "", "[대안] 분할 매수에 적합한 자산 + 한계"))
sc.append(SOT("sot_L261122b_rose_fearful.mp4", 11.96, 9.0,
    ["현금이 다른 때보다 더 많은 걸 사 주는 때가 있습니다.", "모을 때가 있고, 쓸 때가 있습니다."],
    "워렌 버핏", "버크셔 해서웨이 회장 · 찰리 로즈 인터뷰 2008.10", "찰리 로즈 2008-10-01 워렌 버핏 인터뷰",
    "[대안] 원음③ 버핏 — STT 11.96~20.96 (편당 재사용 1개)"))
sc.append(S(["il_L261121j_gold_pie.png", "il_L261107s_scale_coins.jpeg"],
    ["그래서 밸류노트의 최선의 대안은, 신호에 맞춘 3회 분할 매수입니다.",
     "지금처럼 신호가 0개에서 1개일 땐 생각한 금액의 3분의 1. 2개, 3개로 늘면 다음 3분의 1. 4개 이상이면 마지막 3분의 1.",
     "신호는 비중을 늘리는 타이밍이고, 분할 매수는 반등을 놓치지 않는 방법입니다. 매수 권유가 아니라 판단 틀의 예시입니다."],
    [steps("밸류노트의 최선의 대안 · 3회 분할 매수 (예시)", [["신호 0~1개", "1/3", "지금"], ["신호 2~3개", "1/3", "다음"], ["신호 4개 이상", "1/3", "마지막"]], line=1, at=0.05)],
    "밸류노트 판단 틀 예시(2026-11-24, 매수 권유 아님)", "[대안] 신호 연동 3회 분할 매수"))
sc.append(S(["il_L261113g2_ring_hand.jpeg", G("il_L261124g_ring_palm")],
    ["1월 고점 근처에서 사신 분은 본전까지 50% 넘게 올라야 합니다. 추가로 사실 땐 간격을 더 넓혀 분할 매수하는 게 맞습니다."],
    [P("본전까지 +50% 이상", at=0.35, color="gold")],
    "고점 대비 -37.1%(TheStreet 2026-11-23) → 본전 회복 필요 상승률 약 +59%", "[대안] 1월 매수자"))
sc.append(S(["il_L261123s_crossroads_person.png", "il_L261123s_fork_road.png"],
    ["확인할 날짜는 세 개입니다. 12월 9일 연준 회의, 12월 물가 발표, 그리고 1월 말 세계금협회의 4분기 금 수요 보고서."],
    [tl([["12.9", "연준 회의"], ["12월", "물가 발표"], ["1월 말", "세계금협회 보고서"]], line=0)],
    "연준 2026 FOMC 일정(12월 8~9일) · 세계금협회 금 수요 동향", "[대안] 확인할 날짜"))
sc.append(S(["globe_L261124g_gold_promo.mp4"],
    ["오늘 본 금 바닥 신호 5개, 같은 이름과 기준으로 밸류노트 계기판에 올려 두었습니다. 신호가 바뀌는 날 알림으로 받아 보실 수 있습니다. 링크는 고정 댓글에 있습니다."],
    [], "", "[대안] 계기판 안내 (새 랜딩 디자인 캡처)", hold=0.4))
sc.append(S([G("il_L261124g_ring_box_macro"), "il_L261105g_cin_cbvault.jpeg"],
    ["처음 들으신 말로 돌아가겠습니다. 금은 지금 AI 주식처럼 취급받고 있다. 금이 다시 금처럼 움직이는 날, 신호가 하나씩 켜질 겁니다.",
     "금, 얼마에 사셨나요? 그리고 신호 몇 개가 켜지면 사실 건가요? 댓글로 남겨 주세요.",
     "밸류노트는 숫자 뒤에 숨은 이야기를 같이 펼쳐 보는 곳입니다. 좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다."],
    [quote(["신호 몇 개가 켜지면", "사실 건가요?"], "댓글로 남겨 주세요", line=1, at=0.2)],
    "", "[엔딩] 북엔드 콜백 + 질문 [콜백] 부크바 원음"))
sc.append({"v": {"type": "end", "sub": "", "btn_at": ["0:거시적", "0:거시적", "0:거시적"], "note": {"text": ""}, "dark_end": True, "end_v2": True,
                 "slogan": ["시장의 흐름 뒤", "숨은 이야기를 읽는 채널", "거시적 관점으로 시장을 이해하면, 투자가 달라집니다"]},
           "lines": ["거시적 관점으로 시장을 이해하면, 투자가 달라집니다. 감사합니다. 밸류노트였습니다."],
           "sketch_add": [], "asof": False, "src": "", "note": "[북엔드] 끝 화면"})

ph = [c["lib"] for x in sc for c in x["v"].get("cuts", []) if c["lib"].startswith("il_")]
dups = sorted({l for l in ph if ph.count(l) > 1})
assert not [c["lib"] for x in sc for c in x["v"].get("cuts", []) if re.match(r'^v[a-z]+_\d+\.mp4$', c["lib"])], "무료 영상 0"

base = json.load(open(HJ + '/scripts/youtube/long/specs/L261123-soxl-3.json'))
spec = {k: base[k] for k in ['format', 'world', 'notebook', 'overlay', 'look', 'roadmap', 'hook', 'music', 'design', 'synthetic_media'] if k in base}
TITLE = "금값 전망 3편, 바닥 신호 5가지 | 한 돈 101만 → 66만 원, 지금 1개 켜졌다"
spec.update({
 "id": "L261124-gold-3", "company": "GOLD", "no_data": True, "series": "금값 전망 시리즈", "plan": "P261124-gold-3",
 "scheduled_at": "2026-11-24T18:00:00+09:00", "manual": True,
 "opening": "한 돈 101만 → 66만 → 신호 5개 헤드라인 맛보기 → 부크바 원음 → 어제 반등(젠슨 황) → 신호로 확인",
 "hook_type": "우리 채널 실제 사례(신호 0/5 다음 날 +40%) + 원음",
 "endscreen_target": "L261113-gold-2", "endscreen_also": "L261123-soxl-3",
 "title": TITLE,
 "doc_title": "금값 바닥 신호 5가지와 3회 분할 매수",
 "title_en": "Gold down 37% from its record: five bottom signals (1 of 5 lit) and why splitting your buys beats guessing the low",
 "description_head": "금값이 1월 최고가에서 37% 빠졌습니다. 지난주 AI 주식발 마진콜로 한 주에 9% 넘게 빠졌다가, 젠슨 황이 돌아온 월요일 하루 만에 3.5% 올랐습니다.\n금 바닥 신호 5가지(실질금리·연준·달러·금 ETF·공포 지수)를 하나씩 풀고 지금 켜진 1개, 과거 4번의 금 바닥 백테스트, 그리고 바닥을 맞힐 수 없을 때 밸류노트가 판단하는 최선의 대안인 3회 분할 매수를 정리합니다.\n\n📟 바닥 계기판(반도체·금 신호, 매일 자동 갱신) 👉 valuenote.co.kr/semi",
 "description_en": "Gold is 37% below its January record. Margin calls tied to the AI-stock rout knocked it down more than 9% in a week before a 3.5% rebound on the day Nvidia reinstated Jensen Huang. We look at the two kinds of gold bear markets in 50 years, five signals that appeared near past bottoms (one is lit now), and how splitting purchases worked in 2008 and 2011 compared with guessing the low. Not investment advice.",
 "pinned_comment": "📟 금·반도체 바닥 계기판(신호 5개, 매일 자동 갱신) 👉 valuenote.co.kr/semi\n신호가 하나라도 켜지거나 꺼지는 날 알림으로 알려 드립니다.\n※ 신호는 늦게 켜집니다. 가격은 신호보다 먼저 움직일 수 있습니다.\n\n금, 얼마에 사셨나요? 신호 몇 개가 켜지면 사실 건가요?\n\n※ 원음: Kitco(피터 부크바), 찰리 로즈 2008(워렌 버핏). 숫자 기준 2026년 11월 23일 미국 종가. 2008년 3회 분할 매수는 가정 계산입니다. 매수·매도 권유가 아닙니다.",
 "hook_promises": ["금 바닥 신호 5가지와 지금 켜진 개수", "과거 4번 바닥 백테스트", "밸류노트의 최선의 대안, 3회 분할 매수"],
 "viewer_question": "금값 바닥은 언제, 지금 사도 될까",
 "tags": ["금값전망", "금값", "금시세", "금시세전망", "금값 바닥", "금 ETF", "KRX 금현물", "분할매수", "금 투자", "은값"],
 "search_keywords": ["금값전망", "금값 바닥", "금시세전망", "금 지금 사도 될까", "분할매수"],
 "sources": ["Kitco 뉴스 2026-11-02(피터 부크바)", "찰리 로즈 2008-10-01(워렌 버핏)", "24/7 월스트리트 2026-11-21(팀 시모어)", "로이터/Kitco 2026-11-23", "TheStreet 2026-11-23", "블룸버그 2026-11-23", "야후 파이낸스 2026-11-23", "팁스워치 2026-11-19", "GoldSilver 2026-11-20", "베이비핍스 2026-11-17", "벤징가 2026-11-21", "세계금협회", "센추리 파이낸셜", "헤럴드경제 2026-11-20·22", "매일경제 2026-11-23", "피터 쉬프 X 2026-11-19", "파인와이어 2026-11-23", "CNN 2015-12-17"],
 "format_note": "v4 2026-11-24 14:58 대표 — 신호 1개=1장 구성, 3회 분할 매수 결론, 금 신호 1/5(VIX 켜짐), 제목·썸네일 '바닥 신호 5가지'",
 "orig_mode": "sot_test", "orig_mode_note": "원음+한국어 자막(더빙 없음). 부크바·버핏(타이밍) 구간은 도착 후 STT로 확정.",
 "voice_speed": 1.03,
 "photo_lift": 1.25,
 "thumb_fixed": "2026-11-24 대표 — 제목·썸네일 '바닥 신호 5가지' 후킹 (drafts/L261124-gold-3_thumbs.py) — 렌더가 덮어쓰지 않게",
 "thumb": {"photo": G("il_L261124g_thumb_goldbars"), "focus_x": 0.6, "l1": "금값 바닥 신호 5가지", "l2": "지금 1개 켜졌다", "pos": "left"},
 "ab_sets": [
  {"key": "a", "default": True, "title": TITLE, "file": "thumb_a.jpg", "type": "A 금값 바닥 신호 5가지 / 지금 1개 켜졌다"},
  {"key": "b", "title": TITLE, "file": "thumb_b.jpg", "type": "B 금값 101만 → 66만 / 바닥 신호 5가지 (2편 틀)"},
  {"key": "c", "title": TITLE, "file": "thumb_c.jpg", "type": "C 금이 AI 주식처럼 팔렸다 / 바닥 신호 5가지"}],
 "scenes": sc,
})
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(spec, open(OUT, 'w'), ensure_ascii=False, indent=1)
narr = sum(len(re.sub(r'[^가-힣0-9A-Za-z]', '', l)) for s in sc if not s.get('sot') for l in s['lines'])
sot = sum(s['sot']['dur'] for s in sc if s.get('sot'))
print('scenes', len(sc), 'narr_syll', narr, 'narr_sec', round(narr / 6.1), 'sot_sec', sot, 'total_min', round((narr / 6.1 + sot) / 60, 1), 'dup_photos', dups)
