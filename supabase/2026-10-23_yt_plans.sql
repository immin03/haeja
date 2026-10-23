-- 롱폼 기획안 승인제 (2026-10-23 운영자): 기획안을 먼저 승인받고, 승인된 것만 원고·렌더링한다.
-- 저장: docs collection 'yt_plans', owner = publisher. 상태: proposed → approved → producing → done / rejected
create or replace function public.yt_plan_list()
returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  return coalesce((select jsonb_agg(d.data || jsonb_build_object('id', d.id, 'updated_at', d.updated_at)
      order by case d.data->>'status' when 'proposed' then 0 when 'approved' then 1 when 'producing' then 2 else 3 end,
               coalesce((d.data->>'rank')::int, 99), d.updated_at desc)
    from docs d where d.collection = 'yt_plans' and d.owner = public.publisher_id()
      and (d.data->>'status' in ('proposed','approved','producing') or d.updated_at > now() - interval '14 days')), '[]'::jsonb);
end $f$;

create or replace function public.yt_plan_set(p_id text, p_status text, p_note text default null)
returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare cur text;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  if p_status not in ('approved','rejected','proposed') then raise exception 'bad status'; end if;
  select data->>'status' into cur from docs where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id;
  if cur is null then raise exception 'not found'; end if;
  if cur in ('producing','done') then return jsonb_build_object('ok', false, 'reason', '이미 제작 중이거나 끝난 기획안입니다'); end if;
  update docs set data = data || jsonb_build_object('status', p_status, 'decided_at', now(), 'owner_note', coalesce(p_note, data->>'owner_note')), updated_at = now()
    where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id;
  return jsonb_build_object('ok', true);
end $f$;

revoke all on function public.yt_plan_list() from public, anon;
revoke all on function public.yt_plan_set(text, text, text) from public, anon;
grant execute on function public.yt_plan_list() to authenticated;
grant execute on function public.yt_plan_set(text, text, text) to authenticated;
