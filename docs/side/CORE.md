# From Korea, With Love — 핵심 규칙 (2026-11-03, 토큰 절약판)

> 매 대화·작업이 읽는 유일한 문서. 상세·역사·예시는 저장소 `docs/side/HANDOVER.md`(장 번호 동일)를 **필요한 장만 grep** 해서 읽는다. 전체를 읽지 않는다.
> 운영자: 최민우 대표님. 본업 밸류노트, 이 채널은 가벼운 부업. 답은 한국어, 결론·할 일 먼저, 여러 안이면 하나를 추천.

## 0. 지금 운영 방식 — 검증 모드 (11/2~11/15, 판정 11/16) — 다른 모든 규칙보다 우선
- 진단(10/31): 쇼츠 조회 95, 계속 시청 42.7%/이탈 57.3% → 문제는 **첫 1초 훅**. 알고리즘 노출 거의 없음.
- **주 4편**: 월·수·금·일 08:00 KST. `sc_settings.value`: slots=["08:00"], post_days=[0,1,3,5], per_day 1, verify 기준값.
- **3~4컷, 엔딩 포함 15~20초**, `end.dur` 3.0, 편당 약 $0.9~1.1.
- **훅 먼저**: 첫 프레임 = 가장 궁금한 장면, 첫 자막 = 질문/단정 한 줄(배경 설명 금지). 썸네일 = 첫 컷 1초. 감정 절제는 결말에만.
- **제목·첫 자막에 'Kachi' 금지** → a bird / a magpie / this little bird. Kachi는 엔딩·설명·고정 댓글·태그에서만.
- 형식 실험 `spec.experiment={var:"format",value:"A|B|C|D"}`: 11/2 A(P261104-broom-heart, 완료) · 11/4 B 김치 묻는 이유(R2610312301B1) · 11/6 C 까치와 매운 김치(R2610312302C1) · 11/8 D 꼬마 김밥(R2610312303D1) · 11/9 A P261105-haenyeo-tangerine · 11/11 B 생일 미역국(R2610312304B2) · 11/13 C 붕어빵(R2610312305C2) · 11/15 D 꼬마 호떡(R2610312306D2). A=반전 감성, B=Why Koreans 호기심, C=까치 코미디, D=미니어처 만들기 루프.
- 보류(rejected+hold): P261102-cat-basket, dad-longjongs, P261103-market-sweetpotato, jindo-army, P261031-kachi-handkerchief, P261116-suneung-lunchbox. A가 이기면 3~4컷·훅 먼저로 되살림.
- 판정: 8편 중 하나라도 1,000회 또는 계속 시청 60%↑ → 그 형식으로 주력. 하나도 없으면 유료 생성 중단 권고.
- 제1 원칙 = Supabase docs agent `side-owner-rules`(status applied). 모든 작업이 맨 먼저 읽고, 이 문서보다 우선.
- 예약 작업(11/3 축소): 작업자 토·월·수·금 09:41 (공개 2일 전 제작) · 업로드 데스크 일·화·목·토 18:40 (대표님 Chrome, "이 컴퓨터 필요" 켜짐) · 벤치마킹은 꺼 둠(요청 시에만, /side 인박스).
- 예산 `daily_usd` 3.5. Higgsfield 실단가 ≈ 그림 0.125 · 영상5초 0.25. 잔액 open.higgsfield.ai → Billing.

## 1. 대표님 방식 (꼭)
- 결과물은 내보내기 전 렌더 QA(프레임 직접 확인). 오래 걸리는 일은 먼저 돌리고 다른 일. 속도 중시.
- 반려 = 수정 요청(`feedback` type rework). 새 세션은 **rework부터**. 고친 뒤 `feedback`에 claude 답.
- 게시·제작 상태는 기억 아닌 실제 데이터(Supabase·릴리스)로 확인 후 말한다.
- 제목에 #shorts 금지(설명 끝 해시태그에 한 번), 제목 40자 안쪽. 자막 파일·설정 안 함. 알림 최소, 결과는 /side.

