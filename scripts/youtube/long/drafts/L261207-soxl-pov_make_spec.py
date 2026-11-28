import json, os, re
# SOXL 2인칭 시점 편 (2026-11-27 대표 10:01~10:54) — 기획안: 프로젝트 문서 claude/youtube/drafts/P261207-soxl-pov-plan.md v4
# 구조: [훅] 시점 화면 15초 + 날짜 가림 떡밥 → 로고 → 1막 49일(시점 화면, 긴박) → 3분대 반전(2022년 공개) → 기존 톤 해설
#       → 다섯 계좌 결과 → 파는 전략(가볍게) → 그때와 지금 → 계기판 → 북엔드
# 화면: 시점·표·그래프는 drafts/L261207-soxl-pov_fx.html 로 미리 만든 8초 영상(pov_L261207_*.mp4). 렌더러는 영상을 8초까지만 풀어 왕복 재생하므로
#       영상 한 컷 = 내레이션 한 줄(7초 안쪽), 움직임은 앞 3초에 끝나고 뒤는 정지에 가깝게 만든다.
# 숫자: 야후 파이낸스 일별 시세(2026-11-27 조회). 반전 전에는 연도·달러 가격·실제 인물 이름을 말하지도 쓰지도 않는다.
# 원음: 1차 렌더에는 없음(이슈편 아님). 제롬 파월 2022 원음은 media/clip-queue.json 에 요청 → 도착하면 반전 장면에 넣는다.
HJ = os.environ.get('HJ', '/home/claude/haeja')
OUT = HJ + '/scripts/youtube/long/specs/L261207-soxl-pov.json'
CLIPS_OUT = HJ + '/scripts/youtube/long/drafts/L261207-soxl-pov_clips.json'
PRE = 'pov_L261207_fx_'
SRC0 = '야후 파이낸스 일별 시세'                                   # 반전 전: 연도를 드러내지 않는다
SRC = '야후 파이낸스 SOXL·SOXX·나스닥 일별 시세 2021-12~2026-11'
CL = {}

def c(name, **p):
    CL[PRE + name] = p; return PRE + name + '.mp4'

def S(cuts, lines, src='', note='', sketch=None, **kw):
    v = {"type": "media", "full": True, "wash": "none", "cuts": [{"lib": x} for x in cuts], "wash_amt": 0.85, "cine": False, "doc_cine": False}
    if len(cuts) > 1: assert len(cuts) == len(lines), (note, len(cuts), len(lines)); v["cut_by_line"] = True
    v.update(kw.pop('v', {}))
    d = {"v": v, "sketch_add": [], "asof": False, "src": src, "sketch": sketch or [], "lines": lines, "note": note}
    d.update(kw)
    fx = []   # 2026-11-28 대표 "카톡 올라갈 때 띵띵 — 효과음이 군데군데": 화면 움직임에 맞춰 자동으로 붙인다
    for i, x in enumerate(cuts):
        q = CL.get(x[:-4]); li = i if len(cuts) > 1 else 0
        if not q: continue
        k = q['k']; E = lambda at, kind: fx.append({"line": li, "at": round(at, 2), "k": kind})
        if k == 'lock':
            for n in q['notis']: E(n['t'], 'buzz'); E(n['t'] + .04, 'ping')
        elif k == 'chat':
            for j, m in enumerate(q['msgs']): E(.35 + j * q.get('gap', .75), 'pop' if m.get('me') else 'ping')
        elif k == 'acct':
            for h in q.get('hits', [.9, 1.7, 2.4]): E(h, 'thud')
        elif k == 'mon': E(q.get('bt', 1.0), 'alert')
        elif k == 'plunge': E(.3, 'thud')
        if q.get('heart'):
            tt = .2   # 하락이 깊어질수록 점점 빠르고 크게 (11/28 대표)
            for j in range(9): E(tt, 'heart' if j < 4 else 'heart2'); tt += max(.5, .95 - j * .07)
        elif k == 'choice' and not q.get('hi'):
            for j in range(4): E(.3 + j * .28, 'pop')
        elif k == 'table':
            fr = q.get('fresh', q.get('vis', list(range(len(q['rows'])))))
            for j in range(len(fr)): E(.25 + j * q.get('gap', .12), 'tick')
        elif k == 'gauge':
            if not q.get('still'):
                for j in range(len(q['sig'])): E(.3 + j * q.get('gap', .5), 'tick')
            if q.get('on'): E(q.get('ont', 1.4), 'ping')
        elif k == 'redact' and q.get('mode') == 'reveal':
            for j in (0, 1, 2, 3, 6, 7, 10, 11): E(1.0 + j * .22, 'tick')
            E(3.5, 'chime')
    if fx: d["sfx"] = fx
    return d

def SOT(clip, start, dur, lines, at, name, sub, src, note):   # 원음 + 한국어 자막(더빙 없음, orig_mode sot_test)
    return {"v": {"type": "media", "full": True, "wash": "none", "cuts": [{"lib": clip, "start": start}], "wash_amt": 0.85, "cine": True, "doc_cine": True, "news_scale": 0.66},
            "sketch_add": [], "asof": False, "src": src, "sketch": [{"kind": "lower", "text": name, "sub": sub, "line": 0, "at": 0.3}],
            "lines": lines, "note": note, "news": True, "sot": {"clip": clip, "start": start, "dur": dur, "rms": 0.085, "at": at}}

def CH(scene, chapter): scene["chapter"] = chapter; return scene

