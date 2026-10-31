# From Korea, With Love — 인수인계서 (2026-10-30 새벽 개정)

> 이 문서 하나만 새 프로젝트에 올리면 이어서 작업할 수 있게 썼다. 처음 읽는 Claude는 이 문서를 끝까지 읽고 시작한다.
> 운영자: 최민우 대표님 (아래 "대표님"). 밸류노트(ValueNote, 금융 콘텐츠 앱·채널)가 본업 채널이고, 이 채널은 **가볍게 운영하는 부업 채널**이다.

---

## 0. 한 줄 요약
진행자 까치(Kachi)가 나오는 **말 없는 미니어처 애니메이션 감성 쇼츠**(25~35초)를 Higgsfield로 만들어, 하루 2편 유튜브에 올린다. 그림·영상 생성 → 렌더 → 관리자 페이지 검수 → 대표님이 휴대폰으로 받아서 업로드.

---

## 0-1. 운영 방식 (2026-10-28 15:20 대표님 결정 — 가장 우선)
- **매일 2편, 주말 포함 (08:00 미국 저녁 · 22:00 인도 저녁·유럽 낮).** 하루 2편 넘게 올리지 않는다(대표님 직접 업로드 포함). `sc_settings.value`: slots = weekend_slots = ["08:00","22:00"]
- **한 편 4~5컷, 엔딩 포함 약 22~25초, 편당 약 $1.3~1.6, 월 약 $90~100** (2026-10-28 18:07 대표님 확정). 길이는 기획 단계에서 이야기에 맞게 정한다(단순하면 4컷, 시간이 흐르거나 반전이 있으면 5컷)
  - 근거: 우리 감성 쇼츠 표본(길이 확인 110편)에서 21~30초가 하루 조회수 중앙값 최고(약 5.4만), 15초 이하가 최저(약 0.2만). 전체 쇼츠 10만 8천 편 분석(Quso)은 11~20초가 최고
  - **이미 만든 영상을 뒤에서 줄이지 않는다** (17:57 대표님 "억지로 줄이니 개연성이 다 없어졌다"). 결말이 기대는 원인(예: 까치가 남긴 감을 먹는 장면)은 반드시 보여 준다
  - 비용 절감은 컷을 빼서가 아니라: 같은 장면이 이어지는 컷은 앞 영상 마지막 프레임(ffmpeg -sseof -0.1 … -frames:v 1)으로 시작, 반복 장소·인물 그림 재사용, 기획 먼저로 고침 0회
  - 정지 컷·싼 모델·해상도 낮추기는 여전히 금지
- **기획 먼저(PLAN-FIRST) — "처음에 기획을 탄탄하게 해서 한 번에 렌더링"**: 기획안은 그대로 찍기만 하면 되는 촬영표여야 승인한다.
  - `spec.bible`: 인물(나이·얼굴·머리·옷 색·까치 대비 크기)·장소(구조·빛·시간·계절)·색감·반복 소품을 고정 문장으로 정해 모든 프롬프트에 그대로 쓴다. 같은 장소·인물이 다시 나오면 예전 그림 재사용(`spec.reuse`)
  - `spec.shots`: 4~5개 {n, img_prompt(최종 그림 프롬프트 전문), refs, reuse, action(작고 느린 동작 하나), dur, cap, detail}
  - `spec.details`: 말없는 디테일 2~4개(아래 3장)
  - 승인 전 점검: 소리 없이도 이해되고 결말의 원인이 화면에 다 나오는가(첫 컷 궁금증 → 가운데 전환 → 마지막 컷 반전), 컷마다 7장 체크리스트 위험 요소(손가락, 글자, 인물 3명 이상, 빠른 동작, 크기 불일치, 액자 속 얼굴)를 미리 안전한 장면으로 바꿨는가, **3장 "감정 표현·개연성" 점검을 통과했는가**, **3장 "유튜브 수익 정책" 점검을 통과했는가**
  - 제작은 촬영표를 그대로: 그림 한 번에 → 한 번 점검 → 실패 컷만 1회 고침 → 영상 한 번에. 고침이 생기면 원인을 7장 체크리스트에 한 줄 추가. 목표 고침 0회
- **예산**: 매일 3.5달러(`daily_usd`, 관리자 설정 탭에서 변경). 넘으면 그날 제작을 멈추고 다음 날 이어 감. 실제 Higgsfield 단가는 생성기 단가표의 약 2.5배 → 그림 약 0.125, 영상(5초) 약 0.25달러, 4~5컷 한 편 약 1.3~1.6달러. API 잔액은 open.higgsfield.ai → Billing (웹사이트 구독 크레딧과 별개, 2026-10-28 100달러 충전). 대표님이 실측 단가를 알려 주시면 `value.prices` 에 넣는다
- 완성본은 1일 치만 미리(`buffer_days` 1). 기획안(촬영표)은 5일 치(무료)
- 완전 자동: Claude가 트렌드로 기획·승인·제작, 업로드 작업자가 스튜디오 예약. 대표님은 **중단**과 트렌드 탭 **만들어 줘**만
- 학습: 하루 단위 조회수(매일 07:40) + 스튜디오 분석으로 HIT 포맷은 이어 가고 WEAK 는 원인 하나씩 바꾼다. 제작 고침 횟수도 학습. `sc_settings.value.learn`, `docs/side/LEARN.md`
- 예약 작업: "까치 채널 작업자 (하루 2편)" 01:41·09:41·13:41·17:41·21:41 / "From Korea, With Love 쇼츠 업로드 (하루 2번)" 06:40·18:40 (대표님 Chrome, 이 컴퓨터 필요 켜짐) / "까치 채널 벤치마킹·개선 제안" 10:53
- **Chrome 쓰는 예약 작업은 "이 컴퓨터 필요"를 반드시 켠다** (2026-10-28 19:50 대표님). 예약 작업은 클라우드 새 세션으로 시작해 기본 설정으로는 대표님 PC의 Chrome에 닿지 못한다(10/28 19:14 밸류노트·19:41 까치 업로드 모두 "Chrome 연결 안 됨"). 새로 만들 때 `requires_local_device: true` 로 만들고, 만든 뒤 대표님께 데스크톱 앱 → 더 보기 → 예약됨에서 켜졌는지 확인을 알린다. 업로드 시간대에 PC·Claude 데스크톱 앱·Chrome이 켜져 있어야 한다
- **Chrome 공유 잠금**: 밸류노트 업로드 데스크와 같은 Chrome·구글 계정을 쓴다. Supabase `docs` collection 'locks' id 'chrome-studio' 를 holder 'kachi' 로 잡고, 끝나면 released=true. 까치 데스크는 작업 뒤 반드시 youtube.com 과 Studio 를 둘 다 "밸류노트 ValueNote"(UCXh2Zs40HIrLZK5GTrHyYSQ)로 되돌린다. **Studio 는 youtube.com 과 별도로 마지막 채널을 기억한다** — youtube.com 에서 채널을 바꾼 뒤 `studio.youtube.com/channel/UCXh2Zs40HIrLZK5GTrHyYSQ` 를 직접 열어 확인한다(2026-10-30 실제로 겪음)

