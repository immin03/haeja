"""명상록 실화극 1호 「배신한 사람에게 하는 가장 완벽한 복수」 (약 9~10분)
사실: 카시우스 디오 72권 §22~29. 각색: 황제·카시우스·베루스의 대사와 천막 장면, 황후 편지의 내용.
python3 cine_ep01.py gen | genv N | spec
"""
import re, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE); import cine01 as C
TAG = "cep01"; N, M, V = C.G, C.M, C.V; CAS = "tc_66860d458ca8b2dc5f72b865"
FILM, EMP, GEN, SEED, WAN = C.FILM, C.EMP, C.GEN, C.SEED, C.WAN
CASS = ("the Roman general Avidius Cassius at about forty-five, lean hawk-nosed face, close-cropped black hair, short black beard, hard pale eyes, gilded bronze muscle cuirass, purple-red cloak")
FAU = ("the Roman empress Faustina the Younger at about forty-five, elegant tired face, dark hair braided and pinned up, deep blue wool stola, gold earrings")
SYR = "in the Roman province of Syria in harsh dry white sunlight, pale stone and dust, deep hard shadows"
DAN = "at a Roman winter legion camp on the Danube frontier, blue-grey dusk, snow on leather tents, warm orange campfires in the distance, breath visible in the cold"
TENT2 = "inside a dark leather Roman command tent on the Danube at night, an iron brazier glowing orange, deep blue shadow"
MC = " His mouth stays closed."
IMG = {  # 이름: (모델 S/W, 그림, 움직임)
 "ride": ("W", "Wide shot of " + CASS + " riding a dark horse along a long column of Roman legionaries " + SYR + ", red banners without symbols.", "He rides slowly forward along the marching column; dust rises; slow tracking shot."),
 "city": ("W", "Epic wide shot of a great mud-brick Mesopotamian walled city burning at dusk beside a wide river, smoke columns, tiny Roman siege lines in the foreground.", "Smoke drifts and flames flicker; very slow push-in."),
 "casp": ("W", "Close portrait, three-quarter view, of " + CASS + ", " + SYR + ", calm proud expression, mouth closed." + C.FACE, "He stays still, a slow blink, a slight turn of the head; mouth stays closed; very slow push-in."),
 "order": ("W", "Close-up " + TENT2 + ": an older man's hand in a crimson wool sleeve pressing a bronze seal ring into dark wax on a rolled papyrus, a blurred document with no readable writing.", "The hand presses the ring into the wax and lifts it slowly."),
 "snow": ("W", "Wide shot " + DAN + ", rows of tents, sentries with cloaks, grey river beyond.", "Snow falls lightly, smoke drifts, a sentry walks slowly; very slow pan."),
 "sick": ("W", "Medium shot " + TENT2 + ": " + EMP + " lying ill on a low camp bed under wool blankets, sweat on his pale face, eyes half closed, a clay cup beside him." + MC, "He breathes slowly with difficulty, a weak slow blink; mouth stays closed; brazier light flickers."),
 "boy": ("W", "Medium shot " + TENT2 + ": a Roman boy of thirteen with curly golden-brown hair and a white tunic with a purple stripe, standing by a tent pole, uneasy eyes, face fully visible and lit." + " His mouth stays closed.", "He looks down and then toward the tent flap; mouth stays closed; light flickers."),
 "fau": ("W", "Close portrait, three-quarter view, of " + FAU + ", " + TENT2.replace("inside", "standing inside") + ", looking down with fear held behind a composed face, firelight on her cheek. Her face is in the middle of the frame, fully visible, mouth closed.", "She breathes slowly, her eyes lift a little; mouth stays closed; light flickers; very slow push-in."),
 "write": ("W", "Close-up " + TENT2 + " by a small oil lamp: a woman's hand with a gold bracelet writing with a reed pen on a sheet of papyrus, only blurred dark smudges of ink with nothing readable.", "The hand writes slowly; the lamp flame flickers."),
 "courier": ("W", "Wide shot of a lone Roman courier on a horse galloping along a frozen road through bare black trees at blue dusk, cloak flying.", "He gallops past from left to right, snow kicked up; camera pans to follow."),
 "msgr": ("W", "Medium shot " + SYR + " under a command awning: a dusty Roman messenger kneeling, holding up a rolled letter, before " + CASS + " seen from behind.", "The messenger bows his head and holds up the letter; dust drifts."),
 "decide": ("W", "Close portrait of " + CASS + ", shade of an awning in Syria, reading a small scroll, jaw clenched, a cold decision in his eyes, mouth closed." + C.FACE, "He lowers the scroll slowly and stares ahead; mouth stays closed; very slow push-in."),
 "read": ("W", "Close portrait, three-quarter view, of " + EMP + ", " + TENT2 + ", thin and recovering, holding a small scroll and reading it, his face slowly going still." + C.FACE + MC, "He reads, his eyes stop moving, he slowly lowers the scroll; mouth stays closed; very slow push-in."),
 "alone": ("W", "Medium shot from behind and to the side of " + EMP + ", standing alone at the open flap of a tent at night looking out over snow and distant campfires, deep blue night, firelight on his shoulder.", "He stands still, his breath visible, snow falling; very slow push-in."),
 "camp": ("W", "Medium shot " + DAN + ": four Roman legionaries in cloaks huddled around a campfire, leaning in and whispering, worried faces lit by fire.", "They glance around uneasily and lean closer; fire flickers."),
 "ppl": ("W", "Close shot of a grizzled Roman legionary in a snow-dusted helmet standing in formation, listening, weathered face fully visible, mouth closed, breath visible in the cold, " + "blue dusk light.", "He stands still and listens, a slow blink, breath in the cold; mouth stays closed."),
 "envoy": ("W", "Medium shot " + DAN.replace("at a", "in a clearing at a") + ": bearded Sarmatian envoys in furs and scale armour bowing before a Roman officer at a wooden table, a treaty being made.", "An envoy bows and steps back; snow falls lightly."),
 "chief": ("W", "Close shot of a bearded Sarmatian chieftain in furs and a scale coat, offering with an open hand, firelit, snow behind him, mouth closed.", "He extends his open hand and nods slowly; mouth stays closed."),
 "refuse": ("W", "Over-the-shoulder shot from behind " + EMP + " in a snowy camp, his crimson shoulder in the foreground, facing a fur-clad chieftain who lowers his hand.", "The chieftain slowly lowers his hand and bows; snow falls."),
 "march": ("W", "Epic wide shot of a long Roman army column crossing mountain passes toward the east at sunrise, standards without symbols, dust and cold light.", "The column marches slowly; camera glides very slowly."),
 "ehorse": ("W", "Medium shot of " + EMP + " riding a grey horse at the head of the column, tired resolute eyes, morning light." + MC, "He rides steadily forward; mouth stays closed; camera moves with him."),
 "walk": ("W", "Medium shot of " + CASS + " walking alone on foot along a pale dusty camp road " + SYR + ", tents behind him, unaware.", "He walks slowly toward the camera; dust drifts."),
 "dec": ("W", "Low wide shot " + SYR + ": a Roman cavalryman's silhouette dismounting beside a fallen figure half hidden behind a horse, dust in the hard light, nothing graphic, no blood.", "The silhouette dismounts and walks forward; dust drifts."),
 "desert": ("W", "Vast empty pale Syrian plain under white sky, a single riderless horse standing far away, heat haze, nothing else.", "Heat haze shimmers; the horse flicks its tail; the camera stays still."),
 "bag": ("W", "Medium shot of two Roman riders on a dusty road at sunset, one with a closed dark leather sack tied to his saddle, seen from behind, long shadows.", "They ride slowly away from the camera; dust rises."),
 "grave": ("W", "Close shot at dusk of two Roman soldiers' hands and iron spades filling a small hole in dry earth, plain and quiet, nothing graphic.", "Spades push dry earth into the hole slowly; dust drifts."),
 "senate": ("W", "Wide shot of the interior of the Roman Senate house, tiers of white-togaed senators in shafts of light, marble floor.", "Senators shift and murmur, light moves slowly; very slow push-in."),
 "sen2": ("W", "Medium shot of older Roman senators in white togas standing and raising their hands in demand, marble hall, shafts of light, mouths closed.", "They raise their hands; mouths stay closed; slow drift."),
 "scroll": ("W", "Close-up " + TENT2 + ": an older man's hand tying a cord around a rolled letter on a table, wax and seal ring beside it, nothing readable.", "The hand slowly ties the cord and rests."),
 "wife": ("W", "Medium shot " + TENT.replace("in the dry eastern provinces", "") if False else "Medium wide shot inside a large leather Roman command tent at night: " + EMP + " sitting at the table at left, and " + FAU + " standing at the far side of the tent, half in shadow, neither looking at the other, firelight between them. Mouths closed.", "Neither moves; firelight flickers between them; very slow push-in."),
 "out": ("W", "Inside a large leather Roman command tent before dawn: an empty wooden stool and table, a low stone fire pit with only grey ash and one thin thread of smoke, cold blue light.", "The thread of smoke rises slowly; the camera stays still."),
 "m1": ("W", "Photorealistic contemporary scene in a Seoul apartment at night, cool neutral light, desaturated: a middle-aged Korean woman at a kitchen table, her face lit by a smartphone she is holding, the screen not visible, mouth closed, face fully visible.", "She looks at the phone, her thumb hovering, a slow breath; mouth stays closed. Modern real footage."),
 "m2": ("W", "Photorealistic contemporary scene in a Seoul office at night, cool neutral light, desaturated: a Korean man in his fifties sitting alone at a desk, looking down at a smartphone on the desk, screen not visible, mouth closed, face fully visible.", "He stares at the phone and slowly turns it face down; mouth stays closed. Modern real footage."),
 "m3": ("W", "Photorealistic contemporary close-up, cool neutral light, desaturated: a hand holding a smartphone over a wooden table in a Seoul home, the screen glow visible but no readable content, a thumb hovering.", "The thumb hovers and slowly withdraws; the phone is set down. Modern real footage."),
 # Seedance: 움직임이 중요한 장면·말하는 장면
 "cloak": ("S", "Medium wide shot " + SYR + ": on a stone platform " + CASS + " having a purple cloak placed on his shoulders by two officers, ranks of Roman soldiers below raising swords, dust and hard sun.", "The officers settle the cloak on his shoulders, he steps forward and raises one arm; soldiers raise swords. Real-time motion."),
 "cheer": ("S", "Wide shot from behind ranks of Roman legionaries " + SYR + ", thrusting swords upward toward a distant figure on a platform, dust in the light.", "They thrust their swords upward and shout together; dust rises."),
 "ctalk": ("S", "Close portrait, nearly frontal, of " + CASS + " on a platform " + SYR + ", his lips parted in the middle of speaking loudly, fierce eyes." + C.FACE, "He speaks loudly to an army, his lips and jaw moving naturally in continuous speech for the whole shot; the camera is almost still."),
 "arrive": ("S", "Medium shot " + TENT2 + ": " + GEN + ", snow on his cloak, entering and holding out a sealed scroll to " + EMP + " who sits wrapped in a blanket, both faces lit by the brazier.", "The general steps forward and hands over the scroll; the emperor takes it slowly."),
 "ranks": ("S", "Epic wide shot " + DAN + ": a Roman legion in silent ranks in the snow, " + EMP + " climbing a low wooden platform before them, standards without symbols.", "He climbs the steps slowly and turns to face the army; snow falls; slow crane forward."),
 "spk": ("S", "Close portrait, three-quarter view, of " + EMP + " on a platform in the snow at blue dusk, thin and pale, crimson cloak, snowflakes in his grey hair, lips parted in the middle of speaking." + C.FACE, "He speaks slowly and sorrowfully to an army, his lips and jaw moving naturally in continuous speech for the whole shot; his breath visible; the camera is almost still."),
 "spkw": ("S", "Medium shot from the front and slightly below of " + EMP + " standing on a wooden platform in the snow, addressing unseen soldiers, one hand open at his side, lips parted, blue dusk, torches.", "He speaks with one open hand moving slightly, his lips and jaw moving naturally in continuous speech; breath visible; snow falls."),
 "strike": ("S", "Medium shot " + SYR + ": a mounted Roman centurion with a transverse-crested helmet riding past " + CASS + " on foot, a raised sword catching the sun, nothing graphic, no blood.", "The horseman rides past at speed and swings the sword; the man on foot staggers and clutches his neck with one hand; the horse carries the rider on; dust bursts. No blood."),
 "cent": ("S", "Medium tracking shot " + SYR + ": a Roman centurion with a transverse-crested helmet riding a horse at a walk along a dusty road, one hand drifting to his sword hilt, cold eyes.", "He rides forward and his hand closes slowly on the sword hilt; camera moves with him."),
 "bury": ("S", "Close portrait, three-quarter view, of " + EMP + " sitting in a tent in warm evening light, looking away toward the side, lips parted in the middle of speaking a few quiet words, tired eyes." + C.FACE, "He says a few quiet words, his lips moving naturally and slowly, then closes his mouth and looks down; the camera is almost still."),
 "diary": ("S", "Close-up " + TENT2 + " by an oil lamp: an old man's hand with a crimson sleeve writing with a reed pen on a wax tablet, only blurred strokes with nothing readable, ink pot and a small stack of papyrus beside it.", "The hand writes slowly, stops, then continues; the lamp flame flickers; very slow push-in."),
}
MOVE2 = "Same moment continuing. The camera drifts slowly sideways and pushes in closer. Small natural motion only."
L = []  # (클립, 목소리, 대사, 옵션)
def s(clip, v=None, t=None, **k): L.append((clip, v, t, k))
c = lambda n: "c1v_" + n
# 훅 (시안과 같은 대사)
s(c("chest"), N, "!배신한 사람에게 하는 가장 완벽한 복수.", pre=0.6, post=0.5, tin="black", fin=0.5, sfx=[["impact_2.mp3", 0.1, 0.3]])
s(c("enter"), N, "2천 년 전, 이 복수를 실제로 한 사람이 있습니다.", pre=0.15, post=0.05)
s(c("seal"), N, "여기, 그를 배신한 사람들의 이름이 든 상자가 있습니다.", pre=0.2, post=0.3)
s(c("hand"), N, "열어 보기만 하면 됩니다.", pre=0.2, post=0.2, dur=5.0, sfx=[["heartbeat_2.mp3", 1.8, 0.35]])
s(c("push"), N, "그런데 그는, 상자를 불 속에 넣었습니다.", pre=0.3, post=0.6, sfx=[["fire_2.mp3", 1.2, 0.8], ["impact_3.mp3", 1.5, 0.35]])
s(c("burn"), dur=3.6, amb=["fire_2.mp3", 0.75], tout="black", fout=0.7)
s("INTRO")
# 1 가장 믿은 장군
for a in [("ride", N, "십 년 전, 로마 동쪽 전선에 한 장군의 이름이 퍼졌습니다."), ("city", N, "파르티아와의 전쟁에서, 그는 적의 수도까지 밀고 들어갔습니다."), ("casp", N, "이름은 아비디우스 카시우스."), ("casp_b", N, "이 이름을 기억해 주십시오."),
          ("order", N, "황제는 그를 믿었습니다. 제국의 동쪽 전부를 맡겼습니다."), ("order_b", N, "군대도, 속주도, 전쟁을 치를 권한까지."),
          ("snow", N, "서기 175년 봄. 황제는 멀리 도나우 강 전선에 있었습니다."), ("snow_b", N, "쉰네 살의 황제는, 몇 해째 천막에서 겨울을 나고 있었습니다."),
          ("sick", N, "그리고 그해, 황제가 쓰러집니다."), ("sick_b", N, "병은 깊었고, 소문은 황제보다 빨리 움직였습니다."), ("boy", N, "후계자인 아들 코모두스는 아직 열세 살."),
          ("fau", N, "곁을 지키던 황후 파우스티나는 두려웠습니다."), ("fau_b", N, "남편이 죽으면, 어린 아들은 어떻게 될 것인가."),
          ("write", N, "전해지기로는, 황후가 카시우스에게 몰래 편지를 보냈다고 합니다."), ("write_b", N, "황제가 죽으면, 당신이 제국을 맡아 달라고."), ("courier", N, "이 편지를 기억해 주십시오. 진실은 아무도 모릅니다."),
          # 2 오보와 선언
          ("msgr", N, "몇 주 뒤, 시리아에 소식이 닿습니다."), ("msgr_b", N, "황제가 죽었다는 소식이었습니다."), ("cloak", N, "175년 4월, 카시우스는 군대 앞에서 황제를 선언합니다."), ("ctalk", CAS, "황제는 죽었다. 이제 로마는 나를 따르라."), ("cheer", N, "시리아와 이집트가 그를 따랐습니다."),
          ("msgr", N, "그런데 며칠 뒤, 다른 소식이 도착합니다."), ("decide", N, "황제는 살아 있었습니다."), ("decide_b", N, "돌아갈 수 있었습니다. 실수였다고 말할 수도 있었습니다."), ("casp", N, "그러나 그는 멈추지 않았습니다."),
          # 3 천막의 밤
          ("courier_b", N, "도나우의 황제에게 소식이 닿은 것은 그 뒤였습니다."), ("arrive", N, "소식을 전한 것은 카파도키아 총독, 베루스였습니다."), ("read", N, "가장 믿은 사람의 이름이, 그 편지에 있었습니다."), ("read_b", M, "그였단 말인가. 왜, 하필 그였는가."),
          ("alone", N, "황제는 처음에 이 소식을 숨겼습니다."), ("camp", N, "그러나 소문은 막사 사이로 번졌습니다."), ("camp_b", N, "병사들이 술렁이기 시작합니다."),
          # 4 연설
          ("ranks", N, "황제는 병사들을 모았습니다. 모두가 분노의 연설을 기다렸습니다."), ("spk", M, "병사들이여. 나는 분노하러 여기 선 것이 아니다."), ("ppl", M, "내 운명을 슬퍼하러 왔다."), ("spkw", M, "내게 가장 소중한 벗이, 나를 향해 음모를 꾸몄다."),
          ("ppl_b", M, "이 전쟁에서 내가 얻고 싶은 것은 하나다."), ("spk2", M, "내게 잘못한 사람을 용서하는 것."), ("spkw2", M, "우정을 저버린 사람의 친구로 남는 것이다.")]:
    s(*a)
