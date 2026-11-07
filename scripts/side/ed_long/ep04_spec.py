"""EPISODE 4 렌더 설정 — 3편 틀(spec_ep03: 인트로·목소리 크기·엔딩·끝에 모은 할 일)을 물려받고, 11/7 분석을 반영해 장 구성을 바꾼다
python3 ep04.py spec → scripts/side/ed_long/spec_ep04.json

11/7 대표 "위 분석 전부 반영":
- 7장 → 5장. 장 카드 = 번호 매듭(로마 숫자 + "첫 번째 방법 · …")
- 장 순서: 카드 → 현대 장면 1번(질문) → 로마 이야기 → 독백·구절 → 해설(개념 카드) → 강한 한 줄 + 여운 장면 → 다음 장 예고
  (현대 장면은 장 앞에만, 이야기 도중 핑퐁 없음)
- 훅의 '그날 밤'을 마지막 '닫기'에서 같은 독백으로 닫는다
- 3편 v4 피드백 유지: 입 움직이는 영상은 그 사람이 말할 때만, 책에 손 얹는 장면 천천히, 일곱(→다섯) 문장·할 일은 빠르게
"""
import json, os, copy, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ep04 as E
import ep01_spec as F
import library as L
from ep02_spec import ELEC, subs_of as _subs
from ep03_spec import auto_faces

TENT = ["fire_4.mp3", 0.38]; TENT2 = ["fire_0.mp3", 0.3]; CAMP = ["wind_2.mp3", 0.4]; CITY = ["night_2.mp3", 0.25]; FORUM = ["wind_1.mp3", 0.3]
FIRE = ["fire_2.mp3", 0.4]; SNOW = ["wind_6.mp3", 0.35]
ORD = {1: "FIRST", 2: "SECOND", 3: "THIRD", 4: "FOURTH", 5: "FIFTH"}; NUM = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
KO = {1: "첫 번째 방법", 2: "두 번째 방법", 3: "세 번째 방법", 4: "네 번째 방법", 5: "다섯 번째 방법"}


def subs_of(t, v):
    return _subs(t, v if v in (E.G, E.M) else "CAST")


def mod(src, vs):   # 현대 장면 — 녹아들듯, 짧은 여백
    s = F.shot("still", src, vs, CITY, {"grade": "modern", "move": {"zoom": [1.0, 1.07], "pan": [[0.01, 0], [-0.01, 0]]}})
    s.update({"tin": "dissolve", "pre": 0.3, "post": 0.4}); return s


# 11/8 대표: "현실이 몇 초 한 컷으로 지나가 로마와 겹쳐 헷갈린다" →
#  ① 현대 장면 2컷(상황 → 속마음), ② 들어갈 때 '지금 · …', 로마로 돌아올 때 '다시 · …' 시간·장소 자막,
#  ③ 로마로 돌아오는 순간 짧은 암전 + 책장 소리(전환음은 책장 소리만 — 11/4 규칙)
NOW = {1: "지금 · 어느 늦은 밤", 2: "지금 · 남편이 떠난 집", 3: "지금 · 강아지가 떠난 저녁", 4: "지금 · 출근길", 5: "지금 · 엄마가 떠난 뒤"}
BACK = {1: "다시, 그날 밤 · 할랄라의 막사", 2: "다음 날 아침 · 로마에서 온 편지", 3: "며칠 뒤 · 마을 밖 언덕", 4: "장례 다음 날 새벽 · 할랄라", 5: "몇 달 뒤 · 파우스티노폴리스"}


def lib(name, vs=None, **ex):
    return L.lib_shot(name, voices=vs, extra=(ex or None))