D1 = dict(day='1일째'); D19 = dict(day='19일째'); D27 = dict(day='27일째'); D49 = dict(day='49일째')
N = lambda t, col, i, app, ttl: dict(t=t, c=col, i=i, app=app, ttl=ttl)
BL, RD, YL = '#2f6bff', '#e0262b', '#f7c600'
T49 = [['아무것도 안 함', '-91%'], ['1일째 손절', '-64%'], ['한 번에 물타기', '-82%'], ['7번 나눠 사기', '-78%']]
T1Y = [['아무것도 안 함', '-79%'], ['손절', '-64%'], ['한 번에 물타기', '-57%'], ['나눠 사기', '-48%'], ['7달러에 기다리기', '-30%']]
T2Y = [['아무것도 안 함', '-54%'], ['손절', '-64%'], ['한 번에 물타기', '-8%'], ['나눠 사기', '+12%'], ['7달러에 기다리기', '+51%']]
TEX = [['2배에 전부 매도', '+111%', '약 3달 뒤'], ['2·3·5배에 나눠 매도', '+247%'], ['2024년 정점에 매도', '+880%'], ['계속 보유 · 2025년 4월', '+18%']]
LOW = [['9.21', 11.4], ['9.30', 8.86], ['10.12', 7.34], ['10.13 저가', 6.21, '$6.21', 'b'], ['10.13', 8.0], ['10.14', 6.93, '', 'b']]
HOLD = [['2022.10', 7, '$7'], ['2024.7', 68.59, '$68'], ['2025.4', 8.25, '$8', 'b'], ['2026.6', 300.77, '$300'], ['지금', 32.02, '$32', 'b']]
ROOM = '반도체 물린 사람들 (47)'
sc = []

# ───────── 훅 (첫 장 전) ─────────
sc.append(S(['il_L261207p_bed_phone.jpeg', c('lock', k='lock', wake=1, dow='토요일', time='6:42', clock='오전 6:42', **D1, notis=[
        N(.8, BL, '증', '증권', 'SOXL <b>-17.3%</b> 급락 마감'), N(1.4, RD, 'N', '뉴스', '[속보] 미 증시 일제히 급락'),
        N(2.0, YL, '톡', '김 과장', '야, 반도체 봤냐'), N(2.6, BL, '증', '증권', '보유 종목 <b>-78%</b> 손실 중')]),
     c('acct78', k='acct', label='수익률 · 고점에 매수', **{'from': -73.5}, to=-78.1, sub='오늘 하루 -17.3%', clock='오전 6:43', **D1)],
    ["아직 어두운 새벽, 머리맡에서 휴대폰이 연달아 울립니다.", "6시 42분. SOXL이 하루 만에 17% 떨어졌다는 알림입니다.",
     "계좌를 엽니다. 고점에 산 당신의 수익률은 마이너스 78%입니다."], SRC0, "[훅] 시점 화면 — 알림·계좌"))
sc.append(S([c('cal', k='big', pre='다음 금리 결정까지', l1='앞으로', l2='[26일]', s2=120, clock='오전 6:44', **D1),
     c('question', k='big', l1='당신이라면', l2='[오늘], 어떻게 하시겠습니까?', s2=70, clock='오전 6:45', **D1)],
    ["26일 뒤에는 금리 결정이 기다리고 있습니다.", "당신이라면 오늘, 어떻게 하시겠습니까?"], SRC0, "[훅] 질문"))
# 2026-11-28 대표: 날짜는 화면 구석에 자연스럽게 가려만 두고 말하지 않는다 → 3분 뒤 공개
sc.append(S([c('choice0', k='choice', q='이 영상이 끝날 때쯤', recon=1)],
    ["이 영상이 끝날 때쯤, 손절과 물타기, 그리고 기다리기 중 무엇이 어떤 결과였는지 숫자로 확인하시게 됩니다."], '', "[훅] [약속]"))
sc.append({"v": {"type": "media", "full": True, "wash": "none", "cuts": [{"lib": "il_L261116p_wallst_red.png"}], "wash_amt": 0.85, "cine": True, "ident": True},
           "lines": ["현명한 투자를 위한 경제 채널, 밸류노트 지금 시작합니다."], "sketch_add": [], "asof": False, "src": "", "sketch": [], "dur": 6.0, "note": "[로고 인트로] 시그니처"})

# ───────── 1막: 49일 (시점 화면) ─────────
sc.append(CH(S(['il_L261207p_desk_night2.jpeg', c('speech', k='mon', head='연준 의장<br>단 8분 연설', tick='나스닥 -3.9% · 반도체 지수 상품 -5.7%', **{'from': -73.5}, to=-78.1, clock='밤 11:00', **D1),
     c('pain', k='mon', head='"가계와 기업에<br>고통 따를 것"', hs=34, tick='물가 안정이 최우선 · 금리 인상 지속 시사', **{'from': -75.0}, to=-78.1, bt=.6, clock='밤 11:08', **D1)],
    ["1일째 밤. 당신은 책상 앞에 앉아 있습니다.", "미국 중앙은행 의장이 단 8분 동안 연설합니다.", "물가를 잡기 위해 가계와 기업의 고통을 감수하겠다는 내용입니다."], SRC0, "[1일째] 연설 속보"), "1일째"))
sc.append(S([c('drop17', k='acct', label='오늘 하루', **{'from': -3.0}, to=-17.3, ref='어제 종가', clock='오전 6:42', **D1),
     c('quarter', k='acct', label='고점 대비', **{'from': -73.5}, to=-78.1, sub='남은 돈은 22%', ref='고점', clock='오전 6:43', **D1)],
    ["반도체 3배 상품은 그날 하루에만 17% 빠집니다.", "고점 대비로는 마이너스 78%. 계좌에는 이미 4분의 1도 남지 않았습니다."], SRC0, "[1일째] 계좌"))
sc.append(S([c('choice1', k='choice', **D1), c('choice2', k='choice', hi=[0, 1], **D1), c('choice3', k='choice', hi=[2, 3], **D1)],
    ["여기서 당신이 고를 수 있는 길은 네 가지입니다.", "지금이라도 손절한다. 아니면 가진 돈을 한 번에 넣어 물을 탄다.",
     "여러 번에 나눠서 산다. 아니면 더 떨어질 때까지 현금을 들고 기다린다."], '', "[1일째] 선택 버튼 넷"))
