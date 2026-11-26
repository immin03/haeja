import json, os, re
# 금리의 모든 것 — 이자는 원래 죄였다 (2026-11-26 대표) — 대본: 프로젝트 문서 claude/youtube/drafts/L261204-rate-script.md v3
# 기준: 청소년도 '재밌고 이해하기 쉬웠다'고 느끼는 교육 영상, 시의성(특정 회의 날짜·확률) 없이 오래 볼 영상, 썰 중심·숫자는 파동 장에서만, 열린 결말
# v6 2026-11-25: 기승전결 재구성(약력·위워크·쿠팡·멈출 수 없는 남자·시간 싸움), 실제 영상 우선, 코드 그래픽 9종
# 개연성 사슬(한 줄): 2000년 '하나만 맞히면 산다'는 교훈 → 그 하나(오픈AI)를 위해 엔비디아까지 판다 → 그래도 모자라 빌리고 보증받는다
#   → 돈이 가장 많이 몰린 6월 1일 "조정은 최고의 기회" → 그날이 꼭대기 → 빚 이자·손실 → 그래도 메모리(SK하이닉스)까지 노린다
#   → 그 사슬 끝에 내 반도체 주식 → 살아남을지는 '하나'(오픈AI)가 빚보다 먼저 결과를 내느냐 → 그래서 볼 숫자(손정의 체온계)
# 원칙: 원음 자막만(더빙 없음), 밸류노트 연결 장 없음, 진행자 컷 2회, 대표 생성 사진은 '○○ 무렵 · 재연 이미지' 표기(_v.png)
HJ = os.environ.get('HJ', '/home/claude/haeja')
LIB = HJ + '/scripts/blog/media/lib/'
OUT = HJ + '/scripts/youtube/long/specs/L261204-rate.json'
STT = HJ + '/media/stt/'
PENDING = set()

def G(stem):
    for ext in ('.png', '.jpg', '.jpeg', '.webp', '.mp4'):
        if os.path.exists(LIB + stem + ext): return stem + ext
    PENDING.add(stem + '.png'); return stem + '.png'

import subprocess
def V(name, start, dur):   # 2026-11-25 v6: 실제 영상(소리 없이)에서 필요한 구간만 잘라 쓴다 — 같은 원본도 구간마다 다른 파일
    out = f"{name}__{int(start)}_{int(dur)}.mp4"
    if not os.path.exists(LIB + out):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", LIB + name + ".mp4", "-t", str(dur), "-an",
                        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", LIB + out], check=True)
    return out

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

def P(t, s="", line=0, at=0.4, color="red"): return {"kind": "punch", "text": t, "sub": s, "line": line, "at": at, "color": color, "hold": 2.6}
def steps(title, rows, line=0, at=0.3): return {"kind": "steps", "title": title, "rows": rows, "on": None, "line": line, "at": at}
def tl(events, on=None, line=0, at=0.3): return {"kind": "timeline", "events": events, "on": on, "line": line, "at": at}
def quote(rows, by, line=0, at=0.2): return {"kind": "quote", "rows": rows, "by": by, "line": line, "at": at}
def lower(t, sub, line=0, at=0.15): return {"kind": "lower", "text": t, "sub": sub, "line": line, "at": at}

# 원음 구간(STT로 확정) — 확정 전엔 아래 기본값
SOTS = json.load(open(os.path.join(os.path.dirname(__file__), 'L261204-rate_sots.json'))) if os.path.exists(os.path.join(os.path.dirname(__file__), 'L261204-rate_sots.json')) else {}
def sot_cfg(key, start, dur, at=None):
    c = SOTS.get(key, {}); return c.get('start', start), c.get('dur', dur), c.get('at', at), c.get('lines')


# ── 코드 그래픽: 장면 말 길이에 맞춰 secs를 정하고 cfg를 쓴다(렌더는 fx_render로) ──
GL = HJ + '/scripts/youtube/long/globe/cfg_L261204r/'
os.makedirs(GL, exist_ok=True)
def FX(name, mode, cfg, lines, src="", note=""):
    sec = sum(len(l.replace(' ', '')) for l in lines) / 6.1 + 0.6 * len(lines) + 1.2
    json.dump({"page": "fx_bw.html", "mode": mode, "secs": round(sec + 1.5), "cfg": cfg}, open(GL + name + '.json', 'w'), ensure_ascii=False, indent=1)
    clip = f"globe_L261204r_fx_{name}.mp4"
    if not os.path.exists(LIB + clip): PENDING.add(clip)
    return {"v": {"type": "media", "full": True, "wash": "none", "cuts": [{"lib": clip}], "wash_amt": 0.85, "cine": True, "doc_cine": True},
            "sketch_add": [], "asof": False, "src": src, "sketch": [], "lines": lines, "note": note}

