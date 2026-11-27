import json, os, re
# 금리의 모든 것 — 이자는 원래 죄였다 (2026-11-26 대표) — 대본: 프로젝트 문서 claude/youtube/drafts/L261204-rate-script.md v3
# 기준: 청소년도 '재밌고 이해하기 쉬웠다'고 느끼는 교육 영상, 썰 중심·숫자는 파동 장에서만, 열린 결말
# 11/26 15:23 대표: 마지막에 누가 정하나·물가와 일자리·12월 9일 결정(시장 예상)·금값/비트코인/주식 출렁 → 밸류노트로 마무리. 화면 글자는 핵심 한마디만(중복 금지)
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
FXDUR = json.load(open(os.path.join(os.path.dirname(__file__), 'L261204-rate_fxdur.json')))   # 지난 렌더에서 잰 장면 길이(말 길이) — 테두리 옮기는 시각 계산용
_TLP = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'social', 'youtube', 'L261204-rate', 'timeline.json')
TL = {tuple(x_[2] for x_ in e["lines"]): e["lines"] for e in (json.load(open(_TLP)) if os.path.exists(_TLP) else [])}   # 11/27 지난 렌더의 실제 말 시각(줄 시작·길이)
def _hl(name, lines, hl):
    """hl=[(말 조각, 칸번호), ...] → [[초, 칸번호], ...] — 그 조각을 말하기 시작하는 시각(2026-11-27 대표: 말할 때마다 빨간 테두리가 그 칸으로)"""
    ch = [len(l.replace(' ', '')) for l in lines]
    m = FXDUR.get(name)
    speak = (m["dur"] - .35 - .2 * len(lines)) if (m and m["lines"] == lines) else sum(ch) / 6.1   # 같은 말이면 실제 길이, 아니면 추정
    rate = sum(ch) / max(speak, 1)
    out = []
    if tuple(lines) in TL:   # 실제 줄 시작·길이가 있으면 그걸로: 줄 시작 + 줄 길이 × (앞 글자 / 줄 글자)
        L_ = TL[tuple(lines)]
        for frag, idx in hl:
            li = next(i for i, l in enumerate(lines) if frag in l); a_, d_, tx = L_[li]
            nb = len(tx[:tx.index(frag)].replace(' ', '')); nt = max(1, len(tx.replace(' ', '')))
            out.append([round(a_ + d_ * nb / nt - .12, 2), idx])
        return out
    for frag, idx in hl:
        li = next(i for i, l in enumerate(lines) if frag in l)
        before = sum(ch[:li]) + len(lines[li][:lines[li].index(frag)].replace(' ', ''))
        out.append([round(before / rate + .2 * li - .15, 2), idx])
    return out

def _tl_lines(lines):
    L_ = TL.get(tuple(lines))
    if L_: return L_
    out = []; u = .25
    for l in lines: d_ = len(l.replace(" ", "")) / 6.1; out.append([u, d_, l]); u += d_ + .2
    return out
def _wt(L_, w):
    for a_, d_, tx in L_:
        if w in tx: return a_ + d_ * len(tx[:tx.index(w)].replace(" ", "")) / max(1, len(tx.replace(" ", "")))
    raise KeyError(w)
def PS(cuts, lines, punches, src="", note=""):
    """2026-11-27 대표 '같은 코드 효과가 연속 — 사진+텍스트로도': cuts=[(사진, 바뀌는 낱말|None)], punches=[(글, 작은 글, 나오는 낱말)] — 글은 자기 사진이 바뀔 때 사라진다"""
    L_ = _tl_lines(lines); end_ = L_[-1][0] + L_[-1][1] + .35
    cs = [dict({"lib": c[0]}, **({"word": c[1]} if c[1] else {}), **({"crop": list(c[2])} if len(c) > 2 else {})) for c in cuts]
    bt = [0.0] + [_wt(L_, c[1]) for c in cuts[1:]]
    sk = []
    for t, sub, w in punches:
        t0 = _wt(L_, w); j_ = max(i for i, b in enumerate(bt) if b <= t0 + .3)
        li_ = next(i for i, l in enumerate(L_) if w in l[2]); at_ = round((t0 - L_[li_][0]) / max(.1, L_[li_][1]), 2)
        sk.append({"kind": "punch", "text": t, "sub": sub, "line": li_, "at": at_, "color": "red", "hold": 2.6, "t0": round(t0, 2), "until": round(bt[j_ + 1] if j_ + 1 < len(bt) else end_, 2), "sync": False})
    sc_ = S([cuts[0][0]], lines, sk, src, note); sc_["v"]["cuts"] = cs; return sc_

def FX(name, mode, cfg, lines, src="", note="", hl=None, at=None):
    if hl: cfg = dict(cfg, hl=_hl(name, lines, hl))
    if at: cfg = dict(cfg, at=[t for t, _ in _hl(name, lines, at)])
    if cfg.get("rise_word"): cfg = dict(cfg, rise_at=_hl(name, lines, [(cfg["rise_word"], 0)])[0][0])   # 바닥이 오르는 순간 = 그 말
    if isinstance(cfg.get("t02"), str): cfg = dict(cfg, t02=_hl(name, lines, [(cfg["t02"], 0)])[0][0])   # 둘째 선이 그려지기 시작하는 말
    if cfg.get("bar_words"): cfg = dict(cfg, bar_at=[t for t, _ in _hl(name, lines, [(w, 0) for w in cfg["bar_words"]])])   # 사슬: 그 말을 할 때 그 칸이 켜진다
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
    "출애굽기 22:25(개역한글)", "[훅] 성경 구절 — 비장하게", pause_after={"0": 1.1}))   # 11/26 대표 "변리를 받지 말 것이며 하고 한 템포 쉬고"
sc.append(S([R + "church_burial"],
    ["800년 전 유럽에선 이자를 받은 사람은 죽어서도 교회 묘지에 묻힐 수 없었습니다. 이자는 그만큼 무서운 죄였죠."],
    [], "제3차 라테라노 공의회 1179년 제25조", "[훅] 묻히지 못한 사람들"))
sc.append(S([R + "trading_screens"],
    ["그런데 지금은 어떨까요. 그 죄였던 이자가 집값도, 주식도, 금값도, 심지어 AI 회사의 몸값까지 정합니다.",
     "죄였던 이자는 어떻게 세상의 왕이 됐을까요? 4,000년 금리의 역사를, 아주 쉽게 처음부터 따라가 보겠습니다."],
    [], "함무라비 법전(기원전 1750년 무렵)부터 2026년까지", "[훅] 약속"))
sc.append({"v": {"type": "media", "full": True, "wash": "none", "cuts": [{"lib": "il_L261116p_wallst_red.png"}], "wash_amt": 0.85, "cine": True, "ident": True},
           "lines": ["현명한 투자를 위한 경제 채널, 밸류노트 지금 시작합니다."], "sketch_add": [], "asof": False, "src": "", "sketch": [], "dur": 6.0, "note": "[로고 인트로] 시그니처"})

sc.append(S([R + "friend_loan"],
    ["시작하기 전에 금리부터 아주 쉽게 정리하고 갈게요. 친구에게 10만 원을 빌리고 1년 뒤에 11만 원을 갚기로 했다면, 더 갚는 1만 원이 이자, 10%가 금리입니다."],
    [], "계산 예시(10만 원을 1년 빌려 11만 원 상환 = 금리 10%)", "[개념] 금리란"))
sc.append(FX("whatrate", "chain", {"kicker": "금리란?", "title": "돈을 빌리는 값", "nodes": [
        {"k": "10만 원 빌림"}, {"k": "1년 뒤"}, {"k": "11만 원 갚음"}, {"k": "금리 10%"}], "step": 1.3},
    ["그러니까 금리는 돈을 빌려 쓰는 값, 돈의 렌트비인 셈이죠. 이 렌트비가 어떻게 세상을 움직이게 됐는지, 4,000년 전으로 가 보겠습니다."],
    "계산 예시 · 함무라비 법전(기원전 1750년 무렵)", "[개념] 돈의 렌트비(코드)"))

