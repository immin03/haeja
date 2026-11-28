"""황제의 일기 에세이형 롱폼 1편 · 나이 들수록 사람을 줄이는 사람들의 진짜 이유 (2026-11-28)
python3 lf01.py gen   → scripts/side/gen/EDL261128-lf01.json (현대 장면 그림, Z-Image) + scripts/side/voices_req.json (녹음)
python3 lf01.py spec  → scripts/side/ed_long/spec_lf01.json (렌더 설정)

11/28 대표 결정
- 벤치마킹(심리학 탐정 「인생 후반전에 강해지는 남자들」 64만, 부자 패턴 연구소 45만, 하나둘 심리학 16만) 틀을 따른 에세이형 롱폼.
  기획안: Claude Docs 「황제의 일기 롱폼 1편 기획안」, 프로젝트 문서 BENCH-PSYDETECTIVE-2026-11-28.
- 그림체 A(실사 시네마틱, 어두운 바탕에 따뜻한 불빛). 새 그림은 Z-Image Turbo(장당 $0.015).
- 기존 소스는 톤이 맞는 것만 조금: 로마 가로 영상(황제 구간·인용), 현대 그림 3장.
- 저화질(540p)로 먼저 렌더 → 대표 수정 → 최종 렌더.
- 사례 인물 '영수'는 여러 이야기를 재구성한 가상 인물(설명란에 표기).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TAG = "lf01"
G = "tc_6731b2e0855f351b98d30c48"   # 건석 (해설)
M = "tc_62d66c2d1523be99355fda02"   # 명일 (황제)

STYLE = ("Dark low-key cinematic film still, Rembrandt lighting, warm amber and champagne-gold highlights, deep blacks, "
         "the background falls into near-black shadow, subtle film grain, shallow depth of field, 35mm, horizontal 16:9, "
         "main subject in the middle band of the frame, contemporary Korea. No text, no letters, no readable screens, no logos.")
YS = ("a Korean man about 58 years old with grey-streaked short black hair, deep forehead lines and tired kind eyes, clean-shaven, "
      "wearing a plain charcoal cardigan over a dark shirt")

IMAGES = {
 "lf1_phone_glow": "Close-up of an older man's hand holding a smartphone in a dark room at night, his thumb scrolling a very long list, the screen glow lighting his fingers, the list is only soft blurred lines.",
 "lf1_scroll_face": f"Close-up of {YS}, his face lit only by the cold glow of a phone screen held below, late at night, eyes reading.",
 "lf1_calllog": "A smartphone lying face down on a wooden kitchen table beside a cup of tea gone cold, one warm pendant lamp above, the rest of the room in darkness.",
 "lf1_emptytable": "A round restaurant table after a gathering, empty chairs pushed back, half-empty glasses and plates, a man in a dark coat leaving through the door in the background, dim warm light.",
 "lf1_envelopes": "A neat stack of plain white envelopes in an open wooden desk drawer, an older man's hand resting on top, lit by a small desk lamp.",
 "lf1_window_man": f"{YS} standing by a dark apartment window at night looking out at distant city lights, calm face, one warm lamp behind him.",
 "lf1_hall_three": "A very long wooden dining table in a dim modern hall with dozens of empty chairs fading into darkness, only three chairs at the near end lit by one warm pendant lamp, three teacups steaming, no people.",
 "lf1_two_paths": "A lone man in a dark coat standing where a quiet park path splits in two at dusk, one path toward a warm lit house, the other into darkness, seen from behind.",
 "lf1_ys_table": f"{YS} sitting alone at a wooden kitchen table late at night, hands clasped, looking down, a smartphone face down beside an open notebook and a cup of tea, one warm pendant lamp above.",
 "lf1_ys_office": f"{YS} sitting at his desk in an emptying office in the evening, most desks dark, a framed photo and a small plant on his desk, warm desk lamp.",
 "lf1_ys_sleep": f"{YS} sitting at a kitchen table at night scrolling his phone, behind him a bedroom door left slightly open into darkness, quiet apartment.",
 "lf1_phone_list": "Extreme close-up of a smartphone screen in the dark showing a long scrolling list of contacts as blurred unreadable lines, warm reflections, shallow focus.",
 "lf1_bizcards": "An old leather business card holder overflowing with faded business cards on a wooden table, cards blurred and unreadable, warm lamp light.",
 "lf1_ys_wonder": f"Close-up of {YS} at night, phone light on his face, he pauses and stares into space, thoughtful.",
 "lf1_finger": "Close-up of an older man's finger touching a phone screen, counting, the screen only soft blurred light, dark kitchen.",
 "lf1_family_photo": "A small framed family photo on a dark wooden shelf, the photo softly out of focus, a reading lamp glowing beside it.",
 "lf1_ys_facedown": f"{YS} with his hands folded on a wooden table at night, a smartphone placed face down in front of him, he sits very still, one pendant lamp.",
 "lf1_ys_city": f"{YS} standing at a tall window in a dark living room at night, his reflection faint in the glass, the city lights below.",
 "lf1_cafe_envelope": "Inside a small old-fashioned coffee shop in the evening, two Korean men in their late fifties at a table, a white envelope slid across the table, warm dim lights.",
 "lf1_friend_leaves": f"In a small coffee shop in the evening, a man walks out of the door with his back turned, while {YS} remains seated alone at the table, looking at the empty chair.",
 "lf1_son_phone": f"A Korean holiday dinner table at night with many dishes, a grown son in his thirties looking down at his phone, {YS} beside him speaking to him, warm low light.",
 "lf1_ys_dark": f"{YS} sitting alone in a dark living room late at night, only a small floor lamp on, his face half in shadow, quiet.",
 "lf1_windows": "A large apartment building at night seen from across the street, only a few windows lit with warm light, in some of them a lone figure sitting at a table.",
 "lf1_crossroads": "Two older men in dark coats walking away from each other at a quiet night crossroads, wet asphalt reflecting warm streetlights.",
 "lf1_gathering": "A crowded noisy Korean restaurant gathering of men in their fifties, glasses raised, one older man at the end of the table forcing a tired smile, warm busy light.",
 "lf1_taxi": "An older Korean man in a suit sitting in the back seat of a taxi late at night, head resting against the window, exhausted, city lights streaking past.",
 "lf1_notebook": "An older man's hands opening a small dark leather notebook on a wooden table under a warm lamp, a pen beside it.",
 "lf1_ys_morning": f"{YS} by a kitchen window in the early morning, holding a mug with both hands, soft first light on his calm face, the room still dim.",
 "lf1_clock": "An old round wall clock in a dim living room, a single warm lamp below it, quiet evening.",
 "lf1_library": "An empty university library reading room at night, long wooden desks with green-shaded lamps, rows of books in shadow.",
 "lf1_networking": "A busy evening networking party of young Korean professionals in their late twenties, exchanging business cards and laughing, warm bokeh lights.",
 "lf1_older_couple": "An older Korean couple in their sixties laughing quietly at a small table in a warm tea house at night, cups of tea between them.",
 "lf1_ripples": "Top view of dark still water in a stone basin, a single drop creating concentric rings of warm golden reflected light.",
 "lf1_candles": "Five lit candles in a tight circle on a dark table, with more unlit candles arranged in wider rings around them fading into darkness.",
 "lf1_phone_cups": "A smartphone lying on a wooden table next to five small teacups arranged in a semicircle, warm lamp light, dark background.",
 "lf1_archive": "Tall archive shelves full of old cardboard folders and boxes in a dim room, a single desk lamp at the end of the aisle.",
 "lf1_album": "An old photo album open on a table, black-and-white photographs softly out of focus, an elderly hand turning a page, warm lamp.",
 "lf1_elder_walk": "Two Korean men in their eighties walking slowly side by side through an autumn park at golden dusk, one resting a hand on the other's shoulder, seen from behind.",
 "lf1_ys_pen": f"{YS} at a kitchen table at night holding a pen above an open notebook, the phone pushed aside, thinking.",
 "lf1_ys_cafe_alone": f"{YS} sitting alone at a small coffee shop table in the evening, looking at the empty chair across from him and a half-finished cup.",
 "lf1_empty_chair": "An empty wooden chair at a small coffee shop table, a half-finished cup of coffee in front of it, dim warm light, nobody there.",
 "lf1_cracked_cup": "A white porcelain cup with a thin crack on a dark wooden table, a single beam of warm light on it.",
 "lf1_umbrella": "An older man in a dark coat holding a black umbrella, standing calmly on a rainy street at night, warm shop light behind him.",
 "lf1_ys_listen": f"{YS} sitting across a table from another man in the evening, listening calmly with a slight nod, warm low light.",
 "lf1_door": "A wooden apartment door left half open, warm light spilling from inside into a dark hallway.",
 "lf1_calendar": "A paper wall calendar crowded with many circled dates and scribbled marks, nothing readable, lit by a single lamp in a dark room.",
 "lf1_yearend": "A Korean year-end company dinner in a large banquet room, rows of men in suits raising glasses, noisy, warm golden light.",
 "lf1_ys_home_late": f"{YS} loosening his tie at the entrance of his dark apartment late at night, shoes still on, tired face, one hallway light.",
 "lf1_pruning": "An older man's hands carefully pruning a small bonsai tree with tiny shears on a wooden table, cut leaves falling, warm lamp.",
 "lf1_phone_down": f"{YS} gently setting his phone down on a table after a call in the evening, a calm settled expression.",
 "lf1_two_friends": "Two old Korean friends in their sixties laughing together at a small table in a warm street tea house at night, cups of tea.",
 "lf1_bonsai": "A healthy, neatly pruned small bonsai tree on a dark wooden table, warm side light, peaceful.",
 "lf1_ink": "A single drop of dark ink spreading slowly in a clear glass of water, backlit by warm golden light, black background.",
 "lf1_gossip": "Three men in their fifties at a dim bar table, one leaning in and talking animatedly, another slumped and tired, glasses on the table.",
 "lf1_river_talk": "Two older people walking slowly along a riverside path at dusk talking quietly, warm streetlights coming on, seen from behind.",
 "lf1_dye": "White cloth being slowly dipped into a dark indigo dye vat, the color spreading upward through the fabric, warm side light, close-up.",
 "lf1_ys_dawn": f"{YS} standing at a window at dawn, warm golden light falling on his calm face, eyes closed for a moment.",
 "lf1_reading_chair": "An empty reading armchair with a folded blanket, a small lamp and an open book on a side table, a quiet dark room at night.",
 "lf1_coat_door": "An older man hurriedly putting on his coat at his apartment door at night, phone in hand, restless.",
 "lf1_ys_trail": f"{YS} in a dark hiking jacket climbing a forest mountain trail near Seoul at early dawn, mist between the trees, walking stick.",
 "lf1_summit": "A mountain summit rest area at sunrise, four Korean hikers in their sixties sharing tea from a thermos and laughing, golden light, mist below.",
 "lf1_ridge": "Silhouette of an older man standing alone on a mountain ridge at sunrise, layers of misty mountains glowing gold behind him.",
 "lf1_hall_three_close": "Close view of three chairs at the end of a long dark table lit by one warm pendant lamp, three teacups steaming, the rest of the room in shadow.",
 "lf1_five_cups": "Five teacups around a small round wooden table under one warm pendant lamp, steam rising, cozy and quiet, no people.",
 "lf1_ys_writes": f"{YS} writing slowly in a small notebook at a kitchen table at night under one warm pendant lamp, his phone face down aside, a calm settled face.",
 "lf1_two_cups": "Two teacups on a small wooden table by a window at night, one warm lamp, quiet and intimate.",
 "lf1_ys_side": f"Side profile of {YS} sitting by a dark apartment window at night, city lights blurred outside, his face quiet and unreadable, one warm lamp behind.",
 "lf1_friends_three": "Three Korean friends in their sixties, two women and one man, talking calmly over cups of tea at a small wooden table in a quiet tea house at night, warm pendant light.",
 "lf1_ys_street": f"{YS} walking home alone along a narrow quiet residential street at night, seen from behind, wet pavement reflecting warm streetlights.",
 "lf1_coat_door2": "Seen from behind, an older Korean man in a dark coat standing at his apartment front door at night about to go out, the door half open into a dim corridor, restless posture.",
 "lf1_phone_list2": "A smartphone lying on a dark wooden table at night, its screen glowing softly but completely out of focus, only warm bokeh light, no interface visible.",
}

# (화면, 녹음 키, 대본). 화면: 'n:<키>' = 새 그림, 'i:<키>' = 기존 그림, 'v:<키>' = 기존 로마 영상. 키가 m 으로 시작하면 황제(명일) 목소리.
SEQ = [
 # 0:00 훅
 ("n:lf1_phone_glow", "h01", "휴대폰 연락처를 한번 열어 보십시오. 몇 명이 들어 있습니까."),
 ("n:lf1_scroll_face", "h02", "오백 명, 어쩌면 천 명이 넘을지도 모릅니다."),
 ("n:lf1_calllog", "h03", "그런데 지난 한 달 동안, 내가 먼저 전화를 건 사람은 몇 명입니까. 아마 손에 꼽을 겁니다."),
 ("n:lf1_emptytable", "h04", "우리는 이것을 쓸쓸한 일이라고 배웠습니다. 나이가 들면 사람이 떠난다고요."),
 ("n:lf1_envelopes", "h05", "모임이 줄고, 전화가 줄고, 경조사 봉투만 남는다고요."),
 ("n:lf1_window_man", "h06", "그런데 이상한 사람들이 있습니다. 떠나가기를 기다리지 않고, 스스로 줄이는 사람들입니다."),
 ("n:lf1_hall_three", "h07", "그리고 그들은, 나이가 들수록 오히려 편안해집니다."),
 # 0:40 약속
 ("v:hfr_tent_write_dark", "p01", "천팔백 년 전, 세상에서 만나야 할 사람이 가장 많았던 한 남자도 같은 일을 했습니다."),
 ("v:hfr_torchcrowd_wide", "p02", "로마의 황제, 마르쿠스 아우렐리우스입니다."),
 ("n:lf1_two_paths", "p03", "사람을 줄이는 사람과, 그저 사람이 줄어드는 사람. 둘 사이의 차이는 단 하나입니다."),
 ("v:libv_candle_face", "p04", "그 하나는, 이 영상의 마지막에 말씀드리겠습니다."),
 ("INTRO", None, None),
 # 1:05 한 사람의 밤
 ("n:lf1_ys_table", "y01", "영수 씨의 이야기부터 하겠습니다. 여러 사람의 이야기를 모아 다시 꾸민, 한 사람의 이야기입니다."),
 ("n:lf1_ys_office", "y02", "영수 씨는 올해 쉰여덟입니다. 한 회사에서 스물여덟 해를 일했고, 석 달 뒤면 정년입니다."),
 ("n:lf1_ys_sleep", "y03", "어느 토요일 밤, 아내가 먼저 잠든 뒤, 영수 씨는 식탁에 앉아 휴대폰 연락처를 처음부터 끝까지 넘겨 보았습니다."),
 ("n:lf1_phone_list2", "y04", "천이백 명이 조금 넘었습니다."),
 ("n:lf1_bizcards", "y05", "거래처 부장, 이십 년 전 같은 부서 후배, 이름만 보고는 얼굴이 떠오르지 않는 사람들."),
 ("n:lf1_ys_wonder", "y06", "그는 문득 궁금해졌습니다. 이 중에 지난 한 달 동안 통화한 사람은 몇 명일까."),
 ("n:lf1_finger", "y07", "통화 기록을 열어 세어 보니, 여섯 명이었습니다. 그중 넷은 일 때문이었습니다."),
 ("n:lf1_family_photo", "y08", "남은 두 사람은, 아내와 딸이었습니다."),
 ("n:lf1_ys_facedown", "y09", "영수 씨는 휴대폰을 엎어 놓고 한참 앉아 있었습니다."),
 ("n:lf1_ys_side", "y10", "서운함도 아니고, 억울함도 아닌, 이상한 기분이었습니다."),
 ("n:lf1_ys_city", "y11", "스물여덟 해 동안 쌓은 사람이 천이백 명인데, 정년이 지나면 이 중 몇 명이 남을까."),
 ("n:lf1_cafe_envelope", "y12", "지난달, 오랜 친구 하나가 영수 씨에게 돈을 빌려 갔습니다."),
 ("n:lf1_friend_leaves", "y13", "봉투를 받아 든 친구는 고맙다는 말도 없이 일어섰습니다."),
 ("n:lf1_son_phone", "y14", "지난 명절에는 다 큰 아들이 식탁에서 휴대폰만 보았습니다. 영수 씨가 무슨 말을 해도 고개를 들지 않았습니다."),
 ("n:lf1_ys_dark", "y15", "그날 밤 영수 씨는 생각했습니다. 사람이 떠나가는 게 아니라, 나는 처음부터 혼자였던 건 아닐까."),
 ("n:lf1_windows", "y16", "많은 분들이 이 밤을 압니다. 쉰이 넘고, 예순이 가까워지면, 누구나 한 번은 이 식탁에 앉게 됩니다."),
 ("n:lf1_crossroads", "y17", "그런데 여기서 사람은 두 갈래로 나뉩니다."),
 ("n:lf1_gathering", "y18", "한쪽은 남은 사람이라도 붙잡으려 애씁니다. 모임마다 나가고, 단체 대화방마다 답을 하고, 서운한 일이 생겨도 참습니다."),
 ("n:lf1_taxi", "y19", "그리고 더 지칩니다."),
 ("n:lf1_notebook", "y20", "다른 한쪽은, 그 밤을 계기로 스스로 줄이기 시작합니다."),
 ("n:lf1_ys_morning", "y21", "놀라운 것은, 두 번째 사람들이 더 외로워지지 않는다는 겁니다. 오히려 더 단단해집니다. 왜 그럴까요."),
 # 3:00 왜 줄어드는가
 ("n:lf1_clock", "r01", "먼저 알아야 할 것이 있습니다. 나이가 들수록 사람이 줄어드는 것은, 고장이 아니라 정상입니다."),
 ("n:lf1_library", "r02", "미국 스탠퍼드대학교의 심리학자 로라 카스텐슨은 이것을 오래 연구했습니다."),
 ("n:lf1_networking", "r03", "사람은 남은 시간이 넉넉하다고 느낄 때, 새로운 사람을 많이 만나려 합니다. 언젠가 도움이 될지 모르니까요."),
 ("v:libv_hourglass", "r04", "그런데 남은 시간이 유한하다고 느끼기 시작하면, 고르기 시작합니다. 넓은 관계보다, 마음이 편한 소수를 택합니다."),
 ("n:lf1_friends_three", "r05", "이것을 사회정서적 선택 이론이라고 부릅니다."),
 ("n:lf1_older_couple", "r06", "중요한 것은, 이 변화가 나이 든 사람들을 더 불행하게 만들지 않았다는 점입니다. 관계의 수는 줄었지만, 감정의 만족도는 오히려 높아졌습니다."),
 ("n:lf1_ripples", "r07", "영국의 인류학자 로빈 던바도 비슷한 이야기를 합니다."),
 ("n:lf1_candles", "r08", "사람이 진짜로 가깝게 지낼 수 있는 사람은, 가장 안쪽에 다섯 명 남짓입니다. 그 바깥에 열다섯, 그 바깥에 쉰, 그리고 얼굴과 이름을 아는 정도가 백오십 명입니다."),
 ("n:lf1_phone_cups", "r09", "연락처에 천이백 명이 있어도, 마음이 닿는 사람은 원래 다섯 명 남짓이라는 뜻입니다."),
 ("n:lf1_archive", "r10", "그리고 하버드대학교가 여든 해 넘게 같은 사람들을 따라간 연구가 있습니다. 성인발달연구입니다."),
 ("n:lf1_album", "r11", "이 연구를 이끄는 로버트 월딩거 교수는 이렇게 정리합니다."),
 ("n:lf1_elder_walk", "r12", "여든 살에 가장 건강했던 사람들은, 쉰 살 무렵 관계에 가장 만족했던 사람들이었다고요. 관계의 수가 아니라, 관계의 질이었습니다."),
 ("n:lf1_ys_pen", "r13", "그러니까 영수 씨의 연락처가 줄어드는 것은 문제가 아닙니다. 문제는, 줄어드는 것을 그냥 당하느냐, 아니면 내가 고르느냐입니다."),
 # 5:00 황제
 ("v:hfr_rainforest_column", "e01", "이제 한 남자를 만나 보겠습니다. 서기 170년대, 로마 제국은 북쪽 국경에서 끝없는 전쟁을 치르고 있었습니다."),
 ("v:hfr_snowmarch_rider", "e02", "그 한가운데, 쉰 줄에 들어선 황제가 있었습니다. 마르쿠스 아우렐리우스."),
 ("v:hfr_senate_whisper_wide", "e03", "그는 하루에도 수백 명을 만났습니다. 원로원 의원, 장군, 청원하러 온 사람, 아첨하러 온 사람, 그를 미워하는 사람."),
 ("v:hfr_petition_point", "e04", "세상에서 가장 많은 사람을 상대해야 했던 남자였습니다."),
 ("v:hfr_tent_write_blue", "e05", "그 남자가 전쟁터를 오가며 밤마다 써 내려간 일기가 있습니다. 훗날 『명상록』이라고 불리게 된 글입니다."),
 ("v:cep1_stop", "e06", "그런데 그 일기의 첫 권을 펼쳐 보면, 이상한 점이 있습니다. 전쟁 이야기도, 정치 이야기도 없습니다."),
 ("v:cep1_diary2", "e07", "그 첫 권은 사람의 이름으로 채워져 있습니다."),
 ("v:hfr_garden_read", "m0", "할아버지에게서는 온화함을 배웠다. 어머니에게서는 검소함을 배웠다. 스승 루스티쿠스에게서는, 내 성품을 고치고 다듬어야 한다는 것을 배웠다."),
 ("v:hfr_elder_nod", "e08", "열 명이 훌쩍 넘는 사람들의 이름과, 그들에게서 배운 것들."),
 ("v:libv_close_diary", "e09", "수만 명을 만난 남자가 일기의 첫머리에 남긴 것은, 고마운 사람들의 짧은 명단이었습니다."),
 ("v:hfr_milkyway_camp_back", "e10", "그는 사람을 미워해서 줄인 것이 아니었습니다. 누구를 마음에 남길지, 스스로 골랐던 것입니다."),
 ("v:libv_window_moon", "e11", "그렇다면 사람을 줄이는 사람들에게는, 어떤 이유가 있는 걸까요. 네 가지로 말씀드리겠습니다."),
 # 이유 1
 ("CARD:I", None, None),
 ("n:lf1_ys_cafe_alone", "a01", "첫 번째. 그들은 사람에게 실망하지 않습니다. 어떤 사람을 만날지 미리 알기 때문입니다."),
 ("n:lf1_empty_chair", "a02", "영수 씨가 가장 힘들었던 것은, 친구가 고맙다는 말 없이 떠난 일이 아니었습니다. 그 친구가 그럴 줄 몰랐다는 사실이었습니다."),
 ("n:lf1_cracked_cup", "a03", "우리는 대개 사람에게 기대를 걸어 두고, 그 기대가 무너질 때 상처를 받습니다."),
 ("v:hfr_tent_lookup_blue", "a04", "마르쿠스는 매일 아침, 일을 시작하기 전에 스스로에게 이렇게 말했습니다."),
 ("v:hfr_alone_stand", "m1", "오늘 나는 참견하는 사람, 배은망덕한 사람, 오만한 사람, 속이는 사람, 시기하는 사람을 만날 것이다."),
 ("v:hfr_petition_listen", "a05", "비관처럼 들리지만, 아닙니다. 그는 이어서 이렇게 씁니다. 그들이 그렇게 된 것은 무엇이 선하고 무엇이 악한지 모르기 때문이며, 그들도 나와 같은 사람이라고."),
 ("n:lf1_umbrella", "a06", "미리 알고 만나면, 같은 일을 겪어도 덜 다칩니다."),
 ("n:lf1_ys_listen", "a07", "사람을 줄이는 사람들은 차가운 사람이 아닙니다. 기대를 사람마다 다르게 거는 사람들입니다."),
 ("n:lf1_door", "a08", "아무에게나 마음을 다 주지 않으니, 아무에게나 다치지도 않습니다."),
 ("n:lf1_ys_street", "a09", "영수 씨가 봉투를 건넨 그 친구를 미워할 필요는 없습니다. 다만 그 친구에게는, 다음부터 그만큼만 기대하면 됩니다."),
 # 이유 2
 ("CARD:II", None, None),
 ("n:lf1_calendar", "b01", "두 번째. 그들은 약속을 줄이는 게 아니라, 필요 없는 것을 덜어 냅니다."),
 ("n:lf1_yearend", "b02", "정년을 앞둔 영수 씨의 달력에는 한 달에 모임이 열한 개 있었습니다. 동창회, 옛 부서 모임, 거래처 송년회, 이름만 남은 산악회."),
 ("n:lf1_ys_home_late", "b03", "그중 다녀와서 마음이 가벼웠던 자리는 몇 개였을까요. 영수 씨는 솔직하게 세어 보았습니다. 둘이었습니다."),
 ("v:hfr_tent_write_dark", "b04", "마르쿠스는 일기에 이렇게 적었습니다."),
 ("v:libv_candle_face", "m2", "평온하고 싶다면, 적게 하라. 꼭 필요한 일만 하라."),
 ("v:libv_dust_light", "b05", "그리고 이렇게 덧붙입니다. 우리가 하는 말과 행동의 대부분은 필요 없는 것이니, 그것을 덜어 내면 시간도 생기고 마음도 고요해진다고."),
 ("n:lf1_pruning", "b06", "여기서 오해하면 안 되는 것이 있습니다. 덜어 낸다는 것은 연락을 끊는다는 뜻이 아닙니다."),
 ("n:lf1_phone_down", "b07", "다녀오면 지치기만 하는 자리에, 의무감으로 가지 않는 것입니다."),
 ("n:lf1_two_friends", "b08", "대신 그렇게 남은 시간을, 다녀오면 마음이 따뜻해지는 사람에게 씁니다."),
 ("n:lf1_bonsai", "b09", "열한 개의 모임 대신 두 개의 모임에 가는 사람은, 덜 외로운 것이 아니라 더 깊이 연결되어 있습니다."),
 # 이유 3
 ("CARD:III", None, None),
 ("n:lf1_ink", "c01", "세 번째. 그들은 곁에 두는 사람이 내 마음의 색을 정한다는 것을 압니다."),
 ("n:lf1_gossip", "c02", "어떤 사람과 한 시간을 보내고 나면 이유 없이 기운이 빠집니다. 남 이야기, 돈 이야기, 누가 잘되고 누가 망했다는 이야기."),
 ("n:lf1_river_talk", "c03", "어떤 사람과 한 시간을 보내고 나면 내가 조금 나은 사람이 된 것 같습니다."),
 ("v:hfr_tent_face_dark", "c04", "마르쿠스는 이렇게 썼습니다."),
 ("v:libv_rain_window", "m3", "네 마음은 네가 자주 떠올리는 것들을 닮아 간다. 영혼은 생각에 물든다."),
 ("n:lf1_dye", "c05", "자주 떠올리는 것에는, 자주 만나는 사람도 들어갑니다."),
 ("v:hfr_elder_wide", "c06", "그래서 그는 또 이렇게 적었습니다. 기운을 내고 싶을 때는, 곁에 있는 사람들의 좋은 점을 떠올려 보라고. 누구는 부지런하고, 누구는 겸손하고, 누구는 너그럽다고."),
 ("v:cep1_diary", "c07", "일기 첫 권의 그 명단이 바로 이것이었습니다. 그는 힘든 밤마다, 자신을 물들인 좋은 사람들을 다시 떠올렸던 것입니다."),
 ("n:lf1_ys_dawn", "c08", "나이가 들수록 사람을 줄이는 사람들은, 결국 자기 마음의 색을 지키는 사람들입니다. 남은 시간 동안 어떤 색으로 물들고 싶은지, 스스로 고르는 사람들입니다."),
 # 이유 4
 ("CARD:IV", None, None),
 ("n:lf1_reading_chair", "d01", "네 번째. 그들은 혼자 있는 시간을 빈자리가 아니라 쉼터로 씁니다."),
 ("n:lf1_coat_door2", "d02", "사람을 줄이면 가장 먼저 찾아오는 것이 혼자 있는 시간입니다. 많은 사람이 이 시간을 견디지 못해 다시 아무 모임에나 나갑니다."),
 ("v:hfr_milkyway_camp_wide", "d03", "마르쿠스는 이 문제를 정확하게 알고 있었습니다. 사람들은 쉬고 싶을 때 시골로, 바닷가로, 산으로 떠나려 한다. 그러나 언제든 자기 안으로 물러날 수 있다."),
 ("v:hfr_alone_breath", "m4", "사람이 물러날 수 있는 곳 중에, 자기 마음보다 고요하고 편안한 곳은 없다."),
 ("n:lf1_ys_trail", "d04", "영수 씨는 요즘 토요일 아침마다 혼자 산에 오릅니다. 처음 몇 주는 어색했습니다."),
 ("n:lf1_summit", "d05", "그런데 어느 날 정상에서, 처음 보는 또래 사람들과 보온병 차를 나눠 마시며 한참을 웃었습니다."),
 ("n:lf1_ridge", "d06", "혼자 있는 법을 아는 사람에게는, 이상하게도 좋은 사람이 찾아옵니다. 매달리지 않으니, 상대도 편안하기 때문입니다."),
 # 14:00 약속한 답
 ("n:lf1_ys_table", "z01", "이제 처음에 약속드린 이야기를 하겠습니다. 사람을 줄이는 사람과, 그저 사람이 줄어드는 사람. 둘의 차이는 단 하나입니다."),
 ("n:lf1_hall_three", "z02", "!줄어드는 사람은, 누가 떠났는지를 셉니다."),
 ("n:lf1_hall_three_close", "z03", "!줄이는 사람은, 누구를 남길지를 고릅니다."),
 ("n:lf1_five_cups", "z04", "같은 다섯 명이 남아도, 떠나간 천 명을 세는 사람은 외롭고, 남은 다섯 명을 고른 사람은 넉넉합니다."),
 ("v:cep1_read", "z05", "수만 명을 만났던 황제가 일기 첫 권에 적은 것은 떠난 사람들의 명단이 아니었습니다. 고마운 사람들의 명단이었습니다."),
 ("n:lf1_ys_writes", "z06", "그날 밤 식탁에 앉아 있던 영수 씨는, 이제 연락처 대신 공책을 엽니다. 그리고 다섯 사람의 이름을 적습니다."),
 ("RECAP", None, None),
 ("n:lf1_two_cups", "q01", "여러분에게 끝까지 남은 한 사람은 누구입니까. 이름은 적지 않으셔도 됩니다. 어떤 사람인지만, 댓글로 들려주세요."),
 ("FINALE", None, None),
]
RETAKE = {"p04": 2, "r08": 2, "r09": 2, "e07": 2, "b02": 2, "e03": 4, "d02": 4, "y06": 3, "m2": 2, "b05": 2, "b08": 2, "c06": 4}   # 11/28 음성 관문 불통과(1·2·3·4차)
TEMPO_X = {"y06": 0.96, "e03": 0.96, "c06": 1.0, "d02": 0.96}   # 3차까지 끌림이 남은 줄: 늦추는 폭을 줄인다
RECAP_V = [("t01", "오늘 밤, 이 세 가지만 해 보십시오."),
           ("t02", "첫째, 지난 한 달 동안 내가 먼저 연락한 사람의 이름을 적어 보십시오."),
           ("t03", "둘째, 끝까지 곁에 두고 싶은 다섯 사람을 적고, 그중 한 사람에게 오늘 고맙다고 말해 보십시오."),
           ("t04", "셋째, 다녀오면 지치기만 하는 약속 하나를, 정중하게 미뤄 보십시오.")]
RECAP_ITEMS = ["먼저 연락한 사람의 이름 적기", "곁에 둘 다섯 사람 적고, 한 사람에게 고맙다고 말하기", "지치기만 하는 약속 하나, 정중히 미루기"]
OUTRO_V = [("o1", "좋아요와 구독은, 영상 제작에 큰 힘이 됩니다. 감사합니다."),
           ("o2", "다음 이야기에서도, 황제가 일기에 남긴 문장으로 오늘을 함께 짚어 보겠습니다.")]
VERSE = {"m1": (["오늘 나는 참견하는 사람, 배은망덕한 사람,", "오만한 사람, 시기하는 사람을 만날 것이다."], "명상록 2권 1절"),
         "m2": (["평온하고 싶다면, 적게 하라.", "꼭 필요한 일만 하라."], "명상록 4권 24절"),
         "m3": (["네 마음은 네가 자주 떠올리는 것들을 닮아 간다.", "영혼은 생각에 물든다."], "명상록 5권 16절"),
         "m4": (["자기 마음보다", "고요하고 편안한 곳은 없다."], "명상록 4권 3절"),
         "m0": (["고마운 사람들의 이름으로 시작하는 일기"], "명상록 1권")}
CARDS = {"I": ("THE FIRST REASON", "첫 번째 이유 · 사람에게 실망하지 않는다", "They know whom they will meet"),
         "II": ("THE SECOND REASON", "두 번째 이유 · 필요 없는 것을 덜어 낸다", "Do less, but better"),
         "III": ("THE THIRD REASON", "세 번째 이유 · 곁에 두는 사람에게 물든다", "The soul is dyed by its thoughts"),
         "IV": ("THE FOURTH REASON", "네 번째 이유 · 혼자 있는 시간을 쉼터로 쓴다", "No retreat quieter than one's own soul")}
CONCEPT = {"r05": ("심리학 · 카스텐슨", ["사회정서적 선택 이론"], "Socioemotional Selectivity Theory"),
           "r08": ("인류학 · 던바", ["5 · 15 · 50 · 150"], "Dunbar's circles of friendship"),
           "r12": ("하버드 성인발달연구", ["관계의 수가 아니라, 관계의 질"], "Harvard Study of Adult Development")}
CAPTION = {"e01": "기원후 170년대 · 도나우 전선", "y01": "여러 이야기를 재구성한 사례입니다", "c06": "명상록 6권 48절"}


def lines():
    """녹음할 줄 (키, 목소리, 글) — 대본 순서대로"""
    out = []
    for scr, k, txt in SEQ:
        if not k: continue
        if any(o[0] == k for o in out): continue   # 같은 장면 다시 쓰는 줄(z01 등)은 키가 달라 중복 없음
        out.append((k, M if k.startswith("m") else G, txt.lstrip("!")))
    out += [(k, G, t) for k, t in RECAP_V] + [(k, G, t) for k, t in OUTRO_V]
    return out


def gen():
    jobs = []
    for k, p in IMAGES.items():
        prompt = p + " " + STYLE
        assert len(prompt) <= 780, (k, len(prompt))
        jobs.append({"id": k, "kind": "image", "endpoint": "z-image/turbo", "raw_prompt": True, "body": {"prompt": prompt, "aspect_ratio": "16:9"}})
    json.dump(jobs, open(os.path.join(ROOT, "scripts/side/gen/EDL261128-lf01.json"), "w"), ensure_ascii=False, indent=1)
    V = []
    for k, vid, txt in lines():
        V.append({"name": k, "id": vid, "line": txt, "emotion": "tonedown", "tempo": TEMPO_X.get(k, 0.86 if vid == M else 0.92), **({"take": RETAKE[k]} if k in RETAKE else {})})
    json.dump({"requested": "2026-11-28T14:30", "note": "lf01 수정 녹음 — 대표 11/28 '말 속도 살짝 느리게'(해설 0.92·황제 0.86, 속도는 후처리라 0원), 음성 관문 불통과 7줄은 새 테이크", "tag": TAG, "keep": True,
               "lang": "kor", "model": "ssfm-v30", "emotion": "tonedown", "tempo": 1.0, "voices": V},
              open(os.path.join(ROOT, "scripts/side/voices_req.json"), "w"), ensure_ascii=False, indent=1)
    print(f"그림 {len(jobs)}장 · 녹음 {len(V)}줄 · 글자 {sum(len(v['line']) for v in V)}")


def subs_of(txt):
    """자막: 문장 → 32자 넘으면 쉼표에서 나눔"""
    emph = txt.startswith("!"); txt = txt.lstrip("!")
    if emph: return ["!" + txt]
    out = []
    for s in re.split(r"(?<=[.?])\s+", txt.strip()):
        if len(s) <= 32: out.append(s); continue
        parts = [x.strip() for x in s.split(", ")]; cur = ""
        for i, x in enumerate(parts):
            seg = x + ("," if i < len(parts) - 1 else "")
            if cur and len(cur) + 1 + len(seg) > 32: out.append(cur); cur = seg
            else: cur = (cur + " " + seg).strip()
        if cur: out.append(cur)
    return out


def spec():
    vf = {k: f"voice_{TAG}_{i:02d}_{k}.mp3" for i, (k, _, _) in enumerate(lines(), 1)}
    vf["m_x1"] = "../lp3/voice_lp3_07_m_x1.mp3"; vf["e_x2"] = "../ep01x/voice_ep01x_01_e_x2.mp3"
    subs = {}; shots = [{"type": "black", "dur": 0.6, "fixed": True}]
    for scr, k, txt in SEQ:
        if scr == "INTRO":
            shots += [{"type": "black", "dur": 0.4, "fixed": True},
                      {"type": "intro", "sfx": [["cinematic_6.mp3", 1.47, 0.7], ["ring_synth.wav", 2.4, 0.5], ["drum_5.mp3", 3.92, 1.0], ["impact_2.mp3", 3.02, 0.8], ["cinematic_4.mp3", 4.9, 0.55], ["transition_5.mp3", 8.96, 0.5]]},
                      {"type": "episode", "kicker": "ESSAY", "num": 1, "title": "나이 들수록 사람을 줄이는 사람들", "en": "Those Who Choose Fewer", "dur": 4.6, "fixed": True, "amb": ["wind_2.mp3", 0.3], "sfx": [["drum_6.mp3", 0.3, 0.45]], "tout": "black", "fout": 0.8}]
            continue
        if scr.startswith("CARD:"):
            n = scr[5:]; lab, ttl, en = CARDS[n]
            shots.append({"type": "card", "label": lab, "num": n, "title": ttl, "en": en, "dur": 4.0, "fixed": True, "sfx": [["paper_3.mp3", 0.25, 0.4]], "amb": ["wind_2.mp3", 0.25]})
            continue
        if scr == "RECAP":
            shots.append({"type": "recap", "items": RECAP_ITEMS, "voice": [k for k, _ in RECAP_V], "pre": 0.6, "post": 2.0, "gap": 0.7, "nocap": True,
                          "head": "오늘 밤, 이 세 가지만", "head_en": "THREE THINGS FOR TONIGHT", "sfx": [["paper_3.mp3", 0.2, 0.45]], "tin": "dissolve", "fin": 0.8})
            continue
        if scr == "FINALE":
            shots.append({"type": "finale", "dur": 18.0, "voice": ["m_x1", "e_x2", "o1", "o2"], "pre": 0.8, "gap": 0.8, "post": 1.0, "nocap": True, "tin": "black",
                          "slogan": "매일 밤, 황제처럼 생각하라", "prev_kicker": "다른 이야기  ·  황제의 일기", "amb": ["wind_2.mp3", 0.15], "sfx": []})
            continue
        kind, src = scr.split(":", 1)
        s = {"type": "video" if kind == "v" else "still", "src": src, "voice": [k], "pre": 0.3, "post": 0.5,
             "move": {"zoom": [1.0, 1.08] if len(shots) % 2 else [1.08, 1.0]}}
        if kind == "v": s["amb"] = ["fire_0.mp3", 0.25]
        if k.startswith("m"):
            s.update({"pre": 0.6, "post": 1.2, "particles": "dust", "move": {"zoom": [1.0, 1.1]}})
            ln, srcv = VERSE[k]; s["overlays"] = [{"kind": "verse", "lines": ln, "src": srcv, "at_voice": k}]
        if k in CONCEPT:
            kk, ln, en = CONCEPT[k]; s["overlays"] = [{"kind": "concept", "kicker": kk, "lines": ln, "en": en, "at_voice": k, "offset": 0.4, "len": "shot"}]
        if k in CAPTION:
            s.setdefault("overlays", []).append({"kind": "caption", "text": CAPTION[k], "at": 0.3, "pos": "top"})
        if k in ("z02", "z03"): s["post"] = 1.2
        shots.append(s)
        subs[k] = subs_of(txt)
    for k, t in RECAP_V + OUTRO_V: subs[k] = subs_of(t)
    n = len(shots)
    ix = lambda t, k=0: [i for i, x in enumerate(shots) if x["type"] == t][k]
    i_intro, i_ep, i_rc = ix("intro"), ix("episode"), ix("recap")
    c1, c3 = ix("card", 0), ix("card", 2)
    # 11/28 대표: 인트로는 예전 편과 똑같이 — 훅 음악은 인트로 전 검은 화면에서 끝나고(꼬리 없음), 본 음악은 제목 카드 뒤에 시작
    mus = [{"file": "sad_3.mp3", "at_shot": 1, "offset": 0.3, "start": 0, "until_shot": i_intro - 1, "tail": 0.0, "vol": 0.16, "fin": 2, "fout": 1.5},
           {"file": "cinematic_0.mp3", "at_shot": i_ep + 1, "offset": 0.5, "start": 0, "until_shot": c1, "vol": 0.18, "fin": 3, "fout": 3},
           {"file": "cinematic_5.mp3", "at_shot": c1 + 1, "offset": 1.0, "start": 0, "until_shot": c3, "vol": 0.18, "fin": 3, "fout": 3},
           {"file": "sad_1.mp3", "at_shot": c3 + 1, "offset": 1.0, "start": 0, "until_shot": i_rc, "vol": 0.16, "fin": 3, "fout": 3},
           {"file": "cinematic_4.mp3", "at_shot": i_rc, "offset": 0.5, "start": 0, "until_shot": n, "vol": 0.18, "fin": 3, "fout": 3}]
    S = {"root": "../../..", "gen_dir": "social/side/gen", "sfx_dir": "social/side/ed_long/sfx", "music_dir": "social/side/ed_long/music", "out_dir": "_long",
         "intro": {"logo": "docs/emperor/profile_final.png"},
         "monologue_fx": "highpass=f=70,aecho=0.9:0.35:35|70:0.09|0.04,", "voice_gain": {"mono": 3.8, "narr": 1.2, "cast": 0.85}, "cap_scale": 1.3, "corner_logo": "scripts/side/ed_long/corner_logo.png",
         "id": "edl_lf01", "voice_dir": f"social/side/voice_samples/{TAG}", "voice_files": vf, "subs": subs,
         "monologue_voices": [k for k in vf if k.startswith("m")], "music": mus, "shots": shots, "cast_voices": []}
    json.dump(S, open(os.path.join(HERE, "spec_lf01.json"), "w"), ensure_ascii=False, indent=1)
    print(f"장면 {len(shots)}개 · 새 그림 {sum(1 for x in shots if x.get('src','').startswith('lf1_'))}회 사용")


if __name__ == "__main__":
    {"gen": gen, "spec": spec}[sys.argv[1]]()