s("ppl_b", dur=3.0, amb=["wind_2.mp3", 0.3], start=2.0)
for a in [("alone_b", N, "기록에 따르면, 황제는 그를 욕하지 않았습니다."), ("scroll", N, "그가 쓴 말은 하나, 은혜를 모르는 사람이었습니다."), ("diary", N, "『명상록』에는 이런 문장이 있습니다."), ("diary2", M, "은혜를 모르는 사람을 탓할 때는, 무엇보다 너 자신을 돌아보라."), ("scroll_b", N, "믿음을 준 것은, 나의 선택이었다는 뜻입니다."),
          # 5 동쪽으로
          ("envoy", N, "황제는 서둘러 북쪽 전쟁을 끝냅니다."), ("chief", N, "야만족들이 군사를 보내 돕겠다고 제안했습니다."), ("refuse", M, "로마 사람끼리의 일을, 너희에게 보일 수는 없다."), ("march", N, "그리고 군대를 이끌고 동쪽으로 향합니다."), ("ehorse", N, "살아 있는 카시우스를 만나, 용서하기 위해서였습니다."),
          # 6 일격
          ("walk", N, "그러나 그 만남은 오지 않습니다."), ("walk_b", N, "7월, 시리아."), ("cent", N, "백인대장 안토니우스가, 말을 타고 카시우스에게 다가옵니다."), ("strike", N, "칼이 목을 스쳤습니다. 치명상은 아니었습니다."), ("dec", N, "말은 그대로 지나갔고, 십인대장이 끝을 맺었습니다.")]:
    s(*a)