# ───────── 기: 이자는 죄였다 ─────────
sc.append(CH(S(["il_R1204b_hammurabi"],
    ["이야기는 4,000년 전 바빌론에서 시작합니다. 함무라비 왕이 돌기둥에 새긴 법전에는, 놀랍게도 이자 규칙이 있었습니다."],
    [], "함무라비 법전(기원전 1750년 무렵) · 루브르 박물관 소장", "[기] 함무라비"), "이자는 죄였다"))
sc.append(FX("caps", "vs2", {"hl_style": "fill", "kicker": "4,000년 전 이자 상한", "title": "함무라비 법전", "items": [
        {"k": "곡식", "big": "33%"},
        {"k": "은", "big": "20%", "hi": True}],
        "foot": "함무라비 법전 제88조"},
    ["곡식을 빌리면 이자는 1년에 3분의 1까지, 은을 빌리면 5분의 1까지만. 이보다 이자를 더 받으면, 빌려준 돈을 통째로 잃었습니다."],
    "함무라비 법전 제88조", "[기] 이자 상한(코드)", hl=[('곡식을', 0), ('은을 빌리면', 1)]))
sc.append(S([R + "babylon_market"],
    ["사람들은 이미 알고 있었던 겁니다. 이자는 없앨 수 없다. 대신 묶어 둬야 한다."],
    [], "", "[기] 묶어 둔 이자"))
sc.append(S([R + "moneylender_candle"],
    ["그리고 처음에 본 성경 문장에는 반전이 하나 숨어 있습니다. 형제에게는 이자를 받지 말라. 그런데 다른 곳에는, 이방인에게는 받아도 된다고 적혀 있죠.",
     "이 한 줄 때문에, 1,000년 넘게 유럽에서는 돈놀이를 누가 하느냐가 갈렸습니다."],
    [P("형제는 안 되고, 이방인은 된다", s="신명기 23장 20절", line=1, at=0.1)], "신명기 23:20", "[기] 성경의 반전"))
sc.append(S(["il_R1204b_dante_hell"],
    ["중세 교회는 이자를 '시간을 파는 죄'라고 불렀습니다. 시간은 신의 것인데, 사람이 시간에 값을 매겼다는 거죠.",
     "단테의 『신곡』에서 고리대금업자들은 지옥의 불비가 쏟아지는 모래밭에 앉아, 목에 건 돈주머니만 내려다봅니다."],
    [], "단테 『신곡』 지옥편 제17곡", "[기] 단테 지옥"))
sc.append(S([R + "venice_court", "il_R1204b_shylock"],
    ["셰익스피어의 『베니스의 상인』에는, 돈을 못 갚으면 살 1파운드를 떼어 가겠다는 고리대금업자 샤일록이 나옵니다.",
     "그만큼 사람들은 이자 받는 사람을 미워했습니다."],
    [], "셰익스피어 『베니스의 상인』(1596년 무렵)", "[기] 샤일록", v={"cut_by_line": True}))
sc.append(S([R + "islamic_bank"],
    ["이 생각은 지금도 살아 있습니다. 이슬람 은행은 지금도 이자를 받지 않습니다. 대신 은행이 집을 같이 사서, 이자 대신 임대료나 이익을 나누는 방식을 쓰죠."],
    [], "이슬람 금융(리바 금지)", "[기] 지금도 이자가 없는 은행"))
sc.append(S(["il_R1204b_medici_palazzo"],
    ["그런데 이렇게 미움받던 이자를, 신의 눈을 피해 당당히 받아 낸 가문이 있었습니다."],
    [], "", "[리후킹] 신의 눈을 피한 가문"))

# ───────── 승: 신의 눈을 피한 사람들 ─────────
sc.append(CH(S([R + "florence_bench", "il_R1204b_ledger_coins"],
    ["15세기 이탈리아 피렌체의 메디치 가문입니다. 메디치는 이자라는 말을 쓰지 않았습니다. 대신 환전 수수료를 받았죠.",
     "피렌체에서 금화를 빌려주고, 몇 달 뒤 런던에서 다른 나라 돈으로 돌려받습니다. 그 사이 환율 차이가 사실상 이자였던 겁니다."],
    [], "메디치 은행 환어음 거래(15세기)", "[승] 메디치의 비법", v={"cut_by_line": True}), "신의 눈을 피한 사람들"))
sc.append(FX("trick", "chain", {"kicker": "메디치의 비법", "title": "이름만 바꾼 이자", "nodes": [
        {"k": "피렌체에서 빌려줌"}, {"k": "런던에서 받음"}, {"k": "환율 차이 = 이자"}], "step": 1.6, "dx": 520},
    ["이름만 바꿨을 뿐, 하는 일은 똑같았습니다. 교회도 환전은 정당한 장사라고 보고 막지 않았죠."],
    "", "[승] 환어음 구조(코드)"))
sc.append(S(["il_R1204b_cosimo", R + "renaissance_chapel"],
    ["메디치 가문은 이렇게 유럽 최고의 부자가 됐고, 교황까지 배출합니다.",
     "재밌는 건 그다음입니다. 죄를 씻으려 했다는 이야기도 있죠. 메디치는 교회와 예술가들에게 엄청난 돈을 썼고, 그 돈으로 피어난 게 르네상스입니다. 어린 미켈란젤로도 메디치 집안에서 자랐습니다."],
    [], "메디치 가문(15세기)", "[승] 르네상스", v={"cut_by_line": True}))
sc.append(S([R + "broken_bench"],
    ["은행을 뜻하는 영어 뱅크도 여기서 나왔습니다. 환전상이 앉던 긴 의자, 이탈리아 말로 방코입니다.",
     "장사가 망하면 그 의자를 부쉈는데, 부서진 의자, 방카 로타가 파산을 뜻하는 영어 뱅크럽트가 됐습니다."],
    [P("방코 → 뱅크", s="부서진 의자 방카 로타 → 뱅크럽트(파산)", line=1, at=0.1)], "", "[승] 어원"))
sc.append(S([R + "london_1694", "il_R1204b_boe"],
    ["그리고 1694년 영국. 프랑스와 전쟁 중이던 왕에게 돈이 급했습니다. 상인들이 돈을 모아 왕에게 120만 파운드를 빌려주고, 이자를 받기로 합니다.",
     "이렇게 생긴 게 영란은행, 영국의 중앙은행입니다. 죄였던 이자가, 나라를 움직이는 숫자가 된 순간이죠."],
    [], "영란은행 설립(1694)", "[승] 영란은행", v={"cut_by_line": True}))
sc.append(S(["il_R1204b_eccles"],
    ["그리고 300년 뒤, 이 숫자는 무기가 됩니다."],
    [], "영란은행 설립 1694년 → 볼커 의장 취임 1979년", "[리후킹] 무기"))

# ───────── 전: 금리가 무기가 되다 ─────────
# 11/27 18:05 대표 "1979년 미국 얘기할 때 왜 볼커 사진 — 그 말에 맞는 사진 / '키가 2미터'에 사진과 '폴 볼커' 글씨, 다음 원음 영상까지 유지"
_VL = ["1979년 미국, 물가가 1년에 10% 넘게 뛰던 때입니다. 마트 물건값이 해마다 10%씩 오른다고 생각해 보세요.",
       "이때 키가 2미터 넘는 사람이 미국 중앙은행, 연준의 의장이 됩니다. 폴 볼커입니다. 훗날 그는 그때를 이렇게 기억합니다."]
