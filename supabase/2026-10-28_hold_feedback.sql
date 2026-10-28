-- 보류 사유 피드백 (2026-10-28 운영자: "앞으로 보류할 때 의견 제출해서 계속 반영하게끔 해 줘")
-- 관리자 페이지에서 쇼츠·롱폼·릴스를 보류하면 사유를 적게 하고, 그 사유를 docs collection 'feedback'에 쌓는다.
-- 모든 제작 작업(릴스·쇼츠·롱폼·블로그·카드)은 기획·원고를 쓰기 전에 public.content_feedback_list()를 읽고
-- 각 사유를 지켜야 할 규칙으로 반영한다 (scripts/CONTENT.md 7장).
-- 한 번 규칙으로 옮겨 적은(README 반복 실수 기록 등) 항목은 content_feedback_mark로 folded 표시한다. 목록에서는 계속 보인다.

create or replace function public.content_feedback_add(p_id text, p_channel text, p_title text, p_reason text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare d jsonb; r text := nullif(btrim(coalesce(p_reason, '')), '');
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  if r is null then raise exception 'empty reason'; end if;
  select data into d from docs where owner = public.publisher_id() and collection = 'feedback' and id = p_id;
  insert into docs (owner, collection, id, updated_at, data)
  values (public.publisher_id(), 'feedback', p_id, now(), jsonb_build_object(
    'id', p_id, 'channel', p_channel, 'title', p_title, 'reason', r, 'action', 'hold', 'at', now(), 'folded', false,
    'history', coalesce(d->'history', '[]'::jsonb) || jsonb_build_array(jsonb_build_object('at', now(), 'reason', r))))
  on conflict (owner, collection, id) do update set data = excluded.data, updated_at = now();
  return jsonb_build_object('ok', true);
end $$;

-- 관리자(로그인) 또는 서버 작업(execute_sql, auth.role() 없음)만 읽는다
create or replace function public.content_feedback_list(p_days int default 120)
returns jsonb language plpgsql security definer set search_path = public as $$
begin
  if coalesce(auth.role(), '') = 'anon' or (coalesce(auth.role(), '') = 'authenticated' and not public.is_admin()) then raise exception 'not admin'; end if;
  return coalesce((select jsonb_agg(data order by updated_at desc) from docs
    where owner = public.publisher_id() and collection = 'feedback' and updated_at > now() - make_interval(days => p_days)), '[]'::jsonb);
end $$;

create or replace function public.content_feedback_mark(p_id text, p_where text default null)
returns jsonb language plpgsql security definer set search_path = public as $$
begin
  if coalesce(auth.role(), '') = 'anon' or (coalesce(auth.role(), '') = 'authenticated' and not public.is_admin()) then raise exception 'not admin'; end if;
  update docs set data = data || jsonb_build_object('folded', true, 'folded_at', now(), 'folded_into', p_where), updated_at = updated_at
    where owner = public.publisher_id() and collection = 'feedback' and id = p_id;
  return jsonb_build_object('ok', found);
end $$;

revoke all on function public.content_feedback_add(text, text, text, text) from public, anon;
revoke all on function public.content_feedback_list(int) from public, anon;
revoke all on function public.content_feedback_mark(text, text) from public, anon;
grant execute on function public.content_feedback_add(text, text, text, text) to authenticated;
grant execute on function public.content_feedback_list(int) to authenticated;
grant execute on function public.content_feedback_mark(text, text) to authenticated;
