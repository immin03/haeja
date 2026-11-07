"""황제의 일기 EPISODE 4 · 아내를 잃은 밤 — 대본·촬영표 (2026-11-07)
python3 ep04.py gen     → scripts/side/gen/EDL261107-ep04.json (그림) + scripts/side/voices_req.json (녹음)
python3 ep04.py genv    → scripts/side/gen/EDL261107-ep04v.json (영상, 그림이 나온 뒤)
python3 ep04.py spec    → scripts/side/ed_long/spec_ep04.json (렌더 설정)

11/7 대표: "위 분석 전부 반영해서 준비해봐" — 반영한 것
- 제목·썸네일: 결과형 「소중한 사람을 잃어도 무너지지 않는 5가지 방법」, 『명상록』 표기 2장 + 스토아 철학 1장, 숫자 = 실제 장 수(5)
- 7장 → 5장. 장마다 번호 카드(THE FIRST WAY · 첫 번째 방법)로 매듭
- 현대 장면은 장 맨 앞에 한 번만(질문을 던지는 용도), 그 뒤는 로마에 머문다. 핑퐁 금지
- 편 전체를 관통하는 사건 하나: 훅에서 연 '그날 밤'(황후의 죽음)을 마지막에 '그녀가 없는 아침이 왔다'로 닫는다
- 여운 장면은 강한 문장 직후에만
개연성(시간 순서): 훅(175년 겨울, 할랄라, 그날 밤) → 상황("몇 달 전" 카시우스 반란 → 동방 행차 → 돌아오는 길에 병) — 회상은 이 한 번뿐
  → I(그날 밤, 자책) → II(다음 날, 로마의 소문 · 신격화 요청) → III(장례) → IV(장례 다음 날 새벽, 다시 길을 나섬·용서) → V(몇 달 뒤, 파우스티노폴리스·소녀 기금) → 닫기(그날 밤의 문장)
성별 균형: 현대 장면 남 2 · 여 3, 조연 시녀(여) · 원로원(남)
역사 근거: 파우스티나 사망(175/176, 카파도키아 할랄라, 『카시우스 디오』 71.29·『로마 황제 열전』 마르쿠스 26) · 145년 혼인 · 신격화 요청 · 파우스티노폴리스 · 새 '파우스티나의 소녀들' 기금(열전 26.6) · 반란 도시 관용(디오 71.27~28)
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
from ep01 import STYLE, MEMO, EMP, VT, G, M

TAG = "ep04"
CASTV = {"MAID": "tc_6a4f2130d153a5cac8e19996",      # 황후의 시녀 (지선, 중년 여성) — 3편 과부와 같은 목소리
         "SENATOR": "tc_675a73eb789ff3ea6cc80235"}   # 원로원 의원 (권일)
MODN = ("Same painterly cinematic oil-painting texture and fine film grain, but a cool desaturated blue-grey palette with only one small warm light, "
        "horizontal 16:9 widescreen film frame, main subject in the middle band of the frame, nothing important in the top and bottom eighth of the frame, faces clearly lit. "
        "Absolutely no text, no letters, no numbers, no readable screens, no watermark, no brands anywhere.")
FAUS = ("the Roman empress Faustina the Younger at about forty-five, gentle oval face, wavy dark-brown hair parted in the middle and gathered in a low bun, "
        "small pearl earrings, a deep blue stola with a pale mantle")
HAL = "a small village in Cappadocia at the foot of the snowy Taurus mountains, a Roman imperial camp of leather tents beside low stone houses"
FACE = " His face is in the middle of the frame, fully visible and lit, with space above his head."

IMAGES = {
 # 훅 — 175년 겨울, 할랄라, 그날 밤
 "e4_halala": ("Wide view at dusk in winter of " + HAL + ", campfires and torches glowing, soldiers standing still in the cold, smoke rising, one large tent in the center lit from inside.", STYLE),
 "e4_maid": ("Inside a large Roman imperial tent at night lit by oil lamps, a middle-aged Roman maid in a plain grey tunic and shawl kneeling at the tent entrance, tears on her face, speaking, "
             "and " + EMP + " standing in the foreground turning toward her, his face lit and frozen in shock." + FACE, STYLE),
 "e4_alone": ("Inside a dim Roman imperial tent late at night, " + EMP + " sitting alone on a wooden stool beside a bed covered with a pale linen sheet, elbows on his knees, hands clasped, "
              "head slightly bowed but his grieving face visible in the light of one small oil lamp." + FACE, STYLE),
 "e4_faustina": ("A warm portrait of " + FAUS + ", sitting by a window in a Roman villa, smiling softly toward someone off-camera, golden afternoon light on her face, face in the middle of the frame.", MEMO),
 # 상황 — 몇 달 전, 반란과 동방 행차
 "e4_march": ("A long Roman imperial procession winding along a mountain road in the eastern provinces, legionaries, horses and a covered imperial carriage, dust in golden late light, the Taurus mountains ahead.", STYLE),
 # 문장 II — 로마의 소문, 원로원에 보낸 편지
 "e4_rumor": ("Night in a marble colonnade in Rome, two Roman senators in white togas with broad purple stripes reading a letter by torchlight, one leaning in to whisper with a sly cold smirk." +
              FACE.replace("His face is", "Their faces are"), STYLE),
 "e4_wedding": ("A warm memory of a Roman wedding in the year 145: a young " + EMP.replace("at about fifty-four, short curly grey-brown hair, short grey-flecked beard, lean weathered face", "at about twenty-four, short curly brown hair, a short young beard, a gentle face") +
                " holding the right hand of a young bride of about fifteen with dark wavy hair and a flame-orange veil, family in togas around them, flower garlands, soft sunlight.", MEMO),
 # 문장 III — 장례
 "e4_pyre": ("A Roman funeral pyre on a snowy hillside outside the village at dusk, flames rising high, legionaries standing in a silent half circle with lowered standards, "
             "and " + EMP + " standing closest to the fire in a dark cloak, seen in three-quarter view, the firelight on his grieving face.", STYLE),
 "e4_children": ("A warm memory in a Roman villa garden: " + FAUS + " sitting on a stone bench with several small children around her, one little girl on her lap, a fountain and lemon trees, soft light, gentle laughter.", MEMO),
 # 문장 IV — 다음 날 새벽, 다시 길로
 "e4_dawn": ("Cold blue dawn in the Roman camp in Cappadocia, " + EMP + " stepping out of his tent fully dressed in his crimson cloak, his face tired but steady, a secretary with wax tablets and two officers waiting for him, snow on the ground." + FACE, STYLE),
 "e4_city": ("The gate of a Syrian city in the Roman East, citizens and elders in long robes kneeling and bowing their heads in fear, " + EMP + " on foot in front of them raising one hand in a calm gesture of pardon, soldiers behind, warm daylight." + FACE, STYLE),
 # 문장 V — 파우스티나의 도시, 파우스티나의 소녀들
 "e4_girls": ("A warm sunlit courtyard in Rome, a line of poor young Roman girls in simple tunics receiving bread and small purses of coins from kind officials, a mother holding her daughter's hand and smiling, a carved stone relief of a woman on the wall behind, no letters.", MEMO),
 # 오늘의 장면 (현대) — 장 맨 앞에 한 번씩. 남 2 · 여 3
 "e4m_call": ("A Korean man in his early fifties standing frozen in a dark apartment hallway late at night, holding a phone to his ear, shocked face, coat half on, one small lamp.", MODN),
 "e4m_house": ("A Korean woman in her early sixties sitting alone on a sofa in a quiet living room at dusk, holding her late husband's grey cardigan in her lap, his reading glasses on the side table, tired eyes.", MODN),
 "e4m_dog": ("A Korean woman in her mid forties kneeling in a small apartment in the evening beside an empty dog bed, holding a worn red leash in both hands, soft lamp light, quiet grief.", MODN),
 "e4m_bus": ("A Korean man in his early sixties in a dark coat sitting by the window of a city bus at grey morning, looking out at people hurrying to work, his face tired and lonely.", MODN),
 # 11/8 대표: 현대 장면이 몇 초 한 컷이라 로마와 헷갈림 → 장마다 2컷(상황 → 속마음)으로, 1장은 아버지 별세로
 "e4m_funeral": ("The same Korean man in his early fifties now in a black mourning suit with a hemp mourning armband, sitting alone late at night in a quiet Korean funeral hall room, "
                 "a framed portrait of an old father with a black ribbon and white chrysanthemums on the altar behind him slightly out of focus, his head lowered, regret on his face, faces clearly lit.", MODN),
 "e4m_family": ("The same Korean woman in her early sixties at a family dinner table, relatives talking to her with well-meaning faces, she looks down at her untouched rice bowl, holding back tears, warm dim light.", MODN),
 "e4m_walk": ("The same Korean woman in her mid forties walking alone on a riverside path at dusk, holding a worn red leash with no dog attached, her face sad but calm, autumn trees.", MODN),
 "e4m_shirt": ("The same Korean man in his early sixties alone in a small kitchen at dawn, clumsily ironing a white shirt on a board, a framed photo of his late wife on the shelf slightly out of focus, cold light with one warm lamp.", MODN),
 "e4m_mom": ("A Korean woman in her late forties sitting at a kitchen table late at night, holding her phone with both hands and looking at the glowing screen with tears in her eyes, the screen not readable, an old woman's cardigan on the chair beside her.", MODN),
 "e4m_letter": ("A Korean woman in her late forties at a small school office, handing a white envelope to a shy high-school girl in uniform, a framed photo of an older woman on the desk between them, warm light, gentle smiles.", MODN),
}
VIDEOS = {   # wan 3.0, 8개 이하 (LIBRARY.md 4장)
 "ev4_halala": ("e4_halala", "Torches and campfires flicker in the cold wind, smoke drifts slowly, soldiers stand still; very slow push-in toward the lit tent."),
 "ev4_maid": ("e4_maid", "The kneeling maid speaks through tears with small lip movements; the emperor slowly turns his head toward her and freezes; lamp flames flicker."),
 "ev4_alone": ("e4_alone", "The emperor sits very still beside the covered bed, slowly lowers his head a little and closes his eyes; the small lamp flame trembles; very slow push-in."),
 "ev4_rumor": ("e4_rumor", "One senator leans closer and whispers with a cold smirk while the other keeps reading the letter; the torch flickers."),
 "ev4_pyre": ("e4_pyre", "Flames of the pyre rise and sway, sparks drift into the dusk sky; the emperor stands still and the firelight moves on his face; soldiers do not move."),
 "ev4_dawn": ("e4_dawn", "The emperor steps out of the tent, pauses, takes a slow breath of cold air and nods to the waiting officers; breath mist in the cold."),
 "ev4_city": ("e4_city", "The kneeling elders slowly raise their heads as the emperor lowers his raised hand; cloth moves in a light wind."),
 "ev4_girls": ("e4_girls", "An official hands a small loaf of bread to a girl, who smiles; the mother squeezes her daughter's hand; dust glitters in the sunlight."),
}

HOOK = [
 ("h1", G, "기원후 백칠십오 년 겨울. 타우루스 산맥 아래, 카파도키아의 작은 마을 할랄라."),
 ("h_maid", "MAID", "폐하… 황후께서, 숨을 거두셨습니다."),
 ("h2", G, "삼십 년을 함께한 아내, 파우스티나였습니다. 그날 밤, 제국에서 가장 강한 남자는, 막사에 혼자 남았습니다."),
 ("m_h1", M, "그녀가 없는 아침이, 온다."),
 ("m_h2", M, "!그래도, 나는 일어나야 한다."),
]

LINES = [
 # 상황 (몇 달 전) — 회상은 이 한 번
 ("s1", G, "몇 달 전, 제국에 거짓 소문이 퍼졌습니다. 황제가 죽었다는 소문이었습니다."),
 ("s2", G, "동방을 맡고 있던 장군 아비디우스 카시우스는, 그 소문을 믿고 스스로 황제라 선언했습니다. 첫 번째 이야기에서 들려드린, 바로 그 반란입니다."),
 ("s3", G, "반란은 석 달 만에 끝났습니다. 황제는 흔들린 동방을 다독이러 먼 길을 떠났고, 황후 파우스티나가 그 길을 함께했습니다."),
 ("s4", G, "그리고 돌아오는 길, 산맥 아래 작은 마을에서, 황후는 병으로 쓰러졌습니다."),
 # 첫 번째 방법 — 그날 밤 (8권 49절)
 ("d1q", G, "한밤중, 요양병원에서 걸려 온 전화 한 통. 아버지가, 방금 돌아가셨다고 합니다."),
 ("d1q2", G, "빈소에 앉아서도, 머릿속에는 같은 말만 맴돕니다. 지난 주말에 찾아뵀더라면. 그날 전화를, 조금만 더 길게 받았더라면."),
 ("d1a", G, "그날 밤, 황제의 머릿속에도 생각이 몰려들었을 겁니다."),
 ("d1b", G, "내가 그 먼 길에 데려오지 않았다면. 조금만 더 일찍, 의사를 불렀다면."),
 ("d1c", G, "새벽이 오도록, 황제는 등불 옆에 앉아 있었습니다. 그리고 일기를 펼쳤습니다."),
 ("m1a", M, "내 아이가 아프다. 그것은 보인다."),
 ("m1b", M, "그러나 아이가 위험하다는 것은, 보이지 않는다."),
 ("m1c", M, "처음 보이는 것 이상을, 스스로에게 말하지 마라."),
 ("d1d", G, "황제는 일어난 사실과, 내가 그 위에 덧붙이는 이야기를 나누었습니다. 아내가 떠났다는 것은 사실입니다. 그러나 '모두 내 탓이다'는, 내가 덧붙인 이야기였습니다."),
 ("d1e", G, "!일어난 일은 하나입니다. 그 위에 쌓는 이야기가, 사람을 무너뜨립니다."),
 ("d1t", G, "날이 밝자, 로마에서 온 편지 한 통이 막사에 닿았습니다."),
 # 두 번째 방법 — 로마의 소문 (1권 17절)
 ("d2q", G, "남편을 떠나보내고 한 달. 사람들은 이제 어떻게 살 거냐고 묻습니다. 그런데 떠오르는 건, 그가 남기고 간 빈자리뿐입니다."),
 ("d2q2", G, "위로한다며 건넨 말들이, 오히려 가슴을 찌릅니다. 이제 그만 잊으라고, 산 사람은 살아야 한다고."),
 ("d2a", G, "편지에는, 차가운 소문이 적혀 있었습니다. 황후가 카시우스와 몰래 편지를 주고받으며, 반란을 부추겼다는 소문이었습니다."),
 ("r_sen", "SENATOR", "황후가 반란을 부추겼다더군. 그러니 하늘이 데려간 거지."),
 ("d2b", G, "황제는 그 소문에 답하지 않았습니다. 대신 원로원에 편지를 보냈습니다. 아내를, 신으로 모시게 해 달라고."),
 ("m2a", M, "나는 신들께 감사한다."),
 ("m2b", M, "그토록 순하고, 그토록 다정하고, 그토록 꾸밈없는 사람이, 내 아내였음을."),
 ("m2c", M, "그토록 다정하고 꾸밈없는 아내를 만난 것에, 감사한다."),
 ("d2c", G, "황제는 잃은 것을 세지 않고, 받은 것을 셌습니다. 열다섯 살 신부와 스물네 살 신랑으로 만나 함께한 삼십 년. 함께 키운 아이들. 함께 건넌 전쟁터."),
 ("d2d", G, "!떠난 사람이 남긴 것을 세는 동안, 그 사람은 내 안에서 다시 살아납니다."),
 ("d2t", G, "며칠 뒤, 마을 밖 언덕에 장작이 쌓였습니다."),
 # 세 번째 방법 — 장례 (9권 35절)
 ("d3q", G, "열다섯 해를 함께한 강아지를 떠나보낸 날. 집 안의 모든 것이 그대로인데, 모든 것이 달라져 있습니다."),
 ("d3q2", G, "누군가는 고작 개 한 마리라고 말합니다. 하지만 내게는, 열다섯 해의 아침과 저녁이었습니다."),
 ("d3a", G, "황후를 위한 장례의 불이, 겨울 하늘로 타올랐습니다. 병사들은 깃발을 내리고, 말없이 서 있었습니다."),
 ("d3b", G, "황제에게 이별은, 처음이 아니었습니다. 그는 이미 여러 아이를 먼저 떠나보낸 아버지였습니다."),
 ("m3a", M, "어제의 것은 오늘 다른 것이 되고, 오늘의 것은 내일 또 다른 것이 된다."),
 ("m3b", M, "자연은, 그 변화를 기뻐한다."),
 ("m3c", M, "잃는다는 것은, 변한다는 것일 뿐이다."),
 ("d3c", G, "황제에게 죽음은, 사라짐이 아니라 자연의 큰 흐름으로 돌아가는 일이었습니다. 슬퍼하지 말라는 말이 아닙니다. 끝이라고만, 여기지 말라는 겁니다."),
 ("d3d", G, "!함께한 시간은 사라지지 않습니다. 모양을 바꿔, 내 안에 남을 뿐입니다."),
 ("d3t", G, "장례가 끝난 다음 날 새벽. 황제는, 다시 일어나야 했습니다."),
 # 네 번째 방법 — 다음 날 새벽 (5권 1절)
 ("d4q", G, "아내를 보낸 지 한 달. 출근길 버스 창밖으로, 아무 일 없다는 듯 돌아가는 세상이 야속하기만 합니다."),
 ("d4q2", G, "그래도 아침이면, 서툰 손으로 셔츠를 다려 입고 집을 나섭니다. 아내가 늘 해 주던 일을, 이제는 혼자 합니다."),
 ("d4a", G, "막사 밖에는, 서기와 장교들이 기다리고 있었습니다. 반란에 흔들린 동방의 도시들이, 황제의 판단을 기다리고 있었습니다."),
 ("d4b", G, "황제는 다시 길을 나섰습니다. 그리고 반란에 가담했던 도시들에, 대부분 벌 대신 용서를 내렸습니다."),
 ("m4a", M, "새벽에 일어나기 싫을 때, 이렇게 말하라."),
 ("m4b", M, "나는 따뜻한 이불 속에 있으려고, 태어난 것이 아니다."),
 ("m4c", M, "나는, 사람의 일을 하러 일어난다."),
 ("d4c", G, "슬픔을 이겨 내라는 말이 아닙니다. 슬픔을 안은 채로, 오늘 해야 할 작은 일 하나로 돌아가라는 겁니다. 황제에게 그 일은, 제국을 돌보는 일이었습니다."),
 ("d4d", G, "!밥을 짓고, 집을 나서고, 화분에 물을 주는 일. 그 작은 일이, 나를 다시 일으킵니다."),
 ("d4t", G, "그리고 얼마 뒤, 황제는 아내를 위해, 한 가지 일을 시작했습니다."),
 # 다섯 번째 방법 — 몇 달 뒤 (6권 7절)
 ("d5q", G, "어머니를 떠나보낸 지 일 년. 휴대폰에는 아직도, 엄마라는 이름을 지우지 못했습니다."),
 ("d5q2", G, "보고 싶은 마음은 그대로인데, 그 그리움을 어디에 두어야 할지, 아직도 모르겠습니다."),
 ("d5a", G, "황제는 아내가 숨을 거둔 마을 할랄라를, 파우스티노폴리스, 파우스티나의 도시라고 이름 붙였습니다."),
 ("d5b", G, "그리고 아내의 이름으로, 가난한 집 소녀들을 돕는 기금을 세웠습니다. 사람들은 그 아이들을, 파우스티나의 소녀들이라고 불렀습니다."),
 ("m5a", M, "한 가지에서 기쁨을 찾고, 거기서 쉬어라."),
 ("m5b", M, "남을 위한 한 가지 일에서, 또 다른 일로 옮겨 가는 것."),
 ("m5c", M, "남을 위한 일에서 다음 일로, 거기서 기쁨을 찾아라."),
 ("d5c", G, "황제는 그리움을, 가슴속에만 두지 않았습니다. 아내의 이름으로, 누군가의 내일을 도왔습니다. 그렇게 슬픔은, 세상에 남는 좋은 일이 되었습니다."),
 ("d5d", G, "!어머니의 이름으로 건넨 작은 장학금 하나. 그리움은 그렇게, 누군가의 내일이 됩니다."),
 # 닫기 — 그날 밤으로
 ("c1", G, "그날 밤, 막사에 혼자 남았던 황제. 그 뒤로도 그는 몇 해를 더 살며, 마지막까지 제국을 지켰습니다."),
 ("m_c1", M, "그녀가 없는 아침이, 왔다. 그리고 나는, 일어났다."),
 # 정리·끝
 ("r1", G, "소중한 사람을 잃었을 때, 황제가 일기에 남긴 다섯 가지 방법을, 다시 짚어 보겠습니다."),
 ("t0", G, "오늘 밤, 잠들기 전에, 이 세 가지만 해 보세요."),
 ("r9", G, "!떠난 사람은 돌아오지 않습니다. 그러나 그 사람에게 받은 것은, 오늘도 나를 살게 합니다."),
 ("o1", G, "좋아요와 구독은, 영상 제작에 큰 힘이 됩니다. 감사합니다."),
 ("o2", G, "다음 이야기에서도, 황제가 일기에 남긴 문장들을 들려드리겠습니다."),
]
EMO = {"h_maid": "sad", "r_sen": "whisper"}


def clean(t): return t.lstrip("!")


def gen():
    jobs = [{"id": k, "kind": "image", "endpoint": "xai/grok-imagine-image-2.0", "body": {"aspect_ratio": "16:9", "prompt": p + " " + st}} for k, (p, st) in IMAGES.items()]
    json.dump(jobs, open(os.path.join(ROOT, "scripts/side/gen/EDL261107-ep04.json"), "w"), ensure_ascii=False, indent=1)
    V = []
    for n, v, t in HOOK + LINES:
        V.append({"name": n, "id": CASTV.get(v, v), "line": clean(t), "emotion": EMO.get(n, "tonedown"), "tempo": 0.85 if v == M else 1.0})
    json.dump({"requested": "2026-11-07T15:40", "note": "황제의 일기 EPISODE 4 전편 녹음 (해설 건석, 황제 명일, 조연 시녀·원로원)", "tag": TAG, "keep": True, "lang": "kor",
               "model": "ssfm-v30", "emotion": "tonedown", "tempo": 1.0, "voices": V}, open(os.path.join(ROOT, "scripts/side/voices_req.json"), "w"), ensure_ascii=False, indent=1)
    print(len(jobs), "그림,", len(V), "줄 녹음")


def genv():
    vj = [{"id": k, "kind": "video", "endpoint": "alibaba/wan-3.0/image-to-video", "image": f"social/side/gen/{src}.jpeg", "body": {"duration": 5, "prompt": p + " " + VT}} for k, (src, p) in VIDEOS.items()]
    json.dump(vj, open(os.path.join(ROOT, "scripts/side/gen/EDL261107-ep04v.json"), "w"), ensure_ascii=False, indent=1)
    print(len(vj), "영상")


if __name__ == "__main__":
    if sys.argv[1] == "gen": gen()
    elif sys.argv[1] == "genv": genv()
    else:
        import ep04_spec; ep04_spec.build()
