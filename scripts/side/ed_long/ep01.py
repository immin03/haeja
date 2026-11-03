"""황제의 밤 편지 EPISODE 1 · 배신당한 밤 — 대본·촬영표 (2026-11-03)
python3 ep01.py gen     → scripts/side/gen/EDL261103-ep01.json (그림·영상) + scripts/side/voices_req.json (녹음)
python3 ep01.py spec    → scripts/side/ed_long/spec_ep01.json (렌더 설정)
대본 규칙: '!' 로 시작하면 강조 자막(가운데 큰 금색), 해설=건석(존댓말), 독백=명일(1인칭 반말, 마지막 줄 = 명상록 구절)
구절은 조지 롱 영역본(1862) 기준 권·절.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
G = "tc_6731b2e0855f351b98d30c48"   # 건석 (해설)
M = "tc_62d66c2d1523be99355fda02"   # 명일 (황제)
TAG = "ep01"

STYLE = ("Cinematic oil-painting look, like a dark Renaissance chiaroscuro painting brought to life, deep warm shadows, a single warm candle or torch light source, "
         "muted bronze, umber and deep navy palette, fine film grain, painterly texture, horizontal 16:9 widescreen film frame, main subject in the middle band of the frame, "
         "nothing important in the top and bottom eighth of the frame. Absolutely no text, no letters, no numbers, no writing, no logos, no watermark anywhere.")
MOD = ("Same painterly cinematic oil-painting texture and fine film grain, but a cool desaturated blue-grey palette with only one small warm light, "
       "horizontal 16:9 widescreen film frame, main subject in the middle band of the frame, nothing important in the top and bottom eighth of the frame. "
       "Absolutely no text, no letters, no numbers, no readable screens, no watermark, no brands anywhere.")
MEMO = ("Cinematic oil-painting look like a warm golden memory, soft hazy sunlight, gentle bloom, warm amber and ochre palette, fine film grain, painterly texture, "
        "horizontal 16:9 widescreen film frame, main subject in the middle band of the frame. Absolutely no text, no letters, no numbers, no logos, no watermark anywhere.")
EMP = ("the Roman emperor Marcus Aurelius at about fifty-four, short curly grey-brown hair, short grey-flecked beard, lean weathered face, "
       "plain brown wool tunic under a deep crimson military cloak")
VT = ("Keep the painterly look and every detail identical to the first frame. One simple, slow, subtle motion only; the camera stays almost still with at most a very slow gentle push-in. "
      "No text, no morphing faces, no extra fingers or limbs, no sudden camera shake, no cuts.")

IMAGES = {
 "e2a_generals": ("Inside a large Roman command tent at night, three Roman generals in bronze armor and red cloaks standing around a wooden map table, one leaning forward and pointing angrily at the map, "
                  "another with arms crossed; at the far end " + EMP + " sits in shadow, seen from behind and slightly to the side so his face is not visible; oil lamps and a candle light the scene.", STYLE),
 "e2b_bed": ("A Korean man in his fifties lying awake in bed at night in a dark apartment bedroom, staring at the ceiling, a phone face down on the nightstand, faint city light through the curtains.", MOD),
 "e2c_kitchen": ("A Korean woman in her late fifties sitting alone at a kitchen table late at night, holding a cup of tea with both hands, looking down, deep in thought, a single pendant lamp above her.", MOD),
 "e3a_soldiers": ("Night in a Roman legionary winter camp on the Danube, hundreds of soldiers with torches gathered in the snow, " + EMP + " standing on a low wooden platform addressing them, "
                  "seen from behind at a distance so his face is not visible, his crimson cloak lit by torchlight, breath visible in the cold air.", STYLE),
 "e3b_sofa": ("A Korean man in his fifties sitting alone on a sofa in a dim living room at night, looking at his phone with a flat, slightly disappointed expression, the phone screen glow on his face, no readable screen.", MOD),
 "e3c_meeting": ("A modern office meeting room in the evening, a middle-aged Korean man standing by a blank whiteboard after speaking, while seated colleagues look at their laptops and away from him.", MOD),
 "e4a_alone": ("Deep night inside a Roman command tent, " + EMP + " sitting alone on the edge of a simple camp bed, elbows on his knees, head slightly lowered, seen from the side in deep shadow so his face is mostly hidden, "
               "a single candle on a stool beside him, the empty map table behind, perfect stillness.", STYLE),
 "e4b_stars": ("A lone figure in a deep crimson cloak, the Roman emperor seen from behind, standing at the open flap of a command tent looking up at a vast starry winter sky over the frozen Danube river, "
               "snow-covered tents fading into the distance, a faint glow of the tent behind him.", STYLE),
 "e4c_bench": ("An older Korean man in his sixties sitting alone on a wooden bench by a quiet river at dawn, holding a thermos cup with both hands, calm and peaceful, mist on the water, seen from the side.", MOD),
 "e4d_cafe": ("A Korean woman in her fifties reading a book alone by a café window in soft early morning light, a cup of coffee beside her, a calm and content expression.", MOD),
 "e5a_antoninus": ("A sunlit garden of a Roman villa, an elderly kind Roman emperor with a white beard in a simple white toga walking slowly side by side with a young man of about eighteen with short curly brown hair, "
                   "the older man's hand resting on the young man's shoulder, cypress trees and a fountain behind them, both seen in profile.", MEMO),
 "e5c_friends": ("Three Korean friends in their sixties sitting together at a small table in a warm street tent restaurant at night, laughing quietly, small dishes on the table, warm orange light, a cozy intimate moment.", MOD),
 "e5d_couple": ("An elderly Korean couple walking slowly side by side along a path in an autumn park, the wife holding her husband's arm, fallen yellow leaves, soft late afternoon light, seen from behind.", MOD),
 "e6a_box": ("Inside the Roman command tent by day, a small wooden box wrapped in dark cloth resting on the wooden table, a kneeling soldier with lowered head beside the table, "
             "the emperor in his crimson cloak standing with his back to the box, turned away, one hand slightly raised as if saying no, his face not visible, cold pale light through the tent.", STYLE),
 "e6c_car": ("A Korean man in his forties sitting in a parked car at night with both hands gripping the steering wheel, jaw clenched, rain streaks on the windshield, red tail lights blurred outside.", MOD),
 "e6d_hall": ("A Korean woman in her forties standing in an apartment hallway with her eyes closed and one hand on her chest, taking a slow calming breath, a closed door behind her, soft evening light.", MOD),
 "e7a_fire": ("Inside the Roman command tent at night, a bundle of folded parchment letters tied with string burning in a bronze brazier, bright orange flames and drifting embers, "
              "the dark silhouette of the emperor standing beyond the fire, watching.", STYLE),
 "e7b_dawn": ("Dawn over the Roman legionary camp on the Danube, golden light breaking through clouds, " + EMP + " standing on a small snowy hill seen from behind, "
              "his crimson cloak moving in the wind, long rows of legionaries with shields and standards assembled below him, breath visible, a hopeful solemn mood.", STYLE),
 "e7c_curtain": ("A Korean man in his fifties opening the curtains of an apartment window at sunrise, golden morning light flooding in over the Seoul skyline, seen from behind.", MOD),
 "e7d_breakfast": ("A Korean father in his sixties and his adult son in his thirties sitting at a kitchen table sharing a simple breakfast in warm morning light, the father smiling softly, a quiet warm moment.", MOD),
}
VIDEOS = {
 "ev_rider": ("lp11_rider", "The rider slowly approaches the tent while soldiers turn their heads to watch, the red sun sinking lower."),
 "ev_generals": ("e2a_generals", "The general leaning over the map slowly jabs his finger at the map while the others stay still, the lamp flames flickering."),
 "ev_stars": ("e4b_stars", "Gentle snow begins to fall and the stars twinkle softly while the emperor stands still and the camera slowly pushes in."),
 "ev_box": ("e6a_box", "The emperor stays turned away and slowly lowers his raised hand while the kneeling soldier bows his head lower."),
 "ev_fire": ("e7a_fire", "The flames rise and curl the burning letters while bright embers drift upward."),
 "ev_dawn": ("e7b_dawn", "The crimson cloak ripples in the wind and the golden dawn light slowly spreads across the assembled legion."),
 "ev_garden": ("e5a_antoninus", "The two men walk slowly forward side by side in the warm sunlight while leaves sway gently."),
}

# ---------- 대본 ----------
# 각 줄: (이름, 목소리, 문장). 문장 앞 '!' = 강조 자막
LINES = [
 # 2장
 ("d2a", G, "날이 밝기도 전에, 장군들이 막사로 모여들었습니다."),
 ("d2b", G, "한 장군은 카시우스의 가족을 모두 잡아들이자고 했습니다. 다른 장군은, 그와 편지를 주고받은 자들을 하나도 남김없이 찾아내자고 했습니다."),
 ("d2c", G, "황제는 한참 동안, 아무 말도 하지 않았습니다."),
 ("m2a", M, "그가 틀렸다. 그건 분명하다."),
 ("m2b", M, "그런데 그의 잘못 때문에, 그의 가족까지 벌을 받아야 하는가."),
 ("m2c", M, "남의 잘못은, 그것이 생긴 자리에 두어라."),
 ("d2d", G, "실제로 황제는 반란이 끝난 뒤에도, 카시우스의 가족을 벌하지 않았다고 전해집니다."),
 ("d2e", G, "남이 저지른 잘못을 내 마음속으로 끌고 들어와, 몇 번이고 다시 재판하지 않는 것. 스토아 철학자들이 매일 연습한 일입니다."),
 ("d2f", G, "몇 년 전, 나에게 모진 말을 했던 사람이 있습니다. 그 사람은 이미 잊었을지도 모릅니다. 그런데 그 말은, 오늘 밤에도 내 머릿속에서 다시 재생됩니다."),
 ("d2g", G, "!잘못은 그 사람이 했는데, 벌은 매일 밤 내가 받고 있습니다."),
 ("d2h", G, "오늘 밤에는, 그 일을 한 번만 내려놓아 보세요. 그것은, 그 사람의 몫입니다."),
 ("d2i", G, "다음 날, 황제는 병사들 앞에 섰습니다."),
 # 3장
 ("d3a", G, "병사들은 불안했습니다. 누가 진짜 황제인지, 누구 편에 서야 살아남는지, 모두가 눈치를 보고 있었습니다."),
 ("d3b", G, "장군들은 지금이야말로 강하게 보여야 할 때라고 했습니다. 반역자를 크게 꾸짖고, 병사들의 환호를 받아야 한다고."),
 ("d3c", G, "그러나 황제는 병사들 앞에서, 카시우스를 욕하지 않았습니다. 오히려 그를 용서할 수 있기를 바란다고 말했다고 전해집니다."),
 ("m3a", M, "그들이 나를 칭송한다고, 내가 더 나은 사람이 되는가."),
 ("m3b", M, "그들이 나를 비웃는다고, 내가 더 못한 사람이 되는가."),
 ("m3c", M, "칭찬받는다고, 더 나아지지도 더 나빠지지도 않는다."),
 ("d3d", G, "황제는 일기에 이렇게 덧붙였습니다. 에메랄드는 누가 칭찬해 주지 않아도, 에메랄드라고."),
 ("d3e", G, "내 가치를, 남의 반응에 맡기지 않는 것. 이것이 세 번째 문장입니다."),
 ("d3f", G, "단체방에 올린 사진에 아무도 반응하지 않을 때. 회의에서 내 의견만 그냥 지나갈 때. 우리는 하루에도 몇 번씩, 남의 반응으로 나를 잽니다."),
 ("d3g", G, "!박수를 받지 못했다고, 내가 한 일이 작아지지는 않습니다."),
 ("d3h", G, "오늘 밤에는, 아무도 알아주지 않은 오늘의 일 하나를 떠올려 보세요. 그 일은, 그것만으로 충분했습니다."),
 ("d3i", G, "그날 밤, 황제는 아무도 막사에 들이지 않았습니다."),
 # 4장
 ("d4a", G, "장군들이 모두 물러가고, 막사에는 촛불 하나만 남았습니다."),
 ("d4b", G, "제국을 다스리는 사람에게, 혼자 있는 시간은 거의 없었습니다. 이 밤이, 그에게 허락된 유일한 고요였습니다."),
 ("m4a", M, "사람들은 바닷가로, 산으로, 시골로 떠나고 싶어 한다."),
 ("m4b", M, "나도 그랬다. 그러나 이제는 안다."),
 ("m4c", M, "사람은 어디로 물러나도, 자기 마음속보다 고요한 곳을 찾지 못한다."),
 ("d4c", G, "학자들은 이 대목을, 마음속 요새라고 부릅니다. 바깥이 아무리 시끄러워도, 언제든 들어가 쉴 수 있는 곳입니다."),
 ("d4d", G, "황제가 이 일기를 쓴 곳은 화려한 궁전이 아니라, 대부분 전쟁터의 막사였습니다. 그는 그곳에서 매일 밤, 자기 마음으로 물러났습니다."),
 ("d4e", G, "아이들이 모두 떠난 집. 은퇴하고 처음 맞은 조용한 월요일. 우리는 혼자가 된 시간을, 외로움이라고만 부릅니다."),
 ("d4f", G, "!하지만 그 시간은, 내 마음으로 돌아갈 수 있는 유일한 시간이기도 합니다."),
 ("d4g", G, "오늘 밤에는, 휴대폰을 내려놓고 십 분만 혼자 앉아 보세요. 그곳이, 당신의 요새입니다."),
 ("d4h", G, "그리고 촛불 아래에서, 황제는 오래된 얼굴들을 떠올렸습니다."),
 # 5장
 ("d5a", G, "명상록의 첫 권은 조금 특별합니다. 철학이 아니라, 고마운 사람들의 이름으로 가득합니다."),
 ("d5b", G, "할아버지에게서 배운 것, 어머니에게서 배운 것, 스승에게서 배운 것. 황제는 한 사람씩, 그들이 준 것을 적어 내려갔습니다."),
 ("m5a", M, "양아버지에게서는, 온화함과, 한번 정한 일을 끝까지 지키는 법을 배웠다."),
 ("m5b", M, "루스티쿠스에게서는, 에픽테토스의 글을 처음 받아 읽었다."),
 ("m5c", M, "좋은 조부모와, 좋은 부모와, 좋은 스승과, 좋은 벗을 만난 것에 감사한다."),
 ("d5c", G, "가장 믿던 사람에게 배신당한 밤, 황제가 붙잡은 것은 원망이 아니라, 고마운 얼굴들이었습니다."),
 ("d5d", G, "고마운 일을 꾸준히 적는 사람들이, 더 잘 자고 더 행복하다고 느낀다는 연구들이 있습니다. 이천 년 전 황제는, 이미 그 일을 하고 있었습니다."),
 ("d5e", G, "연락처에 이름은 수백 개인데, 정작 힘든 밤에 전화할 사람은 몇 명뿐입니다."),
 ("d5f", G, "!그 몇 명이면, 충분합니다."),
 ("d5g", G, "오늘 밤에는, 나를 만든 세 사람의 이름을 적어 보세요. 그리고 그중 한 사람에게, 짧은 안부를 보내 보세요."),
 ("d5h", G, "그리고 몇 달 뒤, 황제의 막사에 상자 하나가 도착했습니다."),
 # 6장
 ("d6a", G, "반란은, 석 달 엿새 만에 끝났습니다. 카시우스를 죽인 것은, 그의 부하였던 백인대장이었습니다."),
 ("d6b", G, "그는 카시우스의 목을 상자에 담아, 황제에게 보냈습니다."),
 ("d6c", G, "황제는 그 상자를 열지 않았습니다. 보지 않겠다고 하고, 묻어 주라고 했습니다."),
 ("d6d", G, "그리고 용서할 기회를 빼앗겼다며, 오히려 슬퍼했다고 전해집니다."),
 ("m6a", M, "나는 그에게 화가 났었다. 그러나 그 화는, 그를 해치지 못했다."),
 ("m6b", M, "화는, 언제나 나를 먼저 해쳤다."),
 ("m6c", M, "화는, 화나게 한 일보다 우리를 더 아프게 한다."),
 ("d6e", G, "스토아 철학자 세네카는 분노를, 잠깐의 광기라고 불렀습니다. 황제는 화를 참은 것이 아니라, 화가 자기를 망치게 두지 않았습니다."),
 ("d6f", G, "운전 중에 끼어든 차. 끝까지 사과하지 않은 사람. 그 화는, 그 사람이 아니라 나의 저녁을 망칩니다."),
 ("d6g", G, "!끊어 낼 사람은 끊어도 됩니다. 다만, 미움까지 들고 갈 필요는 없습니다."),
 ("d6h", G, "오늘 밤에는, 화가 올라올 때 숨을 세 번만 쉬어 보세요. 그 세 번이, 오늘 저녁을 지켜 줍니다."),
 ("d6i", G, "그날 밤, 반란에 얽힌 편지들이 불 속으로 들어갔습니다."),
 # 7장
 ("d7a", G, "그 편지들에는, 카시우스와 몰래 뜻을 나눈 사람들의 이름이 적혀 있었습니다."),
 ("d7b", G, "편지들은 읽히지 않은 채, 모두 불태워졌습니다. 원망할 이름들도, 함께 재가 되었습니다."),
 ("m7a", M, "내가 얼마나 더 살지, 아무도 모른다."),
 ("m7b", M, "그렇다면 남은 날을, 미움에 쓸 수는 없다."),
 ("m7c", M, "하루하루를 마지막 날처럼 보내는 것. 거기에 성품의 완성이 있다."),
 ("d7c", G, "라틴어로 메멘토 모리, 죽음을 기억하라. 스토아 철학자들에게 죽음을 떠올리는 일은, 오늘을 아끼는 연습이었습니다."),
 ("d7d", G, "새벽이 밝자, 황제는 다시 군대 앞에 섰습니다. 그에게는 아직, 끝나지 않은 전쟁이 있었습니다."),
 ("d7e", G, "우리에게는 언젠가 하자고 미뤄 둔 말들이 있습니다. 고맙다는 말, 미안하다는 말, 보고 싶었다는 말."),
 ("d7f", G, "!오늘이 마지막이라면, 그 말을 내일로 미루지는 않을 겁니다."),
 ("d7g", G, "오늘 밤에는, 미뤄 둔 말 하나를 보내 보세요. 짧아도 괜찮습니다."),
 # 정리·아웃트로
 ("r1", G, "가장 믿던 사람에게 배신당한 밤, 황제가 일기에 남긴 일곱 문장을 다시 짚어 보겠습니다."),
 ("r2", G, "첫째, 남의 생각을 짐작하느라, 남은 날들을 쓰지 마라."),
 ("r3", G, "둘째, 남의 잘못은, 그것이 생긴 자리에 두어라."),
 ("r4", G, "셋째, 칭찬은 나를 더 낫게도, 더 못하게도 만들지 않는다."),
 ("r5", G, "넷째, 가장 고요한 곳은, 내 마음속이다."),
 ("r6", G, "다섯째, 좋은 사람 몇이면, 충분하다."),
 ("r7", G, "여섯째, 화는, 나를 먼저 해친다."),
 ("r8", G, "일곱째, 오늘을, 마지막 날처럼."),
 ("r9", G, "!사람을 줄인다는 것은, 사람을 미워한다는 뜻이 아닙니다. 내 마음에 들일 사람을, 고른다는 뜻입니다."),
 ("o1", G, "오늘 이야기가 마음에 닿으셨다면, 구독과 좋아요로 황제의 일기를 함께 이어 가 주세요."),
 ("o2", G, "다음 이야기에서는, 무례한 사람들 앞에서 황제가 매일 아침 스스로에게 했던 말을 들려드리겠습니다."),
 # 1장 보강 (에픽테토스)
 ("c1g", G, "이 생각은 노예 출신 철학자, 에픽테토스에게서 왔습니다. 그는 우리를 괴롭히는 것은 일 자체가 아니라, 그 일에 대한 우리의 생각이라고 가르쳤습니다."),
]
TXT = {n: t for n, v, t in LINES}; VOICE = {n: v for n, v, t in LINES}


def clean(t): return t.lstrip("!")


def gen():
    jobs = []
    for k, (p, st) in IMAGES.items():
        jobs.append({"id": k, "kind": "image", "endpoint": "xai/grok-imagine-image-2.0", "body": {"aspect_ratio": "16:9", "prompt": p + " " + st}})
    for k, (src, p) in VIDEOS.items():
        jobs.append({"id": k, "kind": "video", "endpoint": "alibaba/wan-3.0/image-to-video", "image": f"social/side/gen/{src}.jpeg", "body": {"duration": 5, "prompt": p + " " + VT}})
    json.dump(jobs, open(os.path.join(ROOT, "scripts/side/gen/EDL261103-ep01.json"), "w"), ensure_ascii=False, indent=1)
    V = [{"name": n, "id": v, "line": clean(t), "emotion": "tonedown", "tempo": 0.85 if v == M else 1.0} for n, v, t in LINES]
    json.dump({"requested": "2026-11-03T14:50", "note": "황제의 밤 편지 EPISODE 1 본편 녹음 (해설 건석, 황제 명일)", "tag": TAG, "keep": True, "lang": "kor",
               "model": "ssfm-v30", "emotion": "tonedown", "tempo": 1.0, "voices": V}, open(os.path.join(ROOT, "scripts/side/voices_req.json"), "w"), ensure_ascii=False, indent=1)
    print(len(jobs), "생성 작업,", len(V), "줄 녹음")


if __name__ == "__main__":
    if sys.argv[1] == "gen": gen()
    else:
        import ep01_spec; ep01_spec.build()
