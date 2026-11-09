# 2026-11-09 팔란티어 롱폼 — 대표 확정 원고 v3(11/9 숫자 축소·전망 보강)(yt_plans P261110-palantir-what data.script) 그대로
# 사용: python3 scripts/youtube/long/drafts/_build_L261109-palantir.py → specs/L261109-palantir-what.json
import json, os, copy, re, math
HERE = os.path.dirname(os.path.abspath(__file__)); SPECS = os.path.join(HERE, "..", "specs")
LIB = os.path.join(HERE, "..", "..", "..", "blog", "media", "lib")
SCRIPT = json.load(open(os.path.join(HERE, "_script_L261109-nvidia.json"), encoding="utf-8"))
base = json.load(open(os.path.join(SPECS, "L261108-lev-91.json"), encoding="utf-8"))
soxl = json.load(open(os.path.join(SPECS, "L261107-soxl-38.json"), encoding="utf-8"))
OUT_DIR = os.environ.get("OUT_DIR", SPECS)
BANNED = {"commons_handshake_1.jpg", "commons_handshake_2.jpg", "commons_samsungfab_1.jpg", "commons_pyeongtaek_1.jpg", "commons_pyeongtaek_2.jpg"}
PREV = set()
for sid in ("L261107-soxl-38", "L261108-lev-91", "L261107-midterm-ai", "L261108-pepero-day", "L261109-palantir-what"):
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