def SG(cuts, lines, sketch=None, src="", note="", **kw):   # 공용·생성 사진이 아직 안 왔으면 PENDING에만 올린다
    return S(cuts, lines, sketch, src, note, **kw)

R = "il_R1204_"
sc = []
# ───────── 훅: 형제에게 이자를 받지 말라 ─────────
sc.append(S([R + "stone_tablet"],
    ["“네가 만일 나의 백성 중 가난한 자에게 돈을 꾸이면, 변리를 받지 말 것이며.”",
     "3,000년 전 성경에 적힌 문장입니다. 변리, 바로 이자를 말합니다."],
    [quote(["가난한 자에게 돈을 꾸이면", "변리를 받지 말 것이며"], "출애굽기 22장 25절 · 개역한글", line=0, at=0.1)],
    "출애굽기 22:25(개역한글)", "[훅] 성경 구절 — 비장하게"))
sc.append(S([R + "church_burial"],
    ["800년 전 유럽에선 이자를 받은 사람은 죽어서도 교회 묘지에 묻힐 수 없었습니다. 이자는 그만큼 무서운 죄였죠."],
    [], "제3차 라테라노 공의회 1179년 제25조", "[훅] 묻히지 못한 사람들"))
sc.append(S([R + "trading_screens"],
    ["그런데 지금은 어떨까요. 그 죄였던 이자가 집값도, 주식도, 금값도, 심지어 AI 회사의 몸값까지 정합니다.",
     "죄였던 이자는 어떻게 세상의 왕이 됐을까요? 4,000년 금리의 역사를, 아주 쉽게 처음부터 따라가 보겠습니다."],
    [], "", "[훅] 약속"))
sc.append({"v": {"type": "media", "full": True, "wash": "none", "cuts": [{"lib": "il_L261116p_wallst_red.png"}], "wash_amt": 0.85, "cine": True, "ident": True},
           "lines": ["현명한 투자를 위한 경제 채널, 밸류노트 지금 시작합니다."], "sketch_add": [], "asof": False, "src": "", "sketch": [], "dur": 6.0, "note": "[로고 인트로] 시그니처"})

sc.append(S([R + "friend_loan"],
    ["시작하기 전에 금리부터 아주 쉽게 정리하고 갈게요. 친구에게 10만 원을 빌리고 1년 뒤에 11만 원을 갚기로 했다면, 더 갚는 1만 원이 이자, 10%가 금리입니다."],
    [], "", "[개념] 금리란"))
sc.append(FX("whatrate", "chain", {"kicker": "금리란?", "title": "돈을 빌리는 값", "nodes": [
        {"k": "10만 원", "sub": "빌린 돈"}, {"k": "1년", "sub": "쓰는 동안"}, {"k": "11만 원", "sub": "갚는 돈"}, {"k": "10%", "sub": "금리 = 돈의 렌트비"}], "step": 1.3},
    ["그러니까 금리는 돈을 빌려 쓰는 값, 돈의 렌트비인 셈이죠. 이 렌트비가 어떻게 세상을 움직이게 됐는지, 4,000년 전으로 가 보겠습니다."],
    "", "[개념] 돈의 렌트비(코드)"))

# ───────── 기: 이자는 죄였다 ─────────
sc.append(CH(S(["commons_hammurabi_stele_1"],
    ["이야기는 4,000년 전 바빌론에서 시작합니다. 함무라비 왕이 돌기둥에 새긴 법전에는, 놀랍게도 이자 규칙이 있었습니다."],
    [], "함무라비 법전(기원전 1750년 무렵) · 루브르 박물관 소장 · 위키미디어 공용", "[기] 함무라비"), "이자는 죄였다"))
sc.append(FX("caps", "vs2", {"kicker": "4,000년 전 이자 상한", "title": "함무라비 법전", "items": [
        {"k": "곡식을 빌리면", "big": "33", "unit": "%까지", "sub": "1년에 3분의 1"},
        {"k": "은을 빌리면", "big": "20", "unit": "%까지", "sub": "1년에 5분의 1", "hi": True}],
        "foot": "자료: 함무라비 법전 제88조 · 고대 메소포타미아 대출 문서"},
    ["곡식을 빌리면 이자는 1년에 3분의 1까지, 은을 빌리면 5분의 1까지만. 이걸 넘겨 받으면, 빌려준 돈을 통째로 잃었습니다."],
    "함무라비 법전 제88조", "[기] 이자 상한(코드)"))
sc.append(S([R + "babylon_market"],
    ["사람들은 이미 알고 있었던 겁니다. 이자는 없앨 수 없다. 대신 묶어 둬야 한다."],
    [], "", "[기] 묶어 둔 이자"))
