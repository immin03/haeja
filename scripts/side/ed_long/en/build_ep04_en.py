"""Build the English spec for EPISODE 4 (The Night He Lost Her) from the finished Korean spec ../spec_ep04.json + ep04_en.json.
Owner 2026-11-13 00:27 KST: English long-form, one a day, from the Korean back catalogue.
Same shots, clips, sound and music as the Korean cut. Changes: voices (ep04en1/ep04en2 voice-fast runs), subtitles, every on-screen text,
modern scenes → Western images (e4en_*), finale → English end card v2 (same as cine_ep01_en).
python3 build_ep04_en.py  → en/spec_ep04_en.json  (fails if any Hangul is left in subs/shots)
"""
import json, os, re, copy, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ED = os.path.dirname(HERE); ROOT = os.path.abspath(os.path.join(ED, "..", "..", ".."))
sys.path.insert(0, ED)
import ep04 as K
E = json.load(open(os.path.join(HERE, "ep04_en.json"))); T = E["strings"]
S = json.load(open(os.path.join(ED, "spec_ep04.json")))
VD = ["ep04en1", "ep04en2"]

# 1) voices: every Korean line name → the English take
vf = {}
for d in VD:
    p = os.path.join(ROOT, "social/side/voice_samples", d)
    for f in sorted(os.listdir(p)):
        if f.endswith(".mp3"): vf[f[:-4].split("_", 3)[-1]] = "../" + d + "/" + f
need = [n for n, _, _ in K.HOOK + K.LINES]
miss = [n for n in need if n not in vf]
if miss: raise SystemExit("missing English takes: " + ", ".join(miss))
vf["endA"] = "../cep01en5/voice_cep01en5_99_endA.mp3"   # English end card text A (Ron), same as cine_ep01_en
vf["o1"] = "../cep01en3/voice_cep01en3_24_o1.mp3"        # "Think like an emperor, every night. The Emperor's Diary." — same slogan take on every episode
S["voice_dir"] = "social/side/voice_samples/" + VD[0]; S["root"] = "../../../.."
S["voice_files"] = {k: v for k, v in vf.items()}

# 2) subtitles
who = {n: v for n, v, _ in K.HOOK + K.LINES}
def subs_of(t, v):
    emph = t.startswith("!"); t = t.lstrip("!")
    if v not in (K.G, K.M): return "“" + t + "”"
    parts = [x for x in re.split(r"(?<=[.?!])\s+", t) if x]
    return [("!" + x if emph else x) for x in parts] if len(parts) > 1 else ("!" + t if emph else t)
S["subs"] = {n: subs_of(E["lines"][n], who[n]) for n in need if n not in ("o1", "o2")}
S["monologue_voices"] = [n for n in need if who[n] == K.M]

# 3) on-screen text
KO_NOW = ["지금 · 어느 늦은 밤", "지금 · 남편이 떠난 집", "지금 · 강아지가 떠난 저녁", "지금 · 출근길", "지금 · 엄마가 떠난 뒤"]
KO_BACK = ["다시, 그날 밤 · 할랄라의 막사", "다음 날 아침 · 로마에서 온 편지", "며칠 뒤 · 마을 밖 언덕", "장례 다음 날 새벽 · 할랄라", "몇 달 뒤 · 파우스티노폴리스"]
CAP = {"기원후 175년 겨울 · 카파도키아, 할랄라": T["hook_caption"], "몇 달 전 · 기원후 175년 봄": T["sit_caption"]}
for i in range(5): CAP[KO_NOW[i]] = T["NOW"][str(i + 1)]; CAP[KO_BACK[i]] = T["BACK"][str(i + 1)]
CH = T["chapters"]; card_n = 0; verse_n = 0; concept_n = 0; recap_n = 0
for sh in S["shots"]:
    if sh.get("src") in E["modern_images"]: sh["src"] = E["modern_images"][sh["src"]]
    for ov in sh.get("overlays", []):
        if ov.get("kind") == "caption": ov["text"] = CAP[ov["text"]]
        elif ov.get("kind") == "verse":
            verse_n += 1; c = CH[str(verse_n)]; ov["lines"] = c["verse"]; ov["src"] = c["src"]
        elif ov.get("kind") == "concept":
            concept_n += 1; c = CH[str(concept_n)]; ov["kicker"] = c["kicker"]; ov["lines"] = [c["concept"]]
    t = sh.get("type")
    if t == "card":
        card_n += 1; sh["title"] = CH[str(card_n)]["title"]
    elif t == "episode":
        sh["title"] = T["episode_title"]; sh["en"] = T["episode_en"]
    elif t == "recap":
        recap_n += 1
        if recap_n == 1: sh["items"] = T["recap_items"]; sh["head"] = T["recap_head"]
        else: sh["items"] = T["tonight_items"]; sh["head"] = T["tonight_head"]
    elif t == "finale":   # English end card v2 (owner 2026-11-11 approved for cine_ep01_en): slogan o1 + ending text A
        sh.pop("prev_kicker", None)
        sh.update({"dur": 18.0, "voice": ["o1", "endA"], "endcard": "v2", "pre": 0.8, "gap": 0.9, "post": 2.6,
                   "slogan": "Think like an emperor, every night.", "brand_ko": "Marcus Aurelius  ·  Meditations", "cta": "See you in the next story"})
assert card_n == 5 and verse_n == 5 and concept_n == 5 and recap_n == 2, (card_n, verse_n, concept_n, recap_n)
S["id"] = "edl_ep04_en"
gen = os.path.join(ROOT, "social/side/gen")
for v in E["modern_images"].values():
    if not any(os.path.exists(os.path.join(gen, v + e)) for e in (".jpeg", ".jpg", ".png")): raise SystemExit("modern image missing: " + v)
out = os.path.join(HERE, "spec_ep04_en.json")
json.dump(S, open(out, "w"), ensure_ascii=False, indent=1)
bad = sorted({x for x in json.dumps({k: S[k] for k in ("subs", "shots", "intro")}, ensure_ascii=False).split('"') if re.search(r"[가-힣]", x)})
if bad: raise SystemExit("Korean strings left: " + " | ".join(bad[:12]))
print(out, len(S["shots"]), "shots", len(S["voice_files"]), "voices")