SP = "뉴욕타임스·FT 보도 인용 (CBS·세계일보 2026-11-09)"
NV = "프리마켓 약 -5.1% (2026-11-09 기준) · 환율 1,355원"
MS = "코튼 상원의원 서한 2025-10-13 · NYT 보도 인용"
FIN = "매수·매도 권유 아님"
M((0,0), ["vstockmarket_47213", "commons_nvidiahq_2", "il_L261107s_chip_crack".replace("il_","")], [PU("약 310조 원", "엔비디아 프리마켓 시가총액 감소", color="red", at=0.25, soft=False, hold=2.0)], src=NV, cold=True, first=True)
M((0,1), ["vbusinessman_231", "vdocuments_24632"], [], src="CBS News 2026-11-09", cold=True)
M((0,2), ["vspy_14090", "vsingapore_20174", "vsingapore_30966"], [LOW("MEGASPEED", "싱가포르 데이터센터 회사", at=0.4)], cold=True)
M((0,3), ["L2611sy_export_boxes", "L261101_warehouse", "server_7863"], [LOW("보도 내용", "미국 상원의원 서한 인용", at=0.1)], src=MS, cold=True)
M((0,4), ["vmoney_47005", "commons_nvidiagpu_2"], [PU("6조 원+", "엔비디아 제품 구매액", color="gold", at=0.15, soft=False, hold=1.8)], src="NYT 보도 인용", cold=True)
M((0,5), ["vhacker_46627", "vsecret_49379", "vsurveillance_23673", "vsecret_50747"], [], src=SP, cold=True)
M((0,6), ["vchina_28611", "chip_47048"], [], cold=True)
M((0,7), ["vsilhouette_33968", "vdetective_32780"], [], cold=True)
M((0,8), ["vanalytics_41277".replace("41277","5462"), "vstockmarket_47214"], [], cold=True)
ident = copy.deepcopy(soxl["scenes"][9]); ident.pop("dur", None); ident["lines"] = [L(1,0)]; ident["en"] = [""]; S.append(ident)
T("확인된 것과 의혹", "")
M((2,0), ["commons_nvidiahq_3", "vmeeting_4809"], [TB(["확인", "의혹"], [["불륜 인정·이사회 조사", "중국 스파이 여부"]], ["green", "red"], at=0.2)], src="CBS News 2026-11-09")
M((2,1), ["vnewspaper_41192", "vchina_13312"], [], src=SP)
M((2,2), ["vdocuments_48385"], [], src="엔비디아 이사회 성명")
M((2,3), ["L261105h_archive"], [P("사태 총정리")])
M((2,4), ["commons_nytbuilding_2", "newspaper_41191_a", "vdocuments_24632".replace("24632","24632") if False else "L261107s_seoul_bed_phone"], [P("10월 29일 · 뉴욕타임스 보도")], src="뉴욕타임스 보도 인용")
M((2,5), ["commons_ustreasury_3"], [P("11월 4일 · 미국 하원 3개 위원회")], src="미국 하원")
M((2,6), ["vnewspaper_41199".replace("41199","41192") if False else "L261105k_cin_phone".replace("L261105k_cin_phone","L261107s_phone_red")], [P("11월 7일 · 파이낸셜타임스 보도")], src="FT 보도 인용")
M((2,7), ["vpresentation_24173", "L2611ss_dc_build".replace("L2611ss_dc_build","vairplane_4368"), "L2611sy_myeongdong_night"], [P("11월 8일 · 불륜 인정 · 이사회 조사")], src="CBS News · 세계일보 2026-11-09")
M((2,8), ["vstockmarket_47214".replace("47214","47213") if False else "commons_nvidiagpu_1".replace("commons_nvidiagpu_1","vnetwork_19653") if False else "vwallstreet_4842"], [P("11월 9일 · 프리마켓 약 -5%")], src=NV)
M((2,9), ["vsingapore_28635"], [])
T("게임 회사가 AI 회사가 됐다", "")
M((3,0), ["vsingapore_30998", "datacenter_23282"], [])
M((3,1), ["laptop_1781", "phone_4915"], [TB(["2015년", "2023년 3월"], [["세븐로드 인터내셔널", "메가스피드"]], ["gray", "gold"], at=0.2)], src="NYT·Reuters 보도 인용")
M((3,2), ["vnetwork_4916", "server_20822"], [])
M((3,3), ["L261107m_dc_plains", "cargo_4011"], [])
M((3,4), ["vdocuments_22856", "vmoney_18261"], [PU("48억 달러", "2024.6~2026.2 구매액 · 약 6조 5천억 원", at=0.5, hold=2.0)], src="NYT 무역 기록 확인")
M((3,5), ["vsingapore_20174".replace("20174","30966") if False else "map_39787"], [])
M((3,6), ["vdetective_49252"], [])
M((3,7), ["L2611ss_night_office", "vsilhouette_1214", "vcapitol_49851"], [LOW("톰 코튼 미국 상원의원", "2025년 10월 상무부 서한", at=0.15)], src=MS)
M((3,8), ["vshanghai_30977"], [], src=MS)
M((3,9), ["server_23215", "cargo_30125"], [], src="NYT 보도 인용")
M((3,10), ["L261107m_cargo_chips", "L261108p_warehouse"], [], src=MS)
M((3,11), ["server_24033", "vcontract_23112"], [], src="엔비디아 입장")
M((3,12), ["vdocuments_24632".replace("24632","48385") if False else "vcontract_23222".replace("23222","28362") if False else "vmeeting_15716".replace("15716","4809") if False else "vcourt_46820".replace("46820","47602") if False else "L261105h_contract".replace("L261105h_contract","L2611ss_night_office") if False else "server_47050"], [], src="메가스피드 입장")
T("국경을 넘지 않는 칩", "")
M((4,0), ["L261105k_cin_cargonight"], [])
M((4,1), ["L261110a_server_aisle", "vnetwork_26778", "vdata_50749"], [TB(["칩", "계산 능력"], [["말레이시아에 있음", "중국 고객이 사용"]], ["gray", "red"], at=0.5)])
M((4,2), ["commons_datacenter_3", "vshanghai_31063"], [], src="NYT 보도 인용")
M((4,3), ["L261107m_dc_cooling", "vdata_14724"], [])
M((4,4), ["vsurveillance_23988"], [])
T("감청 기록에서 나온 이름", "")
M((5,0), ["vsilhouette_34041", "vnews_14044"], [], src=SP)
M((5,1), ["vsurveillance_23016", "vhacker_46634"], [], src=SP)
M((5,2), ["L261109p_file_network", "vsecret_50745", "vhacker_34838"], [], src=SP)
M((5,3), ["vnightcity_40747", "phone_14669"], [], src="세계일보 2026-11-09")
M((5,4), ["vhandshake_46755", "vmoney_45703", "chip_47258"], [], src=MS)
M((5,5), ["vwashington_22787", "vdocuments_39496", "vspy_22997", "vchina_31089"], [LOW("보도 내용", "미국 정부 내부 문서 인용 · 미확인", at=0.1)], src="뉴욕타임스 보도 인용")
M((5,6), ["vconference_23116", "commons_nvidiahq_1"], [], src="엔비디아 입장")
M((5,7), ["vdetective_32782", "vcomputer_308"], [])
T("젠슨 황은 왜 중국에 팔자고 했나", "")
M((6,0), ["vnewspaper_34190", "commons_ustreasury_2", "vwallstreet_24515"], [P("2023년 5월 · 파이낸셜타임스")], src="FT 2023-05")
M((6,1), ["L261105h_contract"], [])
M((6,2), ["vconference_23116".replace("23116","23116") if False else "vpresentation_1" if False else "vmeeting_4809".replace("4809","22961"), "vchina_36314", "chip_47051"], BARS("중국 시장 점유율", [b("이전", 95, "95%", "gray"), b("2025년 5월", 50, "50%", "red")]), src="2025 컴퓨텍스 발언")
M((6,3), ["vwashington_22786", "vcontract_28362", "vsemiconductor_1139", "vsemiconductor_1138"], [TB(["2025년 8월", "2025년 12월"], [["H20 · 매출 15% 납부", "H200 허가"]], ["gold", "gold"], at=0.2)], src="Reuters·NPR 2025")
M((6,4), ["vdetective_32780".replace("32780","49252") if False else "vsilhouette_1214".replace("1214","33968") if False else "vbusinessman_42648"], [])
M((6,5), ["vmoney_18296", "vshanghai_26816"], [IC("dollar", "① 돈", at=0.08), PU("약 27조 원", "직전 회계연도 중국 매출", at=0.5, hold=1.8)], src="엔비디아 연간 실적 (Yahoo Finance 2026-05-04)")
M((6,6), ["vsemiconductor_1140", "L2611ss_china_fab", "vprogramming_41654"], [IC("chip", "② 생태계 논리", at=0.08)], src="엔비디아 10-K")
M((6,7), ["vspy_46639", "L261109p_locked_drive"], [IC("warning", "③ 외부 영향력 · 입증되지 않음", at=0.08, color="red")])
M((6,8), ["vchina_28699"], [])
M((6,9), ["L261110a_bund_night", "commons_nvidiagpu_1", "vchina_13312".replace("13312","28611") if False else "L2611sy_export_boxes".replace("export_boxes","court")], [PU("0", "젠슨 황이 밝힌 중국 내 자사 점유율 · 2026년 4월", color="red", at=0.6, hold=1.8)], src="Yahoo Finance 2026-05-04")
M((6,10), ["vsatellite_47399"], [])
M((6,11), ["vwallstreet_3051".replace("3051","24515") if False else "commons_nvidiahq_2".replace("_2","_1") if False else "chip_47051".replace("47051","47048") if False else "vnightcity_40746"], [])
T("한 사람에게 걸린 회사", "")
M((7,0), ["commons_nvidiahq_2".replace("_2","_3") if False else "vofficebuilding_40652"], [])
M((7,1), ["vstockmarket_47012", "vmoney_18261".replace("18261","47005") if False else "vstockmarket_47016"], [PU("2,310억 달러", "프리마켓 시가총액 감소 · 약 310조 원", color="red", at=0.3, hold=2.0)], src=NV)
M((7,2), ["vbusinessman_8941", "vmeeting_15716"], [])
M((7,3), ["L2611ss_night_office".replace("L2611ss_night_office","vofficebuilding_40701"), "vmeeting_22961".replace("22961","15716") if False else "L261105h_towerman"], [LOW("후계 구도", "공개된 승계 계획 없음", at=0.1)], src="파이낸셜뉴스 2026-11-09")
M((7,4), ["vphonecall_23073", "vdocuments_22856".replace("22856","24632") if False else "vnews_41204"], [], src="Bloomberg 인터뷰(2026-10-29) · 파이낸셜뉴스 인용")
M((7,5), ["vcourt_46820", "vcontract_23222"], [], src="엔비디아 이사회 성명")
M((7,6), ["vwashington_22784"], [], src="세계일보 2026-11-09")
M((7,7), ["vwashington_22788", "vdocuments_45923"], [TB(["회신 기한", "비공개 설명"], [["11월 11일", "11월 18일 요구"]], ["gold", "red"], at=0.25)], src="미국 하원 3개 위원회")
M((7,8), ["vstockmarket_47792"], [])
T("엔비디아 주가 전망", "")
M((8,0), ["L261110a_exchange_night", "vwallstreet_24517"], [PU("19조 7천억 원", "국내 투자자 엔비디아 보관금액 · 11월 5일", at=0.3, hold=1.8)], src="한국예탁결제원 (비즈워치 2026-11-09)")
M((8,1), ["L261107m_storm_tower", "vstockmarket_47213".replace("47213","47016") if False else "vanalytics_41277"], BARS("엔비디아 시가총액 (달러)", [b("10월 고점", 5.8, "5.8조", "gray"), b("11월", 4.5, "약 4.5조", "red")]), src="파이낸셜뉴스 2026-11-09 · 11/6 종가 기준 추정")
M((8,2), ["commons_hbm_1", "chip_47051".replace("47051","47258") if False else "vsemiconductor_1138".replace("1138","1141") if False else "vdata_21053"], [TB(["엔비디아", "AMD·브로드컴·TSMC"], [["약 -5%", "소폭 상승"]], ["red", "green"], at=0.3)], src=NV)
M((8,3), ["server_47050".replace("47050","7863") if False else "L261110a_server_aisle".replace("L261110a_server_aisle","commons_datacenter_1"), "vdata_5404"], BARS("분기 매출 (달러)", [b("직전 분기", 96.2, "962억", "gray"), b("이번 분기 전망", 108, "1,080억", "gold")]), src="엔비디아 2027 회계연도 2분기 실적 (SEC 8-K)")
M((8,4), ["vnews_14044".replace("14044","41204") if False else "vconference_23116".replace("23116","4809") if False else "vmeeting_4809".replace("4809","4809") if False else "vbusinessman_42648".replace("42648","231") if False else "L261110a_midnight_phones"], [], src="FourWeekMBA·비즈워치 2026-11-09")
M((8,5), ["vtyping_41183"], [])
M((8,6), ["vstockmarket_9607"], [IC("up", "① 단기 충격 · 유출 없음 + CEO 유지", at=0.08, color="gold")], src=FIN)
M((8,7), ["vwashington_22787".replace("22787","22786") if False else "vsingapore_30966".replace("30966","30998") if False else "cargo_4011".replace("4011","30125") if False else "containership_30467", "Y261105_a_china"], [IC("globe", "② 규제 확대 · 동남아시아 판매", at=0.08, color="gold")], src=FIN)
M((8,8), ["L261109p_box_exit", "vnewyork_30544"], [IC("warning", "③ CEO 교체 · 기업가치 할인", at=0.08, color="red")], src=FIN)
M((8,9), ["L261107s_dawn_phone"], [])
M((8,10), ["vcapitol_49851".replace("49851","40700") if False else "vwashington_22786".replace("22786","22788") if False else "vdocuments_48385".replace("48385","39496") if False else "vcontract_28362".replace("28362","23112") if False else "L261105k_cin_phone"], [IC("bolt", "11월 11일 · 참석 회신 기한", at=0.08)], src="미국 하원 3개 위원회")
M((8,11), ["vstockmarket_47214".replace("47214","47016") if False else "vanalytics_5462".replace("5462","41277") if False else "L261104g_morning_phone", "L2611ss_dc_build"], [IC("bolt", "11월 18일 아침(한국 시간) · 실적", at=0.08)], src="비즈워치 2026-11-09")
M((8,12), ["vmeeting_22961".replace("22961","4809") if False else "vconference_23116".replace("23116","23116") if False else "vpresentation_0" if False else "L261110a_search_phone"], [], src=FIN)
M((8,13), ["vcourt_47602", "vcourt_46117"], [IC("building", "이사회 조사 결과", at=0.08)], src=FIN)
M((8,14), ["commons_ustreasury_1", "commons_skhynix_1", "vsemiconductor_1141"], [IC("globe", "미국 상무부의 메가스피드 조사", at=0.08)], src=FIN)
M((8,15), ["commons_hbm_2", "vdata_14724".replace("14724","5404") if False else "L261107m_night_worker"], [], src=FIN)
T("", "")
CH_PENDING.pop()
M((9,0), ["vsingapore_28635".replace("28635","30998") if False else "vsatellite_46148", "vnightcity_49878"], [])
M((9,1), ["L261107s_chip_stairs"], [], src=FIN)
S.append({"v": {"type": "end", "sub": "", "btn_at": ["0:좋아요", "0:구독", "0:구독"], "note": {"text": ""}, "closing_photo": resolve("vsatellite_47401"), "backdrop": resolve("commons_datacenter_2"), "bd_dim": 0.74},
    "lines": [L(9,2)], "endscreen": 8, "sketch_add": [], "en": [""], "asof": False, "src": ""})
