"""황제의 일기 EPISODE 2 · 무례한 사람들 — 대본·촬영표 (2026-11-04)
python3 ep02.py gen     → scripts/side/gen/EDL261104-ep02.json (그림·영상) + scripts/side/voices_req.json (녹음)
python3 ep02.py spec    → scripts/side/ed_long/spec_ep02.json (렌더 설정)
기획안: Claude Docs 「황제의 일기 EPISODE 2 · 무례한 사람들 기획안」
1단계(11/4): 훅 + 인트로 + EPISODE 2 오프닝만. 조연 목소리(헤로데스·근위대장)는 후보를 함께 녹음해 고른다.
대본 규칙은 1편과 같다: '!' = 가운데 큰 금색 강조 자막, 해설=건석(존댓말), 독백=명일(1인칭 반말).
"""
import json, os, sys, copy

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
from ep01 import STYLE, MOD, MEMO, EMP, VT, G, M   # 1편과 같은 화풍·황제 외모·목소리

TAG = "ep02"
# 조연 목소리 후보 (11/4 대표: 조연은 Claude 가 골라도 됨). 오디션 녹음 뒤 CAST 에 고른 것을 둔다
HERODES_CAND = {"jongdae": "tc_67e38d8c771b5511659c4534", "kwonil": "tc_675a73eb789ff3ea6cc80235", "deokhwan": "tc_66860d458ca8b2dc5f72b865",
                "zeus": "tc_6a5882fe54564e2a06a218bb", "poseidon": "tc_6a8f9d53322676d2f0934a21"}
PREFECT_CAND = {"wangkwon": "tc_66a1ea9420b813b5c36197f1", "junseong": "tc_66e26710ac44cf7c7ebfdb71", "hades": "tc_6a867e6bd49b8f6a07db59da"}

HER = ("an elderly Greek scholar of about seventy-three, long flowing white beard, thin white curly hair, gaunt hollow cheeks, red-rimmed grief-stricken eyes, "
       "white wool himation with a thin purple border over a pale tunic")
HALL = ("a torch-lit Roman imperial tribunal hall in the frontier city of Sirmium, rough stone walls hung with dark red banners, a raised stone dais at the far end")
PREF = "a Roman praetorian prefect in polished bronze muscle armor and a dark purple cloak, close-cropped grey hair, hard square jaw"

IMAGES = {
 "e2_clock": ("Extreme close-up of an ancient Roman water clock (clepsydra) on a stone pedestal in " + HALL + ": a bronze spout above a clear glass-and-bronze vessel, "
              "a single bright drop of water falling, the rest of the hall melting into deep dark blur, torchlight glinting on the water.", STYLE),
 "e2_court": ("Wide dramatic shot inside " + HALL + ": in the centre of the floor " + HER + " stands with his right arm stretched out, pointing furiously toward the dais, mouth open as if shouting; "
              "on the left a group of Athenian delegates in white togas recoil; along the walls Roman guards with tall shields; at the far end on the dais " + EMP +
              " sits very still on a curule chair, small in the distance, his face in shadow. Tense frozen moment, torch smoke in the air.", STYLE),
 "e2_sword": ("Tight close-up at waist height of " + PREF + ": his right hand in a leather bracer gripping the ivory hilt of a gladius and drawing it a hand's width out of a bronze-fitted scabbard, "
              "the steel blade catching torchlight, the blurred white figure of an old man in the background beyond.", STYLE),
 "e2_eyes": ("Intimate close-up portrait of " + EMP + " seated on the imperial dais, his face fully visible and clearly lit by a warm torch from the side, calm steady eyes looking straight ahead "
             "at someone off-camera, not angry, a faint sadness, absolutely still, deep shadow behind him.", STYLE),
}
VIDEOS = {
 "ev2_clock": ("e2_clock", "A single drop of water falls slowly from the bronze spout into the vessel and makes small ripples; the torchlight flickers softly."),
 "ev2_court": ("e2_court", "The old man shakes his outstretched arm and shouts toward the dais, his beard trembling; the delegates lean back; torch flames waver; the emperor stays completely still."),
 "ev2_sword": ("e2_sword", "The hand slowly slides the blade a little further out of the scabbard and stops, knuckles tightening; torchlight runs along the steel."),
 "ev2_eyes": ("e2_eyes", "The emperor blinks once slowly and keeps looking ahead with calm eyes; the torchlight flickers across his face; very slow push-in."),
}

HOOK = [   # (이름, 목소리, 대사)
 ("h_her", "HERODES", "이것이, 루키우스를 대접한 대가입니까!"),
 ("h1", G, "로마 황제 앞에서, 한 노인이 소리쳤습니다."),
 ("h2", G, "근위대장의 손이, 칼자루로 갔습니다. 법정의 모두가, 피를 볼 거라고 생각했습니다."),
 ("m_h1", M, "오늘 나는, 무례한 사람을 만날 것이다."),
 ("m_h2", M, "!나는 그것을, 이미 알고 있었다."),
]
AUDITION = [("her", "HERODES", "이것이, 루키우스를 대접한 대가입니까!", "angry"),
            ("her2", "HERODES", "늙은이는, 두려운 것이 별로 없소.", "tonedown"),
            ("pref", "PREFECT", "죽고 싶은 모양이군.", "tonedown")]


def clean(t): return t.lstrip("!")


def gen():
    jobs = []
    for k, (p, st) in IMAGES.items():
        jobs.append({"id": k, "kind": "image", "endpoint": "xai/grok-imagine-image-2.0", "body": {"aspect_ratio": "16:9", "prompt": p + " " + st}})
    for k, (src, p) in VIDEOS.items():
        jobs.append({"id": k, "kind": "video", "endpoint": "alibaba/wan-3.0/image-to-video", "image": f"social/side/gen/{src}.jpeg", "body": {"duration": 5, "prompt": p + " " + VT}})
    json.dump(jobs, open(os.path.join(ROOT, "scripts/side/gen/EDL261104-ep02.json"), "w"), ensure_ascii=False, indent=1)
    V = [{"name": n, "id": v, "line": clean(t), "emotion": "tonedown", "tempo": 0.85 if v == M else 1.0} for n, v, t in HOOK if v in (G, M)]
    for key, who, line, emo in AUDITION:   # 조연 오디션: 후보마다 같은 대사
        for nm, vid in (HERODES_CAND if who == "HERODES" else PREFECT_CAND).items():
            V.append({"name": f"a_{key}_{nm}", "id": vid, "line": line, "emotion": emo, "tempo": 1.0})
    json.dump({"requested": "2026-11-04T10:10", "note": "황제의 일기 EPISODE 2 훅 녹음 + 조연(헤로데스·근위대장) 오디션", "tag": TAG, "keep": True, "lang": "kor",
               "model": "ssfm-v30", "emotion": "tonedown", "tempo": 1.0, "voices": V}, open(os.path.join(ROOT, "scripts/side/voices_req.json"), "w"), ensure_ascii=False, indent=1)
    print(len(jobs), "생성 작업,", len(V), "줄 녹음")


if __name__ == "__main__":
    if sys.argv[1] == "gen": gen()
    else:
        import ep02_spec; ep02_spec.build()
