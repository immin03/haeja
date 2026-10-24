-- 롱폼 기획안 운영 개편 (2026-10-24 운영자):
-- 1) 승인한 순서대로 다음 빈 롱폼 편성일(일·월·수·금 19:00 KST)을 자동 배정한다.
-- 2) 관리자 페이지에서 '추가 기획안 요청'과 기획안별 '의견'을 남기면, 매시간 도는 처리 작업(Claude)이
--    새 기획안을 올리거나 의견대로 기획안을 고친다. 저장: docs collection 'yt_plan_requests', owner = publisher.

-- 다음 빈 롱폼 편성일: 내일부터 찾는다(당일 08:47 제작 작업이 그날 편성분을 만든다).
create or replace function public.yt_next_long_slot(p_skip text default null)
returns timestamptz language plpgsql stable security definer set search_path to 'public' as $f$
declare d date := (now() at time zone 'Asia/Seoul')::date + 1; i int;
begin
  for i in 0..120 loop
    if extract(dow from d + i) in (0, 1, 3, 5)
      and not exists (select 1 from docs p where p.collection = 'yt_plans' and p.owner = public.publisher_id() and p.id is distinct from p_skip
            and p.data->>'status' in ('approved','producing','done') and p.data->>'target_at' is not null
            and ((p.data->>'target_at')::timestamptz at time zone 'Asia/Seoul')::date = d + i)
      and not exists (select 1 from youtube_posts y where y.kind = 'long' and y.status <> 'hold'
            and (y.scheduled_at at time zone 'Asia/Seoul')::date = d + i)
    then return ((d + i)::timestamp + time '19:00') at time zone 'Asia/Seoul'; end if;
  end loop;
  return null;
end $f$;

create or replace function public.yt_plan_set(p_id text, p_status text, p_note text default null)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare cur text; slot timestamptz; patch jsonb;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  if p_status not in ('approved','rejected','proposed') then raise exception 'bad status'; end if;
  select data->>'status' into cur from docs where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id;
  if cur is null then raise exception 'not found'; end if;
  if cur in ('producing','done') then return jsonb_build_object('ok', false, 'reason', '이미 제작 중이거나 끝난 기획안입니다'); end if;
  patch := jsonb_build_object('status', p_status, 'decided_at', now(), 'owner_note', coalesce(p_note, (select data->>'owner_note' from docs where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id)));
  if p_status = 'approved' then
    slot := public.yt_next_long_slot(p_id);
    patch := patch || jsonb_build_object('target_at', to_char(slot at time zone 'Asia/Seoul', 'YYYY-MM-DD"T"HH24:MI:SS"+09:00"'), 'slot_auto', true, 'approved_at', now());
  end if;
  update docs set data = case when p_status = 'proposed' then (data || patch) - 'target_at' - 'slot_auto' - 'approved_at' else data || patch end, updated_at = now()
    where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id;
  return jsonb_build_object('ok', true, 'target_at', slot);
end $f$;

-- 요청 남기기: p_kind 'more'(추가 기획안 n편) | 'revise'(이 기획안을 의견대로 고치기)
create or replace function public.yt_plan_request(p_kind text, p_note text default null, p_plan_id text default null, p_count int default 5)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare rid text := 'R' || to_char(now() at time zone 'Asia/Seoul', 'YYMMDDHH24MISS') || substr(md5(random()::text), 1, 4); pst text;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  if p_kind not in ('more','revise') then raise exception 'bad kind'; end if;
  if p_kind = 'revise' then
    if coalesce(btrim(p_note), '') = '' then return jsonb_build_object('ok', false, 'reason', '의견을 적어 주세요'); end if;
    select data->>'status' into pst from docs where collection = 'yt_plans' and owner = public.publisher_id() and id = p_plan_id;
    if pst is null then raise exception 'not found'; end if;
    if pst in ('producing','done') then return jsonb_build_object('ok', false, 'reason', '이미 제작이 시작된 기획안입니다. 영상 검수에서 수정 요청을 남겨 주세요'); end if;
    update docs set data = data || jsonb_build_object('comments', coalesce(data->'comments', '[]'::jsonb) || jsonb_build_array(jsonb_build_object('at', now(), 'by', 'owner', 'text', btrim(p_note), 'req', rid))), updated_at = now()
      where collection = 'yt_plans' and owner = public.publisher_id() and id = p_plan_id;
  end if;
  insert into docs (owner, collection, id, data, updated_at) values (public.publisher_id(), 'yt_plan_requests', rid,
    jsonb_build_object('kind', p_kind, 'note', nullif(btrim(coalesce(p_note, '')), ''), 'plan_id', p_plan_id, 'count', greatest(1, least(coalesce(p_count, 5), 10)), 'status', 'pending', 'at', now()), now());
  return jsonb_build_object('ok', true, 'id', rid);
end $f$;

create or replace function public.yt_plan_req_list()
returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  return coalesce((select jsonb_agg(d.data || jsonb_build_object('id', d.id) order by d.id desc)
    from docs d where d.collection = 'yt_plan_requests' and d.owner = public.publisher_id()
      and (d.data->>'status' in ('pending','working') or d.updated_at > now() - interval '3 days')), '[]'::jsonb);
end $f$;

revoke all on function public.yt_next_long_slot(text) from public, anon;
revoke all on function public.yt_plan_request(text, text, text, int) from public, anon;
revoke all on function public.yt_plan_req_list() from public, anon;
grant execute on function public.yt_next_long_slot(text) to authenticated;
grant execute on function public.yt_plan_request(text, text, text, int) to authenticated;
grant execute on function public.yt_plan_req_list() to authenticated;