s("desert", N, "석 달 여엿새.", pre=0.5, post=3.0, dur=5.0)
s("desert_b", N, "그것이 그가 황제였던 시간입니다.", post=0.8)
for a in [("bag", N, "그의 머리가 황제에게 오고 있었습니다."), ("bury", M, "묻어라. 보지 않겠다."), ("grave", N, "도착하기도 전에 묻으라는 명령이었습니다."), ("read", M, "살아서 만나고 싶었다. 이제, 용서할 사람이 없다."), ("grave_b", N, "그는 이렇게 썼습니다."), ("diary", M, "가장 좋은 복수는, 그 사람과 같아지지 않는 것이다."),
          # 7 상자의 대화
          ("c1v_chest", N, "그리고 얼마 뒤, 상자 하나가 황제 앞에 도착합니다."), ("c1v_wide", V, "폐하. 카시우스의 편지들입니다."), ("c1v_emp_listen", V, "원로원 의원, 장군, 총독. 누가 그를 도왔는지, 전부 들어 있습니다."), ("c1v_ots", M, "읽어 보았는가."), ("c1v_gen_talk", V, "아닙니다. 폐하께서 먼저 보셔야 합니다."), ("c1v_emp_talk", M, "이걸 읽으면, 내일 나는 누구를 보게 되겠나."), ("c1v_hand", V, "폐하를 배신한 자들입니다."), ("c1v_emp_fire", M, "아니다. 내일부터는, 모든 사람이 배신자로 보일 것이다.")]:
    s(*a)