TITLE = "엔비디아 젠슨 황 불륜 사태 총정리, 프리장 310조 증발과 주가 전망"
spec = {k: base[k] for k in ["fx", "format", "world", "notebook", "hook", "overlay"]}
spec["look"] = {"paper": "blueprint", "dark": "ink", "accent": "sky"}
spec["music"] = copy.deepcopy(base["music"]); spec["music"].pop("bed_eq", None)
spec["music"].update(bed=["social/music/samples3/H6_full.mp3@30", "social/music/samples3/H1_full.mp3@30"], bed_gain_db=3, bed_hp=120, note="본편 H6 House - July → H1 Deep House Sunset · 120Hz 아래 차단 (대표 11/9)")
spec.update({"id": "L261109-nvidia-huang", "company": "NVDA", "no_data": True, "series": "긴급", "scheduled_at": "2026-11-09T21:00:00+09:00",
 "events": [{"at": "2026-11-09T18:43:00+09:00", "by": "owner", "what": "채팅 지시 — 엔비디아 긴급 롱폼, 빨리 렌더. 남들이 모르는 싱가포르 회사·중국 개방론 중심 훅·리훅"}],
 "opening": "미스터리형 — 310조 증발 → 불륜이 아니라 싱가포르 회사 → 상자째 칩 → 감청 기록 → 중국 개방론의 이유", "hook_type": "미스터리 훅 + 리훅",
 "endscreen_target": "L261107-soxl-38", "title": TITLE, "doc_title": "젠슨 황 사건은 어디서 시작됐나", "title_en": "Nvidia stock outlook: the Jensen Huang scandal began with a Singapore company",
 "tags": ["엔비디아 사태 총정리", "젠슨 황 불륜", "엔비디아 주가 전망", "엔비디아 주가", "엔비디아", "젠슨 황", "메가스피드", "엔비디아 이사회 조사", "엔비디아 실적", "NVDA", "미국 주식", "서학개미", "AI 칩", "대중국 수출 규제"],
 "search_keywords": ["엔비디아 주가 전망", "엔비디아 주가", "젠슨 황", "엔비디아", "NVDA"],
 "sources": ["CBS News 2026-11-09 (젠슨 황 성명·이사회 독립 조사·메가스피드 48억 달러)", "세계일보 2026-11-09 (NYT·FT 보도: 감청·이름 공개·내부 문서·타이베이 사진·트럼프 발언)", "FourWeekMBA 2026-11-09 (프리마켓 -5.1%, 약 2,310억 달러) · 환율 1,355원", "톰 코튼 상원의원 보도자료·서한 2025-10-13/14", "TechFlow 칼럼이 인용한 NYT·Reuters 보도 (세븐로드 2015 등록, 2023-03 사명 변경, 2024-06 구매 시작, 인스퍼 관련 납품, 말레이시아·인도네시아 데이터센터)", "뉴스스페이스 2026-11 (엔비디아·메가스피드 입장, 중국 외교부 반박)", "Yahoo Finance 2026-05-04 (점유율 0 발언, 중국 매출 196.7억 달러, 10-K 경고) · FT 2023-05 (CGTN·SupplyChainBrain 인용) · Reuters·NPR 2025 (H20 15%)", "미국 하원 3개 위원회 비공개 설명 요구 (2026-11-04, 11/18·회신 11/11)", "사진: Wikimedia Commons · 영상: Mixkit·Pexels · 음악: Pixabay"],
 "pinned_comment": "젠슨 황의 중국 개방론, 여러분은 돈·논리·외부 영향력 중 무엇이라고 보시나요? 댓글로 나눠 주세요.\n※ 스파이 관련 내용은 보도된 의혹이며 사실로 확인되지 않았습니다. 2026년 11월 9일 프리마켓 기준이며 매수·매도 권유가 아닙니다.\n좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다.",
 "description_head": "엔비디아 주가 전망이 궁금하신 분들을 위해 정리했습니다.\n\n엔비디아는 11월 9일 프리마켓에서 약 5% 내렸습니다. 젠슨 황은 불륜을 인정했고 이사회는 독립 조사를 시작했습니다. 상대 여성이 중국 스파이라는 내용은 미국 언론이 보도한 의혹이며 확인되지 않았습니다. 이 사건의 출발점인 싱가포르 회사 메가스피드, 젠슨 황의 중국 개방론, 주주가 앞으로 볼 3가지를 다룹니다.",
 "description_en": "Nvidia fell about 5% premarket after CEO Jensen Huang admitted an affair and the board opened an independent probe. Espionage claims remain unverified reporting. We trace Megaspeed, Huang's China stance and what shareholders should watch.",
 "hook_promises": ["싱가포르 회사의 정체", "중국 개방론의 이유", "주주가 볼 것 3가지"], "viewer_question": "젠슨 황 사건은 어디서 시작됐고 주주에게 얼마나 큰 문제인가",
 "format_note": "11/9 긴급. 스파이는 의혹으로만, 상대 여성 이름·사진 없음, 실존 인물 사진 없음.",
 "thumb": {"photo": "il_L261107s_chip_crack.jpeg", "focus_x": 0.5, "l1": "엔비디아 젠슨 황 불륜 사태", "l2": "총정리", "pos": "left", "s1": 60, "s2": 110},
 "ab_sets": [{"key": "a", "default": True, "title": TITLE, "file": "thumb_a.jpg", "type": "A 불륜 사태 총정리"}, {"key": "b", "title": TITLE, "file": "thumb_b.jpg", "type": "B 310조"}, {"key": "c", "title": TITLE, "file": "thumb_c.jpg", "type": "C 중국 개방론"}],
 "scenes": S})