---

## 1. 대표님이 일하는 방식 (꼭 지킬 것)
- **답은 한국어**로, 결론과 할 일을 먼저, 배경 설명은 짧게. 여러 안이 있으면 하나를 분명히 추천한다.
- 대표님은 개발자가 아닌 "바이브 코더". 코드는 파일 단위로 완성해서 주고, 어디에 어떻게 넣는지 정확히 알려 준다. 가능하면 Claude가 직접 커밋·실행까지 한다.
- **결과물은 내보내기 전에 반드시 렌더링 점검(QA)**. 프레임을 뽑아 직접 눈으로 확인한 뒤에 보여 준다.
- **속도를 중요하게 본다.** 오래 걸리는 일(생성·렌더)은 먼저 돌려 놓고, 기다리는 동안 다른 일을 한다. 무엇 때문에 시간이 걸리는지 짧게 알려 준다.
- 제작이 끝난 것은 바로 관리자 페이지 검수 탭에 올려 둔다. 관리자에서 확인할 수 있는 결과는 따로 알림을 많이 보내지 않는다.
- 게시 여부·제작 상태는 기억으로 단정하지 말고 실제 데이터(저장소, 릴리스, Supabase)를 확인한 뒤 말한다.
- 한국어 문서·디자인 산출물: Pretendard 또는 SUIT 글꼴, `word-break: keep-all`.
- **반려 = 수정 요청** (2026-10-28 대표님: "반려할 때 반려 코멘트 반영하게 해 줘"). 관리자에서 '수정 요청'을 누르면 코멘트가 `feedback` 에 남고 status 가 `rework` 가 된다. 새 세션은 **시작하자마자 rework 부터 처리**한다(아래 5-1). 고친 뒤 무엇을 고쳤는지 `feedback` 에 Claude 답을 남긴다.
- **제목에 #shorts 넣지 않는다** (2026-10-28 결정). 세로 3분 이하는 자동으로 쇼츠로 분류되고, 쇼츠 피드에서 제목이 잘려 #shorts 가 자리만 차지한다. #shorts 는 **설명 끝 해시태그에 한 번**. 제목은 40자 안쪽(관리자 카드에 글자 수 표시).

---

## 2. 채널 정보
| 항목 | 값 |
|---|---|
| 채널 이름 | **From Korea, With Love** (2026-10-28 변경. 이전 이름: What Korea Says / What Korea Says with Kachi) |
| 핸들 | **@KachiFromKorea** (2026-10-30 스튜디오에서 확인, 적용됨). 기존 핸들은 @WhatKoreaSaysTV |
| 채널 ID | UCR5ao2RmISHYMmDinRPIaDw (스튜디오 `studio.youtube.com/channel/UCR5ao2RmISHYMmDinRPIaDw`) |
| 계정 | 밸류노트와 같은 구글 계정 아래 브랜드 채널 |
| 진행자 | 까치 **Kachi** — 한국에서 좋은 소식을 전하는 새. 소포(사랑)를 배달하는 캐릭터 |
| 시청자 | 전 세계(미국 우선), 영어 최소. 가족이 봐도 되는 수준이지만 **'아동용 아님'**으로 설정(아동용이면 맞춤 광고·댓글이 막힌다) |
| 브랜드 파일 | 저장소 `docs/side/`: profile_800.png, banner_2560x1440.jpg, watermark_150.png, logo_main.png(까치+글자), logo_text.png(글자만) |

**채널 설명 (현재 확정본, 2026-10-30 "every week" → "every day")**
```
Hi, I'm Kachi, the magpie! 🐦

In Korea, the magpie (kkachi) is known as the bird that brings good news. Koreans say that when a magpie sings in the morning, a happy surprise or a welcome guest is on the way. That's why I love bringing you tiny stories from Korea that warm your heart.

A mom's box packed at 2 a.m. The last persimmons left on the tree for the birds. Grandma's first bite of kimchi on kimjang day.

Every story is told in a tiny miniature world, with love from Korea 💛

New stories every day. Follow, and tell me which Korean story touched you most!

Visuals are AI-generated miniature illustrations.
```