s("c1v_ots", M, "불을 가져오게.", pre=1.0, post=0.3, start=2.3)
s("c1v_gen_talk_b", V, "폐하. 저들은 폐하를 죽이려 했습니다.")
s("c1v_emp_talk_b", M, "그래서, 나까지 그들처럼 되어야 하겠나.", pre=0.5, post=1.3)
s("c1v_push", dur=4.6, amb=["fire_2.mp3", 0.7], sfx=[["fire_2.mp3", 1.2, 0.8]])
s("c1v_burn", N, "다른 기록은 베루스가 대신 태웠다고도 전합니다.", post=0.3)
s("c1v_seal", N, "확실한 것은, 그 이름들이 어디에도 남지 않았다는 것입니다.")
for a in [("senate", N, "원로원은 공모자들을 처벌하라고 요구했습니다."), ("sen2", M, "내 치세에, 원로원 의원이 피 흘리는 일은 없기를 바란다."), ("senate_b", N, "완전한 자비는 아니었습니다."), ("sen2_b", N, "카시우스의 아들은 살해됐고, 몇몇은 추방됐습니다."),
          ("wife", N, "그리고 황후."), ("wife_b", N, "그가 아내를 의심했는지, 기록은 말하지 않습니다."), ("diary2", N, "다만 그는, 신들에게 감사한 목록에 이렇게 적었습니다."), ("wife", M, "이런 아내가 내 곁에 있었던 것에, 감사한다.")]:
    s(*a)
s("out", dur=4.5, amb=["wind_2.mp3", 0.25], tout="black", fout=0.9)
# 8 현대 한 덩어리
for a in [("m3", N, "2026년, 서울.", {"tin": "black", "fin": 0.6}), ("m1", N, "오래 함께한 동업자, 가족, 친구.", {}), ("m2", N, "그 사람이 내 이야기를 어떻게 했는지 알 수 있는 메시지가", {}), ("m3_b", N, "오늘 손안에 있다면, 여러분은 열겠습니까.", {}), ("m1_b", N, "열면 이름을 얻습니다. 대신 그 이름을 평생 들고 삽니다.", {"tout": "black", "fout": 0.6})]:
    s(a[0], a[1], a[2], grade="none", amb=["night_2.mp3", 0.12], **a[3])
# 9 방법 3개
s("diary2", N, "배신한 사람에게 하는 복수, 세 가지입니다.", tin="black", fin=0.6)
s("scroll_b", N, "첫째, 욕하지 마십시오. 그 말은 내 입만 더럽힙니다.")
s("grave", N, "둘째, 그의 끝을 구경하지 마십시오.")
s("c1v_hand", N, "셋째, 알 필요 없는 것은 열지 마십시오.")
s("c1v_burn", N, "이것이, 황제가 한 복수였습니다.", post=1.0)
s("RECAP"); s("FINALE")


def clipid(k): return "cep1_" + k


def img_key(k): return {"spk2": "spk", "spkw2": "spkw", "diary2": "diary"}.get(k, k[:-2] if k.endswith("_b") else k)


def used():
    u = []
    for x in L:
        if x[0] in ("INTRO", "RECAP", "FINALE") or x[0].startswith("c1v_"): continue
        if x[0] not in u: u.append(x[0])
    return u


def gen():
    ids = list(IMG)
    jobs = [{"id": "cep1i_" + k, "kind": "image", "endpoint": "xai/grok-imagine-image-2.0", "body": {"aspect_ratio": "16:9", "prompt": v[1] + " " + FILM}} for k, v in IMG.items()]
    json.dump(jobs, open(os.path.join(ROOT, "scripts/side/gen/EDL261110-cep01i.json"), "w"), ensure_ascii=False, indent=1)
    lines = {}; vs = []
    for i, x in enumerate(L):
        if x[1]:
            n = f"l{i:03d}"; lines[n] = x
            vs.append({"name": n, "id": x[1], "line": x[2].lstrip("!"), "emotion": "tonedown", "tempo": 0.85 if x[1] == M else 1.0})
    for n, t, v in [("o1", "매일 밤, 황제처럼 생각하라. 황제의 일기.", N), ("o2", "좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다.", N)]:
        vs.append({"name": n, "id": v, "line": t, "emotion": "tonedown", "tempo": 1.0})
    json.dump({"requested": "2026-11-10T00:40", "note": "명상록 실화극 1호", "tag": TAG, "keep": True, "lang": "kor", "model": "ssfm-v30", "emotion": "tonedown", "tempo": 1.0, "voices": vs}, open(os.path.join(ROOT, "scripts/side/voices_req.json"), "w"), ensure_ascii=False, indent=1)
    print(len(jobs), "그림", len(vs), "대사", sum(len(x[2]) for x in L if x[1]), "자")


def videos():
    out = []
    for k in used():
        b = img_key(k); kind, _, mv = IMG[b]
        ep = SEED if kind == "S" else WAN
        out.append((k, ep, b, (MOVE2 if k.endswith("_b") else mv) + " " + C.MOVE))
    return out


def batches():
    cost = lambda e: 0.75 if e == SEED else 0.10
    v = sorted(videos(), key=lambda x: -cost(x[1])); bs = [[]]; t = 0
    for x in v:
        if t + cost(x[1]) > 2.95: bs.append([]); t = 0
        bs[-1].append(x); t += cost(x[1])
    return bs


def genv():
    bs = batches()
    for i, b in enumerate(bs, 1):
        jobs = [{"id": clipid(k), "kind": "video", "endpoint": e, "image": f"social/side/gen/cep1i_{im}.jpeg", "body": {"duration": 5, "prompt": p}} for k, e, im, p in b]
        json.dump(jobs, open(os.path.join(ROOT, f"scripts/side/gen/EDL261110-cep01v{i}.json"), "w"), ensure_ascii=False, indent=1)
    print(len(bs), "묶음", sum(len(b) for b in bs), "클립", round(sum(0.75 if x[1] == SEED else 0.1 for b in bs for x in b), 2), "달러")


