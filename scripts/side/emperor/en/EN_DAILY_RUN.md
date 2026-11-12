# The Emperor's Diary (EN) — 영어 쇼츠 하루 3편 제작·게시 절차

대표 결정: 2026-11-11 15:26 KST "쇼츠 전부 배포해, 일 3회 또는 4회 너가 판단해서, 최대한 사람들 많이 보는 시간대에" → 하루 3편.
첫 편 en05b(JjXKNtvMzsc, 11/11 15:30 공개)가 기준 완성본이다. 글꼴·구성·길이는 이 편과 똑같이 만든다(대표 15:11 "롱폼 스타일과 폰트 맞춰서").
채널: The Emperor's Diary, @EmperorsDiary-en (UCRvSvKOjbsEXKY03TCP9I1w). 독립 채널로 보이게 한다 — 제목·설명·고정 댓글·링크에 한국 채널, 번역판, 한국어판 같은 말을 절대 쓰지 않는다(대표 15:04).

## 게시 시각 (미국 동부 시청 시간대)
| 칸 | 한국 시각 | 미국 동부 |
|---|---|---|
| 아침 | 21:47 (D) | 07:47 |
| 점심 | 01:47 (D+1) | 11:47 |
| 저녁 | 08:47 (D+1) | 18:47 |
제작 작업이 D 날 낮에 세 편을 만들고, 업로드 작업이 D 날 저녁 전에 세 편을 스튜디오 예약 게시로 올린다.

## A. 제작 (예약 작업 "The Emperor's Diary (EN) 쇼츠 제작", 매일 13:41 KST)
0. 빈 칸 확인: `select id, scheduled_at from ed_posts where kind='reel_en' and scheduled_at >= '<D> 21:00+09' and scheduled_at < '<D+1> 12:00+09'`. 이미 찬 칸은 건너뛴다. 셋 다 차 있으면 끝.
1. 소재 고르기: 한국 채널 쇼츠(ed_posts kind='reel', id like 'ep%')를 유튜브 반응 순으로(ed_stats platform 'youtube' 최신 views, 같으면 likes) 줄 세우고, `images->>'from'` 으로 이미 영어판을 만든 편은 뺀다. 위에서부터 빈 칸 수만큼 고른다.
2. 대본(영어로 새로 쓴다, 번역 아님 — SHORTS_EN.md 1·2·8절):
   - 첫 문장 = 훅: 0~2초에 단독으로 서는 짧은 펀치 문장, 같은 문장을 첫 화면 큰 글씨로(hook 3줄 안팎).
   - 30~45초. 해설(Ron) 묶음 n0(훅)·n1·n2·n4, 황제 인용(Robert) 묶음 e3·e5. en05b(`long_en05b.json`) 구조를 그대로 따른다.
   - 인용은 확실히 아는 『명상록』 권·절만, 조지 롱(1862) 번역을 쉽게 다듬은 문장. 지어낸 인용 금지.
   - 미국식 철자, 한글 0자, 특정 앱·플랫폼 이름 금지("feed", "phone" 같은 일반어는 됨).
   - 제목: 문제/결과 먼저 60자 미만, 대문자 강조 1~2단어, 끝 " | Marcus Aurelius" 또는 " | Stoicism", 해시태그 없음.
   - `long_<id>.json`(id = en + 한국 편 번호, 예 ep19 → en19), `fx_<id>.json`(장면 6컷). 장면은 **TEMPLATE.md '★ 공용 라이브러리·생성 상한' 그대로**: `python3 ../library.py build` 후 장면마다 `python3 ../library.py find <주제어> --vert` 먼저(한국어판과 같은 장면이면 같은 파일을 같이 쓴다, 최근 5편 사용분은 뒤로), 맞는 게 없을 때만 `scripts/side/gen/EDS<yymmdd>-<id>.json` 에 0~2개 생성. fx 를 다 쓰면 `python3 ../library.py check fx_<id>.json` 통과(한 편 안 중복 금지).
3. 녹음: voice-fast 워크플로를 REST로 부른다(`gh api -X POST repos/immin03/haeja/actions/workflows/voice-fast.yml/dispatches --input body.json`, body = {"ref":"main","inputs":{"req": "<JSON 문자열>"}}).
   req = {"tag":"<id>v","lang":"eng","model":"ssfm-v30","keep":true,"voices":[{name,id,line,emotion,intensity,tempo}…]}.
   이름 `<id>_<묶음>_<A|B>`(n0,n1,n2,e3,n4,e5,end 각 A·B 두 테이크). 해설 Ron `tc_6620ee223bc61e2f6b79fdb5` tempo 0.95 tonedown, 인용 Robert `tc_66bc600762cab997910b107b` tempo 0.88 tonedown(en/VOICES.json).
   end 문장 = "Tonight's task. " + tonight 줄을 이은 문장. 마무리(o1~o3)는 녹음하지 않고 `social/side/voice_samples/en05d` 의 o1_A·o2_A·o3_A 를 0.3초·0.4초 쉼으로 이어 쓴다(같은 문장).
   결과는 `social/side/voice_samples/<id>v/` 에 커밋된다. 실행이 끝날 때까지 8분씩 나눠 확인.
