-- 맞춤 푸시(push-digest): 매일 08:40 KST 전체, 19:10 KST 칼럼·관심 회사 큰 변화만
-- 관심 회사(interests)·알림 종류(push_prefs)·보낸 기록(push_state)은 docs 표에 사용자별로 저장된다(기존 RLS 그대로).
select cron.unschedule(jobid) from cron.job where jobname in ('haeja-push-am', 'haeja-push-pm');
select cron.schedule('haeja-push-am', '40 23 * * *', $$select public._fn_call('push-digest', '{}')$$);
select cron.schedule('haeja-push-pm', '10 10 * * *', $$select public._fn_call('push-digest', '{"mode":"evening"}')$$);
