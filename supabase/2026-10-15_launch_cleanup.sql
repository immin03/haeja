-- ValueNote 공개 직전 정리 — Supabase → SQL Editor에 붙여넣고 Run 한 번
-- 1) 회원 탈퇴 기능  2) 오늘 테스트로 생긴 가입 계정·방문 기록 정리 (운영 계정·체험 계정은 그대로)

-- ============ 1) 회원 탈퇴: 본인 계정과 본인 데이터만 지운다 ============
create or replace function public.delete_my_account() returns void
language plpgsql security definer set search_path = public, auth as
$$
declare me uuid := auth.uid();
begin
  if me is null then raise exception 'not signed in'; end if;
  if me = public.publisher_id() or me = public.demo_id() then raise exception 'protected account'; end if;
  delete from public.events where uid = me;
  delete from public.docs where owner = me;
  delete from auth.users where id = me;
end $$;
revoke all on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;

-- ============ 2) 테스트 데이터 정리 ============
-- 운영 계정(immin03@gmail.com)과 체험 계정(demo@valuenote.app)을 뺀 나머지 계정을 지운다 (오늘 테스트용 sori.korea.official@gmail.com)
delete from public.docs where owner in (select id from auth.users where id <> public.publisher_id() and id <> public.demo_id());
delete from auth.users where id <> public.publisher_id() and id <> public.demo_id();
-- 방문·가입 기록을 0에서 시작
delete from public.events;

-- 결과 확인: 계정 2개(운영·체험)만 남아야 한다
select email from auth.users order by created_at;