EXTRA = {"이사회도 국가": ["vnewspaper_41199"], "메가스피드도 외부": ["vhandshake_30016"], "누군가 정말": ["L261110a_conveyor_night"], "그럼 주주에게": ["vstockmarket_47213".replace("47213","47016") if False else "vnetwork_31536"], "엔비디아는 1993": ["vofficebuilding_31663"],
 "엔비디아에는 공개": ["vmeeting_4809".replace("4809","22961") if False else "vhandshake_24047"], "신뢰 문제도": ["vnetwork_19653"], "이제 주가 전망": ["vnewyork_4442"], "엔비디아 시가총액은": ["vnewyork_33965"], "같은 프리마켓": ["vsemiconductor_1138".replace("1138","1140") if False else "Y261105_a_server"], "사업 숫자는": ["vairplane_4204"],
 "그래서 대중국": ["vcontract_23222".replace("23222","28362") if False else "L261110a_search_phone".replace("search_phone","midnight_phones") if False else "commons_datacenter_4", "vdocuments_39496".replace("39496","22856") if False else "vmoney_47005".replace("47005","18296") if False else "L2611ss_china_fab".replace("L2611ss_china_fab","vanalytics_5462") if False else "vairplane_28000"],
 "첫째는 단기": ["vstockmarket_47792".replace("47792","47213") if False else "vnewyork_26920"], "둘째는 규제": ["vairplane_7025"], "11월 11일은": ["vcomputer_46635"], "한국 시간": ["vstockmarket_47213".replace("47213","47012") if False else "vmoney_18261".replace("18261","45703") if False else "vanalytics_5462".replace("5462","41277") if False else "L261105h_parisnight".replace("L261105h_parisnight","L2611sy_court") if False else "commons_nvidiahq_3".replace("_3","_2") if False else "commons_datacenter_2".replace("_2","_3") if False else "vpresentation_1" if False else "L261107m_subway_phone"], "실적 설명회": ["vpresentation_24068"], "정리하면": ["vsatellite_45033"], "아직 확인되지": ["vsatellite_47401".replace("47401","46148") if False else "space_18772"]}
