"""Build the English spec for cine_ep01 (The Emperor's Diary EN) from the Korean episode code (../cine_ep01.py) + cine_ep01_en.json.
Same shots, clips, sound design and music as the Korean cut; only the voice files, subtitles, on-screen text and the modern (현실판) stills change.
Voices: social/side/voice_samples/cep01en1..3 (voice-fast runs, names l000.., n1..n5, o1, o2). Output: en/spec_cine_ep01_en.json
python3 build_cine_ep01_en.py
"""
import json, os, sys, types

HERE = os.path.dirname(os.path.abspath(__file__)); ED = os.path.dirname(HERE)
sys.path.insert(0, ED)
E = json.load(open(os.path.join(HERE, "cine_ep01_en.json")))
VD = ["cep01en1", "cep01en2", "cep01en3"]

src = open(os.path.join(ED, "cine_ep01.py"), encoding="utf-8").read()
rep = [
    ('TAG = "cep01"', f'TAG = "{VD[0]}"'),
    ('d2 = "social/side/voice_samples/cep01b"\n    for f in sorted(os.listdir(os.path.join(ROOT, d2))):\n        if f.endswith(".mp3"):\n            n = f[:-4].split("_", 3)[-1]; vf[n] = "../cep01b/" + f',
     '\n'.join(['for dd2 in ' + repr(VD[1:]) + ':',
                '        for f in sorted(os.listdir(os.path.join(ROOT, "social/side/voice_samples", dd2))):',
                '            if f.endswith(".mp3"): vf[f[:-4].split("_")[-1]] = "../" + dd2 + "/" + f'])),
    ('for dd in ("cep01c", "cep01d", "cep01e", "cep01f", "cep01g", "cep01h"):', 'for dd in ():'),
    ('vf["l026"] = vf["cas_" + CAS_PICK]', 'pass'),
    ('"head": "뒤통수 친 사람을 이기는 3가지 방법", "head_en": "THREE WAYS"', '"head": ' + json.dumps(E["screens"]["recap"]["head"]) + ', "head_en": "THREE WAYS"'),
    ('"voice": ["o1", "q5"]', '"voice": ["o1", "o2"]'),
    ('"slogan": "매일 밤, 황제처럼 생각하라", "brand_ko": "황제의 일기  ·  명상록 실화극", "cta": "명상록 실화극  ·  다음 이야기에서 뵙겠습니다"',
     '"slogan": ' + json.dumps(E["screens"]["finale"]["slogan"]) + ', "brand_ko": ' + json.dumps(E["screens"]["finale"]["brand"]) + ', "cta": ' + json.dumps(E["screens"]["finale"]["cta"])),
    ('"ko": "황제의 일기  :  명상록 실화극", "series": "배신 편"', '"ko": "True Stories from the Meditations", "series": "BETRAYAL"'),
    ('S = {"id": "cine_ep01"', 'S = {"id": "cine_ep01_en"'),
    ('open(os.path.join(HERE, "spec_cine_ep01.json"), "w")', 'open(OUT_SPEC, "w")'),
]
for a, b in rep:
    assert a in src, "pattern not found: " + a[:60]
    src = src.replace(a, b)
src = src.replace('if __name__ == "__main__":', 'if __name__ == "__main_disabled__":')
m = types.ModuleType("cine_ep01_en"); m.__file__ = os.path.join(ED, "cine_ep01.py"); m.OUT_SPEC = os.path.join(HERE, "spec_cine_ep01_en.json")
exec(compile(src, m.__file__, "exec"), m.__dict__)

# English lines (same order/index as the Korean L)
for k, (role, txt) in E["lines"].items():
    i = int(k); clip, v, t, o = m.L[i]
    assert v, f"line {i} has no voice in Korean L"
    m.L[i] = (clip, v, txt, o)
for i, (clip, v, t, o) in enumerate(m.L):
    if v and str(i) not in E["lines"]: raise SystemExit(f"missing English line {i}: {t}")
for k, (role, txt) in E["insert"].items(): m.NEWV[k] = txt
m.ENDS[:] = E["screens"]["recap"]["items"]
vs = E["screens"]["finale_verses"]; vi = iter(vs)
m.MV[:] = [(a, b, ((next(vi)["lines"], None) if c else None)) for a, b, c in m.MV]
vi = iter(vs)
m.MV[:] = [(a, b, ((c[0], next(vi)["src"]) if c else None)) for a, b, c in m.MV]
m.spec()

S = json.load(open(m.OUT_SPEC))
gen = os.path.join(m.ROOT, "social/side/gen")
for sh in S["shots"]:
    s = sh.get("src") or ""
    if s.startswith("cep1i_m") or s.startswith("cep1_m"):   # 현실판: Western people (cep1en_m1..3)
        k = s.split("_")[-1]
        new = "cep1en_" + ("m" + k[1] if k.startswith("m") else k)
        if not any(os.path.exists(os.path.join(gen, new + e)) for e in (".jpeg", ".jpg", ".png", ".webp")): raise SystemExit("modern image missing: " + new)
        sh["src"] = new; sh["type"] = "still"
S["voice_dir"] = "social/side/voice_samples/" + VD[0]
json.dump(S, open(m.OUT_SPEC, "w"), ensure_ascii=False, indent=1)
import re
bad = [x for x in json.dumps({k: S[k] for k in ("subs", "shots", "intro")}, ensure_ascii=False).split('"') if re.search(r"[가-힣]", x)]
print("Korean strings left in spec:", bad[:10])
print(len(S["shots"]), "shots", len(S["voice_files"]), "voices")
