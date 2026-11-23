import json, os, re, copy
# 금값 전망 3편 — 바닥 신호 5가지 (2026-11-24 대표 07:33~07:34)
# 방향: SOXL 3편(신호 0/5) 다음 날 SOXL +40% → "바닥은 아무도 못 맞힌다" → 금도 신호 1/5
#       → 신호는 '비중을 늘리는 타이밍', 분할 매수는 '놓치지 않는 방법'. 둘을 같이 쓴다. ("가장 현명"이라 단정하지 않음)
# 틀: SOXL 3편(L261123-soxl-3) 최종 v12 — 직접 만든 사진·코드 그래픽 위주, 무료 영상 0, 원음+한국어 자막, 말 속도 1.03, 사진 밝게
HJ = os.environ.get('HJ', '/home/claude/haeja')
LIB = HJ + '/scripts/blog/media/lib/'
OUT = HJ + '/scripts/youtube/long/specs/L261124-gold-3.json'
PENDING = {"gold3_boockvar_kitco.mp4", "gold3_buf_rose_timing.mp4"}   # clip-queue 요청 중(11/24 07:5x) — 도착 전엔 관문 ③이 막는다

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
# ───────── 콜드 오픈 (1분 미만): SOXL 3편 다음 날 +40% → 금도 신호 1/5 → 기다려야 하나 ─────────
sc.append(S(["globe_L261123s_fx_gauge_final.mp4"],
    ["지난 월요일, 저희는 반도체 바닥 신호 5개 중 켜진 게 하나도 없다는 영상을 올렸습니다."],
    [punch("반도체 바닥 신호 0/5", "밸류노트 SOXL 3편 · 2026.11.23 공개", color="gold")],
    "밸류노트 SOXL 3편(2026-11-23 17:10 공개)", "[훅] 0/5 계기판"))
sc.append(S(["il_L261107m_wallst_cheer.jpeg", "il_L261113a_phone_vs_chart.jpeg"],
    ["그리고 바로 그날 밤, 엔비디아 이사회가 젠슨 황을 다시 불러들였습니다. 엔비디아는 하루에 31%, SOXL은 약 31달러에서 43달러로 40% 올랐습니다.",
     "신호를 기다리던 분은, 이 하루를 그대로 놓쳤습니다."],
    [punch("SOXL 하루 +40%", "약 31달러 → 43달러 · 2026.11.23 미국 종가", color="red")],
    "야후 파이낸스 2026-11-23(엔비디아 +31%, 젠슨 황 복귀) · 밸류노트 계기판 시세(SOXL 11.20 30.88 → 11.23 43.21달러)", "[훅] 다음 날 +40%"))
BV = os.path.exists(LIB + "gold3_boockvar_aistock.mp4")   # 1074~1094초 영상 구간 — 도착 전엔 전체 음성 + 키트코 화면(0~120초 중 부크바 장면)
bv = SOT("gold3_boockvar_aistock.mp4" if BV else "gold3_boockvar_kitco.mp4", 4.0 if BV else 66.5, 11.1,
    ["금은 지금 AI 주식처럼 취급받고 있습니다.", "금은 AI 주식이 아닙니다. 결국 회복할 겁니다."],
    "피터 부크바", "원포인트 BFG 웰스파트너스 최고투자책임자 · Kitco 2026.10.30", "Kitco 뉴스 2026-11-02 공개(10-30 뉴올리언스 투자 콘퍼런스 녹화)",
    "[훅] 원음① 부크바 — STT 1078.1~1089.0초 'I think while gold is treated like an AI stock today, which it's not, it is not and it will recover'")
if not BV: bv["sot"].update({"clip": "gold3_boockvar_kitco_audio.mp3", "start": 1078.0})
bv["sot"]["at"] = [[0.1, 4.7], [4.8, 6.2]]
sc.append(bv)
sc.append(S(["il_L261113a_trader_gold.jpeg", "commons_goldbars_1.jpg"],
    ["금도 같은 주에 같은 일을 겪었습니다. 지난주 9% 넘게 빠져 1년 2개월 만의 최저까지 내려갔다가, 같은 월요일 하루 만에 3.5% 튀어 올랐습니다.",
     "금 바닥 신호도 5개 중 아직 1개만 켜졌습니다. 그럼 신호가 다 켜질 때까지 기다려야 할까요?"],
    [punch("금 신호 1/5", "2026.11.23 미국 종가 기준 · 5장에서 하나씩", color="gold")],
    "로이터/Kitco 2026-11-23(현물 +3.5% 3,654.97달러, 지난주 -9% 이상) · TheStreet 2026-11-23(11.20 3,513.54달러, 14개월 최저)", "[훅] 질문"))
