"""EPISODE 2 렌더 설정 만들기 — 1편 설정(spec_ep01.json)의 공통 값(인트로·자막·목소리 크기)을 물려받는다 (2026-11-04)
1단계: 훅 + 인트로 + EPISODE 2 오프닝"""
import json, os, copy, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ep02 as E

CAST = {"HERODES": "jongdae", "PREFECT": "wangkwon"}   # 오디션 뒤 확정 (조연은 Claude 가 고름)


import re
import ep01_spec as F   # 문장 묶음(카드 → 장면 → 독백·구절 → 해설 → 오늘의 장면 → 오늘 밤 → 다음 예고) 만드는 틀은 1편과 같다
TENT = ["fire_4.mp3", 0.38]; TENT2 = ["fire_0.mp3", 0.3]; CAMP = ["wind_2.mp3", 0.4]; RAIN = ["rain_3.mp3", 0.45]; HALLA = ["fire_4.mp3", 0.32]


def subs_of(t, v):
    emph = t.startswith("!"); t = t.lstrip("!")
    if v not in (E.G, E.M): return f"“{t}”"   # 조연 대사는 따옴표
    parts = [x for x in re.split(r"(?<=[.?!])\s+", t) if x]
    return [("!" + x if emph else x) for x in parts] if len(parts) > 1 else ("!" + t if emph else t)