### 2-1. 스튜디오 설정 (2026-10-30 대표님 요청으로 Chrome에서 전부 점검·최적화)
대표님 질문 "해외로 설정되어 있어? 거주 국가, 타겟층(미국)": **유튜브에는 시청 국가를 고르는 설정이 없다.** 노출 국가는 영상 언어 신호와 초기 시청자 반응으로 알고리즘이 정한다. 그래서 언어 신호를 전부 영어로 맞추고, 업로드 시간을 미국 저녁에 맞췄다.
| 위치 | 값 | 비고 |
|---|---|---|
| 설정 → 채널 → 거주 국가 | 대한민국 (유지) | 실제 거주지. 수익·세금용이라 시청자 타겟과 무관, 바꾸면 안 됨 |
| 설정 → 채널 → 키워드 | Kachi, From Korea With Love, Korea, Korean culture, Korean family, Korean mom, Korean grandma, heartwarming, wholesome, kindness, miniature, diorama, claymation, clay animation, magpie, emotional shorts | 10/30 교체(옛 방향 North Korea·Korean snacks·What Korea Says 등 삭제) |
| 설정 → 채널 → 고급 | 아동용 아님 · 관심 기반 광고 켬 · 클립 허용 · 화질·음질 개선 허용 | 그대로 유지 |
| 기능 사용 자격 | 표준·중급·고급 모두 사용 설정됨 | |
| 업로드 기본 설정 → 설명 | 비움 | 옛 방향 문구("What does Korea really think? We translate…")가 남아 있어 삭제. 편마다 spec 설명에 채널 문구가 들어간다. 이미 올린 7편 설명은 깨끗했음 |
| 업로드 기본 설정 → 태그 | Kachi, From Korea With Love, Korea, heartwarming, wholesome, miniature, claymation | 옛 방향 태그(Korean reaction, netizens…) 교체 |
| 업로드 기본 설정 → 공개 | 비공개(예약 업로드용) | |
| 업로드 기본 설정 → 고급 | 카테고리 **영화/애니메이션**(엔터테인먼트에서 변경), 동영상 언어·제목/설명 언어 **영어**, 표준 라이선스, 댓글 켬·기본 검토, 좋아요 수 표시 | 이미 올린 쇼츠 7편도 카테고리 일괄 변경 |
| 커뮤니티 운영 | 차단 단어(sub4sub, check my channel, telegram, whatsapp, crypto, bitcoin, forex, onlyfans, t.me, promo sm, investment opportunity 등) · 해시태그·URL 포함 댓글 검토 보류 | 스팸은 지우지 않고 검토함으로 |
| 변경·합성 콘텐츠 | 아니요 | 유튜브 정책상 고지 대상은 "사실처럼 보이는" AI 콘텐츠. 완전한 애니메이션은 대상 아님. 실존 인물·장소를 실사처럼 만들 때만 "예" |
업로드 데스크 지시문(예약 작업)에 "자세히 보기에서 카테고리·언어 확인" 단계를 추가했다(2026-10-30).

---

## 3. 방향이 어떻게 바뀌어 왔나 (같은 고민 반복하지 않기)
1. (10/27) 한국 네티즌 반응 영어 롱폼 → 남의 영상 허락 문제로 접음
2. (10/27) 까치 진행 미니어처 롱폼 8분(초코파이 편 완성, 성우 Typecast Audrey, 음악 Owies Ukulele) → 공수가 너무 큼
3. (10/28) 머니멘터리 영상(AI 예수 쇼츠 7,500만 회 사례)을 보고 **감성 쇼츠로 전환**. 종교 자극형·저작권 애매한 옛 영화 짜깁기는 쓰지 않는다(광고주 기피, 수익 정지 위험). 대신 **까치 + 한국적인 장면 + 엄마·할머니·동물 감성**으로 간다
4. 롱폼 파이프라인은 남아 있다(쇼츠에서 크게 터진 주제를 가끔 롱폼으로 키우는 용도). 초코파이 롱폼·쇼츠는 완성되어 검수 탭에 있음

**감성 쇼츠 기준**
- 말 없음. 컷은 모두 영상(보통 5~7개), 컷마다 4~8단어 영어 자막 한 줄(없는 컷도 있음). 영상만 봐도 이해되어야 한다
- 한국이 화면으로 드러나야 한다: 한옥, 장독대, 김장, 감나무, 서울 아파트, 남산타워, 포장마차 등
- 감정 하나에 집중: 엄마, 할머니, 세대 이어짐, 동물 모성, 작은 친절
- **자막 파일·자막 설정은 하지 않는다** (대표님 결정)
- **이야기 품질 기준 (2026-10-28 15:53 대표님: "너무 단조로워, 큰 감동도 없고 억지스럽다, 까치가 등장했으면")**: "모르는 사람이 갑자기 착한 일을 한다"는 금지. 기획마다 ① 친절의 이유(첫 컷에 관계·과거를 심는다) ② 마지막 컷의 반전·회수(첫 컷이 새 의미를 갖게) ③ 까치가 직접 움직이는 역할(알아채고, 물어 오고, 이어 준다 — 구경꾼 아님) ④ 시작보다 큰 보상(재회, 돌아온 선물, 드러나는 가족). 놀라움·감정 정점·자연스러움·까치 역할을 1~5점으로 매겨 넷 다 4점 이상만 승인. 기준 예: P261028-bus-scarf "The magpie remembered his scarf" (지난겨울 할아버지가 까치 새끼들에게 덮어 준 목도리를 올겨울 까치가 돌려준다)
- **감정 표현은 담담하게 — 억지 눈물 금지 (2026-10-29 대표님: "뭐할 때마다 적나라하게 우는 모습이 오바스럽다, 담담하거나 울컥하는 모습이 낫다")**
  - 눈물 흘리기·우는 얼굴·흐느끼기·젖은 눈 클로즈업을 쓰지 않는다. 그림·영상 프롬프트에 tears, crying, sobbing, eyes filled with tears, wet eyes 를 쓰지 않는다
  - 감정 정점은 **멈칫, 입술 다물기, 숨 한 번 고르기, 말없이 고개 끄덕이기, 조용히 번지는 미소, 손을 꼭 잡기·어깨에 손 얹기, 고개 돌리기** 같은 절제된 동작과 소품(1장 디테일)으로 보여 준다. 감동은 인물이 아니라 시청자가 느끼게 둔다
  - 한 편에 '울컥' 정점은 한 번(마지막 컷 근처)만. 나머지 컷은 평온하거나 일상적인 표정
  - 자막·제목에서도 우는 장면 묘사를 하지 않는다(이모지 😭 는 제목에 써도 되지만 화면 속 인물은 울지 않는다)