_VLL = _tl_lines(_VL); _vt = _wt(_VLL, "이때 키가"); _vend = _VLL[-1][0] + _VLL[-1][1] + .35
_vs = S(["il_R1204c_s21_2"], _VL,
    [{"kind": "lower", "text": "폴 볼커", "sub": "미국 연방준비제도 의장 · 1979~1987", "line": 1, "at": 0.0, "t0": round(_vt + .1, 2), "until": round(_vend + 1.0, 2), "fade_out": .15}],
    "연준 역사(federalreservehistory.org) · 사진: 위키미디어 공용", "[전] 볼커 등장")
_vs["v"]["cuts"] = [{"lib": "il_R1204c_s21_2.png"}, {"lib": "il_R1204c_s21_1.png", "word": "마트 물건값"},
                    {"lib": "commons_volcker_1.jpg", "word": "이때 키가 2미터"}, {"lib": "commons_volcker_2.jpg", "word": "훗날 그는"}]
sc.append(CH(_vs, "금리가 무기가 되다"))
if 'volcker' in SOTS:
    st, du, at, ln = sot_cfg('volcker', 0.0, 20.0)
    sc.append(SOT(SOTS['volcker']['clip'], st, du, ln, "폴 볼커", "전 연준 의장", SOTS['volcker'].get('src', ''), "[전] 원음 볼커", at))
    sc[-1]["sketch"][0].update({"at": 0.0, "t0": 0.0})   # 11/27 대표: 앞 장면의 '폴 볼커' 글씨가 끊기지 않게 원음 시작부터
sc.append(FX("volcker20", "vs2", {"hl_style": "pop", "kicker": "볼커 쇼크", "title": "금리를 20%까지", "items": [
        {"k": "1979년 물가", "big": "10%+"},
        {"k": "1981년 금리", "big": "20%", "hi": True}],
        "foot": "미국 연방준비제도 · 노동통계국"},
    ["볼커는 금리를 무려 20%까지 올렸습니다. 돈 빌리는 값을 엄청 비싸게 만들어서, 사람들이 돈을 덜 쓰게 하고 물가를 잡겠다는 거죠."],
    "연준 기준금리 1981년 최고 20%(federalreservehistory.org, 2026-11 확인)", "[전] 금리 20%(코드)", at=[("볼커는", 0), ("20%까지", 1)]))
sc.append(S([R + "tractors_dc"],
    ["미국이 발칵 뒤집혔습니다. 빚을 진 농부들은 트랙터를 몰고 워싱턴으로 가, 연준 건물을 막아섰습니다."],
    [], "연준 역사 · 미국 돈 박물관(MOAF)", "[전] 트랙터"))
sc.append(S([R + "lumber_mail", R + "keys_coffin"],
    ["집이 안 팔린 건설업자들은 쓸모없어진 각목에 우표를 붙여 연준으로 보냈고,",
     "차를 못 판 자동차 딜러들은 팔지 못한 차의 열쇠를 관에 담아 보냈습니다."],
    [], "세인트루이스 연준 FRASER(각목 원본 보관) · 연준 역사", "[전] 각목과 관", v={"cut_by_line": True}))
sc.append(S(["il_L261113g2_volcker_pit"],
    ["그래도 볼커는 물러서지 않았습니다. 결국 물가는 잡혔고, 미국은 그 뒤 20년 가까이 호황을 누립니다. 금리 하나로 나라 전체의 체온을 바꾼 겁니다.", "그럼 금리 이야기는 여기서 끝일까요? 아직 아닙니다. 진짜 반전은 그다음입니다."],
    [], "연준 역사(federalreservehistory.org, 2026-11 확인)", "[전] 볼커의 승리 · 가짜 결말"))
sc.append(S([R + "lehman_2008"],
    ["그리고 2008년 금융위기. 이번엔 반대로 미국이 금리를 0%까지 내립니다. 돈을 거의 공짜로 빌릴 수 있는 시대가, 그 뒤로 10년 넘게 이어졌죠."],
    [], "연준 2008-12-16 기준금리 0~0.25%", "[전] 2008 제로 금리"))
sc.append(S([R + "copenhagen_home"],
    ["그리고 볼커가 금리를 올린 지 꼭 40년 뒤인 2019년, 정반대 세상이 옵니다. 덴마크의 한 은행이 이런 주택 대출을 내놓습니다. 금리, 마이너스 0.5%.",
     "빌린 돈보다 덜 갚는 대출. 은행이 돈 좀 빌려 가 달라고 하는, 공짜 돈의 시대였습니다."],
    [P("금리 -0.5%", s="2019년 덴마크 위스케 은행 10년 주택 대출", line=0, at=0.75)], "CNBC 2019-08-12", "[전] 마이너스 금리"))
sc.append(FX("bill2022", "lchart", {"kicker": "공짜 돈의 청구서", "title": "1년 만에 0%대 → 4%대", "badge": "+4.25%포인트", "badge_at": 7.4,
        "ser": [["2021-12", 0.25], ["2022-02", 0.25], ["2022-03", 0.5], ["2022-05", 1.0], ["2022-06", 1.75], ["2022-07", 2.5], ["2022-09", 3.25], ["2022-11", 4.0], ["2022-12", 4.5]],
        "marks": [{"d": "2021-12", "label": "기준금리 0%대", "color": "pink", "at": 4.6, "up": False}, {"d": "2022-12", "label": "4%대", "color": "pink", "up": True, "at": 7.3}], "t0": 4.8, "dur": 2.6,
        "ser2": [["2021-12", 15645], ["2022-02", 13751], ["2022-03", 14221], ["2022-05", 12081], ["2022-06", 11029], ["2022-07", 12391], ["2022-09", 10576], ["2022-11", 11468], ["2022-12", 10466]],
        "name2": "나스닥", "end2": "나스닥 -33%", "t02": "나스닥은", "dur2": 2.4},   # 11/27 대표 "금리 올라가는 거 보여줄 때 나스닥 내려가는 거 같은 그래프에"
    ["그리고 2022년, 청구서가 날아옵니다. 물가가 다시 뛰자 미국은 0%대였던 금리를 1년 만에 4%대로 올렸고, 기술주가 모인 나스닥은 한 해에 33% 빠졌습니다."],
    "연준 기준금리 상단 2021-12 0.25% → 2022-12 4.50% · 나스닥 종합지수 월말 종가 2021-12 15,645 → 2022-12 10,466(-33.1%)", "[전] 2022(코드 · 선 그래프)"))
sc.append(S(["il_L261113g2_fed_winter"],
    ["그런데 이상하지 않으세요? 볼커 때는 금리가 20%였는데, 왜 지금은 4%만 돼도 세상이 이렇게 흔들릴까요?"],
    [], "연준 기준금리 1981년 20% · 2022-12 4.25~4.50%", "[리후킹] 왜 4%에도"))

# ───────── 파동: 금리의 파동이 커졌다 ─────────
# 11/27 18:35 대표 A안 확정: 물 높이 비유 → 바람(금리)과 물(빚). 같은 바람도 작은 호수에선 잔물결, 바다에선 먼 거리를 밀며 큰 파도(취송거리)
_W = "il_R1204d_"
sc.append(CH(PS([(_W + "lake_wide.png", None), (_W + "lake_ripple.png", "작은 호수에선"), (_W + "sea_wind.png", "그런데 바다에선"), (_W + "big_wave.png", "집채만 한"),
                 (_W + "lake_wide.png", "1980년 미국의", (.5, .55, 1.3)), (_W + "big_wave.png", "지금은 바다", (.5, .45, 1.25))],   # 11/28 크레딧 충전 → 4장 모두 사용
    ["금리를 바람, 빚을 물이라고 생각해 보세요. 같은 바람이 불어도, 작은 호수에선 잔물결로 끝납니다.",
     "그런데 바다에선 그 바람이 수천 킬로미터를 밀고 가면서, 집채만 한 파도가 되죠. 1980년 미국의 빚은 호수였습니다. 지금은 바다입니다."],
    [("금리는 바람, 빚은 물", "", "금리를 바람")],
    "미국 재무부(나라 빚 1980 회계연도 말 9,077억 달러 → 2026년 38조 달러+)", "[파동] 바람과 물 비유(사진+글)"), "금리의 파동"))
