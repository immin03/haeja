# 10/29 09:45 작업자: P0 미달 기획 4건(11/2~11/3)을 PLAN-FIRST 촬영표로 새로 씀. 개선 #1(제목)·#2(비·추위 동물+까치 덮개) 반영
import json
STYLE = "Style: handcrafted 3D miniature diorama photographed with a macro lens, tilt-shift, shallow depth of field, soft cinematic light, felt, clay, paper and wood textures with tiny hand-painted details, gentle film grain, warm nostalgic color grade, clay figurines with soft rounded faces and gentle, restrained, understated expressions (no tears, no crying, no exaggerated sad faces), not photorealistic. Vertical 9:16 frame, main subject in the middle of the frame, a calm uncluttered area in the top fifth of the frame. Absolutely no text, no letters, no numbers, no hangul, no logos, no labels, no brand names, no watermark anywhere."
KACHI = "The magpie is exactly the character in the magpie reference image: a small round chibi magpie with a glossy black head, cream-white face and belly, big shiny dark-brown eyes, short black beak, dark navy-blue wings, a red knotted neckerchief and a small brown leather satchel. It does NOT hold a microphone."
TAIL = "Keep the miniature clay diorama look and every character design identical to the first frame. One simple, small action only; subtle, slow, gentle motion; the camera stays almost still with at most a slow gentle push-in. No text, no morphing faces, no extra fingers or limbs, no sudden camera shake, no cuts. No tears, no crying."
MAG = "social/side/gen/c1_magpie.jpeg"
G = "social/side/gen/"
END = "\n\nIn Korea, the magpie is the bird that brings good news 🐦\n\n"

def build(pfx, bible, shots):
    out = []
    for s in shots:
        parts = [bible[k] for k in s["b"]]
        p = " ".join(parts) + " " + s["scene"] + (" " + KACHI if s["kachi"] else "") + " " + STYLE
        iid = f"{pfx}{s['n']}_{s['slug']}"
        out.append({"n": s["n"], "id": iid, "vid": f"{pfx}v{s['n']}_{s['slug']}", "img_prompt": p,
                    "refs": ([MAG] if s["kachi"] else []) + [G + f"{pfx}{r}.jpeg" for r in s.get("refs", [])],
                    "reuse": None, "action": s["action"], "dur": 5, "cap": s["cap"], "detail": s["detail"]})
    return out

