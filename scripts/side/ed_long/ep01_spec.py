"""EPISODE 1 렌더 설정 만들기 — 파일럿 앞부분(훅·인트로·오프닝·1장)을 이어받고 2~7장, 정리, 아웃트로를 붙인다 (2026-11-03)
python3 ep01.py spec → scripts/side/ed_long/spec_ep01.json
"""
import copy, json, os, re
import ep01 as E

HERE = os.path.dirname(os.path.abspath(__file__))
NUM = ["", "I", "II", "III", "IV", "V", "VI", "VII"]
ORD = ["", "FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH", "SIXTH", "SEVENTH"]
TENT = ["fire_4.mp3", 0.38]; TENT2 = ["fire_0.mp3", 0.3]; CAMP = ["wind_2.mp3", 0.4]; CITY = ["rain_0.mp3", 0.2]; NIGHT = ["night_6.mp3", 0.18]
CARD_SFX = [["paper_2.mp3", 0.25, 0.4], ["ring_synth.wav", 0.35, 0.12]]   # 11/4 대표: 일곱 문장 카드는 무게감 덜한 잔잔한 소리(책장 넘김 + 작은 종)
# 11/4 대표: 비스듬한 종이(lqv08c) 펜 장면은 종이 한 장 가득 원근에 맞춘 필기체를 미리 입혀 두고 펜은 쓰는 척만
PAGE = {"tip0": [1025, 510], "lead": 30, "clean": True, "ink": [40, 26, 14], "paper_lv": [72, 98], "strength": 0.82, "paper": [[290, 330], [1080, 170], [1720, 770], [710, 1060]], "page": {"corners": [[290, 330], [1080, 170], [1720, 770], [710, 1060]], "paper": [1000, 1150], "u0": 120, "u1": 930, "v0": 80, "pen_v": 640, "last_u": 640, "lines": 6, "text": "Do not waste the remainder of thy life in thoughts about others, when thou dost not refer thy thoughts to some object of common utility. For thou losest the opportunity of doing something else when thou hast such thoughts as these, what is such a person doing, and why, and what is he saying, and what is he thinking of, and what is he contriving, and whatever else of the kind makes us wander away from the observation of our own ruling power."}}
WQ = {"tip0": [1025, 510], "lead": 715, "static": True, "clean": True, "size": 150, "ink": [40, 26, 14], "paper_lv": [72, 98],
      "paper": [[330, 240], [1560, 215], [1720, 1000], [300, 1000]]}


def subs_of(name):
    t = E.TXT[name]; emph = t.startswith("!"); t = t.lstrip("!")
    parts = [x for x in re.split(r"(?<=[.?!])\s+", t) if x]
    return [("!" + x if emph else x) for x in parts] if len(parts) > 1 else ("!" + t if emph else t)


def write(lines, quad):
    w = dict(WQ); w.update({"lines": lines[:-1], "line": lines[-1], "quad": quad}); return w


Q2 = [[600, 236], [1430, 222], [1430, 512], [600, 526]]
Q3 = [[620, 215], [1420, 200], [1420, 520], [620, 534]]

