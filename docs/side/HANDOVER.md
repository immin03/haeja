# From Korea, With Love — 인수인계서 (2026-10-28 오후 개정)

> 이 문서 하나만 새 프로젝트에 올리면 이어서 작업할 수 있게 썼다. 처음 읽는 Claude는 이 문서를 끝까지 읽고 시작한다.
> 운영자: 최민우 대표님 (아래 "대표님"). 밸류노트(ValueNote, 금융 콘텐츠 앱·채널)가 본업 채널이고, 이 채널은 **가볍게 운영하는 부업 채널**이다.

---

## 0. 한 줄 요약
진행자 까치(Kachi)가 나오는 **말 없는 미니어처 애니메이션 감성 쇼츠**(25~35초)를 Higgsfield로 만들어, 하루 2편 유튜브에 올린다. 그림·영상 생성 → 렌더 → 관리자 페이지 검수 → 대표님이 휴대폰으로 받아서 업로드.

---

## 0-1. 운영 방식 (2026-10-28 오후 대표님 결정 — 가장 우선)
- **하루 4편, 완전 자동.** 업로드 시각(KST): **03:00 유럽 저녁 · 08:00 미국 동부 저녁 · 13:00 미국 서부 저녁 · 22:00 인도 저녁·유럽 낮** (`sc_settings.value.slots`, per_day = 칸 수, `auto` true)
- **완성본 3일 치를 미리 비축**(`buffer_days` 3), 기획안은 5일 치
- 기획: Claude가 트렌드(`sc_hot`)에서 지금 뜨는 구조를 골라 **한국의 정·사랑, 한국 장소·물건, 까치를 살짝** 얹는다. 길이 자유(4~9컷). 승인은 Claude가 한다
- **학습**: "뜬 포맷이 있으면 그 포맷으로 계속, 그 주제도 몇 번 더." 작업자가 하루 단위 조회수(매일 07:40 수집, 공개 후 24·48시간·7일)와 스튜디오 분석(시청 선택 비율·평균 시청 비율, 업로드 작업자가 읽음)을 채널 중앙값과 비교 → 2배 이상이면 같은 포맷 후속 2~3편, 절반 미만이면 원인 하나씩 바꿔 보기, 3번 연속 약하면 1주 쉬기. 하루 1칸은 새 구조 실험. 교훈은 `sc_settings.value.learn`(관리자 성과 탭)과 `docs/side/LEARN.md`
- 렌더가 끝나면 `sc_import` 가 자동 모드에서 바로 'approved' → 업로드 작업자가 스튜디오 예약
- **관리자 페이지는 보기 위주**(대표님: "체크박스 이런 것도 필요 없어. 다 너가 체크할 거야"): 편성·트렌드·성과·설정 4탭. 대표님이 하는 일은 **중단**(사유 있으면 고치고, 없으면 교체. 예약된 영상은 "[중단]" + 비공개)과 트렌드 탭의 **만들어 줘** 요청(sc_plans status 'requested' → 가장 빠른 빈칸에 우선 편성)뿐. 직접 올리기는 카드의 "비상시 직접 올리기" 접힘 칸에만
- 예약 작업: "까치 채널 작업자 (기획·제작·학습 완전 자동, 하루 4편)" 01:41·09:41·13:41·17:41·21:41 / "From Korea, With Love 쇼츠 업로드 (하루 4편)" 06:40·18:40 (대표님 컴퓨터 Chrome 필요)
- **비용 절감 규칙 (2026-10-28, 목표 편당 0.6달러 이하)**: ① 그림을 먼저 만들고 점검을 통과한 컷만 영상으로 만든다(그림·영상 한 번에 돌리지 않는다 — 지금까지 3편 비용의 약 40%가 다시 만들기였다) ② 영상 컷은 움직임이 이야기인 2~3컷만, 나머지는 그림 한 장을 천천히 움직이는 컷(`emo.py` 의 `{"img": …, "move": "in|out|left|right|up|down"}`, 0원) ③ 컷 5~6개 ④ 같은 장소·인물은 앞 편 그림을 재사용(편집 생성 0.05달러로 계절·시간만 바꾸기) ⑤ 같은 포맷 후속편은 배경·소품 그림을 그대로 쓴다 ⑥ 약한 포맷에는 돈을 더 쓰지 않는다
- 비용: 하루 4편 × 약 0.6달러 = 약 2.4달러. 잔액이 떨어지면 작업자가 멈추고 성과 탭에 "⚠ 충전 필요"

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
| 핸들 | 추천 @KachiFromKorea (안 되면 @FromKoreaWithKachi → @KachiKorea). 기존 핸들은 @WhatKoreaSaysTV. **대표님이 실제로 무엇으로 바꿨는지 확인할 것** |
| 계정 | 밸류노트와 같은 구글 계정 아래 브랜드 채널 |
| 진행자 | 까치 **Kachi** — 한국에서 좋은 소식을 전하는 새. 소포(사랑)를 배달하는 캐릭터 |
| 시청자 | 전 세계, 영어 최소. 가족이 봐도 되는 수준이지만 **'아동용 아님'**으로 설정(아동용이면 맞춤 광고·댓글이 막힌다) |
| 브랜드 파일 | 저장소 `docs/side/`: profile_800.png, banner_2560x1440.jpg, watermark_150.png, logo_main.png(까치+글자), logo_text.png(글자만) |