P = []
# ---------------- A. 11/2 08:00 고양이·까치 소쿠리 지붕 (개선 #2) ----------------
B = {
 "cat": "MOTHER CAT: a small calico street cat with white, orange and black patches, a short tail with a black tip, green eyes.",
 "kittens": "KITTENS: exactly two tiny calico kittens, one mostly orange, one mostly white.",
 "place": "PLACE: the stone jangdokdae platform in the back yard of an old hanok: rows of round brown earthenware crocks (onggi) with lids on a low stone platform, a low grey stone wall behind, a persimmon tree beside the wall, one small dented brass bowl on the platform edge.",
 "basket": "BASKET: a round shallow woven bamboo sieve-basket (sokuri), pale straw colour, about four times as wide as the magpie.",
 "size": "The magpie is tiny: about the size of the mother cat's head.",
}
A_shots = [
 {"n":1,"slug":"bowl","b":["cat","place","size"],"kachi":True,
  "scene":"Warm late-summer afternoon light. The mother cat and the magpie eat side by side from the one small dented brass bowl on the stone platform edge, peacefully, the magpie pecking at a crumb on the rim. Only one cat and only one magpie in the scene, no kittens.",
  "action":"The magpie pecks once at the bowl's rim while the cat slowly licks her lips; leaves sway softly.",
  "cap":"They always shared one bowl.","detail":"찌그러진 놋그릇 하나(둘이 나눠 먹는 사이)"},
 {"n":2,"slug":"rain","b":["cat","kittens","place","size"],"kachi":True,
  "scene":"A cold late-autumn evening, heavy cold rain, blue-grey light. In the open gap between two crocks at the front of the stone platform, the soaked mother cat curls around her two tiny kittens, fur wet and flat, with no roof over them; the empty dented brass bowl collects rain. On top of the stone wall behind, exactly one magpie sits hunched in the rain, looking down at them. The persimmon tree is bare.",
  "action":"Rain falls steadily; the mother cat pulls the kittens a little closer; the magpie on the wall slowly tilts its head.",
  "cap":"Then the cold rain came.","detail":"빗물 고인 빈 놋그릇(1컷과 대비)"},
 {"n":3,"slug":"basket","b":["cat","kittens","place","basket","size"],"kachi":True,"refs":["2_rain"],
  "scene":"The same cold rainy evening at the same spot. The round woven bamboo sieve-basket now leans like a small roof over the gap between the two crocks, already covering the mother cat and her two kittens, who peek out dry from underneath. Exactly one magpie, soaked, stands on the stone platform at the basket's front rim, holding the rim in its beak as if it has just pulled it into place. A faint wet drag trail on the stone platform leads from the far side of the platform to the basket.",
  "action":"The magpie gives one small final tug on the basket rim with its beak, then lets go and shakes the rain from its head.",
  "cap":"Kachi didn't fly home that night.","detail":"바닥에 남은 소쿠리 끌린 자국(까치가 끌어 왔다)"},
 {"n":4,"slug":"spring","b":["cat","place","basket","size"],"kachi":True,"refs":["1_bowl"],
  "scene":"Bright spring morning, white persimmon blossoms and fresh green leaves. High in the persimmon tree is a magpie's twig nest. Below the tree on the stone platform, the round woven bamboo sieve-basket lies upside down as a little roof, and the mother cat and two half-grown calico cats (one mostly orange, one mostly white) sit in a calm row in front of it, all three looking up at the nest like guards. Exactly one adult magpie with a red neckerchief stands on the rim of the nest, two tiny fluffy grey chicks without neckerchiefs peek out of the nest. The dented brass bowl sits in front of the cats with a few crumbs.",
  "action":"The adult magpie on the nest rim dips its head down toward the cats; the three cats slowly blink up at it.",
  "cap":"Now they guard her nest.","detail":"같은 소쿠리가 고양이 집이 됨 + 지켜보는 둥지(보은)"},
]
A_bible = dict(B); A_bible["palette"] = "cut 1 = warm late-summer afternoon; cuts 2-3 = cold late-autumn rain, blue-grey evening; cut 4 = bright spring morning with persimmon blossoms"
P.append({
 "id":"P261102-cat-basket","old":"P261031-rain-umbrella","publish_at":"2026-11-02T08:00:00+09:00","line":"emo",
 "title":"She shared her bowl… then came the rain 🐱☔",
 "title_ko":"여름 내내 한옥 장독대에서 길고양이와 까치는 찌그러진 놋그릇 하나를 나눠 먹었다. 차가운 늦가을 비, 갓 낳은 새끼 둘을 품고 지붕 없이 젖는 고양이. 까치가 대나무 소쿠리를 끌어와 지붕을 만들어 주고 자기는 밤새 비를 맞는다. 봄, 감나무 위 까치 둥지에 새끼가 깨고, 소쿠리 집 앞의 고양이 셋이 나란히 둥지를 지킨다.",
 "hook":"첫 컷: 고양이와 까치가 한 그릇을? — 왜 같이 먹는 사이인지가 비 오는 밤 까치가 돕는 이유",
 "emotion":"animal","korea":"한옥 장독대·대나무 소쿠리·감나무",
 "outline":[{"scene":"늦여름, 장독대 끝 찌그러진 놋그릇 하나를 고양이와 까치가 나눠 먹는다","action":"까치가 그릇 가장자리를 쪼고 고양이가 입맛을 다신다","cap":"They always shared one bowl."},
            {"scene":"늦가을 찬비, 항아리 사이 틈에서 고양이가 새끼 둘을 품고 젖는다. 담 위의 까치가 내려다본다","action":"고양이가 새끼를 끌어안고 까치가 고개를 갸웃","cap":"Then the cold rain came."},
            {"scene":"까치가 소쿠리를 끌어와 지붕처럼 기대 놓았다. 젖은 까치가 마지막으로 테두리를 당긴다","action":"마지막 한 번 당기고 머리를 턴다","cap":"Kachi didn't fly home that night."},
            {"scene":"봄, 감나무 위 까치 둥지에 새끼 둘. 소쿠리 집 앞의 고양이 셋이 나란히 둥지를 올려다본다","action":"까치가 고개를 숙이고 고양이들이 천천히 눈을 깜빡인다","cap":"Now they guard her nest."}],
 "bible":A_bible,"shots":build("cb",A_bible,A_shots),
 "details":[{"prop":"찌그러진 놋그릇 하나","where":[1,2,4],"meaning":"둘이 나눠 먹던 사이 → 빗물 고인 빈 그릇 → 다시 함께"},
            {"prop":"대나무 소쿠리(끌린 자국)","where":[3,4],"meaning":"까치가 직접 끌어온 지붕이 봄엔 고양이 가족의 집"},
            {"prop":"감나무(빈 가지 → 꽃·둥지)","where":[2,4],"meaning":"계절이 지나 은혜가 돌아옴"}],
 "format":"animal-shelter-kachi (개선 #2: 비·추위 작은 동물 + 까치 덮개 → 보은)","hook_type":"odd-friendship-first-frame","music":"music_i-believe-2",
 "pinned":"Have you ever seen a cat and a bird be friends? 🐱🐦 Tell Kachi 💛",
 "description":"All summer, a street cat and a magpie shared one little bowl in a Korean hanok yard.\nThen the cold rain came… and the magpie didn't fly home."+END+"#Cat #Magpie #Kindness #Korea #AnimalFriends #shorts",
 "tags":["cat","magpie","kittens","animal friendship","kindness","rain","hanok","Korea","miniature animation","Kachi","From Korea With Love"],
 "notes":"컷마다 동물 수를 못박음(어미 1·새끼 2·까치 1, 4컷 새끼 까치 2는 목수건 없음). 까치 크기 = 어미 고양이 머리만큼. 소쿠리를 끄는 큰 동작 대신 '이미 거의 덮은 소쿠리를 마지막 한 번 당김' + 바닥 끌린 자국으로 원인을 보여 줌. 4컷 새끼 고양이는 반쯤 자란 고양이(봄, 몇 달 뒤 — 고양이 성장 개월 수와 맞음). 장독 뚜껑·소쿠리에 글자 없음.",
 "p0":{"surprise":4,"emotion":4,"natural":4,"kachi":5},
 "why":"개선 #2(비·추위 속 작은 동물 + 까치가 지붕을 물어다 줌, 마지막 컷 보은) 첫 적용. 원래 노란 우산 기획은 11/1 우산 누렁이 편과 소품·전제가 겹치고 '이유·반전'이 없어(P0 미달) 교체. 동물 가족 유형(이번 달 상위 20편 하루 333만 회)",
})
# ---------------- B. 11/2 22:00 아빠의 빨간 내복 ----------------
B = {
 "dad_then":"DAD (years ago): a thin Korean father in his early forties, short black hair, kind tired face, an old faded pink-red long-john top with two square cloth patches on the elbows.",
 "girl":"GIRL (years ago): his daughter about seven years old, round face, black hair in one low ponytail, yellow pajamas.",
 "dad_now":"DAD (now): the same father in his early sixties, short grey hair, the same kind face with deeper lines, a brown knitted cardigan.",
 "woman":"DAUGHTER (now): the same girl grown into a woman of twenty-five, round face, black hair in one low ponytail, a camel wool coat, a small grey suitcase.",
 "place":"PLACE: a small old countryside house: a warm-floored room with a yellow oiled-paper floor (ondol), a low wooden table, a sliding paper door (hanji) with a wooden lattice; outside, a little yard with a low stone wall and a blue metal gate.",
 "drawing":"DRAWING: a child's crayon drawing on a small sheet of paper: a smiling stick-figure dad in a bright red long-john suit with a big red heart beside him, no writing at all.",
 "parcel":"PARCEL: a small box wrapped in plain brown kraft paper tied with red string in a bow, about twice the size of the magpie.",
 "size":"The magpie is tiny: about the size of the father's hand.",
}
B_shots = [
 {"n":1,"slug":"patch","b":["dad_then","girl","place","drawing"],"kachi":False,
  "scene":"Years ago, a winter night, a dim yellow lamp. The father sits on the floor by the low table holding up the elbow of his faded patched long-john sleeve to the lamp, looking at a new hole with a small tired smile. Behind him, the sliding paper door is open a crack and the little girl peeks in, holding the crayon drawing against her chest with both arms. Slightly faded colours like an old memory. Hands simple and mostly hidden in the fabric.",
  "action":"The father slowly lowers the worn sleeve with a small tired smile; the girl behind the door hugs her drawing a little tighter.",
  "cap":"Dad always said they were fine.","detail":"팔꿈치에 덧댄 헝겊 두 장(낡은 내복) + 아이가 품은 그림"},
 {"n":2,"slug":"parcel","b":["dad_now","place","parcel","size"],"kachi":True,
  "scene":"Now, a snowy winter morning. The father stands at the open blue metal gate. Exactly one magpie stands on top of the gate post, the small kraft-paper parcel tied with red string set down in front of its feet on the snowy post. The father looks at the magpie and the parcel in surprise. No signs, no mailbox letters.",
  "action":"The magpie nudges the parcel one small step toward the father with its beak; snowflakes drift down.",
  "cap":"Her first paycheck came in a box.","detail":"빨간 끈 소포(까치가 배달)"},
 {"n":3,"slug":"open","b":["dad_now","place","drawing","size"],"kachi":True,"refs":["1_patch","2_parcel"],
  "scene":"Inside the warm room, the father kneels by the low table over the opened kraft-paper box: inside lies a neatly folded brand-new bright red long-john set, and on top of it the old yellowed crayon drawing from years ago, its paper soft and creased. Exactly one magpie stands on the edge of the low table, watching. The old faded patched long johns hang folded on a wall hook in the background. Hands simple and mostly hidden.",
  "action":"The father slowly lifts the old crayon drawing a little toward the light and presses his lips together in a quiet smile.",
  "cap":"She kept it all these years.","detail":"새 빨간 내복 위 옛 크레용 그림 + 벽에 걸린 덧댄 낡은 내복"},
 {"n":4,"slug":"home","b":["dad_now","woman","place"],"kachi":False,"refs":["3_open"],
  "scene":"Late afternoon, snowy yard, the blue metal gate open. The father stands on the house step; the bright red cuff of his new long johns shows under his brown cardigan sleeve. Coming through the gate with her small grey suitcase is his daughter, now grown, smiling. They are a few steps apart. The old crayon drawing is pinned on the house wall beside the door. Warm golden light.",
  "action":"The father slowly nods and smiles as the daughter takes one step closer; snow falls gently.",
  "cap":"Then she came home for the winter.","detail":"카디건 소매 밖 새 빨간 내복 + 문 옆에 붙은 크레용 그림"},
]
B_bible = dict(B); B_bible["palette"]="cut 1 = years ago, dim yellow lamp, slightly faded; cuts 2-4 = now, bright snowy winter, warm golden indoor light"
P.append({
 "id":"P261102-dad-longjohns","old":"P261031-first-paycheck","publish_at":"2026-11-02T22:00:00+09:00","line":"emo",
 "title":"Dad's long johns were patched… then 🎁",
 "title_ko":"오래전 겨울밤, 아빠는 덧댄 낡은 빨간 내복을 등불에 비춰 보고, 일곱 살 딸은 문틈에서 '새 빨간 내복 입은 아빠' 크레용 그림을 품고 있다. 세월이 흘러 딸의 첫 월급날, 까치가 빨간 끈 소포를 대문에 배달한다. 상자 안엔 새 빨간 내복과 그때 그 크레용 그림. 해 질 녘 새 내복 소매를 내보인 아빠 앞으로 딸이 겨울 휴가를 맞아 대문을 들어선다.",
 "hook":"첫 컷: 아빠는 왜 구멍 난 내복을 계속 기워 입을까, 문틈의 아이는 무슨 그림을 안고 있을까",
 "emotion":"mom","korea":"첫 월급 빨간 내복 풍습·시골집 온돌방·파란 대문",
 "outline":[{"scene":"오래전 겨울밤, 아빠가 덧댄 내복 팔꿈치 구멍을 등불에 비춰 본다. 문틈의 딸이 크레용 그림을 품고 있다","action":"아빠가 소매를 내리며 지친 미소","cap":"Dad always said they were fine."},
            {"scene":"지금 눈 오는 아침, 까치가 대문 기둥에 빨간 끈 소포를 내려놓았다","action":"까치가 소포를 부리로 아빠 쪽으로 민다","cap":"Her first paycheck came in a box."},
            {"scene":"상자 안 새 빨간 내복 위에 그때 그 크레용 그림. 벽엔 덧댄 낡은 내복","action":"아빠가 그림을 빛에 비추며 입술을 다문 미소","cap":"She kept it all these years."},
            {"scene":"해 질 녘 마당, 새 내복 소매가 보이는 아빠 앞으로 다 큰 딸이 가방을 끌고 들어선다","action":"아빠가 천천히 고개를 끄덕이며 미소","cap":"Then she came home for the winter."}],
 "bible":B_bible,"shots":build("dl",B_bible,B_shots),
 "details":[{"prop":"팔꿈치 헝겊 두 장 덧댄 낡은 내복","where":[1,3],"meaning":"아빠는 자기 것은 늘 기워 입었다"},
            {"prop":"크레용 그림(빨간 내복 입은 아빠 + 하트)","where":[1,3,4],"meaning":"일곱 살 딸의 소원이 첫 월급으로 이뤄짐"},
            {"prop":"카디건 소매 밖 새 빨간 내복","where":[4],"meaning":"말없이 바로 입었다"}],
 "format":"parent-sacrifice-repaid + Kachi delivery","hook_type":"quiet-sacrifice-question","music":"music_miss-you",
 "pinned":"What did YOU buy with your first paycheck? 💛 Tell Kachi",
 "description":"Dad always patched his old red long johns.\nIn Korea, many people spend their first paycheck on red long johns for their parents — a warm thank-you."+END+"#FirstPaycheck #Dad #Korea #KoreanCulture #Family #shorts",
 "tags":["first paycheck","dad","red long johns","Korean tradition","family","Korea","magpie","miniature animation","Kachi","From Korea With Love"],
 "notes":"세월 18년(딸 7→25, 아빠 40대 초→60대 초) 맞춤. 소포가 대문에 온 이유 = 까치 배달(까치는 소포 배달 캐릭터). 인물 한 컷 최대 2명, 3컷 아빠+까치. 크레용 그림은 글자 없이 막대 인물·하트만. 4컷 아빠 얼굴은 3컷 ref. 눈물 금지 — 입술 다문 미소·끄덕임.",
 "p0":{"surprise":4,"emotion":5,"natural":4,"kachi":4},
 "why":"원안(딸이 시장에서 내복 사서 드림)은 반전·까치 역할이 없어 P0 미달 → 어린 딸의 그림을 첫 컷에 심고 마지막에 회수, 까치가 소포 배달. 부모 희생→갚기 구조(79만~290만 회)",
})
# ---------------- C. 11/3 08:00 시장 할머니 군고구마 ----------------
B = {
 "grandma_then":"GRANDMA (years ago): a Korean market grandma in her late sixties, black-grey permed short hair, round kind face, a red-and-navy floral padded vest, dark sleeve covers on her arms.",
 "boy":"BOY (years ago): a thin Korean schoolboy about fourteen, short black hair, round glasses, navy school uniform jacket, an open dark-green backpack.",
 "grandma_now":"GRANDMA (now): the same grandma in her mid-eighties, snow-white permed short hair, the same round kind face with deeper smile wrinkles, the same red-and-navy floral padded vest, a little more bent.",
 "man":"MAN (now): the same boy grown into a man about thirty-five, short black hair, the same round glasses, a navy wool coat over a grey suit, a grey scarf.",
 "place":"PLACE: one small street stall at the corner of an old Korean traditional market alley: a low wooden platform with flat round bamboo baskets of napa cabbages, green onions and radishes, a little round black charcoal drum with roasted sweet potatoes on top, a striped canvas awning on a thin metal pole, one warm bare bulb. No signs, no price tags, no posters, no writing anywhere.",
 "potato":"SWEET POTATO: a roasted sweet potato with purple-brown skin, wrapped halfway in plain brown paper.",
 "size":"The magpie is tiny: about the size of a roasted sweet potato.",
}
C_shots = [
 {"n":1,"slug":"gift","b":["grandma_then","boy","place","potato","size"],"kachi":True,
  "scene":"Years ago, a winter dusk, slightly faded colours like an old memory. The thin schoolboy stands in front of the stall; the grandma leans over and drops a warm roasted sweet potato wrapped in plain brown paper into his open backpack, steam rising. Exactly one magpie perches on the awning pole above, watching. Hands simple and mostly hidden.",
  "action":"Steam curls up from the sweet potato in the backpack; the boy gives a small shy bow; the magpie tilts its head.",
  "cap":"She never let him walk home hungry.","detail":"종이에 반쯤 싼 군고구마(나중에 회수)"},
 {"n":2,"slug":"unsold","b":["grandma_now","place","size"],"kachi":True,
  "scene":"Now, a snowy winter night, the market alley empty and dark beyond the stall. The baskets are still piled high with unsold cabbages and green onions, a little snow on them. The old grandma sits small on a low stool under the single warm bulb, shoulders hunched, hands tucked into her sleeves. The charcoal drum is cold and empty. Exactly one magpie on the awning pole looks down the empty alley.",
  "action":"The grandma slowly rubs her tucked arms against the cold; snow falls; the magpie turns its head toward the alley.",
  "cap":"Now nobody stopped for her.","detail":"차갑게 식은 빈 군고구마 통(1컷과 대비) + 쌓인 채소"},
 {"n":3,"slug":"lead","b":["man","size"],"kachi":True,"refs":["1_gift"],
  "scene":"The snowy entrance of the same old market alley at night, warm shop lights far behind, no signs, no writing. The man in the navy coat with round glasses, holding a paper bag against his chest, has stopped walking and looks up. Exactly one magpie flutters just in front of his face at eye level, wings open, as if calling him into the alley.",
  "action":"The magpie hovers with slow wing beats and drifts a little toward the alley; the man turns his head to follow it.",
  "cap":"But Kachi remembered someone.","detail":"남자가 품에 안은 종이봉투(속에 군고구마)"},
 {"n":4,"slug":"return","b":["grandma_now","man","place","potato","size"],"kachi":True,"refs":["2_unsold","3_lead"],
  "scene":"At the stall under the warm bulb. The man crouches in front of the old grandma so their eyes are level; on the stall between them he has set down a warm roasted sweet potato wrapped halfway in plain brown paper, steam rising. Beside him on the ground stand several full plain paper bags of her cabbages and green onions; the baskets behind are now empty. The grandma looks at his round glasses with quiet recognition and a soft smile. Exactly one magpie sits on the empty basket rim. Hands simple and mostly hidden.",
  "action":"Steam rises from the sweet potato; the grandma slowly breaks into a soft smile and nods; the magpie fluffs its feathers.",
  "cap":"This time, he brought the sweet potato.","detail":"같은 군고구마(회수) + 비어 버린 채소 바구니"},
]
C_bible = dict(B); C_bible["palette"]="cut 1 = years ago, winter dusk, slightly faded warm; cuts 2-4 = now, snowy blue night, one warm bulb"
P.append({
 "id":"P261103-market-sweetpotato","old":"P261031-market-greens","publish_at":"2026-11-03T08:00:00+09:00","line":"emo",
 "title":"She fed a hungry boy… then winter came 🍠",
 "title_ko":"오래전 겨울, 시장 모퉁이 할머니는 배고픈 중학생 가방에 늘 군고구마 하나를 넣어 줬다. 지켜보던 까치. 지금, 눈 오는 밤 채소가 하나도 안 팔린 채 식은 화로 옆에 웅크린 할머니. 까치가 시장 입구에서 퇴근하던 둥근 안경의 남자 앞을 날며 골목으로 이끈다. 그가 채소를 모두 사 담고, 이번엔 자기가 군고구마를 할머니 앞에 놓는다.",
 "hook":"첫 컷: 할머니는 왜 그 아이 가방에만 고구마를 넣어 줄까 — 둥근 안경이 마지막에 얼굴을 알아보는 열쇠",
 "emotion":"grand","korea":"전통시장 좌판·군고구마 드럼통",
 "outline":[{"scene":"오래전 겨울 저녁, 할머니가 마른 중학생 가방에 군고구마를 넣어 준다. 차양 막대 위 까치","action":"김이 오르고 소년이 꾸벅","cap":"She never let him walk home hungry."},
            {"scene":"지금 눈 오는 밤, 안 팔린 채소 더미와 식은 화로, 웅크린 할머니. 까치가 빈 골목을 본다","action":"할머니가 팔을 비비고 까치가 고개를 돌린다","cap":"Now nobody stopped for her."},
            {"scene":"시장 입구, 둥근 안경의 남자 눈앞에서 까치가 날갯짓하며 골목으로 부른다","action":"까치가 골목 쪽으로 날고 남자가 고개를 돌린다","cap":"But Kachi remembered someone."},
            {"scene":"좌판 앞에 쪼그려 앉은 남자, 채소는 모두 봉지에, 할머니 앞엔 김 나는 군고구마. 할머니가 안경을 보고 알아본다","action":"할머니가 천천히 미소 짓고 끄덕인다","cap":"This time, he brought the sweet potato."}],
 "bible":C_bible,"shots":build("mk",C_bible,C_shots),
 "details":[{"prop":"종이에 반쯤 싼 군고구마","where":[1,4],"meaning":"그때 받은 것을 그대로 돌려줌"},
            {"prop":"둥근 안경","where":[1,3,4],"meaning":"20년이 지나도 같은 소년임을 알아보는 표시"},
            {"prop":"식은 화로·쌓인 채소 → 빈 바구니","where":[2,4],"meaning":"외로운 밤이 끝남"}],
 "format":"kindness-returns + Kachi connects","hook_type":"why-question-first-frame","music":"music_we-ll-be-okay",
 "pinned":"Is there someone you still want to thank? 🍠 Tell Kachi 💛",
 "description":"Years ago, a market grandma never let a hungry schoolboy walk home with an empty stomach.\nOne snowy night, nobody stopped at her stall… but a magpie remembered."+END+"#Kindness #Grandma #Korea #KoreanMarket #Wholesome #shorts",
 "tags":["kindness","grandma","Korean market","sweet potato","street vendor","Korea","magpie","miniature animation","Kachi","From Korea With Love"],
 "notes":"세월 약 21년(14→35, 할머니 60대 후반→80대 중반). 까치가 남자를 아는 이유 = 1컷에 그 자리에 있었음(까치가 사는 시장 모퉁이). 시장 간판·가격표·봉지 글자 금지(정류장·가게 체크리스트). 한 컷 최대 2명. 4컷 남자 얼굴은 3컷 ref, 할머니는 2컷 ref. 손은 소매·봉지에 숨김.",
 "p0":{"surprise":4,"emotion":5,"natural":4,"kachi":4},
 "why":"원안(모르는 회사원이 채소를 다 삼)은 '갑자기 착한 낯선 사람' 금지 기준(P0) 미달 → 첫 컷에 할머니의 오랜 친절을 심고, 까치가 그를 이끌어 오고, 같은 군고구마로 회수. 노인을 돕는 친절 구조(하루 4만~13만 회)",
})
# ---------------- D. 11/3 22:00 군대 간 오빠를 기다린 진돗개 ----------------
B = {
 "puppy":"PUPPY: a small white Korean Jindo puppy with pointed ears, a curled fluffy tail and a little red cotton bandana tied around its neck.",
 "dog":"DOG: the same white Korean Jindo now grown into a medium-sized adult dog, pointed upright ears, curled tail, the same little red cotton bandana now slightly faded.",
 "young":"YOUNG MAN: a Korean young man about twenty, very short buzz-cut black hair, round friendly face; in cut 1 a grey hoodie with a navy duffel bag; in cut 4 a plain olive-green military uniform and cap with no badges, no name tags, no patches, no writing.",
 "place":"PLACE: a tiny countryside bus stop: a small wooden shelter with a tiled roof and a wooden bench, a narrow road curving away between rice fields toward low mountains, a single tall persimmon tree beside the shelter. No signs, no timetable, no posters, no writing anywhere.",
 "size":"The magpie is tiny: about the size of the dog's head.",
}
D_shots = [
 {"n":1,"slug":"leave","b":["puppy","young","place"],"kachi":False,
  "scene":"Early spring morning, soft pale light, rice fields flooded and green. The young man in a grey hoodie with his navy duffel bag kneels at the bus stop, forehead gently touching the forehead of the little white Jindo puppy with the red bandana. Only one person and one puppy. Hands simple and hidden in the puppy's fur.",
  "action":"The puppy slowly licks the young man's chin once; his buzz-cut head stays bowed against it.",
  "cap":"He left for the army.","detail":"강아지 목의 빨간 반다나(오빠가 묶어 줌)"},
 {"n":2,"slug":"wait","b":["dog","place","size"],"kachi":True,
  "scene":"Late autumn sunset, golden harvested rice fields, the persimmon tree heavy with orange fruit. The grown white Jindo with the faded red bandana sits alone in front of the bus stop bench, facing the empty curving road. Exactly one magpie sits on the tiled roof of the shelter above him.",
  "action":"The dog's ears twitch toward the empty road; a persimmon leaf drifts down past him.",
  "cap":"Every evening, he waited.","detail":"바랜 빨간 반다나 + 자란 몸(시간 경과)"},
 {"n":3,"slug":"song","b":["dog","place","size"],"kachi":True,"reuse":"lastframe:2",
  "scene":"(starts from the last frame of cut 2) The same sunset at the bus stop.",
  "action":"The magpie on the roof lifts its head and sings toward the far end of the road, beak opening; below, the dog's ears snap upright and its curled tail starts to wag slowly.",
  "cap":"A magpie's song means someone's coming.","detail":"까치 울음 = 반가운 손님(한국 속설)"},
 {"n":4,"slug":"home","b":["dog","young","place","size"],"kachi":True,"refs":["1_leave","2_wait"],
  "scene":"Dusk at the same bus stop, the warm glow of a departing bus's tail lights far down the road. The young man in a plain olive-green military uniform kneels with his duffel bag beside him; the grown white Jindo with the faded red bandana presses its head into his chest, tail curled high. Exactly one magpie sits on the bench end beside them. Hands simple and hidden in the dog's fur.",
  "action":"The dog's curled tail wags slowly; the young man closes his eyes with a quiet smile; the magpie hops once on the bench.",
  "cap":"He came home.","detail":"강아지 → 다 자란 개 + 같은 반다나"},
]
D_bible = dict(B); D_bible["palette"]="cut 1 = early spring morning, pale green; cuts 2-3 = late autumn golden sunset; cut 4 = dusk, warm glow"
dshots = build("jd",D_bible,D_shots)
dshots[2]["reuse"]="lastframe:2"; dshots[2]["img_prompt"]=None
P.append({
 "id":"P261103-jindo-army","old":"P261101-jindo-bus","publish_at":"2026-11-03T22:00:00+09:00","line":"emo",
 "title":"He left for the army… his puppy waited 🐕",
 "title_ko":"봄, 군대 가는 오빠가 시골 정류장에서 빨간 반다나를 묶어 준 진돗개 강아지와 이마를 맞댄다. 가을, 다 자란 진돗개는 매일 해 질 녘 정류장에서 빈 길을 본다. 지붕 위 까치가 길 끝을 보며 운다(한국에선 까치가 울면 반가운 손님이 온다). 개의 귀가 서고 — 군복 입은 오빠가 돌아와 무릎을 꿇는다.",
 "hook":"첫 컷: 왜 정류장에서 강아지와 이별할까 — 빨간 반다나와 강아지 크기가 시간의 흐름과 같은 개임을 보여 줌",
 "emotion":"animal","korea":"군 입대·시골 버스 정류장·진돗개·까치 울음 속설",
 "outline":[{"scene":"봄 아침 시골 정류장, 입대하는 청년이 빨간 반다나 강아지와 이마를 맞댄다","action":"강아지가 턱을 한 번 핥는다","cap":"He left for the army."},
            {"scene":"가을 노을, 다 자란 진돗개가 혼자 빈 길을 본다. 지붕 위 까치","action":"귀가 길 쪽으로 움찔","cap":"Every evening, he waited."},
            {"scene":"(2컷 마지막 프레임에서 이어짐) 까치가 길 끝을 향해 울고 개의 귀가 선다","action":"까치가 울고 개 꼬리가 흔들린다","cap":"A magpie's song means someone's coming."},
            {"scene":"해 질 녘, 군복 입은 청년이 무릎 꿇고 개가 품에 머리를 묻는다. 벤치 끝의 까치","action":"꼬리가 천천히 흔들리고 청년이 눈을 감고 미소","cap":"He came home."}],
 "bible":D_bible,"shots":dshots,
 "details":[{"prop":"빨간 반다나(새것 → 바램)","where":[1,2,4],"meaning":"같은 개, 흐른 시간"},
            {"prop":"강아지 → 다 자란 진돗개","where":[1,2,4],"meaning":"군 복무 기간 동안 자람(약 1년 반, 개 성장과 맞음)"},
            {"prop":"감나무(봄 → 주황 감)","where":[1,2],"meaning":"계절이 지남"}],
 "format":"loyal-dog-reunion + Kachi good-news song","hook_type":"farewell-first-frame","music":"music_i-believe-2",
 "pinned":"Who waited for YOU to come home? 🐕 Tell Kachi 💛",
 "description":"He left for the army in spring. His little Jindo waited at the bus stop every evening.\nIn Korea, when a magpie sings, someone you love is on the way."+END+"#Jindo #Dog #Korea #LoyalDog #Reunion #shorts",
 "tags":["Jindo","dog","loyal dog","reunion","military","bus stop","Korea","magpie","miniature animation","Kachi","From Korea With Love"],
 "notes":"3컷은 2컷 영상 마지막 프레임에서 시작(새 그림 없음). 군복은 계급장·명찰·패치 없는 단색(정치·북한 연상 없음). 한 컷 최대 1명 + 개 + 까치. 18개월 복무 → 강아지가 성견으로 자람(수명·나이 맞음). 4컷 청년 얼굴은 1컷 ref. 정류장 표지·시간표 글자 금지.",
 "p0":{"surprise":4,"emotion":5,"natural":4,"kachi":4},
 "why":"원안(매일 할머니 기다리는 개)은 반전·까치 역할 없음(P0 미달) → 입대 이별을 첫 컷에, 까치 울음(반가운 손님 속설)이 귀환을 알리는 회수. 충견 기다림(하루 12만~76만 회). 3컷 마지막 프레임 이어 쓰기로 그림 1장 절약",
})