- **개연성 점검 (2026-10-29 대표님: "개연성 측면에서도 계속 개선이 필요")** — 기획 승인 전 아래를 하나씩 확인한다
  - 세월이 흐르는 이야기: 인물 나이 차와 동물 나이가 맞는가(개 수명 약 10~15년, 까치 수명 길어야 10년 남짓 → 세월 차이를 그 안으로). 같은 인물의 얼굴·옷 단서가 이어지는가
  - 결말 소품의 경로: 마지막 컷에 나오는 물건(우산·목도리·손수건)이 **어떻게 거기 왔는지**가 앞 컷에 보이는가(누가 두고 갔는지, 누가 가져왔는지)
  - 인물이 왜 그 장소·시간에 있는가(퇴근길, 명절 귀성, 매일 같은 시각 등 이유가 화면이나 자막에 한 번은 나온다)
  - 까치의 행동 동기: 까치가 왜 그 사람을 돕는지(받은 은혜, 매일 받는 먹이 등)가 첫 컷에 심겨 있는가
  - 우연이 두 번 겹치지 않는가(우연은 한 편에 하나까지)
  - 동물 행동이 지나치게 사람 같지 않은가(개가 우산을 물고 오는 정도는 OK, 우산을 펴는 건 X)
- **말없는 디테일 설계 (2026-10-28 대표님)**: 기획 단계에서 이야기의 감정을 대사 없이 보여 주는 소품·배경을 먼저 정한다. 예: 엄마 집 액자엔 엄마와 딸이 함께 찍은 사진, 딸 방 액자엔 까치 사진만 → "엄마가 자식을 더 생각한다". 낡은 장갑 vs 새 장갑, 냉장고에 붙은 아이 어릴 적 사진, 자기 담요를 내어 준 흔적 등. 기획안 `spec.details` = [{prop, where(컷 번호), meaning}] 2~4개. 그림 프롬프트에 해당 컷마다 그대로 넣고(액자 속 사진은 인물 ref 를 함께 넣어 같은 얼굴로), 점검 때 "설계한 디테일이 보이는가"를 확인한다. 처음부터 넣어 한 번에 렌더를 끝낸다
- **유튜브 수익 정책 점검 (2026-10-30 조사, 대표님 결정 필요 사항 포함)**
  - 2026년 7월 유튜브가 수익 창출 불가 '진정성 없는 콘텐츠' 세 가지를 정리했다: ① 영상마다 차이가 거의 없는 템플릿·AI 대량 생산물 ② **동물이 곤경에 처했다가 누군가 구해 주는 영상**(AI 여부와 무관, 이런 영상 위주 채널은 YPP 제외) ③ AI 페르소나가 민감한 주제를 다루는 영상 (TechCrunch 2026-07-20)
  - 그래서: 길고양이·새끼 동물이 비·추위에 떨다 구조되는 구조는 **채널의 주력으로 삼지 않는다**. 동물이 나오는 편은 고통이 아니라 관계·은혜 갚기·일상의 따뜻함으로 시작한다(예: 매일 밥 주던 경비원에게 고양이가 무언가 돌려준다). 동물이 다치거나 굶는 장면 금지. 7-1장 트렌드 결론(비·길고양이·작은 친절이 가장 셈)보다 이 정책이 우선
  - 템플릿 반복 위험 줄이기: 편마다 장소·계절·소품·반전이 달라야 하고, 같은 구조를 연달아 쓰지 않는다. 까치의 성격·연속성(같은 까치, 같은 소포)을 살린다
  - 이미 예약된 "The night guard did this for a stray cat 🥹"(E261030-guard-cat, 10/30)은 이 위험에 해당할 수 있다 — 한 편만으로 문제가 되지는 않지만 같은 구조를 이어 가지 않는다

---

## 4. 업로드 운영
- 매일 2편 08:00 · 22:00, 주말 포함 (위 0-1)
- 업로드는 예약 작업이 대표님 Chrome의 유튜브 스튜디오로 한다("이 컴퓨터 필요" 켜져 있어야 함). 직접 올릴 때만 관리자 카드의 "직접 올릴 때" 펼침을 쓴다
- '변경되거나 합성된 콘텐츠' 질문: 캐릭터 애니메이션이라 "아니요". 실존 인물을 실사처럼 만들면 그 편만 "예"
- 카테고리 영화/애니메이션, 동영상 언어·제목/설명 언어 영어 (업로드 기본값, 2-1장)
- 썸네일은 반드시 이야기 장면. 엔딩 화면(흐린 배경, 글자 로고, 하트·터치 점, Double-tap 문구, Follow 알약)이 썸네일이면 업로드 데스크가 자동 반려한다
- 쇼츠 수익은 1,000회당 수십~100원대라 조회수만으로는 작다. 목표는 구독자·채널 성장 → 이후 협찬·롱폼

---

## 5. 시스템 구조
**저장소**: GitHub `immin03/haeja` (밸류노트와 같은 저장소. 사이드 채널 파일은 아래 경로에만 있다)