**채널 설명 (현재 확정본)**
```
Hi, I'm Kachi, the magpie! 🐦

In Korea, the magpie (kkachi) is known as the bird that brings good news. Koreans say that when a magpie sings in the morning, a happy surprise or a welcome guest is on the way. That's why I love bringing you tiny stories from Korea that warm your heart.

A mom's box packed at 2 a.m. The last persimmons left on the tree for the birds. Grandma's first bite of kimchi on kimjang day.

Every story is told in a tiny miniature world, with love from Korea 💛

New stories every week. Follow, and tell me which Korean story touched you most!

Visuals are AI-generated miniature illustrations.
```

---

## 3. 방향이 어떻게 바뀌어 왔나 (같은 고민 반복하지 않기)
1. (10/27) 한국 네티즌 반응 영어 롱폼 → 남의 영상 허락 문제로 접음
2. (10/27) 까치 진행 미니어처 롱폼 8분(초코파이 편 완성, 성우 Typecast Audrey, 음악 Owies Ukulele) → 공수가 너무 큼
3. (10/28) 머니멘터리 영상(AI 예수 쇼츠 7,500만 회 사례)을 보고 **감성 쇼츠로 전환**. 종교 자극형·저작권 애매한 옛 영화 짜깁기는 쓰지 않는다(광고주 기피, 수익 정지 위험). 대신 **까치 + 한국적인 장면 + 엄마·할머니·동물 감성**으로 간다
4. 롱폼 파이프라인은 남아 있다(쇼츠에서 크게 터진 주제를 가끔 롱폼으로 키우는 용도). 초코파이 롱폼·쇼츠는 완성되어 검수 탭에 있음

**감성 쇼츠 기준**
- 말 없음. 컷 5~6개(영상 2~3 + 움직이는 그림), 컷마다 4~8단어 영어 자막 한 줄(없는 컷도 있음). 영상만 봐도 이해되어야 한다
- 한국이 화면으로 드러나야 한다: 한옥, 장독대, 김장, 감나무, 서울 아파트, 남산타워, 포장마차 등
- 감정 하나에 집중: 엄마, 할머니, 세대 이어짐, 동물 모성, 작은 친절
- **자막 파일·자막 설정은 하지 않는다** (대표님 결정)

---

## 4. 업로드 운영
- **하루 4편**(2026-10-28 결정): 03:00 / 08:00 / 13:00 / 22:00 KST. 위 0-1 참고
- 업로드는 예약 작업이 대표님 Chrome의 유튜브 스튜디오로 한다. 직접 올릴 때만 관리자 카드의 "직접 올릴 때" 펼침을 쓴다
- '변경되거나 합성된 콘텐츠' 질문: 캐릭터 애니메이션이라 "아니요". 실존 인물을 실사처럼 만들면 그 편만 "예"
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
- **approved 기획안**: 아래 작업 순서대로 생성 → 점검 → 렌더. spec 의 `scheduled_at` = 기획안 `publish_at`, `id` 는 `E<yymmdd>-<slug>`. 시작할 때 status 'producing', 렌더가 검수 탭에 뜨면 'made' 와 `sc_videos.plan_id` 연결.
- 자동 작업자(예약 작업 "까치 채널 작업자")가 하루 3번 같은 일을 한다. 대화 중이면 대화에서 먼저 처리해도 된다.