sc.append(S([c('chat1', k='chat', title=ROOM, msgs=[dict(who='박 대리', text='여기가 바닥입니다. 저는 더 삽니다'), dict(who='이 차장', text='반도체는 끝났어요. 저는 정리합니다'), dict(me=1, text='…')], **D1),
     c('tease49', k='big', pre='네 가지 선택의 결과', l1='공개는', l2='[49일째]에', **D1)],
    ["단체 대화방은 둘로 갈립니다. 지금이 바닥이라는 사람, 반도체는 끝났다는 사람.", "결과는 49일째에 공개하겠습니다. 누가 맞았을까요?"], SRC0, "[1일째] 대화방 + [R1]"))

sc.append(S(['il_L261207p_pov_elevator.jpeg', c('bounce', k='big', pre='일주일 사이', l1='15일째', l2='[+14%] 반등', col='', day='15일째'),
     c('chat_b', k='chat', title=ROOM, msgs=[dict(who='박 대리', text='보셨죠? 바닥 맞다니까요'), dict(who='최 과장', text='저도 오늘 더 샀습니다'), dict(me=1, text='이제 끝난 건가…')], day='15일째')],
    ["15일째 아침. 출근길 엘리베이터에서 당신은 또 계좌를 엽니다.", "가격이 일주일 사이 14% 올랐습니다.", "대화방에는 드디어 끝났다는 말이 돌기 시작합니다. 정말 끝난 걸까요?"], SRC0, "[15일째] 속임수 반등"))
sc.append(CH(S(['il_L261207p_subway_phone2.jpeg', c('cpi', k='mon', head='미 물가,<br>예상보다 높았다', tick='나스닥 -5.2% · 반도체 지수 상품 -6.2%', **{'from': -79.8}, to=-83.4, clock='밤 9:30', **D19),
     c('drop18', k='acct', label='오늘 하루', **{'from': -4.0}, to=-18.2, sub='나스닥 -5.2%', ref='어제 종가', clock='오전 6:40', **D19)],
    ["19일째 밤. 퇴근길 지하철에서 속보가 뜹니다.", "이번에는 물가 지표가 예상보다 높게 나왔습니다.", "나스닥이 하루에 5% 넘게 빠지고, SOXL은 18% 떨어집니다."], SRC0, "[19일째] 물가 충격"), "19일째"))
sc.append(S([c('lump24', k='acct', label='1일째에 물탄 돈', **{'from': -8.0}, to=-24.3, ref='물탄 가격', sub='19일 만의 손실', clock='오전 6:41', **D19),
     c('regret', k='chat', title=ROOM, msgs=[dict(who='박 대리', text='물을 너무 일찍 탔습니다…'), dict(who='최 과장', text='저도요. 남은 돈이 없습니다'), dict(me=1, text='저도 1일째에 다 넣었습니다')], **D19)],
    ["1일째에 한 번에 물을 탄 사람은 19일 만에 그 돈의 24%를 잃었습니다.", "물을 너무 일찍 탔다는 후회가 시작됩니다."], SRC0, "[19일째] 물탄 돈"))

sc.append(CH(S(['il_L261207p_livingroom_3am2.jpeg', c('rate', k='mon', head='연준, 기준금리<br>0.75%p 인상', tick='세 번 연속 0.75%p 인상 · 나스닥 -1.8%', **{'from': -84.0}, to=-84.4, clock='새벽 3:00', **D27),
     c('dd84', k='acct', label='고점 대비', **{'from': -83.4}, to=-84.4, sub='금리 인상 세 번째', ref='고점', hits=[1.0], clock='새벽 3:02', **D27)],
    ["27일째 새벽 3시. 잠이 오지 않아 거실로 나옵니다.", "금리가 0.75%포인트 오릅니다. 세 번 연속입니다.", "고점 대비 손실은 84%까지 커졌습니다."], SRC0, "[27일째] 금리 인상"), "27일째"))
sc.append(S([c('chat2', k='chat', title=ROOM, msgs=[dict(who='이 차장', text='손절했습니다. 다들 건승하세요'), dict(who='최 과장', text='저는 또 물 탔습니다. 이게 마지막 돈입니다'), dict(who='박 대리', text='…')], **D27),
     c('worst', k='big', l1='그런데', l2='가장 무서운 날은 [아직]', s2=72, **D27)],
    ["바닥이라던 사람들이 조용해집니다. 손절했다는 글, 마지막 돈까지 물을 탔다는 글이 올라옵니다.", "그런데 가장 무서운 날은 아직 오지 않았습니다."], '', "[27일째] 대화방 + [R2]"))

sc.append(CH(S(['il_L261207p_monitor_hands2.jpeg', c('dawn', k='lock', dow='목요일', time='9:31', clock='밤 9:31', **D49, notis=[
        N(.7, RD, 'N', '뉴스', '[속보] 미 물가 또 예상 상회'), N(1.3, BL, '증', '증권', '나스닥 선물 <b>급락</b>'), N(1.9, BL, '증', '증권', 'SOXL 개장가 <b>-12.5%</b>')]),
     c('plunge', k='plunge', heart=1, cap='49일째 · 개장 직후 · 고점 대비', **{'from': -89.9}, to=-91.5, clock='밤 10:30', **D49)],
    ["49일째 밤. 당신은 다시 모니터 앞에 앉았습니다.", "물가가 또 예상을 넘었습니다.", "한 시간 뒤 장이 열리자, 가격이 수직으로 떨어집니다."], SRC0, "[49일째] 개장 급락"), "49일째"))