CH = {
 2: dict(title="남의 잘못은 그 사람의 몫이다", en="Leave the wrong where it was done",
        scene=[("video", "ev_generals", ["d2a", "d2b"], TENT, {"sfx": [["impact_6.mp3", 4.0, 0.35]]}), ("still", "e2a_generals", ["d2c"], TENT, {"move": {"zoom": [1.05, 1.25], "pan": [[0, 0], [0.18, 0.02]]}})],
        mono=("still", "e2a_generals", {"move": {"zoom": [1.3, 1.42], "pan": [[0.2, 0.03], [0.22, 0.03]]}, "flicker": True}),
        mvoices=["m2a", "m2b", "m2c"], verse=["남의 잘못은,", "그것이 생긴 자리에 두어라."], src="명상록 9권 20절",
        interp=[("still", "lq07_txt", ["d2d"]), ("still", "e4a_alone", ["d2e"])],
        concept=("d2e", "스토아 철학 · 판단을 내려놓기", "남의 잘못은, 그 사람의 몫", "Leave the wrong where it lies"),
        apply=[("e2b_bed", ["d2f"]), ("e2c_kitchen", ["d2g"])], tonight=(["그 일을 한 번만 내려놓기", "그것은 그 사람의 몫"], "d2h"),
        teaser=("e3a_soldiers", "d2i", CAMP)),
 3: dict(title="칭찬에 기대지 마라", en="Praise makes nothing better",
        scene=[("still", "e3a_soldiers", ["d3a"], CAMP, {"particles": "snow", "rack": 1.2}), ("still", "e2a_generals", ["d3b"], TENT, {"move": {"zoom": [1.1, 1.0]}}),
               ("still", "e3a_soldiers", ["d3c"], CAMP, {"particles": "snow", "move": {"zoom": [1.25, 1.45], "pan": [[0, 0.05], [0, 0.08]]}, "sfx": [["war_7.mp3", 0.0, 0.18]]})],
        mono=("still", "e3a_soldiers", {"move": {"zoom": [1.5, 1.62], "pan": [[0, 0.08], [0, 0.09]]}, "particles": "snow"}),
        mvoices=["m3a", "m3b", "m3c"], verse=["칭찬받는다고,", "더 나아지지도 더 나빠지지도 않는다."], src="명상록 4권 20절",
        interp=[("still", "lq08_write", ["d3d"]), ("still", "e4a_alone", ["d3e"])],
        concept=("d3e", "스토아 철학 · 내면의 가치", "칭찬은 아무것도 더하지 않는다", "Praise adds nothing"),
        apply=[("e3b_sofa", ["d3f"]), ("e3c_meeting", ["d3g"])], tonight=(["아무도 몰라 준 오늘의 일 하나", "그것만으로 충분했다"], "d3h"),
        teaser=("e4a_alone", "d3i", TENT2)),
 4: dict(title="가장 고요한 곳은 내 마음속이다", en="Retire into thyself",
        scene=[("still", "e4a_alone", ["d4a"], TENT2, {"rack": 1.5, "flicker": True}), ("video", "ev_stars", ["d4b"], NIGHT, {"particles": "snow"})],
        mono=("video", "lwv2_front", {"flicker": True, "move": {"zoom": [1.0, 1.06]}}),
        mvoices=["m4a", "m4b", "m4c"], verse=["사람은 어디로 물러나도,", "자기 마음속보다 고요한 곳을 찾지 못한다."], src="명상록 4권 3절",
        interp=[("still", "e4b_stars", ["d4c"]), ("still", "e4a_alone", ["d4d"])],
        concept=("d4c", "피에르 아도 · 『내면의 성채』", "마음속 요새", "The Inner Citadel"),
        apply=[("e4c_bench", ["d4e"]), ("e4d_cafe", ["d4f"])], tonight=(["휴대폰을 내려놓고", "십 분만 혼자 앉기"], "d4g"),
        teaser=("lp09_teacher", "d4h", None, {"grade": "memory", "leak": True})),
 5: dict(title="좋은 사람 몇이면 충분하다", en="A few good people are enough",
        scene=[("video", "ev_garden", ["d5a"], None, {"grade": "memory", "leak": True, "tin": "dissolve"}), ("still", "lp09_teacher", ["d5b"], None, {"grade": "memory", "leak": True})],
        mono=("video", "lqv08c_write", {"flicker": True, "move": {"zoom": [1.0, 1.06]}}),
        mvoices=["m5a", "m5b", "m5c"], verse=["좋은 조부모와 부모와 스승과 벗을", "만난 것에 감사한다."], src="명상록 1권 17절",
        interp=[("still", "e5a_antoninus", ["d5c"], {"grade": "memory", "leak": True}), ("still", "e4a_alone", ["d5d"])],
        concept=("d5d", "명상록 1권 · 감사의 목록", "나를 만든 사람들", "The Gratitude List"),
        apply=[("e5c_friends", ["d5e"]), ("e5d_couple", ["d5f"])], tonight=(["나를 만든 세 사람의 이름 적기", "그중 한 사람에게 안부"], "d5g"),
        teaser=("lp11_rider", "d5h", CAMP, {"sfx": [["horse_6.mp3", 0.0, 0.45]]})),
 6: dict(title="끊어도, 미워하지는 마라", en="Anger hurts us more than the wrong",
        scene=[("video", "ev_rider", ["d6a"], CAMP, {"tin": "flash", "sfx": [["impact_1.mp3", 0.0, 0.5], ["horse_6.mp3", 0.2, 0.4]]}),
               ("video", "ev_box", ["d6b", "d6c"], TENT2, {"sfx": [["heartbeat_7.mp3", 0.0, 0.25]]}), ("still", "lp04_eyes", ["d6d"], None, {"rack": 1.4, "flicker": True})],
        mono=("still", "lp04_eyes", {"move": {"zoom": [1.2, 1.32], "pan": [[0, -0.02], [0, -0.03]]}, "flicker": True}),
        mvoices=["m6a", "m6b", "m6c"], verse=["화는, 화나게 한 일보다", "우리를 더 아프게 한다."], src="명상록 11권 18절",
        interp=[("still", "e6a_box", ["d6e"])],
        concept=("d6e", "세네카 · 『분노에 관하여』", "분노는 잠깐의 광기다", "Anger is a brief madness"),
        apply=[("e6c_car", ["d6f"]), ("e6d_hall", ["d6g"])], tonight=(["화가 올라올 때", "숨을 세 번"], "d6h"),
        teaser=("e7a_fire", "d6i", ["fire_3.mp3", 0.4])),
 7: dict(title="오늘을 마지막 날처럼", en="Pass every day as the last",
        scene=[("video", "ev_fire", ["d7a", "d7b"], ["fire_2.mp3", 0.45], {"tin": "flash", "sfx": [["fire_1.mp3", 0.0, 0.6]]})],
        mono=("still", "e7a_fire", {"move": {"zoom": [1.15, 1.3]}, "particles": "embers", "flicker": True}),
        mvoices=["m7a", "m7b", "m7c"], verse=["하루하루를 마지막 날처럼 보내는 것,", "거기에 성품의 완성이 있다."], src="명상록 7권 69절",
        interp=[("still", "e4b_stars", ["d7c"]), ("video", "ev_dawn", ["d7d"], {"tin": "flash", "sfx": [["impact_2.mp3", 0.0, 0.45], ["war_7.mp3", 0.3, 0.2]]})],
        concept=("d7c", "스토아 철학 · 메멘토 모리", "죽음을 기억하라", "Memento Mori"),
        apply=[("e7c_curtain", ["d7e"]), ("e7d_breakfast", ["d7f"])], tonight=(["미뤄 둔 말 하나", "오늘 보내기"], "d7g"),
        teaser=None),
}
MUSIC = {2: ("cinematic_5.mp3", 0), 3: ("sad_3.mp3", 0), 4: ("cinematic_4.mp3", 0), 5: ("dramatic_1.mp3", 0), 6: ("cinematic_5.mp3", 90), 7: ("cinematic_4.mp3", 110)}