| 경로 | 역할 |
|---|---|
| `scripts/side/gen/*.json` | Higgsfield 생성 작업 목록. 이 파일을 push 하면 `side-gen` 워크플로가 그 파일만 생성 |
| `scripts/side/gen.py` | 생성기. 이미지 xai/grok-imagine-image-2.0($0.04~0.05), 영상 alibaba/wan-3.0/image-to-video 5초(~$0.10). 이미 있는 결과는 건너뜀. 실행당 비용 상한 `SIDE_GEN_MAX_USD`(기본 3달러) |
| `social/side/gen/` | 생성 결과(id.jpeg / id.mp4 + id.json 기록). `cut/` 은 배경 제거한 까치 PNG |
| `scripts/side/cutout.py` | 까치 배경 제거(rembg isnet). `python3 scripts/side/cutout.py h_이름` |
| `scripts/side/specs_emo/E*.json` | **감성 쇼츠 렌더 설정**. push 하면 `side-emo` 워크플로가 렌더 → 릴리스 업로드 → `social/side/queue.json` 등록 |
| `scripts/side/specs_draft/` | 렌더 대기 중인 설정(점검 끝나면 specs_emo 로 git mv) |
| `scripts/side/emo.py` | 감성 쇼츠 렌더러. `python3 scripts/side/emo.py <ID> --local` 로 로컬 점검 렌더(업로드 안 함, 결과 `_emo/<ID>.mp4`) |
| `scripts/side/brand2.py` | 로고·배너·프로필·워터마크 합성 |
| `scripts/side/render2.py`, `side-long2.yml` | 롱폼(까치 내레이션) 렌더러 — 지금은 거의 안 씀 |
| `scripts/side/music.py` | Mixkit 무료 음악(저작자 표시 불필요) 받아 릴리스 `side-assets` 에 올림 |
| `side.html` | 관리자 페이지 **valuenote.co.kr/side** (밸류노트 관리자와 분리, 로그인만 공유). 탭: 검수·업로드 / 트렌드 / 기획안 / 작업 현황 / 성과 / 설정 (2026-10-28 전면 개편) |
| `supabase/functions/sc-trend-collect` | 감성 쇼츠 트렌드 수집기(엣지 함수). 매일 07:40 KST cron `side-hot-collect`. 우리 올린 영상 조회수도 여기서 읽는다 |
| `supabase/2026-10-28_side_kachi.sql` | 오늘 DB 변경(수정 요청·피드백, 트렌드 표, 이전 방향 보관) |
| `docs/side/` | 브랜드 이미지, 이 인수인계서 |

**GitHub Secrets** (이미 등록됨): HF_API_KEY, HF_API_KEY_ID, HF_API_KEY_SECRET(Higgsfield), TYPECAST_API_KEY, PEXELS_API_KEY

**릴리스**: `side-assets`(음악·성우 샘플), `side-<ID>`(편별 완성 영상)

**Supabase** (프로젝트 id `msjbrwyzkiueqnzjeicm`, 밸류노트와 공용)
- 표: `sc_trends`, `sc_plans`, `sc_videos`, `sc_settings`, `sc_jobs`(작업 현황 탭용 — `supabase/2026-10-27_side_jobs.sql` 을 대표님이 아직 실행 안 했을 수 있음)
- `sc_videos.status`: review(검수 대기) → approved(업로드 대기) → uploaded(올림). rework(수정 요청), rejected(폐기), archived(보관 — 이전 방향 롱폼·초코파이·손흥민). `feedback` = [{at, by: owner|claude, type: rework|note|fixed|discard|archive, text}]. `stats` = {now, h24, h48, d7, hist} 조회수(수집기가 채움)
- `sc_plans`: requested(작성 요청) → pending(승인 대기) → approved(제작 대기) → producing → made. rework(수정 요청), rejected. 감성 쇼츠 기획안은 `line='emo'`, `emotion`(mom·grand·animal·kind·korea·underdog·style), `korea`(한국 장면), `outline`=[{scene, cap}] 컷 목록, `spec`={music, pinned, description, tags, notes}, `publish_at`
- `sc_settings` 는 `id=1` 한 행, 설정은 `value` jsonb 안에 있다(키 열 없음)
- `sc_trends`: kind='idea'(까치 추천 소재: emotion, korea, apply, reactions=왜 먹히나, evidence=[{video_id,title,views,channel}], score) / 'season'(day, upload_by) / 'legacy'(이전 방향, 안 보임)
- `sc_hot_queries`(검색어 30개, cat=감정 유형) → `sc_hot_videos` + `sc_hot_snaps`(날마다 조회수) → 뷰 `sc_hot`(views, per_day=하루 증가, measured=전날 대비 실측 여부, age_days)
- `sc_import()`: 10분마다 사이트의 `/social/side/queue.json` 을 읽어 `sc_videos` 에 넣는다. `kind` 가 `short` 면 단독 쇼츠 행으로 들어간다(2026-10-28 수정). 급하면 `sc_videos` 에 직접 insert 해도 된다
- 관리자 검수 카드: 단독 쇼츠는 영상·썸네일 받기, 제목·설명·태그·고정 댓글(`pinned`) 복사

### 5-1. 새 세션이 가장 먼저 할 일 (대표님 관리자 입력 처리)
```sql
select id, status, title, note, feedback from sc_videos where status = 'rework';
select id, status, title, note, feedback from sc_plans where status in ('rework','requested','approved') order by publish_at;
```
- **영상 rework**: 마지막 owner 코멘트대로 컷을 편집 생성으로 고치거나 spec(자막·음악·엔딩)을 고쳐 다시 렌더 → `sc_import` 가 새 video_url 을 받으면 자동으로 review 로 돌아간다. 이어서 `feedback` 에 `{"by":"claude","type":"fixed","text":"무엇을 고쳤는지"}` 추가.
- **기획안 rework / requested**: 코멘트대로 outline·title·spec 을 고쳐(또는 새로 써서) status 'pending' 으로, feedback 에 Claude 답.
- **approved 기획안**: 아래 작업 순서대로 생성 → 점검 → 렌더. spec 의 `scheduled_at` = 기획안 `publish_at`, `id` 는 `E<yymmdd>-<slug>`. 시작할 때 status 'producing', 렌더가 검수 탭에 뜨면 'made' 와 `sc_videos.plan_id` 연결. **생성 직전 프롬프트에 tears/crying/Pixar 같은 표현이 남아 있지 않은지, 3장 개연성·수익 정책 점검을 통과하는지 한 번 더 본다**
- 자동 작업자(예약 작업 "까치 채널 작업자")가 하루 3번 같은 일을 한다. 대화 중이면 대화에서 먼저 처리해도 된다.