sc.append(S(['il_L261207p_pov_grip.jpeg', c('dd91', k='acct', heart=1, label='고점 대비', **{'from': -89.9}, to=-91.5, sub='1억 원 → 850만 원', ref='고점', clock='밤 10:34', **D49),
     c('delist', k='chat', title=ROOM, msgs=[dict(who='최 과장', text='물 타고 싶어도 이제 돈이 없습니다'), dict(who='박 대리', text='이러다 상품이 없어지는 것 아닙니까'), dict(me=1, text='지금이라도 팔아야 합니까')], **D49)],
    ["휴대폰을 쥔 손에 힘이 들어갑니다.", "고점 대비 마이너스 91%. 1억 원을 넣었다면 850만 원이 남는 숫자입니다.", "물을 타고 싶어도 돈이 없다는 말, 상품이 없어지는 것 아니냐는 말까지 나옵니다."], SRC0, "[49일째] 바닥"))
sc.append(S([c('rebound', k='plunge', v=1, cap='49일째 · 하루 등락', **{'from': -12.5}, low=-15.4, to=9.0, clock='새벽 5:00', **D49),
     c('next13', k='acct', label='다음 날 하루', **{'from': 0.0}, to=-13.4, sub='사야 합니까, 팔아야 합니까', ref='어제 종가', clock='오전 6:40', day='50일째')],
    ["그런데 그날, 장중에 갑자기 방향이 바뀝니다. 종가는 오히려 9% 올랐습니다.", "그리고 다음 날 다시 13% 떨어집니다. 지금 사야 합니까, 팔아야 합니까?"], SRC0, "[49일째] 반등과 재하락"))

# ───────── 반전 ─────────
sc.append(CH(S([c('reveal0', k='redact', mode='hide', pre='화면 구석의 가려진 날짜', post='', recon=1), c('reveal', k='redact', mode='reveal', pre='49일째, 오늘은', post='4년 전의 실제 기록입니다', recon=1)],
    ["그런데 화면 구석에 가려져 있던 날짜, 눈치채셨습니까?", "49일째인 오늘은, 2022년 10월 13일입니다."], SRC, "[반전] [떡밥 회수] [콜백] 날짜 공개"), "날짜 공개"))
sc.append(S([c('record', k='tline', title='49일의 정체', items=[[0, '2022.8.26', '1일째'], [.37, '9.13', '19일째'], [.55, '9.21', '27일째'], [1, '10.13', '49일째']], hi=[0, 3]),
     c('powell', k='big', style='vn', pre='1일째의 연설', l1='제롬 파월 연준 의장', l2='잭슨홀 · [2022년 8월 26일]', s2=60),
     ],
    ["지금까지 보신 49일은 2022년 8월 26일부터 10월 13일까지, 4년 전의 실제 기록입니다.", "1일째의 8분 연설은 제롬 파월 연준 의장의 잭슨홀 연설이었습니다. 그날의 실제 목소리입니다."], SRC + ' · 연준 잭슨홀 연설 2022-08-26', "[반전] 기록의 정체"))
PSRC = '캔자스시티 연준 잭슨홀 심포지엄 2022-08-26(미국) · 제롬 파월 의장 개막 연설'
sc.append(SOT('pov_powell_jh22_short.mp4', 2.6, 7.6, ["오늘 제 발언은 더 짧고, 초점은 더 좁고, 메시지는 더 직접적일 겁니다."], [[0.1, 7.4]],
    '제롬 파월', '미국 연준 의장 · 잭슨홀 2022.8.26', PSRC, "[반전] 원음① 파월 — 짧고 직접적으로"))
sc.append(SOT('pov_powell_jh22_pain.mp4', 2.6, 19.6, ["금리가 오르고 성장이 느려지고 고용이 약해지면, 물가는 내려갈 겁니다.", "하지만 가계와 기업에는 고통도 따를 겁니다.",
     "이것은 물가를 낮추는 데 따르는 안타까운 비용입니다. 그러나 물가 안정에 실패하면 훨씬 더 큰 고통이 옵니다."], [[0.1, 7.1], [7.1, 11.4], [11.4, 19.4]],
    '제롬 파월', '미국 연준 의장 · 잭슨홀 2022.8.26', PSRC, "[반전] 원음② 파월 — 가계와 기업에 고통"))
sc.append(S([c('cpi22', k='big', style='vn', pre='49일째 밤의 속보', l1='미국 소비자물가', l2='[2022년 9월]분 발표', s2=64)],
    ["그리고 49일째 밤의 속보는 2022년 9월 미국 소비자물가 발표였습니다."], SRC + ' · 미국 노동통계국 2022-10-13', "[반전] 49일째 속보의 정체"))
sc.append(S([c('hikes', k='bars', title='2022년 미국 금리 인상', sub='한 번에 0.75%p씩 네 번 연속', items=[['6월', 75, '0.75%p'], ['7월', 75, '0.75%p'], ['9월', 75, '0.75%p'], ['11월', 75, '0.75%p']], hi=[2])],
    ["그해 미국 중앙은행은 물가를 잡기 위해 금리를 0.75%포인트씩 네 번 연속 올렸습니다. 27일째의 인상은 그 세 번째였습니다."], SRC + ' · 연준 FOMC 2022', "[반전] 2022년 금리"))
# 11/28 대표: 가만히 있는 진행자 컷은 어색 → 시점 편에서는 뺀다(문구 화면으로)
sc.append(S([c('nopred', k='big', style='vn', l1='이 영상은', l2='앞으로를 [예측하지 않습니다]', s2=66), c('facts', k='big', style='vn', l1='같은 상황, 각각의 선택', l2='[있었던 숫자]만 봅니다', s2=76)],
    ["왜 과거의 기록을 지금 일처럼 보여 드렸을까요? 이 영상은 앞으로를 예측하지 않습니다.", "같은 상황에서 각각의 선택이 실제로 어떤 결과를 냈는지, 있었던 숫자만 보여 드리겠습니다."], '', "[반전] 진행자 — 톤 전환"))