CH4 = {
 1: dict(title="사실에 이야기를 덧붙이지 마라", en="Say no more than first appearances report",
        q=[mod("e4m_call", ["d1q"]), mod("e4m_funeral", ["d1q2"])],
        scene=[F.shot("still", "e4_alone", ["d1a"], TENT, {"flicker": True, "move": {"zoom": [1.0, 1.1]}}),
               F.shot("still", "e4_alone", ["d1b"], TENT, {"flicker": True, "gap": 0.5, "move": {"zoom": [1.22, 1.34], "pan": [[0.0, -0.02], [0.01, -0.03]]}}),
               lib("candle_diary", ["d1c"], pre=0.3, post=0.4)],
        mono="quill2", mvoices=["m1a", "m1b", "m1c"], verse=["처음 보이는 것 이상을,", "스스로에게 말하지 마라."], src="명상록 8권 49절",
        interp=[F.shot("still", "e4_alone", ["d1d"], TENT2, {"flicker": True, "move": {"zoom": [1.1, 1.2]}})],
        concept=("d1d", "스토아 철학 · 첫인상", "사실에 이야기를 덧붙이지 마라", "Say no more than first appearances report"),
        knot=lib("tent_stars", ["d1e"], pre=0.6, post=1.6),
        teaser=F.shot("still", "e4_rumor", ["d1t"], CITY, {"move": {"zoom": [1.0, 1.08]}})),
 2: dict(title="잃은 것 말고, 받은 것을 세어라", en="Count what was given",
        q=[mod("e4m_house", ["d2q"]), mod("e4m_family", ["d2q2"])],
        scene=[F.shot("still", "e4_rumor", ["d2a", "r_sen"], CITY, {"gap": 0.5, "flicker": True, "move": {"zoom": [1.08, 1.2]}}),
               lib("letter_open", ["d2b"], pre=0.3, post=0.5)],
        mono="candle_face", mvoices=["m2a", "m2b", "m2c"], verse=["그토록 다정하고 꾸밈없는 아내를,", "만난 것에 감사한다."], src="명상록 1권 17절",
        interp=[F.shot("still", "e4_wedding", ["d2c"], ["wind_1.mp3", 0.2], {"grade": "memory", "leak": True, "move": {"zoom": [1.0, 1.12]}})],
        concept=("d2c", "스토아 철학 · 감사", "잃은 것 말고, 받은 것을 세어라", "Count what was given"),
        knot=F.shot("still", "e4_faustina", ["d2d"], ["wind_1.mp3", 0.2], {"grade": "memory", "leak": True, "pre": 0.6, "post": 1.6, "move": {"zoom": [1.0, 1.1]}}),
        teaser=lib("pyre_far", ["d2t"], pre=0.3, post=1.2)),
 3: dict(title="잃음은 끝이 아니라, 변화다", en="Loss is nothing but change",
        q=[mod("e4m_dog", ["d3q"]), mod("e4m_walk", ["d3q2"])],
        scene=[F.shot("still", "e4_pyre", ["d3a"], FIRE, {"particles": "embers", "move": {"zoom": [1.0, 1.1]}}),
               F.shot("still", "e4_children", ["d3b"], ["wind_1.mp3", 0.2], {"grade": "memory", "leak": True, "move": {"zoom": [1.0, 1.1]}})],
        mono="quill2", mvoices=["m3a", "m3b", "m3c"], verse=["잃는다는 것은,", "변한다는 것일 뿐이다."], src="명상록 9권 35절",
        interp=[lib("autumn_leaves", ["d3c"], pre=0.3, post=0.5)],
        concept=("d3c", "스토아 철학 · 자연의 순환", "잃음은 끝이 아니라 변화", "Loss is nothing but change"),
        knot=lib("river_flow", ["d3d"], pre=0.6, post=1.6),
        teaser=lib("dawn_camp", ["d3t"], pre=0.3, post=1.2)),
 4: dict(title="슬픔을 안고, 오늘의 일로", en="I rise to do the work of a human being",
        q=[mod("e4m_bus", ["d4q"]), mod("e4m_shirt", ["d4q2"])],
        scene=[F.shot("still", "e4_dawn", ["d4a"], SNOW, {"move": {"zoom": [1.0, 1.1]}}),
               F.shot("still", "e4_city", ["d4b"], FORUM, {"move": {"zoom": [1.0, 1.1]}})],
        mono="candle_face", mvoices=["m4a", "m4b", "m4c"], verse=["나는, 사람의 일을 하러", "일어난다."], src="명상록 5권 1절",
        interp=[F.shot("still", "e4_dawn", ["d4c"], SNOW, {"move": {"zoom": [1.2, 1.32], "pan": [[0.0, -0.02], [0.02, -0.02]]}})],
        concept=("d4c", "스토아 철학 · 의무", "슬픔을 안고, 오늘의 일로", "I rise to do the work of a human being"),
        knot=lib("sunrise_hills", ["d4d"], pre=0.6, post=1.6),
        teaser=lib("rain_march", ["d4t"], pre=0.3, post=1.2)),
 5: dict(title="그리움을, 좋은 일로 바꿔라", en="From one kind act to another",
        q=[mod("e4m_mom", ["d5q"]), mod("e4m_mom", ["d5q2"]) | {"tin": "cut", "move": {"zoom": [1.18, 1.28], "pan": [[0.0, -0.01], [0.01, -0.02]]}}],   # 둘째 컷도 현대(아치 창문 그림은 로마로 보여 헷갈림)
        scene=[F.shot("still", "e4_halala", ["d5a"], SNOW, {"move": {"zoom": [1.12, 1.24]}}),
               F.shot("still", "e4_girls", ["d5b"], ["wind_1.mp3", 0.2], {"grade": "memory", "move": {"zoom": [1.0, 1.1]}})],
        mono="quill2", mvoices=["m5a", "m5b", "m5c"], verse=["남을 위한 일에서 다음 일로,", "거기서 기쁨을 찾아라."], src="명상록 6권 7절",
        interp=[F.shot("still", "e4_girls", ["d5c"], ["wind_1.mp3", 0.2], {"grade": "memory", "move": {"zoom": [1.2, 1.32]}})],
        concept=("d5c", "스토아 철학 · 공동체를 위한 행위", "그리움을, 좋은 일로", "From one kind act to another"),
        knot=mod("e4m_letter", ["d5d"]) | {"pre": 0.6, "post": 1.6},
        teaser=None),
}
PICK = {'d1q': 'voice_ep04b_01_d1qa.mp3', 'd1q2': 'voice_ep04b_04_d1q2b.mp3', 'd2q2': 'voice_ep04b_06_d2q2b.mp3', 'd3q2': 'voice_ep04b_07_d3q2a.mp3', 'd4q2': 'voice_ep04b_10_d4q2b.mp3', 'd5q': 'voice_ep04b_11_d5qa.mp3', 'd5q2': 'voice_ep04b_14_d5q2b.mp3'}   # 11/8 2테이크 중 짧은(끌림 없는) 쪽
MUSIC4 = {1: ("sad_3.mp3", 0), 2: ("cinematic_5.mp3", 0), 3: ("sad_3.mp3", 60), 4: ("cinematic_4.mp3", 0), 5: ("cinematic_4.mp3", 110)}