sc.append(S([R + "moneylender_candle"],
    ["그리고 처음에 본 성경 문장에는 반전이 하나 숨어 있습니다. 형제에게는 이자를 받지 말라. 그런데 다른 곳에는, 이방인에게는 받아도 된다고 적혀 있죠.",
     "이 한 줄 때문에, 1,000년 넘게 유럽에서는 돈놀이를 누가 하느냐가 갈렸습니다."],
    [P("형제는 안 되고, 이방인은 된다", s="신명기 23장 20절", line=1, at=0.1)], "신명기 23:20", "[기] 성경의 반전"))
sc.append(S(["commons_dore_inferno_3"],
    ["중세 교회는 이자를 '시간을 파는 죄'라고 불렀습니다. 시간은 신의 것인데, 사람이 시간에 값을 매겼다는 거죠.",
     "단테의 『신곡』에서 고리대금업자들은 지옥의 불비가 쏟아지는 모래밭에 앉아, 목에 건 돈주머니만 내려다봅니다."],
    [], "귀스타브 도레 『신곡』 지옥편 삽화 · 탐욕의 죄(1861, 저작권 소멸) · 위키미디어 공용", "[기] 단테 지옥"))
sc.append(S([R + "venice_court", "commons_shylock_painting_1"],
    ["셰익스피어의 『베니스의 상인』에는, 돈을 못 갚으면 살 1파운드를 떼어 가겠다는 고리대금업자 샤일록이 나옵니다.",
     "그만큼 사람들은 이자 받는 사람을 미워했습니다."],
    [], "셰익스피어 『베니스의 상인』(1596년 무렵)", "[기] 샤일록", v={"cut_by_line": True}))
sc.append(S([R + "islamic_bank"],
    ["이 생각은 지금도 살아 있습니다. 이슬람 은행은 지금도 이자를 받지 않습니다. 대신 은행이 집을 같이 사서, 이자 대신 임대료나 이익을 나누는 방식을 쓰죠."],
    [], "이슬람 금융(리바 금지)", "[기] 지금도 이자가 없는 은행"))
sc.append(S(["commons_medici_palazzo_1"],
    ["그런데 이렇게 미움받던 이자를, 신의 눈을 피해 당당히 받아 낸 가문이 있었습니다."],
    [], "", "[리후킹] 신의 눈을 피한 가문"))

# ───────── 승: 신의 눈을 피한 사람들 ─────────
sc.append(CH(S([R + "florence_bench", "commons_reymerswaele_changer_1"],
    ["15세기 이탈리아 피렌체의 메디치 가문입니다. 메디치는 이자라는 말을 쓰지 않았습니다. 대신 환전 수수료를 받았죠.",
     "피렌체에서 금화를 빌려주고, 몇 달 뒤 런던에서 다른 나라 돈으로 돌려받습니다. 그 사이 환율 차이가 사실상 이자였던 겁니다."],
    [], "메디치 은행 환어음 거래(15세기)", "[승] 메디치의 비법", v={"cut_by_line": True}), "신의 눈을 피한 사람들"))
sc.append(FX("trick", "chain", {"kicker": "메디치의 비법", "title": "이름만 바꾼 이자", "nodes": [
        {"k": "피렌체", "sub": "금화를 빌려준다"}, {"k": "몇 달 뒤 런던", "sub": "다른 나라 돈으로 받는다"}, {"k": "환율 차이", "sub": "사실상 이자"}], "step": 1.6},
    ["이름만 바꿨을 뿐, 하는 일은 똑같았습니다. 교회도 환전은 정당한 장사라고 보고 막지 않았죠."],
    "", "[승] 환어음 구조(코드)"))
sc.append(S(["commons_cosimo_medici_1", R + "renaissance_chapel"],
    ["메디치 가문은 이렇게 유럽 최고의 부자가 됐고, 교황까지 배출합니다.",
     "재밌는 건 그다음입니다. 죄를 씻으려 했다는 이야기도 있죠. 메디치는 교회와 예술가들에게 엄청난 돈을 썼고, 그 돈으로 피어난 게 르네상스입니다. 어린 미켈란젤로도 메디치 집안에서 자랐습니다."],
    [], "폰토르모 「코시모 데 메디치」(저작권 소멸) · 위키미디어 공용", "[승] 르네상스", v={"cut_by_line": True}))
sc.append(S([R + "broken_bench"],
    ["은행을 뜻하는 영어 뱅크도 여기서 나왔습니다. 환전상이 앉던 긴 의자, 이탈리아 말로 방코입니다.",
     "장사가 망하면 그 의자를 부쉈는데, 부서진 의자, 방카 로타가 파산을 뜻하는 영어 뱅크럽트가 됐습니다."],
    [P("방코 → 뱅크", s="부서진 의자 방카 로타 → 뱅크럽트(파산)", line=1, at=0.1)], "", "[승] 어원"))