# ───────── 2막: 선택의 결과 (2026-11-28 대표: 2022년 대응은 요약 — 표는 말하는 줄만 하나씩) ─────────
SET = [['고점에서 산 주식', '100주', '2021.12.27'], ['1일째에 더 가진 돈', '평가액과 같은 금액']]
sc.append(CH(S([c('setup1', k='table', plain=1, title='계산 조건', rows=SET, vis=[0]), c('setup1b', k='table', plain=1, title='계산 조건', rows=SET, vis=[0, 1], fresh=[1], hi=[1])],
    ["계산 조건입니다. 고점에서 100주를 산 사람이 있습니다.", "이 사람이 1일째에, 남은 평가액만큼의 돈을 더 갖고 있다고 가정했습니다."], SRC, "[결과] 계산 조건"), "선택의 결과"))
sc.append(S([c('t49_a', k='table', title='49일째', sub='2022.10.13', rows=T49, vis=[0], hi=[0]), c('t49_b', k='table', title='49일째', sub='2022.10.13', rows=T49, vis=[0, 1], fresh=[1], hi=[1]),
     c('t49_c', k='table', title='49일째', sub='2022.10.13', rows=T49, fresh=[2, 3], gap=1.6, hi=[2, 3])],
    ["49일째입니다. 아무것도 하지 않은 계좌는 마이너스 91%였습니다.", "1일째에 손절한 계좌는 마이너스 64%에서 멈췄습니다.",
     "한 번에 물을 탄 계좌는 마이너스 82%, 7번 나눠 산 계좌는 마이너스 78%였습니다."], SRC, "[결과] 49일째 표"))
sc.append(S([c('wait7', k='path', title='7달러 매수 주문', sub='7달러 이하 거래는 2일', pts=LOW, line=[7, '7달러'], hi=[3]),
     c('wait6', k='path', title='6달러 매수 주문', sub='한 번도 체결되지 않음', pts=LOW, line=[6, '6달러'], hi=[3])],
    ["현금을 들고 7달러를 기다린 사람은 샀습니다. 7달러 아래로 거래된 날은 단 2일이었습니다.",
     "6달러를 기다린 사람은 끝내 사지 못했습니다. 최저가는 6달러 21센트였습니다."], SRC, "[결과] 기다린 사람 + [R3]"))
sc.append(S([c('y1_b', k='table', title='1년 뒤', sub='2023.10.13 · 18.98달러', rows=T1Y, gap=.5, hi=[4])],
    ["1년 뒤에도 다섯 계좌는 모두 손실이었습니다. 7달러에 산 계좌가 마이너스 30%로 가장 나았습니다."], SRC, "[결과] 1년 뒤"))
sc.append(S([c('y2_a', k='path', title='2년 뒤', sub='2024.10.14', pts=[['2022.10', 6.93], ['2023.10', 18.98], ['2024.7', 68.59], ['2024.10', 40.82]], hi=[3]),
     c('y2_b', k='table', title='2년 뒤', sub='2024.10.14 · 40.82달러', rows=T2Y, vis=[3, 4], fresh=[4, 3], gap=1.8, hi=[3, 4]),
     c('y2_c', k='table', title='2년 뒤', sub='2024.10.14 · 40.82달러', rows=T2Y, vis=[1, 2, 3, 4], fresh=[2, 1], gap=1.8, hi=[1, 2]),
     c('y2_d', k='table', title='2년 뒤', sub='2024.10.14 · 40.82달러', rows=T2Y, fresh=[0], hi=[0])],
    ["2년 뒤, 가격은 40달러를 넘습니다. 여기서 순서가 뒤집힙니다.", "7달러에 산 계좌는 플러스 51%, 나눠 산 계좌는 플러스 12%로 돌아섭니다.",
     "한 번에 물을 탄 계좌는 마이너스 8%, 손절한 계좌는 여전히 마이너스 64%입니다.", "아무것도 하지 않은 계좌는 2년이 지나도 마이너스 54%였습니다."], SRC, "[결과] 2년 뒤"))
sc.append(S([c('gpt1', k='tline', title='저점 48일 뒤', items=[[0, '2022.10.13', '장중 저점'], [1, '2022.11.30', '챗GPT 공개']], hi=[1], note='48일')],
    ["가격을 되돌린 것은 저점 48일 뒤에 공개된 챗GPT였습니다. 그 밤에는 누구도 몰랐던 변수입니다."], SRC + ' · 오픈AI 2022-11-30', "[결과] 챗GPT"))
TEX3 = TEX[:3]
sc.append(S([c('exit_1', k='table', title='7달러에 산 뒤', sub='언제 팔았나', rows=TEX3, vis=[0], hi=[0]), c('exit_2', k='table', title='7달러에 산 뒤', sub='언제 팔았나', rows=TEX3, vis=[0, 1], fresh=[1], hi=[1]),
     c('exit_3', k='table', title='7달러에 산 뒤', sub='언제 팔았나', rows=TEX3, fresh=[2], hi=[2]),
     c('hold_b', k='bars', title='팔지 않고 계속 보유했다면', items=[['2024년 7월', 880, '+880%'], ['2025년 4월', 18, '+18%']], hi=[1], gap=1.6)],
    ["파는 방법도 결과를 갈랐습니다. 7달러에 산 사람이 2배에 전부 팔았다면 111%였습니다.", "2배, 3배, 5배에 3분의 1씩 나눠 팔았다면 247%입니다.",
     "2024년 7월 정점에 전부 팔았다면 880%입니다.", "팔지 않고 들고 있었다면, 880%는 2025년 4월에 18%로 줄었습니다."], SRC, "[매도] 파는 방법별 수익률(요약)"))

