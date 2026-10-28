# From Korea, With Love — 인수인계서 (2026-10-28 기준)

> 이 문서 하나만 새 프로젝트에 올리면 이어서 작업할 수 있게 썼다. 처음 읽는 Claude는 이 문서를 끝까지 읽고 시작한다.
> 운영자: 최민우 대표님 (아래 "대표님"). 밸류노트(ValueNote, 금융 콘텐츠 앱·채널)가 본업 채널이고, 이 채널은 **가볍게 운영하는 부업 채널**이다.

---

## 0. 한 줄 요약
진행자 까치(Kachi)가 나오는 **말 없는 미니어처 애니메이션 감성 쇼츠**(25~35초)를 Higgsfield로 만들어, 하루 2편 유튜브에 올린다. 그림·영상 생성 → 렌더 → 관리자 페이지 검수 → 대표님이 휴대폰으로 받아서 업로드.

---

## 1. 대표님이 일하는 방식 (꼭 지킬 것)
- **답은 한국어**로, 결론과 할 일을 먼저, 배경 설명은 짧게. 여러 안이 있으면 하나를 분명히 추천한다.
- 대표님은 개발자가 아닌 "바이브 코더". 코드는 파일 단위로 완성해서 주고, 어디에 어떻게 넣는지 정확히 알려 준다. 가능하면 Claude가 직접 커밋·실행까지 한다.
- **결과물은 내보내기 전에 반드시 렌더링 점검(QA)**. 프레임을 뽑아 직접 눈으로 확인한 뒤에 보여 준다.
- **속도를 중요하게 본다.** 오래 걸리는 일(생성·렌더)은 먼저 돌려 놓고, 기다리는 동안 다른 일을 한다. 무엇 때문에 시간이 걸리는지 짧게 알려 준다.
- 제작이 끝난 것은 바로 관리자 페이지 검수 탭에 올려 둔다. 관리자에서 확인할 수 있는 결과는 따로 알림을 많이 보내지 않는다.
- 게시 여부·제작 상태는 기억으로 단정하지 말고 실제 데이터(저장소, 릴리스, Supabase)를 확인한 뒤 말한다.
- 한국어 문서·디자인 산출물: Pretendard 또는 SUIT 글꼴, `word-break: keep-all`.

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
- 말 없음. 컷마다 4~8단어 영어 자막 한 줄(없는 컷도 있음). 영상만 봐도 이해되어야 한다
- 한국이 화면으로 드러나야 한다: 한옥, 장독대, 김장, 감나무, 서울 아파트, 남산타워, 포장마차 등
- 감정 하나에 집중: 엄마, 할머니, 세대 이어짐, 동물 모성, 작은 친절
- **자막 파일·자막 설정은 하지 않는다** (대표님 결정)

---

## 4. 업로드 운영
- **하루 2편**: 오전 8시(미국 저녁) / 오후 8시(유럽 낮·미국 아침). 첫 2주 28편으로 어떤 감정 유형이 터지는지 보고, 잘 되는 유형만 하루 3편으로 늘린다
- 대표님이 관리자 페이지(휴대폰)에서 영상을 받고, 제목·설명·태그·고정 댓글을 복사해 유튜브 앱으로 올린다
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
| `side.html` | 관리자 페이지 **valuenote.co.kr/side** (밸류노트 관리자와 분리, 로그인만 공유) |
| `docs/side/` | 브랜드 이미지, 이 인수인계서 |

**GitHub Secrets** (이미 등록됨): HF_API_KEY, HF_API_KEY_ID, HF_API_KEY_SECRET(Higgsfield), TYPECAST_API_KEY, PEXELS_API_KEY

**릴리스**: `side-assets`(음악·성우 샘플), `side-<ID>`(편별 완성 영상)

**Supabase** (프로젝트 id `msjbrwyzkiueqnzjeicm`, 밸류노트와 공용)
- 표: `sc_trends`, `sc_plans`, `sc_videos`, `sc_settings`, `sc_jobs`(작업 현황 탭용 — `supabase/2026-10-27_side_jobs.sql` 을 대표님이 아직 실행 안 했을 수 있음)
- `sc_import()`: 10분마다 사이트의 `/social/side/queue.json` 을 읽어 `sc_videos` 에 넣는다. `kind` 가 `short` 면 단독 쇼츠 행으로 들어간다(2026-10-28 수정). 급하면 `sc_videos` 에 직접 insert 해도 된다
- 관리자 검수 카드: 단독 쇼츠는 영상·썸네일 받기, 제목·설명·태그·고정 댓글(`pinned`) 복사

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
 "title": "Every Korean mom packs THIS box 📦😭 #shorts",
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

## 8. 제작 현황 (2026-10-28 11:30)
| 편 | ID | 상태 |
|---|---|---|
| 엄마의 택배 — Every Korean mom packs THIS box 📦😭 | E261029-moms-box | 1차 렌더(엔딩 없음)가 관리자에 있음. 글자 수정 6컷(M04) 생성 중 → 끝나면 새 엔딩으로 재렌더 |
| 엄마 까치 — She stayed like this all night ❄️ | E261031-snow-nest | 렌더 중(side-emo) |
| 까치밥 — Why Koreans never pick the last persimmon 🥺 | E261030-kkachi-bap | 4컷 수정(M05) 생성 중 → 끝나면 specs_draft → specs_emo 로 옮겨 렌더 |
| 초코파이(롱폼 8분 + 쇼츠) | S261029-choco-pie | 완성, 검수 탭(옛 채널명 로고) |

**다음 배치 후보** (하루 2편 소화하려면 미리 5~10편씩 생성)
- 김장 날 첫 입: 할머니가 수육에 김치를 싸서 손주 입에 넣어 주고, 까치도 받아먹다 매워서 빨개짐(감동+웃음)
- 비 오는 골목 우산: 장맛비 서울 골목, 까치가 노란 아이 우산을 끌어와 젖은 아기 고양이에게 씌워 줌, 엄마 고양이가 눈을 깜빡여 고마움 표시
- 그 밖에: 수능 날 엄마의 도시락, 첫 월급 내복 선물, 설날 세배와 할아버지, 군대 간 아들 면회, 이산가족 대신 고향 생각(정치색 피함), 추석 보름달 아래 할머니와 송편

**비용**: Higgsfield 45달러 충전, 지금까지 약 15달러 사용 → 남은 돈 약 30달러(편당 1~1.3달러, 수정 생성 포함 시 1.5달러). 정확한 잔액은 Higgsfield 대시보드 확인

---

## 9. 대표님 할 일 (확인 필요)
- 유튜브 스튜디오: 채널 이름·핸들·설명·프로필·배너·워터마크 교체
- Supabase SQL Editor 에서 `supabase/2026-10-27_side_jobs.sql` 실행(관리자 '작업 현황' 탭)
- 초코파이 롱폼·쇼츠 업로드 여부 결정(옛 채널명 로고가 들어가 있음 → 올릴 거면 로고 교체 재렌더)
