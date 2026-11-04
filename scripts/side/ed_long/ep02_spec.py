"""EPISODE 2 렌더 설정 만들기 — 1편 설정(spec_ep01.json)의 공통 값(인트로·자막·목소리 크기)을 물려받는다 (2026-11-04)
1단계: 훅 + 인트로 + EPISODE 2 오프닝"""
import json, os, copy, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ep02 as E

CAST = {"HERODES": "jongdae", "PREFECT": "wangkwon"}   # 오디션 뒤 확정 (조연은 Claude 가 고름)


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
    sp["voice_files"] = vf
    sp["subs"] = {n: (f"“{t}”" if v not in (E.G, E.M) else t) for n, v, t in E.HOOK}   # 조연 대사는 따옴표로
    sp["monologue_voices"] = [n for n, v, t in E.HOOK if v == E.M]
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
    sp["shots"] = S
    sp["cast_voices"] = [n for n, v, t in E.HOOK if v not in (E.G, E.M)]
    sp["music"] = []
    json.dump(sp, open(os.path.join(HERE, "spec_ep02.json"), "w"), ensure_ascii=False, indent=1)
    print("장면", len(S), "목소리", len(vf))