# ───────── 3막: 그때와 지금 (요약) ─────────
REC = [['SOXL · 3배', 4.3, '4.3년'], ['반도체 지수 상품 · 1배', 2.0, '약 2년']]
sc.append(CH(S([c('rec_a', k='bars', title='원금 회복까지', sub='2021년 12월 고점 기준', items=REC, vis=[0], hi=[0]), c('rec_b', k='bars', title='원금 회복까지', sub='2021년 12월 고점 기준', items=REC, fresh=[1], hi=[1])],
    ["아무것도 하지 않은 계좌가 원금을 되찾기까지는 4년 넘게 걸렸습니다.", "같은 지수를 1배로 따라간 상품은 약 2년이었습니다."], SRC, "[지금] [콜백] 회복 기간"), "그때와 지금"))
sc.append(S([c('x10_a', k='bars', title='원금으로 돌아오려면', items=[['46% 빠진 지수', 1.9, '1.9배'], ['90% 빠진 3배 상품', 10.5, '10배 이상']], hi=[1], gap=1.8)],
    ["지수는 46% 빠져서 2배 가까이 오르면 됐지만, 90% 빠진 3배 상품은 10배 넘게 올라야 했습니다."], SRC, "[지금] 10배"))
sc.append(S([c('y2000_a', k='bars', title='고점 회복까지', sub='필라델피아 반도체 지수', items=[['2000년 고점', 17, '17년'], ['2021년 고점', 2, '약 2년']], hi=[0], gap=1.8),
     c('y2000_b', k='big', style='vn', l1='2년 만의 회복은', l2='[당연한 일]이 아니다')],
    ["2000년 닷컴 버블 고점의 반도체 지수는, 그 가격을 되찾는 데 17년이 걸렸습니다.", "2022년처럼 2년 만에 돌아온 것이 당연한 일은 아니라는 뜻입니다."], SRC + ' · 블룸버그 2017-11-21', "[지금] 2000년 반례"))
sc.append(S([c('now_a', k='path', title='SOXL, 지금', sub='2026.6.22 → 11.25', pts=[['2026.6', 300.77, '$300'], ['2026.11', 32.02, '$32', 'b']], hi=[1]),
     c('now_b', k='bars', title='고점 대비 하락 폭', items=[['2022년', 90.5, '-90.5%'], ['2026년 지금', 89.4, '-89%']], hi=[1], gap=1.2)],
    ["그리고 지금입니다. SOXL은 6월 고점 300달러에서 32달러로, 89% 떨어졌습니다.", "2022년의 90%와 거의 같은 깊이입니다."], SRC, "[지금] 같은 깊이"))
sc.append(S([c('same', k='big', style='vn', l1='같은 점', l2='[금리]가 오르는 시기'), c('diff', k='big', style='vn', l1='다른 점', l2='재고 과잉 → [AI 과열 우려]', s2=58), c('unk', k='big', style='vn', l1='이번의 변수는', l2='[아무도 모른다]')],
    ["같은 점은 금리입니다. 그때도 지금도 금리가 오르는 시기입니다.", "다른 점은 원인입니다. 그때는 반도체 재고, 지금은 AI 투자 과열 우려입니다.",
     "그때의 챗GPT 같은 변수가 이번에도 나타날지는 누구도 알 수 없습니다."], SRC, "[지금] 같은 점·다른 점"))
sc.append(S([c('ref', k='big', style='vn', l1='이 기록은 정답이 아니라', l2='[참고 자료]'), c('what', k='big', style='vn', l1='그러면 지금은', l2='[무엇을 보고] 움직일까', s2=76)],
    ["그래서 이 기록은 정답이 아니라 참고 자료입니다.", "그러면 지금은 무엇을 보고 움직여야 할까요?"], '', "[가짜 결말] [지금] 참고 자료 + [R4]"))

# ───────── 4막: 바닥 신호 (2026-11-28 대표: 신호 소개 → 과거 저점 때 켜진 개수 → 나눠 사고 나눠 판 결과 → 계기판 보는 법) ─────────
GSRC = '밸류노트 반도체 바닥 계기판 과거 대입 2026-11-24 · 계기판 2026-11-27'
SIG = [['실적', '악재에도<br>안 빠질 때'], ['가격', '예상 PER<br>12배 이하'], ['기간', '고점 뒤<br>253일'], ['공포', '공포 지수<br>30 넘긴 뒤 진정'], ['금리', '10년물 금리<br>정점 뒤 하락']]
BT = [['2011년 저점', '1개'], ['2016년 저점', '2개'], ['2018년 저점', '1개'], ['2022년 저점', '1개']]
sc.append(CH(S([c('g_intro', k='gauge', title='반도체 바닥 신호', sub='5가지 · 매일 자동 갱신', sig=SIG, gap=.55),
     c('g_intro2', k='gauge', title='반도체 바닥 신호', sub='5가지 · 매일 자동 갱신', sig=SIG, still=1, scan=1)],
    ["밸류노트는 반도체 바닥 신호 다섯 가지를 매일 확인합니다.", "실적, 가격, 기간, 공포, 금리입니다. 조건이 맞으면 하나씩 켜집니다."], GSRC, "[신호] 계기판 소개"), "바닥 신호"))
sc.append(S([c('bt_a', k='table', plain=1, title='저점 당일 켜진 신호', sub='5개 중', rows=BT, gap=1.0),
     c('bt_b', k='big', style='vn', l1='다섯 개가 다 켜진 적은', l2='[한 번도 없었다]'),
     c('bt_c', k='table', title='저점 1년 뒤 반도체 지수', sub='필라델피아 반도체 지수', rows=[['2011년 저점', '+23%'], ['2016년 저점', '+72%'], ['2018년 저점', '+74%'], ['2022년 저점', '+62%']], gap=.8)],
    ["지난 네 번의 반도체 저점에서, 저점 당일 켜진 신호는 1개 아니면 2개였습니다.", "다섯 개가 다 켜진 적은 없었습니다. 가장 많을 때가 4개였고, 저점이 지난 뒤였습니다.",
     "그리고 네 번 모두, 저점 1년 뒤 반도체 지수는 23%에서 74% 올라 있었습니다."], GSRC, "[신호] 과거 저점 4번"))