sc.append(FX("ripple", "ripple", {"kicker": "같은 1%포인트, 다른 물", "title": "미국 나라 빚", "ponds": [
        {"k": "1980년 · 1조 달러", "v": "이자 +90억 달러", "r": 0.12},
        {"k": "지금 · 38조 달러+", "v": "이자 +3,800억 달러", "r": 0.92}], "drop": 2.2},
    ["1980년 미국 나라 빚은 1조 달러 정도였습니다. 그때 금리 1%포인트는 1년 이자 90억 달러였죠.", "지금은 빚이 38조 달러가 넘습니다. 같은 1%포인트가, 이제 3,800억 달러입니다."],
    "미국 재무부(1980 회계연도 말 9,077억 달러 · 2026년 38조 달러+)", "[파동] 연못과 바다(코드)"))
sc.append(PS([("il_base_bond_certs.jpeg", None), ("il_base_dollar_stack.jpeg", "금리가 딱"), ("il_L261113a_cash_count.jpeg", "1년 이자만")],   # 11/27 대표 "지구 위성 사진이 빚이랑 관련이 있나?"
    ["세계 전체 빚은 365조 달러입니다. 금리가 딱 1%포인트만 올라도, 단순하게 계산해서 1년 이자만 3조 6,500억 달러가 더 붙습니다."],
    [("세계 빚 365조 달러", "", "세계 전체"), ("이자 +3.65조 달러", "금리 1%포인트 오르면 · 1년", "금리가 딱")],
    "IIF 2026-09-23", "[파동] 세계 빚(사진+글)"))
sc.append(PS([("il_L261107m_powerlines_homes.jpeg", None), ("il_L261107m_powerlines_homes.jpeg", "금리가 1%포인트만", (.7, .7, 1.6)), ("il_L261107m_powerlines_homes.jpeg", "한 달에", (.3, .72, 1.7))],
    ["우리 집으로 가져와 볼까요. 3억 원을 빌린 집이라면, 금리가 1%포인트만 올라도 1년 이자가 300만 원 늘어납니다. 한 달에 25만 원이 더 나가는 거죠."],
    [("1년 이자 +300만 원", "3억 대출 · 금리 1%포인트", "금리가 1%포인트만"), ("매달 +25만 원", "", "한 달에")],
    "계산 예시(3억 원 × 1%포인트 = 1년 300만 원, 한 달 25만 원)", "[파동] 우리 집(사진+글)"))
sc.append(FX("usint", "race", {"kicker": "미국 정부가 1년에 내는 이자", "title": "국방비보다 큰 이자", "fmt": "{k}억 달러", "fx": 1, "dec": 0, "step": 1.45, "room": 1.22, "fixmax": True, "y0": 400, "bh": 150, "x0": 420,
        "colors": {"2019년": "rgb(225,225,228)", "2026년": "rgb(255,77,109)"},
        "frames": [{"label": "", "vals": {"2019년": 0.1, "2026년": 0.1}}, {"label": "", "vals": {"2019년": 0.1, "2026년": 0.1}}, {"label": "", "vals": {"2019년": 3750, "2026년": 0.1}}, {"label": "", "vals": {"2019년": 3750, "2026년": 0.1}}, {"label": "", "vals": {"2019년": 3750, "2026년": 10520}}]},   # 말("2019년"·"2026년")에 맞춘 단계
    ["미국 정부가 1년에 내는 이자는 2019년 3,750억 달러에서, 2026년 1조 520억 달러가 됐습니다. 하루에 29억 달러. 나라를 지키는 국방비보다 이자가 더 큽니다."],
    "미국 재무부 2026 회계연도", "[파동] 미국 이자(코드 · 막대)"))
sc.append(FX("aivsint", "vs2", {"hl_style": "pop", "kicker": "같은 돈을 두고", "title": "AI와 이자", "items": [
        {"k": "국채 이자", "big": "3.3", "unit": "조 달러", "hi": True},
        {"k": "AI 투자", "big": "2.6", "unit": "조 달러"}],
        "foot": "1년 기준 · 국제금융협회(IIF) 2026-09"},
    ["더 놀라운 건 이겁니다. 선진국 정부들이 1년 동안 낸 국채 이자가 3조 3,000억 달러. 세계가 AI에 쓴 2조 6,000억 달러보다 많습니다.",
     "AI와 이자가, 사실상 같은 돈을 두고 다투고 있는 셈이죠."],
    "IIF 2026-09-23", "[파동] AI vs 이자(코드)", hl=[('선진국', 0), ('세계가 AI', 1)]))
sc.append(FX("chain", "chain", {"kicker": "파도가 오는 순서", "title": "몇 초 만에 번지는 파동", "nodes": [
        {"k": "금리 발표"}, {"k": "국채 금리"}, {"k": "달러"}, {"k": "성장주"}], "step": 1.5, "wave": True},
    ["파도의 속도도 달라졌습니다. 예전엔 금리가 바뀌면 몇 달에 걸쳐 퍼졌지만, 지금은 발표 몇 초 만에 국채 금리가 움직이고, 달러가 움직이고, 성장주가 출렁입니다."],
    "", "[파동] 파도 순서(코드)"))
sc.append(FX("floor", "floor", {"kicker": "왜 국채에서 시작할까", "title": "모든 금리의 바닥", "base": {"k": "국채 금리", "v0": 4, "v1": 5},
        "bars": [{"k": "회사 대출", "spread": 1.5}, {"k": "집 대출", "spread": 2.2}, {"k": "주식 기대 수익", "spread": 4}], "rise_label": "바닥이 오르면, 전부 같이 오른다",
        "rise_word": "국채 금리가 오르면", "bar_words": ["회사 대출도", "집 대출도", "주식도"]},
    ["그럼 왜 파도는 국채에서 시작할까요? 미국 국채는 세상에서 가장 안전한 빚입니다. 미국 정부가 못 갚을 일은 거의 없으니까요.",
     "그래서 국채 금리가 모든 금리의 바닥이 됩니다. 회사 대출도, 집 대출도, 국채 금리 위에 위험한 만큼 조금씩 더 얹은 값이죠. 주식도 마찬가지입니다. 안전한 국채보다는 더 벌어야 사니까요.",
     "그러니 바닥인 국채 금리가 오르면, 그 위에 얹힌 모든 금리가 같이 올라갑니다. 파도가 늘 국채에서 시작하는 이유입니다."],
    "", "[파동] 국채가 바닥인 이유(코드)"))
sc.append(S(["il_L261113g_fed_dusk"],
    ["정리하면 이렇습니다. 아까 본 볼커 때보다 금리 숫자 자체는 낮지만, 그 금리가 흔드는 물이 수십 배가 됐습니다. 그래서 작은 변화도, 이제는 큰 파도가 됩니다."],
    [], "", "[파동] 정리"))

# ───────── 결: 금리를 읽는 법 ─────────
sc.append(CH(S(["il_R1204b_crash1929"],
    ["1929년 10월, 뉴욕 월가 앞에 사람들이 몰려들었습니다. 주가가 하루에 10% 넘게 무너진 날이었죠."],
    [], "1929년 10월 뉴욕 증시 대폭락", "[결] 1929"), "금리를 읽는 법"))
