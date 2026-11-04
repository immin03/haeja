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


# ================= 2단계(11/4 대표: 2편 전체 렌더링) — 상황·문장 I~VII·정리·아웃트로 =================
# 개연성 점검(기획안 표 기준, 시간은 앞으로만): 훅(재판 중) → 상황(재판 며칠 전) → I(그 무렵 황제의 아침 습관) → II(재판 전날 밤 낙뢰)
#  → III(재판 당일: 루키우스 발언 뒤를 이어 근위대장과 말다툼, 퇴장 — 훅 대사는 다시 읽지 않음) → IV(퇴장 직후 재판을 이어 감, 눈물)
#  → V(그날 밤 근위대장이 본보기를 요구) → VI(며칠 뒤 판결: II의 슬픔을 거둠) → VII(훗날 편지: 편 전체의 답)
#  기획안 표에서 V(근위대장 말다툼)를 IV 뒤에 두면 퇴장 뒤로 시간이 거꾸로 가서, 말다툼은 III 퇴장 장면 안으로 옮기고 V는 그날 밤으로 바꿨다.
TAG2 = "ep02b"
ATHEN = "tc_66860d458ca8b2dc5f72b865"   # 아테네 대표 (덕환 — 헤로데스·근위대장과 겹치지 않는 중년 목소리)
CASTV = {"HERODES": HERODES_CAND["jongdae"], "PREFECT": PREFECT_CAND["wangkwon"], "ATHEN": ATHEN}
MODN = ("Same painterly cinematic oil-painting texture and fine film grain, but a cool desaturated blue-grey palette with only one small warm light, "
        "horizontal 16:9 widescreen film frame, main subject in the middle band of the frame, nothing important in the top and bottom eighth of the frame, faces clearly lit. "
        "Absolutely no text, no letters, no numbers, no readable screens, no watermark, no brands anywhere.")
CAMP2 = "the Roman frontier camp and walled city of Sirmium on the Sava river"
ATH = "a group of middle-aged Athenian citizens in white wool himations with olive wreaths on their heads"