sc.append(S([c('late', k='big', style='vn', l1='신호가 다 켜지길 기다리면', l2='바닥은 [이미 지나간다]', s2=72), c('split', k='big', style='vn', l1='한 번에 맞히지 않고', l2='신호마다 [나눠서] 산다', s2=76)],
    ["신호가 다 켜지기를 기다리면, 바닥은 이미 지나가 있습니다.", "그래서 한 번에 맞히려 하지 않고, 신호가 켜질 때마다 나눠서 사는 방법이 있습니다."], GSRC, "[신호] 그래서 나눠 산다"))
sc.append(S([c('sp_a', k='bars', title='본전 가격', sub='2022년 · 49일간 7번 나눠 사기', items=[['아무것도 안 함', 73, '73달러'], ['7번 나눠 사기', 36.5, '36달러']], hi=[1], gap=2.2),
     c('sp_b', k='bars', title='원금을 되찾은 때', sub='2021년 12월 고점 기준', items=[['아무것도 안 함', 4.3, '2026년 4월'], ['7번 나눠 사기', 2.4, '2024년']], hi=[1], gap=1.8)],
    ["2022년에 49일 동안 7번 나눠 산 계좌는, 본전 가격이 73달러에서 36달러로 내려왔습니다.", "이 계좌는 2024년에 원금을 되찾았습니다. 아무것도 안 한 계좌보다 약 2년 빨랐습니다."], SRC, "[신호] 나눠 산 계좌 — 본전 가격"))
SX = [['2·3·5배에 나눠 매도', '+233%'], ['계속 보유 · 2025년 4월', '-26%']]
sc.append(S([c('sx_a', k='table', title='나눠 산 돈의 결과', sub='평균 11달러 매수', rows=SX, vis=[0], hi=[0]), c('sx_b', k='table', title='나눠 산 돈의 결과', sub='평균 11달러 매수', rows=SX, fresh=[1], hi=[1]),
     c('sx_c', k='big', style='vn', pre='2022년 · 나눠 사고 나눠 판 결과', l1='대략 이 범위', l2='[-26% ~ +233%]', s2=96), c('sx_d', k='big', style='vn', l1='2022년의 숫자', l2='이번에도 [같다는 뜻은 아니다]', s2=60)],
    ["나눠 산 돈을 2배, 3배, 5배에 3분의 1씩 팔았다면, 그 돈의 수익률은 약 230%였습니다.", "팔지 않고 들고 있었다면, 2025년 4월에는 다시 마이너스 26%였습니다.",
     "나눠 사고 나눠 판 결과는 대략 이 범위 안에 있었습니다.", "물론 2022년의 숫자입니다. 이번에도 같다는 뜻은 아닙니다."], SRC + ' · 평균 매수가 11.13달러의 2·3·5배 도달 기준', "[신호] 나눠 판 결과의 범위"))
sc.append(CH(S([c('g_now', k='gauge', title='반도체 바닥 신호, 지금', sub='11월 27일 기준', sig=SIG, still=1, on=[3], ont=1.2, foot='5개 중 [1개] 켜짐'),
     c('g_now2', k='gauge', title='반도체 바닥 신호, 지금', sub='11월 27일 기준', sig=SIG, still=1, on=[3], ont=0, foot='5개 중 [1개] 켜짐')],
    ["지금 계기판은 다섯 개 중 1개가 켜져 있습니다. 공포 신호입니다.", "치솟았던 공포 지수가 가라앉으면 켜지는 신호입니다. 나머지 넷은 아직 꺼져 있습니다."], GSRC, "[마무리] 계기판 지금"), "마무리"))
sc.append(S(['app_semi_L261207.mp4'],
    ["반도체 계기판은 이렇게 보시면 됩니다. 신호가 바뀔 때 알림을 받고 싶은 분은 설명란의 링크를 확인해 주세요."], '', "[마무리] 계기판 보는 법 + 안내 1회"))
sc.append(S(['il_L261207p_pov_window.jpeg', c('today', k='lock', dow='', dtext='오늘', time='6:42', day='오늘', today=1, notis=[N(.8, BL, '증', '증권', 'SOXL 고점 대비 <b>-89%</b>'), N(1.6, YL, '톡', '김 과장', '야, 반도체 봤냐')]),
     c('q2', k='big', l1='다시, 처음의 질문', l2='당신이라면 [오늘]?', day='오늘', today=1)],
    ["이제 2022년이 아니라, 오늘입니다.", "새벽 6시 42분. 휴대폰이 다시 울립니다.", "당신이라면 오늘, 어떻게 하시겠습니까?"], SRC, "[북엔드] 다시 1인칭 화면 — 첫 질문으로"))
sc.append(S([c('ask', k='big', style='vn', l1='여러분의 선택은?', l2='[댓글]로 남겨 주세요')],
    ["그날 여러분이라면 네 가지 중 무엇을 고르셨을지, 댓글로 남겨 주세요."], '', "[마무리] 질문"))
sc.append(S(['il_L261124g_fed_stone_dawn.jpeg'], ["여러분의 구독, 좋아요, 댓글은 영상 제작에 큰 힘이 됩니다."], '', "[마무리] 구독", v={"cine": True, "doc_cine": True}))
sc.append({"v": {"type": "end", "sub": "", "btn_at": ["0:거시적", "0:거시적", "0:거시적"], "note": {"text": ""}, "dark_end": True, "end_v2": True,
                 "slogan": ["시장의 흐름 뒤", "숨은 이야기를 읽는 채널", "거시적 관점으로 시장을 이해하면, 투자가 달라집니다"]},
           "lines": ["거시적 관점으로 시장을 이해하면, 투자가 달라집니다. 감사합니다. 밸류노트였습니다."],
           "sketch_add": [], "asof": False, "src": "", "note": "[북엔드] 끝 화면"})