sc.append(FX("bubbles", "chain", {"kicker": "버블을 끝낸 것", "title": "늘 금리였다", "dx": 520,
        "nodes": [{"k": "1929 대공황"}, {"k": "2000 닷컴"}, {"k": "2022 기술주"}]},
    ["역사를 보면 버블을 끝낸 건 늘 금리였습니다. 1929년 대공황 직전에도, 2000년 닷컴 버블 직전에도, 2022년에도, 미국은 금리를 올리고 있었습니다."],
    "연준 역사 · 1929년 8월 재할인율 6% · 2000년 5월 6.5%", "[결] 버블과 금리(코드 · 사슬)", at=[("1929년 대공황", 0), ("2000년", 1), ("2022년에도", 2)]))
sc.append(FX("discount", "race", {"kicker": "10년 뒤 받을 1억 원", "title": "지금 가치는?", "fmt": "{k}만 원", "fx": 1, "dec": 0, "step": 1.5, "room": 1.25, "fixmax": True, "y0": 400, "bh": 150, "x0": 420,
        "colors": {"금리 1%": "rgb(225,225,228)", "금리 5%": "rgb(255,77,109)"},
        "frames": [{"label": "", "vals": {"금리 1%": 0.1, "금리 5%": 0.1}}] * 5 + [{"label": "", "vals": {"금리 1%": 9053, "금리 5%": 0.1}}] * 2 + [{"label": "", "vals": {"금리 1%": 9053, "금리 5%": 6139}}]},   # 말("1%면"·"5%면")에 맞춘 단계
    ["그래서 AI 같은 큰 꿈일수록 금리에 약합니다. 10년 뒤에 받을 1억 원을 생각해 보세요. 금리가 1%면 지금 가치로 9,053만 원이지만, 금리가 5%면 6,139만 원으로 줄어듭니다.",
     "돈을 벌 날이 먼 미래일수록, 금리가 오를 때 지금 몸값이 크게 깎이는 거죠. 게다가 AI 데이터센터는 대부분 빌린 돈으로 짓습니다."],
    "계산 예시(1억 원 ÷ 1.01^10 = 9,053만 원, ÷ 1.05^10 = 6,139만 원)", "[결] 할인(코드 · 막대)"))
sc.append(FX("read3", "vs2", {"hl_style": "pop", "kicker": "금리 뉴스를 볼 때", "title": "세 가지만 기억하세요", "items": [
        {"k": "하나", "big": "10년 국채", "bs": 76},
        {"k": "둘", "big": "예상과 차이", "bs": 76},
        {"k": "셋", "big": "파도 순서", "bs": 76, "hi": True}]},
    ["그러니 금리 뉴스를 볼 때는 세 가지만 기억하세요.",
     "첫째, 중앙은행이 정하는 기준금리보다, 시장이 매기는 10년 국채 금리가 내 주식에 더 가깝습니다. 둘째, 결정 그 자체보다 예상과 얼마나 달랐는지가 시장을 움직입니다. 셋째, 파도는 국채, 달러, 주식 순서로 옵니다."],
    "", "[결] 읽는 법(코드)", hl=[('첫째', 0), ('둘째', 1), ('셋째', 2)]))
# (11/27 질문 한 줄은 아래 위원 장면 첫 줄로 합침 — 3초짜리 사진 장면 없앰)
sc.append(CH(PS([("il_R1204b_fomc_room.png", None), ("il_R1204c_s44_1.png", "미국에서는"), ("il_R1204c_s44_1.png", "투표로", (.45, .55, 1.5)), ("il_R1204c_s44_2.png", "한국에서는")],
    ["그럼 이 금리는 누가 정할까요?", "미국에서는 중앙은행인 연준의 위원 12명이 1년에 8번 모여 투표로 정합니다.", "한국에서는 한국은행 금융통화위원 7명이 정하죠."],
    [("미국 연준 12명", "1년에 8번 투표", "위원 12명"), ("한국은행 7명", "금융통화위원회", "한국에서는")],
    "연준 FOMC(투표권 12명 · 연 8회) · 한국은행 금융통화위원회(7명)", "[다음 파도] 위원 수(사진+글)"), "다음 파도"))
sc.append(FX("watch", "vs2", {"hl_style": "fill", "kicker": "이들이 보는 것", "title": "물가와 일자리", "items": [
        {"k": "물가가 뜨거우면", "big": "올린다", "hi": True},
        {"k": "일자리가 식으면", "big": "내린다"}],
        "foot": "미국 물가 목표 2%"},
    ["이들이 보는 건 크게 두 가지입니다. 물가와 일자리.", "물가가 너무 오르면 금리를 올려 돈을 덜 쓰게 하고, 경기가 식어 일자리가 줄면 금리를 내려 돈이 돌게 합니다. 볼커가 한 일도 바로 이거였죠. 미국이 목표로 하는 물가는 1년에 2%입니다."],
    "연준 물가 목표 2%", "[다음 파도] 올릴까 내릴까(코드)", hl=[('물가가 너무', 0), ('경기가 식어', 1)]))
sc.append(PS([("il_L261107m_capitol_dawn.jpeg", None), ("il_L261107m_capitol_dawn.jpeg", "12월 9일,", (.5, .45, 1.6)), ("il_L261110a_empty_podium.jpeg", "한국 시간으로는"), ("il_L261110a_empty_podium.jpeg", "미국 물가가", (.3, .55, 1.6)), ("il_L261110a_empty_podium.jpeg", "시장은 금리가", (.75, .5, 1.5)), ("il_L261110a_empty_podium.jpeg", "가능성을", (.5, .6, 1.25))],
    ["그리고 지금 전 세계가 보고 있는 날짜가 있습니다. 12월 9일, 미국 연준의 올해 마지막 금리 결정입니다. 한국 시간으로는 10일 새벽이죠.",
     "미국 물가가 5년 넘게 목표를 웃돌자, 시장은 금리가 0.25%포인트 더 오를 가능성을 97.8%로 보고 있습니다."],
    [("12월 9일", "올해 마지막 금리 결정", "12월 9일,"), ("인상 확률 97.8%", "+0.25%포인트 · CME 페드워치 11월 25일", "가능성을")],
    "CME FedWatch 2026-11-25 스냅숏(0.25%p 인상 97.8%) · 연준 목표 범위 3.75~4.00%", "[다음 파도] 12월 9일(사진+글)"))
sc.append(S(["il_R1204b_markets_wait"],
    ["그래서 금값도, 비트코인도, 주식도, 이 날짜를 앞두고 출렁이고 있습니다.",
     "그런데 아까 두 번째로 기억하자고 한 것, 기억하시죠? 가격에는 이미 모두가 아는 금리 인상이 반영돼 있습니다. 진짜 파도는 결정 그 자체보다, 연준이 그날 뭐라고 말하느냐에서 나옵니다."],
    [], "", "[다음 파도] 출렁이는 시장"))
# 2026-11-27 08:57 대표 "금리 결정 다음 연준이 뭐라고 하는 게 중요하다 — 이 부분을 조금 더 구체적으로, 사람들 헷갈릴 수 있다"
sc.append(FX("fedsays", "chain", {"kicker": "12월 9일, 같이 나오는 것", "title": "결정 하나에 세 가지", "dx": 520,
        "nodes": [{"k": "금리 결정"}, {"k": "기자회견"}, {"k": "점도표"}], "wave": True},
    ["연준은 그날 금리만 발표하지 않습니다. 세 가지가 같이 나옵니다.",
     "첫째, 금리 결정. 이번엔 시장이 이미 거의 다 예상하고 있어서, 결정 자체는 큰 뉴스가 아닙니다.",
     "둘째, 성명서와 의장 기자회견. 여기서 '물가가 아직 높다', '추가 인상도 검토한다' 같은 한 문장이 나오면 시장이 바로 움직입니다.",
     "셋째, 점도표. 연준 위원들이 각자 내년 말 금리가 어디쯤일지 점을 하나씩 찍은 표입니다. 점들이 위로 몰려 있으면 내년에도 더 오른다는 뜻이고, 아래로 내려오면 이제 멈춘다는 뜻이죠."],
    "연준 FOMC 발표 구성: 정책 결정 · 성명서 · 의장 기자회견 · 경제전망 요약(SEP, 점도표는 3·6·9·12월)", "[다음 파도] 결정 뒤에 볼 것(코드 · 사슬)",
    at=[("첫째", 0), ("둘째", 1), ("셋째", 2)]))
