# 황제의 일기 데일리 쇼츠 — 매일 자동 제작 순서 (2026-11-04 대표 확정, 고정)

예약 작업 "황제의 일기 데일리 쇼츠 제작"이 매일 04:41(KST)에 이 문서대로 그날 3편을 만들어 예약까지 끝낸다.
규칙의 근거는 TEMPLATE.md 맨 아래 "2026-11-04 대표 확정" 절. 이 문서와 TEMPLATE.md가 다르면 이 문서가 이긴다.

## 고정값
- 게시 시각(KST): **07:40 / 12:20 / 20:30** (유튜브 쇼츠·인스타 릴스·틱톡 같은 시각, 쓰레드 글도 같은 시각)
  · 롱폼 소개 쇼츠가 있는 날은 19:30에 따로 (이 작업이 만들지 않음)
- 길이 실험: **35초 / 45초 / 55초 전후** 세 가지를 시간대마다 날마다 돌린다
  · k = (오늘 날짜의 연중 일수) % 3 → 07:40 = L[(k)%3], 12:20 = L[(k+1)%3], 20:30 = L[(k+2)%3], L = [35, 45, 55]
  · 길이는 대본에서 맞춘다(문장 수·인용 길이). 쉼을 잘라 길이를 맞추지 않는다. ±4초 안이면 통과
  · 결과는 성과 분석 작업이 길이별로 비교한다 (ed_posts.duration_sec 꼭 기록)
- 양식은 A 하나. 장면은 어두운 그림만(ed*, lc*, lib_*, edv*), 편마다 장면 묶음이 겹치지 않게, 어제 쓴 묶음은 피한다
- 목소리: 해설 건석 tc_6731b2e0855f351b98d30c48, 명상록 인용은 황제 명일 tc_62d66c2d1523be99355fda02 (tempo 0.9). 둘 다 tonedown, 묶음별 2테이크
- 마지막 화면: render_ed.py 기본값(롱폼과 같은 금색 디자인). 유튜브용 --platform shorts, 인스타·틱톡용 --platform reels

## 순서
0. 확인: app_config ed_paused 가 true면 멈춤. ed_posts 에 오늘 07:40/12:20/20:30 reel 이 이미 있으면 그 칸은 건너뛴다.
1. 준비: 저장소 sparse clone 후 `scripts/side/emperor`, `social/side/gen`(쓰는 그림만), `docs/emperor/profile_final.png`.
   글꼴 /root/fonts: `Hahmlet[wght].ttf`(google/fonts ofl/hahmlet), `CormorantSC-SemiBold.ttf`(ofl/cormorantsc), `PinyonScript-Regular.ttf`(ofl/pinyonscript),
   Pretendard SemiBold/Bold/ExtraBold(.otf, orioncactus/pretendard). 음악·엔딩 목소리·로고는 `scripts/side/emperor/assets/` → `/home/claude/ed/music/`, `/home/claude/logo/logo_final.png` 로 복사.
2. 기획(3편): 최근 14일 ed_posts 제목과 겹치지 않는 "사람 문제" 주제, 제목은 TEMPLATE.md 제목 규칙(짧게, 핵심만).
   명상록 인용은 권·절을 확실히 아는 것만, George Long(1862) 영역본을 충실히 옮긴 쉬운 한국어. 로마 시대 장면만, 현대 상황은 내레이션 말로만(플랫폼 이름 금지).
3. 대본 파일: 편마다 `long_<id>.json`(구조는 `long_ep08a.json`을 그대로 따름: kicker, hook, title_line, music, cuts, tonight, source, gap, hold, sents)
   sents 시각은 0으로 두고 문장 글·group·cut·style 만 채운다. 묶음 줄 목록은 `/home/claude/vo/v2_lines.json` 에 `{ "<id>": [["n1", 건석, 글], ["e2", 명일, 인용], ...] }`
   (인용 묶음 이름은 e 로 시작). 오늘의 할 일 내레이션(end)도 같은 요청에 넣는다.
4. 녹음: `scripts/side/voices_req.json` 에 묶음마다 A·B 두 테이크(이름 `<id>_<묶음>_<A|B>`), tag `d<yymmdd>` 로 커밋·푸시 → side-gen 워크플로가
   `social/side/voice_samples/<tag>/` 에 올릴 때까지 `gh run list -R immin03/haeja --workflow side-gen.yml` 로 기다린다(최대 40분).
5. 음성 조립: 테이크 고르기(고음역 튐이 적은 쪽) → `ED_LINES=/home/claude/vo/v2_lines.json python3 voice_v2.py <id> <A,B,…> <voice_dir>` → `long_<id>a.json`
6. 일기 쓰는 장면: `python3 tablet_script.py social/side/gen/edv02_tablet.mp4 /home/claude/ed/edv02_<id>.mp4 "<Long 영어 원문 3줄, |로 구분>"`
7. 렌더: `python3 build_long.py long_<id>a.json` → `python3 render_ed.py /home/claude/ed/spec_<id>a.json <yt.mp4> --platform shorts` 와 `--platform reels`
8. 검사(필수): `python3 voice_qa.py <yt.mp4> /home/claude/ed/spec_<id>a.json` 가 "통과"여야 한다. 장면 8장 한 장짜리 격자를 한 번 보고
   글자 잘림·겹침·밝은 그림 위 자막만 고친다. 자막이 말보다 먼저 넘어가지 않는지 인용 구간 프레임 2장으로 확인.
   불통과 2번이면 그 편은 올리지 않고 docs collection 'alerts' 에 남긴다.
9. 올리기: TEMPLATE.md 인코딩대로 `docs/emperor/ep/<id>_reels.mp4`(유튜브), `<id>_reels_ig.mp4`(인스타·틱톡), 표지 `hook_<id>.jpg`(1초 프레임) 커밋·푸시,
   사이트 주소가 200이 될 때까지 기다린 뒤
   유튜브: `ED_KEY=<app_config ed_yt_long_key> ./yt_up.sh <id> <yt.mp4> <meta.json>` (meta = title "<제목> #shorts", description(TEMPLATE 설명란), tags, publish_at = 게시 시각 UTC)
   ed_posts: ep07~09 행과 같은 열로 insert (video_path = _reels_ig, cover_path, yt_video_id, duration_sec, ig_caption, ig_comment, th_text, tt_text, yt_comment, to_ig/to_th true, 상태 pending, paused false)
10. 끝: 커밋 메시지는 한국어, 마지막 줄 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. 결과 한 줄: "완료: <id 제목 길이초> ×3" / "실패: <원인>"

## 하지 않는 것
- tighten.py(쉼 잘라 붙이기), B·C 양식, 밝은 그림, 새 유료 그림·영상 생성, 브라우저 사용(틱톡은 틱톡 업로드 작업이 따로 올림)
- /tmp 에 렌더 임시 파일을 남기지 않는다 (render_ed.py가 자동 삭제)