sc.append(S([R + "london_1694", "commons_boe_building_1"],
    ["그리고 1694년 영국. 프랑스와 전쟁 중이던 왕에게 돈이 급했습니다. 상인들이 돈을 모아 왕에게 120만 파운드를 빌려주고, 이자를 받기로 합니다.",
     "이렇게 생긴 게 영란은행, 영국의 중앙은행입니다. 죄였던 이자가, 나라를 움직이는 숫자가 된 순간이죠."],
    [], "영란은행 설립(1694)", "[승] 영란은행", v={"cut_by_line": True}))
sc.append(S(["commons_eccles_building_1"],
    ["그리고 300년 뒤, 이 숫자는 무기가 됩니다."],
    [], "", "[리후킹] 무기"))

# ───────── 전: 금리가 무기가 되다 ─────────
sc.append(CH(S([G("commons_volcker_1") if os.path.exists(LIB + "commons_volcker_1.jpg") else "commons_eccles_2"],
    ["1979년 미국, 물가가 1년에 10% 넘게 뛰던 때입니다. 마트 물건값이 해마다 10%씩 오른다고 생각해 보세요.",
     "이때 키가 2미터 넘는 사람이 미국 중앙은행, 연준의 의장이 됩니다. 폴 볼커입니다. 훗날 그는 그때를 이렇게 기억합니다."],
    [lower("폴 볼커", "미국 연방준비제도 의장 · 1979~1987", line=1, at=0.3)], "연준 역사(federalreservehistory.org)", "[전] 볼커 등장"), "금리가 무기가 되다"))
if 'volcker' in SOTS:
    st, du, at, ln = sot_cfg('volcker', 0.0, 20.0)
    sc.append(SOT(SOTS['volcker']['clip'], st, du, ln, "폴 볼커", "전 연준 의장", SOTS['volcker'].get('src', ''), "[전] 원음 볼커", at))
sc.append(FX("volcker20", "vs2", {"kicker": "볼커 쇼크", "title": "금리를 20%까지", "items": [
        {"k": "1979년 미국 물가", "big": "10", "unit": "%+", "sub": "해마다 물건값이"},
        {"k": "1981년 미국 기준금리", "big": "20", "unit": "%", "sub": "돈 빌리는 값을\n이만큼 비싸게", "hi": True}],
        "foot": "자료: 미국 연방준비제도 · 노동통계국"},
    ["볼커는 금리를 무려 20%까지 올렸습니다. 돈 빌리는 값을 엄청 비싸게 만들어서, 사람들이 돈을 덜 쓰게 하고 물가를 잡겠다는 거죠."],
    "", "[전] 금리 20%(코드)"))
sc.append(S([R + "tractors_dc"],
    ["미국이 발칵 뒤집혔습니다. 빚을 진 농부들은 트랙터를 몰고 워싱턴으로 가, 연준 건물을 막아섰습니다."],
    [], "연준 역사 · 미국 돈 박물관(MOAF)", "[전] 트랙터"))
sc.append(S([R + "lumber_mail", R + "keys_coffin"],
    ["집이 안 팔린 건설업자들은 쓸모없어진 각목에 우표를 붙여 연준으로 보냈고,",
     "차를 못 판 자동차 딜러들은 팔지 못한 차의 열쇠를 관에 담아 보냈습니다."],
    [], "세인트루이스 연준 FRASER(각목 원본 보관) · 연준 역사", "[전] 각목과 관", v={"cut_by_line": True}))
sc.append(S(["il_L261113g2_volcker_pit"],
    ["그래도 볼커는 물러서지 않았습니다. 결국 물가는 잡혔고, 미국은 그 뒤 20년 가까이 호황을 누립니다. 금리 하나로 나라 전체의 체온을 바꾼 겁니다."],
    [], "", "[전] 볼커의 승리"))
sc.append(S([R + "lehman_2008"],
    ["그리고 2008년 금융위기. 이번엔 반대로 미국이 금리를 0%까지 내립니다. 돈을 거의 공짜로 빌릴 수 있는 시대가, 그 뒤로 10년 넘게 이어졌죠."],
    [], "연준 2008-12-16 기준금리 0~0.25%", "[전] 2008 제로 금리"))
sc.append(S([R + "copenhagen_home"],
    ["그런데 40년 뒤, 정반대 세상이 옵니다. 2019년 덴마크의 한 은행이 이런 주택 대출을 내놓습니다. 금리, 마이너스 0.5%.",
     "빌린 돈보다 덜 갚는 대출. 은행이 돈 좀 빌려 가 달라고 하는, 공짜 돈의 시대였습니다."],
    [P("금리 -0.5%", s="2019년 덴마크 위스케 은행 10년 주택 대출", line=0, at=0.75)], "CNBC 2019-08-12", "[전] 마이너스 금리"))