**작업 순서 (한 편 만들기)**
1. `scripts/side/gen/Mxx-이름.json` 작성 → commit/push → `side-gen` 실행(약 10~20분, 이미지 먼저 → 영상)
2. `git pull` 후 이미지 전부 한 장에 모아 **눈으로 점검**(아래 7번 체크리스트). 문제 컷은 편집 생성으로 고친다(원본을 ref 로 넣고 "Keep everything ... the same. Only change ...")
3. `scripts/side/specs_emo/E날짜-이름.json` 작성 → `emo.py --local` 로 점검 렌더 → 프레임 확인
4. push → `side-emo` 가 렌더·등록 → 관리자 검수 탭에 뜬다(안 뜨면 sc_videos 확인)
- push 가 렌더를 일으키면 안 될 때는 커밋 메시지에 `[skip ci]`
- **side-gen 은 한 번에 하나만 돌고, 대기 중인 실행은 더 새 push 가 오면 GitHub가 취소한다**(2026-10-28 실제로 발생). push 뒤 반드시 그 커밋의 실행 결과를 확인하고 cancelled 면 `gh workflow run side-gen.yml -R immin03/haeja --ref main -f files="<파일 이름들>"` 로 다시 돌린다
- Higgsfield 잔액이 0이면 기록 json 의 error 에 "credit balance is too low" 가 남는다. 충전 뒤 retry:true 로 다시
- GitHub GraphQL 이 막혀 있으니 `gh release download` 대신 `gh api repos/immin03/haeja/releases/...` REST 를 쓴다

---

## 6. 감성 쇼츠 형식 (emo.py)
- 1080×1920, 30fps. 5초 영상 6~7컷을 0.2초부터 4.4초씩 잘라 0.5초 겹침 페이드로 잇는다
- 자막: Poppins SemiBold 74px, 화면 위쪽 19% 지점, 흐린 어두운 판 위 흰 글씨. 첫 자막은 첫 프레임부터 보인다(훅)
- 음악: Mixkit 감성 곡(아래), 시작 지점 조절, 1.2초 페이드 인·2.2초 페이드 아웃, loudnorm
- **엔딩 4.2초 (2026-10-30 개편 — 대표님: "좋아요 화면 두 번 클릭하는 거, 팔로우 유도 더 자연스럽게. 좋아요 두 번 클릭이 중요할 것 같아")**. 프레임마다 PIL 로 그려 ffmpeg 로 묶는다(커밋 3b319e8)
  - 0.0초 마지막 장면을 흐리게, 글자 로고(logo_text)가 살짝 튀어 오름 → 0.25~1.35초 소포 든 까치가 오른쪽 위에서 날아와 로고 'From' 위에 앉음 → 1.45초 문구 "Kachi brings you love, from Korea"
  - 1.9초 **더블탭 연출**: 까치 오른쪽 빈자리를 흰 터치 점(손끝)이 2.12초·2.40초 톡톡 두 번 누름 → 빨간 물결 두 번 → 둘째 탭에 빨간 하트가 튀어나오고 작은 하트들이 위로 날아감, 까치가 기뻐서 폴짝 → 아래에 **"Double-tap ♥" / "if this warmed your heart"**
  - 2.85초 빨간 알약 **"Follow for a new story every day"**(버튼 대신 '매일 새 이야기'라는 이유를 주는 문장)
  - 모든 요소가 쇼츠 아래 제목 영역(y>1470)과 오른쪽 버튼 줄(x>940) 밖에 있다
  - 문구는 spec `end` 에서 바꿀 수 있다: `phrase`, `tap_line`(기본 "if this warmed your heart"), `follow_line`(기본 "Follow for a new story every day")
  - 참고: 쇼츠 화면을 두 번 탭하면 좋아요가 되는지는 유튜브 공식 문서로 확인하지 못했다(2026-06 쇼츠 좋아요 버튼이 하트로 바뀜, 한 번 탭은 화면 정리). 그래서 하트 모양을 크게 보여 주어 시청자가 오른쪽 하트 버튼을 눌러도 같은 뜻이 되게 했다
  - 10/30 이전에 렌더된 편(10/30~10/31 예약분 포함)은 옛 엔딩(♥ Like / Follow 버튼). 다시 렌더하지 않았다
- spec 예시
```json
{
 "id": "E261029-moms-box",
 "title": "Every Korean mom packs THIS box 📦😭",
 "description": "…\n\nIn Korea, the magpie is the bird that brings good news 🐦\n\n#KoreanMom #Kimchi #shorts",
 "tags": ["Korean mom", "kimchi", "Korea", "Kachi", "From Korea With Love", "shorts"],
 "pinned": "What was in YOUR mom's box? 📦 Tell Kachi in the comments 💛",
 "scheduled_at": "2026-10-29T20:00:00+09:00",
 "music": {"file": "music_miss-you.mp3", "start": 19.5, "vol": 0.9},
 "cuts": [{"v": "mbv13_pack", "in": 0.2, "dur": 4.4, "cap": "2 a.m. in Seoul."}, {"v": "mbv23_note", "in": 0.2, "dur": 4.4}],
 "thumb": {"cut": 6, "t": 1.4},
 "end": {"phrase": "Kachi brings you love, from Korea", "fly": "h_fly_love", "host": "h_love", "dur": 4.2}
}
```
- 음악 후보(릴리스 side-assets): music_miss-you(첼로+피아노, 19.5초부터 쓰면 상자 여는 순간 고조), music_classical-7, music_i-believe-2, music_we-ll-be-okay, music_classical-vibes-5, music_love-in-the-air. 밝은 곡: music_owies-ukulele 등

---

