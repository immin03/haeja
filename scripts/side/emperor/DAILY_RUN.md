# 황제의 일기 데일리 쇼츠 — 매일 자동 제작 순서 (2026-11-04 대표 확정, 고정)

예약 작업 "황제의 일기 데일리 쇼츠 제작"이 매일 04:41(KST)에 이 문서대로 그날 2편을 만들어 예약까지 끝낸다. (2026-11-04 19:47 대표 변경: 데일리 3편 → 2편)
★ 규칙의 원본은 TEMPLATE.md 하나다. 제목·썸네일·설명란·댓글 규칙은 **이 문서에 다시 적지 않는다** — 반드시 TEMPLATE.md 해당 절을 읽고 그대로 따른다.
(2026-11-08 사고: 이 문서가 11/6 제목 양식을 베껴 적어 두고 "이 문서가 이긴다"고 해서, 11/7 대표가 TEMPLATE.md 제목 규칙을 바꿨는데도 14~17편이 옛 양식으로 나갔다. 같은 규칙을 두 곳에 적지 않는다. TEMPLATE.md 와 이 문서가 다르면 **TEMPLATE.md 가 이긴다.**)

## 고정값
- ★ 장면: `scripts/side/ed_long/LIBRARY.md` 3장 — 새 그림·영상 생성 금지, 라이브러리(CLIPS.json)에서만 고르고 최근 7일 안에 쓴 클립은 피하며 쓰지 않는 클립은 제외
- ★ 제목: **TEMPLATE.md '★ 제목 규칙' 절을 읽고 그대로** (여기에 요약하지 않음). 기획 단계에서 그 절의 "자가 검사" 줄을 하나씩 확인하고 통과해야 다음 단계로 간다
- ★ 썸네일: **TEMPLATE.md '★ 썸네일 규칙' 절을 읽고 그대로**
- 게시 시각(KST): **12:20 / 20:30** 두 편 (유튜브 쇼츠·인스타 릴스·틱톡 같은 시각, 쓰레드 글도 같은 시각)
  · 07:40 은 롱폼 소개 쇼츠 전용 칸(롱폼 다음 날 오전, 이 작업이 만들지 않음). 롱폼이 없는 날도 07:40 데일리는 만들지 않는다
  · 롱폼 본편은 19:30
- 길이 실험 (2026-11-08 대표: "길이 긴 것들 더 끼워 넣어서 테스트"): **20:30 칸은 매일 75초 전후, 12:20 칸은 40초/55초 교대** (이전 35/45/55 대체)
  · 12:20 = (오늘 날짜의 연중 일수) % 2 == 0 ? 40 : 55 / 20:30 = 75. 하루 두 편 중 한 편(50%)이 61~90초 구간
  · 근거(11/8 유튜브 API 실측 220편): 10만~100만 회 편 91개 중 42%가 61~90초, 12%가 90초+. 중간값 61초. 1만~10만에 그친 편은 54%가 45초 이하. 60초 초과 편 좋아요율 2.1% vs 45초 이하 0.85%
  · 75초 편은 "N가지" 제목(이유·방법 3~5개, 화면에 I·II·III)으로 — 항목이 있어야 길어도 안 늘어진다. 벤치 N가지 제목 25편 중간 66초
  · 결과 비교 기준은 조회수가 아니라 스튜디오 '계속 시청함'(안 넘김 비율)과 좋아요율. 2주 뒤(11/22) 길이별 비교
  · 길이는 대본에서 맞춘다(문장 수·인용 길이). 쉼을 잘라 길이를 맞추지 않는다. ±4초 안이면 통과
  · 결과는 성과 분석 작업이 길이별로 비교한다 (ed_posts.duration_sec 꼭 기록)
- 양식은 A 하나. 장면은 어두운 그림만(ed*, lc*, lib_*, edv*), 편마다 장면 묶음이 겹치지 않게, 어제 쓴 묶음은 피한다
- 목소리: 해설 건석 tc_6731b2e0855f351b98d30c48, 명상록 인용은 황제 명일 tc_62d66c2d1523be99355fda02 (tempo 0.9). 둘 다 tonedown, 묶음별 2테이크
- 화면: 시네마틱 고정 포맷(FX.md). 마지막 화면은 슬로건+엔딩 한 화면(fx_short.py). 유튜브용 --platform shorts, 인스타·틱톡용 --platform reels

