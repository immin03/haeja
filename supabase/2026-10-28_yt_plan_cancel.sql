-- 제작 중 반려 (2026-10-28 운영자: "관리자 제작중에도 반려할수있게 해줘 이유같이 적으면서")
-- 승인(제작 대기)·제작 중(producing) 기획안을 사유와 함께 반려한다.
--  · 상태는 rejected, cancelled = true, cancel_reason·owner_note에 사유, 진행률에 "반려됨 · 제작 중단"
--  · 사유는 docs 'feedback'에도 쌓여 이후 모든 제작이 규칙으로 읽는다 (content_feedback_add와 같은 형식)
--  · 제작 작업이 모르고 상태를 producing/done으로 되돌리려 해도 트리거가 rejected로 붙잡는다
--    (대표님이 '다시 승인 대기로'(proposed)를 누르는 것만 풀린다)

create or replace function public.yt_plan_cancel(p_id text, p_reason text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare pd jsonb; r text := nullif(btrim(coalesce(p_reason, '')), ''); cur text;
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  if r is null then return jsonb_build_object('ok', false, 'reason', '반려 사유를 적어 주세요'); end if;
  select data into pd from docs where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id;
  cur := pd->>'status';
  if cur is null then raise exception 'not found'; end if;
  if cur not in ('approved', 'producing') then
    return jsonb_build_object('ok', false, 'reason', case cur when 'done' then '이미 검수 탭으로 넘어갔습니다. 검수 탭에서 보류해 주세요' else '제작 중인 기획안이 아닙니다' end);
  end if;
  update docs set data = data || jsonb_build_object(
      'status', 'rejected', 'cancelled', true, 'cancelled_at', now(), 'cancelled_from', cur,
      'cancel_reason', r, 'owner_note', r, 'decided_at', now(), 'urgent', false,
      'progress', jsonb_build_object('pct', coalesce((pd->'progress'->>'pct')::int, 0), 'step', '반려됨 · 제작 중단 (' || r || ')', 'at', now())),
    updated_at = now()
  where collection = 'yt_plans' and owner = public.publisher_id() and id = p_id;
  insert into docs (owner, collection, id, updated_at, data)
  values (public.publisher_id(), 'feedback', p_id, now(), jsonb_build_object(
    'id', p_id, 'channel', 'long', 'title', coalesce(pd->>'title', p_id), 'reason', r, 'action', 'cancel', 'at', now(), 'folded', false,
    'history', jsonb_build_array(jsonb_build_object('at', now(), 'reason', r))))
  on conflict (owner, collection, id) do update set
    data = docs.data || jsonb_build_object('reason', r, 'action', 'cancel', 'at', now(), 'folded', false,
      'history', coalesce(docs.data->'history', '[]'::jsonb) || jsonb_build_array(jsonb_build_object('at', now(), 'reason', r))),
    updated_at = now();
  return jsonb_build_object('ok', true, 'was', cur);
end $$;
revoke all on function public.yt_plan_cancel(text, text) from public;
grant execute on function public.yt_plan_cancel(text, text) to authenticated;

-- 반려된 기획안을 제작 작업이 되살리지 못하게 붙잡는 트리거
create or replace function public.yt_plan_cancel_guard()
returns trigger language plpgsql as $$
begin
  if new.collection = 'yt_plans'
     and coalesce((old.data->>'cancelled')::boolean, false)
     and old.data->>'status' = 'rejected'
     and coalesce(new.data->>'status', '') in ('approved', 'producing', 'done') then
    new.data := new.data || jsonb_build_object('status', 'rejected', 'progress', old.data->'progress');
  end if;
  return new;
end $$;
drop trigger if exists yt_plan_cancel_guard on public.docs;
create trigger yt_plan_cancel_guard before update on public.docs
  for each row when (old.collection = 'yt_plans') execute function public.yt_plan_cancel_guard();

-- 다시 승인 대기로 돌릴 때는 반려 표시를 지운다 (yt_plan_set 'proposed'는 그대로 쓰고, 여기서 정리)
create or replace function public.yt_plan_uncancel_clean()
returns trigger language plpgsql as $$
begin
  if new.collection = 'yt_plans' and new.data->>'status' = 'proposed' and coalesce((old.data->>'cancelled')::boolean, false) then
    new.data := new.data - 'cancelled' - 'cancelled_at' - 'cancelled_from' - 'progress';
  end if;
  return new;
end $$;
drop trigger if exists yt_plan_uncancel_clean on public.docs;
create trigger yt_plan_uncancel_clean before update on public.docs
  for each row when (old.collection = 'yt_plans') execute function public.yt_plan_uncancel_clean();