base = json.load(open(HJ + '/scripts/youtube/long/specs/L261126-son.json', encoding='utf-8'))
spec = {k: base[k] for k in ['format', 'world', 'notebook', 'overlay', 'look', 'roadmap', 'hook', 'music', 'design', 'synthetic_media'] if k in base}
spec.update({
 "id": "L261207-soxl-pov", "company": "SOXL", "no_data": True, "series": "SOXL", "plan": "P261207-soxl-pov",
 "scheduled_at": "2026-12-07T12:30:00+09:00", "manual": True,
 "opening": "새벽 알림 → 계좌 -78% → 금리 결정 26일 전 → 당신이라면 오늘? (날짜는 구석에 가려만 둠)",
 "hook_type": "시점 화면(2인칭)",
 "endscreen_target": "L261123-soxl-3", "endscreen_also": "L261126-son",
 "title": "SOXL -89%, 당신이라면 오늘 어떻게 하시겠습니까? | 49일의 기록",
 "doc_title": "SOXL 49일의 기록",
 "title_en": "SOXL is down 89%. What would you do today? A 49-day record through your own eyes",
 "description_head": "SOXL이 고점 대비 89% 떨어졌습니다. 손절, 한 번에 물타기, 나눠 사기, 현금 들고 기다리기. 같은 상황에서 네 가지 선택이 실제로 어떤 결과를 냈는지 49일의 기록으로 따라가 봅니다.\n이 영상은 예측하지 않습니다. 있었던 숫자만 보여 드립니다.\n\n📟 반도체 바닥 신호(매일 자동 갱신) 👉 valuenote.co.kr/semi",
 "description_en": "SOXL has fallen 89% from its peak. We follow a real 49-day stretch through an investor's own screens and compare what four choices (cut losses, buy all at once, buy in steps, wait in cash) actually led to, plus how different exits played out. No forecasts, only recorded numbers. Not investment advice. Account, news and chat screens are reconstructions.",
 "pinned_comment": "49일의 기록, 어떠셨나요. 그날 여러분은 넷 중 무엇을 고르셨을지 댓글로 남겨 주세요.\n📟 반도체 바닥 신호(매일 자동 갱신) 👉 valuenote.co.kr/semi\n\n※ 계좌·뉴스·대화방 화면은 재구성 화면입니다. 숫자는 야후 파이낸스 일별 시세 기준(2026년 11월 25일 종가까지). 매수·매도 권유가 아닙니다.",
 "hook_promises": ["네 가지 선택의 실제 결과", "파는 방법에 따른 수익률", "바닥 신호 보는 법"],
 "viewer_question": "SOXL -89%, 지금 손절·물타기·기다리기 중 무엇을 해야 하나",
 "tags": ["SOXL", "SOXL 주가", "SOXL 전망", "SOXL 물타기", "반도체", "레버리지 ETF", "금리 인상", "엔비디아", "삼성전자", "SK하이닉스", "TQQQ"],
 "search_keywords": ["SOXL 주가 전망", "SOXL 물타기", "SOXL 손절", "반도체 바닥", "레버리지 ETF"],
 "sources": ["밸류노트 반도체 바닥 계기판(2026-11-25) · 과거 대입(2026-11-24)", "야후 파이낸스 SOXL·SOXX·나스닥 일별 시세(2026-11-27 조회)", "캔자스시티 연준 잭슨홀 심포지엄 영상 2022-08-26", "연준 FOMC 2022-09-21", "오픈AI 2022-11-30", "블룸버그 2017-11-21"],
 "format_note": "v1 2026-11-27 대표 — 2인칭 시점 화면(니치 벤딩 1호), 초반 반전 암시, 3분대 반전 뒤 기존 톤, 파는 전략은 가볍게. 시점·표·그래프는 미리 만든 영상(pov_L261207_*). 파월 잭슨홀 2022 원음 2개 · 실사 6장 · 계기판 2022년 대입",
 "orig_mode": "sot_test", "orig_mode_note": "원음+한국어 자막(더빙 없음). 구간은 받아쓰기로 확정(30.6~38.2초, 94.6~114.2초).",
 "voice_speed": base.get("voice_speed", 1.03), "photo_lift": 1.25,
 "thumb": {"photo": "il_base_trader_red.jpeg", "focus_x": 0.5, "l1": "SOXL -89%", "l2": "오늘, 당신의 선택은?", "pos": "left"},
 "scenes": sc,
})
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(spec, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(CL, open(CLIPS_OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
used = sorted(set(re.findall(r'"(' + PRE + r'[^"]+)\.mp4"', json.dumps(sc, ensure_ascii=False))))
assert set(used) == set(CL), (set(used) ^ set(CL))
longl = [(round(len(re.sub(r'[^가-힣0-9A-Za-z]', '', l)) / 6.1 + .35, 1), l[:26]) for s in sc if len(s['v'].get('cuts', [])) > 1 or any(str(x.get('lib', '')).startswith(PRE) for x in s['v'].get('cuts', [])) for l in s['lines']]
print('7.6초 넘는 줄:', [x for x in longl if x[0] > 7.6])
narr = sum(len(re.sub(r'[^가-힣0-9A-Za-z]', '', l)) for s in sc for l in s['lines'])
nl = sum(len(s['lines']) for s in sc)
print('scenes', len(sc), 'clips', len(CL), 'lines', nl, 'est_sec', round(narr / 6.1 + .35 * nl), 'min', round((narr / 6.1 + .35 * nl) / 60, 2))