## 7. 프롬프트 규칙과 점검 체크리스트
**공통 STYLE (모든 이미지 끝에 붙인다)** — 2026-10-29 표정 문구 변경("deeply emotional Pixar-like expressions" 삭제)
```
Style: handcrafted 3D miniature diorama photographed with a macro lens, tilt-shift, shallow depth of field, soft cinematic light, felt, clay, paper and wood textures with tiny hand-painted details, gentle film grain, warm nostalgic color grade, clay figurines with soft rounded faces and gentle, restrained, understated expressions (no tears, no crying, no exaggerated sad faces), not photorealistic. Vertical 9:16 frame, main subject in the middle of the frame, a calm uncluttered area in the top fifth of the frame. Absolutely no text, no letters, no numbers, no hangul, no logos, no labels, no brand names, no watermark anywhere.
```
**KACHI (까치가 나오는 컷, ref 에 `social/side/gen/c1_magpie.jpeg`)**
```
The magpie is exactly the character in the magpie reference image: a small round chibi magpie with a glossy black head, cream-white face and belly, big shiny dark-brown eyes, short black beak, dark navy-blue wings, a red knotted neckerchief and a small brown leather satchel. It does NOT hold a microphone.
```
**영상 공통 꼬리**
```
Keep the miniature clay diorama look and every character design identical to the first frame. One simple, small action only; subtle, slow, gentle motion; the camera stays almost still with at most a slow gentle push-in. No text, no tears, no crying, no morphing faces, no extra fingers or limbs, no sudden camera shake, no cuts.
```
- **`scripts/side/gen_next/` 작업 파일은 믿지 말고 제작 때 `sc_plans.spec.shots` 의 img_prompt·action 으로 다시 만든다** (2026-10-30 핼러윈 편 제작 중 발견: 10/29 이전 파일 4쌍 — 핼러윈·손수건·우산 강아지·홍시 — 에 옛 STYLE "Pixar" 와 "happy tears"·"eyes fill with tears" 가 그대로 남아 있었음. 촬영표가 정본)
- 같은 인물·장소·소품이 다시 나오는 컷은 **앞 컷 이미지를 ref 로 함께** 넣는다(얼굴·옷·상자 일관성)
- 까치가 안 나와야 하는 컷에는 까치 ref 를 넣지 않는다(넣으면 마이크 든 큰 까치가 끼어든다 — 까치밥 1컷 실수)
- 감정 정점 컷의 표정 문구 예: "he goes still, lips pressed together, then a slow, quiet smile", "she pauses for a moment, then smiles softly", "her eyes gently closed with a quiet, relieved smile", "he lets out a small breath and nods"

**점검 체크리스트 (실제로 나왔던 실수들)**
- [ ] **깨진 글자**: 액자·간판·라벨·포장지에 AI 티 나는 한글·영어가 있으면 안 된다. 기본은 글자 없는 그림·무지 포장, 꼭 필요한 자리는 깔끔한 **'Kachi'** 한 단어 (대표님 지적, 2026-10-28)
- [ ] 실제 브랜드 로고(노트북 사과 로고 등) 없음
- [ ] 별 문양 없음(비행기 빨간 별 → 북한·공산권 연상, 하트로 교체했음)
- [ ] 까치가 마이크를 들고 있지 않음, 크기가 장면에 맞음
- [ ] 같은 인물이 한 화면에 두 번 나오지 않음
- [ ] 하늘·배경에 이어 붙인 듯한 가로 띠 없음
- [ ] 이야기 소품이 맞는지(예: "마지막 감"인데 감이 열 개 달려 있으면 안 됨)
- [ ] 자막이 밝은 장면에서도 읽히는지, 마지막 문구 줄바꿈이 자연스러운지
- [ ] 기획한 디테일(액자 속 사진, 소품 대비 등)이 해당 컷에 실제로 보이는지, 액자 속 인물이 본편 인물과 같은 얼굴인지
- [ ] **눈물·우는 얼굴 없음** — 볼에 눈물 줄기, 눈가 반짝이는 물방울, 찡그린 울상이 보이면 편집 생성으로 "calm, restrained expression, no tears" 로 고친다 (대표님 지적, 2026-10-29)
- [ ] **썸네일이 이야기 장면인지** — `thumb.cut` 이 엔딩 카드를 가리키면 안 된다(10/29 까치밥 편이 엔딩 화면 썸네일로 올라간 실수)
  - 2026-10-30부터 `thumb.cut` 은 **1부터 센 이야기 컷 번호**(엔딩 화면은 번호가 없음), `t` 는 그 컷 안 0.5초~(dur−0.3)초. emo.py 가 어긋나면 렌더를 멈춘다(`check_thumb`). 예전 0부터 센 값은 모두 +1 로 옮김
  - 컷을 더하거나 빼거나 순서를 바꾸면 **thumb 을 다시 고르고** 렌더 뒤 `social/side/<id>/thumb.jpg` 를 직접 열어 본다: 로고·"Kachi brings you love, from Korea"·♥/Follow·흐림·검은 화면·깨진 글자 없음, 얼굴 또렷, 가능하면 까치가 보이는 장면. 피드백에 "thumb 확인 <컷>/<초>" 기록
  - 기준 그림: 나쁜 예 `social/side/E261030-kkachi-bap/thumb.jpg`(엔딩 화면, 보관용으로 그대로 둠), 좋은 예 `social/side/E261030-guard-cat/thumb.jpg`
- [ ] **동물이 고통받다 구조되는 장면이 아닌지** (3장 수익 정책)
- [ ] **'없어야 하는' 소품이 정말 없는지** — "이웃 대문엔 호박등, 할머니 대문만 없음"처럼 빈자리로 대비를 만드는 디테일은 그림 모델이 무시하고 같이 그려 넣는다(10/30 핼러윈 2컷 고침). 프롬프트 앞쪽에 "her own gate has NO pumpkin and NO lantern" 을 따로 한 문장으로 쓰고, 대비 소품은 화면 멀리 배치
- [ ] **얼굴이 가려진 인물(유령 천·인형탈 등)의 크기** — 크기 단서가 없으면 까치보다 작은 장난감처럼 나온다(10/30 핼러윈 3컷 고침). "seven-year-old child, fills half the frame height, walks on the ground, shoes visible" 와 "Kachi about the size of the child's head" 를 함께 적는다

