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
    sp["voice_gain"] = {**sp.get("voice_gain", {}), "cast": 1.25}
    S = []
    S.append({"type": "black", "dur": 0.8, "fixed": True, "amb": ["wind_6.mp3", 0.4]})
    # 훅: 물방울 → 고함 → 해설 → 칼 → 황제의 눈(독백)
    S.append({"type": "video", "src": "ev2_clock", "dur": 2.6, "fixed": True, "move": {"zoom": [1.0, 1.06]}, "amb": ["night_2.mp3", 0.25], "tin": "black", "fin": 0.8,
              "overlays": [{"kind": "caption", "text": "기원후 2세기 · 판노니아 시르미움, 황제의 법정", "at": 0.3}]})
    S.append({"type": "video", "src": "ev2_court", "voice": ["h_her", "h1"], "pre": 0.15, "gap": 0.6, "post": 0.4, "move": {"zoom": [1.0, 1.1]}, "flicker": True,
              "amb": ["fire_4.mp3", 0.4], "sfx": [["impact_5.mp3", 0.1, 0.5], ["whoosh_0.mp3", 0.0, 0.3]]})
    S.append({"type": "video", "src": "ev2_sword", "voice": ["h2"], "pre": 0.3, "post": 0.4, "move": {"zoom": [1.0, 1.08]}, "flicker": True, "tin": "flash",
              "amb": ["fire_0.mp3", 0.3], "sfx": [["swords_2.mp3", 0.25, 0.55]]})
    S.append({"type": "video", "src": "ev2_eyes", "voice": ["m_h1", "m_h2"], "pre": 0.5, "gap": 1.0, "post": 0.9, "move": {"zoom": [1.04, 1.16]}, "flicker": True,
              "sfx": [["heartbeat_5.mp3", 0.1, 0.9], ["heartbeat_5.mp3", 0.9, 0.6], ["heartbeat_5.mp3", 1.7, 0.35]], "tout": "black", "fout": 1.0})
    S.append({"type": "black", "dur": 0.4, "fixed": True})
    intro = [s for s in base["shots"] if s["type"] == "intro"][0]; S.append(copy.deepcopy(intro))
    S.append({"type": "episode", "num": 2, "title": "무례한 사람들", "en": "The Rude and the Ungrateful", "dur": 4.6, "fixed": True,
              "amb": ["wind_2.mp3", 0.3], "sfx": [["drum_6.mp3", 0.3, 0.45]], "tout": "black", "fout": 0.8})
    sp["shots"] = S
    sp["cast_voices"] = [n for n, v, t in E.HOOK if v not in (E.G, E.M)]
    sp["music"] = []
    json.dump(sp, open(os.path.join(HERE, "spec_ep02.json"), "w"), ensure_ascii=False, indent=1)
    print("장면", len(S), "목소리", len(vf))