IMAGES2 = {
 "e2_sirmium": ("Wide view at early morning of " + CAMP2 + ": stone walls, rows of legion tents, mist rising from the wide river, a few torches still burning, soldiers small in the distance.", STYLE),
 "e2_athenians": (ATH + " standing together inside " + HALL + ", one of them stepping forward and speaking earnestly with an open hand toward the dais, faces lit by torchlight.", STYLE),
 "e2_herodes": ("Close portrait of " + HER + ", sitting alone on a stone bench in a dim room, his eyes red with grief and anger, one hand gripping his staff, warm torchlight on his face.", STYLE),
 "e2_lightning": ("Night storm over a Roman travellers' lodge with a red tiled roof outside the walls of Sirmium, heavy rain, a brilliant jagged bolt of lightning striking the roof, the whole scene lit blue-white for an instant.", STYLE),
 "e2_daughters": ("Inside an empty room of a Roman lodge at dawn after a storm, two small girls' tunics folded on a bed, two little wooden dolls and a pair of small sandals on the floor, rain-wet window light, deep sorrowful stillness, no people.", STYLE),
 "e2_rain": ("A Roman command tent at night in pouring rain, a single warm lamp glowing through the canvas from inside, puddles reflecting the light, guards standing in the rain with shields.", STYLE),
 "e2_walkout": ("Inside " + HALL + ": " + HER + " seen from behind walking away toward the open doors at the end of the hall, his white himation trailing, a bronze water clock dripping in the foreground on the right, "
                "the stunned crowd and guards turning to watch him leave.", STYLE),
 "e2_tears": ("Close portrait of " + EMP + " seated on the tribunal dais, his face fully visible and lit by warm torchlight, his eyes glistening with a single tear, listening with deep compassion to someone off-camera.", STYLE),
 "e2_prefect": ("Night inside a Roman command tent lit by oil lamps: " + PREF + " standing and speaking forcefully with one hand on the hilt of his sword, facing " + EMP + " who sits at a wooden table seen from behind and to the side, "
                "a scroll on the table.", STYLE),
 "e2_verdict": ("A Roman scribe in a plain tunic standing in " + HALL + " and reading aloud from an unrolled parchment scroll, the emperor seated on the dais behind him small in the distance, the crowd listening in silence.", STYLE),
 "e2_letter": ("Close-up of " + EMP + "'s hands pressing a bronze signet ring into a dark red wax seal on a folded parchment letter on a wooden table, a candle and an inkwell beside it, warm candlelight, only hands and table visible.", STYLE),
 "e2_reading": ("An old Greek scholar with a long white beard, " + "white wool himation" + ", sitting by an open window of a villa in Athens with the Acropolis far in the distance, holding an unrolled letter with a broken red wax seal, "
                "his eyes wet, a faint softening smile, warm afternoon light on his face.", MEMO),
 "e2_dawn": ("Dawn inside a Roman command tent, " + EMP + " sitting on a camp stool with a small wax tablet notebook open on his knee, looking up thoughtfully toward the pale light at the tent opening, "
             "his face clearly lit by the soft dawn light, an extinguished lamp beside him.", STYLE),
 "e2_gym": ("A sunlit Roman palaestra wrestling ground: two athletes with oiled skin grappling on the sand, one has scratched the other's arm, the scratched man steps back calmly with a small smile, other athletes watching from a colonnade.", MEMO),
 "e2_market": ("A crowded ancient Roman street market by day, a fruit seller and a customer shouting at each other over a stall, people passing by without much notice, baskets of fruit and hanging cloth, warm dusty light.", STYLE),
 "e2_morning": ("Sunrise over the walls of Sirmium, " + EMP + " standing alone on the stone wall walk seen from behind, his crimson cloak moving in the wind, looking out over the misty river and the camp, golden light, calm and resolved.", STYLE),
 # 오늘의 장면(현대)
 "e2m_elevator": ("A Korean man in his late forties in a suit standing in front of closed office elevator doors on a Monday morning, holding a coffee, his jaw tight, bracing himself, other office workers blurred behind.", MODN),
 "e2m_breath": ("A Korean man in his late forties standing by an office window early in the morning, eyes closed, taking a slow deep breath before a meeting, a notebook in his hand.", MODN),
 "e2m_holiday": ("A Korean family holiday dinner table with many dishes, an older Korean uncle in his seventies pointing his chopsticks and talking loudly at a tense nephew in his forties, other relatives looking down awkwardly.", MODN),
 "e2m_uncle": ("An older Korean man in his seventies sitting alone on a small apartment balcony at night, looking at an old faded family photograph in his hands, lonely and tired, city lights behind.", MODN),
 "e2m_office": ("A modern Korean open-plan office, a middle-aged man talking loudly on his phone with his feet up on the desk while a woman in her forties at the next desk quietly closes her eyes in resignation.", MODN),
 "e2m_ceiling": ("A Korean woman in her fifties sitting on a sofa in a dim apartment living room at night, looking up at the ceiling with a tired expression as if hearing noise from upstairs, a lamp beside her.", MODN),
 "e2m_restaurant": ("A small Korean restaurant at lunchtime, a weary waiter putting down a dish abruptly with a cold expression in front of a Korean woman in her forties who looks hurt and surprised.", MODN),
 "e2m_bed": ("A Korean woman in her forties lying awake in bed at night in a dark bedroom, eyes open, staring at the ceiling, replaying something in her mind, faint light from the window.", MODN),
 "e2m_friend": ("Two Korean women in their forties at a café table in the evening, one leaning in and telling something in a low voice, the other freezing with a hurt, shocked face, cups of coffee between them.", MODN),
 "e2m_walk": ("A Korean man in his fifties walking alone along a quiet riverside path at night under street lamps, hands in his coat pockets, calm composed face, seen from the side.", MODN),
 "e2m_phone": ("Close-up of a Korean man's hands holding a smartphone in a dark room at night, his thumb hovering just above the screen, the screen glow lighting his fingers, no readable text on the screen.", MODN),
 "e2m_tea": ("A Korean man in his forties at a kitchen table late at night, his smartphone placed face down beside him, pouring himself a cup of warm tea with a calmer expression, a single pendant lamp above.", MODN),
 "e2m_family": ("A Korean family dinner at home, an elderly father in his seventies speaking sternly while his son in his forties sits silently looking down at his rice bowl, the mother glancing between them.", MODN),
 "e2m_shoes": ("An apartment entrance, a Korean man in his forties kneeling to help his elderly father in his seventies put on his shoes, the father looking away stubbornly, the son patient and gentle, warm hallway light.", MODN),
}
VIDEOS2 = {
 "ev2_lightning": ("e2_lightning", "The lightning flashes and fades, heavy rain keeps falling and the roof glows briefly; then darkness and rain."),
 "ev2_walkout": ("e2_walkout", "The old man keeps walking slowly away toward the open doors while water drips from the bronze clock; the crowd stays frozen; torch flames waver."),
}

