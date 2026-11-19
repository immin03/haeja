# 원음(뉴스·인물 발언) 확보 절차 — 렌더 전에 끝낸다

2026-11-19 대표 18:07 "렌더는 웬만하면 한 번에" · r178(이슈 롱폼 원음 3개 이상) · r179(원음 짧게 → 한국어 더빙, 자막만 금지) · r180 ③(이름표 3초·자막 위) · r181(원음 구간에도 음악 유지).

**원칙: 원음 클립 파일이 레포(`scripts/blog/media/lib/`)에 실제로 들어온 뒤에만 렌더를 시작한다.**
`prerender_gate.py` ③이 막는다 — 스펙이 참조하는 클립이 없거나, `media/clip-queue.json` 에 아직 대기 중인 클립을 쓰면 실패.
원음을 못 구하면 "원음 없이 다른 성우 더빙"으로 바꾸지 말고(r178), 대표에게 알림을 남기고 그 장면을 빼거나 다른 원음으로 바꾼다.

## 왜 렌더 환경에서 직접 받지 못하나

- GitHub Actions(yt-long)·이 클라우드 작업 환경에서 유튜브는 막혀 있다(봇 확인·IP 차단, yt-dlp 실패).
- 그래서 원음은 **대표 PC의 크롬**에서 받는다. 클라우드 작업은 요청(clip-queue)만 쓴다.

## 순서 (D-2 원고 단계에서 시작, D-1 렌더 전 마감)

1. **원고에서 원음 고르기** — 장면마다 `dub: {clip, start, orig, voice, person}` + 이름표 `sketch: [{kind:"lower", text:"<인물·방송사>"}]` + `src: "<방송사> <날짜>(<나라>) · <무슨 원음>"`.
   이슈 롱폼은 원음 3개 이상. 원음은 2초 안팎, 이어서 한국어 더빙 문장(`lines`).
2. **요청 쓰기** — `media/clip-queue.json` 의 `clips` 에 한 줄씩 추가하고 `[skip ci]` 로 푸시:
   `{"name": "<스펙에 쓸 이름, 확장자 없이>", "url": "https://www.youtube.com/watch?v=…", "start": <초>, "dur": <초 ≤ 120>, "mode": "video"|"audio"}`
   `note` 에 날짜·편 id·용도 한 줄. audio 는 STT로 구간 찾기용(화면에 안 씀).
3. **대표 PC에서 받기 — 크롬 구간 녹화 방식(지금 실제로 되는 방법)**
   - 대표 PC 크롬(로그인된 일반 브라우저)에서 영상을 `start` 지점에 두고 구간을 화면·소리 녹화(크롬 확장 또는 탭 녹화) → `.webm` 저장.
   - 파일 이름 = `<name>.webm` (요청 이름 그대로).
   - GitHub 웹(https://github.com/immin03/haeja/upload/main/scripts/blog/media/lib)에 올리고 커밋 메시지 `clip: <name> [skip ci]`.
     웹 업로드는 파일당 25MB 이하 — 2분 넘는 구간은 나눈다.
   - 11/19 미국 전쟁 편(war_* 8건)이 이 방법으로 13:10~13:17 에 들어왔다(작성자 immin03, 커미터 GitHub = 웹 업로드).
4. **도착 확인** — 클라우드 작업이 `git pull` 후 `ls scripts/blog/media/lib/<name>.*` 로 확인. 도착하면 clip-queue 에서 그 줄을 지우거나 그대로 둬도 된다(관문은 lib 에 파일이 있으면 대기로 보지 않는다).
   필요하면 구간을 잘라 `sot_<편>_<이름>.mp4` 로 만든다(ffmpeg, 뉴스 화면은 렌더러가 66%로 줄여 방송 띠와 자막 겹침을 막는다).
5. **관문 통과 → 렌더** — `python3 scripts/youtube/long/prerender_gate.py <spec>` 이 ③에서 통과해야 specs/ 로 옮겨 렌더.

## clip-queue 수집기가 GitHub 에 못 올리던 문제 (원인 추정: 토큰 없음)

- 증상: 11/17 앤트로픽·테슬라·엔비디아 편 요청 19건(bbg_ant_*, cnbc_*, au_*, musk_conflicted_q3 등)은 `media/clip-queue.json` 에 있지만 lib 에 한 건도 도착하지 않았다.
  레포에 남은 원음 커밋은 11/19 웹 업로드(커미터 GitHub)뿐 — 수집기가 직접 `git push`/API 로 올린 커밋은 한 번도 없다.
- 수집기(대표 PC에서 clip-queue 를 읽어 받는 쪽)는 이 레포에 코드가 없다. 받기까지는 됐더라도 올리는 단계에서 인증이 없어 멈춘 것으로 본다.
- 대표 PC에서 확인하는 방법 (터미널):
  1. `git -C <haeja 폴더> remote -v` — https 주소인지, 토큰이 들어간 주소인지
  2. `gh auth status` — GitHub CLI 로그인 여부 / `echo $GH_TOKEN $GITHUB_TOKEN` — 환경 변수에 토큰이 있는지
  3. `git -C <haeja 폴더> config --get credential.helper` — 비어 있으면 저장된 자격 증명 없음
  4. `git -C <haeja 폴더> push --dry-run` — "Authentication failed"·"could not read Username" 이면 토큰 없음 확정
  5. 수집기 로그에서 다운로드 성공(파일 생성)과 업로드 실패가 갈리는지
- 고치는 방법: GitHub 세분화 토큰(레포 immin03/haeja, Contents: Read and write)을 만들어 PC 환경 변수 `GH_TOKEN` 또는 `gh auth login` 으로 등록 → 수집기가 `gh api -X PUT repos/immin03/haeja/contents/scripts/blog/media/lib/<name>.webm`(100MB 이하) 또는 `git push` 로 올리게 한다. 커밋 메시지는 `clip: <name> [skip ci]`(렌더가 돌지 않게).
- 고치기 전까지는 위 3번(크롬 구간 녹화 → GitHub 웹 업로드)이 기본 경로다.