sc.append(S(["commons_goldvault_1.jpg"],
    ["오늘은 금이 왜 AI 주식처럼 팔렸는지, 50년 동안 금 폭락이 어떻게 끝났는지, 그리고 바닥을 못 맞히는 우리가 놓치지 않는 방법까지 정리하겠습니다."],
    [], "세계금협회(1980~2015 금 하락장) · 센추리 파이낸셜(2008·2020)", "[약속] 세 가지"))
sc.append({"v": {"type": "media", "full": True, "wash": "none", "cuts": [{"lib": "il_L261116p_wallst_red.png"}], "wash_amt": 0.85, "cine": True, "ident": True},
           "lines": ["현명한 투자를 위한 경제 채널, 밸류노트 지금 시작합니다."], "sketch_add": [], "asof": False, "src": "", "sketch": [], "dur": 6.0, "note": "[로고 인트로] 시그니처"})

# ───────── 1장: 금은 왜 AI 주식처럼 팔렸나 ─────────
sc.append(CH(S(["il_L261113a3_s25_margin.png", "il_L261123s_earnings_desk.png"],
    ["1장, 금은 왜 AI 주식처럼 팔렸나.", "AI 주식에 빚을 내 투자한 펀드가 있다고 해 보겠습니다. 엔비디아가 일주일에 23% 빠지면, 증권사는 담보가 모자라니 당장 현금을 넣으라고 요구합니다. 이걸 마진콜이라고 합니다."],
    [steps("마진콜이 금을 파는 순서", [["AI 주식 급락", "엔비디아 1주일 -23%"], ["담보 부족", "증권사가 현금 요구"], ["팔 수 있는 걸 판다", "덜 빠지고 바로 팔리는 금"]], line=1)],
    "파인와이어 2026-11-23(마진콜 구조, 엔비디아 주간 -23%)", "[1장] 마진콜 구조"), "금은 왜 AI 주식처럼 팔렸나"))
sc.append(S(["il_L261113a_cash_count.jpeg", "il_L261107m_trading_red.jpeg"],
    ["이미 20% 빠진 주식을 팔면 손실이 확정됩니다. 그래서 덜 빠졌고, 가장 빨리 현금으로 바꿀 수 있는 걸 먼저 팝니다. 그게 금이었습니다.",
     "CNBC 패스트 머니의 팀 시모어는 이렇게 표현했습니다. 금은 지금 안전자산이 아니라 현금을 마련하는 자산이라고요."],
    [quote(["금은 지금 안전자산이 아니라", "현금 마련용 자산이다"], "팀 시모어 · CNBC 패스트 머니 2026.11.20", line=1, at=0.3)],
    "24/7 월스트리트 2026-11-21(팀 시모어 CNBC 패스트 머니 11-20 'funding trade… margin calls')", "[1장] 시모어 인용"))
sc.append(S(["il_L261113a3_s29_wallstreet.jpeg", "il_L261105h_ticker.jpeg"],
    ["이번이 처음도 아닙니다. 10월 30일에도 금은 하루에 120달러 넘게 빠져 4,000달러 아래로 내려갔습니다. 그날도 기술주가 함께 무너졌죠.",
     "앞에서 들으신 피터 부크바의 말이 바로 그 주에 나왔습니다. 금이 S&P 500과 유난히 붙어서 움직인다, 이건 억지로 파는 물량이라고요."],
    [punch("10월 30일 하루 -120달러", "4,000달러 아래로 · 같은 날 기술주 급락", color="red")],
    "Kitco 2026-11-04(10월 30일 금 120달러 넘게 하락·4,000달러 아래, 부크바 'forced selling')", "[1장] 10월 30일에도"))
