"""명상록 실화극 시안 (2026-11-09 대표: 훅 + 인트로 + 대화 약 1분) — 대본·촬영표
python3 cine01.py gen   → scripts/side/gen/EDL261109-cine01.json(그림) + scripts/side/voices_req.json(녹음)
python3 cine01.py genv N → scripts/side/gen/EDL261109-cine01vN.json(영상 N묶음, 회차 상한 3달러 안)

사실: 문서 상자를 읽지 않고 태움(카시우스 디오 72권 §29, 다른 전승은 베루스가 대신 태움), 베루스 = 카파도키아 총독.
각색: 천막의 대화 전체, 상자를 불구덩이에 넣는 동작.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

TAG = "cine01"
G = "tc_6731b2e0855f351b98d30c48"   # 건석 (해설)
M = "tc_62d66c2d1523be99355fda02"   # 명일 (황제)
V = "tc_675a73eb789ff3ea6cc80235"   # 권일 (장군 베루스)

FILM = ("Photorealistic film still from a prestige epic historical drama, shot on ARRI Alexa with anamorphic lenses, natural skin pores and wrinkles, real wool, leather and bronze textures, "
        "volumetric firelight and thin smoke haze, deep teal-black shadows against warm orange firelight, shallow depth of field, subtle 35mm film grain, realistic human hands with five fingers. "
        "Not a painting, not an illustration. Horizontal 16:9 widescreen frame, main subject in the middle band of the frame, nothing important in the top and bottom eighth of the frame. "
        "Absolutely no text, no letters, no numbers, no writing, no logos, no watermark anywhere.")
EMP = ("the Roman emperor Marcus Aurelius at age fifty-four, lean weathered face, short curly grey-brown hair, short grey-flecked full beard, deep tired eyes, "
       "plain brown wool tunic under a deep crimson wool military cloak fastened with a round bronze brooch")
GEN = ("a Roman general of about fifty, clean-shaven square jaw, short dark hair grey at the temples, a pale old scar across his left eyebrow, "
       "dented bronze muscle cuirass over a red tunic, dark red cloak")
TENT = ("inside a large Roman leather command tent at night in the dry eastern provinces, heavy leather walls, wooden tent poles, a rough wooden camp table, "
        "a low round fire pit ringed with stones in the middle of the tent glowing with orange flames")
CHEST = "a dark oak travel chest bound with black iron straps, about the size of a large suitcase, its lid closed, a leather strap across the lid sealed with a lump of dark red wax"
FACE = " His face is in the middle of the frame, fully visible and lit, with space above his head."

IMAGES = {
 "c1_chest": "Low close-up " + TENT + ": " + CHEST + " sitting on the rough wooden table, two scarred soldier's hands in leather bracers just letting go of it after setting it down, dust hanging in the firelight, the fire pit out of focus behind.",
 "c1_enter": "Wide shot " + TENT + ": seen from directly behind, " + EMP.replace("lean weathered face, ", "") + " stepping alone through the parted tent flap into the tent, his back to the camera, a dark silhouette rimmed with orange firelight, walking toward the table where a dark iron-bound chest waits beside the fire.",
 "c1_seal": "Extreme close-up of a lump of dark red wax seal on a worn leather strap across the lid of a dark oak chest bound with black iron, the wax has an abstract smooth blurred impression with no symbols, orange firelight sliding across it, tiny dust motes, extremely shallow depth of field, deep darkness behind.",
 "c1_hand": "Close-up from the side at table height: an older man's weathered hand with a deep crimson wool sleeve resting flat on the closed lid of " + CHEST + ", the fingers just touching the red wax seal, firelight on the knuckles, deep darkness behind.",
 "c1_push": "Medium shot " + TENT + ": " + EMP + " in three-quarter view from behind, bending forward, both hands pushing " + CHEST + " off the edge of the low stone rim into the burning fire pit, the near corner of the chest already in the flames, sparks bursting upward, his face in shadow.",
 "c1_burn": "Extreme close-up: inside a fire pit a dark oak chest engulfed in flames, its lid cracked and split open by the heat, tightly rolled papyrus scrolls and folded letters inside blackening and curling, the writing is only blurred dark smudges with nothing readable, bright embers and sparks rising, very shallow depth of field.",
 "c1_wide": "Wide two-shot " + TENT + ": on the left " + EMP + " sitting on a plain wooden camp stool at the table in profile; on the right, standing across the table, " + GEN + ", both hands resting on " + CHEST + " on the table between them. The fire pit glows in the foreground out of focus. Both faces visible and lit.",
 "c1_emp_listen": "Close portrait, three-quarter view, of " + EMP + ", sitting at night in a dark leather tent, lit from below and one side by warm firelight, his mouth closed, silently listening, his eyes lowered toward something on the table in front of him." + FACE,
 "c1_ots": "Over-the-shoulder shot from behind the out-of-focus crimson-cloaked shoulder of a seated man in the left foreground, looking across a wooden table at " + GEN + ", standing, firelight on his face, his mouth closed, his eyes uneasy, in a dark leather tent at night. His face is in the middle of the frame, fully visible and lit.",
 "c1_gen_talk": "Close portrait, three-quarter view, of " + GEN + ", in a dark leather tent at night, warm firelight from one side, his lips slightly parted in the middle of speaking, his brow tense, urgent eyes." + FACE,
 "c1_emp_talk": "Close portrait, nearly frontal, of " + EMP + ", in a dark leather tent at night, warm firelight from one side and deep shadow on the other, his lips slightly parted in the middle of speaking quietly, calm heavy eyes looking up at someone standing." + FACE,
 "c1_emp_fire": "Medium close-up in profile of " + EMP + ", sitting very still in a dark leather tent at night, looking into a fire just out of frame, orange light moving over his face, his mouth closed, thin smoke drifting between him and the camera." + FACE,
}

EMP2 = ("Close portrait, three-quarter view, of " + EMP.replace("short grey-flecked full beard", "short neatly trimmed grey-flecked beard") + ", sitting in a dark leather tent at night, warm firelight from one side and deep shadow on the other, a small flame out of focus behind him, "
        "his lips slightly parted in the middle of speaking quietly, calm heavy eyes looking up toward someone standing." + FACE)
SEED = "bytedance/seedance-2.5/image-to-video"; WAN = "alibaba/wan-3.0/image-to-video"
MOVE = ("Photorealistic live-action footage, keep the face, costume, lighting and every detail identical to the first frame. Natural human motion at real-time speed, firelight flickers realistically. "
        "Smooth steady camera, no cuts, no sudden shake, no morphing faces, no extra fingers or limbs, no text appearing.")
VIDEOS = {  # 이름: (묶음, 모델, 움직임)
 "c1v_enter": (1, SEED, "He walks slowly forward away from the camera into the tent toward the chest, his cloak swaying with each step; the tent flap falls closed behind him; the camera follows him slowly."),
 "c1v_hand": (1, SEED, "The hand rests on the lid, the fingers slowly curl and tighten, then stop just above the wax seal and do not break it; the firelight flickers on the knuckles; very slow push-in."),
 "c1v_push": (1, SEED, "With a slow heavy effort he pushes the chest forward into the fire, it tips and slides into the flames, a burst of sparks and embers rises around him; the camera stays still."),
 "c1v_burn": (1, SEED, "Flames climb over the chest, the scrolls inside curl and blacken and catch fire, embers swirl upward; very slow push-in."),
 "c1v_wide": (2, SEED, "The general slides the chest a few centimetres toward the seated emperor and takes his hands away; the emperor stays still and looks at it; flames flicker in the foreground; very slow push-in."),
 "c1v_gen_talk": (2, SEED, "He speaks urgently in Latin, his lips and jaw moving naturally in continuous speech for the whole shot, a small tense shake of the head; the firelight moves on his face; the camera is almost still."),
 "c1v_emp_talk": (2, SEED, "He speaks slowly and quietly, his lips and jaw moving naturally in continuous unhurried speech for the whole shot, then a slow blink; the firelight moves on his face; very slow push-in."),
 "c1v_ots": (3, SEED, "The general listens without speaking, his mouth stays closed, he swallows and his eyes narrow a little; the out-of-focus shoulder stays still; the firelight moves on his face."),
 "c1v_gen_talk_b": (3, SEED, "He leans forward and speaks with rising anger, his lips and jaw moving naturally in continuous forceful speech for the whole shot; the firelight moves on his face; the camera is almost still."),
 "c1v_emp_talk_b": (3, SEED, "He looks up and says one quiet sentence, his lips and jaw moving naturally and slowly, then he stops speaking, closes his mouth and holds the look in silence; the firelight moves on his face; very slow push-in."),
 "c1v_chest": (3, WAN, "The hands let go and draw away out of frame; dust drifts in the firelight; very slow push-in on the chest."),
 "c1v_seal": (3, WAN, "Firelight slides slowly across the wax seal; dust motes drift; the camera glides very slowly along the leather strap."),
 "c1v_emp_listen": (3, WAN, "He keeps listening in silence, his mouth stays closed, a slow breath and one slow blink; the firelight moves over his face; very slow push-in."),
 "c1v_emp_fire": (3, WAN, "He stays still looking into the fire, his mouth stays closed, one slow blink; smoke drifts across; firelight moves on his face; very slow push-in."),
}

LINES = [  # 이름, 목소리, 대사
 ("n1", G, "배신한 사람에게 하는 가장 완벽한 복수."),
 ("n2", G, "2천 년 전, 이 복수를 실제로 한 사람이 있습니다."),
 ("n3", G, "여기, 그를 배신한 사람들의 이름이 든 상자가 있습니다."),
 ("n4", G, "열어 보기만 하면 됩니다."),
 ("n5", G, "그런데 그는, 상자를 불 속에 넣었습니다."),
 ("g1a", V, "폐하. 카시우스의 편지들입니다."),
 ("g1b", V, "원로원 의원, 장군, 총독. 누가 그를 도왔는지, 전부 들어 있습니다."),
 ("e1", M, "읽어 보았는가."),
 ("g2", V, "아닙니다. 폐하께서 먼저 보셔야 합니다."),
 ("e2", M, "이걸 읽으면, 내일 나는 누구를 보게 되겠나."),
 ("g3", V, "폐하를 배신한 자들입니다."),
 ("e3", M, "아니다. 내일부터는, 모든 사람이 배신자로 보일 것이다."),
 ("e4", M, "불을 가져오게."),
 ("g4", V, "폐하. 저들은 폐하를 죽이려 했습니다."),
 ("e5", M, "그래서, 나까지 그들처럼 되어야 하겠나."),
]


def gen():
    jobs = [{"id": k, "kind": "image", "endpoint": "xai/grok-imagine-image-2.0", "body": {"aspect_ratio": "16:9", "prompt": p + " " + FILM}} for k, p in IMAGES.items()]
    json.dump(jobs, open(os.path.join(ROOT, "scripts/side/gen/EDL261109-cine01.json"), "w"), ensure_ascii=False, indent=1)
    vs = []
    for n, v, t in LINES:
        for take in "ABC":   # 줄마다 3테이크 — 음성 깨짐 대비, 좋은 것을 고른다
            vs.append({"name": f"{n}_{take}", "id": v, "line": t, "emotion": "tonedown", "tempo": 0.85 if v == M else 1.0})
    json.dump({"requested": "2026-11-09T19:10", "note": "명상록 실화극 시안 (해설 건석, 황제 명일, 장군 권일)", "tag": TAG, "keep": True, "lang": "kor", "model": "ssfm-v30", "emotion": "tonedown", "tempo": 1.0, "voices": vs},
              open(os.path.join(ROOT, "scripts/side/voices_req.json"), "w"), ensure_ascii=False, indent=1)
    print(len(jobs), "그림", len(vs), "테이크")


def genv(n):
    src = lambda k: f"social/side/gen/{k.replace('c1v_', 'c1_').replace('_talk_b', '_talk')}{'2' if k.startswith('c1v_emp_talk') else ''}.jpeg"
    jobs = [] if n != 2 else [{"id": "c1_emp_talk2", "kind": "image", "endpoint": "xai/grok-imagine-image-2.0", "body": {"aspect_ratio": "16:9", "prompt": EMP2 + " " + FILM}}]
    jobs += [{"id": k, "kind": "video", "endpoint": e, "image": src(k), "body": {"duration": 5, "prompt": p + " " + MOVE}} for k, (b, e, p) in VIDEOS.items() if b == n]
    json.dump(jobs, open(os.path.join(ROOT, f"scripts/side/gen/EDL261109-cine01v{n}.json"), "w"), ensure_ascii=False, indent=1)
    print(len(jobs), "영상")


if __name__ == "__main__":
    gen() if sys.argv[1] == "gen" else genv(int(sys.argv[2]))