## 2. 채널
From Korea, With Love · @KachiFromKorea · UCR5ao2RmISHYMmDinRPIaDw (밸류노트 UCXh2Zs40HIrLZK5GTrHyYSQ 와 같은 구글 계정의 브랜드 채널). 진행자 까치 Kachi(좋은 소식·소포 배달). '아동용 아님', 카테고리 영화/애니메이션, 언어 영어, 합성 콘텐츠 '아니요'. 브랜드 파일 `docs/side/`. 채널 설명 전문·스튜디오 설정 → HANDOVER 2장.
**Chrome 공유 잠금**: docs 'locks' id 'chrome-studio' holder 'kachi', 끝나면 released=true. 작업 뒤 Studio와 youtube.com 모두 밸류노트로 되돌림(Studio는 `studio.youtube.com/channel/UCXh2Zs40HIrLZK5GTrHyYSQ` 직접 열어 확인).

## 3. 콘텐츠 규칙
- 말 없음. 모든 컷 5초 영상(정지 컷·싼 모델·저해상도 금지). 컷마다 4~8단어 영어 자막 한 줄(없어도 됨). 한국이 화면에 보임(한옥·장독대·김장·감나무·포장마차…). 감정 하나.
- 이야기 품질(P0): ① 친절의 이유를 1컷에 ② 마지막 컷 반전·회수 ③ 까치의 능동 역할 ④ 시작보다 큰 보상. 놀라움·정점·자연스러움·까치 역할 각 4점↑만 승인.
- 감정 절제: 눈물·우는 얼굴 금지(프롬프트에 tears/crying/wet eyes 금지). 정점은 멈칫·입술 다물기·숨 고르기·조용한 미소·손 잡기로. 울컥은 한 편에 한 번(결말).
- 개연성: 나이·동물 수명(개 10~15년, 까치 ~10년) 맞추기, 결말 소품의 경로가 앞 컷에 보임, 왜 거기 있는지 한 번은 나옴, 까치가 돕는 동기를 1컷에, 우연은 한 편에 하나, 동물 행동 과도하게 사람 같지 않게.
- 말없는 디테일 `spec.details` 2~4개(액자 속 사진 대비 등), 해당 컷 프롬프트에 그대로.
- **수익 정책(2026-07 유튜브)**: 동물 곤경→구조형 주력 금지, 동물이 다치거나 굶는 장면 금지, 편마다 장소·계절·소품·반전 달리(템플릿 반복 금지). 종교 자극·유명 캐릭터·실존 인물·정치·북한 금지.
- 기획안 = 촬영표(`spec.bible`, `spec.shots` 3~4개 {n,img_prompt,refs,reuse,action,dur,cap,detail}, `spec.details`, `spec.experiment`, `pinned` 필수). 제작은 그대로: 그림 한 번에 → 격자 1장 점검 → 실패 컷만 1회 고침 → 영상 한 번에. 이어지는 장면은 앞 영상 마지막 프레임(ffmpeg -sseof -0.1 … -frames:v 1)으로 시작.

## 4. 시스템
- 저장소 `immin03/haeja`: `scripts/side/gen/*.json`(push → `side-gen`) · `scripts/side/gen.py` · `social/side/gen/`(결과) · `scripts/side/specs_draft/`→`specs_emo/E*.json`(push → `side-emo` 렌더·릴리스·queue 등록) · `scripts/side/emo.py <ID> --local`(점검 렌더 `_emo/<ID>.mp4`) · `side.html`(/side 관리자) · `supabase/functions/sc-trend-collect`.
- Supabase `msjbrwyzkiueqnzjeicm`: `sc_videos`(review→approved→uploaded, rework/rejected/archived, `feedback`, `stats`) · `sc_plans`(requested→pending→approved→producing→made, line 'emo', `spec`, `publish_at`) · `sc_settings` id=1 `value` jsonb · `sc_trends`/`sc_hot*` · `sc_improve` · docs agent `side-learn`, `side-brief-<D>`, `side-brief-inbox`, `side-task-changes`. `sc_import()` 10분마다 queue.json → sc_videos.
- side-gen은 한 번에 하나, 새 push가 오면 대기 실행 취소됨 → 확인 후 `gh workflow run side-gen.yml -R immin03/haeja --ref main -f files="…"`. GraphQL 막힘 → `gh api` REST. 잔액 0이면 error "credit balance is too low" → 충전 뒤 retry:true.
- 새 세션 첫 SQL: `select id,status,title,note,feedback from sc_videos where status='rework'; select id,status,title,note,feedback from sc_plans where status in ('rework','requested','approved') order by publish_at;` approved 기획 제작: `id`=`E<yymmdd>-<slug>`, `scheduled_at`=`publish_at`, 시작 시 'producing', 검수 탭에 뜨면 'made'+`sc_videos.plan_id`.
- 엔딩(10/30 개편, 3.0초): 로고 튀어 오름 → 까치 날아와 앉음 → "Kachi brings you love, from Korea" → 더블탭 하트 연출 "Double-tap ♥ / if this warmed your heart" → "Follow for a new story every day". spec `end`로 문구 변경. 썸네일은 반드시 이야기 장면(`thumb.cut`이 엔딩이면 업로드 데스크 자동 반려).
- 자막 Poppins SemiBold 74px 위쪽 19%. 음악 릴리스 side-assets(music_miss-you 19.5초부터 등).