# ---------- 11/10 대표 A안: 대사 중에는 말하는 입을 보여주지 않는다(듣는 사람·뒷모습·손). 카시우스 선언만 예외. 해설·무언 장면 추가로 8분 이상
SP = "on a wooden platform in the snow at blue dusk, torches"
IMG2 = {"sback": "Medium wide shot from directly behind " + EMP.replace("the Roman", "a Roman") + " standing " + SP + ", only his back and crimson cloak visible, facing ranks of Roman legionaries in the snow, no face of him visible.",
        "ppl2": "Close shot of a young Roman legionary in a snow-dusted helmet standing in formation at blue dusk, listening, eyes wet and shining, face fully visible, mouth closed, breath in the cold.",
        "ppl3": "Close shot of a scarred old Roman centurion with a transverse-crested helmet standing in the snow at blue dusk, listening with his jaw set, face fully visible, mouth closed, torchlight on his cheek.",
        "hand2": "Close-up of an older man's pale hand with a crimson wool sleeve gripping the snow-covered wooden rail of a platform at blue dusk, knuckles tight, snow falling, torches blurred behind.",
        "glis": "Close portrait, three-quarter view, of " + GEN + " " + TENT2.replace("inside a dark", "inside a dark") + ", standing and listening, conflicted eyes, firelight on his face." + C.FACE + " His mouth stays firmly closed.",
        "stop": "Close-up " + TENT2 + ": an older man's hand with a crimson sleeve raised palm-out in a quiet gesture of refusal, in the blurred background a kneeling soldier with a closed dark leather sack, nothing graphic."}
W_ = C.MOVE
VID2 = {"sback": ("sback", "cep1i_sback.jpeg", "His cloak moves in the wind, snow falls, the ranks stand still; very slow push-in. We never see his face."), "ppl2": ("ppl2", "cep1i_ppl2.jpeg", "He stands still, a slow blink, his eyes glisten, breath in the cold; mouth stays closed."),
        "ppl3": ("ppl3", "cep1i_ppl3.jpeg", "He stands still and slowly lowers his eyes; mouth stays closed; torchlight flickers."), "hand2": ("hand2", "cep1i_hand2.jpeg", "The hand tightens slowly on the rail, snow falling on it; very slow push-in."),
        "glis": ("glis", "cep1i_glis.jpeg", "He listens without moving, a slow blink; his mouth stays closed the whole shot; firelight flickers; very slow push-in."), "glis_b": ("glis", "cep1i_glis.jpeg", "He swallows and his eyes shift slightly toward the fire; his mouth stays closed the whole shot; very slow drift."),
        "glis_c": ("glis", "cep1i_glis.jpeg", "He slowly lowers his eyes in shame and bows his head slightly; his mouth stays closed the whole shot."), "elis": ("elis", "c1_emp_listen.jpeg", "He listens without moving, a slow blink; his mouth stays closed the whole shot; firelight flickers; very slow push-in."),
        "elis_b": ("elis", "c1_emp_listen.jpeg", "He looks down at the chest and back up slowly; his mouth stays closed the whole shot; firelight flickers."), "stop": ("stop", "cep1i_stop.jpeg", "The raised hand stays still and slowly closes; firelight flickers; the soldier lowers his head.")}
REPL = {40: "sback", 42: "ppl2", 44: "ppl3", 45: "hand2", 65: "stop", 77: "glis_b", 79: "elis_b"}   # 11/10 대표: 장군이 말한 직후엔 황제(입 보임)로   # 11/10 대표: 대화에 입 나오는 장면 두 개(74 장군, 80 황제)는 되살림
NEWV = {"n1": "시리아 출신의 그는, 규율이 무섭기로 이름난 장군이었습니다.", "n2": "곡창 이집트가 넘어가자, 원로원은 카시우스를 국가의 적으로 선포했습니다.", "n3": "제국의 절반이, 하룻밤 사이에 적이 될 수 있었습니다.", "n4": "그는 열세 살 아들을 곁으로 불러, 후계자로 세웠습니다.", "n5": "그 뒤 황제는 동쪽을 돌며, 반란에 가담한 도시들을 너그럽게 대했습니다."}
INS = {10: [("ride", "n1", {})], 27: [("senate", "n2", {})], 36: [("alone", None, {"dur": 3.5, "start": 1.5, "amb": ["wind_2.mp3", 0.3]}), ("snow_b", "n3", {})], 39: [("hand2", None, {"dur": 2.8, "amb": ["wind_2.mp3", 0.3], "sfx": [["heartbeat_2.mp3", 0.3, 0.4]]})],
       54: [("boy", "n4", {})], 55: [("march", None, {"dur": 3.5, "start": 1.5, "amb": ["wind_2.mp3", 0.2], "sfx": [["drum_1.mp3", 0.2, 0.5], ["war_7.mp3", 0.0, 0.25]]})], 69: [("diary", None, {"dur": 3.0, "start": 2.0})], 83: [("ehorse", "n5", {})]}
CAS_C = {"zeus": "tc_6a5882fe54564e2a06a218bb", "poseidon": "tc_6a8f9d53322676d2f0934a21", "hades": "tc_6a867e6bd49b8f6a07db59da", "jongdae": "tc_67e38d8c771b5511659c4534"}
CAS_PICK = "zeus"


def gen2():
    jobs = [{"id": "cep1i_" + k, "kind": "image", "endpoint": "xai/grok-imagine-image-2.0", "body": {"aspect_ratio": "16:9", "prompt": v + " " + FILM}} for k, v in IMG2.items()]
    json.dump(jobs, open(os.path.join(ROOT, "scripts/side/gen/EDL261110-cep01j.json"), "w"), ensure_ascii=False, indent=1)
    v = [{"id": clipid(k), "kind": "video", "endpoint": WAN, "image": "social/side/gen/" + im, "body": {"duration": 5, "prompt": p + " " + C.MOVE}} for k, (_, im, p) in VID2.items()]
    json.dump(v, open(os.path.join(ROOT, "scripts/side/gen/EDL261110-cep01v8.json"), "w"), ensure_ascii=False, indent=1)
    vs = [{"name": n, "id": N, "line": t, "emotion": "tonedown", "tempo": 1.0} for n, t in NEWV.items()]
    vs += [{"name": "cas_" + n, "id": i, "line": "황제는 죽었다. 이제 로마는 나를 따르라.", "emotion": "angry", "intensity": 1.2, "tempo": 0.92} for n, i in CAS_C.items()]
    json.dump({"requested": "2026-11-10T07:00", "note": "실화극 1호 보강", "tag": "cep01b", "keep": True, "lang": "kor", "model": "ssfm-v30", "emotion": "tonedown", "tempo": 1.0, "voices": vs}, open(os.path.join(ROOT, "scripts/side/voices_req.json"), "w"), ensure_ascii=False, indent=1)