def chapter4(n, c):
    S = [{"type": "card", "label": f"THE {ORD[n]} WAY", "num": NUM[n], "title": f"{KO[n]} · {c['title']}", "en": c["en"], "dur": 4.2, "fixed": True,
          "sfx": F.CARD_SFX, "amb": ["wind_2.mp3", 0.25]}]
    q = copy.deepcopy(c["q"])
    q[0].setdefault("overlays", []).append({"kind": "caption", "text": NOW[n], "at": 0.3, "pos": "top", "size": 44})
    q[-1].update({"post": 0.6})
    S += q
    sc = copy.deepcopy(c["scene"])
    sc[0].setdefault("overlays", []).insert(0, {"kind": "caption", "text": BACK[n], "at": 0.3, "pos": "top", "size": 44})
    sc[0].update({"tin": "black", "fin": 0.5, "pre": max(sc[0].get("pre", 0.3), 0.5)})
    sc[0]["sfx"] = (sc[0].get("sfx") or []) + [["paper_3.mp3", 0.05, 0.45]]
    S += sc
    m = lib(c["mono"], c["mvoices"])
    m.update({"gap": 1.0, "pre": 0.8, "post": 1.8, "nocap_voices": [c["mvoices"][-1]], "tin": "dissolve"})
    m["overlays"] = [{"kind": "verse", "lines": c["verse"], "src": c["src"], "at_voice": c["mvoices"][-1]}]
    S.append(m)
    cv, kick, line, en = c["concept"]
    for s in copy.deepcopy(c["interp"]):
        if cv in (s.get("voice") or []): s["overlays"] = [{"kind": "concept", "kicker": kick, "lines": [line], "en": en, "at_voice": cv, "offset": 0.4, "len": 5.0}]
        S.append(s)
    k = copy.deepcopy(c["knot"]); k["tin"] = "dissolve"; S.append(k)   # 강한 한 줄 + 여운 — 장의 매듭
    if c["teaser"]:
        t = copy.deepcopy(c["teaser"]); t.update({"tout": "black", "fout": 0.8}); S.append(t)
    else:
        S[-1].update({"tout": "black", "fout": 0.8})
    return S