sc.append(FX("bill2022", "vs2", {"kicker": "공짜 돈의 청구서", "title": "2022년", "items": [
        {"k": "2021년 말 미국 기준금리", "big": "0", "unit": "%대", "sub": "공짜 돈의 시대"},
        {"k": "2022년 말", "big": "4", "unit": "%대", "sub": "1년 만에\n나스닥 -33%", "hi": True}],
        "foot": "자료: 미국 연방준비제도 · 나스닥"},
    ["그리고 2022년, 청구서가 날아옵니다. 물가가 다시 뛰자 미국은 0%대였던 금리를 1년 만에 4%대로 올렸고, 기술주가 모인 나스닥은 한 해에 33% 빠졌습니다."],
    "", "[전] 2022 청구서(코드)"))
sc.append(S(["il_L261113g2_fed_winter"],
    ["그런데 이상하지 않으세요? 볼커 때는 금리가 20%였는데, 왜 지금은 4%만 돼도 세상이 이렇게 흔들릴까요?"],
    [], "", "[리후킹] 왜 4%에도"))

# ───────── 파동: 금리의 파동이 커졌다 ─────────
sc.append(CH(S([R + "stone_pond", R + "stone_ocean"],
    ["돌 하나를 떠올려 보세요. 작은 연못에 던지면 물결이 조금 일고 끝납니다.",
     "그런데 같은 돌을 바다에 던지면 어떨까요. 금리는 돌이고, 빚은 물입니다."],
    [], "", "[파동] 비유", v={"cut_by_line": True}), "금리의 파동"))
sc.append(FX("ripple", "ripple", {"kicker": "같은 돌, 다른 물", "title": "미국 나라 빚", "ponds": [
        {"k": "1980년", "v": "약 1조 달러", "sub": "작은 연못", "r": 0.12},
        {"k": "지금", "v": "38조 달러+", "sub": "큰 바다", "r": 0.92}], "drop": 2.2,
        "foot": "자료: 미국 재무부"},
    ["1980년 미국 나라 빚은 1조 달러 정도였습니다. 지금은 38조 달러가 넘습니다. 같은 금리라도 흔드는 물의 양이, 서른 배 넘게 커진 거죠."],
    "미국 재무부(1980 회계연도 말 9,077억 달러 · 2026년 38조 달러+)", "[파동] 연못과 바다(코드)"))
sc.append(FX("world", "vs2", {"kicker": "세계의 바다", "title": "금리 1%포인트의 무게", "items": [
        {"k": "세계 빚", "big": "365", "unit": "조 달러", "sub": "2026년 상반기"},
        {"k": "금리가 1%포인트 오르면", "big": "3.65", "unit": "조 달러", "sub": "1년 이자가 더 붙는다\n(단순 계산)", "hi": True}],
        "foot": "자료: 국제금융협회(IIF) 글로벌 부채 모니터 2026-09"},
    ["세계 전체 빚은 365조 달러입니다. 금리가 딱 1%포인트만 올라도, 단순하게 계산해서 1년 이자만 3조 6,500억 달러가 더 붙습니다."],
    "IIF 2026-09-23", "[파동] 세계 빚(코드)"))
sc.append(FX("home", "vs2", {"kicker": "우리 집으로 가져오면", "title": "3억 원 대출이라면", "items": [
        {"k": "금리가 1%포인트 오르면", "big": "300", "unit": "만 원", "sub": "1년 이자가 더"},
        {"k": "한 달로 나누면", "big": "25", "unit": "만 원", "sub": "매달 더 나가는 돈", "hi": True}],
        "foot": "계산: 3억 원 × 1% = 1년 300만 원"},
    ["우리 집으로 가져와 볼까요. 3억 원을 빌린 집이라면, 금리가 1%포인트만 올라도 1년 이자가 300만 원 늘어납니다. 한 달에 25만 원이 더 나가는 거죠."],
    "", "[파동] 우리 집(코드)"))
sc.append(FX("usint", "vs2", {"kicker": "미국 정부가 내는 이자", "title": "국방비보다 큰 이자", "items": [
        {"k": "2019년", "big": "3,750", "unit": "억 달러", "sub": "1년 순이자"},
        {"k": "2026년", "big": "1조 520", "unit": "억 달러", "sub": "하루 약 29억 달러\n국방비보다 많다", "hi": True}],
        "foot": "자료: 미국 재무부 · 포춘 2026-10-17"},
    ["미국 정부가 1년에 내는 이자는 2019년 3,750억 달러에서, 2026년 1조 520억 달러가 됐습니다. 하루에 29억 달러. 나라를 지키는 국방비보다 이자가 더 큽니다."],
    "미국 재무부 2026 회계연도", "[파동] 미국 이자(코드)"))