# ---------- 렌더 설정 (python3 cine_ep01.py spec) — ED_FPS=24, 장면 길이는 클립(5초)에 최대한 맞춘다
FIRE = ["fire_4.mp3", 0.34]; FIRE2 = ["fire_0.mp3", 0.28]; COLD = ["wind_2.mp3", 0.24]; DRY = ["wind_1.mp3", 0.16]
AMB = {}
for keys, a in [("order sick boy fau write read arrive scroll wife diary bury", FIRE), ("out", ["wind_2.mp3", 0.2]), ("snow alone camp ranks spk spkw ppl envoy chief refuse courier march ehorse", COLD),
                ("ride casp msgr decide cloak ctalk cheer walk dec desert bag grave cent strike", DRY), ("city", ["fire_1.mp3", 0.3]), ("senate sen2", None)]:
    for k in keys.split(): AMB[k] = a
SFX = {"ride": [["horse_0.mp3", 0.2, 0.3]], "city": [["fire_1.mp3", 0.0, 0.35], ["war_3.mp3", 0.4, 0.14]], "casp": [["cinematic_2.mp3", 0.0, 0.35]], "order": [["paper_1.mp3", 0.5, 0.4]], "snow": [["wind_4.mp3", 0.0, 0.25]],
       "sick": [["heartbeat_1.mp3", 0.5, 0.3]], "sick_b": [["heartbeat_1.mp3", 0.3, 0.3]], "fau": [["heartbeat_3.mp3", 1.0, 0.18]], "write": [["paper_2.mp3", 0.4, 0.4]], "courier": [["horse_2.mp3", 0.1, 0.5]], "courier_b": [["horse_2.mp3", 0.1, 0.4]],
       "msgr": [["paper_3.mp3", 1.0, 0.35]], "msgr_b": [["impact_3.mp3", 1.2, 0.35]], "cheer": [["war_7.mp3", 0.1, 0.5], ["impact_2.mp3", 0.1, 0.3]], "cloak": [["war_7.mp3", 0.3, 0.3], ["cinematic_6.mp3", 0.3, 0.4]], "decide": [["heartbeat_2.mp3", 0.6, 0.35]], "decide_b": [["impact_3.mp3", 2.5, 0.25]],
       "arrive": [["wind_3.mp3", 0.0, 0.3], ["paper_1.mp3", 2.0, 0.35]], "read": [["heartbeat_2.mp3", 0.5, 0.4], ["impact_3.mp3", 2.0, 0.3]], "camp": [["fire_3.mp3", 0.0, 0.3], ["night_1.mp3", 0.0, 0.15]], "ranks": [["war_7.mp3", 0.0, 0.2], ["drum_2.mp3", 0.5, 0.4]], "spk": [["wind_4.mp3", 0.0, 0.15]],
       "envoy": [["war_5.mp3", 0.0, 0.12]], "march": [["war_7.mp3", 0.0, 0.3], ["drum_1.mp3", 0.3, 0.5], ["horse_3.mp3", 0.0, 0.2]], "ehorse": [["horse_3.mp3", 0.0, 0.4]], "walk": [["wind_3.mp3", 0.0, 0.2]], "cent": [["horse_0.mp3", 0.1, 0.35], ["heartbeat_2.mp3", 0.8, 0.45]],
       "strike": [["horse_1.mp3", 0.1, 0.5], ["swords_2.mp3", 1.0, 0.55], ["impact_1.mp3", 1.1, 0.6]], "dec": [["horse_1.mp3", 0.0, 0.3], ["impact_0.mp3", 2.6, 0.5]], "desert": [["wind_4.mp3", 0.0, 0.35]], "bag": [["horse_0.mp3", 0.0, 0.3]], "bury": [["impact_3.mp3", 0.3, 0.2]],
       "senate": [["war_0.mp3", 0.0, 0.05], ["cinematic_2.mp3", 0.0, 0.3]], "scroll": [["paper_1.mp3", 0.6, 0.4]], "diary": [["paper_2.mp3", 0.5, 0.3]], "c1v_chest": [["impact_3.mp3", 0.3, 0.3]], "c1v_emp_fire": [["impact_3.mp3", 3.5, 0.25]], "c1v_burn": [["fire_2.mp3", 0.0, 0.5]]}   # 11/10 대표: 효과음 더 풍부하게
TALK = {"spk", "spkw", "spk2", "spkw2", "ctalk", "bury", "c1v_emp_talk", "c1v_emp_talk_b", "c1v_gen_talk", "c1v_gen_talk_b", "c1v_emp_fire"}   # 입이 움직이는 클립: 소리와 입이 같이 시작·끝나도록 앞뒤 여백 최소
ENDS = ["욕하지 마라", "그의 끝을 구경하지 마라", "알 필요 없는 것은 열지 마라"]
INTRO_SFX = [["cinematic_6.mp3", 1.47, 1.0], ["war_7.mp3", 0.6, 0.18], ["ring_synth.wav", 2.4, 0.35], ["impact_2.mp3", 3.02, 1.0], ["impact_0.mp3", 3.02, 0.7], ["drum_5.mp3", 3.92, 1.0], ["drum_0.mp3", 3.92, 0.7],
             ["cinematic_4.mp3", 4.9, 0.8], ["impact_3.mp3", 6.2, 0.55], ["transition_5.mp3", 8.96, 0.5]]   # 11/10 대표: 원래 속도, 더 웅장하게


MV = [("cloak", 0.0, None), ("cheer", 0.5, None), ("ride", 0.0, None), ("city", 0.0, None), ("march", 0.5, None), ("casp", 0.0, None),
      ("ranks", 0.0, None), ("sback", 0.0, (["오늘 나는 무례하고", "은혜를 모르는 사람을 만날 것이다"], "명상록 2권 1절")), ("ppl2", 0.0, None), ("ppl3", 0.0, None),
      ("strike", 0.5, None), ("dec", 0.0, None), ("desert", 0.0, None), ("alone", 0.0, None), ("c1v_emp_fire", 0.0, (["가장 좋은 복수는", "그 사람과 같아지지 않는 것이다"], "명상록 6권 6절")),
      ("c1v_push", 0.0, None), ("c1v_burn", 0.0, None), ("c1v_seal", 0.0, None), ("diary", 0.0, (["우주는 변화이고", "삶은 생각이 만든다"], "명상록 4권 3절"))]