sc.append(FX("reaction", "vs2", {"kicker": "같은 0.25%p 인상이라도", "title": "말 한마디에 갈린다", "hl_style": "spot", "items": [
        {"k": "\"이번이 마지막일 수도\"", "big": "주식 ↑", "bs": 96},
        {"k": "\"내년에도 더 올린다\"", "big": "주식 ↓", "bs": 96, "color": "red"}]},
    ["그래서 같은 0.25%포인트 인상이라도, 연준이 '이번이 마지막일 수 있다'고 하면 주식이 오히려 오를 수 있고,",
     "'내년에도 더 올린다'고 하면 떨어질 수 있습니다. 결정보다 말을 보라는 이유입니다."],
    "", "[다음 파도] 시장 반응(코드)", hl=[("이번이 마지막", 0), ("내년에도 더", 1)]))
sc.append(S([R + "closing_dawn", "il_R1204c_s49_1", "il_R1204c_s49_3"],
    ["맨 처음 본 성경 문장, 기억하시죠? 3,000년 전엔 지옥에 가는 죄였던 숫자가, 이제 365조 달러의 바다를 흔듭니다.",
     "다음 파도가 올 때, 여러분은 메디치가 될까요, 샤일록이 될까요?"],
    [], "", "[마무리] 열린 질문", v={"cuts": [{"lib": R + "closing_dawn.png"}, {"lib": "il_R1204c_s49_1.png", "word": "3,000년 전엔"}, {"lib": "il_R1204c_s49_3.png", "word": "다음 파도가"}]}))   # 11/27 대표 "메디치 줌인하지 마 — 두 명 다 원래대로"
# 11/28 08:34 대표 "마지막에 밸류노트 금리 페이지를 살짝 소개 — 그 화면으로 보여 주고 넘어가자"
sc.append(S(["il_L261123s_fed_dawn"],
    ["지금 금리가 어디 있는지는 밸류노트 금리 페이지에 정리해 두었습니다. 나라별 국채 금리와 기준금리, 다음 결정일까지 매일 갱신됩니다.",
     "금리가 바뀌면 내 종목의 적정 주가가 어떻게 달라지는지도 직접 움직여 볼 수 있습니다. 주소는 설명란에 있습니다."],
    [], "밸류노트 금리 페이지(valuenote.co.kr/rate, 2026-11-28 화면)", "[마무리] 금리 페이지 소개(앱 화면)",
    v={"cuts": [{"lib": "app_rates_L261204_a.mp4"}, {"lib": "app_rates_L261204_b.mp4", "word": "금리가 바뀌면 내"}]}))
sc.append(S(["il_R1204b_subscribe"],
    ["여러분의 구독, 좋아요, 댓글은 영상 제작에 큰 힘이 됩니다."],
    [], "", "[마무리] 구독"))
sc.append({"v": {"type": "end", "sub": "", "btn_at": ["0:거시적", "0:거시적", "0:거시적"], "note": {"text": ""}, "dark_end": True, "end_v2": True,
                 "slogan": ["시장의 흐름 뒤", "숨은 이야기를 읽는 채널", "거시적 관점으로 시장을 이해하면, 투자가 달라집니다"]},
           "lines": ["거시적 관점으로 시장을 이해하면, 투자가 달라집니다. 감사합니다. 밸류노트였습니다."],
           "sketch_add": [], "asof": False, "src": "", "note": "[북엔드] 끝 화면"})

for _x in sc:   # 2026-11-26: 실사로 만든 그림인데 프롬프트의 painting 같은 낱말로 애니메이션풍으로 잡히는 컷
    for _c in _x['v'].get('cuts', []):
        if _c.get('lib') in ('il_R1204_friend_loan.png', 'il_R1204_renaissance_chapel.png'): _c['allow_anim'] = True
ph = [c["lib"] for x in sc for c in x["v"].get("cuts", []) if c["lib"].startswith("il_")]
dups = sorted({l for l in ph if ph.count(l) > 1})

base = json.load(open(HJ + '/scripts/youtube/long/specs/L261124-gold-3.json'))
# ── 겹침 관문(2026-11-26): 한 장면 안에서 강조 문구·이름표·인용·단계표가 동시에 뜨지 않게 ──
for _i, _s in enumerate(sc):
    _k = [(b.get("kind"), b.get("line", 0), b.get("at", 0)) for b in (_s.get("sketch") or []) if b.get("kind") in ("punch", "lower", "quote", "steps", "tl", "stamp")]
    if any(k in ("steps", "tl") for k, _, _ in _k) and len(_k) > 1:
        raise SystemExit(f"겹침: 장면 {_i} 단계표·연표는 끝까지 남으니 다른 강조와 같이 못 둠 {_k}")
    _lines = [l for _, l, _ in _k]
    _w = sorted((b["t0"], b["until"]) for b in (_s.get("sketch") or []) if b.get("t0") is not None and b.get("until") is not None)
    _ok = len(_w) == len(_k) and all(_w[i][1] <= _w[i + 1][0] + .05 for i in range(len(_w) - 1))   # 11/27: 시각을 못박은 글씨끼리 안 겹치면 같은 줄에 둘 수 있다
    if len(_lines) != len(set(_lines)) and not _ok:
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
# 2026-11-27 대표 "한 사진 4~5초 넘게 쓰지 말고, 사진을 과감하게 더 생성해 더 많이 — 인트로는 더": 장면마다 추가 생성 사진(인트로는 큰 베이스마다, 뒤는 약 3.5초마다 고르게)
# 11/27 검수: 글자·숫자가 읽히는 사진(sold 표지판·달력 2장·글자 새겨진 비석)은 뺌
EXTRA = {
 "il_R1204_stone_tablet.png": [
  "il_R1204c_s01_1.png",
  "il_R1204c_s01_2.png"
 ],
 "il_R1204_church_burial.png": [
  "il_R1204c_s02_1.png"
 ],
 "il_R1204_trading_screens.png": [
  "il_R1204c_s03_1.png",
  "il_R1204c_s03_2.png",
  "il_R1204c_s03_3.png",
    "il_R1204c_s03_5.png",
  "il_R1204c_s03_6.png",
  "il_R1204c_s03_7.png"
 ],
 "il_R1204_friend_loan.png": [
  "il_R1204c_s05_1.png",
  "il_R1204c_s05_2.png",
    "il_R1204c_s05_4.png"
 ],
 "il_R1204b_hammurabi.png": [
  "il_R1204c_s07_1.png",
  "il_R1204c_s07_2.png"
 ],
 "il_R1204_babylon_market.png": [
  "il_R1204c_s09_1.png"
 ],
 "il_R1204_moneylender_candle.png": [
  "il_R1204c_s10_1.png",
  "il_R1204c_s10_2.png",
  "il_R1204c_s10_3.png",
  "il_R1204c_s10_4.png"
 ],
 "il_R1204b_dante_hell.png": [
  "il_R1204c_s11_1.png",
  "il_R1204c_s11_2.png",
  "il_R1204c_s11_3.png"
 ],
 "il_R1204_venice_court.png": [
  "il_R1204c_s12_1.png",
  "il_R1204c_s12_2.png"
 ],
 "il_R1204_islamic_bank.png": [
  "il_R1204c_s13_1.png",
  "il_R1204c_s13_2.png"
 ],
 "il_R1204b_medici_palazzo.png": [
  "il_R1204c_s14_1.png"
 ],
 "il_R1204_florence_bench.png": [
  "il_R1204c_s15_1.png",
  "il_R1204c_s15_2.png",
  "il_R1204c_s15_3.png"
 ],
 "il_R1204b_cosimo.png": [
  "il_R1204c_s17_1.png",
  "il_R1204c_s17_2.png",
  "il_R1204c_s17_3.png"
 ],
 "il_R1204_broken_bench.png": [
  "il_R1204c_s18_1.png",
  "il_R1204c_s18_2.png",
  "il_R1204c_s18_3.png"
 ],
 "il_R1204_london_1694.png": [
  "il_R1204c_s19_1.png",
  "il_R1204c_s19_2.png",
  "il_R1204c_s19_3.png"
 ],
 "il_R1204_tractors_dc.png": [
  "il_R1204c_s24_1.png"
 ],
 "il_R1204_lumber_mail.png": [
  "il_R1204c_s25_1.png",
  "il_R1204c_s25_2.png"
 ],
 "il_L261113g2_volcker_pit.jpeg": [
  "il_R1204c_s26_1.png",
  "il_R1204c_s26_2.png",
  "il_R1204c_s26_3.png"
 ],
 "il_R1204_lehman_2008.png": [
  "il_R1204c_s27_1.png",
  "il_R1204c_s27_2.png"
 ],
 "il_R1204_copenhagen_home.png": [
  "il_R1204c_s28_1.png",
  "il_R1204c_s28_2.png",
  "il_R1204c_s28_3.png",
  "il_R1204c_s28_4.png"
 ],
 "il_L261113g2_fed_winter.jpeg": [
  "il_R1204c_s30_1.png"
 ],
 "il_R1204_stone_pond.png": [],   # 11/27 물 높이 비유로 바꿈 — 돌 던지는 사진은 뺌
 "il_L261113g_fed_dusk.jpeg": [
  "il_R1204c_s39_1.png",
  "il_R1204c_s39_2.png"
 ],
 "il_R1204b_crash1929.png": [
  "il_R1204c_s40_1.png"
 ],
 "il_R1204b_fomc_room.png__off": [
  "il_R1204c_s44_1.png",
  "il_R1204c_s44_2.png"
 ],
 "il_R1204b_markets_wait.png": [
  "il_R1204c_s48_1.png",
  "il_R1204c_s48_2.png",
  "il_R1204c_s48_3.png"
 ],
 "il_L261123s_fed_dawn.png": [
  "il_R1204c_s50_1.png",
  "il_R1204c_s50_2.png"
 ],
 "il_R1204b_subscribe.png": [
  "il_R1204c_s51_1.png"
 ]
}
for s_ in sc:
    _c = s_["v"].get("cuts") or []
    if _c and _c[0].get("lib") in EXTRA:
        for _n in EXTRA[_c[0]["lib"]]:
            if not os.path.exists(LIB + _n): PENDING.add(_n)
            _c.append({"lib": _n})

