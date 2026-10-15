-- 로그인 없이 둘러보기 — Supabase → SQL Editor에 붙여넣고 Run 한 번
-- 비회원(anon)은 운영 계정이 공개하는 공용 자료(기업 점수·개요·트렌드·주가·환율)만 읽을 수 있다.
-- 회원 개인 기록(보유 종목·일지·설정 등)은 지금처럼 본인만 읽는다.

-- 정책 안에서 운영 계정 번호를 확인하는 함수 (운영 계정 번호만 돌려주며 개인 정보는 없음)
grant execute on function public.publisher_id() to anon;

drop policy if exists "guest read" on public.docs;
create policy "guest read" on public.docs for select to anon
  using (collection = any (array['screen','profiles','trends','prices','fx']) and owner = public.publisher_id());

-- 확인: 마지막 줄에 guest read 정책이 보이면 성공
select policyname, roles::text from pg_policies where tablename = 'docs' and policyname = 'guest read';