sc.append(FX("aivsint", "vs2", {"kicker": "같은 돈을 두고", "title": "AI와 이자", "items": [
        {"k": "선진국 정부가 1년간 낸 국채 이자", "big": "3.3", "unit": "조 달러", "hi": True},
        {"k": "세계가 1년간 AI에 쓴 돈", "big": "2.6", "unit": "조 달러"}],
        "foot": "자료: 국제금융협회(IIF) 2026-09"},
    ["더 놀라운 건 이겁니다. 선진국 정부들이 1년 동안 낸 국채 이자가 3조 3,000억 달러. 세계가 AI에 쓴 2조 6,000억 달러보다 많습니다.",
     "AI와 이자가, 사실상 같은 돈을 두고 다투고 있는 셈이죠."],
    "IIF 2026-09-23", "[파동] AI vs 이자(코드)"))
sc.append(FX("chain", "chain", {"kicker": "파도가 오는 순서", "title": "몇 초 만에 번지는 파동", "nodes": [
        {"k": "금리 발표", "sub": "중앙은행"}, {"k": "국채 금리", "sub": "시장이 매기는 금리"}, {"k": "달러", "sub": "환율"}, {"k": "성장주", "sub": "AI·반도체"}], "step": 1.5},
    ["파도의 속도도 달라졌습니다. 예전엔 금리가 바뀌면 몇 달에 걸쳐 퍼졌지만, 지금은 발표 몇 초 만에 국채 금리가 움직이고, 달러가 움직이고, 성장주가 출렁입니다."],
    "", "[파동] 파도 순서(코드)"))
sc.append(S(["il_L261113g_fed_dusk"],
    ["정리하면 이렇습니다. 금리 숫자 자체는 볼커 때보다 낮지만, 그 금리가 흔드는 물이 수십 배가 됐습니다. 그래서 작은 변화도, 이제는 큰 파도가 됩니다."],
    [], "", "[파동] 정리"))

# ───────── 결: 금리를 읽는 법 ─────────
sc.append(CH(S(["commons_crash1929_1"],
    ["1929년 10월, 뉴욕 월가 앞에 사람들이 몰려들었습니다. 주가가 하루에 10% 넘게 무너진 날이었죠."],
    [], "1929년 대폭락 · 위키미디어 공용", "[결] 1929"), "금리를 읽는 법"))
sc.append(FX("bubbles", "vs2", {"kicker": "버블을 끝낸 것", "title": "늘 금리였다", "items": [
        {"k": "1929년", "big": "대공황", "unit": "", "sub": "금리를 올린 뒤\n대폭락"},
        {"k": "2000년", "big": "닷컴", "unit": "", "sub": "6.5%까지 올린 뒤\n붕괴"},
        {"k": "2022년", "big": "기술주", "unit": "", "sub": "0%대 → 4%대\n나스닥 -33%", "hi": True}],
        "foot": "자료: 미국 연방준비제도 역사"},
    ["역사를 보면 버블을 끝낸 건 늘 금리였습니다. 1929년 대공황 직전에도, 2000년 닷컴 버블 직전에도, 2022년에도, 미국은 금리를 올리고 있었습니다."],
    "연준 역사 · 1929년 8월 재할인율 6% · 2000년 5월 6.5%", "[결] 버블과 금리(코드)"))
sc.append(FX("discount", "vs2", {"kicker": "10년 뒤 받을 1억 원", "title": "지금 값은 얼마?", "items": [
        {"k": "금리 1%일 때", "big": "9,053", "unit": "만 원", "sub": "지금 가치"},
        {"k": "금리 5%일 때", "big": "6,139", "unit": "만 원", "sub": "같은 1억인데\n3,000만 원 가까이 줄어든다", "hi": True}],
        "foot": "계산: 1억 원 ÷ (1+금리)^10"},
    ["그래서 AI 같은 큰 꿈일수록 금리에 약합니다. 10년 뒤에 받을 1억 원을 생각해 보세요. 금리가 1%면 지금 가치로 9,053만 원이지만, 금리가 5%면 6,139만 원으로 줄어듭니다.",
     "돈을 벌 날이 먼 미래일수록, 금리가 오를 때 지금 몸값이 크게 깎이는 거죠. 게다가 AI 데이터센터는 대부분 빌린 돈으로 짓습니다."],
    "", "[결] 할인율(코드)"))