LINES2 = [   # (이름, 목소리, 문장) — 목소리: G 해설, M 황제, 'HERODES'/'PREFECT'/'ATHEN' 조연
 # 상황 (재판 며칠 전)
 ("s1", G, "카시우스의 반란이 일어나기 한 해 전. 황제는 다뉴브 전선의 도시, 시르미움에 머물고 있었습니다."),
 ("s2", G, "그곳으로, 먼 아테네에서 시민 대표들이 찾아왔습니다. 한 노인을 고발하기 위해서였습니다."),
 ("s3", G, "헤로데스 아티쿠스. 당대 최고의 웅변가이자, 젊은 황제에게 그리스어 웅변을 가르친 옛 스승이었습니다."),
 ("s_ath", "ATHEN", "황제시여, 아테네는 더 이상, 그 사람의 집 마당이 아닙니다."),
 ("s4", G, "황제는 전쟁터 한가운데서, 자기 스승의 재판을 열어야 했습니다."),
 ("s5", G, "그 재판을 앞둔 날들에도, 황제의 아침은 언제나 같은 방식으로 시작되었습니다."),
 # 문장 I
 ("d1a", G, "황제는 날이 밝으면, 하루를 시작하기 전에 자기 자신에게 먼저 말을 걸었습니다."),
 ("d1b", G, "오늘 누구를 만나게 될지, 그 사람이 어떻게 나올지를, 미리 떠올려 보는 것이었습니다."),
 ("m1a", M, "오늘 나는, 참견하는 자와, 은혜를 모르는 자와, 오만한 자를 만날 것이다."),
 ("m1b", M, "그들은 무엇이 선이고 무엇이 악인지 모르기에, 그렇게 행동하는 것이다."),
 ("m1c", M, "아침마다 스스로에게 말하라. 오늘 나는, 무례한 사람들을 만나게 될 것이라고."),
 ("d1c", G, "스토아 철학자들은 이것을, 나쁜 일을 미리 그려 보는 연습이라고 불렀습니다. 라틴어로, 프라에메디타티오 말로룸입니다."),
 ("d1d", G, "법정에서 황제의 얼굴이 흔들리지 않았던 이유가, 여기에 있습니다. 무례는 그에게, 아침마다 미리 만나 본 손님이었습니다."),
 ("d1e", G, "월요일 아침, 회사 엘리베이터 앞. 문이 열리기도 전에, 그 부장의 목소리가 벌써 들리는 것 같습니다."),
 ("d1f", G, "!미리 각오한 무례는, 나를 기습하지 못합니다."),
 ("d1g", G, "오늘 밤에는, 내일 만날 까다로운 사람 한 명과, 그가 할 법한 말을 미리 적어 보세요. 내일 그 말은, 처음 듣는 말이 아닐 겁니다."),
 ("d1h", G, "그런데 재판 전날 밤, 아무도 예상하지 못한 일이 일어났습니다."),
 # 문장 II (재판 전날 밤)
 ("d2a", G, "그날 밤, 시르미움에 거센 폭풍이 몰아쳤습니다. 번개 하나가, 헤로데스 일행이 묵던 숙소에 내리꽂혔습니다."),
 ("d2b", G, "그 자리에서, 헤로데스가 딸처럼 아끼며 키우던 쌍둥이 자매가 숨을 거두었습니다."),
 ("d2c", G, "이미 자기 자식들을 여럿 먼저 떠나보낸 노인에게, 그 아이들은 남은 기쁨이었다고 전해집니다."),
 ("d2d", G, "다음 날, 노인은 그 슬픔을 그대로 안은 채, 법정에 서게 됩니다."),
 ("m2a", M, "누군가 나에게 잘못을 하면, 먼저 생각하라."),
 ("m2b", M, "그는 무엇을 좋다고 여기고, 무엇을 나쁘다고 여겼기에, 그렇게 했는가."),
 ("m2c", M, "그가 무엇을 옳다고 믿었는지 보면, 화 대신 연민이 남는다."),
 ("d2e", G, "황제는 사람을 볼 때, 행동보다 그 뒤에 있는 판단을 보려고 했습니다. 무례한 말은 대개, 그 사람이 지고 있는 무게에서 나옵니다."),
 ("d2f", G, "명절 식탁에서, 너는 아직도 그 회사 다니냐고 묻는 큰아버지. 알고 보니 그는 평생, 자기 자식과 비교당하며 살아온 사람이었습니다."),
 ("d2g", G, "!그를 이해한다고 그 말이 옳아지지는 않습니다. 다만, 내 화가 조금 작아질 뿐입니다."),
 ("d2h", G, "오늘 밤에는, 오늘 나를 언짢게 한 사람에게 있었을 사정을, 한 줄로 써 보세요."),
 ("d2i", G, "그리고 날이 밝자, 재판이 시작되었습니다."),
 # 문장 III (재판 당일)
 ("d3a", G, "물시계의 물이 떨어지기 시작했습니다. 변론에 주어진 시간이었습니다."),
 ("d3b", G, "헤로데스는 고발에 답하지 않았습니다. 대신 황제를 똑바로 쳐다보며, 서운함을 쏟아 냈습니다."),
 ("d3c", G, "그리고 물시계의 물이 다 떨어지기도 전에, 자리를 박차고 일어섰습니다. 근위대장이 그 앞을 막아섰습니다."),
 ("p3", "PREFECT", "죽고 싶은 모양이군."),
 ("h3", "HERODES", "늙은이는, 두려운 것이 별로 없소."),
 ("d3d", G, "노인은 그대로, 법정을 나가 버렸습니다. 황제의 법정에서, 황제에게 등을 보인 것입니다."),
 ("m3a", M, "무례한 자 때문에 화가 날 때면, 스스로에게 물어라."),
 ("m3b", M, "세상에 무례한 사람이 하나도 없을 수 있는가. 그럴 수는 없다."),
 ("m3c", M, "불가능한 것을 바라지 마라. 무례한 사람이 없는 세상은 없다."),
 ("d3e", G, "황제는 무례한 사람을 만나는 일을, 겨울에 추위를 만나는 일처럼 여겼습니다. 놀랄 일이 아니라, 세상의 한 부분이라는 겁니다."),
 ("d3f", G, "회사를 옮겨도, 모임을 옮겨도, 꼭 한 명은 있는 그 사람. 이사 간 아파트에도, 위층에는 또 그런 집이 있었습니다."),
 ("d3g", G, "!어디에나 있는 사람이라면, 만날 때마다 놀랄 필요는 없습니다."),
 ("d3h", G, "오늘 밤에는, 그런 사람도 있는 법이라고, 소리 내어 한 번 말해 보세요."),
 ("d3i", G, "법정의 모든 눈이, 황제에게로 향했습니다."),
 # 문장 IV (퇴장 직후)
 ("d4a", G, "무거운 정적이 흘렀습니다. 모두가, 황제가 크게 노할 거라고 생각했습니다."),
 ("d4b", G, "그러나 황제는 얼굴빛 하나 바꾸지 않고, 아테네 사람들을 향해 말했습니다."),
 ("m4x", M, "변론을, 계속하시오."),
 ("s_ath2", "ATHEN", "그는 우리 도시를, 자기 집 곳간처럼 다루었습니다."),
 ("d4c", G, "아테네 사람들은 그동안 겪은 일들을 하나씩 털어놓았습니다. 그 호소를 듣던 황제는, 끝내 눈물을 보였다고 전해집니다."),
 ("m4a", M, "그의 말이, 나를 해쳤는가."),
 ("m4b", M, "아니다. 해쳤다고 여기는 내 판단이, 나를 해친다."),
 ("m4c", M, "상처받았다는 생각을 버려라. 그러면, 상처도 사라진다."),
 ("d4d", G, "황제는 모욕을 마음에 담아 두지 않았습니다. 그래서 그 자리에서, 모욕한 사람이 아니라 호소하는 사람들의 말을 들을 수 있었습니다."),
 ("d4e", G, "식당 직원이 던진 퉁명스러운 한마디. 집에 와서 씻고 누워서도, 그 말이 몇 번이고 다시 재생됩니다."),
 ("d4f", G, "!그 말은 한 번 들었는데, 상처는 내가 백 번 냈습니다."),
 ("d4g", G, "오늘 밤에는, 오늘 들은 말 하나를, 실제로 들은 말과 내가 붙인 해석으로 나눠 적어 보세요."),
 ("d4h", G, "재판이 끝난 그날 밤, 황제의 막사로 한 사람이 찾아왔습니다."),
 # 문장 V (그날 밤)
 ("d5a", G, "근위대장이었습니다. 그는 칼자루에 손을 얹은 채 말했습니다."),
 ("p5", "PREFECT", "폐하, 그는 모두가 보는 앞에서 폐하를 모욕했습니다. 본보기를 보이셔야 합니다."),
 ("d5b", G, "궁정의 많은 사람이 같은 생각이었습니다. 황제의 위엄이, 땅에 떨어졌다고."),
 ("m5a", M, "그들은 내 위엄이 무너졌다고 말한다."),
 ("m5b", M, "그러나 한 노인의 무례가, 내 위엄을 가져갈 수는 없다."),
 ("m5c", M, "누가 나를 경멸하는가. 그것은 그의 몫이다. 내 몫은, 경멸받을 일을 하지 않는 것이다."),
 ("d5c", G, "황제는 남의 평가와 자기 행동 사이에, 분명한 선을 그었습니다. 남이 나를 어떻게 보는지는 그의 영역이고, 내가 어떻게 행동하는지만 내 영역이라는 겁니다."),
 ("d5d", G, "내가 없는 자리에서 누가 내 험담을 했다는 말을, 가장 친한 친구에게서 전해 들었을 때."),
 ("d5e", G, "!그가 나를 어떻게 말하는지는 그의 일입니다. 내가 어떻게 사는지만, 내 일입니다."),
 ("d5f", G, "오늘 밤에는, 누가 뭐라 하든 내가 부끄럽지 않게 한 일 하나를, 적어 보세요."),
 ("d5g", G, "며칠 뒤, 판결이 내려졌습니다."),
 # 문장 VI (판결)
 ("d6a", G, "모두가 무거운 벌을 예상했습니다. 황제를 모욕한 죄였으니까요."),
 ("d6b", G, "그러나 판결은 뜻밖에 가벼웠습니다. 헤로데스 본인은 벌하지 않고, 그의 해방노예 몇 사람에게만 가벼운 벌을 내렸습니다."),
 ("d6c", G, "딸 같은 아이들을 잃은 노인에게는, 그 슬픔이 이미 충분한 벌이라고 여겼다고 전해집니다."),
 ("m6a", M, "그는 나를 모욕했다. 나도 그를 모욕할 수 있다."),
 ("m6b", M, "그러나 그렇게 하는 순간, 나는 그와 같은 사람이 된다."),
 ("m6c", M, "가장 좋은 복수는, 그와 같아지지 않는 것이다."),
 ("d6d", G, "황제는 일기에 이런 비유도 남겼습니다. 레슬링 훈련장에서 상대가 손톱으로 할퀴어도, 우리는 그를 원수로 여기지 않고, 그저 조심할 뿐이라고."),
 ("d6e", G, "밤 열한 시, 무례한 문자에 더 날 선 답장을 썼다가, 전송 버튼 앞에서 멈춘 손가락."),
 ("d6f", G, "!똑같이 갚는 순간, 그 사람이 나를 이깁니다."),
 ("d6g", G, "오늘 밤에는, 보내려던 날 선 답장을, 하루만 묵혀 보세요."),
 ("d6h", G, "그리고 시간이 흐른 뒤, 황제는 한 통의 편지를 썼습니다."),
 # 문장 VII (훗날)
 ("d7a", G, "받는 사람은, 헤로데스 아티쿠스였습니다."),
 ("d7b", G, "황제는 그에게, 지금도 변함없이 당신을 존경한다고 썼다고 전해집니다."),
 ("d7c", G, "법정에서 등을 돌린 스승에게, 황제는 끝내 등을 돌리지 않았습니다."),
 ("m7a", M, "사람은, 서로를 위해 태어났다."),
 ("m7b", M, "무례한 사람도, 그 사람들 가운데 하나다."),
 ("m7c", M, "그러니 가르쳐라. 가르칠 수 없다면, 견뎌라."),
 ("d7d", G, "스토아 철학자들은 사람을, 한 몸의 손과 발처럼 서로 이어진 존재로 보았습니다. 손이 발에게 화를 내며, 등을 돌릴 수는 없다는 겁니다."),
 ("d7e", G, "삼십 년째 같은 말로 상처를 주는 부모님. 그래도, 안 볼 수는 없는 사람."),
 ("d7f", G, "!끊을 수 없는 사람이라면, 가르치거나 견디면 됩니다. 다만, 닮지는 마세요."),
 ("d7g", G, "오늘 밤에는, 가르칠 사람과 견딜 사람을, 한 명씩 나눠 보세요."),
 # 정리·아웃트로
 ("r1", G, "무례한 사람 앞에서, 황제가 일기에 남긴 일곱 문장을 다시 짚어 보겠습니다."),
 ("r2", G, "첫째, 아침마다 미리 각오하라."),
 ("r3", G, "둘째, 그가 무엇을 옳다고 믿었는지 보라."),
 ("r4", G, "셋째, 무례한 사람이 없는 세상은 없다."),
 ("r5", G, "넷째, 상처받았다는 생각을 내려놓아라."),
 ("r6", G, "다섯째, 경멸은 그의 몫이다."),
 ("r7", G, "여섯째, 가장 좋은 복수는, 닮지 않는 것."),
 ("r8", G, "일곱째, 가르치거나, 견디거나."),
 ("r9", G, "!무례는 막을 수 없습니다. 내가 그와 같아지지 않는 것만이, 내 몫입니다."),
 ("o1", G, "오늘 이야기가 마음에 닿으셨다면, 구독과 좋아요로 황제의 일기를 함께 이어 가 주세요."),
 ("o2", G, "다음 이야기에서는, 아무도 알아주지 않을 때 황제가 붙잡았던 문장들을 들려드리겠습니다."),
]
EMO2 = {"p3": "tonedown", "h3": "tonedown", "p5": "angry", "s_ath": "tonedown", "s_ath2": "sad"}


