"""EPISODE 3 렌더 설정 — 2편 틀(ep02_spec)을 그대로 쓰고 장면·대본만 바꾼다 (2026-11-04)
python3 ep03.py spec → scripts/side/ed_long/spec_ep03.json"""
import json, os, copy, sys, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ep03 as E
import ep01_spec as F
from ep02_spec import ELEC, subs_of as _subs

TENT = ["fire_4.mp3", 0.38]; TENT2 = ["fire_0.mp3", 0.3]; CAMP = ["wind_2.mp3", 0.4]; CITY = ["night_2.mp3", 0.25]; FORUM = ["wind_1.mp3", 0.3]


def subs_of(t, v):
    return _subs(t, v if v in (E.G, E.M) else "CAST")


def auto_faces(srcs):
    """그림 속 얼굴 위치(원본 비율) — 2편에서 만든 '얼굴이 띠에 잘리지 않게' 규칙용. 가장 큰 얼굴 하나만"""
    import cv2
    fc = cv2.CascadeClassifier(os.path.join(HERE, "haar", "haarcascade_frontalface_default.xml")); out = {}
    for k in srcs:
        p = os.path.join(E.ROOT, "social/side/gen", k + ".jpeg")
        if os.path.exists(p): im = cv2.imread(p)
        else:
            cap = cv2.VideoCapture(os.path.join(E.ROOT, "social/side/gen", k + ".mp4")); ok, im = cap.read()
            if not ok: continue
        h, w = im.shape[:2]; g = cv2.equalizeHist(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY))
        r = sorted(fc.detectMultiScale(g, 1.1, 7, minSize=(w // 16, w // 16)), key=lambda b: -b[2] * b[3])
        if len(r):
            x, y, a, b = r[0]; out[k] = [round(x / w, 3), round(max(0, y / h - 0.03), 3), round((x + a) / w, 3), round((y + b) / h, 3)]
    return out


CH3 = {
 1: dict(title="포도나무처럼", en="Like a vine that bears grapes",
        scene=[("video", "ev3_plague", ["d1a", "d1b"], CITY, {"move": {"zoom": [1.0, 1.08]}}),
               ("still", "e3_widow", ["w1", "d1c"], ["wind_1.mp3", 0.25], {"gap": 0.6, "move": {"zoom": [1.0, 1.12]}})],
        mono=("video", "lwv3_side", {"flicker": True, "move": {"zoom": [1.0, 1.06]}}),
        mvoices=["m1a", "m1b", "m1c"], verse=["포도나무가 포도를 맺듯,", "선을 행하고 아무것도 바라지 마라."], src="명상록 5권 6절",
        interp=[("still", "e3_vine", ["d1d"], {"grade": "memory", "leak": True, "move": {"zoom": [1.0, 1.1]}})],
        concept=("d1d", "스토아 철학 · 본성에 따라 살기", "선은 그 자체로 보상이다", "Like a vine that bears grapes"),
        apply=[("e3m_kitchen", ["d1e"]), ("e3m_family", ["d1f"])], tonight=(["오늘 한 좋은 일 하나", "아무에게도 말하지 않기"], "d1g"),
        teaser=("e3_carriage", "d1h", ["wind_6.mp3", 0.35], {"move": {"zoom": [1.0, 1.08]}})),
 2: dict(title="세 번째 것을 바라지 마라", en="Seek not a third thing",
        scene=[("video", "ev3_carriage", ["d2a"], ["wind_6.mp3", 0.4], {"tin": "flash", "sfx": [["horse_6.mp3", 0.0, 0.35]]}),
               ("still", "e3_lucius", ["d2b"], TENT2, {"rack": 1.4, "move": {"zoom": [1.0, 1.12]}, "flicker": True}),
               ("still", "e3_rumor", ["d2c", "r_sen", "d2d"], ["fire_2.mp3", 0.25], {"gap": 0.5, "flicker": True, "move": {"zoom": [1.0, 1.1]}})],
        mono=("video", "lwv2_front", {"flicker": True, "move": {"zoom": [1.0, 1.06]}}),
        mvoices=["m2a", "m2b", "m2c"], verse=["선을 행했으면 그것으로 끝이다,", "세 번째 것을 바라지 마라."], src="명상록 7권 73절",
        interp=[("still", "e3_lucius", ["d2e"], {"move": {"zoom": [1.3, 1.42], "pan": [[0.1, 0], [0.12, 0]]}, "flicker": True})],
        concept=("d2e", "스토아 철학 · 보답을 바라지 않는 선", "선행에 인정까지 바라지 마라", "Seek not a third thing"),
        apply=[("e3m_hospital", ["d2f"]), ("e3m_funeral", ["d2g"])], tonight=(["내가 한 일에 붙여 둔", "'알아 달라'는 마음 떼어 내기"], "d2h"),
        teaser=("e3_treasury", "d2i", TENT2, {"move": {"zoom": [1.0, 1.1]}})),
 3: dict(title="이름은 금방 잊힌다", en="Fame is soon forgotten",
        scene=[("still", "e3_treasury", ["d3a"], TENT2, {"move": {"zoom": [1.1, 1.24]}, "flicker": True}),
               ("still", "e3_senate", ["d3b", "t_sen", "d3c", "m3x"], ["wind_1.mp3", 0.2], {"gap": 0.6, "move": {"zoom": [1.0, 1.12]}})],
        mono=("video", "lwv3_side", {"flicker": True, "move": {"zoom": [1.04, 1.1]}}),
        mvoices=["m3a", "m3b", "m3c"], verse=["이름은 금방 잊힌다,", "지금, 옳은 일을 하라."], src="명상록 4권 19절",
        interp=[("still", "e3_senate", ["d3d"], {"move": {"zoom": [1.3, 1.45], "pan": [[0.12, 0.02], [0.14, 0.02]]}})],
        concept=("d3d", "스토아 철학 · 명성의 덧없음", "이름보다 오늘의 옳은 일", "Fame is soon forgotten"),
        apply=[("e3m_promotion", ["d3e"]), ("e3m_desk", ["d3f"])], tonight=(["이름 없이도", "뿌듯했던 오늘의 일 하나"], "d3g"),
        teaser=("e3_forum", "d3h", FORUM, {"move": {"zoom": [1.0, 1.08]}})),
 4: dict(title="칭찬을 듣든 비난을 듣든", en="Do thy duty",
        scene=[("still", "e3_cups", ["d4a"], FORUM, {"move": {"zoom": [1.0, 1.12], "pan": [[0.02, 0], [-0.02, 0]]}}),
               ("still", "e3_gown", ["d4b", "c4"], FORUM, {"gap": 0.4, "move": {"zoom": [1.15, 1.28]}}),
               ("still", "e3_watch", ["d4c"], FORUM, {"rack": 1.2, "move": {"zoom": [1.0, 1.1]}})],
        mono=("video", "lwv2_front", {"flicker": True, "move": {"zoom": [1.04, 1.1]}}),
        mvoices=["m4a", "m4b", "m4c"], verse=["칭찬을 듣든 비난을 듣든,", "해야 할 일을 하라."], src="명상록 6권 2절",
        interp=[("still", "e4a_alone", ["d4d"], {"move": {"zoom": [1.0, 1.1]}, "flicker": True})],
        concept=("d4d", "스토아 철학 · 의무", "박수와 상관없이, 할 일을 한다", "Do thy duty"),
        apply=[("e3m_nurse", ["d4e"]), ("e3m_guard", ["d4f"])], tonight=(["내일 아무도 안 보는 곳에서", "할 일 하나 정하기"], "d4g"),
        teaser=("e3_soldiers", "d4h", CAMP, {"move": {"zoom": [1.0, 1.08]}})),
 5: dict(title="남의 평가를 앞에 두지 마라", en="We value others' opinion more",
        scene=[("still", "e3_soldiers", ["d5a", "v_sol"], CAMP, {"gap": 0.5, "move": {"zoom": [1.12, 1.26]}, "sfx": [["war_7.mp3", 0.0, 0.18]]}),
               ("still", "e3_refuse", ["d5b", "m5x", "d5c"], CAMP, {"gap": 0.6, "flicker": True, "move": {"zoom": [1.0, 1.12]}})],
        mono=("video", "lwv3_side", {"flicker": True, "move": {"zoom": [1.0, 1.06]}}),
        mvoices=["m5a", "m5b", "m5c"], verse=["남의 평가를,", "내 판단보다 앞에 두지 마라."], src="명상록 12권 4절",
        interp=[("still", "e3_refuse", ["d5d"], {"move": {"zoom": [1.3, 1.4]}, "flicker": True})],
        concept=("d5d", "스토아 철학 · 내면의 판단", "인기보다 판단", "Value thine own judgment"),
        apply=[("e3m_mother", ["d5e"]), ("e3m_meeting", ["d5f"])], tonight=(["남의 눈 때문에 미뤄 둔", "옳은 결정 하나 적기"], "d5g"),
        teaser=("e4a_alone", "d5h", TENT2, {"flicker": True, "move": {"zoom": [1.12, 1.22]}})),
 6: dict(title="좋은 사람이 되어라", en="Be such a man",
        scene=[("still", "e3_senators", ["d6a"], FORUM, {"move": {"zoom": [1.0, 1.1]}}),
               ("still", "e4b_stars", ["d6b"], ["night_6.mp3", 0.2], {"particles": "snow", "move": {"zoom": [1.0, 1.08]}})],
        mono=("video", "lwv2_front", {"flicker": True, "move": {"zoom": [1.0, 1.06]}}),
        mvoices=["m6a", "m6b", "m6c"], verse=["좋은 사람을 논하지 말고,", "좋은 사람이 되어라."], src="명상록 10권 16절",
        interp=[("still", "e3_forum", ["d6c"], {"move": {"zoom": [1.2, 1.32], "pan": [[0.05, 0], [0.07, 0]]}})],
        concept=("d6c", "스토아 철학 · 실천", "철학은 말이 아니라 삶", "Be such a man"),
        apply=[("e3m_volunteer", ["d6d"]), ("e3m_volunteer2", ["d6e"])], tonight=(["말로만 했던 좋은 일 하나", "이번 주에 직접 하기"], "d6f"),
        teaser=("e3_return", "d6i", ["wind_1.mp3", 0.2], {"move": {"zoom": [1.0, 1.08]}})),
 7: dict(title="이미 보상받았다", en="Virtue is its own reward",
        scene=[("still", "e3_return", ["d7a", "d7b"], ["wind_1.mp3", 0.2], {"move": {"zoom": [1.1, 1.24]}}),
               ("still", "e3_statue", ["d7c"], ["wind_2.mp3", 0.25], {"grade": "memory", "leak": True, "move": {"zoom": [1.0, 1.12]}})],
        mono=("video", "lwv3_side", {"flicker": True, "move": {"zoom": [1.04, 1.1]}}),
        mvoices=["m7a", "m7b", "m7c"], verse=["공동체를 위해 일했다면,", "나는 이미 보상받았다."], src="명상록 11권 4절",
        interp=[("still", "e3_vine", ["d7d"], {"grade": "memory", "leak": True, "move": {"zoom": [1.2, 1.32]}})],
        concept=("d7d", "스토아 철학 · 덕은 그 자체로 보상", "좋은 일은 이미 받은 보상", "Virtue is its own reward"),
        apply=[("e3m_retire", ["d7e"]), ("e3m_home", ["d7f"])], tonight=(["내가 오래 해 온 일 하나에게", "'잘했다' 말해 주기"], "d7g"),
        teaser=None),
}
MUSIC3 = {1: ("sad_3.mp3", 0), 2: ("cinematic_5.mp3", 0), 3: ("dramatic_1.mp3", 0), 4: ("cinematic_4.mp3", 0), 5: ("cinematic_5.mp3", 90), 6: ("sad_3.mp3", 60), 7: ("cinematic_4.mp3", 110)}


def build():
    base = json.load(open(os.path.join(HERE, "spec_ep02.json")))   # 2편 최종 설정(인트로 효과음·목소리 크기·엔딩 양식)을 물려받는다
    sp = {k: copy.deepcopy(base[k]) for k in ("root", "gen_dir", "sfx_dir", "music_dir", "out_dir", "intro", "monologue_fx", "voice_gain")}
    sp["id"] = "edl_ep03"; sp["voice_dir"] = f"social/side/voice_samples/{E.TAG}"
    d = os.path.join(E.ROOT, sp["voice_dir"]); vf = {}
    for n in (sorted(os.listdir(d)) if os.path.isdir(d) else []):
        if n.endswith(".mp3"): vf[n[:-4].split("_", 3)[-1]] = n
    vf["o3"] = "../ep02c/voice_ep02c_01_o3.mp3"   # 1편 추천 화면 해설(2편과 같은 녹음)
    vf["m_x1"] = "../lp3/voice_lp3_07_m_x1.mp3"; vf["e_x2"] = "../ep01x/voice_ep01x_01_e_x2.mp3"
    sp["voice_files"] = vf
    ALL = E.HOOK + E.LINES
    sp["subs"] = {n: subs_of(t, v) for n, v, t in ALL}
    for n in ("m3x", "m5x"): sp["subs"][n] = "“" + E.clean(dict((a, c) for a, b, c in ALL)[n]) + "”"   # 황제가 소리 내어 한 말
    sp["monologue_voices"] = [n for n, v, t in ALL if v == E.M] + ["m_x1"]
    S = []
    # 훅: 웅성거림 → 경매꾼 → 해설 → 수군대는 원로원 → 내려다보는 황제(독백)
    S.append({"type": "black", "dur": 0.8, "fixed": True, "amb": ["wind_6.mp3", 0.4]})
    S.append({"type": "video", "src": "ev3_forum", "voice": ["h_cr", "h1"], "pre": 0.3, "gap": 0.6, "post": 0.4, "move": {"zoom": [1.0, 1.1]}, "tin": "black", "fin": 0.8,
              "amb": ["war_7.mp3", 0.12], "overlays": [{"kind": "caption", "text": "기원후 169년 · 로마, 트라야누스 광장", "at": 0.3}]})
    S.append({"type": "still", "src": "e3_gown", "voice": ["h2"], "pre": 0.2, "post": 0.3, "move": {"zoom": [1.0, 1.12]}, "amb": FORUM})
    S.append({"type": "still", "src": "e3_senators", "voice": ["h_sen"], "pre": 0.3, "post": 0.5, "move": {"zoom": [1.05, 1.18]}, "amb": FORUM})
    S.append({"type": "still", "src": "e3_watch", "voice": ["m_h1", "m_h2"], "pre": 0.5, "gap": 1.0, "post": 0.9, "move": {"zoom": [1.04, 1.16]}, "flicker": True,
              "sfx": [["heartbeat_5.mp3", 0.1, 0.9], ["heartbeat_5.mp3", 0.9, 0.6], ["heartbeat_5.mp3", 1.7, 0.35]], "tout": "black", "fout": 1.0})
    S.append({"type": "black", "dur": 0.4, "fixed": True})
    S.append(copy.deepcopy([s for s in base["shots"] if s["type"] == "intro"][0]))
    S.append({"type": "episode", "num": 3, "title": "아무도 알아주지 않을 때", "en": "When No One Notices", "dur": 4.6, "fixed": True,
              "amb": ["wind_2.mp3", 0.3], "sfx": [["drum_6.mp3", 0.3, 0.45]], "tout": "black", "fout": 0.8})
    sit = len(S)
    S.append(F.shot("still", "e3_triumph", ["s1"], ["war_7.mp3", 0.15], {"tin": "black", "fin": 0.8, "move": {"zoom": [1.0, 1.1]},
                    "overlays": [{"kind": "caption", "text": "삼 년 전 · 기원후 166년", "at": 0.3}]}))
    S.append(F.shot("still", "e3_triumph", ["s2"], ["wind_6.mp3", 0.3], {"move": {"zoom": [1.3, 1.45], "pan": [[0.0, 0.05], [0.0, 0.06]]}}))
    S.append(F.shot("still", "e3_galen", ["s3"], TENT2, {"flicker": True, "move": {"zoom": [1.0, 1.12]}}))
    s4 = F.shot("still", "e3_morning", ["s4"], CAMP, {"move": {"zoom": [1.0, 1.08]}}); s4.update({"tout": "black", "fout": 0.8, "post": 1.4}); S.append(s4)
    card = {}
    for n in range(1, 8):
        card[n] = len(S); S += F.chapter(n, CH3[n])
    rec = len(S)
    S.append({"type": "recap", "items": ["포도나무처럼, 선을 행하고 바라지 마라", "세 번째 것을 바라지 마라", "이름은 금방 잊힌다, 지금 옳은 일을 하라", "칭찬을 듣든 비난을 듣든, 할 일을 하라",
                                         "남의 평가를 내 판단보다 앞에 두지 마라", "좋은 사람을 논하지 말고, 되어라", "선을 행했다면, 이미 보상받았다"],
              "voice": ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8"], "gap": 0.8, "pre": 0.8, "post": 1.0, "recap_offset": 1, "nocap": True,
              "head_en": "SEVEN LINES FOR WHEN NO ONE NOTICES", "sfx": [["paper_3.mp3", 0.2, 0.45]], "tin": "black", "fin": 1.0})
    S.append(F.shot("still", "e3_statue", ["r9"], ["wind_2.mp3", 0.25], {"grade": "memory", "move": {"zoom": [1.18, 1.0]}, "post": 1.6, "tin": "dissolve"}))
    # 11/4 대표: 이전 편 추천 화면은 빼고, 마지막 빈 화면(유튜브 최종 화면)에 구독 + 이전 편 영상을 스튜디오에서 배치
    out = len(S)
    # 11/4 대표: 마지막 한 화면 — 슬로건·황제의 일기 내레이션과 함께 구독·좋아요 버튼 + 이전 편 영상 자리(유튜브 최종 화면 요소를 같은 자리에 배치), 20초
    S.append({"type": "finale", "dur": 20.0, "voice": ["m_x1", "e_x2", "o1", "o2"], "pre": 0.8, "gap": 0.8, "post": 1.0, "nocap": True, "tin": "black",
              "slogan": "매일 밤, 황제처럼 생각하라", "prev_kicker": "이전 이야기  ·  EPISODE 2", "next": "아내를 잃은 밤", "amb": ["wind_2.mp3", 0.15],
              "sfx": [["click_2.mp3", 0, 0.0]]})
    # 11/4 대표: 영상미·장면 전환 강화 — 그림의 첫 등장은 움직이는 영상으로, 목소리 둘 이상인 이야기 장면은 영상 → 같은 장면 클로즈업 그림으로 한 번 더 끊어 간다
    VID = {src: k for k, (src, _) in list(E.VIDEOS.items()) + list(E.VIDEOS_PLUS.items())}
    seen = set(); S2 = []
    for x in S:
        src = x.get("src")
        if x.get("type") == "still" and src in VID and src not in seen and os.path.exists(os.path.join(E.ROOT, "social/side/gen", VID[src] + ".mp4")):
            seen.add(src); vs = x.get("voice") or []; vs = [vs] if isinstance(vs, str) else vs
            v = copy.deepcopy(x); v["type"] = "video"; v["src"] = VID[src]; v.pop("rack", None)
            if len(vs) >= 2 and not x.get("overlays") and x.get("type") == "still":
                v["voice"] = vs[:1]; v["post"] = 0.3
                c = copy.deepcopy(x); c["voice"] = vs[1:]; c["tin"] = "dissolve"; c["pre"] = 0.2
                c["move"] = {"zoom": [1.18, 1.3], "pan": [[0.0, -0.02], [0.02, -0.03]]}
                S2 += [v, c]
            else: S2.append(v)
        else:
            if src in VID: seen.add(src)
            S2.append(x)
    S[:] = S2
    cards = [i for i, x in enumerate(S) if x.get("type") == "card"]; card = {n + 1: i for n, i in enumerate(cards)}   # 끊은 뒤 번호 다시 매김
    rec = [i for i, x in enumerate(S) if x.get("type") == "recap"][0]; out = [i for i, x in enumerate(S) if x.get("type") == "finale"][0]
    sit = [i for i, x in enumerate(S) if x.get("type") == "episode"][0] + 1
    faces = auto_faces({x.get("src") for x in S if x.get("src") and x["type"] in ("still", "video")})
    for x in S:
        if x.get("src") in faces: x["face"] = faces[x["src"]]
        if x.get("type") != "intro" and x.get("sfx"):
            x["sfx"] = [["paper_3.mp3", f[1], max(f[2], 0.4)] if f[0] == "paper_2.mp3" else f for f in x["sfx"] if f[0] not in ELEC]
        if x.get("type") == "tonight": x["nocap"] = True; x["sfx"] = []
        if x.get("src") not in ("lwv3_side", "lwv2_front") and x.get("sfx"): x["sfx"] = [f for f in x["sfx"] if f[0] != "paper_6.mp3"]
    mus = [{"file": "cinematic_0.mp3", "at_shot": sit, "offset": 0.5, "start": 0, "until_shot": card[1], "vol": 0.22, "fin": 3, "fout": 3}]
    for n in range(1, 8):
        f, st = MUSIC3[n]; nxt = card[n + 1] if n < 7 else rec
        mus.append({"file": f, "at_shot": card[n], "offset": 1.0, "start": st, "until_shot": nxt, "vol": 0.2, "fin": 3, "fout": 3})
    mus.append({"file": "sad_5.mp3", "at_shot": rec, "offset": 0.5, "start": 0, "until_shot": out + 2, "tail": 0, "vol": 0.22, "fin": 2, "fout": 4})
    sp["music"] = mus
    sp["shots"] = S
    sp["cast_voices"] = [n for n, v, t in ALL if v not in (E.G, E.M)]
    json.dump(sp, open(os.path.join(HERE, "spec_ep03.json"), "w"), ensure_ascii=False, indent=1)
    print("장면", len(S), "목소리", len(vf), "카드", card, "얼굴", len(faces))