sc.append(FX("read3", "vs2", {"kicker": "금리 뉴스를 볼 때", "title": "세 가지만 기억하세요", "items": [
        {"k": "하나", "big": "10년", "unit": "국채 금리", "sub": "기준금리보다\n내 주식에 더 가깝다"},
        {"k": "둘", "big": "예상", "unit": "과의 차이", "sub": "다 아는 결정은\n이미 가격에 있다"},
        {"k": "셋", "big": "순서", "unit": "국채 → 달러 → 주식", "sub": "파도가 오는 길", "hi": True}]},
    ["그러니 금리 뉴스를 볼 때는 세 가지만 기억하세요.",
     "첫째, 중앙은행이 정하는 기준금리보다, 시장이 매기는 10년 국채 금리가 내 주식에 더 가깝습니다. 둘째, 결정 그 자체보다 예상과 얼마나 달랐는지가 시장을 움직입니다. 셋째, 파도는 국채, 달러, 주식 순서로 옵니다."],
    "", "[결] 읽는 법(코드)"))
sc.append(S([R + "closing_dawn"],
    ["3,000년 전엔 지옥에 가는 죄였던 숫자가, 이제 365조 달러의 바다를 흔듭니다.",
     "다음 파도가 올 때, 여러분은 메디치가 될까요, 샤일록이 될까요?"],
    [], "", "[마무리] 열린 질문"))
sc.append(S(["il_L261123s_fed_dawn"],
    ["지금 금리가 어디 있는지, 다음 결정은 언제인지는 밸류노트 금리 페이지에서 매일 확인하실 수 있습니다."],
    [], "", "[마무리] 금리 페이지 안내"))
sc.append(S(["il_L261104g_fed_winter"],
    ["여러분의 구독, 좋아요, 댓글은 영상 제작에 큰 힘이 됩니다."],
    [], "", "[마무리] 구독"))
sc.append({"v": {"type": "end", "sub": "", "btn_at": ["0:거시적", "0:거시적", "0:거시적"], "note": {"text": ""}, "dark_end": True, "end_v2": True,
                 "slogan": ["시장의 흐름 뒤", "숨은 이야기를 읽는 채널", "거시적 관점으로 시장을 이해하면, 투자가 달라집니다"]},
           "lines": ["거시적 관점으로 시장을 이해하면, 투자가 달라집니다. 감사합니다. 밸류노트였습니다."],
           "sketch_add": [], "asof": False, "src": "", "note": "[북엔드] 끝 화면"})

ph = [c["lib"] for x in sc for c in x["v"].get("cuts", []) if c["lib"].startswith("il_")]
dups = sorted({l for l in ph if ph.count(l) > 1})

base = json.load(open(HJ + '/scripts/youtube/long/specs/L261124-gold-3.json'))
# ── 겹침 관문(2026-11-26): 한 장면 안에서 강조 문구·이름표·인용·단계표가 동시에 뜨지 않게 ──
for _i, _s in enumerate(sc):
    _k = [(b.get("kind"), b.get("line", 0), b.get("at", 0)) for b in (_s.get("sketch") or []) if b.get("kind") in ("punch", "lower", "quote", "steps", "tl", "stamp")]
    if any(k in ("steps", "tl") for k, _, _ in _k) and len(_k) > 1:
        raise SystemExit(f"겹침: 장면 {_i} 단계표·연표는 끝까지 남으니 다른 강조와 같이 못 둠 {_k}")
    _lines = [l for _, l, _ in _k]
    if len(_lines) != len(set(_lines)):
        raise SystemExit(f"겹침: 장면 {_i} 같은 줄에 강조 2개 {_k}")
    for (k1, l1, a1), (k2, l2, a2) in zip(sorted(_k, key=lambda x: x[1]), sorted(_k, key=lambda x: x[1])[1:]):
        if l2 == l1 + 1 and a1 > 0.5:
            raise SystemExit(f"겹침: 장면 {_i} {k1}(줄{l1}, {a1})가 다음 줄 {k2}와 겹칠 수 있음")

# 2026-11-26 대표 "2분경 그래프가 날아갔다": 깨진 영상 파일(렌더 중단으로 반쯤 쓰인 mp4)이 그대로 들어가 화면이 비었음 → 쓰는 영상은 전부 열어 보고 길이를 확인한다
import re as _re, subprocess as _sp
for _m in sorted(set(_re.findall(r'"([^"/]+\.mp4)"', json.dumps(sc, ensure_ascii=False)))):
    _p = LIB + _m
    if _m in PENDING: continue
    _d = _sp.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', _p], capture_output=True, text=True).stdout.strip() if os.path.exists(_p) else ''
    try: _ok = float(_d) > 0.5
    except ValueError: _ok = False
    if not _ok: raise SystemExit(f"영상 파일이 없거나 깨짐: {_m}")
    if _sp.run(['git', '-C', HJ, 'ls-files', '--error-unmatch', _p], capture_output=True).returncode != 0:   # 2026-11-26: 만든 잘라 쓴 영상을 커밋 안 해 렌더 관문에서 막힘 → 커밋할 목록을 알려 준다
        print(f"⚠ 커밋 안 된 화면 파일(같이 커밋할 것): {_m}")
