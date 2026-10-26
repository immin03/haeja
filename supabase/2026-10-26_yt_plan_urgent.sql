-- 롱폼 긴급 제작 (2026-10-26 운영자): "긴급으로 누르는 경우에는 바로 제작할 수 있게 해 줘."
-- 관리자 기획안 카드의 '긴급 · 바로 제작' → yt_plan_urgent: 승인 + urgent 표시 + 게시 일시(지정 없으면 지금부터 5시간 30분 뒤, 30분 단위 올림).
-- 매시 35분에 도는 '롱폼 긴급 제작 감시' 작업이 urgent 기획안을 찾아 롱폼 제작 작업을 즉시 실행한다(아침 8시 47분을 기다리지 않음).
-- 렌더링·검수 시간 때문에 게시 일시는 지금부터 최소 5시간 뒤. 하루 1편 규칙은 그대로.

create or replace function public.yt_plan_urgent(p_id text, p_target timestamptz default null)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare pd jsonb; t timestamptz; d date;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  select data into pd from docs where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id;
  if pd is null then raise exception 'not found'; end if;
  if pd->>'status' not in ('proposed', 'approved') then return jsonb_build_object('ok', false, 'reason', '이미 제작 중이거나 끝난 기획안입니다'); end if;
  t := coalesce(p_target, to_timestamp(ceil(extract(epoch from now() + interval '5 hours 30 minutes') / 1800) * 1800));
  if t < now() + interval '5 hours' then
    return jsonb_build_object('ok', false, 'reason', '제작 시작까지 최대 1시간, 제작·렌더링에 4시간 정도 걸립니다. 게시 일시를 지금부터 5시간 뒤 이후로 골라 주세요');
  end if;
  d := (t at time zone 'Asia/Seoul')::date;
  if exists (select 1 from docs p where p.collection = 'yt_plans' and p.owner = public.publisher_id() and p.id <> p_id
        and p.data->>'target_at' is not null and p.data->>'status' in ('approved','producing','done')
        and ((p.data->>'target_at')::timestamptz at time zone 'Asia/Seoul')::date = d)
     or exists (select 1 from youtube_posts y where y.kind = 'long' and y.status not in ('hold','stale')
        and (y.scheduled_at at time zone 'Asia/Seoul')::date = d) then
    return jsonb_build_object('ok', false, 'reason', to_char(d, 'MM/DD') || '에는 이미 롱폼이 잡혀 있습니다. 다른 날을 고르거나 그날 롱폼을 먼저 보류해 주세요');
  end if;
  update docs set data = (data || jsonb_build_object('status', 'approved', 'decided_at', now(), 'approved_at', coalesce(data->>'approved_at', now()::text),
      'target_at', to_char(t at time zone 'Asia/Seoul', 'YYYY-MM-DD"T"HH24:MI:SS"+09:00"'), 'slot_auto', false, 'fixed_date', true, 'slot_by', 'owner',
      'urgent', true, 'urgent_at', now(), 'progress', jsonb_build_object('pct', 1, 'step', '긴급 제작 대기 · 1시간 안에 시작', 'at', now()))) - 'urgent_fired_at', updated_at = now()
    where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id;
  return jsonb_build_object('ok', true, 'target_at', t);
end $f$;

revoke all on function public.yt_plan_urgent(text, timestamptz) from public, anon;
grant execute on function public.yt_plan_urgent(text, timestamptz) to authenticated;
