-- 관리자: 정리본 '새 정리본 받기' 구독자 목록
create or replace function public.admin_leads()
returns jsonb language plpgsql stable security definer set search_path to 'public','auth' as $$
begin
  if not public.is_admin() and current_user not in ('postgres','service_role') then raise exception 'not admin'; end if;
  return coalesce((
    select jsonb_agg(jsonb_build_object(
      'email', l.email, 'guide', l.guide, 'src', l.src, 'at', l.created_at,
      'member', exists(select 1 from auth.users u where lower(u.email) = lower(l.email))
    ) order by l.created_at desc)
    from leads l), '[]'::jsonb);
end $$;
revoke all on function public.admin_leads() from public, anon;
grant execute on function public.admin_leads() to authenticated;