spec = {k: base[k] for k in ['format', 'world', 'notebook', 'overlay', 'look', 'roadmap', 'hook', 'music', 'design', 'synthetic_media'] if k in base}
TITLE = "이자는 원래 죄였다 | 금리는 어떻게 세상을 지배하게 됐나"
spec.update({
 "id": "L261204-rate", "company": "RATE", "no_data": True, "series": "", "plan": "P261204-rate",
 "scheduled_at": "2026-12-04T19:30:00+09:00", "manual": True,
 "opening": "성경 구절(형제에게 이자를 받지 말라) → 묻히지 못한 고리대금업자 → 지금은 이자가 모든 가격을 정한다 → 어떻게 왕이 됐나",
 "hook_type": "고전 문장 + 반전(죄 → 왕)",
 "endscreen_target": "L261126-son", "endscreen_also": "L261123-soxl-3",
 "title": TITLE,
 "doc_title": "금리의 모든 것",
 "title_en": "Interest used to be a sin. How did interest rates come to rule the world?",
 "description_head": "3,000년 전 성경은 형제에게 이자를 받지 말라고 했고, 800년 전 교회는 이자를 받은 사람을 묘지에 묻어 주지도 않았습니다. 그 죄였던 이자가 지금은 집값·주식·금값, AI 회사의 몸값까지 정합니다.\n함무라비 법전의 이자 상한, 메디치 가문이 이자를 받은 비법, 은행과 파산이라는 말의 뿌리, 영란은행, 볼커의 금리 20%와 각목 우편, 마이너스 금리 대출, 그리고 금리의 파도가 왜 예전보다 훨씬 커졌는지까지 쉽게 풀었습니다.\n\n📈 지금 금리와 다음 결정일 👉 valuenote.co.kr/rate",
 "description_en": "Interest was once a sin. From Hammurabi's interest caps and the Medici's bills of exchange to the Bank of England, the Volcker shock and negative-rate mortgages, we explain how interest rates came to rule the world and why their waves are bigger than ever. Some images are AI-generated reenactments and are labeled. Not investment advice.",
 "pinned_comment": "📈 지금 금리와 다음 결정일(매일 갱신) 👉 valuenote.co.kr/rate\n\n다음 파도가 올 때, 여러분은 메디치일까요 샤일록일까요? 생각을 남겨 주세요.\n\n※ 옛 그림·기록 사진은 저작권이 끝났거나 공개 이용이 허락된 자료(위키미디어 공용)이고, 일부 사진은 재연 이미지(AI 생성)입니다. 숫자 기준 2026년. 매수·매도 권유가 아닙니다.",
 "hook_promises": ["이자가 죄였던 시절", "죄였던 이자가 왕이 된 과정", "금리의 파도가 커진 이유와 읽는 법"],
 "viewer_question": "금리는 왜 이렇게 세상을 흔드나",
 "tags": ["금리", "이자", "기준금리", "금리 역사", "메디치", "볼커", "연준", "국채 금리", "마이너스 금리", "경제 공부", "금리 쉽게"],
 "search_keywords": ["금리란", "금리 역사", "금리 오르면", "이자 역사", "볼커"],
 "sources": ["출애굽기 22:25·신명기 23:20(개역한글)", "제3차 라테라노 공의회(1179) 제25조", "함무라비 법전 제88조", "연준 역사(federalreservehistory.org)", "세인트루이스 연준 FRASER", "CNBC 2019-08-12", "IIF 글로벌 부채 모니터 2026-09-23", "미국 재무부·포춘 2026-10-17", "위키미디어 공용"],
 "format_note": "2026-11-26 대표 — 청소년도 재밌고 쉽게, 시의성 없이 오래 볼 금리 입문, 썰 중심·숫자는 파동 장에서만, 열린 결말, 국내 방송사·영화 장면 금지",
 "orig_mode": "sot_test", "orig_mode_note": "원음+한국어 자막(더빙 없음).",
 "voice_speed": 1.03,
 "photo_lift": 1.25,
 "thumb_fixed": "2026-11-26 — 썸네일은 따로 만든다",
 "thumb": {"photo": "il_R1204_stone_tablet.png", "focus_x": 0.6, "l1": "이자는 원래", "l2": "죄였다", "pos": "left"},
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
