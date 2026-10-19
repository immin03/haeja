-- 2026-10-19: 주요 일정 알림 (경제 레이더 > 다가오는 주요 일정)
-- 매일 한국 시각 18시(UTC 09시)에 calendar 함수를 부른다.
--  - 보유·관심 종목 실적 발표일을 모아 fx/earnings(운영자 소유 공용 문서)에 저장
--  - settings.main.calAlert = true 인 사용자에게 "내일" 경제 일정·실적 발표 알림을 넣음 (푸시는 docs_alert_push 트리거)
-- 이미 적용됨. 다시 실행해도 안전함.
select cron.unschedule('haeja-calendar') where exists (select 1 from cron.job where jobname = 'haeja-calendar');
select cron.schedule('haeja-calendar', '0 9 * * *', $$select public._fn_call('calendar', '{}')$$);
