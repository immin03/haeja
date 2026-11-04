"""황제의 일기 EPISODE 3 · 아무도 알아주지 않을 때 — 대본·촬영표 (2026-11-04)
python3 ep03.py gen     → scripts/side/gen/EDL261104-ep03.json (그림) + scripts/side/voices_req.json (녹음)
python3 ep03.py genv    → scripts/side/gen/EDL261104-ep03v.json (영상, 그림이 나온 뒤)
python3 ep03.py spec    → scripts/side/ed_long/spec_ep03.json (렌더 설정)
기획안: Claude Docs 「황제의 일기 EPISODE 3 · 아무도 알아주지 않을 때 기획안」
개연성: 훅(169년 경매 도중) → 상황("삼 년 전" 166, 역병) → I(166~168 장례) → II(169 겨울 루키우스) → III(169 봄 빈 금고, 팔기로)
        → IV(두 달의 경매: 훅의 뒤를 이어 감, 훅 대사 반복 없음) → V(170년대 초 상여금 거절) → VI(그날 밤 '철학자' 비웃음) → VII(전쟁 뒤 환불, 훗날)
성별 균형(11/4 기획 원칙): 현대 장면 여성 6·남성 6·가족 2, 조연에 여성(과부) 목소리
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
from ep01 import STYLE, MEMO, EMP, VT, G, M

TAG = "ep03"
CASTV = {"CRIER": "tc_66e26710ac44cf7c7ebfdb71",     # 경매꾼 (준성)
         "SENATOR": "tc_675a73eb789ff3ea6cc80235",   # 원로원 의원 (권일)
         "WIDOW": "tc_6a4f2130d153a5cac8e19996",     # 과부 (지선, 중년 여성)
         "SOLDIER": "tc_6a867e6bd49b8f6a07db59da"}   # 병사 대표 (하데스)
MODN = ("Same painterly cinematic oil-painting texture and fine film grain, but a cool desaturated blue-grey palette with only one small warm light, "
        "horizontal 16:9 widescreen film frame, main subject in the middle band of the frame, nothing important in the top and bottom eighth of the frame, faces clearly lit. "
        "Absolutely no text, no letters, no numbers, no readable screens, no watermark, no brands anywhere.")
FORUM = "the Forum of Trajan in Rome, tall marble colonnades and the great column of Trajan behind, grey winter daylight"
CRIER = "a stout Roman auctioneer in a plain brown tunic with a loud open mouth"
SEN = "two Roman senators in white togas with broad purple stripes"
FACE = " His face is in the middle of the frame, fully visible and lit, with space above his head."

IMAGES = {
 # 훅 — 169년 경매
 "e3_forum": ("Wide view of a public auction in " + FORUM + ": a wooden auction platform piled with gold cups, crystal bowls and marble statues, " + CRIER +
              " holding up a shimmering gold-embroidered silk gown, a large crowd of Roman citizens pressing around, some pointing and laughing.", STYLE),
 "e3_gown": ("Close-up of " + CRIER + " on a wooden platform lifting high a magnificent purple silk gown embroidered with gold thread, the fabric catching the light, blurred crowd faces below." + FACE, STYLE),
 "e3_senators": ("Medium shot of " + SEN + " standing apart from a crowd in a marble colonnade, one leaning to whisper in the other's ear with a contemptuous smirk, both looking toward something off-camera." + FACE.replace("His face is", "Their faces are"), STYLE),
 "e3_watch": ("Medium close portrait of " + EMP + " standing alone at a high marble balcony above a crowded forum, watching quietly with calm steady eyes, no crown, grey daylight on his face." + FACE, STYLE),
 # 상황 — 166년, 역병
 "e3_triumph": ("A Roman triumphal procession returning to Rome in 166 AD, legionaries with standards and laurels marching through a city gate, cheering crowds on the roofs, "
                "but one exhausted soldier in the front row looks feverish and pale, coughing into his hand.", STYLE),
 "e3_plague": ("A narrow Roman street during a plague at dusk, a wooden cart carrying bodies wrapped in white cloth pulled by a hooded man, shuttered houses, a woman covering her mouth with a shawl in a doorway, smoke from braziers.", STYLE),
 "e3_galen": ("Inside a dim Roman sick room, an older Greek physician with a short grey beard kneeling beside a feverish patient on a straw mattress, examining the red rash on the patient's arm by lamplight." + FACE, STYLE),
 # 문장 I — 장례
 "e3_widow": ("A poor Roman woman of about forty in a simple dark shawl standing beside a modest burial pyre at the edge of the city at dawn, a Roman official in a plain toga quietly handing coins to the pyre keeper, the woman looking surprised and grateful." + FACE.replace("His", "Her").replace("his", "her"), STYLE),
 "e3_vine": ("A sunlit grapevine heavy with ripe dark grapes on an old Roman stone terrace, warm golden light through the leaves, a few bees, peaceful, no people.", MEMO),
 # 문장 II — 루키우스
 "e3_carriage": ("A Roman imperial carriage stopped on a frozen winter road in northern Italy at dusk, soldiers with torches crowding around its open door in alarm, snow on the ground.", STYLE),
 "e3_lucius": ("Inside a dim Roman imperial villa at night, a handsome bearded man of about forty lying still on a bed under a purple blanket, eyes closed, and " + EMP + " sitting beside him holding his hand, head bowed in grief, one candle.", STYLE),
 "e3_rumor": ("Night in a Roman tavern, a group of men leaning close over cups of wine, whispering a rumor with sly expressions, one glancing over his shoulder, oil lamps." + FACE.replace("His face is", "Their faces are"), STYLE),
 # 문장 III — 빈 금고
 "e3_treasury": ("A vast Roman treasury vault with many large open wooden chests that are almost completely empty, only a few scattered coins at the bottom, a single torch, a clerk holding a wax tablet staring in dismay.", STYLE),
 "e3_senate": ("Inside the Roman Senate house (Curia), rows of senators in white togas on marble benches, one senator standing and gesturing insistently toward " + EMP +
               " who sits at the front with his face visible, listening with a firm, calm expression.", STYLE),
 # 문장 IV — 두 달의 경매
 "e3_cups": ("Close-up of an auction table in " + FORUM + ": golden drinking cups, rock-crystal goblets, jeweled boxes and a small bronze statue being handed to a buyer, coins changing hands.", STYLE),
 # 문장 V — 상여금
 "e3_soldiers": ("A Roman army camp on the Danube after a victory, a crowd of weary legionaries with dented shields gathered before a wooden tribunal, a scarred veteran in front raising his fist and shouting a demand." + FACE, STYLE),
 "e3_refuse": ("Close portrait of " + EMP + " standing on a wooden tribunal before soldiers, wind in his cloak, speaking with a firm, sad but resolute face, torches and standards behind him." + FACE, STYLE),
 # 문장 VII — 환불, 훗날
 "e3_return": ("A Roman office in a marble hall, a well-dressed Roman merchant handing a golden cup back across a table to an imperial clerk who counts coins back into his hand, calm and polite, scrolls on shelves.", STYLE),
 "e3_statue": ("The bronze equestrian statue of Marcus Aurelius on the Capitoline Hill at dawn, golden light, a few pigeons, ancient stones, quiet and timeless.", MEMO),
 "e3_morning": ("Dawn over a Roman legionary camp on the Danube, " + EMP + " walking alone between the tents in his crimson cloak, seen from the side, soldiers starting fires, soft golden light, quiet resolve.", STYLE),
 # 오늘의 장면 (현대) — 여성 6·남성 6·가족 2
 "e3m_kitchen": ("A Korean woman in her late fifties setting a simple dinner table alone in a small apartment kitchen in the evening, her family's chairs empty, tired but gentle face, warm pendant light.", MODN),
 "e3m_family": ("A Korean family of four eating dinner, the husband and teenage children looking at their phones while the mother in her fifties quietly refills their bowls, nobody looking at her.", MODN),
 "e3m_hospital": ("A Korean woman in her fifties sitting beside her elderly mother's hospital bed at night, holding her mother's hand, exhausted, a small lamp, the city outside the window.", MODN),
 "e3m_funeral": ("A Korean funeral hall, relatives in black clothes chatting in a group in the background, while a woman in her fifties in black mourning clothes sits alone in front, quiet and tired.", MODN),
 "e3m_promotion": ("A modern Korean office, a man in his late forties standing at the back of a meeting room watching his boss being congratulated by colleagues, his face calm but hurt.", MODN),
 "e3m_desk": ("A Korean man in his late forties alone at his office desk late at night, finishing his work under a desk lamp, a small satisfied smile, the empty office around him dark.", MODN),
 "e3m_nurse": ("A Korean nurse in her forties in a dim hospital ward at three in the morning gently pulling a blanket over a sleeping elderly patient, only the monitor light glowing.", MODN),
 "e3m_guard": ("An older Korean apartment security guard in his sixties sweeping fallen leaves in front of the apartment entrance at dawn, no one around, calm and diligent.", MODN),
 "e3m_mother": ("A Korean mother in her forties in a living room kneeling to talk with her ten-year-old daughter, who is pouting and pointing at a friend's phone in a photo, the mother firm but gentle.", MODN),
 "e3m_meeting": ("A Korean man in his fifties standing alone at the head of a meeting table after making an unpopular decision, colleagues looking away, his face resolute.", MODN),
 "e3m_volunteer": ("An older Korean man in his seventies in an apron quietly serving rice at a free community meal center, elderly people sitting at long tables, warm light, no cameras.", MODN),
 "e3m_volunteer2": ("A Korean woman in her forties in a park handing a warm drink to an elderly homeless man on a bench, both seen from the side, winter evening.", MODN),
 "e3m_retire": ("A Korean man in his early sixties walking out of an office building at dusk carrying a small cardboard box of his belongings and a bouquet, looking back once.", MODN),
 "e3m_home": ("An older Korean couple in their sixties sitting together on a sofa at home looking at an old photo album with their adult daughter, warm lamp light, gentle smiles.", MODN),
}
VIDEOS = {
 "ev3_forum": ("e3_forum", "The auctioneer slowly waves the shimmering silk gown above his head while the crowd laughs and points; banners and cloth move in the wind."),
 "ev3_plague": ("e3_plague", "The cart rolls slowly down the street, the hooded man pulling it, smoke drifting from the braziers; the woman in the doorway lowers her eyes."),
 "ev3_carriage": ("e3_carriage", "Torches flicker in the wind and soldiers rush toward the carriage door while light snow falls."),
}

HOOK = [
 ("h_cr", "CRIER", "황후의 비단옷이오! 금실로 수놓은, 황후의 옷이오!"),
 ("h1", G, "기원후 백육십구 년, 로마 트라야누스 광장. 황제가, 궁전의 보물을 시장에 내놓았습니다."),
 ("h2", G, "황금 잔과 수정 그릇, 그리고 황후의 옷까지. 사람들은 수군거렸습니다."),
 ("h_sen", "SENATOR", "철학에 빠진 황제가, 이제는 장사꾼이 되었군."),
 ("m_h1", M, "아무도 알아주지 않을 것이다."),
 ("m_h2", M, "!그래도, 나는 한다."),
]

LINES = [
 # 상황 (삼 년 전)
 ("s1", G, "삼 년 전. 동방 원정을 마친 군대가, 승리의 행렬을 이루며 로마로 돌아왔습니다."),
 ("s2", G, "그런데 그 행렬과 함께, 보이지 않는 손님이 따라 들어왔습니다. 역병이었습니다."),
 ("s3", G, "훗날 안토니누스 역병이라 불린 이 병은, 제국 곳곳에서 수많은 목숨을 앗아 갔습니다. 의사 갈레노스는, 열병과 붉은 발진을 기록으로 남겼습니다."),
 ("s4", G, "황제는 로마를 떠나지 않았습니다."),
 # 문장 I
 ("d1a", G, "시신은 수레에 실려 나갔습니다. 가난한 사람들에게는, 장례를 치를 돈조차 없었습니다."),
 ("d1b", G, "황제는 나라의 돈으로, 가난한 이들의 장례를 치러 주게 했다고 전해집니다."),
 ("w1", "WIDOW", "우리 남편 장례를, 황제께서 치러 주셨대요. 그런데 그분 얼굴은, 한 번도 못 봤어요."),
 ("d1c", G, "황제는 그 일을, 어디에도 드러내지 않았습니다."),
 ("m1a", M, "어떤 사람은 남에게 잘해 주고, 그 빚을 꼭 받아 내려 한다."),
 ("m1b", M, "어떤 사람은 입으로는 말하지 않아도, 마음속에 장부를 적는다."),
 ("m1c", M, "포도나무가 포도를 맺듯, 선을 행하고 아무것도 바라지 마라."),
 ("d1d", G, "황제는 좋은 사람을, 포도를 맺고도 자랑하지 않는 포도나무에 비유했습니다. 열매를 맺는 것이 포도나무의 본성이듯, 선을 행하는 것이 사람의 본성이라는 겁니다."),
 ("d1e", G, "삼십 년 동안 차려 온 저녁 밥상. 고맙다는 말은 없는데, 내일도 밥은 차려야 합니다."),
 ("d1f", G, "!알아주는 사람이 없어도, 그 밥상은 가족을 살렸습니다."),
 ("d1g", G, "오늘 밤에는, 오늘 한 좋은 일 하나를 떠올리고, 그 일을 아무에게도 말하지 않아 보세요. 포도나무처럼요."),
 ("d1h", G, "그리고 그해 겨울, 황제에게 또 하나의 소식이 날아들었습니다."),
 # 문장 II (169년 겨울)
 ("d2a", G, "북쪽 전선으로 함께 가던 길, 공동 황제이자 아우인 루키우스가, 마차 안에서 쓰러졌습니다."),
 ("d2b", G, "루키우스는 끝내 일어나지 못했습니다. 황제는 아우를 신으로 모시는 장례를, 정성껏 치러 주었습니다."),
 ("d2c", G, "그러나 로마에는, 이상한 소문이 돌았습니다."),
 ("r_sen", "SENATOR", "황제가, 자기 아우를 독살했다더군."),
 ("d2d", G, "황제는 그 소문에, 한마디도 답하지 않았습니다."),
 ("m2a", M, "너는 선을 행했고, 그는 그 덕을 보았다."),
 ("m2b", M, "그런데 왜, 바보처럼 세 번째 것을 찾는가."),
 ("m2c", M, "선을 행했으면 그것으로 끝이다. 세 번째 것을 바라지 마라."),
 ("d2e", G, "황제는 선을 행하는 일과, 그 일로 인정받는 일을 분명히 나누었습니다. 앞의 것은 내 몫이고, 뒤의 것은 남의 몫이라는 겁니다."),
 ("d2f", G, "십 년 동안 홀로 어머니 병간호를 했습니다. 그런데 장례식장에서, 친척들은 한마디씩 거들기만 했습니다."),
 ("d2g", G, "!내가 한 일은, 남이 알아줘야 완성되는 일이 아닙니다."),
 ("d2h", G, "오늘 밤에는, 내가 한 일에 붙여 둔 알아 달라는 마음을, 살짝 떼어 내 보세요."),
 ("d2i", G, "그해 봄, 제국의 금고가 바닥을 드러냈습니다."),
 # 문장 III (169년 봄)
 ("d3a", G, "역병으로 사람이 줄고, 북쪽에서는 게르만족이 국경을 넘어왔습니다. 그런데 군대를 꾸릴 돈이, 없었습니다."),
 ("d3b", G, "원로원은 손쉬운 길을 말했습니다."),
 ("t_sen", "SENATOR", "세금을 더 걷으면 됩니다, 폐하."),
 ("d3c", G, "그러나 황제는 고개를 저었습니다. 그리고 아무도 예상하지 못한 결정을 내렸습니다."),
 ("m3x", M, "궁전의 것을, 팔겠소."),
 ("m3a", M, "죽은 뒤의 이름에 매달리는 사람은 잊는다."),
 ("m3b", M, "그를 기억하는 사람들도, 곧 모두 떠난다는 것을."),
 ("m3c", M, "이름은 금방 잊힌다. 지금, 옳은 일을 하라."),
 ("d3d", G, "세금을 올리면 쉬웠을 겁니다. 하지만 그 짐은, 역병에 지친 백성이 졌을 겁니다. 황제는 이름을 남기는 일보다, 오늘의 옳은 일을 앞에 두었습니다."),
 ("d3e", G, "또 밀린 승진 발표날. 밤새 만든 보고서는, 상사의 이름으로 올라갔습니다."),
 ("d3f", G, "!이름은 남이 가져가도, 그 일을 해낸 사람은 나입니다."),
 ("d3g", G, "오늘 밤에는, 이름 없이도 뿌듯했던 오늘의 일 하나를, 떠올려 보세요."),
 ("d3h", G, "그렇게 트라야누스 광장에, 경매대가 세워졌습니다."),
 # 문장 IV (두 달의 경매)
 ("d4a", G, "경매는, 두 달 동안 이어졌다고 전해집니다. 황금 잔과 수정 그릇, 대대로 내려온 조각상까지 하나씩 팔려 나갔습니다."),
 ("d4b", G, "사람들은 웃었습니다. 황제가 체면을 잃었다고. 황후의 옷까지 내다 파는 황제라고."),
 ("c4", "CRIER", "더 부르실 분 없소? 팔렸소!"),
 ("d4c", G, "그렇게 모은 돈으로, 황제는 백성에게 세금을 더 걷지 않고 군대를 꾸렸습니다."),
 ("m4a", M, "추울 때든 따뜻할 때든, 졸릴 때든 푹 잤을 때든."),
 ("m4b", M, "칭찬을 듣든, 비난을 듣든."),
 ("m4c", M, "칭찬을 듣든 비난을 듣든, 해야 할 일을 하라."),
 ("d4d", G, "스토아 철학자들은 이것을, 의무라고 불렀습니다. 남의 박수와 상관없이, 내 자리에서 마땅히 할 일입니다."),
 ("d4e", G, "새벽 세 시, 아무도 보지 않는 병동. 간호사는 잠든 환자의 이불을, 다시 덮어 줍니다."),
 ("d4f", G, "!아무도 보지 않는 일이, 세상을 굴러가게 합니다."),
 ("d4g", G, "오늘 밤에는, 내일 아무도 보지 않는 곳에서 할 일 하나를, 정해 보세요."),
 ("d4h", G, "몇 해 뒤, 다뉴브 전선. 큰 승리를 거둔 병사들이, 황제 앞에 모여들었습니다."),
 # 문장 V (170년대 초)
 ("d5a", G, "병사들은 상여금을 요구했습니다. 목숨을 걸고 싸웠으니, 그만한 상을 달라는 것이었습니다."),
 ("v_sol", "SOLDIER", "폐하, 우리는 피를 흘렸습니다. 그에 맞는 상을 주십시오."),
 ("d5b", G, "황제는 거절했습니다. 그리고 이렇게 말했다고 전해집니다."),
 ("m5x", M, "그대들에게 더 주는 것은, 그대들 부모와 형제의 피에서 짜내는 것이오."),
 ("d5c", G, "병사들은 투덜거렸습니다. 인기를 얻기 쉬운 길을, 황제는 또 마다한 것입니다."),
 ("m5a", M, "사람은 누구보다 자기를 사랑하면서도,"),
 ("m5b", M, "자기 생각보다, 남의 생각을 더 무겁게 여긴다."),
 ("m5c", M, "남의 평가를, 내 판단보다 앞에 두지 마라."),
 ("d5d", G, "황제에게 인기는 목표가 아니었습니다. 옳다고 판단한 일이 인기가 없을 때, 그는 판단 쪽을 택했습니다."),
 ("d5e", G, "우리 반에서 나만 휴대폰이 없다는 아이의 말. 엄마의 마음은, 하루에도 몇 번씩 흔들립니다."),
 ("d5f", G, "!미움받는 결정이, 틀린 결정은 아닙니다."),
 ("d5g", G, "오늘 밤에는, 남의 눈 때문에 미뤄 둔 옳은 결정 하나를, 적어 보세요."),
 ("d5h", G, "그날 밤, 막사에서 황제는, 자신을 비웃는 말들을 떠올렸습니다."),
 # 문장 VI (그날 밤)
 ("d6a", G, "로마에는 그를, 철학자 황제라고 비꼬는 사람들이 있었습니다. 책을 붙들고 생각만 하는 황제라고."),
 ("d6b", G, "그러나 그날 밤 일기에, 황제는 다른 이야기를 적었습니다."),
 ("m6a", M, "좋은 사람이란, 어떤 사람인가."),
 ("m6b", M, "그것을 따지는 데, 남은 날을 쓰지 마라."),
 ("m6c", M, "좋은 사람이 무엇인지 논하지 말고, 좋은 사람이 되어라."),
 ("d6c", G, "황제에게 철학은, 말이 아니라 행동이었습니다. 경매대에 오른 황후의 옷이, 그가 쓴 어떤 문장보다 그의 철학을 잘 보여 주었습니다."),
 ("d6d", G, "매주 토요일, 무료 급식소에 말없이 나와 밥을 푸는 할아버지가 있습니다. 사진 한 장 남기지 않습니다."),
 ("d6e", G, "!말보다 먼저, 손이 움직이는 사람. 그 사람이, 좋은 사람입니다."),
 ("d6f", G, "오늘 밤에는, 말로만 해 왔던 좋은 일 하나를, 이번 주에 직접 해 보세요."),
 ("d6i", G, "그리고 전쟁이 끝난 뒤, 황제는 경매에서 물건을 산 사람들에게, 한 가지를 알렸습니다."),
 # 문장 VII (전쟁 뒤, 훗날)
 ("d7a", G, "원하는 사람은 물건을 돌려주고, 낸 돈을 다시 받아 가도 된다고. 돌려주지 않는다고 해서, 아무도 벌하지 않았습니다."),
 ("d7b", G, "누군가는 돌려주었고, 누군가는 간직했습니다. 황제는 그 누구에게도, 고맙다는 말을 요구하지 않았습니다."),
 ("d7c", G, "그리고 오랜 세월이 흐른 뒤, 사람들은 그를 로마 오현제의 마지막 황제로 기억했습니다. 그를 알아준 것은, 시간이었습니다."),
 ("m7a", M, "나는 공동체를 위해, 무언가를 했는가."),
 ("m7b", M, "그렇다면, 나는 이미 보상을 받았다."),
 ("m7c", M, "공동체를 위해 일했다면, 나는 이미 보상받았다."),
 ("d7d", G, "황제는 보상을 바깥에서 찾지 않았습니다. 좋은 일을 한 순간, 그 사람은 이미 조금 더 좋은 사람이 되어 있다는 겁니다."),
 ("d7e", G, "삼십 년 다닌 회사의 마지막 날. 송별회는 짧았고, 누구도 내 이름을 오래 기억하지 않을 겁니다."),
 ("d7f", G, "!하지만 그 삼십 년이, 한 가족을 키웠습니다."),
 ("d7g", G, "오늘 밤에는, 내가 오래 해 온 일 하나에게, 잘했다고 말해 주세요."),
 # 정리·끝
 ("r1", G, "아무도 알아주지 않을 때, 황제가 일기에 남긴 일곱 문장을 다시 짚어 보겠습니다."),
 ("r2", G, "첫째, 포도나무처럼, 선을 행하고 바라지 마라."),
 ("r3", G, "둘째, 세 번째 것을 바라지 마라."),
 ("r4", G, "셋째, 이름은 금방 잊힌다. 지금, 옳은 일을 하라."),
 ("r5", G, "넷째, 칭찬을 듣든 비난을 듣든, 할 일을 하라."),
 ("r6", G, "다섯째, 남의 평가를, 내 판단보다 앞에 두지 마라."),
 ("r7", G, "여섯째, 좋은 사람을 논하지 말고, 좋은 사람이 되어라."),
 ("r8", G, "일곱째, 선을 행했다면, 이미 보상받았다."),
 ("r9", G, "!알아주는 사람이 없어도, 좋은 일은 이미 일어났습니다."),
 ("o1", G, "오늘 이야기가 마음에 닿으셨다면, 구독과 좋아요로 황제의 일기를 함께 이어 가 주세요."),
 ("o2", G, "다음 이야기에서는, 아내를 잃은 밤 황제가 일기에 남긴 문장들을 들려드리겠습니다."),
]
EMO = {"h_cr": "toneup", "h_sen": "tonedown", "r_sen": "whisper", "t_sen": "tonedown", "c4": "toneup", "v_sol": "angry", "w1": "sad"}


def clean(t): return t.lstrip("!")


def gen():
    jobs = [{"id": k, "kind": "image", "endpoint": "xai/grok-imagine-image-2.0", "body": {"aspect_ratio": "16:9", "prompt": p + " " + st}} for k, (p, st) in IMAGES.items()]
    json.dump(jobs, open(os.path.join(ROOT, "scripts/side/gen/EDL261104-ep03.json"), "w"), ensure_ascii=False, indent=1)
    V = []
    for n, v, t in HOOK + LINES:
        V.append({"name": n, "id": CASTV.get(v, v), "line": clean(t), "emotion": EMO.get(n, "tonedown"), "tempo": 0.85 if v == M else 1.0})
    json.dump({"requested": "2026-11-04T18:00", "note": "황제의 일기 EPISODE 3 전편 녹음 (해설 건석, 황제 명일, 조연 경매꾼·원로원·과부·병사)", "tag": TAG, "keep": True, "lang": "kor",
               "model": "ssfm-v30", "emotion": "tonedown", "tempo": 1.0, "voices": V}, open(os.path.join(ROOT, "scripts/side/voices_req.json"), "w"), ensure_ascii=False, indent=1)
    print(len(jobs), "그림,", len(V), "줄 녹음")


def genv():
    vj = [{"id": k, "kind": "video", "endpoint": "alibaba/wan-3.0/image-to-video", "image": f"social/side/gen/{src}.jpeg", "body": {"duration": 5, "prompt": p + " " + VT}} for k, (src, p) in VIDEOS.items()]
    json.dump(vj, open(os.path.join(ROOT, "scripts/side/gen/EDL261104-ep03v.json"), "w"), ensure_ascii=False, indent=1)
    print(len(vj), "영상")


if __name__ == "__main__":
    if sys.argv[1] == "gen": gen()
    elif sys.argv[1] == "genv": genv()
    else:
        import ep03_spec; ep03_spec.build()
