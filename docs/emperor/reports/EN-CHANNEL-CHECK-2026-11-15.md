# The Emperor's Diary (EN) 점검 (2026-11-15)

## 현황 (스튜디오, 11/15 오전)
- 구독 27 · 48시간 조회 3,878 · 쇼츠 '계속 시청함' 48.2%(한국 채널 31.5%보다 높음)
- 상위: How to BEAT People Who Disrespect You 1,242 / STOP Arguing… 801 / The BEST Revenge… 691 / This Is Why PEOPLE Keep Draining You 427
- 하위: Why VACATIONS… 4 · DREADING Today? 11 · Why ONE Comment… 35
- 유입 정정: 쇼츠는 쇼츠 피드 91.7%·검색 4.4%. '검색 44%'는 롱폼 1편(조회 9회 중 4회) 기준이었다.

## 고정 댓글 사고 (09:35 조치)
- 원인: ed-publish 가 영어 편 댓글을 한국 채널 토큰으로 달았고(en09·en19·en11·px02en·en14, 숨겨짐·고정 불가), 고정 단계가 업로드 작업 안에만 있어 올릴 게 없으면 건너뜀.
- 조치: DB 트리거 ed_posts_en_comment_guard, 5편 재게시·고정, 예약 작업 "공개 직후 고정 댓글 + 시청자 댓글 하트·답글"(22:03·02:03·09:03).

## 채널 분리·성과 별도 수집 (11:11 대표 지시)
- 새 함수 ed-stats-en → ed_stats platform 'youtube_en'(account / 영상별 조회·좋아요·댓글 / search_rank). cron emperor-stats-en 3시간마다, emperor-stats-en-rank 매일 10:55 KST.
- 관리자 /side 미국 탭: 편별 조회·구독자(7일 증가)를 youtube_en 기록으로, '검색 순위' 카드 추가.
- 영어 채널 로그인 연결이 없어 시청 지속률·검색어 리포트는 아직 못 읽는다(연결하면 가능).

## 검색 노출 (무리하지 않는 선)
- 자동완성 근거 검색어: marcus aurelius quotes / meditations marcus aurelius / stoicism marcus aurelius / stoic quotes / stoic lessons, 문제형 how to deal with disrespectful people / ignore people who disrespect you / how to stop overthinking / how to not care what people think / how to deal with toxic people / how to control emotions.
- 추적 검색어 8개(app_config ed_en_keywords): 11/15 기준 전부 50위 밖 → 기준점.
- 적용: 채널 소개 문구 보강, 채널 키워드 9개 추가, 쇼츠 30편 태그 일괄 추가, en19 문제형 태그 2개, SHORTS_EN.md 8-1 규칙(소재·제목·설명 첫 줄·태그·고정 댓글), EN_DAILY_RUN 참조.
- 하지 않은 것: 이미 올린 영상 제목 변경, 설명 일괄 수정.

## 댓글
- en19 시청자 댓글 2개에 하트 + 답글. en08 정치 댓글("Trump.")은 손대지 않음(정치 댓글은 하트·답글 모두 안 함).
- 이후 예약 작업이 새 댓글에 하트·짧은 답글(1~2문장, 출처 확실한 명상록 인용만).

## 남은 것
- 스튜디오에 'px02en reels 설명 추가 — 초안' 비공개 초안 1개.