---

## 7-1. 트렌드에서 확인된 것 (2026-10-28 첫 수집, 이번 달 업로드 감성 쇼츠 355편)
- 감정 유형별 상위 20편 하루 조회수 합: **작은 친절 624만 > 동물 가족 333만 > 엄마 130만** > 미니어처 38만 > 한국 문화 28만 > 할머니 17만
- 최상위 사례: "They Kicked This Stray Cat Out in the Rain… So He Built Him a HOME" 1,013만 회(14일), "A Small Act of Kindness" 913만 회(7일), "He Built a Safe Home for a Mother Cat and Her 5 Kittens" 55만 회(1일), "A Mother's Love Has No Limits" 290만 회(8일), "POV: Your Mom Packed Your Field Trip Lunch" 14만 회(3일)
- 결론: **비·길고양이·작은 친절**과 **엄마의 희생→세월 뒤 갚기** 구조가 가장 세다. 한국 장면은 이 구조 위에 얹는다(한국 문화만으로는 약함)
- **단, 2026-07 유튜브 정책으로 "동물 곤경 → 구조"형은 수익 제외 위험이 크다(3장).** 조회수가 커도 주력으로 쓰지 않고, '엄마의 희생→세월 뒤 갚기'와 '받은 은혜를 까치가 돌려준다' 쪽을 주력으로 한다
- 종교 자극형(예수·신)·유명 캐릭터(소닉 등)는 수치가 커도 쓰지 않는다

## 8. 제작 현황 (2026-10-30 01:40 스튜디오 기준)
| 편 | 상태 |
|---|---|
| Every Korean mom packs THIS box 📦😭 | 공개 10/28 |
| She stayed like this all night ❄️ | 공개 10/28 (대표님 직접 업로드) |
| The magpie remembered his scarf 🧣🥺 | 공개 10/29 |
| Why Koreans never pick the last persimmon 🥺 | 공개 10/29 (썸네일이 엔딩 화면으로 올라간 편) |
| Mom always said she wasn't hungry… 🥺 | 예약 10/30 |
| The night guard did this for a stray cat 🥹 | 예약 10/30 |
| Grandpa waved until we were gone 🥺 | 예약 10/31 |
| 초코파이(롱폼 8분 + 쇼츠) S261029-choco-pie | 완성, 보관함(옛 채널명 로고) |

**2026-10-29 07:50 감정 표현·개연성 반영 (대표님 지시, 다음 제작분부터)**: 승인된 기획 9건(`sc_plans` line='emo', approved)의 STYLE 문구와 영상 꼬리를 위 7장 새 문구로 바꿈. 눈물 표현 제거 — 핼러윈 할머니(마지막 컷 "말없이 꼭 끌어안는다"), 빨간 손수건(아빠 "잠시 멈췄다가 조용히 미소"), 홍시 할머니("잠시 멈췄다 부드럽게 미소"), 첫 월급(아빠가 "내복을 한참 쓰다듬다 말없이 고개를 끄덕인다"). 개연성 보정 — 우산 강아지(소년 8→12살, 선생님 20대 후반→중반: 개 나이 약 13년. 1컷에 우산을 강아지에게 두고 가는 장면 추가 → 늙은 개가 그 우산을 가져오는 이유), 빨간 손수건(소년 8→14살, 아빠 30대 중반→30살, 딸 5→4살). 아직 촬영표(shots)가 없는 기획(시장 채소·진돗개 버스·노란 우산 고양이·첫 월급·수능 도시락)은 촬영표를 쓸 때 3장 개연성 점검을 적용한다 — 특히 시장 채소는 회사원이 할머니를 돕는 이유(예전 인연)를 첫 컷에 심어야 한다. 노란 우산 고양이처럼 동물이 비에 젖는 기획은 3장 수익 정책 점검을 함께 한다. 이미 완성된 영상은 고치지 않았다.

**다음 배치 후보** (하루 2편 소화하려면 미리 5~10편씩 생성)
- 김장 날 첫 입: 할머니가 수육에 김치를 싸서 손주 입에 넣어 주고, 까치도 받아먹다 매워서 빨개짐(감동+웃음)
- 그 밖에: 수능 날 엄마의 도시락, 첫 월급 내복 선물, 설날 세배와 할아버지, 군대 간 아들 면회, 이산가족 대신 고향 생각(정치색 피함), 추석 보름달 아래 할머니와 송편

**비용**: 정확한 잔액은 Higgsfield 대시보드(open.higgsfield.ai → Billing) 확인

---

## 9. 대표님 할 일 (확인 필요)
- Supabase SQL Editor 에서 `supabase/2026-10-27_side_jobs.sql` 실행(관리자 '작업 현황' 탭)
- 초코파이 롱폼·쇼츠 업로드 여부 결정(옛 채널명 로고가 들어가 있음 → 올릴 거면 로고 교체 재렌더). 지금은 관리자 '보관함'에 있음(되돌리기 버튼)
- 관리자 설정 탭에 핸들 @KachiFromKorea 입력(아직 안 했다면)
- 동물 구조형 소재를 계속 쓸지 결정(3장 수익 정책) — Claude 추천: 주력에서 빼고 은혜 갚기·엄마·할머니 쪽으로
- [ ] **세월이 흐른 같은 인물·동물** — 어릴 적 그림(ref)을 넣으면 '어른'·'늙은 개'도 어린 모습으로 나온다(10/31 우산 강아지 2컷 늙은 개가 강아지로, 홍시 4컷 어른 손녀가 다섯 살로 나와 고침). 세월 뒤 컷엔 어릴 적 그림을 ref 로 넣지 말고 "clearly a grown adult, taller than…, NOT a child" / "OLD dog, not a puppy, thick grey-white muzzle" 를 한 문장으로 따로 쓴다
