"""lf01 유튜브 업로드 정보(제목·설명·태그). 챕터 시간은 렌더 뒤 plan_edl_lf01.json 에서 읽는다.
저장소 루트에서: python3 scripts/side/ed_long/meta_lf01.py > /home/claude/render/lf01_meta.json
"""
import json
D = 'scripts/side/ed_long/'
plan = json.load(open(D + 'plan_edl_lf01.json')); spec = json.load(open(D + 'spec_lf01.json'))
sh = spec['shots']


def at_voice(k):
    for i, x in enumerate(sh):
        v = x.get('voice'); v = [v] if isinstance(v, str) else (v or [])
        if k in v: return plan[i]['t0']


def at_type(t, n=None):
    for i, x in enumerate(sh):
        if x['type'] == t and (n is None or x.get('num') == n): return plan[i]['t0']


mmss = lambda t: f"{int(t // 60)}:{int(t % 60):02d}"
ch = [(0, '연락처 1,200명, 통화한 사람 6명'), (at_voice('y01'), '영수 씨의 토요일 밤'), (at_voice('r01'), '사람이 줄어드는 건 고장이 아니라 정상'),
      (at_voice('e01'), '수만 명을 만난 황제의 일기 첫 권'), (at_type('card', 'I'), '첫 번째 이유 · 사람에게 실망하지 않는다'),
      (at_type('card', 'II'), '두 번째 이유 · 필요 없는 것을 덜어 낸다'), (at_type('card', 'III'), '세 번째 이유 · 곁에 두는 사람에게 물든다'),
      (at_type('card', 'IV'), '네 번째 이유 · 혼자 있는 시간을 쉼터로 쓴다'), (at_voice('z01'), '줄이는 사람과 줄어드는 사람의 단 하나의 차이'),
      (at_type('recap'), '오늘 밤, 이 세 가지만')]
desc = f"""나이가 들수록 사람이 줄어드는 것은 쓸쓸한 일일까요.
어떤 사람들은 떠나가기를 기다리지 않고 스스로 줄입니다. 그리고 오히려 편안해집니다.
천팔백 년 전, 세상에서 가장 많은 사람을 상대했던 로마 황제 마르쿠스 아우렐리우스도 그랬습니다.
그의 일기 『명상록』과 심리학 연구로, 사람을 줄이는 사람들의 4가지 이유를 짚어 봅니다.

여러분에게 끝까지 남은 한 사람은 누구입니까. 어떤 사람인지 댓글로 들려주세요.

[목차]
""" + "\n".join(f"{mmss(t)} {n}" for t, n in ch) + """

[참고]
· 마르쿠스 아우렐리우스, 『명상록』 1권, 2권 1절, 4권 3절, 4권 24절, 5권 16절, 6권 48절
· 로라 카스텐슨(스탠퍼드대), 사회정서적 선택 이론
· 로빈 던바(옥스퍼드대), 던바의 수 5·15·50·150
· 하버드 성인발달연구(로버트 월딩거)

※ 사례 속 '영수 씨'는 여러 사람의 이야기를 모아 다시 꾸민 가상 인물입니다.
※ 영상 속 장면은 AI로 만든 이미지와 영상입니다.

#명상록 #인간관계 #마르쿠스아우렐리우스"""
tags = ['명상록', '마르쿠스 아우렐리우스', '인간관계', '나이 들수록', '사람을 줄이는 이유', '스토아 철학', '중년', '노후', '인생 조언', '철학', '황제의 일기', '던바의 수', '하버드 성인발달연구']
print(json.dumps({"title": "나이 들수록 사람을 줄이는 4가지 이유 | 명상록", "description": desc, "tags": tags}, ensure_ascii=False, indent=1))