sc.append(S(["il_L261123s_city_lights_on.png", "il_L261113a_chip_wafer_gold.jpeg"],
    ["그래서 금은 주식과 같은 날 빠지고, 같은 날 올랐습니다. 젠슨 황이 돌아온 월요일, 금이 3.5% 뛴 이유도 같습니다. 마진콜이 풀리자 억지로 팔던 물량이 멈춘 겁니다.",
     "금 자체가 나빠진 게 아니라, 팔기 쉬운 자산이라서 팔렸다는 뜻입니다."],
    [bars([{"label": "11.20 저점", "v": 3513.54, "text": "3,513달러", "color": "gray"}, {"label": "11.23", "v": 3654.97, "text": "3,655달러", "color": "gold"}], line=0)],
    "TheStreet 2026-11-23(11.20 3,513.54달러) · 로이터/Kitco 2026-11-23(마진콜로 금 매도, 월요일 +3.5%)", "[1장] 같은 날 빠지고 같은 날 오름"))
sc.append(S(["il_L261113g2_rain_goldshop.jpeg"],
    ["그럼 이건 금에게 좋은 소식일까요, 나쁜 소식일까요? 답은 과거에 있습니다. 금이 이렇게 억지로 팔린 적이 처음이 아니거든요."],
    [], "", "[1장] 리후킹 [R1]"))

# ───────── 2장: 50년, 금 폭락의 두 종류 ─────────
sc.append(CH(S(["il_L261113g2_trading_1980.jpeg", "il_L261113g3_bank_1980.jpeg"],
    ["2장, 50년 동안 금 폭락은 두 종류였습니다.", "첫째는 금리와 달러가 끌어내린 폭락입니다. 1980년 연준 의장 폴 볼커가 금리를 끌어올리자, 금은 2년 동안 52% 빠졌습니다."],
    [punch("1980~82년 -52%", "볼커의 금리 인상 · 세계금협회", line=1, color="red")],
    "세계금협회 'What's a bear case for gold: A historical perspective'(1980.9~1982.6 -52%)", "[2장] 금리형 1980"), "50년, 금 폭락의 두 종류"))
sc.append(S(["il_L261113g2_gold_2015.jpeg", "il_L261123s_fed_dawn.png"],
    ["2011년에도 같았습니다. 금리가 오를 거라는 예상과 강한 달러에 금은 4년 넘게 42% 빠졌습니다. 이런 폭락은 느리고, 길었습니다."],
    [punch("2011~15년 -42%", "4년 4개월 · 1,814달러 → 1,060달러", color="red")],
    "세계금협회(2011.8 1,814달러 → 2015.12 1,060달러, -42%)", "[2장] 금리형 2011"))
sc.append(S(["il_L261105g_cin_crisis2008.jpeg", "il_L261105g_cin_panic.jpeg"],
    ["둘째는 억지로 팔린 폭락입니다. 2008년 금융위기 때 금은 221일 동안 34% 빠졌습니다. 2020년 코로나 때는 11일 만에 15% 빠졌죠.",
     "그런데 이 폭락은 빨리 끝났습니다. 2008년 바닥에서 3년 뒤, 금은 125% 올라 있었습니다."],
    [bars([{"label": "2008 하락", "v": 33.9, "text": "-34%", "color": "red"}, {"label": "바닥 뒤 3년", "v": 125.1, "text": "+125%", "color": "gold"}], line=1)],
    "센추리 파이낸셜 '금의 위기 후 회복'(2008.3.17 1,031.90 → 10.24 682.50달러, 221일, 3년 +125.1% · 2020.3.9~3.20 -14.6%, 11일)", "[2장] 강제 매도형"))
sc.append(S(["il_L261105g_cin_vaultclose.jpeg"],
    ["정리하면 금리 때문에 빠진 금은 오래 걸렸고, 억지로 팔린 금은 빨리 돌아왔습니다. 금 폭락은 깊이보다 종류가 결과를 갈랐습니다.",
     "문제는, 이번 폭락이 둘 중 하나가 아니라는 겁니다."],
    [steps("금 폭락 두 종류", [["금리·달러형", "1980년 · 2011년", "느리고 길다"], ["강제 매도형", "2008년 · 2020년", "빠르고 짧다"]])],
    "세계금협회 · 센추리 파이낸셜", "[2장] 정리 + 리후킹 [R2]"))

