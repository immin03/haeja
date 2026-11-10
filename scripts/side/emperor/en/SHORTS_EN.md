# The Emperor's Diary (EN) — 영어 쇼츠 제작 규칙

채널: The Emperor's Diary, @EmperorsDiary-en (UCRvSvKOjbsEXKY03TCP9I1w) — 한국 채널 황제의 일기(@황제의일기)의 영어판.
원본: 대표 2026-11-11 02:09 KST 지시 (같은 날 02:08 "한국판과 똑같은 화면" 지시를 대체). 미국 스토아 쇼츠 문법을 따른다.

## 1. 훅 = 피드 속 진짜 썸네일
- 0~2초: 인트로·로고·제목 카드 없이, 단독으로 서는 짧은 펀치 문장을 바로 말하고 같은 문장을 큰 글씨로 띄운다.
- 제목, 첫 문장, 첫 화면(표지)이 같은 약속을 한다.
- long_<id>.json: `hook` = 첫 화면 큰 글씨, 첫 문장(sents[0])은 같은 말 · style `"none"`(자막 중복 없음), `kicker` 는 비움.

## 2. 길이
- 30~45초를 목표로 한국판 구조를 줄인다(결론·payoff 는 남김).

## 3. 목소리 (Typecast, lang "eng") — en/VOICES.json
- 해설: Ron `tc_6620ee223bc61e2f6b79fdb5`, 천천히(tempo 0.95), tonedown
- 마르쿠스 아우렐리우스 본인 말(명상록 직접 인용)만: Robert `tc_66bc600762cab997910b107b`, tempo 0.88
- 묶음마다 A·B 두 테이크. 급할 때는 voice-fast 워크플로(REST dispatch)로 side-gen 대기열을 건너뛴다.

## 4. 화면 글씨
- `ED_LANG=en` 으로 render_ed.py / fx_short.py / build_long.py 를 돌리면 영어 글꼴·문구가 적용된다(글꼴은 en/fonts, 저장소 포함).
- 짧은 펀치 문장·자막: 굵은 산세리프(Inter Bold), 큰 흰 글씨. 황제 인용: 우아한 세리프(Playfair Display SemiBold Italic).
- 은은한 어두운 비네트. 화면 아래 20%(쇼츠 버튼)와 오른쪽 끝을 피한다 — 왼쪽 정렬 글 한 줄 폭 820px 이하.
- 미국 철자(neighbor), 한글 0자.

## 5. 장면
- 기존 라이브러리 클립 재사용(CLIPS.json), 새 생성 없음. 어두운 시네마틱 색감, 고대 로마·석상·폭풍·폐허 느낌.

## 6. 음악
- 목소리 아래 낮은 오케스트라 배경. 황제 라이브러리 곡 중 Content ID 안전한 것만: classical-7(start 91, bed 0.22) 또는 miss-you(start 19.5, bed 0.22). secret-garden 금지.

## 7. 표지
- 데스크톱 업로드는 프레임을 자동으로 고르므로 첫 프레임부터 강하게(뚜렷한 장면 + 훅 글씨, 고대비).
- 스튜디오가 쇼츠 표지/프레임 선택을 주면 훅 글씨가 있는 프레임을 고른다.

## 8. 제목·설명 (미국 기준, 대표 01:58·02:09)
- 제목: 문제/결과 먼저, 50자 안팎(60자 미만), 대문자 강조 1~2단어, 해시태그 없음. 예: "STOP Comparing Your Life to Theirs | Marcus Aurelius"
- 설명: 첫 문장에 키워드, 1~2줄 요약, 구독 CTA 한 줄, "Meditations quotes adapted from George Long's public-domain translation.",
  AI 공개(스튜디오 '변경되거나 합성된 콘텐츠' = 예, 한국판과 동일), 끝에 해시태그 3~5개: #Shorts #Stoicism #MarcusAurelius + 주제 태그 1개.

## 9. 기록
- Supabase ed_posts 에 `kind='reel_en'` 으로 넣는다(한국 업로더·인스타·틱톡·쓰레드·댓글 작업은 kind 'reel' 만 읽음).
  to_ig/to_th false, ig/th/tt/yt_comment 상태 'skip: EN', ig_caption = 유튜브 설명, images = {"yt_tags": [...], "lang": "en", "channel": "@EmperorsDiary-en"}.