def build():
    base = json.load(open(os.path.join(HERE, "spec_ep03.json")))
    sp = {k: copy.deepcopy(base[k]) for k in ("root", "gen_dir", "sfx_dir", "music_dir", "out_dir", "intro", "monologue_fx", "voice_gain")}
    sp["id"] = "edl_ep04"; sp["voice_dir"] = f"social/side/voice_samples/{E.TAG}"
    d = os.path.join(E.ROOT, sp["voice_dir"]); vf = {}
    for n in (sorted(os.listdir(d)) if os.path.isdir(d) else []):
        if n.endswith(".mp3"): vf[n[:-4].split("_", 3)[-1]] = n
    vf["m_x1"] = "../lp3/voice_lp3_07_m_x1.mp3"; vf["e_x2"] = "../ep01x/voice_ep01x_01_e_x2.mp3"   # 슬로건·황제의 일기 (매 편 같은 녹음)
    # 11/7 소리 끌림 검사(take_check)로 다시 받은 줄 — 통과한 테이크로 바꾼다 (d5b는 세 테이크 모두 첫 말 '그리고'를 0.7초 늘여 읽음: 가장 짧은 a)
    for k, f in {"d3a": "voice_ep04r_01_d3aa.mp3", "d3c": "voice_ep04r_03_d3ca.mp3", "d4c": "voice_ep04r_05_d4ca.mp3",
                 "d4t": "voice_ep04r_08_d4tb.mp3", "d5b": "voice_ep04r_09_d5ba.mp3"}.items(): vf[k] = "../ep04r/" + f
    # 11/8 수정분(ep04b) — 2테이크 중 검사 통과한 것 (PICK에서 고름)
    for k, f in PICK.items(): vf[k] = "../ep04b/" + f
    sp["voice_files"] = vf
    ALL = E.HOOK + E.LINES
    sp["subs"] = {n: subs_of(t, v) for n, v, t in ALL}
    sp["monologue_voices"] = [n for n, v, t in ALL if v == E.M] + ["m_x1"]
    S = []
    # 훅 — 할랄라의 밤 → 시녀의 전갈(말할 때만 영상) → 막사에 혼자 → 독백
    S.append({"type": "black", "dur": 0.8, "fixed": True, "amb": ["wind_6.mp3", 0.4]})
    S.append({"type": "still", "src": "e4_halala", "voice": ["h1"], "pre": 0.4, "post": 0.4, "move": {"zoom": [1.0, 1.1]}, "tin": "black", "fin": 0.8,
              "amb": ["wind_6.mp3", 0.4], "overlays": [{"kind": "caption", "text": "기원후 175년 겨울 · 카파도키아, 할랄라", "at": 0.3, "pos": "top"}]})
    S.append({"type": "still", "src": "e4_maid", "voice": ["h_maid"], "pre": 0.4, "post": 0.6, "move": {"zoom": [1.0, 1.08]}, "flicker": True, "amb": TENT,
              "sfx": [["heartbeat_5.mp3", 0.0, 0.5]]})
    S.append({"type": "still", "src": "e4_alone", "voice": ["h2"], "pre": 0.3, "post": 0.4, "move": {"zoom": [1.0, 1.12]}, "flicker": True, "amb": TENT})
    hm = lib("candle_face", ["m_h1", "m_h2"])
    hm.update({"pre": 0.5, "gap": 1.0, "post": 0.9, "tin": "dissolve", "tout": "black", "fout": 1.0,
               "sfx": [["heartbeat_5.mp3", 0.1, 0.9], ["heartbeat_5.mp3", 0.9, 0.6], ["heartbeat_5.mp3", 1.7, 0.35]]})
    S.append(hm)
    S.append({"type": "black", "dur": 0.4, "fixed": True})
    S.append(copy.deepcopy([s for s in base["shots"] if s["type"] == "intro"][0]))
    S.append({"type": "episode", "num": 4, "title": "아내를 잃은 밤", "en": "The Night He Lost Her", "dur": 4.6, "fixed": True,
              "amb": ["wind_2.mp3", 0.3], "sfx": [["drum_6.mp3", 0.3, 0.45]], "tout": "black", "fout": 0.8})
    # 상황 — 몇 달 전 (회상은 이 한 번)
    S.append(F.shot("still", "lp11_rider", ["s1"], ["wind_6.mp3", 0.3], {"tin": "black", "fin": 0.8, "move": {"zoom": [1.0, 1.1]},
                    "overlays": [{"kind": "caption", "text": "몇 달 전 · 기원후 175년 봄", "at": 0.3, "pos": "top"}]}))
    S.append(F.shot("video", "lpv02_messenger", ["s2"], TENT2, {"move": {"zoom": [1.0, 1.06]}}))
    S.append(F.shot("still", "e4_march", ["s3"], ["wind_1.mp3", 0.3], {"move": {"zoom": [1.0, 1.12], "pan": [[0.02, 0], [-0.02, 0]]}}))
    s4 = F.shot("still", "e4_halala", ["s4"], SNOW, {"move": {"zoom": [1.1, 1.2]}}); s4.update({"tout": "black", "fout": 0.8, "post": 1.4}); S.append(s4)
    for n in range(1, 6): S += chapter4(n, CH4[n])
    # 닫기 — 훅의 '그날 밤'으로 돌아가 같은 독백으로 닫는다
    S.append(F.shot("still", "e4_alone", ["c1"], TENT2, {"tin": "black", "fin": 0.8, "flicker": True, "move": {"zoom": [1.3, 1.0]}, "post": 0.6}))
    cl = lib("emp_ridge", ["m_c1"]); cl.update({"pre": 0.6, "post": 2.0, "tin": "dissolve", "tout": "black", "fout": 1.2}); S.append(cl)
    S.append({"type": "recap", "items": ["사실에 이야기를 덧붙이지 마라", "잃은 것 말고, 받은 것을 세어라", "잃음은 끝이 아니라, 변화다", "슬픔을 안고, 오늘의 일로", "그리움을, 좋은 일로 바꿔라"],
              "voice": ["r1"], "pre": 0.8, "post": 2.2, "cascade": [1.3, 0.5], "nocap": True, "head": "소중한 사람을 잃었을 때 · 다섯 가지 방법",
              "head_en": "FIVE WAYS THROUGH LOSS", "sfx": [["paper_3.mp3", 0.2, 0.45]], "tin": "black", "fin": 1.0})
    S.append(lib("candle_diary", ["t0"], pre=0.5, post=0.4, tin="dissolve"))
    S.append({"type": "recap", "items": ["떠난 사람에게 받은 것, 세 가지 적기", "내일 아침 할 작은 일, 하나 정해 두기", "그 사람 이름으로 할 좋은 일, 하나 떠올리기"],
              "dur": 6.2, "fixed": True, "cascade": [0.5, 0.8], "nocap": True, "amb": ["wind_2.mp3", 0.22],
              "head": "오늘 밤, 이 세 가지만", "head_en": "THREE THINGS FOR TONIGHT", "sfx": [["paper_3.mp3", 0.2, 0.45]], "tin": "dissolve", "fin": 0.8})
    S.append(F.shot("still", "e4_faustina", ["r9"], ["wind_2.mp3", 0.25], {"grade": "memory", "leak": True, "move": {"zoom": [1.12, 1.0]}, "post": 1.6, "tin": "dissolve"}))
    S.append({"type": "finale", "dur": 20.0, "voice": ["m_x1", "e_x2", "o1", "o2"], "pre": 0.8, "gap": 0.8, "post": 1.0, "nocap": True, "tin": "black",
              "slogan": "매일 밤, 황제처럼 생각하라", "prev_kicker": "이전 이야기  ·  EPISODE 3", "amb": ["wind_2.mp3", 0.15], "sfx": [["click_2.mp3", 0, 0.0]]})
    # 그림의 첫 등장은 영상으로 (있을 때), 말하는 사람 영상은 그 사람이 말할 때만
    VID = {src: k for k, (src, _) in E.VIDEOS.items()}
    SPEAK = {"h_maid": "ev4_maid", "r_sen": "ev4_rumor"}
    TALKERS = {"ev4_maid", "ev4_rumor"}
    have = lambda k: os.path.exists(os.path.join(E.ROOT, "social/side/gen", k + ".mp4"))
    seen = set(); S2 = []
    for x in S:
        src = x.get("src"); vs = x.get("voice") or []; vs = [vs] if isinstance(vs, str) else vs
        if x.get("type") == "still" and any(v in SPEAK and SPEAK[v] == VID.get(src) for v in vs) and have(VID[src]):
            seen.add(src); segs = []
            for v in vs:
                kind = "video" if (v in SPEAK and SPEAK[v] == VID.get(src)) else "still"
                if segs and segs[-1][0] == kind: segs[-1][1].append(v)
                else: segs.append((kind, [v]))
            for j, (kind, vv) in enumerate(segs):
                c = copy.deepcopy(x); c["voice"] = vv; c.pop("overlays", None) if j else None
                if j: c["tin"] = "dissolve" if kind == "still" else "cut"; c["pre"] = 0.15
                if j < len(segs) - 1: c["post"] = 0.15
                if kind == "video": c.update({"type": "video", "src": VID[src], "move": {"zoom": [1.04, 1.1], "loop": True}})
                S2.append(c)
            continue
        if x.get("type") == "still" and src in VID and VID[src] in TALKERS: S2.append(x); continue
        if x.get("type") == "still" and src in VID and src not in seen and have(VID[src]):
            seen.add(src); v = copy.deepcopy(x); v["type"] = "video"; v["src"] = VID[src]; v.pop("rack", None); S2.append(v)
        else:
            if src in VID: seen.add(src)
            S2.append(x)
    S[:] = S2
    for x in S:
        if x.get("lib") == "close_diary" and x.get("breath"): x.update({"dur": 4.4, "tout": "black", "fout": 1.9})
    cards = [i for i, x in enumerate(S) if x.get("type") == "card"]; card = {n + 1: i for n, i in enumerate(cards)}
    rec = [i for i, x in enumerate(S) if x.get("type") == "recap"][0]; out = [i for i, x in enumerate(S) if x.get("type") == "finale"][0]
    sit = [i for i, x in enumerate(S) if x.get("type") == "episode"][0] + 1
    clo = [i for i, x in enumerate(S) if x.get("voice") == ["c1"]][0]
    faces = auto_faces({x.get("src") for x in S if x.get("src") and x["type"] in ("still", "video")})
    for x in S:
        if x.get("src") in faces: x["face"] = faces[x["src"]]
        if x.get("type") != "intro" and x.get("sfx"):
            x["sfx"] = [["paper_3.mp3", f[1], max(f[2], 0.4)] if f[0] == "paper_2.mp3" else f for f in x["sfx"] if f[0] not in ELEC]
        if x.get("src") not in ("lwv3_side", "lwv2_front", "libv_quill", "libv_quill2", "libv_candle_face") and x.get("sfx"): x["sfx"] = [f for f in x["sfx"] if f[0] != "paper_6.mp3"]
    mus = [{"file": "cinematic_0.mp3", "at_shot": sit, "offset": 0.5, "start": 0, "until_shot": card[1], "vol": 0.22, "fin": 3, "fout": 3}]
    for n in range(1, 6):
        f, st = MUSIC4[n]; nxt = card[n + 1] if n < 5 else clo
        mus.append({"file": f, "at_shot": card[n], "offset": 1.0, "start": st, "until_shot": nxt, "vol": 0.2, "fin": 3, "fout": 3})
    mus.append({"file": "sad_5.mp3", "at_shot": clo, "offset": 0.5, "start": 0, "until_shot": out + 2, "tail": 0, "vol": 0.28, "fin": 2, "fout": 4})
    sp["music"] = mus
    sp["shots"] = S
    sp["cast_voices"] = [n for n, v, t in ALL if v not in (E.G, E.M)]
    json.dump(sp, open(os.path.join(HERE, "spec_ep04.json"), "w"), ensure_ascii=False, indent=1)
    print("장면", len(S), "목소리", len(vf), "카드", card, "얼굴", len(faces))
