-- 2026-11-06 대표님: "쇼츠 조회 이거보다 많이 되었는데", "여전히 안 바뀌는데"
-- yt-public 함수가 유튜브 API로 읽은 영상별 조회수를 stats.public 에만 덮어쓴다(스튜디오 기록 등 다른 키는 그대로).
create or replace function public.yt_set_public_views(p_id text, p_views bigint, p_at timestamptz, p_by text)
returns void language sql security definer set search_path = public as $$
  update youtube_posts
     set stats = coalesce(stats, '{}'::jsonb) || jsonb_build_object('public', jsonb_build_object('at', p_at, 'by', p_by, 'views', p_views))
   where id = p_id
$$;
revoke all on function public.yt_set_public_views(text, bigint, timestamptz, text) from public, anon, authenticated;
grant execute on function public.yt_set_public_views(text, bigint, timestamptz, text) to service_role;

-- 같은 날 시험했던 DB 쪽 영상 페이지 읽기(믿을 수 없어 폐기)
drop function if exists public.yt_views_queue();
drop function if exists public.yt_views_apply();
drop function if exists public._yt_view_of(text);
drop table if exists public.yt_views_req;