def gen2():
    jobs = []
    for k, (p, st) in IMAGES2.items():
        jobs.append({"id": k, "kind": "image", "endpoint": "xai/grok-imagine-image-2.0", "body": {"aspect_ratio": "16:9", "prompt": p + " " + st}})
    json.dump(jobs, open(os.path.join(ROOT, "scripts/side/gen/EDL261104-ep02b.json"), "w"), ensure_ascii=False, indent=1)
    vj = [{"id": k, "kind": "video", "endpoint": "alibaba/wan-3.0/image-to-video", "image": f"social/side/gen/{src}.jpeg", "body": {"duration": 5, "prompt": p + " " + VT}} for k, (src, p) in VIDEOS2.items()]
    json.dump(vj, open(os.path.join(ROOT, "scripts/side/gen/EDL261104-ep02v.json"), "w"), ensure_ascii=False, indent=1)
    V = []
    for n, v, t in LINES2:
        if n in ("p3", "h3"): continue   # 오디션 녹음(a_pref_wangkwon, a_her2_jongdae)을 그대로 쓴다
        vid = CASTV.get(v, v)
        V.append({"name": n, "id": vid, "line": clean(t), "emotion": EMO2.get(n, "tonedown"), "tempo": 0.85 if v == M else 1.0})
    json.dump({"requested": "2026-11-04T13:40", "note": "황제의 일기 EPISODE 2 본편 녹음 (해설 건석, 황제 명일, 조연 근위대장·아테네 대표)", "tag": TAG2, "keep": True, "lang": "kor",
               "model": "ssfm-v30", "emotion": "tonedown", "tempo": 1.0, "voices": V}, open(os.path.join(ROOT, "scripts/side/voices_req.json"), "w"), ensure_ascii=False, indent=1)
    print(len(jobs), "그림,", len(vj), "영상(그림 뒤),", len(V), "줄 녹음")


if __name__ == "__main__":
    if sys.argv[1] == "gen": gen()
    elif sys.argv[1] == "gen2": gen2()
    else:
        import ep02_spec; ep02_spec.build()
