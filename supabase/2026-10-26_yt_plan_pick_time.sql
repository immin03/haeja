-- 롱폼 게시 일시 직접 지정 (2026-10-26 운영자): "기획안 영상 승인해서 바로 렌더링할 때, 날짜 시간 지정할 수 있게 해 줘.
-- 너가 지정한 날짜에 무조건 따라가는 게 아니라."
-- 승인할 때 p_target(게시 일시)을 주면 그 시각으로, 비우면 지금처럼 다음 빈 편성일(일·월·수·금 19:00)로 배정한다.
-- 승인된 기획안은 yt_plan_retime으로 게시 일시를 바꿀 수 있다(제작이 시작되기 전까지).
-- 제작 작업(매일 08:47)은 게시 시각 기준 12시간 전 날짜에 만든다: 게시가 그날 12:00~다음 날 11:59면 그날 아침 제작.
-- 그래서 지정 가능한 시각 = 담당 제작 실행(그날 08:47)이 아직 안 지났고, 그 뒤 4시간 13분 이상(렌더링·검수 시간) 남은 시각.

create or replace function public.yt_target_check(p_id text, p_target timestamptz)
returns text language plpgsql stable security definer set search_path to 'public' as $f$
declare loc timestamp := p_target at time zone 'Asia/Seoul'; prod timestamptz; d date := (p_target at time zone 'Asia/Seoul')::date;
begin
  prod := (((loc - interval '12 hours')::date)::timestamp + time '08:47') at time zone 'Asia/Seoul';
  if prod <= now() then
    return '그 시각은 제작(매일 아침 8시 47분)이 이미 지나서 맞출 수 없습니다. 내일 오후 1시 이후로 골라 주세요';
  end if;
  if p_target < prod + interval '4 hours 13 minutes' then
    return '제작·렌더링에 4시간 정도 걸려서 낮 12시~12시 59분은 고를 수 없습니다. 오후 1시 이후나 다음 날 오전으로 골라 주세요';
  end if;
  if exists (select 1 from docs p where p.collection = 'yt_plans' and p.owner = public.publisher_id() and p.id is distinct from p_id
        and p.data->>'target_at' is not null and p.data->>'status' in ('approved','producing','done')
        and ((p.data->>'target_at')::timestamptz at time zone 'Asia/Seoul')::date = d)
     or exists (select 1 from youtube_posts y where y.kind = 'long' and y.status not in ('hold','stale')
        and (y.scheduled_at at time zone 'Asia/Seoul')::date = d) then
    return to_char(d, 'MM/DD') || '에는 이미 롱폼이 잡혀 있습니다. 하루에 롱폼은 1편만 올립니다';
  end if;
  return null;
end $f$;

drop function if exists public.yt_plan_set(text, text, text);
create or replace function public.yt_plan_set(p_id text, p_status text, p_note text default null, p_target timestamptz default null)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare cur text; slot timestamptz; patch jsonb; pd jsonb; bad text; manual boolean := false;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  if p_status not in ('approved','rejected','proposed') then raise exception 'bad status'; end if;
  select data into pd from docs where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id;
  cur := pd->>'status';
  if cur is null then raise exception 'not found'; end if;
  if cur in ('producing','done') then return jsonb_build_object('ok', false, 'reason', '이미 제작 중이거나 끝난 기획안입니다'); end if;
  patch := jsonb_build_object('status', p_status, 'decided_at', now(), 'owner_note', coalesce(p_note, pd->>'owner_note'));
  if p_status = 'approved' then
    if p_target is not null then
      bad := public.yt_target_check(p_id, p_target);
      if bad is not null then return jsonb_build_object('ok', false, 'reason', bad); end if;
      slot := p_target; manual := true;
    elsif coalesce((pd->>'fixed_date')::boolean, false) and pd->>'target_at' is not null and (pd->>'target_at')::timestamptz > now() then
      slot := (pd->>'target_at')::timestamptz;
    else
      slot := public.yt_next_long_slot(p_id);
    end if;
    patch := patch || jsonb_build_object('target_at', to_char(slot at time zone 'Asia/Seoul', 'YYYY-MM-DD"T"HH24:MI:SS"+09:00"'),
      'slot_auto', not manual and not coalesce((pd->>'fixed_date')::boolean, false), 'approved_at', now())
      || case when manual then jsonb_build_object('fixed_date', true, 'slot_by', 'owner') else '{}'::jsonb end;
  end if;
  update docs set data = case when p_status = 'proposed' and not coalesce((pd->>'fixed_date')::boolean, false) then (data || patch) - 'target_at' - 'slot_auto' - 'approved_at'
                              when p_status = 'proposed' then (data || patch) - 'slot_auto' - 'approved_at' else data || patch end, updated_at = now()
    where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id;
  return jsonb_build_object('ok', true, 'target_at', slot);
end $f$;

-- 승인해 둔 기획안의 게시 일시 바꾸기
create or replace function public.yt_plan_retime(p_id text, p_target timestamptz)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare cur text; bad text;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  select data->>'status' into cur from docs where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id;
  if cur is null then raise exception 'not found'; end if;
  if cur <> 'approved' then return jsonb_build_object('ok', false, 'reason', '제작이 시작된 뒤에는 게시 일시를 여기서 바꿀 수 없습니다. 영상 검수에서 바꿔 주세요'); end if;
  bad := public.yt_target_check(p_id, p_target);
  if bad is not null then return jsonb_build_object('ok', false, 'reason', bad); end if;
  update docs set data = data || jsonb_build_object('target_at', to_char(p_target at time zone 'Asia/Seoul', 'YYYY-MM-DD"T"HH24:MI:SS"+09:00"'),
      'slot_auto', false, 'fixed_date', true, 'slot_by', 'owner', 'retimed_at', now()), updated_at = now()
    where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id;
  return jsonb_build_object('ok', true, 'target_at', p_target);
end $f$;

revoke all on function public.yt_target_check(text, timestamptz) from public, anon;
revoke all on function public.yt_plan_set(text, text, text, timestamptz) from public, anon;
revoke all on function public.yt_plan_retime(text, timestamptz) from public, anon;
grant execute on function public.yt_target_check(text, timestamptz) to authenticated;
grant execute on function public.yt_plan_set(text, text, text, timestamptz) to authenticated;
grant execute on function public.yt_plan_retime(text, timestamptz) to authenticated;