def spec():
    from cine01 import STILL
    d = "social/side/voice_samples/" + TAG; vf = {}
    for f in sorted(os.listdir(os.path.join(ROOT, d))):
        if f.endswith(".mp3"): vf[f[:-4].split("_")[-1]] = f
    q = lambda t: "\u201c" + t + "\u201d"; subs = {}; shots = []; mono = []; cast = []
    dur_of = lambda n: float(os.popen(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {os.path.join(ROOT, d, vf[n])}").read())
    d2 = "social/side/voice_samples/cep01b"
    for f in sorted(os.listdir(os.path.join(ROOT, d2))):
        if f.endswith(".mp3"):
            n = f[:-4].split("_", 3)[-1]; vf[n] = "../cep01b/" + f
    for dd in ("cep01c", "cep01d", "cep01e"):
        if os.path.isdir(os.path.join(ROOT, "social/side/voice_samples", dd)):
            for f in sorted(os.listdir(os.path.join(ROOT, "social/side/voice_samples", dd))):
                if f.endswith(".mp3"): vf[f[:-4].split("_", 3)[-1]] = f"../{dd}/" + f
    vf["l026"] = vf["cas_" + CAS_PICK]
    pos = {}
    def add(i, k, v, t, o, n):
        if k == "INTRO": shots.append({"type": "intro", "sfx": INTRO_SFX}); return
        if k == "RECAP":
            shots.append({"type": "recap", "center": True, "items": ENDS, "dur": 9.0, "fixed": True, "cascade": [1.3, 1.7], "nocap": True, "amb": ["wind_2.mp3", 0.16],
                          "head": "뒤통수 친 사람을 이기는 3가지 방법", "head_en": "THREE WAYS", "tin": "dissolve", "fin": 0.9,
                          "sfx": [["whoosh_2.mp3", 0.0, 0.3], ["impact_3.mp3", 1.3, 0.5], ["drum_5.mp3", 1.3, 0.35], ["impact_3.mp3", 3.0, 0.5], ["impact_2.mp3", 4.7, 0.6], ["drum_5.mp3", 4.7, 0.45]]}); return
        if k == "FINALE":   # 11/10 대표: 정리 뒤 1~2분 뮤직비디오처럼 (대사 없이 장면 + 웅장한 음악 + 명상록 구절)
            for j, (src, st, ov) in enumerate(MV):
                sh = {"type": "video", "src": src if src.startswith("c1v_") else clipid(src), "move": {"zoom": [1.0, 1.06] if j % 2 == 0 else [1.06, 1.0]}, "dur": 4.6, "start": st, "nocap": True, "tin": "dissolve", "fin": 0.6}
                if ov: sh["overlays"] = [{"kind": "verse", "lines": ov[0], "src": ov[1], "at": 0.6, "until": 4.4, "size": 64}]
                if j == len(MV) - 1: sh.update(tout="black", fout=1.4, dur=5.6)
                shots.append(sh)

            shots.append({"type": "finale", "dur": 13.0, "voice": ["o1", "q3"], "pre": 0.6, "gap": 0.6, "post": 1.4, "nocap": True, "tin": "black", "slogan": "매일 밤, 황제처럼 생각하라", "brand_ko": "황제의 일기  ·  명상록 실화극", "cta": "명상록 실화극  ·  다음 이야기에서 뵙겠습니다", "amb": ["wind_2.mp3", 0.12], "sfx": [["cinematic_6.mp3", 0.2, 0.5]]}); return
        base = k[:-2] if k.endswith("_b") or k.endswith("_c") else k.rstrip("2") if k in ("spk2", "spkw2", "diary2") else k
        o = dict(o); a = o.pop("amb", AMB.get(base, FIRE if k.startswith("c1v_") or base in ("glis", "elis", "stop") else COLD)); pre = o.pop("pre", 0.3); post = o.pop("post", 0.4)
        if o.get("grade") == "none": o["grade"] = "modern"
        if n:
            if k in TALK: pre, post = min(pre, 0.1), min(post, 0.15)
            elif dur_of(n) + pre + post > 5.04: pre, post = min(pre, 0.12), min(post, 0.15)   # 클립을 늘리지 않게
            subs[n] = ("!" + t[1:]) if t.startswith("!") else (t if v == N else q(t.lstrip("!")))
            if v == M: mono.append(n)
            elif v in (V, CAS): cast.append(n)
        sh = {"type": "video", "src": k if k.startswith("c1v_") else clipid(k), "move": dict(STILL), "pre": pre, "post": post, "start": o.pop("start", 0.0)}
        if a: sh["amb"] = list(a)
        if n: sh["voice"] = [n]
        sb = SFX.get(k) or SFX.get(base)
        if sb and "sfx" not in o: o["sfx"] = sb
        ident = VID2[k][1] if k in VID2 else k if k.startswith("c1v_") else img_key(k)
        pv = shots[-1] if shots else None   # 11/10 대표: 같은 그림을 두 번 다시 틀지 않는다 → 한 장면으로 이어 길게
        if n and pv and pv.get("_id") == ident and pv.get("voice") and k not in TALK and not o and sum(dur_of(x) for x in pv["voice"]) + dur_of(n) + 0.4 * len(pv["voice"]) <= 10.2:
            pv["voice"].append(n); pv["gap"] = 0.4; pv["post"] = post; return True
        sh["_id"] = ident
        sh.update(o)
        if not sh["src"].startswith("c1v_") and not os.path.exists(os.path.join(ROOT, "social/side/gen", sh["src"] + ".mp4")):   # 11/10 대표: 비용 절약 — 영상 없는 장면은 그림 + 카메라 이동 + 입자
            im = VID2[k][1][:-5] if k in VID2 else "cep1i_" + img_key(k); j = len(shots) % 4
            mv = [{"zoom": [1.0, 1.07]}, {"zoom": [1.08, 1.0]}, {"zoom": [1.06, 1.06], "pan": [[-0.03, 0], [0.03, 0]]}, {"zoom": [1.03, 1.09], "pan": [[0, 0.02], [0, -0.02]]}][j]
            sh.update(type="still", src=im, move=mv, flicker=a is not None and a[0].startswith("fire"), particles="snow" if a in (COLD,) or k in ("snow", "snow_b", "out") else "embers" if a and a[0].startswith("fire") else "dust"); sh.pop("start", None)
        shots.append(sh)
    for i, (k, v, t, o) in enumerate(L):
        pos[i] = len(shots)
        if add(i, REPL.get(i, k), v, t, o, f"l{i:03d}" if v else None): pos[i] = len(shots) - 1
        for k2, n2, o2 in INS.get(i, []): add(None, k2, N if n2 else None, NEWV.get(n2), o2, n2)
    def m(f, a, b, vol, start=0, fin=3, fout=3, tail=2.0, offset=0.5): return {"file": f, "at_shot": a, "offset": offset, "start": start, "until_shot": b, "vol": vol, "fin": fin, "fout": fout, "tail": tail}
    # 11/10 대표: 카시우스 등장을 첫 장면으로
    hook = [dict(shots[pos[25]], pre=0, post=0, dur=3.0, tin="black", fin=0.25), dict(shots[pos[26]], pre=0.05, post=0.2), dict(shots[pos[27]], pre=0, post=0, dur=2.6, tout="black", fout=0.5)]
    hook[0].pop("voice", None); hook[2].pop("voice", None)
    hook[0]["sfx"] = [["war_7.mp3", 0.0, 0.45], ["impact_2.mp3", 0.0, 0.55], ["drum_5.mp3", 0.1, 0.6]]; hook[2]["sfx"] = [["war_7.mp3", 0.0, 0.6], ["impact_0.mp3", 0.1, 0.5]]
    shots[0:0] = hook
    Z = lambda i: pos[i] + 3 if i in pos else len(shots)
    music = [m("dramatic_4.mp3", 0, 3, 0.34, fin=0.2, fout=0.8, tail=0.2, offset=0), m("cinematic_5.mp3", Z(0), Z(5), 0.2, fin=1, fout=1.2, offset=0), m("dramatic_4.mp3", Z(6), Z(7), 0.55, fin=0.6, fout=2.0, tail=0.3, offset=0.2)]
    for f, a, b, vol, kw in [("cinematic_0.mp3", 7, 23, 0.2, {}), ("dramatic_0.mp3", 23, 32, 0.22, {}), ("sad_0.mp3", 32, 39, 0.17, {"start": 20}), ("sad_3.mp3", 39, 52, 0.24, {"fin": 3, "fout": 4}), ("epic_0.mp3", 52, 57, 0.24, {}),
                             ("sad_1.mp3", 57, 62, 0.27, {"start": 12, "fin": 2, "tail": 0.6, "fout": 2.5}), ("sad_5.mp3", 64, 70, 0.19, {}), ("sad_3.mp3", 70, 84, 0.17, {"start": 60}), ("sad_1.mp3", 84, 92, 0.17, {}),
                             ("sad_0.mp3", 93, 98, 0.1, {"start": 60, "fin": 2, "fout": 1.5, "tail": 0.4}), ("cinematic_4.mp3", 98, 103, 0.22, {"start": 110}), ("epic_0.mp3", 103, 105, 0.42, {"start": 5, "fin": 1.5, "fout": 4, "tail": 0, "offset": 0})]:
        music.append(m(f, Z(a), Z(b), vol, **kw))
    # 11/10 대표: 같은 그림·영상을 두 번 이어 틀지 않는다 → 한 장면으로 길게 + 살짝 클로즈업
    base = lambda x: re.sub(r"^(cep1i?_|c1v_|c1_)", "", (x.get("src") or "")).replace("_b", "").rstrip("2") if x["type"] in ("video", "still") and not x.get("nocap") else None
    out, remap = [], {}
    for i, x in enumerate(shots):
        p = out[-1] if out else None
        if p and i > 3 and base(x) and base(x) == base(p) and x["type"] == p["type"] and not p.get("tout") and not x.get("tin"):
            if x.get("voice"): p["voice"] = (p.get("voice") or []) + x["voice"]; p["gap"] = 0.5; p["post"] = x.get("post", 0.4)
            else: p["post"] = p.get("post", 0.4) + x.get("dur", 3.0)
            p.pop("dur", None); p["move"] = {"zoom": [1.0, 1.1]}
            for k_ in ("sfx",):
                if x.get(k_) and not p.get(k_): p[k_] = x[k_]
            remap[i] = len(out) - 1; continue
        remap[i] = len(out); out.append(x)
    for mu in music: mu["at_shot"] = remap.get(mu["at_shot"], len(out)); mu["until_shot"] = remap.get(mu["until_shot"], len(out))
    shots = out
    ii = [k for k, x in enumerate(shots) if x["type"] == "intro"][0]   # 11/10 대표: 강한 후킹 뒤 로고로 너무 급하게 넘어감 → 어둠 속 한 박자
    shots[ii - 1].update(tout="black", fout=1.2); shots[ii - 1]["post"] = shots[ii - 1].get("post", 0.4) + 0.6
    shots.insert(ii, {"type": "black", "dur": 0.8, "amb": ["wind_2.mp3", 0.2], "sfx": [["impact_3.mp3", 0.0, 0.25]]})
    for mu in music:
        if mu["at_shot"] >= ii: mu["at_shot"] += 1
        if mu["until_shot"] >= ii: mu["until_shot"] += 1
    DRAMA = {"cep1_strike": [["swords_2.mp3", 0.9, 0.6], ["impact_1.mp3", 1.0, 0.85], ["cinematic_6.mp3", 1.0, 0.6], ["heartbeat_2.mp3", 1.6, 0.5]],   # 카시우스 최후
             "cep1_dec": [["impact_0.mp3", 0.4, 0.7], ["drum_5.mp3", 0.4, 0.6], ["heartbeat_3.mp3", 1.5, 0.45]],
             "cep1_desert": [["wind_4.mp3", 0.0, 0.45], ["heartbeat_1.mp3", 0.5, 0.35]],
             "cep1_read": [["impact_3.mp3", 0.6, 0.55], ["heartbeat_2.mp3", 0.6, 0.5], ["cinematic_2.mp3", 0.0, 0.3]],   # 황제가 배신을 알게 되는 순간
             "cep1_alone": [["wind_3.mp3", 0.0, 0.4], ["heartbeat_1.mp3", 0.4, 0.35]], "cep1_stop": [["impact_3.mp3", 0.3, 0.5]],
             "cep1_grave": [["wind_4.mp3", 0.0, 0.3], ["impact_3.mp3", 0.5, 0.35]], "cep1i_grave": [["wind_4.mp3", 0.0, 0.3], ["impact_3.mp3", 0.5, 0.35]]}
    for x in shots:
        if x.get("src") in DRAMA: x["sfx"] = DRAMA[x["src"]]
    for x in shots: x.pop("_id", None)
    S = {"id": "cine_ep01", "root": "../../..", "gen_dir": "social/side/gen", "sfx_dir": "social/side/ed_long/sfx", "music_dir": "social/side/ed_long/music", "out_dir": "_long",
         "intro": {"logo": "docs/emperor/profile_final.png", "ko": "황제의 일기  :  명상록 실화극"}, "cap_scale": 1.12, "monologue_fx": "highpass=f=70,aecho=0.9:0.35:35|70:0.06|0.03,", "voice_gain": {"mono": 3.8, "narr": 1.2, "cast": 1.0},
         "voice_dir": d, "voice_files": vf, "subs": subs, "monologue_voices": mono, "cast_voices": cast, "music": music, "shots": shots}
    json.dump(S, open(os.path.join(HERE, "spec_cine_ep01.json"), "w"), ensure_ascii=False, indent=1); print(len(shots), "장면", len(vf), "목소리")


if __name__ == "__main__":
    {"gen": gen, "genv": genv, "spec": spec, "gen2": gen2}[sys.argv[1]]()
