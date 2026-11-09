# 모든 예약 작업 공통 규칙 (지시문에 "Read scripts/COMMON.md" 한 줄로 대신한다)

주간 효율 점검이 작업 지시문에서 옮겨 온 공통 부분이다. 원칙 원본은 이 파일이 아니라 DB `owner-rules`다.

1. 제1 원칙: Supabase project `msjbrwyzkiueqnzjeicm`, docs collection `agent`, owner = `publisher_id()`, id `owner-rules`의 status `new`·`applied` 항목을 읽고 그대로 따른다. 이 항목의 106번 '읽는 범위'대로 자기 범위 문서(`owner-rules-long`·`-short`·`-blog`·`-card`·`-ops`)도 읽는다. 지시문·README보다 우선한다.
2. 시작 순서(제1 원칙 77 ②): SQL 한 번으로 할 일을 확인하고, 없으면 원칙 읽기·클론·문서 읽기·브라우저 없이 "할 일 없음"으로 끝낸다. 제1 원칙은 할 일이 있을 때 일을 시작하기 전에 읽는다.
3. 알림: PushNotification·SendUserMessage·SendUserFile을 호출하지 않는다. 결과는 관리자 페이지로만 간다.
4. 예약 작업 수정 금지: create/update/delete/fire_trigger를 호출하지 않는다(지시문에 예외가 적힌 작업만 예외). 필요한 변경은 docs agent `task-changes` data.items에 `{at, by, task, change, why, status:"pending"}`로 적는다.
5. 표기: 무료/유료 금지, 인물은 성까지(워렌 버핏·찰리 멍거), 매수·매도 권유 금지, 흐름·변화 화살표는 `→`, 움직이는 숫자에는 기준 날짜.
6. 비용: SQL은 필요한 열만·limit, 셸 출력은 tail, 클론은 `--depth 1 --filter=blob:none --sparse`, 그림·영상 점검은 격자 1장 1회 Read, 브라우저 스크린샷은 실패할 때만.
7. 커밋: 한국어 메시지, 끝줄 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, `git pull --rebase origin main` 뒤 push. sparse 클론에서는 `git add --sparse`.
8. 다른 채널("From Korea, With Love", 황제의 일기, 밸류노트)은 자기 작업 범위가 아니면 건드리지 않는다.