## 순서
0. 확인: app_config ed_paused 가 true면 멈춤. ed_posts 에 오늘 12:20/20:30 데일리 reel 이 이미 있으면 그 칸은 건너뛴다.
1. 준비: 저장소 sparse clone 후 `scripts/side/emperor`, `social/side/gen`(쓰는 그림만), `docs/emperor/profile_final.png`.
   글꼴 /root/fonts: `Hahmlet[wght].ttf`(google/fonts ofl/hahmlet), `CormorantSC-SemiBold.ttf`(ofl/cormorantsc), `PinyonScript-Regular.ttf`(ofl/pinyonscript),
   Pretendard SemiBold/Bold/ExtraBold(.otf, orioncactus/pretendard). 음악·엔딩 목소리·로고는 `scripts/side/emperor/assets/` → `/home/claude/ed/music/`, `/home/claude/logo/logo_final.png` 로 복사.
2. 기획(2편): 최근 14일 ed_posts 제목과 겹치지 않는 "사람 문제" 주제. 제목은 **TEMPLATE.md '★ 제목 규칙' 그대로** — 이 단계 끝에 그 절의 자가 검사를 통과하지 못하면 다시 짓는다. 첫 화면 훅 2줄 = 제목(`| 명상록` 꼬리는 첫 화면에 넣지 않고 유튜브 제목에만).
   명상록 인용은 권·절을 확실히 아는 것만, George Long(1862) 영역본을 충실히 옮긴 쉬운 한국어. 로마 시대 장면만, 현대 상황은 내레이션 말로만(플랫폼 이름 금지).
3. 대본 파일: 편마다 `long_<id>.json`(구조는 `long_ep08a.json`을 그대로 따름: kicker, hook, title_line, music, cuts, tonight, source, gap, hold, sents)
   sents 시각은 0으로 두고 문장 글·group·cut·style 만 채운다. 묶음 줄 목록은 `/home/claude/vo/v2_lines.json` 에 `{ "<id>": [["n1", 건석, 글], ["e2", 명일, 인용], ...] }`
   (인용 묶음 이름은 e 로 시작). 오늘의 할 일 내레이션(end)도 같은 요청에 넣는다 — 글은 반드시 "오늘의 할 일. " + 이 편 tonight 두 줄 그대로.
   ★ 2026-11-04 8편 사고 재발 방지: 다른 편·예전 폴더의 녹음은 어떤 경우에도 쓰지 않는다. long_<id>.json 의 end_voice 는 오늘 받은
   voice_samples/<tag>/…_end_<A|B>.mp3 를 그대로 가리킨다(옆의 .txt 원문으로 voice_v2.py 가 대조, 다르면 멈춤).
4. 녹음: `scripts/side/voices_req.json` 에 묶음마다 A·B 두 테이크(이름 `<id>_<묶음>_<A|B>`), tag `d<yymmdd>` 로 커밋·푸시 → side-gen 워크플로가
   `social/side/voice_samples/<tag>/` 에 올릴 때까지 `gh run list -R immin03/haeja --workflow side-gen.yml` 로 기다린다(최대 40분).
5. 음성 조립: 테이크 고르기 — `python3 take_check.py <mp3> "<대본 글>"` 가 통과한 것 중 고음역 튐이 적은 쪽 (소리 끌림·원문 불일치는 불통과, 둘 다 불통과면 그 묶음만 다시 녹음) → `ED_LINES=/home/claude/vo/v2_lines.json python3 voice_v2.py <id> <A,B,…> <voice_dir>` → `long_<id>a.json`
6. 일기 쓰는 장면: `python3 tablet_script.py social/side/gen/edv02_tablet.mp4 /home/claude/ed/edv02_<id>.mp4 "<Long 영어 원문 3줄, |로 구분>"`
7. 렌더: `python3 build_long.py long_<id>a.json` → `python3 render_ed.py /home/claude/ed/spec_<id>a.json <base.mp4> --platform shorts`
   → ★ 시네마틱 고정 포맷(2026-11-05 대표 확정, FX.md 필독): CLIPS.json 에서 장면을 골라 `fx_<id>.json` 을 쓰고
   `python3 fx_short.py /home/claude/ed/spec_<id>a.json <base.mp4> <yt.mp4> --fx fx_<id>.json --platform shorts` 와 `... <ig.mp4> ... --platform reels`
   (render_ed 의 reels 렌더는 하지 않는다. 클립은 social/side/gen/<클립>.mp4 를 sparse-checkout 에 추가)
8. 검사(필수): `python3 voice_qa.py <base.mp4> /home/claude/ed/spec_<id>a.json` 가 "통과"여야 한다(조각 대조 + 소리 끌림). 오늘의 할 일 구간은 화면 글과 녹음 원문(.txt)이 같은지 한 번 더 눈으로 확인. 장면 8장 한 장짜리 격자를 한 번 보고
   글자 잘림·겹침·밝은 그림 위 자막만 고친다. 자막이 말보다 먼저 넘어가지 않는지 인용 구간 프레임 2장으로 확인.
   불통과 2번이면 그 편은 올리지 않고 docs collection 'alerts' 에 남긴다.