**작업 순서 (한 편 만들기)**
1. `scripts/side/gen/Mxx-이름.json` 작성 → commit/push → `side-gen` 실행(약 10~20분, 이미지 먼저 → 영상)
2. `git pull` 후 이미지 전부 한 장에 모아 **눈으로 점검**(아래 7번 체크리스트). 문제 컷은 편집 생성으로 고친다(원본을 ref 로 넣고 "Keep everything ... the same. Only change ...")
3. `scripts/side/specs_emo/E날짜-이름.json` 작성 → `emo.py --local` 로 점검 렌더 → 프레임 확인
4. push → `side-emo` 가 렌더·등록 → 관리자 검수 탭에 뜬다(안 뜨면 sc_videos 확인)
- push 가 렌더를 일으키면 안 될 때는 커밋 메시지에 `[skip ci]`
- GitHub GraphQL 이 막혀 있으니 `gh release download` 대신 `gh api repos/immin03/haeja/releases/...` REST 를 쓴다

---

## 6. 감성 쇼츠 형식 (emo.py)
- 1080×1920, 30fps. 5초 영상 6~7컷을 0.2초부터 4.4초씩 잘라 0.5초 겹침 페이드로 잇는다
- 자막: Poppins SemiBold 74px, 화면 위쪽 19% 지점, 흐린 어두운 판 위 흰 글씨. 첫 자막은 첫 프레임부터 보인다(훅)
- 음악: Mixkit 감성 곡(아래), 시작 지점 조절, 1.2초 페이드 인·2.2초 페이드 아웃, loudnorm
- **엔딩 4.2초 (확정)**: 마지막 장면을 흐리게 → 글자 로고(logo_text) → 소포 든 까치(`cut/h_fly_love.png`)가 오른쪽 위에서 날아와 로고 'From' 위에 앉는다(`cut/h_love.png`) → 문구 **"Kachi brings you love, from Korea"** → ♥ Like / Follow 버튼. 쇼츠 아래 제목 영역과 오른쪽 버튼 줄(x>940)을 피한다
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
 "thumb": {"cut": 5, "t": 1.4},
 "end": {"phrase": "Kachi brings you love, from Korea", "fly": "h_fly_love", "host": "h_love", "dur": 4.2}
}
```
- 음악 후보(릴리스 side-assets): music_miss-you(첼로+피아노, 19.5초부터 쓰면 상자 여는 순간 고조), music_classical-7, music_i-believe-2, music_we-ll-be-okay, music_classical-vibes-5, music_love-in-the-air. 밝은 곡: music_owies-ukulele 등

---

## 7. 프롬프트 규칙과 점검 체크리스트
**공통 STYLE (모든 이미지 끝에 붙인다)**
```
Style: handcrafted 3D miniature diorama photographed with a macro lens, tilt-shift, shallow depth of field, soft cinematic light, felt, clay, paper and wood textures with tiny hand-painted details, gentle film grain, warm nostalgic color grade, clay figurines with soft rounded faces and deeply emotional Pixar-like expressions, not photorealistic. Vertical 9:16 frame, main subject in the middle of the frame, a calm uncluttered area in the top fifth of the frame. Absolutely no text, no letters, no numbers, no hangul, no logos, no labels, no brand names, no watermark anywhere.
```
**KACHI (까치가 나오는 컷, ref 에 `social/side/gen/c1_magpie.jpeg`)**
```
The magpie is exactly the character in the magpie reference image: a small round chibi magpie with a glossy black head, cream-white face and belly, big shiny dark-brown eyes, short black beak, dark navy-blue wings, a red knotted neckerchief and a small brown leather satchel. It does NOT hold a microphone.
```
**영상 공통 꼬리**
```
Keep the miniature clay diorama look and every character design identical to the first frame. Smooth, gentle, cinematic motion, no text, no morphing faces, no extra fingers or limbs, no sudden camera shake, no cuts.
```
- 같은 인물·장소·소품이 다시 나오는 컷은 **앞 컷 이미지를 ref 로 함께** 넣는다(얼굴·옷·상자 일관성)
- 까치가 안 나와야 하는 컷에는 까치 ref 를 넣지 않는다(넣으면 마이크 든 큰 까치가 끼어든다 — 까치밥 1컷 실수)

**점검 체크리스트 (실제로 나왔던 실수들)**
- [ ] **깨진 글자**: 액자·간판·라벨·포장지에 AI 티 나는 한글·영어가 있으면 안 된다. 기본은 글자 없는 그림·무지 포장, 꼭 필요한 자리는 깔끔한 **'Kachi'** 한 단어 (대표님 지적, 2026-10-28)
- [ ] 실제 브랜드 로고(노트북 사과 로고 등) 없음
- [ ] 별 문양 없음(비행기 빨간 별 → 북한·공산권 연상, 하트로 교체했음)
- [ ] 까치가 마이크를 들고 있지 않음, 크기가 장면에 맞음
- [ ] 같은 인물이 한 화면에 두 번 나오지 않음
- [ ] 하늘·배경에 이어 붙인 듯한 가로 띠 없음
- [ ] 이야기 소품이 맞는지(예: "마지막 감"인데 감이 열 개 달려 있으면 안 됨)
- [ ] 자막이 밝은 장면에서도 읽히는지, 마지막 문구 줄바꿈이 자연스러운지

---

## 7-1. 트렌드에서 확인된 것 (2026-10-28 첫 수집, 이번 달 업로드 감성 쇼츠 355편)
- 감정 유형별 상위 20편 하루 조회수 합: **작은 친절 624만 > 동물 가족 333만 > 엄마 130만** > 미니어처 38만 > 한국 문화 28만 > 할머니 17만
- 최상위 사례: "They Kicked This Stray Cat Out in the Rain… So He Built Him a HOME" 1,013만 회(14일), "A Small Act of Kindness" 913만 회(7일), "He Built a Safe Home for a Mother Cat and Her 5 Kittens" 55만 회(1일), "A Mother's Love Has No Limits" 290만 회(8일), "POV: Your Mom Packed Your Field Trip Lunch" 14만 회(3일)
- 결론: **비·길고양이·작은 친절**과 **엄마의 희생→세월 뒤 갚기** 구조가 가장 세다. 한국 장면은 이 구조 위에 얹는다(한국 문화만으로는 약함)
- 종교 자극형(예수·신)·유명 캐릭터(소닉 등)는 수치가 커도 쓰지 않는다

## 8. 제작 현황 (2026-10-28 12:00)
| 편 | ID | 상태 |
|---|---|---|
| 엄마의 택배 — Every Korean mom packs THIS box 📦😭 | E261029-moms-box | 완성(31.7초, 새 엔딩·글자 수정 반영), 검수 탭 |
| 까치밥 — Why Koreans never pick the last persimmon 🥺 | E261030-kkachi-bap | 완성(27.8초), 검수 탭 |
| 엄마 까치 — She stayed like this all night ❄️ | E261031-snow-nest | 완성(27.8초), 검수 탭 |
| 초코파이(롱폼 8분 + 쇼츠) | S261029-choco-pie | 완성, 검수 탭(옛 채널명 로고) |

**기획안 탭 승인 대기 (2026-10-28 오후 작성)**: 비 오는 골목 노란 우산(10/31 08:00) · "Mom always said she wasn't hungry" 붕어빵(10/31 20:00) · 아파트 경비 아저씨의 고양이 상자 집(11/1 08:00) · 수능 도시락(11/16 20:00 시즌 고정). 제목에서 #shorts 뺀 상태로 DB·spec·queue 모두 정리함.

**다음 배치 후보** (하루 2편 소화하려면 미리 5~10편씩 생성)
- 김장 날 첫 입: 할머니가 수육에 김치를 싸서 손주 입에 넣어 주고, 까치도 받아먹다 매워서 빨개짐(감동+웃음)
- 비 오는 골목 우산: 장맛비 서울 골목, 까치가 노란 아이 우산을 끌어와 젖은 아기 고양이에게 씌워 줌, 엄마 고양이가 눈을 깜빡여 고마움 표시
- 그 밖에: 수능 날 엄마의 도시락, 첫 월급 내복 선물, 설날 세배와 할아버지, 군대 간 아들 면회, 이산가족 대신 고향 생각(정치색 피함), 추석 보름달 아래 할머니와 송편

**비용**: Higgsfield 45달러 충전, 지금까지 약 16달러 사용 → 남은 돈 약 29달러(편당 1~1.3달러, 수정 생성 포함 시 1.5달러). 정확한 잔액은 Higgsfield 대시보드 확인

---

## 9. 대표님 할 일 (확인 필요)
- 유튜브 스튜디오: 채널 이름·핸들·설명·프로필·배너·워터마크 교체
- Supabase SQL Editor 에서 `supabase/2026-10-27_side_jobs.sql` 실행(관리자 '작업 현황' 탭)
- 초코파이 롱폼·쇼츠 업로드 여부 결정(옛 채널명 로고가 들어가 있음 → 올릴 거면 로고 교체 재렌더). 지금은 관리자 '보관함'에 있음(되돌리기 버튼)
- 관리자 설정 탭에 실제로 정한 핸들 입력
