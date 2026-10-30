-- 2026-10-30 대표님 긴급 요청(할로윈, R261030091555cb94) · 제1 원칙 19:
-- "대표님이 정한 시각이 있는 콘텐츠는 그 시각에 올린다" — 칸 재배치 함수가 대표 지정 시각을 옮기지 않게 한다.
-- ① 인스타: id 가 H 로 시작하는 릴스(대표 긴급 요청 편)는 U·E·Q 처럼 움직이지 않고 앞뒤 60분을 막는다.
-- ② 유튜브 쇼츠: note 에 '대표 지정 시각'이 있으면 그 시각을 고정하고 다른 쇼츠가 앞뒤 90분을 피한다.
-- 적용은 Supabase 에서 아래처럼 배포된 함수 본문을 바꿔 넣었다(실제 본문은 2026-10-30_content_spacing.sql).
do $do$
declare d text;
begin
  d := pg_get_functiondef('public.ig_reslot(boolean)'::regprocedure);
  d := replace(d, '^(U|E|Q)', '^(U|E|Q|H)');
  execute d;
  d := pg_get_functiondef('public.yt_short_reslot(boolean)'::regprocedure);
  d := replace(d, $q$(status = 'uploaded' or youtube_id is not null)$q$, $q$(status = 'uploaded' or youtube_id is not null or coalesce(note,'') like '%대표 지정 시각%')$q$);
  d := replace(d, $q$p.kind = 'short' and p.status in ('review','approved') and p.youtube_id is null$q$, $q$p.kind = 'short' and p.status in ('review','approved') and p.youtube_id is null and coalesce(p.note,'') not like '%대표 지정 시각%'$q$);
  execute d;
end $do$;