# ───────── 3장: 이번엔 둘이 겹쳤다 ─────────
sc.append(CH(S(["il_L261113g3_cb_vault.jpeg", "il_L261105g_cin_fedbuilding.jpeg"],
    ["3장, 이번엔 둘이 겹쳤습니다.", "1월 28일 금은 5,589달러로 사상 최고였습니다. 2월부터 10월까지는 금리와 달러가 끌어내렸습니다. 미국 10년 물가연동국채 금리는 11월 19일 입찰에서 2.903%, 2002년 이후 가장 높았습니다."],
    [punch("실질금리 2.903%", "미국 10년 물가연동국채 입찰 · 2026.11.19 · 2002년 이후 최고", line=1, color="gold")],
    "TheStreet 2026-11-23(1월 28일 최고 5,589달러) · 팁스워치 2026-11-19(10년 물가연동국채 입찰 2.903%)", "[3장] 1단계 금리형"), "이번엔 둘이 겹쳤다"))
sc.append(S(["il_L261123s_empty_wallet.png", "il_L261113g2_rings_velvet.jpeg"],
    ["그리고 11월, 그 위에 AI 주식발 마진콜이 겹쳤습니다. 천천히 빠지던 금이 한 주 만에 9% 넘게 떨어진 이유입니다.",
     "고점에서 지금까지 37% 빠졌습니다. 한 돈에 101만 원 하던 금이 66만 원대가 됐습니다."],
    [punch("한 돈 101만 원 → 66만 원대", "1월 고점 → 2026.11.22 · 국제 금값 고점 대비 -37%", color="red")],
    "TheStreet 2026-11-23(고점 대비 -37.1%) · 헤럴드경제 2026-11-22(한 돈 66만 원대)", "[3장] 2단계 강제 매도"))
sc.append(S(["commons_jewelryshop_1.jpg", "il_L261113g3_coin_jar.jpeg"],
    ["큰손들도 갈라졌습니다. 미국 대표 금 ETF에서는 한 달 동안 26억 달러가 빠져나갔습니다.",
     "반대로 세계 중앙은행들은 3분기에 금을 321톤 샀습니다. 1년 전보다 42% 많습니다. 한국 개인들도 금값이 빠지자 사들이고 있고요."],
    [bars([{"label": "미국 금 ETF 30일", "v": 26, "text": "-26억 달러", "color": "red"}, {"label": "중앙은행 3분기", "v": 321, "text": "+321톤", "color": "gold"}], line=1)],
    "벤징가 2026-11-21(GLD 30일 26억 달러 순유출) · 세계금협회 3분기(중앙은행 321.2톤, +42%) · 매일경제 2026-11-23(개인 저가 매수)", "[3장] 큰손 갈림"))
sc.append(S(["il_L261123s_dice_desk.png", "il_L261113g2_cb_vault_door.jpeg"],
    ["월가 전망도 정반대입니다. 골드만삭스는 금이 최고가를 되찾는 데 2년쯤 걸린다고 봤습니다.",
     "금 강세론자 피터 쉬프는 이렇게 썼습니다."],
    [quote(["큰 폭의 금값 하락은", "사들일 기회다"], "피터 쉬프 · 2026.11.19 X", line=1, at=0.2)],
    "헤럴드경제 2026-11-20(골드만삭스 '최고치 회복까지 약 2년') · 피터 쉬프 X 2026-11-19('The big drop in gold is an opportunity to buy')", "[3장] 월가 대립"))
sc.append(S(["il_L261123s_bond_glow.png", "commons_goldcert_1.jpg"],
    ["그럼 마진콜만 끝나면 2008년처럼 바로 오를까요? 그때와 지금은 금리가 정반대입니다. 2008년엔 금리를 내렸고, 지금은 올리고 있습니다.",
     "그래서 필요한 게, 바닥에서 반복된 신호입니다."],
    [], "", "[가짜 결말] 2008과 다른 점"))

# ───────── 4장: 금 바닥 신호 5가지 ─────────
GAUGE = [["① 실질금리", "정점 뒤 2.66% 아래로", "2.77% · 대기"],
         ["② 연준", "12월 9일 인상 멈춤 신호", "인상 확률 90%대 · 대기"],
         ["③ 달러", "정점 찍고 하락", "19개월 최고권 · 대기"],
         ["④ 금 ETF", "유출 멈추고 유입", "30일 -26억 달러 · 대기"],
         ["⑤ 공포 VIX", "30 위 → 30 아래로", "35.89 → 26.62 · 켜짐"]]