def shot(kind, src, voices, amb=None, extra=None):
    if kind == "write":
        s = {"type": "video", "src": src, "write": extra, "flicker": True, "move": {"zoom": [1.0, 1.06]}}
        extra = None
    else:
        s = {"type": kind, "src": src}
        s["move"] = {"zoom": [1.0, 1.08]} if kind == "still" else {"zoom": [1.0, 1.05]}
    if voices: s["voice"] = voices
    if amb: s["amb"] = amb
    s.setdefault("tin", "dissolve")
    if extra: s.update(copy.deepcopy(extra))
    return s


def chapter(n, c):
    S = []; mus_at = None
    S.append({"type": "card", "label": f"THE {ORD[n]} LINE", "num": NUM[n], "title": c["title"], "en": c["en"], "dur": 4.2, "fixed": True, "sfx": CARD_SFX, "amb": ["wind_2.mp3", 0.25]})
    for kind, src, vs, amb, ex in c["scene"]: S.append(shot(kind, src, vs, amb, ex))
    mk, msrc, mex = c["mono"]
    m = shot(mk, msrc, c["mvoices"], TENT2, mex if mk != "write" else mex)
    if mk == "write": m = shot("write", msrc, c["mvoices"], TENT2, mex)
    m.update({"gap": 1.0, "pre": 0.8, "post": 1.8, "nocap_voices": [c["mvoices"][-1]]})
    m.setdefault("sfx", []).append(["paper_6.mp3", 0.4, 0.5])
    m["overlays"] = [{"kind": "verse", "lines": c["verse"], "src": c["src"], "at_voice": c["mvoices"][-1]}]
    S.append(m)
    cv, kick, line, en = c["concept"]
    for it in c["interp"]:
        kind, src, vs = it[:3]; ex = it[3] if len(it) > 3 else {}
        s = shot(kind, src, vs, TENT2 if kind == "still" else CAMP, ex)
        if cv in vs: s["overlays"] = [{"kind": "concept", "kicker": kick, "lines": [line], "en": en, "at_voice": cv, "offset": 0.4, "len": 5.0}]
        S.append(s)
    for src, vs in c["apply"]: S.append(shot("still", src, vs, CITY, {"grade": "modern", "move": {"zoom": [1.0, 1.07], "pan": [[0.01, 0], [-0.01, 0]]}}))
    tl, tv = c["tonight"]
    S.append({"type": "tonight", "lines": tl, "voice": tv, "pre": 0.8, "post": 1.4, "amb": ["fire_0.mp3", 0.18], "nocap": True, "sfx": [["paper_6.mp3", 0.2, 0.35]]})
    if c["teaser"]:
        t = c["teaser"]; ex = t[3] if len(t) > 3 else {}
        s = shot("still", t[0], [t[1]], t[2], ex); s.update({"tout": "black", "fout": 0.8, "post": 1.4}); S.append(s)
    return S