for s_ in spec["scenes"]:
    for k_, ex_ in EXTRA.items():
        if s_.get("lines") and s_["lines"][0].startswith(k_) and "cuts" in s_["v"]:
            s_["v"]["cuts"] += [{"lib": resolve(c_)} for c_ in ex_]
for s_ in spec["scenes"]:
    if s_["v"].get("cine"):
        for e_ in s_.get("sketch") or []:
            if e_.get("kind") == "lower": e_["y"] = 540
out = os.path.join(OUT_DIR, "L261109-nvidia-huang.json")
json.dump(spec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
spoken = [x for sc in S for x in sc.get("lines", [])]; expected = [x for c, l in SCRIPT for x in l]
assert " ".join(spoken) == " ".join(expected), "불일치"
tot = sum(syl(t) for t in spoken); nums = sum(len(re.findall(r"[0-9][0-9,.]*", t)) for t in spoken)
print("scenes", len(S), "syl", tot, "est", round(tot/6.1), "숫자", nums, "cuts", sum(r[1] for r in REPORT))
print("긴 컷:", [r for r in REPORT if r[2] > 4.6])
print("반복:", sorted({w[1] for w in WARN if w[0]=="반복"}))
print("직전 겹침:", len({w[1] for w in WARN if w[0]!="반복"}))