CH2 = {
 1: dict(title="아침마다 미리 각오하라", en="Begin the morning by saying to thyself",
        scene=[("still", "e2_dawn", ["d1a", "d1b"], TENT2, {"rack": 1.2, "move": {"zoom": [1.0, 1.12]}})],
        mono=("video", "lwv3_side", {"flicker": True, "move": {"zoom": [1.0, 1.06]}}),
        mvoices=["m1a", "m1b", "m1c"], verse=["아침마다 스스로에게 말하라,", "오늘 나는 무례한 사람들을 만날 것이다."], src="명상록 2권 1절",
        interp=[("still", "e2_dawn", ["d1c"], {"move": {"zoom": [1.25, 1.38], "pan": [[0.05, -0.02], [0.07, -0.02]]}}), ("still", "e2_eyes", ["d1d"], {"move": {"zoom": [1.0, 1.12]}, "flicker": True})],
        concept=("d1c", "스토아 철학 · 미리 그려 보기", "예고된 무례는 기습이 되지 않는다", "Premeditatio malorum"),
        apply=[("e2m_elevator", ["d1e"]), ("e2m_breath", ["d1f"])], tonight=(["내일 만날 까다로운 사람 한 명", "그가 할 법한 말을 미리 적기"], "d1g"),
        teaser=("e2_rain", "d1h", RAIN, {"sfx": [["impact_3.mp3", 0.6, 0.3]]})),
 2: dict(title="그가 무엇을 옳다고 믿었는지 보라", en="With what opinion he did wrong",
        scene=[("video", "ev2_lightning", ["d2a"], RAIN, {"tin": "flash", "sfx": [["impact_3.mp3", 0.0, 0.55], ["rain_5.mp3", 0.0, 0.35]]}),
               ("still", "e2_daughters", ["d2b", "d2c"], ["rain_0.mp3", 0.25], {"move": {"zoom": [1.0, 1.15]}, "rack": 1.4}),
               ("still", "e2_herodes", ["d2d"], None, {"move": {"zoom": [1.0, 1.1]}, "flicker": True})],
        mono=("video", "lwv2_front", {"flicker": True, "move": {"zoom": [1.0, 1.06]}}),
        mvoices=["m2a", "m2b", "m2c"], verse=["그가 무엇을 옳다고 믿었는지 보면,", "화 대신 연민이 남는다."], src="명상록 7권 26절",
        interp=[("still", "e2_rain", ["d2e"], {"move": {"zoom": [1.15, 1.0]}})],
        concept=("d2e", "스토아 철학 · 판단을 보라", "무례 뒤에는 그의 사정이 있다", "See the opinion behind the act"),
        apply=[("e2m_holiday", ["d2f"]), ("e2m_uncle", ["d2g"])], tonight=(["나를 언짢게 한 사람", "그에게 있었을 사정 한 줄"], "d2h"),
        teaser=("e2_clock", "d2i", HALLA, {"sfx": [["water_drip.wav", 0.8, 0.25]]})),
 3: dict(title="무례한 사람이 없는 세상은 없다", en="Shameless men must be in the world",
        scene=[("still", "e2_court", ["d3a", "d3b"], HALLA, {"flicker": True, "move": {"zoom": [1.0, 1.14]}, "sfx": [["water_drip.wav", 0.4, 0.22]]}),
               ("video", "ev2_sword", ["d3c", "p3", "h3"], HALLA, {"flicker": True, "gap": 0.5, "move": {"zoom": [1.04, 1.12]}}),
               ("video", "ev2_walkout", ["d3d"], HALLA, {"flicker": True})],
        mono=("video", "lwv3_side", {"flicker": True, "move": {"zoom": [1.04, 1.1]}}),
        mvoices=["m3a", "m3b", "m3c"], verse=["불가능한 것을 바라지 마라,", "무례한 사람이 없는 세상은 없다."], src="명상록 9권 42절",
        interp=[("still", "e2_market", ["d3e"], {"move": {"zoom": [1.0, 1.1], "pan": [[0.02, 0], [-0.02, 0]]}})],
        concept=("d3e", "스토아 철학 · 자연을 따르라", "무례도 세상의 일부다", "Shameless men must be in the world"),
        apply=[("e2m_office", ["d3f"]), ("e2m_ceiling", ["d3g"])], tonight=(["그런 사람도 있는 법", "소리 내어 한 번 말하기"], "d3h"),
        teaser=("e2_eyes", "d3i", HALLA, {"flicker": True, "move": {"zoom": [1.1, 1.22]}})),
 4: dict(title="상처받았다는 생각을 내려놓아라", en="Take away thy opinion",
        scene=[("video", "ev2_eyes", ["d4a", "d4b", "m4x"], HALLA, {"flicker": True, "gap": 0.6, "move": {"zoom": [1.0, 1.1]}}),
               ("still", "e2_athenians", ["s_ath2"], HALLA, {"flicker": True, "move": {"zoom": [1.2, 1.32], "pan": [[0.04, 0], [0.06, 0]]}}),
               ("still", "e2_tears", ["d4c"], HALLA, {"flicker": True, "rack": 1.4, "move": {"zoom": [1.0, 1.12]}})],
        mono=("video", "lwv2_front", {"flicker": True, "move": {"zoom": [1.04, 1.1]}}),
        mvoices=["m4a", "m4b", "m4c"], verse=["상처받았다는 생각을 버려라,", "그러면 상처도 사라진다."], src="명상록 4권 7절",
        interp=[("still", "e2_tears", ["d4d"], {"move": {"zoom": [1.3, 1.42], "pan": [[0, -0.03], [0, -0.04]]}, "flicker": True})],
        concept=("d4d", "에픽테토스 · 사실과 판단", "말이 아니라 해석이 아프게 한다", "Take away the opinion"),
        apply=[("e2m_restaurant", ["d4e"]), ("e2m_bed", ["d4f"])], tonight=(["오늘 들은 말 하나", "들은 말과 내가 붙인 해석 나누기"], "d4g"),
        teaser=("e2_prefect", "d4h", TENT, {"move": {"zoom": [1.0, 1.08]}})),
 5: dict(title="경멸은 그의 몫이다", en="Let him look to that",
        scene=[("still", "e2_prefect", ["d5a", "p5"], TENT, {"flicker": True, "gap": 0.5, "move": {"zoom": [1.12, 1.26], "pan": [[-0.04, 0], [-0.06, 0]]}}),
               ("still", "e2a_generals", ["d5b"], TENT, {"move": {"zoom": [1.0, 1.1]}})],
        mono=("video", "lwv3_side", {"flicker": True, "move": {"zoom": [1.0, 1.06]}}),
        mvoices=["m5a", "m5b", "m5c"], verse=["누가 나를 경멸하는가, 그것은 그의 몫이다.", "내 몫은, 경멸받을 일을 하지 않는 것이다."], src="명상록 11권 13절",
        interp=[("still", "e4a_alone", ["d5c"], {"move": {"zoom": [1.0, 1.1]}, "flicker": True})],
        concept=("d5c", "스토아 철학 · 통제의 이분법", "그의 경멸은 그의 몫", "Let him look to that"),
        apply=[("e2m_friend", ["d5d"]), ("e2m_walk", ["d5e"])], tonight=(["누가 뭐라 하든", "부끄럽지 않게 한 일 하나"], "d5f"),
        teaser=("e2_verdict", "d5g", HALLA, {"move": {"zoom": [1.0, 1.08]}})),
 6: dict(title="가장 좋은 복수는 닮지 않는 것", en="Not to become like the wrong doer",
        scene=[("still", "e2_verdict", ["d6a", "d6b"], HALLA, {"flicker": True, "move": {"zoom": [1.1, 1.25]}}),
               ("still", "e2_herodes", ["d6c"], None, {"rack": 1.4, "move": {"zoom": [1.15, 1.28]}, "flicker": True})],
        mono=("video", "lwv2_front", {"flicker": True, "move": {"zoom": [1.0, 1.06]}}),
        mvoices=["m6a", "m6b", "m6c"], verse=["가장 좋은 복수는,", "그와 같아지지 않는 것이다."], src="명상록 6권 6절",
        interp=[("still", "e2_gym", ["d6d"], {"grade": "memory", "leak": True, "move": {"zoom": [1.0, 1.1]}})],
        concept=("d6d", "명상록 6권 20절 · 훈련장의 비유", "할퀸 상대도 원수는 아니다", "As in the gymnasium"),
        apply=[("e2m_phone", ["d6e"]), ("e2m_tea", ["d6f"])], tonight=(["보내려던 날 선 답장", "하루만 묵히기"], "d6g"),
        teaser=("e2_letter", "d6h", TENT2, {"move": {"zoom": [1.0, 1.1]}})),
 7: dict(title="가르치거나, 견디거나", en="Teach them then or bear with them",
        scene=[("still", "e2_letter", ["d7a"], TENT2, {"move": {"zoom": [1.12, 1.24]}, "sfx": [["paper_2.mp3", 0.3, 0.3]]}),
               ("still", "e2_reading", ["d7b", "d7c"], ["wind_1.mp3", 0.2], {"grade": "memory", "leak": True, "move": {"zoom": [1.0, 1.12]}})],
        mono=("video", "lwv3_side", {"flicker": True, "move": {"zoom": [1.04, 1.1]}}),
        mvoices=["m7a", "m7b", "m7c"], verse=["사람은 서로를 위해 존재한다,", "가르치거나, 견디거나."], src="명상록 8권 59절",
        interp=[("still", "lp09_teacher", ["d7d"], {"grade": "memory", "leak": True, "move": {"zoom": [1.0, 1.1]}})],
        concept=("d7d", "스토아 철학 · 공동체", "우리는 서로를 위해 태어났다", "Made for one another"),
        apply=[("e2m_family", ["d7e"]), ("e2m_shoes", ["d7f"])], tonight=(["가르칠 사람 한 명,", "견딜 사람 한 명"], "d7g"),
        teaser=None),
}
MUSIC2 = {1: ("cinematic_5.mp3", 0), 2: ("sad_3.mp3", 0), 3: ("dramatic_1.mp3", 0), 4: ("cinematic_4.mp3", 0), 5: ("cinematic_5.mp3", 90), 6: ("sad_3.mp3", 60), 7: ("cinematic_4.mp3", 110)}