## 5. 프롬프트 (그대로 복사)
STYLE(모든 그림 끝): `Style: handcrafted 3D miniature diorama photographed with a macro lens, tilt-shift, shallow depth of field, soft cinematic light, felt, clay, paper and wood textures with tiny hand-painted details, gentle film grain, warm nostalgic color grade, clay figurines with soft rounded faces and gentle, restrained, understated expressions (no tears, no crying, no exaggerated sad faces), not photorealistic. Vertical 9:16 frame, main subject in the middle of the frame, a calm uncluttered area in the top fifth of the frame. Absolutely no text, no letters, no numbers, no hangul, no logos, no labels, no brand names, no watermark anywhere.`
KACHI(까치 컷, ref `social/side/gen/c1_magpie.jpeg`): `The magpie is exactly the character in the magpie reference image: a small round chibi magpie with a glossy black head, cream-white face and belly, big shiny dark-brown eyes, short black beak, dark navy-blue wings, a red knotted neckerchief and a small brown leather satchel. It does NOT hold a microphone.`
영상 꼬리: `Keep the miniature clay diorama look and every character design identical to the first frame. One simple, small action only; subtle, slow, gentle motion; the camera stays almost still with at most a slow gentle push-in. No text, no tears, no crying, no morphing faces, no extra fingers or limbs, no sudden camera shake, no cuts.`
같은 인물·장소 재등장 컷은 앞 컷 이미지를 ref로. 까치 없는 컷엔 까치 ref 넣지 않기.

## 6. 점검 체크리스트
깨진 글자(액자·간판·라벨; 필요하면 'Kachi' 한 단어만) · 실제 브랜드 로고 · 별 문양 · 까치 마이크·크기 · 같은 인물 두 번 · 하늘 가로 띠 · 소품 개수 맞나(마지막 감=한 개) · 자막 가독성·줄바꿈 · 설계한 디테일 보이나(액자 속 얼굴 동일) · 눈물 없음 · 썸네일이 이야기 장면 · 동물 고통→구조 아님 · 손가락·3명 이상·빠른 동작·크기 불일치 미리 회피.

## 7. 토큰 규칙 (11/3 대표님: "토큰 효율 극대화, 할 수 있는 건 전부")
- 이 문서만 읽고, HANDOVER.md는 필요한 장만 grep. 긴 문서를 대화에 붙여 넣지 않는다.
- 작업 시작은 SQL 한 번 → 할 일 없으면 즉시 종료(클론·문서·브라우저 없이).
- 그림 점검은 4~5컷을 1024px 격자 1장으로 1회 Read. 렌더 점검은 컷당 프레임 1장을 가로로 이어 붙인 1장.
- SQL은 필요한 열만(`select *`·`stats.hist`·긴 `feedback` 금지), `limit` 항상. 셸은 `git pull -q`, `gh run view --json conclusion`, 긴 로그 `tail -20`. 웹 검색은 표준 모드, 트렌드는 `sc_hot`만 읽기.
- 브라우저: 스크린샷 금지(실패 시만), find+클릭·get_page_text 사용, 영상당 ~15회 호출.
- 시장 동향·성과 수집은 자동 Claude 작업 없이 /side 버튼(요청)으로만. Supabase cron(엣지 함수)은 토큰 0이라 유지.
- 기계적 작업(업로드·집계)은 Sonnet/Haiku, 기획·판정만 Opus/Fable. 대화는 작업 하나당 새 대화.
- 기계적 판단은 코드로: emo.py가 썸네일 컷·제목 40자·#shorts·금지어(tears 등)를 검사해 거부한다(없으면 추가).