# ---------- 생성 작업 파일 + 요약 출력 ----------
import os
os.makedirs("scripts/side/gen_next", exist_ok=True)
slug = {"P261102-cat-basket":"M261102-cat-basket","P261102-dad-longjohns":"M261102-dad-longjohns","P261103-market-sweetpotato":"M261103-market-sweetpotato","P261103-jindo-army":"M261103-jindo-army"}
for p in P:
    imgs, vids = [], []
    for s in p["shots"]:
        if s["img_prompt"]:
            imgs.append({"id": s["id"], "kind": "image", "endpoint": "xai/grok-imagine-image-2.0",
                         "ref": [r[:-5] for r in s["refs"]], "body": {"prompt": s["img_prompt"], "aspect_ratio": "9:16"}})
        src = f"social/side/gen/{s['id']}.jpeg"
        if s["reuse"] and s["reuse"].startswith("lastframe:"):
            prev = p["shots"][int(s["reuse"].split(":")[1]) - 1]["vid"]
            src = f"social/side/gen/{prev}_last.jpeg"
        vids.append({"id": s["vid"], "kind": "video", "endpoint": "alibaba/wan-3.0/image-to-video", "image": src,
                     "body": {"prompt": s["action"] + " " + TAIL, "duration": 5}})
    json.dump(imgs, open(f"scripts/side/gen_next/{slug[p['id']]}-img.json", "w"), ensure_ascii=False, indent=1)
    json.dump(vids, open(f"scripts/side/gen_next/{slug[p['id']]}-vid.json", "w"), ensure_ascii=False, indent=1)
    p["gen"] = slug[p["id"]]
    n_img = len(imgs); n_vid = len(vids)
    p["est_usd"] = round(n_img * 0.125 + n_vid * 0.25, 3)
    print(p["id"], len(p["title"]), p["title"], "img", n_img, "vid", n_vid, "$", p["est_usd"])
json.dump(P, open("scripts/side/plans_next/261029-0945-plans.json", "w"), ensure_ascii=False, indent=1)