def body(S, sp):
    """EPISODE 오프닝 뒤: 상황 → 문장 I~VII → 정리 → 아웃트로 → 엔딩"""
    sit = len(S)
    S.append(F.shot("still", "e2_sirmium", ["s1"], CAMP, {"tin": "black", "fin": 0.8, "move": {"zoom": [1.0, 1.1]}, "particles": "embers"}))
    S.append(F.shot("still", "e2_athenians", ["s2", "s_ath"], HALLA, {"gap": 0.5, "move": {"zoom": [1.0, 1.12]}, "flicker": True}))
    S.append(F.shot("still", "e2_court", ["s3"], HALLA, {"move": {"zoom": [1.25, 1.4], "pan": [[0, 0.02], [0, 0.03]]}, "flicker": True}))
    S.append(F.shot("still", "e2_sirmium", ["s4"], CAMP, {"move": {"zoom": [1.25, 1.12], "pan": [[0.05, 0], [0.03, 0]]}}))
    s5 = F.shot("still", "lp01_camp", ["s5"], CAMP, {"move": {"zoom": [1.0, 1.08]}}); s5.update({"tout": "black", "fout": 0.8, "post": 1.4}); S.append(s5)
    card = {}
    for n in range(1, 8):
        card[n] = len(S); S += F.chapter(n, CH2[n])
    rec = len(S)
    S.append({"type": "recap", "items": ["아침마다 미리 각오하라", "그가 무엇을 옳다고 믿었는지 보라", "무례한 사람이 없는 세상은 없다", "상처받았다는 생각을 내려놓아라",
                                         "경멸은 그의 몫이다", "가장 좋은 복수는, 닮지 않는 것", "가르치거나, 견디거나"],
              "voice": ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8"], "gap": 0.8, "pre": 0.8, "post": 1.0, "recap_offset": 1, "nocap": True, "head_en": "SEVEN LINES FOR THE RUDE AND THE UNGRATEFUL",
              "sfx": [["transition_5.mp3", 0.0, 0.35]], "tin": "black", "fin": 1.0})
    S.append(F.shot("still", "e2_morning", ["r9"], ["wind_2.mp3", 0.25], {"move": {"zoom": [1.18, 1.0]}, "post": 1.6, "tin": "dissolve"}))
    out = len(S)
    S.append({"type": "outro", "voice": ["o1", "o2"], "gap": 0.7, "pre": 1.0, "post": 2.6, "dur": 12.0, "nocap": True,
              "next_kicker": "NEXT  ·  EPISODE 3", "next": "아무도 알아주지 않을 때", "slogan_at": 999, "tap_sub": 3.4, "tap_like": 4.2,
              "sfx": [["ring_synth.wav", 3.42, 0.45], ["click_2.mp3", 3.4, 0.6], ["click_2.mp3", 4.2, 0.6], ["ring_synth.wav", 4.22, 0.35], ["drum_6.mp3", 0.2, 0.4]]})
    S.append({"type": "end", "dur": 7.5, "voice": ["m_x1", "e_x2"], "pre": 0.9, "gap": 0.9, "post": 2.6, "nocap": True, "slogan": "매일 밤, 황제처럼 생각하라", "tin": "black",
              "sfx": [["ring_synth.wav", 0.5, 0.25]]})
    for x in S[sit:]:   # 1편에서 배운 점: 펜 소리는 펜 영상에만, 오늘 밤 카드는 자막 없이
        if x.get("src") not in ("lwv3_side", "lwv2_front") and x.get("sfx"): x["sfx"] = [f for f in x["sfx"] if f[0] != "paper_6.mp3"]
        if x.get("type") == "tonight": x["nocap"] = True; x["sfx"] = []
    mus = [{"file": "cinematic_0.mp3", "at_shot": sit, "offset": 0.5, "start": 0, "until_shot": card[1], "vol": 0.22, "fin": 3, "fout": 3}]
    for n in range(1, 8):
        f, st = MUSIC2[n]; nxt = card[n + 1] if n < 7 else rec
        mus.append({"file": f, "at_shot": card[n], "offset": 1.0, "start": st, "until_shot": nxt, "vol": 0.2, "fin": 3, "fout": 3})
    mus.append({"file": "sad_5.mp3", "at_shot": rec, "offset": 0.5, "start": 0, "until_shot": out + 2, "tail": 0, "vol": 0.22, "fin": 2, "fout": 4})
    sp["music"] = mus
    print("카드", card, "정리", rec, "아웃트로", out)


