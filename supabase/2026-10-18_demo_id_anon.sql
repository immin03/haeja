-- 로그인이 끊긴 기기에서 저장할 때 "permission denied for function demo_id"가 뜨던 문제.
-- demo_id()는 체험 계정 번호만 돌려주므로 비로그인(anon)도 실행 가능하게 둔다.
grant execute on function public.demo_id() to anon;