# 2026-11-27 08:46 대표 "집이란 말과 동시에, 금이란 말과 동시에, AI라는 말과 동시에 사진을 딱딱딱 — 마지막 사진으로 쭉": 훅 셋째 장면은 낱말 컷
for s_ in sc:
    _c = s_["v"].get("cuts") or []
    if _c and _c[0].get("lib") == R + "trading_screens.png":
        s_["v"]["cuts"] = [{"lib": R + "trading_screens.png"},
                           {"lib": "il_R1204c_s03_1.png", "word": "집값"}, {"lib": "il_R1204c_s03_5.png", "word": "주식"},
                           {"lib": "il_R1204c_s03_2.png", "word": "금값"}, {"lib": "il_R1204c_s03_3.png", "word": "AI"},
                           {"lib": "il_R1204c_s03_6.png", "word": "죄였던 이자는"}, {"lib": "il_R1204c_s03_7.png", "word": "4,000년 금리의"}]   # 11/27 09:49 대표: AI 사진은 '몸값까지 정합니다'까지, 다음 문장에서 새 사진으로 인트로 마무리

# ── 2026-11-27 10:46 대표 "사진 하나를 5초 넘게(특히 메디치) 쓰지 말 것 · 볼커 사진은 '키가 2미터' 때 · 하이라이트 글씨는 그 사진과 같이 나오고 같이 사라질 것"
#    사진 컷을 말에 묶는다: 지난 렌더의 실제 줄 시각으로 문장·쉼표 경계 중 3~4.8초 간격 지점을 고르고, 그 낱말(word)에서 사진이 바뀐다(렌더가 실제 말 시각으로 다시 계산)
#    사진이 모자라면 같은 사진의 다른 부분을 당겨 찍은 컷(crop)을 넣는다. 펀치·이름표는 자기 사진이 바뀌는 순간에 사라진다(t0·until)
import re as _re, math as _m
_TLR = json.load(open(_TLP)) if os.path.exists(_TLP) else []
_TLB = {tuple(l[2] for l in e["lines"]): e["lines"] for e in _TLR}   # 줄 글로 찾는다(첫 사진이 바뀌어도 찾게)
FIRST_AT = {}   # 11/27 볼커 장면은 직접 컷을 정함   # 이 사진은 이 말에서 처음 나온다
_CROPS = [(.3, .4, 1.45), (.7, .55, 1.45), (.5, .35, 1.6)]
def _cands(lines):
    out = []   # (시각, 줄번호, 글자위치)
    for li, (a_, d_, tx) in enumerate(lines):
        nt = max(1, len(tx.replace(" ", "")))
        for m_ in _re.finditer(r"(?:(?<=[.?!])|(?<=,)) +(?=\S)", tx):
            k_ = m_.end(); out.append((a_ + d_ * len(tx[:k_].replace(" ", "")) / nt, li, k_))
        if li: out.append((a_, li, 0))
        for m_ in _re.finditer(r" (?=\S)", tx):   # 낱말 사이(5초를 넘길 때만 씀)
            k_ = m_.end(); out.append((a_ + d_ * len(tx[:k_].replace(" ", "")) / nt + 1e-4, li, -k_))
    return sorted(out)
def _frag(lines, li, k_):
    tx = lines[li][2]; k_ = abs(k_); allt = " / ".join(l[2] for l in lines)
    for n_ in range(4, 30):
        f_ = tx[k_:k_ + n_]
        if f_.strip() and allt.count(f_) == 1 and not f_.endswith(" "): return f_
    return tx[k_:k_ + 12]