def build():
    base = json.load(open(os.path.join(HERE, "spec_ep01.json")))
    sp = {k: copy.deepcopy(base[k]) for k in ("root", "gen_dir", "sfx_dir", "music_dir", "out_dir", "intro", "monologue_fx", "voice_gain")}
    sp["id"] = "edl_ep02"; sp["voice_dir"] = "social/side/voice_samples/ep02"
    names = sorted(os.listdir(os.path.join(E.ROOT, sp["voice_dir"]))) if os.path.isdir(os.path.join(E.ROOT, sp["voice_dir"])) else []
    vf = {}
    for n in names:   # voice_ep02_07_h1.mp3 → h1
        stem = n[:-4].split("_", 3)[-1]; vf[stem] = n
    for n, who, t in E.HOOK:   # 조연 대사는 오디션에서 고른 사람의 녹음을 쓴다
        if who == "HERODES": vf[n] = vf.get(f"a_her_{CAST['HERODES']}")
    vf["p3"] = vf.get(f"a_pref_{CAST['PREFECT']}"); vf["h3"] = vf.get(f"a_her2_{CAST['HERODES']}")
    d2 = os.path.join(E.ROOT, "social/side/voice_samples", E.TAG2)
    for n in (sorted(os.listdir(d2)) if os.path.isdir(d2) else []):   # 본편 녹음 (voice_ep02b_NN_이름.mp3)
        if n.endswith(".mp3"): vf[n[:-4].split("_", 3)[-1]] = f"../{E.TAG2}/{n}"
    vf["m_x1"] = "../lp3/voice_lp3_07_m_x1.mp3"; vf["e_x2"] = "../ep01x/voice_ep01x_01_e_x2.mp3"   # 엔딩(1편과 같은 녹음)
    sp["voice_files"] = vf
    ALL = E.HOOK + E.LINES2
    sp["subs"] = {n: subs_of(t, v) for n, v, t in ALL}
    sp["subs"]["m4x"] = "“변론을, 계속하시오.”"
    sp["monologue_voices"] = [n for n, v, t in ALL if v == E.M] + ["m_x1"]
    sp["voice_gain"] = {**sp.get("voice_gain", {}), "mono": 3.8, "narr": 1.2, "cast": 0.85}   # 11/4 대표: 노인보다 해설·황제가 작게 들림
    S = []
    S.append({"type": "black", "dur": 0.8, "fixed": True, "amb": ["wind_6.mp3", 0.4]})
    # 훅: 물방울 → 고함 → 해설 → 칼 → 황제의 눈(독백)
    S.append({"type": "video", "src": "ev2_clock", "dur": 2.6, "fixed": True, "move": {"zoom": [1.0, 1.06]}, "amb": ["night_2.mp3", 0.25], "tin": "black", "fin": 0.8, "sfx": [["water_drip.wav", 0.55, 0.32], ["water_drip.wav", 1.85, 0.26]],
              "overlays": [{"kind": "caption", "text": "기원후 2세기 · 판노니아 시르미움, 황제의 법정", "at": 0.3}]})
    S.append({"type": "video", "src": "ev2_court", "voice": ["h_her", "h1"], "pre": 0.15, "gap": 0.6, "post": 0.4, "move": {"zoom": [1.0, 1.1]}, "flicker": True,
              "amb": ["fire_4.mp3", 0.4], "sfx": [["impact_5.mp3", 0.1, 0.5], ["whoosh_0.mp3", 0.0, 0.3]]})
    S.append({"type": "video", "src": "ev2_sword", "voice": ["h2"], "pre": 0.3, "post": 0.4, "move": {"zoom": [1.0, 1.08]}, "flicker": True, "tin": "flash",
              "amb": ["fire_0.mp3", 0.3], "sfx": []})
    S.append({"type": "video", "src": "ev2_eyes", "voice": ["m_h1", "m_h2"], "pre": 0.5, "gap": 1.0, "post": 0.9, "move": {"zoom": [1.04, 1.16]}, "flicker": True,
              "sfx": [["heartbeat_5.mp3", 0.1, 0.9], ["heartbeat_5.mp3", 0.9, 0.6], ["heartbeat_5.mp3", 1.7, 0.35]], "tout": "black", "fout": 1.0})
    S.append({"type": "black", "dur": 0.4, "fixed": True})
    intro = [s for s in base["shots"] if s["type"] == "intro"][0]; intro = copy.deepcopy(intro)
    # 11/4 대표: 인트로 효과음 박자 — 각 소리의 '가장 큰 순간'을 그림에 맞춘다 (금빛 원 0.8~2.6, 주화 2.4, 충격 4.0, 영문 제목 5.0, 사라짐 9.6~10.2)
    intro["sfx"] = [["paper_6.mp3", 0.8, 0.9], ["cinematic_6.mp3", 1.47, 0.7], ["ring_synth.wav", 2.4, 0.5], ["drum_5.mp3", 3.92, 1.0],
                    ["impact_2.mp3", 3.02, 0.8], ["cinematic_4.mp3", 4.9, 0.55], ["transition_5.mp3", 8.96, 0.5]]
    S.append(intro)
    S.append({"type": "episode", "num": 2, "title": "무례한 사람들", "en": "The Rude and the Ungrateful", "dur": 4.6, "fixed": True,
              "amb": ["wind_2.mp3", 0.3], "sfx": [["drum_6.mp3", 0.3, 0.45]], "tout": "black", "fout": 0.8})
    body(S, sp)
    sp["shots"] = S
    sp["cast_voices"] = [n for n, v, t in ALL if v not in (E.G, E.M)]
    json.dump(sp, open(os.path.join(HERE, "spec_ep02.json"), "w"), ensure_ascii=False, indent=1)
    print("장면", len(S), "목소리", len(vf))