4. 조립·렌더 (DAILY_RUN.md 1단계 준비 그대로 + `ED_LANG=en`):
   take_check.py 로 테이크 고르기 → `ED_LINES=/home/claude/vo/v2_lines.json ED_LANG=en python3 voice_v2.py <id> <A,B,…> <voice_dir>` →
   `ED_LANG=en python3 build_long.py long_<id>a.json` → `ED_LANG=en python3 render_ed.py /home/claude/ed/spec_<id>a.json base.mp4 --platform shorts` →
   `ED_LANG=en python3 fx_short.py /home/claude/ed/spec_<id>a.json base.mp4 <id>_yt.mp4 --fx fx_<id>.json --platform shorts` →
   `ED_LANG=en python3 voice_gate.py /home/claude/ed/spec_<id>a.json <id>_yt.mp4 <id>_yt.mp4` 가 "통과"여야 한다(영어 받아쓰기 모델 자동 사용).
   화면 확인: 12장 격자 한 장을 Read — 글자 잘림·겹침, 한글, 영어 글꼴이 Cinzel/EB Garamond 인지.
5. 표지: long_<id>.json 에 "cover"(대문자 2~3줄, 금빛은 {…}, TEMPLATE.md ★ 쇼츠 표지 규칙) → `ED_LANG=en python3 cover_ed.py <id>` → docs/emperor/en/cover_<id>.jpg. ed_posts.images.yt_cover 에 경로 기록, 업로드 때 썸네일은 이 파일.
   커밋: `docs/emperor/en/<id>_reels.mp4`, `hook_<id>.jpg`(0초 프레임), `cover_<id>.jpg`, `<id>_reels.mp4.voiceqa.json`, `scripts/side/emperor/long_<id>.json`·`fx_<id>.json`.
6. 기록: 사용 기록 `python3 ../library.py check ../fx_<id>.json --record --ep=<id> --at="<칸 시각>"`(library_usage.jsonl 커밋). ed_posts insert — id `<id>`, kind 'reel_en', title, video_path `/docs/emperor/en/<id>_reels.mp4`, cover_path, scheduled_at(칸 시각), duration_sec, voice_qa(도장 값),
   ig_caption = 유튜브 설명(SHORTS_EN.md 8절: 첫 문장 키워드, 1~2줄 요약, "Subscribe for a new lesson from the Meditations every day.", 출처 한 줄, `#Shorts #Stoicism #MarcusAurelius #<주제>`),
   to_ig/to_th false, ig/th/tt/ig_comment/yt_comment 상태 'skip: EN', images {"yt_tags":[…], "lang":"en", "channel":"@EmperorsDiary-en", "from":"<한국 편 id>"}.
   한 편이 실패해도 나머지는 계속, 실패는 docs alerts 'ed-en-<D>-<id>' 로 남긴다.

## B. 업로드 (예약 작업 "The Emperor's Diary (EN) 쇼츠 업로드", 매일 18:13 KST, 대표님 컴퓨터의 크롬)
1. `select * from ed_posts where kind='reel_en' and yt_video_id is null and paused=false and scheduled_at > now() + interval '20 minutes' order by scheduled_at`. 없으면 끝.
2. 크롬 잠금(docs locks 'chrome-studio', holder 'ed-en-upload') → 자기 새 탭. 스튜디오 헤더가 The Emperor’s Diary 인지 확인(아니면 계정 전환).
3. 편마다 `studio.youtube.com/channel/UCRvSvKOjbsEXKY03TCP9I1w/videos/upload?d=ud` 에서:
   - 파일: raw.githubusercontent.com/immin03/haeja/<커밋>/<video_path> 를 **8MB씩 Range 요청**으로 받아 Blob 으로 합친 뒤 `input[type=file]` 에 DataTransfer 로 넣는다(한 번에 받는 GET 은 실패함, 11/11 확인).
   - 제목·설명(ig_caption)·썸네일(이미지 file input 에 images.yt_cover, 없으면 hook jpg)·"아동용 아님"·고급 설정의 "예, AI가 사용되었습니다"·태그(images.yt_tags)·동영상 언어 영어(미국).
   - 공개 상태: "예약" → scheduled_at 날짜·시각(한국 시간) → 예약. 공개 직전 20분 미만이면 바로 공개.
   - 완료 후 `update ed_posts set yt_video_id='<id>' where id='<post>'`.
4. 탭 닫고 잠금 해제. 마지막 한 줄: "완료: 예약 <n>편" / "할 일 없음" / "실패: <원인>".