sc.append(CH(S(["commons_goldvault_2.jpg"],
    ["4장, 금 바닥 신호 5가지.", "과거 금 바닥에서 반복된 신호를 5개로 정리했습니다. 하나씩 지금 숫자에 대 보겠습니다."],
    [steps("금 바닥 신호 5가지", [r[:2] for r in GAUGE], line=1)],
    "", "[4장] 신호 소개"), "금 바닥 신호 5가지"))
sc.append(S(["commons_nyfedvault_1.jpg", "commons_nyfedvault_2.jpg"],
    ["첫째, 실질금리. 물가를 뺀 금리가 높을수록 이자가 없는 금은 불리합니다. 입찰에선 2.9%까지 올랐고, 시장 금리는 지금 2.77%입니다. 2.66% 아래로 내려와야 켜지니, 아직 대기입니다.",
     "둘째, 연준. 12월 9일 회의에서 금리 인상을 멈춘다는 신호가 나와야 합니다. 2015년 12월 첫 인상 직후가 4년 하락의 바닥이었습니다. 지금 시장은 인상 쪽에 무게를 싣고 있어, 이것도 대기."],
    [steps("금 바닥 신호", [GAUGE[0], GAUGE[1]])],
    "팁스워치 2026-11-19(실질금리 2.903%) · FRED DFII10(2.77%) · GoldSilver 2026-11-20(12월 인상 확률 99%) · CNN 2015-12-17(첫 인상 다음 날 금값 6년 최저)", "[4장] 신호 ①②"))
sc.append(S(["commons_goldbars_2.jpg"],
    ["셋째, 달러. 금은 달러로 값을 매기니 달러가 강하면 금이 눌립니다. 달러 인덱스는 이번 달 19개월 만의 최고를 찍었고, 아직 꺾이지 않았습니다.",
     "넷째, 금 ETF. 2008년과 2020년엔 바닥 직후 ETF로 돈이 다시 들어왔습니다. 지금은 아직 빠져나가는 중입니다."],
    [steps("금 바닥 신호", [GAUGE[2], GAUGE[3]])],
    "베이비핍스 2026-11-17(달러 인덱스 19개월 최고) · 벤징가 2026-11-21(GLD 30일 순유출)", "[4장] 신호 ③④"))
sc.append(S(["il_L261121j_kr_investor_night.png", "il_L261108v_lev_calc.jpeg"],
    ["다섯째, 공포 지수 VIX. 30 위로 치솟았다가 30 아래로 내려올 때, 억지로 파는 물량이 끝났습니다. 지난 금요일 35.89였던 VIX가 젠슨 황이 돌아온 월요일 26.62로 내려왔습니다. 이건 켜졌습니다.",
     "그래서 지금 금 바닥 신호는 5개 중 1개입니다."],
    [steps("금 바닥 신호 1/5", GAUGE)],
    "밸류노트 계기판 시세(VIX 11.20 35.89 → 11.23 26.62)", "[4장] 신호 ⑤ + 1/5"))
sc.append(S(["globe_L261123s_fx_gauge_final.mp4"],
    ["그런데 여기서 꼭 짚어야 할 게 있습니다. 반도체도 신호가 0개였는데, 하루에 40%가 올랐습니다.",
     "신호는 바닥을 확인해 주는 지표라 늦게 켜집니다. 가격은 늘 신호보다 먼저 움직입니다. 신호만 기다리면, 가장 크게 오르는 첫날을 놓칠 수 있습니다."],
    [punch("신호는 늦게 켜진다", "SOXL 신호 0/5 → 다음 날 +40%", color="red")],
    "밸류노트 SOXL 3편(2026-11-23) · 계기판 시세(SOXL 11.20 30.88 → 11.23 43.21달러)", "[4장] 반례 — 신호는 늦다 [R3]"))

# ───────── 5장: 바닥을 못 맞히는 우리가 놓치지 않는 법 ─────────
_bf = SOT("gold3_buf_rose_timing.mp4", 17.6, 8.7,
    ["경기는 돌아섭니다. 6개월 뒤일지 2년 뒤일지는 모르겠습니다.", "2년 쪽이 더 가능성 있겠죠. 한두 달은 아닐 겁니다."],
    "워런 버핏", "버크셔 해서웨이 회장 · 찰리 로즈 인터뷰 2008.10", "찰리 로즈 2008-10-01 워런 버핏 인터뷰",
    "[5장] 원음② 버핏 — STT 확정 17.68~26.18초 'They will turn around … six months or two years … not one month or two months'")
