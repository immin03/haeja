# 황제의 일기 쇼츠 템플릿 (2026-11-02 확정)

## 구성 (약 28~31초)
1. 훅 화면: 작은 금색 한 줄 + 큰 훅 2줄(함렛 600, 좌측 정렬), 내레이션은 화면 가운데 자막(가운데 정렬, 2줄 이내)
2. 일기 쓰는 장면(템플릿 영상 edv02_tablet + tablet_script.py): 그 편 인용문의 영어 필기체가 펜을 따라 새겨짐. 핵심 인용은 큰 글씨(자막 없음)
3. 이야기 장면: 그 편 내용에 맞는 로마 시대 장면(현대 장면 금지). 큰 글씨 1~2개
4. 오늘 밤 할 일: 로고 없음, 출처, 하단 THE EMPEROR'S DIARY는 첫 화면과 같은 위치·글꼴
5. 슬로건: "매일 밤, 황제처럼 생각하라 · 황제의 일기" (성우: outro_default.mp3 — '생각하라'·'일기' 끝음을 낮춘 버전)
6. 마지막: 주화 로고 → 황제의 일기 → THE EMPEROR'S DIARY → 안내 문구 → 버튼 3개(금색 가는 테두리 원 + 아이보리 선 아이콘)
   릴스: 좋아요·팔로우·친구에게 공유 / 쇼츠: 좋아요·구독(종)·친구에게 공유

## 고정값
- 성우: Typecast 건석 tc_6731b2e0855f351b98d30c48, tonedown, tempo 1.0 (두 테이크 받아 쉼이 또렷한 쪽)
- 글꼴: Hahmlet 600 / Cormorant SC / Pretendard SemiBold, 아이보리 톤
- 음악 3곡 돌려쓰기 (편 번호 % 3): 1 miss-you(시작 19.5s) → 2 classical-7(91s) → 0 secret-garden(97s), 내레이션 아래 bed 0.30
- '출근' 같은 현대 표현 금지 → "일을 시작하기 전에" 등

## 새 장면을 만들 때 (대표 지시 2026-11-02)
렌더링 전에 프롬프트를 촘촘히 쓴다: 시대·장소·연도, 손/인물 위치와 얼굴 노출 여부, 소품의 역사 고증(두루마리·밀랍판·청동),
화면 속 글씨 처리, 카메라 움직임(고정 또는 아주 느린 줌인), 상단 3분의 1 텍스트 여백, 금지 요소. 영상이 흘러 주인공이 화면 밖으로 빠지면 정지 이미지 + 줌인으로 대체.

## 설명란
"<인용문>" — 마르쿠스 아우렐리우스 『명상록』 <권> <절>
<사연 2~3문장>
🌙 오늘 밤 할 일 / <한 줄>
━━━ 황제의 일기 | THE EMPEROR'S DIARY / 로마 황제 마르쿠스 아우렐리우스가 매일 밤 자기 자신에게만 쓴 일기, 『명상록』. / 매일 3편, 황제의 생각을 한 줄씩 나눕니다. / 구독해 두시면 오늘 밤에도 황제의 한 줄이 찾아갑니다. / 매일 밤, 황제처럼 생각하라.
#명상록 #마르쿠스아우렐리우스 #스토아 #스토아철학 #철학 #인생명언 #황제의일기 #shorts

## 고정 댓글
<그 편 질문 1문장> <답 유도 1문장> 🌙 황제의 일기는 매일 3편, 로마 황제의 생각을 한 줄씩 나눕니다. 구독해 두시면 오늘 밤에도 황제의 한 줄이 찾아갑니다.

## 자동 게시 (2026-11-02)
- 인스타 릴스·쓰레드 글: Supabase 함수 ed-publish (cron emperor-social, 5분마다), 대기열 ed_posts, 계정 ed_accounts (밸류노트 social_* 와 분리)
- 영상 주소: https://www.valuenote.co.kr/docs/emperor/ep/<id>_reels.mp4 (repo docs/emperor/ep 에 올리면 됨)
- 쓰레드: 표지 사진 1장(cover_path) + 글. 끝맺음은 함수가 자동으로 붙임 → 빈 줄 + "매일 밤, 황제처럼 생각하라.\n황제의 일기."
- 계정 연결: social-oauth ?go=<nonce> (social_oauth_state 에 platform instagram_ed/threads_ed/youtube_ed 로 1회용 nonce, 1시간 유효)
- 유튜브 API 연결은 youtube_account id=2
- 멈추기: app_config ed_paused = true

## 표지(썸네일) 양식 (2026-11-02 확정)
- "큰 흰 글씨 + 강한 장면" 프레임 1장 = 유튜브 맞춤 썸네일 = 릴스 cover_url = 쓰레드 사진 = 틱톡 커버
- thumb_epXX.jpg 로 docs/emperor/ep 에 올리고 ed_posts.cover_path 에 경로 지정

## 인코딩
- 그레인(fx.grain) 쓰면 파일이 커짐 → libx264 -crf 24 -tune grain -maxrate 9M (유튜브용)
- 인스타 업로드본은 별도: -crf 23 -tune grain -maxrate 5M -bufsize 10M, 오디오 aac 48kHz 스테레오 160k (<id>_reels_ig.mp4)
  · 3편 원본(6Mbps, 96kHz 모노)은 인스타 처리 ERROR 났음
- 사이트 배포는 몇 분 늦음 → HEAD 200 확인 후 게시 (ed-publish {"action":"check","url":...})

## 틱톡
- 스튜디오 업로드는 크롬 file_upload (10MB 미만, /mnt/user-data/uploads 에 복사). fetch 는 CSP 로 막힘
- 설명: 제목. "인용" 출처. 매일 3편… 팔로우해 두시면… 매일 밤, 황제처럼 생각하라. #명상록 #철학 #황제의일기
- 커버는 첫 프레임(훅 화면)이 그대로 큰 글씨 양식이라 따로 안 바꿔도 됨
