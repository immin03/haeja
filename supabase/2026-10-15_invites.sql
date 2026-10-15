-- 친구 초대 집계 — Supabase → SQL Editor에 붙여넣고 Run 한 번
-- 초대 링크는 /?ref=inv-<회원번호 앞 8자리>. 그 링크로 처음 들어와 가입한 계정 수를 센다.

-- 서버(분석 함수)가 쓰는 집계: 특정 회원의 초대 가입 수
create or replace function public.invite_count(p_uid uuid) returns integer
language sql stable security definer set search_path = public as
$$
  select count(distinct e.uid)::int from public.events e
  where e.kind = 'signup' and e.uid is not null and e.uid <> p_uid
    and e.ref = 'inv-' || left(replace(p_uid::text, '-', ''), 8)
$$;
revoke all on function public.invite_count(uuid) from public, anon, authenticated;
grant execute on function public.invite_count(uuid) to service_role;

-- 앱 화면용: 로그인한 본인의 초대 가입 수만
create or replace function public.my_invites() returns integer
language sql stable security definer set search_path = public as
$$ select case when auth.uid() is null then 0 else public.invite_count(auth.uid()) end $$;
revoke all on function public.my_invites() from public, anon;
grant execute on function public.my_invites() to authenticated;

-- 확인: 두 함수가 보이면 성공
select proname from pg_proc where proname in ('invite_count', 'my_invites');