_bf["sot"]["at"] = [[0.1, 4.8], [6.1, 2.6]]
sc.append(CH(_bf, "놓치지 않는 법, 나눠 사기"))
sc.append(S(["il_L261123s_dawn_chip_city.png"],
    ["지난 월요일로 돌아가 보겠습니다. 하루 40%를 다 잡은 사람은 거의 없습니다. 신호를 기다린 사람은 아무것도 못 잡았고요.",
     "그런데 생각한 금액의 3분의 1이라도 미리 넣어 둔 사람은, 그 하루의 3분의 1을 가져갔습니다. 바닥을 맞히진 못해도, 아예 놓치지는 않은 겁니다."],
    [punch("3분의 1만 넣어 둬도", "오른 날의 3분의 1은 내 것", color="gold")],
    "", "[5장] SOXL 월요일로 본 나눠 사기 [콜백] 콜드 오픈 +40%"))
sc.append(S(["il_L261113g3_coins_rise.jpeg", "il_L261109p_calc_notebook.jpeg"],
    ["버핏조차 바닥 날짜는 모른다고 했습니다. 그럼 바닥을 맞힐 수 없는 우리는 어떻게 해야 할까요? 답은 나눠 사는 겁니다.",
     "2008년으로 가 보겠습니다. 고점 대비 20%, 30%, 34% 빠졌을 때 세 번 나눠 샀다면 평균 단가는 743달러. 3년 뒤 수익률은 107%였습니다.",
     "20% 빠졌을 때 한 번에 다 샀다면 86%. 바닥 682달러를 정확히 맞혔다면 125%. 나눠 산 쪽이 바닥을 맞힌 사람에 꽤 가까웠습니다."],
    [bars([{"label": "-20%에 한 번에", "v": 86, "text": "+86%", "color": "gray"}, {"label": "세 번 나눠", "v": 107, "text": "+107%", "color": "gold"}, {"label": "바닥 정확히", "v": 125, "text": "+125%", "color": "gray"}], line=1)],
    "밸류노트 가정 계산 · 2008.3.17 고점 1,031.90달러 기준 -20%(825.5)·-30%(722.3)·-34%(682.5) 균등 매수, 3년 뒤 1,535달러(바닥 대비 +125.1%, 센추리 파이낸셜). 실제 체결가·비용·환율 미반영", "[5장] 2008 분할 매수 계산"))
sc.append(S(["il_L261123s_hourglass_wafer.png", "il_L261113g2_coin_shop_1980.jpeg"],
    ["반대로 길게 빠진 2011년은 어땠을까요? 고점 대비 20% 빠진 2013년 봄에 한 번에 산 분은, 원금을 되찾는 데 6년이 넘게 걸렸습니다.",
     "같은 지점부터 20%, 30%, 40%에서 세 번 나눠 산 분은 평균 단가가 1,270달러 근처라, 2016년 초에 원금을 되찾았습니다. 나눠 사면 바닥을 못 맞혀도, 버티는 시간이 짧아집니다."],
    [bars([{"label": "-20%에 한 번에", "v": 6.3, "text": "약 6년", "color": "red"}, {"label": "세 번 나눠", "v": 2.8, "text": "약 3년", "color": "gold"}], line=1)],
    "밸류노트 가정 계산 · 2011.8 고점 1,814달러 기준 -20%(1,451)·-30%(1,270)·-40%(1,088) 균등 매수, 원금 회복 시점은 월평균 시세 기준 근삿값(세계금협회·LBMA). 비용·환율 미반영", "[5장] 2011 분할 매수 계산"))
sc.append(S(["il_L261105g_cin_goldload.jpeg"],
    ["그리고 금은 나눠 사기에 잘 맞는 자산입니다. SOXL 같은 3배 상품은 출렁이는 동안 값이 녹아내리지만, 금은 1배라 나눠 사는 동안 그런 손실이 없습니다.",
     "다만 나눠 산다고 손실이 없는 건 아닙니다. 2011년처럼 길게 빠지면, 나눠 산 분도 한동안은 마이너스입니다. 바닥을 맞힐 수 없을 때, 후회를 가장 줄이는 방법이라는 뜻입니다."],
    [], "", "[5장] 금이 나눠 사기에 맞는 이유 + 한계"))