for s_ in sc:
    v_ = s_["v"]; cs_ = v_.get("cuts") or []
    if not cs_ or s_.get("sot") or v_.get("ident") or any(isinstance(c_, dict) and c_.get("word") for c_ in cs_): continue
    if any(str(c_.get("lib", "")).endswith(".mp4") for c_ in cs_): continue
    L_ = _TLB.get(tuple(s_["lines"]))
    if not L_: continue
    end_ = L_[-1][0] + L_[-1][1] + .35
    cands = _cands(L_); bnd = [(0.0, None)]; last = 0.0
    fa = next((FIRST_AT[c_["lib"]] for c_ in cs_ if c_["lib"] in FIRST_AT), None)
    if fa:   # 지정 사진이 나오는 경계는 반드시 둔다
        li_ = next(i for i, l in enumerate(L_) if fa in l[2]); k0 = L_[li_][2].index(fa)
        must = (L_[li_][0] + L_[li_][1] * len(L_[li_][2][:k0].replace(" ", "")) / max(1, len(L_[li_][2].replace(" ", ""))), li_, k0)
    else: must = None
    while True:
        if must and last < must[0] - .1 and must[0] - last <= 5.0 and must[0] - last >= 2.4:
            nxt = [c for c in cands if c[0] < must[0] - 2.4 and c[0] >= last + 3.0 and c[2] >= 0]
            if must[0] - last > 4.8 and nxt: c = nxt[0]
            else: c = must; must_used = True
            bnd.append((c[0], (c[1], c[2]))); last = c[0]; continue
        if end_ - last <= 4.7: break
        ph = [c for c in cands if last + 2.8 <= c[0] <= last + 4.6 and c[2] >= 0 and end_ - c[0] >= 2.2 and (not must or c[0] < must[0] - 2.4 or c[0] > must[0])]
        wd = [c for c in cands if last + 2.8 <= c[0] <= last + 4.4 and end_ - c[0] >= 2.2 and (not must or c[0] < must[0] - 2.4 or c[0] > must[0])]
        c = (ph[-1] if ph else (wd[len(wd) // 2] if wd else None))
        if c is None: break
        bnd.append((c[0], (c[1], c[2]))); last = c[0]
    if fa and not any(b_[1] and abs(b_[0] - must[0]) < .05 for b_ in bnd):
        bnd = [b_ for b_ in bnd if not (b_[1] and must[0] - 2.4 < b_[0] < must[0] + 2.4)] + [(must[0], (must[1], must[2]))]; bnd.sort(key=lambda x: x[0])
    n_ = len(bnd)
    _sn = set(); pool = [c_ for c_ in cs_ if c_["lib"] not in FIRST_AT and not (c_["lib"] in _sn or _sn.add(c_["lib"]))]; fx_ = [c_ for c_ in cs_ if c_["lib"] in FIRST_AT]
    new = []
    for i_ in range(n_):
        if fx_ and must and abs(bnd[i_][0] - must[0]) < .05: new.append(dict(fx_[0])); continue
        if pool: new.append(dict(pool.pop(0))); continue
        src_ = new[i_ - 1] if i_ else cs_[0]; base_ = {k: v for k, v in src_.items() if k not in ("word", "crop", "d")}
        new.append(dict(base_, crop=list(_CROPS[i_ % len(_CROPS)])))
    for i_ in range(1, n_):
        li_, k_ = bnd[i_][1]; new[i_]["word"] = _frag(L_, li_, k_)
    for c_ in new: c_.pop("d", None)
    v_["cuts"] = new; v_.pop("cut_by_line", None)
    # 하이라이트(펀치·이름표): 자기 사진 구간에 묶는다
    for it in s_.get("sketch", []):
        if it.get("kind") not in ("punch", "lower"): continue
        if it.get("kind") == "lower" and it.get("text") == "폴 볼커" and must:
            t0_ = must[0]
        else:
            li_ = min(it.get("line", 0), len(L_) - 1); t0_ = L_[li_][0] + it.get("at", .05) * L_[li_][1]
        bt = [b_[0] for b_ in bnd]; j_ = max(i for i, b in enumerate(bt) if b <= t0_ + .3)
        it["t0"] = round(bt[j_] + .15, 2); it["until"] = round(bt[j_ + 1] if j_ + 1 < len(bt) else end_, 2)

spec = {k: base[k] for k in ['format', 'world', 'notebook', 'overlay', 'look', 'roadmap', 'hook', 'music', 'design', 'synthetic_media'] if k in base}
spec['music'] = dict(spec['music'], intro="social/music/own/intro_conspiracy.mp3", intro_offset=0.0,
    hits=[0.09, 5.85, 11.31, 16.9, 23.75, 26.91, 31.46, 34.97, 38.13, 41.1, 44.93, 49.48, 55.05, 58.4, 63.99, 67.29, 70.1, 75.91, 81.2, 86.26],   # 11/27 08:57 대표 '1초도 안 돼서 바뀌는 건 정신없다' → 큰 베이스 약 3~5초 간격으로 되돌림
    intro_by_owner="2026-11-26 15:24 대표: 우리가 만든 인트로 음악 중에서 약간 음모론 같은 그런 인트로 음악 있지 않았어? 그거 한번 써줄래?",
    note="2026-11-26 대표 '음모론 같은 인트로' → 자체 제작 intro_conspiracy(Suno) · 큰 베이스 시각(150Hz 아래 세기 봉우리, 2.8초 간격) · 본편은 M4·M5 그대로")
TITLE = "금리의 모든 것 | 4,000년 전엔 “죄”였던 이자, 금리가 지배하는 세상은 어떻게 만들어졌나"   # 11/27 18:57 썸네일 확정에 맞춤
spec.update({
 "id": "L261204-rate", "company": "RATE", "no_data": True, "series": "", "plan": "P261204-rate",
 "scheduled_at": "2026-11-27T17:30:00+09:00", "manual": True,
 "opening": "성경 구절(형제에게 이자를 받지 말라) → 묻히지 못한 고리대금업자 → 지금은 이자가 모든 가격을 정한다 → 어떻게 왕이 됐나",
 "hook_type": "고전 문장 + 반전(죄 → 왕)",
 "endscreen_target": "L261126-son", "endscreen_also": "L261123-soxl-3",
 "title": TITLE,
 "doc_title": "금리의 모든 것",
 "title_en": "Interest used to be a sin. How did interest rates come to rule the world?",
 "description_head": "3,000년 전 성경은 형제에게 이자를 받지 말라고 했고, 800년 전 교회는 이자를 받은 사람을 묘지에 묻어 주지도 않았습니다. 그 죄였던 이자가 지금은 집값·주식·금값, AI 회사의 몸값까지 정합니다.\n함무라비 법전의 이자 상한, 메디치 가문이 이자를 받은 비법, 은행과 파산이라는 말의 뿌리, 영란은행, 볼커의 금리 20%와 각목 우편, 마이너스 금리 대출, 그리고 금리의 파도가 왜 예전보다 훨씬 커졌는지까지 쉽게 풀었습니다.\n\n📈 지금 금리와 다음 결정일 👉 valuenote.co.kr/rate",
 "description_en": "Interest was once a sin. From Hammurabi's interest caps and the Medici's bills of exchange to the Bank of England, the Volcker shock and negative-rate mortgages, we explain how interest rates came to rule the world and why their waves are bigger than ever. Some images are AI-generated reenactments and are labeled. Not investment advice.",
 "pinned_comment": "📈 지금 금리와 다음 결정일(매일 갱신) 👉 valuenote.co.kr/rate\n\n다음 파도가 올 때, 여러분은 메디치일까요 샤일록일까요? 생각을 남겨 주세요.\n\n※ 역사 장면 사진은 재연 이미지(AI 생성)이고, 폴 볼커 사진은 위키미디어 공용 자료입니다. 숫자 기준 2026년 11월. 매수·매도 권유가 아닙니다.",
 "hook_promises": ["이자가 죄였던 시절", "죄였던 이자가 왕이 된 과정", "금리의 파도가 커진 이유와 읽는 법"],
 "viewer_question": "금리는 왜 이렇게 세상을 흔드나",
 "tags": ["금리", "이자", "기준금리", "금리 역사", "메디치", "볼커", "연준", "국채 금리", "마이너스 금리", "경제 공부", "금리 쉽게"],
 "search_keywords": ["금리란", "금리 역사", "금리 오르면", "이자 역사", "볼커"],
 "sources": ["출애굽기 22:25·신명기 23:20(개역한글)", "제3차 라테라노 공의회(1179) 제25조", "함무라비 법전 제88조", "연준 역사(federalreservehistory.org)", "세인트루이스 연준 FRASER", "CNBC 2019-08-12", "IIF 글로벌 부채 모니터 2026-09-23", "미국 재무부·포춘 2026-10-17", "위키미디어 공용"],
 "format_note": "2026-11-26 대표 — 청소년도 재밌고 쉽게, 시의성 없이 오래 볼 금리 입문, 썰 중심·숫자는 파동 장에서만, 열린 결말, 국내 방송사·영화 장면 금지",
 "orig_mode": "sot_test", "orig_mode_note": "원음+한국어 자막(더빙 없음).",
 "voice_speed": 1.0,   # 11/28 대표 "살짝 빠르다" → 1.03에서 1.00으로(시안)
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