def build():
    P = json.load(open(os.path.join(HERE, "spec_pilot.json")))
    sp = copy.deepcopy(P); sp["id"] = "edl_ep01"
    sp["voice_dir"] = "social/side/voice_samples/ep01"
    vf = {k: ("../lp2/" + v if v.startswith("voice_lp2") else v) for k, v in P["voice_files"].items()}
    for i, (n, v, t) in enumerate(E.LINES): vf[n] = f"voice_ep01_{i + 1:02d}_{n}.mp3"
    sp["voice_files"] = vf
    sp["monologue_voices"] = P["monologue_voices"] + [n for n, v, t in E.LINES if v == E.M]
    subs = dict(P["subs"])
    for n, v, t in E.LINES: subs[n] = subs_of(n)
    sp["subs"] = subs
    sh = sp["shots"]
    # 앞부분: 파일럿 0~18 (훅·인트로·오프닝·상황·1장). 1장 해설에 에픽테토스 보강
    for s in sh:
        if s.get("src") == "lq08_txt" and "c1c" in str(s.get("voice")): s["voice"] = ["c1c", "c1g"]
    sh[12]["sfx"] = CARD_SFX; sh[12]["label"] = "THE FIRST LINE"
    # 11/3 대표 피드백: 심장박동 두세 번 더(점점 약하게), 펜 장면은 글씨 합성 없이 두 각도 번갈아, 오프닝은 깔끔하게
    sh[3]["sfx"] = [["heartbeat_5.mp3", 0.05, 1.2], ["heartbeat_5.mp3", 0.85, 1.0], ["heartbeat_5.mp3", 1.65, 0.7], ["heartbeat_5.mp3", 2.45, 0.45], ["heartbeat_5.mp3", 3.25, 0.25]]
    sh[5].pop("write", None); sh[5]["src"] = "lwv2_front"; sh[5]["move"] = {"zoom": [1.0, 1.08]}
    ep = sh[8]; ep.pop("chapter", None); ep["sfx"] = [["drum_6.mp3", 0.3, 0.45]]; ep["dur"] = 4.6
    m1 = sh[14]; m1.pop("write", None); m1["src"] = "lqv08c_write"
    m2 = copy.deepcopy(m1); m1["voice"] = ["m_c1b1", "m_c1b2"]; m1["post"] = 0.6; m1["overlays"] = []
    m2.update({"src": "lwv2_front", "voice": ["m_c1b3", "m_c1b4"], "pre": 0.5, "tin": "dissolve",
               "overlays": [{"kind": "verse", "lines": ["남의 생각을 짐작하느라,", "남은 날들을 쓰지 마라."], "src": "명상록 3권 4절", "at_voice": "m_c1b4"}]})
    sh.insert(15, m2)
    # 11/3 대표: 1:19 펜 장면의 낙서는 지우고 상황에 맞는 필기체만 종이에 고정 (손 쪽은 가림 처리)
    m1["write"] = write(["Do not waste the remainder", "of thy life in thoughts about others."], Q2)
    # 1장 해설이 같은 각도 종이 그림으로 오래 이어지지 않게: 에픽테토스 대목은 스승 회상 장면으로
    for i, x in enumerate(sh):
        if x.get("src") == "lq08_txt":
            x["src"] = "lq08_write"; x["voice"] = ["c1c"]
            sh.insert(i + 1, {"type": "still", "src": "lp09_teacher", "voice": ["c1g"], "grade": "memory", "leak": True, "tin": "dissolve",
                              "move": {"zoom": [1.0, 1.1], "pan": [[0.02, 0], [-0.02, 0]]}, "pre": 0.3, "post": 0.6})
            break
    # 11/4 대표: 1장 끝 "몇 달 뒤 상자 도착"은 6장(d5h→d6b)과 겹치고 다음 장면("날이 밝기도 전에")과 시간도 거꾸로 → 1장 쪽을 뺀다
    sh[:] = [x for x in sh if "c1f" not in (x.get("voice") if isinstance(x.get("voice"), list) else [x.get("voice")])]
    for x in sh:
        if "c1e" in str(x.get("voice")): x.update({"tout": "black", "fout": 1.0, "post": max(x.get("post", 0.6), 1.4)})
    # 파일럿 때 쉼표 단위로 잘게 나눈 1장 자막은 문장 단위로 (목소리와 어긋나지 않게)
    for k in ("c1a", "c1c", "c1d", "c1e", "s1", "s3"):
        if k in E.TXT: continue
    subs["c1a"] = ["전령이 물러간 뒤에도, 황제는 편지를 내려놓지 못했습니다.", "아비디우스 카시우스.", "동방의 전쟁을 승리로 이끌고, 황제가 동방 전체를 맡겼던 장군이었습니다."]
    subs["c1c"] = ["황제는 이 생각을 일기 곳곳에 되풀이해 적었습니다.", "스토아 철학에서는 이것을, 내 힘이 닿는 것과 닿지 않는 것을 가르는 일이라고 합니다.", "!남의 마음은, 언제나 내 힘이 닿지 않는 쪽에 있습니다."]
    subs["c1d"] = ["회의가 끝난 뒤, 나를 두고 뒷말을 했다는 동료.", "며칠째 답이 없는 오랜 친구.", "!우리는 그 사람의 속을 짐작하느라, 밤을 통째로 씁니다."]
    subs["c1e"] = ["오늘 밤에는, 그 사람 대신 나에게 물어보세요.", "지금 내 힘이 닿는 일은, 무엇인가."]
    for x in sh:
        if x.get("type") == "tonight": x["nocap"] = True
    sp["subs"] = subs
    end = sh.pop()                      # 옛 엔딩 제거
    S = sh
    card_idx = {1: 12}
    for n in range(2, 8):
        card_idx[n] = len(S); S += chapter(n, CH[n])
    rec = len(S)
    S.append({"type": "recap", "items": ["남의 생각을 짐작하느라, 남은 날들을 쓰지 마라", "남의 잘못은, 그것이 생긴 자리에 두어라", "칭찬은 나를 더 낫게도, 더 못하게도 만들지 않는다",
                                         "가장 고요한 곳은, 내 마음속이다", "좋은 사람 몇이면, 충분하다", "화는, 나를 먼저 해친다", "오늘을, 마지막 날처럼"],
              "voice": ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8"], "gap": 0.8, "pre": 0.8, "post": 1.0, "recap_offset": 1, "nocap": True,
              "sfx": [["transition_5.mp3", 0.0, 0.35]], "tin": "black", "fin": 1.0})
    S.append(shot("still", "e7b_dawn", ["r9"], ["wind_2.mp3", 0.25], {"move": {"zoom": [1.18, 1.0]}, "post": 1.6, "tin": "dissolve"}))
    out = len(S)
    S.append({"type": "outro", "voice": ["o1", "o2"], "gap": 0.7, "pre": 1.0, "post": 2.6, "dur": 12.0, "nocap": True,
              "next_kicker": "NEXT  ·  EPISODE 2", "next": "무례한 사람들", "slogan_at": 999, "tap_sub": 3.4, "tap_like": 4.2,
              "sfx": [["ring_synth.wav", 3.42, 0.45], ["click_2.mp3", 3.4, 0.6], ["click_2.mp3", 4.2, 0.6], ["ring_synth.wav", 4.22, 0.35], ["drum_6.mp3", 0.2, 0.4]]})
    # 11/3 대표: 맨 마지막 엔딩 — "매일 밤, 황제처럼 생각하라 · 황제의 일기"
    #   황제(명일) "매일 밤, 황제처럼 생각하라." → 해설(건석) "황제의 일기." — 글자는 각 목소리 시작에 맞춰 뜬다
    sp["voice_files"]["e_x2"] = "../ep01x/voice_ep01x_01_e_x2.mp3"
    S.append({"type": "end", "dur": 7.5, "voice": ["m_x1", "e_x2"], "pre": 0.9, "gap": 0.9, "post": 2.6, "nocap": True, "slogan": "매일 밤, 황제처럼 생각하라", "tin": "black",
              "sfx": [["ring_synth.wav", 0.5, 0.25]]})
    # 음악
    mus = [m for m in P["music"]]; mus[0]["until_shot"] = card_idx[2]; mus[0].pop("len", None)
    for n in range(2, 8):
        f, st = MUSIC[n]; nxt = card_idx[n + 1] if n < 7 else rec
        mus.append({"file": f, "at_shot": card_idx[n], "offset": 1.0, "start": st, "until_shot": nxt, "vol": 0.2, "fin": 3, "fout": 3})
    mus.append({"file": "sad_5.mp3", "at_shot": rec, "offset": 0.5, "start": 0, "until_shot": out + 2, "tail": 0, "vol": 0.22, "fin": 2, "fout": 4})
    sp["music"] = mus
    sp["voice_gain"] = {"mono": 1.9}   # 11/3 대표: 황제 목소리 조금 더 크게 (1.45 → 1.9)
    # 11/4 대표 피드백 정리
    for x in S:
        if x.get("src") == "lqv08c_write": x["src"] = "lwv3_side"; x.pop("write", None)   # 11/4: 비스듬한 종이 영상 → 새 옆 각도(글이 이미 써 있는 종이)
        if x.get("src") == "lq08_write" and x["type"] == "still": x["src"] = "lq08_page"   # 같은 장면 그림에도 같은 글
        if x.get("src") not in ("lwv3_side", "lwv2_front") and x["type"] != "intro":   # 글씨 쓰는 장면이 아니면 펜 소리 빼기
            if x.get("sfx"): x["sfx"] = [f for f in x["sfx"] if f[0] != "paper_6.mp3"]
    json.dump(sp, open(os.path.join(HERE, "spec_ep01.json"), "w"), ensure_ascii=False, indent=1)
    print("장면", len(S), "카드 위치", card_idx, "정리", rec, "아웃트로", out)
