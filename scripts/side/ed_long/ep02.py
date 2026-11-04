"""황제의 일기 EPISODE 2 · 무례한 사람들 — 대본·촬영표 (2026-11-04)
python3 ep02.py gen [part]   → scripts/side/gen/EDL261104-ep02<part>.json (그림·영상) + scripts/side/voices_req.json (녹음)
python3 ep02.py spec         → scripts/side/ed_long/spec_ep02.json (렌더 설정)
1차(part=h): 훅 + 인트로 + EPISODE 2 오프닝만 먼저 (대표 11/4: "인트로만 먼저 렌더링")
목소리: 해설 건석 / 황제 명일 / 노학자 헤로데스 = 종대(tc_67e38d8c771b5511659c4534, 노년 남성, 장면 대사만 angry)
        근위대장 바사이우스 = 대진(tc_6a0e85a97f7750959b970d5d) — 2편 문장 V 에서 사용. 조연은 Claude 가 골라 쓰기로 함(11/4 대표)
기획안: Claude Docs 「황제의 일기 EPISODE 2 · 무례한 사람들 기획안」 — 개연성 표(같은 사실은 한 번만, 시간은 앞으로만)를 대본과 대조할 것
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
from ep01 import STYLE, VT, EMP   # 1편과 같은 화풍·영상 규칙·황제 묘사

G = "tc_6731b2e0855f351b98d30c48"    # 건석 (해설)
M = "tc_62d66c2d1523be99355fda02"    # 명일 (황제)
HER = "tc_67e38d8c771b5511659c4534"  # 종대 → 헤로데스 아티쿠스 (노학자)
BAS = "tc_6a0e85a97f7750959b970d5d"  # 대진 → 근위대장 바사이우스
HER_ALT = {"Deokhwan": "tc_66860d458ca8b2dc5f72b865", "Hakchul": "tc_63a3d9d14b235ddd6541a78e", "Joonghyun": "tc_61cd3cc126463f411925e8a6"}
FACE = "his face clearly visible and well lit from the side by warm torchlight, natural realistic facial proportions"
HERODES = ("an old Greek scholar about seventy-five with a long white beard and thin white hair, deep-set eyes, wearing a pale cream himation over a tunic, "
           "a heavy gold signet ring, " + FACE)

IMAGES = {
 # 훅
 "e2_court": ("Inside a torch-lit Roman basilica courtroom in a frontier military town at night, " + HERODES + ", standing in the middle of the floor and pointing an accusing finger "
              "up toward a raised imperial judgment seat at the right edge of the frame, his face twisted with grief and fury, mouth open as if shouting; behind him a small delegation "
              "of Athenian men in white togas stepping back in shock; Roman guards in bronze armor along the stone walls; a tall bronze water clock on a stand in the left foreground.", STYLE),
 "e2_sword": ("Tight close-up of a Roman praetorian prefect's armored right hand gripping the hilt of a gladius at his hip, the blade drawn a third of the way out of its scabbard, "
              "red wool cloak and bronze cuirass, torchlight glinting along the steel, the courtroom behind melting into soft dark blur.", STYLE),
 "e2_eyes": ("Close-up portrait of " + EMP + ", seated on a raised wooden judgment seat in a torch-lit Roman courtroom, " + FACE + ", calm steady eyes looking down at someone "
             "off-screen to the left, no anger at all, only a faint sadness, very shallow depth of field, the dark hall behind him.", STYLE),
}
VIDEOS = {
 "ev2_court": ("e2_court", "The old scholar shouts and jabs his finger toward the judgment seat, his white beard trembling with rage; the men behind him flinch back a step; torches flicker."),
 "ev2_sword": ("e2_sword", "The armored hand slowly draws the sword a little further out of the scabbard, then stops and holds still; torchlight slides along the blade."),
 "ev2_eyes": ("e2_eyes", "The emperor blinks once slowly and keeps looking steadily ahead, his calm expression unchanged; warm torchlight flickers softly across his face."),
}

# (이름, 목소리, 대사, 감정) — '!' 로 시작하면 강조 자막
LINES_H = [
 ("x_h1", HER, "이것이, 내가 루키우스를 대접한 보답입니까!", "angry"),
 ("h1", G, "로마 황제 앞에서, 한 노인이 소리쳤습니다.", None),
 ("h2", G, "법정에 있던 모두가, 피를 보게 될 거라고 생각했습니다.", None),
 ("m_h1", M, "오늘 나는, 무례한 사람을 만날 것이다.", None),
 ("m_h2", M, "!나는 그것을, 이미 알고 있었다.", None),
 ("h3", G, "황제는 화를 내지 않았습니다. 그 이유는, 그의 일기 둘째 권 첫머리에 적혀 있습니다.", None),
]
# 조연 목소리 후보 샘플(같은 대사) — 대표가 바꾸고 싶을 때 들어 보도록 저장만 해 둔다
SAMPLES = [("cand_her_" + k, v, "이것이, 내가 루키우스를 대접한 보답입니까!", "angry") for k, v in HER_ALT.items()] + [
           ("cand_bas_daejin", BAS, "헤로데스, 죽고 싶은 모양이군.", None), ("cand_bas_sungho", "tc_5fe06471a9f79e8f959be96f", "헤로데스, 죽고 싶은 모양이군.", None)]


def clean(t): return t.lstrip("!")


def gen(part="h"):
    jobs = []
    for k, (p, st) in IMAGES.items():
        jobs.append({"id": k, "kind": "image", "endpoint": "xai/grok-imagine-image-2.0", "body": {"aspect_ratio": "16:9", "prompt": p + " " + st}})
    for k, (src, p) in VIDEOS.items():
        jobs.append({"id": k, "kind": "video", "endpoint": "alibaba/wan-3.0/image-to-video", "image": f"social/side/gen/{src}.jpeg", "body": {"duration": 5, "prompt": p + " " + VT}})
    json.dump(jobs, open(os.path.join(ROOT, f"scripts/side/gen/EDL261104-ep02{part}.json"), "w"), ensure_ascii=False, indent=1)
    V = []
    for n, v, t, emo in LINES_H + SAMPLES:
        V.append({"name": n, "id": v, "line": clean(t), "emotion": emo or "tonedown", "tempo": 0.85 if v == M else 1.0})
    json.dump({"requested": "2026-11-04T10:40", "note": "황제의 일기 EPISODE 2 훅 녹음 + 조연(노학자·근위대장) 후보 샘플", "tag": "ep02h", "keep": True, "lang": "kor",
               "model": "ssfm-v30", "emotion": "tonedown", "tempo": 1.0, "voices": V}, open(os.path.join(ROOT, "scripts/side/voices_req.json"), "w"), ensure_ascii=False, indent=1)
    print(len(jobs), "생성 작업,", len(V), "줄 녹음")


if __name__ == "__main__":
    if sys.argv[1] == "gen": gen(*(sys.argv[2:3] or ["h"]))
    else:
        import ep02_spec; ep02_spec.build()