sc.append(SOT("sot_L261122b_rose_fearful.mp4", 11.96, 9.0,
    ["현금이 다른 때보다 더 많은 걸 사 주는 때가 있습니다.", "모을 때가 있고, 쓸 때가 있습니다."],
    "워런 버핏", "버크셔 해서웨이 회장 · 찰리 로즈 인터뷰 2008.10", "찰리 로즈 2008-10-01 워런 버핏 인터뷰",
    "[5장] 원음③ 버핏 — STT 11.96~20.96 (L261122b에서 쓴 원본, 편당 재사용 1개)"))
sc.append(S(["il_L261121j_gold_pie.png", "il_L261107s_scale_coins.jpeg"],
    ["그래서 신호와 나눠 사기를 같이 쓰는 방법을 예시로 정리했습니다.",
     "지금처럼 신호가 0개에서 1개일 땐 생각한 금액의 3분의 1만. 신호가 2개, 3개로 늘면 다음 3분의 1. 4개 이상이면 마지막 3분의 1.",
     "신호는 비중을 늘리는 타이밍이고, 나눠 사기는 놓치지 않는 방법입니다. 매수 권유가 아니라, 판단 틀의 예시입니다."],
    [steps("신호 + 나눠 사기 (예시)", [["신호 0~1개", "1/3", "지금"], ["신호 2~3개", "1/3", "다음"], ["신호 4개 이상", "1/3", "마지막"]], line=1)],
    "밸류노트 판단 틀 예시(2026-11-24, 매수 권유 아님)", "[5장] 판단 틀"))
sc.append(S(["il_L261113g2_ring_hand.jpeg", "commons_goldring_1.jpg"],
    ["1월에 한 돈 100만 원 근처에서 사신 분은 본전까지 50% 넘게 올라야 합니다. 과거 금리형 폭락이면 몇 년이 걸릴 수 있어, 추가로 살 땐 더 천천히 나누는 게 맞습니다.",
     "장롱 속 돌반지는 살 때와 팔 때 값 차이가 커서, 1편에서 본 기준대로 따로 판단하시면 됩니다."],
    [punch("본전까지 +50% 이상", "1월 고점 매수 기준 · 지금 -37%", color="gold")],
    "고점 대비 -37.1%(TheStreet 2026-11-23) → 본전 회복 필요 상승률 약 +59%(1÷0.629)", "[5장] 상황별"))
sc.append(S(["il_L261123s_crossroads_person.png", "il_L261123s_fork_road.png"],
    ["확인할 날짜는 세 개입니다. 12월 9일 연준 회의, 12월 물가 발표, 그리고 1월 말 세계금협회의 4분기 금 수요 보고서."],
    [tl([["12.9", "연준 회의"], ["12월", "물가 발표"], ["1월 말", "세계금협회 보고서"]], line=0)],
    "연준 2026 FOMC 일정(12월 8~9일) · 세계금협회 금 수요 동향(분기 다음 달 말 발표)", "[5장] 확인할 날짜"))
sc.append(S(["globe_L261124g_gold_promo.mp4"],
    ["오늘 본 금 바닥 신호 5개, 같은 이름과 기준으로 밸류노트 계기판에 올려 두었습니다. 신호가 바뀌는 날 알림으로 받아 보실 수 있습니다. 링크는 고정 댓글에 있습니다."],
    [], "", "[5장] 계기판 안내 (valuenote.co.kr/semi?tab=gold 11/23 마감 화면 캡처)", hold=0.4))