9. 올리기: fx_short.py 결과 그대로(인코딩 포함) `docs/emperor/ep/<id>_reels.mp4`(유튜브), `<id>_reels_ig.mp4`(인스타·틱톡), 표지 `hook_<id>.jpg`(0초 프레임: `ffmpeg -ss 0 -i <yt.mp4> -frames:v 1 -q:v 2 hook_<id>.jpg` — 자막 없는 첫 화면인지 Read 로 한 번 확인) 커밋·푸시,
   사이트 주소가 200이 될 때까지 기다린 뒤
   유튜브: `ED_KEY=<app_config ed_yt_long_key> ./yt_up.sh <id> <yt.mp4> <meta.json> hook_<id>.jpg`
   meta.json = {"title": "<제목> | 명상록"(해시태그 없음, 40자 이내 — yt_up.sh 가 어기면 멈춤), "description": TEMPLATE 설명란(#shorts 는 여기 끝에), "tags": TEMPLATE '태그 세트', "publish_at": 게시 시각 UTC}
   썸네일: yt_up.sh 가 끝에 yt_thumb.sh 로 hook_<id>.jpg 를 지정한다(200 이 아니면 실패). 실제 화면 확인은 Chrome 작업 몫(TEMPLATE 썸네일 규칙)
   ★ 댓글(2026-11-05 대표): yt_comment·ig_comment 는 질문 뒤 빈 줄 하나 + "좋아요와 구독은 영상 제작에 큰 힘이 됩니다. 감사합니다."(인스타는 '구독' → '팔로우') 로 끝낸다
   ed_posts: ep07~09 행과 같은 열로 insert (video_path = _reels_ig, cover_path, yt_video_id, duration_sec, ig_caption, ig_comment, th_text, tt_text, yt_comment, to_ig/to_th true, 상태 pending, paused false)
10. 끝: 커밋 메시지는 한국어, 마지막 줄 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. 결과 한 줄: "완료: <id 제목 길이초> ×2" / "실패: <원인>"

## ★ 멈춤·침묵 재발 방지 (2026-11-06 대표 지시, 필수)
사고: 11/6 04:41 회차가 시작 30분 만에 오류로 끊겼다(커밋·녹음 요청·알림 0건). 아무것도 남기지 않고 죽어서 대표가 09:33에 직접 발견했다.
1. 진행 기록(heartbeat): 시작 즉시, 그리고 0~10 각 단계에 들어갈 때마다
   `insert into docs (owner, collection, id, data) values (publisher_id(),'agent','ed-daily-run', jsonb_build_object('day','<yymmdd>','step','<번호 이름>','status','running','at',now())) on conflict (owner, collection, id) do update set data = excluded.data, updated_at = now();`
   끝나면 status 'done'(두 편 예약 완료) 또는 'failed'(+ 'why'). 감시 작업이 이것으로 살아 있는지 판단한다.
2. 명령 시간 제한: 셸 명령 하나는 최대 10분(timeout 600000). curl/wget 은 `--max-time 90 --retry 2`, git clone/fetch 는 `timeout 540`.
   10분 넘게 걸릴 수 있는 일(녹음 워크플로 대기, 긴 렌더)은 한 번에 기다리지 말고 8분 이하로 나눠 되풀이 확인한다. 한 호출로 40분 기다리기 금지.
3. 같은 단계가 두 번 실패하면 그 자리에서 멈추지 말고: alerts 에 `ed-daily-<yymmdd>-fail`(level warn, title "황제의 일기 데일리 쇼츠 제작 실패", body "<단계> · <원인 한 줄>")을 먼저 쓰고, heartbeat status 'failed' 로 바꾼 뒤 끝낸다. 알림 없이 끝나는 일은 없어야 한다.
4. 이미 만든 결과(녹음·렌더·업로드)는 다음 회차가 이어 쓸 수 있게 단계마다 바로 커밋·푸시한다. 0단계는 ed_posts 와 저장소(voice_samples/d<yymmdd>, docs/emperor/ep/<id>*)를 보고 끝난 단계는 건너뛴다.
5. 감시 작업 "황제의 일기 데일리 쇼츠 감시"(06:23·10:23·16:23)가 오늘 칸이 비어 있고 제작이 살아 있지 않으면(heartbeat 40분 이상 멈춤 또는 failed) 이 작업을 다시 돌리고 /side 알림을 남긴다.

## 하지 않는 것
- tighten.py(쉼 잘라 붙이기), B·C 양식, 밝은 그림, 새 유료 그림·영상 생성, 브라우저 사용(틱톡은 틱톡 업로드 작업이 따로 올림)
- /tmp 에 렌더 임시 파일을 남기지 않는다 (render_ed.py가 자동 삭제)
