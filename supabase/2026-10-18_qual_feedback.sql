-- 정성 평가에 대한 사용자 의견 (2026-10-18)
-- 사용자는 docs(collection='qual_feedback')에 자기 의견만 쓴다(기존 owner 정책). 점수는 바꾸지 않는다.
-- 운영자는 아래 두 함수로 전체 의견을 읽고, 답변·처리 상태를 남긴다.

create or replace function public.admin_qual_feedback() returns jsonb
language sql stable security definer set search_path = public, auth as
$$
  select coalesce(jsonb_agg(jsonb_build_object(
           'owner', d.owner, 'id', d.id, 'email', u.email, 'at', d.data ->> 'at',
           'key', d.data ->> 'key', 'ticker', d.data ->> 'ticker', 'name', d.data ->> 'name', 'market', d.data ->> 'market',
           'text', d.data ->> 'text', 'status', coalesce(d.data ->> 'status', 'new'), 'reply', d.data ->> 'reply',
           'shared', coalesce((d.data ->> 'shared')::boolean, false), 'qualAt', d.data ->> 'qualAt', 'snapshot', d.data -> 'snapshot')
         order by d.data ->> 'at' desc), '[]')
  from public.docs d left join auth.users u on u.id = d.owner
  where d.collection = 'qual_feedback' and public.is_admin();
$$;
revoke all on function public.admin_qual_feedback() from public, anon;
grant execute on function public.admin_qual_feedback() to authenticated;

create or replace function public.admin_qual_feedback_set(p_owner uuid, p_id text, p_status text, p_reply text) returns void
language plpgsql security definer set search_path = public as
$$
begin
  if not public.is_admin() then raise exception 'not admin'; end if;
  update public.docs set data = data || jsonb_build_object('status', p_status, 'reply', nullif(p_reply, ''), 'repliedAt', now()),
         updated_at = now()
   where collection = 'qual_feedback' and owner = p_owner and id = p_id;
end $$;
revoke all on function public.admin_qual_feedback_set(uuid, text, text, text) from public, anon;
grant execute on function public.admin_qual_feedback_set(uuid, text, text, text) to authenticated;