sc.append(S(["commons_goldring_2.jpg", "il_L261105g_cin_cbvault.jpeg"],
    ["처음 들으신 말로 돌아가겠습니다. 금은 지금 AI 주식처럼 팔리고 있다. 금이 다시 금처럼 움직이는 날, 신호가 하나씩 켜질 겁니다.",
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
 "opening": "SOXL 3편 신호 0/5 → 다음 날 +40% → 부크바 원음 '금은 AI 주식처럼 취급' → 금 -9% 뒤 +3.5% → 금 신호 1/5, 기다려야 하나 → 약속",
 "hook_type": "우리 채널 실제 사례(신호 0/5 다음 날 +40%) + 원음",
 "endscreen_target": "L261113-gold-2", "endscreen_also": "L261123-soxl-3",
 "title": TITLE,
 "doc_title": "금값 바닥 신호 5가지와 나눠 사기",
 "title_en": "Gold down 37% from its record: five bottom signals (1 of 5 lit) and why splitting your buys beats guessing the low",
 "description_head": "금값이 1월 최고가에서 37% 빠졌습니다. 지난주 AI 주식발 마진콜로 한 주에 9% 넘게 빠졌다가, 젠슨 황이 돌아온 월요일 하루 만에 3.5% 올랐습니다.\n50년 동안 금 폭락이 끝난 두 가지 방식(금리·달러형, 강제 매도형), 지금 켜진 바닥 신호 5가지 중 1개, 그리고 바닥을 맞힐 수 없을 때 나눠 사기가 2008년·2011년에 어떤 결과였는지 정리합니다.\n\n📟 바닥 계기판(반도체·금 신호, 매일 자동 갱신) 👉 valuenote.co.kr/semi",
 "description_en": "Gold is 37% below its January record. Margin calls tied to the AI-stock rout knocked it down more than 9% in a week before a 3.5% rebound on the day Nvidia reinstated Jensen Huang. We look at the two kinds of gold bear markets in 50 years, five signals that appeared near past bottoms (one is lit now), and how splitting purchases worked in 2008 and 2011 compared with guessing the low. Not investment advice.",
 "pinned_comment": "📟 금·반도체 바닥 계기판(신호 5개, 매일 자동 갱신) 👉 valuenote.co.kr/semi\n신호가 하나라도 켜지거나 꺼지는 날 알림으로 알려 드립니다.\n※ 신호는 늦게 켜집니다. 가격은 신호보다 먼저 움직일 수 있습니다.\n\n금, 얼마에 사셨나요? 신호 몇 개가 켜지면 사실 건가요?\n\n※ 원음: Kitco(피터 부크바), 찰리 로즈 2008(워런 버핏). 숫자 기준 2026년 11월 23일 미국 종가. 2008·2011 나눠 사기는 가정 계산입니다. 매수·매도 권유가 아닙니다.",
 "hook_promises": ["금이 AI 주식처럼 팔린 이유", "50년 금 폭락의 두 종류", "바닥을 못 맞혀도 놓치지 않는 방법"],
 "viewer_question": "금값 바닥은 언제, 지금 사도 될까",
 "tags": ["금값전망", "금값", "금시세", "금시세전망", "금값 바닥", "금 ETF", "KRX 금현물", "분할매수", "금 투자", "은값"],
 "search_keywords": ["금값전망", "금값 바닥", "금시세전망", "금 지금 사도 될까", "분할매수"],
 "sources": ["Kitco 뉴스 2026-11-02(피터 부크바)", "찰리 로즈 2008-10-01(워런 버핏)", "24/7 월스트리트 2026-11-21(팀 시모어)", "로이터/Kitco 2026-11-23", "TheStreet 2026-11-23", "블룸버그 2026-11-23", "야후 파이낸스 2026-11-23", "팁스워치 2026-11-19", "GoldSilver 2026-11-20", "베이비핍스 2026-11-17", "벤징가 2026-11-21", "세계금협회", "센추리 파이낸셜", "헤럴드경제 2026-11-20·22", "매일경제 2026-11-23", "피터 쉬프 X 2026-11-19", "파인와이어 2026-11-23", "CNN 2015-12-17"],
 "format_note": "v1 2026-11-24 대표 07:33~07:34 — SOXL 3편 다음 날 +40% 사례로 '신호는 늦다 + 나눠 사기' 결론, 금 신호 1/5(VIX 켜짐), 제목·썸네일 '바닥 신호 5가지'",
 "orig_mode": "sot_test", "orig_mode_note": "원음+한국어 자막(더빙 없음). 부크바·버핏(타이밍) 구간은 도착 후 STT로 확정.",
 "voice_speed": 1.03,
 "photo_lift": 1.25,
 "thumb_fixed": "2026-11-24 대표 — 제목·썸네일 '바닥 신호 5가지' 후킹 (drafts/L261124-gold-3_thumbs.py) — 렌더가 덮어쓰지 않게",
 "thumb": {"photo": "commons_goldbars_1.jpg", "focus_x": 0.6, "l1": "금값 바닥 신호 5가지", "l2": "지금 1개 켜졌다", "pos": "left"},
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
